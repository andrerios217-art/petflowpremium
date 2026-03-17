from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    String,
    Date,
    DateTime,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComissaoLancamento(Base):
    __tablename__ = "comissao_lancamentos"
    __table_args__ = (
        UniqueConstraint(
            "producao_id",
            "etapa",
            name="uq_comissao_lancamento_producao_etapa",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    configuracao_id = Column(
        Integer,
        ForeignKey("comissao_configuracoes.id"),
        nullable=True,
        index=True,
    )

    producao_id = Column(Integer, ForeignKey("producao.id"), nullable=False, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=False, index=True)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=False, index=True)

    etapa = Column(String(50), nullable=False, index=True)
    pontos = Column(Integer, nullable=False, default=0)

    status = Column(String(30), nullable=False, default="CAPTURADO", index=True)
    competencia = Column(Date, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    configuracao = relationship("ComissaoConfiguracao")
    producao = relationship("Producao")
    agendamento = relationship("Agendamento")
    funcionario = relationship("Funcionario")