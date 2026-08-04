"""Modello dati relazionale del CRM.

Tutte le entità sono collegate da chiavi esterne coerenti (relazioni vere,
non testo libero). Dato un cliente si possono recuperare in un colpo solo
lead, preventivi, contratti, sinistri, incassi e documenti collegati
(scheda cliente a 360°) tramite le relationship definite qui sotto.

Ciclo di vita:  Lead → Preventivo → Contratto attivo → Scadenza/Rinnovo → Sinistro
Le SCADENZE non sono una tabella a sé: sono DERIVATE dai contratti attivi in
scadenza (vedi Contratto.giorni_alla_scadenza / query in blueprints/scadenze.py).
"""
import enum
import re
from datetime import date, datetime, time

from sqlalchemy import event
from sqlalchemy.orm import validates

from extensions import db


# --------------------------------------------------------------------------- #
#  Costanti di dominio (stati / enumerazioni)                                  #
# --------------------------------------------------------------------------- #
STADI_LEAD = ["nuovo", "contattato", "qualificato", "proposta", "vinto", "perso"]
FONTI_LEAD = ["referral", "sito", "social", "chiamata", "evento", "altro"]
STATI_PREVENTIVO = ["bozza", "inviato", "accettato", "rifiutato"]
STATI_CONTRATTO = ["in attesa", "attivo", "scaduto", "disdetto"]
STATI_SINISTRO = ["aperto", "perizia", "chiuso"]
STATI_INCASSO = ["da_incassare", "incassato", "in_ritardo"]

# Stato della Pratica: stessa impostazione delle altre entità (colonna String +
# lista di valori ammessi), così i template/filtri restano coerenti col resto.
# Stati "generici", validi per QUALSIASI tipologia di pratica.
STATI_PRATICA_BASE = ["aperta", "in_lavorazione", "in_attesa_cliente",
                      "completata", "annullata"]

# Stati della catena di emissione polizza (Fase B). Hanno senso solo per le
# tipologie che arrivano davvero all'emissione (vedi STATI_PER_TIPOLOGIA): per
# sinistro/consulenza/nuovo_preventivo non vanno mostrati. Valori senza spazi
# (finiscono come classi CSS badge-{{ x }}).
STATI_PRATICA_EMISSIONE = ["documentazione_da_integrare", "attesa_pagamento",
                           "pagamento_verificato", "attesa_otp",
                           "in_coda_emissione", "emessa", "certificato_inviato",
                           "persa"]

# Unione: tutti i valori ammessi a livello di validazione della colonna. La
# validazione resta permissiva (accetta ogni stato valido); a filtrare quali
# stati mostrare per una data tipologia ci pensa STATI_PER_TIPOLOGIA nella UI.
STATI_PRATICA = STATI_PRATICA_BASE + STATI_PRATICA_EMISSIONE

# Posizione di ciascuno stato nella scala di avanzamento (0 = inizio). Serve a
# mostrare a che punto è la pratica e a proporre lo stato successivo (flusso
# guidato). Solo la catena LINEARE di emissione ha un "dopo" univoco: gli stati
# di servizio (in_lavorazione, in_attesa_cliente) e gli esiti finali non
# compaiono qui perché non hanno una posizione unica nella scala.
ORDINE_STATI_PRATICA = {
    "aperta": 0,
    "documentazione_da_integrare": 1,
    "attesa_pagamento": 2,
    "pagamento_verificato": 3,
    "attesa_otp": 4,
    "in_coda_emissione": 5,
    "emessa": 6,
    "certificato_inviato": 7,
}

# Motivi per cui una pratica si chiude senza emissione (stato "persa"). Default
# ragionevole, da confermare/estendere col cliente.
# TODO CLIENTE: validare l'elenco dei motivi di perdita.
MOTIVI_PERDITA = ["premio_troppo_alto", "rimasto_con_attuale", "non_risponde",
                  "veicolo_non_acquistato", "documentazione_mancante", "altro"]

# Appuntamento: tipo ed esito modellati come le altre entità (String + lista).
# Il tipo "otp" copre l'appuntamento per la firma/verifica OTP previsto dal
# flusso di lavorazione pratica. Valori senza spazi (finiscono come classi CSS).
TIPI_APPUNTAMENTO = ["otp", "consulenza", "firma", "sopralluogo", "altro"]
ESITI_APPUNTAMENTO = ["da_svolgere", "svolto", "annullato", "non_presentato"]

# Comunicazione: canale di uscita ed esito registrato.
# NB sull'esito: con i link wa.me/mailto non è possibile sapere se il messaggio
# è stato davvero consegnato. "registrato" indica solo che la comunicazione è
# stata tracciata a sistema (link generato), NON che sia stata recapitata.
CANALI_COMUNICAZIONE = ["whatsapp", "email", "altro"]
ESITI_COMUNICAZIONE = ["registrato", "inviato", "consegnato", "fallito"]

