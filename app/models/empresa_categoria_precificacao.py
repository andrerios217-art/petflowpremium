from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)

from app.core.database import Base


class EmpresaCategoriaPrecificacao(Base):
    __tablename__ = "empresa_categoria_precificacoes"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey("produto_categorias.id"), nullable=False, index=True)

    modo = Column(String(20), nullable=False, default="MARKUP", server_default="MARKUP")
    percentual = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "categoria_id",
            name="uq_empresa_categoria_precificacoes_empresa_categoria",
        ),
        CheckConstraint(
            "modo IN ('MARKUP', 'MARGEM')",
            name="ck_empresa_categoria_precificacoes_modo_valido",
        ),
        CheckConstraint(
            "percentual >= 0",
            name="ck_empresa_categoria_precificacoes_percentual_non_negative",
        ),
    )