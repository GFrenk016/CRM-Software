"""Anagrafica clienti: elenco con filtro multi-campo, CRUD e scheda 360°."""
from datetime import date, datetime

from flask import (Blueprint, flash, redirect, render_template, request, url_for)
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import (ESITI_APPUNTAMENTO, STADI_LEAD, TIPI_APPUNTAMENTO, Cliente,
                    Contratto, Lead, Pratica, TipologiaPratica, Veicolo)
from utils import parse_date

bp = Blueprint("clienti", __name__, url_prefix="/clienti")


def _build_filters(args):
    """Traduce i parametri di ricerca in condizioni SQL (WHERE), non lato client.

    Le condizioni si combinano in AND: si possono incrociare più campi
    contemporaneamente (es. clienti con figli E con polizza in scadenza in un mese).
    Restituisce (query, valori_form) dove valori_form ripopola il form.
    """
    q = Cliente.query
    conditions = []
    f = {k: (args.get(k) or "").strip() for k in (
        "nome", "citta", "provincia", "professione", "stato_civile",
        "con_figli", "scad_mese", "scad_anno")}

    if f["nome"]:
        like = f"%{f['nome']}%"
        conditions.append(db.or_(
            Cliente.nome.ilike(like),
            Cliente.cognome.ilike(like),
            Cliente.codice_fiscale.ilike(like),
            Cliente.email.ilike(like),
            Cliente.cellulare.ilike(like),
        ))
    # Città, provincia e professione arrivano da una tendina costruita sui
    # valori realmente presenti: il valore è esatto, quindi si confronta con
    # l'uguaglianza. Con il LIKE di prima (nato per l'input libero) scegliere
    # "Roma" avrebbe pescato anche "Roma Nord", un risultato sbagliato e
    # difficile da notare perché la lista sembra comunque plausibile.
    if f["citta"]:
        conditions.append(Cliente.citta == f["citta"])
    if f["provincia"]:
        conditions.append(Cliente.provincia == f["provincia"])
    if f["professione"]:
        conditions.append(Cliente.professione == f["professione"])
    if f["stato_civile"]:
        conditions.append(Cliente.stato_civile == f["stato_civile"])
    if f["con_figli"] == "si":
        conditions.append(Cliente.num_figli > 0)
    elif f["con_figli"] == "no":
        conditions.append(db.or_(Cliente.num_figli == 0, Cliente.num_figli == None))  # noqa: E711

    # Filtro incrociato: clienti con una polizza in scadenza in un dato mese/anno.
    # Si traduce in una JOIN sui contratti con estrazione mese/anno dalla data.
    if f["scad_mese"] or f["scad_anno"]:
        q = q.join(Contratto, Contratto.cliente_id == Cliente.id)
        if f["scad_mese"]:
            conditions.append(
                db.func.strftime("%m", Contratto.data_scadenza) == f"{int(f['scad_mese']):02d}")
        if f["scad_anno"]:
            conditions.append(
                db.func.strftime("%Y", Contratto.data_scadenza) == f["scad_anno"])
        q = q.distinct()

    if conditions:
        q = q.filter(and_(*conditions))
    return q, f


def _opzioni_distinte(colonna, selezionato=None):
    """Valori realmente presenti in una colonna, per popolare una tendina.

    DISTINCT lato database e non un set costruito in Python: servono poche
    stringhe, caricare tutti i clienti in memoria per estrarle sarebbe
    sproporzionato e peggiorerebbe man mano che l'anagrafica cresce.

    Solo clienti non archiviati, perché l'elenco filtrato mostra solo quelli:
    una città rimasta in tendina senza clienti visibili darebbe zero risultati
    senza che si capisca perché.
    """
    righe = (db.session.query(colonna)
             .filter(Cliente.archiviato.is_(False),
                     colonna.isnot(None), colonna != "")
             .distinct().all())
    valori = sorted({r[0] for r in righe})
    return _con_selezionato(valori, selezionato)


