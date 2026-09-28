from pydantic import BaseModel
from typing import Optional, List


class FilaBobinaBase(BaseModel):
    numero_fila: int
    maquina_grupo: Optional[str] = ""
    referencia_empaque: Optional[str] = ""
    peso_montar: Optional[float] = 0
    peso_desmontar: Optional[float] = 0
    peso_desmontar_estimado: Optional[bool] = False
    consumido: Optional[float] = 0
    contador: Optional[int] = 0
    observaciones: Optional[str] = ""

class FilaBobinaCreate(FilaBobinaBase):
    pass

class FilaBobinaOut(FilaBobinaBase):
    id: int
    class Config:
        from_attributes = True


class RegistroBobinasBase(BaseModel):
    periodo: Optional[str] = ""
    referencia_producto: Optional[str] = ""
    referencia_enfardadora: Optional[str] = ""
    maquina: Optional[str] = ""
    proveedor: Optional[str] = ""
    fecha: Optional[str] = ""
    turno: Optional[str] = ""
    peso_desperdicio: Optional[float] = 0
    peso_desperdicio_fardo: Optional[float] = 0
    nombre_operario: Optional[str] = ""
    firma_data: Optional[str] = ""
    pro_numero: Optional[str] = ""
    lote: Optional[str] = ""

class RegistroBobinasCreate(RegistroBobinasBase):
    filas: List[FilaBobinaCreate] = []

class RegistroBobinasOut(RegistroBobinasBase):
    id: int
    filas: List[FilaBobinaOut] = []
    class Config:
        from_attributes = True


class FilaRotuladoBase(BaseModel):
    numero_fila: int
    hora: Optional[str] = ""
    fechado: Optional[str] = ""
    fechado_cumple: Optional[str] = "SI"
    sellado_cumple: Optional[str] = "SI"
    referencia: Optional[str] = ""

class FilaRotuladoCreate(FilaRotuladoBase):
    pass

class FilaRotuladoOut(FilaRotuladoBase):
    id: int
    class Config:
        from_attributes = True


class RegistroRotuladoBase(BaseModel):
    fecha: Optional[str] = ""
    turno: Optional[str] = ""
    maquina: Optional[str] = ""
    nombre_operario: Optional[str] = ""
    firma_data: Optional[str] = ""
    pro_numero: Optional[str] = ""
    lote: Optional[str] = ""

class RegistroRotuladoCreate(RegistroRotuladoBase):
    filas: List[FilaRotuladoCreate] = []

class RegistroRotuladoOut(RegistroRotuladoBase):
    id: int
    filas: List[FilaRotuladoOut] = []
    class Config:
        from_attributes = True


class FilaPesoBase(BaseModel):
    numero_fila: int
    hora: Optional[str] = ""
    muestra_1: Optional[float] = None
    muestra_2: Optional[float] = None
    muestra_3: Optional[float] = None
    muestra_4: Optional[float] = None
    muestra_5: Optional[float] = None
    muestra_6: Optional[float] = None
    muestra_7: Optional[float] = None
    muestra_8: Optional[float] = None
    muestra_9: Optional[float] = None
    muestra_10: Optional[float] = None
    muestra_11: Optional[float] = None
    muestra_12: Optional[float] = None
    muestra_13: Optional[float] = None
    muestra_14: Optional[float] = None
    muestra_15: Optional[float] = None
    muestra_16: Optional[float] = None
    muestra_17: Optional[float] = None
    muestra_18: Optional[float] = None
    muestra_19: Optional[float] = None
    muestra_20: Optional[float] = None
    muestra_21: Optional[float] = None
    muestra_22: Optional[float] = None
    muestra_23: Optional[float] = None
    muestra_24: Optional[float] = None
    muestra_25: Optional[float] = None
    observaciones: Optional[str] = ""

class FilaPesoCreate(FilaPesoBase):
    pass

class FilaPesoOut(FilaPesoBase):
    id: int
    class Config:
        from_attributes = True


class RegistroPesosBase(BaseModel):
    fecha: Optional[str] = ""
    turno: Optional[str] = ""
    maquina: Optional[str] = ""
    referencia: Optional[str] = ""
    nombre_operario: Optional[str] = ""
    firma_data: Optional[str] = ""
    pro_numero: Optional[str] = ""
    lote: Optional[str] = ""

class RegistroPesosCreate(RegistroPesosBase):
    filas: List[FilaPesoCreate] = []

class RegistroPesosOut(RegistroPesosBase):
    id: int
    filas: List[FilaPesoOut] = []
    class Config:
        from_attributes = True


# ── Control de Peso — Enfardadoras (formato aparte, 6 muestras) ──────────────
class FilaPesoEnfardadoraBase(BaseModel):
    numero_fila: int
    hora: Optional[str] = ""
    muestra_1: Optional[float] = None
    muestra_2: Optional[float] = None
    muestra_3: Optional[float] = None
    muestra_4: Optional[float] = None
    muestra_5: Optional[float] = None
    muestra_6: Optional[float] = None
    muestra_7: Optional[float] = None
    muestra_8: Optional[float] = None
    muestra_9: Optional[float] = None
    muestra_10: Optional[float] = None
    muestra_11: Optional[float] = None
    muestra_12: Optional[float] = None
    muestra_13: Optional[float] = None
    muestra_14: Optional[float] = None
    muestra_15: Optional[float] = None
    observaciones: Optional[str] = ""

class FilaPesoEnfardadoraCreate(FilaPesoEnfardadoraBase):
    pass

class FilaPesoEnfardadoraOut(FilaPesoEnfardadoraBase):
    id: int
    class Config:
        from_attributes = True

class RegistroPesoEnfardadoraBase(BaseModel):
    fecha: Optional[str] = ""
    turno: Optional[str] = ""
    enfardadora: Optional[str] = ""
    maquinas: Optional[str] = ""
    referencia: Optional[str] = ""
    nombre_operario: Optional[str] = ""
    firma_data: Optional[str] = ""
    pro_numero: Optional[str] = ""
    lote: Optional[str] = ""

class RegistroPesoEnfardadoraCreate(RegistroPesoEnfardadoraBase):
    filas: List[FilaPesoEnfardadoraCreate] = []

class RegistroPesoEnfardadoraOut(RegistroPesoEnfardadoraBase):
    id: int
    filas: List[FilaPesoEnfardadoraOut] = []
    class Config:
        from_attributes = True


class EstimacionRestanteOut(BaseModel):
    disponible: bool
    peso_por_unidad: Optional[float] = None
    consumido_estimado: Optional[float] = None
    peso_restante_estimado: Optional[float] = None
    fuente_fila_id: Optional[int] = None
    fuente_registro_id: Optional[int] = None