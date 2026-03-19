from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.security import verify_password
from app.models.caixa_divergencia import CaixaDivergencia
from app.models.caixa_movimento import CaixaMovimento
from app.models.caixa_sessao import CaixaSessao
from app.models.configuracao import Configuracao
from app.models.empresa import Empresa
from app.models.usuario import Usuario


DECIMAL_2 = Decimal("0.01")


def _agora_utc():
    return datetime.now(timezone.utc)


def _decimal_2(valor) -> Decimal:
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def _carregar_caixa_query(db: Session):
    return (
        db.query(CaixaSessao)
        .options(
            joinedload(CaixaSessao.usuario_responsavel),
            joinedload(CaixaSessao.usuario_abertura),
            joinedload(CaixaSessao.usuario_fechamento),
            joinedload(CaixaSessao.gerente_abertura),
            joinedload(CaixaSessao.gerente_fechamento),
            joinedload(CaixaSessao.movimentos),
            joinedload(CaixaSessao.divergencias),
        )
    )


def _get_empresa_or_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


def _get_usuario_or_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


def _get_caixa_sessao_or_404(
    db: Session,
    caixa_sessao_id: int,
    for_update: bool = False,
) -> CaixaSessao:
    query = _carregar_caixa_query(db).filter(CaixaSessao.id == caixa_sessao_id)
    if for_update:
        query = query.with_for_update()
    caixa = query.first()
    if not caixa:
        raise HTTPException(status_code=404, detail="Sessão de caixa não encontrada.")
    return caixa


def _get_caixa_aberto_por_empresa(
    db: Session,
    empresa_id: int,
    for_update: bool = False,
) -> CaixaSessao | None:
    query = _carregar_caixa_query(db).filter(
        CaixaSessao.empresa_id == empresa_id,
        CaixaSessao.status == "ABERTO",
    )
    if for_update:
        query = query.with_for_update()
    return query.order_by(CaixaSessao.id.desc()).first()


def _get_ultimo_caixa_fechado(db: Session, empresa_id: int) -> CaixaSessao | None:
    return (
        db.query(CaixaSessao)
        .filter(
            CaixaSessao.empresa_id == empresa_id,
            CaixaSessao.status == "FECHADO",
        )
        .order_by(CaixaSessao.id.desc())
        .first()
    )


def _get_config_valor(
    db: Session,
    empresa_id: int,
    chave: str,
    valor_padrao: str,
) -> str:
    config = (
        db.query(Configuracao)
        .filter(
            Configuracao.empresa_id == empresa_id,
            Configuracao.chave == chave,
        )
        .first()
    )
    if not config or config.valor is None:
        return valor_padrao
    return str(config.valor).strip()


def _get_config_decimal(
    db: Session,
    empresa_id: int,
    chave: str,
    valor_padrao: str,
) -> Decimal:
    valor = _get_config_valor(db, empresa_id, chave, valor_padrao)
    try:
        return _decimal_2(valor)
    except Exception:
        return _decimal_2(valor_padrao)


def _get_config_bool(
    db: Session,
    empresa_id: int,
    chave: str,
    valor_padrao: bool,
) -> bool:
    valor = _get_config_valor(db, empresa_id, chave, "true" if valor_padrao else "false")
    return valor.lower() in ("1", "true", "sim", "yes", "on")


def _validar_usuario_da_empresa(usuario: Usuario, empresa_id: int, label: str):
    if usuario.empresa_id != empresa_id:
        raise HTTPException(
            status_code=400,
            detail=f"{label} não pertence à empresa informada.",
        )
    if not getattr(usuario, "ativo", True):
        raise HTTPException(
            status_code=400,
            detail=f"{label} está inativo.",
        )


