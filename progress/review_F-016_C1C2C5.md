<!-- progress/review_F-016_C1C2C5.md -->
# Revisión F-016 · bloques C1, C2 y C5 (más topes de tamaño, «Evidencias», coherencia y barrido)

Revisión completa (pasada 1) desde `745a43c` (`dev` = merge-base) hasta HEAD `c08461f`. Reviewer, 2026-10-28.
Rigor declarado: **`critico`** (`harness/features.json`, entrada F-016). C3, C3 bis, C4, C4 bis y C4 ter **quedan
fuera** de este trozo (otros reviewers en paralelo). Nada contra Sigrid ni contra la API desplegada. No se ha
editado código, tests ni specs. `init.sh` ejecutado una sola vez, tal cual. El commit `1733c2f` (alta de F-018, del
líder) y el worktree `.claude/worktrees/` (F-018) quedan fuera de alcance por encargo.

## Veredicto del bloque: **CHANGES_REQUESTED** (H1 bloquea; H2 y H3 son de una línea, para el mismo arreglo)

C1 en verde y medido; las «Evidencias» casan con mi ejecución; topes de tamaño dentro; sin secretos, personas ni
CIF. Rechaza `progress/current.md` (C2, H1): **quinta feature seguida** (F-010, F-011, F-015, F-007, F-016) con
«Lo siguiente» y «Prompt para retomar» atrasados. T17-T18 (MANUAL) y T19 (esta revisión) abiertas no deciden el
veredicto (criterio de F-010/F-011/F-015/F-007, ver C5).

## Cambios requeridos

1. **H1 · C2, `progress/current.md` tiene partes falsas hoy.**
   - `current.md:199-205`, «Prompt para retomar»: «**F-016** (proforma a origen) está en spec [...] si
     `specs/F-016-*/` ya existe y está en `spec_ready`, espera la aprobación del humano». Falso: spec v2 aprobada
     (`2f2d4f6`), T1-T16 hechas, revisión troceada en curso. Una sesión que lo siga se quedaría esperando una
     PARADA 1 ya dada e ignoraría los avisos, T17-T18 y el merge.
   - `current.md:193-197`, «Lo siguiente en el backlog»: «**F-016** (arriba): spec de la proforma a origen» y
     «Después de F-016: F-008 [...]». Falso desde `1733c2f`: la siguiente es **F-018** (prioridad 9; F-008 pasa a 10,
     `features.json` y `BACKLOG.md:18`), y F-016 no está en spec.
   - `current.md:21-25`, «**Decisiones abiertas para el humano**» P1 (D6) y P3 (D12) con «Recomendación»: ya
     decididas (cabecera `current.md:3`, `design.md:143`, `:164`, `:174-176`, «aprobado por el humano, 2026-10-28»).
   - Requerido: reescribir prompt y «Lo siguiente» al estado real (F-016 `in_progress`, revisión troceada T19 en
     curso; después avisos a `proformas`/`facturas` que manda el líder, merge, despliegue con
     `SIGRID_PROFORMA_ORIGEN_ENABLED=false` y T17-T18 con quién lanza cada una; luego F-018) y pasar l. 21-25 a
     «decididas» o quitarlas. Los bloques heredados con pendientes vivos (F-007, F-015, F-009 T24, F-006, arnés,
     configuración) no son lo que se rechaza.
2. **H2 · C5, `harness/features.json` (F-016, `acceptance[3]`)**: «commit:true exige SIGRID_DOMAIN_WRITE_ENABLED,
   SIGRID_PROFORMA_WRITE_ENABLED y autorización expresa». A origen exige además `SIGRID_PROFORMA_ORIGEN_ENABLED`
   (R4, D10). La `description` aún dice «La spec decide cómo se elige la anterior», cuando v2 decidió que la elige el
   llamante. Requerido: añadir la llave al criterio (y una frase de v2 a la descripción) y regenerar `BACKLOG.md`
   con `harness/backlog.py`. El `status` sí es correcto.
3. **H3 · C5, `specs/F-016-proforma-a-origen/tasks.md:21` (T15)** marcada `[x]` con parte de su «Verificación» sin
   hacer: «las dos consultas del contrato probadas en lectura sobre una cadena real» está PENDIENTE
   (`impl_F-016.md:111-112`, `:157`) y se movió a V0/V2 de `verificacion_manual.md` y a T17. Se acepta el
   desplazamiento (es lectura en producción, del humano), pero debe constar en la propia tarea. Requerido: anotarlo
   en T15 («la prueba en lectura de §2.3 se hace en T17, V0/V2»).

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` sobre `c08461f`: **exit 0**, «ENTORNO LISTO». `3549 passed, 1 skipped, 1 warning in
  325.17s`; PUERTA COBERTURA `[OK]` 100.0 % de 270 líneas (270/270, umbral 80 %, critico); PUERTA TAMAÑO `[OK]`;
  BACKLOG al día; `features.json` y `rigor.json` válidos; rama correcta. Avisos: F-015 `blocked` (esperado) y ruff.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`, `progress/current.md`,
  `progress/history.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` (los `[OK] Existe` de `init.sh`).

