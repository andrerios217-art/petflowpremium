from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.security import verify_password
from app.models.atendimento_clinico import AtendimentoClinico
from app.models.caixa_movimento import CaixaMovimento
from app.models.caixa_sessao import CaixaSessao
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.financeiro_receber import FinanceiroReceber
from app.models.pdv_pagamento import PdvPagamento
from app.models.pdv_venda import PdvVenda
from app.models.pdv_venda_item import PdvVendaItem
from app.models.usuario import Usuario
from app.schemas.pdv import (
    PdvCancelRequest,
    PdvCheckoutRequest,
    PdvVendaCreate,
    PdvVendaItemAdd,
    PdvVendaUpdate,
)


DECIMAL_2 = Decimal("0.01")
DECIMAL_3 = Decimal("0.001")


def _agora_utc():
    return datetime.now(timezone.utc)


def _decimal_2(valor) -> Decimal:
    if valor is None:
        return Decimal("0.00")
    return Decimal(str(valor)).quantize(DECIMAL_2, rounding=ROUND_HALF_UP)


def _decimal_3(valor) -> Decimal:
    if valor is None:
        return Decimal("0.000")
    return Decimal(str(valor)).quantize(DECIMAL_3, rounding=ROUND_HALF_UP)


def _normalizar_texto(valor: str | None) -> str:
    if not valor:
        return ""
    valor = unicodedata.normalize("NFKD", valor)
    valor = "".join(c for c in valor if not unicodedata.combining(c))
    valor = valor.lower().strip()
    valor = re.sub(r"\s+", " ", valor)
    return valor


def _somente_digitos(valor: str | None) -> str:
    if not valor:
        return ""
    return re.sub(r"\D", "", valor)


def _tokens_busca(termo: str) -> list[str]:
    termo = _normalizar_texto(termo)
    if not termo:
        return []
    return [token for token in termo.split(" ") if token]


def _match_cliente(cliente: Cliente, tokens: Iterable[str]) -> bool:
    nome = _normalizar_texto(getattr(cliente, "nome", None))
    cpf = _somente_digitos(getattr(cliente, "cpf", None))
    telefone = _somente_digitos(getattr(cliente, "telefone", None))
    telefone_fixo = _somente_digitos(getattr(cliente, "telefone_fixo", None))

    for token in tokens:
        token_digits = _somente_digitos(token)

        if token_digits:
            if (
                token_digits not in cpf
                and token_digits not in telefone
                and token_digits not in telefone_fixo
            ):
                return False
        else:
            if token not in nome:
                return False

    return True


def _carregar_venda_query(db: Session):
    return (
        db.query(PdvVenda)
        .options(
            joinedload(PdvVenda.cliente),
            joinedload(PdvVenda.caixa_sessao),
            joinedload(PdvVenda.itens).joinedload(PdvVendaItem.atendimento_clinico),
            joinedload(PdvVenda.pagamentos),
        )
    )


def _query_venda_lock(db: Session):
    return db.query(PdvVenda)


def _get_empresa_or_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


def _get_cliente_or_404(db: Session, cliente_id: int) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente


def _get_usuario_or_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


def _get_venda_or_404(db: Session, venda_id: int, for_update: bool = False) -> PdvVenda:
    if for_update:
        venda = (
            _query_venda_lock(db)
            .filter(PdvVenda.id == venda_id)
            .with_for_update(of=PdvVenda)
            .first()
        )
    else:
        venda = (
            _carregar_venda_query(db)
            .filter(PdvVenda.id == venda_id)
            .first()
        )

    if not venda:
        raise HTTPException(status_code=404, detail="Venda PDV não encontrada.")
    return venda


def _get_caixa_sessao_or_404(
    db: Session,
    caixa_sessao_id: int,
    for_update: bool = False,
) -> CaixaSessao:
    query = db.query(CaixaSessao).filter(CaixaSessao.id == caixa_sessao_id)
    if for_update:
        query = query.with_for_update(of=CaixaSessao)
    caixa = query.first()
    if not caixa:
        raise HTTPException(status_code=404, detail="Sessão de caixa não encontrada.")
    return caixa


def _get_caixa_aberto_por_empresa(
    db: Session,
    empresa_id: int,
    for_update: bool = False,
) -> CaixaSessao | None:
    query = db.query(CaixaSessao).filter(
        CaixaSessao.empresa_id == empresa_id,
        CaixaSessao.status == "ABERTO",
    )
    if for_update:
        query = query.with_for_update(of=CaixaSessao)
    return query.order_by(CaixaSessao.id.desc()).first()


