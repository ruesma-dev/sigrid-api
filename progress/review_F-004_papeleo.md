<!-- progress/review_F-004_papeleo.md -->
# F-004 · Revisión acotada — papeleo (C1,C2,C4,C4ter,C5) + RED/cobertura + docs T16/T17

**Ámbito (encargo del líder):** C1, C2, C5, C4 (trazabilidad R1-R24), C4 ter,
solo RED+cobertura de C4 bis (mutación T15 fuera, no lanzada), fidelidad
documental T16/T17. Revisión completa (pasada 1). No se ejecutó `init.sh`
(instrucción del encargo); sí `pytest -k f004 -q` (175 pasan, 1263
deseleccionados, 1,49 s) y `grep`/lectura directa. Datos de `init.sh` del
líder: ENTORNO LISTO, 1.437 pasan/1 skip, cobertura 100,0 % (455/455), tamaño
OK — coinciden con `impl_F-004.md` §6-7.

## Veredicto: CHANGES_REQUESTED (parcial, solo mi ámbito)

Un único hallazgo bloquea C4: las verificaciones MANUAL no están en
`progress/current.md` con su comando exacto, solo en `tasks.md`. Todo lo
demás en mi ámbito es correcto.

## C1/C2 — Arnés y estado

- [x] Ficheros exigidos presentes (`CLAUDE.md`, `features.json`, `SPECS.md`,
  `current.md`, `history.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`). Una sola
  feature `in_progress` (F-004); rama correcta; `current.md` describe solo
  la sesión activa (bloques de F-003 son cierres fechados, no restos).

## C4 — Verificación real

- [x] R1-R21 con `test_f004_rN_*`: 130 tests por `grep`, 175 pasan
  (parametrizados incluidos), repartidos: `test_f004_models.py` (R1-R3),
  `test_f004_settings.py` (R4-R5), `test_f004_document_write_guard.py`
  (R7-R8), `test_f004_statements.py` (R11-R20), `test_f004_use_case.py`
  (R6-R7,R9-R17,R21), `test_f004_route.py` (R2-R3). R19 confirmado también
  contra código: `git diff dev...HEAD --stat` vacío para los tres guardias
  de seguridad. R16 con corrección de test documentada honestamente en
  `impl_F-004.md` §3.
- [x] Sin red ni BBDD: único `import pyodbc` (en `test_f004_route.py`) es
  para doblar `pyodbc.IntegrityError`, no para conectar.
- [ ] **MANUAL con comando exacto en `current.md`** — NO se cumple.
  `current.md` resume "T18-T22" en una frase; los comandos exactos (App
  Settings, consulta de la huérfana clase 35, `POST` con payloads,
  `documents/read`) solo están en `tasks.md` T18-T21. Precedente F-003
  (`review_F-003_c1c2c5.md`, `review_F-003_c4.md`): ese checkbox se aprobó
  porque el comando de T8 SÍ estaba citado en `current.md`. Aquí no.
- **R22** (meta): satisfecho en agregado, igual que R9 en F-003.
- **R23** (MANUAL sha256+idempotencia): sin test, correcto, depende de
  T20/T21 — mismo hallazgo de arriba. **R24**: ver docs, abajo.

## C4 ter — Rutas sensibles

- **N/A justificado**: `harness/rutas_sensibles.json` no existe (comprobado);
  sin declaración el bloque es N/A por diseño del arnés.

## C4 bis (solo RED y cobertura)

- [x] **RED**: `impl_F-004.md` §3 trae salida real de fallo (no "se hizo
  TDD") para las 5 parejas, cruzada con commits (rojo/verde:
  `d714964`/`00f6140`, `308fa2b`/`d285e38`, `4f21c73`/`5a7edf6`,
  `15ce980`/`a8b4c17`, `9e1aeac`/`0d9e8d1`; ruta en `fe78317`). Tres
  correcciones de test documentadas sin ocultar nada.
- [x] **Cobertura**: `[OK]` 100,0 % (455/455), línea literal citada.
  Mutación fuera de este encargo (T15 no lanzada).

## Fidelidad documental T16/T17

- **T16**: `grep -n "ruesma_rep" CLAUDE.md docs/ARCHITECTURE.md
  CHECKPOINTS.md` — los tres dicen "se escribe SOLO por
  `sigrid/concepto-grafico`, nunca por `sql/write`". Contrastado con código:
  ruta en `function_app.py:262`, única que importa
  `AttachConceptoGraficoUseCase`; los tres guardias no cambiaron. Correcto.
- **T17** (`azure-apps` commit `a40684f`): diff completo leído.
  `sigrid_api.md` cubre §2/§2.1, §2.2 (aclaración `ide` documental vs
  `(emp,cod)`, cita `explore_F-004_relacion_gra.md`), §4 (7 App Settings,
  nombres = R4), §5.1 (`DocumentWriteGuard`, triple llave), §7.1/§7.6/§8/§8.8
  (endpoint completo). `dedicacion.md`, `partes.md`, `remesas.md` corrigen
  "réplica" → "documental, READ_WRITE, solo escribible por
  `sigrid/concepto-grafico`". Nada afirmado desmiente el código dentro de lo
  cruzado; no releí `explore_F-004_mediciones.md`/`_relacion_gra.md` línea a
  línea (fuera de mi ámbito de "no profundizar en código/mediciones").

## C5 — Cierre de sesión

- [N/A, feature no cerrada] `tasks.md`: T15/T18-T22 en `[ ]`, correcto — la
  feature sigue `in_progress` con mutación y manuales pendientes.
- [x] Árbol limpio (`git status --porcelain` sin salida); `features.json`
  refleja el estado real (`in_progress`, `critico`).

## Cambios requeridos

1. **`progress/current.md`** — copiar de `tasks.md` T18-T21 el comando
   exacto de cada verificación MANUAL pendiente (App Settings, consulta de
   la huérfana, `POST` con sus payloads, `documents/read`), como se hizo con
   T8 en F-003.

Con eso corregido, mi ámbito queda APROBADO.
