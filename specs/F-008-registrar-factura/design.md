<!-- specs/F-008-registrar-factura/design.md -->
# F-008 · Diseño: `POST /api/sigrid/factura` (v2)

Requisitos: [`requirements.md`](requirements.md). Mediciones: [`explore_F-008.md`](../../progress/explore_F-008.md) (M52-M63).

## 1. Respuesta corta

| Pregunta | Respuesta (medida) |
|---|---|
| ¿Qué escribe Sigrid al registrar? | En REC: `con` tip 15, `dcf` (`cla` 1001, `FR<aa>/`), `dcfpro` ×N, `dcfrec` ×0-1, `con` 25 + `pag` ×M, `consii`, `log` (M52, M53, M58) |
| ¿Y la contabilidad? | **No está en el alta**: 0 asientos y 0 `regiva` en REC/COM. La hace «Contabilizar» (M53, M55). Fuera (P1) |
| ¿De dónde salen las líneas? | De albaranes o proformas (copia de `dcapro`), **o del llamante** (sin origen, como la sin vincular de F-009), o de las dos (mixta) (M61) |
| ¿A origen? | Es el modo de los albaranes (`dca.docoritip 1`); la factura no hace cadena propia. Columnas a origen por regla, 99,5 % (M63) |
| ¿Vencimientos? | **Los manda el llamante** (fecha e importe); la API valida, no calcula (P12, P13) |
| ¿Quién llama? | Cualquier app con prefijo de referencia en configuración y `usu` válido (P15) |
| ¿Cabe aquí? | **El alta, sí** (mismo tipo de escritura que el albarán). La contabilidad y FRGG (cuenta de gasto línea a línea), **no** (§8) |

## 2. Encaje en la arquitectura

Patrón de `sigrid/proforma`: ruta en `function_app.py`, modelo Pydantic, caso de uso que valida con lecturas y ejecuta en
`run_in_write_transaction` un trabajo reentrante, y un módulo puro de sentencias y filas. **No hereda** de
`CreateAlbaranCompraUseCase`: importa funciones sueltas de `albaran_compra_statements` (resolución de producto, naturaleza,
partida, analítica, almacén e `importe_linea`) para las líneas sin origen, sin editarlo.

Flujo: el llamante (p. ej. `facturas`, `proformas`) concilia y un humano aprueba → `sigrid/factura` da de alta en REC →
Administración comprueba y contabiliza en el escritorio. La API no sabe qué app llama: solo ve prefijo y `usu`.

## 3. Ficheros a crear

| Ruta | Capa | Qué |
|---|---|---|
| `domain/models/factura_models.py` | domain | `FacturaRequest`, `LineaSinOrigen`, `Vencimiento`, `FacturaResultado`, `FacturaError(ValueError)` con `codigo`, `details` |
| `application/use_cases/factura_statements.py` | application | Lecturas `Lnn`, escrituras, listas blancas y constructores puros de filas |
| `application/use_cases/factura_lineas.py` | application | Puro: línea de origen (modo mes / origen, R17-R19) y sin origen (R20-R23) |
| `application/use_cases/create_factura_use_case.py` | application | `CreateFacturaUseCase.run(request)` |
| `specs/F-008-registrar-factura/verificacion_manual.md` | spec | Pasos MANUAL del humano (T19-T21) |
| `tests/test_f008_*.py`, `tests/f008_dobles.py` | tests | `models`, `route`, `settings`, `statements`, `lineas`, `use_case`, `transaccion` |

`factura_vencimiento.py` de la v1 **desaparece**: no hay regla (R31).

## 4. Ficheros a modificar

| Ruta | Cambio |
|---|---|
| `function_app.py` | Ruta `sigrid/factura`, `_exigir_escritura_de_facturas`, manejo de `FacturaError` |
| `config/settings.py` | `SIGRID_FACTURA_WRITE_ENABLED` (False), `_PREFIJOS_REFERENCIA` ([]), `_MAX_LINEAS` (500), `_PRODUCTOS_SIN_ORIGEN` ([]), `_NATURALEZA_POR_PRODUCTO` ({}), `_IVAS` ([]) |
| `.env.example`, `local.settings.sample.json` | Las seis, sin valores reales |
| `docs/ARCHITECTURE.md`, `CLAUDE.md` (mapa) | Ruta, modelos, caso de uso |
| `azure-apps/sigrid_api.md` | §4, §7, §8.11 (nueva), §9.5, §10, en el mismo trabajo |

