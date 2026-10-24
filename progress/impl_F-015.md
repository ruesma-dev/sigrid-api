<!-- progress/impl_F-015.md -->
# F-015 · Informe del implementer

Rama `feature/F-015-albaran-plantilla-y-retencion`, rigor **critico**. Spec v2 aprobada el 2026-10-24 (D1-D12),
T0 cerrada. Tareas **T1-T18 y T22 hechas**; **T19-T21 MANUALES, sin marcar** (despliegue, dry-runs R29, grabación
autorizada y limpieza: humano y líder). Nada contra Sigrid: ni lecturas ni escrituras; los tests no tocan red ni base.

## Qué cambió

- **Cabecera por lista blanca (O1, R1-R10)**. `con` sale de `construir_con` con exactamente las 19 `CON_COLUMNAS` de
  F-006 y `tiemod` = fecha OLE UTC del alta (`SellosAlbaran.tiemod`). `dca` sale de `construir_dca` con las 145
  `DCA_COLUMNAS`, cada una con UN origen en `ORIGEN_DCA`: identidad (6), cascada (15; pago y banco en bloque),
  calculadas (18) y fijas (106, valor del alta a mano). `resolver_cascada` aplica contrato → respaldo → `prv` (el
  `auxpag` del `prv` si el pago sale de él) y devuelve las columnas sin fuente; columna ausente en una fila leída ⇒
  `ValueError` (R10). `INSERT` de `con` y `dca` con columnas fijas; solo `dcapro` se sigue clonando.
- **Respaldo opcional (R6)**: L5 por `entide` o por CIF con `c.cod LIKE 'AC__/%'`, `d.cla = 0` y `ISNULL(d.entref, '')
  NOT LIKE 'PROF%'` (los tres como `?`). Ya no se lee la `con` del albarán anterior. Sin respaldo, el alta sigue
  (`template_ide` 0); sale `proveedor_sin_albaran_previo`.
- **Proveedor por CIF (R4, R7)**: sin contrato ni respaldo, L17 (`prv` vivo del CIF en la empresa de la obra):
  `proveedor_no_encontrado` / `proveedor_ambiguo`. El `prv` del `entide` se lee siempre por `read_full_row`.
- **Avisos (R5, D12)**: `cabecera_sin_dato` (pago sin fuente, o banco sin fuente con efecto `CC`/`CT`/`TR`, leído de
  `auxefp`), informativo, en previa y en `creado`.
- **Retención (O2, R12-R23)**: L16 (`ctrrec` con la clase de su `rec`), `resolver_retencion` (`RetencionNoSoportada`
  ⇒ 400 `retencion_no_soportada`, también en dry-run, tras la idempotencia y antes de las líneas),
  `calcular_retencion` (`Decimal`, `ROUND_HALF_UP`), `construir_dcarec` (21 columnas), `dca.tot` = `totpag` =
  `totdoc` − `cuo`, aviso `retencion_del_contrato`, `totales` + `tot`/`retenciones`/`n_retenciones`,
  `FilasAlbaran.dcarec`, `numerar(ide_dcarec=…)`, previa con `peek_next_ide("dcarec")` solo si la hay, idempotente
  con `d.tot` en L11, traza con `n_retenciones`. Commit: applock `SIGRID_IDE_dcarec` entre `_mov` y `_log`, E6b,
  `INSERT` tras los `mov`, reintento con `ide` nuevo y E12 `COUNT(*) FROM dbo.dcarec WHERE docide = ?`.
- **Documentación**: docstring de `sigrid_albaran` y `docs/ARCHITECTURE.md` (T16); `azure-apps/sigrid_api.md` §7.5,
  §7.6, §8.6 (con la limitación del clásico, D9), §8.7 y §13 con nota **PENDIENTE DE DESPLIEGUE**, commit local
  `49dfb36` en `azure-apps` (sin push; no tiene remoto). Contrato v8.3 y §Limpieza: commit `67927eb` (sin código).

## Ficheros tocados

| Fichero | Qué |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | lista blanca, cascada, L5/L11/L16/L17, E6b, E12, `INSERT` fijos, retención, `numerar` |
| `application/use_cases/create_albaran_compra_use_case.py` | cabecera, L17, avisos, L16, `_construir`, previa, commit, idempotente, traza |
| `domain/models/albaran_compra_models.py` | códigos de cabecera y de aviso (T8) |
| `function_app.py` (solo docstring), `docs/ARCHITECTURE.md` | T16 |
| `tests/f009_dobles.py` | filas completas de 145 columnas, `prv`, `auxpag`, L16/L17, `dcarec` (E6b, `INSERT`, E12) |
| `tests/test_f015_statements.py`, `tests/test_f015_use_case.py` | 167 tests nuevos (R1-R26) |
| `tests/test_f009_{statements,use_case,equivalencia,mutacion,route,models}.py` | T8 y T14, cada cambio con su R |
| `specs/F-015-…/tasks.md`; `progress/mutacion_F-015.md`, `progress/red_F-015.md` | marcas, campaña, trazas RED |

Commits: `67927eb` (docs), T1-T18 de `f8deb5e` a `b369a7f` (uno por tarea; T15 es solo una comprobación).

## Decisiones y desviaciones (también en `progress/current.md`)

1. **Orden**: T2 antes que T1 (el doble usa `DCA_COLUMNAS`); T8 antes que T7 (el caso de uso lanza los códigos
   nuevos); la parte de caso de uso de T3 va en T7; los nombres SQL nuevos del doble entran con su tarea.
2. **R5**: el efecto se lee de `auxefp` por `read_full_row` (como `ctr`, `prv`, `auxpag`) y se compara su `cod` con
   `CC`, `CT`, `TR`; solo con el banco sin fuente y `efeide` ≠ 0. Sin fila, `ValueError`. No es SQL nuevo.
3. **R5, R10**: aviso y comprobación de columnas una vez, tras `conest`/`usu` (`resolver_cascada`), fuera de la
   transacción.
4. **R21, «tras los `mov`»**: E6b se reserva justo después de E6 (de ahí su nombre) y el `INSERT` va tras los `INSERT`
   de `mov`, antes de los `UPDATE` del contrato. Sin retención, ni reserva ni `INSERT`.
5. **R23**: E12 de `dcarec` siempre, esperando 0 o 1 (también protege de una `dcarec` ajena); por eso las secuencias
   de F-009 ganan `releer_dcarec`.
6. **R19**: `n_retenciones` solo en las trazas de `previsto` y `creado`; `idempotente` no lee `dcarec` (R18) y un
   error no la conoce.
7. **L16 como lectura de lista** (`muchas=True`: con varias filas el error es de negocio, nunca truncado silencioso).
8. **El literal `''` de L5** lo fija la spec (design §Sentencias); el control negativo (F-009 R31, F-015 R24) admite
   solo ese.
9. **Textos**: aviso «El contrato lleva el recargo RET5 (5 %): se retienen 1.05 sobre 21.00 y el neto (tot) es
   totdoc menos la retencion.»; error: el motivo de `resolver_retencion` + «… alta a mano.». En `idempotente`,
   `retenciones` en `Decimal` (4568,11 − 4379,34 = 188,77, no 188,76999…).
10. **T18**: la ronda 1 dejó un mutante medido como superviviente equivalente (`ide_dcarec + n`): el `+ n` era código
    muerto. `numerar` rechaza ahora más de una `dcarec` (`ValueError`), con test y RED.
11. **Tests de F-009 renombrados** (decían «clon», ya falso): `test_f009_r11_con_con_lo_del_albaran`,
    `test_f009_r21_dca_con_pago_y_efecto_del_respaldo_y_lo_del_albaran`,
    `test_f009_r21_dca_sin_contrato_ctride_0_y_entidad_del_respaldo`, `test_f009_r21_dca_lleva_exactamente_sus_columnas`.
    Nuevo `test_f015_r26_con_ctrrec_solo_cambian_el_neto_y_la_dcarec` en `test_f009_equivalencia.py` (usa su
    maquinaria del clásico).

## Tests de F-009 que cambian (T14, commit `c0e40ef`; T8, `72d82b4`)

Todos dentro de lo declarado en R26-R27; ninguno fuera. `git diff dev --stat -- 'tests/test_f009_*.py'` para el
reviewer.

| Test (fichero) | R | Cambio |
|---|---|---|
| `sql_l5_*` ×2 (statements); `r11_lecturas…`, `r11_con_emp…`, `r11_sin_contrato_la_plantilla…` (use_case) | R6 | SQL y parámetros de L5 |
| `sql_l11_idempotencia…` (statements); `_EXISTENTE` y totales de `idempotente` (use_case, mutacion) | R18 | `d.tot` y `retenciones` |
| `r26_sql_applocks…` (statements); `r25_el_albaran_entero…` (use_case) | R21 | `SIGRID_IDE_dcarec` |
| `r25_sql_insert_de_las_tablas_clonadas…`, `r31_una_fila_clonada_vacia…`, `r31_solo_se_inserta…` | R1, R21 | `con`/`dca` fijas, `dcarec` |
| `r31_sin_delete_merge_ni_ddl` | R24, R6 | 47 sentencias; solo el `''` de L5 |
| `r22_sellos…`, `_sellos()` | R8 | `tiemod` |
| `r11_con_*` ×2, `r21_dca_*` ×3 (statements) | R1-R9 | API nueva (renombrados, punto 11) |
| `r25_las_filas_numeradas…`, `r23_filas_como_diccionario…` (statements); `r23_las_seis_filas…` (use_case); `r7_previa_extendida…` (route) | R1, R17 | `con`/`dca` completas; `filas.dcarec` |
| `r11_proveedor_sin_albaran_previo…`, `r11_sin_contrato_y_sin_albaran_previo…` (use_case) | R6, R7 | el alta sigue; L17 |
| `r7_superconjunto…` (use_case) | R17 | `tot`, `retenciones`, `n_retenciones` |
| `_SECUENCIA_COMPLETA`, `r26_sin_vinculadas_ni_mov…` (use_case) | R23 | `releer_dcarec` |
| `r25_la_fila_dca_escrita_lleva_las_bancarias` (use_case) | R1, R9 | sin corchetes; `cpacue1` fija `''` |
| `r32_traza_de_una_previa`, `r32_traza_de_un_commit` (use_case) | R19 | `n_retenciones: 0` |
| `r9_las_lecturas_de_lista…` (mutacion) | R12 | L16 en `_LISTAS` |
| `DECLARADAS` y las dos `r33_*` (equivalencia) | R26 | con: todas; dca: no cascada (de `ORIGEN_DCA`); difieren `tiemod` y las fijas de M19 |
| `r9_codigos_cerrados…` y `codigo_fuera_de_la_lista…` (models, T8) | R4, R6, R7, R14 | códigos nuevos y el retirado |

R11 (T15): `git diff dev -- tests/fixtures/f009_caracterizacion.json tests/test_f009_caracterizacion.py
application/use_cases/create_purchase_albaran_use_case.py application/use_cases/create_direct_albaran_use_case.py
domain/models/albaran_domain_models.py domain/models/albaran_directo_models.py
application/use_cases/parte_reclamacion_statements.py` → **salida vacía** (medido). El dorado pasa sin tocarlo.

## Fase RED (R27: R1, R2, R3, R5, R6, R7, R9, R12, R14, R15, R21, R23)

Salida real, con el test escrito y antes del código; completa (más T4, T8, T11, T18) en
[`red_F-015.md`](red_F-015.md). Agrupado con su cuenta delante. Tras el código, cada bloque pasó en verde.

```
$ python -m pytest tests/test_f015_statements.py -k "r1 or r9" -q --tb=line          # T2 · R1, R9
E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'DCA_FIJAS'
FAILED tests/test_f015_statements.py::test_f015_r1_origen_dca_cubre_las_145_sin_huecos_ni_repetidas
FAILED tests/test_f015_statements.py::test_f015_r9_fijas_valor_del_alta_a_mano
7 failed in 3.42s
$ python -m pytest tests/test_f015_statements.py -k "r6 or r7" -q --tb=line          # T3 · R6, R7
E   AttributeError: module '…albaran_compra_statements' has no attribute 'L5_RESPALDO_POR_ENTIDE'. Did you mean: 'L5_PLANTILLA_POR_ENTIDE'?
FAILED tests/test_f015_statements.py::test_f015_r7_sql_l17_proveedor_por_cif_vivo_en_la_empresa
5 failed, 7 deselected in 1.13s
$ python -m pytest tests/test_f015_statements.py -k "r2 or r3 or r4 or r5 or r8 or r9 or r10 or r25" -q --tb=line   # T5
      5 E   AttributeError: module '…albaran_compra_statements' has no attribute 'pago_del_proveedor'
     30 E   TypeError: construir_dca() got an unexpected keyword argument 'contrato'
35 failed, 4 passed, 11 deselected in 1.18s
$ python -m pytest tests/test_f015_statements.py -k "r1 or r24" -q --tb=line         # T6 · R1 (INSERT fijos)
E   Failed: DID NOT RAISE ValueError
E   AssertionError: assert frozenset({'dcapro'}) == frozenset({'c...a', 'dcapro'})
6 failed, 15 passed, 35 deselected in 1.02s
$ python -m pytest tests/test_f015_use_case.py -k "r3 or r5 or r6 or r7" -q --tb=line   # T7 (caso de uso previo restaurado)
     21 E   TypeError: construir_con() takes 0 positional arguments but 1 positional argument (and 4 keyword-only arguments) were given
      5 E   ValueError: 'proveedor_sin_albaran_previo' no es un codigo de error de sigrid/albaran. Permitidos: …
$ python -m pytest tests/test_f015_statements.py -k "r12 or r14" -q --tb=line        # T9 · R12, R14
      6 E   AttributeError: module '…albaran_compra_statements' has no attribute 'RetencionNoSoportada'
      4 E   AttributeError: module '…albaran_compra_statements' has no attribute 'resolver_retencion'
$ python -m pytest tests/test_f015_statements.py -k "r13 or r15" -q --tb=line        # T10 · R15
      5 E   AttributeError: module '…albaran_compra_statements' has no attribute 'calcular_retencion'
      1 8 failed, 68 deselected in 1.44s
$ python -m pytest tests/test_f015_use_case.py tests/test_f015_statements.py -k "r12 or r14 or r16 or r17 or r18 or r19 or r20" -q --tb=line   # T12
     12 E   Failed: DID NOT RAISE AlbaranCompraError
      3 E   ValueError: too many values to unpack (expected 7)
28 failed, 19 passed, 103 deselected, 1 warning in 1.49s
$ python -m pytest tests/test_f015_statements.py -k "r21 or r23 or r24" -q --tb=line  # T13a · R21, R23
      3 E   AttributeError: 'AlbaranCompraStatements' object has no attribute 'insertar_dcarec'. Did you mean: 'insertar_dca'?
      1 E   AttributeError: 'AlbaranCompraStatements' object has no attribute 'releer_dcarec'. Did you mean: 'releer_dca'?
8 failed, 2 passed, 84 deselected in 1.16s
$ python -m pytest tests/test_f015_use_case.py -k "r21 or r22 or r23" -q --tb=line     # T13b · R21, R22, R23
      6 E   ValueError: Hay dcarec y no se ha reservado ide_dcarec.
      1 E   Failed: DID NOT RAISE AlbaranCompraError
8 failed, 64 deselected, 1 warning in 1.43s
```

## Fuera del alcance

El clásico y `albaran-directo` (D9: limitación documentada en `azure-apps`); `empide` desde el `usu` (D10: albaranes
F-069); interpretar el documento de forma de pago (D1). No se corrige el `empide` de las altas ya escritas.

## Lo que falta (no es del implementer)

- **Avisar a albaranes antes de desplegar** (sv9/sv4 con los mapeos nuevos; contrato v8.3, ya acusado en T0).
- **T19-T21 MANUALES**: despliegue (`func publish`, el humano), dry-runs R29 (contrato con `RET5`, sin `ctrrec`, sin
  contrato, proveedor sin respaldo), una grabación solo con autorización expresa, revisada en la UI, repetida e
  anulada desde la UI, y la limpieza (design §Limpieza) con su autorización.
- Tras desplegar: quitar las notas «PENDIENTE DE DESPLIEGUE» de `azure-apps/sigrid_api.md`.
- Revisión del reviewer contra `CHECKPOINTS.md`.

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Suite completa (`bash harness/init.sh`, última ejecución, HEAD `b369a7f` + este informe) | **2871 passed, 1 skipped**, 0 failed |
| Tests de F-015 (`test_f015_statements.py` + `test_f015_use_case.py`) | 167 passed (más `test_f015_r26` en equivalencia) |
| Tests de F-009 (statements, use_case, equivalencia, mutacion, route, models, caracterizacion) | 582 passed |
| Cobertura de líneas cambiadas (`PUERTA COBERTURA`) | **100.0 % de 237 líneas** (237/237, umbral 80 %, nivel critico) |
| Mutación, ronda 2 (`--workers 1`, HEAD `97c4e8b`) | **104 generados, 104 muertos, 0 supervivientes, 0 timeouts** (1602,5 s) |
| Mutación, ronda 1 (HEAD `40f1425`) | 103 generados, 102 muertos, 1 timeout medido como superviviente equivalente y quitado (decisión 10) |
| Tiempo de la suite | 133,81 s (`init.sh`); línea base de la campaña 156,3 s |
| `ruff` | ficheros tocados limpios; 79 avisos previos en el repo (no bloquean; `function_app.py` trae 3 previos) |

Detalle de la campaña: [`mutacion_F-015.md`](mutacion_F-015.md). Salida de `init.sh`: «ENTORNO LISTO», PUERTA TAMAÑO
en verde (requirements 134/150, design 237/250).
