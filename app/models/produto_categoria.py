from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProdutoCategoria(Base):
    __tablename__ = "produto_categorias"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    nome = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)
    margem_padrao_pct = Column(Numeric(10, 2), nullable=True)

    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "nome", name="uq_produto_categorias_empresa_nome"),
    )

    produtos = relationship("Produto", back_populates="categoria")