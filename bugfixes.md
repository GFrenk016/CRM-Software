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