# Regex di dominio -----------------------------------------------------------
# Codice fiscale persona fisica (16 caratteri, formato standard italiano).
RE_CODICE_FISCALE = re.compile(r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$")
# Targa italiana formato corrente: 2 lettere, 3 cifre, 2 lettere (es. AB123CD).
RE_TARGA = re.compile(r"^[A-Z]{2}\d{3}[A-Z]{2}$")


# --------------------------------------------------------------------------- #
#  Enumerazioni della Pratica (Python Enum con label leggibile per la UI)      #
# --------------------------------------------------------------------------- #
# A differenza degli stati "storici" (semplici liste), qui serve una LABEL in
# italiano distinta dal valore salvato: per questo si usa un Enum vero. In DB
# però si persiste comunque una String (il .value), coerente con lo stile del
# resto dei modelli e senza tipi ENUM nativi lato Postgres (più facili da
# migrare in futuro).
class PrioritaPratica(enum.Enum):
    BASSA = "bassa"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"

    @property
    def label(self):
        return self.value.capitalize()

    @classmethod
    def valori(cls):
        return [m.value for m in cls]


class TipologiaPratica(enum.Enum):
    NUOVO_PREVENTIVO = "nuovo_preventivo"
    BERSANI = "bersani"
    NUOVO_ACQUISTO = "nuovo_acquisto"
    RINNOVO = "rinnovo"
    PAGAMENTO_POLIZZA_RATA = "pagamento_polizza_rata"
    SOSTITUZIONE_VEICOLO = "sostituzione_veicolo"
    SOSPENSIONE = "sospensione"
    RIATTIVAZIONE = "riattivazione"
    CONSULENZA = "consulenza"
    SINISTRO = "sinistro"

    @property
    def label(self):
        return _LABEL_TIPOLOGIA[self]

    @classmethod
    def valori(cls):
        return [m.value for m in cls]


_LABEL_TIPOLOGIA = {
    TipologiaPratica.NUOVO_PREVENTIVO: "Nuovo Preventivo",
    TipologiaPratica.BERSANI: "Legge Bersani",
    TipologiaPratica.NUOVO_ACQUISTO: "Nuovo Acquisto",
    TipologiaPratica.RINNOVO: "Rinnovo",
    TipologiaPratica.PAGAMENTO_POLIZZA_RATA: "Pagamento Polizza/Rata",
    TipologiaPratica.SOSTITUZIONE_VEICOLO: "Sostituzione Veicolo",
    TipologiaPratica.SOSPENSIONE: "Sospensione",
    TipologiaPratica.RIATTIVAZIONE: "Riattivazione",
    TipologiaPratica.CONSULENZA: "Consulenza",
    TipologiaPratica.SINISTRO: "Sinistro",
}


# Il flusso a 8 step di emissione vale SOLO per queste tipologie. Le altre non
# devono vedere gli stati di emissione nei select (restano sugli stati generici).
# TODO CLIENTE: sospensione e riattivazione qui NON hanno emissione (scelta
# conservativa); confermare se debbano invece seguire la catena.
TIPOLOGIE_CON_EMISSIONE = {
    TipologiaPratica.BERSANI.value,
    TipologiaPratica.RINNOVO.value,
    TipologiaPratica.NUOVO_ACQUISTO.value,
    TipologiaPratica.SOSTITUZIONE_VEICOLO.value,
    TipologiaPratica.PAGAMENTO_POLIZZA_RATA.value,
}


def _stati_ammessi_tipologia(tipologia):
    """Stati selezionabili per una tipologia, in ordine di lavorazione.

    Per le tipologie con emissione: prima la scala lineare (aperta → catena di
    emissione), poi gli stati/esiti fuori catena. Per le altre: solo i generici.
    """
    if tipologia in TIPOLOGIE_CON_EMISSIONE:
        scala = sorted(ORDINE_STATI_PRATICA, key=ORDINE_STATI_PRATICA.get)
        fuori_scala = [s for s in STATI_PRATICA if s not in scala]
        return scala + fuori_scala
    return list(STATI_PRATICA_BASE)


# Mappa tipologia → stati mostrabili nei select. Costruita una volta sola.
STATI_PER_TIPOLOGIA = {t: _stati_ammessi_tipologia(t)
                       for t in TipologiaPratica.valori()}


# --------------------------------------------------------------------------- #
#  Compagnie (i mandati del plurimandatario)                                   #
# --------------------------------------------------------------------------- #
class Compagnia(db.Model):
    __tablename__ = "compagnie"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    note = db.Column(db.Text)

    # Relazioni inverse
    preventivi = db.relationship("Preventivo", back_populates="compagnia")
    contratti = db.relationship("Contratto", back_populates="compagnia")

    def __repr__(self):
        return f"<Compagnia {self.nome}>"


# --------------------------------------------------------------------------- #
#  Cliente (anagrafica)                                                        #
# --------------------------------------------------------------------------- #
class Cliente(db.Model):
    __tablename__ = "clienti"
    id = db.Column(db.Integer, primary_key=True)

    # Anagrafica di base
    nome = db.Column(db.String(80), nullable=False)
    cognome = db.Column(db.String(80), nullable=False)
    indirizzo = db.Column(db.String(200))
    citta = db.Column(db.String(80))
    cap = db.Column(db.String(10))
    provincia = db.Column(db.String(4))

    # Contatti
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(40))
    cellulare = db.Column(db.String(40))

    # Documento d'identità
    # 16 caratteri, univoco (indice unique): più CF NULL restano ammessi sia su
    # SQLite sia su Postgres. Il formato è validato da @validates più sotto.
    codice_fiscale = db.Column(db.String(16), unique=True, index=True)
    data_nascita = db.Column(db.Date)
    tipo_documento = db.Column(db.String(40))
    numero_documento = db.Column(db.String(40))

    # Profilo
    professione = db.Column(db.String(80))
    stato_civile = db.Column(db.String(40))       # celibe/nubile, coniugato, ...
    convivenza = db.Column(db.Boolean, default=False)
    num_figli = db.Column(db.Integer, default=0)

    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Relazioni: la scheda 360° del cliente -----------------------------
    lead = db.relationship("Lead", back_populates="cliente",
                           cascade="all, delete-orphan")
    preventivi = db.relationship("Preventivo", back_populates="cliente",
                                 cascade="all, delete-orphan")
    contratti = db.relationship("Contratto", back_populates="cliente",
                                cascade="all, delete-orphan")
    sinistri = db.relationship("Sinistro", back_populates="cliente",
                               cascade="all, delete-orphan")
    incassi = db.relationship("Incasso", back_populates="cliente",
                              cascade="all, delete-orphan")
    documenti = db.relationship("Documento", back_populates="cliente",
                                cascade="all, delete-orphan")
    veicoli = db.relationship("Veicolo", back_populates="cliente",
                              cascade="all, delete-orphan")
    pratiche = db.relationship("Pratica", back_populates="cliente",
                               cascade="all, delete-orphan")
    appuntamenti = db.relationship("Appuntamento", back_populates="cliente",
                                   cascade="all, delete-orphan")
    # Le comunicazioni NON seguono il cliente nella cancellazione: sono la
    # traccia (audit) di cosa è stato mandato e quando, utile in caso di
    # contestazione, quindi devono sopravvivere all'eliminazione dell'anagrafica.
    # Cascade di default ("save-update, merge"): eliminando il cliente,
    # SQLAlchemy AZZERA cliente_id sulle comunicazioni (SET NULL a livello ORM)
    # invece di cancellarle. Niente passive_deletes: su SQLite le FK non sono
    # applicate (nessun PRAGMA foreign_keys=ON), quindi l'azzeramento in memoria
    # dell'ORM è ciò che garantisce cliente_id = NULL su questo DB; l'ondelete
    # "SET NULL" sulla FK copre invece i DB che applicano i vincoli (Postgres).
    comunicazioni = db.relationship("Comunicazione", back_populates="cliente")

    @validates("codice_fiscale")
    def _valida_codice_fiscale(self, key, value):
        """Normalizza (upper/trim) e valida il formato del CF, se valorizzato."""
        if not value:
            return None
        value = value.strip().upper()
        if not RE_CODICE_FISCALE.match(value):
            raise ValueError(f"Codice fiscale non valido: {value!r}")
        return value

    @property
    def nome_completo(self):
        return f"{self.cognome} {self.nome}".strip()

    @property
    def indirizzo_completo(self):
        """Indirizzo aggregato DERIVATO dai campi già presenti (via/cap/città/prov).

        Scelta: una property, non una colonna. I dati vivono già separati in
        indirizzo/cap/citta/provincia; duplicarli in un campo aggregato
        introdurrebbe solo rischio di disallineamento. Qui si compone a runtime,
        mantenendo un'unica fonte di verità.
        """
        via = (self.indirizzo or "").strip()
        localita = " ".join(p for p in [(self.cap or "").strip(),
                                        (self.citta or "").strip()] if p)
        prov = (self.provincia or "").strip()
        if prov:
            localita = f"{localita} ({prov})".strip()
        return ", ".join(p for p in [via, localita.strip()] if p)

    @property
    def iniziali(self):
        c = (self.cognome[:1] if self.cognome else "")
        n = (self.nome[:1] if self.nome else "")
        return (c + n).upper() or "?"

    @property
    def ha_figli(self):
        return bool(self.num_figli and self.num_figli > 0)

    @property
    def scadenze(self):
        """Scadenze = contratti attivi con una data di scadenza (derivate)."""
        return [c for c in self.contratti if c.data_scadenza]

    def __repr__(self):
        return f"<Cliente {self.nome_completo}>"


