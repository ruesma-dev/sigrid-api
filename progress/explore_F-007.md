<!-- progress/explore_F-007.md -->
# F-007 · Medición en producción de la proforma de subcontratista (solo lecturas)

Medido el 2026-10-18 por `POST /api/sql/read` de la API desplegada (base `ruesma`), con SQL parametrizado,
`TOP`/agregados y **ninguna escritura ni dry-run de dominio**. Script en el scratchpad del spec-author, fuera del
repositorio. «PROF26» = `con.tip 14`, `emp 1`, `cod LIKE 'PROF26/%'` (1.216 documentos el día de la medición);
«AC26» = lo mismo con `AC26/%` (29.476). Diccionario: [`azure-apps/sigrid_tablas.md`](../../azure-apps/sigrid_tablas.md)
(`dca`, `dcapro`, `dcarec`, `ctrrec`, `sercon`); no se duplica aquí. Sin nombres de personas ni de proveedores.

Sirve también a **F-008** (factura de compra): §M15 recoge cómo enlaza la factura con la proforma. La v2
(M16-M26, 2026-10-19) mide lo que necesita la app de facturas: fecha, cadenas, identificación de líneas y duplicadas.

## M1 · Qué es una proforma en Sigrid

Un **albarán de compra** (`con.tip 14` + extensión `dca` + líneas `dcapro`) de **otra serie y otra clase**:

| `sercon` | `tip` | `cod` | `res` | `tam` | `emp` | `estini` | `xjsini` | `xjsvar` |
|---|---|---|---|---|---|---|---|---|
| 87 | 14 | `AC<AÑO2>/` | Albarán de compra | 5 | 0 | 0 | — | — |
| 228 | 14 | `NTC<AÑO2>/` | Nota de cargo | 5 | 0 | 0 | — | — |
| **230** | 14 | **`PROF<AÑO2>/`** | **Proforma subcontratista** | **5** | 0 | 0 | `alta_con` | **`cla=141`** |

- Códigos: `PROF24/` 387, `PROF25/` 1.253, `PROF26/` 1.216 (último `PROF26/01282`); todos `emp 1`, `LEN(cod) = 12`
  (5 dígitos con ceros), la serie **se reinicia cada año** (como `AC`). `con.subtip` 0 y `con.serie` 0 en el 100 %.
- **`dca.cla = 141`** en el 99,3 % de PROF26 (desde 2025: 2.461 con 141 y 8 con 0) y en el 0 % de AC26 (17
  albaranes `AC` antiguos con 141 desde 2025). Ninguna tabla de catálogo tiene el `ide` 141 (`cla`, `consubtip`): el
  valor lo pone la serie (`xjsvar`). Es lo que distingue la proforma; el `cod` `PROF` lo confirma.
- **`con.tip 20` no es un documento de compra: es el asiento contable (`asi`)**, que reutiliza el `cod` del
  documento (1.170 de 1.170 `PROF26/` de `tip 20` están en `dbo.asi`). Las proformas en `est` 3 CON (73) y 10 FAC
  (1.097) tienen asiento; las de `est` 1 PDT (15) y 2 COM (31), no: **el alta no crea asiento**. La memoria del arnés
  que describe el 20 como «otra familia de documentos de compra» está equivocada.

## M2 · Estados y fila de `log`

`conest` del 14: 1 `PDT` Pendiente, 2 `COM` Comprobado, 3 `CON` Contabilizado, 10 `FAC` Facturado. PROF desde 2025:
`est` 0 → 5, 1 → 19, 2 → 31, 3 → 187, 10 → 2.227. Altas de `log` de PROF26 (cruce por `tip` + `cod`, `tab 'con'`):
`ope 1` con `est 1` y `ori 0` en las 1.309 filas (más que documentos: el `cod` se reutiliza al anular, M17b de
F-009); 104 de `ope 2`. **Nace en 1 PDT con la fila de alta de F-009.**

## M3 · Contrato, obra y proveedor

- `dca.ctride > 0`: 94,1 % de PROF26 (desde 2025: 2.318 de 2.469); AC26, 77,5 %. Obras de **construcción**
  (desde 2025: 0678 527, 0672 462, 0677 422, 0681 293, 0702 219…), todas `emp 1`.
- `ctr.tipgenpro`, `ctr.modproqui` y `ctr.prforitip` **no discriminan**: la mayoría de los contratos con proformas
  los tienen a 0 o NULL (1.822 de 2.318 proformas).
