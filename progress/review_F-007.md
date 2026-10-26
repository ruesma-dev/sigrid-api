<!-- progress/review_F-007.md -->
Revisión incremental desde `30ca6b0` (pasada 3), consolidado de las pasadas 1 (completa, `dev...fe85523`), 2 (`fe85523..765f273`) y 3 (`30ca6b0..0f053da`)

# F-007 · Registrar proforma · veredicto consolidado

- **Veredicto: APPROVED** para merge a `dev`, contra `CHECKPOINTS.md` y la spec v3.1 con las enmiendas 1 y 2.
- **La feature NO pasa a `done` todavía.** Faltan las tareas MANUALES T20-T22 (ver «Lo que este veredicto no cubre»).
- **Nivel de rigor: `critico`**, el declarado en `harness/features.json`. Exige fase RED con salida real, cobertura
  ≥ 80 % de lo cambiado, campaña de mutación con cero supervivientes salvo aceptación escrita del humano, RM1-RM6 y
  RM5 (reproducir un equivalente).
- **HEAD aprobado: `0f053da`.** Entre `765f273` y `0f053da` solo entran informes y documentación (pasada 3). Nada se
  lanzó contra Sigrid ni contra la API desplegada.

## Informes que se resumen

| Pasada | Bloque | Veredicto del bloque |
|---|---|---|
| 1 | [`C1C2C5`](review_F-007_C1C2C5.md) · [`C3C4ter`](review_F-007_C3C4ter.md) · [`C4red`](review_F-007_C4red.md) | CR (H1, H2) · APPROVED · CR (H1) |
| 1 | [`mutacion`](review_F-007_mutacion.md) · [`nucleo`](review_F-007_nucleo.md) · [`proforma`](review_F-007_proforma.md) | CR (1-3) · APPROVED · CR (D1-D5) |
| 2 | [`proforma_p2`](review_F-007_proforma_p2.md) · [`C_p2`](review_F-007_C_p2.md) · [`nucleo_mutacion_p2`](review_F-007_nucleo_mutacion_p2.md) | CR, solo documentación (N1 · N1-N2 · 1-2) |
| 3 | [`p3`](review_F-007_p3.md) | APPROVED: la enmienda 2 cierra todo lo de la pasada 2 |

## Checkpoints

| Checkpoint | Estado | Evidencia (detalle en el informe enlazado) |
|---|---|---|
| **C1** arnés completo y en verde | [x] | `init.sh` sobre `0f053da`, exit 0: `3393 passed, 1 skipped`; COBERTURA 100,0 % (736/736); TAMAÑO OK (150/150, 249/250, 176/220) |
| **C2** estado coherente | [x] | Una sola `in_progress` (F-007), F-015 `blocked` con motivo. `current.md` y la descripción de F-007 se reescribieron (H1/H2, T38). Rama correcta |
| **C3** arquitectura y convenciones | [x] | Hexagonal; primera línea con ruta; LP1-LP6 constantes, `?` y guardia de bases; sin DML/DDL nuevos; traza R33 sin datos (C3C4ter) |
| **C3 bis** documentos de fuera | [x] | 6 en `docs/referencia/` con cabecera; sin originales en el historial; barrido de secretos y personas limpio; autorización de las hojas con precios en `impl_F-007.md:27-28` |
| **C4** verificación real | [x] | R1-R34 con tests `test_f007_rN_*` en verde; sin red ni `pyodbc` (medido en p1 con `socket`/`pyodbc` bloqueados); MANUAL con comando exacto en `verificacion_manual.md`, enlazado desde `current.md:19-20` (D2 y V1 corregidos en p3) |
| **C4 bis** fase RED | [x] | Salida real en el informe; reproducida en las 8 tareas de la pasada 1 y en T29/T33 de las correcciones (worktrees borrados) |
| **C4 bis** cobertura | [x] | PUERTA `[OK]` 100,0 %, recalculada aparte en la pasada 1 (710/710; ahora 736/736) |
| **C4 bis** mutación | [x] | 381 mutantes, 376 muertos, 5 supervivientes, 0 sin aceptar (`mutacion_F-007.md`). La campaña no se reejecutó (78 min según el informe): RM4 con 23/23 mutantes manuales medidos en p2, más A1-A5, S1-S5, N1-N16 y P1-P7 |
| **C4 bis** RM1-RM6 | [x] | RM1: se midió `4a94da0` y después solo cambiaron G1-G4 (medidas, mueren). RM2: 381 × 12,3 ≈ 4674 s. RM3: ningún equivalente sale muerto. RM5: R2-1 `cifras: int = 0` reproducido y aceptado por el humano (2026-10-26). RM6: guardas en el origen del dato verificadas |
| **C4 ter** rutas sensibles | N/A | Justificado: no existe `harness/rutas_sensibles.json`, así que `init.sh` no evalúa la puerta. El diff no toca `infrastructure/` (0 líneas) |
| **C5** `tasks.md` y commits | [x]* | T0-T19 y T25-T40 `[x]`, con commit `F-007 Tn:` cada una y RED/verde separados. *Siguen abiertas, por diseño, T20-T22 (MANUAL, después del merge), T23 (esta revisión) y T24 (el `init.sh` final, ya verde aquí). Bloquean el `done`, no el veredicto: es el criterio aceptado por el humano en F-010, F-011 y F-015 |
| **C5** sin temporales · `features.json` | [x] | `git status` limpio; ningún worktree de revisión vivo; `in_progress` es el estado real |

