<!-- specs/F-010-documents-read-nombres-y-clave/design.md -->
# F-010 · Diseño

Requisitos en [`requirements.md`](requirements.md). Dos arreglos independientes en
`documents/read`, cada uno en su capa; ninguna dependencia nueva, ninguna App Setting nueva,
ningún fichero `.sql` (la consulta es la de hoy, compuesta en el adaptador).

## Encaje y límite de microservicio

Todo vive dentro de la responsabilidad actual de `sigrid-api` (servir el BLOB de `ruesma_rep`
con acceso controlado). No hay lógica nueva de otro dominio: **no procede extraer nada**. Capas
(`docs/ARCHITECTURE.md`): el modelo y la excepción en *domain*, la traducción petición →
localización en *application*, el SQL en *infrastructure*, la cabecera en *interface_adapters*,
el código HTTP en `function_app.py`.

## Ficheros a modificar

| Fichero | Qué cambia | R |
|---|---|---|
| `interface_adapters/http/http_response_factory.py` | Función nueva `filename_header_value()`; `binary_file_response` la usa para `X-Document-Filename` y pasa `safe=""` al `quote` de `Content-Disposition` | R1-R5 |
| `domain/models/sql_models.py` | `DocumentReadRequest`: `id_column`/`id_value` opcionales, campo `key`, validadores, constante `MAX_COLUMNAS_CLAVE = 4`, método `localizacion()` | R6-R9, R12 |
| `domain/models/document_models.py` | Excepción `DocumentoAmbiguoError(ValueError)`; `RawDocumentRecord` pierde `id_value` | R13, R15 |
| `domain/ports/sql_repository.py` | Firma de `read_document`: `key: dict[str, Any]` sustituye a `id_column`/`id_value`; docstring con las excepciones | R10-R14 |
| `infrastructure/repositories/sql_server_repository.py` | Función pura `build_document_query()`; `read_document` con `TOP (2)`, `fetchall()` y los tres errores | R10-R14 |
| `application/use_cases/read_document_use_case.py` | Pasa `key=request.localizacion()`; nombre de reserva desde la localización | R12, R15 |
| `function_app.py` | `documents_read`: `except DocumentoAmbiguoError` → 409, **antes** de los demás `except` | R13 |
| `../azure-apps/sigrid_api.md` | §8.3 y §10 (repo aparte, commit aparte, sin push) | R16 |

## Ficheros a crear (tests; sin red ni BBDD)

- `tests/test_f010_cabecera.py` — R1-R4 sobre `filename_header_value` y `binary_file_response`.
- `tests/test_f010_modelo.py` — R6-R9 y `localizacion()` (R12) sobre `DocumentReadRequest`.
- `tests/test_f010_repositorio.py` — R10-R14 sobre `build_document_query` y `read_document`
  con `_connect` doblado (cursor falso que registra SQL y parámetros y devuelve 0, 1 o 2 filas).
  Ajustes falsos con `SimpleNamespace`: nunca se llama a `pyodbc.connect`.
- `tests/test_f010_caso_de_uso.py` — R12, R15 con repositorio doble que registra la llamada.
- `tests/test_f010_ruta.py` — R5, R7, R13 y textos de R14 en la ruta, con `build_dependencies`
  doblado a una tupla de ocho y el caso de uso doblado (patrón de `tests/test_f004_route.py`).

Nombres trazables `test_f010_rN_...` (`docs/CONVENTIONS.md`).

## Ficheros que NO se tocan

- `infrastructure/security/` entero: `IdentifierGuard` se **usa** igual que hoy.
- `infrastructure/serialization/json_encoder.py`, `config/settings.py`: sin ajustes nuevos.
- Rutas y casos de uso que no son `documents/read`; `build_dependencies()` (la tupla de ocho no
  cambia).
- `scripts/` (en particular `invoke_api_examples.py`): `scripts/` **cuenta** para cobertura y
  mutación (`harness/alcance.py` no lo excluye), y no hay nada que arreglar que no sea cosmético.
- `docs/ARCHITECTURE.md`: no cambia ni la estructura ni una regla de dominio.
- Repos ajenos: `sigrid-api-v2`, `albaranes`, `mcp-bbdd`, `datamart-seg-anual`.

## A. La cabecera (interface_adapters)

