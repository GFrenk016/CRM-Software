# CRM Assicurativo

Applicazione web locale per la gestione delle attività commerciali e operative di un subagente assicurativo plurimandatario.

Il progetto centralizza anagrafiche, lead, pratiche, preventivi, contratti, scadenze, sinistri, incassi e documenti, offrendo una vista completa del rapporto con ogni cliente.

## Panoramica

Il CRM segue l’intero ciclo di vita assicurativo:

```text
Lead → Preventivo → Contratto → Scadenza/Rinnovo → Sinistro
```

A questo flusso si affianca il modulo **Pratiche**, utilizzato per organizzare il lavoro operativo: raccolta documenti, appuntamenti, comunicazioni, avanzamento dell’emissione e collegamenti con clienti, veicoli, preventivi e polizze.

L’applicazione è progettata per un utilizzo **locale e mono-utente**. Non richiede servizi cloud, API esterne o un processo di build frontend.

## Funzionalità principali

### Dashboard operativa

- KPI calcolati direttamente dal database
- valore complessivo della pipeline
- tasso di conversione dei lead
- distribuzione per stadio e fonte
- contratti attivi e preventivi presenti
- scadenze nei successivi 30 giorni
- incassi da riscuotere e pagamenti in ritardo
- sinistri ancora aperti
- clienti da ricontattare nel mese corrente

### Anagrafica clienti

- creazione, modifica, archiviazione e ripristino dei clienti
- validazione e unicità del codice fiscale
- gestione di recapiti, indirizzo, dati personali e professionali
- registrazione dei veicoli con controllo del formato e unicità della targa
- filtri combinabili su dati anagrafici, nucleo familiare e scadenze
- scheda cliente a 360° con tutte le entità collegate
- eliminazione controllata tramite relazioni e regole di cascade

Quando viene creato un cliente, il sistema genera automaticamente il relativo lead nella pipeline. È inoltre possibile aprire contestualmente una pratica.

### Pipeline commerciale

- vista Kanban con drag and drop
- stadi: nuovo, contattato, qualificato, proposta, vinto e perso
- persistenza immediata dello spostamento nel database
- valore stimato e prossima azione
- conteggio dei giorni trascorsi nello stadio
- punteggio lead deterministico basato su:
  - completezza dell’anagrafica
  - valore stimato
  - avanzamento commerciale

La pipeline viene mantenuta allineata all’anagrafica: ogni cliente attivo dispone di un lead, mentre i clienti archiviati vengono esclusi dalla board senza perdere lo storico.

### Gestione delle pratiche

- numerazione automatica nel formato `PR-ANNO-PROGRESSIVO`
- collegamento con cliente, lead, contratto, sinistro e veicolo
- classificazione per tipologia, priorità e stato
- filtri per famiglia di stato
- assegnazione automatica della priorità urgente per le lavorazioni critiche
- flusso guidato per l’emissione della polizza
- registrazione delle date dei principali passaggi
- avvisi non bloccanti per operazioni fuori dalle finestre di emissione
- verifica dei dati obbligatori in base alla tipologia di pratica
- gestione del motivo di perdita e della futura data di ricontatto
- checklist dei documenti attesi
- appuntamenti e comunicazioni collegati
- creazione di più preventivi a partire dalla stessa pratica

### Preventivi e confronto compagnie

- gestione degli stati: bozza, inviato, accettato e rifiutato
- collegamento con cliente, lead, veicolo e pratica
- confronto tra più compagnie consultate
- registrazione di premio, garanzie e note per ciascuna compagnia
- evidenziazione dell’offerta più conveniente
- scelta della compagnia selezionata
- conversione di un preventivo accettato in contratto attivo
- mantenimento del collegamento tra preventivo e polizza generata

### Contratti e scadenze

- gestione di compagnia, numero di polizza, ramo, premio e stato
- collegamento al preventivo di origine
- vista di dettaglio con sinistri e incassi associati
- scadenziario calcolato automaticamente dai contratti attivi
- ordinamento e monitoraggio delle polizze prossime alla scadenza

Le scadenze non vengono duplicate in una tabella separata: sono derivate dalla data di scadenza dei contratti, mantenendo un’unica fonte di verità.

### Sinistri

- numerazione progressiva
- collegamento obbligatorio a cliente e contratto
- gestione di tipologia, data di apertura, stato e importo stimato
- monitoraggio degli stati aperto, perizia e chiuso

