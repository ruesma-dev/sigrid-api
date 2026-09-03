<!-- BACKLOG.md -->
# Backlog

**Fichero generado por `harness/backlog.py` a partir de `harness/features.json`. No lo edites a mano**: edita el JSON y vuelve a generarlo (lo hace solo `bash harness/init.sh`).

Resumen: **2 features**, 2 abiertas, 0 terminadas.

## Trabajo abierto

| # | Feature | Prioridad | Estado | Rigor | Rama |
|---|---|---|---|---|---|
| F-001 | Test de calentamiento: el guardia de escritura rechaza una base no permitida | 1 | pendiente | estandar | `feature/F-001-calentamiento` |
| F-002 | Spike: viabilidad de escribir en la base documental ruesma_rep | 2 | pendiente | critico | `feature/F-002-spike-escritura-ruesma-rep` |

## Terminadas

_Todavía no hay features terminadas._

## Detalle

### F-001 · Test de calentamiento: el guardia de escritura rechaza una base no permitida

estado **pendiente** · prioridad 1 · rigor `estandar` · SDD no · rama `feature/F-001-calentamiento`

Feature trivial para validar el circuito completo del arnés en este repositorio (rama, acceptance, implementer, reviewer, cierre). Anade un test unitario sobre SqlWriteGuard que fije por escrito la regla que hoy solo vive en configuracion: una peticion de escritura contra una base fuera de ALLOWED_WRITE_DATABASES (p.ej. ruesma_rep) se rechaza.

### F-002 · Spike: viabilidad de escribir en la base documental ruesma_rep

estado **pendiente** · prioridad 2 · rigor `critico` · SDD sí · rama `feature/F-002-spike-escritura-ruesma-rep`

Averiguar si es posible, y con que garantias, escribir adjuntos en ruesma_rep (base documental de Sigrid). Hoy esta deliberadamente fuera de ALLOWED_WRITE_DATABASES y solo se lee. Incluye: modelo real de las tablas documentales, permisos del usuario user_rw sobre esa base, como enlaza Sigrid un documento con su concepto, y que haria falta en la API. Prerrequisito de la propuesta docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md. Solo lectura y diagnostico salvo autorizacion expresa del humano para una escritura concreta.
