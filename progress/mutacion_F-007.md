<!-- progress/mutacion_F-007.md -->
# F-007 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-007 --workers 1` el 2026-10-26 19:53.

## Alcance

Origen del diff: **rama** (`60db95586ce144d70d7c08e3640da397842c8383` .. `feature/F-007-registrar-proforma`).

| Fichero | Líneas en alcance |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | 12 |
| `application/use_cases/create_albaran_compra_use_case.py` | 176 |
| `application/use_cases/create_proforma_use_case.py` | 478 |
| `application/use_cases/proforma_statements.py` | 721 |
| `config/settings.py` | 27 |
| `domain/models/albaran_compra_models.py` | 14 |
| `domain/models/proforma_models.py` | 301 |
| `function_app.py` | 69 |
| `interface_adapters/http/http_response_factory.py` | 3 |
| **Total** | **1801** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 381 |
| Mutantes evaluados | 381 |
| Muertos | 376 |
| Supervivientes | 5 |
| Timeouts | 0 |
| Timeouts repasados en serie | 0: ningún mutante agotó el reloj |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4674.3 s |
| SHA de HEAD medido | `4a94da0bb7b114ed9234a0ab2e7d40a848a2e8fe` |
| Línea base (s) — `.` | 79.5 |
| Media por mutante evaluado (s) | 12.3 |
| Timeout efectivo por mutante (s) | 159 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `application/use_cases/albaran_compra_statements.py:331` [entero]

- Original: `def siguiente_cod(prefijo: str, maximo: int | None, *, cifras: int = 0) -> str:`
- Mutado:   `def siguiente_cod(prefijo: str, maximo: int | None, *, cifras: int = 1) -> str:`

#### Análisis (implementer)

> Por qué ningún test lo caza: **equivalente**. `str(n).zfill(0)` y `str(n).zfill(1)` dan lo mismo para cualquier
> entero (`str` nunca es vacío). El defecto `0` existe para que las llamadas de F-009 sin `cifras` sigan iguales
> (`tests/test_f009_statements.py::test_f009_r26_siguiente_cod` lo llama así y es intocable, R31); las dos del núcleo
> pasan `cifras=self.perfil.cifras_serie`.
> **Medido**: aplicado a mano en un worktree desechable, la suite entera en verde (`3297 passed, 1 skipped`, exit 0,
> 85,8 s, ronda 1). Decisión: **mutante equivalente, justificado para el humano**. No es código muerto: quitar el
> defecto rompe la firma que usa el test intocable de F-009.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 2. `application/use_cases/create_albaran_compra_use_case.py:1591` [entero]

- Original: `linea.plantilla = {**dict.fromkeys(_DCAPRO_SIN_PLANTILLA, 0), "ivaide": linea.ivaide}`
- Mutado:   `linea.plantilla = {**dict.fromkeys(_DCAPRO_SIN_PLANTILLA, 1), "ivaide": linea.ivaide}`

#### Análisis (implementer)

> Por qué ningún test lo caza: **hueco real del test** (código nuevo de D1, T28). La rama sin plantilla de
> `_de_la_plantilla_del_contrato` pone la base de una sin vincular sin histórico (`_DCAPRO_SIN_PLANTILLA` a 0); el
> test de T28 comparaba solo las **claves** de la fila con las del albarán, no los valores: con `1`, `envide`,
> `reqcuo`, `lintip`, `taride` y `cuoman` salían a 1 en el `dcapro` sin que nada lo viera.
> Decisión: **test nuevo** `test_f007_t32_sin_historico_las_columnas_de_la_sin_plantilla_salen_como_en_el_albaran`
> (`tests/test_f007_perfil.py`): esas cinco columnas, iguales a las del albarán sin histórico y a 0; cuenta y
> naturaleza a 0. Fase ROJA con el mutante aplicado en el worktree: `E AssertionError: assert {'envide': 1,...ride':
> 0, ...} == {'envide': 0,...ride': 0, ...}` (`test_f007_perfil.py:501`) → `1 failed, 41 passed`.

### 3. `application/use_cases/create_proforma_use_case.py:335` [entero]

- Original: `request, sentencias.leer_lineas_de_albaran(int(filas[0][0])), muchas=True`
- Mutado:   `request, sentencias.leer_lineas_de_albaran(int(filas[1][0])), muchas=True`

