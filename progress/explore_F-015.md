<!-- progress/explore_F-015.md -->
# F-015 · Medición en producción de la plantilla de cabecera y de la retención (solo lecturas)

Medido el 2026-10-19 por `POST /api/sql/read` de la API desplegada (base `ruesma`), SQL parametrizado, agregados y `TOP`;
**ninguna escritura ni dry-run de dominio**. Script en el scratchpad del spec-author, fuera del repositorio. «AC26» =
`con.tip 14`, `emp 1`, `cod LIKE 'AC26/%'` (29.485 el día de la medición). Completa, sin repetirlas, §M1, §M10 y §M14 de
`progress/explore_F-007.md` (rama `feature/F-007-registrar-proforma`). Diccionario: `azure-apps/sigrid_tablas.md`
(`dca`, `dcarec`, `ctrrec`, `entrec`, `rec`, `sercon`, `apu`). Sin nombres de personas ni de proveedores.

## O1 · Plantilla de cabecera

- **M1 · Series del `tip 14`** (emp 1, desde 2025): `AC25/` 34.301 y `AC26/` 29.485 con `cla 0`; `PROF25/` 1.253 y
  `PROF26/` 1.209 con `cla 141`; `AC25/` 17 y `AC24/` 1 con `cla 141`; `PROF26/` 8 con `cla 0`; `NTC25/` 4 con `cla 0`.
  `sercon` del 14: 87 `AC<AÑO2>/`, 228 `NTC<AÑO2>/`, 230 `PROF<AÑO2>/` (`xjsvar cla=141`). Ni `con` ni `dca` guardan la
  serie: se reconoce por el prefijo del `cod` **y** la clase. Filtro `cod LIKE 'AC__/%' AND cla = 0`: excluye las tres
  familias raras (PROF, NTC y los 18 AC de clase 141).
- **M2 · L5 de hoy** (último `dca` del proveedor en la empresa, sin serie): de 832 proveedores con AC26, **18 (2,2 %)**
  tienen como último una `PROF26/` (`cla 141`), 813 un `AC26/` y 1 un `AC25/`. Entre los 857 con algún `tip 14` en 2026,
  43 tienen una PROF como último.
- **M3 · L5 propuesta**: sobre 3 de esos proveedores devuelve un `AC26/`, un `AC25/` y un **`AC18/`** (plantilla vieja,
  ver design §Riesgos); 0,9-5,2 s en frío, como la de hoy.
- **M4 · Sin ningún AC**: **6 proveedores** con `tip 14` en 2026 no tienen ningún `AC` de clase 0 en la empresa 1: todos
  solo con PROF y contrato (27 documentos, el último del 2026-09-24). Con el filtro darían `proveedor_sin_albaran_previo`.
- **M5 · Facturación y cadena en la cabecera** (AC26 por `con.est`; columnas con valor ≠ 0):

| `est` | n | `estfac` | `fecfac`/`horfac`/`antestfac` | `idefac` | `docoritip`/`docoriide` | `pasori` | `pasdeside`/`docrelide`/`fecpag`/`imprec` |
|---|---|---|---|---|---|---|---|
| 1 PDT | 869 | 1 | 4 | 0 | 1 | 0 | 0 |
| 2 COM | 329 | 49 | 49 | 3 | 2 | 0 | 0 |
| 3 CON | 4.591 | 5 | 8 | 2 | 1 | 1 | 0 |
| 10 FAC | 23.696 | 23.696 | 23.696 | 5.014 | 63/57 | 0 | 1/0/0/0 |

  El escritorio da de alta sin facturación ni cadena (fila PDT); la plantilla, el último AC del proveedor, está en `FAC` el
  80 % de las veces y trae `fecfac`, `horfac`, `antestfac` (100 %) e `idefac` (21 %). F-009 pisa `estfac` y `estser` a 0
  pero **clona el resto** (`construir_dca`; el clásico igual): es un defecto de F-009, no solo de la proforma.
