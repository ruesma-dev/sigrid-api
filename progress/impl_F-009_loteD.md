<!-- progress/impl_F-009_loteD.md -->
# F-009 · lote D (T13-T15 y observaciones O1/O2 del lote C) · informe del implementer

Rama `feature/F-009-alta-albaran-compra`, spec v8.2, nivel `critico`. Commits (locales, sin push):
`6ed3c7a` T13 · `8ac52cb` T14 · `fd1674c` T15 · `11d13c0` O1 y O2 · `8ab15de` T13 (test de la tupla de ocho).
T13, T14 y T15 marcadas en `tasks.md`.

## Ficheros tocados

| Fichero | Qué |
|---|---|
| `function_app.py` | selector de modo, camino extendido, guarda R8 en las dos rutas, `except AlbaranCompraError`, docstring H32, octava posición de `build_dependencies` |
| `application/use_cases/create_albaran_compra_use_case.py` | `run` = traza R32 alrededor de `_ejecutar` (el `run` de antes, sin cambios); `reloj`; mensaje de O2 |
| `tests/test_f009_route.py` (nuevo) | 40 tests de la ruta |
| `tests/test_f009_use_case.py` | +7 de R32, +7 de O1, +1 de O2 |
| `tests/test_f009_caracterizacion.py` | **solo el arnés**: el doble de `build_dependencies` devuelve ocho (`…, caso_de_uso, None`). Dorado y `CASOS` intactos |

Sin tocar (comprobado con `git diff 1ac999a --stat`, vacío): casos de uso y modelos del clásico y de
`albaran-directo`, `infrastructure/` (seguridad y repositorio), `.env`, `tests/fixtures/`.

## T13 · `function_app.py`

- **R1**: `sigrid_albaran` lee el cuerpo y llama a `elegir_modo_albaran(body)` antes de validar nada. Extendido →
  `_sigrid_albaran_extendido` (`AlbaranCompraRequest` → R8 → `CreateAlbaranCompraUseCase.run`); clásico → el
  camino de siempre (`AddPurchaseAlbaranRequest` → R8 → `CreatePurchaseAlbaranUseCase.run`). `peticion_mixta` sale
  del selector sin tocar el repositorio. Lo que no es objeto JSON va al clásico, como hoy.
- **R9**: `except AlbaranCompraError` **antes** del `except ValidationError`/`ValueError` (hereda de `ValueError`, O4
  del lote B) → 400 `{ok:false, error, details:{type:"AlbaranCompraError", codigo[, lineas]}}`; `lineas` solo si las
  trae (`lineas_no_validas`), con `FalloLinea.model_dump()` = `{indice, referencia_linea, codigo, mensaje}`. El resto
  de `except` no cambia: `ValueError` → 400 de texto; lo inesperado → 500.
- **R8**: `_exigir_escritura_de_albaranes(settings, commit)` en `sigrid_albaran` (los dos modos) y en
  `sigrid_albaran_directo`, **después** de validar el modelo y **antes** de `use_case.run` (design). Con `commit` y
  `SIGRID_ALBARAN_WRITE_ENABLED=false` → 400 `escritura_albaranes_deshabilitada`; el dry-run no cambia.
- **H32**: docstring nuevo (dos modos; el clásico crea solo las líneas recibidas y suma las del mismo `ctrpro`; R8).
- **Cableado**: `build_dependencies` devuelve **ocho**; la octava es `CreateAlbaranCompraUseCase(repository,
  settings)`. Las rutas que desempaquetan la tupla pasan a ocho `_`; `sigrid_albaran` lee por índice (0, 6, 7).

### Decisiones de T13

1. **`type` de R8 en el clásico y en `albaran-directo`**: `AlbaranCompraError` (la guarda lanza ese error y lo traduce
   el mismo `except`). Contrato §3.3 da esa forma; para el clásico y el directo es lo único nuevo visible (R2, R3).
2. **Orden R8 frente a las guardas del extendido**: con `commit:true` y la llave cerrada, R8 (ruta) responde antes que
   `demasiadas_lineas`/`referencia_no_permitida` (caso de uso). Es lo que dice design («antes de `use_case.run`»); el
   §4.1 del contrato las agrupa en el mismo paso «sin leer la base», así que F-053 no ve diferencia de estado (`error`).
