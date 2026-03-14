from datetime import datetime, date, time, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.cliente import Cliente
from app.models.funcionario import Funcionario
from app.models.pet import Pet
from app.models.servico import Servico


router = APIRouter(tags=["Agenda Veterinária"])


def _get_week_range(data_ref: date):
    inicio = data_ref - timedelta(days=data_ref.weekday())
    fim = inicio + timedelta(days=6)
    return inicio, fim


def _safe_datetime_iso(data_value, hora_value):
    if not data_value:
        return None

    if hora_value:
        dt = datetime.combine(data_value, hora_value)
        return dt.isoformat()

    return datetime.combine(data_value, time.min).isoformat()


def _servico_valor(servico: Servico) -> Decimal:
    valor = (
        getattr(servico, "venda", None)
        or getattr(servico, "valor", None)
        or 0
    )
    return Decimal(str(valor))


def _servico_tempo_previsto(servico: Servico) -> int:
    """
    Retorna o tempo previsto em minutos.
    Ajuste aqui se o seu model de Servico usar outro nome de campo.
    """
    candidatos = [
        getattr(servico, "tempo_previsto", None),
        getattr(servico, "duracao_minutos", None),
        getattr(servico, "duracao", None),
        60,
    ]

    for valor in candidatos:
        try:
            numero = int(valor)
            if numero > 0:
                return numero
        except (TypeError, ValueError):
            continue

    return 60


def _buscar_servicos_do_agendamento(db: Session, agendamento_id: int):
    servicos = (
        db.query(Servico)
        .join(AgendamentoServico, AgendamentoServico.servico_id == Servico.id)
        .filter(
            AgendamentoServico.agendamento_id == agendamento_id,
            Servico.tipo_servico == "VETERINARIO",
        )
        .order_by(Servico.nome.asc())
        .all()
    )

    return [
        {
            "id": getattr(servico, "id", None),
            "nome": getattr(servico, "nome", ""),
            "tipo_servico": getattr(servico, "tipo_servico", ""),
            "porte_referencia": getattr(servico, "porte_referencia", ""),
            "valor": float(_servico_valor(servico)),
        }
        for servico in servicos
    ]


def _buscar_cliente(db: Session, cliente_id: Optional[int]):
    if not cliente_id:
        return None
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def _buscar_pet(db: Session, pet_id: Optional[int]):
    if not pet_id:
        return None
    return db.query(Pet).filter(Pet.id == pet_id).first()


def _buscar_funcionario(db: Session, funcionario_id: Optional[int]):
    if not funcionario_id:
        return None
    return db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()


def _serialize_agendamento(db: Session, agendamento: Agendamento):
    cliente = _buscar_cliente(db, getattr(agendamento, "cliente_id", None))
    pet = _buscar_pet(db, getattr(agendamento, "pet_id", None))
    funcionario = _buscar_funcionario(db, getattr(agendamento, "funcionario_id", None))
    servicos = _buscar_servicos_do_agendamento(db, getattr(agendamento, "id", None))

    valor_total = 0.0
    for servico in servicos:
        valor_total += float(servico.get("valor", 0) or 0)

    data_agendamento = getattr(agendamento, "data", None)
    hora_agendamento = getattr(agendamento, "hora", None)

    return {
        "id": getattr(agendamento, "id", None),
        "data": data_agendamento.isoformat() if data_agendamento else None,
        "hora": hora_agendamento.strftime("%H:%M:%S") if hora_agendamento else None,
        "data_agendamento": _safe_datetime_iso(data_agendamento, hora_agendamento),
        "status": getattr(agendamento, "status", "AGUARDANDO"),
        "prioridade": getattr(agendamento, "prioridade", "NORMAL"),
        "observacoes": getattr(agendamento, "observacoes", "") or "",
        "tem_intercorrencia": bool(getattr(agendamento, "tem_intercorrencia", False)),
        "valor_total": valor_total,
        "cliente": {
            "id": getattr(cliente, "id", None) if cliente else None,
            "nome": getattr(cliente, "nome", "") if cliente else "",
            "telefone": getattr(cliente, "telefone", "") if cliente else "",
            "email": getattr(cliente, "email", "") if cliente else "",
        },
        "pet": {
            "id": getattr(pet, "id", None) if pet else None,
            "nome": getattr(pet, "nome", "") if pet else "",
            "especie": getattr(pet, "especie", "") if pet else "",
            "raca": getattr(pet, "raca", "") if pet else "",
            "porte": getattr(pet, "porte", "") if pet else "",
            "sexo": getattr(pet, "sexo", "") if pet else "",
            "idade": getattr(pet, "idade", None) if pet else None,
        },
        "funcionario": {
            "id": getattr(funcionario, "id", None) if funcionario else None,
            "nome": getattr(funcionario, "nome", "") if funcionario else "",
        },
        "servicos": servicos,
    }


