<!-- progress/impl_F-018.md -->
# F-018 · Informe del implementer

Spec v1.2 aprobada por el humano (P1-P11). Rama `feature/F-018-descuento-por-linea`. Rigor `critico`.

## T0 · Contratos (sin código; `02dc4ad`)

- `contrato_albaranes.md` → **v8.4** (§2.2 `precio` y fila `dto`, §2.3, §3.1, §3.2, §3.4, §4.2, §4.3 y H8) y
  `contrato_proformas.md` → **v1.3** (§2.2, §3, §3.1, §4, §6 y §8). §4.3 del de albaranes se corrigió aunque T0 no lo
  listaba: decía «no aplica descuentos». Los textos de aviso a las dos sesiones están en este fichero en `02dc4ad`.
- **Acuses (2026-10-29, por el líder):** `albaranes` y `proformas` aceptan la v8.4 y la v1.3.
- **Texto de `albaranes`** (§2.2, columna «Origen en albaranes» de `precio` y `dto`, nota de notación I/P/d/Qs, y §2.4
  regla 4; `7aae0ba`, commit propio): pegado tal cual. El único retoque es escapar `|I|`/`|Qs|` (`\|`) dentro de la
  tabla. **Cotejado con §2.2/§3.1 y con la spec: sin choque.** `round(d, 2)` con 0 < d ≤ 100 cabe en R4. El bruto
  que cuadra a ±0,01 sigue R1/R2. Sin `dto` con d = 0 es R7. El porcentaje único es H8. No comparar con el `ctrpro`
  es compatible con D3. Una diferencia que no es choque: ellos no leen `dto`/`precio_bruto`; §3.1 decía «leerlas si
  vienen», y la previa se compara por `total`.

## P11 (bloqueo antes de T1, resuelto)

`test_f009_models.py::test_f009_r7_la_respuesta_es_superconjunto_de_la_clasica` (l. 538-548) fija los campos de
`LineaResultado`. Medido con el cambio aplicado y revertido: 4 fallos (P9, P10 y este) y 3.546 en verde (`514baa1`).
**P11 = (a)**, decidida por el humano el 2026-10-29. En la spec, `841e291`.

## T1 · Línea base de R7

`python -m pytest tests/test_f007_*.py tests/test_f009_*.py tests/test_f015_*.py tests/test_f016_*.py -q` →
**1484 passed** (22,5 s), sobre `9886967`. Ficheros (25), red de R7: `test_f007_{filas, models, perfil, route,
settings, statements_contrato, statements_lineas, transaccion, use_case}`, `test_f009_{caracterizacion, equivalencia,
models, mutacion, route, settings, statements, use_case}`, `test_f015_{statements, use_case}`, `test_f016_{models,
route, settings, statements, transaccion, use_case}`.
