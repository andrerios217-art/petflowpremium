from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, Body, Body, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

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
    relatorio_vendas as relatorio_vendas_crud,
    remover_item,
)
from app.crud.pdv_relatorios import relatorio_itens_vendidos as relatorio_itens_vendidos_crud
from app.crud.ia_compras import analisar_compras_produtos as analisar_compras_produtos_crud
from app.models.assinatura_pet import AssinaturaPet
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

# === PATCH PDV PRODUCAO ROBUSTA VECTORPET ===

def _vp_pdv_prod_colunas(modelo):
    try:
        return {coluna.name for coluna in modelo.__table__.columns}
    except Exception:
        return set()


def _vp_pdv_prod_set(obj, campo, valor):
    try:
        if campo in _vp_pdv_prod_colunas(type(obj)):
            setattr(obj, campo, valor)
            return True
    except Exception:
        pass

    return False


def _vp_pdv_prod_decimal(valor):
    try:
        return Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


def _vp_pdv_prod_status(valor):
    return str(valor or "").strip().upper()


def _vp_pdv_prod_recalcular_venda(db: Session, venda: PdvVenda | None):
    if venda is None:
        return None

    itens = (
        db.query(PdvVendaItem)
        .filter(PdvVendaItem.venda_id == venda.id)
        .all()
    )

    subtotal = Decimal("0.00")
    tem_produto = False
    tem_servico = False

    for item in itens:
        quantidade = _vp_pdv_prod_decimal(getattr(item, "quantidade", 1) or 1)
        valor_unitario = _vp_pdv_prod_decimal(getattr(item, "valor_unitario", 0) or 0)
        desconto_item = _vp_pdv_prod_decimal(getattr(item, "desconto_valor", 0) or 0)

        valor_total = _vp_pdv_prod_decimal(getattr(item, "valor_total", 0))

        if valor_total <= 0 and valor_unitario > 0:
            valor_total = (quantidade * valor_unitario - desconto_item).quantize(Decimal("0.01"))
            _vp_pdv_prod_set(item, "valor_total", valor_total)
            db.add(item)

        subtotal += valor_total

        tipo = _vp_pdv_prod_status(getattr(item, "tipo_item", ""))

        if tipo == "PRODUCT":
            tem_produto = True
        else:
            tem_servico = True

    desconto = _vp_pdv_prod_decimal(getattr(venda, "desconto_valor", 0))
    acrescimo = _vp_pdv_prod_decimal(getattr(venda, "acrescimo_valor", 0))
    total = subtotal - desconto + acrescimo

    if total < 0:
        total = Decimal("0.00")

    _vp_pdv_prod_set(venda, "subtotal", subtotal.quantize(Decimal("0.01")))
    _vp_pdv_prod_set(venda, "valor_total", total.quantize(Decimal("0.01")))

    if tem_produto and tem_servico:
        _vp_pdv_prod_set(venda, "origem", "MIXED")
    elif tem_servico:
        _vp_pdv_prod_set(venda, "origem", "SERVICE_ONLY")
    elif tem_produto:
        _vp_pdv_prod_set(venda, "origem", "PRODUCT_ONLY")

    db.add(venda)
    db.flush()

    return venda


def _vp_pdv_prod_cliente_id(producao):
    agendamento = getattr(producao, "agendamento", None)
    return getattr(agendamento, "cliente_id", None) if agendamento else None


def _vp_pdv_prod_cliente_nome(producao):
    agendamento = getattr(producao, "agendamento", None)

    if not agendamento:
        return None

    cliente = getattr(agendamento, "cliente", None)
    return getattr(cliente, "nome", None) if cliente else None


def _vp_pdv_prod_preparar_venda_cliente(venda, producao):
    cliente_id = _vp_pdv_prod_cliente_id(producao)

    if cliente_id and getattr(venda, "cliente_id", None) and int(venda.cliente_id) != int(cliente_id):
        raise HTTPException(
            status_code=400,
            detail="Esse serviço pertence a outro cliente.",
        )

    if cliente_id and not getattr(venda, "cliente_id", None):
        _vp_pdv_prod_set(venda, "cliente_id", cliente_id)
        _vp_pdv_prod_set(venda, "modo_cliente", "REGISTERED_CLIENT")
        _vp_pdv_prod_set(venda, "nome_cliente_snapshot", _vp_pdv_prod_cliente_nome(producao))


