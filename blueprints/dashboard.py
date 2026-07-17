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

    # ----------------------------------------------------------------------- #
    #  Urgenze operative: liste azionabili (CHI/QUANTO è urgente + link)       #
    # ----------------------------------------------------------------------- #
    oggi = date.today()
    LIMITE = 5

    # 1) Scadenze in arrivo: contratti attivi che scadono nei prossimi 30 gg
    scadenze_q = Contratto.query.filter(
        Contratto.stato == "attivo",
        Contratto.data_scadenza != None,          # noqa: E711
        Contratto.data_scadenza >= oggi,
        Contratto.data_scadenza <= oggi + timedelta(days=30),
    ).order_by(Contratto.data_scadenza.asc())
    urg_scadenze = scadenze_q.limit(LIMITE).all()
    urg_scadenze_tot = scadenze_q.count()

    # 2) Incassi in ritardo: non incassati con data prevista già passata
    incassi_q = Incasso.query.filter(
        Incasso.data_incasso == None,             # noqa: E711
        Incasso.data_prevista != None,            # noqa: E711
        Incasso.data_prevista < oggi,
    ).order_by(Incasso.data_prevista.asc())
    urg_incassi = incassi_q.limit(LIMITE).all()
    urg_incassi_tot = incassi_q.count()
    # Giorni di ritardo calcolati lato Python (niente logica di date nel template)
    ritardi = {i.id: (oggi - i.data_prevista).days for i in urg_incassi}

    # 3) Sinistri aperti: tutti quelli non ancora chiusi
    sinistri_q = Sinistro.query.filter(
        Sinistro.stato != "chiuso"
    ).order_by(Sinistro.data_apertura.asc())
    urg_sinistri = sinistri_q.limit(LIMITE).all()
    urg_sinistri_tot = sinistri_q.count()

    return render_template(
        "dashboard.html",
        valore_pipeline=valore_pipeline, tot_lead=tot_lead,
        conversione=conversione, vinti=vinti,
        per_stadio=per_stadio, max_stadio=max_stadio, per_fonte=per_fonte,
        n_clienti=n_clienti, n_contratti=n_contratti, n_preventivi=n_preventivi,
        n_sinistri_aperti=n_sinistri_aperti, scadenze_30=scadenze_30,
        da_incassare=da_incassare, in_ritardo=in_ritardo,
        oggi=oggi,
        urg_scadenze=urg_scadenze, urg_scadenze_tot=urg_scadenze_tot,
        urg_incassi=urg_incassi, urg_incassi_tot=urg_incassi_tot,
        ritardi=ritardi,
        urg_sinistri=urg_sinistri, urg_sinistri_tot=urg_sinistri_tot,
        limite_urgenze=LIMITE,
    )
