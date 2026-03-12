from datetime import datetime
from sqlalchemy.orm import Session, joinedload

from app.models.producao import Producao
from app.models.agendamento import Agendamento


COLUNAS_VALIDAS = [
    "ORDEM",
    "PRE_BANHO",
    "PRE_TOSA",
    "BANHO",
    "FINALIZACAO_BANHO",
    "TOSA",
    "SECAGEM",
]


def agendamento_tem_tosa(agendamento: Agendamento) -> bool:
    for item in agendamento.servicos_agendamento:
        nome = (item.servico.nome or "").lower()
        if "tosa" in nome:
            return True
    return False


def listar_cards(db: Session, empresa_id: int):
    return (
        db.query(Producao)
        .join(Producao.agendamento)
        .options(
            joinedload(Producao.agendamento).joinedload(Agendamento.pet),
            joinedload(Producao.agendamento).joinedload(Agendamento.cliente),
            joinedload(Producao.agendamento).joinedload(Agendamento.servicos_agendamento).joinedload("servico"),
            joinedload(Producao.funcionario),
        )
        .filter(
            Agendamento.empresa_id == empresa_id,
            Producao.finalizado == False
        )
        .order_by(Producao.created_at.asc())
        .all()
    )


def buscar_por_agendamento(db: Session, agendamento_id: int):
    return (
        db.query(Producao)
        .filter(Producao.agendamento_id == agendamento_id)
        .first()
    )


def buscar_por_id(db: Session, producao_id: int):
    return (
        db.query(Producao)
        .options(
            joinedload(Producao.agendamento).joinedload(Agendamento.pet),
            joinedload(Producao.agendamento).joinedload(Agendamento.cliente),
            joinedload(Producao.agendamento).joinedload(Agendamento.servicos_agendamento).joinedload("servico"),
            joinedload(Producao.funcionario),
        )
        .filter(Producao.id == producao_id)
        .first()
    )


def criar_ordem_se_nao_existir(db: Session, agendamento: Agendamento):
    ordem = buscar_por_agendamento(db, agendamento.id)
    if ordem:
        return ordem

    ordem = Producao(
        agendamento_id=agendamento.id,
        coluna="ORDEM",
        etapa_status="AGUARDANDO",
        prioridade=agendamento.prioridade or "NORMAL",
        finalizado=False,
    )
    db.add(ordem)
    db.commit()
    db.refresh(ordem)
    return ordem


def iniciar_etapa(db: Session, ordem: Producao, funcionario_id: int):
    if ordem.funcionario_id is None:
        ordem.funcionario_id = funcionario_id

    ordem.etapa_status = "EM_EXECUCAO"
    db.commit()
    db.refresh(ordem)
    return ordem


def _montar_intercorrencias(intercorrencias, descricao_intercorrencia):
    itens = intercorrencias or []
    texto = ", ".join(itens).strip()

    if descricao_intercorrencia:
        if texto:
            texto += f" | OUTROS: {descricao_intercorrencia}"
        else:
            texto = f"OUTROS: {descricao_intercorrencia}"

    return texto or None


def proxima_coluna_apos_pre_banho(agendamento: Agendamento):
    if agendamento_tem_tosa(agendamento):
        return "PRE_TOSA"
    return "BANHO"


def proxima_coluna_apos_finalizacao_banho(agendamento: Agendamento):
    if agendamento_tem_tosa(agendamento):
        return "TOSA"
    return None


def mover_etapa(
    db: Session,
    ordem: Producao,
    coluna_destino: str,
    funcionario_id: int | None = None,
    secagem_tempo: int | None = None,
    intercorrencias=None,
    descricao_intercorrencia=None,
):
    coluna_atual = ordem.coluna
    agendamento = ordem.agendamento

    if funcionario_id and ordem.funcionario_id is None:
        ordem.funcionario_id = funcionario_id

    if coluna_destino not in COLUNAS_VALIDAS and coluna_destino != "FINALIZAR":
        raise ValueError("Coluna de destino inválida.")

    fluxo_permitido = {
        "ORDEM": ["PRE_BANHO"],
        "PRE_BANHO": [proxima_coluna_apos_pre_banho(agendamento)],
        "PRE_TOSA": ["BANHO"],
        "BANHO": ["SECAGEM", "FINALIZACAO_BANHO"],
        "SECAGEM": ["FINALIZACAO_BANHO"],
        "FINALIZACAO_BANHO": ["TOSA", "FINALIZAR"],
        "TOSA": ["FINALIZAR"],
    }

    destinos = [d for d in fluxo_permitido.get(coluna_atual, []) if d]

    if coluna_destino not in destinos:
        raise ValueError(f"Não é permitido mover de {coluna_atual} para {coluna_destino}.")

    if coluna_atual == "PRE_BANHO":
        ordem.intercorrencias = _montar_intercorrencias(intercorrencias, descricao_intercorrencia)

    if coluna_destino == "SECAGEM":
        if not secagem_tempo or secagem_tempo <= 0:
            raise ValueError("Informe um tempo de secagem válido.")
        ordem.secagem_tempo = secagem_tempo
        ordem.secagem_inicio = datetime.utcnow()
        ordem.etapa_status = "AGUARDANDO"
    elif coluna_destino == "FINALIZAR":
        ordem.finalizado = True
        ordem.etapa_status = "CONCLUIDO"
        agendamento.status = "FINALIZADO"
    else:
        ordem.coluna = coluna_destino
        ordem.etapa_status = "AGUARDANDO"

    if coluna_destino == "FINALIZAR":
        db.commit()
        db.refresh(ordem)
        return ordem

    ordem.coluna = coluna_destino
    db.commit()
    db.refresh(ordem)
    return ordem