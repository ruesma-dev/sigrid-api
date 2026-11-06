<!-- specs/F-008-registrar-factura/design.md -->
# F-008 · Diseño: `POST /api/sigrid/factura` (v3.2, enmienda 1)

Requisitos: [`requirements.md`](requirements.md). Mediciones: [`explore_F-008.md`](../../progress/explore_F-008.md) (M52-M74), M75-M76 (§8).

## 1. Respuesta corta

| Pregunta | Respuesta (medida) |
|---|---|
| ¿Qué escribe Sigrid al registrar? | `con` tip 15, `dcf` (`cla` 1001), `dcfpro` ×N, `dcfrec` ×0-1, `con` 25 + `pag` ×M, `consii`, `log` (M52, M53, M58) |
| ¿Y la contabilidad? | **No está en el alta**: 0 asientos y 0 `regiva` en REC/COM ni en COMGG. La hace «Contabilizar» (M53, M55, M67). Fuera (P1) |
| ¿FRGG? | **Dentro, con y sin orígenes** (P11, P18). La cuenta de gasto es `dcfpro.cueide`, fijada **en el alta** y leída por «Contabilizar» (99,5 %, M65): en las líneas propias la manda el llamante con la analítica; las de albarán son idénticas a FR (M69). **No hay que escribir contabilidad** |
| ¿Líneas? | De albaranes o proformas (copia de `dcapro`), del llamante (sin origen; FR con producto o con cuenta), o mixtas (M61, M71) |
| ¿A origen y vencimientos? | Los manda el llamante; la API calcula por M63 y **compara** (P14) y valida vencimientos sin calcular (P12-P13) |
| ¿Naturaleza? | Enmienda 1: la forzada para `<emp>:<producto>` si la hay; si no, la de la ficha (`pro.natide`), en FR y en `sigrid/albaran` |

## 2. Encaje en la arquitectura

Patrón de `sigrid/proforma`: ruta en `function_app.py`, modelo Pydantic, caso de uso que valida con lecturas y ejecuta en
`run_in_write_transaction` un trabajo reentrante, y módulos puros de sentencias y filas. **No hereda** de
`CreateAlbaranCompraUseCase`: importa funciones sueltas de `albaran_compra_statements` (producto, naturaleza, partida,
analítica, almacén, `importe_linea`, `sellos_del_alta`) para las líneas FR sin origen. La enmienda 1 añade allí la lectura de
la ficha y la elección mapa/ficha (`naturalezas_elegidas`), que usan las dos rutas: una sola regla, en el módulo de F-009.

Flujo: el llamante concilia y un humano aprueba → alta en REC o RECGG → Administración comprueba y contabiliza. La API solo ve
prefijo y `usu` (P15: al desplegar, solo `facturas`).

## 3. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `domain/models/factura_models.py` | domain | `FacturaRequest`, `LineaSinOrigen`, `EntradaAOrigen`, `Vencimiento`, `FacturaResultado`, `FacturaError(ValueError)` con `codigo`, `details` |
| `application/use_cases/factura_statements.py` | application | Lecturas `Lnn`, escrituras, listas blancas y constructores puros de filas |
| `application/use_cases/factura_lineas.py` | application | Puro: línea de origen (mes / origen + comparación, R19-R22) y **un solo** constructor de línea sin origen con atributo `serie` (R25-R28) |
| `application/use_cases/create_factura_use_case.py` | application | `CreateFacturaUseCase.run(request)` |
| `specs/F-008-registrar-factura/verificacion_manual.md` | spec | Pasos MANUAL del humano (T22-T24) |
| `tests/test_f008_*.py`, `tests/f008_dobles.py` | tests | `models`, `route`, `settings`, `statements`, `lineas`, `use_case`, `transaccion` |
| `tests/test_f008_naturaleza_albaran.py` | tests | Enmienda 1 en `sigrid/albaran`: forzado, ficha, rechazos, proforma intacta (R49-R51, R53) |

