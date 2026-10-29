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
  `sigrid/partes-reclamacion`, `sigrid/proforma` (F-007; a origen, F-016), `documents/read`,
  `diagnostics/tcp`.
  `build_dependencies()` devuelve una tupla de **ocho** posiciones (la 6 es el
  albarán clásico y la 7 el modo extendido, F-009); las rutas que no la usan
  entera la desempaquetan igual.
- **`domain/`** — sin dependencias de infraestructura.
  - `models/`: `sql_models` (lectura/escritura/documentos), `document_models`,
    `sigrid_domain_models` (líneas de contrato), `albaran_domain_models`,
    `albaran_directo_models`, `albaran_compra_models` (modo extendido de
    `sigrid/albaran`, F-009), `concepto_grafico_models` (adjuntar documentos),
    `parte_reclamacion_models` (alta en lote de partes de Posventa),
    `proforma_models` (proforma de mes, F-007), `proforma_origen_models`
    (códigos y respuesta de la proforma a origen, F-016).
  - `ports/sql_repository.py`: interfaz `SqlRepository`.
- **`application/use_cases/`** — un caso de uso por capacidad:
  `execute_sql_query_use_case`, `execute_sql_command_use_case`,
  `read_document_use_case`, `add_contract_lines_use_case`,
  `create_purchase_albaran_use_case`, `create_direct_albaran_use_case`,
  `create_albaran_compra_use_case` (modo extendido de `sigrid/albaran`, con su
  constructor puro `albaran_compra_statements`; F-009),
  `create_partes_reclamacion_use_case` (una transacción por parte, con su
  constructor puro de sentencias `parte_reclamacion_statements`),
  `create_proforma_use_case` (subclase del modo extendido, con su constructor
  puro `proforma_statements`; F-007; y `proforma_origen_statements` para el
  modo a origen, F-016).
- **`infrastructure/`** — `repositories/sql_server_repository.py` (adaptador
  pyodbc, elige credencial de lectura o escritura según la operación),
  `security/` (guardias) y `serialization/json_encoder.py`.
- **`interface_adapters/http/http_response_factory.py`** — construcción
  uniforme de respuestas HTTP. El 400 de Pydantic de las 10 rutas lo construye
  `validation_error_response(exc)` (F-012): `details = {type, validation}`, con
  `exc.errors()` pasado por `json.dumps(..., default=str)`, de modo que lo no
  serializable (la excepción de una regla con mensaje propio, en `ctx.error`)
  sale como texto en vez de un 500 y lo demás sale idéntico. No traza: la traza
  de cada `except ValidationError` sigue en su ruta.
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
    (lecturas L1-L17 y sentencias de transacción E1-E12), autovalidado con
    `DatabaseReferenceGuard`, y funciones puras (código de serie, balance de
    stock y PMP, estados del contrato, importes con `Decimal`, constructores de
    filas). Sin E/S. `create_albaran_compra_use_case` orquesta: guardas sin
    leer la base, lecturas de cabecera y de líneas (acumula **todos** los fallos
    de línea), construcción pura y, con `commit`, un `work` reentrante en
    **una** transacción del repositorio (`run_in_write_transaction`) bajo
    applocks en orden fijo (`SIGRID_REFEXT_14`, `SIGRID_SERIE_14`, `SIGRID_IDE_con`,
    `_dcapro`, `_ctrprodes`, `_mov`, `_dcarec`, `_log`): idempotencia re-comprobada dentro,
    `cod` e `ide` reservados con `UPDLOCK, HOLDLOCK`, relecturas antes del
    COMMIT. La colisión de clave agotada sale del caso de uso como
    `AlbaranCompraError(colision_de_clave)`: la ruta no captura `IntegrityError`.
  - **Cabecera por lista blanca (F-015 O1)**: `con` y `dca` no se clonan de
    ninguna fila. `con` lleva exactamente `CON_COLUMNAS` (F-006) y `dca` las 145
    de `DCA_COLUMNAS`, cada una con UN origen (`ORIGEN_DCA`): identidad (del
    contrato; sin él, del respaldo por CIF o del `prv` único del CIF, L17),
    cascada contrato → respaldo → `prv` (pago y banco en bloque; sin fuente, vacía
    y aviso `cabecera_sin_dato`), calculadas (petición, obra, totales) y fijas (lo
    que deja el alta a mano). El **respaldo** es el último albarán `AC` de clase 0
    del proveedor que no es proforma (L5), y es opcional. Solo `dcapro` se sigue
    clonando de su plantilla de línea.
  - **Retención del contrato (F-015 O2)**: con contrato, L16 lee sus `ctrrec`;
    uno soportado (clases 3, 4, 5, sin `valfij` ni `ivaide`) da UNA `dcarec`
    (`bas` sobre `totbas` o `totdoc`, `cuo` en `Decimal` `ROUND_HALF_UP`) y
    `dca.tot` = `totpag` = `totdoc` − `cuo`; más de uno o uno raro, 400
    `retencion_no_soportada`. En el commit, su `ide` (E6b) va bajo el applock
    `SIGRID_IDE_dcarec`, el `INSERT` tras los `mov` y su relectura en E12.
  - **Descuento por línea (F-018)**: `LineaAlbaranIn.dto` opcional (0-100, como
    mucho 2 decimales; 0 o ausente = sin descuento, `con_dto`). Con `dto`
    pedido, `precio` es el bruto: `dcapro.tar` = bruto, `dcapro.dto` = texto de
    Sigrid (`40%`, `1,5%`), `tot` = `redondear_euros(can·tar·(1 − dto/100))`,
    `pre` = `tot`/`can` (neto, el de `mov` y del PMP) e `ivacuo` sobre `tot`;
    `dca.impbru` suma los brutos (sin ninguna línea con descuento, = `totbas`
    como antes). Una vinculada **sin** `dto` que casa por la opción C con un
    `ctrpro` de dto legible > 0 y `tar` ≠ 0 copia `tar`/`dto` como antes y
    calcula `tot`/`pre`/`ivacuo` como Sigrid (R15). Con `dto` pedido, la
    vinculada escribe lo pedido y avisa de cada diferencia con el `ctrpro`
    (bruto frente a `tar`: `precio_distinto_del_contrato`; porcentaje:
    `dto_distinto_del_contrato`). La línea de respuesta lleva `dto` y
    `precio_bruto` solo con descuento (un serializador omite las dos claves
    cuando valen `None`); la traza, `n_lineas_con_dto` si hay alguna. Sin SQL
    nuevo. El clásico y `albaran-directo` **ignoran** `dto`: sus líneas
    (`ReceivedLine`, `DirectLine`) no llevan `extra="forbid"`, así que la clave
    se descarta en silencio. Riesgo: quien mande el bruto con `dto` a esas rutas
    graba la línea sin descuento y sin error; solo el modo extendido lo aplica
    (y `sigrid/proforma` lo rechaza con 400).
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

