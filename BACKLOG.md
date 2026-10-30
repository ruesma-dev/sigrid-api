<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **18 features**, 7 abiertas, 11 terminadas.

Bloqueadas: **F-015, F-016**.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-001 | Test de calentamiento: el guardia de escritura rechaza una base no permitida | 1 | pendiente | estandar | `feature/F-001-calentamiento` |
| F-016 | sigrid/proforma registra también proformas a origen, según indique el jefe de obra | 8 | bloqueada | critico | `feature/F-016-proforma-a-origen` |
| F-008 | Endpoint de dominio para registrar facturas de compra | 10 | pendiente | critico | `feature/F-008-registrar-factura` |
| F-013 | sql/read aplica timeout_seconds como tope de la consulta, no solo del login | 13 | pendiente | critico | `feature/F-013-sql-read-timeout` |
| F-014 | Los dry-run de dominio validan la base contra ALLOWED_DATABASES | 14 | pendiente | critico | `feature/F-014-dry-run-valida-base` |
| F-015 | El modo extendido de sigrid/albaran no hereda la cabecera de una proforma y escribe la retención del contrato | 15 | bloqueada | critico | `feature/F-015-albaran-plantilla-y-retencion` |
| F-017 | Partidas con el código repetido en la obra: líneas sin contrato de sigrid/proforma | 16 | pendiente | critico | `feature/F-017-partidas-repetidas` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-002 | Spike: viabilidad de escribir en la base documental ruesma_rep | 2 | critico |
| F-003 | El guardia de escritura debe validar tambien las bases nombradas dentro del SQL | 3 | critico |
| F-004 | Endpoint de dominio para adjuntar un documento a un concepto de Sigrid | 4 | critico |
| F-005 | concepto-grafico admite documentos sin clase de grafico, como Sigrid en contratos y albaranes | 5 | critico |
| F-006 | Endpoint de dominio para crear partes de reclamación de Posventa, en lote | 6 | critico |
| F-009 | Modo extendido de sigrid/albaran: alta idempotente de albaranes de compra del pipeline (PRE-1 de albaranes F-053) | 7 | critico |
| F-007 | Endpoint de dominio para registrar proformas | 8 | critico |
| F-018 | Descuento por línea (dto) en el alta de albarán, heredado por sigrid/proforma | 9 | critico |
| F-010 | documents/read: nombres de fichero no ASCII sin 500 y localización de la fila sin ambigüedad | 10 | critico |
| F-011 | documents/read valida database contra ALLOWED_DATABASES y _connect valida el nombre de base para toda la API | 11 | critico |
| F-012 | Los 400 de validación no acaban en 500 cuando el error de pydantic trae una excepción en ctx | 12 | estandar |

## Detalle

### F-001 · Test de calentamiento: el guardia de escritura rechaza una base no permitida

estado **pendiente** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-calentamiento`

Feature trivial para validar el circuito completo del arnés en este repositorio (rama, acceptance, implementer, reviewer, cierre). Anade un test unitario sobre SqlWriteGuard que fije por escrito la regla que hoy solo vive en configuracion: una peticion de escritura contra una base fuera de ALLOWED_WRITE_DATABASES (p.ej. ruesma_rep) se rechaza.

### F-016 · sigrid/proforma registra también proformas a origen, según indique el jefe de obra

estado **bloqueada** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-016-proforma-a-origen`

Alta del 2026-10-28 por decisión del humano (V8 de F-007): la proforma se tiene que poder registrar a origen o por meses según indique el jefe de obra en proformas; por defecto, por meses. F-007 (desplegada, solo de mes) queda como está y la petición sin el campo nuevo sigue igual. A origen (medido en progress/explore_F-007.md §M11 y §M16-M26, en la rama de F-007; diseño v2 superado): dca.docoritip 1 y docoriide = la anterior de la cadena del contrato (cadenas paralelas por partidas, serie mezclada PROF/AC), la proforma arrastra todas las líneas de la anterior (también con can 0), canorilin a la línea anterior del mismo ctrpro y canoriori acumulado. Spec v2 (cambio de alcance del humano, 2026-10-28): el modo, la anterior y qué línea continúa cada una los decide y los busca en Sigrid el llamante (proformas); la API solo registra y valida la integridad de la cadena. Cambios en el contrato con proformas: v1.2. Escritura de dominio en el ERP de producción: dry-run por defecto; commit:true con la llave SIGRID_PROFORMA_WRITE_ENABLED (y, a origen, SIGRID_PROFORMA_ORIGEN_ENABLED) y autorización expresa. Avisar a proformas (y a facturas si cambia lo que lee) antes del despliegue.

