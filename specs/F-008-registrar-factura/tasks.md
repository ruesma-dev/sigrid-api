<!-- specs/F-008-registrar-factura/tasks.md -->
# F-008 · Tareas (v3.1)

No se empieza ninguna hasta que el humano apruebe la v3.1 (P1-P21 decididas, `design.md` §9). Tests `test_f008_rN_*`, sin red ni BBDD: `SqlRepository` doblado. Rigor `critico`: fase RED antes de cada implementación.

- [x] T0: Medir solo con lecturas `sys.columns` de `con`, `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y fijar en `progress/impl_F-008.md` tipos, nulabilidad y lista blanca  |  Verificación: tabla en el informe, revisada antes de T7
- [x] T1: `config/settings.py`, `.env.example` y `local.settings.sample.json` con las siete variables, cerradas o vacías por defecto (R4, R6, R8, R24-R26, R47)  |  Verificación: `tests/test_f008_settings.py`
- [x] T2: `domain/models/factura_models.py`: petición con `serie`, `modo`, `origenes`, `a_origen`, `lineas` por serie, `vencimientos`, `vencimiento_retencion`; resultado y `FacturaError` (R1, R2, R9, R21, R23, R32, R44)  |  Verificación: `tests/test_f008_models.py`, incluida la mezcla de campos de serie y FRGG con `origenes` aceptada (P18)
- [x] T3: `validar_vencimientos` puro: fecha real, rango, repetidas, suma (R33-R35)  |  Verificación: `tests/test_f008_lineas.py`
- [x] T4: `linea_de_origen` en modo mes y origen con la tabla de §6, con casos anónimos de M63, igual en FR y FRGG (R12, R17, R19, R20)  |  Verificación: `tests/test_f008_lineas.py`
- [x] T5: `comparar_a_origen`: faltas, sobras, repetidas y tolerancias en el borde (±0,001 / ±0,01) (R21, R22)  |  Verificación: `tests/test_f008_lineas.py`
- [x] T6: `resolver_linea_gg` y el constructor único `linea_sin_origen(serie=...)`: cuenta y analítica, obra y centro desde la analítica, `almide` de cabecera, ceros, NDED como otro IVA (R24, R26-R28)  |  Verificación: `tests/test_f008_lineas.py`, mismo constructor parametrizado por serie
- [x] T7: `resolver_linea_fr` reutilizando las funciones de F-009 sin editarlas, sobre el constructor de T6 (R25, R28)  |  Verificación: `tests/test_f008_lineas.py` y `git diff --stat` sin cambios en `albaran_compra_statements.py`
- [x] T8: Constructores puros de `con` (estado por serie), `dcf` (con y sin orígenes, en las dos series), `dcfrec`, `pag`, `consii`, `dcaprodes` y `log` por lista blanca (R9, R12, R29, R31, R32, R34, R38)  |  Verificación: `tests/test_f008_statements.py`
- [x] T9: Lecturas con `?`: orígenes y líneas, línea anterior, retención, proveedor, obra, `usu`, `iva`, `conest` (REC y RECGG), asiento, cuenta (`tip 17`, `niv` 5), analítica (`tip 19`, hoja) y su obra, idempotencia y duplicadas (R7, R10-R15, R18, R24-R26, R43)  |  Verificación: `tests/test_f008_statements.py`, SQL comparado carácter a carácter
- [x] T10: Reserva de `cod` por serie: `FR<aa>/` 5 cifras y `FRGG<aa>/` 4 cifras, sin que una casa la otra (R9, R37)  |  Verificación: `tests/test_f008_statements.py`
- [ ] T11: `CreateFacturaUseCase` previa: orden de validación de §7, sin escribir, FR y FRGG, con y sin orígenes y mixtas (R3, R5-R35, R43, R44)  |  Verificación: `tests/test_f008_use_case.py`, incluido que no se llama a ninguna sentencia de escritura
- [ ] T12: Trabajo de la transacción: applocks en orden, re-comprobación con `UPDLOCK` (también R22), reserva e `INSERT`s; sin orígenes, sin marcas; FRGG con orígenes, con marcas (R36-R38, R43)  |  Verificación: `tests/test_f008_transaccion.py`
- [ ] T13: `UPDATE`s de marcas y su condición de una fila (R40-R42)  |  Verificación: `tests/test_f008_transaccion.py`, con la carrera que revierte todo
- [ ] T14: Relectura antes del COMMIT y reintento reentrante (R37, R45)  |  Verificación: `tests/test_f008_transaccion.py`
- [ ] T15: Lista negativa: ninguna sentencia nombra `asi`, `apu`, `regiva`, `regirp`, `mov`, `dcfproana`, `dcfpropar`, `dcfprodes`, ni contiene `DELETE`; ningún cálculo de vencimiento (R35, R39)  |  Verificación: `tests/test_f008_statements.py` recorriendo todas las constantes
- [ ] T16: Ruta `sigrid/factura`, llave propia, errores y traza sin datos sensibles ni cuentas (R1, R4, R46)  |  Verificación: `tests/test_f008_route.py`
- [ ] T17: Compatibilidad: suites de rutas existentes sin cambios (R47)  |  Verificación: `python -m pytest tests -k "f007 or f009 or f015 or f016 or f018"`
- [ ] T18: `docs/ARCHITECTURE.md`, `CLAUDE.md` y `azure-apps/sigrid_api.md` en el mismo trabajo (R48)  |  Verificación: `tests/test_documentos_del_arnes.py` y revisión
- [ ] T19: Escribir `specs/F-008-registrar-factura/verificacion_manual.md` con los pasos exactos y las consultas de lectura posteriores, FR y FRGG  |  Verificación: revisión del reviewer
- [ ] T20: Campaña de mutación entera sobre `factura_*` y `create_factura_use_case`, supervivientes 0 o justificados por el humano  |  Verificación: `python -m harness.mutacion --rama feature/F-008-registrar-factura`
- [ ] T21: Revisión del reviewer contra `CHECKPOINTS.md`  |  Verificación: `progress/review_F-008.md` APROBADO
- [ ] T22: Comprobar los permisos de `user_rw` (V1) con quien administra Sigrid  |  Verificación: MANUAL (humano): `INSERT` en `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y `UPDATE` en `con`, `dca`, `dcapro`, `ctrpro`, `ctr`
- [ ] T23: Desplegar con la llave cerrada y lanzar previas de mes, a origen, mixta, FR sin origen, FRGG sin origen y FRGG con albarán sobre facturas reales ya registradas en el escritorio  |  Verificación: MANUAL (humano): pasos de `verificacion_manual.md`, sin `commit`
- [ ] T24: Una grabación FR en la obra 0404 y una FRGG, cada una solo con autorización expresa; «Comprobar» y «Contabilizar» en el escritorio y anularlas después (V2-V4, V6, V7)  |  Verificación: MANUAL (humano): asiento cuadrado, marcas revertidas o el resultado anotado
- [ ] T25: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
