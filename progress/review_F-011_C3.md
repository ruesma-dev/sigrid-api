Revisión completa (pasada 1) · bloque C3 y C3 bis · `git diff dev...HEAD` con HEAD `4d1c266a6bce40566e1aa9cb7dca79424229e399`

# F-011 · Revisión acotada: C3 y C3 bis

- **Veredicto del bloque:** APPROVED
- **Alcance del encargo:** solo C3 (arquitectura, convenciones, reglas de Sigrid), C3 bis, fidelidad del
  código a la spec (R1-R17, design), ficheros vedados, secretos y documentación (`docs/ARCHITECTURE.md` y
  `../azure-apps/sigrid_api.md`, commit `7bddfd4`). C1, C2, C4, C4 bis y C5 los revisan otros encargos.
- **Nivel de rigor:** `critico` (declarado en la spec). Las puertas que exige (RED, cobertura, mutación,
  RM1-RM6) son de C4 bis y quedan fuera de este bloque.
- **Lo que NO se ejecutó, por encargo:** ni `bash harness/init.sh` ni la suite completa (otra revisión
  corre la campaña de mutación). Sí tests concretos: `tests/test_f011_*.py`, `tests/test_f010_caso_de_uso.py`
  y `tests/test_f010_ruta.py` → **160 passed, 1 warning in 3.56s**.

## C3 — El código respeta arquitectura y convenciones

- [x] **Hexagonal.** `domain/models/document_models.py` añade `BaseNoPermitidaError(ValueError)` sin
  importar nada nuevo. `application/use_cases/read_document_use_case.py` importa `config.settings.Settings`
  y el dominio (precedente: `execute_sql_query_use_case.py`, como dice el design). El adaptador
  `sql_server_repository.py` usa `IdentifierGuard`, que ya importaba. La composición sigue en
  `build_dependencies()` de `function_app.py`, con la tupla de ocho intacta.
- [x] **Primera línea con ruta** en los 4 ficheros de producción tocados y en los 4 tests nuevos.
- [x] **Sin `print()`, sin TODO, sin secretos, sin dependencias nuevas.** Barrido del diff (`print(`,
  `TODO|FIXME|XXX|breakpoint|pdb`): sin aciertos. `requirements.txt` y `pyproject.toml` sin diff contra
  `dev`. Las claves de los tests (`no-es}una-clave`, `tampoco`, `no-es-una-clave`) son de mentira, con
  precedente en `tests/test_f010_repositorio.py`. ruff sobre los ficheros cambiados: los 10 avisos
  existían ya en `dev` (F401 de `quote`, PIE810, UP035, S110/BLE001 del adaptador). Ninguno es de F-011.
- [x] **Reglas de dominio de Sigrid:**
  - [x] Base correcta: `documents/read` sigue leyendo `ruesma_rep`. No se abre ninguna escritura nueva y
    `ruesma_rep` sigue fuera de `ALLOWED_WRITE_DATABASES`.
  - N/A `cod/res/fec/tip/est` en `con`: F-011 no añade ni cambia SQL (design §SQL).
  - N/A Nada se recalcula solo: no hay escrituras nuevas.
  - N/A Estados: no se resuelve ni se escribe ningún estado.
  - [x] SQL parametrizado: no hay SQL nuevo. La única composición de texto que se toca, la cadena ODBC,
    queda **más** cerrada: `DATABASE={safe_database};` con el valor validado.

**Fidelidad a la spec (R1-R15, design):** sin desviaciones.
- R1/R4: texto `La base de datos '<db>' no está permitida. Permitidas: <a, b>` o `(ninguna)`, igual al
  glosario. R2/R6: `_validar_base` es la primera línea de `run`, antes de `localizacion()` y de
  `read_document`. R3: `not in` es una comparación exacta sobre el valor que el modelo ya recorta.
  R7: `ReadDocumentUseCase(repository, settings)` con el mismo `settings`. R8: hereda de `ValueError` y el
  `except BaseNoPermitidaError` va antes que `IdentifierValidationError` y `ValueError`, con
  `details={"type": "BaseNoPermitidaError"}` literal. R9: `logger.warning("BaseNoPermitidaError en
  documents/read: %s", exc)`.
- R13-R15: `_connect` valida con `IdentifierGuard.validate_identifier(database, field_name="database")`
  y usa el valor que devuelve. Los 8 métodos públicos que conectan pasan por `_connect`, y es el único
  `pyodbc.connect` del código de producción (comprobado con grep). El texto de R14 sale tal cual del
  guardia, que cita el valor sin recortar.
- **Ficheros:** los previstos en el design. `harness/features.json`, `BACKLOG.md` y `progress/current.md`
  vienen de los commits de spec del líder. `git diff --stat dev...HEAD -- infrastructure/security config
  domain/models/sql_models.py scripts interface_adapters` sale **vacío**. `.env` no está versionado.
  `tests/test_f010_caso_de_uso.py` solo cambia las dos construcciones (R12).

## C3 bis — Documentos que entran de fuera

- N/A, los cuatro checkboxes: el diff no añade ni modifica nada en `docs/referencia/` (0 ficheros) ni
  incorpora PDF ni ofimática.

## Secretos (diff, specs, progress y `azure-apps` 7bddfd4)

Barrido propio sobre las líneas añadidas de `git diff dev...HEAD` (que incluye `specs/` y `progress/`) y
sobre `git show 7bddfd4` en `azure-apps`. Patrones: correo, IPv4, GUID, `password\s*[=:]`, `pwd=` sin
llave, `secret`, `api[_-]?key`, `x-functions-key`, `code=`, `AccountKey`, `SharedAccess`, `Bearer `, JWT
`eyJ…`, y base64 de 40 caracteres o más. **Aciertos:** solo SHAs de git (40 hex) y las claves de mentira
de los tests. Ninguna IP, GUID, cadena de conexión ni function key. Los nombres
`func-sigridapi-dev-huyke` y `rg-sigrid-dev-data-api` del design ya estaban en `dev` (3 ficheros) y no son
de la lista de CLAUDE.md.

