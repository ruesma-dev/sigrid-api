<!-- progress/review_F-004_papeleo.md -->
# F-004 · Revisión acotada — papeleo (C1,C2,C4,C4ter,C5) + RED/cobertura + docs T16/T17

**Ámbito (encargo del líder):** C1, C2, C5, C4 (trazabilidad R1-R24), C4 ter,
solo RED+cobertura de C4 bis (mutación T15 fuera), fidelidad documental
T16/T17. Revisión completa (pasada 1). No se ejecutó `init.sh` (instrucción
del encargo); sí `pytest -k f004 -q` (175 pasan, 1263 deseleccionados,
1,49 s) y `grep`/lectura directa. Datos de `init.sh` del líder: ENTORNO
LISTO, 1.437 pasan/1 skip, cobertura 100,0 % (455/455), tamaño OK —
coinciden con `impl_F-004.md` §6-7.

## Veredicto: APROBADO (parcial, solo mi ámbito) — re-revisado tras `5deaac6`

`0632738` había cerrado el hallazgo de origen (comandos MANUAL en
`current.md`) pero introdujo dos defectos: T18 inline y T20 sin la consulta
de huérfanos. `5deaac6` corrige los dos: T18 ahora fija las App Settings por
`f004_appsettings.json` (ASCII sin BOM, las cuatro claves, array
`{name,value,slotSetting}`) y `--settings "@f004_appsettings.json"`, sin
nada inline; T20 incorpora la 4ª consulta de `propuesta §14 nivel 3`
(huérfanos, texto exacto) con criterio "ninguna fila". Contrastado línea a
línea contra `tasks.md` T18-T21 y contra la propuesta: ya no falta ningún
comando ni criterio, y nada contradice la spec. Mi ámbito queda saldado.
**No he juzgado el código/tests/`sigrid_api.md` que el implementer sigue
tocando ahora mismo** (`concepto_grafico_statements.py`,
`attach_concepto_grafico_use_case.py`, `requirements.txt`) ni ejecutado la
suite: fuera de este encargo.

## C1/C2/C4 ter — Arnés, estado y rutas sensibles

- [x] Ficheros exigidos presentes. Una sola feature `in_progress` (F-004);
  rama correcta; `current.md` describe solo la sesión activa (bloques de
  F-003 son cierres fechados, no restos).
- **C4 ter N/A justificado**: `harness/rutas_sensibles.json` no existe.

## C4 — Verificación real

- [x] R1-R21 con `test_f004_rN_*`: 130 tests por `grep`, 175 pasan
  (parametrizados incluidos): `test_f004_models.py` (R1-R3),
  `test_f004_settings.py` (R4-R5), `test_f004_document_write_guard.py`
  (R7-R8), `test_f004_statements.py` (R11-R20), `test_f004_use_case.py`
  (R6-R7,R9-R17,R21), `test_f004_route.py` (R2-R3). R19 confirmado contra
  código: `git diff dev...HEAD --stat` vacío para los tres guardias de
  seguridad. R16 con corrección de test documentada en `impl_F-004.md` §3.
- [x] Sin red ni BBDD: único `import pyodbc` (`test_f004_route.py`) dobla
  `pyodbc.IntegrityError`, no conecta.
- [x] **MANUAL con comando exacto en `current.md`** — presente y correcto
  desde `5deaac6`: T18 por fichero JSON, T20 con las 4 consultas.
- **R22** (meta): satisfecho en agregado, igual que R9 en F-003.
- **R23** (MANUAL sha256+idempotencia): sin test, correcto, depende de
  T20/T21, ya bien listados. **R24**: ver docs, abajo.

## C4 bis (solo RED y cobertura)

- [x] **RED**: `impl_F-004.md` §3 trae salida real de fallo (no "se hizo
  TDD") para las 5 parejas, cruzada con commits rojo/verde (`d714964`/
  `00f6140`, `308fa2b`/`d285e38`, `4f21c73`/`5a7edf6`, `15ce980`/`a8b4c17`,
  `9e1aeac`/`0d9e8d1`; ruta en `fe78317`). Correcciones de test durante el
  desarrollo documentadas sin ocultar nada.
- [x] **Cobertura**: `[OK]` 100,0 % (455/455), línea literal citada.
  Mutación fuera de este encargo (T15 no lanzada).

## Fidelidad documental T16/T17

- **T16**: `grep -n "ruesma_rep" CLAUDE.md docs/ARCHITECTURE.md
  CHECKPOINTS.md` — los tres dicen "se escribe SOLO por
  `sigrid/concepto-grafico`, nunca por `sql/write`", coherente con la ruta
  registrada en `function_app.py:262` y con que los tres guardias de
  seguridad no cambiaron. Correcto.
- **T17** (`azure-apps` `a40684f`, diff completo leído): `sigrid_api.md`
  cubre §2/§2.1/§2.2, §4 (7 App Settings = R4), §5.1 (`DocumentWriteGuard`),
  §7.1/§7.6/§8/§8.8; `dedicacion.md`/`partes.md`/`remesas.md` corrigen
  "réplica" → "documental, READ_WRITE, solo escribible por
  `sigrid/concepto-grafico`". Nada desmiente el código; no releí las
  mediciones línea a línea (fuera de mi ámbito).

## C5 — Cierre de sesión

- [N/A, feature no cerrada] `tasks.md`: T15/T18-T22 en `[ ]`, correcto (sigue
  `in_progress`). `features.json` refleja el estado real. Árbol con cambios
  sin commitear ahora mismo (`concepto_grafico_statements.py`,
  `requirements.txt`, `test_f004_statements.py`): es el implementer
  trabajando en vivo, no un resto de sesión — no lo evalúo, fuera de mi
  encargo, y la sesión no está cerrada.

## Cambios requeridos

Ninguno. Los dos de la pasada anterior (T18 inline, T20 sin huérfanos)
quedaron corregidos en `5deaac6`.