def _validar_gerente(
    db: Session,
    empresa_id: int,
    gerente_id: int | None,
    senha_gerente: str | None,
) -> Usuario:
    if not gerente_id:
        raise HTTPException(
            status_code=400,
            detail="Autorização gerencial obrigatória para esta operação.",
        )

    if not senha_gerente:
        raise HTTPException(
            status_code=400,
            detail="Senha do gerente é obrigatória para esta operação.",
        )

    gerente = _get_usuario_or_404(db, gerente_id)
    _validar_usuario_da_empresa(gerente, empresa_id, "Gerente")

    tipo = (gerente.tipo or "").lower()
    if tipo not in ("admin", "gerente"):
        raise HTTPException(
            status_code=403,
            detail="O usuário informado não possui perfil gerencial.",
        )

    if not verify_password(senha_gerente, gerente.senha_hash):
        raise HTTPException(
            status_code=401,
            detail="Senha do gerente inválida.",
        )

    return gerente


def _calcular_nivel_risco(
    valor_diferenca: Decimal,
    tolerancia: Decimal,
    reincidencias_7_dias: int = 0,
) -> str:
    diferenca_abs = _decimal_2(abs(valor_diferenca))

    if diferenca_abs == Decimal("0.00"):
        return "BAIXO"

    if reincidencias_7_dias >= 3:
        return "ALTO"

    if diferenca_abs <= tolerancia:
        return "BAIXO"

    limite_medio = tolerancia * Decimal("10.00")
    if limite_medio < Decimal("5.00"):
        limite_medio = Decimal("5.00")

    if diferenca_abs <= limite_medio:
        return "MEDIO"

    return "ALTO"


def _contar_reincidencias_usuario(
    db: Session,
    empresa_id: int,
    usuario_id: int,
    dias: int = 7,
) -> int:
    data_inicial = _agora_utc() - timedelta(days=dias)
    return (
        db.query(CaixaDivergencia)
        .filter(
            CaixaDivergencia.empresa_id == empresa_id,
            CaixaDivergencia.usuario_responsavel_id == usuario_id,
            CaixaDivergencia.ocorreu_em >= data_inicial,
        )
        .count()
    )


def _registrar_divergencia(
    db: Session,
    *,
    empresa_id: int,
    caixa_sessao_id: int,
    tipo: str,
    valor_referencia,
    valor_informado,
    usuario_responsavel_id: int,
    motivo_padrao: str | None,
    motivo_detalhe: str | None,
    gerente_autorizador_id: int | None,
    tolerancia: Decimal,
) -> CaixaDivergencia | None:
    referencia = _decimal_2(valor_referencia)
    informado = _decimal_2(valor_informado)
    diferenca = informado - referencia

    if diferenca == Decimal("0.00"):
        return None

    reincidencias = _contar_reincidencias_usuario(
        db,
        empresa_id=empresa_id,
        usuario_id=usuario_responsavel_id,
        dias=7,
    )

    divergencia = CaixaDivergencia()
    divergencia.definir(
        empresa_id=empresa_id,
        caixa_sessao_id=caixa_sessao_id,
        tipo=tipo,
        valor_referencia=referencia,
        valor_informado=informado,
        usuario_responsavel_id=usuario_responsavel_id,
        motivo_padrao=motivo_padrao,
        motivo_detalhe=motivo_detalhe,
        gerente_autorizador_id=gerente_autorizador_id,
        nivel_risco=_calcular_nivel_risco(
            valor_diferenca=diferenca,
            tolerancia=tolerancia,
            reincidencias_7_dias=reincidencias,
        ),
    )

    if gerente_autorizador_id:
        divergencia.status = "JUSTIFICADA"
    else:
        divergencia.status = "PENDENTE_ANALISE"

    db.add(divergencia)
    db.flush()
    return divergencia


def _exige_gerente_por_diferenca(
    diferenca: Decimal,
    tolerancia: Decimal,
) -> bool:
    return _decimal_2(abs(diferenca)) > _decimal_2(tolerancia)


def _somar_movimentos(
    movimentos: list[CaixaMovimento],
    *,
    tipo: str | None = None,
    forma_pagamento: str | None = None,
) -> Decimal:
    total = Decimal("0.00")
    for movimento in movimentos or []:
        if tipo and movimento.tipo_movimento != tipo:
            continue
        if forma_pagamento and movimento.forma_pagamento != forma_pagamento:
            continue
        total += _decimal_2(movimento.valor)
    return total


