# F-018 · Diseño (v1.2)

Medidas: [`progress/explore_F-018.md`](../../progress/explore_F-018.md) (M45-M51). Base: F-009 design §Filas, §Importes y
§Equivalencia; F-015 design §Lista blanca; F-007 y F-016 (en `dev`, `6aca027`); contratos
[`contrato_albaranes.md`](../F-009-alta-albaran-compra/contrato_albaranes.md) (v8.3) y
[`contrato_proformas.md`](../F-007-registrar-proforma/contrato_proformas.md) (v1.2). v1.2: P1-P9 decididas, P10 abierta.

## La decisión de fondo

**Un campo opcional más en la línea del modo extendido, y la línea con descuento se construye como la construye la UI
de Sigrid; también la vinculada que copia el dto del contrato (P5), en el albarán y en la proforma (P8 = (a)).** Sin
ruta nueva, sin App Setting, sin SQL nuevo, sin tocar `infrastructure/` ni el código de proforma. El cambio vive en
las tres piezas del modo extendido (modelo, constructor puro, caso de uso); **sin dto efectivo** (ni pedido ni copiado
legible del `ctrpro`) cada pieza sigue por el camino de hoy.

- **Límite de microservicio: cabe.** Escribir una línea como la escribe el ERP es construir bien el documento; qué
  descuento lleva lo decide el llamante (sv9 lo lee del albarán del proveedor).

## Decisiones (decididas por el humano, 2026-10-28)

- **D1 · Columnas (P1).** Con dto efectivo: `tar` = bruto, `dto` = texto de R3, `tot` = R2, `pre` = `float(tot) /
  cantidad` (neto), `ivacuo` sobre `tot`, `mov` y PMP con el neto. Regla de la UI en el 99,99 % (M46), del `ctrpro`
  (M49h) y del `mov` (M48). Descartada la alternativa B (`pre` = bruto): rompía `tot` = `can`·`pre` e inflaba el PMP.
- **D2 · Redondeo (P2).** `ROUND_HALF_UP` sobre el producto exacto en `Decimal` (`redondear_euros`, H33; M46).
- **D3 · Vinculadas con `dto` pedido: validar, no pisar (P3).** Se escribe lo pedido y cada diferencia con el `ctrpro`
  es un aviso informativo, siempre que difieran: `precio_distinto_del_contrato` (bruto contra `ctrpro.tar`, tolerancia
  0,0001 de H14) y `dto_distinto_del_contrato` (R14); los dos si hay las dos diferencias.
- **D4 · Alcance de la petición (P4).** Solo el modo extendido de `sigrid/albaran` admite `dto`. El clásico y
  `albaran-directo` son intocables (F-009 R4, F-015 R11); `sigrid/proforma` no lo admite (400 sin código, como hoy).
- **D5 · `impbru`.** Σ por línea de `redondear_euros(can·tar)` en las de dto efectivo (pedido o copiado) y de `tot` en
  las demás: sin ninguna, `impbru` = `totbas` como hoy (R7, R8).
- **D6 · `dto` 0 = sin dto; 0 ≤ `dto` ≤ 100 (P6).** `LineaAlbaranIn.con_dto` = `dto is not None and dto > 0`. 100 da
  `tot` 0 y `pre` 0, como un precio 0, que ya se admite.
- **D7 · Formato y lectura del texto.** `texto_de_dto(Decimal)`: `normalize()`, sin exponente, punto → coma, más `%`.
  `porcentaje_de_dto` acepta solo el formato de Sigrid, `^\s*\d+(,\d+)?\s*%\s*$` (100 % de los textos medidos, M45,
  M49f); otra forma es no legible, y un dto copiado no legible deja la línea en la opción C de hoy (R15).
