<!-- progress/review_F-006_estado.md -->
Revisión completa (pasada 1) · acotada a C1, C2 y C5 · HEAD `22ba2a5`

# F-006 · Revisión acotada — estado del arnés (C1, C2, C5)

- **Rama:** `feature/F-006-alta-parte-reclamacion` · **rigor:** `critico` (declarado en
  `harness/features.json`).
- **Fuera de este encargo:** C3, C3 bis, C4, C4 bis, C4 ter (y con ellas RED, mutación,
  trazabilidad requisito → test y fidelidad documental). Los cubren los otros revisores.
- `bash harness/init.sh` ejecutado **una vez**, sin pipes, el 2026-09-25: `ENTORNO LISTO`.

## C1 — El arnés está completo y en verde

- **OK** `bash harness/init.sh` termina con exit 0: `ENTORNO LISTO. Puedes trabajar.`
  - pytest: **1731 passed, 1 skipped, 1 warning in 185.34s** (el aviso es el de pydantic
    `schema` en `DocumentReadRequest`, previo).
  - `PUERTA COBERTURA: 100.0% de 560 líneas cambiadas cubiertas (560/560, umbral 80%, nivel critico)`.
  - `PUERTA TAMAÑO`: requirements 140/150, design 167/250, impl 187/220.
  - ruff: 80 avisos, los mismos de deuda previa que cita el informe.
  - **Cotejo con «Evidencias» de `impl_F-006.md` §9:** tests 1.731 / 1 saltado / 0 fallos
    → **coincide**; cobertura 100,0 % de 560 → **coincide**. Tiempo de suite: el informe
    dice 151,79 s y hoy salen 185,34 s (+22 %): variación normal de máquina, no de
    alcance; solo se anota.
- **OK** Existen `CLAUDE.md`, `harness/features.json`, `specs/SPECS.md`,
  `progress/current.md`, `progress/history.md`, `docs/ARCHITECTURE.md`,
  `docs/CONVENTIONS.md` (líneas `[OK] Existe …` de `init.sh`).

## C2 — El estado es coherente

- **OK** Una sola `in_progress`: F-006 (`init.sh`: «en curso: ['F-006']»; lectura del
  JSON: F-001/F-007/F-008 `pending`, F-002…F-005 `done`). `BACKLOG.md al día` según
  `init.sh`, y su diff en la rama muestra F-006 «en curso» y F-007/F-008 pendientes.
- **OK** Rama actual `feature/F-006-alta-parte-reclamacion`, la de F-006 en
  `features.json` (`init.sh`: `[OK] Rama actual`). No es `main` ni `dev`.
- **KO** `progress/current.md` **no** describe solo la sesión activa. De sus 300 líneas,
  unas 230 son de F-004/F-005 y varias son **falsas hoy**, no solo antiguas:
  - l. 286-291 «Lo siguiente en el backlog»: «F-005 espera al **reviewer**». F-005 está
    `done` y mergeada en `dev` (`0d8b206`, `210fac1`).
  - l. 293-300 «Prompt para retomar»: manda retomar F-005 «pendiente de review» en
    `cfb8048`. Una sesión nueva que lo siga trabaja sobre la feature equivocada.
  - «Lo que espera al humano» punto 1: «Queda el merge de **F-005** cuando el reviewer
    apruebe» → ya mergeada.
  - l. 44-48, dentro del propio bloque de F-006: «implementer lanzado. Spec en `a805f4a`;
    **faltan sus respuestas a Q1-Q4** … Al terminar: F-006 a `spec_ready` y **PARAR**».
    Contradice la línea anterior y el estado real (spec aprobada, implementación hecha).
  - Guiones «de referencia» de F-005 (obra 0404) y de F-004 (T18-T21), ya ejecutados:
    su sitio es `history.md` / los `verificacion_F-00x_*.md`, que ya existen.
  El bloque «F-006 · Implementación» (l. 4-28) sí es correcto y está al día.
- **OK** Toda feature `done` tiene su resumen en `history.md`: F-002 (l. 8), F-003 (l. 51),
  F-004 (l. 108), F-005 (l. 153).

## C5 — La sesión se cerró bien

