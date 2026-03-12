from sqlalchemy.orm import Session
from app.models.endereco import Endereco


def create(db: Session, empresa_id: int, cliente_id: int, data: dict) -> Endereco:
    endereco = Endereco(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        cep=data.get("cep"),
        rua=data.get("rua"),
        numero=data.get("numero"),
        bairro=data.get("bairro"),
        cidade=data.get("cidade"),
        uf=data.get("uf"),
        complemento=data.get("complemento"),
    )
    db.add(endereco)
    db.commit()
    db.refresh(endereco)
    return endereco


def get_by_cliente_id(db: Session, cliente_id: int):
    return db.query(Endereco).filter(Endereco.cliente_id == cliente_id).first()


def update(db: Session, endereco: Endereco, data: dict):
    endereco.cep = data.get("cep")
    endereco.rua = data.get("rua")
    endereco.numero = data.get("numero")
    endereco.bairro = data.get("bairro")
    endereco.cidade = data.get("cidade")
    endereco.uf = data.get("uf")
    endereco.complemento = data.get("complemento")
    db.commit()
    db.refresh(endereco)
    return endereco