## 4. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `function_app.py` | Ruta `sigrid/factura`, `_exigir_escritura_de_facturas`, manejo de `FacturaError` |
| `config/settings.py` | `SIGRID_FACTURA_WRITE_ENABLED` (False), `_PREFIJOS_REFERENCIA` ([]), `_MAX_LINEAS` (500), `_PRODUCTOS_SIN_ORIGEN` ([]), `_NATURALEZA_POR_PRODUCTO` ({}), `_IVAS` ([]), `_CUENTAS_GASTO_PREFIJOS` ([]). Enmienda 1 (R54): `sigrid_factura_` y `sigrid_albaran_naturaleza_forzada` (alias `SIGRID_*_NATURALEZA_FORZADA`, `{}`), validador `parse_naturaleza_forzada` (§6); se **retiran** los campos `sigrid_factura_` y `sigrid_albaran_naturaleza_por_producto` (el de proforma se queda) |
| `.env.example`, `local.settings.sample.json` | Las siete, sin valores reales; enmienda 1: las dos `_FORZADA` en lugar de las dos viejas |
| `docs/ARCHITECTURE.md`, `CLAUDE.md` (mapa) | Ruta, modelos, caso de uso |
| `azure-apps/sigrid_api.md` | §4, §7, §8.11 (nueva), §9.5, §10; enmienda 1: §4 (mapeos = forzado), §8.6 y §8.11 |
| `application/use_cases/albaran_compra_statements.py` | Enmienda 1: `L15D_NATURALEZA_DE_FICHA`, `leer_naturalezas_de_ficha`, `naturalezas_elegidas` (§6) |
| `application/use_cases/create_albaran_compra_use_case.py` | Enmienda 1: `PerfilAlta.naturaleza_de_ficha: bool = False` (`PERFIL_ALBARAN` True y `campo_naturalezas` = `sigrid_albaran_naturaleza_forzada`); `_Catalogo._leer_naturalezas` con `naturalezas_elegidas`; mensaje por origen |
| `factura_models.py`, `factura_lineas.py`, `create_factura_use_case.py` | Enmienda 1: R23 (FR con `cuenta`), ficha (R49-R50), resolvedor por línea (R52) |
| `specs/F-009-alta-albaran-compra/contrato_albaranes.md` | Enmienda 1: H34 revisado, §2.2 y fila de `naturaleza_no_valida` (sin código nuevo); antes, aviso a `albaranes` |

Despliegue: prefijos **solo `FAC-`** (P15); productos `MA9999`, `SM9999`, `SB9999`, `QA9999`, `XA9999`, `SM370001`; IVAs `I21`, `I10`,
`ISP21`, `i0`, `i4`, `I21NDED`, `I10NDED` (P21); cuentas `["6"]` (P19; vacía, ninguna línea con `cuenta` es válida); forzadas, T34.

## 5. Ficheros que NO se tocan

`infrastructure/security/*`; `create_proforma_use_case.py`, `proforma_*`, `create_purchase_albaran_use_case.py`,
`create_direct_albaran_use_case.py` (P22), `attach_concepto_grafico_use_case.py`; de F-009, todo salvo lo de §4 (enmienda 1);
los ajustes `SIGRID_ALBARAN_*` y `SIGRID_PROFORMA_*` (ni nombres ni defectos; `SIGRID_ALBARAN_EMPRESAS_OBRA` se lee);
`SIGRID_DOCUMENT_ALLOWED_CONTIP` (P9). `domain/ports/sql_repository.py` y el adaptador no cambian.

## 6. Clases, funciones y reglas

