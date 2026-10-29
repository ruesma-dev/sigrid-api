<!-- specs/F-018-descuento-por-linea/verificacion_manual.md -->
# F-018 · Verificación manual (R27; T19-T20)

Los comandos exactos de design §V. El resultado de cada paso (salidas, lo que no cuadre) se anota en
`progress/verificacion_F-018.md`.

**Cuándo y quién.** Todo después de la revisión aprobada (T18) y del despliegue, que lanza el **humano** (`func
publish`, con el prefijo `!`). F-018 no trae App Settings nuevas. Las lecturas y las previas (V1-V3 y V5) las lanza el
**líder** con autorización del humano para esa sesión; la grabación (V4), el **humano**, con autorización expresa para
esa escritura. Todo desde PowerShell 5.1, contra la API desplegada; nada por SQL directo. **Nunca `DELETE`**: lo grabado
se anula desde la UI de Sigrid.

**Sin secretos.** Ni la URL ni la clave ni los nombres de los recursos se escriben en ningún fichero: van en variables
de entorno de la consola.

```powershell
$env:SIGRID_API_APP = "<nombre de la Function App>"; $env:SIGRID_API_RG = "<su grupo de recursos>"
$env:SIGRID_API_BASE_URL = "<URL base de la Function App>"
$env:SIGRID_API_FUNCTION_KEY = az functionapp keys list --name $env:SIGRID_API_APP --resource-group $env:SIGRID_API_RG --query "functionKeys.default" -o tsv
```

## V0 · Setup

`Leer` lee por `sql/read` y **para si viene `truncated`**; `Q` imprime; `Fila` da la primera fila (un array, por
posición); `Llamar` llama a una ruta y, si responde 400, devuelve el cuerpo; `Lineas` resume las líneas de respuesta.

```powershell
$base = $env:SIGRID_API_BASE_URL; $headers = @{ "x-functions-key" = $env:SIGRID_API_FUNCTION_KEY }
function Leer($sql, $p = @(), $max = 1000) {
  $b = @{ database = "ruesma"; sql = $sql; parameters = $p; max_rows = $max } | ConvertTo-Json -Depth 5
  $r = Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b))
  if ($r.truncated) { throw "Lectura truncada: no vale" }; $r }
function Q($sql, $p = @()) { Leer $sql $p | ConvertTo-Json -Depth 8 }
function Fila($sql, $p = @()) { (Leer $sql $p).rows[0] }
function Llamar($ruta, $cuerpo) {
  $b = $cuerpo | ConvertTo-Json -Depth 6
  try { Invoke-RestMethod -Uri "$base/api/$ruta" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) }
  catch { $_.ErrorDetails.Message } }
function Lineas($r) { $r.lineas | Select-Object indice, referencia_linea, ctrpro_ide, cantidad, precio, total, iva_cuota, dto, precio_bruto | Format-Table }
function Pct($texto) { [double]("$texto".Trim().TrimEnd("%").Trim().Replace(",", ".")) }
```

**Tras desplegar, antes que nada:** una previa de `sigrid/albaran` **sin** `dto` (la de F-015 V2, por ejemplo) y se
mira que la respuesta no trae `dto` ni `precio_bruto` en ninguna línea y que `filas.dca.impbru` = `filas.dca.totbas`.

## V1 · Selección (lectura)

**V1a · Línea sin vincular con dto del escritorio** (obra 0692, `MA9999`). Columnas: 0 `con.cod`, 1 `proveedor CIF`,
2 `can`, 3 `tar`, 4 `dto`, 5 `pre`, 6 `tot`, 7 `res`, 8 `unimed`, 9 `dca.impbru`, 10 `dca.totbas`, 11 `dca.ide`:

```powershell
$A = Fila "SELECT TOP 1 c.cod, d.entcif, p.can, p.tar, p.dto, p.pre, p.tot, p.res, p.unimed, d.impbru, d.totbas, d.ide FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide JOIN dbo.con c ON c.ide = d.ide JOIN dbo.con o ON o.ide = d.obride JOIN dbo.con pc ON pc.ide = p.proide WHERE c.tip = ? AND c.cod LIKE ? AND o.tip = ? AND o.cod = ? AND pc.cod = ? AND p.docoritip <> ? AND p.dto LIKE ? AND p.dto NOT LIKE ? AND p.can > ? ORDER BY c.ide DESC" @(14, "AC__/%", 42, "0692", "MA9999", 44, "%[%]", "%[^0-9,% ]%", 0)
$A
```

**V1b · `ctrpro` con dto `N%` y un albarán del escritorio vinculado** (empresa 1, `canser` < `can`, `tar` ≠ 0).
Columnas: 0 `ctrpro.ide`, 1 `pre`, 2 `tar`, 3 `dto`, 4 `ctr` cod, 5 obra cod, 6 `entcif`, 7 `can` de la línea del
albarán, 8 su `pre`, 9 su `tot`, 10 cod del albarán:

```powershell
$B = Fila "SELECT TOP 1 k.ide, k.pre, k.tar, k.dto, c.cod, o.cod, t.entcif, a.can, a.pre, a.tot, ca.cod FROM dbo.ctrpro k JOIN dbo.ctr t ON t.ide = k.docide JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride JOIN dbo.dcapro a ON a.linoriide = k.ide AND a.docoritip = ? JOIN dbo.con ca ON ca.ide = a.docide WHERE c.tip = ? AND o.tip = ? AND o.emp = ? AND ca.cod LIKE ? AND k.dto LIKE ? AND k.dto NOT LIKE ? AND k.tar <> ? AND k.canser < k.can AND a.can > ? ORDER BY ca.ide DESC" @(44, 44, 42, 1, "AC__/%", "%[%]", "%[^0-9,% ]%", 0, 0)
$B
```

**V1c · Contrato con dto y una proforma del escritorio desde 2025** (M50). Columnas: 0 `ctr.ide`, 1 cod, 2 obra cod,
3 `ide` de la proforma, 4 su cod, 5 `fec`; y sus líneas vinculadas a un `ctrpro` con dto (0 `ctrpro.ide`, 1
`ctrpro.pre`, 2 `can`, 3 `pre`, 4 `tot`, 5 `tar`, 6 `dto`, 7 `res`):

```powershell
$C = Fila "SELECT TOP 1 t.ide, c.cod, o.cod, d.ide, cd.cod, cd.fec FROM dbo.dca d JOIN dbo.con cd ON cd.ide = d.ide JOIN dbo.ctr t ON t.ide = d.ctride JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride WHERE cd.tip = ? AND cd.cod LIKE ? AND d.cla = ? AND cd.fec >= ? AND EXISTS (SELECT 1 FROM dbo.dcapro p JOIN dbo.ctrpro k ON k.ide = p.linoriide WHERE p.docide = d.ide AND p.docoritip = ? AND p.can <> ? AND k.dto LIKE ? AND k.dto NOT LIKE ? AND k.tar <> ?) ORDER BY cd.fec DESC, cd.ide DESC" @(14, "PROF%", 141, 20250101, 44, 0, "%[%]", "%[^0-9,% ]%", 0)
$lineasC = (Leer "SELECT k.ide, k.pre, p.can, p.pre, p.tot, p.tar, p.dto, p.res FROM dbo.dcapro p JOIN dbo.ctrpro k ON k.ide = p.linoriide WHERE p.docide = ? AND p.docoritip = ? AND p.can <> ? AND k.dto LIKE ? AND k.dto NOT LIKE ? AND k.tar <> ? ORDER BY p.pos, p.ide" @($C[3], 44, 0, "%[%]", "%[^0-9,% ]%", 0)).rows
$C; $lineasC | ForEach-Object { $_ -join " | " }
```

Si alguna lectura no devuelve fila, se anota y se para: no se inventa el caso.

## V2 · Previa sin vincular con dto (gemela de V1a)

La línea de V1a con el mismo producto, cantidad, bruto (`tar`) y dto, sin contrato:

```powershell
$cuerpoA = @{ database = "ruesma"; cod_obra = "0692"; cod_contrato = $null; cif_proveedor = $A[1]; usu = "prueba"
  referencia_externa = "ALB-prueba-F018-1"; su_referencia = "prueba-F018-1"; commit = $false
  lineas = @(@{ referencia_linea = "1"; producto = "MA9999"; descripcion = "$($A[7])".Trim(); unidad = "$($A[8])".Trim(); cantidad = $A[2]; precio = $A[3]; dto = (Pct $A[4]) }) }
$r = Llamar "sigrid/albaran" $cuerpoA
$r.estado; Lineas $r; $r.filas.dcapro | Select-Object tar, dto, pre, tot, ivacuo
$r.filas.dca | Select-Object impbru, totbas; $r.filas.mov | Select-Object pre, prc, almpma
```

Se mira: `previsto`; `tar`, `dto`, `tot` y `pre` iguales a `$A[3]`, `$A[4]`, `$A[6]` y `$A[5]` (`pre` = `tot`/`can`);
`filas.dca.impbru` = round(`can`·`tar`, 2) y `totbas` = `tot`; `filas.mov.pre` = el neto; la línea de respuesta con
`dto` y `precio_bruto` = `tar`; sin avisos de precio ni de dto.

## V3 · Previas vinculadas contra el `ctrpro` de V1b

```powershell
function CuerpoB($ref, $linea) { @{ database = "ruesma"; cod_obra = $B[5]; cod_contrato = $B[4]; cif_proveedor = $B[6]; usu = "prueba"
  referencia_externa = $ref; su_referencia = $ref; commit = $false; lineas = @($linea) } }
$r1 = Llamar "sigrid/albaran" (CuerpoB "ALB-prueba-F018-2" @{ referencia_linea = "1"; ctrpro_ide = $B[0]; cantidad = $B[7]; precio = $B[2]; dto = (Pct $B[3]) })
$r2 = Llamar "sigrid/albaran" (CuerpoB "ALB-prueba-F018-3" @{ referencia_linea = "1"; ctrpro_ide = $B[0]; cantidad = $B[7]; precio = $B[2]; dto = ((Pct $B[3]) + 1) })
$r3 = Llamar "sigrid/albaran" (CuerpoB "ALB-prueba-F018-4" @{ referencia_linea = "1"; ctrpro_ide = $B[0]; cantidad = $B[7]; precio = $B[1] })
foreach ($r in @($r1, $r2, $r3)) { $r.estado; Lineas $r; $r.filas.dcapro | Select-Object tar, dto, pre, tot; $r.filas.dca | Select-Object impbru, totbas; $r.lineas.avisos }
```

