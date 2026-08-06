# Task list — CRM Assicurativo, Fase 1 (Analisi Funzionale)

> Fonte dei requisiti: `CRM_Assicurativo_Analisi_Funzionale_Fase1.docx` (documento del cliente).
> Ogni task qui deriva da una frase di quel documento. Verificata contro il codice
> esistente: le task descrivono solo ciò che manca davvero.

---

## 🅰️ Fase A — Fondamenta ✅ COMPLETATA

- [x] Modello **Pratica** (numero identificativo `PR-{anno}-{progressivo}`, stato, priorità, operatore, tipologia)
- [x] 10 tipologie di pratica: nuovo preventivo, Bersani, nuovo acquisto, rinnovo, pagamento polizza/rata, sostituzione veicolo, sospensione, riattivazione, consulenza, sinistro
- [x] Campo **Codice Fiscale** su Cliente (con validazione formato)
- [x] Campo **indirizzo completo** su Cliente (property `indirizzo_completo`)
- [x] Modello **Veicolo** con **targa** (validata) per preventivi RC Auto
- [x] Collegamento Pratica ↔ Cliente / Lead
- [x] Collegamento Pratica ↔ Contratto / Sinistro
- [x] Collegamento Preventivo ↔ Veicolo
- [x] Sezione **Pratiche** nel frontend (sidebar tra Pipeline e Anagrafica, lista con filtri)

---

## 🅰️➕ Fase A2 — Fondamenta mancanti ✅ COMPLETATA

> Modelli e collegamenti che le Fasi B e C danno per esistenti ma che nessuna task creava.
> Da fare **prima** di B e C, altrimenti quelle fasi si bloccano a metà.

- [X] **Collegamento Pratica ↔ Preventivo**
      Oggi Pratica ha `contratto_id` e `sinistro_id` ma **non** `preventivo_id`,
      mentre "nuovo preventivo" è la prima tipologia di pratica e la Fase C
      richiede lo storico preventivi sulla Pratica.

- [X] **Modello Appuntamento** (cliente, pratica, data/ora, tipo, note, esito)
      Richiesto dal flusso Fase B ("appuntamento OTP") e dalla scheda cliente Fase C.
      Oggi non esiste.

- [X] **Modello Comunicazione** (pratica, cliente, canale, destinatario, testo, data, esito)
      La Fase C deve mostrare le comunicazioni nella scheda cliente, ma `messaggi.py`
      genera solo link `wa.me`/`mailto` e **non registra niente**.

- [X] **Aggiungere `pratica_id` a Documento** (nullable)
      Serve per "registrazione dei documenti mancanti" di quella pratica e per
      "invio certificato" alla chiusura. Oggi Documento è legato solo al Cliente.

- [X] **Impostazioni agenzia** (IBAN, ragione sociale, orari finestre emissione)
      Il flusso prevede "invio IBAN" ma l'IBAN non esiste da nessuna parte nel modello.
      Tabella impostazioni a riga singola o costanti in `config.py`.

- [X] **Punto d'ingresso: ogni contatto genera una pratica**
      Prima frase del metodo operativo del cliente. Oggi creando un Cliente nasce
      automaticamente un **Lead**, non una Pratica. Va allineato.

---

## 🅱️ Fase B — Logica di business sulla Pratica ✅ COMPLETATA