#### Análisis (implementer)

> Por qué ningún test lo caza: **falso superviviente de la herramienta**. Con una sola fila de L11 (la línea de
> antes lo exige), `filas[1]` es un `IndexError`. **Medido** a mano en el worktree `../sigrid-api-mut007-p1`
> (HEAD `4a94da0`, suite F-007 + F-009 + F-015, base `1327 passed`): **muere**, `3 failed, 1324 passed`
> (`test_f007_r23_misma_referencia_de_proforma_del_contrato_es_idempotente[False]` y `[True]`,
> `test_f007_t18_las_lineas_del_idempotente_piden_el_tope_de_filas`). Ya moría en la ronda 2.
> Decisión: sin cambio; anotado para `arnes-base` (abajo).

### 4. `application/use_cases/create_proforma_use_case.py:354` [booleano]

- Original: `_c, filas = self._leer(request, lecturas.leer_lineas_de_proforma(proforma.ide), muchas=True)`
- Mutado:   `_c, filas = self._leer(request, lecturas.leer_lineas_de_proforma(proforma.ide), muchas=False)`

#### Análisis (implementer)

> Por qué ningún test lo caza: **falso superviviente de la herramienta**. **Medido** a mano en el mismo worktree:
> **muere**, `1 failed, 1326 passed` (`test_f007_t18_las_lecturas_de_muchas_filas_piden_el_tope_de_filas`, que pide
> `max_allowed_rows` a cada lectura de muchas filas, LP6 incluida). Ya moría en la ronda 2.
> Decisión: sin cambio; anotado para `arnes-base` (abajo).

### 5. `application/use_cases/create_proforma_use_case.py:380` [logico]

- Original: `assert isinstance(request, _AltaDeProforma) and request._contexto is not None`
- Mutado:   `assert isinstance(request, _AltaDeProforma) or request._contexto is not None`

#### Análisis (implementer)

> Por qué ningún test lo caza: **equivalente** (medido: `1327 passed` con el mutante). La guarda de tipos de
> `_resolver_contrato` (T33) une dos condiciones que en todo camino real son ciertas a la vez (el caso de uso siempre
> le pasa un `_AltaDeProforma` con su contexto); con `or`, un contexto vacío fallaría igual una línea después.
> Decisión: **reescrita** como dos `assert` (una por condición; las dos sirven a mypy), commit de T32. Sus mutantes
> (`is None` por `is not None`, `not isinstance`) **mueren** a mano: `40 failed, 38 passed` en
> `test_f007_use_case.py` + `test_f007_transaccion.py`.
> Lo mismo en `_comprobar_dentro`: su `if contexto is None: return` era **código muerto** (el caso de uso siempre
> pone el contexto antes de llamar al núcleo; la puerta de cobertura lo vio sin cubrir) y pasa a las mismas dos
> guardas. Sus mutantes mueren a mano: `21 failed, 57 passed` en esos dos ficheros.

## Análisis (implementer)

**Estado final: 0 supervivientes no aceptados.** Pasada 1 (HEAD `4a94da0`, 381 mutantes, 376 muertos, 5
supervivientes): el equivalente `cifras: int = 0` (§1) —**el equivalente `cifras: int = 0` lo aceptó por escrito el
humano el 2026-10-26**—; un hueco real cazado con un test nuevo (§2); dos falsos supervivientes de la herramienta que
mueren a mano (§3, §4); y una guarda equivalente reescrita para que cada condición se pueda matar (§5). Después de la
campaña solo cambiaron ese test y esa guarda (commit de T32), y sus mutantes se midieron a mano.

**Falsos supervivientes en serie** (tercera vez en F-007, tras el `% 101` de la ronda 1): §3 y §4 mueren en 13 s
con la suite de F-007, F-009 y F-015 en un worktree. Para `arnes-base`: la campaña en serie también declara
supervivientes que no lo son (sin diagnosticar; pista ya anotada: el veredicto con `exit 5` o con una selección de
tests que no incluye los que lo matan).

**Rondas anteriores**: ronda 1 (`a3acbd7`), 375 / 67; ronda 2 (`7cbff6b`), 374 / 2. Detalle de su resolución en
`progress/impl_F-007.md` §T18 y en el historial de este fichero (`git log -p progress/mutacion_F-007.md`).

