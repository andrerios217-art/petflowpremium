from datetime import datetime

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


class CashbackLancamento(Base):
    __tablename__ = "cashback_lancamentos"

    TIPO_CREDITO = "CREDITO"
    TIPO_DEBITO = "DEBITO"
    TIPO_ESTORNO = "ESTORNO"
    TIPO_EXPIRACAO = "EXPIRACAO"
    TIPO_AJUSTE = "AJUSTE"

    ORIGEM_PDV_VENDA = "PDV_VENDA"
    ORIGEM_PDV_USO = "PDV_USO"
    ORIGEM_CANCELAMENTO = "CANCELAMENTO"
    ORIGEM_EXPIRACAO = "EXPIRACAO"
    ORIGEM_MANUAL = "MANUAL"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    venda_id = Column(Integer, ForeignKey("pdv_vendas.id"), nullable=True, index=True)

    tipo = Column(String(20), nullable=False, index=True)
    origem = Column(String(30), nullable=False, index=True)

    valor = Column(Numeric(10, 2), nullable=False)
    saldo_apos = Column(Numeric(10, 2), nullable=False)

    expira_em = Column(DateTime, nullable=True, index=True)
    observacao = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint(
            "valor >= 0",
            name="ck_cashback_lancamentos_valor_non_negative",
        ),
        CheckConstraint(
            "saldo_apos >= 0",
            name="ck_cashback_lancamentos_saldo_apos_non_negative",
        ),
        CheckConstraint(
            "tipo IN ('CREDITO', 'DEBITO', 'ESTORNO', 'EXPIRACAO', 'AJUSTE')",
            name="ck_cashback_lancamentos_tipo_valid",
        ),
        CheckConstraint(
            "origem IN ('PDV_VENDA', 'PDV_USO', 'CANCELAMENTO', 'EXPIRACAO', 'MANUAL')",
            name="ck_cashback_lancamentos_origem_valid",
        ),
    )

    empresa = relationship("Empresa")
    cliente = relationship("Cliente")
    venda = relationship("PdvVenda")

    @property
    def is_credito(self) -> bool:
        return self.tipo == self.TIPO_CREDITO

    @property
    def is_debito(self) -> bool:
        return self.tipo == self.TIPO_DEBITO

    @property
    def is_estorno(self) -> bool:
        return self.tipo == self.TIPO_ESTORNO

    @property
    def is_expiracao(self) -> bool:
        return self.tipo == self.TIPO_EXPIRACAO

    @property
    def is_ajuste(self) -> bool:
        return self.tipo == self.TIPO_AJUSTE