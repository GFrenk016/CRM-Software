"""Registro incassi / provvigioni: board stile Monday con celle colorate."""
from datetime import date

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)

from extensions import db
from models import STATI_INCASSO, Cliente, Contratto, Incasso
from utils import parse_date

bp = Blueprint("incassi", __name__, url_prefix="/incassi")


def _sync_stato(inc):
    """Allinea lo stato ai dati (incassato se c'è data incasso, in ritardo se scaduto)."""
    inc.stato = inc.stato_effettivo()


@bp.route("/")
def index():
    stato = (request.args.get("stato") or "").strip()
    incassi = Incasso.query.all()
    # ricalcolo "in ritardo" al volo rispetto a oggi
    for inc in incassi:
        nuovo = inc.stato_effettivo()
        if inc.stato != nuovo:
            inc.stato = nuovo
    db.session.commit()

    if stato:
        incassi = [i for i in incassi if i.stato == stato]
    incassi.sort(key=lambda i: (i.data_prevista or date.max))

    totali = {
        "da_incassare": sum(i.importo for i in Incasso.query.filter_by(stato="da_incassare")),
        "in_ritardo": sum(i.importo for i in Incasso.query.filter_by(stato="in_ritardo")),
        "incassato": sum(i.importo for i in Incasso.query.filter_by(stato="incassato")),
    }
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    contratti = Contratto.query.order_by(Contratto.numero_polizza).all()
    # Cliente pre-selezionato quando si arriva "da scheda cliente" (?cliente_id=X):
    # la board apre in automatico la modale di nuovo incasso col cliente scelto.
    cliente_sel = request.args.get("cliente_id", type=int)
    return render_template("incassi/board.html", incassi=incassi, totali=totali,
                           stati=STATI_INCASSO, stato_sel=stato,
                           clienti=clienti, contratti=contratti,
                           cliente_sel=cliente_sel)


@bp.route("/<int:inc_id>/stato", methods=["POST"])
def cambia_stato(inc_id):
    """Endpoint JSON: click su una cella di stato nella board Monday-style."""
    inc = Incasso.query.get_or_404(inc_id)
    payload = request.get_json(silent=True) or {}
    nuovo = payload.get("stato")
    if nuovo not in STATI_INCASSO:
        return jsonify(ok=False), 400
    inc.stato = nuovo
    # Coerenza date <-> stato
    if nuovo == "incassato" and not inc.data_incasso:
        inc.data_incasso = date.today()
    if nuovo != "incassato":
        inc.data_incasso = None
    db.session.commit()
    return jsonify(ok=True, stato=inc.stato,
                   data_incasso=inc.data_incasso.strftime("%d/%m/%Y")
                   if inc.data_incasso else None)


@bp.route("/nuovo", methods=["POST"])
@bp.route("/<int:inc_id>/modifica", methods=["POST"])
def salva(inc_id=None):
    f = request.form
    inc = Incasso.query.get_or_404(inc_id) if inc_id else Incasso()
    if inc_id is None:
        db.session.add(inc)
    inc.cliente_id = int(f["cliente_id"])
    inc.contratto_id = int(f["contratto_id"])
    inc.descrizione = f.get("descrizione", "").strip() or None
    inc.importo = float(f.get("importo") or 0)
    inc.data_prevista = parse_date(f.get("data_prevista"))
    inc.data_incasso = parse_date(f.get("data_incasso"))
    _sync_stato(inc)
    db.session.commit()
    flash("Incasso salvato.", "success")
    return redirect(url_for("incassi.index"))


@bp.route("/<int:inc_id>/elimina", methods=["POST"])
def elimina(inc_id):
    inc = Incasso.query.get_or_404(inc_id)
    db.session.delete(inc)
    db.session.commit()
    flash("Incasso eliminato.", "success")
    return redirect(url_for("incassi.index"))
