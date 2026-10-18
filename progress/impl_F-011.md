<!-- progress/impl_F-011.md -->
# F-011 · Informe del implementer

Rama `feature/F-011-documents-read-valida-database`. Rigor `critico`. Decisiones aprobadas: D1 =
`ALLOWED_DATABASES`, D2 = **A1**, D3 = 400 `BaseNoPermitidaError` listando las bases, D4 = sensible a
mayúsculas. Hechas **T1-T11 y T15**; **T12-T14 son MANUAL** (líder/humano) y siguen abiertas. No se ha
llamado a la API desplegada ni al SQL Server.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `domain/models/document_models.py` | `class BaseNoPermitidaError(ValueError)`, con docstring como el de `DocumentoAmbiguoError` |
| `application/use_cases/read_document_use_case.py` | constructor `(repository, settings)`; `_validar_base` es la primera línea de `run` (antes de `localizacion()` y de `read_document`); igualdad exacta contra `settings.allowed_databases`, leída en cada llamada; texto `La base de datos '<db>' no está permitida. Permitidas: <a, b>` o `(ninguna)` |
| `function_app.py` | `ReadDocumentUseCase(repository, settings)` (la tupla sigue de ocho); `except BaseNoPermitidaError` antes de `IdentifierValidationError` y de `ValueError`, con `warning` y `details={"type": "BaseNoPermitidaError"}` **literal** |
| `infrastructure/repositories/sql_server_repository.py` | A1: en `_connect`, `safe_database = IdentifierGuard.validate_identifier(database, field_name="database")` y `DATABASE={safe_database};`. Vale para los 8 métodos que conectan |
| `tests/test_f010_caso_de_uso.py` | solo las 2 construcciones de `ReadDocumentUseCase` reciben `SimpleNamespace(allowed_databases=["ruesma_rep"])`; ninguna aserción cambia (R12) |
| `tests/test_f011_caso_de_uso.py` (28) | R1-R6, R8, R10 |
| `tests/test_f011_ruta.py` (15) | R1, R4, R8, R9, R10, R11 y el caso A1 de lista mal configurada |
| `tests/test_f011_composicion.py` (2) | R7 |
| `tests/test_f011_repositorio.py` (89) | R13-R15 en los 8 métodos del adaptador |
| `docs/ARCHITECTURE.md` | párrafo de listas blancas + viñeta nueva de `_connect` (T10) |
| `azure-apps/sigrid_api.md` | §4, §4.1, §5.1 (capas 3 y 6), §7.2, §8.3 (nota, fila `database`, tabla de errores) y §10. Commit **`7bddfd4`** en `azure-apps`, sin push. Notas «PENDIENTE DE DESPLIEGUE» hasta T14 |

No se tocó `infrastructure/security/`, `config/`, `scripts/`, `interface_adapters/` ni
`domain/models/sql_models.py` (T8: `git diff dev --stat -- …` vacío). Ni `.env`, ni `features.json`, ni
`BACKLOG.md`.

## Lo que había que confirmar: ¿el dominio conecta en dry-run antes de la lista blanca?

**Sí, en cuatro casos.** Comprobado en el código:

- `sigrid/contrato-lineas`: `locate_contract` (l. 38) conecta; `ALLOWED_WRITE_DATABASES` solo en el paso 6
  con `commit` (l. 171).
- `sigrid/albaran` clásico (`create_purchase_albaran_use_case.py`): `locate_contract` en l. 191 y la lista
  en l. 506, solo después de `if not request.commit` (l. 481).
- `sigrid/albaran-directo` (`create_direct_albaran_use_case.py`): `_resolve_obra` en l. 76 y la lista en
  l. 299, después del retorno del dry-run (l. 277).
- **Además, el modo extendido de `sigrid/albaran`** (`create_albaran_compra_use_case.py`):
  `_comprobar_guardas` hace `return` si no hay `commit` (l. 292) antes de mirar la lista (l. 306), y
  `_leer` llama a `execute_read_query` con `SqlReadRequest.model_construct(database=request.database)`,
  así que tampoco pasa por `SqlQueryGuard`. El spec-author no lo mencionaba.
- `sigrid/partes-reclamacion` y `sigrid/concepto-grafico` validan la base **siempre**, antes de leer.

Con A1 los cuatro devuelven 400 `IdentifierValidationError` ante una base fuera del patrón: todas las
rutas de dominio capturan `ValueError` y devuelven `details.type = type(exc).__name__`. **Lo que A1 no
cierra:** una base que **sí** casa con el patrón y a la que llega `ro_user` se sigue leyendo en esas
previas, con su SQL fijo. Sería una feature aparte, no de F-011.

