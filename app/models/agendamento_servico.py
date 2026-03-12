from sqlalchemy import Column, Integer, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgendamentoServico(Base):
    __tablename__ = "agendamento_servicos"

    id = Column(Integer, primary_key=True, index=True)

    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=False)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=False)

    preco = Column(Numeric(10, 2), nullable=False)
    tempo_previsto = Column(Integer, nullable=False)

    agendamento = relationship("Agendamento", back_populates="servicos_agendamento")
    servico = relationship("Servico")