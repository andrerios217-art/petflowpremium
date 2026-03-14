from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProducaoHistorico(Base):
    __tablename__ = "producao_historico"

    id = Column(Integer, primary_key=True, index=True)

    producao_id = Column(Integer, ForeignKey("producao.id"), nullable=False, index=True)
    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=True, index=True)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=True, index=True)
    servico_id = Column(Integer, ForeignKey("servicos.id"), nullable=True, index=True)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=True, index=True)

    etapa = Column(String(50), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="INICIADO")

    iniciado_em = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finalizado_em = Column(DateTime(timezone=True), nullable=True)

    tempo_gasto_minutos = Column(Integer, nullable=True)

    intercorrencia = Column(Text, nullable=True)
    observacoes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    producao = relationship("Producao", back_populates="historicos")
    agendamento = relationship("Agendamento")
    pet = relationship("Pet")
    servico = relationship("Servico")
    funcionario = relationship("Funcionario")