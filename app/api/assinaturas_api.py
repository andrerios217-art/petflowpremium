from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_actor, get_db, get_empresa_id_atual
from app.crud.assinatura import (
    atualizar_assinatura,
    buscar_assinatura_por_id,
    cancelar_assinatura,
    criar_assinatura,
    listar_assinaturas,
    listar_consumos_assinatura,
    registrar_consumo_assinatura,
)
from app.schemas.assinatura import (
    AssinaturaConsumoOperacaoResponse,
    AssinaturaOperacaoResponse,
    AssinaturaPetConsumoCreate,
    AssinaturaPetConsumoOut,
    AssinaturaPetCreate,
    AssinaturaPetOut,
    AssinaturaPetUpdate,
)

router = APIRouter(prefix="/assinaturas", tags=["assinaturas"])


@router.get("", response_model=list[AssinaturaPetOut], include_in_schema=False)
@router.get("/", response_model=list[AssinaturaPetOut])
def listar_assinaturas_route(
    status: str | None = Query(default=None),
    cliente_id: int | None = Query(default=None),
    pet_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
):
    return listar_assinaturas(
        db=db,
        empresa_id=empresa_id,
        status=status,
        cliente_id=cliente_id,
        pet_id=pet_id,
    )


@router.get("/{assinatura_id}", response_model=AssinaturaPetOut)
def obter_assinatura_route(
    assinatura_id: int,
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
):
    assinatura = buscar_assinatura_por_id(
        db=db,
        assinatura_id=assinatura_id,
        empresa_id=empresa_id,
    )
    if not assinatura:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")

    return assinatura


@router.post("", response_model=AssinaturaOperacaoResponse, include_in_schema=False)
@router.post("/", response_model=AssinaturaOperacaoResponse)
def criar_assinatura_route(
    payload: AssinaturaPetCreate,
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
):
    try:
        payload_com_empresa = AssinaturaPetCreate(
            empresa_id=empresa_id,
            cliente_id=payload.cliente_id,
            pet_id=payload.pet_id,
            data_inicio=payload.data_inicio,
            data_fim=payload.data_fim,
            dia_fechamento_ciclo=payload.dia_fechamento_ciclo,
            usar_limite_ate_dia_28=payload.usar_limite_ate_dia_28,
            nao_cumulativa=payload.nao_cumulativa,
            ativa_renovacao=payload.ativa_renovacao,
            origem=payload.origem,
            observacoes=payload.observacoes,
            contrato_externo_id=payload.contrato_externo_id,
            itens=payload.itens,
        )

        assinatura = criar_assinatura(db=db, data=payload_com_empresa)
        return AssinaturaOperacaoResponse(
            ok=True,
            mensagem="Assinatura criada com sucesso.",
            assinatura=assinatura,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.put("/{assinatura_id}", response_model=AssinaturaOperacaoResponse)
def atualizar_assinatura_route(
    assinatura_id: int,
    payload: AssinaturaPetUpdate,
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
):
    try:
        assinatura = atualizar_assinatura(
            db=db,
            assinatura_id=assinatura_id,
            empresa_id=empresa_id,
            data=payload,
        )
        return AssinaturaOperacaoResponse(
            ok=True,
            mensagem="Assinatura atualizada com sucesso.",
            assinatura=assinatura,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/{assinatura_id}/cancelar", response_model=AssinaturaOperacaoResponse)
def cancelar_assinatura_route(
    assinatura_id: int,
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
):
    try:
        assinatura = cancelar_assinatura(
            db=db,
            assinatura_id=assinatura_id,
            empresa_id=empresa_id,
        )
        return AssinaturaOperacaoResponse(
            ok=True,
            mensagem="Assinatura cancelada com sucesso.",
            assinatura=assinatura,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get(
    "/{assinatura_id}/consumos",
    response_model=list[AssinaturaPetConsumoOut],
)
def listar_consumos_assinatura_route(
    assinatura_id: int,
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
):
    assinatura = buscar_assinatura_por_id(
        db=db,
        assinatura_id=assinatura_id,
        empresa_id=empresa_id,
    )
    if not assinatura:
        raise HTTPException(status_code=404, detail="Assinatura não encontrada.")

    return listar_consumos_assinatura(
        db=db,
        assinatura_id=assinatura_id,
        empresa_id=empresa_id,
    )


@router.post(
    "/{assinatura_id}/consumos",
    response_model=AssinaturaConsumoOperacaoResponse,
)
def registrar_consumo_assinatura_route(
    assinatura_id: int,
    payload: AssinaturaPetConsumoCreate,
    db: Session = Depends(get_db),
    empresa_id: int = Depends(get_empresa_id_atual),
    current_actor: dict = Depends(get_current_actor),
):
    if payload.assinatura_id != assinatura_id:
        raise HTTPException(
            status_code=400,
            detail="O ID da assinatura no corpo difere do ID da rota.",
        )

    if payload.empresa_id != empresa_id:
        raise HTTPException(
            status_code=400,
            detail="Empresa do consumo difere da empresa do usuário logado.",
        )

    try:
        consumo = registrar_consumo_assinatura(db=db, data=payload)
        return AssinaturaConsumoOperacaoResponse(
            ok=True,
            mensagem="Consumo registrado com sucesso.",
            consumo=consumo,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e