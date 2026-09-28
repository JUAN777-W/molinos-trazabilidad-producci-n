from pydantic import BaseModel
from typing import Optional, List


class InfoMaquinaOut(BaseModel):
    maquina: str
    turno: str
    fecha: str
    referencia_producto: Optional[str] = None
    referencia_label: Optional[str] = None
    siguiente_numero_estiva: int
    tipo: Optional[str] = None   # TRIGO | MAIZ — para filtrar el desplegable de referencia si hace falta corregirla


class RegistroEstibaCreate(BaseModel):
    fecha: str
    turno: str
    maquina: str
    referencia_producto: str
    cantidad_pacas: int
    plancha: str
    alto: str
    nombre_operario_montacargas: str

class RegistroEstibaOut(RegistroEstibaCreate):
    id: int
    numero_estiva: int
    class Config:
        from_attributes = True
