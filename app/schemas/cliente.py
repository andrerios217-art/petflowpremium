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
    is_assinante: bool = False
    total_assinaturas_ativas: int = 0
    total_pets_com_assinatura: int = 0
    consumo_assinatura_resumo: str | None = None

    class Config:
        from_attributes = True