from decimal import Decimal
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.comissao_configuracao import ComissaoConfiguracao
from app.models.comissao_faixa import ComissaoFaixa
from app.models.comissao_fechamento import ComissaoFechamento
from app.models.comissao_lancamento import ComissaoLancamento
from app.models.funcionario import Funcionario
from app.schemas.comissao import ComissaoConfiguracaoOut, ComissaoConfiguracaoUpsert

router = APIRouter(prefix="/api/comissao", tags=["Comissão"])


class AcaoComissao(BaseModel):
    empresa_id: int
    funcionario_id: int
    competencia: str
    motivo: str | None = None


def _agora_utc():
    return datetime.now(timezone.utc)


def _parse_competencia(competencia: str) -> date:
    try:
        ano, mes = competencia.split("-")
        return date(int(ano), int(mes), 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Competência inválida. Use YYYY-MM.")


def _ordenar_faixas(faixas):
    return sorted(faixas, key=lambda faixa: int(faixa.pontos_min))


def _validar_faixas(faixas):
    if not faixas:
        raise HTTPException(status_code=400, detail="Adicione ao menos uma faixa de comissão.")

    faixas_ordenadas = _ordenar_faixas(faixas)

    if int(faixas_ordenadas[0].pontos_min) != 0:
        raise HTTPException(status_code=400, detail="A primeira faixa deve começar em 0 pontos.")

    faixa_aberta_encontrada = False

    for index, faixa in enumerate(faixas_ordenadas):
        pontos_min = int(faixa.pontos_min)
        pontos_max = None if faixa.pontos_max is None else int(faixa.pontos_max)
        valor_reais = Decimal(faixa.valor_reais)

        if pontos_min < 0:
            raise HTTPException(status_code=400, detail=f"A faixa {index + 1} possui início inválido.")

        if pontos_max is not None and pontos_max < pontos_min:
            raise HTTPException(status_code=400, detail=f"A faixa {index + 1} possui fim inválido.")

        if valor_reais < 0:
            raise HTTPException(status_code=400, detail=f"A faixa {index + 1} possui valor em R$ inválido.")

        if pontos_max is None:
            if faixa_aberta_encontrada:
                raise HTTPException(status_code=400, detail="Só pode existir uma faixa aberta.")
            faixa_aberta_encontrada = True

            if index != len(faixas_ordenadas) - 1:
                raise HTTPException(status_code=400, detail="A faixa aberta deve ser a última.")

        if index > 0:
            faixa_anterior = faixas_ordenadas[index - 1]
            max_anterior = None if faixa_anterior.pontos_max is None else int(faixa_anterior.pontos_max)

            if max_anterior is None:
                raise HTTPException(status_code=400, detail="Não é permitido adicionar faixa após faixa aberta.")

            if pontos_min != max_anterior + 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"As faixas devem ser contínuas. A faixa {index + 1} deve começar em {max_anterior + 1}.",
                )

    return faixas_ordenadas


def _serializar_configuracao(config: ComissaoConfiguracao):
    return {
        "id": config.id,
        "empresa_id": config.empresa_id,
        "pontos_banho": config.pontos_banho,
        "pontos_tosa": config.pontos_tosa,
        "pontos_finalizacao": config.pontos_finalizacao,
        "dias_trabalhados_mes": config.dias_trabalhados_mes,
        "responsavel_aprovacao": config.responsavel_aprovacao,
        "faixas": [
            {
                "id": faixa.id,
                "ordem": faixa.ordem,
                "pontos_min": faixa.pontos_min,
                "pontos_max": faixa.pontos_max,
                "valor_reais": float(faixa.valor_reais or 0),
                "ativo": faixa.ativo,
            }
            for faixa in sorted(config.faixas, key=lambda item: item.ordem)
        ],
    }


