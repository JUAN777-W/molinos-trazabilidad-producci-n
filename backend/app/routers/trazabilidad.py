from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.models.models import (
    RecepcionMateriaPrima, Usuario, RegistroBobinas, RegistroRotulado, RegistroEstiba,
)
from app.schemas.trazabilidad_schemas import (
    RecepcionMateriaPrimaCreate, RecepcionMateriaPrimaOut,
    ResumenTrazabilidad, LineaTiempoSiloItem,
    BobinaResumenItem, RotuladoResumenItem, EstibaResumenItem, ConsultaTrazabilidadOut,
)
from app.auth import get_current_user, require_admin
from app.routers.informe import _es_trigo

router = APIRouter()


# ─── RECEPCIÓN DE MATERIA PRIMA ───────────────────────────────────────────────
@router.post("/recepciones", response_model=RecepcionMateriaPrimaOut, status_code=201)
def crear_recepcion(
    payload: RecepcionMateriaPrimaCreate,
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user),
):
    registro = RecepcionMateriaPrima(
        **payload.model_dump(),
        registrado_por_id=current_user.id,
        nombre_registrado_por=current_user.nombre,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


@router.get("/recepciones", response_model=List[RecepcionMateriaPrimaOut])
def listar_recepciones(
    proveedor: Optional[str] = Query(None, description="Búsqueda parcial por proveedor"),
    tipo_grano: Optional[str] = Query(None, description="TRIGO | MAIZ"),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(RecepcionMateriaPrima)
    if proveedor:
        q = q.filter(RecepcionMateriaPrima.proveedor.ilike(f"%{proveedor}%"))
    if tipo_grano:
        q = q.filter(RecepcionMateriaPrima.tipo_grano == tipo_grano.upper())
    return q.order_by(RecepcionMateriaPrima.id.desc()).all()


@router.delete("/recepciones/{recepcion_id}", status_code=204)
def eliminar_recepcion(recepcion_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    r = db.query(RecepcionMateriaPrima).filter(RecepcionMateriaPrima.id == recepcion_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Recepción no encontrada")
    db.delete(r)
    db.commit()


# ─── RESUMEN ───────────────────────────────────────────────────────────────────
@router.get("/resumen", response_model=ResumenTrazabilidad)
def resumen_trazabilidad(db: Session = Depends(get_db), _=Depends(get_current_user)):
    todas = db.query(RecepcionMateriaPrima).all()
    inicio_mes = date.today().replace(day=1).strftime('%Y-%m-%d')
    del_mes = [r for r in todas if (r.fecha or '') >= inicio_mes]

    aprobadas = [r for r in todas if r.resultado_calidad == 'APROBADO']
    pct_aprobado = round(len(aprobadas) / len(todas) * 100, 1) if todas else 0.0

    silos_activos = sorted({r.silo_destino for r in todas if r.silo_destino})

    return ResumenTrazabilidad(
        total_recepciones=len(todas),
        kg_totales_mes=round(sum(r.cantidad_kg or 0 for r in del_mes), 2),
        pct_aprobado=pct_aprobado,
        silos_activos=silos_activos,
    )


# ─── LÍNEA DE TIEMPO POR SILO ──────────────────────────────────────────────────
@router.get("/linea-tiempo-silo", response_model=List[LineaTiempoSiloItem])
def linea_tiempo_silo(
    silo: str = Query(...),
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    """
    Qué lotes de materia prima entraron a un silo específico en un rango de
    fechas — pensado para investigar hacia atrás un problema de calidad
    detectado en producción, sin necesitar rastreo exacto de molienda.
    """
    q = db.query(RecepcionMateriaPrima).filter(RecepcionMateriaPrima.silo_destino.ilike(f"%{silo}%"))
    if desde:
        q = q.filter(RecepcionMateriaPrima.fecha >= desde)
    if hasta:
        q = q.filter(RecepcionMateriaPrima.fecha <= hasta)
    registros = q.order_by(RecepcionMateriaPrima.fecha.desc()).all()

    return [
        LineaTiempoSiloItem(
            fecha=r.fecha, tipo_grano=r.tipo_grano, proveedor=r.proveedor,
            lote_proveedor=r.lote_proveedor, cantidad_kg=r.cantidad_kg or 0,
            resultado_calidad=r.resultado_calidad or '',
        )
        for r in registros
    ]


# ══════════════════════════════════════════════════════════════════════════════
# CONSULTA DE TRAZABILIDAD — dado fecha + máquina, junta lo que ya existe en
# Bobinas, Rotulado y Estibas de ese turno, más la materia prima que entró a
# planta en los días previos (misma lógica "aproximada por ventana de fechas"
# que ya usa /linea-tiempo-silo, porque el sistema no rastrea la molienda
# exacta). No requiere ninguna tabla nueva ni tocar los formatos de operario.
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/consulta", response_model=ConsultaTrazabilidadOut)
def consultar_trazabilidad(
    fecha: str = Query(...),
    maquina: str = Query(...),
    dias_ventana_materia_prima: int = Query(15, ge=1, le=60),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    tipo_grano = 'TRIGO' if _es_trigo(maquina) else 'MAIZ'

    regs_bobinas = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha == fecha, RegistroBobinas.maquina.ilike(f"%{maquina}%")
    ).order_by(RegistroBobinas.id.desc()).all()
    bobinas = [
        BobinaResumenItem(
            id=r.id, turno=r.turno, referencia_producto=r.referencia_producto,
            proveedor=r.proveedor, nombre_operario=r.nombre_operario,
            materiales_empaque=sorted({f.referencia_empaque for f in r.filas if f.referencia_empaque}),
            kg_consumidos=round(sum(f.consumido or 0 for f in r.filas), 2),
        )
        for r in regs_bobinas
    ]

    regs_rotulado = db.query(RegistroRotulado).filter(
        RegistroRotulado.fecha == fecha, RegistroRotulado.maquina == maquina
    ).order_by(RegistroRotulado.id.desc()).all()
    rotulado = [
        RotuladoResumenItem(
            id=r.id, nombre_operario=r.nombre_operario,
            total_fechados=len(r.filas),
            fechados_cumplen=sum(1 for f in r.filas if f.fechado_cumple == 'SI'),
            fechados_no_cumplen=sum(1 for f in r.filas if f.fechado_cumple == 'NO'),
        )
        for r in regs_rotulado
    ]

    regs_estibas = db.query(RegistroEstiba).filter(
        RegistroEstiba.fecha == fecha, RegistroEstiba.maquina == maquina
    ).order_by(RegistroEstiba.numero_estiva).all()
    estibas = [
        EstibaResumenItem(
            id=r.id, turno=r.turno, numero_estiva=r.numero_estiva,
            referencia_producto=r.referencia_producto, cantidad_pacas=r.cantidad_pacas,
            nombre_operario_montacargas=r.nombre_operario_montacargas,
        )
        for r in regs_estibas
    ]

    fecha_desde_mp = (date.fromisoformat(fecha) - timedelta(days=dias_ventana_materia_prima)).strftime('%Y-%m-%d')
    materia_prima = db.query(RecepcionMateriaPrima).filter(
        RecepcionMateriaPrima.tipo_grano == tipo_grano,
        RecepcionMateriaPrima.fecha >= fecha_desde_mp, RecepcionMateriaPrima.fecha <= fecha,
    ).order_by(RecepcionMateriaPrima.fecha.desc()).all()

    return ConsultaTrazabilidadOut(
        fecha=fecha, maquina=maquina, tipo_grano=tipo_grano,
        bobinas=bobinas, rotulado=rotulado, estibas=estibas,
        materia_prima_aproximada=materia_prima,
        nota=(
            f"La materia prima mostrada es la que entró a planta en los {dias_ventana_materia_prima} días "
            f"previos a esta fecha para {tipo_grano.lower()} — es una aproximación por ventana de tiempo, "
            "no un rastreo exacto de qué lote específico se molió (los silos pueden mezclar varios lotes)."
        ),
    )