"""Popolamento del database con dati FITTIZI di esempio.

Nessun dato reale di clienti: nomi, contatti e numeri sono inventati e servono
solo a mostrare l'applicazione funzionante. Eseguito da db.py se il DB è vuoto,
oppure manualmente con:  python seed.py
"""
import random
from datetime import date, datetime, timedelta

from extensions import db
from models import (Cliente, Compagnia, Contratto, Incasso, Lead, Preventivo,
                    Sinistro)


def _d(days_from_today):
    return date.today() + timedelta(days=days_from_today)


def seed():
    """Crea un set coerente di dati di esempio. Presuppone tabelle già create."""
    if Cliente.query.first():
        return  # già popolato

    # --- Compagnie (mandati) ------------------------------------------------
    comp_nomi = ["Generali", "Allianz", "UnipolSai", "AXA", "Cattolica"]
    compagnie = [Compagnia(nome=n) for n in comp_nomi]
    db.session.add_all(compagnie)
    db.session.flush()

    # --- Clienti (fittizi) --------------------------------------------------
    clienti_seed = [
        dict(nome="Marco", cognome="Rossi", citta="Milano", provincia="MI",
             cap="20100", indirizzo="Via Dante 12", email="marco.rossi@example.com",
             cellulare="333 1112233", codice_fiscale="RSSMRC80A01F205X",
             data_nascita=date(1980, 1, 1), tipo_documento="Carta identità",
             numero_documento="AY1234567", professione="Ingegnere",
             stato_civile="coniugato", convivenza=True, num_figli=2),
        dict(nome="Giulia", cognome="Bianchi", citta="Torino", provincia="TO",
             cap="10100", indirizzo="Corso Francia 45", email="giulia.bianchi@example.com",
             cellulare="340 2223344", codice_fiscale="BNCGLI85M41L219Y",
             data_nascita=date(1985, 8, 1), tipo_documento="Patente",
             numero_documento="TO9988776", professione="Insegnante",
             stato_civile="nubile", convivenza=False, num_figli=0),
        dict(nome="Luca", cognome="Verdi", citta="Bologna", provincia="BO",
             cap="40100", indirizzo="Via Emilia 200", email="luca.verdi@example.com",
             cellulare="329 3334455", codice_fiscale="VRDLCU75R15A944Z",
             data_nascita=date(1975, 10, 15), tipo_documento="Carta identità",
             numero_documento="CA5566778", professione="Commerciante",
             stato_civile="coniugato", convivenza=True, num_figli=3),
        dict(nome="Sara", cognome="Ferrari", citta="Roma", provincia="RM",
             cap="00100", indirizzo="Via Nazionale 88", email="sara.ferrari@example.com",
             cellulare="347 4445566", codice_fiscale="FRRSRA90T50H501W",
             data_nascita=date(1990, 12, 10), tipo_documento="Carta identità",
             numero_documento="AX1122334", professione="Avvocato",
             stato_civile="convivente", convivenza=True, num_figli=1),
        dict(nome="Antonio", cognome="Russo", citta="Napoli", provincia="NA",
             cap="80100", indirizzo="Via Toledo 15", email="antonio.russo@example.com",
             cellulare="331 5556677", codice_fiscale="RSSNTN68B19F839K",
             data_nascita=date(1968, 2, 19), tipo_documento="Patente",
             numero_documento="NA2233445", professione="Artigiano",
             stato_civile="coniugato", convivenza=True, num_figli=2),
        dict(nome="Elena", cognome="Costa", citta="Firenze", provincia="FI",
             cap="50100", indirizzo="Viale Europa 7", email="elena.costa@example.com",
             cellulare="338 6667788", codice_fiscale="CSTLNE82S52D612P",
             data_nascita=date(1982, 11, 12), tipo_documento="Carta identità",
             numero_documento="AY7788990", professione="Medico",
             stato_civile="nubile", convivenza=False, num_figli=0),
        dict(nome="Davide", cognome="Greco", citta="Genova", provincia="GE",
             cap="16100", indirizzo="Via XX Settembre 30",
             email="davide.greco@example.com", cellulare="345 7778899",
             codice_fiscale="GRCDVD78E23D969Q", data_nascita=date(1978, 5, 23),
             tipo_documento="Carta identità", numero_documento="CA3344556",
             professione="Impiegato", stato_civile="coniugato",
             convivenza=True, num_figli=1),
        dict(nome="Chiara", cognome="Marino", citta="Bari", provincia="BA",
             cap="70100", indirizzo="Corso Cavour 102",
             email="chiara.marino@example.com", cellulare="333 8889900",
             codice_fiscale="MRNCHR93P44A662R", data_nascita=date(1993, 9, 4),
             professione="Grafica", stato_civile="nubile",
             convivenza=False, num_figli=0),
    ]
    clienti = [Cliente(**c) for c in clienti_seed]
    db.session.add_all(clienti)
    db.session.flush()

    fonti = ["referral", "sito", "social", "chiamata", "evento", "altro"]
    stadi = ["nuovo", "contattato", "qualificato", "proposta", "vinto", "perso"]
    azioni = ["Richiamare per preventivo", "Inviare documentazione",
              "Fissare appuntamento", "Sollecito rinnovo", "Verificare esigenze"]

    # --- Lead (uno per cliente, stadi vari) ---------------------------------
    for i, cl in enumerate(clienti):
        db.session.add(Lead(
            cliente_id=cl.id,
            stadio=stadi[i % len(stadi)],
            fonte=fonti[i % len(fonti)],
            valore_stimato=random.choice([800, 1200, 1800, 2500, 3500, 5000, 7500]),
            prossima_azione=random.choice(azioni),
            data_prossima_azione=_d(random.randint(1, 20)),
            stadio_updated_at=datetime.utcnow() - timedelta(days=random.randint(0, 25)),
        ))

    # --- Preventivi ---------------------------------------------------------
    oggetti = ["RC Auto", "Polizza Casa", "Vita + Infortuni", "RC Professionale",
               "Polizza Moto"]
    stati_prev = ["bozza", "inviato", "accettato", "rifiutato", "accettato"]
    preventivi = []
    for i, cl in enumerate(clienti[:5]):
        p = Preventivo(
            numero=f"PRV-{i+1:04d}",
            cliente_id=cl.id,
            lead_id=cl.lead[0].id if cl.lead else None,
            compagnia_id=compagnie[i % len(compagnie)].id,
            oggetto=oggetti[i % len(oggetti)],
            premio_proposto=random.choice([420, 650, 900, 1200, 1500]),
            stato=stati_prev[i % len(stati_prev)],
            data_invio=_d(-random.randint(5, 40)),
        )
        preventivi.append(p)
    db.session.add_all(preventivi)
    db.session.flush()

    # --- Contratti attivi (alcuni originati da preventivi accettati) --------
    rami = ["Auto", "Casa", "Vita", "RC Professionale", "Infortuni"]
    contratti = []
    for i, cl in enumerate(clienti):
        prev = next((p for p in preventivi
                     if p.cliente_id == cl.id and p.stato == "accettato"), None)
        c = Contratto(
            cliente_id=cl.id,
            preventivo_id=prev.id if prev else None,
            compagnia_id=compagnie[i % len(compagnie)].id,
            numero_polizza=f"POL{random.randint(100000, 999999)}",
            ramo=rami[i % len(rami)],
            premio=random.choice([420, 580, 650, 900, 1200]),
            data_emissione=_d(-random.randint(200, 360)),
            data_scadenza=_d(random.choice([-10, 8, 20, 45, 120, 200])),
            stato="attivo",
        )
        contratti.append(c)
    db.session.add_all(contratti)
    db.session.flush()

    # --- Sinistri -----------------------------------------------------------
    tipi_sin = ["Auto - Tamponamento", "Casa - Perdita acqua",
                "Infortuni - Frattura", "Auto - Furto"]
    stati_sin = ["aperto", "perizia", "chiuso"]
    for i, c in enumerate(contratti[:4]):
        db.session.add(Sinistro(
            numero=f"SIN-{i+1:04d}",
            cliente_id=c.cliente_id,
            contratto_id=c.id,
            tipo=tipi_sin[i % len(tipi_sin)],
            data_apertura=_d(-random.randint(10, 90)),
            stato=stati_sin[i % len(stati_sin)],
            importo_stimato=random.choice([850, 1500, 3200, 500]),
        ))

    # --- Incassi / Provvigioni ---------------------------------------------
    for i, c in enumerate(contratti):
        # una provvigione già prevista per ogni contratto
        incassato = i % 3 == 0
        in_ritardo = i % 3 == 1
        db.session.add(Incasso(
            cliente_id=c.cliente_id,
            contratto_id=c.id,
            descrizione=f"Provvigione {c.ramo}",
            importo=round((c.premio or 0) * 0.15, 2),
            data_prevista=_d(-5) if in_ritardo else _d(random.randint(3, 30)),
            data_incasso=_d(-2) if incassato else None,
            stato="incassato" if incassato else ("in_ritardo" if in_ritardo
                                                 else "da_incassare"),
        ))

    db.session.commit()


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        seed()
        print("Seed completato.")
