"""Bacheca / Dashboard: KPI calcolati da query reali sul database."""
from datetime import date, timedelta

from flask import Blueprint, render_template
from sqlalchemy import func

from extensions import db
from models import (STADI_LEAD, Cliente, Contratto, Incasso, Lead, Preventivo,
                    Sinistro)

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def index():
    # Valore pipeline = somma valore stimato dei lead ancora aperti
    aperti = ["nuovo", "contattato", "qualificato", "proposta"]
    valore_pipeline = db.session.query(
        func.coalesce(func.sum(Lead.valore_stimato), 0)
    ).filter(Lead.stadio.in_(aperti)).scalar()

    tot_lead = db.session.query(func.count(Lead.id)).scalar()
    vinti = db.session.query(func.count(Lead.id)).filter(Lead.stadio == "vinto").scalar()
    persi = db.session.query(func.count(Lead.id)).filter(Lead.stadio == "perso").scalar()
    chiusi = vinti + persi
    conversione = round((vinti / chiusi) * 100) if chiusi else 0

    # Distribuzione per stadio
    per_stadio_raw = dict(
        db.session.query(Lead.stadio, func.count(Lead.id))
        .group_by(Lead.stadio).all()
    )
    per_stadio = [(s, per_stadio_raw.get(s, 0)) for s in STADI_LEAD]
    max_stadio = max([n for _, n in per_stadio] + [1])

    # Distribuzione per fonte
    per_fonte = (
        db.session.query(Lead.fonte, func.count(Lead.id))
        .group_by(Lead.fonte).order_by(func.count(Lead.id).desc()).all()
    )

    # Contatori operativi
    n_clienti = db.session.query(func.count(Cliente.id)).scalar()
    n_contratti = db.session.query(func.count(Contratto.id)).filter(
        Contratto.stato == "attivo").scalar()
    n_preventivi = db.session.query(func.count(Preventivo.id)).scalar()
    n_sinistri_aperti = db.session.query(func.count(Sinistro.id)).filter(
        Sinistro.stato != "chiuso").scalar()

    # Scadenze entro 30 giorni (derivate dai contratti attivi)
    entro = date.today() + timedelta(days=30)
    scadenze_30 = db.session.query(func.count(Contratto.id)).filter(
        Contratto.stato == "attivo",
        Contratto.data_scadenza != None,          # noqa: E711
        Contratto.data_scadenza <= entro,
        Contratto.data_scadenza >= date.today(),
    ).scalar()

    # Incassi da riscuotere / in ritardo
    da_incassare = db.session.query(
        func.coalesce(func.sum(Incasso.importo), 0)
    ).filter(Incasso.data_incasso == None).scalar()          # noqa: E711
    in_ritardo = db.session.query(func.count(Incasso.id)).filter(
        Incasso.data_incasso == None,                        # noqa: E711
        Incasso.data_prevista < date.today(),
    ).scalar()

    return render_template(
        "dashboard.html",
        valore_pipeline=valore_pipeline, tot_lead=tot_lead,
        conversione=conversione, vinti=vinti,
        per_stadio=per_stadio, max_stadio=max_stadio, per_fonte=per_fonte,
        n_clienti=n_clienti, n_contratti=n_contratti, n_preventivi=n_preventivi,
        n_sinistri_aperti=n_sinistri_aperti, scadenze_30=scadenze_30,
        da_incassare=da_incassare, in_ritardo=in_ritardo,
    )