Valores de despliegue propuestos (P15-P17): prefijos uno por app (`FAC-`, `PRF-`…), productos `MA9999`, `SM9999`, `SB9999`,
`QA9999`, `XA9999`, `SM370001`; IVAs `I21`, `I10`, `ISP21`, `i0`.

## 5. Ficheros que NO se tocan

`infrastructure/security/*`; `albaran_compra_statements.py`, `create_albaran_compra_use_case.py`, `create_proforma_use_case.py`,
`proforma_*`, `create_purchase_albaran_use_case.py`, `attach_concepto_grafico_use_case.py` (se importan, no se editan); los
ajustes `SIGRID_ALBARAN_*` y `SIGRID_PROFORMA_*` (cada endpoint tiene los suyos; `SIGRID_ALBARAN_EMPRESAS_OBRA` se lee, no
cambia); `SIGRID_DOCUMENT_ALLOWED_CONTIP` (P9, ajuste aparte). `domain/ports/sql_repository.py` y el adaptador no cambian.

## 6. Clases, funciones y reglas

```python
class CreateFacturaUseCase:
    def __init__(self, repository: SqlRepository, settings: Settings) -> None: ...
    def run(self, request: FacturaRequest) -> dict[str, Any]: ...

def linea_de_origen(dcapro: Mapping, anterior: Mapping | None, *, modo: str, cuenta_pendiente: int) -> dict: ...
def linea_sin_origen(linea: LineaSinOrigen, resuelto: Mapping, *, tasa_iva: Decimal) -> dict: ...
def validar_vencimientos(vencimientos, *, fecha_factura: int, totpag: Decimal) -> None: ...   # R29
def construir_con_factura(...), construir_dcf(...), construir_dcfrec(...), construir_pag(...),
    construir_consii(...), construir_dcaprodes(...) -> dict[str, Any]: ...
```

**Petición** (`FacturaRequest`, `extra="forbid"`):

| Campo | Tipo | Notas |
|---|---|---|
| `database`, `usu` (≤24), `referencia_externa` (1-128) | texto | `usu` → `log.usu`, validado en `dbo.usu` (R7) |
| `cif_proveedor`, `numero_factura` (1-128, a `entref`), `fecha_factura` (`AAAAMMDD`, a `fecdoc`) | | |
| `cod_obra` | texto, opcional | obligatorio sin `origenes` (R10) |
| `modo` | `"mes"` \| `"origen"` | defecto `"mes"` (R16) |
| `origenes` | lista de `con.cod`, 0..N | albaranes o proformas `tip 14` |
| `lineas` | lista de `LineaSinOrigen`, 0..N | `producto`, `partida?`, `paride?`, `descripcion` (1-128), `unidad?`, `cantidad`, `precio`, `iva` |
| `vencimientos` | lista 1..12 de `{fecha, importe}` | R28-R29 |
| `vencimiento_retencion` | fecha, opcional | solo con retención `reccla` 5 (R30) |
| `total_base`, `total_iva`, `total_factura` | decimales | `total_factura` = líquido con retención |
| `commit` | bool | `false` |

**Cabecera `con`:** `tip` 15, `cod`, `res` = `<entres>. (<entref>)` truncado a 128, `fec` = hoy en Madrid
(`sellos_del_alta(instante, None, "FR")`), `est` = REC de `conest`, `tiemod`, `tex` vacío.

**Cabecera `dcf`** (lista blanca; lo no listado, el vacío del tipo según T0):
- Con orígenes: del primer origen por `cod` (M57) `ent*`, `obride`, `cenide`, `almide`, `empide`, `dir*1`, `pagide`, `pagtex`,
  `pagfor`, `efeide`, `eioide`, `ivadif`, `cocide`, `tipgar`, `fecent`, `feclim`, `ban*`; `ctride` del contrato de los orígenes.
