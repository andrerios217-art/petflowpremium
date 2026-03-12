from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate


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


def list_all(db: Session, q: str | None = None):
    query = db.query(Cliente).order_by(Cliente.id.desc())

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

    return query.all()


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
    cliente_id: int | None = None
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
        "telefone_duplicado": telefone_duplicado
    }