3. **`ValidationError` del extendido**: se traza solo `(loc, type)` (como F-006), porque `str(exc)` volcaría
   descripciones y precios (R32). Va en `_sigrid_albaran_extendido`, sin tocar el `except` existente del clásico
   (que sigue trazando `str(exc)`: R2). La respuesta es la de siempre (400 `Solicitud invalida.` sin `codigo`).
4. **`except AlbaranCompraError` traza solo códigos** (`codigo` y `(indice, codigo)` por línea), no `str(exc)`.
5. **Sin `except pyodbc.IntegrityError` en el extendido** (design lo pedía): la colisión ya llega como
   `AlbaranCompraError(colision_de_clave)` desde el caso de uso (decisión 12 del lote C); un `except` que nada alcanza
   sería código muerto y un superviviente seguro en T16.
6. `tests/test_f004_route.py` dice en un docstring «tupla de siete»: sigue pasando (usa `deps[0]`, `deps[1]`); no lo
   toco porque es de otra feature. Para T17/T18 o el líder.

### Fase RED de T13 (R1 y R8), traza real

Primero con el `function_app.py` de `1ac999a` (sin cambios; el doble ya da ocho):
`.venv/Scripts/python.exe -m pytest tests/test_f009_route.py -q -p no:cacheprovider` → `31 failed, 5 passed`;
falla incluso el clásico porque la ruta desempaqueta siete:
```
WARNING  function_app:function_app.py:214 ValueError en sigrid/albaran: too many values to unpack (expected 7)
...test_f009_route.py:166: AssertionError: assert {'type': 'ValueError'} == {'type': 'Alb...ticion_mixta'}
```
Para que la RED de R1 y R8 sea de comportamiento y no de la tupla, primero el cableado (ocho) y otra vez,
`… -k "r1_peticion_mixta and con_lineas or r8_commit_con_la_llave_cerrada or r1_con_lineas_va or t13"`:
```
E   AssertionError: assert [AddPurchaseA...commit=False)] == []
      Left contains one more item: AddPurchaseAlbaranRequest(database='ruesma', cod_contrato='CTSU16/0206',
      cod_obra='0404', cif_proveedor='B12345678', su_referencia='A-77', fecha_albaran=20261005,
      lineas_recibidas=[], empide=None, commit=False)
test_f009_route.py:117   (R1: la petición extendida se iba al clásico, que ignora `lineas`)
E   assert 200 == 400
test_f009_route.py:164   (R1: la petición mixta pasaba)
E   assert 200 == 400
test_f009_route.py:310   (R8 [clasico], [extendido] y [directo]: el commit llegaba al caso de uso)
FAILED ...test_f009_r1_con_lineas_va_al_caso_de_uso_extendido
FAILED ...test_f009_r1_peticion_mixta_400_sin_leer_la_base[con_lineas]
FAILED ...test_f009_r8_commit_con_la_llave_cerrada_400_sin_ejecutar_el_caso_de_uso[clasico]
FAILED ...test_f009_r8_commit_con_la_llave_cerrada_400_sin_ejecutar_el_caso_de_uso[extendido]
FAILED ...test_f009_r8_commit_con_la_llave_cerrada_400_sin_ejecutar_el_caso_de_uso[directo]
```
`test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho` (añadido tras ver 4 líneas sin cubrir en la puerta:
`sql/read`, `sql/write`, `contrato-lineas` y `documents/read` no tenían test de ruta) contra el `function_app.py`
anterior: `4 failed` con `AssertionError: assert 'ValueError' == 'ValidationError'`.

### Qué fijan los 40 tests de `test_f009_route.py`

R1: con `lineas` → extendido; sin las dos → clásico; la clave basta aunque su valor no valga (`{"referencia_externa"}`,
`{"lineas": []}`, `{"lineas": null}` → 400 de Pydantic **del extendido**: pide `usu`); mixta (también con `lineas:
null`) → `details` exacto `{type, codigo:"peticion_mixta"}` con un repositorio que revienta si se toca; lista,
número o texto → clásico. R7 de punta a punta (caso de uso real con `f009_dobles`): 200, todos los campos de
`AddPurchaseAlbaranResponse` más `estado`, `referencia_externa`, `avisos`, `lineas` con `indice` 0, seis `filas`, sin
columnas bancarias ni sus valores (`ES12`, `ES34`) en el JSON. R9: cabecera (`details` exacto, sin `lineas`),
`lineas_no_validas` con todas (forma exacta), `ValueError` (truncado) → 400 de texto, `RuntimeError` → 500, campo
`naturaleza` → 400 sin código. R8 (×3 rutas): commit cerrado → 400 sin ejecutar; `commit:false` y sin `commit` → 200
con la llave cerrada; abierta → llega; cuerpo inválido con commit → 400 de Pydantic (la guarda va después); el directo
sigue construyéndose con `(repository, settings)`. R32 en la ruta: ni descripción, ni precio, ni valores sobrantes en
la traza del `ValidationError`; de `lineas_no_validas`, códigos sí y mensajes no. Cableado de las ocho posiciones y
docstring (sin «TODAS las lineas»; nombra los dos modos y la llave).

