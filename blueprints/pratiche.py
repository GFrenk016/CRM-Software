"""Pratiche: unità di lavoro operativa collegata a cliente/contratto/sinistro."""
from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import (STATI_PRATICA, Cliente, Contratto, Lead, Pratica,
                    PrioritaPratica, Sinistro, TipologiaPratica)

bp = Blueprint("pratiche", __name__, url_prefix="/pratiche")


@bp.route("/")
def index():
    stato = (request.args.get("stato") or "").strip()
    priorita = (request.args.get("priorita") or "").strip()
    tipologia = (request.args.get("tipologia") or "").strip()

    q = Pratica.query
    if stato:
        q = q.filter_by(stato=stato)
    if priorita:
        q = q.filter_by(priorita=priorita)
    if tipologia:
        q = q.filter_by(tipologia=tipologia)
    pratiche = q.order_by(Pratica.data_apertura.desc()).all()

    conteggi = {s: Pratica.query.filter_by(stato=s).count() for s in STATI_PRATICA}

    # Dati per i <select> del modale "Nuova pratica"
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    lead = Lead.query.all()
    contratti = Contratto.query.order_by(Contratto.numero_polizza).all()
    sinistri = Sinistro.query.order_by(Sinistro.numero).all()

    return render_template(
        "pratiche/list.html", pratiche=pratiche, stati=STATI_PRATICA,
        stato_sel=stato, priorita_sel=priorita, tipologia_sel=tipologia,
        conteggi=conteggi, clienti=clienti, lead=lead, contratti=contratti,
        sinistri=sinistri, priorita_opts=PrioritaPratica,
        tipologia_opts=TipologiaPratica,
    )


@bp.route("/<int:pratica_id>")
def detail(pratica_id):
    """Scheda della singola pratica: è la pagina dove vive tutta la lavorazione
    (avanzamento, documenti, appuntamenti, comunicazioni, preventivi collegati).
    Da qui passeranno gli automatismi e il flusso guidato degli step successivi.
    """
    p = Pratica.query.get_or_404(pratica_id)
    return render_template("pratiche/detail.html", p=p)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:pratica_id>/modifica", methods=["GET", "POST"])
def form(pratica_id=None):
    p = Pratica.query.get_or_404(pratica_id) if pratica_id else None
    if request.method == "POST":
        f = request.form
        try:
            if p is None:
                p = Pratica(cliente_id=int(f["cliente_id"]),
                           tipologia=f["tipologia"])
                db.session.add(p)
            else:
                p.cliente_id = int(f["cliente_id"])
                p.tipologia = f["tipologia"]
            p.contratto_id = int(f["contratto_id"]) if f.get("contratto_id") else None
            p.sinistro_id = int(f["sinistro_id"]) if f.get("sinistro_id") else None
            p.lead_id = int(f["lead_id"]) if f.get("lead_id") else None
            p.stato = f.get("stato", "aperta")
            p.priorita = f.get("priorita", PrioritaPratica.MEDIA.value)
            p.operatore = f.get("operatore", "").strip() or None
            p.note = f.get("note", "").strip() or None
            db.session.commit()
            flash("Pratica salvata.", "success")
            return redirect(url_for("pratiche.index"))
        except ValueError as e:
            db.session.rollback()
            flash(str(e), "error")

    clienti = Cliente.query.order_by(Cliente.cognome).all()
    lead = Lead.query.all()
    contratti = Contratto.query.order_by(Contratto.numero_polizza).all()
    sinistri = Sinistro.query.order_by(Sinistro.numero).all()
    cliente_sel = request.args.get("cliente_id", type=int)
    return render_template(
        "pratiche/form.html", p=p, clienti=clienti, lead=lead, contratti=contratti,
        sinistri=sinistri, stati=STATI_PRATICA, priorita_opts=PrioritaPratica,
        tipologia_opts=TipologiaPratica, cliente_sel=cliente_sel,
    )


@bp.route("/<int:pratica_id>/elimina", methods=["POST"])
def elimina(pratica_id):
    p = Pratica.query.get_or_404(pratica_id)
    db.session.delete(p)
    db.session.commit()
    flash("Pratica eliminata.", "success")
    return redirect(url_for("pratiche.index"))
