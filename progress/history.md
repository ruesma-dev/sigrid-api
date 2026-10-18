<!-- progress/history.md -->
# Histórico del arnés

Registro append-only. El líder mueve aquí el resumen de cada feature terminada.

---

## F-002 · Spike: viabilidad de escribir en la base documental `ruesma_rep`

**Cerrada el 2026-09-03.** Rigor `critico`. Sin rama de feature: se ejecutó
como exploración de solo lectura durante la instalación del arnés, a petición
directa del humano.

**Pregunta:** ¿se puede escribir en `ruesma_rep`, y con qué garantías?

**Respuesta: sí, y sin ningún trámite previo.**

- `ruesma_rep` es `READ_WRITE`, `ONLINE`, **sin replicación** ni grupos de
  disponibilidad, en la **misma instancia** que `ruesma` y creada tres minutos
  después que ella. No es una réplica: el sufijo `_rep` es «repositorio».
- El ERP le escribe **entre 94 y 248 filas por día laborable**. Una réplica de
  solo lectura no puede recibir eso.
- **`user_rw` ya tiene permiso de `INSERT`** sobre su única tabla, `dbo.gra`.
  No hace falta `CREATE USER` ni `GRANT`.
- Tiene **una sola tabla**, con índice único por `(emp, cod)` —idempotencia
  gratis— y el binario en columna `image`.
- El motor es **SQL Server 2012**: `HASHBYTES` no admite un PDF completo, así
  que el `sha256` va calculado en Python.

**Método:** solo lecturas por `sql/read`, más tres `INSERT ... SELECT ...
WHERE 1 = 0` por `sql/write` (autorizados expresamente por el humano) que no
pueden insertar ninguna fila. Con control negativo: el mismo patrón contra
`master.dbo.spt_monitor` devuelve `229 · permiso INSERT denegado`, lo que
demuestra que el motor comprueba permisos aunque no inserte. **Ninguna fila
escrita en Sigrid.**

**Hallazgo colateral, y es el que más importa:** `SqlWriteGuard` valida el
campo `database` de la petición pero **no las bases nombradas dentro del SQL**.
La política «`ruesma_rep` no se escribe» no está aplicada de verdad. De ahí
sale **F-003**, que va antes que el endpoint.

**Informe:** [`progress/explore_ruesma_rep.md`](explore_ruesma_rep.md).
**Consecuencia:** F-003 (cerrar el guardia) y F-004 (endpoint de dominio),
decidido por el humano el 2026-09-03 frente a la alternativa de abrir
`ALLOWED_WRITE_DATABASES`.

---

---

## F-003 · El guardia valida también las bases nombradas dentro del SQL

**Cerrada el 2026-09-05.** Rigor `critico`. Rama
`feature/F-003-guardia-bases-cruzadas`, 22 commits sobre `dev`.
**Pendiente de merge a `dev`, que lo hace el humano.**

**El agujero:** `SqlWriteGuard` y `SqlQueryGuard` validaban el campo
`database` de la petición, que es la base de la **conexión**. Como en SQL
Server una sentencia salta a otra base de la misma instancia con solo
cualificar el nombre, con `database: "ruesma"` se podía escribir en
`ruesma_rep`: la política que `ALLOWED_WRITE_DATABASES` decía aplicar **no
estaba aplicada**. Medido el 2026-09-03, no supuesto.

**La solución:** `infrastructure/security/database_reference_guard.py`, un
reconocedor de nombres cualificados —no un analizador de T-SQL—. Tres o más
partes se validan contra la lista blanca; cuatro o más se rechazan siempre.
**Sin variable de entorno para desactivarlo**, a propósito: un interruptor de
seguridad configurable acaba apagado.

