from pydantic import BaseModel


class EnderecoCreate(BaseModel):
    empresa_id: int
    cliente_id: int | None = None
    cep: str | None = None
    rua: str | None = None
    numero: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    complemento: str | None = None


class EnderecoOut(BaseModel):
    id: int
    empresa_id: int
    cliente_id: int
    cep: str | None = None
    rua: str | None = None
    numero: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    complemento: str | None = None

    class Config:
        from_attributes = True