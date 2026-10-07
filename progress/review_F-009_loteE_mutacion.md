<!-- progress/review_F-009_loteE_mutacion.md -->
Revisión completa (pasada 1) del lote E, parte de mutación (T16), diff `ebb0ddc..3d681e63dad9d5f9bc1524e7ceaaf41a5382e878`

# F-009 · Revisión del lote E (T16, campaña de mutación) · **Veredicto: APPROVED**

Alcance: `92bf606` (aislamiento del test de la tupla de ocho), `db945d6` (31 tests nuevos), `8a85804` (14 sitios de
producción quitados), `3d681e6` (informes). Lo aprobado en los lotes A-D queda dado por bueno. T17-T18 los revisa otro
reviewer (`review_F-009_loteE_docs.md`, ya commiteado en `632b9a8`, que solo toca `progress/`): aquí no se miran.

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de lo cambiado, mutación con cero
supervivientes salvo equivalentes con justificación aceptada por el humano, y RM5 (reproducir uno de los equivalentes).

## Verificación ejecutada (salida real)

- `bash harness/init.sh` tal cual: `2370 passed, 1 skipped`; `PUERTA COBERTURA: 100.0% de 1103 líneas cambiadas`
  (nivel critico); `PUERTA TAMAÑO` en verde; rama correcta; `ENTORNO LISTO`. `ruff check` de los dos tests y los dos
  ficheros de producción tocados: `All checks passed!`.
- **Recálculo puro (C4 bis)**: `alcance_de_feature("F-009")` + `generar_mutantes` sobre HEAD (producción idéntica a
  `8a85804`: `git diff --stat 8a85804 3d681e6` solo toca `progress/` y `tasks.md`). Origen `rama 2a5ac24..`, y por
  fichero 1040/119, 1338/279, 92/11, 365/64, 94/8 (líneas/mutantes) para statements, caso de uso, `config/settings.py`,
  modelos y `function_app.py`: **2929 líneas y 481 mutantes**, igual que el informe. Los dos supervivientes existen
  tal cual (`comparacion`, l. 1328 col 30 y l. 1333 col 30, mismo texto original→mutado).
- **Alcance completo**: `git diff --stat 2a5ac24 HEAD` fuera de tests/docs/progress da esos 5 `.py` y 3 ficheros no
  Python. **Campaña no reejecutada**: 2.077,9 s (~35 min) > 60 s; vale el recálculo, las RM y las muestras de abajo.

### Muestra de muertos con su test (punto 3): 8 de 8 caen, y caen por el test que dice el informe

Worktree desechable de HEAD en el scratchpad; cada mutante localizado con `generar_mutantes`, aplicado con
`aplicar_mutante`, `pytest -q --tb=no tests/test_f009_mutacion.py -rf`, y restaurado (`git status` vacío al final):

| Sitio (HEAD) | Original → mutado | Resultado | Test que cae |
|---|---|---|---|
| `albaran_compra_statements.py:284` | `abs(almcan) < EPSILON_STOCK` → `<=` | 1 failed, 30 passed | `r19_el_epsilon_del_stock_es_estricto` |
| `create_albaran_compra_use_case.py:248` | `ensure_ascii=False` → `True` | 1 failed, 30 passed | `r32_duracion_con_un_decimal_y_textos_sin_escapar` |
| `create_albaran_compra_use_case.py:1338` | `linea.avisos[:0] = propios` → `[:1]` | 1 failed, 30 passed | `r16_los_avisos_del_contrato_van_delante_…` |
| `albaran_compra_statements.py:992` | `set(fila) != set(columnas) or len…` → `and` | 1 failed, 30 passed | `r25_la_fila_fija_con_una_columna_cambiada_…` |
| `create_albaran_compra_use_case.py:1328` | `datos.cantidad > 0` → `> 1` | 1 failed, 30 passed | `r18_supera_pendiente_tambien_con_cantidades_…` |
| `albaran_compra_models.py:220` | `paride … strict=True` → `strict=False` | 1 failed, 30 passed | `r14b_paride_como_texto_no_cuela` |
| `create_albaran_compra_use_case.py:599` | `float(suma_can or 0)` → `or 1` | 1 failed, 30 passed | `r20_sumas_null_del_contrato_en_el_commit` |
| `create_albaran_compra_use_case.py:1328` | `servido[ide] > pendiente + 1e-9` → `>=` | 1 failed, 30 passed | `r18_servir_exactamente_lo_pendiente_no_avisa` |

