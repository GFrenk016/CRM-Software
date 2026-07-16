"""Estensioni Flask condivise (istanziate qui per evitare import circolari)."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
