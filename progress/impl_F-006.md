<!-- progress/impl_F-006.md -->
# F-006 · Informe del implementer

`POST /api/sigrid/partes-reclamacion`: alta en lote de partes de reclamación de Posventa
(`con.tip 708`), una transacción por parte, dry-run por defecto. Rama
`feature/F-006-alta-parte-reclamacion`, rigor `critico`. Spec aprobada con Q1-Q4; ninguna
reabierta. **Nada escrito contra Sigrid**: sin despliegue, sin App Settings, sin `sql/write`
ni endpoints de dominio contra la API desplegada.

## 1 · Qué se hizo, por tarea

| Tarea | Commit | Qué |
|---|---|---|
| T3 | `c0fc82b` | `tests/test_f006_settings.py` en rojo (R4, R5), con el entorno aislado como F-004 T14c |
| T4 | `8bda5d1` | Cuatro campos en `config/settings.py` (prefijos por `parse_string_list`) y claves en `local.settings.sample.json` |
| T5 | `81bc619` | `tests/test_f006_models.py` en rojo (R1, R2, códigos cerrados) |
| T6 | `1af37d9` | `domain/models/parte_reclamacion_models.py` |
| T7 | `e3f4006` | `tests/test_f006_statements.py` en rojo: SQL carácter a carácter de L1-L10 y E2-E14 |
| T8 | `b660e22` (+ `69d8390`, origen OLE en UTC explícito, sin cambio de valor) | `application/use_cases/parte_reclamacion_statements.py` |
| T9 | `ee22b9f` | `tests/test_f006_use_case.py` en rojo, con repositorio, cursor y reloj dobles |
| T10 | `13664ef` | `application/use_cases/create_partes_reclamacion_use_case.py` |
| T11 | `2af370e` | Ruta `sigrid/partes-reclamacion` en `function_app.py` (+57, −0) y `tests/test_f006_route.py` |
| T12 | `deb60f0`, `3852580` | Suite completa en verde; test de rutas inmune a `get_functions()` no idempotente del SDK; cobertura del reloj por defecto |
| T14 | `33d7b66`, `b4dea19`; `azure-apps` **`7df52e9`** | `docs/ARCHITECTURE.md`, mapa de rutas de `CLAUDE.md`, `azure-apps/sigrid_api.md` (§intro, §1.1, §4, §4.1, §7.1, §7.2, §7.5, §7.6, §8, §8.9 nueva, §9.2, §10) |
| T13 | `22e23f7` + ronda 2 | Mutación completa: ver §6 y [`mutacion_F-006.md`](mutacion_F-006.md) |
| Revisión | `2edba47`, `657a9bf`, `52ba4be` | T17 y T16 del guion manual (§7) y M1, el aviso de `ValidationError` sin valores (§9) |

T1/T2 venían hechas. **T15-T18 son MANUALES del humano y no se han tocado** (§7). T19: §6.

## 2 · Ficheros

Nuevos: `domain/models/parte_reclamacion_models.py` (206 l.),
`application/use_cases/parte_reclamacion_statements.py` (~465 l.),
`application/use_cases/create_partes_reclamacion_use_case.py` (~805 l.) y los cinco
`tests/test_f006_*.py`. Modificados: `config/settings.py` (+16), `local.settings.sample.json`,
`function_app.py` (solo añade; `git diff` sin líneas `-`), `docs/ARCHITECTURE.md`, `CLAUDE.md`,
`specs/.../tasks.md`, `progress/current.md`. **Sin tocar**: `infrastructure/security/*`,
`sql_server_repository.py`, ninguna ruta existente, ninguna App Setting existente
(`ALLOWED_WRITE_DATABASES` sigue `["ruesma"]`), `requirements.txt`.

## 3 · Decisiones de diseño y desviaciones (todas en `progress/current.md`)

1. **L1 con la plantilla literal.** `sercon.cod` guarda `RS<año2>.<mes>/` tal cual (leído, §4);
   L1 la pide con `?` y el prefijo de cada parte sale de su `fec` local de Madrid
   (`prefijo_de_serie`). Un lote que cruce la medianoche de fin de mes numera cada parte en su mes.
2. **Numeración del dry-run leída una vez por lote** (L9, L10, `peek_next_ide`) y desplazada por
   los `previsto` anteriores; `design.md` dice «por parte»: igual resultado, 6×50 conexiones menos.
