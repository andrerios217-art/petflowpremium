from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class EstoqueDeposito(Base):
    __tablename__ = "estoque_depositos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    nome = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)

    padrao = Column(Boolean, nullable=False, default=False, server_default="false")
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "nome", name="uq_estoque_depositos_empresa_nome"),
    )

    saldos = relationship("EstoqueSaldo", back_populates="deposito")
    movimentos = relationship("EstoqueMovimento", back_populates="deposito")