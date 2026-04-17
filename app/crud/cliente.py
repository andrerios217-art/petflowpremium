from sqlalchemy import distinct, func, or_
from sqlalchemy.orm import Session

from app.models.assinatura_pet import AssinaturaPet
from app.models.assinatura_pet_item import AssinaturaPetItem
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate


FILTROS_ASSINATURA_VALIDOS = {"todos", "assinantes", "nao_assinantes"}


def create(db: Session, data: ClienteCreate) -> Cliente:
    cliente = Cliente(
        empresa_id=data.empresa_id,
        nome=data.nome,
        cpf=data.cpf,
        email=data.email,
        telefone=data.telefone,
        telefone_fixo=data.telefone_fixo,
    )
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def get_by_id(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def get_by_cpf(db: Session, cpf: str):
    return db.query(Cliente).filter(Cliente.cpf == cpf).first()


def get_by_email(db: Session, email: str):
    return db.query(Cliente).filter(Cliente.email == email).first()


def get_by_telefone(db: Session, telefone: str):
    return db.query(Cliente).filter(Cliente.telefone == telefone).first()


def _montar_subquery_assinaturas_ativas():
    return (
        AssinaturaPet.__table__.select()
        .with_only_columns(
            AssinaturaPet.empresa_id.label("empresa_id"),
            AssinaturaPet.cliente_id.label("cliente_id"),
            func.count(distinct(AssinaturaPet.id)).label("total_assinaturas_ativas"),
            func.count(distinct(AssinaturaPet.pet_id)).label("total_pets_com_assinatura"),
        )
        .where(AssinaturaPet.status == "ATIVA")
        .group_by(AssinaturaPet.empresa_id, AssinaturaPet.cliente_id)
        .subquery()
    )


def _montar_subquery_consumo_resumo():
    return (
        AssinaturaPetItem.__table__.join(
            AssinaturaPet,
            AssinaturaPet.id == AssinaturaPetItem.assinatura_id,
        )
        .select()
        .with_only_columns(
            AssinaturaPet.empresa_id.label("empresa_id"),
            AssinaturaPet.cliente_id.label("cliente_id"),
            func.sum(AssinaturaPetItem.quantidade_contratada).label("quantidade_contratada"),
            func.sum(AssinaturaPetItem.quantidade_consumida).label("quantidade_consumida"),
        )
        .where(
            AssinaturaPet.status == "ATIVA",
            AssinaturaPetItem.ativo.is_(True),
        )
        .group_by(AssinaturaPet.empresa_id, AssinaturaPet.cliente_id)
        .subquery()
    )


def _normalizar_filtro_assinatura(filtro_assinatura: str | None) -> str:
    filtro = (filtro_assinatura or "todos").strip().lower()
    if filtro not in FILTROS_ASSINATURA_VALIDOS:
        return "todos"
    return filtro


def list_all(
    db: Session,
    q: str | None = None,
    filtro_assinatura: str | None = None,
):
    filtro_assinatura = _normalizar_filtro_assinatura(filtro_assinatura)

    cliente_assinaturas = _montar_subquery_assinaturas_ativas()
    cliente_consumo = _montar_subquery_consumo_resumo()

    query = (
        db.query(
            Cliente,
            func.coalesce(cliente_assinaturas.c.total_assinaturas_ativas, 0).label("total_assinaturas_ativas"),
            func.coalesce(cliente_assinaturas.c.total_pets_com_assinatura, 0).label("total_pets_com_assinatura"),
            func.coalesce(cliente_consumo.c.quantidade_contratada, 0).label("quantidade_contratada"),
            func.coalesce(cliente_consumo.c.quantidade_consumida, 0).label("quantidade_consumida"),
        )
        .outerjoin(
            cliente_assinaturas,
            (cliente_assinaturas.c.cliente_id == Cliente.id)
            & (cliente_assinaturas.c.empresa_id == Cliente.empresa_id),
        )
        .outerjoin(
            cliente_consumo,
            (cliente_consumo.c.cliente_id == Cliente.id)
            & (cliente_consumo.c.empresa_id == Cliente.empresa_id),
        )
        .order_by(Cliente.id.desc())
    )

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Cliente.nome.ilike(like),
                Cliente.cpf.ilike(like),
                Cliente.email.ilike(like),
                Cliente.telefone.ilike(like),
            )
        )

    if filtro_assinatura == "assinantes":
        query = query.filter(cliente_assinaturas.c.total_assinaturas_ativas.isnot(None))
    elif filtro_assinatura == "nao_assinantes":
        query = query.filter(cliente_assinaturas.c.total_assinaturas_ativas.is_(None))

    resultados = []
    for (
        cliente,
        total_assinaturas_ativas,
        total_pets_com_assinatura,
        quantidade_contratada,
        quantidade_consumida,
    ) in query.all():
        cliente.is_assinante = int(total_assinaturas_ativas or 0) > 0
        cliente.total_assinaturas_ativas = int(total_assinaturas_ativas or 0)
        cliente.total_pets_com_assinatura = int(total_pets_com_assinatura or 0)

        contratada = int(quantidade_contratada or 0)
        consumida = int(quantidade_consumida or 0)

        if cliente.is_assinante and contratada > 0:
            cliente.consumo_assinatura_resumo = f"{consumida}/{contratada} consumidos"
        elif cliente.is_assinante:
            cliente.consumo_assinatura_resumo = "Sem consumo lançado"
        else:
            cliente.consumo_assinatura_resumo = None

        resultados.append(cliente)

    return resultados


def update(db: Session, cliente: Cliente, data: dict):
    cliente.email = data.get("email")
    cliente.telefone = data.get("telefone")
    cliente.telefone_fixo = data.get("telefone_fixo")
    db.commit()
    db.refresh(cliente)
    return cliente


def toggle_ativo(db: Session, cliente: Cliente):
    cliente.ativo = not cliente.ativo
    db.commit()
    db.refresh(cliente)
    return cliente


def validar_duplicidade(
    db: Session,
    cpf: str | None = None,
    email: str | None = None,
    telefone: str | None = None,
    cliente_id: int | None = None,
):
    query = db.query(Cliente)

    cpf_duplicado = False
    email_duplicado = False
    telefone_duplicado = False

    if cpf:
        q = query.filter(Cliente.cpf == cpf)
        if cliente_id:
            q = q.filter(Cliente.id != cliente_id)
        cpf_duplicado = q.first() is not None

    if email:
        q = query.filter(Cliente.email == email)
        if cliente_id:
            q = q.filter(Cliente.id != cliente_id)
        email_duplicado = q.first() is not None

    if telefone:
        q = query.filter(Cliente.telefone == telefone)
        if cliente_id:
            q = q.filter(Cliente.id != cliente_id)
        telefone_duplicado = q.first() is not None

    return {
        "cpf_duplicado": cpf_duplicado,
        "email_duplicado": email_duplicado,
        "telefone_duplicado": telefone_duplicado,
    }