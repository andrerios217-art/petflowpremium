from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.crud import cliente as cliente_crud
from app.crud import endereco as endereco_crud
from app.crud import pet as pet_crud
from app.models.pet import Pet
from app.schemas.cliente import ClienteCreate, ClienteOut
from app.schemas.cliente_completo import ClienteCompletoCreate

router = APIRouter(prefix="/api/clientes", tags=["clientes"])


@router.get("/", response_model=list[ClienteOut])
def listar(
    q: str | None = Query(default=None),
    filtro_assinatura: str = Query(default="todos"),
    db: Session = Depends(get_db),
):
    return cliente_crud.list_all(db, q=q, filtro_assinatura=filtro_assinatura)


@router.get("/validar-duplicidade")
def validar_duplicidade(
    cpf: str | None = Query(default=None),
    email: str | None = Query(default=None),
    telefone: str | None = Query(default=None),
    cliente_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return cliente_crud.validar_duplicidade(
        db=db,
        cpf=cpf,
        email=email,
        telefone=telefone,
        cliente_id=cliente_id,
    )


@router.get("/{cliente_id}")
def obter_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = cliente_crud.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    endereco = endereco_crud.get_by_cliente_id(db, cliente_id)
    pets = db.query(Pet).filter(Pet.cliente_id == cliente_id).order_by(Pet.id.asc()).all()

    return {
        "cliente": {
            "id": cliente.id,
            "empresa_id": cliente.empresa_id,
            "nome": cliente.nome,
            "cpf": cliente.cpf,
            "email": cliente.email,
            "telefone": cliente.telefone,
            "telefone_fixo": cliente.telefone_fixo,
            "ativo": cliente.ativo,
        },
        "endereco": {
            "cep": endereco.cep if endereco else None,
            "rua": endereco.rua if endereco else None,
            "numero": endereco.numero if endereco else None,
            "bairro": endereco.bairro if endereco else None,
            "cidade": endereco.cidade if endereco else None,
            "uf": endereco.uf if endereco else None,
            "complemento": endereco.complemento if endereco else None,
        },
        "pets": [
            {
                "id": pet.id,
                "nome": pet.nome,
                "nascimento": str(pet.nascimento) if pet.nascimento else None,
                "raca": pet.raca,
                "sexo": pet.sexo,
                "temperamento": pet.temperamento,
                "peso": float(pet.peso) if pet.peso is not None else None,
                "porte": pet.porte,
                "observacoes": pet.observacoes,
                "pode_perfume": pet.pode_perfume,
                "pode_acessorio": pet.pode_acessorio,
                "castrado": pet.castrado,
                "ativo": pet.ativo,
            }
            for pet in pets
        ],
    }


@router.post("/", response_model=ClienteOut)
def criar(payload: ClienteCreate, db: Session = Depends(get_db)):
    return cliente_crud.create(db, payload)


@router.post("/completo")
def criar_completo(payload: ClienteCompletoCreate, db: Session = Depends(get_db)):
    if payload.cliente.cpf:
        existente = cliente_crud.get_by_cpf(db, payload.cliente.cpf)
        if existente:
            raise HTTPException(status_code=400, detail="CPF já cadastrado.")

    if not payload.pets:
        raise HTTPException(status_code=400, detail="É necessário cadastrar ao menos um pet.")

    cliente = cliente_crud.create(db, ClienteCreate(**payload.cliente.model_dump()))

    endereco = endereco_crud.create(
        db=db,
        empresa_id=payload.cliente.empresa_id,
        cliente_id=cliente.id,
        data=payload.endereco.model_dump(),
    )

    pets = []
    for pet_data in payload.pets:
        dados_pet = pet_data.model_dump()
        dados_pet["empresa_id"] = payload.cliente.empresa_id
        dados_pet["cliente_id"] = cliente.id
        pet = pet_crud.create(db, dados_pet)
        pets.append(pet)

    return {
        "cliente_id": cliente.id,
        "endereco_id": endereco.id,
        "pets_ids": [pet.id for pet in pets],
        "message": "Cadastro completo realizado com sucesso.",
    }


@router.put("/{cliente_id}")
def editar_cliente(cliente_id: int, payload: dict, db: Session = Depends(get_db)):
    cliente = cliente_crud.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    cliente_atualizado = cliente_crud.update(db, cliente, payload.get("cliente", {}))

    endereco = endereco_crud.get_by_cliente_id(db, cliente_id)
    if endereco:
        endereco_crud.update(db, endereco, payload.get("endereco", {}))

    return {
        "message": "Cliente atualizado com sucesso.",
        "cliente_id": cliente_atualizado.id,
    }


@router.patch("/{cliente_id}/toggle")
def toggle_cliente(cliente_id: int, db: Session = Depends(get_db)):
    cliente = cliente_crud.get_by_id(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    cliente = cliente_crud.toggle_ativo(db, cliente)
    return {"id": cliente.id, "ativo": cliente.ativo}