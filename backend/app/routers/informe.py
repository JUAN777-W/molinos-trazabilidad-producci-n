from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models.models import RegistroBobinas, FilaBobina, RegistroRotulado, FilaRotulado, RegistroPesos, RegistroPesoEnfardadora, Usuario
from app.auth import require_admin, create_token
from app.pdf_render import render_planilla_pdf, nombre_archivo
from app.email_sender import enviar_pdfs_exportacion, envio_configurado as email_configurado
from app.n8n_sender import enviar_pdfs_a_n8n, envio_configurado as n8n_configurado
from datetime import datetime

router = APIRouter()

TURNO_LABELS = {
    'T1': 'Turno 1 — 6:00 a.m. a 2:00 p.m.',
    'T2': 'Turno 2 — 2:00 p.m. a 10:00 p.m.',
    'T3': 'Turno 3 — 10:00 p.m. a 6:00 a.m.',
}

DIVISORES_POR_CODIGO = {
    '10-20-5': 10, '10-20-6': 25, '10-20-64': 25, '10-20-65': 25, '10-20-66': 25,
    '10-20-7': 10, '10-20-8': 25,
    '11-20-19': 20, '11-20-20': 20, '11-20-21': 20, '11-20-25': 96, '11-20-3': 24,
    '11-20-5': 20, '11-20-57': 24, '11-20-59': 20, '11-20-6': 20, '11-20-61': 24,
    '11-20-62': 20, '11-20-65': 20, '11-20-66': 20, '11-20-72': 20, '11-20-73': 20,
    '11-20-76': 10, '11-20-77': 20, '11-20-79': 20, '11-20-83': 20, '11-20-84': 24,
    '11-20-85': 20, '11-20-86': 20, '11-20-87': 20,
}

DIV_RULES = [
    ('24lb', 24), ('20kg', 20), ('50kg', 2),
    ('250g', 96), ('1000', 20), ('trigo', 25),
]
MAQUINAS_TRIGO = {'8S', '9X', '10Y', '11Z'}
META_PACAS_TRIGO = 6000
META_KG_MAIZ = 85000

def _get_divisor(ref_key: str) -> int:
    if ref_key in DIVISORES_POR_CODIGO:
        return DIVISORES_POR_CODIGO[ref_key]
    for fragmento, div in DIV_RULES:
        if fragmento in (ref_key or ''):
            return div
    return 20

def _es_trigo(maquina: str) -> bool:
    for m in MAQUINAS_TRIGO:
        if m in (maquina or '').upper():
            return True
    return False

# ─── Schemas ──────────────────────────────────────────────────────────────────
class FilaInformeOut(BaseModel):
    maquina: str
    operario: str
    contador_final: int
    fardos_enfardadora: int
    referencias: List[str]
    tiempo_parada: Optional[str] = ""

class ConsumoEmpaque(BaseModel):
    descripcion: str
    consumo_produccion: float
    desperdicio: float
    desperdicio_fardo: float
    consumo_total: float
    porcentaje_desperdicio: float
    porcentaje_desperdicio_fardo: float

class ProductividadOut(BaseModel):
    tipo: str
    meta_valor: float
    meta_unidad: str
    logrado: float
    pct_meta: float
    cumple_meta: bool
    total_pacas: float
    divisor_usado: int
    nota_meta: str

class InformeGeneralOut(BaseModel):
    fecha: str
    turno: str
    turno_label: str
    maquinas_activas: List[dict]
    total_unidades_maiz: int
    total_pacas_maiz: float
    total_unidades_trigo: int
    total_pacas_trigo: float
    consumo_empaque: List[ConsumoEmpaque]
    total_consumido_kg: float
    total_desperdicio_empaque_kg: float
    total_desperdicio_fardo_kg: float
    pct_desperdicio_empaque: float
    pct_desperdicio_fardo: float
    total_fechados: int
    fechados_cumplen: int
    fechados_no_cumplen: int
    productividad_maiz: ProductividadOut
    productividad_trigo: ProductividadOut
    registros_incluidos: List[int]
    generado_en: str

class InformeTurnoResumen(BaseModel):
    id: int
    fecha: str
    turno: str
    turno_label: str
    maquina: str
    operario: str
    generado_en: str
    pro_numero: str = ""
    lote: str = ""

