<!-- progress/impl_F-009_loteE_mutacion.md -->
# F-009 · Informe del implementer · Lote E, T16 (campaña de mutación, rigor `critico`)

Rama `feature/F-009-alta-albaran-compra`, 2026-10-06/07. Spec v8.2. Sin red, sin Azure, sin SQL Server. Sin push.

| Commit | Qué |
|---|---|
| `92bf606` | `tests/test_f009_route.py`: el test de la tupla de ocho, aislado del entorno (base roja en la campaña) |
| `db945d6` | `tests/test_f009_mutacion.py` (nuevo, 31 tests): matan 60 supervivientes (el mensaje del commit dice 61 por error: son 60) |
| `8a85804` | `albaran_compra_statements.py` y `create_albaran_compra_use_case.py`: fuera 14 sitios de código que nadie lee o comprobaciones inalcanzables |
| (este) | `progress/mutacion_F-009.md`, este informe, `tasks.md` (T16 `[x]`), `progress/current.md` |

Sin tocar: casos de uso y modelos del clásico y de `albaran-directo`, `infrastructure/`, `.env`, el dorado de T1
(`tests/fixtures/`, `CASOS`), `harness/`. Comprobado con `git diff ebb0ddc --stat` (solo los 5 ficheros de arriba).

## Resultado

**Campaña válida: `8a85804`, 4 workers, 481 mutantes, 479 muertos, 2 supervivientes, 0 timeouts, 0 sin veredicto,
2.077,9 s.** Los 2 supervivientes son **equivalentes demostrados midiendo** (abajo) y se reevaluaron **en serie**: siguen
vivos. Informe completo, con la historia de las campañas y la tabla RED de los 76, en `progress/mutacion_F-009.md`.

## Historia (detalle en `mutacion_F-009.md`)

