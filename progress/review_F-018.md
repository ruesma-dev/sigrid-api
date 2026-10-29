<!-- progress/review_F-018.md -->
Revisión incremental desde `7ce2240` (pasada 2, consolidación de T18) hasta HEAD `706f9c8`; `azure-apps` hasta `d53a4f6`

# F-018 · Veredicto consolidado

- **Veredicto: CHANGES_REQUESTED.** Hay que cambiar tres frases de texto, y no se toca el código: la cota de un
  céntimo de la proforma **de mes** aparece sin todas sus condiciones (cambios 1-3). Todo lo demás está resuelto y medido.
- **Rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura ≥ 80 %, mutación con cero
  supervivientes (o equivalentes demostrados, con RM5 sobre uno), RM1-RM6 y C4 ter si hay rutas sensibles declaradas.
- **Qué se revisó:** lo aprobado hasta `7ce2240` por los seis bloques se da por bueno. El delta es `260cd2f`
  (texto), `9201846` (líder), `706f9c8` (informe) y `d53a4f6` (`azure-apps`). No he cambiado de rama, no he aplicado
  mutantes, no he editado nada, ni he tocado Sigrid ni la API.

## 1. Los cambios pedidos, uno a uno

| Pedido | Comprobado contra | ¿Resuelto? |
|---|---|---|
| docs 1: estado de `contrato_albaranes` | l. 54-57: «acusada por albaranes el 2026-10-29», «pendiente de despliegue». El «no admite `dto`» es cierto en lo desplegado (`dev` `6aca027`: `LineaAlbaranIn` con `extra="forbid"`). Punto 6 «Hecho» (`7aae0ba`) | sí |
| docs 2: estado de `contrato_proformas` | Cabecera l. 9-11 y §8 l. 431-434: acusada, pendiente de despliegue y la corrección anotada | sí |
| docs 3: cota a origen | l. 18-19 y §3.1 l. 266-273: «no acotada a un céntimo», crece con `canoriori`/`cantidad` y la hereda `importe_anterior_cadena`. **Cifras recalculadas** (abajo) | sí |
| docs 4: condición de la cota en albaranes | Punto 4 l. 69-74, §3.1 l. 362-366 y `azure-apps` §8.6 l. 1170-1174: `cantidad` ≤ `ctrpro.can` **y** `pre` = `tot`/`can`, con el contraejemplo. **Recalculado** | sí |
| docs 5: el clásico y el directo ignoran `dto` | `azure-apps` l. 1156-1159 y `ARCHITECTURE` l. 130-134: «lo ignoran», sin `extra="forbid"`, con el riesgo; solo la proforma da 400 | sí |
| docs 6: §13 y §10 de `azure-apps` | §13 l. 1789: F-016 desplegada el 2026-10-28; l. 1793: entrada F-018 pendiente. §10 l. 1666: cita la v1.3 | sí |
| docs 7: V3 y V4 | V3 l. 105-114: «sin avisos de precio ni de dto», y los dos ajenos explicados. V4 l. 137-145: obra y CIF los fija el humano, con previa antes del `commit:true`. Es coherente porque `$cuerpoA` es sin vincular (`cod_contrato` nulo). Resumen en `current.md` l. 29-33 | sí |
| O1 (`ARCHITECTURE` l. 118) | «Con `dto` pedido» | sí |
| H1 (`current.md`) | l. 4-21: F-018 al día. l. 35-42 y 71-74: F-016 en pasado. l. 236 y 245-251: «Lo siguiente» y el prompt al estado real. Sin «spec en redacción», «worktree», «No se empieza T1» ni «Siguiente: T0» | sí |
| H2 (`features.json`) | `acceptance[1]` con R7 y sus excepciones (R15, P9-P11). `title` y `description` con lo decidido en v1.2. `BACKLOG.md` regenerado (`init.sh`: «al día») | sí |
| Decisión del líder sobre el cambio 3 | Documentada sin tocar código: «forma de Sigrid, `pre` = `tot`/`can` (M46)», en el contrato §3.1 y en `azure-apps` §8.10 | sí |

**Cifras de los cambios 3 y 4, recalculadas** con `importe_con_dto`, `importe_linea`, `usa_precio_del_contrato` e
`importe_de_cadena` del código (script en el scratchpad, sin red). Datos: `ctrpro` de 36 uds, `tar` 4,278, 40 %, que
da `tot` 92,40 y `pre` 2,566667.

- **Cambio 3:** MES 1 y `canoriori` 30, **77,10** frente a 77,00; MES 0,5 y 30, **76,80** frente a 77,00; MES 2 y
  36, **92,34** frente a 92,40. En los tres, el `tot` del MES es igual al de la v1.2 (2,57; 1,28; 5,13).
- **Cambio 4:** 1.000 uds casan por la opción C (`True`) y dan **2.566,80** frente a **2.566,67**: 0,13 > 0,05.
- **Barrido de la cota** (200.000 casos aleatorios, semilla 18): con `cantidad` ≤ `can` y `pre` = `tot`/`can`, la
  peor diferencia es **0,01**; con `cantidad` > `can`, llega a **0,25**. La cota es cierta con sus dos condiciones y
  solo con ellas.

## 2. Código desde la campaña de mutación

`git diff 7ce2240 --stat` toca 14 ficheros: `BACKLOG.md`, `docs/ARCHITECTURE.md`, `harness/features.json`,
`progress/*` (siete), los dos contratos y `verificacion_manual.md`. **No toca ningún `.py` ni `tests/`**, así que la
campaña (medida en `e649e38`), la cobertura y la fase RED siguen valiendo para HEAD.

## 3. `bash harness/init.sh` (tal cual, solo, sin nada en paralelo)

- **Ejecución:** de 13:54:21 a 14:00:58, sobre `706f9c8`, con el árbol limpio y sin cambio de rama en el reflog.
  Exit 0 y «ENTORNO LISTO».
- **Suite:** **3793 passed, 1 skipped, 1 warning in 340.41s**. Tarda más que en los bloques (158-192 s), pero es
  tiempo de máquina y no cambia ningún resultado.
- **Puertas:** COBERTURA `[OK]` 100.0 % de 102 líneas (102/102, umbral 80 %, critico); TAMAÑO `[OK]` (requirements
  135/150, design 242/250, impl 219/220); BACKLOG al día; `features.json` y `rigor.json` válidos; rama correcta.
- **Avisos:** F-015 y F-016 `blocked` (esperado) y ruff con 79 avisos (deuda previa).

## 4. La incidencia del checkout a `dev` (13:23:30-13:23:44)

El reflog la confirma. Los cuatro bloques aprobados se commitearon entre 13:27:02 y 13:33:59, así que estaban
trabajando durante la ventana:

- **`mutacion` y `C4red`:** todo en worktrees. `C4red` repitió a las 13:28:57, con `git show` de la rama, su única
  lectura en el árbol principal. **No les afecta.**
- **`C3C4ter`:** la huella SQL se hizo en copias `git archive`, y las rutas con `git diff`/`git log`. Los «427
  passed» incluyen `test_f018_*`, que no existe en `dev`. **No le afecta.**
- **`logica`:** es el único con riesgo. Si el lado «rama» de su cruce R7 hubiera corrido en la ventana, habría
  comparado `dev` con `dev`. Los mtimes de su scratchpad lo descartan: `cruce_dev.json` es de las 13:23:20,
  `cruce_rama.json` de las 13:23:24 y `rama.txt` de las 13:22:42, todo **antes** del checkout. Aun así, **reejecuté su
  `cruce.py` sobre HEAD** (exit 0): la salida es idéntica byte a byte a su `cruce_dev.json` (440.149 bytes).

Mi `init.sh` (§3) cubre además las suites que los bloques ejecutaron en el árbol principal (243, 427, 1485 y 3793).
**Ningún resultado aprobado se midió sobre `dev`** en la ventana.

## 5. Consolidación contra `CHECKPOINTS.md`

- **C1:** [x] `init.sh` con exit 0 (§3). [x] Existen los ficheros base.
- **C2:**
  - [x] Una sola `in_progress`.
  - [x] Rama correcta, con `dev` como ancestro.
  - [x] `current.md` al día (H1).
  - [x] Toda `done` tiene su sección en `history.md`.
- **C3** (`C3C4ter`):
  - [x] Hexagonal; primera línea con la ruta; sin prints, TODOs ni secretos.
  - [x] Reglas de Sigrid: base correcta, `con`, nada recalculado solo, sin estados fijos.
  - [x] SQL parametrizado y sin SQL nuevo (huella idéntica a `dev`).
  - El delta solo es texto, así que no cambia nada de esto.
- **C3 bis:** N/A con motivo: ni F-018 ni el delta tocan `docs/referencia/`.
- **C4** (`C4red`, `logica`): [x] un test por requisito (abajo); [x] sin red ni BBDD; [x] V0-V5 en `current.md`
  l. 23-33, V4 con autorización expresa.
- **C4 bis:**
  - [x] `critico` declarado; RED con salida real, reproducida en 5 commits; cobertura `[OK]` al 100 %.
  - [x] Mutación 66/66 muertos: base corrida, sin cabecera «⚠ CAMPAÑA NO VÁLIDA», «Workers 1» y totales recalculados.
  - [x] Campaña **no reejecutada** (1.637,7 s según el informe), pero con RM4 sobre 4 mutantes en worktree.
  - [x] RM1 con SHA completo `e649e38` (el delta no toca `.py`, §2) y RM2 coherente (24,8 s por mutante).
  - [x] RM5: N/A con motivo, no hay equivalentes declarados. RM6: no se quitó ninguna guarda.
  - [x] Campaña manual: N/A con motivo, la automática generó 66 mutantes.
  - [x] Cero supervivientes; «Evidencias» con los cuatro números.
- **C4 ter:** N/A con motivo: no existe `harness/rutas_sensibles.json`. Las rutas de escritura se revisaron igualmente
  (sin endpoint, sin App Setting y sin `DELETE`).
- **C5:**
  - [ ] T18-T21 abiertas: esta revisión, T19-T20 MANUAL tras el despliegue y T21 el cierre. Con el criterio aceptado
    por el humano desde F-010, **bloquean el `done`, no el APROBADO**.
  - [x] Un commit `F-018 Tn:` por tarea; el delta, en español y con su pie.
  - [x] Árbol limpio y un solo worktree.
  - [x] `features.json` al día (H2).
- **Documentación y contratos** (R28, bloque `docs`): **[ ]**, por los cambios 1-3 de abajo.

**Cobertura requisito → test** (detalle en `review_F-018_logica.md` y `review_F-018_C4red.md`):

- R1-R9, R11-R18, R20-R24 y R26: tests `test_f018_rN_*` en los cinco ficheros `tests/test_f018_*.py`.
- R10: aserciones `# (R10)` en `test_f018_r24_commit_vinculada_r15` y en un test `r15`.
- R19: las suites del clásico y del directo sin tocar, más el dorado `f009_caracterizacion`.
- R7: además, el cruce contra `dev` del §4.
- R25 se cubre en C4 bis; R27 es MANUAL (`verificacion_manual.md`); R28 son los documentos.

## Cambios requeridos

Es la misma clase de defecto que el cambio 4, en el contrato hermano: la proforma de mes casa por la misma opción C,
así que su cota tiene las mismas dos condiciones. El contraejemplo de 1.000 uds frente a 36 da 0,13. La cabecera de
`contrato_proformas.md` (l. 17-19) ya lo dice bien; estos tres sitios no:

1. **`specs/F-007-registrar-proforma/contrato_proformas.md` l. 217-218 (§3).** Dice «hasta un céntimo por línea así
   (más si el propio `ctrpro` no cumple `pre` = `tot`/`can`)». Añadir «o si `cantidad` > `ctrpro.can`».
2. **El mismo fichero, l. 430 (§8).** Dice «hasta un céntimo por línea frente a `importe_mes` (§3)», sin condiciones.
   Añadir «con `cantidad` ≤ `ctrpro.can` y `pre` = `tot`/`can`».
3. **`azure-apps/sigrid_api.md` l. 1431-1432 (§8.10).** Dice «como mucho 1 céntimo por línea frente a antes con
   `cantidad` ≤ `ctrpro.can`». Añadir «y un `ctrpro` con `pre` = `tot`/`can`».

Para la pasada 3 basta con una revisión incremental de esas líneas más `init.sh`: no hay código ni campaña que repetir.

## Automejora (propuesta, no aplicada)

- **Para `reviewer.md` y `arnes-base`:** quien corrige una cota numérica de un contrato busca la misma frase en
  **todos** los contratos y en `azure-apps` (`grep` del término, aquí «céntimo»). Los cambios 3 y 4 se arreglaron
  donde se señalaron, pero no en sus hermanos.
- **Para `arnes-base`:** los informes troceados deberían anotar la **hora** de cada medida en el árbol principal. Lo que
  dejó fechar la incidencia del §4 fueron los mtimes del scratchpad.
