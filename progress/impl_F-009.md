<!-- progress/impl_F-009.md -->
# F-009 · Informe del implementer

Rigor de la feature: `critico` (`harness/features.json`). Los informes de T0 viven aparte
(`impl_F-009_T0a*.md`); este recoge la implementación por lotes.

## Lote A · T1 (caracterización) — 2026-10-06

### Qué cambió

| Commit | Ficheros | Qué |
|---|---|---|
| `783f2d1` | `tests/test_f009_caracterizacion.py`, `tests/fixtures/f009_caracterizacion.json` | Test y dorado (6 casos) |
| `c5c51c6` | `tests/test_f009_caracterizacion.py` | Solo ruff (imports, `collections.abc`, `noqa: DTZ001` justificado); el dorado no cambia |
| `112cb3c` | `specs/.../tasks.md`, `progress/current.md`, este informe | T1 `[x]` y estado |
| `91b929d` | test, dorado (+195 líneas, 0 borradas) y `tasks.md` (T14) | **Revisión pasada 1, cambio 1**: 7 casos de las ramas de error de las rutas; T14 reformulada (decisión del líder sobre el cambio 2) |
| (seguimiento) | este informe, `progress/current.md` | Cambio 3 |

`git log --oneline -- tests/fixtures/f009_caracterizacion.json` → `91b929d`, `783f2d1`: los dos `F-009 T1:` y
anteriores a todo cambio de producción de F-009 (aún no hay ninguno). T14 dice ahora exactamente eso.

**Ni una línea de producción**: `git diff dev --stat -- '*.py' ':(exclude)tests/**'` sale vacío, y el
`git diff dev` de los cuatro ficheros de T14 da 0 líneas.

### Cómo funciona

- Entra por la **ruta HTTP real** (`function_app.sigrid_albaran` y `sigrid_albaran_directo`, con
  `_function.get_user_function()`, como `test_f006_route.py`), así que fija también la traducción de
  excepciones a HTTP. `build_dependencies` se dobla con
  `(settings, repo, None, None, None, None, CreatePurchaseAlbaranUseCase(repo, settings))`: el caso de uso
  clásico es el **real**, solo se doblan el repositorio y los ajustes.
- `RepositorioDoble` graba cada llamada en orden: `locate_contract`, `read_full_row`, `read_rows_by`,
  `peek_next_ide` (kwargs completos), `execute_read_query` (`database`, `sql`, `parameters`, `max_rows`) y
  `run_in_write_transaction` (base, timeout, applocks, timeout de applock, reintentos y **cada sentencia del
  cursor con su SQL y parámetros**: los `MAX(ide)`, los `INSERT` columna a columna, los `UPDATE`) más el
  resultado de `work`. Responde con datos fijos por SQL y parámetros.
- Aislamiento: `datetime` del módulo clásico sustituido por un reloj fijo (2026-03-15 09:30:05; el
  directo importa de él `_today_yyyymmdd` y `_now_hhmmss`), y `sql_models.get_settings` doblado, porque
  `SqlReadRequest` lo llama al validar y si no leería el `.env` de la máquina.
- `SettingsDoble` con `sigrid_albaran_write_enabled=True`: la **llave de R8 abierta**, para que los casos
  de commit pasen igual antes y después de F-009 (design §Caracterización). Hoy ese atributo no lo lee nadie.
- Lo observado (`ruta`, `peticion` o `crudo`, `status`, `cuerpo`, `llamadas`) se pasa por JSON y se
  compara por igualdad con el dorado, tras quitar **solo** la clave `url` de cada error de
  `details.validation` (lleva la versión de pydantic). El test **no sabe regenerar** el dorado: se escribió
  con un script del scratchpad (no versionado) que llama a `ejecutar`; la ampliación de `91b929d` **comprobó
  antes de escribir que los seis casos previos salían idénticos** y solo añadió los nuevos.

### Qué fija el dorado (13 casos: los seis de design §Caracterización y siete de las rutas)