- **D8 · Respuesta sin claves nuevas sin dto.** `LineaResultado.dto` y `.precio_bruto` con defecto `None`, y un
  `model_serializer(mode="wrap")` que **omite esas dos claves cuando valen `None`**. Así una línea sin dto efectivo se
  vuelca igual que hoy (R7) y `tests/test_f016_models.py` (`_LINEA_RESPUESTA_F007`, l. 286) sigue pasando. Las
  subclases de proforma (`LineaProformaResultado`, `LineaProformaOrigenResultado`) heredan campos y serializador. En
  `idempotente`, `None` (L11 no lee `tar` ni `dto`; cambiarla rompería el SQL fijado por F-009/F-015, R23).
- **D9 · P5: la vinculada que copia el dto del contrato, como Sigrid.** Opción C con `ctrpro.dto` legible > 0 y
  `ctrpro.tar` ≠ 0: se copian `tar` y `dto` como hoy y `tot`/`pre`/`ivacuo` salen de `importe_con_dto(cantidad, tar, d,
  iva)` en lugar de `importe_linea(cantidad, ctrpro.pre, iva)`. La condición de la opción C (`usa_precio_del_contrato`,
  `precio` contra el `ctrpro.pre` neto) **no cambia**. **Cota**: con `ctrpro.pre` = `ctrpro.tot`/`ctrpro.can` (M49h:
  1.758 de 1.783) y `can` ≤ `ctrpro.can`, |Δ`tot`| ≤ 0,01 por línea (|`can`·(`pre` − `tar`·f)| ≤ 0,005 más dos
  redondeos); fuera de eso puede ser mayor (Riesgos). Ejemplo: `tar` 4,278, `40%`, `ctrpro.can` 36 (`tot` 92,40),
  `can` 12,5: hoy 32,08, con P5 32,09.
- **D10 · P8 = (a): la proforma hereda D9, de mes y a origen, sin interruptor.** `CreateProformaUseCase` construye sus
  vinculadas con el núcleo (`super()._construir`, `create_proforma_use_case.py:557`), así que R21 sale **sin tocar**
  `create_proforma_use_case.py` ni `PerfilAlta` (`test_f007_perfil.py::test_f007_r31_*` sigue igual). Queda como las
  proformas del escritorio (M50, `PROF26/01377`). Detalle: §La proforma.
- **D11 · Documentación (P7).** Se corrige el motivo de ARCHITECTURE §Semántica 9 y de `sigrid_api.md` §9.4/§12: `pre`
  ya es neto (M46, M49h); prorratear sobre `tot` sigue siendo la regla (exacta al céntimo).
- **D12 · P9.** `dto_distinto_del_contrato` se añade al conjunto cerrado de `tests/test_f009_models.py:413` (precedente:
  F-015 T8). Lo que además rompe en la proforma es P10.

## Compatibilidad: qué tests fijan hoy un `ctrpro` con dto (búsquedas del 2026-10-28 sobre `c6eb281`)

**Albarán.** `grep -rn dto tests/`. Un `ctrpro` con dto no vacío solo aparece en:

| Dónde | Texto | Tests que fijan la opción C de hoy con él |
|---|---|---|
| `tests/f009_dobles.py:180` (ctrpro 9001) | `10+2,5` | `test_f009_use_case.py::test_f009_r17_precio_del_contrato_con_tar_y_dto` (l. 547); vinculadas con precio 10,5; `test_f009_equivalencia.py` (l. 180); `test_f007_perfil.py` (l. 68, 392-461, perfil de proforma) |
| `tests/test_f009_statements.py:1077`, `:1346` | `10+2,5` | `::test_f009_r17_vinculada_con_precio_del_contrato_toma_pre_tar_y_dto` (l. 1432) |
| `tests/test_f009_statements.py:1472`, `:1480` | `5` | `::test_f009_r17_opcion_c_vinculada_100_uds_toma_el_precio_del_contrato` (l. 1478) |
| `tests/test_f009_mutacion.py:153` | `7` (`tar` None) | `::test_f009_r17_precio_null_del_ctrpro_es_cero_y_coincide_con_precio_cero` (l. 149) |