Se mira: **r1** (su bruto y su dto) sin avisos de precio ni de dto, `tot` = `$B[9]` del albarán del escritorio para
esa cantidad; **r2** (otro dto) con `dto_distinto_del_contrato` (los dos porcentajes en el mensaje) y sin
`precio_distinto_del_contrato`; **r3** (sin `dto`, con su `pre` neto, R15) sin avisos, `tar`/`dto` del `ctrpro`, `tot`
= `$B[9]` y `pre` = `$B[8]` (±1 céntimo en `tot` solo si el albarán del escritorio se hizo con otro `pre`), y la línea
de respuesta con `dto` y `precio_bruto`.

## V5 · Previa de proforma de mes contra el contrato de V1c

Las líneas de V1c (las vinculadas a un `ctrpro` con dto), con `precio` = el `ctrpro.pre`, como manda hoy `proformas`, y
`otra_del_mes` para que salga `previsto`:

```powershell
$lin = @(); $mes = [decimal]0; $i = 0
foreach ($l in $lineasC) { $i++; $d = "$($l[7])".Trim(); if (-not $d) { $d = "-" }; if ($d.Length -gt 128) { $d = $d.Substring(0, 128) }
  $lin += @{ referencia_linea = "V$i"; ctrpro_ide = $l[0]; cantidad = $l[2]; precio = $l[1]; descripcion = $d }
  $mes += [math]::Round([decimal]$l[2] * [decimal]$l[1], 2, [MidpointRounding]::AwayFromZero) }
$p = Llamar "sigrid/proforma" @{ database = "ruesma"; usu = "prueba"; referencia_externa = "PRF-prueba-F018-1"; cod_obra = $C[2]
  cod_contrato = $C[1]; periodo = [int]"$($C[5])".Substring(0, 6); importe_mes = [double]$mes; otra_del_mes = $true; commit = $false; lineas = $lin }
$p.estado; Lineas $p; $p.filas.dcapro | Select-Object linoriide, can, tar, dto, pre, tot; $p.filas.dca | Select-Object impbru, totbas; $p.avisos
```

Se mira: `previsto`; cada línea con `tar`/`dto` del `ctrpro`, `tot` y `pre` iguales a los de la proforma del escritorio
(`$lineasC` columnas 4 y 3; ±1 céntimo por línea solo donde Sigrid partió de otro `pre`), `dto` y `precio_bruto` en la
respuesta, `filas.dca.impbru` = Σ round(`can`·`tar`, 2) y `totbas` = Σ `tot`; los avisos de la hoja, los de siempre.

## V4 · Grabación (T20; el humano, con autorización expresa para esta escritura)

El cuerpo de V2 (o el de r1 de V3) con otra referencia y `commit:true`:

```powershell
$cuerpoG = $cuerpoA.Clone(); $cuerpoG.referencia_externa = "ALB-prueba-F018-5"; $cuerpoG.su_referencia = "prueba-F018-5"; $cuerpoG.commit = $true
$g = Llamar "sigrid/albaran" $cuerpoG
$g.estado; $g.con_ide; $g.cod; Lineas $g
Q "SELECT ide, pos, tar, dto, pre, tot, ivacuo FROM dbo.dcapro WHERE docide = ? ORDER BY pos" @($g.con_ide)
Q "SELECT impbru, impnet, totbas, totdoc, tot, synckey FROM dbo.dca WHERE ide = ?" @($g.con_ide)
Q "SELECT ide, canent, cansal, pre, prc, almpma FROM dbo.mov WHERE docide = ?" @($g.con_ide)
```

Se mira: `creado`; las filas leídas iguales a las de la respuesta y a las de V2. **Revisión en la UI de Sigrid**:
P.Bruto, Dto, Precio, Importe y totales como en el albarán del escritorio de V1a; abrir la línea y cerrarla **sin
cambiar nada**, y releer la `dcapro` de arriba: no debe haber recalculado nada. Repetición, el mismo cuerpo:

```powershell
$h = Llamar "sigrid/albaran" $cuerpoG
$h.estado; $h.con_ide; Lineas $h
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("ALB-prueba-F018-5")
```

Se mira: `idempotente`, el mismo `con_ide`, las líneas sin `dto` ni `precio_bruto` (D8) y una sola fila. Después,
**anularlo desde la UI de Sigrid** (nunca `DELETE`) y comprobar en lectura que no queda nada (0, 0 y 0):

```powershell
Q "SELECT COUNT(*) AS n FROM dbo.con WHERE ide = ?" @($g.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.dcapro WHERE docide = ?" @($g.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("ALB-prueba-F018-5")
```

Tras V4, el líder avisa a albaranes (su F-110) y a proformas de que F-018 está desplegada (T20).
