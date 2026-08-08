# Bugfixes

## Sessione "15 task" — riepilogo

**14 task chiuse su 14**, un commit per task perché una regressione si isoli
subito. La lista dettagliata è qui sotto; qui sta solo ciò che non era ovvio.

**Tre task avevano una causa diversa da quella ipotizzata**, e vale la pena
saperlo:

- **"Lead collegato" al primo caricamento**: era **già risolto** (c8dd7f7), la
  voce era rimasta solo non spuntata. Verificato in sei scenari. Ma lo stesso bug
  era ancora aperto sull'altro caricatore (contratti di sinistri e incassi), dove
  in modifica la polizza collegata non compariva affatto: corretto lì.
- **"Da ricontattare questo mese"**: il criterio di intervallo della query **non
  ha errori di confine** (verificato sui 36 mesi di tre anni). Le pratiche non
  comparivano perché per le tipologie senza emissione lo stato "persa" non era
  selezionabile — cioè la task dello stato "persa", non la query.
- **Comunicazioni non registrate**: il record non si perdeva per strada, **non
  veniva mai creato**. La modale "Messaggio" non ha mai avuto una rotta che
  scrivesse una Comunicazione.

**Due bug di perdita di dato trovati per strada**, non nella lista iniziale:
riaprire il form di una pratica persa senza emissione ne **azzerava lo stato** al
salvataggio; e in modifica di un sinistro/incasso il menu Contratto era vuoto,
col rischio di salvare la polizza sbagliata.

**Cosa NON è stato fatto**, e perché:

- Le task erano **14, non 15**: la lista fornita numera da 1 a 14 senza salti
  (l'ultima è la registrazione comunicazioni). Non c'è una quindicesima task da
  qualche parte: sono state fatte tutte quelle presenti.
- Gli **altri popup di errore mancanti** trovati controllando quello del codice
  fiscale (campi obbligatori, email, 500 su sinistri/incassi) sono stati
  **segnalati e non risolti**, come chiedeva la task: "controlla se mancano altri
  popup e segnalali". Dettaglio nella task del CF e nel debito tecnico.
- L'**ora in UTC** delle comunicazioni è segnalata nel debito tecnico e non
  corretta qui: riguarda tutti i timestamp dello schema, non questa funzione.

[X] In nuova pratica, contratto/sinistro/lead collegato devono apparire solo quelli del cliente selezionato (per lead appare semplicemente e basta, mentre gli altri devono essere selezionabili), rimuovere la parte "operatore"
[X] i tasti Nuovo Preventivo, nuovo contratto, nuovo sinistro, nuovo incasso devono aprirsi come pannello che sta sopra (gia ce l ha nuovo incasso), stessa cosa per i tasti modifica
[X] la sezione documenti deve essere piu gestibile: intanto i tasti devono essere fissi in basso a sinistra, e se il testo è lungo va accorciato con i puntini per evitare che esce fuori dal riquadratino, inoltre quando si carica si deve mostrare un anteprima
      Classe dedicata `.doc-item` (card in colonna, tasti sotto e allineati a
      sinistra, alla stessa altezza in ogni card): `.related-item` NON e' stata
      toccata perche' la condividono appuntamenti e comunicazioni in _macros.html.
      Nome file troncato con ellissi (serve `min-width:0` sul figlio flex) e nome
      intero nell'attributo `title`. Anteprima PRIMA del caricamento con
      FileReader: miniatura per le immagini, icona + nome + peso per PDF e altri
      tipi, e sparisce se si annulla la scelta. `previewDoc()`, che apre i
      documenti gia' caricati, resta com'era.
[X] in anagrafica, i filtri devono essere tutti selezionabili col dropdown, che elencano le opzioni disponibili in base ai dati che ci sono
      Citta', Provincia, Professione e Anno scadenza diventano `<select>`
      popolati con query DISTINCT lato database sui soli clienti non archiviati
      (una tendina non deve proporre valori che darebbero zero risultati); anche
      Stato civile ora viene dai dati invece che da una lista fissa scritta a mano.
      In `_build_filters()` il confronto passa da `ILIKE %valore%` a uguaglianza:
      con la tendina il valore e' esatto e scegliere "Roma" non deve piu' tirare
      dentro "Roma Nord". Un valore selezionato ma non piu' disponibile (URL a
      mano, o ultimo cliente archiviato) resta in lista, altrimenti il filtro
      sparirebbe dalla tendina restando attivo. Il campo "Nome / CF / email /
      cell." resta un input libero: li' si cerca per frammento.

