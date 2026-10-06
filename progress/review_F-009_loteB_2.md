<!-- progress/review_F-009_loteB_2.md -->
Revisión completa (pasada 1) del trozo 2 del lote B: T5 (`f0130ed`) y T6 (`d936ced`), sobre HEAD `53489b3`. `43eae24` solo
añade tests de T3 (CIF) y T4 (`insertar_clonada`): es del otro reviewer y aquí solo se comprueba que no afecta a T5-T6.

# F-009 · Revisión del lote B, trozo 2 (T5-T6: funciones puras y filas)

**Veredicto: CHANGES_REQUESTED.** Hay un solo cambio requerido: el PMP se calcula mal cuando el stock vuelve a 0 con
residuo binario, y ese valor se escribiría en producción. Lo demás cumple la spec v8.1.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % y mutación con cero
supervivientes. La mutación es T16 (lote E): el plan de lotes aprobado por el humano en la PARADA 1
(`progress/current.md`) la pone al final, sobre la feature entera. En este trozo es N/A por ese motivo y se exigirá al
cierre.

## Verificación ejecutada (salidas reales)

- `bash harness/init.sh`, tal cual: `2110 passed, 1 skipped`, `PUERTA COBERTURA 100.0% (517/517)`, `PUERTA TAMAÑO` OK,
  `ENTORNO LISTO`.
- Las dos verificaciones de `tasks.md`: T5 `-k "r15 or r17 or r18 or r19 or r20 or r26"` da `72 passed`; T6 da `69 passed`.
- **RED de T5 reproducida** sobre una copia en el scratchpad (`git archive e2d52fb` más los tests de `f0130ed`). Sale
  `65 failed, 4 passed, 49 deselected`, idéntico al informe, con `AttributeError` de `siguiente_balance`,
  `redondear_euros`, `sufijo_analitica`, `encadenar_balances`, etc. El test de la regla A (R18,
  `siguiente_balance((10.0, 2.0), -4.0, 3.0)`) está entre los que fallaban.
- `ruff check` está limpio en los dos ficheros. No hay `print` ni secretos. Los tests no usan red ni BBDD: todo es puro.
- `git diff dev` está vacío en los casos de uso y modelos del clásico y de `albaran-directo`, en `infrastructure/security/`,
  `function_app.py` y `.env`. `tests/fixtures/` no ha cambiado desde `055a7e1`.

## Regla a regla (contra la spec y las mediciones)

| Regla | Código | Veredicto |
|---|---|---|
| `siguiente_cod`, `prefijo_de_serie` (R22, R26) | `albaran_compra_statements.py:186-194` | OK. Sin ceros a la izquierda, como `AC26/15950` |
| `siguiente_balance` (R19): `almcan`, `almpma` sin redondear, `prepma` = PMP de partida, `(0, 0)` sin `mov` | `:229-258` | OK con exactitud aritmética. **Falla con residuo binario** (cambio 1) |
| `encadenar_balances`: encadena por (producto, almacén), no toca `vigentes` | `:261-278` | OK. El test cubre 5 líneas con 3 pares y comprueba `prepma(n) = almpma(n-1)` |
| Regla A (R18): `canent` < 0 y la misma fórmula; stock final negativo | `:257`, `:654` | OK (M5) |
| `sufijo_analitica` / `codigo_analitica` (R15, M16d) | `:284-297` | OK. Quita un solo `MOD.`; `CD.SB37` queda entero; vacío ⇒ `None`; `RTRIM` de la obra |
| `estados_contrato` (R20), también con `Σcanser` < 0 y sumas `NULL` | `:304-314` | OK. A 2 decimales, como el clásico (`9,999` cuenta como servido) |
| `importe_linea`, `redondear_euros` (R17, H33) | `:197-226` | OK. `Decimal(repr)` y `ROUND_HALF_UP`: 2,675 da 2,68 y 1,005 da 1,01. IVA en fracción (M11) |
| `con` (R11, R22): `tip` 14, `emp` de la obra, `est` 1, `res` a 128 | `:399-414` | OK |
| `dca` (R21, H16): overrides del clásico solo sobre columnas existentes, `ctride` (0 sin contrato), `synckey`, bancarias escritas | `:417-461` | OK |
| `dcapro` vinculada (R12, R16, R17, H35, decisión 10) | `:473-544` | OK. `caaide`, `cod2`, `dncide` y `dncproide` salen del `ctrpro` (`''`/0 si faltan), nunca de la plantilla. `paride` es el pedido |
| `dcapro` sin vincular (R13, R13b, §Reseteo, R30c) | `:547-607` | OK. Aplica el §Reseteo completo (`cod2` vacío, DNC a 0, `tex` vacío, `fec` 0). Toma `natide`, `cueide` y `caaide` de los parámetros (el mapeo). Pone `docori*`, `canoriori` e `imporiori` a 0, `pre` = `tar` = `precio`, `dto` `''`, y `paride` es el resuelto |
| `ctrprodes` (R12, M6): una por vinculada, `can` con signo | `:610-621` | OK |
| `mov` (R19, R22, N1): `emp` = `con.emp`, fecha y hora del alta, `prepma` = `balance.prepma` | `:624-665` | OK |
| `log` (R22, M13): `est` 1, `ori` 0, `ope` 1, `usu` | `:668-685` | OK. Mismas columnas y nulos que F-006 |
| `numerar` (R25, R27): reentrante; `lindeside`/`linide` apuntan a su `dcapro` aunque haya sin vincular intercaladas | `:715-761` | OK. Corrige el 1:1 implícito del clásico |

