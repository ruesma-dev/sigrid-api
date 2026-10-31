<!-- progress/review_F-008.md -->
Revisión incremental desde `591d9ab` (pasada 3): delta `591d9ab..8313ba0` + azure-apps `654e7fd` y `f3f6474` (`sigrid_api.md`)

# F-008 · Review consolidada (T21)

**Veredicto: APPROVED.** Las condiciones C1-C3 de la pasada 2 están resueltas. Quedan solo las verificaciones
manuales T22-T24 y el `init.sh` final (T25).

- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige tests trazables, fase RED con salida
  real, cobertura ≥ 80 % de lo cambiado, mutación con 0 supervivientes sin justificar y RM1-RM6 (RM5 con muestra).
- **Base:** lo aprobado en la pasada 2 (`591d9ab`, resumida abajo) y en los siete informes troceados de `2879ddb`
  queda dado por bueno. El delta son `45e9707` (informe), `e2bc1f4` (código y 6 tests), `1b9f266` (R16b en
  `requirements.md`) y `8313ba0` (informe y `current.md`). No cambia firmas públicas, no mueve ficheros, no toca
  `infrastructure/`, `.env` ni `infra/`. Solo `CODIGOS_FACTURA` gana un código (`factura_models.py:43`).
- **Árbol:** principal sin tocar ni cambiar de rama. Mutaciones en un worktree detached del scratchpad, borrado al
  acabar; `git worktree list` muestra solo el principal y `python -m harness.mutacion --restaurar` dice «no quedó
  ningún mutante aplicado».

## Medición propia en `8313ba0`

- `bash harness/init.sh` (tal cual): exit 0, `4217 passed, 1 skipped, 1 warning in 241.21s`, `ENTORNO LISTO`.
- `PUERTA COBERTURA: 99.3% de 1203 líneas cambiadas cubiertas (1194/1203, umbral 80%, nivel critico)` `[OK]`.
- `python -m harness.tamano --feature F-008`: exit 0, `requirements 150/150, design 229/250, impl 189/220`. Este
  informe tiene ≤ 140 líneas.
- `pytest tests -k f008 --collect-only`: **424** (418 de la pasada 2 + 6 de R16b).

## (1) `origen_sin_lineas`: código, orden y efectos

- **Dónde.** `_lineas_de_origen` (`create_factura_use_case.py:621-656`) filtra ahora por `can` ≠ 0 al agrupar y,
  antes del bucle, rechaza los orígenes que se quedan sin ninguna (`details.origenes` = sus `cod`, en el orden de la
  petición). Esa función la llaman la previa (paso 6, `:291-295`) y la transacción tras `_bloquear_origenes` con
  la relectura `bloquear=True` (`:897-903`), así que la regla se repite bajo `UPDLOCK`.
- **Orden de design §7.** Cae en «orígenes y modo → `a_origen`»: después de `_origenes` (modo, proveedor,
  contabilizado) y antes de `origen_ya_facturado`, `comparar_a_origen`, `_sin_origen`, retención y totales. Que
  vaya antes de `origen_ya_facturado` es coherente (es del origen, no de una línea) y lo fija
  `test_f008_orden_origen_sin_lineas_antes_que_ya_facturado`.
- **No escribe nada.** En la previa salta antes de `_escribir`: `repo.transaccion is None`. Con `commit`, se
  rechaza antes de abrir la transacción (`test_f008_r16b_con_commit_no_se_escribe_nada`: ni bloqueos, ni reservas,
  ni marcas). Bajo bloqueo, ROLLBACK con el mundo intacto y el origen sigue en `est` 3
  (`test_f008_r16b_origen_que_se_queda_sin_lineas_bajo_bloqueo`).
- **Sin regresiones.** R16 no cambia: las de `can` 0 siguen sin pasar (el filtro se movió del bucle a la
  agrupación, misma semántica) y `test_f008_r16_solo_lineas_con_can_distinta_de_cero` sigue verde. Los orígenes de
  `can` mixto pasan como antes (`test_f008_r15_la_linea_de_can_cero_no_cuenta`, verde). El acceso directo
  `por_origen[...]` en el bucle no puede dar `KeyError`: todo origen ausente ya salió por `vacios`.
- **Los cuatro casos de la regla** están cubiertos: un origen vacío entre dos, un origen sin ninguna fila en
  `dcapro`, el único origen vacío y el que se vacía entre la previa y el bloqueo.

## (2) Mutantes de R16b, reproducidos (worktree propio en `8313ba0`, base 107/107 en verde)

Suite: `tests/test_f008_use_case.py` y `tests/test_f008_transaccion.py`, `-x`.

| Mutante (texto original → mutado, `create_factura_use_case.py`) | Resultado |
|---|---|
| `if float(fila["can"] or 0):` → `if not float(fila["can"] or 0):` (`:630`) | MUERTO, exit 1 |
| `if vacios:` → `if not vacios:` (`:633`) | MUERTO, exit 1 |
| `... not in por_origen]` → `... in por_origen]` (`:632`) | MUERTO, exit 1 |
| `if vacios:` → `if False:` (sin `-x`) | MUERTO, **6 fallos**: los 6 tests de R16b, incluidos los 2 de transacción |

- El último confirma que la comprobación bajo bloqueo tiene test propio: sin la regla, el test de la relectura
  con `UPDLOCK` falla, no solo los de la previa.
