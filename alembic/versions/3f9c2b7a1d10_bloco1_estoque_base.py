from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3f9c2b7a1d10"
down_revision = "1218e1e21f2f"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "produto_categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("margem_padrao_pct", sa.Numeric(10, 2), nullable=True),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "nome", name="uq_produto_categorias_empresa_nome"),
    )
    op.create_index(op.f("ix_produto_categorias_empresa_id"), "produto_categorias", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_produto_categorias_id"), "produto_categorias", ["id"], unique=False)

    op.create_table(
        "produtos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=True),
        sa.Column("sku", sa.String(length=60), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("unidade", sa.String(length=20), server_default="UN", nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("aceita_fracionado", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("preco_venda_atual", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("estoque_minimo", sa.Numeric(10, 3), server_default="0", nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["categoria_id"], ["produto_categorias.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "sku", name="uq_produtos_empresa_sku"),
    )
    op.create_index(op.f("ix_produtos_categoria_id"), "produtos", ["categoria_id"], unique=False)
    op.create_index(op.f("ix_produtos_empresa_id"), "produtos", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_produtos_id"), "produtos", ["id"], unique=False)

    op.create_table(
        "produto_codigos_barras",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=60), nullable=False),
        sa.Column("tipo", sa.String(length=20), server_default="INTERNO", nullable=False),
        sa.Column("principal", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "codigo", name="uq_produto_codigos_barras_empresa_codigo"),
    )
    op.create_index(op.f("ix_produto_codigos_barras_empresa_id"), "produto_codigos_barras", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_produto_codigos_barras_id"), "produto_codigos_barras", ["id"], unique=False)
    op.create_index(op.f("ix_produto_codigos_barras_produto_id"), "produto_codigos_barras", ["produto_id"], unique=False)

    op.create_table(
        "estoque_depositos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("padrao", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("ativo", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("empresa_id", "nome", name="uq_estoque_depositos_empresa_nome"),
    )
    op.create_index(op.f("ix_estoque_depositos_empresa_id"), "estoque_depositos", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_estoque_depositos_id"), "estoque_depositos", ["id"], unique=False)

    op.create_table(
        "estoque_saldos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("deposito_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("quantidade_atual", sa.Numeric(14, 3), server_default="0", nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["deposito_id"], ["estoque_depositos.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "empresa_id",
            "deposito_id",
            "produto_id",
            name="uq_estoque_saldos_empresa_deposito_produto",
        ),
    )
    op.create_index(op.f("ix_estoque_saldos_deposito_id"), "estoque_saldos", ["deposito_id"], unique=False)
    op.create_index(op.f("ix_estoque_saldos_empresa_id"), "estoque_saldos", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_estoque_saldos_id"), "estoque_saldos", ["id"], unique=False)
    op.create_index(op.f("ix_estoque_saldos_produto_id"), "estoque_saldos", ["produto_id"], unique=False)

    op.create_table(
        "estoque_movimentos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("deposito_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("tipo_movimento", sa.String(length=20), nullable=False),
        sa.Column("origem", sa.String(length=20), nullable=False),
        sa.Column("origem_id", sa.Integer(), nullable=True),
        sa.Column("quantidade", sa.Numeric(14, 3), nullable=False),
        sa.Column("saldo_antes", sa.Numeric(14, 3), nullable=False),
        sa.Column("saldo_depois", sa.Numeric(14, 3), nullable=False),
        sa.Column("custo_unitario", sa.Numeric(10, 2), nullable=True),
        sa.Column("documento_referencia", sa.String(length=120), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["deposito_id"], ["estoque_depositos.id"]),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_estoque_movimentos_deposito_id"), "estoque_movimentos", ["deposito_id"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_empresa_id"), "estoque_movimentos", ["empresa_id"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_id"), "estoque_movimentos", ["id"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_origem"), "estoque_movimentos", ["origem"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_origem_id"), "estoque_movimentos", ["origem_id"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_produto_id"), "estoque_movimentos", ["produto_id"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_tipo_movimento"), "estoque_movimentos", ["tipo_movimento"], unique=False)
    op.create_index(op.f("ix_estoque_movimentos_usuario_id"), "estoque_movimentos", ["usuario_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_estoque_movimentos_usuario_id"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_tipo_movimento"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_produto_id"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_origem_id"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_origem"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_id"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_empresa_id"), table_name="estoque_movimentos")
    op.drop_index(op.f("ix_estoque_movimentos_deposito_id"), table_name="estoque_movimentos")
    op.drop_table("estoque_movimentos")

    op.drop_index(op.f("ix_estoque_saldos_produto_id"), table_name="estoque_saldos")
    op.drop_index(op.f("ix_estoque_saldos_id"), table_name="estoque_saldos")
    op.drop_index(op.f("ix_estoque_saldos_empresa_id"), table_name="estoque_saldos")
    op.drop_index(op.f("ix_estoque_saldos_deposito_id"), table_name="estoque_saldos")
    op.drop_table("estoque_saldos")

    op.drop_index(op.f("ix_estoque_depositos_id"), table_name="estoque_depositos")
    op.drop_index(op.f("ix_estoque_depositos_empresa_id"), table_name="estoque_depositos")
    op.drop_table("estoque_depositos")

    op.drop_index(op.f("ix_produto_codigos_barras_produto_id"), table_name="produto_codigos_barras")
    op.drop_index(op.f("ix_produto_codigos_barras_id"), table_name="produto_codigos_barras")
    op.drop_index(op.f("ix_produto_codigos_barras_empresa_id"), table_name="produto_codigos_barras")
    op.drop_table("produto_codigos_barras")

    op.drop_index(op.f("ix_produtos_id"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_empresa_id"), table_name="produtos")
    op.drop_index(op.f("ix_produtos_categoria_id"), table_name="produtos")
    op.drop_table("produtos")

    op.drop_index(op.f("ix_produto_categorias_id"), table_name="produto_categorias")
    op.drop_index(op.f("ix_produto_categorias_empresa_id"), table_name="produto_categorias")
    op.drop_table("produto_categorias")