### `sigrid/proforma` (F-007): el núcleo del modo extendido con otro perfil

Alta idempotente de UNA proforma de mes de un subcontratista como albarán de compra
(`con.tip` 14) de la serie `PROF<aa>/` (5 cifras) con `dca.cla` 141. No hay núcleo
nuevo: `CreateProformaUseCase` **hereda** de `CreateAlbaranCompraUseCase` y cambia
solo lo que pasan cinco costuras, que en el albarán valen lo de antes (R31; su
dorado y sus tests no se tocan):

1. **`PerfilAlta`** (`PERFIL_ALBARAN` / `PERFIL_PROFORMA`): endpoint de la traza,
   prefijo y cifras de la serie, `cla`, la llave y su código, los nombres de las
   App Settings (prefijos, tope de líneas, productos y naturalezas) y la clase del
   error (`AlbaranCompraError` / `ProformaError`).
2. **Serie**: `prefijo_de_serie` y `sellos_del_alta` reciben el prefijo; las
   constantes SQL no cambian.
3. **`_comprobar_dentro`**: gancho tras E1 bajo `SIGRID_REFEXT_14`, vacío en el
   albarán; en la proforma repite LP1 por el cursor (R28) y, si alguien registró la
   del mes entre la previa y el commit, responde `existente` (o
   `proforma_del_mes_existente`) sin escribir.
4. **Catálogo**: con `productos_del_contrato`, una línea sin vincular admite además
   los productos de las líneas del contrato (R17).
5. **Códigos de clase**: `FalloLinea`, `AlbaranCompraError` y `AvisoAlbaran` validan
   contra su `codigos`; las subclases de proforma los amplían.

Lo propio de la proforma, por capa:

- *domain*: `proforma_models` — `ProformaRequest` (`periodo` entero `AAAAMM`,
  números estrictos, `extra="forbid"`), `LineaProformaIn` (`ctrpro_ide` o
  `producto`, nunca juntos), `ProformaResponse` (la del modo extendido más
  `existente`, `contrato` y `origen`), `ProformaError` (con `reparto` solo en
  `hoja_de_varios_contratos`) y `FalloLineaProforma` (con `candidatos`).
- *application*: `proforma_statements` — LP1-LP6, SQL constante con `?` validado con
  `DatabaseReferenceGuard` (solo `SELECT`), y funciones puras: resolver el contrato
  (R7-R9: por petición, por proveedor —el CIF manda sobre el nombre— o por las
  líneas), identificar las líneas (R14), la fecha del periodo, cuadrar la hoja
  (R19), anterior y origen sobre las proformas del contrato (R20-R22), buscar la del
  mes (R24) y traducir la petición a un `AlbaranCompraRequest` del núcleo.
  `create_proforma_use_case` orquesta: obra, referencia (R23), contrato, líneas,
  existente o idempotente, y el resto por el flujo del núcleo; el contexto de R28
  viaja en un `PrivateAttr` de una subclase interna de la petición del núcleo.
