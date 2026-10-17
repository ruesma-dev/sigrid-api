<!-- progress/review_F-010.md -->
Revisión incremental desde `c3d4e45` (pasada 2, final consolidada) · punta `cf5bbda`, último código `64ffde0`

# Review F-010 · Veredicto final consolidado

Reviewer, 2026-10-17. Lo aprobado en los troceados hasta `c3d4e45` queda dado por bueno salvo donde
el delta lo toca; `init.sh`, la suite y la campaña de mutación se han ejecutado **enteros** sobre la punta.

## Veredicto: RECHAZADO (solo papeleo; el código queda aprobado)

El código final es correcto: H1 cerrado y medido, `init.sh` en verde, mutación **24/24 muertos** sobre
el código final. Rechazo por dos checkboxes de evidencia que el arreglo de H1 y la reescritura de H2
dejaron en `[ ]` (C4 bis·Mutación/RM1 y C4·manuales). **No hay que tocar código ni tests.** La pasada 3
puede ser incremental solo sobre `progress/` (más `init.sh`).

## Nivel de rigor

`critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 % de lo cambiado,
mutación completa con **cero supervivientes** sin test o justificación aceptada por el humano, y las
`MANUAL (humano)` listadas con su comando exacto.

## Cambios requeridos

1. **H3 · `progress/mutacion_F-010.md` no mide el código que se revisa (RM1).** Declara SHA `bb4a612`,
   198 líneas y 23 mutantes; `64ffde0` tocó tres ficheros del alcance (`read_document_use_case.py`,
   `sql_repository.py`, `sql_server_repository.py`) y el alcance real es **209 líneas y 24 mutantes**
   (el nuevo: `read_document_use_case.py:26`, `is not None` → `is None`). Regenerar con
   `python -m harness.mutacion --feature F-010 --workers 1` sobre la punta, sin `Edit`/`Write`
   mientras corre, y poner al día la tabla «Evidencias» de `progress/impl_F-010.md` (l. 150-161,
   hoy previa a H1: suite 2530 passed/1 skipped, F-010 160 tests, 24 mutantes). Resultado esperado,
   ya medido por mí: 24/24 (ver «Mutación»).
2. **H4 · `progress/current.md` (lo lleva el líder).** (a) l. 17-19: H1 sigue «en corrección por el
   implementer» y la mutación «en remedición»; ya están cerrados (`64ffde0`, `cf5bbda`). (b) l. 23-24:
   T13-T15 se listan **sin comando ni enlace a él**. La reescritura de H2 (`0443a4c`) borró el bloque
   que decía «comandos en design §Verificación manual», que es justo en lo que se apoyó el `[x]` de C4
   en `review_F-010_C4.md` (l. 26-28 y 102). Basta con enlazar `specs/F-010-…/design.md` §Verificación
   manual (l. 216) y el comando de T14 de `tasks.md` l. 17.

## H1 y H2

- **H1 cerrado.** `64ffde0`: `build_document_query`, puerto y adaptador aceptan `key_field_name="key"`;
  el caso de uso pasa `"id_column"` si no hay `key` (`read_document_use_case.py:26`). Medido en una copia
  de `dev` (`git archive dev`): `id_column=" ide;x "` → `IdentifierValidationError`
  `"El identificador 'id_column' contiene caracteres no permitidos: ide;x"`; en la rama el test
  `test_f010_r12_id_column_no_valido_conserva_su_texto` exige ese literal y pasa, y
  `test_f010_r10_key_no_valida_informa_key` mantiene `'key'` con `key`. **RED reproducido** en una copia
  de `64ffde0` quitando la l. 26: mismo fallo que pega `impl_F-010.md` l. 179-184 (`'id_column'` →
  `'key'`), `1 failed, 1 passed`. Sin cambios en SQL, parámetros, código 400 ni `infrastructure/security/`.
  Desviación de las firmas de `design.md` (l. 143, 155): declarada en «Corrección H1», aceptada.
- **H2 cerrado en lo requerido** (F-010 arriba con T13-T15 y aviso a albaranes; «Lo siguiente» y el
  prompt nombran F-010). Deja dos restos nuevos (H4) y uno heredado no bloqueante (O1).

## Puertas medidas por mí

| Puerta | Resultado real |
|---|---|
| `bash harness/init.sh` | exit 0, **ENTORNO LISTO**; `2530 passed, 1 skipped` en 48,1 s; ruff 79 avisos (deuda previa) |
| Cobertura | `[OK]` **100,0 % de 80 líneas cambiadas** (80/80, umbral 80 %, nivel critico) |
| Tamaño | `[OK]` requirements 122/150, design 248/250, impl 195/220 |
| Mutación (serie, worktree aislado en `cf5bbda`, salida en scratchpad) | **24/24 muertos**, 0 superv., 0 timeouts, 0 sin veredicto, 183,5 s, base 46,8 s, media 7,6 s |

## Mutación (C4 bis + RM1-RM6) sobre el código final

- Recálculo puro (`alcance_de_feature` + `generar_mutantes`) en la punta: 7 ficheros, **209 líneas,
  24 mutantes**, idénticos uno a uno (operador y texto) a los evaluados por mi campaña. Los 23 previos
  coinciden con `review_F-010_mutacion.md`; el 24.º es el de H1 y sale **muerto** ([1/24]).
- Campaña: `python -m harness.mutacion --feature F-010 --workers 1 --rama feature/F-010-… --salida
  <scratchpad>` en un worktree *detached* en `cf5bbda` (código = `64ffde0`; `64ffde0..cf5bbda` solo
  añade `review_F-010_mutacion.md`). Sin `Edit`/`Write` durante la campaña. Línea base en verde. Worktree
  retirado y `git status` limpio después (solo el ajeno `` `0`].{t ``).
- [x] 183,5 s > 60 s, pero la campaña se **reejecutó entera** (encargo). [x] Coste por mutante
  183,5 × 1 ÷ 24 = 7,6 s (> 1 s). [x] Sin «⚠ CAMPAÑA NO VÁLIDA» ni «Sin veredicto» ≠ 0.
- [ ] **RM1** en mi medición sí (SHA `cf5bbda3…` = HEAD); **en el informe de `progress/` no** → H3.
- [x] **RM2**: 24 × 7,6 = 182,4 ≈ 183,5 s; media/base = 0,16 (> 0,1); media < base explicada por `-x`.
- [x] **RM3**: ningún equivalente sale muerto; el nuevo cambia qué campo cita el error (observable).
- [x] **RM4**: usado para el RED de H1 (copia en scratchpad). N/A **RM5**: rigor `critico`, pero no hay
  ningún equivalente declarado ni superviviente que muestrear. [x] **RM6**: `64ffde0` no quita código
  defensivo; lo de `strict=True` ya lo juzgó `review_F-010_mutacion.md`.
- [x] Cero supervivientes: no hay análisis `PENDIENTE` ni justificación que pedir al humano.

## Checkpoints (consolidado)

Detalle en [`review_F-010_C4.md`](review_F-010_C4.md), [`review_F-010_C1C3C5.md`](review_F-010_C1C3C5.md)
y [`review_F-010_mutacion.md`](review_F-010_mutacion.md); aquí, si siguen valiendo tras `64ffde0`.

- **C1** [x] `init.sh` exit 0 (medido hoy; el troceado lo dejó N/A) · [x] siete ficheros base.
- **C2** [x] una sola `in_progress` (F-010) · [x] rama `feature/F-010-documents-read-nombres-y-clave` ·
  [x] `current.md` solo la sesión activa en lo exigido por H2 (restos: H4a, O1) · [x] toda `done` en
  `history.md` (sin cambios desde el troceado).
- **C3** [x] hexagonal: el caso de uso pasa un `str` al puerto, nada de infraestructura en dominio ·
  [x] primera línea con ruta (ficheros del delta sin cambio de cabecera) · [x] sin `print`, TODO,
  secretos ni dependencias nuevas · [x] trampas Sigrid: solo lectura de `ruesma_rep` por
  `documents/read`, SQL con `?`, nada que escribir ni recalcular (sin cambio en el delta).
- **C3 bis** N/A: ningún fichero en `docs/referencia/` (`git diff dev...HEAD --stat`).
- **C4** [x] trazabilidad R1-R18 (tabla en `review_F-010_C4.md`; R12 gana tres tests en `64ffde0`) ·
  [x] unit tests sin red ni BBDD (los nuevos parchean `pyodbc.connect` para fallar si se llama) ·
  **[ ] manuales listadas con su comando exacto en `current.md`** → H4b.
- **C4 bis** [x] `rigor` declarado · [x] fase RED (troceado + RED de H1 reproducido) · [x] cobertura
  `[OK]` 100 % · **[ ] mutación con totales reales del código revisado** → H3 · [x] muertos comprobados ·
  [x] coste por mutante · [x] sin cabecera de campaña no válida · [ ] RM1 → H3 · [x] RM2 · N/A RM5
  (sin equivalentes) · [x] RM6 · N/A campaña manual (la automática dio 24 mutantes) · [x] sin
  supervivientes · [x] «Evidencias» existe con los cuatro números y workers, pero previa a H1 → H3.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json` y `init.sh` no señala rutas.
