<!-- progress/current.md -->
# Trabajo en curso

## F-006 · spec escrita el 2026-09-24, pendiente de aprobación del humano

El spec-author dejó `specs/F-006-alta-parte-reclamacion/` (requirements 150/150, design
167/250, tasks 19 tareas) y la medición en producción, solo lecturas, en
[`explore_F-006_modelo_parte.md`](explore_F-006_modelo_parte.md). Lo medido: un parte nuevo
son `con` + `rcp` + `rcpint` (pos 0) + fila de alta en `dbo.log`, nace en `est` 1 `SAT`
(`sercon.estini`), la serie `RS<aa>.<mm>/` se reinicia cada mes con 4 dígitos, no hay tabla
de contadores (`serconcod` vacía) y el índice único `(emp, tip, cod)` detecta la colisión con
la UI. La referencia externa del importador es `conext.cod='RCPCLI'`.

**Decisiones abiertas que tiene que validar el humano antes de implementar** (detalle al
principio de `requirements.md`):

- **Q1** — Referencia externa en `RCPCLI` **con prefijo obligatorio del llamante** (el campo
  ya lo usan el promotor y notas a mano), o alternativa `con.doc`.
- **Q2** — `rcp.rcptip` (forma de comunicación): 0 por defecto, informable `{0, 1}`.
- **Q3** — Escribir la fila de alta en `dbo.log` como el escritorio (el portal no la escribe).
- **Q4** — Qué UPV real se usa para el `commit:true` de prueba (la obra 0404 no tiene UPV).
- Además, para que conste: una obra por lote; `rcp.pos` puede repetirse ante una alta
  simultánea de la UI (sin índice único, inocuo); el `HOLDLOCK` sobre `log` retiene un instante
  las altas de log de otros usuarios.

## F-006 · Alta de partes de reclamación en lote (EN SPEC, 2026-09-24)

Rama `feature/F-006-alta-parte-reclamacion` (desde `dev` `210fac1`). Alta en
el backlog, F-007 (proformas) y F-008 (facturas de compra) anotadas, y
referencias en `docs/referencia/` (Word de Posventa y manual de Sigrid, con
markitdown): commit `ad5d500`.

**Decisiones del humano (2026-09-24)**, recogidas en `features.json`: lote con
tope y **una transacción por parte**, respuesta parte a parte; idempotencia por
**referencia externa** que aporta quien llama; tipo de reclamación **`0002` por
defecto e informable**; el manual se incorpora entero pese a su cláusula de
copyright; F-008 es de **compra**. La referencia principal es el Word
(`postventa_pasos_crear_parte.md`); sus capturas llevan nombres de
propietarios y no se transcriben.

**Estado (2026-09-24): `in_progress`, spec aprobada por el humano («sí») con Q1-Q4 aplicadas (`35c3c42`); implementer lanzado.** Spec en `a805f4a`; faltan sus respuestas a Q1-Q4 de `requirements.md`. El spec-author midió en producción, solo con lecturas, el
modelo de filas de un parte (`RS26.08/0169`, obra 0677, como modelo) →
`progress/explore_F-006_modelo_parte.md` y la spec en
`specs/F-006-alta-parte-reclamacion/`. Al terminar: F-006 a `spec_ready` y
**PARAR** para la aprobación del humano.

**Respuestas del humano a Q1-Q4 (2026-09-24), spec APROBADA con ellas:**
- **Q1:** referencia externa en `conext` `RCPCLI` con prefijo obligatorio
  **`PVI-`** (`SIGRID_RECLAMACION_PREFIJOS_REFERENCIA=["PVI-"]`). Medido antes
  de decidir: en 2026, 0 de 1.656 partes manuales, 10 de 929 del importador y
  1 de 312 del portal usan `RCPCLI`; el proceso del Word no lo toca.
- **Q2:** `forma_comunicacion` por defecto **1 «Escrita»**, informable.
- **Q3:** se escribe la fila de alta en `dbo.log` con el `usu` de la petición.
- **Q4:** prueba en la obra **0626** (`con.ide` 1758465, estado 25 CER), UPV
  **`0626.03PORTAL 1.1.A`**: 132 UPV en PRE, ninguna con propietario ni
  persona (nadie lo ve en el portal), 25 `obrofc` todos con proveedor, 5
  partes RS ya cerrados. La prueba no ejercita la copia de propietario.

**Spec ajustada a Q1-Q4 (spec-author, 2026-09-24):** `requirements.md`
cambia «Preguntas abiertas» por «Decisiones del humano», R1 y el modelo pasan
`forma_comunicacion` a defecto 1, se quita la redacción condicional de Q3, y
R22/T15-T18 usan `PVI-`, `PVI-PRUEBA-0001`, obra `0626` y UPV
`0626.03PORTAL 1.1.A`. T2 queda hecha. Oficio de la prueba elegido con una
lectura por `sql/read`: `0039` con proveedor `1181` (único `obrofc` de ese
oficio en la obra; el `0070` tiene dos proveedores y se evitó). Nada más del
diseño cambia; tamaño 140/150 y 167/250. **Sin decisiones abiertas.**

> Todo lo que sigue es de F-004/F-005, ya cerradas y verificadas.

> **F-005 cerrada el 2026-09-06 con veredicto APROBADO** (código y
> papeleo) e `init.sh` en verde: 1.502 tests, cobertura 100 % de las 7 líneas
> cambiadas, mutación 6/6. Informes: [`impl_F-005.md`](impl_F-005.md),
> [`review_F-005.md`](review_F-005.md),
> [`review_F-005_papeleo.md`](review_F-005_papeleo.md). No hay ninguna
> feature `in_progress`.
>
> `sigrid/concepto-grafico` admite `gratipide = 0` («sin clase»), que es como
> Sigrid adjunta en contratos (`con.tip` 44) y albaranes de compra (`tip` 14),
> **solo si el `0` se pone explícitamente en
> `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`**. Mergeada (`0d8b206`), desplegada y
> **verificada en producción el 2026-09-06** con un `commit:true` autorizado
> sobre el albarán `AC26/15951` de la obra 0404
> ([`verificacion_F-005_obra0404.md`](verificacion_F-005_obra0404.md)). Las
> App Settings quedan en `[708,44,14]` y `[35,0]`: el endpoint acepta ya
> reclamaciones, contratos y albaranes de compra.
>
> **F-004 quedó cerrada el 2026-09-06 con veredicto APROBADO.** Lo suyo, y el
> merge pendiente, sigue documentado abajo.

## Lo que espera al humano, por orden

1. **F-004 mergeada en `dev` (`70ac430`) y empujada**, `main` al día. Queda
   el merge de **F-005** cuando el reviewer apruebe. `azure-apps` acumula
   cinco commits locales (`a40684f`, `157b392`, `e0a7667`, `5e9a7bc`…) y
   **no tiene remoto**; hay además un `.env` sin trackear ajeno a estas
   sesiones que no debe commitearse.
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

## Guion de la verificación de F-005 en la obra 0404 (ejecutado el 2026-09-06; referencia)

Criterio 8 de F-005. Solo tras mergear y **desplegar** la rama. `$BASE` y
`$KEY` como en el guion de F-004; cabeceras `x-functions-key` y
`Content-Type: application/json`. Conceptos de la obra 0404 («CUBIERTA NAVE
14 - JOHN DEERE», `con.ide` 828942) ya localizados:

| Concepto | `conide` | `contip` | Gráficos hoy |
|---|---|---|---|
| Contrato `CTSB20/0519` (PROTECCIONES MADRILEÑAS) | 1686634 | 44 | 2, ambos sin clase |
| Albarán de compra `AC26/15951` (GARSAN, ALB-PRUEBA-001) | 2774375 | 14 | 0 → **1 tras M3** |

### M1 — ampliar las App Settings (siguen con la escritura abierta)

`f005_appsettings.json` (ASCII sin BOM):
```json
[{"name": "SIGRID_DOCUMENT_ALLOWED_CONTIP", "value": "[708,44,14]", "slotSetting": false},
 {"name": "SIGRID_DOCUMENT_ALLOWED_GRATIPIDE", "value": "[35,0]", "slotSetting": false}]
```
```powershell
az functionapp config appsettings set -g rg-sigrid-dev-data-api -n func-sigridapi-dev-huyke --settings "@f005_appsettings.json"
az functionapp config appsettings list -g rg-sigrid-dev-data-api -n func-sigridapi-dev-huyke --query "[?starts_with(name,'SIGRID_DOCUMENT_ALLOWED')]"
```

### M2 — dry-run (100 % lectura) sobre el contrato y el albarán

`POST $BASE/api/sigrid/concepto-grafico`, **sin `commit`**, una vez por concepto:
```json
{"database": "ruesma", "conide": 1686634, "contip": 44, "gratipide": 0,
 "res": "PRUEBA API - BORRAR", "nom": "prueba_f005.pdf", "usu": "prueba",
 "contenido_base64": "<PDF pequeño en base64>"}
```
y lo mismo con `"conide": 2774375, "contip": 14`. Negativo: la misma petición
con `"gratipide": 40` debe seguir exigiendo `auxgra` (clase 40 existe → acepta),
y con `"gratipide": 99` → `clase_de_grafico_no_permitida`.
**Criterio:** `committed:false`, `filas_afectadas:0`; en el preview la fila de
negocio lleva `gratipide 0` y la documental `gratipide 0` y `res ''`; `enlace.pos`
192 en el contrato (ya tiene 64 y 128) y 64 en el albarán; **sin** aviso de
`tipaso`; y `SELECT MAX(ide) FROM dbo.gra` en las dos bases sin cambiar.

### M3 — primer `commit:true` (autorización expresa, una llamada)

La petición de M2 del concepto elegido con `"commit": true`. Después:
```json
{"database": "ruesma_rep", "table": "gra", "id_column": "cod",
 "id_value": "<cod devuelto>", "blob_column": "ima"}
```
y por `sql/read` en `ruesma`:
```sql
SELECT ide, cod, emp, res, gratipide, vin, DATALENGTH(ima) FROM dbo.gra WHERE cod = ?
SELECT r.ide, r.con, r.gra, r.pos, r.cla FROM dbo.rcg r JOIN dbo.gra g ON g.ide = r.gra WHERE g.cod = ?
SELECT g.ide, g.cod FROM dbo.gra g LEFT JOIN dbo.rcg r ON r.gra = g.ide WHERE r.ide IS NULL AND g.res = 'PRUEBA API - BORRAR'
```
y la primera también en `ruesma_rep`. **Criterio:** `sha256` idéntico; negocio
`gratipide 0`, `ima` NULL; documental `gratipide 0`, `res ''`, `DATALENGTH` =
bytes; enlace 1 fila; huérfanos ninguna; **el documento se ve en la ficha del
contrato o del albarán en Sigrid** con la misma pinta que los que Sigrid crea
(sin clase). Repetir la llamada → `idempotente:true`, `filas_afectadas:0`.

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
