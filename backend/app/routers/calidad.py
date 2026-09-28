import random
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import RegistroPesos, FilaPeso, MuestreoCalidad, MuestraCalidadItem, Usuario, ReferenciaEmpaque
from app.schemas.calidad_schemas import (
    MuestreoCalidadCreate, MuestreoCalidadOut, MuestreoCalidadResumen,
    MuestraCalidadItemUpdate, MuestraCalidadItemOut,
)
from app.auth import get_current_user

router = APIRouter()


class ReferenciaDisponibleOut(BaseModel):
    codigo: str
    descripcion: str



def require_admin_o_calidad(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol not in ("admin", "calidad"):
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin o calidad.")
    return current_user


RANGOS_PESO = {
    'kilo': (1000.0, 1015.0),   # valores > 800 se evalúan como referencia de 1000g
    'libra': (500.0, 508.0),
}


def _evaluar_cumple(valor: float) -> str:
    minimo, maximo = RANGOS_PESO['kilo'] if valor > 800 else RANGOS_PESO['libra']
    return "SI" if minimo <= valor <= maximo else "NO"


def _muestreo_to_resumen(m: MuestreoCalidad) -> MuestreoCalidadResumen:
    total = len(m.items)
    ok = sum(1 for it in m.items if it.cumple == "SI")
    pct = round(ok / total * 100, 1) if total > 0 else 0.0
    return MuestreoCalidadResumen(
        id=m.id, fecha=m.fecha, referencia=m.referencia,
        cantidad_solicitada=m.cantidad_solicitada, cantidad_encontrada=m.cantidad_encontrada,
        nombre_generado_por=m.nombre_generado_por, creado_en=m.creado_en, pct_cumple=pct,
    )


@router.post("/muestreos/generar", response_model=MuestreoCalidadOut, status_code=201)
def generar_muestreo(
    payload: MuestreoCalidadCreate,
    db: Session = Depends(get_db), current_user: Usuario = Depends(require_admin_o_calidad),
):
    """Junta TODOS los valores de peso ya registrados ese día para esta
    referencia (sin importar turno ni máquina), y elige al azar la cantidad
    pedida — sin repetir, y sin tocar los registros originales de Pesos."""
    registros = db.query(RegistroPesos).filter(
        RegistroPesos.fecha == payload.fecha,
        RegistroPesos.referencia == payload.referencia,
    ).all()

    pool = []
    for reg in registros:
        for fila in reg.filas:
            for pos in range(1, 7):
                valor = getattr(fila, f"muestra_{pos}")
                if valor is not None:
                    pool.append({
                        'valor': valor, 'posicion': pos,
                        'turno': reg.turno, 'maquina': reg.maquina, 'hora': fila.hora,
                        'fila_peso_id': fila.id,
                    })

    if not pool:
        raise HTTPException(
            status_code=404,
            detail="No hay ninguna muestra de peso registrada para esa fecha y referencia todavía."
        )

    cantidad_real = min(payload.cantidad_solicitada, len(pool))
    elegidas = random.sample(pool, cantidad_real)

    # Se guarda la descripción legible del catálogo (no el código crudo),
    # para que se vea bien en la lista y en el PDF — el emparejamiento con
    # los registros de Pesos ya se hizo arriba usando el código real.
    ref_catalogo = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.codigo == payload.referencia).first()
    referencia_legible = ref_catalogo.descripcion if ref_catalogo else payload.referencia

    muestreo = MuestreoCalidad(
        fecha=payload.fecha, referencia=referencia_legible,
        cantidad_solicitada=payload.cantidad_solicitada, cantidad_encontrada=cantidad_real,
        generado_por_id=current_user.id, nombre_generado_por=current_user.nombre,
    )
    db.add(muestreo)
    db.flush()

    for i, m in enumerate(elegidas, start=1):
        db.add(MuestraCalidadItem(
            muestreo_id=muestreo.id, numero_muestra=i,
            turno_origen=m['turno'], maquina_origen=m['maquina'], hora_origen=m['hora'],
            fila_peso_id=m['fila_peso_id'], posicion_muestra=m['posicion'],
            valor_peso=m['valor'], cumple=_evaluar_cumple(m['valor']),
        ))

    db.commit()
    db.refresh(muestreo)
    return muestreo


@router.get("/referencias-disponibles", response_model=List[ReferenciaDisponibleOut])
def referencias_disponibles(
    fecha: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db), _=Depends(require_admin_o_calidad),
):
    """Referencias que SÍ tienen al menos un registro de Control de Peso
    guardado para esa fecha (cualquier turno) — para llenar el desplegable
    sin riesgo de que se digite mal y no coincida con lo ya guardado.
    Devuelve también la descripción legible del catálogo de bodega, para
    que en pantalla se vea el nombre y no solo el código."""
    filas = db.query(RegistroPesos.referencia).filter(
        RegistroPesos.fecha == fecha,
        RegistroPesos.referencia.isnot(None),
        RegistroPesos.referencia != "",
    ).distinct().all()
    codigos = sorted({f[0] for f in filas})

    catalogo = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.codigo.in_(codigos)).all()
    mapa_descripciones = {r.codigo: r.descripcion for r in catalogo}

    return [
        ReferenciaDisponibleOut(codigo=c, descripcion=mapa_descripciones.get(c, c))
        for c in codigos
    ]


@router.get("/muestreos", response_model=List[MuestreoCalidadResumen])
def listar_muestreos(
    fecha: Optional[str] = Query(None),
    referencia: Optional[str] = Query(None),
    db: Session = Depends(get_db), _=Depends(require_admin_o_calidad),
):
    q = db.query(MuestreoCalidad)
    if fecha:
        q = q.filter(MuestreoCalidad.fecha == fecha)
    if referencia:
        q = q.filter(MuestreoCalidad.referencia == referencia)
    muestreos = q.order_by(MuestreoCalidad.id.desc()).all()
    return [_muestreo_to_resumen(m) for m in muestreos]


@router.get("/muestreos/{muestreo_id}", response_model=MuestreoCalidadOut)
def obtener_muestreo(muestreo_id: int, db: Session = Depends(get_db), _=Depends(require_admin_o_calidad)):
    m = db.query(MuestreoCalidad).filter(MuestreoCalidad.id == muestreo_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Muestreo no encontrado")
    return m


@router.put("/muestras/{item_id}", response_model=MuestraCalidadItemOut)
def actualizar_muestra(
    item_id: int, payload: MuestraCalidadItemUpdate,
    db: Session = Depends(get_db), _=Depends(require_admin_o_calidad),
):
    """Para que ella agregue sus observaciones de calidad, o corrija el
    cumple/no-cumple si hace falta, sobre una muestra puntual ya elegida."""
    item = db.query(MuestraCalidadItem).filter(MuestraCalidadItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Muestra no encontrada")
    if payload.cumple is not None:
        item.cumple = payload.cumple
    if payload.observaciones_calidad is not None:
        item.observaciones_calidad = payload.observaciones_calidad
    db.commit()
    db.refresh(item)
    return item


@router.delete("/muestreos/{muestreo_id}", status_code=204)
def eliminar_muestreo(muestreo_id: int, db: Session = Depends(get_db), _=Depends(require_admin_o_calidad)):
    m = db.query(MuestreoCalidad).filter(MuestreoCalidad.id == muestreo_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Muestreo no encontrado")
    db.delete(m)
    db.commit()