**Ninguno está en el formato de Sigrid** (`N%`): con R14 son no legibles y siguen la opción C de hoy. Los demás `dto`
son de plantillas que se sobrescriben (`f009_dobles.py:230` `5`, `test_f009_statements.py:1030` `5+5`) o vacíos. Si
R14 aceptara `5` sin `%`, cambiaría l. 1478 (`tot` 104,94 → 114,00): por eso R14 se queda en el formato de Sigrid.

**Proforma (P8 = (a)), medido:** `grep -rn dto tests/test_f007_*.py tests/test_f016_*.py` → **0 líneas**; `grep -c dto
tests/fixtures/f007_obra0719.json tests/fixtures/f016_cadena.json` → **0 y 0**; `grep -n dto tests/f007_dobles.py
tests/f016_dobles.py` → l. 98 `"dto": ""` en `ctrpro_0719` (el **único** origen de `ctrpro` de los dos dobles: con
`tar` = `pre`; `RepositorioOrigen` hereda de `RepositorioProforma`, `f016_dobles.py` no define `ctrpro`) y l. 66 `"dto":
""` en `fila_dcapro` (filas LP9 de la cadena, no `ctrpro`). `test_f007_perfil.py` usa el 9001 (`10+2,5`, no legible).
**Ningún test ni dorado de F-007/F-016 cambia por R21.** R21 se prueba con `ctrpro` `N%` propios (`test_f018_proforma`).

**Conjuntos cerrados de avisos (P9, P10), medido** en una copia aislada (`git archive c6eb281`) con
`dto_distinto_del_contrato` añadido a `CODIGOS_AVISO` y `pytest tests/` (3.546 en verde): fallan
`test_f009_r9_codigos_cerrados_de_design` (`test_f009_models.py`, P9) y, **además**, en `test_f016_models.py`,
`test_f016_r20_los_conjuntos_de_f007_identicos` (l. 216) y `test_f016_r20_los_codigos_nuevos_en_las_subclases`
(l. 226): `CODIGOS_AVISO_PROFORMA` es `CODIGOS_AVISO | {…}` (`proforma_models.py:57`) y `_AVISO_F007` (l. 204-210) lo
fija literal. (El cuarto fallo, `test_mutacion_alcance_por_ficheros.py`, falla igual sin el cambio: la copia no es un
repositorio git.) → **P10**.

## La proforma con P8 = (a) (leído en `create_proforma_use_case.py` y `proforma_*_statements.py`)

