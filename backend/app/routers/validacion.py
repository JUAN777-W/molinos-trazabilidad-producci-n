from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from app.database import get_db
from app.models.models import RegistroBobinas, RegistroRotulado, RegistroPesos
from app.auth import get_current_user

router = APIRouter()


class ConflictoTurno(BaseModel):
    formato: str          # "Bobinas" | "Rotulado" | "Pesos"
    id: int
    turno: str
    maquina: str
    operario: str


class ValidacionTurnoOut(BaseModel):
    consistente: bool
    mensaje: str
    conflictos: List[ConflictoTurno]


@router.get("/turno", response_model=ValidacionTurnoOut)
def validar_turno(
    fecha: str = Query(...),
    maquina: str = Query(...),
    turno: str = Query(...),
    excluir_formato: Optional[str] = Query(None, description="Formato que se está guardando, para no comparar contra sí mismo"),
    excluir_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Verifica que, para la misma fecha y máquina, no exista ya un registro en
    Bobinas, Rotulado o Pesos con un turno DIFERENTE. Esto evita que los 3
    formatos de un mismo turno queden con datos contradictorios (lo cual
    rompería los informes por planilla y por mes).

    La comparación de máquina es por contención (ilike), no igualdad exacta,
    porque Bobinas puede guardar la máquina en pareja (ej. "9X-8S") mientras
    que Rotulado y Pesos solo guardan una máquina individual (ej. "9X").
    """
    conflictos: List[ConflictoTurno] = []

    # ── Bobinas ──────────────────────────────────────────────────────────────
    q = db.query(RegistroBobinas).filter(
        RegistroBobinas.fecha == fecha, RegistroBobinas.maquina.ilike(f"%{maquina}%")
    )
    if excluir_formato == "Bobinas" and excluir_id:
        q = q.filter(RegistroBobinas.id != excluir_id)
    for r in q.all():
        if r.turno and r.turno != turno:
            conflictos.append(ConflictoTurno(
                formato="Bobinas", id=r.id, turno=r.turno,
                maquina=r.maquina or "", operario=r.nombre_operario or "",
            ))

    # ── Rotulado ─────────────────────────────────────────────────────────────
    q = db.query(RegistroRotulado).filter(
        RegistroRotulado.fecha == fecha, RegistroRotulado.maquina.ilike(f"%{maquina}%")
    )
    if excluir_formato == "Rotulado" and excluir_id:
        q = q.filter(RegistroRotulado.id != excluir_id)
    for r in q.all():
        if r.turno and r.turno != turno:
            conflictos.append(ConflictoTurno(
                formato="Rotulado", id=r.id, turno=r.turno,
                maquina=r.maquina or "", operario=r.nombre_operario or "",
            ))

    # ── Pesos ────────────────────────────────────────────────────────────────
    q = db.query(RegistroPesos).filter(
        RegistroPesos.fecha == fecha, RegistroPesos.maquina.ilike(f"%{maquina}%")
    )
    if excluir_formato == "Pesos" and excluir_id:
        q = q.filter(RegistroPesos.id != excluir_id)
    for r in q.all():
        if r.turno and r.turno != turno:
            conflictos.append(ConflictoTurno(
                formato="Pesos", id=r.id, turno=r.turno,
                maquina=r.maquina or "", operario=r.nombre_operario or "",
            ))

    if conflictos:
        detalles = "; ".join(
            f"{c.formato} (máq. {c.maquina}, operario {c.operario}) tiene Turno {c.turno}"
            for c in conflictos
        )
        return ValidacionTurnoOut(
            consistente=False,
            mensaje=f"Hay otro formato para esta fecha y máquina con un turno distinto: {detalles}. "
                    f"Verifica que estás usando el turno correcto antes de guardar.",
            conflictos=conflictos,
        )

    return ValidacionTurnoOut(consistente=True, mensaje="Consistente", conflictos=[])