<!-- progress/review_F-008_mutacion.md -->
Revisión completa (pasada 1), trozo `mutacion`, sobre HEAD `2879ddb` (base `ccfb334`).

# F-008 · Revisión troceada · Mutación (C4 bis + RM del rigor `critico`)

**Veredicto: APPROVED** (del trozo). Sin cambios requeridos; una observación no bloqueante (O1).

- **Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige campaña entera, cero
  supervivientes sin justificación aceptada y RM5 (demostración ejecutable de UN equivalente).
- **Fuera de este trozo:** RED, cobertura, lógica, C1/C2/C3/C5, docs (otros revisores).
- **Cómo se midió:** dos worktrees detached en el scratchpad (`2879ddb` y `eba243e`), nunca el árbol
  principal; mutantes generados y aplicados con `harness.mutacion.generar_mutantes`/`aplicar_mutante`,
  `pytest -q -x -p no:cacheprovider`, `PYTHONDONTWRITEBYTECODE=1`, línea base en verde antes de cada lote.
  Solo cuenta como MUERTO un exit 1; exit 0 = VIVO; otro código = error, no muerte (lección del exit 5).
  `git status` limpio en los worktrees tras cada lote; worktrees borrados al acabar.

## Lo medido

| # | Comprobación | Resultado |
|---|---|---|
| 1 | Recálculo puro en `eba243e` (`parsear_diff`+`filtrar_produccion`+`generar_mutantes`) | **2738 líneas, 568 mutantes**: coincide fichero a fichero con el informe |
| 2 | Muestra de **35 de los 82 «con test nuevo»** (36 posiciones: #1 casa en 2 líneas) sobre `2879ddb`, suite `-k f008` | **36/36 MUERTOS**, cada uno por el test que el informe cita |
| 3 | Los 3 «falsos positivos» (#17 l.461, #18 l.487, #28 l.772; ids de campaña 76/85/182) | MUERTOS en los tres escenarios: `2879ddb -k f008`; `eba243e -k f008` (suite ANTERIOR a T20); y `eba243e` con la **suite entera `.`** como la campaña (12–14 s cada uno) |
| 4 | Los **15 mutantes nuevos** que nacen en las líneas reescritas por T20 (17 posiciones) | **17/17 MUERTOS** |
| 5 | Muestra aleatoria (semilla 20261031) de **50 de los 467 «muertos»** sobre `eba243e` | **50/50 MUERTOS** (una 51.ª posición, `function_app.py:307`, está fuera del alcance: mismo texto en otra ruta) |
| 6 | RM5: fuerza bruta sobre `_fecha_real` (#64–#66) | Reescritura `len(str(valor)) != 8` ≡ rango original: **0 diferencias** en las ~9 M entradas donde podían divergir |

Muestra de (2): #1, 3, 6, 7, 8, 9, 10, 12, 14, 19, 20, 21, 22, 23, 25, 26, 30, 36, 38, 40, 44, 49, 55, 58,
59, 62, 67, 70, 72, 76, 84, 95, 98, 99, 101 (los cinco ficheros del alcance y los siete operadores).

Scripts y salidas (JSON con veredicto, segundos y test que falla), en el scratchpad de la sesión:
`recalculo.py`, `peticiones.py`, `evaluar.py`, `muestra_muertos.py`, `rm5_fecha.py`, `r_*.json`.

## Puntos que se pedía decidir

1. **Los 82 con test nuevo:** confirmado por muestra amplia (43 %). Todos caen y por el test declarado.
2. **Los 3 falsos positivos:** confirmado que son falsos. Caen incluso con la suite **de antes de T20** y
   **entera**, es decir, en las condiciones exactas de la campaña. La campaña los dio por vivos porque
   corría sobre el árbol principal con otra medición concurrente; la causa exacta sigue sin aislar, pero
   el efecto medido es conservador (inventa vivos, no muertos), y la muestra de 50 muertos (5) descarta
   el error en la dirección peligrosa. Coincide con la lección de la memoria del proyecto.
3. **Los 16 de código muerto/equivalente:** era inalcanzable o equivalente de verdad, con dos matices:
   - #27 `cuo=Decimal(0)`: `totales_factura` calcula `totbas = Σ tot` sin mirar `cuo` → equivalente; la
     suma directa que lo sustituye es idéntica. Su mutante nuevo (`Decimal(1)`) cae.
   - #29 `or 0` → `assert`: **RM6 verificado en el origen**: el mismo `_montar` lanza
     `vencimiento_retencion_no_valido` (l. 772–779) si hay garantía y `vence is None`, **antes** de
     llamar a `_filas` (l. 781). Mutante `is None` del `assert` cae.
   - #31: el defecto `.get(…, 0)` se cambia por un error explícito antes del UPDATE: **añade** defensa.
   - #32–#35: `E10_SUMAS_CONTRATO` (`SUM` sin `GROUP BY`), `_EF_IDE` (`ISNULL(MAX(ide),0)+1`) y
     `ER1`–`ER13` (`COUNT(*)`) son agregados sin `GROUP BY`: siempre una fila y, salvo `SUM`, nunca
     NULL. Para `SUM`, la versión anterior tampoco cubría NULL dentro de la fila: comportamiento igual.
   - #50–#54: `assert` partidos; mutantes nuevos `is None` caen.
   - #63–#66: ver O1.
4. **¿Relanzar la campaña por T20?** **No hace falta.** El delta `eba243e..2879ddb` en producción es solo
   el diff de T20 (3 ficheros); en `tests/` solo **añade** (0 líneas borradas). Los 15 mutantes que T20
   crea están medidos y mueren (4); los 30 que desaparecen son los 16 de código muerto más 14 que ya
   estaban muertos en líneas reescritas; el resto de mutantes son textualmente los mismos y la suite solo
   ha crecido, así que no pueden revivir. Relanzar costaría ~5 h para el mismo resultado.

## Checkpoints de C4 bis (parte de mutación)

- [x] Rigor declarado: `critico`.
- [x] **Mutación**: `progress/mutacion_F-008.md` generado por la herramienta, totales verificados (1).
- [x] **Muertos comprobados**: Tiempo total 17.936 s > 60 s → **campaña no reejecutada (≈5 h según el
      informe)**; en su lugar recálculo puro, RM1–RM6 y la muestra de 50 muertos (5).
- [x] **Coste por mutante**: 17.936 × 1 ÷ 568 = 31,6 s > 1 s.
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0.
- [x] **RM1**: SHA medido `eba243e`, no es HEAD; lo cambiado después toca el alcance (T20) y el delta
      está medido entero por mí (punto 4). Alcance revisado: 2755 líneas en `2879ddb` frente a 2738.
- [x] **RM2**: 568 × 31,6 = 17.949 ≈ 17.936 s; media 31,6 s = 14,6 % de la base 216,1 s (no hay salto de
      orden de magnitud; lo explica el 82 % de muertos con `-x`).
- [x] **RM3**: ningún mutante equivalente aparece como muerto; los dos mal etiquetados de O1 son
      supervivientes, no muertos.
- [x] **RM4**: aplicado como verificación principal (subconjunto `-k f008` sobre copia aislada).
- [x] **RM5**: reproducido UNO elegido por mí (#64–#66, `_fecha_real`) por fuerza bruta (6).
- [x] **RM6**: guardas quitadas (#29, #32–#35) con el invariante verificado en quien construye el dato.
- N/A Campaña manual: la automática generó 568 mutantes; no hubo sustitución manual.
- [x] Ningún análisis en `PENDIENTE`; supervivientes restantes 0.
- [x] «Evidencias» de `impl_F-008.md` con mutantes, supervivientes, workers (1) y tiempo.

## Observación no bloqueante

**O1.** `mutacion_F-008.md` etiqueta #64 (`10000101 < valor`) y #65 (`valor < 99991231`) como
«equivalentes» por «tope redundante». **No lo son**: rechazan 1000-01-01 y 9999-12-31, que la original
acepta (medido en `rm5_fecha.py`). Solo #66 es equivalente. No cambia el veredicto: la línea ya no existe,
la reescritura es equivalente a la original (0 diferencias) y `test_f008_r2_fecha_en_los_bordes_vale`
cubre 10000101 y 99991231. Si se toca el informe, conviene corregir esas dos frases.

## Propuesta de automejora (no aplicada)

Que `harness.mutacion` se niegue a arrancar (o marque la campaña) si detecta otra campaña o worktree de
medición activos sobre el mismo repositorio: los 3 falsos vivos de F-008 nacen de esa concurrencia.
