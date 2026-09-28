from pydantic import BaseModel
from typing import Optional, List


# ─── PLAN PREVENTIVO ────────────────────────────────────────────────────────
class PlanPreventivoOut(BaseModel):
    id: int
    linea: str
    seccion_componente: str
    actividad: str
    tipo: Optional[str] = None
    frecuencia: Optional[str] = None
    responsable: Optional[str] = None
    tiempo_min: Optional[int] = None
    repuesto_insumo: Optional[str] = None
    class Config:
        from_attributes = True


# ─── CRONOGRAMA ─────────────────────────────────────────────────────────────
class CronogramaItemOut(BaseModel):
    id: int
    maquina: str
    seccion_componente: str
    frecuencia: Optional[str] = None
    ultima_ejecucion: Optional[str] = None
    proxima_fecha: Optional[str] = None      # calculado
    dias_para_vencer: Optional[int] = None   # calculado (negativo = vencido)
    estado: str                              # SIN_REGISTRAR | OK | PROXIMO | VENCIDO — calculado
    observaciones: Optional[str] = None
    turnos_produccion_recientes: Optional[int] = None  # cruce con Bobinas (últimos 30 días), solo si VENCIDO
    class Config:
        from_attributes = True


class CronogramaEjecucionUpdate(BaseModel):
    ultima_ejecucion: str  # 'YYYY-MM-DD'
    observaciones: Optional[str] = None


# ─── HISTORIAL CORRECTIVO ───────────────────────────────────────────────────
class HistorialCorrectivoCreate(BaseModel):
    maquina: str
    equipo_componente: str
    fecha_mantenimiento: Optional[str] = None  # algunos registros históricos del Excel original no traían fecha
    fecha_cambio: Optional[str] = None
    mantenimiento_realizado: str
    costo: Optional[float] = None
    estado_resultante: str  # MALO | MEDIO | BUENO
    hubo_cambio: Optional[str] = None          # SI | NO — igual, algún registro histórico venía sin este dato
    prioridad: Optional[str] = None  # CRITICA | ALTA | MEDIA | BAJA

class HistorialCorrectivoOut(HistorialCorrectivoCreate):
    id: int
    class Config:
        from_attributes = True


# ─── REPUESTOS CRÍTICOS ─────────────────────────────────────────────────────
class RepuestoCriticoOut(BaseModel):
    id: int
    seccion: Optional[str] = None
    componente: Optional[str] = None
    referencia: Optional[str] = None
    marca: Optional[str] = None
    cantidad_instalada: Optional[int] = None
    maquinas_aplica: Optional[str] = None
    stock_minimo_sugerido: Optional[int] = None
    class Config:
        from_attributes = True


# ─── RESUMEN / ALERTAS ──────────────────────────────────────────────────────
class ResumenMantenimiento(BaseModel):
    total_puntos: int
    vencidos: int
    proximos: int
    ok: int
    sin_registrar: int
    costo_total_historico: float
    pct_historico_con_costo: float


# ─── SOLICITUDES DE MANTENIMIENTO (reporte puntual de operarios) ────────────
class SolicitudMantenimientoCreate(BaseModel):
    maquina: str
    descripcion_problema: str
    prioridad: str = "MEDIA"  # CRITICA | ALTA | MEDIA | BAJA

class SolicitudResolverIn(BaseModel):
    resolucion_descripcion: str
    costo: Optional[float] = None
    estado_resultante: str = "BUENO"  # MALO | MEDIO | BUENO
    hubo_cambio: str = "NO"           # SI | NO

class SolicitudMantenimientoOut(BaseModel):
    id: int
    maquina: str
    descripcion_problema: str
    prioridad: str
    estado: str  # PENDIENTE | RESUELTO
    fecha_reporte: str
    nombre_reportado_por: Optional[str] = None
    fecha_resolucion: Optional[str] = None
    resolucion_descripcion: Optional[str] = None
    class Config:
        from_attributes = True


# ─── NOTIFICACIONES (campanita — combina cronograma vencido + solicitudes) ──
class NotificacionOut(BaseModel):
    tipo: str          # "PREVENTIVO" | "SOLICITUD"
    id_origen: int      # id del CronogramaMantenimiento o de la SolicitudMantenimiento
    maquina: str
    descripcion: str
    prioridad_o_estado: str  # para preventivo: "VENCIDO"/"PROXIMO"; para solicitud: la prioridad
    fecha: str