"""fase A2 fix: inverti pratica-preventivo, comunicazioni sopravvivono a delete cliente

Revision ID: 47fd4032f359
Revises: 361e808ad3be
Create Date: 2026-07-31 15:59:02.423907

Copre due dei tre fix della correzione Fase A2 che toccano lo SCHEMA:

  Fix 1 - Inversione Pratica <-> Preventivo
    Prima: pratiche.preventivo_id (una pratica -> un preventivo).
    Dopo:  preventivi.pratica_id  (una pratica -> molti preventivi), così da
           avere lo storico preventivi sulla pratica e permettere revisioni /
           riquotazioni. FK nullable, nessun cascade.

  Fix 2 - Le comunicazioni sopravvivono alla cancellazione del cliente
    comunicazioni.cliente_id diventa NULLABLE con FK ondelete=SET NULL: se il
    cliente viene cancellato la comunicazione resta a registro con cliente_id
    azzerato (destinatario/testo/data intatti).

Il Fix 3 (Appuntamento.esito default "da_svolgere") NON è qui: è un default
lato Python (client-side), non modifica lo schema del database.

TRAPPOLA SQLite: con batch_alter_table, create_foreign_key(None, ...) fallisce
con "Constraint must have a name". Tutti i constraint qui hanno un nome
esplicito, sia in upgrade sia in downgrade. Per poter eliminare le FK
originariamente ANONIME (comunicazioni.cliente_id) si passa una
naming_convention al batch, così la FK riflessa assume un nome deterministico
e può essere droppata per nome.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47fd4032f359'
down_revision = '361e808ad3be'
branch_labels = None
depends_on = None


# Stessa convenzione usata per i nomi già presenti nello schema
# (es. fk_pratiche_preventivo_id_preventivi). Serve a dare un nome alle FK
# riflesse ma anonime durante il rebuild batch di SQLite.
NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def upgrade():
    # --- Fix 1: sposta il collegamento da pratiche a preventivi -------------
    # Rimuove pratiche.preventivo_id (verso: pratica -> UN preventivo).
    with op.batch_alter_table('pratiche', schema=None) as batch_op:
        batch_op.drop_constraint('fk_pratiche_preventivo_id_preventivi',
                                 type_='foreignkey')
        batch_op.drop_column('preventivo_id')

    # Aggiunge preventivi.pratica_id (verso: pratica -> MOLTI preventivi).
    # FK nullable, nessun cascade: eliminando la pratica i preventivi restano.
    with op.batch_alter_table('preventivi', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pratica_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_preventivi_pratica_id_pratiche',
                                    'pratiche', ['pratica_id'], ['id'])

    # --- Fix 2: comunicazioni.cliente_id nullable + ondelete SET NULL -------
    # La naming_convention nomina la FK anonima riflessa così da poterla droppare
    # e ricrearla con ondelete='SET NULL'.
    with op.batch_alter_table('comunicazioni', schema=None,
                              naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.alter_column('cliente_id', existing_type=sa.INTEGER(),
                              nullable=True)
        batch_op.drop_constraint('fk_comunicazioni_cliente_id_clienti',
                                 type_='foreignkey')
        batch_op.create_foreign_key('fk_comunicazioni_cliente_id_clienti',
                                    'clienti', ['cliente_id'], ['id'],
                                    ondelete='SET NULL')


def downgrade():
    # --- Fix 2 (inverso): ripristina comunicazioni.cliente_id NOT NULL ------
    # ATTENZIONE (documentato): il modello ripristinato impone cliente_id NOT
    # NULL. Le eventuali comunicazioni ORFANE (cliente_id NULL, prodotte dalla
    # cancellazione di un cliente mentre era attivo il SET NULL) non sono
    # rappresentabili in quel modello. Invece di far fallire il rebuild NOT NULL
    # in modo oscuro, qui le eliminiamo ESPLICITAMENTE segnalando quante e
    # perché. È perdita di dati consapevole: è l'unico modo di tornare allo
    # schema precedente, che quelle righe non ammette.
    conn = op.get_bind()
    orfane = conn.execute(
        sa.text("SELECT COUNT(*) FROM comunicazioni WHERE cliente_id IS NULL")
    ).scalar()
    if orfane:
        print(
            f"[downgrade 47fd4032f359] ATTENZIONE: elimino {orfane} comunicazioni "
            "orfane (cliente_id NULL). Il downgrade ripristina cliente_id NOT NULL "
            "e tali righe non sono rappresentabili nello schema precedente."
        )
        conn.execute(sa.text("DELETE FROM comunicazioni WHERE cliente_id IS NULL"))

    with op.batch_alter_table('comunicazioni', schema=None,
                              naming_convention=NAMING_CONVENTION) as batch_op:
        batch_op.drop_constraint('fk_comunicazioni_cliente_id_clienti',
                                 type_='foreignkey')
        # Ricreata CON NOME (in origine era anonima): funzionalmente identica,
        # ma un nome esplicito è obbligatorio col batch SQLite.
        batch_op.create_foreign_key('fk_comunicazioni_cliente_id_clienti',
                                    'clienti', ['cliente_id'], ['id'])
        batch_op.alter_column('cliente_id', existing_type=sa.INTEGER(),
                              nullable=False)

    # --- Fix 1 (inverso): rimetti pratiche.preventivo_id, togli pratica_id ---
    with op.batch_alter_table('preventivi', schema=None) as batch_op:
        batch_op.drop_constraint('fk_preventivi_pratica_id_pratiche',
                                 type_='foreignkey')
        batch_op.drop_column('pratica_id')

    with op.batch_alter_table('pratiche', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preventivo_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_pratiche_preventivo_id_preventivi',
                                    'preventivi', ['preventivo_id'], ['id'])
