from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.producao import Producao
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico


COLUNAS_VALIDAS = [
    "PRE_BANHO",
    "PRE_TOSA",
    "BANHO",
    "FINALIZACAO_BANHO",
    "TOSA",
    "SECAGEM",
]


def _query_base(db: Session):
    return (
        db.query(Producao)
        .options(
            joinedload(Producao.funcionario),
            joinedload(Producao.agendamento).joinedload(Agendamento.pet),
            joinedload(Producao.agendamento).joinedload(Agendamento.cliente),
            joinedload(Producao.agendamento).joinedload(Agendamento.funcionario),
            joinedload(Producao.agendamento)
            .joinedload(Agendamento.servicos_agendamento)
            .joinedload(AgendamentoServico.servico),
        )
    )


def agendamento_tem_tosa(agendamento: Agendamento) -> bool:
    for item in agendamento.servicos_agendamento:
        nome = (item.servico.nome or "").strip().lower() if item.servico else ""
        if "tosa" in nome:
            return True
    return False


def listar_cards(db: Session, empresa_id: int):
    return (
        _query_base(db)
        .join(Producao.agendamento)
        .filter(
            Agendamento.empresa_id == empresa_id,
            Producao.finalizado.is_(False)
        )
        .order_by(Producao.created_at.asc())
        .all()
    )


def buscar_por_agendamento(db: Session, agendamento_id: int):
    return (
        _query_base(db)
        .filter(Producao.agendamento_id == agendamento_id)
        .first()
    )


def buscar_por_id(db: Session, producao_id: int):
    return (
        _query_base(db)
        .filter(Producao.id == producao_id)
        .first()
    )


def criar_ordem_se_nao_existir(db: Session, agendamento: Agendamento):
    ordem_existente = buscar_por_agendamento(db, agendamento.id)
    if ordem_existente:
        return ordem_existente

    ordem = Producao(
        agendamento_id=agendamento.id,
        coluna="PRE_BANHO",
        etapa_status="AGUARDANDO",
        prioridade=(agendamento.prioridade or "NORMAL"),
        finalizado=False,
    )
    db.add(ordem)
    db.commit()
    db.refresh(ordem)

    return buscar_por_id(db, ordem.id)


def iniciar_etapa(db: Session, ordem: Producao, funcionario_id: int):
    if ordem.coluna == "SECAGEM":
        return buscar_por_id(db, ordem.id)

    if ordem.funcionario_id is None:
        ordem.funcionario_id = funcionario_id

    ordem.etapa_status = "EM_EXECUCAO"
    db.commit()
    db.refresh(ordem)

    return buscar_por_id(db, ordem.id)


def _montar_intercorrencias(intercorrencias, descricao_intercorrencia):
    itens = intercorrencias or []
    texto = ", ".join(itens).strip()

    if descricao_intercorrencia:
        if texto:
            texto += f" | OUTROS: {descricao_intercorrencia}"
        else:
            texto = f"OUTROS: {descricao_intercorrencia}"

    return texto or None


def _mesclar_texto_existente(texto_atual: Optional[str], novo_texto: Optional[str]) -> Optional[str]:
    atual = (texto_atual or "").strip()
    novo = (novo_texto or "").strip()

    if atual and novo:
        return f"{atual}\n{novo}"
    if novo:
        return novo
    return atual or None


def proxima_coluna_automatica(
    ordem: Producao,
    usar_secagem: bool = False,
) -> str:
    coluna_atual = ordem.coluna
    agendamento = ordem.agendamento

    if coluna_atual == "PRE_BANHO":
        return "PRE_TOSA" if agendamento_tem_tosa(agendamento) else "BANHO"

    if coluna_atual == "PRE_TOSA":
        return "BANHO"

    if coluna_atual == "BANHO":
        return "SECAGEM" if usar_secagem else "FINALIZACAO_BANHO"

    if coluna_atual == "SECAGEM":
        return "FINALIZACAO_BANHO"

    if coluna_atual == "FINALIZACAO_BANHO":
        return "TOSA" if agendamento_tem_tosa(agendamento) else "FINALIZAR"

    if coluna_atual == "TOSA":
        return "FINALIZAR"

    raise ValueError(f"Não há próxima etapa configurada para {coluna_atual}.")


def proximo_destino_preview(ordem: Producao) -> Optional[str]:
    if ordem.coluna == "BANHO":
        return None

    try:
        return proxima_coluna_automatica(ordem, usar_secagem=False)
    except ValueError:
        return None


def mover_para_proxima_etapa(
    db: Session,
    ordem: Producao,
    funcionario_id: Optional[int] = None,
    usar_secagem: bool = False,
    secagem_tempo: Optional[int] = None,
    intercorrencias=None,
    descricao_intercorrencia=None,
    observacoes_gerais: Optional[str] = None,
):
    if funcionario_id and ordem.funcionario_id is None:
        ordem.funcionario_id = funcionario_id

    destino = proxima_coluna_automatica(ordem, usar_secagem=usar_secagem)

    texto_intercorrencias = _montar_intercorrencias(
        intercorrencias,
        descricao_intercorrencia
    )

    if ordem.coluna == "PRE_BANHO" and texto_intercorrencias:
        ordem.intercorrencias = _mesclar_texto_existente(ordem.intercorrencias, texto_intercorrencias)
        ordem.agendamento.tem_intercorrencia = True

    if destino == "SECAGEM":
        if not secagem_tempo or secagem_tempo <= 0:
            raise ValueError("Informe um tempo de secagem válido.")

        ordem.secagem_tempo = secagem_tempo
        ordem.secagem_inicio = datetime.utcnow()
        ordem.coluna = "SECAGEM"
        ordem.etapa_status = "AGUARDANDO"

    elif destino == "FINALIZAR":
        if texto_intercorrencias:
            ordem.intercorrencias = _mesclar_texto_existente(ordem.intercorrencias, texto_intercorrencias)
            ordem.agendamento.tem_intercorrencia = True

        ordem.observacoes = _mesclar_texto_existente(ordem.observacoes, observacoes_gerais)

        ordem.finalizado = True
        ordem.etapa_status = "CONCLUIDO"
        ordem.agendamento.status = "FINALIZADO"

    else:
        ordem.coluna = destino
        ordem.etapa_status = "AGUARDANDO"

    db.commit()
    db.refresh(ordem)

    return buscar_por_id(db, ordem.id)