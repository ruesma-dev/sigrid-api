<!-- progress/review_F-011_mutacion.md -->
Revisión completa (pasada 1) · bloque acotado: C4 bis, mutación y RM1–RM6 · HEAD `4d1c266`

# F-011 · Revisión de la campaña de mutación

**Veredicto del bloque: APPROVED** (sin cambios requeridos; hay dos observaciones que no bloquean y una propuesta de automejora).

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura y mutación con
**cero supervivientes** sin justificación aceptada por el humano. La fase RED y la cobertura no entran en este
bloque: van en `review_F-011_rojo.md` y en los demás informes troceados.

Entorno: git worktree aislado en el scratchpad sobre `4d1c266`, rama temporal `review-f011-mut`. Mutantes
aplicados por Bash (script de Python) y restaurados con `git checkout` tras cada uno; durante la campaña no se
usó Edit ni Write. `git status` limpio tras cada mutante y al final. Worktree y rama borrados.

## Checkpoints de C4 bis (parte de mutación)

- [x] **Informe generado por la herramienta.** `progress/mutacion_F-011.md` existe, con totales reales y sin
      cabecera «⚠ CAMPAÑA NO VÁLIDA». «Sin veredicto (base rota)» = 0 y la línea base consta (61,4 s).
- [x] **Totales verificados de forma independiente (recálculo puro).** `harness.alcance.alcance_de_feature`
      da origen `rama` `e153b39..feature/F-011…`, 4 ficheros y **43 líneas** (18 + 9 + 11 + 5), igual que el
      informe. `generar_mutantes` da **2**: `read_document_use_case.py:53 [logico] or→and` y
      `function_app.py:489 [entero] 400→401`.
      Prueba de control del cero por fichero: con los ficheros enteros salen 5 / 1 / 52 / 52 mutantes. El
      generador funciona; los ceros de `document_models.py` y `sql_server_repository.py` dentro del alcance
      salen de los operadores (no tiene operador para `not in`, para literales de texto ni para argumentos con
      nombre), no de un fallo.
- [x] **Muertos comprobados, no solo contados.** El «Tiempo total» es de 83,7 s, más de 60 s, así que la regla
      no obligaba a reejecutar. Aun así, por encargo, **reejecuté la campaña entera en serie** sobre HEAD
      (`python -m harness.mutacion --feature F-011 --workers 1 --salida <scratchpad>`): **2 generados, 2
      evaluados, 2 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 105,0 s**, línea base 70,1 s,
      media 52,5 s, SHA medido `4d1c266a6bce40566e1aa9cb7dca79424229e399`. Coincide con el informe del
      implementer. Mi informe quedó fuera de `progress/`, en
      `C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-sigrid-api\2b5145bb-bc95-4386-b786-7860ca1437e3\scratchpad\mut_reviewer_F-011.md`.
- [x] **Coste por mutante.** 83,7 × 1 ÷ 2 = 41,9 s por mutante. Muy por encima de 1 s.
- [x] **RM1 · SHA.** El informe midió `cafc340…`, no HEAD. Pero `git diff cafc340..4d1c266` no toca ningún
      fichero del alcance: solo `tests/test_f011_ruta.py`, `docs/ARCHITECTURE.md`, `tasks.md` y `progress/`.
      El código de producción medido es el mismo, y mi campaña sobre HEAD lo confirma.
- [x] **RM2 · Coherencia del tiempo.** 2 × 41,8 = 83,6 ≈ 83,7 s. Media ÷ base = 0,68 con 1 worker: es
      coherente con `-x` y 2 de 2 muertos. No hay salto de orden de magnitud.
- [x] **RM5 · Equivalentes (solo en `critico`).** No hay ninguno declarado equivalente. M14 era equivalente
      con el código de entonces. En vez de declararlo así, el implementer añadió un test con una subclase que
      lo vuelve observable. Lo reproduje y muere (ver la tabla).
- [x] **RM6 · Guardas quitadas.** N/A justificado: ningún mutante se mató quitando código defensivo. La
      feature añade guardas (`_validar_base` y el `IdentifierGuard` de `_connect`) y no quita ninguna.

## RM3 y RM4 (criterio)

- **RM3.** La línea base del subconjunto está en verde sobre el worktree limpio (**160 passed**, 1 aviso de
  pydantic por el campo `schema`, que ya existía). Ningún mutante muerto es equivalente en comportamiento
  observable. X7 (lista leída una sola vez) y X14 (otro `Settings` en la composición) solo los caza un test
  concreto de diseño: R10 «se lee en cada llamada» y la identidad de R7. Esos tests vigilan requisitos
  escritos; ninguno de los dos muere por una suite que ya estuviera en rojo.
- **RM4.** Apliqué así toda la campaña manual. Los tests fueron `tests/test_f011_{caso_de_uso,ruta,composicion,repositorio}.py`
  y `tests/test_f010_{caso_de_uso,ruta}.py` (160 tests), con `PYTHONDONTWRITEBYTECODE=1` y
  `-p no:cacheprovider`, sin `-x`, para contar los fallos.

## Campaña manual del reviewer (una fila por mutante, texto exacto y nº de fallos)

`UC` = `application/use_cases/read_document_use_case.py`, `FA` = `function_app.py`,
`RP` = `infrastructure/repositories/sql_server_repository.py`, `MO` = `domain/models/document_models.py`.

