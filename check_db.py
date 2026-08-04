"""Controllo rapido dello schema di crm.db (Fase A2).

Uso:  python check_db.py
"""
import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crm.db")

if not os.path.exists(DB):
    raise SystemExit("crm.db non trovato: avvia prima l'app almeno una volta.")

con = sqlite3.connect(DB)
tabelle = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]

print("TABELLE:", ", ".join(tabelle), "\n")

if "alembic_version" not in tabelle:
    print("!! DB LEGACY: nessuna migrazione applicata.")
    print("   Cancella crm.db e riavvia l'app (dentro ci sono solo dati di esempio).\n")
else:
    rev = con.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    atteso = "4051e3e74071"
    print(f"REVISIONE ALEMBIC: {rev}", "(OK)" if rev == atteso else f"(atteso {atteso})", "\n")


def colonne(tabella):
    return [r[1] for r in con.execute(f"PRAGMA table_info({tabella})")]


print("--- Task Fase A2 ---")

controlli = [
    ("Modello Appuntamento",        "appuntamenti" in tabelle),
    ("Modello Comunicazione",       "comunicazioni" in tabelle),
    ("Impostazioni agenzia",        "impostazioni_agenzia" in tabelle),
    ("pratica_id su Documento",     "pratica_id" in colonne("documenti")),
    ("pratica_id su Preventivo",    "pratica_id" in colonne("preventivi")),
    ("preventivo_id rimosso da Pratica",
                                    "preventivo_id" not in colonne("pratiche")),
]

for nome, ok in controlli:
    print(f"  [{'OK' if ok else '--'}] {nome}")

print("\n--- Colonne delle nuove tabelle ---")
for t in ("appuntamenti", "comunicazioni", "impostazioni_agenzia"):
    if t in tabelle:
        print(f"  {t}: {', '.join(colonne(t))}")

print("\n--- Conteggi ---")
for t in ("clienti", "lead", "pratiche", "preventivi",
          "appuntamenti", "comunicazioni"):
    if t in tabelle:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {n}")

con.close()