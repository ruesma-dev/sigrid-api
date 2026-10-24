<!-- progress/review_F-015_C4red.md -->
Revisión completa (pasada 1) de `dev...e42e0ad`, acotada a C4 y a la parte de C4 bis sobre fase RED y cobertura

# Review F-015 · bloque C4 + C4 bis (RED y cobertura)

**Veredicto del bloque: CAMBIOS.** Un único hallazgo, documental (H1): las verificaciones MANUAL de R29 no tienen
comando exacto en ningún sitio. El código y los tests de este bloque están bien: fase RED reproducida por mí en las
12 R de R27, cobertura 100 % de 237 reproducida, cada R con un test que aserta valores.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Este bloque exige tests trazables por R sin red
ni BBDD, MANUAL con comando exacto, fase RED con salida real y cobertura de las líneas cambiadas ≥ 80 %.

**Lo que NO se ejecutó, por orden del encargo:** ni `bash harness/init.sh` ni la suite completa (corren otros
reviewers). Nada contra Sigrid. Ejecuté solo los tests de F-015 y F-009 (**806 passed**, 22 s), y las RED sobre
copias en el scratchpad. El árbol queda limpio: `git status` solo muestra los informes de los otros reviewers.

## C4 — La verificación es real

- [x] **Cada R tiene ≥ 1 test trazable y todos pasan.** Ver la tabla. Hay tres R sin `test_f015_rN_*` propio, todas
  justificadas: R2 la fija el centinela de R25 (docstring «R2, R25», T5); R11, el dorado de F-009, que no cambia
  (`git diff dev` de los 7 ficheros de T15: **vacío**, medido); R27 es esta revisión. R28 es documental (otro
  bloque); R29 y R30 son MANUAL.
- [x] **Los unit tests no tocan red ni BBDD.** `f009_dobles.py` solo importa `application.*` y la stdlib. Los
  tests de F-015 usan `RepositorioDoble` y funciones puras. No hay `pyodbc`, `socket`, `requests` ni `httpx`.
- [ ] **MANUAL listadas con su comando exacto.** → **H1.**

## C4 bis — fase RED y cobertura (lo demás de C4 bis es de otro bloque)

- [x] **Rigor declarado**: `critico`.
- [x] **Fase RED con salida real en R1, R2, R3, R5, R6, R7, R9, R12, R14, R15, R21 y R23.** Tests y código van en
  el mismo commit en cada tarea, así que `git log -p` no puede probar el orden. Lo comprobé **reconstruyendo** cada
  RED: árbol del commit C, con los ficheros de producción de `C^` y los tests de C, en el scratchpad. Ejecuté el
  mismo `-k` que la traza:

| Tarea (commit) | R | Resultado reproducido | ¿Cuadra con `red_F-015.md`? |
|---|---|---|---|
| T2 `7f4c488` | R1, R9 | 7 failed (`DCA_COLUMNAS`, `DCA_FIJAS`…) | sí, los mismos 7 tests |
| T3 `e7bc324` | R6, R7 | 5 failed; L5 falla **por el SQL** (faltan `cod LIKE`/`cla`/`PROF`) | sí |
| T5 `e7b6c1f` | R2, R3, R5, R9 | 35 failed, 4 passed: 30 `TypeError` + 5 `pago_del_proveedor` | sí, exacto |
| T6 `7e0300d` | R1 | 6 failed, 15 passed (diferencias de SQL y `DID NOT RAISE`) | sí, exacto |
| T7 `6743724` (caso de uso de `C^`) | R3, R5, R6, R7 | 21 `TypeError` + 5 `proveedor_sin_albaran_previo` + 1 regex | sí |
| T9 `12247ff` | R12, R14 | 12 failed | sí (la traza omite 2 líneas sueltas) |
| T10 `a0345d9` | R15 | **9** failed, 7 `calcular_retencion` | **casi**: ver O1 |
| T12 `b4234d3` (los dos ficheros de `C^`) | R12, R14 | 28 failed, 19 passed, 12 `DID NOT RAISE` | sí, exacto |
| T13 `8166ed6` sentencias | R21, R23 | 8 failed, 2 passed | sí, exacto |
| T13 `8166ed6` caso de uso de `C^` | R21, R23 | 8 failed: 6 `ide_dcarec`, 1 `[[2900011]]`, 1 `DID NOT RAISE` | sí, exacto |
| T18 `97c4e8b` | R12 (dos `dcarec`) | 1 failed `DID NOT RAISE ValueError` | sí |

  Las RED de R3 y R6 en el caso de uso (T7), y la de R5, fallan por la firma: `construir_con` y `construir_dca`
  cambian de API. Es lo esperable en TDD de una API nueva. Además, R6 tiene RED **de comportamiento** en T3 (el SQL),
  R1 en T6 y R14/R23 en T12/T13 (`DID NOT RAISE`).
