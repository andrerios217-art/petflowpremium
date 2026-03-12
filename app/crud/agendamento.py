from sqlalchemy.orm import Session, joinedload

from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.pet import Pet
from app.models.servico import Servico

STATUS_AGUARDANDO = "AGUARDANDO"
STATUS_EM_ATENDIMENTO = "EM_ATENDIMENTO"
STATUS_FINALIZADO = "FINALIZADO"
STATUS_FALTA = "FALTA"
STATUS_CANCELADO = "CANCELADO"

STATUS_ALIAS = {
    "AGUARDANDO": STATUS_AGUARDANDO,
    "AGUARDANDO ": STATUS_AGUARDANDO,
    "Aguardando".upper(): STATUS_AGUARDANDO,
    "EM_ATENDIMENTO": STATUS_EM_ATENDIMENTO,
    "EM ATENDIMENTO": STATUS_EM_ATENDIMENTO,
    "Em_atendimento".upper(): STATUS_EM_ATENDIMENTO,
    "FINALIZADO": STATUS_FINALIZADO,
    "Finalizado".upper(): STATUS_FINALIZADO,
    "FALTA": STATUS_FALTA,
    "Falta".upper(): STATUS_FALTA,
    "CANCELADO": STATUS_CANCELADO,
    "Cancelado".upper(): STATUS_CANCELADO,
}

TRANSICOES_VALIDAS = {
    STATUS_AGUARDANDO: {
        STATUS_EM_ATENDIMENTO,
        STATUS_FALTA,
        STATUS_CANCELADO,
    },
    STATUS_EM_ATENDIMENTO: {
        STATUS_FINALIZADO,
    },
    STATUS_FINALIZADO: set(),
    STATUS_FALTA: set(),
    STATUS_CANCELADO: set(),
}


def _normalizar_status(valor: str) -> str:
    texto = (valor or "").strip().upper().replace("-", "_")
    texto = " ".join(texto.split())
    return STATUS_ALIAS.get(texto, texto)


def _query_base(db: Session):
    return (
        db.query(Agendamento)
        .options(
            joinedload(Agendamento.cliente),
            joinedload(Agendamento.pet),
            joinedload(Agendamento.funcionario),
            joinedload(Agendamento.servicos_agendamento).joinedload(AgendamentoServico.servico),
        )
    )


def _serialize_agendamento(ag: Agendamento):
    return {
        "id": ag.id,
        "empresa_id": ag.empresa_id,
        "cliente_id": ag.cliente_id,
        "pet_id": ag.pet_id,
        "funcionario_id": ag.funcionario_id,
        "data": ag.data,
        "hora": ag.hora,
        "status": _normalizar_status(ag.status),
        "prioridade": ag.prioridade,
        "observacoes": ag.observacoes,
        "cliente_nome": ag.cliente.nome if ag.cliente else "-",
        "pet_nome": ag.pet.nome if ag.pet else "-",
        "funcionario_nome": ag.funcionario.nome if ag.funcionario else None,
        "servicos": [
            {
                "id": item.id,
                "servico_id": item.servico_id,
                "nome": item.servico.nome if item.servico else f"Serviço #{item.servico_id}",
                "preco": float(item.preco),
                "tempo_previsto": item.tempo_previsto,
            }
            for item in ag.servicos_agendamento
        ],
    }


def _buscar_agendamento_model(db: Session, agendamento_id: int):
    return (
        _query_base(db)
        .filter(Agendamento.id == agendamento_id)
        .first()
    )


def get_model_by_id(db: Session, agendamento_id: int):
    return _buscar_agendamento_model(db, agendamento_id)


def _validar_servicos_por_porte(db: Session, pet_id: int, servicos_payload: list):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        return False, "Pet não encontrado."

    porte_pet = (pet.porte or "").strip().upper()

    for item in servicos_payload:
        servico = db.query(Servico).filter(Servico.id == item.servico_id).first()

        if not servico:
            return False, f"Serviço {item.servico_id} não encontrado."

        porte_servico = (servico.porte_referencia or "").strip().upper()

        if porte_pet and porte_servico and porte_pet != porte_servico:
            return False, f"O serviço {servico.nome} é para porte {porte_servico}, mas o pet é {porte_pet}."

    return True, None


def list_semana(db: Session, empresa_id: int, data_inicio, data_fim):
    agendamentos = (
        _query_base(db)
        .filter(
            Agendamento.empresa_id == empresa_id,
            Agendamento.data >= data_inicio,
            Agendamento.data <= data_fim,
        )
        .order_by(Agendamento.data, Agendamento.hora)
        .all()
    )

    return [_serialize_agendamento(ag) for ag in agendamentos]


def get_by_id(db: Session, agendamento_id: int):
    ag = _buscar_agendamento_model(db, agendamento_id)

    if not ag:
        return None

    return _serialize_agendamento(ag)


def create(db: Session, data):
    valido, erro = _validar_servicos_por_porte(db, data.pet_id, data.servicos)
    if not valido:
        return {"error": erro}

    agendamento = Agendamento(
        empresa_id=data.empresa_id,
        cliente_id=data.cliente_id,
        pet_id=data.pet_id,
        funcionario_id=data.funcionario_id,
        data=data.data,
        hora=data.hora,
        prioridade=data.prioridade,
        observacoes=data.observacoes,
        status=STATUS_AGUARDANDO,
    )

    db.add(agendamento)
    db.flush()

    for servico in data.servicos:
        db.add(
            AgendamentoServico(
                agendamento_id=agendamento.id,
                servico_id=servico.servico_id,
                preco=servico.preco,
                tempo_previsto=servico.tempo_previsto,
            )
        )

    db.commit()

    ag = _buscar_agendamento_model(db, agendamento.id)
    return _serialize_agendamento(ag)


def update(db: Session, agendamento_id: int, data):
    ag = _buscar_agendamento_model(db, agendamento_id)

    if not ag:
        return None

    status_atual = _normalizar_status(ag.status)
    if status_atual not in {STATUS_AGUARDANDO, STATUS_EM_ATENDIMENTO}:
        return {"error": "Só é possível editar agendamentos com status AGUARDANDO ou EM_ATENDIMENTO."}

    valido, erro = _validar_servicos_por_porte(db, ag.pet_id, data.servicos)
    if not valido:
        return {"error": erro}

    ag.funcionario_id = data.funcionario_id
    ag.data = data.data
    ag.hora = data.hora
    ag.prioridade = data.prioridade
    ag.observacoes = data.observacoes

    (
        db.query(AgendamentoServico)
        .filter(AgendamentoServico.agendamento_id == agendamento_id)
        .delete(synchronize_session=False)
    )

    for servico in data.servicos:
        db.add(
            AgendamentoServico(
                agendamento_id=ag.id,
                servico_id=servico.servico_id,
                preco=servico.preco,
                tempo_previsto=servico.tempo_previsto,
            )
        )

    db.commit()
    db.refresh(ag)

    ag = _buscar_agendamento_model(db, agendamento_id)
    return _serialize_agendamento(ag)


def alterar_status(db: Session, agendamento_id: int, status: str):
    ag = _buscar_agendamento_model(db, agendamento_id)

    if not ag:
        return None

    status_atual = _normalizar_status(ag.status)
    novo_status = _normalizar_status(status)

    permitidos = TRANSICOES_VALIDAS.get(status_atual, set())

    if novo_status not in permitidos:
        return False

    ag.status = novo_status
    db.commit()
    db.refresh(ag)

    ag = _buscar_agendamento_model(db, agendamento_id)
    return _serialize_agendamento(ag)


def delete(db: Session, agendamento_id: int):
    ag = (
        db.query(Agendamento)
        .filter(Agendamento.id == agendamento_id)
        .first()
    )

    if not ag:
        return None

    if _normalizar_status(ag.status) != STATUS_AGUARDANDO:
        return False

    db.delete(ag)
    db.commit()

    return True