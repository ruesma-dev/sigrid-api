<!-- progress/current.md -->
# Trabajo en curso

## F-009 cerrada (2026-10-07), `done`, **sin desplegar** — guion T19-T24

Resumen en `history.md`. Mergeada a `dev` con `--no-ff` (local; el push lo hace el humano). Spec v8.2;
contrato con albaranes en `specs/F-009-alta-albaran-compra/contrato_albaranes.md` (§2-§4 congelado: F-053 usa
`8a6ecab`; avisar a la sesión de albaranes ANTES de tocarlo). Mutación: 2 equivalentes aceptados por el humano.

**Avance (2026-10-07):** **T19 hecha**: App Settings aplicadas (llave `false`) y `func publish` desde `dev`
(`b050109`, push hecho). **T20 y T21 hechas** sobre `CTSU16/0206`: el dry-run clásico sale igual que antes; el
extendido (vinculada sin partida, MA9999 con partida, devolución vinculada y QA9999 sin partida) trae producto,
naturaleza (MA99, QA99), analítica (`0404.CDSB37`, `0404.CDQA12`), cuenta y `prepma` correctos. **T22 hecha**, con
autorización del humano limitada a que el contrato solo cambie la medición (sin añadir ni borrar líneas;
`ctrprodes` incluido): llave abierta solo para la prueba y cerrada justo después. Albarán **`AC26/28916`** (`con.ide`
2850080, `synckey` `ALB-prueba-F009-1`, usuario `prueba`), la repetición responde `idempotente`. Lecturas tras la
grabación: 4 `dcapro`, 4 `mov` con `prepma` = `almpma` del `mov` anterior del par en los 4, 2 `ctrprodes`
(+1/−1), `canser` 258688 6→7 y 258687 1→0, contrato con 17 líneas y Σ`can` 84 sin cambios, estados 0/0 y `log`
de alta. Correo al director de Administración y Control de Costes para revisar la contabilización.
**Siguiente:** T23 (anular `AC26/28916` desde la UI) **después** de su respuesta; luego, la comprobación en
lectura de que el `con` ya no existe y de que el stock y `canser` vuelven a su valor.

**Guion de verificación manual** (cada paso con el humano; escrituras solo con su autorización expresa y concreta):

1. **T19 · Despliegue** desde `dev` tras el push. App Settings por fichero JSON (`--settings "@fichero.json"`,
   listas y mapeo solo en JSON, cargadas antes con `Settings` como variable de entorno):
   `SIGRID_ALBARAN_WRITE_ENABLED=false`, `SIGRID_ALBARAN_PREFIJOS_REFERENCIA=["ALB-"]`,
   `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO=["MA9999","QA9999","XA9999"]`, `SIGRID_ALBARAN_EMPRESAS_OBRA=[1]`,
   `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO={"MA9999":"MA99","QA9999":"QA99","XA9999":"XA99"}` y el tope de líneas
   por defecto. `func azure functionapp publish func-sigridapi-dev-huyke --python` lo lanza el humano con `!`.
   Tras T19, albaranes ya puede probar la **previa** (`commit=false`) contra el servicio real.
2. **T20** · dry-run clásico de siempre sobre `CTSU16/0206` (obra 0404): igual que antes salvo `cod`/`ide`.
3. **T21** · dry-run extendido sobre `CTSU16/0206`: una vinculada, una MA9999 con partida (naturaleza `MA99`,
   `caa` `0404.CDSB37`), una QA9999 sin partida y una negativa; revisar `filas` y `avisos` con el humano.
4. **T22** · **una** grabación (`commit:true`) autorizada, con la llave abierta solo para la prueba y usuario
   `prueba`; revisión en la UI (líneas, partidas, naturaleza, analítica, cuenta, `cod2` y planificación de la
   vinculada, stock, PMP y **`prepma` frente a un albarán del escritorio del mismo día y almacén**, medición del
   contrato) y repetición `idempotente`. Volver a cerrar la llave.
5. **T23** · anular el albarán de prueba desde la UI (nunca `DELETE`); comprobar en lectura que el `con` ya no existe.
6. **T24** · con F-053 en real: `prepma` de la primera alta real y stock/PMP/`canser` de la primera devolución real
   (consultas en `progress/spec_F-009.md` §Manuales).

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

Primero, el despliegue y la verificación de F-009 (guion de arriba). Después,
F-007 (proformas) y F-008 (facturas de compra), `pending` con `sdd` y rigor
`critico`; F-001 (calentamiento); y la feature propuesta para que `sql/read`
fije el tope real de la consulta. Candidato del arnés: el diagnóstico de la
mutación paralela (en F-009 no dio falsos supervivientes: 76 de 76 confirmados
en serie).

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-009 está cerrada y mergeada a
> `dev`, sin desplegar: sigue el guion T19-T24 de `current.md` con el humano
> (despliegue con la llave cerrada, previas y UNA grabación autorizada). Antes de
> tocar §2-§4 del contrato con albaranes, avisa a la sesión de albaranes.
