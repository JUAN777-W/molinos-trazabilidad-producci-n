from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RegistroBobinas(Base):
    __tablename__ = "registro_bobinas"

    id = Column(Integer, primary_key=True, index=True)
    periodo = Column(String(100))
    referencia_producto = Column(String(100))
    referencia_enfardadora = Column(String(50), nullable=True)  # ancho de fardo (código de bodega), distinto del material de Empacadora A/B
    maquina = Column(String(50))
    proveedor = Column(String(100))
    fecha = Column(String(20))
    turno = Column(String(20))
    peso_desperdicio = Column(Float, default=0)
    peso_desperdicio_fardo = Column(Float, default=0)
    nombre_operario = Column(String(200))
    firma_data = Column(Text)
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pro_numero = Column(String(50), nullable=True)  # nº de orden de producción del lote de exportación, lo asigna el admin en Informes
    lote = Column(String(100), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    filas = relationship("FilaBobina", back_populates="registro", cascade="all, delete-orphan")


class FilaBobina(Base):
    __tablename__ = "filas_bobinas"

    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("registro_bobinas.id"))
    numero_fila = Column(Integer)
    maquina_grupo = Column(String(10))
    referencia_empaque = Column(String(200))
    peso_montar = Column(Float, default=0)
    peso_desmontar = Column(Float, default=0)
    peso_desmontar_estimado = Column(Boolean, default=False)  # True = calculado automático, no pesado de verdad
    consumido = Column(Float, default=0)
    contador = Column(Integer, default=0)
    observaciones = Column(String(500))

    registro = relationship("RegistroBobinas", back_populates="filas")


class RegistroRotulado(Base):
    __tablename__ = "registro_rotulado"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20))
    turno = Column(String(20))
    maquina = Column(String(50))
    nombre_operario = Column(String(200))
    firma_data = Column(Text)
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pro_numero = Column(String(50), nullable=True)
    lote = Column(String(100), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    filas = relationship("FilaRotulado", back_populates="registro", cascade="all, delete-orphan")


class FilaRotulado(Base):
    __tablename__ = "filas_rotulado"

    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("registro_rotulado.id"))
    numero_fila = Column(Integer)
    hora = Column(String(30))
    fechado = Column(String(200))
    fechado_cumple = Column(String(5), default="SI")
    sellado_cumple = Column(String(5), default="SI")
    referencia = Column(String(200))

    registro = relationship("RegistroRotulado", back_populates="filas")


class RegistroPesos(Base):
    __tablename__ = "registro_pesos"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20))
    turno = Column(String(20))
    maquina = Column(String(50))
    referencia = Column(String(200))
    nombre_operario = Column(String(200))
    firma_data = Column(Text)
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pro_numero = Column(String(50), nullable=True)
    lote = Column(String(100), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    filas = relationship("FilaPeso", back_populates="registro", cascade="all, delete-orphan")


class FilaPeso(Base):
    __tablename__ = "filas_pesos"

    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("registro_pesos.id"))
    numero_fila = Column(Integer)
    hora = Column(String(30))
    muestra_1 = Column(Float)
    muestra_2 = Column(Float)
    muestra_3 = Column(Float)
    muestra_4 = Column(Float)
    muestra_5 = Column(Float)
    muestra_6 = Column(Float)
    muestra_7 = Column(Float)
    muestra_8 = Column(Float)
    muestra_9 = Column(Float)
    muestra_10 = Column(Float)
    muestra_11 = Column(Float)
    muestra_12 = Column(Float)
    muestra_13 = Column(Float)
    muestra_14 = Column(Float)
    muestra_15 = Column(Float)
    muestra_16 = Column(Float)
    muestra_17 = Column(Float)
    muestra_18 = Column(Float)
    muestra_19 = Column(Float)
    muestra_20 = Column(Float)
    muestra_21 = Column(Float)
    muestra_22 = Column(Float)
    muestra_23 = Column(Float)
    muestra_24 = Column(Float)
    muestra_25 = Column(Float)
    observaciones = Column(String(500))

    registro = relationship("RegistroPesos", back_populates="filas")