## Mutantes manuales reproducibles (T36)

Ficheros con ≤ 2 mutantes automáticos (`domain/models/albaran_compra_models.py` 0, `config/settings.py` 2) y el
`setdefault` de N7. Medidos en el worktree desechable `../sigrid-api-mut007-p1` (HEAD `4a94da0`, **nunca** en el
árbol compartido; borrado al acabar) con `python -m pytest tests/test_f007_*.py tests/test_f009_*.py
tests/test_f015_*.py -q --tb=no -p no:cacheprovider -rf`; base `1327 passed`. Cada uno: sustitución **exacta** del
texto (que aparece una sola vez), suite y `git checkout --` del fichero. **11 de 11 mueren.**

| Id | Fichero:línea | Original → mutado | Resultado (primer test que cae) |
|---|---|---|---|
| N7 | `application/use_cases/create_albaran_compra_use_case.py:1325` | `por_proide.setdefault(_entero(ctrpro.get("proide")), ctrpro)` → `por_proide[_entero(ctrpro.get("proide"))] = ctrpro` | 1 failed (`test_f007_r17_dos_lineas_del_contrato_con_el_producto_el_iva_es_el_de_la_primera_por_pos`) |
| A1 | `domain/models/albaran_compra_models.py:64` | tras `"linea_no_es_del_contrato",` se añade `"linea_ambigua",` (código de proforma en `CODIGOS_LINEA`) | 2 failed (`test_f007_r6_los_nuevos_no_entran_en_los_conjuntos_de_albaranes`) |
| A2 | `domain/models/albaran_compra_models.py:36` | entre `"peticion_mixta",` y `"escritura_albaranes_deshabilitada",` se añade `"proforma_del_mes_existente",` | 1 failed (`test_f009_r9_codigos_cerrados_de_design`) |
| A3 | `domain/models/albaran_compra_models.py:136` | en `_codigo_de_linea`, `if value not in cls.codigos:` → `if value not in CODIGOS_LINEA:` | 8 failed (`test_f007_r6_lineas_no_validas_con_candidatos`) |
| A4 | `domain/models/albaran_compra_models.py:158` | `if codigo not in type(self).codigos:` → `if codigo not in CODIGOS_CABECERA:` | 38 failed (`test_f007_r6_proforma_error_es_un_error_de_albaran`) |
| A5 | `domain/models/albaran_compra_models.py:330` | en `_codigo_de_aviso`, `if value not in cls.codigos:` → `if value not in CODIGOS_AVISO:` | 49 failed (`test_f007_r6_avisos_de_proforma[contrato_a_origen]`) |
| S1 | `config/settings.py:141` | `Field(False, alias="SIGRID_PROFORMA_WRITE_ENABLED")` → `Field(True, alias="SIGRID_PROFORMA_WRITE_ENABLED")` | 1 failed (`test_f007_r4_los_cinco_ajustes_arrancan_con_defecto_cerrado`) |
| S2 | `config/settings.py:167` | se quita `"sigrid_proforma_prefijos_referencia",` de los campos de `parse_string_list` | 4 failed (`test_f007_r4_las_listas_usan_parse_string_list[...]`) |
| S3 | `config/settings.py:253` | se quita `"sigrid_proforma_naturaleza_por_producto",` de los campos de `parse_string_dict` | 8 failed (`test_f007_r4_los_valores_de_despliegue_llegan_por_el_entorno`) |
| S4 | `config/settings.py:152` | `Field(500, alias="SIGRID_PROFORMA_MAX_LINEAS")` → `Field(100, alias="SIGRID_PROFORMA_MAX_LINEAS")` | 1 failed (`test_f007_r4_los_cinco_ajustes_arrancan_con_defecto_cerrado`) |
| S5 | `config/settings.py:146` | alias `"SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO"` → `"SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO"` | 6 failed (`test_f007_r4_los_valores_de_despliegue_llegan_por_el_entorno`) |

`interface_adapters/http/http_response_factory.py` (0 automáticos) solo cambia un docstring: no hay código que mutar.
**Límite conocido de la herramienta**: no muta literales de texto ni argumentos con nombre; el SQL de LP1-LP6 lo fijan
los tests carácter a carácter.
