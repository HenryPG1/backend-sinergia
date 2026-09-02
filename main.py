"""
main.py
Backend del sistema de reportes fotográficos — VERSIÓN SIN BASE DE DATOS.

Un solo flujo: recibe los datos y fotos del frontend, genera el PDF con
formato SOLINFTEC, y lo envía por correo al supervisor. No guarda nada
de forma permanente.

Para arrancar:
    uvicorn main:app --reload
Luego abre:  http://localhost:8000/docs
"""
import logging
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
# from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

import schemas
from reporte_pdf import (
    generar_pdf_reporte, guardar_fotos_temporales, limpiar_temporales
)
from enviar_correo import enviar_reporte

# Muestra los mensajes de log (INFO y superiores) en la consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Backend Sinergia - Reportes (sin base de datos)")

# Permite que el frontend hable con este backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# RF-03: convierte los errores de validación en mensajes claros para el frontend
@app.exception_handler(RequestValidationError)
async def errores_de_validacion(request: Request, exc: RequestValidationError):
    """
    Recoge todos los errores de validación de Pydantic y los devuelve
    en un formato limpio y legible en lugar del error técnico por defecto.
    """
    mensajes = []
    for error in exc.errors():
        # 'loc' indica en qué campo ocurrió el error
        campo = " → ".join(str(x) for x in error["loc"] if x != "body")
        mensajes.append(f"{campo}: {error['msg']}")

    logging.warning("Reporte rechazado por validación: %s", mensajes)

    return JSONResponse(
        status_code=422,
        content={
            "exito": False,
            "mensaje": "Los datos enviados no son válidos.",
            "errores": mensajes,
        },
    )


def generar_correlativo() -> str:
    """
    Genera un número de reporte basado en la fecha y hora actual.
    Sin base de datos no hay un contador, así que usamos la marca de tiempo
    para que cada reporte tenga un identificador único.
    """
    ahora = datetime.now(timezone.utc)
    return f"REP-{ahora.year}-{ahora.strftime('%m%d%H%M%S')}"


@app.get("/")
def inicio():
    """Confirma que el servidor está vivo."""
    return {"mensaje": "Backend de Sinergia (sin BD) funcionando correctamente"}

@app.post("/reportes/preview")
def previsualizar_reporte(datos: schemas.ReporteEntrada):
    """
    Genera el PDF y lo devuelve directamente en la respuesta, SIN enviarlo
    por correo. Sirve para previsualizar el reporte en el navegador y para
    demostrar la generación del PDF sin depender del servicio de correo.
    """
    correlativo = generar_correlativo()

    datos_pdf = {
        "correlativo": correlativo,
        "cliente": datos.cliente,
        "direccion": datos.direccion,
        "ciudad": datos.ciudad,
        "pais": datos.pais,
        "tercero": datos.tercero,
        "proyecto": datos.proyecto,
        "actividad": datos.actividad,
        "tipo_equipo": datos.tipo_equipo,
        "modelo_equipo": datos.modelo_equipo,
        "unidad": datos.unidad,
        "placa": datos.placa,
        "tecnico": datos.tecnico,
        "fecha": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
    }

    fotos_base64 = [f.model_dump() for f in datos.fotografias]
    fotos_listas, temporales = guardar_fotos_temporales(fotos_base64)

    try:
        pdf_bytes = generar_pdf_reporte(datos_pdf, fotos_listas)
    finally:
        limpiar_temporales(temporales)

    # Devuelve el PDF para verlo en el navegador (inline)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="{correlativo}.pdf"'
        },
    )

@app.post("/reportes/enviar")
def crear_y_enviar_reporte(datos: schemas.ReporteEntrada):
    """
    Recibe un reporte completo, genera el PDF y lo envía por correo.
    No guarda nada de forma permanente.
    La validación de los datos ya la hizo Pydantic (ver schemas.py, RF-03).
    """
    correlativo = generar_correlativo()

    # Prepara el diccionario de datos para el generador de PDF
    datos_pdf = {
        "correlativo": correlativo,
        "cliente": datos.cliente,
        "direccion": datos.direccion,
        "ciudad": datos.ciudad,
        "pais": datos.pais,
        "tercero": datos.tercero,
        "proyecto": datos.proyecto,
        "actividad": datos.actividad,
        "tipo_equipo": datos.tipo_equipo,
        "modelo_equipo": datos.modelo_equipo,
        "unidad": datos.unidad,
        "placa": datos.placa,
        "tecnico": datos.tecnico,
        "fecha": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
    }

    # Convierte las fotos base64 en archivos temporales
    fotos_base64 = [f.model_dump() for f in datos.fotografias]
    fotos_listas, temporales = guardar_fotos_temporales(fotos_base64)

    try:
        # Genera el PDF en memoria
        pdf_bytes = generar_pdf_reporte(datos_pdf, fotos_listas)
    finally:
        # Limpia los archivos temporales pase lo que pase
        limpiar_temporales(temporales)

    # Envía el PDF por correo (o lo simula si no hay Gmail configurado)
    nombre_pdf = f"{correlativo}.pdf"
    resultado = enviar_reporte(
        correo_destino=datos.correo_supervisor,
        asunto=f"Reporte de instalación {correlativo}",
        cuerpo=(
            f"Adjunto el reporte de instalación {correlativo} "
            f"de la unidad {datos.unidad}."
        ),
        pdf_bytes=pdf_bytes,
        nombre_pdf=nombre_pdf,
    )

    return {
        "correlativo": correlativo,
        "resultado_envio": resultado,
    }
