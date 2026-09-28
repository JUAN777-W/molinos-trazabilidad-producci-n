from pydantic import BaseModel
from typing import Optional, List


class RegistroParoCreate(BaseModel):
    fecha: str
    turno: str
    maquina: str
    hora_inicio: str
    hora_fin: str
    categoria_paro: str
    descripcion_motivo: Optional[str] = ""
    requirio_mantenimiento: bool = False


class RegistroParoOut(BaseModel):
    id: int
    fecha: str
    turno: str
    maquina: str
    hora_inicio: str
    hora_fin: str
    duracion_minutos: float
    categoria_paro: str
    descripcion_motivo: Optional[str] = ""
    requirio_mantenimiento: bool
    solicitud_mantenimiento_id: Optional[int] = None
    nombre_operario: Optional[str] = ""
    class Config:
        from_attributes = True


class DisponibilidadMaquinaItem(BaseModel):
    maquina: str
    turnos_trabajados: int
    minutos_turno_teorico: float
    minutos_parado: float
    disponibilidad_pct: float


class ParoPorCategoriaItem(BaseModel):
    categoria_paro: str
    cantidad_paros: int
    minutos: float
    pct_del_total: float


class OEEResumenOut(BaseModel):
    fecha_desde: str
    fecha_hasta: str
    disponibilidad_pct: float
    rendimiento_pct: float
    calidad_pct: float
    oee_pct: float
    total_paros: int
    minutos_totales_parada: float
    disponibilidad_por_maquina: List[DisponibilidadMaquinaItem]
    paros_por_categoria: List[ParoPorCategoriaItem]
    nota_metodologia: str
