# progress/explore_ruesma_rep.md

# Exploración · ¿Se puede escribir en la base documental `ruesma_rep`?

| | |
|---|---|
| **Fecha** | 2026-09-03 |
| **Feature** | F-002 (spike de viabilidad) |
| **Alcance ejecutado** | Lecturas por `sql/read`, más **pruebas de permiso por `sql/write` que no dejan ninguna fila** (autorizadas por el humano). **Verificado después que la base quedó intacta**, ver §3.2 |
| **Contexto** | Prerrequisito de `docs/propuestas/2026-09-03_endpoint_adjuntar_documento.md`, que dejaba tres preguntas bloqueantes (Q1, Q2, Q3) |
| **Secretos** | Ninguno. No se recogen aquí host, instancia, credenciales ni claves |

---

## 1 · Resumen

**`ruesma_rep` NO es una réplica de solo lectura.** Es una base normal, en
lectura/escritura, en la misma instancia que `ruesma`, y el ERP le escribe
entre 100 y 250 filas cada día laborable. La premisa de la propuesta queda
**MEDIDA**, no inferida.

Y `user_rw` **ya tiene `SELECT`, `INSERT` y `UPDATE`** sobre su única tabla:
no hace falta ningún `GRANT` ni ningún DBA. Lo único que impide escribir por la
puerta buena es `ALLOWED_WRITE_DATABASES`, una App Setting — y esa política
**ni siquiera está aplicada de verdad**, porque el guardia no mira las bases
que el SQL nombra dentro (§3.4).

## 2 · Q1 — ¿Es escribible, y es la misma instancia? **RESUELTA: sí a las dos**

| Comprobación | Resultado |
|---|---|
| `DATABASEPROPERTYEX('ruesma_rep','Updateability')` | **`READ_WRITE`** |
| `Status` | `ONLINE` |
| `IsInStandBy` | `0` |
| `sys.databases.is_read_only` | `False` |
| `IsPublished` / `IsSubscribed` / `IsMergePublished` | `0` / `0` / `0` — **sin replicación** |
| `IsHadrEnabled` | `0` — sin grupos de disponibilidad |
| `@@SERVERNAME` desde `ruesma` y desde `ruesma_rep` | **el mismo** |
| Propietario de ambas bases | `sa` |
| Fecha de creación | 2024-10-14, con **3 minutos** de diferencia entre una y otra |

Las dos bases se crearon a la vez, en la misma instancia, y ninguna es réplica
de la otra. El sufijo `_rep` es «repositorio», no «réplica». Los documentos de
`azure-apps/dedicacion.md`, `partes.md` y `remesas.md` que la llaman «réplica
que no admite escritura» están **equivocados** y hay que corregirlos.

**Consecuencia de diseño:** una transacción que toque las dos bases desde una
sola conexión es **local**, no distribuida. No hace falta MSDTC.

### 2.1 · Y le escriben todos los días

`dbo.gra` de la documental tenía **359.341 filas** el 2026-09-03, `ide` de 1 a
359.341 sin huecos y **ninguna fila sin binario**. Altas por día laborable en
agosto: entre 94 y 248. El día de la consulta llevaba **127**, la última a las
12:28, con el login de una persona de la casa. Una réplica de solo lectura no
puede recibir eso.

## 3 · Q2 — ¿Puede escribir el usuario de escritura? **RESUELTA: SÍ PUEDE**

> **Resultado, y es el titular de este informe:** `user_rw` **entra en
> `ruesma_rep` y tiene permiso de `INSERT` sobre `dbo.gra`**. No hace falta
> ningún `GRANT`. Lo único que impide escribir en la base documental hoy es
> `ALLOWED_WRITE_DATABASES`, una App Setting.

### 3.1 · Cómo se midió, sin escribir ni una fila

Autorizado por el humano el 2026-09-03 para esta acción concreta. Se enviaron
por `sql/write` (con `database: "ruesma"`, la base permitida) tres sentencias
`INSERT ... SELECT ... WHERE 1 = 0`. Ninguna puede insertar una fila; lo que se
mide es el error del motor, que aparece **al compilar**, antes de ejecutar.