## Decisión 11: sí hay riesgo real con floats

`almcan` y `almpma` son «Real» en Sigrid (`azure-apps/sigrid_tablas.md`, tabla `mov`). Por eso el stock que lee
L12/E7 arrastra el residuo de sumas binarias. Lo he ejecutado con la función real:

- Stock `0.1 + 0.2` a PMP 10, y se devuelve todo (`-0.3`) a 10,5. Sale `almcan = 5.55e-17` y
  `almpma = -2.7e15`.
- Si después entra otra línea del mismo par, su `prepma` (en `mov` y en `dcapro`) también vale `-3.7e15`. Según la
  hipótesis de §`prepma`, el escritorio copiaría ese valor como `prepma` del siguiente `mov`.
- Con `pre = pma` el residuo no se nota (`almpma` 4,0).

Se da cuando una devolución vacía el almacén (o una entrada salda un stock negativo) con un precio distinto del PMP.
También dentro del propio albarán: `+0.1`, `+0.2`, `-0.3`. El valor `almcan · almpma` sigue siendo correcto, pero el
PMP publicado es absurdo, queda escrito y no se corrige solo. Además, un residuo negativo dispararía un
`stock_negativo` espurio en el lote C.

El informe dice que el PMP solo se conserva con stock exactamente 0 «como el clásico». No es así: el clásico usa `pre`
cuando `stock_new` es 0 (`create_purchase_albaran_use_case.py:360`). El código sigue R19, que manda conservar. Lo que
está mal es la afirmación del informe, no el código.

## Decisión 1 (`tot` de la vinculada dentro de la tolerancia): opinión, no cambio requerido

**Las fuentes discrepan.** R17 y el contrato §2.2 dicen `tot = cantidad·precio` (el importe aprobado). Design
§Importes y el contrato §3.1 (tabla de la respuesta: `tot = round(can·pre, 2)`) dicen `cantidad·pre`. Las dos opciones
solo difieren cuando 0 < |`precio` − `ctrpro.pre`| ≤ 0,0001. La diferencia máxima es |cantidad|·0,0001: 0,01 € con
100 uds; 0,05 € con 500 (el umbral `ALTA_SIGRID_TOLERANCIA_EUR` de sv9); 0,10 € con 1.000; **2,50 € con 25.000 kg**
(medido: `importe_linea(25000, 1.0495)` = 26.237,50 frente a 26.235,00 con 1,0494).

En el caso normal la diferencia no se ve. Si sv9 valoró al precio del contrato, `precio` = round(importe/cantidad, 6) y
δ ≤ 0,005/|cantidad| + 5·10⁻⁷, así que con 25.000 uds se queda en ~0,02 €. El caso que importa es otro: albaranes
guarda el precio con menos decimales que `ctrpro.pre`.

- **A, `cantidad·precio` (lo implementado).** El total casa con lo aprobado. A cambio, la fila escrita es incoherente:
  `tot` ≠ `can·pre` de la propia fila, y el `mov` y el PMP valoran a `pre` mientras el albarán suma `tot`. **Nadie lo
  detecta**: ni sv9, ni los tests, ni la previa. Además, contradice dos de las cuatro fuentes.
- **B, `cantidad·pre`.** La fila queda coherente, como hacen el escritorio y el clásico. Si la diferencia pasa de
  0,05 €, sv9 la marca `importe_distinto` **en la previa (dry-run), antes de escribir nada**. El fallo se ve, pero puede
  dejar ese albarán en `revisar` cada vez que se reintente.
- **Recomendación: C, la tolerancia también en céntimos.** Se toman `pre`, `tar` y `dto` del `ctrpro` solo si
  |δ| ≤ 0,0001 **y** `round(cantidad·precio, 2) == round(cantidad·pre, 2)`. Si no, se sigue la vía de
  `precio_distinto_del_contrato` (`pre` = `tar` = `precio`). La fila es coherente y el total es el aprobado siempre. El
  coste: algún aviso más y la pérdida del `tar`/`dto` del contrato en líneas grandes con δ minúsculo.
- Si se descarta C, prefiero **B** a A: un descuadre que sv9 ve antes de escribir es mejor que una incoherencia escrita
  en el ERP en silencio.
- Lo decide el humano. Al decidir, hay que alinear R17, design §Importes y contrato §2.2/§3.1 en la misma frase.

## Checkpoints

- **C1** [x] `init.sh` en verde · [x] ficheros del arnés presentes.
- **C2** [x] una sola feature `in_progress` · [x] rama `feature/F-009-alta-albaran-compra` · [x] `current.md` al día ·
  [x] `history.md` (no hay ninguna `done` nueva).
- **C3** [x] hexagonal: módulo de `application/`. Importa los guardias de `infrastructure/security`, como
  `concepto_grafico_statements` y `parte_reclamacion_statements`, y como pide design §Ficheros. Esa importación es de
  T4 · [x] primera línea con ruta · [x] sin `print`, TODO ni secretos · [x] `cod`/`res`/`fec`/`tip`/`est` en `con`, no
  en `dca` · [x] nada se recalcula solo: hay funciones para totales, `canser`/`estser`, `mov`/PMP; el cableado es del
  lote C · [x] `est` validado por L13 contra `conest` (R22) · [x] SQL con `?` (T4).
- **C3 bis** N/A: el trozo no trae documentos externos.
- **C4** [x] cada regla de T5-T6 tiene test (tabla de abajo) · [x] sin red ni BBDD · [x] los manuales T19-T24 están
  listados.
- **C4 bis** [x] `rigor` declarado · [x] RED de T5 con salida real y reproducida (R15, R17, R18, R19). T6 no tiene RED
  en R34 · [x] cobertura 100 % (517/517) · N/A mutación, RM1-RM6 y las demás casillas de campaña: T16, lote E, plan
  aprobado (ver cabecera) · [x] «Evidencias» con los cuatro números (mutación «no medido», con su motivo).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T5 y T6 `[x]`, con commits `F-009 T5:` y `F-009 T6:` · N/A el resto de `tasks.md` (la feature sigue
  abierta) · [ ] ficheros sin trackear: hay un `` `0`].{t `` vacío en la raíz, del 2026-09-24, **anterior al lote y
  ajeno a él**. No bloquea; el humano puede borrarlo · [x] `features.json` al día.

## Cobertura (requisito → tests de `tests/test_f009_statements.py`)

| Req. | Tests |
|---|---|
| R11 | `r11_con_clon_de_la_plantilla_con_lo_del_albaran`, `r11_res_del_con_recortado_a_128` |
| R12, H35 | `r12_dcapro_vinculada_desde_su_plantilla_y_su_ctrpro`, `r12_h35_*`, `r12_descripcion_*`, `r12_sin_unidad_*`, `r12_dos_lineas_*`, `r12_sin_plantilla_*`, `r12_ctrprodes_*` |
| R13, R13b | `r13_dcapro_sin_vincular_con_reseteo`, `r13b_naturaleza_y_cuenta_*`, `r13_iva_*`, `r13_sin_unidad_*`, `r13_la_plantilla_no_se_toca` |
| R14, R16 | `r14_vinculada_sin_partida_*`, `r14_sin_vincular_sin_partida_*`, `r16_partida_distinta_*` |
| R15 | `r15_sufijo_analitica` (13 casos), `r15_codigo_de_la_analitica`, `r15_almacen_centro_y_analitica_*` |
| R17 | `r17_redondear_euros_*`, `r17_importe_linea` (10), `r17_sumar_importes_*`, `r17_tolerancia_de_precio` (8), `r17_vinculada_*` (3), `r17_importes_de_la_linea_*` |
| R18 | `r18_devolucion_regla_a`, `r18_devolucion_que_deja_el_stock_negativo`, `r18_mov_de_devolucion_*` |
| R19 | `r19_balance_de_entrada`, `r19_sin_mov_*`, `r19_almpma_sin_redondear`, `r19_con_denominador_cero_*`, `r19_encadenado_*`, `r19_mov_fechado_en_el_alta_*` |
| R20 | `r20_estados_contrato` (8, con Σcanser < 0), `r20_estados_con_sumas_nulas` |
| R21, R23 | `r21_dca_*` (3), `r23_filas_como_diccionario_*` |
| R22 | `r22_prefijo_*`, `r22_sellos_*` (4), `r22_log_de_alta_*` |
| R25, R26 | `r25_numerar_*` (4), `r26_siguiente_cod` |

## Cambios requeridos

1. **`application/use_cases/albaran_compra_statements.py:256-257`**
   (`almpma = pma if almcan == 0 else ...`). Hay que tratar como cero un `|almcan|` por debajo de un ε declarado,
   conservar el PMP y escribir `almcan = 0.0`.
   - **Valor de ε.** Propongo 1e-6: muy por debajo de cualquier cantidad real y muy por encima del residuo de un
     `float`. Hay que justificarlo en el docstring y en el informe.
   - **Por qué no es un cambio de spec.** R19 dice «con `stock + can` = 0 se conserva», y un residuo de 1e-17 *es* 0 en
     cantidades.
   - **Tests.** `siguiente_balance((0.1 + 0.2, 10.0), -0.3, 10.5)` debe dar `(almcan, almpma) == (0.0, 10.0)`. Otro con
     residuo negativo. Y uno de `encadenar_balances` con `+0.1`, `+0.2`, `-0.3` del mismo par, comprobando el `prepma`
     de la línea siguiente.
   - **Informe.** Corregir la decisión 11 de `progress/impl_F-009_loteB.md`: el clásico no conserva, usa `pre`.

## Observaciones (no bloquean; para el líder y el lote C)

- **O1.** La vinculada hereda de su plantilla (otra `dcapro` del producto) las columnas del §Reseteo: `med`, `canmed`,
  `fec`, `item`, `anexo`, `pla`, `texcom`, `pac`… Es lo que dice la spec («como hoy», M14 sobre la API, R33) y lo fija
  el test, pero conviene mirarlo en la UI en T22.
- **O2.** Diferencias con el clásico que no están declaradas en §Equivalencia (R33/T12): `con.res` se recorta a 128
  aquí y a 200 en el clásico; y con stock final 0 el clásico usa `pre` y aquí se conserva el PMP. Hay que declararlas o
  evitarlas en el dato fijo de T12.
- **O3.** T6 está `[x]`, pero «`mov` si y solo si `tipmov` = 1» y «`dcapro.prepma` = `mov.prepma` o 0» los decide el
  caso de uso: los constructores reciben `prepma` por parámetro. El reviewer del lote C debe exigir esos tests (R19,
  R21) en T7/T10.
- **O4.** La traza «T6 también se escribió antes: `32 failed, 38 passed, 85 deselected`» no coincide con lo
  reproducido sobre `f0130ed` más los tests de `d936ced`: `31 failed, 38 passed, 86 deselected`. Probablemente es de un
  estado intermedio. T6 no exige RED, así que no bloquea.

## Automejora (propuesta, no aplicada)

Añadir a `CHECKPOINTS.md` C3, en las trampas de Sigrid: «los campos “Real” (`almcan`, `almpma`, `can`) se comparan con
tolerancia, nunca con `== 0`». Es el mismo fallo que el clásico (`if stock_new`) y lo heredaría cualquier caso de uso
que toque `mov`.