- **M6 · Totales en divisa**: `totbasdiv`, `totivadiv` y `totdocdiv` ≠ 0 en **1 de 29.487** AC26; `totdiv` y `totpagdiv`
  a 0 en los 26.184 sin retención. F-009 (y el clásico) escriben ahí `totbas`/`totiva`/`totdoc`; el escritorio, 0.
- **M7 · Lo que sí se hereda** (AC26 frente al AC anterior del mismo proveedor): `cueide` 99,8 %, `efeide` 96,7 %, `cocide`
  94,2 %, `pagide` y `pagtex` 93,3 %, `ivadif` 92,4 % (86,4 % en PDT; `= ctr.ivadif` en el 93,7 % de los con contrato). El
  resto de columnas probadas (`fecrec`, `fecent`, `feclim`, `comide`, `alqide`, `ano`, `mes`, `tex`, `texent`, `ref*`), a 0
  o vacías. La regla de F-009 (M14b: pago, efecto y dirección de la plantilla) se sostiene.

## O2 · Retención (`dcarec`)

- **M8 · Cuántas**: AC26 con **una** `dcarec` 3.301, sin ninguna 26.184, **ninguno con dos o más**. Por recargo: `RET5`
  (`cla 5`) 3.181 (`valpor` 0,05 en 3.142; también 0,015, 0,016, 0,03, 0,00891), `180A19` (IRPF 19 %, `cla 3`) 25,
  `RET2.5` 17, `RETESP` (`cla 1`) 2, `190G01_15` (`cla 3`) 1, y 75 con un `recide` fuera del catálogo. `RET5T` (`cla 4`,
  sobre total): 0 en AC26, 16 en AC25.
- **M9 · Origen** (AC26 por contrato, `ctrrec` y `dcarec`):

| | con `dcarec` | sin | % con |
|---|---|---|---|
| contrato con `ctrrec` | 2.995 | 387 | **88,6** |
| contrato sin `ctrrec` | 57 | 19.409 | 0,3 |
| sin contrato | 249 | 6.388 | 3,8 |

  Sin contrato no sale de `entrec` (la retención por defecto del proveedor): de los 249, solo 11 son de proveedores con
  `entrec` y **ninguna** con el mismo recargo; los 85 AC sin contrato de proveedores con `entrec` llevan `dcarec` en 11.
  Es manual. Contratos con `ctrrec` y AC26: 484 siempre con `dcarec`, 57 mezcla, 10 nunca (12 documentos).
- **M10 · Por tipo de albarán** (contrato con `ctrrec`): con alguna vinculada, **99,1 %** (1.331 de 1.343); solo sin
  vincular y positivo, 82,7 % (929 de 1.123); **devolución** (solo sin vincular, `totbas` < 0), 80,6 % (671 de 832), con
  `bas` y `cuo` negativos; `totbas` 0, 76,2 % (64 de 84, `bas` y `cuo` 0).
- **M11 · Copia del `ctrrec`** (2.993 `dcarec` con el mismo `recide` que el `ctrrec` de su contrato; 59 sin él):
  `valpor` 99,8 %, `pos` 98,9 %, `valdef`/`valmod`/`valfij`/`reccla` 99,2 %, `ivaide`, `tex` y `resalt` 100 %, **`cueide`
  96,0 %**. De los 121 con `cueide` distinto (35 contratos): 87 con `dcarec.cueide` 0 y 22 con `ctrrec.cueide` 0.
  Contratos con `tip 14` en 2026 y `ctrrec`: **651, todos con una sola**. Soportables (`valfij` 0, `ivaide` 0, `cla` 3/4/5):
  636 (`cla 5` 633, `cla 3` 2, `cla 4` 1). No: `valfij` 1 en 6, `ivaide` 777740 en 2 y **`recide` 0** (fila vacía, sin
  `rec`) en 7 (sus 6 AC26 llevan una `dcarec` puesta a mano). En total, **15 de 651 (2,3 %)**.