## Hallazgos y cómo se cerraron

| Hallazgo | Gravedad | Cierre |
|---|---|---|
| C1C2C5 H1 · `current.md` con partes falsas | bloqueaba | T38; resuelto en p2 |
| C1C2C5 H2 · descripción de F-007 atrasada | baja | T38 + `BACKLOG.md` regenerado; p2 |
| C4red H1 · MANUAL sin comando exacto | bloqueaba | T37 `verificacion_manual.md`; p2 lo dejó en parte (N1, N2) y se cerró en p3 |
| mutacion 1 · N7 (`setdefault`) sin test | real | T34; N7 muere (p2) |
| mutacion 2 · A1-A5, S1-S5 irreproducibles | bloqueaba | T36, tabla con texto exacto; los 10 reproducidos (p2); líneas corregidas en p3 |
| mutacion 3 · aceptación de `cifras: int = 0` | critico | Aceptado por el humano el 2026-10-26 (`mutacion_F-007.md`) |
| proforma D1 · R17 sin plantilla daba IVA 0 | media | T27-T28: IVA del `ctrpro`; el albarán no cambia (p2, diferencial 279/279) |
| proforma D2 · R28 no repetía R23 bajo el applock | baja | T29-T30: gancho con la fila de E1 antes del `return` idempotente; LP5 por el cursor |
| proforma D3 · idempotente de dentro con `origen` y avisos | baja | T29-T30: `origen` nulo, `avisos` `[]` |
| proforma D4 · `producto` + medición vinculada en silencio | baja | Enmienda 1 + T25-T26: R14 por partida y precio, estricto |
| proforma D5 · hora de Madrid sin test | baja | T31: bordes del mes y cambio de año |
| nucleo O1 / O3 · design corto; `Settings` único | obs. | design (p2) · `azure-apps` §8.10 y D1-D3 (dry-run de `sigrid/albaran` primero) |
| proforma O3, O4 · `otra_del_mes`; `entcif` | obs. | R24 v3.1 · T33 (`_cargar_contrato` y `proveedor_no_encontrado`) |
| C3C4ter obs. 1 · mensaje de la llave decía «albaranes» | obs. | T35 (`PerfilAlta.documentos`) |
| C4red O4 · residuo de R28 | obs. | Se cerró con la corrección de D2 |
| proforma_p2 N1 · §4 del contrato sin dos códigos | doc. | Enmienda 2: §4 completa frente a los 28 códigos (p3) |
| C_p2 N1-N4 · D2 en bash, mensaje de V1, `Lineas`, `dcarec` | doc. | Enmienda 2 (p3) |
| nucleo_mutacion_p2 1-3 · `design.md` frente a T33/T35 | doc. | Enmienda 2 (p3); O8 de proforma_p2 también |

## Trazabilidad requisito → test (detalle en `review_F-007_C4red.md`)

