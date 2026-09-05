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
