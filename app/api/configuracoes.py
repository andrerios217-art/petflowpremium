from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import configuracao as configuracao_crud


router = APIRouter(prefix="/configuracoes", tags=["configuracoes"])


CHAVE_DESCONTO_ASSINANTE_PRODUTOS = "desconto_assinante_produtos_percentual"
CHAVE_DESCONTO_ASSINANTE_SERVICOS = "desconto_assinante_servicos_percentual"


class DescontoAssinantePayload(BaseModel):
    empresa_id: int = Field(..., gt=0)
    percentual_produtos: float = Field(default=0, ge=0, le=100)
    percentual_servicos: float = Field(default=0, ge=0, le=100)


class DescontoAssinanteOut(BaseModel):
    empresa_id: int
    percentual_produtos: float
    percentual_servicos: float


def _to_float_percentual(valor, default: float = 0.0) -> float:
    try:
        percentual = float(valor)
    except (TypeError, ValueError):
        percentual = default

    if percentual < 0:
        return 0.0

    if percentual > 100:
        return 100.0

    return round(percentual, 2)


@router.get("/desconto-assinante", response_model=DescontoAssinanteOut)
def obter_desconto_assinante(
    empresa_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    valor_produtos = configuracao_crud.get_valor(
        db,
        empresa_id=empresa_id,
        chave=CHAVE_DESCONTO_ASSINANTE_PRODUTOS,
        default="0",
    )

    valor_servicos = configuracao_crud.get_valor(
        db,
        empresa_id=empresa_id,
        chave=CHAVE_DESCONTO_ASSINANTE_SERVICOS,
        default="0",
    )

    return {
        "empresa_id": empresa_id,
        "percentual_produtos": _to_float_percentual(valor_produtos),
        "percentual_servicos": _to_float_percentual(valor_servicos),
    }


@router.post("/desconto-assinante", response_model=DescontoAssinanteOut)
def salvar_desconto_assinante(
    payload: DescontoAssinantePayload,
    db: Session = Depends(get_db),
):
    percentual_produtos = _to_float_percentual(payload.percentual_produtos)
    percentual_servicos = _to_float_percentual(payload.percentual_servicos)

    if percentual_produtos < 0 or percentual_produtos > 100:
        raise HTTPException(
            status_code=400,
            detail="O percentual de desconto para produtos deve estar entre 0 e 100.",
        )

    if percentual_servicos < 0 or percentual_servicos > 100:
        raise HTTPException(
            status_code=400,
            detail="O percentual de desconto para serviços deve estar entre 0 e 100.",
        )

    configuracao_crud.upsert(
        db,
        empresa_id=payload.empresa_id,
        chave=CHAVE_DESCONTO_ASSINANTE_PRODUTOS,
        valor=str(percentual_produtos),
    )

    configuracao_crud.upsert(
        db,
        empresa_id=payload.empresa_id,
        chave=CHAVE_DESCONTO_ASSINANTE_SERVICOS,
        valor=str(percentual_servicos),
    )

    return {
        "empresa_id": payload.empresa_id,
        "percentual_produtos": percentual_produtos,
        "percentual_servicos": percentual_servicos,
    }