## Decisiones de diseño y desviaciones

- **Ninguna desviación de la spec.** Dos añadidos, los dos dentro de su alcance:
  - El texto de rechazo se compone tal como lo da el design (`', '.join(...) or '(ninguna)'`).
  - **Test extra `test_f011_r8_el_tipo_es_literal_tambien_para_una_subclase`**: fija el `details.type`
    literal que exige el design. Sin él, el mutante M14 (`type(exc).__name__`) sobrevivía (ver abajo).
- R14 se probó en **los 8** métodos que conectan (la tarea pedía 4) y con 8 bases inválidas (las 5 de la
  tarea más `ruesma rep`, `ruesma;` y `ruesma}`). R15 compara la cadena **literal** en los 8 métodos y
  las 3 bases, con una clave que lleva `}` para fijar también el escape de `PWD`.
- Efecto lateral de A1, documentado y probado (`test_f011_r13_se_usa_el_valor_que_devuelve_el_guardia`):
  `IdentifierGuard` recorta, así que una base con espacios alrededor (`" ruesma "`) conecta ahora a
  `DATABASE=ruesma;` en vez de `DATABASE= ruesma ;`. Ningún consumidor la manda así; los modelos de
  `sql/read` y `documents/read` ya la recortaban.
- T4 se puso en ROJO en una **copia aislada** (`git worktree` en el scratchpad, ya borrado), no en el árbol.

## Fase ROJO (trazas reales)

**T1** — `.venv/Scripts/python -m pytest tests/test_f011_caso_de_uso.py -q -p no:cacheprovider`, antes
de tocar el código:
```
E       TypeError: ReadDocumentUseCase.__init__() takes 2 positional arguments but 3 were given
tests\test_f011_caso_de_uso.py:70: TypeError
>       assert issubclass(modelos.BaseNoPermitidaError, ValueError)
E       AttributeError: module 'domain.models.document_models' has no attribute 'BaseNoPermitidaError'
28 failed, 1 warning in 1.39s
```
**T2, ROJO semántico** — mismo comando, con la clase y el constructor ya puestos pero **sin**
`_validar_base` (así el fallo no es solo de firma):
```
E       AssertionError: no debía llamarse a read_document
E       Failed: DID NOT RAISE BaseNoPermitidaError
E           infrastructure.security.identifier_guard.IdentifierValidationError: El identificador 'table' contiene caracteres no permitidos: gra;x
21 failed, 7 passed, 1 warning in 1.83s
```
(Los 7 que pasan son R8 y R10: la clase ya existía y la base permitida ya llegaba.) Después:
`python -m pytest tests/test_f011_caso_de_uso.py tests/test_f010_caso_de_uso.py -q` → `39 passed`.

**T3** — `python -m pytest tests/test_f011_ruta.py -q`, antes del `except BaseNoPermitidaError`:
```
E       assert [(30, 'ValueE...das: ruesma')] == [(30, 'BaseNo...das: ruesma')]
E         At index 0 diff: (30, "ValueError en documents/read: La base de datos 'ruesma_rep' no está permitida. Permitidas: ruesma") != (30, "BaseNoPermitidaError en documents/read: La base de datos 'ruesma_rep' no está permitida. Permitidas: ruesma")
FAILED tests/test_f011_ruta.py::test_f011_r9_el_rechazo_deja_un_warning - ass...
1 failed, 12 passed, 1 warning in 1.60s
```
**Hallazgo:** sin la rama propia, el `except ValueError` genérico ya devolvía 400 con
`details.type = type(exc).__name__` = `BaseNoPermitidaError`. La rama solo cambia el texto del log y fija
el literal. Por eso R9 y el test de la subclase son los que la sostienen. Después: `28 passed`, con
`tests/test_f010_ruta.py` incluido.

**T4** — en la copia aislada, con `ReadDocumentUseCase(repository, otro_settings)`:
```
>       assert document_use_case._settings is ajustes_propios
E       assert Settings(...) is Settings(...)
FAILED tests/test_f011_composicion.py::test_f011_r7_el_caso_de_uso_documental_recibe_el_settings_de_la_aplicacion
1 failed, 1 passed
```
y con `otro_settings` construido desde `allowed_write_databases`: `2 failed` (la base de escritura pasaba
la validación y llegaba al repositorio). En el árbol real: `2 passed`.

