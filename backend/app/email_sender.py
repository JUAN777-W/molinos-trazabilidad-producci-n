"""Envía por correo los PDF de exportación (Control de Empaque, Rotulado y
Sellado, Control de Peso, Control de Peso Enfardadora) al canal de Teams
correspondiente, una vez el admin les asigna PRO y lote desde Informes.

Requiere estas variables en el .env — mientras no estén configuradas, el
envío simplemente se omite (la asignación de PRO/lote en la base de datos
sigue funcionando igual, solo no se manda el correo):
  SMTP_HOST=smtp.office365.com
  SMTP_PORT=587
  SMTP_USER=orlando.pradilla@molinosdelatlantico.com
  SMTP_PASS=<contraseña de aplicación>
  EMAIL_EXPORTACION_DESTINO=<correo del canal de Teams "Empacado">
"""
import os
import smtplib
from email.message import EmailMessage

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_DESTINO = os.getenv("EMAIL_EXPORTACION_DESTINO", "")


def envio_configurado() -> bool:
    return bool(SMTP_HOST and SMTP_USER and SMTP_PASS and EMAIL_DESTINO)


def enviar_pdfs_exportacion(pro_numero: str, lote: str, archivos: list[tuple[str, bytes]]) -> None:
    """archivos: lista de (nombre_archivo, contenido_pdf). Lanza excepción si
    falla — quien lo llame decide si lo considera crítico o no."""
    if not envio_configurado():
        raise RuntimeError("Envío de correo no configurado (faltan variables SMTP_* / EMAIL_EXPORTACION_DESTINO en .env)")

    msg = EmailMessage()
    msg["Subject"] = f"Planillas de empacado — PRO{pro_numero} · Lote {lote}"
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_DESTINO
    msg.set_content(
        f"Planillas de Control de Empaque, Rotulado y Sellado, Control de Peso y "
        f"Control de Peso Enfardadora del PRO {pro_numero}, lote {lote}.\n\n"
        f"Adjuntas en este correo, ya nombradas — solo hace falta moverlas a la "
        f"carpeta de exportación que corresponda.\n\n"
        f"Enviado automáticamente por el sistema de Molinos del Atlántico."
    )
    for nombre, contenido in archivos:
        msg.add_attachment(contenido, maintype="application", subtype="pdf", filename=nombre)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
