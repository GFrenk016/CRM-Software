"""Preventivi: vista distinta dai contratti. Un preventivo accettato può
generare un contratto attivo collegato (link all'origine)."""
from datetime import date

from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import (STATI_PREVENTIVO, Cliente, Compagnia, Contratto, Lead,
                    Preventivo, Veicolo)
from utils import parse_date

bp = Blueprint("preventivi", __name__, url_prefix="/preventivi")


def _prossimo_numero():
    n = Preventivo.query.count() + 1
    return f"PRV-{n:04d}"


def _scadenza_riferimento(prev):
    """Scadenza a cui ordinare un preventivo: la più vicina tra i contratti
    ATTIVI del suo cliente.

    Il Preventivo NON ha una data di scadenza propria (un preventivo non "scade"
    come una polizza): la si risale dal cliente → contratti attivi →
    data_scadenza. Ritorna None se il cliente non ha contratti attivi datati.
    """
    scadenze = [k.data_scadenza for k in prev.cliente.contratti
                if k.stato == "attivo" and k.data_scadenza]
    return min(scadenze) if scadenze else None


@bp.route("/")
def index():
    stato = (request.args.get("stato") or "").strip()
    ordina = (request.args.get("ordina") or "").strip()
    q = Preventivo.query
    if stato:
        q = q.filter_by(stato=stato)
    if ordina == "scadenza":
        # Ordinamento per scadenza della polizza attuale del cliente, crescente,
        # con i preventivi senza scadenza in fondo. Si risale via relazione
        # (vedi _scadenza_riferimento), quindi si ordina in Python: None-last si
        # ottiene con una chiave-tupla (prima il flag "senza scadenza").
        preventivi = q.all()
        preventivi.sort(key=lambda p: (_scadenza_riferimento(p) is None,
                                       _scadenza_riferimento(p) or date.max))
    else:
        preventivi = q.order_by(Preventivo.created_at.desc()).all()
    # Dati per i <select> del modale "Nuovo preventivo"
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    lead = Lead.query.all()
    veicoli = Veicolo.query.all()
    # Scadenza di riferimento per riga (derivata dai contratti attivi del
    # cliente): mostrata in colonna così l'ordinamento è leggibile.
    scadenze_rif = {p.id: _scadenza_riferimento(p) for p in preventivi}
    return render_template("preventivi/list.html", preventivi=preventivi,
                           stati=STATI_PREVENTIVO, stato_sel=stato,
                           ordina_sel=ordina, scadenze_rif=scadenze_rif,
                           clienti=clienti, compagnie=compagnie, lead=lead,
                           veicoli=veicoli)


@bp.route("/nuovo", methods=["GET", "POST"])
@bp.route("/<int:prev_id>/modifica", methods=["GET", "POST"])
def form(prev_id=None):
    prev = Preventivo.query.get_or_404(prev_id) if prev_id else None
    if request.method == "POST":
        f = request.form
        if prev is None:
            prev = Preventivo(numero=_prossimo_numero())
            db.session.add(prev)
        prev.cliente_id = int(f["cliente_id"])
        prev.lead_id = int(f["lead_id"]) if f.get("lead_id") else None
        prev.compagnia_id = int(f["compagnia_id"]) if f.get("compagnia_id") else None
        prev.veicolo_id = int(f["veicolo_id"]) if f.get("veicolo_id") else None
        prev.oggetto = f.get("oggetto", "").strip() or None
        prev.premio_proposto = float(f.get("premio_proposto") or 0)
        prev.stato = f.get("stato", "bozza")
        prev.data_invio = parse_date(f.get("data_invio"))
        db.session.commit()
        flash("Preventivo salvato.", "success")
        return redirect(url_for("preventivi.index"))
    clienti = Cliente.query.order_by(Cliente.cognome).all()
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    lead = Lead.query.all()
    veicoli = Veicolo.query.all()
    # Cliente pre-selezionato quando si crea "da scheda cliente" (?cliente_id=X)
    cliente_sel = request.args.get("cliente_id", type=int)
    return render_template("preventivi/form.html", p=prev, clienti=clienti,
                           compagnie=compagnie, lead=lead, veicoli=veicoli,
                           stati=STATI_PREVENTIVO, cliente_sel=cliente_sel)


@bp.route("/<int:prev_id>/converti", methods=["POST"])
def converti(prev_id):
    """Genera un contratto attivo a partire da un preventivo accettato."""
    prev = Preventivo.query.get_or_404(prev_id)
    if prev.contratto:
        flash("Questo preventivo ha già un contratto collegato.", "error")
        return redirect(url_for("contratti.detail", contratto_id=prev.contratto.id))
    prev.stato = "accettato"
    contratto = Contratto(
        cliente_id=prev.cliente_id,
        preventivo_id=prev.id,
        compagnia_id=prev.compagnia_id,
        numero_polizza=f"POL-DA-{prev.numero}",
        ramo=prev.oggetto,
        premio=prev.premio_proposto,
        data_emissione=date.today(),
        stato="attivo",
    )
    db.session.add(contratto)
    db.session.commit()
    flash("Contratto generato dal preventivo. Completa numero polizza e scadenza.",
          "success")
    return redirect(url_for("contratti.form", contratto_id=contratto.id))


@bp.route("/<int:prev_id>/elimina", methods=["POST"])
def elimina(prev_id):
    prev = Preventivo.query.get_or_404(prev_id)
    db.session.delete(prev)
    db.session.commit()
    flash("Preventivo eliminato.", "success")
    return redirect(url_for("preventivi.index"))
