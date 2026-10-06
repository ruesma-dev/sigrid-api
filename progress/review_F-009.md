<!-- progress/review_F-009.md -->
# Revisión F-009 · por lotes

## Lote A · T1 (caracterización) — 2026-10-06

Revisión completa (pasada 1) del lote A: commits `783f2d1`, `c5c51c6`, `112cb3c` sobre `c5ec2a2`.

**Veredicto pasada 1: CHANGES_REQUESTED** (resumida; la segunda pasada está más abajo).

**Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED, cobertura, mutación con cero
supervivientes y MANUAL listadas. Lote de solo test: lo que aplica se valida; lo demás, N/A justificado abajo.

### Comprobaciones de la pasada 1 (resumen)

1. **Sin producción** en los tres commits (`git show --stat`); `git diff dev` sin producción; dorado con un commit. [x]
2. **Qué fija y si caza.** Ruta HTTP real con el caso de uso clásico real; graba respuesta completa, cada llamada al
   repositorio (SQL, parámetros, `max_rows`), applocks, reintentos, timeouts y cada sentencia de la transacción
   (filas columna a columna). Están los seis casos de design §Caracterización. Cambios míos en el árbol, revertidos
   con `git checkout --`, con `python -m pytest tests/test_f009_caracterizacion.py -q -p no:cacheprovider`:

   | # | Cambio (original → mutado) | Resultado |
   |---|---|---|
   | M1 | clásico: `SET estser = ?, estfac = ?` → `SET estfac = ?, estser = ?` (UPDATE `ctr`) | `[clasico_commit]` FAILED |
   | M2 | directo `_resolve_obra`: `ORDER BY ide DESC` → `ORDER BY ide ASC` | `[directo_dry_run]`, `[directo_commit]` FAILED |
   | M3 | clásico: `"n_lineas_contrato": len(contract_lines)` → `len(contract_lines) - 1` | `[clasico_dry_run]`, `[clasico_commit]` FAILED |

3. **Límite «el dry-run no expone filas»:** no es un hueco (esas filas no las observa nadie, salen del mismo código
   que el commit, y T14 congela ese código). **Hueco real en la ruta**, lo único del clásico que toca el lote D: el
   **sondeo S1** (mensaje `"Solicitud invalida."` cambiado y un selector ingenuo `if "lineas" in body ...` tras
   `req.get_json()`) pasó con 32 tests verdes, y el cuerpo `5` pasaba de 400 a **500 `TypeError`**.
4. **Sin red, BBDD ni secretos:** barrido del dorado (correos, IPv4, GUID, claves, NIF): solo `B00000000`, sintético. [x]
5. **Riesgo para el lote D:** el dorado no guarda la forma de `build_dependencies`; si T13 cambia la tupla de 7,
   se adaptan la lambda de `ejecutar` y `SettingsDoble`, **sin tocar el dorado**. El reviewer del lote D debe
   comprobar que el diff de este test se limita a dobles y `ejecutar` (ni `CASOS` ni las comprobaciones legibles).
6. `bash harness/init.sh` en verde (1743 passed, 1 skipped). [x]

Cambios pedidos: (1) fijar las ramas de error de las dos rutas (Pydantic, cuerpo no objeto, cuerpo no
parseable), quitando solo `url` de `details.validation`; (2) que el líder decida sobre el commit único del dorado
(T14) y el design; (3) actualizar `impl_F-009.md`.

## Lote A · segunda pasada — 2026-10-06

Revisión incremental desde `112cb3c` (pasada 2): commits `91b929d` y `850a09a`.

**Veredicto: APPROVED**

### Contra los cambios pedidos

1. **[x] Ramas de error fijadas.** Seis casos nuevos (no siete, ver la observación O1): `clasico_falla_pydantic`,
   `clasico_cuerpo_numero`, `clasico_cuerpo_lista`, `clasico_cuerpo_no_json` (campo `crudo`, sin pasar por JSON),
   `directo_falla_pydantic` y `directo_cuerpo_numero`. Todos 400 y con `llamadas` = `[]`; el no parseable da
   `details.type` `JSONDecodeError`. `ejecutar` quita **solo** `url` de cada error de `details.validation`; `type`,
   `loc`, `msg`, `input` y `ctx` siguen comparándose. Comprobación legible nueva:
   `test_f009_r2_r3_las_ramas_de_error_de_las_rutas_no_llegan_al_repositorio`. `test_f009_r4_*` cambia de nombre
   (`..._casos_definidos`), coherente con el superconjunto que ha aceptado el líder.
2. **[x] Decisión del líder aplicada.** `git log -- tests/fixtures/f009_caracterizacion.json` → `91b929d`, `783f2d1`,
   los dos `F-009 T1:` y anteriores a todo cambio de producción. T14 en `tasks.md`: «con solo commits `F-009 T1:`,
   todos anteriores a cualquier cambio de código de producción de F-009 (…sin reescribir historia)». Es coherente
   y se puede comprobar con los mismos dos comandos. `design.md` sin tocar (`git show --stat`).
3. **[x]** `impl_F-009.md` §Lote A actualizado con la tabla de los casos nuevos y su motivo.

### Comprobaciones de la pasada 2

- **Sin producción:** `91b929d` = `tasks.md` + test + dorado; `850a09a` = `current.md` + `impl_F-009.md`.
  `git diff dev --stat` sin `tests/`, `progress/`, `specs/`, `BACKLOG.md` ni `features.json`: vacío.
- **Los seis casos previos, idénticos:** `git show 91b929d -- <dorado>` no tiene ninguna línea `-`. Además, comparé
  el JSON de `783f2d1:` con el de HEAD caso a caso: 6 → 12 claves, `all(a[k] == b[k])` = `True`.
- **Los nuevos cazan cambios.** Ahora en una **copia aislada** (`git archive HEAD` al scratchpad, ejecutada con el
  `.venv` del repositorio; el árbol real no se ha tocado y `git status` queda igual que al empezar):

  | # | Cambio en `function_app.py` de la copia | Resultado |
  |---|---|---|
  | S1 | `sigrid_albaran`: `"Solicitud invalida."` → `"Solicitud no valida."` + `if "lineas" in body or "referencia_externa" in body: raise RuntimeError(...)` tras `req.get_json()` | `[clasico_falla_pydantic]`, `[clasico_cuerpo_numero]`, `[clasico_cuerpo_lista]` FAILED; 3 failed / 14 passed |
  | S2 | `sigrid_albaran_directo`: guarda R8 ingenua `if body.get("commit") is True and not settings.sigrid_albaran_write_enabled: raise ValueError(...)` tras `req.get_json()` | `[directo_cuerpo_numero]` FAILED (`AttributeError` → 500); 1 failed / 16 passed |
  | — | copia sin cambios | 17 passed |

  S2 es justo la forma más probable de implementar R8 «antes de ejecutar el caso de uso»: el dorado la caza.
- **Calidad:** `ruff check tests/test_f009_caracterizacion.py`: `All checks passed!`. Primera línea con la ruta;
  sin `print`; datos sintéticos (los casos nuevos solo añaden `ruesma_prueba`, `9999`, `B00000000`).
- **`bash harness/init.sh`** (tal cual): `ENTORNO LISTO`; **1750 passed, 1 skipped** (+7 tests: 6 parametrizados + 1
  legible); `PUERTA COBERTURA: N/A (F-009 no cambia líneas Python de producción frente a dev)`; tamaño en topes.

### Checkpoints (lote A, estado final)

- **C1** [x] init en verde · [x] ficheros base.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [x] sin `done` nuevas. `current.md` arrastra la cola
  de la v7 «ya superada»: observación no bloqueante, anterior a este lote.
- **C3** [x] sin producción · [x] primera línea con la ruta · [x] sin `print`, TODOs, secretos ni dependencias
  nuevas · reglas de Sigrid: N/A por contenido (no hay SQL nuevo; el que se graba es el de `dev`).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R2 → `test_f009_r2_*` (8 parametrizados + 2 legibles + 1 compartido), R3 → `test_f009_r3_*` (4 + 1 + el
  compartido `test_f009_r2_r3_*`), R4 → `test_f009_r4_*` + T14; el resto de R1-R36 corresponde a los lotes B-E
  (N/A aquí) · [x] sin red ni BBDD · [x] este lote no añade verificaciones MANUAL.
- **C4 bis** [x] rigor `critico` declarado · [x] fase RED: el entregable es el propio test, demostrado con las
  trazas del implementer y mis M1-M3, S1 y S2 · [x] cobertura N/A con el motivo impreso · N/A mutación y todo
  su bloque (muertos, coste, cabecera de campaña no válida, RM1, RM2, RM5, RM6, campaña manual, supervivientes):
  este lote no tiene producción que mutar; la campaña `critico` es T16 (lote E) · [x] «Evidencias» presente.
- **C4 ter** N/A: el repositorio no declara `harness/rutas_sensibles.json` (solo existe el `.ejemplo.json`).
- **C5** N/A `tasks.md` completo (feature por lotes; T2-T25 pendientes según el plan) · [x] T1 `[x]` con sus commits
  `F-009 T1:` · [x] `features.json` al día. Residuo sin trackear `` `0`].{t `` (0 bytes, 2026-09-24): anterior a
  F-009 y ajeno a este lote; que lo borre el humano.

### Observaciones (no bloquean)

- **O1 · Recuento de casos mal escrito.** El dorado tiene **12** casos (6 + **6** de las rutas), pero
  `progress/impl_F-009.md` línea 48 dice «13 casos… siete de las rutas», la línea 64 «En los siete de las rutas», y
  `progress/current.md` dice «13 casos»; el mensaje de `91b929d` también dice «siete» (ese queda así: no se reescribe
  historia). Corregir a 12/seis en el próximo commit de seguimiento: el reviewer del lote D se apoyará en ese número.
- Para el lote D: T13 debe dejar en verde los 17 tests de este fichero **sin tocar el dorado** ni `CASOS`.

### Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C4 bis (fase RED) pide romper «en una copia aislada, nunca en el árbol real», y el encargo de la
  pasada 1 pidió hacerlo en el árbol y revertir. Unificar los dos; la copia con `git archive HEAD` al scratchpad
  (pasada 2) cuesta lo mismo y no expone el árbol.
- `.claude/agents/reviewer.md`: en los tests de caracterización, exigir que cubran **cada rama de la capa que la
  feature va a modificar** (aquí, las salidas de error de la ruta), no solo los casos que enumera el design.
