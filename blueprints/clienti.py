"""Anagrafica clienti: elenco con filtro multi-campo, CRUD e scheda 360°."""
from datetime import date

from flask import (Blueprint, flash, redirect, render_template, request, url_for)
from sqlalchemy import and_

from extensions import db
from models import Cliente, Compagnia, Contratto
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
    if f["citta"]:
        conditions.append(Cliente.citta.ilike(f"%{f['citta']}%"))
    if f["provincia"]:
        conditions.append(Cliente.provincia.ilike(f["provincia"]))
    if f["professione"]:
        conditions.append(Cliente.professione.ilike(f"%{f['professione']}%"))
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


@bp.route("/")
def index():
    q, filtri = _build_filters(request.args)
    clienti = q.order_by(Cliente.cognome, Cliente.nome).all()
    stati_civili = ["celibe/nubile", "coniugato", "convivente", "divorziato", "vedovo"]
    filtri_attivi = any(v for v in filtri.values())
    return render_template("clienti/list.html", clienti=clienti, filtri=filtri,
                           stati_civili=stati_civili, filtri_attivi=filtri_attivi)


@bp.route("/<int:cliente_id>")
def detail(cliente_id):
    """Scheda 360°: cliente + tutte le entità collegate via FK."""
    cliente = Cliente.query.get_or_404(cliente_id)
    return render_template("clienti/detail.html", c=cliente, oggi=date.today())


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:cliente_id>/modifica", methods=["GET", "POST"])
def form(cliente_id=None):
    cliente = Cliente.query.get_or_404(cliente_id) if cliente_id else None
    if request.method == "POST":
        data = _read_form(request.form)
        if cliente is None:
            cliente = Cliente(**data)
            db.session.add(cliente)
            flash("Cliente creato.", "success")
        else:
            for k, v in data.items():
                setattr(cliente, k, v)
            flash("Cliente aggiornato.", "success")
        db.session.commit()
        return redirect(url_for("clienti.detail", cliente_id=cliente.id))
    return render_template("clienti/form.html", c=cliente)


@bp.route("/<int:cliente_id>/elimina", methods=["POST"])
def delete(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    db.session.delete(cliente)
    db.session.commit()
    flash("Cliente eliminato.", "success")
    return redirect(url_for("clienti.index"))


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
