<!-- progress/current.md -->
# Trabajo en curso

> **F-005 implementada el 2026-09-06 y pendiente del reviewer.** Rama
> `feature/F-005-grafico-sin-clase`, SHA de código `cfb8048`, `init.sh` en
> verde (1.502 tests, cobertura 100 % de las 7 líneas cambiadas, mutación
> 6/6 muertos y 0 supervivientes). El informe está en
> [`impl_F-005.md`](impl_F-005.md) y la campaña en
> [`mutacion_F-005.md`](mutacion_F-005.md).
>
> `sigrid/concepto-grafico` admite ya `gratipide = 0` («sin clase»), que es
> como Sigrid adjunta en contratos (`con.tip` 44) y albaranes de compra
> (`tip` 14). **Solo si el `0` se pone explícitamente en
> `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`**: el defecto de la App Setting no
> cambia y sin tocar configuración el comportamiento es el de F-004.
>
> **Nada de esta sesión tocó la API desplegada ni el ERP.** Queda del humano
> la prueba manual (criterio 8): ampliar las App Settings a
> `ALLOWED_CONTIP=[708,44,14]` y `ALLOWED_GRATIPIDE=[35,0]` y hacer el
> dry-run y el primer `commit:true` sobre la obra **0404**.
>
> **F-004 quedó cerrada el 2026-09-06 con veredicto APROBADO.** Lo suyo, y el
> merge pendiente, sigue documentado abajo.

## Lo que espera al humano, por orden

1. **Merge de `feature/F-004-endpoint-concepto-grafico` a `dev`** y push (los
   agentes no empujan). `azure-apps` tiene commits locales (`a40684f`,
   `157b392`) y **no tiene remoto**.
2. **T18-T21 HECHAS el 2026-09-06.** Desplegado `70ac430`, App Settings
   cerradas, dry-run en verde
   ([`verificacion_F-004_t18_t19.md`](verificacion_F-004_t18_t19.md)) y el
   **primer `commit:true` real**, autorizado por el humano, sobre la
   reclamación 2811179 con `usu=prueba`: tres filas escritas, `sha256`
   idéntico por `documents/read`, sin huérfanos, repetición idempotente
   ([`verificacion_F-004_t20_t21.md`](verificacion_F-004_t20_t21.md)).
   El humano abrió el gráfico desde la ficha de Sigrid (obra 0677, PDF en
   blanco, correcto) y ordenó **abrir el endpoint**: desde el 2026-09-06
   `SIGRID_DOCUMENT_WRITE_ENABLED=true` de forma estable.

   **Le queda al humano:** decidir si el adjunto de prueba (`cod`
   `202609060933388219.prueba`, reclamación `RS26.08/0123`) se borra desde la
   UI de Sigrid, y dar a Posventa su function key (contrato en
   `azure-apps/sigrid_api.md` §8.8). Para la obra 404: el tipo de un contrato
   es 44; un albarán tendrá el suyo; añadirlo a `SIGRID_DOCUMENT_ALLOWED_CONTIP`.

## Guion de T18-T21 (ya ejecutado el 2026-09-06; se conserva como referencia)

Todas después de desplegar. `$BASE` = `SIGRID_API_BASE_URL`, `$KEY` =
`SIGRID_API_FUNCTION_KEY` (del `.env` de `albaranes/services/albaranes-persistencia`).
Cabeceras siempre: `x-functions-key: $KEY`, `Content-Type: application/json`.

### T18 — desplegar y fijar las App Settings nuevas, cerradas

Las App Settings van por fichero JSON (ASCII, sin BOM), nunca inline: los
corchetes y comillas de las listas se rompen al pasar por PowerShell.
`f004_appsettings.json`:
```json
[{"name": "SIGRID_DOCUMENT_WRITE_ENABLED", "value": "false", "slotSetting": false},
 {"name": "SIGRID_DOCUMENT_WRITE_DATABASE", "value": "ruesma_rep", "slotSetting": false},
 {"name": "SIGRID_DOCUMENT_ALLOWED_CONTIP", "value": "[708]", "slotSetting": false},
 {"name": "SIGRID_DOCUMENT_ALLOWED_GRATIPIDE", "value": "[35]", "slotSetting": false}]
```
```powershell
func azure functionapp publish func-sigridapi-dev-huyke --python
az functionapp config appsettings set -g rg-sigrid-dev-data-api -n func-sigridapi-dev-huyke --settings "@f004_appsettings.json"
az functionapp config appsettings list -g rg-sigrid-dev-data-api -n func-sigridapi-dev-huyke `
  --query "[?starts_with(name,'SIGRID_DOCUMENT') || name=='ALLOWED_WRITE_DATABASES']"
```
**Criterio:** las cuatro con esos valores y `ALLOWED_WRITE_DATABASES` sigue en
`["ruesma"]`. Para la prueba en la **obra 404** hay que medir antes el `tip` del
concepto (albarán/contrato) y añadirlo a `SIGRID_DOCUMENT_ALLOWED_CONTIP`.

### T19 — dry-run contra producción (100 % lectura)

Paso previo, `POST $BASE/api/sql/read` con `database: "ruesma"`, para anotar la
huérfana real de clase 35 (su `con`):
```sql
SELECT n.ide, n.cod, n.res, n.fec, r.con FROM dbo.gra n JOIN dbo.rcg r ON r.gra = n.ide
LEFT JOIN ruesma_rep.dbo.gra d ON d.emp = n.emp AND d.cod = n.cod
WHERE n.gratipide = 35 AND d.ide IS NULL
```
Después, `POST $BASE/api/sigrid/concepto-grafico` **sin `commit`**, contra una
reclamación normal y contra la de la huérfana:
```json
{"database": "ruesma", "conide": <ide reclamación>, "contip": 708, "gratipide": 35,
 "res": "PRUEBA API - BORRAR", "nom": "prueba.pdf", "usu": "<tu login Sigrid>",
 "contenido_base64": "<PDF pequeño en base64>"}
```
Y los negativos, cambiando un campo cada vez: `conide` de una factura →
`tipo_de_concepto_no_coincide`; un PNG en base64 → `tipo_de_fichero_no_permitido`;
`usu` inventado → `usuario_no_valido`.
**Criterio:** `committed:false`, `dry_run:true`, `filas_afectadas:0`, las filas
E4/E5 del preview completas; en la huérfana `idempotente:false` con el aviso; y
después `SELECT MAX(ide) FROM dbo.gra` en `ruesma` y en `ruesma_rep` **sin cambiar**.
Respuestas pegadas en `impl_F-004.md`.

### T20 — primer `commit:true` (autorización expresa, una sola llamada)

Con `SIGRID_DOCUMENT_WRITE_ENABLED=true` y `SIGRID_DOMAIN_WRITE_ENABLED=true`
solo durante esa ventana, la misma petición de T19 con `"commit": true` sobre la
reclamación (u obra 404) elegida. Luego `POST $BASE/api/documents/read`:
```json
{"database": "ruesma_rep", "table": "gra", "id_column": "cod",
 "id_value": "<cod devuelto>", "blob_column": "ima"}
