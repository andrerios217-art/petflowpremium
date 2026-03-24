from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import verify_password
from app.models.agendamento import Agendamento
from app.models.agendamento_servico import AgendamentoServico
from app.models.atendimento_clinico import AtendimentoClinico
from app.models.caixa_movimento import CaixaMovimento
from app.models.caixa_sessao import CaixaSessao
from app.models.cliente import Cliente
from app.models.empresa import Empresa
from app.models.estoque_deposito import EstoqueDeposito
from app.models.estoque_movimento import EstoqueMovimento
from app.models.estoque_saldo import EstoqueSaldo
from app.models.financeiro_receber import FinanceiroReceber
from app.models.pdv_pagamento import PdvPagamento
from app.models.pdv_venda import PdvVenda
from app.models.pdv_venda_item import PdvVendaItem
from app.models.producao import Producao
from app.models.produto import Produto
from app.models.usuario import Usuario
from app.schemas.pdv import (
    PdvCancelRequest,
    PdvCheckoutRequest,
    PdvVendaCreate,
    PdvVendaItemAdd,
    PdvVendaProducaoCreate,
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


def _match_cliente(cliente: Cliente, tokens: list[str], telefone_digits: str) -> bool:
    if not tokens and not telefone_digits:
        return True

    nome = _normalizar_texto(getattr(cliente, "nome", None))
    cpf = _somente_digitos(getattr(cliente, "cpf", None))
    telefone = _somente_digitos(getattr(cliente, "telefone", None))

    if telefone_digits and telefone_digits in telefone:
        return True

    base = " ".join([nome, cpf, telefone]).strip()
    if not base:
        return False

    return all(token in base for token in tokens)


def _match_produto(produto: Produto, tokens: list[str]) -> bool:
    if not tokens:
        return True

    nome = _normalizar_texto(getattr(produto, "nome", None))
    sku = _normalizar_texto(getattr(produto, "sku", None))
    descricao = _normalizar_texto(getattr(produto, "descricao", None))

    base = " ".join([nome, sku, descricao]).strip()
    if not base:
        return False

    return all(token in base for token in tokens)


def _carregar_venda_query(db: Session):
    return (
        db.query(PdvVenda)
        .options(
            joinedload(PdvVenda.cliente),
            joinedload(PdvVenda.itens),
            joinedload(PdvVenda.pagamentos),
        )
    )


def _query_venda_lock(db: Session):
    return db.query(PdvVenda).with_for_update()


def _carregar_atendimento_query(db: Session):
    return (
        db.query(AtendimentoClinico)
        .options(
            joinedload(AtendimentoClinico.cliente),
            joinedload(AtendimentoClinico.pet),
            joinedload(AtendimentoClinico.itens),
        )
    )


def _query_atendimento_lock(db: Session):
    return db.query(AtendimentoClinico).with_for_update()


def _get_empresa_or_404(db: Session, empresa_id: int) -> Empresa:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")
    return empresa


def _get_cliente_or_404(db: Session, cliente_id: int | None) -> Cliente:
    if not cliente_id:
        raise HTTPException(status_code=400, detail="cliente_id inválido.")
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return cliente


def _get_usuario_or_404(db: Session, usuario_id: int) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return usuario


def _get_produto_catalogo_or_404(db: Session, produto_id: int, empresa_id: int) -> Produto:
    produto = (
        db.query(Produto)
        .filter(
            Produto.id == produto_id,
            Produto.empresa_id == empresa_id,
        )
        .first()
    )
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado para esta empresa.")
    if not produto.ativo:
        raise HTTPException(status_code=400, detail="Produto inativo não pode ser vendido no PDV.")
    return produto


def _get_venda_or_404(db: Session, venda_id: int, for_update: bool = False) -> PdvVenda:
    query = _query_venda_lock(db) if for_update else db.query(PdvVenda)
    venda = query.filter(PdvVenda.id == venda_id).first()
    if not venda:
        raise HTTPException(status_code=404, detail="Venda não encontrada.")
    return venda


def _get_caixa_sessao_or_404(db: Session, caixa_sessao_id: int, for_update: bool = False) -> CaixaSessao:
    query = db.query(CaixaSessao).with_for_update() if for_update else db.query(CaixaSessao)
    caixa = query.filter(CaixaSessao.id == caixa_sessao_id).first()
    if not caixa:
        raise HTTPException(status_code=404, detail="Sessão de caixa não encontrada.")
    return caixa


def _get_caixa_aberto_por_empresa(db: Session, empresa_id: int) -> CaixaSessao | None:
    return (
        db.query(CaixaSessao)
        .filter(
            CaixaSessao.empresa_id == empresa_id,
            CaixaSessao.status == "ABERTO",
        )
        .order_by(CaixaSessao.id.desc())
        .first()
    )


def _get_atendimento_or_404(db: Session, atendimento_id: int, for_update: bool = False) -> AtendimentoClinico:
    query = _query_atendimento_lock(db) if for_update else db.query(AtendimentoClinico)
    atendimento = query.filter(AtendimentoClinico.id == atendimento_id).first()
    if not atendimento:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado.")
    return atendimento


def _recarregar_venda(db: Session, venda_id: int) -> PdvVenda:
    return _carregar_venda_query(db).filter(PdvVenda.id == venda_id).first()


def _recarregar_atendimento(db: Session, atendimento_id: int) -> AtendimentoClinico:
    return _carregar_atendimento_query(db).filter(AtendimentoClinico.id == atendimento_id).first()


def _gerar_numero_venda(venda_id: int) -> str:
    return f"PDV-{venda_id:06d}"


def _gerar_numero_venda_provisorio() -> str:
    return f"PV-{int(_agora_utc().timestamp())}"


def _calcular_total_atendimento(atendimento: AtendimentoClinico) -> Decimal:
    total = Decimal("0.00")
    for item in getattr(atendimento, "itens", []) or []:
        total += Decimal(str(getattr(item, "valor_total", 0) or 0))
    return _decimal_2(total)


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


def _descricao_producao(producao: Producao) -> str:
    agendamento = getattr(producao, "agendamento", None)
    pet = getattr(agendamento, "pet", None) if agendamento else None
    pet_nome = getattr(pet, "nome", None) if pet else None

    nomes = []
    for item in getattr(agendamento, "servicos_agendamento", []) or []:
        servico = getattr(item, "servico", None)
        nome_servico = (getattr(servico, "nome", None) or "").strip() if servico else ""
        if nome_servico:
            nomes.append(nome_servico)

    descricao_base = ", ".join(nomes[:5]) if nomes else "Serviços petshop"
    if len(nomes) > 5:
        descricao_base += ", ..."

    if pet_nome:
        return f"{descricao_base} - {pet_nome}"
    return descricao_base


def _calcular_total_producao(producao: Producao) -> Decimal:
    total = Decimal("0.00")
    agendamento = getattr(producao, "agendamento", None)
    for item in getattr(agendamento, "servicos_agendamento", []) or []:
        total += Decimal(str(getattr(item, "preco", 0) or 0))
    return _decimal_2(total)


def _validar_venda_aberta(venda: PdvVenda):
    if venda.status != "ABERTA":
        raise HTTPException(status_code=400, detail="A venda não está aberta para alterações.")


def _validar_gerente(gerente: Usuario):
    tipo = str(getattr(gerente, "tipo", "") or "").strip().lower()
    if tipo not in {"gerente", "admin"}:
        raise HTTPException(status_code=403, detail="Usuário informado não é gerente.")


def _validar_caixa_para_venda(caixa: CaixaSessao, empresa_id: int, exigir_aberto: bool = True):
    if caixa.empresa_id != empresa_id:
        raise HTTPException(status_code=400, detail="Caixa não pertence à empresa informada.")
    if exigir_aberto and caixa.status != "ABERTO":
        raise HTTPException(status_code=400, detail="Abra o caixa antes de realizar vendas.")


def _validar_atendimento_disponivel_para_pdv(db: Session, atendimento: AtendimentoClinico, venda: PdvVenda):
    if atendimento.empresa_id != venda.empresa_id:
        raise HTTPException(status_code=400, detail="Atendimento não pertence à empresa informada.")
    if atendimento.status != "FINALIZADO":
        raise HTTPException(status_code=400, detail="Atendimento não está finalizado para envio ao PDV.")
    if atendimento.enviado_pdv:
        raise HTTPException(status_code=400, detail="Atendimento já foi enviado ao PDV.")
    if venda.modo_cliente != "REGISTERED_CLIENT":
        raise HTTPException(status_code=400, detail="Venda balcão não aceita itens de serviço.")
    if venda.cliente_id != atendimento.cliente_id:
        raise HTTPException(status_code=400, detail="Atendimento pertence a um cliente diferente da venda atual.")

    existe_item = (
        db.query(PdvVendaItem)
        .join(PdvVenda, PdvVenda.id == PdvVendaItem.venda_id)
        .filter(
            PdvVendaItem.atendimento_clinico_id == atendimento.id,
            PdvVenda.status == "ABERTA",
        )
        .first()
    )
    if existe_item:
        raise HTTPException(status_code=400, detail="Este atendimento já está vinculado a outra venda aberta.")


def _atualizar_snapshots_cliente(venda: PdvVenda):
    if venda.modo_cliente != "REGISTERED_CLIENT" or not venda.cliente:
        return
    venda.nome_cliente_snapshot = getattr(venda.cliente, "nome", None)
    venda.telefone_cliente_snapshot = getattr(venda.cliente, "telefone", None)
    venda.updated_at = _agora_utc()


def _gerar_financeiro_recebido_para_venda(db: Session, venda: PdvVenda, forma_pagamento: str, valor: Decimal):
    receber_existente = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.origem_tipo == "PDV_VENDA",
            FinanceiroReceber.origem_id == venda.id,
        )
        .first()
    )
    if receber_existente:
        return receber_existente

    hoje = _agora_utc().date()

    receber = FinanceiroReceber(
        empresa_id=venda.empresa_id,
        cliente_id=venda.cliente_id,
        origem_tipo="PDV_VENDA",
        origem_id=venda.id,
        descricao=f"Venda PDV {venda.numero_venda or venda.id}",
        observacao=f"Forma: {forma_pagamento}",
        valor=_decimal_2(valor),
        valor_pago=_decimal_2(valor),
        vencimento=hoje,
        data_pagamento=hoje,
        status="PAGO",
    )
    db.add(receber)
    db.flush()
    return receber


