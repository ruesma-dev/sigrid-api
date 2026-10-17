<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010 --workers 1` el 2026-10-17 19:42.

## Alcance

Origen del diff: **rama** (`838a94ab9f4d47395c23305cacf752e5e0fa5983` .. `feature/F-010-documents-read-nombres-y-clave`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/read_document_use_case.py` | 9 |
| `domain/models/document_models.py` | 8 |
| `domain/models/sql_models.py` | 84 |
| `domain/ports/sql_repository.py` | 6 |
| `function_app.py` | 10 |
| `infrastructure/repositories/sql_server_repository.py` | 64 |
| `interface_adapters/http/http_response_factory.py` | 17 |
| **Total** | **198** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 23 |
| Mutantes evaluados | 23 |
| Muertos | 23 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 155.4 s |
| SHA de HEAD medido | `bb4a612b07a6cddfda0fcd6187d5f4b673af19e4` |
| Línea base (s) — `.` | 50.2 |
| Media por mutante evaluado (s) | 6.8 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Ronda anterior (para la trazabilidad)

Primera campaña, mismo comando, sobre `bef6a25`: 24 mutantes, 22 muertos, **2 supervivientes**,
246,7 s. Los dos se resolvieron en `bb4a612` y esta campaña los confirma muertos o desaparecidos:

1. `domain/models/sql_models.py:200` `min_length=1 -> 2` en `id_column`: hueco real (ningún test
   usaba un `id_column` de un carácter). Test nuevo
   `test_f010_r8_id_column_de_un_caracter_se_acepta_como_hoy`; **medido**: con el mutante
   aplicado a mano, ese test falla (`1 failed, 54 passed`) y sin él pasa.
2. `infrastructure/repositories/sql_server_repository.py:49` `zip(..., strict=True -> False)`:
   la estrictez no podía dispararse (nombres y valores salían del mismo dict). Se quita el
   código en vez de pedir que se acepte el equivalente: `build_document_query` compone ahora
   pares `(nombre validado, valor)` y el `zip` desaparece (de ahí 24 -> 23 mutantes).
