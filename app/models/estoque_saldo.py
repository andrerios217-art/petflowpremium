from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class EstoqueSaldo(Base):
    __tablename__ = "estoque_saldos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    deposito_id = Column(Integer, ForeignKey("estoque_depositos.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)

    quantidade_atual = Column(Numeric(14, 3), nullable=False, default=0, server_default="0")

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "deposito_id",
            "produto_id",
            name="uq_estoque_saldos_empresa_deposito_produto",
        ),
    )

    deposito = relationship("EstoqueDeposito", back_populates="saldos")
    produto = relationship("Produto", back_populates="saldos")