class InformeTurnoDetalleOut(BaseModel):
    id: int
    fecha: str
    turno: str
    turno_label: str
    maquina: str
    operario: str
    filas_maquinas: List[FilaInformeOut]
    total_produccion_maquinas: dict
    productividad: dict
    total_fechados: int
    fechados_cumplen: int
    fechados_no_cumplen: int
    consumo_empaque: List[ConsumoEmpaque]
    total_consumido_kg: float
    total_desperdicio_kg: float
    total_desperdicio_fardo_kg: float
    porcentaje_desperdicio_global: float
    porcentaje_desperdicio_fardo: float
    total_muestras_pesos: int
    generado_en: str

class EnlacesPlanillaOut(BaseModel):
    """Ids reales de Rotulado y Pesos que corresponden al mismo turno de este
    registro de Bobinas — para poder abrir la planilla exacta de cada uno
    desde el panel admin (Bobinas es siempre 1, Rotulado/Pesos pueden ser 1 o
    2 si la máquina es pareja)."""
    bobinas_id: int
    rotulado_ids: List[int]
    pesos_ids: List[int]
    pesos_enfardadora_ids: List[int]

class AsignarExportacionIn(BaseModel):
    """Número de PRO y lote de exportación — los asigna el admin desde Informes,
    una vez sabidos, y se aplican de una vez a las 4 planillas del turno/máquina
    (Bobinas, Rotulado, Pesos, Pesos Enfardadora)."""
    pro_numero: str = ""
    lote: str = ""

class AsignarExportacionOut(BaseModel):
    bobinas_id: int
    rotulado_ids: List[int]
    pesos_ids: List[int]
    pesos_enfardadora_ids: List[int]
    pro_numero: str
    lote: str
    correo_enviado: bool = False
    correo_error: str = ""

# ─── Endpoints ────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[InformeTurnoResumen])
def listar_informes(db: Session = Depends(get_db), _=Depends(require_admin)):
    registros = db.query(RegistroBobinas).order_by(RegistroBobinas.id.desc()).all()
    return [InformeTurnoResumen(
        id=r.id, fecha=r.fecha or '', turno=r.turno or '',
        turno_label=TURNO_LABELS.get(r.turno or '', r.turno or ''),
        maquina=r.maquina or '', operario=r.nombre_operario or '',
        generado_en=(r.creado_en.strftime('%Y-%m-%d %H:%M:%S') if r.creado_en else ''),
        pro_numero=r.pro_numero or '', lote=r.lote or '',
    ) for r in registros]