- Sin orígenes (M61): `ent*`, `pagide`, `efeide`, `eioide`, `ban*` del proveedor; `pagfor`/`pagtex` de `auxpag` de ese `pagide`;
  `obride`, `cenide`, `almide` de la obra; `ctride` 0.
- Siempre: `cueide` = `prv.cueide`, `cla` 1001, `synckey`, `hor` del sello, totales de R24; `estfac`, `estser`, `estped`,
  `docoritip`, `docoriide`, `facoriide`, `fecpag` 0.

**Líneas de origen** (`linea_de_origen`): R17 + `cueide` = `prv.cuepdtide`, `pos` múltiplo de 64 (primero las de origen por orden
de `origenes` y `dcapro.pos`, luego las sin origen en el orden de la petición). Columnas a origen:

| Modo | `canoriori` | `canoriant` | `imporiant` | `imporiori` |
|---|---|---|---|---|
| mes | `can` | 0 | 0 | `tot` |
| origen, vinculada | `dcapro.canoriori` | `canoriori` de la anterior | `imporiori` de la anterior | `dcapro.imporiori` |
| origen, sin vincular | `dcapro.canoriori` | ídem | ídem | `imporiant` + `tot` |

«Anterior» = la `dcapro` de `dcapro.canorilin` (lectura propia, L-anterior); sin ella, 0. Es una **copia** de lo que ya
dejó escrito el albarán, no una deducción: por eso se reproduce en vez de pedirlo al llamante (P14).

**Líneas sin origen** (`linea_sin_origen`): producto por `(emp, cod)` y lista blanca; naturaleza por el mapeo; `cueide` = la `cua`
de `cuacomcod`; partida, almacén, centro y `caaide` con las funciones de F-009 (R13b, R14, R14b, R15); `ivaide` del código `iva`
(lectura de `dbo.iva` + `con.cod`); importes de R23.

**Vencimientos** (`validar_vencimientos`): fechas reales con `datetime.date`, en [`fecha_factura`, `fecha_factura` + 730 días],
sin repetir; Σ `importe` = `totpag` ±0,01. **`pag`**: `cla` 0, uno por vencimiento, `tot` = su `importe`, `fecven` = su `fecha`;
`efeide`, `cueide`, `entide`, `cenide`, `entref`, `ban*` de `dcf`. `cla` 2: `tot` = `cuo`, `retide` = `recide`, `cueide` =
`dcfrec.cueide`, `fecven` = `vencimiento_retencion`. `con`: `tip` 25, `cod` `<cod>_NN` (cla 0 primero), `res` `Pago i de n
<res>`, `fec` = `con.fec`, `est` PDT.

**Marcas (`UPDATE`, siempre por `ide` y con `?`):**

```sql
UPDATE dbo.dcapro SET canfac = canfac + ? WHERE ide = ? AND canfac = 0;     -- exige 1 fila (R36)
UPDATE dbo.dca SET estfac = 1, fecfac = ?, horfac = ?, antestfac = 3 WHERE ide = ? AND estfac = 0;
UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = 14 AND est = ?;          -- CON -> FAC (R37)
UPDATE dbo.ctrpro SET canfac = canfac + ? WHERE ide = ?;
UPDATE dbo.ctr SET estfac = ? WHERE ide = ?;
```

**SQL:** sin ficheros `NN_*.sql` ni esquema nuevo: SQL parametrizado en constantes de `factura_statements.py`.

## 7. Transacción

Previa: lecturas con `execute_read_query` y construcción sin escritura. Orden de validación: cuerpo → llaves → prefijo y `usu`
→ obra y proveedor → orígenes y modo → líneas sin origen (fallos juntos) → totales → retención → vencimientos → duplicadas.

Commit: `run_in_write_transaction` con applocks **en este orden fijo**, compatible con los existentes (`_con` antes y `_log` al final):
`SIGRID_REFEXT_15`, `SIGRID_SERIE_15`, `SIGRID_IDE_con`, `SIGRID_IDE_dcfpro`, `SIGRID_IDE_dcaprodes`, `SIGRID_IDE_dcfrec`,
`SIGRID_IDE_pag`, `SIGRID_IDE_consii`, `SIGRID_IDE_log`.

