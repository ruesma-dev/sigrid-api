# F-018 · Diseño (v1.1)

Medidas: [`progress/explore_F-018.md`](../../progress/explore_F-018.md) (M45-M51). Base: F-009 design §Filas, §Importes y
§Equivalencia; F-015 design §Lista blanca; F-016 (en `dev` desde `6735a75`); contrato
[`contrato_albaranes.md`](../F-009-alta-albaran-compra/contrato_albaranes.md). v1.1: respuesta del humano a la PARADA 1.

## La decisión de fondo

**Un campo opcional más en la línea del modo extendido, y la línea con descuento se construye como la construye la UI
de Sigrid; también la vinculada que copia el dto del contrato (P5).** Sin ruta nueva, sin App Setting, sin SQL nuevo y
sin tocar `infrastructure/`. El cambio vive en las tres piezas del modo extendido (modelo, constructor puro, caso de
uso); **sin dto efectivo** (ni pedido ni copiado legible del `ctrpro`) cada pieza sigue por el camino de hoy.

- **Límite de microservicio: cabe.** Escribir una línea como la escribe el ERP es construir bien el documento; qué
  descuento lleva lo decide el llamante (sv9 lo lee del albarán del proveedor).

## Decisiones (decididas por el humano, 2026-10-28: «todo lo propuesto, pero P5 se corrige aquí; rango 0 a 100»)

- **D1 · Columnas (P1).** Con dto efectivo: `tar` = bruto, `dto` = texto de R3, `tot` = R2, `pre` = `float(tot) /
  cantidad` (neto), `ivacuo` sobre `tot`, `mov` y PMP con el neto. Regla de la UI en el 99,99 % (M46), del `ctrpro`
  (M49h) y del `mov` (M48). Descartada la alternativa B (`pre` = bruto): rompía `tot` = `can`·`pre` e inflaba el PMP.
- **D2 · Alcance (P4).** Solo el modo extendido de `sigrid/albaran`. El clásico y `albaran-directo` son intocables (F-009
  R4, F-015 R11). `sigrid/proforma` no admite `dto`: se preguntará a `proformas` si sus hojas traen bruto + dto en los
  44 contratos con descuento desde 2025 (M50); si sí, feature aparte. Que herede R15 o no es P8.
- **D3 · Vinculadas con `dto` pedido: validar, no pisar (P3).** Se escribe lo pedido y cada diferencia con el `ctrpro`
  es un aviso informativo: `precio_distinto_del_contrato` (bruto contra `ctrpro.tar`, tolerancia 0,0001 de H14) y
  `dto_distinto_del_contrato` (R14); los dos si hay las dos diferencias.
- **D4 · `impbru` (P5).** Σ por línea de `redondear_euros(can·tar)` en las de dto efectivo (pedido o copiado) y de `tot`
  en las demás: sin ninguna, `impbru` = `totbas` como hoy (R7, R8).
- **D5 · `dto` 0 = sin dto; 0 ≤ `dto` ≤ 100 (P6).** `LineaAlbaranIn.con_dto` = `dto is not None and dto > 0`. 100 da
  `tot` 0 y `pre` 0, como un precio 0, que ya se admite.
- **D6 · Formato y lectura del texto.** `texto_de_dto(Decimal)`: `normalize()`, sin exponente, punto → coma, más `%`.
  `porcentaje_de_dto` acepta solo el formato de Sigrid, `^\s*\d+(,\d+)?\s*%\s*$` (100 % de los textos medidos, M45,
  M49f); otra forma es no legible, y un dto copiado no legible deja la línea en la opción C de hoy (R15).
- **D7 · Respuesta sin claves nuevas sin dto.** `LineaResultado.dto` y `.precio_bruto` con defecto `None`, y un
  `model_serializer(mode="wrap")` que **omite esas dos claves cuando valen `None`**. Así una línea sin dto efectivo se
  vuelca igual que hoy (R7) y `tests/test_f016_models.py` (`_LINEA_RESPUESTA_F007`, l. 286, comparado en
  `test_f016_r1_la_respuesta_de_mes_no_trae_claves_nuevas` y `test_f016_r19_…`) sigue pasando sin tocarlo. En
  `idempotente`, `None` (L11 no lee `tar` ni `dto`; cambiarla rompería el SQL fijado por F-009/F-015, R21).