> Le spunte erano rimaste vuote nonostante la fase fosse completata e mergiata
> (PR #13). Verificate una per una contro il codice e aggiornate in Fase C.

- [X] Stato **"documentazione_da_integrare"** su Pratica (+ badge CSS)
      `STATI_PRATICA_EMISSIONE` in models.py, badge in style.css.

- [X] **Elenco documenti mancanti** collegato alla pratica
      Modello `ChecklistDocumento` (pratica, tipo, ricevuto, note), distinto da
      `Documento`; gestito dal dettaglio pratica.

- [X] **Verifica dei dati anagrafici ricevuti**
      `Pratica.campi_mancanti` + `CAMPI_RICHIESTI_PER_TIPOLOGIA`, avviso in cima
      al dettaglio pratica.

- [X] **Invio richiesta documentazione al cliente**
      Il CRM compone testo e link wa.me/mailto e REGISTRA la comunicazione;
      l'invio resta all'operatore (nessun automatismo).

- [X] **Priorità automatica**: massima per Bersani, nuovi acquisti, sostituzioni veicolo
      Evento `before_flush` alla creazione, senza sovrascrivere le scelte manuali.

- [X] **Ordinamento preventivi ordinari per scadenza polizza**
      Filtro "Ordina: scadenza polizza attuale" nella lista preventivi.

- [X] **Flusso esito positivo** (8 step)
      `ORDINE_STATI_PRATICA` + scala di avanzamento e pulsante "prossimo step"
      sul dettaglio pratica, con le date di passaggio fissate automaticamente.

- [X] **Vincolo due finestre giornaliere di emissione**
      Avviso NON bloccante sul passaggio a coda/emissione fuori orario.
      Gli orari (9-11 / 15-17) restano un default: domanda cliente #1 aperta.

- [X] **Flusso esito negativo → "Clienti da ricontattare"**
      Stato "persa" + `motivo_perdita` e `data_scadenza_riferimento` sulla
      Pratica, veicolo collegato per la targa.

- [X] **Ricontatto alla scadenza successiva**
      Lista "Da ricontattare questo mese" in bacheca. L'invio a CRM chiuso
      resta fuori scope Fase 1 (richiede il gestionale online).

---

## 🅲 Fase C — Arricchimento vista ✅ COMPLETATA

- [X] **Preventivo: compagnie consultate (più di una), garanzie, note**
      Nuovo modello `PreventivoCompagnia` (premio, garanzie, note per riga),
      unicità su (preventivo, compagnia), property derivate `premio_piu_basso` e
      `compagnia_piu_economica`; `Preventivo.compagnia_id` è ora la "compagnia
      scelta" e `premio_proposto` il suo premio. Nel form: righe ripetibili con
      evidenza del premio più basso e promozione a compagnia scelta.
      ⚠️ Le **garanzie** sono un elenco PROVVISORIO (costante `GARANZIE`,
      `# TODO CLIENTE`) salvato come stringa separata da virgola: ampliarlo non
      richiederà una migrazione. Domanda cliente #3 ancora aperta.

- [X] **Storico preventivi visibile su Pratica e su Scheda Cliente**
      *Era già presente* (sezione "Preventivi collegati" sulla Pratica e
      "Preventivi" sulla scheda cliente): non rifatto, solo arricchito con
      compagnia scelta, premio, numero di compagnie consultate e quotazione
      migliore.

- [X] **Scheda cliente completa**: anagrafica, veicoli, preventivi, polizze,
      documenti, comunicazioni, appuntamenti, stato pratiche
      *Già presente tutto tranne le comunicazioni*, aggiunte in questa fase
      (canale, destinatario, testo, data ed esito, dalla più recente).

- [X] **Ricerca avanzata per Codice Fiscale**
      Nuova pagina `/ricerca` ("Ricerca CF" in sidebar): un CF, anche parziale,
      apre la vista aggregata in sola lettura (pratiche, polizze, preventivi,
      targhe, documenti, appuntamenti, comunicazioni, sinistri). Il *filtro* su
      CF nell'anagrafica *esisteva già* e non è stato toccato: quello che
      mancava era la vista aggregata.

- [X] **Evidenziazione altri veicoli collegati al cliente** (cross selling / fidelizzazione)
      Property `Cliente.veicoli_scoperti` (veicoli senza contratto attivo) e
      avviso nel dettaglio pratica e nel form preventivo.
      ⚠️ La copertura si DEDUCE da preventivo/pratica collegati al contratto:
      manca un legame diretto Veicolo ↔ Contratto, quindi una polizza caricata a
      mano lascia il veicolo fra gli "scoperti" (`# TODO CLIENTE` in models.py).

---

## 🅳 Fase D — Integrazioni esterne

- [ ] **Collegamento WhatsApp**
      Oggi: link `wa.me` cliccabili, gratis. WhatsApp che invia da solo richiede
      WhatsApp Business API: ~30-50 €/mese di piattaforma + centesimi per messaggio,
      template pre-approvati da Meta, consenso esplicito del cliente.
      Decisione commerciale, non tecnica.

- [ ] **Collegamento social**
      ↳ dipende da: domanda cliente #4 — requisito attualmente non definito,
      non stimabile né costruibile così com'è.

- [ ] **Google Form → import dati nel gestionale**
      Due strade: (a) export CSV dal Form + bottone di import nel CRM — subito, gratis;
      (b) API Google con account di servizio — più automatico, ma il CRM deve
      essere aperto per leggere.
      Form: `https://docs.google.com/forms/d/e/1FAIpQLSf8iBsIeViS7LT-f98IdLLsHaqEHYkD9zLQ7x1qiDvBgp52Zg/viewform`

---

## ❓ Domande aperte per il cliente

1. [ ] **Orari delle due finestre giornaliere di emissione** → blocca Fase B
      Fase B è andata avanti con 9-11 / 15-17, modificabili da Impostazioni.
2. [ ] **Quali documenti servono per ogni tipologia di pratica** (Bersani ≠ rinnovo) → blocca Fase B
      Fase B è andata avanti con la checklist compilabile a mano sulla pratica.
3. [ ] **Quali garanzie tracciare nel preventivo** → blocca Fase C
      Fase C è andata avanti con l'elenco provvisorio della costante `GARANZIE`
      (rc_auto, furto_incendio, kasko, cristalli, assistenza_stradale,
      tutela_legale, infortuni_conducente, eventi_naturali, atti_vandalici):
      ampliarlo è una modifica a quella costante, senza migrazione.
4. [ ] **"Collegamento social": quali piattaforme e per fare cosa?** (ricevere richieste dai DM? pubblicare? acquisire lead?) → blocca Fase D
5. [ ] **Il gestionale resta sul PC o va online?** → condiziona tutti gli automatismi
      e la persistenza reale dei dati

---

## 🔧 Decisioni tecniche (da prendere internamente, non dal cliente)

1. [X] **Flusso a 8 step: stati della pratica o campo separato `step_flusso`?**
       Decisa in Fase B: **stati della pratica**. `STATI_PRATICA` si allarga con
       gli stati di emissione e `STATI_PER_TIPOLOGIA` evita che le tipologie
       senza emissione li vedano; la scala vive in `ORDINE_STATI_PRATICA`.

2. [X] **"Clienti da ricontattare": FK o tabella piatta?**
       Decisa in Fase B: **FK**, coerente col resto del progetto. Nessuna tabella
       nuova: la lista è derivata dalle pratiche "perse" con
       `data_scadenza_riferimento`, e nome/CF/targa si leggono dalle relazioni.

3. [X] **"Coda emissioni": stato della pratica, vista dedicata, o entrambi?**
       Decisa in Fase B: **stato** (`in_coda_emissione`), con il filtro per
       famiglia "in emissione" nella lista pratiche al posto di una vista a sé.

---

## ⚙️ Debito tecnico noto (fuori scope funzionale)

- [ ] `config.py` usa SQLite hardcoded anche in produzione: su Render il filesystem
      è effimero, i dati non persistono tra deploy. Servirebbe leggere `DATABASE_URL`
      da env per usare Postgres.
- [ ] Bug aperto nella sezione Veicoli della scheda cliente (da specificare)
- [ ] `avvia_crm.bat`: la logica batch non è mai stata eseguita su Windows reale
      (scritta e riletta, non testata dal vivo)

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