# ══════════════════════════════════════════════════════════════════════════════
# CONTROL DE PESO — ENFARDADORAS. Formato aparte del de Empacadoras: la
# enfardadora no tiene su propio código de máquina (usa la pareja de
# empacadoras de esa línea), pesa fardos completos (no unidades individuales)
# y solo necesita 6 muestras por hora, no 25.
# ══════════════════════════════════════════════════════════════════════════════
class RegistroPesoEnfardadora(Base):
    __tablename__ = "registro_peso_enfardadora"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20))
    turno = Column(String(20))
    enfardadora = Column(String(50))    # etiqueta legible, ej. "Enfardadora 1 (Maíz)"
    maquinas = Column(String(50))       # código crudo de la línea, ej. "1P-2Q"
    referencia = Column(String(50))     # ancho de fardo (código de bodega)
    nombre_operario = Column(String(200))
    firma_data = Column(Text)
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    pro_numero = Column(String(50), nullable=True)
    lote = Column(String(100), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())

    filas = relationship("FilaPesoEnfardadora", back_populates="registro", cascade="all, delete-orphan")


class FilaPesoEnfardadora(Base):
    __tablename__ = "filas_peso_enfardadora"

    id = Column(Integer, primary_key=True, index=True)
    registro_id = Column(Integer, ForeignKey("registro_peso_enfardadora.id"))
    numero_fila = Column(Integer)
    hora = Column(String(30))
    muestra_1 = Column(Float)
    muestra_2 = Column(Float)
    muestra_3 = Column(Float)
    muestra_4 = Column(Float)
    muestra_5 = Column(Float)
    muestra_6 = Column(Float)
    muestra_7 = Column(Float)
    muestra_8 = Column(Float)
    muestra_9 = Column(Float)
    muestra_10 = Column(Float)
    muestra_11 = Column(Float)
    muestra_12 = Column(Float)
    muestra_13 = Column(Float)
    muestra_14 = Column(Float)
    muestra_15 = Column(Float)
    observaciones = Column(String(500))

    registro = relationship("RegistroPesoEnfardadora", back_populates="filas")


# ══════════════════════════════════════════════════════════════════════════════
# MUESTREO DE CALIDAD — auditoría estadística para la ingeniera de calidad.
# Toma al azar N muestras YA REGISTRADAS en Control de Peso (de cualquier
# turno/máquina del día, para una referencia dada) y las guarda aparte, con
# su evaluación de cumple/no cumple y las observaciones de calidad — sin
# tocar ni depender de los registros originales de Pesos.
# ══════════════════════════════════════════════════════════════════════════════
class MuestreoCalidad(Base):
    __tablename__ = "muestreo_calidad"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20), nullable=False)             # día auditado (ambos turnos)
    referencia = Column(String(200), nullable=False)         # código o descripción de la referencia
    cantidad_solicitada = Column(Integer, nullable=False)     # cuántas pidió (ej. 98)
    cantidad_encontrada = Column(Integer, nullable=False)      # cuántas había disponibles en el pool
    generado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nombre_generado_por = Column(String(200))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("MuestraCalidadItem", back_populates="muestreo", cascade="all, delete-orphan")


class MuestraCalidadItem(Base):
    __tablename__ = "muestra_calidad_item"

    id = Column(Integer, primary_key=True, index=True)
    muestreo_id = Column(Integer, ForeignKey("muestreo_calidad.id"))
    numero_muestra = Column(Integer, nullable=False)          # 1..N, el orden dentro de este muestreo

    # De dónde salió esta muestra dentro de los registros de Pesos originales:
    turno_origen = Column(String(20))
    maquina_origen = Column(String(50))
    hora_origen = Column(String(30))
    fila_peso_id = Column(Integer, ForeignKey("filas_pesos.id"), nullable=True)
    posicion_muestra = Column(Integer)                          # cuál de las 6 columnas (1-6) era en el original

    valor_peso = Column(Float, nullable=False)
    cumple = Column(String(5))                                   # SI / NO — calculado automático al generar
    observaciones_calidad = Column(String(500))

    muestreo = relationship("MuestreoCalidad", back_populates="items")



# ─── USUARIOS ─────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════
# MANTENIMIENTO — migrado del plan de Excel (Empacadoras, Enfardadoras, Bandas/Sopladores)
# ══════════════════════════════════════════════════════════════════════════════

