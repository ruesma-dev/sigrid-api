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
10 failed, 2 passed (las dos que pasan: ninguna existente cambia)
```
