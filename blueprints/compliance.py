"""Compliance documentale: checklist per cliente basata su dati REALI.

Nessun dato inventato: ogni spunta deriva dallo stato effettivo del cliente
e dai documenti realmente caricati.
"""
from flask import Blueprint, render_template

from models import Cliente, Documento

bp = Blueprint("compliance", __name__, url_prefix="/compliance")


def _ha_doc(cliente, chiavi):
    for d in cliente.documenti:
        tipo = (d.tipo or "").lower()
        if any(k in tipo for k in chiavi):
            return True
    return False


@bp.route("/")
def index():
    righe = []
    for c in Cliente.query.order_by(Cliente.cognome).all():
        dati_identita = bool(c.codice_fiscale and c.numero_documento)
        doc_identita = _ha_doc(c, ["identità", "identita", "patente", "passaporto"])
        privacy = _ha_doc(c, ["privacy", "consenso", "gdpr"])
        contatti = bool(c.email or c.cellulare or c.telefono)
        checks = [dati_identita, doc_identita, privacy, contatti]
        completi = sum(1 for x in checks if x)
        righe.append({
            "cliente": c,
            "dati_identita": dati_identita,
            "doc_identita": doc_identita,
            "privacy": privacy,
            "contatti": contatti,
            "completo": completi == len(checks),
            "parziale": 0 < completi < len(checks),
        })
    return render_template("compliance/list.html", righe=righe)
