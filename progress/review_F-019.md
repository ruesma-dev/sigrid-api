<!-- progress/review_F-019.md -->
Revisión incremental desde `23db6eb` (pasada 2) · delta `23db6eb..f72caea`

# F-019 · Actualizar el arnés 1.7.8 → 1.10.1 (reviewer)

**Veredicto: APPROVED**

Pasada 1 (`30cfcb4..23db6eb`): CHANGES_REQUESTED por los tests propios de F-004 pisados por el payload y por la
incoherencia de F-008 entre `current.md` y `features.json`. Lo aprobado allí (fusión de los seis adaptados) queda dado
por bueno; resumen abajo.

**Nivel de rigor:** `documental`, declarado en `features.json`. Exige C1–C3, C3 bis/ter si aplican y C5; sin fase
RED, cobertura ni mutación (C4 bis N/A por nivel). Carril `estandar`. `sdd: false`: se valida contra `acceptance`.

## Delta revisado

Siete ficheros: `tests/test_f004_settings_concepto_grafico.py` (nuevo), `progress/current.md`, `harness/features.json`
(+1 línea), `specs/F-008-registrar-factura/tasks.md`, `BACKLOG.md`, `progress/impl_F-019.md` y este informe. Nada de
código de la API ni del arnés: no invalida lo aprobado en la pasada 1.

1. **Tests de F-004 recuperados.** `diff` contra `git show 30cfcb4:tests/test_f004_settings.py`: **solo cambia la
   primera línea** (la ruta). Las 8 funciones `test_f004_r4_*`/`test_f004_r5_*` con sus nombres; `--collect-only` → 26
   tests (parametrizados), que explican el 6162 → 6188. El `tests/test_f004_settings.py` del arnés no se toca
   (`git diff 23db6eb..HEAD` vacío). Ejecutados junto a `test_estados.py` y `test_backlog_md.py`: 190 passed.
2. **Barrido de colisiones.** Lo repetí sobre **todo el repositorio**, no solo `tests/` y `scripts/`: ficheros de
   `30cfcb4` que no estaban en el payload 1.7.8 (`685da06`) = 359 propios; su cruce con el payload 1.10.1 da **una sola
   colisión, `tests/test_f004_settings.py`**, la ya recuperada. Coincide con el del implementer.
3. **F-008.** Mi cambio requerido 3 decía que faltaba T35 y que el destino era `in_review`: **era un error mío**, por
   leer un `current.md` desactualizado. Comprobado: `progress/review_F-008.md` abre con «Veredicto: APPROVED» (T21 en
   pasada 3, `8313ba0`; T35 en pasada 2, `fa0bfcf`; consolidada en `6483480`), y `625fb49`/`16a741c` son T34 y T34.5;
   los cinco commits existen y están en `dev`. `progress/verificacion_F-008.md` existe. El destino correcto es
   **`human_review`**, como corrigió el líder.
   Coherencia ahora: `features.json` = `spec_ready` + `spec_aprobada: "2026-10-30"`; `current.md` titula «`spec_ready`
   como aparcamiento», dice que se retoma en `human_review`, que la spec no se vuelve a presentar y qué manuales quedan;
   `tasks.md` marca T21, T34 y T35 `[x]` con sus commits, y deja `[ ]` T22-T25 (manuales), que es lo que lista
   `current.md`. `BACKLOG.md` al día (`backlog.py --comprobar` lo cubre el portero). Sin contradicciones.

## Resumen de la pasada 1 (sigue valiendo)

- Seis adaptados = payload 1.10.1 + **exactamente** las personalizaciones que tenían en `30cfcb4` (delta comparado
  línea a línea): reglas duras de Sigrid, mapa, markitdown, bloque de Ruesma, `RUTAS_PYTHON`, `RAMA_BASE=dev`,
  `COMANDO_TESTS=""`, §9, trampas de C3, índice de `docs/referencia/`. Sin `[ADAPTAR]` sueltos.
- Bloques genéricos de 1.7.16/1.8.0/1.9.0/F-070 presentes; resto del payload igual byte a byte; `.gitignore` completo;
  `rigor.json` no estaba afinado.
- Sin contradicciones entre `CLAUDE.md`, `CONVENTIONS.md` y `leader.md` (merges y push); el protocolo de `azure-apps`
  del proyecto es más estricto que el global y manda.
- `.claude/settings.json`: sin `PostToolUse`, `model`/`effortLevel`, allowlist del reviewer, hooks de energía y Stop.

## Checkpoints

| | |
|---|---|
| C1 `ARNES_SIN_CACHE=1 bash harness/init.sh` exit 0 | [x] exit 0, `ENTORNO LISTO`: 6188 passed, 47 skipped en 971 s (pasada 2, sin caché; sin servicios.json) |
| C1 ficheros base existen | [x] |
| C2 una sola activa | [x] solo F-019 (F-008 aparcada fuera de los activos) |
| C2 prioridad | [x] F-019 comprometida por el humano (alta del 2026-11-20) |
| C2 rama `feature/F-019-actualizar-arnes` | [x] |
| C2 `current.md` coherente | [x] F-008 coherente con `features.json` y `tasks.md` (punto 3) |
| C2 `done` con resumen en `history.md` | [x] sin cambios en `done` |
| C3 hexagonal, ruta en 1.ª línea, sin prints/secretos | [x] sin código de la API; el test recuperado lleva su ruta nueva |
| C3 trampas de Sigrid | [x] sin SQL ni escritura; las cinco trampas siguen en C3 |
| C3 bis | N/A: `docs/referencia/` no cambia en `30cfcb4..HEAD` |
| C3 ter | N/A: el entregable no atribuye afirmaciones a personas |
| C3 quater | N/A: F-019 no cambia lo que la API expone ni consume |
| C4 un test por `acceptance` | [x] 1: `harness/VERSION` leído por el portero; 2: `test_f070_r30_*`, `test_estados.py` (R31) y los recuperados `test_f004_r4/r5_*`; 3: `tests/test_f004_settings.py` del arnés; 4: el portero y este informe |
| C4 tests sin red ni BBDD | [x] |
| C4 MANUAL | N/A: F-019 no tiene verificaciones manuales |
| C4 bis (RED, cobertura, mutación, e2e) | N/A por nivel `documental` |
| C5 commits `F-019: …` | [x] todos los de la rama con el prefijo |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- C3 dice «tope de 1.000 filas»; el despliegue sirve 500.000 (`CLAUDE.md` global). Texto previo: otra feature.
- `current.md` arrastra pendientes de features cerradas (F-018, F-016, F-007, F-015): práctica previa; lo decide el líder.
- Al cerrar F-019, F-008 pasa a `human_review` y `estados --avisos` no avisará: ya tiene `spec_aprobada`.

## Automejora (propuesta, no aplicada)

- **Instalador (`arnes-base`):** los tests del arnés se nombran por F del arnés (`test_f004_*`, `test_f019_*`) y
  `tests/**` como `arnes_puro` pisa en silencio el homónimo de un proyecto. Si el destino existe y no estaba en el
  payload de la versión instalada, es propio: no pisar y avisar. A medio plazo, prefijo `test_arnes_*`.
- **`reviewer.md`:** en una actualización del arnés, barrer «modificado que no existía en el payload anterior».
- **`reviewer.md`:** el estado de otra feature se comprueba en su `review_F-XXX.md` y sus commits, no en `current.md`
  (lección de mi error en el punto 3 de la pasada 1).
