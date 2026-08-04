"""Fase C: compagnie consultate sul preventivo (confronto premi) e note preventivo

Revision ID: 522d460a5485
Revises: fa28332730b6
Create Date: 2026-08-04 14:33:20.167454

Unica migrazione della Fase C. Copre le sole modifiche di SCHEMA:

  * nuova tabella preventivo_compagnie: una riga per ogni compagnia interpellata
    su un preventivo, col premio quotato, le garanzie incluse e le note. Il
    subagente è plurimandatario e confronta più compagnie; Preventivo.compagnia_id
    resta e assume il significato di "compagnia scelta".
    Vincolo di unicità (preventivo_id, compagnia_id): la stessa compagnia non va
    consultata due volte sullo stesso preventivo.
  * preventivi.note -> campo libero sul preventivo (nullable).

Le GARANZIE non toccano il DB: sono valori di una colonna String separati da
virgola (vedi la costante GARANZIE in models.py), così ampliare l'elenco NON
richiederà una nuova migrazione.

TRAPPOLA SQLite (come nelle migrazioni A2 e Fase B): i vincoli anonimi non
sopravvivono al batch mode. Anche qui, quindi, FK e UNIQUE hanno un NOME
esplicito (convenzione del progetto fk_<tabella>_<colonna>_<tabella_riferita>).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '522d460a5485'
down_revision = 'fa28332730b6'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'preventivo_compagnie',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('preventivo_id', sa.Integer(), nullable=False),
        sa.Column('compagnia_id', sa.Integer(), nullable=False),
        sa.Column('premio', sa.Float(), nullable=True),
        sa.Column('garanzie', sa.String(length=400), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['compagnia_id'], ['compagnie.id'],
                                name='fk_preventivo_compagnie_compagnia_id_compagnie'),
        sa.ForeignKeyConstraint(['preventivo_id'], ['preventivi.id'],
                                name='fk_preventivo_compagnie_preventivo_id_preventivi'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('preventivo_id', 'compagnia_id',
                            name='uq_preventivo_compagnia'),
    )
    with op.batch_alter_table('preventivi', schema=None) as batch_op:
        batch_op.add_column(sa.Column('note', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('preventivi', schema=None) as batch_op:
        batch_op.drop_column('note')

    op.drop_table('preventivo_compagnie')