def calcular_resumo_financeiro_caixa(caixa: CaixaSessao) -> dict:
    movimentos = caixa.movimentos or []

    total_vendas = _somar_movimentos(movimentos, tipo="VENDA")
    total_dinheiro = _somar_movimentos(
        movimentos,
        tipo="VENDA",
        forma_pagamento="DINHEIRO",
    )
    total_pix = _somar_movimentos(
        movimentos,
        tipo="VENDA",
        forma_pagamento="PIX",
    )
    total_cartao_debito = _somar_movimentos(
        movimentos,
        tipo="VENDA",
        forma_pagamento="CARTAO_DEBITO",
    )
    total_cartao_credito = _somar_movimentos(
        movimentos,
        tipo="VENDA",
        forma_pagamento="CARTAO_CREDITO",
    )
    total_sangria = _somar_movimentos(movimentos, tipo="SANGRIA")
    total_suprimento = _somar_movimentos(movimentos, tipo="SUPRIMENTO")
    total_estorno_dinheiro = _somar_movimentos(
        movimentos,
        tipo="ESTORNO",
        forma_pagamento="DINHEIRO",
    )
    total_ajuste = _somar_movimentos(movimentos, tipo="AJUSTE")

    saldo_dinheiro_esperado = (
        _decimal_2(caixa.valor_abertura_informado)
        + total_dinheiro
        + total_suprimento
        + total_ajuste
        - total_sangria
        - total_estorno_dinheiro
    )

    return {
        "caixa_sessao_id": caixa.id,
        "total_vendas": _decimal_2(total_vendas),
        "total_dinheiro": _decimal_2(total_dinheiro),
        "total_pix": _decimal_2(total_pix),
        "total_cartao_debito": _decimal_2(total_cartao_debito),
        "total_cartao_credito": _decimal_2(total_cartao_credito),
        "total_sangria": _decimal_2(total_sangria),
        "total_suprimento": _decimal_2(total_suprimento),
        "saldo_dinheiro_esperado": _decimal_2(saldo_dinheiro_esperado),
    }


def obter_caixa_aberto(db: Session, empresa_id: int) -> CaixaSessao | None:
    _get_empresa_or_404(db, empresa_id)
    return _get_caixa_aberto_por_empresa(db, empresa_id, for_update=False)


def listar_caixas(
    db: Session,
    empresa_id: int,
    status: str | None = None,
    limite: int = 50,
):
    _get_empresa_or_404(db, empresa_id)

    query = (
        _carregar_caixa_query(db)
        .filter(CaixaSessao.empresa_id == empresa_id)
        .order_by(CaixaSessao.id.desc())
    )

    if status:
        query = query.filter(CaixaSessao.status == status)

    return query.limit(limite).all()


def obter_caixa(db: Session, caixa_sessao_id: int) -> CaixaSessao:
    return _get_caixa_sessao_or_404(db, caixa_sessao_id, for_update=False)


