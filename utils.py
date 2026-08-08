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


def rendi_form(pagina_template, campi_template, titolo, **ctx):
    """Serve lo stesso form come pagina piena o come frammento per il pannello.

    Con ?modal=1 restituisce solo header + campi, da iniettare in #modal-body
    (lo fa apriFormModale in app.js). Senza, la solita pagina che estende
    base.html. In entrambi i casi i campi vengono dallo STESSO partial, così
    non possono divergere: prima ogni sezione aveva il form duplicato fra la
    pagina di modifica e il <template> del modale "nuovo", e le due copie erano
    già fuori sincrono.

    `in_modal` finisce nel contesto: serve ai campi per decidere se "Annulla"
    chiude il pannello o torna all'elenco.
    """
    from flask import render_template, request
    in_modal = request.args.get("modal") == "1"
    ctx.update(campi_template=campi_template, titolo=titolo, in_modal=in_modal)
    if in_modal:
        return render_template("_form_modale.html", **ctx)
    return render_template(pagina_template, **ctx)


def register_template_helpers(app):
    app.jinja_env.filters["eur"] = eur
    app.jinja_env.filters["data_it"] = data_it

    @app.context_processor
    def inject_globals():
        # Voci di navigazione della sidebar (label, endpoint, icona)
        nav = [
            ("Bacheca", "dashboard.index", "grid"),
            ("Pipeline", "pipeline.index", "kanban"),
            ("Pratiche", "pratiche.index", "inbox"),
            ("Anagrafica", "clienti.index", "users"),
            # Vista aggregata a partire dal codice fiscale: sta accanto
            # all'anagrafica perché è il modo alternativo di arrivare al cliente.
            ("Ricerca CF", "ricerca.index", "search"),
            ("Preventivi", "preventivi.index", "file-text"),
            ("Contratti", "contratti.index", "shield"),
            ("Scadenziario", "scadenze.index", "calendar"),
            ("Sinistri", "sinistri.index", "alert"),
            ("Incassi", "incassi.index", "wallet"),
            ("Compagnie", "compagnie.index", "building"),
            ("Compliance", "compliance.index", "check-shield"),
            ("Impostazioni", "impostazioni.index", "settings"),
        ]
        return {"NAV_ITEMS": nav, "oggi": date.today()}