- **D8 · P5: la vinculada que copia el dto del contrato, como Sigrid.** Opción C con `ctrpro.dto` legible > 0 y
  `ctrpro.tar` ≠ 0: se copian `tar` y `dto` como hoy y `tot`/`pre`/`ivacuo` salen de `importe_con_dto(cantidad, tar, d,
  iva)` en lugar de `importe_linea(cantidad, ctrpro.pre, iva)`. La condición de la opción C (`usa_precio_del_contrato`,
  `precio` contra el `ctrpro.pre` neto) **no cambia**. Diferencia con hoy: `tot` y `pre` a un céntimo como mucho,
  `impbru` bruto y el `mov` con el `pre` = `tot`/`can`.
- **D9 · Documentación (P7).** Se corrige el motivo de ARCHITECTURE §Semántica 9 y de `sigrid_api.md` §9.4/§12: `pre`
  ya es neto (M46, M49h); prorratear sobre `tot` sigue siendo la regla (exacta al céntimo).

## Compatibilidad: qué tests fijan hoy una vinculada con `ctrpro` con dto (búsqueda del 2026-10-28)

`grep -rn dto tests/` en la rama al día con `dev` (`6735a75`). Un `ctrpro` con dto no vacío solo aparece en:

| Dónde | Texto | Tests que fijan la opción C de hoy con él |
|---|---|---|
| `tests/f009_dobles.py:180` (ctrpro 9001) | `10+2,5` | `test_f009_use_case.py::test_f009_r17_precio_del_contrato_con_tar_y_dto` (l. 547: `tot` 21,0); los de vinculadas con precio 10,5 y `test_f009_equivalencia.py` (l. 180, `pre`/`tar`/`dto`/`tot` frente al clásico) |
| `tests/test_f009_statements.py:1077`, `:1346` (`_ctrpro`) | `10+2,5` | `::test_f009_r17_vinculada_con_precio_del_contrato_toma_pre_tar_y_dto` (l. 1432: `tot` 21,0) |
| `tests/test_f009_statements.py:1472`, `:1480` | `5` | `::test_f009_r17_opcion_c_vinculada_100_uds_toma_el_precio_del_contrato` (l. 1478: `pre` 1,0494, `tot` 104,94) |
| `tests/test_f009_mutacion.py:153` | `7` (`tar` None) | `::test_f009_r17_precio_null_del_ctrpro_es_cero_y_coincide_con_precio_cero` (l. 149: `tot` 0) |

**Ninguno está en el formato de Sigrid** (`N%`): con R14 los tres son no legibles y la línea sigue la opción C de hoy,
así que **ningún test ni dorado de F-007, F-009, F-015 o F-016 cambia por P5**. Los demás `dto` de los tests son de
plantillas de línea que se sobrescriben (`f009_dobles.py:230` `5`, `test_f009_statements.py:1030` `5+5`) o vacíos
(`f007_dobles.py:98`, `f016_dobles.py:66`, `test_f009_caracterizacion.py:184-221`); el dorado
`tests/fixtures/f009_caracterizacion.json` es del modo clásico, que no se toca. Si R14 aceptara `5` sin `%`, cambiaría
l. 1478 (`pre` 1,0494 → 1,14, `tot` 104,94 → 114,00): por eso R14 se queda en el formato de Sigrid. P5 se prueba con
`ctrpro` nuevos de `test_f018_*` con dto `N%`.

**Sí cambia un test de F-009 por R17** (no por P5): `tests/test_f009_models.py:413` fija `CODIGOS_AVISO` como conjunto
cerrado; añadir `dto_distinto_del_contrato` exige añadirlo allí (P9; precedente: F-015 T8 lo cambió igual).

## F-016 en `dev`: lo que comparte con F-018 (leído en el código)

- `CreateProformaUseCase` hereda `_construir(request, cabecera, lineas, sellos, vigentes)` y F-016 lo **sobrescribe**
  llamando a `super()` (`create_proforma_use_case.py:557`): F-018 conserva esa firma y las de las funciones públicas del
  constructor (solo argumentos con nombre y defecto). `superponer_cadena` y `filas_arrastradas`
  (`proforma_origen_statements.py`) toman las filas del núcleo tal cual; `importe_de_cadena` usa Σ ROUND(`canoriori`·`pre`).
