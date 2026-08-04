"""Appuntamenti: agenda leggera gestita dal dettaglio pratica e dalla scheda
cliente (nessuna pagina indice a sé). Il tipo "otp" copre l'appuntamento per la
firma/verifica OTP del flusso di lavorazione pratica.

Le azioni tornano sempre alla pagina di provenienza (campo hidden `next`), così
lo stesso set di route serve sia la scheda cliente sia il dettaglio pratica.
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, request, url_for

from extensions import db
from models import Appuntamento, Cliente, Pratica

bp = Blueprint("appuntamenti", __name__, url_prefix="/appuntamenti")


def _parse_data_ora(value):
    """Converte l'input HTML datetime-local ('aaaa-mm-ggThh:mm') in datetime."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def _torna_a():
    """URL di ritorno: il campo `next` del form, con fallback all'elenco pratiche."""
    return request.form.get("next") or url_for("pratiche.index")


@bp.route("/nuovo", methods=["POST"])
def nuovo():
    cliente_id = request.form.get("cliente_id", type=int)
    if not cliente_id or not Cliente.query.get(cliente_id):
        flash("Cliente non valido per l'appuntamento.", "error")
        return redirect(_torna_a())
    pratica_id = request.form.get("pratica_id", type=int)
    # La pratica è opzionale, ma se indicata deve esistere.
    if pratica_id and not Pratica.query.get(pratica_id):
        pratica_id = None
    try:
        db.session.add(Appuntamento(
            cliente_id=cliente_id,
            pratica_id=pratica_id,
            data_ora=_parse_data_ora(request.form.get("data_ora")),
            tipo=request.form.get("tipo", "").strip() or None,
            note=request.form.get("note", "").strip() or None,
        ))
        db.session.commit()
        flash("Appuntamento aggiunto.", "success")
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
    return redirect(_torna_a())


@bp.route("/<int:appuntamento_id>/esito", methods=["POST"])
def esito(appuntamento_id):
    a = Appuntamento.query.get_or_404(appuntamento_id)
    try:
        a.esito = request.form.get("esito", "").strip() or None
        db.session.commit()
        flash("Esito appuntamento aggiornato.", "success")
    except ValueError as e:
        db.session.rollback()
        flash(str(e), "error")
    return redirect(_torna_a())


@bp.route("/<int:appuntamento_id>/elimina", methods=["POST"])
def elimina(appuntamento_id):
    a = Appuntamento.query.get_or_404(appuntamento_id)
    db.session.delete(a)
    db.session.commit()
    flash("Appuntamento eliminato.", "success")
    return redirect(_torna_a())
