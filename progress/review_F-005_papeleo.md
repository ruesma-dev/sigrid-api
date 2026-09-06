<!-- progress/review_F-005_papeleo.md -->
# F-005 · Revisión ACOTADA (papeleo) — C1,C2,C5,C4,C4 ter,C4 bis(RED+cob),doc

Pasada de papeleo, ámbito completo asignado. SHA revisado: `becd3b8` (código
sigue en `cfb8048`; `becd3b8` solo toca `progress/`). No ejecuté `init.sh` ni
la suite completa (dato del líder: verde, 1.502 pasan, cobertura 100 % 7/7,
tamaño OK); sí `pytest -k f005 -q` y una reproducción de la fase RED en
worktree aislado, en la pasada anterior. Código, diseño y campaña de
mutación: fuera de mi ámbito (otro reviewer).

## Veredicto: APROBADO (papeleo)

## C1 — OK
Ficheros obligatorios presentes. `init.sh` verde según el líder.

## C2 — OK
Una sola `in_progress` (F-005). Rama correcta. `current.md` ya no dice que el
merge de F-004 está pendiente (`becd3b8` lo corrige: F-004 mergeada en `dev`
`70ac430` y empujada); lo que queda es el merge de F-005, pendiente de este
veredicto.

## C4 — OK (saldado tras `becd3b8`)
Trazabilidad acceptance→test: 1→(a), 2→(b), 3→(e), 5 (sin red, RED) y 7 (doc)
verificados en la pasada anterior; 4 y 6 fuera de mi ámbito (diseño/diff y
mutación); 9 (init.sh) es dato del líder.

**8 (MANUAL obra 0404), antes CHANGES_REQUESTED, ahora resuelto.**
`becd3b8` añade a `current.md` la sección «Verificación MANUAL de F-005 en la
obra 0404 (humano), con su comando exacto», con los dos conceptos ya
localizados (contrato `CTSB20/0519` ide 1686634 tip 44; albarán `AC26/15950`
ide 2774375 tip 14) y:
- **M1**: JSON de las App Settings a `[708,44,14]`/`[35,0]` y el `az
  functionapp config appsettings set`/`list` exactos.
- **M2**: cuerpo JSON del dry-run para los dos conceptos (`gratipide:0`), los
  negativos (`gratipide:40` y `99`) y el criterio con `MAX(ide)`.
- **M3**: el `commit:true`, el `documents/read` por `cod`, las tres consultas
  SQL de comprobación, el criterio incluyendo la ficha de Sigrid, y la
  repetición idempotente.
Es un comando reproducible sin reconstrucción por parte del humano, al mismo
nivel de detalle que el guion T18-T21 de F-004 que motivó la exigencia. La
sección queda inmediatamente después de la lista «Lo que espera al humano»,
claramente rotulada y localizable.

## C4 ter — N/A (justificado)
No existe `harness/rutas_sensibles.json`: el bloque es N/A por ausencia de
declaración.

## C4 bis (solo RED y cobertura) — OK
Sin cambios respecto a la pasada anterior: RED reproducida en worktree sobre
`ca2b123` (10 failed/13 passed, idéntico a la traza de `impl_F-005.md`);
cobertura 100 % (7/7) reportada por `init.sh`, dato del líder.

## Fidelidad documental — OK
Sin cambios: `azure-apps/sigrid_api.md` en `5e9a7bc` (§4 y §8.8) coincide con
el código (`document_write_guard.py:162`, `attach_concepto_grafico_use_
case.py:272`, `concepto_grafico_models.py:75`).

## C5 — OK
`git status` limpio salvo el commit de papeleo `becd3b8`. `tasks.md` N/A
(sdd=false). `features.json` refleja el estado real.

## Cambios requeridos
Ninguno.
