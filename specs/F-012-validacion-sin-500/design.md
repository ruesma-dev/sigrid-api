# F-012 · Diseño: un solo 400 de validación, serializable siempre

Requisitos en [`requirements.md`](requirements.md). Encaje: el arreglo vive en el
adaptador de salida HTTP (`interface_adapters/http/`), que es quien serializa;
dominio, casos de uso, guardias e infraestructura no se tocan. No sale del límite
del microservicio.

## Medición (pydantic 2.11.3, `.venv`, sin red ni base)

Script fuera del repo: cada modelo de petición con cuerpos inválidos y
`json.dumps(exc.errors())`. Los modelos `sql_*` con `get_settings` doblado.

| Línea | Ruta | Modelo | ¿Valor no serializable desde la petición? |
|---|---|---|---|
| 105 | `sql/read` | `SqlReadRequest` | No: sus validadores usan `PydanticCustomError` (ctx `le`, `input` numéricos) |
| 143 | `sql/write` | `SqlWriteRequest` | **Sí**: `model_validator` con `ValueError` («`sql` y `statements`», «ni uno ni otro») |
| 179 | `sigrid/contrato-lineas` | `AddContractLinesRequest` | No: validadores que solo recortan |
| 237 | `sigrid/albaran` (clásico y `ValidationError` que escape del caso de uso extendido) | `AddPurchaseAlbaranRequest` | No desde la petición; sí desde dentro (ver abajo) |
| 271 | `sigrid/albaran` extendido | `AlbaranCompraRequest`, `LineaAlbaranIn` | **Sí**: 2 reglas de petición y 4 de línea (R1), todas `ValueError` |
| 330 | `sigrid/albaran-directo` | `AddDirectAlbaranRequest` | No |
| 388 | `sigrid/concepto-grafico` | `AttachConceptoGraficoRequest` | **Sí**: `contenido_base64` mal formado (`field_validator` con `ValueError`) |
| 443 | `sigrid/partes-reclamacion` | `CreatePartesReclamacionRequest` | No desde la petición; sí desde dentro |
| 504 | `documents/read` | `DocumentReadRequest` | No: `PydanticCustomError` sin `ctx` |

«Desde dentro»: modelos de respuesta con validador `ValueError` (`FalloLinea`,
`AvisoAlbaran` en `albaran_compra_models`, `MotivoParte` en
`parte_reclamacion_models`). Un `ValidationError` suyo durante `use_case.run`
sube al `except ValidationError` de la ruta y hoy sería 500 también. Sin camino
conocido, pero lo cubre el mismo arreglo (R5).

En todos los casos que fallan, `ctx == {"error": ValueError(...)}` y `loc`
es `()` (regla de petición) o `("lineas", i)` (regla de línea). El resto de
`ctx` que hoy sale (`ge`, `le`, `expected`, `pattern`, `class_name`) es
serializable, y **el dorado de F-009 lo fija** en 4 casos (`ge: 0.0` y
`class_name` en clásico y `albaran-directo`): ese dato decide D1.

Comparadas sobre los casos del dorado y un `finite_number` con `inf`:
`json.loads(exc.json())` sale idéntico a la lista de hoy; `exc.errors(include_context=False)`
quita `ctx` y rompe el dorado.

## Ficheros a crear

- `tests/test_f012_respuesta_validacion.py` — unit tests del helper (R4, R6, R11),
  con modelos Pydantic mínimos definidos en el propio test.
- `tests/test_f012_rutas.py` — tests de ruta (R1-R3, R5, R8, R10), con los dobles
  de `tests/test_f009_route.py` (`dependencias`, `CasoDoble`, `EXTENDIDO`,
  `SettingsDoble` de `tests/f009_dobles.py`) y el patrón de `tests/test_f004_route.py`
  para `concepto-grafico`. Se importan, no se copian.

## Ficheros a modificar

- `interface_adapters/http/http_response_factory.py` — función nueva (abajo).
  `json_response`, `error_response` y lo de F-010 no cambian.
- `function_app.py` — los 9 bloques
  `return error_response("Solicitud invalida.", status_code=400, details={...exc.errors()})`
  pasan a `return validation_error_response(exc)`, e importación. El `logger.warning`
  de cada `except ValidationError` se queda **tal cual** (incluido el de `(loc, type)`
  del extendido y de partes). Ni el orden de los `except` ni el resto cambian.
