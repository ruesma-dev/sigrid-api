<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003 --workers 8` el 2026-09-04 00:53.

## Alcance

Origen del diff: **rama** (`f1946d928f8fadd346e1c4dd14370dd7606b9cb2` .. `feature/F-003-guardia-bases-cruzadas`).

| Fichero | Líneas en alcance |
|---|---|
| `infrastructure/security/database_reference_guard.py` | 237 |
| `infrastructure/security/sql_query_guard.py` | 18 |
| `infrastructure/security/sql_write_guard.py` | 17 |
| `scripts/verificar_sql_ecosistema.py` | 241 |
| **Total** | **513** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 129 |
| Mutantes evaluados | 129 |
| Muertos | 105 |
| Supervivientes | 18 |
| Timeouts | 6 |
| Timeouts repasados en serie | 6 — 0 con veredicto tras el repaso, 6 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1377.1 s |
| SHA de HEAD medido | `495c8e9a55903ebbcf2627644d599cdd933d7112` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_0` | 46.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_1` | 45.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_2` | 47.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_3` | 48.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_4` | 47.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_5` | 45.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_6` | 47.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003__wsym56u/wk_7` | 46.1 |
| Media por mutante evaluado (s) | 10.7 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `infrastructure/security/database_reference_guard.py:88` [logico]

- Original: `if not sql or not sql.strip():`
- Mutado:   `if not sql and not sql.strip():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `infrastructure/security/database_reference_guard.py:104` [comparacion]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) >= 1 and not partes[-1]:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `infrastructure/security/database_reference_guard.py:104` [entero]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) > 2 and not partes[-1]:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `infrastructure/security/database_reference_guard.py:105` [entero]

- Original: `partes = partes[:-1]`
- Mutado:   `partes = partes[:-2]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `infrastructure/security/database_reference_guard.py:147` [logico]

- Original: `delimitado = (identificador.startswith("[") and identificador.endswith("]")) or (`
- Mutado:   `delimitado = (identificador.startswith("[") or identificador.endswith("]")) or (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `infrastructure/security/database_reference_guard.py:148` [logico]

- Original: `identificador.startswith('"') and identificador.endswith('"')`
- Mutado:   `identificador.startswith('"') or identificador.endswith('"')`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `infrastructure/security/database_reference_guard.py:179` [aritmetico]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice - 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `infrastructure/security/database_reference_guard.py:182` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "]":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `infrastructure/security/database_reference_guard.py:182` [aritmetico]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 1 < total and sql[fin - 1] == "]":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `infrastructure/security/database_reference_guard.py:182` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 1 < total and sql[fin + 2] == "]":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `infrastructure/security/database_reference_guard.py:183` [entero]

- Original: `fin += 2`
- Mutado:   `fin += 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `infrastructure/security/database_reference_guard.py:201` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "'":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `infrastructure/security/database_reference_guard.py:201` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 1 < total and sql[fin + 2] == "'":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `infrastructure/security/database_reference_guard.py:224` [aritmetico]

- Original: `fin = sql.find("*/", indice + 2)`
- Mutado:   `fin = sql.find("*/", indice - 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `scripts/verificar_sql_ecosistema.py:40` [entero]

- Original: `sys.path.insert(0, str(RAIZ_PROYECTO))`
- Mutado:   `sys.path.insert(1, str(RAIZ_PROYECTO))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `scripts/verificar_sql_ecosistema.py:140` [booleano]

- Original: `return False, []`
- Mutado:   `return True, []`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `scripts/verificar_sql_ecosistema.py:219` [entero]

- Original: `recorte = sql if args.detalle else " ".join(sql.split())[:150]`
- Mutado:   `recorte = sql if args.detalle else " ".join(sql.split())[:151]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `scripts/verificar_sql_ecosistema.py:224` [entero]

- Original: `print("-" * 78)`
- Mutado:   `print("-" * 79)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

## Timeouts

Estos agotaron el reloj **también al repasarlos en serie**, uno a uno y sin nadie compitiendo por la máquina: la contención ya no los explica. Míralos como un cuelgue de verdad, no como ruido.

- `infrastructure/security/database_reference_guard.py:183` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:186` [aritmetico] fin += 1 -> fin -= 1
- `infrastructure/security/database_reference_guard.py:202` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:217` [comparacion] if fin == -1: -> if fin != -1:
- `infrastructure/security/database_reference_guard.py:217` [entero] if fin == -1: -> if fin == -2:
- `infrastructure/security/database_reference_guard.py:225` [entero] if fin == -1: -> if fin == -2:

