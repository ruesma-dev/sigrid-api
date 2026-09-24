<!-- progress/explore_F-006_modelo_parte.md -->
# F-006 · Exploración: qué escribe Sigrid al crear un parte de reclamación

> Spec-author, 2026-09-24. **Solo lecturas** por `POST /api/sql/read` de la API
> desplegada (`database: "ruesma"`, SQL con `?`). Sin datos personales: los
> propietarios y personas se citan por `ide`, nunca por nombre; el login de Sigrid,
> solo por su longitud. Sin secretos.
>
> Parte de referencia (capturas de `docs/referencia/postventa_pasos_crear_parte.md`):
> `RS26.08/0169`, `con.ide` **2811304**, obra `0677` (`con.ide` 2244405, `emp` 1),
> unidad postventa `con.ide` 2751478 (`con.tip` **707**).

## 1. Qué tablas escribe la UI (resuelve la pregunta «¿y cualquier otra?»)

Barrido de 37 tablas con columnas que apuntan a `con`/`rcp` (`conact`, `concam`,
`conext`, `conextmul`, `conseg`, `consegweb`, `contex`, `rca`, `rcc`, `rcd`, `rcf`,
`rcl`, `rcx`, `rcg`, `tar`, `act`, `verhis`, `dog`, `pertab`, `concnt`, `condir`,
`confam`, `conala`, `conavf`, `logfav`, `sol`, `contie`, `conzoa`, `conpli`,
`consub`, `concue`, `conauxcar`, `conauxgra`, `conque`, `conpac`, `condog`, `res`)
con `WITH p AS (SELECT CAST(? AS int) id) SELECT '<t>', COUNT(*) ... UNION ALL ...`
sobre 2811304 → **solo `tar` = 2** (las tareas nacen al pasar a PTE, no al crear).

Agregado sobre los 23.516 partes (`con.tip = 708`), por estado:

| est | n | sin `rcp` | con `rcpint` | con `tar` | con `conext` | con `contex` | con `rcg` | `rcx`/`concam`/`act` |
|---|---|---|---|---|---|---|---|---|
| 1 SAT | 3.520 | 1.512 | 3.502 | 1 | 1.846 | 0 | 23 | 0 |
| 3 PTE | 943 | 0 | 937 | 907 | 267 | 2 | 143 | 0 |
| 5 TER | 3.792 | 0 | 3.778 | 3.732 | 219 | 0 | 117 | 0 |
| 7 NPR | 693 | 0 | 687 | 335 | 548 | 498 | 342 | 0 |
| 9 CER | 14.568 | 0 | 14.514 | 7.851 | 9.488 | 83 | 7.686 | 0 |

Y **`dbo.log`**: la UI de escritorio escribe una fila de **alta** (`ope=1`).
`SELECT ... FROM dbo.log WHERE cod = 'RS26.08/0169'` → `ope 1` el 20260804 a las
104129 (= `rcp.hor`) y `ope 5` el 20260811. El 2026-09-23: **94 de 94** partes del
escritorio (`rcptip 0`) tienen su fila de alta y **0 de 14** del portal (`rcptip 3`).
Constantes en 500 altas (días 0804, 0922, 0923): `emp 1`, `ori 0`, `ope 1`,
`tab 'con'`, `tip 708`, `est 1`, `tex` NULL, `err` NULL, `fec = con.fec`, `res =
con.res` (407; los 93 restantes se editaron después). `log` no tiene IDENTITY; sus
`ide` son contiguos (máx 8.488.888 con 8.488.879 filas) → `MAX(ide)+1`.

**Conclusión:** un parte nuevo son `con` + `rcp` + `rcpint` (0..N) + `log` (alta), y
`conext` si se informa la referencia externa. `tar`, `rcg`, `contex` y el resto
aparecen **después** (PTE, adjuntos, rechazo). Ninguna de las cinco tablas tiene
IDENTITY ni trigger (`OBJECTPROPERTY(...,'TableHasIdentity')` = 0,
`sys.triggers` = 0) ni DEFAULT en columna alguna (`INFORMATION_SCHEMA.COLUMNS`).

**Anomalía medida:** 1.512 partes SAT **sin fila `rcp`** (1.508 de importaciones
masivas de 2021-2023 y 4 de 2026): la UI inserta `con` al aceptar la ventana
«Nuevo» y `rcp` al guardar la ficha; si se cierra sin guardar queda `con` suelto.
El endpoint escribe las dos en la misma transacción, así que no lo reproduce.

## 2. Columnas de cada fila y su origen

