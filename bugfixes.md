## Task list — CRM Assicurativo, Fase 1 (Analisi Funzionale)

### 🅰️ Fase A — Fondamenta
- [ ] Creare modello **Pratica** (numero identificativo, stato, priorità, operatore, tipologia)
- [ ] Definire le tipologie di pratica: nuovo preventivo, Bersani, nuovo acquisto, rinnovo, pagamento polizza/rata, sostituzione veicolo, sospensione, riattivazione, consulenza, sinistro
- [ ] Collegare Pratica a Cliente/Lead esistenti
- [ ] Collegare Pratica a Contratto/Sinistro dove pertinente
- [ ] Aggiungere campo **Codice Fiscale** al modello Cliente (se mancante)
- [ ] Aggiungere campo **indirizzo completo** al modello Cliente (se mancante)
- [ ] Aggiungere campo **targa** al modello Veicolo/Cliente per preventivi RC Auto

### 🅱️ Fase B — Logica di business sulla Pratica
- [ ] Stato **"Documentazione da integrare"** sulla Pratica
- [ ] Elenco documenti mancanti collegato alla pratica
- [ ] Invio automatico richiesta documentazione al cliente
- [ ] Priorità automatica: massima per Bersani, nuovi acquisti, sostituzioni veicolo
- [ ] Ordinamento preventivi ordinari per scadenza polizza
- [ ] Flusso esito positivo: richiesta doc mancante → invio IBAN → verifica pagamento → appuntamento OTP → coda emissioni → emissione polizza → invio certificato → chiusura pratica
- [ ] Vincolo: emissioni concentrate in **due finestre giornaliere**
- [ ] Flusso esito negativo → archiviazione in **"Clienti da ricontattare"** (Nome, Cognome, CF, Targa, scadenza, motivo perdita, note)
- [ ] Ricontatto automatico alla scadenza successiva

### 🅲 Fase C — Arricchimento vista
- [ ] Preventivo: campi compagnie consultate, premio, garanzie, note, stato trattativa
- [ ] Storico preventivi visibile sia su Pratica sia su Scheda Cliente
- [ ] Scheda cliente completa: anagrafica, veicoli, preventivi, polizze, documenti, comunicazioni, appuntamenti, stato pratiche
- [ ] Ricerca avanzata per Codice Fiscale (pratiche, polizze, preventivi, targhe, documenti, comunicazioni)
- [ ] Evidenziazione altri veicoli collegati al cliente (cross selling/fidelizzazione)

### 🅳 Fase D — Integrazioni esterne
- [ ] Collegamento WhatsApp e social
- [ ] Collegamento Google Form → import automatico dati nel gestionale

---

## vecchi
[X] Passando il mouse deve aprirsi la sidebar, non tramite un tasto
[X] Bacheca che mostra piu cose: Urgenze operative (la cosa più utile, in cima)
Scadenze polizze nei prossimi 7/30 giorni — è il cuore del business ricorrente, dovrebbe saltare all'occhio subito, non essere sepolta nella sezione Scadenze
Incassi in ritardo — chi non ha ancora pagato, con quanto tempo di ritardo
Sinistri aperti che aspettano un'azione (es. perizia da sollecitare)
[X] Le cose nella bacheca devono essere cliccabili (clienti che porta alla anagrafica, sinistri aperti che porta ai sinistri ecc..)
[X] Stessa cosa per il tasto nuovo cliente, deve essere per tutti i pannelli
[X] Sezione Preventivi, tasto che mostra il profilo del cliente
[X] Nel nuovo contratto, quando si clicca Cliente, si deve aprire un pannello di ricerca, e mettere tra gli stati anche la voce "in attesa"
[X] Il tasto Nuovo Cliente non deve aprire un nuova finestra, ma un pannello che va sopra tutto al centro
[X] Quando si visualizza un cliente ci devono essere diversi tasti che portano alle altre sezioni del CRM
[X] Il tasto messaggio secondo me deve essere messo nella sidebar, per il momento deve essere semplice: seleziona cliente, whatsapp o email, selezionare il messaggio preimpostato e boh suggerisci tu Claude
[X] Nella Pipeline, non si deve creare dal tasto nuovo lead, quello deve essere rimosso perche deve essere creato in automatico quando mandano il form, comunque un tasto per metterlo manualmente nella sezione anagrafica ci deve essere, cosi in qualsiasi caso lo puo creare e mettere nell anagrafica e automaticamente anchje nella Pipeline
[X] Dropdown quando si sceglie il tipo di Documento, che deve apparire sotto con tasti anteprima, scarica ed elimina
[X] In incassi, deve aprirsi un Dropdown per segnalarlo
[X] In Incassi, tasto per visualizzare contratto, cliente

---

## Fase A — Fondamenta Pratiche (solo modello dati + migrazioni)

Questa fase introduce SOLO il livello dati: nessuna route/view/template per le
Pratiche (arriveranno in una fase successiva).

