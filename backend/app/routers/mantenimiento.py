from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models.models import (
    PlanPreventivo, CronogramaMantenimiento, HistorialCorrectivo, RepuestoCritico,
    RegistroBobinas, Usuario, SolicitudMantenimiento,
)
from app.schemas.mantenimiento_schemas import (
    PlanPreventivoOut, CronogramaItemOut, CronogramaEjecucionUpdate,
    HistorialCorrectivoCreate, HistorialCorrectivoOut, RepuestoCriticoOut,
    ResumenMantenimiento, SolicitudMantenimientoCreate, SolicitudResolverIn,
    SolicitudMantenimientoOut, NotificacionOut,
)
from app.auth import get_current_user, require_admin

router = APIRouter()

FRECUENCIA_DIAS = {
    'Diaria': 1, 'Semanal': 7, 'Quincenal': 15, 'Mensual': 30,
    'Bimestral': 60, 'Trimestral': 90, 'Semestral': 180, 'Anual': 365,
}

# ─────────────────────────────────────────────────────────────────────────────
# MAPEO entre el nombre de máquina del cronograma de mantenimiento (heredado
# del Excel: "EMPACA 1".."EMPACA 9", "ENFA 1".."ENFA 4") y el código real que
# usan Bobinas/Rotulado/Pesos (1P, 2Q, 4T, 5U, 6V, 7W, 8S, 9X, 10Y, 11Z).
#
# ⚠️ PENDIENTE DE CONFIRMAR: se deja vacío a propósito. Sin este mapeo, el
# cruce "¿cuánto ha producido esta máquina mientras su mantenimiento está
# vencido?" no se puede calcular con certeza — más vale no adivinar y mostrar
# "sin dato" a que se muestre información cruzada incorrecta.
# Rellenar así una vez se confirme, por ejemplo:
#   MAPEO_MAQUINA_CRONOGRAMA = {'EMPACA 1': '1P', 'EMPACA 2': '2Q', ...}
# ─────────────────────────────────────────────────────────────────────────────
MAPEO_MAQUINA_CRONOGRAMA: dict = {}


def _calcular_estado_cronograma(item: CronogramaMantenimiento) -> dict:
    if not item.ultima_ejecucion:
        return {'proxima_fecha': None, 'dias_para_vencer': None, 'estado': 'SIN_REGISTRAR'}

    dias_freq = FRECUENCIA_DIAS.get(item.frecuencia or '', 30)
    try:
        ultima_dt = datetime.strptime(item.ultima_ejecucion, '%Y-%m-%d').date()
    except ValueError:
        return {'proxima_fecha': None, 'dias_para_vencer': None, 'estado': 'SIN_REGISTRAR'}

    proxima_dt = ultima_dt + timedelta(days=dias_freq)
    dias_para_vencer = (proxima_dt - date.today()).days

    if dias_para_vencer < 0:
        estado = 'VENCIDO'
    elif dias_para_vencer <= 7:
        estado = 'PROXIMO'
    else:
        estado = 'OK'

    return {
        'proxima_fecha': proxima_dt.strftime('%Y-%m-%d'),
        'dias_para_vencer': dias_para_vencer,
        'estado': estado,
    }


def _turnos_produccion_recientes(db: Session, maquina_cronograma: str, dias: int = 30) -> Optional[int]:
    codigo = MAPEO_MAQUINA_CRONOGRAMA.get(maquina_cronograma)
    if not codigo:
        return None
    desde = (date.today() - timedelta(days=dias)).strftime('%Y-%m-%d')
    return db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha >= desde,
        RegistroBobinas.maquina.ilike(f"%{codigo}%"),
    ).count()


