<!-- progress/review_F-018_C1C2C5.md -->
# Revisión F-018 · bloques C1, C2 y C5 (más «Evidencias», coherencia de estado y barrido)

Revisión completa (pasada 1) desde `6aca027` (`dev` = merge-base) hasta HEAD `7ce2240`. Reviewer, 2026-10-29.
Rigor declarado: **`critico`** (`harness/features.json`, entrada F-018). C3, C3 bis, C4, C4 bis y C4 ter **quedan
fuera** de este trozo (otros reviewers en paralelo). Nada contra Sigrid ni contra la API desplegada. No se ha editado
código, tests ni specs. `init.sh` ejecutado una vez, tal cual.

## Veredicto del bloque: **CHANGES_REQUESTED** (H1 y H2; arreglo de texto, sin tocar código)

C1 en verde y medido; las «Evidencias» casan con lo que he medido, incluidas las dos cifras de la red de R7 (reproducidas
en sus commits); topes de tamaño dentro; commits con convención y pie; sin secretos. Rechaza `progress/current.md`
(C2, H1): **sexta feature seguida** (F-010, F-011, F-015, F-007, F-016, F-018) con «Lo siguiente» y «Prompt para
retomar» atrasados. Y `features.json` (C5, H2) con un criterio `acceptance` que contradice la spec aprobada.

## Incidente provocado por este reviewer (leerlo antes que nada)

Por un error en un comando compuesto ejecuté `git checkout -q dev` **en el árbol principal**. El reflog lo fecha:
`13:23:30` pasa a `dev` (`6aca027`) y `13:23:44` vuelve a `feature/F-018-descuento-por-linea` (`7ce2240`), **14 s**.
Árbol y rama restaurados (`git status`: solo los informes sin trackear de los revisores en paralelo). Efectos: los ficheros
que difieren entre `dev` y la rama se reescribieron dos veces (mtimes nuevos, contenido idéntico al de HEAD). **Si algún
revisor en paralelo leyó ficheros o ejecutó tests entre las 13:23:30 y las 13:23:44, ese resultado midió `dev`, no
F-018, y debe repetirse.** El líder debería preguntar a los trozos `C3C4ter`, `docs`, `logica` y `mutacion`.
Lo mío: mis comandos son secuenciales y todo lo medido en el árbol principal antes de él (primer `init.sh`, recuentos)
lo precede; las cifras de la red de R7 salieron de worktrees en el scratchpad. Aun así repetí `init.sh` (C1).

## Cambios requeridos

1. **H1 · C2, `progress/current.md` tiene partes falsas hoy.**
   - `current.md:259-266`, «Prompt para retomar»: «**F-018** (descuento por línea) es la siguiente: spec en redacción
     en un worktree; enséñala al humano antes de implementar». Falso: spec v1.2 aprobada (P1-P11), T0-T17 hechas, el
     worktree ya no existe (`git worktree list`: solo el árbol principal). Una sesión que lo siga volvería a la PARADA 1.
   - `current.md:248-257`, «Lo siguiente en el backlog»: «su spec se está redactando en un worktree aparte [...] se
     pasa a `spec_ready` y se enseña al humano cuando F-016 esté cerrada». Falso por lo mismo.
   - `current.md:23-46`, dos secciones de F-018 en imperativo y contradichas por la de `:4`: «**No se empieza T1 hasta
     tener los acuses.**» (`:35-36`) y «Siguiente: T0 [...] y sus acuses» (`:46`). Los acuses llegaron
     (`impl_F-018.md:12`) y no constan aquí.
   - `current.md:84-88` (F-016): «cambios de texto pedidos [...] en corrección. Después: veredicto consolidado [...]
     merge a `dev`, despliegue». Contradice `:48-55` (F-016 aprobada, mergeada y **desplegada** el 2026-10-28).
   - Requerido: reescribir prompt y «Lo siguiente» al estado real (F-018 `in_progress`, T18 revisión troceada en curso;
     después veredicto consolidado, merge a `dev`, despliegue que lanza el humano, T19 previas del líder, T20 grabación
     con autorización expresa y avisos a `albaranes`/`proformas`, T21; F-016 `blocked` con T17-T18; luego F-008);
     condensar `:23-46` en una línea histórica con los acuses, y dejar `:84-88` en pasado. Los bloques heredados con
     pendientes vivos (F-007, F-015, F-009 T24, F-006, arnés, configuración) **no** son lo que se rechaza.
2. **H2 · C5, `harness/features.json` (F-018) no refleja la spec aprobada.**
   - `acceptance[1]`: «Sin dto o con dto 0 [...] se comportan exactamente igual que antes (tests y dorados de F-007,
     F-009, F-015 y F-016 sin tocar)». Contradice R7 y R15 (`requirements.md:38-42`, `:67-71`): una vinculada sin `dto`
     contra un `ctrpro` con dto legible **cambia** (copia el dto, P5), la proforma lo hereda (R21-R22, P8), y P9-P11
     tocan tres líneas de `test_f009_models.py`/`test_f016_models.py` (`cd68b11`). Tal como está, el criterio no se
     cumple nunca y bloquearía el `done` en literal.
   - `description`: «A decidir en la spec [...] si aplica a sigrid/proforma» y el `title` «y, si aplica, en
     sigrid/proforma»: decidido en v1.2 (la proforma no admite `dto`, R20, pero hereda R15).
   - Requerido: reescribir `acceptance[1]` con R7 («sin dto efectivo, igual que antes; salvo R15 y las tres líneas de
     P9-P11») y añadir una frase de v1.2 a la `description`; regenerar `BACKLOG.md` con `harness/backlog.py`.

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh`, **ejecución que vale: 13:29:53-13:32:57** sobre `ba5abbc` (= `7ce2240` + los cuatro
  informes de los revisores en paralelo; reflog sin cambio de rama en ese intervalo): **exit 0**, «ENTORNO LISTO.
  Puedes trabajar.». `3793 passed, 1 skipped, 1 warning in 158.52s` (la primera, sobre `7ce2240` y anterior al
  incidente, dio lo mismo en 192,26 s); PUERTA COBERTURA `[OK]` 100.0 % de 102 líneas (102/102, umbral 80 %, critico); PUERTA TAMAÑO
  `[OK]` (requirements 135/150, design 242/250, impl **219/220**); BACKLOG al día; `features.json` y `rigor.json`
  válidos; rama correcta. Avisos: F-015/F-016 `blocked` (esperado) y ruff 79 (deuda previa, igual que en F-016).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`, `progress/history.md`,
  `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` (los `[OK] Existe` de `init.sh`).

## C2 — El estado es coherente

- [x] Una sola `in_progress`: F-018 (`init.sh`: «18 features, 8 abiertas, en curso: ['F-018'], bloqueadas:
  ['F-015', 'F-016']»). `done`: F-002..F-007, F-009..F-012.
- [x] Rama `feature/F-018-descuento-por-linea`, la de `features.json` (no `main`); `dev` (`6aca027`) es ancestro de HEAD.
- [ ] `progress/current.md` describe solo la sesión activa y sin partes falsas: **H1**.
- [x] Toda `done` tiene su sección en `progress/history.md` (l. 8, 51, 108, 153, 183, 224, 272, 297, 322, 342).

| Fuente | Estado de F-018 | ¿Coherente? |
|---|---|---|
| `features.json` | `in_progress`, `critico`, `sdd`, prioridad 9, rama correcta | estado sí; texto no (H2) |
| `BACKLOG.md` | «En curso: **F-018**» (l. 8, 18, 54); `backlog.py --comprobar` → exit 0 | sí |
| `tasks.md` | T0-T17 `[x]`; T18 (esta revisión), T19-T20 MANUAL y T21 `[ ]` | sí |
| `impl_F-018.md` | T1-T17 hechas; T18-T20 pendientes; acuses de T0 en l. 12 | sí |
| `current.md:4-21` | T1-T17, siguiente T18, V0-V5 con quién las lanza | sí |
| `current.md:23-46`, `:84-88`, `:248-266` | «no se empieza T1», «Siguiente: T0», spec «en redacción» | **no** (H1) |

## C5 — La sesión se cerró bien

- [ ] (no bloquea el APROBADO) `tasks.md` con todas `[x]`: T18 es esta revisión; T19-T20 son MANUAL (previas tras el
  despliegue y un `commit:true` autorizado); T21 es el `init.sh` de cierre. Criterio de F-010/F-011/F-015/F-007/F-016,
  aceptado por el humano: **bloquean el `done`, no el APROBADO para merge.**
- [x] Un commit `F-018 Tn:` por tarea hecha: T0 `02dc4ad` (+ `7aae0ba`, texto de `albaranes`), T1 `99a7ee6`, T2
  `9cd79ad`, T3 `e9ad53e` + `cd68b11` (las tres líneas en commit propio, como pide la spec), T4 `3ed597e`, T5 `46767ac`,
  T6 `be77bd3`, T7 `7e92940`, T8 `007f965`, T9 `bfa2b38`, T10 `09ba32d`, T11 `f53f382`, T12 `f9b4520`, T13 `3b238c1`,
  T14 `4ea35bb` + `24e785a` + `7ce2240`, T16 `536ce9c`; T15 y T17 juntas en `e649e38` (T15 es `azure-apps` `f168a36`,
  existe y toca solo `sigrid_api.md`). Ningún commit mezcla código de dos tareas. `6d11dcd` (F-007, doc de F-016
  desplegada) vive en la rama y está declarado en `impl_F-018.md`: entra en `dev` con F-018, sin bloqueo.
- [x] Mensajes: los 30 commits sin merge de `dev..HEAD` en español y **todos** con `Co-Authored-By: Claude Opus 5.5
  <noreply@anthropic.com>`; `Claude-Session` en 25 (faltan en los 5 últimos: el pie vigente no lo exige).
- [x] Sin temporales ni artefactos de F-018: `git status --short` solo lista los informes de los revisores en paralelo
  (`review_F-018_{C3C4ter,docs,logica,mutacion}.md`). Lo `--ignored` (`.txt`, `.csv`, terraform, `.pem`, `.zip`) es
  anterior y ajeno, ya anotado en F-016. `git worktree list`: solo el árbol principal (los míos, retirados).
- [x] `features.json` refleja el **estado** real: `in_progress` con T18-T21 abiertas (texto: H2).

## «Evidencias» (`impl_F-018.md:208-219`) contra lo medido

| Evidencia | Medido por este reviewer | ¿Casa? |
|---|---|---|
| 3.793 passed, 1 skipped (sobre `e649e38`) | `init.sh` sobre `7ce2240`: idéntico; `e649e38..7ce2240` solo toca `progress/` y `tasks.md` | sí |
| 243 tests F-018 (50/100/38/12/43) | `pytest --collect-only` por fichero: 50, 100, 38, 12, 43 = 243 | sí |
| Red R7: 1.484 (T1) → 1.525 (T10) | worktrees en el scratchpad: `9886967` → **1484 passed**; `09ba32d` (+ `test_f018_use_case/proforma`) → **1525 passed** | sí |
| Cobertura 100 % (102/102) | PUERTA COBERTURA: idéntico | sí |
| Mutación 66 / 66 / 0 / 0 | `mutacion_F-018.md`: SHA `e649e384…`, 1.637,7 s, base 136,7 s, media 24,8 s, Workers 1 | cifras del informe (la verificación independiente es de C4 bis) |
| Suite 187,08 s | 192,26 s (revisores en paralelo) | sí |
| Ruff «All checks passed» | sobre los tres `.py` de producción, `tests/test_f018_*` y los dos tests tocados: sí. `function_app.py` da 3 avisos, los tres en líneas de `e903394` (`git blame`) | sí |

Para el trozo C4 bis: la tabla «Evidencias» **no trae la fila de workers** que pide C4 bis (sí está en el título de
§T14, `--workers 1`, y en `mutacion_F-018.md`). El SHA medido (`e649e38`) es anterior a HEAD, pero el delta no toca
`.py`. Que decida allí si basta.

**Barrido de datos sensibles** sobre `current.md`, `impl/explore/mutacion_F-018.md`, `specs/F-018-*/*.md`, los dos
contratos y `tests/test_f018_*.py`, con `grep -iE`: `password|secret|api[_-]?key|code=|token|azurewebsites|AccountKey|
Server=|UID=|PWD=`, IPv4, GUID, correos `.es/.com/.net/.org`, CIF/NIF/NIE. Resultado: **nada real**. Solo placeholders
de los contratos (`B00000000`, `ALB-3f2b9c1e-0000-4000-8000-…`) y un código de partida que parece IP. La clave de
`verificacion_manual.md` se lee con `az functionapp keys list` a `$env:` y la URL es `<URL base …>`. Los ficheros
nuevos de código y de `progress/` llevan la primera línea con su ruta; `git diff --check`: solo una línea en blanco
final en `mutacion_F-018.md` (generado por la herramienta).

## Resumen para el líder

- Rechazan **H1** (`current.md`) y **H2** (`features.json` + regenerar `BACKLOG.md`): texto, en un commit, sin tocar
  código ni `impl_F-018.md` (está a 219/220).
- `init.sh` en verde (13:29:53-13:32:57, sobre `ba5abbc`); «Evidencias» casan, red de R7 reproducida; T18-T21 abiertas bloquean el `done`,
  no el merge.
- **Comprobar con los trozos paralelos la ventana 13:23:30-13:23:44** (incidente de arriba).

## Automejora (propuesta, no aplicada)

- **Sexta** feature rechazada en C2 por «Prompt para retomar» atrasado. Tercera vez que se propone: aviso de `init.sh`
  si «Prompt para retomar» no nombra la feature `in_progress` y su última tarea `[x]`. Vale para `arnes-base`.
- **Prohibir `git checkout`/`git switch` a los reviewers en el árbol principal** (regla en `reviewer.md` y, mejor, una
  regla `deny` en `.claude/settings.json` para el subagente): en una revisión troceada, un cambio de rama de segundos
  invalida en silencio lo que miden los demás trozos. Lo medido en otra versión, siempre en un worktree. Para `arnes-base`.
