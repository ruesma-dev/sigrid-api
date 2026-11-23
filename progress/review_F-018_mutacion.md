<!-- progress/review_F-018_mutacion.md -->
Revisión completa (pasada 1) del bloque C4 bis · mutación y RM, sobre HEAD `7ce2240` (campaña medida en `e649e38`)

# F-018 · Review troceada: mutación (C4 bis) y exigencias de rigor `critico`

**Veredicto del bloque: APROBADO**

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura, campaña
completa (`max_mutantes: null`), **cero supervivientes** y verificaciones MANUAL con comando exacto.
Este encargo cubre la mutación y las reglas RM1–RM6; fase RED, cobertura, C4 (MANUAL) y `init.sh` son de
otros encargos de la revisión troceada.

## Método (todo fuera del árbol principal)

- Worktree desechable en `e649e38` dentro del scratchpad; quitado con `git worktree remove` al acabar.
- No se ejecutó `harness.mutacion` ni se aplicó ningún mutante en el árbol principal.
- Los mutantes se aplicaron con `harness.mutacion.aplicar_mutante` sobre los `Mutante` que devuelve
  `generar_mutantes`: es exactamente el texto original → mutado de la campaña, no una reescritura a mano.
- Cada ejecución lanzó los cuatro ficheros `tests/test_f018_{statements,use_case,proforma,models}.py`
  (200 tests) con `__pycache__` purgado y `-p no:cacheprovider`. Línea base sin mutar: **exit 0, 200 passed**.

## ¿El informe es la campaña 3 y corresponde a `e649e38`?

| Comprobación | Resultado |
|---|---|
| Historia de `progress/mutacion_F-018.md` | Entra por primera vez en `7ce2240`: no hay versión anterior que reutilizar |
| SHA de HEAD medido | `e649e384dd06941e8aae500d57445894ab06ca59` (completo) |
| Cronología | Commit `e649e38` 12:35:18; informe escrito 13:04:35 (mtime) − 1.637,7 s ⇒ arranque ≈ 12:37. Posterior a `24e785a` (12:34:51) |
| No puede ser la campaña 1 | La 1 se cortó en el mutante 48; este informe evalúa 66 |
| No puede ser la campaña 2 | La 2 dio 2 supervivientes y base 365 s; este da 0 y base 136,7 s |
| `e649e38..7ce2240` | Solo `progress/impl_F-018.md`, `progress/mutacion_F-018.md` y `tasks.md` (T14 a `[x]`). **Cero líneas de producción ni de tests**: la campaña vale para HEAD |
| `536ce9c..e649e38` en producción | Diff vacío en `application/ domain/ function_app.py infrastructure/ config/ interface_adapters/`: los arreglos de T14 son solo tests |

## Checkpoints C4 bis (mutación y RM)

- [x] `rigor` declarado: `critico`.
- [x] **Totales verificados de forma independiente** (cálculo puro con `harness.alcance.alcance_de_feature`
      y `generar_mutantes`): alcance `6aca027..rama`, **245 líneas** (104 / 84 / 48 / 9) y **66 mutantes**
      (29 / 24 / 13 / 0 en `function_app.py`, cuyas 9 líneas son docstring). Coinciden fila a fila.
- [x] **Muertos comprobados.** «Tiempo total» 1.637,7 s > 60 s: **campaña no reejecutada (27 min según el
      informe)**. En su lugar, RM4 sobre 12 mutantes (tabla de abajo): los 12 mueren con exit 1.
- [x] **Coste por mutante:** 1.637,7 × 1 ÷ 66 = **24,8 s** ≫ 1 s.
- [x] Sin cabecera «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; la línea base **corrió** (136,7 s).
- [x] **RM1:** SHA completo y es el alcance que reviso (ver tabla anterior).
- [x] **RM2:** W = 1; media 24,8 s = 0,18 × base (no hay salto de orden de magnitud); 66 × 24,8 = 1.636,8 s
      frente a 1.637,7 s (redondeo de la media). Media < base es lo esperable con `-x` y 66/66 muertos.
- [x] **RM3:** repasados los 66 textos original → mutado; ninguno es equivalente (todos cambian un valor,
      un mensaje, una rama o lanzan excepción observable). Ningún equivalente sale muerto.
- [x] **RM5:** N/A justificado: no hay ningún superviviente declarado «equivalente». El único «superviviente»
      de la campaña 1 que el implementer descartó como falso (`importe_con_dto` `*` → `//`) lo reproduje: muere.
- [x] **RM6:** `4ea35bb` y `24e785a` solo tocan `tests/`; producción idéntica desde `536ce9c`. No se quitó
      ninguna guarda para matar mutantes.
- [x] Campaña manual: N/A justificado, la automática generó 66 mutantes (no hubo sustitución manual).
- [x] Supervivientes con análisis / cero en `critico`: 0 supervivientes, nada que justificar ni que aceptar.
- [x] «Evidencias» con los cuatro números. Workers: «Workers 1» en el informe de mutación y `--workers 1`,
      «todas en serie» en la cabecera de T14 (`impl_F-018.md` l. 169-171). Ver observación 1.
- [x] Ningún N/A sin motivo escrito en este bloque.

## Las funciones nuevas tienen mutantes

| Función | Mutantes | Función | Mutantes |
|---|---|---|---|
| `texto_de_dto` | 1 | `_con_dto_efectivo` | 7 |
| `porcentaje_de_dto` | 6 | `_avisos_de_dto` | 8 |
| `importe_con_dto` | 5 | `construir_dcapro_vinculada` (con `dto`) | 5 |
| `bruto_de_linea` | 1 | `construir_dcapro_sin_vincular` (con `dto`) | 1 |
| `dto_del_contrato` | 6 | `construir_dca(impbru=)` | 1 |
| `dto_coincide` | 2 | `_CIEN` (módulo) | 1 |

Resto: `_avisos_de_contrato` 3, `_construir` 3, `_respuesta` 1, `run` 2; modelos: `LineaAlbaranIn.dto` 3,
`_dto_con_dos_decimales` 4, `con_dto` 4, `_sin_claves_de_dto_vacias` 2. `LineaResultado` (6 líneas,
declaraciones `= None`) y `function_app.py` (docstring) no generan mutantes: legítimo.

## Los tests de `4ea35bb` y `24e785a` matan su mutante (medido, con control)

«Antes»: mismo mutante con los tests del commit anterior al arreglo. Ningún exit 5 en ninguna ejecución.

| Mutante (texto exacto del generador) | Antes | Con `e649e38` | Tests que caen |
|---|---|---|---|
| A · statements:439 `porcentaje <= 0` → `<= 1` | tests de `536ce9c`: exit 0, 195 passed | exit 1, **2 failed** | `test_f018_d9_dto_del_contrato[ctrpro2]`, `[ctrpro3]` (1 % y 0,5 %) |
| B · use_case:1282 `get("pre") or 0` → `or 1` | `536ce9c`: exit 0, 195 passed | exit 1, **1 failed** | `test_f018_r15_ctrpro_con_pre_0_y_otro_precio_no_copia_el_dto` |
| C · use_case:1699 `get("tar") or 0` → `or 1` | `4ea35bb`: exit 0, 198 passed | exit 1, **2 failed** | `test_f018_r12_ctrpro_sin_tar_avisa_del_bruto_pedido[tar_0]`, `[tar_null]` |
| D · use_case:1718 `porcentaje_de_dto(texto) or 0` → `or 1` | `4ea35bb`: exit 0, 198 passed | exit 1, **1 failed** | `test_f018_r13_ctrpro_sin_dto_cuenta_como_0` (ahora `"(0%)"`) |

Cuadra con lo que declara `impl_F-018.md` (2 y 1; 2 y 1). Los cuatro huecos eran reales y el test nuevo es
el que los cierra.

## RM4 · Otros mutantes reproducidos (muestra elegida por el reviewer)

| Mutante | Resultado |
|---|---|
| statements:999 `get("pre") or 0` → `or 1` (gemelo de B en `construir_dcapro_vinculada`) | exit 1, 1 failed |
| statements:425 `cantidad * tar` → `cantidad // tar` (el falso superviviente de la campaña 1) | exit 1, 35 failed en los 4 ficheros |
| use_case:332 `sum(1 …)` → `sum(2 …)` (traza R18) | exit 1, 2 failed |
| use_case:1031 `importes[-1][0]` → `importes[-2][0]` | exit 1, 16 failed |
| models:252 `strict=True` → `strict=False` | exit 1, 4 failed |
| models:268 `exponent < -2` → `< -3` | exit 1, 3 failed |
| models:268 `exponent < -2` → `<= -2` | exit 1, 6 failed |
| statements:922 `impbru is None` → `is not None` | exit 1, 14 failed |

Sobre la pista del `exit 5` (`ResultadoSuite.verde`, `harness/mutacion.py` l. 484-491, sigue contando
`PYTEST_SIN_TESTS` como verde): solo puede **inventar supervivientes**, nunca muertos; con 0 supervivientes
no hay nada que pueda haber ocultado aquí.

## Fuera de este bloque (para el veredicto consolidado)

- Fase RED, cobertura e `init.sh`: no ejecutados por este encargo (otros encargos). En el worktree, los
  200 tests de F-018 en `e649e38` pasan.
- Rigor `critico`, verificaciones MANUAL: `verificacion_manual.md` (V0–V5) y su lista en `current.md`
  existen; su resultado real llega en T19/T20, tras el despliegue. Lo juzga el encargo de C4.
- **Incidencia de convivencia:** el reflog del árbol principal registra `checkout` a `dev` a las 13:23:30 y
  vuelta a la rama a las 13:23:44, hecho por otro agente. Todo test lanzado en el árbol principal en esa
  ventana midió `dev`. No afecta a este informe (todo se midió en worktree); avisar a los demás encargos.

## Cambios requeridos

Ninguno.

## Observaciones no bloqueantes

1. La tabla «Evidencias» de `impl_F-018.md` (l. 208-219) no repite el nº de workers en su fila de mutación;
   está en la cabecera de T14 y en el informe de mutación. Basta con añadir «, 1 worker (serie)».

## Automejora (propuesta, no aplicada)

- `.claude/agents/reviewer.md`, RM4: cuando un commit añade tests «para matar un superviviente», exigir el
  **control**: el mutante con los tests del commit anterior debe sobrevivir (exit 0, no 5) y con los nuevos
  morir. Sin el «antes», un test que mata el mutante por otra vía no se distingue del que cierra el hueco.
- `CLAUDE.md` / protocolo de revisión troceada: ningún encargo cambia de rama el árbol principal; quien
  necesite `dev` usa un worktree (la incidencia de 13:23 lo demuestra).