- `traducir` no pasa `dto`, y `_AltaDeProforma.model_validate(traducida.model_dump())` (l. 309) sigue validando con
  `dto: None`. Las líneas de respuesta se rehacen con `LineaProformaResultado(**linea.model_dump(exclude={"avisos"}))`
  (l. 594, 644): con D7, sin dto efectivo no aparecen las claves nuevas.
- **Hereda R15 por la opción C** (`construir_dcapro_vinculada` es la del núcleo): P8.

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `tests/test_f018_models.py` | R4, R16, R17: `dto` válido e inválido, `con_dto`, claves omitidas con `None`, código de aviso nuevo |
| `tests/test_f018_statements.py` | R1-R3, R5, R8, R14, R15: `texto_de_dto`, `porcentaje_de_dto`, `importe_con_dto` (casos de M46), `construir_dcapro_*` con y sin dto pedido o copiado, `construir_dca` con `impbru` |
| `tests/test_f018_use_case.py` | R1, R6, R8-R18, R20-R22 con el doble de F-009 sin modificarlo y `ctrpro` propios con dto `N%` |
| `tests/test_f018_compatibilidad.py` | R7, R19, R24 sobre peticiones de F-009, F-015, F-007 y F-016; `git diff dev` vacío en los protegidos |
| `specs/F-018-descuento-por-linea/verificacion_manual.md` | Comandos literales de R25 (T17) |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `domain/models/albaran_compra_models.py` | `LineaAlbaranIn.dto` y `con_dto`; `CODIGOS_AVISO` + `dto_distinto_del_contrato`; `LineaResultado.dto`, `.precio_bruto` y el serializador de D7 |
| `application/use_cases/albaran_compra_statements.py` | §Funciones puras; `construir_dcapro_vinculada` (`dto` pedido y D8) y `construir_dcapro_sin_vincular` con `dto: float \| None = None`; `construir_dca` con `impbru: float \| None = None` |
| `application/use_cases/create_albaran_compra_use_case.py` | §Flujo: `_construir`, `_avisos_de_contrato`, la línea de respuesta y la traza |
| `tests/test_f009_models.py` | Solo l. 413: `dto_distinto_del_contrato` en el conjunto (R17, P9) |
| `function_app.py` | Solo el docstring de `sigrid_albaran` (R26) |
| `specs/F-009-alta-albaran-compra/contrato_albaranes.md` | v8.4, §Contrato, **antes** de implementar (T0) |
| `docs/ARCHITECTURE.md`; `azure-apps/sigrid_api.md` | R26 (`azure-apps` en commit aparte) |
| Según P8 (b): `create_albaran_compra_use_case.py` (`PerfilAlta`) y `create_proforma_use_case.py` (`PERFIL_PROFORMA`) | Campo `dto_del_contrato_como_sigrid: bool = True`; la proforma, `False` |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py`, `albaran_domain_models.py`,
`albaran_directo_models.py`, `tests/test_f009_caracterizacion.py`, `tests/fixtures/`; `proforma_statements.py`,
`proforma_origen_statements.py`, los modelos de proforma y `contrato_proformas.md` (salvo lo que diga P8); los demás tests
y dobles de F-007, F-009, F-015 y F-016; `infrastructure/`, `config/settings.py`, `local.settings.sample.json`, `infra/`.
Sin ficheros `NN_nombre.sql`: no hay SQL nuevo (R21).

## Funciones puras (application, `albaran_compra_statements.py`, sin E/S)

```python
def texto_de_dto(dto: float | Decimal) -> str          # R3: 40 -> "40%", 1.5 -> "1,5%", 100 -> "100%"
def porcentaje_de_dto(texto: str | None) -> Decimal | None
    # R14: None/'' -> Decimal(0); "N%"/"N,N…%" con espacios -> Decimal(N); otra forma -> None (no legible)
def importe_con_dto(cantidad: float, tar: float, dto: float | Decimal, iva: float) -> tuple[Decimal, Decimal, float]
    # R1, R2, R5: tot = redondear_euros(_decimal(cantidad) * _decimal(tar) * (1 - _decimal(dto) / 100));
    # ivacuo = redondear_euros(tot * _decimal(iva)); pre = float(tot) / cantidad. Devuelve (tot, ivacuo, pre)
