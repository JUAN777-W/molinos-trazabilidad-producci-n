from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database import get_db
from app.models.models import RegistroEstiba, RegistroBobinas, ReferenciaEmpaque
from app.schemas.estiba_schemas import InfoMaquinaOut, RegistroEstibaCreate, RegistroEstibaOut
from app.auth import get_current_user

router = APIRouter()

MAQUINAS_TRIGO = {'8S', '9X', '10Y', '11Z'}


def _siguiente_numero(db: Session, fecha: str, turno: str, maquina: str) -> int:
    ultimo = db.query(RegistroEstiba).filter(
        RegistroEstiba.fecha == fecha, RegistroEstiba.turno == turno, RegistroEstiba.maquina == maquina
    ).order_by(RegistroEstiba.numero_estiva.desc()).first()
    return (ultimo.numero_estiva + 1) if ultimo else 1


# ─── PÚBLICO — sin login, para el operario de montacargas de la cooperativa ──
@router.get("/info-maquina/{maquina}", response_model=InfoMaquinaOut)
def info_maquina(
    maquina: str, turno: str = Query(...),
    db: Session = Depends(get_db),
):
    """Dado el QR fijo de una máquina y el turno que elige el operario, sugiere
    automáticamente la referencia que está corriendo ahí (tomada del último
    registro de Bobinas de ese turno) y el próximo número de estiva."""
    hoy = date.today().strftime('%Y-%m-%d')

    registro = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha == hoy, RegistroBobinas.turno == turno,
        RegistroBobinas.maquina.ilike(f"%{maquina}%"),
    ).order_by(RegistroBobinas.id.desc()).first()

    referencia_codigo = registro.referencia_producto if registro else None
    referencia_label = None
    tipo = 'TRIGO' if maquina.upper() in MAQUINAS_TRIGO else 'MAIZ'

    if referencia_codigo:
        ref = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.codigo == referencia_codigo).first()
        if ref:
            referencia_label = ref.descripcion
            tipo = ref.categoria or tipo

    return InfoMaquinaOut(
        maquina=maquina.upper(), turno=turno, fecha=hoy,
        referencia_producto=referencia_codigo, referencia_label=referencia_label,
        siguiente_numero_estiva=_siguiente_numero(db, hoy, turno, maquina.upper()),
        tipo=tipo,
    )


@router.post("/estibas", response_model=RegistroEstibaOut, status_code=201)
def crear_estiba(payload: RegistroEstibaCreate, db: Session = Depends(get_db)):
    """Sin login — lo llena el operario de montacargas de la cooperativa desde
    el celular, escaneando el QR fijo de la máquina."""
    numero = _siguiente_numero(db, payload.fecha, payload.turno, payload.maquina.upper())
    registro = RegistroEstiba(
        fecha=payload.fecha, turno=payload.turno, maquina=payload.maquina.upper(),
        numero_estiva=numero, referencia_producto=payload.referencia_producto,
        cantidad_pacas=payload.cantidad_pacas, plancha=payload.plancha, alto=payload.alto,
        nombre_operario_montacargas=payload.nombre_operario_montacargas,
    )
    db.add(registro)
    db.commit()
    db.refresh(registro)
    return registro


# ─── PROTEGIDO — para el encargado de bodega, dentro del panel admin ─────────
@router.get("/estibas", response_model=List[RegistroEstibaOut])
def listar_estibas(
    fecha: Optional[str] = Query(None),
    turno: Optional[str] = Query(None),
    maquina: Optional[str] = Query(None),
    db: Session = Depends(get_db), _=Depends(get_current_user),
):
    q = db.query(RegistroEstiba)
    if fecha:
        q = q.filter(RegistroEstiba.fecha == fecha)
    if turno:
        q = q.filter(RegistroEstiba.turno == turno)
    if maquina:
        q = q.filter(RegistroEstiba.maquina == maquina.upper())
    return q.order_by(RegistroEstiba.fecha.desc(), RegistroEstiba.id.desc()).all()
