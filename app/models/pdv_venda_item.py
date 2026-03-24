from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class PdvVendaItem(Base):
    __tablename__ = "pdv_venda_itens"

    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("pdv_vendas.id"), nullable=False, index=True)

    # Natureza comercial do item no PDV
    # - SERVICE = atendimento/serviço
    # - PRODUCT = item vendido como produto
    tipo_item = Column(String(20), nullable=False, index=True)

    # Origem operacional do item
    # - SERVICE = atendimento/serviço
    # - CATALOG_PRODUCT = produto real do catálogo
    # - PRODUCTION = item vindo do fluxo de produção
    origem_item = Column(String(30), nullable=False, index=True)

    # Para itens de serviço
    atendimento_clinico_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    # Para itens de produto de catálogo
    produto_id = Column(
        Integer,
        ForeignKey("produtos.id"),
        nullable=True,
        index=True,
    )

    # Regra explícita de estoque
    # Não inferir mais apenas por tipo_item
    gera_movimento_estoque = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
        index=True,
    )

    descricao_snapshot = Column(String(255), nullable=False)
    observacao = Column(Text, nullable=True)

    quantidade = Column(Numeric(10, 3), nullable=False, default=Decimal("1.000"))
    valor_unitario = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    desconto_valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    valor_total = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "tipo_item IN ('SERVICE', 'PRODUCT')",
            name="ck_pdv_venda_itens_tipo_item",
        ),
        CheckConstraint(
            "origem_item IN ('SERVICE', 'CATALOG_PRODUCT', 'PRODUCTION')",
            name="ck_pdv_venda_itens_origem_item",
        ),
        CheckConstraint(
            "quantidade > 0",
            name="ck_pdv_venda_itens_quantidade_positive",
        ),
        CheckConstraint(
            "valor_unitario >= 0",
            name="ck_pdv_venda_itens_valor_unitario_non_negative",
        ),
        CheckConstraint(
            "desconto_valor >= 0",
            name="ck_pdv_venda_itens_desconto_non_negative",
        ),
        CheckConstraint(
            "valor_total >= 0",
            name="ck_pdv_venda_itens_valor_total_non_negative",
        ),
        CheckConstraint(
            "("
            "tipo_item = 'SERVICE' "
            "AND origem_item = 'SERVICE' "
            "AND atendimento_clinico_id IS NOT NULL "
            "AND produto_id IS NULL "
            "AND gera_movimento_estoque = false"
            ") "
            "OR "
            "("
            "tipo_item = 'PRODUCT' "
            "AND origem_item = 'CATALOG_PRODUCT' "
            "AND produto_id IS NOT NULL "
            "AND atendimento_clinico_id IS NULL"
            ") "
            "OR "
            "("
            "tipo_item = 'PRODUCT' "
            "AND origem_item = 'PRODUCTION' "
            "AND atendimento_clinico_id IS NULL "
            "AND gera_movimento_estoque = false"
            ")",
            name="ck_pdv_venda_itens_consistencia_origem",
        ),
    )

    venda = relationship("PdvVenda", back_populates="itens")
    atendimento_clinico = relationship("AtendimentoClinico")
    produto = relationship("Produto")

    @property
    def eh_servico(self) -> bool:
        return self.tipo_item == "SERVICE"

    @property
    def eh_produto(self) -> bool:
        return self.tipo_item == "PRODUCT"

    @property
    def eh_produto_catalogo(self) -> bool:
        return self.tipo_item == "PRODUCT" and self.origem_item == "CATALOG_PRODUCT"

    @property
    def eh_item_producao(self) -> bool:
        return self.tipo_item == "PRODUCT" and self.origem_item == "PRODUCTION"

    @property
    def deve_baixar_estoque(self) -> bool:
        return bool(
            self.tipo_item == "PRODUCT"
            and self.origem_item == "CATALOG_PRODUCT"
            and self.gera_movimento_estoque
            and self.produto_id is not None
        )

    def recalcular_total(self):
        quantidade = Decimal(str(self.quantidade or Decimal("0.000")))
        valor_unitario = Decimal(str(self.valor_unitario or Decimal("0.00")))
        desconto = Decimal(str(self.desconto_valor or Decimal("0.00")))

        total = (quantidade * valor_unitario) - desconto
        if total < Decimal("0.00"):
            total = Decimal("0.00")

        self.valor_total = total
        self.updated_at = _agora_utc()

    def definir_como_servico(
        self,
        atendimento_clinico_id: int,
        descricao_snapshot: str,
        valor_unitario: Decimal | float | str,
        quantidade: Decimal | float | str = Decimal("1.000"),
        desconto_valor: Decimal | float | str = Decimal("0.00"),
        observacao: str | None = None,
    ):
        self.tipo_item = "SERVICE"
        self.origem_item = "SERVICE"
        self.atendimento_clinico_id = atendimento_clinico_id
        self.produto_id = None
        self.gera_movimento_estoque = False
        self.descricao_snapshot = descricao_snapshot
        self.quantidade = Decimal(str(quantidade))
        self.valor_unitario = Decimal(str(valor_unitario))
        self.desconto_valor = Decimal(str(desconto_valor))
        self.observacao = observacao
        self.recalcular_total()

    def definir_como_produto_catalogo(
        self,
        produto_id: int,
        descricao_snapshot: str,
        valor_unitario: Decimal | float | str,
        quantidade: Decimal | float | str = Decimal("1.000"),
        desconto_valor: Decimal | float | str = Decimal("0.00"),
        observacao: str | None = None,
        gera_movimento_estoque: bool = True,
    ):
        self.tipo_item = "PRODUCT"
        self.origem_item = "CATALOG_PRODUCT"
        self.produto_id = produto_id
        self.atendimento_clinico_id = None
        self.gera_movimento_estoque = bool(gera_movimento_estoque)
        self.descricao_snapshot = descricao_snapshot
        self.quantidade = Decimal(str(quantidade))
        self.valor_unitario = Decimal(str(valor_unitario))
        self.desconto_valor = Decimal(str(desconto_valor))
        self.observacao = observacao
        self.recalcular_total()

    def definir_como_item_producao(
        self,
        descricao_snapshot: str,
        valor_unitario: Decimal | float | str,
        quantidade: Decimal | float | str = Decimal("1.000"),
        desconto_valor: Decimal | float | str = Decimal("0.00"),
        observacao: str | None = None,
        produto_id: int | None = None,
    ):
        self.tipo_item = "PRODUCT"
        self.origem_item = "PRODUCTION"
        self.produto_id = produto_id
        self.atendimento_clinico_id = None
        self.gera_movimento_estoque = False
        self.descricao_snapshot = descricao_snapshot
        self.quantidade = Decimal(str(quantidade))
        self.valor_unitario = Decimal(str(valor_unitario))
        self.desconto_valor = Decimal(str(desconto_valor))
        self.observacao = observacao
        self.recalcular_total()