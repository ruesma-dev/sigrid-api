<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **8 features**, 4 abiertas, 4 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-001 | Test de calentamiento: el guardia de escritura rechaza una base no permitida | 1 | pendiente | estandar | `feature/F-001-calentamiento` |
| F-006 | Endpoint de dominio para crear partes de reclamación de Posventa, en lote | 6 | spec lista | critico | `feature/F-006-alta-parte-reclamacion` |
| F-007 | Endpoint de dominio para registrar proformas | 7 | pendiente | critico | `feature/F-007-registrar-proforma` |
| F-008 | Endpoint de dominio para registrar facturas de compra | 8 | pendiente | critico | `feature/F-008-registrar-factura` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-002 | Spike: viabilidad de escribir en la base documental ruesma_rep | 2 | critico |
| F-003 | El guardia de escritura debe validar tambien las bases nombradas dentro del SQL | 3 | critico |
| F-004 | Endpoint de dominio para adjuntar un documento a un concepto de Sigrid | 4 | critico |
| F-005 | concepto-grafico admite documentos sin clase de grafico, como Sigrid en contratos y albaranes | 5 | critico |

## Detalle

### F-001 · Test de calentamiento: el guardia de escritura rechaza una base no permitida

estado **pendiente** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-calentamiento`

Feature trivial para validar el circuito completo del arnés en este repositorio (rama, acceptance, implementer, reviewer, cierre). Anade un test unitario sobre SqlWriteGuard que fije por escrito la regla que hoy solo vive en configuracion: una peticion de escritura contra una base fuera de ALLOWED_WRITE_DATABASES (p.ej. ruesma_rep) se rechaza.

### F-006 · Endpoint de dominio para crear partes de reclamación de Posventa, en lote

estado **spec lista** · prioridad 6 · rigor `critico` · SDD sí · rama `feature/F-006-alta-parte-reclamacion`

Alta del 2026-09-24 por petición del humano. Crear en Sigrid partes de reclamación de Posventa (con.tip 708, serie RS<aa>.<mm>/) como lo hace la UI segun docs/referencia/postventa_pasos_crear_parte.md (referencia principal) y postventa_manual_sigrid.md: desde la unidad postventa, descripcion, tipo de reclamacion, oficio e intervinientes (rcpint -> obrofc de la obra). Lo consume postventa-incidencias F-040 (volcado masivo de incidencias aprobadas). DECISIONES DEL HUMANO (2026-09-24): (1) endpoint de LOTE con tope (~50), CADA PARTE EN SU PROPIA TRANSACCION y respuesta parte a parte, reutilizando las lecturas comunes de la obra; (2) idempotencia por REFERENCIA EXTERNA que aporta quien llama, guardada en un campo de Sigrid (la spec mide cual; candidato: el 'N. Referencia Externo' del importador Excel de Sigrid, con el posible conflicto de la referencia del promotor); (3) tipo de reclamacion por defecto 0002 PRIMER LISTADO POSTVENTA, informable en la peticion. Propuesta aceptada: peticion por codigos, no por ide; interviniente que no este en los oficios de la obra -> se rechaza el parte; el parte nace en su estado inicial y NO se pasa a PTE (proceso de Sigrid que crea tareas y envia correos); codigo de serie calculado DENTRO de la transaccion bajo applock; interruptor propio apagado por defecto ademas de SIGRID_DOMAIN_WRITE_ENABLED; dry-run por defecto. Fuera: pasar a PTE, tareas, correos del portal, fotos (ya van por concepto-grafico), alta de unidades postventa u oficios de obra.

### F-007 · Endpoint de dominio para registrar proformas

estado **pendiente** · prioridad 7 · rigor `critico` · SDD sí · rama `feature/F-007-registrar-proforma`

Alta del 2026-09-24 por petición del humano, anotada sin estudiar todavía. Escritura de dominio en el ERP de producción: dry-run por defecto, commit:true solo con autorización expresa, una transacción, reserva de ide y de código de serie bajo applock, idempotencia frente a reintentos. La spec mide antes en producción (solo lectura) qué filas escribe Sigrid al hacerlo desde la UI. Relación con postventa-incidencias (F-046/F-047: coste de la posventa y vínculo de la incidencia con la proforma, el coste y la venta). Proforma = albarán proforma de subcontratista (manual de Postventa de Sigrid, «Documentos de compras»): trabajos realizados que se pueden facturar. Qué tipo de concepto, serie y tablas usa Sigrid, y su relación con el contrato y con la reclamación, los investiga la spec. Estudiar si reutiliza create_purchase_albaran_use_case.

### F-008 · Endpoint de dominio para registrar facturas de compra

estado **pendiente** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-008-registrar-factura`

