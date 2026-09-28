from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.models import (
    RegistroParoMaquina, RegistroBobinas, SolicitudMantenimiento, Usuario,
)
from app.schemas.oee_schemas import (
    RegistroParoCreate, RegistroParoOut, OEEResumenOut,
    DisponibilidadMaquinaItem, ParoPorCategoriaItem,
)
from app.auth import get_current_user, require_admin
from app.routers.dashboard import _pct_desperdicio
from app.routers.informe import META_KG_MAIZ, META_PACAS_TRIGO, _es_trigo, _get_divisor

router = APIRouter()

CATEGORIAS_PARO_VALIDAS = {
    "MECANICO", "ELECTRICO", "FALTA_MATERIA_PRIMA", "CAMBIO_FORMATO", "LIMPIEZA", "OTRO",
}
TURNO_DURACION_MINUTOS = 480.0  # 8 horas


def _minutos_entre(hora_inicio: str, hora_fin: str) -> float:
    try:
        h1, m1 = (int(x) for x in hora_inicio.split(":"))
        h2, m2 = (int(x) for x in hora_fin.split(":"))
    except (ValueError, AttributeError):
        raise HTTPException(status_code=400, detail="hora_inicio / hora_fin deben tener formato HH:MM")
    minutos = (h2 * 60 + m2) - (h1 * 60 + m1)
    if minutos < 0:
        minutos += 24 * 60  # el paro cruzó la medianoche
    return float(minutos)