# --------------------------------------------------------------------------- #
#  Lead (pipeline commerciale)                                                 #
# --------------------------------------------------------------------------- #
class Lead(db.Model):
    __tablename__ = "lead"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)

    stadio = db.Column(db.String(20), default="nuovo", nullable=False)
    fonte = db.Column(db.String(20), default="altro")
    valore_stimato = db.Column(db.Float, default=0.0)
    prossima_azione = db.Column(db.String(200))
    data_prossima_azione = db.Column(db.Date)
    stadio_updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="lead")
    preventivi = db.relationship("Preventivo", back_populates="lead")
    # FK nullable lato Pratica: se il lead viene eliminato le pratiche
    # collegate NON vengono cancellate, il riferimento viene solo azzerato.
    pratiche = db.relationship("Pratica", back_populates="lead")

    @property
    def giorni_nello_stadio(self):
        base = self.stadio_updated_at or self.created_at or datetime.utcnow()
        return (datetime.utcnow() - base).days

    @property
    def punteggio(self):
        """Punteggio lead DETERMINISTICO (0-100), su criteri reali e dichiarati.

        - Completezza anagrafica (max 40): quanti campi chiave sono compilati.
        - Valore stimato       (max 30): scala fino a 10.000 €.
        - Avanzamento stadio   (max 30): più avanti nella pipeline, più alto.
        Nessun numero casuale: a parità di dati il punteggio è sempre lo stesso.
        """
        c = self.cliente
        campi = [c.email, c.cellulare or c.telefono, c.codice_fiscale,
                 c.indirizzo, c.data_nascita, c.professione]
        compilati = sum(1 for v in campi if v)
        p_dati = round((compilati / len(campi)) * 40)

        p_valore = round(min((self.valore_stimato or 0) / 10000, 1) * 30)

        peso_stadio = {"nuovo": 0, "contattato": 0.3, "qualificato": 0.6,
                       "proposta": 0.85, "vinto": 1.0, "perso": 0.0}
        p_stadio = round(peso_stadio.get(self.stadio, 0) * 30)

        return max(0, min(100, p_dati + p_valore + p_stadio))

    def __repr__(self):
        return f"<Lead {self.id} {self.stadio}>"