```python
#: ASCII imprimible (0x20-0x7E) salvo "%": lo que X-Document-Filename deja tal cual (R1-R3).
_SEGUROS_EN_CABECERA = "".join(chr(c) for c in range(0x20, 0x7F) if chr(c) != "%")

def filename_header_value(file_name: str) -> str:
    """Nombre para X-Document-Filename: ASCII imprimible que `unquote` devuelve al original."""
    return quote(file_name, safe=_SEGUROS_EN_CABECERA, encoding="utf-8", errors="strict")
```

`binary_file_response`: `"X-Document-Filename": filename_header_value(file_name)` y
`quote(file_name, safe="")` en `Content-Disposition`. Nada más cambia en la función.

**Decisión D1 — codificar, no quitar, y codificar solo lo imprescindible.**

- *Quitar la cabecera*: descartado. `albaranes-persistencia`
  (`infrastructure/sigrid/sigrid_api_contrato_client.py:709`) toma de ella el nombre del PDF del
  contrato y caería a `documento_<ide>`; sus scripts de diagnóstico y `sigrid-api-v2` también la
  leen. mcp-bbdd no la lee (usa `Content-Type` y `X-Document-Size`).
- *`quote(nombre, safe="")` completo* (como `Content-Disposition`): descartado. Cambiaría también
  los nombres ASCII con espacios o paréntesis (`"Contrato 2024.pdf"` → `"Contrato%202024.pdf"`),
  que hoy funcionan (94,3 % de los adjuntos medidos por el datamart), y albaranes los vería
  cambiados sin haber pedido nada.
- *Elegida*: codificación porcentual UTF-8 de todo lo que no sea ASCII imprimible **y del `%`**.
  Un nombre ASCII sin `%` viaja idéntico (R3); todo nombre se decodifica sin ambigüedad con
  `unquote` (R2), porque el `%` literal siempre va como `%25`. Coste: un nombre ASCII **con** `%`
  cambia (`"100% real.pdf"` → `"100%25 real.pdf"`); albaranes lo vería así hasta añadir
  `unquote`, que es retrocompatible con el servidor viejo. Los controles 0x00-0x1F y 0x7F se
  codifican: cierra además cualquier inyección de cabecera por CR/LF, aunque el caso de uso ya
  los sustituye por `_`.
- Por qué el `range` y no `string.punctuation`: la campaña muta enteros con +1; con `range`, los
  dos mutantes (`0x21` y `0x80`) los matan los tests del espacio (R3) y de DEL (R1). La
  comparación `!= "%"` la mata el test del `%` (R2).

**Decisión D2 — `safe=""` en `Content-Disposition`.** `quote` deja `/` sin codificar por
defecto y RFC 5987 no lo admite en `filename*`. El caso de uso ya sustituye `/` por `_`
(`_resolve_filename`), así que para todo nombre que llega a la ruta el valor es idéntico al de
hoy (lo que pide el `acceptance`); el cambio solo hace correcta a la función por sí misma. Test:
nombre con `/` → `%2F`; nombres sin `/` → igual que `quote(nombre)`.

El 500 vacío no lo reproduce un test unitario: ñ y á son latin-1 y `func.HttpResponse` las
admite; quien las rechaza es el host. El criterio verificable es R1-R2, y la prueba real es R18.

## B. La localización (domain, application, infrastructure)

### `DocumentReadRequest` (domain/models/sql_models.py)

```python
MAX_COLUMNAS_CLAVE = 4

id_column: str | None = Field(None, min_length=1)
id_value: Any = None
key: dict[str, StrictInt | StrictStr] | None = None
```

- `_strip_identifier` sigue en `database`, `schema`, `table`, `id_column`, `blob_column`, pero
  **deja `None` como `None`** (hoy `str(None)` daría `"None"`).
- `@field_validator("key")` (after): recorta nombres; rechaza vacío, `> MAX_COLUMNAS_CLAVE`,
  nombre vacío y duplicados por `casefold()` (R9). Devuelve el dict con los nombres recortados,
  **conservando el orden** del JSON.
- `@model_validator(mode="after")`: con `presente = "id_value" in self.model_fields_set`:
  `key` con `id_column` o `presente` → error (R7); sin `key`, falta `id_column` o falta
  `presente` → error (R8). Mensajes: `"key es excluyente con id_column/id_value."` y
  `"Indica key, o id_column con id_value."`. Pydantic los convierte en `ValidationError` → 400.
- `StrictInt | StrictStr` rechaza `null`, booleanos, decimales, listas y objetos (R6); en modo
  estricto `"123"` sigue siendo texto y `123` entero (sin coerción entre ellos).
- `def localizacion(self) -> dict[str, Any]`: `dict(self.key)` si hay `key`; si no,
  `{self.id_column: self.id_value}` (R12).
