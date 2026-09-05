# progress/explore_F-004_mediciones.md

# F-004 · Mediciones T1/T2 contra el ERP (solo lectura)

| | |
|---|---|
| **Fecha** | 2026-09-05 · todo lo de aquí es **[MEDIDO]** salvo lo marcado [INFERIDO] |
| **Vía** | `POST /api/sql/read` de la API desplegada, script temporal en el scratchpad; ninguna escritura, ningún `commit` |
| **Adaptaciones** | `gra` no tiene `hor` (Q4 se ejecutó sin ella). `tex` y `cam` son `text`: en el `GROUP BY` van como `CAST(... AS varchar(400))`. `rcg` real tiene 7 columnas (`feclee`, `fecalt` no constan en `sigrid_tablas.md`) |
| **Volúmenes** | `ruesma.gra` 284.096 filas · `ruesma_rep.gra` 359.572 · `dbo.log` 8.442.751 (última `fec` 20260905) |

## 1 · T2 — Preguntas abiertas

### Q4 · Formato de `gra.cod` (`SELECT TOP (200) ide, cod, usu, fec, gratipide, vin FROM dbo.gra ORDER BY ide DESC`, ruesma, 200 filas)

| Comprobación (ruesma, 284.096 filas) | Resultado |
|---|---|
| `cod LIKE '[0-9]{18}.' + usu` (14 dígitos fecha-hora + 4 dígitos + `.` + login) | **252.155** (88,8 %) · en la documental 325.204 de 359.572 |
| `LEFT(cod,8) = fec` | 250.505: en ~1.650 filas `fec` es posterior al sello (edición de la fecha desde la UI, p. ej. `202609021115143453.acarretero` con `fec=20260903`) |
| Longitud de `cod` | 11 a 68 |
| Excepciones (31.941) | **El nombre del fichero como `cod`**: `CTR_01_CTSB25_0709_7.doc`, `29_NO2604_0021.pdf`, `1_707_0677_03VILLA 7_.pdf`. Por `gratipide`: 9 (28.481, 2017-2026), 1, 3, 39 (818, hasta 20260903), 0 (434), 37… Vienen de importaciones masivas/otro módulo |
| Dentro de `gratipide=35` | **3.680 de 3.680** con el formato sello+login |
| Los 4 dígitos `dddd` | min `0005`, max `9998`, **solo 1.268 valores distintos** en 252.155 filas; `0041` aparece 4.689 veces (1,9 %), el resto ~500 cada uno. En el mismo segundo **no crecen con `ide`** (290660 → `8419`, 290661 → `5565`; 291868 `0617`, 291869 `0905`) |
| Colisiones de segundo | Máximo 2 filas por segundo desde `ide` 290.000 (mismo o distinto usuario); siempre distinto `dddd` |

[INFERIDO] `dddd` no es secuencia ni milisegundos: un generador pseudoaleatorio con pocos estados (patrón de `Rnd` sin semilla, que repite `0041` al arrancar). **Implicación para la decisión**: no hay indicio de que Sigrid interprete el sello ni los 4 dígitos —tolera 31.941 `cod` que son nombres de fichero, incluidos 818 de 2021-2026 del mismo usuario de Posventa— así que conservar el formato y sacar `dddd` del `sha256` es, como mínimo, tan bueno como lo que hace el ERP; la unicidad la da el índice `emp+cod`, no el formato.

### Q5 · `gra.guid`

| Base | `COUNT(*)` | `guid` no vacío |
|---|---|---|
| ruesma | 284.096 | **0** |
| ruesma_rep | 359.572 | **0** |

`SELECT TOP (10) ... WHERE guid <> ''` devuelve 0 filas en ambas. **Implicación**: Sigrid no usa `guid` en ninguna fila; el defecto del diseño (idempotencia por contenido, `guid` sin escribir) no choca con nada del ERP, y la columna quedaría libre si el humano prefiriese usarla.

### Q7 · `dbo.log`