3. **E5 solo con intervinientes.** Sin ellos no se reserva `ide` de `rcpint` (no se usaría); el
   applock `SIGRID_IDE_rcpint` se toma igual, para no alterar el orden.
4. **Timeout de cada transacción = `DEFAULT_WRITE_TIMEOUT_SECONDS`**: R4 no trae uno propio.
5. **`IntegrityError` por nombre de clase** (sin `pyodbc` en `application/`). Agotados los
   reintentos → `colision_de_clave`; otra excepción → `error_de_escritura`, sin reintento.
6. **Mayúsculas.** `PVI-` tal cual (más estricto); lo demás con `casefold()`, como la colación CI.
   El primer parte con una referencia es su dueño; los siguientes, `referencia_duplicada_en_lote`.
7. **`committed` = se creó al menos un parte** (en commit sin creados, `false`, como F-004).
8. Serie: si no hay **exactamente una** fila activa con `tam 4` → `serie_no_encontrada`.
9. Tras la ronda 1 de mutación se quitó código muerto con su invariante en quien construye el
   dato (RM6): `fila[:N]`, `or 0` de `cliide/recide`, `frozen` de `_Lote` y el `0` de
   `ide_rcpint` sin intervinientes (detalle en `mutacion_F-006.md`).

## 4 · Lecturas contra el ERP (solo `sql/read`, 2026-09-24)

- `sercon WHERE tip = 708` → 213 `RS<año2>.<mes>/` (emp 1, tam 4, act 1, estini 1) y 214 `RP…`
  (emp 0); la L1 exacta → 1 fila (213, 1, 4, 1). `con.cod` varchar(24), `con.tiemod` float.
- `INFORMATION_SCHEMA.COLUMNS` de `con`, `rcp`, `rcpint`, `conext`, `log`: 19/20/5/11/14
  columnas con **exactamente** los nombres y el orden de `design.md` §Filas.
- 2026-09-25 (revisión): **una** lectura para el oficio del negativo de T16 (citada en T16).

## 5 · Fase RED (trazas reales)

Cada test se escribió y ejecutó ANTES que su código; salida real recortada a las líneas de error. Los centrales (R11-R15) se vieron además fallar contra un esqueleto vacío (`run` -> `NotImplementedError`) antes de escribir el caso de uso.

**T3 RED**

```
$ python -m pytest tests/test_f006_settings.py -q
E AttributeError: 'Settings' object has no attribute 'sigrid_reclamacion_prefijos_referencia'   (x9)
E AttributeError: 'Settings' object has no attribute 'sigrid_reclamacion_write_enabled'. Did you mean: 'sigrid_domain_write_enabled'?  (x2)
E AssertionError: falta SIGRID_RECLAMACION_WRITE_ENABLED en local.settings.sample.json
12 failed, 1 passed in 4.33s
```

**T5 RED**

```
$ python -m pytest tests/test_f006_models.py -q
tests\test_f006_models.py:17: in <module>
    from domain.models.parte_reclamacion_models import (
E   ModuleNotFoundError: No module named 'domain.models.parte_reclamacion_models'
ERROR tests/test_f006_models.py
1 error in 2.29s
```

**T7 RED**

```
$ python -m pytest tests/test_f006_statements.py -q
    from application.use_cases.parte_reclamacion_statements import (
E   ModuleNotFoundError: No module named 'application.use_cases.parte_reclamacion_statements'
ERROR tests/test_f006_statements.py
1 error in 0.77s
```

**T9 RED**

```
$ python -m pytest tests/test_f006_use_case.py -q
    from application.use_cases.create_partes_reclamacion_use_case import (
E   ModuleNotFoundError: No module named 'application.use_cases.create_partes_reclamacion_use_case'
ERROR tests/test_f006_use_case.py
1 error in 0.49s
```

**T10 RED contra esqueleto vacío (run -> NotImplementedError), R11-R15**

```
$ python -m pytest tests/test_f006_use_case.py -q -k "r11 or r12 or r13 or r14 or r15"
application\use_cases\create_partes_reclamacion_use_case.py:10: NotImplementedError
FAILED ...::test_f006_r11_work_ejecuta_e1_a_e14_en_orden
FAILED ...::test_f006_r13_una_colision_repite_la_transaccion_entera_con_numeros_nuevos
FAILED ...::test_f006_r14_una_relectura_que_no_cuadra_revierte[con] (y rcp, rcpint, conext, log)
FAILED ...::test_f006_r15_commit_idempotente_dentro_de_la_transaccion
(... 22 en total)
22 failed, 58 deselected in 3.40s
```