def _cancelar_financeiro_da_venda(db: Session, venda: PdvVenda):
    receber = (
        db.query(FinanceiroReceber)
        .filter(
            FinanceiroReceber.origem_tipo == "PDV_VENDA",
            FinanceiroReceber.origem_id == venda.id,
        )
        .first()
    )
    if not receber:
        return None
    receber.status = "CANCELADO"
    receber.updated_at = _agora_utc()
    db.add(receber)
    db.flush()
    return receber


def _registrar_movimento_venda(db: Session, venda: PdvVenda, forma_pagamento: str, valor: Decimal):
    movimento = CaixaMovimento(
        empresa_id=venda.empresa_id,
        caixa_sessao_id=venda.caixa_sessao_id,
        tipo_movimento="VENDA",
        forma_pagamento=forma_pagamento,
        valor=_decimal_2(valor),
        origem_tipo="PDV_VENDA",
        origem_id=venda.id,
        motivo="Venda PDV",
        usuario_id=venda.usuario_abertura_id or 0,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    db.add(movimento)
    db.flush()
    return movimento


def _escolher_caixa_para_estorno(db: Session, venda: PdvVenda) -> CaixaSessao:
    caixa_atual = _get_caixa_aberto_por_empresa(db, venda.empresa_id)
    if caixa_atual:
        return caixa_atual
    return _get_caixa_sessao_or_404(db, venda.caixa_sessao_id)


def _registrar_movimento_estorno(db: Session, venda: PdvVenda, forma_pagamento: str, valor: Decimal):
    caixa = _escolher_caixa_para_estorno(db, venda)

    movimento = CaixaMovimento(
        empresa_id=venda.empresa_id,
        caixa_sessao_id=caixa.id,
        tipo_movimento="ESTORNO",
        forma_pagamento=forma_pagamento,
        valor=_decimal_2(valor),
        origem_tipo="PDV_VENDA",
        origem_id=venda.id,
        motivo="Estorno venda PDV",
        usuario_id=venda.usuario_cancelamento_id or venda.usuario_abertura_id or 0,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    db.add(movimento)
    db.flush()
    return movimento


def _get_deposito_padrao_pdv_or_404(db: Session, empresa_id: int) -> EstoqueDeposito:
    deposito = (
        db.query(EstoqueDeposito)
        .filter(EstoqueDeposito.empresa_id == empresa_id)
        .order_by(EstoqueDeposito.id.asc())
        .first()
    )
    if not deposito:
        raise HTTPException(
            status_code=400,
            detail="Nenhum depósito cadastrado para a empresa. Configure o estoque antes de finalizar a venda.",
        )
    return deposito


def _buscar_saldo_for_update(
    db: Session,
    empresa_id: int,
    deposito_id: int,
    produto_id: int,
) -> EstoqueSaldo | None:
    return (
        db.query(EstoqueSaldo)
        .filter(
            EstoqueSaldo.empresa_id == empresa_id,
            EstoqueSaldo.deposito_id == deposito_id,
            EstoqueSaldo.produto_id == produto_id,
        )
        .with_for_update()
        .first()
    )


def _itens_produto_para_baixa(venda: PdvVenda) -> list[PdvVendaItem]:
    itens = []
    for item in venda.itens or []:
        if getattr(item, "deve_baixar_estoque", False):
            itens.append(item)
    return itens


def _validar_saldo_estoque_venda(
    db: Session,
    venda: PdvVenda,
    deposito_id: int,
):
    for item in _itens_produto_para_baixa(venda):
        saldo = _buscar_saldo_for_update(
            db=db,
            empresa_id=venda.empresa_id,
            deposito_id=deposito_id,
            produto_id=item.produto_id,
        )

        saldo_atual = _decimal_3(saldo.quantidade_atual if saldo else Decimal("0.000"))
        quantidade_item = _decimal_3(item.quantidade)

        if saldo_atual < quantidade_item:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Saldo insuficiente para o produto ID {item.produto_id}. "
                    f"Disponível: {saldo_atual}. Necessário: {quantidade_item}."
                ),
            )


