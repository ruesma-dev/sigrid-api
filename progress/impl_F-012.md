<!-- progress/impl_F-012.md -->
# F-012 · Informe del implementer

Rama `feature/F-012-validacion-sin-500`. Rigor `estandar`. Decisiones aprobadas el 2026-10-18: D1 = **B**
(`default=str`), D2 = helper único en las **9** rutas, D3 = **sin** red global en `json_response`, D4 =
documentar en azure-apps (el aviso a albaranes lo da el líder). Hechas **T1-T8 y T11**; **T9 y T10 son MANUAL**
(humano / líder) y siguen abiertas. No se ha llamado a la API desplegada ni al SQL Server.

## Qué cambió

| Fichero | Cambio |
|---|---|
| `interface_adapters/http/http_response_factory.py` | `_errores_serializables(exc)` = `json.loads(json.dumps(exc.errors(), default=str))` y `validation_error_response(exc)` = `error_response("Solicitud invalida.", status_code=400, details={"type": type(exc).__name__, "validation": ...})`. Importa `ValidationError` de `pydantic`. `json_response`, `error_response` y lo de F-010 sin tocar |
| `function_app.py` | los 9 bloques `return error_response("Solicitud invalida.", ..., "validation": exc.errors()})` pasan a `return validation_error_response(exc)` (sustitución por regex con `n == 9` comprobado) + importación. **Ningún `logger.warning` cambia**, ni el orden de los `except` |
| `tests/test_f012_respuesta_validacion.py` (12) | R4, R6, R11 con modelos mínimos propios |
| `tests/test_f012_rutas.py` (26) | R1 (7 casos: las 6 reglas, la de «uno solo» en sus dos variantes), R4 en ruta, R2 (2), R3, R5 (3), R8 (9 rutas con espía + fuente), R10 (2) |
| `docs/ARCHITECTURE.md` | frase de `interface_adapters/http/` (T7) |
| `../azure-apps/sigrid_api.md` | §1.3 (viñeta nueva del 400 de validación), §8.2 (párrafo nuevo), §8.6 («400 sin código» y la frase del `ValidationError` interno, que decía «saldría como 400» y era falsa antes de F-012), §8.8. Notas **PENDIENTE DE DESPLIEGUE** hasta T10. Commit **`4584469`** en `azure-apps`, sin push. §10 sin cambios (design) |

No se tocó `domain/`, `application/`, `infrastructure/`, `config/`, `scripts/`, el dorado de F-009 ni su test
(T5: `git diff dev --stat -- tests/fixtures tests/test_f009_caracterizacion.py domain application infrastructure
config` **vacío**). Ni `.env`, ni `features.json`, ni `BACKLOG.md`. Ningún test previo cambió.

## Decisiones de diseño

- **Dobles importados, no copiados**: `CasoDoble`, `RepositorioIntocable`, `EXTENDIDO`, `CLASICO`,
  `_LIMITES_SQL` de `test_f009_route`; `SettingsDoble` de `f009_dobles`; los cuerpos válidos de
  `test_f004_route._CUERPO` y `test_f006_route._CUERPO`. Una clase `Entorno` dobla las 8 posiciones de
  `build_dependencies`, los tres casos de uso que construye la propia ruta (`directo`, `grafico`, `partes`) y
  `sql_models.get_settings`; `ninguno_llamado()` comprueba «sin llamar al caso de uso» en R1-R3.
- **R8 con espía además del test de fuente**: se sustituye `function_app.validation_error_response` por un
  envoltorio que cuenta llamadas; cada una de las 9 rutas debe llamarlo exactamente una vez. El test de fuente
  (regex `details\s*=\s*\{[^}]*exc\.errors\(\)` ausente y 9 `return validation_error_response(exc)`) queda como
  segunda barrera.
- **R10 en dos casos**, no uno: con `referencia_linea` repetida el validador corta antes de mirar
  `cod_contrato`, así que «exige» nunca saldría en ese `msg`. Se prueba también la vinculada sin contrato.
- **R4 «cualquier otra clave»** cubierto con un `input` opaco (objeto con `__str__`), además de `ctx`.
- **Byte a byte (R6)**: un test compara `get_body()` del helper con el de `error_response(..., exc.errors())`
  sobre un caso serializable con `ñ` (mismo `ensure_ascii=False`).