Alta del 2026-09-24 por petición del humano, anotada sin estudiar todavía. Escritura de dominio en el ERP de producción: dry-run por defecto, commit:true solo con autorización expresa, una transacción, reserva de ide y de código de serie bajo applock, idempotencia frente a reintentos. La spec mide antes en producción (solo lectura) qué filas escribe Sigrid al hacerlo desde la UI. Relación con postventa-incidencias (F-046/F-047: coste de la posventa y vínculo de la incidencia con la proforma, el coste y la venta). Facturas de COMPRA (de proveedor, las que imputan coste): decidido por el humano el 2026-09-24. Una factura en Sigrid arrastra contabilidad y estados de los documentos de origen (albaranes, proformas): la spec decide qué recalcula el endpoint y qué deja a Sigrid, y si cabe en este microservicio.

### F-002 · Spike: viabilidad de escribir en la base documental ruesma_rep

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-spike-escritura-ruesma-rep`

Averiguar si es posible, y con que garantias, escribir adjuntos en ruesma_rep (base documental de Sigrid). Hoy esta deliberadamente fuera de ALLOWED_WRITE_DATABASES y solo se lee. Incluye: modelo real de las tablas documentales, permisos del usuario user_rw sobre esa base, como enlaza Sigrid un documento con su concepto, y que haria falta en la API. Prerrequisito de la propuesta docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md. Solo lectura y diagnostico salvo autorizacion expresa del humano para una escritura concreta. RESUELTO el 2026-09-03: ruesma_rep es READ_WRITE, misma instancia, sin replicacion, y user_rw ya tiene INSERT sobre su unica tabla dbo.gra (medido con INSERT ... WHERE 1=0 y control negativo que devuelve 229). No hace falta ningun GRANT. Informe completo en progress/explore_ruesma_rep.md.

### F-003 · El guardia de escritura debe validar tambien las bases nombradas dentro del SQL

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-guardia-bases-cruzadas`

SqlWriteGuard valida el campo 'database' de la peticion, pero no los identificadores de base que aparecen dentro de la sentencia. Por eso hoy se puede escribir en ruesma_rep pidiendo database='ruesma' y nombrando ruesma_rep.dbo.gra en el SQL: medido el 2026-09-03. La politica de ALLOWED_WRITE_DATABASES no esta realmente aplicada. Va antes que F-004 porque F-004 depende de que la documental siga cerrada a sql/write.

### F-004 · Endpoint de dominio para adjuntar un documento a un concepto de Sigrid

estado **terminada** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-004-endpoint-concepto-grafico`

Implementar POST /api/sigrid/concepto-grafico segun docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md, actualizada con lo medido en F-002. Hace las tres escrituras en una sola transaccion local (binario en ruesma_rep.gra, metadatos en ruesma.gra con el mismo cod, enlace en ruesma.rcg) y no abre sql/write a la base documental. Dry-run por defecto. Lo pide postventa-incidencias F-012.

### F-005 · concepto-grafico admite documentos sin clase de grafico, como Sigrid en contratos y albaranes

estado **terminada** · prioridad 5 · rigor `critico` · SDD no · rama `feature/F-005-grafico-sin-clase`

Sigrid adjunta los documentos de contratos (con.tip 44) y albaranes de compra (con.tip 14, tabla dca, cod AC) SIN clase de grafico: gratipide=0 en el 99,98 % de los casos, medido el 2026-09-06. El endpoint sigrid/concepto-grafico (F-004) exige una clase de la lista blanca que exista en dbo.auxgra, asi que hoy rechaza gratipide=0. Se admite 0 como 'sin clase' SOLO cuando SIGRID_DOCUMENT_ALLOWED_GRATIPIDE lo incluya explicitamente, sin consultar auxgra ni tipaso en ese caso, y sin relajar nada mas. Decidido por el humano (opcion 2) frente a usar la clase 40 DOCUMENTOS GENERALES. Primera prueba real en la obra 0404 (CUBIERTA NAVE 14 - JOHN DEERE).
