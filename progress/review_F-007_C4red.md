<!-- progress/review_F-007_C4red.md -->
Revisión completa (pasada 1) de `dev...fe85523`, acotada a C4 y a la parte de C4 bis sobre fase RED y cobertura

# Review F-007 · bloque C4 + C4 bis (RED y cobertura)

**Veredicto del bloque: CHANGES_REQUESTED.** Un único hallazgo que bloquea, documental (H1): las verificaciones
MANUAL T21-T22 no tienen comando exacto en ningún sitio (mismo hallazgo que F-015, `review_F-015_C4red.md` H1). El
código y los tests de este bloque están bien: fase RED reproducida por mí en las ocho tareas de test, cobertura
100 % de 710 líneas reproducida, R1-R33 con tests que asertan valores.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Este bloque exige tests trazables por R sin red
ni BBDD, MANUAL con comando exacto, fase RED con salida real y cobertura de las líneas cambiadas ≥ 80 %.

**No ejecutado, por orden del encargo:** `init.sh`, la suite completa, nada contra Sigrid ni la API. Sí: F-007 →
**466 passed**; F-009 + F-015 → **816 passed**; `test_f012_rutas.py` → **26 passed**. Worktree
`../sigrid-api-rev007-roja` creado y **borrado**. Árbol limpio salvo los informes de los demás reviewers.

## C4 — La verificación es real

- [x] **Cada R tiene ≥ 1 test trazable y todos pasan.** Tabla abajo. R34 es esta revisión; R35 (MANUAL) y R36
  (documental) son de otro bloque.
- [x] **Los unit tests no tocan red ni BBDD.** Sin `pyodbc`, `socket`, `requests` ni `httpx`; `build_dependencies`
  doblado (`test_f007_route.py:48`); Settings con `_env_file=None`. **Medido:** los 466 pasan con `socket.connect`,
  `socket.create_connection` y `pyodbc.connect` sustituidos por un `raise` (plugin en el scratchpad).
- [ ] **MANUAL listadas con su comando exacto.** → **H1.**

## C4 bis — fase RED y cobertura (la mutación es de otro bloque)

- [x] **Rigor declarado**: `critico`.
- [x] **Fase RED real.** El informe trae la salida de las ocho (§Fase ROJA). La reproduje en un worktree: cada commit
  de test falla y su commit de implementación pasa, con estos resultados:

| Tarea (commit) | ROJA reproducida | Verde (commit) | ¿Cuadra con el informe? |
|---|---|---|---|
| T2 `64087fd` perfil | `ImportError: PERFIL_ALBARAN`, 1 error | T5 `ab037a0`: 37 passed | sí |
| T3 `1b04ba5` settings | 40 failed, 2 passed (`AttributeError sigrid_proforma_*`) | T4 `03a17a7`: 42 passed | sí, exacto |
| T6 `3f28e74` models | `ModuleNotFoundError proforma_models` | T7 `9022f29`: 118 passed | sí |
| T8 `78d21e1` contrato | `ModuleNotFoundError proforma_statements` | T9 `22ab898`: 50 passed | sí |
| T10 `e0f105e` lineas | `ImportError: FalloIdentificacion` | T11 `7e6b06c`: 92 passed | sí |
| T12 `41900cb` use_case | `ModuleNotFoundError create_proforma_use_case` | T13 `b00e59c`: 42 passed | sí |
| T14 `a8e3085` transaccion | 6 failed, 9 passed (`('creado'…) == ('existente'…)`, `DID NOT RAISE`) | T15 `a44bba9`: 15 passed | sí, exacto |
| T16 `fb3f42c` route | 17 failed (`no attribute 'CreateProformaUseCase'`, `'sigrid_proforma' in`) | T17 `1ac55b3`: 17 passed | sí, exacto |

  Cinco ROJAS son de colección (módulo nuevo; aceptado en F-009/F-015); T3, T14 y T16 fallan por aserto o atributo
  (las 9 que ya pasaban en T14 caracterizan lo heredado, y el informe lo dice). **Tests tocados entre ROJA y verde** (`git diff <roja> <verde> -- tests/`): T5, T9 y
  T7→HEAD solo reordenan imports (ruff); T11 ajusta la **entrada** de dos tests de T10 sin tocar sus asertos (ver O2);
  T17 toca el test de F-012 (ver abajo). De verde a HEAD ningún test de F-007 pierde un `assert` ni un `def test`
  (solo se añaden: models +62, use_case +64, contrato +2).
- [x] **Cobertura creíble.** El informe da `[OK] 100.0% de 710 líneas` (salida real de `init.sh` pegada). La medí
  aparte con `coverage` en el scratchpad (`COVERAGE_FILE` fuera del repo) y `python -m harness.cobertura --cov <json>`:
  - solo `tests/test_f007_*.py` → **99,9 % (709/710)**: la que falta es `create_albaran_compra_use_case.py:392`
    (guarda `base_de_datos_no_permitida` del núcleo, de F-009);
  - F-007 + F-009 + F-015 + F-012 → **100,0 % (710/710)**, igual que el informe.

  Que asertan y no solo ejecutan: de 251 funciones de test, 12 no tienen `assert` literal y todas lo hacen por un
  ayudante (`invalida()` = `pytest.raises(ValidationError)`) o comprueban que no se lanza
  (`test_f007_r19_sin_anterior_u_origen_no_se_comprueba_el_origen`). El SQL se compara carácter a carácter (LP1-LP6,
  `test_f007_r32_*`) y la previa, columna a columna. La mutación (372/374 muertos) la juzga otro bloque.
  El encargo citaba 712 líneas: es la cifra de T17 de `current.md` (O1); tras T18 son 710, las que mido.

## Test de F-012 tocado (desviación 13)

`tests/test_f012_rutas.py:253-254`, commit `1ac55b3` (el de la ruta, T17): `== 9` → `== 10` con el comentario
«F-007: diez rutas con `sigrid/proforma`». Cambio **mínimo y justificado**: el test cuenta las rutas que devuelven
`validation_error_response(exc)` y hoy hay 10 (medido); sigue siendo igualdad exacta. El docstring de
`http_response_factory.py:48` ya dice «10 rutas»; la ruta nueva la cubre `test_f007_route.py` (400 de F-012).

## Trazabilidad R → test (todos en verde)

| R | Tests (fichero `test_f007_*`) |
|---|---|
| R1 | models `r1_no_valida` (21 casos), `r1_periodo_aaaamm…`, `r1_fecha_proforma…` |
| R2 | models `r2_linea_no_valida`, `r2_descripcion_obligatoria`, `r2_referencia_de_linea_unica` |
| R3 | models `r3_sus_cuatro_variantes_no_validan`, `r3_lo_que_si_vale` |
| R4 | settings, 12 tests / 42 casos (defecto cerrado, JSON, CSV no arranca, ejemplo, ninguna existente cambia) |
| R5 | route `r5_commit_con_la_llave_cerrada_antes_del_caso_de_uso`, `r5_el_dry_run_no_cambia…`, `r5_la_llave_del_albaran…` |
| R6 | route `r6_*` (8: `codigo`, `lineas` con `candidatos`, `reparto`, F-012, 500); use_case `r6_fallos_de_la_etapa_1_juntos…` |
| R7 | statements_contrato `r7_*` (8, incl. `contrato_de_otro_proveedor`) |
| R8 | statements_contrato `r8_*` (18: fecha ≤ fin de periodo, `nlin` 0, CIF, nombre normalizado, líneas) |
| R9 | statements_contrato `r9_*` (10, `hoja_de_varios_contratos` con reparto); route `r6_hoja_de_varios_contratos…` |
| R10 | models `r10_resuelto_por_cerrado`; contrato (`lineas`); use_case :349 (`peticion`), `r24_las_tres_hojas…` (`proveedor`) |
| R11 | lineas `r11_sin_contrato_no_identifica_y_exige_producto`; use_case `r11_sin_contrato_por_el_camino_de_f015` |
| R12 | lineas `r12_entref_por_defecto`; use_case `r12_previsto_con_la_cabecera_de_proforma`, `r12_su_referencia…` |
| R13 | models `r13_de_contrato_por_ctrpro_o_medicion_positiva`; lineas `r13_de_contrato_y_sin_contrato` |
| R14 | lineas `r14_ctrpro_ide_del_contrato_se_acepta_sin_reidentificar` (el embudo daría ELABORACION, manda el ide), `r14_ctrpro_ide_de_otro_contrato_o_de_ninguno` (262990, línea de CTSB26/0472 = otro contrato de la obra, contra 0417 → `linea_no_es_del_contrato`, `candidatos == []`), 8 de respaldo, `r14_r16_revisar_lineas…`; filas `t18_r14_*` (4) |
| R15 | use_case `r15_vinculadas_como_f009_con_la_partida_del_ctrpro`, `r15_partida_de_imputacion_manda` |
| R16 | lineas `r16_sin_producto_es_obligatorio_aunque_el_contrato_tenga_uno_solo` (`producto_obligatorio`), `r14_r16_…`; use_case `r16_producto_ni_de_la_lista_ni_del_contrato` |
| R17 | use_case `r17_berenjeno_sin_vincular_con_el_producto_del_contrato` (natide/cueide/caaide/ivaide) y 7 más |
| R18 | lineas `r18_fecha_de_periodo`, `r18_periodo_futuro_o_fecha_fuera…`; use_case `r18_periodo_futuro_sin_leer_nada` |
| R19 | lineas `r19_*` (6, bordes 0,05 y 0,001) |
| R20 | lineas `r20_*` (8: previas al periodo, aviso de cabecera y de línea en el borde) |
| R21 | lineas `r21_supera_contrato_y_10_en_el_borde` (100 % y 110 %), `r21_contrato_sin_importe…` |
| R22 | lineas `r22_contrato_con_proforma_a_origen` |
| R23 | lineas `r23_es_proforma_del_mismo_contrato`; use_case `r23_*` (3: idempotente, desaparece, conflicto); filas `t18_r23` |
| R24 | lineas `r24_*` (6); use_case `r24_las_tres_hojas_de_la_0719_son_existentes` (previa y `commit`, líneas de LP6 campo a campo, sin transacción), `r24_solo_cuenta_el_contrato_resuelto`, `r24_existente_de_ctsb26_0472…` (LP1 con `ctride` y `PROF%`). La `AC` con `entref` `PROF%`: `AC26/25548` (`entref` `PROF0826_0719`) es la `existente`; LP1 exacto en `r32_lp1` |
| R25 | transaccion `r25_la_previa_no_reserva_nada`; use_case `r12_previsto…` (`transacciones == []`) |
| R26 | use_case `r26_guardas_sin_leer_la_base` (`referencia_no_permitida`, `demasiadas_lineas` en dry-run, dos llaves), `r26_la_llave_del_albaran…` — ver O3 |
| R27 | transaccion `r27_orden_de_las_sentencias_y_applocks_de_f015`, `r27_solo_los_update_de_f009…`; use_case `r27_retencion…` |
| R28 | transaccion `r28_*` (6: misma del mes → `existente` sin escribir y LP6 fuera; otro total → error; `otra_del_mes` sigue; misma referencia → `idempotente`; otra obra → conflicto; sin contrato no lee LP1) — ver O4 |
| R29 | transaccion `r29_colision_de_clave_y_reintento_reentrante`, `r29_…tras_los_reintentos`, `r29_relecturas_que_no_cuadran` |
| R30 | models `r30_*` (6); use_case (`contrato`, `origen`, `ctrpro_ide`, `de_contrato`, `cantidad_anterior_sigrid`) |
| R31 | perfil `r31_*` (24) + F-009/F-015 816 passed con `git diff dev...HEAD` **vacío** en `test_f009_*`, `test_f015_*`, `f009_dobles.py`, dorado e `infrastructure/` |
| R32 | statements_contrato `r32_*` (10: LP1-LP6 exactas, guardia de bases, sin DELETE/MERGE/DDL); transaccion `r27_solo_los_update…` |
| R33 | use_case `r33_*` (4: existente, previa, error, excepción; traza exacta y sin nombres, CIF ni importes) |
| R34 | esta revisión: nombres `test_f007_rN_*`, sin red, RED y SQL exacto verificados |

## Hallazgos

- **H1 (C4, tercer punto; bloquea).** T21 y T22 (R35) no tienen comando exacto en ningún sitio:
  `progress/current.md:123` solo dice «T20-T22 MANUALES»; `tasks.md` T21 dice «`POST /api/sigrid/proforma` con
  `commit:false` devuelve `existente`» sin cuerpo ni URL; `design.md` no tiene §Verificación manual; no existe
  `progress/verificacion_F-007.md`. **Cambio requerido** (papeleo, sin tocar código): una §Verificación manual en
  `design.md` enlazada desde `current.md` (o directamente en `current.md`) con:
  1. El `Invoke-RestMethod` literal de los dry-runs de T21 (URL, `x-functions-key` como variable sin valor, cuerpo
     JSON con `commit:false`) para las tres hojas de la 0719 (0472, 0417, 0369) y, para cada una, la variante con
     `otra_del_mes:true`; qué mirar (`estado`, `cod` `AC26/…` esperado, nº de líneas, totales). Resolver ahí la
     desviación 3 (¿`AC26/25552` o `/29425` para la 0417?).
  2. Para T22, la secuencia exacta (`commit:true` autorizado, repetirlo → `idempotente`) y las lecturas `sql/read`
     de antes y después (ficha, `dcapro` vinculadas, `dcarec`, servido) y de tras la anulación desde la UI.
  3. T20 (conversación con Administración y `proformas`) no lleva comando: basta decir qué se anota y dónde.

## Observaciones (no bloquean este bloque)

- **O1 (bloque C2).** `progress/current.md:116-117` trae las cifras de T17 (3297 passed, 712 líneas); en HEAD, 3347 y 710.
- **O2.** El commit verde T11 (`7e6b06c`) cambió la entrada de dos tests de T10 sin decirlo en el informe:
  `test_f007_r14_revisar_lineas_lleva_los_candidatos_de_la_ambigua` (añade `precio=0.5` para que el embudo no deshaga
  el empate) y `test_f007_traducir_linea_de_contrato_sin_partida` (una sola línea en la hoja). Los asertos no
  cambian y no se debilitan; conviene anotarlo en §Desviaciones.
- **O3.** R26 «credenciales y base de escritura»: ningún test de F-007 lo ejerce con `ProformaError`; lo cubre el
  núcleo compartido (F-009) y por eso `create_albaran_compra_use_case.py:392` solo sale cubierta con la suite de F-009.
  Un caso más en el paramétrico de `r26_guardas_sin_leer_la_base` (sin credenciales; base fuera de
  `allowed_write_databases`) lo cerraría.
- **O4 (para el humano / bloque de spec).** R28 pide repetir R23 dentro; la desviación 8 deja dentro la regla E1 de
  F-009 (misma `entide` y obra), así que «misma referencia de otra `cla`, mismo proveedor y obra» bajo el applock no
  daría `referencia_en_conflicto`. Declarado como residual y sin test; que lo acepte el humano por escrito.

## Automejora (propuesta, no aplicada)

H1 se repite (F-015, F-007). Para `specs/SPECS.md` y `spec-author.md` de `arnes-base`: toda tarea `MANUAL` que llame
a un endpoint enlaza a una §Verificación manual del diseño con el comando literal (secretos como variable).
