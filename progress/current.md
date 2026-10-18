<!-- progress/current.md -->
# Trabajo en curso

## F-011 en `in_progress` (2026-10-18): revisión aprobada por bloques; faltan revisión final, merge, T13 y T14

Rama `feature/F-011-documents-read-valida-database`. Spec aprobada por el humano el 2026-10-18: D1 = `ALLOWED_DATABASES`
tal cual; D2 = **A1** (`IdentifierGuard` en `_connect`, para toda la API); D3 = 400 `BaseNoPermitidaError` listando las
bases; D4 = sensible a mayúsculas. Título ampliado. Autorizado el paso 5 de la verificación manual.

- **Implementer:** T1-T11 y T15 hechas (`impl_F-011.md`; mutación `mutacion_F-011.md`). `azure-apps` `7bddfd4` (sin
  push: no tiene remoto) con notas «PENDIENTE DE DESPLIEGUE».
- **Revisión por bloques sobre `4d1c266`:** C3 (`review_F-011_C3.md`), C4 (`review_F-011_C4.md`), ROJO y cobertura
  (`review_F-011_rojo.md`) y mutación (`review_F-011_mutacion.md`, 23 manuales + campaña, 0 supervivientes):
  APROBADO. C1/C2/C5 (`review_F-011_C1C2C5.md`): CHANGES_REQUESTED solo por H1, este fichero desfasado;
  corregido por el líder. Guía de T14 ajustada con las observaciones 1-4 de `review_F-011_C4.md`.
- **T12 hecha** (líder, solo lectura, 2026-10-18): `ALLOWED_DATABASES` = `master`, `ruesma_rep`, `ruesma`;
  `ALLOWED_WRITE_DATABASES` = `ruesma`; `SIGRID_DOCUMENT_WRITE_DATABASE` = `ruesma_rep`. Todas casan con el patrón
  (`verificacion_F-011.md`).
- **Lo que queda, en orden** (T13 y T14 bloquean el `done`, no el merge, como en F-010):
  1. Revisión final consolidada → `review_F-011.md`.
  2. Merge `--no-ff` a `dev` (líder) y push (humano: `! git -C C:/Users/pgris/PycharmProjects/sigrid-api push origin dev`).
  3. **T13 (humano):** `! func azure functionapp publish func-sigridapi-dev-huyke --python`. Sin App Settings nuevas.
  4. **T14 (líder, lecturas + el dry-run autorizado):** pasos 1-5 de design §Verificación manual, con un script
     Python en el scratchpad que lee la function key del `.env` (nada al repo): `ruesma_rep` → 200 y 17865 bytes;
     `base_inexistente_f011` → 400 `BaseNoPermitidaError` (si no, PARAR); `ruesma_rep;APP=f011` y `RUESMA_REP` →
     400 `BaseNoPermitidaError`; `sql/read` sobre `ruesma_rep` y `ruesma` → 200; dry-run de `sigrid/contrato-lineas`
     con `database:"ruesma;APP=f011"` → 400 `IdentifierValidationError`. Resultados en `verificacion_F-011.md`;
     después quitar las notas «PENDIENTE DE DESPLIEGUE» de `azure-apps/sigrid_api.md` y pasar a `done`.
- **Confirmado en el código:** `sigrid/contrato-lineas` (l. 38 frente a 171), el albarán clásico (l. 191 frente a
  506), `albaran-directo` (l. 76 frente a 299) y el modo extendido de `sigrid/albaran` (l. 292-306) conectan en
  dry-run con `request.database` sin lista blanca. Con A1 rechazan una base fuera del patrón. **Hueco residual**
  (feature propia): en esos dry-run se puede leer una base que case con el patrón y a la que llegue `ro_user`.

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
  y reconfirmar supervivientes. `sigrid-api` va en el arnés 1.7.8 (base en 1.7.16): actualizar con el instalador tras
  F-011. Mientras tanto, nada de Edit/Write durante una campaña.
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
  feature propia (fijar `connection.timeout` en `execute_read_query` y actualizar
  `azure-apps/sigrid_api.md`). Mientras tanto, no relanzar una lectura justo después de un corte.
- **`sigrid-api-v2`** tiene el mismo fallo de cabecera que arregló F-010 (`interface_adapters/http/responses.py:62`):
  aviso para ese repositorio, no tarea de este.
- **500 en vez de 400 en el modo extendido de `sigrid/albaran`** (previo, de F-009; hallazgo de
  `review_F-011_C3.md`, reproducido): un error de `model_validator` (p. ej. línea vinculada sin `cod_contrato`) deja
  un `ValueError` en `ctx` de `exc.errors()` y `error_response` falla con `TypeError: Object of type ValueError is not
  JSON serializable` (`function_app.py` l. 261-271). Feature propia (`exc.errors(include_context=False)` o
  equivalente, y mirar las demás rutas). Afecta a albaranes: recibe un 500 mudo.
- **Dry-run de dominio lee cualquier base que case con el patrón** y a la que llegue `ro_user` (residual de F-011).
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

F-010 cerrada el 2026-10-18 (resumen en `history.md`). F-009 solo espera T24 (con F-053 en real). **F-011 en
`in_progress`**: revisión aprobada por bloques, faltan revisión final, merge, T13 y T14 (arriba). Después: F-007
(proformas) y F-008 (facturas de compra), `pending` con `sdd` y rigor `critico`; F-001 (calentamiento); la feature
propuesta para que `sql/read` fije el tope real de la consulta; y, como candidatas nuevas, el 500 del modo extendido
de `sigrid/albaran` y el hueco residual del dry-run de dominio. Candidato del arnés: el diagnóstico de la mutación
paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-011 está `in_progress`: revisión por bloques aprobada; faltan la
> revisión final, el merge a `dev`, el despliegue (T13, lo lanza el humano) y T14 (guion arriba). F-010 está cerrada
> y desplegada. F-009 está desplegada con la llave abierta; solo queda T24 cuando F-053 esté en real. Antes de tocar
> §2-§4 del contrato con albaranes, avisa a la sesión de albaranes. Lo siguiente del backlog (F-007, F-008, la
> feature de `sql/read`): no arranques nada sin preguntar.