| # | Sentencia | Resultado | Qué prueba |
|---|---|---|---|
| 1 | `INSERT INTO ruesma.dbo.gra (ide) SELECT 0 WHERE 1 = 0` | **HTTP 200**, `affected_rows: 0`, `committed: true` | Control positivo: la técnica funciona y no escribe |
| 2 | `INSERT INTO ruesma_rep.dbo.tabla_que_no_existe_prueba (ide) SELECT 0 WHERE 1 = 0` | **Error 208** — «El nombre de objeto no es válido» | Control de acceso: el error es de **objeto**, no el 916 de «sin acceso a la base». **`user_rw` entra en `ruesma_rep`** y resuelve nombres dentro de ella |
| 3 | `INSERT INTO ruesma_rep.dbo.gra (ide) SELECT 0 WHERE 1 = 0` | **HTTP 200**, `affected_rows: 0`, `committed: true` | **`user_rw` puede insertar en la tabla documental** |

**Control negativo — la técnica sí detecta la falta de permiso.** Sin él, un
`200` podría significar «no se comprobó nada». Se comprobó con una tabla real
de `master`, con el mismo `WHERE 1 = 0`:

```
INSERT INTO master.dbo.spt_monitor (lastrun) SELECT GETDATE() WHERE 1 = 0
  -> 229 · «Se denegó el permiso INSERT en el objeto 'spt_monitor'»
```

El motor comprueba el permiso **aunque no se inserte ninguna fila**. Luego el
`200` del caso 3 significa permiso concedido de verdad, no comprobación
omitida.

La hipótesis (b) de más abajo queda descartada: el usuario existe en la
documental, aunque `ro_user` no pueda verlo en `sys.database_principals` —la
vista está filtrada por permisos, como se advertía.

### 3.2 · Qué permisos tiene exactamente, y el susto

Segunda tanda, para saber si además de `INSERT` tiene lo que hace falta para
reservar el `ide`:

| Sentencia | Resultado | Lectura |
|---|---|---|
| `INSERT INTO ruesma_rep.dbo.gra (ide) SELECT MAX(ide) FROM ruesma_rep.dbo.gra WHERE 1 = 0` | Error **515** — «No se puede insertar el valor NULL en la columna `ide`» | **`SELECT` concedido**: la subconsulta se ejecutó contra la documental. Si faltara el permiso, el error habría sido 229 de `SELECT`, no 515 de restricción |
| `UPDATE ruesma_rep.dbo.gra SET res = res WHERE 1 = 0` | **HTTP 200**, 0 filas | **`UPDATE` también concedido.** Esto no es una buena noticia |

**El susto, y va escrito porque fue un error de método mío.** La primera
sentencia **sí intentó insertar una fila**. `SELECT MAX(ide) … WHERE 1 = 0` es
un agregado sin `GROUP BY`, y eso devuelve **una fila con `NULL`**, no cero
filas: el `WHERE 1 = 0` no protege cuando hay una función de agregación. Lo
que impidió la escritura fue la restricción `NOT NULL` de `ide`, no el diseño
de la prueba. La transacción falló y revirtió.

**Verificado que no quedó nada** (lectura posterior sobre la documental):
`COUNT(*) = MAX(ide) = 359.438`, secuencia contigua sin huecos, **cero filas
sin binario, cero sin `cod`, cero sospechosas**. En negocio, igual. El
incremento desde las 359.341 de la primera medición son altas normales de los
usuarios de Sigrid durante la tarde, al ritmo medido de ~200 al día.

**Regla que se lleva de aquí:** para probar permisos sin escribir, la sentencia
debe ser `SELECT <constantes> WHERE 1 = 0`, **sin agregados**. Con `MIN`, `MAX`,
`COUNT` o `SUM` la fila sale igual.

### 3.3 · `UPDATE` concedido: el riesgo real

`user_rw` puede **modificar** cualquier fila de `ruesma_rep.dbo.gra`. Y ahí
están los **359.438 documentos** de la empresa, con estas circunstancias:

- **`ruesma.gra.ima` está vacío**: el binario de la documental es la **única
  copia**.
- La base está en modelo de recuperación **`SIMPLE`** (medido): sin copias de
  log, la recuperación llega como mucho al último backup completo.
- Y el guardia **no impide** llegar a esa tabla desde `sql/write` (§3.4).

No se probó `DELETE`: `CLAUDE.md` lo prohíbe contra Sigrid sin excepción. Dado
que `INSERT`, `SELECT` y `UPDATE` están concedidos, lo prudente es asumir que
el permiso es amplio —`db_datawriter` o equivalente— hasta que alguien con
acceso al motor lo mire.

### 3.5 · Lo que se sabía antes de la prueba (se conserva por trazabilidad)

Lo medido, y es más raro de lo esperado:

- En **`ruesma_rep`** no hay más usuarios de base que `ro_user` (más los del
  sistema: `dbo`, `guest`, `INFORMATION_SCHEMA`, `sys`).
- En **`ruesma`**, exactamente lo mismo: tampoco aparece un usuario de
  escritura.
- Los únicos logins visibles en la instancia son `ro_user` y `sa`.
- La conexión de lectura es `ro_user`, con rol `db_datareader` en las dos
  bases y `CONNECT` explícito. No es `sysadmin`, ni `db_owner`, ni
  `db_datawriter`.

**Aviso de método:** `sys.database_principals` y `sys.server_principals` están
**filtradas por permisos**. Que `ro_user` no vea el usuario de escritura no
prueba que no exista. Pero sí prueba que, si existe, **no está mapeado de una
forma que `ro_user` pueda ver en ninguna de las dos bases**.

De ahí salen dos hipótesis, y conviene resolverlas antes que nada porque
llevan a sitios opuestos:

| Hipótesis | Qué implicaría |
|---|---|
| **(a)** El login de escritura es `sa`, o cualquier otro `sysadmin` | Sería `dbo` en todas las bases. **Descartada**: la App Setting `SQL_SERVER_WRITE_USERNAME` de la Function App vale `user_rw`, no `sa` |
| **(b)** Es un login propio, mapeado en `ruesma` y sin usuario en `ruesma_rep` | El `INSERT` cruzado fallaría con el error 916. **Descartada por la prueba de §3.1**: el error fue 208, de objeto, no 916 |

Se comprobó además, por `az functionapp config appsettings list`, la
configuración real de la Function App desplegada:
`SQL_SERVER_WRITE_USERNAME = user_rw`, `ALLOWED_WRITE_DATABASES = ["ruesma"]`,
`ALLOWED_WRITE_PREFIXES = ["INSERT","UPDATE","DELETE"]`,
`ALLOWED_DATABASES = ["master","ruesma_rep","ruesma"]` y
`SIGRID_DOMAIN_WRITE_ENABLED = true`.

**Dos avisos que salen de ahí y no son el objeto del spike:**

- `ALLOWED_DATABASES` incluye **`master`**. La lectura de `master` no la
  necesita ningún consumidor conocido; conviene revisar si debe seguir ahí.
- `MAX_ALLOWED_ROWS` desplegado vale **500.000**, no los 1.000 que documenta
  `azure-apps/sigrid_api.md`. Uno de los dos está mal y hay que decidir cuál.

### 3.4 · Y el agujero que esto destapa

El guardia `SqlWriteGuard` valida **el campo `database` de la petición**, no
las bases que el SQL nombra dentro. Por eso la prueba de §3.1 funcionó: basta
con pedir `database: "ruesma"` y escribir `ruesma_rep.dbo.gra` en la sentencia.

Es decir: **la política «`ruesma_rep` no se escribe» no está realmente
aplicada**. Cualquiera con la function key puede escribir en la base
documental hoy, sin tocar configuración. Que la única tabla sea `gra` acota el
daño, pero la lista blanca de bases de escritura no es la barrera que la
documentación dice que es.

Esto es un **hallazgo de seguridad independiente de la feature** y merece
decisión propia: o se cierra (validando en el guardia los identificadores de
base que aparecen en el SQL) o se documenta que la lista blanca solo cubre el
caso accidental, no el deliberado.

