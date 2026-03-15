from datetime import datetime
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.atendimento_clinico import AtendimentoClinico
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


def _normalizar_lista_unica(itens: List[str]) -> List[str]:
    resultado = []
    vistos = set()

    for item in itens:
        texto = str(item or "").strip()
        chave = texto.lower()
        if texto and chave not in vistos:
            vistos.add(chave)
            resultado.append(texto)

    return resultado


def _ordenar_timeline_item(item: dict):
    return (
        item.get("iniciado_em")
        or item.get("finalizado_em")
        or datetime.min,
        item.get("agendamento_id") or 0,
        item.get("etapa") or "",
    )


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
            joinedload(Agendamento.producao).joinedload(Producao.funcionario),
            joinedload(Agendamento.producao)
            .selectinload(Producao.historicos)
            .joinedload(ProducaoHistorico.funcionario),
        )
        .filter(Agendamento.pet_id == pet_id)
        .order_by(Agendamento.data.desc(), Agendamento.hora.desc(), Agendamento.id.desc())
        .all()
    )

    atendimentos = []
    timeline_producao = []
    intercorrencias_grooming = []

    for agendamento in agendamentos:
        producao = agendamento.producao

        servicos_executados = []
        for item in agendamento.servicos_agendamento or []:
            nome_servico = _obter_nome_generico(getattr(item, "servico", None))
            if nome_servico:
                servicos_executados.append(nome_servico)

        timeline = []
        if producao and producao.historicos:
            historicos_ordenados = sorted(
                producao.historicos,
                key=lambda h: (
                    h.iniciado_em or h.finalizado_em or datetime.min,
                    h.id or 0,
                )
            )
            for historico in historicos_ordenados:
                timeline_item = {
                    "etapa": historico.etapa,
                    "status": historico.status,
                    "iniciado_em": historico.iniciado_em,
                    "finalizado_em": historico.finalizado_em,
                    "funcionario": _obter_nome_generico(historico.funcionario),
                    "intercorrencia": historico.intercorrencia,
                    "observacoes": historico.observacoes,
                    "tempo_gasto_minutos": historico.tempo_gasto_minutos,
                }
                timeline.append(timeline_item)
                timeline_producao.append(
                    {
                        "agendamento_id": agendamento.id,
                        "data": agendamento.data,
                        "hora": agendamento.hora,
                        **timeline_item,
                    }
                )

        intercorrencias = []
        if producao and producao.intercorrencias:
            intercorrencias.extend(_texto_para_lista(producao.intercorrencias))

        for item_timeline in timeline:
            if item_timeline.get("intercorrencia"):
                intercorrencias.extend(_texto_para_lista(item_timeline.get("intercorrencia")))

        intercorrencias_unicas = _normalizar_lista_unica(intercorrencias)

        funcionario_responsavel = _obter_nome_generico(agendamento.funcionario)
        if not funcionario_responsavel and producao and producao.funcionario:
            funcionario_responsavel = _obter_nome_generico(producao.funcionario)

        for descricao in intercorrencias_unicas:
            intercorrencias_grooming.append(
                {
                    "agendamento_id": agendamento.id,
                    "data": agendamento.data,
                    "hora": agendamento.hora,
                    "descricao": descricao,
                    "funcionario": funcionario_responsavel,
                    "origem": "GROOMING",
                }
            )

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

    consultas = (
        db.query(AtendimentoClinico)
        .options(
            joinedload(AtendimentoClinico.veterinario),
            joinedload(AtendimentoClinico.anamnese),
            joinedload(AtendimentoClinico.prontuario),
            joinedload(AtendimentoClinico.agendamento)
            .selectinload(Agendamento.servicos_agendamento)
            .joinedload(AgendamentoServico.servico),
        )
        .filter(AtendimentoClinico.pet_id == pet_id)
        .order_by(AtendimentoClinico.data_inicio.desc(), AtendimentoClinico.id.desc())
        .all()
    )

    consultas_veterinarias = []

    for consulta in consultas:
        servicos_consulta = []
        if consulta.agendamento and consulta.agendamento.servicos_agendamento:
            for item in consulta.agendamento.servicos_agendamento:
                nome_servico = _obter_nome_generico(getattr(item, "servico", None))
                if nome_servico:
                    servicos_consulta.append(nome_servico)

        anamnese = consulta.anamnese
        prontuario = consulta.prontuario

        consultas_veterinarias.append(
            {
                "atendimento_id": consulta.id,
                "agendamento_id": consulta.agendamento_id,
                "data_inicio": consulta.data_inicio,
                "data_fim": consulta.data_fim,
                "status": consulta.status,
                "veterinario": _obter_nome_generico(consulta.veterinario),
                "observacoes_recepcao": consulta.observacoes_recepcao,
                "observacoes_clinicas": consulta.observacoes_clinicas,
                "servicos_executados": _normalizar_lista_unica(servicos_consulta),
                "anamnese": {
                    "queixa_principal": anamnese.queixa_principal if anamnese else None,
                    "historico_atual": anamnese.historico_atual if anamnese else None,
                    "alimentacao": anamnese.alimentacao if anamnese else None,
                    "alergias": anamnese.alergias if anamnese else None,
                    "uso_medicacao_atual": anamnese.uso_medicacao_atual if anamnese else None,
                    "observacoes": anamnese.observacoes if anamnese else None,
                },
                "prontuario": {
                    "exame_fisico": prontuario.exame_fisico if prontuario else None,
                    "diagnostico": prontuario.diagnostico if prontuario else None,
                    "conduta": prontuario.conduta if prontuario else None,
                    "observacoes": prontuario.observacoes if prontuario else None,
                },
            }
        )

    timeline_producao = sorted(
        timeline_producao,
        key=_ordenar_timeline_item,
        reverse=True,
    )

    intercorrencias_grooming = sorted(
        intercorrencias_grooming,
        key=lambda item: (
            item.get("data") or datetime.min.date(),
            item.get("hora") or datetime.min.time(),
            item.get("agendamento_id") or 0
        ),
        reverse=True,
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
        "atendimentos_grooming": atendimentos,
        "consultas_veterinarias": consultas_veterinarias,
        "intercorrencias_grooming": intercorrencias_grooming,
        "timeline_producao": timeline_producao,
    }