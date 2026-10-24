<!-- progress/red_F-015.md -->
# F-015 · Trazas completas de la fase RED

Salida real de cada comando, lanzado con el test ya escrito y ANTES del código de su tarea (`.venv/Scripts/python.exe -m pytest ... -p no:cacheprovider`; los errores repetidos van agrupados, con su cuenta delante, por `sort | uniq -c`). Índice y resumen en [`impl_F-015.md`](impl_F-015.md).

### T2 · R1, R9 (fijas)
$ python -m pytest tests/test_f015_statements.py -k "r1 or r9" -q --tb=line
tests\test_f015_statements.py:99: AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'DCA_CALCULADAS'
E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'DCA_FIJAS'
tests\test_f015_statements.py:107: AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'DCA_FIJAS'
=========================== short test summary info ===========================
FAILED tests/test_f015_statements.py::test_f015_r1_dca_columnas_son_las_145_del_esquema_vivo_en_su_orden
FAILED tests/test_f015_statements.py::test_f015_r1_columnas_de_texto_de_dca
FAILED tests/test_f015_statements.py::test_f015_r1_origen_dca_cubre_las_145_sin_huecos_ni_repetidas
FAILED tests/test_f015_statements.py::test_f015_r1_identidad_y_su_nombre_en_el_proveedor
FAILED tests/test_f015_statements.py::test_f015_r1_cascada_grupos_y_nombres_en_el_proveedor
FAILED tests/test_f015_statements.py::test_f015_r1_calculadas_de_la_peticion_la_obra_o_un_calculo
FAILED tests/test_f015_statements.py::test_f015_r9_fijas_valor_del_alta_a_mano
7 failed in 3.42s

### T3 · R6, R7 (sentencias)
$ python -m pytest tests/test_f015_statements.py -k "r6 or r7" -q --tb=line
tests\test_f015_statements.py:159: AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'PATRON_SERIE_RESPALDO'
E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'TIP_PROVEEDOR'
tests\test_f015_statements.py:167: AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'TIP_PROVEEDOR'
E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'L5_RESPALDO_POR_ENTIDE'. Did you mean: 'L5_PLANTILLA_POR_ENTIDE'?
tests\test_f015_statements.py:177: AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'L5_RESPALDO_POR_ENTIDE'. Did you mean: 'L5_PLANTILLA_POR_ENTIDE'?
=========================== short test summary info ===========================
FAILED tests/test_f015_statements.py::test_f015_r6_sql_l5_respaldo_por_entide_sin_proformas
FAILED tests/test_f015_statements.py::test_f015_r6_sql_l5_respaldo_por_cif_sin_contrato
FAILED tests/test_f015_statements.py::test_f015_r6_constantes_del_respaldo - ...
FAILED tests/test_f015_statements.py::test_f015_r7_sql_l17_proveedor_por_cif_vivo_en_la_empresa
FAILED tests/test_f015_statements.py::test_f015_r6_r7_las_sentencias_nuevas_se_validan_al_construir
5 failed, 7 deselected in 1.13s

### T4 · R8 (`con` y `tiemod`; no exigida por R27, se deja igual)
$ python -m pytest tests/test_f015_statements.py -k "r8 and con" -q --tb=line
E   TypeError: construir_con() got an unexpected keyword argument 'tiemod'
FAILED tests/test_f015_statements.py::test_f015_r8_con_sellos_con_tiemod_ole_utc_del_alta
FAILED tests/test_f015_statements.py::test_f015_r8_con_exactamente_las_columnas_de_f006_con_su_valor
FAILED tests/test_f015_statements.py::test_f015_r8_con_res_recortado_a_128_y_sin_entres
3 failed, 12 deselected in 1.02s

### T5 · R2, R3, R5, R9 (y R4, R8, R10, R25)
$ python -m pytest tests/test_f015_statements.py -k "r2 or r3 or r4 or r5 or r8 or r9 or r10 or r25" -q --tb=line
      5 E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'pago_del_proveedor'
     30 E   TypeError: construir_dca() got an unexpected keyword argument 'contrato'
FAILED tests/test_f015_statements.py::test_f015_r3_una_columna_vacia_en_el_contrato_pasa_al_respaldo[cueide]
FAILED tests/test_f015_statements.py::test_f015_r3_una_columna_vacia_en_el_contrato_pasa_al_respaldo[eioide]
FAILED tests/test_f015_statements.py::test_f015_r3_una_columna_vacia_en_el_contrato_pasa_al_respaldo[dirdir1]
FAILED tests/test_f015_statements.py::test_f015_r3_una_columna_vacia_en_el_contrato_pasa_al_respaldo[dircon1]
FAILED tests/test_f015_statements.py::test_f015_r3_vacia_en_contrato_y_respaldo_pasa_al_proveedor[cueide]
FAILED tests/test_f015_statements.py::test_f015_r3_vacia_en_contrato_y_respaldo_pasa_al_proveedor[eioide]
FAILED tests/test_f015_statements.py::test_f015_r3_vacia_en_contrato_y_respaldo_pasa_al_proveedor[dirdir1]
FAILED tests/test_f015_statements.py::test_f015_r3_none_cuenta_como_vacio - T...
35 failed, 4 passed, 11 deselected in 1.18s

