<!-- progress/mutacion_F-007.md -->
# F-007 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-007 --workers 1` el 2026-10-25 17:08.

## Alcance

Origen del diff: **rama** (`60db95586ce144d70d7c08e3640da397842c8383` .. `feature/F-007-registrar-proforma`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 12 |
| `application/use_cases/create_albaran_compra_use_case.py` | 146 |
| `application/use_cases/create_proforma_use_case.py` | 438 |
| `application/use_cases/proforma_statements.py` | 714 |
| `config/settings.py` | 27 |
| `domain/models/albaran_compra_models.py` | 14 |
| `domain/models/proforma_models.py` | 301 |
| `function_app.py` | 69 |
| `interface_adapters/http/http_response_factory.py` | 3 |
| **Total** | **1724** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 374 |
| Mutantes evaluados | 374 |
| Muertos | 372 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 3755.1 s |
| SHA de HEAD medido | `7cbff6b8a772b6325cad34e00c559c6a9977db37` |
| Línea base (s) — `.` | 67.8 |
| Media por mutante evaluado (s) | 10.0 |
| Timeout efectivo por mutante (s) | 136 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/albaran_compra_statements.py:331` [entero]

- Original: `def siguiente_cod(prefijo: str, maximo: int | None, *, cifras: int = 0) -> str:`
- Mutado:   `def siguiente_cod(prefijo: str, maximo: int | None, *, cifras: int = 1) -> str:`

#### Análisis (implementer)

> Por qué ningún test lo caza: **equivalente**. `str(n).zfill(0)` y `str(n).zfill(1)` dan lo mismo para cualquier
> entero (`str` nunca es vacío). El defecto `0` existe para que las llamadas de F-009 sin `cifras` sigan iguales
> (`tests/test_f009_statements.py::test_f009_r26_siguiente_cod` lo llama así y es intocable, R31); las dos del núcleo
> pasan `cifras=self.perfil.cifras_serie`.
> **Medido**: aplicado a mano en un worktree desechable, la suite entera en verde (`3297 passed, 1 skipped`, exit 0,
> 85,8 s, ronda 1). Decisión: **mutante equivalente, justificado para el humano**. No es código muerto: quitar el
> defecto rompe la firma que usa el test intocable de F-009.

### 2. `domain/models/proforma_models.py:170` [entero]

- Original: `return 1900 <= valor // 10000 <= 2999`
- Mutado:   `return 1900 <= valor // 10000 <= 3000`

#### Análisis (implementer)

> Por qué ningún test lo caza: **hueco del test**. `test_f007_t18_fecha_proforma_fuera_de_los_anios[30000101]` pedía
> el 400 con `periodo=300001`, que ya es inválido por sí mismo: el 400 salía por el periodo y no por el año.
> Decisión: **test corregido** (periodo válido; el modelo no cruza fecha y periodo, eso es R18 del caso de uso), commit
> `8c92d52`. Fase ROJA con el mutante aplicado en el worktree: `FAILED
> tests/test_f007_models.py::test_f007_t18_fecha_proforma_fuera_de_los_anios[30000101]` — `Failed: DID NOT RAISE
> ValidationError` (`1 failed, 1531 passed`, exit 1).

## Análisis (implementer)

**Estado final: 0 supervivientes no aceptados.** Uno equivalente justificado (§1) y uno cazado tras la ronda 2 (§2).
La ronda 2 midió `7cbff6b`; después solo cambió un test (`8c92d52`), y su mutante se midió a mano con la suite entera.

**Ronda 1** (HEAD `a3acbd7`, 375 mutantes: 308 muertos, **67 supervivientes**, 0 timeouts, 7997 s). Cada superviviente
se aplicó a mano en un `git worktree` desechable (`sigrid-api-mut007`) y se corrió la suite (los de F-007 con sus
tests; los del núcleo con F-009 y F-015 dentro). Resolución, por grupos (commit `904a2ef`):

| Grupo (nº de la ronda 1) | Qué era | Resolución |
|---|---|---|
| `muchas=True` de LP1-LP4, LP6 y las líneas del idempotente (61, 64, 67, 68, 73, 75) | **Hueco real**: sin el tope, `sql/read` aplica su defecto y un contrato grande sale truncado (400) | 2 tests: cada lectura pide `max_allowed_rows` |
| `or 0` de las filas de LP1, LP3, LP4, LP6 y `docoritip` (104-117, 211-214, 255-267) | Hueco: nadie probaba columnas a NULL (un `paride` 1 es una partida real) | Tests de `de_fila` y `lineas_del_existente` con NULL |
| `frozen=True` (43, 102, 107, 209) | Hueco de intención: lo leído y el contexto de R28 no cambian | Test parametrizado de inmutabilidad |
| Bordes de R14, R20, R21 (101, 166, 170, 172, 219, 225, 231) | Huecos: borde de tolerancia, la del primer día del periodo, contrato de 1 €, dos que casan, partida nombrada | Tests de borde |
| Mensaje de `referencia_en_conflicto` (59) y LP4 con un marcador (95) | Huecos | Tests |
| Bordes de los campos del modelo (288-352) | Huecos: longitudes 1 y 24, `strict` de los orígenes, `numero_orden` 0, periodo y fecha en sus bordes y el 29 de febrero | Tests de modelo |
| `if len(quedan) <= 1: break` en `identificar_linea` (167) | **Código muerto**: sin el `break`, un filtro que no casa no quita nada, así que el resultado es el mismo | Quitado |
| `vinculada = ctrpro_ide > 0` (84) | Regla numérica repetida | Se usa el `tipo` de línea del núcleo |
| `19000101 <= valor <= 29991231` (321), `190001 <= periodo <= 299912` (352) | **Equivalentes medidos** (29991232 y 299913 nunca son válidos) | Reescritos por el año (`1900 <= … <= 2999`): ahora el borde se puede probar |
| `int(cla or 0)` en `es_proforma` (241) | **Equivalente medido** (NULL da 0 o 1, nunca 141) | `cla == CLA_PROFORMA` y test con NULL |
| `cifras: int = 0` (4) | Equivalente medido (§1) | Justificado |
| `% 101` en `prefijo_de_serie` (3, núcleo) | **Falso superviviente de la herramienta**: a mano muere en 7 s (`test_f007_r31_prefijo_de_serie_con_el_defecto_ac`), y en la ronda 2 la campaña también lo mata | Sin cambio; anotado para `arnes-base` |

**Ficheros con ≤ 2 mutantes automáticos**: `domain/models/albaran_compra_models.py` (0) y `config/settings.py` (2).
Diez mutantes **manuales** en el worktree, suite entera, **los diez mueren**: `FalloLinea`/`AlbaranCompraError` con
un código de proforma en el conjunto base, las tres validaciones contra el conjunto fijo en vez del de la clase
(costura 5), la llave abierta por defecto, prefijos y naturalezas fuera de sus validadores, tope 100 y la lista de
productos leída de la App Setting de albaranes. `interface_adapters/http/http_response_factory.py` (0) solo cambia
un docstring (T19): no hay código que mutar. Detalle con el test que cae en `progress/impl_F-007.md`.

**Núcleo de F-009** (prioridad del encargo): 34 mutantes automáticos en `create_albaran_compra_use_case.py` y 8 en
`albaran_compra_statements.py`; ninguno sobrevive en la ronda 2 salvo el equivalente §1.

**Límite conocido de la herramienta**: no muta literales de texto ni argumentos con nombre; el SQL de LP1-LP6 lo fijan
los tests carácter a carácter.
