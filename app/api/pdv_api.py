from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.crud.pdv import (
    adicionar_item,
    atualizar_venda,
    buscar_clientes,
    buscar_produtos,
    cancelar_venda,
    checkout_venda,
    criar_venda,
    enviar_producao_para_pdv,
    listar_atendimentos_prontos,
    listar_producao_prontos,
    listar_vendas,
    obter_venda,
    remover_item,
)
from app.models.atendimento_clinico import AtendimentoClinico
from app.models.pdv_pagamento import PdvPagamento
from app.models.pdv_venda import PdvVenda
from app.models.pdv_venda_item import PdvVendaItem
from app.models.producao import Producao
from app.models.usuario import Usuario
from app.schemas.pdv import (
    PdvAtendimentoProntoOut,
    PdvCancelRequest,
    PdvCheckoutRequest,
    PdvClienteBuscaOut,
    PdvOperacaoResponse,
    PdvProducaoProntoOut,
    PdvVendaCreate,
    PdvVendaItemAdd,
    PdvVendaListOut,
    PdvVendaOut,
    PdvVendaProducaoCreate,
    PdvVendaUpdate,
)

router = APIRouter(prefix="/api/pdv", tags=["PDV"])


def _to_float(valor):
    return float(valor or 0)


def _serializar_cliente(cliente):
    if not cliente:
        return None
    return {
        "id": cliente.id,
        "nome": getattr(cliente, "nome", None),
        "cpf": getattr(cliente, "cpf", None),
        "telefone": getattr(cliente, "telefone", None),
        "saldo_cashback": _to_float(getattr(cliente, "saldo_cashback", 0)),
    }


def _serializar_produto(produto):
    if not produto:
        return None
    return {
        "id": produto.id,
        "empresa_id": produto.empresa_id,
        "nome": getattr(produto, "nome", None),
        "ativo": bool(getattr(produto, "ativo", False)),
        "preco_venda_atual": _to_float(getattr(produto, "preco_venda_atual", 0)),
        "estoque_atual": _to_float(getattr(produto, "estoque_atual", 0)),
    }