- 236 proveedores con PROF en 2026; 211 de ellos tienen también `AC` en 2026.
- Varias proformas del mismo contrato el mismo día: 139 de 971 pares (contrato, día).

## M4 · Cabecera `dca`: qué cambia frente al albarán (porcentaje de filas con valor no nulo)

| Columna | PROF26 | AC26 | Lectura |
|---|---|---|---|
| `cla` | 99,3 | 0,0 | M1 |
| `docoritip` | 76,5 | 0,2 | «Es documento origen»; M11 |
| `docoriide` | 63,7 | 0,2 | documento anterior de la cadena; M11 |
| `ivadif` | 55,0 | 8,3 | igual a `ctr.ivadif` en 1.043 de 1.144 con contrato (91,2 %) |
| `totiva` | 27,4 | 84,8 | inversión del sujeto pasivo (M9) |
| `estfac`/`fecfac`/`horfac`/`antestfac` | ~92 | ~81 | de la facturación (M15), no del alta |
| `idefac` | 4,8 | 17,0 | M15 |

El resto de las 145 columnas, iguales (`synckey` 0 % en las dos: el pipeline de albaranes no está en real).
`con.res` = `<entres>. (<entref>)` en el 83 % (AC 75 %); `entref` (su referencia) 100 %.

## M5 · Líneas `dcapro`

21.618 líneas en PROF26 (AC26: 116.134). Diferencias de relleno:

| Columna | PROF26 | AC26 | Lectura |
|---|---|---|---|
| `can`/`tot` ≠ 0 | 31,4 | 98,2 | líneas arrastradas a cantidad 0 (M11) |
| `canorilin` | 78,4 | 2,0 | línea del documento anterior (M11) |
| `canoriori` | 78,1 | 61,5 | cantidad **a origen** en la proforma (M11) |
| `canmed` | 28,8 | 0,1 | medición desglosada (`med`, binario), la teclea el usuario |
| `ivacuo` ≠ 0 | 4,6 | 65,2 | M9 |
| `cod2` | 71,3 | 35,6 | del `ctrpro` (H35 de F-009) |
| `dncide`/`dncproide` | 63,8 | 26,5 | del `ctrpro` |
| `docori*`/`linoriide` | 63,5 | 22,1 | vinculadas al contrato (`docoritip 44`) |

`refent` 0 % (libre, como en F-009 R30c). `dcapropar` y `dcaproana`: 0 filas en PROF26.

## M6 · Contrato servido, `ctrprodes` y `mov`

- Una `ctrprodes` por línea vinculada, **también con `can` 0** (PROF26: 9.582 de las 13.729 son de líneas con `can` 0;
  desde 2025, 35.578 para 35.552 vinculadas, ninguna sin línea).
- `ctrpro.canser` = Σ `can` de las vinculadas (contrato `CTSB25/0662`, 21 proformas: 10.980,79 = 10.980,79; por
  `ctrpro`, igual en los 8 medidos; `canser` puede superar `can`): **la `can` de la proforma es la del periodo**.
- `mov` como el albarán (`tip 1`, `oritip 5`, `destip 2`, `doctip 14`), **si y solo si `pro.tipmov` = 1** (PROF26
  desde junio: `can` ≠ 0 y `tipmov` 1 → 2.182 de 2.182 con `mov`; `tipmov` 0 → 0; `can` 0 y `tipmov` 1 → 4.375 de 4.519).

## M7-M8 · Productos y naturaleza

Vinculadas: `SM370001` (`tipmov` 0) 6.311, `SM9999` 4.633, `SB9999` 1.848, `XA9999` 356, `MA9999` 308. Sin
vincular: `SB9999` 2.839, `SM9999` 2.790, `SM370001` 1.418, `MA9999` 434, `XA9999` 78, `QA9999` 39. Naturaleza de
las sin vincular: `SB9999` → `SB99` y `SM9999` → `SM99` en el 100 %; `SM370001` → `SM37` 1.297 de 1.418;
`MA9999` → `MA1501` 313 y `MA99` 121 (el caso H34 de F-009).

## M9 · IVA

`ivaide` 790408 (tasa 0) en 19.790 de 21.618 líneas (91,5 %), 777740 (21 %) en 1.714: la subcontrata de obra va por
**inversión del sujeto pasivo**. El IVA de la línea es el del `ctrpro` (vinculadas), como en F-009.

## M10 · Retenciones (`dcarec`)

