"""add cashback base

Revision ID: 20260409_01_cashback_base
Revises: 20260406_01_financeiro_plano_dre
Create Date: 2026-04-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260409_01_cashback_base"
down_revision = "20260406_01_financeiro_plano_dre"
branch_labels = None
depends_on = None
def upgrade():
    op.add_column(
        "clientes",
        sa.Column(
            "saldo_cashback",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_table(
        "cashback_configuracoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("percentual_cashback", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("valor_minimo_venda", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("dias_validade", sa.Integer(), nullable=True),
        sa.Column("permite_uso_no_pdv", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("acumula_com_desconto", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", name="uq_cashback_configuracoes_empresa"),
        sa.CheckConstraint(
            "percentual_cashback >= 0 AND percentual_cashback <= 100",
            name="ck_cashback_configuracoes_percentual_range",
        ),
        sa.CheckConstraint(
            "valor_minimo_venda >= 0",
            name="ck_cashback_configuracoes_valor_minimo_non_negative",
        ),
        sa.CheckConstraint(
            "dias_validade IS NULL OR dias_validade >= 0",
            name="ck_cashback_configuracoes_dias_validade_non_negative",
        ),
    )
    op.create_index(
        op.f("ix_cashback_configuracoes_id"),
        "cashback_configuracoes",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_configuracoes_empresa_id"),
        "cashback_configuracoes",
        ["empresa_id"],
        unique=False,
    )

    op.create_table(
        "cashback_lancamentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("venda_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("origem", sa.String(length=30), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False),
        sa.Column("saldo_apos", sa.Numeric(10, 2), nullable=False),
        sa.Column("expira_em", sa.DateTime(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["venda_id"], ["pdv_vendas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "valor >= 0",
            name="ck_cashback_lancamentos_valor_non_negative",
        ),
        sa.CheckConstraint(
            "saldo_apos >= 0",
            name="ck_cashback_lancamentos_saldo_apos_non_negative",
        ),
        sa.CheckConstraint(
            "tipo IN ('CREDITO', 'DEBITO', 'ESTORNO', 'EXPIRACAO', 'AJUSTE')",
            name="ck_cashback_lancamentos_tipo_valid",
        ),
        sa.CheckConstraint(
            "origem IN ('PDV_VENDA', 'PDV_USO', 'CANCELAMENTO', 'EXPIRACAO', 'MANUAL')",
            name="ck_cashback_lancamentos_origem_valid",
        ),
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_id"),
        "cashback_lancamentos",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_empresa_id"),
        "cashback_lancamentos",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_cliente_id"),
        "cashback_lancamentos",
        ["cliente_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_venda_id"),
        "cashback_lancamentos",
        ["venda_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_tipo"),
        "cashback_lancamentos",
        ["tipo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_origem"),
        "cashback_lancamentos",
        ["origem"],
        unique=False,
    )
    op.create_index(
        op.f("ix_cashback_lancamentos_expira_em"),
        "cashback_lancamentos",
        ["expira_em"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_cashback_lancamentos_expira_em"), table_name="cashback_lancamentos")
    op.drop_index(op.f("ix_cashback_lancamentos_origem"), table_name="cashback_lancamentos")
    op.drop_index(op.f("ix_cashback_lancamentos_tipo"), table_name="cashback_lancamentos")
    op.drop_index(op.f("ix_cashback_lancamentos_venda_id"), table_name="cashback_lancamentos")
    op.drop_index(op.f("ix_cashback_lancamentos_cliente_id"), table_name="cashback_lancamentos")
    op.drop_index(op.f("ix_cashback_lancamentos_empresa_id"), table_name="cashback_lancamentos")
    op.drop_index(op.f("ix_cashback_lancamentos_id"), table_name="cashback_lancamentos")
    op.drop_table("cashback_lancamentos")

    op.drop_index(op.f("ix_cashback_configuracoes_empresa_id"), table_name="cashback_configuracoes")
    op.drop_index(op.f("ix_cashback_configuracoes_id"), table_name="cashback_configuracoes")
    op.drop_table("cashback_configuracoes")

    op.drop_column("clientes", "saldo_cashback")