def _anni_scadenza(selezionato=None):
    """Anni distinti in cui scade almeno un contratto di un cliente attivo."""
    # NB: strftime è specifico di SQLite, come l'estrazione mese/anno in
    # _build_filters. È il debito tecnico già annotato in bugfixes.md
    # (config.py con SQLite hardcoded): non risolto qui, solo segnalato.
    anno = db.func.strftime("%Y", Contratto.data_scadenza)
    righe = (db.session.query(anno)
             .select_from(Contratto)
             .join(Cliente, Contratto.cliente_id == Cliente.id)
             .filter(Cliente.archiviato.is_(False),
                     Contratto.data_scadenza.isnot(None))
             .distinct().all())
    # Anni a 4 cifre: l'ordine alfabetico coincide con quello numerico.
    anni = sorted({r[0] for r in righe if r[0]})
    return _con_selezionato(anni, selezionato)


def _con_selezionato(valori, selezionato):
    """Tiene in lista il valore filtrato anche se non è più fra i disponibili.

    Capita arrivando da un URL scritto a mano (?citta=X) o se l'ultimo cliente
    di quella città viene archiviato: senza questo la tendina tornerebbe da
    sola su "Tutte" mentre il filtro resta applicato, e l'elenco vuoto non
    avrebbe più una spiegazione visibile.
    """
    if selezionato and selezionato not in valori:
        return sorted(valori + [selezionato])
    return valori


@bp.route("/")
def index():
    q, filtri = _build_filters(request.args)
    # L'elenco operativo mostra solo i clienti attivi: gli archiviati si
    # consultano dalla modale dedicata (tasto "Archiviati" in alto).
    clienti = (q.filter(Cliente.archiviato.is_(False))
               .order_by(Cliente.cognome, Cliente.nome).all())
    archiviati = (Cliente.query.filter(Cliente.archiviato.is_(True))
                  .order_by(Cliente.archiviato_at.desc(), Cliente.cognome).all())
    # Tendine del pannello filtri. Anche stato civile passa da qui: la lista
    # fissa scritta a mano proponeva voci senza nemmeno un cliente dietro.
    citta = _opzioni_distinte(Cliente.citta, filtri["citta"])
    province = _opzioni_distinte(Cliente.provincia, filtri["provincia"])
    professioni = _opzioni_distinte(Cliente.professione, filtri["professione"])
    stati_civili = _opzioni_distinte(Cliente.stato_civile, filtri["stato_civile"])
    anni_scadenza = _anni_scadenza(filtri["scad_anno"])
    filtri_attivi = any(v for v in filtri.values())
    return render_template("clienti/list.html", clienti=clienti, filtri=filtri,
                           archiviati=archiviati, stati_civili=stati_civili,
                           citta=citta, province=province,
                           professioni=professioni, anni_scadenza=anni_scadenza,
                           filtri_attivi=filtri_attivi)


@bp.route("/archivia", methods=["POST"])
def archivia():
    """Archivia i clienti spuntati nell'elenco (azione massiva).

    Non tocca contratti, sinistri o incassi: è solo un flag di visibilità.
    Idempotente: riarchiviare un cliente già archiviato non cambia nulla e non
    ne aggiorna la data, così l'ordinamento della modale resta stabile.
    """
    ids = [int(i) for i in request.form.getlist("ids") if str(i).isdigit()]
    if not ids:
        flash("Nessun cliente selezionato.", "error")
        return redirect(url_for("clienti.index"))
    clienti = Cliente.query.filter(Cliente.id.in_(ids),
                                   Cliente.archiviato.is_(False)).all()
    for cliente in clienti:
        cliente.archiviato = True
        cliente.archiviato_at = datetime.utcnow()
    db.session.commit()
    n = len(clienti)
    flash(f"{n} cliente archiviato." if n == 1 else f"{n} clienti archiviati.",
          "success")
    return redirect(url_for("clienti.index"))


@bp.route("/<int:cliente_id>/ripristina", methods=["POST"])
def ripristina(cliente_id):
    """Riporta un cliente archiviato nell'elenco operativo (e in Pipeline)."""
    cliente = Cliente.query.get_or_404(cliente_id)
    cliente.archiviato = False
    cliente.archiviato_at = None
    db.session.commit()
    flash(f"{cliente.nome_completo} ripristinato.", "success")
    return redirect(url_for("clienti.index"))


@bp.route("/<int:cliente_id>")
def detail(cliente_id):
    """Scheda 360°: cliente + tutte le entità collegate via FK."""
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("clienti/detail.html", c=cliente, oggi=date.today(),
                           tipi_appuntamento=TIPI_APPUNTAMENTO,
                           esiti_appuntamento=ESITI_APPUNTAMENTO)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:cliente_id>/modifica", methods=["GET", "POST"])