Dentro, reentrante: (1) re-comprobar R39; (2) releer con `WITH (UPDLOCK, HOLDLOCK)` `dcapro` y `dca` de los orígenes y repetir
R13-R14 (el escritorio no toma nuestros applocks); (3) reservar `cod` e `ide` (`pag` comparte `ide` con su `con`); (4)
`INSERT`s; (5) `UPDATE`s; (6) relectura R41. El `work` no calcula con estado de intentos anteriores. Una factura sin
orígenes salta (2) y (5).

## 8. Riesgos y decisiones

- **LÍMITE DE MICROSERVICIO.** Cabe el alta de FR (de mes, a origen, mixta, sin origen con productos de lista blanca). **No cabe**
  la contabilidad (P1) ni FRGG: allí cada línea lleva una cuenta de gasto 62xx elegida a mano (42 cuentas, 94 % sin producto,
  M61); elegirla es una decisión contable. Si se pidiera, `blocked` y otro servicio o el escritorio.
- **Cuenta y analítica de la sin origen.** Reproducen el escritorio en el 96,1 % y el 85,6 % (M61); el resto lo corrige
  Administración en «Comprobar». V6 lo confirma. Es el mismo criterio ya aceptado en F-009 para la sin vincular.
- **Cabecera sin origen desde el proveedor**: `ban*` coincide solo en el 58-74 % (M61, muestra de 117). Se acepta: la `pag`
  nace en PDT, fuera de remesas, y se revisa en «Comprobar».
- **Vencimientos del llamante**: la API no puede saber si son los correctos; valida forma, rango y suma. Una fecha anterior a
  la factura (0,26 %, M62) se rechaza (P12).
- **A origen por regla** (99,5 %): las 39 líneas que no casan son correcciones a mano; con la copia la factura es coherente con
  su albarán, que es lo que «Contabilizar» cruza.
- **Exigir el origen contabilizado** (P4) sigue: una proforma recién creada da `origen_sin_contabilizar`.
- **Clonar la cabecera** se descarta (F-015); listas blancas. **`dca.idefac`** no se escribe (M54).
- **Reversión:** no hay. Un alta equivocada se anula en el escritorio, nunca con `DELETE` (V4).
- **Carrera con el escritorio:** `UPDLOCK` y `UPDATE` condicionado a `canfac` = 0; el índice `con_emptipcod` obliga a reintentar.
- **Permisos (V1):** si `user_rw` no tiene `UPDATE` de `con`, `dca`, `dcapro`, la primera grabación falla con ROLLBACK (T19).
- **Varios llamantes:** dos apps con el mismo prefijo se pisarían la idempotencia; por eso un prefijo por app, fijado en el
  despliegue. La traza registra el prefijo y `usu`, no la app.

## 9. Decisiones del humano

**v1, aprobada el 2026-10-30** (P1-P10 = la *Recomendada*; texto en `git show 1a3e739:specs/F-008-registrar-factura/design.md`). **Se mantienen:** P1 (alta en REC sin contabilidad), P2 (`pag` y
`consii`), P4 (origen sin contabilizar rechazado), P6 (orígenes enteros), P9 (PDF por `concepto-grafico`), P10 (factura del
proveedor). **Cambian por la corrección del humano del 2026-10-30:** P3 → P12-P13; P5 → P14; P7 → P11; P8 → P15.

**Qué cambió de la v1 a la v2:**

