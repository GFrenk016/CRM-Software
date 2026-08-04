"""fix A2: preventivi.pratica_id (inverte pratica-preventivo), comunicazioni sopravvivono alla cancellazione cliente

Revision ID: 4051e3e74071
Revises: 361e808ad3be
Create Date: 2026-07-31 17:25:49.869834

Copre tre correzioni della Fase A2 (fatta su DB ancora vuoto di dati reali):

Fix 1 — Inverte il collegamento Pratica <-> Preventivo.
    Prima: pratiche.preventivo_id (una pratica -> un solo preventivo).
    Dopo:  preventivi.pratica_id  (una pratica -> molti preventivi), così una
    pratica "nuovo preventivo" può produrre revisioni/riquotazioni e la Pratica
    espone lo storico dei preventivi (Pratica.preventivi).

Fix 2 — Le comunicazioni sopravvivono alla cancellazione del cliente.
    comunicazioni.cliente_id diventa NULLABLE con FK ondelete="SET NULL": il
    registro (audit di cosa è stato mandato e quando) resta leggibile anche
    dopo l'eliminazione dell'anagrafica, con cliente_id = NULL.

Fix 3 — Appuntamento.esito default "da_svolgere".
    NON compare qui: è un default lato ORM (Python), come gli altri campi di
    stato del progetto, e non produce alcun cambiamento di schema/DDL.

Note SQLite/batch:
  * Tutti i constraint hanno un NOME esplicito, in upgrade e in downgrade: su
    SQLite `create_foreign_key(None, ...)` fallisce con "Constraint must have a
    name" (come già gestito nella migrazione 361e808ad3be).
  * La FK preesistente comunicazioni.cliente_id -> clienti era stata creata
    SENZA nome (in 361e808ad3be). Per poterla rimuovere in batch si passa una
    naming_convention: SQLAlchemy assegna alla FK riflessa il nome
    "fk_comunicazioni_cliente_id_clienti", che qui usiamo in drop_constraint.
    La stessa convenzione dà un nome anche alla FK (pure senza nome) di
    comunicazioni.pratica_id, che viene così ricreata e SOPRAVVIVE al rebuild.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4051e3e74071'
down_revision = '361e808ad3be'
branch_labels = None
depends_on = None


# Convenzione di naming applicata alle tabelle riflesse in batch, così le FK
# preesistenti create senza nome (SQLite) ottengono un nome deterministico e
# possono essere manipolate/ricreate.
NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade():
    # --- Fix 2: comunicazioni.cliente_id NULLABLE + ondelete SET NULL --------
    # naming_convention necessaria per rimuovere la FK preesistente (senza nome).
    with op.batch_alter_table('comunicazioni', schema=None,
                              naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('cliente_id',
                              existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.drop_constraint('fk_comunicazioni_cliente_id_clienti',
                                 type_='foreignkey')
        batch_op.create_foreign_key('fk_comunicazioni_cliente_id_clienti',
                                    'clienti', ['cliente_id'], ['id'],
                                    ondelete='SET NULL')

    # --- Fix 1: rimuove pratiche.preventivo_id (+ relativa FK) ---------------
    with op.batch_alter_table('pratiche', schema=None) as batch_op:
        batch_op.drop_constraint('fk_pratiche_preventivo_id_preventivi',
                                 type_='foreignkey')
        batch_op.drop_column('preventivo_id')

    # --- Fix 1: aggiunge preventivi.pratica_id (+ FK verso pratiche) ---------
    with op.batch_alter_table('preventivi', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pratica_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_preventivi_pratica_id_pratiche',
                                    'pratiche', ['pratica_id'], ['id'])


def downgrade():
    # --- Fix 1 (inverso): rimuove preventivi.pratica_id ----------------------
    with op.batch_alter_table('preventivi', schema=None) as batch_op:
        batch_op.drop_constraint('fk_preventivi_pratica_id_pratiche',
                                 type_='foreignkey')
        batch_op.drop_column('pratica_id')

    # --- Fix 1 (inverso): ripristina pratiche.preventivo_id (+ FK) -----------
    with op.batch_alter_table('pratiche', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preventivo_id', sa.INTEGER(),
                                      nullable=True))
        batch_op.create_foreign_key('fk_pratiche_preventivo_id_preventivi',
                                    'preventivi', ['preventivo_id'], ['id'])

    # --- Fix 2 (inverso): comunicazioni.cliente_id torna NOT NULL ------------
    # ATTENZIONE: dopo il Fix 2 possono esistere comunicazioni "orfane" con
    # cliente_id = NULL (clienti cancellati). Rimettere la colonna NOT NULL
    # con righe NULL presenti fallirebbe con un IntegrityError poco chiaro a
    # metà rebuild. Lo gestiamo ESPLICITAMENTE: se ci sono righe orfane il
    # downgrade si ferma con un messaggio che spiega cosa fare, INVECE di
    # cancellarle in silenzio (distruggendo proprio l'audit che il Fix 2
    # protegge) o di rompersi in modo opaco.
    conn = op.get_bind()
    orfane = conn.execute(sa.text(
        "SELECT COUNT(*) FROM comunicazioni WHERE cliente_id IS NULL"
    )).scalar()
    if orfane:
        raise RuntimeError(
            f"Downgrade bloccato: {orfane} comunicazioni hanno cliente_id = NULL "
            "(clienti cancellati). Rimettere cliente_id NOT NULL le perderebbe. "
            "Prima del downgrade riassegnale a un cliente esistente, oppure "
            "cancellale/archiviale manualmente se accettabile, poi riprova."
        )

    with op.batch_alter_table('comunicazioni', schema=None,
                              naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('fk_comunicazioni_cliente_id_clienti',
                                 type_='foreignkey')
        batch_op.create_foreign_key('fk_comunicazioni_cliente_id_clienti',
                                    'clienti', ['cliente_id'], ['id'])
        batch_op.alter_column('cliente_id',
                              existing_type=sa.INTEGER(),
                              nullable=False)
