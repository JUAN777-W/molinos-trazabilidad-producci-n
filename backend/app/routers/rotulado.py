from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import RegistroRotulado, FilaRotulado, Usuario
from app.schemas.schemas import RegistroRotuladoCreate, RegistroRotuladoOut
from app.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/", response_model=List[RegistroRotuladoOut])
def listar(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    q = db.query(RegistroRotulado).order_by(RegistroRotulado.id.desc())
    if current_user.rol != "admin":
        q = q.filter(RegistroRotulado.operario_id == current_user.id)
    return q.all()


@router.get("/{registro_id}", response_model=RegistroRotuladoOut)
def obtener(registro_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    reg = db.query(RegistroRotulado).filter(RegistroRotulado.id == registro_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if current_user.rol != "admin" and reg.operario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    return reg


@router.post("/", response_model=RegistroRotuladoOut, status_code=201)
def crear(payload: RegistroRotuladoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    data = payload.model_dump(exclude={"filas"})
    data["operario_id"] = current_user.id
    data["nombre_operario"] = current_user.nombre
    reg = RegistroRotulado(**data)
    db.add(reg)
    db.flush()
    for fila in payload.filas:
        db.add(FilaRotulado(registro_id=reg.id, **fila.model_dump()))
    db.commit()
    db.refresh(reg)
    return reg


@router.put("/{registro_id}", response_model=RegistroRotuladoOut)
def actualizar(registro_id: int, payload: RegistroRotuladoCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    reg = db.query(RegistroRotulado).filter(RegistroRotulado.id == registro_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if current_user.rol != "admin" and reg.operario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    for k, v in payload.model_dump(exclude={"filas"}).items():
        setattr(reg, k, v)
    db.query(FilaRotulado).filter(FilaRotulado.registro_id == registro_id).delete()
    for fila in payload.filas:
        db.add(FilaRotulado(registro_id=reg.id, **fila.model_dump()))
    db.commit()
    db.refresh(reg)
    return reg


@router.delete("/{registro_id}", status_code=204)
def eliminar(registro_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    reg = db.query(RegistroRotulado).filter(RegistroRotulado.id == registro_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(reg)
    db.commit()
