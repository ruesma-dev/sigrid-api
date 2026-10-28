<!-- progress/mutacion_F-016.md -->
# F-016 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-016 --workers 1` el 2026-10-28 17:11.

## Alcance

Origen del diff: **rama** (`745a43c06ed67a5fec25c7e9d9a526d1d6c29b43` .. `feature/F-016-proforma-a-origen`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/create_proforma_use_case.py` | 233 |
| `application/use_cases/proforma_origen_statements.py` | 337 |
| `config/settings.py` | 4 |
| `domain/models/proforma_models.py` | 30 |
| `domain/models/proforma_origen_models.py` | 114 |
| `function_app.py` | 25 |
| **Total** | **743** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 116 |
| Mutantes evaluados | 116 |
| Muertos | 102 |
| Supervivientes | 14 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4937.2 s |
| SHA de HEAD medido | `06ffcb6b8ee3392187de6ab79388802715821ddb` |
| Línea base (s) — `.` | 129.4 |
| Media por mutante evaluado (s) | 42.6 |
| Timeout efectivo por mutante (s) | 259 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/create_proforma_use_case.py:355` [booleano]

- Original: `request, lecturas.leer_sucesoras(ctride, anterior.ide), muchas=True`
- Mutado:   `request, lecturas.leer_sucesoras(ctride, anterior.ide), muchas=False`

#### Análisis (implementer)

> Ningún test miraba el `max_rows` de LP8; el doble devuelve todas las filas pida lo que pida. Hueco real: con el defecto (200) una lectura grande saldría truncada. Medido: sobrevive (3544 passed). Decisión: **test nuevo** `test_f016_t14_lp8_y_lp9_piden_el_tope_de_filas` (`tests/test_f016_use_case.py`); medido con él: muerto.

### 2. `application/use_cases/create_proforma_use_case.py:359` [booleano]

- Original: `request, lecturas.leer_lineas_anterior(anterior.ide), muchas=True`
- Mutado:   `request, lecturas.leer_lineas_anterior(anterior.ide), muchas=False`

#### Análisis (implementer)

> Lo mismo para LP9 (las líneas de la anterior, plantilla de las arrastradas). Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_lp8_y_lp9_piden_el_tope_de_filas`; medido con él: muerto.

### 3. `application/use_cases/create_proforma_use_case.py:361` [booleano]

- Original: `filas = [dict(zip(columnas, fila, strict=True)) for fila in leidas]`
- Mutado:   `filas = [dict(zip(columnas, fila, strict=False)) for fila in leidas]`

#### Análisis (implementer)

> Con `strict=False` una lectura con columnas y valores descuadrados se truncaría en silencio; el doble siempre los da cuadrados. Medido: sobrevive. Decisión: **test nuevo** `test_f016_t14_una_lp9_mal_formada_no_se_trunca_en_silencio` (`tests/test_f016_use_case.py`, LP9 con una columna de más → `ValueError`); medido con él: muerto.

### 4. `application/use_cases/create_proforma_use_case.py:565` [entero]

- Original: `dcapro += filas_arrastradas(cadena.filas, usadas, (len(dcapro) + 1) * POS_PASO)`
- Mutado:   `dcapro += filas_arrastradas(cadena.filas, usadas, (len(dcapro) + 2) * POS_PASO)`

#### Análisis (implementer)

> **Superviviente falso.** Medido aplicándolo a mano y con la suite entera como la campaña (`-x -q --tb=no -p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`), dos veces y antes de añadir ningún test: **muerto** por `test_f016_r18_insert_de_las_arrastradas_y_relectura_con_todas` (`pos` 448 y 512), y además lo fija `test_f016_r11_r12_previa_encadenada_lee_y_escribe_la_cadena`. No sé por qué la campaña lo dio por superviviente (serie, 1 worker); queda anotado para el reviewer. Decisión: **ninguna, ya lo caza la suite**.

### 5. `application/use_cases/create_proforma_use_case.py:639` [entero]

- Original: `float(continuada.get("canoriori") or 0) if continuada is not None else 0.0`
- Mutado:   `float(continuada.get("canoriori") or 1) if continuada is not None else 0.0`

#### Análisis (implementer)

> Ninguna continuada de la fixture tenía `canoriori` 0 en la anterior, así que `or 0` y `or 1` daban lo mismo. Hueco real (M41: hay líneas con `canoriori` 0). Medido: sobrevive. Decisión: **test nuevo** `test_f016_t14_ceros_de_la_anterior_llegan_como_ceros_a_la_respuesta` (`tests/test_f016_use_case.py`); medido con él: muerto.

### 6. `application/use_cases/create_proforma_use_case.py:676` [entero]

- Original: `origen = float(fila.get("canoriori") or 0)`
- Mutado:   `origen = float(fila.get("canoriori") or 1)`

#### Análisis (implementer)

> La respuesta de una arrastrada con `canoriori` 0: ninguna de la fixture lo tenía. Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_ceros_…` (arrastrada con ceros); medido con él: muerto.

### 7. `application/use_cases/create_proforma_use_case.py:683` [entero]

- Original: `proide=int(fila.get("proide") or 0),`
- Mutado:   `proide=int(fila.get("proide") or 1),`

#### Análisis (implementer)

> `proide` 0 en una arrastrada. Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_ceros_…`; medido con él: muerto.

### 8. `application/use_cases/create_proforma_use_case.py:687` [entero]

- Original: `precio=float(fila.get("pre") or 0),`
- Mutado:   `precio=float(fila.get("pre") or 1),`

#### Análisis (implementer)

> `pre` 0 en una arrastrada. Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_ceros_…`; medido con él: muerto.

### 9. `application/use_cases/create_proforma_use_case.py:690` [entero]

- Original: `almide=int(fila.get("almide") or 0),`
- Mutado:   `almide=int(fila.get("almide") or 1),`

#### Análisis (implementer)

> `almide` 0 en una arrastrada. Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_ceros_…`; medido con él: muerto.

### 10. `application/use_cases/create_proforma_use_case.py:692` [entero]

- Original: `paride=int(fila.get("paride") or 0),`
- Mutado:   `paride=int(fila.get("paride") or 1),`

#### Análisis (implementer)

> `paride` 0 en una arrastrada. Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_ceros_…`; medido con él: muerto.

### 11. `application/use_cases/create_proforma_use_case.py:693` [entero]

- Original: `de_contrato=vinculo > 0,`
- Mutado:   `de_contrato=vinculo > 1,`

#### Análisis (implementer)

> `> 0` frente a `> 1` solo difiere con `linoriide` 1 (un `ctrpro` de `ide` 1, válido aunque improbable). Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_ceros_…` con la arrastrada vinculada al `ctrpro` 1 (`de_contrato` cierto); medido con él: muerto.

### 12. `application/use_cases/proforma_origen_statements.py:89` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer)

> Nadie intentaba modificar un `DocumentoCadena`. Lo validado fuera viaja a la transacción y a cada reintento: que sea inmutable es parte del diseño (R17, reintento reentrante). Medido: sobrevive. Decisión: **test nuevo** `test_f016_t14_los_documentos_validados_son_inmutables` (`tests/test_f016_statements.py`); medido con él: muerto.

### 13. `application/use_cases/proforma_origen_statements.py:105` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (implementer)

> Lo mismo para `CadenaValidada`. Medido: sobrevive. Decisión: **test nuevo**, el mismo `test_f016_t14_los_documentos_validados_son_inmutables`; medido con él: muerto.

### 14. `application/use_cases/proforma_origen_statements.py:256` [not]

- Original: `if not _vinculo(fila):`
- Mutado:   `if _vinculo(fila):`

#### Análisis (implementer)

> En la fixture el `imporiori` de la anterior coincidía con el que pone el núcleo (4433,64 en la vinculada y 0 en la sin vincular), así que invertir la condición no cambiaba nada. Medido: sobrevive. Decisión: **test nuevo** `test_f016_t14_continuada_imporiori_del_ctrpro_o_de_la_anterior_cuando_difieren` (`tests/test_f016_statements.py`); medido con él: muerto.

## Medición de los supervivientes (implementer, 2026-10-28)

Cada uno aplicado a mano sobre el árbol y la suite ENTERA como la campaña (`python -m pytest -x -q --tb=no -p
no:cacheprovider` con `PYTHONDONTWRITEBYTECODE=1`), restaurando después; el árbol queda limpio (`git status`).

| # | Sin tests nuevos | Con los tests de T14 |
|---|---|---|
| 1-3, 5-14 | sobreviven: `3544 passed, 1 skipped` cada uno (146-330 s) | **muertos**, cada uno por el test que nombra su análisis (21-34 s) |
| 4 | **muerto** (`1 failed, 3148 passed`): superviviente falso de la campaña | muerto |

Resultado: **0 supervivientes no aceptados**; ningún mutante equivalente que aceptar.
