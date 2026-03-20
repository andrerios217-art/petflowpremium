from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud.caixa import (
    abrir_caixa,
    atualizar_status_divergencia,
    buscar_operadores_caixa,
    calcular_resumo_financeiro_caixa,
    fechar_caixa,
    listar_caixas,
    listar_divergencias,
    obter_caixa,
    obter_caixa_aberto,
    obter_divergencia,
    registrar_sangria,
    registrar_suprimento,
)
from app.schemas.caixa import (
    CaixaDivergenciaAtualizarStatusRequest,
    CaixaDivergenciaOut,
    CaixaOperacaoResponse,
    CaixaOperadorBuscaOut,
    CaixaResumoFinanceiroOut,
    CaixaSangriaRequest,
    CaixaSessaoAberturaRequest,
    CaixaSessaoFechamentoRequest,
    CaixaSessaoOut,
    CaixaSessaoResumoOut,
    CaixaSuprimentoRequest,
)

router = APIRouter(prefix="/api/caixa", tags=["Caixa"])


@router.get("/operadores", response_model=list[CaixaOperadorBuscaOut])
def buscar_operadores_caixa_api(
    empresa_id: int = Query(..., ge=1),
    q: str = Query(..., min_length=1),
    limite: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return buscar_operadores_caixa(
        db,
        empresa_id=empresa_id,
        termo=q,
        limite=limite,
    )


@router.get("/atual", response_model=CaixaSessaoOut | None)
def obter_caixa_atual(
    empresa_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    return obter_caixa_aberto(db, empresa_id)


@router.get("/sessoes", response_model=list[CaixaSessaoResumoOut])
def listar_sessoes_caixa(
    empresa_id: int = Query(..., ge=1),
    status: str | None = Query(None),
    limite: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return listar_caixas(
        db,
        empresa_id=empresa_id,
        status=status,
        limite=limite,
    )


@router.get("/sessoes/{caixa_sessao_id}", response_model=CaixaSessaoOut)
def obter_sessao_caixa(
    caixa_sessao_id: int,
    db: Session = Depends(get_db),
):
    return obter_caixa(db, caixa_sessao_id)


@router.post("/abrir", response_model=CaixaOperacaoResponse)
def abrir_caixa_api(
    payload: CaixaSessaoAberturaRequest,
    db: Session = Depends(get_db),
):
    caixa_sessao, divergencia = abrir_caixa(db, payload)

    mensagem = "Caixa aberto com sucesso."
    if divergencia:
        mensagem = "Caixa aberto com divergência registrada."

    return {
        "ok": True,
        "mensagem": mensagem,
        "caixa_sessao": caixa_sessao,
        "divergencia": divergencia,
    }


@router.post("/sessoes/{caixa_sessao_id}/fechar", response_model=CaixaOperacaoResponse)
def fechar_caixa_api(
    caixa_sessao_id: int,
    payload: CaixaSessaoFechamentoRequest,
    db: Session = Depends(get_db),
):
    caixa_sessao, divergencia = fechar_caixa(db, caixa_sessao_id, payload)

    mensagem = "Caixa fechado com sucesso."
    if divergencia:
        mensagem = "Caixa fechado com divergência registrada."

    return {
        "ok": True,
        "mensagem": mensagem,
        "caixa_sessao": caixa_sessao,
        "divergencia": divergencia,
    }


@router.post("/sangria", response_model=CaixaOperacaoResponse)
def registrar_sangria_api(
    payload: CaixaSangriaRequest,
    db: Session = Depends(get_db),
):
    caixa_sessao, _movimento = registrar_sangria(db, payload)
    return {
        "ok": True,
        "mensagem": "Sangria registrada com sucesso.",
        "caixa_sessao": caixa_sessao,
        "divergencia": None,
    }


@router.post("/suprimento", response_model=CaixaOperacaoResponse)
def registrar_suprimento_api(
    payload: CaixaSuprimentoRequest,
    db: Session = Depends(get_db),
):
    caixa_sessao, _movimento = registrar_suprimento(db, payload)
    return {
        "ok": True,
        "mensagem": "Suprimento registrado com sucesso.",
        "caixa_sessao": caixa_sessao,
        "divergencia": None,
    }


@router.get("/sessoes/{caixa_sessao_id}/resumo", response_model=CaixaResumoFinanceiroOut)
def obter_resumo_caixa_api(
    caixa_sessao_id: int,
    db: Session = Depends(get_db),
):
    caixa_sessao = obter_caixa(db, caixa_sessao_id)
    return calcular_resumo_financeiro_caixa(caixa_sessao)


@router.get("/divergencias", response_model=list[CaixaDivergenciaOut])
def listar_divergencias_api(
    empresa_id: int = Query(..., ge=1),
    status: str | None = Query(None),
    usuario_responsavel_id: int | None = Query(None, ge=1),
    limite: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return listar_divergencias(
        db,
        empresa_id=empresa_id,
        status=status,
        usuario_responsavel_id=usuario_responsavel_id,
        limite=limite,
    )


@router.get("/divergencias/{divergencia_id}", response_model=CaixaDivergenciaOut)
def obter_divergencia_api(
    divergencia_id: int,
    db: Session = Depends(get_db),
):
    return obter_divergencia(db, divergencia_id)


@router.post("/divergencias/{divergencia_id}/status", response_model=CaixaDivergenciaOut)
def atualizar_status_divergencia_api(
    divergencia_id: int,
    payload: CaixaDivergenciaAtualizarStatusRequest,
    db: Session = Depends(get_db),
):
    return atualizar_status_divergencia(db, divergencia_id, payload)