- `extra` sigue en `ignore`, como hoy: `forbid` rompería a clientes que manden campos de más.

### Excepción y registro (domain/models/document_models.py)

```python
class DocumentoAmbiguoError(ValueError):
    """La localización casa con más de una fila: no se sirve ninguna (R13)."""

@dataclass(frozen=True)
class RawDocumentRecord:
    file_name_candidates: list[str]
    content: bytes
```

Hereda de `ValueError` para que, si alguien quitara el `except` propio, cayera en 400 y no en
500; aun así su `details.type` seguiría sin ser `"ValueError"`. `id_value` sale del registro:
el repositorio solo lo devolvía de vuelta y el nombre de reserva ya sale de la petición (R15).

### Puerto (domain/ports/sql_repository.py)

```python
def read_document(self, *, database: str, schema: str, table: str, key: dict[str, Any],
                  blob_column: str, filename_columns: list[str]) -> RawDocumentRecord:
    """Lee UNA fila. Lanza IdentifierValidationError (nombre no válido), ValueError
    (ninguna fila, o BLOB NULL) y DocumentoAmbiguoError (más de una fila)."""
```

Un solo camino: `id_column`/`id_value` se traduce a `key` en el modelo, así que el adaptador no
tiene dos ramas de SQL que mantener (y que mutar).

### Adaptador (infrastructure/repositories/sql_server_repository.py)

```python
def build_document_query(*, schema: str, table: str, key: dict[str, Any], blob_column: str,
                         filename_columns: list[str]) -> tuple[str, list[Any], str]:
    """(sql, parámetros, condición legible). Pura: valida identificadores y compone."""
```

- Valida con `IdentifierGuard.validate_identifier` en este orden: `schema`, `table`, cada
  nombre de `key` (`field_name="key"`), `blob_column`, `filename_columns` (R10).
- SQL (R11):
  `SELECT TOP (2) [f1], …, CAST([blob] AS varbinary(max)) AS file_content FROM [s].[t] WHERE [c1] = ? AND [c2] = ?`.
  Parámetros: `list(key.values())`. Condición legible: `" AND ".join(f"{c}={v}")` con los
  nombres validados; con una columna es `ide=365617`, como hoy (R14).
- `read_document`: compone, conecta como hoy (credencial de lectura, `autocommit=True`,
  `default_query_timeout_seconds`), `cursor.execute(sql, *params)`, `rows = cursor.fetchall()`.
  Sin filas → `ValueError` (texto R14); `len(rows) > 1` → `DocumentoAmbiguoError` (texto R13);
  BLOB `None` → `ValueError` (texto R14). Candidatos de nombre como hoy.
- `fetchall()` y no `fetchmany(2)`: el `TOP (2)` ya acota a dos filas y así no hay un entero
  que la campaña pueda mutar a un equivalente (`fetchmany(3)` sería indistinguible).

### Caso de uso (application/use_cases/read_document_use_case.py)

`localizacion = request.localizacion()`; `read_document(..., key=localizacion, ...)`;
`_resolve_filename(candidatos, contenido, etiqueta)` con
`etiqueta = "_".join(str(v) for v in localizacion.values())` y reserva `f"document_{etiqueta}"`
(R15). El saneado y la extensión, como hoy.

### Ruta (function_app.py)

Primer `except` de `documents_read`:
`except DocumentoAmbiguoError as exc:` → `logger.warning(...)` y
`error_response(str(exc), status_code=409, details={"type": "DocumentoAmbiguoError"})`.
El resto de `except` no cambia.

**Decisión D3 — 409 para la ambigüedad.** Alternativa: 400 con `details.type` propio.
Elegido 409 porque distingue la ambigüedad de «no hay fila» por el **código** (albaranes solo
mira el código; mcp-bbdd trata todo lo que no es 200, 400-`ValueError`, 401/403, 3xx o 5xx
reintentable como «origen no disponible», que es lo correcto para este caso). Con 400 y tipo
distinto el efecto en mcp-bbdd sería el mismo; en albaranes, indistinguible por código.

**Decisión D4 — tope de 4 columnas, constante de código.** El índice único más ancho de `gra`
tiene 2; 4 da margen sin abrir `WHERE` arbitrarios. Constante y no App Setting: no es algo que
operación deba girar, y un ajuste más es una deriva más entre local y Azure.

