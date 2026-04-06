"""add campos dre financeiro pagar

Revision ID: 4c2b8f9d1a7e
Revises: 3f9c2b7a1d10
Create Date: 2026-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4c2b8f9d1a7e"
down_revision = "8ebb6229bdeb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "financeiro_pagar",
        sa.Column("grupo_dre", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "financeiro_pagar",
        sa.Column("categoria_dre", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "financeiro_pagar",
        sa.Column("subcategoria_dre", sa.String(length=100), nullable=True),
    )

    op.create_index(
        "ix_financeiro_pagar_grupo_dre",
        "financeiro_pagar",
        ["grupo_dre"],
        unique=False,
    )
    op.create_index(
        "ix_financeiro_pagar_categoria_dre",
        "financeiro_pagar",
        ["categoria_dre"],
        unique=False,
    )
    op.create_index(
        "ix_financeiro_pagar_subcategoria_dre",
        "financeiro_pagar",
        ["subcategoria_dre"],
        unique=False,
    )


def downgrade():
    op.drop_index("ix_financeiro_pagar_subcategoria_dre", table_name="financeiro_pagar")
    op.drop_index("ix_financeiro_pagar_categoria_dre", table_name="financeiro_pagar")
    op.drop_index("ix_financeiro_pagar_grupo_dre", table_name="financeiro_pagar")

    op.drop_column("financeiro_pagar", "subcategoria_dre")
    op.drop_column("financeiro_pagar", "categoria_dre")
    op.drop_column("financeiro_pagar", "grupo_dre")