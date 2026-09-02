"""
enviar_correo.py
Envía el reporte PDF por correo electrónico usando Gmail (SMTP).

Incluye un MODO DE PRUEBA: si las credenciales de Gmail no están
configuradas en el .env, en lugar de fallar, guarda el PDF en una carpeta
local y reporta que "simuló" el envío. Así se puede completar y probar
todo el backend antes de tener la contraseña de Gmail.
"""
import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()

# Credenciales del correo (vienen del .env)
CORREO_ORIGEN = os.getenv("CORREO_ORIGEN")        # ej. reportes.sinergia@gmail.com
CORREO_CLAVE = os.getenv("CORREO_CLAVE")          # la contraseña de aplicación de 16 letras

# Carpeta donde se guardan los PDF en modo de prueba (cuando no hay Gmail)
CARPETA_PRUEBA = "correos_simulados"


def enviar_reporte(correo_destino: str, asunto: str, cuerpo: str,
                   pdf_bytes: bytes, nombre_pdf: str) -> dict:
    """
    Envía el PDF por correo. Devuelve un diccionario con el resultado.

    Si CORREO_ORIGEN y CORREO_CLAVE están configurados en el .env,
    envía de verdad por Gmail. Si no, entra en MODO DE PRUEBA: guarda
    el PDF localmente y reporta el envío como simulado.
    """
    # ----- MODO DE PRUEBA: sin credenciales de Gmail -----
    if not CORREO_ORIGEN or not CORREO_CLAVE:
        os.makedirs(CARPETA_PRUEBA, exist_ok=True)
        ruta = os.path.join(CARPETA_PRUEBA, nombre_pdf)
        with open(ruta, "wb") as f:
            f.write(pdf_bytes)
        return {
            "enviado": False,
            "modo": "prueba",
            "mensaje": (
                f"MODO PRUEBA: el correo no se envió porque no hay credenciales "
                f"de Gmail configuradas. El PDF se guardó en '{ruta}' para revisión. "
                f"Destinatario que se habría usado: {correo_destino}."
            ),
        }

    # ----- MODO REAL: envío por Gmail -----
    try:
        mensaje = EmailMessage()
        mensaje["From"] = CORREO_ORIGEN
        mensaje["To"] = correo_destino
        mensaje["Subject"] = asunto
        mensaje.set_content(cuerpo)

        # Adjunta el PDF
        mensaje.add_attachment(
            pdf_bytes, maintype="application", subtype="pdf", filename=nombre_pdf
        )

        # Conexión segura con el servidor de Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(CORREO_ORIGEN, CORREO_CLAVE)
            servidor.send_message(mensaje)

        return {
            "enviado": True,
            "modo": "real",
            "mensaje": f"Reporte enviado correctamente a {correo_destino}.",
        }
    except Exception as e:
        return {
            "enviado": False,
            "modo": "error",
            "mensaje": f"No se pudo enviar el correo: {e}",
        }
