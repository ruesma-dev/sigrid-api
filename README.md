# sigrid-api

API serverless de solo lectura sobre SQL Server on-prem para Azure, construida con Azure Functions (Python 3.12).

## Objetivo

Exponer una API HTTP interna que permita:

1. Ejecutar consultas `SELECT`/`WITH` controladas sobre SQL Server y devolver resultados en JSON.
2. Recuperar documentos binarios desde la base de datos y devolverlos por HTTP, sin persistirlos en Azure.

## Arquitectura recomendada

- **1 Function App** en **Azure Functions Flex Consumption**
- **1 Storage Account** asociado a la Function App
- **1 Key Vault** para secretos (`SQL_SERVER_PASSWORD`)
- **1 subnet dedicada** en el **spoke DEV** para integración de red
- **1 Function App** con dos funciones HTTP:
  - `POST /api/sql/read`
  - `POST /api/documents/read`

### Por qué esta opción

- Mínimo coste
- Un solo punto de despliegue
- Una sola integración de red al spoke DEV
- Un solo almacén de secretos
- Contrato HTTP simple para ser consumido desde local o desde otros servicios Azure

## Contrato HTTP

### 1. `POST /api/sql/read`

#### Request

```json
{
  "database": "ruesma_rep",
  "sql": "SELECT TOP 10 ide, nom, nomori FROM dbo.gra WHERE nom LIKE ? ORDER BY ide DESC",
  "parameters": ["%castillo%"],
  "timeout_seconds": 30,
  "max_rows": 200
}
```

#### Response

```json
{
  "ok": true,
  "database": "ruesma_rep",
  "columns": ["ide", "nom", "nomori"],
  "rows": [
    [340434, "DNI MANUEL CASTILLO BURGOS.pdf", "DNI MANUEL CASTILLO BURGOS.pdf"]
  ],
  "row_count": 1,
  "truncated": false
}
```

#### Controles aplicados

- Solo permite consultas que empiecen por `SELECT` o `WITH`
- Deniega palabras peligrosas (`INSERT`, `UPDATE`, `DELETE`, `MERGE`, `ALTER`, `DROP`, `TRUNCATE`, `EXEC`, `USE`, etc.)
- Solo admite una sentencia
- Límite configurable de timeout
- Límite configurable de filas devueltas
- Lista blanca de bases de datos permitidas

### 2. `POST /api/documents/read`

#### Request

```json
{
  "database": "ruesma_rep",
  "schema": "dbo",
  "table": "gra",
  "id_column": "ide",
  "id_value": 340434,
  "blob_column": "ima",
  "filename_columns": ["nomori", "nom"],
  "disposition": "attachment"
}
```

#### Response

- `Content-Type`: detectado por firma binaria (`application/pdf`, `image/jpeg`, `image/png`, `image/tiff`, `application/octet-stream`)
- `Content-Disposition`: `attachment` o `inline`
- Cuerpo: binario del documento
- Cabeceras auxiliares:
  - `X-Document-Filename`
  - `X-Document-Size`

## Estructura del proyecto

```text
sigrid-api/
├─ function_app.py
├─ host.json
├─ requirements.txt
├─ local.settings.sample.json
├─ .funcignore
├─ .env.example
├─ README.md
├─ config/
│  └─ settings.py
├─ application/
│  └─ use_cases/
│     ├─ execute_sql_query_use_case.py
│     └─ read_document_use_case.py
├─ domain/
│  ├─ models/
│  │  ├─ document_models.py
│  │  └─ sql_models.py
│  └─ ports/
│     └─ sql_repository.py
├─ infrastructure/
│  ├─ repositories/
│  │  └─ sql_server_repository.py
│  ├─ security/
│  │  ├─ identifier_guard.py
│  │  └─ sql_query_guard.py
│  └─ serialization/
│     └─ json_encoder.py
└─ scripts/
   └─ invoke_api_examples.py
```

## Configuración local en PyCharm (Windows)

### Requisitos

- Python 3.12
- ODBC Driver 18 for SQL Server en tu equipo Windows
- Azure Functions Core Tools v4
- Azure CLI

### Crear entorno local

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Preparar `local.settings.json`

Copia `local.settings.sample.json` a `local.settings.json` y rellena los valores locales.

### Lanzar localmente

```powershell
func start
```

## Despliegue manual en Azure (recomendado para aprender)

### 1. Preparar la red

1. Entra en `vnet-spoke-dev-spaincentral`.
2. Crea una subnet nueva, dedicada a la Function App.
3. Recomendación:
   - Nombre: `snet-func-sigrid-dev`
   - Tamaño: `/27`
4. Delega la subnet a:
   - `Microsoft.App/environments`

> No reutilices esta subnet para VMs, Private Endpoints ni otros servicios.

### 2. Crear Storage Account

1. Suscripción: `Ruesma`
2. RG: uno de aplicación, por ejemplo `rg-sigrid-dev-data-api`
3. Región: `Spain Central`
4. Tipo estándar LRS

### 3. Crear Key Vault

1. Crea `kv-sigrid-dev-data-api`
2. Guarda al menos este secreto:
   - `sql-server-password`
3. Opcionalmente guarda también:
   - `sql-server-username`
   - `sql-server-host`
   - `sql-server-port`

### 4. Crear Function App (Flex Consumption)

1. Tipo: **Function App**
2. Hosting plan: **Flex Consumption**
3. Runtime: **Python 3.12**
4. Región: `Spain Central`
5. Storage: el Storage Account creado antes
6. Activa identidad administrada **System Assigned**
7. Configura integración de red a la subnet `snet-func-sigrid-dev`

### 5. Dar acceso a Key Vault

En el Key Vault, asigna a la identidad administrada de la Function App el rol:

- **Key Vault Secrets User**

### 6. Configurar variables de entorno en la Function App

En **Environment variables / App settings** crea:

- `SQL_DRIVER = ODBC Driver 18 for SQL Server`
- `SQL_SERVER_HOST = 192.168.14.238`
- `SQL_SERVER_PORT = 49782`
- `SQL_SERVER_USERNAME = ro_user`
- `SQL_SERVER_PASSWORD = @Microsoft.KeyVault(SecretUri=<SECRET_URI>)`
- `DEFAULT_QUERY_TIMEOUT_SECONDS = 30`
- `MAX_QUERY_TIMEOUT_SECONDS = 120`
- `DEFAULT_MAX_ROWS = 200`
- `MAX_ALLOWED_ROWS = 1000`
- `MAX_INLINE_BINARY_BYTES = 65536`
- `ALLOWED_DATABASES = master,ruesma_rep,ruesma`
- `ALLOWED_QUERY_PREFIXES = SELECT,WITH`

### 7. Publicar el código

#### Opción recomendada: Core Tools

Desde la raíz del proyecto:

```powershell
func azure functionapp publish <NOMBRE_DE_LA_FUNCTION_APP>
```

Para Python, Core Tools usa **remote build** por defecto, que es lo recomendado.

## Cómo invocarla desde local o desde otro servicio

### Usando Function Key

Añade la cabecera:

```http
x-functions-key: <FUNCTION_KEY>
```

### Ejemplo Python para `sql/read`

```python
import requests

base_url = "https://<app-name>.azurewebsites.net"
function_key = "<FUNCTION_KEY>"

payload = {
    "database": "ruesma_rep",
    "sql": "SELECT TOP 5 ide, nom, nomori FROM dbo.gra ORDER BY ide DESC",
    "parameters": [],
    "max_rows": 5,
    "timeout_seconds": 30,
}

resp = requests.post(
    f"{base_url}/api/sql/read",
    headers={
        "x-functions-key": function_key,
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=60,
)
resp.raise_for_status()
print(resp.json())
```

### Ejemplo Python para `documents/read`

```python
import requests
from pathlib import Path

base_url = "https://<app-name>.azurewebsites.net"
function_key = "<FUNCTION_KEY>"

payload = {
    "database": "ruesma_rep",
    "schema": "dbo",
    "table": "gra",
    "id_column": "ide",
    "id_value": 340434,
    "blob_column": "ima",
    "filename_columns": ["nomori", "nom"],
    "disposition": "attachment",
}

resp = requests.post(
    f"{base_url}/api/documents/read",
    headers={
        "x-functions-key": function_key,
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=120,
)
resp.raise_for_status()

filename = resp.headers.get("X-Document-Filename", "documento.bin")
Path(filename).write_bytes(resp.content)
print(f"Guardado: {filename}")
```

## Recomendaciones operativas

1. No mantengas el SQL con puerto dinámico indefinidamente. Pásalo a puerto fijo.
2. Mantén `ro_user` como usuario de solo lectura.
3. No expongas esta API como `anonymous`; usa `function` + keys.
4. Si más adelante necesitas endurecer seguridad, añade Microsoft Entra ID delante de la Function App.


## Terraform dentro del proyecto

Sí. En este proyecto el Terraform va **dentro de la carpeta del proyecto de PyCharm**:

```text
sigrid-api/
└─ infra/
   ├─ terraform/
   └─ scripts/
```

La carpeta `infra/terraform` contiene únicamente la **infraestructura**.
El **código de la Function App** sigue en la raíz del proyecto.

## Flujo recomendado

1. Desplegar infraestructura con Terraform desde `infra/terraform`
2. Cargar el secreto SQL en Key Vault
3. Publicar el código con `func azure functionapp publish`
4. Obtener la host key para invocar la API desde local o desde otro servicio Azure
