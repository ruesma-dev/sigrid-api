<!-- progress/review_F-007_C1C2C5.md -->
# Revisión F-007 · bloques C1, C2 y C5 (más «Evidencias», commits y worktrees)

Revisión completa (pasada 1) desde `60db955` (`dev` = merge-base) hasta HEAD `fe85523`. Reviewer, 2026-10-26.
Rigor declarado: **`critico`** (campo `rigor` de `harness/features.json`). C3, C3 bis, C4, C4 bis y C4 ter
**quedan fuera** de este trozo (otros reviewers en paralelo). Nada contra Sigrid ni contra la API desplegada. No
se ha editado código, tests ni specs; ningún commit. `init.sh` ejecutado una sola vez, tal cual.

## Veredicto del bloque: **CHANGES_REQUESTED** (H1 bloquea; H2 es de una línea)

C1 en verde y medido; las «Evidencias» casan con mi ejecución. Rechaza `progress/current.md` (C2, H1): **cuarta
feature seguida** (F-010, F-011, F-015, F-007) con «Lo siguiente» y «Prompt para retomar» atrasados. T20-T22
(MANUAL) abiertas no deciden el veredicto (criterio de F-010/F-011/F-015, ver C5).

## Cambios requeridos

1. **H1 · C2, `progress/current.md` tiene partes falsas hoy y no describe solo la sesión activa.**
   - `current.md:268-278`, «Lo siguiente en el backlog»: «**F-015 está `in_progress`** [...] sigue la **pasada 2
     de la revisión**; después, avisar a albaranes, el despliegue [...] Hasta cerrarla no se arranca otra
     feature» y «Después de F-015: F-007 [...] `pending`». Falso: F-015 está `blocked`, aprobada, desplegada y
     verificada (`current.md:4-11`); F-007 está `in_progress` con T1-T19 hechas.
   - `current.md:280-288`, «Prompt para retomar»: manda retomar la pasada 2 de F-015 y dice que F-007 está
     «`spec_ready`, pendiente de la PARADA 1». Una sesión que lo siga ignoraría F-007 entera (revisión en curso,
     avisos sin mandar, T20-T22) y repetiría una revisión ya aprobada.
   - `current.md:105-106`: «`harness/features.json` sigue con F-015 en `in_progress`»: ya no (es `blocked`).
   - `current.md:16-17`, `:19-20` y `:43-44` (bloque de F-015): «Antes de desplegar: avisar a albaranes»,
     «Mientras no se despliegue [...]» y «Lo siguiente: merge a `dev`, aviso a albaranes, despliegue y T19-T21»:
     superados por la cabecera `:4` («desplegada y verificada»). Dejar solo lo que sigue vivo al desbloquear.
   - `current.md:89-90`: D4 termina en «Confirmar.», pero `:59` dice que la PARADA 1 la aprobó el humano.
   - `current.md:63` («`proformas` respondió a las preguntas de la v3») frente a `:101-102` («Preguntas para
     `proformas`»), `impl_F-007.md:77-78` («Siguen abiertas las preguntas de design §Preguntas») y T20 (las
     espera). Decir cuál es verdad: ¿qué preguntas siguen abiertas?
   - Requerido: reescribir «Lo siguiente» y el prompt para el estado real (F-007 `in_progress`, revisión troceada
     T23 en curso, después avisos a `proformas`/`facturas`/albaranes que manda el líder, merge, despliegue con la
     llave cerrada y T20-T22 con quién lanza cada una; F-015 `blocked` a la espera de `AC26/30670`) y quitar las
     frases superadas citadas. Los bloques heredados con pendientes vivos (F-009 T24, F-006, decisiones del arnés,
     «De configuración») no son lo que se rechaza.
2. **H2 · C2/C5, `harness/features.json:137` (F-007)**: la `description` sigue diciendo «anotada sin estudiar
   todavía», habla de postventa-incidencias y no nombra a `proformas` (F-005) ni la proforma de mes v3; sale así
   en `BACKLOG.md`. `current.md:106-107` ya lo apunta como tarea del líder. Requerido: actualizarla (y regenerar
   `BACKLOG.md` con `harness/backlog.py`). El `status` sí es correcto.

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` sobre `fe85523`: **exit 0**, «ENTORNO LISTO». `3347 passed, 1 skipped, 1 warning in
  81.41s`; PUERTA COBERTURA `[OK]` 100.0 % de 710 líneas (710/710, umbral 80 %, critico); PUERTA TAMAÑO `[OK]`
  (requirements 150/150, design 239/250, impl 196/220); BACKLOG al día; `rigor.json` válido; rama correcta.
  Avisos: F-015 `blocked` (esperado) y ruff 79 avisos de deuda previa (no bloquea).
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`,
  `progress/history.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` (los `[OK] Existe` de `init.sh`).

## C2 — El estado es coherente

- [x] Una sola `in_progress`: F-007. `blocked`: F-015. `done`: F-002..F-006, F-009..F-012. `pending`: F-001,
  F-008, F-013, F-014 (`init.sh`: «15 features, 6 abiertas, en curso: ['F-007'], bloqueadas: ['F-015']»).
- [x] Rama `feature/F-007-registrar-proforma`, la que declara `features.json` (no `main`). `dev` (`60db955`) es
  ancestro de HEAD.
- [ ] `progress/current.md` describe solo la sesión activa y sin partes falsas: **H1**.
- [x] Toda `done` tiene su sección en `progress/history.md` (l. 8, 51, 108, 153, 183, 224, 272, 297, 322).

**F-015 `blocked`, ¿explicado?** Sí: `current.md:4-11` da el motivo (falta que Administración anule `AC26/30670`,
`con.ide` 2860439, desde la UI, nunca `DELETE`), la última lectura (2026-10-25), que se bloquea **para liberar el
único `in_progress` a F-007**, y los pasos al desbloquear. Lo registra el commit `a05c053`. Coherente con el
árbol: el código de F-015 ya está en `dev` (merge `60db955`) y en su rama quedan 4 commits de documentación
(`e6c8671`, `2a84faa`, `891e936`, `3b93a20`), que es el «merge de la rama de F-015 a `dev`» pendiente de `:10-11`.

| Fuente | Estado de F-007 | ¿Coherente? |
|---|---|---|
| `features.json` | `in_progress`, `critico`, `sdd`, rama correcta | sí (descripción atrasada: H2) |
| `BACKLOG.md` | `init.sh`: «BACKLOG.md al día» | sí |
| `tasks.md` | T0-T19 `[x]`; T20-T22 MANUAL, T23 (esta revisión) y T24 `[ ]` | sí |
| `impl_F-007.md:6-7` | T1-T19 hechas, «Paro en T19» | sí |
| `current.md:57-123` | `in_progress`, T1-T19 hechas, queda avisos, T20-T22, T23, T24 | sí (salvo `:89-90`, `:101`) |
| `current.md:268-288` | F-015 `in_progress`, F-007 `spec_ready`/`pending` | **no** (H1) |

## C5 — La sesión se cerró bien

- [ ] (no bloquea el APROBADO) `tasks.md` con todas `[x]`: **T20, T21 y T22 abiertas**, y deben estarlo: son
  MANUAL posteriores al merge (V8 con Administración, App Settings y despliegue, dry-runs de la 0719 y un
  `commit:true` autorizado); T23 es esta revisión y T24 el `init.sh` final. Mismo criterio que F-010, F-011 y
  F-015 (`review_F-015_C1C2C5.md`, aceptado por el humano): **bloquean el `done`, no el APROBADO para merge.**
- [x] Al menos un commit `F-007 Tn:` por tarea hecha, ninguno que mezcle código de dos tareas: T1 `04f13ba`, T2
  `64087fd`, T3 `1b04ba5`, T4 `03a17a7`, T5 `ab037a0`, T6 `3f28e74`, T7 `9022f29` (+ `9dc9eb5`, orden de imports
  de los tests de T6, un fichero), T8 `78d21e1`, T9 `22ab898`, T10 `e0f105e`, T11 `7e6b06c`, T12 `41900cb`, T13
  `b00e59c`, T14 `a8e3085`, T15 `a44bba9`, T16 `fb3f42c`, T17 `1ac55b3` (+ `bbd562c`, huecos de cobertura), T18
  `904a2ef`, `8c92d52`, `d9e97a8` (este último con el informe de mutación y las marcas T18-T19 en `tasks.md`),
  T19 `7cbff6b` (+ `af81713` en `azure-apps`). **T0** con formato `F-007:` (`fef6450`, `cc40470`, `7215541`):
  fase de spec, solo lectura; mismo criterio que F-015 T0. Los informes van como `F-007:` (`a3acbd7`, `e557b9e`,
  `fe85523`), como manda `CONVENTIONS.md:47` para ajustes. Los dos merges de `dev` (`b804e5e`, `6ece24d`) son
  entrantes, no commits a `dev`.