**Evidencias:** suite 1.262 pasan / 1 skip; cobertura 99,2 % (254/256) de las
líneas cambiadas; `ruff` con los mismos 79 avisos de deuda previa; verificador
del ecosistema con **0 rechazos** sobre 13.639 ficheros y 256 consumidores
—que es como se demostró la condición dura del humano, «nada de lo que hoy
funciona puede empezar a fallar»—; mutación con 7 supervivientes, todos
equivalentes aceptados. Detalle en `impl_F-003.md`, `mutacion_F-003.md`,
`mutacion_F-003_remuestreo.md` y los seis informes `review_F-003*`.

**Seis fallos encontrados en cuatro rondas de revisión**, tres de ellos
agujeros que dejaban pasar. **Cinco eran la misma causa:** el neutralizador y
el reconocedor leían los identificadores delimitados con reglas distintas, y
cada vez que difieren —un apóstrofo, un escape `]]`, un `--`, un salto de
línea— una referencia puede esconderse dentro de un falso identificador. Se
parchearon caso a caso durante tres rondas hasta unificarlos, y **esa
unificación debió ser el primer arreglo**. Si aparece un séptimo de la misma
familia, no se parchea: se reemplaza el reconocedor por un tokenizador propio
que recorra la sentencia una vez y clasifique cada tramo.

**Lección de método, que costó dos aceptaciones:** los supervivientes de
mutación se analizan **midiendo** —aplicando el mutante y ejecutando— y nunca
leyendo. Una aceptación de 13 quedó anulada porque cuatro análisis leídos eran
falsos. En esta sesión, dos supervivientes «nuevos» resultaron mal
clasificados por la propia campaña: uno se cuelga y otro muere en 1,9 s.

**Lo que se descubrió de la herramienta:** la campaña paralela clasifica mal
en algún caso. Se reevaluaron **en serie los 138 mutantes**, los 123 muertos
incluidos: **0 falsos muertos**. Su sesgo es pesimista —inventa supervivientes,
no los esconde—, así que ninguna línea del guardia queda dada por cubierta sin
estarlo. El diagnóstico de `harness/mutacion_paralela.py` queda como trabajo
aparte, para portar a `arnes-base`.

**T8, la verificación manual contra la API desplegada, hecha el 2026-09-05**
tras desplegar `dev`: salida del script de `albaranes-persistencia` idéntica
byte a byte antes y después, y el guardia rechazando con 400 lo que antes se
colaba. Detalle en `current.md` de esa sesión.

---

## F-004 · Endpoint de dominio `POST /api/sigrid/concepto-grafico`

**Cerrada el 2026-09-06.** Rigor `critico`. Rama
`feature/F-004-endpoint-concepto-grafico`. **Pendiente de merge a `dev`** (lo
hace el humano) y de las verificaciones manuales T18-T21 contra producción.

**Qué hace:** adjunta un documento a un concepto de Sigrid escribiendo tres
filas en UNA transacción local: el binario en `ruesma_rep.dbo.gra`, los
metadatos en `ruesma.dbo.gra` con **el mismo `cod` y `emp`**, y el enlace en
`ruesma.dbo.rcg`. Dry-run por defecto; `commit:true` exige dos App Settings
abiertas. Idempotencia por contenido (`sha256` en Python, motor SQL Server
2012) apoyada en el índice único `(emp, cod)`. `ALLOWED_WRITE_DATABASES` no
cambia y ningún guardia se toca: el SQL constante del endpoint se autovalida
con el `DatabaseReferenceGuard` de F-003. Vale para cualquier tipo de concepto
(reclamación, contrato, albarán): lo decide la lista blanca
`SIGRID_DOCUMENT_ALLOWED_CONTIP`.

**La regla de gobierno cambió, con aprobación del humano:** «`ruesma_rep` no
se escribe» pasa a «se escribe solo por `sigrid/concepto-grafico`, nunca por
`sql/write`», en `CLAUDE.md`, `CHECKPOINTS.md` y `docs/ARCHITECTURE.md`.

