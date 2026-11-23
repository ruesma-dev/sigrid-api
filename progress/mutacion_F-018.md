<!-- progress/mutacion_F-018.md -->
# F-018 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-018 --workers 1` el 2026-10-29 13:04.

## Alcance

Origen del diff: **rama** (`6aca02731cd0f5b7f3c066aceb2584981910395d` .. `feature/F-018-descuento-por-linea`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 104 |
| `application/use_cases/create_albaran_compra_use_case.py` | 84 |
| `domain/models/albaran_compra_models.py` | 48 |
| `function_app.py` | 9 |
| **Total** | **245** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 66 |
| Mutantes evaluados | 66 |
| Muertos | 66 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1637.7 s |
| SHA de HEAD medido | `e649e384dd06941e8aae500d57445894ab06ca59` |
| Línea base (s) — `.` | 136.7 |
| Media por mutante evaluado (s) | 24.8 |
| Timeout efectivo por mutante (s) | 274 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

