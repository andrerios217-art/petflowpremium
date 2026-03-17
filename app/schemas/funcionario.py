from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


FUNCOES_VALIDAS = {
    "Banhista",
    "Tosador",
    "Recepção",
    "Gerente",
    "Veterinário",
}


class FuncionarioCreate(BaseModel):
    empresa_id: int
    nome: str = Field(..., min_length=2)
    cpf: str
    email: EmailStr
    telefone: str
    funcao: str
    crmv: Optional[str] = None
    senha: str = Field(..., min_length=4)

    acesso_dashboard: bool = False
    acesso_clientes: bool = False
    acesso_pets: bool = False
    acesso_servicos: bool = False
    acesso_funcionarios: bool = False
    acesso_agenda: bool = False
    acesso_producao: bool = False
    acesso_estoque: bool = False
    acesso_financeiro: bool = False
    acesso_crm: bool = False
    acesso_relatorios: bool = False
    acesso_configuracoes: bool = False

    @field_validator("funcao")
    @classmethod
    def validar_funcao(cls, value: str) -> str:
        value = value.strip()

        if value not in FUNCOES_VALIDAS:
            raise ValueError("Função inválida.")

        return value

    @field_validator("crmv")
    @classmethod
    def normalizar_crmv(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()
        return value or None

    @model_validator(mode="after")
    def validar_crmv_para_veterinario(self):
        if self.funcao == "Veterinário" and not self.crmv:
            raise ValueError("CRMV é obrigatório para funcionário com função Veterinário.")

        if self.funcao != "Veterinário":
            self.crmv = None

        return self


class FuncionarioOut(BaseModel):
    id: int
    empresa_id: int
    nome: str
    cpf: str
    email: EmailStr
    telefone: str
    funcao: str
    crmv: Optional[str] = None

    acesso_dashboard: bool
    acesso_clientes: bool
    acesso_pets: bool
    acesso_servicos: bool
    acesso_funcionarios: bool
    acesso_agenda: bool
    acesso_producao: bool
    acesso_estoque: bool
    acesso_financeiro: bool
    acesso_crm: bool
    acesso_relatorios: bool
    acesso_configuracoes: bool

    ativo: bool

    class Config:
        from_attributes = True