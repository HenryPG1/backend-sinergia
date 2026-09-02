"""
reporte_pdf.py
Genera el reporte fotográfico de una instalación en formato PDF,
replicando el formato tipo SOLINFTEC con marca SINERGIA.

VERSIÓN SIN BASE DE DATOS:
Recibe los datos directamente como un diccionario y las fotos como una
lista, en lugar de un objeto de base de datos. Devuelve el PDF en memoria
(bytes), listo para adjuntar a un correo, sin guardarlo en disco de forma
permanente.
"""
import io
import os
import base64
import tempfile

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
)

# Datos fijos de la empresa (marca SINERGIA)
EMPRESA_NOMBRE = "SINERGIA SOLUCIONES S. A."
EMPRESA_DIR = "Sacatepéquez, Guatemala\nMonitoreo Vehicular\nwww.sinergia.com.gt"

ANCHO_UTIL = 18 * cm


def _val(datos, campo, defecto="—"):
    """Devuelve el valor de un campo del diccionario, o un guion si está vacío."""
    valor = datos.get(campo)
    return str(valor) if valor not in (None, "") else defecto


def _imagen_valida(ruta):
    """Comprueba que el archivo sea una imagen que se puede abrir de verdad."""
    try:
        from PIL import Image as PILImage
        with PILImage.open(ruta) as im:
            im.verify()
        return True
    except Exception:
        return False


