<!-- progress/mutacion_F-015_pasada2.md -->
# F-015 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-015 --workers 1` el 2026-10-24 15:40.

## Alcance

Origen del diff: **rama** (`5da4e85caab2e1151ddd3e29970bd7b56c173778` .. `feature/F-015-albaran-plantilla-y-retencion`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 13 |
| **Total** | **13** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 1 |
| Mutantes evaluados | 1 |
| Muertos | 1 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 98.2 s |
| SHA de HEAD medido | `b67de1ff8a7b387f2495fd5a6df701decd122b8f` |
| Línea base (s) — `.` | 89.3 |
| Media por mutante evaluado (s) | 98.2 |
| Timeout efectivo por mutante (s) | 179 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Mutantes a mano (la herramienta no muta el `raise` ni el texto)

Medidos en serie sobre HEAD `b67de1f`, sin otra edición en curso:

| Mutante (l. 425) | Suite | Veredicto |
|---|---|---|
| `if fila["valpor"] is None:` -> `if not fila["valpor"]:` (rechazaría el 0 %) | `tests/` entera: **2880 passed** | **superviviente**: hueco real, nada fijaba que un 0 % se admite |
| el mismo, con `test_f015_r14_valpor_0_es_soportado_solo_none_no` nuevo | `-k valpor_0`: `E   ...RetencionNoSoportada: El recargo RET5 no lleva valpor (sin porcentaje).` **1 failed** | **muerto** |
| quitar la comprobación entera | los tres casos `valpor_null` de la fase RED (P2.4 de `red_F-015.md`): 3 failed | muerto |

Revertido cada uno con `git checkout --`; sin el mutante, `-k valpor_0`: 1 passed.
