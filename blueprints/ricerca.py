"""Ricerca per codice fiscale: un CF → tutto ciò che è collegato a quel cliente.

Non è un filtro in più sull'anagrafica (quello esiste già in clienti.py, che
cerca su nome/cognome/CF/email/cellulare e restituisce un ELENCO): qui si parte
dal codice fiscale e si arriva a una VISTA AGGREGATA in sola lettura — pratiche,
polizze, preventivi, targhe, documenti, comunicazioni e appuntamenti in una
schermata sola, senza passare da una sezione all'altra.

Sola lettura per scelta: la scheda cliente resta l'unico posto dove si modifica
qualcosa, così non ci sono due punti da tenere allineati.
"""
from flask import Blueprint, render_template, request

from models import Cliente

bp = Blueprint("ricerca", __name__, url_prefix="/ricerca")


@bp.route("/")
def index():
    # Il CF si normalizza come nel modello (upper/trim): scriverlo minuscolo o
    # con spazi in coda è la norma quando lo si incolla da un documento.
    cf = (request.args.get("cf") or "").strip().upper()
    cliente_id = request.args.get("cliente_id", type=int)

    # Scelta esplicita dall'elenco dei risultati (CF parziale su più clienti).
    if cliente_id:
        cliente = Cliente.query.get_or_404(cliente_id)
        return render_template("ricerca/index.html", cf=cf, cliente=cliente,
                               risultati=None, cercato=True)

    if not cf:
        return render_template("ricerca/index.html", cf="", cliente=None,
                               risultati=None, cercato=False)

    # Ricerca PARZIALE: il CF completo è unique, ma si ammette anche un
    # frammento (le prime lettere del cognome, la parte della data di nascita),
    # perché spesso si ha in mano solo un pezzo. Quindi più clienti sono
    # possibili anche con la colonna unique.
    risultati = (Cliente.query
                 .filter(Cliente.codice_fiscale.ilike(f"%{cf}%"))
                 .order_by(Cliente.cognome, Cliente.nome)
                 .all())

    if len(risultati) == 1:
        return render_template("ricerca/index.html", cf=cf,
                               cliente=risultati[0], risultati=None,
                               cercato=True)
    # 0 risultati → messaggio esplicito nel template (non una pagina vuota);
    # più di uno → elenco da cui scegliere.
    return render_template("ricerca/index.html", cf=cf, cliente=None,
                           risultati=risultati, cercato=True)
