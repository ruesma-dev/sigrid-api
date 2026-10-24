<!-- progress/review_F-015_retencion.md -->
Revisión completa (pasada 1), bloque RETENCIÓN y camino de COMMIT (R12-R26, D8), `dev...e42e0ad`

# F-015 · Revisión troceada: retención y commit

- **Veredicto del bloque: APROBADO** (sin hallazgos bloqueantes; 4 observaciones O1-O4).
- **Rigor:** `critico` (declarado). Este encargo cubre conformidad funcional; fase RED, cobertura y
  mutación son de otro bloque. RED de R12, R14, R15, R21 y R23 consta con salida real en
  `progress/impl_F-015.md` y `progress/red_F-015.md`.
- **Alcance:** R12-R24 contra el código, R25/R26 solo en lo de retención y F-009, R11 (dorado).
  No se ejecutaron `init.sh` ni la suite completa (corren otros reviewers en paralelo, como pedía el
  encargo). Nada contra Sigrid. Árbol limpio tras la revisión (`git status`: solo
  `review_F-015_C1C2C5.md`, de otro reviewer).

## Ejecutado

| Qué | Resultado |
|---|---|
| `pytest tests/test_f015_statements.py tests/test_f015_use_case.py tests/test_f009_equivalencia.py tests/test_f009_caracterizacion.py` | 187 passed |
| `pytest tests/test_f009_{statements,use_case,mutacion,route,models}.py` | 562 passed |
| Sonda propia (4 casos, fuera del repo: `C:\Users\pgris\AppData\Local\Temp\claude\C--Users-pgris-PycharmProjects-sigrid-api\2b5145bb-bc95-4386-b786-7860ca1437e3\scratchpad\probe\test_probe_retencion.py`) | 4 passed |
| `git diff dev --stat` del dorado, su test, los 4 intocables de F-009 R4, `parte_reclamacion_statements.py`, `infrastructure/`, `config/` | vacío |

Sonda: (a) devolución **solo sin vincular** con RET5 en commit: `totbas` −8,03, `cuo` −0,40,
`tot` = `totpag` = −9,32, sin `ctrprodes` ni E9-E11, E6b antes de los `INSERT`, `dcarec` tras
`dcapro`/`mov`; (b) `IntegrityError` en `insert_con` del intento 1: ninguna `dcarec` en ese intento,
la del 2 con `ide` 44102 y `docide` = el `con` nuevo, E12 con el `con` nuevo; (c) empates negativos
(clase 4 sobre `totdoc` −3.775,30 → −188,77; −0,005 → −0,01); (d) `idempotente` en commit con
`tot` neto 24,36 → `retenciones` 1,05 y sin `INSERT`.

## Conformidad requisito a requisito

| R | Código (`albaran_compra_statements.py` = S, `create_albaran_compra_use_case.py` = U) | Tests | |
|---|---|---|---|
| R12 | U:482-498 lee L16 solo con contrato; S:397-419 `None` sin filas | `r12_con_contrato_l16_tras_conest_y_usuario`, `r12_sin_contrato_no_se_lee_l16`, `r12_contrato_con_ret5…`, `r12_contrato_sin_ctrrec…`, `r12_en_devolucion…`, `r12_numerar_con_dos_dcarec…` | [x] |
| R13 | S:446-463 (13 copiadas del `ctrrec`, `bas`/`cuo`, 4 a 0); S:827 `tot` = `totdoc` − `cuo`, `totpag` = `tot` | `r13_dcarec_copia…`, `r13_tot_y_totpag_netos…` (incluye `cuo` negativo), `r13_tot_neto_sin_error_binario` | [x] |
| R14 | S:404-418 (varios, `recide` 0, sin `rec`, clase ∉ {3,4,5}, `valfij`, `ivaide`); U:299 tras L11/idempotencia y `conest`/`usu`, antes de `auxpag` y líneas | `r14_ctrrec_no_soportado` ×6, `r14_retencion_no_soportada_400_antes_de_las_lineas` ×12 (dry-run y commit), `r12_un_albaran_ya_escrito_es_idempotente_aunque_su_retencion_no_valga` | [x] |
| R15 | S:436-443: `bas` = `redondear_euros(totales[CLASES_RETENCION_BASE[cla]])`, `cuo` = `redondear_euros(bas · Decimal(repr(valpor)))`, `ROUND_HALF_UP` (lejos del cero en negativo) = M12 | `r15_base_por_clase…` (5, 3, 4), `r15_empate_a_medio_centimo_lejos_del_cero` (±188,77), `r15_en_decimal_no_en_binario`, `r15_totbas_0…`, `r15_otro_porcentaje` | [x] |
| R16 | U:1156-1163; tras los de cabecera | `r16_aviso…` ×3 | [x] |
| R17 | U:993-995 `tot` = `dca.tot`, `retenciones` = `cuo`, `n_retenciones`; `filas.dcarec` | `r17_totales_*` ×3, `r21_lo_insertado_es_lo_que_se_devuelve` | [x] |
| R18 | S:224 L11 con `d.tot`; U:614-647 `retenciones` = r2(`totdoc`) − r2(`tot`); `_resolver_referencia` (U:586) solo compara `entide`/`obride`, nunca totales | `r18_sql_l11_con_el_tot`, `r18_idempotente_tot_y_retenciones…` (188,77 y 0) | [x] |
| R19 | U:272-274 solo `n_retenciones`, no en `idempotente` ni en error | `r19_*` ×3 (busca `1.05`, `0.05`, `RET5`… en el log) | [x] |
| R20 | U:1024-1041 `peek_next_ide("dcarec")` solo con `dcarec` | `r20_previa_numera_la_dcarec_con_peek…`, `r12_contrato_sin_ctrrec…` (sin peek) | [x] |
| R21 | S:63-72 applock entre `_mov` y `_log`; S:279 E6b; U:690-719 reserva tras E6 e `INSERT` tras los `mov`; sin retención ni reserva ni `INSERT` | `r21_applock…`, `r21_sql_e6b…`, `r21_sql_insert_de_dcarec…`, `r21_con_retencion_e6b_tras_e6_e_insert_tras_los_mov` (secuencia exacta), `r21_sin_retencion…` | [x] |
| R22 | U:670-705 `work` reentrante: E6b por intento, `numerar` sobre filas recién construidas; el repositorio hace `ROLLBACK` antes de reintentar (`sql_server_repository.py:350-357`): sin huérfanas ni `ide` anterior | `r22_el_reintento_recalcula_el_ide_de_la_dcarec` + sonda (b) | [x] |
| R23 | S:295 E12 `COUNT(*) … WHERE docide = ?`; U:751 espera `len(filas.dcarec)` (0 o 1); `AlbaranCompraError` ⇒ `ROLLBACK` (repo:358-363) | `r23_sql_e12…`, `r23_relectura_de_dcarec_distinta_revierte` (1→0, 1→2, 0→1) | [x] |
| R24 | 47 constantes validadas por `DatabaseReferenceGuard` en el constructor (S:1183-1186); `UPDATE` solo E9 y E11; sin `DELETE`/`MERGE`/DDL; único literal el `''` de L5 que fija la spec | `r24_las_sentencias_nuevas_estan_validadas`, `r24_control_negativo…`, `test_f009_r31_sin_delete_merge_ni_ddl` | [x] |