def generar_pdf_reporte(datos: dict, fotografias: list) -> bytes:
    """
    Genera el PDF y lo devuelve como bytes (en memoria).

    datos: diccionario con los campos del reporte, por ejemplo:
        {
          "correlativo": "REP-2026-0001",
          "cliente": "MAGDALENA", "direccion": "...", "ciudad": "...",
          "pais": "Guatemala", "tercero": "...", "proyecto": "...",
          "actividad": "Instalación", "tipo_equipo": "TPL",
          "modelo_equipo": "John Deere", "unidad": "07-234", "placa": "No",
          "tecnico": "Noe Mijangos", "fecha": "23/01/2026"
        }

    fotografias: lista de diccionarios, cada uno con:
        { "componente": "GPS", "observacion": "-", "ruta_archivo": "/tmp/..jpg", "orden": 0 }
    """
    buffer = io.BytesIO()  # el PDF se arma en memoria, no en disco

    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=1.2 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()

    est_empresa = ParagraphStyle("emp", parent=estilos["Normal"],
                                 fontSize=7, alignment=TA_LEFT, leading=9)
    est_titulo = ParagraphStyle("tit", parent=estilos["Normal"],
                                fontSize=12, alignment=TA_CENTER, fontName="Helvetica-Bold")
    est_celda = ParagraphStyle("cel", parent=estilos["Normal"], fontSize=8, leading=10)
    est_etiqueta = ParagraphStyle("eti", parent=estilos["Normal"],
                                  fontSize=8, fontName="Helvetica-Bold", leading=10)
    est_num = ParagraphStyle("num", parent=estilos["Normal"],
                             fontSize=30, alignment=TA_CENTER,
                             textColor=colors.red, fontName="Helvetica-Bold")
    est_foto_tit = ParagraphStyle("ft", parent=estilos["Normal"],
                                  fontSize=8, alignment=TA_CENTER, fontName="Helvetica-Bold")
    est_obs = ParagraphStyle("obs", parent=estilos["Normal"], fontSize=7, leading=9)

    story = []

    # ---------- ENCABEZADO ----------
    empresa_txt = EMPRESA_DIR.replace("\n", "<br/>")
    encabezado = Table(
        [[Paragraph("[LOGO SINERGIA]", est_empresa),
          Paragraph(f"<b>{EMPRESA_NOMBRE}</b><br/>{empresa_txt}", est_empresa)]],
        colWidths=[ANCHO_UTIL * 0.4, ANCHO_UTIL * 0.6],
    )
    encabezado.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(encabezado)

    titulo_tbl = Table([[Paragraph("REPORTE DE INSTALACIÓN", est_titulo)]],
                       colWidths=[ANCHO_UTIL])
    titulo_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(titulo_tbl)

    # ---------- TABLA DE DATOS GENERALES ----------
    correlativo = datos.get("correlativo", "REP-2026-0000")
    numero = correlativo.split("-")[-1] if "-" in correlativo else correlativo

    datos_izq = [
        [Paragraph("Cliente", est_etiqueta), Paragraph(_val(datos, "cliente"), est_celda)],
        [Paragraph("Dirección", est_etiqueta), Paragraph(_val(datos, "direccion"), est_celda)],
        [Paragraph("Ciudad", est_etiqueta), Paragraph(_val(datos, "ciudad"), est_celda)],
        [Paragraph("País", est_etiqueta), Paragraph(_val(datos, "pais", "Guatemala"), est_celda)],
        [Paragraph("Tercero", est_etiqueta), Paragraph(_val(datos, "tercero"), est_celda)],
    ]
    tabla_izq = Table(datos_izq, colWidths=[2.5 * cm, ANCHO_UTIL * 0.68 - 2.5 * cm])
    tabla_izq.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    num_tbl = Table(
        [[Paragraph("REPORT Nº", est_etiqueta)], [Paragraph(numero, est_num)]],
        colWidths=[ANCHO_UTIL * 0.32], rowHeights=[0.7 * cm, 1.8 * cm],
    )
    num_tbl.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
        ("LINEBELOW", (0, 0), (0, 0), 0.5, colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    fila_datos = Table([[tabla_izq, num_tbl]],
                       colWidths=[ANCHO_UTIL * 0.68, ANCHO_UTIL * 0.32])
    fila_datos.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(fila_datos)

    datos2 = [
        [Paragraph("Nº Proyecto", est_etiqueta), Paragraph(_val(datos, "proyecto"), est_celda),
         Paragraph("Actividad", est_etiqueta), Paragraph(_val(datos, "actividad", "Instalación"), est_celda)],
        [Paragraph("Tipo Equipo", est_etiqueta), Paragraph(_val(datos, "tipo_equipo"), est_celda),
         Paragraph("Modelo", est_etiqueta), Paragraph(_val(datos, "modelo_equipo"), est_celda)],
        [Paragraph("Nº Flota", est_etiqueta), Paragraph(_val(datos, "unidad"), est_celda),
         Paragraph("Placa", est_etiqueta), Paragraph(_val(datos, "placa"), est_celda)],
        [Paragraph("Técnico", est_etiqueta), Paragraph(_val(datos, "tecnico"), est_celda),
         Paragraph("Fecha", est_etiqueta), Paragraph(_val(datos, "fecha"), est_celda)],
    ]
    tabla2 = Table(datos2, colWidths=[2.5 * cm, ANCHO_UTIL / 2 - 2.5 * cm,
                                       2.5 * cm, ANCHO_UTIL / 2 - 2.5 * cm])
    tabla2.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("BACKGROUND", (2, 0), (2, -1), colors.whitesmoke),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(tabla2)
    story.append(Spacer(1, 6))

    # ---------- CUADRÍCULA DE FOTOS (3 columnas) ----------
    fotos = sorted(fotografias, key=lambda f: f.get("orden", 0)) if fotografias else []

    col_ancho = ANCHO_UTIL / 3
    img_ancho = col_ancho - 0.4 * cm
    img_alto = 4.5 * cm

    def celda_foto(foto):
        elementos = [Paragraph(foto.get("componente", "").upper(), est_foto_tit)]
        ruta = foto.get("ruta_archivo")
        if ruta and os.path.exists(ruta) and _imagen_valida(ruta):
            try:
                elementos.append(Image(ruta, width=img_ancho, height=img_alto))
            except Exception:
                elementos.append(Paragraph("(imagen no válida)", est_obs))
        else:
            elementos.append(Spacer(1, img_alto * 0.4))
            elementos.append(Paragraph("(sin imagen)", est_obs))
            elementos.append(Spacer(1, img_alto * 0.4))
        obs = foto.get("observacion") or "-"
        elementos.append(Paragraph(f"OBS: {obs}", est_obs))
        return elementos

    filas_fotos = []
    for i in range(0, len(fotos), 3):
        grupo = fotos[i:i + 3]
        fila = [celda_foto(f) for f in grupo]
        while len(fila) < 3:
            fila.append([Paragraph("", est_obs)])
        filas_fotos.append(fila)

    if filas_fotos:
        tabla_fotos = Table(filas_fotos, colWidths=[col_ancho] * 3)
        tabla_fotos.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tabla_fotos)
    else:
        story.append(Paragraph("Sin fotografías registradas.", est_celda))

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawCentredString(letter[0] / 2, 1 * cm, f"Página {documento.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=pie, onLaterPages=pie)

    # Devuelve los bytes del PDF (en memoria)
    buffer.seek(0)
    return buffer.getvalue()


def guardar_fotos_temporales(fotografias_base64: list) -> list:
    """
    Recibe las fotos como base64 (lo que manda el frontend), las escribe
    en archivos temporales y devuelve la lista lista para generar_pdf_reporte.
    Los archivos temporales se limpian después con limpiar_temporales().
    """
    fotos_listas = []
    temporales = []
    for i, foto in enumerate(fotografias_base64):
        b64 = foto.get("imagen_base64", "")
        ruta_tmp = None
        if b64:
            try:
                fd, ruta_tmp = tempfile.mkstemp(suffix=".jpg", prefix=f"foto_{i}_")
                with os.fdopen(fd, "wb") as f:
                    f.write(base64.b64decode(b64))
                temporales.append(ruta_tmp)
            except Exception:
                ruta_tmp = None
        fotos_listas.append({
            "componente": foto.get("componente", ""),
            "observacion": foto.get("observacion", ""),
            "ruta_archivo": ruta_tmp,
            "orden": foto.get("orden", i),
        })
    return fotos_listas, temporales


def limpiar_temporales(temporales: list):
    """Borra los archivos temporales de las fotos después de usarlos."""
    for ruta in temporales:
        try:
            os.remove(ruta)
        except Exception:
            pass
