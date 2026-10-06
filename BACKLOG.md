<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **9 features**, 4 abiertas, 5 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-001 | Test de calentamiento: el guardia de escritura rechaza una base no permitida | 1 | pendiente | estandar | `feature/F-001-calentamiento` |
| F-009 | Modo extendido de sigrid/albaran: alta idempotente de albaranes de compra del pipeline (PRE-1 de albaranes F-053) | 7 | spec lista | critico | `feature/F-009-alta-albaran-compra` |
| F-007 | Endpoint de dominio para registrar proformas | 8 | pendiente | critico | `feature/F-007-registrar-proforma` |
| F-008 | Endpoint de dominio para registrar facturas de compra | 9 | pendiente | critico | `feature/F-008-registrar-factura` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-002 | Spike: viabilidad de escribir en la base documental ruesma_rep | 2 | critico |
| F-003 | El guardia de escritura debe validar tambien las bases nombradas dentro del SQL | 3 | critico |
| F-004 | Endpoint de dominio para adjuntar un documento a un concepto de Sigrid | 4 | critico |
| F-005 | concepto-grafico admite documentos sin clase de grafico, como Sigrid en contratos y albaranes | 5 | critico |
| F-006 | Endpoint de dominio para crear partes de reclamación de Posventa, en lote | 6 | critico |

## Detalle

### F-001 · Test de calentamiento: el guardia de escritura rechaza una base no permitida

estado **pendiente** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-calentamiento`

Feature trivial para validar el circuito completo del arnés en este repositorio (rama, acceptance, implementer, reviewer, cierre). Anade un test unitario sobre SqlWriteGuard que fije por escrito la regla que hoy solo vive en configuracion: una peticion de escritura contra una base fuera de ALLOWED_WRITE_DATABASES (p.ej. ruesma_rep) se rechaza.

### F-009 · Modo extendido de sigrid/albaran: alta idempotente de albaranes de compra del pipeline (PRE-1 de albaranes F-053)

estado **spec lista** · prioridad 7 · rigor `critico` · SDD sí · rama `feature/F-009-alta-albaran-compra`

Alta del 2026-10-01 a petición del líder de albaranes: PRE-1 de albaranes F-053 (alta automática en Sigrid de los albaranes aprobados). v2 con las respuestas del humano (2026-10-01): se AMPLÍA POST sigrid/albaran con un modo extendido elegido por las claves del JSON (lineas o referencia_externa; mezclado con lineas_recibidas -> 400 peticion_mixta); el modo clásico queda idéntico a hoy (incluida la suma de lineas_recibidas al mismo ctrpro), fijado por un test de caracterización escrito sobre dev antes de tocar nada; albaran-directo intacto. Modo extendido: un albarán por petición con líneas vinculadas (ctrpro; consumen medición) y sin vincular (producto por código, lista blanca MA9999), partida por línea (nunca heredada) o almacén, precio del llamante, negativas en los dos tipos (canser < 0 admitido; regla de mov/PMP medida o hipótesis A verificada con la primera devolución real), idempotencia por dca.synckey dentro de la transacción, errores con código y fallos por línea, cod reservado dentro de la transacción. Segunda llave SIGRID_ALBARAN_WRITE_ENABLED (defecto false) para el commit de los dos modos y de albaran-directo. v3 (2026-10-02) con la primera pasada de T0: regla A de devoluciones medida, con.est 1 PDT, plantilla solo del mismo proveedor, fila de alta en log con usu, producto por (emp, cod). v4 (2026-10-02): N1 = el mov se fecha en el alta sin recalcular posteriores; N2 = partida_ambigua rechaza la línea; N3 = el script de T0 se retira de la rama al cerrar T0. Antes de in_progress: repetir T0 de M3, M7, M9, M11, M13 y M14 (progress/spec_F-009.md) y retirar el script. v5 (2026-10-05): incorpora los huecos H2, H3, H10-H19, H21, H26, H27, H32 y H33 de specs/F-009-alta-albaran-compra/contrato_albaranes.md §5 y las decisiones del humano: obra solo en las empresas de SIGRID_ALBARAN_EMPRESAS_OBRA (quinta App Setting) y plantilla y con.emp de la empresa de la obra; imputable sin exigir hoja (H4); precio negativo -> fallo de línea precio_negativo (H8); almacén y centro para toda sin vincular, ficha de obra antes que alm, caaide según M16; lista de reseteo de las sin vincular; IVA de la plantilla del mismo proveedor; tolerancia de precio 0,0001; Decimal ROUND_HALF_UP; sin columnas bancarias en la respuesta; fecha futura rechazada; CIF normalizado; indice desde 0; idempotente con committed false; sin UPDATE de medición si no hay vinculadas (H31). Reglas condicionales a T0: paride opcional (M3, H17), excluir anulados (M17, H9), referencia_linea en dcapro.refent (M18, H18). Puerta dura H20: sin M9 cerrada no hay modo real. Antes de in_progress: UNA repetición de T0 con el script ampliado (--solo M3 M7 M9 M11 M13 M14 M16 M17 M18), su volcado en la spec, la retirada del script. v5.1 (2026-10-05): respuestas del humano a la v5 (progress/spec_F-009.md §v5.1): N4-N9, N11 y N12 aprobadas con la recomendación; SIN campo almacen: en Ruesma «almacén» es dejar la línea sin partida (partida ausente o null -> paride 0, nunca heredada del ctrpro ni de otra línea; almide/cenide del almacén físico en toda línea; aviso sin_partida_en_linea_con_partida en la vinculada cuyo ctrpro tiene partida); pasarla a partida al desacopiar se hace en Sigrid, fuera de la API; SIN fecha_no_valida: la API no rechaza fechas futuras (solo formato y rango; lo hace la app, H19 entero en albaranes; sustituye a N10). v6 (2026-10-05): repetición de T0 (T0b) y decisiones del humano (progress/spec_F-009.md §v6): M3 = 4.312 códigos de partida repetidos entre imputables -> paride opcional con partida (paride_no_valido; F-049 conserva el ide); M7 -> no se escribe dcapropar; M13 -> con.est 1 y fila de log con est 1 y ori 0; M18 -> referencia_linea (1-24) en dcapro.refent y devuelta en idempotente; M14 -> lista de reseteo de las sin vincular ampliada y cerrada (cod2 vacío salvo consulta a negocio); M16 -> orden del almacén confirmado y caaide de las vinculadas siempre el del ctrpro (hipótesis partida/almacén refutada). Decisiones: toda línea es vinculada o lleva un producto de la lista blanca elegido por albaranes línea a línea (despliegue ["MA9999", "QA9999"]; puerta H20 para los dos); la analítica de las sin vincular sale del producto y queda condicional a M16b, sin regla provisional. Abiertas: M9 y M11 (cortadas por tiempo), M14b (forma de pago y efecto), M16b, M17b (o T23). Precondición de in_progress: T0b-bis (--solo M9 M11 M14 M16 M17) volcada y T0c. v7 (2026-10-05): T0b-bis y decisiones del humano (progress/spec_F-009.md §v7): M9 -> mov si y solo si pro.tipmov = 1 para cualquier producto, como el escritorio (H20 cerrado, puerta dura retirada); M11 -> L8b justificada; M14 -> dcapro.prepma = mov.prepma de su mov (corrige R21; su valor, pregunta P1/M14c); M14b -> plantilla L5 se mantiene; M17b -> anular borra el con y el cod se reutiliza (H9 cerrado, R30b retirada); M16b -> sin dcaproana y analítica de las sin vincular = caa <obra>.<sufijo del caagascod de la naturaleza de la línea>, cueide del cuacomcod de esa naturaleza, condicional a M16c; campo opcional naturaleza en la sin vincular (naturaleza_no_valida; si falta, la del producto; qué manda albaranes, consulta a negocio para F-053); analitica_no_resuelta si no existe la caa; lista blanca de despliegue ["MA9999", "QA9999", "XA9999"] (contrato v6.1). v8 (2026-10-06): T0b-ter y T0b-quater, contrato v7.1 y decisiones del humano (progress/spec_F-009.md §v8): XA9999 con tipmov 1 (mov si y solo si tipmov = 1 para los tres de la lista blanca); prepma 0 en la línea sin mov; cueide = la cua del cuacomcod de la naturaleza (P3, P4) y numemp en {0, empresa} (P2); analítica de las sin vincular = caa del centro de la línea con <obra>.<caagascod sin el prefijo MOD.> (M16c/M16d; analitica_no_resuelta si no existe); naturaleza de las sin vincular por un mapeo producto -> naturaleza en la sexta App Setting SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO (defecto {}, despliegue MA9999->MA99, QA9999->QA99, XA9999->XA99; nunca del maestro; naturaleza_no_valida), con el campo opcional naturaleza de la v7 retirado (H34); vinculadas con cod2, dncide y dncproide del ctrpro (H35); mov.prepma = media ponderada global del producto, condicional a M14e. Contrato: solo se toca para actualizar consumos. v8.1 (2026-10-06, T0c; progress/spec_F-009.md §v8.1): T0b-quinquies hecha y T0 cerrada; M14e refuta la media ponderada global (2 de 34 entradas, 4 de 16 devoluciones); mov.prepma (y dcapro.prepma) = el almpma del último mov del mismo producto y almacén antes de la línea (PMP del almacén vigente en el alta, encadenado en el albarán; 0 sin mov anterior), hipótesis coherente con los datos verificada a mano en T22 y T24; fuera L12b-c, E7b sin UPDLOCK y siguiente_prepma; aprobadas por el humano: campo naturaleza retirado, cuacomcod sin una única cua -> naturaleza_no_valida y tex vacío en las sin vincular; script de T0 retirado (N3). Precondición de in_progress: aprobación del humano de la v8.1 (PARADA 1).

### F-007 · Endpoint de dominio para registrar proformas

estado **pendiente** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-007-registrar-proforma`

