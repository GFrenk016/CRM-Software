"""Funzioni di supporto: formattazione per i template e helper filtri SQL."""
from datetime import date, datetime


def eur(value):
    """Formatta un importo in stile italiano: 1.234,50 €."""
    try:
        v = float(value or 0)
    except (TypeError, ValueError):
        return "—"
    s = f"{v:,.2f}"                     # 1,234.50
    s = s.replace(",", "§").replace(".", ",").replace("§", ".")
    return f"€ {s}"


def data_it(value):
    """Formatta una data come gg/mm/aaaa."""
    if not value:
        return "—"
    if isinstance(value, datetime):
        value = value.date()
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    return str(value)


def parse_date(value):
    """Converte 'aaaa-mm-gg' (input HTML date) in oggetto date, o None."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def register_template_helpers(app):
    app.jinja_env.filters["eur"] = eur
    app.jinja_env.filters["data_it"] = data_it

    @app.context_processor
    def inject_globals():
        # Voci di navigazione della sidebar (label, endpoint, icona)
        nav = [
            ("Bacheca", "dashboard.index", "grid"),
            ("Pipeline", "pipeline.index", "kanban"),
            ("Anagrafica", "clienti.index", "users"),
            ("Preventivi", "preventivi.index", "file-text"),
            ("Contratti", "contratti.index", "shield"),
            ("Scadenziario", "scadenze.index", "calendar"),
            ("Sinistri", "sinistri.index", "alert"),
            ("Incassi", "incassi.index", "wallet"),
            ("Compagnie", "compagnie.index", "building"),
            ("Compliance", "compliance.index", "check-shield"),
        ]
        return {"NAV_ITEMS": nav, "oggi": date.today()}