**Lo medido antes de escribir la spec, y que la cambió:** la relación entre
las dos `gra` es **solo por `(emp, cod)`**, nunca por `ide` (índice único
`gra_empcod` en las dos bases; los `ide` solo coinciden en 426 filas de 2009;
`dog.codrep` lo confirma); `vin=3` es «binario en el repositorio»; la fila
documental lleva siempre `gratipide=0` y `res=''`; ninguna columna tiene
`DEFAULT`, así que las 29 de `gra` y las 7 de `rcg` van explícitas. Informes:
`explore_F-004_mediciones.md`, `explore_F-004_relacion_gra.md`.

**Evidencias (`79c5520`):** 1.480 tests, 1 skip; cobertura 100 % (465/465);
mutación **167/167 muertos, 0 supervivientes** tras cerrar con 16 tests los
36 de la primera campaña (los 36 remedidos en serie, ninguno equivalente);
revisión en cuatro encargos, todos APROBADO (`review_F-004*.md`).

**Hallazgo colateral:** el script `diagnose_sigrid_contrato_docs.py` de
albaranes cruzaba por `ide` y devolvía documentos ajenos; corregido en el
monorepo `albaranes` (`dev`, `febce08`). La T8 de F-003 valía como
no-regresión, no como diagnóstico.

**Del arnés:** la campaña paralela produce falsos supervivientes de forma no
reproducible; pista concreta: `ResultadoSuite.verde` cuenta el `exit 5` de
pytest como suite verde. Sesgo pesimista; diagnóstico como trabajo aparte.

---

## F-005 · `concepto-grafico` admite documentos sin clase de gráfico

**Cerrada el 2026-09-06.** Rigor `critico`, `sdd: false`. Rama
`feature/F-005-grafico-sin-clase`. Pendiente de merge, despliegue y de la
prueba manual en la obra 0404 (guion en `current.md`).

**Por qué:** Sigrid adjunta los documentos de contratos (`con.tip` 44) y de
albaranes de compra (`tip` 14, tabla `dca`) **sin clase de gráfico**
(`gratipide=0` en el 99,98 % y el 100 % de los casos, medido), con las mismas
constantes que el endpoint ya escribe. F-004 exigía una clase de `auxgra`, así
que rechazaba el 0. El humano eligió admitirlo (opción 2) frente a usar la
clase 40 «DOCUMENTOS GENERALES».

**Qué cambia (7 líneas, 3 ficheros):** el guardia acepta `gratipide=0`
**solo si `0` está en `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`**, sin exigir
`auxgra` ni `fecbaj`; el caso de uso no lee `auxgra` en ese caso; el modelo
baja el suelo a 0. Nada más se relaja: ni otros guardias, ni el repositorio,
ni `ALLOWED_WRITE_DATABASES`, ni el constructor de sentencias. Sin tocar
configuración, el comportamiento es el de F-004.

**Evidencias (`cfb8048`):** 1.502 tests; cobertura 100 % (7/7); mutación
**6/6 muertos**, tras eliminar un literal que la campaña demostró muerto
(cerrado midiendo con un canario y su control negativo, no aceptando un
equivalente); dos revisiones APROBADO (`review_F-005.md`,
`review_F-005_papeleo.md`), con 3 de 6 mutantes reproducidos y el alcance
recalculado.

**Lección:** cuando un superviviente resulta código muerto, se quita el
código, no se pide aceptar el equivalente.

## F-006 · Alta en lote de partes de reclamación de Posventa

**Cerrada el 2026-09-25.** Rigor `critico`, `sdd: true`. Rama
`feature/F-006-alta-parte-reclamacion`, mergeada en `dev` (`9e552b0`),
**desplegada y verificada en producción el mismo día**: dry-run del lote de
prueba, escritura real autorizada del parte `RS26.09/0439` (obra 0626, UPV
`0626.03PORTAL 1.1.A`), ficha comprobada por el humano en Sigrid y repetición
idempotente ([`verificacion_F-006_obra0626.md`](verificacion_F-006_obra0626.md)).
Por decisión del humano, `SIGRID_RECLAMACION_WRITE_ENABLED` queda **abierta**.

