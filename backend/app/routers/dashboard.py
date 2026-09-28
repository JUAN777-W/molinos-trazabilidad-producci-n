from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.models import RegistroBobinas, FilaBobina, RegistroRotulado, FilaRotulado, RegistroPesos, Usuario
from app.auth import require_admin
from app.referencias_catalogo import referencia_label
from datetime import date, timedelta

router = APIRouter()

# ─── Umbral de desperdicio aceptable (ajustar según meta real de la planta) ──
META_DESPERDICIO_PCT = 3.0
DIAS_ALERTA_DESPERDICIO = 3  # días seguidos por encima de la meta para generar alerta


class TarjetaResumen(BaseModel):
    total_turnos_hoy: int
    total_turnos_mes: int
    total_kg_consumidos_hoy: float
    promedio_desperdicio_pct: float
    fechados_no_cumplen_hoy: int
    maquinas_activas_hoy: int

class ProduccionPorMaquina(BaseModel):
    maquina: str
    total_kg: float
    total_unidades: int
    turnos: int

class UltimoRegistro(BaseModel):
    id: int
    tipo: str
    fecha: str
    maquina: str
    operario: str
    turno: str

class PuntoTendencia(BaseModel):
    fecha: str
    kg_consumidos: float
    turnos: int

class Alerta(BaseModel):
    tipo: str        # "desperdicio" | "fechado" | "sin_registro"
    severidad: str    # "alta" | "media"
    mensaje: str

class DashboardOut(BaseModel):
    tarjetas: TarjetaResumen
    produccion_por_maquina: List[ProduccionPorMaquina]
    ultimos_registros: List[UltimoRegistro]
    fechados_semana: dict
    tendencia_diaria: List[PuntoTendencia]
    alertas: List[Alerta]
    meta_desperdicio_pct: float


def _rango_mes_anterior():
    primer_dia_actual = date.today().replace(day=1)
    ultimo_dia_mes_anterior = primer_dia_actual - timedelta(days=1)
    primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    return (
        primer_dia_mes_anterior.strftime('%Y-%m-%d'),
        ultimo_dia_mes_anterior.strftime('%Y-%m-%d'),
    )


def _pct_desperdicio(registros: list) -> float:
    valores = []
    for r in registros:
        consumido = sum(f.consumido or 0 for f in r.filas)
        if consumido > 0 and r.peso_desperdicio:
            valores.append(r.peso_desperdicio / consumido * 100)
    return round(sum(valores) / len(valores), 2) if valores else 0.0


