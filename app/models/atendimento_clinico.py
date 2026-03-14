from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.core.database import Base


class AtendimentoClinico(Base):
    __tablename__ = "atendimentos_clinicos"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)

    agendamento_id = Column(Integer, ForeignKey("agendamentos.id"), nullable=True)

    pet_id = Column(Integer, ForeignKey("pets.id"), nullable=False)

    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    veterinario_id = Column(Integer, ForeignKey("funcionarios.id"), nullable=True)

    status = Column(String(20), default="EM_ATENDIMENTO")

    data_inicio = Column(DateTime, default=datetime.utcnow)

    data_fim = Column(DateTime, nullable=True)

    observacoes_recepcao = Column(Text, nullable=True)

    observacoes_clinicas = Column(Text, nullable=True)

    enviado_pdv = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    updated_at = Column(DateTime, default=datetime.utcnow)

    # RELACIONAMENTOS

    empresa = relationship("Empresa")

    agendamento = relationship("Agendamento")

    pet = relationship("Pet")

    cliente = relationship("Cliente")

    veterinario = relationship("Funcionario")

    anamnese = relationship(
        "PetAnamnese",
        back_populates="atendimento",
        uselist=False,
        cascade="all, delete-orphan"
    )

    prontuario = relationship(
        "PetProntuario",
        back_populates="atendimento",
        uselist=False,
        cascade="all, delete-orphan"
    )

    itens = relationship(
        "AtendimentoClinicoItem",
        back_populates="atendimento",
        cascade="all, delete-orphan"
    )

    medicacoes = relationship(
        "PetMedicacao",
        back_populates="atendimento",
        cascade="all, delete-orphan"
    )

    exames = relationship(
        "PetExame",
        back_populates="atendimento",
        cascade="all, delete-orphan"
    )

    receitas = relationship(
        "PetReceita",
        back_populates="atendimento",
        cascade="all, delete-orphan"
    )

    vacinas = relationship(
        "PetVacina",
        back_populates="atendimento",
        cascade="all, delete-orphan"
    )

    def finalizar(self):
        self.status = "FINALIZADO"
        self.data_fim = datetime.utcnow()

    def marcar_enviado_pdv(self):
        self.enviado_pdv = True