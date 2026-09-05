<!-- progress/mutacion_F-004.md -->
# F-004 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-004 --workers 8` el 2026-09-06 00:23.

## Alcance

Origen del diff: **rama** (`f8bb8c69bdeb472d7f2fd68033f2fdfa722276f0` .. `feature/F-004-endpoint-concepto-grafico`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/attach_concepto_grafico_use_case.py` | 571 |
| `application/use_cases/concepto_grafico_statements.py` | 340 |
| `config/settings.py` | 81 |
| `domain/models/concepto_grafico_models.py` | 165 |
| `function_app.py` | 66 |
| `infrastructure/security/document_write_guard.py` | 160 |
| **Total** | **1383** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 167 |
| Mutantes evaluados | 167 |
| Muertos | 167 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 366.0 s |
| SHA de HEAD medido | `79c55208ebfef500b1c3b9e38926a635874f50cd` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_0` | 88.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_1` | 87.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_2` | 87.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_3` | 86.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_4` | 90.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_5` | 94.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_6` | 90.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-004_8y5jg25a/wk_7` | 87.7 |
| Media por mutante evaluado (s) | 2.2 |
| Timeout efectivo por mutante (s) | 189 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 8 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

---

> **De dónde sale ese cero.** No es que no hubiera nada que arreglar: la campaña
> anterior, sobre `d4e8535`, dejó **36 supervivientes**. Los 36 se reevaluaron EN
> SERIE (ninguno era falso), se cerraron con **16 tests nuevos** verificados en fase
> RED contra su propio mutante, y esos tests entraron en `79c5520` sin tocar una sola
> línea de producción. Lo que sigue es esa medición, superviviente a superviviente,
> y el aviso sobre lo que el modo paralelo hizo mal por el camino.


## Análisis de los 36 supervivientes de la campaña sobre `d4e8535`

Los 36 supervivientes que publicó la campaña paralela de `d4e8535` (167 mutantes,
131 muertos, 36 supervivientes, 0 timeouts) se cierran aquí uno a uno. Nada de esto
está leído: cada veredicto viene de EJECUTAR.

### Resumen

| Desenlace | Cuántos |
|---|---|
| Falsos supervivientes (mueren al reevaluarlos en serie) | **0** |
| Cerrados con **test nuevo** (RED contra el mutante, verde con el original) | **36** |
| **Equivalentes** propuestos al humano | **0** |

**Ningún superviviente queda pendiente de aceptación del humano**: los 36 eran huecos
de tests reales y los 36 tienen ya un test que los mata. 16 tests nuevos, ninguna
línea de producción tocada.

### Fase 1 — Reevaluación EN SERIE de los 36 (medida, no leída)

Reproducción exacta de la generación de la campaña sobre `d4e8535`:
`harness.alcance.alcance_de_feature('F-004')` → 6 ficheros, **1.383 líneas** (origen
`rama`, `f8bb8c6..feature/F-004-endpoint-concepto-grafico`), y
`harness.mutacion.generar_mutantes` → **167 mutantes**, el mismo número. Los 36
supervivientes publicados se localizan uno a uno ahí por (fichero, línea, operador,
texto original, texto mutado): **los 36, ninguno ambiguo**.

Ejecución: `git worktree add --detach <scratchpad>/wt_serie HEAD` y
`ejecutar_campania(alcance, EjecutorPytest(raiz=wt), mutantes=<los 36>, workers=1)`,
con el `.env` del árbol principal volcado al entorno igual que hace la campaña
(`mutacion_paralela.volcar_variables`) y con el mismo ejecutor que usa la paralela
(`ejecutor_para(..., raiz=wt, raiz_venvs=<árbol principal>)`, es decir
`pytest -x -q --tb=no -p no:cacheprovider tests`). Nada más corriendo en paralelo.

- **Línea base del worktree: 42,9 s, en verde** (la paralela midió 88,2-95,4 s por
  worker: eso era la contención).
- **Timeout efectivo: 120 s** (el suelo de `rigor.json`); la paralela concedió 191 s.
- **Resultado: 36 supervivientes, 0 muertos, 0 timeouts, `aviso_base = None`.**

**Cero falsos supervivientes.** A diferencia de F-003 —donde dos de nueve estaban mal
clasificados y uno moría en 1,9 s—, aquí la campaña paralela no se inventó ninguno:
los 36 son huecos de tests de verdad. Consecuencia práctica: no se descarta ninguno,
hay que cerrarlos todos.

### Fase 2 — Cómo se cerró cada uno

La decisión por defecto era el test nuevo, y ninguno necesitó la salida de
«equivalente»: los 36 cambian comportamiento observable. Cada test se verificó en
**RED contra su mutante**: mutante aplicado con `harness.mutacion.aplicar_mutante` en
el mismo worktree, con los ficheros de test nuevos copiados dentro, y
`python -m pytest -q --tb=no -p no:cacheprovider tests/test_f004_*.py`. Sin mutante
los 192 tests de esos cinco ficheros están en verde; con cada mutante puesto cae el
test que le corresponde y solo ese (los mutantes 10, 11, 18 y 19 tumban dos y tres
casos, porque sus tests están parametrizados).

Los 16 tests nuevos, por fichero:

| Fichero | Tests nuevos | Mutantes que matan |
|---|---|---|
| `tests/test_f004_document_write_guard.py` | 4 | 31-36 |
| `tests/test_f004_models.py` | 2 (uno con 8 casos) | 20-28 |
| `tests/test_f004_statements.py` | 2 (uno con 4 casos) | 13-19 |
| `tests/test_f004_use_case.py` | 7 | 1-12 |
| `tests/test_f004_route.py` | 1 | 29-30 |

### Ficha por superviviente

#### 1. `application/use_cases/attach_concepto_grafico_use_case.py:93` [aritmetico]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() + arranque) * 1000, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Ningun test miraba el VALOR de `duracion_ms`: `test_f004_r21_la_traza_lleva_lo_que_hace_falta` solo comprueba que la clave `duracion` aparece en el JSON. Y con el reloj real la duracion de la suite es de microsegundos, asi que casi cualquier formula produce un numero plausible.
> 
> **Decisión: TEST NUEVO** — `test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.56s   →  exit=1
> FAILED tests/…::test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 2. `application/use_cases/attach_concepto_grafico_use_case.py:93` [aritmetico]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() - arranque) // 1000, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 1, y peor: con el reloj real la traza sale `"duracion_ms": 0.0` (medido en la propia suite), que es EXACTAMENTE lo que devuelve `// 1000`. Sin fijar el reloj, mutante y original son indistinguibles.
> 
> **Decisión: TEST NUEVO** — `test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.58s   →  exit=1
> FAILED tests/…::test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 3. `application/use_cases/attach_concepto_grafico_use_case.py:93` [entero]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1001, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 1: nadie comparaba el numero, solo la presencia de la clave.
> 
> **Decisión: TEST NUEVO** — `test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.64s   →  exit=1
> FAILED tests/…::test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 4. `application/use_cases/attach_concepto_grafico_use_case.py:93` [entero]

- Original: `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 2)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 1. Ademas es el mas fino de los cuatro: solo se ve si la duracion tiene centesimas de milisegundo, cosa que un reloj no fijado no garantiza.
> 
> **Decisión: TEST NUEVO** — `test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.60s   →  exit=1
> FAILED tests/…::test_f004_r21_la_duracion_va_en_milisegundos_y_con_un_decimal
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 5. `application/use_cases/attach_concepto_grafico_use_case.py:94` [booleano]

- Original: `logger.info(json.dumps(traza, ensure_ascii=False, default=str))`
- Mutado:   `logger.info(json.dumps(traza, ensure_ascii=True, default=str))`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Ningun dato de los tests llevaba un caracter fuera de ASCII, asi que `ensure_ascii=True` y `False` producian byte a byte el mismo JSON.
> 
> **Decisión: TEST NUEVO** — `test_f004_r21_la_traza_no_escapa_los_acentos`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.74s   →  exit=1
> FAILED tests/…::test_f004_r21_la_traza_no_escapa_los_acentos
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 6. `application/use_cases/attach_concepto_grafico_use_case.py:251` [entero]

- Original: `ide, tip, emp, cod, res = filas[0][:5]`
- Mutado:   `ide, tip, emp, cod, res = filas[0][:6]`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Todas las filas de `concepto` de los dobles traen exactamente 5 columnas, y sobre una tupla de 5 `[:5]` y `[:6]` dan lo mismo. El corte defensivo solo se nota si la fila trae columnas de mas, que es justo el caso para el que se escribio.
> 
> **Decisión: TEST NUEVO** — `test_f004_r7_una_fila_de_concepto_con_columnas_de_mas_no_revienta`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.64s   →  exit=1
> FAILED tests/…::test_f004_r7_una_fila_de_concepto_con_columnas_de_mas_no_revienta
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 7. `application/use_cases/attach_concepto_grafico_use_case.py:273` [logico]