```
**Criterio:** `sha256` del binario descargado idéntico al enviado; en `ruesma`,
`SELECT * FROM dbo.gra WHERE cod = ?` → 1 fila con `ima` NULL, en `ruesma_rep`
→ 1 fila con `DATALENGTH(ima)` = bytes enviados, `SELECT * FROM dbo.rcg WHERE
gra = <ide negocio>` → 1 fila; la 4ª consulta, huérfanos de la prueba,
`SELECT g.ide, g.cod, g.res FROM dbo.gra g LEFT JOIN dbo.rcg r ON r.gra = g.ide
WHERE r.ide IS NULL AND g.res = 'PRUEBA API - BORRAR'` → **ninguna fila**; y **el
gráfico se abre desde la ficha en Sigrid**.

### T21 — idempotencia

Repetir **exactamente** la llamada de T20 con `"commit": true`.
**Criterio:** `idempotente:true`, `filas_afectadas:0`, y
`SELECT COUNT(*) FROM dbo.rcg r JOIN dbo.gra g ON g.ide = r.gra WHERE g.cod = ?`
sigue en 1. Limpieza, si toca, desde la UI de Sigrid.

## Pendiente de decisión del humano

### Del arnés — valen para cualquier proyecto, así que van a `arnes-base`

- **Diagnosticar `harness/mutacion_paralela.py`.** Dos evidencias ya: en F-003,
  un mutante que muere en 1,9 s salió superviviente; en F-004, 5 supervivientes
  no reproducibles sobre el mismo commit. **Pista concreta** del reviewer
  final: `ResultadoSuite.verde` (`harness/mutacion.py` l. 491) da verde para
  `exit 5` de pytest (ningún test recogido) y `ejecutar` (l. 612) lo traduce a
  SUPERVIVIENTE. Propuesta: `SUPERVIVIENTE` con `sin_tests` → `INDETERMINADO`.
  Sesgo pesimista en las dos features, así que los ceros son sólidos.
- **Un test que construye `Settings` real debe aislar el entorno** (la campaña
  exporta el `.env`): lección de F-004 T14c; merece regla en `CONVENTIONS.md`.
- Pendientes de antes: `pytest-timeout` para los cuelgues; «Evidencias» con
  SHA y workers como regla; `init.sh` sin aviso de `mutacion_F-XXX.md` en
  `critico`; RM5 pide reproducir uno; `harness/rutas_sensibles.json` no
  existe en un repo con `infrastructure/security/`; cada trozo de revisión
  debe declarar qué checkpoints deja fuera.

### De configuración y de la base

- **`local.settings.json` está versionado con dos contraseñas reales** desde
  el primer commit (`e903394`, 2026-04-16), en `origin/main` y `origin/dev`.
  Lo que cierra el hueco es **rotarlas** en Sigrid y en el Key Vault; después
  `git rm --cached local.settings.json` y `.gitignore`.
- **`ALLOWED_DATABASES` incluye `master`** y ningún consumidor lo necesita.
- **`user_rw` tiene `UPDATE`** sobre `ruesma_rep.dbo.gra`; no se probó `DELETE`.
- El guard de `ALLOWED_WRITE_DATABASES` vacía **falla abierto** en los cuatro
  casos de uso de dominio (patrón calcado de albaranes); feature propia.
- `scripts/verificar_sql_ecosistema.py` copia a mano las listas blancas.
- 19.196 filas documentales sin dueño ni en `gra` ni en `dog` (~2.000/año):
  Sigrid parece borrar en negocio sin borrar en el repositorio.
- En albaranes, `sigrid_api_contrato_client.py` resuelve por `cod` sin `emp`
  (8 `cod` repetidos entre empresas, hoy inocuo).

## Lo siguiente en el backlog

F-005 espera al **reviewer**. Después, `harness/features.json` solo deja
F-001 (`pending`, calentamiento). Candidatos: el diagnóstico del arnés de
mutación, o lo que pida `postventa-incidencias` F-012, que era quien esperaba
este endpoint.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-005 está implementada en
> `feature/F-005-grafico-sin-clase` (`cfb8048`) y pendiente de **review**
> contra `CHECKPOINTS.md`; su informe es `progress/impl_F-005.md`. F-004 está
> cerrada y solo espera el merge del humano. Si el humano trae el resultado de
> la prueba manual de F-005 en la obra 0404, anótalo en `impl_F-005.md`. No
> arranques nada nuevo sin preguntar.