# """
# main.py
# Backend del sistema de reportes fotográficos — VERSIÓN SIN BASE DE DATOS.

# Un solo flujo: recibe los datos y fotos del frontend, genera el PDF con
# formato SOLINFTEC, y lo envía por correo al supervisor. No guarda nada
# de forma permanente.

# Para arrancar:
#     uvicorn main:app --reload
# Luego abre:  http://localhost:8000/docs
# """
# from datetime import datetime, timezone

# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware

# import schemas
# from reporte_pdf import (
#     generar_pdf_reporte, guardar_fotos_temporales, limpiar_temporales
# )
# from enviar_correo import enviar_reporte

# app = FastAPI(title="Backend Sinergia - Reportes (sin base de datos)")

# # Permite que el frontend hable con este backend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# def generar_correlativo() -> str:
#     """
#     Genera un número de reporte basado en la fecha y hora actual.
#     Sin base de datos no hay un contador, así que usamos la marca de tiempo
#     para que cada reporte tenga un identificador único.
#     """
#     ahora = datetime.now(timezone.utc)
#     return f"REP-{ahora.year}-{ahora.strftime('%m%d%H%M%S')}"


# @app.get("/")
# def inicio():
#     """Confirma que el servidor está vivo."""
#     return {"mensaje": "Backend de Sinergia (sin BD) funcionando correctamente"}


# @app.post("/reportes/enviar")
# def crear_y_enviar_reporte(datos: schemas.ReporteEntrada):
#     """
#     Recibe un reporte completo, genera el PDF y lo envía por correo.
#     No guarda nada de forma permanente.
#     """
#     if not datos.fotografias:
#         raise HTTPException(
#             status_code=400,
#             detail="El reporte debe incluir al menos una fotografía."
#         )

#     correlativo = generar_correlativo()

#     # Prepara el diccionario de datos para el generador de PDF
#     datos_pdf = {
#         "correlativo": correlativo,
#         "cliente": datos.cliente,
#         "direccion": datos.direccion,
#         "ciudad": datos.ciudad,
#         "pais": datos.pais,
#         "tercero": datos.tercero,
#         "proyecto": datos.proyecto,
#         "actividad": datos.actividad,
#         "tipo_equipo": datos.tipo_equipo,
#         "modelo_equipo": datos.modelo_equipo,
#         "unidad": datos.unidad,
#         "placa": datos.placa,
#         "tecnico": datos.tecnico,
#         "fecha": datetime.now(timezone.utc).strftime("%d/%m/%Y"),
#     }

#     # Convierte las fotos base64 en archivos temporales
#     fotos_base64 = [f.model_dump() for f in datos.fotografias]
#     fotos_listas, temporales = guardar_fotos_temporales(fotos_base64)

#     try:
#         # Genera el PDF en memoria
#         pdf_bytes = generar_pdf_reporte(datos_pdf, fotos_listas)
#     finally:
#         # Limpia los archivos temporales pase lo que pase
#         limpiar_temporales(temporales)

#     # Envía el PDF por correo (o lo simula si no hay Gmail configurado)
#     nombre_pdf = f"{correlativo}.pdf"
#     resultado = enviar_reporte(
#         correo_destino=datos.correo_supervisor,
#         asunto=f"Reporte de instalación {correlativo}",
#         cuerpo=(
#             f"Adjunto el reporte de instalación {correlativo} "
#             f"de la unidad {datos.unidad}."
#         ),
#         pdf_bytes=pdf_bytes,
#         nombre_pdf=nombre_pdf,
#     )

#     return {
#         "correlativo": correlativo,
#         "resultado_envio": resultado,
#     }

@app.get("/health")
def salud():
    """
    Endpoint de salud: confirma que el servicio está operativo.
    Estándar en backends profesionales para monitoreo automático.
    """
    return {
        "estado": "ok",
        "servicio": "backend-sinergia",
        "hora": datetime.now(timezone.utc).isoformat(),
    }