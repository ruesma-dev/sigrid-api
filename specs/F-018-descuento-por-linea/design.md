# F-018 · Diseño (v1)

Medidas: [`progress/explore_F-018.md`](../../progress/explore_F-018.md) (M45-M51). Base: F-009 design §Filas, §Importes y
§Equivalencia; F-015 design §Lista blanca; contrato [`contrato_albaranes.md`](../F-009-alta-albaran-compra/contrato_albaranes.md).

## La decisión de fondo

**Un campo opcional más en la línea del modo extendido, y la línea con descuento se construye como la construye la UI
de Sigrid.** Sin ruta nueva, sin App Setting, sin SQL nuevo y sin tocar `infrastructure/`. Todo el cambio vive en las
tres piezas del modo extendido (modelo, constructor puro, caso de uso), y **sin `dto` (o con 0) cada pieza sigue por el
camino de hoy**: la rama nueva solo se entra con `dto` > 0.

- **Límite de microservicio: cabe.** Escribir una línea como la escribe el ERP es construir bien el documento; qué
  descuento lleva lo decide el llamante (sv9 lo lee del albarán del proveedor).
- **Dependencia con F-016** (en curso en su rama, no está en `dev`): F-016 no toca el núcleo (su design §Ficheros que NO
  se tocan) pero **sobrescribe `_construir`** y llama a `super()._construir(request, cabecera, lineas, sellos,
  vigentes)`. F-018 conserva esa firma posicional y las de las funciones públicas del constructor (solo añade
  argumentos con nombre y defecto). Si F-016 entra en `dev` antes, la rama de F-018 se pone al día y sus tests de F-016
  pasan sin tocarlos (T1, T15).

## Decisiones

- **D1 · Columnas (P1).** Con `dto` > 0: `tar` = `precio` (bruto), `dto` = texto de R3, `tot` = R2, `pre` = `float(tot)
  / cantidad` (neto), `ivacuo` sobre `tot`. Es la regla de la UI en el 99,99 % (M46) y la del `ctrpro` (M49h).
  **Alternativa B, descartada salvo que el humano la mantenga**: `pre` = `tar` = bruto y `tot` neto. Rompe `tot` =
  `can`·`pre`, que Sigrid conserva en 24.614 de 24.616 líneas con dto; obliga a decidir el precio del `mov` (Sigrid usa
  el neto, M48: el bruto inflaría el PMP en el porcentaje del dto) y deja en la UI una línea que el escritorio no
  produce nunca (`tar` = `pre` con dto: 62 de 24.616, M46). Con B cambian R1, R8 y R9.
- **D2 · Alcance.** Solo el modo extendido de `sigrid/albaran`. El clásico y `albaran-directo` son intocables (F-009
  R4, F-015 R11) y quedan obsoletos con F-053. `sigrid/proforma` **no** en esta feature: `proformas` no lo ha pedido;
  M50 da 211 de 8.989 proformas con dto (2,3 %), casi todas vinculadas con el dto del contrato, que hoy ya copia la
  opción C si la hoja trae el precio neto del contrato. Si las hojas traen el bruto, es una feature aparte tras F-016
  (P4). `LineaProformaIn` sigue con `extra="forbid"` y `traducir` no pasa `dto` (R20).
- **D3 · Vinculadas: validar, no pisar.** Con `dto` > 0 se escribe lo pedido y se compara con el `ctrpro`: bruto con
  `ctrpro.tar` (tolerancia 0,0001 de H14) y porcentaje con `ctrpro.dto` (R14), y cada diferencia es un aviso
  informativo (`precio_distinto_del_contrato`, `dto_distinto_del_contrato`). Es la misma política que el precio (F-009
  R17: se escribe el pedido y se avisa), el albarán del proveedor es la prueba de lo recibido, y en 2.243 de 2.244
  vinculadas con los dos dto coinciden (M49a), así que el aviso será raro. Descartado copiar el dto del `ctrpro` (un
  descuento distinto en el albarán es un dato, no un error del llamante) y el error de línea (pararía albaranes
  legítimos; si albaranes lo quiere bloqueante, lo hace en sv9 con el código: P3).
- **D4 · `impbru`.** Σ por línea del bruto redondeado en las líneas con dto y de `tot` en las demás (R8). Así un
  albarán sin `dto` sigue con `impbru` = `totbas` (R7) aunque alguna vinculada copie un dto del `ctrpro` por la opción C:
  ese camino se queda como está (P5).