### T6 · R1, R24 (INSERT de con y dca; R1 con fase RED)
$ python -m pytest tests/test_f015_statements.py -k "r1 or r24" -q --tb=line
E   AssertionError: assert ('INSERT INTO... 'delo', ...]) == ('INSERT INTO..., 'res', ...])
E   AssertionError: assert 'INSERT INTO ..., ?, ?, ?, ?)' == 'INSERT INTO ..., ?, ?, ?, ?)'
E   Failed: DID NOT RAISE ValueError
E   Failed: DID NOT RAISE ValueError
E   AssertionError: assert frozenset({'dcapro'}) == frozenset({'c...a', 'dcapro'})
FAILED tests/test_f015_statements.py::test_f015_r1_insert_de_con_con_sus_19_columnas_fijas
FAILED tests/test_f015_statements.py::test_f015_r1_insert_de_dca_con_sus_145_columnas_fijas
FAILED tests/test_f015_statements.py::test_f015_r1_una_fila_de_cabecera_que_no_cuadra_no_se_inserta[insertar_con]
FAILED tests/test_f015_statements.py::test_f015_r1_una_fila_de_cabecera_que_no_cuadra_no_se_inserta[insertar_dca]
FAILED tests/test_f015_statements.py::test_f015_r24_solo_dcapro_se_clona - As...
FAILED tests/test_f015_statements.py::test_f015_r24_los_insert_de_cabecera_se_validan_al_construir
6 failed, 15 passed, 35 deselected in 1.02s

### T8 · códigos (no exigida por R27; se deja la traza)
$ python -m pytest tests/test_f009_models.py -q --tb=line
FAILED tests/test_f009_models.py::test_f009_r9_codigos_cerrados_de_design - A...
FAILED tests/test_f009_models.py::test_f009_r9_codigo_fuera_de_la_lista_no_se_construye[proveedor_sin_albaran_previo]
2 failed, 144 passed in 1.46s

### T7 · R3, R5, R6, R7 en el caso de uso (tests escritos; caso de uso de F-009 sin T7, restaurado del commit anterior)
$ python -m pytest tests/test_f015_use_case.py -k "r3 or r5 or r6 or r7" -q --tb=line
     21 E   TypeError: construir_con() takes 0 positional arguments but 1 positional argument (and 4 keyword-only arguments) were given
      5 E   ValueError: 'proveedor_sin_albaran_previo' no es un codigo de error de sigrid/albaran. Permitidos: almacen_de_obra_no_resuelto, base_de_datos_no_permitida, colision_d…
      1 FAILED tests/test_f015_use_case.py::test_f015_r7_sin_proveedor_unico_por_cif_no_se_da_de_alta[filas_l171-proveedor_ambiguo]
      1 FAILED tests/test_f015_use_case.py::test_f015_r7_sin_proveedor_unico_por_cif_no_se_da_de_alta[filas_l170-proveedor_no_encontrado]
      1 FAILED tests/test_f015_use_case.py::test_f015_r7_sin_contrato_ni_respaldo_el_prv_unico_del_cif
      1 FAILED tests/test_f015_use_case.py::test_f015_r7_proveedor_ilegible_no_sigue
      1 FAILED tests/test_f015_use_case.py::test_f015_r7_con_contrato_sin_respaldo_no_se_busca_por_cif
      1 FAILED tests/test_f015_use_case.py::test_f015_r6_sin_respaldo_el_alta_sigue_con_contrato_y_proveedor
      1 FAILED tests/test_f015_use_case.py::test_f015_r6_sin_contrato_el_respaldo_por_cif_da_la_identidad
      1 FAILED tests/test_f015_use_case.py::test_f015_r6_respaldo_ilegible_no_sigue
      1 FAILED tests/test_f015_use_case.py::test_f015_r6_no_se_lee_la_con_del_albaran_anterior
      1 FAILED tests/test_f015_use_case.py::test_f015_r6_l5_con_serie_clase_y_sin_proformas
      1 FAILED tests/test_f015_use_case.py::test_f015_r5_pago_sin_fuente_avisa_y_escribe_vacio
      1 FAILED tests/test_f015_use_case.py::test_f015_r5_el_aviso_tambien_en_el_alta