1. `ebb0ddc`: abortada (exit 2) por un fichero vacío sin versionar en la raíz, `` `0`].{t `` (24-09, ajeno). **Apartado**
   al scratchpad durante T16 y **repuesto** al final: no es mío y no lo borro; decide el humano.
2. `ebb0ddc`: abortada (exit 3), **línea base roja en paralelo**: `test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho`
   `[sql_read]`/`[sql_write]`. Reproducido (4 suites a la vez con el `.env` volcado al entorno como hace la campaña:
   `2 failed, 2337 passed` en las cuatro) y diagnosticado: `SqlReadRequest`/`SqlWriteRequest` llaman a `get_settings()`
   al validar sus defectos, el `ALLOWED_DATABASES` del entorno no se decodifica (`SettingsError`) y el 400 trae un
   error de configuración. Lección 4. Arreglo en el test (dobla `get_settings` de `sql_models` con límites fijos); el
   comportamiento vigilado (tupla de ocho) no cambia. RED/verde con el `.env` volcado:
   ```
   == antes (worktree en ebb0ddc)
   FAILED tests/test_f009_route.py::test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho[sql_read]
   FAILED tests/test_f009_route.py::test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho[sql_write]
   2 failed, 2 passed, 1 warning in 1.29s
   == despues (arbol de trabajo)
   4 passed, 1 warning in 1.26s
   ```
3. `92bf606`, 4 workers: 494 mutantes, 418 muertos, **76 supervivientes**, 3.545,3 s. **Reevaluados los 76 en serie**
   (`workers=1`, worktree de `92bf606`, `ejecutar_campania(mutantes=...)` desde un script del scratchpad):
   `evaluados=76 muertos=0 supervivientes=76 timeouts=0 base_rota=0 segundos=5884.2`. Ningún falso superviviente.
4. `8a85804`, 4 workers: la válida (arriba). Sus 2 supervivientes, reevaluados en serie en un worktree de `8a85804`:
   `evaluados=2 muertos=0 supervivientes=2 timeouts=0 base_rota=0 segundos=251.8`.

## Desenlace de los 76 de la campaña 3

### 60 · test nuevo (fase RED, `db945d6`)

Cada test fija un comportamiento de la spec que nadie fijaba; ninguno se debilitó ni se cambió comportamiento. Por
grupos (el mutante exacto de cada uno, en el docstring del test y en la tabla RED de `mutacion_F-009.md`):

| Grupo | Tests (`test_f009_…`) |
|---|---|
| NULL de Sigrid = 0 (R17, R19, R20, R30) | `r30_idempotente_con_nulos_en_lo_leido`, `r19_balance_vigente_con_nulos_…`, `r20_sumas_null_…`, `r20_sumas_previstas_con_can_null_…`, `r17_iva_null_…`, `r17_precio_null_…` (×2), `r15_caaide_null_…`, `r18_servido_negativo_con_canser_null_…`, `r20_una_suma_null_…` |
| Fronteras de R18 (`supera_pendiente`, `servido_negativo`) y R17 (`precio` 0) | `r18_servir_exactamente_lo_pendiente_…`, `r18_supera_pendiente_…_menores_que_uno`, `r18_una_positiva_tras_una_devolucion_…`, `r17_precio_cero_es_valido` |
| ε estricto (R19) y O4 del lote C de punta a punta | `r19_el_epsilon_del_stock_es_estricto`, `r19_epsilon_de_punta_a_punta_…` |
| Tope de filas de las lecturas de lista (`muchas`) | `r9_las_lecturas_de_lista_piden_el_tope_…` |
| Traza R32 (un decimal, UTF-8 sin escapar) | `r32_duracion_con_un_decimal_y_textos_sin_escapar` |
| Contrato §2: mínimos de 1 y `paride` estricto | `r5_un_caracter_basta_…`, `r14b_paride_como_texto_no_cuela` |
| Inmutabilidad de las filas de un intento (R27) | `r27_las_filas_y_los_datos_de_un_intento_son_inmutables` |
| Otros: `tipmov` ausente, mensajes, orden de avisos, `res`, `IN (?)`, fila fija | `r19_producto_sin_fila_en_pro_…`, `r30_el_conflicto_nombra_…`, `r29_el_mensaje_nombra_…`, `r16_los_avisos_del_contrato_van_delante_…`, `r13_la_sin_vincular_escribe_su_descripcion`, `r31_…_un_solo_marcador`, `r25_la_fila_fija_…`, `r20_sumas_previstas_redondeadas_…` |

Además, `r19_encadenar_devuelve_un_balance_por_movimiento` (invariante de RM6) y `r20_el_contrato_de_los_dobles_es_el_esperado`
(control de los datos de los dobles). **RED**: con el original, `31 passed`; con cada mutante aplicado, el test de su
fila cae. Extracto real (la tabla completa de 76 filas está en `mutacion_F-009.md`), comando
`python -m pytest -q --tb=no -p no:cacheprovider tests/test_f009_mutacion.py -rf` en un worktree de `92bf606`:
```
 1 | albaran_compra_statements.py:284 | if abs(almcan) < EPSILON_STOCK: -> if abs(almcan) <= EPSILON_STOCK: | exit 1 | 1 failed, 30 passed, 1 warning in 1.34s | test_f009_r19_el_epsilon_del_stock_es_estricto
15 | create_albaran_compra_use_case.py:256 | ...leer_lineas_de_albaran(int(existente[0]), muchas=True -> muchas=False | exit 1 | 1 failed, 30 passed, 1 warning in 1.23s | test_f009_r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no
31 | create_albaran_compra_use_case.py:680 | if linea.precio < 0: -> if linea.precio < 1: | exit 1 | 2 failed, 29 passed, 1 warning in 1.35s | test_f009_r17_precio_null_del_ctrpro_y_precio_cero_no_avisan, test_f009_r17_precio_cero_es_valido
63 | create_albaran_compra_use_case.py:1316 | servido[ide] > pendiente + 1e-9 -> servido[ide] >= pendiente + 1e-9 | exit 1 | 1 failed, 30 passed, 1 warning in 1.18s | test_f009_r18_servir_exactamente_lo_pendiente_no_avisa
66 | create_albaran_compra_use_case.py:1326 | linea.avisos[:0] = propios -> linea.avisos[:1] = propios | exit 1 | 1 failed, 30 passed, 1 warning in 1.39s | test_f009_r16_los_avisos_del_contrato_van_delante_de_los_de_la_plantilla
```
O4 del lote C (ε de punta a punta por el caso de uso), cerrado: stock 0,3 − 0,1 − 0,2 llega al segundo `mov` como
`almcan` 0.0 con el PMP del primero conservado.

### 14 · código que nadie lee o comprobación inalcanzable (quitado en `8a85804`)

Demostración con **canario** (el valor de relleno sustituido por algo que revienta si se lee o se usa) + **control
negativo** (el mismo canario con el valor alcanzado a propósito: tiene que salir rojo y por el canario). Sustituciones
exactas sobre `create_albaran_compra_use_case.py` de `92bf606`, en un worktree desechable:
- `_Linea`: `natide|cueide|caaide|tipmov|ivaide: int = 0` → `= _CANARIO` (`_CANARIO = object()`), `paride=0,` de
  `_vinculada` y `_sin_vincular` → `paride=_CANARIO,`, y un `__getattribute__` que lanza
  `AssertionError("CANARIO: se leyo _Linea.<campo> sin asignar")` si el valor leído es `_CANARIO`.
- `ctride = ... if de_la_obra else 0` → `else _Canario()` e `ide_log=0` → `ide_log=_Canario()` (clase cuyo `__int__`,
  `__index__`, `__eq__`, `__hash__`, `__str__`, `__repr__`, `__format__`, `__bool__`, `__float__`, `__lt__`, `__gt__` y
  `__add__` lanzan); `self._cab.almacen_sin_vincular or (0, 0)` → `or _canario_tupla()` (función que lanza).

Resultados reales:
```
canario: exit 0 | ['2370 passed, 1 skipped, 1 warning in 72.96s (0:01:12)'] | lineas con CANARIO: 0
neg_paride:  exit 1 | 110 failed, 93 passed | CANARIO: se leyo _Linea.paride sin asignar   (sin `base.paride = paride`)
neg_natide:  exit 1 | 52 failed, 151 passed | CANARIO: se leyo _Linea.natide sin asignar   (sin `natide=natide,`)
neg_cueide:  exit 1 | 52 failed, 151 passed | CANARIO: se leyo _Linea.cueide sin asignar   (sin `cueide=cueide,`)
neg_caaide:  exit 1 | 52 failed, 151 passed | CANARIO: se leyo _Linea.caaide sin asignar   (sin `caaide=caaide,`)
neg_tipmov:  exit 1 | 84 failed, 119 passed | CANARIO: se leyo _Linea.tipmov sin asignar   (sin `linea.tipmov = tipmov.get(...)`)
neg_ivaide:  exit 1 | 52 failed, 151 passed | CANARIO: se leyo _Linea.ivaide sin asignar   (sin `linea.ivaide = _entero(...)`)
neg_ctride:  exit 1 | 2 failed, 201 passed  | CANARIO: se uso un valor de relleno          (`_fila_completa` sin el `if de_la_obra`)
neg_ide_log: exit 1 | 1 failed, 202 passed  | CANARIO: se uso un valor de relleno          (sin el `replace(filas, log=...)`)
neg_almacen: exit 1 | 63 failed, 140 passed | CANARIO: se uso almacen_sin_vincular or (0, 0) (`almacen_sin_vincular = None` tras el catálogo)
```
(controles negativos con `tests/test_f009_use_case.py`, `test_f009_mutacion.py` y `test_f009_equivalencia.py`).

Qué se quitó (sin cambio de comportamiento; suite entera en verde después, `2370 passed, 1 skipped`):
- `_Linea`: `paride`, `natide`, `cueide`, `caaide`, `tipmov`, `ivaide` pasan a `int | None = None` («sin resolver / no
  aplica»), docstring con quién los pone; `_vinculada` y `_sin_vincular` ya no pasan `paride=0`.
- `_resolver_contrato`: sin `ctride ... else 0`; `ctride` se calcula tras la guarda `contrato_no_encontrado`.
- Commit: `numerar(..., ide_log=None)` (tipo `int | None` en `numerar`, docstring); el `ide` lo pone E11b como antes.
- `_sin_vincular`: `or (0, 0)` → `assert self._cab.almacen_sin_vincular is not None` (lo fija `_resolver_lineas`, R15).
- `zip(..., strict=True)` (n.º 6, 34, 37): **RM6**. Quitar `strict` es quitar defensa, así que el invariante se
  verifica en quien construye el dato: `numerar` construye `ides_dcapro` con `range(len(filas.dcapro))` dos líneas
  antes (ahora se indexa con `enumerate`, sin `zip`), y `encadenar_balances` añade un `Balance` por movimiento, fijado
  por el test nuevo `test_f009_r19_encadenar_devuelve_un_balance_por_movimiento` (0 a 11 movimientos, pares repetidos);
  comentario en el caso de uso que lo cita. Los tres `strict=False` sobrevivieron a la suite entera en serie.

### 2 · equivalentes demostrados (los supervivientes de la campaña válida)

`create_albaran_compra_use_case.py:1328` `cantidad > 0` → `>= 0` y `:1333` `cantidad < 0` → `<= 0` (en `92bf606`, l. 1316
y 1321). Solo difieren con `cantidad == 0`, que el modelo rechaza (`test_f009_models.py`, `vinculada(cantidad=0)` y
`cantidad=0.0`). Medido sobre `8a85804`:
1. Suite entera **en serie** con el mutante aplicado: sobrevive (punto 4 de la historia).
2. Diferencial original frente a mutante (módulo mutado cargado aparte, dobles de `f009_dobles.py`), **5.000 peticiones
   válidas** al azar (semilla 20261006; 1 a 5 vinculadas sobre 9001-9003, cantidades enteras, con 3 decimales y de
   frontera, `canser` NULL/0/5/20/`can`/al azar, precio del contrato u otro, 30 % en commit), comparando la respuesta
   entera (`model_dump`) o el error:
   ```
   l1316 cantidad > 0 -> >= 0: 5000 peticiones validas, 0 diferencias | control con cantidad 0 colada: 75 de 200 difieren
   l1321 cantidad < 0 -> <= 0: 5000 peticiones validas, 0 diferencias | control con cantidad 0 colada: 74 de 200 difieren
   ```
3. Control negativo: añadir al final una línea de `cantidad` 0 sobre el mismo `ctrpro` con `model_construct` (sin
   validar) hace diferir 75 y 74 de 200: el diferencial ve la diferencia cuando existe.

No hay código que quitar: la comparación separa positivas de devoluciones. **Se piden aceptar como equivalentes** (en
`critico`, el humano). RM5: el reviewer puede reproducir uno aplicando el mutante y corriendo la suite.

## Decisiones

1. **4 workers** (el defecto de la máquina, 22 núcleos) y reevaluación en serie de TODO superviviente (lección 2): la
   campaña en serie habría sido 494 × ~70 s ≈ 9,6 h.
2. Tests en un fichero nuevo, `tests/test_f009_mutacion.py`, con nombres `test_f009_rN_*` (R34) y el mutante que mata
   cada uno en su docstring (con la línea de `92bf606`).
3. Inmutabilidad de `_Obra`, `_Contrato`, `_Construido` y `FilasAlbaran`: test (R27, reentrante) en vez de quitar el
   `frozen`: es defensa barata y el test la fija (precedente F-006 con `Sellos`).
4. El fichero ajeno `` `0`].{t `` se apartó y se repuso; no lo commiteo ni lo borro.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests | `2370 passed, 1 skipped` (suite entera; 58,96 s en el `init.sh` final, 77,2 s tras `8a85804`) |
| Tests nuevos | 31 en `tests/test_f009_mutacion.py`; 1 test aislado en `tests/test_f009_route.py` |
| Cobertura de líneas cambiadas | **100,0 %** (1103/1103, umbral 80 %) |
| Mutación (campaña válida) | SHA `8a858049a5d111b96bd03be562fd709ee3ce1054`, **4 workers**, 481 generados/evaluados, 479 muertos, 2 supervivientes (equivalentes demostrados), 0 timeouts, 0 sin veredicto |
| Tiempo de la campaña | 2.077,9 s; línea base 109,2-112,6 s por worker; timeout efectivo 226 s |
| Coste por mutante | 2.077,9 × 4 ÷ 481 = **17,3 s** (RM2: media 4,3 s × 4 = 17,3 s; `-x` y 479 muertos) |
| Árbol al terminar | `git status` limpio salvo el fichero ajeno repuesto; `python -m harness.mutacion --estado` → «Sin campaña de mutación en curso.»; sin worktrees de la campaña (`git worktree list`) |

### `bash harness/init.sh` final

Ejecutado tal cual, al final (con este informe ya escrito):
```
[OK] compileall: sin errores de sintaxis
[AVISO] ruff: 80 avisos (deuda previa, no bloquea)   <- ninguno en ficheros de F-009
2370 passed, 1 skipped, 1 warning in 58.96s
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 1103 líneas cambiadas cubiertas (1103/1103, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250, impl 196/220, review 117/140)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Pendiente

- Aceptación del humano de los 2 equivalentes (nivel `critico`).
- Revisión del lote E (T16-T18). Después PARADA 2 y los manuales T19-T24.
- Arnés (no tocado, lección 2): esta vez la campaña paralela no dio falsos supervivientes (76 de 76 confirmados en
  serie). La propuesta `sin_tests` → INDETERMINADO sigue pendiente para `arnes-base`.
