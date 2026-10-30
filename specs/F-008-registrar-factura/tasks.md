<!-- specs/F-008-registrar-factura/tasks.md -->
# F-008 · Tareas

No se empieza ninguna hasta que el humano apruebe la spec y responda P1-P10 de `design.md`. Tests `test_f008_rN_*`, sin red ni BBDD: `SqlRepository` doblado.

- [ ] T0: Medir solo con lecturas `sys.columns` de `con`, `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y fijar en `progress/impl_F-008.md` tipos, nulabilidad y lista blanca  |  Verificación: tabla en el informe, revisada antes de T3
- [ ] T1: `config/settings.py` y `.env.example` con las tres variables, apagadas por defecto (R3, R5, R6, R37)  |  Verificación: `tests/test_f008_settings.py`
- [ ] T2: `domain/models/factura_models.py` con petición, resultado y `FacturaError` (R1, R2, R33)  |  Verificación: `tests/test_f008_models.py`
- [ ] T3: `factura_vencimiento.py` con la regla y el token `R`, parametrizado con casos anónimos de M58 (R28, R29)  |  Verificación: `tests/test_f008_vencimiento.py`
- [ ] T4: Constructores puros de `con`, `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y `log` por lista blanca (R14, R15, R18, R22, R23, R27)  |  Verificación: `tests/test_f008_statements.py`
- [ ] T5: Lecturas de albaranes, líneas, retención, proveedor, conest, asiento e idempotencia, todas con `?` (R7-R12, R31, R32)  |  Verificación: `tests/test_f008_statements.py`
- [ ] T6: `CreateFacturaUseCase` previa: resolver, validar, calcular, sin escribir (R2, R4-R13, R16-R18, R22, R28, R29, R31-R33)  |  Verificación: `tests/test_f008_use_case.py`, incluido que no se llama a ninguna sentencia de escritura
- [ ] T7: Trabajo de la transacción: applocks en orden, re-comprobación con `UPDLOCK`, reserva e `INSERT`s (R19-R21, R23, R31, R32)  |  Verificación: `tests/test_f008_transaccion.py`
- [ ] T8: `UPDATE`s de marcas y su condición de una fila (R24-R26)  |  Verificación: `tests/test_f008_transaccion.py`, con la carrera que revierte todo
- [ ] T9: Relectura antes del COMMIT y reintento reentrante (R21, R34)  |  Verificación: `tests/test_f008_transaccion.py`
- [ ] T10: Lista negativa: ninguna sentencia nombra `asi`, `apu`, `regiva`, `regirp`, `mov`, ni contiene `DELETE` (R30)  |  Verificación: `tests/test_f008_statements.py` recorriendo todas las constantes
- [ ] T11: Ruta `sigrid/factura`, llave propia, errores y traza sin datos sensibles (R1, R3, R35)  |  Verificación: `tests/test_f008_route.py`
- [ ] T12: Compatibilidad: suites de rutas existentes sin cambios (R36)  |  Verificación: `python -m pytest tests -k "f007 or f009 or f016 or f018"`
- [ ] T13: `docs/ARCHITECTURE.md`, `CLAUDE.md` y `azure-apps/sigrid_api.md` en el mismo trabajo (R38)  |  Verificación: `tests/test_documentos_del_arnes.py` y revisión
- [ ] T14: Escribir `specs/F-008-registrar-factura/verificacion_manual.md` con los pasos exactos y las consultas de lectura posteriores  |  Verificación: revisión del reviewer
- [ ] T15: Campaña de mutación entera sobre `factura_*` y `create_factura_use_case`, supervivientes 0 o justificados por el humano  |  Verificación: `python -m harness.mutacion --rama feature/F-008-registrar-factura`
- [ ] T16: Revisión del reviewer contra `CHECKPOINTS.md`  |  Verificación: `progress/review_F-008.md` APROBADO
- [ ] T17: Comprobar los permisos de `user_rw` (V1) con quien administra Sigrid  |  Verificación: MANUAL (humano): confirmar `INSERT` en `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y `UPDATE` en `con`, `dca`, `dcapro`, `ctrpro`, `ctr`
- [ ] T18: Desplegar con la llave cerrada y lanzar previas sobre facturas reales ya comparadas con una factura del escritorio  |  Verificación: MANUAL (humano): pasos de `verificacion_manual.md`, sin `commit`
- [ ] T19: Una grabación de prueba en la obra 0404, solo con autorización expresa para esa acción, y «Comprobar» y «Contabilizar» en el escritorio; después anularla desde el escritorio (V2-V4)  |  Verificación: MANUAL (humano): asiento cuadrado, marcas revertidas o el resultado anotado
- [ ] T20: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