### Nuovo modello `Pratica` (tabella `pratiche`)
- `numero_identificativo` — String(20), univoco, generato automaticamente nel
  formato `PR-{anno}-{progressivo}` (progressivo per-anno, zero-padded a 4 cifre,
  es. `PR-2026-0001`). Il repo non aveva una convenzione anno-based (esistevano
  solo `PRV-0001` / `SIN-0001`), quindi si è adottato il formato proposto.
  L'assegnazione avviene in un evento SQLAlchemy `before_flush` (non
  `before_insert`), così più pratiche create nello stesso flush ricevono
  progressivi consecutivi senza collisioni sull'indice univoco.
- `stato` — String(30), default `aperta`. Valori in `STATI_PRATICA`
  (`aperta`, `in lavorazione`, `in attesa cliente`, `completata`, `annullata`).
  Segue lo stile "colonna String + lista di costanti" già usato per
  `STATI_CONTRATTO` / `STATI_SINISTRO`.
- `priorita` — String(20), default `media`. Enum Python `PrioritaPratica`
  (`bassa`/`media`/`alta`/`urgente`) con `.label`, persistito come String.
- `tipologia` — String(40), obbligatoria. Enum Python `TipologiaPratica` con i 10
  valori richiesti e label italiane per la UI (es. `bersani` → "Legge Bersani",
  `pagamento_polizza_rata` → "Pagamento Polizza/Rata"). Persistito come String
  (niente ENUM nativo Postgres, più facile da migrare).
- `operatore` — String(120), campo libero (app mono-utente, nessun modello User).
- Timestamp `data_apertura` e `data_ultimo_aggiornamento` (con `onupdate`).
- Validazione applicativa di `stato`/`priorita`/`tipologia` via `@validates`.

### Relazioni Pratica
- `cliente_id` → FK `clienti.id`, **NOT NULL** (ogni pratica ha un cliente).
  Inverso `Cliente.pratiche` con `cascade="all, delete-orphan"` (coerente col
  resto della scheda 360°).
- `contratto_id` → FK `contratti.id`, **nullable**. Inverso `Contratto.pratiche`
  senza cascade (eliminando il contratto la pratica resta, il FK va a NULL).
- `sinistro_id` → FK `sinistri.id`, **nullable**. Inverso `Sinistro.pratiche`.

### Estensioni al modello `Cliente`
- `codice_fiscale` — esisteva già come `String(20)` senza vincoli. Portato a
  `String(16)` con **indice univoco** (`ix_clienti_codice_fiscale`, i NULL
  restano ammessi) e validazione formato CF italiano via `@validates` (regex
  `^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$`, con normalizzazione upper/trim).
- `indirizzo_completo` — implementato come **property Python** (non colonna): i
  campi `indirizzo/cap/citta/provincia` esistono già, aggregarli a runtime evita
  duplicazione e disallineamenti (unica fonte di verità).

### Nuovo modello `Veicolo` (tabella `veicoli`)
Scenario trovato: **nessun** modello Veicolo esistente. Un cliente
assicurativo può avere **più veicoli** (più polizze auto), quindi si è scelta la
relazione **1:N** (`Veicolo.cliente_id` FK → `clienti.id`) anziché mettere
`targa` su Cliente. Campi: `targa` (String(10), univoco, indice
`ix_veicoli_targa`, validazione formato targa italiana `^[A-Z]{2}\d{3}[A-Z]{2}$`
con normalizzazione), `marca`, `modello`, `created_at`. Inverso `Cliente.veicoli`
con cascade delete-orphan.

### Migrazioni (Flask-Migrate / Alembic — nuova introduzione)
Il progetto NON aveva migrazioni: lo schema veniva creato con `db.create_all()`
all'avvio. Introdotto **Flask-Migrate** come fonte di verità dello schema:
- `requirements.txt`: aggiunto `Flask-Migrate==4.0.7`.
- `app.py`: inizializzato `Migrate`; all'avvio, al posto di `db.create_all()`,
  ora gira `upgrade()` (poi `seed()`). Su DB nuovo (o su Render) crea tutte le
  tabelle fino alla revisione head. Guardia `CRM_SKIP_STARTUP_UPGRADE=1` per
  eseguire i comandi `flask db ...` senza innescare upgrade/seed.
- `migrations/` inizializzato; prima revisione `35a972207853` (schema completo
  incluse `pratiche`, `veicoli` e gli indici). **Reversibilità verificata**:
  `upgrade` → `downgrade base` (droppa tutto) → `upgrade` di nuovo, ok.
- ⚠️ DB locale pre-esistente: un vecchio `crm.db` creato con `create_all()` non
  ha la tabella `alembic_version`; va **eliminato una volta** (contiene solo dati
  di esempio) per adottare le migrazioni. All'avvio l'app lo rileva e logga un
  avviso invece di andare in errore.

Sezioni esistenti (Pipeline, Documenti, Incassi, Messaggi, ecc.) non modificate.
