<!-- progress/current.md -->
# Trabajo en curso

## F-018 `in_progress` (2026-10-29): implementada; revisión troceada (T18) en corrección

Rama `feature/F-018-descuento-por-linea`, petición de `albaranes` (su F-110). Spec v1.2
[`specs/F-018-descuento-por-linea/`](../specs/F-018-descuento-por-linea/), aprobada por el humano (P1-P11; P11 = (a)
en `841e291`); medición M45-M51 en [`explore_F-018.md`](explore_F-018.md). Acuses de los contratos v8.4 (`albaranes`)
y v1.3 (`proformas`) recibidos el 2026-10-29; `albaranes` pegó su texto en `7aae0ba` y deja apagada
`ALTA_SIGRID_ENVIAR_DTO` hasta el aviso de despliegue. T1-T17 hechas (implementer): mutación en serie 66/66 muertos,
cobertura 100 % de 102 líneas cambiadas; informe [`impl_F-018.md`](impl_F-018.md).

**T18, revisión troceada (2026-10-29)**: APROBADOS `logica`, `C3C4ter`, `C4red` y `mutacion`. Cambios de texto en
`docs` (estado de los contratos; cota a origen de la proforma y de las vinculadas grandes; el clásico y
`albaran-directo` ignoran `dto`; notas caducadas de `azure-apps`; V3/V4 de la verificación manual), en corrección por
el implementer, y en `C1C2C5` (este fichero y `features.json`, corregidos por el líder). Incidencia: un revisor pasó
el árbol principal a `dev` de 13:23:30 a 13:23:44; `init.sh` repetido después sobre `ba5abbc`, en verde (3.793 passed).

**Después**: veredicto consolidado en `review_F-018.md`, merge a `dev`, despliegue (lo ordena el humano), aviso de
despliegue a `albaranes`, `proformas` y `facturas`, T19 (previas del líder), T20 (grabación con autorización expresa)
y T21.

**Verificaciones MANUAL pendientes** (comandos literales en
[`verificacion_manual.md`](../specs/F-018-descuento-por-linea/verificacion_manual.md); todo tras el despliegue):
- **V0**: setup (variables de entorno, sin secretos) y previa de regresión de `sigrid/albaran` sin `dto`.
- **V1** (líder, lecturas `sql/read`): V1a línea sin vincular con dto de la obra 0692 (`MA9999`); V1b `ctrpro` con dto
  `N%` y un albarán del escritorio vinculado; V1c contrato con dto y proforma del escritorio desde 2025.
- **V2** (líder, previa `commit:false`): la gemela de V1a, con `tar`/`dto`/`tot`/`pre`/`impbru`/`mov` como el escritorio.
- **V3** (líder, previas): contra V1b con su bruto y dto (sin avisos de precio ni de dto; los de partida o pendiente son
  ajenos a F-018), con otro dto (`dto_distinto_del_contrato`) y sin `dto` (R15: `tot`/`pre` como el escritorio).
- **V5** (líder, previa de proforma de mes con `otra_del_mes`): contra V1c, `tot`/`pre` y `impbru` como Sigrid.
- **V4** (humano, **solo con autorización expresa para esa escritura**, en la obra y con el proveedor que fije él):
  `commit:true`, revisión en la UI, repetición `idempotente` y anulación desde la UI (nunca `DELETE`) (T20).

## F-016 `blocked` (2026-10-28): proforma a origen DESPLEGADA; espera T17-T18 del humano

**Desplegada el 2026-10-28** (`dev` `6735a75`, orden del humano) con `SIGRID_PROFORMA_ORIGEN_ENABLED=false`; D1-D3
en [`verificacion_F-016.md`](verificacion_F-016.md). Revisión APROBADA (`review_F-016.md`); avisos a `proformas` y
`facturas` enviados (`proformas` lo usará en su F-005). **Motivo del `blocked`**: quedan T17 (previas sobre cadenas
reales, que lanza el líder con el visto bueno del humano, y avisar a `proformas` del resultado de §2.3) y T18
(grabaciones con autorización expresa); se pasa a `blocked` para dejar sitio a F-018 (una sola `in_progress`).
T20 y `done` tras T17-T18.

### Historia de F-016

Rama `feature/F-016-proforma-a-origen` desde `dev`. El humano decidió (V8 de F-007) que la proforma se registre **a
origen o por meses según indique el jefe de obra**, y por defecto por meses. Material: `progress/explore_F-007.md`
§M11 y §M16-M26 (el modelo a origen ya medido) y la spec de F-007.

**Spec escrita (spec-author, 2026-10-28), v2**: [`specs/F-016-proforma-a-origen/`](../specs/F-016-proforma-a-origen/)
(tasks T0-T20) y medición nueva M41-M44 (solo lecturas) en [`explore_F-016.md`](explore_F-016.md). Resumen:
`modo: "origen"` en la petición (sin él, F-007 exacta, sin claves nuevas); el llamante manda `proforma_anterior` o
`primera_de_cadena` y `linea_anterior` por línea; la API valida (del contrato, a origen, punta; línea de la anterior y
del mismo tipo), arrastra el resto a 0 y escribe las columnas a origen como Sigrid; sin tocar el núcleo de F-009 ni
los tests de F-007; llave propia `SIGRID_PROFORMA_ORIGEN_ENABLED`.

**Cambio de alcance (humano, 2026-10-28; sustituye a la enmienda 1)**: la API solo registra y valida; el modo, la
anterior, las continuaciones y los importes a buscar en Sigrid son del portal. Fuera la elección por importe, la
deducción del ANTERIOR, los avisos de comparación con la cadena y P2 (D7, del llamante); P4-P6 decididas (D14).

**Decisiones del humano (2026-10-28, aprobadas con la spec v2)**: P1 (D6) las arrastradas solo como `dcapro`, sin
`ctrprodes` ni `mov` a 0 (se comprueba en la UI, V9); P3 (D12) primero las líneas pedidas y después las arrastradas;
D3, D10 y D11 aceptadas con la spec.

**Implementación (implementer, 2026-10-28)**: T1-T16 **hechas** y commiteadas; `bash harness/init.sh` en verde
(3549 passed, cobertura 100 % de 270 líneas, mutación sin supervivientes no aceptados). `azure-apps` `3744877` y
`7afe9e9`. Queda: los avisos a `proformas` y `facturas` (texto en el informe, los envía el líder), T17-T18 manuales
del humano (`specs/F-016-proforma-a-origen/verificacion_manual.md`, con la prueba en lectura de las consultas del
contrato v1.2 §2.3), T19 revisión y T20 al cierre. Detalle en [`impl_F-016.md`](impl_F-016.md).

**Revisión troceada T19 (2026-10-28)**: aprobados `origen`, `C3C4ter`, `C4red` y `mutacion`; los cambios de texto
de `docs` y `C1C2C5` se corrigieron (`30a3d83`, `f0a870c`) y el veredicto consolidado salió APROBADO
(`review_F-016.md`, `5690963`). Avisos a `proformas` y `facturas` enviados; merge a `dev` y despliegue el 2026-10-28
(arriba).

## F-007 cerrada (2026-10-28): pendiente operativo

Resumen en `history.md`. Queda del humano: V6 en la UI y **anular `PROF26/01360`** (`con_ide` 2861898, obra 0404)
desde la UI; después, lecturas (sin `con` 2861898; `canser` de los `ctrpro` 258782 y 258783 de vuelta a 0). En
producción, `SIGRID_PROFORMA_WRITE_ENABLED=false`: abrirla es decisión del humano, y se avisa a `proformas`.
**F-017** (`pending`): códigos de partida repetidos en las obras, sacado de V8.

## F-015 `blocked` (2026-10-25): desplegada y verificada; espera la anulación de `AC26/30670`

**Por qué `blocked`:** solo falta el cierre manual. Administración tiene que revisar `AC26/30670` (`con.ide` 2860439,
grabación V5 autorizada en la obra 0404) y anularla desde la UI de Sigrid (nunca `DELETE`). Lectura del 2026-10-25:
sigue en Sigrid (1 `dcapro`, 1 `dcarec`, `ctrpro` 104172 con `canser` 70). Se pasa a `blocked` para liberar el único
`in_progress` a F-007. Al desbloquear: lecturas de comprobación (sin `con`, `dca` ni `dcarec` de 2860439, `canser` de
vuelta a 69), quitar las notas «PENDIENTE DE DESPLIEGUE» de F-015 en `azure-apps` (`49dfb36`), `done`, `history.md` y
merge de la rama de F-015 a `dev` (4 commits de documentación; el humano hace el push).

Detalle: [`impl_F-015.md`](impl_F-015.md) (decisiones y desviaciones), [`review_F-015.md`](review_F-015.md)
(pasada 2 APROBADA) y [`verificacion_manual.md`](../specs/F-015-albaran-plantilla-y-retencion/verificacion_manual.md).
La ampliación de R14 de F-015 (`ctrrec` con `valpor` NULL → 400 `retencion_no_soportada`) está en el contrato con
albaranes §3.3 y en `azure-apps/sigrid_api.md` §8.6.

## F-012 cerrada, desplegada y verificada (2026-10-19)

Resumen en `history.md`; verificación en [`verificacion_F-012.md`](verificacion_F-012.md). Albaranes, confirmado.
Fuera de alcance y sin alta todavía: las trazas `str(exc)` de las demás rutas vuelcan `input` de la petición.

## F-008 espera (2026-10-19)

- **F-008** (facturas de compra, su F-012): tienen casi todos los datos y enlazan cada línea con su `dcapro.ide` de
  origen; encaja con `explore_F-007.md` §M15. Requisitos de facturas: dry-run, idempotencia, `con.cod` e `ide` en la
  respuesta, forma de pago y vencimiento por defecto del contrato o `prv`.

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

**F-018** (arriba): en revisión; después merge, despliegue y T19-T21. **F-016** (arriba): desplegada; T17-T18.
**F-015 está `blocked`** hasta que
Administración anule `AC26/30670`. F-009 solo espera T24 (con F-053 en real). Después de F-018: F-008 (facturas de
compra, prioridad 10); F-017 (partidas repetidas); F-001 (calentamiento); F-013 (`sql/read` fija el tope real de la
consulta) y F-014 (el hueco residual del dry-run de dominio). Del arnés: actualizar `sigrid-api` a la versión de
`arnes-base` cuando salga la del encargo del hook, y el diagnóstico de la mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. **F-018** (descuento por línea) está `in_progress`: implementada y en
> revisión troceada (T18); después veredicto consolidado, merge a `dev`, despliegue que ordena el humano, avisos y
> T19-T21 (guion en `specs/F-018-descuento-por-linea/verificacion_manual.md`). **F-016** (proforma a origen) está
> `blocked`: desplegada el 2026-10-28 con la llave de origen cerrada; quedan T17 (previas, las lanza el líder con el
> visto bueno del humano) y T18 (grabaciones autorizadas una a una), guion en
> `specs/F-016-proforma-a-origen/verificacion_manual.md`. F-007 está cerrada; queda que el humano anule `PROF26/01360`. **F-015 está `blocked`** a la espera de
> que Administración anule `AC26/30670` desde la UI. F-009 está desplegada con la llave abierta; solo queda T24.
