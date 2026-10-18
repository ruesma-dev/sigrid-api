<!-- progress/mutacion_F-011.md -->
# F-011 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-011 --workers 1` el 2026-10-18 09:31.

## Alcance

Origen del diff: **rama** (`e153b39dc90c0d4f4e5f34e57e69cd65cf56f712` .. `feature/F-011-documents-read-valida-database`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/read_document_use_case.py` | 18 |
| `domain/models/document_models.py` | 9 |
| `function_app.py` | 11 |
| `infrastructure/repositories/sql_server_repository.py` | 5 |
| **Total** | **43** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 2 |
| Mutantes evaluados | 2 |
| Muertos | 2 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 83.7 s |
| SHA de HEAD medido | `cafc34062fa16621dc56abd60569a46234c34f83` |
| Línea base (s) — `.` | 61.4 |
| Media por mutante evaluado (s) | 41.8 |
| Timeout efectivo por mutante (s) | 123 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Campaña manual complementaria (implementer, 2026-10-18)

La herramienta solo generó **2 mutantes en 43 líneas**: sus operadores no tocan `not in`, literales de
texto, argumentos con nombre ni la composición de la cadena de `_connect`. Para el nivel `critico` se
aplicaron **a mano 14 mutantes** sobre el mismo HEAD (`cafc340`), uno a uno, con un script que reescribe el
fichero, lanza `pytest -q -x` sobre `tests/test_f011_*.py`, `tests/test_f010_caso_de_uso.py` y
`tests/test_f010_ruta.py` con `PYTHONDONTWRITEBYTECODE=1` y restaura con `git checkout`. Sin Edit ni Write
durante la campaña (el hook PostToolUse no se disparó). `git status` limpio al terminar.

| # | Fichero | Mutación | Resultado | Test que lo caza |
|---|---|---|---|---|
| M1 | caso de uso | `not in` → `in` | muerto | `test_f011_r1_base_no_permitida_lanza_con_el_texto_exacto` |
| M2 | caso de uso | quitar `self._validar_base(...)` | muerto | ídem |
| M3 | caso de uso | separador `', '` → `','` | muerto | ídem |
| M4 | caso de uso | lista + una base extra | muerto | ídem |
| M5 | caso de uso | `está` → `esta` en el texto | muerto | ídem |
| M6 | modelo | `BaseNoPermitidaError(Exception)` | muerto | `test_f011_r8_base_no_permitida_hereda_de_value_error` |
| M7 | modelo | hereda de `DocumentoAmbiguoError` | muerto | `test_f011_r8_no_es_documento_ambiguo` |
| M8 | ruta | texto del `warning` → `ValueError en ...` | muerto | `test_f011_r9_el_rechazo_deja_un_warning` |
| M9 | ruta | `details.type` → `"ValueError"` | muerto | `test_f011_r1_base_no_permitida_da_400_con_cuerpo_exacto` |
| M10 | composición | otro `Settings` para el caso de uso | muerto | `test_f011_r7_el_caso_de_uso_documental_recibe_el_settings_de_la_aplicacion` |
| M11 | `_connect` | `safe_database = database` (sin guardia) | muerto | `test_f011_r14_lista_mal_configurada_la_corta_el_adaptador_sin_conectar` |
| M12 | `_connect` | `field_name="db"` | muerto | ídem |
| M13 | `_connect` | `DATABASE={database}` (valor crudo) | muerto | `test_f011_r13_se_usa_el_valor_que_devuelve_el_guardia` |
| M14 | ruta | `details.type` literal → `type(exc).__name__` | **sobrevivió → muerto** | `test_f011_r8_el_tipo_es_literal_tambien_para_una_subclase` (nuevo) |

**M14.** Sobrevivió en la primera pasada: sin subclases, `type(exc).__name__` vale exactamente
`"BaseNoPermitidaError"`, así que era equivalente con el código de hoy. Pero el design (§Clases, entrada)
exige el literal «como el 409 de F-010» para que una subclase futura no cambie el `details.type` que lee
mcp-bbdd. Se añadió el test con una subclase, se volvió a aplicar M14 a mano y **muere**
(`1 failed, 14 passed`). Restaurado con `git checkout -- function_app.py`.

**Resultado conjunto: 16 mutantes (2 de la herramienta + 14 a mano), 16 muertos, 0 supervivientes.**