### Verificación de T13 (salida real)

```
pytest tests/test_f009_route.py           -> 40 passed, 1 warning in 2.06s
pytest tests/test_f009_caracterizacion.py -> 17 passed, 1 warning in 1.46s   (dorado sin cambios)
```

## T14 · R2-R4 (salida real)

```
$ git diff dev -- application/use_cases/create_purchase_albaran_use_case.py \
    application/use_cases/create_direct_albaran_use_case.py domain/models/albaran_domain_models.py \
    domain/models/albaran_directo_models.py | wc -l
0
$ git log --format='%h %ad %s' --date=iso -- tests/fixtures/f009_caracterizacion.json
91b929d 2026-10-06 16:44:29 +0200 F-009 T1: caracterización de las ramas de error de las dos rutas
783f2d1 2026-10-06 15:48:36 +0200 F-009 T1: test de caracterización del modo clásico y de albaran-directo
$ git log --reverse --format='%h %ad %s' --date=iso dev..HEAD -- config domain application function_app.py infrastructure | head -1
c7c0b95 2026-10-06 17:50:20 +0200 F-009 T2: seis App Settings SIGRID_ALBARAN_* con defecto cerrado
$ git merge-base --is-ancestor 91b929d c7c0b95 && echo ...
91b929d es ancestro de c7c0b95 (primer commit de produccion)
```
El dorado solo tiene los dos commits de T1, los dos anteriores al primer cambio de producción de F-009.

## T15 · trazas R32

`run` mide con `reloj` (constructor, `time.monotonic` por defecto, como F-006; decisión 13 del lote C) y emite **una**
traza JSON (`logger.info`) al terminar, con éxito o sin él: `endpoint`, `modo`, `database`, `obra` (`cod_obra`),
`contrato` (`cod_contrato` o `null`), `referencia`, `commit`, `n_lineas`, `resultado` (`ok`|`error`|`excepcion`) y
`duracion_ms`; con `ok`, `estado`, `cod`, `con_ide` y `codigos` (avisos de cabecera y de línea, en orden); con
`error`, `codigo` y `codigos` de las líneas que fallan; con `excepcion`, solo el **tipo**. Nunca `descripcion`,
`unidad`, `su_referencia`, CIF, `entres`, mensajes, precios, importes ni bancarias.

**Fase RED**, `.venv/Scripts/python.exe -m pytest tests/test_f009_use_case.py -q -p no:cacheprovider -k "r32 or
mayusculas or exact or iva_inexistente" --tb=line` (tests escritos antes que el código):
```
.........FFFFFFFF                                                        [100%]
E   TypeError: CreateAlbaranCompraUseCase.__init__() got an unexpected keyword argument 'reloj'
test_f009_use_case.py:1327   (x6: previa, commit, idempotente, cabecera, lineas_no_validas, excepción)
E   AttributeError: 'CreateAlbaranCompraUseCase' object has no attribute '_reloj'. Did you mean: '_repo'?
```
Después: `pytest tests/test_f009_use_case.py -k r32` → `7 passed, 163 deselected`. Cada test compara la traza
**entera** (dict exacto, `duracion_ms` 250,0 con un reloj doble 100,0 → 100,25), exige un único registro `INFO` y
busca en `caplog.text` once valores prohibidos (`Arena de rio`, `m3`, `A-77`, `2.675`, `10.5`, `ES12`, `ES34`,
`PROVEEDOR PRUEBA SL`, `B12345678`, el texto `DRY-RUN` de `cod_provisional` y el de las llaves), más los mensajes de
los fallos de línea y el de `truncada`.

## Observación O1 del lote C (decisión 8)