- **M12 · Cálculo** (`valfij` 0 e `ivaide` 0): **`cuo` = ROUND(decimal(ROUND(`bas`, 2)) · `valpor`, 2)** en **3.223 de
  3.223**; con `float`, 3.178 (los 45 de diferencia, empates a medio céntimo con residuo binario, p. ej. 3.775,30 · 0,05 =
  188,765 → 188,77). Es `redondear_euros` de F-009 (`Decimal`, `ROUND_HALF_UP`, lejos del cero también en negativos).
  `bas` = `totbas` en `RET5` 3.169 de 3.181 (los 12, `valfij` 1 o `RETESP`), `180A19` 24 de 25, `RET2.5` 17 de 17;
  `RET5T` (`cla 4`): `bas` = **`totdoc`** en 22 de 22 (AC25 y PROF26). `valfij` 1: `bas` ≠ `totbas` en 13 de 15 (base
  tecleada); `valfij` 2: `cuo` ≠ el cálculo en 15 de 15.
- **M13 · Totales**: con `dcarec` de catálogo, **`tot` = `totdoc` − `cuo`** en 3.224 de 3.226 (`RETESP` no resta) y `totpag` = `tot`
  en el 100 %; sin `dcarec`, `tot` = `totdoc` y `totpag` = `tot` en 26.184 de 26.184. `imprec` 0 en el 100 % de AC26: la
  retención **no** va en `imprec`. `dcarec`: `pos` 64 en 3.298 de 3.301; `ivacuo`, `reqcuo`, `refide`, `frasupide`, `tex`,
  `resalt` e `item` vacíos salvo 21 `ivacuo` (con `ivaide` ≠ 0, 49 en total; 25 de ellos con `ctrrec.ivaide` 0).
- **M14 · Esquema vivo de `dbo.dcarec`** (`sys.columns`): `ide` int no nulo, `docide` int no nulo, `recide`, `pos`, `bas`
  float, `valdef`, `valpor` float, `valcan` float, `valmod`, `valfij`, `cuo` float, `tex` text, `reccla` tinyint, `cueide`,
  `ivaide`, `ivacuo` float, `reqcuo` float, `refide`, `resalt` varchar(48), `frasupide`, `item`. `MAX(ide)` 44.133 para
  41.478 filas: `ide` por `MAX+1`, como las demás.

## Contabilización y factura

- **M15 · Asiento del albarán**: AC26 en `CON`/`FAC` con `dcarec`: 3.012 de 3.041 con asiento (`con.tip 20`, mismo `cod`);
  **ningún apunte** en la cuenta de su `dcarec`. Σ debe = **`totbas`** en 622 de 625 (con `dcarec`) y 1.811 de 1.811 (sin):
  el asiento del albarán lleva solo la base; ni IVA ni retención. Escribir `dcarec` y `tot` neto **no cambia** ese asiento.
- **M16 · La factura hereda la retención del albarán, no del contrato** (`FR26/` que facturan AC de contratos con
  `ctrrec`): albarán con `dcarec` → factura con `dcfrec` en **1.577 de 1.645 (95,9 %)**; albarán sin `dcarec` → **6 de 42
  (14,3 %)**. `dcfrec.recide` = el del albarán en 2.308 de 2.312. Un albarán sin retención acaba, casi siempre, en una
  factura sin retención: se paga de más al subcontratista.

## Lo que solo se ve en la UI (verificación del humano)

- V1: que el escritorio muestra la `dcarec` escrita por la API y el total neto, y que abrir y grabar el albarán no la
  recalcula distinto (redondeo, `cueide`).
- V2: que la factura hecha desde un albarán de la API hereda su `dcarec` (M16), con F-053 en real.
- V3: con qué `cueide` deja el escritorio la `dcarec` cuando el `ctrrec` tiene otro (M11: 4,0 %).