`con` (19 columnas; valores de los 23.516 partes): `emp 1`, `subtip 0`, `cee 0`,
`fecbaj 0`, `serie 0`, `hor 0`, `doc ''` (**100 %**), `del/delo/obr/ico ''` (salvo
127 con `ico '#FF0000.0'`, marca manual), `tex` NULL (22.882). `res` = descripción
corta (≤128; en 2811304, 32 caracteres = el texto de la ventana «Nuevo»). `fec` =
fecha de alta. `tiemod` nunca NULL ni 0: fecha OLE (días desde 1899-12-30) **en
UTC** — 2811304: 46238.362141 = 2026-08-04 08:41:29 frente a `rcp.hor` 104129 local
(CEST); 2841197: 18:20:12 frente a 202012. `est` → §4.

`rcp` (20 columnas) de 2811304: `upvide` 2751478, `pos` 1370496, `fec` 20260804,
`hor` 104129, `cliide` 2811575, `recide` 2811576, `cntide` 0, `tel`/`ele`/`solrcp`
NULL, `tex` = descripción larga, `rcpide` 0, `motrcp ''`, `rcptip` 1, `fecpre` 0,
`trcpide` 2, `resubi` 12 caracteres («Ubicación»), `texurg ''`, `ofcide` 143.

- **`rcp.pos` es global:** los 22.004 `pos` son distintos, múltiplos de 64 y siguen
  el orden de `ide` sin excepción (`ROW_NUMBER` por `ide` = por `pos` en 22.004) →
  `MAX(pos)+64` sobre **toda** `rcp`. Sin índice único: `rcp_posupvide (pos, upvide)`.
- **Propietario y persona salen de la UPV** (manual, p. 52): `rcp.cliide = upv.cliide`
  y `rcp.recide = upv.peride` en el 100 % del portal y del importador de 2026 (las
  diferencias históricas son UPV que cambiaron de propietario después); `cntide 0`
  en 1.656/1.656 manuales, 929/929 del importador y 309/309 del portal de 2026.
- **Manuales 2026 (`rcptip 1`, 1.656):** `tel`/`ele`/`solrcp` NULL, `motrcp ''`,
  `texurg ''`, `fecpre 0`, `rcpide 0` (1.654), `tex = con.res` (1.654).
- **`rcptip`** (forma de comunicación, entero): 0 = 1.940 (importador/escritorio sin
  informar), 1 = 12.808 («Escrita» en la captura), 3 = 7.256 (portal: todos traen
  `conext` `02`/`03` y `texurg` «Normal»/«Urgente»). El 2 no aparece.

`rcpint` (5 columnas): 2811304 tiene 2 filas, `pos 0`, `cauave 0`, `obrofcide` 2173
(oficio 0046, proveedor `con.tip 5` cod 41000012) y 2268 (oficio 0143, proveedor
5942), ambas de la obra 2244405. **Escritorio e importador → `pos 0`** (2026: 1.505,
471+126, 52+127, 329+3 filas); **portal → `pos` global `MAX+64`**. `cauave` 0/1
según «causante». 23.212 de 23.215 `rcpint` apuntan a un `obrofc` de la obra de su
UPV. Índice **único `(rcpide, obrofcide)`**. `ide` propio (máx 25.404) → `MAX+1`.
Partes con N intervinientes desde 2025: 1 → 4.475, 2 → 704, 3 → 14, 4 → 8, 5 → 1.

`rcp.ofcide` coincide con el oficio de algún interviniente en 1.600/1.658 manuales,
2.571/2.584 del portal y 708/969 del importador (desde 2025): **no es una regla**.
En cambio `rcp.ofcide` (≠0) **sí es un oficio de la obra** (`obrofc` de la obra de la
UPV) en 1.646/1.652 manuales, 2.577/2.583 del portal y 893/923 del importador.

## 3. Numeración de la serie

`dbo.sercon` (definición de series; `serconcod` está **vacía**: no hay tabla de
contadores): ide 213, `tip 708`, `cod 'RS<año2>.<mes>/'`, «Reclamaciones postventa»,
**`tam 4`**, `act 1`, `emp 1`, **`estini 1`**, `xjsini 'alta_con'`,
**`xjsvar 'trcpide=0003'`** (por eso la UI propone el tipo 3). La 214 es la preventa
`RP<año2>.<mes>/` (`emp 0`, `trcpide=0001`).

- **Se reinicia cada mes**: desde 2025, cada prefijo `RSaa.mm/` empieza en `0001`.
- **4 dígitos con ceros** en los 20.757 `RS` (todos `LEN(cod)=12`); máximo mensual
  medido 1.716 (RS26.01, 1.553 filas → hay huecos de borrados; se numera por MAX).
- **El mes del código es el de `con.fec`**: 20.756 de 20.757 (la excepción, de 2022).
- **Índice ÚNICO `con_emptipcod (emp, tip, cod)`**: detecta la colisión con un alta
  simultánea de la UI. `con_indide` único sobre `ide`. Sin SEQUENCE ni IDENTITY.
- Base con `READ_COMMITTED_SNAPSHOT` **OFF**, sin snapshot, compatibilidad 110,
  SQL Server 11.0.6020 (2012), intercalación **`Modern_Spanish_CI_AS`** (los `LIKE` y
  las comparaciones de texto no distinguen mayúsculas).

## 4. Estado inicial

`conest` para `tip 708`: 1 `SAT` SIN ATENDER (pos 32, portal «1.INCIDENCIA
REGISTRADA»), 3 `PTE`, 5 `TER`, 7 `NPR`, 9 `CER`. Nace en **1 `SAT`**: lo dice
`sercon.estini = 1` de la serie y lo confirman las 500 filas de alta de `log` (`est
1`) y el 100 % de los partes de escritorio del 2026-09-23 antes de tramitarse. El
2811304 está hoy en 3 porque se pasó a PTE el 0811 (fila `ope 5` y sus 2 `tar`).

## 5. Referencia externa (idempotencia)

`dbo.defext` define campos extendidos por tipo. Para `tip 708`: **ide 36, `cod
'RCPCLI'`, «Nº Referencia Externo»**, `camtip 0` (texto) — es el campo del
importador Excel; y `MR00`-`MR03` (motivos de rechazo). Se guarda en `dbo.conext`
(`conide`, `cod`, `camtip`, `camtab`, `valt varchar(80)`, `valn`, `valf`, `vali`,
`valm`, `valb`), índice **único `(conide, cod)`** y `conext_codvaln (cod, valn)`; sin
índice sobre `valt`. Filas `RCPCLI` hoy: 5.097, todas `camtip 0`, `camtab ''`, `valn 0`,
`valf 0`, `vali 0`, `valm`/`valb` NULL; `ide` propio (máx 56.285) → `MAX+1`.

Uso actual de `RCPCLI` por serie-año: RS21 3.746 (3.237 distintos, ≤15 caracteres),
RS22 333, RP20 1 → **referencias del promotor** con patrón `V#I2021…`, `VX4I2021…`,
`IDCI2021…`; RS23 1.006 → casi todo `OK`/`ok` (2 valores distintos); RS26 11 →
texto libre de motivos («según proyecto»), en partes NPR. **Conflicto real**: el
campo ya lo usan a mano para otras cosas y el importador para el promotor.

Alternativa medida: `con.doc` («Documento/Num Expediente», `varchar(24)`, índices
`con_empdoc` y `con_emptipdoc`, **no únicos**) está vacío en el 100 % de los 708;
es barato de buscar pero no se ve en la ficha del parte. `con.tex` (observaciones)
lo usan 634 partes.

## 6. Resolución por códigos

- **Obra:** `con.tip 42` + `cod` **+ `emp`**: el código `0677` existe en `emp 1`
  (2244405) **y en `emp 28`** (2287432). Único por `con_emptipcod`.
- **`emp`:** todas las UPV (1.328) y todos los partes (23.516) son `emp 1` =
  `sercon.emp` de la serie RS.
- **Unidad postventa:** `con.tip 707` + `cod` + `emp`, y `upv.obride` = la obra. El
  código empieza por el de la obra en 1.325 de 1.326. Máximo 232 UPV por obra.
  `conest 707`: 1 PRE, 5 GAR, 10 TG.
- **Tipo:** `auxtrcp` 1 `0001` PREVENTA, **2 `0002` PRIMER LISTADO POSTVENTA**, 3
  `0003` POST VENTA, 4 `0004` VISITA DE CORTESIA; ninguno de baja; `cod` único.
- **Clase:** `auxrcp` 1 `0001` Vicios o defectos, 2 `0002` Habitabilidad, 3 `0003`
  Estructura.
- **Oficio:** `auxofc`, 130 filas, `cod` único, ninguna de baja (`0143` → ide 143,
  `0046` → ide 46; los dos se llaman «Carpintería de madera»).
- **Oficios de la obra:** `obrofc (obride, pos, ofcide, prvide, coment)`, 39 filas en
  0677 (31 oficios, 37 proveedores, 3 sin proveedor). En todo Sigrid: **114 obras×oficio
  con varios proveedores y 51 tripletas `(obra, oficio, proveedor)` repetidas**; 110
  filas sin proveedor y 412 sin oficio. Proveedor = `con.tip 5` por `cod`.

## 7. Obra de prueba

La obra 0404 (la de F-005) **no tiene UPV ni oficios** (0 y 0). Obras con UPV: 0592,
0593, 0594, 0595, 0609, 0615, 0620, 0626, 0627, 0634, 0642, 0646, 0651, 0656, 0677…
No existe una obra de prueba con postventa: la elige el humano (pregunta abierta).
