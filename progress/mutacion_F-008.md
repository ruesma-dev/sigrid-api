<!-- progress/mutacion_F-008.md -->
# F-008 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-008 --workers 1` el 2026-10-30 23:36.

## Alcance

Origen del diff: **rama** (`ccfb334b2de0302a3a88d17555c76c618a3dfa33` .. `feature/F-008-registrar-factura`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/create_factura_use_case.py` | 1114 |
| `application/use_cases/factura_lineas.py` | 514 |
| `application/use_cases/factura_statements.py` | 754 |
| `config/settings.py` | 29 |
| `domain/models/factura_models.py` | 238 |
| `function_app.py` | 89 |
| **Total** | **2738** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 568 |
| Mutantes evaluados | 568 |
| Muertos | 467 |
| Supervivientes | 101 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 17936.0 s |
| SHA de HEAD medido | `eba243e02fdc547144b9ce6139382df6c3d65e5c` |
| Línea base (s) — `.` | 216.1 |
| Media por mutante evaluado (s) | 31.6 |
| Timeout efectivo por mutante (s) | 433 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Resultado tras el análisis (T20, medido)

Cada superviviente se aplicó, uno a uno, en un worktree aislado con el código y los tests finales, y se corrió
`python -m pytest -q -x tests -k f008` (script en el scratchpad de la sesión; nada se aceptó sin ejecutarlo).

| Clase | Nº | Qué se hizo |
|---|---|---|
| Hueco real: test nuevo que lo mata | 82 | 31 tests (70 casos) en `tests/test_f008_mutantes.py`; muerte medida |
| Falso superviviente de la campaña | 3 | 76, 85, 182: los caza la suite **sin cambios**; la campaña los dio por vivos (ver abajo) |
| Código muerto o equivalente | 16 | línea quitada o reescrita; los mutantes de las líneas nuevas caen (medido) |
| **Supervivientes restantes** | **0** | ninguno pendiente de aceptación del humano |

Los tres falsos positivos: la campaña corrió en el árbol principal mientras yo medía en otro worktree, y su
`pytest` dio verde con el mutante aplicado; aislado, el mismo mutante cae con los tests de antes de T20. No he
encontrado la causa (el arnés purga el bytecode y usa `PYTHONDONTWRITEBYTECODE`). Como un falso superviviente
es conservador, no invalida los 467 muertos, pero queda anotado para el reviewer.

Los números de línea de abajo son los de la campaña (HEAD `eba243e`); el código final los desplaza unas líneas.

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/create_factura_use_case.py:143` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test intentaba modificar los datos internos congelados.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_la_obra_y_la_factura_montada_son_inmutables`. Medido: el mutante cae.

### 2. `application/use_cases/create_factura_use_case.py:178` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test intentaba modificar los datos internos congelados.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_la_obra_y_la_factura_montada_son_inmutables`. Medido: el mutante cae.

### 3. `application/use_cases/create_factura_use_case.py:243` [aritmetico]

- Original: `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((self._reloj() + arranque) * 1000, 1)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test fijaba el reloj y comprobaba `duracion_ms`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r46_duracion_en_milisegundos_con_un_decimal`. Medido: el mutante cae.

### 4. `application/use_cases/create_factura_use_case.py:243` [aritmetico]

- Original: `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((self._reloj() - arranque) // 1000, 1)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test fijaba el reloj y comprobaba `duracion_ms`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r46_duracion_en_milisegundos_con_un_decimal`. Medido: el mutante cae.

### 5. `application/use_cases/create_factura_use_case.py:243` [entero]

- Original: `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((self._reloj() - arranque) * 1001, 1)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test fijaba el reloj y comprobaba `duracion_ms`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r46_duracion_en_milisegundos_con_un_decimal`. Medido: el mutante cae.

### 6. `application/use_cases/create_factura_use_case.py:243` [entero]

- Original: `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)`
- Mutado:   `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 2)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test fijaba el reloj y comprobaba `duracion_ms`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r46_duracion_en_milisegundos_con_un_decimal`. Medido: el mutante cae.

### 7. `application/use_cases/create_factura_use_case.py:244` [booleano]

- Original: `logger.info(json.dumps(traza, ensure_ascii=False, default=str))`
- Mutado:   `logger.info(json.dumps(traza, ensure_ascii=True, default=str))`

#### Análisis

> Por que ningun test lo cazaba: Ninguna traza llevaba texto no ASCII.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r46_la_traza_se_lee_en_castellano`. Medido: el mutante cae.

### 8. `application/use_cases/create_factura_use_case.py:316` [comparacion]

- Original: `if len(request.lineas) > tope:`
- Mutado:   `if len(request.lineas) >= tope:`

#### Análisis

> Por que ningun test lo cazaba: El tope solo se probaba por encima, nunca justo en el borde.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r8_justo_en_el_tope_pasa`. Medido: el mutante cae.

### 9. `application/use_cases/create_factura_use_case.py:391` [logico]

- Original: `mismo_cif = bool(proveedor) and _cif(proveedor[0][3]) == _cif(request.cif_proveedor)`
- Mutado:   `mismo_cif = bool(proveedor) or _cif(proveedor[0][3]) == _cif(request.cif_proveedor)`

#### Análisis

> Por que ningun test lo cazaba: El conflicto solo se probaba cambiando el numero, no el proveedor, ni con proveedor inexistente; y no se miraba `details`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r43_conflicto_por_proveedor`. Medido: el mutante cae.

### 10. `application/use_cases/create_factura_use_case.py:392` [entero]

- Original: `if len(filas) > 1 or not mismo_cif or str(fila[3] or "").strip() != request.numero_factura:`
- Mutado:   `if len(filas) > 2 or not mismo_cif or str(fila[3] or "").strip() != request.numero_factura:`

#### Análisis

> Por que ningun test lo cazaba: Nunca habia dos facturas con la misma referencia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r43_dos_facturas_con_la_misma_referencia_son_conflicto`. Medido: el mutante cae.

### 11. `application/use_cases/create_factura_use_case.py:392` [logico]

- Original: `if len(filas) > 1 or not mismo_cif or str(fila[3] or "").strip() != request.numero_factura:`
- Mutado:   `if len(filas) > 1 and not mismo_cif or str(fila[3] or "").strip() != request.numero_factura:`

#### Análisis

> Por que ningun test lo cazaba: Nunca habia dos facturas con la misma referencia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r43_dos_facturas_con_la_misma_referencia_son_conflicto`. Medido: el mutante cae.

### 12. `application/use_cases/create_factura_use_case.py:396` [entero]

- Original: `details={"cod": str(fila[1] or "").strip()},`
- Mutado:   `details={"cod": str(fila[2] or "").strip()},`

#### Análisis

> Por que ningun test lo cazaba: El conflicto solo se probaba cambiando el numero, no el proveedor, ni con proveedor inexistente; y no se miraba `details`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r43_conflicto_por_proveedor`. Medido: el mutante cae.

### 13. `application/use_cases/create_factura_use_case.py:396` [logico]

- Original: `details={"cod": str(fila[1] or "").strip()},`
- Mutado:   `details={"cod": str(fila[1] and "").strip()},`

#### Análisis

> Por que ningun test lo cazaba: El conflicto solo se probaba cambiando el numero, no el proveedor, ni con proveedor inexistente; y no se miraba `details`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r43_conflicto_por_proveedor`. Medido: el mutante cae.

### 14. `application/use_cases/create_factura_use_case.py:418` [entero]

- Original: `almide, cenide = (ficha[0][0], ficha[0][1]) if ficha else (0, 0)`
- Mutado:   `almide, cenide = (ficha[0][0], ficha[0][1]) if ficha else (1, 0)`

#### Análisis

> Por que ningun test lo cazaba: El doble siempre devolvia ficha de almacen para la obra.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_obra_sin_ficha_de_almacen_queda_a_cero_en_la_cabecera`. Medido: el mutante cae.

### 15. `application/use_cases/create_factura_use_case.py:418` [entero]

- Original: `almide, cenide = (ficha[0][0], ficha[0][1]) if ficha else (0, 0)`
- Mutado:   `almide, cenide = (ficha[0][0], ficha[0][1]) if ficha else (0, 1)`

#### Análisis

> Por que ningun test lo cazaba: El doble siempre devolvia ficha de almacen para la obra.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_obra_sin_ficha_de_almacen_queda_a_cero_en_la_cabecera`. Medido: el mutante cae.

### 16. `application/use_cases/create_factura_use_case.py:457` [entero]

- Original: `if len({_entero(o["emp"]) for o in origenes}) > 1 or len({_entero(o["obride"]) for o in origenes}) > 1 \`
- Mutado:   `if len({_entero(o["emp"]) for o in origenes}) > 2 or len({_entero(o["obride"]) for o in origenes}) > 1 \`

#### Análisis

> Por que ningun test lo cazaba: Ningun caso tenia dos empresas con la misma obra.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r13_misma_obra_en_dos_empresas_son_varias_obras`. Medido: el mutante cae.

### 17. `application/use_cases/create_factura_use_case.py:461` [comparacion]

- Original: `if len({_entero(o["ctride"]) for o in origenes}) > 1:`
- Mutado:   `if len({_entero(o["ctride"]) for o in origenes}) >= 1:`

#### Análisis

> Medido: el mutante **cae** con la suite SIN cambios (test_f008_r13_varios_contratos (y toda previa con origen)), aplicado aislado en un worktree.
> El «superviviente» es un falso positivo de la campana (corrio a la vez que mis mediciones en otro
> arbol; no explicado). Decision: ninguna; no es un hueco.

### 18. `application/use_cases/create_factura_use_case.py:487` [comparacion]

- Original: `_entero(origen["est"]) != estados[(TIP_ALBARAN, CON)]`
- Mutado:   `_entero(origen["est"]) == estados[(TIP_ALBARAN, CON)]`

#### Análisis

> Medido: el mutante **cae** con la suite SIN cambios (test_f008_r14_origen_sin_contabilizar_por_estado_y_por_asiento), aplicado aislado en un worktree.
> El «superviviente» es un falso positivo de la campana (corrio a la vez que mis mediciones en otro
> arbol; no explicado). Decision: ninguna; no es un hueco.

### 19. `application/use_cases/create_factura_use_case.py:550` [entero]

- Original: `"almide": obra.almide, "empide": 0, "pagide": proveedor["pagide"], "pagtex": pagtex,`
- Mutado:   `"almide": obra.almide, "empide": 1, "pagide": proveedor["pagide"], "pagtex": pagtex,`

#### Análisis

> Por que ningun test lo cazaba: No se comprobaba `dcf.empide` en la cabecera sin origen.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_sin_origenes_la_cabecera_nace_sin_empresa_de_envio`. Medido: el mutante cae.

### 20. `application/use_cases/create_factura_use_case.py:578` [entero]

- Original: `or any(len(v) > 1 for v in por_origen.values())`
- Mutado:   `or any(len(v) > 2 for v in por_origen.values())`

#### Análisis

> Por que ningun test lo cazaba: Las dos retenciones de un origen siempre eran distintas (las cazaba la firma).
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r31_dos_retenciones_iguales_en_un_origen_no_se_copian`. Medido: el mutante cae.

### 21. `application/use_cases/create_factura_use_case.py:603` [logico]

- Original: `if modo == "origen" and enlazadas:`
- Mutado:   `if modo == "origen" or enlazadas:`

#### Análisis

> Por que ningun test lo cazaba: Ninguna linea de mes llevaba `canorilin`: la lectura de mas no se veia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r20_de_mes_no_se_leen_las_lineas_anteriores`. Medido: el mutante cae.

### 22. `application/use_cases/create_factura_use_case.py:652` [entero]

- Original: `clave(f[1]): (_entero(f[0]), float(f[2] or 0))`
- Mutado:   `clave(f[1]): (_entero(f[0]), float(f[2] or 1))`

#### Análisis

> Por que ningun test lo cazaba: Ningun IVA del doble tenia tasa NULL.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r24_iva_sin_tasa_en_la_ficha_cuenta_como_cero`. Medido: el mutante cae.

### 23. `application/use_cases/create_factura_use_case.py:687` [logico]

- Original: `prefijos = _unicos([a.split(".")[0] for a in analiticas if "." in a and a.split(".")[0]])`
- Mutado:   `prefijos = _unicos([a.split(".")[0] for a in analiticas if "." in a or a.split(".")[0]])`

#### Análisis

> Por que ningun test lo cazaba: Ninguna analitica sin obra delante (sin punto o empezando por punto).
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r26_analitica_sin_obra_delante_no_vale_ni_busca_obra`. Medido: el mutante cae.

### 24. `application/use_cases/create_factura_use_case.py:687` [entero]

- Original: `prefijos = _unicos([a.split(".")[0] for a in analiticas if "." in a and a.split(".")[0]])`
- Mutado:   `prefijos = _unicos([a.split(".")[0] for a in analiticas if "." in a and a.split(".")[1]])`

#### Análisis

> Por que ningun test lo cazaba: Ninguna analitica sin obra delante (sin punto o empezando por punto).
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r26_analitica_sin_obra_delante_no_vale_ni_busca_obra`. Medido: el mutante cae.

### 25. `application/use_cases/create_factura_use_case.py:757` [comparacion]

- Original: `if len(dcfpro) > tope:`
- Mutado:   `if len(dcfpro) >= tope:`

#### Análisis

> Por que ningun test lo cazaba: El tope total (origen + sin origen) no se probaba en el borde.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r8_justo_en_el_tope_contando_las_de_origen_pasa`. Medido: el mutante cae.

### 26. `application/use_cases/create_factura_use_case.py:760` [comparacion]

- Original: `if request.total_base <= 0:`
- Mutado:   `if request.total_base < 0:`

#### Análisis

> Por que ningun test lo cazaba: El abono solo se probaba con base negativa, no con 0.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r30_base_cero_tambien_es_abono`. Medido: el mutante cae.

### 27. `application/use_cases/create_factura_use_case.py:763` [entero]

- Original: `totbas = _d(totales_factura(dcfpro, cuo=Decimal(0))["totbas"])`
- Mutado:   `totbas = _d(totales_factura(dcfpro, cuo=Decimal(1))["totbas"])`

#### Análisis

> Codigo muerto o equivalente: El argumento `cuo=Decimal(0)` no influia en `totbas` (equivalente). Se sustituye por la suma directa de `tot`.
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 28. `application/use_cases/create_factura_use_case.py:772` [not]

- Original: `if (garantia and (vence is None or not fecha_de_vencimiento_valida(vence, fecha_factura=request.fecha_factura))) \`
- Mutado:   `if (garantia and (vence is None or fecha_de_vencimiento_valida(vence, fecha_factura=request.fecha_factura))) \`

#### Análisis

> Medido: el mutante **cae** con la suite SIN cambios (test_f008_r31_r34_retencion_del_origen_con_su_pag_cla_2), aplicado aislado en un worktree.
> El «superviviente» es un falso positivo de la campana (corrio a la vez que mis mediciones en otro
> arbol; no explicado). Decision: ninguna; no es un hueco.

### 29. `application/use_cases/create_factura_use_case.py:818` [entero]

- Original: `plazos.append((2, dcfrec["cuo"], int(request.vencimiento_retencion or 0),`
- Mutado:   `plazos.append((2, dcfrec["cuo"], int(request.vencimiento_retencion or 1),`

#### Análisis

> Codigo muerto o equivalente: `or 0` inalcanzable: con garantia `_montar` ya exige `vencimiento_retencion`. Se quita; un `assert` documenta el invariante (su mutante `is None` cae: medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 30. `application/use_cases/create_factura_use_case.py:981` [logico]

- Original: `if _entero(d["docoritip"]) == TIP_CONTRATO and _entero(d["linoriide"])`
- Mutado:   `if _entero(d["docoritip"]) == TIP_CONTRATO or _entero(d["linoriide"])`

#### Análisis

> Por que ningun test lo cazaba: Ninguna linea con `linoriide` sin ser de contrato.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r42_linea_con_linoriide_que_no_es_de_contrato_no_toca_el_ctrpro`. Medido: el mutante cae.

### 31. `application/use_cases/create_factura_use_case.py:989` [entero]

- Original: `esperado[ctrpro] = esperado.get(ctrpro, Decimal(0)) + _d(dcapro["can"])`
- Mutado:   `esperado[ctrpro] = esperado.get(ctrpro, Decimal(1)) + _d(dcapro["can"])`

#### Análisis

> Codigo muerto o equivalente: El defecto de `esperado.get(ctrpro, ...)` solo actuaba si la linea de contrato no existia, y entonces la relectura fallaba igual (equivalente). Ahora es un error explicito `filas_afectadas_inesperadas` ANTES del UPDATE, con `test_f008_r42_linea_de_contrato_que_ya_no_existe_revierte_sin_sumar` (RED: `KeyError: 9901`).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 32. `application/use_cases/create_factura_use_case.py:995` [entero]

- Original: `suma_can, suma_canser, suma_canfac = sumas[0] if sumas else (0, 0, 0)`
- Mutado:   `suma_can, suma_canser, suma_canfac = sumas[0] if sumas else (1, 0, 0)`

#### Análisis

> Codigo muerto o equivalente: El respaldo `(0, 0, 0)` era inalcanzable: `E10_SUMAS_CONTRATO` es un agregado sin GROUP BY y aqui siempre hay lineas vinculadas. Se quita.
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 33. `application/use_cases/create_factura_use_case.py:995` [entero]

- Original: `suma_can, suma_canser, suma_canfac = sumas[0] if sumas else (0, 0, 0)`
- Mutado:   `suma_can, suma_canser, suma_canfac = sumas[0] if sumas else (0, 1, 0)`

#### Análisis

> Codigo muerto o equivalente: El respaldo `(0, 0, 0)` era inalcanzable: `E10_SUMAS_CONTRATO` es un agregado sin GROUP BY y aqui siempre hay lineas vinculadas. Se quita.
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 34. `application/use_cases/create_factura_use_case.py:995` [entero]

- Original: `suma_can, suma_canser, suma_canfac = sumas[0] if sumas else (0, 0, 0)`
- Mutado:   `suma_can, suma_canser, suma_canfac = sumas[0] if sumas else (0, 0, 1)`

#### Análisis

> Codigo muerto o equivalente: El respaldo `(0, 0, 0)` era inalcanzable: `E10_SUMAS_CONTRATO` es un agregado sin GROUP BY y aqui siempre hay lineas vinculadas. Se quita.
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 35. `application/use_cases/create_factura_use_case.py:1062` [entero]

- Original: `return int(fila[0] or 0) if fila else 0`
- Mutado:   `return int(fila[0] or 0) if fila else 1`

#### Análisis

> Codigo muerto o equivalente: `if fila else 0` inalcanzable: reservas y relecturas son agregados sin GROUP BY (siempre una fila, nunca NULL). Se quita.
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 36. `application/use_cases/create_factura_use_case.py:1078` [logico]

- Original: `"origen": fila["docoricod"] or None, "linea": fila["linoriide"] or None,`
- Mutado:   `"origen": fila["docoricod"] and None, "linea": fila["linoriide"] or None,`

#### Análisis

> Por que ningun test lo cazaba: No se comparaba el resumen `lineas`/`origenes`/`vencimientos` de la respuesta.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r3_resumen_de_una_mixta`. Medido: el mutante cae.

### 37. `application/use_cases/create_factura_use_case.py:1078` [logico]

- Original: `"origen": fila["docoricod"] or None, "linea": fila["linoriide"] or None,`
- Mutado:   `"origen": fila["docoricod"] or None, "linea": fila["linoriide"] and None,`

#### Análisis

> Por que ningun test lo cazaba: No se comparaba el resumen `lineas`/`origenes`/`vencimientos` de la respuesta.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r3_resumen_de_una_mixta`. Medido: el mutante cae.

### 38. `application/use_cases/create_factura_use_case.py:1079` [comparacion]

- Original: `"indice": None if i < n_origen else i - n_origen, "can": fila["can"], "tot": fila["tot"],`
- Mutado:   `"indice": None if i <= n_origen else i - n_origen, "can": fila["can"], "tot": fila["tot"],`

#### Análisis

> Por que ningun test lo cazaba: No se comparaba el resumen `lineas`/`origenes`/`vencimientos` de la respuesta.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r3_resumen_de_una_mixta`. Medido: el mutante cae.

### 39. `application/use_cases/create_factura_use_case.py:1079` [aritmetico]

- Original: `"indice": None if i < n_origen else i - n_origen, "can": fila["can"], "tot": fila["tot"],`
- Mutado:   `"indice": None if i < n_origen else i + n_origen, "can": fila["can"], "tot": fila["tot"],`

#### Análisis

> Por que ningun test lo cazaba: No se comparaba el resumen `lineas`/`origenes`/`vencimientos` de la respuesta.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r3_resumen_de_una_mixta`. Medido: el mutante cae.

### 40. `application/use_cases/create_factura_use_case.py:1106` [booleano]

- Original: `database=request.database, estado="idempotente", committed=False, dry_run=not request.commit,`
- Mutado:   `database=request.database, estado="idempotente", committed=True, dry_run=not request.commit,`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 41. `application/use_cases/create_factura_use_case.py:1106` [not]

- Original: `database=request.database, estado="idempotente", committed=False, dry_run=not request.commit,`
- Mutado:   `database=request.database, estado="idempotente", committed=False, dry_run=request.commit,`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 42. `application/use_cases/create_factura_use_case.py:1109` [entero]

- Original: `totales={"totbas": float(fila[4] or 0), "totiva": float(fila[5] or 0),`
- Mutado:   `totales={"totbas": float(fila[4] or 1), "totiva": float(fila[5] or 0),`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 43. `application/use_cases/create_factura_use_case.py:1109` [entero]

- Original: `totales={"totbas": float(fila[4] or 0), "totiva": float(fila[5] or 0),`
- Mutado:   `totales={"totbas": float(fila[4] or 0), "totiva": float(fila[5] or 1),`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 44. `application/use_cases/create_factura_use_case.py:1110` [entero]

- Original: `"totdoc": float(fila[6] or 0), "tot": float(fila[7] or 0)},`
- Mutado:   `"totdoc": float(fila[7] or 0), "tot": float(fila[7] or 0)},`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 45. `application/use_cases/create_factura_use_case.py:1110` [entero]

- Original: `"totdoc": float(fila[6] or 0), "tot": float(fila[7] or 0)},`
- Mutado:   `"totdoc": float(fila[6] or 1), "tot": float(fila[7] or 0)},`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 46. `application/use_cases/create_factura_use_case.py:1110` [entero]

- Original: `"totdoc": float(fila[6] or 0), "tot": float(fila[7] or 0)},`
- Mutado:   `"totdoc": float(fila[6] or 0), "tot": float(fila[7] or 1)},`

#### Análisis

> Por que ningun test lo cazaba: La respuesta idempotente no se comparaba entera, ni en commit, ni con totales NULL o `tot` != `totdoc`.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r44_respuesta_idempotente_entera`. Medido: el mutante cae.

### 47. `application/use_cases/factura_lineas.py:262` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test intentaba modificar los datos internos congelados.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_la_obra_y_la_factura_montada_son_inmutables`. Medido: el mutante cae.

### 48. `application/use_cases/factura_lineas.py:279` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test intentaba modificar los datos internos congelados.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_la_obra_y_la_factura_montada_son_inmutables`. Medido: el mutante cae.

### 49. `application/use_cases/factura_lineas.py:302` [entero]

- Original: `obride: int = 0`
- Mutado:   `obride: int = 1`

#### Análisis

> Por que ningun test lo cazaba: Nadie construia `LecturasLineas` sin la parte FR.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_lecturas_sin_leer_quedan_vacias`. Medido: el mutante cae.

### 50. `application/use_cases/factura_lineas.py:347` [logico]

- Original: `assert iva is not None and leida is not None and caa is not None and obra is not None`
- Mutado:   `assert iva is not None or leida is not None and caa is not None and obra is not None`

#### Análisis

> Codigo muerto o equivalente: Conjuncion dentro de un `assert` de estrechado de tipos tras `if fallos: return`: cualquier `and`->`or` es equivalente. Se parte en un `assert` por valor; cada mutante `is None`/`not isinstance` cae (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 51. `application/use_cases/factura_lineas.py:347` [logico]

- Original: `assert iva is not None and leida is not None and caa is not None and obra is not None`
- Mutado:   `assert iva is not None and leida is not None or caa is not None and obra is not None`

#### Análisis

> Codigo muerto o equivalente: Conjuncion dentro de un `assert` de estrechado de tipos tras `if fallos: return`: cualquier `and`->`or` es equivalente. Se parte en un `assert` por valor; cada mutante `is None`/`not isinstance` cae (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 52. `application/use_cases/factura_lineas.py:347` [logico]

- Original: `assert iva is not None and leida is not None and caa is not None and obra is not None`
- Mutado:   `assert iva is not None and leida is not None and caa is not None or obra is not None`

#### Análisis

> Codigo muerto o equivalente: Conjuncion dentro de un `assert` de estrechado de tipos tras `if fallos: return`: cualquier `and`->`or` es equivalente. Se parte en un `assert` por valor; cada mutante `is None`/`not isinstance` cae (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 53. `application/use_cases/factura_lineas.py:507` [logico]

- Original: `assert iva is not None and isinstance(naturaleza, tuple) and paride is not None`
- Mutado:   `assert iva is not None or isinstance(naturaleza, tuple) and paride is not None`

#### Análisis

> Codigo muerto o equivalente: Conjuncion dentro de un `assert` de estrechado de tipos tras `if fallos: return`: cualquier `and`->`or` es equivalente. Se parte en un `assert` por valor; cada mutante `is None`/`not isinstance` cae (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 54. `application/use_cases/factura_lineas.py:507` [logico]

- Original: `assert iva is not None and isinstance(naturaleza, tuple) and paride is not None`
- Mutado:   `assert iva is not None and isinstance(naturaleza, tuple) or paride is not None`

#### Análisis

> Codigo muerto o equivalente: Conjuncion dentro de un `assert` de estrechado de tipos tras `if fallos: return`: cualquier `and`->`or` es equivalente. Se parte en un `assert` por valor; cada mutante `is None`/`not isinstance` cae (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 55. `application/use_cases/factura_statements.py:188` [entero]

- Original: `return Decimal(repr(float(valor or 0)))`
- Mutado:   `return Decimal(repr(float(valor or 1)))`

#### Análisis

> Por que ningun test lo cazaba: `totales_factura` no se probaba con NULL, ni con descuento menor que 1 %, ilegible o `tot` != can x tar.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r29_tot_e_ivacuo_nulos_suman_cero`. Medido: el mutante cae.

### 56. `application/use_cases/factura_statements.py:194` [entero]

- Original: `bruto_de_linea(float(f["can"] or 0), float(f["tar"] or 0))`
- Mutado:   `bruto_de_linea(float(f["can"] or 1), float(f["tar"] or 0))`

#### Análisis

> Por que ningun test lo cazaba: `totales_factura` no se probaba con NULL, ni con descuento menor que 1 %, ilegible o `tot` != can x tar.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r29_tot_e_ivacuo_nulos_suman_cero`. Medido: el mutante cae.

### 57. `application/use_cases/factura_statements.py:194` [entero]

- Original: `bruto_de_linea(float(f["can"] or 0), float(f["tar"] or 0))`
- Mutado:   `bruto_de_linea(float(f["can"] or 0), float(f["tar"] or 1))`

#### Análisis

> Por que ningun test lo cazaba: `totales_factura` no se probaba con NULL, ni con descuento menor que 1 %, ilegible o `tot` != can x tar.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r29_tot_e_ivacuo_nulos_suman_cero`. Medido: el mutante cae.

### 58. `application/use_cases/factura_statements.py:195` [entero]

- Original: `if (porcentaje_de_dto(f["dto"]) or 0) > 0 else d(f["tot"])`
- Mutado:   `if (porcentaje_de_dto(f["dto"]) or 1) > 0 else d(f["tot"])`

#### Análisis

> Por que ningun test lo cazaba: `totales_factura` no se probaba con NULL, ni con descuento menor que 1 %, ilegible o `tot` != can x tar.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r29_tot_e_ivacuo_nulos_suman_cero`. Medido: el mutante cae.

### 59. `application/use_cases/factura_statements.py:195` [comparacion]

- Original: `if (porcentaje_de_dto(f["dto"]) or 0) > 0 else d(f["tot"])`
- Mutado:   `if (porcentaje_de_dto(f["dto"]) or 0) >= 0 else d(f["tot"])`

#### Análisis

> Por que ningun test lo cazaba: `totales_factura` no se probaba con NULL, ni con descuento menor que 1 %, ilegible o `tot` != can x tar.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r29_tot_e_ivacuo_nulos_suman_cero`. Medido: el mutante cae.

### 60. `application/use_cases/factura_statements.py:195` [entero]

- Original: `if (porcentaje_de_dto(f["dto"]) or 0) > 0 else d(f["tot"])`
- Mutado:   `if (porcentaje_de_dto(f["dto"]) or 0) > 1 else d(f["tot"])`

#### Análisis

> Por que ningun test lo cazaba: `totales_factura` no se probaba con NULL, ni con descuento menor que 1 %, ilegible o `tot` != can x tar.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r29_tot_e_ivacuo_nulos_suman_cero`. Medido: el mutante cae.

### 61. `application/use_cases/factura_statements.py:251` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test intentaba modificar los datos internos congelados.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_la_obra_y_la_factura_montada_son_inmutables`. Medido: el mutante cae.

### 62. `application/use_cases/factura_statements.py:539` [entero]

- Original: `uno = _marcadores(1)`
- Mutado:   `uno = _marcadores(2)`

#### Análisis

> Por que ningun test lo cazaba: El recorrido de T15 no comprobaba con cuantos marcadores formatea.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_t15_las_de_in_se_recorren_con_un_marcador`. Medido: el mutante cae.

### 63. `domain/models/factura_models.py:84` [entero]

- Original: `if not 10000101 <= valor <= 99991231:`
- Mutado:   `if not 10000102 <= valor <= 99991231:`

#### Análisis

> Codigo muerto o equivalente: La comprobacion de rango se reescribe como `len(str(valor)) != 8`; sus tres mutantes (`==`, 9, 7) caen, medido.
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 64. `domain/models/factura_models.py:84` [comparacion]

- Original: `if not 10000101 <= valor <= 99991231:`
- Mutado:   `if not 10000101 < valor <= 99991231:`

#### Análisis

> Codigo muerto o equivalente: Tope superior redundante (`date` ya rechaza mes 13+ y ano de cinco cifras): equivalente. La linea se reescribe como `len(str(valor)) != 8` y sus mutantes caen (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 65. `domain/models/factura_models.py:84` [comparacion]

- Original: `if not 10000101 <= valor <= 99991231:`
- Mutado:   `if not 10000101 <= valor < 99991231:`

#### Análisis

> Codigo muerto o equivalente: Tope superior redundante (`date` ya rechaza mes 13+ y ano de cinco cifras): equivalente. La linea se reescribe como `len(str(valor)) != 8` y sus mutantes caen (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 66. `domain/models/factura_models.py:84` [entero]

- Original: `if not 10000101 <= valor <= 99991231:`
- Mutado:   `if not 10000101 <= valor <= 99991232:`

#### Análisis

> Codigo muerto o equivalente: Tope superior redundante (`date` ya rechaza mes 13+ y ano de cinco cifras): equivalente. La linea se reescribe como `len(str(valor)) != 8` y sus mutantes caen (medido).
> Decision: linea quitada o reescrita (medido: el mutante ya no existe).

### 67. `domain/models/factura_models.py:86` [entero]

- Original: `date(valor // 10000, valor // 100 % 100, valor % 100)`
- Mutado:   `date(valor // 10001, valor // 100 % 100, valor % 100)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban fechas validas como el 29 de febrero bisiesto, que distinguen las cuentas de ano, mes y dia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_fecha_en_los_bordes_vale`. Medido: el mutante cae.

### 68. `domain/models/factura_models.py:86` [entero]

- Original: `date(valor // 10000, valor // 100 % 100, valor % 100)`
- Mutado:   `date(valor // 10000, valor // 101 % 100, valor % 100)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban fechas validas como el 29 de febrero bisiesto, que distinguen las cuentas de ano, mes y dia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_fecha_en_los_bordes_vale`. Medido: el mutante cae.

### 69. `domain/models/factura_models.py:86` [entero]

- Original: `date(valor // 10000, valor // 100 % 100, valor % 100)`
- Mutado:   `date(valor // 10000, valor // 100 % 101, valor % 100)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban fechas validas como el 29 de febrero bisiesto, que distinguen las cuentas de ano, mes y dia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_fecha_en_los_bordes_vale`. Medido: el mutante cae.

### 70. `domain/models/factura_models.py:86` [entero]

- Original: `date(valor // 10000, valor // 100 % 100, valor % 100)`
- Mutado:   `date(valor // 10000, valor // 100 % 100, valor % 101)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban fechas validas como el 29 de febrero bisiesto, que distinguen las cuentas de ano, mes y dia.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_fecha_en_los_bordes_vale`. Medido: el mutante cae.

### 71. `domain/models/factura_models.py:97` [entero]

- Original: `linea: int = Field(..., ge=1, strict=True)        # dcapro.ide de la linea de origen`
- Mutado:   `linea: int = Field(..., ge=2, strict=True)        # dcapro.ide de la linea de origen`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los bordes `ge`/`gt` de los numeros.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_bordes_numericos`. Medido: el mutante cae.

### 72. `domain/models/factura_models.py:98` [booleano]

- Original: `canoriori: float = Field(..., strict=True)`
- Mutado:   `canoriori: float = Field(..., strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 73. `domain/models/factura_models.py:99` [booleano]

- Original: `imporiori: float = Field(..., strict=True)`
- Mutado:   `imporiori: float = Field(..., strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 74. `domain/models/factura_models.py:105` [booleano]

- Original: `fecha: int = Field(..., strict=True)`
- Mutado:   `fecha: int = Field(..., strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 75. `domain/models/factura_models.py:123` [booleano]

- Original: `precio: float = Field(..., strict=True)`
- Mutado:   `precio: float = Field(..., strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 76. `domain/models/factura_models.py:124` [entero]

- Original: `iva: str = Field(..., min_length=1, max_length=24)`
- Mutado:   `iva: str = Field(..., min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 77. `domain/models/factura_models.py:125` [entero]

- Original: `producto: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `producto: str | None = Field(default=None, min_length=2, max_length=24)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 78. `domain/models/factura_models.py:125` [entero]

- Original: `producto: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `producto: str | None = Field(default=None, min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 79. `domain/models/factura_models.py:126` [entero]

- Original: `partida: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `partida: str | None = Field(default=None, min_length=2, max_length=24)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 80. `domain/models/factura_models.py:126` [entero]

- Original: `partida: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `partida: str | None = Field(default=None, min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 81. `domain/models/factura_models.py:127` [entero]

- Original: `paride: int | None = Field(default=None, ge=1, strict=True)`
- Mutado:   `paride: int | None = Field(default=None, ge=2, strict=True)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los bordes `ge`/`gt` de los numeros.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_bordes_numericos`. Medido: el mutante cae.

### 82. `domain/models/factura_models.py:127` [booleano]

- Original: `paride: int | None = Field(default=None, ge=1, strict=True)`
- Mutado:   `paride: int | None = Field(default=None, ge=1, strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 83. `domain/models/factura_models.py:128` [entero]

- Original: `unidad: str | None = Field(default=None, max_length=8)`
- Mutado:   `unidad: str | None = Field(default=None, max_length=9)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 84. `domain/models/factura_models.py:129` [entero]

- Original: `cuenta: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `cuenta: str | None = Field(default=None, min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de cuenta y analitica.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_cuenta_y_analitica_frgg`. Medido: el mutante cae.

### 85. `domain/models/factura_models.py:130` [entero]

- Original: `analitica: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `analitica: str | None = Field(default=None, min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de cuenta y analitica.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_cuenta_y_analitica_frgg`. Medido: el mutante cae.

### 86. `domain/models/factura_models.py:134` [entero]

- Original: `database: str = Field(..., min_length=1, max_length=128)`
- Mutado:   `database: str = Field(..., min_length=2, max_length=128)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 87. `domain/models/factura_models.py:134` [entero]

- Original: `database: str = Field(..., min_length=1, max_length=128)`
- Mutado:   `database: str = Field(..., min_length=1, max_length=129)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 88. `domain/models/factura_models.py:135` [entero]

- Original: `usu: str = Field(..., min_length=1, max_length=24)`
- Mutado:   `usu: str = Field(..., min_length=2, max_length=24)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 89. `domain/models/factura_models.py:136` [entero]

- Original: `referencia_externa: str = Field(..., min_length=1, max_length=128)`
- Mutado:   `referencia_externa: str = Field(..., min_length=2, max_length=128)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 90. `domain/models/factura_models.py:138` [entero]

- Original: `cif_proveedor: str = Field(..., min_length=1, max_length=24)`
- Mutado:   `cif_proveedor: str = Field(..., min_length=2, max_length=24)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 91. `domain/models/factura_models.py:138` [entero]

- Original: `cif_proveedor: str = Field(..., min_length=1, max_length=24)`
- Mutado:   `cif_proveedor: str = Field(..., min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 92. `domain/models/factura_models.py:139` [entero]

- Original: `numero_factura: str = Field(..., min_length=1, max_length=128)`
- Mutado:   `numero_factura: str = Field(..., min_length=2, max_length=128)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 93. `domain/models/factura_models.py:141` [entero]

- Original: `cod_obra: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `cod_obra: str | None = Field(default=None, min_length=2, max_length=24)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 94. `domain/models/factura_models.py:141` [entero]

- Original: `cod_obra: str | None = Field(default=None, min_length=1, max_length=24)`
- Mutado:   `cod_obra: str | None = Field(default=None, min_length=1, max_length=25)`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los largos de los textos en sus bordes.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_largos_de_los_textos_en_sus_bordes`. Medido: el mutante cae.

### 95. `domain/models/factura_models.py:147` [booleano]

- Original: `vencimiento_retencion: int | None = Field(default=None, strict=True)`
- Mutado:   `vencimiento_retencion: int | None = Field(default=None, strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 96. `domain/models/factura_models.py:149` [booleano]

- Original: `total_iva: float = Field(..., strict=True)`
- Mutado:   `total_iva: float = Field(..., strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 97. `domain/models/factura_models.py:150` [booleano]

- Original: `total_factura: float = Field(..., strict=True)`
- Mutado:   `total_factura: float = Field(..., strict=False)`

#### Análisis

> Por que ningun test lo cazaba: Ningun test mandaba un numero como texto.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r1_numeros_estrictos`. Medido: el mutante cae.

### 98. `domain/models/factura_models.py:162` [logico]

- Original: `if any(not valor or len(valor) > 24 for valor in recortados):`
- Mutado:   `if any(not valor and len(valor) > 24 for valor in recortados):`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los codigos de origen en 24/25 caracteres ni en blanco.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_codigos_de_origen_de_1_a_24_recortados`. Medido: el mutante cae.

### 99. `domain/models/factura_models.py:162` [comparacion]

- Original: `if any(not valor or len(valor) > 24 for valor in recortados):`
- Mutado:   `if any(not valor or len(valor) >= 24 for valor in recortados):`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los codigos de origen en 24/25 caracteres ni en blanco.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_codigos_de_origen_de_1_a_24_recortados`. Medido: el mutante cae.

### 100. `domain/models/factura_models.py:162` [entero]

- Original: `if any(not valor or len(valor) > 24 for valor in recortados):`
- Mutado:   `if any(not valor or len(valor) > 25 for valor in recortados):`

#### Análisis

> Por que ningun test lo cazaba: No se probaban los codigos de origen en 24/25 caracteres ni en blanco.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r2_codigos_de_origen_de_1_a_24_recortados`. Medido: el mutante cae.

### 101. `function_app.py:471` [comparacion]

- Original: `lineas = exc.details.get("lineas", []) if exc.codigo == "lineas_no_validas" else []`
- Mutado:   `lineas = exc.details.get("lineas", []) if exc.codigo != "lineas_no_validas" else []`

#### Análisis

> Por que ningun test lo cazaba: Ningun test miraba la traza de la ruta con fallos de linea.
> Decision: test nuevo `tests/test_f008_mutantes.py::test_f008_r46_la_ruta_traza_los_codigos_de_cada_linea`. Medido: el mutante cae.

