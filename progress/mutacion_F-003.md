<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003 --workers 8` el 2026-09-04 00:26.

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
| Muertos | 73 |
| Supervivientes | 52 |
| Timeouts | 4 |
| Timeouts repasados en serie | 4 — 0 con veredicto tras el repaso, 4 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1278.0 s |
| SHA de HEAD medido | `ff83893a908f74ca33e0825ff4831615619bc51a` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_0` | 50.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_1` | 47.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_2` | 47.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_3` | 47.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_4` | 46.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_5` | 46.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_6` | 46.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_ajl9yktq/wk_7` | 46.1 |
| Media por mutante evaluado (s) | 9.9 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `infrastructure/security/database_reference_guard.py:74` [logico]

- Original: `permitidas = {base.strip().lower() for base in allowed if base and base.strip()}`
- Mutado:   `permitidas = {base.strip().lower() for base in allowed if base or base.strip()}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `infrastructure/security/database_reference_guard.py:80` [logico]

- Original: `f"{', '.join(sorted(permitidas)) or '(ninguna)'}"`
- Mutado:   `f"{', '.join(sorted(permitidas)) and '(ninguna)'}"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `infrastructure/security/database_reference_guard.py:88` [logico]

- Original: `if not sql or not sql.strip():`
- Mutado:   `if not sql and not sql.strip():`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `infrastructure/security/database_reference_guard.py:104` [comparacion]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) >= 1 and not partes[-1]:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `infrastructure/security/database_reference_guard.py:104` [entero]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) > 2 and not partes[-1]:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `infrastructure/security/database_reference_guard.py:105` [entero]

- Original: `partes = partes[:-1]`
- Mutado:   `partes = partes[:-2]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `infrastructure/security/database_reference_guard.py:147` [logico]

- Original: `delimitado = (identificador.startswith("[") and identificador.endswith("]")) or (`
- Mutado:   `delimitado = (identificador.startswith("[") or identificador.endswith("]")) or (`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `infrastructure/security/database_reference_guard.py:148` [logico]

- Original: `identificador.startswith('"') and identificador.endswith('"')`
- Mutado:   `identificador.startswith('"') or identificador.endswith('"')`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `infrastructure/security/database_reference_guard.py:166` [entero]

- Original: `indice = 0`
- Mutado:   `indice = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `infrastructure/security/database_reference_guard.py:179` [aritmetico]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice - 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `infrastructure/security/database_reference_guard.py:179` [entero]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice + 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `infrastructure/security/database_reference_guard.py:182` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "]":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `infrastructure/security/database_reference_guard.py:182` [aritmetico]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 1 < total and sql[fin - 1] == "]":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `infrastructure/security/database_reference_guard.py:182` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 1 < total and sql[fin + 2] == "]":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `infrastructure/security/database_reference_guard.py:183` [entero]

- Original: `fin += 2`
- Mutado:   `fin += 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `infrastructure/security/database_reference_guard.py:197` [entero]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice + 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `infrastructure/security/database_reference_guard.py:201` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "'":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `infrastructure/security/database_reference_guard.py:201` [aritmetico]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 1 < total and sql[fin - 1] == "'":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `infrastructure/security/database_reference_guard.py:201` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 1 < total and sql[fin + 2] == "'":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `infrastructure/security/database_reference_guard.py:202` [entero]

- Original: `fin += 2`
- Mutado:   `fin += 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `infrastructure/security/database_reference_guard.py:211` [aritmetico]

- Original: `salida.append(" " * (fin - indice + 1))`
- Mutado:   `salida.append(" " * (fin + indice + 1))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `infrastructure/security/database_reference_guard.py:211` [aritmetico]

- Original: `salida.append(" " * (fin - indice + 1))`
- Mutado:   `salida.append(" " * (fin - indice - 1))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `infrastructure/security/database_reference_guard.py:211` [entero]

- Original: `salida.append(" " * (fin - indice + 1))`
- Mutado:   `salida.append(" " * (fin - indice + 2))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `infrastructure/security/database_reference_guard.py:212` [entero]

- Original: `indice = fin + 1`
- Mutado:   `indice = fin + 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `infrastructure/security/database_reference_guard.py:217` [comparacion]

- Original: `if fin == -1:`
- Mutado:   `if fin != -1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `infrastructure/security/database_reference_guard.py:217` [entero]