def _get_atendimento_or_404(
    db: Session,
    atendimento_id: int,
    for_update: bool = False,
) -> AtendimentoClinico:
    query = (
        db.query(AtendimentoClinico)
        .options(
            joinedload(AtendimentoClinico.cliente),
            joinedload(AtendimentoClinico.pet),
            joinedload(AtendimentoClinico.itens),
        )
        .filter(AtendimentoClinico.id == atendimento_id)
    )

    if for_update:
        query = query.with_for_update()

    atendimento = query.first()
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento clínico não encontrado.")
    return atendimento


def _recarregar_venda(db: Session, venda_id: int) -> PdvVenda:
    return _get_venda_or_404(db, venda_id, for_update=False)


def _gerar_numero_venda(venda_id: int) -> str:
    return f"PDV-{str(venda_id).zfill(6)}"


def _gerar_numero_venda_provisorio() -> str:
    return f"TMP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"


def _calcular_total_atendimento(atendimento: AtendimentoClinico) -> Decimal:
    total = Decimal("0.00")
    for item in getattr(atendimento, "itens", []) or []:
        total += _decimal_2(getattr(item, "valor_total", 0) or 0)
    return total


def _descricao_atendimento(atendimento: AtendimentoClinico) -> str:
    pet = getattr(atendimento, "pet", None)
    pet_nome = getattr(pet, "nome", None) if pet else None

    descricoes = []
    for item in getattr(atendimento, "itens", []) or []:
        descricao = (getattr(item, "descricao", None) or "").strip()
        if descricao:
            descricoes.append(descricao)

    if descricoes:
        descricao_base = " | ".join(descricoes[:3])
        if len(descricoes) > 3:
            descricao_base += " | ..."
    else:
        descricao_base = "Atendimento clínico"

    if pet_nome:
        return f"{descricao_base} - {pet_nome}"

    return descricao_base


def _validar_venda_aberta(venda: PdvVenda):
    if venda.status != "ABERTA":
        raise HTTPException(
            status_code=400,
            detail="A operação só é permitida para vendas com status ABERTA.",
        )


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
            detail="Autorização gerencial é obrigatória para esta operação.",
        )

    if not senha_gerente:
        raise HTTPException(
            status_code=400,
            detail="Senha do gerente é obrigatória para esta operação.",
        )

    gerente = _get_usuario_or_404(db, gerente_id)
    _validar_usuario_da_empresa(gerente, empresa_id, "Gerente")

    if (gerente.tipo or "").lower() not in ("admin", "gerente"):
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


def _validar_caixa_para_venda(
    caixa: CaixaSessao,
    empresa_id: int,
    exigir_aberto: bool = True,
):
    if caixa.empresa_id != empresa_id:
        raise HTTPException(
            status_code=400,
            detail="A sessão de caixa não pertence à empresa informada.",
        )

    if exigir_aberto and caixa.status != "ABERTO":
        raise HTTPException(
            status_code=400,
            detail="É necessário ter um caixa aberto para esta operação.",
        )


def _resolver_usuario_operacao(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    fallback_usuario_id: int | None,
    label: str,
) -> Usuario:
    usuario_resolvido_id = usuario_id or fallback_usuario_id
    if not usuario_resolvido_id:
        raise HTTPException(
            status_code=400,
            detail=f"{label} é obrigatório para esta operação.",
        )

    usuario = _get_usuario_or_404(db, usuario_resolvido_id)
    _validar_usuario_da_empresa(usuario, empresa_id, label)
    return usuario


def _validar_cliente_da_venda(venda: PdvVenda, cliente_id: int):
    if venda.modo_cliente != "REGISTERED_CLIENT":
        raise HTTPException(
            status_code=400,
            detail="Esta venda está em modo balcão e não aceita itens de atendimento.",
        )

    if venda.cliente_id != cliente_id:
        raise HTTPException(
            status_code=400,
            detail="Não é permitido misturar itens de clientes diferentes na mesma venda.",
        )


