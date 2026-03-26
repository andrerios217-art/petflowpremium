from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class EstoqueMovimento(Base):
    __tablename__ = "estoque_movimentos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    deposito_id = Column(Integer, ForeignKey("estoque_depositos.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)

    tipo_movimento = Column(String(20), nullable=False, index=True)
    origem = Column(String(20), nullable=False, index=True)
    origem_id = Column(Integer, nullable=True, index=True)
    origem_item_id = Column(Integer, nullable=True, index=True)

    quantidade = Column(Numeric(14, 3), nullable=False)
    saldo_antes = Column(Numeric(14, 3), nullable=False)
    saldo_depois = Column(Numeric(14, 3), nullable=False)

    custo_unitario = Column(Numeric(10, 2), nullable=True)
    documento_referencia = Column(String(120), nullable=True)
    observacao = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deposito = relationship("EstoqueDeposito", back_populates="movimentos")
    produto = relationship("Produto", back_populates="movimentos")