def _baixar_estoque_venda(
    db: Session,
    venda: PdvVenda,
    deposito_id: int,
    usuario_id: int | None,
):
    for item in _itens_produto_para_baixa(venda):
        saldo = _buscar_saldo_for_update(
            db=db,
            empresa_id=venda.empresa_id,
            deposito_id=deposito_id,
            produto_id=item.produto_id,
        )

        if not saldo:
            saldo = EstoqueSaldo(
                empresa_id=venda.empresa_id,
                deposito_id=deposito_id,
                produto_id=item.produto_id,
                quantidade_atual=Decimal("0.000"),
                updated_at=_agora_utc(),
            )
            db.add(saldo)
            db.flush()

            saldo = _buscar_saldo_for_update(
                db=db,
                empresa_id=venda.empresa_id,
                deposito_id=deposito_id,
                produto_id=item.produto_id,
            )

        saldo_antes = _decimal_3(saldo.quantidade_atual)
        quantidade_item = _decimal_3(item.quantidade)
        saldo_depois = _decimal_3(saldo_antes - quantidade_item)

        if saldo_depois < Decimal("0.000"):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Saldo insuficiente para o produto ID {item.produto_id}. "
                    f"Disponível: {saldo_antes}. Necessário: {quantidade_item}."
                ),
            )

        movimento = EstoqueMovimento(
            empresa_id=venda.empresa_id,
            deposito_id=deposito_id,
            produto_id=item.produto_id,
            usuario_id=usuario_id,
            tipo_movimento="SAIDA",
            origem="PDV",
            origem_id=venda.id,
            quantidade=quantidade_item,
            saldo_antes=saldo_antes,
            saldo_depois=saldo_depois,
            custo_unitario=None,
            documento_referencia=venda.numero_venda,
            observacao=f"Baixa automática por venda PDV #{venda.id}",
            created_at=_agora_utc(),
        )
        db.add(movimento)

        saldo.quantidade_atual = saldo_depois
        saldo.updated_at = _agora_utc()
        db.add(saldo)

    db.flush()


