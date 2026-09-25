"""Compagnie / mandati del plurimandatario."""
import re
from flask import (Blueprint, flash, redirect, render_template, request, url_for)

from extensions import db
from models import Compagnia

bp = Blueprint("compagnie", __name__, url_prefix="/compagnie")


def _colore():
    value = request.form.get("colore", "#2563eb")
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else "#2563eb"


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
                                     colore=_colore(),
                                     note=request.form.get("note", "").strip() or None))
            db.session.commit()
            flash("Compagnia aggiunta.", "success")
    return redirect(url_for("compagnie.index"))


@bp.post("/<int:comp_id>/colore")
def colore(comp_id):
    comp = Compagnia.query.get_or_404(comp_id)
    comp.colore = _colore()
    db.session.commit()
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
