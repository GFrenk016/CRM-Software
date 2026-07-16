"""Scadenziario / Rinnovi: DERIVATO dai contratti attivi in scadenza.

Non è una tabella a sé: è una query sui contratti con data_scadenza filtrabile
per finestra temporale. Il rinnovo si gestisce aggiornando il contratto.
"""
from datetime import date, timedelta

from flask import Blueprint, render_template, request

from models import Compagnia, Contratto

bp = Blueprint("scadenze", __name__, url_prefix="/scadenze")


@bp.route("/")
def index():
    # Finestra selezionabile: prossimi N giorni (default 60), o scadute.
    finestra = request.args.get("finestra", "60")
    compagnia = (request.args.get("compagnia") or "").strip()

    q = Contratto.query.filter(
        Contratto.stato == "attivo",
        Contratto.data_scadenza != None,               # noqa: E711
    )
    if compagnia:
        q = q.filter(Contratto.compagnia_id == int(compagnia))

    oggi = date.today()
    if finestra == "scadute":
        q = q.filter(Contratto.data_scadenza < oggi)
    else:
        giorni = int(finestra) if finestra.isdigit() else 60
        q = q.filter(
            Contratto.data_scadenza >= oggi,
            Contratto.data_scadenza <= oggi + timedelta(days=giorni),
        )

    contratti = q.order_by(Contratto.data_scadenza).all()
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    return render_template("scadenze/list.html", contratti=contratti,
                           compagnie=compagnie, finestra=finestra,
                           compagnia_sel=compagnia)