# --------------------------------------------------------------------------- #
#  Preventivo                                                                  #
# --------------------------------------------------------------------------- #
class Preventivo(db.Model):
    __tablename__ = "preventivi"
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(30), unique=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey("lead.id"))            # opzionale
    compagnia_id = db.Column(db.Integer, db.ForeignKey("compagnie.id"))
    # Pratica di origine (FK nullable, nessun cascade): una pratica di tipo
    # "nuovo preventivo" può generare PIÙ preventivi (revisioni/riquotazioni),
    # quindi il collegamento sta qui, lato Preventivo. Se la pratica viene
    # eliminata il preventivo NON sparisce, il riferimento resta solo azzerato.
    pratica_id = db.Column(db.Integer, db.ForeignKey("pratiche.id"))     # nullable
    # Veicolo di riferimento per preventivi RC Auto (opzionale: non tutti i
    # preventivi riguardano un veicolo, es. Vita/Infortuni/Casa).
    veicolo_id = db.Column(db.Integer, db.ForeignKey("veicoli.id"))
    # Pratica di origine (FK nullable, nessun cascade): una singola pratica di
    # lavorazione (es. "nuovo preventivo") può generare PIÙ preventivi nel tempo
    # (revisioni, riquotazioni dopo richieste del cliente). Vedi Pratica.preventivi.
    pratica_id = db.Column(db.Integer, db.ForeignKey("pratiche.id"))      # nullable

    oggetto = db.Column(db.String(200))         # es. "RC Auto", "Vita + Infortuni"
    premio_proposto = db.Column(db.Float, default=0.0)
    stato = db.Column(db.String(20), default="bozza")
    data_invio = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="preventivi")
    lead = db.relationship("Lead", back_populates="preventivi")
    compagnia = db.relationship("Compagnia", back_populates="preventivi")
    veicolo = db.relationship("Veicolo")
    # Contratto generato da questo preventivo accettato (se esiste)
    contratto = db.relationship("Contratto", back_populates="preventivo",
                                uselist=False)
    # Pratica di origine (molti preventivi → una pratica). Relazione inversa
    # di Pratica.preventivi (lista).
    pratica = db.relationship("Pratica", back_populates="preventivi")

    def __repr__(self):
        return f"<Preventivo {self.numero} {self.stato}>"


# --------------------------------------------------------------------------- #
#  Contratto attivo (polizza emessa)                                          #
# --------------------------------------------------------------------------- #
class Contratto(db.Model):
    __tablename__ = "contratti"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    preventivo_id = db.Column(db.Integer, db.ForeignKey("preventivi.id"))  # origine
    compagnia_id = db.Column(db.Integer, db.ForeignKey("compagnie.id"))

    numero_polizza = db.Column(db.String(40), nullable=False)
    ramo = db.Column(db.String(80))             # Auto, Casa, Vita, RC, ...
    premio = db.Column(db.Float, default=0.0)
    data_emissione = db.Column(db.Date)
    data_scadenza = db.Column(db.Date)
    stato = db.Column(db.String(20), default="attivo")
    note = db.Column(db.Text)

    cliente = db.relationship("Cliente", back_populates="contratti")
    preventivo = db.relationship("Preventivo", back_populates="contratto")
    compagnia = db.relationship("Compagnia", back_populates="contratti")
    sinistri = db.relationship("Sinistro", back_populates="contratto",
                               cascade="all, delete-orphan")
    incassi = db.relationship("Incasso", back_populates="contratto",
                              cascade="all, delete-orphan")
    # FK nullable lato Pratica: se il contratto viene eliminato le pratiche
    # collegate NON vengono cancellate, il riferimento viene solo azzerato.
    pratiche = db.relationship("Pratica", back_populates="contratto")

    @property
    def giorni_alla_scadenza(self):
        if not self.data_scadenza:
            return None
        return (self.data_scadenza - date.today()).days

    @property
    def stato_scadenza(self):
        """Etichetta derivata per lo scadenziario."""
        g = self.giorni_alla_scadenza
        if g is None:
            return "n/d"
        if g < 0:
            return "scaduta"
        if g <= 15:
            return "imminente"
        if g <= 30:
            return "in_scadenza"
        return "attiva"

    def __repr__(self):
        return f"<Contratto {self.numero_polizza}>"


