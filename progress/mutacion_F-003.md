<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003 --workers 8` el 2026-09-04 01:42.

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
| Muertos | 110 |
| Supervivientes | 13 |
| Timeouts | 6 |
| Timeouts repasados en serie | 6 — 0 con veredicto tras el repaso, 6 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1363.6 s |
| SHA de HEAD medido | `539f1f63ecfb823cd8160f7afc5baf8d4e40ae8a` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_0` | 51.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_1` | 51.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_2` | 53.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_3` | 52.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_4` | 53.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_5` | 53.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_6` | 52.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_gzfo6lub/wk_7` | 54.6 |
| Media por mutante evaluado (s) | 10.6 |
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

### 2. `infrastructure/security/database_reference_guard.py:104` [comparacion]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) >= 1 and not partes[-1]:`

#### Análisis

> **Por qué ningún test lo caza:** `partes` nunca tiene menos de dos
> elementos. La expresión regular exige al menos un punto para formar una
> cadena cualificada, así que `_partir` siempre devuelve dos o más. Con
> `len >= 2` garantizado, `> 1` y `>= 1` son la misma condición.
> **Decisión: EQUIVALENTE por construcción.**

### 3. `infrastructure/security/database_reference_guard.py:104` [entero]

- Original: `if len(partes) > 1 and not partes[-1]:`
- Mutado:   `if len(partes) > 2 and not partes[-1]:`

#### Análisis

> **Por qué ningún test lo caza:** solo difieren cuando hay exactamente dos
> partes y la última está vacía (`dbo.`). Con `> 1` se descarta la vacía y
> queda una parte; con `> 2` no se descarta y quedan dos. **Ambos caminos
> terminan en `len(partes) <= 2`, es decir, en «esto no nombra una base».**
> **Decisión: EQUIVALENTE**, los dos desembocan en la misma rama.

### 4. `infrastructure/security/database_reference_guard.py:147` [logico]

- Original: `delimitado = (identificador.startswith("[") and identificador.endswith("]")) or (`
- Mutado:   `delimitado = (identificador.startswith("[") or identificador.endswith("]")) or (`

#### Análisis

> **Por qué ningún test lo caza:** los identificadores que llegan aquí salen
> de `_IDENT`, que solo casa delimitadores **balanceados** (`\[[^\]]*\]`).
> Un identificador que empiece por `[` termina por `]` siempre, así que
> «empieza Y termina» y «empieza O termina» valen lo mismo para toda entrada
> alcanzable. **Decisión: EQUIVALENTE por construcción.** Para matarlo haría
> falta llamar al método privado con una entrada que la regex nunca produce.

### 5. `infrastructure/security/database_reference_guard.py:148` [logico]

- Original: `identificador.startswith('"') and identificador.endswith('"')`
- Mutado:   `identificador.startswith('"') or identificador.endswith('"')`

#### Análisis

> **Por qué ningún test lo caza:** idéntico al anterior, con comillas dobles
> en vez de corchetes: `"[^"
]*"` también está balanceado por construcción.
> **Decisión: EQUIVALENTE por construcción.**

### 6. `infrastructure/security/database_reference_guard.py:179` [aritmetico]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice - 1`

#### Análisis

> **Por qué ningún test lo caza:** empieza a buscar el `]` de cierre una
> posición antes del `[`. El bucle avanza igual y encuentra el mismo cierre,
> salvo que el carácter justo anterior al `[` sea otro `]`, es decir, dos
> identificadores delimitados pegados sin nada en medio (`[a][b]`), que no es
> T-SQL válido: entre dos identificadores va siempre un punto, una coma o un
> espacio. **Decisión: EQUIVALENTE para toda entrada que el motor aceptaría.**

### 7. `infrastructure/security/database_reference_guard.py:182` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "]":`

#### Análisis

> **Por qué ningún test lo caza:** mueve el límite del `and` en vez del
> índice, y solo cambia el comportamiento en el último carácter de la cadena,
> donde un `]` final no puede formar un escape porque no hay nada detrás.
> **Decisión: EQUIVALENTE.**

### 8. `infrastructure/security/database_reference_guard.py:182` [aritmetico]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 1 < total and sql[fin - 1] == "]":`

#### Análisis

