from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.models.assinatura_pet import AssinaturaPet
from app.models.assinatura_pet_consumo import AssinaturaPetConsumo
from app.models.assinatura_pet_item import AssinaturaPetItem
from app.models.pet import Pet
from app.models.servico import Servico
from app.schemas.assinatura import (
    AssinaturaPetConsumoCreate,
    AssinaturaPetCreate,
    AssinaturaPetUpdate,
)


def buscar_assinatura_por_id(
    db: Session,
    assinatura_id: int,
    empresa_id: int,
) -> AssinaturaPet | None:
    return (
        db.query(AssinaturaPet)
        .options(
            joinedload(AssinaturaPet.itens),
            joinedload(AssinaturaPet.consumos),
        )
        .filter(
            AssinaturaPet.id == assinatura_id,
            AssinaturaPet.empresa_id == empresa_id,
        )
        .first()
    )


def listar_assinaturas(
    db: Session,
    empresa_id: int,
    status: str | None = None,
    cliente_id: int | None = None,
    pet_id: int | None = None,
) -> list[AssinaturaPet]:
    query = (
        db.query(AssinaturaPet)
        .options(joinedload(AssinaturaPet.itens))
        .filter(AssinaturaPet.empresa_id == empresa_id)
        .order_by(AssinaturaPet.id.desc())
    )

    if status:
        query = query.filter(AssinaturaPet.status == status)

    if cliente_id:
        query = query.filter(AssinaturaPet.cliente_id == cliente_id)

    if pet_id:
        query = query.filter(AssinaturaPet.pet_id == pet_id)

    return query.all()


def existe_assinatura_ativa_para_pet(
    db: Session,
    empresa_id: int,
    pet_id: int,
    ignorar_assinatura_id: int | None = None,
) -> bool:
    query = db.query(AssinaturaPet).filter(
        AssinaturaPet.empresa_id == empresa_id,
        AssinaturaPet.pet_id == pet_id,
        AssinaturaPet.status == "ATIVA",
    )

    if ignorar_assinatura_id:
        query = query.filter(AssinaturaPet.id != ignorar_assinatura_id)

    return db.query(query.exists()).scalar()


def _validar_pet_do_cliente(
    db: Session,
    empresa_id: int,
    cliente_id: int,
    pet_id: int,
) -> Pet:
    pet = (
        db.query(Pet)
        .filter(
            Pet.id == pet_id,
            Pet.cliente_id == cliente_id,
            Pet.empresa_id == empresa_id,
        )
        .first()
    )
    if not pet:
        raise ValueError("Pet não encontrado para este cliente.")
    return pet


def _buscar_servico_empresa(
    db: Session,
    empresa_id: int,
    servico_id: int,
) -> Servico:
    servico = (
        db.query(Servico)
        .filter(
            Servico.id == servico_id,
            Servico.empresa_id == empresa_id,
        )
        .first()
    )
    if not servico:
        raise ValueError(f"Serviço {servico_id} não encontrado para a empresa.")
    return servico


def _criar_item_assinatura(
    db: Session,
    assinatura: AssinaturaPet,
    empresa_id: int,
    item_data,
) -> AssinaturaPetItem:
    servico = _buscar_servico_empresa(db, empresa_id, item_data.servico_id)

    nome_servico = item_data.nome_servico.strip() if item_data.nome_servico else servico.nome
    preco_base = Decimal(str(item_data.preco_unitario_base))
    percentual = Decimal(str(item_data.percentual_desconto))

    item = AssinaturaPetItem(
        assinatura=assinatura,
        empresa_id=empresa_id,
        servico_id=servico.id,
        nome_servico=nome_servico,
        quantidade_contratada=item_data.quantidade_contratada,
        quantidade_consumida=0,
        preco_unitario_base=preco_base,
        percentual_desconto=percentual,
        ativo=True,
    )
    item.recalcular_precos()
    db.add(item)
    return item


def criar_assinatura(
    db: Session,
    data: AssinaturaPetCreate,
) -> AssinaturaPet:
    _validar_pet_do_cliente(
        db=db,
        empresa_id=data.empresa_id,
        cliente_id=data.cliente_id,
        pet_id=data.pet_id,
    )

    if existe_assinatura_ativa_para_pet(
        db=db,
        empresa_id=data.empresa_id,
        pet_id=data.pet_id,
    ):
        raise ValueError("Já existe uma assinatura ativa para este pet.")

    assinatura = AssinaturaPet(
        empresa_id=data.empresa_id,
        cliente_id=data.cliente_id,
        pet_id=data.pet_id,
        status="ATIVA",
        origem=data.origem,
        data_inicio=data.data_inicio,
        data_fim=data.data_fim,
        dia_fechamento_ciclo=data.dia_fechamento_ciclo,
        usar_limite_ate_dia_28=data.usar_limite_ate_dia_28,
        nao_cumulativa=data.nao_cumulativa,
        ativa_renovacao=data.ativa_renovacao,
        observacoes=data.observacoes,
        contrato_externo_id=data.contrato_externo_id,
    )

    db.add(assinatura)
    db.flush()

    for item_data in data.itens:
        _criar_item_assinatura(
            db=db,
            assinatura=assinatura,
            empresa_id=data.empresa_id,
            item_data=item_data,
        )

    db.flush()
    assinatura.recalcular_totais()
    db.commit()
    db.refresh(assinatura)

    return buscar_assinatura_por_id(
        db=db,
        assinatura_id=assinatura.id,
        empresa_id=data.empresa_id,
    )