| Consulta (ruesma) | Resultado |
|---|---|
| `SELECT COUNT(*) FROM dbo.log WHERE tab = 'gra'` | **0** |
| `SELECT TOP (20) * FROM dbo.log WHERE tab = 'gra'` | 0 filas (columnas: ide, emp, ori, ope, fec, hor, usu, tab, tip, cod, res, tex, est, err) |
| `tab LIKE '%gra%' OR tab LIKE '%rcg%'` | solo `auxgra` = 46 (altas/ediciones del catálogo de clases, 2021-2024) |
| Top `tab` | `con` 5.156.664 · `''` 2.925.536 · `cab` 358.109 · `rcc` 874 · `auxcno` 502 · `auxpronat` 321 · … |
| Log de `aechevarria` el 20260818 entre 11:30 y 11:50 (la pareja se importó a las 11:40:39) | 2 filas: 11:46:12 `ope=5` «Proceso de Cambio de estado (RCP Seleccionados: 1): Cerrar parte» y 11:46:33 `tab=con tip=708 cod=RS26.08/0123` «Cerrar parte». **Ninguna a las 11:40** |
| Log del concepto `RS26.08/0123` (todas las fechas) | 3 filas: alta `ope=1` 20260804, «Pasar a pendiente» 20260811, «Cerrar parte» 20260818. **Nada de la importación del gráfico** |
| `auxgra.conlog` («Generar log») | **0 en las 48 clases**, incluida la 35 |

**Implicación**: el ERP no deja rastro en `dbo.log` al importar un gráfico de la clase 35 (ni de ninguna: `tab='gra'` no existe en 8,4 M de filas); el defecto del diseño (no escribir `log`) se sostiene, y no hay «cuarta escritura». Matiz: `conlog=0` en todas las clases, así que lo medido es el comportamiento con el log desactivado por catálogo.

## 2 · T1 — Pareja real de parte firmado

Distribución `gratipide, vin` en ruesma: `35/3` = **3.680** filas (todas las de clase 35; no hay 35 con otro `vin`). En la documental **no existe `gratipide=35`**: solo `0/3` (353.178) y `34/3` (6.394). Pareja elegida: la más reciente, `202608181140392614.aechevarria`.

### 2.1 · Las 29 columnas × 2 bases (`WHERE cod = ?`, 1 fila en cada base)

| Col | ruesma (ide 296221) | ruesma_rep (ide 357208) | | Col | ruesma | ruesma_rep |
|---|---|---|---|---|---|---|
| ide | 296221 | 357208 | | tipocu | 0 | 0 |
| cod | `202608181140392614.aechevarria` | **igual** | | texrev | `''` | `''` |
| emp | 1 | **1** | | numrev | 0 | 0 |
| res | `PARTE FIRMADO` | **`''`** | | salfec | 0 | 0 |
| tex | NULL | NULL | | salhor | 0 | 0 |
| cla | `''` | `''` | | salusu | `''` | `''` |
| usu | aechevarria | aechevarria | | saltex | `''` | `''` |
| fec | 20260818 | 20260818 | | mntide | 0 | 0 |
| nom | `RS26.08 - 0123 PARTE FIRMADO.pdf` | igual | | guid | `''` | `''` |
| nomori | igual que `nom` | igual | | graant | 0 | 0 |
| ima (DATALENGTH) | **NULL** | **242.534 bytes** | | anx | 0 | 0 |
| gratipide | 35 | **0** | | ori | 0 | 0 |
| vin | 3 | 3 | | pul (DATALENGTH) | NULL | NULL |
| estcon | 0 | 0 | | tip | 0 | 0 |
| cam | NULL | NULL | | | | |

### 2.2 · Enlace con el concepto