- **D5 · `dto` 0 = sin dto.** `LineaAlbaranIn.con_dto` (propiedad) es `dto is not None and dto > 0`; el caso de uso solo
  pasa `dto` a las funciones puras si `con_dto`, y si no las llama exactamente como hoy (R7). 100 se admite (lo pidió
  albaranes; da `tot` 0 y `pre` 0, como un precio 0, que ya se admite).
- **D6 · Formato del texto.** `texto_de_dto(Decimal)`: `normalize()`, sin exponente, punto → coma, más `%`. El lector
  (`porcentaje_de_dto`) acepta solo `^\s*\d+(,\d+)?\s*%\s*$` (M45/M49f: 100 % de los textos desde 2020 y 2024).
- **D7 · Respuesta.** Campos nuevos en `LineaResultado` con defecto `None` (`dto`, `precio_bruto`), sin cambiar los que
  ya hay ni su valor; en `idempotente` van `null` porque L11 no lee `tar` ni `dto` y cambiarla rompería el SQL fijado
  por los tests de F-009/F-015 (R21). `precio` pasa a ser el neto en las líneas con dto: es el `pre` escrito, como hoy.

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `tests/test_f018_models.py` | R4, R16, R17: `dto` válido e inválido (texto, booleano, −0,01, 100,01, 3 decimales, `NaN`), `con_dto`, campos nuevos de `LineaResultado`, código de aviso nuevo |
| `tests/test_f018_statements.py` | R1-R3, R5, R8, R14: `texto_de_dto`, `porcentaje_de_dto`, `importe_con_dto` (casos de M46), `construir_dcapro_*` con y sin `dto`, `construir_dca` con `impbru` |
| `tests/test_f018_use_case.py` | R1, R6, R8-R18, R20-R22 con el doble de F-009 (`tests/f009_dobles.py`, sin modificarlo): previa y commit con dto, `mov`, PMP, `ctrprodes`, avisos de vinculadas, respuesta, traza |
| `tests/test_f018_compatibilidad.py` | R7, R19, R24: peticiones de F-009, F-015 y F-007 con `dto` ausente, `null` y 0 → mismas filas, mismo SQL grabado y misma respuesta salvo R16; `git diff dev` vacío en los ficheros protegidos |
| `specs/F-018-descuento-por-linea/verificacion_manual.md` | Comandos literales de R25 (T17) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `domain/models/albaran_compra_models.py` | `LineaAlbaranIn.dto` (R4) y `con_dto` (D5); `CODIGOS_AVISO` + `dto_distinto_del_contrato` (R17); `LineaResultado.dto` y `.precio_bruto` (R16) |
| `application/use_cases/albaran_compra_statements.py` | §Funciones puras; `construir_dcapro_vinculada` y `construir_dcapro_sin_vincular` con `dto: float \| None = None`; `construir_dca` con `impbru: float \| None = None` |
| `application/use_cases/create_albaran_compra_use_case.py` | §Flujo: `_construir`, `_avisos_de_contrato`, la respuesta de línea y la traza |
| `function_app.py` | Solo el docstring de `sigrid_albaran` (R26) |
| `specs/F-009-alta-albaran-compra/contrato_albaranes.md` | v8.4, §Contrato, **antes** de implementar (T0) |
| `docs/ARCHITECTURE.md`; `azure-apps/sigrid_api.md` | R26 (`azure-apps` en commit aparte) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py`, `tests/test_f009_caracterizacion.py`, `tests/fixtures/f009_caracterizacion.json`; los
`proforma_*` (modelos, sentencias, caso de uso) y `contrato_proformas.md` (F-016 lo tiene abierto en su rama); **todos
los tests y dobles de F-007, F-009 y F-015** (R7); `infrastructure/` entero, `config/settings.py`,
`local.settings.sample.json`, `infra/`. Sin ficheros `NN_nombre.sql`: no hay SQL nuevo (R21).

## Funciones puras (application, `albaran_compra_statements.py`, sin E/S)

```python
def texto_de_dto(dto: float | Decimal) -> str          # R3: 40 -> "40%", 1.5 -> "1,5%", 21.45 -> "21,45%"
def porcentaje_de_dto(texto: str | None) -> Decimal | None
    # R14: None/'' -> Decimal(0); "N%"/"N,NN%" con espacios -> Decimal(N); otra forma -> None (no legible)
def importe_con_dto(cantidad: float, tar: float, dto: float, iva: float) -> tuple[Decimal, Decimal, float]
    # R1, R2, R5: tot = redondear_euros(_decimal(cantidad) * _decimal(tar) * (1 - _decimal(dto) / 100));
    # ivacuo = redondear_euros(tot * _decimal(iva)); pre = float(tot) / cantidad. Devuelve (tot, ivacuo, pre)
