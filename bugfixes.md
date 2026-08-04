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

## 🅰️➕ Fase A2 — Fondamenta mancanti

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

## 🅱️ Fase B — Logica di business sulla Pratica

- [ ] Stato **"documentazione_da_integrare"** su Pratica (+ badge CSS)

- [ ] **Elenco documenti mancanti** collegato alla pratica
      Nuovo modello checklist (pratica, tipo documento, ricevuto sì/no),
      distinto da `Documento` che rappresenta il file caricato.
      ↳ dipende da: `pratica_id` su Documento (A2)

- [ ] **Verifica dei dati anagrafici ricevuti**
      Il documento dice "verifica dei dati ricevuti", non solo dei documenti.
      Segnalare campi obbligatori mancanti/incompleti sulla pratica.

- [ ] **Invio richiesta documentazione al cliente**
      Il documento dice "invio della richiesta al cliente" — non "automatico".
      Il CRM prepara il messaggio, l'operatore lo invia.
      ↳ dipende da: modello Comunicazione (A2)

- [ ] **Priorità automatica**: massima per Bersani, nuovi acquisti, sostituzioni veicolo

- [ ] **Ordinamento preventivi ordinari per scadenza polizza**

- [ ] **Flusso esito positivo** (8 step)
      richiesta doc mancante → invio IBAN → verifica pagamento → appuntamento OTP
      → coda emissioni → emissione polizza → invio certificato → chiusura pratica
      ↳ dipende da: Appuntamento (A2), Impostazioni/IBAN (A2), decisione tecnica #1

- [ ] **Vincolo due finestre giornaliere di emissione**
      ↳ dipende da: domanda cliente #1 (orari)

- [ ] **Flusso esito negativo → "Clienti da ricontattare"**
      Campi richiesti dal cliente: Nome, Cognome, CF, Targa, data scadenza,
      motivo perdita, note.
      ↳ dipende da: decisione tecnica #2

- [ ] **Ricontatto alla scadenza successiva**
      Come lista "da ricontattare questo mese" che compare all'apertura del CRM.
      Un invio che parte a CRM chiuso richiede il gestionale online → fuori scope Fase 1.

---

## 🅲 Fase C — Arricchimento vista

- [ ] **Preventivo: compagnie consultate (più di una), garanzie, note**
      ⚠️ `premio_proposto` e `stato` (bozza/inviato/accettato/rifiutato) **esistono già** —
      non rifarli. Manca: tabella figlia con una riga per compagnia consultata
      (premio e garanzie proprie), più il campo note.
      ↳ dipende da: domanda cliente #3 (quali garanzie)

- [ ] **Storico preventivi visibile su Pratica e su Scheda Cliente**
      ↳ dipende da: Pratica ↔ Preventivo (A2)

- [ ] **Scheda cliente completa**: anagrafica, veicoli, preventivi, polizze,
      documenti, comunicazioni, appuntamenti, stato pratiche
      ↳ dipende da: Appuntamento + Comunicazione (A2)

- [ ] **Ricerca avanzata per Codice Fiscale**
      Un CF → pratiche, polizze, preventivi, targhe, documenti, comunicazioni

- [ ] **Evidenziazione altri veicoli collegati al cliente** (cross selling / fidelizzazione)

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
2. [ ] **Quali documenti servono per ogni tipologia di pratica** (Bersani ≠ rinnovo) → blocca Fase B
3. [ ] **Quali garanzie tracciare nel preventivo** → blocca Fase C
4. [ ] **"Collegamento social": quali piattaforme e per fare cosa?** (ricevere richieste dai DM? pubblicare? acquisire lead?) → blocca Fase D
5. [ ] **Il gestionale resta sul PC o va online?** → condiziona tutti gli automatismi
      e la persistenza reale dei dati

---

## 🔧 Decisioni tecniche (da prendere internamente, non dal cliente)

1. [ ] **Flusso a 8 step: stati della pratica o campo separato `step_flusso`?**
       Stati = `STATI_PRATICA` si allarga, ma i 5 attuali si sovrappongono
       ("in lavorazione" vs gli step). Campo separato = più pulito, un concetto in più.
       → blocca Fase B

2. [ ] **"Clienti da ricontattare": FK o tabella piatta?**
       Nome/Cognome/CF stanno già su Cliente, la Targa su Veicolo. FK = coerente col
       resto del progetto ("relazioni vere, non testo libero"), tabella piatta = più
       semplice ma i dati divergono se il cliente cambia qualcosa.
       → blocca Fase B

3. [ ] **"Coda emissioni": stato della pratica, vista dedicata, o entrambi?**
       → blocca Fase B

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