**Por qué:** `postventa-incidencias` (F-040) vuelca en Sigrid las incidencias
aprobadas en su bandeja y la pasarela no sabía crear un parte. Referencia
principal: el Word interno de Posventa (`docs/referencia/postventa_pasos_crear_parte.md`),
con el manual de Sigrid como apoyo.

**Qué hace:** `POST /api/sigrid/partes-reclamacion`, lote de hasta 50 partes de
una obra, **una transacción por parte** y respuesta parte a parte; escribe `con`,
`rcp`, `rcpint`, `conext` (`RCPCLI`) y `log` como el escritorio de Sigrid
(medido en producción, `explore_F-006_modelo_parte.md`); código `RS<aa>.<mm>/NNNN`
e `ide` reservados **dentro** de la transacción bajo applock, con reintento si
choca con un alta simultánea de la UI (índice único `emp, tip, cod`); idempotencia
por referencia externa con prefijo `PVI-`; tipo `0002` y forma «Escrita» por
defecto; nace en SAT y no pasa a PTE. Dry-run por defecto e interruptor propio
`SIGRID_RECLAMACION_WRITE_ENABLED` apagado. Decisiones del humano del 2026-09-24
en `requirements.md`. F-007 (proformas) y F-008 (facturas de compra) quedan
anotadas en el backlog.

**Evidencias (`98db7ef`):** 1.733 tests (231 de F-006); cobertura 100 % de 560
líneas; mutación 217/217 sobre `22e23f7` (la ronda 1 dejó 42: 6 falsos del modo
paralelo y 36 reales, cerrados) y 8/8 manuales en el arreglo M1. Revisión troceada
en cinco parciales y tres pasadas (`review_F-006*.md`), APROBADO. `azure-apps`
`7df52e9` (sin push).

**Lecciones:** trocear la revisión volvió a funcionar y cazó un error real del
guion manual: T17 apagaba `SIGRID_DOMAIN_WRITE_ENABLED`, de la que dependen los
demás endpoints de dominio. Los guiones MANUAL se revisan contra el estado
desplegado (`azure-apps`), no solo contra la spec. Una ruta nueva no debe copiar
`str(ValidationError)` al log: lleva los valores de entrada.

---

## F-009 · Modo extendido de `sigrid/albaran`: alta de albaranes de compra desde albaranes (PRE-1 de F-053)

**Cerrada el 2026-10-07, sin desplegar.** Rigor `critico`, `sdd`. Rama `feature/F-009-alta-albaran-compra`, mergeada a
`dev` con `--no-ff`. Spec v8.2 (`specs/F-009-alta-albaran-compra/`); historia de versiones en `progress/spec_F-009.md`.

**Por qué:** albaranes (F-053) tiene que dar de alta en Sigrid los albaranes de compra aprobados, con líneas que la
pasarela no sabía escribir: sin contrato, sin partida, devoluciones, producto y cuenta analítica. El contrato con
albaranes lo escribió primero su agente (33 huecos, `contrato_albaranes.md`) y es de sigrid-api: albaranes solo lo
toca para actualizar consumos (regla del humano).

