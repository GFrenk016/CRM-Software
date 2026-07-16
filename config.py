"""Configurazione applicazione CRM.

Tutto locale: nessun servizio esterno. Il database è un singolo file SQLite
e gli allegati vengono salvati sul filesystem nella cartella uploads/.
"""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Chiave usata da Flask per i messaggi flash / sessione locale.
    SECRET_KEY = os.environ.get("CRM_SECRET_KEY", "crm-locale-mono-utente")

    # Database: un unico file .db relazionale nella cartella del progetto.
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "crm.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cartella dove persistono i documenti allegati (carta d'identità, moduli...).
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB per file

    # Estensioni ammesse per gli allegati.
    ALLOWED_UPLOAD_EXTENSIONS = {
        "pdf", "png", "jpg", "jpeg", "gif", "webp",
        "doc", "docx", "xls", "xlsx", "txt", "csv",
    }
