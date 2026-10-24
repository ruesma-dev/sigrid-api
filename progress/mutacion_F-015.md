<!-- progress/mutacion_F-015.md -->
# F-015 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-015 --workers 1` el 2026-10-24 14:45.

## Alcance

Origen del diff: **rama** (`6faacd78f6b9007f9dd424cd47a8d0e3240a2c08` .. `feature/F-015-albaran-plantilla-y-retencion`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 491 |
| `application/use_cases/create_albaran_compra_use_case.py` | 214 |
| `domain/models/albaran_compra_models.py` | 9 |
| `function_app.py` | 9 |
| **Total** | **723** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 104 |
| Mutantes evaluados | 104 |
| Muertos | 104 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1602.5 s |
| SHA de HEAD medido | `97c4e8be1b51a32c2d123cde955e5024c89cb6b8` |
| Línea base (s) — `.` | 156.3 |
| Media por mutante evaluado (s) | 15.4 |
| Timeout efectivo por mutante (s) | 313 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.


## Análisis (implementer)

**Ronda 1** (HEAD `40f1425`, 103 mutantes: 102 muertos, 0 supervivientes, 1 timeout). El timeout
(`numerar`: `ide_dcarec + n` → `- n`) se **midió** aplicándolo a mano: la suite entera pasa en verde
(2870 passed en 174 s, por encima de su línea base de 97 s; de ahí el timeout). Era un superviviente
real y **equivalente** bajo R12 (como mucho una `dcarec`: `n` siempre 0), así que el `+ n` era código
muerto. Se quitó y `numerar` rechaza ahora más de una `dcarec` (`ValueError`), con su test y su fase
RED (`test_f015_r12_numerar_con_dos_dcarec_no_numera`, commit `97c4e8b`).

**Ronda 2** (esta, HEAD `97c4e8b`): 104 de 104 muertos, sin timeouts. Ningún superviviente que
analizar.

**Límite conocido de la herramienta** (anotado en `current.md` para `arnes-base`): no genera mutantes
para literales de texto, `not in` ni argumentos con nombre. El SQL nuevo (L5, L11, L16, L17, E6b, los
`INSERT` y E12) lo fijan los tests carácter a carácter y las listas de columnas (`DCA_COLUMNAS`,
`DCAREC_COLUMNAS`, `ORIGEN_DCA`) el centinela R25 y los tests de esquema.