Alta del 2026-09-24 por petición del humano, anotada sin estudiar todavía. Escritura de dominio en el ERP de producción: dry-run por defecto, commit:true solo con autorización expresa, una transacción, reserva de ide y de código de serie bajo applock, idempotencia frente a reintentos. La spec mide antes en producción (solo lectura) qué filas escribe Sigrid al hacerlo desde la UI. Relación con postventa-incidencias (F-046/F-047: coste de la posventa y vínculo de la incidencia con la proforma, el coste y la venta). Proforma = albarán proforma de subcontratista (manual de Postventa de Sigrid, «Documentos de compras»): trabajos realizados que se pueden facturar. Qué tipo de concepto, serie y tablas usa Sigrid, y su relación con el contrato y con la reclamación, los investiga la spec. Estudiar si reutiliza create_purchase_albaran_use_case.

### F-008 · Endpoint de dominio para registrar facturas de compra

estado **pendiente** · prioridad 9 · rigor `critico` · SDD sí · rama `feature/F-008-registrar-factura`

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

### F-006 · Endpoint de dominio para crear partes de reclamación de Posventa, en lote

estado **terminada** · prioridad 6 · rigor `critico` · SDD sí · rama `feature/F-006-alta-parte-reclamacion`

Alta del 2026-09-24 por petición del humano. Crear en Sigrid partes de reclamación de Posventa (con.tip 708, serie RS<aa>.<mm>/) como lo hace la UI segun docs/referencia/postventa_pasos_crear_parte.md (referencia principal) y postventa_manual_sigrid.md: desde la unidad postventa, descripcion, tipo de reclamacion, oficio e intervinientes (rcpint -> obrofc de la obra). Lo consume postventa-incidencias F-040 (volcado masivo de incidencias aprobadas). DECISIONES DEL HUMANO (2026-09-24): (1) endpoint de LOTE con tope (~50), CADA PARTE EN SU PROPIA TRANSACCION y respuesta parte a parte, reutilizando las lecturas comunes de la obra; (2) idempotencia por REFERENCIA EXTERNA que aporta quien llama, guardada en un campo de Sigrid (la spec mide cual; candidato: el 'N. Referencia Externo' del importador Excel de Sigrid, con el posible conflicto de la referencia del promotor); (3) tipo de reclamacion por defecto 0002 PRIMER LISTADO POSTVENTA, informable en la peticion. Propuesta aceptada: peticion por codigos, no por ide; interviniente que no este en los oficios de la obra -> se rechaza el parte; el parte nace en su estado inicial y NO se pasa a PTE (proceso de Sigrid que crea tareas y envia correos); codigo de serie calculado DENTRO de la transaccion bajo applock; interruptor propio apagado por defecto ademas de SIGRID_DOMAIN_WRITE_ENABLED; dry-run por defecto. Fuera: pasar a PTE, tareas, correos del portal, fotos (ya van por concepto-grafico), alta de unidades postventa u oficios de obra.
