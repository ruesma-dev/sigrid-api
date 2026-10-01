<!-- specs/F-009-alta-albaran-compra/tasks.md -->
# F-009 · Tareas

Precondición de `in_progress`: T0 hecha y sus resultados volcados en la spec (o la PARADA 1 repetida si contradicen algo).

- [ ] T0: Mediciones M1-M15 de solo lectura por `sql/read` (consultas exactas en `progress/spec_F-009.md` §Mediciones); resultado en `progress/explore_F-009_mediciones.md` y ajuste de los [Mn] de la spec  |  Verificación: MANUAL (humano, o un explorer con su autorización expresa para esas lecturas)
- [ ] T1: `config/settings.py` con las cuatro claves de R5 y defecto cerrado; `local.settings.sample.json`  |  Verificación: `pytest tests/test_f009_settings.py` (`test_f009_r5_*`, `test_f009_r8_*`)
- [ ] T2: `domain/models/albaran_compra_models.py`: petición, validadores de R2, respuesta de R3 y `AlbaranCompraError` con el conjunto cerrado de códigos (R4)  |  Verificación: `pytest tests/test_f009_models.py` (`test_f009_r1_*`, `_r2_*`, `_r3_*`, `_r4_*`)
- [ ] T3: `albaran_compra_statements.py`: SQL constante L1-L14 y E1-E12, autovalidación con `DatabaseReferenceGuard`, control negativo de `DELETE`/`MERGE`/DDL/`UPDATE` ajeno (R29)  |  Verificación: `pytest tests/test_f009_statements.py -k "r29 or sql"` comparando el SQL carácter a carácter
- [ ] T4: Funciones puras `siguiente_cod`, `siguiente_balance` (entrada R17 y devolución R16 según M5), `estados_contrato` (R18) e `importe_linea` (R15), con fase RED  |  Verificación: `pytest tests/test_f009_statements.py -k "r15 or r16 or r17 or r18 or r24"`; traza RED en `impl_F-009.md`
- [ ] T5: Constructores de filas `con`, `dca`, `dcapro` vinculada y sin vincular con lista de reseteo, `ctrprodes` y `mov` (R10-R14, R19, R20)  |  Verificación: `pytest tests/test_f009_statements.py -k "r10 or r11 or r12 or r13 or r14 or r19 or r20"`
- [ ] T6: Test de equivalencia con `CreatePurchaseAlbaranUseCase` y sus diferencias declaradas (R31)  |  Verificación: `pytest tests/test_f009_equivalencia.py`
- [ ] T7: Caso de uso, resolución de cabecera (R9) y de líneas (R10-R14), con todos los fallos de línea acumulados (R4), con fase RED en R12  |  Verificación: `pytest tests/test_f009_use_case.py -k "r4 or r9 or r10 or r11 or r12 or r13 or r14"`
- [ ] T8: Idempotencia y prefijo de la referencia en dry-run y en commit (R27, R28), con fase RED  |  Verificación: `pytest tests/test_f009_use_case.py -k "r27 or r28"`
- [ ] T9: Dry-run con credenciales de lectura y preview completo (R21)  |  Verificación: `pytest tests/test_f009_use_case.py -k r21`
- [ ] T10: Commit: guardas (R22), `work` reentrante en una transacción (R23), reservas bajo applock (R24), reintento (R25) y relecturas (R26), con fase RED  |  Verificación: `pytest tests/test_f009_use_case.py -k "r22 or r23 or r24 or r25 or r26"`
- [ ] T11: Devoluciones de punta a punta en el caso de uso, `canser` < 0 y stock negativo (R16), con fase RED  |  Verificación: `pytest tests/test_f009_use_case.py -k r16`
- [ ] T12: Ruta `sigrid/albaran-compra` en `function_app.py` (R1, R3, R4); ninguna ruta existente cambia salvo T13  |  Verificación: `pytest tests/test_f009_route.py`
- [ ] T13: SOLO si el humano aprueba la pregunta 2: guarda de `SIGRID_ALBARAN_WRITE_ENABLED` en el commit de `sigrid/albaran` y `albaran-directo` (R7); `git diff dev -- application/use_cases/create_*albaran* domain/models/albaran_*` vacío (R6)  |  Verificación: `pytest tests/test_f009_route.py -k "r6 or r7"` y el `git diff` vacío
- [ ] T14: Trazas sin descripciones ni precios (R30)  |  Verificación: `pytest tests/test_f009_use_case.py -k r30` con `caplog`
- [ ] T15: Campaña de mutación de rigor `critico` sobre la feature, cero supervivientes o equivalentes con demostración  |  Verificación: `python -m harness.mutacion --feature F-009` → `progress/mutacion_F-009.md`
- [ ] T16: `docs/ARCHITECTURE.md` y mapa de rutas de `CLAUDE.md` (R34)  |  Verificación: revisión del reviewer
- [ ] T17: `azure-apps/sigrid_api.md` §4, §4.1, §7.2, §7.5, §7.6, §8.10, §10 y §13 (R34), commit aparte en `azure-apps`  |  Verificación: revisión del reviewer
- [ ] T18: Despliegue con `SIGRID_ALBARAN_WRITE_ENABLED=false`, `SIGRID_ALBARAN_PREFIJOS_REFERENCIA` y `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` según las preguntas 3 y 4  |  Verificación: MANUAL (humano): `func azure functionapp publish` y `az functionapp config appsettings set` con fichero JSON (sigrid_api.md §11)
- [ ] T19: Dry-run sobre `CTSU16/0206` (obra 0404) con una vinculada, una sin vincular `MA9999` con partida, una de almacén y una negativa (cuerpo en `progress/spec_F-009.md` §Manuales)  |  Verificación: MANUAL (humano): `Invoke-RestMethod` a `/api/sigrid/albaran-compra`, revisión de `filas` y `avisos`
- [ ] T20: Primer `commit:true` autorizado de ese albarán, con la llave abierta solo para la prueba; revisión en la UI (líneas, partidas, stock, medición del contrato) y repetición `idempotente`  |  Verificación: MANUAL (humano), con autorización expresa para esa escritura concreta
- [ ] T21: Anular el albarán de prueba desde la UI de Sigrid (nunca `DELETE`) y comprobar que revierte stock y `canser`  |  Verificación: MANUAL (humano)
- [ ] T22: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
