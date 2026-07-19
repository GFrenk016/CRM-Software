"""Modello dati relazionale del CRM.

Tutte le entità sono collegate da chiavi esterne coerenti (relazioni vere,
non testo libero). Dato un cliente si possono recuperare in un colpo solo
lead, preventivi, contratti, sinistri, incassi e documenti collegati
(scheda cliente a 360°) tramite le relationship definite qui sotto.

Ciclo di vita:  Lead → Preventivo → Contratto attivo → Scadenza/Rinnovo → Sinistro
Le SCADENZE non sono una tabella a sé: sono DERIVATE dai contratti attivi in
scadenza (vedi Contratto.giorni_alla_scadenza / query in blueprints/scadenze.py).
"""
from datetime import date, datetime

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
    codice_fiscale = db.Column(db.String(20))
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

    @property
    def nome_completo(self):
        return f"{self.cognome} {self.nome}".strip()

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

    oggetto = db.Column(db.String(200))         # es. "RC Auto", "Vita + Infortuni"
    premio_proposto = db.Column(db.Float, default=0.0)
    stato = db.Column(db.String(20), default="bozza")
    data_invio = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="preventivi")
    lead = db.relationship("Lead", back_populates="preventivi")
    compagnia = db.relationship("Compagnia", back_populates="preventivi")
    # Contratto generato da questo preventivo accettato (se esiste)
    contratto = db.relationship("Contratto", back_populates="preventivo",
                                uselist=False)

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

    tipo = db.Column(db.String(60))             # "Carta identità", "Modulo firmato", ...
    filename = db.Column(db.String(255))        # nome originale mostrato all'utente
    stored_name = db.Column(db.String(255))     # nome fisico su disco (uploads/)
    mime = db.Column(db.String(100))
    size = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    cliente = db.relationship("Cliente", back_populates="documenti")

    @property
    def is_immagine(self):
        return bool(self.mime and self.mime.startswith("image/"))

    @property
    def is_pdf(self):
        return self.mime == "application/pdf"

    def __repr__(self):
        return f"<Documento {self.filename}>"
