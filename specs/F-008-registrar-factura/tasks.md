<!-- specs/F-008-registrar-factura/tasks.md -->
# F-008 · Tareas (v2)

No se empieza ninguna hasta que el humano apruebe la v2 y responda P11-P17 de `design.md` §9. Tests `test_f008_rN_*`, sin red ni BBDD: `SqlRepository` doblado. Rigor `critico`: fase RED antes de cada implementación.

- [ ] T0: Medir solo con lecturas `sys.columns` de `con`, `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y fijar en `progress/impl_F-008.md` tipos, nulabilidad y lista blanca  |  Verificación: tabla en el informe, revisada antes de T4
- [ ] T1: `config/settings.py`, `.env.example` y `local.settings.sample.json` con las seis variables, cerradas o vacías por defecto (R4, R6, R8, R21, R22, R43)  |  Verificación: `tests/test_f008_settings.py`
- [ ] T2: `domain/models/factura_models.py`: petición con `modo`, `origenes`, `lineas`, `vencimientos`, `vencimiento_retencion`; resultado y `FacturaError` (R1, R2, R20, R28, R40)  |  Verificación: `tests/test_f008_models.py`
- [ ] T3: `validar_vencimientos` puro: fecha real, rango, repetidas, suma (R29, R30, R31)  |  Verificación: `tests/test_f008_lineas.py`
- [ ] T4: `factura_lineas.py`: `linea_de_origen` en modo mes y origen con la tabla de §6, con casos anónimos de M63 (R17-R19)  |  Verificación: `tests/test_f008_lineas.py`
- [ ] T5: `factura_lineas.py`: `linea_sin_origen` reutilizando las funciones de F-009 sin editarlas (R20-R23)  |  Verificación: `tests/test_f008_lineas.py` y `git diff --stat` sin cambios en `albaran_compra_statements.py`
- [ ] T6: Constructores puros de `con`, `dcf` (con y sin orígenes), `dcfrec`, `pag` (N vencimientos + retención), `consii`, `dcaprodes` y `log` por lista blanca (R11, R24, R27, R28, R30, R34)  |  Verificación: `tests/test_f008_statements.py`
- [ ] T7: Lecturas con `?`: orígenes y sus líneas, línea anterior (`canorilin`), retención, proveedor por entidad y por CIF, obra, `usu`, `iva`, `conest`, asiento, idempotencia y duplicadas (R7, R9-R14, R16, R21, R39)  |  Verificación: `tests/test_f008_statements.py`, SQL comparado carácter a carácter
- [ ] T8: `CreateFacturaUseCase` previa: orden de validación de §7, sin escribir (R3, R5-R31, R39, R40)  |  Verificación: `tests/test_f008_use_case.py`, incluido que no se llama a ninguna sentencia de escritura
- [ ] T9: Trabajo de la transacción: applocks en orden, re-comprobación con `UPDLOCK`, reserva e `INSERT`s; factura sin orígenes sin marcas (R32-R34, R39)  |  Verificación: `tests/test_f008_transaccion.py`
- [ ] T10: `UPDATE`s de marcas y su condición de una fila (R36-R38)  |  Verificación: `tests/test_f008_transaccion.py`, con la carrera que revierte todo
- [ ] T11: Relectura antes del COMMIT y reintento reentrante (R33, R41)  |  Verificación: `tests/test_f008_transaccion.py`
- [ ] T12: Lista negativa: ninguna sentencia nombra `asi`, `apu`, `regiva`, `regirp`, `mov`, `dcfproana`, `dcfpropar`, `dcfprodes`, ni contiene `DELETE`; ningún cálculo de vencimiento (R31, R35)  |  Verificación: `tests/test_f008_statements.py` recorriendo todas las constantes
- [ ] T13: Ruta `sigrid/factura`, llave propia, errores y traza sin datos sensibles (R1, R4, R42)  |  Verificación: `tests/test_f008_route.py`
- [ ] T14: Compatibilidad: suites de rutas existentes sin cambios (R43)  |  Verificación: `python -m pytest tests -k "f007 or f009 or f015 or f016 or f018"`
- [ ] T15: `docs/ARCHITECTURE.md`, `CLAUDE.md` y `azure-apps/sigrid_api.md` en el mismo trabajo (R44)  |  Verificación: `tests/test_documentos_del_arnes.py` y revisión
- [ ] T16: Escribir `specs/F-008-registrar-factura/verificacion_manual.md` con los pasos exactos y las consultas de lectura posteriores  |  Verificación: revisión del reviewer
- [ ] T17: Campaña de mutación entera sobre `factura_*` y `create_factura_use_case`, supervivientes 0 o justificados por el humano  |  Verificación: `python -m harness.mutacion --rama feature/F-008-registrar-factura`
- [ ] T18: Revisión del reviewer contra `CHECKPOINTS.md`  |  Verificación: `progress/review_F-008.md` APROBADO
- [ ] T19: Comprobar los permisos de `user_rw` (V1) con quien administra Sigrid  |  Verificación: MANUAL (humano): `INSERT` en `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y `UPDATE` en `con`, `dca`, `dcapro`, `ctrpro`, `ctr`
- [ ] T20: Desplegar con la llave cerrada y lanzar previas de mes, a origen, mixta y sin origen sobre facturas reales ya registradas en el escritorio  |  Verificación: MANUAL (humano): pasos de `verificacion_manual.md`, sin `commit`
- [ ] T21: Una grabación de prueba en la obra 0404, solo con autorización expresa para esa acción; «Comprobar» y «Contabilizar» en el escritorio y anularla después (V2-V4, V6)  |  Verificación: MANUAL (humano): asiento cuadrado, marcas revertidas o el resultado anotado
- [ ] T22: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
