"""cria tabelas base de assinaturas

Revision ID: 20260410_assinaturas_base
Revises: 20260409_01_cashback_base
Create Date: 2026-04-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260410_assinaturas_base"
down_revision = "20260409_01_cashback_base"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "assinaturas_pet",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ATIVA"),
        sa.Column("origem", sa.String(length=20), nullable=False, server_default="INTERNA"),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("data_cancelamento", sa.Date(), nullable=True),
        sa.Column("dia_fechamento_ciclo", sa.Integer(), nullable=False, server_default="28"),
        sa.Column("usar_limite_ate_dia_28", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("nao_cumulativa", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("ativa_renovacao", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("valor_bruto", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_desconto", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_final", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("contrato_externo_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["pet_id"], ["pets.id"]),
        sa.CheckConstraint(
            "status IN ('ATIVA', 'PAUSADA', 'CANCELADA', 'ENCERRADA')",
            name="ck_assinaturas_pet_status",
        ),
        sa.CheckConstraint(
            "origem IN ('INTERNA', 'EXTERNA')",
            name="ck_assinaturas_pet_origem",
        ),
        sa.CheckConstraint(
            "dia_fechamento_ciclo >= 1 AND dia_fechamento_ciclo <= 28",
            name="ck_assinaturas_pet_dia_fechamento_1_28",
        ),
        sa.CheckConstraint(
            "valor_bruto >= 0",
            name="ck_assinaturas_pet_valor_bruto_non_negative",
        ),
        sa.CheckConstraint(
            "valor_desconto >= 0",
            name="ck_assinaturas_pet_valor_desconto_non_negative",
        ),
        sa.CheckConstraint(
            "valor_final >= 0",
            name="ck_assinaturas_pet_valor_final_non_negative",
        ),
    )
    op.create_index(op.f("ix_assinaturas_pet_id"), "assinaturas_pet", ["id"], unique=False)
    op.create_index(op.f("ix_assinaturas_pet_empresa_id"), "assinaturas_pet", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_assinaturas_pet_cliente_id"), "assinaturas_pet", ["cliente_id"], unique=False)
    op.create_index(op.f("ix_assinaturas_pet_pet_id"), "assinaturas_pet", ["pet_id"], unique=False)
    op.create_index(op.f("ix_assinaturas_pet_status"), "assinaturas_pet", ["status"], unique=False)
    op.create_index(op.f("ix_assinaturas_pet_origem"), "assinaturas_pet", ["origem"], unique=False)
    op.create_index(
        op.f("ix_assinaturas_pet_contrato_externo_id"),
        "assinaturas_pet",
        ["contrato_externo_id"],
        unique=False,
    )

    op.create_table(
        "assinaturas_pet_itens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assinatura_id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("servico_id", sa.Integer(), nullable=False),
        sa.Column("nome_servico", sa.String(length=150), nullable=False),
        sa.Column("quantidade_contratada", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quantidade_consumida", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("preco_unitario_base", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("percentual_desconto", sa.Numeric(5, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_desconto_unitario", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("preco_unitario_final", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["assinatura_id"], ["assinaturas_pet.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"]),
        sa.CheckConstraint(
            "quantidade_contratada >= 1",
            name="ck_assinaturas_pet_itens_qtd_contratada_min_1",
        ),
        sa.CheckConstraint(
            "quantidade_consumida >= 0",
            name="ck_assinaturas_pet_itens_qtd_consumida_non_negative",
        ),
        sa.CheckConstraint(
            "quantidade_consumida <= quantidade_contratada",
            name="ck_assinaturas_pet_itens_qtd_consumida_lte_contratada",
        ),
        sa.CheckConstraint(
            "preco_unitario_base >= 0",
            name="ck_assinaturas_pet_itens_preco_base_non_negative",
        ),
        sa.CheckConstraint(
            "percentual_desconto >= 0 AND percentual_desconto <= 100",
            name="ck_assinaturas_pet_itens_percentual_desconto_0_100",
        ),
        sa.CheckConstraint(
            "valor_desconto_unitario >= 0",
            name="ck_assinaturas_pet_itens_valor_desconto_unitario_non_negative",
        ),
        sa.CheckConstraint(
            "preco_unitario_final >= 0",
            name="ck_assinaturas_pet_itens_preco_final_non_negative",
        ),
    )
    op.create_index(op.f("ix_assinaturas_pet_itens_id"), "assinaturas_pet_itens", ["id"], unique=False)
    op.create_index(
        op.f("ix_assinaturas_pet_itens_assinatura_id"),
        "assinaturas_pet_itens",
        ["assinatura_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_itens_empresa_id"),
        "assinaturas_pet_itens",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_itens_servico_id"),
        "assinaturas_pet_itens",
        ["servico_id"],
        unique=False,
    )

    op.create_table(
        "assinaturas_pet_consumos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("assinatura_id", sa.Integer(), nullable=False),
        sa.Column("assinatura_item_id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("pet_id", sa.Integer(), nullable=False),
        sa.Column("servico_id", sa.Integer(), nullable=False),
        sa.Column("data_consumo", sa.Date(), nullable=False),
        sa.Column("competencia_ano", sa.Integer(), nullable=False),
        sa.Column("competencia_mes", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("origem", sa.String(length=20), nullable=False, server_default="MANUAL"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="CONFIRMADO"),
        sa.Column("agendamento_id", sa.Integer(), nullable=True),
        sa.Column("pdv_venda_id", sa.Integer(), nullable=True),
        sa.Column("pdv_venda_item_id", sa.Integer(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["assinatura_id"], ["assinaturas_pet.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assinatura_item_id"], ["assinaturas_pet_itens.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["pet_id"], ["pets.id"]),
        sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"]),
        sa.ForeignKeyConstraint(["agendamento_id"], ["agendamentos.id"]),
        sa.ForeignKeyConstraint(["pdv_venda_id"], ["pdv_vendas.id"]),
        sa.ForeignKeyConstraint(["pdv_venda_item_id"], ["pdv_venda_itens.id"]),
        sa.CheckConstraint(
            "competencia_mes >= 1 AND competencia_mes <= 12",
            name="ck_assinaturas_pet_consumos_competencia_mes_1_12",
        ),
        sa.CheckConstraint(
            "competencia_ano >= 2020",
            name="ck_assinaturas_pet_consumos_competencia_ano_min",
        ),
        sa.CheckConstraint(
            "quantidade >= 1",
            name="ck_assinaturas_pet_consumos_quantidade_min_1",
        ),
        sa.CheckConstraint(
            "origem IN ('MANUAL', 'AGENDAMENTO', 'PDV', 'ATENDIMENTO')",
            name="ck_assinaturas_pet_consumos_origem",
        ),
        sa.CheckConstraint(
            "status IN ('PENDENTE', 'CONFIRMADO', 'ESTORNADO', 'CANCELADO')",
            name="ck_assinaturas_pet_consumos_status",
        ),
    )
    op.create_index(op.f("ix_assinaturas_pet_consumos_id"), "assinaturas_pet_consumos", ["id"], unique=False)
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_assinatura_id"),
        "assinaturas_pet_consumos",
        ["assinatura_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_assinatura_item_id"),
        "assinaturas_pet_consumos",
        ["assinatura_item_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_empresa_id"),
        "assinaturas_pet_consumos",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_cliente_id"),
        "assinaturas_pet_consumos",
        ["cliente_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_pet_id"),
        "assinaturas_pet_consumos",
        ["pet_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_servico_id"),
        "assinaturas_pet_consumos",
        ["servico_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_data_consumo"),
        "assinaturas_pet_consumos",
        ["data_consumo"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_competencia_ano"),
        "assinaturas_pet_consumos",
        ["competencia_ano"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_competencia_mes"),
        "assinaturas_pet_consumos",
        ["competencia_mes"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_origem"),
        "assinaturas_pet_consumos",
        ["origem"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_status"),
        "assinaturas_pet_consumos",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_agendamento_id"),
        "assinaturas_pet_consumos",
        ["agendamento_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_pdv_venda_id"),
        "assinaturas_pet_consumos",
        ["pdv_venda_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_assinaturas_pet_consumos_pdv_venda_item_id"),
        "assinaturas_pet_consumos",
        ["pdv_venda_item_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_assinaturas_pet_consumos_pdv_venda_item_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_pdv_venda_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_agendamento_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_status"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_origem"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_competencia_mes"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_competencia_ano"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_data_consumo"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_servico_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_pet_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_cliente_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_empresa_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_assinatura_item_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_assinatura_id"), table_name="assinaturas_pet_consumos")
    op.drop_index(op.f("ix_assinaturas_pet_consumos_id"), table_name="assinaturas_pet_consumos")
    op.drop_table("assinaturas_pet_consumos")

    op.drop_index(op.f("ix_assinaturas_pet_itens_servico_id"), table_name="assinaturas_pet_itens")
    op.drop_index(op.f("ix_assinaturas_pet_itens_empresa_id"), table_name="assinaturas_pet_itens")
    op.drop_index(op.f("ix_assinaturas_pet_itens_assinatura_id"), table_name="assinaturas_pet_itens")
    op.drop_index(op.f("ix_assinaturas_pet_itens_id"), table_name="assinaturas_pet_itens")
    op.drop_table("assinaturas_pet_itens")

    op.drop_index(op.f("ix_assinaturas_pet_contrato_externo_id"), table_name="assinaturas_pet")
    op.drop_index(op.f("ix_assinaturas_pet_origem"), table_name="assinaturas_pet")
    op.drop_index(op.f("ix_assinaturas_pet_status"), table_name="assinaturas_pet")
    op.drop_index(op.f("ix_assinaturas_pet_pet_id"), table_name="assinaturas_pet")
    op.drop_index(op.f("ix_assinaturas_pet_cliente_id"), table_name="assinaturas_pet")
    op.drop_index(op.f("ix_assinaturas_pet_empresa_id"), table_name="assinaturas_pet")
    op.drop_index(op.f("ix_assinaturas_pet_id"), table_name="assinaturas_pet")
    op.drop_table("assinaturas_pet")