# ─── PLAN PREVENTIVO (catálogo, solo lectura) ────────────────────────────────
@router.get("/plan-preventivo", response_model=List[PlanPreventivoOut])
def listar_plan_preventivo(
    linea: Optional[str] = Query(None, description="EMPACADORAS | ENFARDADORAS | BANDAS_SOPLADORES"),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(PlanPreventivo)
    if linea:
        q = q.filter(PlanPreventivo.linea == linea.upper())
    return q.order_by(PlanPreventivo.linea, PlanPreventivo.seccion_componente).all()


# ─── CRONOGRAMA ───────────────────────────────────────────────────────────────
@router.get("/cronograma", response_model=List[CronogramaItemOut])
def listar_cronograma(
    maquina: Optional[str] = Query(None),
    estado: Optional[str] = Query(None, description="Filtrar por SIN_REGISTRAR | OK | PROXIMO | VENCIDO"),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(CronogramaMantenimiento)
    if maquina:
        q = q.filter(CronogramaMantenimiento.maquina == maquina)
    items = q.order_by(CronogramaMantenimiento.maquina, CronogramaMantenimiento.seccion_componente).all()

    resultado = []
    for item in items:
        calc = _calcular_estado_cronograma(item)
        turnos = _turnos_produccion_recientes(db, item.maquina) if calc['estado'] == 'VENCIDO' else None
        out = CronogramaItemOut(
            id=item.id, maquina=item.maquina, seccion_componente=item.seccion_componente,
            frecuencia=item.frecuencia, ultima_ejecucion=item.ultima_ejecucion,
            proxima_fecha=calc['proxima_fecha'], dias_para_vencer=calc['dias_para_vencer'],
            estado=calc['estado'], observaciones=item.observaciones,
            turnos_produccion_recientes=turnos,
        )
        if not estado or out.estado == estado.upper():
            resultado.append(out)

    # Ordenar: vencidos primero, luego próximos, luego el resto
    orden_prioridad = {'VENCIDO': 0, 'PROXIMO': 1, 'SIN_REGISTRAR': 2, 'OK': 3}
    resultado.sort(key=lambda x: orden_prioridad.get(x.estado, 9))
    return resultado


@router.put("/cronograma/{item_id}/ejecutar", response_model=CronogramaItemOut)
def registrar_ejecucion(
    item_id: int, payload: CronogramaEjecucionUpdate,
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user),
):
    item = db.query(CronogramaMantenimiento).filter(CronogramaMantenimiento.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Punto de cronograma no encontrado")
    item.ultima_ejecucion = payload.ultima_ejecucion
    if payload.observaciones is not None:
        item.observaciones = payload.observaciones
    item.actualizado_por_id = current_user.id
    db.commit()
    db.refresh(item)

    calc = _calcular_estado_cronograma(item)
    return CronogramaItemOut(
        id=item.id, maquina=item.maquina, seccion_componente=item.seccion_componente,
        frecuencia=item.frecuencia, ultima_ejecucion=item.ultima_ejecucion,
        proxima_fecha=calc['proxima_fecha'], dias_para_vencer=calc['dias_para_vencer'],
        estado=calc['estado'], observaciones=item.observaciones,
        turnos_produccion_recientes=None,
    )


# ─── HISTORIAL CORRECTIVO ─────────────────────────────────────────────────────
@router.get("/historial", response_model=List[HistorialCorrectivoOut])
def listar_historial(
    maquina: Optional[str] = Query(None),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(HistorialCorrectivo)
    if maquina:
        q = q.filter(HistorialCorrectivo.maquina == maquina)
    return q.order_by(HistorialCorrectivo.id.desc()).all()


@router.post("/historial", response_model=HistorialCorrectivoOut, status_code=201)
def crear_historial(
    payload: HistorialCorrectivoCreate,
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user),
):
    registro = HistorialCorrectivo(**payload.model_dump(), registrado_por_id=current_user.id)
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


# ─── REPUESTOS CRÍTICOS (catálogo, solo lectura) ─────────────────────────────
@router.get("/repuestos", response_model=List[RepuestoCriticoOut])
def listar_repuestos(
    seccion: Optional[str] = Query(None),
    maquina: Optional[str] = Query(None, description="Filtra por texto contenido en 'maquinas_aplica'"),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(RepuestoCritico)
    if seccion:
        q = q.filter(RepuestoCritico.seccion == seccion)
    if maquina:
        q = q.filter(RepuestoCritico.maquinas_aplica.ilike(f"%{maquina}%"))
    return q.order_by(RepuestoCritico.seccion, RepuestoCritico.componente).all()


# ─── RESUMEN / ALERTAS ────────────────────────────────────────────────────────
@router.get("/resumen", response_model=ResumenMantenimiento)
def resumen_mantenimiento(db: Session = Depends(get_db), _=Depends(get_current_user)):
    items = db.query(CronogramaMantenimiento).all()
    conteo = {'VENCIDO': 0, 'PROXIMO': 0, 'OK': 0, 'SIN_REGISTRAR': 0}
    for item in items:
        estado = _calcular_estado_cronograma(item)['estado']
        conteo[estado] += 1

    historial = db.query(HistorialCorrectivo).all()
    con_costo = [h for h in historial if h.costo is not None]
    costo_total = sum(h.costo for h in con_costo)
    pct_con_costo = round(len(con_costo) / len(historial) * 100, 1) if historial else 0.0

    return ResumenMantenimiento(
        total_puntos=len(items),
        vencidos=conteo['VENCIDO'], proximos=conteo['PROXIMO'],
        ok=conteo['OK'], sin_registrar=conteo['SIN_REGISTRAR'],
        costo_total_historico=round(costo_total, 2),
        pct_historico_con_costo=pct_con_costo,
    )


# ══════════════════════════════════════════════════════════════════════════════
# SOLICITUDES DE MANTENIMIENTO — reporte puntual de un problema en una máquina,
# hecho por cualquier operario (no viene del cronograma preventivo).
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/solicitudes", response_model=SolicitudMantenimientoOut, status_code=201)
def crear_solicitud(
    payload: SolicitudMantenimientoCreate,
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user),
):
    solicitud = SolicitudMantenimiento(
        maquina=payload.maquina, descripcion_problema=payload.descripcion_problema,
        prioridad=payload.prioridad, estado="PENDIENTE",
        fecha_reporte=date.today().strftime('%Y-%m-%d'),
        reportado_por_id=current_user.id, nombre_reportado_por=current_user.nombre,
    )
    db.add(solicitud)
    db.commit()
    db.refresh(solicitud)
    return solicitud


@router.get("/solicitudes", response_model=List[SolicitudMantenimientoOut])
def listar_solicitudes(
    estado: Optional[str] = Query(None, description="PENDIENTE | RESUELTO"),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(SolicitudMantenimiento)
    if estado:
        q = q.filter(SolicitudMantenimiento.estado == estado.upper())
    return q.order_by(SolicitudMantenimiento.id.desc()).all()


@router.put("/solicitudes/{solicitud_id}/resolver", response_model=SolicitudMantenimientoOut)
def resolver_solicitud(
    solicitud_id: int, payload: SolicitudResolverIn,
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user),
):
    """Marca la solicitud como resuelta Y crea automáticamente el registro
    correspondiente en el Historial Correctivo — así queda documentado en un
    solo lugar, sin tener que escribirlo dos veces."""
    solicitud = db.query(SolicitudMantenimiento).filter(SolicitudMantenimiento.id == solicitud_id).first()
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    if solicitud.estado == "RESUELTO":
        raise HTTPException(status_code=400, detail="Esta solicitud ya estaba resuelta")

    hoy = date.today().strftime('%Y-%m-%d')

    historial = HistorialCorrectivo(
        maquina=solicitud.maquina,
        equipo_componente=solicitud.descripcion_problema[:300],
        fecha_mantenimiento=hoy,
        mantenimiento_realizado=payload.resolucion_descripcion,
        costo=payload.costo,
        estado_resultante=payload.estado_resultante,
        hubo_cambio=payload.hubo_cambio,
        prioridad=solicitud.prioridad,
        registrado_por_id=current_user.id,
    )
    db.add(historial)
    db.flush()  # para obtener historial.id antes de enlazarlo

    solicitud.estado = "RESUELTO"
    solicitud.fecha_resolucion = hoy
    solicitud.resolucion_descripcion = payload.resolucion_descripcion
    solicitud.resuelto_por_id = current_user.id
    solicitud.historial_correctivo_id = historial.id

    db.commit()
    db.refresh(solicitud)
    return solicitud


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICACIONES — la campanita del ingeniero. Combina en una sola lista:
#   - Puntos del cronograma preventivo que ya están VENCIDOS
#   - Solicitudes puntuales de operarios que siguen PENDIENTES
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/notificaciones", response_model=List[NotificacionOut])
def listar_notificaciones(db: Session = Depends(get_db), _=Depends(get_current_user)):
    notificaciones: List[NotificacionOut] = []

    cronograma = db.query(CronogramaMantenimiento).all()
    for item in cronograma:
        calc = _calcular_estado_cronograma(item)
        if calc['estado'] == 'VENCIDO':
            notificaciones.append(NotificacionOut(
                tipo="PREVENTIVO", id_origen=item.id, maquina=item.maquina,
                descripcion=f"Mantenimiento preventivo vencido: {item.seccion_componente} ({item.frecuencia})",
                prioridad_o_estado="VENCIDO",
                fecha=calc['proxima_fecha'] or '',
            ))

    solicitudes = db.query(SolicitudMantenimiento).filter(SolicitudMantenimiento.estado == "PENDIENTE").all()
    for s in solicitudes:
        notificaciones.append(NotificacionOut(
            tipo="SOLICITUD", id_origen=s.id, maquina=s.maquina,
            descripcion=s.descripcion_problema,
            prioridad_o_estado=s.prioridad,
            fecha=s.fecha_reporte,
        ))

    # Más urgente primero: solicitudes CRITICA/ALTA y preventivos vencidos arriba
    orden_prioridad = {'CRITICA': 0, 'VENCIDO': 0, 'ALTA': 1, 'MEDIA': 2, 'BAJA': 3}
    notificaciones.sort(key=lambda n: orden_prioridad.get(n.prioridad_o_estado, 2))
    return notificaciones