| Caso | Qué cubre |
|---|---|
| `clasico_dry_run` | Plantilla de cabecera del mismo proveedor; 9001 con histórico de `dcapro` y `mov` (PMP recalculado); 9002 sin histórico propio (cae a la 1.ª línea del albarán plantilla) ni `mov`; pedidas en orden inverso al contrato (salen por `pos`); sin `fecha_albaran` (hoy, serie `AC26/`); `tar`/`dto`/`tex`/`unimed`/`almide`/`cenide` nulos en el `ctrpro`; los 4 `peek_next_ide`; respuesta completa |
| `clasico_commit` | **Dos `lineas_recibidas` al mismo `ctrpro` (2 + 5 = 7, se suman) que superan lo pendiente (6)** y otra con cantidad 0 (sin `UPDATE canser`, `mov` con `canent` 0); plantilla por la serie, de otro proveedor (aviso) y sin columnas `*div`; 9001 sin ningún histórico (fila mínima y aviso); `fecha_albaran` 2025 y `empide` en la petición; transacción: applocks, 4 `MAX(ide)`, `INSERT` de `con`, `dca`, 2 `dcapro`, 2 `ctrprodes`, 2 `mov`, `UPDATE ctrpro` (7.0, 5101) y `UPDATE ctr` |
| `clasico_contrato_inexistente` | 400 `{type: ValueError}` con su mensaje; solo `locate_contract` |
| `clasico_linea_ajena` | 400 con su mensaje; se para tras `read_rows_by` |
| `directo_dry_run` | Sin `almide`/`cenide` en la petición (salen de la plantilla de cada producto); `res` recortado; 9002 cae a la plantilla del documento; 3 `peek_next_ide` |
| `directo_commit` | `almide`/`cenide` en la petición; `ivaide` forzado en una línea; 9004 sin histórico (fila mínima, sin `cenide` ni `ivaide`) y cantidad 0; `su_referencia` vacía (`res` = `"… ()"`); transacción: 3 applocks, 3 `MAX(ide)`, `INSERT` de `con`, `dca`, 2 `dcapro`, 2 `mov` |
| `clasico_falla_pydantic` | Sin `cod_contrato` y `cantidad` −1: 400 `"Solicitud invalida."`, `ValidationError`, dos errores (`missing`, `greater_than_equal` con `ctx`) |
| `clasico_cuerpo_numero` / `_lista` | Cuerpo `5` y `[]`: 400 `ValidationError` `model_type` (hoy no es 500) |
| `clasico_cuerpo_no_json` | `{esto no es json`: 400 con el mensaje del decodificador y `details.type` **`JSONDecodeError`** (subclase de `ValueError`) |
| `directo_falla_pydantic` | Sin `cif_proveedor` y línea sin `can`: 400 `ValidationError`, dos `missing` |
| `directo_cuerpo_numero` | Cuerpo `5`: 400 `ValidationError` `model_type` |

En los siete de las rutas, **`llamadas` = `[]`**: no se llega al repositorio.

Además, cuatro comprobaciones legibles sobre el propio dorado (la suma 7.0 en el `UPDATE ctrpro`, los 400
`ValueError` sin transacción, las ramas de error de las rutas sin llamadas y los dry-run sin transacción),
para que un cambio del dorado no pase en silencio.

**Datos sintéticos**: base `ruesma_prueba`, CIF `B00000000`, obra `9999`, contrato `CT00/0001`, `ide`
inventados (3001, 5001…), `empide` 7777 (no el defecto real de settings). `grep -ciE
"password|pwd|secret|clave_|192\.168|2425207"` sobre el dorado: 0.

### Qué deja fuera y por qué

- **Filas construidas en dry-run**: el dry-run no expone `con`, `dcapro` ni `ctrprodes` (solo `cabecera`,
  `lineas`, `movimientos`); esas filas se fijan columna a columna en los dos casos de commit, por los `INSERT`.
  Comprobado: una mutación de `dcapro.tar` en el directo la caza `directo_commit`, no `directo_dry_run`.
- **Commit con `SIGRID_DOMAIN_WRITE_ENABLED` apagado o base no permitida**, plantilla «cualquier albarán»
  (tercer *fallback* de `_find_template_ide`), producto sin almacén en el directo, obra o proveedor
  inexistentes en el directo, contrato duplicado y `lineas_recibidas` vacía: **no los enumera el diseño** y
  viven en los casos de uso, que T14 congela (`git diff dev` vacío). Los 400 de Pydantic y de cuerpo no válido
  **sí se fijan desde `91b929d`** (viven en la ruta, que T13 edita); el directo con cuerpo no parseable no se
  añadió: es la misma línea `req.get_json()` y el mismo `except ValueError` que ya fija el clásico, y su
  ruta no gana selector en F-009.