**Decisión D5 — `TOP (2)` para toda petición.** En el caso normal (fila única) el coste es el
de hoy. En el ambiguo viajan como mucho dos BLOB antes del 409; acotado y solo en peticiones
erróneas. `COUNT(*) OVER ()` daría el total exacto pero recorre todas las filas que casan
(`emp = 1` son cientos de miles): descartado.

## Documentación (R16)

`../azure-apps/sigrid_api.md`, commit aparte en ese repo (local, sin push):

- §8.3: tabla de campos con `key` (1-4 columnas, valores entero o texto, AND, excluyente con
  `id_column`/`id_value`); 409 `DocumentoAmbiguoError`; 400 `ValueError` = no hay fila o BLOB
  vacío (contrato del que depende mcp-bbdd); codificación de `X-Document-Filename` con
  `unquote` y `Content-Disposition` `filename*` como fuente canónica; en `gra`, localizar por
  `ide` o por `key {emp, cod}`. Corregir de paso la frase de `MAX_INLINE_BINARY_BYTES`, que es
  de `sql/read` (JSON) y no aplica aquí.
- §10: consumidores de `documents/read` — albaranes-persistencia (`id_column ide`, lee
  `X-Document-Filename`), mcp-bbdd F-023 (`id_column cod`, `filename_columns ["cod"]`) y la
  F-139 del datamart (solo el índice; abre el binario mcp-bbdd).

## Verificación manual (R18) — humano, solo lectura

PowerShell 5.1, con `SIGRID_API_BASE_URL` y `SIGRID_API_FUNCTION_KEY` en el entorno (nunca en
fichero). **Antes del despliegue**, paso 0 y paso 4a; **después**, el resto. En `progress/` se
anota «coincide / no coincide», nunca el `nomori` ni el `cod` (llevan nombres de personas).

```powershell
$h = @{ "x-functions-key" = $env:SIGRID_API_FUNCTION_KEY }; $u = "$env:SIGRID_API_BASE_URL/api"
function Doc($cuerpo, $fichero) { Invoke-WebRequest -UseBasicParsing -Method Post -Uri "$u/documents/read" -Headers $h -ContentType "application/json" -Body $cuerpo -OutFile $fichero -PassThru }
# 0. Clave y nombre de la fila (sql/read)
Invoke-RestMethod -Method Post -Uri "$u/sql/read" -Headers $h -ContentType "application/json" -Body '{"database":"ruesma_rep","sql":"SELECT emp, cod, nomori FROM dbo.gra WHERE ide = ?","parameters":[365617]}'
# 1. Por ide con nomori: 200, cabecera ASCII que decodifica al nomori del paso 0
$r1 = Doc '{"database":"ruesma_rep","table":"gra","id_column":"ide","id_value":365617,"blob_column":"ima","filename_columns":["nomori"]}' f010_ide.bin
$r1.StatusCode; [Uri]::UnescapeDataString($r1.Headers["X-Document-Filename"]); $r1.Headers["Content-Disposition"]
# 2. Misma fila por key: mismo tamaño y mismo hash (sustituir <emp> y <cod> del paso 0)
$r2 = Doc '{"database":"ruesma_rep","table":"gra","key":{"emp":<emp>,"cod":"<cod>"},"blob_column":"ima","filename_columns":["nomori"]}' f010_key.bin
$r2.Headers["X-Document-Size"]; (Get-FileHash f010_ide.bin).Hash -eq (Get-FileHash f010_key.bin).Hash
# 3. Ambigüedad: 409 y DocumentoAmbiguoError
try { Doc '{"database":"ruesma_rep","table":"gra","id_column":"emp","id_value":1,"blob_column":"ima","filename_columns":["cod"]}' f010_amb.bin } catch { $_.Exception.Response.StatusCode.value__; (New-Object IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() }
```

4. Regresión de nombres ASCII: (a) antes de desplegar, elegir con `sql/read` un `ide` de
   `ruesma_rep.dbo.gra` cuyo `nomori` sea ASCII con espacios y guardar
   `X-Document-Filename` y `Content-Disposition` de `Doc` con ese `ide` y `["nomori"]`;
   (b) después, repetir y comparar: idénticos. Borrar `f010_*.bin` al terminar.

## Riesgos

- **Hallazgo fuera de alcance**: `documents/read` no valida `database` contra
  `ALLOWED_DATABASES` y la interpola en la cadena de conexión (`_connect`). Decisión del humano
  (informe, D6); no se toca aquí.
- `filename_columns: []` compone `SELECT TOP (2) , CAST(...)` → error de sintaxis → 500, como
  hoy. No lo pide nadie; anotado en el informe.