- [x] Convención de mensajes: los 35 commits de `dev..HEAD` (33 + 2 merges) en español y **todos** con el pie
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` (comprobado con `%(trailers:key=Co-Authored-By)`;
  también `af81713` en `azure-apps`). Observación sin bloqueo: muchos van sin tildes ni eñes («campana de
  mutacion», «anio», «nucleo»); «campana» por «campaña» cambia el sentido. Mejor con tildes en adelante.
- [x] Sin temporales ni artefactos sin trackear: `git status --short` vacío antes y después de `init.sh`. En
  `--ignored`, lo único posterior al último commit es `.coverage` y `coverage.json` (los regenera `init.sh`); el
  resto (`.txt`, `.csv`, terraform, `__pycache__`) es anterior y ajeno. El fichero suelto `` `0`].{t `` ya no está.
- [x] Worktrees: `git worktree list` al empezar solo mostraba el árbol principal; el `../sigrid-api-mut007` de la
  medición del implementer está borrado (`impl_F-007.md:173`, comprobado). **Durante esta revisión** apareció
  `C:/Users/pgris/PycharmProjects/sigrid-api-rev007-mut` (detached en `fe85523`, creado 2026-10-26 07:40, después
  del último commit de 2026-10-25 17:16): es del reviewer de mutación en paralelo, no del implementer. Quien lo
  creó debe hacer `git worktree remove` antes del merge.
- [x] `features.json` refleja el estado real: `in_progress` es lo correcto con T20-T24 abiertas (descripción: H2).

**Huérfanos fuera del alcance de F-007 (no bloquean):** dos ramas locales `worktree-agent-a6ce68ad257b23e45` y
`worktree-agent-ac0c369f0e3b12f11`, sin worktree, ambas en `2a5ac24` (merge de F-006, 2026-09-25) y contenidas en
HEAD: restos de agentes de F-006; el humano puede borrarlas con `git branch -d`. En `azure-apps` hay un
`datamart_seg_anual.md` modificado sin commitear, de otro proyecto: ajeno a F-007.

## «Evidencias» contra lo medido

| Evidencia del informe (`impl_F-007.md:177-195`) | Medido por este reviewer | ¿Casa? |
|---|---|---|
| Suite 3347 passed, 1 skipped | `init.sh` sobre `fe85523`: idéntico | sí |
| 466 tests de F-007 | `pytest tests/test_f007_*.py -q -p no:cacheprovider`: 466 passed | sí |
| Cobertura 100,0 % (710/710, critico) | PUERTA COBERTURA: idéntico | sí |
| Tamaño requirements 150/150, design 239/250, impl 196/220 | PUERTA TAMAÑO: idéntico | sí |
| Mutación ronda 2: 374 / 372 / 2 / 0 timeouts, 3755 s | `mutacion_F-007.md`: mismas cifras, 3755.1 s, Workers 1, SHA `7cbff6b8…`, base 67,8 s, media 10,0 s (374 × 10,0 ≈ 3740) | sí (la verificación independiente de la campaña es del trozo C4 bis) |
| Tiempo de la suite 100,63 s | 81,41 s en esta ejecución | sí: carga distinta; no es reproducible al segundo |

Para el trozo de C4 bis (no es de este bloque): la tabla «Evidencias» no tiene fila de **workers**; el dato está
en `impl_F-007.md:40` («En serie (`--workers 1`)») y en el informe de mutación. C4 bis lo pide en «Evidencias».

## Resumen para el líder

- Rechaza **H1** (`current.md:268-288` y las frases de `:16-20`, `:43-44`, `:89-90`, `:101-106`): arreglo de
  minutos. **H2**: la descripción de F-007 en `features.json` y regenerar `BACKLOG.md`.
- `init.sh` en verde sobre `fe85523`; las «Evidencias» casan con lo medido; commits con convención y pie.
- T20-T22 abiertas: bloquean el `done`, no el merge (precedente F-010/F-011/F-015).
- Retirar el worktree `sigrid-api-rev007-mut` antes del merge (es de la revisión de mutación).

## Automejora (propuesta, no aplicada)

- Cuarta feature seguida rechazada en C2 por «Lo siguiente» y «Prompt para retomar» atrasados. Reitero la
  propuesta de `review_F-011_C1C2C5.md` y `review_F-015_C1C2C5.md`: paso fijo del líder en `leader.md` al lanzar
  y al recibir al implementer, y un aviso de `init.sh` si la feature `in_progress` no aparece en «Prompt para
  retomar» o si allí aparece otra con un estado distinto del de `features.json`. Vale para `arnes-base`.
