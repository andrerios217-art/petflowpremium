from sqlalchemy.orm import Session
from app.models.auditoria import Auditoria


def registrar(
    db: Session,
    empresa_id: int,
    usuario_id: int | None,
    acao: str,
    tabela: str,
    registro_id: int | None = None,
):
    log = Auditoria(
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        acao=acao,
        tabela=tabela,
        registro_id=registro_id,
    )
    db.add(log)
    db.commit()