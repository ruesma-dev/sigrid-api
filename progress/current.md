<!-- progress/current.md -->
# Trabajo en curso

## F-009 `in_progress` (2026-10-06) — implementación por lotes

**PARADA 1 aprobada por el humano (2026-10-06):** v8.1 y plan en cinco lotes, cada uno implementer → reviewer
(revisión troceada por bloques de `CHECKPOINTS.md`), sin empezar el siguiente hasta aprobar el anterior:
**A** T1 (caracterización, commit sin producción) · **B** T2-T6 (settings, modelos, SQL, funciones puras, filas) ·
**C** T7-T12 (caso de uso, idempotencia, dry-run, commit, devoluciones, equivalencia) · **D** T13-T15
(`function_app.py`, R2-R4, trazas) · **E** T16-T18 (mutación, `ARCHITECTURE.md`, `azure-apps/sigrid_api.md`).
Luego PARADA 2 y manuales T19-T24 (despliegue y escrituras solo con autorización expresa). Fuera:
`infrastructure/security/`, casos de uso y modelos del clásico y de `albaran-directo`, `.env`, Azure y SQL Server.
**Lote A aprobado** (T1, `783f2d1` + `91b929d`; segunda pasada APPROVED, `055a7e1`). **Lote en curso:** B. **T2-T6 hechas** (implementer, 2026-10-06; `c7c0b95`, `91f80f6`, `e2d52fb`, `f0130ed`, `d936ced`, `43eae24`): settings (R10), modelos (R1, R5-R7, R9), SQL L1-L15/E1-E12 (R31), funciones puras y filas; informe en [`impl_F-009_loteB.md`](impl_F-009_loteB.md). Revisión: trozo 1 APROBADO; trozo 2, ciclo 1 hecho (ε de stock cero `EPSILON_STOCK` = 1e-6 y **opción C** del humano para el precio de la vinculada: `usa_precio_del_contrato`, `tot` = round(can·pre, 2)). **Siguiente:** segunda pasada del trozo 2.

**Spec v8.2 (spec-author, 2026-10-06):** opción C del humano para los importes de la vinculada (R17, design §Importes,
contrato §2.2/§3.1/§3.2/H14, solo redacción), ε = 1e-6 del stock en R19 y dos diferencias más en §Equivalencia (O2).
Detalle en [`spec_F-009.md`](spec_F-009.md) §v8.2. **Pendiente**: el implementer pasa `importe_linea`/tolerancia de A a C;
el humano confirma que el cambio de §3.2 del contrato (cuándo salta `precio_distinto_del_contrato`) es solo redacción para F-053.

### Estado de la spec al aprobarla

**v8.1 (spec-author, T0c):** T0b-quinquies volcada ([`spec_F-009.md`](spec_F-009.md) §v8.1). **M14e refuta la media
ponderada global** del producto (2 de 34 entradas, 4 de 16 devoluciones). Regla nueva aprobada por el humano:
`mov.prepma` (y `dcapro.prepma`) = **el `almpma` del último `mov` del mismo producto y almacén antes de la línea** (el
PMP del almacén vigente en el alta; encadenado en el albarán; 0 sin `mov` anterior), hipótesis coherente con los datos
y no demostrada sobre el histórico ⇒ verificación manual en **T22** (frente a un albarán del escritorio del mismo día y
almacén) y **T24** (primera alta real). Simplificación: fuera L12b-c, E7b (y su lectura sin `UPDLOCK`) y
`siguiente_prepma`; el valor sale de L12/E7. Aprobadas por el humano las decisiones de §v8: campo `naturaleza`
retirado, `cuacomcod` sin una única `cua` ⇒ `naturaleza_no_valida` y `tex` vacío en las sin vincular. **T0 cerrada**,
sin mediciones pendientes ni preguntas abiertas; §Condicionales solo con lo manual (T22-T24). **Script de T0 retirado**
(`scripts/medir_f009_t0.py` y su prueba, commit propio; quedan en el historial). Contrato: solo estado (cabecera, §0,
§5 y §8), sin tocar la forma de §2-§4 (congelada para F-053); con la Parte A de las propuestas de F-053 (H8, H17, H28,
H29 y H30 cerrados por el humano el 2026-10-06). Topes: 150/150 y 249/250. **Siguiente:** el humano aprueba la v8.1 y
el líder hace la PARADA 1 de implementación (T1, caracterización sobre `dev`) antes de pasar a `in_progress`.

*(Lo que sigue es el estado de la v7, ya superado por la v8.)*

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
sin medir), P6 (F-053). **Respuestas del humano (2026-10-05):** `XA9999` es decisión suya
(confirmado); P1 (M14c), P2, P3 y P5 se miden en la misma pasada. **T0a-ter hecha** (M16c, M14c,
`XA9999`, `numemp`; `38d3571`, `ade7b47`, `bda26b1`; APPROVED en la segunda pasada:
[`review_F-009_T0a_ter.md`](review_F-009_T0a_ter.md)). **T0b-ter hecha** (2026-10-06, fichero
`%TEMP%\f009_t0_20261006_005622.txt`): `XA9999` con `tipmov` 1; `cueide` = `cuacomcod` de la
naturaleza 97,9 % (P3 y P4 cerrados); `numemp` 0 en todas (P2); `prepma` 0 sin `mov`; analítica con
la regla de la v7 solo 86,8 % (XA9999 0 %: su `caagascod` no lleva `.`; MA9999 con partida 92,3 %);
`mov.prepma` sin explicar (es el «Precio Medio Compra» del producto, no del almacén). Negocio
(correo del director de Administración y Control de Costes): `cod2` lo pone el jefe de obra en la
planificación de compras; naturalezas específicas «a efectos prácticos no se usan». **T0a-quater
hecha** (M14d, M16d, M19 nueva; `aa599f0`, `8e6e298`, `7f350bb`, `2b7a85f`; APPROVED en la segunda
pasada: [`review_F-009_T0a_quater.md`](review_F-009_T0a_quater.md)). **Siguiente, del humano
(T0b-quater):** `--solo M14 M16 M19` (comando en
[`impl_F-009_T0a_quater.md`](impl_F-009_T0a_quater.md)) → T0c (v8 y retirada del script).
**Pendiente del humano:** confirmar H34 (naturaleza por mapeo producto → naturaleza `MA99`/`QA99`/
`XA99`) y H35 (las vinculadas copian `cod2`/`dncide`/`dncproide` del `ctrpro`), que trae el contrato
v7.1 (`2631b1a`, **segundo commit de la sesión de albaranes en este repo**); y si albaranes debe
proponer en un fichero aparte en vez de editar el contrato. **Ojo:** la sesión del agente de albaranes editó `contrato_albaranes.md` en este
repo (`844ebc8`, v6.1); la v7 lo integró. El contrato es de sigrid-api: albaranes debería proponer, no
editar.

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
