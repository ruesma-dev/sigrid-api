<!-- progress/review_F-004.md -->
Revisión incremental desde `d4e8535` (pasada final; ámbito: C4 bis, RM1-RM6 y
consolidación). Lo aprobado en los tres reviews troceados queda dado por bueno:
`git diff d4e8535..79c5520 --stat` y `79c5520..31fdadf --stat` confirman que
desde entonces solo cambiaron `tests/`, `progress/` y `specs/`.

# F-004 · Review final

## Veredicto: **APROBADO** (consolidado, con dos apuntes de papeleo)

**Nivel de rigor: `critico`** (declarado en `harness/features.json`): fase RED,
cobertura, campaña de mutación **completa** (`max_mutantes: null`), **cero
supervivientes** y las verificaciones `MANUAL (humano)` con su comando exacto.
`init.sh` no lo ejecuto yo (lo mide el líder), pero sí verifiqué la suite:
`pytest -q -p no:cacheprovider tests` en un worktree limpio sobre `79c5520` →
**1.480 passed, 1 skipped, 39,0 s**. No apruebo sobre rojo.

## C4 bis — la puerta de mutación

- [x] **Existe `progress/mutacion_F-004.md`** generado por la herramienta: 167
      mutantes, **167 muertos, 0 supervivientes, 0 timeouts**, 366,0 s.
- [x] **Totales verificados de forma independiente** (cálculo puro), sobre el
      árbol en `31fdadf`: `alcance_de_feature('F-004')` → origen `rama`
      (`f8bb8c6..feature/F-004-…`), **6 ficheros y 1.383 líneas**, idénticas una
      a una a la tabla del informe (571/340/81/165/66/160); `generar_mutantes`
      fichero a fichero → **167**, repartidos 63/49/23/18/7/7. Exacto.