def bruto_de_linea(cantidad: float, tar: float) -> Decimal   # R8: redondear_euros(cantidad · tar)
def dto_coincide(pedido: float, texto_ctrpro: str | None) -> bool | None
    # R13/R14: None si el texto del ctrpro no es legible; si no, Decimal igual (sin tolerancia: ambos con <= 2-4 dec.)
```

`importe_linea`, `sumar_importes`, `usa_precio_del_contrato` y `siguiente_balance` **no cambian**.

## Filas (R1, R8-R11)

- **`construir_dcapro_sin_vincular(..., dto=None)`**: con `dto` `None`, el cuerpo de hoy. Con `dto` > 0, lo mismo salvo
  `tar` = `precio`, `dto` = `texto_de_dto(dto)`, `tot`/`ivacuo`/`pre` de `importe_con_dto`.
- **`construir_dcapro_vinculada(..., dto=None)`**: con `dto` `None`, el cuerpo de hoy (opción C incluida). Con `dto` > 0,
  **sin** `usa_precio_del_contrato`: `tar` = `precio`, `dto` = `texto_de_dto(dto)`, `tot`/`ivacuo`/`pre` de
  `importe_con_dto`; el resto de columnas (producto, IVA, analítica, `docori*`, `canoriori`, `cod2`…) como hoy.
- **`construir_dca(..., impbru=None)`**: `impbru` = el pasado o, con `None`, `totales["totbas"]` (hoy). El resto, igual.
- **`mov`**: sin cambio de código: `_construir` ya le pasa `dcapro[...]["pre"]` (el neto) a `encadenar_balances` y a
  `construir_mov` (R9). `ctrprodes`, igual (R10).

## Flujo (cambios en `CreateAlbaranCompraUseCase`)

1. Validación y lecturas: igual. El `ctrpro` ya trae `tar` y `dto` (`read_rows_by`, fila completa): sin lectura nueva.
2. `_construir` (firma igual): por línea, `dto = datos.dto if datos.con_dto else None` y se pasa a `construir_dcapro_*`
   **solo con nombre**. `importes`: sin `dto`, `importe_linea(datos.cantidad, fila["pre"], linea.iva)` como hoy; con
   `dto`, `(Decimal(repr(fila["tot"])), Decimal(repr(fila["ivacuo"])))` (recalcular desde el `pre` neto podría mover un
   céntimo). `impbru` = `float(Σ bruto_de_linea o tot)` **solo si** alguna línea `con_dto`; si no, `None` a `construir_dca`.
3. `_avisos_de_contrato`: si la línea `con_dto`, en lugar de `usa_precio_del_contrato`, R12 (con `precio_coincide(precio,
   ctrpro.tar)`) y R13 (`dto_coincide`; `None` → aviso con «no se puede leer el descuento del contrato»). Si no, lo de hoy.
4. Respuesta (`LineaResultado`): `dto` = `float(porcentaje_de_dto(fila["dto"]))` o `None` si no legible;
   `precio_bruto` = `fila["tar"]`. `idempotente`: sin cambio (los dos `None` por defecto).
5. Traza: `n_lineas_con_dto` = nº de líneas `con_dto` (R18), en la traza del caso de uso y en la de `idempotente`.

## Contrato con albaranes v8.4 (lo pasa el líder a albaranes ANTES de implementar; R26)

| Cambio | § | Qué hace sv9 (recomendación, su F-110) |
|---|---|---|
| `lineas[].dto` opcional: número 0-100, ≤ 2 decimales, sin cascada; con él, `precio` es el **bruto** | §2.2 | Mandar `precio` = unitario bruto del albarán y `dto`; sin descuento, como hoy (`precio` = importe/cantidad) |
| Línea con dto: `tar` = bruto, `dto` `"N%"`, `tot` = ROUND_HALF_UP(`can`·`tar`·(1 − dto/100), 2), `pre` = `tot`/`can`; `mov` y PMP con el neto; `impbru` bruto | §3.1, §4.2 | Comparar la previa por `total` de línea (el importe del albarán); `precio` de la respuesta es el neto |
| Línea de respuesta: `dto`, `precio_bruto` (en `idempotente`, `null`) | §3.1 | Guardar o mostrar, a su elección |
| Aviso `dto_distinto_del_contrato` (línea, informativo); `precio_distinto_del_contrato` compara el bruto con dto | §3.2 | Informativo; bloqueante si lo deciden (P3) |
| H8: descuentos por línea, ya soportados; de cabecera y en cascada, no | §5 H8 | Un `dto` en cascada del proveedor se convierte a un único porcentaje en sv9 o va a revisión |

## Verificación manual (R25; comandos literales en `verificacion_manual.md`, T17)

- **V1 · Selección (lectura, `sql/read`)**: un `AC` del escritorio de la obra 0692 con líneas con dto sin vincular de
  `MA9999` y su albarán gemelo (mismo producto, cantidad, bruto y dto) para comparar; y un `ctrpro` con dto de un
  contrato de la empresa 1 con `canser` < `can`.
- **V2 · Previa sin vincular** (`commit:false`, `dto` 40, la cantidad y el bruto de V1): `filas.dcapro` con `tar`,
  `dto` `40%`, `tot` y `pre` iguales a los del albarán del escritorio; `filas.dca.impbru` bruto; `filas.mov.pre` neto.
- **V3 · Previa vinculada** contra el `ctrpro` de V1: igual dto y bruto → sin avisos; otro dto → `dto_distinto_del_contrato`.
- **V4 · Grabación** (solo con autorización expresa para esa escritura; llave de albaranes ya abierta): V2 con
  `commit:true` sobre `CTSU16/0206` (obra 0404) o la que diga el humano, revisada en la UI (P.Bruto, Dto, Precio,
  Importe, totales; abrir y cerrar la línea sin que la UI recalcule nada), repetida (`idempotente`) y anulada desde la UI
  (nunca `DELETE`); lecturas de que no queda `con`.

## Riesgos

- **Recalcular desde el neto mueve céntimos**: por eso los importes de la cabecera salen de la fila (Flujo 2) y no de
  `importe_linea(can, pre)`. Test con 0,3 · 12.825 · 0,99 (3.809,03; `pre` 12.696,766…).
- **`float(tot) / cantidad`** frente al `Real` de Sigrid: el mismo cociente en doble precisión (M46: `pre` = `tot`/`can`
  en 23.991); los tests comparan con la expresión exacta, no con un literal redondeado.
- **sv9 manda el neto y además `dto`** (doble descuento): en vinculadas lo delata `precio_distinto_del_contrato` (compara
  con el bruto); en sin vincular, no hay referencia: lo deja claro el contrato (§2.2) y lo cubre V2.
- **Merge con F-016**: ver §La decisión de fondo; T1 y T15 lo comprueban.
- **Mutación**: las ramas `con_dto` dejan intacto el camino de hoy, así que los mutantes del camino viejo los matan los
  tests de F-009/F-015, y los de la rama nueva, los de F-018 (casos de M46 con empate y negativo).

## Preguntas para el humano (PARADA 1)

- **P1 (bloqueante) · ¿`tar` o `pre` para el unitario original?** Pediste `pre` = unitario original; Sigrid lo guarda en
  `tar` y deja en `pre` el neto (M46, M48, M49h). Propuesta: D1 (como Sigrid). Si prefieres la alternativa B, dime
  también qué precio lleva el `mov` (bruto o neto).
- **P2 · Redondeo**: medido `ROUND_HALF_UP` sobre el producto exacto, el de F-009 (R2). ¿Conforme?
- **P3 · Diferencias con el contrato**: avisos informativos (D3). ¿O error de línea si el dto no es el del contrato?
- **P4 · Proformas**: ¿se deja `sigrid/proforma` fuera (D2) y se pregunta a `proformas` si sus hojas traen bruto + dto
  en los contratos con descuento (44 contratos desde 2025, M50)? Si sí, feature aparte tras F-016.
- **P5 · Camino de hoy con dto en el `ctrpro`**: una vinculada sin `dto` que casa con un `ctrpro` con dto escribe hoy
  `impbru` = `totbas` y `tot` = ROUND(`can`·`ctrpro.pre`) en vez del bruto y de ROUND(`can`·`tar`·(1 − d)) (a un
  céntimo como mucho). Se deja como está para no cambiar nada sin dto (R7). ¿O se corrige aquí, aceptando que cambie?
- **P6 · `dto` 100**: se admite (lo pidió albaranes). ¿O se limita a < 100?
- **P7 · Documentación**: M46 desmiente el motivo de ARCHITECTURE §Semántica 9 («`canfac·pre` ignora el dto»): `pre`
  ya es neto. Propuesta: corregir el motivo (R26), manteniendo la regla de prorratear sobre `tot`.