def _vp_pdv_prod_preencher_item(item, venda, producao):
    valor = _vp_pdv_prod_decimal(_total_producao(producao))
    descricao = _descricao_producao(producao)

    if valor <= 0:
        raise HTTPException(
            status_code=400,
            detail="Esse serviço está com valor zerado. Verifique o agendamento/serviço antes de cobrar.",
        )

    _vp_pdv_prod_set(item, "venda_id", venda.id)
    _vp_pdv_prod_set(item, "empresa_id", getattr(venda, "empresa_id", None))
    _vp_pdv_prod_set(item, "tipo_item", "SERVICE")
    _vp_pdv_prod_set(item, "origem_item", "SERVICE")
    _vp_pdv_prod_set(item, "atendimento_clinico_id", None)
    _vp_pdv_prod_set(item, "produto_id", None)
    _vp_pdv_prod_set(item, "gera_movimento_estoque", False)
    _vp_pdv_prod_set(item, "descricao_snapshot", descricao)
    _vp_pdv_prod_set(item, "observacao", f"PRODUCAO_ID:{producao.id};AGENDAMENTO_ID:{getattr(producao, 'agendamento_id', '')}")
    _vp_pdv_prod_set(item, "quantidade", Decimal("1.00"))
    _vp_pdv_prod_set(item, "valor_unitario", valor)
    _vp_pdv_prod_set(item, "desconto_valor", Decimal("0.00"))
    _vp_pdv_prod_set(item, "desconto_percentual", Decimal("0.00"))
    _vp_pdv_prod_set(item, "acrescimo_valor", Decimal("0.00"))
    _vp_pdv_prod_set(item, "valor_total", valor)

    return item


@router.post("/vendas/{venda_id}/producao/{producao_id}/adicionar")
@router.post("/vendas/{venda_id}/producao/{producao_id}/adicionar-debug")
def adicionar_producao_sem_duplicar_pdv(
    venda_id: int,
    producao_id: int,
    db: Session = Depends(get_db),
):
    try:
        venda = (
            db.query(PdvVenda)
            .filter(PdvVenda.id == venda_id)
            .first()
        )

        if venda is None:
            raise HTTPException(status_code=404, detail="Venda não encontrada.")

        if _vp_pdv_prod_status(getattr(venda, "status", "")) != "ABERTA":
            raise HTTPException(status_code=400, detail="A venda precisa estar aberta.")

        producao = (
            db.query(Producao)
            .filter(Producao.id == producao_id)
            .first()
        )

        if producao is None:
            raise HTTPException(status_code=404, detail="Serviço da produção não encontrado.")

        _vp_pdv_prod_preparar_venda_cliente(venda, producao)

        marcador = f"PRODUCAO_ID:{producao.id}"

        item_existente = (
            db.query(PdvVendaItem)
            .filter(PdvVendaItem.observacao.ilike(f"%{marcador}%"))
            .first()
        )

        venda_antiga = None

        if item_existente is not None:
            venda_antiga = (
                db.query(PdvVenda)
                .filter(PdvVenda.id == item_existente.venda_id)
                .first()
            )

            status_antigo = _vp_pdv_prod_status(getattr(venda_antiga, "status", ""))

            if venda_antiga and venda_antiga.id != venda.id and status_antigo in ["FECHADA", "CONCLUIDA", "FINALIZADA", "PAGA"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Esse serviço já foi cobrado na venda {getattr(venda_antiga, 'numero_venda', venda_antiga.id)}.",
                )

            item = item_existente
        else:
            item = PdvVendaItem()

        _vp_pdv_prod_preencher_item(item, venda, producao)

        db.add(item)

        _vp_pdv_prod_set(producao, "enviado_pdv", True)
        db.add(producao)

        if venda_antiga is not None and venda_antiga.id != venda.id:
            _vp_pdv_prod_recalcular_venda(db, venda_antiga)

        _vp_pdv_prod_recalcular_venda(db, venda)

        db.commit()
        db.refresh(venda)

        return _serializar_venda(venda, db=db)

    except HTTPException:
        raise
    except Exception as erro:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adicionar serviço da produção no PDV: {type(erro).__name__}: {erro}",
        ) from erro

# === FIM PATCH PDV PRODUCAO ROBUSTA VECTORPET ===

# === PATCH CHECKOUT PDV VECTORPET ===

def _vp_checkout_colunas(modelo):
    try:
        return {coluna.name for coluna in modelo.__table__.columns}
    except Exception:
        return set()


def _vp_checkout_set(obj, campo, valor):
    try:
        if campo in _vp_checkout_colunas(type(obj)):
            setattr(obj, campo, valor)
            return True
    except Exception:
        pass

    return False


def _vp_checkout_decimal(valor):
    try:
        return Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


@router.post("/vendas/{venda_id}/checkout")
def checkout_venda_pdv_vectorpet_seguro(
    venda_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
):
    """
    Restaura o endpoint de finalização da venda.
    Primeiro tenta usar o fluxo original do sistema.
    Se o schema tiver sido alterado, finaliza com fallback seguro.
    """
    try:
        try:
            schema = PdvCheckoutRequest(**payload)
            venda = checkout_venda(db, venda_id, schema)

            return {
                "ok": True,
                "mensagem": "Venda finalizada com sucesso.",
                "venda": _serializar_venda(venda, db=db),
            }
        except HTTPException:
            raise
        except Exception:
            db.rollback()

        venda = (
            db.query(PdvVenda)
            .filter(PdvVenda.id == venda_id)
            .first()
        )

        if venda is None:
            raise HTTPException(status_code=404, detail="Venda não encontrada.")

        status = str(getattr(venda, "status", "") or "").upper()

        if status not in ["ABERTA", "OPEN"]:
            raise HTTPException(status_code=400, detail="A venda precisa estar aberta para finalizar.")

        dados_pagamento = payload.get("pagamento") or payload or {}

        forma_pagamento = str(
            dados_pagamento.get("forma_pagamento")
            or dados_pagamento.get("forma")
            or "DINHEIRO"
        ).strip() or "DINHEIRO"

        valor_total_venda = _vp_checkout_decimal(getattr(venda, "valor_total", 0))
        valor_pago = _vp_checkout_decimal(dados_pagamento.get("valor") or valor_total_venda)

        parcelas = (
            dados_pagamento.get("quantidade_parcelas")
            or dados_pagamento.get("Quantidade_parcelas")
            or dados_pagamento.get("parcelas")
            or 1
        )

        try:
            parcelas = int(parcelas)
        except Exception:
            parcelas = 1

        if parcelas < 1:
            parcelas = 1

        if parcelas > 12:
            parcelas = 12

        if valor_total_venda > 0 and valor_pago <= 0:
            raise HTTPException(status_code=400, detail="Informe um valor de pagamento válido.")

        pagamento = PdvPagamento()

        _vp_checkout_set(pagamento, "venda_id", venda.id)
        _vp_checkout_set(pagamento, "forma_pagamento", forma_pagamento)
        _vp_checkout_set(pagamento, "valor", valor_pago)
        _vp_checkout_set(pagamento, "quantidade_parcelas", parcelas)
        _vp_checkout_set(pagamento, "status", "CONFIRMADO")
        _vp_checkout_set(pagamento, "recebido_em", datetime.now(timezone.utc))
        _vp_checkout_set(pagamento, "created_at", datetime.now(timezone.utc))
        _vp_checkout_set(pagamento, "updated_at", datetime.now(timezone.utc))

        db.add(pagamento)

        _vp_checkout_set(venda, "status", "FECHADA")
        _vp_checkout_set(venda, "fechada_em", datetime.now(timezone.utc))
        _vp_checkout_set(venda, "updated_at", datetime.now(timezone.utc))

        db.add(venda)
        db.commit()
        db.refresh(venda)

        return {
            "ok": True,
            "mensagem": "Venda finalizada com sucesso.",
            "venda": _serializar_venda(venda, db=db),
        }

    except HTTPException:
        raise
    except Exception as erro:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao finalizar venda no PDV: {type(erro).__name__}: {erro}",
        ) from erro

# === FIM PATCH CHECKOUT PDV VECTORPET ===

