from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProdutoCodigoBarras(Base):
    __tablename__ = "produto_codigos_barras"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)

    codigo = Column(String(60), nullable=False)
    tipo = Column(String(20), nullable=False, default="INTERNO", server_default="INTERNO")

    principal = Column(Boolean, nullable=False, default=False, server_default="false")
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("empresa_id", "codigo", name="uq_produto_codigos_barras_empresa_codigo"),
    )

    produto = relationship("Produto", back_populates="codigos_barras")