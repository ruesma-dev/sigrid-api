<!-- progress/review_F-016_C4red.md -->
# Revisión F-016 · C4 y C4 bis (fase RED y cobertura)

Revisión completa (pasada 1) desde `745a43c` (`dev` = merge-base) hasta HEAD `c08461f`. Reviewer, 2026-10-28.
Fuera de este trozo: la mutación de C4 bis (otro reviewer), `bash harness/init.sh` y la suite completa (otro reviewer
en paralelo), C1-C3, C4 ter y C5. `1733c2f` (alta de F-018) y `.claude/worktrees/` son ajenos a F-016. No se ha
tocado código, tests ni specs; sin red ni BBDD; el único commit es este fichero.

## Veredicto: **APROBADO** (para este bloque)

**Nivel de rigor:** `critico`, declarado en `harness/features.json` (no heredado). Exige fase RED con salida real,
cobertura de líneas cambiadas ≥ 80 % y mutación sin supervivientes no aceptados (esta última, fuera de este trozo).

## Fase RED: reproducida, no solo leída

Cada commit RED toca **solo** `tests/`, `progress/` y `tasks.md`; cada GREEN, solo producción (salvo lo de la
observación O5). Exporté cada commit con `git archive` a mi scratchpad (sin worktree, sin tocar el árbol) y ejecuté su
fichero de tests con el `.venv`:

| Lote | Commit RED | Resultado reproducido | Informe dice | Commit GREEN | Reproducido |
|---|---|---|---|---|---|
| T2/T3 | `9b4c70a` | 1 error de colección: `ModuleNotFoundError ... proforma_origen_models` | igual | `60a5052` | 38 passed |
| T4/T5 | `e6688c3` | 10 failed, 1 passed | 10 failed, 1 passed | `284f0bd` | 11 passed |
| T6/T7 | `fd73ee5` | 1 error: `ModuleNotFoundError ... proforma_origen_statements` | igual | `87c97bd` | 45 passed |
| T8/T9 | `d1252a2` | 20 failed, 9 passed | 20 failed, 9 passed | `3a1c2c5` | 29 passed |
| T10/T11 | `31496ca` | 5 failed, 7 passed | 5 failed, 7 passed | `3591400` | 12 passed |
| T12/T13 | `1ef36da` | 1 failed, 15 passed | 1 failed, 15 passed | `93bbce3` | 16 passed |

Los conteos coinciden al número. Las que pasan en RED están explicadas en el informe (R1 de mes y errores de F-007 en
T8; la parte de fuera hecha en T9 para T10; R3 y códigos ya cubiertos por T2/T5 en T12), y es coherente con el orden de
tareas. **Ningún test se debilitó después de su RED**: `git diff <red> HEAD` de cada fichero muestra solo añadidos
(`test_f016_t14_*` de la campaña) y la reordenación de imports de `06ffcb6`; `test_f016_models.py` y
`test_f016_settings.py` no han cambiado desde su RED.

## Cobertura: reproducida de forma independiente

`coverage run` **solo con los 6 ficheros `test_f016_*.py`** (datos en el scratchpad, sin pisar `.coverage` ni
`coverage.json` del árbol) y `python -m harness.cobertura --base dev --cov <scratchpad>/cov16.json`:
`PUERTA COBERTURA: 100.0% de 270 líneas cambiadas cubiertas (270/270, umbral 80%, nivel critico)`. Coincide con
«Evidencias» y demuestra que las 270 líneas las cubren los tests propios de F-016, no la suite heredada.
Suite acotada en HEAD: **156 passed** (116 funciones con sus parametrizaciones), 7,2 s.

## Checkpoints de este trozo

**C4**
- [x] Cada requisito con ≥ 1 test trazable que pasa: R1, R3-R22 con `test_f016_rN_*` (tabla abajo). **R2** sin
  `test_f016_r2_*`: cubierto por la red de T1 (tests de F-007/F-009/F-015 y dorados sin modificar, nombrados en
  `impl_F-016.md` §T1, como prevé `tasks.md` T1 aprobado por el humano) y por el `git diff dev` vacío del núcleo.
  Justificación: R2 es de no-modificación; un test unitario solo podría fijarlo con un hash del fichero (frágil y sin
  valor). Ver O1 y la propuesta de automejora.
