<!-- progress/review_F-011_C1C2C5.md -->
# Revisión F-011 · bloques C1, C2 y C5 (más la incidencia de `dev` y `azure-apps`)

Revisión completa (pasada 1) del estado de la rama, `git diff e153b39..4d1c266` (`dev`...HEAD), y de
`azure-apps` `7bddfd4`. Reviewer, 2026-10-18. Rigor declarado: **`critico`** (campo `rigor` de
`harness/features.json`). C3, C3 bis, C4, C4 bis y C4 ter **quedan fuera** de este trozo (otras
revisiones). No se ha ejecutado `init.sh` ni la suite completa, por orden expresa del encargo (hay una
campaña de mutación en paralelo). Tampoco se ha ejecutado ningún test: este bloque no lo necesitaba.

## Veredicto del bloque: **CHANGES_REQUESTED** (1 hallazgo, de arreglo corto)

Lo que rechaza es `progress/current.md` (C2, H1): lo mismo que se rechazó en F-010 (`review_F-010_C1C3C5.md`
H2). Lo demás de C1, C2 y C5 está en orden, salvo el choque conocido de las tareas MANUAL (ver C5), que
**no** decide este veredicto.

## Cambios requeridos

1. **H1 · C2, `progress/current.md` tiene partes falsas hoy y no describe solo la sesión activa.**
   - l. 134-142, «Lo siguiente en el backlog»: dice que F-011 está «dada de alta en `pending`» y que su
     spec «espera a que el humano decida D1 [...], D2 [...], D3 y D4». Falso desde `24930a7`: D1-D4 están
     aprobadas (lo dice el propio fichero en l. 13-15) y F-011 está `in_progress` con T1-T11 y T15 hechas.
   - l. 144-149, «Prompt para retomar»: no dice que F-011 está `in_progress` y la mete en «lo siguiente
     del backlog [...] no arranques nada sin preguntar». Una sesión nueva que siga ese prompt ignoraría
     una feature a medias con T12-T14 pendientes (y T12 es la previa que, si falla, obliga a PARAR antes
     de desplegar: con A1, una base fuera del patrón tumbaría el endpoint que la use).
   - l. 4, título «spec aprobada, implementer lanzado»: superado (el implementer ya terminó).
   - Requerido: reescribir el título de F-011, «Lo siguiente» y el prompt para el estado real (F-011
     `in_progress`, revisión en curso, T12-T14 MANUAL pendientes y quién lanza cada una). Los bloques
     heredados de F-009 (l. 23-48) y F-006 (l. 50-71) se dejan como en `dev` si el humano los mantiene por
     sus pendientes vivos (T24, anular `RS26.09/0439`); no son lo que rechaza.
   - **De paso, para el trozo de C4** (no es de este bloque): `current.md` **no lista** T12-T14 con su
     comando exacto (solo «Quedan T12-T14 (MANUAL)», l. 8), que es lo que pide el tercer punto de C4. Están
     en `impl_F-011.md` §«Fuera del alcance». Moverlos a `current.md` con el arreglo de H1 cierra los dos.

## C1 — El arnés está completo y en verde

- **N/A** `bash harness/init.sh` termina con exit 0: **no ejecutado por orden expresa del encargo**
  (campaña de mutación en paralelo). El implementer declara ENTORNO LISTO en T15 (`2664 passed, 1
  skipped`, cobertura 16/16, tamaño en verde; `.coverage` y `coverage.json` del árbol son de 09:41, la
  hora de `4d1c266`). Este trozo **no lo certifica**: debe ejecutarlo quien cierre la revisión, sobre la
  punta final.
- [x] Existen los siete ficheros base (`CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
  `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`),
  comprobado con `test -f`.

## C2 — El estado es coherente

- [x] Una sola `in_progress`: F-011 (las demás: F-002..F-006, F-009, F-010 `done`; F-001, F-007, F-008
  `pending`).
- [x] Rama actual `feature/F-011-documents-read-valida-database`, la de `features.json` (no `main`).
- [ ] `progress/current.md` describe solo la sesión activa: **H1**.
- [x] Toda `done` tiene su sección en `progress/history.md` (F-002, F-003, F-004, F-005, F-006, F-009 y
  F-010: l. 8, 51, 108, 153, 183, 224 y 272).

Coherencia entre las fuentes (lo que pedía el encargo), medida:

| Fuente | Estado de F-011 | ¿Coherente? |
|---|---|---|
| `harness/features.json` | `in_progress`, `critico`, `sdd`, rama correcta, título ampliado | sí |
| `BACKLOG.md` | «En curso: F-011», fila y ficha «en curso»; `python harness/backlog.py --comprobar` → exit 0 (al día) | sí |
| `tasks.md` | T1-T11 y T15 `[x]`; T12-T14 `[ ]` (MANUAL) | sí |
| `impl_F-011.md` | «Hechas T1-T11 y T15; T12-T14 son MANUAL y siguen abiertas» | sí |
| `current.md` l. 4-21 | T1-T11 y T15 hechas, quedan T12-T14 y el reviewer | sí |
| `current.md` l. 134-149 | F-011 en `pending`, D1-D4 sin decidir | **no** (H1) |

## C5 — La sesión se cerró bien

- [ ] `tasks.md` con todas las tareas `[x]`: **T12, T13 y T14 abiertas.** Aplicado `CHECKPOINTS.md` tal
  cual, esto es un `[ ]`. Son MANUAL (T12 lectura previa al despliegue, T13 despliegue que lanza el
  humano, T14 verificación desplegada) y **no se pueden hacer antes del merge**: T13 despliega `dev`, y
  a `dev` no se mergea sin APROBADO. Es el choque conocido (propuesta de F-010, encargo
  `ENCARGO_pendiente_C5_admite_manual_pendiente.md` en `arnes-base`, `current.md` l. 98-99).
  **Qué bloquea qué:**
  - Por la letra de `CHECKPOINTS.md`, este `[ ]` bloquearía también el APROBADO; pero exigirlo haría
    imposible aprobar nunca una feature con despliegue, y el precedente de F-010 (APROBADO para merge con
    T13-T15 abiertas, aceptado por el humano) lo trató como bloqueante **solo del `done`**. Ese es el
    criterio que aplico: **T12-T14 bloquean el `done`, no el APROBADO para merge.** Que el humano lo dé
    por bueno otra vez o cierre el encargo de `arnes-base`.
  - Ojo con T12: aunque no bloquee el merge, **sí bloquea el despliegue (T13)**. Es la que dice PARAR si
    `ALLOWED_DATABASES`, `ALLOWED_WRITE_DATABASES` o `SIGRID_DOCUMENT_WRITE_DATABASE` no casan con
    `^[A-Za-z_][A-Za-z0-9_]*$`.
  - **Lo que sí bloquea el APROBADO en este trozo es solo H1**, que no depende de nada manual.
- [x] Un commit `F-011 Tn:` por tarea hecha: T1 `6defcad`, T2 `9929e69`, T3 `adbc2ec`, T4 `bcfd5db`, T5
  `b76c403`, T6 `2583cb7`, T9 `0b9476e`, T10 `0924530`, T11 `c054db9` (+ `7bddfd4` en `azure-apps`), T15
  `4d1c266`. **T7-T8 comparten `cafc340`**: dos verificaciones sin código (solo marcan `tasks.md`), mismo
  criterio aceptado en F-010 (`2bcda71`, T9-T10). Hay un commit extra sin tarea, `0cba54a` (`F-011: test de
  la ruta sin el aviso ISC004`), solo `tests/test_f011_ruta.py`, explicado en el informe: correcto.
  T12-T14 sin commit, por abiertas (punto anterior).
- [x] Sin ficheros temporales ni artefactos sin trackear **de la feature**. `git status --short`: solo
  `` `0`].{t `` (vacío, 2026-09-24 12:31, anterior a la rama, ya anotado como ajeno en `current.md`
  l. 70-71). `git status --ignored`: lo de siempre (`.txt`/`.csv` de junio-julio, `__pycache__`,
  `coverage.json`, terraform), nada nuevo de F-011. **Fuera del árbol, a limpiar al cerrar la revisión**
  (no son del implementer, son de las revisiones en paralelo): dos worktrees en el scratchpad de esta
  sesión, `wt` (rama `review-f011-mut`) y `wt_rojo` (rama `review-f011-rojo`), ambos sobre `4d1c266`. Quien
  los creó debe hacer `git worktree remove` y `git branch -D` de esas dos ramas antes del merge.
- [x] `features.json` refleja el estado real: `in_progress` es lo correcto con T12-T14 abiertas.

## Incidencia declarada: `git checkout dev` accidental

Comprobado, **sin efecto**:

- `git rev-parse dev` = `e153b39dc90c0d4f4e5f34e57e69cd65cf56f712`; `git diff e153b39 dev` vacío.
- `git reflog show dev`: la última entrada sigue siendo `dev@{0}` = el merge de F-010 (`e153b39`, 00:50).
  Ningún commit, reset ni merge en `dev` después.
- `git reflog` de HEAD: `HEAD@{3}` checkout a `dev` y `HEAD@{2}` vuelta a la rama en `c054db9`, sin
  nada entre medias; después solo `0cba54a` y `4d1c266`, ambos en la rama.
- `git stash list` vacío (no se escondió nada al cambiar). `main` sigue en `2a5ac24` (`main@{0}` es el
  fast-forward de siempre).

## `azure-apps`

- [x] `7bddfd4` existe en `master` (09:34:24), único commit posterior a `bdc8ec0` (F-010 desplegada y
  verificada, 00:42, ya explicado en esa feature). **No hay nada más suyo sin explicar.**
- Toca **solo** `sigrid_api.md` (+45 −4). Mensaje con el formato `sigrid-api: ...` de ese repo, cita
  F-011 y «pendiente de despliegue», con `Co-Authored-By`.
- Árbol limpio (`git status --short` vacío), sin stash, sin remoto (sin push, como debe).
- Barrido de sensibles sobre el diff de `7bddfd4` (patrones: `password|pwd=|secret|token|accountkey|
  sharedaccess|code=`, IPv4, prefijo de GUID, correos): solo el correo del autor del commit y el
  `Co-Authored-By`. Sin secretos. La fidelidad del texto al código la juzga el trozo de C3/R16.

## Resumen para el líder

- Rechaza **solo H1** (`current.md` l. 4 y 134-149). Arreglo de minutos; sugerido junto con listar
  T12-T14 con su comando exacto (C4, otro trozo).
- T12-T14 abiertas: `[ ]` literal en C5, que trato como bloqueante del `done` y no del merge (precedente
  F-010). T12 bloquea además el despliegue.
- `dev` intacto en `e153b39`; `azure-apps` con `7bddfd4` y nada más.
- `init.sh` no certificado aquí (prohibido por el encargo): que lo ejecute el cierre.
- Limpiar los worktrees `review-f011-mut` y `review-f011-rojo` antes del merge.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C2 «`current.md` solo la sesión activa» ha rechazado ya dos features seguidas (F-010 y
  F-011) por la **misma** causa: «Lo siguiente en el backlog» y «Prompt para retomar» se quedan atrás
  cuando la feature avanza. Propuesta para `arnes-base`: que el líder reescriba esas dos secciones como
  paso fijo al lanzar el implementer y al recibir su informe (en `leader.md`), y que `init.sh` avise si
  la feature `in_progress` de `features.json` no aparece en la sección «Prompt para retomar».