[X] la targa viene visualizzata due volte del veicolo in Veicoli
      `Veicolo.descrizione` include già la targa fra parentesi, quindi
      stamparla accanto alla targa in evidenza la ripeteva. Ora accanto alla
      targa restano solo marca e modello.
[X] quando si crea una nuova pratica, non si ha la priorità massima di default
      Default **Urgente** sul form a pagina piena e sul pannello "Nuova pratica"
      della lista, solo in CREAZIONE: in modifica vince la priorità già
      salvata, altrimenti riaprire il form rialzerebbe da solo le pratiche
      declassate a mano. Nessun conflitto con la priorità automatica
      (`_priorita_automatica_pratiche`, before_flush): quella alza a urgente,
      il default parte già da urgente. Verificato che la regola automatica
      continua a scattare sulle pratiche create via codice (priorità None) e a
      rispettare una scelta manuale non neutra.
[X] manca popup errore di quando si inserisce un codice fiscale non valido (controllo se mancano altri popup di errore)
      **Causa:** il formato del CF era già validato da `@validates` su Cliente e
      l'unicità dall'indice unique, ma nessuna delle due eccezioni era
      intercettata nella vista: `ValueError` e `IntegrityError` uscivano dalla
      richiesta e l'utente vedeva una **pagina 500**, non un messaggio — quindi
      un CF sbagliato sembrava solo "non salvare". Ora tornano al form con un
      flash "error" e i valori digitati ancora dentro.
      ⚠️ **Altri popup di errore mancanti trovati durante il controllo** (NON
      risolti in questa sessione, sono task a sé):
      1. **Campi obbligatori aggirabili lato server.** `nome` e `cognome` sono
         `nullable=False` ma il controllo è solo l'attributo HTML `required`:
         una POST con i campi vuoti crea un cliente con stringhe vuote e nessun
         errore (verificato: HTTP 302 e cliente creato). Manca una validazione
         server.
      2. **Email mai validata.** Solo `type="email"` lato browser: `"non-una-email"`
         arriva al database e viene salvata così com'è (verificato). Non c'è
         nessun `@validates` sulla colonna.
      3. **Sinistri e incassi vanno in 500 su dati non numerici.** `int(f["contratto_id"])`
         e `float(f.get("importo"))` non sono in un try: un contratto vuoto o un
         importo non numerico danno pagina 500 senza messaggio (verificato). È
         esattamente la stessa classe di bug del CF, sugli altri form.
      ✅ Già a posto e lasciato com'è: la **targa non valida** mostra
      correttamente il toast rosso (`clienti.aggiungi_veicolo` ha già try/except).
[X] in comunicazioni mettere la x in basso a destra sui messaggi registrati con eventuale finestra di conferma, per evitare duplicati
      Rotta `POST /messaggi/comunicazioni/<id>/elimina` + x nel macro
      `comunicazioni_list`, con `confirm()` e `next` per tornare da dove si era
      (la stessa comunicazione si vede da scheda cliente e da dettaglio
      pratica). `next_url` è opzionale: la vista aggregata per codice fiscale
      non lo passa e resta di sola consultazione.
[X] i popup in generale devono durare come minimo 5 sec
      `toast()`: minimo 5000 ms (prima 3500 fissi). I messaggi lunghi restano di
      più (~60 ms per carattere) con tetto a 10s, così un errore prolisso non si
      pianta in mezzo allo schermo.
[X] **Form preventivo: chiarire "Compagnia scelta" vs "Compagnie consultate".**
      Logica server NON toccata (è corretta: la riga spuntata *è* la compagnia
      scelta). Quando una riga è spuntata "Scelta", i campi in alto passano in
      sola lettura, sono marcati come derivati (`.is-derivato`) e una nota dice
      da dove arriva il valore. Senza righe spuntate restano compilabili: è il
      caso della compagnia singola. Sono `disabled` e non `readonly` perché su
      `<select>` readonly non esiste; il campo così non viene inviato, ed è
      giusto — a valorizzarlo pensa il server dalla riga spuntata. Salvataggio
      verificato end-to-end.