- Original: `if fila is not None and not (fila[4] or "").strip():`
- Mutado:   `if fila is not None or not (fila[4] or "").strip():`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Solo estaba probado el `tipaso` VACIO (`test_f004_r17_la_clase_sin_tipaso_se_avisa`), que entra en la rama por las dos versiones. Faltaba el caso feliz —clase con `tipaso`—, donde el mutante avisa de algo que no pasa.
> 
> **Decisión: TEST NUEVO** — `test_f004_r7_una_clase_con_tipaso_no_genera_ningun_aviso`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.31s   →  exit=1
> FAILED tests/…::test_f004_r7_una_clase_con_tipaso_no_genera_ningun_aviso
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 8. `application/use_cases/attach_concepto_grafico_use_case.py:273` [logico]

- Original: `if fila is not None and not (fila[4] or "").strip():`
- Mutado:   `if fila is not None and not (fila[4] and "").strip():`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 7: con `tipaso` vacio, `(fila[4] or "")` y `(fila[4] and "")` dan los dos la cadena vacia y el aviso sale igual.
> 
> **Decisión: TEST NUEVO** — `test_f004_r7_una_clase_con_tipaso_no_genera_ningun_aviso`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.26s   →  exit=1
> FAILED tests/…::test_f004_r7_una_clase_con_tipaso_no_genera_ningun_aviso
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 9. `application/use_cases/attach_concepto_grafico_use_case.py:307` [entero]

- Original: `ide_negocio, cod_existente, ide_enlace, binario = fila[:4]`
- Mutado:   `ide_negocio, cod_existente, ide_enlace, binario = fila[:5]`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo motivo que el 6, en la busqueda de idempotencia: los candidatos de los dobles traen exactamente 4 columnas.
> 
> **Decisión: TEST NUEVO** — `test_f004_r17_un_candidato_con_columnas_de_mas_no_revienta`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.36s   →  exit=1
> FAILED tests/…::test_f004_r17_un_candidato_con_columnas_de_mas_no_revienta
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 10. `application/use_cases/attach_concepto_grafico_use_case.py:387` [not]

- Original: `dry_run=not request.commit,`
- Mutado:   `dry_run=request.commit,`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** La respuesta idempotente se comprobaba a fondo (`idempotente`, `committed`, `cod`, los dos `ide`, `filas_afectadas`) pero nunca su `dry_run`, que es el campo por el que el cliente distingue una simulacion de una peticion real que no tuvo nada que escribir.
> 
> **Decisión: TEST NUEVO** — `test_f004_r17_la_respuesta_idempotente_declara_el_modo_y_no_inventa_fecha`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 2 failed, 190 passed, 1 warning in 1.39s   →  exit=1
> FAILED tests/…::test_f004_r17_la_respuesta_idempotente_declara_el_modo_y_no_inventa_fecha
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 11. `application/use_cases/attach_concepto_grafico_use_case.py:393` [entero]

- Original: `request, documento, cod_existente, concepto.emp, 0,`
- Mutado:   `request, documento, cod_existente, concepto.emp, 1,`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Nadie miraba el `fec` de la respuesta idempotente. Es 0 a proposito: la fila no se ha creado ahora, y darle una fecha inventada seria mentir sobre cuando se colgo el documento.
> 
> **Decisión: TEST NUEVO** — `test_f004_r17_la_respuesta_idempotente_declara_el_modo_y_no_inventa_fecha`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 2 failed, 190 passed, 1 warning in 1.56s   →  exit=1
> FAILED tests/…::test_f004_r17_la_respuesta_idempotente_declara_el_modo_y_no_inventa_fecha
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 12. `application/use_cases/attach_concepto_grafico_use_case.py:540` [booleano]

