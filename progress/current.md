<!-- progress/current.md -->
# Trabajo en curso

## F-011 en `in_progress` (2026-10-18): spec aprobada, implementer lanzado

**Implementer (2026-10-18): T1-T11 y T15 hechas** (informe `progress/impl_F-011.md`, mutación
`progress/mutacion_F-011.md`: 16 mutantes, 0 supervivientes; cobertura 100 % de 16 líneas). `azure-apps` `7bddfd4`
con notas «PENDIENTE DE DESPLIEGUE». **Quedan T12-T14 (MANUAL)** y el reviewer. Confirmado en el código: el albarán clásico (`locate_contract`, l. 191, frente a la lista en
l. 506), `albaran-directo` (`_resolve_obra`, l. 76, frente a l. 299) y el modo extendido de `sigrid/albaran`
(`_comprobar_guardas` solo mira la lista con `commit`, l. 292-306) conectan en dry-run con `request.database` sin lista
blanca. Partes y concepto-gráfico la validan siempre antes de leer.

**Aprobación del humano (2026-10-18):** D1 = `ALLOWED_DATABASES` tal cual; D2 = **A1** (`IdentifierGuard` en `_connect`);
D3 = 400 `BaseNoPermitidaError` listando las bases; D4 = sensible a mayúsculas. Autorizado el paso 5 de la
verificación manual (dry-run de `sigrid/contrato-lineas` con base inyectada, sin `commit`). Título ampliado.

Rama `feature/F-011-documents-read-valida-database`; spec en `specs/F-011-documents-read-valida-database/`, informe y
decisiones D1-D4 en [`spec_F-011.md`](spec_F-011.md). **Hallazgo nuevo, confirmado por el líder:** el hueco no es
solo de `documents/read`: `sigrid/contrato-lineas` conecta en dry-run con `request.database` (`locate_contract`,
`add_contract_lines_use_case.py:38`) y la lista blanca de escritura solo se mira en el paso 6 con `commit` (l. 171);
el albarán clásico y `albaran-directo` siguen el mismo patrón. Solo lo cierra A1 (D2: `IdentifierGuard` en `_connect`).

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
- **Hook `PostToolUse` y mutación** (F-010, `review_F-010_mutacion.md`): el hook de `.claude/settings.json` ejecuta
  pytest tras cada Edit/Write y falseó un superviviente durante una campaña en serie. Propuesta sin aplicar: saltarlo
  mientras exista `.arnes_cache/mutacion_en_curso.json`, `PYTHONDONTWRITEBYTECODE=1` y que la herramienta recompruebe
  cada superviviente antes de declararlo.
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

F-010 cerrada el 2026-10-18 (resumen en `history.md`). F-009 solo espera T24 (con F-053 en real). **F-011**
(`documents/read` valida `database`, D6 de F-010, rigor `critico`) dada de alta en `pending` el 2026-10-18 a
petición del humano. **Spec de F-011 escrita el 2026-10-18** (`specs/F-011-documents-read-valida-database/`,
informe `progress/spec_F-011.md`): espera a que el humano decida D1 (qué lista), D2 (blindar `_connect` para toda
la API, lo que cierra también un hueco nuevo en el dry-run de `sigrid/contrato-lineas`), D3 y D4. Después: F-007 (proformas) y F-008 (facturas de compra),
`pending` con `sdd` y rigor `critico`; F-001 (calentamiento); y la feature propuesta para que `sql/read` fije el tope
real de la consulta. Candidato del arnés: el diagnóstico de la mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-010 está cerrada y desplegada. F-009 está desplegada con la llave
> abierta; solo queda T24 cuando F-053 esté en real. Antes de tocar §2-§4 del contrato con albaranes, avisa a la
> sesión de albaranes. Lo siguiente del backlog (F-011, F-007, F-008, la feature de `sql/read`): no arranques nada
> sin preguntar.