def _normalizar_servico_ids(servico_ids):
    if servico_ids is None:
        return []

    if not isinstance(servico_ids, list):
        raise HTTPException(status_code=400, detail="O campo servico_ids deve ser uma lista.")

    ids_normalizados = []
    for item in servico_ids:
        try:
            valor = int(item)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Há IDs de serviços inválidos na requisição.")

        if valor > 0 and valor not in ids_normalizados:
            ids_normalizados.append(valor)

    return ids_normalizados


def _resolver_empresa_id(cliente=None, pet=None, funcionario=None, body=None):
    body = body or {}

    empresa_candidates = [
        body.get("empresa_id"),
        getattr(cliente, "empresa_id", None) if cliente else None,
        getattr(pet, "empresa_id", None) if pet else None,
        getattr(funcionario, "empresa_id", None) if funcionario else None,
    ]

    for value in empresa_candidates:
        try:
            numero = int(value)
        except (TypeError, ValueError):
            continue

        if numero > 0:
            return numero

    return None


def _validar_consistencia_multiempresa(cliente=None, pet=None, funcionario=None, empresa_id=None):
    empresa_ids_encontradas = []

    for entidade in [cliente, pet, funcionario]:
        if entidade is None:
            continue

        valor = getattr(entidade, "empresa_id", None)
        if valor is not None:
            empresa_ids_encontradas.append(valor)

    if empresa_id is not None:
        empresa_ids_encontradas.append(empresa_id)

    empresa_ids_unicas = {item for item in empresa_ids_encontradas if item is not None}

    if len(empresa_ids_unicas) > 1:
        raise HTTPException(
            status_code=400,
            detail="Cliente, pet e responsável pertencem a empresas diferentes."
        )


