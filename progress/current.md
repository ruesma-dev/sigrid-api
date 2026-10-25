<!-- progress/current.md -->
# Trabajo en curso

## F-015 en `in_progress` (2026-10-24)

Spec v2 aprobada por el humano (D1-D12; orden contrato → albarán anterior → proveedor en todas las columnas). T0 cerrada:
albaranes acusa la v8.3 el 2026-10-24 ([`t0_F-015_albaranes.md`](t0_F-015_albaranes.md) §Acuse). **Antes de desplegar:
avisar a albaranes** (sv9 y sv4 con los mapeos nuevos van antes o a la vez). Redactados (commit sin código): la
resolución del `usu` que confirma albaranes (contrato §2.1, §2.4.9, H1, §7) y, en design §Limpieza, el filtro por
`synckey LIKE 'ALB-%'` más su lista de `con.ide` en vez de `empide`; sin corregir `empide`. Mientras no se
despliegue, las altas reales siguen copiando columnas de la plantilla (~4 al día); el humano no ha pedido pausarlas.

### Implementación (implementer, 2026-10-24)

- **Terminada la parte del implementer**: T1-T18 y T22 hechas, informe en [`impl_F-015.md`](impl_F-015.md)
  (init.sh en verde, cobertura 100 % de las líneas cambiadas, mutación 104/104 muertos). **Quedan T19-T21
  MANUALES** (despliegue tras avisar a albaranes, dry-runs R29, grabación autorizada, limpieza) y la revisión.
  T8 antes que T7: el caso de uso lanza los códigos nuevos y `AlbaranCompraError` rechaza los que no están en la
  lista cerrada. La parte de caso de uso de T3 (R6, R7) va en T7, que la necesita entera.
- **Decisiones de T9-T18** (detalle en el informe, §Decisiones): E6b justo tras E6 y el `INSERT` de `dcarec` tras
  los de `mov` (R21); E12 de `dcarec` siempre, esperando 0 o 1 (R23); `n_retenciones` solo en las trazas de
  `previsto`/`creado` (R19); L16 como lectura de lista; el `''` de L5 (spec) es el único literal admitido por el
  control negativo; `numerar` rechaza más de una `dcarec` (la campaña midió el `+ n` como código muerto).
- **`azure-apps`** `49dfb36` (local, sin push): `sigrid_api.md` con notas «PENDIENTE DE DESPLIEGUE» que hay que
  quitar al desplegar.
- **Decisión (R5)**: para saber si el efecto escrito es de confirming o transferencia se lee el `auxefp` del `efeide`
  con `read_full_row` (como el `ctr`, el `prv` y el `auxpag`) y se compara su `cod` con `CC`, `CT`, `TR` (M22). Solo
  cuando el banco no tiene fuente y hay `efeide`. La spec dice qué avisar pero no nombra esa lectura; no es SQL
  nuevo. Sin fila de `auxefp`, `ValueError` como con `prv` y `auxpag`.
- **Decisión (R5, R10)**: el aviso y la comprobación de columnas se hacen una vez, tras `conest`/`usu`, con
  `resolver_cascada` (la parte de `construir_dca` que lee filas), fuera de la transacción.
- **Revisión troceada**: pasada 1 en `5da4e85` (seis informes `review_F-015_*.md`; retención y transacción
  aprobadas). Arreglos de la pasada 1 hechos por el implementer (sección «Pasada 2» del informe), uno por commit.
  **Pasada 2: APROBADO** (`review_F-015.md`, `e5eb1f9`). Lo siguiente: merge a `dev`, aviso a albaranes, despliegue
  y T19-T21.
- **Ampliación de R14 ordenada por el líder (pasada 2, retencion O2)**: un `ctrrec` con `valpor` NULL da 400
  `retencion_no_soportada` en vez de un 500 (`InvalidOperation`). R14 no lo listaba; no contradice nada de la spec
  (mismo código, mismo mapeo en sv9). Recogido en el contrato con albaranes §3.3 y en la nota de la v8.3, y en
  `azure-apps/sigrid_api.md` §8.6. R14 lo nombra desde `87abd53`. Se le dice a albaranes en el aviso previo al despliegue.