### F-008 · Endpoint de dominio para registrar facturas de compra

estado **pendiente** · prioridad 10 · rigor `critico` · SDD sí · rama `feature/F-008-registrar-factura`

Alta del 2026-09-24 por petición del humano, anotada sin estudiar todavía. Escritura de dominio en el ERP de producción: dry-run por defecto, commit:true solo con autorización expresa, una transacción, reserva de ide y de código de serie bajo applock, idempotencia frente a reintentos. La spec mide antes en producción (solo lectura) qué filas escribe Sigrid al hacerlo desde la UI. Relación con postventa-incidencias (F-046/F-047: coste de la posventa y vínculo de la incidencia con la proforma, el coste y la venta). Facturas de COMPRA (de proveedor, las que imputan coste): decidido por el humano el 2026-09-24. Una factura en Sigrid arrastra contabilidad y estados de los documentos de origen (albaranes, proformas): la spec decide qué recalcula el endpoint y qué deja a Sigrid, y si cabe en este microservicio.

### F-013 · sql/read aplica timeout_seconds como tope de la consulta, no solo del login

estado **pendiente** · prioridad 13 · rigor `critico` · SDD sí · rama `feature/F-013-sql-read-timeout`

Alta del 2026-10-18 a petición del humano (hallazgo del reviewer de F-009 T0a-bis, 2026-10-05). infrastructure/repositories/sql_server_repository.py pasa timeout_seconds a pyodbc.connect(timeout=…), que es el tiempo de login; los casos de uso de dominio sí fijan cursor.connection.timeout. Una lectura que el balanceador corta a los 230 s sigue corriendo en el SQL Server de producción (causa verosímil del 1205 y de los 121 s de M14 en F-009 T0b). Afecta a todos los consumidores de sql/read: la spec decide el tope por defecto y el máximo, y cómo responde la API cuando salta (error claro, sin filas a medias).

### F-014 · Los dry-run de dominio validan la base contra ALLOWED_DATABASES

estado **pendiente** · prioridad 14 · rigor `critico` · SDD sí · rama `feature/F-014-dry-run-valida-base`

Alta del 2026-10-18 a petición del humano: residual de F-011 (progress/review_F-011_C3.md). En dry-run, sigrid/contrato-lineas, sigrid/albaran clásico y extendido y sigrid/albaran-directo conectan con request.database sin lista blanca (la de escritura solo se mira con commit). Desde F-011 un nombre fuera del patrón se rechaza en _connect, pero una base que case con él y a la que llegue ro_user (p. ej. master) se sigue leyendo con el SQL fijo de esas previas. Cambio de seguridad pequeño que toca a los consumidores de esos endpoints: avisarles antes del despliegue.

### F-015 · El modo extendido de sigrid/albaran no hereda la cabecera de una proforma y escribe la retención del contrato

estado **bloqueada** · prioridad 15 · rigor `critico` · SDD sí · rama `feature/F-015-albaran-plantilla-y-retencion`

Alta del 2026-10-18 a petición del humano: O1 y O2 medidos por la spec de F-007 (progress/explore_F-007.md §M10 y §M14, en la rama feature/F-007-registrar-proforma). F-009 está desplegada con SIGRID_ALBARAN_WRITE_ENABLED=true y la usará F-053 de albaranes en real: conviene cerrarla antes. O1: la plantilla de cabecera (L5 de F-009, último dca del proveedor sin filtrar serie) es una proforma PROF<aa>/ en 17 de 831 proveedores con AC26; el albarán nacería con dca.cla 141, docoritip/docoriide, ivadif y campos de facturación de la proforma. O2: F-009 no escribe dcarec; el 88,5 % de los AC26 de contratos con ctrrec la llevan (RET5: bas = totbas, cuo = round(bas·valpor, 2), dca.tot = totdoc − cuo). La spec decide de dónde sale la plantilla (solo serie AC, sercon 87) y cómo se copia la retención del contrato (ctrrec → dcarec, cueide/valpor/pos), mide los casos raros (4,6 % con cueide distinto, retenciones sobre total) y deja a verificación del humano lo que solo se ve en la UI. Toca el contrato con albaranes (§2-§4 congelado): avisar a la sesión de albaranes ANTES de cambiarlo.

### F-017 · Partidas con el código repetido en la obra: líneas sin contrato de sigrid/proforma

estado **pendiente** · prioridad 16 · rigor `critico` · SDD sí · rama `feature/F-017-partidas-repetidas`

Alta del 2026-10-28 por decisión del humano (V8 de F-007, punto 3). Una línea sin contrato de sigrid/proforma con un código de partida que la obra tiene repetido entre sus imputables da 400 partida_ambigua, y la petición no admite paride. Según el humano «no debería haber». Medido el 2026-10-28 (solo lectura): 4 de las 16 obras con PROF26 — 0677 (40.04.01 y 40.04.02, partidas distintas con compras), 0672 (20.02.05), 0692 (CI.6.1-CI.6.7 en los capítulos CI.6 y CI.06) y 0404 (pruebas, presupuesto cargado 5 veces). Las líneas de contrato no se ven afectadas (llevan el paride del ctrpro). La spec decide entre detectarlo y avisar para que se corrija en Sigrid, admitir paride o una regla de desempate, con Administración.

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

### F-009 · Modo extendido de sigrid/albaran: alta idempotente de albaranes de compra del pipeline (PRE-1 de albaranes F-053)

estado **terminada** · prioridad 7 · rigor `critico` · SDD sí · rama `feature/F-009-alta-albaran-compra`

Alta del 2026-10-01 a petición del líder de albaranes: PRE-1 de albaranes F-053 (alta automática en Sigrid de los albaranes aprobados). v2 con las respuestas del humano (2026-10-01): se AMPLÍA POST sigrid/albaran con un modo extendido elegido por las claves del JSON (lineas o referencia_externa; mezclado con lineas_recibidas -> 400 peticion_mixta); el modo clásico queda idéntico a hoy (incluida la suma de lineas_recibidas al mismo ctrpro), fijado por un test de caracterización escrito sobre dev antes de tocar nada; albaran-directo intacto. Modo extendido: un albarán por petición con líneas vinculadas (ctrpro; consumen medición) y sin vincular (producto por código, lista blanca MA9999), partida por línea (nunca heredada) o almacén, precio del llamante, negativas en los dos tipos (canser < 0 admitido; regla de mov/PMP medida o hipótesis A verificada con la primera devolución real), idempotencia por dca.synckey dentro de la transacción, errores con código y fallos por línea, cod reservado dentro de la transacción. Segunda llave SIGRID_ALBARAN_WRITE_ENABLED (defecto false) para el commit de los dos modos y de albaran-directo. v3 (2026-10-02) con la primera pasada de T0: regla A de devoluciones medida, con.est 1 PDT, plantilla solo del mismo proveedor, fila de alta en log con usu, producto por (emp, cod). v4 (2026-10-02): N1 = el mov se fecha en el alta sin recalcular posteriores; N2 = partida_ambigua rechaza la línea; N3 = el script de T0 se retira de la rama al cerrar T0. Antes de in_progress: repetir T0 de M3, M7, M9, M11, M13 y M14 (progress/spec_F-009.md) y retirar el script. v5 (2026-10-05): incorpora los huecos H2, H3, H10-H19, H21, H26, H27, H32 y H33 de specs/F-009-alta-albaran-compra/contrato_albaranes.md §5 y las decisiones del humano: obra solo en las empresas de SIGRID_ALBARAN_EMPRESAS_OBRA (quinta App Setting) y plantilla y con.emp de la empresa de la obra; imputable sin exigir hoja (H4); precio negativo -> fallo de línea precio_negativo (H8); almacén y centro para toda sin vincular, ficha de obra antes que alm, caaide según M16; lista de reseteo de las sin vincular; IVA de la plantilla del mismo proveedor; tolerancia de precio 0,0001; Decimal ROUND_HALF_UP; sin columnas bancarias en la respuesta; fecha futura rechazada; CIF normalizado; indice desde 0; idempotente con committed false; sin UPDATE de medición si no hay vinculadas (H31). Reglas condicionales a T0: paride opcional (M3, H17), excluir anulados (M17, H9), referencia_linea en dcapro.refent (M18, H18). Puerta dura H20: sin M9 cerrada no hay modo real. Antes de in_progress: UNA repetición de T0 con el script ampliado (--solo M3 M7 M9 M11 M13 M14 M16 M17 M18), su volcado en la spec, la retirada del script. v5.1 (2026-10-05): respuestas del humano a la v5 (progress/spec_F-009.md §v5.1): N4-N9, N11 y N12 aprobadas con la recomendación; SIN campo almacen: en Ruesma «almacén» es dejar la línea sin partida (partida ausente o null -> paride 0, nunca heredada del ctrpro ni de otra línea; almide/cenide del almacén físico en toda línea; aviso sin_partida_en_linea_con_partida en la vinculada cuyo ctrpro tiene partida); pasarla a partida al desacopiar se hace en Sigrid, fuera de la API; SIN fecha_no_valida: la API no rechaza fechas futuras (solo formato y rango; lo hace la app, H19 entero en albaranes; sustituye a N10). v6 (2026-10-05): repetición de T0 (T0b) y decisiones del humano (progress/spec_F-009.md §v6): M3 = 4.312 códigos de partida repetidos entre imputables -> paride opcional con partida (paride_no_valido; F-049 conserva el ide); M7 -> no se escribe dcapropar; M13 -> con.est 1 y fila de log con est 1 y ori 0; M18 -> referencia_linea (1-24) en dcapro.refent y devuelta en idempotente; M14 -> lista de reseteo de las sin vincular ampliada y cerrada (cod2 vacío salvo consulta a negocio); M16 -> orden del almacén confirmado y caaide de las vinculadas siempre el del ctrpro (hipótesis partida/almacén refutada). Decisiones: toda línea es vinculada o lleva un producto de la lista blanca elegido por albaranes línea a línea (despliegue ["MA9999", "QA9999"]; puerta H20 para los dos); la analítica de las sin vincular sale del producto y queda condicional a M16b, sin regla provisional. Abiertas: M9 y M11 (cortadas por tiempo), M14b (forma de pago y efecto), M16b, M17b (o T23). Precondición de in_progress: T0b-bis (--solo M9 M11 M14 M16 M17) volcada y T0c. v7 (2026-10-05): T0b-bis y decisiones del humano (progress/spec_F-009.md §v7): M9 -> mov si y solo si pro.tipmov = 1 para cualquier producto, como el escritorio (H20 cerrado, puerta dura retirada); M11 -> L8b justificada; M14 -> dcapro.prepma = mov.prepma de su mov (corrige R21; su valor, pregunta P1/M14c); M14b -> plantilla L5 se mantiene; M17b -> anular borra el con y el cod se reutiliza (H9 cerrado, R30b retirada); M16b -> sin dcaproana y analítica de las sin vincular = caa <obra>.<sufijo del caagascod de la naturaleza de la línea>, cueide del cuacomcod de esa naturaleza, condicional a M16c; campo opcional naturaleza en la sin vincular (naturaleza_no_valida; si falta, la del producto; qué manda albaranes, consulta a negocio para F-053); analitica_no_resuelta si no existe la caa; lista blanca de despliegue ["MA9999", "QA9999", "XA9999"] (contrato v6.1). v8 (2026-10-06): T0b-ter y T0b-quater, contrato v7.1 y decisiones del humano (progress/spec_F-009.md §v8): XA9999 con tipmov 1 (mov si y solo si tipmov = 1 para los tres de la lista blanca); prepma 0 en la línea sin mov; cueide = la cua del cuacomcod de la naturaleza (P3, P4) y numemp en {0, empresa} (P2); analítica de las sin vincular = caa del centro de la línea con <obra>.<caagascod sin el prefijo MOD.> (M16c/M16d; analitica_no_resuelta si no existe); naturaleza de las sin vincular por un mapeo producto -> naturaleza en la sexta App Setting SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO (defecto {}, despliegue MA9999->MA99, QA9999->QA99, XA9999->XA99; nunca del maestro; naturaleza_no_valida), con el campo opcional naturaleza de la v7 retirado (H34); vinculadas con cod2, dncide y dncproide del ctrpro (H35); mov.prepma = media ponderada global del producto, condicional a M14e. Contrato: solo se toca para actualizar consumos. v8.1 (2026-10-06, T0c; progress/spec_F-009.md §v8.1): T0b-quinquies hecha y T0 cerrada; M14e refuta la media ponderada global (2 de 34 entradas, 4 de 16 devoluciones); mov.prepma (y dcapro.prepma) = el almpma del último mov del mismo producto y almacén antes de la línea (PMP del almacén vigente en el alta, encadenado en el albarán; 0 sin mov anterior), hipótesis coherente con los datos verificada a mano en T22 y T24; fuera L12b-c, E7b sin UPDLOCK y siguiente_prepma; aprobadas por el humano: campo naturaleza retirado, cuacomcod sin una única cua -> naturaleza_no_valida y tex vacío en las sin vincular; script de T0 retirado (N3). Precondición de in_progress: aprobación del humano de la v8.1 (PARADA 1).

