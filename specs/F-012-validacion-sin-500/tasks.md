# F-012 · Tareas

> **Aprobada por el humano el 2026-10-18** con las recomendaciones: D1 = **B** (saneado con `default=str`), D2 = helper único en las **9** rutas, D3 = **sin** red global en `json_response` y D4 = documentar en `azure-apps` y avisar a la sesión de albaranes antes de desplegar.

Las tareas asumen D1 = B, D2 = 9 rutas, D3 = no: es lo aprobado.

- [x] T1: Escribir `tests/test_f012_respuesta_validacion.py` (R4, R6, R11) en ROJO; traza en `progress/impl_F-012.md`  |  Verificación: `python -m pytest tests/test_f012_respuesta_validacion.py -q` falla (no existe `validation_error_response`)
- [x] T2: `validation_error_response(exc)` en `interface_adapters/http/http_response_factory.py` según design §Clases y funciones  |  Verificación: `python -m pytest tests/test_f012_respuesta_validacion.py -q` en verde
- [x] T3: Escribir `tests/test_f012_rutas.py` (R1 por las 6 reglas, R2, R3, R5, R8 por las 9 rutas y de fuente, R10) en ROJO; traza del 500 de hoy en el informe  |  Verificación: `python -m pytest tests/test_f012_rutas.py -q` falla en R1, R2, R3, R5 y R8-fuente
- [x] T4: Sustituir los 9 bloques de `function_app.py` por `return validation_error_response(exc)` sin tocar trazas ni orden de `except` (R8, R9, R10)  |  Verificación: `python -m pytest tests/test_f012_rutas.py tests/test_f012_respuesta_validacion.py -q` en verde
- [x] T5: Suite completa sin tocar aserciones previas ni regenerar el dorado (R7, R9)  |  Verificación: `python -m pytest -q` en verde y `git diff dev --stat -- tests/fixtures tests/test_f009_caracterizacion.py domain application infrastructure config` vacío
- [x] T6: Campaña de mutación muestreada de rigor `estandar`; supervivientes analizados en el informe  |  Verificación: `python -m harness.mutacion --feature F-012` → `progress/mutacion_F-012.md`
- [x] T7: `docs/ARCHITECTURE.md`, frase de `interface_adapters/http/` (R12)  |  Verificación: revisión del reviewer contra el código
- [x] T8: `../azure-apps/sigrid_api.md` §1.3, §8.2, §8.6 y §8.8 según design §Ficheros a modificar (R12), con nota «PENDIENTE DE DESPLIEGUE» hasta T10; commit aparte en `azure-apps`, sin push  |  Verificación: revisión del reviewer contra el código
- [x] T9: **MANUAL (humano)**: avisar a la sesión de albaranes (D4) y desplegar `dev` (`func azure functionapp publish ...`, lo lanza el humano); sin App Settings nuevas  |  Verificación: MANUAL (humano), la Function App lista las 9 funciones
- [x] T10: **MANUAL (líder, solo lectura)**: paso 1 de design §Verificación manual y, con autorización del humano, el 2 (R13); después quitar la nota de T8  |  Verificación: MANUAL (humano): 400 `ValidationError` con `ctx.error` en texto; resultados en `progress/verificacion_F-012.md`
- [x] T11: Ejecutar `bash harness/init.sh` en verde  |  Verificación: termina en ENTORNO LISTO
