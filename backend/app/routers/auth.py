from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import Usuario
from app.schemas.auth_schemas import (
    LoginRequest, TokenResponse, UsuarioCreate, UsuarioOut, UsuarioUpdate
)
from app.auth import hash_password, verify_password, create_token, get_current_user, require_admin

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    if user.activo != "SI":
        raise HTTPException(status_code=403, detail="Usuario inactivo")
    token = create_token({"sub": user.username, "rol": user.rol})
    return TokenResponse(
        access_token=token,
        rol=user.rol,
        nombre=user.nombre,
        username=user.username,
        maquinas_asignadas=user.maquinas_asignadas
    )


@router.get("/me", response_model=UsuarioOut)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user


# ── CRUD de usuarios (solo admin) ─────────────────────────────────────────────
@router.get("/usuarios", response_model=List[UsuarioOut])
def listar_usuarios(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(Usuario).order_by(Usuario.nombre).all()


@router.post("/usuarios", response_model=UsuarioOut, status_code=201)
def crear_usuario(payload: UsuarioCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    if db.query(Usuario).filter(Usuario.username == payload.username).first():
        raise HTTPException(status_code=400, detail="El username ya existe")
    if db.query(Usuario).filter(Usuario.cedula == payload.cedula).first():
        raise HTTPException(status_code=400, detail="La cédula ya está registrada")
    user = Usuario(
        nombre=payload.nombre,
        cedula=payload.cedula,
        username=payload.username,
        hashed_password=hash_password(payload.password),
        rol=payload.rol,
        maquinas_asignadas=payload.maquinas_asignadas,
        activo="SI"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/usuarios/{user_id}", response_model=UsuarioOut)
def actualizar_usuario(user_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if payload.nombre: user.nombre = payload.nombre
    if payload.cedula: user.cedula = payload.cedula
    if payload.maquinas_asignadas is not None: user.maquinas_asignadas = payload.maquinas_asignadas
    if payload.activo: user.activo = payload.activo
    if payload.password: user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/usuarios/{user_id}", status_code=204)
def eliminar_usuario(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.delete(user)
    db.commit()


# ── Firma escaneada (se pega sola en las planillas al guardar) ────────────────
class FirmaUpload(BaseModel):
    firma_imagen: str  # imagen en base64 (data URL), ej. "data:image/png;base64,...."


class FirmaOut(BaseModel):
    firma_imagen: Optional[str] = None


@router.put("/usuarios/{user_id}/firma", response_model=FirmaOut)
def actualizar_firma(user_id: int, payload: FirmaUpload, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Sube o reemplaza la firma escaneada de un usuario (solo admin)."""
    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    user.firma_imagen = payload.firma_imagen
    db.commit()
    return FirmaOut(firma_imagen=user.firma_imagen)


@router.get("/mi-firma", response_model=FirmaOut)
def mi_firma(current_user: Usuario = Depends(get_current_user)):
    """El usuario autenticado consulta su propia firma, para pegarla automáticamente al guardar una planilla."""
    return FirmaOut(firma_imagen=current_user.firma_imagen)