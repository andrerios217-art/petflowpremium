from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import configuracao as configuracao_crud


router = APIRouter(prefix="/configuracoes", tags=["configuracoes"])


CHAVE_DESCONTO_ASSINANTE = "desconto_assinante_percentual"


class DescontoAssinantePayload(BaseModel):
    empresa_id: int = Field(..., gt=0)
    percentual: float = Field(..., ge=0, le=100)


class DescontoAssinanteOut(BaseModel):
    empresa_id: int
    percentual: float


@router.get("/desconto-assinante", response_model=DescontoAssinanteOut)
def obter_desconto_assinante(
    empresa_id: int = Query(..., gt=0),
    db: Session = Depends(get_db),
):
    valor = configuracao_crud.get_valor(
        db,
        empresa_id=empresa_id,
        chave=CHAVE_DESCONTO_ASSINANTE,
        default="0",
    )

    try:
        percentual = float(valor)
    except (TypeError, ValueError):
        percentual = 0.0

    return {
        "empresa_id": empresa_id,
        "percentual": percentual,
    }


@router.post("/desconto-assinante", response_model=DescontoAssinanteOut)
def salvar_desconto_assinante(
    payload: DescontoAssinantePayload,
    db: Session = Depends(get_db),
):
    percentual = round(float(payload.percentual), 2)

    if percentual < 0 or percentual > 100:
        raise HTTPException(
            status_code=400,
            detail="O percentual de desconto deve estar entre 0 e 100.",
        )

    configuracao_crud.upsert(
        db,
        empresa_id=payload.empresa_id,
        chave=CHAVE_DESCONTO_ASSINANTE,
        valor=str(percentual),
    )

    return {
        "empresa_id": payload.empresa_id,
        "percentual": percentual,
    }