"""
Script de siembra: carga el catálogo de referencias de empaque (trigo y maíz)
extraído de la pestaña CONTROL INV del Excel de bodega (Mov_Bodega_Empaque_FR1.xlsm).

Ejecutar UNA SOLA VEZ desde la carpeta backend/:
    python seed_referencias_empaque.py

Es seguro volver a correrlo: si el código ya existe, lo actualiza en vez de duplicarlo.
"""
from app.database import SessionLocal
from app.models.models import ReferenciaEmpaque

# (codigo, descripcion, categoria, promedio_bobina_kg)
SEED_REFERENCIAS = [
    ('10-20-1', 'EMP PAPEL PANADERIA NIEVE 50KG', 'TRIGO', 2435),
    ('10-20-11', 'EMP SUBPRODUCTOS FRANJA AZUL', 'TRIGO', None),
    ('10-20-19', 'EMP PAPEL REPOSTERIA 50K', 'TRIGO', 95.45),
    ('10-20-2', 'EMP PAPEL PANADERIA NIEVE 12.5KG', 'TRIGO', 99.83),
    ('10-20-21', 'EMP PAPEL REPOSTERIA 25KG', 'TRIGO', 83.47),
    ('10-20-24', 'EMP POLI PANADERIA NIEVE 25KG', 'TRIGO', None),
    ('10-20-3', 'EMP POLI NIEVE 50KG', 'TRIGO', 5312.5),
    ('10-20-5', 'EMP TRIGO TRADICIONAL 1000GR', 'TRIGO', 23.89),
    ('10-20-54', 'EMP PAPEL PANADERIA NIEVE 25KG', 'TRIGO', 93.81),
    ('10-20-6', 'EMP TRIGO TRADICIONAL 500GR', 'TRIGO', 24.71),
    ('10-20-61', 'EMP REPOSTERIA PREMIUM 50 K', 'TRIGO', 108.7),
    ('10-20-62', 'EMP REPOSTERIA PREMIUM 25 KL', 'TRIGO', 98.92),
    ('10-20-64', 'EMP LAMINA HNA TRIGO QUICKSY 500GR', 'TRIGO', 24.17),
    ('10-20-65', 'EMP LAMINADO TRIGO LEUDANTE QUICKSY 500GR', 'TRIGO', None),
    ('10-20-66', 'EMP LAMINA TRIGO DEL COSTAL 500 G CALOR CONST', 'TRIGO', 25.39),
    ('10-20-67', 'EMP SUBPRODUCTOS FRANJA ROJA', 'TRIGO', 288.19),
    ('10-20-68', 'EMP SUBPRODUCTOS FRANJA AMARILLA', 'TRIGO', 481.48),
    ('10-20-7', 'EMP TRIGO LEUDANTE 1000GR', 'TRIGO', 24.26),
    ('10-20-8', 'EMP TRIGO LEUDANTE 500GR', 'TRIGO', 24.1),
    ('10-20-9', 'REEMPAQUE KILO', 'TRIGO', 329.7),
    ('11-20-1', 'EMP POLI MAIZ 50KG', 'MAIZ', 856),
    ('11-20-10', 'REEMPAQUE LIBRA', 'MAIZ', 1111.72),
    ('11-20-19', 'EMP MAIZ BCO 1000 NAL ROVEMA', 'MAIZ', 23.3),
    ('11-20-20', 'EMP MAIZ BLANCO MASAPAN NAL ROVEMA', 'MAIZ', 33.2),
    ('11-20-21', 'EMP MAIZ AMARILLO 1000G NAL ROVEMA', 'MAIZ', 23.99),
    ('11-20-25', 'EMP MAIZ BLANCO 250GR', 'MAIZ', 23.7),
    ('11-20-3', 'EMP MAIZ AMARILLO 500GR', 'MAIZ', 24.4),
    ('11-20-5', 'EMP MAIZ BLANCO 1000GR', 'MAIZ', 24.86),
    ('11-20-57', 'EMP MAIZ BLANCO 500GR MANTEQUILLA Y SAL', 'MAIZ', 28.86),
    ('11-20-59', 'EMP LAM MANTEQUILLA SAL KL EXPORTACION PANAMA', 'MAIZ', 19.37),
    ('11-20-6', 'EMP MAIZ BL. LAM EXPO PANAMA 1000KG', 'MAIZ', 29.12),
    ('11-20-61', 'EMP MASAPAN LIBRA', 'MAIZ', 21.7),
    ('11-20-62', 'EMP MASAPAN 1000 GMS ALMOHADILLA', 'MAIZ', 23.5),
    ('11-20-63', 'EMP FARDO X93 CM LIBRA', 'MAIZ', 50.94),
    ('11-20-64', 'EMP FARDO X 112 CM KILO', 'MAIZ', 49.28),
    ('11-20-65', 'EMP MAIZ AMARLLO 1000 GMS', 'MAIZ', 24.89),
    ('11-20-66', 'EMP MAIZ AMARILLO EXP 1000 CATEDRAL PANAMA', 'MAIZ', 20.79),
    ('11-20-70', 'EMP MAIZ BLANCO 20 K MAS X MENOS ROVEMA NACIONAL', 'MAIZ', 24.33),
    ('11-20-72', 'EMP MAIZ BCO EXP 1000G DISTRISANDER CATEDRAL', 'MAIZ', 23.21),
    ('11-20-73', 'EMP MAIZ B ALMO DISTRISANDER 1000GRM', 'MAIZ', 25.55),
    ('11-20-75', 'RL 128 CM TERMOENCOGIBLE TUBULAR', 'MAIZ', 35.43),
    ('11-20-76', 'EMP HNA MAIZ BLANCO QUICKSY 1000 GR NO ROVEMA', 'MAIZ', 25.25),
    ('11-20-77', 'EMP MAIZ AMARILLO 1000 GR QUICKSY NO ROVEMA', 'MAIZ', 24.12),
    ('11-20-79', 'EMP HNA PREC MAIZ BCO DEL COSTAL 1000 GRARA', 'MAIZ', None),
    ('11-20-80', 'EMP HNA MAIZ BLANCO 2.5KG ROVEMA', 'MAIZ', 23.19),
    ('11-20-83', 'EMP PREC BLANCA 1010G NEW BRAZ.', 'MAIZ', 24.75),
    ('11-20-84', 'EMP MAIZ BLANCO 500GR CATEDRA', 'MAIZ', 24.05),
    ('11-20-85', 'EMP MAIZ BLANCO EXP 1000GR ROVEMA USA', 'MAIZ', 22.66),
    ('11-20-86', 'EMP PREC BLANCA LA COMADRE 1000G', 'MAIZ', 25.19),
    ('11-20-87', 'EMP PREC AMARILLA LA COMADRE 1000G', 'MAIZ', 24.62),
    ('11-20-9', 'REEMPAQUE MAIZ KILO', 'MAIZ', 334.78),
    ('4-1-6', 'HILO GRANDE', 'TRIGO', 1),
    ('4-2-14', 'ROLLO HNA MAIZ BCO PANAMA 2.5 KL EXP ROV', 'MAIZ', 23.98),
]

def run():
    db = SessionLocal()
    creados, actualizados = 0, 0
    try:
        for codigo, descripcion, categoria, promedio_bobina_kg in SEED_REFERENCIAS:
            existente = db.query(ReferenciaEmpaque).filter(ReferenciaEmpaque.codigo == codigo).first()
            if existente:
                existente.descripcion = descripcion
                existente.categoria = categoria
                existente.promedio_bobina_kg = promedio_bobina_kg
                actualizados += 1
            else:
                db.add(ReferenciaEmpaque(
                    codigo=codigo,
                    descripcion=descripcion,
                    categoria=categoria,
                    promedio_bobina_kg=promedio_bobina_kg,
                    activo="SI",
                ))
                creados += 1
        db.commit()
        print(f"Listo. Referencias creadas: {creados}, actualizadas: {actualizados}, total: {len(SEED_REFERENCIAS)}")
    finally:
        db.close()


if __name__ == "__main__":
    run()