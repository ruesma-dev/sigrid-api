<!-- docs/ARCHITECTURE.md -->
# Arquitectura · sigrid-api

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
>
> La documentación **exhaustiva** del microservicio (endpoints campo a campo,
> infraestructura Azure, diagnóstico, consumidores) vive en el repositorio
> `azure-apps`, fichero `sigrid_api.md`. Este documento es el resumen
> normativo para trabajar dentro del repo; ante duda de detalle, manda aquél,
> y si cambias lo que la API expone o consume hay que actualizarlo en el
> mismo trabajo.

## Qué hace este proyecto

`sigrid-api` es un microservicio (Azure Function App, Python 3.12) que expone
de forma acotada y auditable el SQL Server on-premise del ERP **Sigrid** al
resto de sistemas de Construcciones Ruesma. **Es el único punto de acceso a
esa base de datos**: nadie —ni el datamart, ni el pipeline de albaranes, ni
Power BI, ni los scripts de consulta— se conecta por SQL directo. Ofrece
cuatro capacidades: lectura SQL acotada, descarga de documentos binarios,
escritura SQL genérica transaccional y escritura de dominio de alto nivel
sobre objetos de Sigrid.

## Capas y estructura

Hexagonal, con las dependencias apuntando siempre al dominio.

- **`function_app.py`** — único adaptador de entrada. Declara las rutas HTTP y
  compone las dependencias una sola vez (`build_dependencies()` + `lru_cache`).
  Rutas: `sql/read`, `sql/write`, `sigrid/contrato-lineas`, `sigrid/albaran`,
  `sigrid/albaran-directo`, `documents/read`, `diagnostics/tcp`.
- **`domain/`** — sin dependencias de infraestructura.
  - `models/`: `sql_models` (lectura/escritura/documentos), `document_models`,
    `sigrid_domain_models` (líneas de contrato), `albaran_domain_models`,
    `albaran_directo_models`.
  - `ports/sql_repository.py`: interfaz `SqlRepository`.
- **`application/use_cases/`** — un caso de uso por capacidad:
  `execute_sql_query_use_case`, `execute_sql_command_use_case`,
  `read_document_use_case`, `add_contract_lines_use_case`,
  `create_purchase_albaran_use_case`, `create_direct_albaran_use_case`.
- **`infrastructure/`** — `repositories/sql_server_repository.py` (adaptador
  pyodbc, elige credencial de lectura o escritura según la operación),
  `security/` (guardias) y `serialization/json_encoder.py`.
- **`interface_adapters/http/http_response_factory.py`** — construcción
  uniforme de respuestas HTTP.
- **`config/settings.py`** — `Settings` (pydantic-settings) leído de `.env` en
  local y de App Settings en Azure.

## Semántica de dominio imprescindible

Reglas que **no** se deducen del código y que causan bugs si se ignoran:

1. **Dos bases con propósitos distintos, no una y su réplica.** `ruesma` es la
   base de **negocio** (todo dato y toda escritura). `ruesma_rep` es la base
   **documental** (BLOBs: PDFs y ofimática adjuntos a los conceptos) y hoy
   solo se **lee**, vía `documents/read`.
2. **Casi todo en Sigrid es un Concepto (`con`)** con extensión 1:1 por tipo
   (`obr`, `ctr`, `dca`, `dcf`, `prv`…) que comparte el mismo `ide`. El
   discriminador es `con.tip`; el nombre legible es `con.res`. Para obtener
   código y descripción de casi cualquier objeto hay que hacer
   `JOIN dbo.con ON con.ide = X.ide`: la extensión sola no los tiene.
3. **`cod`, `res` y `fec` viven en `con`, NUNCA en la extensión.** Insertarlos
   en la extensión da `42S22 "El nombre de columna 'cod' no es válido"`.
4. **Las fechas son enteros `YYYYMMDD`**, y `0` significa nulo.
5. **`ide` no es IDENTITY y no hay SEQUENCE activa.** Se asigna por
   `MAX(ide)+1`, lo que es una condición de carrera: los endpoints de dominio
   lo resuelven con `sp_getapplock` + reintento. Quien escriba con `sql/write`
   se queda sin esa protección.
6. **Sigrid no tiene triggers: nada se recalcula solo.** Totales de cabecera,
   `canser`, estados `estser/estfac`, stock y PMP en el ledger `mov` los
   mantiene la API en los endpoints de dominio. Un INSERT a mano deja el ERP
   a medias.
7. **`con.est` es un entero cuyo significado depende del tipo y es
   configurable por instalación.** Nunca hardcodear un estado: resolverlo
   contra `dbo.conest` por `con.tip = conest.tip AND con.est = conest.est`.
8. **`dca` es albarán y `dcf` es factura.** Confundir `dcapro` con líneas
   facturadas es el error más frecuente.
9. **El facturado no es `canfac * pre`**: eso ignora el descuento de línea.
   Se prorratea sobre el neto: `SUM(canfac / NULLIF(can,0) * tot)`.
10. **Comparativo → contrato tiene doble vía** (`ctr.comide` y
    `comlin.ctride`): hay que deduplicar antes de sumar importes.

## Acceso a datos y sistemas externos

- **Único sistema externo: SQL Server on-premise de Sigrid** (PRODUCCIÓN, sin
  entorno de pruebas), alcanzado por red privada desde la Function App.
- **Límites duros**: `MAX_ALLOWED_ROWS` (1.000 filas por petición),
  `MAX_QUERY_TIMEOUT_SECONDS` (120 s) y un corte del balanceador a 230 s.
  Toda agregación se hace en SQL, nunca trayéndose filas para sumarlas fuera.
- **SQL siempre parametrizado** con `?` y valores en `parameters`.
- **Las listas blancas de bases se aplican dos veces**: al campo `database` de
  la petición (la base de la conexión) y a **las bases que el SQL nombra
  dentro**, con `DatabaseReferenceGuard`. Sin lo segundo, una sentencia puede
  saltar a otra base de la misma instancia cualificando el nombre
  (`otra_base.dbo.tabla`) y la lista blanca no aplica nada. Los nombres de
  cuatro partes (servidor vinculado) se rechazan siempre. La lectura cruzada
  entre las bases de `ALLOWED_DATABASES` sigue permitida: hay diagnósticos que
  la usan.
- **Escritura apagada por defecto**, y encendida por capas independientes:
  credenciales `user_rw`, `ALLOWED_WRITE_PREFIXES`, `ALLOWED_WRITE_DATABASES`
  y, para dominio, `SIGRID_DOMAIN_WRITE_ENABLED` más `commit:true` explícito
  en la petición (por defecto **dry-run**).
- **PROHIBIDO desde local**: escribir sin autorización expresa del humano para
  esa acción concreta; `DELETE` contra Sigrid en cualquier caso; escribir en
  `ruesma_rep`; y tocar `.env` o cualquier secreto.
- Los **tests no tocan red ni base de datos**: el puerto `SqlRepository` se
  dobla.

## Infra y despliegue

- Azure Function App (Flex Consumption, Python 3.12) + Storage Account + Key
  Vault para secretos + subnet dedicada para la integración de red hacia
  on-premise. Detalle y comandos en
  `docs/DEPLOYMENT_TERRAFORM_AND_CODE.md` y en `azure-apps/sigrid_api.md`.
- **Autenticación**: `x-functions-key` en cabecera; sin ella, 401.
- **Secretos**: solo en Key Vault / App Settings. Ni contraseñas, ni cadenas
  de conexión, ni claves, ni IDs de suscripción o tenant, ni IPs internas
  entran en el repositorio. `.env` nunca viaja ni se versiona.