### F-007 · Endpoint de dominio para registrar proformas

estado **terminada** · prioridad 8 · rigor `critico` · SDD sí · rama `feature/F-007-registrar-proforma`

Alta del 2026-09-24 por petición del humano; spec v3 (2026-10-25) y enmienda 1 (2026-10-26). POST /api/sigrid/proforma registra UNA proforma de mes de un subcontratista —la hoja del jefe de obra ya leída y casada por el microservicio proformas (su F-005), que la llama desde su bandeja: previa antes de aprobar y grabación al aprobar— como un albarán de compra tip 14 de la serie PROF<aa>/ con dca.cla 141, solo con las partidas de MES ≠ 0: las de contrato vinculadas a su ctrpro (ctrpro_ide), las nuevas sin vincular con su producto. El contrato lo resuelve la API (obra + proveedor y, con varios, las líneas) o lo fija cod_contrato; cabecera y retención como F-015; existente si la proforma del contrato y mes ya está en Sigrid; idempotente por la referencia PRF-<id>. Reutiliza el núcleo del modo extendido de sigrid/albaran (F-009) con otro perfil, sin cambiar su conducta. Escritura de dominio en el ERP de producción: dry-run por defecto; commit:true con su propia llave SIGRID_PROFORMA_WRITE_ENABLED y autorización expresa. facturas lee lo registrado por el entref PROF<MMAA>_<cod_obra>. Contrato: specs/F-007-registrar-proforma/contrato_proformas.md.

### F-018 · Descuento por línea (dto) en el alta de albarán, heredado por sigrid/proforma

estado **terminada** · prioridad 9 · rigor `critico` · SDD sí · rama `feature/F-018-descuento-por-linea`

Alta del 2026-10-28 a petición de la sesión albaranes (su F-110), con el sí del humano, que la fija como la siguiente feature tras F-016. Las líneas con descuento (albaranes de CECOIS, obra 0692) acaban en Sigrid con el unitario ya descontado porque sigrid/albaran (modo extendido, F-009/F-015) solo admite cantidad y precio y sv9 manda precio = importe / cantidad. Se pide lineas[].dto opcional (porcentaje 0-100, hasta 2 decimales, sin cascada): dcapro.pre = precio bruto, dcapro.dto = dto, importe de línea y totales de dca con el descuento aplicado como la UI de Sigrid; la previa devuelve dto e importe por línea; sin dto o con 0, todo igual que hoy. A decidir en la spec, midiendo antes en producción (solo lectura): formato de dcapro.dto (texto, admite cascada), tot y redondeo, impbru/totbas, precio del mov y PMP, ctrprodes y canser; en las vinculadas el ctrpro ya aporta pre/tar/dto si el precio cuadra (H14 C) y la inclinación es validar el dto de la línea contra el del ctrpro, no pisarlo; si aplica a sigrid/proforma. Al publicar el contrato, documentarlo en azure-apps/sigrid_api.md y avisar a albaranes (F-110). Decidido en la spec v1.2 (humano, P1-P11): tar bruto y pre neto = tot/can como Sigrid; la vinculada sin dto que casa por la opción C con un ctrpro con dto se escribe como Sigrid (P5, R15); sigrid/proforma no admite dto en la petición (R20) pero hereda R15 (P8 = a).

