# CRM Assicurativo — Subagente plurimandatario

Gestionale locale (mono-utente) per un subagente assicurativo plurimandatario:
clienti, lead/pipeline, preventivi, contratti, scadenze/rinnovi, sinistri,
incassi/provvigioni, documenti. Tutto in locale, nessun servizio cloud.

Ciclo di vita gestito: **Lead → Preventivo → Contratto attivo → Scadenza/Rinnovo → Sinistro**,
con **incassi/provvigioni** collegati ai contratti.

## Stack tecnico

- **Backend:** Python + **Flask** (sincrono, server-rendered — più semplice da
  mantenere di FastAPI per un'app locale mono-utente senza API pubblica).
- **Database:** **SQLite** (un unico file `crm.db`) con schema relazionale vero
  (chiavi esterne coerenti), tramite Flask-SQLAlchemy.
- **Frontend:** template **Jinja** serviti da Flask + piccoli endpoint JSON per
  le parti interattive (drag&drop pipeline, celle stato incassi, anteprima
  documenti, messaggistica). Nessun build step, nessun framework JS.
- **Documenti:** salvati su filesystem in `uploads/`, con solo il riferimento
  nel database. Persistono dopo il riavvio.
- **Zero dipendenze cloud:** font di sistema e icone SVG inline (nessun CDN),
  funziona anche completamente offline.

## Come avviarlo in locale

Serve **Python 3.10+**.

```bash
# 1. (consigliato) crea un ambiente virtuale
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. installa le dipendenze
pip install -r requirements.txt

# 3. avvia il programma
python app.py
```

Al primo avvio il database `crm.db` viene creato automaticamente e popolato con
**dati fittizi di esempio** (nessun dato reale).

Poi apri il browser su:

```
http://localhost:5000
```

Per fermare il programma: `Ctrl+C` nel terminale.

### Ripartire da zero

Per svuotare tutto e ricreare i dati di esempio, chiudi l'app ed elimina il file
del database:

```bash
rm crm.db      # Windows: del crm.db
python app.py
```

## Struttura del progetto

```
app.py               # entrypoint (python app.py)
config.py            # configurazione (percorso DB, cartella upload, limiti)
extensions.py        # istanza SQLAlchemy condivisa
models.py            # schema relazionale (tutte le entità e relazioni)
seed.py              # dati fittizi di esempio
utils.py             # filtri Jinja (€, date) e voci di navigazione
blueprints/          # una sezione per modulo (clienti, pipeline, preventivi,
                     #   contratti, scadenze, sinistri, incassi, compagnie,
                     #   compliance, documenti, messaggi, dashboard)
templates/           # base.html + template per ogni sezione
static/css, static/js
uploads/             # documenti allegati (non versionati)
crm.db               # database SQLite (generato)
```

## Funzionalità

- **Anagrafica clienti** con scheda **360°**: da un cliente si vedono in un'unica
  pagina lead, preventivi, contratti, scadenze, sinistri, incassi e documenti.
- **Filtro avanzato multi-campo** tradotto in query SQL (es. clienti *con figli*
  **e** con *polizza in scadenza in un dato mese/anno*).
- **Sidebar** comprimibile (toggle) e auto-collassante nelle sezioni operative.
- **Documenti:** upload, anteprima (immagini/PDF in modale) e download.
- **Contratti attivi** e **Preventivi** come sezioni distinte; un preventivo può
  **generare un contratto** collegato (link all'origine).
- **Scadenziario** derivato automaticamente dai contratti attivi.
- **Registro incassi** stile *Monday*: celle di stato colorate, cliccabili per
  cambiare stato (da incassare / incassato / in ritardo).
- **Messaggistica** WhatsApp (`wa.me`) ed Email (`mailto:`) verso più clienti
  selezionati, con apertura sequenziale e conferma tra un destinatario e l'altro.
- **Pipeline kanban** con drag & drop tra gli stadi, persistito nel database.
- **Dashboard** con KPI calcolati da query reali (valore pipeline, conversione,
  distribuzione per stadio/fonte, scadenze, incassi).
- **Punteggio lead deterministico** (completezza dati + valore + stadio), senza
  alcun valore casuale.

> Nota: uso mono-utente in locale, quindi non è prevista autenticazione né
> deploy online. Non esporre `app.py` in rete così com'è.
