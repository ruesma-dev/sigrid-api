<!-- progress/review_F-015_C1C2C5.md -->
# Revisión F-015 · bloques C1, C2 y C5 (más «Evidencias» y `proveedor_sin_albaran_previo`)

Revisión completa (pasada 1) desde `6faacd7` (`dev` = merge-base) hasta HEAD `e42e0ad`. Reviewer, 2026-10-24.
Rigor declarado: **`critico`** (campo `rigor` de `harness/features.json`). C3, C3 bis, C4, C4 bis y C4 ter
**quedan fuera** de este trozo (otras revisiones). Nada contra Sigrid: ni lecturas ni escrituras (todo lo que
dependa de Sigrid aquí es N/A porque este bloque no lo necesita y el encargo lo prohíbe). No se ha editado código
ni specs.

## Veredicto del bloque: **CAMBIOS** (H1 bloquea; H2 y H3 son de texto, para el mismo arreglo)

C1 en verde y medido. Rechaza `progress/current.md` (C2, H1): el mismo defecto que ya rechazó F-010 y F-011. Las
tareas MANUAL T19-T21 abiertas no deciden el veredicto (criterio de F-010/F-011, ver C5).

## Cambios requeridos

1. **H1 · C2, `progress/current.md` tiene partes falsas hoy y no describe solo la sesión activa.**
   - `progress/current.md:192-197`, «Prompt para retomar»: no dice que F-015 está `in_progress` y la mete en «Lo
     siguiente del backlog (F-007, F-008, F-013, F-014, F-015): no arranques nada sin preguntar». Una sesión que siga
     ese prompt ignoraría una feature con la implementación terminada, la revisión en curso y T19-T21 por hacer
     (y el aviso a albaranes previo al despliegue).
   - `progress/current.md:182-188`, «Lo siguiente en el backlog»: lista F-015 entre lo que viene «Después», como
     «dada de alta el 2026-10-18».
   - `progress/current.md:42` y `:53`: título «F-008 y F-015 esperan (2026-10-19)» y viñeta «F-015 [...] spec v2
     arriba»: superado desde `cb93995` (in_progress) y `e42e0ad` (implementer terminado).
   - Requerido: reescribir el prompt y «Lo siguiente» para el estado real (F-015 `in_progress`, revisión troceada en
     curso, después avisar a albaranes, desplegar y T19-T21 con quién lanza cada una) y quitar F-015 del título y
     la viñeta de l. 42-54. Los bloques heredados con pendientes vivos (F-009 T24, F-006, decisiones del arnés) se
     dejan: no son lo que rechaza.
   - **De paso, para el trozo de C4** (no es de este bloque): `current.md:15-17` dice «Quedan T19-T21 MANUALES»
     sin el **comando exacto** que pide C4; `tasks.md` T19 solo dice «`Invoke-RestMethod` a `/api/sigrid/albaran`
     con `commit:false`». Arreglarlo con H1 cierra los dos.
2. **H2 · Informe, `progress/impl_F-015.md:18`**: «Sin respaldo, el alta sigue (`template_ide` 0); sale
   `proveedor_sin_albaran_previo`». Se lee como «se emite», y es lo contrario de lo que hace el código (ver la
   comprobación abajo). Requerido: «se retira `proveedor_sin_albaran_previo`» o equivalente. No es un fallo de
   código: es el registro de la feature diciendo algo falso por ambigüedad.
3. **H3 · Informe, `progress/impl_F-015.md:47`**: «T1-T18 de `f8deb5e` a `b369a7f` (uno por tarea; T15 es solo una
   comprobación)». El primer commit del tramo es `7f4c488` (T2, antes que T1 por la desviación declarada); T18
   tiene dos commits (`97c4e8b`, `b369a7f`); T15 no tiene commit propio y se marcó `[x]` dentro de `c0e40ef`
   (mensaje «T14», que no la nombra). Requerido: decirlo así en el informe. El hecho en sí se acepta (ver C5).

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` ejecutado una vez, tal cual, sobre `e42e0ad`: **exit 0**, «ENTORNO LISTO».
  `2871 passed, 1 skipped, 1 warning in 174.56s`; PUERTA COBERTURA `[OK]` 100.0 % de 237 líneas (237/237, umbral
  80 %, critico); PUERTA TAMAÑO `[OK]` (requirements 134/150, design 237/250, impl 180/220); BACKLOG al día;
  `rigor.json` válido; rama correcta. Único aviso: ruff, 79 avisos de deuda previa (no bloquea).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`,
  `progress/history.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` (`ls` y los `[OK] Existe` de `init.sh`).