[X] **Form preventivo/pratica: "Lead collegato" non si aggiorna al primo
      caricamento** → **era già risolto**, la voce era rimasta solo non spuntata.
      Il commit c8dd7f7 aveva già aggiunto sia l'init al `DOMContentLoaded` sia
      `initContenutoModale()`. Verificato in tutti e sei i casi (pratica e
      preventivo × pagina piena, pannello modale, con e senza cliente
      pre-selezionato): il lead mostrato è sempre quello del cliente selezionato.
      ⚠️ **Ma lo stesso bug era ancora aperto sull'altro caricatore**, ed è
      stato corretto qui: `caricaContrattiCliente` (sinistri e incassi) girava
      solo su `onchange` e dentro il pannello modale, mai al render di una
      pagina piena. Il menu "Contratto" restava vuoto finché non si ritoccava il
      cliente e in modifica **la polizza già collegata non compariva affatto**.
[X] mettere i tasti di nuovo sinistro, nuovo incasso in dettaglio contratto
      Aprono il pannello modale con cliente E contratto già pre-selezionati. Il
      contratto viaggia in `?contratto_id=` e finisce in `data-selected`, lo
      stesso meccanismo che la modifica usa già: il menu resta popolato da
      `caricaContrattiCliente()` e quindi continua a contenere solo le polizze
      di quel cliente.
[X] **Stato "persa" mancante per le tipologie senza emissione**
      Spostato in `STATI_PRATICA_BASE`. Verificata la coerenza delle strutture
      derivate: `STATI_PRATICA` resta senza duplicati, `ORDINE_STATI_PRATICA` e
      `SCALA_AVANZAMENTO` sono invariati ("persa" non è un passo della scala e
      non ci è mai stato), `FAMIGLIE_STATI_PRATICA` continua a coprire tutti gli
      stati una volta sola con "persa" in "chiuse", e l'ordine del menu per le
      tipologie con emissione non cambia.
      Risolve di riflesso anche un caso di **perdita di dato**: riaprire il form
      di una pratica persa senza emissione ne azzerava lo stato, perché
      `filtraStatiPratica()` nascondeva "persa" e ripiegava sul primo stato
      disponibile — bastava un salvataggio per perdere l'esito senza avviso.
[X] quando si mette la voce altro nella pratica, si deve aprire anche un pannello dove scrivere la motivazione
      Nuova colonna `pratiche.motivo_perdita_dettaglio` (Text, nullable),
      migrazione Alembic **7026369d95aa**. Colonna dedicata e non un riuso di
      `note`: quelle sono appunti di lavorazione, questa è il motivo della
      perdita e va letta accanto al motivo (property `motivo_perdita_label`, usata
      in bacheca e sul dettaglio pratica). Il campo compare solo scegliendo
      "altro", anche al primo render. Lato server il testo si conserva solo
      finché il motivo resta "altro": cambiando motivo descriverebbe una perdita
      diversa da quella registrata. Migrazione verificata in upgrade
      incrementale, downgrade + re-upgrade e catena completa da DB vuoto.
[X] non compare in ricontattare questo mese nella bacheca, se messo nel mese corrente
      **La causa NON era il criterio di intervallo**, che è corretto: `>= primo
      del mese` e `< primo del mese successivo` copre tutto il mese corrente,
      estremi inclusi. Verificato sui 36 mesi di tre anni (bisestili compresi,
      zero errori di confine) e sui dati reali con scadenza al primo, a oggi e
      all'ultimo giorno del mese — tutte compaiono, e il giorno precedente al
      mese resta correttamente fuori.
      La causa vera è la task dello stato "persa" qui sopra: per le tipologie
      senza catena di emissione "persa" non era selezionabile, quindi quelle
      pratiche **non potevano proprio entrare nella lista**. Corretto quello, una
      consulenza persa con scadenza nel mese corrente compare regolarmente. In
      `dashboard.py` è rimasto un commento che indica dove guardare, così nessuno
      "corregge" in futuro un intervallo che è già giusto.