- **Reintentos de `run_in_write_transaction`**: el doble ejecuta `work` una vez; el reintento vive en el
  repositorio, que F-009 no toca.
- **Riesgo para el lote D**: el doble de `build_dependencies` es una tupla de 7. Si T13 cambia su forma o hace
  que la ruta clásica construya el caso de uso de otra manera, habrá que adaptar **el arnés del test** (no el
  dorado); el reviewer del lote D debe comprobar T14 en su forma nueva (solo commits `F-009 T1:` en el dorado).

### Verificación: sensibilidad del test (equivalente a la fase RED)

T1 es caracterización: por diseño pasa sobre `dev` y no hay RED de «antes del código». Para demostrar que
no es un test vacío se introdujeron **tres cambios temporales de producción**, sin commit y revertidos con
`git checkout --` (después, `git status --short` sin ficheros de producción). Comando en los tres:
`python -m pytest tests/test_f009_caracterizacion.py -q`.

1. Clásico, sin sumar las líneas repetidas (`received_map[...] = float(rl.cantidad)`):
```
E         Differing items:
E         {'cuerpo': {'ok': True, 'database': 'ruesma_prueba', 'committed': True, 'dry_run': False, ...}} != {'cuerpo': {...}}
E         {'llamadas': [{'metodo': 'locate_contract', ... 'parameters': [14, 'AC25/%'], ...}, ...]} != {'llamadas': [...
FAILED tests/test_f009_caracterizacion.py::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_commit]
1 failed, 9 passed, 1 warning in 4.63s
```
2. Directo, `row["tar"] = 0` en vez de `pre`:
```
FAILED tests/test_f009_caracterizacion.py::test_f009_r3_albaran_directo_se_comporta_como_en_dev[directo_commit]
1 failed, 9 passed, 1 warning in 4.53s
```
3. `function_app.py`, un campo más en `details` de los `ValueError`:
```
FAILED tests/test_f009_caracterizacion.py::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_contrato_inexistente]
FAILED tests/test_f009_caracterizacion.py::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_linea_ajena]
2 failed, 8 passed, 1 warning in 4.12s
```

**Pasada 2 (cambio 1 de la revisión), en una copia aislada** (`git worktree add --detach` de `91b929d` en el
scratchpad, como pide C4 bis; retirada después con `git worktree remove`; el árbol real no se tocó). Cada
cambio, revertido con `git checkout -- function_app.py` antes del siguiente; comando
`python -m pytest tests/test_f009_caracterizacion.py -q -p no:cacheprovider`:

| # | Cambio temporal en `function_app.py` | Resultado |
|---|---|---|
| S1 | El sondeo del reviewer: en `sigrid_albaran`, `"Solicitud invalida."` → `"Solicitud no valida."` y selector ingenuo `if "lineas" in body or "referencia_externa" in body: raise RuntimeError` | `[clasico_falla_pydantic]`, `[clasico_cuerpo_numero]`, `[clasico_cuerpo_lista]` FAILED · 3 failed, 14 passed |
| M-a | `sigrid_albaran_directo`: `details` del `ValidationError` sin `validation` | `[directo_falla_pydantic]`, `[directo_cuerpo_numero]` FAILED · 2 failed, 15 passed |
| M-b | `sigrid_albaran`: `body.get("commit")` antes de validar (cuerpo no objeto → 500) | `[clasico_cuerpo_numero]`, `[clasico_cuerpo_lista]` FAILED · 2 failed, 15 passed |
| M-c | `sigrid_albaran`: `ValueError` de `get_json()` convertido en `RuntimeError` (→ 500) | `[clasico_cuerpo_no_json]` FAILED · 1 failed, 16 passed |

### Salida real de `pytest tests/test_f009_caracterizacion.py -v` (tras `91b929d`)