**Qué hace:** `POST /api/sigrid/albaran` decide el modo por las claves del JSON (`lineas`/`referencia_externa` ⇒
extendido; mezcla ⇒ `peticion_mixta`); el clásico y `albaran-directo` siguen idénticos (test de caracterización con
dorado escrito antes del código). Un albarán por petición en UNA transacción: `con` (emp de la obra, `cod` y `ide`
reservados bajo applock, `est` 1), `dca` (plantilla del último albarán del mismo proveedor y empresa, `synckey` =
`ALB-…`), `dcapro` vinculadas (consumen medición: `ctrprodes`, `canser`, estados del contrato; `caaide`, `cod2`,
`dncide`/`dncproide` del `ctrpro`) y sin vincular (MA9999/QA9999/XA9999 elegido por albaranes; naturaleza del mapeo
MA99/QA99/XA99, nunca del maestro; analítica `<obra>.<caagascod sin MOD.>`; cuenta del `cuacomcod`; IVA de la última
línea del mismo proveedor), partida o sin partida («almacén»), `mov` si y solo si `pro.tipmov` = 1 con `prepma` = PMP
del almacén antes de la entrada, devoluciones (regla A), `log` de alta; idempotencia por `synckey`; errores con código,
también por línea; dry-run por defecto y segunda llave `SIGRID_ALBARAN_WRITE_ENABLED` (cierra también el clásico y
`albaran-directo`). Seis App Settings nuevas, defecto cerrado, solo en JSON.

**Mediciones (T0, solo lectura, cinco pasadas):** M1-M19 sobre producción decidieron cada regla (plantilla, estados,
partidas imputables, analítica, cuenta, `tipmov`, `prepma`, anulación que borra, `refent` libre, `cod2`…); las cifras en
`spec_F-009.md` §v5-§v8.1. Dos hipótesis refutadas midiendo (analítica de la partida o del almacén; media ponderada
global del producto). Consultas a negocio (director de Administración y Control de Costes) sobre `cod2`, planificación
de compras y naturalezas.

**Evidencias:** 2.370 tests; cobertura 100 % de 1.103 líneas cambiadas; mutación `critico` 481/479 sobre `8a85804`
(4 workers; la campaña previa dejó 76, **todos confirmados en serie**: 60 muertos con tests nuevos y 14 eran código
muerto, quitado), 2 equivalentes **aceptados por el humano**. Cinco lotes (A-E) con revisión troceada por lote,
APROBADO (`review_F-009*.md`). `azure-apps` `51b29a6` (sin push: no tiene remoto).

**Lecciones:**
- Medir antes de escribir reglas: la analítica, la naturaleza y el `prepma` salieron distintos de lo que parecía, y
  el maestro de MA9999 tiene la naturaleza mal (MA1501, «cerámico»).
- Las lecturas pesadas de T0 cortadas por el balanceador **siguen vivas en el servidor** (`sql/read` no fija el tope
  de la consulta): causa probable de un interbloqueo en producción. Feature propia pendiente.
- Comparar campos «Real» de Sigrid con tolerancia, nunca `== 0` (residuo binario ⇒ PMP absurdo).
- Un test que construye `Settings` (o que valida modelos que la leen) debe aislar el entorno: la campaña exporta el
  `.env` (otra vez, `92bf606`).
- Coordinación entre sesiones: el consumidor congela su referencia del contrato y el dueño avisa antes de tocar
  §2-§4.

**Queda (guion en `current.md`):** despliegue y verificación manual T19-T24 (una grabación autorizada).

---

## F-010 · `documents/read`: nombres no ASCII sin 500 y localización sin ambigüedad

**Cerrada el 2026-10-18.** Rigor `critico`. Rama `feature/F-010-documents-read-nombres-y-clave`. Propuesta de
datamart-seg-anual (F-139) y mcp-bbdd (F-023), verificada por el líder con lecturas antes de la spec.

- **El 500:** `X-Document-Filename` iba sin codificar y el host de Functions rechaza las cabeceras no ASCII (500 con
  cuerpo vacío; ~5,7 % de los adjuntos de compras, medido por datamart). Ahora va con codificación porcentual UTF-8
  de lo no ASCII, los controles y el `%`; un nombre ASCII sin `%` sale idéntico. `Content-Disposition` con
  `quote(safe="")`.
