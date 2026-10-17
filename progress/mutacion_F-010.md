<!-- progress/mutacion_F-010.md -->
# F-010 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-010 --workers 1` el 2026-10-17 20:20.

## Alcance

Origen del diff: **rama** (`838a94ab9f4d47395c23305cacf752e5e0fa5983` .. `feature/F-010-documents-read-nombres-y-clave`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/read_document_use_case.py` | 11 |
| `domain/models/document_models.py` | 8 |
| `domain/models/sql_models.py` | 84 |
| `domain/ports/sql_repository.py` | 10 |
| `function_app.py` | 10 |
| `infrastructure/repositories/sql_server_repository.py` | 69 |
| `interface_adapters/http/http_response_factory.py` | 17 |
| **Total** | **209** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 24 |
| Mutantes evaluados | 24 |
| Muertos | 24 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 148.3 s |
| SHA de HEAD medido | `913761aa6007d31b47ec070253b048580e55d5dc` |
| Línea base (s) — `.` | 45.6 |
| Media por mutante evaluado (s) | 6.2 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.



## Rondas anteriores (para la trazabilidad)

Esta campaña se regeneró sobre la punta `913761a` por el hallazgo H3 de `review_F-010.md`: la
ronda 2 se había medido sobre `bb4a612`, antes de la corrección H1 (`64ffde0`).

- **Ronda 2** (`bb4a612`, mismo comando): 198 líneas, 23 mutantes, 23 muertos, 0 supervivientes,
  155,4 s. La ronda final suma 11 líneas (las de H1 en caso de uso, puerto y adaptador) y un
  mutante, `application/use_cases/read_document_use_case.py:26` `is not None -> is None`: muerto.
- **Ronda 1** (`bef6a25`, mismo comando): 24 mutantes, 22 muertos, **2 supervivientes**, 246,7 s.
  Ambos se resolvieron en `bb4a612`:
  1. `domain/models/sql_models.py:200` `min_length=1 -> 2` en `id_column`: hueco real (ningún test
     usaba un `id_column` de un carácter). Test nuevo
     `test_f010_r8_id_column_de_un_caracter_se_acepta_como_hoy`; **medido**: con el mutante
     aplicado a mano, ese test falla (`1 failed, 54 passed`) y sin él pasa. Muerto también aquí (4/24).
  2. `infrastructure/repositories/sql_server_repository.py:49` `zip(..., strict=True -> False)`:
     la estrictez no podía dispararse (nombres y valores salían del mismo dict). Se quitó el
     código en vez de pedir que se acepte el equivalente: `build_document_query` compone pares
     `(nombre validado, valor)` y el `zip` desaparece.
