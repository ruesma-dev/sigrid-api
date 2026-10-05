<!-- progress/current.md -->
# Trabajo en curso

## F-009 spec v7 (2026-10-05), `spec_ready` — espera la validación del humano y T0b-ter

**v7 (spec-author):** T0b-bis volcada ([`spec_F-009.md`](spec_F-009.md) §v7, tabla M → resultado →
decisión). Cerradas: M9 (`mov` si y solo si `pro.tipmov` = 1; **H20 cerrado**, sin puerta dura), M11
(L8b), M14b (L5), M17b (anular borra; **H9 cerrado**, R30b retirada) y `dcaproana` (no se escribe).
M14 corrige R21: `dcapro.prepma` = `mov.prepma`. Decisión del humano aplicada: campo opcional
`naturaleza` en la sin vincular (`naturaleza_no_valida`); analítica = `caa` `<obra>.<sufijo del
caagascod>` y cuenta del `cuacomcod` de la naturaleza, **condicional a M16c** (`analitica_no_resuelta`).
Lista blanca con `XA9999` (contrato v6.1). Contrato con albaranes al día (§2.2, §3.3, H9, H10, H20, §8).
Topes: 150/150 y 250/250. **Para el humano:** validar la v7 y las preguntas **P1-P6** de §v7: P1
(`mov.prepma`: ¿M14c en T0b-ter?), P2 (`numemp`), P3 (`cua` por empresa), P4 (cuenta cuando el
usuario cambia la naturaleza: la muestra apunta a la del producto, contra la decisión), P5 (`XA9999`
sin medir), P6 (F-053). **Siguiente:** T0b-ter (`--solo M16` con M16c, en curso por el implementer;
`--solo M14 M16` si se aprueba M14c) → T0c (v8 y retirada del script).

*(Lo que sigue es el estado de la v6, ya superado por T0b-bis.)*

## F-009 spec v6 (2026-10-05), `spec_ready` — espera la validación del humano y T0b-bis

**v6 (spec-author):** T0b volcada en la spec ([`spec_F-009.md`](spec_F-009.md) §v6, tabla M →
resultado → decisión). Cerradas: M3 (`paride` opcional, R14b), M7 (sin `dcapropar`), M13 (`est` 1,
`ori` 0), M14 (reseteo), M16 (almacén; `caaide` de las vinculadas del `ctrpro`) y M18
(`referencia_linea` en `dcapro.refent`, R30c). Decisiones del humano aplicadas: lista blanca
`["MA9999", "QA9999"]` con producto por línea (H20 para los dos) y analítica de las sin vincular
condicional a M16b, sin regla provisional. Abiertas a **T0b-bis** (`--solo M9 M11 M14 M16 M17`, tras
ampliar el script con M14b, M16b y M17b; M9 y M11 deben cubrir también QA9999): M9, M11, M14b, M16b,
M17b. **Para el humano:** validar la v6; `cod2` y `dncide` (consultados por correo al director de
Administración y Control de Costes el 2026-10-05; no bloquean); confirmar `tex` vacío en las sin
vincular. Topes: requirements 150/150, design 250/250 (la regla de M16b tendrá que resumir y enlazar).
**T0a-bis hecha** (script de la segunda pasada, `00179a2`, `0037c72`, `c42bb2b`; APPROVED en la
segunda pasada: [`review_F-009_T0a_bis.md`](review_F-009_T0a_bis.md)). **Siguiente, del humano
(T0b-bis):** `--solo M9 M11 M14 M16 M17` (comando en [`impl_F-009_T0a_bis.md`](impl_F-009_T0a_bis.md))
y pegar el fichero de `%TEMP%`. Después T0c: v7 (o PARADA si M16b no da regla) y retirar el script.

*(Lo que sigue es el estado de la v5.1, ya superado por T0b.)*

PRE-1 de albaranes F-053: **modo extendido de `sigrid/albaran`** (el clásico, idéntico y fijado
por un test de caracterización previo). **v5** incorpora los huecos de F-009 del contrato con
albaranes ([`contrato_albaranes.md`](../specs/F-009-alta-albaran-compra/contrato_albaranes.md) §5,
con tabla de estado H1-H33) y las decisiones del humano del 2026-10-05 (H4, H8, H9, H17, H20, H28,
H31). **v5.1** aplica las respuestas a N4-N12: aprobadas con la recomendación salvo N10, sustituida;
**sin campo `almacen`** (la línea sin partida, `partida` ausente o `null`, es el «almacén» de
Ruesma: `paride` 0 nunca heredado, `almide`/`cenide` en toda línea, aviso
`sin_partida_en_linea_con_partida`) y **sin `fecha_no_valida`** (las fechas futuras las controla la
app). Detalle en [`spec_F-009.md`](spec_F-009.md) §v5.1. Topes: requirements 150/150, design 249/250.

**v5.1 aprobada por el humano** (2026-10-05, «lo demás ok»). **T0a hecha** (script ampliado,
`7592dc7`, `988e7c1`, `2f68c41`; APPROVED en la segunda pasada: [`review_F-009_T0a.md`](review_F-009_T0a.md)).
**Siguiente, del humano (T0b):** lanzar **una** repetición
`--solo M3 M7 M9 M11 M13 M14 M16 M17 M18` (comando al final de [`impl_F-009_T0a.md`](impl_F-009_T0a.md))
y pegar el fichero de `%TEMP%`. Después T0c: el spec-author lo vuelca (v6 si cambia alguna regla
condicional) y se retira el script (N3). Puerta dura H20: sin M9 cerrada no hay modo real. El fichero de
resultados de T0 vive en `%TEMP%`. F-053 debe dejar de mandar `almacen` (daría 400 sin código).

**Para el agente de albaranes:** [`para_albaranes_F-009.md`](para_albaranes_F-009.md) (decisiones
del humano y huecos de F-053/F-049/F-051; F-053 debe realinearse con la v5.1).

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

F-007 (proformas) y F-008 (facturas de compra), `pending`
con `sdd` y rigor `critico`; y F-001 (calentamiento). Candidato del arnés: el
diagnóstico de la mutación paralela.

## Prompt para retomar

> Lee `CLAUDE.md` y `progress/current.md`. F-006 está cerrada, desplegada y
> verificada; queda que el humano anule en Sigrid el parte de prueba
> `RS26.09/0439`. Lo siguiente del backlog es F-007 (proformas) o F-008 (facturas
> de compra), ambas `pending` con `sdd`: no arranques ninguna sin preguntar.
