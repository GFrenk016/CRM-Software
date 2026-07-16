"""Compagnie / mandati del plurimandatario."""
from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import Compagnia

bp = Blueprint("compagnie", __name__, url_prefix="/compagnie")


@bp.route("/")
def index():
    compagnie = Compagnia.query.order_by(Compagnia.nome).all()
    return render_template("compagnie/list.html", compagnie=compagnie)


@bp.route("/nuova", methods=["POST"])
def nuova():
    nome = request.form.get("nome", "").strip()
    if nome:
        if Compagnia.query.filter_by(nome=nome).first():
            flash("Compagnia già presente.", "error")
        else:
            db.session.add(Compagnia(nome=nome,
                                     note=request.form.get("note", "").strip() or None))
            db.session.commit()
            flash("Compagnia aggiunta.", "success")
    return redirect(url_for("compagnie.index"))


@bp.route("/<int:comp_id>/elimina", methods=["POST"])
def elimina(comp_id):
    comp = Compagnia.query.get_or_404(comp_id)
    if comp.contratti or comp.preventivi:
        flash("Impossibile eliminare: compagnia collegata a contratti/preventivi.",
              "error")
    else:
        db.session.delete(comp)
        db.session.commit()
        flash("Compagnia eliminata.", "success")
    return redirect(url_for("compagnie.index"))
