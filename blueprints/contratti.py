"""Contratti attivi: polizze effettivamente emesse, distinte dai preventivi."""
from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import (STATI_CONTRATTO, Cliente, Compagnia, Contratto, Preventivo)
from utils import parse_date

bp = Blueprint("contratti", __name__, url_prefix="/contratti")


@bp.route("/")
def index():
    compagnia = (request.args.get("compagnia") or "").strip()
    stato = (request.args.get("stato") or "").strip()
    q = Contratto.query
    if compagnia:
        q = q.filter_by(compagnia_id=int(compagnia))
    if stato:
        q = q.filter_by(stato=stato)
    contratti = q.order_by(Contratto.data_scadenza).all()
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    # Dati per i <select>/ricerca del modale "Nuovo contratto"
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    preventivi = Preventivo.query.order_by(Preventivo.numero).all()
    return render_template("contratti/list.html", contratti=contratti,
                           compagnie=compagnie, stati=STATI_CONTRATTO,
                           compagnia_sel=compagnia, stato_sel=stato,
                           clienti=clienti, preventivi=preventivi)


@bp.route("/<int:contratto_id>")
def detail(contratto_id):
    c = Contratto.query.get_or_404(contratto_id)
    return render_template("contratti/detail.html", c=c)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:contratto_id>/modifica", methods=["GET", "POST"])
def form(contratto_id=None):
    c = Contratto.query.get_or_404(contratto_id) if contratto_id else None
    if request.method == "POST":
        f = request.form
        if c is None:
            c = Contratto()
            db.session.add(c)
        c.cliente_id = int(f["cliente_id"])
        c.preventivo_id = int(f["preventivo_id"]) if f.get("preventivo_id") else None
        c.compagnia_id = int(f["compagnia_id"]) if f.get("compagnia_id") else None
        c.numero_polizza = f.get("numero_polizza", "").strip()
        c.ramo = f.get("ramo", "").strip() or None
        c.premio = float(f.get("premio") or 0)
        c.data_emissione = parse_date(f.get("data_emissione"))
        c.data_scadenza = parse_date(f.get("data_scadenza"))
        c.stato = f.get("stato", "attivo")
        c.note = f.get("note", "").strip() or None
        db.session.commit()
        flash("Contratto salvato.", "success")
        return redirect(url_for("contratti.detail", contratto_id=c.id))
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    preventivi = Preventivo.query.order_by(Preventivo.numero).all()
    # Cliente pre-selezionato quando si crea "da scheda cliente" (?cliente_id=X)
    cliente_sel = request.args.get("cliente_id", type=int)
    return render_template("contratti/form.html", c=c, clienti=clienti,
                           compagnie=compagnie, preventivi=preventivi,
                           stati=STATI_CONTRATTO, cliente_sel=cliente_sel)


@bp.route("/<int:contratto_id>/elimina", methods=["POST"])
def elimina(contratto_id):
    c = Contratto.query.get_or_404(contratto_id)
    db.session.delete(c)
    db.session.commit()
    flash("Contratto eliminato.", "success")
    return redirect(url_for("contratti.index"))
