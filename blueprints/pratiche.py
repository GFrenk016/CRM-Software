"""Pratiche: unità di lavoro operativa collegata a cliente/contratto/sinistro."""
from datetime import date

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)
from sqlalchemy import func

from extensions import db
# _numero_intl vive in messaggi.py (normalizzazione numero per wa.me): la
# riusiamo per comporre il link della richiesta documenti, invece di duplicarla.
from blueprints.messaggi import _numero_intl
from models import (ESITI_APPUNTAMENTO, FAMIGLIE_STATI_PRATICA,
                    LABEL_FAMIGLIA_PRATICA, MOTIVI_PERDITA, ORDINE_STATI_PRATICA,
                    SCALA_AVANZAMENTO, STATI_DATA_PASSAGGIO, STATI_PER_TIPOLOGIA,
                    STATI_PRATICA, STATI_VINCOLO_FINESTRA, TIPI_APPUNTAMENTO,
                    ChecklistDocumento, Cliente, Contratto, Lead, Pratica,
                    PrioritaPratica, Sinistro, TipologiaPratica, Veicolo,
                    get_impostazioni, in_finestra_emissione,
                    registra_comunicazione)
from utils import parse_date

bp = Blueprint("pratiche", __name__, url_prefix="/pratiche")


def _testo_richiesta_documenti(p):
    """Compone il testo della richiesta dai ChecklistDocumento NON ancora ricevuti.

    Ritorna (testo, mancanti): testo vuoto se non manca nulla. Il CRM prepara
    solo il testo/link; l'invio effettivo lo fa l'operatore (vedi detail.html).
    """
    mancanti = [cd.tipo for cd in p.checklist_documenti if not cd.ricevuto]
    if not mancanti:
        return "", mancanti
    nome = (p.cliente.nome or p.cliente.nome_completo or "").strip()
    elenco = "\n".join(f"- {t}" for t in mancanti)
    testo = (f"Gentile {nome},\nper procedere con la pratica "
             f"{p.numero_identificativo} la preghiamo di farci pervenire i "
             f"seguenti documenti:\n{elenco}\nCordiali saluti.")
    return testo, mancanti


def _id_del_cliente(modello, valore, cliente_id):
    """Accetta l'id solo se quella riga appartiene davvero al cliente.

    Difesa lato server contro un collegamento incrociato: il menu nel browser è
    già filtrato, ma basta una POST costruita a mano (o un cliente cambiato
    dopo aver scelto il contratto) per collegare roba di un altro. In quel caso
    restituiamo None: meglio un campo vuoto che un dato sbagliato.
    """
    if not valore:
        return None
    riga = modello.query.filter_by(id=int(valore), cliente_id=cliente_id).first()
    return riga.id if riga else None


@bp.route("/")
def index():
    # Con 13 stati i chip di filtro sarebbero troppi: si filtra per FAMIGLIA di
    # stato (aperte / in attesa / in emissione / chiuse), non per singolo stato.
    famiglia = (request.args.get("famiglia") or "").strip()
    priorita = (request.args.get("priorita") or "").strip()
    tipologia = (request.args.get("tipologia") or "").strip()

    q = Pratica.query
    if famiglia in FAMIGLIE_STATI_PRATICA:
        q = q.filter(Pratica.stato.in_(FAMIGLIE_STATI_PRATICA[famiglia]))
    if priorita:
        q = q.filter_by(priorita=priorita)
    if tipologia:
        q = q.filter_by(tipologia=tipologia)
    pratiche = q.order_by(Pratica.data_apertura.desc()).all()

    # Conteggi per famiglia con UNA sola query (GROUP BY stato), non 13 COUNT.
    per_stato = dict(db.session.query(Pratica.stato, func.count(Pratica.id))
                     .group_by(Pratica.stato).all())
    conteggi = {fam: sum(per_stato.get(s, 0) for s in stati)
                for fam, stati in FAMIGLIE_STATI_PRATICA.items()}

    # Per il modale "Nuova pratica" serve solo l'elenco clienti: contratti e
    # sinistri arrivano da /pratiche/collegabili dopo la scelta del cliente.
    clienti = Cliente.query.order_by(Cliente.cognome).all()

    return render_template(
        "pratiche/list.html", pratiche=pratiche, stati=STATI_PRATICA,
        famiglie=FAMIGLIE_STATI_PRATICA, label_famiglia=LABEL_FAMIGLIA_PRATICA,
        famiglia_sel=famiglia, priorita_sel=priorita, tipologia_sel=tipologia,
        conteggi=conteggi, clienti=clienti, priorita_opts=PrioritaPratica,
        tipologia_opts=TipologiaPratica, stati_per_tipologia=STATI_PER_TIPOLOGIA,
    )


