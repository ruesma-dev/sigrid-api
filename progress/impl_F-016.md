<!-- progress/impl_F-016.md -->
# F-016 · Informe del implementer (T1-T16)

Spec v2 aprobada (2026-10-28, D6 y D12). Rama `feature/F-016-proforma-a-origen`. Rigor `critico`.

## T1 · La red de R1 y R2

`python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py -q` en la rama, antes de tocar
nada: **1328 passed** en 15,5 s. Ficheros (sin modificar en todo el trabajo):
`test_f007_{filas,models,perfil,route,settings,statements_contrato,statements_lineas,transaccion,use_case}.py`,
`test_f009_{caracterizacion,equivalencia,models,mutacion,route,settings,statements,use_case}.py`,
`test_f015_{statements,use_case}.py`, los dobles `f007_dobles.py` y `f009_dobles.py` y los dorados
`fixtures/f007_obra0719.json` y `fixtures/f009_caracterizacion.json`.

## Fase RED (salidas reales, recortadas a lo que falla)

**T2** `python -m pytest tests/test_f016_models.py -q`:
```
tests/test_f016_models.py:31: in <module>
    from domain.models.proforma_origen_models import (
E   ModuleNotFoundError: No module named 'domain.models.proforma_origen_models'
ERROR tests/test_f016_models.py
1 error in 1.47s
```

**T4** `python -m pytest tests/test_f016_settings.py -q`:
```
E   AttributeError: 'Settings' object has no attribute 'sigrid_proforma_origen_enabled'. Did you mean: 'sigrid_proforma_write_enabled'?
E   Failed: DID NOT RAISE ValidationError
E   AssertionError: assert None == 'false'
FAILED tests/test_f016_settings.py::test_f016_r4_la_llave_de_origen_arranca_cerrada
FAILED tests/test_f016_settings.py::test_f016_r4_se_lee_de_su_alias_como_booleano[true-True]
FAILED tests/test_f016_settings.py::test_f016_r4_un_valor_que_no_es_booleano_no_arranca[quizas]
10 failed, 1 passed in 2.01s (la que pasa: ninguna existente cambia)
```

**T6** `python -m pytest tests/test_f016_statements.py -q`:
```
tests/f016_dobles.py:26: in <module>
    from application.use_cases.proforma_origen_statements import ProformaOrigenStatements
E   ModuleNotFoundError: No module named 'application.use_cases.proforma_origen_statements'
ERROR tests/test_f016_statements.py
1 error in 2.57s
```

**T8** `python -m pytest tests/test_f016_use_case.py -q` (motivos agrupados con `grep "^E  " | sort | uniq -c`):
```
FAILED tests/test_f016_use_case.py::test_f016_r8_r13_previa_de_una_primera
FAILED tests/test_f016_use_case.py::test_f016_r11_r12_previa_encadenada_lee_y_escribe_la_cadena
FAILED tests/test_f016_use_case.py::test_f016_r5_existente_antes_de_validar_la_anterior
FAILED tests/test_f016_use_case.py::test_f016_r7_anterior_con_sucesora - Fail...
FAILED tests/test_f016_use_case.py::test_f016_r9_los_fallos_de_r9_y_de_la_etapa_1_juntos
FAILED tests/test_f016_use_case.py::test_f016_r14_tope_con_las_arrastradas_aun_en_previa
20 failed, 9 passed, 1 warning in 1.66s
      6 E       Failed: DID NOT RAISE AlbaranCompraError
      3 E       AssertionError: assert <class '...ProformaResponse'> is ProformaOrigenResponse
      2 E       KeyError: 'modo'
      1 E       domain.models.proforma_models.ProformaError: El contrato ya tiene proforma de este mes con otro importe: PROF26/00401. ...
      1 E       AssertionError: assert ['cod_provisi...ato_a_origen'] == ['cod_provisi...to_de_sigrid']
```
Las 9 que pasan son las de R1 (mes) y las que solo miran errores de F-007 (`importe_mes_no_cuadra`, `proforma_del_mes_existente`).

**T10** `python -m pytest tests/test_f016_transaccion.py -q` (T9 ya hecha: la parte de fuera pasa):
```
E       AssertionError: assert ['referencia'...rprodes', ...] == ['referencia'..._dcapro', ...]
E         At index 2 diff: 'reservar_cod' != 'lp8_sucesoras'
E       assert [] == [[14, 2793879, 2850201]]
E       Failed: DID NOT RAISE ProformaOrigenError
E       domain.models.proforma_models.ProformaError: El contrato ya tiene proforma de este mes con otro importe: PROF26/00401. Si es una segunda, otra_del_mes.
FAILED tests/test_f016_transaccion.py::test_f016_r18_orden_de_las_sentencias_y_applocks_de_f015
FAILED tests/test_f016_transaccion.py::test_f016_r17_lp8_por_el_cursor_tras_lp1
FAILED tests/test_f016_transaccion.py::test_f016_r17_sucesora_aparecida_dentro_no_escribe
FAILED tests/test_f016_transaccion.py::test_f016_r17_a_origen_del_mes_con_otro_total_aparecida_dentro_sigue
FAILED tests/test_f016_transaccion.py::test_f016_r18_reintento_reentrante_con_las_mismas_filas
5 failed, 7 passed, 1 warning in 2.25s
```

**T12** `python -m pytest tests/test_f016_route.py -q` (R3 y los códigos ya pasan por T2/T5; falta la llave):
```
>       assert estado == 400
E       assert 200 == 400
tests\test_f016_route.py:90: AssertionError
FAILED tests/test_f016_route.py::test_f016_r4_commit_a_origen_con_la_llave_cerrada_antes_del_caso_de_uso
1 failed, 15 passed, 1 warning in 1.82s
```
