"""Genera el PDF real de una planilla ya guardada, en el propio servidor —
en vez de depender de que alguien use "Guardar como PDF" en el diálogo de
impresión del navegador. Para que el PDF se vea idéntico al que ya conocen
los operarios, no se rearma el diseño en Python: se abre la misma pantalla
de la aplicación (en modo solo lectura, "?verId=") con un navegador sin
interfaz (Chromium vía Playwright) y se imprime esa página tal cual,
reusando el mismo HTML/CSS de siempre.
"""
import os
import json
from playwright.sync_api import sync_playwright

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200")

# Debe calzar con las etiquetas que ya usan en las carpetas de exportación.
TIPO_LABELS = {
    'bobinas': 'CONTROL DE EMPAQUE',
    'rotulado': 'ROTULADO Y SELLADO',
    'pesos': 'CONTROL DE PESO',
    'pesos-enfardadora': 'CONTROL DE PESO ENFARDADORA',
}


def nombre_archivo(tipo: str, pro_numero: str, lote: str) -> str:
    etiqueta = TIPO_LABELS.get(tipo, tipo.upper())
    partes = [etiqueta]
    if pro_numero:
        partes.append(f"PRO{pro_numero}")
    if lote:
        partes.append(f"LOTE {lote}")
    return " - ".join(partes) + ".pdf"


def render_planilla_pdf(tipo: str, registro_id: int, token: str) -> bytes:
    """Devuelve los bytes del PDF de una planilla ya guardada (tipo: 'bobinas',
    'rotulado', 'pesos' o 'pesos-enfardadora')."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            # Primero se entra a la app para poder guardar el token de sesión
            # en localStorage — recién ahí se navega a la planilla, porque el
            # interceptor de autenticación lo lee en cada petición.
            page.goto(FRONTEND_URL)
            page.evaluate("(t) => localStorage.setItem('token', t)", token)
            page.goto(f"{FRONTEND_URL}/{tipo}?verId={registro_id}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(400)  # margen para que Angular termine de pintar los datos
            page.emulate_media(media="print")
            pdf_bytes = page.pdf(
                print_background=True,
                margin={"top": "10mm", "bottom": "10mm", "left": "10mm", "right": "10mm"},
            )
            return pdf_bytes
        finally:
            browser.close()