[X] il tasto vedi tutti che sono in scadenze in arrivo, deve essere anche in incassi in ritardo, e in sinistri aperti
      Aggiunto su entrambe, puntato alle liste **già filtrate**
      (`/incassi/?stato=in_ritardo`, `/sinistri/?stato=aperti`). Per i sinistri
      il filtro non esisteva: la card conta i non chiusi (aperto **e** in
      perizia) mentre la lista sapeva filtrare solo per stato singolo, quindi il
      link avrebbe mostrato meno righe del numero appena letto; aggiunta la voce
      "aperti (non chiusi)", che è un raggruppamento e non uno stato del modello.
      Il link delle scadenze ora apre lo scadenziario a 30 giorni invece dei 60
      di default: era l'unico dei tre a portare a una lista più lunga del proprio
      conteggio. Verificato che i tre conteggi coincidono con le righe mostrate.
[X] quando si clicca per visualizzare il documento, non fa nulla
      **Causa:** `|tojson` produce una stringa JSON fra virgolette DOPPIE e Flask
      non le converte in entità HTML (`htmlsafe_dumps` sostituisce solo `< > & '`).
      Dentro `onclick="..."` la prima virgoletta del nome file **chiudeva
      l'attributo**: il browser leggeva `onclick="previewDoc(1, "` e il resto
      diventava attributi HTML spuri. In console: *"Unexpected end of input"*,
      e il tasto occhio non faceva niente. La rotta `/documenti/<id>/anteprima`
      era invece a posto (200 col contenuto giusto).
      **Fix:** attributo fra apici singoli — il caso opposto non si presenta,
      perché `|tojson` gli apici li scrive già come `'`. Verificato nel browser
      su PDF, file di testo e un nome con apostrofo; controllato che nessun altro
      template usi `|tojson` dentro un attributo a virgolette doppie.
[X] apparentemente quando si invia una comunicazione non la registra
      **Causa:** tracciando le richieste durante un invio, l'unica POST che parte
      dalla modale "Messaggio" è `/messaggi/destinatari`, che si limita a
      restituire numero ed email per costruire i link; poi `inviaMessaggi()` apre
      wa.me/mailto e finisce lì. **Nessuna rotta di quel blueprint scriveva una
      Comunicazione**: il record non si perdeva per strada, non veniva mai
      creato. Il modello Comunicazione è arrivato in Fase A2 e all'epoca fu
      collegato solo alla richiesta documenti sulla pratica; la modale Messaggio,
      più vecchia, non è mai stata agganciata.
      **Fix:** rotta `POST /messaggi/registra`, chiamata una volta per
      destinatario subito dopo l'apertura del link, con canale effettivamente
      usato (whatsapp/email), recapito, testo personalizzato e data/ora. Si
      registrano solo i destinatari davvero aperti: chi viene saltato per
      contatto mancante non deve risultare contattato. Se la registrazione
      fallisce lo si dice con un toast invece di tacere.
      L'esito resta "registrato" e non "consegnato": con un link cliccabile la
      consegna non è verificabile.
      ⚠️ `data_invio` usa `datetime.utcnow()` come tutti i timestamp del
      progetto, quindi **l'ora mostrata è UTC, non l'ora locale italiana**
      (in estate due ore indietro). Vale per tutte le comunicazioni, anche quelle
      già registrate dalla richiesta documenti: non è stato cambiato qui perché
      è una decisione sul fuso orario che riguarda l'intero schema, non questa
      funzione. Vedi debito tecnico in fondo.


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
- [X] ~~Bug aperto nella sezione Veicoli della scheda cliente (da specificare)~~
      Era la targa stampata due volte: chiuso.
- [ ] `avvia_crm.bat`: la logica batch non è mai stata eseguita su Windows reale
      (scritta e riletta, non testata dal vivo)
- [ ] **Timestamp in UTC mostrati come ora locale.** Tutti i `datetime` del
      progetto usano `datetime.utcnow()` (created_at, data_apertura,
      `Comunicazione.data_invio`, ...) ma vengono stampati tali e quali. Sulle
      comunicazioni si vede: l'ora dell'invio è due ore indietro rispetto
      all'orologio italiano d'estate. Va deciso una volta per tutte se salvare
      timezone-aware e convertire in visualizzazione: è una modifica di schema +
      template, non del singolo punto che stampa l'ora.
- [ ] **Validazioni senza messaggio d'errore** (dettagli nella task del codice
      fiscale qui sopra): campi obbligatori aggirabili con una POST diretta,
      email mai validata lato server, e `int()`/`float()` non protetti in
      sinistri e incassi che danno pagina 500 invece di un toast.

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