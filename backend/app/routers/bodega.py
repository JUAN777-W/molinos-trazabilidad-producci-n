from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.models.models import (
    OrdenSalida, RegistroBobinas, Usuario, ReferenciaEmpaque,
    MovimientoInventario, PedidoCompra, AjustePlanta
)
from app.auth import get_current_user
from app.schemas.bodega_schemas import (
    OrdenSalidaCreate, OrdenSalidaOut, SugerenciaOut,
    ReconciliacionItem, ReconciliacionResumen, ReferenciaEmpaqueOut,
    MovimientoCreate, MovimientoOut, InventarioItem, InventarioPlantaItem,
    PedidoCompraCreate, PedidoCompraOut, RecepcionPedidoCreate,
    RendimientoItem, RendimientoResumen,
    AjustePlantaCreate, AjustePlantaOut,
)

router = APIRouter()


# ─── Permisos ──────────────────────────────────────────────────────────────────
# El rol "bodega" ya está soportado por el modelo Usuario (campo libre) -> el
# día que se cree un usuario con rol="bodega" desde el panel, automáticamente
# tendrá acceso a todo lo de este router sin tocar código.
def require_admin_o_bodega(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.rol not in ("admin", "bodega"):
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin o bodega.")
    return current_user


def _orden_to_out(o: OrdenSalida) -> OrdenSalidaOut:
    return OrdenSalidaOut(
        id=o.id, fecha=o.fecha or "", turno=o.turno or "",
        area_solicitante=o.area_solicitante or "Producción",
        codigo_producto=o.codigo_producto, referencia_producto=o.referencia_producto or "",
        cantidad_bobinas=o.cantidad_bobinas or 0,
        cantidad_kg=o.cantidad_kg or 0.0, observaciones=o.observaciones,
        nombre_operario=o.nombre_operario or "", creado_en=o.creado_en,
    )


def _mov_to_out(m: MovimientoInventario) -> MovimientoOut:
    return MovimientoOut(
        id=m.id, fecha=m.fecha or "", tipo_operacion=m.tipo_operacion or "",
        codigo_producto=m.codigo_producto or "", referencia_producto=m.referencia_producto or "",
        cantidad_kg=m.cantidad_kg or 0.0, cantidad_bobinas=m.cantidad_bobinas or 0,
        n_documento=m.n_documento, proveedor=m.proveedor, destino=m.destino,
        observaciones=m.observaciones, nombre_usuario=m.nombre_usuario or "",
        creado_en=m.creado_en,
    )


def _pedido_to_out(p: PedidoCompra) -> PedidoCompraOut:
    return PedidoCompraOut(
        id=p.id, numero_orden_compra=p.numero_orden_compra, fecha=p.fecha or "",
        proveedor=p.proveedor or "", codigo_producto=p.codigo_producto or "",
        referencia_producto=p.referencia_producto or "",
        cantidad_pedida_kg=p.cantidad_pedida_kg or 0.0,
        cantidad_recibida_kg=p.cantidad_recibida_kg or 0.0,
        fecha_estimada=p.fecha_estimada, precio_unitario=p.precio_unitario,
        estado=p.estado or "PENDIENTE", observaciones=p.observaciones, creado_en=p.creado_en,
    )


# ══════════════════════════════════════════════════════════════════════════════
# CATÁLOGO DE REFERENCIAS
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/referencias", response_model=List[ReferenciaEmpaqueOut])
def listar_referencias(
    categoria: Optional[str] = Query(None, description="TRIGO o MAIZ"),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.activo == "SI")
    if categoria:
        q = q.filter(ReferenciaEmpaque.categoria == categoria.upper())
    referencias = q.order_by(ReferenciaEmpaque.descripcion).all()
    return [
        ReferenciaEmpaqueOut(
            codigo=r.codigo, descripcion=r.descripcion,
            categoria=r.categoria, promedio_bobina_kg=r.promedio_bobina_kg,
        )
        for r in referencias
    ]


# ══════════════════════════════════════════════════════════════════════════════
# ORDEN DE SALIDA
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/ordenes", response_model=OrdenSalidaOut, status_code=201)
def crear_orden(
    payload: OrdenSalidaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    orden = OrdenSalida(
        fecha=payload.fecha, turno=payload.turno, area_solicitante=payload.area_solicitante,
        codigo_producto=payload.codigo_producto, referencia_producto=payload.referencia_producto,
        cantidad_bobinas=payload.cantidad_bobinas,
        cantidad_kg=payload.cantidad_kg, observaciones=payload.observaciones,
        nombre_operario=current_user.nombre, operario_id=current_user.id,
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)

    # Sincroniza automáticamente el ledger de inventario: la entrega SALE de bodega (signo negativo)
    if payload.codigo_producto:
        mov = MovimientoInventario(
            fecha=payload.fecha, tipo_operacion="ENTREGA",
            codigo_producto=payload.codigo_producto, referencia_producto=payload.referencia_producto,
            cantidad_kg=-abs(payload.cantidad_kg), cantidad_bobinas=-abs(payload.cantidad_bobinas),
            destino=payload.area_solicitante, observaciones=f"Orden de Salida #{orden.id}",
            origen_orden_salida_id=orden.id, usuario_id=current_user.id, nombre_usuario=current_user.nombre,
        )
        db.add(mov)
        db.commit()

    return _orden_to_out(orden)


@router.get("/ordenes", response_model=List[OrdenSalidaOut])
def listar_ordenes(
    fecha: Optional[str] = Query(None),
    referencia: Optional[str] = Query(None), db: Session = Depends(get_db),
    _=Depends(require_admin_o_bodega),
):
    q = db.query(OrdenSalida)
    if fecha: q = q.filter(OrdenSalida.fecha == fecha)
    if referencia: q = q.filter(OrdenSalida.referencia_producto == referencia)
    return [_orden_to_out(o) for o in q.order_by(OrdenSalida.id.desc()).all()]


@router.get("/ordenes/{orden_id}", response_model=OrdenSalidaOut)
def obtener_orden(orden_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    orden = db.query(OrdenSalida).filter(OrdenSalida.id == orden_id).first()
    if not orden:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    return _orden_to_out(orden)


# ══════════════════════════════════════════════════════════════════════════════
# SUGERENCIA DE PEDIDO
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/sugerencia", response_model=SugerenciaOut)
def sugerencia_pedido(
    referencia: str = Query(...), codigo_producto: Optional[str] = Query(None),
    turnos_atras: int = Query(10, ge=1, le=60),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    # Bobinas guarda el código (no el texto descriptivo) en referencia_producto,
    # así que si tenemos el código, buscamos por ahí; si no, caemos al texto
    # por compatibilidad con registros antiguos.
    clave_busqueda = codigo_producto or referencia
    q = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_producto == clave_busqueda)
    registros = q.order_by(RegistroBobinas.id.desc()).limit(turnos_atras).all()

    referencia_catalogo = None
    if codigo_producto:
        referencia_catalogo = db.query(ReferenciaEmpaque).filter(
            ReferenciaEmpaque.codigo == codigo_producto
        ).first()

    if not registros:
        if referencia_catalogo and referencia_catalogo.promedio_bobina_kg:
            return SugerenciaOut(
                referencia_producto=referencia, kg_promedio_historico=0.0,
                kg_sugerido=0.0, bobinas_sugeridas=0, turnos_analizados=0,
                fuente_promedio_bobina="catalogo_bodega",
                nota=f"Sin historial de producción todavía. Según bodega, cada bobina de esta "
                     f"referencia pesa en promedio {referencia_catalogo.promedio_bobina_kg} kg.",
            )
        return SugerenciaOut(
            referencia_producto=referencia, kg_promedio_historico=0.0,
            kg_sugerido=0.0, bobinas_sugeridas=0, turnos_analizados=0,
            fuente_promedio_bobina="sin_dato",
            nota="Sin historial suficiente todavía. Pide según criterio del supervisor.",
        )

    kg_por_turno, pesos_montados = [], []
    for r in registros:
        kg_por_turno.append(sum(f.consumido or 0 for f in r.filas))
        for f in r.filas:
            if f.peso_montar and f.peso_montar > 0:
                pesos_montados.append(f.peso_montar)

    kg_promedio = round(sum(kg_por_turno) / len(kg_por_turno), 2) if kg_por_turno else 0.0
    kg_sugerido = round(kg_promedio * 1.05, 2)

    fuente = "historico_produccion"
    if pesos_montados:
        peso_promedio_bobina = round(sum(pesos_montados) / len(pesos_montados), 2)
    elif referencia_catalogo and referencia_catalogo.promedio_bobina_kg:
        peso_promedio_bobina = referencia_catalogo.promedio_bobina_kg
        fuente = "catalogo_bodega"
    else:
        peso_promedio_bobina = 0.0
        fuente = "sin_dato"

    bobinas_sugeridas = int((kg_sugerido / peso_promedio_bobina) + 0.999) if peso_promedio_bobina > 0 else 0

    return SugerenciaOut(
        referencia_producto=referencia, kg_promedio_historico=kg_promedio,
        kg_sugerido=kg_sugerido, bobinas_sugeridas=bobinas_sugeridas, turnos_analizados=len(registros),
        fuente_promedio_bobina=fuente,
        nota=f"Calculado sobre los últimos {len(registros)} turnos registrados para esta referencia.",
    )


# ══════════════════════════════════════════════════════════════════════════════
# RECONCILIACIÓN
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/reconciliacion", response_model=ReconciliacionResumen)
def reconciliacion(fecha: str = Query(...), db: Session = Depends(get_db), _=Depends(require_admin_o_bodega)):
    ordenes = db.query(OrdenSalida).filter(OrdenSalida.fecha == fecha).all()
    items: List[ReconciliacionItem] = []
    total_kg_pedido, total_kg_consumido = 0.0, 0.0

    for o in ordenes:
        # Ya no se cruza por máquina: la Orden de Salida no pregunta por máquina
        # específica (para evitar el problema de las parejas de máquinas, donde
        # producción guarda "9X-8S" pero bodega solo pediría "9X"). El cruce
        # ahora es por fecha + turno + CÓDIGO (no por el texto descriptivo):
        # el formulario de Bobinas guarda el código de bodega (ej. "10-20-8")
        # en su campo referencia_producto, mientras que la Orden de Salida
        # guarda la descripción legible en el suyo — por eso se compara contra
        # o.codigo_producto, que es el mismo código que usa Bobinas.
        clave_match = o.codigo_producto or o.referencia_producto
        registros = db.query(RegistroBobinas).filter(
            RegistroBobinas.fecha == o.fecha,
            RegistroBobinas.turno == o.turno, RegistroBobinas.referencia_producto == clave_match,
        ).all()

        if not registros:
            items.append(ReconciliacionItem(
                orden_id=o.id, fecha=o.fecha, turno=o.turno,
                referencia_producto=o.referencia_producto, kg_pedido=o.cantidad_kg,
                bobinas_pedidas=o.cantidad_bobinas, kg_consumido_real=0.0,
                diferencia_kg=o.cantidad_kg, diferencia_pct=100.0, estado="SIN_REGISTRO_PRODUCCION",
            ))
            total_kg_pedido += o.cantidad_kg
            continue

        kg_consumido = sum(sum(f.consumido or 0 for f in r.filas) for r in registros)
        diferencia = round(o.cantidad_kg - kg_consumido, 2)
        diferencia_pct = round((diferencia / o.cantidad_kg * 100), 1) if o.cantidad_kg > 0 else 0.0
        estado = "AJUSTADO" if abs(diferencia_pct) <= 5 else ("SOBRANTE" if diferencia > 0 else "FALTANTE")

        items.append(ReconciliacionItem(
            orden_id=o.id, fecha=o.fecha, turno=o.turno,
            referencia_producto=o.referencia_producto, kg_pedido=o.cantidad_kg,
            bobinas_pedidas=o.cantidad_bobinas, kg_consumido_real=round(kg_consumido, 2),
            diferencia_kg=diferencia, diferencia_pct=diferencia_pct, estado=estado,
        ))
        total_kg_pedido += o.cantidad_kg
        total_kg_consumido += kg_consumido

    return ReconciliacionResumen(
        fecha=fecha, total_ordenes=len(ordenes), total_kg_pedido=round(total_kg_pedido, 2),
        total_kg_consumido=round(total_kg_consumido, 2),
        diferencia_total_kg=round(total_kg_pedido - total_kg_consumido, 2), items=items,
    )


# ══════════════════════════════════════════════════════════════════════════════
# MOVIMIENTOS DE INVENTARIO (compras, devoluciones, mercancía no apta, ajustes)
# Reemplaza las pestañas FORMULARIO + BASE del Excel.
# ══════════════════════════════════════════════════════════════════════════════
TIPOS_MOVIMIENTO_MANUAL = {"COMPRA", "DEVOLUCION", "MERCANCIA_NO_APTA", "AJUSTE", "INVENTARIO_INICIAL"}

# Signo según tipo: compra e inventario inicial SUMAN a bodega; devolución SUMA
# (vuelve a bodega); mercancía no apta RESTA (sale del inventario disponible);
# ajuste puede ser + o -, se respeta el signo que el usuario ingrese.
SIGNO_POSITIVO = {"COMPRA", "DEVOLUCION", "INVENTARIO_INICIAL"}
SIGNO_NEGATIVO = {"MERCANCIA_NO_APTA"}


@router.post("/movimientos", response_model=MovimientoOut, status_code=201)
def crear_movimiento(
    payload: MovimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if payload.tipo_operacion not in TIPOS_MOVIMIENTO_MANUAL:
        raise HTTPException(
            status_code=400,
            detail=f"tipo_operacion debe ser uno de: {', '.join(sorted(TIPOS_MOVIMIENTO_MANUAL))}",
        )

    kg = abs(payload.cantidad_kg)
    bobinas = abs(payload.cantidad_bobinas)
    if payload.tipo_operacion in SIGNO_NEGATIVO:
        kg, bobinas = -kg, -bobinas
    elif payload.tipo_operacion == "AJUSTE":
        kg, bobinas = payload.cantidad_kg, payload.cantidad_bobinas  # respeta el signo tal cual lo ingresen

    mov = MovimientoInventario(
        fecha=payload.fecha, tipo_operacion=payload.tipo_operacion,
        codigo_producto=payload.codigo_producto, referencia_producto=payload.referencia_producto,
        cantidad_kg=kg, cantidad_bobinas=bobinas, n_documento=payload.n_documento,
        proveedor=payload.proveedor, destino=payload.destino, observaciones=payload.observaciones,
        usuario_id=current_user.id, nombre_usuario=current_user.nombre,
    )
    db.add(mov)
    db.commit()
    db.refresh(mov)
    return _mov_to_out(mov)


@router.get("/movimientos", response_model=List[MovimientoOut])
def listar_movimientos(
    fecha: Optional[str] = Query(None), tipo_operacion: Optional[str] = Query(None),
    codigo_producto: Optional[str] = Query(None), limite: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db), _=Depends(require_admin_o_bodega),
):
    q = db.query(MovimientoInventario)
    if fecha: q = q.filter(MovimientoInventario.fecha == fecha)
    if tipo_operacion: q = q.filter(MovimientoInventario.tipo_operacion == tipo_operacion)
    if codigo_producto: q = q.filter(MovimientoInventario.codigo_producto == codigo_producto)
    movimientos = q.order_by(MovimientoInventario.id.desc()).limit(limite).all()
    return [_mov_to_out(m) for m in movimientos]


# ══════════════════════════════════════════════════════════════════════════════
# CONTROL DE INVENTARIO (calculado en tiempo real, reemplaza pestaña CONTROL INV)
# ══════════════════════════════════════════════════════════════════════════════
def _calcular_inventario_items(db: Session, categoria: Optional[str] = None) -> List[InventarioItem]:
    q = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.activo == "SI")
    if categoria:
        q = q.filter(ReferenciaEmpaque.categoria == categoria.upper())
    referencias = q.order_by(ReferenciaEmpaque.descripcion).all()

    hoy = date.today()
    hace_90_dias = (hoy - timedelta(days=90)).strftime('%Y-%m-%d')

    resultado: List[InventarioItem] = []
    for r in referencias:
        movimientos = db.query(MovimientoInventario).filter(
            MovimientoInventario.codigo_producto == r.codigo
        ).all()
        saldo_kg = sum(m.cantidad_kg or 0 for m in movimientos)
        saldo_bobinas = sum(m.cantidad_bobinas or 0 for m in movimientos)

        entregas_90d = [
            abs(m.cantidad_kg) for m in movimientos
            if m.tipo_operacion == "ENTREGA" and (m.fecha or "") >= hace_90_dias
        ]
        consumo_promedio_mensual = round(sum(entregas_90d) / 3, 2) if entregas_90d else 0.0

        cobertura_dias = None
        estado_cobertura = "SIN_CONSUMO"
        if consumo_promedio_mensual > 0:
            cobertura_dias = round(saldo_kg / (consumo_promedio_mensual / 30), 1)
            if cobertura_dias < 15:
                estado_cobertura = "CRITICO"
            elif cobertura_dias < 30:
                estado_cobertura = "BAJO"
            else:
                estado_cobertura = "OK"
        elif saldo_kg > 0:
            estado_cobertura = "SIN_CONSUMO"

        pedidos_pendientes = db.query(PedidoCompra).filter(
            PedidoCompra.codigo_producto == r.codigo, PedidoCompra.estado != "COMPLETO"
        ).all()
        pedidos_pendientes_kg = round(
            sum((p.cantidad_pedida_kg or 0) - (p.cantidad_recibida_kg or 0) for p in pedidos_pendientes), 2
        )
        fechas_estimadas = [p.fecha_estimada for p in pedidos_pendientes if p.fecha_estimada]
        proxima_entrega_fecha = min(fechas_estimadas) if fechas_estimadas else None

        resultado.append(InventarioItem(
            codigo=r.codigo, descripcion=r.descripcion, categoria=r.categoria,
            saldo_kg=round(saldo_kg, 2), saldo_bobinas=int(saldo_bobinas),
            consumo_promedio_mensual_kg=consumo_promedio_mensual, cobertura_dias=cobertura_dias,
            estado_cobertura=estado_cobertura, pedidos_pendientes_kg=pedidos_pendientes_kg,
            proxima_entrega_fecha=proxima_entrega_fecha,
        ))

    return resultado


@router.get("/inventario", response_model=List[InventarioItem])
def control_inventario(
    categoria: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin_o_bodega),
):
    return _calcular_inventario_items(db, categoria)


# ── Alertas de inventario: referencias en cobertura crítica o baja ───────────
# Pensado para mostrarse en el Dashboard principal, de un vistazo para gerencia.
@router.get("/alertas-inventario", response_model=List[InventarioItem])
def alertas_inventario(
    db: Session = Depends(get_db),
    _=Depends(require_admin_o_bodega),
):
    items = _calcular_inventario_items(db)
    criticas = [i for i in items if i.estado_cobertura in ("CRITICO", "BAJO")]
    # Más urgente primero: críticos antes que bajos, y dentro de cada grupo, menor cobertura primero
    criticas.sort(key=lambda i: (0 if i.estado_cobertura == "CRITICO" else 1, i.cobertura_dias if i.cobertura_dias is not None else 9999))
    return criticas


# ══════════════════════════════════════════════════════════════════════════════
# KARDEX DE PLANTA — lo que hay FÍSICAMENTE en producción, no en bodega.
#
# Saldo en planta = Entregado (OrdenSalida) − Consumido real (RegistroBobinas)
#                    − Devuelto a bodega (MovimientoInventario tipo DEVOLUCION)
#
# No requiere ninguna tabla nueva: se calcula a partir de datos que ya existen.
# Pensado para que, al recibir una nueva Orden de Salida, el encargado de
# bodega vea de inmediato si producción ya tiene suficiente en planta antes
# de despachar más — así se evita la acumulación de rollos de más en planta.
# ══════════════════════════════════════════════════════════════════════════════
def _consumido_planta_por_codigo(db: Session, codigo: str, fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None) -> float:
    """Kg consumidos de un código en un rango de fechas (ambos límites
    opcionales, inclusive) — suma Empacadora A/B (por referencia_producto) y
    Enfardadora (por referencia_enfardadora) por separado, sin mezclarlas."""
    q_prod = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_producto == codigo)
    if fecha_desde:
        q_prod = q_prod.filter(RegistroBobinas.fecha >= fecha_desde)
    if fecha_hasta:
        q_prod = q_prod.filter(RegistroBobinas.fecha <= fecha_hasta)
    kg_prod = sum(
        sum(f.consumido or 0 for f in reg.filas if f.maquina_grupo in ('A', 'B')) for reg in q_prod.all()
    )

    q_enf = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_enfardadora == codigo)
    if fecha_desde:
        q_enf = q_enf.filter(RegistroBobinas.fecha >= fecha_desde)
    if fecha_hasta:
        q_enf = q_enf.filter(RegistroBobinas.fecha <= fecha_hasta)
    kg_enf = sum(
        sum(f.consumido or 0 for f in reg.filas if f.maquina_grupo == 'ENF') for reg in q_enf.all()
    )

    return kg_prod + kg_enf


