from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class FinanceiroPlanoDRE(Base):
    __tablename__ = "financeiro_plano_dre"

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "grupo",
            "categoria",
            "subcategoria",
            name="uq_financeiro_plano_dre_empresa_classificacao",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    grupo = Column(String(100), nullable=False, index=True)
    categoria = Column(String(100), nullable=False, index=True)
    subcategoria = Column(String(100), nullable=False, index=True)

    ordem = Column(Integer, nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    empresa = relationship("Empresa")
    contas_pagar = relationship("FinanceiroPagar", back_populates="classificacao_dre")