@bp.route("/<int:pratica_id>")
def detail(pratica_id):
    """Scheda della singola pratica: è la pagina dove vive tutta la lavorazione
    (avanzamento, documenti, appuntamenti, comunicazioni, preventivi collegati).
    """
    p = Pratica.query.get_or_404(pratica_id)
    testo_richiesta, documenti_mancanti = _testo_richiesta_documenti(p)
    wa_number = _numero_intl(p.cliente.cellulare or p.cliente.telefono)
    return render_template("pratiche/detail.html", p=p,
                           testo_richiesta=testo_richiesta,
                           documenti_mancanti=documenti_mancanti,
                           # Cross selling: gli altri mezzi del cliente senza
                           # copertura attiva (escluso quello della pratica).
                           veicoli_scoperti=p.cliente.altri_veicoli_scoperti(p.veicolo_id),
                           wa_number=wa_number, scala=SCALA_AVANZAMENTO,
                           pos_corrente=ORDINE_STATI_PRATICA.get(p.stato),
                           tipi_appuntamento=TIPI_APPUNTAMENTO,
                           esiti_appuntamento=ESITI_APPUNTAMENTO)


@bp.route("/<int:pratica_id>/avanza", methods=["POST"])
def avanza(pratica_id):
    """Avanzamento guidato: porta la pratica allo stato successivo della scala.

    Valorizza la data del passaggio (pagamento_verificato / emessa /
    certificato_inviato) e, se si entra nella coda/emissione fuori dalle finestre
    di emissione, mostra un avviso NON bloccante (l'avanzamento avviene comunque).
    """
    p = Pratica.query.get_or_404(pratica_id)
    prossimo = p.stato_successivo
    if not prossimo:
        flash("Nessuno step successivo per questa pratica.", "error")
        return redirect(url_for("pratiche.detail", pratica_id=p.id))

    p.stato = prossimo
    # Fissa la data del passaggio se non già presente (non la si sovrascrive).
    campo_data = STATI_DATA_PASSAGGIO.get(prossimo)
    if campo_data and getattr(p, campo_data) is None:
        setattr(p, campo_data, date.today())

    # Vincolo finestre di emissione: avviso non bloccante fuori orario.
    if prossimo in STATI_VINCOLO_FINESTRA and \
            not in_finestra_emissione(get_impostazioni()):
        flash("Passaggio a '%s' fuori dalle finestre di emissione: verifica gli "
              "orari prima di procedere in compagnia." % prossimo.replace("_", " "),
              "warning")

    db.session.commit()
    flash("Pratica avanzata a: %s." % prossimo.replace("_", " "), "success")
    return redirect(url_for("pratiche.detail", pratica_id=p.id))


# --------------------------------------------------------------------------- #
#  Checklist documenti (cosa DEVE arrivare) e richiesta documenti al cliente   #
# --------------------------------------------------------------------------- #
@bp.route("/<int:pratica_id>/checklist", methods=["POST"])
def checklist_aggiungi(pratica_id):
    p = Pratica.query.get_or_404(pratica_id)
    tipo = (request.form.get("tipo") or "").strip()
    if not tipo:
        flash("Indica il tipo di documento.", "error")
        return redirect(url_for("pratiche.detail", pratica_id=p.id))
    db.session.add(ChecklistDocumento(
        pratica_id=p.id, tipo=tipo,
        note=(request.form.get("note") or "").strip() or None,
        ricevuto=False))
    db.session.commit()
    flash("Documento aggiunto alla checklist.", "success")
    return redirect(url_for("pratiche.detail", pratica_id=p.id))


@bp.route("/<int:pratica_id>/checklist/<int:item_id>/toggle", methods=["POST"])
def checklist_toggle(pratica_id, item_id):
    item = ChecklistDocumento.query.filter_by(
        id=item_id, pratica_id=pratica_id).first_or_404()
    item.ricevuto = not item.ricevuto
    db.session.commit()
    return redirect(url_for("pratiche.detail", pratica_id=pratica_id))


@bp.route("/<int:pratica_id>/checklist/<int:item_id>/elimina", methods=["POST"])
def checklist_elimina(pratica_id, item_id):
    item = ChecklistDocumento.query.filter_by(
        id=item_id, pratica_id=pratica_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash("Voce checklist eliminata.", "success")
    return redirect(url_for("pratiche.detail", pratica_id=pratica_id))


@bp.route("/<int:pratica_id>/richiesta-documenti", methods=["POST"])
def richiesta_documenti(pratica_id):
    """Registra a sistema la richiesta documenti composta e aperta dall'operatore.

    NIENTE invio automatico e niente API a pagamento: il link wa.me/mailto viene
    aperto lato client (vedi app.js), qui si TRACCIA solo la comunicazione con
    registra_comunicazione(), coerentemente con il resto del CRM.
    """
    p = Pratica.query.get_or_404(pratica_id)
    payload = request.get_json(silent=True) or {}
    canale = payload.get("canale", "whatsapp")
    testo = (payload.get("testo") or "").strip()
    destinatario = (payload.get("destinatario") or "").strip() or None
    if not testo:
        return jsonify(ok=False, error="Nessun testo da registrare"), 400
    registra_comunicazione(cliente_id=p.cliente_id, canale=canale,
                           destinatario=destinatario, testo=testo,
                           pratica_id=p.id)
    return jsonify(ok=True)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:pratica_id>/modifica", methods=["GET", "POST"])
def form(pratica_id=None):
    p = Pratica.query.get_or_404(pratica_id) if pratica_id else None
    if request.method == "POST":
        f = request.form
        try:
            if p is None:
                p = Pratica(cliente_id=int(f["cliente_id"]),
                           tipologia=f["tipologia"])
                db.session.add(p)
            else:
                p.cliente_id = int(f["cliente_id"])
                p.tipologia = f["tipologia"]
            # I menu sono già filtrati sul cliente lato browser, ma il filtro
            # client-side non è una garanzia: qui ricontrolliamo che contratto,
            # sinistro e veicolo appartengano DAVVERO al cliente della pratica.
            # Se non è così azzeriamo il riferimento invece di salvare un
            # collegamento incrociato tra clienti diversi.
            p.contratto_id = _id_del_cliente(Contratto, f.get("contratto_id"),
                                             p.cliente_id)
            p.sinistro_id = _id_del_cliente(Sinistro, f.get("sinistro_id"),
                                            p.cliente_id)
            p.veicolo_id = _id_del_cliente(Veicolo, f.get("veicolo_id"),
                                           p.cliente_id)
            # Il lead NON si sceglie: dopo la regola "pipeline specchio
            # dell'anagrafica" ogni cliente ne ha esattamente uno, quindi il
            # collegamento si deriva. Il form lo mostra soltanto.
            lead = Lead.query.filter_by(cliente_id=p.cliente_id).first()
            p.lead_id = lead.id if lead else None
            p.stato = f.get("stato", "aperta")
            p.priorita = f.get("priorita", PrioritaPratica.MEDIA.value)
            p.note = f.get("note", "").strip() or None
            # Esito negativo (compilato solo quando la pratica è "persa").
            p.motivo_perdita = f.get("motivo_perdita", "").strip() or None
            p.data_scadenza_riferimento = parse_date(f.get("data_scadenza_riferimento"))
            db.session.commit()
            flash("Pratica salvata.", "success")
            return redirect(url_for("pratiche.detail", pratica_id=p.id))
        except ValueError as e:
            db.session.rollback()
            flash(str(e), "error")

    # Contratti, sinistri e veicoli NON si caricano più qui: i menu partono
    # vuoti e li riempie /pratiche/collegabili quando si sceglie il cliente.
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    cliente_sel = request.args.get("cliente_id", type=int)
    return render_template(
        "pratiche/form.html", p=p, clienti=clienti, stati=STATI_PRATICA,
        motivi_perdita=MOTIVI_PERDITA, priorita_opts=PrioritaPratica,
        tipologia_opts=TipologiaPratica, cliente_sel=cliente_sel,
        stati_per_tipologia=STATI_PER_TIPOLOGIA,
    )


@bp.route("/collegabili")
def collegabili():
    """Entità collegabili a una pratica, filtrate sul cliente selezionato.

    Serve i due form "nuova/modifica pratica": scegliendo il cliente, i menu
    contratto/sinistro/veicolo si ripopolano con SOLO la roba sua. Prima erano
    liste globali, quindi era possibile (e facilissimo) collegare a una pratica
    il contratto di un altro cliente.

    Il lead non è una scelta: dopo la regola "pipeline specchio dell'anagrafica"
    ogni cliente ha un lead solo, quindi lo restituiamo come etichetta da
    mostrare e basta — il collegamento lo fa il server da sé.
    """
    cliente_id = request.args.get("cliente_id", type=int)
    if not cliente_id:
        return jsonify(contratti=[], sinistri=[], veicoli=[], lead=None)

    contratti = (Contratto.query.filter_by(cliente_id=cliente_id)
                 .order_by(Contratto.numero_polizza).all())
    sinistri = (Sinistro.query.filter_by(cliente_id=cliente_id)
                .order_by(Sinistro.numero).all())
    veicoli = (Veicolo.query.filter_by(cliente_id=cliente_id)
               .order_by(Veicolo.targa).all())
    lead = Lead.query.filter_by(cliente_id=cliente_id).first()

    return jsonify(
        contratti=[{"id": k.id,
                    "label": " · ".join(x for x in (k.numero_polizza, k.ramo,
                                                    k.compagnia.nome if k.compagnia else None) if x)}
                   for k in contratti],
        sinistri=[{"id": s.id, "label": f"{s.numero or 'senza numero'} · {s.stato or '—'}"}
                  for s in sinistri],
        veicoli=[{"id": v.id,
                  "label": f"{v.targa} · {' '.join(x for x in (v.marca, v.modello) if x) or '—'}"}
                 for v in veicoli],
        lead=({"id": lead.id, "label": f"{lead.stadio} · {lead.giorni_nello_stadio} gg"}
              if lead else None),
    )


@bp.route("/<int:pratica_id>/elimina", methods=["POST"])
def elimina(pratica_id):
    p = Pratica.query.get_or_404(pratica_id)
    db.session.delete(p)
    db.session.commit()
    flash("Pratica eliminata.", "success")
    return redirect(url_for("pratiche.index"))
