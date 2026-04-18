"""adiciona pontos_tosa_higienica em comissao_configuracoes

Revision ID: 20260417_comissao_tosa_higienica
Revises: 20260410_assinaturas_base
Create Date: 2026-04-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260417_comissao_tosa_higienica"
down_revision = "20260410_assinaturas_base"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "comissao_configuracoes",
        sa.Column("pontos_tosa_higienica", sa.Integer(), nullable=False, server_default="0"),
    )
    op.alter_column("comissao_configuracoes", "pontos_tosa_higienica", server_default=None)


def downgrade():
    op.drop_column("comissao_configuracoes", "pontos_tosa_higienica")