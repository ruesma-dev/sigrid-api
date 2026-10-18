# F-011 · Diseño: `documents/read` valida `database`

> **Aprobada por el humano el 2026-10-18** con D1 = `ALLOWED_DATABASES` tal cual, D2 = **A1**, D3 = 400 `BaseNoPermitidaError` listando las bases permitidas y D4 = sensible a mayúsculas. Las tareas y requisitos marcados [A1] / «solo con A1» **aplican**. El humano autoriza también el paso 5 de la verificación manual (un dry-run de `sigrid/contrato-lineas` con una base inyectada, sin `commit`).

Requisitos en [`requirements.md`](requirements.md). Rigor `critico`.

## Contexto medido en el código (2026-10-18)

- `DocumentReadRequest` (`domain/models/sql_models.py`) solo recorta `database`;
  `ReadDocumentUseCase.run` y la ruta `documents_read` de `function_app.py` lo
  pasan tal cual; `SqlServerRepository.read_document` → `_connect` lo interpola en
  `DATABASE={database};`.
- `sql/read` y `sql/write` lo validan con su guardia (`database not in lista`).
- **Hallazgo: el hueco no es solo de `documents/read`.** `sigrid/contrato-lineas`
  conecta en dry-run con `request.database` sin lista blanca: la comprobación de
  `ALLOWED_WRITE_DATABASES` está en el paso 6 de `add_contract_lines_use_case.py`
  (l. 171), solo con `commit`, y la primera lectura (`locate_contract`, l. 39) ya
  conecta. El albarán clásico (l. 506) y `albaran-directo` (l. 299) siguen el
  mismo patrón (a confirmar por el implementer). Solo lo cierra D2 = A1.
- Todas las rutas capturan `ValueError` → 400 con `details.type` = clase.
- mcp-bbdd (`cliente_documentos.py` l. 220): 400 con `details.type == "ValueError"`
  → «sin binario»; cualquier otro 400 → «origen no disponible». Los tres
  consumidores mandan la constante `ruesma_rep`.

## Decisiones (las cuatro necesitan al humano)

**D1 · Qué lista. Recomendado: `ALLOWED_DATABASES` tal cual.**
- (a) **`ALLOWED_DATABASES`** — misma frontera que `sql/read`, con la misma
  credencial `ro_user`. Una lista más estrecha no protege nada: `sql/read` ya lee
  cualquier tabla de esas bases, y por nombre de tres partes la de `ruesma_rep`
  desde `ruesma`. Sin App Setting nueva ni paso de despliegue. Además hace cierta
  la línea de `azure-apps/sigrid_api.md` §4.1 (`ALLOWED_DATABASES … # lectura y
  documentos`), que hoy es falsa.
- (b) App Setting nueva `ALLOWED_DOCUMENT_READ_DATABASES` (p. ej. `["ruesma_rep"]`,
  defecto `[]` = cerrado). Saca `master` y `ruesma` de `documents/read`, que solo
  sirve binarios. Coste: `config/settings.py` y su validador; y un paso de
  despliegue **antes** de publicar el código, porque con el defecto cerrado los
  tres consumidores recibirían 400:
  `az functionapp config appsettings set -n func-sigridapi-dev-huyke -g
  rg-sigrid-dev-data-api --settings "@f011.json"` con
  `[{"name":"ALLOWED_DOCUMENT_READ_DATABASES","value":"[\"ruesma_rep\"]","slotSetting":false}]`
  (JSON ASCII sin BOM, §11), y releerla antes de `func publish`.
- (c) `SIGRID_DOCUMENT_WRITE_DATABASE` — **descartada**: es la llave de la
  escritura documental; atar la lectura a ella acopla dos interruptores (vaciarla
  para apagar `concepto-grafico` cortaría las lecturas).
- (d) Constante `"ruesma_rep"` en el código — descartada: configuración en código.
- `master` en `ALLOWED_DATABASES` es otra decisión (afecta a `sql/read`; la lista
  desplegada la copian `tests/test_sql_query_guard_bases.py` y
  `scripts/verificar_sql_ecosistema.py`): queda **fuera** de F-011.

**D2 · ¿Se blinda `_connect` para todos los endpoints? Recomendado: A1.**
- **A1 · `IdentifierGuard.validate_identifier(database, field_name="database")`
  dentro de `_connect`** (R13-R15). No modifica `infrastructure/security/`: solo
  lo usa, como ya hace el adaptador con tablas y columnas y el caso de uso
  documental con la base de `SIGRID_DOCUMENT_WRITE_DATABASE`. **Sí es un cambio
  de seguridad en el adaptador compartido**: lo atraviesan las ocho conexiones de
  todos los endpoints. Cierra el hueco de dominio del contexto y el de una lista
  blanca mal configurada. Riesgo: un nombre de base fuera del patrón (guion,
  dígito inicial) dejaría de conectar; las tres de hoy pasan, y T12 lo comprueba
  en las App Settings antes de desplegar.
- A0 · No tocar `_connect`. Cumple el acceptance para `documents/read` (R1-R5),
  pero deja abierto el hueco de dominio. Si el humano elige A0: fuera R13-R15, T5
  y T6, y el paso 5 de §Verificación manual.
