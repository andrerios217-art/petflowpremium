from collections import Counter
from datetime import datetime, timezone, date
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.crud.assinatura import registrar_consumo_assinatura
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.assinatura_pet import AssinaturaPet
from app.models.assinatura_pet_consumo import AssinaturaPetConsumo
from app.models.comissao_configuracao import ComissaoConfiguracao
from app.models.comissao_lancamento import ComissaoLancamento
from app.models.producao import Producao
from app.models.producao_historico import ProducaoHistorico
from app.schemas.assinatura import AssinaturaPetConsumoCreate

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


def agendamento_tem_banho_completo(agendamento: Agendamento) -> bool:
    for item in agendamento.servicos_agendamento:
        nome = (item.servico.nome or "").strip().lower() if item.servico else ""
        if "banho completo" in nome:
            return True
    return False


def listar_cards(db: Session, empresa_id: int):
    return (
        _query_base(db)
        .join(Producao.agendamento)
        .filter(
            Agendamento.empresa_id == empresa_id,
            Producao.finalizado.is_(False),
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
    db.commit()
    db.refresh(ordem)
    return buscar_por_id(db, ordem.id)


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
        if agendamento_tem_banho_completo(agendamento):
            return "TOSA"
        if agendamento_tem_tosa(agendamento):
            return "TOSA"
        return "FINALIZAR"

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


def _etapa_eh_comissionavel(etapa: Optional[str]) -> bool:
    return StringStatus(etapa) in {"BANHO", "TOSA", "TOSA_HIGIENICA", "FINALIZACAO_BANHO"}


def _etapa_comissao_para_lancamento(ordem: Producao, etapa: str) -> str:
    etapa_normalizada = StringStatus(etapa)

    if etapa_normalizada == "TOSA" and ordem.agendamento and agendamento_tem_banho_completo(ordem.agendamento):
        return "TOSA_HIGIENICA"

    return etapa_normalizada


def _obter_competencia(ordem: Producao) -> date:
    if ordem.agendamento and ordem.agendamento.data:
        return ordem.agendamento.data.replace(day=1)
    return _agora_utc().date().replace(day=1)


def _buscar_configuracao_comissao(db: Session, empresa_id: Optional[int]) -> Optional[ComissaoConfiguracao]:
    if not empresa_id:
        return None
    return (
        db.query(ComissaoConfiguracao)
        .filter(ComissaoConfiguracao.empresa_id == empresa_id)
        .first()
    )


def _pontos_da_etapa(config: Optional[ComissaoConfiguracao], etapa: str) -> int:
    if not config:
        return 0
    etapa_normalizada = StringStatus(etapa)
    if etapa_normalizada == "BANHO":
        return int(config.pontos_banho or 0)
    if etapa_normalizada == "TOSA":
        return int(config.pontos_tosa or 0)
    if etapa_normalizada == "TOSA_HIGIENICA":
        return int(getattr(config, "pontos_tosa_higienica", 0) or 0)
    if etapa_normalizada == "FINALIZACAO_BANHO":
        return int(config.pontos_finalizacao or 0)
    return 0


def _capturar_comissao_etapa(
    db: Session,
    ordem: Producao,
    etapa: str,
    historico_finalizado: Optional[ProducaoHistorico],
):
    etapa_lancamento = _etapa_comissao_para_lancamento(ordem, etapa)

    if not _etapa_eh_comissionavel(etapa_lancamento):
        return None
    if not historico_finalizado:
        return None

    funcionario_dono = historico_finalizado.funcionario_id
    if not funcionario_dono:
        return None

    empresa_id = getattr(ordem.agendamento, "empresa_id", None) if ordem.agendamento else None
    config = _buscar_configuracao_comissao(db, empresa_id)
    pontos = _pontos_da_etapa(config, etapa_lancamento)

    lancamento_existente = (
        db.query(ComissaoLancamento)
        .filter(
            ComissaoLancamento.producao_id == ordem.id,
            ComissaoLancamento.etapa == etapa_lancamento,
        )
        .first()
    )
    if lancamento_existente:
        return lancamento_existente

    lancamento = ComissaoLancamento(
        empresa_id=empresa_id,
        configuracao_id=config.id if config else None,
        producao_id=ordem.id,
        agendamento_id=ordem.agendamento_id,
        funcionario_id=funcionario_dono,
        etapa=etapa_lancamento,
        pontos=int(pontos),
        status="CAPTURADO",
        competencia=_obter_competencia(ordem),
    )
    db.add(lancamento)
    return lancamento


def _buscar_assinatura_ativa_do_pet(db: Session, ordem: Producao) -> Optional[AssinaturaPet]:
    agendamento = ordem.agendamento
    if not agendamento:
        return None

    return (
        db.query(AssinaturaPet)
        .options(joinedload(AssinaturaPet.itens))
        .filter(
            AssinaturaPet.empresa_id == agendamento.empresa_id,
            AssinaturaPet.cliente_id == agendamento.cliente_id,
            AssinaturaPet.pet_id == agendamento.pet_id,
            AssinaturaPet.status == "ATIVA",
        )
        .order_by(AssinaturaPet.id.desc())
        .first()
    )


def _servicos_do_agendamento(ordem: Producao) -> list[AgendamentoServico]:
    if not ordem.agendamento:
        return []
    return list(getattr(ordem.agendamento, "servicos_agendamento", []) or [])


def _contar_consumos_existentes_por_servico(
    db: Session,
    empresa_id: int,
    agendamento_id: int,
) -> Counter:
    rows = (
        db.query(
            AssinaturaPetConsumo.servico_id,
            AssinaturaPetConsumo.quantidade,
        )
        .filter(
            AssinaturaPetConsumo.empresa_id == empresa_id,
            AssinaturaPetConsumo.agendamento_id == agendamento_id,
            AssinaturaPetConsumo.status.in_(["PENDENTE", "CONFIRMADO"]),
        )
        .all()
    )

    contador = Counter()
    for servico_id, quantidade in rows:
        if servico_id:
            contador[servico_id] += int(quantidade or 0)
    return contador


def _mapear_itens_disponiveis_assinatura(assinatura: AssinaturaPet) -> dict[int, list]:
    itens_por_servico: dict[int, list] = {}

    for item in list(getattr(assinatura, "itens", []) or []):
        if not item or not item.ativo:
            continue
        if item.quantidade_disponivel <= 0:
            continue
        itens_por_servico.setdefault(item.servico_id, []).append(item)

    for servico_id in itens_por_servico:
        itens_por_servico[servico_id].sort(key=lambda item: item.id)

    return itens_por_servico


def _registrar_consumos_assinatura_na_finalizacao(
    db: Session,
    ordem: Producao,
) -> tuple[bool, int]:
    agendamento = ordem.agendamento
    if not agendamento:
        return False, 0

    assinatura = _buscar_assinatura_ativa_do_pet(db, ordem)
    if not assinatura:
        return False, 0

    servicos_agendamento = _servicos_do_agendamento(ordem)
    if not servicos_agendamento:
        return False, 0

    itens_disponiveis = _mapear_itens_disponiveis_assinatura(assinatura)
    if not itens_disponiveis:
        return False, 0

    existentes_por_servico = _contar_consumos_existentes_por_servico(
        db=db,
        empresa_id=agendamento.empresa_id,
        agendamento_id=agendamento.id,
    )

    necessidade_por_servico = Counter()
    for item_agendamento in servicos_agendamento:
        if item_agendamento.servico_id:
            necessidade_por_servico[item_agendamento.servico_id] += 1

    for servico_id, quantidade_existente in existentes_por_servico.items():
        if servico_id in necessidade_por_servico:
            necessidade_por_servico[servico_id] = max(
                necessidade_por_servico[servico_id] - quantidade_existente,
                0,
            )

    if not necessidade_por_servico:
        return True, 0

    todos_cobertos = True
    total_registrado = 0

    for servico_id, quantidade_necessaria in necessidade_por_servico.items():
        if quantidade_necessaria <= 0:
            continue

        itens_para_servico = itens_disponiveis.get(servico_id, [])
        disponibilidade_total = sum(item.quantidade_disponivel for item in itens_para_servico)

        if disponibilidade_total < quantidade_necessaria:
            todos_cobertos = False
            continue

        restante = quantidade_necessaria
        for item_assinatura in itens_para_servico:
            while restante > 0 and item_assinatura.quantidade_disponivel > 0:
                payload = AssinaturaPetConsumoCreate(
                    assinatura_id=assinatura.id,
                    assinatura_item_id=item_assinatura.id,
                    empresa_id=agendamento.empresa_id,
                    cliente_id=agendamento.cliente_id,
                    pet_id=agendamento.pet_id,
                    servico_id=servico_id,
                    data_consumo=agendamento.data,
                    quantidade=1,
                    origem="AGENDAMENTO",
                    status="CONFIRMADO",
                    agendamento_id=agendamento.id,
                    observacoes=f"Consumo automático na finalização da produção {ordem.id}.",
                )
                registrar_consumo_assinatura(db=db, data=payload)
                total_registrado += 1
                restante -= 1

            if restante <= 0:
                break

        if restante > 0:
            todos_cobertos = False

    return todos_cobertos, total_registrado


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

    etapa_atual = ordem.coluna
    destino = proxima_coluna_automatica(ordem, usar_secagem=usar_secagem)

    texto_intercorrencias = _montar_intercorrencias(
        intercorrencias,
        descricao_intercorrencia,
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

        historico_finalizado = _finalizar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            observacoes=observacoes_gerais,
            intercorrencia=texto_intercorrencias,
        )
        _capturar_comissao_etapa(db=db, ordem=ordem, etapa=etapa_atual, historico_finalizado=historico_finalizado)

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

        historico_finalizado = _finalizar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            observacoes=observacoes_gerais,
            intercorrencia=texto_intercorrencias,
        )
        _capturar_comissao_etapa(db=db, ordem=ordem, etapa=etapa_atual, historico_finalizado=historico_finalizado)

        todos_servicos_cobertos, consumos_registrados = _registrar_consumos_assinatura_na_finalizacao(
            db=db,
            ordem=ordem,
        )

        ordem.finalizado = True
        ordem.etapa_status = "CONCLUIDO"
        ordem.agendamento.status = "FINALIZADO"

        observacao_assinatura = None
        if consumos_registrados > 0:
            observacao_assinatura = (
                f"Consumo automático de assinatura registrado na finalização: {consumos_registrados} item(ns)."
            )
            ordem.observacoes = _mesclar_texto_existente(ordem.observacoes, observacao_assinatura)

        if todos_servicos_cobertos:
            if hasattr(ordem, "aguardando_pdv"):
                ordem.aguardando_pdv = False
            if hasattr(ordem, "enviado_pdv"):
                ordem.enviado_pdv = False
            if hasattr(ordem, "enviado_pdv_em"):
                ordem.enviado_pdv_em = None
        else:
            if hasattr(ordem, "aguardando_pdv"):
                ordem.aguardando_pdv = True
            if hasattr(ordem, "enviado_pdv"):
                ordem.enviado_pdv = False
            if hasattr(ordem, "enviado_pdv_em"):
                ordem.enviado_pdv_em = None

    else:
        historico_finalizado = _finalizar_historico_etapa(
            db=db,
            ordem=ordem,
            etapa=ordem.coluna,
            observacoes=observacoes_gerais,
            intercorrencia=texto_intercorrencias,
        )
        _capturar_comissao_etapa(db=db, ordem=ordem, etapa=etapa_atual, historico_finalizado=historico_finalizado)

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