### T9 · R12, R14
$ python -m pytest tests/test_f015_statements.py -k "r12 or r14" -q --tb=line
      6 E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'RetencionNoSoportada'
      4 E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'resolver_retencion'
      1 FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[varias]
      1 FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[valfij]
      1 FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[sin_rec]
      1 FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[recide_0]
      1 FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[ivaide]
      1 FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[clase_1]
      1 FAILED tests/test_f015_statements.py::test_f015_r14_clases_soportadas_y_su_base
      1 FAILED tests/test_f015_statements.py::test_f015_r12_un_ctrrec_soportado_es_la_retencion[5]
      1 FAILED tests/test_f015_statements.py::test_f015_r12_un_ctrrec_soportado_es_la_retencion[4]
      1 FAILED tests/test_f015_statements.py::test_f015_r12_un_ctrrec_soportado_es_la_retencion[3]
      1 FAILED tests/test_f015_statements.py::test_f015_r12_sql_l16_recargos_del_contrato_con_su_clase
      1 FAILED tests/test_f015_statements.py::test_f015_r12_sin_ctrrec_no_hay_retencion

### T10 · R15 (y R13)
$ python -m pytest tests/test_f015_statements.py -k "r13 or r15" -q --tb=line
      5 E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'calcular_retencion'
      1 FAILED tests/test_f015_statements.py::test_f015_r15_totbas_0_retencion_0 - At...
      1 FAILED tests/test_f015_statements.py::test_f015_r15_otro_porcentaje - Attribu...
      1 FAILED tests/test_f015_statements.py::test_f015_r15_empate_a_medio_centimo_lejos_del_cero
      1 FAILED tests/test_f015_statements.py::test_f015_r15_base_por_clase_del_recargo[5-esperado0]
      1 FAILED tests/test_f015_statements.py::test_f015_r15_base_por_clase_del_recargo[4-esperado2]
      1 FAILED tests/test_f015_statements.py::test_f015_r15_base_por_clase_del_recargo[3-esperado1]
      1 FAILED tests/test_f015_statements.py::test_f015_r13_dcarec_copia_del_ctrrec_con_bas_y_cuo
      1 FAILED tests/test_f015_statements.py::test_f015_r13_dcarec_columnas_del_esquema_vivo
      1 E   assert 188.77 == 188.76
      1 E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'construir_dcarec'. Did you mean: 'construir_dca'?
      1 E   AttributeError: module 'application.use_cases.albaran_compra_statements' has no attribute 'DCAREC_COLUMNAS'. Did you mean: 'DCA_COLUMNAS'?
      1 8 failed, 68 deselected in 1.44s

### T11 · R13, R17, R20 (no exigidas por R27; se deja la traza)
$ python -m pytest tests/test_f015_statements.py -k "r13 or r17 or r20" -q --tb=line
      2 E   TypeError: FilasAlbaran.__init__() got an unexpected keyword argument 'dcarec'
      2 E   AttributeError: 'FilasAlbaran' object has no attribute 'dcarec'
      1 4 failed, 6 passed, 75 deselected in 1.36s

### T12 · R12, R14 (RED exigida), R16-R20
$ python -m pytest tests/test_f015_use_case.py tests/test_f015_statements.py -k "r12 or r14 or r16 or r17 or r18 or r19 or r20" -q --tb=line
     12 E   Failed: DID NOT RAISE AlbaranCompraError
     12 tests\test_f015_use_case.py:446: Failed: DID NOT RAISE AlbaranCompraError
      3 E   ValueError: too many values to unpack (expected 7)
      3 application\use_cases\create_albaran_compra_use_case.py:581: ValueError: too many values to unpack (expected 7)
      2 E   KeyError: 'tot'
      2 E   KeyError: 'n_retenciones'
      1 E   assert [] == [(44001, 2900001)]
      1 E   ValueError: not enough values to unpack (expected 1, got 0)
      1 E   KeyError: 'codigo'
      1 E   AssertionError: assert {'totbas': 21...neas': 1, ...} == {'totbas': 21...': 24.36, ...}
      1 E   AssertionError: assert [] == [{'ide': 4400...os': 64, ...}]
      1 E   AssertionError: assert [] == [('retencion_... retencion.')]
28 failed, 19 passed, 103 deselected, 1 warning in 1.49s

### T13a · R21, R23 (RED exigida), R24: sentencias
$ python -m pytest tests/test_f015_statements.py -k "r21 or r23 or r24" -q --tb=line
      3 E   AttributeError: 'AlbaranCompraStatements' object has no attribute 'insertar_dcarec'. Did you mean: 'insertar_dca'?
      2 E   AttributeError: 'AlbaranCompraStatements' object has no attribute 'reservar_ide_dcarec'. Did you mean: 'reservar_ide_dcapro'?
      1 E   assert 44 == 47
      1 E   AttributeError: 'AlbaranCompraStatements' object has no attribute 'releer_dcarec'. Did you mean: 'releer_dca'?
      1 E   AssertionError: assert ('SIGRID_REFE...IDE_mov', ...) == ('SIGRID_REFE...IDE_mov', ...)
8 failed, 2 passed, 84 deselected in 1.16s

### T13b · R21, R22, R23 (RED exigida en R21 y R23): caso de uso
$ python -m pytest tests/test_f015_use_case.py -k "r21 or r22 or r23" -q --tb=line
      6 E   ValueError: Hay dcarec y no se ha reservado ide_dcarec.
      1 E   assert [] == [[2900011]]
      1 E   Failed: DID NOT RAISE AlbaranCompraError
8 failed, 64 deselected, 1 warning in 1.43s

### T18 · R12: el superviviente medido de la campaña (`ide_dcarec + n`)
$ python -m pytest tests/test_f015_statements.py -k dos_dcarec -q --tb=line
E   Failed: DID NOT RAISE ValueError
tests\test_f015_statements.py:883: Failed: DID NOT RAISE ValueError
1 failed, 94 deselected in 1.10s

## Pasada 2 de la revisión

### P2.1 · R15: el mutante M10 (`Decimal(valpor)` en vez de `_decimal(valpor)`), aplicado a mano
Código de producción en `e42e0ad` + el test nuevo. Con M10 aplicado:
$ python -m pytest tests/test_f015_statements.py -k valpor_por_su_repr -q --tb=line
    # l. 443: return bas, redondear_euros(bas * Decimal(ctrrec["valpor"]))
E   AssertionError: assert Decimal('0.01') == Decimal('0.02')
E   AssertionError: assert Decimal('-0.04') == Decimal('-0.05')
E   AssertionError: assert Decimal('0.01') == Decimal('0.02')
3 failed, 95 deselected in 0.85s
Revertido M10 (código de `e42e0ad`):
3 passed, 95 deselected in 0.86s

### P2.2 · R25, la casilla «con contrato y sin respaldo» (control, no RED)
El comportamiento ya era correcto (el revisor lo midió): los dos tests nuevos no
pueden fallar contra el código de `e42e0ad`. Control medido con un mutante a mano,
`if contrato is not None or respaldo is not None:` -> `if respaldo is not None:`
(identidad e `ivadif` dejan de salir del contrato cuando no hay respaldo):
$ python -m pytest tests/test_f015_statements.py tests/test_f015_use_case.py tests/test_f009_equivalencia.py -q
FAILED tests/test_f015_statements.py::test_f015_r25_centinela_con_contrato_sin_respaldo_todo_del_contrato
FAILED tests/test_f015_statements.py::test_f015_r25_contrato_sin_cascada_y_sin_respaldo_pasa_al_proveedor
FAILED tests/test_f015_use_case.py::test_f015_r6_sin_respaldo_el_alta_sigue_con_contrato_y_proveedor
FAILED tests/test_f015_use_case.py::test_f015_r7_con_contrato_sin_respaldo_no_se_busca_por_cif
4 failed, 171 passed, 1 warning in 3.89s
Revertido: 175 passed.

### P2.4 · R14 ampliado: `valpor` NULL -> `retencion_no_soportada` (RED exigida, retencion O2)
Código de producción de `df16827` (sin el cambio) + los dos casos `valpor_null` nuevos:
$ python -m pytest tests/test_f015_statements.py tests/test_f015_use_case.py -k "valpor_null" -q --tb=line
E   Failed: DID NOT RAISE RetencionNoSoportada
C:\Users\pgris\PycharmProjects\sigrid-api\tests\test_f015_statements.py:666: Failed: DID NOT RAISE RetencionNoSoportada
E   decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
C:\Users\pgris\PycharmProjects\sigrid-api\application\use_cases\albaran_compra_statements.py:334: decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
E   decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
C:\Users\pgris\PycharmProjects\sigrid-api\application\use_cases\albaran_compra_statements.py:334: decimal.InvalidOperation: [<class 'decimal.ConversionSyntax'>]
FAILED tests/test_f015_statements.py::test_f015_r14_ctrrec_no_soportado[valpor_null]
FAILED tests/test_f015_use_case.py::test_f015_r14_retencion_no_soportada_400_antes_de_las_lineas[False-valpor_null]
FAILED tests/test_f015_use_case.py::test_f015_r14_retencion_no_soportada_400_antes_de_las_lineas[True-valpor_null]
(en el caso de uso, el 500 «excepcion» que señalaba O2). Con la comprobación en
`resolver_retencion`:
$ python -m pytest tests/test_f015_statements.py tests/test_f015_use_case.py -k "valpor_null or r14" -q --tb=line
22 passed, 154 deselected, 1 warning in 1.50s
