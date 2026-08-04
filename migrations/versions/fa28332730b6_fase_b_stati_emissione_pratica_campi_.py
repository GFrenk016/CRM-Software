"""Fase B: stati emissione pratica, campi data/esito, veicolo_id, checklist documenti

Revision ID: fa28332730b6
Revises: 47fd4032f359
Create Date: 2026-08-04 07:19:45.440879

Unica migrazione della Fase B. Copre le sole modifiche di SCHEMA (i nuovi stati
della pratica sono valori di una colonna String già esistente, quindi non
toccano il DB):

  * pratiche.veicolo_id  -> FK nullable verso veicoli (serve la targa nella lista
    "da ricontattare"; nessun cascade).
  * pratiche: date di passaggio di stato (data_pagamento_verificato,
    data_emissione, data_invio_certificato) e campi esito negativo
    (motivo_perdita, data_scadenza_riferimento). Tutte nullable.
  * nuova tabella checklist_documenti (cosa DEVE arrivare per la pratica),
    distinta da documenti (cosa È arrivato).

TRAPPOLA SQLite (come nelle migrazioni A2): con batch_alter_table,
create_foreign_key(None, ...) fallisce con "Constraint must have a name". La FK
di veicolo_id ha quindi un NOME esplicito (convenzione del progetto
fk_<tabella>_<colonna>_<tabella_riferita>), sia in upgrade sia in downgrade.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa28332730b6'
down_revision = '47fd4032f359'
branch_labels = None
depends_on = None


# Nome esplicito per la FK veicolo_id (obbligatorio col batch SQLite).
FK_PRATICHE_VEICOLO = 'fk_pratiche_veicolo_id_veicoli'


def upgrade():
    op.create_table(
        'checklist_documenti',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pratica_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(length=80), nullable=False),
        sa.Column('ricevuto', sa.Boolean(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['pratica_id'], ['pratiche.id'],
                                name='fk_checklist_documenti_pratica_id_pratiche'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('pratiche', schema=None) as batch_op:
        batch_op.add_column(sa.Column('veicolo_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('data_pagamento_verificato', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('data_emissione', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('data_invio_certificato', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('motivo_perdita', sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column('data_scadenza_riferimento', sa.Date(), nullable=True))
        batch_op.create_foreign_key(FK_PRATICHE_VEICOLO, 'veicoli',
                                    ['veicolo_id'], ['id'])


def downgrade():
    with op.batch_alter_table('pratiche', schema=None) as batch_op:
        batch_op.drop_constraint(FK_PRATICHE_VEICOLO, type_='foreignkey')
        batch_op.drop_column('data_scadenza_riferimento')
        batch_op.drop_column('motivo_perdita')
        batch_op.drop_column('data_invio_certificato')
        batch_op.drop_column('data_emissione')
        batch_op.drop_column('data_pagamento_verificato')
        batch_op.drop_column('veicolo_id')

    op.drop_table('checklist_documenti')
