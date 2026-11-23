<!-- progress/review_F-008_logica_lectura.md -->
Revisión completa (pasada 1) del trozo `logica-lectura`: `git diff ccfb334...HEAD`, HEAD `2879ddb`.

# F-008 · Revisión troceada (T21) · Lógica de lectura y validación (R1-R35)

**Veredicto: CHANGES_REQUESTED** (1 defecto de comportamiento, 1 de orden/documentación; ver «Cambios requeridos»).

**Nivel de rigor:** `critico` (declarado en `harness/features.json`). En este trozo se exige trazabilidad R→test
con tests que fallarían si se rompe la regla; RED, cobertura y mutación son de otros revisores.

## Alcance y método

- Secciones de `requirements.md`: Entrada/llaves/llamantes (R1-R8), Serie/proveedor/obra (R9-R12), Orígenes
  (R13-R17), Modo (R18-R22), Líneas sin origen (R23-R28), Importes y retención (R29-R31), Vencimientos (R32-R35),
  con `design.md` §6-§7 y las «Decisiones»/«Desviaciones» de `progress/impl_F-008.md` que las tocan.
- Código leído entero: `domain/models/factura_models.py`, `application/use_cases/factura_lineas.py`,
  `create_factura_use_case.py` (l. 1-850: previa, validación y montaje), constantes LF1-LF17 y constructores de
  `factura_statements.py`, la ruta `sigrid/factura` de `function_app.py`.
- Ejecutado: `pytest tests/test_f008_models.py tests/test_f008_lineas.py tests/test_f008_use_case.py
  tests/test_f008_route.py` → **229 passed**. Sin `init.sh` ni suite completa (regla de convivencia).
- Sondas propias sobre el doble `tests/f008_dobles.py`, en el scratchpad (sin red, sin tocar el árbol): S1-S6 abajo.

## Fuera de este trozo (N/A con motivo)

- C1, C2, C3, C3 bis, C4 bis, C5, fase RED, cobertura, mutación (RM1-RM6), docs: **N/A**, asignados a otros
  revisores por el encargo T21 troceado.
- R36-R48 (transacción, escrituras, marcas, idempotencia, respuesta, traza, compatibilidad): **N/A**, otro revisor.
  Solo he mirado de ellos lo imprescindible para entender el orden de validación.

## Trazabilidad requisito → test (todos los tests citados pasan)

| R | ¿Se cumple? | Test que lo prueba (fichero `tests/test_f008_*`) |
|---|---|---|
| R1 | Sí: `extra="forbid"`, números `strict`, 400 propio sin `input` | `models` (estrictos, extra), `route` (400 sin eco) |
| R2 | Sí (`_coherencia`) | `models` (sin orígenes ni líneas, origen sin orígenes, repetidos, `a_origen` en mes) |
| R3 | Sí | `use_case::r3_la_previa_solo_lee` y toda previa (`repo.transaccion is None`) |
| R4-R5 | Sí (ruta + `_comprobar_guardas`) | `route`, `use_case::r5_commit_exige_todas_las_llaves`, `r5_base_no_permitida` |
| R6 | Sí; lista vacía no admite | `use_case::r6_*` |
| R7 | Sí | `use_case::r7_usuario_no_valido` |
| R8 | Sí, también contando las de origen (`_montar`) | `use_case::r8_*` (dos) |
| R9 | Sí: FR 5 cifras REC, FRGG 4 cifras RECGG | `use_case::r9_*`, `statements` (prefijo y cifras) |
| R10 | Sí | `use_case::r10_proveedor_no_encontrado/_ambiguo` |
| R11 | Sí | `use_case::r11_*`, `r11_r13_varias_obras` |
| R12 | Sí, en las dos series | `lineas::r12_*`, `use_case::r12_*` (tres) |
| R13 | Sí | `use_case::r13_*` (cinco) |
| R14 | Sí: estado CON y asiento `tip 20` | `use_case::r14_*`, `transaccion` |
| R15-R16 | Sí | `use_case::r15_*` (dos) |
| R17 | Sí, copia literal sin recalcular | `lineas::r17_*` |
| R18 | Sí | `use_case::r18_modo_no_coincide_y_modos_distintos` |
| R19-R20 | Sí: las cuatro clases de M63, en `Decimal`, nulos a 0 | `lineas::r19_*`, `r20_*` (siete) |
| R21-R22 | Sí: tolerancias ±0,001/±0,01 con borde | `lineas::r21_*`, `r22_*` (incl. `en_el_borde`) |
| R23 | **Parcial** — ver cambio 1 | `models` (campos por serie, negativos) |
| R24 | Sí; NDED solo cambia `ivaide` | `lineas::r24_*`, `p21_*`, `use_case::r24_*` |
| R25 | **Parcial** — `paride` sin `partida` (cambio 1) | `lineas::r25_*` (nueve), `use_case::r25_*` |
| R26-R27 | Sí: hoja `niv` 5, prefijo, analítica hoja con obra | `lineas::r26_*`, `r27_*` |
| R28 | Sí: un constructor, HALF_UP | `lineas::r28_*` (seis) |
| R29 | Sí | `statements` (totales), `use_case` previas |
| R30 | Sí: ±0,01/0,05/0,05 con borde; abono | `use_case::r30_*` (tres) |
| R31 | Sí: una retención igual en todos, `cuo` = round(`bas`·`valpor`) (fracción, como F-015) | `use_case::r31_*` |
| R32-R33 | Sí: 730 sí/731 no, repetidas, suma en `Decimal` ±0,01 | `lineas::r33_*` (ocho), `use_case::r33_*` |
| R34 | Sí | `use_case::r34_*` (dos), `lineas::r34_*` |
| R35 | Sí: no se mira `pagfor`/`pagdia`/`pagmes` | por construcción (`validar_vencimientos`) |

Sondas que confirman reglas: S2 `importe_linea(1, 2.675, 0.21)` = (2,68; 0,56) HALF_UP; S3 `total_base` +0,01
cuadra y +0,011 da `totales_no_cuadran`; S4 FRGG mixta (albarán + línea propia): origen con `cuepdtide` 4009 y
analítica del albarán, propia con cuenta 629, analítica `GG.GEN`, obra 9000 y centro 81 de su prefijo, `almide`
el de la `dcf` (R12, R27, P18 correctos).

## Desviaciones y decisiones del implementer que tocan este trozo

- «Idempotencia antes que orígenes»: correcta y bien motivada.
- «`retencion_no_soportada` antes que los totales»: **incompleta** (cambio 2).
- «`abono_no_soportado` antes de comparar totales»: aceptada; tiene test.
- «Orígenes en la empresa de la obra o en las admitidas; si un código está en varias, `origen_no_encontrado` con
  pista»: aceptada; conservadora.
- Desviación 2 (`linea_sin_origen` sin `tasa_iva`): aceptada, la tasa viaja en `LineaResuelta`.

## Cambios requeridos

1. **`paride` sin `partida` en una línea FR se descarta en silencio** (R23, R25 → F-009 R14b).
   - Dónde: `application/use_cases/factura_lineas.py:399-400` (`resolver_partida` devuelve 0 si `partida` es
     `None`, sin mirar `paride`) y `domain/models/factura_models.py:117-131` / `_coherencia` (l. 167-188), que no
     tienen el validador de F-009 (`domain/models/albaran_compra_models.py:280-281`: «'paride' solo va con
     'partida'», 400).
   - Escenario (sonda S1): línea FR `{"producto": "MA9999", "paride": 355}` sin `partida` → previa **OK** con
     `dcfpro.paride` = 0. El llamante pidió imputar a la partida 355 y la factura se graba sin partida, sin
     error ni aviso. R25 manda aplicar «las reglas de F-009 … R14b y sus mismos fallos»; en F-009 ese cuerpo es 400.
   - Cambio: en `_coherencia` (o en `LineaSinOrigen`), `paride` sin `partida` → `ValueError` (400 sin `codigo`,
     R1), y un test en `tests/test_f008_models.py` que lo pruebe (y que falle si se quita la regla).
2. **El orden real de `retencion_no_soportada` no es el de design §7 ni el que declara el informe.**
   - Dónde: `application/use_cases/create_factura_use_case.py:282` llama a `_retencion` en el paso 5, antes de
     las líneas de origen (R15), `a_origen` (R21-R22) y las líneas sin origen (R24). La desviación de
     `impl_F-008.md` dice solo «antes que los totales».
   - Escenario (sonda S5): origen con una línea ya facturada **y** una retención con `valfij` → responde
     `retencion_no_soportada`, no `origen_ya_facturado`. Ningún `test_f008_orden_*` fija la posición.
   - Cambio (a elegir): mover la llamada a `_retencion` justo antes de `_montar` (tras `_sin_origen`; solo
     necesita `origenes`), que es lo que dice la desviación, **o** corregir el texto de la desviación con el
     alcance real. En los dos casos, añadir un `test_f008_orden_*` que fije la posición elegida.

## Observaciones (no bloquean; decisión del humano)

- **O1 · Origen sin ninguna línea facturable** (sonda S6): un origen cuyas líneas son todas `can` 0, junto a otro
  con líneas, pasa con 0 líneas (`origenes[1].lineas` = 0), y en el commit R41 lo pasaría a FAC y `estfac` 1 sin
  `dcaprodes`. La spec (R16) no lo prohíbe ni lo mide. Propuesta: confirmar con el humano o rechazarlo
  (`origen_sin_lineas`), porque marcar facturado un albarán del que no se ha facturado nada no es reversible por API.
- **O2 · Orden de las guardas sin base**: `_comprobar_guardas` (l. 313-345) comprueba `demasiadas_lineas` →
  prefijo → llaves, y design §7 dice llaves → prefijo. Sin efecto real (no hay lecturas antes y la ruta ya aplica
  R4), pero conviene alinear texto o código cuando se toque el cambio 2.
- **O3 · FR sin origen en obra sin almacén en su ficha**: la `dcf.almide` sale 0 (de la obra, l. 550) mientras
  la línea toma el único `alm` de la obra (`_almacen`, l. 733-744). Es cabecera (otro revisor); lo dejo anotado
  para quien revise `construir_dcf`.

## Propuesta de automejora (no aplicada)

- `CHECKPOINTS.md`/reviewer: cuando una feature «reutiliza las reglas de F-0xx», exigir que el reviewer compare
  también los **validadores de modelo** de esa feature, no solo las funciones importadas: aquí la regla R14b de
  F-009 vivía en el modelo y por eso no viajó con `resolver_partida`.
