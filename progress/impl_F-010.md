<!-- progress/impl_F-010.md -->
# Implementación F-010 · `documents/read`: nombres no ASCII y localización sin ambigüedad

Implementer, 2026-10-17. Rama `feature/F-010-documents-read-nombres-y-clave`, rigor `critico`.
Spec aprobada (D1-D5 y D7; **D6 fuera**, no implementado). Commits `b86a4c8` .. `c13686f` en la
rama y `0c4cbeb` en `azure-apps` (sin push en ninguno). No se ha llamado a la API desplegada,
ni a Azure, ni al SQL Server.

## Qué cambió

| Fichero | Cambio | R |
|---|---|---|
| `interface_adapters/http/http_response_factory.py` | `filename_header_value()` (porcentual UTF-8 de todo lo que no es ASCII imprimible 0x20-0x7E y del `%`); `X-Document-Filename` la usa; `quote(nombre, safe="")` en `Content-Disposition` | R1-R4 |
| `domain/models/sql_models.py` | `MAX_COLUMNAS_CLAVE = 4`; `DocumentReadRequest`: `id_column`/`id_value` opcionales, `key: dict[str, StrictInt \| StrictStr] \| None`, validador de `key` (vacío, >4, nombre en blanco, duplicado por `casefold`), validador de modelo (exclusión y ausencia), `localizacion()`; `_strip_identifier` deja `None` como `None` | R6-R9, R12 |
| `domain/models/document_models.py` | `DocumentoAmbiguoError(ValueError)`; `RawDocumentRecord` sin `id_value` | R13, R15 |
| `domain/ports/sql_repository.py` | `read_document(..., key=...)` con docstring de excepciones | R10-R14 |
| `infrastructure/repositories/sql_server_repository.py` | `build_document_query()` pura (valida schema, table, cada nombre de `key`, blob, filename; `SELECT TOP (2) … WHERE [c1] = ? AND …`); `read_document` con `fetchall()`: 0 filas → `ValueError`, >1 → `DocumentoAmbiguoError`, BLOB `NULL` → `ValueError` | R10-R14 |
| `application/use_cases/read_document_use_case.py` | Pasa `key=request.localizacion()`; reserva `document_<v1>_<v2>…` | R12, R15 |
| `function_app.py` | `except DocumentoAmbiguoError` → 409 `{type: DocumentoAmbiguoError}`, **antes** de los demás `except` | R13 |
| `../azure-apps/sigrid_api.md` | §8.3 reescrita (campos, `key`, cabeceras, `unquote`, `filename*` canónica, tabla de errores 400/409/500, corregida la frase de `MAX_INLINE_BINARY_BYTES`); §2.2 recomienda `key {emp, cod}`; §10: fila de mcp-bbdd al día y subsección «Consumidores de `documents/read`». Marcada **PENDIENTE DE DESPLIEGUE** | R16 |

Tests nuevos (157, sin red ni BBDD): `tests/test_f010_cabecera.py` (55), `test_f010_modelo.py`
(55), `test_f010_repositorio.py` (23; `_connect` doblado y `pyodbc.connect` sustituido por algo
que revienta), `test_f010_caso_de_uso.py` (9), `test_f010_ruta.py` (15). Ninguna aserción previa
tocada (R17); `test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho`: 4 passed.

## Decisiones y desviaciones respecto al diseño (justificadas)

1. **Validadores con `PydanticCustomError`, no `ValueError`** (design §B decía `ValueError`).
   Medido en T8: la ruta vuelca `exc.errors()` a JSON y un `ValueError` viaja dentro de `ctx`,
   así que el 400 de R7-R9 reventaba con `TypeError: Object of type ValueError is not JSON
   serializable` (500 en producción). Es el patrón que ya usa `sql_models.py`. Commit `fd06b96`
   y test `test_f010_r7_r9_los_errores_se_serializan_a_json`. Mismos textos que el diseño.
2. **`build_document_query` sin `zip`**: compone pares `(nombre validado, valor)`. La primera
   campaña dejó vivo `zip(strict=True -> False)`, que no podía dispararse: se quitó el código
   en vez de pedir aceptar un equivalente (`bb4a612`). Firma y retorno, los del diseño.