def buscar_clientes(db: Session, empresa_id: int, termo: str, limite: int = 20) -> list[Cliente]:
    _get_empresa_or_404(db, empresa_id)

    termo = (termo or "").strip()
    if not termo:
        return []

    telefone_digits = _somente_digitos(termo)
    tokens = _tokens_busca(termo)

    candidatos = (
        db.query(Cliente)
        .filter(Cliente.empresa_id == empresa_id)
        .order_by(Cliente.nome.asc(), Cliente.id.asc())
        .limit(max(limite * 5, 50))
        .all()
    )

    encontrados = [c for c in candidatos if _match_cliente(c, tokens, telefone_digits)]
    return encontrados[:limite]


def buscar_produtos(db: Session, empresa_id: int, termo: str, limite: int = 20) -> list[Produto]:
    _get_empresa_or_404(db, empresa_id)

    termo = (termo or "").strip()
    if not termo:
        return []

    tokens = _tokens_busca(termo)
    like = f"%{termo.strip()}%"

    query = (
        db.query(Produto)
        .filter(
            Produto.empresa_id == empresa_id,
            Produto.ativo.is_(True),
            or_(
                Produto.nome.ilike(like),
                Produto.sku.ilike(like),
                Produto.descricao.ilike(like),
            ),
        )
        .order_by(Produto.nome.asc(), Produto.id.asc())
        .limit(max(limite * 3, 50))
    )

    candidatos = query.all()
    encontrados = [p for p in candidatos if _match_produto(p, tokens)]
    return encontrados[:limite]


