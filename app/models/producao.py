from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Producao(Base):
    __tablename__ = "producao"

    id = Column(Integer, primary_key=True, index=True)

    agendamento_id = Column(
        Integer,
        ForeignKey("agendamentos.id"),
        nullable=False,
        unique=True,
        index=True
    )

    coluna = Column(String(30), nullable=False, default="ORDEM")
    etapa_status = Column(String(20), nullable=False, default="AGUARDANDO")
    prioridade = Column(String(20), nullable=False, default="NORMAL")

    funcionario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=True)

    secagem_tempo = Column(Integer, nullable=True)
    secagem_inicio = Column(DateTime(timezone=True), nullable=True)

    observacoes = Column(Text, nullable=True)
    intercorrencias = Column(Text, nullable=True)

    finalizado = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    agendamento = relationship("Agendamento", back_populates="producao")
    funcionario = relationship("Funcionario")