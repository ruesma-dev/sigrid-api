<!-- specs/F-004-endpoint-concepto-grafico/requirements.md -->
# F-004 · Requisitos

**`POST /api/sigrid/concepto-grafico`: adjuntar un documento a un concepto de
Sigrid escribiendo el binario en la base documental, en una sola transacción.**

## Contexto

Fuente: `docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md` sobre lo **medido** en
`progress/explore_ruesma_rep.md`: `ruesma_rep` es `READ_WRITE`, misma instancia que `ruesma`,
una sola tabla `dbo.gra` (29 columnas, `ima` tipo `image`, índice ÚNICO `(emp, cod)`);
`user_rw` ya tiene `SELECT`/`INSERT`; motor SQL Server 2012. Adjuntar son tres filas: binario
en `ruesma_rep.dbo.gra`, metadatos en `ruesma.dbo.gra` con el **mismo `cod`** y enlace en
`ruesma.dbo.rcg`. F-003 cerró la documental a `sql/write`; esto abre **solo** esta puerta.
Rigor `critico`: producción sin entorno de pruebas.

## Contrato y configuración (propuesta §6, §12.1)

**R1.** CUANDO llegue `POST /api/sigrid/concepto-grafico` con `x-functions-key` y JSON
con `database`, `conide`, `contip`, `gratipide`, `res` (≤48), `nom` (≤255), `usu` (≤24),
`contenido_base64`, y opcionales `sha256` y `commit` (defecto `false`), el sistema debe
validarlo con Pydantic y responder 400 `Solicitud invalida.` ante campo ausente, longitud
excedida o base64 mal formado. El cliente NO envía base documental, tabla, columna,
`ide`, `cod` ni `vin`.

**R2.** El sistema debe responder con la misma forma en dry-run y en commit (`ok`, `committed`,
`dry_run`, `idempotente`, `database`, `database_documental`, `concepto`, `grafico`, `enlace`,
`filas_afectadas`, `avisos`; campos en `design.md`), con `grafico.sha256` y `grafico.bytes` siempre.

**R3.** SI falla una validación de negocio, ENTONCES el sistema debe responder 400
`{ok:false, error:<mensaje>, details:{type, codigo}}` con `codigo` en:
`escritura_documental_deshabilitada`, `base_de_datos_no_permitida`,
`concepto_no_encontrado`, `tipo_de_concepto_no_coincide`, `clase_de_grafico_no_permitida`,
`usuario_no_valido`, `fichero_vacio`, `tipo_de_fichero_no_permitido`, `tamano_excedido`,
`sha256_no_coincide`, `colision_de_clave`, `filas_afectadas_inesperadas`. Lo inesperado
sigue en 500 con `details.exception`, como el resto de rutas.

**R4.** El sistema debe leer siete App Settings nuevas con defecto seguro:
`SIGRID_DOCUMENT_WRITE_ENABLED=false`, `SIGRID_DOCUMENT_WRITE_DATABASE=""`,
`SIGRID_DOCUMENT_MAX_BYTES=10485760`, `SIGRID_DOCUMENT_ALLOWED_MAGIC=["%PDF-"]`,
`SIGRID_DOCUMENT_ALLOWED_CONTIP=[]`, `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE=[]`,
`SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS=120`. Con los defectos `Settings()` arranca y el
endpoint responde `escritura_documental_deshabilitada`.

**R5.** El sistema no debe cambiar valor ni uso de ninguna App Setting existente:
`ALLOWED_WRITE_DATABASES` sigue siendo `["ruesma"]` y `sql/write` sigue sin poder nombrar
la documental (tests de F-003 en verde).

## Guards y dry-run (propuesta §10, §11, §14)

**R6.** SI `SIGRID_DOCUMENT_WRITE_DATABASE` está vacía, ENTONCES
`escritura_documental_deshabilitada`, también en dry-run. SI `database` no está en
`ALLOWED_WRITE_DATABASES` o es la documental, ENTONCES `base_de_datos_no_permitida`.

**R7.** El sistema debe validar contra el ERP, con lecturas: (a) SI no hay `dbo.con` con
`ide = conide` → `concepto_no_encontrado`; (b) SI `con.tip ≠ contip` o `contip ∉
SIGRID_DOCUMENT_ALLOWED_CONTIP` → `tipo_de_concepto_no_coincide` (lista vacía: ningún
concepto vale); (c) SI `gratipide ∉ SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`, no existe en
`dbo.auxgra` o su `fecbaj ≠ 0` → `clase_de_grafico_no_permitida`; (d) SI no existe
`dbo.usu` con `cod = usu` → `usuario_no_valido`.

**R8.** El sistema debe decodificar el base64 en modo estricto y, sobre los bytes: 0
bytes → `fichero_vacio`; más de `SIGRID_DOCUMENT_MAX_BYTES` (comprobado también sobre la
longitud del base64 antes de decodificar) → `tamano_excedido`; sin firma de
`SIGRID_DOCUMENT_ALLOWED_MAGIC` → `tipo_de_fichero_no_permitido`; `sha256` enviado distinto
del calculado → `sha256_no_coincide`. El `sha256` se calcula **siempre** en Python
(`hashlib`) y va en la respuesta.

**R9.** MIENTRAS `commit` sea `false`, el sistema debe ejecutar todos los guards y **solo
lecturas con credenciales de lectura** (concepto, `auxgra`, `usu`, `MAX(pos)` de `rcg`,
búsqueda de idempotencia, `peek_next_ide` en las dos `gra` y en `rcg`), sin abrir conexión
de escritura, y devolver el preview con `committed:false`, `dry_run:true`,
`filas_afectadas:0` y el aviso de `ide` provisionales.

