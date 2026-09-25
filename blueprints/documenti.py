"""Documenti allegati: upload su filesystem (uploads/), anteprima e download.

I file sono salvati su disco con un nome fisico univoco; nel database si tiene
solo il riferimento (stored_name) e i metadati. Persistono dopo il riavvio.
"""
import mimetypes
import os
import uuid

from flask import (Blueprint, abort, current_app, flash, redirect,
                   request, send_from_directory, url_for)
from werkzeug.utils import secure_filename

from extensions import db
from models import Cliente, Documento, Contratto, Veicolo, AltroProdotto, Proposta

bp = Blueprint("documenti", __name__, url_prefix="/documenti")


def _ammesso(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_UPLOAD_EXTENSIONS"]


@bp.route("/carica/<int:cliente_id>", methods=["POST"])
def carica(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Nessun file selezionato.", "error")
        return redirect(url_for("clienti.detail", cliente_id=cliente_id))
    if not _ammesso(file.filename):
        flash("Tipo di file non ammesso.", "error")
        return redirect(url_for("clienti.detail", cliente_id=cliente_id))

    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else "bin"
    destinazioni = {
        "contratto": (Contratto, "contratto_id"),
        "veicolo": (Veicolo, "veicolo_id"),
        "prodotto": (AltroProdotto, "prodotto_id"),
        "proposta": (Proposta, "proposta_id"),
    }
    tipo_dest = request.form.get("destinazione", "")
    identificativo = request.form.get("destinazione_id", type=int)
    if tipo_dest or identificativo:
        if tipo_dest not in destinazioni or not identificativo:
            abort(400)
        modello, campo = destinazioni[tipo_dest]
        entita = modello.query.get_or_404(identificativo)
        if entita.cliente_id != cliente.id:
            abort(400)
    else:
        campo = None
    gruppo = tipo_dest if campo else "generali"
    cartella = os.path.join("clienti", str(cliente.id), gruppo)
    directory = os.path.join(current_app.config["UPLOAD_FOLDER"], cartella)
    os.makedirs(directory, exist_ok=True)
    stored = os.path.join(cartella, f"{uuid.uuid4().hex}.{ext}")
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
    # O_EXCL impedisce di sostituire anche accidentalmente un file già presente.
    with open(path, "xb") as output:
        file.save(output)

    doc = Documento(
        cliente_id=cliente.id,
        tipo=request.form.get("tipo", "").strip() or "Altro",
        filename=original,
        stored_name=stored,
        mime=file.mimetype or mimetypes.guess_type(original)[0],
        size=os.path.getsize(path),
    )
    if campo:
        setattr(doc, campo, identificativo)
    db.session.add(doc)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        os.remove(path)
        raise
    flash("Documento caricato.", "success")
    if tipo_dest == "contratto":
        return redirect(url_for("contratti.detail", contratto_id=identificativo))
    return redirect(url_for("clienti.detail", cliente_id=cliente_id))


@bp.route("/<int:doc_id>/anteprima")
def anteprima(doc_id):
    """Serve il file inline (per immagini/PDF nel modale di anteprima)."""
    doc = Documento.query.get_or_404(doc_id)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"],
                               doc.stored_name, as_attachment=False,
                               download_name=doc.filename)


@bp.route("/<int:doc_id>/download")
def download(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"],
                               doc.stored_name, as_attachment=True,
                               download_name=doc.filename)


@bp.route("/<int:doc_id>/elimina", methods=["POST"])
def elimina(doc_id):
    doc = Documento.query.get_or_404(doc_id)
    cliente_id = doc.cliente_id
    contratto_id = doc.contratto_id
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.stored_name or "")
    db.session.delete(doc)
    db.session.commit()
    if doc.stored_name and os.path.isfile(path):
        os.remove(path)
    flash("Documento eliminato.", "success")
    if contratto_id:
        return redirect(url_for("contratti.detail", contratto_id=contratto_id))
    return redirect(url_for("clienti.detail", cliente_id=cliente_id))