| Qué | ¿Cambia? | Por qué |
|---|---|---|
| `dcapro` `tot`, `pre`, `ivacuo` de una vinculada con `ctrpro` `N%` | **sí** (D9) | `super()._construir` → `construir_dcapro_vinculada` |
| `dca.impbru` (bruto), `totbas`, `totiva`, `totdoc`, `tot`, retención | **sí** (R8) | los suma el núcleo de las filas |
| Línea de respuesta: `precio` (neto), `total`, `dto`, `precio_bruto` | **sí** | `LineaProformaResultado(**linea.model_dump(…))` (l. 594, 644) |
| A origen `importe_origen_cadena` | **sí** | `importe_de_cadena(escritas)` = Σ round(`canoriori`·`pre`) con el `pre` neto |
| A origen `canoriori`, `imporiori` (= `ctrpro.tot`), `cantidad_*_cadena` | no | dependen de `can` y del `ctrpro` (`superponer_cadena`; `albaran_compra_statements.py:950-951`) |
| `importe_anterior_cadena`, arrastradas (fila y respuesta) | no | filas leídas de la anterior; `_linea_arrastrada` no pone `dto` |
| F-007 R19 (`comprobar_hoja`, `linea_descuadrada`), `origen` | no | comparan la **petición** (`importe_de_lineas`), no las filas |
| `existente` (±0,05) y `anterior_distinto_de_sigrid` | no el código | comparan `totbas` **leído**; lo nuevo es lo que se registra (Riesgos) |
| `existente`/`idempotente` (líneas leídas), traza R33/F-016 R21 | no | LP6/L11 sin `dto`; `run` propio sin `n_lineas_con_dto` |
| Avisos R12/R13 | nunca | solo con `dto` pedido, que la proforma no admite |

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `tests/test_f018_models.py` | R4, R16, R17: `dto` válido e inválido, `con_dto`, claves omitidas con `None`, código de aviso nuevo |
| `tests/test_f018_statements.py` | R1-R3, R5, R8, R14, R15: funciones puras (casos de M46 y D9), `construir_dcapro_*`, `construir_dca` con `impbru` |
| `tests/test_f018_use_case.py` | R1, R6, R8-R18, R20, R23-R24 con el doble de F-009 sin modificarlo y `ctrpro` propios con dto `N%` |
| `tests/test_f018_proforma.py` | R21, R22: subclases en el test de `RepositorioProforma`/`RepositorioOrigen` con un `ctrpro` `N%` coherente (`pre` = `tot`/`can`, también en LP4) |
| `tests/test_f018_compatibilidad.py` | R7, R19, R26 sobre peticiones de F-009, F-015, F-007 y F-016; `git diff dev` vacío en los protegidos |
| `specs/F-018-descuento-por-linea/verificacion_manual.md` | Comandos literales de R27 |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `domain/models/albaran_compra_models.py` | `LineaAlbaranIn.dto` y `con_dto`; `CODIGOS_AVISO` + `dto_distinto_del_contrato`; `LineaResultado.dto`, `.precio_bruto` y el serializador de D8 |
| `application/use_cases/albaran_compra_statements.py` | §Funciones puras; `construir_dcapro_vinculada` (`dto` pedido y D9) y `construir_dcapro_sin_vincular` con `dto: float \| None = None`; `construir_dca` con `impbru: float \| None = None` |
| `application/use_cases/create_albaran_compra_use_case.py` | §Flujo: `_construir`, `_avisos_de_contrato`, la línea de respuesta y la traza de `run` |
| `tests/test_f009_models.py` | Solo l. 413: el código nuevo en el conjunto (R17, P9) |
| `tests/test_f016_models.py` | Solo si P10 = (a): el código nuevo en `_AVISO_F007` (l. 204-210) |
| `function_app.py` | Solo el docstring de `sigrid_albaran` (R28) |
| `specs/F-009-alta-albaran-compra/contrato_albaranes.md` | v8.4 (§Contratos), **antes** de implementar (T0) |
| `specs/F-007-registrar-proforma/contrato_proformas.md` | v1.3 (§Contratos), **antes** de implementar (T0) |
| `docs/ARCHITECTURE.md`; `azure-apps/sigrid_api.md` | R28 (`azure-apps` en commit aparte) |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py`, `create_proforma_use_case.py`, `proforma_statements.py`, `proforma_origen_statements.py`,
`proforma_models.py`, `proforma_origen_models.py`; `tests/fixtures/`, `tests/test_f009_caracterizacion.py`, los dobles
(`f007_dobles.py`, `f009_dobles.py`, `f016_dobles.py`) y los demás tests de F-007, F-009, F-015 y F-016;
`infrastructure/`, `config/settings.py`, `local.settings.sample.json`, `infra/`. Sin `NN_nombre.sql` (R23).

## Funciones puras (application, `albaran_compra_statements.py`, sin E/S)

```python
def texto_de_dto(dto: float | Decimal) -> str          # R3: 40 -> "40%", 1.5 -> "1,5%", 100 -> "100%"
def porcentaje_de_dto(texto: str | None) -> Decimal | None
    # R14: None/'' -> Decimal(0); "N%"/"N,N…%" con espacios -> Decimal(N); otra forma -> None (no legible)