def _calcular_inventario_planta(db: Session, dias_consumo_promedio: int = 30) -> List[InventarioPlantaItem]:
    referencias = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.activo == "SI").order_by(ReferenciaEmpaque.descripcion).all()
    hoy = date.today()
    hace_n_dias = (hoy - timedelta(days=dias_consumo_promedio)).strftime('%Y-%m-%d')

    resultado: List[InventarioPlantaItem] = []
    for r in referencias:
        # Si hay un ajuste manual (conteo físico) para esta referencia, se usa
        # como punto de partida — solo se cuentan movimientos DESPUÉS de esa
        # fecha, para no duplicar lo que el conteo físico ya reflejaba.
        ultimo_ajuste = db.query(AjustePlanta).filter(
            AjustePlanta.codigo == r.codigo
        ).order_by(AjustePlanta.fecha.desc(), AjustePlanta.id.desc()).first()

        fecha_desde = ultimo_ajuste.fecha if ultimo_ajuste else None
        saldo_base = ultimo_ajuste.cantidad_kg if ultimo_ajuste else 0.0
        saldo_base_bobinas = (ultimo_ajuste.cantidad_bobinas or 0) if ultimo_ajuste else 0

        # Entregado (solo después del ajuste, si existe)
        q_entregado = db.query(OrdenSalida).filter(OrdenSalida.codigo_producto == r.codigo)
        if fecha_desde:
            q_entregado = q_entregado.filter(OrdenSalida.fecha >= fecha_desde)
        ordenes_entregadas = q_entregado.all()
        total_entregado = sum(o.cantidad_kg or 0 for o in ordenes_entregadas)
        total_entregado_bobinas = sum(o.cantidad_bobinas or 0 for o in ordenes_entregadas)

        # Consumido real (solo después del ajuste, si existe) — cada fila de
        # Bobinas con peso_montar > 0 representa una bobina física que se montó.
        #
        # OJO: Empacadora A/B y Enfardadora consumen materiales DISTINTOS en el
        # mismo turno — el producto final (referencia_producto) en A/B, y el
        # ancho de fardo (referencia_enfardadora) en ENF. Por eso se buscan por
        # separado y solo se suman las filas del grupo de máquina que de verdad
        # corresponde a esta referencia, para no mezclar consumo de una
        # referencia de fardo con el de la harina empacada, ni al revés.
        q_registros_prod = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_producto == r.codigo)
        if fecha_desde:
            q_registros_prod = q_registros_prod.filter(RegistroBobinas.fecha >= fecha_desde)
        registros_prod = q_registros_prod.all()
        consumido_empacadoras = sum(
            sum(f.consumido or 0 for f in reg.filas if f.maquina_grupo in ('A', 'B')) for reg in registros_prod
        )
        bobinas_empacadoras = sum(
            sum(1 for f in reg.filas if f.maquina_grupo in ('A', 'B') and f.peso_montar and f.peso_montar > 0)
            for reg in registros_prod
        )

        q_registros_enf = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_enfardadora == r.codigo)
        if fecha_desde:
            q_registros_enf = q_registros_enf.filter(RegistroBobinas.fecha >= fecha_desde)
        registros_enf = q_registros_enf.all()
        consumido_enfardadora = sum(
            sum(f.consumido or 0 for f in reg.filas if f.maquina_grupo == 'ENF') for reg in registros_enf
        )
        bobinas_enfardadora = sum(
            sum(1 for f in reg.filas if f.maquina_grupo == 'ENF' and f.peso_montar and f.peso_montar > 0)
            for reg in registros_enf
        )

        total_consumido = consumido_empacadoras + consumido_enfardadora
        total_consumido_bobinas = bobinas_empacadoras + bobinas_enfardadora

        # Devuelto a bodega (solo después del ajuste, si existe)
        q_devoluciones = db.query(MovimientoInventario).filter(
            MovimientoInventario.codigo_producto == r.codigo,
            MovimientoInventario.tipo_operacion == "DEVOLUCION",
        )
        if fecha_desde:
            q_devoluciones = q_devoluciones.filter(MovimientoInventario.fecha >= fecha_desde)
        devoluciones = q_devoluciones.all()
        total_devuelto = sum(abs(m.cantidad_kg or 0) for m in devoluciones)
        total_devuelto_bobinas = sum(abs(m.cantidad_bobinas or 0) for m in devoluciones)

        saldo_planta = round(saldo_base + total_entregado - total_consumido - total_devuelto, 2)
        saldo_planta_bobinas = saldo_base_bobinas + total_entregado_bobinas - total_consumido_bobinas - total_devuelto_bobinas

        # Consumo promedio diario reciente (para cobertura) — se calcula
        # siempre sobre el histórico real completo, sin importar el ajuste,
        # y de nuevo separando Empacadoras (por referencia_producto) de
        # Enfardadora (por referencia_enfardadora).
        registros_prod_todos = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_producto == r.codigo).all()
        registros_prod_recientes = [reg for reg in registros_prod_todos if (reg.fecha or "") >= hace_n_dias]
        consumo_reciente_prod = sum(
            sum(f.consumido or 0 for f in reg.filas if f.maquina_grupo in ('A', 'B')) for reg in registros_prod_recientes
        )

        registros_enf_todos = db.query(RegistroBobinas).filter(RegistroBobinas.referencia_enfardadora == r.codigo).all()
        registros_enf_recientes = [reg for reg in registros_enf_todos if (reg.fecha or "") >= hace_n_dias]
        consumo_reciente_enf = sum(
            sum(f.consumido or 0 for f in reg.filas if f.maquina_grupo == 'ENF') for reg in registros_enf_recientes
        )

        consumo_reciente = consumo_reciente_prod + consumo_reciente_enf
        consumo_promedio_diario = round(consumo_reciente / dias_consumo_promedio, 2) if consumo_reciente > 0 else 0.0

        cobertura_dias = None
        estado = "SIN_DATO"
        if consumo_promedio_diario > 0:
            cobertura_dias = round(saldo_planta / consumo_promedio_diario, 1)
            if cobertura_dias >= 3:
                estado = "SOBRA"
            elif cobertura_dias >= 1:
                estado = "OK"
            else:
                estado = "BAJO"
        elif saldo_planta > 0:
            estado = "SOBRA"

        hoy_str = hoy.strftime('%Y-%m-%d')
        primer_dia_mes_str = hoy.replace(day=1).strftime('%Y-%m-%d')
        consumido_hoy = round(_consumido_planta_por_codigo(db, r.codigo, fecha_desde=hoy_str, fecha_hasta=hoy_str), 2)
        consumido_mes = round(_consumido_planta_por_codigo(db, r.codigo, fecha_desde=primer_dia_mes_str, fecha_hasta=hoy_str), 2)

        resultado.append(InventarioPlantaItem(
            codigo=r.codigo, descripcion=r.descripcion, categoria=r.categoria,
            total_entregado_kg=round(total_entregado, 2), total_consumido_kg=round(total_consumido, 2),
            total_devuelto_kg=round(total_devuelto, 2), saldo_planta_kg=saldo_planta,
            total_entregado_bobinas=total_entregado_bobinas, total_consumido_bobinas=total_consumido_bobinas,
            total_devuelto_bobinas=total_devuelto_bobinas, saldo_planta_bobinas=saldo_planta_bobinas,
            consumido_hoy_kg=consumido_hoy, consumido_mes_kg=consumido_mes,
            consumo_promedio_diario_kg=consumo_promedio_diario, cobertura_dias_planta=cobertura_dias,
            estado_cobertura=estado, tiene_ajuste_manual=(ultimo_ajuste is not None),
        ))

    return resultado