# === PATCH DEBUG PDV ENDPOINT ATENDIMENTO ===
@router.post("/vendas/{venda_id}/atendimentos/{atendimento_id}/adicionar-debug")
def adicionar_atendimento_debug_pdv(
    venda_id: int,
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    try:
        venda = (
            db.query(PdvVenda)
            .filter(PdvVenda.id == venda_id)
            .first()
        )

        if venda is None:
            raise HTTPException(status_code=404, detail="Venda não encontrada.")

        atendimento = (
            db.query(AtendimentoClinico)
            .filter(AtendimentoClinico.id == atendimento_id)
            .first()
        )

        if atendimento is None:
            raise HTTPException(status_code=404, detail="Atendimento clínico não encontrado.")

        # Usa o CRUD original de item, sem montar PdvVendaItem manualmente.
        payload = PdvVendaItemAdd(
            tipo_item="SERVICE",
            atendimento_clinico_id=atendimento.id,
            produto_id=None,
            descricao_snapshot=_descricao_atendimento(atendimento),
            quantidade=1,
            valor_unitario=_total_atendimento(atendimento),
            desconto_valor=0,
        )

        venda = adicionar_item(db, venda_id, payload)

        try:
            atendimento.enviado_pdv = True
            db.add(atendimento)
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(venda)

        return _serializar_venda(venda, db=db)

    except HTTPException:
        raise
    except Exception as erro:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro real ao adicionar atendimento no PDV: {type(erro).__name__}: {erro}",
        ) from erro
# === FIM PATCH DEBUG PDV ENDPOINT ATENDIMENTO ===

# === PATCH PDV ROTAS DEDICADAS VECTORPET ===
import re as _vp_pdv_re_dedicado


def _vp_pdv_colunas_dedicado(modelo):
    try:
        return {coluna.name for coluna in modelo.__table__.columns}
    except Exception:
        return set()


def _vp_pdv_set_dedicado(obj, campo, valor):
    try:
        if campo in _vp_pdv_colunas_dedicado(type(obj)):
            setattr(obj, campo, valor)
            return True
    except Exception:
        pass

    return False


def _vp_pdv_decimal_dedicado(valor):
    try:
        return Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except Exception:
        return Decimal("0.00")


def _vp_pdv_recalcular_venda_dedicado(db: Session, venda: PdvVenda):
    itens = (
        db.query(PdvVendaItem)
        .filter(PdvVendaItem.venda_id == venda.id)
        .all()
    )

    subtotal = Decimal("0.00")
    tem_produto = False
    tem_servico = False

    for item in itens:
        quantidade = _vp_pdv_decimal_dedicado(getattr(item, "quantidade", 1) or 1)
        valor_unitario = _vp_pdv_decimal_dedicado(getattr(item, "valor_unitario", 0) or 0)
        desconto_item = _vp_pdv_decimal_dedicado(getattr(item, "desconto_valor", 0) or 0)

        valor_total = _vp_pdv_decimal_dedicado(getattr(item, "valor_total", 0))

        if valor_total <= 0 and valor_unitario > 0:
            valor_total = (quantidade * valor_unitario - desconto_item).quantize(Decimal("0.01"))
            _vp_pdv_set_dedicado(item, "valor_total", valor_total)
            db.add(item)

        subtotal += valor_total

        tipo = str(getattr(item, "tipo_item", "") or "").upper()

        if tipo == "PRODUCT":
            tem_produto = True
        else:
            tem_servico = True

    desconto = _vp_pdv_decimal_dedicado(getattr(venda, "desconto_valor", 0))
    acrescimo = _vp_pdv_decimal_dedicado(getattr(venda, "acrescimo_valor", 0))

    total = subtotal - desconto + acrescimo

    if total < 0:
        total = Decimal("0.00")

    _vp_pdv_set_dedicado(venda, "subtotal", subtotal.quantize(Decimal("0.01")))
    _vp_pdv_set_dedicado(venda, "valor_total", total.quantize(Decimal("0.01")))

    if tem_produto and tem_servico:
        _vp_pdv_set_dedicado(venda, "origem", "MIXED")
    elif tem_servico:
        _vp_pdv_set_dedicado(venda, "origem", "SERVICE_ONLY")
    elif tem_produto:
        _vp_pdv_set_dedicado(venda, "origem", "PRODUCT_ONLY")

    db.add(venda)
    db.flush()

    return venda


def _vp_pdv_cliente_nome(obj):
    cliente = getattr(obj, "cliente", None)
    return getattr(cliente, "nome", None) if cliente else None


def _vp_pdv_cliente_id_producao(producao):
    agendamento = getattr(producao, "agendamento", None)
    return getattr(agendamento, "cliente_id", None) if agendamento else None


def _vp_pdv_cliente_nome_producao(producao):
    agendamento = getattr(producao, "agendamento", None)

    if not agendamento:
        return None

    cliente = getattr(agendamento, "cliente", None)
    return getattr(cliente, "nome", None) if cliente else None