- **56 % de PROF26 llevan `dcarec`** (680: `RET5` 670, `RET5T` 6, `RET2.5` 3, IRPF 15 % 1); AC26, 3.222 filas (11 %).
- Catálogo `rec`: `RET5` «Retención garantía 5 % (sobre base imponible)» `cla 5`, `valpor 0,05`; `RET2.5` `cla 5`;
  `RET5T` «sobre total» `cla 4`; IRPF profesionales `cla 3` (`regirp 1`).
- Salen del **contrato** (`ctrrec`): PROF26 con contrato → 674 con el mismo `recide` que su `ctrrec`, 32 con `ctrrec` y
  sin `dcarec`, 12 con `dcarec` sin `ctrrec`, 426 sin ninguna. `cueide`, `valpor` y `pos` iguales a los del `ctrrec`
  en 643 de 674 (95,4 %).
- Cálculo (`RET5`, 670): `bas` = `dca.totbas` (100 %); `cuo` = round(`bas`·`valpor`, 2) en 629 (93,9 %);
  **`dca.tot` = `totdoc` − `cuo`** en 666 (99,4 %); `totpag` = `tot` en el 100 % de PROF26; `ivacuo` 0.
- **AC26 de contratos con `ctrrec`: 2.991 con `dcarec` y 387 sin** (88,5 %). F-009 no escribe `dcarec` (O2).

## M11 · Cadena «a origen»

- `dca.docoriide` apunta al **documento anterior del mismo contrato** (PROF26: 718 proformas y 47 albaranes `AC` del
  mismo contrato; 9 de otro). Con contrato: 772 encadenadas, 140 con `docoritip 1` y sin anterior, 232 con
  `docoritip 0`; sin contrato: 54 con 0, 18 con 1. La regla de `docoritip` en la primera **no sale de los datos**.
- **Cadenas paralelas** en un mismo contrato, separadas por partida: `CTSB25/0662` lleva dos, alternas (partidas
  355326… y 355477…). La elige el usuario al crear la proforma.
- `dcapro.canorilin` → la línea del documento anterior **del mismo `ctrpro`** en el 100 % (16.939). La proforma
  **arrastra todas las líneas de la anterior**: 13.590 de las 16.939 encadenadas van a `can` 0.
- **`canoriori` = `canoriori` de la anterior + `can`** en 16.938 de 16.939 (cantidad a origen). En la primera,
  `canoriori` = `can` (vinculadas 2.483 de 2.612; sin vincular 1.334 de 2.067, 524 con 0). `imporiori` = `ctrpro.tot`
  en el 100 % de las vinculadas. En AC26, `canoriori` = `ctrpro.can` (24.597 de 25.646): **regla distinta**.

## M13 · Posventa (F-046/F-047 de postventa-incidencias)

- Obra **POSTV2**: `emp 1` (desde 2020) y `emp 28` (desde 2025-07). Documentos `tip 14` desde 2025: **1.283 albaranes
  `AC` (`cla 0`) y 3 proformas** (sin contrato, 1-4 líneas). Desde 2020: 3.593 `AC`, 195 con contrato.
- La **partida** de la línea es el **capítulo = la promoción** (`0654-B` 406 líneas, `0656` 379, `0639` 343…).
- **Ningún código `RS…`** de parte en `con.res`, `dca.entref`, `dca.tex`, `dcapro.res`, `tex` ni `refent` (0 de
  1.286 documentos y 0 de 3.992 líneas).
- Sigrid **no enlaza** parte y coste: `rcp` solo lo referencian `act.rcpide` (0 filas), `rcpint` y `tar.rcpide`
  (13.700 tareas, ninguna con `ctride`, `dcpide`, `dvpide`, `costot` ni `ventot` distinto de 0).
- **Conclusión:** el coste de posventa entra hoy como **albarán** en POSTV2, no como proforma, y el vínculo con la
  incidencia no existe en Sigrid: tendría que viajar en un campo que escriba la API (`dcapro.refent`, `synckey`).

## M14 · Plantilla de cabecera de F-009 (O1)

De los 831 proveedores con AC26, **17 tienen como último `dca` una proforma**: la L5 de F-009 (último `dca` del
proveedor, sin filtrar serie) clonaría `cla 141`, `docoritip`/`docoriide`, `ivadif` y los campos de facturación.

## M15 · Para F-008: la factura que factura una proforma

- Líneas de factura (`FR26/`) con `dcfpro.docoritip` 14 y `linoriide` = línea de PROF26: **6.349 con `can` ≠ 0 y 1
  con 0** (solo pasan las líneas con cantidad); 1.072 facturas ↔ 1.129 proformas (casi 1 a 1).
- La proforma recibe una **`dcaprodes` por línea facturada** (6.350, = las `dcfpro` anteriores), `dcapro.canfac`,
  `dca.estfac` 1, `fecfac`/`horfac`/`antestfac` y `con.est` 10 FAC (1.097 de 1.097 con factura). `dca.idefac` solo
  en el 4,8 % (AC 17 %): no es el enlace fiable; el enlace es por línea.
- La contabilización crea el asiento `tip 20` con el mismo `cod` (M1).
- `dcfpro` tiene `docoritip`, `docoricod`, `docoriide`, `linoriide`, `canorilin`, `canoriant`, `canoriori`,
  `imporiant`, `imporiori`, `canmed`, `canser`, `canfac`, `cancan`, `candes` (nombres leídos de `sys.columns`).


## v2 · Medición del 2026-10-19 para la app de facturas (M16-M26)

Mismo método (solo lecturas, `sql/read`, script fuera del repositorio). «Desde 2025» = PROF con `c.fec >= 20250101`
(2.470); «a origen» = `dca.docoritip 1`. Motivo: el llamante es la app de facturas (F-063), que lee la **hoja de
certificación** del buzón (sin CIF ni fecha; MES, ORIGEN y ANTERIOR por partida y en totales; nº de orden).

### M16 · `entref` y fecha

- `dca.entref` desde 2025: `PROF<MMAA>_<obra>` 1.266, `PROF_<MMAA>_<obra>[_sufijo]` 824, `PREV<MMAA>_<obra>` 134,
  `PREV… ANUL` 64, otros 182 (números del proveedor, ajustes). El mes del `entref` es el de `con.fec` en 1.237 de
  1.266 (97,7 %); el sufijo es el `cod` de la obra en 1.248. **No es el nº de orden de la hoja**: ese no consta en Sigrid.
- `dca.mes` 0 y `dca.periodo` vacío en el 100 %; `dca.fecdoc` = `con.fec` en 2.454 de 2.470; `fecrec` 0 siempre.
- Días de `con.fec` hasta fin de mes (a origen, 1.963): 0 → 187, 1-10 → 1.609, más de 10 → 167. No hay una regla
  fija de día: la proforma se fecha **dentro del mes certificado**, casi siempre en sus últimos diez días.
- `PREV` (positiva) y `PREV… ANUL` (negativa, el mes siguiente) son **provisiones de coste**, `docoritip 0`, fuera
  de toda cadena: no son lo que llega del buzón.

### M17 · `docoritip` (cierra V1)

`docoritip 0` ⇒ sin anterior en el 100 %. A origen desde 2025: 1.963 de 2.470, de ellas **321 primeras de cadena**
(`docoritip 1`, `docoriide 0`). Una proforma a origen **lleva `docoritip 1` también cuando es la primera**; las de 0
son provisiones, ajustes y proformas sueltas sin ORIGEN/ANTERIOR.

### M18 · (contrato, mes) no es clave

A origen con contrato desde 2025 por (contrato, mes de `con.fec`): 1.522 grupos con una, 188 con dos y 5 con 3-5.
De los pares: 158 son **cadenas paralelas** (sin líneas de contrato comunes), 43 comparten `ctrpro` sin estar
encadenados y 18 son **dos certificaciones del mismo mes en la misma cadena**.

### M19 · Cadenas

- Ningún documento tiene dos sucesores (1.630 anteriores, uno cada uno): la cadena es **lineal**.
- Puntas (a origen sin sucesor) de 2026 por contrato: 203 contratos con una y 34 con dos (31 pares sin líneas
  comunes, 3 con alguna). Por mes de la punta: septiembre 100, el resto 12-35 (cadenas cerradas o liquidadas).
- La cadena **mezcla series**: anteriores de una PROF desde 2025, 1.550 PROF y 92 `AC`; sucesores, 1.489 y 103.
  Hay 354 `AC` a origen desde 2025. Anterior del mismo contrato 766, de otro 9 (siempre el mismo proveedor).

### M20 · Ninguna clave de texto identifica la línea de contrato

243 contratos con PROF a origen en 2026, 8.707 `ctrpro` (máx. 416 por contrato). Contratos donde la clave es única:
`paride` 43, `cod2` 25 (20 sin `cod2`), `res` 98, (`paride`, `res`) 182, (código de partida, `res`) 182 (75 %).
Una proforma puede tener 2-3 líneas del mismo `ctrpro` (283 pares de 13.315). **La línea se identifica por `ide`.**
Tamaño (929 a origen de 2026): media 22 líneas (máx. 197), media 6 con MES (máx. 80); 633 llevan sin vincular.

### M21 · Vinculadas frente a su `ctrpro`

En PROF26 a origen: `paride` = el del `ctrpro` en 13.302 de 13.609 (97,7 %; nuevas 98,7 %), `pre` en 98 %, `res` en
99 %. **La partida de la vinculada sale del `ctrpro`** (en F-009, R16, no se hereda: allí es otra semántica).

### M22 · Cabecera: pago y anterior

- PROF26 con contrato (1.145): `dca.pagide` = `ctr.pagide` en 1.077 (94,1 %), y entonces `pagtex` también; = el
  del proveedor en 785. La `dca` no tiene vencimiento (es de la factura y su cartera: F-008).
- Encadenada frente a su anterior (775): `entide`, `almide`, `cenide` y `obride` iguales en el 100 %, `pagide` 92 %,
  `ivadif` 91 %, `cla` 93 % (el resto, anteriores `AC`).

### M23 · Arrastre de líneas

- 746 de 775 encadenadas arrastran **todas** las líneas de la anterior, 15 todas salvo las vacías, 14 no. Las
  nuevas van al final en 375, intercaladas en 84 (316 sin nuevas).
- Arrastradas (16.963): `canoriant` y `imporiant` 0 en el 100 %; `canoriori` = el de la anterior + `can` en el
  99,9 %; `imporiori` = el de la anterior en el 100 %; `pre`, `paride`, `res`, `proide`, `ivaide` iguales en el
  98-100 %; `pos` igual en el 84 %. `canorilin` = la línea de la anterior (también en las sin vincular).
- Sin vincular de cadenas: arrastradas con MES 678, nuevas con MES 892; `imporiori` 0 en el 99 %. Productos de las
  nuevas con MES: `SB9999` 412, `SM9999` 378, `SM370001` 246 (`tipmov` 0), `MA9999` 54, `XA9999` 20, otros 14.

### M24 · Plantilla de una primera de cadena

PROF26 primeras (156): el proveedor tenía ya alguna PROF en 88, solo `AC` en 48 y nada en 20 (13 %).

### M25 · Simulación: elegir la anterior con los datos de la hoja

Para cada PROF26 encadenada con contrato (773), candidatas = puntas a origen del contrato en ese momento:

| Regla | Única y correcta | Varias | Ninguna | Incorrecta |
|---|---|---|---|---|
| Cantidad ANTERIOR de las líneas con MES | 677 | 85 | 9 | 2 |
| Lo mismo, exigiendo una línea común | 523 | 0 | 250 | 0 |
| **Importe ANTERIOR total (Σ round(`canoriori`·`pre`, 2), ±0,05 €) y ninguna línea en contradicción** | **745 (96,4 %)** | 1 | 27 | 0 |

Con la tercera regla, de 140 primeras de cadena con contrato, 139 no casan con ninguna punta y 1 casa con una punta
de total 0.

### M26 · Detectar la PROF ya dada de alta

Regla: otra a origen del contrato con Σ round(`canoriori`·`pre`, 2) = ORIGEN (±0,05 €) y, por cada `ctrpro` con MES,
la misma `can` y `canoriori`. Sobre 913 PROF26 a origen con contrato, solo 4 tienen otra que case (2 pares): uno de
dos proformas con total 0 y otro de dos proformas distintas de la misma obra con importes idénticos.

## Lo que solo se sabe con la UI o con una hoja real (verificación del humano)

- ~~V1~~: cerrada por M17 (`docoritip 1` en la primera a origen).
- V2: pasa a F-015 (copia de `ctrrec` a `dcarec`).
- V3: qué columnas de `dca` toma el escritorio del contrato y cuáles de la anterior o de la última proforma.
- V4: si el TOTAL ANTERIOR de una hoja real es el Σ round(`canoriori`·`pre`, 2) de su anterior en Sigrid (M25).
- V5: si la hoja es una impresión de Sigrid (mismas líneas y orden que la anterior) y qué es su «Nº ORDEN».
