from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    senha: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tipo_usuario: str | None = None
    nome: str | None = None
    permissoes: dict | None = None
