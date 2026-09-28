from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ─── Generar un muestreo nuevo ────────────────────────────────────────────────
class MuestreoCalidadCreate(BaseModel):
    fecha: str                    # 'YYYY-MM-DD' — se buscan AMBOS turnos de ese día
    referencia: str                # código o descripción, igual a como se guardó en Pesos
    cantidad_solicitada: int = 98


class MuestraCalidadItemOut(BaseModel):
    id: int
    numero_muestra: int
    turno_origen: Optional[str] = None
    maquina_origen: Optional[str] = None
    hora_origen: Optional[str] = None
    posicion_muestra: Optional[int] = None
    valor_peso: float
    cumple: Optional[str] = None
    observaciones_calidad: Optional[str] = None
    class Config:
        from_attributes = True


class MuestreoCalidadOut(BaseModel):
    id: int
    fecha: str
    referencia: str
    cantidad_solicitada: int
    cantidad_encontrada: int
    nombre_generado_por: Optional[str] = None
    creado_en: Optional[datetime] = None
    items: List[MuestraCalidadItemOut] = []
    class Config:
        from_attributes = True


class MuestreoCalidadResumen(BaseModel):
    """Para el listado — sin los items, más liviano."""
    id: int
    fecha: str
    referencia: str
    cantidad_solicitada: int
    cantidad_encontrada: int
    nombre_generado_por: Optional[str] = None
    creado_en: Optional[datetime] = None
    pct_cumple: float
    class Config:
        from_attributes = True


# ─── Actualizar observaciones/cumple de una muestra individual ───────────────
class MuestraCalidadItemUpdate(BaseModel):
    cumple: Optional[str] = None              # por si ella necesita corregirlo a mano
    observaciones_calidad: Optional[str] = None