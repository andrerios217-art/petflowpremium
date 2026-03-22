from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    categoria_id = Column(Integer, ForeignKey("produto_categorias.id"), nullable=True, index=True)

    sku = Column(String(60), nullable=False)
    nome = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=True)
    unidade = Column(String(20), nullable=False, default="UN", server_default="UN")

    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
    aceita_fracionado = Column(Boolean, nullable=False, default=False, server_default="false")

    preco_venda_atual = Column(Numeric(10, 2), nullable=False, default=0, server_default="0")
    estoque_minimo = Column(Numeric(10, 3), nullable=False, default=0, server_default="0")

    observacao = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "sku", name="uq_produtos_empresa_sku"),
    )

    categoria = relationship("ProdutoCategoria", back_populates="produtos")
    codigos_barras = relationship(
        "ProdutoCodigoBarras",
        back_populates="produto",
        cascade="all, delete-orphan",
    )
    saldos = relationship("EstoqueSaldo", back_populates="produto")
    movimentos = relationship("EstoqueMovimento", back_populates="produto")