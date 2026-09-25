<!-- progress/review_F-006_rigor.md -->
Revisión completa (pasada 1), acotada a C4 bis. Código medido: `22ba2a5` (producción idéntica a `22e23f7`).

# F-006 · Revisión de rigor (C4 bis: fase RED, cobertura, mutación, RM)

Revisión acotada por encargo del líder. **No se han ejecutado** `init.sh`, la suite completa
ni ninguna campaña de mutación, porque hay otros revisores trabajando en paralelo. Todo lo que se ha
ejecutado corrió en worktrees desechables del scratchpad (`wt_red`, `wt_r1` = `3852580`,
`wt_head` = `22ba2a5`) con `-p no:cacheprovider`. Ya se han quitado (`git worktree list` muestra solo
el árbol principal). Mientras revisaba, HEAD pasó a `70237c6`. Ese commit solo toca
`progress/current.md` (`git diff --stat 22ba2a5..HEAD`), así que el alcance sigue siendo el mismo.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 %,
una campaña **completa** de mutación con 0 supervivientes y RM5.

## Checkpoints C4 bis

- [x] **Rigor declarado.** `critico` es un valor válido de `harness/rigor.json`.
- [x] **Fase RED.** Las trazas del impl §5 son plausibles y las he reproducido yo:
  - Orden de commits en `git log --oneline dev..HEAD`: cada commit de test va antes que el de su código. Son `c0fc82b`→`8bda5d1`, `81bc619`→`1af37d9`, `e3f4006`→`b660e22` y `ee22b9f`→`13664ef`. Además, `git show --stat` confirma que los commits de test no incluyen código de producción. `13664ef` toca 2 líneas del test por un tema de lint (`repo`→`_` y un comprehension), sin cambiar su semántica.
  - Reproducción 1, R11/R13 en `ee22b9f`: `python -m pytest -p no:cacheprovider tests/test_f006_use_case.py -q -k "r11 or r13"` da `E ModuleNotFoundError: No module named 'application.use_cases.create_partes_reclamacion_use_case'` y `1 error`.
  - Reproducción 2, R11-R15 contra un esqueleto vacío (`run` → `NotImplementedError`) que escribí en el worktree: `-k "r11 or r12 or r13 or r14 or r15"` da **`22 failed, 58 deselected`**. Coincide al pie de la letra con el informe. Fallan, entre otros, `r11_work_ejecuta_e1_a_e14_en_orden`, `r13_una_colision_repite...`, `r14_una_relectura_que_no_cuadra_revierte[con|rcp|rcpint|conext|log]` y `r15_commit_idempotente...`.
  - Reproducción 3, T3 en `c0fc82b`: `tests/test_f006_settings.py` da **`12 failed, 1 passed`**, con los mismos 9 + 2 `AttributeError` y el `AssertionError` del sample. Es idéntico al informe.
  - Reproducción 4, T7 en `e3f4006`: `ModuleNotFoundError ... parte_reclamacion_statements` y `1 error`. Idéntico.
