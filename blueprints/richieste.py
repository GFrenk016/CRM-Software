"""Ingresso server-to-server per il modulo contatti esterno."""
import hmac

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Cliente, Lead

bp = Blueprint("richieste", __name__, url_prefix="/api/richieste")


@bp.post("/")
def crea_lead():
    expected = current_app.config.get("CRM_FORM_TOKEN", "")
    provided = request.headers.get("X-CRM-Form-Token", "")
    if not expected or not hmac.compare_digest(provided, expected):
        return jsonify(error="Non autorizzato"), 401
    if (request.content_length or 0) > 16_384 or not request.is_json:
        return jsonify(error="Inviare un JSON fino a 16 KB"), 400
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="JSON non valido"), 400

    def campo(key, limit):
        value = data.get(key, "")
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError(f"Campo {key} non valido")
        return value.strip()

    try:
        nome = campo("nome", 80)
        cognome = campo("cognome", 80)
        email = campo("email", 120)
        cellulare = campo("cellulare", 40)
        cf = campo("codice_fiscale", 16).upper()
        messaggio = campo("messaggio", 200)
        if not nome or not cognome or not (email or cellulare):
            raise ValueError("Nome, cognome e almeno un recapito sono obbligatori")
        if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
            raise ValueError("Email non valida")
        cliente = (Cliente.query.filter_by(codice_fiscale=cf).first() if cf else None)
        if cliente is None and email:
            cliente = Cliente.query.filter(func.lower(Cliente.email) == email.lower()).first()
        if cliente is not None and cf and cliente.codice_fiscale and cliente.codice_fiscale != cf:
            raise ValueError("Email già presente con un codice fiscale diverso")
        if cliente is not None and cliente.archiviato:
            raise ValueError("Cliente archiviato: verifica la scheda prima di riattivarlo")
        created = cliente is None
        if created:
            cliente = Cliente(nome=nome, cognome=cognome, email=email or None,
                              cellulare=cellulare or None, codice_fiscale=cf or None)
            db.session.add(cliente)
        # Un invio ripetuto riusa il lead: non duplica le card della Pipeline
        # né altera i dati o lo stadio di un cliente già lavorato.
        lead = cliente.lead[0] if not created and cliente.lead else None
        if lead is None:
            lead = Lead(cliente=cliente, stadio="nuovo", fonte="sito",
                        note=messaggio or None)
            db.session.add(lead)
        db.session.commit()
    except (ValueError, IntegrityError) as error:
        db.session.rollback()
        return jsonify(error=str(error) if isinstance(error, ValueError)
                       else "Codice fiscale già presente: verifica i dati"), 400
    return jsonify(cliente_id=cliente.id, codice_cliente=cliente.codice_cliente,
                   lead_id=lead.id, created=created), 201 if created else 200
