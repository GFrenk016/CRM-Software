# Collaudo CRM — nei panni del subagente

> Regola d'oro: mentre fai questo giro **non sei uno sviluppatore**.
> Non aprire l'editor, non sistemare niente. Annota e basta.
> Se ti fermi a correggere, perdi il filo di come si sente lui.

## Il personaggio

**Salvatore Greco**, 47 anni, subagenzia a Rossano, plurimandatario.
Portafoglio di circa 400 clienti, quasi tutto auto e moto, qualche casa.
Lavora da solo, la moglie gli dà una mano con la carta.
Non è un tecnico: se una cosa non si capisce in tre secondi, la salta e
torna al quaderno.

Ogni volta che ti blocchi, la domanda è: **Salvatore cosa farebbe qui?**

---

## Setup

1. Fai una copia di `crm.db` prima di iniziare, così puoi rifare il giro.
2. Se vuoi partire pulito, cancella `crm.db` e riavvia: le migrazioni
   girano da sole e il seed rimette dati di esempio.
3. Tieni aperto un blocco note. Ti serve per la sezione "Registro" in
   fondo.

---

## Giro 1 — Il nuovo contatto (Legge Bersani)

Il figlio di un cliente storico ha appena preso la patente. Il padre
chiama: vuole intestare la macchina al ragazzo sfruttando la Bersani.

1. **Anagrafica → Nuovo cliente**. Crea il ragazzo. Nel form seleziona
   tipologia pratica *Legge Bersani*.
2. Vai in **Pipeline**. C'è la sua card nel primo stadio?
3. Dalla card, apri la **scheda cliente**. Aggiungi il **veicolo** con la targa.
4. Vai in **Pratiche**, apri la pratica appena nata.
   - La priorità è massima? (Bersani dovrebbe alzarla da sola)
   - Ci sono avvisi sui **campi anagrafici mancanti**?
   - Compila la **checklist documenti**: cosa gli serve davvero?
5. Usa **Richiesta documenti**: manda il messaggio al cliente.
   Torna indietro e controlla che la comunicazione sia registrata.
6. Fai avanzare la pratica con **prossimo step**, uno alla volta, fino a
   `certificato_inviato`.
   - Prova a passare a `in_coda_emissione` **fuori** dagli orari 9-11 / 15-17.
     Ti avvisa? Ti lascia passare comunque?

### Da segnare
- [ ] Quanti click dal "il padre chiama" al "pratica aperta e completa"?
- [ ] C'è un punto in cui non hai capito cosa fare dopo?
- [ ] Hai dovuto scrivere la stessa cosa due volte in schermate diverse?

---

## Giro 2 — Il preventivo con più compagnie

Una signora chiede un preventivo RC auto. Salvatore interroga tre compagnie.

1. **Preventivi → Nuovo**. Collega cliente e veicolo.
2. Aggiungi **tre righe compagnia** con premi e garanzie diverse.
   Il premio più basso viene evidenziato?
3. Le **garanzie** disponibili corrispondono a quelle che userebbe davvero?
   (Questo elenco è provvisorio — è un TODO cliente aperto)
4. **Converti** il preventivo in contratto.
5. Vai in **Contratti**: c'è? Ha una data di scadenza sensata?
6. Vai in **Incassi**: si è generato qualcosa o devi crearlo a mano?

