<!-- progress/review_F-015_mutacion.md -->
Revisión completa (pasada 1) · bloque **mutación de C4 bis** · HEAD `e42e0ad`

# F-015 · Revisión de la campaña de mutación y mutantes manuales

**Veredicto: CHANGES_REQUESTED** (un superviviente real en rigor `critico`, H1).

- **Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura y mutación con cero
  supervivientes, y RM5 con un equivalente reproducido.
- **Dónde se ha trabajado:** en un worktree aparte (`../sigrid-api-mut-F015` sobre `e42e0ad`), por orden del líder,
  con el `.venv` del repositorio principal. Ya está eliminado (`git worktree remove`). El árbol principal no se ha tocado:
  `git status` solo enseña los `review_F-015_*.md` sin seguimiento de los otros reviewers. No se han ejecutado ni
  `init.sh` ni la suite completa, y nada ha ido contra Sigrid.

## C4 bis · campaña automática (`progress/mutacion_F-015.md`)

| Comprobación | Estado | Evidencia |
|---|---|---|
| Alcance y número de mutantes recalculados | [x] | `alcance_de_feature` + `generar_mutantes` sobre HEAD: 491 + 214 + 9 + 9 = **723** líneas y **58 + 46 + 0 + 0 = 104** mutantes. Coincide con el informe |
| Ficheros mutados = lo que cambió | [x] | Los 4 ficheros de producción del diff `dev...HEAD`. `tests/`, `progress/` y `specs/` quedan fuera por diseño |
| Cero mutantes en `models` y `function_app` | [x] | Prueba de control: en esas líneas solo hay literales de texto y docstrings. Con el fichero entero sí salen mutantes (64 y 43), así que el generador funciona: el cero es una exclusión legítima |
| RM1 · SHA medido | [x] | Se midió `97c4e8b` y HEAD es `e42e0ad`. `git diff --stat 97c4e8b..HEAD` solo toca `progress/` y `tasks.md`: ningún fichero del alcance. No hay que repetir |
| RM2 · coherencia del tiempo | [x] | Ver nota 1 |
| Cabecera «⚠ CAMPAÑA NO VÁLIDA» o «Sin veredicto» ≠ 0 | [x] | No hay cabecera. Sin veredicto = 0. Línea base corrida (156,3 s). `--workers 1` |
| Reejecutar la campaña | N/A | Campaña no reejecutada: 1602,5 s (≈ 27 min) según el informe, por encima del umbral de 60 s. Me quedo en recálculo puro + RM1–RM6 + mutantes manuales |
| RM3 · ningún equivalente sale muerto | [x] | El informe no declara ningún equivalente muerto. En mi tanda, el mutante de control equivalente (M17) **sobrevive**, como debe |
| RM5 · reproducir un equivalente (critico) | [x] | El único declarado fue el de la ronda 1, `ide_dcarec + n` → `- n`. Reproducido sobre `40f1425`: **748 passed** en los tests de F-009 y F-015. Es equivalente, como se dijo |
| RM6 · código defensivo | [x] | No se quitó ninguna guarda: se **añadió** una (`numerar` rechaza más de una `dcarec`). El invariante también se cumple en el origen del dato: `resolver_retencion` rechaza más de un `ctrrec` (R14) y `_construir` añade como mucho una `dcarec`. Fase RED en `red_F-015.md` §T18 |
| Cero supervivientes (critico) | [ ] | **H1**: el generador no lo ve (no muta llamadas), pero el mutante manual M10 sobrevive |

**Nota 1 (RM2).** La media es 15,4 s y la línea base 156,3 s: el cociente es 0,099, justo por debajo de la décima parte
del literal de RM2. **No es un salto inventado:** el tiempo total cuadra (104 × 15,4 = 1601,6 ≈ 1602,5 s), y con `-x` un
mutante muerto se para en el primer test de F-009. Ese test está en la **posición 1371 de 2872** en el orden de
recogida. Lo medido es 6 s de recogida y 12,8 s para los 1370 tests anteriores. Encaja con el caso legítimo de F-038.

## Mutantes manuales (21: 20 de búsqueda y 1 de control)

Cada mutante se aplicó en el worktree. Se ejecutaron solo los tests de F-015 y F-009: `test_f015_statements`,
`test_f015_use_case` y `test_f009_{statements,use_case,equivalencia,models,route,mutacion,caracterizacion}` (749 tests,
unos 12 s por mutante). Después se revirtió con `git checkout -- <fichero>`, y el script comprueba que `git status` queda
limpio tras cada uno. El script está en el scratchpad de la sesión (`mutantes_f015.py`). Abreviaturas: S =
`albaran_compra_statements.py`, U = `create_albaran_compra_use_case.py`.

| # | Fichero:línea | Cambio (original → mutado) | Resultado (fallos) · test que lo mata |
|---|---|---|---|
| M01 | S:696 | orden `(contrato, respaldo, proveedor)` → `(respaldo, contrato, proveedor)` | MUERTO (3) · `test_f015_r3_el_contrato_manda_sobre_el_respaldo` |
| M02 | S:696 | → `(contrato, proveedor, respaldo)` | MUERTO (11) · `test_f015_r3_una_columna_vacia_en_el_contrato_pasa_al_respaldo[*]` |
| M03 | S:671 | `valor.strip() != ""` → `valor != ""` | MUERTO (1) · `test_f015_r3_un_texto_de_espacios_cuenta_como_vacio` |
| M04 | S:672 | `return valor != 0` → `return True` | MUERTO (31) · `test_f015_r3_vacia_en_contrato_y_respaldo_pasa_al_proveedor[*]` |
| M05 | S:788 | `ivadif`: `(contrato if … else respaldo)` → `(respaldo if … else contrato)` | MUERTO (2) · `test_f015_r3_ivadif_del_contrato_aunque_sea_0` |
| M06 | S:194-195 | L5 por `entide`: `NOT LIKE ?` (PROF%) → `LIKE ?` | MUERTO (2) · `test_f015_r6_sql_l5_respaldo_por_entide_sin_proformas` |
| M07 | S:46 | `CLA_ALBARAN = 0` → `1` | MUERTO (10) · `test_f015_r6_constantes_del_respaldo`, `…_l5_con_serie_clase_y_sin_proformas` |
| M08 | S:45 | `"AC__/%"` → `"AC%"` | MUERTO (10) · `test_f015_r6_constantes_del_respaldo`, `test_f015_r6_sql_l5_*` |
| M09 | S:339 | `rounding=ROUND_HALF_UP` → `"ROUND_HALF_EVEN"` | MUERTO (8) · `test_f015_r15_empate_a_medio_centimo_lejos_del_cero` |
| **M10** | S:443 | `bas * _decimal(ctrrec["valpor"])` → `bas * Decimal(ctrrec["valpor"])` | **SUPERVIVIENTE** (0 de 749) → **H1** |
| M11 | S:827 | `totdoc - cuo` → `totdoc + cuo` | MUERTO (9) · `test_f015_r13_tot_y_totpag_netos_de_la_retencion[*]` |
| M12 | U:995 | `"n_retenciones": len(dcarec)` → `1` | MUERTO (6) · `test_f015_r17_totales_sin_retencion`, `test_f015_r19_la_traza_sin_retencion_dice_0` |
| M13 | U:444 | L17 `len(filas) > 1` → `> 2` | MUERTO (1) · `test_f015_r7_sin_proveedor_unico_por_cif_no_se_da_de_alta[…proveedor_ambiguo]` |
| M14 | U:442 | `proveedor_no_encontrado` → `proveedor_ambiguo` | MUERTO (1) · `test_f015_r7_sin_proveedor_unico_por_cif_no_se_da_de_alta[…no_encontrado]` |
| M15 | S:147 | `{"CC","CT","TR"}` → `{"CC","CT"}` | MUERTO (1) · `test_f015_r5_banco_sin_fuente_con_confirming_o_transferencia_avisa[TR]` |
| M16 | S:147 | `{"CC","CT","TR"}` → `{"CT","TR"}` | MUERTO (3) · `…_avisa[CC]`, `test_f015_r5_el_aviso_tambien_en_el_alta` |
| M17 | U:471 | `and all(… GRUPO_BANCO)` → `and any(…)` · **control** | SOBREVIVE, como se esperaba: es **equivalente**. `de_un_grupo` mete en `sin_fuente` todo el grupo banco o nada, así que `all` ≡ `any` |
| M18 | U:751 | E12 `dcarec`: `len(filas.dcarec)` → `1` | MUERTO (26) · `test_f015_r21_sin_retencion_ni_reserva_ni_insert` |
| M19 | U:751 | E12 `dcarec`: `len(filas.dcarec)` → `0` | MUERTO (5) · `test_f015_r21_con_retencion_e6b_tras_e6_e_insert_tras_los_mov` |
| M20 | U:670 y U:691-694 | el reintento reutiliza el `ide` de `dcarec` del primer intento (caché `_primero`) | MUERTO (1) · `test_f015_r22_el_reintento_recalcula_el_ide_de_la_dcarec` |
| M21 | U:693 | `if cabecera.retencion is not None` → `if True` (E6b siempre) | MUERTO (3) · `test_f015_r21_sin_retencion_ni_reserva_ni_insert`, `test_f009_r26_…` |

Resultado: de 20 mutantes de búsqueda, **19 muertos y 1 superviviente real (M10)**. El control M17 sobrevive, que es
lo que debe pasar con un equivalente: es la contraprueba de RM3 en esta tanda.

## Hallazgos

**H1 · M10 sobrevive: ningún test fija que `valpor` entra en `Decimal` por su `repr` y no por su binario.**
Lo he medido, no razonado. Con M10 aplicado, `calcular_retencion({"cla": 5, "valpor": 0.015}, {"totbas": 1.0, …})` da
`cuo` **0.01** en vez de **0.02**. Con `bas` −3,00 da −0,04 en vez de −0,05, y con `valpor` 0,03 y `bas` 0,50, 0,01 en
vez de 0,02. `ctrrec.valpor` es `Real` en Sigrid (`azure-apps/sigrid_tablas.md`), así que pyodbc lo entrega como `float`.
Y 0,015 y 0,03 son valores reales de producción (`explore_F-015.md` M11): su binario queda justo por debajo de su
decimal. Los tests actuales usan `valpor` 0,05, cuyo binario queda por encima y no da la vuelta, y 0,015 con 1234,56,
que no cae en un empate. Por eso no lo ven. El código está bien. Falta el test.

## Cambios requeridos

1. `tests/test_f015_statements.py`, junto a `test_f015_r15_en_decimal_no_en_binario` (línea 669): añadir un test de R15
   con un `valpor` cuyo binario quede por debajo de su decimal, en empate a medio céntimo y en los dos signos. Por
   ejemplo:
   `calcular_retencion(ctrrec(valpor=0.015), {"totbas": 1.0, "totiva": 0.0, "totdoc": 1.0}) == (Decimal("1.00"), Decimal("0.02"))`
   y su negativo con `totbas` −3,0 → `Decimal("-0.05")`. Hay que dejar en `red_F-015.md` la salida real con M10
   aplicado (falla) y sin él (pasa): es la forma de medir que mata a M10.

## Automejora (propuesta, no aplicada)

- **RM2** (`.claude/agents/reviewer.md`): el umbral literal de «la décima parte de la línea base» marca como sospechosa
  esta campaña, que es legítima (0,099). Propuesta: comparar la media con el tiempo que tarda la suite, con `-x`, en
  llegar al **primer test del módulo mutado** (posición en `pytest --co`), no con la línea base entera. Vale para
  cualquier proyecto: candidata a `arnes-base`.
- **Generador** (ya anotado en `current.md`): M10 muestra otro hueco. Cambiar el nombre de una función o de un
  constructor (`_decimal` → `Decimal`) tampoco se muta.