class PlanPreventivo(Base):
    """Catálogo de actividades preventivas (de las 3 hojas 'Plan Preventivo ...')."""
    __tablename__ = "plan_preventivo"

    id = Column(Integer, primary_key=True, index=True)
    linea = Column(String(30), nullable=False)          # EMPACADORAS | ENFARDADORAS | BANDAS_SOPLADORES
    seccion_componente = Column(String(300), nullable=False)
    actividad = Column(Text, nullable=False)
    tipo = Column(String(50))                            # Mecánico / Eléctrico / Neumático / etc.
    frecuencia = Column(String(50))                      # Diaria/Semanal/.../Anual (algunas incluyen aclaración, ej. "Anual (según desgaste)")
    responsable = Column(String(50))                      # Operario / Técnico Mtto / Electricista
    tiempo_min = Column(Integer)
    repuesto_insumo = Column(String(300))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class CronogramaMantenimiento(Base):
    """Cronograma vivo: una fila por máquina+sección (99 puntos de control).
    El estado (OK/Próximo/Vencido) y la próxima fecha se calculan en el backend
    a partir de ultima_ejecucion + la frecuencia — no se guardan, para que
    nunca queden desactualizados."""
    __tablename__ = "cronograma_mantenimiento"

    id = Column(Integer, primary_key=True, index=True)
    maquina = Column(String(30), nullable=False)          # EMPACA 1..9, ENFA 1..4, BANDAS, SOPLADORES
    seccion_componente = Column(String(300), nullable=False)
    frecuencia = Column(String(50))
    ultima_ejecucion = Column(String(20), nullable=True)   # 'YYYY-MM-DD'; null = nunca registrado
    observaciones = Column(Text)
    actualizado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class HistorialCorrectivo(Base):
    """Historial de mantenimientos correctivos (17 originales del inventario + nuevos)."""
    __tablename__ = "historial_correctivo"

    id = Column(Integer, primary_key=True, index=True)
    maquina = Column(String(30), nullable=False)
    equipo_componente = Column(String(300))
    fecha_mantenimiento = Column(String(20))               # 'YYYY-MM-DD'
    fecha_cambio = Column(String(20))
    mantenimiento_realizado = Column(Text)
    costo = Column(Float, nullable=True)
    estado_resultante = Column(String(10))                 # MALO / MEDIO / BUENO
    hubo_cambio = Column(String(5))                         # SI / NO
    prioridad = Column(String(10), nullable=True)           # CRITICA/ALTA/MEDIA/BAJA — solo en registros nuevos
    registrado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class SolicitudMantenimiento(Base):
    """Reporte puntual de un problema en una máquina, hecho por cualquier
    operario (no viene del cronograma preventivo). Alimenta la campanita de
    notificaciones del ingeniero, y al resolverse queda registrada también
    en el Historial Correctivo."""
    __tablename__ = "solicitud_mantenimiento"

    id = Column(Integer, primary_key=True, index=True)
    maquina = Column(String(30), nullable=False)
    descripcion_problema = Column(Text, nullable=False)
    prioridad = Column(String(10), default="MEDIA")          # CRITICA/ALTA/MEDIA/BAJA
    estado = Column(String(20), default="PENDIENTE")          # PENDIENTE / RESUELTO
    fecha_reporte = Column(String(20), nullable=False)        # 'YYYY-MM-DD'
    reportado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nombre_reportado_por = Column(String(200))

    fecha_resolucion = Column(String(20), nullable=True)
    resolucion_descripcion = Column(Text, nullable=True)      # qué se hizo para resolverlo
    resuelto_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    historial_correctivo_id = Column(Integer, ForeignKey("historial_correctivo.id"), nullable=True)  # queda enlazado al registro que se creó al resolver

    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class RepuestoCritico(Base):
    """Repuestos críticos por sección/componente (271 referencias del inventario)."""
    __tablename__ = "repuesto_critico"

    id = Column(Integer, primary_key=True, index=True)
    seccion = Column(String(200))
    componente = Column(String(300))
    referencia = Column(String(200), nullable=True)
    marca = Column(String(100), nullable=True)
    cantidad_instalada = Column(Integer, nullable=True)
    maquinas_aplica = Column(String(300))
    stock_minimo_sugerido = Column(Integer, nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ══════════════════════════════════════════════════════════════════════════════
# TRAZABILIDAD — Recepción de Materia Prima (trigo/maíz)
#
# ⚠️ Alcance real: esto registra lo que entra a la planta y a qué silo va, con
# su control de calidad. NO da trazabilidad exacta "esta bolsa vino de este
# camión" porque el sistema no rastrea la molienda (los silos pueden mezclar
# varios lotes). Da trazabilidad APROXIMADA por silo + ventana de fechas.
# ══════════════════════════════════════════════════════════════════════════════
class RecepcionMateriaPrima(Base):
    __tablename__ = "recepcion_materia_prima"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20), nullable=False)             # 'YYYY-MM-DD'
    tipo_grano = Column(String(10), nullable=False)         # TRIGO | MAIZ
    proveedor = Column(String(200), nullable=False)
    lote_proveedor = Column(String(100))                    # número/código de lote que trae el proveedor
    placa_vehiculo = Column(String(20), nullable=True)
    cantidad_kg = Column(Float, nullable=False)
    silo_destino = Column(String(100), nullable=False)

    # Control de calidad
    humedad_pct = Column(Float, nullable=True)
    impurezas_pct = Column(Float, nullable=True)
    peso_especifico = Column(Float, nullable=True)
    resultado_calidad = Column(String(20))                  # APROBADO | CONDICIONAL | RECHAZADO
    observaciones_calidad = Column(Text, nullable=True)

    registrado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nombre_registrado_por = Column(String(200))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ══════════════════════════════════════════════════════════════════════════════
