import os
import io
import base64
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
# OCR con Tesseract (gratis, local) — solo LEE el texto de la foto del
# fechado, no decide si cumple o no. Esa decisión la sigue tomando el
# operario a mano, con su propio botón de SI/NO en la pantalla.
#
# Requiere tener Tesseract-OCR instalado en el computador (ver instrucciones
# de instalación). Si no está en el PATH del sistema, se puede indicar la
# ruta exacta con la variable de entorno TESSERACT_CMD en el archivo .env,
# por ejemplo: TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
# ─────────────────────────────────────────────────────────────────────────────
try:
    import pytesseract
    from PIL import Image

    _tesseract_cmd = os.getenv("TESSERACT_CMD")
    if _tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = _tesseract_cmd

    _OCR_DISPONIBLE = True
except ImportError:
    _OCR_DISPONIBLE = False


class VisionRequest(BaseModel):
    image_base64: str   # data:image/jpeg;base64,....
    vida_meses: int = 0
    ref_label: str = ""


@router.post("/analizar-fechado")
async def analizar_fechado(req: VisionRequest):
    if not _OCR_DISPONIBLE:
        raise HTTPException(
            status_code=500,
            detail="Tesseract/pytesseract no está instalado en este servidor. "
                   "Corre: pip install pytesseract pillow, e instala Tesseract-OCR."
        )

    try:
        _, b64data = req.image_base64.split(",", 1)
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de imagen inválido")

    try:
        img_bytes = base64.b64decode(b64data)
        imagen = Image.open(io.BytesIO(img_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="No se pudo abrir la imagen recibida")

    try:
        # PSM 6 = "asume un solo bloque de texto uniforme" — respeta mejor
        # los saltos de línea reales del sello (3 líneas: lote, hora, vencimiento)
        # en vez de intentar adivinar columnas/párrafos y mezclarlo todo en una.
        texto = pytesseract.image_to_string(imagen, lang="spa+eng", config="--psm 6").strip()
        # Quita líneas vacías que a veces deja Tesseract entre renglones
        texto = "\n".join(linea.strip() for linea in texto.splitlines() if linea.strip())
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tesseract no pudo leer la imagen — revisa que esté bien instalado. Detalle: {e}"
        )

    if not texto:
        return {
            "fechado_texto": "",
            "cumple": None,
            "motivo": "No se detectó texto en la foto — repite la toma con mejor luz/enfoque, o escribe el texto a mano.",
        }

    return {
        "fechado_texto": texto,
        "cumple": None,  # el operario decide, la IA solo lee el texto
        "motivo": "Texto leído automáticamente — verifica que sea correcto y confirma si cumple.",
    }