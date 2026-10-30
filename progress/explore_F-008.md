<!-- progress/explore_F-008.md -->
# F-008 · Medición en producción de la factura de compra (solo lecturas)

Medido el 2026-10-30 por `POST /api/sql/read` de la API desplegada (base `ruesma`), SQL con agregados y `TOP`; **ninguna
escritura ni dry-run de dominio**. Scripts en el scratchpad del spec-author, fuera del repositorio. Sin nombres de personas
ni de proveedores, ni CIF. Numeración a continuación de [`explore_F-018.md`](explore_F-018.md) (M51). Parte de §M15 y §M30 de
[`explore_F-007.md`](explore_F-007.md), que siguen valiendo y no se repiten. Diccionario:
[`azure-apps/sigrid_tablas.md`](../../azure-apps/sigrid_tablas.md) (`dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `apu`,
`regiva`, `regirp`, `prv`, `auxpag`).

«FR26» = `con.tip 15`, `emp 1`, `cod LIKE 'FR26/%'` (11.394 el día de la medición). «FR26/1» = el tramo reciente,
`cod LIKE 'FR26/1%'` (1.408 facturas, 10.860 líneas). Los estados cambian en vivo: las cifras de REC/COM se movieron entre dos
consultas del mismo día (6/5 → 4/5).

**Lo principal:** la contabilización **no** ocurre al dar de alta. El alta (REC) escribe el documento, la cartera y el SII y
marca los orígenes; el asiento y los registros de IVA e IRPF llegan después, con «Contabilizar» en el escritorio. Esa frontera
permite un endpoint de alta **sin tocar contabilidad**.

## M52 · Series y estados

- **Series `tip 15`** (`sercon`): 107 `FR<AÑO2>/` «Facturas de obra», 163 `FRGG<AÑO2>/` «gastos generales» (`estini` 20), 125
  `AB<AÑO2>/` y 178 `ABGG<AÑO2>/` «abonos», 232 «no utilizar». Desde 2025, **ninguna** factura en `AB`/`ABGG`.
- `dcf.cla` **1001** en todas. FR26 `emp 1`: 11.394, `cod` de 10 caracteres (`FR26/00001`…, 5 cifras), máximo 11.410: hay
  huecos. Por empresa: `emp 1` y `39` usan `FR`; las demás casi solo `FRGG`. La serie sale del año de `con.fec` (FR25 con 4
  altas en enero de 2026 de 12.461).
- `con.fec` es la fecha de alta, no la de la factura: igual a `fecdoc` en 3.756, posterior en 7.346, anterior en 292.
- **`conest` 15:** 1 REC, 2 COM, 3 CON, 4 APJO, 5 APRJG, 6 APRADM, 10 APR (aprobado pago), 15 RECH, y 20/25/30 las de GG.
  FR26: REC 4-6, COM 5, CON 212-219, APJO 148, APRJG 277, APRADM 237, APR 10.488, RECH 5, FRAAPR 11.
- `dbo.log` de una factura: `ope 1` (alta, `tab con`, `est 1`), `ope 3`, `ope 5` con texto «Comprobar factura» y «Factura
  contabilizada», `ope 24` (firma digital de aprobación), `ope 30`. En REC, `ope 1`; en COM, además `ope 5`.

## M53 · Qué existe en cada estado: la frontera de la contabilización

FR26 por `con.est`, número de facturas con cada fila:

| est | n | asiento `tip 20` mismo `cod` | `regiva` | `regirp` | `pag` | `dcfrec` | `dcfpro` |
|---|---|---|---|---|---|---|---|
| 1 REC | 6 | **0** | **0** | 0 | 4 | 1 | 4 |
| 2 COM | 5 | **0** | **0** | 0 | 5 | 3 | 5 |
| 3 CON | 212 | 212 | 212 | 0 | 212 | 39 | 212 |
| 4-6 | 662 | 662 | 658 | 2 | 662 | 180 | 662 |
| 10 APR | 10.488 | 10.488 | 10.488 | 26 | 10.488 | 2.285 | 10.488 |

Igual en FRGG26: 25 COMGG, 28 de 28 con `pag` y **0** asiento ni `regiva`; 30 CONGG, 1.658 con todo. Las 2 REC sin `pag` son
las 2 **sin líneas**. `consii`: **100 %** de las que tienen líneas, en todos los estados (M58). `rcg` (PDF adjunto, por
`rcg.con`): 0 de 4 en REC, 5 de 5 en COM, 218 de 219 en CON (M59). `confir`: ninguna en REC/COM; aparece con la aprobación.
`conext`: ninguna. `mov`: octubre, 6.018 filas, **todas** `doctip 14`: la factura no mueve stock. `dcfpropar`, `dcfproana` y
`dcfproimp`: 0 filas en FR26; `dcfprodes`: 18 de 94.334 líneas. `dcapropar`: 0.

**Fila a fila, el alta en REC son:** `con` 15, `dcf`, `dcfpro` ×N, `dcfrec` ×0-1, `con` 25 + `pag` ×M, `consii`, `log`.

## M54 · Qué pasa con los orígenes al dar de alta

Líneas de las facturas en REC y COM con `docoritip 14` (139):

- `con.est` del albarán **10 FAC**, `dca.estfac` 1, `fecfac` ≠ 0 y `antestfac` 3 en el 100 %. **Se marca en el alta, no al
  contabilizar.**
- `dcapro.canfac` = `dcfpro.can` en 139 de 139; `dcaprodes` (`docdestip 15`, `docdeside` = factura, `lindeside` = línea, `can`
  = la de la línea) en 139 de 139.
- `ctrpro.canfac` = Σ `dcapro.canfac` del `ctrpro` en 28 de 28 vinculadas.
- `dca.fecfac` es la **fecha de la operación**, no la de la factura: = `log` de alta en 2.457 de 2.522 (97,4 %); = `con.fec`
  de la factura, 8,4 %; = `fecdoc`, 1,9 %.
- `dca.idefac` = la factura en 673 de 3.252 albaranes: 1 de 1.151 si la factura tiene **un** albarán y 672 de 2.101 si tiene
  varios. Sin regla: el enlace fiable es por línea (M15).
- **`antestfac` es 3 en el 100 % de los facturados**, incluso en los que no pasaron por CON: es un valor fijo, no el estado
  anterior.
- `ctr.estfac` (contratos desde 2025): con todo facturado 199 de 204 en 1 y 92 de 2.263 en 0: la regla de `estados_contrato`
  se sostiene y hay contratos *stale*.

**El albarán contabilizado va antes.** AC26/1: `est 1` 132, ninguno con asiento; `est 3` 1.622, todos; `est 10` 8.166, todos.
PROF26: 1 y 2, ninguna; 3 y 10, todas. El asiento del albarán (D 6xxx / H 4009, 4109 o 4149) lleva su fecha en 3.231 de 3.252 y
es anterior a la factura en 2.995. Orígenes de FR26 (factura, albarán) por estado actual del albarán:

| `con.est` del albarán | con asiento | sin asiento |
|---|---|---|
| 10 FAC | **26.517** | 115 |
| 3 CON | 27 | 6 |
| 2 COM / 1 PDT / 0 | 1 | 74 |

Es decir, **99,3 % contabilizados**; el escritorio **no lo impide** (0,7 %). Sin asiento del albarán, el asiento de la factura
carga en 4009 lo que nunca se abonó: la cuenta queda descuadrada.

## M55 · La parte contable, que hace «Contabilizar»

Apuntes de los asientos de FR26/1 (`apu` por `asi.cod` = `con.cod`; 1.398 asientos, `con.est` 0). La columna «Qué es» es lectura
por el plan contable, no medición:

| Cuenta | Filas | Lado | Qué es |
|---|---|---|---|
| 4009, 4109, 4149 | 603 + 619 + 164 | Debe | Facturas pendientes de recibir: **cancela lo que abonó el albarán** |
| 4720 / 4721 | 1.053 / 378 | Debe | IVA soportado; 4721, inversión del sujeto pasivo |
| 4771 / 4770 | 339 / 64 | Haber | IVA repercutido del ISP |
| 4000, 4100, 4140 | 600 + 624 + 167 | Haber | Proveedor o acreedor (la del `dcf.cueide`) |
| 4008, 4108, 4180 | 32 + 292 + 8 | Haber | Retenciones de garantía |
| 4751 | 6 | Haber | IRPF retenido |
| 6000, 6060, 6210, 6281, 6299 | 88 | Debe | Líneas sin albarán, y ajustes frente al albarán |

Además `regiva` (1:1+ por tipo de IVA), `regirp` y la `consii.regivaide`. Hay 19 familias de cuenta y decisiones de ISP,
deducibilidad, periodo de IVA y ajustes. **Esto no se reproduce con seguridad desde aquí** y no hace falta: lo hace el
escritorio, a partir de lo que deja el alta. La aprobación por firma (`ope 24`) tampoco.

## M56 · Líneas: `dcfpro` frente a su `dcapro`

- **Origen de las líneas de FR26:** 92.470 `docoritip 14`, 1.725 `0`, 34 `44`, 8 `15`. FR26 con **todas** las líneas de
  albarán: **10.449 de 11.387 (91,8 %)**; ninguna, 64. `FRGG26`: 7.830 líneas sin origen y 904 de albarán.
- Por factura: 8,3 líneas de media (máx. 373), 2,4 albaranes (máx. 121), un albarán en 8.687, **varias obras en 82 (0,7 %)**,
  sin contrato 2.608. Contratos distintos: 1 en 1.388, 2 en 9 de 1.397 (`dcf.ctride` = el mayor, 9 de 9).
- **Albarán entero en la factura:** 3.230 de 3.252 (99,3 %). Por `dca`: facturado entero 24.639, parcial 59.
- **10.794 líneas FR26/1 con origen, iguales a su `dcapro`:** `can`, `dto`, `proide`, `cenide`, `caaide`, `natide`, `almide`,
  `obride`, `cod2`, `unimed`, `prepma`, `dncide`, `docoricod` 100 %; `pre`, `tar`, `tot` 10.792; `res` 10.793; `ivaide` 10.671,
  `ivacuo` 10.666; `paride` 10.238 (albarán 0 y factura informada, 334). `cueide` **0**.
- **Las diferencias de IVA son correcciones humanas:** I21→I10 66, I21→ISP21 37, ISP21→I21 17, I10→I21 2.
- **`dcfpro.cueide` = `prv.cuepdtide`** («Cue. Fras Pendientes») en **92.507 de 92.520** (99,99 %) de FR26 con origen 14, haya o
  no asiento del albarán. En líneas sin origen, la cuenta 6xxx. `dcf.cueide` = `prv.cueide` 1.397 de 1.397.
- **`pos` en múltiplos de 64** en 10.854 de 10.860. A cero: `canser`, `canfac`, `cancan`, `candes`, `canorilin`, `apuide`, `lintip`,
  `refent`, `ivaope`, `anades`.
- **Origen a origen (`dca.docoritip` 1):** 1.077 facturas de FR26 de 11.323 con albarán (9,5 %): 991 PROF, 86 AC. De mes (`docoritip`
  0): 9.463 líneas, `canoriori` = `can` **100 %**, `canoriant` 12. A origen: `canoriori` = el de `dcapro` en 1.278 de 1.286, pero
  `imporiori` = el de `dcapro` en 952 y `imporiori` − `imporiant` = `tot` solo en 399 (31 %). **La de mes se sabe; la a origen, no.**

## M57 · Cabecera `dcf` y totales

- **Frente al primer albarán de origen** (1.397 facturas): `entide`, `entcif`, `entres`, `obride`, `cenide`, `almide` 100 %;
  `diremp1` 1.396, `dirdir1` 1.395; `fecent`, `coc`, `feclim` ≥ 1.395; `cue` 1.394; `eio` 1.394; `ban*` 1.387; `ivadif` 1.362;
  `ctride` 1.338; `efeide` 1.350; `tipgar` 1.330; `pagfor` 1.312; `pagide`/`pagtex` 1.293 (92,6 %; `prv` 1.080, `ctr` 1.034);
  `empide` 1.164 (83,3 %). `entref` difiere: es el número de **la factura**, no del albarán.
- **`synckey` a vacío en las 168.203 `dcf`** de la historia: libre para la idempotencia (como en `dca`, F-009).
- A cero en todas las sep+ (1.393): `estped/ser/fac`, `ant*`, `fecfac`, `horfac`, `idefac`, `pasori`, `docoritip`, `docoriide`,
  `facoriide`, `fecpag`, `ano`, `mes`, `numregcon`, `synckey`, divisa. `fecrec`, `tex` y `caaide` tampoco se usan.
- **Totales** (1.408): `totbas` = Σ `tot` **100 %**; `totdoc` = `totbas` + `totiva` 100 %; `impnet` = `totbas` 100 %; `totpag` = `tot`
  100 %; `impbru` = `impnet` 1.287 (el resto, dto: F-018). **`totiva` = Σ `ivacuo`: 1.361 ±0,01, 1.400 ±0,05, 1.408 ±1** (máx. 0,31):
  el IVA del papel no siempre es la suma de líneas.
- **Duplicados:** de 29.016 pares (`entcif`, `entref`) desde 2025 (sin RECH), **41 repetidos** (0,14 %): el escritorio no lo impide.
- **Abonos:** 326 de 11.394 con `tot` < 0, todos en serie `FR`, `facoriide` 0 en todos; 304 con líneas de albarán.

## M58 · Cartera y SII: lo que el alta escribe además

- **`pag` es concepto `tip 25`** con su `con`: `cod` = `<cod factura>_NN`, `res` «Pago i de n <res>», `fec` = la de la factura,
  `est` 1 PDT (`conest` 25: 1 PDT, 2 APR, 3 EMI, 5 CAR, 7 REM, 10 PAG…). En REC/COM, `remide` y `fecrea` a 0: **no entra en remesas**
  hasta que Sigrid lo aprueba.
- **`pag.cla` 0** (pago): 880 de 888 facturas con uno; `tot` = `totpag` en 879. **`pag.cla` 2** (retención de garantía): uno por
  `dcfrec` de `reccla` 5, `tot` = `cuo` 2.484 de 2.486, `retide` = `recide` 100 %, `cueide` = `dcfrec.cueide` 2.446. La IRPF
  (`reccla` 3) no tiene `pag` propio. `pag.efeide`, `cueide`, `entide`, `cenide`, `entref` = los de `dcf` (≥ 99 %); `ban*` 96 %.
- **`dcf.pagfor`** (`auxpag.formul`): `120` 4.286, `150 450R` 1.592, `150` 1.289, `90` 1.270, `0` 965, `30` 747, `120 450R` 684…;
  con varios plazos sin retención, **2** en todo FR26. La `R` es la retención.
- **El vencimiento no se reproduce por completo.** 735 `pag` `cla 0` en `est 1` de FR26/1 frente a las reglas probadas (días de
  `pagfor`, días de pago `prv.pagdia` —texto libre: `15`, `15,30`, `15 y 30`—, meses sin pago `prv.pagmes` —`8,12`, `8.12`—):
  sobre `fecdoc` 58,5 %; **sobre `con.fec`, con 15 y 30 si el proveedor no trae días y último día si el mes es corto, 77,3 %**.
  Los fallos incluyen fechas que nadie calcula (un vencimiento **anterior** a la factura). `prvobrpag`: 1 de 735.
- **Retención:** `fecven` = `con.fec` + 15 meses (450/30) en 187 de 197 (94,9 %).
- **`consii`**, una por factura con líneas en **todos** los estados: `tipcom` A0, `tipdoc` F1, `claope` 01, `emiter`, `facsimcua`,
  `facsinide`, `difplaenv` N: **203 de 203** con esos valores. `desope` = `con.res` 181 de 203; `fecope` en 6; `regivaide` 0
  hasta contabilizar.

## M59 · Retención y adjunto

- `dcfrec` (FR26): `bas` = `totbas`, `cuo` = round(`bas`·`valpor`, 2) y `tot` = `totdoc` − `cuo` ≥ 99,6 %; una por factura.
- **Frente a la `dcarec` del albarán** (1.151 facturas de un albarán): con retención 333 y 341; mismo `recide` 321, misma `cuo`
  322, misma `cueide` 302. Sale del origen, como en F-015.
- `reccla` 5 la inmensa mayoría (2.259 de 2.285 en APR), 3 IRPF 26.
- **PDF:** casi toda factura lleva `rcg` desde COM. `sigrid/concepto-grafico` solo admite hoy `[708,44,14]`: falta el 15.

## M60 · Consumidores

- `facturas` (`azure-apps/facturas.md`): `sql/read` y conciliación; `CUADRA` «no aprueba nada» y lo que se haga con él es su F-012.
  **Lee `dca`/`dcapro`/`con`**: un albarán facturado cambia `con.est` a 10, igual que con el escritorio.
- `datamart-seg-anual`: copia `dcf`, `dcfpro`, `dca`, `dcapro`, `dcfrec` (`raw`); una factura de la API se ve como cualquier otra.
- `remesas`: lee `pag` por `remide`; una `pag` en PDT sin remesa no le llega.
- `proformas`: sus proformas son los orígenes (`est` 1 PDT al nacer); hay que contabilizarlas antes de facturarlas (M54).

## Lo que no se puede medir leyendo (verificación del humano)

- **V1:** si `user_rw` puede hacer `UPDATE` de `con`, `dca` y `dcapro` e `INSERT` en `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii` y
  `dcaprodes`. `sys.database_permissions` no se ve con el usuario de lectura.
- **V2:** si «Comprobar» y «Contabilizar» del escritorio aceptan una factura de la API y generan un asiento que cuadra.
- **V3:** si el escritorio deja corregir `pag.fecven` en REC/COM y si regenera los vencimientos al guardar.
- **V4:** si anular la factura desde el escritorio revierte `canfac`, `dcaprodes`, `con.est` del albarán y el `pag`.
- **V5:** qué decide `dcf.empide` (83 % el del albarán) y `dca.idefac`.