@router.get("/api/agenda-veterinaria/semana")
def listar_agenda_veterinaria_semana(
    data_ref: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    try:
        if data_ref:
            data_base = datetime.strptime(data_ref, "%Y-%m-%d").date()
        else:
            data_base = date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data de referência inválida. Use YYYY-MM-DD.")

    inicio, fim = _get_week_range(data_base)

    agendamentos = (
        db.query(Agendamento)
        .join(AgendamentoServico, AgendamentoServico.agendamento_id == Agendamento.id)
        .join(Servico, Servico.id == AgendamentoServico.servico_id)
        .filter(
            Agendamento.data >= inicio,
            Agendamento.data <= fim,
            Servico.tipo_servico == "VETERINARIO",
        )
        .distinct()
        .order_by(Agendamento.data.asc(), Agendamento.hora.asc())
        .all()
    )

    itens = []
    for agendamento in agendamentos:
        serializado = _serialize_agendamento(db, agendamento)
        serializado["historico_url"] = (
            f"/api/pets/{serializado['pet']['id']}/historico"
            if serializado["pet"]["id"]
            else None
        )
        itens.append(serializado)

    dias = []
    cursor = inicio
    while cursor <= fim:
        dias.append(
            {
                "data": cursor.isoformat(),
                "label": cursor.strftime("%d/%m/%Y"),
                "dia_semana": [
                    "Segunda",
                    "Terça",
                    "Quarta",
                    "Quinta",
                    "Sexta",
                    "Sábado",
                    "Domingo",
                ][cursor.weekday()],
            }
        )
        cursor += timedelta(days=1)

    return {
        "periodo": {
            "inicio": inicio.isoformat(),
            "fim": fim.isoformat(),
            "inicio_label": inicio.strftime("%d/%m/%Y"),
            "fim_label": fim.strftime("%d/%m/%Y"),
        },
        "dias": dias,
        "agendamentos": itens,
    }


@router.get("/api/agenda-veterinaria/servicos")
def listar_servicos_veterinarios(
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Servico).filter(
        Servico.tipo_servico == "VETERINARIO",
        Servico.ativo == True,  # noqa: E712
    )

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(Servico.nome.ilike(termo))

    servicos = query.order_by(Servico.nome.asc()).all()

    return [
        {
            "id": getattr(item, "id", None),
            "nome": getattr(item, "nome", ""),
            "tipo_servico": getattr(item, "tipo_servico", ""),
            "porte_referencia": getattr(item, "porte_referencia", ""),
            "valor": float(_servico_valor(item)),
            "ativo": bool(getattr(item, "ativo", True)),
        }
        for item in servicos
    ]


@router.get("/api/agenda-veterinaria/clientes")
def listar_clientes(
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Cliente)

    if busca:
        termo = f"%{busca.strip()}%"
        filtros = []

        if hasattr(Cliente, "nome"):
            filtros.append(Cliente.nome.ilike(termo))
        if hasattr(Cliente, "telefone"):
            filtros.append(Cliente.telefone.ilike(termo))
        if hasattr(Cliente, "email"):
            filtros.append(Cliente.email.ilike(termo))

        if filtros:
            query = query.filter(or_(*filtros))

    if hasattr(Cliente, "ativo"):
        query = query.filter(Cliente.ativo == True)  # noqa: E712

    clientes = query.order_by(Cliente.nome.asc()).limit(50).all()

    return [
        {
            "id": getattr(item, "id", None),
            "nome": getattr(item, "nome", ""),
            "telefone": getattr(item, "telefone", ""),
            "email": getattr(item, "email", ""),
        }
        for item in clientes
    ]


@router.get("/api/agenda-veterinaria/pets")
def listar_pets(
    cliente_id: Optional[int] = Query(None),
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Pet)

    if cliente_id is not None and hasattr(Pet, "cliente_id"):
        query = query.filter(Pet.cliente_id == cliente_id)

    if busca:
        termo = f"%{busca.strip()}%"
        filtros = []

        if hasattr(Pet, "nome"):
            filtros.append(Pet.nome.ilike(termo))
        if hasattr(Pet, "raca"):
            filtros.append(Pet.raca.ilike(termo))

        if filtros:
            query = query.filter(or_(*filtros))

    if hasattr(Pet, "ativo"):
        query = query.filter(Pet.ativo == True)  # noqa: E712

    pets = query.order_by(Pet.nome.asc()).limit(100).all()

    return [
        {
            "id": getattr(item, "id", None),
            "nome": getattr(item, "nome", ""),
            "cliente_id": getattr(item, "cliente_id", None),
            "especie": getattr(item, "especie", ""),
            "raca": getattr(item, "raca", ""),
            "porte": getattr(item, "porte", ""),
            "sexo": getattr(item, "sexo", ""),
        }
        for item in pets
    ]


@router.get("/api/agenda-veterinaria/funcionarios")
def listar_funcionarios(
    busca: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Funcionario)

    if busca:
        termo = f"%{busca.strip()}%"
        if hasattr(Funcionario, "nome"):
            query = query.filter(Funcionario.nome.ilike(termo))

    if hasattr(Funcionario, "ativo"):
        query = query.filter(Funcionario.ativo == True)  # noqa: E712

    funcionarios = query.order_by(Funcionario.nome.asc()).limit(50).all()

    return [
        {
            "id": getattr(item, "id", None),
            "nome": getattr(item, "nome", ""),
        }
        for item in funcionarios
    ]


@router.get("/api/agenda-veterinaria/agendamentos/{agendamento_id}")
def detalhar_agendamento_veterinario(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    agendamento = (
        db.query(Agendamento)
        .filter(Agendamento.id == agendamento_id)
        .first()
    )

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    servicos = _buscar_servicos_do_agendamento(db, agendamento_id)
    if not servicos:
        raise HTTPException(status_code=400, detail="Este agendamento não pertence à agenda veterinária.")

    payload = _serialize_agendamento(db, agendamento)
    payload["historico_url"] = (
        f"/api/pets/{payload['pet']['id']}/historico"
        if payload["pet"]["id"]
        else None
    )
    return payload


@router.post("/api/agenda-veterinaria/agendamentos")
async def criar_agendamento_veterinario(
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Requisição inválida. Envie um JSON válido.")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Corpo da requisição inválido.")

    cliente_id = body.get("cliente_id")
    pet_id = body.get("pet_id")
    funcionario_id = body.get("funcionario_id")
    data_agendamento = body.get("data_agendamento")
    observacoes = body.get("observacoes", "")
    prioridade = body.get("prioridade", "NORMAL")
    status = body.get("status", "AGUARDANDO")
    servico_ids = _normalizar_servico_ids(body.get("servico_ids", []))

    if not cliente_id:
        raise HTTPException(status_code=400, detail="Cliente é obrigatório.")
    if not pet_id:
        raise HTTPException(status_code=400, detail="Pet é obrigatório.")
    if not data_agendamento:
        raise HTTPException(status_code=400, detail="Data/hora do agendamento é obrigatória.")
    if not servico_ids:
        raise HTTPException(status_code=400, detail="Selecione ao menos um serviço veterinário.")

    try:
        data_agendamento_dt = datetime.fromisoformat(data_agendamento)
    except ValueError:
        raise HTTPException(status_code=400, detail="Data/hora inválida.")

    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    pet = db.query(Pet).filter(Pet.id == pet_id).first()
    if not pet:
        raise HTTPException(status_code=404, detail="Pet não encontrado.")

    if hasattr(Pet, "cliente_id") and getattr(pet, "cliente_id", None) != cliente_id:
        raise HTTPException(status_code=400, detail="O pet selecionado não pertence ao cliente informado.")

    funcionario = None
    if funcionario_id:
        funcionario = db.query(Funcionario).filter(Funcionario.id == funcionario_id).first()
        if not funcionario:
            raise HTTPException(status_code=404, detail="Funcionário não encontrado.")

    empresa_id = _resolver_empresa_id(
        cliente=cliente,
        pet=pet,
        funcionario=funcionario,
        body=body,
    )

    _validar_consistencia_multiempresa(
        cliente=cliente,
        pet=pet,
        funcionario=funcionario,
        empresa_id=empresa_id,
    )

    servicos = (
        db.query(Servico)
        .filter(
            Servico.id.in_(servico_ids),
            Servico.tipo_servico == "VETERINARIO",
            Servico.ativo == True,  # noqa: E712
        )
        .all()
    )

    if len(servicos) != len(servico_ids):
        raise HTTPException(status_code=400, detail="Há serviços inválidos ou não veterinários na seleção.")

    try:
        novo_agendamento = Agendamento()

        if hasattr(novo_agendamento, "empresa_id") and empresa_id:
            novo_agendamento.empresa_id = empresa_id

        if hasattr(novo_agendamento, "cliente_id"):
            novo_agendamento.cliente_id = cliente_id
        if hasattr(novo_agendamento, "pet_id"):
            novo_agendamento.pet_id = pet_id
        if hasattr(novo_agendamento, "funcionario_id"):
            novo_agendamento.funcionario_id = funcionario_id
        if hasattr(novo_agendamento, "data"):
            novo_agendamento.data = data_agendamento_dt.date()
        if hasattr(novo_agendamento, "hora"):
            novo_agendamento.hora = data_agendamento_dt.time()
        if hasattr(novo_agendamento, "observacoes"):
            novo_agendamento.observacoes = observacoes
        if hasattr(novo_agendamento, "prioridade"):
            novo_agendamento.prioridade = prioridade
        if hasattr(novo_agendamento, "status"):
            novo_agendamento.status = status

        db.add(novo_agendamento)
        db.flush()

        for servico in servicos:
            rel = AgendamentoServico()

            if hasattr(rel, "agendamento_id"):
                rel.agendamento_id = novo_agendamento.id

            if hasattr(rel, "servico_id"):
                rel.servico_id = servico.id

            if hasattr(rel, "preco"):
                rel.preco = _servico_valor(servico)

            if hasattr(rel, "tempo_previsto"):
                rel.tempo_previsto = _servico_tempo_previsto(servico)

            db.add(rel)

        db.commit()
        db.refresh(novo_agendamento)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Não foi possível salvar o agendamento por restrição de integridade: {str(exc.orig)}"
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Erro de banco de dados ao criar o agendamento veterinário."
        )

    payload = _serialize_agendamento(db, novo_agendamento)
    payload["historico_url"] = (
        f"/api/pets/{payload['pet']['id']}/historico"
        if payload["pet"]["id"]
        else None
    )
    payload["message"] = "Agendamento veterinário criado com sucesso."
    return payload


@router.post("/api/agenda-veterinaria/agendamentos/{agendamento_id}/iniciar-atendimento")
def iniciar_atendimento_veterinario(
    agendamento_id: int,
    db: Session = Depends(get_db),
):
    agendamento = (
        db.query(Agendamento)
        .filter(Agendamento.id == agendamento_id)
        .first()
    )

    if not agendamento:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado.")

    servicos = _buscar_servicos_do_agendamento(db, agendamento_id)
    if not servicos:
        raise HTTPException(status_code=400, detail="Este agendamento não pertence à agenda veterinária.")

    payload = _serialize_agendamento(db, agendamento)

    return {
        "message": "Atendimento clínico pronto para abertura.",
        "agendamento": payload,
        "atendimento_clinico": {
            "modo": "draft_local",
            "agendamento_id": payload["id"],
            "pet_id": payload["pet"]["id"],
            "cliente_id": payload["cliente"]["id"],
            "historico_url": (
                f"/api/pets/{payload['pet']['id']}/historico"
                if payload["pet"]["id"]
                else None
            ),
            "pdv_integracao_preparada": True,
            "permite_historico_sem_fechar_anamnese": True,
        },
    }