- **RM1:** la campaña (`eba243e`) no cubre este delta; lo cubren los 7 mutantes manuales del informe
  (`impl:142-145`), de los que he reproducido 3 al pie de la letra más uno propio. No hace falta relanzarla.
- **RM3:** ninguno de los mutantes es equivalente. **RM6:** se quitó la guarda `if not float(can): continue`
  del bucle, pero el invariante pasa a la agrupación, que construye el dato (`:629-631`): mismo filtro, en origen.

## (3) Spec y documentación frente al código

- **R16b** (`requirements.md:50`): «SI un origen no tiene ninguna línea con `can` ≠ 0, ENTONCES
  `origen_sin_lineas`, también bajo bloqueo». Coincide con el código y los tests.
- **azure-apps `f3f6474`** (§8.11): la fila `origenes` y la lista de códigos dicen `origen_sin_lineas` con
  `details.origenes`. Coincide.
- **azure-apps `654e7fd`** (hallazgo 6 de docs, condición C3): los 11 códigos de `lineas_no_validas` coinciden uno
  a uno con los de `factura_lineas.py:312-504`, con la forma `{indice, codigo, mensaje}` de `FalloLineaFactura`
  (`create_factura_use_case.py:680-692`). La búsqueda de `cod_obra` en `SIGRID_ALBARAN_EMPRESAS_OBRA` y el
  `obra_no_encontrada` si no está en exactamente una coinciden con `_obra_pedida` (`:413-424`), y los orígenes sin
  `cod_obra` se buscan en esas empresas (`:450`). Los dos commits tocan solo `sigrid_api.md`.

## (4) Decisiones del humano constan en el informe

- **C1** (commits agrupados T9-T10 y T12-T14): `impl_F-008.md:91-94`, «Aceptada por el humano el 2026-10-31».
- **C2** (R16b): `impl:133-145`, con el RED pegado (`6 failed`, `DID NOT RAISE` y las aserciones de código) y los
  7 mutantes manuales. `current.md:13-14` lo recoge.
- **C3:** `impl:165-166` remite a `654e7fd`.

## (5) Evidencias de `impl_F-008.md:172-184` frente a lo medido

| Informe | Medido | ¿Coincide? |
|---|---|---|
| 4217 passed, 1 skipped | 4217 passed, 1 skipped | sí |
| 424 de F-008 | 424 recogidos | sí |
| 99,3 % (1194/1203) | idéntico | sí |
| 11 manuales, 11 muertos | 4 reproducidos de R16b, 4 muertos (6 más en la pasada 2) | sí |
| 276,07 s (máquina cargada) | 241,21 s | sí (reloj) |
| tamaño impl 170/220 | 189/220 | **no**: es la cifra de una medición anterior; menor, dentro del tope |

`features.json`: F-008 sigue siendo la única `in_progress`, rigor `critico`. Los 4 commits del delta están en
español y llevan `Co-Authored-By`.

## Checkpoints (delta; el resto, en la pasada 2 y en los informes troceados)

- [x] C1 `init.sh` verde · [x] C2 estado coherente (`current.md` recoge las decisiones) · [x] C3 sin cambios de
  estados: `origen_sin_lineas` se rechaza antes de tocar `con.est`
- [x] C3 bis N/A: el delta no toca `docs/referencia/`
- [x] C4 trazabilidad: R16b con 6 tests por nombre; R48 completo con `654e7fd` y `f3f6474`
- [x] C4 bis: RED pegado (`impl:136-139`), cobertura `[OK]`, mutación con 0 supervivientes en el delta, RM1-RM6
- [x] C4 ter N/A: no hay `harness/rutas_sensibles.json` y el delta no toca `infrastructure/security/`
- [x] C5: desviación 7 aceptada por el humano; árbol limpio, sin temporales, sin `print` ni `breakpoint`

## Pasada 2 (`591d9ab`), en resumen

Los 14 hallazgos bloqueantes de la pasada 1 quedaron corregidos, salvo el 6 de docs, rebajado a condición C3 y
resuelto ahora en `654e7fd`. Se reprodujeron 6 mutantes de aquella ronda (todos muertos). Las condiciones C1 y C2
eran decisiones del humano; las tomó el 2026-10-31. Detalle: `git show 591d9ab:progress/review_F-008.md`.

## Observaciones menores (no bloquean, a criterio)

- La fila «tamaño impl» de Evidencias dice 170/220; mide 189/220.
- `requirements.md` está en 150/150: cualquier línea más rompe la puerta de tamaño.
- Siguen en pie los menores de la pasada 2: «seis App Settings» en D1 de `verificacion_manual.md` (son cinco),
  «equivalentes» #64 y #65 en `mutacion_F-008.md`, y las O1-O6 de escritura (la O2 se comprueba en T22/T23).

## Pendiente para cerrar F-008

- **T22:** permisos de `user_rw` (V1), con quien administra Sigrid.
- **T23:** desplegar con la llave cerrada, D1-D5 y previas P1-P7 de `verificacion_manual.md`, sin `commit`.
- **T24:** G1 (FR en la obra 0404) y G2 (FRGG), cada una con su autorización expresa; después «Comprobar»,
  «Contabilizar» y anularlas en el escritorio (V2-V4, V6, V7).
- **T25:** `bash harness/init.sh` final. Abrir `SIGRID_FACTURA_WRITE_ENABLED` es decisión del humano.

## Automejora (propuesta, no aplicada)

Que la fila «tamaño» de Evidencias la imprima `init.sh` en la misma línea que los tests, para que no se quede con la
cifra de una medición anterior cuando el informe crece después.
