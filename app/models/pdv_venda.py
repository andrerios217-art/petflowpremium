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


class PdvVenda(Base):
    __tablename__ = "pdv_vendas"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    # Toda venda pertence a uma sessão de caixa
    caixa_sessao_id = Column(
        Integer,
        ForeignKey("caixa_sessoes.id"),
        nullable=False,
        index=True,
    )

    # Modo da venda:
    # - REGISTERED_CLIENT = cliente cadastrado
    # - WALK_IN = venda balcão
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True, index=True)
    modo_cliente = Column(String(30), nullable=False, default="WALK_IN", index=True)

    # Número amigável para operação/consulta
    numero_venda = Column(String(30), nullable=True, index=True)

    # Snapshots para venda balcão ou histórico da venda
    nome_cliente_snapshot = Column(String(150), nullable=True)
    telefone_cliente_snapshot = Column(String(20), nullable=True)

    # Origem da venda:
    # - PRODUCT_ONLY
    # - SERVICE_ONLY
    # - MIXED
    origem = Column(String(30), nullable=False, default="PRODUCT_ONLY", index=True)

    # Status da venda:
    # - ABERTA
    # - FECHADA
    # - CANCELADA
    status = Column(String(20), nullable=False, default="ABERTA", index=True)

    subtotal = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    desconto_valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    acrescimo_valor = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    valor_total = Column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    observacoes = Column(Text, nullable=True)

    usuario_abertura_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    usuario_fechamento_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)
    usuario_cancelamento_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True, index=True)

    aberta_em = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    fechada_em = Column(DateTime(timezone=True), nullable=True)
    cancelada_em = Column(DateTime(timezone=True), nullable=True)

    motivo_cancelamento = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=_agora_utc)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=_agora_utc,
        onupdate=_agora_utc,
    )

    __table_args__ = (
        CheckConstraint(
            "modo_cliente IN ('REGISTERED_CLIENT', 'WALK_IN')",
            name="ck_pdv_vendas_modo_cliente",
        ),
        CheckConstraint(
            "origem IN ('PRODUCT_ONLY', 'SERVICE_ONLY', 'MIXED')",
            name="ck_pdv_vendas_origem",
        ),
        CheckConstraint(
            "status IN ('ABERTA', 'FECHADA', 'CANCELADA')",
            name="ck_pdv_vendas_status",
        ),
        CheckConstraint("subtotal >= 0", name="ck_pdv_vendas_subtotal_non_negative"),
        CheckConstraint(
            "desconto_valor >= 0", name="ck_pdv_vendas_desconto_non_negative"
        ),
        CheckConstraint(
            "acrescimo_valor >= 0", name="ck_pdv_vendas_acrescimo_non_negative"
        ),
        CheckConstraint("valor_total >= 0", name="ck_pdv_vendas_total_non_negative"),
        CheckConstraint(
            "(modo_cliente = 'REGISTERED_CLIENT' AND cliente_id IS NOT NULL) "
            "OR "
            "(modo_cliente = 'WALK_IN' AND cliente_id IS NULL)",
            name="ck_pdv_vendas_cliente_por_modo",
        ),
    )

    empresa = relationship("Empresa")
    caixa_sessao = relationship("CaixaSessao", back_populates="vendas")
    cliente = relationship("Cliente")

    usuario_abertura = relationship("Usuario", foreign_keys=[usuario_abertura_id])
    usuario_fechamento = relationship("Usuario", foreign_keys=[usuario_fechamento_id])
    usuario_cancelamento = relationship("Usuario", foreign_keys=[usuario_cancelamento_id])

    itens = relationship(
        "PdvVendaItem",
        back_populates="venda",
        cascade="all, delete-orphan",
    )
    pagamentos = relationship(
        "PdvPagamento",
        back_populates="venda",
        cascade="all, delete-orphan",
    )

    @property
    def eh_balcao(self) -> bool:
        return self.modo_cliente == "WALK_IN"

    @property
    def possui_cliente_cadastrado(self) -> bool:
        return self.modo_cliente == "REGISTERED_CLIENT" and self.cliente_id is not None

    @property
    def pode_receber_atendimentos(self) -> bool:
        return self.modo_cliente == "REGISTERED_CLIENT"

    @property
    def esta_aberta(self) -> bool:
        return self.status == "ABERTA"

    @property
    def esta_fechada(self) -> bool:
        return self.status == "FECHADA"

    @property
    def esta_cancelada(self) -> bool:
        return self.status == "CANCELADA"

    def definir_cliente_cadastrado(self, cliente_id: int):
        self.modo_cliente = "REGISTERED_CLIENT"
        self.cliente_id = cliente_id
        self.updated_at = _agora_utc()

    def definir_como_balcao(
        self,
        nome_cliente_snapshot: str | None = None,
        telefone_cliente_snapshot: str | None = None,
    ):
        self.modo_cliente = "WALK_IN"
        self.cliente_id = None
        self.nome_cliente_snapshot = nome_cliente_snapshot
        self.telefone_cliente_snapshot = telefone_cliente_snapshot
        self.updated_at = _agora_utc()

    def recalcular_totais(self):
        subtotal = Decimal("0.00")

        for item in self.itens or []:
            valor_item = item.valor_total if item.valor_total is not None else Decimal("0.00")
            subtotal += Decimal(str(valor_item))

        self.subtotal = subtotal

        desconto = Decimal(str(self.desconto_valor or Decimal("0.00")))
        acrescimo = Decimal(str(self.acrescimo_valor or Decimal("0.00")))

        total = subtotal - desconto + acrescimo
        if total < Decimal("0.00"):
            total = Decimal("0.00")

        self.valor_total = total
        self.updated_at = _agora_utc()

        self._atualizar_origem()

    def _atualizar_origem(self):
        possui_produto = False
        possui_servico = False

        for item in self.itens or []:
            if item.tipo_item == "PRODUCT":
                possui_produto = True
            elif item.tipo_item == "SERVICE":
                possui_servico = True

        if possui_produto and possui_servico:
            self.origem = "MIXED"
        elif possui_servico:
            self.origem = "SERVICE_ONLY"
        else:
            self.origem = "PRODUCT_ONLY"

    def fechar(self, usuario_fechamento_id: int | None = None):
        self.status = "FECHADA"
        self.usuario_fechamento_id = usuario_fechamento_id
        self.fechada_em = _agora_utc()
        self.updated_at = _agora_utc()

    def cancelar(
        self,
        motivo_cancelamento: str | None = None,
        usuario_cancelamento_id: int | None = None,
    ):
        self.status = "CANCELADA"
        self.motivo_cancelamento = motivo_cancelamento
        self.usuario_cancelamento_id = usuario_cancelamento_id
        self.cancelada_em = _agora_utc()
        self.updated_at = _agora_utc()