def _validar_atendimento_disponivel_para_pdv(
    db: Session,
    atendimento: AtendimentoClinico,
    venda: PdvVenda,
):
    if atendimento.status != "FINALIZADO":
        raise HTTPException(
            status_code=400,
            detail="Somente atendimentos FINALIZADOS podem ser enviados ao PDV.",
        )

    if getattr(atendimento, "empresa_id", None) != venda.empresa_id:
        raise HTTPException(
            status_code=400,
            detail="O atendimento não pertence à mesma empresa da venda.",
        )

    if not getattr(atendimento, "cliente_id", None):
        raise HTTPException(
            status_code=400,
            detail="O atendimento não possui cliente vinculado.",
        )

    _validar_cliente_da_venda(venda, atendimento.cliente_id)

    item_existente = (
        db.query(PdvVendaItem)
        .join(PdvVenda, PdvVenda.id == PdvVendaItem.venda_id)
        .filter(
            PdvVendaItem.atendimento_clinico_id == atendimento.id,
            PdvVenda.status != "CANCELADA",
        )
        .first()
    )
    if item_existente:
        raise HTTPException(
            status_code=400,
            detail="Este atendimento já está vinculado a uma venda do PDV.",
        )


def _validar_checkout(
    venda: PdvVenda,
    caixa: CaixaSessao,
    payload: PdvCheckoutRequest,
):
    _validar_venda_aberta(venda)
    _validar_caixa_para_venda(caixa, venda.empresa_id, exigir_aberto=True)

    itens = (
        db.query(PdvVendaItem)
        .filter(PdvVendaItem.venda_id == venda.id)
        .all()
    ) if False else venda.itens

    if not itens:
        raise HTTPException(
            status_code=400,
            detail="Não é possível finalizar uma venda sem itens.",
        )

    possui_servico = any(item.tipo_item == "SERVICE" for item in itens)
    if venda.modo_cliente == "WALK_IN" and possui_servico:
        raise HTTPException(
            status_code=400,
            detail="Venda balcão não pode conter atendimentos.",
        )

    if len(venda.pagamentos or []) > 0:
        raise HTTPException(
            status_code=400,
            detail="Esta venda já possui pagamento registrado.",
        )

    valor_pagamento = _decimal_2(payload.pagamento.valor)
    valor_total = _decimal_2(venda.valor_total)

    if valor_total <= Decimal("0.00"):
        raise HTTPException(
            status_code=400,
            detail="A venda precisa ter valor total maior que zero para ser finalizada.",
        )

    if valor_pagamento != valor_total:
        raise HTTPException(
            status_code=400,
            detail="A venda só pode ser finalizada com pagamento integral.",
        )


def _atualizar_snapshots_cliente(venda: PdvVenda):
    if venda.cliente:
        if not venda.nome_cliente_snapshot:
            venda.nome_cliente_snapshot = getattr(venda.cliente, "nome", None)
        if not venda.telefone_cliente_snapshot:
            venda.telefone_cliente_snapshot = getattr(venda.cliente, "telefone", None)


def _gerar_financeiro_recebido_para_venda(
    db: Session,
    venda: PdvVenda,
    pagamento: PdvPagamento,
):
    data_base = pagamento.recebido_em.date() if pagamento.recebido_em else date.today()

    conta = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.origem_tipo == "PDV_VENDA",
            FinanceiroReceber.origem_id == venda.id,
        )
        .first()
    )

    if not conta:
        conta = FinanceiroReceber(
            empresa_id=venda.empresa_id,
            cliente_id=venda.cliente_id,
            origem_tipo="PDV_VENDA",
            origem_id=venda.id,
            descricao=f"Venda PDV {venda.numero_venda or venda.id}",
            observacao=venda.observacoes,
            valor=_decimal_2(venda.valor_total),
            valor_pago=_decimal_2(pagamento.valor),
            vencimento=data_base,
            data_pagamento=data_base,
            status="PAGO",
            created_at=_agora_utc(),
            updated_at=_agora_utc(),
        )
        db.add(conta)
        return conta

    conta.cliente_id = venda.cliente_id
    conta.descricao = f"Venda PDV {venda.numero_venda or venda.id}"
    conta.observacao = venda.observacoes
    conta.valor = _decimal_2(venda.valor_total)
    conta.valor_pago = _decimal_2(pagamento.valor)
    conta.vencimento = data_base
    conta.data_pagamento = data_base
    conta.status = "PAGO"
    conta.updated_at = _agora_utc()
    return conta


def _cancelar_financeiro_da_venda(db: Session, venda_id: int):
    contas = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.origem_tipo == "PDV_VENDA",
            FinanceiroReceber.origem_id == venda_id,
        )
        .all()
    )
    for conta in contas:
        db.delete(conta)


def _registrar_movimento_venda(
    db: Session,
    venda: PdvVenda,
    pagamento: PdvPagamento,
    usuario_id: int,
):
    movimento = CaixaMovimento(
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    movimento.definir_como_venda(
        empresa_id=venda.empresa_id,
        caixa_sessao_id=venda.caixa_sessao_id,
        valor=_decimal_2(pagamento.valor),
        forma_pagamento=pagamento.forma_pagamento,
        usuario_id=usuario_id,
        origem_id=venda.id,
        observacoes=f"Recebimento da venda {venda.numero_venda or venda.id}",
    )
    db.add(movimento)
    return movimento


def _escolher_caixa_para_estorno(db: Session, venda: PdvVenda) -> CaixaSessao:
    caixa_aberto_atual = _get_caixa_aberto_por_empresa(
        db,
        venda.empresa_id,
        for_update=True,
    )
    if caixa_aberto_atual:
        return caixa_aberto_atual
    return _get_caixa_sessao_or_404(db, venda.caixa_sessao_id, for_update=True)


def _registrar_movimento_estorno(
    db: Session,
    venda: PdvVenda,
    pagamento: PdvPagamento,
    usuario_id: int,
    gerente_autorizador_id: int | None,
):
    caixa_estorno = _escolher_caixa_para_estorno(db, venda)

    movimento = CaixaMovimento(
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    movimento.definir_como_estorno(
        empresa_id=venda.empresa_id,
        caixa_sessao_id=caixa_estorno.id,
        valor=_decimal_2(pagamento.valor),
        forma_pagamento=pagamento.forma_pagamento,
        usuario_id=usuario_id,
        origem_tipo="PDV_VENDA_CANCELAMENTO",
        origem_id=venda.id,
        motivo="CANCELAMENTO_VENDA",
        observacoes=f"Estorno do cancelamento da venda {venda.numero_venda or venda.id}",
        gerente_autorizador_id=gerente_autorizador_id,
    )
    db.add(movimento)
    return movimento


def buscar_clientes(
    db: Session,
    empresa_id: int,
    termo: str,
    limite: int = 20,
):
    _get_empresa_or_404(db, empresa_id)

    termo = (termo or "").strip()
    if not termo:
        return []

    tokens = _tokens_busca(termo)

    clientes = (
        db.query(Cliente)
        .filter(
            Cliente.empresa_id == empresa_id,
            Cliente.ativo.is_(True),
        )
        .order_by(Cliente.nome.asc())
        .all()
    )

    encontrados = [cliente for cliente in clientes if _match_cliente(cliente, tokens)]
    return encontrados[:limite]


def listar_atendimentos_prontos(
    db: Session,
    empresa_id: int,
    cliente_id: int | None = None,
):
    _get_empresa_or_404(db, empresa_id)

    query = (
        db.query(AtendimentoClinico)
        .options(
            joinedload(AtendimentoClinico.cliente),
            joinedload(AtendimentoClinico.pet),
            joinedload(AtendimentoClinico.itens),
        )
        .filter(
            AtendimentoClinico.empresa_id == empresa_id,
            AtendimentoClinico.status == "FINALIZADO",
            AtendimentoClinico.enviado_pdv.is_(False),
        )
        .order_by(AtendimentoClinico.id.desc())
    )

    if cliente_id:
        query = query.filter(AtendimentoClinico.cliente_id == cliente_id)

    return query.all()


def criar_venda(db: Session, payload: PdvVendaCreate) -> PdvVenda:
    _get_empresa_or_404(db, payload.empresa_id)

    caixa = _get_caixa_sessao_or_404(db, payload.caixa_sessao_id, for_update=True)
    _validar_caixa_para_venda(caixa, payload.empresa_id, exigir_aberto=True)

    venda = PdvVenda(
        empresa_id=payload.empresa_id,
        caixa_sessao_id=caixa.id,
        numero_venda=_gerar_numero_venda_provisorio(),
        observacoes=payload.observacoes,
        usuario_abertura_id=caixa.usuario_responsavel_id,
        aberta_em=_agora_utc(),
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )

    if payload.modo_cliente == "REGISTERED_CLIENT":
        cliente = _get_cliente_or_404(db, payload.cliente_id)
        if getattr(cliente, "empresa_id", None) != payload.empresa_id:
            raise HTTPException(
                status_code=400,
                detail="O cliente informado não pertence à empresa selecionada.",
            )
        venda.definir_cliente_cadastrado(cliente.id)
        venda.nome_cliente_snapshot = getattr(cliente, "nome", None)
        venda.telefone_cliente_snapshot = getattr(cliente, "telefone", None)
    else:
        venda.definir_como_balcao(
            nome_cliente_snapshot=payload.nome_cliente_snapshot,
            telefone_cliente_snapshot=payload.telefone_cliente_snapshot,
        )

    db.add(venda)
    db.flush()

    venda.numero_venda = _gerar_numero_venda(venda.id)
    venda.recalcular_totais()

    db.commit()
    db.refresh(venda)

    return _recarregar_venda(db, venda.id)


def listar_vendas(
    db: Session,
    empresa_id: int,
    status: str | None = None,
    limite: int = 50,
):
    _get_empresa_or_404(db, empresa_id)

    query = (
        _carregar_venda_query(db)
        .filter(PdvVenda.empresa_id == empresa_id)
        .order_by(PdvVenda.id.desc())
    )

    if status:
        query = query.filter(PdvVenda.status == status)

    return query.limit(limite).all()


def obter_venda(db: Session, venda_id: int) -> PdvVenda:
    return _get_venda_or_404(db, venda_id)


def atualizar_venda(
    db: Session,
    venda_id: int,
    payload: PdvVendaUpdate,
) -> PdvVenda:
    venda = _get_venda_or_404(db, venda_id, for_update=True)
    _validar_venda_aberta(venda)

    if payload.observacoes is not None:
        venda.observacoes = payload.observacoes

    if payload.desconto_valor is not None:
        venda.desconto_valor = _decimal_2(payload.desconto_valor)

    if payload.acrescimo_valor is not None:
        venda.acrescimo_valor = _decimal_2(payload.acrescimo_valor)

    venda.recalcular_totais()

    db.commit()
    return _recarregar_venda(db, venda.id)


def adicionar_item(
    db: Session,
    venda_id: int,
    payload: PdvVendaItemAdd,
) -> PdvVenda:
    venda = _get_venda_or_404(db, venda_id, for_update=True)
    _validar_venda_aberta(venda)

    item = PdvVendaItem(
        venda_id=venda.id,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )

    if payload.tipo_item == "SERVICE":
        atendimento = _get_atendimento_or_404(
            db,
            payload.atendimento_clinico_id,
            for_update=True,
        )
        _validar_atendimento_disponivel_para_pdv(db, atendimento, venda)

        valor_total = _calcular_total_atendimento(atendimento)
        if valor_total <= Decimal("0.00"):
            raise HTTPException(
                status_code=400,
                detail="O atendimento não possui valor faturável para envio ao PDV.",
            )

        item.definir_como_servico(
            atendimento_clinico_id=atendimento.id,
            descricao_snapshot=_descricao_atendimento(atendimento),
            valor_unitario=valor_total,
            quantidade=Decimal("1.000"),
            desconto_valor=payload.desconto_valor or Decimal("0.00"),
            observacao=payload.observacao,
        )
    else:
        item.definir_como_produto(
            produto_id=payload.produto_id,
            descricao_snapshot=payload.descricao_snapshot,
            valor_unitario=payload.valor_unitario,
            quantidade=payload.quantidade,
            desconto_valor=payload.desconto_valor,
            observacao=payload.observacao,
        )

    db.add(item)
    db.flush()

    venda.recalcular_totais()
    _atualizar_snapshots_cliente(venda)

    db.commit()
    return _recarregar_venda(db, venda.id)


def remover_item(db: Session, venda_id: int, item_id: int) -> PdvVenda:
    venda = _get_venda_or_404(db, venda_id, for_update=True)
    _validar_venda_aberta(venda)

    item = (
        db.query(PdvVendaItem)
        .filter(
            PdvVendaItem.id == item_id,
            PdvVendaItem.venda_id == venda.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item da venda não encontrado.")

    db.delete(item)
    db.flush()

    venda.recalcular_totais()

    db.commit()
    return _recarregar_venda(db, venda.id)


def checkout_venda(
    db: Session,
    venda_id: int,
    payload: PdvCheckoutRequest,
) -> PdvVenda:
    venda = _get_venda_or_404(db, venda_id, for_update=True)
    caixa = _get_caixa_sessao_or_404(db, venda.caixa_sessao_id, for_update=True)

    venda = _recarregar_venda(db, venda.id)
    venda.recalcular_totais()
    _validar_checkout(venda, caixa, payload)

    if payload.observacoes is not None:
        venda.observacoes = payload.observacoes

    operador_recebimento = _resolver_usuario_operacao(
        db,
        empresa_id=venda.empresa_id,
        usuario_id=payload.pagamento.usuario_id,
        fallback_usuario_id=(
            venda.usuario_abertura_id or caixa.usuario_responsavel_id or caixa.usuario_abertura_id
        ),
        label="Operador do recebimento",
    )

    recebido_em = payload.pagamento.recebido_em or _agora_utc()

    pagamento = PdvPagamento(
        venda_id=venda.id,
        forma_pagamento=payload.pagamento.forma_pagamento,
        valor=_decimal_2(payload.pagamento.valor),
        status="RECEBIDO",
        referencia=payload.pagamento.referencia,
        observacoes=payload.pagamento.observacoes,
        usuario_id=operador_recebimento.id,
        recebido_em=recebido_em,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    db.add(pagamento)
    db.flush()

    _registrar_movimento_venda(
        db,
        venda=venda,
        pagamento=pagamento,
        usuario_id=operador_recebimento.id,
    )

    for item in venda.itens:
        if item.tipo_item == "SERVICE" and item.atendimento_clinico_id:
            atendimento = _get_atendimento_or_404(
                db,
                item.atendimento_clinico_id,
                for_update=True,
            )
            if hasattr(atendimento, "marcar_enviado_pdv") and callable(atendimento.marcar_enviado_pdv):
                atendimento.marcar_enviado_pdv()
            else:
                atendimento.enviado_pdv = True
                if hasattr(atendimento, "updated_at"):
                    atendimento.updated_at = datetime.utcnow()

    _gerar_financeiro_recebido_para_venda(db, venda, pagamento)
    venda.fechar(usuario_fechamento_id=operador_recebimento.id)

    db.commit()
    return _recarregar_venda(db, venda.id)


def cancelar_venda(
    db: Session,
    venda_id: int,
    payload: PdvCancelRequest,
) -> PdvVenda:
    venda = _get_venda_or_404(db, venda_id, for_update=True)

    if venda.status == "CANCELADA":
        return _recarregar_venda(db, venda.id)

    caixa_venda = _get_caixa_sessao_or_404(db, venda.caixa_sessao_id, for_update=True)
    venda = _recarregar_venda(db, venda.id)

    usuario_cancelamento = _resolver_usuario_operacao(
        db,
        empresa_id=venda.empresa_id,
        usuario_id=payload.usuario_cancelamento_id,
        fallback_usuario_id=(
            venda.usuario_fechamento_id
            or venda.usuario_abertura_id
            or caixa_venda.usuario_responsavel_id
            or caixa_venda.usuario_abertura_id
        ),
        label="Operador do cancelamento",
    )

    gerente_autorizador_id = None
    motivo_cancelamento = (payload.motivo_cancelamento or "").strip() or None

    if venda.status == "FECHADA":
        if not motivo_cancelamento:
            raise HTTPException(
                status_code=400,
                detail="Motivo do cancelamento é obrigatório para venda fechada.",
            )

        gerente = _validar_gerente(
            db,
            empresa_id=venda.empresa_id,
            gerente_id=payload.gerente_autorizador_id,
            senha_gerente=payload.senha_gerente,
        )
        gerente_autorizador_id = gerente.id

        for pagamento in venda.pagamentos or []:
            if pagamento.status == "CANCELADO":
                continue

            pagamento.cancelar(
                observacoes="Pagamento cancelado por cancelamento da venda.",
            )
            _registrar_movimento_estorno(
                db,
                venda=venda,
                pagamento=pagamento,
                usuario_id=usuario_cancelamento.id,
                gerente_autorizador_id=gerente_autorizador_id,
            )

        for item in venda.itens or []:
            if item.tipo_item == "SERVICE" and item.atendimento_clinico_id:
                atendimento = _get_atendimento_or_404(
                    db,
                    item.atendimento_clinico_id,
                    for_update=True,
                )
                atendimento.enviado_pdv = False
                if hasattr(atendimento, "updated_at"):
                    atendimento.updated_at = datetime.utcnow()

        _cancelar_financeiro_da_venda(db, venda.id)

    venda.cancelar(
        motivo_cancelamento=motivo_cancelamento,
        usuario_cancelamento_id=usuario_cancelamento.id,
    )

    db.commit()
    return _recarregar_venda(db, venda.id)