> **Por qué ningún test lo caza:** mira el carácter anterior en vez del
> siguiente para decidir si hay escape. Un `]` inmediatamente antes del cierre
> significa que ya se procesó como parte del identificador, así que la decisión
> resultante coincide en toda entrada balanceada.
> **Decisión: EQUIVALENTE en el resultado observable**, y cubierto por el test
> de propiedad.

### 9. `infrastructure/security/database_reference_guard.py:182` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "]":`
- Mutado:   `if fin + 1 < total and sql[fin + 2] == "]":`

#### Análisis

> **Por qué ningún test lo caza:** afecta al escape `]]` dentro de un
> identificador. Si el escape no se reconoce, el identificador cierra antes y
> el resto se vuelve a analizar; como los corchetes están balanceados, las
> zonas que quedan protegidas son las mismas y el conjunto de bases detectadas
> no cambia. Lo comprueban
> `test_f003_r3_el_corchete_de_cierre_escapado_no_confunde` y el test de
> propiedad, que incluye `[raro]]nombre]` entre sus contextos.
> **Decisión: EQUIVALENTE en el resultado observable.**

### 10. `infrastructure/security/database_reference_guard.py:183` [entero]

- Original: `fin += 2`
- Mutado:   `fin += 3`

#### Análisis

> **Por qué ningún test lo caza:** salta un carácter de más tras un escape
> `]]`. Dentro de un identificador delimitado el contenido se copia tal cual y
> no se analiza, así que adelantar de más solo puede terminar el identificador
> antes; el texto sobrante vuelve al análisis general, donde no forma ninguna
> cadena cualificada nueva. **Decisión: EQUIVALENTE en el resultado
> observable.**

### 11. `infrastructure/security/database_reference_guard.py:201` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == "'":`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == "'":`

#### Análisis

> **Por qué ningún test lo caza:** mismo caso que el `]]` pero con el `''` de
> los literales, y en el borde final de la cadena, donde una comilla suelta no
> puede ser un escape. Su gemelo —el que mueve el índice en vez del límite— sí
> murió, con
> `test_f003_r11_una_comilla_escapada_no_cierra_el_literal_antes_de_tiempo`.
> **Decisión: EQUIVALENTE.**

### 12. `infrastructure/security/database_reference_guard.py:224` [aritmetico]

- Original: `fin = sql.find("*/", indice + 2)`
- Mutado:   `fin = sql.find("*/", indice - 2)`

#### Análisis

> **Por qué ningún test lo caza:** busca el `*/` de cierre dos posiciones
> antes de donde debería. Como la búsqueda arranca antes de la apertura `/*`,
> encuentra el mismo cierre salvo que hubiera un `*/` pegado justo delante, lo
> que exige un comentario cerrado inmediatamente antes y sin separación
> (`*//*...*/`). Ni el ecosistema ni el generador de la API producen eso.
> **Decisión: EQUIVALENTE para toda entrada realista**, anotado como el más
> débil de los trece.

### 13. `scripts/verificar_sql_ecosistema.py:40` [entero]

- Original: `sys.path.insert(0, str(RAIZ_PROYECTO))`
- Mutado:   `sys.path.insert(1, str(RAIZ_PROYECTO))`

#### Análisis

> **Por qué ningún test lo caza:** no es lógica del guardia, sino la línea que
> permite al script importar el proyecto cuando se ejecuta suelto. Insertar la
> raíz en la posición 1 en vez de la 0 solo cambiaría algo si el primer
> elemento de `sys.path` contuviera otro paquete llamado igual, y durante los
> tests el proyecto ya está importado. **Decisión: EQUIVALENTE.**

## Timeouts

Estos agotaron el reloj **también al repasarlos en serie**, uno a uno y sin nadie compitiendo por la máquina: la contención ya no los explica. Míralos como un cuelgue de verdad, no como ruido.

- `infrastructure/security/database_reference_guard.py:183` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:186` [aritmetico] fin += 1 -> fin -= 1
- `infrastructure/security/database_reference_guard.py:202` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:217` [comparacion] if fin == -1: -> if fin != -1:
- `infrastructure/security/database_reference_guard.py:217` [entero] if fin == -1: -> if fin == -2:
- `infrastructure/security/database_reference_guard.py:225` [entero] if fin == -1: -> if fin == -2:

