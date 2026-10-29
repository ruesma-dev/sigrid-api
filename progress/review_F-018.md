<!-- progress/review_F-018.md -->
Revisión incremental desde `3fcca4c` (pasada 3) hasta HEAD `21763d9`; `azure-apps` desde `d53a4f6` hasta `6ceabb0`

# F-018 · Veredicto consolidado

- **Veredicto: APROBADO** para merge a `dev`. El `done` sigue bloqueado por T19-T21 (MANUAL tras el despliegue y el
  cierre), con el criterio aceptado por el humano desde F-010.
- **Rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 %, mutación con cero
  supervivientes (o equivalentes demostrados, con RM5 sobre uno), RM1-RM6 y C4 ter si hay rutas sensibles declaradas.
- **Historia:** la pasada 1 fue la revisión troceada de T18 (seis informes `review_F-018_*.md`). La pasada 2 (`3fcca4c`)
  verificó sus correcciones y pidió tres frases. La pasada 3 (esta) revisa solo ese delta; lo aprobado antes se da por
  bueno. No he cambiado de rama, no he aplicado mutantes, no he editado nada, ni he tocado Sigrid ni la API.

## Pasada 3: los cambios 1-3 de la pasada 2

| Cambio | Ahora dice | ¿Resuelto? |
|---|---|---|
| 1 · `contrato_proformas.md` §3 (l. 218-219) | «más si el propio `ctrpro` no cumple `pre` = `tot`/`can` **o si `cantidad` > `ctrpro.can`**» | sí |
| 2 · `contrato_proformas.md` §8 (l. 434-435) | «hasta un céntimo por línea frente a `importe_mes` **con `cantidad` ≤ `ctrpro.can` y `pre` = `tot`/`can`**» | sí |
| 3 · `azure-apps/sigrid_api.md` §8.10 (l. 1432-1433) | «con `cantidad` ≤ `ctrpro.can` **y un `ctrpro` con `pre` = `tot`/`can`**; a origen, más, §8.10.1» (§8.10.1 existe, l. 1444) | sí |
| Extra · cabecera punto 4 (l. 23-25) y §4 (l. 355-358) | Antes, «más de unas cinco líneas», que suponía la cota de un céntimo (5 × 0,01 = la tolerancia de 0,05 de `existente`). Ahora añade «menos si alguna no cumple las dos condiciones». Correcto y coherente | sí |

**Mi `grep`** de «céntimo», «tolerancia», «0,05» y «±» en los dos contratos, `ARCHITECTURE`, `verificacion_manual`
y `azure-apps/sigrid_api.md`:

- Toda cota de un céntimo ligada a F-018 lleva ya sus dos condiciones:
  - proformas l. 18-19, 218, 434 y 355-358;
  - albaranes l. 70-74 y 363-366;
  - `azure-apps` l. 1171-1174 y 1432.
- La cota a origen dice «no acotada» en proformas l. 269 y en `azure-apps` l. 1471.
- Lo demás es ajeno a la cota:
  - la tolerancia 0,0001 de H14 y el ±0,05 de la hoja y de sv9;
  - `verificacion_manual` l. 108 y 132, que comparan con el `tot` del escritorio, calculado con la misma fórmula
    `round(can·tar·(1 − d))` que R15, así que no dependen de la cota.
- **Revisado y no es defecto:** proformas l. 155-156 (la punta con `importe_cadena` = ANTERIOR ± 0,05).
  - Es una sugerencia para la bandeja, medida en M25 sobre cadenas escritas por Sigrid, que ya cumplen `pre` = `tot`/`can`.
  - F-018 hace que la API escriba igual que esas cadenas.
  - Si no sale una única punta, elige la persona.

**Código intacto.** `git diff 3fcca4c --stat` toca solo `contrato_proformas.md` y `progress/impl_F-018.md`.
`git diff d53a4f6 --stat` en `azure-apps` toca solo `sigrid_api.md`. Desde la campaña (`7ce2240`) no ha cambiado
ningún `.py` ni `tests/`, así que mutación, RED y cobertura siguen valiendo para HEAD.

**`bash harness/init.sh`** (tal cual y solo):

- **Ejecución:** de 14:31:28 a 14:37:55, sobre `21763d9`, con el árbol limpio y sin cambio de rama en el reflog.
  Exit 0 y «ENTORNO LISTO».
- **Suite:** **3793 passed, 1 skipped, 1 warning in 313.94s**.
- **Puertas:** COBERTURA `[OK]` 100.0 % de 102 líneas (umbral 80 %, critico); TAMAÑO `[OK]` (requirements 135/150,
  design 242/250, impl **220/220**, review 137/140); BACKLOG al día; `features.json` y `rigor.json` válidos.
- **Avisos:** F-015 y F-016 `blocked` (esperado) y ruff con 79 avisos (deuda previa).

## Pasada 2 (consolidado, `3fcca4c`): lo verificado y que sigue en pie

- **Cambios de `docs` 1-7 y O1, y H1-H2 de `C1C2C5`: resueltos.**
  - Contratos acusados y pendientes de despliegue. El «no admite `dto`» es cierto en `dev`: `LineaAlbaranIn` con
    `extra="forbid"`.
  - Cota a origen «no acotada» y cota de albaranes con sus dos condiciones.
  - El clásico y el directo «ignoran» `dto`.
  - §13 y §10 de `azure-apps` al día.
  - V3 acotada; V4 con la obra y el CIF que fija el humano (coherente: `$cuerpoA` es sin vincular).
  - `current.md` al estado real; `features.json` con R7 y sus excepciones; `BACKLOG.md` regenerado.
  - La decisión del líder sobre el cambio 3 (forma de Sigrid, M46) está documentada.
- **Cifras recalculadas** con `importe_con_dto`, `importe_linea`, `usa_precio_del_contrato` e `importe_de_cadena`:
  - Datos: `ctrpro` de 36 uds, `tar` 4,278, 40 %, que da `tot` 92,40.
  - A origen: 77,10/77,00, 76,80/77,00 y 92,34/92,40.
  - Vinculada de 1.000 uds: 2.566,80/2.566,67.
  - Barrido de 200.000 casos: con las dos condiciones, la peor diferencia es 0,01; sin ellas, 0,25.
- **Incidencia del checkout a `dev` (13:23:30-13:23:44):** ningún resultado aprobado se midió sobre `dev`.
  - `mutacion` y `C4red` midieron en worktrees.
  - Los 427 de `C3C4ter` incluyen `test_f018_*`, que no existe en `dev`.
  - El lado «rama» del cruce R7 de `logica` es de las 13:23:24, antes del checkout. Su `cruce.py`, reejecutado sobre
    `706f9c8`, da una salida idéntica byte a byte a la de `dev` (440.149 bytes).
  - El `init.sh` de la pasada 2 (13:54-14:00, 3793 passed) y el de esta cubren las suites.

## Consolidación contra `CHECKPOINTS.md`

- **C1:** [x] `init.sh` con exit 0. [x] Existen los ficheros base.
- **C2:**
  - [x] Una sola `in_progress`.
  - [x] Rama correcta, con `dev` como ancestro.
  - [x] `current.md` al día (H1).
  - [x] Toda `done` en `history.md`.
- **C3** (`C3C4ter`):
  - [x] Hexagonal; primera línea con la ruta; sin prints, TODOs ni secretos.
  - [x] Reglas de Sigrid: base, `con`, nada recalculado solo, sin estados fijos.
  - [x] Sin SQL nuevo (huella idéntica a `dev`).
- **C3 bis:** N/A con motivo: ni F-018 ni el delta tocan `docs/referencia/`.
- **C4** (`C4red`, `logica`): [x] un test por requisito; [x] sin red ni BBDD; [x] V0-V5 en `current.md`, V4 con
  autorización expresa.
- **C4 bis:**
  - [x] `critico`; RED con salida real, reproducida en 5 commits; cobertura `[OK]` al 100 %.
  - [x] Mutación 66/66 muertos: base corrida, sin cabecera «⚠ CAMPAÑA NO VÁLIDA», «Workers 1» y totales recalculados.
  - [x] Campaña **no reejecutada** (1.637,7 s según el informe), pero con RM4 sobre 4 mutantes en worktree.
  - [x] RM1 con SHA completo `e649e38` (el delta no toca `.py`) y RM2 coherente (24,8 s por mutante).
  - [x] RM5: N/A con motivo, no hay equivalentes. RM6: no se quitó ninguna guarda.
  - [x] Campaña manual: N/A con motivo, hubo 66 mutantes automáticos.
  - [x] Cero supervivientes; «Evidencias» con los cuatro números.
- **C4 ter:** N/A con motivo: no existe `harness/rutas_sensibles.json`. Las rutas de escritura se revisaron igualmente
  (sin endpoint, sin App Setting y sin `DELETE`).
- **C5:**
  - [ ] T18-T21 abiertas: bloquean el `done`, no el APROBADO (criterio del humano desde F-010). T18 se marca con
    este veredicto.
  - [x] Un commit `F-018 Tn:` por tarea, en español y con su pie.
  - [x] Árbol limpio y un solo worktree.
  - [x] `features.json` al día.
- **Documentación y contratos** (R28): [x] tras la pasada 3.

**Cobertura requisito → test** (detalle en `review_F-018_logica.md` y `review_F-018_C4red.md`):

- R1-R9, R11-R18, R20-R24 y R26: tests `test_f018_rN_*` en los cinco ficheros `tests/test_f018_*.py`.
- R10: aserciones `# (R10)` en `test_f018_r24_commit_vinculada_r15` y en un test `r15`.
- R19: las suites del clásico y del directo sin tocar, más el dorado `f009_caracterizacion`.
- R7: además, el cruce contra `dev`.
- R25 se cubre en C4 bis; R27 es MANUAL (`verificacion_manual.md`); R28 son los documentos.

**Para el líder:** `impl_F-018.md` está en 220/220, en el tope. Cualquier línea más pone la PUERTA TAMAÑO en rojo.

## Automejora (propuesta, no aplicada)

- **Para `reviewer.md` y `arnes-base`:** quien corrige una cota numérica de un contrato busca la misma frase en
  **todos** los contratos y en `azure-apps`. En la pasada 3 el implementer lo hizo y encontró la frase de «unas cinco
  líneas». Conviene dejarlo escrito como paso obligatorio.
- **Para `arnes-base`:** los informes troceados deberían anotar la hora de cada medida en el árbol principal, y los
  reviewers no deberían hacer `checkout` en el árbol principal (propuesta de `C1C2C5`).
