<!-- progress/review_F-006.md -->
Revisión incremental desde 22ba2a5 (pasada 2, consolidada) · HEAD `e354862` · 2026-09-25

# F-006 · Veredicto consolidado

**Veredicto: CHANGES_REQUESTED.** Hay un solo cambio pendiente y es documental: la tabla de la
campaña manual de M1 (C4 bis, casilla «campaña manual»). Los arreglos T16, T17, `current.md` y el
código de M1 están verificados y en verde. Los cinco parciales de la pasada 1 se dan por buenos
tal como están (lo aprobado hasta `22ba2a5`). Esta pasada solo mira el delta `22ba2a5..HEAD`.

**Nivel de rigor:** `critico` (declarado en `harness/features.json`). Pide fase RED, cobertura
≥ 80 %, una campaña de mutación completa con 0 supervivientes y RM5.

## 1 · `bash harness/init.sh` (una vez, sin pipes) frente a «Evidencias» (impl §10)

| Dato | `init.sh` de hoy | impl §10 | ¿Coincide? |
|---|---|---|---|
| Suite | 1733 passed, 1 skipped, 1 warning, 93,45 s | 1.733 / 1 / 0; 101,62 s y 96,68 s | Sí (el tiempo es de otra ejecución) |
| Cobertura | `100.0% de 560 líneas cambiadas (560/560, umbral 80%, nivel critico)` | 100,0 % de 560 | Sí |
| Tamaño | requirements 140/150, design 167/250, **impl 219/220** | — | OK, pero sin margen: ver cambio 1 |
| Final | `ENTORNO LISTO`, exit 0; `ruff` 80 avisos (los previos) | `ENTORNO LISTO` | Sí |

Los 560 no cambian con M1: sustituye una sentencia por otra y los comentarios no cuentan.

## 2 · ¿Toca el delta solo lo esperado? (`git diff 22ba2a5..HEAD`, commit a commit)

- `70237c6`: `current.md`. `2edba47`/`657a9bf`: `tasks.md` (T16-T18) e `impl`. `52ba4be`:
  `function_app.py` (+6/−1, solo el `except ValidationError`) y `tests/test_f006_route.py` (+44).
  `49bbd25`/`8877704`: `impl`, `current.md` y `mutacion_F-006.md` (solo añade una sección; la
  cabecera medida no cambia). `e354862`: los cinco parciales.
- Las líneas quitadas de `impl` §1-§6 solo resumen texto, no cambian ningún dato (diff leído).
- Nada en `infrastructure/`, `config/`, `domain/`, `application/` ni `infra/`. `dev` y `main`
  en `210fac1`; `git branch -r --contains 70237c6` vacío: sin push.
- **Lo aprobado no se ha reabierto.** El recálculo puro en HEAD (`alcance_de_feature` +
  `generar_mutantes`) da el mismo alcance (808/463/16/206/62) y **217 mutantes** (135/39/3/34/6).
  Es el total de la campaña sobre `22e23f7`, que por tanto sigue valiendo (RM1).

## 3 · Verificación de cada CAMBIO pedido, contra el estado actual

**Estado, cambio 1 (`current.md`): resuelto.** Solo F-006; sin F-004/F-005 ni «faltan Q1-Q4» /
«spec_ready y PARAR». «Prompt para retomar» apunta a F-006 y su revisión troceada, deja fuera
T15-T18 y sigue valiendo tras este veredicto. Lo pendiente del humano que queda sigue vigente.

**Verificación, cambio 1 (T17): resuelto.** `SIGRID_DOMAIN_WRITE_ENABLED` «NO se toca» (cotejado:
`azure-apps/sigrid_api.md:330` la da en `true`). Abre **solo** `SIGRID_RECLAMACION_WRITE_ENABLED`
(JSON ASCII sin BOM, `--settings "@f006_abrir_reclamacion.json"`) y la cierra a `false` en un paso 3
«**DESPUÉS de T18**» (R10); T18 acaba con ese paso. La verificación pide que
`SIGRID_DOMAIN_WRITE_ENABLED` **siga en `true`**. Cuerpo del `commit` literal.

**Verificación, cambio 2 (T16): resuelto, y lo he comprobado ejecutándolo.** El lote literal
tiene tres referencias distintas (`PVI-PRUEBA-0001/0002/0003`). Contra el orden de `_planificar`
(`create_partes_reclamacion_use_case.py:432-484`: prefijo → duplicada → UPV → tipo → clase → oficio
→ intervinientes), el 2 cae en la UPV `0626.99NO EXISTE`; el 3 pasa UPV, tipo `0002` y oficio
`0039`, y cae en `_resolver_intervinientes` (l. 537): `0006` no tiene `obrofc` en 0626.

Lo he confirmado con un script en el scratchpad (`t16_sim.py`). Extrae el JSON **de `tasks.md` tal
cual** y lo pasa por el caso de uso con los dobles de `test_f006_use_case.py`, que modelan obra 0626,
UPV y 0039/1181. Resultado: `committed False`, `previsto` (5 filas),
`unidad_postventa_no_encontrada`, `interviniente_no_esta_en_la_obra` y `transacciones: []`. El
`LIKE` va con el parámetro literal y el aviso del cambio de mes.

**M1 (código): resuelto.** `function_app.py:357-360` solo registra `[(loc, type)]`. El `loc` lleva
nombres de campo e índices, no valores. El test `test_f006_r20_el_aviso_de_validacion_no_vuelca_…`
marca referencia y descripción y comprueba que no aparecen, además de `input`, el prefijo, `loc` y
`type`. **RED reproducido:** el mutante MA (volver a `exc`) da `2 failed` con los mismos mensajes que
impl §9. El test y el código van en el mismo commit, pero la reproducción lo cubre.

**M1 (mutación): la prueba de control es legítima.** `generar_mutantes` da 0 sobre las l. 355-360
y 42 sobre `function_app.py` entero: el generador funciona, esas líneas no tienen operador. He
reproducido los **8** manuales sobre una copia (`git archive HEAD` en el scratchpad, `m1_repro.py`).
El árbol queda limpio.

| Id | Texto exacto aplicado (en `function_app.py:357-360`) | Resultado |
|---|---|---|
| base | sin cambios | 12 passed |
| MA | `[(error["loc"], error["type"]) for error in exc.errors()]` → `exc` | 2 failed |
| MB | → `[error["type"] for error in exc.errors()]` | 2 failed |
| MC | → `[error["loc"] for error in exc.errors()]` | 2 failed |
| MD | → `exc.errors()` | 2 failed |
| ME | → `[]` | 2 failed |
| MF | `"ValidationError en sigrid/partes-reclamacion: %s"` → `"%s"` | 2 failed |
| MG | `logger.warning(` → `logger.debug(` | 2 failed |
| MH | `logger.warning(` → `logger.info(` | 2 failed |

Todos cambian el log que se observa, así que ninguno es equivalente (RM3 no aplica). **Pero** el
informe no trae este texto exacto (ver cambio 1). Además, su «1 failed» de MA no cuadra con los 2
fallos que salen al ejecutar el fichero, salvo que se lanzara con `-x`, y no lo dice.

## 4 · Checkpoints (suma de los cinco parciales y esta pasada)

| Checkpoint | Estado | Fuente |
|---|---|---|
| C1 `init.sh` exit 0 · ficheros base | [x] · [x] | esta pasada (§1) · `estado` |
| C2 una `in_progress` · rama · historia | [x] · [x] · [x] | `estado`, confirmado por `init.sh` de hoy |
| C2 `current.md` solo la sesión activa | [x] | esta pasada (antes KO en `estado`) |
| C3 hexagonal · 1.ª línea · sin print/secretos · Sigrid | [x] ×4 | `codigo`; M1 no importa nada ni añade `print` |
| C3 bis (4 casillas) | [x] | `docs` |
| C4 trazabilidad R1-R23 · sin red ni BBDD | [x] · [x] | `verificacion`; M1 añade 2 tests de R20 (231 en total) |
| C4 MANUAL listadas con comando exacto | [x] | esta pasada (antes KO en `verificacion`) |
| C4 bis rigor · RED · cobertura · mutación · muertos · coste · cabecera | [x] ×7 | `rigor`; RED y cobertura de M1, esta pasada |
| C4 bis RM1 · RM2 · RM5 · RM6 | [x] ×4 | `rigor`; RM1 revalidado aquí (217 en HEAD) |
| **C4 bis campaña manual (0 mutantes → manual)** | **[ ]** | **esta pasada: sin texto exacto ni número de fallos por fila** |
| C4 bis supervivientes analizados · «Evidencias» · sin N/A | [x] ×3 | `rigor` y §1 |
| C4 ter | N/A | No existe `harness/rutas_sensibles.json`: N/A por el propio texto del checkpoint. El criterio, aplicado a mano en `verificacion`, sale OK |
| C5 `tasks.md` | [x] | T1-T14 y T19 `[x]`. T15-T18 **N/A para el cierre**: son MANUAL del humano, posteriores al merge (criterio de `review_F-004.md`). Guion exacto en `tasks.md` T15-T18 |
| C5 sin temporales · `features.json` | [x] · [x] | `estado`. `` `0`].{t `` sigue sin trackear y es ajeno: lo decide el humano |

## 5 · Cambios requeridos

1. **`progress/mutacion_F-006.md`, sección «Ronda de revisión · M1»:** reescribir la tabla con una
   fila por mutante, cada una con `function_app.py:<línea>`, el **texto exacto original → mutado** y el
   **número de fallos** (`N failed`, y si se usó `-x`, decirlo). La columna de §3 sirve de
   referencia, pero el implementer tiene que ejecutarlo él. Justificación: `CHECKPOINTS.md`
   l. 237-244 no deja marcar el punto sin ese texto, y «sin `loc`» o «lista vacía» están
   descritos con palabras. La tabla va en `mutacion_F-006.md` y **no** en `impl`, que ya está en
   219/220. Si `impl` §9 cambia, que siga cabiendo.

La pasada 3 será incremental desde `e354862` y solo sobre ese fichero, más `init.sh`.

## 6 · Menores abiertos y su destino (no bloquean)

- **M2** (`codigo`), `[0-9]` acepta superíndices con la colación CI. Hoy hay 0 filas afectadas y
  el fallo acabaría en rollback. **Destino:** se queda anotado; si aparece, será una feature propia.
- **O1-O6** (`codigo`): dueño de la referencia, orden R7-R8 frente a E1, `log.usu`, texto de
  `error_de_escritura`, presupuesto por parte, deadlock y cp1252. **Destino:** O2 y O4 van a
  `postventa-incidencias` (F-040) cuando lo consuma; el resto se queda documentado.
- **Docs 1-2**: en §8.9, «o sin ficha `rcp`», y en §7.2, `base_de_datos_no_permitida` también en
  dry-run. **Destino:** la próxima vez que se toque `azure-apps/sigrid_api.md`.
- **Rigor 1-2** (numeración de la ronda 1 irreproducible; T11 con test y código en un commit) y
  **verificación, nota 1** (R5): no piden cambio; la automejora de `rigor` va a `arnes-base`.
- **Nuevas**, para el humano en T15-T18: en T16 `indice` empieza en 0 (el «parte 1» es `indice`
  0; se distinguen por `referencia_externa`); el `--query` de T15 lleva paréntesis, que según
  `sigrid_api.md` §11 rompen `az.cmd` en Windows (ya lo avisa impl §8).

## 7 · Automejora (propuesta, no aplicada)

- `reviewer.md` y `CHECKPOINTS.md`, «campaña manual»: exigir que la tabla la **genere el script**
  que aplica los mutantes (volcando `original → mutado` y la última línea de pytest), no que se
  escriba a mano. Así el texto exacto sale gratis y el formato no provoca otra ronda de revisión.
  Vale para cualquier proyecto, así que va a `arnes-base`.