def importe_con_dto(cantidad: float, tar: float, dto: float | Decimal, iva: float) -> tuple[Decimal, Decimal, float]
    # R1, R2, R5: tot = redondear_euros(_decimal(cantidad) * _decimal(tar) * (1 - _decimal(dto) / 100));
    # ivacuo = redondear_euros(tot * _decimal(iva)); pre = float(tot) / cantidad. Devuelve (tot, ivacuo, pre)
def bruto_de_linea(cantidad: float, tar: float) -> Decimal   # R8: redondear_euros(cantidad · tar)
def dto_del_contrato(ctrpro: Mapping) -> Decimal | None      # D9: el dto legible > 0 con tar != 0; si no, None
def dto_coincide(pedido: float, texto_ctrpro: str | None) -> bool | None   # R13: None si no es legible
```

`importe_linea`, `sumar_importes`, `usa_precio_del_contrato` y `siguiente_balance` **no cambian**.

## Filas (R1, R8-R11, R15)

- **`construir_dcapro_sin_vincular(..., dto=None)`**: con `None`, el cuerpo de hoy. Con `dto` > 0: `tar` = `precio`,
  `dto` = `texto_de_dto(dto)`, `tot`/`ivacuo`/`pre` de `importe_con_dto`.
- **`construir_dcapro_vinculada(..., dto=None)`**: con `dto` > 0, sin `usa_precio_del_contrato`: `tar` = `precio`, `dto`
  = `texto_de_dto(dto)` y los importes de `importe_con_dto`. Con `None`, la opción C de hoy y, si casa y
  `dto_del_contrato(ctrpro)` no es `None`, `tot`/`ivacuo`/`pre` de `importe_con_dto(cantidad, tar, d, iva)` (D9); si
  no, `importe_linea` como hoy. El resto de columnas (producto, IVA, analítica, `docori*`, `canoriori`, `cod2`…), igual.
- **`construir_dca(..., impbru=None)`**: con `None`, `totales["totbas"]` (hoy). **`mov`** y **`ctrprodes`**: sin cambio
  de código; `_construir` ya pasa `dcapro[...]["pre"]` a `encadenar_balances` y `construir_mov` (R9).

## Flujo (cambios en `CreateAlbaranCompraUseCase`; la proforma los hereda, D10)

1. Validación y lecturas: igual. El `ctrpro` ya trae `tar` y `dto` (fila completa): sin lectura nueva.
2. `_construir` (firma igual, la sobrescribe F-016): por línea, `dto = datos.dto if datos.con_dto else None`, pasado
   **solo con nombre**. Dto efectivo = `con_dto`, o vinculada que casa por la opción C con `dto_del_contrato(ctrpro)`.
   `importes`: sin dto efectivo, `importe_linea(datos.cantidad, fila["pre"], linea.iva)` como hoy; con él,
   `(Decimal(repr(fila["tot"])), Decimal(repr(fila["ivacuo"])))` (recalcular desde el neto movería céntimos).
   `impbru` (R8) solo si hay alguna.
3. `_avisos_de_contrato`: con `con_dto`, R12 (`precio_coincide(precio, ctrpro.tar)`) y R13 (`dto_coincide`); si no, hoy.
4. Respuesta: con dto efectivo, `dto` = `float(porcentaje_de_dto(fila["dto"]))` y `precio_bruto` = `fila["tar"]`.
5. Traza de `run` (R18): `n_lineas_con_dto` = nº de líneas de la respuesta con `dto` no `None`, solo si es > 0. La
   proforma tiene su propio `run` y no la lleva (R22).

## Contratos (los escribe T0 y el líder los envía ANTES de implementar; R28)

**Albaranes v8.4** (`contrato_albaranes.md`):

| Cambio | § | Qué hace sv9 (su F-110) |
|---|---|---|
| `lineas[].dto` opcional: número de 0 a 100 (incluidos), ≤ 2 decimales, sin cascada; con él, `precio` es el **bruto** | §2.2 | `precio` = unitario bruto y `dto`; sin descuento, como hoy (`precio` = importe/cantidad) |
| Línea con dto: `tar` = bruto, `dto` texto con coma (`"1,5%"`), `tot` = ROUND_HALF_UP(`can`·`tar`·(1 − dto/100), 2) sobre el producto exacto, `pre` = `tot`/`can` **sin redondear**; `mov` y PMP con el neto; `impbru` bruto | §3.1, §4.2 | Comparar la previa por `total` de línea; `precio` de la respuesta es el neto |
| Línea de respuesta con dto: `dto` y `precio_bruto`; sin dto, sin esas claves; en `idempotente`, nunca | §3.1 | Leerlas si vienen |
| Avisos **informativos** `dto_distinto_del_contrato` (nuevo) y `precio_distinto_del_contrato` (con dto, compara el bruto con `ctrpro.tar`); los dos si hay las dos diferencias | §3.2 | Informativos; bloqueantes si sv9 lo decide |
| **P5**: vinculada **sin** `dto` que casa con un `ctrpro` con dto: `tot`/`pre` por la regla de arriba con el dto copiado (un céntimo como mucho con `can` ≤ `ctrpro.can`, D9), `impbru` bruto, `mov` con ese neto; trae `dto`/`precio_bruto` | §3.1, §4.2 | Su comparación de `total` admite el céntimo |
| H8: descuento por línea, soportado; de cabecera y en cascada, no | §5 H8 | Una cascada del proveedor, a un porcentaje en sv9 o a revisión |

**Proformas v1.3** (`contrato_proformas.md`; compatible hacia atrás salvo las vinculadas con `ctrpro` con dto):

| Cambio | § | Qué hace `proformas` (su F-005) |
|---|---|---|
| La petición sigue sin `dto` (400 sin código) | §2.2 | Nada |
| Vinculada cuyo `ctrpro` tiene dto `N%` (M50: 211 proformas desde 2025, 44 contratos), de mes y a origen: `tar` y `dto` del contrato, `tot` = ROUND_HALF_UP(`can`·`tar`·(1 − d/100), 2), `pre` = `tot`/`can`, `impbru` bruto; `totales` sobre esos `tot` | §3, §3.1 | `precio` de la hoja = `ctrpro.pre` como hoy; esperar ±1 céntimo por línea entre `importe_mes` y `totales.totbas` |
| Esas líneas traen `dto` y `precio_bruto` también en la de mes (excepción a «sin claves nuevas» de §3.1); las demás, `existente`, `idempotente` y arrastradas, no | §3, §3.1 | Leerlas si vienen |
| A origen: `importe_origen_cadena` con ese `pre`; `cantidad_*_cadena` e `importe_anterior_cadena`, igual | §3.1 | Su cotejo con el ORIGEN de la hoja admite los céntimos |
| `existente` (±0,05) y `anterior_distinto_de_sigrid` comparan con el `totbas` registrado, que ahora sigue la regla de Sigrid | §3, §4 | Reenviar siempre con la misma `referencia_externa` (`idempotente`) |
| `facturas` lee esas líneas con `tot` neto y `tar` bruto, como las del escritorio (`PROF26/01377`) | §6 | (aviso a `facturas`) |

## V · Verificación manual (R27; comandos literales en `verificacion_manual.md`)

- **V1 · Selección (lectura, `sql/read`)**: un `AC` del escritorio de la obra 0692 con líneas con dto sin vincular de
  `MA9999` y su gemelo (mismo producto, cantidad, bruto y dto); un `ctrpro` con dto `N%` de la empresa 1 con `canser` <
  `can` y un albarán del escritorio vinculado a él; y un contrato con dto con proformas desde 2025 (M50).
- **V2 · Previa sin vincular** (`commit:false`, dto 40): `tar`, `dto` `40%`, `tot` y `pre` iguales a los del escritorio;
  `filas.dca.impbru` bruto; `filas.mov.pre` neto. **V3 · Previas vinculadas** contra el `ctrpro` de V1: con su bruto y
  su dto, sin avisos; con otro dto, `dto_distinto_del_contrato`; **sin `dto` y con su `pre` neto (R15)**, `tot`/`pre` como
  el albarán del escritorio vinculado.
- **V4 · Grabación** (solo con autorización expresa para esa escritura): V2 o V3 con `commit:true` en la obra que diga
  el humano, revisada en la UI (P.Bruto, Dto, Precio, Importe, totales; abrir y cerrar la línea sin que recalcule),
  repetida (`idempotente`) y anulada desde la UI (nunca `DELETE`); lecturas de que no queda el `con`.
- **V5 · Previa de proforma de mes** (`commit:false`, `otra_del_mes: true` para que salga `previsto`) contra el contrato
  de V1: las líneas de contrato con dto, con `tot`/`pre` de Sigrid, `dto`/`precio_bruto` y `impbru` bruto, comparadas
  con la proforma del escritorio de ese contrato.

## Riesgos

- **Recalcular desde el neto mueve céntimos**: los importes de cabecera salen de la fila (Flujo 2). Test con 0,3 ·
  12.825 · 0,99 (3.809,03; `pre` 12.696,766…).
- **`float(tot) / cantidad`** frente al `Real` de Sigrid: el mismo cociente (M46: 23.991); los tests comparan con la
  expresión, no con un literal redondeado.
- **sv9 manda el neto y además `dto`** (doble descuento): en vinculadas lo delata `precio_distinto_del_contrato`; en sin
  vincular no hay referencia: lo dice el contrato (§2.2) y lo cubre V2.
- **P5 con un `ctrpro` incoherente** (`pre` ≠ `tot`/`can`, 25 de 1.783 en M49h) **o `can` > `ctrpro.can`**: la cota de
  D9 no vale y la diferencia con hoy puede pasar del céntimo; es la del propio contrato, como la deja Sigrid. V3 y V5.
- **Proforma (D10)**: `totbas` registrado se separa de `importe_mes` hasta un céntimo por línea con dto del contrato.
  `existente` sigue con ±0,05 por documento: con más de ~5 de esas líneas, una hoja **reenviada con otra referencia**
  no se reconocería (de mes, `proforma_del_mes_existente`, sin escribir; a origen, aviso `otra_del_mes` y alta en
  cadena paralela). Con la misma referencia sale `idempotente` (L11). Se avisa en v1.3; la tolerancia no cambia.
- **Mutación**: el camino de hoy lo matan los tests de F-007/F-009/F-015/F-016; las ramas nuevas, los de F-018 (M46:
  empate, negativo, 100 %, no legible, `tar` 0; D9: un céntimo).

## Preguntas para el humano

- **P10 (bloqueante) · El aviso nuevo rompe también `tests/test_f016_models.py`.** P9 se aceptó como «única excepción»,
  pero no lo es (medido, §Compatibilidad): `CODIGOS_AVISO_PROFORMA` = `CODIGOS_AVISO | {…}` y F-016 lo fija literal en
  `_AVISO_F007`. **(a)** Añadir `dto_distinto_del_contrato` a `_AVISO_F007` (una línea, l. 204-210): la proforma lo admite
  en su conjunto pero nunca lo emite (no admite `dto`). **(b)** Quitarlo de los conjuntos de proforma en
  `proforma_models.py:57` (`CODIGOS_AVISO - {…}`): toca código de proforma y rompe en su lugar
  `tests/test_f007_models.py:275` (`== CODIGOS_AVISO | {…}`). **(c)** Sin código nuevo: R13 reutiliza
  `precio_distinto_del_contrato` con mensaje propio (deshace P3 y P9; ningún test existente cambia).
  **Recomendación: (a).**