## Commit e idempotencia (propuesta §7, §8, §9)

**R10.** CUANDO `commit` sea `true`, el sistema debe exigir además
`SIGRID_DOMAIN_WRITE_ENABLED`, `SIGRID_DOCUMENT_WRITE_ENABLED` y credenciales de escritura;
si falta alguna, `escritura_documental_deshabilitada`.

**R11.** El sistema debe hacer las tres escrituras en **UNA** conexión contra `database`
con `autocommit=False` (transacción local, sin MSDTC), llegando a la documental por nombre
de tres partes, en este orden: (1) binario en `<documental>.dbo.gra`; (2) metadatos en
`dbo.gra` con `ima` NULL y `vin=3`; (3) enlace en `dbo.rcg` con `con=conide`,
`gra=ide de (2)`, `pos=MAX(pos)+64` del concepto, `cla=0`.

**R12.** El sistema debe reservar los tres `ide` dentro de la transacción, bajo
`sp_getapplock` por recurso y `SELECT ISNULL(MAX(ide),0)+1 … WITH (UPDLOCK, HOLDLOCK)`, y
usar el `ide` reservado de (2) en `rcg.gra` sin rederivarlo por `cod`. Ante clave
duplicada, `run_in_write_transaction` revierte y reintenta hasta `DOMAIN_WRITE_MAX_RETRIES`.

**R13.** El sistema debe generar el `cod` **una sola vez por petición**, en Python, con el
formato medido `AAAAMMDDHHMMSS` + 4 dígitos + `.` + `usu` (hora Europe/Madrid), y escribir
**la misma cadena** y el mismo `emp` (`con.emp` del concepto) en (1) y (2).

**R14.** Antes del `COMMIT`, el sistema debe releer las tres filas por clave dentro de la
transacción; SI alguna no devuelve exactamente una fila → `ROLLBACK` y `filas_afectadas_inesperadas`.

**R15.** SI cualquier paso falla —guard, reserva, `INSERT`, relectura, clave duplicada
tras los reintentos—, ENTONCES `ROLLBACK` sin que quede **ninguna** de las tres filas, con
`colision_de_clave` cuando el error sea de clave duplicada.

**R16.** El sistema debe apoyar la unicidad del `cod` en el índice único `(emp, cod)` de
la documental: **sin** `COUNT(*)` previo por `cod`; un `cod` repetido lo rechaza el motor y
aplica R15.

**R17.** CUANDO el mismo documento (mismo tamaño y `sha256`) ya esté enlazado al mismo
`conide`, el sistema debe responder `ok:true`, `idempotente:true`, `filas_afectadas:0` con
`ide` y `cod` de lo existente, sin escribir nada. Se busca dentro de la transacción tras
el applock (y en dry-run con lecturas), comparando en Python el `sha256` de los binarios
del concepto con `DATALENGTH(ima)` igual. No se escribe en `gra.guid`.

## Seguridad, verificación y documentación (propuesta §11, §14; acceptance 7-9)

**R18.** Todo el SQL del endpoint debe ser **constante** en el código con los valores
como `?`; el único identificador no literal es la base documental, que sale de
configuración y pasa por `IdentifierGuard`. Ninguno viene de la petición.

**R19.** El sistema debe validar cada sentencia con `DatabaseReferenceGuard.validate(…,
allowed=[database, documental])` antes de abrir conexión, sin modificar
`sql_write_guard.py`, `sql_query_guard.py` ni `database_reference_guard.py`. La única base
ajena a la conexión que se nombra es la documental, y solo `dbo.gra`.

**R20.** El sistema no debe emitir `UPDATE`, `DELETE`, `MERGE` ni DDL en ninguna
sentencia del endpoint (control negativo en tests).

**R21.** CUANDO termine una llamada, el sistema debe registrar una traza con `conide`,
`contip`, `gratipide`, `cod`, `bytes`, `sha256`, `usu`, `commit`, `idempotente`,
`filas_afectadas`, resultado y duración; **nunca** el binario ni el base64.

**R22.** El sistema debe cubrir R1-R21 con tests unitarios sin red ni BBDD
(`test_f004_rN_*`), incluido el constructor de sentencias comparando el SQL generado
carácter a carácter, con fase RED en R11-R17.

**R23.** MANUAL (humano): tras el primer `commit:true` autorizado, el binario descargado
con `documents/read` (`database` documental, `table=gra`, `id_column=cod`) debe tener el
`sha256` enviado, y repetir la misma llamada debe dar `idempotente:true` con **una** sola
fila en `rcg`.

**R24.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (§2.1,
§4, §5, §7, §8, §10), corregir «réplica» en `dedicacion.md`, `partes.md` y `remesas.md`, y
ajustar `docs/ARCHITECTURE.md`, `CHECKPOINTS.md` (C3) y `CLAUDE.md` donde dicen que
`ruesma_rep` solo se lee.

## Preguntas abiertas y fuera de alcance

Decide el humano; consultas, defectos y exclusiones en `design.md`: Q4 formato de `gra.cod` ·
Q5 idempotencia por contenido en vez de `guid` o `cod` determinista, sin `clave_idempotencia`
· Q7 fila en `dbo.log` (por defecto NO) · `auxgra.tipaso` no se valida contra `con.tip` ·
columnas no variables de `gra`, fijadas midiendo una pareja real (T1).