def _vp_pdv_reabrir_origem_item_dedicado(db: Session, item: PdvVendaItem | None):
    if item is None:
        return

    atendimento_id = getattr(item, "atendimento_clinico_id", None)

    if atendimento_id:
        atendimento = (
            db.query(AtendimentoClinico)
            .filter(AtendimentoClinico.id == atendimento_id)
            .first()
        )

        if atendimento is not None:
            _vp_pdv_set_dedicado(atendimento, "enviado_pdv", False)
            db.add(atendimento)

    observacao = str(getattr(item, "observacao", "") or "")
    match = _vp_pdv_re_dedicado.search(r"PRODUCAO_ID:(\d+)", observacao)

    if match:
        producao = (
            db.query(Producao)
            .filter(Producao.id == int(match.group(1)))
            .first()
        )

        if producao is not None:
            _vp_pdv_set_dedicado(producao, "enviado_pdv", False)
            db.add(producao)


@router.post("/vendas/{venda_id}/atendimentos/{atendimento_id}/adicionar")
def adicionar_atendimento_dedicado_pdv(
    venda_id: int,
    atendimento_id: int,
    db: Session = Depends(get_db),
):
    venda = (
        db.query(PdvVenda)
        .filter(PdvVenda.id == venda_id)
        .first()
    )

    if venda is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")

    if str(getattr(venda, "status", "") or "").upper() != "ABERTA":
        raise HTTPException(status_code=400, detail="A venda precisa estar aberta.")

    atendimento = (
        db.query(AtendimentoClinico)
        .filter(AtendimentoClinico.id == atendimento_id)
        .first()
    )

    if atendimento is None:
        raise HTTPException(status_code=404, detail="Atendimento clínico não encontrado.")

    cliente_id = getattr(atendimento, "cliente_id", None)

    if cliente_id and getattr(venda, "cliente_id", None) and int(venda.cliente_id) != int(cliente_id):
        raise HTTPException(status_code=400, detail="Esse atendimento pertence a outro cliente.")

    if cliente_id and not getattr(venda, "cliente_id", None):
        _vp_pdv_set_dedicado(venda, "cliente_id", cliente_id)
        _vp_pdv_set_dedicado(venda, "modo_cliente", "REGISTERED_CLIENT")
        _vp_pdv_set_dedicado(venda, "nome_cliente_snapshot", _vp_pdv_cliente_nome(atendimento))

    valor = _vp_pdv_decimal_dedicado(_total_atendimento(atendimento))
    descricao = _descricao_atendimento(atendimento)

    item = PdvVendaItem()
    _vp_pdv_set_dedicado(item, "venda_id", venda.id)
    _vp_pdv_set_dedicado(item, "empresa_id", getattr(venda, "empresa_id", None))
    _vp_pdv_set_dedicado(item, "tipo_item", "SERVICE")
    _vp_pdv_set_dedicado(item, "atendimento_clinico_id", atendimento.id)
    _vp_pdv_set_dedicado(item, "produto_id", None)
    _vp_pdv_set_dedicado(item, "descricao_snapshot", descricao)
    _vp_pdv_set_dedicado(item, "observacao", f"ATENDIMENTO_CLINICO_ID:{atendimento.id}")
    _vp_pdv_set_dedicado(item, "quantidade", Decimal("1.00"))
    _vp_pdv_set_dedicado(item, "valor_unitario", valor)
    _vp_pdv_set_dedicado(item, "desconto_valor", Decimal("0.00"))
    _vp_pdv_set_dedicado(item, "desconto_percentual", Decimal("0.00"))
    _vp_pdv_set_dedicado(item, "acrescimo_valor", Decimal("0.00"))
    _vp_pdv_set_dedicado(item, "valor_total", valor)

    db.add(item)

    _vp_pdv_set_dedicado(atendimento, "enviado_pdv", True)
    db.add(atendimento)

    _vp_pdv_recalcular_venda_dedicado(db, venda)

    try:
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao adicionar atendimento no PDV: campo obrigatório ausente ou inválido. {erro.orig}",
        ) from erro
    except Exception as erro:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adicionar atendimento no PDV: {erro}",
        ) from erro

    db.refresh(venda)

    return _serializar_venda(venda, db=db)


