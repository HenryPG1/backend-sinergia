"""
schemas.py
Define la FORMA de los datos que el frontend envía al backend.
Sin base de datos: solo hay esquemas de ENTRADA (lo que llega),
no de salida, porque no se guarda ni se consulta nada.
"""
from pydantic import BaseModel, EmailStr


class FotografiaEntrada(BaseModel):
    componente: str            # a qué módulo pertenece la foto (GPS, Antena...)
    observacion: str | None = None
    imagen_base64: str         # la foto codificada en texto (base64)
    orden: int = 0


class ReporteEntrada(BaseModel):
    # Correo del supervisor al que se enviará el reporte
    correo_supervisor: EmailStr

    # Datos generales de la instalación (formato SOLINFTEC)
    cliente: str | None = None
    direccion: str | None = None
    ciudad: str | None = None
    pais: str | None = "Guatemala"
    tercero: str | None = None
    proyecto: str | None = None
    actividad: str | None = "Instalación"
    tipo_equipo: str | None = None
    modelo_equipo: str | None = None
    unidad: str                # placa / identificador del vehículo (obligatorio)
    placa: str | None = None
    tecnico: str | None = None

    # Las fotografías de la instalación
    fotografias: list[FotografiaEntrada]
