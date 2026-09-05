<!-- progress/review_F-003_c1c2c5.md -->
# F-003 · Revisión acotada: C1, C2, C5

Encargo troceado del líder: solo checkpoints C1, C2 y C5. No se ha ejecutado
`init.sh` ni `pytest` en esta revisión (campaña de mutación corriendo en
background con 8 workers); el resultado de C1.1 es el de la ejecución que hizo
el líder en esta misma sesión, y el líder la repetirá al cerrar.

## C1 — El arnés está completo y en verde

- [x] `bash harness/init.sh` termina con exit code 0. **No verificado por mí**:
  doy por bueno el resultado del líder en esta sesión — ENTORNO LISTO, 1.262
  tests (1 skip), cobertura 99,2 %, puerta de tamaño OK, ruff 79 avisos (deuda
  previa). El líder debe repetirlo antes de cerrar la feature.
- [x] Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
  `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
  `docs/CONVENTIONS.md`. Comprobado con `ls`/`test -f`: los siete están.

## C2 — El estado es coherente

- [x] Solo F-003 está `in_progress` en `harness/features.json` (línea 62); las
  demás son `pending` (líneas 26, 84) o `done` (línea 43).
- [x] Rama actual `feature/F-003-guardia-bases-cruzadas`, coincide con el
  campo `branch` de la entrada F-003 y no es `main` ni `dev`.
- [x] `progress/current.md` describe solo la sesión activa de F-003: estado,
  verificación, historia de los seis fallos, lo pendiente (mutación a relanzar,
  segundo encargo al reviewer, T8 manual) y un bloque explícito de decisiones
  fuera de F-003 (config `ALLOWED_DATABASES`, permisos `user_rw`, mejoras de
  arnés, F-004) que son notas de cierre de sesión, no restos de una sesión
  anterior sin limpiar.
- [x] `progress/history.md` trae resumen de F-002, la única feature `done`;
  F-003 sigue `in_progress` y no debe tener entrada todavía — correcto.

## C5 — La sesión se cerró bien

- [x] `tasks.md`: T1–T7, T9–T16 en `[x]`. **T8 en `[ ]`** — es el único
  pendiente, y es la verificación MANUAL post-despliegue («solo se puede hacer
  DESPUÉS de desplegar»), listada en `current.md` con su comando exacto
  (`scripts/diagnose_sigrid_contrato_docs.py`) y su criterio. Encaja con el
  carve-out explícito de C4 para verificaciones `MANUAL (humano)`: quedan
  pendientes de que el humano las ejecute, no bloquean el resto de tareas. No
  lo trato como checkbox vacío de C5 mientras la feature siga `in_progress`.
  Commits por tarea: T11, T13, T14, T15, T16 llevan `F-003 Tn:` explícito;
  T1–T7 y T9–T10 se resolvieron en 2-3 commits `F-003: ...` sin tag de tarea
  (`4892e36`, `b70a689`), lo cual ya fue señalado y aceptado por el reviewer en
  la pasada 1 (`review_F-003.md:112-115`: «los dos primeros no [llevan
  F-003 Tn:], pero eso fue lo que pedí en la pasada 1»). No reabro ese punto:
  ya está resuelto y documentado.
- [x] Árbol limpio: `git status --porcelain` sin salida, dos veces
  comprobado. Sin ficheros temporales ni artefactos sin trackear.
- [x] `harness/features.json` refleja el estado real: `status: in_progress`,
  `rigor: critico`, coincide con lo que falta (mutación por relanzar tras T16,
  T8 pendiente de despliegue, cierre pendiente de merge por el humano).

## Veredicto (solo sobre C1, C2, C5)

**APPROVED** en el ámbito de este encargo. Ningún checkbox vacío sin motivo;
el único hueco (T8) está justificado por escrito y no depende de este bloque.
No me pronuncio sobre C3, C3 bis, C4, C4 bis ni C4 ter: los cubren los otros
dos reviewers en paralelo.
