<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003 --workers 8` el 2026-09-04 11:14.

## Alcance

Origen del diff: **rama** (`f1946d928f8fadd346e1c4dd14370dd7606b9cb2` .. `feature/F-003-guardia-bases-cruzadas`).

| Fichero | Líneas en alcance |
|---|---|
| `infrastructure/security/database_reference_guard.py` | 246 |
| `infrastructure/security/sql_query_guard.py` | 18 |
| `infrastructure/security/sql_write_guard.py` | 17 |
| `scripts/verificar_sql_ecosistema.py` | 241 |
| **Total** | **522** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 132 |
| Mutantes evaluados | 132 |
| Muertos | 116 |
| Supervivientes | 10 |
| Timeouts | 5 |
| Timeouts repasados en serie | 6 — 1 con veredicto tras el repaso, 5 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2340.8 s |
| SHA de HEAD medido | `41357abd74252517319d59676d1b7f5a21fa39e8` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_0` | 52.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_1` | 54.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_2` | 54.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_3` | 50.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_4` | 51.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_5` | 51.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_6` | 52.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_f13a4z_i/wk_7` | 51.5 |
| Media por mutante evaluado (s) | 17.7 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `infrastructure/security/database_reference_guard.py:88` [logico]

- Original: `if not sql or not sql.strip():`
- Mutado:   `if not sql and not sql.strip():`

#### Análisis

> **Por qué ningún test lo caza:** es una guarda de atajo, no de corrección.
> Con `and`, un SQL en blanco (`"   "`) deja de cortarse ahí y sigue al
> análisis normal, que lo neutraliza, no encuentra ninguna cadena cualificada y
> devuelve lo mismo: nada. Los dos caminos coinciden para toda entrada vacía o
> en blanco, y `test_f003_r5_un_sql_vacio_o_en_blanco_no_rompe` los recorre.
> **Decisión: EQUIVALENTE.** Matarlo exigiría un test que compruebe *por qué
> ruta* se llegó al resultado, que es acoplarse al interior.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `infrastructure/security/database_reference_guard.py:112` [comparacion]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) >= 1 and not partes[-1]:`

#### Análisis

> **Por qué ningún test lo caza:** `partes` nunca tiene menos de dos
> elementos. La expresión regular exige al menos un punto para formar una
> cadena cualificada, así que `_partir` siempre devuelve dos o más. Con
> `len >= 2` garantizado, `> 1` y `>= 1` son la misma condición.
> **Decisión: EQUIVALENTE por construcción.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 3. `infrastructure/security/database_reference_guard.py:112` [entero]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) > 2 and not partes[-1]:`

#### Análisis

> **Por qué ningún test lo caza:** solo difieren cuando hay exactamente dos
> partes y la última está vacía (`dbo.`). Con `> 1` se descarta la vacía y
> queda una parte; con `> 2` no se descarta y quedan dos. **Ambos caminos
> terminan en `len(partes) <= 2`, es decir, en «esto no nombra una base».**
> **Decisión: EQUIVALENTE**, los dos desembocan en la misma rama.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 4. `infrastructure/security/database_reference_guard.py:112` [logico]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) > 1 or not partes[-1]:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `infrastructure/security/database_reference_guard.py:156` [logico]

- Original: `delimitado = (identificador.startswith("[") and identificador.endswith("]")) or (`
- Mutado:   `delimitado = (identificador.startswith("[") or identificador.endswith("]")) or (`

#### Análisis

> **Por qué ningún test lo caza:** los identificadores que llegan aquí salen
> de `_IDENT`, que solo casa delimitadores **balanceados** (`\[[^\]]*\]`).
> Un identificador que empiece por `[` termina por `]` siempre, así que
> «empieza Y termina» y «empieza O termina» valen lo mismo para toda entrada
> alcanzable. **Decisión: EQUIVALENTE por construcción.** Para matarlo haría
> falta llamar al método privado con una entrada que la regex nunca produce.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 6. `infrastructure/security/database_reference_guard.py:157` [logico]

- Original: `identificador.startswith('"') and identificador.endswith('"')`
- Mutado:   `identificador.startswith('"') or identificador.endswith('"')`

#### Análisis

> **Por qué ningún test lo caza:** idéntico al anterior, con comillas dobles
> en vez de corchetes: `"[^"

]*"` también está balanceado por construcción.
> **Decisión: EQUIVALENTE por construcción.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 7. `infrastructure/security/database_reference_guard.py:188` [aritmetico]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice - 1`

#### Análisis

> **Por qué ningún test lo caza:** empieza a buscar el `]` de cierre una
> posición antes del `[`. El bucle avanza igual y encuentra el mismo cierre,
> salvo que el carácter justo anterior al `[` sea otro `]`, es decir, dos
> identificadores delimitados pegados sin nada en medio (`[a][b]`), que no es
> T-SQL válido: entre dos identificadores va siempre un punto, una coma o un
> espacio. **Decisión: EQUIVALENTE para toda entrada que el motor aceptaría.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 8. `infrastructure/security/database_reference_guard.py:192` [entero]

- Original: `fin += 2`
- Mutado:   `fin += 3`

#### Análisis

> **Por qué ningún test lo caza:** salta un carácter de más tras un escape
> `]]`. Dentro de un identificador delimitado el contenido se copia tal cual y
> no se analiza, así que adelantar de más solo puede terminar el identificador
> antes; el texto sobrante vuelve al análisis general, donde no forma ninguna
> cadena cualificada nueva. **Decisión: EQUIVALENTE en el resultado
> observable.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 9. `infrastructure/security/database_reference_guard.py:210` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "'":`

#### Análisis

> **Por qué ningún test lo caza:** mismo caso que el `]]` pero con el `''` de
> los literales, y en el borde final de la cadena, donde una comilla suelta no
> puede ser un escape. Su gemelo —el que mueve el índice en vez del límite— sí
> murió, con
> `test_f003_r11_una_comilla_escapada_no_cierra_el_literal_antes_de_tiempo`.
> **Decisión: EQUIVALENTE.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 10. `scripts/verificar_sql_ecosistema.py:40` [entero]

- Original: `sys.path.insert(0, str(RAIZ_PROYECTO))`
- Mutado:   `sys.path.insert(1, str(RAIZ_PROYECTO))`

#### Análisis

> **Por qué ningún test lo caza:** no es lógica del guardia, sino la línea que
> permite al script importar el proyecto cuando se ejecuta suelto. Insertar la
> raíz en la posición 1 en vez de la 0 solo cambiaría algo si el primer
> elemento de `sys.path` contuviera otro paquete llamado igual, y durante los
> tests el proyecto ya está importado. **Decisión: EQUIVALENTE.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

## Timeouts

Estos agotaron el reloj **también al repasarlos en serie**, uno a uno y sin nadie compitiendo por la máquina: la contención ya no los explica. Míralos como un cuelgue de verdad, no como ruido.

- `infrastructure/security/database_reference_guard.py:195` [aritmetico] fin += 1 -> fin -= 1
- `infrastructure/security/database_reference_guard.py:211` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:226` [comparacion] if fin == -1: -> if fin != -1:
- `infrastructure/security/database_reference_guard.py:226` [entero] if fin == -1: -> if fin == -2:
- `infrastructure/security/database_reference_guard.py:234` [entero] if fin == -1: -> if fin == -2:

