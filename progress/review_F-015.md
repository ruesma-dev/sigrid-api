<!-- progress/review_F-015.md -->
Revisión incremental desde `5da4e85` (pasada 2) hasta HEAD `87abd53`. Veredicto consolidado de F-015. Reviewer, 2026-10-24.

# Review F-015 · pasada 2 y veredicto consolidado

## Veredicto: **APPROVED**

Los 11 hallazgos H de la pasada 1 están cerrados en el diff, igual que las observaciones atendidas (retención O1-O4,
cabecera O1). El código nuevo (`valpor` NULL ⇒ `retencion_no_soportada`) es correcto y tiene su fase RED real. Mis
5 mutantes manuales mueren todos. `init.sh` en verde. Las MANUALES T19-T21 siguen abiertas y no deciden el
veredicto (criterio de F-010/F-011/F-012). Nada contra Sigrid. No he editado código ni specs.

**Rigor:** `critico`, declarado en `harness/features.json`. Exige RED, cobertura ≥ 80 % de lo cambiado, mutación
con cero supervivientes o equivalentes demostrados, RM1-RM6 y «Evidencias».

**Lo que se miró.** El delta `5da4e85..87abd53` entero: 16 commits y 14 ficheros, más `azure-apps` `bc0c597`. Lo
aprobado en la pasada 1 no se ha vuelto a leer: retención y transacción; C3 bis; C4 ter; la campaña de 104/104. El
delta no lo invalida: no cambia ninguna firma pública, no mueve ningún fichero y el código de producción solo cambia
en `albaran_compra_statements.py` (docstring y 2 líneas).

## 1 · Cierre de los hallazgos de la pasada 1 (comprobado en el diff)

| Hallazgo | Cierre | Estado |
|---|---|---|
| C1C2C5 H1 · `current.md` | Ya no aparece F-015 en el título «F-008 espera» ni en su viñeta. «Lo siguiente» y el prompt para retomar (`current.md:192-210`) dicen `in_progress`, que va la pasada 2 y luego aviso, despliegue y T19-T21 con quién lanza cada paso | [x] |
| C1C2C5 H2 · `impl:18` | «se retira `proveedor_sin_albaran_previo`» | [x] |
| C1C2C5 H3 · `impl:47` | Commits reales: T2 `7f4c488` primero, T15 sin commit propio (marcada en `c0e40ef`) y T18 en dos commits | [x] |
| C3 H1 = cabecera H3 · docstring | `albaran_compra_statements.py:13-22`: v8.3, solo `dcapro` se clona (`_TABLAS_CLONADAS`); `CON_/DCA_/DCAREC_COLUMNAS`; L16, L17, E6b, E12_DCAREC | [x] |
| C3 H2 = cabecera H2 · contrato §4.1/§4.2 | `contrato_albaranes.md:405-410` pone el orden real (L5 antes que L17). §4.2 (`:423-424`) saca la identidad de la cascada. La nota de la v8.3 (`:49-53`) lo recoge sin pedir acuse | [x] |
| C3 H3 · `azure-apps` §8.6 | `bc0c597`: (a) `ivadif` sale del contrato aunque sea 0, del albarán anterior sin contrato y nunca del `prv`; (b) `cabecera_sin_dato` solo salta por el pago, o por el banco con CC/CT/TR; sin aviso en las demás. Más `valpor` vacío | [x] |
| C4red H1 · comandos T19-T21 | `verificacion_manual.md` V0-V6, enlazado desde design §Verificación manual, `tasks.md` T19-T21 y `current.md:38-40`. Detalle en la §3 | [x] |
| cabecera H1 · R25 con contrato y sin respaldo | `test_f015_statements.py:345` hace (a): todo sale del contrato y `sin_fuente` queda vacío. `:358` hace (b): cascada vaciada ⇒ `prv` y `auxpag`, `dircon1` sin fuente, `ivadif` 0 con fuente, identidad del contrato. El control P2.2 de `red_F-015.md` da 4 failed con el mutante | [x] |
| mutación H1 · M10 | `test_f015_r15_valpor_por_su_repr_y_no_por_su_binario` (`:717`, 0,015/0,03 y los dos signos). P2.1 da 3 failed con M10 aplicado y 3 passed sin él | [x] |
| retención O1 · R12 solo sin vincular | `test_f015_use_case.py:422`: commit, RET5, −8,03 → −0,40, `tot` −9,32, sin E9-E11 en la secuencia | [x] |
| retención O2 · `valpor` NULL | `dfc72b8` (ver la §2) | [x] |
| retención O3 · L11 con 8 columnas | `test_f009_use_case.py:713-714` | [x] |
| retención O4 · aviso de R26 | `test_f009_equivalencia.py:224`: `retencion_del_contrato` una vez. El parámetro `avisos` es opcional y no debilita los demás casos | [x] |
| cabecera O1 · `auxefp` | design §Flujo paso 2 (`design.md:138-140`) | [x] |

## 2 · Código nuevo: `valpor` NULL (`dfc72b8`, `albaran_compra_statements.py:425-426`)

- **Corrección.** La guarda está en `resolver_retencion`. Así corre después de la idempotencia y antes de las líneas,
  en dry-run y en commit, como R14 (lo fijan los dos `[False|True-valpor_null]`). Un 0 % sigue admitido: `is None`
  y no `not`. El mapeo a 400 es el de `RetencionNoSoportada`, sin código nuevo. R14 (`requirements.md:69`) lo nombra
  desde `87abd53`, decisión del líder dentro de D8 («`ctrrec` no soportado ⇒ error»). El contrato §3.3 y
  `azure-apps` lo recogen con el mismo código y el mismo mapeo, así que albaranes no tiene que hacer nada.
- **RED** (`red_F-015.md` §P2.4): la salida real, con el código de `df16827`. Fallan 3: `DID NOT RAISE` y
  `InvalidOperation` (el 500 de O2). Con el cambio, 22 passed. Es evidencia, no una frase.
- **Mutación.** `progress/mutacion_F-015_pasada2.md`: 1 generado, 1 muerto, 98,2 s. Recálculo puro
  (`alcance_de_feature(base='5da4e85')` + `generar_mutantes`): **13 líneas y 1 mutante** (`:425 is None -> is not
  None`), como el informe. **Campaña no reejecutada: 98,2 s según el informe** (> 60 s). RM1: SHA `b67de1f`, y
  `git diff b67de1f..HEAD` no toca producción. RM2: base 89,3 s, total 98,2 = 1 × 98,2. Sin «⚠ CAMPAÑA NO VÁLIDA».
- **Mis mutantes manuales.** Worktree aparte `../sigrid-api-mut2-F015` en `87abd53`, con `test_f015_*`,
  `test_f009_equivalencia` y `test_f009_use_case` (350 tests; base: 180 de los tres primeros en verde). El fichero
  se revierte tras cada mutante (comprobado igual al original), el worktree está borrado (`git worktree list`: solo
  el principal) y el árbol queda limpio.

  | Mutante | Resultado |
  |---|---|
  | MA · quitar la guarda | MUERTO, 3 failed (los `valpor_null`) |
  | MB · `is None` → `not fila["valpor"]` | MUERTO, 1 failed (`r14_valpor_0_es_soportado_solo_none_no`) |
  | MC · `raise RetencionNoSoportada` → `raise ValueError` | MUERTO, 3 failed |
  | MD · el texto «(sin porcentaje)» quitado | MUERTO, 3 failed |
  | ME · `return fila` → `return None` tras la guarda | MUERTO, 18 failed |

  Reproduje al pie de la letra dos filas del informe manual del implementer, «quitar la comprobación» (= MA) y
  `not valpor` (= MB), con el mismo resultado. RM3: ningún mutante equivalente sale muerto. RM5: no se declara ningún
  equivalente. RM6: no se quitó código defensivo, se añadió.
- **F-009 y el dorado.** El diff no toca `test_f009_caracterizacion.py`, el dorado ni los ficheros de F-009 que no
  deben cambiar (`git diff --stat dev...HEAD`). Los cambios de los tests de F-009 los refuerzan: 8 columnas y el
  aviso. La suite entera está en verde.

## 3 · `verificacion_manual.md`

- [x] **Literales.** V0 trae el setup y cuatro ayudas. V1-V4 llevan su lectura `sql/read` de selección,
  parametrizada con `?`, su cuerpo `commit:$false` y lo que se mira. V5 da la secuencia exacta: medición, `commit:true`,
  repetición y lecturas. Las lecturas de V3 y V4 coinciden con L5 y L17 del código (`AC__/%`, `cla 0`, `PROF%` y
  `fecbaj 0`).
- [x] **Sin secretos.** La clave se lee con `az` en la consola y no se escribe. El host y el grupo de recursos ya están
  en `azure-apps/sigrid_api.md:226-229`. No hay IP, ID de suscripción ni contraseña: hice un barrido del diff de la
  pasada 2 (IP, GUID, `code=`, `print(`) y dio 0.
- [x] **Quién lanza cada paso** (`:6-9`, cabecera de V5 y V6): V0-V4 el líder, con autorización; el despliegue, V5 y
  V6 el humano.
- [x] **Autorización expresa en V5 y V6** (`:101`, `:134`), igual en `tasks.md` T20 y T21.
- [x] **Sin `DELETE`.** La única mención es «nunca `DELETE`» (`:124`): la anulación es desde la UI.
- [x] **Filtro de la limpieza** (V6 = design §Limpieza, `design.md:176-189`): `d.synckey LIKE ?` con `"ALB-%"` más
  `c.ide IN (…)`, la lista de albaranes, «no por `empide`». El `UPDATE` va por `ide`, `synckey` y `estfac`, con
  `max_affected_rows` = N.

## 4 · `CHECKPOINTS.md` completo (consolidado)

| Bloque | Marca | Base |
|---|---|---|
| C1 · `init.sh` exit 0 y ficheros del arnés | [x] | Esta pasada: «ENTORNO LISTO», **2881 passed, 1 skipped**, 116 s. Tamaños: requirements 134/150, design 248/250, impl 220/220 |
| C2 · una `in_progress`, rama correcta, `current.md`, `history` | [x] | F-015 es la única. Rama `feature/F-015-…`. `current.md` al día (H1 cerrado; ver la O1). `history.md`: N/A, F-015 no está `done` |
| C3 · hexagonal, primera línea, sin print/TODO/secretos | [x] | Delta: docstring, una guarda y tests. Sin imports nuevos. `verificacion_manual.md` lleva su ruta en la línea 1. Barrido limpio |
| C3 · reglas de Sigrid (base, `con`, recálculo, `conest`, `?`) | [x] | Pasada 1 (`review_F-015_C3C4ter.md`). El delta no escribe SQL de producción y las lecturas del anexo van con `?` |
| C3 bis · documentos de fuera | N/A | El delta no añade nada a `docs/referencia/`. `verificacion_manual.md` es de spec, no viene de fuera |
| C4 · requisito → test; tests sin red; MANUAL con comando | [x] | La tabla de abajo y la pasada 1. Los dobles no tocan red ni BBDD. T19-T21 con comandos literales (C4red H1 cerrado) |
| C4 bis · `rigor` declarado | [x] | `critico` |
| C4 bis · fase RED | [x] | La pasada 1 más P2.1 y P2.4 de esta, con salida real. P2.2 es un control, declarado como tal |
| C4 bis · cobertura | [x] | `PUERTA COBERTURA` [OK] 100,0 % de 239/239 |
| C4 bis · mutación, muertos comprobados, tiempo | [x] | 104/104 de la pasada 1 (`review_F-015_mutacion.md`, M10 ya cerrado). Pasada 2: recalculada y con 5 manuales míos |
| C4 bis · sin «CAMPAÑA NO VÁLIDA» y RM1, RM2, RM5, RM6 | [x] | Ver la §2. RM5: ningún equivalente declarado en esta pasada (el de la ronda 1 lo aceptó la pasada 1). RM6: nada quitado |
| C4 bis · campaña de 0 sustituida por una manual | N/A | No dio 0, dio 1. La tabla manual es un complemento y es reproducible: 2 filas reproducidas |
| C4 bis · supervivientes con análisis y «Evidencias» | [x] | Sin supervivientes abiertos: el `not valpor` lo mata un test nuevo. «Evidencias» trae los cuatro números al día |
| C4 ter · rutas sensibles | N/A | No existe `harness/rutas_sensibles.json`, solo el ejemplo |
| C5 · `tasks.md` y commits Tn | [x] | T1-T18 y T22 `[x]`. T19-T21 MANUALES abiertas, que no deciden (criterio de F-010/F-011/F-012). Commits aceptados en la pasada 1 (H3 cerrado) |
| C5 · sin temporales; `features.json` | [x] | `git status` limpio y worktree borrado. `in_progress`, que es el estado real |