| Requisitos | Tests (`tests/test_f007_*`) |
|---|---|
| R1-R3, R10, R13, R30 | `models` (`r1_*`, `r2_*`, `r3_*`, `r10_*`, `r13_*`, `r30_*`) |
| R4-R6 | `settings` (42 casos), `route` (`r5_*`, `r6_*`) |
| R7-R9, R14 | `statements_contrato` (`r7_*`, `r8_*`, `r9_*`), `statements_lineas` (`r14_*` estrictos, de T25) |
| R11-R12, R15-R18 | `statements_lineas`, `use_case` (`r12_*`, `r15_*`, `r16_*`, `r17_*`, `r18_*` con hora de Madrid), `perfil` (IVA por `pos`) |
| R19-R24 | `statements_lineas` (`r19_*`-`r24_*`), `use_case` (`r23_*`, `r24_las_tres_hojas…`) |
| R25-R29 | `transaccion` (`r25_*`, `r27_*`, `r28_*` con LP5 dentro, `r29_*`), `use_case` (`r26_*`) |
| R31-R33 | `perfil` (`r31_*`) + F-009/F-015 intactos (816 passed, diferencial 279/279); `statements_contrato` (`r32_*`); `use_case` (`r33_*`) |
| R34 / R35-R36 | esta revisión / MANUAL (`verificacion_manual.md`) y documentación |

## Lo que este veredicto NO cubre

- **T20**: V8 con Administración (lista de productos sin contrato, contratos a origen) y la respuesta de `proformas`
  a design §Preguntas.
- **T21**: App Settings en JSON con la llave **cerrada**, despliegue (D2, lo lanza el humano con `!`), dry-run de
  `sigrid/albaran` primero y dry-runs de las tres hojas de la 0719.
- **T22**: **una** grabación `commit:true` autorizada por el humano para esa llamada, repetida (`idempotente`) y
  anulada desde la UI si es de prueba, nunca con `DELETE`.

Este veredicto no prueba nada contra el Sigrid real: ni la serie `PROF`, ni la `cla 141` en la ficha, ni el paso a
factura (V6). **F-007 sigue `in_progress` hasta que T20-T22 consten en `progress/verificacion_F-007.md` y T24 se
repita en verde.** Antes de desplegar hay que mandar los avisos a `proformas` (texto v1.1, `impl_F-007.md`), a
`facturas` y a albaranes. Los manda el líder.

## Observaciones abiertas (decisión del humano; ninguna bloquea)

- **O1** (proforma): `existente` pierde el aviso de línea `anterior_distinto_de_sigrid`, porque sus líneas son las
  de LP6.
- **O2** (proforma): en `existente`, `proide` 0, `referencia_linea` vacío y `ctrpro_ide` 0 (no `null`) en las no
  vinculadas. Fuera de lo que promete §3.
- **O5** (proforma): `fecha_proforma` posterior a hoy se admite si cae en el mes en curso. R18 no lo prohíbe.
- **O6** (proforma): con `otra_del_mes`, si la del mes aparece entre la previa y el commit, el aviso calculado dentro
  se descarta.
- **O7** (proforma_p2): si E1 encuentra la referencia en un documento de otro proveedor u obra, el mensaje dice
  «albaran(es)…» (`create_albaran_compra_use_case.py:660-664`). El código es correcto.
- **Automejora `setdefault`** (mutacion, p1): exigir en rigor `critico` un mutante manual «primera ↔ última» cuando
  el diff construye un diccionario con `setdefault` o `next(...)`. Va a `reviewer.md` y a `arnes-base`.

Menores, sin acción obligatoria:
- C4red O2: T11 cambió la entrada de dos tests de T10 sin anotarlo; los asertos no cambian.
- C4red O3: R26 (credenciales y base) solo lo cubre F-009.
- C3C4ter: el 500 devuelve `str(exc)` en las 10 rutas (heredado).
- nucleo O2: `PERFIL_ALBARAN.cla` es dato muerto.
- C_p2: la `acceptance` 2 nombra `SIGRID_DOMAIN_WRITE_ENABLED` y no la llave propia.

Para el líder: `current.md:205` todavía habla de la «pasada 2». Hay que ponerlo al día con este veredicto.

## Automejora (propuestas, no aplicadas; valen para `arnes-base`)

1. Cada bloque MANUAL dice en qué shell se teclea, y su «Se mira» copia el texto del código (C_p2).
2. La tarea que introduce un código nuevo para un consumidor toca en el mismo commit su tabla de códigos (proforma_p2).
3. `init.sh` avisa si el «Prompt para retomar» de `current.md` no nombra la feature `in_progress` (C1C2C5).
4. Declarar `infrastructure/security/**` en `harness/rutas_sensibles.json` de este repositorio (C3C4ter).
5. Revisión troceada: el consolidado debería poder citar por bloque el SHA aprobado, para que la pasada siguiente sea
   incremental sin reconstruirlo a mano.

## Cambios requeridos

Ninguno.