# --------------------------------------------------------------------------- #
#  Sinistro                                                                    #
# --------------------------------------------------------------------------- #
class Sinistro(db.Model):
    __tablename__ = "sinistri"
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(30), unique=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    contratto_id = db.Column(db.Integer, db.ForeignKey("contratti.id"), nullable=False)

    tipo = db.Column(db.String(120))            # es. "Auto - Tamponamento"
    data_apertura = db.Column(db.Date)
    stato = db.Column(db.String(20), default="aperto")
    importo_stimato = db.Column(db.Float, default=0.0)
    note = db.Column(db.Text)

    cliente = db.relationship("Cliente", back_populates="sinistri")
    contratto = db.relationship("Contratto", back_populates="sinistri")
    pratiche = db.relationship("Pratica", back_populates="sinistro")

    def __repr__(self):
        return f"<Sinistro {self.numero} {self.stato}>"


# --------------------------------------------------------------------------- #
#  Incasso / Provvigione                                                       #
# --------------------------------------------------------------------------- #
class Incasso(db.Model):
    __tablename__ = "incassi"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    contratto_id = db.Column(db.Integer, db.ForeignKey("contratti.id"), nullable=False)

    descrizione = db.Column(db.String(200))
    importo = db.Column(db.Float, default=0.0)
    data_prevista = db.Column(db.Date)
    data_incasso = db.Column(db.Date)           # null finché non incassato
    stato = db.Column(db.String(20), default="da_incassare")

    cliente = db.relationship("Cliente", back_populates="incassi")
    contratto = db.relationship("Contratto", back_populates="incassi")

    def stato_effettivo(self):
        """Ricalcola lo stato considerando i ritardi rispetto a oggi."""
        if self.data_incasso:
            return "incassato"
        if self.data_prevista and self.data_prevista < date.today():
            return "in_ritardo"
        return "da_incassare"

    def __repr__(self):
        return f"<Incasso {self.id} {self.stato}>"


# --------------------------------------------------------------------------- #
#  Documento (allegato su filesystem, path salvato in DB)                     #
# --------------------------------------------------------------------------- #
class Documento(db.Model):
    __tablename__ = "documenti"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)
    # Collegamento opzionale a una pratica specifica (FK nullable, nessun
    # cascade): serve per allegare documenti alla pratica e, in fase successiva,
    # per l'invio del certificato a chiusura pratica.
    pratica_id = db.Column(db.Integer, db.ForeignKey("pratiche.id"))     # nullable

    tipo = db.Column(db.String(60))             # "Carta identità", "Modulo firmato", ...
    filename = db.Column(db.String(255))        # nome originale mostrato all'utente
    stored_name = db.Column(db.String(255))     # nome fisico su disco (uploads/)
    mime = db.Column(db.String(100))
    size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="documenti")
    pratica = db.relationship("Pratica", back_populates="documenti")

    @property
    def is_immagine(self):
        return bool(self.mime and self.mime.startswith("image/"))

    @property
    def is_pdf(self):
        return self.mime == "application/pdf"

    def __repr__(self):
        return f"<Documento {self.filename}>"


# --------------------------------------------------------------------------- #
#  Veicolo (un cliente può averne più d'uno → relazione 1:N)                   #
# --------------------------------------------------------------------------- #
class Veicolo(db.Model):
    __tablename__ = "veicoli"
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"), nullable=False)

    targa = db.Column(db.String(10), nullable=False, unique=True, index=True)
    marca = db.Column(db.String(60))
    modello = db.Column(db.String(60))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="veicoli")

    @validates("targa")
    def _valida_targa(self, key, value):
        """Normalizza e valida la targa (formato italiano corrente AA000AA)."""
        if not value:
            raise ValueError("La targa è obbligatoria.")
        value = value.replace(" ", "").strip().upper()
        if not RE_TARGA.match(value):
            raise ValueError(f"Targa non valida: {value!r}")
        return value

    @property
    def descrizione(self):
        parti = [p for p in [self.marca, self.modello] if p]
        base = " ".join(parti)
        return f"{base} ({self.targa})".strip() if base else self.targa

    def __repr__(self):
        return f"<Veicolo {self.targa}>"


