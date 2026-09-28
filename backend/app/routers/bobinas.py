from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.models import RegistroBobinas, FilaBobina, Usuario
from app.schemas.schemas import RegistroBobinasCreate, RegistroBobinasOut, EstimacionRestanteOut
from app.auth import get_current_user, require_admin

router = APIRouter()


@router.get("/", response_model=List[RegistroBobinasOut])
def listar(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    q = db.query(RegistroBobinas).order_by(RegistroBobinas.id.desc())
    if current_user.rol != "admin":
        q = q.filter(RegistroBobinas.operario_id == current_user.id)
    return q.all()


@router.get("/{registro_id}", response_model=RegistroBobinasOut)
def obtener(registro_id: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    reg = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if current_user.rol != "admin" and reg.operario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    return reg


@router.post("/", response_model=RegistroBobinasOut, status_code=201)
def crear(payload: RegistroBobinasCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    data = payload.model_dump(exclude={"filas"})
    data["operario_id"] = current_user.id
    data["nombre_operario"] = current_user.nombre
    reg = RegistroBobinas(**data)
    db.add(reg)
    db.flush()
    for fila in payload.filas:
        db.add(FilaBobina(registro_id=reg.id, **fila.model_dump()))
    db.commit()
    db.refresh(reg)
    return reg


@router.put("/{registro_id}", response_model=RegistroBobinasOut)
def actualizar(registro_id: int, payload: RegistroBobinasCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    reg = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if current_user.rol != "admin" and reg.operario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sin acceso")
    for k, v in payload.model_dump(exclude={"filas"}).items():
        setattr(reg, k, v)
    db.query(FilaBobina).filter(FilaBobina.registro_id == registro_id).delete()
    for fila in payload.filas:
        db.add(FilaBobina(registro_id=reg.id, **fila.model_dump()))
    db.commit()
    db.refresh(reg)
    return reg


@router.delete("/{registro_id}", status_code=204)
def eliminar(registro_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    reg = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not reg:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(reg)
    db.commit()


# Estima el peso restante del último rollo del turno usando el rendimiento
# real del rollo completo más reciente de la misma referencia.
@router.get("/estimar-restante", response_model=EstimacionRestanteOut)
def estimar_restante(
    referencia_producto: str = Query(...),
    unidades_rollo_actual: int = Query(..., gt=0, description="contador de esta fila - contador de la fila anterior"),
    peso_montar_actual: float = Query(..., gt=0),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    # Filas de la misma referencia con peso_desmontar medido (no estimado)
    candidatas = (
        db.query(FilaBobina)
        .join(RegistroBobinas, FilaBobina.registro_id == RegistroBobinas.id)
        .filter(
            RegistroBobinas.referencia_producto == referencia_producto,
            FilaBobina.peso_montar.isnot(None), FilaBobina.peso_montar > 0,
            FilaBobina.peso_desmontar.isnot(None), FilaBobina.peso_desmontar > 0,
            FilaBobina.peso_desmontar_estimado.isnot(True),
            FilaBobina.contador.isnot(None), FilaBobina.contador > 0,
        )
        .order_by(RegistroBobinas.id.desc(), FilaBobina.numero_fila.desc())
        .limit(40)
        .all()
    )

    for fila in candidatas:
        anterior = (
            db.query(FilaBobina)
            .filter(
                FilaBobina.registro_id == fila.registro_id,
                FilaBobina.maquina_grupo == fila.maquina_grupo,
                FilaBobina.numero_fila < fila.numero_fila,
            )
            .order_by(FilaBobina.numero_fila.desc())
            .first()
        )
        contador_anterior = anterior.contador if (anterior and anterior.contador) else 0
        unidades = (fila.contador or 0) - contador_anterior
        if unidades <= 0:
            continue

        peso_consumido_real = (fila.peso_montar or 0) - (fila.peso_desmontar or 0)
        if peso_consumido_real <= 0:
            continue

        peso_por_unidad = peso_consumido_real / unidades
        consumido_estimado = round(unidades_rollo_actual * peso_por_unidad, 2)
        peso_restante_estimado = round(peso_montar_actual - consumido_estimado, 2)

        return EstimacionRestanteOut(
            disponible=True,
            peso_por_unidad=round(peso_por_unidad, 6),
            consumido_estimado=consumido_estimado,
            peso_restante_estimado=max(0.0, peso_restante_estimado),
            fuente_fila_id=fila.id,
            fuente_registro_id=fila.registro_id,
        )

    return EstimacionRestanteOut(disponible=False)