## Documentación (R16): fiel a lo implementado

- `docs/ARCHITECTURE.md`: el párrafo de listas blancas (validación en el caso de uso, igualdad exacta,
  antes de los identificadores y de conectar, `details.type` nunca `"ValueError"`) y la viñeta de
  `_connect` (A1 para toda la API, dry-run de dominio, lista mal configurada, 400 sin conectar) coinciden
  con el código y con mi prueba de abajo.
- `azure-apps/sigrid_api.md`: §4 (fila `ALLOWED_DATABASES`), §4.1 (nota «lectura y documentos», cierta
  desde F-011), §5.1 capas 3 y 6, §7.2 (base del dry-run), §8.3 (nota, fila `database`, fila nueva y fila
  `IdentifierValidationError` ampliada) y §10 (efecto nulo; para mcp-bbdd es «origen no disponible»).
  Todo coincide con el código. Las notas «PENDIENTE DE DESPLIEGUE» son correctas mientras T12-T14 sigan
  abiertas. El commit está en local, sin push.
- Imprecisión menor, que **no bloquea**: §5.1 capa 6 enumera «espacios» entre lo que se rechaza. Los
  **interiores** se rechazan, pero los de alrededor se recortan y conectan (el efecto lateral de abajo).
  La fila `database` de §8.3 sí lo dice bien. El comentario de `_connect` arrastra la misma ambigüedad.
  Sugerencia: escribir «espacios interiores».

## Efecto lateral declarado: `IdentifierGuard` recorta

Es benigno. Todos los modelos de entrada ya recortan `database` antes de llegar al adaptador: `sql_models`
(lectura, escritura, documentos), `sigrid_domain_models`, `albaran_domain_models`,
`albaran_directo_models` y `albaran_compra_models` (`mode="before"`), `parte_reclamacion_models` y
`concepto_grafico_models`. Las listas `ALLOWED_*` salen recortadas de `parse_string_list`, y la base
documental se recorta en `attach_concepto_grafico_use_case.py` l. 165. El recorte tampoco abre un rodeo:
las listas blancas se comparan **antes** de `_connect` y con el valor ya recortado. Solo lo notaría un
llamador interno que pasara la base sin recortar, y hoy no hay ninguno. Además está fijado por
`test_f011_r13_se_usa_el_valor_que_devuelve_el_guardia`.

## Hallazgo del modo extendido de `sigrid/albaran`: cubierto por A1, comprobado

En el código, `_comprobar_guardas` (`create_albaran_compra_use_case.py`) hace `return` en dry-run antes
de mirar `allowed_write_databases`, y `_leer` usa `SqlReadRequest.model_construct(database=...)`, que se
salta el `SqlQueryGuard`. `run` relanza toda excepción (`except Exception: … raise`), y
`_sigrid_albaran_extendido` se llama dentro del `try` de `sigrid_albaran`, así que el
`IdentifierValidationError` acaba en el `except ValueError` → 400.

**Verificación propia, sin red:** script en el scratchpad (`f011_dominio.py`) con
`Settings.model_construct` (no lee `.env`), `get_settings` doblado y `pyodbc.connect` prohibido. Llama a
las rutas **reales** con `database: "ruesma;APP=f011"` en dry-run:

| Ruta | Con A1 (HEAD) | Sin A1 (guardia neutralizado en memoria) |
|---|---|---|
| `sigrid/contrato-lineas` | 400 `IdentifierValidationError` | 500, conexión intentada |
| `sigrid/albaran` clásico | 400 `IdentifierValidationError` | 500, conexión intentada |
| `sigrid/albaran` extendido | 400 `IdentifierValidationError` | 500, conexión intentada |
| `sigrid/albaran-directo` | 400 `IdentifierValidationError` | 500, conexión intentada |
| Conexiones a `pyodbc.connect` | **0** | **4** |

`partes-reclamacion` y `concepto-grafico` validan la base contra la lista antes de leer, y sus
`except Exception` relanzan. **Conclusión:** A1 cubre los cuatro huecos de dry-run, como dice el informe.
El **residual** declarado es real y queda fuera de F-011: una base que case con el patrón (p. ej.
`master` u otra de la instancia a la que llegue `ro_user`) se sigue leyendo en esas previas, con SQL fijo.
`sigrid_api.md` §5.1 lo dice. Recomiendo que el líder lo registre como feature.

## Observaciones fuera de alcance (no bloquean F-011)

1. **500 en vez de 400, previo a F-011 (F-009):** en el modo extendido de `sigrid/albaran`, un error de
   `model_validator` (p. ej. línea vinculada sin `cod_contrato`) produce `exc.errors()` con un
   `ValueError` en `ctx`. `error_response` no lo serializa y la petición acaba en **500 `TypeError: Object
   of type ValueError is not JSON serializable`**. Lo reproduje con el mismo script. `function_app.py`
   l. 261-271 no lo toca F-011. Conviene una feature que use `exc.errors(include_context=False)` o
   equivalente, y que mire si otras rutas tienen el mismo patrón.
2. En la raíz del repositorio hay un fichero sin seguimiento llamado `` `0`].{t `` que ya estaba al
   empezar la sesión. No es de F-011. Que el humano decida si se borra.

## Cambios requeridos

Ninguno en este bloque. La sugerencia de «espacios interiores» es opcional.

Estado del árbol tras la revisión: `git status` sin cambios propios, salvo este informe (sin commit).
