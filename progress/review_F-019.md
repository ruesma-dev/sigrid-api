<!-- progress/review_F-019.md -->
Revisión completa (pasada 1) · desde `30cfcb4` (alta, incluida) hasta `23db6eb`

# F-019 · Actualizar el arnés 1.7.8 → 1.10.1 (reviewer)

**Veredicto: CHANGES_REQUESTED**

**Nivel de rigor:** `documental`, declarado en `features.json`. Exige C1–C3, C3 bis/ter si aplican y C5; sin fase
RED, cobertura ni mutación (C4 bis N/A por nivel). Carril `estandar`. `sdd: false`: se valida contra `acceptance`.

## Lo que se perdió: `tests/test_f004_settings.py` (bloqueante)

El instalador aplicó `tests/**` como `arnes_puro` y el payload 1.10.1 trae un `tests/test_f004_settings.py` **del
arnés** (su F-004: `settings.json` sin `PostToolUse`). Ese nombre ya lo usaba **sigrid-api para su propia F-004**
(`concepto-grafico`, rigor `critico`; commits `d714964`..`2c51973`). Se pisó en `28c4330` sin conflicto ni aviso.
Se perdieron 8 tests (R4 y R5 de F-004), entre ellos
`test_f004_r5_allowed_write_databases_sigue_siendo_solo_la_de_negocio` (que `ruesma_rep` siga fuera de
`ALLOWED_WRITE_DATABASES`, regla dura de `CLAUDE.md`) y `test_f004_r4_los_siete_ajustes_nuevos_arrancan_con_defecto_seguro`
(las llaves de escritura documental apagadas por defecto). `grep "def test_f004_r[45]" tests/` → **0**: nada los cubre
ya. El informe del implementer leyó sus 10 rojos de antes de la fusión como «de settings.json» y no lo detectó.

Método: para cada fichero modificado o borrado en `30cfcb4..HEAD` comprobé si existía en el payload 1.7.8
(`arnes-base` `685da06`). Solo dos no existían: `harness/ARNES_VERSION.md` (lo escribe el instalador, correcto) y este.

## Lo demás de la fusión (correcto)

- **Seis adaptados, sin pérdidas.** Comparé el delta «payload → nuestro» de HEAD con el delta «1.7.8 → nuestro» de
  `30cfcb4`: **idénticos línea a línea en los seis**. Es decir, cada fichero = payload 1.10.1 + exactamente las mismas
  personalizaciones que había. Conservado: título, mapa del repositorio, las seis reglas duras de Sigrid, markitdown,
  bloque de Ruesma; `RUTAS_PYTHON`, `RAMA_BASE=dev`, `COMANDO_TESTS=""`, §9 desactivada; las cinco trampas de C3;
  índice y puntero de `docs/referencia/README.md`. Sin marcas `[ADAPTAR]` sueltas.
- **Bloques genéricos.** Todos los que mandan los resúmenes 1.7.16/1.8.0/1.9.0 y F-070 están (se sigue de lo anterior:
  la única diferencia con el payload son las personalizaciones). El resto del payload (`arnes_puro`) es byte a byte
  igual salvo excluidos/estado del proyecto. `.gitignore` trae todas las líneas de `gitignore.arnes`. `rigor.json` no
  estaba afinado (igual al de `685da06`): no hacía falta `rigor.local.json`.
- **Contradicciones.** Ninguna interna: `CLAUDE.md`, `CONVENTIONS.md` y `leader.md` dicen lo mismo de merges (a `dev`
  tras el OK al resumen final, a `main` preguntando) y push (siempre humano). El protocolo de `azure-apps` del proyecto
  (`pull --rebase`, conflicto ⇒ `blocked`) es más estricto que el del `CLAUDE.md` global (`pull` y resolver en local) y
  manda por ser el del proyecto: correcto.
- **`.claude/settings.json`**: idéntico al payload; sin `PostToolUse`; `model: claude-opus-5-5`, `effortLevel: high`;
  allowlist con `ARNES_SIN_CACHE=1 bash harness/init.sh`, los siete `harness.*`/`backlog.py` y `git checkout -b`;
  conserva SessionStart/SessionEnd (`despierto_hook.sh`) y el Stop ligero.
- `harness/VERSION` y `ARNES_VERSION.md` = 1.10.1. `python harness/backlog.py --comprobar` → 0.

## F-008 y el estado (bloqueante, menor)

`30cfcb4` pasó F-008 de `in_progress` a `spec_ready` y no tocó `progress/current.md`, que sigue titulando
«F-008 `in_progress`». Además, `spec_ready` en la 1.10.1 significa «spec entregada, presentar su resumen al humano»
(`leader.md`, tabla de estados): un líder que la retome por el estado repetiría la parada de la spec, aprobada el
2026-10-30. Y el plan del commit («pasará a `human_review`») es **incorrecto**: según `current.md` a F-008 le falta
T35 (reviewer de la enmienda 1); `human_review` exige el APROBADO del reviewer. Saltaría la revisión de una feature
`critico` que escribe en producción.

Valoración: aparcarla en un estado no activo es inevitable mientras F-019 ocupe la única activa, y `spec_ready` vale
como aparcamiento **si el rastro lo dice**. Lo que no vale es la incoherencia ni el destino equivocado.

## Checkpoints

| | |
|---|---|
| C1 `ARNES_SIN_CACHE=1 bash harness/init.sh` exit 0 | [x] exit 0, `ENTORNO LISTO`: 6162 passed, 47 skipped en 1080 s; sin servicios.json, sin caché |
| C1 ficheros base existen | [x] |
| C2 una sola activa | [x] solo F-019 |
| C2 prioridad | [x] F-019 comprometida por el humano (alta del 2026-11-20) |
| C2 rama `feature/F-019-actualizar-arnes` | [x] |
| C2 `current.md` coherente | **[ ]** F-008 dice `in_progress` en `current.md` y `spec_ready` en `features.json` |
| C2 `done` con resumen en `history.md` | [x] sin cambios en `done` |
| C3 hexagonal, ruta en 1.ª línea, sin prints/secretos | [x] no hay código de la API en el diff; `harness/**` es payload |
| C3 trampas de Sigrid | [x] no hay SQL ni escritura; las cinco trampas siguen en C3 |
| C3 bis | N/A: `docs/referencia/README.md` no cambia en el diff (`git diff 30cfcb4..HEAD` vacío) |
| C3 ter | N/A: el entregable no atribuye afirmaciones a personas (solo ficheros del arnés y el informe) |
| C3 quater | N/A: F-019 no cambia lo que la API expone ni consume; no cruza la frontera |
| C4 un test por `acceptance` | **[ ]** criterio 2 («conservan lo propio de sigrid-api»): incumplido por `test_f004_settings.py`; criterios 1, 3 y 4 cubiertos por `test_f070_r30_*`, `test_f004_*` del arnés y el portero |
| C4 tests sin red ni BBDD | [x] |
| C4 MANUAL | N/A: no hay verificaciones manuales |
| C4 bis (RED, cobertura, mutación, e2e) | N/A por nivel `documental` |
| C5 commits `F-019: …`, uno por fichero adaptado | [x] 9 commits, todos con el prefijo |

## Cambios requeridos

1. **Recuperar los 8 tests propios de F-004** con `git show 30cfcb4:tests/test_f004_settings.py`, en un fichero de
   **nombre que no choque con el payload** (p. ej. `tests/test_f004_settings_concepto_grafico.py`, primera línea con
   su ruta nueva), sin tocar el `tests/test_f004_settings.py` del arnés (lo volvería a pisar la próxima
   actualización). Mismos nombres de función `test_f004_r4_*`/`test_f004_r5_*`. Commit `F-019: …`.
2. **Barrer otras colisiones**: confirmar en `impl_F-019.md` que ningún otro fichero propio de `tests/` ni de `scripts/`
   coincide con un nombre del payload 1.10.1 (mi barrido dice que no; que conste el comando).
3. **`progress/current.md`, sección F-008**: título con el estado real (`spec_ready` como aparcamiento mientras F-019
   ocupa la activa) y el destino correcto al retomarla: **`in_review`** (falta T35), **no** `human_review`, anotando
   antes `spec_aprobada: "2026-10-30"` en su entrada de `features.json` (si no, `python -m harness.estados --avisos`
   avisará al activarla). La spec no se vuelve a presentar.
4. Volver a pasar `bash harness/init.sh` completo tras 1 y anotar el resultado real en `impl_F-019.md`.

## Observaciones (no bloquean)

- C3 dice «tope de 1.000 filas por petición»; el despliegue sirve 500.000 (`CLAUDE.md` global). Texto propio previo:
  otra feature.
- `current.md` arrastra secciones de features cerradas (F-018, F-016, F-007, F-015): son pendientes operativos del
  humano, práctica previa de este repositorio; C2 pide limpiarlo. Lo dejo al líder.
- Fin de línea LF en los fusionados con `autocrlf=true`: sin efecto en las puertas.

## Automejora (propuesta, no aplicada)

- **`arnes-base`, instalador:** los tests del arnés se llaman por **feature del arnés** (`test_f004_*`, `test_f019_*`)
  y chocan con los de cualquier proyecto que tenga esa F. `tests/**` como `arnes_puro` los pisa en silencio. Propuesta:
  en `actualizar`, si el fichero destino existe y **no** estaba en el payload de la versión instalada, tratarlo como
  propio (no pisar, abortar o avisar); a medio plazo, prefijar los tests del arnés (`test_arnes_f004_*`).
- **`reviewer.md`:** añadir a la revisión de una actualización del arnés el barrido «fichero modificado que no existía
  en el payload de la versión anterior», que es lo que lo ha cazado aquí.
