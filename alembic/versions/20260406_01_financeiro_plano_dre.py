"""cria plano dre e vincula contas a pagar por id

Revision ID: 20260406_01_financeiro_plano_dre
Revises: 4c2b8f9d1a7e
Create Date: 2026-04-06 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect, text


revision = "20260406_01_financeiro_plano_dre"
down_revision = "4c2b8f9d1a7e"
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def _get_columns(bind, table_name: str) -> set[str]:
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade():
    bind = op.get_bind()

    if not _has_table(bind, "financeiro_plano_dre"):
        op.create_table(
            "financeiro_plano_dre",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("empresa_id", sa.Integer(), nullable=False),
            sa.Column("grupo", sa.String(length=100), nullable=False),
            sa.Column("categoria", sa.String(length=100), nullable=False),
            sa.Column("subcategoria", sa.String(length=100), nullable=False),
            sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
            sa.UniqueConstraint(
                "empresa_id",
                "grupo",
                "categoria",
                "subcategoria",
                name="uq_financeiro_plano_dre_empresa_classificacao",
            ),
        )
        op.create_index("ix_financeiro_plano_dre_id", "financeiro_plano_dre", ["id"])
        op.create_index("ix_financeiro_plano_dre_empresa_id", "financeiro_plano_dre", ["empresa_id"])
        op.create_index("ix_financeiro_plano_dre_ativo", "financeiro_plano_dre", ["ativo"])
        op.create_index("ix_financeiro_plano_dre_grupo", "financeiro_plano_dre", ["grupo"])
        op.create_index("ix_financeiro_plano_dre_categoria", "financeiro_plano_dre", ["categoria"])
        op.create_index(
            "ix_financeiro_plano_dre_subcategoria",
            "financeiro_plano_dre",
            ["subcategoria"],
        )

    colunas_pagar = _get_columns(bind, "financeiro_pagar")

    if "classificacao_dre_id" not in colunas_pagar:
        with op.batch_alter_table("financeiro_pagar") as batch_op:
            batch_op.add_column(sa.Column("classificacao_dre_id", sa.Integer(), nullable=True))
            batch_op.create_index(
                "ix_financeiro_pagar_classificacao_dre_id",
                ["classificacao_dre_id"],
            )
            batch_op.create_foreign_key(
                "fk_financeiro_pagar_classificacao_dre_id",
                "financeiro_plano_dre",
                ["classificacao_dre_id"],
                ["id"],
            )

    colunas_pagar = _get_columns(bind, "financeiro_pagar")

    grupo_exists = "grupo_dre" in colunas_pagar
    categoria_exists = "categoria_dre" in colunas_pagar
    subcategoria_exists = "subcategoria_dre" in colunas_pagar

    if grupo_exists and categoria_exists and subcategoria_exists:
        bind.execute(
            text(
                """
                INSERT INTO financeiro_plano_dre (
                    empresa_id,
                    grupo,
                    categoria,
                    subcategoria,
                    ordem,
                    ativo,
                    created_at,
                    updated_at
                )
                SELECT DISTINCT
                    fp.empresa_id,
                    TRIM(COALESCE(NULLIF(fp.grupo_dre, ''), 'Sem grupo')),
                    TRIM(COALESCE(NULLIF(fp.categoria_dre, ''), 'Sem categoria')),
                    TRIM(COALESCE(NULLIF(fp.subcategoria_dre, ''), 'Sem subcategoria')),
                    0,
                    TRUE,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                FROM financeiro_pagar fp
                WHERE fp.empresa_id IS NOT NULL
                ON CONFLICT (
                    empresa_id,
                    grupo,
                    categoria,
                    subcategoria
                ) DO NOTHING
                """
            )
        )

        bind.execute(
            text(
                """
                UPDATE financeiro_pagar fp
                SET classificacao_dre_id = fpd.id
                FROM financeiro_plano_dre fpd
                WHERE
                    fp.classificacao_dre_id IS NULL
                    AND fpd.empresa_id = fp.empresa_id
                    AND fpd.grupo = TRIM(COALESCE(NULLIF(fp.grupo_dre, ''), 'Sem grupo'))
                    AND fpd.categoria = TRIM(COALESCE(NULLIF(fp.categoria_dre, ''), 'Sem categoria'))
                    AND fpd.subcategoria = TRIM(COALESCE(NULLIF(fp.subcategoria_dre, ''), 'Sem subcategoria'))
                """
            )
        )

        with op.batch_alter_table("financeiro_pagar") as batch_op:
            if "grupo_dre" in colunas_pagar:
                batch_op.drop_column("grupo_dre")
            if "categoria_dre" in colunas_pagar:
                batch_op.drop_column("categoria_dre")
            if "subcategoria_dre" in colunas_pagar:
                batch_op.drop_column("subcategoria_dre")


def downgrade():
    bind = op.get_bind()
    colunas_pagar = _get_columns(bind, "financeiro_pagar")

    with op.batch_alter_table("financeiro_pagar") as batch_op:
        if "grupo_dre" not in colunas_pagar:
            batch_op.add_column(sa.Column("grupo_dre", sa.String(length=100), nullable=True))
        if "categoria_dre" not in colunas_pagar:
            batch_op.add_column(sa.Column("categoria_dre", sa.String(length=100), nullable=True))
        if "subcategoria_dre" not in colunas_pagar:
            batch_op.add_column(sa.Column("subcategoria_dre", sa.String(length=100), nullable=True))

    if _has_table(bind, "financeiro_plano_dre"):
        bind.execute(
            text(
                """
                UPDATE financeiro_pagar fp
                SET
                    grupo_dre = fpd.grupo,
                    categoria_dre = fpd.categoria,
                    subcategoria_dre = fpd.subcategoria
                FROM financeiro_plano_dre fpd
                WHERE fp.classificacao_dre_id = fpd.id
                """
            )
        )

    colunas_pagar = _get_columns(bind, "financeiro_pagar")
    if "classificacao_dre_id" in colunas_pagar:
        with op.batch_alter_table("financeiro_pagar") as batch_op:
            try:
                batch_op.drop_constraint(
                    "fk_financeiro_pagar_classificacao_dre_id",
                    type_="foreignkey",
                )
            except Exception:
                pass

            try:
                batch_op.drop_index("ix_financeiro_pagar_classificacao_dre_id")
            except Exception:
                pass

            batch_op.drop_column("classificacao_dre_id")

    if _has_table(bind, "financeiro_plano_dre"):
        for index_name in [
            "ix_financeiro_plano_dre_subcategoria",
            "ix_financeiro_plano_dre_categoria",
            "ix_financeiro_plano_dre_grupo",
            "ix_financeiro_plano_dre_ativo",
            "ix_financeiro_plano_dre_empresa_id",
            "ix_financeiro_plano_dre_id",
        ]:
            try:
                op.drop_index(index_name, table_name="financeiro_plano_dre")
            except Exception:
                pass

        op.drop_table("financeiro_plano_dre")