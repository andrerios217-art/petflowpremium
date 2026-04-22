"""cria tabela de receitas emitidas veterinarias

Revision ID: 20260422_receitas_emitidas
Revises: 20260420_empresa_dados_endereco
Create Date: 2026-04-22 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260422_receitas_emitidas"
down_revision = "20260420_empresa_dados_endereco"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pet_receitas_emitidas",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("atendimento_id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("veterinario_id", sa.Integer(), nullable=True),
        sa.Column("codigo_verificacao", sa.String(length=32), nullable=False),
        sa.Column("hash_documento", sa.String(length=128), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("snapshot_texto_canonico", sa.Text(), nullable=False),
        sa.Column("emitido_em", sa.DateTime(), nullable=False),
        sa.Column("cancelado_em", sa.DateTime(), nullable=True),
        sa.Column("cancelado_motivo", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["atendimento_id"], ["atendimentos_clinicos.id"]),
        sa.ForeignKeyConstraint(["pet_id"], ["pets.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["veterinario_id"], ["funcionarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_pet_receitas_emitidas_id",
        "pet_receitas_emitidas",
        ["id"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_empresa_id",
        "pet_receitas_emitidas",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_atendimento_id",
        "pet_receitas_emitidas",
        ["atendimento_id"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_pet_id",
        "pet_receitas_emitidas",
        ["pet_id"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_cliente_id",
        "pet_receitas_emitidas",
        ["cliente_id"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_veterinario_id",
        "pet_receitas_emitidas",
        ["veterinario_id"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_codigo_verificacao",
        "pet_receitas_emitidas",
        ["codigo_verificacao"],
        unique=True,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_hash_documento",
        "pet_receitas_emitidas",
        ["hash_documento"],
        unique=False,
    )
    op.create_index(
        "ix_pet_receitas_emitidas_emitido_em",
        "pet_receitas_emitidas",
        ["emitido_em"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_pet_receitas_emitidas_emitido_em", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_hash_documento", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_codigo_verificacao", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_veterinario_id", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_cliente_id", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_pet_id", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_atendimento_id", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_empresa_id", table_name="pet_receitas_emitidas")
    op.drop_index("ix_pet_receitas_emitidas_id", table_name="pet_receitas_emitidas")
    op.drop_table("pet_receitas_emitidas")