"""Pipeline commerciale: vista kanban con drag & drop persistito nel DB."""
from datetime import datetime

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)

from extensions import db
from models import (FONTI_LEAD, STADI_LEAD, Cliente, Lead)
from utils import parse_date

bp = Blueprint("pipeline", __name__, url_prefix="/pipeline")

COLORI_STADIO = {
    "nuovo": "#8b91a8", "contattato": "#4f8ef7", "qualificato": "#a855f7",
    "proposta": "#f7b24f", "vinto": "#34d17a", "perso": "#f7524f",
}


@bp.route("/")
def index():
    colonne = []
    for stadio in STADI_LEAD:
        leads = (Lead.query.filter_by(stadio=stadio)
                 .order_by(Lead.stadio_updated_at.desc()).all())
        colonne.append((stadio, COLORI_STADIO[stadio], leads))
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    return render_template("lead/pipeline.html", colonne=colonne, clienti=clienti,
                           fonti=FONTI_LEAD, stadi=STADI_LEAD)


@bp.route("/sposta", methods=["POST"])
def sposta():
    """Endpoint JSON chiamato dal drag & drop: aggiorna lo stadio nel DB."""
    payload = request.get_json(silent=True) or {}
    lead = Lead.query.get(payload.get("lead_id"))
    nuovo = payload.get("stadio")
    if not lead or nuovo not in STADI_LEAD:
        return jsonify(ok=False, error="dati non validi"), 400
    if lead.stadio != nuovo:
        lead.stadio = nuovo
        lead.stadio_updated_at = datetime.utcnow()
        db.session.commit()
    return jsonify(ok=True, lead_id=lead.id, stadio=nuovo,
                   punteggio=lead.punteggio)


@bp.route("/nuovo", methods=["POST"])
@bp.route("/<int:lead_id>/modifica", methods=["POST"])
def salva(lead_id=None):
    form = request.form
    lead = Lead.query.get_or_404(lead_id) if lead_id else Lead()
    if lead_id is None:
        db.session.add(lead)
    lead.cliente_id = int(form["cliente_id"])
    lead.stadio = form.get("stadio", "nuovo")
    lead.fonte = form.get("fonte", "altro")
    lead.valore_stimato = float(form.get("valore_stimato") or 0)
    lead.prossima_azione = form.get("prossima_azione", "").strip() or None
    lead.data_prossima_azione = parse_date(form.get("data_prossima_azione"))
    if lead_id is None:
        lead.stadio_updated_at = datetime.utcnow()
    db.session.commit()
    flash("Lead salvato.", "success")
    return redirect(url_for("pipeline.index"))


@bp.route("/<int:lead_id>/elimina", methods=["POST"])
def elimina(lead_id):
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    flash("Lead eliminato.", "success")
    return redirect(url_for("pipeline.index"))
