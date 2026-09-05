<!-- specs/F-004-endpoint-concepto-grafico/design.md -->
# F-004 · Diseño

## La decisión de fondo

Un **endpoint de dominio** con SQL constante, no abrir `sql/write` a la
documental (propuesta §5). Se reutiliza tal cual el patrón de
`sigrid/albaran-directo`: modelo Pydantic → caso de uso con dry-run por defecto
→ `SqlServerRepository.run_in_write_transaction()` para el commit. Las dos
bases están en la misma instancia [MEDIDO], así que una conexión contra la de
negocio con nombres de tres partes hacia la documental es una transacción
**local**. No se toca ningún guardia: el endpoint no recibe SQL, luego no pasa
por `SqlWriteGuard`; y el SQL que él mismo construye se autovalida con
`DatabaseReferenceGuard` contra `[negocio, documental]` (R19), de modo que la
documental queda autorizada **solo** por `SIGRID_DOCUMENT_WRITE_DATABASE` y
`ALLOWED_WRITE_DATABASES` sigue siendo `["ruesma"]` (R5).

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/concepto_grafico_models.py` | domain | `AttachConceptoGraficoRequest`, `AttachConceptoGraficoResponse`, `ConceptoPreview`, `GraficoPreview`, `EnlacePreview`, y `ConceptoGraficoError(ValueError)` con atributo `codigo` (los de R3) |
| `infrastructure/security/document_write_guard.py` | infrastructure | `DocumentWriteGuard`: base64 estricto, tamaño, firma binaria, `sha256`, listas blancas de `contip`/`gratipide`. Módulo puro: recibe los valores de configuración como argumentos, sin `Settings` |
| `application/use_cases/concepto_grafico_statements.py` | application | `ConceptoGraficoStatements`: **constructor puro de sentencias**. Recibe `(database, documental)`, valida `documental` con `IdentifierGuard`, y expone cada sentencia como `(sql, params)`. Sin I/O. Se autovalida con `DatabaseReferenceGuard` en `__init__` |
| `application/use_cases/attach_concepto_grafico_use_case.py` | application | `AttachConceptoGraficoUseCase(repository, settings)`: guards → lecturas → dry-run o `work(cursor)` |
| `tests/test_f004_settings.py` | — | R4, R5 |
| `tests/test_f004_models.py` | — | R1, R2 |
| `tests/test_f004_document_write_guard.py` | — | R8 (y R7 en la parte de listas) |
| `tests/test_f004_statements.py` | — | R11, R13, R16, R18, R19, R20: SQL exacto |
| `tests/test_f004_use_case.py` | — | R6-R7, R9-R10, R12, R14, R15, R17, R21 con un repositorio y un cursor falsos |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | Siete campos de R4, todos con defecto. Nuevo validador `parse_int_list` para `..._ALLOWED_CONTIP` / `..._ALLOWED_GRATIPIDE` (acepta JSON o CSV como `parse_string_list`). `..._ALLOWED_MAGIC` reutiliza `parse_string_list`; se comparan como bytes ASCII |
| `function_app.py` | Ruta `sigrid/concepto-grafico` (POST) con el mismo esqueleto de `sigrid_albaran_directo`, más dos `except` propios: `ConceptoGraficoError` → 400 con `details.codigo`; `pyodbc.IntegrityError` → 400 `colision_de_clave` («el ERP quedó sin cambios; reintente»). Ninguna ruta existente se edita |
| `local.settings.sample.json` | Las siete claves con sus defectos, comentadas por nombre |
| `docs/ARCHITECTURE.md`, `CHECKPOINTS.md` (C3), `CLAUDE.md` | Donde dicen «`ruesma_rep` solo se lee»: pasa a «solo se escribe por `sigrid/concepto-grafico`, nunca por `sql/write`» |
| `azure-apps/sigrid_api.md`, `dedicacion.md`, `partes.md`, `remesas.md` | R24. Ver T17 |

## Ficheros que NO se tocan

`infrastructure/security/*` (los cuatro guardias se usan, no se editan);
`sql_server_repository.py` (bastan `execute_read_query`, `peek_next_ide` y
`run_in_write_transaction`; sin método nuevo pese a la propuesta §15);
`execute_sql_command_use_case.py`, `read_document_use_case.py`, modelos y casos
de uso de albaranes, `write-lists.json`, `infra/` (el `GRANT` de §12.2 no hace falta [MEDIDO]).

## La relación entre las dos `gra` (`progress/explore_F-004_relacion_gra.md`)

**Solo por `(emp, cod)` [MEDIDO]**: índice único `gra_empcod` en las dos bases, 283.385 parejas,
ningún `ide`, columna ni tabla intermedia las une (los `ide` solo coinciden en 426 filas de 2009 y
divergen desde el 576); el segundo consumidor del repositorio en el ERP, `dog.codrep` («Código
repositorio externo»), referencia la documental por `cod`. Consecuencias: los `ide` de las dos filas
**no tienen que coincidir ni se intenta**; `emp` va en toda búsqueda cruzada (hay 8 `cod` repetidos
entre empresas); L5, L6 y E7 cruzan por `(emp, cod)`. **`vin` es el modo de almacenamiento [MEDIDO]**:
`3` = binario en el repositorio localizado por `(emp, cod)` (99,9 % de negocio, 100 % de la documental),
`0` = incrustado en `ruesma.gra.ima`, `1`/`4` = ruta, `2` = sin binario; el endpoint escribe `vin=3` en
las dos, `ima` NULL en negocio y `tex` vacío. **Riesgo**: si `cod` o `emp` difieren en un carácter entre
las dos filas, el motor no avisa y el gráfico queda «sin fichero» (así son los 517 huérfanos `vin=3` de
2021); por eso R13 exige la misma cadena y el mismo `emp`, y el test de R11 comprueba que E4 y E5
reciben **el mismo objeto** `cod` y `emp` (`is`), no dos copias.

## Modelo de petición (R1)

```python
class AttachConceptoGraficoRequest(BaseModel):
    database: str                      # base de NEGOCIO
    conide: int = Field(..., ge=1)
    contip: int = Field(..., ge=1)
    gratipide: int = Field(..., ge=1)
    res: str = Field(..., min_length=1, max_length=48)
    nom: str = Field(..., min_length=1, max_length=255)
    usu: str = Field(..., min_length=1, max_length=24)   # a propósito: gra.usu es varchar(128), pero el login debe existir en usu.cod (Texto 24)
    contenido_base64: str = Field(..., min_length=4)      # tope: ver R8
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    commit: bool = False
```

`content_type` y `clave_idempotencia` de la propuesta §6.2 **no** se aceptan: el tipo lo decide la
firma binaria (se devuelve el `content_type` detectado, como en `documents/read`), y la clave no tiene
dónde guardarse sin repurponer una columna del ERP (Q5). El tope de longitud del base64
(`ceil(max_bytes*4/3)+4`) se comprueba en el guard, no en el modelo, para que no dependa de `Settings`.

## El constructor de sentencias (R11, R13, R16, R18-R20)

Todas las cadenas son constantes de módulo; `<doc>` es `[documental]` ya
validado por `IdentifierGuard`. Sin `UPDATE`, `DELETE`, `MERGE` ni DDL.

| # | Momento | Sentencia (parámetros `?`) |
|---|---|---|
| L1 | ambos | `SELECT ide, tip, emp, cod, res FROM dbo.con WHERE ide = ?` |
| L2 | ambos | `SELECT ide, cod, res, fecbaj, tipaso FROM dbo.auxgra WHERE ide = ?` |
| L3 | ambos | `SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?` |
| L4 | ambos | `SELECT ISNULL(MAX(pos), 0) + 64, COUNT(*) FROM dbo.rcg WHERE con = ?` |
| L5 | ambos | idempotencia: `SELECT n.ide, n.cod, r.ide, CAST(d.ima AS varbinary(max)) FROM dbo.rcg r JOIN dbo.gra n ON n.ide = r.gra JOIN <doc>.dbo.gra d ON d.emp = n.emp AND d.cod = n.cod WHERE r.con = ? AND DATALENGTH(d.ima) = ?` |
| L6 | ambos | huérfanas: `SELECT n.ide, n.cod FROM dbo.rcg r JOIN dbo.gra n ON n.ide = r.gra LEFT JOIN <doc>.dbo.gra d ON d.emp = n.emp AND d.cod = n.cod WHERE r.con = ? AND d.ide IS NULL` |
| E1 | commit | `SELECT ISNULL(MAX(g.ide), 0) + 1 FROM <doc>.dbo.gra g WITH (UPDLOCK, HOLDLOCK)` |
| E2 | commit | `SELECT ISNULL(MAX(g.ide), 0) + 1 FROM dbo.gra g WITH (UPDLOCK, HOLDLOCK)` |
| E3 | commit | `SELECT ISNULL(MAX(r.ide), 0) + 1 FROM dbo.rcg r WITH (UPDLOCK, HOLDLOCK)` |
| E4 | commit | `INSERT INTO <doc>.dbo.gra (<29 columnas>) VALUES (?, …)` — `ima` = bytes |
| E5 | commit | `INSERT INTO dbo.gra (<29 columnas>) VALUES (?, …)` — `ima` = NULL |
| E6 | commit | `INSERT INTO dbo.rcg (ide, con, gra, pos, cla, feclee, fecalt) VALUES (?, ?, ?, ?, ?, ?, ?)` — `cla=0`, `feclee=0`, `fecalt=0` (las 7 columnas reales; `feclee`/`fecalt` no constan en `sigrid_tablas.md`, son `int` NULL, 0 en las 3.680 filas) |
| E7 | commit | relectura: `SELECT COUNT(*) FROM <doc>.dbo.gra WHERE emp = ? AND cod = ?`, ídem `dbo.gra`, y `SELECT COUNT(*) FROM dbo.rcg WHERE ide = ?` |

Las 29 columnas de `gra` van **explícitas y completas** en E4 y E5, en una
tabla única del módulo, con los valores medidos en
`progress/explore_F-004_mediciones.md` §2.1-2.3 (3.679 parejas, 1 solo grupo):

| Columna | Documental (E4) | Negocio (E5) |
|---|---|---|
| `ide` | reservado E1 | reservado E2 |
| `cod`, `emp`, `usu`, `fec` | generado una vez / `con.emp` / `request.usu` / hoy `AAAAMMDD` | **los mismos** |
| `nom`, `nomori` | `request.nom` en las dos (`nom = nomori` siempre) | ídem |
| `res` | **`''` siempre** (3.679/3.679, aunque en negocio sea otro) | `request.res` |
| `gratipide` | **`0` siempre** (en la documental no existe la clase 35) | `request.gratipide` |
| `vin` | `3` = binario en el repositorio [MEDIDO] | `3` |
| `ima` | el binario | `NULL` |
| `tex`, `cam` | `NULL` (tipo `text`) | `NULL` |
| `cla`, `guid`, `texrev`, `salusu`, `saltex` | `''` | `''` |
| `estcon`, `tipocu`, `numrev`, `salfec`, `salhor`, `mntide`, `graant`, `anx`, `ori`, `tip` | `0` | `0` |
| `pul` | `NULL` | `NULL` |

**Ninguna columna de `gra` ni de `rcg` tiene DEFAULT** y todas admiten NULL salvo `ide`
[MEDIDO con `INFORMATION_SCHEMA.COLUMNS`]: cada constante se escribe explícitamente, porque
omitir una columna la deja en NULL, que no es lo que tiene el ERP. **El test de R11 compara la
lista de columnas completa** de E4, E5 y E6. Por qué explícitas y no clonando una fila plantilla
(patrón de albaranes): `graant` y `mntide` son referencias y clonar copiaría la «versión
anterior» de otro documento; con columnas explícitas el SQL es constante y comparable (R22).

**`cod`** (R13): `f"{ahora:%Y%m%d%H%M%S}{dddd}.{usu}"`, con `ahora` en
`Europe/Madrid` (los workers de Azure corren en UTC; Sigrid sella en hora
local) y `dddd = int(sha256[:8], 16) % 10000` con ceros a la izquierda: sin
azar, reproducible en tests. El constructor recibe `ahora` como argumento.
`fec` sale del mismo instante. Q4 cerrada [MEDIDO]: Sigrid no interpreta el
sello ni `dddd` (pseudoaleatorio con 1.268 valores; tolera 31.941 `cod` que
son nombres de fichero); la unicidad la da el índice `(emp, cod)`.

**Binario e `image`**: `ima` viaja como parámetro `bytes`; SQL Server convierte
`varbinary` → `image` implícitamente. Si el motor lo rechazara, fallaría en
E4, con `ROLLBACK` y nada escrito; la corrección sería `CAST(? AS image)` en la
constante. No se puede sondear antes sin escribir: F-003 cierra la vía
`INSERT … WHERE 1 = 0` por `sql/write` hacia la documental.

## El caso de uso

```
run(request)
  ├─ guards de configuración (R6, R10)  ← antes de tocar la red
  ├─ DocumentWriteGuard: base64, tamaño, firma, sha256 (R8)
  ├─ lecturas L1-L6 con credenciales de LECTURA (R7, R17)
  ├─ cod, fec, filas E4/E5/E6 construidas (sin ide)
  ├─ idempotente → respuesta sin escribir (R17)
  ├─ dry-run → peek_next_ide ×3 (documental gra, negocio gra, rcg) + preview (R9)
  └─ commit → run_in_write_transaction(database=negocio, work=work,
        applock_resources=["SIGRID_IDE_<doc>_gra", "SIGRID_IDE_gra", "SIGRID_IDE_rcg"],
        timeout_seconds=SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS, max_retries=DOMAIN_WRITE_MAX_RETRIES)

work(cursor)                       ← reentrante: se repite entero en cada reintento
  ├─ cursor.connection.timeout = SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS
  ├─ L5 de nuevo (mismo documento ya colgado, ahora bajo applock) → idempotente
  ├─ E1, E2, E3 → tres ide
  ├─ E4, E5, E6 en ese orden (R11)
  ├─ E7: tres relecturas == 1, si no → ConceptoGraficoError(filas_afectadas_inesperadas) (R14)
  └─ return {ides}            → el repositorio hace COMMIT
```

Detalles que no se dejan al azar:

- **Orden documental → metadatos → enlace** (propuesta §7.2): si algo se
  partiera en mitad del `COMMIT`, cada prefijo es invisible para Sigrid; el
  orden inverso reproduce la anomalía de los 51 gráficos sin fichero.
- **Reintento**: `run_in_write_transaction` captura `pyodbc.IntegrityError`, revierte y repite
  `work`. El `cod` es el mismo en cada intento (se generó fuera) y, revertido el anterior, no colisiona
  con `(emp, cod)`. Una colisión real de `cod` —mismo segundo, usuario y `dddd`— se agota en los
  reintentos y sale como `colision_de_clave` (R15, R16).
- **`SET NOCOUNT ON`** lo deja activo el repositorio al tomar el applock; por eso R14 se verifica
  **releyendo** (E7) y no con `cursor.rowcount`, que el driver puede devolver a `-1`.
- **Timeout**: el `timeout_seconds` de `_connect()` es de login, no de sentencia; `work` fija
  `cursor.connection.timeout` para fallar (y revertir) antes de los 230 s del balanceador (propuesta §10).
- **Idempotencia por contenido** (R17): L5 filtra por `DATALENGTH(ima)` igual
  al tamaño enviado, así normalmente devuelve 0 o 1 binarios; el `sha256` se
  compara en Python. `HASHBYTES` no vale en SQL Server 2012 [MEDIDO].
- **Huérfanas** (R17): hay 1 fila real de clase 35 en negocio sin pareja documental [MEDIDO].
  L5 hace `JOIN` con la documental, así que una huérfana **nunca** es candidata: sin binario no
  hay nada que comparar ni `idempotente:true`. L6 las lista, el endpoint avisa «el concepto
  tiene N gráficos sin binario (ide …)» y adjunta de nuevo. No las repara: sería un `UPDATE`.
- **`auxgra.tipaso`** (`UPV,RCP,TAR` en la clase 35 [MEDIDO]) se lee (L2) y se
  devuelve en `avisos` si está vacío, pero **no** se valida contra `con.tip`:
  la correspondencia tipo→código no está medida. La lista blanca de `gratipide` cubre.
- **Auditoría** (R21): `logger.info` con un dict serializado; el `sha256`
  demuestra qué fichero se subió sin guardar el fichero.

## Tests sin red (R22)

- Repositorio falso con `execute_read_query` (devuelve por sentencia), `peek_next_ide` y
  `run_in_write_transaction` (invoca `work` con un cursor falso que graba `execute(sql, *params)`
  y responde a `fetchone`). El test de R15 hace que el cursor lance en E5 y comprueba que no se
  llegó a E6 y que el caso de uso no captura (el rollback es del repositorio real).
- R11: E4 y E5 reciben el mismo objeto `cod` y `emp` (`is`); lista completa de columnas.
- Control negativo de R20: ninguna constante contiene `UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE`.
- R19: `DatabaseReferenceGuard.extract_database_references(sql)` devuelve `[]` o `["<documental>"]`
  por sentencia, y `validate(..., allowed=["ruesma"])` **rechaza** E1/E4/E7/L5/L6: el guardia
  sigue cerrando `sql/write` a lo que este endpoint sí puede hacer.

## Riesgos y decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Idempotencia por contenido | Clave en `gra.guid` (propuesta §9.1) | `guid` es del ERP (vacío en 643.668 filas [MEDIDO]); el contenido no repurpone nada |
| `cod` con formato de Sigrid | `cod` determinista = clave del cliente | Sigrid no lo interpreta [MEDIDO], pero conservar el formato es gratis y mantiene la ficha uniforme |
| Sin `clave_idempotencia` | Aceptarla y guardarla | No hay columna donde vaya sin tocar el ERP |
| `UPDLOCK, HOLDLOCK` en la reserva | Solo applock + reintento (albaranes) | Sigrid escribe ~200 `gra` al día sin nuestro applock; el bloqueo de rango evita colisionar con la UI, y el reintento queda de red |
| Relectura E7 | `cursor.rowcount == 1` | `NOCOUNT ON` en la conexión; el rowcount no es fiable |
| Columnas explícitas | Clonar plantilla | Ver arriba: `graant`/`mntide` |
| Error de clave → 400 `colision_de_clave` en la ruta | Dejarlo en 500 | El cliente debe saber que el ERP quedó sin cambios; se captura en `function_app.py`, que ya importa infraestructura, para no meter `pyodbc` en application |
| Sin fila en `dbo.log` | Escribirla como F-009 | Sigrid no la escribe al importar: 0 filas `tab='gra'` en 8,4 M, `auxgra.conlog=0` en las 48 clases [MEDIDO] |
| `content_type` no se acepta | Aceptarlo y cotejarlo | La firma manda; un texto que elige el cliente no aporta seguridad |
| Dry-run exige `SIGRID_DOCUMENT_WRITE_DATABASE` | Dry-run sin configuración | Sin base documental no hay preview honesto de `ide_documental` ni idempotencia |

**Riesgo principal**: que el constructor se desvíe de lo medido (una columna omitida queda NULL;
`gratipide`/`res` documental copiados de la petición) o que el driver no convierta `bytes` →
`image`. Mitigación: constantes del informe y test de lista completa; el dry-run enseña las filas
completas; el primer commit va sobre una reclamación de prueba elegida por Posventa, con
`res = 'PRUEBA API - BORRAR'` y limpieza desde la UI de Sigrid (propuesta §14, nivel 3). No hay `DELETE`.

**Límite de microservicio**: adjuntar un documento a un concepto es una
operación del ERP; pertenece aquí, como los albaranes. Lo que NO pertenece
aquí es decidir a qué reclamación se adjunta o cuándo: eso es
`postventa-incidencias` (F-012).

## Decisiones medidas (cerradas el 2026-09-05, `progress/explore_F-004_mediciones.md`)

| # | Pregunta | Medido | Decisión |
|---|---|---|---|
| Q4 | ¿Interpreta Sigrid el formato de `gra.cod`? | No: 31.941 `cod` son nombres de fichero; `dddd` pseudoaleatorio (§1) | Formato medido, `dddd` del `sha256` |
| Q5 | ¿Usa Sigrid `gra.guid`? | Vacío en 284.096 + 359.572 filas (§1) | Idempotencia por contenido; `guid=''`; sin `clave_idempotencia` |
| Q7 | ¿Escribe Sigrid `dbo.log` al importar? | 0 filas `tab='gra'`; la pareja no dejó rastro; `conlog=0` (§1) | Sin cuarta escritura |
| tipaso | ¿Qué código corresponde a `con.tip=708`? | `UPV,RCP,TAR` en la clase 35; correspondencia no medida (§2.2) | No se valida; lista blanca |
| gra/rcg | Columnas no variables | §2.1-2.3: documental `gratipide=0`, `res=''`; `rcg` 7 columnas | Constantes explícitas de la tabla de arriba |

El humano **aprobó** el cambio de regla de gobierno (R24): `ruesma_rep` pasa a
escribirse solo por este endpoint, nunca por `sql/write`.

## Fuera de alcance

Borrar o sustituir adjuntos (ni reparar huérfanas); versionado (`graant`);
`multipart` o ficheros de decenas de MB; módulo `dog`/`condog`; abrir
`sql/write` a la documental; portar a `sigrid-api-v2`; escribir en `dbo.log`.