def _valor_faixa(config: ComissaoConfiguracao | None, pontos: int) -> float:
    if not config:
        return 0.0

    faixas_ordenadas = sorted(config.faixas, key=lambda item: item.ordem)

    for faixa in faixas_ordenadas:
        minimo = int(faixa.pontos_min)
        maximo = None if faixa.pontos_max is None else int(faixa.pontos_max)

        if pontos >= minimo and (maximo is None or pontos <= maximo):
            return float(faixa.valor_reais or 0)

    return 0.0


def _fechamento_existente(db: Session, empresa_id: int, funcionario_id: int, competencia_data: date):
    return (
        db.query(ComissaoFechamento)
        .filter(
            ComissaoFechamento.empresa_id == empresa_id,
            ComissaoFechamento.funcionario_id == funcionario_id,
            ComissaoFechamento.competencia == competencia_data,
        )
        .first()
    )


def _resumir_status_funcionario(lancamentos: list[ComissaoLancamento], fechamento: ComissaoFechamento | None) -> str:
    if fechamento:
        return "FECHADO"

    statuses = {str(item.status or "").upper() for item in lancamentos}

    if statuses == {"APROVADO"}:
        return "APROVADO"

    if "REJEITADO" in statuses:
        return "REJEITADO"

    if "APROVADO" in statuses and "CAPTURADO" in statuses:
        return "PARCIAL"

    if statuses:
        return sorted(statuses)[0]

    return "CAPTURADO"


@router.get("/configuracao", response_model=ComissaoConfiguracaoOut)
def obter_configuracao_comissao(
    empresa_id: int = Query(..., ge=1),
    db: Session = Depends(get_db),
):
    config = (
        db.query(ComissaoConfiguracao)
        .filter(ComissaoConfiguracao.empresa_id == empresa_id)
        .first()
    )

    if not config:
        return {
            "empresa_id": empresa_id,
            "pontos_banho": 0,
            "pontos_tosa": 0,
            "pontos_finalizacao": 0,
            "dias_trabalhados_mes": 26,
            "responsavel_aprovacao": None,
            "faixas": [
                {
                    "ordem": 1,
                    "pontos_min": 0,
                    "pontos_max": 9,
                    "valor_reais": 0,
                    "ativo": True,
                }
            ],
        }

    return _serializar_configuracao(config)


@router.post("/configuracao", response_model=ComissaoConfiguracaoOut)
def salvar_configuracao_comissao(
    payload: ComissaoConfiguracaoUpsert,
    db: Session = Depends(get_db),
):
    faixas_ordenadas = _validar_faixas(payload.faixas)

    config = (
        db.query(ComissaoConfiguracao)
        .filter(ComissaoConfiguracao.empresa_id == payload.empresa_id)
        .first()
    )

    if not config:
        config = ComissaoConfiguracao(empresa_id=payload.empresa_id)
        db.add(config)
        db.flush()

    config.pontos_banho = payload.pontos_banho
    config.pontos_tosa = payload.pontos_tosa
    config.pontos_finalizacao = payload.pontos_finalizacao
    config.dias_trabalhados_mes = payload.dias_trabalhados_mes
    config.responsavel_aprovacao = payload.responsavel_aprovacao

    for faixa_existente in list(config.faixas):
        db.delete(faixa_existente)

    db.flush()

    for index, faixa in enumerate(faixas_ordenadas, start=1):
        nova_faixa = ComissaoFaixa(
            configuracao_id=config.id,
            ordem=index,
            pontos_min=int(faixa.pontos_min),
            pontos_max=None if faixa.pontos_max is None else int(faixa.pontos_max),
            valor_reais=Decimal(faixa.valor_reais),
            ativo=True,
        )
        db.add(nova_faixa)

    db.commit()
    db.refresh(config)

    config = (
        db.query(ComissaoConfiguracao)
        .filter(ComissaoConfiguracao.empresa_id == payload.empresa_id)
        .first()
    )

    return _serializar_configuracao(config)


