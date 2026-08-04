"""Impostazioni agenzia: pagina di modifica dell'unica riga (ragione sociale,
IBAN, orari delle due finestre di emissione).

Senza questa pagina lo step "invio IBAN" del flusso non avrebbe nulla da
leggere: l'accesso passa sempre da get_impostazioni() (crea la riga se assente).
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import get_impostazioni

bp = Blueprint("impostazioni", __name__, url_prefix="/impostazioni")


def _parse_ora(value):
    """Converte l'input HTML time ('hh:mm') in oggetto time, o None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


@bp.route("/", methods=["GET", "POST"])
def index():
    imp = get_impostazioni()
    if request.method == "POST":
        f = request.form
        imp.ragione_sociale = f.get("ragione_sociale", "").strip() or None
        imp.iban = f.get("iban", "").strip().replace(" ", "").upper() or None
        # Orari delle due finestre: se un campo è vuoto resta None (finestra non
        # configurata) e in_finestra_emissione la ignora.
        imp.finestra1_inizio = _parse_ora(f.get("finestra1_inizio"))
        imp.finestra1_fine = _parse_ora(f.get("finestra1_fine"))
        imp.finestra2_inizio = _parse_ora(f.get("finestra2_inizio"))
        imp.finestra2_fine = _parse_ora(f.get("finestra2_fine"))
        db.session.commit()
        flash("Impostazioni salvate.", "success")
        return redirect(url_for("impostazioni.index"))
    return render_template("impostazioni/form.html", imp=imp)
