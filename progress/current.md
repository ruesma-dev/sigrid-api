<!-- progress/current.md -->
# Trabajo en curso

## 2026-09-03 · Instalación del arnés y spike de `ruesma_rep`

**Rama:** `chore/instalar-arnes` (no es rama de feature: la instalación del
arnés no pasa por el flujo SDD).

### Hecho

1. **Arnés v1.7.8 instalado y adaptado** (commit `240257d`). `bash
   harness/init.sh` termina en **ENTORNO LISTO**: 341 tests en verde, 1 skip;
   `ruff` avisa de 79 puntos de deuda previa, que no bloquean
   (`LINT_BLOQUEA=0`, como recomienda la guía para repos con historia).
   Se añadió `requirements-dev.txt` (pytest, ruff, coverage), que el arnés
   necesita y el despliegue no.

2. **Spike de F-002 adelantado, solo con lecturas y una prueba de permisos que
   no escribe filas.** Resultado en
   **[`progress/explore_ruesma_rep.md`](explore_ruesma_rep.md)**. En corto:
   - `ruesma_rep` es `READ_WRITE`, misma instancia que `ruesma`, sin
     replicación, y el ERP le escribe ~200 filas cada día laborable.
   - **`user_rw` ya puede insertar en `ruesma_rep.dbo.gra`.** No hace falta
     ningún `GRANT`.
   - La base documental tiene **una sola tabla**, `dbo.gra`, con índice único
     por `(emp, cod)`.
   - El motor es **SQL Server 2012**: `HASHBYTES` no sirve para el binario, el
     `sha256` hay que calcularlo en Python.

### Parada: el portero está en ROJO y hacen falta dos cosas del humano

1. **Aprobar la spec de F-003** (`specs/F-003-guardia-bases-cruzadas/`), que
   está en `spec_ready`. Con «F-003 aprobada, pásala a in_progress y continúa»
   arranca el implementer.
2. **Mergear `chore/instalar-arnes` a `dev`.** Mientras el arnés no esté en la
   rama base, la puerta de cobertura compara la rama de feature contra un `dev`
   sin arnés y mide **625 líneas cambiadas con 0 % de cobertura**, que son las
   del propio arnés, no las de la feature. `bash harness/init.sh` termina en
   rojo por eso y solo por eso. El merge lo hace el humano, nunca el agente.

### Pendiente de decisión del humano

- **Hallazgo de seguridad**: `SqlWriteGuard` valida el campo `database` de la
  petición, no las bases nombradas dentro del SQL. La política «`ruesma_rep`
  no se escribe» no está realmente aplicada. Ver §3.3 del informe.
- **`ALLOWED_DATABASES` incluye `master`** en la Function App desplegada.
- **`MAX_ALLOWED_ROWS = 500000`** desplegado, frente a los 1.000 que documenta
  `azure-apps/sigrid_api.md`.
- Si se sigue adelante con el endpoint de adjuntar documento, hay que
  actualizar `docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md`: sus
  Q1, Q2, Q3 y Q6 ya están medidas, y la de SQL Server 2012 le cambia el
  diseño de idempotencia.
- **Corregir `azure-apps/`**: `dedicacion.md`, `partes.md` y `remesas.md`
  llaman a `ruesma_rep` «réplica que no admite escritura». Está medido que es
  falso.

### No hecho, deliberadamente

- **Ninguna fila escrita en Sigrid.** Las tres sentencias de prueba llevaban
  `WHERE 1 = 0`.
- F-001 y F-002 siguen en `pending`: el flujo SDD no se ha arrancado todavía.
