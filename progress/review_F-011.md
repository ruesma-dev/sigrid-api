<!-- progress/review_F-011.md -->
Revisión incremental desde 4d1c266 (pasada 2, consolidada): delta `4d1c266..fb9e890`; lo anterior, por los cinco informes de bloque

# F-011 · Revisión final consolidada

- **Veredicto: APPROVED para merge a `dev`.** No es el `done`: T13 y T14 (MANUAL, posteriores al merge) siguen
  abiertas y **bloquean solo el `done`**, no este APROBADO. Mismo criterio que F-010 (`review_F-010.md`, pasada 3).
- **Nivel de rigor:** `critico`, declarado en `harness/features.json` (no por defecto). Exige fase RED, cobertura
  ≥ 80 % de lo cambiado, mutación con cero supervivientes y MANUAL listadas con comando y resultado real.
- **Rama / HEAD:** `feature/F-011-documents-read-valida-database`, `fb9e890a0053c99fcd404fb87f07df7c01a9a3c6`.
- Reviewer, 2026-10-18. No he tocado código, tests ni `.env`. Sin commit.

## Lo que se ejecutó en esta pasada

- `bash harness/init.sh` entero sobre `fb9e890`: **ENTORNO LISTO**, exit 0, **2664 passed, 1 skipped**, 0 failed
  (80,2 s). `PUERTA COBERTURA [OK]` 100,0 % (16/16, umbral 80 %). `PUERTA TAMAÑO [OK]`: requirements 107/150,
  design 225/250, impl 167/220 (este informe, tope 140, no existía al medir).
- `git diff 4d1c266 fb9e890 --stat`: 9 ficheros, todos papeleo (`current.md`, los cinco `review_F-011_*.md`,
  `verificacion_F-011.md` nuevo, `design.md`, `tasks.md`). **Ningún fichero de código ni de tests**: la mutación,
  la fase RED y la trazabilidad de los bloques siguen valiendo.
- `git worktree list`: solo el principal; `git branch --list 'review-*'`: vacío. Los worktrees de las revisiones
  en paralelo (C5 de `review_F-011_C1C2C5.md`) ya están limpios.