## 5 · Cobertura: requisito → test (lo que toca el delta; R1-R30 completo en los informes de la pasada 1)

| R | Tests |
|---|---|
| R3-R5, R25 (con contrato y sin respaldo) | `test_f015_r25_centinela_con_contrato_sin_respaldo_todo_del_contrato`, `test_f015_r25_contrato_sin_cascada_y_sin_respaldo_pasa_al_proveedor` |
| R12, R13 (devolución solo sin vincular) | `test_f015_r12_devolucion_sin_vincular_con_retencion` |
| R14 (`valpor` NULL; 0 % admitido) | `test_f015_r14_ctrrec_no_soportado[valpor_null]`, `test_f015_r14_retencion_no_soportada_400_antes_de_las_lineas[*-valpor_null]`, `test_f015_r14_valpor_0_es_soportado_solo_none_no` |
| R15 (`repr` y no binario) | `test_f015_r15_valpor_por_su_repr_y_no_por_su_binario` (3) |
| R26 (aviso) | `test_f015_r26_con_ctrrec_solo_cambian_el_neto_y_la_dcarec` |
| F-009 R30 (L11 de 8) | `test_f009_r30_*` con sus parámetros `otro_proveedor` y `otra_obra` |

## Observaciones (no bloquean)

- **O1 · Restos de la decisión sobre R14, ya tomada en `87abd53`**, que el líder quita al cerrar: `current.md:36`
  («decidir si R14 … lo nombra») e `impl_F-015.md` (desviación (1) y «Lo que falta»). `impl` está en 220/220.
- **O2 · Cambio de spec después de implementar.** R14 y el §3.3 del contrato se ampliaron en la pasada 2. Tienen el
  mismo código y el mismo mapeo, así que no hace falta acuse. Aun así, el humano debería verlo en el resumen de
  cierre (PARADA 2), y el aviso a albaranes previo al despliegue debería mencionarlo.
- **O3 · V6 exige `UPDATE` en `ALLOWED_WRITE_PREFIXES`** (`verificacion_manual.md:136`): es un ajuste de App
  Settings en producción. Lo decide el humano junto con la autorización de V6, y conviene revertirlo después.

## Automejora (propuesta, no aplicada)

- **`.claude/agents/reviewer.md`, RM4.** Cuando la campaña automática genera **≤ 2 mutantes** sobre líneas nuevas,
  pedir 3-5 mutantes manuales sobre esas líneas en un worktree aparte. El `is None → not` de esta pasada solo lo
  encontró la mano, y en el árbol de trabajo nunca se toca. Vale para cualquier proyecto: candidata a `arnes-base`.

## Cambios requeridos

Ninguno.