def abrir_caixa(db: Session, payload) -> tuple[CaixaSessao, CaixaDivergencia | None]:
    _get_empresa_or_404(db, payload.empresa_id)

    caixa_aberto = _get_caixa_aberto_por_empresa(
        db,
        payload.empresa_id,
        for_update=True,
    )
    if caixa_aberto:
        raise HTTPException(
            status_code=400,
            detail="Já existe um caixa aberto para esta empresa.",
        )

    usuario_responsavel = _get_usuario_or_404(db, payload.usuario_responsavel_id)
    _validar_usuario_da_empresa(usuario_responsavel, payload.empresa_id, "Usuário responsável")

    usuario_abertura = _get_usuario_or_404(db, payload.usuario_abertura_id)
    _validar_usuario_da_empresa(usuario_abertura, payload.empresa_id, "Usuário de abertura")

    ultimo_caixa = _get_ultimo_caixa_fechado(db, payload.empresa_id)
    valor_referencia_anterior = _decimal_2(
        ultimo_caixa.valor_fechamento_informado if ultimo_caixa else Decimal("0.00")
    )
    valor_abertura = _decimal_2(payload.valor_abertura_informado)
    diferenca = valor_abertura - valor_referencia_anterior

    tolerancia_abertura = _get_config_decimal(
        db,
        payload.empresa_id,
        "caixa_tolerancia_abertura",
        "0.10",
    )

    gerente_abertura_id = None
    if _exige_gerente_por_diferenca(diferenca, tolerancia_abertura):
        if not payload.motivo_diferenca_abertura:
            raise HTTPException(
                status_code=400,
                detail="Motivo da diferença na abertura é obrigatório.",
            )

        gerente = _validar_gerente(
            db,
            empresa_id=payload.empresa_id,
            gerente_id=payload.gerente_abertura_id,
            senha_gerente=payload.senha_gerente,
        )
        gerente_abertura_id = gerente.id

    caixa = CaixaSessao(
        empresa_id=payload.empresa_id,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    caixa.abrir(
        usuario_responsavel_id=payload.usuario_responsavel_id,
        usuario_abertura_id=payload.usuario_abertura_id,
        valor_abertura_informado=valor_abertura,
        valor_referencia_anterior=valor_referencia_anterior,
        motivo_diferenca_abertura=payload.motivo_diferenca_abertura,
        gerente_abertura_id=gerente_abertura_id,
        observacoes=payload.observacoes,
    )

    db.add(caixa)
    db.flush()

    divergencia = _registrar_divergencia(
        db,
        empresa_id=payload.empresa_id,
        caixa_sessao_id=caixa.id,
        tipo="ABERTURA",
        valor_referencia=valor_referencia_anterior,
        valor_informado=valor_abertura,
        usuario_responsavel_id=payload.usuario_responsavel_id,
        motivo_padrao="DIFERENCA_ABERTURA",
        motivo_detalhe=payload.motivo_diferenca_abertura,
        gerente_autorizador_id=gerente_abertura_id,
        tolerancia=tolerancia_abertura,
    )

    db.commit()
    caixa = _get_caixa_sessao_or_404(db, caixa.id, for_update=False)
    return caixa, divergencia


def fechar_caixa(db: Session, caixa_sessao_id: int, payload) -> tuple[CaixaSessao, CaixaDivergencia | None]:
    caixa = _get_caixa_sessao_or_404(db, caixa_sessao_id, for_update=True)

    if caixa.status != "ABERTO":
        raise HTTPException(
            status_code=400,
            detail="Somente caixas abertos podem ser fechados.",
        )

    usuario_fechamento = _get_usuario_or_404(db, payload.usuario_fechamento_id)
    _validar_usuario_da_empresa(usuario_fechamento, caixa.empresa_id, "Usuário de fechamento")

    resumo = calcular_resumo_financeiro_caixa(caixa)
    valor_esperado = _decimal_2(resumo["saldo_dinheiro_esperado"])
    valor_informado = _decimal_2(payload.valor_fechamento_informado)
    diferenca = valor_informado - valor_esperado

    tolerancia_fechamento = _get_config_decimal(
        db,
        caixa.empresa_id,
        "caixa_tolerancia_fechamento",
        "0.50",
    )

    gerente_fechamento_id = None
    if _exige_gerente_por_diferenca(diferenca, tolerancia_fechamento):
        if not payload.motivo_diferenca_fechamento:
            raise HTTPException(
                status_code=400,
                detail="Motivo da diferença no fechamento é obrigatório.",
            )

        gerente = _validar_gerente(
            db,
            empresa_id=caixa.empresa_id,
            gerente_id=payload.gerente_fechamento_id,
            senha_gerente=payload.senha_gerente,
        )
        gerente_fechamento_id = gerente.id

    caixa.registrar_fechamento(
        usuario_fechamento_id=payload.usuario_fechamento_id,
        valor_fechamento_esperado=valor_esperado,
        valor_fechamento_informado=valor_informado,
        motivo_diferenca_fechamento=payload.motivo_diferenca_fechamento,
        gerente_fechamento_id=gerente_fechamento_id,
    )

    divergencia = _registrar_divergencia(
        db,
        empresa_id=caixa.empresa_id,
        caixa_sessao_id=caixa.id,
        tipo="FECHAMENTO",
        valor_referencia=valor_esperado,
        valor_informado=valor_informado,
        usuario_responsavel_id=caixa.usuario_responsavel_id,
        motivo_padrao="DIFERENCA_FECHAMENTO",
        motivo_detalhe=payload.motivo_diferenca_fechamento,
        gerente_autorizador_id=gerente_fechamento_id,
        tolerancia=tolerancia_fechamento,
    )

    db.commit()
    caixa = _get_caixa_sessao_or_404(db, caixa.id, for_update=False)
    return caixa, divergencia


def registrar_sangria(db: Session, payload) -> tuple[CaixaSessao, CaixaMovimento]:
    caixa = _get_caixa_sessao_or_404(db, payload.caixa_sessao_id, for_update=True)

    if caixa.status != "ABERTO":
        raise HTTPException(
            status_code=400,
            detail="Só é possível registrar sangria com o caixa aberto.",
        )

    if caixa.empresa_id != payload.empresa_id:
        raise HTTPException(
            status_code=400,
            detail="A sessão de caixa não pertence à empresa informada.",
        )

    usuario = _get_usuario_or_404(db, payload.usuario_id)
    _validar_usuario_da_empresa(usuario, caixa.empresa_id, "Usuário")

    exige_gerente = _get_config_bool(
        db,
        caixa.empresa_id,
        "caixa_sangria_exige_gerente",
        False,
    )
    limite_gerente = _get_config_decimal(
        db,
        caixa.empresa_id,
        "caixa_sangria_limite_gerente",
        "999999.99" if not exige_gerente else "0.00",
    )

    gerente_autorizador_id = None
    if exige_gerente or _decimal_2(payload.valor) > limite_gerente:
        gerente = _validar_gerente(
            db,
            empresa_id=caixa.empresa_id,
            gerente_id=payload.gerente_autorizador_id,
            senha_gerente=payload.senha_gerente,
        )
        gerente_autorizador_id = gerente.id

    movimento = CaixaMovimento(
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    movimento.definir_como_sangria(
        empresa_id=payload.empresa_id,
        caixa_sessao_id=payload.caixa_sessao_id,
        valor=_decimal_2(payload.valor),
        usuario_id=payload.usuario_id,
        motivo=payload.motivo,
        observacoes=payload.observacoes,
        gerente_autorizador_id=gerente_autorizador_id,
    )

    db.add(movimento)
    db.commit()

    caixa = _get_caixa_sessao_or_404(db, caixa.id, for_update=False)
    return caixa, movimento


def registrar_suprimento(db: Session, payload) -> tuple[CaixaSessao, CaixaMovimento]:
    caixa = _get_caixa_sessao_or_404(db, payload.caixa_sessao_id, for_update=True)

    if caixa.status != "ABERTO":
        raise HTTPException(
            status_code=400,
            detail="Só é possível registrar suprimento com o caixa aberto.",
        )

    if caixa.empresa_id != payload.empresa_id:
        raise HTTPException(
            status_code=400,
            detail="A sessão de caixa não pertence à empresa informada.",
        )

    usuario = _get_usuario_or_404(db, payload.usuario_id)
    _validar_usuario_da_empresa(usuario, caixa.empresa_id, "Usuário")

    exige_gerente = _get_config_bool(
        db,
        caixa.empresa_id,
        "caixa_suprimento_exige_gerente",
        True,
    )
    limite_gerente = _get_config_decimal(
        db,
        caixa.empresa_id,
        "caixa_suprimento_limite_gerente",
        "999999.99" if not exige_gerente else "0.00",
    )

    gerente_autorizador_id = None
    if exige_gerente or _decimal_2(payload.valor) > limite_gerente:
        gerente = _validar_gerente(
            db,
            empresa_id=caixa.empresa_id,
            gerente_id=payload.gerente_autorizador_id,
            senha_gerente=payload.senha_gerente,
        )
        gerente_autorizador_id = gerente.id

    movimento = CaixaMovimento(
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    movimento.definir_como_suprimento(
        empresa_id=payload.empresa_id,
        caixa_sessao_id=payload.caixa_sessao_id,
        valor=_decimal_2(payload.valor),
        usuario_id=payload.usuario_id,
        motivo=payload.motivo,
        observacoes=payload.observacoes,
        gerente_autorizador_id=gerente_autorizador_id,
    )

    db.add(movimento)
    db.commit()

    caixa = _get_caixa_sessao_or_404(db, caixa.id, for_update=False)
    return caixa, movimento


def listar_divergencias(
    db: Session,
    empresa_id: int,
    status: str | None = None,
    usuario_responsavel_id: int | None = None,
    limite: int = 100,
):
    _get_empresa_or_404(db, empresa_id)

    query = (
        db.query(CaixaDivergencia)
        .options(
            joinedload(CaixaDivergencia.usuario_responsavel),
            joinedload(CaixaDivergencia.gerente_autorizador),
            joinedload(CaixaDivergencia.resolvido_por_usuario),
        )
        .filter(CaixaDivergencia.empresa_id == empresa_id)
        .order_by(CaixaDivergencia.id.desc())
    )

    if status:
        query = query.filter(CaixaDivergencia.status == status)

    if usuario_responsavel_id:
        query = query.filter(
            CaixaDivergencia.usuario_responsavel_id == usuario_responsavel_id
        )

    return query.limit(limite).all()


def obter_divergencia(db: Session, divergencia_id: int) -> CaixaDivergencia:
    divergencia = (
        db.query(CaixaDivergencia)
        .options(
            joinedload(CaixaDivergencia.usuario_responsavel),
            joinedload(CaixaDivergencia.gerente_autorizador),
            joinedload(CaixaDivergencia.resolvido_por_usuario),
        )
        .filter(CaixaDivergencia.id == divergencia_id)
        .first()
    )
    if not divergencia:
        raise HTTPException(status_code=404, detail="Divergência não encontrada.")
    return divergencia


def atualizar_status_divergencia(
    db: Session,
    divergencia_id: int,
    payload,
) -> CaixaDivergencia:
    divergencia = (
        db.query(CaixaDivergencia)
        .filter(CaixaDivergencia.id == divergencia_id)
        .with_for_update()
        .first()
    )
    if not divergencia:
        raise HTTPException(status_code=404, detail="Divergência não encontrada.")

    if payload.status in ("JUSTIFICADA", "CONFIRMADA"):
        gerente = _validar_gerente(
            db,
            empresa_id=divergencia.empresa_id,
            gerente_id=payload.gerente_autorizador_id,
            senha_gerente=payload.senha_gerente,
        )

        if payload.status == "JUSTIFICADA":
            divergencia.marcar_justificada(
                observacao_gerencial=payload.observacao_gerencial,
                gerente_autorizador_id=gerente.id,
            )
        else:
            divergencia.marcar_confirmada(
                observacao_gerencial=payload.observacao_gerencial,
                gerente_autorizador_id=gerente.id,
            )

    elif payload.status == "RESOLVIDA":
        if not payload.resolvido_por_usuario_id:
            raise HTTPException(
                status_code=400,
                detail="Usuário de resolução é obrigatório.",
            )

        usuario = _get_usuario_or_404(db, payload.resolvido_por_usuario_id)
        _validar_usuario_da_empresa(usuario, divergencia.empresa_id, "Usuário de resolução")

        divergencia.marcar_resolvida(
            resolvido_por_usuario_id=payload.resolvido_por_usuario_id,
            observacao_gerencial=payload.observacao_gerencial,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Status de divergência inválido.",
        )

    db.commit()
    db.refresh(divergencia)
    return obter_divergencia(db, divergencia.id)