Siete tests (verdes desde el principio: fijan lo que el código ya hace): partida `01.0A` frente a `01.0a`; producto del
maestro `ma9999`; naturaleza `ma99`; analítica `0404.cdsb37`; cuenta `cuenta-a`; lista blanca exacta (`ma9999` →
`producto_no_permitido` **sin leer** `productos` ni `naturalezas`); mapeo exacto (`ma9999` en la lista blanca y el
maestro, mapeo solo con `MA9999` → `naturaleza_no_valida`). El prefijo exacto ya lo fijaba
`r29_…[distingue_mayusculas]`. **Mutantes aplicados y medidos** (`sed` en el fichero, `pytest -k "mayusculas or
exact"`, `git checkout` después):

| Mutante | Resultado |
|---|---|
| `_clave` sin `.casefold()` | **muere**: 6 failed (partida, producto, naturaleza, analítica, cuenta y mapeo) |
| lista blanca comparada con `_clave` | **muere**: `r13_la_lista_blanca_es_exacta…` |
| mapeo comparado con `_clave` | **muere**: `r13b_el_mapeo_es_exacto` |

## Observación O2 del lote C (decisión 7)

Mensaje nuevo: `El IVA 3 de la linea 0 (referencia_linea 'A') no esta en dbo.iva.` RED real:
```
E   AssertionError:
    - El IVA 3 de la linea 0 no esta en dbo.iva.
    + El IVA 3 de la linea 0 (referencia_linea 'A') no esta en dbo.iva.
```
El test fija el mensaje entero (`^…$`) con dos líneas (la que se nombra es la primera); el mutante que quita la
referencia muere (`1 failed`). Lo de documentarlo en `azure-apps` es de T18.

## `bash harness/init.sh` (tal cual)

Tras `11d13c0` (antes del test de la tupla de ocho):
```
2335 passed, 1 skipped, 1 warning in 125.43s (0:02:05)
[OK] PUERTA COBERTURA: 99.6% de 1102 líneas cambiadas cubiertas (1098/1102, umbral 80%, nivel critico)
```
Las 4 sin cubrir eran `function_app.py:87, 125, 168, 463` (desempaquetado de ocho en rutas sin test). Con `8ab15de`,
final (ruff: 80 avisos de deuda previa; los ficheros del lote, limpios salvo lo previo de `function_app.py`):
```
2339 passed, 1 skipped, 1 warning in 97.10s (0:01:37)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 1102 líneas cambiadas cubiertas (1102/1102, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-009 dentro de los topes (requirements 150/150, design 250/250, impl 196/220, review 117/140)
[OK] Rama actual: feature/F-009-alta-albaran-compra
ENTORNO LISTO. Puedes trabajar.
```

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite completa) | 2339 passed, 1 skipped (`bash harness/init.sh`) |
| Tests de F-009 (los siete ficheros) | 606 passed en 4,66 s; nuevos del lote: 55 (40 de ruta + 15 de caso de uso) |
| Cobertura de las líneas cambiadas | **100,0 %** (1102/1102, umbral 80 %, `critico`), línea `PUERTA COBERTURA` |
| Mutantes | 4 dirigidos (O1 ×3, O2), 4 muertos, 0 supervivientes. La campaña `critico` completa es **T16 (lote E)**, sobre la feature entera, según el plan de lotes aprobado |
| Tiempo de la suite | 97,10 s la suite completa con cobertura; los siete ficheros de F-009, 4,66 s |

## Lo que queda para el lote E y después

- **T16** mutación de toda la feature. Puntos a vigilar del lote D: el orden de los `except` (un `AlbaranCompraError`
  capturado como `ValueError` lo matan los tests de `details` exacto) y `if commit and not …` de R8 (lo matan los
  tests de dry-run con la llave cerrada y de commit con la llave abierta).
- **T17** `docs/ARCHITECTURE.md`: modos de la ruta, `build_dependencies` con ocho posiciones, traza R32.
- **T18** `azure-apps/sigrid_api.md`: R8 con `type` `AlbaranCompraError` también en el clásico y el directo
  (decisión 1); orden R8 frente a `demasiadas_lineas` con commit (decisión 2); el 400 de texto del IVA inexistente
  (O2); lo que ya apuntaba el lote C (O3-O7 del trozo 1, O3 y O6 del trozo 2: ante un 500 en grabación, reenviar la
  misma `referencia_externa`).
- El docstring de `tests/test_f004_route.py` («tupla de siete») queda desfasado (decisión 6).
- Manuales T19-T24, sin cambios.