Los 31 tests fijan comportamiento de la spec: R17 (`precio` 0 válido, solo `< 0` falla), R18 (fronteras de
`supera_pendiente`/`servido_negativo`), R19 (ε = 1e-6 estricto, «< ε»), R20 (sumas NULL = 0), R30 (NULL leídos), R32
(un decimal, sin escapar la `ñ`; la referencia sí se traza), contrato §2 (`min_length=1`, `ge=1`, `strict`). Ver O1.

### Los 2 equivalentes (punto 2, RM5): reproducidos los DOS, no solo uno

- **Suite entera en serie** con cada mutante aplicado (worktree de HEAD): `l1328 >= 0`: `2370 passed, 1 skipped` (exit 0);
  `l1333 <= 0`: `2370 passed, 1 skipped` (exit 0). Sobreviven.
- **Diferencial propio** (no el del implementer: guion mío, semilla 20261007, módulo mutado cargado aparte, dobles de
  `f009_dobles.py`): 3.000 peticiones válidas de 1-5 vinculadas sobre 9001-9003, cantidades enteras, con 3 decimales y en
  frontera (±0,001, 4,999, 5, 5,001, 80, −5, −20), `canser` NULL/0/5/20/`can`/al azar, precio del contrato u otro, 30 %
  en commit; se compara `model_dump` entero o el error. Resultado: **0 diferencias** en los dos. Control negativo (línea
  de `cantidad` 0 colada con `model_copy`, sin validar): **76 y 39 de 200 difieren**. El diferencial ve la diferencia.
- Razonamiento confirmado en el código: solo difieren con `cantidad == 0`; `LineaAlbaranIn` la rechaza
  (`albaran_compra_models.py:236`, `== 0` caza también `-0.0`) y lleva `allow_inf_nan=False` (`:210`), así que tampoco
  entra NaN; `_avisos_de_contrato` solo lo llama `completar` sobre líneas de la petición validada, nunca sobre lo leído.
- **Equivalentes de verdad.** RM3: ninguno sale muerto en la campaña.

### `8a85804`, los 14 sitios quitados (punto 4)

Canario mío sobre HEAD (worktree desechable): `_Linea.__getattribute__` que lanza si se lee `None` en `paride`,
`natide`, `cueide`, `caaide`, `tipmov` o `ivaide`, y `ide_log=_CanarioLog()` (revienta en `__int__`, `__eq__`, `__str__`,
`__format__`…) en lugar del `None` del commit:
```
canario:     exit 0 | 2370 passed, 1 skipped, 1 warning in 69.43s | lineas CANARIO: 0
neg_paride:  exit 1 | 110 failed, 110 passed | CANARIO: se leyo _Linea.paride sin asignar   (sin `base.paride = paride`)
neg_tipmov:  exit 1 | 84 failed, 136 passed  | CANARIO: se leyo _Linea.tipmov sin asignar   (sin `linea.tipmov = …`)
neg_ide_log: exit 1 | 1 failed, 219 passed   | CANARIO: se uso ide_log de relleno         (sin el `replace(filas, log=…)`)
```
(controles con `test_f009_use_case`, `_mutacion`, `_equivalencia` y `_caracterizacion`). Lo demás, confirmado leyendo el
origen del dato: `paride` lo pone siempre `_resolver_lineas:702` (`resolver_partida` da 0 sin partida); `ivaide`, el
constructor de `_vinculada` (`:1153`) y `_plantilla_de_linea` (`:1295`); `natide/cueide/caaide/tipmov` de las sin vincular,
su constructor (`:1194-1197`); `ctride` se calcula tras la guarda `contrato_no_encontrado` (`:460`), con `de_la_obra` no
vacío por construcción; el `assert` del almacén (`:1184`) tiene su invariante en `_resolver_lineas:674`, que lo fija antes
de resolver ninguna línea si hay alguna sin vincular (mismo patrón que los `assert` ya aprobados en `:140` y `:701`).
**RM6** (los tres `zip(strict=True)`): `numerar` indexa con `enumerate` sobre la lista que construye dos líneas antes
(`ides_dcapro`, `range(len(filas.dcapro))`); `encadenar_balances` (`statements:290-307`) añade un `Balance` por
movimiento, fijado por `test_f009_r19_encadenar_devuelve_un_balance_por_movimiento` (0-11 movimientos). Invariante
verificado en quien construye el dato, por escrito en el código (`:809-810`) y en el informe.
**Sin cambio de comportamiento**: suite entera verde; el dorado (`tests/fixtures/f009_caracterizacion.json`) y
`test_f009_caracterizacion.py` no tienen commits en T16 (`git log 8a85804^..HEAD` vacío). `8a85804` solo toca los dos
ficheros nuevos de F-009: ni el clásico (`create_purchase_albaran_use_case.py`), ni `create_direct_albaran_use_case.py`,
ni `infrastructure/`, ni los modelos del contrato §2-§4.

