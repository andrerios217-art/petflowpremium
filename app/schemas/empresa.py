from pydantic import BaseModel


class EmpresaCreate(BaseModel):
    nome: str
    cnpj: str | None = None


class EmpresaOut(BaseModel):
    id: int
    nome: str
    cnpj: str | None = None
    ativa: bool

    class Config:
        from_attributes = True