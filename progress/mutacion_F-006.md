<!-- progress/mutacion_F-006.md -->
# F-006 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-006 --workers 8` el 2026-09-25 00:56.

## Alcance

Origen del diff: **rama** (`210fac12d87d002fb9809ed881e36cc3e631ab3c` .. `feature/F-006-alta-parte-reclamacion`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/create_partes_reclamacion_use_case.py` | 808 |
| `application/use_cases/parte_reclamacion_statements.py` | 463 |
| `config/settings.py` | 16 |
| `domain/models/parte_reclamacion_models.py` | 206 |
| `function_app.py` | 57 |
| **Total** | **1550** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 217 |
| Mutantes evaluados | 217 |
| Muertos | 217 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1355.1 s |
| SHA de HEAD medido | `22e23f7e9a05e0baddcb509b1851b28b4d48b80b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_0` | 335.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_1` | 353.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_2` | 348.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_3` | 343.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_4` | 342.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_5` | 334.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_6` | 329.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-006_ucqpag7q/wk_7` | 331.7 |
| Media por mutante evaluado (s) | 6.2 |
| Timeout efectivo por mutante (s) | 707 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


---

> **De dónde sale ese cero** (añadido por el implementer). La primera campaña, sobre
> `3852580` (228 mutantes, 8 workers, 2.548,9 s), dejó **42 supervivientes**. Se
> reevaluaron **EN SERIE**, uno a uno, en un worktree aparte de ese SHA (aplicar la
> sustitución exacta y correr `pytest -x -k f006 tests`):
>
> - **6 eran falsos** (el modo paralelo los dio por vivos y en serie mueren): n.º 74
>   (`> 1` → `>= 1` en proveedores distintos), 76 (`or` → `and` en el filtro de
>   candidatos), 80 (`elegido[0]` → `[1]` en el aviso de filas idénticas), 118
>   (`filas[0][0]` → `[1]` en L9), 120 (`avisos + [` → `- [`) y 121 (`fetchone()[0]` →
>   `[1]`). Todos «1 failed» en serie. Es el defecto ya conocido de
>   `harness/mutacion_paralela.py` (ver `progress/current.md`): sesgo pesimista.
> - **36 eran reales** y se cerraron en `22e23f7`, sin mutantes equivalentes aceptados:
>   - **Tests nuevos** (el mutante cambiaba algo observable): trazas con reloj que no
>     arranca en 0, duración con decimales y textos no ASCII (n.º 15, 17, 18, 23);
>     `committed` con un solo parte creado (24); `pos` NULL y empates de `pos` en
>     `obrofc` (45, 92, 110, 153); un solo candidato no avisa (75); mensajes de
>     prefijos, repetido y conflicto (91, 108, 167); un carácter basta en cada
>     `min_length=1` (189, 193, 200, 205, 211, 212, 216, 222, 224); `ResumenLote()` a
>     cero (217, 218, 221, 226, 227); `Sellos` inmutable (185).
>   - **Código muerto fuera**, con el invariante en quien construye el dato (RM6):
>     `fila[:N]` sobre filas de SQL constante (64, 65, 68, 69, 90: el SQL trae
>     exactamente esas columnas y lo fija `test_f006_statements`); `or 0` de
>     `cliide/recide` (41: L5 ya hace `ISNULL(..., 0)`); `frozen` del `_Lote` interno
>     (16: se construye una vez y nadie lo muta); el `0` de `ide_rcpint` sin
>     intervinientes (160: ahora `None`, no hay fila que numerar).
>
> Esta segunda campaña, completa y sobre `22e23f7`, es la que vale: 217 mutantes (11
> menos, los de las líneas quitadas), 217 muertos. Coste por mutante =
> 1.355,1 s × 8 ÷ 217 = **50 s**; `media × W` = 6,2 × 8 = 49,6 s frente a una línea base
> de ~340 s con 8 suites compitiendo: la campaña va con `-x` y los mutantes mueren en
> los tests de F-006, a mitad de suite.

## Ronda de revisión · M1 (2026-09-25, `52ba4be`)

Campaña **acotada a las líneas cambiadas** con lo que admite el arnés (`--base` al commit
anterior al cambio):

```
$ python -m harness.mutacion --feature F-006 --base 657a9bf --workers 1 --salida <scratchpad>
F-006: 1 fichero(s), 6 línea(s) de producción (origen rama, 657a9bf308b2f14994acafc90726d4c69f30983f..feature/F-006-alta-parte-reclamacion)
CERO MUTANTES en F-006: el alcance tiene 6 línea(s) de producción pero no se ha generado ni un mutante, así que no se ha juzgado NADA.
  Motivo: esas líneas no llevan código mutable —imports, docstrings, declaraciones, cadenas— o el fichero no se pudo leer. Amplía el alcance o aporta la evidencia de otra forma, y dilo por escrito.
EXIT=3
```

**0 generados no es 0 supervivientes**: el mutador del arnés no tiene operador para
`logger.warning("…", [(error["loc"], error["type"]) for error in exc.errors()])` (solo
cadenas, subíndices y una llamada). Ampliar a `--ficheros function_app.py` mutaría las
rutas ajenas a F-006, y la campaña completa de la rama no añade mutantes nuevos: fuera de
este aviso, el código de producción es el de `22e23f7`, ya medido arriba (217/217).
**Evidencia aportada de otra forma**: 8 mutantes manuales de esas líneas. La tabla de la
ronda 1 los describía con palabras; esta (cambio 1 de `review_F-006.md`, pasada 2) trae el texto exacto
y la ha **reejecutado el implementer** sobre una copia desechable (`git archive ef1fdf9`
extraído en el scratchpad; `function_app.py` y los tests no cambian desde `52ba4be`). Cada
fila sustituye, **solo en la línea indicada** y una sola vez, el texto original por el
mutado, corre la suite de la ruta y restaura el fichero. La copia se borró al terminar.

Comando de cada fila, en la raíz de la copia (sin `-x`; la columna «con `-x`» añade `-x`):

```
python -m pytest tests/test_f006_route.py -q -p no:cacheprovider
```

| Id | Línea | Original → mutado (texto exacto) | Sin `-x` | Con `-x` |
|---|---|---|---|---|
| base | — | sin cambios | 12 passed (exit 0) | 12 passed (exit 0) |
| MA | `function_app.py:359` | `[(error["loc"], error["type"]) for error in exc.errors()]` → `exc` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MB | `function_app.py:359` | `[(error["loc"], error["type"]) for error in exc.errors()]` → `[error["type"] for error in exc.errors()]` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MC | `function_app.py:359` | `[(error["loc"], error["type"]) for error in exc.errors()]` → `[error["loc"] for error in exc.errors()]` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MD | `function_app.py:359` | `[(error["loc"], error["type"]) for error in exc.errors()]` → `exc.errors()` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| ME | `function_app.py:359` | `[(error["loc"], error["type"]) for error in exc.errors()]` → `[]` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MF | `function_app.py:358` | `"ValidationError en sigrid/partes-reclamacion: %s"` → `"%s"` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MG | `function_app.py:357` | `logger.warning(` → `logger.debug(` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MH | `function_app.py:357` | `logger.warning(` → `logger.info(` | **2 failed**, 10 passed (exit 1) | 1 failed, 7 passed (exit 1) |

La base se volvió a correr tras el último mutante: `12 passed` (exit 0). En las 8 filas
los dos fallos son los dos casos de
`test_f006_r20_el_aviso_de_validacion_no_vuelca_los_valores_de_entrada`
(`[…-oficio-oficio-missing]` y `[…-descripcion-string_too_long]`); con `-x` solo llega a
fallar el primero, y la suite se corta ahí (7 passed antes de él). En la línea 357,
`logger.warning(` aparece una sola vez; en el fichero hay más, y no se tocan.

**Por qué la ronda 1 decía «1 failed» para MA.** Lo que se obtiene sin `-x` es `2 failed`,
lo mismo que la revisión en su §3. `1 failed, 7 passed` es exactamente lo que da el mismo
comando **con `-x`** (como la campaña del arnés y la reevaluación en serie de arriba), y la tabla no lo decía. El
número de la ronda 1 era, por tanto, de una ejecución con `-x`, no de un mutante que matara
un solo caso. En los 8 mutantes caen ambos casos parametrizados.

**8 de 8 muertos, 0 supervivientes, 0 equivalentes que pedir al humano.** Todos cambian el
aviso que se observa (nivel, prefijo o contenido), así que ninguno es equivalente.
