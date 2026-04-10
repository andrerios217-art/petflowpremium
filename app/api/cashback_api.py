from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud.cashback import (
    atualizar_configuracao_cashback,
    criar_ou_obter_configuracao_cashback,
    obter_configuracao_cashback,
    obter_extrato_cashback_cliente,
)
from app.schemas.cashback import (
    CashbackConfiguracaoCreate,
    CashbackConfiguracaoOut,
    CashbackConfiguracaoUpdate,
    CashbackExtratoResponse,
)

router = APIRouter(prefix="/api/cashback", tags=["Cashback"])


def _serializar_config(config):
    return {
        "id": config.id,
        "empresa_id": config.empresa_id,
        "ativo": bool(config.ativo),
        "percentual_cashback": config.percentual_cashback,
        "valor_minimo_venda": config.valor_minimo_venda,
        "dias_validade": config.dias_validade,
        "permite_uso_no_pdv": bool(config.permite_uso_no_pdv),
        "acumula_com_desconto": bool(config.acumula_com_desconto),
        "created_at": config.created_at,
        "updated_at": config.updated_at,
    }


def _serializar_lancamento(lanc):
    return {
        "id": lanc.id,
        "empresa_id": lanc.empresa_id,
        "cliente_id": lanc.cliente_id,
        "venda_id": lanc.venda_id,
        "tipo": lanc.tipo,
        "origem": lanc.origem,
        "valor": lanc.valor,
        "saldo_apos": lanc.saldo_apos,
        "expira_em": lanc.expira_em,
        "observacao": lanc.observacao,
        "created_at": lanc.created_at,
    }


@router.get("/configuracao", response_model=CashbackConfiguracaoOut | None)
def obter_configuracao_cashback_api(
    empresa_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    config = obter_configuracao_cashback(db, empresa_id)
    if not config:
        return None
    return _serializar_config(config)


@router.post("/configuracao", response_model=CashbackConfiguracaoOut)
def criar_configuracao_cashback_api(
    payload: CashbackConfiguracaoCreate,
    db: Session = Depends(get_db),
):
    criar_ou_obter_configuracao_cashback(
        db,
        empresa_id=payload.empresa_id,
    )

    config = atualizar_configuracao_cashback(
        db,
        empresa_id=payload.empresa_id,
        ativo=payload.ativo,
        percentual_cashback=payload.percentual_cashback,
        valor_minimo_venda=payload.valor_minimo_venda,
        dias_validade=payload.dias_validade,
        permite_uso_no_pdv=payload.permite_uso_no_pdv,
        acumula_com_desconto=payload.acumula_com_desconto,
    )
    return _serializar_config(config)


@router.put("/configuracao/{empresa_id}", response_model=CashbackConfiguracaoOut)
def atualizar_configuracao_cashback_api(
    empresa_id: int,
    payload: CashbackConfiguracaoUpdate,
    db: Session = Depends(get_db),
):
    config = atualizar_configuracao_cashback(
        db,
        empresa_id=empresa_id,
        ativo=payload.ativo,
        percentual_cashback=payload.percentual_cashback,
        valor_minimo_venda=payload.valor_minimo_venda,
        dias_validade=payload.dias_validade,
        permite_uso_no_pdv=payload.permite_uso_no_pdv,
        acumula_com_desconto=payload.acumula_com_desconto,
    )
    return _serializar_config(config)


@router.get("/clientes/{cliente_id}/extrato", response_model=CashbackExtratoResponse)
def obter_extrato_cashback_cliente_api(
    cliente_id: int,
    empresa_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    data = obter_extrato_cashback_cliente(
        db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
    )
    return {
        "cliente_id": data["cliente_id"],
        "saldo_atual": data["saldo_atual"],
        "lancamentos": [_serializar_lancamento(l) for l in data["lancamentos"]],
    }