from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotaEntradaItem(Base):
    __tablename__ = "notas_entrada_itens"

    id = Column(Integer, primary_key=True, index=True)
    nota_entrada_id = Column(Integer, ForeignKey("notas_entrada.id"), nullable=False, index=True)

    item_numero = Column(Integer, nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=True, index=True)

    codigo_fornecedor = Column(String(60), nullable=True, index=True)
    codigo_barras_nf = Column(String(60), nullable=True, index=True)
    codigo_barras_tributavel_nf = Column(String(60), nullable=True, index=True)
    descricao_nf = Column(String(255), nullable=False)

    ncm = Column(String(20), nullable=True, index=True)
    cest = Column(String(20), nullable=True)
    cfop = Column(String(10), nullable=True)

    unidade_comercial = Column(String(20), nullable=True)
    unidade_tributavel = Column(String(20), nullable=True)

    quantidade_comercial = Column(
        Numeric(14, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0",
    )
    quantidade_tributavel = Column(
        Numeric(14, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0",
    )

    valor_unitario_comercial = Column(
        Numeric(14, 6),
        nullable=False,
        default=Decimal("0.000000"),
        server_default="0",
    )
    valor_unitario_tributavel = Column(
        Numeric(14, 6),
        nullable=False,
        default=Decimal("0.000000"),
        server_default="0",
    )

    valor_total_bruto = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    desconto = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    frete = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    seguro = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    outras_despesas = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    origem_fiscal = Column(String(1), nullable=True)
    cst_icms = Column(String(4), nullable=True)
    csosn = Column(String(4), nullable=True)
    cst_pis = Column(String(4), nullable=True)
    cst_cofins = Column(String(4), nullable=True)

    aliquota_icms = Column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0",
    )
    aliquota_pis = Column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0",
    )
    aliquota_cofins = Column(
        Numeric(8, 4),
        nullable=False,
        default=Decimal("0.0000"),
        server_default="0",
    )

    valor_icms = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_pis = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_cofins = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    match_tipo = Column(String(30), nullable=False, default="SEM_MATCH", server_default="SEM_MATCH")
    match_confiavel = Column(Boolean, nullable=False, default=False, server_default="false")
    observacao_match = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    nota_entrada = relationship("NotaEntrada", back_populates="itens")
    produto = relationship("Produto")