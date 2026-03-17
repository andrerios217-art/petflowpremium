from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComissaoFaixa(Base):
    __tablename__ = "comissao_faixas"

    id = Column(Integer, primary_key=True, index=True)
    configuracao_id = Column(
        Integer,
        ForeignKey("comissao_configuracoes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ordem = Column(Integer, nullable=False, default=1)
    pontos_min = Column(Integer, nullable=False)
    pontos_max = Column(Integer, nullable=True)
    valor_reais = Column(Numeric(10, 2), nullable=False, default=0)
    ativo = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    configuracao = relationship("ComissaoConfiguracao", back_populates="faixas")