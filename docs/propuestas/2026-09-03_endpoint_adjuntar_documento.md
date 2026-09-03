<!-- docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md -->
# Propuesta · `POST /api/sigrid/concepto-grafico`

**Adjuntar un documento a un concepto de Sigrid, escribiendo el binario en la
base documental.**

| | |
|---|---|
| **Estado** | PROPUESTA — no implementada, no aprobada |
| **Fecha** | 2026-09-03 |
| **Repositorio destino** | `sigrid-api` (v1, el desplegado). Ver [§1](#1--contra-qué-repositorio-se-especifica) |
| **Lo pide** | `postventa-incidencias`, feature **F-012** (`blocked`) |
| **Autor** | Redactada por un agente a petición del humano, sobre documentación y código. **No se ha ejecutado ni una llamada** contra Sigrid, la Function desplegada, el PostgreSQL compartido ni SharePoint |
| **Secretos** | Ninguno. Los identificadores de Azure, hosts y credenciales van como marcadores |

> **Convención de este documento.** Cada afirmación va marcada como
> **[MEDIDO]** (comprobado contra el ERP o leído en código/configuración, con
> su fuente), **[INFERIDO]** (deducción razonada, no comprobada) o
> **[ABIERTO]** (no se sabe; lleva la consulta que lo responde). Una propuesta
> que mezcla las tres sin distinguirlas es como se diseña sobre arena.

---

## Índice

0. [Resumen ejecutivo](#0--resumen-ejecutivo)
1. [Contra qué repositorio se especifica](#1--contra-qué-repositorio-se-especifica)
2. [La premisa: ¿es `ruesma_rep` escribible o es una réplica?](#2--la-premisa-es-ruesma_rep-escribible-o-es-una-réplica)
3. [Permisos del login de escritura sobre la documental](#3--permisos-del-login-de-escritura-sobre-la-documental)
4. [El problema, en el modelo de datos](#4--el-problema-en-el-modelo-de-datos)
5. [Por qué un endpoint de dominio y no abrir `sql/write`](#5--por-qué-un-endpoint-de-dominio-y-no-abrir-sqlwrite)
6. [Contrato del endpoint](#6--contrato-del-endpoint)
7. [Transaccionalidad](#7--transaccionalidad)
8. [Reserva de `ide` y correspondencia por `cod`](#8--reserva-de-ide-y-correspondencia-por-cod)
9. [Idempotencia](#9--idempotencia)
10. [Límites, y por qué esos](#10--límites-y-por-qué-esos)
11. [Seguridad: qué se abre y qué NO se abre](#11--seguridad-qué-se-abre-y-qué-no-se-abre)
12. [Configuración y permisos de base de datos](#12--configuración-y-permisos-de-base-de-datos)
13. [Impacto en los consumidores actuales](#13--impacto-en-los-consumidores-actuales)
14. [Verificación sin dejar basura en producción](#14--verificación-sin-dejar-basura-en-producción)
15. [Ficheros a tocar](#15--ficheros-a-tocar)
16. [Qué queda fuera](#16--qué-queda-fuera)
17. [Preguntas abiertas](#17--preguntas-abiertas-y-la-consulta-que-responde-cada-una)

---

## 0 · Resumen ejecutivo

`postventa-incidencias` cierra incidencias de posventa en el ERP (F-009:
`UPDATE dbo.con SET est` + fila en `dbo.log`, ambas en la base de **negocio**).
Lo que no puede hacer es **dejar el parte firmado adjunto a la reclamación**,
porque adjuntar un documento exige **tres escrituras en dos bases** y una de
ellas es la **documental**, que esta pasarela mantiene fuera de la escritura a
propósito.

Esta propuesta añade **un endpoint de dominio**, acotado a ese caso de uso, que
hace las tres escrituras en **una transacción**. No abre `sql/write` a la base
documental; al contrario, la propuesta depende de que siga cerrada.

**El titular, y va primero porque cambia todo lo demás:**

> **`ruesma_rep` NO es una réplica de solo lectura. Es una base documental
> normal, en la MISMA instancia de SQL Server, y el propio ERP le escribe cada
> vez que alguien importa un documento desde la UI de Sigrid.** Que esté fuera
> de `ALLOWED_WRITE_DATABASES` es una **política** de esta pasarela, no una
> limitación técnica. Ver [§2](#2--la-premisa-es-ruesma_rep-escribible-o-es-una-réplica).

Consecuencia directa: la transacción puede abarcar las dos bases **sin MSDTC**,
porque una transacción entre bases de la misma instancia es local.

Y la pieza que falta para poder implementar: **`user_rw` casi con seguridad no
tiene ningún permiso en `ruesma_rep` hoy**, y concedérselo (SELECT + INSERT
sobre **una sola tabla**) es una acción de administrador de base de datos que
esta propuesta describe pero no ejecuta.

---

## 1 · Contra qué repositorio se especifica

**Contra `C:\Users\pgris\PycharmProjects\sigrid-api` (la v1), que es la que
está desplegada.** No hay ambigüedad, y estas son las cinco evidencias:

| Evidencia | Fuente | Qué prueba |
|---|---|---|
| `azure-apps/sigrid_api.md` §11 «Despliegue» manda `cd …\sigrid-api` + `func azure functionapp publish func-sigridapi-dev-huyke` | doc dueño del ecosistema | La v1 es la que se publica |
| Ese documento se actualizó el **2026-08-18** (§4.1, App Settings efectivas) y sigue describiendo **una sola** Function App | el propio doc | Si la v2 estuviera desplegada, el dueño lo habría anotado |
| `remesas.md` (consumidor vivo) tiene `SIGRID_API_BASE_URL = https://func-sigridapi-dev-huyke...`; `partes.md` y `dedicacion.md` nombran la misma Function App | `azure-apps/` | Los consumidores apuntan a la v1 |
| **`func-sigridapi2-dev` no aparece en ningún documento del ecosistema**, solo en el `README.md` de la propia v2 | búsqueda en `azure-apps/*.md` | El cutover de la v2 no ha ocurrido |
| **`sigrid-api-v2` ni siquiera es un repositorio git** (`git log` → *not a git repository*); la v1 tiene historial, ramas y remoto | disco | La v2 es un borrador de trabajo, no un artefacto versionado |

**[MEDIDO]** las cinco.

**La v2 no se ignora, se anota.** Su `README.md` dice que las capas `domain/`,
`application/`, `infrastructure/` y `config/` están copiadas **sin cambios** de
la v1, y que solo cambia `interface_adapters/http/` y `function_app.py`. Este
endpoint sigue exactamente ese reparto: casi todo cae en capas compartidas, y
portarlo a la v2 es **añadir un router**. Se dice aquí para que la migración no
lo pierda por el camino (ver [§15](#15--ficheros-a-tocar)).

### Dónde vive este documento, y por qué aquí

`sigrid-api` **no tiene arnés**: ni `CLAUDE.md`, ni `harness/`, ni `specs/`, ni
`.claude/`. Su único documento propio es `docs/DEPLOYMENT_TERRAFORM_AND_CODE.md`.

Por eso se crea `docs/propuestas/`, con nombre `AAAA-MM-DD_asunto.md`: una
carpeta para diseño **antes** de escribir código, separada de `docs/`, que hoy
es operación. Si más adelante se instala el arnés genérico (`arnes-base`), esto
se mueve a `specs/` sin pérdida.

> **Aviso sobre `sigrid_api.md` en la raíz de este repositorio.** Es una copia
> **desactualizada** del documento del ecosistema. El `CLAUDE.md` transversal
> lo cita por su nombre como el caso que enseñó a no duplicar documentos. Esta
> propuesta **no lo toca**, y quien busque la verdad sobre la pasarela debe ir
> a `azure-apps/sigrid_api.md`. Limpiar esa copia es trabajo aparte.

Y lo que esta propuesta **no** toca, por la misma regla: **`azure-apps/sigrid_api.md`
describe lo que la pasarela hace hoy, no lo que se propone.** Se actualiza el
día que el endpoint exista y esté desplegado, no antes.

---

## 2 · La premisa: ¿es `ruesma_rep` escribible o es una réplica?

Esta es la sección que había que resolver antes de diseñar nada, porque si
`ruesma_rep` fuera una réplica de solo lectura de SQL Server, **la propuesta
entera sería imposible** y habría que decirlo en la primera línea.

### 2.1 · El conflicto documental que hay que deshacer

Cuatro documentos del ecosistema dicen cosas incompatibles:

| Documento | Qué dice |
|---|---|
| **`azure-apps/sigrid_api.md` §2** | «**no son una base y su réplica**: son dos bases con **propósitos distintos**». `ruesma_rep` es la **base documental**. Y: «Está fuera de `ALLOWED_WRITE_DATABASES` **precisamente para impedirlo**» |
| `azure-apps/dedicacion.md` §1 | «La **réplica** `ruesma_rep`. **No admite escritura** y no la usamos» |
| `azure-apps/partes.md` | «la **réplica** `ruesma_rep` no admite escritura» |
| `azure-apps/remesas.md` | «`ruesma_rep` (**réplica de lectura**)» |

Los tres últimos son documentos de **proyectos consumidores**. El primero es el
documento **del dueño de la pasarela**, y la regla de mantenimiento del
ecosistema es explícita: *el dueño del documento es el proyecto que describe*.
Entre «documental» y «réplica», manda `sigrid_api.md`.

Pero eso solo desempata la autoridad. La pregunta técnica se responde con
hechos, y hay tres.

### 2.2 · Hecho 1 — es la misma instancia. **[MEDIDO, en código]**

`infrastructure/repositories/sql_server_repository.py`, método `_connect()`,
construye **una sola** cadena de conexión para todo:

```
SERVER=tcp:{sql_server_host},{sql_server_port};
DATABASE={database};
```

`config/settings.py` declara **un único** `SQL_SERVER_HOST` y un único
`SQL_SERVER_PORT`. **No existe una segunda pareja host/puerto para la base
documental.** Lo único que cambia entre `ruesma` y `ruesma_rep` es el valor de
`DATABASE=`.

Un puerto TCP responde a **una** instancia de SQL Server. Por tanto las dos
bases cuelgan de la misma instancia, exactamente como dibuja el diagrama de
`sigrid_api.md` §3.2 — y ahora está confirmado en el código, no solo en el
dibujo.

**Consecuencia**: una transacción que toque las dos bases desde **una sola
conexión** es una transacción **local**, no distribuida. SQL Server solo
escala a MSDTC cuando intervienen servidores vinculados o llamadas remotas.
**No hace falta MSDTC** — que es una suerte, porque `pyodbc` no lo soporta.

### 2.3 · Hecho 2 — el ERP le escribe todos los días. **[MEDIDO]**

Es el argumento decisivo, y sale de
`postventa-incidencias/docs/referencia/03_modelo_posventa_sigrid.md` §4.1–§4.2
(consultas de solo lectura contra el ERP, 2026-08-25):

- `ruesma_rep.gra` tiene **357.901 filas** y **ninguna con `ima` vacío**.
- Para el parte firmado de ejemplo, `ruesma_rep.gra.ima` mide **242.534 bytes**,
  y su fila se creó el **2026-08-18 a las 11:40:39**, cuando una persona de
  Posventa importó el PDF desde la UI de Sigrid.
- `ruesma.gra.ima` está **vacío** para los 13.450 gráficos de posventa: el
  binario **no existe en ninguna otra parte**.

Es decir: **el byte se escribe en `ruesma_rep` y en ningún sitio más**. Una
réplica de solo lectura no puede recibir esa escritura, y no hay una base
origen desde la que replicarla. La conclusión razonable, y la marco como tal:

> **[INFERIDO, con evidencia fuerte]** `ruesma_rep` es una base normal en
> lectura/escritura. El sufijo `_rep` es «repositorio», no «réplica». Lo que
> hay hoy es una **política de esta pasarela**, escrita en
> `ALLOWED_WRITE_DATABASES`, no un impedimento del motor.

### 2.4 · Hecho 3 — la política es explícita y está en un fichero

`write-lists.json` e `infra/scripts/setup-deploy-write.ps1` fijan
`ALLOWED_WRITE_DATABASES = ["ruesma"]`. Es una App Setting. Se cambia editando
una lista, no migrando una base. **[MEDIDO]**

### 2.5 · La comprobación que convierte la inferencia en dato

Es **una consulta de lectura**, sin efectos, ejecutable por `sql/read`:

```sql
-- database: "ruesma"   (basta ALLOWED_QUERY_PREFIXES = SELECT)
SELECT DATABASEPROPERTYEX('ruesma_rep','Updateability') AS actualizable,  -- 'READ_WRITE' esperado
       DATABASEPROPERTYEX('ruesma_rep','Status')        AS estado,        -- 'ONLINE' esperado
       DATABASEPROPERTYEX('ruesma_rep','IsInStandBy')   AS en_standby,    -- 0 esperado
       DATABASEPROPERTYEX('ruesma','Updateability')     AS negocio_actualizable
```

Y, para dejar clavado que la instancia es una sola, ejecutar **la misma**
consulta con `database: "ruesma"` y con `database: "ruesma_rep"`:

```sql
SELECT @@SERVERNAME AS servidor,
       SERVERPROPERTY('ServerName')   AS nombre_servidor,
       SERVERPROPERTY('InstanceName') AS instancia,
       DB_NAME()                      AS base_actual
```

Si `actualizable` sale `READ_WRITE` y las dos llamadas devuelven el mismo
`servidor`, esta sección pasa entera de **[INFERIDO]** a **[MEDIDO]** y el
diseño de abajo se sostiene tal cual. **Es la primera tarea de cualquier
implementación, y es gratis.**

### 2.6 · Y si la premisa fuera falsa

Si `Updateability` devolviera `READ_ONLY`, o si las dos bases resultaran estar
en instancias distintas, **esta propuesta no vale y hay que decirlo sin
maquillaje**. El diseño alternativo sería otro documento, y las opciones
serían: (a) pedir al proveedor del ERP un procedimiento almacenado que haga el
alta del gráfico completa, (b) la vía del gráfico por **URL** que
`postventa-incidencias` persigue en su F-023 —que solo escribe en la base de
negocio—, o (c) el módulo documental `dog`/`condog`, que tiene columna `url`
nativa. **[Ver §16](#16--qué-queda-fuera)**

El resto del documento asume la premisa verdadera y lo dice en cada punto donde
importa.

---

## 3 · Permisos del login de escritura sobre la documental

**Lo que se sabe leyendo el repositorio y la documentación:**

| Pregunta | Respuesta | Marca |
|---|---|---|
| ¿Hay dos logins, uno de lectura y otro de escritura? | Sí: `ro_user` y `user_rw`, con contraseñas separadas en Key Vault (`sigrid-password`, `sigrid-write-password`) | **[MEDIDO]** `sigrid_api.md` §3.3, §5.1 |
| ¿`ro_user` puede leer `ruesma_rep`? | Sí. `documents/read` abre la conexión con **credenciales de lectura** y `DATABASE=ruesma_rep`, y funciona en producción | **[MEDIDO]** `sql_server_repository.read_document()` usa `_read_credentials()` |
| ¿`ro_user` puede escribir? | No. «`ro_user` **no tiene permisos de escritura en el propio SQL Server**» | **[MEDIDO]** `sigrid_api.md` §5.1 |
| ¿`user_rw` puede escribir en `ruesma`? | Sí, `INSERT`/`UPDATE`. `DELETE` **no** lo tiene concedido de forma general | **[MEDIDO]** `sigrid_api.md` §7.7 y la lista `["INSERT","UPDATE","DELETE"]` de prefijos, que es de verbos SQL y no de permisos reales |
| **¿`user_rw` puede escribir —o siquiera conectarse— en `ruesma_rep`?** | **No se sabe** | **[ABIERTO]** |

**No hay ni un script de `GRANT` en este repositorio.** Se buscó en `infra/` y
en `docs/`: los scripts crean recursos de Azure y fijan App Settings, y ninguno
toca permisos de SQL Server. Los permisos se concedieron a mano en el motor y
no están versionados en ninguna parte.

**Lo más probable, y va marcado [INFERIDO]:** `user_rw` es un *login* del
servidor mapeado como *usuario* **solo en `ruesma`**. Si nunca se le creó
usuario en `ruesma_rep`, un `INSERT` cruzado fallaría con
`916 · El principal del servidor no puede tener acceso a la base de datos
"ruesma_rep" en el contexto de seguridad actual` — un error limpio, no una
escritura a medias. Que falle limpio es una buena noticia, pero no es un
permiso.

**Cómo se responde**, y no se puede desde la pasarela porque `sql/read` usa
siempre las credenciales de lectura: lo ejecuta un administrador del SQL
Server, en una sesión, y es **solo lectura**:

```sql
-- 1) ¿Existe el usuario en la documental?
USE ruesma_rep;
SELECT name, type_desc, authentication_type_desc
FROM sys.database_principals
WHERE name = 'user_rw';

-- 2) Si existe: ¿qué puede hacer sobre dbo.gra?
EXECUTE AS USER = 'user_rw';
    SELECT permission_name, state_desc
    FROM fn_my_permissions('dbo.gra', 'OBJECT');
REVERT;

-- 3) Y lo mismo en negocio, para confirmar el punto de partida
USE ruesma;
EXECUTE AS USER = 'user_rw';
    SELECT 'gra' AS tabla, permission_name FROM fn_my_permissions('dbo.gra','OBJECT')
    UNION ALL
    SELECT 'rcg',          permission_name FROM fn_my_permissions('dbo.rcg','OBJECT');
REVERT;
```

Lo que haría falta conceder está en [§12.2](#122--permisos-de-base-de-datos-la-acción-del-dba).

---

## 4 · El problema, en el modelo de datos

Todo lo de esta sección es **[MEDIDO]** contra el ERP el 2026-08-25 y consta en
`postventa-incidencias/docs/referencia/03_modelo_posventa_sigrid.md` §4.1–§4.3.

```
ruesma  (negocio, escribible hoy)          ruesma_rep  (documental, cerrada hoy)
├── con    la reclamación (tip = 708)      └── gra        357.901 filas
├── gra    282.599 filas · METADATOS             ├── ide  espacio de ide PROPIO
│     └── ima  VACÍO para posventa               ├── cod  ← la MISMA cadena que en negocio
└── rcg    el enlace con → gra                   └── ima  ← EL BINARIO, siempre relleno
```

Cuatro hechos que mandan sobre el diseño:

1. **Hay dos tablas `gra`, en dos bases.** La de negocio guarda los metadatos y
   es la que enlaza `rcg`; la documental guarda el binario en `ima`.
2. **Los `ide` de las dos son espacios independientes.** El mismo número en una
   y otra son documentos distintos (comprobado con un caso concreto).
3. **La pareja se localiza por `cod`.** De los 13.450 gráficos de
   reclamaciones, **13.399 (99,6 %)** tienen su binario en la documental con el
   **mismo `cod`**. Los 51 restantes son metadatos sin fichero: la anomalía que
   este endpoint no debe volver a producir.
4. **`gra.vin = 3`** («INCRUSTADO EXTERNO») es el modo de los 13.450, y en él
   `ruesma.gra.ima` y `ruesma.gra.tex` van **vacíos**. «Externo» significa
   *fuera de la base de negocio*, no *en Internet*.

Cómo queda una fila real de parte firmado — la plantilla exacta que hay que
reproducir:

| Columna de `ruesma.gra` | Valor medido | Quién lo pone |
|---|---|---|
| `cod` | `202608181140392614.<login>` — sello `AAAAMMDDHHMMSS` + 4 dígitos + `.` + login | Sigrid |
| `emp` | la empresa de la reclamación | Sigrid |
| `res` | `PARTE FIRMADO` (Texto 48) | **lo teclea Posventa** |
| `nom` | `RS26.08 - 0123 PARTE FIRMADO.pdf` (Texto 255) | Sigrid |
| `gratipide` | `35` → `auxgra` `PV002` «POSTVENTA:Fotos Reparaciones» | **lo elige Posventa** |
| `vin` | `3` | Sigrid |
| `usu` | el login | Sigrid |
| `fec` | `20260818` (entero `AAAAMMDD`) | Sigrid |
| `ima`, `tex`, `cla`, `guid` | **vacíos** | — |

Y el enlace, `ruesma.rcg` — cinco columnas y ninguna sabe nada del contenido:

| Columna | Valor medido en los 13.450 enlaces |
|---|---|
| `ide` | el del enlace (índice primario único) |
| `con` | la reclamación |
| `gra` | el `ide` del gráfico **en negocio** |
| `pos` | múltiplos de **64**; 52 posiciones distintas en uso |
| `cla` | `0` en los 13.450 |

`auxgra` autoriza el destino: `PV002` (`ide = 35`) tiene
`tipaso = 'UPV,RCP,TAR'`, y **`RCP` es lo que permite colgar el documento de una
reclamación**; `tammax = 0` (sin límite de tamaño configurado) y `fecbaj = 0`
(activo). **El ERP no nos va a frenar por tamaño: el límite tiene que ponerlo
la pasarela.**

---

## 5 · Por qué un endpoint de dominio y no abrir `sql/write`

La alternativa obvia —meter `ruesma_rep` en `ALLOWED_WRITE_DATABASES` y
mandar los tres `INSERT` por `sql/write`— **se descarta**, y no por gusto:

| | Abrir `sql/write` a la documental | Endpoint de dominio acotado |
|---|---|---|
| Qué queda abierto | `INSERT`/`UPDATE`/`DELETE` sobre **cualquier tabla** de la base documental, para **cualquier** poseedor de la function key | **Un** `INSERT` sobre **una** tabla (`dbo.gra`), y solo por esta ruta |
| Superficie de error | Un `UPDATE` mal escrito puede vaciar `ima` de 357.901 documentos. `REQUIRE_WHERE_ON_UPDATE_DELETE` obliga a poner *un* `WHERE`, no a que sea correcto | No hay `UPDATE` ni `DELETE`. El permiso concedido no los incluye |
| Reserva de `ide` | **A cargo del cliente**. `sigrid_api.md` §7.5: `sql/write` **no** protege la reserva con applock | La hace la API, con applock y reintento, como los otros endpoints de dominio |
| Pasar el `ide` de una sentencia a otra | **Imposible**: una sentencia por elemento, sin variables T-SQL compartidas. Hay que rederivar por `cod` | Un cursor abierto toda la transacción: el valor se lee y se reutiliza |
| BLOBs | `sql/write` recibe `parameters` de un JSON; no hay ruta pensada para binarios, ni tope de tamaño, ni validación de tipo de fichero | `varbinary(max)` parametrizado, con tope y validación de firma |
| Auditoría | «alguien hizo un INSERT» | «alguien adjuntó *este* documento, de *este* tamaño, a *este* concepto» |
| Quién conoce las reglas del ERP | **El cliente** | **La API** — que es literalmente la regla práctica de `sigrid_api.md` §7.1 |

`sigrid_api.md` §7.1 lo deja escrito: *«si existe un endpoint de dominio para lo
que quieres hacer, úsalo»*. Esta propuesta crea ese endpoint en vez de quitar
la única barrera que hoy protege 357.901 documentos.

> **El matiz que es el corazón de la propuesta:** la base documental está
> cerrada por una razón, y la propuesta **la respeta**.
> `ALLOWED_WRITE_DATABASES` **sigue siendo `["ruesma"]`** después de este
> cambio. El endpoint nuevo no lee esa lista: usa una suya, y el permiso que se
> concede en el motor es tan estrecho que ni siquiera permitiría el daño que
> preocupa.

---

## 6 · Contrato del endpoint

### 6.1 · Ruta y método

```
POST /api/sigrid/concepto-grafico
```

**Por qué ese nombre.** La familia de dominio ya existente es
`sigrid/contrato-lineas`, `sigrid/albaran`, `sigrid/albaran-directo`: sustantivos
del ERP. En Sigrid la tabla del enlace, `rcg`, se llama literalmente *«Gráficos
en conceptos»*. `concepto-grafico` es esa operación y ninguna otra. Nombres
como `documents/write` se descartan por ser el espejo de `documents/read`, que
es genérico, y este endpoint **no** lo es.

Autenticación: `x-functions-key`, igual que todo lo demás. Sin ella, 401.

### 6.2 · Petición

```jsonc
{
  "database": "ruesma",              // base de NEGOCIO. La documental NO se pide: sale de config
  "conide": 2418732,                 // ide del concepto destino (la reclamación)
  "contip": 708,                     // tipo esperado. Obligatorio: es un control, no un dato
  "gratipide": 35,                   // clase de gráfico (auxgra). Lista blanca en config
  "res": "PARTE FIRMADO",            // gra.res  — Texto 48
  "nom": "RS26.08 - 0123 PARTE FIRMADO.pdf",   // gra.nom — Texto 255
  "usu": "<login-sigrid>",           // gra.usu — validado contra dbo.usu
  "contenido_base64": "JVBERi0xLjQK…",         // el binario
  "content_type": "application/pdf",
  "sha256": "9f86d0…",               // opcional; si viene, se verifica contra lo recibido
  "clave_idempotencia": null,        // opcional; si no viene, se deriva (ver §9)
  "commit": false                    // DRY-RUN POR DEFECTO
}
```

**Cómo viaja el binario: base64 dentro del JSON. Y por qué.**

1. **Coherencia de la pasarela.** Los siete endpoints de hoy validan el cuerpo
   con un modelo Pydantic y aplican el guard sobre el objeto ya validado
   (`sigrid_api.md` §1.2). Aceptar `multipart/form-data` abriría **una segunda
   ruta de parseo** que no pasa por ese embudo — justo donde no conviene tener
   dos caminos, porque es el que escribe en el ERP.
2. **Simetría con `documents/read`.** La pasarela ya tiene el concepto de
   binario dentro de JSON (`MAX_INLINE_BINARY_BYTES`). Base64 en el cuerpo es
   la operación inversa de lo que ya se hace.
3. **El coste es asumible y está medido.** Base64 infla un **33 %**. Con el
   tope propuesto de 10 MB de binario, el cuerpo llega a ~13,4 MB. El parte
   firmado medido pesa **242.534 bytes**: el caso real está dos órdenes de
   magnitud por debajo del tope.
4. **Lo que se pierde, y se dice:** todo el fichero pasa por memoria del
   *worker* dos veces (base64 y decodificado). Si algún día hiciera falta
   adjuntar ficheros de decenas de MB, **la salida correcta no es subir el
   tope: es un endpoint distinto con `multipart` o con carga en dos fases**.
   Queda en [§16](#16--qué-queda-fuera).

**Lo que el cliente NO manda, y es deliberado:**

| No se acepta | Por qué |
|---|---|
| el nombre de la base documental | Sale de configuración. Si viajara en la petición, el cliente elegiría dónde escribir |
| nombres de tabla, esquema o columna | **Este endpoint no construye ni un identificador a partir de la entrada.** Todo el SQL es constante. Ver [§11](#11--seguridad-qué-se-abre-y-qué-no-se-abre) |
| `gra.ide`, `rcg.ide`, `gra.cod` | Los reserva y genera la API ([§8](#8--reserva-de-ide-y-correspondencia-por-cod)) |
| `gra.vin` | Constante `3`, el modo medido de los 13.450 |
| `gra.ima` en la base de **negocio** | Va siempre vacío. El binario solo existe en la documental |

### 6.3 · Respuesta

Misma forma en dry-run y en commit; lo que cambia es `committed`.

```jsonc
{
  "ok": true,
  "committed": false,                  // false en dry-run y en respuesta idempotente
  "idempotente": false,                // true = ya estaba adjunto; no se escribió nada
  "database": "ruesma",
  "database_documental": "ruesma_rep",
  "concepto": {
    "ide": 2418732, "tip": 708, "emp": 1,
    "cod": "RS26.08/0123", "res": "Sellado de encuentro de falsos techos"
  },
  "grafico": {
    "cod": "202609031712045518.<login>",
    "ide_negocio": 296222,             // en dry-run: PREVISUALIZADO (MAX+1), no reservado
    "ide_documental": 357902,          // idem
    "vin": 3, "gratipide": 35,
    "res": "PARTE FIRMADO",
    "nom": "RS26.08 - 0123 PARTE FIRMADO.pdf",
    "bytes": 242534,
    "sha256": "9f86d0…"
  },
  "enlace": { "ide": 13451, "con": 2418732, "gra": 296222, "pos": 128, "cla": 0 },
  "filas_afectadas": 3,                // 0 en dry-run y en respuesta idempotente
  "avisos": []                         // p.ej. "el concepto ya tiene 2 gráficos asociados"
}
```

**El aviso que hay que leer:** en dry-run, `ide_negocio` e `ide_documental` son
**previsualizaciones** (`MAX(ide)+1` sin reservar, con el método
`peek_next_ide` que ya existe y es de solo lectura). Entre el dry-run y el
commit pueden cambiar, y **eso no es un error**: el commit reserva de nuevo,
dentro de la transacción. Quien construya un cliente no debe guardarlos como
si fueran definitivos.

### 6.4 · Errores

Se mantiene **la convención de la casa** (`sigrid_api.md` §1.3): error
controlado → **HTTP 400** con `{ok:false, error, details}`; inesperado → **500**
con `details.exception`. Los siete endpoints actuales lo hacen así y sus
clientes lo dan por hecho; inventar 409 y 413 solo para este endpoint obligaría
a cada cliente a aprender dos gramáticas. **El código de máquina va en `error`,
no en el estado HTTP.**

| `error` | HTTP | Qué significa | Qué hacer |
|---|---|---|---|
| `escritura_documental_deshabilitada` | 400 | Falta alguna de las cinco llaves de [§12.1](#121--app-settings-nuevas) | Es configuración, no la petición |
| `base_de_datos_no_permitida` | 400 | `database` no está en `ALLOWED_WRITE_DATABASES` | Mandar la base de negocio |
| `concepto_no_encontrado` | 400 | No hay fila en `dbo.con` con ese `ide` | Revisar el `ide` |
| `tipo_de_concepto_no_coincide` | 400 | `con.tip` ≠ `contip`, o `contip` fuera de la lista blanca | **Es la barrera que impide adjuntar a una factura o a un contrato** |
| `clase_de_grafico_no_permitida` | 400 | `gratipide` no existe en `auxgra`, o `fecbaj ≠ 0`, o su `tipaso` no autoriza a ese tipo de concepto, o no está en la lista blanca | Elegir una clase válida |
| `usuario_no_valido` | 400 | `usu` no existe en `dbo.usu` | **El documento se firma con un login real o no se escribe** |
| `fichero_vacio` | 400 | 0 bytes tras decodificar | — |
| `tipo_de_fichero_no_permitido` | 400 | La firma binaria no está en la lista blanca, o no casa con `content_type` | Mandar un PDF de verdad |
| `tamano_excedido` | 400 | Supera `SIGRID_DOCUMENT_MAX_BYTES` | **No subir el tope sin releer [§10](#10--límites-y-por-qué-esos)** |
| `sha256_no_coincide` | 400 | El `sha256` enviado no casa con lo recibido | El cuerpo se corrompió en tránsito |
| `codigo_de_grafico_duplicado` | 400 | El `cod` generado ya existe. **No debería ocurrir nunca** | Reintentar; si se repite, hay un problema de reloj |
| `colision_de_ide` | 400 | Tras `DOMAIN_WRITE_MAX_RETRIES` sigue colisionando el `ide` | **El ERP quedó sin ningún cambio.** Reintentar más tarde |
| `filas_afectadas_inesperadas` | 400 | El batch no afectó exactamente a 3 filas → ROLLBACK | Incidente: investigar antes de repetir |
| `permiso_denegado_en_documental` | 400 | El motor rechazó la escritura (error SQL 916/229) | Falta el `GRANT` de [§12.2](#122--permisos-de-base-de-datos-la-acción-del-dba) |
| (inesperado) | 500 | Cualquier otra cosa | Mirar Application Insights |

**El caso que no tiene código de error, y es el peligroso:** que el balanceador
corte a los 230 s. El cliente **no recibe respuesta** y la transacción **puede
haberse confirmado**. La respuesta a eso no es un código HTTP: es la
idempotencia de [§9](#9--idempotencia). Un cliente que reintente con la misma
`clave_idempotencia` no duplica nada; uno que reintente a ciegas, sí.

---

## 7 · Transaccionalidad

**Regla dura: las tres escrituras entran, o no entra ninguna.**

### 7.1 · Cómo se consigue

**Una conexión, abierta contra la base de negocio, con `autocommit=False`, y
nombres de tres partes para llegar a la documental.** Se reutiliza tal cual
`SqlServerRepository.run_in_write_transaction()`, que ya existe y ya hace lo
difícil: toma `sp_getapplock` por cada recurso, ejecuta el trabajo, hace
`commit`, y ante `IntegrityError` hace `rollback` y **reintenta** hasta
`DOMAIN_WRITE_MAX_RETRIES`.

Como las dos bases están en la **misma instancia** ([§2.2](#22--hecho-1--es-la-misma-instancia-medido-en-código)),
esto es **una transacción local**. SQL Server no promueve a MSDTC: la promoción
solo ocurre con servidores vinculados o llamadas remotas, y aquí no hay
ninguna. `pyodbc` no necesita saber nada nuevo.

```
run_in_write_transaction(database=<negocio>, autocommit=False)
  ├─ sp_getapplock  'sigrid-api:ide:<documental>.gra'
  ├─ sp_getapplock  'sigrid-api:ide:<negocio>.gra'
  ├─ sp_getapplock  'sigrid-api:ide:<negocio>.rcg'
  │
  ├─ (0) comprobación de idempotencia          → si ya está: rollback y salir sin escribir
  ├─ (1) INSERT en <documental>.dbo.gra  (ide propio, cod, ima = EL BINARIO)
  ├─ (2) INSERT en <negocio>.dbo.gra     (ide propio, MISMO cod, ima vacío, vin = 3)
  ├─ (3) INSERT en <negocio>.dbo.rcg     (ide propio, con = conide, gra = ide de (2))
  ├─ comprobación: filas afectadas == 3   → si no, rollback
  └─ COMMIT
```

**Detalle fino sobre los applocks, y hay que dejarlo escrito:**
`sp_getapplock` con `@LockOwner = 'Transaction'` toma el bloqueo **en la base
de datos del contexto actual**, que aquí es siempre la de negocio. Los tres
nombres de recurso son etiquetas convenidas, no rutas: lo que serializa es que
**todos los escritores usen las mismas etiquetas**. Como este endpoint es el
único camino de escritura a la documental, la convención se cumple por
construcción. Si algún día hubiera un segundo escritor, tendría que respetar
estos nombres o el applock no valdría de nada.

### 7.2 · El orden importa, aunque haya transacción

Las tres escrituras van en el orden **documental → metadatos → enlace**, y no
es casual. Si por lo que sea la transacción se partiera —un corte de red en
mitad del `commit`, un fallo del motor—, **cada prefijo de esa secuencia es un
estado que el ERP tolera**:

| Hasta dónde llegó | Cómo lo ve Sigrid |
|---|---|
| solo (1) | Un binario huérfano en la documental, al que **no apunta nada**. Invisible |
| (1)+(2) | Una fila `gra` que no cuelga de ningún concepto. No sale en ninguna ficha |
| (1)+(2)+(3) | Correcto |

El orden **inverso** produciría lo contrario: un gráfico visible en la ficha de
la reclamación **cuyo fichero no existe**. Que es exactamente la anomalía de
los **51** gráficos de posventa sin pareja en la documental
([§4](#4--el-problema-en-el-modelo-de-datos)). Se ordena así para que el peor
caso sea invisible en vez de roto.

### 7.3 · Y si NO fueran la misma instancia

Entonces no hay transacción posible sin MSDTC, y `pyodbc` no lo soporta. El
diseño de repuesto sería **dos transacciones locales en el orden de §7.2**,
aceptando la ventana entre ambas:

1. Transacción A, en la documental: `INSERT` del binario. Commit.
2. Transacción B, en negocio: `INSERT` de metadatos + enlace. Commit.
3. Si B falla, **el binario queda huérfano** y no se intenta borrar (no hay
   permiso `DELETE`, y no debe haberlo). Se registra el `cod` en un aviso.
4. Un barrido periódico de solo lectura los lista para que una persona los
   borre desde la UI de Sigrid:

```sql
-- huérfanos: binario en la documental sin metadatos en negocio
SELECT d.ide, d.cod, DATALENGTH(d.ima) AS bytes
FROM <documental>.dbo.gra d
LEFT JOIN <negocio>.dbo.gra n ON n.cod = d.cod
WHERE n.ide IS NULL AND d.cod LIKE '2026%'
```

**Esta rama es el plan B y no se implementa salvo que §2.5 la haga necesaria.**
Se documenta porque la pregunta «¿y si no son la misma instancia?» merece una
respuesta y no un encogimiento de hombros.

---

## 8 · Reserva de `ide` y correspondencia por `cod`

### 8.1 · Por qué es delicado

En Sigrid **`ide` no es IDENTITY ni hay SEQUENCE activa** (`sigrid_api.md`
§7.5, y `sig_ides` está vacía). El siguiente identificador es `MAX(ide)+1`, con
la condición de carrera evidente. Y aquí hay **tres** reservas, en **dos
espacios de numeración independientes** ([§4](#4--el-problema-en-el-modelo-de-datos),
hecho 2).

### 8.2 · La técnica, que no se inventa: se reutiliza la de F-009

`postventa-incidencias` ya resolvió esto en producción para `dbo.log`, y la
técnica está en `specs/F-009-cierre-sigrid/design.md` §7.3 y en el código
`services/postventa-api/infrastructure/sigrid/escrituras.py`
(`SQL_INSERT_LOG`). Su forma canónica:

```sql
INSERT INTO dbo.log (ide, …)
SELECT (SELECT ISNULL(MAX(l.ide), 0) + 1 FROM dbo.log l WITH (UPDLOCK, HOLDLOCK)), …
FROM dbo.con c
WHERE c.ide = ? AND c.tip = ? AND c.est = ?
```

Lo que se reutiliza son **las tres propiedades**, no la sintaxis literal:

1. **`WITH (UPDLOCK, HOLDLOCK)` sobre el agregado** serializa la reserva:
   `HOLDLOCK` mantiene el bloqueo de rango hasta el `commit`, así que dos
   sesiones no pueden leer el mismo `MAX`.
2. **Si aun así colisiona, falla en seguro.** El índice primario único rechaza
   el `INSERT`, la transacción entera se revierte y **el ERP queda sin ningún
   cambio**.
3. **El filtro va en el `FROM`, nunca en un `WHERE EXISTS`**: un agregado sin
   `GROUP BY` devuelve una fila aunque no case nada, y `ISNULL(MAX(ide),0)+1`
   valdría `1` — colisión garantizada contra la fila más antigua de la tabla.
   Es el detalle que F-009 documenta con más énfasis y es fácil de perder.

**Dónde este endpoint mejora sobre F-009, y conviene decirlo.** F-009 tuvo que
meter la reserva *dentro* de la sentencia porque `sql/write` manda cada
sentencia como un elemento independiente y no se puede pasar un valor de una a
otra. **Un endpoint de dominio no tiene esa limitación**: mantiene un cursor
abierto toda la transacción. Así que la reserva puede ser su propia sentencia y
el valor se reutiliza en Python:

```sql
-- reserva, en la documental
SELECT ISNULL(MAX(g.ide), 0) + 1
FROM <documental>.dbo.gra g WITH (UPDLOCK, HOLDLOCK)
```

Mismas tres propiedades, mismo modo de fallo, y encima el **reintento** que
`run_in_write_transaction` ya trae y que F-009 no tiene. Con esto **`rcg.gra`
recibe el `ide` exacto que se acaba de reservar**, sin rederivarlo por `cod` —
que es lo que F-009 habría tenido que hacer, y una fuente de duplicados si
`cod` no fuera único.

### 8.3 · El `cod`, que es la correspondencia entre las dos filas

**`cod` es la única cuerda que une los metadatos con su binario.** No hay clave
foránea, no hay `ide` compartido: `sigrid-api` y el ERP emparejan las dos filas
comparando la cadena.

Formato, copiado del que escribe Sigrid **[MEDIDO]**: `202608181140392614.<login>`

```
AAAAMMDDHHMMSS   4 dígitos   .   login
    14 caracteres     4       1    ≤ 128 en total (gra.cod es Texto 128)
```

- Los 14 primeros: el instante de la operación, en la zona horaria del ERP.
- **Los 4 dígitos siguientes: [ABIERTO]**. En la fila medida valen `2614`. No
  hay documentación de qué significan. La API los generará como un contador o
  un aleatorio de 4 dígitos, **y esto solo es seguro si Sigrid no los
  interpreta** ([§17](#17--preguntas-abiertas-y-la-consulta-que-responde-cada-una), Q4).
- El login: el mismo que va en `gra.usu`, ya validado contra `dbo.usu`.

**La regla que no se puede romper:** el `cod` se genera **una vez**, en Python,
antes de la transacción, y **la misma cadena** se escribe en las dos filas. Si
las dos bases recibieran `cod` distintos, el documento quedaría inaccesible sin
que nada fallara — el peor tipo de error.

**Guarda previa, dentro de la transacción y después del applock:**

```sql
SELECT COUNT(*) FROM dbo.gra WHERE cod = ?            -- en negocio
SELECT COUNT(*) FROM <documental>.dbo.gra WHERE cod = ?
```

Si alguno no es `0` → `codigo_de_grafico_duplicado` y rollback. Hace falta
porque **`gra.cod` no tiene índice único declarado** en el diccionario (solo
`ide` es índice primario) **[MEDIDO]** — así que el motor no nos protege y hay
que protegerse a mano.

### 8.4 · `rcg.pos`

**[MEDIDO]**: múltiplos de 64, con 52 posiciones distintas en uso. **[INFERIDO]**:
es el orden en que se listan los gráficos de un concepto. Regla propuesta:

```sql
SELECT ISNULL(MAX(r.pos), 0) + 64 FROM dbo.rcg r WHERE r.con = ?
```

Un `pos = 64` fijo chocaría con el primer gráfico si la reclamación ya tuviera
uno — y las reclamaciones de posventa a menudo tienen fotos antes del parte.
`rcg.cla = 0`, constante, como en los 13.450 medidos.

---

## 9 · Idempotencia

**Requisito duro: adjuntar dos veces el mismo parte no puede duplicar el
gráfico ni el enlace.** Y no es teórico: el corte del balanceador a 230 s
([§6.4](#64--errores)) produce exactamente el escenario «el cliente no sabe si
se escribió».

### 9.1 · La clave

Se deriva de forma determinista de lo que identifica *este documento en este
concepto*:

```
clave = UUIDv5( namespace_sigrid_api , f"{conide}:{sha256(binario)}" )
```

36 caracteres canónicos. Se guarda en **`gra.guid`** («Identificador Único»,
Texto 48) **[MEDIDO]** que en los partes firmados de posventa está **vacío**.

El cliente puede mandar su propia `clave_idempotencia` (un identificador de su
proceso, p.ej. `F-012:RS26.08/0123`); si no la manda, se usa la derivada. **La
derivada es la buena por defecto**: no depende de que el cliente recuerde nada
entre reintentos, que es justo lo que falla cuando el proceso se cae.

### 9.2 · La comprobación

Dentro de la transacción, después de tomar el applock y antes de cualquier
`INSERT`:

```sql
SELECT TOP (1) g.ide, g.cod, r.ide AS enlace_ide
FROM dbo.gra g
JOIN dbo.rcg r ON r.gra = g.ide
WHERE r.con = ? AND g.guid = ?
```

Si devuelve fila: **no se escribe nada**, se hace `rollback` (no hay nada que
confirmar) y se responde `ok: true, idempotente: true, filas_afectadas: 0`, con
el `ide` y el `cod` de lo que ya existe. **El cliente debe tratarlo como éxito**,
y así hay que documentarlo en `azure-apps/sigrid_api.md` el día del despliegue.

El applock cierra la otra ventana: dos llamadas simultáneas con la misma clave
**se serializan**, y la segunda ve la fila que acaba de confirmar la primera.

### 9.3 · El riesgo de reutilizar `gra.guid`, y su plan B

`guid` es una columna **del ERP**, no nuestra. Que esté vacía en los partes de
posventa **no prueba** que Sigrid no la use en otros módulos —el diccionario
tampoco lo explica— y si el ERP la usara para versionar documentos
(`graant` sugiere que hay versionado), escribir ahí podría confundirlo.

**Es una pregunta abierta que hay que responder ANTES de implementar**
([§17](#17--preguntas-abiertas-y-la-consulta-que-responde-cada-una), Q5).

**Plan B, si `guid` resulta estar en uso:** idempotencia **por contenido**, sin
tocar ninguna columna nueva. El binario ya está en la documental y SQL Server
sabe resumirlo:

```sql
SELECT TOP (1) n.ide, n.cod
FROM dbo.rcg r
JOIN dbo.gra n            ON n.ide = r.gra
JOIN <documental>.dbo.gra d ON d.cod = n.cod
WHERE r.con = ?
  AND HASHBYTES('SHA2_256', d.ima) = ?
```

Es más caro (lee los binarios de los gráficos ya colgados de ese concepto, que
son pocos: los 13.450 gráficos se reparten entre miles de reclamaciones) pero
**no repurpone ninguna columna del ERP**, que es la propiedad que importa.
`HASHBYTES` acepta `varbinary(max)` desde SQL Server 2016 **[INFERIDO: falta
confirmar la versión del motor, Q6]**.

---

## 10 · Límites, y por qué esos

| Límite | Valor propuesto | Justificación |
|---|---|---|
| **Tamaño del binario** | **10 MB** decodificado (`SIGRID_DOCUMENT_MAX_BYTES = 10485760`) | El parte firmado medido pesa **242.534 bytes**. 10 MB deja sitio a un escaneo en color de varias páginas y sigue muy por debajo de lo que revienta la memoria del worker. `auxgra.tammax = 0` **[MEDIDO]**: el ERP no pone ninguno, así que el límite es nuestro o no existe |
| **Tamaño del cuerpo HTTP** | ~13,4 MB | Consecuencia del anterior: base64 infla un 33 % |
| **Timeout de la operación** | **120 s** (`SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS`) | **Deliberadamente por debajo de los 230 s del balanceador.** Si el tope fuera 230, el LB cortaría antes que la aplicación y el cliente no sabría si la transacción se confirmó. Con 120 la aplicación falla primero, hace `rollback` y **responde**. Es la diferencia entre un error y un misterio |
| **Corte del balanceador** | 230 s, no configurable | `sigrid_api.md` §3.4. **No se puede subir.** El binario cruza una VPN site-to-site: es el tramo lento, y por eso el tope de tamaño es a la vez un tope de tiempo |
| **Filas afectadas** | **exactamente 3**, constante del código | Un adjunto correcto afecta a 3 filas: una en cada `gra` y una en `rcg`. Cualquier otro número es un accidente → `rollback`. Misma red de seguridad que `MAXIMO_FILAS_AFECTADAS = 2` en F-009, y **no se hace configurable a propósito**: no hay ningún caso legítimo en que valga otra cosa |
| **`MAX_AFFECTED_ROWS` global** | **no aplica** | Es de `sql/write`. Este endpoint tiene el suyo, fijo |
| **Reintentos ante colisión de `ide`** | `DOMAIN_WRITE_MAX_RETRIES` (3) | Se reutiliza el mecanismo existente |
| **Timeout del applock** | `APPLOCK_TIMEOUT_MS` (10 s) | Idem |
| **Concurrencia** | 1 escritura a la vez, por construcción | El applock serializa. Con el volumen esperado —unas decenas de partes al mes— sobra |

---

## 11 · Seguridad: qué se abre y qué NO se abre

### 11.1 · Lo que se abre, dicho con precisión

> Un `INSERT`, sobre **una** tabla (`<documental>.dbo.gra`), con **columnas
> fijas**, alcanzable **solo** por `POST /api/sigrid/concepto-grafico`, con
> function key, con cinco llaves de configuración echadas y con `commit: true`
> explícito.

### 11.2 · Lo que NO se abre

| Sigue cerrado | Cómo se garantiza |
|---|---|
| `sql/write` contra la base documental | **`ALLOWED_WRITE_DATABASES` sigue siendo `["ruesma"]`.** `execute_write_command()` valida contra esa lista y no se toca. El endpoint nuevo **no lee esa lista**: usa `SIGRID_DOCUMENT_WRITE_DATABASE`, que es otra cosa |
| `UPDATE` y `DELETE` en la documental | **No existe la ruta en el código**, y el `GRANT` de [§12.2](#122--permisos-de-base-de-datos-la-acción-del-dba) concede solo `SELECT, INSERT`. Dos barreras, una de ellas en el motor |
| Cualquier otra tabla de la documental | Lista blanca **constante en el código**, no en configuración: `{documental: {"gra"}}`. Una App Setting mal puesta no puede ampliarla |
| Adjuntar a cualquier concepto | `SIGRID_DOCUMENT_ALLOWED_CONTIP` (p.ej. `[708]`, reclamaciones). **Un `ide` de factura de compra devuelve `tipo_de_concepto_no_coincide`**. Es la contención más importante: el endpoint **no** es «adjunta lo que sea a lo que sea» |
| Clases de gráfico arbitrarias | `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`, **y** validación viva contra `auxgra` (`fecbaj = 0` y `tipaso` autoriza esa familia de concepto) |
| Subir un ejecutable disfrazado | Validación por **firma binaria** (magic bytes): por defecto solo `%PDF-`. Se comprueba el contenido, **no** el `content_type` ni la extensión del `nom`, que son texto que el cliente elige |
| Firmar el documento con el login de otro | `usu` se valida contra `dbo.usu`. Un login inexistente → `usuario_no_valido` |
| Inyección SQL | **Este endpoint no construye ni un identificador a partir de la entrada.** Tabla, esquema, columnas y base salen de constantes y de configuración; todos los valores viajan como parámetros `?`. `IdentifierGuard` ni siquiera hace falta: **no hay nada dinámico que guardar** |
| Escribir sin querer | Doble llave (`SIGRID_DOMAIN_WRITE_ENABLED` **y** `SIGRID_DOCUMENT_WRITE_ENABLED`, ambas `false` por defecto) más **dry-run por defecto**, igual que los otros endpoints de dominio |

### 11.3 · Auditoría

**En Application Insights**, una traza por llamada con: `conide`, `contip`,
`gratipide`, `cod` generado, `bytes`, `sha256`, `usu`, `commit`,
`idempotente`, `filas_afectadas`, resultado y duración. **Nunca el binario, ni
en fragmentos.** El `sha256` es lo que permite demostrar después *qué* fichero
se subió sin guardar el fichero.

**En el propio ERP**, la fila de `gra` deja `usu` y `fec`, que es lo que deja
Sigrid cuando lo hace una persona.

**Decisión: NO se escribe fila en `dbo.log`.** F-009 sí lo hace, porque replica
un **proceso** del ERP («Cerrar parte») que Sigrid registra. Adjuntar un
gráfico no consta que Sigrid lo registre: la fila medida se creó a las 11:40:39
y el `log` medido corresponde al cierre de las 11:46:33. Escribir un `log` que
el ERP no escribe nos haría distinguibles por el lado equivocado. **[ABIERTO]**:
verificarlo antes de implementar
([§17](#17--preguntas-abiertas-y-la-consulta-que-responde-cada-una), Q7); si
resultara que Sigrid sí registra el alta de gráficos, esta decisión se invierte.

---

## 12 · Configuración y permisos de base de datos

### 12.1 · App Settings nuevas

Todas **aditivas y con valor por defecto**. Esto no es un detalle de estilo:
`build_dependencies()` está bajo `@lru_cache` y construye `Settings()` **una
vez para todos los endpoints**. Un campo nuevo sin defecto haría que la
Function App fallara al arrancar y **tumbaría también `sql/read`**, del que
depende el datamart. La regla es: **defecto seguro siempre, y el endpoint falla
en tiempo de petición, no en tiempo de importación.**

| Variable | Defecto | Uso |
|---|---|---|
| `SIGRID_DOCUMENT_WRITE_ENABLED` | **`false`** | Llave maestra de este endpoint |
| `SIGRID_DOCUMENT_WRITE_DATABASE` | `""` | La base documental. Vacío ⇒ endpoint apagado |
| `SIGRID_DOCUMENT_MAX_BYTES` | `10485760` | Tope del binario decodificado |
| `SIGRID_DOCUMENT_ALLOWED_MAGIC` | `["%PDF-"]` | Firmas binarias admitidas |
| `SIGRID_DOCUMENT_ALLOWED_CONTIP` | `[]` | Tipos de concepto destino. **Vacío ⇒ ninguno** |
| `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` | `[]` | Clases de gráfico. **Vacío ⇒ ninguna** |
| `SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS` | `120` | Ver [§10](#10--límites-y-por-qué-esos) |

Las listas vacías por defecto significan que **desplegar el código no habilita
nada**. Hay que decidir explícitamente qué se permite.

Se reutilizan sin cambios: `SIGRID_DOMAIN_WRITE_ENABLED`, `APPLOCK_TIMEOUT_MS`,
`DOMAIN_WRITE_MAX_RETRIES`, `SQL_SERVER_WRITE_USERNAME` / `..._PASSWORD`.

**Lo que NO se toca, y es el punto de la propuesta:**

```
ALLOWED_WRITE_DATABASES  = ruesma      ← SIGUE IGUAL
ALLOWED_WRITE_PREFIXES   = INSERT,UPDATE,DELETE   ← SIGUE IGUAL
ALLOWED_DATABASES        = ruesma,ruesma_rep      ← SIGUE IGUAL
```

Valor de despliegue propuesto para la nueva:
`SIGRID_DOCUMENT_WRITE_DATABASE = <nombre de la base documental>` — el mismo
que ya usa `documents/read`.

**Recordatorios de despliegue** (`sigrid_api.md` §11): fijar las App Settings
por **fichero JSON** en ASCII sin BOM (`az … --settings "@fichero"`), nunca
inline; y tras `appsettings set`, el worker puede tardar en recogerlas
(`stop` + `start` si un flag «no aplica»).

### 12.2 · Permisos de base de datos: la acción del DBA

Sin esto el endpoint devuelve `permiso_denegado_en_documental` y no escribe
nada. Lo ejecuta **una persona con permisos de administrador en el motor**, una
vez:

```sql
-- En la base DOCUMENTAL, y solo ahí.
USE <base_documental>;

-- 1) Mapear el login de escritura como usuario de esta base
CREATE USER [user_rw] FOR LOGIN [user_rw];

-- 2) El permiso MÍNIMO, y sobre UNA sola tabla
GRANT SELECT, INSERT ON OBJECT::dbo.gra TO [user_rw];

-- 3) NADA más. Explícitamente NO se concede:
--    · UPDATE ni DELETE (sobre gra ni sobre nada)
--    · db_datareader ni db_datawriter (darían la base entera)
--    · permisos sobre ninguna otra tabla
```

`SELECT` hace falta —no solo `INSERT`— porque la reserva de `ide`
(`SELECT MAX(ide) … WITH (UPDLOCK, HOLDLOCK)`) y la guarda de `cod` duplicado
son lecturas sobre esa misma tabla.

**Verificación de que el permiso quedó bien acotado**, también de solo lectura:

```sql
USE <base_documental>;
EXECUTE AS USER = 'user_rw';
    SELECT permission_name, state_desc FROM fn_my_permissions('dbo.gra','OBJECT');
    -- Esperado: SELECT e INSERT. Si aparece UPDATE, DELETE o ALTER, el GRANT se pasó.
    SELECT COUNT(*) FROM fn_my_permissions(NULL, 'DATABASE');
    -- Esperado: mínimo. Si sale una lista larga, se concedió un rol y hay que revertirlo.
REVERT;
```

Y en la base de negocio hay que **confirmar** (no conceder, salvo que falte)
que `user_rw` tiene `SELECT, INSERT` sobre `dbo.gra` y `dbo.rcg`.

---

## 13 · Impacto en los consumidores actuales

**Qué se rompe: nada.** Y estas son las razones, no una promesa:

| Consumidor (`sigrid_api.md` §10) | Qué usa | Impacto |
|---|---|---|
| `datamart-seg-anual` | `sql/read` | **Ninguno.** Ni el modelo ni la respuesta de `sql/read` cambian |
| Pipeline de albaranes (sv1–sv6) | `sql/read`, `sigrid/albaran*` | **Ninguno** |
| `finanzas-remesas` | `sql/read` | **Ninguno** |
| `mcp-bbdd` | indirecto | **Ninguno** |
| Scripts de consulta | `sql/read` | **Ninguno** |
| `partes` (sv3/sv5) | `sql/read`, `documents/read`, `sql/write` | **Ninguno.** `documents/read` no se toca |
| `postventa-incidencias` | `sql/read`, `sql/write` | Gana un endpoint. F-009 sigue igual |

**Ficheros compartidos que sí se tocan, y por qué son seguros:**

- **`config/settings.py`** — solo campos nuevos **con defecto**. `extra="ignore"`
  ya está activo, así que un despliegue con las App Settings viejas arranca
  igual. Ver el aviso de [§12.1](#121--app-settings-nuevas): un campo sin
  defecto tumbaría **toda** la Function App, `sql/read` incluido.
- **`function_app.py`** — una ruta nueva y una línea más en
  `build_dependencies()`. Las siete rutas existentes no se editan.
- **`infrastructure/repositories/sql_server_repository.py`** — un método nuevo.
  **`execute_write_command()` no se toca**, que es lo que garantiza que
  `sql/write` sigue sin poder llegar a la documental.
- **`infrastructure/security/sql_write_guard.py`** — **no se toca**. Este
  endpoint no pasa por él porque no recibe SQL.

**Sobre la v2** (`sigrid-api-v2`): sus capas `domain/`, `application/`,
`infrastructure/` y `config/` son copia de las de aquí, así que este trabajo se
porta añadiendo **un router** en `interface_adapters/http/routers/`. Si el
cutover a la v2 ocurre después de implementar esto, hay que rehacer la copia de
esas cuatro capas o se pierde el endpoint.

**Regla de mantenimiento del ecosistema:** cuando este endpoint esté desplegado,
**`azure-apps/sigrid_api.md` se actualiza en ese mismo trabajo** — §2.1 (deja de
ser cierto que «`ruesma_rep` **nunca** se escribe desde la API»), §4 (las App
Settings nuevas), §5 (la capa de seguridad), §7.1 (la tabla de endpoints de
dominio), §8 (la referencia) y §10 (el consumidor nuevo). Y conviene corregir
de paso la palabra «réplica» en `dedicacion.md`, `partes.md` y `remesas.md`,
que es incorrecta ([§2](#2--la-premisa-es-ruesma_rep-escribible-o-es-una-réplica))
y ya ha costado una feature bloqueada.

---

## 14 · Verificación sin dejar basura en producción

No consta que exista una instancia de pruebas de Sigrid. Todo lo de abajo está
pensado para eso.

### Nivel 1 — Tests unitarios, sin red, sin BBDD, sin ERP

El constructor de las sentencias es un **módulo puro**: recibe datos y devuelve
las sentencias y sus parámetros, sin abrir nada. Es el patrón que
`postventa-incidencias` usa en `escrituras.py` para F-009, y ahí el test compara
el SQL **carácter a carácter**. Aquí igual:

- El SQL generado, exacto, para un caso conocido.
- Que el `cod` es **idéntico** en las dos sentencias de `gra`.
- Que el orden es documental → metadatos → enlace.
- Que `vin = 3`, `cla = 0`, `ima` vacío en negocio.
- Guards: `contip` fuera de lista, `gratipide` de baja, firma binaria que no es
  PDF, 0 bytes, tamaño excedido, `sha256` que no casa.
- **Control negativo**: que ninguna sentencia contiene `UPDATE`, `DELETE` ni
  `DROP`, y que la única tabla nombrada en la base documental es `gra`.

`sigrid_api.md` §13 apunta «tests automatizados de guards y casos de uso» como
pendiente del roadmap. Este endpoint es un buen sitio para empezar, porque es
el que escribe binarios en el ERP.

### Nivel 2 — Dry-run contra producción: **es 100 % lectura**

`commit: false` no escribe **nada**. Localiza el concepto, valida `gratipide`
contra `auxgra`, valida el login contra `dbo.usu`, decodifica el binario,
comprueba firma y tamaño, calcula el `sha256`, genera el `cod` y previsualiza
los dos `ide` con `peek_next_ide()` —que ya existe y usa **credenciales de
lectura**—. Se puede ejecutar contra producción tantas veces como haga falta.

**Es aquí donde se detecta el 90 % de los problemas** antes de tocar nada.

### Nivel 3 — El primer commit real, y cómo se limpia

1. **Posventa elige una reclamación de prueba.** No la elegimos nosotros.
2. El PDF es evidentemente de prueba y `res = 'PRUEBA API - BORRAR'`, para que
   cualquiera que lo vea en la ficha sepa qué es.
3. Se ejecuta el dry-run, se lee entero, y **entonces** el commit.
4. **La verificación de punta a punta usa un endpoint que ya existe**: se
   descarga el binario de vuelta con `documents/read` contra la base
   documental, usando `id_column = "cod"` y el `cod` devuelto, y se compara su
   `sha256` con el que se envió. Si coincide, el fichero llegó entero y está
   donde tiene que estar.
5. Comprobación en la UI de Sigrid: el gráfico aparece en la ficha de la
   reclamación y el PDF se abre.
6. **La limpieza la hace Posventa desde la UI de Sigrid**, que es la vía
   soportada: `sigrid_api.md` §7.7 dice que `user_rw` no tiene `DELETE` y que
   lo creado por la API se anula desde la interfaz. **Nosotros no borramos, y
   no debemos poder.**

Consultas de verificación, todas por `sql/read`:

```sql
-- 1) La fila de metadatos, en negocio
SELECT ide, cod, emp, res, nom, gratipide, vin, usu, fec, guid,
       DATALENGTH(ima) AS bytes_en_negocio        -- esperado: NULL o 0
FROM dbo.gra WHERE cod = ?

-- 2) El binario, en la documental  (database: la documental)
SELECT ide, cod, DATALENGTH(ima) AS bytes         -- esperado: los bytes enviados
FROM dbo.gra WHERE cod = ?

-- 3) El enlace
SELECT r.ide, r.con, r.gra, r.pos, r.cla
FROM dbo.rcg r JOIN dbo.gra g ON g.ide = r.gra
WHERE g.cod = ?

-- 4) Que no quedó nada huérfano de la prueba
SELECT g.ide, g.cod, g.res
FROM dbo.gra g LEFT JOIN dbo.rcg r ON r.gra = g.ide
WHERE r.ide IS NULL AND g.res = 'PRUEBA API - BORRAR'
```

### Nivel 4 — Idempotencia, comprobada de verdad

Repetir la **misma** llamada con `commit: true`. Debe devolver
`idempotente: true`, `filas_afectadas: 0`, y la consulta 3 debe seguir
devolviendo **una** fila. Si devolviera dos, el endpoint no cumple su
requisito y no se despliega.

---

## 15 · Ficheros a tocar

Sin código: solo el mapa, para dimensionar.

| Fichero | Qué | Capa |
|---|---|---|
| `domain/models/documento_domain_models.py` | **nuevo** — `AttachDocumentRequest` / `Response`, con la validación Pydantic (tamaño, base64, longitudes de `res`/`nom`/`usu`) | dominio |
| `application/use_cases/attach_concept_document_use_case.py` | **nuevo** — orquesta: guards → dry-run o transacción | aplicación |
| `infrastructure/security/document_write_guard.py` | **nuevo** — base documental, `contip`, `gratipide`, firma binaria, tamaño, login | infraestructura |
| `infrastructure/repositories/sql_server_repository.py` | **modificar** — un método nuevo. `execute_write_command()` **intacto** | infraestructura |
| `config/settings.py` | **modificar** — siete campos, todos con defecto | configuración |
| `function_app.py` | **modificar** — una ruta y una línea en `build_dependencies()` | interfaz |
| `tests/` | **nuevo** — hoy no existe carpeta de tests en este repositorio | — |
| `infra/scripts/grant-documental-write.sql` | **nuevo** — el `GRANT` de [§12.2](#122--permisos-de-base-de-datos-la-acción-del-dba), versionado en vez de a mano | infra |

**Explícitamente NO se tocan:** `infrastructure/security/sql_write_guard.py`,
`infrastructure/security/sql_query_guard.py`,
`application/use_cases/execute_sql_command_use_case.py`,
`application/use_cases/read_document_use_case.py`, ni `write-lists.json`.

---

## 16 · Qué queda fuera

| Fuera de esta propuesta | Por qué |
|---|---|
| **Borrar o sustituir un documento adjunto** | Requiere `DELETE`, que es justo lo que no se concede. Se hace desde la UI de Sigrid (`sigrid_api.md` §7.7) |
| **Versionado de documentos** (`gra.graant`) | El ERP tiene el concepto; no se replica |
| **Adjuntar a tipos de concepto fuera de la lista blanca** | Se abre añadiendo un valor a `SIGRID_DOCUMENT_ALLOWED_CONTIP`, con la decisión que eso merece |
| **Ficheros de decenas de MB** | Pedirían `multipart` o carga en dos fases: otro endpoint, otro diseño |
| **El módulo documental `dog`/`condog`** | Sigrid tiene otra familia documental, con `url` nativa y «Código repositorio externo». Puede ser el camino que el ERP tiene pensado para documentos externos, pero un `dog` **es a su vez un concepto** y obliga a crear su fila en `con`. Más escrituras, más riesgo, y otra propuesta |
| **La vía del gráfico por URL** (F-023 de `postventa-incidencias`) | Alternativa que **no toca la documental**: registra el gráfico como referencia al PDF ya archivado en SharePoint. Está bloqueada por una medida que solo Posventa puede dar. **Este endpoint la hace innecesaria, pero no la sustituye**: es el humano quien decide qué camino se sigue |
| **Ejecutar el proceso nativo «Cerrar parte»** | No lo hace F-009 y no lo hace esto. Adjuntar el documento **no** cierra nada |
| **Abrir `sql/write` a la base documental** | **Rechazado.** [§5](#5--por-qué-un-endpoint-de-dominio-y-no-abrir-sqlwrite) |
| **Actualizar `azure-apps/sigrid_api.md`** | Describe lo que la pasarela hace **hoy**. Se actualiza cuando el endpoint exista, en el trabajo que lo despliegue |
| **Portar el endpoint a `sigrid-api-v2`** | La v2 no está desplegada. Se anota el impacto ([§13](#13--impacto-en-los-consumidores-actuales)) y nada más |

---

## 17 · Preguntas abiertas, y la consulta que responde cada una

Ninguna se puede contestar leyendo. Todas son de **lectura** salvo donde se
indica. Las tres primeras son **bloqueantes**: sin ellas no se empieza a
implementar.

| # | Pregunta | Cómo se responde | Bloqueante |
|---|---|---|---|
| **Q1** | ¿Es `ruesma_rep` `READ_WRITE` y está en la misma instancia que `ruesma`? | Las dos consultas de [§2.5](#25--la-comprobación-que-convierte-la-inferencia-en-dato), por `sql/read`. **Coste: dos llamadas** | **Sí** |
| **Q2** | ¿Tiene `user_rw` usuario y permisos en la base documental? | Las consultas de [§3](#3--permisos-del-login-de-escritura-sobre-la-documental), por un administrador del motor. La pasarela no puede: `sql/read` usa siempre credenciales de lectura | **Sí** |
| **Q3** | ¿Qué columnas rellena Sigrid en la fila de la base **documental**? Está medido que `cod` e `ima` sí; del resto no hay medida | `SELECT TOP (1) ide, cod, emp, res, nom, nomori, gratipide, vin, usu, fec, cla, guid, DATALENGTH(ima) AS bytes FROM dbo.gra WHERE cod = ?` con `database` = la documental, sobre el `cod` del parte de ejemplo. **Si el ERP rellena más columnas, hay que replicarlas o el documento podría no abrirse desde la ficha** | **Sí** |
| **Q4** | ¿Significan algo los 4 dígitos de `gra.cod` entre el sello de tiempo y el punto? | `SELECT TOP (200) cod FROM dbo.gra WHERE cod LIKE '2026%' ORDER BY ide DESC` y mirar si son secuenciales por día, por usuario, o aleatorios | No, pero cambia cómo se genera el `cod` |
| **Q5** | ¿Usa Sigrid la columna `gra.guid` para algo? | `SELECT COUNT(*) AS con_guid FROM dbo.gra WHERE guid IS NOT NULL AND guid <> ''` + `SELECT TOP (20) ide, cod, guid, graant FROM dbo.gra WHERE guid <> ''` | No: hay plan B ([§9.3](#93--el-riesgo-de-reutilizar-graguid-y-su-plan-b)) |
| **Q6** | ¿Qué versión de SQL Server es? (`HASHBYTES` sobre `varbinary(max)` necesita 2016+) | `SELECT @@VERSION, SERVERPROPERTY('ProductMajorVersion')` | No |
| **Q7** | ¿Escribe Sigrid en `dbo.log` al importar un gráfico? | `SELECT TOP (20) * FROM dbo.log WHERE tab = 'gra' ORDER BY ide DESC` y `SELECT COUNT(*) FROM dbo.log WHERE tab = 'gra'` | No, pero decide [§11.3](#113--auditoría) |
| **Q8** | ¿Hay `cod` duplicados en alguna de las dos `gra`? No hay índice único declarado | `SELECT TOP (20) cod, COUNT(*) c FROM dbo.gra GROUP BY cod HAVING COUNT(*) > 1`, en las dos bases | No: la guarda de [§8.3](#83--el-cod-que-es-la-correspondencia-entre-las-dos-filas) lo cubre |
| **Q9** | ¿Cuál es el tamaño real de los partes firmados? El único medido son 242.534 bytes | `SELECT MIN(DATALENGTH(ima)), AVG(CAST(DATALENGTH(ima) AS bigint)), MAX(DATALENGTH(ima)) FROM dbo.gra` en la documental, acotado a los `cod` de posventa | No: dimensiona el tope de [§10](#10--límites-y-por-qué-esos) |
| **Q10** | ¿Existe un entorno de pruebas de Sigrid? | Preguntar. Cambiaría entero [§14](#14--verificación-sin-dejar-basura-en-producción) | No |

---

## Fuentes

Todo lo citado sale de estos ficheros. No se ha ejecutado ninguna consulta ni
llamada para escribir este documento.

| Fuente | Para qué |
|---|---|
| `azure-apps/sigrid_api.md` | La pasarela: endpoints, guards, listas blancas, límites, secretos, consumidores, despliegue, §2 sobre las dos bases |
| `azure-apps/sigrid_tablas.md` (pág. 247) | Definición de `gra`; `rcg` en la pág. correspondiente |
| `azure-apps/dedicacion.md`, `partes.md`, `remesas.md` | El conflicto documental sobre «réplica» |
| `sigrid-api/config/settings.py` | Que hay un solo host/puerto |
| `sigrid-api/infrastructure/repositories/sql_server_repository.py` | `_connect()`, `run_in_write_transaction()`, `peek_next_ide()`, `read_document()` |
| `sigrid-api/write-lists.json`, `infra/scripts/setup-deploy-write.ps1` | La política de escritura, y que es una App Setting |
| `sigrid-api-v2/README.md` | Estado de la v2 |
| `postventa-incidencias/docs/referencia/03_modelo_posventa_sigrid.md` §4 | Las dos `gra`, los `ide` independientes, la pareja por `cod`, la fila campo a campo, `auxgra` |
| `postventa-incidencias/docs/referencia/01_cierre_incidencia_sigrid.md` | La pantalla de importar gráfico |
| `postventa-incidencias/specs/F-009-cierre-sigrid/design.md` §7.3 | La técnica de reserva de `ide` |
| `postventa-incidencias/services/postventa-api/infrastructure/sigrid/escrituras.py` | Esa técnica, implementada y en producción |
| `postventa-incidencias/progress/explore_grafico_url.md` | §3.2 (reserva de `ide` para este caso) y §4 (qué comprueba «Cerrar parte») |
| `postventa-incidencias/harness/features.json` | F-012 y sus criterios de aceptación |
