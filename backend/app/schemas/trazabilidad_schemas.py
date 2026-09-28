from pydantic import BaseModel
from typing import Optional, List


class RecepcionMateriaPrimaCreate(BaseModel):
    fecha: str
    tipo_grano: str              # TRIGO | MAIZ
    proveedor: str
    lote_proveedor: Optional[str] = None
    placa_vehiculo: Optional[str] = None
    cantidad_kg: float
    silo_destino: str
    humedad_pct: Optional[float] = None
    impurezas_pct: Optional[float] = None
    peso_especifico: Optional[float] = None
    resultado_calidad: str = "APROBADO"   # APROBADO | CONDICIONAL | RECHAZADO
    observaciones_calidad: Optional[str] = None

class RecepcionMateriaPrimaOut(RecepcionMateriaPrimaCreate):
    id: int
    nombre_registrado_por: Optional[str] = None
    class Config:
        from_attributes = True


class ResumenTrazabilidad(BaseModel):
    total_recepciones: int
    kg_totales_mes: float
    pct_aprobado: float
    silos_activos: List[str]


class LineaTiempoSiloItem(BaseModel):
    fecha: str
    tipo_grano: str
    proveedor: str
    lote_proveedor: Optional[str] = None
    cantidad_kg: float
    resultado_calidad: str


# ─── CONSULTA DE TRAZABILIDAD (Materia Prima → Empaque → Estibas) ─────────────
class BobinaResumenItem(BaseModel):
    id: int
    turno: Optional[str] = None
    referencia_producto: Optional[str] = None
    proveedor: Optional[str] = None
    nombre_operario: Optional[str] = None
    materiales_empaque: List[str] = []
    kg_consumidos: float = 0.0

class RotuladoResumenItem(BaseModel):
    id: int
    nombre_operario: Optional[str] = None
    total_fechados: int
    fechados_cumplen: int
    fechados_no_cumplen: int

class EstibaResumenItem(BaseModel):
    id: int
    turno: Optional[str] = None
    numero_estiva: int
    referencia_producto: Optional[str] = None
    cantidad_pacas: Optional[int] = None
    nombre_operario_montacargas: Optional[str] = None

class ConsultaTrazabilidadOut(BaseModel):
    fecha: str
    maquina: str
    tipo_grano: str  # TRIGO | MAIZ — inferido de la máquina
    bobinas: List[BobinaResumenItem]
    rotulado: List[RotuladoResumenItem]
    estibas: List[EstibaResumenItem]
    materia_prima_aproximada: List[RecepcionMateriaPrimaOut]
    nota: str