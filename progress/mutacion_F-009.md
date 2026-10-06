<!-- progress/mutacion_F-009.md -->
# F-009 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-009 --workers 4` el 2026-10-07 00:08.

## Alcance

Origen del diff: **rama** (`2a5ac24ee20932a4063c0008f30f8203f3a1204b` .. `feature/F-009-alta-albaran-compra`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 1040 |
| `application/use_cases/create_albaran_compra_use_case.py` | 1338 |
| `config/settings.py` | 92 |
| `domain/models/albaran_compra_models.py` | 365 |
| `function_app.py` | 94 |
| **Total** | **2929** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 481 |
| Mutantes evaluados | 481 |
| Muertos | 479 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2077.9 s |
| SHA de HEAD medido | `8a858049a5d111b96bd03be562fd709ee3ce1054` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-009_xcx5t5e3/wk_0` | 111.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-009_xcx5t5e3/wk_1` | 109.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-009_xcx5t5e3/wk_2` | 109.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-009_xcx5t5e3/wk_3` | 112.6 |
| Media por mutante evaluado (s) | 4.3 |
| Timeout efectivo por mutante (s) | 226 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/create_albaran_compra_use_case.py:1328` [comparacion]

- Original: `if datos.cantidad > 0 and servido[ide] > pendiente + 1e-9:`
- Mutado:   `if datos.cantidad >= 0 and servido[ide] > pendiente + 1e-9:`

#### Análisis

> **Equivalente, demostrado midiendo.** El mutante solo difiere del original con `cantidad == 0`, y
> `LineaAlbaranIn._reglas_de_linea` rechaza esa cantidad antes de que la petición exista (test
> `test_f009_models.py`, casos `cantidad=0` y `cantidad=0.0`). Evidencia ejecutada:
> 1. Reevaluado **en serie** (`workers=1`, worktree de `8a85804`, suite entera): sobrevive.
> 2. Diferencial original frente a mutante sobre **5.000 peticiones válidas** generadas al azar (1 a 5
>    vinculadas, cantidades enteras, decimales y en frontera, `canser` NULL/0/variable, previa y commit):
>    **0 diferencias** en la respuesta completa (`model_dump`) o en el error.
> 3. Control negativo del diferencial: la misma línea con `cantidad` 0 colada con `model_construct`
>    (saltándose el modelo) hace diferir **75 de 200** respuestas: el diferencial sí ve la diferencia
>    cuando existe.
> Sin código que quitar: la comparación es necesaria (separa positivas de devoluciones). Detalle y
> comandos en `progress/impl_F-009_loteE_mutacion.md`.

### 2. `application/use_cases/create_albaran_compra_use_case.py:1333` [comparacion]

- Original: `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:`
- Mutado:   `if datos.cantidad <= 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:`

#### Análisis

> **Equivalente, demostrado midiendo.** El mutante solo difiere del original con `cantidad == 0`, y
> `LineaAlbaranIn._reglas_de_linea` rechaza esa cantidad antes de que la petición exista (test
> `test_f009_models.py`, casos `cantidad=0` y `cantidad=0.0`). Evidencia ejecutada:
> 1. Reevaluado **en serie** (`workers=1`, worktree de `8a85804`, suite entera): sobrevive.
> 2. Diferencial original frente a mutante sobre **5.000 peticiones válidas** generadas al azar (1 a 5
>    vinculadas, cantidades enteras, decimales y en frontera, `canser` NULL/0/variable, previa y commit):
>    **0 diferencias** en la respuesta completa (`model_dump`) o en el error.
> 3. Control negativo del diferencial: la misma línea con `cantidad` 0 colada con `model_construct`
>    (saltándose el modelo) hace diferir **74 de 200** respuestas: el diferencial sí ve la diferencia
>    cuando existe.
> Sin código que quitar: la comparación es necesaria (separa positivas de devoluciones). Detalle y
> comandos en `progress/impl_F-009_loteE_mutacion.md`.



---

> **De dónde salen esos 2** (añadido por el implementer, T16). Esta campaña, sobre `8a85804`, es la que vale.
> Antes hubo otras tres ejecuciones; ninguna se da por buena:
>
> 1. Sobre `ebb0ddc`: **abortada sin informe** (exit 2) por un fichero vacío sin versionar en la raíz
>    (`` `0`].{t ``, del 24-09, ajeno a F-009). Se apartó al scratchpad durante T16 y se repuso al final.
> 2. Sobre `ebb0ddc`: **abortada, línea base roja** (exit 3): `test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho`
>    `[sql_read]`/`[sql_write]` construían `Settings` reales (vía `SqlReadRequest`/`SqlWriteRequest`) y con el `.env`
>    volcado al entorno fallaban. Lección 4. Arreglado en `92bf606` (se dobla `get_settings` de `sql_models`); RED y
>    verde en `progress/impl_F-009_loteE_mutacion.md`.
> 3. Sobre `92bf606`, **4 workers**: 494 mutantes, 418 muertos, **76 supervivientes**, 3.545,3 s. Los 76 se
>    **reevaluaron en serie** (`workers=1`, worktree de `92bf606`, `ejecutar_campania(mutantes=...)`, 5.884,2 s):
>    **76 supervivientes también en serie**, ningún falso superviviente esta vez. Desenlace de los 76:
>    - **60 muertos con tests nuevos** (`tests/test_f009_mutacion.py`, commit `db945d6`), fase RED en la tabla de abajo.
>    - **14 eran código que nadie lee o comprobaciones inalcanzables**, quitados en `8a85804` (sin cambio de
>      comportamiento): n.º 9, 11, 17, 18, 19 (defectos `0` de `natide`, `cueide`, `caaide`, `tipmov`, `ivaide` de
>      `_Linea`), 47, 48 (`paride=0` de relleno), 30 (`ctride ... else 0`), 39 (`ide_log=0` previo a E11b), 46, 50
>      (`almacen_sin_vincular or (0, 0)`), 6, 34, 37 (`zip(..., strict=True)` sobre listas alineadas por
>      construcción). Canario y control negativo de cada uno en el informe del implementer; RM6 para los `strict`.
>    - **2 equivalentes** (n.º 60 y 61), los dos supervivientes de esta campaña, con la demostración de arriba.
>
> 494 → 481 mutantes: 15 sitios de mutación desaparecen con el código quitado y entran 2 (el `is not None` del
> `assert` del almacén y el `[0]` de `ctride` tras la guarda), ambos muertos.
>
> Coste por mutante (CHECKPOINTS) = 2.077,9 s × 4 workers ÷ 481 = **17,3 s**; RM2: media 4,3 s × 4 = 17,3 s frente a
> una línea base de 109-113 s: por debajo porque `-x` corta en el primer fallo y 479 de 481 mueren, sin salto de
> orden de magnitud (> 1/10 de la base).

### Fase RED de los 76 supervivientes de la campaña 3 (`92bf606`)

Cada fila: el mutante aplicado tal cual en un worktree de `92bf606` con `tests/test_f009_mutacion.py` copiado, y
`python -m pytest -q --tb=no -p no:cacheprovider tests/test_f009_mutacion.py -rf` (salida real resumida). Con el
original, `31 passed`. «31 passed» en una fila = el test no lo mata: son los 14 quitados y los 2 equivalentes.

| N.º | Sitio | Original → mutado | Resultado con el mutante | Test que cae |
|---|---|---|---|---|
| 1 | `albaran_compra_statements.py:284` [comparacion] | `if abs(almcan) < EPSILON_STOCK:` → `if abs(almcan) <= EPSILON_STOCK:` | 1 failed, 30 passed | r19_el_epsilon_del_stock_es_estricto |
| 2 | `albaran_compra_statements.py:330` [entero] | `return round(float(valor or 0), 2)` → `return round(float(valor or 1), 2)` | 1 failed, 30 passed | r15_caaide_null_del_ctrpro_es_cero_y_sin_seguimiento_de_origen |
| 3 | `albaran_compra_statements.py:534` [entero] | `if usa_precio_del_contrato(cantidad, precio, ctrpro.get("pre") or 0):` → `if usa_precio_del_contrato(cantidad, precio, ctrpro.get("pre") or 1):` | 1 failed, 30 passed | r17_precio_null_del_ctrpro_es_cero_y_coincide_con_precio_cero |
| 4 | `albaran_compra_statements.py:535` [entero] | `pre = float(ctrpro.get("pre") or 0)` → `pre = float(ctrpro.get("pre") or 1)` | 1 failed, 30 passed | r17_precio_null_del_ctrpro_es_cero_y_coincide_con_precio_cero |
| 5 | `albaran_compra_statements.py:558` [entero] | `"caaide": ctrpro.get("caaide") or 0,` → `"caaide": ctrpro.get("caaide") or 1,` | 1 failed, 30 passed | r15_caaide_null_del_ctrpro_es_cero_y_sin_seguimiento_de_origen |
| 6 | `albaran_compra_statements.py:773` [booleano] | `for ide, fila in zip(ides_dcapro, filas.dcapro, strict=True)` → `for ide, fila in zip(ides_dcapro, filas.dcapro, strict=False)` | 31 passed | — |
| 7 | `create_albaran_compra_use_case.py:102` [booleano] | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | 1 failed, 30 passed | r27_las_filas_y_los_datos_de_un_intento_son_inmutables |
| 8 | `albaran_compra_statements.py:720` [booleano] | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | 1 failed, 30 passed | r27_las_filas_y_los_datos_de_un_intento_son_inmutables |
| 9 | `create_albaran_compra_use_case.py:158` [entero] | `cueide: int = 0` → `cueide: int = 1` | 31 passed | — |
| 10 | `albaran_compra_statements.py:815` [entero] | `uno = _marcadores(1)` → `uno = _marcadores(2)` | 1 failed, 30 passed | r31_todas_las_sentencias_validan_los_in_con_un_solo_marcador |
| 11 | `create_albaran_compra_use_case.py:160` [entero] | `tipmov: int = 0` → `tipmov: int = 1` | 31 passed | — |
| 12 | `create_albaran_compra_use_case.py:240` [entero] | `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)` → `traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 2)` | 1 failed, 30 passed | r32_duracion_con_un_decimal_y_textos_sin_escapar |
| 13 | `albaran_compra_statements.py:991` [logico] | `if set(fila) != set(columnas) or len(fila) != len(columnas):` → `if set(fila) != set(columnas) and len(fila) != len(columnas):` | 1 failed, 30 passed | r25_la_fila_fija_con_una_columna_cambiada_se_rechaza_con_su_nombre |
| 14 | `create_albaran_compra_use_case.py:109` [booleano] | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | 1 failed, 30 passed | r27_las_filas_y_los_datos_de_un_intento_son_inmutables |
| 15 | `create_albaran_compra_use_case.py:256` [booleano] | `request, sentencias.leer_lineas_de_albaran(int(existente[0])), muchas=True` → `request, sentencias.leer_lineas_de_albaran(int(existente[0])), muchas=False` | 1 failed, 30 passed | r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no |
| 16 | `create_albaran_compra_use_case.py:88` [entero] | `return round(float(valor or 0), 2)` → `return round(float(valor or 0), 3)` | 1 failed, 30 passed | r20_sumas_previstas_redondeadas_a_dos_decimales |
| 17 | `create_albaran_compra_use_case.py:157` [entero] | `natide: int = 0` → `natide: int = 1` | 31 passed | — |
| 18 | `create_albaran_compra_use_case.py:162` [entero] | `ivaide: int = 0` → `ivaide: int = 1` | 31 passed | — |
| 19 | `create_albaran_compra_use_case.py:159` [entero] | `caaide: int = 0` → `caaide: int = 1` | 31 passed | — |
| 20 | `create_albaran_compra_use_case.py:508` [entero] | `cantidad=float(can or 0),` → `cantidad=float(can or 1),` | 1 failed, 30 passed | r30_idempotente_con_nulos_en_lo_leido |
| 21 | `create_albaran_compra_use_case.py:175` [booleano] | `@dataclass(frozen=True)` → `@dataclass(frozen=False)` | 1 failed, 30 passed | r27_las_filas_y_los_datos_de_un_intento_son_inmutables |
| 22 | `create_albaran_compra_use_case.py:241` [booleano] | `logger.info(json.dumps(traza, ensure_ascii=False, default=str))` → `logger.info(json.dumps(traza, ensure_ascii=True, default=str))` | 1 failed, 30 passed | r32_duracion_con_un_decimal_y_textos_sin_escapar |
| 23 | `create_albaran_compra_use_case.py:509` [entero] | `precio=float(pre or 0),` → `precio=float(pre or 1),` | 1 failed, 30 passed | r30_idempotente_con_nulos_en_lo_leido |
| 24 | `create_albaran_compra_use_case.py:510` [entero] | `total=float(tot or 0),` → `total=float(tot or 1),` | 1 failed, 30 passed | r30_idempotente_con_nulos_en_lo_leido |
| 25 | `create_albaran_compra_use_case.py:282` [logico] | `f"({', '.join(prefijos) or 'ninguno configurado'}).",` → `f"({', '.join(prefijos) and 'ninguno configurado'}).",` | 1 failed, 30 passed | r29_el_mensaje_nombra_los_prefijos_o_que_no_hay |
| 26 | `create_albaran_compra_use_case.py:517` [entero] | `totales={"totbas": float(totbas or 0), "totdoc": float(totdoc or 0),` → `totales={"totbas": float(totbas or 1), "totdoc": float(totdoc or 0),` | 1 failed, 30 passed | r30_idempotente_con_nulos_en_lo_leido |
| 27 | `create_albaran_compra_use_case.py:313` [booleano] | `muchas: bool = False,` → `muchas: bool = True,` | 1 failed, 30 passed | r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no |
| 28 | `create_albaran_compra_use_case.py:517` [entero] | `totales={"totbas": float(totbas or 0), "totdoc": float(totdoc or 0),` → `totales={"totbas": float(totbas or 0), "totdoc": float(totdoc or 1),` | 1 failed, 30 passed | r30_idempotente_con_nulos_en_lo_leido |
| 29 | `create_albaran_compra_use_case.py:564` [entero] | `vigentes[(proide, almide)] = (float(fila[0] or 0), float(fila[1] or 0))` → `vigentes[(proide, almide)] = (float(fila[0] or 0), float(fila[1] or 1))` | 1 failed, 30 passed | r19_balance_vigente_con_nulos_es_cero_en_previa_y_en_commit |
| 30 | `create_albaran_compra_use_case.py:444` [entero] | `ctride = int(de_la_obra[0]["ide"]) if de_la_obra else 0` → `ctride = int(de_la_obra[0]["ide"]) if de_la_obra else 1` | 31 passed | — |
| 31 | `create_albaran_compra_use_case.py:680` [entero] | `if linea.precio < 0:` → `if linea.precio < 1:` | 2 failed, 29 passed | r17_precio_null_del_ctrpro_y_precio_cero_no_avisan, r17_precio_cero_es_valido |
| 32 | `create_albaran_compra_use_case.py:479` [entero] | `f"{', '.join(str(f[1]).strip() for f in filas)}.",` → `f"{', '.join(str(f[2]).strip() for f in filas)}.",` | 1 failed, 30 passed | r30_el_conflicto_nombra_los_cod_de_los_albaranes |
| 33 | `create_albaran_compra_use_case.py:718` [booleano] | `request, sentencias.leer_almacenes(cabecera.obra.ide, []), muchas=True` → `request, sentencias.leer_almacenes(cabecera.obra.ide, []), muchas=False` | 1 failed, 30 passed | r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no |
| 34 | `create_albaran_compra_use_case.py:840` [booleano] | `balances={linea.indice: b for linea, b in zip(con_mov, balances, strict=True)},` → `balances={linea.indice: b for linea, b in zip(con_mov, balances, strict=False)},` | 31 passed | — |
| 35 | `create_albaran_compra_use_case.py:564` [entero] | `vigentes[(proide, almide)] = (float(fila[0] or 0), float(fila[1] or 0))` → `vigentes[(proide, almide)] = (float(fila[0] or 1), float(fila[1] or 0))` | 1 failed, 30 passed | r19_balance_vigente_con_nulos_es_cero_en_previa_y_en_commit |
| 36 | `create_albaran_compra_use_case.py:590` [entero] | `cabecera.contrato.fila, float(suma_can or 0), float(suma_canser or 0),` → `cabecera.contrato.fila, float(suma_can or 1), float(suma_canser or 0),` | 1 failed, 30 passed | r20_sumas_null_del_contrato_en_el_commit |
| 37 | `create_albaran_compra_use_case.py:799` [booleano] | `for linea, balance in zip(con_mov, balances, strict=True):` → `for linea, balance in zip(con_mov, balances, strict=False):` | 31 passed | — |
| 38 | `create_albaran_compra_use_case.py:864` [entero] | `vigentes[(proide, almide)] = (float(filas[0][0] or 0), float(filas[0][1] or 0))` → `vigentes[(proide, almide)] = (float(filas[0][0] or 1), float(filas[0][1] or 0))` | 1 failed, 30 passed | r19_balance_vigente_con_nulos_es_cero_en_previa_y_en_commit |
| 39 | `create_albaran_compra_use_case.py:568` [entero] | `ide_ctrprodes=ide_ctrprodes, ide_mov=ide_mov, ide_log=0,` → `ide_ctrprodes=ide_ctrprodes, ide_mov=ide_mov, ide_log=1,` | 31 passed | — |
| 40 | `create_albaran_compra_use_case.py:864` [entero] | `vigentes[(proide, almide)] = (float(filas[0][0] or 0), float(filas[0][1] or 0))` → `vigentes[(proide, almide)] = (float(filas[0][0] or 0), float(filas[0][1] or 1))` | 1 failed, 30 passed | r19_balance_vigente_con_nulos_es_cero_en_previa_y_en_commit |
| 41 | `create_albaran_compra_use_case.py:902` [logico] | `suma_canfac = sum(float(l.get("canfac") or 0) for l in contrato.lineas.values())` → `suma_canfac = sum(float(l.get("canfac") and 0) for l in contrato.lineas.values())` | 1 failed, 30 passed | r20_sumas_previstas_con_can_null_y_con_facturado |
| 42 | `create_albaran_compra_use_case.py:590` [entero] | `cabecera.contrato.fila, float(suma_can or 0), float(suma_canser or 0),` → `cabecera.contrato.fila, float(suma_can or 0), float(suma_canser or 1),` | 1 failed, 30 passed | r20_sumas_null_del_contrato_en_el_commit |
| 43 | `create_albaran_compra_use_case.py:775` [logico] | `descripcion=datos.descripcion or "",` → `descripcion=datos.descripcion and "",` | 1 failed, 30 passed | r13_la_sin_vincular_escribe_su_descripcion |
| 44 | `create_albaran_compra_use_case.py:680` [comparacion] | `if linea.precio < 0:` → `if linea.precio <= 0:` | 2 failed, 29 passed | r17_precio_null_del_ctrpro_y_precio_cero_no_avisan, r17_precio_cero_es_valido |
| 45 | `create_albaran_compra_use_case.py:900` [entero] | `suma_can = sum(float(l.get("can") or 0) for l in contrato.lineas.values())` → `suma_can = sum(float(l.get("can") or 1) for l in contrato.lineas.values())` | 1 failed, 30 passed | r20_sumas_previstas_con_can_null_y_con_facturado |
| 46 | `create_albaran_compra_use_case.py:1172` [entero] | `almide, cenide = self._cab.almacen_sin_vincular or (0, 0)` → `almide, cenide = self._cab.almacen_sin_vincular or (1, 0)` | 31 passed | — |
| 47 | `create_albaran_compra_use_case.py:1138` [entero] | `paride=0,` → `paride=1,` | 31 passed | — |
| 48 | `create_albaran_compra_use_case.py:1179` [entero] | `paride=0,` → `paride=1,` | 31 passed | — |
| 49 | `create_albaran_compra_use_case.py:1066` [booleano] | `_c, filas = self._caso._leer(self._request, metodo(*argumentos), muchas=True)` → `_c, filas = self._caso._leer(self._request, metodo(*argumentos), muchas=False)` | 1 failed, 30 passed | r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no |
| 50 | `create_albaran_compra_use_case.py:1172` [entero] | `almide, cenide = self._cab.almacen_sin_vincular or (0, 0)` → `almide, cenide = self._cab.almacen_sin_vincular or (0, 1)` | 31 passed | — |
| 51 | `create_albaran_compra_use_case.py:1321` [entero] | `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` → `if datos.cantidad < 1 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` | 1 failed, 30 passed | r18_una_positiva_tras_una_devolucion_no_avisa_servido_negativo |
| 52 | `create_albaran_compra_use_case.py:1228` [booleano] | `_c, filas = caso._leer(request, s.leer_tipmov(proides), muchas=True)` → `_c, filas = caso._leer(request, s.leer_tipmov(proides), muchas=False)` | 1 failed, 30 passed | r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no |
| 53 | `create_albaran_compra_use_case.py:1240` [booleano] | `_c, filas = caso._leer(request, s.leer_tasas_iva(ivaides), muchas=True)` → `_c, filas = caso._leer(request, s.leer_tasas_iva(ivaides), muchas=False)` | 1 failed, 30 passed | r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no |
| 54 | `create_albaran_compra_use_case.py:1241` [entero] | `tasas = {int(f[0]): float(f[1] or 0) for f in filas}` → `tasas = {int(f[0]): float(f[1] or 1) for f in filas}` | 1 failed, 30 passed | r17_iva_null_es_tasa_cero |
| 55 | `create_albaran_compra_use_case.py:1308` [entero] | `if not usa_precio_del_contrato(datos.cantidad, datos.precio, ctrpro.get("pre") or 0):` → `if not usa_precio_del_contrato(datos.cantidad, datos.precio, ctrpro.get("pre") or 1):` | 1 failed, 30 passed | r17_precio_null_del_ctrpro_y_precio_cero_no_avisan |
| 56 | `albaran_compra_models.py:219` [entero] | `partida: str \| None = Field(default=None, min_length=1, max_length=24)   # None: sin partida` → `partida: str \| None = Field(default=None, min_length=2, max_length=24)   # None: sin partida` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 57 | `create_albaran_compra_use_case.py:1231` [entero] | `linea.tipmov = tipmov.get(linea.proide, 0)` → `linea.tipmov = tipmov.get(linea.proide, 1)` | 1 failed, 30 passed | r19_producto_sin_fila_en_pro_no_lleva_mov |
| 58 | `create_albaran_compra_use_case.py:1316` [entero] | `if datos.cantidad > 0 and servido[ide] > pendiente + 1e-9:` → `if datos.cantidad > 1 and servido[ide] > pendiente + 1e-9:` | 1 failed, 30 passed | r18_supera_pendiente_tambien_con_cantidades_menores_que_uno |
| 59 | `albaran_compra_models.py:261` [entero] | `database: str = Field(..., min_length=1)` → `database: str = Field(..., min_length=2)` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 60 | `create_albaran_compra_use_case.py:1316` [comparacion] | `if datos.cantidad > 0 and servido[ide] > pendiente + 1e-9:` → `if datos.cantidad >= 0 and servido[ide] > pendiente + 1e-9:` | 31 passed | — |
| 61 | `create_albaran_compra_use_case.py:1321` [comparacion] | `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` → `if datos.cantidad <= 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` | 31 passed | — |
| 62 | `create_albaran_compra_use_case.py:1316` [aritmetico] | `if datos.cantidad > 0 and servido[ide] > pendiente + 1e-9:` → `if datos.cantidad > 0 and servido[ide] > pendiente - 1e-9:` | 1 failed, 30 passed | r18_servir_exactamente_lo_pendiente_no_avisa |
| 63 | `create_albaran_compra_use_case.py:1316` [comparacion] | `if datos.cantidad > 0 and servido[ide] > pendiente + 1e-9:` → `if datos.cantidad > 0 and servido[ide] >= pendiente + 1e-9:` | 1 failed, 30 passed | r18_servir_exactamente_lo_pendiente_no_avisa |
| 64 | `create_albaran_compra_use_case.py:1321` [entero] | `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` → `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 1) + servido[ide]) < 0:` | 1 failed, 30 passed | r18_servido_negativo_con_canser_null_y_en_la_frontera |
| 65 | `create_albaran_compra_use_case.py:1321` [entero] | `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` → `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 1:` | 1 failed, 30 passed | r18_servido_negativo_con_canser_null_y_en_la_frontera |
| 66 | `create_albaran_compra_use_case.py:1326` [entero] | `linea.avisos[:0] = propios` → `linea.avisos[:1] = propios` | 1 failed, 30 passed | r16_los_avisos_del_contrato_van_delante_de_los_de_la_plantilla |
| 67 | `create_albaran_compra_use_case.py:1321` [comparacion] | `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:` → `if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) <= 0:` | 1 failed, 30 passed | r18_servido_negativo_con_canser_null_y_en_la_frontera |
| 68 | `albaran_compra_models.py:214` [entero] | `producto: str \| None = Field(default=None, min_length=1, max_length=24)  # sin vincular` → `producto: str \| None = Field(default=None, min_length=2, max_length=24)  # sin vincular` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 69 | `albaran_compra_models.py:220` [booleano] | `paride: int \| None = Field(default=None, ge=1, strict=True)              # R14b; exige partida` → `paride: int \| None = Field(default=None, ge=1, strict=False)              # R14b; exige partida` | 1 failed, 30 passed | r14b_paride_como_texto_no_cuela |
| 70 | `albaran_compra_models.py:262` [entero] | `cod_obra: str = Field(..., min_length=1, max_length=24)` → `cod_obra: str = Field(..., min_length=2, max_length=24)` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 71 | `albaran_compra_models.py:220` [entero] | `paride: int \| None = Field(default=None, ge=1, strict=True)              # R14b; exige partida` → `paride: int \| None = Field(default=None, ge=2, strict=True)              # R14b; exige partida` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 72 | `albaran_compra_models.py:263` [entero] | `usu: str = Field(..., min_length=1, max_length=24)                       # dbo.usu.cod` → `log.usu -> usu: str = Field(..., min_length=2, max_length=24)                       # dbo.usu.cod -> log.usu` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 73 | `albaran_compra_models.py:264` [entero] | `cif_proveedor: str = Field(..., min_length=1, max_length=24)             # H21` → `cif_proveedor: str = Field(..., min_length=2, max_length=24)             # H21` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 74 | `albaran_compra_models.py:265` [entero] | `referencia_externa: str = Field(..., min_length=1, max_length=128)       # dca.synckey` → `referencia_externa: str = Field(..., min_length=2, max_length=128)       # dca.synckey` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 75 | `albaran_compra_models.py:266` [entero] | `cod_contrato: str \| None = Field(default=None, min_length=1, max_length=24)` → `cod_contrato: str \| None = Field(default=None, min_length=2, max_length=24)` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
| 76 | `albaran_compra_models.py:269` [entero] | `empide: int \| None = Field(default=None, ge=1, strict=True)` → `empide: int \| None = Field(default=None, ge=2, strict=True)` | 1 failed, 30 passed | r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero |
