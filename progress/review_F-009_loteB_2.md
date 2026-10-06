<!-- progress/review_F-009_loteB_2.md -->
Revisión incremental desde `53489b3` (pasada 2): solo `2a007f6`. La pasada 1 (completa, T5 `f0130ed` y T6 `d936ced`)
queda resumida abajo; su texto íntegro está en `git show 45a3cb0:progress/review_F-009_loteB_2.md`.

# F-009 · Revisión del lote B, trozo 2 (T5-T6: funciones puras y filas)

**Veredicto: APPROVED** (pasada 2). La pasada 1 fue CHANGES_REQUESTED, con un cambio; está resuelto y verificado.

**Nivel de rigor:** `critico` (declarado): RED, cobertura ≥ 80 % y mutación con cero supervivientes. La mutación es T16
(lote E) por el plan de lotes aprobado en la PARADA 1 (`progress/current.md`): N/A en este trozo, exigible al cierre.

## Segunda pasada (`2a007f6`)

**Alcance.** El commit toca `albaran_compra_statements.py`, `tests/test_f009_statements.py`, `impl_F-009_loteB.md` y
`current.md`. No revisado: los ficheros de `specs/` y `spec_F-009.md` sin commitear (v8.2 del spec-author, en edición).

**Verificación (salidas reales).**
- `bash harness/init.sh`, tal cual: `2127 passed, 1 skipped`, `PUERTA COBERTURA 100.0% (525/525)`, `PUERTA TAMAÑO`
  dentro de los topes (con la spec en edición) y `ENTORNO LISTO`. `ruff` limpio en los dos ficheros.
- **RED reproducida** en el scratchpad (`git archive 45a3cb0` + tests de `2a007f6`): `-k "residuo or epsilon"` da
  `4 failed`; `-k opcion_c` da `11 failed, 2 passed`. Coincide con el informe, incluidos los dos que ya pasaban.

**Cambio requerido 1 (ε de stock): resuelto.**
- `EPSILON_STOCK = 1e-6`, con nombre propio y justificado en el comentario y en el docstring (`:246-249`, `:278-288`).
  Con `|stock + can|` por debajo de ε, `almcan` se escribe 0.0 y se conserva el PMP. Con stock real no se toca.
- Tests: residuo positivo (`0.1 + 0.2` y luego `-0.3`, da `(0.0, 10.0, 10.0)`), residuo negativo, un caso justo por
  encima de ε que **no** es cero, y `encadenar_balances` con `+0.1`, `+0.2`, `-0.3` del mismo par más una cuarta línea
  cuyo `prepma` es el PMP conservado. Son los que pedí.
- Decisión 11 corregida en el informe: el clásico usa `pre` con stock 0; no conserva el PMP.

**Opción C (decisión del humano): bien implementada.**
- `usa_precio_del_contrato(cantidad, precio, pre_contrato)` (`:229-243`) exige |δ| ≤ 0,0001 (`precio_coincide`) **y**
  `redondear_euros(can·precio) == redondear_euros(can·pre)`, en `Decimal` con `ROUND_HALF_UP`.
- `construir_dcapro_vinculada` decide con ella. `tot`/`ivacuo` salen de `importe_linea(cantidad, pre, iva)` con el
  `pre` escrito. Así la fila siempre es coherente, y `tot` siempre es igual a `round(cantidad·precio, 2)`: por la
  condición si se usa el precio del contrato, y por `pre = precio` si no.
- Casos límite del test: δ justo en 0,0001; δ dentro de tolerancia que mueve el céntimo (25.000 uds y 100 uds); δ
  diminuto con céntimo igual; devoluciones con signo; δ fuera de tolerancia con el céntimo igual (sale `False`);
  empate `ROUND_HALF_UP` con 1 ud.
- **El ejemplo del encargo (100 uds, 1,0495 frente a 1,0494) estaba mal y la regla es la de C, no la del ejemplo.**
  Lo he recalculado: 104,95 ≠ 104,94, así que C manda esa línea por `precio_distinto`. El test lo fija así y usa
  1,049402 para el par «100 uds ⇒ precio del contrato / 25.000 uds ⇒ precio distinto». Es correcto.
- Fila de 25.000 uds: `pre` = `tar` = 1,0495, `dto` `''`, `tot` 26.237,50 (el importe aprobado). Fila de 100 uds:
  `pre` 1,0494, `tar`/`dto` del `ctrpro`, `tot` 104,94 e `ivacuo` 22,04.

**Condiciones para el reviewer del lote C** (no bloquean este trozo):
- (a) El aviso `precio_distinto_del_contrato` debe usar `usa_precio_del_contrato` y no `precio_coincide`, que sigue
  siendo pública. El informe se compromete a ello.
- (b) `mov.pre` y el balance se calculan con el `pre` **escrito** en la fila.
- (c) Siguen pendientes O3 (`tipmov` y `dcapro.prepma` = `mov.prepma`) y O2 (diferencias en §Equivalencia, que la v8.2
  ya recoge según `current.md`).

## Pasada 1 (resumen)

**Verificación:** `init.sh` en verde (`2110 passed`, cobertura 517/517). RED de T5 reproducida (`65 failed, 4 passed`).
`git diff dev` vacío en el clásico, `albaran-directo`, `infrastructure/security/`, `function_app.py` y `.env`. Dorado intacto.
| Regla | Código (líneas de la pasada 1, salvo `siguiente_balance`) | Veredicto |
|---|---|---|
| `siguiente_cod`, `prefijo_de_serie` (R22, R26) | `albaran_compra_statements.py:186-194` | OK. Sin ceros a la izquierda, como `AC26/15950` |
| `siguiente_balance` (R19): `almcan`, `almpma` sin redondear, `prepma` = PMP de partida, `(0, 0)` sin `mov` | `:269-288` | OK. Con residuo binario fallaba en la pasada 1; **resuelto en la pasada 2** (ε) |
| `encadenar_balances` por (producto, almacén); regla A (R18, M5) con stock final negativo | `:261-278`, `:654` | OK. 5 líneas con 3 pares, `prepma(n) = almpma(n-1)` |
| `sufijo_analitica` / `codigo_analitica` (R15, M16d) | `:284-297` | OK. Quita un solo `MOD.`; `CD.SB37` queda entero; vacío ⇒ `None`; `RTRIM` de la obra |
| `estados_contrato` (R20), también con `Σcanser` < 0 y sumas `NULL` | `:304-314` | OK. A 2 decimales, como el clásico (`9,999` cuenta como servido) |
| `importe_linea`, `redondear_euros` (R17, H33) | `:197-226` | OK. `Decimal(repr)` y `ROUND_HALF_UP`: 2,675 da 2,68 y 1,005 da 1,01. IVA en fracción (M11) |
| `con` (R11, R22): `tip` 14, `emp` de la obra, `est` 1, `res` a 128 | `:399-414` | OK |
| `dca` (R21, H16): overrides del clásico solo sobre columnas existentes, `ctride` (0 sin contrato), `synckey`, bancarias escritas | `:417-461` | OK |
| `dcapro` vinculada (R12, R16, R17, H35, decisión 10) | `:473-544` | OK. `caaide`, `cod2`, `dncide` y `dncproide` salen del `ctrpro` (`''`/0 si faltan), nunca de la plantilla. `paride` es el pedido |
| `dcapro` sin vincular (R13, R13b, §Reseteo, R30c) | `:547-607` | OK. Aplica el §Reseteo completo (`cod2` vacío, DNC a 0, `tex` vacío, `fec` 0). Toma `natide`, `cueide` y `caaide` de los parámetros (el mapeo). Pone `docori*`, `canoriori` e `imporiori` a 0, `pre` = `tar` = `precio`, `dto` `''`, y `paride` es el resuelto |
| `ctrprodes` (M6, `can` con signo); `mov` (R19, N1: `emp` = `con.emp`, fecha del alta, `prepma` de partida); `log` (M13: `est` 1, `ori` 0) | `:610-685` | OK. `log` igual que F-006 |
| `numerar` (R25, R27): reentrante; `lindeside`/`linide` apuntan a su `dcapro` aunque haya sin vincular intercaladas | `:715-761` | OK. Corrige el 1:1 implícito del clásico |

**Decisión 11 (cambio 1, ya resuelto).** `almcan`/`almpma` son «Real» en Sigrid. Con `0.1 + 0.2` y luego `-0.3` a otro
precio, la comparación exacta `== 0` daba `almpma = -2.7e15`, que se encadenaba como `prepma` de la línea siguiente.

**Decisión 1 (resuelta por el humano: opción C).** Las fuentes discrepaban: R17 y el contrato §2.2 decían
`cantidad·precio`; design y el contrato §3.1, `cantidad·pre`. La diferencia llega a |cantidad|·0,0001 (2,50 € con
25.000 kg). Recomendé C: el precio del contrato solo si el importe coincide al céntimo.

## Checkpoints (pasada 2: se mantienen; C4 bis con RED y cobertura del ciclo 1 verificadas)

- **C1** [x] `init.sh` en verde y ficheros del arnés. **C2** [x] una `in_progress`, rama correcta, `current.md` al día,
  `history.md` (sin `done` nueva).
- **C3** [x] hexagonal (`application/`; los guardias importados son de T4 y siguen el precedente de F-004/F-006) ·
  [x] ruta en la primera línea · [x] sin `print`, TODO ni secretos · [x] `cod`/`res`/`fec`/`tip`/`est` en `con` ·
  [x] totales, `canser`/`estser` y `mov`/PMP con función propia (cableado en el lote C) · [x] `est` contra `conest` (L13).
- **C3 bis** N/A: sin documentos externos. **C4** [x] cada regla de T5-T6 tiene test (tabla) · [x] sin red ni BBDD ·
  [x] manuales T19-T24 listados.
- **C4 bis** [x] `rigor` declarado · [x] RED de T5 con salida real y reproducida (R15, R17, R18, R19). T6 no tiene RED
  en R34 · [x] cobertura 100 % (517/517) · N/A mutación, RM1-RM6 y las demás casillas de campaña: T16, lote E, plan
  aprobado (ver cabecera) · [x] «Evidencias» con los cuatro números (mutación «no medido», con su motivo).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`. **C5** [x] T5 y T6 `[x]` con commits `F-009 T5:`/`T6:` ·
  N/A el resto de `tasks.md` (feature abierta) · N/A sin trackear: el `` `0`].{t `` vacío de la raíz es del 2026-09-24,
  anterior y ajeno al lote (que lo borre el humano) · [x] `features.json` al día.

## Cobertura (requisito → tests de `tests/test_f009_statements.py`; pasada 2 añade `r19_residuo_*`, `r19_por_encima_*`,
`r19_encadenado_con_residuo_binario` y `r17_opcion_c_*` ×4)

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

Ninguno en la pasada 2. El de la pasada 1 (ε en `siguiente_balance`) está resuelto en `2a007f6`.

## Observaciones (no bloquean; para el líder y el lote C)

- **O1.** La vinculada hereda de su plantilla las columnas del §Reseteo (`med`, `canmed`, `fec`, `item`, `anexo`…): es la
  spec («como hoy», M14, R33), pero conviene mirarlo en la UI en T22.
- **O2.** Diferencias con el clásico que no están declaradas en §Equivalencia (R33/T12): `con.res` se recorta a 128
  aquí y a 200 en el clásico; y con stock final 0 el clásico usa `pre` y aquí se conserva el PMP. Hay que declararlas o
  evitarlas en el dato fijo de T12.
- **O3.** T6 está `[x]`, pero «`mov` si y solo si `tipmov` = 1» y «`dcapro.prepma` = `mov.prepma` o 0» los decide el
  caso de uso: los constructores reciben `prepma` por parámetro. El reviewer del lote C debe exigir esos tests (R19,
  R21) en T7/T10.
- **O4.** La RED de T6 del informe (`32 failed, 85 deselected`) no coincide con la reproducida (`31 failed, 86
  deselected`); será un estado intermedio. T6 no exige RED: no bloquea.

**Automejora (propuesta, no aplicada).** En `CHECKPOINTS.md` C3, trampas de Sigrid: «los campos “Real” (`almcan`,
`almpma`, `can`) se comparan con tolerancia, nunca con `== 0`»; el clásico tiene el mismo fallo (`if stock_new`).
