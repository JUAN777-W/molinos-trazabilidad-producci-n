from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ─── CATÁLOGO DE REFERENCIAS DE EMPAQUE ───────────────────────────────────────
class ReferenciaEmpaqueOut(BaseModel):
    codigo: str
    descripcion: str
    categoria: Optional[str] = None
    promedio_bobina_kg: Optional[float] = None


# ─── ORDEN DE SALIDA ───────────────────────────────────────────────────────────
class OrdenSalidaCreate(BaseModel):
    fecha: str
    turno: str
    area_solicitante: str = "Producción"
    codigo_producto: Optional[str] = None
    referencia_producto: str
    cantidad_bobinas: int
    cantidad_kg: float
    observaciones: Optional[str] = None


class OrdenSalidaOut(BaseModel):
    id: int
    fecha: str
    turno: str
    area_solicitante: str
    codigo_producto: Optional[str] = None
    referencia_producto: str
    cantidad_bobinas: int
    cantidad_kg: float
    observaciones: Optional[str] = None
    nombre_operario: str
    creado_en: Optional[datetime] = None


# ─── SUGERENCIA DE PEDIDO ──────────────────────────────────────────────────────
class SugerenciaOut(BaseModel):
    referencia_producto: str
    kg_promedio_historico: float
    kg_sugerido: float
    bobinas_sugeridas: int
    turnos_analizados: int
    fuente_promedio_bobina: str
    nota: str


# ─── RECONCILIACIÓN: PEDIDO VS. CONSUMO REAL ──────────────────────────────────
class ReconciliacionItem(BaseModel):
    orden_id: int
    fecha: str
    turno: str
    referencia_producto: str
    kg_pedido: float
    bobinas_pedidas: int
    kg_consumido_real: float
    diferencia_kg: float
    diferencia_pct: float
    estado: str


class ReconciliacionResumen(BaseModel):
    fecha: str
    total_ordenes: int
    total_kg_pedido: float
    total_kg_consumido: float
    diferencia_total_kg: float
    items: List[ReconciliacionItem]


# ─── MOVIMIENTOS DE INVENTARIO (compras, devoluciones, mercancía no apta, ajustes) ─
class MovimientoCreate(BaseModel):
    fecha: str
    tipo_operacion: str  # COMPRA | DEVOLUCION | MERCANCIA_NO_APTA | AJUSTE | INVENTARIO_INICIAL
    codigo_producto: str
    referencia_producto: str
    cantidad_kg: float
    cantidad_bobinas: int = 0
    n_documento: Optional[str] = None
    proveedor: Optional[str] = None
    destino: Optional[str] = None
    observaciones: Optional[str] = None


class MovimientoOut(BaseModel):
    id: int
    fecha: str
    tipo_operacion: str
    codigo_producto: str
    referencia_producto: str
    cantidad_kg: float
    cantidad_bobinas: int
    n_documento: Optional[str] = None
    proveedor: Optional[str] = None
    destino: Optional[str] = None
    observaciones: Optional[str] = None
    nombre_usuario: str
    creado_en: Optional[datetime] = None


# ─── CONTROL DE INVENTARIO (calculado, reemplaza pestaña CONTROL INV) ─────────
class InventarioItem(BaseModel):
    codigo: str
    descripcion: str
    categoria: Optional[str] = None
    saldo_kg: float
    saldo_bobinas: int
    consumo_promedio_mensual_kg: float
    cobertura_dias: Optional[float] = None
    estado_cobertura: str  # "CRITICO" | "BAJO" | "OK" | "SIN_CONSUMO"
    pedidos_pendientes_kg: float
    proxima_entrega_fecha: Optional[str] = None


# ─── KARDEX DE PLANTA (lo que hay físicamente en producción, no en bodega) ────
class InventarioPlantaItem(BaseModel):
    codigo: str
    descripcion: str
    categoria: Optional[str] = None
    total_entregado_kg: float
    total_consumido_kg: float
    total_devuelto_kg: float
    saldo_planta_kg: float
    # En bobinas/rollos — igual que en kilos, para saber cuántas unidades
    # físicas hay, no solo el peso.
    total_entregado_bobinas: int = 0
    total_consumido_bobinas: int = 0
    total_devuelto_bobinas: int = 0
    saldo_planta_bobinas: int = 0
    consumido_hoy_kg: float = 0.0
    consumido_mes_kg: float = 0.0
    consumo_promedio_diario_kg: float
    cobertura_dias_planta: Optional[float] = None
    estado_cobertura: str  # "SOBRA" | "OK" | "BAJO" | "SIN_DATO"
    tiene_ajuste_manual: bool = False


# ─── PEDIDOS DE COMPRA ─────────────────────────────────────────────────────────
class PedidoCompraCreate(BaseModel):
    numero_orden_compra: Optional[str] = None
    fecha: str
    proveedor: str
    codigo_producto: str
    referencia_producto: str
    cantidad_pedida_kg: float
    fecha_estimada: Optional[str] = None
    precio_unitario: Optional[float] = None
    observaciones: Optional[str] = None


class PedidoCompraOut(BaseModel):
    id: int
    numero_orden_compra: Optional[str] = None
    fecha: str
    proveedor: str
    codigo_producto: str
    referencia_producto: str
    cantidad_pedida_kg: float
    cantidad_recibida_kg: float
    fecha_estimada: Optional[str] = None
    precio_unitario: Optional[float] = None
    estado: str
    observaciones: Optional[str] = None
    creado_en: Optional[datetime] = None


class RecepcionPedidoCreate(BaseModel):
    cantidad_recibida_kg: float
    n_documento: Optional[str] = None
    observaciones: Optional[str] = None


# ─── INFORME DE RENDIMIENTOS MENSUAL ───────────────────────────────────────────
class RendimientoItem(BaseModel):
    referencia_producto: str
    kg_consumido: float
    unidades_producidas: int
    rendimiento_unid_por_kg: float
    desperdicio_kg: float
    pct_desperdicio: float
    turnos: int


class RendimientoResumen(BaseModel):
    mes: str
    total_kg_consumido: float
    total_unidades_producidas: int
    total_desperdicio_kg: float
    pct_desperdicio_promedio: float
    variacion_kg_vs_mes_anterior_pct: float
    items: List[RendimientoItem]


# ─── AJUSTE MANUAL DE SALDO EN PLANTA (conteo físico) ─────────────────────────
class AjustePlantaCreate(BaseModel):
    codigo: str
    fecha: str
    cantidad_kg: float
    cantidad_bobinas: Optional[int] = None
    observaciones: Optional[str] = None

class AjustePlantaOut(AjustePlantaCreate):
    id: int
    class Config:
        from_attributes = True