- [x] **Cobertura.** El informe cita la línea de `init.sh`: `PUERTA COBERTURA: 100.0% de 560 líneas cambiadas cubiertas (560/560, umbral 80%, nivel critico)`. La contrasté por mi cuenta: en `wt_head` ejecuté solo `coverage run --data-file=<scratch> -m pytest -k f006 tests` (229 pasan) y después `harness.cobertura.cobertura_lineas_cambiadas` sobre el alcance. Resultado: **`(560, 560)`**. La cifra se reproduce solo con los tests de F-006.
- [x] **Mutación con totales verificados de forma independiente (cálculo puro).** Con `harness.alcance.alcance_de_feature("F-006")` y `generar_mutantes` en HEAD salen 5 ficheros y 1.550 líneas: 808/463/16/206/57, igual que el informe fichero por fichero. Salen **217 mutantes**: 135 en el caso de uso, 39 en statements, 3 en settings, 34 en modelos y 6 en `function_app`. En `3852580` salen **228**, lo que cuadra con la ronda 1. La diferencia de 11 son las líneas muertas quitadas.
- [x] **Muertos comprobados.** El «Tiempo total» es 1.355,1 s (**22,6 min**, más de 60 s), así que **la campaña no se reejecutó**. Por la regla, y por instrucción del líder, basta el recálculo puro. Lo he completado con RM4: reproduje mutantes sobre copias, detallado más abajo.
- [x] **Coste por mutante.** 1.355,1 × 8 ÷ 217 = **49,96 s**, muy por encima de 1 s. Ronda 1: 2.548,9 × 8 ÷ 228 = 89 s, más alto, como corresponde a 42 mutantes que recorrieron la suite entera.
- [x] **Cabecera válida.** No lleva «⚠ CAMPAÑA NO VÁLIDA». «Sin veredicto (base rota)» = 0, timeouts = 0, muestreo = «no: campaña completa», Workers = 8, y hay 8 filas de línea base (329,8–353,0 s). El alcance está en la tabla.
- [x] **RM1.** El SHA medido es `22e23f7e9a05e0baddcb509b1851b28b4d48b80b`. `git diff --stat 22e23f7..22ba2a5` solo toca `progress/*` y `tasks.md`, y `70237c6` solo `current.md`. No cambia ni un fichero del alcance, y el recálculo en HEAD da el mismo alcance y el mismo número de mutantes.
- [x] **RM2.** `media × W` = 6,2 × 8 = 49,6 s frente a una línea base de ~340 s, un cociente de 0,146. No hay salto de orden de magnitud. Es coherente con `-x`: los `test_f006_*` van en el puesto 11-15 de 35 ficheros por orden alfabético, antes que todos los `test_mutacion_*`, que son los pesados. Así que un mutante muere en torno a una sexta parte de la suite.
- [N/A] **RM5.** El nivel es `critico`, pero se declaran **cero equivalentes** (0 supervivientes, sin justificaciones pendientes). No hay muestra que reproducir.
- [x] **RM6.** El código defensivo quitado en `22e23f7` (`git diff 3852580 22e23f7 -- application ...`) tiene su invariante en quien construye el dato, y lo he verificado:
  - `series[0][:4]`, `obras[0][:3]`, `fila[:4]` y `fila[:3]` → las SELECT de `parte_reclamacion_statements.py:150,153,156,160,164-166` traen exactamente 4/3/4/4/3 columnas, y `test_f006_statements` fija el SQL carácter a carácter. Si alguien añade una columna, el desempaquetado falla de forma ruidosa, no silenciosa.
  - `cliide or 0` y `recide or 0` → L5 (`statements.py:156`) hace `ISNULL(u.cliide, 0), ISNULL(u.peride, 0)`, y el test lo fija en `test_f006_statements.py:80`.
  - `_Lote` sin `frozen` → se construye una sola vez (`use_case.py:366`), y `grep` no encuentra ninguna asignación ni mutación de `lote.*`.
  - `ide_rcpint` 0 → `None` sin intervinientes → no hay filas `rcpint` que numerar, y lo cubre `r11_sin_intervinientes_no_se_toca_rcpint...`.
  - Las guardas `pos or 0` y `fecbaj or 0`, que sí defienden datos NULL reales, **se mantienen** y ahora tienen tests (pos NULL).
- [N/A] **Campaña MANUAL.** No aplica: la campaña automática dio 217 mutantes, no cero, y no se sustituyó por una manual. El repaso en serie de la ronda 1 no es la campaña que vale, pero reproduje igualmente dos de sus filas (ver abajo).
- [x] **Supervivientes analizados.** La campaña válida tiene 0 supervivientes, así que no hay ninguna sección en `PENDIENTE`. Se cumple el cero exigido por `critico`.
- [x] **Evidencias.** Impl §9 trae los cuatro números más los workers (8). Los valores corresponden al código final: la mutación en `22e23f7` tiene la misma producción que HEAD. De F-006 hay 229 tests; con `--collect-only` en HEAD cuento 85 + 76 + 45 + 13 + 10 = 229, **coincide**. La cobertura 560/560 la reproduje en HEAD. Los 1.731 tests de la suite y los 151,79 s **no se reverifican**, porque para eso habría que ejecutar la suite completa, que el encargo prohíbe. Quedan en manos del revisor que ejecute `init.sh`.
- [x] Ningún N/A de este bloque va sin motivo escrito.