## 4 · Q3 — La tabla documental. **RESUELTA**

`ruesma_rep` tiene **una sola tabla: `dbo.gra`**. Nada más. Eso acota mucho el
`GRANT` necesario y el riesgo de abrir la escritura.

Sus 29 columnas son **las mismas** que las de `dbo.gra` en `ruesma`, salvo el
orden de `ori`/`guid`. Lo relevante:

| Columna | Tipo | Observación |
|---|---|---|
| `ide` | `int` NOT NULL | Clave (`gra_indide`, único). Contiguo, sin huecos |
| `cod` | `varchar(128)` | Sello de tiempo + login: `202609031228380648.lgarcia` |
| `emp` | `int` | Empresa |
| `nom` / `nomori` | `varchar(255)` | Nombre del fichero, con su extensión |
| `res` | `varchar(48)` | **Vacío en todas las filas recientes** |
| `ima` | **`image`** | El binario. Tipo *deprecado*, no `varbinary(max)` |
| `gratipide` | `int` | `0` en 352.948 filas, `34` en 6.393 |
| `vin` | `int` | **`3` en todas** las filas |
| `usu` | `varchar(128)` | Login de quien importó |
| `fec` | `int` | `YYYYMMDD` |

**Índices:** `gra_indide` (único, sobre `ide`) y **`gra_empcod` (ÚNICO, sobre
`emp` + `cod`)**. Ese índice único es la idempotencia servida en bandeja: un
`cod` repetido en la misma empresa lo rechaza el motor, no hay que confiar en
una comprobación previa.

**La pareja entre bases va por `cod`, y los `ide` son independientes**: las
mismas cinco últimas filas tenían `ide` 359.341-359.337 en la documental y
298.194-298.190 en negocio, con el mismo `cod`. En negocio, `ima` es **NULL**:
el binario existe solo en la documental.

## 5 · Q6 — Versión del motor. **RESUELTA, y obliga a cambiar la propuesta**

**SQL Server 2012** (`11.0.6020.0`, Standard Edition 64-bit).

Es más antiguo de lo que la propuesta asumía, y tiene dos consecuencias:

1. **`HASHBYTES` no sirve para el binario.** Hasta SQL Server 2016 está
   limitado a 8.000 bytes de entrada; un PDF de 240 KB lo desborda. El
   `sha256` de verificación e idempotencia de la propuesta (§9) **hay que
   calcularlo en Python**, del lado de la API, no en SQL.
2. El binario es `image`, no `varbinary(max)`. Para escribirlo hay que
   comprobar cómo lo maneja `pyodbc` en el `INSERT` (probablemente con un
   `CAST(? AS image)` o dejando que el driver lo envíe como binario largo).

## 6 · Qué queda abierto

| # | Pregunta | Cómo se responde |
|---|---|---|
| Q2 | ¿Puede el login de escritura entrar en la documental? | §3 de este informe: App Setting + `INSERT ... WHERE 1 = 0` |
| Q4 | ¿Significan algo los 4 dígitos finales de `gra.cod`? | Muestra de `cod` del mismo día y mismo usuario |
| Q5 | ¿Usa Sigrid `gra.guid`? | Recuento de `guid` no vacíos |
| Q7 | ¿Escribe Sigrid en `dbo.log` al importar un gráfico? | `dbo.log` filtrado por `tab = 'gra'` |
| — | ¿Cómo enlaza el documento con su concepto? | `dbo.rcg` en la base de **negocio**. No se ha explorado aún |

## 7 · Correcciones que hay que propagar

- **`azure-apps/dedicacion.md`, `partes.md` y `remesas.md`** llaman a
  `ruesma_rep` «réplica que no admite escritura». Es falso: está **MEDIDO**
  que es `READ_WRITE`. Corregirlos, o al menos añadir la nota, es parte del
  trabajo de esta feature según la regla de mantenimiento del ecosistema.
- **`azure-apps/sigrid_api.md` §2** acierta al llamarla «base documental», y
  puede incorporar el dato medido y la lista real de su única tabla.
