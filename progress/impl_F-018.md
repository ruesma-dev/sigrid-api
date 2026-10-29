<!-- progress/impl_F-018.md -->
# F-018 · Informe del implementer

Spec v1.2 aprobada por el humano (P1-P11). Rama `feature/F-018-descuento-por-linea`. Rigor `critico`. **T1-T17 hechas**
(T15 en `azure-apps` `f168a36`); pendientes T18 (revisión) y T19-T20 (MANUAL). `bash harness/init.sh` en verde.

## T0 · Contratos (sin código; `02dc4ad`)

- `contrato_albaranes.md` → **v8.4** (§2.2 `precio` y fila `dto`, §2.3, §3.1, §3.2, §3.4, §4.2, §4.3 y H8) y
  `contrato_proformas.md` → **v1.3** (§2.2, §3, §3.1, §4, §6 y §8). §4.3 del de albaranes se corrigió aunque T0 no lo
  listaba: decía «no aplica descuentos». Los textos de aviso a las dos sesiones están en este fichero en `02dc4ad`.
- **Acuses (2026-10-29, por el líder):** `albaranes` y `proformas` aceptan la v8.4 y la v1.3.
- **Texto de `albaranes`** (§2.2, columna «Origen en albaranes» de `precio` y `dto`, nota de notación I/P/d/Qs, y §2.4
  regla 4; `7aae0ba`, commit propio): pegado tal cual. El único retoque es escapar `|I|`/`|Qs|` (`\|`) dentro de la
  tabla. **Cotejado con §2.2/§3.1 y con la spec: sin choque.** `round(d, 2)` con 0 < d ≤ 100 cabe en R4. El bruto
  que cuadra a ±0,01 sigue R1/R2. Sin `dto` con d = 0 es R7. El porcentaje único es H8. No comparar con el `ctrpro`
  es compatible con D3. Una diferencia que no es choque: ellos no leen `dto`/`precio_bruto`; §3.1 decía «leerlas si
  vienen», y la previa se compara por `total`.

## P11 (bloqueo antes de T1, resuelto)

`test_f009_models.py::test_f009_r7_la_respuesta_es_superconjunto_de_la_clasica` (l. 538-548) fija los campos de
`LineaResultado`. Medido con el cambio aplicado y revertido: 4 fallos (P9, P10 y este) y 3.546 en verde (`514baa1`).
**P11 = (a)**, decidida por el humano el 2026-10-29. En la spec, `841e291`.

## T1 · Línea base de R7

`python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py tests/test_f016_*.py -q` →
**1484 passed** (22,5 s), sobre `9886967`. Ficheros (25), red de R7: `test_f007_{filas, models, perfil, route,
settings, statements_contrato, statements_lineas, transaccion, use_case}`, `test_f009_{caracterizacion, equivalencia,
models, mutacion, route, settings, statements, use_case}`, `test_f015_{statements, use_case}`, `test_f016_{models,
route, settings, statements, transaccion, use_case}`.

## Qué cambió (T2-T17)

| Fichero | Cambio |
|---|---|
| `domain/models/albaran_compra_models.py` | `LineaAlbaranIn.dto` (estricto, 0-100, ≤ 2 decimales) y `con_dto`; `LineaResultado.dto`/`precio_bruto` con serializador que los omite si son `None` (D8); aviso `dto_distinto_del_contrato` |
| `application/use_cases/albaran_compra_statements.py` | Puras: `texto_de_dto`, `porcentaje_de_dto` (solo `^\s*\d+(,\d+)?\s*%\s*$`, `re.ASCII`), `importe_con_dto`, `bruto_de_linea`, `dto_del_contrato`, `dto_coincide`; `construir_dcapro_*` con `dto=` y D9; `construir_dca(impbru=)`. **Sin SQL nuevo** |
| `application/use_cases/create_albaran_compra_use_case.py` | `_construir`: `dto` por nombre, importes de la fila con dto efectivo, `impbru`; `_con_dto_efectivo` (pedido, o R15 con la misma regla que la fila); `_avisos_de_dto` (R12, R13); respuesta con `dto`/`precio_bruto`; traza `n_lineas_con_dto` |
| `function_app.py` | Solo el docstring de `sigrid_albaran` |
| `docs/ARCHITECTURE.md` | Modo extendido con dto y R15; la proforma hereda R15; §Semántica 9 corregido (D11) |
| `tests/test_f018_{models,statements,use_case,proforma,compatibilidad}.py` | Nuevos (T2, T4, T6, T8, T9, T11, T12) |
| `tests/test_f009_models.py` (+2), `tests/test_f016_models.py` (+1) | Las tres líneas de P9, P10 y P11, en su commit (`cd68b11`) |
| `specs/F-018-descuento-por-linea/verificacion_manual.md` | V0-V5 con comandos literales (T17) |
| `specs/F-007-registrar-proforma/contrato_proformas.md` | Cabecera y §8: F-016 desplegada el 2026-10-28 (commit propio) |
| `azure-apps/sigrid_api.md` | §8.6, §8.10 (y su cabecera: F-016 desplegada), §8.10.1, §9.4, §12; `f168a36` en `azure-apps` |

`create_proforma_use_case.py`, `PerfilAlta`, los dobles, las fixtures y todo lo prohibido: **sin tocar** (T13, abajo).

## Decisiones de diseño

- **Dto efectivo en un solo sitio** (`_con_dto_efectivo`): `con_dto`, o vinculada que casa por la opción C con un
  `ctrpro` cuyo `dto_del_contrato` no es `None`. Decide importes, `impbru` y claves de respuesta con la misma regla
  que `construir_dcapro_vinculada` usa para la fila, así que fila, totales y respuesta no pueden divergir.
- **Importes de la fila con dto efectivo** (Flujo 2): `tot`/`ivacuo` se toman de la fila; recalcularlos desde el
  `pre` neto movería céntimos. `impbru` = Σ `bruto_de_linea(can, tar)` de esas líneas + Σ `tot` de las demás, y solo
  se pasa si hay alguna (si no, `None` → `totbas`, R7).
- **R12/R13 solo con `con_dto`**: sin `dto` pedido, el aviso de precio es el de hoy, literal (R15 no avisa). Con
  `dto`, el precio se compara con `ctrpro.tar` (mensaje «precio bruto»), y el porcentaje con `dto_coincide`: `None`
  (no legible) da un mensaje que cita el texto y dice «no se puede leer»; vacío cuenta como `0%`.
- **Tests**: un test de T2 mutaba la lista `lineas` de la fixture compartida de F-007 y rompía tests de F-007 al
  correr juntos; ahora crea una lista nueva (en T10). La retención usa el literal `12.97` (`13.53 - 0.56` en float
  da `12.969999…`).
- **R23 por huella**: `test_f018_r23_las_sentencias_son_las_de_dev` fija el sha256 de `todas_las_sentencias()` de
  albarán, proforma y cadena, medido en un worktree de `dev` (`6aca027`): 47/6/3 sentencias, idénticas a la rama.

## Desviaciones

Ninguna respecto a la spec. Además de lo que lista T15, se corrigió la cabecera de `azure-apps` §8.10, que decía
«F-016 pendiente de despliegue». También, por encargo del líder, la cabecera y §8 de `contrato_proformas.md`
(`6d11dcd`, commit propio).

## Fase RED (salidas reales, filtradas a las líneas `E`/`FAILED`/resumen; el texto completo, en la sesión)

Cada test se escribió y ejecutó **antes** que su código y se comiteó en rojo (T2, T4, T6, T8 y T9: commits solo de tests).

**T2** (`9cd79ad`) · `python -m pytest tests/test_f018_models.py -q -p no:cacheprovider` (errores agrupados con
`sort | uniq -c`):
```
     16 E       pydantic_core._pydantic_core.ValidationError: 1 validation error for LineaAlbaranIn
      3 E           KeyError: 'dto'
      2 E                   AttributeError: 'LineaProformaResultado' object has no attribute 'dto'
      1 E       AssertionError: assert 'dto_distinto_del_contrato' in frozenset({'cabecera_sin_dato', 'cod_provisional', ...})
      1 E                   AttributeError: 'LineaResultado' object has no attribute 'dto'
      1 E                   AttributeError: 'LineaProformaOrigenResultado' object has no attribute 'dto'
      1 E                   AttributeError: 'LineaAlbaranIn' object has no attribute 'dto'
26 failed, 24 passed, 1 warning in 4.04s
```
(Los 24 en verde son los inválidos que ya rechazaba `extra="forbid"` y R20, que ya se cumplía.) Verde tras T3: 50.

**T4** (`3ed597e`) · `python -m pytest tests/test_f018_statements.py -q -p no:cacheprovider`:
```
E   ImportError: cannot import name 'bruto_de_linea' from 'application.use_cases.albaran_compra_statements'
1 error in 3.18s
```
**T6** (`be77bd3`) · el mismo comando, ya con las puras de T5:
```
E       TypeError: construir_dcapro_sin_vincular() got an unexpected keyword argument 'dto'   (x3)
E       TypeError: construir_dcapro_vinculada() got an unexpected keyword argument 'dto'      (x3)
E       AssertionError: assert (4.278, '40%', 32.08, 6.74) == (4.278, '40%', 32.09, 6.74)
E       TypeError: construir_dca() got an unexpected keyword argument 'impbru'
8 failed, 90 passed in 3.68s
```
La aserción de D9 es el ejemplo de la spec: hoy 32,08, como Sigrid 32,09.

