from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.producao import Producao
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.producao_historico import ProducaoHistorico


COLUNAS_VALIDAS = [
    "PRE_BANHO",
    "PRE_TOSA",
    "BANHO",
    "FINALIZACAO_BANHO",
    "TOSA",
    "SECAGEM",
]


def _agora_utc():
    return datetime.now(timezone.utc)


def _normalizar_datetime_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


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
            joinedload(Producao.historicos),
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


def _servico_principal_id(ordem: Producao) -> Optional[int]:
    if not ordem.agendamento or not ordem.agendamento.servicos_agendamento:
        return None

    primeiro_item = ordem.agendamento.servicos_agendamento[0]
    if not primeiro_item or not primeiro_item.servico:
        return None

    return primeiro_item.servico.id


def _calcular_tempo_gasto_minutos(
    iniciado_em: Optional[datetime],
    finalizado_em: Optional[datetime]
) -> Optional[int]:
    if not iniciado_em or not finalizado_em:
        return None

    inicio_utc = _normalizar_datetime_utc(iniciado_em)
    fim_utc = _normalizar_datetime_utc(finalizado_em)

    if not inicio_utc or not fim_utc:
        return None

    delta = fim_utc - inicio_utc
    total_minutos = int(delta.total_seconds() // 60)

    if total_minutos < 0:
        return 0

    return total_minutos


def _buscar_historico_aberto(db: Session, producao_id: int, etapa: str) -> Optional[ProducaoHistorico]:
    return (
        db.query(ProducaoHistorico)
        .filter(
            ProducaoHistorico.producao_id == producao_id,
            ProducaoHistorico.etapa == etapa,
            ProducaoHistorico.finalizado_em.is_(None),
        )
        .order_by(ProducaoHistorico.iniciado_em.desc(), ProducaoHistorico.id.desc())
        .first()
    )


def _criar_historico_etapa(
    db: Session,
    ordem: Producao,
    etapa: str,
    funcionario_id: Optional[int] = None,
    status: str = "INICIADO",
    observacoes: Optional[str] = None,
    intercorrencia: Optional[str] = None,
):
    historico = ProducaoHistorico(
        producao_id=ordem.id,
        agendamento_id=ordem.agendamento_id,
        pet_id=ordem.agendamento.pet.id if ordem.agendamento and ordem.agendamento.pet else None,
        servico_id=_servico_principal_id(ordem),
        funcionario_id=funcionario_id or ordem.funcionario_id,
        etapa=etapa,
        status=status,
        iniciado_em=_agora_utc(),
        observacoes=observacoes,
        intercorrencia=intercorrencia,
    )
    db.add(historico)
    return historico


def _finalizar_historico_etapa(
    db: Session,
    ordem: Producao,
    etapa: str,
    observacoes: Optional[str] = None,
    intercorrencia: Optional[str] = None,
):
    historico = _buscar_historico_aberto(db, ordem.id, etapa)
    if not historico:
        return None

    agora = _agora_utc()
    historico.finalizado_em = agora
    historico.status = "FINALIZADO"
    historico.tempo_gasto_minutos = _calcular_tempo_gasto_minutos(historico.iniciado_em, agora)

    if observacoes:
        historico.observacoes = _mesclar_texto_existente(historico.observacoes, observacoes)

    if intercorrencia:
        historico.intercorrencia = _mesclar_texto_existente(historico.intercorrencia, intercorrencia)

    return historico


def _garantir_historico_iniciado(db: Session, ordem: Producao, funcionario_id: Optional[int] = None):
    historico_aberto = _buscar_historico_aberto(db, ordem.id, ordem.coluna)
    if historico_aberto:
        if funcionario_id and historico_aberto.funcionario_id is None:
            historico_aberto.funcionario_id = funcionario_id
        return historico_aberto

    return _criar_historico_etapa(
        db=db,
        ordem=ordem,
        etapa=ordem.coluna,
        funcionario_id=funcionario_id,
        status="INICIADO",
    )


def _validar_pode_iniciar(ordem: Producao):
    if ordem.finalizado:
        raise ValueError("Esta ordem de produção já foi finalizada.")

    status = StringStatus(ordem.etapa_status)

    if status == "EM_EXECUCAO":
        raise ValueError("Esta etapa já foi iniciada.")

    if status == "CONCLUIDO":
        raise ValueError("Esta etapa já foi concluída.")


def _validar_pode_avancar(ordem: Producao):
    if ordem.finalizado:
        raise ValueError("Esta ordem de produção já foi finalizada.")

    coluna = StringStatus(ordem.coluna)
    status = StringStatus(ordem.etapa_status)

    if coluna == "SECAGEM":
        return

    if status != "EM_EXECUCAO":
        raise ValueError("Esta etapa precisa ser iniciada antes de avançar.")


def StringStatus(valor: Optional[str]) -> str:
    return StringValue(valor).upper()


def StringValue(valor: Optional[str]) -> str:
    return str(valor or "").strip()


def criar_ordem_se_nao_existir(db: Session, agendamento: Agendamento, commit: bool = True):
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
    db.flush()

    if commit:
        db.commit()
        db.refresh(ordem)
        return buscar_por_id(db, ordem.id)

    return ordem


def iniciar_etapa(db: Session, ordem: Producao, funcionario_id: int):
    _validar_pode_iniciar(ordem)

    if ordem.coluna == "SECAGEM":
        return buscar_por_id(db, ordem.id)

    if ordem.funcionario_id is None:
        ordem.funcionario_id = funcionario_id

    ordem.etapa_status = "EM_EXECUCAO"

    _garantir_historico_iniciado(
        db=db,
        ordem=ordem,
        funcionario_id=funcionario_id,
    )

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
    _validar_pode_avancar(ordem)

    if funcionario_id and ordem.funcionario_id is None:
        ordem.funcionario_id = funcionario_id

    destino = proxima_coluna_automatica(ordem, usar_secagem=usar_secagem)

    texto_intercorrencias = _montar_intercorrencias(
        intercorrencias,
        descricao_intercorrencia
    )

    historico_aberto = _buscar_historico_aberto(db, ordem.id, ordem.coluna)
    if not historico_aberto and ordem.etapa_status == "EM_EXECUCAO":
        historico_aberto = _criar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            funcionario_id=funcionario_id or ordem.funcionario_id,
            status="INICIADO",
        )

    if ordem.coluna == "PRE_BANHO" and texto_intercorrencias:
        ordem.intercorrencias = _mesclar_texto_existente(ordem.intercorrencias, texto_intercorrencias)
        ordem.agendamento.tem_intercorrencia = True

    if destino == "SECAGEM":
        if not secagem_tempo or secagem_tempo <= 0:
            raise ValueError("Informe um tempo de secagem válido.")

        _finalizar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            observacoes=observacoes_gerais,
            intercorrencia=texto_intercorrencias,
        )

        ordem.secagem_tempo = secagem_tempo
        ordem.secagem_inicio = _agora_utc()
        ordem.coluna = "SECAGEM"
        ordem.etapa_status = "AGUARDANDO"

        observacao_secagem = f"Secagem programada por {secagem_tempo} minuto(s)."
        _criar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa="SECAGEM",
            funcionario_id=funcionario_id or ordem.funcionario_id,
            status="INICIADO",
            observacoes=observacao_secagem,
        )

    elif destino == "FINALIZAR":
        if texto_intercorrencias:
            ordem.intercorrencias = _mesclar_texto_existente(ordem.intercorrencias, texto_intercorrencias)
            ordem.agendamento.tem_intercorrencia = True

        ordem.observacoes = _mesclar_texto_existente(ordem.observacoes, observacoes_gerais)

        _finalizar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            observacoes=observacoes_gerais,
            intercorrencia=texto_intercorrencias,
        )

        ordem.finalizado = True
        ordem.etapa_status = "CONCLUIDO"
        ordem.agendamento.status = "FINALIZADO"

    else:
        _finalizar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            observacoes=observacoes_gerais,
            intercorrencia=texto_intercorrencias,
        )

        ordem.coluna = destino
        ordem.etapa_status = "AGUARDANDO"

        _criar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=destino,
            funcionario_id=funcionario_id or ordem.funcionario_id,
            status="INICIADO",
        )

    db.commit()
    db.refresh(ordem)

    return buscar_por_id(db, ordem.id)