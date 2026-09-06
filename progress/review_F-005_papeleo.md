<!-- progress/review_F-005_papeleo.md -->
# F-005 · Revisión ACOTADA (papeleo) — C1,C2,C5,C4,C4 ter,C4 bis(RED+cob),doc

Pasada única de papeleo, ámbito completo asignado. SHA revisado: `4e0a940`
(código `cfb8048`). No ejecuté `init.sh` ni la suite completa (dato del
líder: verde, 1.502 pasan, cobertura 100 % 7/7, tamaño OK); sí `pytest -k
f005 -q` y una reproducción de la fase RED en worktree aislado. Código,
diseño y campaña de mutación: fuera de mi ámbito (otro reviewer).

## Veredicto: CHANGES_REQUESTED (papeleo)

## C1 — OK
Ficheros obligatorios presentes. `init.sh` verde según el líder (no
reejecutado, fuera del alcance de esta pasada).

## C2 — OK
Una sola `in_progress` (F-005). Rama correcta. `current.md` conserva
contenido de F-004, pero tiene resumen en `history.md` (l. 108-144) y lo que
queda es una acción **pendiente del humano** (el merge), no un resto de
sesión: se da por bueno.

## C4 — CHANGES_REQUESTED (un punto)
Trazabilidad acceptance→test (tabla de `impl_F-005.md`, verificada):
1→(a) 4 tests, confirmado en `use_case.py:272`. 2→(b) 4 tests. 3→(e) 4 tests.
4 (nada más se relaja/ficheros tocados): fuera de mi ámbito (diseño/diff).
5 (sin red, RED): OK, ver abajo. 6 (mutación): fuera de mi ámbito.
7 (doc azure-apps): OK, ver «Fidelidad documental». 9 (init.sh verde): dato
del líder.

`pytest -k f005 -q`: **23 passed** (1481 deselected), 1.53 s. Sin red/BBDD:
grep sobre los 5 test tocados no halla `requests.`/`socket`/`pyodbc`/
`urlopen`/`http`; usan `RepositorioDoble`.

**8 (MANUAL obra 0404) falla.** `current.md` (l. 11-20) da los valores
exactos de settings (`ALLOWED_CONTIP=[708,44,14]`, `ALLOWED_GRATIPIDE=
[35,0]`) pero para «hacer el dry-run y el commit:true sobre la obra 0404» no
da el cuerpo JSON, ni `conide`/`contip`/`gratipide` a usar, ni el SQL de
comprobación — a diferencia del guion T18-T21 que el mismo fichero conserva
para F-004 (l. 47-121) con bloques literales. Tampoco es un ítem de la lista
«Lo que espera al humano, por orden» (l. 25-46), solo aparece en el banner.
Sin eso el humano reconstruye la petición por su cuenta, justo lo que
«comando exacto» evita.

**Cambio requerido:** añadir a `current.md` un bloque para F-005 (análogo a
T19-T20): JSON de settings ampliadas, cuerpo exacto del `POST /api/sigrid/
concepto-grafico` en dry-run (con `conide`/`contip` reales de la obra 0404,
`gratipide:0`) y en `commit:true`, y los `SELECT` de comprobación (fila de
negocio, documental, `rcg`).

## C4 ter — N/A (justificado)
No existe `harness/rutas_sensibles.json`: el bloque es N/A por ausencia de
declaración.

## C4 bis (solo RED y cobertura) — OK
RED reproducida en worktree separado sobre `ca2b123` (tests) antes de
`cec651a`→`96500e4`→`f36a242`: `pytest -k f005 -q` da **10 failed, 13
passed, 1481 deselected**, idéntico en número y nombres a la traza de
`impl_F-005.md`. Tras la implementación completa, 23 pasan. Worktree
borrado, `git status` limpio.
Cobertura: `init.sh` (dato del líder) reporta `[OK] PUERTA COBERTURA: 100.0%
de 7 líneas (7/7, umbral 80%, nivel critico)`; no la repito, la reejecuta el
líder.

## Fidelidad documental — OK
`azure-apps/sigrid_api.md` en `5e9a7bc`: §4 documenta `0`=«sin clase» (solo
si se pone explícito) y que `ALLOWED_CONTIP` con 44/14 basta; §8.8 documenta
el campo `gratipide` con el `0`, mediciones 99,98 %/100 %, que con `0` no se
consulta `auxgra`, que hacen falta las dos settings y que clase >0 no se
relaja. Contrastado con código: `document_write_guard.py:162`, `attach_
concepto_grafico_use_case.py:272`, `concepto_grafico_models.py:75` (`ge=0`).
Coincide en los tres puntos.

## C5 — OK
`git status` limpio en la rama. `tasks.md` N/A (sdd=false, justificado por
cabecera de `CHECKPOINTS.md`). `features.json` refleja el estado real.

## Cambios requeridos
1. `current.md`: añadir el comando exacto (settings, cuerpo dry-run y
   commit:true, SQL de comprobación) para la verificación MANUAL de la obra
   0404, e incluirlo en la lista ordenada de pendientes del humano.