| Tema | v1 | v2 |
|---|---|---|
| Origen | Solo albaranes/proformas, obligatorios (`albaranes`) | `origenes` 0..N y `lineas` sin origen 0..N; al menos uno (R2, R20-R23) |
| Proveedor y obra | Del albarán | Del albarán, o por CIF y `cod_obra` sin orígenes (R9-R10) |
| A origen | Rechazada (`origen_a_origen_no_soportado`) | `modo` del llamante, validado contra los orígenes; columnas por regla (R16-R19) |
| Vencimiento | Regla del 77 % con `vencimiento` opcional y aviso | `vencimientos` [{fecha, importe}] obligatorios; sin regla ni aviso (R28-R31) |
| Retención | `fecven` = `con.fec` + meses de la `R` | `vencimiento_retencion` del llamante (R30) |
| Llamantes | Solo `facturas` | Prefijos por configuración + `usu` validado, sin lógica por app (R6-R7) |
| Ficheros | `factura_vencimiento.py` | `factura_lineas.py`; tres ajustes nuevos (productos, naturaleza, IVAs) |
| Errores fuera | `origen_a_origen_no_soportado`, `forma_de_pago_no_soportada`, aviso `vencimiento_estimado` | Nuevos: `modo_no_coincide_con_origen`, `origenes_de_modos_distintos`, `proveedor_no_encontrado`/`_ambiguo`, `obra_no_encontrada`, `vencimiento_no_valido`, `vencimientos_no_cuadran`, `vencimiento_retencion_no_valido`, `usuario_no_valido`, fallos de línea de F-009 e `iva_no_valido` |

**Decisiones nuevas (pendientes de validar):**

**P11. ¿Qué es «sin origen»?** *Recomendada:* facturas **FR de obra** con líneas que manda el llamante, solas o junto a orígenes
(mixtas: 7,7 % de FR26, con ajustes negativos), con productos de lista blanca como F-009, sin retención ni contrato cuando no
hay orígenes. **Choca con P7 de la v1**: la mayoría de las facturas sin origen son **FRGG** (2.592 en 2026 frente a 55 FR), y
FRGG sigue fuera porque exige elegir la cuenta de gasto por línea (§8). ¿Bastan las FR, o el humano pensaba en gastos
generales? Si es FRGG, propongo dejarlo `blocked` y estudiarlo aparte.

**P12. ¿Forma y validación de los vencimientos?** *Recomendada:* lista de 1 a 12 `{fecha, importe}` (M62: el alta escribe 1 o 2;
las de 3 y 5 son divisiones posteriores de Tesorería), Σ = `totpag` ±0,01, fechas reales entre `fecha_factura` y +730 días (máx.
medido 690). Alternativa: admitir fechas anteriores a la factura (29 casos, 0,26 %) con aviso. Y `vencimiento_retencion`
obligatoria cuando haya garantía `reccla` 5, también del llamante.

**P13. ¿Queda la regla del 77 % como aviso?** *Recomendada:* **no**, se quita entera: el humano dice que el vencimiento viene
dado, y un aviso que falla una de cada cuatro veces enseña a ignorar avisos.

**P14. ¿A origen: quién manda las cantidades e importes a origen?** *Recomendada:* el llamante manda `modo` y la API **copia** las
columnas a origen del albarán con la regla de M63 (99,5 %), sin pedirlas. A diferencia de F-016, aquí no hay nada que decidir:
la cadena la fijó el albarán al registrarse y la factura solo la refleja. La v1 medía 31 % porque aplicaba la resta
`imporiori` − `imporiant` también a las vinculadas, donde `imporiori` es el importe del contrato. Alternativa: que el llamante
mande `canoriori`/`imporiori` por línea y la API los compare; más trabajo para el llamante sin ganar seguridad.

**P15. ¿Varios llamantes?** *Recomendada:* `SIGRID_FACTURA_PREFIJOS_REFERENCIA` con un prefijo por app, fijado en despliegue, y
`usu` obligatorio validado en `dbo.usu`, como F-006/F-009. La llave de escritura es una para todos. ¿Qué apps y prefijos
habrá al desplegar?

**P16. ¿Naturaleza de la línea sin origen?** *Recomendada:* mapeo propio `SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO`, como F-009
(H34) y F-007. Alternativa: `pro.natide`, que es lo que hace el escritorio en el 97,4 % (M61); F-009 lo descartó por criterio
de negocio y conviene ser coherente.

**P17. ¿IVA de la línea sin origen?** *Recomendada:* el código de IVA lo manda el llamante (está en el papel), limitado a
`SIGRID_FACTURA_IVAS` (I21, I10, ISP21, i0 cubren el 100 % medido). Elegir ISP es fiscal, pero aquí solo se copia lo que dice
la factura; si el humano prefiere, la API puede exigir el del último albarán del producto y proveedor (regla de F-009).
