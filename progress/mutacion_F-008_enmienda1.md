<!-- progress/mutacion_F-008_enmienda1.md -->
# F-008 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-008 --workers 1` el 2026-11-09 11:21.

## Alcance

Origen del diff: **rama** (`09339e8bdd109051ea6fb6432545234532bee254` .. `feature/F-008-registrar-factura`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 60 |
| `application/use_cases/create_albaran_compra_use_case.py` | 72 |
| `application/use_cases/create_factura_use_case.py` | 68 |
| `application/use_cases/factura_lineas.py` | 27 |
| `config/settings.py` | 52 |
| `domain/models/factura_models.py` | 36 |
| **Total** | **315** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 104 |
| Mutantes evaluados | 104 |
| Muertos | 94 |
| Supervivientes | 10 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2160.6 s |
| SHA de HEAD medido | `66c7570d39ad08fb5d09ea2ab0363fc0299f5e3b` |
| Línea base (s) — `.` | 130.8 |
| Media por mutante evaluado (s) | 20.8 |
| Timeout efectivo por mutante (s) | 262 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/albaran_compra_statements.py:665` [entero]

- Original: `[tuple(fila[1:])] if fila is not None and int(fila[1] or 0) and fila[2] is not None`
- Mutado:   `[tuple(fila[1:])] if fila is not None and int(fila[1] or 1) and fila[2] is not None`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: el caso `natide_0` del doble traía también `cod` NULL, así que la comprobación de `fila[2]` tapaba la de `natide`. Hueco real: si existiera un `auxpronat` con `ide` 0, la ficha con `natide` 0 pasaría por válida.
> Decisión: test nuevo, el caso `natide_0_con_auxpronat` en `test_f008_r50_ficha_sin_naturaleza_valida_es_naturaleza_no_valida`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 2. `application/use_cases/albaran_compra_statements.py:665` [entero]

- Original: `[tuple(fila[1:])] if fila is not None and int(fila[1] or 0) and fila[2] is not None`
- Mutado:   `[tuple(fila[1:])] if fila is not None and int(fila[1] or 0) and fila[3] is not None`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: en todos los casos del doble, `cod` y `numemp` eran NULL a la vez (sin `auxpronat`), así que mirar `numemp` daba lo mismo que mirar `cod`. Hueco real: una naturaleza con `numemp` NULL (que vale para todas las empresas) se rechazaría.
> Decisión: test nuevo, `test_f008_r50_ficha_con_numemp_y_fecbaj_nulos_es_valida`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 3. `application/use_cases/create_albaran_compra_use_case.py:1461` [logico]

- Original: `if not _entero(f[3]) and _entero(f[2]) in (0, emp)`
- Mutado:   `if not _entero(f[3]) or _entero(f[2]) in (0, emp)`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: `_naturalezas_del_mapa` es el camino de las proformas (P23). Tras la enmienda, los rechazos por baja o por otra empresa solo se probaban en el camino de la ficha. Hueco real.
> Decisión: test nuevo, `test_f008_r51_sin_ficha_el_mapa_valida_la_candidata_como_siempre` (de_baja, otra_empresa, sin_cuacomcod, dos_candidatas), con el núcleo `_CasoSinFicha`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 4. `application/use_cases/create_albaran_compra_use_case.py:1461` [entero]

- Original: `if not _entero(f[3]) and _entero(f[2]) in (0, emp)`
- Mutado:   `if not _entero(f[3]) and _entero(f[3]) in (0, emp)`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: mismo motivo que el 3: en el camino del mapa ningún caso tenía `numemp` de otra empresa sin baja.
> Decisión: test nuevo, el mismo paramétrico (caso `otra_empresa`). Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 5. `application/use_cases/create_albaran_compra_use_case.py:1463` [logico]

- Original: `if len(candidatas) == 1 and str(candidatas[0][5] or "").strip():`
- Mutado:   `if len(candidatas) == 1 or str(candidatas[0][5] or "").strip():`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: mismo motivo que el 3: en el camino del mapa no había ni dos candidatas ni una sin `cuacomcod`.
> Decisión: test nuevo, el mismo paramétrico (casos `de_baja`, `sin_cuacomcod`, `dos_candidatas`). Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 6. `application/use_cases/create_albaran_compra_use_case.py:1484` [booleano]

- Original: `self._request, self._s.leer_naturalezas_de_ficha(sin_forzar), muchas=True`
- Mutado:   `self._request, self._s.leer_naturalezas_de_ficha(sin_forzar), muchas=False`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: el `max_rows` de L15D no lo comprobaba nadie. El test R9 de F-009 cubre las lecturas de lista, pero con el doble por defecto todos los productos están forzados y L15D no se lanza.
> Decisión: test nuevo, `test_f008_r53_l15d_es_una_lectura_de_lista_y_pide_el_tope`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 7. `application/use_cases/create_factura_use_case.py:738` [logico]

- Original: `if producto in permitidos and filas and not _entero(filas[0][2]):`
- Mutado:   `if producto in permitidos or filas and not _entero(filas[0][2]):`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: un producto que existe pero está fuera de la lista blanca ya acaba en `producto_no_permitido`, así que lo único que cambia es una lectura de naturaleza de más, que ningún test miraba. Hueco real: R53 limita las lecturas a los productos que se van a usar.
> Decisión: test nuevo, `test_f008_r25_r53_producto_no_permitido_no_lee_naturalezas`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 8. `config/settings.py:366` [logico]

- Original: `or not emp.isascii()`
- Mutado:   `and not emp.isascii()`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: ningún caso tenía dígitos que no fueran ASCII. `"\u0661".isdigit()` es cierto y `int` lo convierte a 1, así que sin `isascii` la clave entraría normalizada como `1:…`.
> Decisión: test nuevo, el caso `{"\u0661:MA9999": …}` en `test_f008_r54_forzada_mal_escrita_no_arranca`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 9. `config/settings.py:369` [entero]

- Original: `or not 1 <= len(producto) <= LARGO_MAXIMO_PRODUCTO`
- Mutado:   `or not 2 <= len(producto) <= LARGO_MAXIMO_PRODUCTO`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: no había ningún producto de un solo carácter válido, solo el vacío (rechazado) y el de 24.
> Decisión: test nuevo, el caso `{"1:M": "MA99"}` en `test_f008_r54_forzada_valida_y_normalizada`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.

### 10. `config/settings.py:369` [comparacion]

- Original: `or not 1 <= len(producto) <= LARGO_MAXIMO_PRODUCTO`
- Mutado:   `or not 1 < len(producto) <= LARGO_MAXIMO_PRODUCTO`

#### Análisis (T32, medido)

> Por qué ningún test lo caza: mismo motivo que el 9.
> Decisión: lo mata el mismo caso `1:M`. Medido: con el mutante aplicado a mano, el test nuevo falla (`pytest` exit 1); con el original, en verde.


## Verificación de los supervivientes (T32)

Cada uno de los 10 mutantes se aplicó a mano sobre el fuente (con el original guardado en
memoria y restaurado en un `finally`; `git status` de los fuentes, limpio al terminar), y se
ejecutaron `tests/test_f008_settings.py`, `tests/test_f008_naturaleza_albaran.py` y
`tests/test_f008_use_case.py`. Resultado: **los 10, `exit 1`, cada uno lo caza su test nuevo**.
Ningún mutante se acepta como equivalente: los 10 eran huecos reales. Resultado final:
104 generados, 104 muertos.