@router.get("/", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db), _=Depends(require_admin)):
    hoy = date.today().strftime('%Y-%m-%d')
    inicio_mes = date.today().replace(day=1).strftime('%Y-%m-%d')
    hace_7_dias = [(date.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
    hace_14_dias = [(date.today() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(13, -1, -1)]
    inicio_mes_ant, fin_mes_ant = _rango_mes_anterior()

    # ── Tarjetas ──────────────────────────────────────────────────────────────
    turnos_hoy = db.query(RegistroBobinas).filter(RegistroBobinas.fecha == hoy).count()
    turnos_mes = db.query(RegistroBobinas).filter(RegistroBobinas.fecha >= inicio_mes).count()

    filas_hoy = db.query(FilaBobina).join(RegistroBobinas).filter(RegistroBobinas.fecha == hoy).all()
    kg_hoy = sum(f.consumido or 0 for f in filas_hoy)

    regs_mes = db.query(RegistroBobinas).filter(RegistroBobinas.fecha >= inicio_mes).all()
    prom_desp = _pct_desperdicio(regs_mes)

    filas_rot_hoy = db.query(FilaRotulado).join(RegistroRotulado).filter(
        RegistroRotulado.fecha == hoy
    ).all()
    fechados_no_hoy = sum(1 for f in filas_rot_hoy if f.fechado_cumple == 'NO')

    # Máquinas activas hoy: cuenta máquinas distintas (separando parejas tipo "9X-8S")
    # con al menos un registro de Bobinas hoy. A diferencia del conteo de usuarios
    # activos (que es un dato de configuración, no cambia día a día), esto sí refleja
    # actividad real de planta en el momento.
    registros_hoy_bob = db.query(RegistroBobinas).filter(RegistroBobinas.fecha == hoy).all()
    maquinas_hoy_set = set()
    for r in registros_hoy_bob:
        for m in (r.maquina or '').replace('-', ' ').split():
            if m.strip():
                maquinas_hoy_set.add(m.strip())
    maquinas_activas_hoy = len(maquinas_hoy_set)

    tarjetas = TarjetaResumen(
        total_turnos_hoy=turnos_hoy,
        total_turnos_mes=turnos_mes,
        total_kg_consumidos_hoy=round(kg_hoy, 2),
        promedio_desperdicio_pct=prom_desp,
        fechados_no_cumplen_hoy=fechados_no_hoy,
        maquinas_activas_hoy=maquinas_activas_hoy,
    )

    # ── Producción por máquina (mes actual) ───────────────────────────────────
    regs_maquina = regs_mes
    maquinas_dict: dict = {}
    for r in regs_maquina:
        m = r.maquina or 'Sin máquina'
        if m not in maquinas_dict:
            maquinas_dict[m] = {'kg': 0, 'unidades': 0, 'turnos': 0}
        maquinas_dict[m]['turnos'] += 1
        for f in r.filas:
            maquinas_dict[m]['kg'] += f.consumido or 0
            maquinas_dict[m]['unidades'] += f.contador or 0

    produccion_por_maquina = [
        ProduccionPorMaquina(
            maquina=m,
            total_kg=round(d['kg'], 2),
            total_unidades=d['unidades'],
            turnos=d['turnos'],
        )
        for m, d in sorted(maquinas_dict.items(), key=lambda x: x[1]['kg'], reverse=True)
    ]

    # ── Últimos 10 registros (Bobinas + Rotulado + Pesos) ─────────────────────
    ultimos_bob = db.query(RegistroBobinas).order_by(RegistroBobinas.id.desc()).limit(5).all()
    ultimos_rot = db.query(RegistroRotulado).order_by(RegistroRotulado.id.desc()).limit(5).all()
    ultimos_pes = db.query(RegistroPesos).order_by(RegistroPesos.id.desc()).limit(5).all()

    ultimos: List[UltimoRegistro] = []
    for r in ultimos_bob:
        ultimos.append(UltimoRegistro(
            id=r.id, tipo='Bobinas', fecha=r.fecha or '', maquina=r.maquina or '',
            operario=r.nombre_operario or '', turno=r.turno or ''
        ))
    for r in ultimos_rot:
        ultimos.append(UltimoRegistro(
            id=r.id, tipo='Rotulado', fecha=r.fecha or '', maquina=r.maquina or '',
            operario=r.nombre_operario or '', turno=getattr(r, 'turno', '') or ''
        ))
    for r in ultimos_pes:
        ultimos.append(UltimoRegistro(
            id=r.id, tipo='Pesos', fecha=r.fecha or '', maquina=r.maquina or '',
            operario=r.nombre_operario or '', turno=getattr(r, 'turno', '') or ''
        ))
    ultimos.sort(key=lambda x: x.fecha, reverse=True)
    ultimos = ultimos[:10]

    # ── Fechados últimos 7 días ───────────────────────────────────────────────
    fechados_semana: dict = {}
    for dia in hace_7_dias:
        filas = db.query(FilaRotulado).join(RegistroRotulado).filter(
            RegistroRotulado.fecha == dia
        ).all()
        fechados_semana[dia] = {
            'cumplen': sum(1 for f in filas if f.fechado_cumple == 'SI'),
            'no_cumplen': sum(1 for f in filas if f.fechado_cumple == 'NO'),
        }

    # regs_por_dia_7 se usa más abajo solo para detectar rachas de desperdicio
    # por máquina (alertas). El detalle turno-por-turno ya no se envía al
    # dashboard — ese nivel de detalle vive en "Informes de Turno".
    regs_por_dia_7 = {}
    for dia in hace_7_dias:
        regs_por_dia_7[dia] = db.query(RegistroBobinas).filter(RegistroBobinas.fecha == dia).all()

    # ── Tendencia diaria (últimos 14 días) ─────────────────────────────────────
    tendencia_diaria: List[PuntoTendencia] = []
    for dia in hace_14_dias:
        regs_dia = db.query(RegistroBobinas).filter(RegistroBobinas.fecha == dia).all()
        kg_dia = sum(sum(f.consumido or 0 for f in r.filas) for r in regs_dia)
        tendencia_diaria.append(PuntoTendencia(
            fecha=dia, kg_consumidos=round(kg_dia, 2), turnos=len(regs_dia)
        ))

    # ── Variación de desperdicio vs. mes anterior (solo para la alerta) ────────
    # El detalle completo de meses ya no vive aquí — se fusionó en el Histórico
    # Mensual de 6 meses del panel de Analítica Avanzada, que da más contexto.
    regs_mes_ant = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha >= inicio_mes_ant, RegistroBobinas.fecha <= fin_mes_ant
    ).all()
    pct_desp_actual = prom_desp
    pct_desp_anterior = _pct_desperdicio(regs_mes_ant)
    variacion_desperdicio_pp = round(pct_desp_actual - pct_desp_anterior, 2)

    # ── Alertas automáticas ─────────────────────────────────────────────────────
    alertas: List[Alerta] = []

    # 1) Fechados que no cumplen hoy
    if fechados_no_hoy > 0:
        alertas.append(Alerta(
            tipo='fechado',
            severidad='alta',
            mensaje=f'{fechados_no_hoy} producto(s) con fechado/sellado que no cumple hoy.',
        ))

    # 2) Máquina con desperdicio por encima de la meta varios días seguidos
    ultimos_dias_orden = hace_7_dias[::-1]  # del más reciente al más antiguo
    desp_por_maquina_dia: dict = {}
    for dia in ultimos_dias_orden:
        for r in regs_por_dia_7.get(dia, []):
            consumido = sum(f.consumido or 0 for f in r.filas)
            if consumido <= 0 or not r.peso_desperdicio:
                continue
            pct = r.peso_desperdicio / consumido * 100
            m = r.maquina or 'Sin máquina'
            desp_por_maquina_dia.setdefault(m, []).append((dia, pct))

    for maquina, valores in desp_por_maquina_dia.items():
        valores_ordenados = sorted(valores, key=lambda x: x[0], reverse=True)
        racha = 0
        for _, pct in valores_ordenados:
            if pct > META_DESPERDICIO_PCT:
                racha += 1
            else:
                break
        if racha >= DIAS_ALERTA_DESPERDICIO:
            alertas.append(Alerta(
                tipo='desperdicio',
                severidad='alta',
                mensaje=f'Máquina {maquina}: desperdicio por encima de la meta ({META_DESPERDICIO_PCT}%) durante {racha} días seguidos.',
            ))

    # 3) Desperdicio del mes empeoró de forma notoria vs. mes anterior
    if variacion_desperdicio_pp > 0.5:
        alertas.append(Alerta(
            tipo='desperdicio',
            severidad='media',
            mensaje=f'El % de desperdicio subió {variacion_desperdicio_pp} puntos vs. el mes anterior.',
        ))

    return DashboardOut(
        tarjetas=tarjetas,
        produccion_por_maquina=produccion_por_maquina,
        ultimos_registros=ultimos,
        fechados_semana=fechados_semana,
        tendencia_diaria=tendencia_diaria,
        alertas=alertas,
        meta_desperdicio_pct=META_DESPERDICIO_PCT,
    )


# ══════════════════════════════════════════════════════════════════════════════
# ANALÍTICA AVANZADA — Panel Ejecutivo
#
# Endpoint totalmente aparte del dashboard principal (no modifica nada de lo
# que ya funciona). Pensado para responder preguntas gerenciales: ¿quién rinde
# mejor?, ¿qué referencia desperdicia más?, ¿vamos mejor o peor que hace meses?,
# ¿hay un patrón según el día de la semana o el turno?
# ══════════════════════════════════════════════════════════════════════════════

class RankingOperario(BaseModel):
    operario: str
    turnos: int
    kg_totales: float
    pct_desperdicio_promedio: float

class RankingOperariosOut(BaseModel):
    mejores_desperdicio: List[RankingOperario]   # menor % desperdicio primero
    peores_desperdicio: List[RankingOperario]    # mayor % desperdicio primero
    mas_productivos: List[RankingOperario]       # mayor kg consumidos primero

class DesperdicioPorReferencia(BaseModel):
    referencia: str
    turnos: int
    kg_consumidos: float
    kg_desperdicio: float
    pct_desperdicio: float

class MesHistorico(BaseModel):
    mes: str  # "2026-01"
    kg_consumidos: float
    pct_desperdicio: float
    turnos: int
    cumple_meta: bool
    variacion_kg_pct: Optional[float] = None  # vs. el mes anterior; None si no hay mes previo con datos

class CeldaHeatmap(BaseModel):
    dia_semana: str
    turno: str
    pct_desperdicio_promedio: float
    turnos: int

class CumplimientoPesos(BaseModel):
    total_muestras: int
    dentro_rango: int
    fuera_rango: int
    pct_dentro_rango: float

class AnaliticaOut(BaseModel):
    ranking_operarios: RankingOperariosOut
    desperdicio_por_referencia: List[DesperdicioPorReferencia]
    historico_mensual: List[MesHistorico]
    heatmap_turno_dia: List[CeldaHeatmap]
    cumplimiento_pesos: CumplimientoPesos
    dias_analizados: int
    meta_desperdicio_pct: float


def _rango_mes(offset: int):
    """Devuelve (primer_dia, ultimo_dia, 'YYYY-MM') del mes que está `offset`
    meses atrás del mes actual (offset=0 -> mes actual)."""
    hoy = date.today()
    anio, mes = hoy.year, hoy.month - offset
    while mes <= 0:
        mes += 12
        anio -= 1
    primer_dia = date(anio, mes, 1)
    if mes == 12:
        ultimo_dia = date(anio, 12, 31)
    else:
        ultimo_dia = date(anio, mes + 1, 1) - timedelta(days=1)
    return primer_dia.strftime('%Y-%m-%d'), ultimo_dia.strftime('%Y-%m-%d'), primer_dia.strftime('%Y-%m')


def _muestra_en_rango(v: float) -> bool:
    """Misma regla que usa el semáforo del formulario de Pesos: bolsas de
    ~1000g deben pesar entre 1000-1015g, y las de ~500g entre 500-508g."""
    if v > 800:
        return 1000 <= v <= 1015
    return 500 <= v <= 508


@router.get("/analitica", response_model=AnaliticaOut)
def get_analitica(db: Session = Depends(get_db), _=Depends(require_admin)):
    DIAS_VENTANA = 30
    hace_30_dias = (date.today() - timedelta(days=DIAS_VENTANA - 1)).strftime('%Y-%m-%d')
    regs_30d = db.query(RegistroBobinas).filter(RegistroBobinas.fecha >= hace_30_dias).all()

    # ── Ranking de operarios (últimos 30 días) ────────────────────────────────
    por_operario: dict = {}
    for r in regs_30d:
        op = r.nombre_operario or 'Sin nombre'
        if op not in por_operario:
            por_operario[op] = {'turnos': 0, 'kg': 0.0, 'desp_valores': []}
        por_operario[op]['turnos'] += 1
        consumido = sum(f.consumido or 0 for f in r.filas)
        por_operario[op]['kg'] += consumido
        if consumido > 0 and r.peso_desperdicio:
            por_operario[op]['desp_valores'].append(r.peso_desperdicio / consumido * 100)

    ranking_base = []
    for op, d in por_operario.items():
        pct_prom = round(sum(d['desp_valores']) / len(d['desp_valores']), 2) if d['desp_valores'] else 0.0
        ranking_base.append(RankingOperario(
            operario=op, turnos=d['turnos'], kg_totales=round(d['kg'], 2),
            pct_desperdicio_promedio=pct_prom,
        ))

    # Solo operarios con al menos 2 turnos, para que el ranking sea representativo
    ranking_valido = [r for r in ranking_base if r.turnos >= 2]
    ranking_operarios = RankingOperariosOut(
        mejores_desperdicio=sorted(ranking_valido, key=lambda x: x.pct_desperdicio_promedio)[:5],
        peores_desperdicio=sorted(ranking_valido, key=lambda x: x.pct_desperdicio_promedio, reverse=True)[:5],
        mas_productivos=sorted(ranking_valido, key=lambda x: x.kg_totales, reverse=True)[:5],
    )

    # ── Desperdicio por referencia de producto (últimos 30 días) ──────────────
    por_referencia: dict = {}
    for r in regs_30d:
        ref = referencia_label(r.referencia_producto) or 'Sin referencia'
        if ref not in por_referencia:
            por_referencia[ref] = {'turnos': 0, 'kg': 0.0, 'desp_kg': 0.0}
        por_referencia[ref]['turnos'] += 1
        consumido = sum(f.consumido or 0 for f in r.filas)
        por_referencia[ref]['kg'] += consumido
        por_referencia[ref]['desp_kg'] += r.peso_desperdicio or 0

    desperdicio_por_referencia = []
    for ref, d in por_referencia.items():
        pct = round(d['desp_kg'] / d['kg'] * 100, 2) if d['kg'] > 0 else 0.0
        desperdicio_por_referencia.append(DesperdicioPorReferencia(
            referencia=ref, turnos=d['turnos'], kg_consumidos=round(d['kg'], 2),
            kg_desperdicio=round(d['desp_kg'], 2), pct_desperdicio=pct,
        ))
    desperdicio_por_referencia.sort(key=lambda x: x.pct_desperdicio, reverse=True)

    # ── Histórico mensual (últimos 6 meses, con variación vs. mes anterior) ───
    # Se traen 7 meses internamente: el más antiguo es solo para poder calcular
    # la variación del primer mes que sí se muestra.
    meses_calculados = []
    for offset in range(6, -1, -1):
        primer_dia, ultimo_dia, label = _rango_mes(offset)
        regs_mes_i = db.query(RegistroBobinas).filter(
            RegistroBobinas.fecha >= primer_dia, RegistroBobinas.fecha <= ultimo_dia
        ).all()
        kg_mes_i = sum(sum(f.consumido or 0 for f in r.filas) for r in regs_mes_i)
        meses_calculados.append({
            'mes': label, 'kg': round(kg_mes_i, 2),
            'pct': _pct_desperdicio(regs_mes_i), 'turnos': len(regs_mes_i),
        })

    historico_mensual = []
    for i in range(1, len(meses_calculados)):
        actual, anterior = meses_calculados[i], meses_calculados[i - 1]
        variacion = round(((actual['kg'] - anterior['kg']) / anterior['kg'] * 100), 1) if anterior['kg'] > 0 else None
        historico_mensual.append(MesHistorico(
            mes=actual['mes'], kg_consumidos=actual['kg'], pct_desperdicio=actual['pct'],
            turnos=actual['turnos'], cumple_meta=actual['pct'] <= META_DESPERDICIO_PCT,
            variacion_kg_pct=variacion,
        ))

    # ── Mapa de calor turno × día de la semana (últimos 30 días) ──────────────
    DIAS_ES = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    celdas: dict = {}
    for r in regs_30d:
        if not r.fecha or not r.turno:
            continue
        try:
            fecha_obj = date.fromisoformat(r.fecha)
        except ValueError:
            continue
        dia_nombre = DIAS_ES[fecha_obj.weekday()]
        clave = (dia_nombre, r.turno)
        if clave not in celdas:
            celdas[clave] = {'turnos': 0, 'desp_valores': []}
        celdas[clave]['turnos'] += 1
        consumido = sum(f.consumido or 0 for f in r.filas)
        if consumido > 0 and r.peso_desperdicio:
            celdas[clave]['desp_valores'].append(r.peso_desperdicio / consumido * 100)

    heatmap_turno_dia = []
    for (dia_nombre, turno), d in celdas.items():
        pct_prom = round(sum(d['desp_valores']) / len(d['desp_valores']), 2) if d['desp_valores'] else 0.0
        heatmap_turno_dia.append(CeldaHeatmap(
            dia_semana=dia_nombre, turno=turno, pct_desperdicio_promedio=pct_prom, turnos=d['turnos'],
        ))

    # ── Cumplimiento de Pesos (últimos 30 días) — antes invisible en todo el sistema
    regs_pesos_30d = db.query(RegistroPesos).filter(RegistroPesos.fecha >= hace_30_dias).all()
    total_muestras, dentro_rango = 0, 0
    for r in regs_pesos_30d:
        for f in r.filas:
            for v in [f.muestra_1, f.muestra_2, f.muestra_3, f.muestra_4, f.muestra_5]:
                if v is not None:
                    total_muestras += 1
                    if _muestra_en_rango(v):
                        dentro_rango += 1
    pct_dentro = round(dentro_rango / total_muestras * 100, 1) if total_muestras > 0 else 0.0
    cumplimiento_pesos = CumplimientoPesos(
        total_muestras=total_muestras, dentro_rango=dentro_rango,
        fuera_rango=total_muestras - dentro_rango, pct_dentro_rango=pct_dentro,
    )

    return AnaliticaOut(
        ranking_operarios=ranking_operarios,
        desperdicio_por_referencia=desperdicio_por_referencia[:10],
        historico_mensual=historico_mensual,
        heatmap_turno_dia=heatmap_turno_dia,
        cumplimiento_pesos=cumplimiento_pesos,
        dias_analizados=DIAS_VENTANA,
        meta_desperdicio_pct=META_DESPERDICIO_PCT,
    )


# ─── Monitor en tiempo real ────────────────────────────────────────────────────
class MaquinaEstado(BaseModel):
    maquina: str
    tipo: str
    operario: str
    activo: bool
    turno_actual: str
    referencia: str
    fecha_registro: str

@router.get("/monitor", response_model=List[MaquinaEstado])
def monitor_maquinas(db: Session = Depends(get_db), _=Depends(require_admin)):
    from datetime import date as date_cls
    hoy = date_cls.today().strftime('%Y-%m-%d')

    MAQUINAS_TRIGO = {'8S','9X','10Y','11Z'}
    TODAS_MAQUINAS = ['1P','2Q','4T','5U','6V','7W','8S','9X','10Y','11Z']

    registros_hoy = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha == hoy
    ).order_by(RegistroBobinas.id.desc()).all()

    maquinas_vistas: dict = {}
    for r in registros_hoy:
        maquinas_raw = r.maquina or ''
        partes = [m.strip() for m in maquinas_raw.replace('-', ' ').split()]
        for m in partes:
            if m and m not in maquinas_vistas:
                maquinas_vistas[m] = {
                    'operario': r.nombre_operario or 'Sin asignar',
                    'turno': r.turno or '',
                    'referencia': r.referencia_producto or '',
                    'fecha': r.fecha or '',
                }

    operarios = db.query(Usuario).filter(
        Usuario.activo == 'SI', Usuario.rol == 'operario'
    ).all()
    for op in operarios:
        maquinas_op = [m.strip() for m in (op.maquinas_asignadas or '').replace('-', ' ').split() if m.strip()]
        for m in maquinas_op:
            if m not in maquinas_vistas:
                maquinas_vistas[m] = {
                    'operario': op.nombre,
                    'turno': '',
                    'referencia': '',
                    'fecha': '',
                }

    resultado = []
    for maquina in TODAS_MAQUINAS:
        tipo = 'trigo' if maquina in MAQUINAS_TRIGO else 'maiz'
        if maquina in maquinas_vistas:
            d = maquinas_vistas[maquina]
            resultado.append(MaquinaEstado(
                maquina=maquina,
                tipo=tipo,
                operario=d['operario'],
                activo=bool(d['fecha'] == hoy and d['turno']),
                turno_actual=d['turno'],
                referencia=d['referencia'],
                fecha_registro=d['fecha'],
            ))
        else:
            resultado.append(MaquinaEstado(
                maquina=maquina,
                tipo=tipo,
                operario='Sin operario',
                activo=False,
                turno_actual='',
                referencia='',
                fecha_registro='',
            ))

    return resultado

# ══════════════════════════════════════════════════════════════════════════════
# RENDIMIENTO POR PROVEEDOR — consumo y desperdicio de material de empaque
# (Tuboplast, Plastilene, Dorfan, Flexospring), para saber cuál está rindiendo
# mejor o peor. El desperdicio se registra por TURNO completo, no por rollo
# individual, así que si un turno usó más de un proveedor, el desperdicio de
# ese turno se reparte proporcionalmente entre ellos según cuánto consumió
# cada uno — mismo método que ya se usa para el desglose por referencia de
# empaque en los informes de turno.
# ══════════════════════════════════════════════════════════════════════════════
class ProveedorReferenciaItem(BaseModel):
    referencia_producto: str
    kg_consumidos: float
    kg_desperdicio: float
    pct_desperdicio: float
    turnos: int

class ProveedorItem(BaseModel):
    proveedor: str
    kg_consumidos: float
    kg_desperdicio: float
    pct_desperdicio: float
    turnos: int
    referencias: List[ProveedorReferenciaItem] = []

class ProveedoresResumenOut(BaseModel):
    proveedores: List[ProveedorItem]
    mayor_consumo: Optional[str] = None
    menor_consumo: Optional[str] = None
    mejor_rendimiento: Optional[str] = None   # menor % de desperdicio
    peor_rendimiento: Optional[str] = None    # mayor % de desperdicio


@router.get("/proveedores", response_model=ProveedoresResumenOut)
def resumen_proveedores(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    db: Session = Depends(get_db), _=Depends(require_admin),
):
    q = db.query(RegistroBobinas)
    if fecha_desde:
        q = q.filter(RegistroBobinas.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(RegistroBobinas.fecha <= fecha_hasta)
    registros = q.all()

    # proveedores: total por material de empaque (Tuboplast, Plastilene...).
    # detalle: lo mismo, pero cruzado además por la referencia de producto que
    # se estaba empacando — un mismo proveedor se usa en varias referencias,
    # y eso es justo lo que se quiere poder ver por separado.
    proveedores: dict = {}
    detalle: dict = {}
    for r in registros:
        consumido_total_turno = sum(f.consumido or 0 for f in r.filas)
        if consumido_total_turno <= 0:
            continue
        desp_total_turno = (r.peso_desperdicio or 0) + (getattr(r, 'peso_desperdicio_fardo', 0) or 0)
        ref_label = referencia_label(r.referencia_producto) or 'Sin referencia'

        for f in r.filas:
            prov = (f.referencia_empaque or '').strip().upper()
            if not prov:
                continue
            c = f.consumido or 0
            proporcion = c / consumido_total_turno
            desp_asignado = desp_total_turno * proporcion

            if prov not in proveedores:
                proveedores[prov] = {'consumo': 0.0, 'desperdicio': 0.0, 'turnos': set()}
            proveedores[prov]['consumo'] += c
            proveedores[prov]['desperdicio'] += desp_asignado
            proveedores[prov]['turnos'].add(r.id)

            clave = (prov, ref_label)
            if clave not in detalle:
                detalle[clave] = {'consumo': 0.0, 'desperdicio': 0.0, 'turnos': set()}
            detalle[clave]['consumo'] += c
            detalle[clave]['desperdicio'] += desp_asignado
            detalle[clave]['turnos'].add(r.id)

    items: List[ProveedorItem] = []
    for nombre, d in proveedores.items():
        consumo = round(d['consumo'], 2)
        desperdicio = round(d['desperdicio'], 2)
        base = consumo + desperdicio
        pct_desperdicio = round(desperdicio / base * 100, 2) if base > 0 else 0.0

        referencias_prov: List[ProveedorReferenciaItem] = []
        for (prov2, ref_label), dd in detalle.items():
            if prov2 != nombre:
                continue
            c2 = round(dd['consumo'], 2)
            desp2 = round(dd['desperdicio'], 2)
            base2 = c2 + desp2
            pct2 = round(desp2 / base2 * 100, 2) if base2 > 0 else 0.0
            referencias_prov.append(ProveedorReferenciaItem(
                referencia_producto=ref_label, kg_consumidos=c2, kg_desperdicio=desp2,
                pct_desperdicio=pct2, turnos=len(dd['turnos']),
            ))
        referencias_prov.sort(key=lambda x: x.kg_consumidos, reverse=True)

        items.append(ProveedorItem(
            proveedor=nombre, kg_consumidos=consumo, kg_desperdicio=desperdicio,
            pct_desperdicio=pct_desperdicio, turnos=len(d['turnos']),
            referencias=referencias_prov,
        ))

    items.sort(key=lambda x: x.kg_consumidos, reverse=True)

    mayor_consumo = items[0].proveedor if items else None
    menor_consumo = min(items, key=lambda x: x.kg_consumidos).proveedor if items else None
    mejor_rendimiento = min(items, key=lambda x: x.pct_desperdicio).proveedor if items else None
    peor_rendimiento = max(items, key=lambda x: x.pct_desperdicio).proveedor if items else None

    return ProveedoresResumenOut(
        proveedores=items,
        mayor_consumo=mayor_consumo, menor_consumo=menor_consumo,
        mejor_rendimiento=mejor_rendimiento, peor_rendimiento=peor_rendimiento,
    )