"""bloco4a_nota_entrada_base

Revision ID: 9b7a4c2d1e30
Revises: 3f9c2b7a1d10
Create Date: 2026-03-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9b7a4c2d1e30"
down_revision = "3f9c2b7a1d10"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notas_entrada",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("chave_acesso", sa.String(length=44), nullable=False),
        sa.Column("numero", sa.String(length=20), nullable=True),
        sa.Column("serie", sa.String(length=10), nullable=True),
        sa.Column("modelo", sa.String(length=10), nullable=True),
        sa.Column("data_emissao", sa.DateTime(), nullable=True),
        sa.Column("data_entrada", sa.DateTime(), nullable=True),
        sa.Column("fornecedor_cnpj", sa.String(length=20), nullable=True),
        sa.Column("fornecedor_nome", sa.String(length=180), nullable=True),
        sa.Column("valor_total_produtos", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_total_nota", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_frete", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_seguro", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_desconto", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_outras_despesas", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="IMPORTADA"),
        sa.Column("xml_original", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "chave_acesso", name="uq_notas_entrada_empresa_chave_acesso"),
    )
    op.create_index(op.f("ix_notas_entrada_id"), "notas_entrada", ["id"], unique=False)
    op.create_index(op.f("ix_notas_entrada_empresa_id"), "notas_entrada", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_notas_entrada_chave_acesso"), "notas_entrada", ["chave_acesso"], unique=False)
    op.create_index(op.f("ix_notas_entrada_numero"), "notas_entrada", ["numero"], unique=False)
    op.create_index(op.f("ix_notas_entrada_fornecedor_cnpj"), "notas_entrada", ["fornecedor_cnpj"], unique=False)
    op.create_index(op.f("ix_notas_entrada_status"), "notas_entrada", ["status"], unique=False)

    op.create_table(
        "notas_entrada_itens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nota_entrada_id", sa.Integer(), nullable=False),
        sa.Column("item_numero", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=True),
        sa.Column("codigo_fornecedor", sa.String(length=60), nullable=True),
        sa.Column("codigo_barras_nf", sa.String(length=60), nullable=True),
        sa.Column("codigo_barras_tributavel_nf", sa.String(length=60), nullable=True),
        sa.Column("descricao_nf", sa.String(length=255), nullable=False),
        sa.Column("ncm", sa.String(length=20), nullable=True),
        sa.Column("cest", sa.String(length=20), nullable=True),
        sa.Column("cfop", sa.String(length=10), nullable=True),
        sa.Column("unidade_comercial", sa.String(length=20), nullable=True),
        sa.Column("unidade_tributavel", sa.String(length=20), nullable=True),
        sa.Column("quantidade_comercial", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("quantidade_tributavel", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("valor_unitario_comercial", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("valor_unitario_tributavel", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("valor_total_bruto", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("desconto", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("frete", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("seguro", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("outras_despesas", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("origem_fiscal", sa.String(length=1), nullable=True),
        sa.Column("cst_icms", sa.String(length=4), nullable=True),
        sa.Column("csosn", sa.String(length=4), nullable=True),
        sa.Column("cst_pis", sa.String(length=4), nullable=True),
        sa.Column("cst_cofins", sa.String(length=4), nullable=True),
        sa.Column("aliquota_icms", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("aliquota_pis", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("aliquota_cofins", sa.Numeric(8, 4), nullable=False, server_default="0"),
        sa.Column("valor_icms", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_pis", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("valor_cofins", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("match_tipo", sa.String(length=30), nullable=False, server_default="SEM_MATCH"),
        sa.Column("match_confiavel", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("observacao_match", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["nota_entrada_id"], ["notas_entrada.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notas_entrada_itens_id"), "notas_entrada_itens", ["id"], unique=False)
    op.create_index(op.f("ix_notas_entrada_itens_nota_entrada_id"), "notas_entrada_itens", ["nota_entrada_id"], unique=False)
    op.create_index(op.f("ix_notas_entrada_itens_produto_id"), "notas_entrada_itens", ["produto_id"], unique=False)
    op.create_index(op.f("ix_notas_entrada_itens_codigo_fornecedor"), "notas_entrada_itens", ["codigo_fornecedor"], unique=False)
    op.create_index(op.f("ix_notas_entrada_itens_codigo_barras_nf"), "notas_entrada_itens", ["codigo_barras_nf"], unique=False)
    op.create_index(
        op.f("ix_notas_entrada_itens_codigo_barras_tributavel_nf"),
        "notas_entrada_itens",
        ["codigo_barras_tributavel_nf"],
        unique=False,
    )
    op.create_index(op.f("ix_notas_entrada_itens_ncm"), "notas_entrada_itens", ["ncm"], unique=False)

    op.create_table(
        "produtos_fornecedores_vinculos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("fornecedor_cnpj", sa.String(length=20), nullable=False),
        sa.Column("codigo_fornecedor", sa.String(length=60), nullable=True),
        sa.Column("codigo_barras_fornecedor", sa.String(length=60), nullable=True),
        sa.Column("ultima_descricao_nf", sa.String(length=255), nullable=True),
        sa.Column("ultimo_ncm", sa.String(length=20), nullable=True),
        sa.Column("ultimo_cest", sa.String(length=20), nullable=True),
        sa.Column("ultimo_cfop", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "empresa_id",
            "fornecedor_cnpj",
            "produto_id",
            name="uq_produto_fornecedor_vinculo_empresa_fornecedor_produto",
        ),
    )
    op.create_index(
        op.f("ix_produtos_fornecedores_vinculos_id"),
        "produtos_fornecedores_vinculos",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_produtos_fornecedores_vinculos_empresa_id"),
        "produtos_fornecedores_vinculos",
        ["empresa_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_produtos_fornecedores_vinculos_produto_id"),
        "produtos_fornecedores_vinculos",
        ["produto_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_produtos_fornecedores_vinculos_fornecedor_cnpj"),
        "produtos_fornecedores_vinculos",
        ["fornecedor_cnpj"],
        unique=False,
    )
    op.create_index(
        op.f("ix_produtos_fornecedores_vinculos_codigo_fornecedor"),
        "produtos_fornecedores_vinculos",
        ["codigo_fornecedor"],
        unique=False,
    )
    op.create_index(
        op.f("ix_produtos_fornecedores_vinculos_codigo_barras_fornecedor"),
        "produtos_fornecedores_vinculos",
        ["codigo_barras_fornecedor"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_produtos_fornecedores_vinculos_codigo_barras_fornecedor"), table_name="produtos_fornecedores_vinculos")
    op.drop_index(op.f("ix_produtos_fornecedores_vinculos_codigo_fornecedor"), table_name="produtos_fornecedores_vinculos")
    op.drop_index(op.f("ix_produtos_fornecedores_vinculos_fornecedor_cnpj"), table_name="produtos_fornecedores_vinculos")
    op.drop_index(op.f("ix_produtos_fornecedores_vinculos_produto_id"), table_name="produtos_fornecedores_vinculos")
    op.drop_index(op.f("ix_produtos_fornecedores_vinculos_empresa_id"), table_name="produtos_fornecedores_vinculos")
    op.drop_index(op.f("ix_produtos_fornecedores_vinculos_id"), table_name="produtos_fornecedores_vinculos")
    op.drop_table("produtos_fornecedores_vinculos")

    op.drop_index(op.f("ix_notas_entrada_itens_ncm"), table_name="notas_entrada_itens")
    op.drop_index(op.f("ix_notas_entrada_itens_codigo_barras_tributavel_nf"), table_name="notas_entrada_itens")
    op.drop_index(op.f("ix_notas_entrada_itens_codigo_barras_nf"), table_name="notas_entrada_itens")
    op.drop_index(op.f("ix_notas_entrada_itens_codigo_fornecedor"), table_name="notas_entrada_itens")
    op.drop_index(op.f("ix_notas_entrada_itens_produto_id"), table_name="notas_entrada_itens")
    op.drop_index(op.f("ix_notas_entrada_itens_nota_entrada_id"), table_name="notas_entrada_itens")
    op.drop_index(op.f("ix_notas_entrada_itens_id"), table_name="notas_entrada_itens")
    op.drop_table("notas_entrada_itens")

    op.drop_index(op.f("ix_notas_entrada_status"), table_name="notas_entrada")
    op.drop_index(op.f("ix_notas_entrada_fornecedor_cnpj"), table_name="notas_entrada")
    op.drop_index(op.f("ix_notas_entrada_numero"), table_name="notas_entrada")
    op.drop_index(op.f("ix_notas_entrada_chave_acesso"), table_name="notas_entrada")
    op.drop_index(op.f("ix_notas_entrada_empresa_id"), table_name="notas_entrada")
    op.drop_index(op.f("ix_notas_entrada_id"), table_name="notas_entrada")
    op.drop_table("notas_entrada") 