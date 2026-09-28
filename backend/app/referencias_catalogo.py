# Mismo catálogo de referencias que el frontend (bobinas/rotulado/pesos
# .component.ts) — si cambia allá, actualizar también aquí. Se usa para
# mostrar el nombre real de la referencia en reportes e informes, en vez del
# código interno (ej. "10-20-5") que no dice nada a quien lo lee.

REFERENCIA_LABELS = {
    # Trigo
    '10-20-5': 'EMP TRIGO TRADICIONAL 1000GR',
    '10-20-6': 'EMP TRIGO TRADICIONAL 500GR',
    '10-20-64': 'EMP LAMINA HNA TRIGO QUICKSY 500GR',
    '10-20-65': 'EMP LAMINADO TRIGO LEUDANTE QUICKSY 500GR',
    '10-20-66': 'EMP LAMINA TRIGO DEL COSTAL 500 G CALOR CONST',
    '10-20-7': 'EMP TRIGO LEUDANTE 1000GR',
    '10-20-8': 'EMP TRIGO LEUDANTE 500GR',
    # Maíz
    '11-20-19': 'EMP MAIZ BCO 1000 NAL ROVEMA',
    '11-20-20': 'EMP MAIZ BLANCO MASAPAN NAL ROVEMA',
    '11-20-21': 'EMP MAIZ AMARILLO 1000G NAL ROVEMA',
    '11-20-25': 'EMP MAIZ BLANCO 250GR',
    '11-20-3': 'EMP MAIZ AMARILLO 500GR',
    '11-20-5': 'EMP MAIZ BLANCO 1000GR',
    '11-20-57': 'EMP MAIZ BLANCO 500GR MANTEQUILLA Y SAL',
    '11-20-59': 'EMP LAM MANTEQUILLA SAL KL EXPORTACION PANAMA',
    '11-20-6': 'EMP MAIZ BL. LAM EXPO PANAMA 1000KG',
    '11-20-61': 'EMP MASAPAN LIBRA',
    '11-20-62': 'EMP MASAPAN 1000 GMS ALMOHADILLA',
    '11-20-65': 'EMP MAIZ AMARLLO 1000 GMS',
    '11-20-66': 'EMP MAIZ AMARILLO EXP 1000 CATEDRAL PANAMA',
    '11-20-72': 'EMP MAIZ BCO EXP 1000G DISTRISANDER CATEDRAL',
    '11-20-73': 'EMP MAIZ B ALMO DISTRISANDER 1000GRM',
    '11-20-76': 'EMP HNA MAIZ BLANCO QUICKSY 1000 GR NO ROVEMA',
    '11-20-77': 'EMP MAIZ AMARILLO 1000 GR QUICKSY NO ROVEMA',
    '11-20-79': 'EMP HNA PREC MAIZ BCO DEL COSTAL 1000 GRARA',
    '11-20-83': 'EMP PREC BLANCA 1010G NEW BRAZ.',
    '11-20-84': 'EMP MAIZ BLANCO 500GR CATEDRA',
    '11-20-85': 'EMP MAIZ BLANCO EXP 1000GR ROVEMA USA',
    '11-20-86': 'EMP PREC BLANCA LA COMADRE 1000G',
    '11-20-87': 'EMP PREC AMARILLA LA COMADRE 1000G',
}


def referencia_label(codigo: str) -> str:
    """Nombre legible de una referencia de producto. Si el código no está en
    el catálogo (o ya es texto libre), se devuelve tal cual llegó."""
    if not codigo:
        return codigo
    return REFERENCIA_LABELS.get(codigo.strip(), codigo)