- [x] **Muestreo de mutantes reales:** localicé 8 de los 36 supervivientes
      analizados (#29-#36) por fichero, línea, operador y **texto exacto
      original→mutado**; los ocho existen como mutantes generados.
- [x] **Los muertos están comprobados, no contados.** «Tiempo total» **366 s >
      60 s**, luego vale el recálculo puro más las RM: **campaña NO reejecutada
      (366 s según el informe)**, como manda el checkpoint decir. En su lugar
      reproduje 11 mutantes a mano (abajo).
- [x] **La campaña tardó lo que tenía que tardar:** coste por mutante =
      366 s × 8 workers ÷ 167 = **17,5 s**, muy por encima del segundo que
      dispara la sospecha por construcción.
- [x] **Sin cabecera «⚠ CAMPAÑA NO VÁLIDA»**, «Sin veredicto (base rota)» = 0 y
      «Timeouts repasados en serie: 0»; la línea base corrió y salió verde en
      los 8 worktrees (86,4-94,5 s bajo contención).
- [x] **Cada superviviente con su análisis completado:** los 36 de `d4e8535`
      tienen ficha, ninguna en `PENDIENTE`, y **cero supervivientes** en la
      campaña vigente (`supervivientes_maximos: 0` de `critico`). Campaña
      automática con 167 mutantes: no aplica la tabla de campaña MANUAL.
- [x] **Evidencias** en `impl_F-004.md` §6 y §8.6 con los cuatro números (1.480
      tests, cobertura 100,0 % de 465 líneas, 167 mutantes / 0 supervivientes,
      suite 45,12 s y 60,21 s bajo `coverage`; ver apunte 3). Ningún N/A aquí.

## RM1-RM6

- **RM1 · SHA** [x]. El informe declara
  `79c55208ebfef500b1c3b9e38926a635874f50cd`, el commit del código y los tests.
  HEAD hoy es `31fdadf`, pero ese diff toca solo `progress/` y `specs/`. Prueba
  directa: mi recálculo corre sobre el árbol **en `31fdadf`** y da las mismas
  1.383 líneas y los mismos 167 mutantes. El alcance medido es el que reviso.
- **RM2 · Coherencia del tiempo** [x]. `media × W` = 2,2 × 8 = **17,6 s** por
  mutante, contra una línea base de **39,0 s medida por mí en serie** y de
  86-95 s bajo contención: no hay salto de orden de magnitud (el umbral es la
  décima parte). Quedar por debajo de la base es lo esperado y aquí está
  explicado: se evalúa con `-x`, los **167 mueren**, y los cinco
  `tests/test_f004_*.py` ocupan las posiciones 5-10 de los 30 ficheros de la
  suite, así que casi todos abortan pronto. `mutantes × media` = 367 ≈ 366 s.
- **RM3** [x]: no hay ni un equivalente declarado —los 36 se cerraron con
  test—, así que ninguno puede salir muerto. Satisfecha por vacío. **RM4** [x]:
  es lo que usé, subconjunto de tests sobre una copia, no la campaña entera.
  **RM5** [x] N/A justificado (cero equivalentes y cero supervivientes); el
  encargo lo sustituye por la reproducción de abajo.
- **RM6 · Código defensivo** [x]. `git diff d4e8535..79c5520 --stat`: solo
  `tests/` (5 ficheros, 282 líneas) y `progress/mutacion_F-004.md`. **Cero
  líneas de producción tocadas**: no se quitó ninguna guarda. Verificado.

## Reproducción de los tests nuevos (mi medición, worktree desechable)

Worktree `--detach` sobre `79c5520`, mutante aplicado con
`harness.mutacion.aplicar_mutante`, `pytest -q -p no:cacheprovider` sobre los
cinco ficheros `test_f004_*`. Base sin mutar: **192 passed, 1,42 s**, el mismo
número del informe. Los seis caen con el mutante y pasan sin él, con el test que
el informe dice y el mismo recuento:

| Mutante (fichero:línea [operador] original→mutado) | Resultado |
|---|---|
| `document_write_guard.py:64` [entero] `* 4 / 3`→`* 5 / 3` | 1 failed/191 · `…_un_caracter_por_encima_del_tope_muere_antes_de_decodificar` |
| `document_write_guard.py:64` [entero] `+ 4`→`+ 5` | 1 failed/191 · mismo test |
| `document_write_guard.py:65` [comparacion] `>`→`>=` | 1 failed/191 · `…_la_longitud_exacta_del_tope_del_base64_no_se_rechaza` |
| `function_app.py:275` [entero] `deps[0], deps[1]`→`deps[1], deps[1]` | 1 failed/191 · `…_la_ruta_toma_settings_y_repositorio_de_las_dos_primeras_posiciones` |
| `concepto_grafico_statements.py:62` [entero] `mes == 12`→`mes == 13` | 1 failed/191 · `…_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040` |
| `attach_…_use_case.py:540` [booleano] `idempotente=False`→`True` | 1 failed/191 · `…_la_respuesta_del_commit_dice_que_no_fue_idempotente` |

**No son tests de adorno**: los cuatro que más me olían asertan el valor exacto
—500,1 ms con el reloj fijado por `monkeypatch`, los 18 y 19 caracteres del
tope, `{"repository": "dep1", "settings": "dep0"}` y `_ultimo_domingo` contra
`calendar.monthcalendar` en los 540 meses de 1996-2040—, no que exista la clave.

## El hallazgo del arnés: verosímil, y el sesgo es pesimista

Reproduje también los **5 «supervivientes» de la tirada intermedia**: mueren los
cinco, y no por los pelos —`:191` 4 fallos, `:246` **41**, `:270` **38**, `:271`
1, `:294` 3—. Un mutante que tumba 41 tests no sobrevive a una suite que se
ejecute de verdad: en esa tirada la suite no juzgó el código mutado.

**La sospecha es verosímil y está en el código** (no medida, pero confirmada
como camino posible): `ResultadoSuite.verde` (`harness/mutacion.py` l. 491) da
cierto para `PYTEST_OK` **y `PYTEST_SIN_TESTS` (exit 5)**, y
`EjecutorPytest.ejecutar` (l. 612) traduce todo `verde` en `SUPERVIVIENTE` —una
decisión deliberada, documentada en su docstring—. Los demás códigos van a
`INDETERMINADO`, así que **exit 5 y exit 0 son las dos únicas rutas a un falso
superviviente**, y ambas significan lo mismo: la suite no vio el mutante; qué
produce ese exit 5 bajo contención sigue sin medir. **Para F-004 importa la
dirección, y es pesimista**: convierte muertos en supervivientes, nunca al
revés, así que añade trabajo pero no esconde huecos de tests. La ruta contraria
—un fallo espurio con exit 1 firmando un MUERTO falso— existe en teoría
(`ejecutar` no mira **qué** test cayó), pero aquí no muerde: F-003 remidió 123
muertos con 0 falsos, y el único test nuevo sensible al reloj fija
`time.monotonic` con `monkeypatch`. **El cero de supervivientes es sólido.** No
lo arreglo: es tarea del arnés y de `arnes-base`.

## Veredicto consolidado y qué queda para cerrar

Con los cuatro informes, **F-004 puede pasar a `done`** cuando el líder cierre
estos puntos. T18-T21 no bloquean el cierre de la implementación, igual que la
T8 de F-003; los apuntes 2 y 3 son ediciones de una línea sobre papeleo ya
medido —no cambian ninguna evidencia ni ningún veredicto, por eso no rechazo por
ellos, pero deben estar hechos antes del `done`—:

1. `bash harness/init.sh` en verde sobre `31fdadf` (lo mide el líder) y marcar
   **T22 `[x]`** en `tasks.md`: sigue en `[ ]` y no es tarea manual del humano.
2. **Apunte 1:** `impl_F-004.md` §8.6 aún dice «Mutación: sigue PENDIENTE» y
   contradice a §6, que la da por cerrada. Una línea.
3. **Apunte 2:** C4 bis pide que «Evidencias» declare **con cuántos workers** se
   lanzó la campaña. El dato existe y es correcto —fila «Workers: 8» del informe
   de la herramienta, que §6 enlaza— y con él calculé el coste por mutante;
   falta citarlo en §6.
4. Resumen en `progress/history.md` y `current.md` reducido a la sesión activa.
5. Tras el `done`, PARADA 2 con el humano para **T18-T21** (despliegue con App
   Settings cerradas, dry-run contra producción, primer `commit:true` con
   autorización expresa y repetición idempotente), respuestas a `impl_F-004.md`.

**Automejora propuesta (no aplicada)** a `harness/mutacion.py`, y por
propagación a `arnes-base`: que un veredicto `SUPERVIVIENTE` con `sin_tests`
cierto salga como **`INDETERMINADO`**. «Nadie recogió ningún test» y «los tests
no cazan esto» son cosas distintas y hoy se cuentan igual. Feature aparte.