- **C5** · tareas: T1-T12 y T16 `[x]` con commit `F-010 Tn:` (T9-T10 comparten `2bcda71`; H1 va como
  `F-010 H1:`). **T13-T15 abiertas, MANUAL (humano)**: T13 es antes del despliegue, T14 es el
  despliegue y T15 después; no pueden estar hechas en la revisión de código, y C4 exige precisamente
  que figuren «pendientes de que el humano las ejecute». **Pero C5 no las exime**: dice «todas las
  tareas `[x]`». Por tanto, una vez corregidos H3 y H4, el APROBADO de código **autoriza el merge a
  `dev`** (necesario para T14), **no el `done`**: F-010 pasa a `done` cuando T13-T15 estén `[x]`, o si
  el humano acepta por escrito cerrar con ellas pendientes (precedente: F-009 cerrada con T24).
  [x] sin artefactos de la feature sin trackear · [x] `features.json` coherente (`in_progress`).

## Observaciones (no bloquean)

- **O1** `current.md` l. 26-93: el bloque F-009 conserva el guion T19-T23 ya ejecutado y F-006 su lista
  completa; H2 admitía dejar lo pendiente «como lista corta o en `history.md`». Recortar al cerrar.
- **O2** La puerta de cobertura sigue en 80 líneas tras H1: lo añadido son líneas de continuación
  de llamadas y firmas ya contadas; las cubre la suite (24.º mutante muerto).
