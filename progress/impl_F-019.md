<!-- progress/impl_F-019.md -->
# F-019 · Actualización del arnés 1.7.8 → 1.10.1 (implementer)

Rama `feature/F-019-actualizar-arnes`. Nivel `documental` (sin fase RED, cobertura ni mutación).

## Método

Fusión **a tres bandas** de cada adaptado: nuestro fichero (propio), la 1.7.8 de `arnes-base` (commit `685da06`,
la versión instalada en `240257d`) como base, y el payload 1.10.1 (`arnes-base/arnes-base/`). Con `git merge-file`
**ninguno de los seis dio conflicto**: lo propio de sigrid-api (sustituciones de los `[ADAPTAR]`) y lo nuevo del arnés
no se pisan en ninguna línea. Revisé después cada resultado a mano contra la guía (apartados 1.7.16, 1.8.0, 1.9.0 y
F-070); no quedan marcas `[ADAPTAR]`.

Versión: `harness/VERSION` y `harness/ARNES_VERSION.md` ya decían **1.10.1** (los escribió el instalador; no los toqué).

## Por fichero

| Fichero | Aceptado del arnés | Conservado de sigrid-api |
|---|---|---|
| `.claude/settings.json` | entero: fuera `PostToolUse`, `$adaptar` nuevo, `model: claude-opus-5-5`, `effortLevel: high`, `ARNES_SIN_CACHE`, 7 permisos `python -m harness.*`/`backlog.py`, `git checkout -b` | nada: era idéntico al de la 1.7.8 |
| `docs/CONVENTIONS.md` | entero, con la sección «Git» (merges y push) | nada: idéntico al de la 1.7.8 |
| `harness/init.sh` | §3 (estados, una activa), §3 ter, §3b capa local `rigor.local.json`, §7 bis con `harness.cache_suites` y `ARNES_SIN_CACHE`, §7 quinquies carril, §7 sexies e2e | `RUTAS_PYTHON` de la API, título de la cabecera, §9 desactivada. `RAMA_BASE=dev` y `COMANDO_TESTS=""` ya eran los valores del arnés |
| `CLAUDE.md` | qa-e2e entre subagentes, primera parada = resumen de la spec, paradas con plantilla, push siempre humano y frase final, prioridad F-042 (`blocked > human_review > in_review > in_progress > spec_ready > todo`, una activa), regla «tal cual»/`ARNES_SIN_CACHE`, commits/merges/push, protocolo del repositorio del ecosistema (F-070) dentro del bloque de Ruesma | título, mapa del repositorio, reglas duras de Sigrid (producción, `ruesma_rep`, nunca `DELETE`, endpoints de dominio, SQL con `?`, `infrastructure/security/`), markitdown, convenios de Ruesma (`azure-apps`, `arnes-base`) |
| `CHECKPOINTS.md` | C1/C2 y prioridad, C3 ter, C3 quater, carriles, criterio de `critico` y muestra de C4 bis, muerte/`indeterminado`, casilla del PODADO, RM2, «Dos pasadas», capa e2e, capa local en «Niveles de rigor» | las cinco trampas de dominio de Sigrid en C3 |
| `docs/referencia/README.md` | nada: el del arnés no cambió entre 1.7.8 y 1.10.1 | entero (índice propio y puntero a `azure-apps`) |

`harness/rigor.json`: el nuestro no estaba afinado respecto a la 1.7.8, así que no hacía falta `rigor.local.json`.
`.gitignore` ya trae todas las líneas de `harness/gitignore.arnes`.

## Rama de integración

`git rev-list --count --no-merges dev..main` = **0**; `main..dev` = **424**. `dev` es la rama donde se integra:
`RAMA_BASE=dev` es correcto.

## Choques con lo propio (gana lo más estricto)

- **Merges.** Antes: «Commits locales sí» (merges sin regular). Ahora el arnés dice: merges a `dev` sin preguntar
  tras el OK del humano al resumen final; a `main`, preguntando. No es más laxo que lo que ya hace el humano (memoria:
  «yo mergeo local, él hace push»). El push sigue siendo siempre del humano en ambos textos. Lo dejo como el arnés.
- **Protocolo del ecosistema.** El del arnés (`pull --rebase`, solo el documento propio, commit aparte, push del
  humano, conflicto ⇒ `blocked`) es más estricto que el del CLAUDE.md global (`pull` + resolver en local). Queda el del
  arnés en el CLAUDE.md del proyecto, que manda sobre el global.

## Rojos encontrados

1. `init.sh` inicial (antes de fusionar): rojo en `test_cache_suites_init_sh.py::test_r23_…` (§7 bis vieja).
2. Suite completa sin `-x` (lanzada antes de fusionar): **26 rojos**, todos de los adaptados conservados:
   14 de `test_cache_suites_init_sh.py` (init.sh), 2 de `test_estados.py` (CLAUDE.md y CHECKPOINTS C2), 10 de
   `test_f004_settings.py` (settings.json). Ningún test propio de sigrid-api en rojo.
3. Tras la fusión: **ninguno**. No hubo que tocar código de la API ni `infrastructure/security/`.

## F-008 → `human_review`: NO aplicado (choca con la regla nueva)

Lo probé: con F-008 en `human_review` y F-019 en `in_progress`, el portero da
`[KO] Hay 2 features activas (in_progress/in_review/human_review): F-008, F-019. Máximo 1.` En la 1.10.1
`human_review` cuenta como activa (`harness/estados.py`, `ACTIVOS`). Revertí el cambio: **F-008 sigue en
`spec_ready`**. Opciones para el líder: pasarla a `human_review` cuando F-019 cierre (`done`), o al revés. No
improviso.

## Resultado real de `bash harness/init.sh` (tras las fusiones)

`ENTORNO LISTO`, exit 0. **6162 passed, 47 skipped** en 1554,70 s (25 min 54 s). Cobertura N/A, tamaño, carril y
e2e N/A u OK (nivel documental; sin `servicios.json`). Avisos no bloqueantes: F-015 `blocked`, ruff 113 (deuda
previa). Tras regenerar `BACKLOG.md` y escribir este informe (último commit) solo pasé el portero ligero (`ARNES_SALTAR_SUITES=1`): verde, tamaño impl 80/220. Ese commit no toca código ni tests.

## Commits

`28c4330` arnes_puro y nuevos del instalador · `7f35684` settings.json · `3139bc0` CONVENTIONS.md ·
`3492ae6` init.sh · `b1d1fcd` CLAUDE.md · `14180da` CHECKPOINTS.md · último: BACKLOG.md, current.md e informe.

## Dudas y pendientes

- F-008 a `human_review`: ver arriba; decide el líder/humano el orden.
- Ningún `todo` en `features.json`: con la 1.10.1 el líder debe pedir al humano qué comprometer (F-042).
- C3 (trampas de Sigrid) dice «tope de 1.000 filas por petición»; el CLAUDE.md global dice que la instancia desplegada
  sirve hasta 500.000 (`MAX_ALLOWED_ROWS`). Texto propio previo, fuera del alcance de esta fusión; no lo cambié.
- Los tests del arnés se llaman `test_f019_*` (F-019 del arnés: selección por mutante), homónimos de nuestra F-019.
  Sin efecto en las puertas hoy; lo anoto por si confunde en la revisión.
- Fin de línea: los ficheros fusionados se escribieron con LF; git avisa de que pasarán a CRLF (`autocrlf=true`).
- Sin verificaciones MANUAL. Sin mutación (nivel documental).
