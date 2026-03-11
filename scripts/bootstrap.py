from app.core.database import Base, engine, SessionLocal
from app.models import *  # noqa
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

empresa = db.query(Empresa).filter(Empresa.nome == "Empresa Demo").first()
if not empresa:
    empresa = Empresa(nome="Empresa Demo", cnpj="00.000.000/0001-00")
    db.add(empresa)
    db.commit()
    db.refresh(empresa)

admin = db.query(Usuario).filter(Usuario.email == "admin@petflow.com").first()
if not admin:
    admin = Usuario(
        empresa_id=empresa.id,
        nome="Administrador",
        email="admin@petflow.com",
        senha_hash=hash_password("admin123"),
        tipo="admin",
        ativo=True,
    )
    db.add(admin)
    db.commit()

db.close()
print("Bootstrap concluído.")