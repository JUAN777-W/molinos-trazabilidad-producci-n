from pydantic import BaseModel
from typing import Optional, List


class RegistroMermaBase(BaseModel):
    fecha: str
    turno: str
    maquina: str
    referencia_producto: Optional[str] = ""
    proveedor_empaque: Optional[str] = ""
    tipo_merma: str
    cantidad: float
    unidad_medida: str
    causa_raiz: Optional[str] = ""
    observaciones: Optional[str] = ""


class RegistroMermaCreate(RegistroMermaBase):
    pass


class RegistroMermaOut(RegistroMermaBase):
    id: int
    nombre_operario: Optional[str] = ""
    class Config:
        from_attributes = True


class ResumenProveedorMermaItem(BaseModel):
    proveedor: str
    total_kg: float
    total_und: int
    registros: int


class ResumenTipoMermaItem(BaseModel):
    tipo_merma: str
    total_kg: float
    total_und: int
    registros: int


class ResumenMermasOut(BaseModel):
    por_proveedor: List[ResumenProveedorMermaItem]
    por_tipo: List[ResumenTipoMermaItem]
    total_registros: int
