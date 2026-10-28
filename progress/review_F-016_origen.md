<!-- progress/review_F-016_origen.md -->
# Revisión F-016 · cumplimiento funcional de la spec (R1-R19)

Revisión completa (pasada 1), acotada a R1-R19, de `dev...c08461f` (HEAD de `feature/F-016-proforma-a-origen`).

**Veredicto: APROBADO** (este bloque). Sin defectos bloqueantes; tres observaciones no bloqueantes.

**Encargo troceado**: solo cumplimiento funcional de R1-R19 contra `create_proforma_use_case.py`,
`proforma_origen_statements.py`, `proforma_origen_models.py` y `proforma_models.py`. Quedan fuera, por estar en
otros informes paralelos: `bash harness/init.sh`, la suite entera, CHECKPOINTS C1-C5, la campaña de mutación y la
documentación (R20-R25). Rigor de la feature: `critico` (lo validan esos informes, no este).

## Cómo se verificó

- Lectura del diff `git diff dev...HEAD` de los cuatro ficheros, más el núcleo que usan (`_escribir`, `_previa`,
  `_respuesta`, `_construir`, `numerar`, `_SEGUIMIENTO_A_CERO`, `construir_dcapro_*`) y `buscar_del_mes` de F-007.
- **Aviso de entorno**: mientras revisaba, el árbol principal tenía un mutante aplicado en
  `proforma_origen_statements.py:256` (`if not _vinculo(fila)` → `if _vinculo(fila)`), sin duda la campaña de
  otro revisor. Con él fallaban 2 tests de F-016 en el árbol. Por eso **todo lo verificado es HEAD `c08461f`**,
  sobre una copia limpia (`git archive HEAD`) en el scratchpad. Al cerrar, `git status` vuelve a estar limpio
  (solo los `review_F-016_*.md` sin seguimiento de los otros revisores y `.claude/worktrees/`).
- pytest acotado sobre la copia limpia: `test_f016_{use_case,transaccion,statements,models,route}.py` y
  `test_f007_{use_case,transaccion,route,filas}.py` → **261 passed**.

## R1 / R2 · la proforma de mes no cambia (prioridad del humano)

Recorrí cada camino de mes del `_proforma` reestructurado:

| Punto | Mes antes | Mes ahora | ¿Igual? |
|---|---|---|---|
| Etapa 1 (`:257`) | `if fallos: raise` | `if fallos and not a_origen` (`a_origen` False) | Sí |
| R24 (`:287`) | `buscar_del_mes` | `buscar_del_mes` (la función de origen solo con `a_origen`) | Sí |
| `contrato_a_origen` (`:291-293`) | se emite | el filtro solo corre con `a_origen` | Sí |
| `existente` fuera / dentro | `_existente(...)` | `_a_origen(request, _existente(...))`, identidad en mes (`:623`) | Sí |
| `idempotente` (`:248`) | `_idempotente(...)` | envuelto en `_a_origen`, identidad | Sí |
| `_comprobar_dentro` (`:528-541`) | LP1 + `buscar_del_mes` | `cadena is None` → `buscar_del_mes`, sin LP8 | Sí |
| `_construir` (`:561-566`) | `cla` 141 | igual; la rama de cadena solo con `cadena` | Sí |
| Respuesta | `ProformaResponse` | la misma instancia, **sin claves nuevas** | Sí |
| Traza (`:195`) | claves de F-007 | las de origen solo con `modo == "origen"` | Sí |
| Lecturas | LP1-LP6 en su orden | `ProformaOrigenStatements` no se instancia en mes | Sí |

- Los asserts nuevos de `_construir` (`isinstance(request, _AltaDeProforma)`, `_contexto` no nulo) no abren un
  camino de fallo en mes: `_ejecutar` siempre recibe el `alta` con `_contexto` puesto (`:309-313`), y `_previa` y
  `_escribir` pasan ese mismo objeto. `_comprobar_dentro` ya hacía el mismo assert en F-007.
- R2: `git diff dev...HEAD` no toca `create_albaran_compra_use_case.py`, `albaran_compra_statements.py`,
  `albaran_compra_models.py`, `proforma_statements.py` ni ningún test de F-007/F-009/F-015 (solo hay
  `test_f016_*`, `f016_dobles.py` y el fixture nuevos). `function_app.py`: la llave nueva va **después** de la de F-007
  y solo con `commit and modo == "origen"`; `sigrid/albaran` y `albaran-directo` no cambian.
- Modelo: en mes, `proforma_anterior`/`primera_de_cadena`/`linea_anterior` dan 400 (`_reglas_de_origen`). Lo único
  que cambia en mes es que ahora se admiten `"modo": "mes"` y esos campos a su valor nulo o falso, que antes
  rechazaba `extra="forbid"`: la spec lo pide así (R1, «o trae `"mes"`»).

## A origen · requisito por requisito

| R | Dónde | Resultado |
|---|---|---|
| R3 | `proforma_models.py` `_reglas_de_origen` | exactamente uno de anterior/primera (`==` sobre bool); `sin_contrato`; `linea_anterior` con primera; `linea_anterior` repetida; campos de cadena sin origen → `ValueError` → 400 de F-012 sin `codigo`. OK |
| R4 | `function_app.py` `_exigir_escritura_de_proformas_origen` | después de la llave de F-007, antes del caso de uso, solo con `commit`. OK |
| R5 | `buscar_del_mes_origen` | si **todas** las del mes son a origen: mismo total → `existente`; otro → aviso `otra_del_mes` y sigue. Con alguna de mes, o con `otra_del_mes`, F-007 tal cual (las mixtas con una de mes de otro total dan `proforma_del_mes_existente`, como dice R5). OK |
| R6 | `validar_anterior` + LP7 | ≠ 1 fila, `docoritip` ≠ 1, `fec` > fecha de R18 → `anterior_no_valida`. LP7 se lee sin `muchas` (`max_rows` por defecto) y truncar es error, así que un duplicado se cuenta. OK |
| R7 | `comprobar_sucesoras` + LP8 | cualquier fila → `anterior_con_sucesora` con los `cod` en el mensaje. OK |
| R8 | `_cadena` `:349` | en la primera no se leen LP7, LP8 ni LP9. OK |
| R9 | `validar_continuadas` | no es de la anterior / otro `ctrpro` / de contrato frente a sin vincular → `linea_anterior_no_valida`, en un solo `lineas_no_validas` con los de la etapa 1 (`:363-369`). OK |
| R10 | `avisos_de_nuevas` | identificada, no continuada y con su `ctrpro` en LP9 → aviso con `lineas_anterior`. Se cuelga de la línea en `_a_origen` y entra en `codigos` de la traza. OK |
| R11 | `superponer_cadena` | continuada: `canorilin` = su `ide`, `canoriori` = anterior + `can` (en Decimal), `imporiori` el del núcleo (`ctrpro.tot`) si vinculada o el de la anterior si sin vincular; nueva: `canorilin` 0, `canoriori` = `can`, `imporiori` el de F-007 (0 sin vincular); `canoriant`/`imporiant` 0 en todas. OK |
| R12 | `filas_arrastradas` | copia de LP9 (`SELECT *`, mismo juego de columnas que la plantilla L8 del núcleo); `can`/`tot`/`ivacuo`/`prepma` 0; `canorilin` = `ide`; `canoriori`/`imporiori` conservados; `_SEGUIMIENTO_A_CERO`; `med` None y `canmed` 0 (igual que `_RESETEO_SIN_VINCULAR`); `pos` = (n+1)·64 en el orden de LP9 (`ORDER BY pos, ide`). Al no ser `_Linea`, no generan `ctrprodes`, `mov` ni `UPDATE` (`_escribir` itera `lineas`, no `filas.dcapro`). OK |
| R13 | `cabecera_a_origen` | `docoritip` 1 y `docoriide` = la anterior o 0; las dos están en la lista fija de `dca`. OK |
| R14 | `_cadena` `:374-380` | pedidas + arrastradas > tope → `demasiadas_lineas`, antes de traducir, así que también en la previa. OK |
| R15 | `:271-285` | `comprobar_hoja`, `anterior_y_origen` y los avisos de la línea, sin cambios. OK |
| R16 | `:291-293` | se filtra `contrato_a_origen` antes de componer `avisos`, que es lo que usan `existente` (fuera y dentro) y la respuesta. OK |
| R17 | `_comprobar_dentro` `:528-541` | tras E1, con `buscar_del_mes_origen` en lugar de R24 y, con anterior, LP8 por el cursor. Va antes de reservar nada y se repite en cada reintento de `work`. OK |
| R18 | núcleo sin tocar | las arrastradas van al final de `filas.dcapro`: `numerar` les da `ide` consecutivos, entran en el INSERT clonado y E12 espera `len(filas.dcapro)`, con arrastradas. `APPLOCKS` sin cambios. `superponer_cadena` y `filas_arrastradas` no mutan su entrada, así que reintentar es seguro. OK |
| R19 | `_a_origen` / `_linea_arrastrada` | `cadena` solo en `previsto`/`creado`; `anterior` {cod, ide} o null; los importes de cadena por `importe_de_cadena` (Σ redondeo HALF_UP en Decimal) de LP9 y de lo escrito; `n_arrastradas`. Por línea, los cuatro campos; las arrastradas detrás, con `indice` ≥ n pedidas. En `existente` (fuera y dentro) e `idempotente` (fuera y dentro), `cadena` null y campos a None. OK |

