"""Nucleo familiare e descrizione dei legami fra clienti.

Revision ID: f7105a924edd
Revises: b4e892a1c705
"""
from alembic import op
import sqlalchemy as sa

revision = "f7105a924edd"
down_revision = "b4e892a1c705"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("clienti") as b:
        b.add_column(sa.Column("nucleo_familiare", sa.String(200)))
    with op.batch_alter_table("relazioni_clienti") as b:
        b.add_column(sa.Column("descrizione_inversa", sa.String(80)))
    # La vecchia spunta non descrive chi vive nel nucleo. Ne conserviamo
    # l'informazione senza dedurre coniuge, figli o altri componenti.
    op.execute("UPDATE clienti SET nucleo_familiare = 'Convivenza indicata in precedenza' WHERE convivenza = 1")


def downgrade():
    with op.batch_alter_table("relazioni_clienti") as b:
        b.drop_column("descrizione_inversa")
    with op.batch_alter_table("clienti") as b:
        b.drop_column("nucleo_familiare")
