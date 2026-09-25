"""Altri prodotti e proposte nella scheda cliente."""
from flask import Blueprint, flash, redirect, request, url_for
from extensions import db
from models import Cliente, AltroProdotto, Proposta, RelazioneCliente

bp = Blueprint("extra", __name__, url_prefix="/clienti")


def _ritorno(cliente_id):
    return redirect(url_for("clienti.detail", cliente_id=cliente_id))


@bp.post("/<int:cliente_id>/prodotti")
def prodotto(cliente_id):
    Cliente.query.get_or_404(cliente_id)
    nome = request.form.get("nome", "").strip()
    if not nome:
        flash("Indica il nome del prodotto.", "error")
        return _ritorno(cliente_id)
    db.session.add(AltroProdotto(cliente_id=cliente_id, nome=nome,
        numero_tessera=request.form.get("numero_tessera", "").strip() or None,
        descrizione=request.form.get("descrizione", "").strip() or None))
    db.session.commit()
    flash("Prodotto aggiunto.", "success")
    return _ritorno(cliente_id)


@bp.post("/<int:cliente_id>/prodotti/<int:identificativo>/elimina")
def elimina_prodotto(cliente_id, identificativo):
    item = AltroProdotto.query.filter_by(id=identificativo, cliente_id=cliente_id).first_or_404()
    if item.documenti:
        flash("Elimina prima gli allegati del prodotto.", "error")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Prodotto eliminato.", "success")
    return _ritorno(cliente_id)


@bp.post("/<int:cliente_id>/proposte")
def proposta(cliente_id):
    Cliente.query.get_or_404(cliente_id)
    numero = request.form.get("numero", "").strip()
    if not numero:
        flash("Indica il numero della proposta.", "error")
        return _ritorno(cliente_id)
    db.session.add(Proposta(cliente_id=cliente_id, numero=numero,
        note=request.form.get("note", "").strip() or None))
    db.session.commit()
    flash("Proposta aggiunta.", "success")
    return _ritorno(cliente_id)


@bp.post("/<int:cliente_id>/proposte/<int:identificativo>/elimina")
def elimina_proposta(cliente_id, identificativo):
    item = Proposta.query.filter_by(id=identificativo, cliente_id=cliente_id).first_or_404()
    if item.documenti:
        flash("Elimina prima gli allegati della proposta.", "error")
    else:
        db.session.delete(item)
        db.session.commit()
        flash("Proposta eliminata.", "success")
    return _ritorno(cliente_id)


@bp.post("/<int:cliente_id>/relazioni")
def collega(cliente_id):
    Cliente.query.get_or_404(cliente_id)
    codice = request.form.get("codice_cliente", "").strip().upper()
    if not codice.startswith("CL-") or not codice[3:].isdigit():
        flash("Codice cliente non valido.", "error")
        return _ritorno(cliente_id)
    altro = db.session.get(Cliente, int(codice[3:]))
    if altro is None or altro.id == cliente_id:
        flash("Cliente collegato non trovato.", "error")
        return _ritorno(cliente_id)
    a, b = sorted((cliente_id, altro.id))
    rapporto = request.form.get("rapporto", "").strip()[:80]
    inverso = request.form.get("rapporto_inverso", "").strip()[:80]
    if not rapporto:
        flash("Indica il tipo di relazione.", "error")
        return _ritorno(cliente_id)
    relazione = db.session.get(RelazioneCliente, (a, b))
    if relazione is None:
        relazione = RelazioneCliente(cliente_a_id=a, cliente_b_id=b)
        db.session.add(relazione)
    if cliente_id == a:
        relazione.descrizione, relazione.descrizione_inversa = rapporto, inverso or None
    else:
        relazione.descrizione_inversa, relazione.descrizione = rapporto, inverso or None
    db.session.commit()
    flash("Relazione salvata.", "success")
    return _ritorno(cliente_id)


@bp.post("/<int:cliente_id>/relazioni/<int:altro_id>/elimina")
def scollega(cliente_id, altro_id):
    Cliente.query.get_or_404(cliente_id)
    a, b = sorted((cliente_id, altro_id))
    relazione = db.session.get(RelazioneCliente, (a, b))
    if relazione is None or cliente_id == altro_id:
        flash("Relazione non trovata.", "error")
    else:
        db.session.delete(relazione)
        db.session.commit()
        flash("Collegamento rimosso.", "success")
    return _ritorno(cliente_id)
