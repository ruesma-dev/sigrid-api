<!-- progress/review_F-003_c4.md -->
# F-003 · Revisión acotada — C4 y C4 ter

**Ámbito de este encargo:** SOLO C4 (trazabilidad de tests) y C4 ter (rutas
sensibles). C4 bis (fase RED, cobertura, mutación, RM1-RM6) lo revisa otro
encargo aparte, cuando cierre la campaña de mutación en curso.

**No se ejecutó `bash harness/init.sh` ni la suite completa**, por
restricción explícita del encargo (campaña de mutación en curso con 8
workers). La trazabilidad se verificó con `grep`/lectura directa de
`tests/`. El líder ya ejecutó la suite en esta sesión —**1.262 pasan, 1
skip**— y la volverá a ejecutar al cerrar la feature.

## Veredicto: APROBADO (C4 / C4 ter)

## C4 — La verificación es real

- [x] Cada requisito EARS tiene ≥ 1 test trazable y (según la ejecución
      reportada por el líder en esta sesión) todos pasan.
- [x] Los unit tests no tocan red ni BBDD.
- [x] No hay verificaciones `MANUAL (humano)` pendientes de listar aparte:
      la única (T8, prueba post-despliegue de la lectura cruzada) ya consta
      en `progress/current.md` con su comando exacto (`python
      scripts/diagnose_sigrid_contrato_docs.py` desde
      `albaranes-persistencia`) y su criterio de aceptación, pendiente de
      que el humano la ejecute tras el despliegue.

### Tabla de trazabilidad R1–R11

| Req | Test(s) | Verifica lo que dice el requisito |
|---|---|---|
| R1 | `test_sql_write_guard_bases.py::test_f003_r1_rechaza_escribir_en_la_documental_aunque_el_campo_database_este_permitido`, `test_f003_r1_rechaza_aunque_la_sentencia_culpable_no_sea_la_primera`; `test_database_reference_guard.py::test_f003_r1_rechaza_una_base_fuera_de_la_lista`, `test_f003_r1_lista_vacia_rechaza_cualquier_referencia_cualificada`, `test_f003_r1_una_referencia_seguida_de_un_asterisco_de_multiplicar_no_se_pierde`, `test_f003_r1_una_base_prohibida_nunca_se_cuela` (parametrizado) | Sí. `test_f003_r1_rechaza_escribir...` reproduce literalmente el caso medido (database=ruesma, INSERT a ruesma_rep) y comprueba `WriteValidationError` |
| R2 | `test_sql_write_guard_bases.py::test_f003_r2_acepta_la_documental_si_alguien_la_pone_en_la_lista`; `test_database_reference_guard.py::test_f003_r2_acepta_una_base_que_si_esta_en_la_lista`, `test_f003_r2_los_espacios_sobrantes_de_la_lista_se_ignoran` | Sí, ejecuta sin excepción con la base en la lista |
| R3 | ~20 tests en `test_database_reference_guard.py` (3/4 partes, `base..tabla`, corchetes, comillas dobles, mayúsculas, escapes) | Sí, cubre las seis formas listadas en el requisito una por una |
| R4 | `test_f003_r4_rechaza_siempre_los_nombres_de_cuatro_partes` (parametrizado); réplica en write y query guard (`test_f003_r4_rechaza_los_nombres_de_cuatro_partes[_tambien_en_lectura]`) | Sí, en ambos guardias |
| R5 | `test_f003_r5_*` (múltiples, uno y dos partes, literales, comentarios, delimitados) en los tres ficheros | Sí, incluye `TestConsultasRealesDelEcosistema::test_f003_r5_las_consultas_de_una_y_dos_partes_ni_se_tocan` |
| R6 | `test_sql_write_guard_bases.py::test_f003_r6_el_mensaje_nombra_la_base_y_la_lista_sin_filtrar_credenciales`; `test_database_reference_guard.py::test_f003_r6_con_lista_vacia_el_mensaje_dice_ninguna`, `test_f003_r6_las_entradas_vacias_de_la_lista_no_cuentan_como_base` | Sí, comprueba positivo (nombra base y "escritura") y negativo (`password`, `user_rw`, `server=`, `tcp:` ausentes) |
| R7 | `test_sql_query_guard_bases.py::test_f003_r7_rechaza_una_base_fuera_de_allowed_databases`, `test_f003_r7_si_se_quitara_ruesma_rep_de_la_lista_la_lectura_cruzada_se_rechaza`; `test_database_reference_guard.py::test_f003_r7_un_delimitador_no_puede_esconder_la_referencia`, `test_f003_r7_ninguna_forma_esconde_la_referencia` | Sí, con el mismo criterio de R3-R5 aplicado a lectura |
| R8 | `test_sql_query_guard_bases.py::TestConsultasRealesDelEcosistema::test_f003_r8_las_consultas_que_hoy_funcionan_siguen_pasando`; `test_database_reference_guard.py::test_f003_r8_acepta_lectura_cruzada_cuando_las_dos_bases_estan_permitidas` | Sí, incluye los 7 casos reales del inventario del ecosistema |
| R9 | Sin `test_f003_r9_*` dedicado. Se satisface en agregado: R1-R8 tienen test y ninguno de los 4 ficheros de test importa `requests`/`pyodbc`/socket — usan dobles (`SettingsDoble`, `PeticionDoble`) | Aceptable como meta-requisito de proceso, no de comportamiento verificable con un test propio. Ver nota abajo |
| R10 | `test_f003_r10_*` en los tres ficheros de guardias (prefijos, WHERE obligatorio, sentencia única, palabras prohibidas) + `test_verificar_sql_ecosistema.py::test_f003_r10_*` (12 tests) | Sí para el guardia. Los endpoints `sigrid/albaran*`/`contrato-lineas` no tienen test *nuevo* de F-003, pero su código no cambió (confirmado en `impl_F-003.md` §4, "No tocados") y la suite existente que ya los cubre sigue en verde (1.262 pasan) |
| R11 | `test_f003_r11_*` (11 tests): literal sin cerrar, comentario de bloque sin cerrar, corchete sin cerrar, comillas sin cerrar, corchete mal cerrado, tercer elemento ilegible, dos identificadores delimitados pegados | Sí, cada test comprueba `raises(DatabaseReferenceError)`, no solo detección |

**Nota sobre R9:** es un requisito sobre el proceso de testeo, no sobre
comportamiento del guardia. No existe (ni tendría sentido pedir) un test
`test_f003_r9` que pruebe "los demás tests existen". Se da por cubierto
verificando lo que pide literalmente: que R1-R8 tengan test y que esos tests
no toquen red/BBDD, ambas cosas confirmadas arriba. Si el líder o el humano
prefieren un test explícito de cobertura (p. ej. un test que recorra
`requirements.md` y confirme que existe `test_f003_rN_*` para cada N), es una
mejora menor, no bloqueante para este rigor.

## C4 ter — Verificaciones extra por rutas sensibles

- [N/A — sin declaración] `harness/rutas_sensibles.json` **no existe** en
  este repositorio (solo está `rutas_sensibles.ejemplo.json` y
  `rutas_sensibles.py`). Por la cabecera del propio checkpoint: "Sin esa
  declaración este bloque es N/A y no hay nada que justificar: es la
  configuración del caso mayoritario." No hay, por tanto, ninguna ruta
  sensible declarada contra la que contrastar el diff de F-003.

## Cambios requeridos

Ninguno dentro de este ámbito (C4 / C4 ter).