### F-010 · documents/read: nombres de fichero no ASCII sin 500 y localización de la fila sin ambigüedad

estado **terminada** · prioridad 10 · rigor `critico` · SDD sí · rama `feature/F-010-documents-read-nombres-y-clave`

Alta del 2026-10-16 a propuesta de datamart-seg-anual (F-139) y mcp-bbdd (F-023), que van a abrir adjuntos de Sigrid para la IA. (1) binary_file_response (interface_adapters/http/http_response_factory.py) manda X-Document-Filename sin codificar; el host de Functions rechaza la cabecera no ASCII y responde 500 con cuerpo vacío (fuera del try del handler). Reproducido por el líder el 2026-10-16 contra la API desplegada: ruesma_rep.dbo.gra ide 365617 con filename_columns [nomori] -> 500 vacío; con [cod] -> 200. Datamart midió 11.262 de 199.032 adjuntos de compras (5,7 %) afectados. sigrid-api-v2 tiene la misma línea (responses.py:62), fuera de este repo. (2) read_document hace SELECT TOP (1) ... WHERE [id_column] = ?: si la columna no es única sirve una fila cualquiera sin avisar. En gra los índices únicos son gra_indide (ide, PK) y gra_empcod (emp, cod); cod solo no tiene restricción (hoy 365.617 filas, 365.617 cod distintos, 25 emp). Propuesta del consumidor: clave compuesta opcional (key: {col: valor}, cada nombre por IdentifierGuard, AND) manteniendo id_column/id_value, y error si hay más de una fila. Actualizar azure-apps/sigrid_api.md §8.3 en el mismo trabajo.

### F-011 · documents/read valida database contra ALLOWED_DATABASES y _connect valida el nombre de base para toda la API

estado **terminada** · prioridad 11 · rigor `critico` · SDD sí · rama `feature/F-011-documents-read-valida-database`

Alta del 2026-10-18 a petición del humano: D6 de F-010 (progress/spec_F-010.md), confirmado por el líder en el código. POST documents/read no valida `database` contra ALLOWED_DATABASES (ni DocumentReadRequest en domain/models/sql_models.py, que solo hace strip; ni ReadDocumentUseCase; ni la ruta en function_app.py), mientras que sql/read sí lo hace con SqlQueryGuard. Además infrastructure/repositories/sql_server_repository.py _connect interpola `database` sin escapar en la cadena de conexión (DATABASE={database};), así que un valor con ';' o '=' podría añadir atributos a la cadena ODBC. Hace falta la function key para explotarlo. Consumidores conocidos (mcp-bbdd F-023, datamart F-139, albaranes-persistencia) mandan la constante ruesma_rep, ya permitida: no se rompe ninguno. Decisiones para la spec: dónde validar (modelo, caso de uso o guardia reutilizado) y si además se blinda _connect para TODOS los endpoints, lo que tocaría infraestructura compartida y quizá infrastructure/security/ (cambio de seguridad explícito). Actualizar azure-apps/sigrid_api.md §8.3 en el mismo trabajo.

### F-012 · Los 400 de validación no acaban en 500 cuando el error de pydantic trae una excepción en ctx

estado **terminada** · prioridad 12 · rigor `estandar` · SDD sí · rama `feature/F-012-validacion-sin-500`

Alta del 2026-10-18 a petición del humano (hallazgo de progress/review_F-011_C3.md, reproducido; previo, de F-009). En el modo extendido de sigrid/albaran un error de model_validator (p. ej. línea vinculada sin cod_contrato) deja un ValueError en `ctx` de exc.errors() y error_response falla con `TypeError: Object of type ValueError is not JSON serializable`: albaranes recibe un 500 mudo en vez del 400 con el detalle. function_app.py serializa `exc.errors()` tal cual en 9 rutas (l. 105, 143, 179, 237, 271, 330, 388, 443, 504): la spec mide en cuáles puede pasar y decide el arreglo común (exc.errors(include_context=False), un saneado único o equivalente) sin cambiar la forma de `details.validation` que leen los consumidores.