### Da segnare
- [ ] Dopo la conversione, cosa resta da fare a mano che ti aspettavi automatico?
- [ ] Il contratto porta con sé la **targa**? (so già che no — verifica l'effetto)

---

## Giro 3 — Quello che non si chiude

Un cliente chiede il preventivo, poi sparisce.

1. Apri una pratica e portala a stato **persa**.
2. Metti `motivo_perdita` = *premio troppo alto* e la
   `data_scadenza_riferimento` a fra due mesi.
3. Vai in **Dashboard**: compare in "Da ricontattare"?
4. Prova a metterci una data del mese corrente e ricontrolla.

### Da segnare
- [ ] Se torni fra un mese, questo cliente ti risalta all'occhio o si perde?
- [ ] Il motivo di perdita ti serve a qualcosa dopo, o è solo archiviato?

---

## Giro 4 — La mattina tipo

Questo è il giro più importante. Salvatore apre il CRM alle 8:30 col caffè.

1. Guarda **solo la Dashboard** per due minuti. Senza cliccare altrove.
2. Ora rispondi: **cosa devo fare oggi?**
   Se non lo sai dire dalla sola bacheca, hai trovato il problema più grosso
   del prodotto.
3. Poi clicca in ordine: scadenze in arrivo, incassi in ritardo, sinistri aperti.
   Ognuno ti porta dove ti aspettavi?
4. Vai in **Scadenze**: le polizze dei prossimi 30 giorni ci sono tutte?
5. Vai in **Incassi**: segna un incasso come pagato dal dropdown.

### Da segnare
- [ ] La bacheca ti dà una lista di cose da fare, o solo dei numeri?
- [ ] Quante schermate servono per "chi devo chiamare oggi"?

---

## Giro 5 — Il sinistro

Un cliente tampona. Chiama in panico.

1. **Sinistri → Nuovo**, collega cliente e contratto.
2. Carica un **documento** (constatazione amichevole) dalla scheda cliente.
3. Dalla scheda cliente, riesci a vedere sinistro, contratto e documento
   senza uscire dalla pagina?
4. Manda una comunicazione al cliente per aggiornarlo.

### Da segnare
- [ ] Con un cliente al telefono, ci arrivi in tempo o lo fai aspettare?

---

## Giro 6 — La pulizia

1. In Anagrafica seleziona 2-3 clienti vecchi e usa **Archivia**.
2. Controlla che spariscano da Anagrafica **e** da Pipeline.
3. Apri **Archiviati**, ripristinane uno.
4. Torna in Pipeline: è tornato nello stadio in cui stava?

### Da segnare
- [ ] Il conteggio sul tasto Archiviati è utile o è rumore?
- [ ] Ti aspettavi che l'archiviato sparisse anche da Scadenze e Incassi?
      (Oggi NON sparisce — è la domanda aperta al cliente)

---

## Giro 7 — La ricerca (il momento cross-selling)

Salvatore ha un cliente davanti che vuole assicurare il motorino.

1. Vai in **Ricerca**, cerca per **codice fiscale**.
2. Vedi tutto quello che ha? Contratti, veicoli, pratiche, preventivi?
3. Ci sono **veicoli scoperti** segnalati?
4. Domanda vera: da qui riesci a dirgli *"guardi, anche la Panda di sua
   moglie scade a marzo"* senza aprire altre schermate?

---

## Registro del collaudo

Per ogni intoppo scrivi tre righe, non di più:

```
DOVE:      Pratiche → dettaglio → checklist
COSA:      ho aggiunto un documento e non capivo se era salvato
GRAVITÀ:   fastidio / rallentamento / blocco
```

Poi classifica ogni voce in una di queste tre:

| Tipo | Cosa significa | Cosa ne fai |
|---|---|---|
| **Bug** | fa una cosa sbagliata | lo sistemi tu |
| **Attrito** | funziona ma è scomodo | lo sistemi tu, dopo i bug |
| **Domanda** | non sai come lavora lui davvero | **la chiedi a lui** |

La terza colonna è quella che conta. Ogni voce che finisce lì è una riga
da aggiungere alle domande aperte in `bugfixes.md` — e una scusa
legittima per riaprire il discorso preventivo.

---

## Le tre prove killer

Se hai poco tempo, fai almeno queste.

**1. La prova del telefono.**
Cliente al telefono che chiede "quando mi scade la polizza?".
Cronometra. Sopra i 15 secondi, la ricerca non va bene.

**2. La prova del lunedì.**
Fai un giro oggi. Ripetilo fra tre giorni **senza rileggere questo file**.
Le cose che non ricordi come si fanno sono le cose che Salvatore non farà mai.

**3. La prova del quaderno.**
Alla fine chiediti onestamente: se fossi Salvatore, per quale operazione
tornerei al quaderno invece di aprire il CRM?
Quella è la prossima cosa da costruire — non la Fase D.