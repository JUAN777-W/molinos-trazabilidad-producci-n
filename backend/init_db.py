"""
Ejecutar una sola vez para crear las tablas y el usuario admin inicial.
  python init_db.py
"""
from app.database import engine, Base, SessionLocal
import app.models.models  # noqa
from app.auth import hash_password
from app.models.models import Usuario

Base.metadata.create_all(bind=engine)
print("✅ Tablas creadas correctamente.")

db = SessionLocal()
try:
    existing = db.query(Usuario).filter(Usuario.username == "admin").first()
    if not existing:
        admin = Usuario(
            nombre="Administrador",
            cedula="000000000",
            username="admin",
            hashed_password=hash_password("admin123"),
            rol="admin",
            maquinas_asignadas="",
            activo="SI"
        )
        db.add(admin)
        db.commit()
        print("✅ Usuario admin creado — usuario: admin / contraseña: admin123")
        print("⚠️  Cambia la contraseña del admin después del primer login.")
    else:
        print("ℹ️  Usuario admin ya existe.")
finally:
    db.close()