- **Verificación manual**: comandos literales de T19-T21 (dry-runs V1-V4, grabación V5, limpieza V6) en
  [`verificacion_manual.md`](../specs/F-015-albaran-plantilla-y-retencion/verificacion_manual.md) (anexo de design
  §Verificación manual, aparte por el tope de 250 líneas de design).
- **F-009 que cambian** (T14): lista viva en el informe.
- **Desviación de orden**: T2 antes que T1, porque las filas completas del doble (T1) se construyen con
  `DCA_COLUMNAS` (T2). Y los nombres de las sentencias nuevas en el doble (L17, L16, E6b, `INSERT` y relectura de
  `dcarec`) entran con la tarea que crea cada sentencia (T3, T9, T13): antes no existen.

## F-007 · spec v3 ajustada (2026-10-25), `spec_ready`, pendiente de la PARADA 1

Rama `feature/F-007-registrar-proforma` (con `dev` fusionado: F-015 dentro). Spec v3 en `specs/F-007-registrar-proforma/`
(requisitos 150/150, diseño ~240/250, 24 tareas en lotes A-D) más dos anexos: el **contrato con `proformas`**
([`contrato_proformas.md`](../specs/F-007-registrar-proforma/contrato_proformas.md), borrador v0.1, renombrado con
`git mv` desde `contrato_facturas.md`) y la **plantilla de hoja** para los jefes de obra
([`plantilla_hoja.md`](../specs/F-007-registrar-proforma/plantilla_hoja.md), propuesta). Medición v3 (M27-M40, solo
lecturas; M40 del líder) en [`explore_F-007.md`](explore_F-007.md) §v3; la v2 (a origen) queda como antecedente.

**Qué es la v3:** `POST /api/sigrid/proforma` registra UNA proforma **de mes** del jefe de obra: serie `PROF<aa>/`,
`cla 141`, `docoritip 0`, solo las partidas con MES ≠ 0; las de contrato vinculadas a su `ctrpro` como la vinculada de
F-009 (M28, M30, M40). La llama el microservicio **`proformas` (su F-005)** desde su bandeja: previa antes de aprobar
y grabación al aprobar. `facturas` solo lee lo registrado por `sql/read`, por el `entref` `PROF<MMAA>_<cod_obra>`.
El contrato lo resuelve la API (obra + proveedor y, si hay varios, las líneas: 94,6 % bien, M32) y el llamante lo
cambia con `cod_contrato`. Cabecera y retención de F-015 tal cual. `existente` (por contrato y mes, con sus líneas por
LP6) evita duplicar las ya dadas de alta. Caso de uso: subclase del de F-009 con cinco costuras sin cambio de conducta.

**Ajuste del 2026-10-25 (decisiones del humano, aplicadas):** consumidor `proformas` F-005 (no `facturas` F-063);
`proformas` manda siempre `ctrpro_ide` en las de contrato (la API solo valida que es del contrato resuelto; el embudo
R14 queda de respaldo) y siempre `producto` en las nuevas (sin producto por defecto: `producto_obligatorio`); lista de
productos sin endpoint nuevo (App Setting de `proformas` contenida en la de la API, lectura por `sql/read`); `existente`
con `dcapro.ide`, `linoriide`, producto, cantidad, precio e importe por línea (LP6 nueva, probada en lectura sobre
`AC26/25548`); R24 por contrato, explícito; D3 decidida (`PROF` aunque hoy lo habitual sea `AC`); `usu` = quien aprueba,
`referencia_externa` = `PRF-` + id de `proformas`, previa una por proforma.

**Decisiones que siguen abiertas para el humano** (design §Decisiones):
- **D4 (interpretación del líder, anotada como tal):** «el humano puede cambiar el contrato» = la persona de la
  bandeja de `proformas`, que revisa la previa y reenvía con `cod_contrato`. Confirmar.
- **D5:** hoja de dos contratos (1,7 %) → error con el reparto y una petición por contrato con el mismo `periodo`.
- **D7:** ANTERIOR distinto de Sigrid → aviso, no error. **D8:** exceso sobre contrato → avisos `supera_contrato`
  (> 100 %) y `supera_contrato_10` (> 110 %); frenar la aprobación es de `proformas` y bloquear la factura, de
  `facturas` o F-008.
- **D10:** misma proforma del contrato y mes con el mismo total → `existente`; con otro total, error salvo `otra_del_mes`.
- **D11:** productos sin contrato `SM9999`, `SB9999`, `SM370001` (pendiente de Administración, V8).
- **D13:** contratos que ya van a origen (24,7 %) → aviso `contrato_a_origen`, o bloquear. **D14:** sin contrato
  (15,3 % de las de mes) → dentro solo con `sin_contrato` explícito y CIF, o fuera.
- **Tamaño:** requisitos en el tope (150/150); cualquier añadido obliga a resumir o a partir la feature.

**Preguntas para `proformas`** (design §Preguntas; contrato §7): CIF o nombre del subcontratista; solo partidas con
MES ≠ 0; qué avisos bloquean la aprobación.

**Para el líder:** los cuatro ejemplos de la obra 0719 ya están en Sigrid como `AC` de mes (M29): el dry-run de T21
debe dar `existente` sobre `AC26/25548`, `/29425` y `/25551`. `harness/features.json` sigue con F-015 en
`in_progress` en esta rama aunque está desplegada, y la descripción de F-007 allí no nombra aún a `proformas`: los
actualiza el líder. `azure-apps` no tiene todavía documento de `proformas`; el `entref` que lee `facturas` se declara
allí en T19 (R36).

## F-012 cerrada, desplegada y verificada (2026-10-19)

Resumen en `history.md`; verificación en [`verificacion_F-012.md`](verificacion_F-012.md). Albaranes, confirmado.
Fuera de alcance y sin alta todavía: las trazas `str(exc)` de las demás rutas vuelcan `input` de la petición.

## F-007 con spec v1 en su rama; F-008 espera (2026-10-19)

- **F-007** (`spec_ready` en `feature/F-007-registrar-proforma`, no en `dev`): D1 resuelta por el humano: la llamará
  la app de facturas (su F-063); la proforma puede estar ya en Sigrid o no, y **en el futuro todas se registrarán por
  la app vía la API**. Respuesta de facturas (2026-10-19, detalle en `facturas/progress/explore_alta_sigrid.md`): la
  hoja no trae CIF, fecha, retención ni contrato estructurado; trae MES, ORIGEN y ANTERIOR por partida; pide que el
  endpoint resuelva la cadena a origen. **Spec v2 escrita en su rama** (sección de arriba).
  *Superado el 2026-10-25: el consumidor es `proformas` F-005 (sección de F-007 de arriba).*
- **F-008** (facturas de compra, su F-012): tienen casi todos los datos y enlazan cada línea con su `dcapro.ide` de
  origen; encaja con `explore_F-007.md` §M15. Requisitos de facturas para los dos: dry-run, idempotencia, `con.cod` e
  `ide` en la respuesta, forma de pago y vencimiento por defecto del contrato o `prv`.

## F-011 cerrada, desplegada y verificada (2026-10-18)

Resumen en `history.md`; verificación en [`verificacion_F-011.md`](verificacion_F-011.md). Lo que deja abierto está
en «De configuración y de la base» (dry-run de dominio y el 500 del modo extendido de `sigrid/albaran`).
`azure-apps` `7bddfd4` y `0a0a25f`, locales (no tiene remoto).

## F-009 cerrada, desplegada y verificada (2026-10-07) — llave ABIERTA; queda T24

Resumen en `history.md`. `dev` con el merge `b050109` desplegado en `func-sigridapi-dev-huyke`. Contrato con
albaranes: `specs/F-009-alta-albaran-compra/contrato_albaranes.md` (§2-§4 congelado: F-053 usa `8a6ecab`; avisar a la
sesión de albaranes —hoy `albaranes [6577c2]` en esta máquina— ANTES de tocarlo).

**Hecho:** T19 (App Settings y despliegue), T20-T21 (previas sobre `CTSU16/0206`), T22 (una grabación autorizada,
`AC26/28916`, verificada con lecturas e idempotente; el humano autorizó que el contrato solo cambiara la medición,
`ctrprodes` incluido) y T23 (anulada desde la UI por Administración; comprobado en lectura que no queda nada de
`ALB-prueba-F009-1`). En la misma sesión, Administración dio de baja también los albaranes de prueba de junio de
GARSAN (`AC26/15950`-`15953`, `15980`, `15991`, `16031`): por eso `CTSU16/0206` baja de Σ`canser` 73 a 28 y el stock
del producto 498102 en el almacén 829236 vuelve a sus `mov` de 2019; no es efecto de F-009. **Llave
`SIGRID_ALBARAN_WRITE_ENABLED=true` desde el 2026-10-07**, por orden del humano; albaranes avisado (su llave es
`ALTA_SIGRID_COMMIT` en sv9). `azure-apps` `d066470` (sin push: no tiene remoto).

**Pendiente de confirmar:** respuesta del director de Administración y Control de Costes (correo del 2026-10-07)
sobre si la contabilización de `AC26/28916` salía correcta (sobre todo MA9999 → `0404.CDSB37` con MA99).

**Queda T24** (con F-053 en real, solo lectura): `prepma` de la primera alta real y stock/PMP/`canser` de la primera
devolución real (consultas en `progress/spec_F-009.md` §Manuales).

Guion T19-T24 completo en `history.md` y `progress/spec_F-009.md` §Manuales.

**Riesgos residuales documentados** (`review_F-009_loteC_2.md`): avisos de servido decididos con `canser` leído
fuera de la transacción; reintento ante toda `IntegrityError` («reenvíalo» engañoso, ERP intacto); concurrencia
de estados del contrato como en el clásico. **Para Administración**: la ficha de MA9999 tiene naturaleza `MA1501`.

## F-006 cerrada, desplegada y verificada (2026-09-25)

Resumen en `history.md`; verificación en
[`verificacion_F-006_obra0626.md`](verificacion_F-006_obra0626.md).
`sigrid/partes-reclamacion` queda **abierto** por decisión del humano
(`SIGRID_RECLAMACION_WRITE_ENABLED=true`). Lo que queda:

1. **Anular el parte de prueba `RS26.09/0439`** (obra 0626, UPV
   `0626.03PORTAL 1.1.A`) desde la UI de Sigrid: NO PROCEDE **sin** correo.
   Tras T18 seguía en SAT.
2. Push de `dev` y `main` (el humano). `azure-apps` `7df52e9` y `b3a43c2`,
   locales (no tiene remoto).
3. Dar la function key a `postventa-incidencias` para F-040.

**Menores abiertos (no bloquean):** M2, `[0-9]` acepta superíndices con la
colación CI (0 filas hoy); O2 y O4 van a `postventa-incidencias` F-040; el test
`test_f006_r4_los_prefijos_aceptan_json_y_csv` dice «CSV» pero solo prueba el
constructor: como App Setting, una lista en CSV no arranca la Function (medido;
afecta a todas las listas, ya documentado en `azure-apps/sigrid_api.md` §4).

**Sin trackear en la raíz:** el fichero vacío `` `0`].{t `` (2026-09-24 12:31),
ajeno; lo borra el humano si quiere.

## Lo que espera al humano además de F-006

- Decidir si el adjunto de prueba de F-004 (`cod` `202609060933388219.prueba`,
  reclamación `RS26.08/0123`) se borra desde la UI de Sigrid.
- Dar a Posventa su function key (contrato en `azure-apps/sigrid_api.md` §8.8).
- `azure-apps` no tiene remoto y acumula commits locales; hay un `.env` sin
  trackear allí que no debe commitearse.

## Pendiente de decisión del humano

### Del arnés — valen para cualquier proyecto, así que van a `arnes-base`

- **Diagnosticar `harness/mutacion_paralela.py`.** Dos evidencias ya: en F-003,
  un mutante que muere en 1,9 s salió superviviente; en F-004, 5 supervivientes
  no reproducibles sobre el mismo commit. **Pista concreta** del reviewer
  final: `ResultadoSuite.verde` (`harness/mutacion.py` l. 491) da verde para
  `exit 5` de pytest (ningún test recogido) y `ejecutar` (l. 612) lo traduce a
  SUPERVIVIENTE. Propuesta: `SUPERVIVIENTE` con `sin_tests` → `INDETERMINADO`.
  Sesgo pesimista en las dos features, así que los ceros son sólidos. **Tercera
  evidencia en F-006:** 6 de 42 supervivientes de la ronda 1 murieron al
  reevaluarlos en serie (`mutacion_F-006.md`).
- **Hook `PostToolUse` y mutación**: encargado en `arnes-base` el 2026-10-18 a petición del humano
  (`ENCARGO_pendiente_hook_posttooluse_contamina_la_mutacion.md`, commit `9bdf828`, más la reincidencia F-010 en
  `ENCARGO_pendiente_falsos_supervivientes_con_cache_previa.md`). Propuesta: quitar el hook, una línea en los agentes
  y reconfirmar supervivientes. `sigrid-api` va en el arnés 1.7.8 (base en 1.7.16): actualizar con el instalador cuando
  salga la versión del encargo. Mientras tanto, nada de Edit/Write durante una campaña.
- **`harness/mutacion.py` no genera mutantes** para `not in`, literales de texto ni argumentos con nombre (F-011:
  2 mutantes en 43 líneas; los cubrieron 23 manuales). Para `arnes-base`.
- **C4 y C5 de `CHECKPOINTS.md` chocan** con las tareas MANUAL posteriores al merge (F-010, `review_F-010.md`):
  propuesta «toda tarea `[x]` salvo las MANUAL de despliegue y verificación, que bloquean el `done` pero no el
  APROBADO».
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
- **`sql/read` no aplica `timeout_seconds` como tope de la consulta** (hallazgo del reviewer de
  F-009 T0a-bis, 2026-10-05): `sql_server_repository.py:43` lo pasa a `pyodbc.connect(timeout=…)`,
  que es el tiempo de *login*; los casos de uso de dominio sí fijan `cursor.connection.timeout`.
  Una lectura que el balanceador corta a 230 s **sigue corriendo en el SQL Server de producción**
  (verosímil causa del 1205 y de los 121 s de M14 en T0b). Afecta a todos los consumidores:
  **F-013** en el backlog (fijar `connection.timeout` en `execute_read_query` y actualizar
  `azure-apps/sigrid_api.md`). Mientras tanto, no relanzar una lectura justo después de un corte.
- **`sigrid-api-v2`** tiene el mismo fallo de cabecera que arregló F-010 (`interface_adapters/http/responses.py:62`):
  aviso para ese repositorio, no tarea de este.
- **500 en vez de 400 en el modo extendido de `sigrid/albaran`** (previo, de F-009; hallazgo de
  `review_F-011_C3.md`, reproducido): un error de `model_validator` (p. ej. línea vinculada sin `cod_contrato`) deja
  un `ValueError` en `ctx` de `exc.errors()` y `error_response` falla con `TypeError: Object of type ValueError is not
  JSON serializable` (`function_app.py` l. 261-271). **Cerrado por F-012** (2026-10-19).
- **Dry-run de dominio lee cualquier base que case con el patrón** y a la que llegue `ro_user` (residual de F-011):
  **F-014** en el backlog.
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

**F-015 está `in_progress`** (arriba): implementación y arreglos de la pasada 1 hechos; sigue la **pasada 2 de la
revisión**; después, **avisar a albaranes** (lo hace el líder), el **despliegue** (el humano) y las MANUALES T19-T21
(`specs/F-015-albaran-plantilla-y-retencion/verificacion_manual.md`). Hasta cerrarla no se arranca otra feature (máximo una `in_progress`).

F-009 solo espera T24 (con F-053 en real). Después de F-015: F-007 (proformas) y F-008 (facturas de compra),
`pending` con `sdd` y rigor `critico`; F-001 (calentamiento); F-013 (`sql/read` fija el tope real de la consulta)
y F-014 (el hueco residual del dry-run de dominio). Del arnés:
actualizar `sigrid-api` a la versión de `arnes-base` cuando salga la del encargo del hook, y el diagnóstico de la
mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. **F-015 está `in_progress`** en `feature/F-015-albaran-plantilla-y-retencion`:
> implementada (`impl_F-015.md`) y con los arreglos de la pasada 1 de la revisión hechos; toca la **pasada 2 de la
> revisión** troceada. Después: avisar a albaranes antes de desplegar, el despliegue (lo lanza el humano) y T19-T21
> con los comandos de `verificacion_manual.md` de su spec (dry-runs el líder con autorización; grabación y limpieza el
> humano, con autorización expresa para cada escritura). F-009 está desplegada con la llave abierta; solo queda T24
> cuando F-053 esté en real. F-007 tiene spec v3 en su rama (`spec_ready`), pendiente de la PARADA 1 y de `proformas`. No
> arranques otra feature sin cerrar F-015 ni sin preguntar.