def bruto_de_linea(cantidad: float, tar: float) -> Decimal   # R8: redondear_euros(cantidad · tar)
def dto_del_contrato(ctrpro: Mapping) -> Decimal | None      # D8: el dto legible > 0 con tar != 0; si no, None
def dto_coincide(pedido: float, texto_ctrpro: str | None) -> bool | None   # R13: None si no es legible
```

`importe_linea`, `sumar_importes`, `usa_precio_del_contrato` y `siguiente_balance` **no cambian**.

## Filas (R1, R8-R11, R15)

- **`construir_dcapro_sin_vincular(..., dto=None)`**: con `None`, el cuerpo de hoy. Con `dto` > 0: `tar` = `precio`,
  `dto` = `texto_de_dto(dto)`, `tot`/`ivacuo`/`pre` de `importe_con_dto`.
- **`construir_dcapro_vinculada(..., dto=None)`**: con `dto` > 0, sin `usa_precio_del_contrato`: `tar` = `precio`, `dto`
  = `texto_de_dto(dto)` y los importes de `importe_con_dto`. Con `None`, la opción C de hoy y, si casa y
  `dto_del_contrato(ctrpro)` no es `None`, `tot`/`ivacuo`/`pre` de `importe_con_dto(cantidad, tar, d, iva)` (D8); si
  no, `importe_linea` como hoy. El resto de columnas (producto, IVA, analítica, `docori*`, `canoriori`, `cod2`…), igual.
- **`construir_dca(..., impbru=None)`**: con `None`, `totales["totbas"]` (hoy). **`mov`** y **`ctrprodes`**: sin cambio
  de código; `_construir` ya pasa `dcapro[...]["pre"]` a `encadenar_balances` y `construir_mov` (R9).

## Flujo (cambios en `CreateAlbaranCompraUseCase`)

1. Validación y lecturas: igual. El `ctrpro` ya trae `tar` y `dto` (fila completa): sin lectura nueva.
2. `_construir` (firma igual): por línea, `dto = datos.dto if datos.con_dto else None`, pasado **solo con nombre**.
   Dto efectivo = `con_dto`, o vinculada que casa por la opción C con `dto_del_contrato(ctrpro)`. `importes`: sin dto
   efectivo, `importe_linea(datos.cantidad, fila["pre"], linea.iva)` como hoy; con él, `(Decimal(repr(fila["tot"])),
   Decimal(repr(fila["ivacuo"])))` (recalcular desde el neto movería céntimos). `impbru` (R8) solo si hay alguna.
3. `_avisos_de_contrato`: con `con_dto`, R12 (`precio_coincide(precio, ctrpro.tar)`) y R13 (`dto_coincide`); si no, hoy.
4. Respuesta: con dto efectivo, `dto` = `float(porcentaje_de_dto(fila["dto"]))` y `precio_bruto` = `fila["tar"]`.
5. Traza: `n_lineas_con_dto` solo si es > 0 (R18).

## Contrato con albaranes v8.4 (lo pasa el líder a albaranes ANTES de implementar; R26)

| Cambio | § | Qué hace sv9 (su F-110) |
|---|---|---|
| `lineas[].dto` opcional: número de 0 a 100 (incluidos), ≤ 2 decimales, sin cascada; con él, `precio` es el **bruto** | §2.2 | `precio` = unitario bruto y `dto`; sin descuento, como hoy (`precio` = importe/cantidad) |
| Línea con dto: `tar` = bruto, `dto` texto con coma (`"1,5%"`), `tot` = ROUND_HALF_UP(`can`·`tar`·(1 − dto/100), 2) sobre el producto exacto, `pre` = `tot`/`can` **sin redondear**; `mov` y PMP con el neto; `impbru` bruto | §3.1, §4.2 | Comparar la previa por `total` de línea; `precio` de la respuesta es el neto |
| Línea de respuesta con dto: `dto` y `precio_bruto`; sin dto, sin esas claves; en `idempotente`, nunca | §3.1 | Leerlas si vienen |
| Avisos **informativos** `dto_distinto_del_contrato` (nuevo) y `precio_distinto_del_contrato` (con dto, compara el bruto con `ctrpro.tar`); los dos si hay las dos diferencias | §3.2 | Informativos; bloqueantes si sv9 lo decide |
| **P5**: vinculada **sin** `dto` que casa con un `ctrpro` con dto y copia su `tar`/`dto`: `tot` y `pre` por la regla de arriba con el dto copiado (cambian un céntimo como mucho respecto a hoy), `impbru` bruto, `mov` con ese neto; trae `dto`/`precio_bruto` | §3.1, §4.2 | Su comparación de `total` admite el céntimo |
| H8: descuento por línea, soportado; de cabecera y en cascada, no | §5 H8 | Una cascada del proveedor, a un porcentaje en sv9 o a revisión |

## V · Verificación manual (R25; comandos literales en `verificacion_manual.md`, T17)

- **V1 · Selección (lectura, `sql/read`)**: un `AC` del escritorio de la obra 0692 con líneas con dto sin vincular de
  `MA9999` y su gemelo (mismo producto, cantidad, bruto y dto); y un `ctrpro` con dto `N%` de la empresa 1 con `canser` <
  `can` y un albarán del escritorio vinculado a él.
- **V2 · Previa sin vincular** (`commit:false`, dto 40): `tar`, `dto` `40%`, `tot` y `pre` iguales a los del escritorio;
  `filas.dca.impbru` bruto; `filas.mov.pre` neto. **V3 · Previas vinculadas** contra el `ctrpro` de V1: con su bruto y
  su dto, sin avisos; con otro dto, `dto_distinto_del_contrato`; **sin `dto` y con su `pre` neto (R15)**, `tot`/`pre` como
  el albarán del escritorio vinculado.
- **V4 · Grabación** (solo con autorización expresa para esa escritura): V2 o V3 con `commit:true` en la obra que diga
  el humano, revisada en la UI (P.Bruto, Dto, Precio, Importe, totales; abrir y cerrar la línea sin que recalcule),
  repetida (`idempotente`) y anulada desde la UI (nunca `DELETE`); lecturas de que no queda el `con`.

## Riesgos

- **Recalcular desde el neto mueve céntimos**: los importes de cabecera salen de la fila (Flujo 2). Test con 0,3 ·
  12.825 · 0,99 (3.809,03; `pre` 12.696,766…).
- **`float(tot) / cantidad`** frente al `Real` de Sigrid: el mismo cociente (M46: 23.991); los tests comparan con la
  expresión, no con un literal redondeado.
- **sv9 manda el neto y además `dto`** (doble descuento): en vinculadas lo delata `precio_distinto_del_contrato`; en sin
  vincular no hay referencia: lo dice el contrato (§2.2) y lo cubre V2.
- **P5 con un `ctrpro` incoherente** (`pre` ≠ `tar`·(1 − d)): la opción C casa con el `pre` y el `tot` sale del `tar`;
  la diferencia es la del propio contrato (M49b: `pre` = neto en 1.760 de 2.244, el resto por `can`). V3 lo revisa.
- **Mutación**: el camino de hoy lo matan los tests de F-009/F-015; las ramas nuevas, los de F-018 (M46: empate, negativo,
  100 %, no legible, `tar` 0).

## Preguntas para el humano

- **P8 (bloqueante) · ¿La proforma hereda P5?** `sigrid/proforma` (de mes y a origen) construye sus vinculadas con la
  opción C del núcleo, así que R15 le aplicaría sin pedirlo: una línea de contrato cuyo `ctrpro` tiene dto (M50: 211
  proformas desde 2025, en 44 contratos) escribiría `tot`/`pre` por la regla de Sigrid (un céntimo como mucho por
  línea), `impbru` bruto y, a origen, `importe_de_cadena` con ese `pre`. Ningún test ni dorado de F-007/F-016 cambia
  (sus `ctrpro` tienen dto vacío). **(a) Heredar**: queda como las proformas que hace Sigrid (M50, `PROF26/01377`), pero
  `totbas` puede separarse de `importe_mes` de la hoja en céntimos (R19 de F-007 compara la petición, no la fila, y
  `existente` tolera 0,05 por documento) y hay que anotarlo en `contrato_proformas.md` y avisar a `proformas`.
  **(b) No heredar**: campo `dto_del_contrato_como_sigrid` en `PerfilAlta` (defecto `True`; `PERFIL_PROFORMA` `False`),
  la proforma exactamente como hoy y P5 para proformas junto a P4. `test_f007_perfil.py:85` sigue pasando (el campo
  tiene defecto). **Recomendación: (b)**, para que la proforma no cambie sin que `proformas` lo sepa; se reabre con P4.
- **P9 · `tests/test_f009_models.py:413`.** Añadir `dto_distinto_del_contrato` a ese conjunto cerrado es el único cambio
  en un test existente (precedente: F-015 T8). ¿Conforme, o se reutiliza `precio_distinto_del_contrato` para el dto?