- A2 · Escapar con llaves (`DATABASE={…}`, `}`→`}}`, como `PWD`). Descartada:
  neutraliza sin rechazar, admite nombres arbitrarios y su semántica depende del
  driver, que no se puede verificar sin BBDD.
- A3 · Validar `database` en cada modelo de dominio. Descartada: seis contratos
  públicos para lo que un punto único resuelve.
- A4 · Validar las listas `ALLOWED_*` al arrancar. Descartada: toca
  `config/settings.py` y un valor raro tumbaría la Function entera.

**D3 · Código y tipo del rechazo. Recomendado: 400 `BaseNoPermitidaError`,
texto paralelo al de `sql/read`.** No es `ValueError` (R8: mcp-bbdd lo leería como
«sin binario»), ni `QueryValidationError` (es de `sql/read`), ni 403 (el resto de
validaciones de la API es 400). El texto lista las bases permitidas como
`sql/read` (requiere la function key; la lista ya se ve allí). Alternativa: no
listarlas.

**D4 · Comparación exacta y sensible a mayúsculas** (R3), como `SqlQueryGuard`.
SQL Server no distingue mayúsculas en nombres de base, pero los consumidores
mandan la constante exacta y la paridad con `sql/read` evita dos semánticas.

## Ficheros a crear

- `tests/test_f011_caso_de_uso.py` — R1-R8, R10, R12 en el caso de uso, con
  repositorio doble que registra o revienta y ajustes `SimpleNamespace`.
- `tests/test_f011_ruta.py` — R1, R8, R9, R11 por la ruta: `build_dependencies`
  doblado a la tupla de ocho con el `ReadDocumentUseCase` **real** sobre
  repositorio doble (que revienta si se le llama) y ajustes doble.
- `tests/test_f011_composicion.py` — R7: `build_dependencies()` entrega a
  `ReadDocumentUseCase` el mismo objeto `Settings` que a `ExecuteSqlQueryUseCase`
  (con `get_settings` doblado y `cache_clear()` antes y después; nunca `Settings`
  leído del entorno: lección de F-004 T14c).
- `tests/test_f011_repositorio.py` — **solo con A1**: R13-R15 sobre el adaptador
  real con `pyodbc.connect` sustituido por un doble que captura la cadena.

## Ficheros a modificar

- `domain/models/document_models.py` — añade `BaseNoPermitidaError(ValueError)`,
  con docstring como el de `DocumentoAmbiguoError`.
- `application/use_cases/read_document_use_case.py` — constructor
  `__init__(self, repository: SqlRepository, settings: Settings)`; primera línea
  de `run`: `self._validar_base(request.database)`.
- `function_app.py` — `ReadDocumentUseCase(repository, settings)` en
  `build_dependencies()` (la tupla sigue de ocho posiciones); en `documents_read`,
  `except BaseNoPermitidaError` **antes** de `except IdentifierValidationError` y
  de `except ValueError`.
- `infrastructure/repositories/sql_server_repository.py` — **solo con A1**: en
  `_connect`, `safe_database = IdentifierGuard.validate_identifier(database,
  field_name="database")` antes de componer la cadena, y `DATABASE={safe_database};`.
- `tests/test_f010_caso_de_uso.py` — solo las dos construcciones
  `ReadDocumentUseCase(...)` (l. 40 y 123) reciben
  `SimpleNamespace(allowed_databases=["ruesma_rep"])`. Ninguna aserción (R12).
- `docs/ARCHITECTURE.md` — párrafo «Las listas blancas de bases se aplican dos
  veces»: `documents/read` valida `database` contra `ALLOWED_DATABASES`; con A1,
  `_connect` exige el patrón de identificador a toda base.
- `../azure-apps/sigrid_api.md` — ver §Documentación.

## Ficheros que NO se tocan

- `infrastructure/security/**` (también con A1: `IdentifierGuard` se usa, no se
  cambia), `config/settings.py` (con D1 = a), `domain/models/sql_models.py`
  (la validación no va en el modelo: necesita configuración), los casos de uso de
  dominio (A1 los cubre desde el adaptador), `scripts/`, `interface_adapters/`.
- `harness/features.json` y `BACKLOG.md`: los mueve el líder.

## Clases y funciones

- **domain** · `class BaseNoPermitidaError(ValueError)` — sin atributos; el texto
  va en el mensaje. Hereda de `ValueError` por la misma razón que
  `DocumentoAmbiguoError`.
- **application** · `ReadDocumentUseCase._validar_base(self, database: str) -> None`
  — `permitidas = self._settings.allowed_databases`; si `database not in
  permitidas`, lanza `BaseNoPermitidaError(f"La base de datos '{database}' no está
  permitida. Permitidas: {', '.join(permitidas) or '(ninguna)'}")`. Lee la lista en
  cada llamada (como `SqlQueryGuard`). Va antes de `request.localizacion()` y de
  `read_document` (R2, R6). La importación de `config.settings` desde
  `application` tiene precedente (`execute_sql_query_use_case.py`).