@router.post("/inventario-planta/ajuste", response_model=AjustePlantaOut)
def crear_ajuste_planta(
    payload: AjustePlantaCreate,
    db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user),
):
    """Registra un conteo físico manual del saldo en planta — desde esta
    fecha en adelante, el Kardex de Planta parte de este número, no de cero."""
    ajuste = AjustePlanta(**payload.model_dump(), registrado_por_id=current_user.id)
    db.add(ajuste)
    db.commit()
    db.refresh(ajuste)
    return ajuste


@router.get("/inventario-planta", response_model=List[InventarioPlantaItem])
def inventario_planta(
    categoria: Optional[str] = Query(None),
    solo_con_saldo: bool = Query(False, description="Si es true, solo muestra referencias con saldo > 0 en planta"),
    db: Session = Depends(get_db),
    _=Depends(require_admin_o_bodega),
):
    items = _calcular_inventario_planta(db)
    if categoria:
        items = [i for i in items if i.categoria == categoria.upper()]
    if solo_con_saldo:
        items = [i for i in items if i.saldo_planta_kg > 0]
    return items


# Consulta puntual de una sola referencia — pensada para mostrarse en línea al
# seleccionar la referencia en el formulario de Orden de Salida, así quien
# despacha ve de inmediato cuánto hay ya en planta antes de aprobar el envío.
@router.get("/inventario-planta/{codigo}", response_model=InventarioPlantaItem)
def inventario_planta_por_codigo(
    codigo: str,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    referencia = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.codigo == codigo).first()
    if not referencia:
        raise HTTPException(status_code=404, detail="Referencia no encontrada")
    items = _calcular_inventario_planta(db)
    item = next((i for i in items if i.codigo == codigo), None)
    if not item:
        raise HTTPException(status_code=404, detail="No se pudo calcular el inventario de planta")
    return item


