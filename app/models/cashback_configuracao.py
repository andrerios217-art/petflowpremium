from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class CashbackConfiguracao(Base):
    __tablename__ = "cashback_configuracoes"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    ativo = Column(Boolean, nullable=False, default=False, server_default="false")
    percentual_cashback = Column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    valor_minimo_venda = Column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0",
    )
    dias_validade = Column(Integer, nullable=True)
    permite_uso_no_pdv = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    acumula_com_desconto = Column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            name="uq_cashback_configuracoes_empresa",
        ),
        CheckConstraint(
            "percentual_cashback >= 0 AND percentual_cashback <= 100",
            name="ck_cashback_configuracoes_percentual_range",
        ),
        CheckConstraint(
            "valor_minimo_venda >= 0",
            name="ck_cashback_configuracoes_valor_minimo_non_negative",
        ),
        CheckConstraint(
            "dias_validade IS NULL OR dias_validade >= 0",
            name="ck_cashback_configuracoes_dias_validade_non_negative",
        ),
    )

    empresa = relationship("Empresa")

    @property
    def esta_ativa(self) -> bool:
        return bool(self.ativo)

    def ativar(self):
        self.ativo = True
        self.updated_at = datetime.utcnow()

    def desativar(self):
        self.ativo = False
        self.updated_at = datetime.utcnow()

    def definir_percentual(self, valor: Decimal | float | str):
        valor_decimal = Decimal(str(valor))
        if valor_decimal < Decimal("0.00") or valor_decimal > Decimal("100.00"):
            raise ValueError("O percentual de cashback deve estar entre 0 e 100.")
        self.percentual_cashback = valor_decimal
        self.updated_at = datetime.utcnow()

    def definir_valor_minimo_venda(self, valor: Decimal | float | str):
        valor_decimal = Decimal(str(valor))
        if valor_decimal < Decimal("0.00"):
            raise ValueError("O valor mínimo da venda não pode ser negativo.")
        self.valor_minimo_venda = valor_decimal
        self.updated_at = datetime.utcnow()

    def definir_dias_validade(self, dias: int | None):
        if dias is not None and int(dias) < 0:
            raise ValueError("Os dias de validade não podem ser negativos.")
        self.dias_validade = int(dias) if dias is not None else None
        self.updated_at = datetime.utcnow()