### `92bf606` (punto 5)

El doble de `get_settings` en `sql_models` solo fija los ocho límites que leen los validadores de `SqlReadRequest` y
`SqlWriteRequest` (comprobados en `domain/models/sql_models.py:32-130`). Con `ALLOWED_DATABASES=ruesma` en el entorno:
versión de `ebb0ddc` `2 failed, 2 passed`; la actual `4 passed`. **Control negativo** (la tupla doble de siete en vez de
ocho): `4 failed`. El test sigue vigilando lo que vigilaba.

### Árbol (punto 6)

`python -m harness.mutacion --estado`: «Sin campaña de mutación en curso.». `git worktree list`: solo el principal (los
dos míos, quitados). `git status`: solo `` `0`].{t `` en la raíz, el fichero ajeno preexistente, en su sitio.

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola `in_progress` (F-009) · [x] rama `feature/F-009-alta-albaran-compra` · [x] `current.md` de la
  sesión activa · [x] ninguna feature cerrada en este lote.
- **C3** [x] hexagonal (solo `application/` y tests) · [x] primera línea con ruta · [x] sin prints ni secretos · [x]
  reglas de Sigrid intactas (no cambia SQL ni orden de escrituras).
- **C3 bis** N/A: el lote no trae documentos de fuera.
- **C4** [x] trazabilidad (tests `test_f009_rN_*` por requisito, tabla de 76 filas en `mutacion_F-009.md`) · [x] sin red
  ni BBDD · [x] manuales T19-T24 listados en `tasks.md`.
- **C4 bis** [x] `rigor: critico` · [x] RED real (tabla de 76 filas; 8 reproducidas por mí) · [x] cobertura 100 % ·
  [x] mutación con totales recalculados · [x] muertos: campaña no reejecutada (35 min), recálculo + 8 muestras ·
  [x] coste por mutante 2.077,9 × 4 ÷ 481 = 17,3 s ≥ 1 s · [x] sin «CAMPAÑA NO VÁLIDA», «Sin veredicto» 0 ·
  [x] RM1: SHA `8a858049…` completo; lo posterior a él no toca producción · [x] RM2: 481 × 4,3 ≈ 2.068 s ≈ total; media
  × W = 17,3 s frente a una base de 109-113 s: 1/6, sin salto de orden de magnitud (`-x`, 479/481 muertos) ·
  [x] RM5: reproducidos los dos equivalentes · [x] RM6: arriba · N/A campaña manual: no la hubo, fue automática ·
  [x] análisis de los 2 supervivientes completo (ver condición de cierre abajo) · [x] «Evidencias» con los cuatro
  números, SHA y workers · [x] ningún N/A sin motivo.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T16 `[x]` y 4 commits `F-009 T16: …` · N/A artefactos sin trackear: el único es `` `0`].{t `` (24-09,
  ajeno a F-009, ya anotado en el lote D; decide el humano) · [x] `features.json` coherente (`in_progress`).

**Condición de cierre de la feature (no de este lote)**: en `critico` los 2 equivalentes necesitan la **aceptación del
humano** (PARADA 2). El análisis está completo y verificado aquí; sin esa aceptación, F-009 no puede pasar a `done`.

## Observaciones (no bloquean)

1. `tests/test_f009_mutacion.py:254-274` fija que las lecturas de una fila piden `max_rows=None` (mata `muchas: bool =
   False` → `True`) y `:184-198` fija `frozen` en clases internas (`_Obra`, `_Contrato`, `_Construido`). Las dos rozan la
   implementación más que la spec; se aceptan por fijar el contrato con el puerto y la reentrada de R27 (precedente
   F-006), pero un refactor legítimo las tendrá que tocar.
2. `progress/mutacion_F-009.md:196`, fila 72: el «original → mutado» sale corrompido porque el comentario de la línea lleva
   ` -> ` (`# dbo.usu.cod -> log.usu`). Cosmético; reproducible igualmente por línea y operador.
3. El mensaje de `db945d6` dice 61 supervivientes; son 60 (lo reconoce el propio informe, `impl_…:9`).
4. `_Linea.natide/cueide/caaide` (`int | None`) se pasan a `construir_dcapro_sin_vincular`, anotado con `int`: solo de
   tipos, sin efecto en tiempo de ejecución (sin mypy en la puerta).

## Cambios requeridos

Ninguno.
