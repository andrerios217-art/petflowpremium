from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComissaoConfiguracao(Base):
    __tablename__ = "comissao_configuracoes"
    __table_args__ = (
        UniqueConstraint("empresa_id", name="uq_comissao_configuracao_empresa"),
    )

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    pontos_banho = Column(Integer, nullable=False, default=0)
    pontos_tosa = Column(Integer, nullable=False, default=0)
    pontos_finalizacao = Column(Integer, nullable=False, default=0)

    dias_trabalhados_mes = Column(Integer, nullable=False, default=26)
    responsavel_aprovacao = Column(String(150), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    faixas = relationship(
        "ComissaoFaixa",
        back_populates="configuracao",
        cascade="all, delete-orphan",
        order_by="ComissaoFaixa.ordem.asc()",
    )