# ESTIBAS — reemplaza la hoja de papel de la macro de Excel. Escaneada por el
# operario de montacargas de la cooperativa desde un QR fijo por máquina
# (no requiere login, ya que es personal externo).
# ══════════════════════════════════════════════════════════════════════════════
class RegistroEstiba(Base):
    __tablename__ = "registro_estiba"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20), nullable=False)
    turno = Column(String(20), nullable=False)
    maquina = Column(String(30), nullable=False)
    numero_estiva = Column(Integer, nullable=False)      # se reinicia por fecha+turno+máquina
    referencia_producto = Column(String(100))             # sugerida automáticamente desde Bobinas, editable
    cantidad_pacas = Column(Integer)
    plancha = Column(String(20))
    alto = Column(String(20))
    nombre_operario_montacargas = Column(String(200))     # personal de la cooperativa, texto libre (sin cuenta de usuario)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ══════════════════════════════════════════════════════════════════════════════
# AJUSTE DE INVENTARIO EN PLANTA — para sembrar el saldo real contado a mano
# (ej. al arrancar el sistema), o corregir el calculado si no cuadra con la
# realidad física. Desde la fecha del ajuste en adelante, el Kardex de Planta
# solo suma/resta movimientos NUEVOS sobre este saldo — no cuenta otra vez lo
# que ya pasó antes (para no duplicar).
# ══════════════════════════════════════════════════════════════════════════════
class AjustePlanta(Base):
    __tablename__ = "ajuste_planta"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), nullable=False)           # código de ReferenciaEmpaque
    fecha = Column(String(20), nullable=False)             # 'YYYY-MM-DD' — desde aquí en adelante aplica
    cantidad_kg = Column(Float, nullable=False)            # saldo real contado en planta en ese momento
    cantidad_bobinas = Column(Integer, nullable=True)      # saldo real contado en bobinas/rollos (opcional)
    observaciones = Column(Text, nullable=True)
    registrado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    cedula = Column(String(20), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    rol = Column(String(20), default="operario")
    maquinas_asignadas = Column(String(100), default="")
    activo = Column(String(5), default="SI")
    firma_imagen = Column(Text, nullable=True)  # firma escaneada (base64), se pega sola al guardar planillas
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ─── BODEGA — CATÁLOGO DE REFERENCIAS DE EMPAQUE ──────────────────────────────
class ReferenciaEmpaque(Base):
    """
    Catálogo maestro de referencias de empaque (trigo y maíz), migrado desde
    la pestaña CONTROL INV del Excel de bodega. El código coincide con el
    usado en SIGO (sistema contable de administración).
    """
    __tablename__ = "referencias_empaque"

    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(20), unique=True, nullable=False, index=True)
    descripcion = Column(String(200), nullable=False)
    categoria = Column(String(20))  # "TRIGO" | "MAIZ"
    promedio_bobina_kg = Column(Float, nullable=True)
    activo = Column(String(5), default="SI")
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ─── BODEGA — ORDEN DE SALIDA ─────────────────────────────────────────────────
class OrdenSalida(Base):
    """
    Orden de Salida digital: el documento que producción llena para pedir
    bobinas de empaque a la bodega (reemplaza el talonario en papel).
    Al crearse, genera automáticamente un MovimientoInventario tipo ENTREGA
    para que el saldo de bodega quede sincronizado.
    """
    __tablename__ = "orden_salida"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20))
    turno = Column(String(20))
    area_solicitante = Column(String(100), default="Producción")
    codigo_producto = Column(String(20), nullable=True)
    referencia_producto = Column(String(100))
    maquina = Column(String(50))
    cantidad_bobinas = Column(Integer, default=0)
    cantidad_kg = Column(Float, default=0)
    observaciones = Column(String(500))
    nombre_operario = Column(String(200))
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


