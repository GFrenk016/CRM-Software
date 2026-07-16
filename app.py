"""Entrypoint dell'applicazione CRM.

Avvio in locale:
    pip install -r requirements.txt
    python app.py
Poi apri il browser su http://localhost:5000
"""
import os

from flask import Flask

from config import Config
from extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Cartella upload garantita
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)

    # Registrazione blueprint (una sezione per modulo)
    from blueprints.dashboard import bp as dashboard_bp
    from blueprints.clienti import bp as clienti_bp
    from blueprints.pipeline import bp as pipeline_bp
    from blueprints.preventivi import bp as preventivi_bp
    from blueprints.contratti import bp as contratti_bp
    from blueprints.scadenze import bp as scadenze_bp
    from blueprints.sinistri import bp as sinistri_bp
    from blueprints.incassi import bp as incassi_bp
    from blueprints.compagnie import bp as compagnie_bp
    from blueprints.compliance import bp as compliance_bp
    from blueprints.documenti import bp as documenti_bp
    from blueprints.messaggi import bp as messaggi_bp

    for bp in (dashboard_bp, clienti_bp, pipeline_bp, preventivi_bp, contratti_bp,
               scadenze_bp, sinistri_bp, incassi_bp, compagnie_bp, compliance_bp,
               documenti_bp, messaggi_bp):
        app.register_blueprint(bp)

    # Filtri Jinja utili in tutte le pagine
    from utils import register_template_helpers
    register_template_helpers(app)

    # Creazione tabelle + seed al primo avvio
    with app.app_context():
        db.create_all()
        from seed import seed
        seed()

    return app


app = create_app()


if __name__ == "__main__":
    # host locale, un solo utente: niente esposizione in rete.
    app.run(host="127.0.0.1", port=5000, debug=True)