@router.post("/paros", response_model=RegistroParoOut, status_code=201)
def registrar_paro(
    payload: RegistroParoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    if payload.categoria_paro not in CATEGORIAS_PARO_VALIDAS:
        raise HTTPException(status_code=400, detail=f"categoria_paro inválida. Debe ser una de: {', '.join(sorted(CATEGORIAS_PARO_VALIDAS))}")
    duracion = _minutos_entre(payload.hora_inicio, payload.hora_fin)
    if duracion <= 0:
        raise HTTPException(status_code=400, detail="El paro debe durar más de 0 minutos")

    paro = RegistroParoMaquina(
        fecha=payload.fecha, turno=payload.turno, maquina=payload.maquina,
        hora_inicio=payload.hora_inicio, hora_fin=payload.hora_fin, duracion_minutos=duracion,
        categoria_paro=payload.categoria_paro, descripcion_motivo=payload.descripcion_motivo,
        requirio_mantenimiento=payload.requirio_mantenimiento,
        nombre_operario=current_user.nombre, operario_id=current_user.id,
    )
    db.add(paro)
    db.commit()
    db.refresh(paro)

    if payload.requirio_mantenimiento:
        solicitud = SolicitudMantenimiento(
            maquina=payload.maquina,
            descripcion_problema=f"Paro de máquina ({payload.categoria_paro}, {int(duracion)} min): {payload.descripcion_motivo or 'sin descripción'}",
            prioridad="ALTA" if duracion >= 60 else "MEDIA",
            estado="PENDIENTE",
            fecha_reporte=payload.fecha,
            reportado_por_id=current_user.id, nombre_reportado_por=current_user.nombre,
        )
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
        paro.solicitud_mantenimiento_id = solicitud.id
        db.commit()
        db.refresh(paro)

    return paro


@router.get("/paros", response_model=List[RegistroParoOut])
def listar_paros(
    fecha: Optional[str] = Query(None),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    maquina: Optional[str] = Query(None),
    turno: Optional[str] = Query(None),
    categoria_paro: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    q = db.query(RegistroParoMaquina)
    if fecha:
        q = q.filter(RegistroParoMaquina.fecha == fecha)
    if fecha_desde:
        q = q.filter(RegistroParoMaquina.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroParoMaquina.fecha <= fecha_hasta)
    if maquina:
        q = q.filter(RegistroParoMaquina.maquina == maquina)
    if turno:
        q = q.filter(RegistroParoMaquina.turno == turno)
    if categoria_paro:
        q = q.filter(RegistroParoMaquina.categoria_paro == categoria_paro)
    return q.order_by(RegistroParoMaquina.id.desc()).limit(500).all()


@router.delete("/paros/{paro_id}", status_code=204)
def eliminar_paro(paro_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    paro = db.query(RegistroParoMaquina).filter(RegistroParoMaquina.id == paro_id).first()
    if not paro:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    db.delete(paro)
    db.commit()


# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN OEE — Disponibilidad se calcula 100% de los paros registrados aquí
# (dato exacto). Rendimiento y Calidad reutilizan las mismas metas y la misma
# fórmula de % de desperdicio que ya usan Informes de Turno y el Dashboard,
# pero a nivel de planta/día (no hay una meta de velocidad configurada por
# máquina todavía) — por eso el OEE resultante es una aproximación de planta,
# no un OEE exacto por máquina. Queda explicado en `nota_metodologia`.
# ══════════════════════════════════════════════════════════════════════════════
@router.get("/resumen", response_model=OEEResumenOut)
def resumen_oee(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    hoy = date.today().strftime('%Y-%m-%d')
    fecha_desde = fecha_desde or hoy
    fecha_hasta = fecha_hasta or hoy

    paros = db.query(RegistroParoMaquina).filter(
        RegistroParoMaquina.fecha >= fecha_desde, RegistroParoMaquina.fecha <= fecha_hasta
    ).all()

    registros_bobinas = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha >= fecha_desde, RegistroBobinas.fecha <= fecha_hasta
    ).all()

    # ── Disponibilidad por máquina ─────────────────────────────────────────────
    turnos_por_maquina: dict = {}
    for r in registros_bobinas:
        for m in (r.maquina or '').replace('-', ' ').split():
            m = m.strip()
            if not m:
                continue
            turnos_por_maquina.setdefault(m, set()).add((r.fecha, r.turno))

    minutos_parado_por_maquina: dict = {}
    for p in paros:
        minutos_parado_por_maquina[p.maquina] = minutos_parado_por_maquina.get(p.maquina, 0.0) + p.duracion_minutos

    maquinas_relevantes = set(turnos_por_maquina.keys()) | set(minutos_parado_por_maquina.keys())
    disponibilidad_por_maquina: List[DisponibilidadMaquinaItem] = []
    for m in sorted(maquinas_relevantes):
        turnos_trabajados = len(turnos_por_maquina.get(m, set()))
        minutos_teorico = turnos_trabajados * TURNO_DURACION_MINUTOS
        minutos_parado = minutos_parado_por_maquina.get(m, 0.0)
        disp_pct = round(max(0.0, min(100.0, (1 - minutos_parado / minutos_teorico) * 100)), 1) if minutos_teorico > 0 else 0.0
        disponibilidad_por_maquina.append(DisponibilidadMaquinaItem(
            maquina=m, turnos_trabajados=turnos_trabajados, minutos_turno_teorico=minutos_teorico,
            minutos_parado=round(minutos_parado, 1), disponibilidad_pct=disp_pct,
        ))

    total_minutos_teorico = sum(d.minutos_turno_teorico for d in disponibilidad_por_maquina)
    total_minutos_parado = sum(d.minutos_parado for d in disponibilidad_por_maquina)
    disponibilidad_pct = round(max(0.0, min(100.0, (1 - total_minutos_parado / total_minutos_teorico) * 100)), 1) if total_minutos_teorico > 0 else 0.0

    # ── Rendimiento (kg/pacas logrados vs. la meta de planta del rango) ────────
    dias = len({r.fecha for r in registros_bobinas}) or 1
    kg_maiz = sum(sum(f.consumido or 0 for f in r.filas) for r in registros_bobinas if not _es_trigo(r.maquina or ''))
    pacas_trigo = 0.0
    for r in registros_bobinas:
        if not _es_trigo(r.maquina or ''):
            continue
        c_a = sum(f.consumido or 0 for f in r.filas if f.maquina_grupo == 'A')
        c_b = sum(f.consumido or 0 for f in r.filas if f.maquina_grupo == 'B')
        div_r = _get_divisor(r.referencia_producto or '')
        pacas_trigo += round((c_a + c_b) / div_r, 1) if div_r > 0 else 0

    pct_maiz = min(100.0, kg_maiz / (META_KG_MAIZ * dias) * 100) if kg_maiz > 0 else 0.0
    pct_trigo = min(100.0, pacas_trigo / (META_PACAS_TRIGO * dias) * 100) if pacas_trigo > 0 else 0.0
    if kg_maiz > 0 and pacas_trigo > 0:
        rendimiento_pct = round((pct_maiz + pct_trigo) / 2, 1)
    else:
        rendimiento_pct = round(pct_maiz or pct_trigo, 1)

    # ── Calidad (inverso del % de desperdicio de empaque, ya usado en el Dashboard) ─
    pct_desperdicio = _pct_desperdicio(registros_bobinas)
    calidad_pct = round(max(0.0, 100.0 - pct_desperdicio), 1)

    oee_pct = round(disponibilidad_pct * rendimiento_pct * calidad_pct / 10000, 1)

    # ── Paros por categoría (Pareto) ────────────────────────────────────────────
    por_categoria: dict = {}
    for p in paros:
        if p.categoria_paro not in por_categoria:
            por_categoria[p.categoria_paro] = {"minutos": 0.0, "cantidad": 0}
        por_categoria[p.categoria_paro]["minutos"] += p.duracion_minutos
        por_categoria[p.categoria_paro]["cantidad"] += 1

    total_minutos_paro = sum(d["minutos"] for d in por_categoria.values())
    paros_por_categoria = [
        ParoPorCategoriaItem(
            categoria_paro=cat, cantidad_paros=d["cantidad"], minutos=round(d["minutos"], 1),
            pct_del_total=round(d["minutos"] / total_minutos_paro * 100, 1) if total_minutos_paro > 0 else 0.0,
        )
        for cat, d in sorted(por_categoria.items(), key=lambda x: x[1]["minutos"], reverse=True)
    ]

    return OEEResumenOut(
        fecha_desde=fecha_desde, fecha_hasta=fecha_hasta,
        disponibilidad_pct=disponibilidad_pct, rendimiento_pct=rendimiento_pct,
        calidad_pct=calidad_pct, oee_pct=oee_pct,
        total_paros=len(paros), minutos_totales_parada=round(total_minutos_parado, 1),
        disponibilidad_por_maquina=disponibilidad_por_maquina,
        paros_por_categoria=paros_por_categoria,
        nota_metodologia=(
            "Disponibilidad es exacta (turnos trabajados de 8h menos minutos de paro registrados). "
            "Rendimiento y Calidad se calculan a nivel de planta/día usando las mismas metas de "
            "Informes de Turno y Dashboard — todavía no hay una meta de velocidad configurada por "
            "máquina, así que el OEE mostrado es una aproximación de planta, no un valor exacto por máquina."
        ),
    )