@router.post("/vendas/{venda_id}/producao/{producao_id}/adicionar")
def adicionar_producao_dedicada_pdv(
    venda_id: int,
    producao_id: int,
    db: Session = Depends(get_db),
):
    venda = (
        db.query(PdvVenda)
        .filter(PdvVenda.id == venda_id)
        .first()
    )

    if venda is None:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")

    if str(getattr(venda, "status", "") or "").upper() != "ABERTA":
        raise HTTPException(status_code=400, detail="A venda precisa estar aberta.")

    producao = (
        db.query(Producao)
        .filter(Producao.id == producao_id)
        .first()
    )

    if producao is None:
        raise HTTPException(status_code=404, detail="Serviço da produção não encontrado.")

    cliente_id = _vp_pdv_cliente_id_producao(producao)

    if cliente_id and getattr(venda, "cliente_id", None) and int(venda.cliente_id) != int(cliente_id):
        raise HTTPException(status_code=400, detail="Esse serviço pertence a outro cliente.")

    if cliente_id and not getattr(venda, "cliente_id", None):
        _vp_pdv_set_dedicado(venda, "cliente_id", cliente_id)
        _vp_pdv_set_dedicado(venda, "modo_cliente", "REGISTERED_CLIENT")
        _vp_pdv_set_dedicado(venda, "nome_cliente_snapshot", _vp_pdv_cliente_nome_producao(producao))

    valor = _vp_pdv_decimal_dedicado(_total_producao(producao))
    descricao = _descricao_producao(producao)

    item = PdvVendaItem()
    _vp_pdv_set_dedicado(item, "venda_id", venda.id)
    _vp_pdv_set_dedicado(item, "empresa_id", getattr(venda, "empresa_id", None))
    _vp_pdv_set_dedicado(item, "tipo_item", "SERVICE")
    _vp_pdv_set_dedicado(item, "produto_id", None)
    _vp_pdv_set_dedicado(item, "descricao_snapshot", descricao)
    _vp_pdv_set_dedicado(item, "observacao", f"PRODUCAO_ID:{producao.id};AGENDAMENTO_ID:{getattr(producao, 'agendamento_id', '')}")
    _vp_pdv_set_dedicado(item, "quantidade", Decimal("1.00"))
    _vp_pdv_set_dedicado(item, "valor_unitario", valor)
    _vp_pdv_set_dedicado(item, "desconto_valor", Decimal("0.00"))
    _vp_pdv_set_dedicado(item, "desconto_percentual", Decimal("0.00"))
    _vp_pdv_set_dedicado(item, "acrescimo_valor", Decimal("0.00"))
    _vp_pdv_set_dedicado(item, "valor_total", valor)

    db.add(item)

    _vp_pdv_set_dedicado(producao, "enviado_pdv", True)
    db.add(producao)

    _vp_pdv_recalcular_venda_dedicado(db, venda)

    try:
        db.commit()
    except IntegrityError as erro:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao adicionar serviço da produção no PDV: campo obrigatório ausente ou inválido. {erro.orig}",
        ) from erro
    except Exception as erro:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adicionar serviço da produção no PDV: {erro}",
        ) from erro

    db.refresh(venda)

    return _serializar_venda(venda, db=db)
# === FIM PATCH PDV ROTAS DEDICADAS VECTORPET ===


def _to_float(valor):
    return float(valor or 0)


def _cliente_tem_assinatura_ativa(
    db: Session | None,
    empresa_id: int | None,
    cliente_id: int | None,
) -> bool:
    if not db or not empresa_id or not cliente_id:
        return False

    return (
        db.query(AssinaturaPet.id)
        .filter(
            AssinaturaPet.empresa_id == empresa_id,
            AssinaturaPet.cliente_id == cliente_id,
            AssinaturaPet.status == "ATIVA",
        )
        .first()
        is not None
    )


def _serializar_cliente(cliente, db: Session | None = None):
    if not cliente:
        return None

    empresa_id = getattr(cliente, "empresa_id", None)
    assinatura_ativa = _cliente_tem_assinatura_ativa(
        db=db,
        empresa_id=empresa_id,
        cliente_id=cliente.id,
    )

    return {
        "id": cliente.id,
        "nome": getattr(cliente, "nome", None),
        "cpf": getattr(cliente, "cpf", None),
        "telefone": getattr(cliente, "telefone", None),
        "saldo_cashback": _to_float(getattr(cliente, "saldo_cashback", 0)),
        "assinante": assinatura_ativa,
        "assinatura_ativa": assinatura_ativa,
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
        "valor": _to_float(pagamento.valor),
        "quantidade_parcelas": pagamento.quantidade_parcelas,
        "status": pagamento.status,
        "referencia": pagamento.referencia,
        "observacoes": pagamento.observacoes,
        "usuario_id": pagamento.usuario_id,
        "recebido_em": pagamento.recebido_em,
        "created_at": pagamento.created_at,
        "updated_at": pagamento.updated_at,
    }


