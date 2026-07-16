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
from models import Cliente, Documento

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
    stored = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored)
    file.save(path)

    doc = Documento(
        cliente_id=cliente.id,
        tipo=request.form.get("tipo", "").strip() or "Documento",
        filename=original,
        stored_name=stored,
        mime=file.mimetype or mimetypes.guess_type(original)[0],
        size=os.path.getsize(path),
    )
    db.session.add(doc)
    db.session.commit()
    flash("Documento caricato.", "success")
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
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.stored_name or "")
    if doc.stored_name and os.path.exists(path):
        os.remove(path)
    db.session.delete(doc)
    db.session.commit()
    flash("Documento eliminato.", "success")
    return redirect(url_for("clienti.detail", cliente_id=cliente_id))
