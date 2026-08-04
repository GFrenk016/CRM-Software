"""Entrypoint dell'applicazione CRM.

Avvio in locale:
    pip install -r requirements.txt
    python app.py
Poi apri il browser su http://localhost:5000
"""
import os

from flask import Flask
from flask_migrate import Migrate, upgrade
from sqlalchemy import inspect

from config import Config
from extensions import db

# Estensione di migrazione condivisa (schema gestito da Alembic/Flask-Migrate).
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Cartella upload garantita
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    # I modelli vanno importati prima di init_app di Migrate, così Alembic li
    # "vede" in fase di autogenerate.
    import models  # noqa: F401
    migrate.init_app(app, db)

    # Registrazione blueprint (una sezione per modulo)
    from blueprints.dashboard import bp as dashboard_bp
    from blueprints.clienti import bp as clienti_bp
    from blueprints.pipeline import bp as pipeline_bp
    from blueprints.pratiche import bp as pratiche_bp
    from blueprints.preventivi import bp as preventivi_bp
    from blueprints.contratti import bp as contratti_bp
    from blueprints.scadenze import bp as scadenze_bp
    from blueprints.sinistri import bp as sinistri_bp
    from blueprints.incassi import bp as incassi_bp
    from blueprints.compagnie import bp as compagnie_bp
    from blueprints.compliance import bp as compliance_bp
    from blueprints.documenti import bp as documenti_bp
    from blueprints.messaggi import bp as messaggi_bp
    from blueprints.appuntamenti import bp as appuntamenti_bp
    from blueprints.impostazioni import bp as impostazioni_bp

    for bp in (dashboard_bp, clienti_bp, pipeline_bp, pratiche_bp, preventivi_bp,
               contratti_bp, scadenze_bp, sinistri_bp, incassi_bp, compagnie_bp,
               compliance_bp, documenti_bp, messaggi_bp, appuntamenti_bp,
               impostazioni_bp):
        app.register_blueprint(bp)

    # Filtri Jinja utili in tutte le pagine
    from utils import register_template_helpers
    register_template_helpers(app)

    # Schema allineato tramite migrazioni + seed al primo avvio.
    # Le migrazioni Alembic sono la fonte di verità dello schema: su un DB nuovo
    # (o su Render) `upgrade()` crea tutte le tabelle fino alla revisione head.
    # Durante i comandi `flask db ...` (generazione migrazioni) si salta questo
    # blocco impostando CRM_SKIP_STARTUP_UPGRADE=1, per non innescare upgrade/seed.
    if os.environ.get("CRM_SKIP_STARTUP_UPGRADE"):
        return app

    with app.app_context():
        insp = inspect(db.engine)
        tabelle = insp.get_table_names()
        if tabelle and "alembic_version" not in tabelle:
            # DB legacy creato con il vecchio db.create_all() (solo dati fittizi
            # di seed): va rimosso una volta per adottare le migrazioni. Vedi
            # bugfixes.md. Evitiamo un upgrade() che fallirebbe su tabelle già
            # esistenti e lasciamo comunque partire l'app.
            app.logger.warning(
                "DB pre-migrazioni rilevato: elimina crm.db per adottare "
                "Flask-Migrate (contiene solo dati di esempio)."
            )
        else:
            upgrade()
            from seed import seed
            seed()

    return app


app = create_app()


if __name__ == "__main__":
    # host locale, un solo utente: niente esposizione in rete.
    app.run(host="127.0.0.1", port=5000, debug=True)
