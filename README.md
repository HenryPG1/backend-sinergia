# Backend — Automatización de Reportes Fotográficos

**SINERGIA SOLUCIONES S. A.**

Backend del sistema que automatiza la documentación de instalaciones de equipo de monitoreo vehicular. Recibe los datos y las fotografías que un técnico captura en campo, genera un reporte en PDF con el formato institucional y lo envía por correo al supervisor.

---

## El problema que resuelve

Antes, un técnico volvía de campo y armaba manualmente cada reporte: ordenaba fotos, llenaba datos repetitivos y montaba el PDF a mano. Este backend elimina ese trabajo: recibe todo en una sola operación y produce el reporte automáticamente, con formato uniforme sin importar quién lo generó.

---

## Arquitectura

El sistema sigue un modelo **cliente-servidor**. Este repositorio contiene únicamente el **backend** (servidor).

```
┌────────────────────┐         HTTP/JSON          ┌──────────────────────┐
│   FRONTEND (móvil) │  ───────────────────────▶  │   BACKEND (este repo) │
│                    │                            │                      │
│ · Cámara           │   datos + fotos (base64)   │ · Valida los datos   │
│ · Formulario       │                            │ · Genera el PDF      │
│ · Retención offline│  ◀───────────────────────  │ · Envía por correo   │
│ · Notificaciones   │    confirmación de envío   │                      │
└────────────────────┘                            └──────────────────────┘
```

### Decisión de arquitectura: sin base de datos en el servidor

El backend **no persiste datos en el servidor** por diseño. Procesa cada reporte en memoria y no deja rastro tras enviarlo. Las razones:

- **Retención temporal en el dispositivo:** la captura de datos y su retención cuando no hay conexión son responsabilidad del cliente (dispositivo del técnico), que sincroniza al recuperar señal.
- **Evidencia permanente por correo:** el PDF final queda archivado en el buzón del supervisor, que actúa como registro documental.
- **Seguridad y simplicidad:** sin almacenamiento en servidor no hay superficie de datos que proteger ni costo de infraestructura de base de datos.

> Las funciones de buzón con estados, trazabilidad e histórico consultable requerirían una capa de persistencia y quedan fuera del alcance de esta versión.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Python |
| Framework web | FastAPI |
| Servidor ASGI | Uvicorn |
| Validación de datos | Pydantic |
| Generación de PDF | ReportLab |
| Procesamiento de imágenes | Pillow |
| Envío de correo | smtplib (SMTP sobre SSL) |

Sin costo de licenciamiento: todas las herramientas son libres y de código abierto.

---

## Estructura del proyecto

| Archivo | Responsabilidad |
|---|---|
| `main.py` | Punto de entrada. Define los endpoints y orquesta el flujo. |
| `schemas.py` | Define la forma de los datos de entrada y sus reglas de validación. |
| `reporte_pdf.py` | Genera el PDF con formato institucional a partir de datos y fotos. |
| `enviar_correo.py` | Envía el PDF por correo (con modo de prueba si no hay credenciales). |
| `requirements.txt` | Lista de dependencias con versiones fijadas. |
| `env.example` | Plantilla de variables de entorno (sin credenciales reales). |

---

## Instalación

Requiere **Python 3.11 o superior**.

**1. Clonar el repositorio**

```bash
git clone https://github.com/HenryPG1/backend-sinergia.git
cd backend-sinergia
```

**2. Crear y activar un entorno virtual**

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate
```

**3. Instalar las dependencias**

```bash
pip install -r requirements.txt
```

**4. Configurar las variables de entorno**

Copia `env.example` a un archivo llamado `.env` y complétalo:

```env
CORREO_ORIGEN=reportes.sinergia@gmail.com
CORREO_CLAVE=contraseña_de_aplicacion_de_16_letras
```

> Si no configuras las credenciales, el backend entra en **modo de prueba**: en lugar de enviar el correo, guarda el PDF en la carpeta `correos_simulados/` para revisión. Esto permite probar todo el sistema sin tener una cuenta de correo lista.

---

## Ejecución

```bash
uvicorn main:app --reload
```

El servidor queda disponible en `http://localhost:8000`.

La documentación interactiva de la API (Swagger UI) está en `http://localhost:8000/docs`, donde se pueden probar todos los endpoints desde el navegador.

---

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/` | Confirma que el servidor está activo. |
| `GET` | `/health` | Estado del servicio para monitoreo. |
| `POST` | `/reportes/preview` | Genera el PDF y lo devuelve para previsualizarlo, sin enviar correo. |
| `POST` | `/reportes/enviar` | Genera el PDF y lo envía por correo al supervisor. |

### Ejemplo de cuerpo para `/reportes/enviar` y `/reportes/preview`

```json
{
  "correo_supervisor": "supervisor@empresa.com",
  "cliente": "MAGDALENA",
  "direccion": "KM 99.5 Carretera a Sipacate, Finca Buganvilia",
  "ciudad": "La Democracia, Escuintla",
  "pais": "Guatemala",
  "tercero": "Noe Mijangos (Sinergia)",
  "tipo_equipo": "TPL",
  "modelo_equipo": "John Deere",
  "unidad": "07-234",
  "placa": "No",
  "tecnico": "Noe Mijangos",
  "fotografias": [
    {
      "componente": "Antena GPS",
      "observacion": "-",
      "imagen_base64": "<imagen codificada en base64>",
      "orden": 0
    }
  ]
}
```

---

## Validación de entrada

El backend rechaza los datos inválidos antes de procesarlos y responde con mensajes claros:

- La `unidad` (identificador del vehículo) es obligatoria.
- El reporte debe incluir al menos una fotografía.
- Cada fotografía debe indicar su componente.
- El correo del supervisor debe tener formato válido.

Cuando algo no cumple, la respuesta tiene código `422` e incluye una lista legible de los errores encontrados.

---

## Requerimientos cubiertos

Esta versión del backend cubre los requerimientos funcionales **RF-01 a RF-08** del documento de ingeniería del proyecto: recepción de datos y fotografías, validación, generación del PDF institucional, organización de fotos en cuadrícula, envío por correo, confirmación del resultado e inclusión de correlativo, fecha y técnico.

---

## Equipo

Proyecto de seminario de graduación — SINERGIA SOLUCIONES S. A.

- **Backend:** Henry Sicajau
- **Frontend:** Jom
- **Equipo:** Hank
