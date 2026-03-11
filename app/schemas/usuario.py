from pydantic import BaseModel, EmailStr


class UsuarioCreate(BaseModel):
    empresa_id: int
    nome: str
    email: EmailStr
    senha: str
    tipo: str = "funcionario"


class UsuarioOut(BaseModel):
    id: int
    empresa_id: int
    nome: str
    email: EmailStr
    tipo: str
    ativo: bool

    class Config:
        from_attributes = True