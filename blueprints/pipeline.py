"""Pipeline commerciale: vista kanban con drag & drop persistito nel DB."""
from datetime import datetime

from flask import (Blueprint, flash, jsonify, redirect, render_template,
                   request, url_for)

from extensions import db
from models import (STADI_LEAD, Cliente, Lead)
from utils import parse_date

bp = Blueprint("pipeline", __name__, url_prefix="/pipeline")

COLORI_STADIO = {
    "nuovo": "#8b91a8", "contattato": "#4f8ef7", "qualificato": "#a855f7",
    "proposta": "#f7b24f", "vinto": "#34d17a", "perso": "#f7524f",
}


def _allinea_anagrafica():
    """Garantisce l'invariante 'ogni cliente ATTIVO ha un lead in pipeline'.

    La creazione del lead avviene già in clienti.form (nuovo cliente -> nuovo
    lead) e l'eliminazione avviene per cascade quando si elimina il cliente.
    Questa funzione è la rete di sicurezza per i clienti che quel percorso non
    l'hanno mai attraversato: dati di seed, righe importate, clienti creati
    prima che la regola esistesse. Senza, resterebbero invisibili in pipeline.

    Gli archiviati sono esclusi di proposito: se ne creassimo il lead, tornare
    sulla pipeline li rimetterebbe in board subito dopo averli archiviati.
    Il lead di un cliente archiviato NON viene cancellato, resta nel suo stadio
    e ricompare intatto al ripristino.

    Fa una sola query e scrive solo se c'è davvero qualcosa da recuperare.
    """
    orfani = (Cliente.query
              .outerjoin(Lead, Lead.cliente_id == Cliente.id)
              .filter(Lead.id.is_(None), Cliente.archiviato.is_(False))
              .all())
    if not orfani:
        return
    for cliente in orfani:
        db.session.add(Lead(cliente=cliente, stadio=STADI_LEAD[0],
                            fonte="altro", stadio_updated_at=datetime.utcnow()))
    db.session.commit()


@bp.route("/")
def index():
    _allinea_anagrafica()
    colonne = []
    for stadio in STADI_LEAD:
        # join su Cliente: se in DB restasse un lead senza cliente (cancellazione
        # fatta a mano in SQL, fuori dall'ORM), la card esploderebbe sul template
        # a l.cliente.nome_completo. Con la join quel lead viene semplicemente
        # ignorato invece di rompere la pagina. Lo stesso join filtra via i
        # clienti archiviati, che non devono ingombrare la board.
        leads = (Lead.query.filter_by(stadio=stadio)
                 .join(Cliente)
                 .filter(Cliente.archiviato.is_(False))
                 .order_by(Lead.stadio_updated_at.desc()).all())
        colonne.append((stadio, COLORI_STADIO[stadio], leads))
    return render_template("lead/pipeline.html", colonne=colonne)


@bp.route("/sposta", methods=["POST"])
def sposta():
    """Endpoint JSON chiamato dal drag & drop: aggiorna lo stadio nel DB."""
    payload = request.get_json(silent=True) or {}
    lead = Lead.query.get(payload.get("lead_id"))
    nuovo = payload.get("stadio")
    if not lead or nuovo not in STADI_LEAD:
        return jsonify(ok=False, error="dati non validi"), 400
    if lead.stadio != nuovo:
        lead.stadio = nuovo
        lead.stadio_updated_at = datetime.utcnow()
        db.session.commit()
    return jsonify(ok=True, lead_id=lead.id, stadio=nuovo,
                   punteggio=lead.punteggio)


@bp.route("/<int:lead_id>/modifica", methods=["POST"])
def salva(lead_id):
    """Modifica i dati commerciali del lead (valore, prossima azione, fonte).

    Solo modifica: il lead non si crea da qui, nasce col cliente in Anagrafica.
    Il cliente collegato non è modificabile, altrimenti si potrebbe spostare un
    lead su un'altra anagrafica e rompere la corrispondenza uno-a-uno.
    """
    form = request.form
    lead = Lead.query.get_or_404(lead_id)
    lead.stadio = form.get("stadio", "nuovo")
    lead.fonte = form.get("fonte", "altro")
    lead.valore_stimato = float(form.get("valore_stimato") or 0)
    lead.prossima_azione = form.get("prossima_azione", "").strip() or None
    lead.data_prossima_azione = parse_date(form.get("data_prossima_azione"))
    db.session.commit()
    flash("Lead salvato.", "success")
    return redirect(url_for("pipeline.index"))


# NOTA: non esiste una rotta di eliminazione del lead. Un lead è il riflesso di
# un cliente in Anagrafica: si elimina eliminando il cliente (Cliente.lead ha
# cascade="all, delete-orphan", quindi il lead sparisce dalla pipeline da solo).
# Cancellarlo da qui avrebbe lasciato un cliente in Anagrafica invisibile in
# pipeline, cioè le due sezioni fuori sincrono.