## C2 — El estado es coherente

- [x] Una sola `in_progress`: F-015. `done`: F-002..F-006, F-009..F-012; `pending`: F-001, F-007, F-008, F-013,
  F-014.
- [x] Rama `feature/F-015-albaran-plantilla-y-retencion`, la que declara `features.json` (no `main`).
- [ ] `progress/current.md` describe solo la sesión activa y sin partes falsas: **H1**.
- [x] Toda `done` tiene su sección en `progress/history.md` (l. 8, 51, 108, 153, 183, 224, 272, 297, 322: F-002,
  F-003, F-004, F-005, F-006, F-009, F-010, F-011, F-012).

| Fuente | Estado de F-015 | ¿Coherente? |
|---|---|---|
| `harness/features.json` | `in_progress`, `critico`, `sdd`, rama correcta | sí |
| `BACKLOG.md` | «En curso: F-015», fila y ficha «en curso»; `python harness/backlog.py --comprobar` → exit 0 | sí |
| `tasks.md` | T0-T18 y T22 `[x]`; **T19, T20, T21 `[ ]`** (las tres MANUAL) | sí |
| `impl_F-015.md:5` | «T1-T18 y T22 hechas; T19-T21 MANUALES, sin marcar» | sí |
| `current.md:4-35` | in_progress, implementer terminado, quedan T19-T21 y la revisión | sí |
| `current.md:42-54`, `:182-197` | F-015 «espera», «dada de alta», «no arranques nada» | **no** (H1) |

## C5 — La sesión se cerró bien

- [ ] (no bloquea el APROBADO) `tasks.md` con todas `[x]`: **T19, T20 y T21 abiertas**, y deben estarlo: son
  MANUAL posteriores al despliegue (dry-runs R29, grabación autorizada, limpieza R30), y no se despliega sin merge
  ni se mergea sin APROBADO. Mismo choque conocido y mismo criterio que F-010 y F-011 (`review_F-011_C1C2C5.md`,
  aceptado por el humano): **bloquean el `done`, no el APROBADO para merge.** T21 escribe en producción y exige
  autorización expresa; T19 debe ir tras avisar a albaranes (`current.md:7-8`).
- [x] Un commit `F-015 Tn:` por tarea hecha: T1 `f8deb5e`, T2 `7f4c488`, T3 `e7bc324`, T4 `b4a8cd6`, T5 `e7b6c1f`,
  T6 `7e0300d`, T7 `6743724`, T8 `72d82b4`, T9 `12247ff`, T10 `a0345d9`, T11 `079c913`, T12 `b4234d3`, T13
  `8166ed6`, T14 `c0e40ef`, T16 `719d724`, T17 `40f1425` (+ `49dfb36` en `azure-apps`), T18 `97c4e8b` y `b369a7f`,
  T22 `e42e0ad`. Excepciones aceptadas: **T15** (comprobación sin código, solo la marca, dentro de `c0e40ef`;
  mismo criterio que F-011 T7-T8 y F-010 T9-T10, salvo que el mensaje no la nombra: H3); **T0** con formato
  `F-015:` y no `F-015 T0:` (`871cc0c` el texto v8.3 sin código, comprobado con `git show --stat`; `67927eb` la
  corrección del `usu`; `cb93995` la marca y el paso a `in_progress`): tarea de fase de spec, anterior a la rama
  de implementación; no lo hago bloqueante.
- [x] Sin temporales ni artefactos sin trackear de la feature. `git status --porcelain` vacío antes y después de
  `init.sh`. En `--ignored`, lo único posterior al 2026-10-20 es `.coverage` (lo regenera `init.sh`); los
  `.txt`/`.csv`/terraform son anteriores y ajenos. El fichero suelto `` `0`].{t `` ya no está.
  **Fuera del árbol**: worktree `C:/Users/pgris/PycharmProjects/sigrid-api-mut-F015` en `e42e0ad` (detached),
  creado a las 15:03, después del último commit (14:57): es de la revisión de mutación en paralelo, no del
  implementer. Quien lo creó debe hacer `git worktree remove` antes del merge.
- [x] `features.json` refleja el estado real: `in_progress` es lo correcto con T19-T21 abiertas.

## «Evidencias» contra lo medido

| Evidencia del informe | Medido por este reviewer | ¿Casa? |
|---|---|---|
| Suite 2871 passed, 1 skipped, 0 failed | `init.sh` sobre `e42e0ad`: idéntico | sí |
| F-015: 167 tests (+ `test_f015_r26` en equivalencia) | `--collect-only` de los dos ficheros: 167; el r26 existe en `test_f009_equivalencia.py` | sí |
| F-009: 582 tests (7 ficheros) | `--collect-only` de los mismos 7: 582 | sí |
| Cobertura 100.0 % de 237 (237/237) | PUERTA COBERTURA: idéntico | sí |
| Mutación ronda 2: 104/104/0/0, 1602,5 s, `--workers 1`, HEAD `97c4e8b` | `mutacion_F-015.md`: mismas cifras, SHA `97c4e8be…`, Workers 1, base 156,3 s, media 15,4 s (104 × 15,4 = 1601,6 ≈ 1602,5) | sí (la verificación independiente de la campaña es del trozo C4 bis) |
| Tamaño: requirements 134/150, design 237/250 | idéntico (impl 180/220) | sí |
| Tiempo de la suite 133,81 s | 174,56 s en esta ejecución | sí: carga distinta (reviewers en paralelo); no es un número que se pueda reproducir |

Desde el SHA medido por la campaña (`97c4e8b`) hasta HEAD solo cambian `progress/*`, `current.md` y `tasks.md`
(`git diff --stat 97c4e8b..HEAD`): el alcance de producción medido es el revisado. Commits citados en el informe
(`67927eb`, `c0e40ef`, `72d82b4`, `49dfb36`, `97c4e8b`, `40f1425`, `b369a7f`) existen y dicen lo que el informe
les atribuye, salvo el rango de l. 47 (H3).

## ¿Se retira de verdad `proveedor_sin_albaran_previo`?

**Sí, en el código**; lo falso es solo la frase del informe (H2).

- `domain/models/albaran_compra_models.py`: ya no está en `CODIGOS_CABECERA` (en `dev`, l. 48, sí estaba); y
  `AlbaranCompraError` rechaza todo código fuera de esa lista (l. 152-156), así que **no puede emitirse**.
- Ninguna aparición en `application/`, `domain/`, `infrastructure/` ni `function_app.py` (Grep del árbol, sin
  `progress/`).
- Tests: `tests/test_f009_models.py:440` lo pone en la lista de rechazados (`ValueError «no es un codigo»`) y la
  lista cerrada de l. 385-400 ya no lo trae; `tests/test_f009_use_case.py:177-180` conserva el nombre del caso
  pero ahora comprueba que el alta sigue con `("previsto", 0)`.
- Documentos: `contrato_albaranes.md:358` lo tacha («retirado en la v8.3»), `azure-apps/sigrid_api.md:1096-1097`
  dice «se retira». Las menciones de `specs/F-009-*/design.md:218` y `requirements.md:46` son la spec histórica de
  F-009 y no se tocan.

## Resumen para el líder

- Rechaza **H1** (`current.md` l. 42-54 y 182-197): arreglo de minutos; aprovechar para listar T19-T21 con su
  comando exacto (C4). H2 y H3 son dos frases del informe.
- `init.sh` en verde sobre `e42e0ad` y las «Evidencias» casan con lo medido.
- T19-T21 abiertas: bloquean el `done`, no el merge (precedente F-010/F-011).
- Retirar el worktree `sigrid-api-mut-F015` antes del merge.

## Automejora (propuesta, no aplicada)

- Tercera feature seguida (F-010, F-011, F-015) rechazada en C2 por «Lo siguiente» y «Prompt para retomar»
  atrasados. Insisto en la propuesta de `review_F-011_C1C2C5.md`: paso fijo del líder en `leader.md` al lanzar y al
  recibir al implementer, y aviso de `init.sh` si la feature `in_progress` no aparece en «Prompt para retomar».
  Vale para `arnes-base`.