- [x] Sin red ni BBDD: `grep` de `requests|httpx|socket|urllib|pyodbc|aiohttp|.connect(|SqlServerRepository|getenv|
  os.environ|SIGRID_API_BASE_URL|FUNCTION_KEY` en `tests/test_f016_*.py` y `tests/f016_dobles.py`: sin resultados.
  La ruta dobla `build_dependencies` (`test_f016_route.py:47`); los settings usan `_env_file=None` y limpian el entorno.
- [x] MANUAL listadas: `progress/current.md:29-31` enumera T17-T18 y la prueba en lectura de §2.3, y remite a
  `specs/F-016-proforma-a-origen/verificacion_manual.md` con los comandos exactos (V0 `Invoke-RestMethod`, D, V, G).
  Mismo patrón aceptado en F-015.

**C4 bis (parte RED y cobertura)**
- [x] `rigor` declarado: `critico`.
- [x] Fase RED con salida real en `impl_F-016.md` §«Fase RED» para los seis lotes, y reproducida (tabla de arriba).
- [x] Cobertura: 100 % de 270 líneas, en `[OK]` según el informe y reproducida por mí sin `init.sh`.
- N/A (fuera de este trozo, lo revisa otro reviewer): mutación, «muertos comprobados», coste por mutante, cabecera
  «CAMPAÑA NO VÁLIDA», RM1, RM2, RM5, RM6, campaña manual, supervivientes y el nº de workers de «Evidencias».
- [x] «Evidencias» trae tests (3549 passed, 1 skipped), cobertura (100 %), mutantes (116/14 → 0 no aceptados) y
  tiempo de la suite (199,23 s). El nº de workers no figura: lo juzga el reviewer de mutación (ver O6).
- [x] Ningún N/A de este informe sin motivo.

## R1 / R2: comprobación literal

- `git diff dev --stat -- tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py
  tests/fixtures/f009_caracterizacion.json tests/fixtures/f007_obra0719.json tests/f007_dobles.py tests/f009_dobles.py`:
  **vacío**.
- `git diff dev --stat -- application/use_cases/create_albaran_compra_use_case.py
  application/use_cases/albaran_compra_statements.py domain/models/albaran_compra_models.py
  application/use_cases/proforma_statements.py infrastructure/`: **vacío**.
- Código tocado (`git diff dev --stat`, sin docs): exactamente los ficheros de design §Ficheros a crear/modificar
  (más `BACKLOG.md` y `features.json`, del arnés).

## SQL LP7-LP9 carácter a carácter

`tests/test_f016_statements.py:83-102` compara `LP7_PROFORMA_ANTERIOR`, `LP8_SUCESORAS` y `LP9_LINEAS_ANTERIOR` con `==`
contra el literal completo y sus parámetros (`[14, ctride, cod]`, `[14, ctride, ide]`, `[ide]`); los literales coinciden
con design §SQL. `:105-115` control negativo (solo `SELECT`, sin `DELETE|MERGE|UPDATE|INSERT|DDL|EXEC`, con `?`, sin `;`
ni comillas); `:118-140` guardia de bases por cada sentencia y rechazo de otra base. R17: `test_f016_transaccion.py:83`
fija LP8 por el cursor tras LP1.

## Cobertura de requisitos (R → test)