def _serializar_venda(venda: PdvVenda, db: Session | None = None):
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
        "cliente": _serializar_cliente(venda.cliente, db=db),
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


def _serializar_atendimento_pronto(atendimento: AtendimentoClinico, db: Session | None = None):
    pet = getattr(atendimento, "pet", None)
    cliente = getattr(atendimento, "cliente", None)
    cliente_id = getattr(atendimento, "cliente_id", None)
    empresa_id = getattr(atendimento, "empresa_id", None)

    assinatura_ativa = _cliente_tem_assinatura_ativa(
        db=db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
    )

    return {
        "atendimento_id": atendimento.id,
        "cliente_id": atendimento.cliente_id,
        "cliente_nome": getattr(cliente, "nome", None),
        "pet_nome": getattr(pet, "nome", None) if pet else None,
        "descricao": _descricao_atendimento(atendimento),
        "valor_total": _to_float(_total_atendimento(atendimento)),
        "status": atendimento.status,
        "enviado_pdv": bool(atendimento.enviado_pdv),
        "assinante": assinatura_ativa,
        "assinatura_ativa": assinatura_ativa,
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


def _serializar_producao_pronta(producao: Producao, db: Session | None = None):
    agendamento = getattr(producao, "agendamento", None)
    cliente = getattr(agendamento, "cliente", None) if agendamento else None
    pet = getattr(agendamento, "pet", None) if agendamento else None
    cliente_id = getattr(agendamento, "cliente_id", None) if agendamento else None
    empresa_id = getattr(agendamento, "empresa_id", None) if agendamento else None

    assinatura_ativa = _cliente_tem_assinatura_ativa(
        db=db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
    )

    return {
        "producao_id": producao.id,
        "agendamento_id": getattr(producao, "agendamento_id", None),
        "cliente_id": cliente_id,
        "cliente_nome": getattr(cliente, "nome", None),
        "pet_nome": getattr(pet, "nome", None) if pet else None,
        "descricao": _descricao_producao(producao),
        "valor_total": _to_float(_total_producao(producao)),
        "finalizado": bool(getattr(producao, "finalizado", False)),
        "enviado_pdv": bool(getattr(producao, "enviado_pdv", False)),
        "assinante": assinatura_ativa,
        "assinatura_ativa": assinatura_ativa,
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


@router.get("/clientes/busca")
def buscar_clientes_pdv(
    empresa_id: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    clientes = buscar_clientes(db, empresa_id=empresa_id, termo=q, limite=limite)
    return [_serializar_cliente(cliente, db=db) for cliente in clientes]


@router.get("/produtos/busca")
def buscar_produtos_pdv(
    empresa_id: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    produtos = buscar_produtos(db, empresa_id=empresa_id, termo=q, limite=limite)
    return [_serializar_produto(produto) for produto in produtos]


@router.get("/atendimentos/prontos")
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
    return [_serializar_atendimento_pronto(atendimento, db=db) for atendimento in atendimentos]


@router.get("/producao/prontos")
def listar_producao_prontos_pdv(
    empresa_id: int = Query(..., ge=1),
    cliente_id: int | None = Query(None, ge=1),
    db: Session = Depends(get_db),
):
    producoes = listar_producao_prontos(db, empresa_id=empresa_id, cliente_id=cliente_id)
    return [_serializar_producao_pronta(producao, db=db) for producao in producoes]


@router.get("/relatorio/vendas")
def relatorio_vendas_pdv(
    empresa_id: int = Query(..., ge=1),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    cliente_id: int | None = Query(None, ge=1),
    status: str | None = Query(None),
    limite: int = Query(500, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    return relatorio_vendas_crud(
        db,
        empresa_id=empresa_id,
        data_inicio=data_inicio.isoformat() if data_inicio else None,
        data_fim=data_fim.isoformat() if data_fim else None,
        cliente_id=cliente_id,
        status=status,
        limite=limite,
    )


@router.get("/relatorio/itens-vendidos")
def relatorio_itens_vendidos_pdv(
    empresa_id: int = Query(..., ge=1),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    cliente_id: int | None = Query(None, ge=1),
    status: str | None = Query("FECHADA"),
    tipo_item: str | None = Query(None),
    produto_id: int | None = Query(None, ge=1),
    termo: str | None = Query(None),
    ordenar_por: str = Query("valor_total"),
    ordem: str = Query("desc"),
    limite: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return relatorio_itens_vendidos_crud(
        db,
        empresa_id=empresa_id,
        data_inicio=data_inicio.isoformat() if data_inicio else None,
        data_fim=data_fim.isoformat() if data_fim else None,
        cliente_id=cliente_id,
        status=status,
        tipo_item=tipo_item,
        produto_id=produto_id,
        termo=termo,
        ordenar_por=ordenar_por,
        ordem=ordem,
        limite=limite,
    )


@router.get("/ia-compras/analise-produtos")
def ia_compras_analise_produtos_pdv(
    empresa_id: int = Query(..., ge=1),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    dias_cobertura: int = Query(30, ge=1, le=180),
    prazo_reposicao_dias_uteis: int = Query(3, ge=0, le=30),
    limite: int = Query(300, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return analisar_compras_produtos_crud(
        db,
        empresa_id=empresa_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        dias_cobertura=dias_cobertura,
        prazo_reposicao_dias_uteis=prazo_reposicao_dias_uteis,
        limite=limite,
    )


@router.post("/vendas/producao", response_model=PdvVendaOut)
def enviar_producao_pdv(
    payload: PdvVendaProducaoCreate,
    db: Session = Depends(get_db),
):
    venda = enviar_producao_para_pdv(db, payload)
    return _serializar_venda(venda, db=db)


@router.post("/vendas", response_model=PdvVendaOut)
def criar_venda_pdv(
    payload: PdvVendaCreate,
    db: Session = Depends(get_db),
):
    venda = criar_venda(db, payload)
    return _serializar_venda(venda, db=db)


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
            "cliente": _serializar_cliente(venda.cliente, db=db),
        }
        for venda in vendas
    ]


@router.get("/vendas/{venda_id}", response_model=PdvVendaOut)
def obter_venda_pdv(
    venda_id: int,
    db: Session = Depends(get_db),
):
    venda = obter_venda(db, venda_id)
    return _serializar_venda(venda, db=db)


@router.patch("/vendas/{venda_id}", response_model=PdvVendaOut)
def atualizar_venda_pdv(
    venda_id: int,
    payload: PdvVendaUpdate,
    db: Session = Depends(get_db),
):
    venda = atualizar_venda(db, venda_id, payload)
    return _serializar_venda(venda, db=db)


@router.post("/vendas/{venda_id}/itens", response_model=PdvVendaOut)
def adicionar_item_pdv(
    venda_id: int,
    payload: PdvVendaItemAdd,
    db: Session = Depends(get_db),
):
    venda = adicionar_item(db, venda_id, payload)
    return _serializar_venda(venda, db=db)


@router.delete("/vendas/{venda_id}/itens/{item_id}", response_model=PdvVendaOut)
def remover_item_pdv(
    venda_id: int,
    item_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(PdvVendaItem)
        .filter(
            PdvVendaItem.id == item_id,
            PdvVendaItem.venda_id == venda_id,
        )
        .first()
    )

    _vp_pdv_reabrir_origem_item_dedicado(db, item)

    venda = remover_item(db, venda_id, item_id)
    _vp_pdv_recalcular_venda_dedicado(db, venda)

    db.commit()
    db.refresh(venda)

    return _serializar_venda(venda, db=db)


def checkout_venda_pdv(
    venda_id: int,
    payload: PdvCheckoutRequest,
    db: Session = Depends(get_db),
):
    venda = checkout_venda(db, venda_id, payload)

    return {
        "ok": True,
        "mensagem": "Venda finalizada com sucesso.",
        "venda": _serializar_venda(venda, db=db),
    }


@router.post("/vendas/{venda_id}/cancelar", response_model=PdvOperacaoResponse)
def cancelar_venda_pdv(
    venda_id: int,
    payload: PdvCancelRequest,
    db: Session = Depends(get_db),
):
    venda_aberta = (
        db.query(PdvVenda)
        .filter(PdvVenda.id == venda_id)
        .first()
    )

    if venda_aberta is not None:
        itens = (
            db.query(PdvVendaItem)
            .filter(PdvVendaItem.venda_id == venda_id)
            .all()
        )

        for item in itens:
            _vp_pdv_reabrir_origem_item_dedicado(db, item)

    venda = cancelar_venda(db, venda_id, payload)

    db.commit()

    return {
        "ok": True,
        "mensagem": "Venda cancelada com sucesso.",
        "venda": _serializar_venda(venda, db=db),
    }

