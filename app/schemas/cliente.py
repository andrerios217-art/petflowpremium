from pydantic import BaseModel, EmailStr


class ClienteCreate(BaseModel):
    empresa_id: int
    nome: str
    cpf: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None
    telefone_fixo: str | None = None


class ClienteOut(BaseModel):
    id: int
    empresa_id: int
    nome: str
    cpf: str | None = None
    email: EmailStr | None = None
    telefone: str | None = None
    telefone_fixo: str | None = None
    ativo: bool

    class Config:
        from_attributes = True