# --------------------------------------------------------------------------- #
#  Pratica (unità di lavoro operativa collegata a cliente/contratto/sinistro) #
# --------------------------------------------------------------------------- #
class Pratica(db.Model):
    __tablename__ = "pratiche"
    id = db.Column(db.Integer, primary_key=True)

    # Numero identificativo univoco, generato automaticamente (PR-{anno}-{prog}).
    # L'assegnazione avviene nell'evento before_insert più sotto se non fornito.
    numero_identificativo = db.Column(db.String(20), unique=True, index=True)

    # Relazioni ------------------------------------------------------------
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"),
                           nullable=False)                      # obbligatoria
    lead_id = db.Column(db.Integer, db.ForeignKey("lead.id"))            # nullable
    contratto_id = db.Column(db.Integer, db.ForeignKey("contratti.id"))  # nullable
    sinistro_id = db.Column(db.Integer, db.ForeignKey("sinistri.id"))    # nullable
    # Veicolo di riferimento (FK nullable, nessun cascade): oggi il veicolo sta
    # solo su Preventivo, ma qui serve la targa nella lista "da ricontattare".
    veicolo_id = db.Column(db.Integer, db.ForeignKey("veicoli.id"))      # nullable

    # Attributi operativi --------------------------------------------------
    stato = db.Column(db.String(30), default="aperta", nullable=False)
    priorita = db.Column(db.String(20),
                         default=PrioritaPratica.MEDIA.value, nullable=False)
    tipologia = db.Column(db.String(40), nullable=False)
    operatore = db.Column(db.String(120))       # campo libero: app mono-utente
    note = db.Column(db.Text)

    # Date di passaggio di stato (nullable): lo stato è UNA colonna sola e da
    # solo non conserva lo storico, quindi i momenti chiave si fissano qui quando
    # si avanza (vedi flusso guidato).
    data_pagamento_verificato = db.Column(db.Date)
    data_emissione = db.Column(db.Date)
    data_invio_certificato = db.Column(db.Date)

    # Esito negativo (stato "persa"):
    #  - motivo_perdita: validato contro MOTIVI_PERDITA.
    #  - data_scadenza_riferimento: scadenza della polizza ATTUALE del cliente,
    #    inserita a mano perché può stare presso un'altra compagnia e quindi NON
    #    è derivabile dai contratti in CRM. Serve alla lista "da ricontattare".
    motivo_perdita = db.Column(db.String(40))
    data_scadenza_riferimento = db.Column(db.Date)

    # Timestamp ------------------------------------------------------------
    data_apertura = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultimo_aggiornamento = db.Column(db.DateTime, default=datetime.utcnow,
                                          onupdate=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="pratiche")
    lead = db.relationship("Lead", back_populates="pratiche")
    contratto = db.relationship("Contratto", back_populates="pratiche")
    sinistro = db.relationship("Sinistro", back_populates="pratiche")
    # Veicolo di riferimento (sola lettura lato Pratica, come Preventivo.veicolo).
    veicolo = db.relationship("Veicolo")
    # Checklist dei documenti attesi: figlia della pratica (cascade), sparisce
    # con essa. Distinta dai Documento (file caricati), vedi ChecklistDocumento.
    checklist_documenti = db.relationship("ChecklistDocumento",
                                          back_populates="pratica",
                                          cascade="all, delete-orphan")
    # Storico preventivi generati da questa pratica (una pratica → molti
    # preventivi). Relazione inversa di Preventivo.pratica; nessun cascade:
    # eliminando la pratica i preventivi restano, con pratica_id azzerato.
    preventivi = db.relationship("Preventivo", back_populates="pratica")
    # Collegamenti opzionali (FK nullable lato figlio, nessun cascade): i
    # documenti e gli appuntamenti possono esistere anche senza pratica.
    documenti = db.relationship("Documento", back_populates="pratica")
    appuntamenti = db.relationship("Appuntamento", back_populates="pratica")
    comunicazioni = db.relationship("Comunicazione", back_populates="pratica")

    @validates("stato")
    def _valida_stato(self, key, value):
        if value not in STATI_PRATICA:
            raise ValueError(f"Stato pratica non valido: {value!r}")
        return value

    @validates("priorita")
    def _valida_priorita(self, key, value):
        if value not in PrioritaPratica.valori():
            raise ValueError(f"Priorità non valida: {value!r}")
        return value

    @validates("tipologia")
    def _valida_tipologia(self, key, value):
        if value not in TipologiaPratica.valori():
            raise ValueError(f"Tipologia pratica non valida: {value!r}")
        return value

    @validates("motivo_perdita")
    def _valida_motivo_perdita(self, key, value):
        # Opzionale: valorizzato solo quando la pratica è "persa".
        if value and value not in MOTIVI_PERDITA:
            raise ValueError(f"Motivo perdita non valido: {value!r}")
        return value or None

    @property
    def tipologia_label(self):
        """Label leggibile in italiano per la UI (es. 'Legge Bersani')."""
        return TipologiaPratica(self.tipologia).label if self.tipologia else ""

    @property
    def priorita_label(self):
        return PrioritaPratica(self.priorita).label if self.priorita else ""

    def __repr__(self):
        return f"<Pratica {self.numero_identificativo} {self.stato}>"


def _ultimo_progressivo_anno(connection, anno):
    """Ultimo progressivo già presente sul DB per l'anno dato (0 se nessuno)."""
    prefisso = f"PR-{anno}-"
    ultimo = connection.execute(
        db.text(
            "SELECT numero_identificativo FROM pratiche "
            "WHERE numero_identificativo LIKE :p "
            "ORDER BY numero_identificativo DESC LIMIT 1"
        ),
        {"p": prefisso + "%"},
    ).scalar()
    return int(ultimo.rsplit("-", 1)[1]) if ultimo else 0