- Original: `if fin == -1:`
- Mutado:   `if fin == -2:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `infrastructure/security/database_reference_guard.py:219` [aritmetico]

- Original: `salida.append(" " * (fin - indice))`
- Mutado:   `salida.append(" " * (fin + indice))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `infrastructure/security/database_reference_guard.py:224` [aritmetico]

- Original: `fin = sql.find("*/", indice + 2)`
- Mutado:   `fin = sql.find("*/", indice - 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `infrastructure/security/database_reference_guard.py:224` [entero]

- Original: `fin = sql.find("*/", indice + 2)`
- Mutado:   `fin = sql.find("*/", indice + 3)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `infrastructure/security/database_reference_guard.py:230` [aritmetico]

- Original: `salida.append(" " * (fin + 2 - indice))`
- Mutado:   `salida.append(" " * (fin - 2 - indice))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `infrastructure/security/database_reference_guard.py:230` [entero]

- Original: `salida.append(" " * (fin + 2 - indice))`
- Mutado:   `salida.append(" " * (fin + 3 - indice))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `infrastructure/security/database_reference_guard.py:230` [aritmetico]

- Original: `salida.append(" " * (fin + 2 - indice))`
- Mutado:   `salida.append(" " * (fin + 2 + indice))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `infrastructure/security/database_reference_guard.py:231` [aritmetico]

- Original: `indice = fin + 2`
- Mutado:   `indice = fin - 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `infrastructure/security/database_reference_guard.py:231` [entero]

- Original: `indice = fin + 2`
- Mutado:   `indice = fin + 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `scripts/verificar_sql_ecosistema.py:40` [entero]

- Original: `sys.path.insert(0, str(RAIZ_PROYECTO))`
- Mutado:   `sys.path.insert(1, str(RAIZ_PROYECTO))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `scripts/verificar_sql_ecosistema.py:116` [comparacion]

- Original: `if len(cadena) < 20 or not PARECE_SQL.search(cadena):`
- Mutado:   `if len(cadena) <= 20 or not PARECE_SQL.search(cadena):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `scripts/verificar_sql_ecosistema.py:116` [entero]

- Original: `if len(cadena) < 20 or not PARECE_SQL.search(cadena):`
- Mutado:   `if len(cadena) < 21 or not PARECE_SQL.search(cadena):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `scripts/verificar_sql_ecosistema.py:140` [booleano]

- Original: `return False, []`
- Mutado:   `return True, []`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `scripts/verificar_sql_ecosistema.py:195` [entero]

- Original: `print("=" * 78)`
- Mutado:   `print("=" * 79)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `scripts/verificar_sql_ecosistema.py:197` [entero]

- Original: `print("=" * 78)`
- Mutado:   `print("=" * 79)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `scripts/verificar_sql_ecosistema.py:204` [entero]

- Original: `ficheros = 0`
- Mutado:   `ficheros = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `scripts/verificar_sql_ecosistema.py:205` [entero]

- Original: `consumidores = 0`
- Mutado:   `consumidores = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `scripts/verificar_sql_ecosistema.py:206` [entero]

- Original: `con_sql = 0`
- Mutado:   `con_sql = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `scripts/verificar_sql_ecosistema.py:210` [aritmetico]

- Original: `ficheros += 1`
- Mutado:   `ficheros -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `scripts/verificar_sql_ecosistema.py:210` [entero]

- Original: `ficheros += 1`
- Mutado:   `ficheros += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `scripts/verificar_sql_ecosistema.py:213` [aritmetico]

- Original: `consumidores += 1`
- Mutado:   `consumidores -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `scripts/verificar_sql_ecosistema.py:213` [entero]

- Original: `consumidores += 1`
- Mutado:   `consumidores += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `scripts/verificar_sql_ecosistema.py:215` [aritmetico]

- Original: `con_sql += 1`
- Mutado:   `con_sql -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `scripts/verificar_sql_ecosistema.py:215` [entero]

- Original: `con_sql += 1`
- Mutado:   `con_sql += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `scripts/verificar_sql_ecosistema.py:216` [aritmetico]

- Original: `rechazos_totales += len(rechazos)`
- Mutado:   `rechazos_totales -= len(rechazos)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `scripts/verificar_sql_ecosistema.py:219` [entero]

- Original: `recorte = sql if args.detalle else " ".join(sql.split())[:150]`
- Mutado:   `recorte = sql if args.detalle else " ".join(sql.split())[:151]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `scripts/verificar_sql_ecosistema.py:224` [entero]

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
- `infrastructure/security/database_reference_guard.py:225` [entero] if fin == -1: -> if fin == -2:

