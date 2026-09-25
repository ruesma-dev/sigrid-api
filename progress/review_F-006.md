<!-- progress/review_F-006.md -->
Revisión incremental desde e354862 (pasada 3) · HEAD `98db7ef` · 2026-09-25

# F-006 · Veredicto final

**Veredicto: APPROVED.** El único cambio de la pasada 2 (la tabla de la campaña manual de M1 en
`progress/mutacion_F-006.md`) está resuelto, y he reproducido tres de sus filas. Siguen dándose
por buenos los cinco parciales de la pasada 1 (lo aprobado hasta `22ba2a5`) y la pasada 2 (lo
aprobado hasta `e354862`). La pasada 2 se resume en §2; su detalle está en `git show ef1fdf9`.

**Nivel de rigor:** `critico` (declarado en `harness/features.json`). Pide fase RED, cobertura
≥ 80 %, una campaña de mutación completa con 0 supervivientes y RM5.

## 1 · Pasada 3: el delta `e354862..HEAD`

**Alcance del delta.** `git diff --stat ef1fdf9..HEAD` toca solo `progress/mutacion_F-006.md`
(+40/−17), y `e354862..HEAD` suma el veredicto de la pasada 2 (`review_F-006.md`). No se ha tocado
código, ni tests, ni spec, ni `impl`. El alcance medido y los 217 mutantes de RM1 no cambian.

**La tabla frente a `CHECKPOINTS.md` l. 237-244 y el cambio 1:**

- Una fila por mutante (MA-MH y la base), cada una con `function_app.py:<línea>`, el **texto
  exacto original → mutado** y el número de fallos, **sin `-x` y con `-x`** en columnas separadas.
  El comando se da literal (`python -m pytest tests/test_f006_route.py -q -p no:cacheprovider`).
- Líneas cotejadas con el fichero en HEAD: `357` `logger.warning(`, `358` el mensaje con el
  prefijo, `359` la comprensión `[(error["loc"], error["type"]) for error in exc.errors()]`.
  Las ocho filas apuntan a la línea correcta, y cada texto original aparece una sola vez en ella.
- La discrepancia «1 failed» de la ronda 1 queda explicada: era una ejecución con `-x`.
- Ninguno es equivalente: todos cambian el nivel, el prefijo o el contenido del aviso (RM3).

**Filas reproducidas por mí**, al pie de la letra, sobre una copia desechable (`git archive HEAD`
en el scratchpad). El script sustituye el texto solo en la línea indicada y restaura el fichero:

| Fila | Comando | Informe | Obtenido |
|---|---|---|---|
| base | sin `-x` | 12 passed (exit 0) | 12 passed (exit 0) |
| MB (l. 359) | sin `-x` | 2 failed, 10 passed (exit 1) | 2 failed, 10 passed (exit 1) |
| MG (l. 357) | sin `-x` | 2 failed, 10 passed (exit 1) | 2 failed, 10 passed (exit 1) |
| MA (l. 359) | con `-x` | 1 failed, 7 passed (exit 1) | 1 failed, 7 passed (exit 1) |
| MG (l. 357) | con `-x` | 1 failed, 7 passed (exit 1) | 1 failed, 7 passed (exit 1) |

En MB fallan exactamente los dos casos que nombra el informe:
`test_f006_r20_el_aviso_de_validacion_no_vuelca_los_valores_de_entrada[…-oficio-oficio-missing]`
y `[…-descripcion-string_too_long]`. Después borré la copia, y `git status` solo muestra
`` `0`].{t `` (ajeno y sin trackear, ya estaba).

**`bash harness/init.sh` (una vez, sin pipes):** `1733 passed, 1 skipped, 1 warning` en 92,71 s ·
`PUERTA COBERTURA: 100.0% de 560 líneas cambiadas (560/560, umbral 80%, nivel critico)`, igual que
en la pasada 2 · `PUERTA TAMAÑO` OK (requirements 140/150, design 167/250, impl 219/220) · rama
`feature/F-006-alta-parte-reclamacion` · `ENTORNO LISTO`, exit 0 · `ruff` 80 avisos (los de antes).

## 2 · Pasada 2 (resumen; lo aprobado hasta `e354862`)

- **Delta `22ba2a5..e354862`**: `current.md`, `tasks.md` (T16-T18), `impl`, `mutacion_F-006.md`
  (solo añade una sección), `function_app.py` (+6/−1, solo el `except ValidationError`),
  `tests/test_f006_route.py` (+44) y los cinco parciales. Nada en `infrastructure/`, `config/`,
  `domain/`, `application/` ni `infra/`. Sin push.
- **RM1 revalidado**: con el recálculo puro en HEAD (`alcance_de_feature` + `generar_mutantes`) sale
  el mismo alcance (808/463/16/206/62) y **217 mutantes** (135/39/3/34/6). Es la campaña sobre
  `22e23f7`, que sigue valiendo.
- **`current.md`**: resuelto. Solo F-006, y el prompt para retomar está vigente.
- **T17**: resuelto. No toca `SIGRID_DOMAIN_WRITE_ENABLED` (que sigue en `true`). Abre solo
  `SIGRID_RECLAMACION_WRITE_ENABLED` y la cierra después de T18 (R10).
- **T16**: resuelto y comprobado ejecutándolo (`t16_sim.py` con el JSON literal de `tasks.md`):
  `committed False`, `unidad_postventa_no_encontrada`, `interviniente_no_esta_en_la_obra`.
- **M1 (código)**: `function_app.py:357-360` solo registra `[(loc, type)]`. El test de R20 comprueba
  que no aparecen los valores. RED reproducido: MA da `2 failed`.
- **M1 (control del cero)**: `generar_mutantes` da 0 en l. 355-360 y 42 en el fichero entero, así
  que el cero es legítimo y la campaña manual es la vía correcta.

## 3 · Checkpoints (cinco parciales + pasadas 2 y 3)

| Checkpoint | Estado | Fuente |
|---|---|---|
| C1 `init.sh` exit 0 · ficheros base | [x] · [x] | esta pasada (§1) · `estado` |
| C2 una `in_progress` · rama · historia | [x] · [x] · [x] | `estado`, confirmado por `init.sh` de hoy |
| C2 `current.md` solo la sesión activa | [x] | pasada 2 |
| C3 hexagonal · 1.ª línea · sin print/secretos · Sigrid | [x] ×4 | `codigo`; M1 no importa nada ni añade `print` |
| C3 bis (4 casillas) | [x] | `docs` |
| C4 trazabilidad R1-R23 · sin red ni BBDD | [x] · [x] | `verificacion`; M1 añade 2 tests de R20 (231 en total) |
| C4 MANUAL listadas con comando exacto | [x] | pasada 2 |
| C4 bis rigor · RED · cobertura · mutación · muertos · coste · cabecera | [x] ×7 | `rigor`; RED y cobertura de M1, pasada 2 |
| C4 bis RM1 · RM2 · RM5 · RM6 | [x] ×4 | `rigor`; RM1 revalidado (217 en HEAD) |
| C4 bis campaña manual (0 mutantes → manual) | [x] | **esta pasada**: la tabla cumple l. 237-244, con 3 filas reproducidas |
| C4 bis supervivientes analizados · «Evidencias» · sin N/A | [x] ×3 | `rigor` y §1 |
| C4 ter | N/A | No existe `harness/rutas_sensibles.json`: N/A por el propio texto del checkpoint. El criterio, aplicado a mano en `verificacion`, sale OK |
| C5 `tasks.md` | [x] | T1-T14 y T19 `[x]`. T15-T18 **N/A para el cierre**: son MANUAL del humano, posteriores al merge (criterio de `review_F-004.md`). Guion exacto en `tasks.md` T15-T18 |
| C5 sin temporales · `features.json` | [x] · [x] | `estado`. `` `0`].{t `` sigue sin trackear y es ajeno: lo decide el humano |

## 4 · Cobertura de requisitos

La tabla R1-R23 → test está en el parcial `verificacion` (pasada 1): 231 tests de F-006, más los 2
de R20 que añade M1. La cobertura de líneas cambiadas es del 100 % (560/560).

## 5 · Cambios requeridos

Ninguno.

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
- **Para el humano en T15-T18**: en T16 `indice` empieza en 0 (el «parte 1» es `indice` 0; se
  distinguen por `referencia_externa`); el `--query` de T15 lleva paréntesis, que según
  `sigrid_api.md` §11 rompen `az.cmd` en Windows (ya lo avisa impl §8).
- **Margen de tamaño**: `impl` está en 219/220. Si se añade algo tras el merge, habrá que resumir.

## 7 · Automejora (propuesta, no aplicada)

- `reviewer.md` y `CHECKPOINTS.md`, «campaña manual»: exigir que la tabla la **genere el script**
  que aplica los mutantes (volcando `original → mutado` y la última línea de pytest), no que se
  escriba a mano. Así el texto exacto sale gratis y el formato no provoca otra ronda de revisión.
  Esta ronda lo confirma: un cambio de formato costó una pasada entera. Vale para cualquier
  proyecto, así que va a `arnes-base`.
- `reviewer.md`: el informe de review de una feature con varias pasadas llega al tope (140/140
  en la pasada 2). Proponer que cada pasada **sustituya** a la anterior por un resumen y remita a
  su commit (`git show <sha>`), como hace este. Va también a `arnes-base`.