@event.listens_for(db.session.__class__, "before_flush")
def _assegna_numeri_pratiche(session, flush_context, instances):
    """Assegna il numero identificativo (PR-{anno}-{progressivo}) alle pratiche nuove.

    Fatto a livello di before_flush (non before_insert) perché SQLAlchemy
    accorpa gli INSERT: numerando qui, in memoria, più pratiche create nello
    stesso flush ottengono progressivi consecutivi senza collisioni. Il
    progressivo è per-anno, azzerato a ogni anno solare, zero-padded a 4 cifre.
    """
    nuove = [o for o in session.new
             if isinstance(o, Pratica) and not o.numero_identificativo]
    if not nuove:
        return

    connection = session.connection()
    prossimo = {}   # anno -> prossimo progressivo da assegnare
    for pratica in nuove:
        base = pratica.data_apertura or datetime.utcnow()
        anno = base.year
        if anno not in prossimo:
            prossimo[anno] = _ultimo_progressivo_anno(connection, anno) + 1
        pratica.numero_identificativo = f"PR-{anno}-{prossimo[anno]:04d}"
        prossimo[anno] += 1


# --------------------------------------------------------------------------- #
#  ChecklistDocumento (cosa DEVE arrivare per lavorare la pratica)             #
# --------------------------------------------------------------------------- #
class ChecklistDocumento(db.Model):
    """Traccia i documenti ATTESI su una pratica (cosa deve arrivare).

    Distinto da Documento, che rappresenta il file effettivamente caricato (cosa
    È arrivato): qui si elenca cosa manca ancora. Serve a comporre la richiesta
    documenti al cliente e a capire a colpo d'occhio cosa resta da ricevere.
    """
    __tablename__ = "checklist_documenti"
    id = db.Column(db.Integer, primary_key=True)
    # Figlia della pratica: senza pratica non ha senso, quindi FK obbligatoria e
    # cascade lato Pratica (eliminando la pratica la checklist sparisce).
    pratica_id = db.Column(db.Integer, db.ForeignKey("pratiche.id"),
                           nullable=False)

    tipo = db.Column(db.String(80), nullable=False)   # es. "Carta identità"
    ricevuto = db.Column(db.Boolean, default=False, nullable=False)
    note = db.Column(db.Text)

    pratica = db.relationship("Pratica", back_populates="checklist_documenti")

    def __repr__(self):
        stato = "ricevuto" if self.ricevuto else "atteso"
        return f"<ChecklistDocumento {self.tipo} {stato}>"


# --------------------------------------------------------------------------- #
#  Appuntamento (agenda: es. appuntamento OTP nel flusso di lavorazione)       #
# --------------------------------------------------------------------------- #
class Appuntamento(db.Model):
    __tablename__ = "appuntamenti"
    id = db.Column(db.Integer, primary_key=True)

    # Il cliente è obbligatorio (figlio del Cliente, cascade lato Cliente).
    cliente_id = db.Column(db.Integer, db.ForeignKey("clienti.id"),
                           nullable=False)
    # La pratica è opzionale: un appuntamento può non essere ancora legato a una
    # pratica specifica (FK nullable, nessun cascade).
    pratica_id = db.Column(db.Integer, db.ForeignKey("pratiche.id"))     # nullable

    data_ora = db.Column(db.DateTime)
    tipo = db.Column(db.String(30))             # es. "otp", "consulenza", ...
    note = db.Column(db.Text)
    # Default "da_svolgere" (valore presente in ESITI_APPUNTAMENTO): così un
    # appuntamento nasce già "da fare" e in futuro si potranno filtrare quelli
    # ancora aperti senza gestire il caso NULL. Default lato Python (ORM), come
    # gli altri campi di stato del progetto: nessun server_default a livello DB.
    esito = db.Column(db.String(30), default="da_svolgere")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="appuntamenti")
    pratica = db.relationship("Pratica", back_populates="appuntamenti")

    @validates("tipo")
    def _valida_tipo(self, key, value):
        if value and value not in TIPI_APPUNTAMENTO:
            raise ValueError(f"Tipo appuntamento non valido: {value!r}")
        return value or None

    @validates("esito")
    def _valida_esito(self, key, value):
        if value and value not in ESITI_APPUNTAMENTO:
            raise ValueError(f"Esito appuntamento non valido: {value!r}")
        return value or None

    def __repr__(self):
        return f"<Appuntamento {self.id} {self.tipo}>"