- **La ambigüedad:** `SELECT TOP (1) WHERE [id_column] = ?` servía una fila cualquiera si la columna no era única.
  Ahora `TOP (2)` y **409 `DocumentoAmbiguoError`** para toda petición, y campo opcional `key` (1-4 columnas,
  nombres por `IdentifierGuard`, valores con `?`, AND), excluyente con `id_column`/`id_value`, que siguen igual y
  con los mismos textos de error. En `gra` los únicos índices únicos son `ide` (PK) y `(emp, cod)`.
- **Decisiones del humano:** D1-D5 y D7 de `spec_F-010.md` tal cual. **D6** (no se valida `database`, que además se
  interpola en la cadena de conexión) fuera: es **F-011**.
- **Verificación:** `init.sh` 2530 passed/1 skipped; cobertura 100 % de 80 líneas cambiadas; mutación en serie 24/24
  muertos (`mutacion_F-010.md`). Revisión troceada: H1 (texto de error de `id_column`) y H2-H4 (papeleo), cerrados.
  Desplegada el 2026-10-18 desde `dev` `fc2079a`; T15 en solo lectura: 365617 por `nomori` 200, mismo fichero por
  `key`, 409 por `emp`, cabeceras ASCII idénticas (`verificacion_F-010.md`).
- **Ecosistema:** `azure-apps` `0c4cbeb` y `bdc8ec0` (§8.3). Avisadas albaranes (antes del despliegue; lee la
  cabecera: decodificar con `unquote`), mcp-bbdd y datamart. `sigrid-api-v2` tiene el mismo fallo: aviso.
- **Lección del arnés:** el hook `PostToolUse` puede falsear la mutación en serie (propuesta en `current.md`).

---

## F-011 · `documents/read` valida `database` y `_connect` valida el nombre de base para toda la API

**Cerrada el 2026-10-18.** Rigor `critico`. Rama `feature/F-011-documents-read-valida-database`. Nace del D6 de F-010.

- **El hueco:** `documents/read` no validaba `database` contra ninguna lista y `_connect` la interpolaba sin escapar
  en `DATABASE=…;` de la cadena ODBC. La spec halló que el dry-run de `contrato-lineas`, el albarán clásico,
  `albaran-directo` y el modo extendido de `sigrid/albaran` también conectan con la base de la petición sin lista
  blanca (solo se mira con `commit`).
- **Decisiones del humano:** D1 `ALLOWED_DATABASES` tal cual; D2 **A1** (`IdentifierGuard` en `_connect`, para toda la
  API, sin tocar `infrastructure/security/`); D3 400 `BaseNoPermitidaError` listando las bases; D4 sensible a
  mayúsculas. Autorizó el dry-run del paso 5 de T14.
- **Verificación:** `init.sh` 2664 passed/1 skipped; cobertura 100 % de 16 líneas; mutación 0 supervivientes (la
  herramienta solo generó 2; 23 manuales en la revisión). Revisión troceada en cinco bloques más la final: solo H1
  (`current.md` desfasado), cerrado. T12 (App Settings casan con el patrón), T13 desde `dev` `93710c4` y T14 en
  verde (`verificacion_F-011.md`).
- **Ecosistema:** `azure-apps` `7bddfd4` y `0a0a25f`. Avisados mcp, datamart, albaranes, postventa y facturas: ninguno
  cambia nada. Postventa retrasó su primera escritura de F-059 hasta T14 para no coincidir con el reinicio.
- **Queda fuera** (en `current.md`): el dry-run de dominio lee cualquier base válida a la que llegue `ro_user`; el 500
  del modo extendido de `sigrid/albaran` ante errores de `model_validator` (previo, de F-009).
- **Lecciones del arnés:** encargado en `arnes-base` quitar el hook `PostToolUse` (`9bdf828`); `harness/mutacion.py`
  apenas genera mutantes para este código (sin `not in`, literales ni argumentos con nombre). Un error del líder en
  un aviso (la base de `concepto-grafico`) lo cazó el consumidor: los avisos se contrastan con §8 antes de mandarlos.