- [x] **Cobertura**: medida por mi cuenta con `coverage run -m pytest` (F-015 + F-009, `COVERAGE_FILE` y JSON en el
  scratchpad) y `python -m harness.cobertura --base dev --cov <scratch>/cov_f015.json`. Resultado:
  `PUERTA COBERTURA: 100.0% de 237 líneas cambiadas cubiertas (237/237, umbral 80%, nivel critico)`, **igual a lo
  declarado**. El alcance son los 4 ficheros de producción previstos: `albaran_compra_statements.py`,
  `create_albaran_compra_use_case.py`, `albaran_compra_models.py` y `function_app.py` (solo docstring).

## Cobertura requisito → test (lo que fija el valor)

| R | Test(s) que lo fijan (prefijo `test_f015_`) |
|---|---|
| R1 | `r1_dca_columnas_son_las_145…` (tupla literal de la spec), `r1_origen_dca_cubre…` (6/15/18/106), `r1_insert_de_dca_con_sus_145…` (SQL carácter a carácter), `r1_una_fila_de_cabecera_que_no_cuadra…` |
| R2 | `r25_centinela_*` ×3: ninguna columna fuera de identidad/cascada lleva un valor leído |
| R3 | 17 `r3_*`: vaciado contrato→respaldo y →prv por columna, grupos pago/banco, `None` y espacios como vacío, `ivadif` |
| R4 | `r4_identidad_del_contrato_aunque_venga_vacia`, `r4_con_contrato…`, `r25_…del_proveedor` (nombres `raz`, `tipcif`…) |
| R5 | `r5_sin_fuente_el_vacio…` (valor y columnas), `r5_banco_sin_fuente…avisa` (texto exacto, `CC`/`CT`/`TR`/` cc `), `…no_avisa` (`P`/`R`/`''`) |
| R6 | `r6_sql_l5_*` (SQL y `[14,1,77,"AC__/%",0,"PROF%"]`), `r6_sin_respaldo_el_alta_sigue…` (`template_ide` 0) |
| R7 | `r7_sql_l17…`, `r7_sin_proveedor_unico…` (`no_encontrado`/`ambiguo`, sin lecturas de más), `r7_…el_prv_unico_del_cif` |
| R8 | `r8_calculadas…` (las 18 con su valor), `r8_con_exactamente…` (19), `r8_con_sellos_con_tiemod…`, `r8_diremp1…` |
| R9 | `r9_fijas_valor_del_alta_a_mano` (valor **y tipo**), `r9_fijas_en_la_fila_aunque_todas_las_filas_las_traigan` |
| R10 | `r10_columna_que_falta…` (statements, 5 casos), `r10_columna_ausente_falla_sin_escribir` (sin `peek` ni transacción) |
| R11 | `test_f009_caracterizacion.py` (dorado intacto) + diff de T15 vacío |
| R12 | `r12_contrato_con_ret5_escribe_una_dcarec` (fila entera), `r12_sin_contrato_no_se_lee_l16`, `r12_en_devolucion…` (−1,05) |
| R13 | `r13_dcarec_copia_del_ctrrec…` (21 columnas con valor), `r13_tot_y_totpag_netos…`, `r13_tot_neto_sin_error_binario` |
| R14 | `r14_ctrrec_no_soportado` ×6, `r14_retencion_no_soportada_400_antes_de_las_lineas` ×12 (dry-run y commit, sin `tipmov`) |
| R15 | `r15_empate_a_medio_centimo…` (188,77 y −188,77), `r15_en_decimal…` (1,08), `r15_base_por_clase…` (3, 4, 5) |
| R16 | `r16_aviso…previa` y `…otro_porcentaje` (mensaje literal), `r16_sin_retencion_no_hay_aviso` |
| R17 | `r17_totales_con_retencion` (dict entero), `…en_el_alta…`, `r3_la_respuesta_lleva_lo_escrito_sin_las_bancarias` |
| R18 | `r18_sql_l11_con_el_tot`, `r18_idempotente_tot_y_retenciones…` (188,77 exacto, sin leer L16) |
| R19 | `r19_la_traza_cuenta…sin_importes` (busca 1.05, 0.05, RET5, PAGARE en el texto), `…sin_retencion_dice_0`, `…de_un_error…` |
| R20 | `r20_previa_numera_la_dcarec_con_peek_sin_reservar`, `r20_numerar_*` ×3 |
| R21 | `r21_con_retencion_e6b_tras_e6…` (secuencia entera y applocks), `r21_sql_e6b…`, `r21_lo_insertado…`, `r21_sin_retencion…` |
| R22 | `r22_el_reintento_recalcula_el_ide…` (44101→44102 con su `docide`) |
| R23 | `r23_relectura_de_dcarec_distinta_revierte` (0/2 con retención, 1 sin ella), `r23_sql_e12…` |
| R24 | `r24_control_negativo…` (47 sentencias, solo 2 `UPDATE` previos, solo el `''` de L5), `r24_las_sentencias_nuevas…` |
| R25 | `r25_centinela_*` ×3 (con contrato; sin contrato con respaldo; solo proveedor) + vaciados de R3 |
| R26 | `test_f015_r26_con_ctrrec…` y las dos `test_f009_r33_*`, con el conjunto de diferencias **exacto** (`_DCA_DISTINTAS`) |