# ─── BODEGA — LIBRO DE MOVIMIENTOS (reemplaza pestañas FORMULARIO + BASE) ─────
class MovimientoInventario(Base):
    """
    Ledger único de todos los movimientos que afectan el inventario de bodega:
    inventario inicial, compras (entradas de proveedor), entregas a producción,
    devoluciones, mercancía no apta y ajustes. Convención de signos igual a la
    columna M.KG del Excel: positivo = entra a bodega, negativo = sale de bodega.

    Toda Orden de Salida genera automáticamente un registro aquí (tipo ENTREGA,
    negativo). Los demás tipos se registran directamente desde este ledger.
    """
    __tablename__ = "movimientos_inventario"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20))
    tipo_operacion = Column(String(30))  # INVENTARIO_INICIAL | COMPRA | ENTREGA | DEVOLUCION | MERCANCIA_NO_APTA | AJUSTE
    codigo_producto = Column(String(20), index=True)
    referencia_producto = Column(String(200))
    cantidad_kg = Column(Float, default=0)
    cantidad_bobinas = Column(Integer, default=0)
    n_documento = Column(String(50))
    proveedor = Column(String(150))
    destino = Column(String(100))
    observaciones = Column(String(500))
    origen_orden_salida_id = Column(Integer, ForeignKey("orden_salida.id"), nullable=True)
    origen_pedido_id = Column(Integer, ForeignKey("pedidos_compra.id"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    nombre_usuario = Column(String(200))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ─── BODEGA — PEDIDOS DE COMPRA (reemplaza pestaña PEDIDOS) ───────────────────
class PedidoCompra(Base):
    __tablename__ = "pedidos_compra"

    id = Column(Integer, primary_key=True, index=True)
    numero_orden_compra = Column(String(50))
    fecha = Column(String(20))
    proveedor = Column(String(150))
    codigo_producto = Column(String(20), index=True)
    referencia_producto = Column(String(200))
    cantidad_pedida_kg = Column(Float, default=0)
    cantidad_recibida_kg = Column(Float, default=0)
    fecha_estimada = Column(String(20))
    precio_unitario = Column(Float, nullable=True)
    estado = Column(String(20), default="PENDIENTE")  # PENDIENTE | PARCIAL | COMPLETO
    observaciones = Column(String(500))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    actualizado_en = Column(DateTime(timezone=True), onupdate=func.now())


# ══════════════════════════════════════════════════════════════════════════════
# CONTROL E IMPUTACIÓN DE MERMAS — registro puntual de desperdicio a pie de
# máquina (bolsa rota, harina barrida, defecto de sellado, scrap de bobina),
# separado del % de desperdicio que ya calcula Bobinas — esto es para poder
# clasificar POR QUÉ se perdió material, no solo cuánto.
# ══════════════════════════════════════════════════════════════════════════════
class RegistroMerma(Base):
    __tablename__ = "registro_mermas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20), nullable=False)
    turno = Column(String(20), nullable=False)
    maquina = Column(String(50), nullable=False)
    referencia_producto = Column(String(200))
    proveedor_empaque = Column(String(150))
    tipo_merma = Column(String(30), nullable=False)   # BOLSA_ROTA | HARINA_BARRIDO | DEFECTO_SELLADO | SCRAP_BOBINA | OTRO
    cantidad = Column(Float, nullable=False)
    unidad_medida = Column(String(10), nullable=False)  # KG | UND
    causa_raiz = Column(String(255))
    observaciones = Column(String(500))
    nombre_operario = Column(String(200))
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())


# ══════════════════════════════════════════════════════════════════════════════
# PAROS DE MÁQUINA / OEE — cada paro se registra completo (hora de inicio y de
# fin ya conocidas, igual que el resto de formatos de este sistema, que se
# llenan después del hecho, no con un cronómetro en vivo). Si el paro requirió
# mantenimiento, se crea automáticamente una Solicitud de Mantenimiento
# enlazada, para que quede visible en la campanita de notificaciones.
# ══════════════════════════════════════════════════════════════════════════════
class RegistroParoMaquina(Base):
    __tablename__ = "registro_paros_maquina"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(String(20), nullable=False)
    turno = Column(String(20), nullable=False)
    maquina = Column(String(50), nullable=False)
    hora_inicio = Column(String(10), nullable=False)   # 'HH:MM'
    hora_fin = Column(String(10), nullable=False)       # 'HH:MM'
    duracion_minutos = Column(Float, nullable=False)
    categoria_paro = Column(String(30), nullable=False)  # MECANICO | ELECTRICO | FALTA_MATERIA_PRIMA | CAMBIO_FORMATO | LIMPIEZA | OTRO
    descripcion_motivo = Column(String(500))
    requirio_mantenimiento = Column(Boolean, default=False)
    solicitud_mantenimiento_id = Column(Integer, ForeignKey("solicitud_mantenimiento.id"), nullable=True)
    nombre_operario = Column(String(200))
    operario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())