# --------------------------------------------------------------------------- #
#  Comunicazione (storico messaggi inviati: WhatsApp / Email / altro)          #
# --------------------------------------------------------------------------- #
class Comunicazione(db.Model):
    __tablename__ = "comunicazioni"
    id = db.Column(db.Integer, primary_key=True)

    # Cliente NULLABLE con ondelete="SET NULL": la comunicazione è un record di
    # audit che deve restare leggibile anche dopo la cancellazione del cliente
    # (destinatario/testo/data restano intatti, cliente_id diventa NULL).
    cliente_id = db.Column(db.Integer,
                           db.ForeignKey("clienti.id", ondelete="SET NULL"),
                           nullable=True)
    # Pratica opzionale (FK nullable, nessun cascade).
    pratica_id = db.Column(db.Integer, db.ForeignKey("pratiche.id"))     # nullable

    canale = db.Column(db.String(20), nullable=False)   # whatsapp/email/altro
    destinatario = db.Column(db.String(200))            # numero o indirizzo email
    testo = db.Column(db.Text)
    data_invio = db.Column(db.DateTime, default=datetime.utcnow)
    # Esito: vedi nota su ESITI_COMUNICAZIONE. Con i link wa.me/mailto NON è
    # possibile sapere se il messaggio è stato recapitato: il default onesto è
    # "registrato" (link generato/tracciato), non "consegnato".
    esito = db.Column(db.String(20), default="registrato")

    cliente = db.relationship("Cliente", back_populates="comunicazioni")
    pratica = db.relationship("Pratica", back_populates="comunicazioni")

    @validates("canale")
    def _valida_canale(self, key, value):
        if value not in CANALI_COMUNICAZIONE:
            raise ValueError(f"Canale comunicazione non valido: {value!r}")
        return value

    @validates("esito")
    def _valida_esito(self, key, value):
        if value and value not in ESITI_COMUNICAZIONE:
            raise ValueError(f"Esito comunicazione non valido: {value!r}")
        return value or None

    def __repr__(self):
        return f"<Comunicazione {self.id} {self.canale}>"


def registra_comunicazione(cliente_id, canale, destinatario=None, testo=None,
                           pratica_id=None, esito="registrato", data_invio=None,
                           commit=True):
    """Registra una comunicazione nello storico e la restituisce.

    Helper unico da usare quando si genera un link wa.me/mailto (o si invia un
    messaggio) così da tenere traccia di CHI è stato contattato, QUANDO, su QUALE
    canale e con QUALE testo. NB: con i soli link cliccabili non è possibile
    confermare la consegna, quindi l'esito di default è "registrato" (link
    generato), NON "consegnato". Per registrare un invio effettivo servirebbe un
    callback dal frontend (vedi report / TODO in blueprints/messaggi.py).

    Passare commit=False per accodare la registrazione a una transazione più
    ampia gestita dal chiamante.
    """
    com = Comunicazione(
        cliente_id=cliente_id,
        pratica_id=pratica_id,
        canale=canale,
        destinatario=destinatario,
        testo=testo,
        esito=esito,
        data_invio=data_invio or datetime.utcnow(),
    )
    db.session.add(com)
    if commit:
        db.session.commit()
    return com


# --------------------------------------------------------------------------- #
#  Impostazioni agenzia (tabella a riga singola: id fisso = 1)                 #
# --------------------------------------------------------------------------- #
# Scelta: una tabella a riga singola invece di costanti in config.py, così in
# futuro i valori (IBAN, ragione sociale, finestre di emissione) saranno
# editabili da UI senza toccare il codice/redeploy. L'accesso passa sempre da
# get_impostazioni(), che garantisce l'esistenza dell'unica riga.
# NB: gli orari delle due finestre di emissione polizze sono DEFAULT provvisori,
# da confermare col cliente.
FINESTRA1_INIZIO_DEFAULT = time(9, 0)
FINESTRA1_FINE_DEFAULT = time(11, 0)
FINESTRA2_INIZIO_DEFAULT = time(15, 0)
FINESTRA2_FINE_DEFAULT = time(17, 0)


class ImpostazioniAgenzia(db.Model):
    __tablename__ = "impostazioni_agenzia"
    id = db.Column(db.Integer, primary_key=True)

    ragione_sociale = db.Column(db.String(200))
    iban = db.Column(db.String(34))             # IBAN italiano: 27 caratteri

    # Le due finestre giornaliere di emissione polizze (orari provvisori).
    finestra1_inizio = db.Column(db.Time, default=FINESTRA1_INIZIO_DEFAULT)
    finestra1_fine = db.Column(db.Time, default=FINESTRA1_FINE_DEFAULT)
    finestra2_inizio = db.Column(db.Time, default=FINESTRA2_INIZIO_DEFAULT)
    finestra2_fine = db.Column(db.Time, default=FINESTRA2_FINE_DEFAULT)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ImpostazioniAgenzia {self.ragione_sociale or 'n/d'}>"


def get_impostazioni():
    """Restituisce l'unica riga di impostazioni, creandola con i default se assente.

    Idempotente: la riga ha sempre id=1. Da usare come unico punto di accesso
    alle impostazioni agenzia.
    """
    imp = db.session.get(ImpostazioniAgenzia, 1)
    if imp is None:
        imp = ImpostazioniAgenzia(
            id=1,
            finestra1_inizio=FINESTRA1_INIZIO_DEFAULT,
            finestra1_fine=FINESTRA1_FINE_DEFAULT,
            finestra2_inizio=FINESTRA2_INIZIO_DEFAULT,
            finestra2_fine=FINESTRA2_FINE_DEFAULT,
        )
        db.session.add(imp)
        db.session.commit()
    return imp