No hay ningún test tautológico en los R de F-015. La única comparación consigo mismo es el mensaje de
`cod_provisional`, que es de F-009 (`test_f015_use_case.py:276`). Los ajustes de los tests de F-009 (T14) no
debilitan nada: donde antes había clon ahora se aserta el valor de la lista, y los `insertar_con`/`_dca` antiguos
pasan a esperar `ValueError`.

## Hallazgos

- **H1 (C4, tercer punto; bloquea).** R29 (T19 y T20) no tiene comando exacto en ningún sitio:
  - `progress/current.md:15-16` solo dice «Quedan T19-T21 MANUALES».
  - `tasks.md` T19 solo dice «`Invoke-RestMethod` a `/api/sigrid/albaran` con `commit:false`».
  - Design no tiene §Verificación manual. Para T21 sí vale design §Limpieza (`design.md:174-189`): SQL y parámetros
    exactos, el mismo criterio aceptado en F-010 y F-011.

  **Cambio requerido** (solo papeleo, sin tocar código): añadir una §Verificación manual en `design.md`, enlazada
  desde `current.md`, o ponerla directamente en `current.md`. Debe llevar:
  1. El `Invoke-RestMethod` literal de los cuatro dry-runs de R29: URL, cabecera `x-functions-key` como variable
     (sin el valor) y cuerpo JSON con `commit:false`. Casos: un contrato concreto con `RET5`, uno sin `ctrrec`, un
     albarán sin contrato y un proveedor sin respaldo, cada uno con su obra, CIF y referencia.
  2. Qué mirar en la respuesta de cada uno.
  3. Para T20, la secuencia exacta (`commit:true`, repetir para `idempotente`) y las lecturas `sql/read` que
     comprueban que tras la anulación no queda `con` ni `dcarec` con su `docide`.

## Observaciones (no bloquean)

- **O1.** La traza RED de T10 (`red_F-015.md`, §T10) es de una versión anterior del fichero de tests: declara «8
  failed» y una línea `assert 188.77 == 188.76`. Esa línea era un fallo del propio test: `round(3775.30*0.05, 2)`
  da 188,77 en Python, no 188,76 (lo medí). El test se reescribió luego con 21,50 · 0,05 (`r15_en_decimal…`). La
  RED de R15 es real: con el test commiteado fallan 9 de 9, todos por `calcular_retencion` o `construir_dcarec`
  ausentes. Pero la traza pegada no es la que se reproduce. Para la próxima vez: si un test cambia tras su RED,
  repetir la RED.
- **O2.** R25 pide el centinela «con y sin contrato, con y sin respaldo». Hay 3 de las 4 combinaciones: falta **con
  contrato y sin respaldo**, la cascada contrato → `prv` directa, que es el caso real de un proveedor sin albarán
  previo. Su comportamiento sí está fijado por `test_f015_r6_sin_respaldo_el_alta_sigue_con_contrato_y_proveedor`
  (pago, `cueide`, `dirdir1`) y la campaña lo mata todo, así que no bloquea. Un cuarto centinela
  `_dca(_contrato(), None, …)` cerraría la letra de R25.
- **O3.** T7 y la segunda mitad de T13 se reprodujeron con solo el caso de uso en `C^` (las sentencias, de C). La
  traza de T7 lo declara; la de T13b no. Conviene escribirlo en la cabecera de cada traza RED.

## Automejora (propuesta, no aplicada)

- **`CHECKPOINTS.md` C4 bis, fase RED.** Cuando tests y código van en el mismo commit (lo normal aquí), la traza
  RED solo se puede contrastar reconstruyendo el árbol (`git archive C`, más los ficheros de producción de `C^`).
  Propongo que la traza RED declare, para cada bloque, **qué ficheros de producción estaban en el padre**. Así el
  reviewer la reproduce con un comando y no tiene que deducirlo.
- **`CHECKPOINTS.md` C4, tercer punto.** Repito la propuesta de F-010 y F-011, aún sin decidir: aceptar por escrito
  «MANUAL en `current.md` o enlazadas desde ahí a la §Verificación manual del design».
