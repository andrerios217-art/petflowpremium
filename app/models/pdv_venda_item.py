from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
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

    # Tipo do item:
    # - SERVICE = atendimento/serviço vindo do fluxo operacional
    # - PRODUCT = produto avulso do PDV
    tipo_item = Column(String(20), nullable=False, index=True)

    # Para itens de serviço
    atendimento_clinico_id = Column(
        Integer,
        ForeignKey("atendimentos_clinicos.id"),
        nullable=True,
        unique=True,
        index=True,
    )

    # Para itens de produto
    # Observação:
    # No repositório atual não identifiquei um model/tabela de produto em app/models,
    # então este campo fica sem ForeignKey por enquanto para não quebrar o projeto.
    produto_id = Column(Integer, nullable=True, index=True)

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
            "(tipo_item = 'SERVICE' AND atendimento_clinico_id IS NOT NULL AND produto_id IS NULL) "
            "OR "
            "(tipo_item = 'PRODUCT' AND produto_id IS NOT NULL AND atendimento_clinico_id IS NULL)",
            name="ck_pdv_venda_itens_origem_por_tipo",
        ),
    )

    venda = relationship("PdvVenda", back_populates="itens")
    atendimento_clinico = relationship("AtendimentoClinico")

    @property
    def eh_servico(self) -> bool:
        return self.tipo_item == "SERVICE"

    @property
    def eh_produto(self) -> bool:
        return self.tipo_item == "PRODUCT"

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
        self.atendimento_clinico_id = atendimento_clinico_id
        self.produto_id = None
        self.descricao_snapshot = descricao_snapshot
        self.quantidade = Decimal(str(quantidade))
        self.valor_unitario = Decimal(str(valor_unitario))
        self.desconto_valor = Decimal(str(desconto_valor))
        self.observacao = observacao
        self.recalcular_total()

    def definir_como_produto(
        self,
        produto_id: int,
        descricao_snapshot: str,
        valor_unitario: Decimal | float | str,
        quantidade: Decimal | float | str = Decimal("1.000"),
        desconto_valor: Decimal | float | str = Decimal("0.00"),
        observacao: str | None = None,
    ):
        self.tipo_item = "PRODUCT"
        self.produto_id = produto_id
        self.atendimento_clinico_id = None
        self.descricao_snapshot = descricao_snapshot
        self.quantidade = Decimal(str(quantidade))
        self.valor_unitario = Decimal(str(valor_unitario))
        self.desconto_valor = Decimal(str(desconto_valor))
        self.observacao = observacao
        self.recalcular_total()