**T11 RED**

```
$ python -m pytest tests/test_f006_route.py -q
E AssertionError: assert 'sigrid_partes_reclamacion' in ['sql_read', 'sql_write', 'sigrid_contrato_lineas', 'sigrid_albaran', 'sigrid_albaran_directo', 'sigrid_concepto_grafico', ...]
E AttributeError: <module 'function_app' ...> has no attribute 'CreatePartesReclamacionUseCase'   (x9)
10 failed, 1 warning in 2.31s
```

Además, cada test añadido en la ronda de mutación tiene su RED en la campaña 1: es el
mutante superviviente que lo motivó (listado en `mutacion_F-006.md`), que en la campaña 2 muere.

## 6 · Mutación (T13, rigor `critico`, campaña completa, 8 workers)

| Campaña | SHA | Mutantes | Muertos | Supervivientes | Tiempo | Workers |
|---|---|---|---|---|---|---|
| 1 | `3852580` | 228 | 186 | 42 | 2.548,9 s | 8 |
| 2 (**la que vale**) | `22e23f7e9a05e0baddcb509b1851b28b4d48b80b` | **217** | **217** | **0** | 1.355,1 s | 8 |

De los 42 de la ronda 1, reevaluados **en serie** en un worktree de `3852580`: **6 falsos**
(mueren en serie: n.º 74, 76, 80, 118, 120, 121) y **36 reales**, cerrados en `22e23f7` con
28 tests y 8 líneas de código muerto quitadas (§3.9). **Cero equivalentes aceptados**; 0
timeouts, 0 sin veredicto. Ficha por ficha en [`mutacion_F-006.md`](mutacion_F-006.md).

## 7 · MANUAL pendiente del humano (T15-T18, comandos exactos en `tasks.md`)

- **T15** desplegar y fijar por JSON `SIGRID_RECLAMACION_WRITE_ENABLED=false`, `_MAX_PARTES=50`,
  `_PREFIJOS_REFERENCIA=["PVI-"]`, `_PRESUPUESTO_SEGUNDOS=150`; comprobar `ALLOWED_WRITE_DATABASES`.
- **T16** dry-run en la obra 0626 / UPV `0626.03PORTAL 1.1.A` con los dos negativos; `MAX` sin cambiar.
  **Arreglo de revisión** (cambio 2, `657a9bf`): lote literal `PVI-PRUEBA-0001/0002/0003`: el
  válido; UPV inventada; interviniente `0006` (en `auxofc`, sin `obrofc` en 0626: una `sql/read`,
  citada en T16). `LIKE` literal `RS26.09/[0-9][0-9][0-9][0-9]`, a cambiar si cae en otro mes. Sin
  red, por el caso de uso con los dobles: `previsto`, `unidad_postventa_no_encontrada`, `interviniente_no_esta_en_la_obra`.
- **T17** `commit:true` autorizado de **un** parte, lecturas de comprobación y ficha en Sigrid.
  **Arreglo de revisión** (cambio 1, `2edba47`): `SIGRID_DOMAIN_WRITE_ENABLED` **no se toca** (ya
  `true`; la usan albaranes y `concepto-grafico`). Se abre **solo** `SIGRID_RECLAMACION_WRITE_ENABLED`
  (`f006_abrir_reclamacion.json`) y se cierra a `false` (`f006_cerrar_reclamacion.json`) **después
  de T18** (R10), con `--settings "@…"` y el `appsettings list` de T15. Cuerpo del `commit` literal.
- **T18** repetir → `idempotente`; anular en la UI (NO PROCEDE, sin correo), nunca `DELETE`;
  y cerrar la llave (paso 3 de T17).
- Aviso para T16: sin `SIGRID_RECLAMACION_PREFIJOS_REFERENCIA=["PVI-"]` desplegada, **todo**
  parte sale `referencia_no_permitida`, también en dry-run (defecto cerrado de R4).

## 8 · Fuera de alcance y notas