**T8** (`007f965`) · `python -m pytest tests/test_f018_use_case.py -q -p no:cacheprovider`:
```
E       AssertionError: assert (18.625, '', 18.63, 3.91) == (18.625, '40%', 11.18, 2.35)
E       assert (18.63, 18.63, 3.91, 22.54) == (11.18, 11.18, 2.35, 13.53)
E       assert (18.625, 18.625, 1.0) == (11.18, 11.18, 1.0)
E       AssertionError: assert (-0.4, 1275.6...0.27, -107.16) == (-0.4, 1275.6...7.52, -104.48)
E       assert 26.66 == 19.21
E       AssertionError: assert (12.0, '', 24.0) == (12.0, '40%', 14.4)
E       AssertionError: assert 'bruto' in 'El precio no es el de la linea de contrato: se escribe el pedido.'
E       AssertionError: assert 'dto_distinto_del_contrato' in ['sin_partida_en_linea_con_partida', 'precio_distinto_del_contrato']
E       ValueError: 'dto_distinto_del_contrato' is not in list
E       assert 32.09 == 53.48
E       assert (18.63, 0.93) == (11.18, 0.56)
E       KeyError: 'n_lineas_con_dto'
E       AssertionError: assert None == 21.45
18 failed, ... (r1, r8 x3, r9, r16, r11, r12 x2, r13 x4, r15, r18 x2, r4)
```
**T9** (`bfa2b38`) · `python -m pytest tests/test_f018_proforma.py -q -p no:cacheprovider`:
```
E       assert 10236.37 == 10257.76
E       KeyError: 'dto'
E       KeyError: 'dto'
FAILED tests/test_f018_proforma.py::test_f018_r21_cabecera_de_mes_con_impbru_y_totales_de_las_filas
FAILED tests/test_f018_proforma.py::test_f018_r21_respuesta_de_mes_con_dto_y_precio_bruto
FAILED tests/test_f018_proforma.py::test_f018_r21_a_origen_respuesta_con_dto
3 failed, 7 passed, 1 warning in 1.93s
```
Los 7 en verde: las filas de la proforma (y `importe_origen_cadena`) ya salían bien desde T7, porque la proforma
construye sus vinculadas con el núcleo (D10). El RED de R21 queda en `impbru` y en las claves de la respuesta.

**T11** (R24, en un worktree en `bfa2b38`, sin el código de T10, con los tests nuevos copiados) ·
`python -m pytest tests/test_f018_use_case.py tests/test_f018_proforma.py -k "r23 or r24" -q -p no:cacheprovider`:
```
E       AssertionError: assert (18.625, '', 18.63, 18.625) == (18.625, '40%', 11.18, 11.18)
E       AssertionError: assert None == 40.0
E       AssertionError: assert None == 40.0
E       assert 10236.37 != 10236.37
FAILED tests/test_f018_use_case.py::test_f018_r24_commit_sin_vincular_con_dto
FAILED tests/test_f018_use_case.py::test_f018_r24_commit_vinculada_r15
FAILED tests/test_f018_use_case.py::test_f018_r24_reintento_con_los_mismos_importes
FAILED tests/test_f018_proforma.py::test_f018_r24_commit_de_proforma_de_mes_con_el_dto_del_contrato
4 failed, 3 passed, 40 deselected, 1 warning in 3.36s
```
Los 3 en verde son los de R23: el SQL no cambia ni antes ni después, que es lo que fijan.

**T12** (copia aislada en un worktree en `f9b4520`: `con_dto` → `dto is not None` y `porcentaje_de_dto` aceptando
`5`, `%?`) · `python -m pytest tests/test_f018_compatibilidad.py -q -p no:cacheprovider`:
```
     16 E           assert {'respuesta':...'0404', ...}]} == {'respuesta':...'0404', ...}]}
     16 E           AssertionError: 0
      3 E       AssertionError: assert {'ok': True, ...n': True, ...} == {'ok': True, ...n': True, ...}
      2 E       AssertionError: assert {'ok': True, ...': False, ...} == {'ok': True, ...': False, ...}
21 failed, 22 passed, 1 warning in 6.49s
```
Caen los 16 casos de albarán (8 peticiones × previa/commit, con `dto` 0) y los 5 de proforma con `ctrpro.dto` `5`.

## T13 · Lo protegido no se tocó (R7, R19, D10)

El `git diff dev --stat -- …` literal de T13 solo lista `tests/test_f018_*` (nuevos), `tests/test_f009_models.py | 2 +` y `tests/test_f016_models.py | 1 +`.
`git diff dev --numstat -- tests/test_f009_models.py tests/test_f016_models.py` → `2	0` y `1	0`. Además: nada en
`infra/`, `local.settings.sample.json`, `tests/fixtures/` ni en los dobles `f007/f009/f016_dobles.py`.

