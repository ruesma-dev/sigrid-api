<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003 --workers 8` el 2026-09-05 00:01.

## Alcance

Origen del diff: **rama** (`f1946d928f8fadd346e1c4dd14370dd7606b9cb2` .. `feature/F-003-guardia-bases-cruzadas`).

| Fichero | Líneas en alcance |
|---|---|
| `infrastructure/security/database_reference_guard.py` | 277 |
| `infrastructure/security/sql_query_guard.py` | 18 |
| `infrastructure/security/sql_write_guard.py` | 17 |
| `scripts/verificar_sql_ecosistema.py` | 241 |
| **Total** | **553** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 132 |
| Mutantes evaluados | 132 |
| Muertos | 118 |
| Supervivientes | 7 |
| Timeouts | 7 |
| Timeouts repasados en serie | 7 — 0 con veredicto tras el repaso, 7 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1724.0 s |
| SHA de HEAD medido | `04a511113d69e779251e65f1de91c294dbd39d58` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_0` | 70.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_1` | 70.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_2` | 68.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_3` | 68.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_4` | 72.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_5` | 69.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_6` | 69.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_4slf4hr4/wk_7` | 73.5 |
| Media por mutante evaluado (s) | 13.1 |
| Timeout efectivo por mutante (s) | 147 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

> ### ✅ Los mismos 7, aceptados por el humano el 2026-09-04
>
> Esta campaña corre sobre el código **final**, con el neutralizador de
> delimitados ya unificado (pasada 3). Devuelve **exactamente los mismos siete
> supervivientes** que la anterior: ninguno nuevo, ninguno menos. La aceptación
> del humano sigue valiendo tal cual, y su verificación también: el reviewer los
> reprodujo uno a uno en la pasada 2 midiendo **0 diferencias en 4.050 entradas**
> cada uno.
>
> **Nota sobre una aceptación anterior, anulada.** El 2026-09-04 se aceptaron
> primero **13**, y esa aceptación quedó ANULADA: la pasada 2 demostró que
> cuatro de aquellos análisis eran falsos —no eran equivalentes, hacían fallar
> el guardia ABIERTO y eran matables con un test de una línea—, así que se había
> pedido sobre hechos que no eran. Los cuatro están muertos, y otros dos
> desaparecieron al corregir el reconocedor.
>
> Recorrido: **52 → 18 → 13 → 10 → 7 → 7**.

### 1. `infrastructure/security/database_reference_guard.py:105` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `infrastructure/security/database_reference_guard.py:133` [comparacion]

- Original: `len(partes) > 1`
- Mutado:   `len(partes) >= 1`

#### Análisis

> **Por qué ningún test lo caza:** `partes` nunca tiene menos de dos
> elementos, porque la expresión regular exige al menos un punto para formar
> una cadena cualificada. Con `len >= 2` garantizado, `> 1` y `>= 1` son la
> misma condición. **Decisión: EQUIVALENTE por construcción.** Confirmado por
> el reviewer en la pasada 2: 0 diferencias en 4.050 entradas.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 3. `infrastructure/security/database_reference_guard.py:133` [entero]

- Original: `len(partes) > 1`
- Mutado:   `len(partes) > 2`

#### Análisis

> **Por qué ningún test lo caza:** solo difieren cuando hay exactamente dos
> partes y la última está vacía (`dbo.`). Con `> 1` se descarta la vacía y queda
> una parte; con `> 2` no se descarta y quedan dos. **Ambos caminos terminan en
> `len(partes) <= 2`**, es decir, en «esto no nombra una base».
> **Decisión: EQUIVALENTE.** Confirmado por el reviewer en la pasada 2: 0
> diferencias en 4.050 entradas.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 4. `infrastructure/security/database_reference_guard.py:179` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 5. `infrastructure/security/database_reference_guard.py:180` [logico]

- Original: `identificador.startswith('"') and identificador.endswith('"')`
- Mutado:   `identificador.startswith('"') or identificador.endswith('"')`

#### Análisis

> **Por qué ningún test lo caza:** idéntico al anterior, con comillas dobles
> en vez de corchetes: `"[^"

]*"` también está balanceado por construcción.
> **Decisión: EQUIVALENTE por construcción.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 6. `infrastructure/security/database_reference_guard.py:241` [entero]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 7. `scripts/verificar_sql_ecosistema.py:40` [entero]

- Original: `sys.path.insert(0, str(RAIZ_PROYECTO))`
- Mutado:   `sys.path.insert(1, str(RAIZ_PROYECTO))`

#### Análisis

> **Por qué ningún test lo caza:** no es lógica del guardia, sino la línea que
> permite al script importar el proyecto cuando se ejecuta suelto. Insertar la
> raíz en la posición 1 en vez de la 0 solo cambiaría algo si el primer
> elemento de `sys.path` contuviera otro paquete llamado igual, y durante los
> tests el proyecto ya está importado. **Decisión: EQUIVALENTE.**

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

## Timeouts

Estos agotaron el reloj **también al repasarlos en serie**, uno a uno y sin nadie compitiendo por la máquina: la contención ya no los explica. Míralos como un cuelgue de verdad, no como ruido.

- `infrastructure/security/database_reference_guard.py:218` [aritmetico] fin = indice + 1 -> fin = indice - 1
- `infrastructure/security/database_reference_guard.py:222` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:225` [aritmetico] fin += 1 -> fin -= 1
- `infrastructure/security/database_reference_guard.py:242` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:257` [comparacion] if fin == -1: -> if fin != -1:
- `infrastructure/security/database_reference_guard.py:257` [entero] if fin == -1: -> if fin == -2:
- `infrastructure/security/database_reference_guard.py:265` [entero] if fin == -1: -> if fin == -2:

