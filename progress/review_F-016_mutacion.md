<!-- progress/review_F-016_mutacion.md -->
Revisión completa (pasada 1) · bloque C4 bis, parte de campaña de mutación · HEAD `c08461f`

# F-016 · Review troceada: campaña de mutación

**Veredicto: APROBADO** (este bloque). Sin cambios requeridos; tres observaciones al final.

**Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige campaña con cero
supervivientes sin justificación aceptada por el humano y RM5 sobre los equivalentes.

Fuera de este encargo (otros revisores en paralelo): `bash harness/init.sh`, suite completa,
fase RED, cobertura. No se ha ejecutado `harness.mutacion` (campaña): solo cálculo puro.

## Cobertura del alcance de T14

| Fichero que pide T14 | En el alcance medido | Mutantes |
|---|---|---|
| `application/use_cases/proforma_origen_statements.py` | 337 líneas | 47 |
| `domain/models/proforma_origen_models.py` | 114 líneas | 0 (ver abajo) |
| `application/use_cases/create_proforma_use_case.py` (lo cambiado) | 233 líneas | 50 |
| `domain/models/proforma_models.py` (lo cambiado) | 30 líneas | 14 |
| `function_app.py` (lo cambiado) | 25 líneas | 4 |
| `config/settings.py` (lo cambiado) | 4 líneas | 1 |

Los seis ficheros están; ninguno sobra. Los **0 mutantes de `proforma_origen_models.py`** son
legítimos: el fichero entero está en alcance (114 de 114 líneas, fichero nuevo) y su código son
solo declaraciones de tipos, `frozenset` de cadenas y defectos `None`/`default_factory`, sin
enteros, booleanos, comparaciones ni operadores lógicos que el generador ataque. No hace falta la
prueba de control «ignorando la exclusión»: no hay exclusión, el alcance ya es el fichero entero.

## Recálculo independiente (cálculo puro)

`alcance_de_feature("F-016")` + `generar_mutantes` por fichero, sobre HEAD:
diff `745a43c..feature/F-016-proforma-a-origen` (origen `rama`), **743 líneas, 116 mutantes**.
Coincide con el informe (743 / 116). Los 14 supervivientes del informe existen en la lista
recalculada con el mismo fichero, línea, operador y texto original→mutado (comprobados los 14).

## C4 bis · puntos de campaña

- [x] **Mutación**: `progress/mutacion_F-016.md` generado por la herramienta (`--workers 1`),
      totales verificados por recálculo (arriba).
- [x] **Muertos comprobados**: «Tiempo total» 4937,2 s (82 min) > 60 s → **campaña no reejecutada**
      (además, vedado por el encargo). Vale el recálculo puro más la muestra manual de abajo, que
      incluye 4 mutantes que la campaña dio por muertos (todos muertos de verdad).
- [x] **Coste por mutante**: 4937,2 × 1 ÷ 116 = 42,6 s, muy por encima de 1 s.
- [x] **Sin «⚠ CAMPAÑA NO VÁLIDA»** y «Sin veredicto (base rota)» = 0; línea base medida (129,4 s).
- [x] **RM1**: SHA medido `06ffcb6` ≠ HEAD `c08461f`, pero `git diff 06ffcb6..HEAD` no toca
      **ningún** fichero del alcance (solo docs, specs, progress, `features.json` y los tests de
      T14). El alcance medido es el revisado; no hay que repetir la campaña.
- [x] **RM2**: base 129,4 s, media 42,6 s con 1 worker y 102/116 muertos con `-x` (caso legítimo,
      no salto de orden de magnitud); 116 × 42,6 = 4941,6 ≈ 4937,2 s. Coherente.
- [x] **RM3**: ningún mutante declarado equivalente; nada que pueda «salir muerto» indebidamente.
- [x] **RM5**: N/A justificado: en rigor `critico` aplica a los «equivalentes», y no se declaró
      ninguno (los 14 supervivientes se mataron con tests nuevos).
- [x] **RM6**: `git diff 06ffcb6..HEAD -- application domain config function_app.py` vacío: para
      matar supervivientes **no se tocó código de producción**, solo se añadieron tests. Ninguna
      guarda quitada.
- [x] **Campaña manual**: N/A justificado: la automática dio 116 mutantes, no 0.
- [x] **Cero supervivientes no aceptados (`critico`)**: los 14 tienen análisis medido; 13 muertos
      con los tests de T14 y 1 (n.º 4) muerto por tests previos. Ninguno «aceptado» sin medir.
- [x] **Regla del proyecto (se analiza midiendo / exit 5)**: la tabla de medición del implementer
      da conteos reales (`3544 passed, 1 skipped`, `1 failed, 3148 passed`), no un exit 5. Mis
      ejecuciones (abajo) también traen conteos reales. No había código muerto que quitar.

## Mutantes aplicados a mano (resultado real)

Aplicados en disco con `aplicar_mutante` del arnés sobre el mutante recalculado (no a ojo),
ejecutando `python -m pytest tests/test_f016_*.py tests/test_f007_*.py -q --tb=no
-p no:cacheprovider` con `PYTHONDONTWRITEBYTECODE=1`, y restaurando con `git checkout -- <fichero>`.
Base sin mutar: **668 passed** (13,5 s). Columna «sin T14»: mismo comando con `-k "not t14"`
(deselecciona los 5 tests de T14), para comprobar que el superviviente era real.

| # informe | Fichero:línea · original → mutado | Con todos los tests | Sin T14 |
|---|---|---|---|
| 4 | `create_proforma_use_case.py:565` `(len(dcapro) + 1)` → `+ 2` | **muerto**, 2 failed / 666 passed (`test_f016_r18_insert_de_las_arrastradas_y_relectura_con_todas`, `test_f016_r11_r12_previa_encadenada_lee_y_escribe_la_cadena`) | **muerto**, 2 failed / 661 passed |
| 14 | `proforma_origen_statements.py:256` `if not _vinculo(fila):` → `if _vinculo(fila):` | **muerto**, 1 failed / 667 (`test_f016_t14_continuada_imporiori_…`) | sobrevive, 663 passed |
| 11 | `create_proforma_use_case.py:693` `vinculo > 0` → `> 1` | **muerto**, 1 failed / 667 (`test_f016_t14_ceros_…`) | sobrevive, 663 passed |
| 12 | `proforma_origen_statements.py:89` `frozen=True` → `frozen=False` | **muerto**, 1 failed / 667 (`test_f016_t14_los_documentos_validados_son_inmutables`) | sobrevive, 663 passed |
| 3 | `create_proforma_use_case.py:361` `strict=True` → `strict=False` | **muerto**, 1 failed / 667 (`test_f016_t14_una_lp9_mal_formada_…`) | sobrevive, 663 passed |

Muestra de mutantes que la campaña dio por **muertos** (elegidos al azar, semilla 16, más dos de
frontera en modelos y ruta):

| Mutante (lista recalculada) | Original → mutado | Resultado |
|---|---|---|
| 60 · `proforma_origen_statements.py:129` | `filas_lp7[0]` → `filas_lp7[1]` | muerto, 34 failed / 634 passed |
| 74 · `proforma_origen_statements.py:247` | `"canoriant": 0` → `"canoriant": 1` | muerto, 3 failed / 665 passed |
| 102 · `proforma_models.py:205` | `max_length=24` → `max_length=25` | muerto, 1 failed (`test_f016_r3_proforma_anterior_de_1_a_24`) |
| 115 · `function_app.py:375` | `… == "origen" and not settings…` → `… == "origen" or not settings…` | muerto, 12 failed / 656 passed |

Los tests de T14 son de comportamiento (comparan valores de la respuesta, `FrozenInstanceError`,
`ValueError` ante una LP9 descuadrada, `max_rows` pedido), no espejos de la línea mutada.

Árbol tras las pruebas: `git diff` vacío; solo quedan sin seguimiento `.claude/worktrees/` y los
informes de los otros revisores. Comprobado además que los `.pyc` de los cuatro ficheros tocados
corresponden al fuente restaurado (mtime y tamaño de la cabecera = los del fuente actual).

## Observaciones (no bloquean)

1. **Superviviente falso n.º 4: anomalía de la herramienta sin causa conocida.** Lo matan dos
   tests que ya existían en el SHA medido `06ffcb6` (`tests/test_f016_transaccion.py` no cambia
   desde entonces; en `tests/test_f016_use_case.py` T14 solo añade líneas), y lo reproduzco muerto
   con y sin los tests de T14. Que la campaña en serie lo diera por vivo significa que **su veredicto
   no siempre corresponde al código en disco**. Aquí el error va en la dirección inocua (un vivo de
   más, que se midió a mano), pero el mismo fallo en la dirección contraria daría un **muerto que
   nadie mató** y sería invisible. Hipótesis sin verificar: `_purgar_bytecode`
   (`harness/mutacion.py:430-453`) traga el `OSError` de `unlink` en Windows, y otro proceso en el
   mismo árbol (IDE u otra suite) pudo dejar o retener un `.pyc` del original con igual tamaño.
   **Propuesta al humano** (no aplicada): investigar en `arnes-base`, p. ej. que la campaña
   reverifique en serie cada superviviente antes de escribirlo, o que aborte si no puede purgar el
   `.pyc`. Mitigación para F-016: la muestra de 4 muertos de arriba salió muerta de verdad.
2. **El informe conserva «Supervivientes 14»** porque la campaña no se relanzó tras los tests de
   T14; el «0 no aceptados» descansa en la medición manual del implementer (sección final del
   informe), que reproduzco en 5 de los 14. Admisible según el protocolo (ningún análisis en
   `PENDIENTE`); se deja constancia de que la verificación de T14 («`harness.mutacion` sin
   supervivientes no aceptados») se cumple por análisis medido, no por una segunda campaña.
3. **Interferencia posible con los revisores en paralelo**: por encargo, los mutantes se aplicaron
   en el árbol principal, unos 12-15 s cada uno, entre las ~20:03 y las ~20:11 (hora local del
   2026-10-28). Una suite o un `init.sh` lanzado por otro revisor en esa franja pudo ver un mutante
   y salir en rojo sin culpa del implementer: si alguno informa de un rojo en esa franja, que
   repita. Para próximas revisiones troceadas, aplicar mutantes sobre una copia en el scratchpad
   (RM4) en vez de en el árbol compartido.
