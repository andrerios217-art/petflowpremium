from sqlalchemy import Column, Integer, ForeignKey, Date, Time, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Agendamento(Base):
    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)
    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=True)

    data = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)

    status = Column(String(20), default="AGUARDANDO")
    prioridade = Column(String(20), default="NORMAL")

    observacoes = Column(String(500), nullable=True)
    tem_intercorrencia = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    empresa = relationship("Empresa")
    cliente = relationship("Cliente")
    pet = relationship("Pet")
    funcionario = relationship("Funcionario")

    servicos_agendamento = relationship(
        "AgendamentoServico",
        back_populates="agendamento",
        cascade="all, delete-orphan"
    )

    producao = relationship(
        "Producao",
        back_populates="agendamento",
        uselist=False
    )