**Ruff 158 avisos, no 79: no es deuda de F-016.** `ruff check . --extend-exclude .claude` da **79**, lo mismo que
`dev` medido en un worktree limpio (retirado después); los otros 79 son la copia del repo dentro de
`.claude/worktrees/` (F-018). Sobre los `.py` del diff, 5 avisos, todos en líneas de `e903394` (2026-04-16, `git
blame`). `impl_F-016.md:165` los llama «158 de ruff de deuda previa»: cierto en el fondo, pero el número está
inflado por el worktree ajeno (ver Automejora).

## C2 — El estado es coherente

- [x] Una sola `in_progress`: F-016 (`init.sh`: «18 features, 8 abiertas, en curso: ['F-016'], bloqueadas:
  ['F-015']»). `done`: F-002..F-007, F-009..F-012. `pending`: F-001, F-008, F-013, F-014, F-017, F-018.
- [x] Rama `feature/F-016-proforma-a-origen`, la de `features.json` (no `main`). `dev` (`745a43c`) es ancestro de
  HEAD; sin merges en `dev..HEAD`.
- [ ] `progress/current.md` describe solo la sesión activa y sin partes falsas: **H1**.
- [x] Toda `done` tiene su sección en `progress/history.md` (l. 8, 51, 108, 153, 183, 224, 272, 297, 322, 342;
  F-007 en l. 342).

| Fuente | Estado de F-016 | ¿Coherente? |
|---|---|---|
| `features.json` | `in_progress`, `critico`, `sdd`, prioridad 8, rama correcta | sí (acceptance/descripción: H2) |
| `BACKLOG.md` | «En curso: **F-016**», F-018 siguiente; `backlog.py --comprobar` → exit 0 | sí |
| `tasks.md` | T0-T16 `[x]`; T17-T18 MANUAL, T19 (esta revisión), T20 `[ ]` | sí (T15: H3) |
| `impl_F-016.md` | T1-T16 hechas; queda avisos, T17-T18, T19 y T20 al cierre | sí |
| `current.md:3-19`, `:27-31` | `in_progress`, spec v2 aprobada, T1-T16, init en verde | sí |
| `current.md:21-25`, `:191-205` | decisiones «abiertas», F-016 «en spec», F-008 tras F-016 | **no** (H1) |

## C5 — La sesión se cerró bien

- [ ] (no bloquea el APROBADO) `tasks.md` con todas `[x]`: **T17 y T18 abiertas** y deben estarlo (MANUAL:
  despliegue con la llave cerrada, previas sobre cadenas reales y un `commit:true` autorizado en la 0404); T19 es
  esta revisión; T20 es el `init.sh` de cierre. Mismo criterio que F-010, F-011, F-015 y F-007
  (`review_F-007_C1C2C5.md`, aceptado por el humano): **bloquean el `done`, no el APROBADO para merge.**
- [x] Un commit `F-016 Tn:` por tarea hecha, ninguno mezcla código de dos tareas: T1 `013169e`, T2 `9b4c70a`, T3
  `60a5052`, T4 `e6688c3`, T5 `284f0bd`, T6 `fd73ee5`, T7 `87c97bd`, T8 `d1252a2`, T9 `3a1c2c5`, T10 `31496ca`, T11
  `3591400`, T12 `1ef36da`, T13 `93bbce3` (+ `06ffcb6`, orden de imports), T14 `eca4629`, T15 `7b72daf` (+
  `3744877`/`7afe9e9` en `azure-apps`), T16 `e2a8b23`. **T0** y la fase de spec como `F-016:` (`f46e874`,
  `44b9814`, `f3620e7`, `1ca0336`, `2f2d4f6`): solo lectura, mismo criterio que F-007/F-015 T0. `c08461f` se titula
  «T20» pero T20 sigue `[ ]` y así debe ser (es el `init.sh` de cierre tras el APROBADO): observación, no defecto.
- [x] Convención de mensajes: los 24 commits de `dev..HEAD` en español y **todos** con `Co-Authored-By: Claude Opus
  5.5 <noreply@anthropic.com>` (`%(trailers:key=Co-Authored-By)`); `Claude-Session` desde `1733c2f`, cuando llegó
  la instrucción. Observación sin bloqueo: varios sin tildes («nucleo», «transaccion», «sintetica», «peticion»).
