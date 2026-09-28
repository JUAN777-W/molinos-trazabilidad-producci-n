"""Envía los PDF de exportación al flujo de n8n, que es quien los sube a la
carpeta de Teams — reemplaza la necesidad de una cuenta de correo/contraseña
de aplicación de Microsoft 365 para este envío.

Requiere esta variable en el .env — mientras esté vacía, el envío se omite
igual que con el correo (ver email_sender.py):
  N8N_WEBHOOK_URL=http://localhost:5678/webhook-test/exportacion-pdf
"""
import os
import urllib.request
import uuid

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "")


def envio_configurado() -> bool:
    return bool(N8N_WEBHOOK_URL)


def _build_multipart(fields: dict, archivos: list[tuple[str, bytes]]) -> tuple[bytes, str]:
    boundary = uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    for i, (nombre_archivo, contenido) in enumerate(archivos):
        parts.append(
            (f'--{boundary}\r\nContent-Disposition: form-data; name="archivo_{i}"; '
             f'filename="{nombre_archivo}"\r\nContent-Type: application/pdf\r\n\r\n').encode()
            + contenido + b'\r\n'
        )
    parts.append(f'--{boundary}--\r\n'.encode())
    body = b''.join(parts)
    return body, f'multipart/form-data; boundary={boundary}'


def enviar_pdfs_a_n8n(pro_numero: str, lote: str, archivos: list[tuple[str, bytes]]) -> None:
    """archivos: lista de (nombre_archivo, contenido_pdf). Lanza excepción si falla."""
    if not envio_configurado():
        raise RuntimeError("Envío a n8n no configurado (falta N8N_WEBHOOK_URL en .env)")

    body, content_type = _build_multipart({"pro_numero": pro_numero, "lote": lote}, archivos)
    req = urllib.request.Request(N8N_WEBHOOK_URL, data=body, method="POST", headers={"Content-Type": content_type})
    with urllib.request.urlopen(req, timeout=60) as resp:
        if resp.status >= 300:
            raise RuntimeError(f"n8n respondió con estado {resp.status}")