- Original: `idempotente=False,`
- Mutado:   `idempotente=True,`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** El `idempotente is False` estaba asertado en el dry-run y en el caso de binario distinto, pero nunca en la respuesta del COMMIT, que es la que lo construye en la linea 540.
> 
> **Decisión: TEST NUEVO** — `test_f004_r11_la_respuesta_del_commit_dice_que_no_fue_idempotente`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.58s   →  exit=1
> FAILED tests/…::test_f004_r11_la_respuesta_del_commit_dice_que_no_fue_idempotente
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 13. `application/use_cases/concepto_grafico_statements.py:62` [aritmetico]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio - 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** La rama `mes == 12` de `_ultimo_domingo` no la ejecuta nadie: la regla de respaldo solo pregunta por marzo y por octubre, y el helper no se probaba de forma directa.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.56s   →  exit=1
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 14. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 2, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 13.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.53s   →  exit=1
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 15. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 1, 2, 1) if mes == 12 else date(anio, mes + 1, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 13.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.50s   →  exit=1
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 16. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 1, 1, 2) if mes == 12 else date(anio, mes + 1, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 13. Ademas es el mas sutil: `date(anio + 1, 1, 2)` solo se separa del original en los anios cuyo 31 de diciembre NO cae en domingo.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.13s   →  exit=1
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 17. `application/use_cases/concepto_grafico_statements.py:62` [entero]

- Original: `date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)`
- Mutado:   `date(anio + 1, 1, 1) if mes == 13 else date(anio, mes + 1, 1)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 13; con `mes == 13` la condicion no se cumple nunca y diciembre acaba pidiendo `date(anio, 13, 1)`, que revienta. Nadie llamaba con `mes=12`, asi que nadie lo veia.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.11s   →  exit=1
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 18. `application/use_cases/concepto_grafico_statements.py:64` [entero]

- Original: `ultimo = primero_del_siguiente - timedelta(days=1)`
- Mutado:   `ultimo = primero_del_siguiente - timedelta(days=2)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Restar un dia de mas solo cambia el resultado cuando el ULTIMO DIA del mes es domingo. Los casos probados eran de 2026 (31 de marzo martes, 31 de octubre sabado), donde las dos versiones coinciden.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_cambio_de_hora_cuando_el_mes_acaba_en_domingo`, `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 3 failed, 189 passed, 1 warning in 1.07s   →  exit=1
> FAILED tests/…::test_f004_r13_el_cambio_de_hora_cuando_el_mes_acaba_en_domingo
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 19. `application/use_cases/concepto_grafico_statements.py:65` [entero]

- Original: `return ultimo - timedelta(days=(ultimo.weekday() + 1) % 7)`
- Mutado:   `return ultimo - timedelta(days=(ultimo.weekday() + 1) % 8)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** `% 8` solo se separa de `% 7` cuando `weekday() == 6`, es decir cuando el ultimo dia del mes es domingo: el mismo borde que el 18, y por el mismo motivo no estaba cubierto.
> 
> **Decisión: TEST NUEVO** — `test_f004_r13_el_cambio_de_hora_cuando_el_mes_acaba_en_domingo`, `test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 3 failed, 189 passed, 1 warning in 1.03s   →  exit=1
> FAILED tests/…::test_f004_r13_el_cambio_de_hora_cuando_el_mes_acaba_en_domingo
> FAILED tests/…::test_f004_r13_el_ultimo_domingo_lo_es_en_los_540_meses_de_1996_a_2040
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 20. `domain/models/concepto_grafico_models.py:68` [entero]

- Original: `database: str = Field(..., min_length=1)          # base de NEGOCIO (ruesma)`
- Mutado:   `database: str = Field(..., min_length=2)          # base de NEGOCIO (ruesma)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Estaba probado el borde de ARRIBA (`max_length`) y el rechazo del vacio, pero no el valor minimo exacto que si tiene que entrar.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.18s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 21. `domain/models/concepto_grafico_models.py:69` [entero]

- Original: `conide: int = Field(..., ge=1)                    # con.ide del concepto`
- Mutado:   `conide: int = Field(..., ge=2)                    # con.ide del concepto`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Estaba probado que `0` se rechaza, no que `1` se acepta: subir el `ge` a 2 cerraria la puerta a un `ide` legitimo del ERP sin que ningun test protestara.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.09s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 22. `domain/models/concepto_grafico_models.py:70` [entero]

- Original: `contip: int = Field(..., ge=1)                    # con.tip esperado (se coteja)`
- Mutado:   `contip: int = Field(..., ge=2)                    # con.tip esperado (se coteja)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 21.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.37s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 23. `domain/models/concepto_grafico_models.py:71` [entero]

- Original: `gratipide: int = Field(..., ge=1)                 # clase de grafico (auxgra.ide)`
- Mutado:   `gratipide: int = Field(..., ge=2)                 # clase de grafico (auxgra.ide)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 21.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.36s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 24. `domain/models/concepto_grafico_models.py:72` [entero]

- Original: `res: str = Field(..., min_length=1, max_length=48)`
- Mutado:   `res: str = Field(..., min_length=2, max_length=48)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 20: `res` tenia probado el limite de 48 y el vacio, no el de una letra.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.38s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 25. `domain/models/concepto_grafico_models.py:73` [entero]

- Original: `nom: str = Field(..., min_length=1, max_length=255)`
- Mutado:   `nom: str = Field(..., min_length=2, max_length=255)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 20, en `nom`.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.43s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 26. `domain/models/concepto_grafico_models.py:76` [entero]

- Original: `usu: str = Field(..., min_length=1, max_length=24)`
- Mutado:   `usu: str = Field(..., min_length=2, max_length=24)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 20, en `usu`.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.31s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 27. `domain/models/concepto_grafico_models.py:77` [entero]

- Original: `contenido_base64: str = Field(..., min_length=4)`
- Mutado:   `contenido_base64: str = Field(..., min_length=5)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** El minimo de 4 caracteres —un bloque de base64— no lo comprobaba nadie: los tests usaban base64 de un PDF entero.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.29s   →  exit=1
> FAILED tests/…::test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 28. `domain/models/concepto_grafico_models.py:96` [logico]

- Original: `if not limpio or len(limpio) % 4 != 0 or not _BASE64_RE.fullmatch(limpio):`
- Mutado:   `if not limpio and len(limpio) % 4 != 0 or not _BASE64_RE.fullmatch(limpio):`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** El unico caso de la lista de mal formados con longitud no multiplo de 4 es `AAA`, de 3 caracteres: el `min_length=4` lo rechaza igual, asi que la comprobacion del multiplo de 4 nunca era la que decidia. Hacia falta una cadena de 5 caracteres del alfabeto valido.
> 
> **Decisión: TEST NUEVO** — `test_f004_r1_un_base64_con_longitud_no_multiplo_de_cuatro_se_rechaza`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.29s   →  exit=1
> FAILED tests/…::test_f004_r1_un_base64_con_longitud_no_multiplo_de_cuatro_se_rechaza
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 29. `function_app.py:275` [entero]

- Original: `settings, repository = deps[0], deps[1]`
- Mutado:   `settings, repository = deps[1], deps[1]`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** El doble de `build_dependencies` devolvia `(None,) * 7`: todas las posiciones de la tupla son indistinguibles y coger la equivocada no se nota.
> 
> **Decisión: TEST NUEVO** — `test_f004_r3_la_ruta_toma_settings_y_repositorio_de_las_dos_primeras_posiciones`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.49s   →  exit=1
> FAILED tests/…::test_f004_r3_la_ruta_toma_settings_y_repositorio_de_las_dos_primeras_posiciones
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 30. `function_app.py:275` [entero]

- Original: `settings, repository = deps[0], deps[1]`
- Mutado:   `settings, repository = deps[0], deps[2]`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 29.
> 
> **Decisión: TEST NUEVO** — `test_f004_r3_la_ruta_toma_settings_y_repositorio_de_las_dos_primeras_posiciones`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.55s   →  exit=1
> FAILED tests/…::test_f004_r3_la_ruta_toma_settings_y_repositorio_de_las_dos_primeras_posiciones
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 31. `infrastructure/security/document_write_guard.py:36` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Nadie intentaba modificar un `DocumentoValidado` despues de construirlo, asi que la congelacion del dataclass no la ejercitaba ningun test.
> 
> **Decisión: TEST NUEVO** — `test_f004_r8_el_documento_validado_es_inmutable`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.40s   →  exit=1
> FAILED tests/…::test_f004_r8_el_documento_validado_es_inmutable
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 32. `infrastructure/security/document_write_guard.py:64` [entero]

- Original: `tope_base64 = math.ceil(max_bytes * 4 / 3) + 4`
- Mutado:   `tope_base64 = math.ceil(max_bytes * 5 / 3) + 4`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Los tests del tope usaban valores muy por encima (100 caracteres con `max_bytes=10`) o muy por debajo; el borde exacto —tope y tope+1— no lo tocaba ninguno.
> 
> **Decisión: TEST NUEVO** — `test_f004_r8_un_caracter_por_encima_del_tope_muere_antes_de_decodificar`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.40s   →  exit=1
> FAILED tests/…::test_f004_r8_un_caracter_por_encima_del_tope_muere_antes_de_decodificar
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 33. `infrastructure/security/document_write_guard.py:64` [entero]

- Original: `tope_base64 = math.ceil(max_bytes * 4 / 3) + 4`
- Mutado:   `tope_base64 = math.ceil(max_bytes * 4 / 4) + 4`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 32, por el otro lado: un tope mas corto seguia rechazando los 100 caracteres del test existente.
> 
> **Decisión: TEST NUEVO** — `test_f004_r8_la_longitud_exacta_del_tope_del_base64_no_se_rechaza`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.45s   →  exit=1
> FAILED tests/…::test_f004_r8_la_longitud_exacta_del_tope_del_base64_no_se_rechaza
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 34. `infrastructure/security/document_write_guard.py:64` [entero]

- Original: `tope_base64 = math.ceil(max_bytes * 4 / 3) + 4`
- Mutado:   `tope_base64 = math.ceil(max_bytes * 4 / 3) + 5`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** Mismo hueco que el 32: `+5` en vez de `+4` solo se ve en la longitud exacta del tope mas uno.
> 
> **Decisión: TEST NUEVO** — `test_f004_r8_un_caracter_por_encima_del_tope_muere_antes_de_decodificar`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.38s   →  exit=1
> FAILED tests/…::test_f004_r8_un_caracter_por_encima_del_tope_muere_antes_de_decodificar
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 35. `infrastructure/security/document_write_guard.py:65` [comparacion]

- Original: `if len(contenido_base64) > tope_base64:`
- Mutado:   `if len(contenido_base64) >= tope_base64:`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** `>` y `>=` solo se separan cuando la longitud es EXACTAMENTE la del tope, y ningun test caia ahi.
> 
> **Decisión: TEST NUEVO** — `test_f004_r8_la_longitud_exacta_del_tope_del_base64_no_se_rechaza`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.47s   →  exit=1
> FAILED tests/…::test_f004_r8_la_longitud_exacta_del_tope_del_base64_no_se_rechaza
> ```
> 
> Con el original, los mismos 192 tests en verde.

#### 36. `infrastructure/security/document_write_guard.py:92` [logico]

- Original: `f"({', '.join(firmas_permitidas) or '(ninguna)'}).",`
- Mutado:   `f"({', '.join(firmas_permitidas) and '(ninguna)'}).",`

##### Análisis

> **Serie (sin contención): SUPERVIVIENTE.** No es un falso superviviente de la
> campaña paralela: reevaluado a solas, con la línea base en verde a 42,9 s y
> 120 s de reloj, la suite sigue pasando con el mutante puesto.
> 
> **Por qué ningún test lo cazaba.** `test_f004_r8_una_lista_de_firmas_vacia_no_admite_nada` solo comprueba el `codigo`, no el mensaje; y no habia ningun test que exigiera que el mensaje nombrara las firmas que si valen.
> 
> **Decisión: TEST NUEVO** — `test_f004_r8_el_error_de_firma_nombra_las_firmas_que_si_valen`.
> 
> **Evidencia (RED, medida).** Con el mutante aplicado en el worktree:
> 
> ```
> 1 failed, 191 passed, 1 warning in 1.17s   →  exit=1
> FAILED tests/…::test_f004_r8_el_error_de_firma_nombra_las_firmas_que_si_valen
> ```
> 
> Con el original, los mismos 192 tests en verde.

---

## Aviso medido: el modo paralelo inventó 5 supervivientes por el camino

Entre la campaña de `d4e8535` y la de este informe hubo una tercera, la primera
lanzada sobre `79c5520` (el commit de los tests nuevos). Dio **167 mutantes, 162
muertos y 5 supervivientes**, y **los cinco eran nuevos**: ninguno estaba entre los
36 de `d4e8535`, donde los cinco salieron **muertos**. Los cinco están en el camino
de lectura de `attach_concepto_grafico_use_case.py`:

| Mutante | En `d4e8535` | 1.ª campaña sobre `79c5520` | Reevaluado EN SERIE |
|---|---|---|---|
| `:191` [logico] `and …write_enabled` → `or …` | muerto | superviviente | **muerto** |
| `:246` [not] `if not filas:` → `if filas:` | muerto | superviviente | **muerto** |
| `:270` [comparacion] `existe=fila is not None` → `is None` | muerto | superviviente | **muerto** |
| `:271` [logico] `int(fila[3] or 0)` → `int(fila[3] and 0)` | muerto | superviviente | **muerto** |
| `:294` [entero] `int(filas[0][0])` → `int(filas[0][1])` | muerto | superviviente | **muerto** |

**Medición**, con el mismo método de la fase 1: `git worktree add --detach` sobre
`79c5520`, `ejecutar_campania(..., mutantes=<los 5>, workers=1)`, línea base del
worktree **41,0 s en verde**, timeout 120 s, nada más corriendo.
**Resultado: 5 muertos, 0 supervivientes, 0 timeouts, `aviso_base = None`.** Los
cinco los cazan tests que ya existían antes de este encargo; no hacía falta ni un
test nuevo.

**Se repitió el ciclo, como manda el encargo.** La campaña se relanzó con los mismos
8 workers, esta vez con el ejecutor instrumentado (anota de cada veredicto que no
sea «muerto» el código de salida de pytest, si el fichero mutado estaba de verdad en
disco y la cola de la salida): **167 evaluados, 167 muertos, 0 supervivientes, 0
timeouts, y cero veredictos no-muerto que registrar**. La campaña oficial de este
informe, la tercera sobre `79c5520`, volvió a dar **167/167 muertos**.

**Lo que esto deja probado y lo que no.** Probado: el modo paralelo con 8 workers
**produce falsos supervivientes de forma no reproducible** —cinco en una tirada,
cero en las dos siguientes sobre el MISMO commit—, así que un superviviente suyo no
vale como evidencia hasta remedirlo en serie. Es el mismo defecto que se vio en
F-003 (dos de nueve mal clasificados, uno de ellos muerto en 1,9 s), ahora con una
muestra mayor y con los dos veredictos contrarios sobre el mismo código. No
probado: la causa. El intento de cazarla en vivo no dio nada porque en esa tirada no
hubo ni un veredicto no-muerto que registrar; la sospecha razonable —y **no
medida**— es que `ResultadoSuite.verde` cuenta como superviviente el código de
salida 5 de pytest («nada que recoger»), que bajo contención podría aparecer sin que
el mutante tenga nada que ver. **Queda como tarea del arnés**, no de esta feature.

El sesgo, eso sí, es **pesimista** en las tres campañas medidas hasta hoy: convierte
muertos en supervivientes, nunca al revés (F-003 remidió los 138 mutantes y encontró
**0 falsos muertos** sobre 123). Un sesgo pesimista no esconde huecos de tests: los
inventa. Por eso este cero es sólido —no hay ningún mutante que la campaña dé por
cazado sin estarlo— y por eso cada superviviente se remide antes de escribir sobre él.
