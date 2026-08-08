"""Preventivi: vista distinta dai contratti. Un preventivo accettato può
generare un contratto attivo collegato (link all'origine)."""
from datetime import date

from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import (GARANZIE, STATI_PREVENTIVO, Cliente, Compagnia, Contratto,
                    Lead, Preventivo, PreventivoCompagnia, Veicolo)
from utils import parse_date, rendi_form

bp = Blueprint("preventivi", __name__, url_prefix="/preventivi")


def _prossimo_numero():
    n = Preventivo.query.count() + 1
    return f"PRV-{n:04d}"


def _righe_consultate(form):
    """Legge dal form le righe "compagnia consultata" e le restituisce in ordine.

    Le righe sono ripetibili e cancellabili lato client, quindi gli indici NON
    sono contigui: l'elenco degli indici vivi viaggia nel campo ripetuto
    `cc_idx` e i campi di ogni riga sono suffissati con l'indice. Le righe senza
    compagnia sono righe vuote appena aggiunte e vengono ignorate.

    Ritorna (righe, duplicate): `duplicate` sono i nomi delle compagnie indicate
    più di una volta, scartate perché il vincolo di unicità le rifiuterebbe.
    """
    righe, viste, duplicate = [], set(), []
    for idx in form.getlist("cc_idx"):
        compagnia_id = form.get(f"cc_compagnia_id_{idx}")
        if not compagnia_id:
            continue
        compagnia_id = int(compagnia_id)
        if compagnia_id in viste:
            duplicate.append(compagnia_id)
            continue
        viste.add(compagnia_id)
        righe.append({
            "idx": idx,
            "compagnia_id": compagnia_id,
            "premio": float(form.get(f"cc_premio_{idx}") or 0),
            "garanzie": form.getlist(f"cc_garanzie_{idx}"),
            "note": (form.get(f"cc_note_{idx}") or "").strip() or None,
        })
    return righe, duplicate


def _sincronizza_consultate(prev, righe):
    """Allinea le righe consultate del preventivo a quelle arrivate dal form.

    Aggiorna le righe esistenti IN PLACE (chiave: la compagnia) invece di
    ricrearle: così created_at resta quello della prima consultazione e non si
    passa mai da uno stato intermedio con due righe sulla stessa compagnia, che
    violerebbe il vincolo di unicità.
    """
    per_compagnia = {r.compagnia_id: r for r in prev.compagnie_consultate}
    inviate = set()
    for dati in righe:
        inviate.add(dati["compagnia_id"])
        riga = per_compagnia.get(dati["compagnia_id"])
        if riga is None:
            riga = PreventivoCompagnia(compagnia_id=dati["compagnia_id"])
            prev.compagnie_consultate.append(riga)
        riga.premio = dati["premio"]
        riga.garanzie = dati["garanzie"]      # @validates accetta anche la lista
        riga.note = dati["note"]
    # Le righe non più presenti nel form sono state rimosse dall'operatore:
    # delete-orphan le cancella davvero dal DB.
    for compagnia_id, riga in per_compagnia.items():
        if compagnia_id not in inviate:
            prev.compagnie_consultate.remove(riga)


def _scadenza_riferimento(prev):
    """Scadenza a cui ordinare un preventivo: la più vicina tra i contratti
    ATTIVI del suo cliente.

    Il Preventivo NON ha una data di scadenza propria (un preventivo non "scade"
    come una polizza): la si risale dal cliente → contratti attivi →
    data_scadenza. Ritorna None se il cliente non ha contratti attivi datati.
    """
    scadenze = [k.data_scadenza for k in prev.cliente.contratti
                if k.stato == "attivo" and k.data_scadenza]
    return min(scadenze) if scadenze else None


@bp.route("/")
def index():
    stato = (request.args.get("stato") or "").strip()
    ordina = (request.args.get("ordina") or "").strip()
    q = Preventivo.query
    if stato:
        q = q.filter_by(stato=stato)
    if ordina == "scadenza":
        # Ordinamento per scadenza della polizza attuale del cliente, crescente,
        # con i preventivi senza scadenza in fondo. Si risale via relazione
        # (vedi _scadenza_riferimento), quindi si ordina in Python: None-last si
        # ottiene con una chiave-tupla (prima il flag "senza scadenza").
        preventivi = q.all()
        preventivi.sort(key=lambda p: (_scadenza_riferimento(p) is None,
                                       _scadenza_riferimento(p) or date.max))
    else:
        preventivi = q.order_by(Preventivo.created_at.desc()).all()
    # Il pannello "Nuovo preventivo" arriva montato da /preventivi/nuovo?modal=1,
    # quindi qui non servono più clienti/compagnie/lead/veicoli.
    # Scadenza di riferimento per riga (derivata dai contratti attivi del
    # cliente): mostrata in colonna così l'ordinamento è leggibile.
    scadenze_rif = {p.id: _scadenza_riferimento(p) for p in preventivi}
    return render_template("preventivi/list.html", preventivi=preventivi,
                           stati=STATI_PREVENTIVO, stato_sel=stato,
                           ordina_sel=ordina, scadenze_rif=scadenze_rif)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:prev_id>/modifica", methods=["GET", "POST"])
def form(prev_id=None):
    prev = Preventivo.query.get_or_404(prev_id) if prev_id else None
    if request.method == "POST":
        f = request.form
        if prev is None:
            prev = Preventivo(numero=_prossimo_numero())
            db.session.add(prev)
        prev.cliente_id = int(f["cliente_id"])
        # Il lead non arriva dal form: ogni cliente ne ha uno solo (pipeline
        # specchio dell'anagrafica), quindi lo deriviamo.
        _lead = Lead.query.filter_by(cliente_id=prev.cliente_id).first()
        prev.lead_id = _lead.id if _lead else None
        prev.compagnia_id = int(f["compagnia_id"]) if f.get("compagnia_id") else None
        # Il menu è filtrato lato browser, ma qui ricontrolliamo: un veicolo di
        # un altro cliente non deve poter finire su questo preventivo.
        _v = (Veicolo.query.filter_by(id=int(f["veicolo_id"]),
                                      cliente_id=prev.cliente_id).first()
              if f.get("veicolo_id") else None)
        prev.veicolo_id = _v.id if _v else None
        prev.oggetto = f.get("oggetto", "").strip() or None
        prev.premio_proposto = float(f.get("premio_proposto") or 0)
        prev.stato = f.get("stato", "bozza")
        prev.data_invio = parse_date(f.get("data_invio"))
        prev.note = f.get("note", "").strip() or None

        righe, duplicate = _righe_consultate(f)
        try:
            _sincronizza_consultate(prev, righe)
        except ValueError as e:              # garanzia non ammessa (@validates)
            db.session.rollback()
            flash(str(e), "error")
            return redirect(url_for("preventivi.form", prev_id=prev_id))

        # Promozione a "compagnia scelta": la riga spuntata nel confronto vince
        # sui campi in alto, che restano compilabili quando non si è consultato
        # nessuno (preventivo con una compagnia sola).
        scelta = f.get("cc_scelta")
        riga_scelta = next((r for r in righe if r["idx"] == scelta), None)
        if riga_scelta:
            prev.compagnia_id = riga_scelta["compagnia_id"]
            prev.premio_proposto = riga_scelta["premio"]

        db.session.commit()
        if duplicate:
            nomi = ", ".join(c.nome for c in Compagnia.query
                             .filter(Compagnia.id.in_(duplicate)))
            flash(f"Compagnia indicata più volte, tenuta una sola riga: {nomi}.",
                  "warning")
        flash("Preventivo salvato.", "success")
        return redirect(url_for("preventivi.index"))
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    # Lead e veicoli non si caricano più qui: il lead è derivato e i veicoli
    # arrivano da /pratiche/collegabili filtrati sul cliente scelto.
    # Cliente pre-selezionato quando si crea "da scheda cliente" (?cliente_id=X)
    cliente_sel = request.args.get("cliente_id", type=int)
    # Cross selling: altri veicoli del cliente senza copertura attiva. L'avviso
    # si riferisce al cliente NOTO all'apertura della pagina (quello del
    # preventivo, o quello pre-selezionato); cambiando cliente dal menu a tendina
    # non si aggiorna, perché il dato è calcolato lato server sulle relazioni.
    cliente_avviso = prev.cliente if prev else (
        db.session.get(Cliente, cliente_sel) if cliente_sel else None)
    veicoli_scoperti = (cliente_avviso.altri_veicoli_scoperti(
        prev.veicolo_id if prev else None) if cliente_avviso else [])
    return rendi_form(
        "preventivi/form.html", "preventivi/_campi.html",
        "Modifica preventivo" if prev else "Nuovo preventivo",
        p=prev, clienti=clienti, compagnie=compagnie,
        stati=STATI_PREVENTIVO, cliente_sel=cliente_sel,
        garanzie=GARANZIE, cliente_avviso=cliente_avviso,
        veicoli_scoperti=veicoli_scoperti,
        form_action=url_for("preventivi.form", prev_id=prev_id) if prev_id
        else url_for("preventivi.form"),
    )


@bp.route("/<int:prev_id>/converti", methods=["POST"])
def converti(prev_id):
    """Genera un contratto attivo a partire da un preventivo accettato."""
    prev = Preventivo.query.get_or_404(prev_id)
    if prev.contratto:
        flash("Questo preventivo ha già un contratto collegato.", "error")
        return redirect(url_for("contratti.detail", contratto_id=prev.contratto.id))
    prev.stato = "accettato"
    contratto = Contratto(
        cliente_id=prev.cliente_id,
        preventivo_id=prev.id,
        compagnia_id=prev.compagnia_id,
        numero_polizza=f"POL-DA-{prev.numero}",
        ramo=prev.oggetto,
        premio=prev.premio_proposto,
        data_emissione=date.today(),
        stato="attivo",
    )
    db.session.add(contratto)
    db.session.commit()
    flash("Contratto generato dal preventivo. Completa numero polizza e scadenza.",
          "success")
    return redirect(url_for("contratti.form", contratto_id=contratto.id))


@bp.route("/<int:prev_id>/elimina", methods=["POST"])
def elimina(prev_id):
    prev = Preventivo.query.get_or_404(prev_id)
    db.session.delete(prev)
    db.session.commit()
    flash("Preventivo eliminato.", "success")
    return redirect(url_for("preventivi.index"))
