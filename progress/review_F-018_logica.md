<!-- progress/review_F-018_logica.md -->
Revisión completa (pasada 1) del bloque «lógica contra la spec», sobre HEAD `7ce2240` (`git diff dev...HEAD`).

# F-018 · Revisión troceada: la lógica contra la spec

- **Veredicto del bloque: APROBADO.**
- **Rigor:** `critico`, declarado en `harness/features.json`. Este bloque solo cubre R1-R26 y D1-D12 contra el código y
  sus tests. C1-C5, la fase RED, la cobertura y la mutación (RM1-RM6) son de los otros revisores. Aquí no se ejecutó
  `init.sh`, por la regla de convivencia.
- **Ámbito leído:** `requirements.md` y `design.md` v1.2, `impl_F-018.md`, `explore_F-018.md` (M45-M50) y el diff de
  `albaran_compra_models.py`, `albaran_compra_statements.py` y `create_albaran_compra_use_case.py`. También
  `create_proforma_use_case.py` (`_construir`, `_convertir`, `_a_origen`) y `proforma_origen_statements.py`, en solo
  lectura, para comprobar que R21 se hereda.

## Qué ejecuté (salidas reales)

1. `pytest tests/test_f018_*.py` → **243 passed**.
2. `pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py tests/test_f016_*.py`:
   - en la rama, **1485 passed**;
   - en un worktree de `dev` (`6aca027`) en el scratchpad, **1484 passed**.
   - La única diferencia en `--collect-only` es `test_f007_models.py::test_f007_r6_avisos_de_proforma[dto_distinto_del_contrato]`.
     Es una parametrización derivada de `CODIGOS_AVISO_PROFORMA` y el fichero no se tocó: R17 la espera.
3. **Cruce independiente de R7, rama contra `dev`.** El mismo script se ejecutó en los dos árboles, con los dobles sin
   tocar. Cubre **32 escenarios**:
   - 13 de albarán, en previa y en commit: los 8 de la compatibilidad de F-009/F-015 y 5 nuevos de `ctrpro` que **no**
     deben activar R15 (`dto` `5`, `10+2,5`, `0%`, `40%` con `tar` 0, `40%` con un precio que no casa);
   - 6 de proforma: de mes (existente, previa y commit) y a origen (primera, encadenada y commit).
   - Volcado de cada escenario: `model_dump(mode="json")`, las lecturas, la transacción (SQL y parámetros) y la traza.
   - Resultado: **los dos JSON son idénticos byte a byte** (440.149 bytes). Así R7 queda medido contra el código de
     antes, no solo contra la propia rama, que es lo que hace `test_f018_compatibilidad.py`.
4. **Sondas de casos límite** (scripts en el scratchpad, sin tocar el árbol):
   - validación de `dto` con 23 entradas JSON;
   - las funciones puras con `ctrpro` raros;
   - el caso de uso con `dto` 100, devoluciones con R15 y con `dto`, doble descuento, `ctrpro.dto` con espacios y al
     `0,01%`, y una mezcla de R15, `dto` pedido y una línea sin descuento.

   El worktree de `dev` se quitó al acabar (`git worktree remove` y `prune`). El árbol principal quedó intacto.

## Requisitos y decisiones contra el código y los tests

