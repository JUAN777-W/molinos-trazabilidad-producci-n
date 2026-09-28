from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import RegistroMerma, Usuario
from app.schemas.mermas_schemas import (
    RegistroMermaCreate, RegistroMermaOut,
    ResumenMermasOut, ResumenProveedorMermaItem, ResumenTipoMermaItem,
)
from app.auth import get_current_user, require_admin

router = APIRouter()

TIPOS_MERMA_VALIDOS = {"BOLSA_ROTA", "HARINA_BARRIDO", "DEFECTO_SELLADO", "SCRAP_BOBINA", "OTRO"}


@router.post("/", response_model=RegistroMermaOut, status_code=201)
def registrar_merma(
    payload: RegistroMermaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if payload.tipo_merma not in TIPOS_MERMA_VALIDOS:
        raise HTTPException(status_code=400, detail=f"tipo_merma inválido. Debe ser uno de: {', '.join(sorted(TIPOS_MERMA_VALIDOS))}")
    if payload.unidad_medida not in ("KG", "UND"):
        raise HTTPException(status_code=400, detail="unidad_medida debe ser KG o UND")
    if payload.cantidad <= 0:
        raise HTTPException(status_code=400, detail="La cantidad debe ser mayor a cero")

    merma = RegistroMerma(
        **payload.model_dump(),
        nombre_operario=current_user.nombre,
        operario_id=current_user.id,
    )
    db.add(merma)
    db.commit()
    db.refresh(merma)
    return merma


@router.get("/", response_model=List[RegistroMermaOut])
def listar_mermas(
    fecha: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    maquina: Optional[str] = Query(None),
    tipo_merma: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(RegistroMerma)
    if fecha:
        q = q.filter(RegistroMerma.fecha == fecha)
    if fecha_desde:
        q = q.filter(RegistroMerma.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroMerma.fecha <= fecha_hasta)
    if maquina:
        q = q.filter(RegistroMerma.maquina == maquina)
    if tipo_merma:
        q = q.filter(RegistroMerma.tipo_merma == tipo_merma)
    return q.order_by(RegistroMerma.id.desc()).limit(500).all()


@router.get("/resumen", response_model=ResumenMermasOut)
def resumen_mermas(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    q = db.query(RegistroMerma)
    if fecha_desde:
        q = q.filter(RegistroMerma.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroMerma.fecha <= fecha_hasta)
    registros = q.all()

    por_proveedor: dict = {}
    por_tipo: dict = {}
    for r in registros:
        prov = (r.proveedor_empaque or "Sin proveedor").strip().upper() or "Sin proveedor"
        if prov not in por_proveedor:
            por_proveedor[prov] = {"kg": 0.0, "und": 0, "registros": 0}
        if r.unidad_medida == "KG":
            por_proveedor[prov]["kg"] += r.cantidad
        else:
            por_proveedor[prov]["und"] += int(r.cantidad)
        por_proveedor[prov]["registros"] += 1

        if r.tipo_merma not in por_tipo:
            por_tipo[r.tipo_merma] = {"kg": 0.0, "und": 0, "registros": 0}
        if r.unidad_medida == "KG":
            por_tipo[r.tipo_merma]["kg"] += r.cantidad
        else:
            por_tipo[r.tipo_merma]["und"] += int(r.cantidad)
        por_tipo[r.tipo_merma]["registros"] += 1

    return ResumenMermasOut(
        por_proveedor=[
            ResumenProveedorMermaItem(proveedor=p, total_kg=round(d["kg"], 2), total_und=d["und"], registros=d["registros"])
            for p, d in sorted(por_proveedor.items(), key=lambda x: x[1]["kg"], reverse=True)
        ],
        por_tipo=[
            ResumenTipoMermaItem(tipo_merma=t, total_kg=round(d["kg"], 2), total_und=d["und"], registros=d["registros"])
            for t, d in sorted(por_tipo.items(), key=lambda x: x[1]["registros"], reverse=True)
        ],
        total_registros=len(registros),
    )


@router.delete("/{merma_id}", status_code=204)
def eliminar_merma(merma_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    merma = db.query(RegistroMerma).filter(RegistroMerma.id == merma_id).first()
    if not merma:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(merma)
    db.commit()
