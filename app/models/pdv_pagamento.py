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


class PdvPagamento(Base):
    __tablename__ = "pdv_pagamentos"

    id = Column(Integer, primary_key=True, index=True)

    # MVP: 1 pagamento por venda
    venda_id = Column(
        Integer,
        ForeignKey("pdv_vendas.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # MVP:
    # armazenamos a forma como texto para não depender ainda
    # de uma tabela de formas de pagamento
    #
    # exemplos:
    # - DINHEIRO
    # - PIX
    # - CARTAO_DEBITO
    # - CARTAO_CREDITO
    forma_pagamento = Column(String(30), nullable=False, index=True)

    valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    # NOVO:
    # quantidade de parcelas apenas para controle interno.
    # Para dinheiro, pix e débito, deve ficar 1.
    quantidade_parcelas = Column(Integer, nullable=False, default=1)

    # Status:
    # - RECEBIDO
    # - CANCELADO
    status = Column(String(20), nullable=False, default="RECEBIDO", index=True)

    referencia = Column(String(100), nullable=True)
    observacoes = Column(Text, nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)

    recebido_em = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "forma_pagamento IN ('DINHEIRO', 'PIX', 'CARTAO_DEBITO', 'CARTAO_CREDITO')",
            name="ck_pdv_pagamentos_forma_pagamento",
        ),
        CheckConstraint(
            "status IN ('RECEBIDO', 'CANCELADO')",
            name="ck_pdv_pagamentos_status",
        ),
        CheckConstraint(
            "valor >= 0",
            name="ck_pdv_pagamentos_valor_non_negative",
        ),
        CheckConstraint(
            "quantidade_parcelas >= 1 AND quantidade_parcelas <= 12",
            name="ck_pdv_pagamentos_quantidade_parcelas_range",
        ),
        CheckConstraint(
            "("
            "forma_pagamento = 'CARTAO_CREDITO' "
            "OR quantidade_parcelas = 1"
            ")",
            name="ck_pdv_pagamentos_parcelas_somente_credito",
        ),
    )

    venda = relationship("PdvVenda", back_populates="pagamentos")
    usuario = relationship("Usuario")

    @property
    def eh_dinheiro(self) -> bool:
        return self.forma_pagamento == "DINHEIRO"

    @property
    def eh_pix(self) -> bool:
        return self.forma_pagamento == "PIX"

    @property
    def eh_cartao(self) -> bool:
        return self.forma_pagamento in ("CARTAO_DEBITO", "CARTAO_CREDITO")

    @property
    def eh_cartao_credito(self) -> bool:
        return self.forma_pagamento == "CARTAO_CREDITO"

    def cancelar(self, observacoes: str | None = None):
        self.status = "CANCELADO"
        if observacoes:
            self.observacoes = observacoes
        self.updated_at = _agora_utc()