```
...::test_f009_r4_el_dorado_cubre_exactamente_los_casos_definidos PASSED [  5%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_dry_run] PASSED [ 11%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_commit] PASSED [ 17%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_contrato_inexistente] PASSED [ 23%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_linea_ajena] PASSED [ 29%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_falla_pydantic] PASSED [ 35%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_cuerpo_numero] PASSED [ 41%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_cuerpo_lista] PASSED [ 47%]
...::test_f009_r2_el_modo_clasico_se_comporta_como_en_dev[clasico_cuerpo_no_json] PASSED [ 52%]
...::test_f009_r3_albaran_directo_se_comporta_como_en_dev[directo_dry_run] PASSED [ 58%]
...::test_f009_r3_albaran_directo_se_comporta_como_en_dev[directo_commit] PASSED [ 64%]
...::test_f009_r3_albaran_directo_se_comporta_como_en_dev[directo_falla_pydantic] PASSED [ 70%]
...::test_f009_r3_albaran_directo_se_comporta_como_en_dev[directo_cuerpo_numero] PASSED [ 76%]
...::test_f009_r2_el_commit_suma_las_lineas_repetidas_del_mismo_ctrpro PASSED [ 82%]
...::test_f009_r2_los_errores_del_clasico_son_400_con_valueerror PASSED [ 88%]
...::test_f009_r2_r3_las_ramas_de_error_de_las_rutas_no_llegan_al_repositorio PASSED [ 94%]
...::test_f009_r3_los_dry_run_no_abren_transaccion PASSED [100%]
======================== 17 passed, 1 warning in 4.48s ========================
```
(`...` = `tests/test_f009_caracterizacion.py`. El aviso es el de siempre: `DocumentReadRequest.schema`.)

### `git show --stat` de los commits del dorado

```
783f2d1 F-009 T1: test de caracterización del modo clásico y de albaran-directo
 tests/fixtures/f009_caracterizacion.json | 1733 ++++++++++++++++++++++++++++++
 tests/test_f009_caracterizacion.py       |  429 ++++++++
 2 files changed, 2162 insertions(+)
91b929d F-009 T1: caracterización de las ramas de error de las dos rutas
 specs/F-009-alta-albaran-compra/tasks.md |   2 +-
 tests/fixtures/f009_caracterizacion.json | 195 +++++++++++++++++++++++++++++++
 tests/test_f009_caracterizacion.py       |  55 +++++++--
 3 files changed, 244 insertions(+), 8 deletions(-)
```
`c5c51c6`: `tests/test_f009_caracterizacion.py | 10 +++++++---`. Ninguno toca producción.

### `bash harness/init.sh`

Pasada 1 (tras `c5c51c6`): 1743 passed, 1 skipped; ruff 83 → 80 tras `c5c51c6`. Final de la pasada 2, con
este informe en su sitio:
```
[AVISO] ruff: 80 avisos (deuda previa, no bloquea)      <- igual que antes de T1
1750 passed, 1 skipped, 1 warning in 295.02s (0:04:55)
[OK] PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a dev)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 249/250, impl 192/220, review 111/140)
ENTORNO LISTO. Puedes trabajar.
```

### Evidencias

| Evidencia | Valor real |
|---|---|
| Tests de `test_f009_caracterizacion.py` | 17 pasados, 0 fallidos (4,48 s) |
| Suite completa (`init.sh` final) | 1750 pasados, 1 omitido (antes de T1: 1733 + 1; +17 de este test), 295,02 s |
| Cobertura de líneas cambiadas | N/A: T1 no cambia líneas Python de producción (`PUERTA COBERTURA: N/A`) |
| Mutantes | No aplica a T1 (no hay código de producción nuevo que mutar); la campaña de F-009 es T16 (lote E). En su lugar, 7 cambios manuales de producción (3 en el caso de uso y la ruta en la pasada 1, 4 en las rutas en la pasada 2), los 7 cazados |
| Ruff del fichero de test | `All checks passed!` |

### Pendiente

- Segunda pasada de la revisión del lote A (reviewer). Nada MANUAL en este lote.
- T14 (lote D) comprobará los dos comandos de R2-R4 en su forma nueva.
- Fuera de este lote: el residuo sin trackear `` `0`].{t `` de la raíz (anterior a F-009; lo borra el humano).
