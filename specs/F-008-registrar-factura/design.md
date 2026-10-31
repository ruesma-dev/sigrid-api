<!-- specs/F-008-registrar-factura/design.md -->
# F-008 · Diseño: `POST /api/sigrid/factura` (v3.1)

Requisitos: [`requirements.md`](requirements.md). Mediciones: [`explore_F-008.md`](../../progress/explore_F-008.md) (M52-M74).

## 1. Respuesta corta

| Pregunta | Respuesta (medida) |
|---|---|
| ¿Qué escribe Sigrid al registrar? | `con` tip 15, `dcf` (`cla` 1001), `dcfpro` ×N, `dcfrec` ×0-1, `con` 25 + `pag` ×M, `consii`, `log` (M52, M53, M58) |
| ¿Y la contabilidad? | **No está en el alta**: 0 asientos y 0 `regiva` en REC/COM ni en COMGG. La hace «Contabilizar» (M53, M55, M67). Fuera (P1) |
| ¿FRGG? | **Dentro, con y sin orígenes** (P11, P18). La cuenta de gasto es `dcfpro.cueide`, fijada **en el alta** y leída por «Contabilizar» (99,5 %, M65): en las líneas propias la manda el llamante con la analítica; las de albarán son idénticas a FR (M69). **No hay que escribir contabilidad** |
| ¿De dónde salen las líneas? | De albaranes o proformas (copia de `dcapro`), del llamante (sin origen), o mixtas, en las dos series (M61, M71) |
| ¿A origen? | Modo de los albaranes (`dca.docoritip 1`). La API calcula por la regla de M63 y **compara** con lo que manda el llamante (P14) |
| ¿Vencimientos? | Los manda el llamante; la API valida, no calcula (P12, P13) |
| ¿Quién llama? | Apps con prefijo en configuración y `usu` válido; al desplegar, solo `facturas` (P15) |

## 2. Encaje en la arquitectura

Patrón de `sigrid/proforma`: ruta en `function_app.py`, modelo Pydantic, caso de uso que valida con lecturas y ejecuta en
`run_in_write_transaction` un trabajo reentrante, y módulos puros de sentencias y filas. **No hereda** de
`CreateAlbaranCompraUseCase`: importa funciones sueltas de `albaran_compra_statements` (producto, naturaleza, partida,
analítica, almacén, `importe_linea`, `sellos_del_alta`) para las líneas FR sin origen, sin editarlo.

Flujo: el llamante concilia y un humano aprueba → `sigrid/factura` da de alta en REC (FR) o RECGG (FRGG) → Administración
comprueba y contabiliza en el escritorio. La API no sabe qué app llama: solo ve prefijo y `usu`.

## 3. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `domain/models/factura_models.py` | domain | `FacturaRequest`, `LineaSinOrigen`, `EntradaAOrigen`, `Vencimiento`, `FacturaResultado`, `FacturaError(ValueError)` con `codigo`, `details` |
| `application/use_cases/factura_statements.py` | application | Lecturas `Lnn`, escrituras, listas blancas y constructores puros de filas |
| `application/use_cases/factura_lineas.py` | application | Puro: línea de origen (mes / origen + comparación, R19-R22) y **un solo** constructor de línea sin origen con atributo `serie` (R25-R28) |
| `application/use_cases/create_factura_use_case.py` | application | `CreateFacturaUseCase.run(request)` |
| `specs/F-008-registrar-factura/verificacion_manual.md` | spec | Pasos MANUAL del humano (T22-T24) |
| `tests/test_f008_*.py`, `tests/f008_dobles.py` | tests | `models`, `route`, `settings`, `statements`, `lineas`, `use_case`, `transaccion` |

## 4. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `function_app.py` | Ruta `sigrid/factura`, `_exigir_escritura_de_facturas`, manejo de `FacturaError` |
| `config/settings.py` | `SIGRID_FACTURA_WRITE_ENABLED` (False), `_PREFIJOS_REFERENCIA` ([]), `_MAX_LINEAS` (500), `_PRODUCTOS_SIN_ORIGEN` ([]), `_NATURALEZA_POR_PRODUCTO` ({}), `_IVAS` ([]), `_CUENTAS_GASTO_PREFIJOS` ([]) |
| `.env.example`, `local.settings.sample.json` | Las siete, sin valores reales |
| `docs/ARCHITECTURE.md`, `CLAUDE.md` (mapa) | Ruta, modelos, caso de uso |
| `azure-apps/sigrid_api.md` | §4, §7, §8.11 (nueva), §9.5, §10, en el mismo trabajo |