def form(cliente_id=None):
    cliente = Cliente.query.get_or_404(cliente_id) if cliente_id else None
    if request.method == "POST":
        data = _read_form(request.form)
        if cliente is None:
            cliente = Cliente(**data)
            db.session.add(cliente)
            # Il lead nasce automaticamente con il cliente ed entra nel primo
            # stadio della pipeline. Avviene SOLO alla creazione (non in modifica),
            # così non si generano lead duplicati a ogni aggiornamento anagrafica.
            lead = Lead(cliente=cliente, stadio=STADI_LEAD[0], fonte="altro")
            db.session.add(lead)

            # "Ogni contatto genera una pratica": la tipologia è OPZIONALE perché
            # al primo contatto può non essere ancora nota. Se l'utente la
            # seleziona, creiamo la Pratica insieme al Lead; altrimenti nasce solo
            # il Lead (nessuna tipologia inventata di default).
            tipologia = (request.form.get("tipologia_pratica") or "").strip()
            if tipologia:
                if tipologia not in TipologiaPratica.valori():
                    db.session.rollback()
                    flash("Tipologia pratica non valida.", "error")
                    return render_template("clienti/form.html", c=None,
                                           tipologie=TipologiaPratica)
                db.session.add(Pratica(cliente=cliente, lead=lead,
                                       tipologia=tipologia))
                flash("Cliente creato. Lead e pratica aggiunti.", "success")
            else:
                flash("Cliente creato. Lead aggiunto in pipeline.", "success")
        else:
            for k, v in data.items():
                setattr(cliente, k, v)
            flash("Cliente aggiornato.", "success")
        db.session.commit()
        return redirect(url_for("clienti.detail", cliente_id=cliente.id))
    return render_template("clienti/form.html", c=cliente,
                           tipologie=TipologiaPratica)


@bp.route("/<int:cliente_id>/elimina", methods=["POST"])
def delete(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminato.", "success")
    return redirect(url_for("clienti.index"))


@bp.route("/<int:cliente_id>/veicoli/nuovo", methods=["POST"])
def aggiungi_veicolo(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    try:
        # Il costruttore assegna gli attributi subito: @validates su targa
        # scatta già qui (non solo al commit), quindi va incluso nel try.
        veicolo = Veicolo(
            cliente_id=cliente.id,
            targa=request.form.get("targa", ""),
            marca=request.form.get("marca", "").strip() or None,
            modello=request.form.get("modello", "").strip() or None,
        )
        db.session.add(veicolo)
        db.session.commit()
        flash("Veicolo aggiunto.", "success")
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
    except IntegrityError:
        db.session.rollback()
        flash("Esiste già un veicolo con questa targa.", "error")
    return redirect(url_for("clienti.detail", cliente_id=cliente.id))


@bp.route("/<int:cliente_id>/veicoli/<int:veicolo_id>/elimina", methods=["POST"])
def elimina_veicolo(cliente_id, veicolo_id):
    veicolo = Veicolo.query.filter_by(id=veicolo_id, cliente_id=cliente_id).first_or_404()
    db.session.delete(veicolo)
    db.session.commit()
    flash("Veicolo eliminato.", "success")
    return redirect(url_for("clienti.detail", cliente_id=cliente_id))


def _read_form(form):
    return dict(
        nome=form.get("nome", "").strip(),
        cognome=form.get("cognome", "").strip(),
        indirizzo=form.get("indirizzo", "").strip() or None,
        citta=form.get("citta", "").strip() or None,
        cap=form.get("cap", "").strip() or None,
        provincia=form.get("provincia", "").strip().upper() or None,
        email=form.get("email", "").strip() or None,
        telefono=form.get("telefono", "").strip() or None,
        cellulare=form.get("cellulare", "").strip() or None,
        codice_fiscale=form.get("codice_fiscale", "").strip().upper() or None,
        data_nascita=parse_date(form.get("data_nascita")),
        tipo_documento=form.get("tipo_documento", "").strip() or None,
        numero_documento=form.get("numero_documento", "").strip() or None,
        professione=form.get("professione", "").strip() or None,
        stato_civile=form.get("stato_civile", "").strip() or None,
        convivenza=form.get("convivenza") == "on",
        num_figli=int(form.get("num_figli") or 0),
        note=form.get("note", "").strip() or None,
    )