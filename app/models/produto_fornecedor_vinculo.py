from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.core.database import Base


class ProdutoFornecedorVinculo(Base):
    __tablename__ = "produtos_fornecedores_vinculos"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False, index=True)

    fornecedor_cnpj = Column(String(20), nullable=False, index=True)
    codigo_fornecedor = Column(String(60), nullable=True, index=True)
    codigo_barras_fornecedor = Column(String(60), nullable=True, index=True)

    ultima_descricao_nf = Column(String(255), nullable=True)
    ultimo_ncm = Column(String(20), nullable=True)
    ultimo_cest = Column(String(20), nullable=True)
    ultimo_cfop = Column(String(10), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "fornecedor_cnpj",
            "produto_id",
            name="uq_produto_fornecedor_vinculo_empresa_fornecedor_produto",
        ),
    )