# F-012 · Requisitos: los 400 de validación no acaban en 500

> **Aprobada por el humano el 2026-10-18** con las recomendaciones: D1 = **B** (saneado con `default=str`), D2 = helper único en las **9** rutas, D3 = **sin** red global en `json_response` y D4 = documentar en `azure-apps` y avisar a la sesión de albaranes antes de desplegar.

Origen: `progress/review_F-011_C3.md` §«Observaciones fuera de alcance», punto 1
(previo, de F-009). Rigor `estandar`. Diseño en [`design.md`](design.md);
decisiones abiertas D1-D4 en design §Decisiones.

Hoy las 9 rutas ponen `exc.errors()` tal cual en `details.validation`. Cuando un
validador de Pydantic lanza `ValueError` (un `model_validator` o un
`field_validator`), `exc.errors()` lleva en `ctx.error` **la excepción misma**,
`json.dumps` falla con `TypeError: Object of type ValueError is not JSON
serializable` y el `except Exception` de la ruta devuelve un **500** con ese
texto. Medido con pydantic 2.11.3 (tabla en design §Medición): pasa hoy en
`sigrid/albaran` modo extendido, `sql/write` y `sigrid/concepto-grafico`.

Glosario:
- **400 de validación**: respuesta 400 con `error` = `"Solicitud invalida."` y
  `details` = `{"type": "ValidationError", "validation": [...]}`, sin más claves.
- **Lista de hoy**: `json.loads(json.dumps(exc.errors()))`, es decir, lo que la
  ruta devuelve hoy cuando la serialización no falla (claves `type`, `loc`,
  `msg`, `input`, `ctx` si la hay, `url`).
- **Valor no serializable**: el que hace fallar `json.dumps` con `TypeError`
  (p. ej. un `ValueError` en `ctx.error`).

## A · El 400 que hoy es 500 (acceptance 1)

R1. CUANDO el modo extendido de `sigrid/albaran` recibe una petición que
incumple una regla de `model_validator` —línea vinculada sin `cod_contrato`,
`referencia_linea` repetida, `ctrpro_ide` y `producto` a la vez o ninguno,
`cantidad` 0, línea sin vincular sin `descripcion`, `paride` sin `partida`—, el
sistema debe responder el 400 de validación y no llamar al caso de uso.

R2. CUANDO `sql/write` recibe `sql` y `statements` a la vez, o ninguno de los
dos, el sistema debe responder el 400 de validación sin llamar al caso de uso.

R3. CUANDO `sigrid/concepto-grafico` recibe un `contenido_base64` mal formado,
el sistema debe responder el 400 de validación sin llamar al caso de uso.

R4. SI un error de `exc.errors()` lleva un valor no serializable (en `ctx` o en
cualquier otra clave), ENTONCES el sistema debe ponerlo en `details.validation`
como `str(valor)`; para un `ValueError`, su mensaje (p. ej.
`ctx.error == "Una linea vinculada exige 'cod_contrato'."`).

R5. El sistema no debe responder 500 por serializar `details.validation` en
ninguna de las 9 rutas, aunque el `ValidationError` venga de dentro del caso de
uso (modelos de respuesta con validadores que lanzan `ValueError`).

## B · Lo que no cambia (acceptance 2)

R6. MIENTRAS todos los valores de `exc.errors()` sean serializables, el sistema
debe devolver en `details.validation` exactamente la lista de hoy: mismas
claves (`ctx` incluida, con `ge`, `le`, `expected`, `pattern`, `class_name`…),
mismo orden y mismos valores.

R7. El sistema debe mantener intacto el dorado de caracterización de F-009
(`tests/fixtures/f009_caracterizacion.json`, que fija `ctx` en cuatro casos del
modo clásico y de `albaran-directo`): su test pasa sin regenerarlo.

R8. Las 9 rutas (`sql/read`, `sql/write`, `sigrid/contrato-lineas`,
`sigrid/albaran` clásico, `sigrid/albaran` extendido,
`sigrid/albaran-directo`, `sigrid/concepto-grafico`,
`sigrid/partes-reclamacion`, `documents/read`) deben construir su 400 de
validación con **una única función común** de `interface_adapters/http/`.
`function_app.py` no debe contener ya `exc.errors()` dentro de un `details`.

R9. El sistema debe mantener, en las 9 rutas, el orden de sus `except`, el
código HTTP y el cuerpo de todos los demás errores (`AlbaranCompraError`,
`ConceptoGraficoError`, `ParteReclamacionError`, `BaseNoPermitidaError`,
`ValueError`, 500 inesperado…).

## C · Trazas (acceptance 3)

R10. SI el modo extendido de `sigrid/albaran` rechaza la petición por
Pydantic (incluidas las reglas de R1), ENTONCES su traza debe seguir siendo
solo `(loc, type)` de cada error: ni `msg`, ni `input`, ni `ctx`. Ningún texto,
precio ni referencia de la petición aparece en los registros (R32 de F-009).

R11. La función común de R8 no debe emitir trazas: cada ruta conserva la suya
tal cual está hoy (`partes-reclamacion` sigue trazando solo `(loc, type)`, R20
de F-006).

## D · Documentación (acceptance 4)

R12. El sistema debe tener documentado en `../azure-apps/sigrid_api.md` (§1.3,
§8.2, §8.6 y §8.8) que una regla de validación con mensaje propio sale como 400
de validación con `ctx.error` en texto, y que antes salía 500; y en
`docs/ARCHITECTURE.md`, la función común de R8.

## E · Verificación tras desplegar (manual)

R13. CUANDO el humano haya desplegado, el sistema desplegado debe responder el
400 de validación a una previa (`commit: false`) del modo extendido con una
línea vinculada sin `cod_contrato` (design §Verificación manual).

## Trazabilidad requisito → test

| R | Test (design §Tests) |
|---|---|
| R1 | `test_f012_r1_*` (parametrizado por las 6 reglas) en `tests/test_f012_rutas.py` |
| R2 | `test_f012_r2_*` en `tests/test_f012_rutas.py` |
| R3 | `test_f012_r3_*` en `tests/test_f012_rutas.py` |
| R4 | `test_f012_r4_*` en `tests/test_f012_respuesta_validacion.py` |
| R5 | `test_f012_r5_*` (ruta con caso de uso doble que lanza un `ValidationError` interno) |
| R6 | `test_f012_r6_*` (helper frente a la lista de hoy: `ge`, `literal_error`, `missing`, `string_pattern_mismatch`, `model_type`) |
| R7 | `tests/test_f009_caracterizacion.py` sin tocar |
| R8 | `test_f012_r8_*` (las 9 rutas, parametrizado, y fuente sin `exc.errors()` en `details`) |
| R9 | suite previa sin tocar aserciones (`tests/test_f00*_route.py`, `test_f011_ruta.py`) |
| R10 | `test_f012_r10_*` con `caplog` |
| R11 | `test_f012_r11_*` con `caplog` sobre el helper |
| R12 | revisión del reviewer contra el código |
| R13 | MANUAL (humano / líder, solo lectura), T10 |