- **OK con N/A justificado** `tasks.md` con todas las tareas `[x]` y un commit por tarea:
  - `[x]` T1-T14 y T19. Commits: T3 `c0fc82b`, T4 `8bda5d1`, T5 `81bc619`, T6 `1af37d9`,
    T7 `e3f4006`, T8 `b660e22`, T9 `ee22b9f`, T10 `13664ef`, T11 `2af370e`, T12
    `deb60f0`+`3852580`, T13 `22e23f7`+`22ba2a5`, T14 `33d7b66`+`b4dea19`, T19 en el
    mensaje de `22ba2a5`. `69d8390` («F-006: fecha OLE…») es un ajuste de T8/T9 sin `Tn`:
    se admite, no esconde trabajo sin tarea.
  - T1 y T2 son tareas de la fase de spec (medición y respuestas Q1-Q4), hechas por el
    spec-author/líder antes de la rama de implementación: sus commits son `a805f4a` y
    `35c3c42`, con el formato `F-006:` de la fase de spec. **N/A del formato `Tn`**, por
    ese motivo.
  - T15-T18 `[ ]`: son **MANUAL (humano)**, posteriores al merge y al despliegue
    (App Settings, dry-run, `commit:true` autorizado, idempotencia). **N/A para el cierre
    de la implementación**, con el mismo criterio que `review_F-004.md` l. 119 aplicó a
    T18-T21. Su guion exacto está en `tasks.md` y lo cita `current.md`.
  - Ningún commit de F-006 en `dev` ni en `main`: ambas en `210fac1` (= merge-base) y
    `git log --grep=F-006 dev main` sale vacío.
  - **Sin push:** `git branch -r --contains ad5d500` vacío, la rama no tiene upstream
    (`git status -sb`) y `git ls-remote --heads origin` no lista ninguna rama F-006.
- **OK con observación** Sin ficheros temporales ni artefactos sospechosos: el único sin
  trackear es `` `0`].{t `` (0 bytes, 2026-09-24 12:31), **fuera del índice**
  (`git ls-files -s` no lo lista, `git status --porcelain` lo da como `??`). No lo trae
  ningún commit de la rama. Está declarado en `current.md` como ajeno y su destino se
  deja al humano; recomiendo borrarlo, por su nombre parece un comando de consola mal
  escapado. Ningún temporal de la campaña de mutación en el árbol.
- **OK** `features.json` refleja el estado real: F-006 `in_progress` es correcto mientras
  la revisión no apruebe (implementación hecha, review pendiente, T15-T18 tras el merge).

## Secretos y `.env`

- **OK** `.env` existe y **no** está versionado (`git ls-files` sin `.env`;
  `git log --all -- .env` vacío).
- **OK** Barrido del diff `dev...HEAD` (25 ficheros, +6.240): ninguna contraseña, cadena
  de conexión, clave, GUID de suscripción/tenant ni IP interna. Coincidencias revisadas una
  a una: `sql_server_write_password` (nombre de atributo), `"no-es-una-credencial"` (doble
  de test), `"SECRETO …"` (textos de test que comprueban que la traza no filtra las
  descripciones), y la mención a `SIGRID_API_FUNCTION_KEY` como nombre de variable.
  `local.settings.sample.json` solo añade las cuatro claves `SIGRID_RECLAMACION_*` con
  defectos cerrados.
- Fuera de alcance, ya anotado en `current.md` y previo a F-006: `local.settings.json`
  versionado desde `e903394` con credenciales reales. No lo toca esta rama.

## Cambios requeridos

1. **`progress/current.md`**: dejarlo con la sesión activa de F-006 solamente.
   - Borrar «Lo siguiente en el backlog» (l. 286-291) y reescribir «Prompt para retomar»
     (l. 293-300) para F-006: rama, HEAD, review en curso con informes troceados, y T15-T18
     manuales tras el merge.
   - Corregir l. 44-48: quitar «faltan sus respuestas a Q1-Q4» y «Al terminar: F-006 a
     `spec_ready` y PARAR».
   - Sacar el bloque F-004/F-005 (desde l. 71 «Todo lo que sigue es de F-004/F-005…»
     hasta los guiones de T18-T21 y de la obra 0404) y el punto 1 de «Lo que espera al
     humano»: ya viven en `history.md` y en `verificacion_F-004_*` / `verificacion_F-005_*`.
   - «Pendiente de decisión del humano» puede quedarse si sigue vigente, pero lo que ya
     esté resuelto (el diagnóstico de `mutacion_paralela`, si `impl_F-006.md` lo cerró) se
     actualiza.
2. Opcional, no bloquea: el tiempo de suite de «Evidencias» (151,79 s) no coincide con el
   medido hoy (185,34 s); basta con anotar que es de otra ejecución.

## Automejora (propuesta, no aplicada)

- C2 no dice qué hacer con los guiones «de referencia» de features cerradas: proponer en
  `CHECKPOINTS.md` que al pasar una feature a `done` su bloque salga de `current.md` a
  `history.md` en el mismo commit de cierre; aquí se acumularon dos features.

VEREDICTO PARCIAL: CAMBIOS
