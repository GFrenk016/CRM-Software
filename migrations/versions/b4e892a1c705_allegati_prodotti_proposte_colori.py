"""Allegati contestuali, prodotti, proposte e colori compagnie.

Revision ID: b4e892a1c705
Revises: 7026369d95aa
"""
from alembic import op
import sqlalchemy as sa

revision = "b4e892a1c705"
down_revision = "7026369d95aa"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("compagnie") as b:
        b.add_column(sa.Column("colore", sa.String(7), nullable=False,
                               server_default="#2563eb"))
    op.create_table("altri_prodotti",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clienti.id"), nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("numero_tessera", sa.String(80)),
        sa.Column("descrizione", sa.Text()))
    op.create_table("proposte",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clienti.id"), nullable=False),
        sa.Column("numero", sa.String(80), nullable=False),
        sa.Column("note", sa.Text()))
    op.create_table("relazioni_clienti",
        sa.Column("cliente_a_id", sa.Integer(), sa.ForeignKey("clienti.id"), primary_key=True),
        sa.Column("cliente_b_id", sa.Integer(), sa.ForeignKey("clienti.id"), primary_key=True),
        sa.Column("descrizione", sa.String(80)))
    with op.batch_alter_table("documenti") as b:
        for column, table in (("contratto_id", "contratti"),
                              ("veicolo_id", "veicoli"),
                              ("prodotto_id", "altri_prodotti"),
                              ("proposta_id", "proposte")):
            b.add_column(sa.Column(column, sa.Integer()))
            b.create_foreign_key(f"fk_documenti_{column}", table, [column], ["id"])


def downgrade():
    with op.batch_alter_table("documenti") as b:
        b.drop_column("proposta_id")
        b.drop_column("prodotto_id")
        b.drop_column("veicolo_id")
        b.drop_column("contratto_id")
    op.drop_table("proposte")
    op.drop_table("relazioni_clienti")
    op.drop_table("altri_prodotti")
    with op.batch_alter_table("compagnie") as b:
        b.drop_column("colore")