@router.get("/general", response_model=InformeGeneralOut)
def informe_general(
    fecha: str = Query(...),
    turno: str = Query(...),
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    """Informe consolidado de todas las máquinas de un turno."""
    registros = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha == fecha,
        RegistroBobinas.turno == turno,
    ).all()

    if not registros:
        raise HTTPException(status_code=404, detail="No hay registros para esa fecha y turno")

    maquinas_activas = []
    total_un_maiz = 0; total_pacas_maiz = 0.0
    total_un_trigo = 0; total_pacas_trigo = 0.0
    total_consumido = 0.0
    total_desp_emp = 0.0; total_desp_fardo = 0.0
    refs_agrupadas: dict = {}
    registros_ids = []

    for r in registros:
        registros_ids.append(r.id)
        filas = r.filas
        es_trigo = _es_trigo(r.maquina or '')
        divisor = _get_divisor(r.referencia_producto or '')

        cnt_a = max([f.contador for f in filas if f.maquina_grupo == 'A' and f.contador], default=0)
        cnt_b = max([f.contador for f in filas if f.maquina_grupo == 'B' and f.contador], default=0)
        cnt_enf = max([f.contador for f in filas if f.maquina_grupo == 'ENF' and f.contador], default=0)
        total_un = cnt_a + cnt_b
        pacas = round(total_un / divisor, 1) if divisor > 0 else 0
        consumido_r = sum(f.consumido or 0 for f in filas)

        maquinas_activas.append({
            'maquina': r.maquina or '',
            'operario': r.nombre_operario or '',
            'tipo': 'trigo' if es_trigo else 'maiz',
            'referencia': r.referencia_producto or '',
            'contador_final': total_un,
            'fardos_enfardadora': cnt_enf,
            'pacas': pacas,
            'consumido_kg': round(consumido_r, 2),
            'desperdicio_empaque_kg': r.peso_desperdicio or 0,
            'desperdicio_fardo_kg': getattr(r, 'peso_desperdicio_fardo', 0) or 0,
            'registro_id': r.id,
        })

        if es_trigo:
            total_un_trigo += total_un
            total_pacas_trigo += pacas
        else:
            total_un_maiz += total_un
            total_pacas_maiz += pacas

        total_consumido += consumido_r
        total_desp_emp += r.peso_desperdicio or 0
        total_desp_fardo += getattr(r, 'peso_desperdicio_fardo', 0) or 0

        for f in filas:
            ref = f.referencia_empaque or 'Sin referencia'
            if ref not in refs_agrupadas:
                refs_agrupadas[ref] = {'consumo': 0}
            refs_agrupadas[ref]['consumo'] += f.consumido or 0

    consumo_empaque = []
    for ref, datos in refs_agrupadas.items():
        c = datos['consumo']
        prop = c / total_consumido if total_consumido > 0 else 0
        d_emp = total_desp_emp * prop
        d_far = total_desp_fardo * prop
        consumo_empaque.append(ConsumoEmpaque(
            descripcion=ref,
            consumo_produccion=round(c, 2),
            desperdicio=round(d_emp, 2),
            desperdicio_fardo=round(d_far, 2),
            consumo_total=round(c + d_emp + d_far, 2),
            porcentaje_desperdicio=round(d_emp / c * 100, 2) if c > 0 else 0,
            porcentaje_desperdicio_fardo=round(d_far / c * 100, 2) if c > 0 else 0,
        ))

    rots = db.query(RegistroRotulado).filter(RegistroRotulado.fecha == fecha).all()
    total_fechados = sum(len(r.filas) for r in rots)
    fechados_ok = sum(1 for r in rots for f in r.filas if f.fechado_cumple == 'SI')
    fechados_no = total_fechados - fechados_ok

    pct_desp_emp = round(total_desp_emp / total_consumido * 100, 2) if total_consumido > 0 else 0
    pct_desp_far = round(total_desp_fardo / total_consumido * 100, 2) if total_consumido > 0 else 0

    prod_maiz = ProductividadOut(
        tipo='maiz', meta_valor=META_KG_MAIZ, meta_unidad='kg',
        logrado=round(total_consumido, 1),
        pct_meta=round(total_consumido / META_KG_MAIZ * 100, 1),
        cumple_meta=total_consumido >= META_KG_MAIZ,
        total_pacas=round(total_pacas_maiz, 1), divisor_usado=20,
        nota_meta='Kg consumidos todas las máquinas de maíz del turno'
    )
    todos_trigo_dia = db.query(RegistroBobinas).filter(RegistroBobinas.fecha == fecha).all()
    pacas_trigo_dia = 0.0
    for r in todos_trigo_dia:
        if _es_trigo(r.maquina or ''):
            filas_r = r.filas
            c_a = max([f.contador for f in filas_r if f.maquina_grupo == 'A' and f.contador], default=0)
            c_b = max([f.contador for f in filas_r if f.maquina_grupo == 'B' and f.contador], default=0)
            div_r = _get_divisor(r.referencia_producto or '')
            pacas_trigo_dia += round((c_a + c_b) / div_r, 1) if div_r > 0 else 0

    prod_trigo = ProductividadOut(
        tipo='trigo', meta_valor=META_PACAS_TRIGO, meta_unidad='pacas',
        logrado=round(pacas_trigo_dia, 1),
        pct_meta=round(pacas_trigo_dia / META_PACAS_TRIGO * 100, 1),
        cumple_meta=pacas_trigo_dia >= META_PACAS_TRIGO,
        total_pacas=round(total_pacas_trigo, 1), divisor_usado=25,
        nota_meta='Pacas acumuladas T1+T2 todas las máquinas de trigo'
    )

    return InformeGeneralOut(
        fecha=fecha, turno=turno,
        turno_label=TURNO_LABELS.get(turno, turno),
        maquinas_activas=maquinas_activas,
        total_unidades_maiz=total_un_maiz,
        total_pacas_maiz=round(total_pacas_maiz, 1),
        total_unidades_trigo=total_un_trigo,
        total_pacas_trigo=round(total_pacas_trigo, 1),
        consumo_empaque=consumo_empaque,
        total_consumido_kg=round(total_consumido, 2),
        total_desperdicio_empaque_kg=round(total_desp_emp, 2),
        total_desperdicio_fardo_kg=round(total_desp_fardo, 2),
        pct_desperdicio_empaque=pct_desp_emp,
        pct_desperdicio_fardo=pct_desp_far,
        total_fechados=total_fechados,
        fechados_cumplen=fechados_ok,
        fechados_no_cumplen=fechados_no,
        productividad_maiz=prod_maiz,
        productividad_trigo=prod_trigo,
        registros_incluidos=registros_ids,
        generado_en=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )


def _buscar_planillas_enlazadas(r: RegistroBobinas, db: Session):
    """Dado un registro de Bobinas, busca los registros de Rotulado, Pesos y
    Pesos Enfardadora del MISMO turno/máquina. Puede haber 1 o 2 ids por
    formato (Rotulado/Pesos), según si la máquina es pareja; Pesos
    Enfardadora se busca por el código de línea completo (ej. "1P-2Q"),
    porque esa planilla no tiene máquina propia — usa la pareja."""
    codigos_maquina = [c.strip() for c in (r.maquina or '').split('-') if c.strip()]

    regs_rot = db.query(RegistroRotulado).filter(
        RegistroRotulado.fecha == r.fecha, RegistroRotulado.turno == r.turno,
        RegistroRotulado.maquina.in_(codigos_maquina)
    ).all()
    regs_p = db.query(RegistroPesos).filter(
        RegistroPesos.fecha == r.fecha, RegistroPesos.turno == r.turno,
        RegistroPesos.maquina.in_(codigos_maquina)
    ).all()
    regs_enf = db.query(RegistroPesoEnfardadora).filter(
        RegistroPesoEnfardadora.fecha == r.fecha, RegistroPesoEnfardadora.turno == r.turno,
        RegistroPesoEnfardadora.maquinas == (r.maquina or '')
    ).all()
    return regs_rot, regs_p, regs_enf


