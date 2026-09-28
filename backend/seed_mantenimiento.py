"""
Script de siembra ÚNICA VEZ para el módulo de Mantenimiento.

Lee el archivo Plan_Mantenimiento_Preventivo_Correctivo_Empacadoras_Enfardadoras.xlsx
(debe estar en la misma carpeta que este script, dentro de backend/) y carga:
  - plan_preventivo          (50 actividades: 30 Empacadoras + 13 Enfardadoras + 7 Bandas/Sopladores)
  - cronograma_mantenimiento (99 puntos de control, todos arrancan "sin registrar")
  - historial_correctivo     (17 registros históricos 2017-2025)
  - repuesto_critico         (271 referencias)

Uso:
    cd backend
    python seed_mantenimiento.py

Es seguro correrlo una sola vez. Si se corre dos veces, va a duplicar los datos
(no tiene chequeo de "ya existe" porque está pensado como carga inicial única).
"""
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import openpyxl
from app.database import SessionLocal
from app.models.models import PlanPreventivo, CronogramaMantenimiento, HistorialCorrectivo, RepuestoCritico

ARCHIVO_EXCEL = "Plan_Mantenimiento_Preventivo_Correctivo_Empacadoras_Enfardadoras.xlsx"


def fecha_a_str(valor):
    """Convierte un datetime de openpyxl a 'YYYY-MM-DD', o None si está vacío."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.strftime('%Y-%m-%d')
    return str(valor)


def seed():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), ARCHIVO_EXCEL)
    if not os.path.exists(ruta):
        print(f"❌ No se encontró el archivo: {ruta}")
        print("   Copia el Excel del plan de mantenimiento a la carpeta backend/ con ese nombre exacto.")
        return

    wb = openpyxl.load_workbook(ruta, data_only=True)
    db = SessionLocal()

    total = {'plan': 0, 'cronograma': 0, 'historial': 0, 'repuestos': 0}

    try:
        # ── Planes preventivos (3 hojas -> 1 sola tabla con campo `linea`) ────
        hojas_plan = {
            'Plan Preventivo EMPACADORAS': 'EMPACADORAS',
            'Plan Preventivo ENFARDADORAS': 'ENFARDADORAS',
            'Plan Prev BANDAS-SOPLADORES': 'BANDAS_SOPLADORES',
        }
        for nombre_hoja, linea in hojas_plan.items():
            ws = wb[nombre_hoja]
            for row in ws.iter_rows(min_row=3, values_only=True):
                seccion = row[0]
                if not seccion:
                    continue
                db.add(PlanPreventivo(
                    linea=linea,
                    seccion_componente=str(seccion).strip(),
                    actividad=str(row[1] or '').strip(),
                    tipo=str(row[2] or '').strip(),
                    frecuencia=str(row[3] or '').strip(),
                    responsable=str(row[4] or '').strip(),
                    tiempo_min=int(row[5]) if row[5] is not None else None,
                    repuesto_insumo=str(row[6] or '').strip(),
                ))
                total['plan'] += 1

        # ── Cronograma y Registro (99 puntos de control) ──────────────────────
        ws = wb['Cronograma y Registro']
        for row in ws.iter_rows(min_row=3, values_only=True):
            maquina = row[0]
            if not maquina:
                continue
            db.add(CronogramaMantenimiento(
                maquina=str(maquina).strip(),
                seccion_componente=str(row[1] or '').strip(),
                frecuencia=str(row[2] or '').strip(),
                ultima_ejecucion=fecha_a_str(row[3]),
                observaciones=str(row[6] or '').strip() if row[6] else None,
            ))
            total['cronograma'] += 1

        # ── Historial Correctivo (17 registros originales) ────────────────────
        ws = wb['Historial Correctivo']
        for row in ws.iter_rows(min_row=3, values_only=True):
            maquina = row[0]
            # Saltar filas vacías, el texto instructivo, y el encabezado repetido
            if not maquina or 'Registre' in str(maquina) or maquina == 'Máquina':
                continue
            db.add(HistorialCorrectivo(
                maquina=str(maquina).strip(),
                equipo_componente=str(row[1] or '').strip(),
                fecha_mantenimiento=fecha_a_str(row[2]),
                fecha_cambio=fecha_a_str(row[3]),
                mantenimiento_realizado=str(row[4] or '').strip(),
                costo=float(row[5]) if row[5] is not None else None,
                estado_resultante=str(row[6] or '').strip(),
                hubo_cambio=str(row[7] or '').strip() if row[7] else None,
            ))
            total['historial'] += 1

        # ── Repuestos Críticos (271 referencias) ──────────────────────────────
        ws = wb['Repuestos Criticos']
        for row in ws.iter_rows(min_row=3, values_only=True):
            seccion = row[0]
            if not seccion:
                continue
            db.add(RepuestoCritico(
                seccion=str(seccion).strip(),
                componente=str(row[1] or '').strip(),
                referencia=str(row[2] or '').strip() if row[2] else None,
                marca=str(row[3] or '').strip() if row[3] else None,
                cantidad_instalada=int(row[4]) if row[4] is not None else None,
                maquinas_aplica=str(row[5] or '').strip(),
                stock_minimo_sugerido=int(row[6]) if row[6] is not None else None,
            ))
            total['repuestos'] += 1

        db.commit()
        print("✅ Siembra completada:")
        print(f"   Plan Preventivo:        {total['plan']} actividades")
        print(f"   Cronograma:             {total['cronograma']} puntos de control")
        print(f"   Historial Correctivo:   {total['historial']} registros")
        print(f"   Repuestos Críticos:     {total['repuestos']} referencias")

    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la siembra, se revirtió todo: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()