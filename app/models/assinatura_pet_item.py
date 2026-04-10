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
)
from sqlalchemy.orm import relationship

from app.core.database import Base


def _agora_utc():
    return datetime.now(timezone.utc)


class AssinaturaPetItem(Base):
    __tablename__ = "assinaturas_pet_itens"

    id = Column(Integer, primary_key=True, index=True)

    assinatura_id = Column(
        Integer,
        ForeignKey("assinaturas_pet.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False, index=True)

    nome_servico = Column(String(150), nullable=False)

    quantidade_contratada = Column(Integer, nullable=False, default=1)
    quantidade_consumida = Column(Integer, nullable=False, default=0)

    preco_unitario_base = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    percentual_desconto = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    valor_desconto_unitario = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    preco_unitario_final = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    ativo = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "quantidade_contratada >= 1",
            name="ck_assinaturas_pet_itens_qtd_contratada_min_1",
        ),
        CheckConstraint(
            "quantidade_consumida >= 0",
            name="ck_assinaturas_pet_itens_qtd_consumida_non_negative",
        ),
        CheckConstraint(
            "quantidade_consumida <= quantidade_contratada",
            name="ck_assinaturas_pet_itens_qtd_consumida_lte_contratada",
        ),
        CheckConstraint(
            "preco_unitario_base >= 0",
            name="ck_assinaturas_pet_itens_preco_base_non_negative",
        ),
        CheckConstraint(
            "percentual_desconto >= 0 AND percentual_desconto <= 100",
            name="ck_assinaturas_pet_itens_percentual_desconto_0_100",
        ),
        CheckConstraint(
            "valor_desconto_unitario >= 0",
            name="ck_assinaturas_pet_itens_valor_desconto_unitario_non_negative",
        ),
        CheckConstraint(
            "preco_unitario_final >= 0",
            name="ck_assinaturas_pet_itens_preco_final_non_negative",
        ),
    )

    assinatura = relationship("AssinaturaPet", back_populates="itens")
    empresa = relationship("Empresa")
    servico = relationship("Servico")

    @property
    def quantidade_disponivel(self) -> int:
        restante = (self.quantidade_contratada or 0) - (self.quantidade_consumida or 0)
        return max(restante, 0)

    @property
    def subtotal_bruto(self) -> Decimal:
        return Decimal(str(self.quantidade_contratada or 0)) * Decimal(
            str(self.preco_unitario_base or Decimal("0.00"))
        )

    @property
    def subtotal_desconto(self) -> Decimal:
        return Decimal(str(self.quantidade_contratada or 0)) * Decimal(
            str(self.valor_desconto_unitario or Decimal("0.00"))
        )

    @property
    def subtotal_final(self) -> Decimal:
        return Decimal(str(self.quantidade_contratada or 0)) * Decimal(
            str(self.preco_unitario_final or Decimal("0.00"))
        )

    def recalcular_precos(self):
        preco_base = Decimal(str(self.preco_unitario_base or Decimal("0.00")))
        percentual = Decimal(str(self.percentual_desconto or Decimal("0.00")))

        desconto_unitario = (preco_base * percentual) / Decimal("100.00")
        preco_final = preco_base - desconto_unitario

        if desconto_unitario < Decimal("0.00"):
            desconto_unitario = Decimal("0.00")

        if preco_final < Decimal("0.00"):
            preco_final = Decimal("0.00")

        self.valor_desconto_unitario = desconto_unitario.quantize(Decimal("0.01"))
        self.preco_unitario_final = preco_final.quantize(Decimal("0.01"))
        self.updated_at = _agora_utc()

    def consumir(self, quantidade: int = 1):
        if quantidade <= 0:
            raise ValueError("A quantidade consumida deve ser maior que zero.")

        novo_total = (self.quantidade_consumida or 0) + quantidade
        if novo_total > (self.quantidade_contratada or 0):
            raise ValueError("Consumo maior que a quantidade contratada do item.")

        self.quantidade_consumida = novo_total
        self.updated_at = _agora_utc()

    def estornar_consumo(self, quantidade: int = 1):
        if quantidade <= 0:
            raise ValueError("A quantidade a estornar deve ser maior que zero.")

        novo_total = (self.quantidade_consumida or 0) - quantidade
        if novo_total < 0:
            raise ValueError("Estorno inválido: consumo ficaria negativo.")

        self.quantidade_consumida = novo_total
        self.updated_at = _agora_utc()