def _serializar_item(item: PdvVendaItem):
    return {
        "id": item.id,
        "venda_id": item.venda_id,
        "tipo_item": item.tipo_item,
        "atendimento_clinico_id": item.atendimento_clinico_id,
        "produto_id": item.produto_id,
        "descricao_snapshot": item.descricao_snapshot,
        "observacao": item.observacao,
        "quantidade": _to_float(item.quantidade),
        "valor_unitario": _to_float(item.valor_unitario),
        "desconto_valor": _to_float(item.desconto_valor),
        "valor_total": _to_float(item.valor_total),
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


def _serializar_pagamento(pagamento: PdvPagamento) -> dict:
    return {
        "id": pagamento.id,
        "venda_id": pagamento.venda_id,
        "forma_pagamento": pagamento.forma_pagamento,
        "valor": float(pagamento.valor or 0),
        "quantidade_parcelas": pagamento.quantidade_parcelas,
        "status": pagamento.status,
        "referencia": pagamento.referencia,
        "observacoes": pagamento.observacoes,
        "usuario_id": pagamento.usuario_id,
        "recebido_em": pagamento.recebido_em,
        "created_at": pagamento.created_at,
        "updated_at": pagamento.updated_at,
    }


def _serializar_venda(venda: PdvVenda):
    return {
        "id": venda.id,
        "empresa_id": venda.empresa_id,
        "caixa_sessao_id": venda.caixa_sessao_id,
        "numero_venda": venda.numero_venda,
        "modo_cliente": venda.modo_cliente,
        "cliente_id": venda.cliente_id,
        "nome_cliente_snapshot": venda.nome_cliente_snapshot,
        "telefone_cliente_snapshot": venda.telefone_cliente_snapshot,
        "origem": venda.origem,
        "status": venda.status,
        "subtotal": _to_float(venda.subtotal),
        "desconto_valor": _to_float(venda.desconto_valor),
        "acrescimo_valor": _to_float(venda.acrescimo_valor),
        "valor_total": _to_float(venda.valor_total),
        "observacoes": venda.observacoes,
        "usuario_abertura_id": venda.usuario_abertura_id,
        "usuario_fechamento_id": venda.usuario_fechamento_id,
        "usuario_cancelamento_id": venda.usuario_cancelamento_id,
        "aberta_em": venda.aberta_em.isoformat() if venda.aberta_em else None,
        "fechada_em": venda.fechada_em.isoformat() if venda.fechada_em else None,
        "cancelada_em": venda.cancelada_em.isoformat() if venda.cancelada_em else None,
        "motivo_cancelamento": venda.motivo_cancelamento,
        "created_at": venda.created_at.isoformat() if venda.created_at else None,
        "updated_at": venda.updated_at.isoformat() if venda.updated_at else None,
        "cliente": _serializar_cliente(venda.cliente),
        "itens": [_serializar_item(item) for item in (venda.itens or [])],
        "pagamentos": [_serializar_pagamento(pagamento) for pagamento in (venda.pagamentos or [])],
    }


def _descricao_atendimento(atendimento: AtendimentoClinico) -> str:
    pet = getattr(atendimento, "pet", None)
    pet_nome = getattr(pet, "nome", None) if pet else None

    descricoes = []
    for item in getattr(atendimento, "itens", []) or []:
        descricao = (getattr(item, "descricao", None) or "").strip()
        if descricao:
            descricoes.append(descricao)

    if descricoes:
        descricao_base = " | ".join(descricoes[:3])
        if len(descricoes) > 3:
            descricao_base += " | ..."
    else:
        descricao_base = "Atendimento clínico"

    if pet_nome:
        return f"{descricao_base} - {pet_nome}"
    return descricao_base


def _total_atendimento(atendimento: AtendimentoClinico) -> Decimal:
    total = Decimal("0.00")
    for item in getattr(atendimento, "itens", []) or []:
        total += Decimal(str(getattr(item, "valor_total", 0) or 0))
    return total


def _serializar_atendimento_pronto(atendimento: AtendimentoClinico):
    pet = getattr(atendimento, "pet", None)
    cliente = getattr(atendimento, "cliente", None)
    return {
        "atendimento_id": atendimento.id,
        "cliente_id": atendimento.cliente_id,
        "cliente_nome": getattr(cliente, "nome", None),
        "pet_nome": getattr(pet, "nome", None) if pet else None,
        "descricao": _descricao_atendimento(atendimento),
        "valor_total": _to_float(_total_atendimento(atendimento)),
        "status": atendimento.status,
        "enviado_pdv": bool(atendimento.enviado_pdv),
    }


def _serializar_operador(usuario: Usuario):
    return {
        "id": usuario.id,
        "nome": usuario.nome,
        "email": usuario.email,
        "tipo": usuario.tipo,
        "ativo": bool(usuario.ativo),
        "pode_pdv": bool(getattr(usuario, "pode_pdv", False)),
    }


def _descricao_producao(producao: Producao) -> str:
    agendamento = getattr(producao, "agendamento", None)
    pet = getattr(agendamento, "pet", None) if agendamento else None
    pet_nome = getattr(pet, "nome", None) if pet else None

    nomes = []
    for item in getattr(agendamento, "servicos_agendamento", []) or []:
        servico = getattr(item, "servico", None)
        nome_servico = (getattr(servico, "nome", None) or "").strip() if servico else ""
        if nome_servico:
            nomes.append(nome_servico)

    descricao_base = ", ".join(nomes[:5]) if nomes else "Serviços petshop"
    if len(nomes) > 5:
        descricao_base += ", ..."

    if pet_nome:
        return f"{descricao_base} - {pet_nome}"
    return descricao_base


def _total_producao(producao: Producao) -> Decimal:
    total = Decimal("0.00")
    agendamento = getattr(producao, "agendamento", None)
    for item in getattr(agendamento, "servicos_agendamento", []) or []:
        total += Decimal(str(getattr(item, "preco", 0) or 0))
    return total


def _serializar_producao_pronta(producao: Producao):
    agendamento = getattr(producao, "agendamento", None)
    cliente = getattr(agendamento, "cliente", None) if agendamento else None
    pet = getattr(agendamento, "pet", None) if agendamento else None

    return {
        "producao_id": producao.id,
        "agendamento_id": getattr(producao, "agendamento_id", None),
        "cliente_id": getattr(agendamento, "cliente_id", None),
        "cliente_nome": getattr(cliente, "nome", None),
        "pet_nome": getattr(pet, "nome", None) if pet else None,
        "descricao": _descricao_producao(producao),
        "valor_total": _to_float(_total_producao(producao)),
        "finalizado": bool(getattr(producao, "finalizado", False)),
        "enviado_pdv": bool(getattr(producao, "enviado_pdv", False)),
    }


def _inicio_do_dia(data_ref: date) -> datetime:
    return datetime.combine(data_ref, time.min).replace(tzinfo=timezone.utc)


def _fim_exclusivo_do_dia(data_ref: date) -> datetime:
    return _inicio_do_dia(data_ref + timedelta(days=1))


@router.get("/operadores")
def listar_operadores_pdv(
    empresa_id: int = Query(..., ge=1),
    q: str | None = Query(None),
    limite: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    termo = (q or "").strip()

    query = (
        db.query(Usuario)
        .filter(
            Usuario.empresa_id == empresa_id,
            Usuario.ativo.is_(True),
            Usuario.pode_pdv.is_(True),
        )
    )

    if termo:
        like = f"%{termo}%"
        query = query.filter(
            or_(
                Usuario.nome.ilike(like),
                Usuario.email.ilike(like),
                Usuario.tipo.ilike(like),
            )
        )

    operadores = query.order_by(Usuario.nome.asc(), Usuario.id.asc()).limit(limite).all()
    return [_serializar_operador(usuario) for usuario in operadores]


@router.get("/clientes/busca", response_model=list[PdvClienteBuscaOut])
def buscar_clientes_pdv(
    empresa_id: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    clientes = buscar_clientes(db, empresa_id=empresa_id, termo=q, limite=limite)
    return [_serializar_cliente(cliente) for cliente in clientes]


@router.get("/produtos/busca")
def buscar_produtos_pdv(
    empresa_id: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    produtos = buscar_produtos(db, empresa_id=empresa_id, termo=q, limite=limite)
    return [_serializar_produto(produto) for produto in produtos]


@router.get("/atendimentos/prontos", response_model=list[PdvAtendimentoProntoOut])
def listar_atendimentos_prontos_pdv(
    empresa_id: int = Query(..., ge=1),
    cliente_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    atendimentos = listar_atendimentos_prontos(
        db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
    )
    return [_serializar_atendimento_pronto(atendimento) for atendimento in atendimentos]


@router.get("/producao/prontos", response_model=list[PdvProducaoProntoOut])
def listar_producao_prontos_pdv(
    empresa_id: int = Query(..., ge=1),
    cliente_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    producoes = listar_producao_prontos(db, empresa_id=empresa_id, cliente_id=cliente_id)
    return [_serializar_producao_pronta(p) for p in producoes]


@router.post("/vendas/producao", response_model=PdvVendaOut)
def enviar_producao_pdv(
    payload: PdvVendaProducaoCreate,
    db: Session = Depends(get_db),
):
    venda = enviar_producao_para_pdv(db, payload)
    return _serializar_venda(venda)


@router.post("/vendas", response_model=PdvVendaOut)
def criar_venda_pdv(
    payload: PdvVendaCreate,
    db: Session = Depends(get_db),
):
    venda = criar_venda(db, payload)
    return _serializar_venda(venda)


@router.get("/vendas", response_model=list[PdvVendaListOut])
def listar_vendas_pdv(
    empresa_id: int = Query(..., ge=1),
    status: str | None = Query(None),
    limite: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    vendas = listar_vendas(db, empresa_id=empresa_id, status=status, limite=limite)
    return [
        {
            "id": venda.id,
            "caixa_sessao_id": venda.caixa_sessao_id,
            "numero_venda": venda.numero_venda,
            "modo_cliente": venda.modo_cliente,
            "cliente_id": venda.cliente_id,
            "nome_cliente_snapshot": venda.nome_cliente_snapshot,
            "origem": venda.origem,
            "status": venda.status,
            "valor_total": _to_float(venda.valor_total),
            "aberta_em": venda.aberta_em.isoformat() if venda.aberta_em else None,
            "fechada_em": venda.fechada_em.isoformat() if venda.fechada_em else None,
            "cliente": _serializar_cliente(venda.cliente),
        }
        for venda in vendas
    ]


@router.get("/vendas/{venda_id}", response_model=PdvVendaOut)
def obter_venda_pdv(
    venda_id: int,
    db: Session = Depends(get_db),
):
    venda = obter_venda(db, venda_id)
    return _serializar_venda(venda)


@router.patch("/vendas/{venda_id}", response_model=PdvVendaOut)
def atualizar_venda_pdv(
    venda_id: int,
    payload: PdvVendaUpdate,
    db: Session = Depends(get_db),
):
    venda = atualizar_venda(db, venda_id, payload)
    return _serializar_venda(venda)


@router.post("/vendas/{venda_id}/itens", response_model=PdvVendaOut)
def adicionar_item_pdv(
    venda_id: int,
    payload: PdvVendaItemAdd,
    db: Session = Depends(get_db),
):
    venda = adicionar_item(db, venda_id, payload)
    return _serializar_venda(venda)


@router.delete("/vendas/{venda_id}/itens/{item_id}", response_model=PdvVendaOut)
def remover_item_pdv(
    venda_id: int,
    item_id: int,
    db: Session = Depends(get_db),
):
    venda = remover_item(db, venda_id, item_id)
    return _serializar_venda(venda)


@router.post("/vendas/{venda_id}/checkout", response_model=PdvOperacaoResponse)
def checkout_venda_pdv(
    venda_id: int,
    payload: PdvCheckoutRequest,
    db: Session = Depends(get_db),
):
    venda = checkout_venda(db, venda_id, payload)
    return {
        "ok": True,
        "mensagem": "Venda finalizada com sucesso.",
        "venda": _serializar_venda(venda),
    }


@router.post("/vendas/{venda_id}/cancelar", response_model=PdvOperacaoResponse)
def cancelar_venda_pdv(
    venda_id: int,
    payload: PdvCancelRequest,
    db: Session = Depends(get_db),
):
    venda = cancelar_venda(db, venda_id, payload)
    return {
        "ok": True,
        "mensagem": "Venda cancelada com sucesso.",
        "venda": _serializar_venda(venda),
    }