## Reproducción de mutantes de la ronda 1 (RM4, sobre copias)

Script del scratchpad: localiza el mutante con `generar_mutantes`, lo aplica con `aplicar_mutante`,
ejecuta `pytest -p no:cacheprovider -q -x -k f006 tests` y restaura con `git checkout`. Tras cada
ejecución, `git status` del worktree quedó limpio.

| Mutante (texto exacto) | En `3852580` (ronda 1) | En `22ba2a5` (HEAD) |
|---|---|---|
| `use_case.py:251 committed=resumen.creados > 0` → `> 1` | 222 passed (sobrevive) | **1 failed**: `test_f006_r11_work_ejecuta_e1_a_e14_en_orden` |
| `models.py:169 creados: int = 0` → `= 1` | 222 passed (sobrevive) | **1 failed**: `test_f006_r2_el_resumen_arranca_a_cero` |
| `models.py:139 obra: ... min_length=1` → `min_length=2` | 222 passed (sobrevive) | **1 failed**: `test_f006_r1_un_solo_caracter_basta_en_los_textos_obligatorios` |

**Falsos supervivientes, reevaluados en serie.** Reproduje dos de los seis en `3852580`:
- `use_case.py:609 cursor.fetchone()[0]` → `[1]` da **1 failed** (`r11_commit_una_transaccion_por_parte...`).
- `use_case.py:620 revalidar_unidad_postventa(...), 1` → `2` da **1 failed** (mismo test).

Los dos mueren en serie, como dice el informe. Encaja con el defecto conocido del modo paralelo (el `exit 5` que se cuenta como verde), cuyo sesgo es pesimista.

**RM3 (criterio).** Repasé los 217 mutantes de HEAD y no vi ningún equivalente evidente que figure como muerto. Los dudosos son distinguibles:
- `agotado = True`→`False` en l. 219 procesaría partes que deberían ser `no_procesado`.
- `POS_PASO * k`→`// k` rompe con k=0 y con k≥2.
- `>=`/`>` en el presupuesto y en `10**tam` los fijan tests con reloj y numeración en el límite.
- `@dataclass(frozen=True)`→`False` en `Sellos` es observable y lo fija un test de inmutabilidad.

## Observaciones (no bloquean)

1. **La numeración de la ronda 1 no se puede reproducir.** Los «n.º 74, 76, 80, 118, 120, 121» y las
   listas de números de los 36 reales en `mutacion_F-006.md` no coinciden con el orden de
   `generar_mutantes` en `3852580`. Por ejemplo, `fetchone()[0]→[1]` es el n.º 118 del generador y el
   informe lo llama 121, y `> 1 → >= 1` es el 90 y el informe lo llama 74. Parece el orden de eco
   `[i/n]` de la campaña paralela, que no es contractual. Los 6 falsos se identifican por su texto;
   los 36 reales, solo por categorías.
   Además, impl §6 dice «ficha por ficha», pero lo que hay es un resumen agrupado. No bloquea, porque la campaña que vale tiene
   0 supervivientes y lo verifiqué con 3 reales y 2 falsos.
2. **T11: test y código van en el mismo commit** (`2af370e`). La traza RED de §5 es plausible (el
   `AttributeError` sobre `function_app.CreatePartesReclamacionUseCase`), pero el orden de commits no la
   demuestra. Los requisitos centrales R11-R15 sí tienen el test en un commit anterior.

## Propuesta de automejora (para el humano, no aplicada)

- Añadir a `CHECKPOINTS.md` §C4 bis y a `reviewer.md`: cuando se repasan en serie los supervivientes
  de una ronda previa, **cada fila se identifica por `fichero:línea [operador] original → mutado`**,
  como en `Mutante.descripcion()`, y **nunca por su número**. La numeración de la campaña paralela
  depende del orden de terminación y no la puede reproducir nadie.

VEREDICTO PARCIAL: APROBADO
