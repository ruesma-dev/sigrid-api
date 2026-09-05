<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003 --workers 8` el 2026-09-05 11:39.

## Alcance

Origen del diff: **rama** (`f1946d928f8fadd346e1c4dd14370dd7606b9cb2` .. `feature/F-003-guardia-bases-cruzadas`).

| Fichero | Líneas en alcance |
|---|---|
| `infrastructure/security/database_reference_guard.py` | 331 |
| `infrastructure/security/sql_query_guard.py` | 18 |
| `infrastructure/security/sql_write_guard.py` | 17 |
| `scripts/verificar_sql_ecosistema.py` | 241 |
| **Total** | **607** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 138 |
| Mutantes evaluados | 138 |
| Muertos | 123 |
| Supervivientes | 9 |
| Timeouts | 6 |
| Timeouts repasados en serie | 6 — 0 con veredicto tras el repaso, 6 en timeout todavía |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1681.8 s |
| SHA de HEAD medido | `e1ac0ddd3c75dc2aa8e472238efbbc913dfad8a2` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_0` | 86.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_1` | 82.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_2` | 88.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_3` | 80.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_4` | 84.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_5` | 81.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_6` | 84.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-003_j6x8obg3/wk_7` | 81.5 |
| Media por mutante evaluado (s) | 12.2 |
| Timeout efectivo por mutante (s) | 177 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

> **CORRECCIÓN MEDIDA, posterior a la campaña.** Estos totales son los que
> publicó la campaña paralela y se dejan tal cual, sin retocar, porque son el
> dato crudo de la herramienta. Pero **dos de los 9 supervivientes están mal
> clasificados**, y se ha comprobado ejecutándolos, no leyéndolos: el de la
> línea 263 **se cuelga** (su sitio es la lista de timeouts) y el de la 266
> **muere en 1,9 s**. El recuento real es, por tanto, **124 muertos, 7
> supervivientes y 7 timeouts**. Los 7 supervivientes reales son los que el
> humano aceptó el 2026-09-04.
>
> No es un fallo del guardia ni un hueco de tests: es un fallo de la campaña
> paralela, y su sesgo es **pesimista** —inventa supervivientes, no los
> esconde—. Se reevaluaron **en serie los 138 mutantes seleccionados, incluidos
> los 123 muertos**, y salieron **0 falsos muertos**: ningún muerto de la
> campaña sobrevive sin contención, así que ninguna línea del guardia queda sin
> test por culpa de esto. La medición está en
> [`mutacion_F-003_remuestreo.md`](mutacion_F-003_remuestreo.md), y el
> diagnóstico de `harness/mutacion_paralela.py` queda abierto como trabajo
> aparte, para portarlo luego a `arnes-base`.

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `infrastructure/security/database_reference_guard.py:137` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `infrastructure/security/database_reference_guard.py:166` [comparacion]

- Original: `len(partes) > 1`
- Mutado:   `len(partes) >= 1`

#### Análisis

> **Por qué ningún test lo caza:** `partes` nunca tiene menos de dos
> elementos, porque la expresión regular exige al menos un punto para formar
> una cadena cualificada. Con `len >= 2` garantizado, `> 1` y `>= 1` son la
> misma condición. **Decisión: EQUIVALENTE por construcción.** Confirmado por
> el reviewer en la pasada 2: 0 diferencias en 4.050 entradas.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 3. `infrastructure/security/database_reference_guard.py:166` [entero]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 4. `infrastructure/security/database_reference_guard.py:224` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 5. `infrastructure/security/database_reference_guard.py:225` [logico]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 6. `infrastructure/security/database_reference_guard.py:263` [aritmetico]

- Original: `fin = indice + 1`
- Mutado:   `fin = indice - 1`

#### Análisis

> **Medido, no leído.** Mutante aplicado de verdad en un `git worktree`
> desechable creado desde `e1ac0dd` (el árbol principal no se tocó; retirado
> con `git worktree remove` y comprobado con `git status --porcelain`).
>
> **1) La suite con el mutante puesto NO termina.**
> `python -m pytest -q -p no:cacheprovider` → `EXIT=124` (matado a los 420 s),
> parado en el 62 %; la línea base del mismo worktree tarda **52,95 s**
> (`1262 passed, 1 skipped`). Repetido con `-v` para ver dónde se queda:
> `test_f003_r11_dos_identificadores_delimitados_pegados_no_cuelgan` entra y no
> sale. Repetido con los argumentos EXACTOS de la campaña
> (`pytest -x -q --tb=no -p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`):
> `EXIT=124` a los 200 s, por encima del timeout efectivo de 177 s.
>
> **Este mutante no sobrevive: se cuelga.** `fin = indice - 1` hace que ante dos
> delimitados pegados (`[a][b]`) el `]` anterior se lea como cierre: `salida`
> recibe la cadena vacía e `indice` vuelve a su sitio, y el bucle no avanza
> nunca. Un guardia que se cuelga es una denegación de servicio con la function
> key, que es justo lo que ese test vigila. **Su sitio es la lista de timeouts**,
> con sus hermanos de las líneas 267 y 270; que la campaña lo listara como
> superviviente es una clasificación errónea de la campaña, no un hueco de
> tests.
>
> **2) Diferencial original vs. mutante, ejecutando los dos.** Corpus de
> **4.132 entradas** únicas: 280 cadenas sacadas por `ast` del fichero de tests
> de F-003, 381 sentencias reales del ecosistema (recolectadas con
> `extraer_sql()` de `scripts/verificar_sql_ecosistema.py` sobre
> `PycharmProjects/`), 1.990 generadas por producto cartesiano (25 contextos ×
> 60 piezas con delimitados `[`/`]`/`"` y sus escapes `]]`/`""`, literales
> `'…''…'`, comentarios `--` y `/* */`, y formas de 2, 3 y 4 partes; más 16
> prefijos × 25 colas que terminan en el delimitador doblado, y 9 bases × 10
> formas cualificadas) y 1.978 truncadas por el último carácter. A cada entrada
> se le comparan cuatro observaciones en las dos versiones:
> `extract_database_references`, `validate` de lectura, `validate` de escritura
> y `_neutralizar_literales_y_comentarios`, con presupuesto igual de 300.000
> eventos de línea (`sys.settrace`) para que un cuelgue se anote en vez de
> bloquear la medición.
> Comando: `python <scratchpad>/diferencial.py S6`.
>
> **Resultado: 619 diferencias sobre 4.132 entradas.** 133 en las que el mutante
> se cuelga; 75 en las que el original RECHAZA y el mutante ACEPTA; 167 al
> revés; 244 en las que ambos rechazan por motivo distinto. De esas 75, **17
> nombran una base prohibida que el mutante deja pasar**, entre ellas
> `SELECT 1 AS "z--", j.name FROM msdb.dbo.sysjobs j`: el original devuelve
> `['msdb']` y rechaza, el mutante devuelve `[]` y da vía libre porque blanquea
> el resto de la línea como si fuera comentario.
>
> **Es un séptimo caso de la familia conocida**: con el mutante, el
> neutralizador deja de leer el identificador delimitado por comillas con la
> misma regla que el reconocedor, y reabre exactamente el agujero de la pasada
> 3 (`"z--"` se traga la sentencia y `msdb` se cuela).
>
> **Decisión: NO EQUIVALENTE, y tampoco superviviente — está cazado (por
> cuelgue).** No hace falta ningún test nuevo: `..._dos_identificadores_
> delimitados_pegados_no_cuelgan` lo detiene y los de `"z--"` lo rematarían.
> Lo que sí hace falta es corregir el informe de la campaña, que lo cuenta
> entre los supervivientes cuando es un timeout.