- `git status --short`: solo `` `0`].{t `` (vacío, 2026-09-24, anterior a la rama, ajeno y anotado) y este informe.

## (1) H1 de `review_F-011_C1C2C5.md`: **resuelto**

- Título nuevo («revisión aprobada por bloques; faltan revisión final, merge, T13 y T14»). «Lo siguiente» da F-011
  `in_progress` (ya no `pending` ni D1-D4 sin decidir). El prompt para retomar abre con F-011 y lo que falta.
- **T13 y T14 listadas con su comando:** T13 (humano) `! func azure functionapp publish func-sigridapi-dev-huyke
  --python`, sin App Settings nuevas, tras merge y push. T14 (líder): script Python en el scratchpad que lee la key
  del `.env` sin escribir al repo, pasos 1-5 con su esperado y el PARAR del paso 2; los cuerpos exactos, enlazados a
  design §Verificación manual (criterio aceptado en F-010). Después, quitar «PENDIENTE DE DESPLIEGUE» de `azure-apps`
  y `done`. Cierra también la nota que H1 dejaba para C4.

## (2) fb9e890: sin código, y la guía ajustada es correcta

Aplicadas las cuatro observaciones de `review_F-011_C4.md` en `design.md`:

1. **Cuerpo exacto del paso 5**, contrastado con el modelo:
   - `AddContractLinesRequest` (`domain/models/sigrid_domain_models.py` l. 26-50) exige `cod_contrato`, `cod_obra`,
     `cif_proveedor` (min 1) y `lines` (≥ 1); `ContractLineInput` (l. 9-23), `res` (min 1), `can` y `pre`. El cuerpo
     `{"database":"ruesma;APP=f011","cod_contrato":"F011-NO-EXISTE","cod_obra":"F011","cif_proveedor":"F011","lines":[{"res":"f011","can":1,"pre":0}],"commit":false}`
     **pasa la validación** (el strip de `database` no quita el `;`).
   - Llega a `locate_contract` (`add_contract_lines_use_case.py` l. 38) → `_connect` l. 80: `validate_identifier`
     lanza `IdentifierValidationError(ValueError)` antes de `pyodbc.connect`. La ruta (`function_app.py` l. 181-187)
     da 400 con `details.type` = `IdentifierValidationError`, y el texto de `identifier_guard.py` l. 19 coincide
     literalmente con el de `design.md`.
   - El criterio de PARAR (400 `ValueError` «No se encontro un contrato…» = se conectó) es correcto: es el
     `raise ValueError` de l. 45 del caso de uso con el código viejo.
2. **Paso 5 solo tras un paso 2 correcto**, y consta la autorización del humano del 2026-10-18.
3. **Los 400 se leen con `try/catch` + `StreamReader`** de `azure-apps/sigrid_api.md` §11 (existe, l. 1433); el líder
   usa `urllib`, que lee el cuerpo sin ese apaño.
4. **Paso 0:** patrón por elemento, `SIGRID_DOCUMENT_WRITE_DATABASE` vacía = apagado, consulta clave a clave si `||`
   falla. El paso 4 añade `sql/read` sobre `ruesma` (`dbo.con`, `tip = ?` con 44, parametrizado).

**T12** `[x]` en `tasks.md`, resultado en `verificacion_F-011.md`: las tres claves leídas de Azure, cada elemento
casa con `^[A-Za-z_][A-Za-z0-9_]*$` y `ruesma_rep` está literal en `ALLOWED_DATABASES`. Sin secretos (Function App y
grupo de recursos ya en `azure-apps` §11; ni suscripción ni tenant). Commit `F-011: … T12 hecha …`: mismo formato
que la MANUAL de F-010 (`2f5b6cb F-010: T13 hecha …`), vale.

## (3) Checkpoints (consolidado; detalle en los informes de bloque)

- **C1** [x] `init.sh` exit 0 (esta pasada) · [x] los siete ficheros base (C1C2C5).
- **C2** [x] una sola `in_progress` · [x] rama `feature/F-011-…` · [x] `current.md` solo con la sesión activa (H1
  cerrado; F-009 y F-006 se quedan por sus pendientes vivos, como admitía H1) · [x] toda `done` en `history.md`.
- **C3** (`review_F-011_C3.md`, APPROVED): [x] hexagonal · [x] primera línea con ruta · [x] sin prints, TODOs,
  secretos ni dependencias nuevas · [x] base correcta · [x] SQL parametrizado (no hay SQL nuevo; la cadena ODBC usa
  el valor validado) · N/A `con`/extensión, recálculo y estados: no hay SQL ni escrituras nuevas (justificado allí).
- **C3 bis** N/A los cuatro: el diff no toca `docs/referencia/` (0 ficheros).
- **C4** (`review_F-011_C4.md`, APPROVED): [x] R1-R15 con ≥ 1 test trazable en verde (R16 documental, R17 MANUAL,
  por diseño) · [x] sin red ni BBDD (dobles, `pyodbc.connect` prohibido, `Settings.model_construct`) · [x] MANUAL
  listadas con comando en `current.md` (punto 1).
- **C4 bis** (`review_F-011_rojo.md` y `review_F-011_mutacion.md`, APPROVED):
  - [x] `rigor: "critico"` · [x] fase RED con trazas reales (T1, T3, T4, T5) · [x] cobertura `[OK]` 100 % de 16,
    reproducida hoy.
  - [x] mutación: recálculo puro 43 líneas y 2 mutantes, coincide · [x] muertos comprobados (83,7 s > 60 s, pero el
    reviewer reejecutó en serie sobre `4d1c266`: 2/2 muertos, 0 sin veredicto, 105,0 s) · [x] coste 41,9 s/mutante ·
    [x] sin cabecera de campaña no válida, base rota = 0.
  - [x] RM1: midió `cafc340`, lo posterior no toca el alcance (lo confirma la campaña sobre `4d1c266`, y `fb9e890`
    tampoco lo toca) · [x] RM2: 2 × 41,8 ≈ 83,7 s, media/base 0,68 con 1 worker · [x] RM5: sin equivalentes (M14 se
    hizo observable con un test) · [x] RM6: no se quitó ninguna guarda.
  - [x] manual del reviewer: 23 filas con texto exacto y nº de fallos, 23/23 muertas (complementa, no sustituye) ·
    [x] 0 supervivientes · [x] «Evidencias» con los cuatro números y 1 worker · [x] ningún N/A sin motivo.
- **C4 ter** N/A formal: no existe `harness/rutas_sensibles.json` e `init.sh` no señala rutas. Aun así se verificó
  `_connect` (punto único de conexión, los 8 métodos pasan por la guarda; C4).
- **C5** [ ] aceptado como en F-010: T1-T12 y T15 `[x]`; **T13 y T14 abiertas**, MANUAL, imposibles antes del merge
  (T13 despliega `dev`). Bloquean el `done`, no este APROBADO · [x] un commit `F-011 Tn:` por tarea (T7-T8 comparten
  `cafc340`, criterio de F-010) · [x] sin artefactos de la feature sin trackear · [x] `features.json` `in_progress`.

## Cobertura requisito → test (resumen; tabla completa en `review_F-011_C4.md`)

| R | Test |
|---|---|
| R1-R6, R8, R10 | `tests/test_f011_caso_de_uso.py::test_f011_rN_*`; R1, R4, R8 también en `test_f011_ruta.py` |
| R7 | `tests/test_f011_composicion.py::test_f011_r7_*` |
| R9 | `tests/test_f011_ruta.py::test_f011_r9_el_rechazo_deja_un_warning` |
| R11-R12 | `test_f011_r11_*` y las suites de F-010, intactas |
| R13-R15 | `tests/test_f011_repositorio.py` (8 métodos × bases inválidas; cadena idéntica a `dev`; valor devuelto) |
| R16 | revisión documental: `ARCHITECTURE.md` y `azure-apps` `7bddfd4` (C3) |
| R17 | MANUAL: T14, pasos 1-5 |

## (4) Qué bloquea qué

- **Merge a `dev`:** nada lo bloquea; no hay cambios requeridos.
- **T13** (humano) va tras el merge. T12 está en OK, así que no hay que PARAR antes de desplegar.
- **T14** (líder, lecturas + el dry-run autorizado) va tras T13. Resultados a `verificacion_F-011.md` y fuera las
  notas «PENDIENTE DE DESPLIEGUE» de `azure-apps/sigrid_api.md`. Si el paso 2 o el 5 fallan: PARAR, sin cierre.
- **`done`:** exige T13 y T14 `[x]` y una pasada incremental del reviewer sobre ese delta (como el «Cierre de C5»
  de F-010).

## Observaciones (no bloquean)

- **O1:** recortar al cerrar los bloques de F-009 y F-006 de `current.md`, como el O1 de F-010.
- **O2:** siguen sin decidir las propuestas al arnés de los bloques: C4/C5 frente a las MANUAL posteriores al merge
  (tercera vez), `harness/rutas_sensibles.json` con `sql_server_repository.py`, y los operadores `in`/`not in` y
  literales en `harness/mutacion.py`. Ya anotadas en `current.md` y en `arnes-base`.

## Cambios requeridos

Ninguno.
