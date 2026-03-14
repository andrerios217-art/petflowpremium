from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.cliente import Cliente
from app.models.pet import Pet
from app.models.producao import Producao
from app.models.producao_historico import ProducaoHistorico


def _payload_to_dict(payload) -> dict:
    if payload is None:
        return {}

    if isinstance(payload, dict):
        return payload

    if hasattr(payload, "model_dump"):
        return payload.model_dump(exclude_unset=True)

    if hasattr(payload, "dict"):
        return payload.dict(exclude_unset=True)

    return {}


def list_all(db: Session, q: Optional[str] = None):
    query = (
        db.query(Pet)
        .order_by(Pet.nome.asc(), Pet.id.asc())
    )

    if q:
        termo = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Pet.nome.ilike(termo),
                Pet.raca.ilike(termo),
                Pet.porte.ilike(termo),
                Pet.sexo.ilike(termo),
                Pet.temperamento.ilike(termo),
            )
        )

    return query.all()


def get_by_id(db: Session, pet_id: int):
    return db.query(Pet).filter(Pet.id == pet_id).first()


def create(db: Session, payload):
    data = _payload_to_dict(payload)

    pet = Pet(
        empresa_id=data["empresa_id"],
        cliente_id=data["cliente_id"],
        nome=data["nome"],
        nascimento=data.get("nascimento"),
        raca=data.get("raca"),
        sexo=data.get("sexo"),
        temperamento=data.get("temperamento"),
        peso=data.get("peso"),
        porte=data.get("porte"),
        observacoes=data.get("observacoes"),
        pode_perfume=data.get("pode_perfume", True),
        pode_acessorio=data.get("pode_acessorio", True),
        castrado=data.get("castrado", False),
        foto=data.get("foto"),
        ativo=data.get("ativo", True),
    )

    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def update(db: Session, pet: Pet, payload):
    data = _payload_to_dict(payload)

    campos_permitidos = {
        "empresa_id",
        "cliente_id",
        "nome",
        "nascimento",
        "raca",
        "sexo",
        "temperamento",
        "peso",
        "porte",
        "observacoes",
        "pode_perfume",
        "pode_acessorio",
        "castrado",
        "foto",
        "ativo",
    }

    for campo, valor in data.items():
        if campo in campos_permitidos:
            setattr(pet, campo, valor)

    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def toggle_ativo(db: Session, pet: Pet):
    pet.ativo = not pet.ativo
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def _obter_nome_generico(obj) -> Optional[str]:
    if not obj:
        return None

    for campo in [
        "nome",
        "nome_completo",
        "descricao",
        "titulo",
        "razao_social",
        "fantasia",
    ]:
        valor = getattr(obj, campo, None)
        if valor:
            return str(valor)

    return str(obj.id) if getattr(obj, "id", None) else None


def _texto_para_lista(valor: Optional[str]) -> List[str]:
    if not valor:
        return []

    texto = str(valor).replace("\r", "\n")
    separadores = ["\n", ";", ",", "|"]

    itens = [texto]
    for separador in separadores:
        novos_itens = []
        for item in itens:
            novos_itens.extend(item.split(separador))
        itens = novos_itens

    return [item.strip() for item in itens if item and item.strip()]


def _calcular_tempo_total_atendimento_minutos(
    producao: Optional[Producao],
    timeline: List[dict]
) -> Optional[int]:
    tempos = [
        item.get("tempo_gasto_minutos")
        for item in timeline
        if item.get("tempo_gasto_minutos")
    ]
    if tempos:
        return int(sum(tempos))

    datas_inicio = [
        item.get("iniciado_em")
        for item in timeline
        if item.get("iniciado_em")
    ]
    datas_fim = [
        item.get("finalizado_em")
        for item in timeline
        if item.get("finalizado_em")
    ]

    if datas_inicio and datas_fim:
        inicio = min(datas_inicio)
        fim = max(datas_fim)
        if isinstance(inicio, datetime) and isinstance(fim, datetime) and fim >= inicio:
            return int((fim - inicio).total_seconds() // 60)

    if producao and producao.secagem_tempo:
        return int(producao.secagem_tempo)

    return None


def obter_historico_pet(db: Session, pet_id: int):
    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        return None

    cliente = db.query(Cliente).filter(Cliente.id == pet.cliente_id).first()
    tutor_nome = _obter_nome_generico(cliente)

    agendamentos = (
        db.query(Agendamento)
        .options(
            joinedload(Agendamento.funcionario),
            selectinload(Agendamento.servicos_agendamento).joinedload(AgendamentoServico.servico),
            joinedload(Agendamento.producao)
            .selectinload(Producao.historicos)
            .joinedload(ProducaoHistorico.funcionario),
        )
        .filter(Agendamento.pet_id == pet_id)
        .order_by(Agendamento.data.desc(), Agendamento.hora.desc(), Agendamento.id.desc())
        .all()
    )

    atendimentos = []

    for agendamento in agendamentos:
        producao = agendamento.producao

        servicos_executados = []
        for item in agendamento.servicos_agendamento or []:
            nome_servico = _obter_nome_generico(getattr(item, "servico", None))
            if nome_servico:
                servicos_executados.append(nome_servico)

        timeline = []
        if producao and producao.historicos:
            for historico in producao.historicos:
                timeline.append(
                    {
                        "etapa": historico.etapa,
                        "status": historico.status,
                        "iniciado_em": historico.iniciado_em,
                        "finalizado_em": historico.finalizado_em,
                        "funcionario": _obter_nome_generico(historico.funcionario),
                        "intercorrencia": historico.intercorrencia,
                        "observacoes": historico.observacoes,
                        "tempo_gasto_minutos": historico.tempo_gasto_minutos,
                    }
                )

        intercorrencias = []
        if producao and producao.intercorrencias:
            intercorrencias.extend(_texto_para_lista(producao.intercorrencias))

        for item_timeline in timeline:
            if item_timeline.get("intercorrencia"):
                intercorrencias.extend(_texto_para_lista(item_timeline.get("intercorrencia")))

        intercorrencias_unicas = []
        vistos = set()
        for item in intercorrencias:
            chave = item.strip().lower()
            if chave and chave not in vistos:
                vistos.add(chave)
                intercorrencias_unicas.append(item.strip())

        funcionario_responsavel = _obter_nome_generico(agendamento.funcionario)
        if not funcionario_responsavel and producao and producao.funcionario:
            funcionario_responsavel = _obter_nome_generico(producao.funcionario)

        tempo_total = _calcular_tempo_total_atendimento_minutos(producao, timeline)

        atendimentos.append(
            {
                "agendamento_id": agendamento.id,
                "data": agendamento.data,
                "hora": agendamento.hora,
                "servicos_executados": servicos_executados,
                "funcionario_responsavel": funcionario_responsavel,
                "status_final": agendamento.status,
                "teve_intercorrencia": bool(
                    agendamento.tem_intercorrencia
                    or (producao and producao.intercorrencias)
                    or intercorrencias_unicas
                ),
                "intercorrencias": intercorrencias_unicas,
                "observacoes_gerais": agendamento.observacoes,
                "observacoes_producao": producao.observacoes if producao else None,
                "tempo_total_atendimento_minutos": tempo_total,
                "timeline": timeline,
            }
        )

    return {
        "pet": {
            "id": pet.id,
            "nome": pet.nome,
            "tutor": tutor_nome,
            "raca": pet.raca,
            "porte": pet.porte,
            "peso": pet.peso,
            "sexo": pet.sexo,
            "temperamento": pet.temperamento,
            "observacoes_cadastrais": pet.observacoes,
            "nascimento": pet.nascimento,
            "pode_perfume": pet.pode_perfume,
            "pode_acessorio": pet.pode_acessorio,
            "castrado": pet.castrado,
            "foto": pet.foto,
            "ativo": pet.ativo,
        },
        "atendimentos": atendimentos,
    }