### 7. `infrastructure/security/database_reference_guard.py:266` [entero]

- Original: `if fin + 1 < total and sql[fin + 1] == cierre:`
- Mutado:   `if fin + 2 < total and sql[fin + 1] == cierre:`

#### Análisis

> **Medido, no leído.** Mismo método que el 6: mutante aplicado de verdad en un
> `git worktree` desechable creado desde `e1ac0dd`, con el árbol principal
> intacto (`git status --porcelain` sin cambios de código al terminar).
>
> **1) La suite con el mutante puesto FALLA.**
> `python -m pytest -q -p no:cacheprovider` →
> `1 failed, 1261 passed, 1 skipped` en 38,05 s. El test que lo caza es
> `test_f003_r11_un_corchete_mal_cerrado_falla_cerrado[SELECT * FROM [gra]]]`.
> Repetido con los argumentos EXACTOS de la campaña
> (`pytest -x -q --tb=no -p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`):
> `EXIT=1`, `1 failed, 840 passed` en **1,53 s**.
>
> **Este mutante no sobrevive: está MUERTO**, y muere rápido y de forma
> determinista. Que la campaña lo listara como superviviente es, otra vez, una
> clasificación errónea del informe, no un hueco de tests.
>
> **2) Diferencial original vs. mutante**, con el mismo corpus de **4.132
> entradas** descrito en el análisis del superviviente 6 (misma generación,
> mismas cuatro observaciones por entrada, mismo presupuesto de 300.000 eventos
> de línea). Comando: `python <scratchpad>/diferencial.py S7`.
>
> **Resultado: 103 diferencias sobre 4.132 entradas.** 77 en las que el original
> RECHAZA y el mutante ACEPTA; 26 en las que ambos rechazan por motivo distinto.
> Ninguna en la que el mutante se cuelgue.
>
> El borde donde difieren es exactamente uno: que el delimitador doblado caiga
> en los **dos últimos caracteres** de la sentencia (`fin + 2 == total`). Ahí el
> original ve `]]` sin nada detrás, agota el bucle y aplica R11 —«identificador
> delimitado sin cerrar»—, y el mutante se lo salta, cierra en el primer `]` y
> se traga el segundo como carácter suelto. Ejemplo mínimo:
> `SELECT * FROM [gra]]` → original: `DatabaseReferenceError` («sin cerrar»);
> mutante: `[]` y validación en verde.
>
> **No es una fuga: 0 casos de los 4.132 en que el mutante deje pasar un SQL que
> nombre una base prohibida.** Cuando la sentencia sí nombra una
> (`SELECT * FROM msdb.dbo.t WHERE x = [a]]`), el mutante la rechaza igual, solo
> que por «`msdb` no permitida» en vez de por «sin cerrar». La diferencia es de
> severidad ante SQL que el motor tampoco aceptaría, y aun así **el guardia debe
> rechazarlo (R11)**, que es lo que el test existente exige.
>
> **Decisión: NO EQUIVALENTE, y tampoco superviviente — está MUERTO.** No hace
> falta test nuevo. Lo que hace falta es corregir el recuento de la campaña:
> este mutante pertenece a los 123 muertos.

### 8. `infrastructure/security/database_reference_guard.py:286` [entero]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 9. `scripts/verificar_sql_ecosistema.py:40` [entero]

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

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

## Timeouts

Estos agotaron el reloj **también al repasarlos en serie**, uno a uno y sin nadie compitiendo por la máquina: la contención ya no los explica. Míralos como un cuelgue de verdad, no como ruido.

- `infrastructure/security/database_reference_guard.py:267` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:270` [aritmetico] fin += 1 -> fin -= 1
- `infrastructure/security/database_reference_guard.py:287` [aritmetico] fin += 2 -> fin -= 2
- `infrastructure/security/database_reference_guard.py:309` [comparacion] if pos != -1 -> if pos == -1
- `infrastructure/security/database_reference_guard.py:309` [entero] if pos != -1 -> if pos != -2
- `infrastructure/security/database_reference_guard.py:319` [entero] if fin == -1: -> if fin == -2:

