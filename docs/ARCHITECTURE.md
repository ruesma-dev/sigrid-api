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
  `sigrid/albaran-directo`, `sigrid/concepto-grafico`,
  `sigrid/partes-reclamacion`, `documents/read`, `diagnostics/tcp`.
  `build_dependencies()` devuelve una tupla de **ocho** posiciones (la 6 es el
  albarán clásico y la 7 el modo extendido, F-009); las rutas que no la usan
  entera la desempaquetan igual.
- **`domain/`** — sin dependencias de infraestructura.
  - `models/`: `sql_models` (lectura/escritura/documentos), `document_models`,
    `sigrid_domain_models` (líneas de contrato), `albaran_domain_models`,
    `albaran_directo_models`, `albaran_compra_models` (modo extendido de
    `sigrid/albaran`, F-009), `concepto_grafico_models` (adjuntar documentos),
    `parte_reclamacion_models` (alta en lote de partes de Posventa).
  - `ports/sql_repository.py`: interfaz `SqlRepository`.
- **`application/use_cases/`** — un caso de uso por capacidad:
  `execute_sql_query_use_case`, `execute_sql_command_use_case`,
  `read_document_use_case`, `add_contract_lines_use_case`,
  `create_purchase_albaran_use_case`, `create_direct_albaran_use_case`,
  `create_albaran_compra_use_case` (modo extendido de `sigrid/albaran`, con su
  constructor puro `albaran_compra_statements`; F-009),
  `create_partes_reclamacion_use_case` (una transacción por parte, con su
  constructor puro de sentencias `parte_reclamacion_statements`).
- **`infrastructure/`** — `repositories/sql_server_repository.py` (adaptador
  pyodbc, elige credencial de lectura o escritura según la operación),
  `security/` (guardias) y `serialization/json_encoder.py`.
- **`interface_adapters/http/http_response_factory.py`** — construcción
  uniforme de respuestas HTTP.
- **`config/settings.py`** — `Settings` (pydantic-settings) leído de `.env` en
  local y de App Settings en Azure.

### Los dos modos de `sigrid/albaran` (F-009)

Una sola ruta y dos modos, elegidos **por las claves** del JSON antes de validar
nada (`elegir_modo_albaran`, función pura del dominio): con `lineas` o
`referencia_externa`, **extendido**; sin ninguna, **clásico**; las dos familias
a la vez (`lineas_recibidas` junto a ellas), 400 `peticion_mixta`.

- **Clásico**: `AddPurchaseAlbaranRequest` + `CreatePurchaseAlbaranUseCase`,
  **intocables** (como `albaran-directo`). Los fija un test de caracterización
  con dorado (`tests/test_f009_caracterizacion.py`), que no se regenera. Él y
  `albaran-directo` quedan obsoletos cuando el pipeline de albaranes (F-053)
  esté en real.
- **Extendido** (alta idempotente de UN albarán con líneas vinculadas y sin
  vincular, con o sin partida, y devoluciones), en tres piezas por capa:
  - *domain*: `albaran_compra_models` — petición (`extra="forbid"`), respuesta
    (superconjunto de la clásica, sin columnas bancarias), avisos y
    `AlbaranCompraError(ValueError)` con `codigo` cerrado y `lineas` de fallos.
  - *application*: `albaran_compra_statements` — SQL **constante** con `?`
    (lecturas L1-L15 y sentencias de transacción E1-E12), autovalidado con
    `DatabaseReferenceGuard`, y funciones puras (código de serie, balance de
    stock y PMP, estados del contrato, importes con `Decimal`, constructores de
    filas). Sin E/S. `create_albaran_compra_use_case` orquesta: guardas sin
    leer la base, lecturas de cabecera y de líneas (acumula **todos** los fallos
    de línea), construcción pura y, con `commit`, un `work` reentrante en
    **una** transacción del repositorio (`run_in_write_transaction`) bajo
    applocks en orden fijo (`SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`,
    `_dcapro`, `_ctrprodes`, `_mov`, `_log`): idempotencia re-comprobada dentro,
    `cod` e `ide` reservados con `UPDLOCK, HOLDLOCK`, relecturas antes del
    COMMIT. La colisión de clave agotada sale del caso de uso como
    `AlbaranCompraError(colision_de_clave)`: la ruta no captura `IntegrityError`.
  - *infrastructure*: nada nuevo; reutiliza los métodos del repositorio.
- **Ruta**: la guarda `SIGRID_ALBARAN_WRITE_ENABLED` (R8) va en `sigrid/albaran`
  (los dos modos) y en `sigrid/albaran-directo`, **después** de validar el modelo
  y **antes** del caso de uso, solo con `commit`. `AlbaranCompraError` → 400
  `details:{type, codigo[, lineas]}`; los `except` previos no cambian.
- **Trazas** (R32): una por petición extendida, la emite el **caso de uso** al
  terminar (obra, contrato, referencia, `commit`, `estado`, `cod`, nº de líneas,
  códigos y duración; nunca textos, precios ni datos bancarios). Lo que la ruta
  corta antes del caso de uso (`peticion_mixta`, Pydantic, R8) deja solo su
  `warning` de ruta, sin esa traza.

## Semántica de dominio imprescindible

Reglas que **no** se deducen del código y que causan bugs si se ignoran:

1. **Dos bases con propósitos distintos, no una y su réplica.** `ruesma` es la
   base de **negocio** (todo dato y casi toda escritura). `ruesma_rep` es la
   base **documental** (BLOBs: PDFs y ofimática adjuntos a los conceptos): se
   lee por `documents/read` y se escribe **solo** por
   `sigrid/concepto-grafico`, nunca por `sql/write`. Las dos filas de un mismo
   documento se relacionan por **`(emp, cod)`**, nunca por `ide`: los `ide` de
   las dos `gra` divergen desde 2009 y el join por `ide` devuelve documentos
   ajenos el 99,85 % de las veces [MEDIDO].
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
  en la petición (por defecto **dry-run**). Albaranes, partes y documentos
  tienen además su segunda llave propia (`SIGRID_ALBARAN_WRITE_ENABLED`,
  `SIGRID_RECLAMACION_WRITE_ENABLED`, `SIGRID_DOCUMENT_WRITE_ENABLED`).
- **PROHIBIDO desde local**: escribir sin autorización expresa del humano para
  esa acción concreta; `DELETE` contra Sigrid en cualquier caso; escribir en
  `ruesma_rep` por cualquier vía que no sea `sigrid/concepto-grafico` (y ese,
  con `commit:true` solo con autorización expresa); y tocar `.env` o cualquier
  secreto.
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