- `docs/ARCHITECTURE.md` — en el punto de `interface_adapters/http/`, una frase:
  el 400 de Pydantic de todas las rutas lo construye `validation_error_response`,
  que pasa a texto lo no serializable.
- `../azure-apps/sigrid_api.md` (otro repositorio; commit local aparte, sin push):
  - §1.3 Principios: el 400 de validación es `{type: "ValidationError", validation}`
    con la lista de Pydantic; un valor no serializable (la excepción de una regla
    con mensaje propio) sale como texto en `ctx.error`.
  - §8.2 `sql/write`: `sql` + `statements`, o ninguno, es 400 de validación (antes 500).
  - §8.6 `sigrid/albaran`, punto «400 sin código»: las reglas de R6 de F-009 dan
    400 de validación con `ctx.error` en texto; **antes de F-012 salían 500**
    (sv9 las clasificaba `error` en previa e `incierto` en grabación).
  - §8.8 `concepto-grafico`: base64 mal formado, 400 (antes 500).
  - §10: no cambia la tabla; el efecto para albaranes es el de §8.6.

## Ficheros que NO se tocan

- `domain/models/*` — no se cambian los `ValueError` de los validadores por
  `PydanticCustomError` (D1-E, descartada).
- `tests/fixtures/f009_caracterizacion.json` y `tests/test_f009_caracterizacion.py`
  — no se regeneran (R7).
- `infrastructure/` (security, repositorios, `serialization/json_encoder.py`),
  `application/`, `config/`, `scripts/`.
- `specs/F-009-alta-albaran-compra/contrato_albaranes.md` — congelado; ya
  promete 400 para las reglas de R6 (su tabla de §3.4): F-012 lo cumple, no lo
  cambia.
- Las trazas `str(exc)` de las otras rutas (ver «Fuera de alcance»).

## Clases y funciones

Capa: interface adapters (adaptador HTTP). Sin E/S salvo construir la respuesta.

```python
# interface_adapters/http/http_response_factory.py
def validation_error_response(exc: ValidationError) -> func.HttpResponse:
    """400 «Solicitud invalida.» con details {type, validation} (F-012 R8).
    validation es exc.errors() con cada valor no serializable pasado a str (R4);
    lo serializable sale idéntico (R6). No traza nada (R11)."""
```

- `details` = `{"type": type(exc).__name__, "validation": <lista>}`, construido con
  `error_response(...)` existente: el cuerpo es byte a byte el de hoy cuando todo
  es serializable.
- La lista, según D1 recomendada (B): `json.loads(json.dumps(exc.errors(), default=str))`.
  `default` solo se invoca para lo que `json` no sabe serializar, así que el resto
  (tuplas a listas incluidas, que ya hacía `json_response`) no cambia. El
  implementer puede escribirlo como función privada (`_errores_serializables`).
- Se importa `ValidationError` de `pydantic` (el módulo ya importa `BaseModel`).

## Tests (sin red ni base)

`tests/test_f012_respuesta_validacion.py`:
- R4: modelo con `model_validator` que lanza `ValueError("Regla X")` → 400,
  `validation[0]["ctx"] == {"error": "Regla X"}`, `type == "value_error"`, `loc == []`;
  y con un objeto no serializable en `ctx` de un `PydanticCustomError` → su `str`.
- R6: para `ge`, `literal_error`, `missing`, `string_pattern_mismatch` y `model_type`,
  la lista del helper == `json.loads(json.dumps(exc.errors()))`; y `details` tiene
  solo `type` y `validation`, con `error == "Solicitud invalida."`.
- R11: `caplog` a DEBUG vacío tras llamar al helper.

`tests/test_f012_rutas.py`:
- R1: parametrizado por las 6 reglas sobre `EXTENDIDO` → 400 de validación,
  `CasoDoble.peticiones == []`, `ctx.error` es `str`. Hoy da 500 (fase RED).
- R2: `sql/write` con `sql` + `statements` y con `{"database": "ruesma"}`,
  `sql_models.get_settings` doblado como en `test_f009_t13_*` → 400. Hoy 500.
- R3: `concepto-grafico` con `contenido_base64: "!!!"` → 400, caso de uso doble
  sin llamar. Hoy 500.
- R5: extendido con `CasoDoble(lanza=<ValidationError de MotivoParte o FalloLinea
  con codigo inventado>)` → 400 de validación, no 500.
