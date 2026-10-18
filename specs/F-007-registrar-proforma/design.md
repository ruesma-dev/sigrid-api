<!-- specs/F-007-registrar-proforma/design.md -->
# F-007 · Diseño (v1, pendiente de la PARADA 1)

Medición: [`progress/explore_F-007.md`](../../progress/explore_F-007.md) (**Mn**). Diccionario de Sigrid:
[`azure-apps/sigrid_tablas.md`](../../../azure-apps/sigrid_tablas.md). Base de todo: F-009
([`requirements`](../F-009-alta-albaran-compra/requirements.md), [`design`](../F-009-alta-albaran-compra/design.md)).

## La decisión de fondo

**Una proforma es un albarán de compra con otra serie y otra clase** (M1): `con.tip 14` + `dca` + `dcapro`, serie
`PROF<aa>/` (`sercon` 230, «Proforma subcontratista», 5 cifras, `xjsvar 'cla=141'`) y `dca.cla 141`. Mueve stock como
el albarán (`mov` si `tipmov` = 1), sirve el contrato (`ctrprodes`, `canser`, M6) y nace en 1 `PDT` (M2). Lo que la
hace distinta, medido: la **retención de garantía** del contrato en `dcarec` (56 %, M10), el **IVA de inversión del
sujeto pasivo** (91,5 % de líneas a tasa 0, `ivadif` del contrato, M9), la **cantidad a origen** en `canoriori` y la
**cadena** con la proforma anterior (M11).

Por eso **no se escribe un caso de uso nuevo desde cero**: se reutiliza el núcleo de F-009 (la parte probada en
producción, con su campaña de mutación) con un **perfil de alta** que fija lo que cambia (D6). Ruta propia, segunda
llave propia y listas propias: el contrato HTTP de `sigrid/albaran`, congelado con albaranes (§2-§4 de
`contrato_albaranes.md`), no cambia.

**Límite de microservicio: cabe.** Dar de alta un concepto del ERP con sus efectos (stock, contrato servido,
retención y totales) es de la pasarela, y Sigrid no tiene triggers. Qué se certifica, a qué precio y cuándo lo decide
el llamante (D1). Fuera, por ser de otros: la facturación (F-008), la contabilización (asiento `tip 20`, M1) y el
vínculo incidencia ↔ coste, que es de `postventa-incidencias` F-047.

**Lo que dice la medición sobre posventa (M13), y por eso D1 bloquea:** el coste de posventa entra hoy en la obra
**POSTV2 como albarán `AC`** (1.283 desde 2025) con la partida = capítulo = promoción, y solo 3 proformas en toda su
historia; Sigrid no tiene ningún campo que una un parte (`rcp`) con un documento de compra. F-009 ya da de alta esos
albaranes, y el vínculo con la incidencia puede viajar hoy en `referencia_linea` (`dcapro.refent`, 24 caracteres) o
en `referencia_externa` (`synckey`). La proforma real es otra cosa: la **certificación mensual de un subcontratista**
en una obra en construcción (0678, 0672, 0677…).

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/proforma_models.py` | domain | `ProformaRequest(AlbaranCompraRequest)`: solo redefine `fecha_albaran` con `alias="fecha_proforma"` (mismo dominio; `extra="forbid"` rechaza `fecha_albaran`). La respuesta es `AlbaranCompraResponse` (su `filas` ya es un `dict`) |
| `application/use_cases/proforma_statements.py` | application | SQL constante L5P, L16, E13-E15 (§Sentencias) y puras `retencion_soportada`, `construir_dcarec`, `totales_con_retencion`, `ajustar_dca_proforma`, `ajustar_dcapro_proforma`, `es_proforma`. Sin E/S; se autovalida con `DatabaseReferenceGuard` |
| `application/use_cases/create_proforma_use_case.py` | application | `CreateProformaUseCase(CreateAlbaranCompraUseCase)`: fija `perfil=PERFIL_PROFORMA`; no reimplementa el flujo |
| `tests/test_f007_dorado_extendido.py` + `tests/fixtures/f007_dorado_extendido.json` | — | R22 (T1, sobre `dev`, antes de tocar nada) |
| `tests/test_f007_settings.py`, `_models.py`, `_statements.py`, `_use_case.py`, `_route.py`, `_perfil.py` | — | Ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `application/use_cases/albaran_compra_statements.py` | `PerfilAlta` (dataclass congelada, §Perfil) y `PERFIL_ALBARAN` con los valores de hoy; `prefijo_de_serie(fecha, prefijo=PREFIJO_SERIE)`; `construir_dcapro_vinculada` y `_sin_vincular` reciben la regla de `canoriori`/`imporiori` (defecto: la de hoy). Ninguna constante SQL de F-009 cambia |
| `application/use_cases/create_albaran_compra_use_case.py` | `__init__(…, perfil: PerfilAlta = PERFIL_ALBARAN)`. Lo que hoy lee de `settings.sigrid_albaran_*` y las constantes `_ENDPOINT`, `APPLOCKS` y prefijo, lo lee **del perfil**; cinco ganchos que con `PERFIL_ALBARAN` no hacen nada (§Ganchos) |
| `domain/models/albaran_compra_models.py` | Los tres códigos nuevos de R4 en el conjunto cerrado de `AlbaranCompraError` (aditivo) |
| `config/settings.py` | Los cinco campos de R2 con `parse_string_list` y `parse_string_dict` de F-009 |
| `function_app.py` | Ruta `sigrid/proforma` (POST) con el esqueleto de `sigrid_albaran` extendido: `ProformaRequest.model_validate`, guarda R5 tras validar y antes del caso de uso (solo con `commit`), `CreateProformaUseCase(repository, settings)` construido en la ruta como F-006 (sin tocar la tupla de `build_dependencies`), `AlbaranCompraError` → 400 con `codigo`. Ninguna ruta existente cambia |
| `local.settings.sample.json`, `docs/ARCHITECTURE.md`, `CLAUDE.md` (mapa de rutas) | Claves, ruta, perfil y caso de uso nuevos |
| `azure-apps/sigrid_api.md` | R27, commit aparte en `azure-apps`; corrige también que `tip 20` es el asiento |

## Ficheros que NO se tocan

`create_purchase_albaran_use_case.py`, `create_direct_albaran_use_case.py` y sus modelos; los tests y el dorado de
F-009 (`test_f009_*`, `f009_caracterizacion.json`); `infrastructure/security/*`; `sql_server_repository.py` (bastan
`execute_read_query`, `read_full_row`, `read_rows_by`, `locate_contract`, `peek_next_ide` y `run_in_write_transaction`);
F-004 y F-006; `infra/`; `contrato_albaranes.md`. Sin ficheros `NN_nombre.sql`: SQL constante.

## Perfil (D6)

```python
@dataclass(frozen=True)
class PerfilAlta:
    endpoint: str                    # "sigrid/albaran" | "sigrid/proforma" (trazas)
    prefijo_serie: str               # "AC" | "PROF"
    applocks: tuple[str, ...]        # el de F-009 | el mismo con "SIGRID_IDE_dcarec" antes de "SIGRID_IDE_log"
    llave: str                       # nombre del campo de Settings: sigrid_albaran_write_enabled | sigrid_proforma_write_enabled
    codigo_llave: str                # "escritura_albaranes_deshabilitada" | "escritura_proformas_deshabilitada"
    prefijos: str; productos: str; naturalezas: str; max_lineas: str   # nombres de campos de Settings (R2)
    proforma: bool                   # activa los ganchos de §Ganchos
```

`PERFIL_ALBARAN` reproduce **exactamente** lo de hoy (los literales que hoy están en el código pasan al perfil, sin
cambiar valor). Los nombres de campos se resuelven con `getattr(settings, …)` en un único método del caso de uso; un
test comprueba que todos existen en `Settings` (un error de nombre rompería al arrancar, no en producción).

## Ganchos del núcleo (solo con `perfil.proforma`)

1. **Plantilla de cabecera (R7)**: en lugar de L5, L5P; sin fila, `proveedor_sin_proforma_previa`.
2. **Retenciones (R11, R12)**: tras resolver el contrato, L16; `retencion_soportada` rechaza `reccla` ≠ 5 antes de
   las líneas. Sin contrato o sin filas, ninguna retención.
3. **Construcción (R9, R10, R13)**: tras las funciones de F-009, `ajustar_dca_proforma` y `ajustar_dcapro_proforma`
   (puras, sobre el `dict`); `totales_con_retencion` sustituye `tot`/`totpag` de la `dca` y `construir_dcarec` añade
   `filas["dcarec"]` (en previa con `ide` provisional de `peek_next_ide("dcarec")`).
4. **Transacción (R17, R18, R20)**: E13 reserva `dcarec.ide` tras `mov`, E14 inserta tras los `mov` y antes del `log`,
   E15 cuenta en las relecturas. Todo dentro del mismo `work` reentrante (los reintentos lo reconstruyen).
5. **Idempotencia (R21)**: L11P en lugar de L11, y también como E1 dentro de la transacción; `es_proforma` (con
   `d.cla` y `c.cod`) decide entre `idempotente` y `referencia_en_conflicto`. Con `PERFIL_ALBARAN`, L11 y el
   resultado de hoy (R22; ver Riesgos).

## Filas que se escriben (las de F-009, salvo)

- **`con`** (R8): `cod` `PROF<aa>/NNNNN` (E2 de F-009 con el prefijo del perfil; 5 cifras como `AC`, M1); `res`, `est`
  1 y `log` como F-009 (M2).
- **`dca`** (R9): plantilla = la última proforma del proveedor (L5P); overrides de F-009; `cla` 141; `ivadif` =
  `ctr.ivadif` (0 sin contrato); `docoritip` 1 con contrato, 0 sin él; `docoriide` 0; reseteo de facturación y cadena
  (lista de R9; M4 y M15: si se clonaran, la proforma nacería «facturada» en la ficha). `tot`/`totpag` de R13.
- **`dcapro`** (R10): las de F-009 con `canoriori` = `can` (con signo), `canorilin` y `canoriant` 0, `imporiori` =
  `ctrpro.tot` (vinculadas; F-009 pone `canoriori` = `ctrpro.can`, que es la regla del albarán, M11) y 0 sin vincular.
- **`dcarec`** (R11): una por `ctrrec`, columnas de R11; `bas` = `totbas`; `cuo` = `redondear_euros(bas·valpor)`
  (`Decimal`, `ROUND_HALF_UP`, F-009 H33); `ivacuo`/`reqcuo` 0; `ide` de E13, consecutivos.
- **`ctrprodes`, `mov`, `ctrpro`, `ctr`**: como F-009 (M6, M7); productos y naturalezas, de las listas de R2 (M8).

## Sentencias nuevas (`proforma_statements`; todas con `?`)

- **L5P** `SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = ? AND c.emp = ? AND
  d.entide = ? AND d.cla = ? AND c.cod LIKE ? ORDER BY c.ide DESC` (`[14, emp, entide, 141, 'PROF%']`); sin contrato,
  la variante con `d.entcif = ?` (como L5 de F-009).
- **L16** `SELECT ide, recide, pos, valdef, valpor, valcan, valmod, valfij, reccla, cueide, ivaide, tex, resalt,
  refide, frasupide, item FROM dbo.ctrrec WHERE docide = ? ORDER BY pos, ide`.
- **L11P** = L11 de F-009 con `d.cla` añadida a la lista de columnas (solo en el perfil proforma; la de F-009 no cambia).
- **E13** `SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcarec WITH (UPDLOCK, HOLDLOCK)`; **E14** `INSERT INTO dbo.dcarec
  (<columnas>) VALUES (?, …)`; **E15** `SELECT COUNT(*) FROM dbo.dcarec WHERE docide = ?`.

## Flujo

1. Guardas sin leer la base (R16) con los campos del perfil; con `commit`, llaves, credenciales y base.
2. `ahora` (Madrid) una vez; obra, contrato, **L16 y R12**, L5P, L11P (R21 sale ya si aparece), `conest` y `usu`.
3. Líneas como F-009 (todos los fallos juntos), con la lista blanca y el mapeo del perfil.
4. Construcción pura (F-009 + ganchos 3) → en dry-run, `previsto` con `cod` e `ide` provisionales (también `dcarec`).
5. Con `commit`, `run_in_write_transaction(work)` con `perfil.applocks`; reintentos → `colision_de_clave`.
6. Traza R24 (con `perfil.endpoint` y nº de retenciones) y respuesta.

## Decisiones (abiertas para el humano; recomendación en negrita)

- **D1 · Consumidor y propósito (bloquea la implementación).** ¿Quién llamará a `sigrid/proforma` y para qué? Si es
  `postventa-incidencias` para el coste de posventa, la medición dice que ese coste es un **albarán en POSTV2** (M13) y
  que F-009 ya lo cubre: **recomendación: confirmarlo con negocio; si no hay un llamante de proformas reales, aplazar
  F-007 con esta spec congelada y resolver F-046/F-047 con F-009** (`referencia_linea` = código del parte).
- **D2 · Encadenamiento a origen.** **Fuera de F-007** (cada proforma nace «primera de su cadena»: `docoriide` 0,
  `canoriori` = `can`; estado medido en 442 de las 1.216 proformas de 2026) y, si el llamante lo necesita, F-007b con un campo
  `proforma_anterior` (cadenas paralelas por partida, M11: la cadena no se puede deducir). Consecuencia: la columna
  «a origen» de la impresión solo muestra el periodo; el servido del contrato y los importes son correctos.
- **D3 · Retención.** **Copiar `ctrrec` a `dcarec` y descontarla de `tot`/`totpag`** (M10: 95 % de las proformas con
  contrato y `ctrrec`); solo `reccla` 5; otra clase → `retencion_no_soportada` (RET5T e IRPF: 7 proformas en 2026).
- **D4 · `ivadif` y `docoritip`.** **`ivadif` del contrato** (91,2 %); **`docoritip` 1 con contrato** — no sale de los
  datos (140 frente a 232), se confirma con V1 antes del primer commit.
- **D5 · Plantilla.** **Solo la última proforma del proveedor**, sin caer a un albarán (como H3 de F-009).
- **D6 · Reutilización.** **Perfil en el núcleo de F-009** con dorado previo (R22). Alternativas descartadas abajo.
- **D7 · Configuración.** **Listas propias** (R2), con `SB9999`/`SM9999` como productos sin contrato (M7-M8; los dos
  con `tipmov` 1 y naturaleza única); `SM370001` (`tipmov` 0, varias naturalezas) queda fuera salvo decisión; **obra en
  `SIGRID_ALBARAN_EMPRESAS_OBRA`**, que significa lo mismo.

## Riesgos y decisiones

- **Tocar el núcleo de F-009 (crítico, en producción con la llave abierta).** Mitigación: dorado del modo extendido en
  T1 sobre `dev`; los tests de F-009 no se tocan; el perfil por defecto es literal al código de hoy; campaña de mutación
  sobre todo lo cambiado. Avisar a la sesión de albaranes **antes** de mergear (no cambia su contrato, sí el código que
  la sirve).
- **Doble alta**: `synckey` re-comprobado dentro bajo `SIGRID_REFEXT_14`; los prefijos de referencia distintos
  (`ALB-`/`PRF-`) separan albaranes y proformas. El modo extendido de `sigrid/albaran` seguiría devolviendo como
  `idempotente` una proforma con su misma referencia (comportamiento de hoy, R22): lo evita la configuración.
- **Colisión con el escritorio**: índice único `(emp, tip, cod)` + reintento, como F-009. Applocks en el orden de F-009
  con `_dcarec` insertado antes de `_log`: ningún endpoint los toma en orden inverso.
- **Retención mal calculada**: 93,9 % de coincidencia exacta de `cuo` medida (el resto, redondeos y signos de filas
  antiguas); el humano lo revisa en la ficha en R26.
- **O1 (F-009, fuera de alcance, para el líder):** la L5 de F-009 no filtra serie y en 17 de 831 proveedores el
  último `dca` es una proforma (M14): el albarán nacería con `cla 141`, `docori*` y fechas de factura clonadas.
- **O2 (F-009, fuera de alcance, para el líder):** F-009 no escribe `dcarec`; el 88,5 % de los albaranes de la UI de
  contratos con `ctrrec` la llevan (M10), así que un albarán del pipeline de esos contratos nace sin retención y con
  `tot` = `totdoc`. O1 y O2 merecen su feature antes de que F-053 de albaranes pase a real (`synckey` 0 % hoy).
- **Descartado**: modo nuevo dentro de `sigrid/albaran` (reabre el contrato congelado con albaranes); copiar el caso de
  uso de F-009 (~1.300 líneas duplicadas en una pieza crítica); plantilla de un albarán sin proforma previa (D5);
  calcular la cadena por fecha o por contrato (M11: hay cadenas paralelas); escribir `med`/`canmed` (lo teclea el
  usuario); la regla de `canoriori` del albarán (M11).
