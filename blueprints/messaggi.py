"""Messaggistica WhatsApp / Email verso i clienti selezionati.

Nessuna API a pagamento: si generano link wa.me/<numero>?text=... e mailto:...
Per invii multipli il frontend apre i link in sequenza con conferma tra un
destinatario e l'altro (vedi static/js/app.js).
"""
import re

from flask import Blueprint, jsonify, request

from models import Cliente

bp = Blueprint("messaggi", __name__, url_prefix="/messaggi")


def _numero_intl(raw):
    """Normalizza un numero italiano per wa.me: solo cifre, prefisso 39."""
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if not digits:
        return None
    if digits.startswith("00"):
        digits = digits[2:]
    elif digits.startswith("3"):        # cellulare italiano senza prefisso
        digits = "39" + digits
    return digits


@bp.route("/destinatari", methods=["POST"])
def destinatari():
    """Dato un elenco di id cliente, restituisce i dati per comporre i link."""
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    out = []
    for c in Cliente.query.filter(Cliente.id.in_(ids)).all():
        out.append({
            "id": c.id,
            "nome": c.nome_completo,
            "wa": _numero_intl(c.cellulare or c.telefono),
            "email": c.email,
        })
    return jsonify(destinatari=out)
