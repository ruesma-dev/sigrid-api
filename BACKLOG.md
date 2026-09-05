<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **4 features**, 1 abiertas, 3 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-001 | Test de calentamiento: el guardia de escritura rechaza una base no permitida | 1 | pendiente | estandar | `feature/F-001-calentamiento` |

## Terminadas

| # | Feature | Prioridad | Rigor |
|---|---|---|---|
| F-002 | Spike: viabilidad de escribir en la base documental ruesma_rep | 2 | critico |
| F-003 | El guardia de escritura debe validar tambien las bases nombradas dentro del SQL | 3 | critico |
| F-004 | Endpoint de dominio para adjuntar un documento a un concepto de Sigrid | 4 | critico |

## Detalle

### F-001 · Test de calentamiento: el guardia de escritura rechaza una base no permitida

estado **pendiente** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-calentamiento`

Feature trivial para validar el circuito completo del arnés en este repositorio (rama, acceptance, implementer, reviewer, cierre). Anade un test unitario sobre SqlWriteGuard que fije por escrito la regla que hoy solo vive en configuracion: una peticion de escritura contra una base fuera de ALLOWED_WRITE_DATABASES (p.ej. ruesma_rep) se rechaza.

### F-002 · Spike: viabilidad de escribir en la base documental ruesma_rep

estado **terminada** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-spike-escritura-ruesma-rep`

Averiguar si es posible, y con que garantias, escribir adjuntos en ruesma_rep (base documental de Sigrid). Hoy esta deliberadamente fuera de ALLOWED_WRITE_DATABASES y solo se lee. Incluye: modelo real de las tablas documentales, permisos del usuario user_rw sobre esa base, como enlaza Sigrid un documento con su concepto, y que haria falta en la API. Prerrequisito de la propuesta docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md. Solo lectura y diagnostico salvo autorizacion expresa del humano para una escritura concreta. RESUELTO el 2026-09-03: ruesma_rep es READ_WRITE, misma instancia, sin replicacion, y user_rw ya tiene INSERT sobre su unica tabla dbo.gra (medido con INSERT ... WHERE 1=0 y control negativo que devuelve 229). No hace falta ningun GRANT. Informe completo en progress/explore_ruesma_rep.md.

### F-003 · El guardia de escritura debe validar tambien las bases nombradas dentro del SQL

estado **terminada** · prioridad 3 · rigor `critico` · SDD sí · rama `feature/F-003-guardia-bases-cruzadas`

SqlWriteGuard valida el campo 'database' de la peticion, pero no los identificadores de base que aparecen dentro de la sentencia. Por eso hoy se puede escribir en ruesma_rep pidiendo database='ruesma' y nombrando ruesma_rep.dbo.gra en el SQL: medido el 2026-09-03. La politica de ALLOWED_WRITE_DATABASES no esta realmente aplicada. Va antes que F-004 porque F-004 depende de que la documental siga cerrada a sql/write.

### F-004 · Endpoint de dominio para adjuntar un documento a un concepto de Sigrid

estado **terminada** · prioridad 4 · rigor `critico` · SDD sí · rama `feature/F-004-endpoint-concepto-grafico`

Implementar POST /api/sigrid/concepto-grafico segun docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md, actualizada con lo medido en F-002. Hace las tres escrituras en una sola transaccion local (binario en ruesma_rep.gra, metadatos en ruesma.gra con el mismo cod, enlace en ruesma.rcg) y no abre sql/write a la base documental. Dry-run por defecto. Lo pide postventa-incidencias F-012.
