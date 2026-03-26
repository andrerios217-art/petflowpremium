"""add origem_item_id to estoque_movimentos

Revision ID: 20260325_add_origem_item_id_to_estoque_movimentos
Revises: AJUSTAR_DOWN_REVISION_AQUI
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260325_add_origem_item_id_to_estoque_movimentos"
down_revision = "AJUSTAR_DOWN_REVISION_AQUI"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "estoque_movimentos",
        sa.Column("origem_item_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_estoque_movimentos_origem_item_id",
        "estoque_movimentos",
        ["origem_item_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_estoque_movimentos_origem_item_id",
        table_name="estoque_movimentos",
    )
    op.drop_column("estoque_movimentos", "origem_item_id")