Valores de despliegue propuestos: prefijos **solo `FAC-`** (el de `facturas`, a confirmar con esa app: P15); productos `MA9999`,
`SM9999`, `SB9999`, `QA9999`, `XA9999`, `SM370001`; IVAs `I21`, `I10`, `ISP21`, `i0`, `i4`, `I21NDED`, `I10NDED` (P21); cuentas de gasto `["6"]` (P19).
Con la lista de cuentas vacía, ninguna línea propia FRGG es válida; una FRGG solo de albaranes sí entraría (como una FR).

## 5. Ficheros que NO se tocan

`infrastructure/security/*`; `albaran_compra_statements.py`, `create_albaran_compra_use_case.py`, `create_proforma_use_case.py`,
`proforma_*`, `create_purchase_albaran_use_case.py`, `attach_concepto_grafico_use_case.py` (se importan, no se editan); los
ajustes `SIGRID_ALBARAN_*` y `SIGRID_PROFORMA_*` (`SIGRID_ALBARAN_EMPRESAS_OBRA` se lee); `SIGRID_DOCUMENT_ALLOWED_CONTIP`
(P9, ajuste aparte). `domain/ports/sql_repository.py` y el adaptador no cambian.

## 6. Clases, funciones y reglas

```python
class CreateFacturaUseCase:
    def __init__(self, repository: SqlRepository, settings: Settings) -> None: ...
    def run(self, request: FacturaRequest) -> dict[str, Any]: ...

def linea_de_origen(dcapro: Mapping, anterior: Mapping | None, *, modo: str) -> dict: ...         # R17, R19, R20
def comparar_a_origen(calculadas: Sequence[Mapping], enviadas: Sequence[EntradaAOrigen]) -> None: ...  # R21, R22
def resolver_linea_fr(linea, lecturas: Mapping) -> LineaResuelta: ...      # R25: producto, naturaleza, cuenta, caa...
def resolver_linea_gg(linea, lecturas: Mapping) -> LineaResuelta: ...      # R26: cuenta, analítica y su obra
def linea_sin_origen(linea: LineaSinOrigen, resuelta: LineaResuelta, *, serie: str, almide: int,
                     tasa_iva: Decimal) -> dict: ...                                             # R27, R28
def validar_vencimientos(vencimientos, *, fecha_factura: int, totpag: Decimal) -> None: ...       # R33
def construir_con_factura(...), construir_dcf(...), construir_dcfrec(...), construir_pag(...),
    construir_consii(...), construir_dcaprodes(...) -> dict[str, Any]: ...
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
| `lineas` | lista de `LineaSinOrigen`, 0..N | comunes `descripcion`, `cantidad`, `precio`, `iva`; FR `producto`, `partida?`, `paride?`, `unidad?`; FRGG `cuenta`, `analitica` (R23) |
| `vencimientos` | lista 1..12 de `{fecha, importe}` | R32-R33 |
| `vencimiento_retencion` | fecha, opcional | solo con retención `reccla` 5 (R34) |
| `total_base`, `total_iva`, `total_factura` | decimales | `total_factura` = líquido con retención |
| `commit` | bool | `false` |

La mezcla de campos de serie (p. ej. `cuenta` en FR) la rechaza un `model_validator` (400 sin `codigo`).

**Cabecera `con`:** `tip` 15, `cod` (R37), `res` = `<entres>. (<entref>)` truncado a 128, `fec` = hoy en Madrid
(`sellos_del_alta`), `est` = REC o RECGG de `conest` según `serie`, `tiemod`, `tex` vacío.

**Cabecera `dcf`** (lista blanca; lo no listado, el vacío del tipo según T0):
- Con orígenes: del primer origen por `cod` (M57) `ent*`, `obride`, `cenide`, `almide`, `empide`, `dir*1`, `pagide`, `pagtex`,
  `pagfor`, `efeide`, `eioide`, `ivadif`, `cocide`, `tipgar`, `fecent`, `feclim`, `ban*`; `ctride` del contrato de los orígenes.
- Sin orígenes, FR y FRGG (M61, M67): `ent*`, `pagide`, `efeide`, `eioide`, `ban*` del proveedor; `pagfor`/`pagtex` de `auxpag`;
  `obride`, `cenide`, `almide` de la obra de cabecera; `ctride` 0.
- Siempre: `cueide` = `prv.cueide`, `cla` 1001, `synckey`, `hor` del sello, totales de R29; `estfac`, `estser`, `estped`,
  `docoritip`, `docoriide`, `facoriide`, `fecpag` 0.

**Líneas de origen** (iguales en las dos series, M69): R17 + `cueide` = `prv.cuepdtide`; `pos` múltiplo de 64 (primero las de origen por orden de `origenes` y
`dcapro.pos`, luego las sin origen en el orden de la petición). Columnas a origen:

| Modo | `canoriori` | `canoriant` | `imporiant` | `imporiori` |
|---|---|---|---|---|
| mes | `can` | 0 | 0 | `tot` |
| origen, vinculada | `dcapro.canoriori` | `canoriori` de la anterior | `imporiori` de la anterior | `dcapro.imporiori` |
| origen, sin vincular | `dcapro.canoriori` | ídem | ídem | `imporiant` + `tot` |

«Anterior» = la `dcapro` de `dcapro.canorilin` (lectura propia); sin ella, 0. En modo origen, `comparar_a_origen` casa cada
entrada de `a_origen` con su línea por `dcapro.ide` y compara `canoriori` (±0,001) e `imporiori` (±0,01) (P14). Se escribe lo
calculado, que coincide con lo enviado dentro de la tolerancia.

**Líneas sin origen: un solo camino** (P18). La serie solo elige el resolvedor; los dos devuelven la misma `LineaResuelta`
(dataclass de `factura_lineas.py`: `proide`, `natide`, `paride`, `cueide`, `caaide`, `obride`, `cenide`, `almide` o `None`,
`ivaide`, `tasa_iva`), y `linea_sin_origen` construye la fila igual para las dos (R28; `almide` `None` → el de `dcf`). Una
factura mixta FRGG con albaranes (M71) son líneas de origen más líneas de estas: no hay tercer camino.
- `resolver_linea_fr`: producto por `(emp, cod)` y lista blanca; naturaleza por el mapeo; `cueide` = la `cua` de `cuacomcod`;
  partida, almacén, centro y `caaide` con las funciones de F-009.
- `resolver_linea_gg` (M65-M66): `cuenta` → `con` `tip 17` de la empresa con `cua.niv` 5 y prefijo permitido; `analitica` → `con`
  `tip 19` de la empresa sin hijas en `caa`, cuyo texto antes del primer `.` es el `cod` de una obra de la empresa; de esa obra,
  `obride` y `cenide` (`obr.cenide`); `almide` `None`; `proide`, `paride`, `natide` 0.
- Los dos: `ivaide` del código `iva` (los NDED, como cualquier otro: M72-M73). Fallos juntos en `lineas_no_validas`.

**Vencimientos** (`validar_vencimientos`): fechas reales con `datetime.date`, en [`fecha_factura`, +730 días], sin repetir;
Σ `importe` = `totpag` ±0,01. **`pag`**: `cla` 0, uno por vencimiento, `tot` = su `importe`, `fecven` = su `fecha`; `efeide`,
`cueide`, `entide`, `cenide`, `entref`, `ban*` de `dcf`. `cla` 2: `tot` = `cuo`, `retide` = `recide`, `cueide` = `dcfrec.cueide`,
`fecven` = `vencimiento_retencion`. `con`: `tip` 25, `cod` `<cod>_NN` (cla 0 primero), `res` `Pago i de n <res>`, `fec` =
`con.fec`, `est` PDT.

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

Previa: lecturas con `execute_read_query` y construcción sin escritura. Orden de validación: cuerpo → llaves → prefijo y `usu`
→ obra y proveedor → orígenes y modo → `a_origen` → líneas sin origen (fallos juntos) → totales → retención → vencimientos →
duplicadas.

Commit: `run_in_write_transaction` con applocks **en este orden fijo**, compatible con los existentes (`_con` antes y `_log` al
final): `SIGRID_REFEXT_15`, `SIGRID_SERIE_15` (uno para las dos series), `SIGRID_IDE_con`, `SIGRID_IDE_dcfpro`,
`SIGRID_IDE_dcaprodes`, `SIGRID_IDE_dcfrec`, `SIGRID_IDE_pag`, `SIGRID_IDE_consii`, `SIGRID_IDE_log`.

Dentro, reentrante: (1) re-comprobar R43; (2) releer con `WITH (UPDLOCK, HOLDLOCK)` `dcapro` y `dca` de los orígenes y repetir
R14-R15 y la comparación de R22 (el escritorio no toma nuestros applocks); (3) reservar `cod` e `ide` (`pag` comparte `ide` con
su `con`); (4) `INSERT`s; (5) `UPDATE`s; (6) relectura R45. El `work` no calcula con estado de intentos anteriores. Una factura
sin orígenes, de cualquier serie, salta (2) y (5).

## 8. Riesgos y decisiones

- **LÍMITE DE MICROSERVICIO.** Cabe el alta de FR y FRGG (mes, origen, mixta, sin origen): mismas tablas, mismo
  tipo de escritura que el albarán. **No cabe** la contabilidad (P1). La v2 dejaba fuera FRGG por la cuenta de gasto; M65
  demuestra que es un campo del documento (`dcfpro.cueide`) que el escritorio fija en el alta y «Contabilizar» solo lee: la
  decisión contable la toma el llamante (un humano en su app) y la revisa Administración en «Comprobar».
- **¿Partir la feature?** No hace falta: FRGG añade un resolvedor de línea, un ajuste, dos fallos de línea y la serie/estado;
  con P18 no añade nada a las líneas de origen (M69-M71). Si el humano prefiere entregar antes FR, T6 y la parte FRGG de T2,
  T9-T11, T23 y T24 se separan en una F-0xx sin cambiar el diseño.
- **Cuenta o analítica equivocada en FRGG**: la API valida existencia, hoja, empresa y prefijo, no el acierto. Cuenta no 6xxx
  (1,7 %, inmovilizado 21xx, 46xx, 5xxx) queda fuera con `["6"]`; ampliarlo es ajuste de despliegue, no de código.
- **Cuenta y analítica de la FR sin origen.** Reproducen el escritorio en el 96,1 % y el 85,6 % (M61); el resto lo corrige
  Administración en «Comprobar» (V6), como en F-009.
- **Cabecera sin origen desde el proveedor**: `ban*` coincide solo en el 58-74 % (M61). Se acepta: la `pag` nace en PDT, fuera
  de remesas, y se revisa en «Comprobar».
- **IRPF en FRGG sin orígenes** (4,7 %, M67) queda fuera (P20). La API no lo detecta: depende de que el llamante no las mande.
  Si las manda con `total_factura` líquido, `totales_no_cuadran` las para; con el bruto, entrarían sin retención. Con orígenes,
  la retención la copia R31 del albarán en las dos series, sin que nadie la elija (3 FRGG26 con IRPF del 15 %, M71).
- **IVA no deducible** (P21): el llamante decide la deducibilidad con el código; en el alta un NDED solo cambia `ivaide` (cuota
  completa en `ivacuo` y `totiva`, `consii` igual: M72-M73). Lo no deducible lo trata «Contabilizar». En FR nunca se ha usado.
- **Vencimientos del llamante**: se valida forma, rango y suma, no el acierto. «Regeneración de vencimientos» del escritorio
  (M64) puede reescribirlos: V3.
- **A origen comparado** (P14): las 39 líneas de 7.123 (0,5 %) en que el escritorio se apartó de la regla (correcciones a mano)
  darán `a_origen_no_cuadra` si el llamante las copió de otra fuente; es lo buscado: no se registra lo que no se entiende.
- **Exigir el origen contabilizado** (P4) sigue. **Clonar la cabecera** se descarta (F-015); listas blancas. **`dca.idefac`** no
  se escribe (M54). **Reversión:** no hay; un alta equivocada se anula en el escritorio, nunca con `DELETE` (V4).
- **Carrera con el escritorio:** `UPDLOCK` y `UPDATE` condicionado a `canfac` = 0; el índice `con_emptipcod` obliga a reintentar.
- **Permisos (V1):** si `user_rw` no tiene `UPDATE` de `con`, `dca`, `dcapro`, la primera grabación falla con ROLLBACK (T22).
- **Varios llamantes:** un prefijo por app; dos apps con el mismo prefijo se pisarían la idempotencia. Al desplegar, uno solo.

## 9. Decisiones del humano

**v1, aprobada el 2026-10-30** (P1-P10 = la *Recomendada*; texto en `git show 1a3e739:specs/F-008-registrar-factura/design.md`).
**Se mantienen:** P1 (alta sin contabilidad), P2 (`pag` y `consii`), P4 (origen sin contabilizar rechazado), P6 (orígenes
enteros), P9 (PDF por `concepto-grafico`), P10 (factura del proveedor). Cambiaron: P3 → P12-P13; P5 → P14; P7 → P11; P8 → P15.

**v2 → v3: decididas por el humano el 2026-10-30** (texto de la v2 en `git show 8483e29:specs/F-008-registrar-factura/design.md`):

| P | Decisión | Dónde |
|---|---|---|
| P11 | **Incluir FRGG** (no la recomendada). Medido: la cuenta se fija en el alta, no exige contabilidad (M64-M68) | R9, R23, R26-R27 |
| P12 | Recomendada: 1-12 `{fecha, importe}`, Σ = `totpag` ±0,01, fechas en [factura, +730 días]; `vencimiento_retencion` con garantía | R32-R34 |
| P13 | Recomendada: fuera la regla del 77 %, sin aviso | R35 |
| P14 | **Los manda el llamante** (no la recomendada): `a_origen` por línea; la API compara con M63, `canoriori` ±0,001 e `imporiori` ±0,01. Si no cuadran, **error** `a_origen_no_cuadra` (recomendado frente a aviso: un aviso dejaría escrita una cadena que contradice al albarán, y el que llama puede corregir y reenviar) | R21-R22 |
| P15 | Mecanismo genérico `SIGRID_FACTURA_PREFIJOS_REFERENCIA`; desplegado **solo con el prefijo de `facturas`** | R6, §4 |
| P16 | Recomendada: mapeo propio de naturaleza por producto (solo FR) | R25 |
| P17 | Recomendada: IVA del llamante limitado a `SIGRID_FACTURA_IVAS` | R24 |

**Qué cambió de la v2 a la v3:** `serie` nueva y FRGG sin orígenes (RECGG, `FRGG<aa>/` + 4 cifras); líneas FRGG con `cuenta` y
`analitica`; `a_origen` comparado; ajuste `_CUENTAS_GASTO_PREFIJOS`; errores nuevos `a_origen_incompleto`, `a_origen_no_cuadra`,
`cuenta_no_valida`, `analitica_no_valida`; requisitos renumerados (R1-R48); `log` sin cuentas.

**v3 → v3.1: decididas por el humano el 2026-10-30** (texto de la v3 en `git show 180688d:specs/F-008-registrar-factura/design.md`):

| P | Decisión | Dónde |
|---|---|---|
| P18 | **FRGG con albaranes o proformas, como las mixtas de FR** (no la recomendada). Medido: sus líneas de origen son las de FR (`cueide` = `prv.cuepdtide` 904 de 904; analítica y obra del albarán), y cabecera, marcas, `consii` y `pag` también (M69-M71) | R2, R13, §6 |
| P19 | Recomendada: `cuenta` y `analitica` obligatorias en la línea propia FRGG; cuenta hoja con prefijo configurable (`["6"]`); analítica hoja con obra de la empresa | R26-R27 |
| P20 | Recomendada: IRPF fuera de F-008 (sin orígenes); el que trae el albarán lo copia R31 | R31, §8 |
| P21 | **Incluir `I21NDED` e `I10NDED`** (no la recomendada), mandados por el llamante. Medido: no cambian nada más del alta (M72-M73) | R24, §4 |

**Qué cambió de la v3 a la v3.1:** FRGG admite `origenes` (fuera la regla de R2 que lo rechazaba); las líneas de origen y las
marcas valen para las dos series; las líneas sin origen pasan a un solo constructor (`linea_sin_origen`) con dos resolvedores por
serie; IVAs desplegados con los NDED; cobertura FRGG26 de 82,5 % a 87,2 % (M74). **Sin preguntas pendientes.**
