"""adiciona campos cadastrais e endereco_loja em empresas

Revision ID: 20260420_empresa_dados_endereco
Revises: bf1fcc4f859f
Create Date: 2026-04-20 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260420_empresa_dados_endereco"
down_revision = "bf1fcc4f859f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("empresas", sa.Column("razao_social", sa.String(length=180), nullable=True))
    op.add_column("empresas", sa.Column("nome_fantasia", sa.String(length=180), nullable=True))
    op.add_column("empresas", sa.Column("telefone", sa.String(length=25), nullable=True))
    op.add_column("empresas", sa.Column("email", sa.String(length=150), nullable=True))
    op.add_column("empresas", sa.Column("cep", sa.String(length=10), nullable=True))
    op.add_column("empresas", sa.Column("logradouro", sa.String(length=180), nullable=True))
    op.add_column("empresas", sa.Column("numero", sa.String(length=20), nullable=True))
    op.add_column("empresas", sa.Column("complemento", sa.String(length=120), nullable=True))
    op.add_column("empresas", sa.Column("bairro", sa.String(length=120), nullable=True))
    op.add_column("empresas", sa.Column("cidade", sa.String(length=120), nullable=True))
    op.add_column("empresas", sa.Column("uf", sa.String(length=2), nullable=True))
    op.add_column("empresas", sa.Column("endereco_loja", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("empresas", "endereco_loja")
    op.drop_column("empresas", "uf")
    op.drop_column("empresas", "cidade")
    op.drop_column("empresas", "bairro")
    op.drop_column("empresas", "complemento")
    op.drop_column("empresas", "numero")
    op.drop_column("empresas", "logradouro")
    op.drop_column("empresas", "cep")
    op.drop_column("empresas", "email")
    op.drop_column("empresas", "telefone")
    op.drop_column("empresas", "nome_fantasia")
    op.drop_column("empresas", "razao_social")