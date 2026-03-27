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


class EmpresaPrecificacaoConfig(Base):
    __tablename__ = "empresa_precificacao_configs"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    modo_padrao = Column(String(20), nullable=False, default="MARKUP", server_default="MARKUP")
    percentual_padrao = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", name="uq_empresa_precificacao_configs_empresa_id"),
        CheckConstraint(
            "modo_padrao IN ('MARKUP', 'MARGEM')",
            name="ck_empresa_precificacao_configs_modo_padrao_valido",
        ),
        CheckConstraint(
            "percentual_padrao >= 0",
            name="ck_empresa_precificacao_configs_percentual_padrao_non_negative",
        ),
    )