- [x] Sin temporales ni artefactos sin trackear de F-016: `git status --short` solo muestra `.claude/worktrees/`
  (F-018, ajeno) y los informes de los revisores en paralelo (`review_F-016_C3C4ter.md`, `review_F-016_docs.md`).
  En `--ignored`, lo único posterior a `explore_F-016.md` es `.coverage` (lo regenera `init.sh`) y `__pycache__`;
  el resto (`.txt`, `.csv`, terraform, `.pem`, `.zip`) es anterior y ajeno. `git worktree list`: árbol principal y
  el de F-018 (bloqueado, de otro agente). Las ramas `worktree-agent-a6ce…`/`ac0c…` son restos de F-006 (ya
  anotados en `review_F-007_C1C2C5.md`).
- [x] `features.json` refleja el estado real: `in_progress` es lo correcto con T17-T20 abiertas (texto: H2).

## Topes, «Evidencias» y barrido

| Evidencia (`impl_F-016.md:161-172`) | Medido por este reviewer | ¿Casa? |
|---|---|---|
| Suite 3549 passed, 1 skipped | `init.sh` sobre `c08461f`: idéntico | sí |
| 116 funciones de test F-016 (23/8/6/39/12/28) | `grep -c '^def test_'` por fichero: idéntico | sí |
| Cobertura 100,0 % (270/270, critico) | PUERTA COBERTURA: idéntico | sí |
| Tamaño 118/150, 186/250, impl 151/220 | `python -m harness.tamano --feature F-016`: 118, 186, **172**/220 | sí (151 era antes de la sección; 172 dentro) |
| Mutación 116 / 102 / 14 → 0 no aceptados | `mutacion_F-016.md`: 4937,2 s, SHA `06ffcb6b…`, Workers 1 | cifras del informe (la verificación independiente es del trozo C4 bis) |
| Tiempo de la suite 199,23 s | 325,17 s (tres revisores en paralelo) | sí: carga distinta |
| R1/R2: `git diff dev` vacío de tests/dorados de F-007/F-009/F-015, núcleo, `proforma_statements.py`, `infrastructure/` | `git diff --stat dev..HEAD` de esas rutas: vacío | sí |

Para el trozo de C4 bis: el nº de **workers** no está en la tabla «Evidencias» (sí en `mutacion_F-016.md:37`, 1) y
el SHA medido (`06ffcb6`) es anterior a HEAD; desde entonces, en `.py`, solo `tests/test_f016_{statements,
use_case}.py` (+84/−1, los tests de T14), ningún fichero de producción del alcance: a juzgar allí.

**Barrido de datos sensibles** sobre `specs/F-016-proforma-a-origen/*`, `progress/{explore,impl,mutacion}_F-016.md`,
`progress/current.md`, `contrato_proformas.md`, `tests/fixtures/f016_cadena.json` y `tests/f016_dobles.py`, con
`grep -iE`: `password|secret|api[_-]?key|x-functions-key|code=|token|azurewebsites|https?://|AccountKey|Server=|UID=`,
IPv4, GUID, correos `@*.es|com`; CIF/NIF/NIE (`[A-W]\d{7}[0-9A-J]`, `\d{8}[A-Z]`, `[XYZ]\d{7}[A-Z]`); tratamientos
(`D.|Sr.|Don…`) y una lista de nombres de pila comunes. Resultado: **ningún secreto, persona ni CIF**. Solo
salen la cabecera `x-functions-key` leída de `$env:SIGRID_API_FUNCTION_KEY` (`verificacion_manual.md:33`), el
placeholder `"x"` de un `Settings` de prueba (`:94`) y textos que dicen «sin secretos». Las `res` de la fixture son
descripciones de partidas. Todos los ficheros nuevos llevan la primera línea con su ruta; `git diff --check` limpio.

## Resumen para el líder

- Rechaza **H1** (`current.md:21-25`, `:191-205`): arreglo de minutos. **H2** (`features.json` F-016 + regenerar
  `BACKLOG.md`) y **H3** (nota en T15 de `tasks.md`) en el mismo commit.
- `init.sh` en verde sobre `c08461f`; «Evidencias» casan; commits con convención y pie; topes dentro. T17-T18
  abiertas: bloquean el `done`, no el merge.
- Ojo al merge: `1733c2f` (alta de F-018) vive en esta rama, y el worktree de F-018 salió de `dev` (`745a43c`), sin
  esa alta. Al mergear F-016 a `dev` entra; si F-018 escribe `features.json` antes, habrá conflicto.

## Automejora (propuesta, no aplicada)

- **Quinta** feature seguida rechazada en C2 por el mismo motivo. Reitero `review_F-007_C1C2C5.md`: paso fijo del
  líder en `leader.md` al aprobar la spec y al recibir al implementer, y un aviso de `init.sh` si «Prompt para
  retomar» no nombra la feature `in_progress` con su estado. Vale para `arnes-base`.
- **`init.sh` debe excluir `.claude/worktrees/` del recuento de ruff** (`--extend-exclude .claude`): un worktree de
  agente duplica la «deuda previa» (79 → 158) y esconde un aumento real. Vale para `arnes-base`.
