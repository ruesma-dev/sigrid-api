<!-- progress/impl_F-007.md -->
# F-007 · Informe del implementer (lotes A, B y C: T1-T17)

Rama `feature/F-007-registrar-proforma`, rigor **critico**. Spec v3, PARADA 1 aprobada el 2026-10-25 (D4-D14; D11
con `SM9999`, `SB9999`, `SM370001`). Nada contra Sigrid: ni lecturas ni escrituras; los tests no tocan red ni base.

## T1 · Red de R31 (F-009 y F-015, sin tocarlos)

`git log HEAD..dev` vacío (la rama ya tiene `dev`, `6ece24d`). En verde, antes de tocar nada:
`python -m pytest tests/test_f009_*.py tests/test_f015_*.py -q` → **816 passed**. La red de R31 son estos ficheros,
que no se modifican en ninguna tarea:

- `tests/test_f009_caracterizacion.py` + dorado `tests/fixtures/f009_caracterizacion.json` (clásico y directo)
- `tests/test_f009_equivalencia.py`, `test_f009_models.py`, `test_f009_mutacion.py`, `test_f009_route.py`,
  `test_f009_settings.py`, `test_f009_statements.py`, `test_f009_use_case.py`
- `tests/test_f015_statements.py`, `tests/test_f015_use_case.py`
- el doble `tests/f009_dobles.py` (tampoco se toca: F-007 tiene el suyo, `tests/f007_dobles.py`, que lo extiende)