`construir_dcarec` frente a M14-M16: las 21 columnas en el orden físico de M14; las 13 copiadas son
las de M11, con `cueide` del `ctrrec` (D8, V3 queda para el humano); `ivacuo`, `reqcuo`, `refide`,
`frasupide` a 0 (M13); `imprec` sigue a 0 y la retención no va ahí (M13, test
`r13_tot_y_totpag_netos…`). M15/M16 no piden nada más del albarán: asiento sin cambios, la factura
hereda la `dcarec`.

## F-009: solo cambian las diferencias declaradas (R26, R27)

Revisado `git diff dev -- tests/test_f009_*.py` (6 ficheros, +213/−201) contra la tabla del
informe: cada cambio lleva su `F-015 Rn` en un comentario y cae en L5 (R6), L11/`_EXISTENTE` (R18),
`APPLOCKS` (R21), `INSERT` fijos y `dcarec` (R1, R21), control negativo 40→47 (R24), `tiemod` (R8),
`construir_con`/`construir_dca` con la API nueva (R1-R9), `filas.dcarec` (R17), `releer_dcarec` en las
secuencias (R23), traza `n_retenciones` (R19), L16 en `_LISTAS` (R12) y los códigos (R6, R7, R14).
No encuentro ninguno fuera de lo declarado. Equivalencia: `DECLARADAS["dca"]` se **deriva** de
`ORIGEN_DCA` (no cascada) y los asserts son de igualdad exacta, así que las de cascada tienen que
coincidir con el clon; con `ctrrec`, solo cambian además `tot`/`totpag` y aparece `dcarec`
(`test_f015_r26_con_ctrrec…`). `dcapro`, `ctrprodes` y `mov` como en `dev`.

**R11/T15**: dorado, su test y los intocables, `git diff` vacío (medido). `test_f009_caracterizacion.py` pasa.

## Observaciones (no bloquean)

- **O1 · R12 «sin vinculadas» sin test propio.** `tests/test_f015_use_case.py:415` prueba la devolución
  con una línea **vinculada** negativa, pero M10 dice que la devolución típica es **solo sin vincular**,
  y ningún test del repo combina retención con solo líneas sin vincular (y sin E9-E11) en commit. El
  código no ramifica por eso y la sonda (a) lo confirma, así que el riesgo es bajo. Recomendado: añadir
  `test_f015_r12_devolucion_sin_vincular_con_retencion` (la sonda sirve de plantilla).
- **O2 · `valpor` NULL.** `albaran_compra_statements.py:443`: `_decimal(None)` daría
  `Decimal('None')` → `InvalidOperation`, un 500 «excepcion» sin escribir nada. No es silencioso y M11 no
  mide `valpor` NULL; si Sigrid lo admite, lo suyo sería `retencion_no_soportada`. Para la verificación
  manual R29 o una feature posterior.
- **O3 · Dobles de L11 con 7 columnas.** `tests/test_f009_use_case.py:713-714`: dos casos de conflicto
  siguen con tuplas de 7 (L11 ya da 8). Pasan porque `_resolver_referencia` falla antes de desempaquetar.
  Es cosmético.
- **O4 · R26, el aviso.** R26 declara para el caso con `ctrrec` «`dcarec` y el aviso R16», pero
  `test_f015_r26_con_ctrrec…` (`tests/test_f009_equivalencia.py:204`) no comprueba el aviso, que sí cubren
  los `test_f015_r16_*`. Es cosmético.

Desviación declarada aceptada: E6b se reserva justo tras E6, antes de E7, y el `INSERT` va tras los
`mov` (`impl_F-015.md` decisión 4). Encaja con el nombre «E6b» y con design §Flujo paso 5. Es el mismo
orden en todas las altas de la API, y el applock propio impide un orden inverso entre ellas.

## Cambios requeridos

Ninguno en este bloque. O1 es recomendable antes del cierre. Su sitio es la decisión del líder.
