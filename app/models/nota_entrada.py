from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotaEntrada(Base):
    __tablename__ = "notas_entrada"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    chave_acesso = Column(String(44), nullable=False, index=True)
    numero = Column(String(20), nullable=True, index=True)
    serie = Column(String(10), nullable=True)
    modelo = Column(String(10), nullable=True)

    data_emissao = Column(DateTime, nullable=True)
    data_entrada = Column(DateTime, nullable=True)

    fornecedor_cnpj = Column(String(20), nullable=True, index=True)
    fornecedor_nome = Column(String(180), nullable=True)

    valor_total_produtos = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_total_nota = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_frete = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_seguro = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_desconto = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_outras_despesas = Column(
        Numeric(14, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )

    status = Column(String(20), nullable=False, default="IMPORTADA", server_default="IMPORTADA", index=True)
    xml_original = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    itens = relationship(
        "NotaEntradaItem",
        back_populates="nota_entrada",
        cascade="all, delete-orphan",
        order_by="NotaEntradaItem.item_numero.asc()",
    )

    __table_args__ = (
        UniqueConstraint("empresa_id", "chave_acesso", name="uq_notas_entrada_empresa_chave_acesso"),
    )