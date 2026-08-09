# CRM Assicurativo — Subagente plurimandatario

Gestionale mono-utente per un subagente assicurativo plurimandatario: clienti,
lead/pipeline, **pratiche**, preventivi, contratti, scadenze/rinnovi, sinistri,
incassi, documenti, appuntamenti e storico comunicazioni.

Due cicli di vita convivono:

- **Commerciale:** Lead → Preventivo → Contratto attivo → Scadenza/Rinnovo → Sinistro,
  con incassi collegati ai contratti.
- **Operativo (Pratica):** ogni richiesta del cliente diventa una pratica
  numerata (`PR-anno-progressivo`) con tipologia, priorità e stato, e — per le
  tipologie che arrivano davvero all'emissione — segue la catena guidata
  documentazione → pagamento → OTP → coda emissione → emessa → certificato inviato.

## Stack tecnico

- **Backend:** Python + **Flask** (sincrono, server-rendered — più semplice da
  mantenere di FastAPI per un'app mono-utente senza API pubblica).
- **Database:** **SQLite** (un unico file `crm.db`) con schema relazionale vero
  (chiavi esterne coerenti), tramite Flask-SQLAlchemy. Lo schema è gestito con
  **Flask-Migrate** (Alembic): all'avvio l'app applica automaticamente le
  migrazioni fino all'ultima revisione.
- **Frontend:** template **Jinja** serviti da Flask + piccoli endpoint JSON per
  le parti interattive (drag&drop pipeline, celle stato incassi, anteprima
  documenti, messaggistica). Nessun build step, nessun framework JS.
- **Documenti:** salvati su filesystem in `uploads/`, con solo il riferimento
  nel database.
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

Su Windows c'è anche `avvia_crm.bat`, che fa gli stessi passaggi con un doppio
clic. **Non è ancora stato provato su una macchina Windows reale**: se non
parte, usa la procedura manuale qui sopra.

### Ripartire da zero

Per svuotare tutto e ricreare i dati di esempio, chiudi l'app ed elimina il file
del database:

```bash
rm crm.db      # Windows: del crm.db
python app.py
```

> Se aggiorni da una versione precedente all'introduzione di Flask-Migrate,
> elimina una volta il vecchio `crm.db` (contiene solo dati di esempio): non ha
> la cronologia delle migrazioni e verrà ricreato aggiornato al primo avvio.

### Backup

Il database è **un solo file**: `crm.db`. Copiarlo ad app chiusa è un backup
completo dei dati; per un backup davvero completo va copiata anche la cartella
`uploads/`, che contiene gli allegati veri (nel database ci sono solo i
riferimenti).

### Modificare lo schema (migrazioni)

Dopo aver cambiato i modelli in `models.py`, genera e applica la migrazione:

```bash
export FLASK_APP=app.py CRM_SKIP_STARTUP_UPGRADE=1   # Windows: set ...
flask db migrate -m "descrizione della modifica"
flask db upgrade                                     # oppure riavvia l'app
```

Prima di applicare una migrazione su un database con dati veri, **fai una copia
di `crm.db`**.

## Anteprima online (Render)

`render.yaml` configura un deploy su Render (gunicorn) utile a **far vedere
l'applicazione a distanza**. Va inteso come vetrina temporanea, non come
installazione di lavoro:

- il filesystem di Render è **effimero**: a ogni nuovo deploy il database e gli
  allegati caricati vengono persi e si riparte dai dati di esempio;
- il server gira con orologio **UTC**, quindi le finestre orarie di emissione
  risultano spostate rispetto all'ora italiana (vedi *Limiti noti*);
- non c'è autenticazione: chiunque abbia il link vede tutto. Non caricarci dati
  reali di clienti.

Per un uso online vero servirebbero un database gestito (Postgres via
`DATABASE_URL`) e uno storage esterno per gli allegati: non sono ancora previsti.

## Struttura del progetto

```
app.py               # entrypoint (python app.py) — applica le migrazioni e fa il seed
config.py            # configurazione (percorso DB, cartella upload, limiti)
extensions.py        # istanza SQLAlchemy condivisa
models.py            # schema relazionale, costanti di dominio e validazioni
seed.py              # dati fittizi di esempio
utils.py             # filtri Jinja (€, date), voci di sidebar, form pagina/modale
blueprints/          # una sezione per modulo: dashboard, clienti, pipeline,
                     #   pratiche, preventivi, contratti, scadenze, sinistri,
                     #   incassi, compagnie, compliance, documenti, messaggi,
                     #   appuntamenti, impostazioni, ricerca
migrations/          # cronologia Alembic dello schema
templates/           # base.html, _macros.html + template per ogni sezione
static/css, static/js
uploads/             # documenti allegati (non versionati)
crm.db               # database SQLite (generato)
bugfixes.md          # storico richieste, fasi, domande al cliente, debito tecnico
collaudo_subagente.md# traccia per la prova con il cliente
```

## Funzionalità

**Bacheca (dashboard)**
- Urgenze operative in evidenza — scadenze in arrivo, incassi in ritardo,
  sinistri aperti — ciascuna con link "vedi tutti" a una lista che mostra
  esattamente le stesse righe contate nella card.
- Clienti **da ricontattare** ricavati dalle pratiche perse con data di
  riferimento nel mese.
- KPI da query reali (valore pipeline, conversione, distribuzione per stadio e
  per fonte). Nessun valore casuale.

**Anagrafica e ricerca**
- Scheda cliente **360°**: da un'unica pagina si vedono lead, pratiche,
  preventivi, contratti, scadenze, sinistri, incassi, veicoli, documenti,
  appuntamenti e storico comunicazioni.
- Filtro avanzato multi-campo tradotto in query SQL (es. clienti *con figli* **e**
  con *polizza in scadenza in un dato mese/anno*).
- **Archiviazione clienti**: archiviazione anche massiva dei selezionati, elenco
  archiviati con ripristino. Gli archiviati escono da Anagrafica e Pipeline, ma
  i dati collegati restano.
- **Ricerca CF**: vista aggregata a partire dal codice fiscale, con avviso di
  **cross-selling** sui veicoli del cliente non ancora coperti da polizza.
- Codice fiscale validato sul formato standard italiano e univoco.

**Pipeline**
- Kanban con drag & drop fra gli stadi, persistito nel database.
- Specchio dell'anagrafica: i lead nascono creando un cliente e spariscono se il
  cliente viene eliminato o archiviato. Dalle card si apre la scheda cliente.
- **Punteggio lead deterministico** (completezza dati + valore + stadio).

**Pratiche**
- 10 tipologie (Bersani, rinnovo, nuovo acquisto, sostituzione veicolo,
  pagamento polizza/rata, sospensione, riattivazione, consulenza, sinistro,
  nuovo preventivo), 4 livelli di priorità.
- Stati filtrati per tipologia: la catena di emissione compare solo dove ha
  senso, le altre restano sugli stati generici.
- **Avanzamento guidato** allo stato successivo, **checklist documenti** per
  pratica e **richiesta documenti al cliente** che compone il messaggio e lo
  registra a storico.
- Esito negativo con **motivo di perdita** (elenco chiuso) più **motivazione
  libera** quando si sceglie "altro", e data di riferimento per il ricontatto.
- Collegamenti a lead, preventivo, contratto, sinistro e veicolo.

**Preventivi e contratti**
- **Compagnie consultate** su un preventivo: una riga per compagnia con premio,
  garanzie e note, con il premio più basso evidenziato; la compagnia scelta è
  distinta dalle altre consultate.
- Conversione preventivo → contratto con link all'origine.
- Dal dettaglio contratto si aprono direttamente nuovo sinistro e nuovo incasso,
  già con cliente e polizza pre-selezionati.

**Scadenziario, sinistri, incassi**
- Scadenziario derivato automaticamente dai contratti attivi, con finestra
  temporale selezionabile.
- Registro incassi con celle di stato cliccabili (da incassare / incassato /
  in ritardo).

**Documenti, comunicazioni, appuntamenti**
- Upload con tipo documento, anteprima in modale (immagini e PDF) e download.
- **Storico comunicazioni** per cliente e per pratica: ogni messaggio composto
  dalla modale viene registrato, con canale, destinatario e testo; i doppioni si
  possono eliminare.
- Messaggistica **WhatsApp** (`wa.me`) ed **Email** (`mailto:`) verso più
  clienti selezionati, con apertura sequenziale. Il CRM compone, l'invio lo fa
  l'operatore: nessuna API a pagamento.
- Appuntamenti con tipo (compreso **OTP**) ed esito, gestiti da scheda cliente e
  dettaglio pratica.

**Compagnie, compliance, impostazioni**
- Anagrafica compagnie mandatarie.
- Sezione compliance.
- Impostazioni agenzia: ragione sociale, IBAN e le **due finestre giornaliere di
  emissione**, cioè le fasce orarie in cui il subagente emette davvero le polizze
  presso le compagnie (default 9-11 / 15-17, modificabili; lasciando vuota una
  fascia la si disattiva). Se una pratica viene portata a "in coda emissione" o
  "emessa" fuori da quelle fasce, il CRM mostra un avviso — **non blocca**
  l'operazione, serve solo a ricordare che in quel momento in compagnia non si
  emette.

## Limiti noti

Elenco sintetico; il dettaglio, con le domande ancora aperte per il cliente, sta
in `bugfixes.md`.

- **Orari in UTC.** I timestamp sono salvati con `datetime.utcnow()` e stampati
  senza conversione: nello storico comunicazioni l'ora appare indietro di due ore
  d'estate (una d'inverno). Il controllo delle finestre di emissione usa invece
  l'ora locale della macchina, quindi in locale è corretto ma su un server UTC
  no. Va uniformato.
- **Nessuna autenticazione**: previsto un solo utente su una sola macchina.
- **Deploy online non pronto**: SQLite e allegati su filesystem (vedi
  *Anteprima online*).
- **`avvia_crm.bat` non provato** su Windows reale.
- **Validazioni incomplete**: alcuni campi obbligatori sono aggirabili con una
  POST diretta, l'email non è validata lato server, e importi non numerici
  inviati fuori dal form possono dare errore 500 invece di un avviso.
- **Elenco garanzie provvisorio** e polizze caricate a mano non collegabili a
  una targa: il veicolo resta fra gli "scoperti" anche se assicurato.