| # | Fich. | Original → mutado | Fallos /160 | Primer test que lo caza |
|---|---|---|---|---|
| M1 | UC | `if database not in permitidas:` → `if database in permitidas:` | 52 | `r1_..._texto_exacto` |
| M2 | UC | quitar `self._validar_base(request.database)` | 29 | `r1_..._texto_exacto` |
| M3 | UC | `{', '.join(permitidas)` → `{','.join(permitidas)` | 13 | `r1_..._texto_exacto` |
| M6 | MO | `BaseNoPermitidaError(ValueError)` → `(Exception)` | 1 | `r8_..._hereda_de_value_error` |
| M9 | FA | `details={"type": "BaseNoPermitidaError"}` → `{"type": "ValueError"}` | 6 | `r1_..._400_con_cuerpo_exacto` |
| M11 | RP | `safe_database = IdentifierGuard.validate_identifier(...)` → `safe_database = database` | 66 | `r14_lista_mal_configurada_...` |
| M12 | RP | `field_name="database")` → `field_name="db")` | 65 | `r14_lista_mal_configurada_...` |
| M13 | RP | `f"DATABASE={safe_database};"` → `f"DATABASE={database};"` | 1 | `r13_se_usa_el_valor_que_devuelve_el_guardia` |
| M14 | FA | `{"type": "BaseNoPermitidaError"}` → `{"type": type(exc).__name__}` | 1 | `r8_..._literal_tambien_para_una_subclase` |
| X1 | UC | `_validar_base` movido **después** de `read_document` (orden validar→conectar) | 29 | `r1_..._texto_exacto` |
| X2 | FA | borrar el bloque `except BaseNoPermitidaError` entero (cae en `except ValueError`) | 2 | `r9_..._warning`, `r8_..._subclase` |
| X4 | UC | `not in permitidas` → `database.lower() not in [p.lower() for p in permitidas]` | 3 | `r3_..._mayusculas[RUESMA_REP]` |
| X5 | UC | → `if not any(database.startswith(p) for p in permitidas):` (prefijo) | 18 | `r1_..._texto_exacto` |
| X6 | UC | → `if not any(p in database for p in permitidas):` (subcadena) | 20 | `r1_..._texto_exacto` |
| X7 | UC | lista leída una vez en `__init__` (`self._permitidas`) | 1 | `r10_la_lista_se_lee_en_cada_llamada` |
| X8 | UC | `allowed_databases` → `allowed_write_databases` | 52 | `r1_..._texto_exacto` |
| X9 | FA | `status_code=400` → `422` en el bloque `BaseNoPermitidaError` | 6 | `r1_..._400_con_cuerpo_exacto` |
| X10 | FA | `logger.warning("BaseNoPermitidaError…")` → `logger.info(…)` | 1 | `r9_el_rechazo_deja_un_warning` |
| X11 | UC | `or '(ninguna)'` → `or ''` | 2 | `r4_lista_vacia_...` (caso de uso y ruta) |
| X12 | UC | `raise BaseNoPermitidaError(` → `raise ValueError(` | 28 | `r1_..._texto_exacto` |
| X13 | RP | guardia solo si `autocommit` (`... if autocommit else database`) | 16 | `r14_..._no_conecta[...-execute_write_command]` |
| X14 | FA | `ReadDocumentUseCase(repository, Settings.model_construct(allowed_databases=settings.allowed_write_databases))` | 2 | ambos `r7_*` de composición |
| X15 | UC | `if database not in permitidas and permitidas:` (lista vacía abierta) | 2 | `r4_lista_vacia_...` |

**Resultado: 23 mutantes manuales (9 reproducidos del implementer + 14 nuevos), 23 muertos, 0 supervivientes.**
Todos los puntos que pedía el encargo quedan cubiertos:

- la comparación exacta: M1, X4, X5, X6, X8 y X15;
- el orden «validar antes de conectar»: M2 y X1, más R6 en la suite;
- la llamada a `IdentifierGuard` en `_connect` en toda la API: M11, M12 y X13;
- el uso de su valor devuelto: M13;
- el `details.type` literal: M9 y M14, más X2.

Lo que destapa X2: si faltara el `except` propio, el `except ValueError` ya devuelve `type(exc).__name__` =
`"BaseNoPermitidaError"` con el mismo 400. Solo lo cazan el texto del warning (R9) y el test de la subclase.
Los dos tests son necesarios, y ninguno sobra.

## Observaciones (no bloquean)

1. La tabla manual de `progress/mutacion_F-011.md` no trae el **número de fallos** por fila, y M4, M8 y M10 no
   dan el texto exacto (por ejemplo «otro `Settings`»). El protocolo solo lo exige cuando la manual
   **sustituye** a la automática. Aquí la complementa, así que no bloquea. La tabla de arriba deja la
   evidencia reproducible.
2. Lo que dice el implementer en Evidencias, «M14 … `1 failed, 14 passed`», cuadra con haber ejecutado solo
   `tests/test_f011_ruta.py` (15 tests), no el subconjunto que declara. Es inocuo: con los 160 tests también
   muere con 1 fallo.

## Propuesta de automejora (no aplicada; para el humano)

El generador de `harness/mutacion.py` produjo 2 mutantes en 43 líneas de una feature `critico`. Toda la
evidencia útil de esta feature es manual. Propuesta para `arnes-base`, porque vale para cualquier proyecto:
añadir los operadores `in ↔ not in` y `is ↔ is not` (comparación), y «borrar argumento con nombre» o
«literal de texto → vacío». Habría generado M1, M12, M9 y X11 de forma automática y reproducible.

Archivos: informe propio de la campaña en
`C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-sigrid-api\2b5145bb-bc95-4386-b786-7860ca1437e3\scratchpad\mut_reviewer_F-011.md`,
el script de los mutantes en `...\scratchpad\scripts\manuales.py` y su salida en `...\scratchpad\manuales.log`.
