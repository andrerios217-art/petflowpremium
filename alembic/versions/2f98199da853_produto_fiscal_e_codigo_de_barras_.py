from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2f98199da853"
down_revision = "3f9c2b7a1d10"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "produtos",
        sa.Column("codigo_barras_principal", sa.String(length=60), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column(
            "custo_medio_atual",
            sa.Numeric(10, 4),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "produtos",
        sa.Column("ncm", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("cest", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("cfop_padrao", sa.String(length=10), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("origem_fiscal", sa.String(length=1), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("cst_icms", sa.String(length=4), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("csosn", sa.String(length=4), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("cst_pis", sa.String(length=4), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column("cst_cofins", sa.String(length=4), nullable=True),
    )
    op.add_column(
        "produtos",
        sa.Column(
            "aliquota_icms",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "produtos",
        sa.Column(
            "aliquota_pis",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "produtos",
        sa.Column(
            "aliquota_cofins",
            sa.Numeric(5, 2),
            nullable=False,
            server_default="0",
        ),
    )

    op.create_index(
        "ix_produtos_codigo_barras_principal",
        "produtos",
        ["codigo_barras_principal"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_produtos_empresa_codigo_barras_principal",
        "produtos",
        ["empresa_id", "codigo_barras_principal"],
    )

    op.create_check_constraint(
        "ck_produtos_custo_medio_atual_non_negative",
        "produtos",
        "custo_medio_atual >= 0",
    )
    op.create_check_constraint(
        "ck_produtos_aliquota_icms_range",
        "produtos",
        "aliquota_icms >= 0 AND aliquota_icms <= 100",
    )
    op.create_check_constraint(
        "ck_produtos_aliquota_pis_range",
        "produtos",
        "aliquota_pis >= 0 AND aliquota_pis <= 100",
    )
    op.create_check_constraint(
        "ck_produtos_aliquota_cofins_range",
        "produtos",
        "aliquota_cofins >= 0 AND aliquota_cofins <= 100",
    )
    op.create_check_constraint(
        "ck_produtos_origem_fiscal_valida",
        "produtos",
        "origem_fiscal IS NULL OR origem_fiscal IN ('0', '1', '2', '3', '4', '5', '6', '7', '8')",
    )

    op.alter_column("produtos", "custo_medio_atual", server_default=None)
    op.alter_column("produtos", "aliquota_icms", server_default=None)
    op.alter_column("produtos", "aliquota_pis", server_default=None)
    op.alter_column("produtos", "aliquota_cofins", server_default=None)


def downgrade():
    op.drop_constraint("ck_produtos_origem_fiscal_valida", "produtos", type_="check")
    op.drop_constraint("ck_produtos_aliquota_cofins_range", "produtos", type_="check")
    op.drop_constraint("ck_produtos_aliquota_pis_range", "produtos", type_="check")
    op.drop_constraint("ck_produtos_aliquota_icms_range", "produtos", type_="check")
    op.drop_constraint("ck_produtos_custo_medio_atual_non_negative", "produtos", type_="check")

    op.drop_constraint(
        "uq_produtos_empresa_codigo_barras_principal",
        "produtos",
        type_="unique",
    )
    op.drop_index("ix_produtos_codigo_barras_principal", table_name="produtos")

    op.drop_column("produtos", "aliquota_cofins")
    op.drop_column("produtos", "aliquota_pis")
    op.drop_column("produtos", "aliquota_icms")
    op.drop_column("produtos", "cst_cofins")
    op.drop_column("produtos", "cst_pis")
    op.drop_column("produtos", "csosn")
    op.drop_column("produtos", "cst_icms")
    op.drop_column("produtos", "origem_fiscal")
    op.drop_column("produtos", "cfop_padrao")
    op.drop_column("produtos", "cest")
    op.drop_column("produtos", "ncm")
    op.drop_column("produtos", "custo_medio_atual")
    op.drop_column("produtos", "codigo_barras_principal")