## T14 · Mutación (`python -m harness.mutacion --feature F-018 --workers 1`)

Tres campañas, todas en serie; vale solo la **última**, sobre el código y los tests definitivos (`e649e38`):
**66 mutantes, 66 muertos, 0 supervivientes, 0 timeouts, 1.637,7 s** (`progress/mutacion_F-018.md`).

- **Campaña 1 (descartada, falseada).** Se paró al llegar al límite de uso de la API, en el mutante 48. El líder
  restauró con `git checkout` el fichero mutado **mientras la campaña seguía viva** (pid 804, comprobado con
  `Win32_Process`). Desde ese punto medía el código sin mutar. Se paró la tarea, `--restaurar` retiró el centinela y
  se relanzó de cero; no se reutilizó nada. Sus supervivientes se midieron a mano:
  - `importe_con_dto` `*` → `//` **era falso**: aplicado, caen 16 tests de `test_f018_statements.py`.
  - `dto_del_contrato` `<= 0` → `<= 1` y `_con_dto_efectivo` `or 0` → `or 1` **eran huecos reales**. Tests nuevos:
    `dto_del_contrato` con `1%` y `0,5%`, y `test_f018_r15_ctrpro_con_pre_0_y_otro_precio_no_copia_el_dto`. Medidos
    aplicados: caen 2 y 1 tests (`4ea35bb`).
- **Campaña 2** (`4ea35bb`, 66 / 64 muertos / 2 supervivientes; base 365 s con la máquina cargada). Dos huecos reales:
  - `_avisos_de_dto` `tar or 0` → `or 1`: un `ctrpro` sin P.Bruto con bruto pedido 1 perdía el aviso. Test nuevo:
    `test_f018_r12_ctrpro_sin_tar_avisa_del_bruto_pedido` (tar 0 y NULL).
  - El mensaje de R13 con `or 0` → `or 1`: el test comprobaba `"0%" in mensaje`, que también cumple `"40%"`. Ahora
    comprueba `"(40%)"` y `"(0%)"`.
  Los dos medidos aplicados: caen 2 y 1 tests (`24e785a`).
- **Campaña 3** (`e649e38`): 0 supervivientes; ningún equivalente aceptado sin medirlo.

## Verificaciones MANUAL pendientes

- **T18**: revisión del reviewer contra `CHECKPOINTS.md` (rigor `critico`).
- **T19** (líder, con autorización del humano, tras el despliegue que lanza el humano):
  `specs/F-018-descuento-por-linea/verificacion_manual.md`. V0 incluye la previa de regresión sin `dto`; V1 son
  lecturas; V2, V3 y V5 son previas `commit:false`.
- **T20** (humano, **con autorización expresa para esa escritura**): V4 (`commit:true` revisado en la UI, repetido
  como `idempotente` y anulado desde la UI, nunca `DELETE`), y aviso a albaranes y proformas.
- Los comandos de `verificacion_manual.md` no se han ejecutado: no hubo ninguna llamada a la API ni a Sigrid. Las
  consultas de V1 están escritas contra las columnas del código (`MOV_COLUMNAS`, `dca.obride`, `dcapro.linoriide`).
  Si alguna no devuelve fila, se anota y se para.

## Qué quedó fuera

El modo clásico y `albaran-directo` (sin `dto`, D4); que la petición de proforma admita `dto` (R20); `idempotente`
con `dto`/`precio_bruto` (D8: L11 no lee `tar` ni `dto`). La cabecera §8.6 de `azure-apps` sigue marcando F-015
como «pendiente de despliegue»: es de F-015 y no se tocó.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (`bash harness/init.sh`, 2026-10-29, sobre `e649e38`) | **3.793 passed, 1 skipped**, 0 failed |
| Tests de F-018 | 243 (`models` 50, `statements` 100, `use_case` 38, `proforma` 12, `compatibilidad` 43) |
| Red de R7 (T1 → T10) | 1.484 → 1.525 en `test_f007/f009/f015/f016_*` + `test_f018_use_case/proforma` |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 102 líneas cambiadas cubiertas (102/102, umbral 80%, nivel critico)` |
| Mutación (campaña 3) | 66 generados, 66 muertos, **0 supervivientes**, 0 timeouts (`progress/mutacion_F-018.md`) |
| Tiempo de la suite | 187,08 s (`init.sh`, con cobertura y la máquina cargada); línea base de la mutación 136,7 s |
| `bash harness/init.sh` | **`ENTORNO LISTO. Puedes trabajar.`** (exit 0); `PUERTA TAMAÑO` dentro de topes |
| Lint | `ruff check` sobre producción y `tests/test_f018_*.py`: `All checks passed!` |