# ══════════════════════════════════════════════════════════════════════════════
# PEDIDOS DE COMPRA (reemplaza pestaña PEDIDOS)
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/pedidos", response_model=PedidoCompraOut, status_code=201)
def crear_pedido(
    payload: PedidoCompraCreate, db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    pedido = PedidoCompra(
        numero_orden_compra=payload.numero_orden_compra, fecha=payload.fecha,
        proveedor=payload.proveedor, codigo_producto=payload.codigo_producto,
        referencia_producto=payload.referencia_producto, cantidad_pedida_kg=payload.cantidad_pedida_kg,
        cantidad_recibida_kg=0.0, fecha_estimada=payload.fecha_estimada,
        precio_unitario=payload.precio_unitario, estado="PENDIENTE",
        observaciones=payload.observaciones, usuario_id=current_user.id,
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)
    return _pedido_to_out(pedido)


@router.get("/pedidos", response_model=List[PedidoCompraOut])
def listar_pedidos(
    estado: Optional[str] = Query(None), codigo_producto: Optional[str] = Query(None),
    db: Session = Depends(get_db), _=Depends(require_admin_o_bodega),
):
    q = db.query(PedidoCompra)
    if estado: q = q.filter(PedidoCompra.estado == estado.upper())
    if codigo_producto: q = q.filter(PedidoCompra.codigo_producto == codigo_producto)
    pedidos = q.order_by(PedidoCompra.id.desc()).all()
    return [_pedido_to_out(p) for p in pedidos]


@router.post("/pedidos/{pedido_id}/recepcion", response_model=PedidoCompraOut)
def registrar_recepcion(
    pedido_id: int, payload: RecepcionPedidoCreate, db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    pedido = db.query(PedidoCompra).filter(PedidoCompra.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado")

    pedido.cantidad_recibida_kg = (pedido.cantidad_recibida_kg or 0) + payload.cantidad_recibida_kg
    if pedido.cantidad_recibida_kg >= pedido.cantidad_pedida_kg:
        pedido.estado = "COMPLETO"
    elif pedido.cantidad_recibida_kg > 0:
        pedido.estado = "PARCIAL"

    mov = MovimientoInventario(
        fecha=date.today().strftime('%Y-%m-%d'), tipo_operacion="COMPRA",
        codigo_producto=pedido.codigo_producto, referencia_producto=pedido.referencia_producto,
        cantidad_kg=abs(payload.cantidad_recibida_kg), cantidad_bobinas=0,
        n_documento=payload.n_documento or pedido.numero_orden_compra, proveedor=pedido.proveedor,
        observaciones=payload.observaciones or f"Recepción de pedido #{pedido.id}",
        origen_pedido_id=pedido.id, usuario_id=current_user.id, nombre_usuario=current_user.nombre,
    )
    db.add(mov)
    db.commit()
    db.refresh(pedido)
    return _pedido_to_out(pedido)


# ══════════════════════════════════════════════════════════════════════════════
# INFORME DE RENDIMIENTOS MENSUAL (reemplaza pestaña RENDIMIENTOS)
# ══════════════════════════════════════════════════════════════════════════════
def _mes_anterior(mes: str) -> str:
    anio, m = map(int, mes.split('-'))
    if m == 1:
        return f"{anio - 1}-12"
    return f"{anio}-{m - 1:02d}"


def _calcular_rendimiento_mes(db: Session, mes: str):
    registros = db.query(RegistroBobinas).filter(RegistroBobinas.fecha.like(f"{mes}%")).all()
    grupos: dict = {}
    for r in registros:
        ref = r.referencia_producto or "Sin referencia"
        g = grupos.setdefault(ref, {"kg": 0.0, "unidades": 0, "desperdicio": 0.0, "turnos": 0})
        g["turnos"] += 1
        g["desperdicio"] += r.peso_desperdicio or 0
        for f in r.filas:
            g["kg"] += f.consumido or 0
            g["unidades"] += f.contador or 0
    return grupos


@router.get("/rendimientos", response_model=RendimientoResumen)
def informe_rendimientos(
    mes: str = Query(..., description="Formato YYYY-MM, ej. 2026-07"),
    db: Session = Depends(get_db),
    _=Depends(require_admin_o_bodega),
):
    grupos = _calcular_rendimiento_mes(db, mes)
    grupos_mes_anterior = _calcular_rendimiento_mes(db, _mes_anterior(mes))

    items: List[RendimientoItem] = []
    total_kg, total_unid, total_desp = 0.0, 0, 0.0

    for ref, g in sorted(grupos.items(), key=lambda x: x[1]["kg"], reverse=True):
        kg = round(g["kg"], 2)
        unidades = g["unidades"]
        desperdicio = round(g["desperdicio"], 2)
        total_producido = kg + desperdicio
        pct_desperdicio = round((desperdicio / total_producido * 100), 2) if total_producido > 0 else 0.0
        rendimiento = round(unidades / kg, 4) if kg > 0 else 0.0

        items.append(RendimientoItem(
            referencia_producto=ref, kg_consumido=kg, unidades_producidas=unidades,
            rendimiento_unid_por_kg=rendimiento, desperdicio_kg=desperdicio,
            pct_desperdicio=pct_desperdicio, turnos=g["turnos"],
        ))
        total_kg += kg
        total_unid += unidades
        total_desp += desperdicio

    kg_mes_anterior = sum(g["kg"] for g in grupos_mes_anterior.values())
    variacion_pct = round(((total_kg - kg_mes_anterior) / kg_mes_anterior * 100), 1) if kg_mes_anterior > 0 else 0.0
    total_producido_global = total_kg + total_desp
    pct_desperdicio_promedio = round((total_desp / total_producido_global * 100), 2) if total_producido_global > 0 else 0.0

    return RendimientoResumen(
        mes=mes, total_kg_consumido=round(total_kg, 2), total_unidades_producidas=total_unid,
        total_desperdicio_kg=round(total_desp, 2), pct_desperdicio_promedio=pct_desperdicio_promedio,
        variacion_kg_vs_mes_anterior_pct=variacion_pct, items=items,
    )