@router.get("/lancamentos")
def listar_lancamentos_comissao(
    empresa_id: int = Query(..., ge=1),
    competencia: str | None = Query(default=None),
    funcionario_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
):
    competencia_data = _parse_competencia(competencia) if competencia else None

    query = (
        db.query(ComissaoLancamento)
        .join(Funcionario, Funcionario.id == ComissaoLancamento.funcionario_id)
        .filter(ComissaoLancamento.empresa_id == empresa_id)
        .order_by(ComissaoLancamento.created_at.desc(), ComissaoLancamento.id.desc())
    )

    if competencia_data:
        query = query.filter(ComissaoLancamento.competencia == competencia_data)

    if funcionario_id:
        query = query.filter(ComissaoLancamento.funcionario_id == funcionario_id)

    lancamentos = query.all()

    agrupado_por_funcionario = {}

    for item in lancamentos:
        chave = item.funcionario_id
        fechamento = _fechamento_existente(db, empresa_id, item.funcionario_id, item.competencia)

        if chave not in agrupado_por_funcionario:
            agrupado_por_funcionario[chave] = {
                "funcionario_id": item.funcionario_id,
                "funcionario_nome": item.funcionario.nome if item.funcionario else None,
                "competencia": item.competencia.isoformat() if item.competencia else None,
                "status": item.status,
                "pontos_total": 0,
                "valor_estimado": 0.0,
                "fechado": bool(fechamento),
                "valor_fechado": float(fechamento.valor_final) if fechamento else None,
                "lancamentos": [],
            }

        agrupado_por_funcionario[chave]["pontos_total"] += int(item.pontos or 0)
        agrupado_por_funcionario[chave]["lancamentos"].append({
            "id": item.id,
            "producao_id": item.producao_id,
            "agendamento_id": item.agendamento_id,
            "etapa": item.etapa,
            "pontos": int(item.pontos or 0),
            "status": item.status,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    config = (
        db.query(ComissaoConfiguracao)
        .filter(ComissaoConfiguracao.empresa_id == empresa_id)
        .first()
    )

    for _, grupo in agrupado_por_funcionario.items():
        grupo["valor_estimado"] = _valor_faixa(config, grupo["pontos_total"]) if config else 0.0
        grupo["status"] = _resumir_status_funcionario(
            [
                type("Obj", (), {"status": lanc["status"]})()
                for lanc in grupo["lancamentos"]
            ],
            _fechamento_existente(
                db,
                empresa_id,
                grupo["funcionario_id"],
                _parse_competencia(grupo["competencia"][:7]) if grupo["competencia"] else competencia_data
            ) if grupo["competencia"] else None,
        )

    return {
        "empresa_id": empresa_id,
        "competencia": competencia,
        "funcionarios": list(agrupado_por_funcionario.values()),
    }


@router.post("/aprovar")
def aprovar_comissao(payload: AcaoComissao, db: Session = Depends(get_db)):
    competencia_data = _parse_competencia(payload.competencia)

    fechamento = _fechamento_existente(
        db=db,
        empresa_id=payload.empresa_id,
        funcionario_id=payload.funcionario_id,
        competencia_data=competencia_data,
    )
    if fechamento:
        raise HTTPException(status_code=400, detail="Esta comissão já foi fechada e não pode mais ser alterada.")

    lancamentos = (
        db.query(ComissaoLancamento)
        .filter(
            ComissaoLancamento.empresa_id == payload.empresa_id,
            ComissaoLancamento.funcionario_id == payload.funcionario_id,
            ComissaoLancamento.competencia == competencia_data,
        )
        .all()
    )

    if not lancamentos:
        raise HTTPException(status_code=404, detail="Nenhum lançamento encontrado para aprovação.")

    if any(str(item.status or "").upper() == "FECHADO" for item in lancamentos):
        raise HTTPException(status_code=400, detail="Existem lançamentos fechados e eles não podem ser alterados.")

    if all(str(item.status or "").upper() == "APROVADO" for item in lancamentos):
        raise HTTPException(status_code=400, detail="Todos os lançamentos deste funcionário já foram aprovados.")

    for item in lancamentos:
        item.status = "APROVADO"

    db.commit()
    return {"ok": True}


@router.post("/rejeitar")
def rejeitar_comissao(payload: AcaoComissao, db: Session = Depends(get_db)):
    competencia_data = _parse_competencia(payload.competencia)

    fechamento = _fechamento_existente(
        db=db,
        empresa_id=payload.empresa_id,
        funcionario_id=payload.funcionario_id,
        competencia_data=competencia_data,
    )
    if fechamento:
        raise HTTPException(status_code=400, detail="Esta comissão já foi fechada e não pode mais ser alterada.")

    lancamentos = (
        db.query(ComissaoLancamento)
        .filter(
            ComissaoLancamento.empresa_id == payload.empresa_id,
            ComissaoLancamento.funcionario_id == payload.funcionario_id,
            ComissaoLancamento.competencia == competencia_data,
        )
        .all()
    )

    if not lancamentos:
        raise HTTPException(status_code=404, detail="Nenhum lançamento encontrado para rejeição.")

    if any(str(item.status or "").upper() == "FECHADO" for item in lancamentos):
        raise HTTPException(status_code=400, detail="Existem lançamentos fechados e eles não podem ser alterados.")

    if any(str(item.status or "").upper() == "APROVADO" for item in lancamentos):
        raise HTTPException(
            status_code=400,
            detail="Após aprovado, este lançamento não pode ser rejeitado.",
        )

    for item in lancamentos:
        item.status = "REJEITADO"

    db.commit()
    return {"ok": True}


@router.post("/fechar")
def fechar_comissao(payload: AcaoComissao, db: Session = Depends(get_db)):
    competencia_data = _parse_competencia(payload.competencia)

    fechamento_existente = _fechamento_existente(
        db=db,
        empresa_id=payload.empresa_id,
        funcionario_id=payload.funcionario_id,
        competencia_data=competencia_data,
    )
    if fechamento_existente:
        raise HTTPException(status_code=400, detail="A comissão desta competência já foi fechada.")

    lancamentos = (
        db.query(ComissaoLancamento)
        .filter(
            ComissaoLancamento.empresa_id == payload.empresa_id,
            ComissaoLancamento.funcionario_id == payload.funcionario_id,
            ComissaoLancamento.competencia == competencia_data,
        )
        .all()
    )

    if not lancamentos:
        raise HTTPException(status_code=404, detail="Nenhum lançamento encontrado para fechamento.")

    if any(str(item.status or "").upper() != "APROVADO" for item in lancamentos):
        raise HTTPException(
            status_code=400,
            detail="Todos os lançamentos precisam estar aprovados antes do fechamento.",
        )

    config = (
        db.query(ComissaoConfiguracao)
        .filter(ComissaoConfiguracao.empresa_id == payload.empresa_id)
        .first()
    )

    pontos_total = sum(int(item.pontos or 0) for item in lancamentos)
    valor_final = _valor_faixa(config, pontos_total)

    fechamento = ComissaoFechamento(
        empresa_id=payload.empresa_id,
        funcionario_id=payload.funcionario_id,
        competencia=competencia_data,
        pontos_total=pontos_total,
        valor_final=Decimal(str(valor_final)),
        status="FECHADO",
        aprovado_por=None,
        aprovado_em=_agora_utc(),
    )
    db.add(fechamento)

    for item in lancamentos:
        item.status = "FECHADO"

    db.commit()

    return {
        "ok": True,
        "funcionario_id": payload.funcionario_id,
        "competencia": competencia_data.isoformat(),
        "pontos_total": pontos_total,
        "valor_final": valor_final,
        "status": "FECHADO",
    }