- R8: parametrizado por las 9 rutas con un cuerpo que no valida (`{}`, o
  `{"lineas": []}` para el extendido) → 400 y `set(details) == {"type", "validation"}`,
  cada elemento con `loc`, `msg`, `type`. Más un test de fuente: `inspect.getsource(function_app)`
  no contiene `exc.errors()` dentro de un `details` y llama 9 veces a
  `validation_error_response`.
- R10: extendido con `referencia_linea` repetida `"REF-SECRETA"`, `descripcion`
  `"Arena secreta"`, `precio` `123.456` y vinculada sin `cod_contrato`: en `caplog`
  no aparece ninguno de los tres, ni `"exige"` (el `msg`); sí `value_error`.

Rigor `estandar`: fase RED con traza en el informe, cobertura ≥ 80 % de líneas
cambiadas, mutación muestreada (20, semilla del `rigor.json`).

## Decisiones (abiertas, para el humano)

**D1. Cómo se serializa la lista.** Recomendada **B**.
- A. `exc.errors(include_context=False)`: quita `ctx` a **todas** las rutas
  (`ge`, `expected`, `pattern`… que hoy ven los consumidores) y **rompe el dorado
  de F-009**, que no se regenera. Descartada salvo que el humano acepte ambas cosas.
- **B. Saneado con `default=str`** sobre la lista: lo no serializable, a texto;
  lo demás, idéntico. Cubre `ctx` y cualquier otra clave (R4, R5). Una línea.
- C. Sanear solo `ctx`: igual para todo lo medido, pero un `input` no
  serializable de un `ValidationError` interno seguiría dando 500.
- D. `json.loads(exc.json())`: medido idéntico hoy, pero deja la forma de
  `input`/`ctx` a la versión de Pydantic (un `pip install -U` podría mover el dorado).
- E. Cambiar los validadores a `PydanticCustomError`: cambia `type` (`value_error`
  → propio) y `msg` (sin «Value error, »), toca tres modelos de dominio y no
  protege de un validador futuro. Descartada.

**D2. Alcance.** Recomendado: helper único en las **9** rutas (R8), no solo en
las tres medidas: los «desde dentro» de `albaran` y `partes` también lo necesitan
y quita 9 copias del mismo bloque. Alternativa: solo las 3 rutas medidas.

**D3. Red de seguridad global** (`default=str` en `json_response`).
Recomendado **no**: enmascararía en texto un `Decimal` o un objeto en una
respuesta 200 que hoy falla ruidosamente; F-012 solo arregla el 400.

**D4. Lo que ven los consumidores.** Con B, solo cambian las peticiones que hoy
dan 500: pasan a 400 con `ctx.error` en texto (nadie lo ha visto nunca, porque
nunca se pudo serializar). Para albaranes sv9 un error de regla en **grabación**
pasa de `incierto` a `error` (lo que ya promete su contrato §3.4); en previa sigue
`error`. Recomendado: documentarlo en azure-apps (R12) y **avisar a la sesión
de albaranes antes de desplegar**, como con F-010, aunque no tengan que cambiar
nada.

## Riesgos

- El `msg` de `referencia_linea repetida` incluye la referencia de la petición:
  va en la **respuesta** (como hoy cualquier `input`), nunca en la traza (R10).
- Doble serialización con `default=str`: en `concepto-grafico` el `input` de un
  base64 mal formado es el base64 entero (≤ ~13 MB) y se serializa dos veces; es
  un 400, coste asumible. Ya se devolvía ese `input` en otros errores del campo.

## Fuera de alcance (anotar, no arreglar aquí)

- Las trazas de `sql/read`, `sql/write`, `contrato-lineas`, `albaran` (except
  exterior), `albaran-directo`, `concepto-grafico` y `documents/read` hacen
  `logger.warning(..., exc)`: `str(exc)` vuelca `input` (SQL, base64 recortado,
  textos). Un `ValidationError` interno del extendido llegaría a ese `except`
  exterior y vulneraría R32. Propuesta: feature aparte que unifique la traza
  `(loc, type)` en todas las rutas.

## Verificación manual (tras desplegar, solo lectura)

1. Previa del extendido contra la API desplegada: `EXTENDIDO` de prueba con una
   línea vinculada y sin `cod_contrato`, `commit: false` → 400 de validación con
   `ctx.error` en texto. Pydantic la corta antes de conectar: no lee ni escribe.
2. Opcional, con autorización del humano por ser endpoints de escritura (tampoco
   conectan): `sql/write` con `{"database":"ruesma"}` y `concepto-grafico` con
   `contenido_base64: "!!!"` → 400.
Resultados en `progress/verificacion_F-012.md`.