Orden de cortocircuito a origen ante la repetición: la referencia (`idempotente`) y R5 (`existente`) salen
**antes** que LP8. Así, reenviar la misma proforma ya registrada no da por error `anterior_con_sucesora`.
Es correcto.

## Observaciones (no bloqueantes; para el humano o una feature futura)

1. **El orden de los errores cambia a origen** (`create_proforma_use_case.py:257` y `:271-304`). Los fallos de la
   etapa 1 se aplazan hasta `_cadena`, como manda design §Flujo 5 (R9: «en el mismo `lineas_no_validas`»). Por eso,
   a origen, `importe_mes_no_cuadra`/`hoja_descuadrada`, `proforma_del_mes_existente`, un `existente` (200),
   `anterior_no_valida` y `anterior_con_sucesora` salen antes que `lineas_no_validas`. En mes, en cambio, va primero
   `lineas_no_validas`. Escenario: una hoja a origen con una línea que no es del contrato y del mismo total que una
   proforma a origen del mes ya registrada recibe `existente` y no 400. No contradice ningún Rn, pero
   `contrato_proformas.md` v1.2 no lo dice. Propuesta: una línea en su §4.
2. **`_vinculo` no mira `docoritip` de la línea** (`proforma_origen_statements.py:157-158`, usada en R9, R10 y
   `superponer_cadena`). Una línea de la anterior con `linoriide` hacia algo que no sea un `ctrpro`, si existe en
   proformas, se compararía como si lo fuera. R9 lo define así («`linoriide`»), y en proformas de contrato
   `docoritip` es 44, así que el riesgo es residual. Solo se anota.
3. **A origen, `totales.n_lineas` cuenta las arrastradas** (`_respuesta` del núcleo: `len(filas.dcapro)`; lo fija el
   test R11/R12, 8 = 6 + 2). Cuadra con `lineas`, que también las trae, pero el contrato v1.2 no lo dice. Para
   `proformas`/`facturas`, n_lineas ≠ número de líneas pedidas. Propuesta: una línea en el contrato.

## Cambios requeridos

Ninguno en el alcance de este bloque (R1-R19).

## Automejora (propuesta, no aplicada)

- La revisión troceada en paralelo choca con una campaña de mutación que muta **el árbol principal**: durante esta
  revisión había un mutante aplicado, y un pytest acotado sobre el árbol dio 2 falsos rojos. Propuesta para
  `.claude/agents/reviewer.md`: «Si otro revisor reejecuta la campaña en paralelo, verifica sobre `git archive HEAD`
  en tu scratchpad, nunca sobre el árbol», o que la reejecución de la campaña use un `git worktree` propio.