def listar_atendimentos_prontos(db: Session, empresa_id: int, cliente_id: int | None = None):
    _get_empresa_or_404(db, empresa_id)

    query = (
        _carregar_atendimento_query(db)
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


def listar_producao_prontos(db: Session, empresa_id: int, cliente_id: int | None = None):
    _get_empresa_or_404(db, empresa_id)

    query = (
        db.query(Producao)
        .join(Producao.agendamento)
        .options(
            joinedload(Producao.agendamento).joinedload(Agendamento.cliente),
            joinedload(Producao.agendamento).joinedload(Agendamento.pet),
            joinedload(Producao.agendamento)
            .joinedload(Agendamento.servicos_agendamento)
            .joinedload(AgendamentoServico.servico),
        )
        .filter(
            Agendamento.empresa_id == empresa_id,
            Producao.finalizado.is_(True),
            Producao.aguardando_pdv.is_(True),
            Producao.enviado_pdv.is_(False),
        )
        .order_by(Producao.id.desc())
    )

    if cliente_id:
        query = query.filter(Agendamento.cliente_id == cliente_id)

    return query.all()


def enviar_producao_para_pdv(db: Session, payload: PdvVendaProducaoCreate) -> PdvVenda:
    _get_empresa_or_404(db, payload.empresa_id)

    producao_lock = (
        db.query(Producao)
        .filter(Producao.id == payload.producao_id)
        .with_for_update()
        .first()
    )
    if not producao_lock:
        raise HTTPException(status_code=404, detail="Produção não encontrada.")

    producao = (
        db.query(Producao)
        .options(
            selectinload(Producao.agendamento).selectinload(Agendamento.cliente),
            selectinload(Producao.agendamento).selectinload(Agendamento.pet),
            selectinload(Producao.agendamento)
            .selectinload(Agendamento.servicos_agendamento)
            .selectinload(AgendamentoServico.servico),
        )
        .filter(Producao.id == payload.producao_id)
        .first()
    )
    if not producao:
        raise HTTPException(status_code=404, detail="Produção não encontrada.")

    agendamento = producao.agendamento
    if not agendamento or agendamento.empresa_id != payload.empresa_id:
        raise HTTPException(status_code=400, detail="A produção não pertence à empresa informada.")

    if not producao.finalizado:
        raise HTTPException(status_code=400, detail="Produção ainda não está finalizada.")
    if not getattr(producao, "aguardando_pdv", False):
        raise HTTPException(status_code=400, detail="Produção não está marcada como aguardando PDV.")
    if getattr(producao, "enviado_pdv", False):
        raise HTTPException(status_code=400, detail="Produção já foi enviada ao PDV.")

    caixa = _get_caixa_sessao_or_404(db, payload.caixa_sessao_id, for_update=True)
    _validar_caixa_para_venda(caixa, payload.empresa_id, exigir_aberto=True)

    cliente = _get_cliente_or_404(db, agendamento.cliente_id)
    if getattr(cliente, "empresa_id", None) != payload.empresa_id:
        raise HTTPException(status_code=400, detail="Cliente não pertence à empresa informada.")

    total = _calcular_total_producao(producao)
    if total <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Produção sem valor faturável para PDV.")

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
    venda.definir_cliente_cadastrado(cliente.id)
    venda.nome_cliente_snapshot = getattr(cliente, "nome", None)
    venda.telefone_cliente_snapshot = getattr(cliente, "telefone", None)

    db.add(venda)
    db.flush()

    venda.numero_venda = _gerar_numero_venda(venda.id)

    descricao = f"Produção #{producao.id} - {_descricao_producao(producao)}"
    item = PdvVendaItem(
        venda_id=venda.id,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    item.definir_como_item_producao(
        descricao_snapshot=descricao,
        valor_unitario=total,
        quantidade=Decimal("1.000"),
        desconto_valor=Decimal("0.00"),
        observacao=None,
        produto_id=None,
    )

    db.add(item)
    db.flush()

    venda.recalcular_totais()
    _atualizar_snapshots_cliente(venda)

    producao.enviado_pdv = True
    producao.enviado_pdv_em = _agora_utc()
    producao.aguardando_pdv = False
    db.add(producao)

    db.commit()
    return _recarregar_venda(db, venda.id)


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
            raise HTTPException(status_code=400, detail="O cliente informado não pertence à empresa informada.")
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


def listar_vendas(db: Session, empresa_id: int, status: str | None = None, limite: int = 50):
    _get_empresa_or_404(db, empresa_id)

    query = (
        db.query(PdvVenda)
        .options(joinedload(PdvVenda.cliente))
        .filter(PdvVenda.empresa_id == empresa_id)
        .order_by(PdvVenda.id.desc())
    )

    if status:
        query = query.filter(PdvVenda.status == status)

    return query.limit(limite).all()


def obter_venda(db: Session, venda_id: int) -> PdvVenda:
    _get_venda_or_404(db, venda_id)
    return _recarregar_venda(db, venda_id)


def atualizar_venda(db: Session, venda_id: int, payload: PdvVendaUpdate) -> PdvVenda:
    venda_lock = _get_venda_or_404(db, venda_id, for_update=True)
    venda = _recarregar_venda(db, venda_lock.id)
    _validar_venda_aberta(venda)

    if payload.observacoes is not None:
        venda.observacoes = payload.observacoes

    if payload.desconto_valor is not None:
        venda.desconto_valor = _decimal_2(payload.desconto_valor)

    if payload.acrescimo_valor is not None:
        venda.acrescimo_valor = _decimal_2(payload.acrescimo_valor)

    venda.recalcular_totais()
    _atualizar_snapshots_cliente(venda)

    db.commit()
    return _recarregar_venda(db, venda.id)


def adicionar_item(db: Session, venda_id: int, payload: PdvVendaItemAdd) -> PdvVenda:
    venda_lock = _get_venda_or_404(db, venda_id, for_update=True)
    venda = _recarregar_venda(db, venda_lock.id)
    _validar_venda_aberta(venda)

    item = PdvVendaItem(
        venda_id=venda.id,
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )

    if payload.tipo_item == "SERVICE":
        atendimento_lock = _get_atendimento_or_404(db, payload.atendimento_clinico_id, for_update=True)
        atendimento = _recarregar_atendimento(db, atendimento_lock.id)
        _validar_atendimento_disponivel_para_pdv(db, atendimento, venda)

        valor_total = _calcular_total_atendimento(atendimento)
        item.definir_como_servico(
            atendimento_clinico_id=atendimento.id,
            descricao_snapshot=_descricao_atendimento(atendimento),
            valor_unitario=valor_total,
            quantidade=Decimal("1.000"),
            desconto_valor=payload.desconto_valor or Decimal("0.00"),
            observacao=payload.observacao,
        )
    else:
        if not payload.produto_id:
            raise HTTPException(status_code=400, detail="produto_id é obrigatório para item de produto.")

        produto = _get_produto_catalogo_or_404(
            db=db,
            produto_id=payload.produto_id,
            empresa_id=venda.empresa_id,
        )

        descricao_snapshot = payload.descricao_snapshot or produto.nome
        valor_unitario = payload.valor_unitario
        if valor_unitario is None:
            valor_unitario = produto.preco_venda_atual

        item.definir_como_produto_catalogo(
            produto_id=produto.id,
            descricao_snapshot=descricao_snapshot,
            valor_unitario=valor_unitario,
            quantidade=payload.quantidade,
            desconto_valor=payload.desconto_valor,
            observacao=payload.observacao,
            gera_movimento_estoque=True,
        )

    db.add(item)
    db.flush()

    venda.recalcular_totais()
    _atualizar_snapshots_cliente(venda)

    db.commit()
    return _recarregar_venda(db, venda.id)


def remover_item(db: Session, venda_id: int, item_id: int) -> PdvVenda:
    venda_lock = _get_venda_or_404(db, venda_id, for_update=True)
    venda = _recarregar_venda(db, venda_lock.id)
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
        raise HTTPException(status_code=404, detail="Item não encontrado nesta venda.")

    if item.tipo_item == "SERVICE" and item.atendimento_clinico_id:
        atendimento = _get_atendimento_or_404(db, item.atendimento_clinico_id, for_update=True)
        atendimento.enviado_pdv = False
        atendimento.updated_at = _agora_utc()
        db.add(atendimento)

    db.delete(item)
    db.flush()

    venda.recalcular_totais()
    _atualizar_snapshots_cliente(venda)

    db.commit()
    return _recarregar_venda(db, venda.id)


def checkout_venda(db: Session, venda_id: int, payload: PdvCheckoutRequest) -> PdvVenda:
    venda_lock = _get_venda_or_404(db, venda_id, for_update=True)
    venda = _recarregar_venda(db, venda_lock.id)
    _validar_venda_aberta(venda)

    if payload.observacoes is not None:
        venda.observacoes = payload.observacoes

    venda.recalcular_totais()
    total = _decimal_2(venda.valor_total)

    pagamento_payload = payload.pagamento
    forma_pagamento = pagamento_payload.forma_pagamento
    valor_pago = _decimal_2(pagamento_payload.valor)
    usuario_fechamento_id = pagamento_payload.usuario_id or venda.usuario_abertura_id

    itens_para_baixa = _itens_produto_para_baixa(venda)
    deposito_pdv = None
    if itens_para_baixa:
        deposito_pdv = _get_deposito_padrao_pdv_or_404(db, venda.empresa_id)
        _validar_saldo_estoque_venda(
            db=db,
            venda=venda,
            deposito_id=deposito_pdv.id,
        )

    if total == Decimal("0.00"):
        if valor_pago != Decimal("0.00"):
            raise HTTPException(status_code=400, detail="Venda zerada: valor pago deve ser 0,00.")

        if itens_para_baixa and deposito_pdv:
            _baixar_estoque_venda(
                db=db,
                venda=venda,
                deposito_id=deposito_pdv.id,
                usuario_id=usuario_fechamento_id,
            )

        for item in venda.itens or []:
            if item.tipo_item == "SERVICE" and item.atendimento_clinico_id:
                atendimento = _get_atendimento_or_404(db, item.atendimento_clinico_id, for_update=True)
                atendimento.enviado_pdv = True
                atendimento.updated_at = _agora_utc()
                db.add(atendimento)

        venda.fechar(usuario_fechamento_id=usuario_fechamento_id)
        db.add(venda)

        db.commit()
        return _recarregar_venda(db, venda.id)

    if valor_pago <= Decimal("0.00"):
        raise HTTPException(status_code=400, detail="Valor de pagamento inválido.")
    if valor_pago != total:
        raise HTTPException(status_code=400, detail="Nesta versão, valor pago deve ser igual ao total da venda.")

    pagamento = PdvPagamento(
        venda_id=venda.id,
        forma_pagamento=forma_pagamento,
        valor=valor_pago,
        status="RECEBIDO",
        referencia=pagamento_payload.referencia,
        observacoes=pagamento_payload.observacoes,
        usuario_id=usuario_fechamento_id,
        recebido_em=pagamento_payload.recebido_em or _agora_utc(),
        created_at=_agora_utc(),
        updated_at=_agora_utc(),
    )
    db.add(pagamento)
    db.flush()

    if itens_para_baixa and deposito_pdv:
        _baixar_estoque_venda(
            db=db,
            venda=venda,
            deposito_id=deposito_pdv.id,
            usuario_id=pagamento.usuario_id,
        )

    for item in venda.itens or []:
        if item.tipo_item == "SERVICE" and item.atendimento_clinico_id:
            atendimento = _get_atendimento_or_404(db, item.atendimento_clinico_id, for_update=True)
            atendimento.enviado_pdv = True
            atendimento.updated_at = _agora_utc()
            db.add(atendimento)

    _gerar_financeiro_recebido_para_venda(db, venda, forma_pagamento=forma_pagamento, valor=valor_pago)
    _registrar_movimento_venda(db, venda, forma_pagamento=forma_pagamento, valor=valor_pago)

    venda.fechar(usuario_fechamento_id=pagamento.usuario_id)
    db.add(venda)

    db.commit()
    return _recarregar_venda(db, venda.id)


def _senha_valida(gerente: Usuario, senha: str | None) -> bool:
    if not senha:
        return False
    return verify_password(senha, gerente.senha_hash)


def cancelar_venda(db: Session, venda_id: int, payload: PdvCancelRequest) -> PdvVenda:
    venda_lock = _get_venda_or_404(db, venda_id, for_update=True)
    venda = _recarregar_venda(db, venda_lock.id)

    if venda.status == "CANCELADA":
        raise HTTPException(status_code=400, detail="Venda já está cancelada.")
    if venda.status == "FECHADA":
        raise HTTPException(status_code=400, detail="Venda fechada não pode ser cancelada nesta versão.")

    if payload.gerente_autorizador_id:
        gerente = _get_usuario_or_404(db, payload.gerente_autorizador_id)
        _validar_gerente(gerente)
        if not _senha_valida(gerente, payload.senha_gerente):
            raise HTTPException(status_code=403, detail="Senha do gerente inválida.")

    for item in venda.itens or []:
        if item.tipo_item == "SERVICE" and item.atendimento_clinico_id:
            atendimento = _get_atendimento_or_404(db, item.atendimento_clinico_id, for_update=True)
            atendimento.enviado_pdv = False
            atendimento.updated_at = _agora_utc()
            db.add(atendimento)

    if venda.pagamentos:
        for pag in venda.pagamentos:
            pag.status = "CANCELADO"
            pag.updated_at = _agora_utc()
            db.add(pag)

    if venda.pagamentos:
        forma_pagamento = venda.pagamentos[0].forma_pagamento
        valor = _decimal_2(venda.valor_total)
        _cancelar_financeiro_da_venda(db, venda)
        _registrar_movimento_estorno(db, venda, forma_pagamento=forma_pagamento, valor=valor)

    venda.cancelar(
        motivo_cancelamento=payload.motivo_cancelamento,
        usuario_cancelamento_id=payload.usuario_cancelamento_id,
    )
    db.add(venda)

    db.commit()
    return _recarregar_venda(db, venda.id)