3. **`read_document` no revalida** schema/table/blob para los textos de error: usa `.strip()`
   sobre lo que `build_document_query` ya validó (el guardia solo recorta).
4. **SQL en una línea** (antes multilínea con sangría): es el texto exacto de R11.
5. **Nulos explícitos**: `key: null` y `id_column: null` equivalen a no traerlos (el diseño fija
   la presencia por `model_fields_set` solo para `id_value`). Efecto colateral, mejor que antes:
   `database`/`table`/… a `null` ya no se convierten en el texto `"None"`: dan 400.
6. `ruff`: los avisos nuevos en lo tocado se corrigieron (79 avisos totales frente a 80 al
   empezar); queda deuda previa en esos ficheros (`F401 quote` sin usar en el caso de uso, etc.).

## Fase RED (trazas reales)

Todas con `.venv/Scripts/python -m pytest <fichero> -q` antes del código de producción.

**T1 — cabecera (R1-R4)**, `tests/test_f010_cabecera.py`: `14 failed, 41 passed in 2.28s`.
```
E       AssertionError: assert False
E        +  where False = es_ascii_imprimible('Factura año señal.pdf')
E        +  where False = es_ascii_imprimible('informe 😀.pdf')
E        +  where False = es_ascii_imprimible('合同.pdf')
E        +  where False = es_ascii_imprimible('borrar\x7f.pdf')
E           AssertionError: assert 'x\x00y' == 'x%00y'
>       assert cabecera("a%20b.pdf") == "a%2520b.pdf"
E       AssertionError: assert 'a%20b.pdf' == 'a%2520b.pdf'
E       AssertionError: assert 'a b.pdf' == 'a%20b.pdf'          # unquote ambiguo (R2)
E       AttributeError: module '...http_response_factory' has no attribute 'filename_header_value'
E         + attachment; filename*=UTF-8''carpeta/fichero.pdf     # R4: "/" sin codificar
```
Verde tras T2: `55 passed in 0.86s`.

**T3 — modelo (R6-R9, R12)**, `tests/test_f010_modelo.py`: `16 failed, 24 passed in 0.71s`.
```
E       pydantic_core._pydantic_core.ValidationError: 2 validation errors for DocumentReadRequest
E       id_column
E         Field required [type=missing, input_value={'database': 'ruesma_rep'...'emp': 1, 'cod': 'ABC'}}, ...]
E       id_value
E         Field required [type=missing, ...]
FAILED tests/test_f010_modelo.py::test_f010_r9_el_tope_es_cuatro
FAILED tests/test_f010_modelo.py::test_f010_r12_localizacion_desde_id_column_es_una_clave_de_una_columna
```
(Los 24 que pasaban en rojo son rechazos, que el modelo viejo daba por falta de `id_column`.)
Verde tras T4: `40 passed`.

**T5 — adaptador (R10-R14)**, `tests/test_f010_repositorio.py`: `23 failed in 0.86s`.
```
E       AttributeError: module 'infrastructure.repositories.sql_server_repository' has no attribute 'build_document_query'
E       TypeError: SqlServerRepository.read_document() got an unexpected keyword argument 'key'
E       AttributeError: module 'domain.models.document_models' has no attribute 'DocumentoAmbiguoError'
```
RED de comportamiento de R13 (la razón de ser del 409), script en el scratchpad
(`red_ambiguo.py`, `python -I`) sobre el adaptador previo con un cursor falso de dos filas:
```
SQL: SELECT TOP (1) [nomori], [nom], CAST([ima] AS varbinary(max)) AS file_content FROM [dbo].[gra] WHERE [emp] = ?
Sirve sin error: ['primera.pdf'] b'%PDF-1'
```
Verde tras T6: `23 passed in 0.59s`.

**T7 — caso de uso (R12, R15)**, `tests/test_f010_caso_de_uso.py`: `9 failed in 0.64s`.
```
E       AttributeError: 'RawDocumentRecord' object has no attribute 'id_value'
FAILED tests/test_f010_caso_de_uso.py::test_f010_r12_id_column_llega_como_key_de_una_columna
FAILED tests/test_f010_caso_de_uso.py::test_f010_r15_reserva_con_dos_columnas_une_los_valores_en_orden
```
Verde tras adaptar el caso de uso: `9 passed in 0.44s`.