- **O3** El hook `PostToolUse` no estorbó esta vez (sin `Edit`/`Write` durante la campaña, cero falsos
  supervivientes). Sigue en pie la automejora de `review_F-010_mutacion.md` (portar a `arnes-base`).

## Automejora propuesta (no aplicada)

`CHECKPOINTS.md` C5: decir explícitamente qué pasa con las tareas `MANUAL (humano)` posteriores al
merge (despliegue y verificación): hoy C4 las quiere pendientes y C5 las quiere `[x]`, y cada cierre lo
resuelve a su manera. Propuesta: «toda tarea `[x]` salvo las MANUAL posteriores al merge, que
bloquean el `done` pero no el APROBADO». Vale para cualquier proyecto: a `arnes-base`.

## Cierre de H3 y H4 (pasada 3, incremental desde `913761a`, punta `1a68467`)

`git diff 913761a..HEAD --stat`: solo `progress/` (`current.md`, `impl_F-010.md`, `mutacion_F-010.md`); ni código ni tests.
- **H3 cerrado** (`956f30d`): `mutacion_F-010.md` mide `913761a` (mismo código que `64ffde0`; lo posterior no toca el
  alcance, RM1 [x]): 209 líneas, 24/24 muertos, 0 sin veredicto; 24 × 6,2 ≈ 148,3 s (RM2 [x]); cuadra con mi serie.
  «Evidencias» al día sobre `913761a`, con una sola cabecera de tabla.
- **H4 cerrado** (`1a68467`): sin «en corrección» ni «remedición»; T13-T15 enlazadas a `design.md` §Verificación manual.
- `bash harness/init.sh` entero sobre la punta: ENTORNO LISTO, 2530 passed/1 skipped, cobertura 80/80, TAMAÑO 138/140.

**Veredicto: APROBADO para merge a `dev`.** No es el `done`: C5 sigue con T13-T15 abiertas (MANUAL, humano).