**T5** — `python -m pytest tests/test_f011_repositorio.py tests/test_f011_ruta.py -q`, antes de A1:
```
E       test_f011_repositorio.Capturada            <- la base inyectada llegó a pyodbc.connect
E         At index 0 diff: 'DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:servidor.falso,1433;DATABASE=  ruesma_rep  ;UID=lector;PWD={no-es}}una-clave};...' != ...
E       assert 500 == 400                          <- ruta con lista mal configurada
66 failed, 37 passed, 1 warning in 5.91s
```
(64 de R14, el de R13 y el de la ruta; los 24 de R15 pasan antes y después, como pide R15.) **T6**, tras
A1: `103 passed`.

## Verificación

- `python -m pytest -q` (T7): `2663 passed, 1 skipped` tras T6. Pasan `tests/test_f010_*.py` y
  `test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho` (`164 passed`).
- R12: `git diff dev -- tests/ ':!tests/test_f011_*'` solo trae las dos construcciones de
  `test_f010_caso_de_uso.py`.
- `bash harness/init.sh` (T15) al cerrar: **ENTORNO LISTO**, `2664 passed, 1 skipped, 1 warning in
  53.53s`, `PUERTA COBERTURA: 100.0% de 16 líneas cambiadas cubiertas (16/16, umbral 80%, nivel critico)`,
  PUERTA TAMAÑO en verde. ruff, 79 avisos, los mismos que al empezar (un ISC004 de mi test lo subió a 80; corregido en
  `0cba54a`). Las cuentas de ruff de los cuatro ficheros de producción son iguales a las de `dev`.

## Incidencia operativa (sin efecto)

Al comparar ruff contra `dev`, un `git checkout -q dev --` sin rutas me **cambió a la rama `dev`**. No
cambié nada en ella (árbol limpio, HEAD `e153b39` sin tocar) y volví en el acto a la rama de la
feature (HEAD `c054db9`, `git status` limpio). En `dev` no hay commits ni cambios míos.

## Fuera del alcance / pendiente

- **T12 (MANUAL, líder)**: antes de desplegar, leer en solo lectura `ALLOWED_DATABASES`,
  `ALLOWED_WRITE_DATABASES` y `SIGRID_DOCUMENT_WRITE_DATABASE`, y comprobar que **todos** casan con
  `^[A-Za-z_][A-Za-z0-9_]*$` (con A1, uno fuera del patrón tumbaría ese endpoint).
- **T13 (MANUAL, humano)**: `func azure functionapp publish func-sigridapi-dev-huyke --python`. Sin App
  Settings nuevas.
- **T14 (MANUAL, líder)**: pasos 1-4 de design §Verificación manual y el paso 5 (autorizado, dry-run de
  `contrato-lineas` con `database:"ruesma;APP=f011"`, que debe dar 400 `IdentifierValidationError`);
  después quitar las notas «PENDIENTE DE DESPLIEGUE» de `azure-apps/sigrid_api.md` (§4.1, §5.1 capas 3 y
  6, §7.2, §8.3 y §10).
- Hueco residual, para una feature propia: el dry-run de dominio lee cualquier base de la instancia que
  case con el patrón y a la que llegue `ro_user` (sección del dry-run, arriba).
- Arnés (para `arnes-base`, decide el humano): `harness/mutacion.py` no genera mutantes para `not in`,
  literales de texto ni argumentos con nombre. En F-011 sacó 2 mutantes de 43 líneas, y los ceros de una
  campaña así dicen poco.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite completa, `init.sh`) | **2664 passed, 1 skipped**, 0 failed |
| Tests de F-011 | 134 (28 caso de uso + 15 ruta + 2 composición + 89 repositorio), todos en verde |
| Cobertura de líneas cambiadas | **100,0 %** (16/16), umbral 80 %, nivel `critico` |
| Mutación, herramienta (`python -m harness.mutacion --feature F-011 --workers 1`, HEAD `cafc340`) | **2 generados, 2 muertos, 0 supervivientes**, 0 timeouts, 83,7 s, sin muestreo |
| Mutación, manual complementaria (mismo HEAD, aplicada y ejecutada uno a uno) | **14 mutantes, 14 muertos**; M14 sobrevivió hasta añadir el test del tipo literal y después muere (`1 failed, 14 passed`) |
| Supervivientes finales | **0** (16/16 muertos). Detalle en [`mutacion_F-011.md`](mutacion_F-011.md) |
| Tiempo de la suite | 53,53 s (`init.sh` final); 61,4 s la línea base de la campaña |

Durante las dos campañas no se usó Edit ni Write. Los mutantes manuales se aplicaron con un script por
Bash y se restauraron con `git checkout`. Entre `cafc340` y el HEAD final solo cambian tests, docs y
`progress/`: el código de producción medido es el mismo.
