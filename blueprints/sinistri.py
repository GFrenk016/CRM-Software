"""Sinistri: collegati a un cliente e a un contratto."""
from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import STATI_SINISTRO, Cliente, Contratto, Sinistro
from utils import parse_date

bp = Blueprint("sinistri", __name__, url_prefix="/sinistri")


def _prossimo_numero():
    n = Sinistro.query.count() + 1
    return f"SIN-{n:04d}"


@bp.route("/")
def index():
    stato = (request.args.get("stato") or "").strip()
    q = Sinistro.query
    if stato:
        q = q.filter_by(stato=stato)
    sinistri = q.order_by(Sinistro.data_apertura.desc()).all()
    conteggi = {s: Sinistro.query.filter_by(stato=s).count() for s in STATI_SINISTRO}
    return render_template("sinistri/list.html", sinistri=sinistri,
                           stati=STATI_SINISTRO, stato_sel=stato, conteggi=conteggi)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:sin_id>/modifica", methods=["GET", "POST"])
def form(sin_id=None):
    s = Sinistro.query.get_or_404(sin_id) if sin_id else None
    if request.method == "POST":
        f = request.form
        if s is None:
            s = Sinistro(numero=_prossimo_numero())
            db.session.add(s)
        s.cliente_id = int(f["cliente_id"])
        s.contratto_id = int(f["contratto_id"])
        s.tipo = f.get("tipo", "").strip() or None
        s.data_apertura = parse_date(f.get("data_apertura"))
        s.stato = f.get("stato", "aperto")
        s.importo_stimato = float(f.get("importo_stimato") or 0)
        s.note = f.get("note", "").strip() or None
        db.session.commit()
        flash("Sinistro salvato.", "success")
        return redirect(url_for("sinistri.index"))
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    contratti = Contratto.query.order_by(Contratto.numero_polizza).all()
    return render_template("sinistri/form.html", s=s, clienti=clienti,
                           contratti=contratti, stati=STATI_SINISTRO)


@bp.route("/<int:sin_id>/elimina", methods=["POST"])
def elimina(sin_id):
    s = Sinistro.query.get_or_404(sin_id)
    db.session.delete(s)
    db.session.commit()
    flash("Sinistro eliminato.", "success")
    return redirect(url_for("sinistri.index"))
