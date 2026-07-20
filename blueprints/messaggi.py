"""Messaggistica WhatsApp / Email verso i clienti selezionati.

Nessuna API a pagamento: si generano link wa.me/<numero>?text=... e mailto:...
Per invii multipli il frontend apre i link in sequenza con conferma tra un
destinatario e l'altro (vedi static/js/app.js).

NB: un invio massivo REALE e automatizzato (senza aprire le schede una per una)
richiederebbe un backend di messaggistica dedicato — es. WhatsApp Business API
o un provider di email transazionale (SMTP / SendGrid / Mailgun). Trattandosi
di un'app locale mono-utente, qui ci limitiamo a generare i link cliccabili.
"""
import re

from flask import Blueprint, jsonify, request

from models import Cliente

bp = Blueprint("messaggi", __name__, url_prefix="/messaggi")


# Template messaggio preimpostati. Segnaposto supportato: {nome} (nome cliente),
# sostituito automaticamente lato client al momento dell'invio.
# Sono FISSI nel codice: la gestione CRUD dei template è una task futura separata
# (nessuna nuova tabella nel database per questa funzione).
MESSAGGI_TEMPLATES = [
    {"id": "libero", "label": "Messaggio libero", "testo": ""},
    {"id": "promemoria_polizza", "label": "Promemoria scadenza polizza",
     "testo": ("Gentile {nome}, le ricordiamo che la sua polizza è in "
               "scadenza. La invitiamo a contattarci per procedere al "
               "rinnovo. Cordiali saluti.")},
    {"id": "sollecito_pagamento", "label": "Sollecito pagamento",
     "testo": ("Gentile {nome}, le segnaliamo un pagamento ancora in "
               "sospeso. La preghiamo di regolarizzare la posizione o di "
               "contattarci per eventuali chiarimenti. Cordiali saluti.")},
    {"id": "preventivo_pronto", "label": "Preventivo pronto",
     "testo": ("Gentile {nome}, il preventivo da lei richiesto è pronto. "
               "Restiamo a disposizione per illustrarle tutti i dettagli. "
               "Cordiali saluti.")},
    {"id": "follow_up", "label": "Follow-up primo contatto",
     "testo": ("Gentile {nome}, la ricontattiamo a seguito del nostro primo "
               "contatto per capire come possiamo esserle utili. "
               "Cordiali saluti.")},
]


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


def _primo_nome(c):
    """Nome proprio del cliente per il segnaposto {nome} (fallback: completo)."""
    return (c.nome or c.nome_completo or "").strip()


@bp.route("/config")
def config():
    """Dati per costruire la modale messaggio: elenco clienti + template.

    Restituisce per ogni cliente i flag di disponibilità dei canali, così la
    lista di selezione può segnalare chi ha WhatsApp / email.
    """
    clienti = Cliente.query.order_by(Cliente.cognome, Cliente.nome).all()
    return jsonify(
        clienti=[{
            "id": c.id,
            "nome": c.nome_completo,
            "has_wa": bool(_numero_intl(c.cellulare or c.telefono)),
            "has_email": bool(c.email),
        } for c in clienti],
        templates=MESSAGGI_TEMPLATES,
    )


@bp.route("/destinatari", methods=["POST"])
def destinatari():
    """Dato un elenco di id cliente, restituisce i dati per comporre i link."""
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    out = []
    for c in Cliente.query.filter(Cliente.id.in_(ids)).all():
        out.append({
            "id": c.id,
            "nome": _primo_nome(c),          # per il segnaposto {nome}
            "nome_completo": c.nome_completo,  # per messaggi/conferme a video
            "wa": _numero_intl(c.cellulare or c.telefono),
            "email": c.email,
        })
    return jsonify(destinatari=out)
