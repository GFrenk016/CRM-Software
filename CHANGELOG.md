# Changelog — CRM Assicurativo

Questo documento riporta le modifiche effettivamente entrate nel branch `main`, ricostruite dai commit e dai diff del repository [`GFrenk016/CRM-Software`](https://github.com/GFrenk016/CRM-Software).

> **Nota sulla data richiesta:** un mese esatto prima del 22 settembre 2026 è il **22 agosto 2026**, ma in quella data non risultano commit. Il blocco funzionale più vicino precedente è stato integrato l'**8 agosto 2026**. Il commit successivo, del **1° settembre 2026**, aggiorna soltanto il README.

## 1 settembre 2026 — Documentazione del progetto

### Documentazione

- Riscritto e ampliato il README del CRM: **366 righe aggiunte e 87 rimosse**.
- Nessuna modifica applicativa o allo schema dati in questa data.

**Commit:** [`ec173f5` — README Aggiornato](https://github.com/GFrenk016/CRM-Software/commit/ec173f552ebbe322f3886879097fe893f5f90ee0)

---

## 8 agosto 2026 — Stabilizzazione, usabilità e prevenzione della perdita di dati

La giornata comprende un primo intervento trasversale sui flussi del CRM e una successiva serie di 14 correzioni, confluite nella [PR #15](https://github.com/GFrenk016/CRM-Software/pull/15). Il diff finale della PR #15 modifica **23 file**, con **671 righe aggiunte e 101 rimosse**.

### Anagrafica clienti

#### Aggiunto

- Introdotta l'**archiviazione non distruttiva dei clienti** tramite i campi `archiviato` e `archiviato_at`.
- Aggiunte l'archiviazione multipla dei clienti selezionati, una finestra con l'elenco degli archiviati e l'azione di ripristino.
- I clienti archiviati non compaiono più nell'elenco operativo né nella Pipeline, ma conservano contratti, sinistri, incassi e tutti gli altri dati collegati.
- Convertiti in menu a tendina i filtri per città, provincia, professione, stato civile e anno di scadenza. Le opzioni vengono ricavate dai valori realmente presenti tra i clienti attivi.

#### Corretto

- Il filtro testuale generico resta a ricerca parziale; i nuovi filtri a tendina usano invece un confronto esatto, evitando che, per esempio, “Roma” includa anche “Roma Nord”.
- Gli errori del codice fiscale non causano più una pagina 500:
  - formato non valido → messaggio leggibile;
  - codice fiscale duplicato → avviso specifico;
  - i valori già inseriti nel form vengono conservati dopo l'errore.

**Commit principali:** [`c8dd7f7`](https://github.com/GFrenk016/CRM-Software/commit/c8dd7f7f050b37501d4e909c543e753dde834889), [`924a79d`](https://github.com/GFrenk016/CRM-Software/commit/924a79dce862a578c0790eb6ff3ae2499d01c6fe), [`c809a05`](https://github.com/GFrenk016/CRM-Software/commit/c809a05519e4735d17514ce60e2438adb4823a54)

### Pratiche e collegamenti tra dati

#### Corretto

- Nei form delle pratiche, contratti, sinistri e veicoli collegabili vengono caricati soltanto per il cliente selezionato.
- Aggiunto anche un controllo lato server contro collegamenti incrociati ottenuti tramite richieste costruite manualmente.
- Il Lead collegato non viene più scelto da una lista globale: è mostrato in sola lettura e ricavato automaticamente dal cliente.
- Rimosso il campo `operatore` dalla Pratica, perché il CRM è mono-utente e il dato era ridondante.
- Il caricamento iniziale dei contratti ora funziona anche nei form completi di sinistri e incassi, non soltanto dopo aver cambiato cliente o dentro una modale. Questo evita menu vuoti in modifica e il rischio di salvare una polizza errata.
- Lo stato `persa` è stato spostato dagli stati riservati al flusso di emissione agli stati comuni. Ora qualunque tipologia di pratica può essere chiusa come persa e lo stato non viene azzerato riaprendo il form.

#### Modificato

- Le nuove pratiche partono con priorità **Urgente**; in modifica viene rispettata la priorità già salvata.

**Commit principali:** [`c8dd7f7`](https://github.com/GFrenk016/CRM-Software/commit/c8dd7f7f050b37501d4e909c543e753dde834889), [`f2b572c`](https://github.com/GFrenk016/CRM-Software/commit/f2b572cb3b3abee1f3911e4bfc06c1c5c4372979), [`889ba2c`](https://github.com/GFrenk016/CRM-Software/commit/889ba2c50b2d45708f959a7f2c723c3997de23f1), [`6b4db27`](https://github.com/GFrenk016/CRM-Software/commit/6b4db270befbc3ecba7ae290af82e9f09336706e)

### Motivi di perdita e ricontatto

#### Aggiunto

- Aggiunto il campo libero `motivo_perdita_dettaglio` quando il motivo selezionato è `altro`.
- Aggiunta la migrazione Alembic `7026369d95aa` per la nuova colonna.
- Il dettaglio libero viene mostrato accanto al motivo nella pratica e nella bacheca e viene eliminato automaticamente se il motivo cambia da `altro` a un valore specifico.

#### Corretto

- La lista “Da ricontattare questo mese” non aveva un errore nel calcolo delle date: il problema reale era l'impossibilità di assegnare lo stato `persa` ad alcune tipologie. Il filtro mensile è rimasto invariato ed è stata documentata la diagnosi nel codice.

**Commit:** [`a3da36d`](https://github.com/GFrenk016/CRM-Software/commit/a3da36de77a6253579764868b48a9856190caa7a), [`711a144`](https://github.com/GFrenk016/CRM-Software/commit/711a14464b90815e2397ad66204fbb9d009e1d46)

### Comunicazioni e messaggistica

#### Aggiunto

- La composizione di un messaggio WhatsApp o email ora crea realmente una riga nello storico comunicazioni.
- La registrazione avviene per ogni destinatario effettivamente aperto e salva canale, recapito, testo personalizzato e data/ora.
- L'esito usato è `registrato`, non `consegnato`, perché il CRM apre un link esterno e non può verificare la consegna.
- Aggiunto il pulsante di eliminazione di una comunicazione, con conferma e ritorno alla scheda cliente o pratica di provenienza.
- In caso di mancata registrazione viene mostrato un messaggio di errore, evitando uno storico apparentemente completo ma incompleto nei dati.

**Commit:** [`a1a7dd4`](https://github.com/GFrenk016/CRM-Software/commit/a1a7dd4970e02abe18155c892d533358fca3abe3), [`118251a`](https://github.com/GFrenk016/CRM-Software/commit/118251a2ef74da5d77cd0bd961c73c5b80132450)

### Contratti, sinistri e incassi

#### Aggiunto

- Nella scheda di un contratto sono stati aggiunti i pulsanti **Nuovo sinistro** e **Nuovo incasso**.
- I relativi form si aprono in sovrimpressione con cliente e contratto già selezionati.

#### Corretto

- Il menu Contratto nei form di sinistri e incassi viene popolato correttamente al primo caricamento e mantiene la polizza già salvata durante la modifica.

**Commit:** [`04d0ded`](https://github.com/GFrenk016/CRM-Software/commit/04d0ded468b9ea044f8dfc1b2aa02c594715e205), [`f2b572c`](https://github.com/GFrenk016/CRM-Software/commit/f2b572cb3b3abee1f3911e4bfc06c1c5c4372979)

### Preventivi

#### Modificato

- Chiarita la precedenza tra i campi “Compagnia scelta” e “Compagnie consultate”.
- Se una riga delle compagnie consultate è marcata come scelta, compagnia e premio principali diventano campi derivati e non sono più modificabili separatamente.
- Aggiunti stile visivo e testo esplicativo per segnalare la derivazione dei valori.

**Commit:** [`81ef5de`](https://github.com/GFrenk016/CRM-Software/commit/81ef5dea54e7b1c975067c31e68136420e5d4f1a)

### Bacheca e filtri operativi

#### Aggiunto

- Aggiunti collegamenti “vedi tutti” alle card **Incassi in ritardo** e **Sinistri aperti**.
- Aggiunto il filtro aggregato `aperti` per i sinistri, che comprende tutti i sinistri non chiusi (`aperto` e `in_perizia`).

#### Corretto

- I collegamenti della bacheca ora aprono liste coerenti con il numero mostrato:
  - scadenze limitate a 30 giorni;
  - incassi filtrati su `in_ritardo`;
  - sinistri filtrati su tutti i non chiusi.
- “Vedi tutti” compare anche quando la card contiene meno di cinque elementi, purché esista almeno un risultato.

**Commit:** [`cc4ecca`](https://github.com/GFrenk016/CRM-Software/commit/cc4ecca104ca85d5fafaa3866c7a1a51cc3ec256)

### Documenti

#### Aggiunto

- Aggiunta l'anteprima del file selezionato prima del caricamento:
  - miniatura per le immagini;
  - icona, nome e dimensione per gli altri file.

#### Modificato

- Le card dei documenti hanno i pulsanti fissati e allineati in basso.
- I nomi troppo lunghi vengono troncati con ellissi e restano leggibili per intero tramite tooltip.

#### Corretto

- Riparato il pulsante con l'icona dell'occhio: le virgolette prodotte dal JSON interrompevano l'attributo `onclick`, generando un errore JavaScript e impedendo l'apertura dell'anteprima.

**Commit:** [`c8dd7f7`](https://github.com/GFrenk016/CRM-Software/commit/c8dd7f7f050b37501d4e909c543e753dde834889), [`ffde79b`](https://github.com/GFrenk016/CRM-Software/commit/ffde79b40ebcf9390ddfc9c98de741d27b2965cf), [`c08808d`](https://github.com/GFrenk016/CRM-Software/commit/c08808d9b747a45a5c27fde59b0e1bc6064ae2ac)

### Interfaccia e modali

#### Modificato

- Uniformati i form Nuovo/Modifica di preventivi, contratti, sinistri e incassi: possono essere caricati nello stesso pannello modale centrale senza duplicare il markup dei campi.
- Mantenute le pagine complete come fallback se il caricamento della modale fallisce.
- Aumentata la durata minima dei toast da 3,5 a 5 secondi; i messaggi più lunghi restano visibili fino a 10 secondi.
- Rimossa la targa duplicata nella sezione Veicoli della scheda cliente.

**Commit:** [`c8dd7f7`](https://github.com/GFrenk016/CRM-Software/commit/c8dd7f7f050b37501d4e909c543e753dde834889), [`7133d40`](https://github.com/GFrenk016/CRM-Software/commit/7133d409ee02bd1774c5758b419862f1f8837268), [`57e8699`](https://github.com/GFrenk016/CRM-Software/commit/57e8699be086d66d78b99197abaa6a6a3b55da0b)

### Collaudo e documentazione tecnica

- Aggiunto `collaudo_subagente.md` con una procedura di collaudo estesa.
- Aggiornato `bugfixes.md` con cause, verifiche, attività completate e attività non eseguite.
- Aggiustata la spaziatura del titolo “Documenti collegati” nel dettaglio pratica.

**Commit:** [`1e60527`](https://github.com/GFrenk016/CRM-Software/commit/1e6052730258b6291bebb30e88dd618d6e36556e), [`6a27c29`](https://github.com/GFrenk016/CRM-Software/commit/6a27c29ec84e199a17a00c0d5bc1a071c4f99101)

### Integrazione finale del blocco

**Merge:** [`2e3a644` — Fix 14 bugs: states, forms, UI, and data loss issues](https://github.com/GFrenk016/CRM-Software/commit/2e3a644ee87aa6dbd74ecb8bd00e45ef4f36dc22) · [PR #15](https://github.com/GFrenk016/CRM-Software/pull/15)

---

## 6 agosto 2026 — Fase C: arricchimento delle viste

### Preventivi e confronto compagnie

- Introdotto il modello `PreventivoCompagnia` per registrare più compagnie consultate sullo stesso preventivo, con premio, garanzie e note per ciascuna.
- Aggiunti vincolo univoco preventivo/compagnia e migrazione Alembic dedicata.
- `Preventivo.compagnia_id` rappresenta la compagnia scelta; `premio_proposto` rappresenta il relativo premio.
- Aggiunte le proprietà derivate per premio più basso, compagnia più economica e differenza rispetto alla scelta effettuata.
- Nel form sono disponibili righe ripetibili, selezione della compagnia scelta ed evidenza automatica dell'offerta più economica.
- Lista preventivi e dettaglio pratica mostrano numero di compagnie consultate, migliore quotazione e maggior costo della scelta.

### Comunicazioni cliente

- Aggiunta alla scheda cliente una sezione ordinata cronologicamente con canale, destinatario, testo, data, ora ed esito.
- Introdotta una macro riutilizzabile anche nel dettaglio pratica.
- Le comunicazioni rimaste senza cliente dopo una cancellazione continuano a essere leggibili tramite l'etichetta cliente memorizzata.

### Ricerca per codice fiscale

- Aggiunta la pagina **Ricerca CF** e la relativa voce nella barra laterale.
- Supportata la ricerca completa o parziale, normalizzata in maiuscolo.
- Aggiunta una vista aggregata in sola lettura con pratiche, polizze, preventivi, targhe, documenti, appuntamenti, comunicazioni e sinistri.
- Gestiti esplicitamente sia il caso senza risultati sia quello con più corrispondenze parziali.

### Cross-selling sui veicoli

- Aggiunto il calcolo dei veicoli del cliente privi di un contratto attivo rilevabile.
- Aggiunti avvisi nel dettaglio pratica e nel form preventivo per evidenziare possibili veicoli ancora da assicurare.

**Commit:** [`e848db0`](https://github.com/GFrenk016/CRM-Software/commit/e848db0063ba2be0fdcaaea8aa2453f283b7a9b9), [`dec010d`](https://github.com/GFrenk016/CRM-Software/commit/dec010d5d27a79709f8bb0b1d6508230f4174aa4), [`9c281c4`](https://github.com/GFrenk016/CRM-Software/commit/9c281c4da44aa768d65707b53d06ed7d4f36966e), [`a67c332`](https://github.com/GFrenk016/CRM-Software/commit/a67c332343675482e4c61d61ff6f67354500a32a), [`76518fe`](https://github.com/GFrenk016/CRM-Software/commit/76518feabf40658cead42f9bfdfa1d97b8c4fcca) · [PR #14](https://github.com/GFrenk016/CRM-Software/pull/14)

---

## 4 agosto 2026 — Fase B: logica di business delle pratiche

### Dettaglio pratica

- Aggiunta la pagina di dettaglio della Pratica con dati principali, avanzamento, collegamenti, documenti, appuntamenti, comunicazioni e preventivi.
- Aggiunti collegamenti dalla lista pratiche e dalla scheda cliente.

### Stati e schema

- Introdotta la catena degli stati di emissione, con badge e stati disponibili in base alla tipologia di pratica.
- Aggiunti ordinamento degli stati e scala di avanzamento.
- Aggiunti i campi per date di pagamento, emissione e invio certificato, motivo di perdita, data di ricontatto e veicolo collegato.
- Introdotto il modello `ChecklistDocumento`, distinto dai documenti già ricevuti.

### Automatismi e controlli

- Aggiunta priorità automatica urgente alla creazione per Bersani, nuovo acquisto e sostituzione veicolo.
- Aggiunto il controllo dei campi anagrafici mancanti in base alla tipologia.
- Aggiunta la richiesta documenti via WhatsApp/email con registrazione della comunicazione.
- Aggiunto l'ordinamento dei preventivi in base alla scadenza della polizza del cliente.

### Flusso operativo

- Aggiunto il comando “prossimo step”, con aggiornamento automatico delle date di passaggio.
- Aggiunte le Impostazioni agenzia per ragione sociale, IBAN e finestre orarie di emissione.
- Aggiunto un avviso non bloccante per emissioni eseguite fuori dalle finestre configurate.
- Aggiunta la gestione degli appuntamenti da pratica e scheda cliente, compreso il tipo OTP.
- Aggiunta in bacheca la lista dei clienti da ricontattare nel mese.
- Raggruppati i filtri pratica in famiglie, con conteggi ottenuti tramite un'unica query aggregata.

### Migrazioni

- Rimossa una migrazione A2 duplicata che creava due head Alembic e impediva l'avvio su un database nuovo.
- Ripristinata una catena di migrazioni lineare e verificati upgrade, downgrade e ricreazione da zero.

**Commit:** [`977d574`](https://github.com/GFrenk016/CRM-Software/commit/977d5742ed970b9ee9c6d6cee5599617011ac5fd), [`fae48c0`](https://github.com/GFrenk016/CRM-Software/commit/fae48c0d874b65b1cd11ebe712803b1950234016), [`f96bb54`](https://github.com/GFrenk016/CRM-Software/commit/f96bb54380ddb95b3d0fb816b2d873a0013f6f1f), [`a0b09a1`](https://github.com/GFrenk016/CRM-Software/commit/a0b09a1e1634978624e76bb848203cadd5bcc597), [`4bff727`](https://github.com/GFrenk016/CRM-Software/commit/4bff727fa4c73b90eef49b8d56006d3857d99a62) · [PR #13](https://github.com/GFrenk016/CRM-Software/pull/13)

---

## 1 agosto 2026 — Fase A2: correzioni alle relazioni e conservazione dello storico

### Modello dati

- Invertita la relazione Pratica–Preventivo:
  - rimosso il precedente collegamento uno-a-uno dalla pratica;
  - aggiunto `preventivi.pratica_id`;
  - una pratica può ora contenere più preventivi e revisioni mantenendo lo storico.
- Reso nullable `comunicazioni.cliente_id` con cancellazione `SET NULL`.
- Rimossa la cancellazione a cascata delle comunicazioni insieme al cliente: lo storico resta disponibile come registro di audit.
- Impostato `da_svolgere` come valore iniziale degli appuntamenti.
- Rafforzate le migrazioni SQLite con nomi espliciti per i vincoli e controllo di sicurezza nel downgrade in presenza di comunicazioni orfane.

**Merge:** [`806822d`](https://github.com/GFrenk016/CRM-Software/commit/806822d41ded3ffe7b97893209902314f7f05ad7) · [PR #11](https://github.com/GFrenk016/CRM-Software/pull/11)

---

## Correzioni identificate ma non implementate nel periodo

Per evitare di confondere diagnosi e modifiche realmente consegnate, queste voci risultano annotate ma ancora aperte:

- messaggi di errore mancanti per alcuni campi obbligatori;
- validazione email non uniforme;
- gestione di input non numerici in alcuni form di sinistri e incassi;
- timestamp UTC mostrati come se fossero già in ora locale;
- persistenza di produzione ancora legata a SQLite locale;
- collegamento diretto tra Contratto e Veicolo non presente;
- integrazioni automatiche WhatsApp Business, social e Google Form non implementate.