| Consulta | Resultado |
|---|---|
| `SELECT * FROM dbo.rcg WHERE gra = 296221` | ide 296661 · con **2811179** · gra 296221 · pos **64** · cla 0 · feclee 0 · fecalt 0 |
| `SELECT ide, tip, emp, cod, res FROM dbo.con WHERE ide = 2811179` | tip **708** · emp **1** (= `gra.emp`, confirmado) · cod `RS26.08/0123` · res «Sellado de encuentro de falsos techos de porches» |
| `SELECT * FROM dbo.rcg WHERE con = 2811179` | la misma única fila |
| `SELECT MAX(pos), COUNT(*) FROM dbo.rcg WHERE con = 2811179` | 64 · 1 |
| `SELECT * FROM dbo.auxgra WHERE ide = 35` | cod `PV002` · res «POSTVENTA:Fotos Reparaciones» · pos 2240 · fecbaj 0 · conlog 0 · tiplec 0 · tipver 0 · **tipaso `UPV,RCP,TAR`** · tammax 0 · tipfic 0 · rolacc/roledi vacíos |

`rcg.pos` para los 3.680 gráficos de clase 35: 64 (795), 128 (1.991), 192 (448), 256 (232), … 832 (2): siempre **64 × posición dentro del concepto** (`n_rcg_con=1 → 64`, `2 → 128`, `3 → 192`). Confirma L4 del design (`MAX(pos)+64`). En todo `rcg` no hay `pos=0` (min 8, max 26.744). Cada gráfico de clase 35 tiene **exactamente 1** fila en `rcg`; `con.tip` de esos conceptos: **708** (3.677) y 707 (3).

### 2.3 · Columnas no variables (`GROUP BY ... WHERE gratipide = 35 AND vin = 3`)

**ruesma** (17 grupos, 3.680 filas). Constantes en las 3.680: `estcon=0`, `tipocu=0`, `numrev=0`, `salfec=0`, `salhor=0`, `salusu=''`, `saltex=''`, `mntide=0`, `graant=0`, `anx=0`, `ori=0`, `tip=0`, `cam=NULL`, `tex=NULL`, `cla=''`, `ima=NULL` (3.680/3.680), `guid=''`. **NO constantes**: `res` (texto libre: `PARTE FIRMADO` 3.197, `''` 413, `PARTE` 27, `FOTO` 26, `PARTE FIRMADO 2` 4, erratas…) y `texrev` (`''` 3.267; 413 filas llevan «PARTE FIRMADO»/erratas ahí, escrito en el campo equivocado). `vin` = 3 por construcción del filtro.

**ruesma_rep**, consulta literal de la spec: **0 filas** (no hay `gratipide=35`). Con `JOIN ruesma.dbo.gra g ON g.cod = d.cod AND g.emp = d.emp WHERE g.gratipide = 35`: **1 solo grupo, 3.679 filas**: `res=''`, `gratipide=0`, `vin=3`, `estcon=0`, `tipocu=0`, `texrev=''`, `numrev=0`, `salfec=0`, `salhor=0`, `salusu=''`, `saltex=''`, `mntide=0`, `graant=0`, `anx=0`, `ori=0`, `tip=0`, `cam=NULL`, `tex=NULL`, `cla=''`. Además en las 3.679: `nom`, `nomori`, `usu`, `fec` **iguales** a los de negocio, `nom = nomori`, `ima` **nunca NULL**. `rcg`: `cla=0`, `feclee=0`, `fecalt=0` en las 3.680.

**Huérfano**: 1 fila de negocio con `gratipide=35` **sin pareja** en la documental (3.680 − 3.679). No se ha identificado cuál (fuera de encargo); conviene mirarla antes de T19 porque es un caso real de «negocio sin binario».

## 3 · Lo que cambia o confirma para el diseño (sin decidir)

- Fila documental: `gratipide=0` y `res=''` **siempre**, aunque en negocio sea 35 / «PARTE FIRMADO». El constructor E5 no debe copiar `gratipide` ni `res` de la petición.
- E6 inserta `ide, con, gra, pos, cla`; la tabla tiene además `feclee` y `fecalt` (0 en todo lo medido). Comprobar si admiten NULL/default o si hay que fijarlos a 0.
- `res` de negocio es texto libre del usuario: el valor `'PRUEBA API - BORRAR'` del plan de T19/T20 es compatible.
- No se pudo medir: la fila huérfana concreta; el tipo exacto de `feclee`/`fecalt` (no están en el diccionario). Todo lo demás del encargo, medido.