| Req. | Dónde está en el código | Test que lo fija | ¿Se cumple? |
|---|---|---|---|
| R1 | `construir_dcapro_sin_vincular/vinculada(dto=)`: `tar` = `precio`, `pre` = `float(tot)/cantidad` | `test_f018_r1_*` (statements, use_case) | sí |
| R2 | `importe_con_dto`: `_decimal` por `repr` y `ROUND_HALF_UP`; los 4 casos de M46, el empate negativo y D9 | `test_f018_r2_importe_con_dto` (9 casos) | sí |
| R3 | `texto_de_dto`: `normalize`, formato `f` y coma. Sonda: `1e1` → `10%`, `1E2` → `100%`, `0.1` → `0,1%` | `test_f018_r3_texto_de_dto` (14 casos) | sí |
| R4 | `Field(ge=0, le=100, strict=True)` más el validador de `repr`. Sonda: `true`, `"40"`, `NaN`, `Infinity`, `-1`, `100.01`, `0.005` y `1e-5` → 400; `-0.0` es válido y equivale a sin dto | `test_f018_r4_*` (más el 400 sin código en la ruta) | sí |
| R5 | `ivacuo` = `redondear_euros(tot·iva)` sobre el neto | `test_f018_r5_ivacuo_sobre_el_neto` | sí |
| R6 | `precio_negativo`, sin cambios | `test_f018_r6_precio_negativo_con_dto` | sí |
| R7 | `dto` None (o `con_dto` falso) entra por el cuerpo de antes, e `impbru` None. **Cruce rama/`dev` idéntico** | `test_f018_r7_*`, `test_f018_compatibilidad.py` y las suites de F-007/9/15/16 sin tocar | sí |
| R8 | `brutos` lleva `bruto_de_linea(can, tar)` en las de dto efectivo y `tot` en las demás; `impbru` solo si hay alguna | `test_f018_r8_*` (mezcla 26,66 / 19,21; retención; devolución -510,27) | sí |
| R9 | `mov.pre` = `dcapro.pre` neto, sin tocar `encadenar_balances` | `test_f018_r9_mov_y_pmp_con_el_neto` y `r24_commit_*` | sí |
| R10 | `ctrprodes` por `datos.cantidad`, sin cambios | `test_f018_r24_commit_vinculada_r15` (`servido` [12.5, 9001]) | sí |
| R11 | con `dto`, la rama `if dto is not None` va antes que `usa_precio_del_contrato` | `test_f018_r11_*` (con `precio` = `ctrpro.pre` no copia nada) | sí |
| R12 | `_avisos_de_dto`: `precio_coincide(precio, ctrpro.tar)`, con un mensaje que dice «bruto» | `test_f018_r12_*` (tolerancia 0,0001 / 0,00011) | sí |
| R13 | `dto_coincide`: `None` da el mensaje «no se puede leer»; el aviso lleva los dos porcentajes y sale detrás de R12 | `test_f018_r13_*` (6 tests) | sí |
| R14 | `porcentaje_de_dto` con `\s*(\d+(?:,\d+)?)\s*%\s*`, `re.ASCII` y `fullmatch` | `test_f018_r14_*` (11 legibles y 15 no legibles) | sí |
| R15 | opción C intacta; `dto_del_contrato` decide; `_con_dto_efectivo` aplica la MISMA regla en importes, respuesta y traza | `test_f018_r15_*` (no legible, `tar` 0/None, `0%`, `pre` 0, D9 32,08 → 32,09) | sí |
| R16 | `LineaResultado.dto/precio_bruto` y un `model_serializer(wrap)` que omite los `None` | `test_f018_r16_*` (las 3 subclases e `idempotente`) | sí |
| R17 | `CODIGOS_AVISO` y las 3 líneas de P9, P10 y P11 (`git diff dev`: +2 y +1, ni una más) | `test_f018_r17_*` y `test_f009/f016_models` | sí |
| R18 | `n_lineas_con_dto` solo si es > 0, contado sobre la respuesta | `test_f018_r18_*` (con R15, sin dto y en error) | sí |
| R19 | clásico y `albaran-directo`: `git diff dev...HEAD` vacío en sus ficheros | dorado `f009_caracterizacion` y las suites sin tocar | sí |
| R20 | `LineaProformaIn` con `extra="forbid"`; la traducción (`proforma_statements.py:693`) no pasa `dto` | `test_f018_r20_*` (modelo y ruta) | sí |
| R21 | `super()._construir` y `LineaProformaResultado(**linea.model_dump())` arrastran las claves | `test_f018_r21_*` (mes y origen, `importe_origen_cadena`) | sí |
| R22 | `existente`, `idempotente`, arrastradas, avisos y traza, sin cambios | `test_f018_r22_*` (5 tests) y el cruce de proformas | sí |
| R23 | ninguna sentencia nueva: huella sha256 de las 47+6+3 sentencias igual a `dev` | `test_f018_r23_*` | sí |
| R24 | la misma transacción, applocks y reintento | `test_f018_r24_*` (albarán, R15, reintento y proforma de mes y a origen) | sí |
| R26 | lo que cambia, acotado por rutas | `test_f018_r26_*` | sí |