### Incassi e provvigioni

- registro visuale in stile board
- stati: da incassare, incassato e in ritardo
- aggiornamento dello stato senza ricaricare la pagina
- sincronizzazione tra stato e data di incasso
- rilevamento automatico dei pagamenti scaduti
- riepilogo degli importi per stato

### Documenti e compliance

- caricamento di documenti fino a 25 MB
- associazione del documento al cliente e, facoltativamente, a una pratica
- anteprima di immagini e PDF
- download ed eliminazione degli allegati
- anteprima del file prima del caricamento
- checklist di compliance basata sui dati e sui documenti realmente presenti
- controllo di dati identificativi, documento d’identità, privacy e recapiti

I file vengono conservati nella cartella `uploads/`; nel database sono salvati metadati e riferimenti.

### Comunicazioni e appuntamenti

- preparazione di messaggi WhatsApp tramite `wa.me`
- preparazione di email tramite `mailto:`
- selezione di uno o più destinatari
- modelli di messaggio modificabili
- personalizzazione del testo con il nome del cliente
- composizione automatica delle richieste per i documenti mancanti
- registrazione dello storico delle comunicazioni
- gestione di appuntamenti, tipologia ed esito

Il CRM prepara e apre i messaggi nell’applicazione scelta dall’utente, ma non effettua un invio automatico tramite API esterne.

### Ricerca

- ricerca parziale o completa per codice fiscale
- vista aggregata in sola lettura
- accesso immediato a pratiche, polizze, preventivi, veicoli, documenti, comunicazioni e appuntamenti del cliente

## Stack tecnologico

| Area | Tecnologie |
|---|---|
| Backend | Python, Flask |
| Persistenza | SQLite, SQLAlchemy |
| Migrazioni | Flask-Migrate, Alembic |
| Frontend | Jinja, HTML, CSS, JavaScript |
| Interazioni dinamiche | Fetch API ed endpoint JSON |
| Server WSGI | Gunicorn |
| Distribuzione | esecuzione locale, configurazione Render presente |

L’interfaccia è server-rendered. JavaScript viene utilizzato soltanto per le funzionalità interattive, come pipeline drag and drop, modali, filtri, aggiornamento degli incassi e anteprima dei documenti.

Non sono richiesti Node.js, npm o un processo di compilazione frontend.

## Architettura

L’applicazione utilizza il pattern **application factory** di Flask e separa i moduli tramite Blueprint.

```text
CRM-Software/
├── app.py                 # Application factory ed entrypoint
├── config.py              # Database, sessione e configurazione upload
├── extensions.py          # Istanza SQLAlchemy condivisa
├── models.py              # Modelli, relazioni e logica di dominio
├── seed.py                # Dati dimostrativi iniziali
├── utils.py               # Helper e filtri Jinja
├── requirements.txt
├── avvia_crm.bat          # Avvio assistito su Windows
├── render.yaml            # Configurazione WSGI per Render
│
├── blueprints/            # Moduli applicativi Flask
│   ├── dashboard.py
│   ├── clienti.py
│   ├── pipeline.py
│   ├── pratiche.py
│   ├── preventivi.py
│   ├── contratti.py
│   ├── scadenze.py
│   ├── sinistri.py
│   ├── incassi.py
│   ├── compagnie.py
│   ├── compliance.py
│   ├── documenti.py
│   ├── messaggi.py
│   ├── appuntamenti.py
│   ├── impostazioni.py
│   └── ricerca.py
│
├── templates/             # Layout e viste Jinja
├── static/
│   ├── css/
│   └── js/
├── migrations/            # Migrazioni Alembic
└── uploads/               # Allegati locali non versionati
```

## Modello dati

Il database comprende le seguenti entità principali:

- `Cliente`
- `Lead`
- `Veicolo`
- `Pratica`
- `ChecklistDocumento`
- `Appuntamento`
- `Comunicazione`
- `Preventivo`
- `PreventivoCompagnia`
- `Compagnia`
- `Contratto`
- `Sinistro`
- `Incasso`
- `Documento`
- `ImpostazioniAgenzia`

Le entità sono collegate tramite chiavi esterne e relazioni SQLAlchemy. La scheda cliente utilizza queste relazioni per ricostruire l’intero storico senza duplicare i dati.

Il database SQLite viene salvato nel file:

```text
crm.db
```

Lo schema è gestito tramite migrazioni Alembic, applicate automaticamente all’avvio.

## Requisiti

- Python 3.10 o superiore
- `pip`
- un browser moderno

Non è richiesta alcuna variabile d’ambiente per l’avvio locale.

La variabile opzionale `CRM_SECRET_KEY` permette di sostituire la chiave predefinita utilizzata da Flask per sessione e messaggi flash:

```powershell
$env:CRM_SECRET_KEY = "una-chiave-personale"
```

## Installazione e avvio

Clona la repository:

```bash
git clone https://github.com/GFrenk016/CRM-Software.git
cd CRM-Software
```

Crea un ambiente virtuale:

```bash
python -m venv .venv
```

Attivalo su Windows:

```powershell
.venv\Scripts\activate
```

Oppure su macOS/Linux:

```bash
source .venv/bin/activate
```

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

Avvia l’applicazione:

```bash
python app.py
```

Apri quindi:

```text
http://localhost:5000
```

Al primo avvio il sistema:

1. crea la cartella degli allegati;
2. genera il database SQLite;
3. applica tutte le migrazioni disponibili;
4. inserisce un insieme coerente di dati dimostrativi.

## Avvio rapido su Windows

È disponibile anche lo script:

```text
avvia_crm.bat
```

Lo script crea l’ambiente virtuale se necessario, installa o aggiorna le dipendenze, controlla la compatibilità del database e apre automaticamente il browser.

Se rileva un database precedente all’introduzione delle migrazioni, propone di crearne una copia `crm.db.bak` prima della ricostruzione.

## Ripristino dei dati dimostrativi

Per ricreare il database iniziale, arresta l’applicazione ed elimina `crm.db`.

Windows:

```powershell
Remove-Item crm.db
python app.py
```

macOS/Linux:

```bash
rm crm.db
python app.py
```

Il database verrà ricreato e popolato automaticamente.

## Gestione delle migrazioni

Dopo una modifica ai modelli, imposta le variabili necessarie e genera una nuova migrazione.

PowerShell:

```powershell
$env:FLASK_APP = "app.py"
$env:CRM_SKIP_STARTUP_UPGRADE = "1"

flask db migrate -m "descrizione modifica"
flask db upgrade
```

macOS/Linux:

```bash
export FLASK_APP=app.py
export CRM_SKIP_STARTUP_UPGRADE=1

flask db migrate -m "descrizione modifica"
flask db upgrade
```

`CRM_SKIP_STARTUP_UPGRADE` è una variabile tecnica usata durante la manutenzione dello schema; non è necessaria per il normale avvio.

## Gestione degli allegati

Sono supportati i seguenti formati:

```text
pdf, png, jpg, jpeg, gif, webp,
doc, docx, xls, xlsx, txt, csv
```

La dimensione massima prevista è di 25 MB per file.

Gli allegati e il database non sono versionati da Git e devono essere inclusi nelle procedure di backup.

## Ambito e limitazioni

Il progetto è attualmente pensato come gestionale locale:

- non include autenticazione o gestione di più utenti;
- non deve essere esposto direttamente su Internet nella configurazione attuale;
- utilizza SQLite e filesystem locale per database e allegati;
- WhatsApp ed email vengono aperti tramite link, senza invio automatico;
- non è presente una suite di test automatici;
- la configurazione Render inclusa richiede storage persistente e autenticazione prima di un utilizzo reale online.

Per un’eventuale evoluzione multi-utente sarebbe opportuno introdurre autenticazione, autorizzazioni per ruolo, protezione CSRF, PostgreSQL, storage esterno per gli allegati e test automatici.

## Aspetti tecnici rilevanti

- architettura Flask modulare basata su Blueprint;
- schema relazionale gestito tramite ORM e migrazioni versionate;
- logica di dominio concentrata nei modelli;
- workflow di emissione guidato e dipendente dalla tipologia di pratica;
- validazione lato server dei principali dati assicurativi;
- controllo dei collegamenti per impedire associazioni tra entità appartenenti a clienti diversi;
- KPI e scadenze calcolati da dati reali;
- aggiornamenti asincroni mirati senza dipendere da un framework frontend;
- gestione distinta tra archiviazione non distruttiva ed eliminazione;
- mantenimento dello storico delle comunicazioni anche in caso di eliminazione dell’anagrafica.

## Autore

Progetto sviluppato da [GFrenk016](https://github.com/GFrenk016).