## Observación (no contradice lo aprobado, matiza el texto de la spec)

La spec dice que hoy «el `except Exception` de la ruta devuelve un 500». Medido en la fase RED: eso solo pasa
en el **extendido**, porque su `TypeError` nace en `_sigrid_albaran_extendido` y lo recoge el `except Exception`
de `sigrid_albaran` (500 con `details.exception`). En `sql/write`, `concepto-grafico` y los R5 el `TypeError`
nace **dentro** del `except ValidationError`, y un `except` hermano no lo recoge: la excepción **sale de la
función** y el 500 lo pone el host de Azure Functions (sin el cuerpo JSON del arnés). Para el consumidor es un
500 igual; tras F-012 los dos caminos dan el 400. No cambia nada de lo aprobado.

## Fase RED

**T1** — `python -m pytest tests/test_f012_respuesta_validacion.py -q` antes de T2:

```
E   ImportError: cannot import name 'validation_error_response' from 'interface_adapters.http.http_response_factory'
ERROR tests/test_f012_respuesta_validacion.py
1 error in 1.43s
```

Y la construcción de hoy sobre el mismo modelo del test R4 (`model_validator` con `ValueError("Regla X")`,
`error_response(..., details={"type": ..., "validation": exc.errors()})`):

```
  File "...\Lib\json\encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
TypeError: Object of type ValueError is not JSON serializable
```

**T3** — `python -m pytest tests/test_f012_rutas.py -q` antes de T4 (código de producción con el helper ya
creado pero sin usar): **26 failed**. Extracto real:

```
E       AssertionError: {'ok': False, 'error': 'Error interno ejecutando sigrid/albaran.', 'details': {'type': 'TypeError', 'exception': 'Object of type ValueError is not JSON serializable'}}
E       assert 500 == 400
ERROR    function_app:function_app.py:247 Error inesperado en sigrid/albaran
  (x7 R1 y x1 R4-ruta, idéntico)
E           pydantic_core._pydantic_core.ValidationError: 1 validation error for SqlWriteRequest
E             Value error, Usa 'sql' (atajo) o 'statements' (batch), no ambos. [type=value_error, ...]
E       TypeError: Object of type ValueError is not JSON serializable
  (R2 ninguno: «Debes indicar 'sql' o al menos una sentencia en 'statements'.», mismo TypeError)
E           pydantic_core._pydantic_core.ValidationError: 1 validation error for AttachConceptoGraficoRequest
E           contenido_base64
E             Value error, contenido_base64 no es base64 valido. [type=value_error, input_value='!!!', input_type=str]
E       TypeError: Object of type ValueError is not JSON serializable
E           pydantic_core._pydantic_core.ValidationError: 1 validation error for FalloLinea
E             Value error, 'inventado' no es un codigo de linea de sigrid/albaran. [type=value_error, ...]
E       TypeError: Object of type ValueError is not JSON serializable
  (R5 clásico igual; R5 partes con MotivoParte: «'inventado' no es un codigo de sigrid/partes-reclamacion.»)
E       AttributeError: module 'function_app' has no attribute 'validation_error_response'   (x9, R8 espía)
E       assert not <re.Match object; span=(4257, 4320), match='details={"type": type(exc).__name__, "validation">   (R8 fuente)
E       assert 500 == 400
ERROR    function_app:function_app.py:247 Error inesperado en sigrid/albaran   (x2, R10)
26 failed, 1 warning in 2.40s
```

Fallan exactamente los previstos en T3 (R1, R2, R3, R5, R8-fuente) y además R8-espía y R10, que dependen del
mismo arreglo. **Verde tras T4**: `python -m pytest tests/test_f012_rutas.py tests/test_f012_respuesta_validacion.py
-q` → `38 passed, 1 warning in 1.88s`.

## Mutación (T6)

`python -m harness.mutacion --feature F-012` → [`mutacion_F-012.md`](mutacion_F-012.md): 30 líneas en alcance,
**1 mutante generado, 1 muerto, 0 supervivientes**, 175,2 s (HEAD `347ec24`). El generador solo encontró una
constante entera (`status_code=400` → `401`, muerto): no muta llamadas, argumentos con nombre ni literales de
texto, que es casi todo lo que cambia aquí. Para no quedarme con un 1/1 hueco, apliqué **a mano** seis mutantes
sobre las líneas que sostienen la feature, ejecuté los tests de F-012 y restauré con `git checkout` (medido, no
estimado):

| Mutante manual | Resultado |
|---|---|
| M1 `json.dumps(exc.errors())` sin `default=str` | muerto: 20 failed |
| M2 `_errores_serializables` devuelve `exc.errors()` crudo | muerto: 20 failed |
| M3 `default=repr` en vez de `str` | muerto: 8 failed (R4, R1, R2, R3, R5 comparan el texto exacto) |
| M4 `"Solicitud invalida"` sin punto | muerto: 25 failed |
| M5 `details` sin `type` | muerto: 25 failed |
| M6 `sql/read` vuelve al bloque viejo con `exc.errors()` | muerto: 2 failed (R8 espía `[sql-read]` y R8 fuente) |

M6 es el único que la suite de ruta mata solo por R8: `sql/read` no tiene ninguna regla con `ValueError` desde
la petición (design §Medición), así que su 400 de hoy y el de F-012 son idénticos; lo que se protege ahí es la
regla de «una sola función común», y la protegen el espía y la fuente.

## Verificaciones MANUAL pendientes

- **T9 (humano)**: avisar a la sesión de albaranes (D4; lo da el líder) y desplegar `dev` con `func azure
  functionapp publish ...`. Sin App Settings nuevas.
- **T10 (líder, solo lectura)**: previa del extendido con una línea vinculada sin `cod_contrato`
  (`commit: false`) contra la API desplegada → 400 `ValidationError` con `ctx.error` en texto; el paso 2
  (`sql/write` y `concepto-grafico`), solo con autorización del humano. Después, quitar las notas
  «PENDIENTE DE DESPLIEGUE» de `azure-apps/sigrid_api.md` (§1.3, §8.2, §8.6, §8.8). Resultados en
  `progress/verificacion_F-012.md`.

## Fuera de alcance (anotado, no hecho)

- Las trazas `str(exc)` de `sql/read`, `sql/write`, `contrato-lineas`, `albaran` (except exterior),
  `albaran-directo`, `concepto-grafico` y `documents/read` siguen volcando `input` (design §Fuera de alcance).
  En particular, un `ValidationError` **interno** del extendido (R5) pasa por el `except` exterior de
  `sigrid_albaran`, que traza `str(exc)`: R10 solo cubre el `ValidationError` de la petición. Propuesta del
  diseño: feature aparte que unifique la traza `(loc, type)`.
- `ruff` en los ficheros tocados: los 3 avisos de `function_app.py` (`I001`, `BLE001`, `RUF010`) ya estaban en
  `dev`; el `I001` que introducía `tests/test_f012_rutas.py` se corrigió con `ruff --fix` sobre ese fichero.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados (`bash harness/init.sh`, T11) | **2702 passed, 1 skipped**, 1 warning (2664 antes de F-012 + 38 nuevos) |
| Tests de F-012 | 38 (12 helper + 26 ruta), todos en verde; `test_f009_caracterizacion.py` sin tocar y en verde |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 14 líneas cambiadas cubiertas (14/14, umbral 80%, nivel estandar)` |
| Mutación (herramienta) | 1 generado, 1 muerto, 0 supervivientes (`progress/mutacion_F-012.md`) |
| Mutación (manual, complemento) | 6 aplicados, 6 muertos, 0 supervivientes (tabla arriba) |
| Tiempo de la suite | 75,63 s en el `init.sh` final de T11 (69,40 s en el anterior, 84,62 s en T5; línea base de la campaña, 92,7 s) |
| `bash harness/init.sh` (T11) | **ENTORNO LISTO**; ruff 79 avisos, los mismos que en `dev`; PUERTA TAMAÑO impl 158/220 |

## Commits

`b0dd48f` T1 · `9c965d8` T2 · `b1f4a52` T3 · `40c417a` T4 · `347ec24` T5 · `99ef191` T6 · `829ee9e` T7 ·
`d591897` T8 · T11 (informe, `current.md`, orden de importaciones del test) en el último commit de la rama.
`azure-apps`: `4584469`.