```python
class CreateFacturaUseCase:
    def __init__(self, repository: SqlRepository, settings: Settings) -> None: ...
    def run(self, request: FacturaRequest) -> dict[str, Any]: ...

def linea_de_origen(dcapro: Mapping, anterior: Mapping | None, *, modo: str) -> dict: ...         # R17, R19, R20
def comparar_a_origen(calculadas: Sequence[Mapping], enviadas: Sequence[EntradaAOrigen]) -> None: ...  # R21, R22
def resolver_linea_fr(linea, lecturas: Mapping) -> LineaResuelta: ...      # R25: producto, naturaleza, cuenta, caa...
def resolver_linea_gg(linea, lecturas: Mapping) -> LineaResuelta: ...      # R26: cuenta, analítica, obra (FRGG y FR, R52)
def linea_sin_origen(linea: LineaSinOrigen, resuelta: LineaResuelta, *, serie: str, almide: int,
                     tasa_iva: Decimal) -> dict: ...                                             # R27, R28
def validar_vencimientos(vencimientos, *, fecha_factura: int, totpag: Decimal) -> None: ...       # R33
def construir_con_factura(...), construir_dcf(...), construir_dcfrec(...), construir_pag(...), construir_consii(...), ...
```

**Petición** (`FacturaRequest`, `extra="forbid"`):

| Campo | Tipo | Notas |
|---|---|---|
| `database`, `usu` (≤24), `referencia_externa` (1-128) | texto | `usu` → `log.usu`, validado en `dbo.usu` (R7) |
| `serie` | `"FR"` \| `"FRGG"` | defecto `"FR"`; las dos con o sin `origenes` (R9, P18) |
| `cif_proveedor`, `numero_factura` (1-128, a `entref`), `fecha_factura` (`AAAAMMDD`, a `fecdoc`) | | |
| `cod_obra` | texto, opcional | obligatorio sin `origenes` (R11); en FRGG, la de cabecera (`GG`, `CP` u obra, M64) |
| `modo` | `"mes"` \| `"origen"` | defecto `"mes"` (R18) |
| `origenes` | lista de `con.cod`, 0..N | albaranes o proformas `tip 14` |
| `a_origen` | lista de `{linea, canoriori, imporiori}` | solo en modo origen, una por línea facturada (R21) |
| `lineas` | lista de `LineaSinOrigen`, 0..N | comunes `descripcion`, `cantidad`, `precio`, `iva`; FR `producto`, `partida?`, `paride?`, `unidad?` **o** `cuenta`, `analitica`, `unidad?`; FRGG `cuenta`, `analitica` (R23) |
| `vencimientos` | lista 1..12 de `{fecha, importe}` | R32-R33 |
| `vencimiento_retencion` | fecha, opcional | solo con retención `reccla` 5 (R34) |
| `total_base`, `total_iva`, `total_factura` | decimales | `total_factura` = líquido con retención |
| `commit` | bool | `false` |

Un `model_validator` (400 sin `codigo`) rechaza: campo de la otra serie (`producto`, `partida`, `paride` en FRGG); en FR, una
línea con `producto` y `cuenta` o `analitica` (ambigua), con `cuenta` sin `analitica` o al revés, con `partida`/`paride` sin
`producto`, o sin ninguno de los dos juegos (`OBLIGATORIOS` deja de ser una tupla fija para FR).

**Cabecera `con`:** `tip` 15, `cod` (R37), `res` = `<entres>. (<entref>)` truncado a 128, `fec` = hoy en Madrid, `est` REC/RECGG.

**Cabecera `dcf`** (lista blanca; lo no listado, el vacío del tipo según T0):
- Con orígenes: del primer origen por `cod` (M57) `ent*`, `obride`, `cenide`, `almide`, `empide`, `dir*1`, `pagide`, `pagtex`,
  `pagfor`, `efeide`, `eioide`, `ivadif`, `cocide`, `tipgar`, `fecent`, `feclim`, `ban*`; `ctride` del contrato de los orígenes.
- Sin orígenes, FR y FRGG (M61, M67): `ent*`, `pagide`, `efeide`, `eioide`, `ban*` del proveedor; `pagfor`/`pagtex` de `auxpag`;
  `obride`, `cenide`, `almide` de la obra de cabecera; `ctride` 0.
- Siempre: `cueide` = `prv.cueide`, `cla` 1001, `synckey`, `hor` del sello, totales de R29; `estfac`, `estser`, `estped`,
  `docoritip`, `docoriide`, `facoriide`, `fecpag` 0.

**Líneas de origen** (iguales en las dos series, M69): copia de `proide`, `can`, `pre`, `tar`, `dto`, `tot`, `ivaide`, `ivacuo`,
`cenide`, `caaide`, `paride`, `natide`, `almide`, `obride`, `res`, `tex`, `cod2`, `unimed`, `prepma`, `dncide`, `dncproide` (R17),
`cueide` = `prv.cuepdtide`; `pos` múltiplo de 64 (las de origen por `origenes` y `dcapro.pos`, luego las sin origen):

| Modo | `canoriori` | `canoriant` | `imporiant` | `imporiori` |
|---|---|---|---|---|
| mes | `can` | 0 | 0 | `tot` |
| origen, vinculada | `dcapro.canoriori` | `canoriori` de la anterior | `imporiori` de la anterior | `dcapro.imporiori` |
| origen, sin vincular | `dcapro.canoriori` | ídem | ídem | `imporiant` + `tot` |

«Anterior» = la `dcapro` de `dcapro.canorilin` (lectura propia); sin ella, 0. En modo origen, `comparar_a_origen` casa cada
entrada de `a_origen` con su línea por `dcapro.ide` y compara `canoriori` (±0,001) e `imporiori` (±0,01); se escribe lo calculado.

**Líneas sin origen: un solo camino** (P18). La serie solo elige el resolvedor; los dos devuelven la misma `LineaResuelta`
(dataclass de `factura_lineas.py`: `proide`, `natide`, `paride`, `cueide`, `caaide`, `obride`, `cenide`, `almide` o `None`,
`ivaide`, `tasa_iva`), y `linea_sin_origen` construye la fila igual (R28; `almide` `None` → el de `dcf`). Sin tercer camino.
- `resolver_linea_fr`: producto por `(emp, cod)` y lista blanca; naturaleza por `naturalezas_elegidas` (R49); `cueide` = la `cua`
  de `cuacomcod`; partida, almacén, centro y `caaide` con las funciones de F-009.
- `resolver_linea_gg` (M65-M66): `cuenta` → `con` `tip 17` de la empresa con `cua.niv` 5 y prefijo permitido; `analitica` → `con`
  `tip 19` de la empresa sin hijas en `caa`, cuyo texto antes del primer `.` es el `cod` de una obra de la empresa; de esa obra,
  `obride` y `cenide` (`obr.cenide`); `almide` `None`; `proide`, `paride`, `natide` 0.
- Los dos: `ivaide` del código `iva` (los NDED, como cualquier otro: M72-M73). Fallos juntos en `lineas_no_validas`.
- **Elección por línea (R52):** en FRGG, siempre `resolver_linea_gg`; en FR, `resolver_linea_fr` con `producto` y
  `resolver_linea_gg` con `cuenta`. `_lecturas_fr` solo con las líneas con `producto` (sin ellas no se lee almacén ni producto)
  y `_lecturas_gg` solo con las de `cuenta` (hoy recorre todas: `str(None)`); se funden en una `LecturasLineas`.

**Naturaleza (enmienda 1, R49-R54)**, en `albaran_compra_statements.py`, compartida por `sigrid/albaran` y `sigrid/factura`:

```python
L15D_NATURALEZA_DE_FICHA = (
    "SELECT p.ide, p.natide, n.cod, n.numemp, n.fecbaj, n.caagascod, n.cuacomcod FROM dbo.pro p "
    "LEFT JOIN dbo.auxpronat n ON n.ide = p.natide WHERE p.ide IN {marcadores}"
)
def naturalezas_elegidas(productos: Mapping[str, int], forzadas: Mapping[str, str],
                         por_cod: Mapping[str, Sequence[Sequence[Any]]], por_proide: Mapping[int, Sequence[Any]],
                         *, emp: int) -> tuple[dict[str, Sequence[Any]], dict[str, str]]: ...
def parse_naturaleza_forzada(value: Any) -> dict[str, str]: ...   # Settings, mode="before" (R54)
```

`parse_naturaleza_forzada` reutiliza el análisis de `parse_string_dict` (solo objeto JSON, sin repetidas) y además exige clave
`<emp>:<producto>`: `emp` entero > 0 normalizado (`01:` → `1:`), `producto` de 1-24 sin espacios, valor no vacío; repetidas tras
normalizar, error. Descartado reutilizar los nombres viejos con el formato nuevo: el valor ya cargado (`"MA9999"`) tumbaría el
arranque al desplegar; y aceptar los dos formatos mezclaría un forzado global con uno por empresa sin que se vea.

`productos`: producto → `proide` (de L7, ya en lista blanca, existente y sin baja). Con `f"{emp}:{producto}"` en `forzadas`,
candidatas = filas de L15A por `cod` (la regla del mapeo viejo); si no, la fila de L15D de su `proide` sin `p.ide` (misma forma que L15A), descartada si `p.natide` es 0/NULL o
`n.cod` NULL. Válida = **una** candidata sin baja, `numemp` en {0, `emp`} y `cuacomcod` informado (la regla de hoy). Devuelve las
válidas y el origen (`"forzada"`/`"ficha"`) de todos, para el mensaje de `naturaleza_no_valida` (R50). L15D solo con los
`proide` no forzados (R53). Cuenta (L15C) y analítica (L15B), igual. En `sigrid/albaran`,
`_leer_naturalezas` la usa si `perfil.naturaleza_de_ficha`; con False (proforma), mapa por producto y sin ficha, como hoy (R51).

**Vencimientos** (`validar_vencimientos`): fechas reales con `datetime.date`, en [`fecha_factura`, +730 días], sin repetir;
Σ `importe` = `totpag` ±0,01. **`pag`**: `cla` 0, uno por vencimiento, `tot` = su `importe`, `fecven` = su `fecha`; `efeide`,
`cueide`, `entide`, `cenide`, `entref`, `ban*` de `dcf`. `cla` 2: `tot` = `cuo`, `retide` = `recide`, `cueide` = `dcfrec.cueide`,
`fecven` = `vencimiento_retencion`. `con`: `tip` 25, `cod` `<cod>_NN` (cla 0 primero), `res` `Pago i de n <res>`, `fec` =
`con.fec`, `est` PDT. **`consii`** (R38, las dos series): `tipcom` A0, `tipdoc` F1, `claope` 01, `emiter`, `facsimcua`,
`facsinide` y `difplaenv` N, `desope` = `con.res`, `regivaide` 0.

**Marcas (`UPDATE`, siempre por `ide` y con `?`):**

```sql
UPDATE dbo.dcapro SET canfac = canfac + ? WHERE ide = ? AND canfac = 0;     -- exige 1 fila (R40)
UPDATE dbo.dca SET estfac = 1, fecfac = ?, horfac = ?, antestfac = 3 WHERE ide = ? AND estfac = 0;
UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = 14 AND est = ?;          -- CON -> FAC (R41)
UPDATE dbo.ctrpro SET canfac = canfac + ? WHERE ide = ?;
UPDATE dbo.ctr SET estfac = ? WHERE ide = ?;
```

**SQL:** sin ficheros `NN_*.sql` ni esquema nuevo: SQL parametrizado en constantes de `factura_statements.py`. La reserva de
`cod` filtra por empresa y por `LIKE` del prefijo de la serie (`FR26/%` no casa `FRGG26/%`) y valida el número de cifras.

## 7. Transacción

Previa: lecturas con `execute_read_query`, sin escritura. Orden: cuerpo → llaves → prefijo y `usu` → obra y proveedor →
orígenes y modo → `a_origen` → líneas sin origen (fallos juntos) → totales → retención → vencimientos → duplicadas.

Commit: `run_in_write_transaction` con applocks **en este orden fijo**, compatible con los existentes (`_con` antes y `_log` al
final): `SIGRID_REFEXT_15`, `SIGRID_SERIE_15` (uno para las dos series), `SIGRID_IDE_con`, `SIGRID_IDE_dcfpro`,
`SIGRID_IDE_dcaprodes`, `SIGRID_IDE_dcfrec`, `SIGRID_IDE_pag`, `SIGRID_IDE_consii`, `SIGRID_IDE_log`.

Dentro, reentrante: (1) re-comprobar R43; (2) releer con `WITH (UPDLOCK, HOLDLOCK)` `dcapro` y `dca` de los orígenes y repetir
R14-R15 y la comparación de R22 (el escritorio no toma nuestros applocks); (3) reservar `cod` e `ide` (`pag` comparte `ide` con
su `con`); (4) `INSERT`s; (5) `UPDATE`s; (6) relectura R45. El `work` no calcula con estado de intentos anteriores. Una factura
sin orígenes, de cualquier serie, salta (2) y (5).

## 8. Riesgos y decisiones

- **LÍMITE DE MICROSERVICIO.** Cabe el alta de FR y FRGG (mes, origen, mixta, sin origen): mismas tablas y escritura que el
  albarán. **No cabe** la contabilidad (P1): la cuenta de gasto es un campo del documento (`dcfpro.cueide`) que el escritorio
  fija en el alta y «Contabilizar» solo lee (M65). La enmienda 1 tampoco sale: cambia de dónde se lee la naturaleza. Sin partir.
- **Cuenta o analítica equivocada (FRGG y FR sin producto, 314 líneas FR de 2026 en T23)**: se valida existencia, hoja, empresa
  y prefijo, no el acierto ni que case con una naturaleza; no 6xxx (1,7 %) queda fuera con `["6"]`. FR con producto: 96,1 % y
  85,6 % (M61); el resto, «Comprobar» (V6); `ban*` de cabecera sin origen, 58-74 % (M61). Imputar a otra obra (P4 de T23), no.
- **IRPF en FRGG sin orígenes** (4,7 %, M67) fuera (P20): con `total_factura` líquido, `totales_no_cuadran`; con el bruto, entraría
  sin retención. Con orígenes, R31 copia la del albarán (M71). **NDED** (P21): solo cambia `ivaide` (M72-M73).
- **Vencimientos y a origen del llamante**: se valida forma, rango y suma; «Regeneración de vencimientos» puede reescribirlos (V3).
  Las 39 de 7.123 líneas a origen que se apartan de M63 darán `a_origen_no_cuadra`: es lo buscado (P14).
- **Origen contabilizado** (P4), listas blancas (sin clonar), sin `dca.idefac` (M54), sin reversión (anular en el escritorio,
  nunca `DELETE`, V4). Carrera: `UPDLOCK` y `UPDATE` a `canfac` = 0. Permisos (V1, T22). Un prefijo por app.
- **Enmienda 1, medición.** M75 (líder, 2026-11-06, `pro.natide`): empresa 1 `MA9999`→`MA1501` (`MOD.CDMA15`), 31 y 34 `MA99`;
  `SM370001` en 1 `SM37`, en 34 `SM08`; los demás genéricos = el mapeo; el 75 % de las líneas de 2026 con `MA9999` imputan
  CDMA15. M76 (spec-author, `sql/read`, 2026-11-06): **desplegar ya pasa `MA9999` a la ficha** en la empresa 1, y de sus 59
  obras con albaranes de 2026, 57 tienen `<obra>.CDSB37` y 57 `<obra>.CDMA15`, ninguna la primera sin la segunda: no aparece
  ningún `analitica_no_resuelta` nuevo (31 y 34, sin albaranes en 2026). M77: la 34 no tiene FR de 2026 con obra; `SM08`
  (ficha de `SM370001` allí) lleva la misma cuenta `6060000000` que `SM37` y `MOD.CDSM08`.
- **H34 se invierte** (F-009: «el maestro tiene mal `MA9999`»): una ficha mal puesta imputa mal; mitigan forzado y «Comprobar».
- **Forzado por empresa (D2, ajuste del humano).** El producto es una ficha por empresa; un forzado global habría puesto `SM37`
  también en la 34. Con `<emp>:<producto>` deja de existir ese riesgo.
- **Desplegar cambia el resultado.** Las `_FORZADA` nacen vacías y las viejas se ignoran: manda la ficha desde el primer minuto,
  también en albaranes, que escriben con la llave abierta. Aviso a `albaranes` **antes** del despliegue; marcha atrás sin
  redesplegar: cargar `{"1:MA9999": "MA99"}` en la `_FORZADA` afectada. T34 borra las viejas y carga solo excepciones reales.
- **Código (D3).** `naturaleza_no_valida` reutilizado: `albaranes` ya lo trata como `error`; uno nuevo tocaría F-053.
- **F-009 se edita** (la v3.1 lo prohibía en R47): solo la lectura L15D, `naturalezas_elegidas` y `_leer_naturalezas`. Las
  pruebas de F-009 con producto **fuera** del mapa esperando `naturaleza_no_valida` pasan a necesitar la lectura de ficha en el
  doble: se ajustan y se listan en el informe del implementer (no se borran).
- **P22 (abierta): `albaran-directo`.** No usa ningún mapeo (copia de la última `dcapro`, sin analítica) y nadie la llama
  (obsoleta, `azure-apps` §10). **Recomendada:** no tocarla (R51); si se quiere, feature aparte.
- **P23 (abierta): proformas.** Comparten `_Catalogo` y D1 no las nombra. **Recomendada:** dejarlas igual aquí
  (`naturaleza_de_ficha` False) y decidir en una enmienda de F-007, avisando a `proformas`.

## 9. Decisiones del humano

**v1-v3.1 (2026-10-30)**, texto en `git show 1a3e739:`, `8483e29:` y `180688d:` + esta ruta. Siguen P1 (sin contabilidad), P2
(`pag`, `consii`), P4, P6, P9, P10; P11 FRGG; P12-P13 vencimientos del llamante, sin regla del 77 %; P14 `a_origen` comparado,
error si no cuadra; P15 prefijos genéricos, solo `facturas`; P16 mapeo propio (ahora forzado por empresa, D2); P17 IVA limitado; P18 FRGG
con orígenes; P19 cuenta y analítica en la línea FRGG (`["6"]`); P20 IRPF sin orígenes fuera; P21 NDED incluidos.

**v3.2, enmienda 1 (humano, 2026-11-06; v3.1 en `git show 09339e8:` + esta ruta)**, tras G1 (`FR26/11425`: la `MA9999` salió
con `0444.CDSB37` por el mapeo `MA99`; financiero: «la analítica debe salir del producto, a través de su naturaleza»):

| D | Decisión | Dónde |
|---|---|---|
| D1 | Naturaleza de la ficha (`pro.natide`, empresa de la obra) en FR y en las sin vincular de `sigrid/albaran` | R49 |
| D2 | Forzado opcional **por empresa** (`"<emp>:<producto>"`), en App Settings nuevas `_FORZADA`; las viejas dejan de leerse | R49, R53, R54 |
| D3 | Fuera del mapa y sin naturaleza válida en la ficha: rechazo con `naturaleza_no_valida` (§8) | R50 |
| D4 | FR sin producto: `cuenta` + `analitica` como FRGG; las dos a la vez, ambigua (400); ninguna, 400 | R23, R52 |
| D5 | Tras desplegar, borrar las viejas y cargar solo excepciones reales: tarea manual con autorización | T34 |

**Abiertas:** P22 (`albaran-directo`) y P23 (proformas), §8, con su recomendada aplicada en este diseño.