**T8 — ruta (R5, R7, R8, R13, R14)**, `tests/test_f010_ruta.py`. Primera ejecución (destapó la
desviación 1): 6 casos de R7-R9 con
```
E             Value error, key es excluyente con id_column/id_value. [type=value_error, ...]
E       TypeError: Object of type ValueError is not JSON serializable
```
Tras `fd06b96`, el rojo que queda es el del 409: `1 failed, 14 passed in 0.99s`
```
E       assert 400 == 409
FAILED tests/test_f010_ruta.py::test_f010_r13_ambiguedad_da_409_documento_ambiguo
```
Verde tras el `except`: `15 passed in 0.73s`. R5 ya pasaba en T8 porque su rojo es el de T1
(la cabecera la compone `binary_file_response`).

## Verificación

- T9 `python -m pytest -q`: `2521 passed, 1 skipped` (antes de los tests de nulos); final dentro
  de `init.sh`: `2527 passed, 1 skipped, 1 warning in 47.84s`.
- T10 `git diff dev --stat -- infrastructure/security config scripts`: **vacío**.
- T11: dos campañas en serie (ver «Evidencias»). La paralela no arrancó: el fichero sin
  seguimiento `` `0`].{t `` de la raíz cuenta como «árbol con cambios» y la herramienta exige
  `--workers 1`. No lo he tocado ni incluido en ningún commit.
- T12: `azure-apps` `0c4cbeb` (revisión del reviewer contra el código).
- T16 `bash harness/init.sh`: **ENTORNO LISTO** (ver «Evidencias»).

## Fuera de alcance (sin tocar)

- **D6**: `documents/read` sigue sin validar `database` contra `ALLOWED_DATABASES` y `_connect`
  la interpola en la cadena de conexión. Feature aparte, por decisión del humano.
- `sigrid-api-v2` (mismo fallo de cabecera), `scripts/invoke_api_examples.py` (guarda con el
  nombre sin decodificar), `filename_columns: []` → 500 como antes (documentado en §8.3).
- Consumidores: ningún cambio en albaranes, mcp-bbdd ni datamart.

## Pendiente (lo coordina el líder con el humano)

- **T13 MANUAL (humano), antes de desplegar, solo lectura**: paso 0 y 4a de design
  §Verificación manual (cabeceras de un `ide` con `nomori` ASCII con espacios, guardadas fuera
  del repo).
- **Aviso a albaranes antes de desplegar** (`albaranes [dd1842]`): `X-Document-Filename` puede
  llevar `%XX`; decodificar con `unquote`.
- **T14 MANUAL (humano)**: `func azure functionapp publish func-sigridapi-dev-huyke --python`
  desde `dev` tras el merge; sin App Settings nuevas.
- **T15 MANUAL (humano), solo lectura**: pasos 1-3 y 4b (ide 365617 con `nomori` → 200 y nombre
  decodificado igual; misma fila por `key {emp, cod}` → mismo hash; `id_column emp` → 409;
  cabeceras ASCII idénticas a las de T13).
- Tras desplegar: quitar en `azure-apps/sigrid_api.md` §8.3 el aviso «PENDIENTE DE
  DESPLIEGUE» y avisar a mcp-bbdd y datamart.
- Revisión del reviewer contra `CHECKPOINTS.md`; `done` solo tras su APROBADO.

## Evidencias

| Evidencia | Valor medido |
|---|---|
Medidas sobre la punta `913761a` (posterior a H1 `64ffde0`; H3 de `review_F-010.md`).

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite completa, `init.sh`) | **2530 passed, 1 skipped**, 0 failed, 47,87 s |
| Tests de F-010 | 160 (55 cabecera + 55 modelo + 24 repositorio + 11 caso de uso + 15 ruta, por `pytest --co`), todos en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 80 líneas cambiadas cubiertas (80/80, umbral 80%, nivel critico)` (antes de los tests de nulos: 97,5 %, 78/80; las dos líneas eran los `return None` de `null` explícito) |
| Mutación, ronda 1 (`bef6a25`, `--workers 1`) | 24 generados, 22 muertos, **2 supervivientes**, 0 timeouts, 246,7 s |
| Mutación, ronda 2 (`bb4a612`, `--workers 1`, previa a H1) | 23 generados, 23 muertos, 0 supervivientes, 155,4 s, 198 líneas |
| Mutación, ronda final (`913761a`, `--workers 1`) | 209 líneas en alcance; **24 generados, 24 evaluados, 24 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto, 148,3 s, línea base 45,6 s, media 6,2 s/mutante, timeout 120 s → [`mutacion_F-010.md`](mutacion_F-010.md). El mutante nuevo respecto a la ronda 2 es el de H1 (`read_document_use_case.py:26`, `is not None → is None`): muerto |
| Análisis de supervivientes (ronda 1) | 1) `min_length=1→2` de `id_column`: hueco real, test nuevo; **medido** con el mutante aplicado a mano: `1 failed, 54 passed`. 2) `zip(strict=True→False)`: estrictez inalcanzable, código quitado (24→23 mutantes). Detalle en el informe de mutación. Ronda final: sin supervivientes que analizar |
| Tiempo de la suite | 47,87 s (`init.sh`); línea base de la campaña final 45,6 s |
| `bash harness/init.sh` final | **ENTORNO LISTO**; ruff 79 avisos (deuda previa, no bloquea); PUERTA TAMAÑO en verde |

## Corrección H1 (review_F-010_C1C3C5.md, opción a)

**Qué cambió.** Con `id_column` no válido el error decía `'key'`; R12 exige el texto de `dev`
(`dev:infrastructure/repositories/sql_server_repository.py`, `field_name="id_column"`).
`build_document_query` y `read_document` (adaptador y puerto) aceptan `key_field_name: str =
"key"`, que solo cambia el nombre citado por `IdentifierGuard` para los nombres de `key`; el caso
de uso pasa `"id_column"` si la petición no trae `key`. SQL, parámetros, orden de validación,
código 400 y tipo `IdentifierValidationError` sin cambios. `infrastructure/security/` sin tocar.
Ficheros: `infrastructure/repositories/sql_server_repository.py`, `domain/ports/sql_repository.py`,
`application/use_cases/read_document_use_case.py`, `tests/test_f010_caso_de_uso.py` (2 tests
nuevos sobre el adaptador real, sin conexión; 2 aserciones de `key_field_name` en los existentes),
`tests/test_f010_repositorio.py` (1 test nuevo).

**RED** (test escrito antes del arreglo):
`.venv/Scripts/python -m pytest tests/test_f010_caso_de_uso.py -q -k "conserva_su_texto"`
```
E       AssertionError: assert 'El identific...itidos: ide;x' == 'El identific...itidos: ide;x'
E         - El identificador 'id_column' contiene caracteres no permitidos: ide;x
E         ?                   ^^^^^^^^^
E         + El identificador 'key' contiene caracteres no permitidos: ide;x
E         ?                   ^^^
FAILED tests/test_f010_caso_de_uso.py::test_f010_r12_id_column_no_valido_conserva_su_texto
```
**GREEN**: los 5 ficheros `test_f010_*` + `test_f004_route`, `test_f006_route`,
`test_f009_route` → `222 passed`. F-010 pasa de 157 a 160 tests.

**Mutantes aplicados a mano** (los 5 ficheros `test_f010_*`, restaurado tras cada uno):
M1 adaptador vuelve a `field_name="key"` → `2 failed, 158 passed`; M2 `read_document` no reenvía
el argumento → `2 failed`; M3 el caso de uso pasa siempre `"key"` → `2 failed`; M4 condición
invertida → `4 failed`; M5 el caso de uso no pasa el argumento → `3 failed`. Los cinco, muertos.

**No ejecutado aquí, a propósito** (encargo del líder): `bash harness/init.sh` ni la campaña de
mutación (corre en otro worktree). Ambas se ejecutaron después sobre `913761a` (corrección H3):
la tabla «Evidencias» de arriba ya refleja esta corrección.