def atualizar_assinatura(
    db: Session,
    assinatura_id: int,
    empresa_id: int,
    data: AssinaturaPetUpdate,
) -> AssinaturaPet:
    assinatura = buscar_assinatura_por_id(db, assinatura_id, empresa_id)
    if not assinatura:
        raise ValueError("Assinatura não encontrada.")

    payload = data.model_dump(exclude_unset=True)

    if "pet_id" in payload or "cliente_id" in payload:
        cliente_id = payload.get("cliente_id", assinatura.cliente_id)
        pet_id = payload.get("pet_id", assinatura.pet_id)

        _validar_pet_do_cliente(
            db=db,
            empresa_id=empresa_id,
            cliente_id=cliente_id,
            pet_id=pet_id,
        )

        if pet_id != assinatura.pet_id and existe_assinatura_ativa_para_pet(
            db=db,
            empresa_id=empresa_id,
            pet_id=pet_id,
            ignorar_assinatura_id=assinatura.id,
        ):
            raise ValueError("O pet informado já possui assinatura ativa.")

    for campo, valor in payload.items():
        setattr(assinatura, campo, valor)

    assinatura.recalcular_totais()
    db.commit()
    db.refresh(assinatura)

    return buscar_assinatura_por_id(db, assinatura.id, empresa_id)


def cancelar_assinatura(
    db: Session,
    assinatura_id: int,
    empresa_id: int,
) -> AssinaturaPet:
    assinatura = buscar_assinatura_por_id(db, assinatura_id, empresa_id)
    if not assinatura:
        raise ValueError("Assinatura não encontrada.")

    assinatura.cancelar()
    db.commit()
    db.refresh(assinatura)

    return buscar_assinatura_por_id(db, assinatura.id, empresa_id)


def registrar_consumo_assinatura(
    db: Session,
    data: AssinaturaPetConsumoCreate,
) -> AssinaturaPetConsumo:
    assinatura = buscar_assinatura_por_id(db, data.assinatura_id, data.empresa_id)
    if not assinatura:
        raise ValueError("Assinatura não encontrada.")

    if assinatura.status != "ATIVA":
        raise ValueError("Só é possível consumir assinatura ativa.")

    item = (
        db.query(AssinaturaPetItem)
        .filter(
            AssinaturaPetItem.id == data.assinatura_item_id,
            AssinaturaPetItem.assinatura_id == data.assinatura_id,
            AssinaturaPetItem.empresa_id == data.empresa_id,
        )
        .first()
    )
    if not item:
        raise ValueError("Item da assinatura não encontrado.")

    if item.servico_id != data.servico_id:
        raise ValueError("O serviço informado não corresponde ao item da assinatura.")

    item.consumir(data.quantidade)

    competencia_ano, competencia_mes = AssinaturaPetConsumo.criar_competencia(data.data_consumo)

    consumo = AssinaturaPetConsumo(
        assinatura_id=data.assinatura_id,
        assinatura_item_id=data.assinatura_item_id,
        empresa_id=data.empresa_id,
        cliente_id=data.cliente_id,
        pet_id=data.pet_id,
        servico_id=data.servico_id,
        data_consumo=data.data_consumo,
        competencia_ano=competencia_ano,
        competencia_mes=competencia_mes,
        quantidade=data.quantidade,
        origem=data.origem,
        status=data.status,
        agendamento_id=data.agendamento_id,
        pdv_venda_id=data.pdv_venda_id,
        pdv_venda_item_id=data.pdv_venda_item_id,
        observacoes=data.observacoes,
    )

    db.add(consumo)
    db.commit()
    db.refresh(consumo)

    return consumo


def listar_consumos_assinatura(
    db: Session,
    assinatura_id: int,
    empresa_id: int,
) -> list[AssinaturaPetConsumo]:
    return (
        db.query(AssinaturaPetConsumo)
        .filter(
            AssinaturaPetConsumo.assinatura_id == assinatura_id,
            AssinaturaPetConsumo.empresa_id == empresa_id,
        )
        .order_by(
            AssinaturaPetConsumo.data_consumo.desc(),
            AssinaturaPetConsumo.id.desc(),
        )
        .all()
    )