- `azure-apps` tiene un commit local nuevo (`7df52e9`), sin push; solo `sigrid_api.md`.
- `docs/ARCHITECTURE.md` ya omitía antes `attach_concepto_grafico_use_case` (F-004); no se tocó.
- El fichero vacío sin trackear `` `0`].{t `` (ajeno, del 2026-09-24 12:31) impedía la campaña
  paralela (exige árbol limpio): se apartó al scratchpad y se devolvió al terminar.
- `ruff` en los ficheros nuevos: `All checks passed!`; los 3 avisos de `function_app.py` son previos.
- M1 solo toca el log: el 400 sigue devolviendo `exc.errors()` (con `input`) a quien pidió, y
  las demás rutas siguen logueando `str(exc)`.
- Aviso para T15 (no tocada): `sigrid_api.md` §11 dice que los paréntesis JMESPath rompen `az.cmd`
  en Windows, y su `--query` usa `starts_with(...)`.

## 9 · Ronda de revisión: M1 (`52ba4be`)

El aviso de `ValidationError` de esa ruta (`function_app.py:355`) volcaba `str(exc)`, con
`input_value`; ahora solo `[(loc, type), …]`, p. ej. `[(('partes', 0, 'oficio'), 'missing')]`.
Test `test_f006_r20_el_aviso_de_validacion_no_vuelca_los_valores_de_entrada` (falta `oficio`;
descripción > 128), con referencia y descripción marcadas.

**RED** (test escrito, código sin tocar):

```
$ python -m pytest tests/test_f006_route.py -q -k r20
E       AssertionError: assert 'input' not in 'ValidationE...11/v/missing'
E           =missing, input_value={'referencia_externa': 'P..., 'proveedor': '1181'}]}, input_type=dict]
E       AssertionError: assert 'MARCA' not in 'WARNING  fu...g_too_long\n'
E           ut_value='MARCA-DESCRIPCION-NO-LOG...xxxxxxxxxxxxxxxxxxxxxxx', input_type=str]
FAILED tests/test_f006_route.py::test_f006_r20_el_aviso_..._entrada[cambios_del_parte0-oficio-oficio-missing]
FAILED tests/test_f006_route.py::test_f006_r20_el_aviso_..._entrada[cambios_del_parte1-None-descripcion-string_too_long]
2 failed, 10 deselected, 1 warning in 2.88s
```

**GREEN**: `python -m pytest tests/test_f006_route.py -q` → `12 passed`.

**Mutación acotada** (`--base 657a9bf`): el arnés da **CERO MUTANTES** (exit 3, sin
informe) porque esas líneas no tienen operador que mutar. Evidencia aportada de otra forma:
**8 mutantes manuales aplicados y ejecutados, 8 muertos, 0 supervivientes** (volver a `exc`,
sin `loc`, sin `type`, dict entero con `input`, lista vacía, sin prefijo, `debug`, `info`).
Detalle en [`mutacion_F-006.md`](mutacion_F-006.md) §Ronda de revisión.

## 10 · Evidencias

| Evidencia | Valor |
|---|---|
| **Tests ejecutados** | **1.733 pasan**, 1 se salta, 0 fallan (`bash harness/init.sh`, 2026-09-25, código de `52ba4be`); de F-006, **231** (`-k f006`: 85 del caso de uso, 76 del modelo, 45 del constructor, 13 de ajustes, **12** de la ruta) |
| **Cobertura de las líneas cambiadas** | **100,0 %** — `PUERTA COBERTURA: 100.0% de 560 líneas cambiadas cubiertas (560/560, umbral 80%, nivel critico)` |
| **Mutantes generados y supervivientes** | Rama completa: **217/217 muertos, 0 supervivientes** sobre `22e23f7` (§6; el resto del código de producción no ha cambiado). Ronda M1 sobre `52ba4be`: el arnés genera **0** (exit 3); **8 manuales, 8 muertos** (§9) |
| **Tiempo de la suite** | **101,62 s** bajo `coverage`, **en esa ejecución** de `init.sh` sobre el código de `52ba4be` (la de cierre, sobre `49bbd25`: 1.733 pasan en 96,68 s, `ENTORNO LISTO`; la de T19, 151,79 s); los tests de F-006 solos, 4,24 s |
| **`bash harness/init.sh`** | **`ENTORNO LISTO`** (exit 0): cobertura `[OK]`, tamaño `[OK]`, 80 avisos de `ruff`, los previos |
| **Contra el ERP** | 3 `sql/read` (§4), la tercera en esta ronda. Ninguna escritura, ningún despliegue, ninguna App Setting |
