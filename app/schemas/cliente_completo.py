from pydantic import BaseModel, EmailStr


class ClienteDados(BaseModel):
    empresa_id: int
    nome: str
    cpf: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None
    telefone_fixo: str | None = None


class EnderecoDados(BaseModel):
    cep: str | None = None
    rua: str | None = None
    numero: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    complemento: str | None = None


class PetDados(BaseModel):
    nome: str
    nascimento: str | None = None
    raca: str | None = None
    sexo: str | None = None
    temperamento: str | None = None
    peso: float | None = None
    porte: str | None = None
    observacoes: str | None = None
    pode_perfume: bool = True
    pode_acessorio: bool = True
    castrado: bool = False
    foto: str | None = None


class ClienteCompletoCreate(BaseModel):
    cliente: ClienteDados
    endereco: EnderecoDados
    pets: list[PetDados]