- **D1-D12:** se cumplen.
  - D5 (`impbru`) y D8 (serializador) están medidos arriba.
  - D9: la condición de la opción C no cambia, porque el diff conserva `usa_precio_del_contrato(cantidad, precio,
    ctrpro.pre)`.
  - D10: `create_proforma_use_case.py` y los demás protegidos tienen `git diff dev...HEAD --stat` vacío.
- **Fuera de este bloque:** R25 (RED y mutación), R27 (MANUAL) y R28 (documentación).

## Casos límite pedidos (medidos)

- **`dto` 100.** Sin vincular, 3 × 10 al 100 %:
  - fila: `tot` 0 y `pre` 0;
  - `impbru` 30,00 y `totbas` 0;
  - `mov.pre` 0, con un PMP que se recalcula igual que con un precio 0 (D6);
  - respuesta: `dto` 100 y `precio_bruto` 10.
- **Cantidad negativa.**
  - Con `dto` -0,4 · 1.275,68 · 0,975 sale -497,52, con `impbru` -510,27 (en los tests).
  - R15 con una devolución de -1: `tot` -2,57 y `pre` 2,57, igual que con `dto` 40 pedido y bruto 4,278. Coherente.
- **Céntimos en la frontera.**
  - 11,175 → 11,18, -11,175 → -11,18, 53,475 → 53,48 y 3.809,025 → 3.809,03, en `Decimal` exacto.
  - El ejemplo de D9 da 32,09, donde hoy da 32,08.
- **`ctrpro.dto` ilegible** (`10+2,5`, `5`, `40`, `1.5%`, con espacio duro, con cifras no ASCII): opción C de hoy, sin
  aviso, idéntico a `dev` (cruce).
- **Doble descuento** (sv9 manda el neto más `dto`): sale `precio_distinto_del_contrato` (bruto 2,5667 frente a `tar`
  4,278). Es lo que promete §Riesgos.

## Observaciones (no bloquean; para el humano)

- **O1 · Un `ctrpro.dto` legible mayor que 100 se aplica.**
  - Ejemplo medido: `porcentaje_de_dto("150%")` = 150. Con R15, 2 × 10 da `tot` **-10,00** sobre una cantidad positiva.
  - R14 y R15 no ponen techo y M45 mide un máximo de 99,99, así que hoy no se da en Sigrid.
  - Si se quiere cerrar: `dto_del_contrato` con `porcentaje <= 100`, en una feature o en un ajuste aprobado. Hoy el
    código cumple la spec.
- **O2 · R12 con `ctrpro.tar` NULL compara el bruto con 0**, así que avisa siempre. La opción C, en cambio, usa
  `tar = pre` cuando es NULL.
  - Es una decisión del implementer (la fija `test_f018_r12_ctrpro_sin_tar_avisa_del_bruto_pedido`). La spec no dice
    nada y el aviso es solo informativo.
  - Se aceptaría igual comparando con `ctrpro.pre`; lo anoto para que quede vista.
- **O3 · `dto` 100 no tiene test en el caso de uso:** solo lo cubren la función pura
  (`test_f018_r2_100_por_cien_da_cero`) y el modelo. La sonda de arriba confirma el comportamiento. Es una mejora
  opcional, no un hueco de requisito.
- **O4 · Un `ctrpro.dto` no textual daría `AttributeError`.** No es alcanzable: la columna es texto de 24 (M45) y
  pyodbc devuelve `str`.

## Cambios requeridos

Ninguno en este bloque.

## Automejora (propuesta, no aplicada)

- El cruce rama/`dev` del punto 3 (mismo script en un worktree de `dev`, volcado JSON y comparación) es barato: unos
  20 s. Es la prueba más directa de un requisito «sin dto, exactamente lo de antes».
- Propongo añadir a `CHECKPOINTS.md` (C3) que toda feature con un requisito de compatibilidad «idéntico a hoy» la
  demuestre **contra `dev`**, no solo comparando la rama consigo misma.