| R | Tests que lo fijan (fichero: nº) | Lo que de verdad comprueban |
|---|---|---|
| R1 | models `r1_*` (3), use_case `r1_*` (2), `r21_en_mes_la_traza_no_cambia` + red T1 | sin LP7-LP9, sin claves nuevas en `model_dump` |
| R2 | red T1 (F-007/F-009/F-015 sin tocar) + `git diff dev` vacío | O1 |
| R3 | models `r3_*` (10), route `r3_peticion_invalida_400_de_f012_sin_codigo` | cada combinación inválida, límites 1-24 |
| R4 | settings `r4_*` (6), route `r4_*` (4) | defecto `false`, booleano estricto, orden tras la llave F-007 |
| R5 | statements `r5_*` (7), use_case `r5_*` (3) y `r23_idempotente_a_origen_sin_cadena`, transacción `r17_la_misma_referencia_*` | tolerancia, `existente` antes de LP7 |
| R6 | statements `r6_*` (4), use_case `r6_*` (2) | mismo día vale, siguiente no; nulos; lecturas exactas |
| R7 | statements `r7_*` (2), use_case `r7_anterior_con_sucesora`, transacción `r17_sucesora_aparecida_dentro_no_escribe` | `cod` de la sucesora, parámetros de LP8 |
| R8 | use_case `r8_r13_previa_de_una_primera`, transacción `r17_en_primera_sin_lp8` | ninguna de LP7-LP9 leída, `docoriide` 0 |
| R9 | statements `r9_*` (6), use_case `r9_*` (2), route `r9_linea_anterior_no_valida_400_con_sus_lineas` | fallos juntos y en orden |
| R10 | statements `r10_*` (2), use_case `r10_nueva_con_su_ctrpro_*` | aviso con los `dcapro.ide` |
| R11 | statements `r11_*` (3) y `t14_continuada_imporiori_*`, use_case `r11_r12_*` | `canoriori` acumulado, coma flotante |
| R12 | statements `r12_*` (3), use_case `r11_r12_*`, `r19_arrastradas_en_la_respuesta` | orden detrás, columnas de R12 |
| R13 | statements `r13_cabecera_a_origen`, use_case `r8_r13_*` | `docoritip` 1, `docoriide` |
| R14 | use_case `r14_tope_con_las_arrastradas_aun_en_previa` | frontera 7 falla / 8 pasa |
| R15 | use_case `r15_*` (3) | avisos iguales a mes, cuadre |
| R16 | use_case `r15_r16_avisos_de_f007_iguales_y_sin_contrato_a_origen` | comprobé que la de mes SÍ emite `contrato_a_origen` (no es filtro vacío) |
| R17 | transacción `r17_*` (7) | LP8 dentro, sucesora/del mes aparecidas dentro |
| R18 | transacción `r18_*` (5) | orden y applocks, relectura E12, sin `UPDATE`/`ctrprodes`/`mov`, reintento |
| R19 | models `r19_*` (3), statements `r19_*` (3), use_case `r19_*` (2), route `r19_de_punta_a_punta_*` | `cadena` e importes |
| R20 | models `r20_*` (6), route `r20_errores_de_la_cadena_400_con_codigo` | conjuntos de F-007 idénticos (`is`/`==`) |
| R21 | use_case `r21_*` (4) | campos de traza y ausencia de datos sensibles |
| R22 | statements `r22_*` (6) | ver sección SQL |

## Observaciones (no bloquean)

- **O1.** R23 pide `test_f016_rN_*` para R1-R22 y R2 no lo tiene. Aceptado con la justificación de C4; si el humano
  prefiere la letra, la salida es reformular R23 («R2 por la red de T1»), no un test de hash.
- **O2.** `tests/test_f016_use_case.py:309` `test_f016_r23_idempotente_a_origen_sin_cadena` alude a F-007 R23 pero choca
  con la R23 de F-016; fija R5. Cosmético.
- **O3.** `test_f016_r5_a_origen_del_mes_con_otro_total_avisa_y_sigue` existe en `test_f016_statements.py:398` y
  `test_f016_use_case.py:293`: módulos distintos, se ejecutan los dos. Cosmético.
- **O4.** El RED de T2 y T6 es un error de colección (módulo inexistente): válido para módulos nuevos, pero no enseña
  qué aserción falla. Que esos tests muerden lo respalda la campaña de mutación (fuera de este trozo).
- **O5.** El GREEN `87c97bd` toca `tests/f016_dobles.py:88` (`fila_lp7(cod, ...)` → `fila_lp7(documento, ...)`): el RED
  llamaba `fila_lp7(PARALELA, cod=PUNTA)` (`test_f016_statements.py:163`), que habría chocado con el parámetro. Arregla
  el doble, no relaja ninguna aserción.
- **O6 (para otros trozos).** `tasks.md` T15 está `[x]` con su verificación («consultas probadas en lectura sobre una
  cadena real») aún pendiente y manual (C2/C5). «Evidencias» no declara workers (reviewer de mutación).

## Automejora propuesta (no aplicada)

`CHECKPOINTS.md` C4, primer punto: añadir «Un requisito de no-modificación (no tocar X) se da por cubierto con los
tests previos de X sin modificar y el `git diff` vacío, citados en el informe; no exige `test_fXXX_rN_*`». Vale para
cualquier proyecto: portar a `arnes-base` si el humano lo aprueba.
