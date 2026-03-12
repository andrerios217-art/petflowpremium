from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.models.pet import Pet
from app.schemas.pet import PetCreate


def create(db: Session, data: PetCreate) -> Pet:
    pet = Pet(
        empresa_id=data.empresa_id,
        cliente_id=data.cliente_id,
        nome=data.nome,
        nascimento=data.nascimento,
        raca=data.raca,
        sexo=data.sexo,
        temperamento=data.temperamento,
        peso=data.peso,
        porte=data.porte,
        observacoes=data.observacoes,
        pode_perfume=data.pode_perfume,
        pode_acessorio=data.pode_acessorio,
        castrado=data.castrado,
        foto=data.foto,
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def create_from_dict(db: Session, empresa_id: int, cliente_id: int, data: dict) -> Pet:
    nascimento = None
    if data.get("nascimento"):
        nascimento = datetime.strptime(data["nascimento"], "%Y-%m-%d").date()

    pet = Pet(
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        nome=data.get("nome"),
        nascimento=nascimento,
        raca=data.get("raca"),
        sexo=data.get("sexo"),
        temperamento=data.get("temperamento"),
        peso=data.get("peso"),
        porte=data.get("porte"),
        observacoes=data.get("observacoes"),
        pode_perfume=data.get("pode_perfume", True),
        pode_acessorio=data.get("pode_acessorio", True),
        castrado=data.get("castrado", False),
        foto=data.get("foto"),
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)
    return pet


def create_many_from_list(db: Session, empresa_id: int, cliente_id: int, pets_data: list[dict]) -> list[Pet]:
    pets = []
    for item in pets_data:
        pets.append(create_from_dict(db, empresa_id, cliente_id, item))
    return pets


def get_by_id(db: Session, pet_id: int):
    return db.query(Pet).filter(Pet.id == pet_id).first()


def get_by_cliente_id(db: Session, cliente_id: int):
    return db.query(Pet).filter(Pet.cliente_id == cliente_id).order_by(Pet.id.asc()).all()


def list_all(db: Session, q: str | None = None):
    query = db.query(Pet).order_by(Pet.id.desc())

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Pet.nome.ilike(like),
                Pet.raca.ilike(like),
                Pet.porte.ilike(like),
            )
        )

    return query.all()


def update(db: Session, pet: Pet, data: dict):
    if data.get("nascimento"):
        pet.nascimento = datetime.strptime(data["nascimento"], "%Y-%m-%d").date()
    pet.nome = data.get("nome")
    pet.raca = data.get("raca")
    pet.sexo = data.get("sexo")
    pet.temperamento = data.get("temperamento")
    pet.peso = data.get("peso")
    pet.porte = data.get("porte")
    pet.observacoes = data.get("observacoes")
    pet.pode_perfume = data.get("pode_perfume", True)
    pet.pode_acessorio = data.get("pode_acessorio", True)
    pet.castrado = data.get("castrado", False)
    db.commit()
    db.refresh(pet)
    return pet


def toggle_ativo(db: Session, pet: Pet):
    pet.ativo = not pet.ativo
    db.commit()
    db.refresh(pet)
    return pet