@router.get("/{registro_id}/enlaces", response_model=EnlacesPlanillaOut)
def enlaces_planilla(registro_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Dado el id de un registro de Bobinas, encuentra los ids reales de las
    planillas relacionadas del MISMO turno — para poder abrir desde el panel
    admin la planilla exacta de cada uno (no solo el informe resumido)."""
    r = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    regs_rot, regs_p, regs_enf = _buscar_planillas_enlazadas(r, db)

    return EnlacesPlanillaOut(
        bobinas_id=r.id,
        rotulado_ids=[reg.id for reg in regs_rot],
        pesos_ids=[reg.id for reg in regs_p],
        pesos_enfardadora_ids=[reg.id for reg in regs_enf],
    )


def _generar_y_enviar_pdfs(
    admin: Usuario, pro_numero: str, lote: str,
    r: RegistroBobinas, regs_rot, regs_p, regs_enf,
) -> tuple[bool, str]:
    """Renderiza el PDF real de las 4 planillas (server-side, mismo diseño de
    siempre). Si hay un flujo de n8n configurado, lo usa (sube directo a la
    carpeta de Teams); si no, manda las planillas por correo al canal de
    Teams configurado. Si ninguno está configurado todavía, o algo falla, no
    revienta la asignación de PRO/lote — solo se informa que no se pudo
    enviar."""
    if not n8n_configurado() and not email_configurado():
        return False, "El envío automático no está configurado todavía (falta N8N_WEBHOOK_URL o los datos SMTP)."
    try:
        token = create_token({"sub": admin.username, "rol": admin.rol})
        archivos = [
            (nombre_archivo('bobinas', pro_numero, lote), render_planilla_pdf('bobinas', r.id, token)),
        ]
        for reg in regs_rot:
            archivos.append((nombre_archivo('rotulado', pro_numero, lote), render_planilla_pdf('rotulado', reg.id, token)))
        for reg in regs_p:
            archivos.append((nombre_archivo('pesos', pro_numero, lote), render_planilla_pdf('pesos', reg.id, token)))
        for reg in regs_enf:
            archivos.append((nombre_archivo('pesos-enfardadora', pro_numero, lote), render_planilla_pdf('pesos-enfardadora', reg.id, token)))

        if n8n_configurado():
            enviar_pdfs_a_n8n(pro_numero, lote, archivos)
        else:
            enviar_pdfs_exportacion(pro_numero, lote, archivos)
        return True, ""
    except Exception as e:
        return False, str(e)


@router.put("/{registro_id}/asignar-exportacion", response_model=AsignarExportacionOut)
def asignar_exportacion(
    registro_id: int, payload: AsignarExportacionIn,
    db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)
):
    """Asigna el número de PRO y el lote de exportación a las 4 planillas de un
    turno/máquina de una sola vez (Bobinas/Control de Empaque, Rotulado,
    Pesos, Pesos Enfardadora), genera el PDF real de cada una y las manda por
    correo al canal de Teams de exportación."""
    r = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    regs_rot, regs_p, regs_enf = _buscar_planillas_enlazadas(r, db)

    r.pro_numero = payload.pro_numero
    r.lote = payload.lote
    for reg in [*regs_rot, *regs_p, *regs_enf]:
        reg.pro_numero = payload.pro_numero
        reg.lote = payload.lote
    db.commit()

    correo_enviado, correo_error = (False, "")
    if payload.pro_numero or payload.lote:
        correo_enviado, correo_error = _generar_y_enviar_pdfs(admin, payload.pro_numero, payload.lote, r, regs_rot, regs_p, regs_enf)

    return AsignarExportacionOut(
        bobinas_id=r.id,
        rotulado_ids=[reg.id for reg in regs_rot],
        pesos_ids=[reg.id for reg in regs_p],
        pesos_enfardadora_ids=[reg.id for reg in regs_enf],
        pro_numero=payload.pro_numero, lote=payload.lote,
        correo_enviado=correo_enviado, correo_error=correo_error,
    )


@router.post("/{registro_id}/reenviar-exportacion", response_model=AsignarExportacionOut)
def reenviar_exportacion(registro_id: int, db: Session = Depends(get_db), admin: Usuario = Depends(require_admin)):
    """Vuelve a generar y mandar por correo los PDF de exportación de este
    turno/máquina, usando el PRO/lote que ya tenía asignado — para cuando el
    primer envío falló (por ejemplo, antes de terminar de configurar el
    correo) y hay que reintentarlo."""
    r = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    if not r.pro_numero and not r.lote:
        raise HTTPException(status_code=400, detail="Este turno todavía no tiene PRO/lote asignado")

    regs_rot, regs_p, regs_enf = _buscar_planillas_enlazadas(r, db)
    correo_enviado, correo_error = _generar_y_enviar_pdfs(admin, r.pro_numero or "", r.lote or "", r, regs_rot, regs_p, regs_enf)

    return AsignarExportacionOut(
        bobinas_id=r.id,
        rotulado_ids=[reg.id for reg in regs_rot],
        pesos_ids=[reg.id for reg in regs_p],
        pesos_enfardadora_ids=[reg.id for reg in regs_enf],
        pro_numero=r.pro_numero or "", lote=r.lote or "",
        correo_enviado=correo_enviado, correo_error=correo_error,
    )


@router.get("/{registro_id}", response_model=InformeTurnoDetalleOut)
def informe_detalle(registro_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    """Informe detallado de una máquina específica."""
    r = db.query(RegistroBobinas).filter(RegistroBobinas.id == registro_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    filas = r.filas
    es_trigo = _es_trigo(r.maquina or '')
    divisor = _get_divisor(r.referencia_producto or '')

    grupos: dict = {}
    for f in filas:
        g = f.maquina_grupo
        if g not in grupos:
            grupos[g] = {'contadores': [], 'referencias': [], 'consumido': 0}
        if f.contador: grupos[g]['contadores'].append(f.contador)
        if f.referencia_empaque: grupos[g]['referencias'].append(f.referencia_empaque)
        grupos[g]['consumido'] += f.consumido or 0

    filas_maquinas = [FilaInformeOut(
        maquina=g, operario=r.nombre_operario or '',
        contador_final=max(d['contadores']) if d['contadores'] else 0,
        fardos_enfardadora=0,
        referencias=list(set(d['referencias'])),
    ) for g, d in grupos.items()]

    cnt_a = max([f.contador for f in filas if f.maquina_grupo == 'A' and f.contador], default=0)
    cnt_b = max([f.contador for f in filas if f.maquina_grupo == 'B' and f.contador], default=0)
    cnt_enf = max([f.contador for f in filas if f.maquina_grupo == 'ENF' and f.contador], default=0)
    total_un = cnt_a + cnt_b
    total_pacas = round(total_un / divisor, 1) if divisor > 0 else 0
    consumido_total = sum(f.consumido or 0 for f in filas)
    desp_emp = r.peso_desperdicio or 0
    desp_fardo = getattr(r, 'peso_desperdicio_fardo', 0) or 0

    refs_agrupadas: dict = {}
    for f in filas:
        ref = f.referencia_empaque or 'Sin referencia'
        if ref not in refs_agrupadas: refs_agrupadas[ref] = {'consumo': 0}
        refs_agrupadas[ref]['consumo'] += f.consumido or 0

    consumo_empaque = []
    for ref, datos in refs_agrupadas.items():
        c = datos['consumo']
        prop = c / consumido_total if consumido_total > 0 else 0
        d_e = desp_emp * prop; d_f = desp_fardo * prop
        consumo_empaque.append(ConsumoEmpaque(
            descripcion=ref, consumo_produccion=round(c, 2),
            desperdicio=round(d_e, 2), desperdicio_fardo=round(d_f, 2),
            consumo_total=round(c + d_e + d_f, 2),
            porcentaje_desperdicio=round(d_e / c * 100, 2) if c > 0 else 0,
            porcentaje_desperdicio_fardo=round(d_f / c * 100, 2) if c > 0 else 0,
        ))

    todos_dia = db.query(RegistroBobinas).filter(RegistroBobinas.fecha == r.fecha).all()
    if es_trigo:
        pacas_dia = sum(
            round((max([f.contador for f in rd.filas if f.maquina_grupo=='A' and f.contador], default=0) +
                   max([f.contador for f in rd.filas if f.maquina_grupo=='B' and f.contador], default=0)) /
                  _get_divisor(rd.referencia_producto or ''), 1)
            for rd in todos_dia if _es_trigo(rd.maquina or '')
        )
        prod = {'tipo':'trigo','meta_valor':META_PACAS_TRIGO,'meta_unidad':'pacas',
                'logrado':round(pacas_dia,1),'pct_meta':round(pacas_dia/META_PACAS_TRIGO*100,1),
                'cumple_meta':pacas_dia>=META_PACAS_TRIGO,'total_pacas':total_pacas,
                'divisor_usado':divisor,'nota_meta':'Acumulado T1+T2 todas las máquinas de trigo'}
    else:
        kg_dia = sum(sum(f.consumido or 0 for f in rd.filas)
                     for rd in todos_dia if not _es_trigo(rd.maquina or ''))
        prod = {'tipo':'maiz','meta_valor':META_KG_MAIZ,'meta_unidad':'kg',
                'logrado':round(kg_dia,1),'pct_meta':round(kg_dia/META_KG_MAIZ*100,1),
                'cumple_meta':kg_dia>=META_KG_MAIZ,'total_pacas':total_pacas,
                'divisor_usado':divisor,'nota_meta':'Acumulado del día todas las máquinas de maíz'}

    codigos_maquina = [c.strip() for c in (r.maquina or '').split('-') if c.strip()]

    regs_rot = db.query(RegistroRotulado).filter(
        RegistroRotulado.fecha == r.fecha,
        RegistroRotulado.maquina.in_(codigos_maquina)
    ).all()
    total_f = sum(len(reg.filas) for reg in regs_rot)
    ok_f = sum(1 for reg in regs_rot for f in reg.filas if f.fechado_cumple == 'SI')

    regs_p = db.query(RegistroPesos).filter(
        RegistroPesos.fecha == r.fecha,
        RegistroPesos.maquina.in_(codigos_maquina)
    ).all()
    muestras = sum(
        1 for reg in regs_p for fp in reg.filas
        for m in [fp.muestra_1, fp.muestra_2, fp.muestra_3, fp.muestra_4, fp.muestra_5]
        if m is not None
    )

    pct_e = round(desp_emp/consumido_total*100,2) if consumido_total>0 else 0
    pct_f = round(desp_fardo/consumido_total*100,2) if consumido_total>0 else 0

    return InformeTurnoDetalleOut(
        id=r.id, fecha=r.fecha or '', turno=r.turno or '',
        turno_label=TURNO_LABELS.get(r.turno or '', r.turno or ''),
        maquina=r.maquina or '', operario=r.nombre_operario or '',
        filas_maquinas=filas_maquinas,
        total_produccion_maquinas={'empacadoras_AB':total_un,'enfardadora':cnt_enf,'total_pacas':total_pacas,'divisor':divisor},
        productividad=prod,
        total_fechados=total_f, fechados_cumplen=ok_f, fechados_no_cumplen=total_f-ok_f,
        consumo_empaque=consumo_empaque,
        total_consumido_kg=round(consumido_total,2),
        total_desperdicio_kg=round(desp_emp,2),
        total_desperdicio_fardo_kg=round(desp_fardo,2),
        porcentaje_desperdicio_global=pct_e,
        porcentaje_desperdicio_fardo=pct_f,
        total_muestras_pesos=muestras,
        generado_en=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    )