- **entrada** · rama nueva de `documents_read`:
  `logger.warning("BaseNoPermitidaError en documents/read: %s", exc)` y
  `error_response(str(exc), status_code=400, details={"type": "BaseNoPermitidaError"})`
  — literal, como el 409 de F-010, no `type(exc).__name__`.
- **infrastructure (A1)** · `_connect`: el cambio de arriba; la firma no cambia.
  Con A1, si la lista de lectura trajera por error `ruesma_rep;APP=x`, esa
  petición pasaría `_validar_base` y la cortaría el adaptador: 400
  `IdentifierValidationError` por el `except` que ya existe, sin conectar (test
  en `test_f011_ruta.py` con el adaptador real y `pyodbc.connect` prohibido).

## Errores de `documents/read` tras F-011

| Código | `details.type` | Cuándo | Cambia |
|---|---|---|---|
| 400 | `BaseNoPermitidaError` | `database` fuera de `ALLOWED_DATABASES` | **nuevo** |
| 400 | `ValidationError` | cuerpo mal formado | no |
| 400 | `IdentifierValidationError` | identificador no válido (y, con A1, base fuera del patrón) | solo su alcance |
| 400 | `ValueError` | sin binario (mcp-bbdd) | no |
| 409 | `DocumentoAmbiguoError` | más de una fila | no |
| 500 | la excepción | inesperado | no |

## SQL

No aplica: ni SQL nuevo ni cambios en el de `build_document_query`.

## Encaje en la arquitectura y límite del microservicio

Validación de entrada del propio servicio, en la capa que ya tiene la
configuración (application), como los casos de uso de dominio con
`ALLOWED_WRITE_DATABASES`; la defensa de A1 en infrastructure, junto a la de
identificadores. Dentro del límite: no hay nada que extraer.

## Riesgos

- **Mayúsculas** (D4): un consumidor nuevo que mande `RUESMA_REP` recibirá 400.
- **A1**: base desplegada fuera del patrón → caída de todos los endpoints. T12 lo
  descarta leyendo las App Settings antes del despliegue.
- **Mutación**: `or '(ninguna)'` y el orden de los `except` exigen tests con lista
  vacía y no vacía, y el `details.type` literal comparado con `!= "ValueError"`.
- **Logs**: el valor rechazado viaja al `warning`, igual que hoy en `sql/read`.

## Documentación (T11, `azure-apps`, commit aparte, sin push)

- §8.3: fila `database` («debe estar en `ALLOWED_DATABASES`, comparación exacta;
  hoy `ruesma_rep`»), fila nueva en la tabla de errores, nota F-011 con fecha y
  verificación.
- §5.1: en la capa 3 (o nueva), `documents/read` valida la base; con A1, la
  capa 6 añade que `_connect` exige el patrón a toda base.
- §4: la fila `ALLOWED_DATABASES` dice «lectura (`sql/read`) y `documents/read`».
- §10 «Consumidores de `documents/read`»: efecto nulo (mandan `ruesma_rep`);
  para mcp-bbdd el 400 nuevo es «origen no disponible», no «sin binario».

## Verificación manual (solo lectura; la ejecuta el líder)

Patrón de §8.3 de `azure-apps/sigrid_api.md` (`$base`, `$headers` con la function
key del `.env` local; nada de ello se escribe en el repo). Cuerpo base:
`{"table":"gra","id_column":"ide","id_value":365617,"blob_column":"ima","filename_columns":["nomori"]}`.

- **Paso 0 (T12, antes de desplegar)**: `az functionapp config appsettings list
  -n func-sigridapi-dev-huyke -g rg-sigrid-dev-data-api --query "[?name=='ALLOWED_DATABASES'
  || name=='ALLOWED_WRITE_DATABASES' || name=='SIGRID_DOCUMENT_WRITE_DATABASE'].{clave:name,
  valor:value}" -o table`. Esperado: `ruesma_rep` literal en `ALLOWED_DATABASES`;
  con A1, todos los valores casan con `^[A-Za-z_][A-Za-z0-9_]*$`. Si no, PARAR.
- **Paso 1**: `database: "ruesma_rep"` → 200, `X-Document-Size` 17865.
- **Paso 2**: `database: "base_inexistente_f011"` → 400, `details.type`
  `BaseNoPermitidaError`, texto de R1. Cualquier otra respuesta: PARAR (no está
  el código nuevo).
- **Paso 3** (solo si el 2 da lo esperado): `"ruesma_rep;APP=f011"` y
  `"RUESMA_REP"` → 400 `BaseNoPermitidaError`.
- **Paso 4**: `sql/read` con `{"database":"ruesma_rep","sql":"SELECT ide FROM
  dbo.gra WHERE ide = ?","parameters":[365617]}` → 200, una fila.
- **Paso 5** (solo con A1, y con autorización del humano para esta llamada
  concreta aunque sea dry-run): `sigrid/contrato-lineas` con `commit:false`,
  `database:"ruesma;APP=f011"` y campos de relleno → 400
  `IdentifierValidationError` sin conectar.