- **Descuento (F-018)**: la petición de proforma **no** admite `dto` (400 sin
  `codigo`), pero sus vinculadas se construyen con el núcleo, así que una línea
  contra un `ctrpro` con dto legible hereda R15 (de mes y a origen, sin
  interruptor ni cambio en `create_proforma_use_case`): `tot`/`pre` de Sigrid,
  `dca.impbru` bruto, `dto` y `precio_bruto` en la línea de respuesta, y a origen
  `importe_origen_cadena` con ese `pre`.
- *infrastructure*: nada nuevo.
- **Ruta**: la llave `SIGRID_PROFORMA_WRITE_ENABLED` (R5) solo con `commit`,
  después de validar y antes del caso de uso; la de albaranes no la abre.
  `ProformaError` → 400 `details:{type, codigo[, lineas][, reparto]}`. Una traza por
  petición (R33) sin textos, nombres, CIF ni importes.

### `sigrid/proforma` a origen (F-016): un modo de la misma ruta, sin tocar el núcleo

Con `modo: "origen"` la proforma se registra a origen (`dca.docoritip` 1, `docoriide`
= la anterior; por línea `canorilin` y `canoriori` acumulado). Sin `modo`, F-007
exacta: cada rama nueva es inerte en mes y la respuesta no trae claves nuevas (R1).
La API **registra y valida**; elegir el modo, la anterior y qué línea continúa cada
una es del llamante (`proformas`), que lee Sigrid por `sql/read`
(`contrato_proformas.md` v1.2 §2.3). No toca el núcleo de F-009 ni `proforma_statements`:

- *domain*: `ProformaRequest` y `LineaProformaIn` ganan `modo`,
  `proforma_anterior`, `primera_de_cadena` y `linea_anterior` (combinaciones de R3
  → 400 sin `codigo`). `proforma_origen_models` amplía por **subclases** los códigos,
  el error, el fallo de línea, el aviso y la respuesta (`cadena`, campos de línea);
  los conjuntos y clases de F-007 no cambian.
- *application*: `proforma_origen_statements` — LP7 (la anterior por `cod` en el
  contrato), LP8 (sus sucesoras), LP9 (sus `dcapro`, `SELECT *` como plantilla),
  constantes con `?` validadas con `DatabaseReferenceGuard`, y funciones puras
  (validar la anterior y las continuaciones, aviso de R10, superponer las columnas a
  origen, construir las **arrastradas**, cabecera a origen, la del mes a origen e
  importe de cadena). `create_proforma_use_case` ramifica por `modo`: valida fuera
  (LP7-LP9), en `_construir` superpone la cadena y añade las arrastradas **al final**
  de `filas.dcapro` (así numeración, previa, `INSERT` y relectura E12 las cuentan sin
  cambiar el núcleo; no generan `ctrprodes`, `mov` ni `UPDATE`), en
  `_comprobar_dentro` relee LP8 por el cursor bajo el applock (R17) y en `_convertir`
  devuelve `ProformaOrigenResponse`.
- **Ruta**: tercera llave `SIGRID_PROFORMA_ORIGEN_ENABLED` (defecto `false`) solo con
  `commit` y `modo: "origen"`, después de la de F-007 y antes del caso de uso. La
  traza añade `modo`, `primera_de_cadena`, la anterior y los nº de continuadas y
  arrastradas.

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
9. **El facturado se prorratea sobre `tot`**: `SUM(canfac / NULLIF(can,0) * tot)`.
   `dcapro.pre` ya es el precio **neto** (`tot`/`can` sin redondear: el
   descuento de línea está dentro; el bruto es `tar` y el porcentaje, el texto
   `dto`), así que `canfac * pre` no ignora el descuento; prorratear sobre `tot`
   sigue siendo la regla porque es exacta al céntimo (corregido en F-018).
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
  la usan. `documents/read` valida su `database` contra la misma
  `ALLOWED_DATABASES` (F-011), en el caso de uso y por igualdad exacta, antes
  de los identificadores y de conectar: fuera de ella, 400
  `BaseNoPermitidaError` (hereda de `ValueError`, pero su `details.type` nunca
  es `"ValueError"`, que para mcp-bbdd significa «sin binario»).
- **Toda base pasa por `IdentifierGuard` antes de conectar** (F-011, D2 = A1):
  `SqlServerRepository._connect` la valida con
  `IdentifierGuard.validate_identifier(database, field_name="database")` y
  compone `DATABASE=` con el valor validado, porque la cadena ODBC no la escapa.
  Es la defensa en profundidad de toda la API, no la lista blanca: cierra el
  dry-run de `contrato-lineas`, `albaran` (los dos modos) y `albaran-directo`,
  que conectan con la base de la petición sin mirar `ALLOWED_WRITE_DATABASES`
  (solo con `commit`), y el caso de una lista blanca mal configurada. Fuera del
  patrón, 400 `IdentifierValidationError` sin conectar.
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
