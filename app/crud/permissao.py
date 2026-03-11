from sqlalchemy.orm import Session
from app.models.permissao import Permissao


def create_default_permissions(db: Session, usuario_id: int):
    defaults = [
        ("dashboard", True, True, False),
        ("clientes", True, True, False),
        ("pets", True, True, False),
        ("agenda", True, True, False),
    ]
    for modulo, ver, editar, excluir in defaults:
        db.add(
            Permissao(
                usuario_id=usuario_id,
                modulo=modulo,
                pode_visualizar=ver,
                pode_editar=editar,
                pode_excluir=excluir,
            )
        )
    db.commit()