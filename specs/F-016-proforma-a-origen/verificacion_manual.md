<!-- specs/F-016-proforma-a-origen/verificacion_manual.md -->
# F-016 · Verificación manual (R24; T17-T18)

Los comandos exactos de T17 y T18, con el modelo de
[`F-007/verificacion_manual.md`](../F-007-registrar-proforma/verificacion_manual.md). El resultado de cada paso
(salidas, tiempos, lo que no cuadre) se anota en `progress/verificacion_F-016.md`. V2 es además la verificación de T15:
las dos consultas de `contrato_proformas.md` v1.2 §2.3, probadas en lectura sobre cadenas reales.

**Cuándo y quién.** Todo después de la revisión aprobada (T19). El despliegue (D1-D3) y las grabaciones (G) los lanza
el **humano**, cada escritura con autorización expresa para esa llamada. Las lecturas y las previas (V1-V6) las lanza el
líder con autorización del humano para esa sesión. Todo desde PowerShell 5.1 **salvo D2** (`func publish` lo lanza el
humano con el prefijo `!`, que corre en bash). Contra la API desplegada; nada por SQL directo. **Nunca `DELETE`**: lo
grabado se anula desde la UI de Sigrid.

**Sin secretos.** Ni la URL ni la clave ni los nombres de los recursos se escriben en ningún fichero: van en variables
de entorno de la consola. Los JSON de App Settings se dejan en `$env:TEMP`, fuera del repositorio.

```powershell
$env:SIGRID_API_APP = "<nombre de la Function App>"; $env:SIGRID_API_RG = "<su grupo de recursos>"
$env:SIGRID_API_BASE_URL = "<URL base de la Function App>"
$env:SIGRID_API_FUNCTION_KEY = az functionapp keys list --name $env:SIGRID_API_APP --resource-group $env:SIGRID_API_RG --query "functionKeys.default" -o tsv
```

## V0 · Setup (antes de D3)

`Leer` lee por `sql/read` y **para si viene `truncated`**; `Q` imprime; `Fila` da la primera fila; `Llamar` llama a una
ruta y, si responde 400, devuelve el cuerpo. `Puntas` y `LineasDe` son **las dos consultas del contrato v1.2 §2.3**,
copiadas tal cual. Columnas de `Puntas`: 0 `ide`, 1 `cod`, 2 `fec`, 3 `totbas`, 4 `docoriide`, 5 `importe_cadena`. De
`LineasDe`: 0 `ide`, 1 `pos`, 2 `linoriide`, 3 `docoritip`, 4 `partida`, 5 `producto`, 6 `res`, 7 `unimed`, 8 `pre`,
9 `can`, 10 `canoriori`.

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
$SQL_PUNTAS = "SELECT c.ide, c.cod, c.fec, d.totbas, d.docoriide, (SELECT ISNULL(SUM(ROUND(p.canoriori * p.pre, 2)), 0) FROM dbo.dcapro p WHERE p.docide = d.ide) AS importe_cadena FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND d.docoritip = ? AND NOT EXISTS (SELECT 1 FROM dbo.dca s JOIN dbo.con cs ON cs.ide = s.ide WHERE cs.tip = ? AND s.ctride = d.ctride AND s.docoriide = d.ide) ORDER BY c.fec DESC, c.ide DESC"
$SQL_LINEAS = "SELECT p.ide, p.pos, p.linoriide, p.docoritip, ISNULL(pp.cod, '') AS partida, ISNULL(pc.cod, '') AS producto, p.res, p.unimed, p.pre, p.can, p.canoriori FROM dbo.dcapro p LEFT JOIN dbo.obrparpar pp ON pp.ide = p.paride LEFT JOIN dbo.con pc ON pc.ide = p.proide WHERE p.docide = ? ORDER BY p.pos, p.ide"
function Puntas($ctride) { (Leer $SQL_PUNTAS @(14, $ctride, 1, 14)).rows }
function LineasDe($ide) { (Leer $SQL_LINEAS @($ide)).rows }
function CodDe($ide) { (Fila "SELECT cod FROM dbo.con WHERE ide = ?" @($ide))[0] }
function Ctr($ctride) { Fila "SELECT c.cod, o.cod FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride WHERE t.ide = ?" @($ctride) }
function Desc($l) { $d = "$($l[6])".Trim(); if (-not $d) { $d = "-" }; if ($d.Length -gt 128) { $d = $d.Substring(0, 128) }; $d }
# La hoja de la PUNTA misma (sus lineas con MES), a origen: la API debe responder `existente`.
function HojaDe($ctride, $punta, $ref) {
  $c = Ctr $ctride; $lineas = @(); $mes = [decimal]0
  foreach ($l in (LineasDe $punta[0])) {
    if ([decimal]$l[9] -eq 0) { continue }
    $x = @{ referencia_linea = "L$($l[1])"; cantidad = $l[9]; precio = $l[8]; descripcion = (Desc $l) }
    if ($l[3] -eq 44 -and $l[2] -gt 0) { $x.ctrpro_ide = $l[2] } else { $x.producto = $l[5]; $x.partida = $l[4] }
    $lineas += $x; $mes += [math]::Round([decimal]$l[9] * [decimal]$l[8], 2, [MidpointRounding]::AwayFromZero) }
  $h = @{ database = "ruesma"; usu = "prueba"; referencia_externa = $ref; cod_obra = $c[1]; cod_contrato = $c[0]
          periodo = [int]"$($punta[2])".Substring(0, 6); importe_mes = [double]$mes; modo = "origen"; commit = $false; lineas = $lineas }
  if ($punta[4] -gt 0) { $h.proforma_anterior = CodDe $punta[4] } else { $h.primera_de_cadena = $true }
  $h }
# La del mes SIGUIENTE encadenada a la punta: continua sus $n primeras lineas de contrato con cantidad 1.
function Siguiente($ctride, $punta, $ref, $n = 2) {
  $c = Ctr $ctride; $lineas = @(); $mes = [decimal]0
  foreach ($l in (LineasDe $punta[0])) {
    if ($lineas.Count -ge $n) { break }; if ($l[3] -ne 44 -or $l[2] -le 0) { continue }
    $lineas += @{ referencia_linea = "S$($l[1])"; ctrpro_ide = $l[2]; linea_anterior = $l[0]; cantidad = 1; precio = $l[8]; descripcion = (Desc $l) }
    $mes += [math]::Round([decimal]$l[8], 2, [MidpointRounding]::AwayFromZero) }
  $f = [datetime]::ParseExact("$($punta[2])", "yyyyMMdd", $null).AddMonths(1); if ($f -gt (Get-Date)) { $f = Get-Date }
  @{ database = "ruesma"; usu = "prueba"; referencia_externa = $ref; cod_obra = $c[1]; cod_contrato = $c[0]
     periodo = [int]$f.ToString("yyyyMM"); importe_mes = [double]$mes; modo = "origen"; proforma_anterior = $punta[1]
     commit = $false; lineas = $lineas } }
function Lineas($r) { $r.lineas | Select-Object indice, referencia_linea, linea_anterior, arrastrada, ctrpro_ide, cantidad, cantidad_anterior_cadena, cantidad_origen_cadena | Format-Table }
```

`HojaDe` manda las líneas sin vincular con su producto: si alguno no está en `SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO`
ni en el contrato, da `producto_no_permitido`; se anota y se elige otra punta.

## D · Despliegue (T17; el humano)

**D1 · La App Setting nueva, cerrada.** Booleana: un valor que no lo sea impide arrancar la Function (y tumba todas las
rutas). Fichero ASCII sin BOM, validado con `Settings` antes de subirlo:

```powershell
$f = "$env:TEMP\f016_appsettings.json"
'[{"name":"SIGRID_PROFORMA_ORIGEN_ENABLED","value":"false","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline $f
$env:F016_JSON = $f
@'
import json, os
for s in json.load(open(os.environ["F016_JSON"], encoding="ascii")):
    os.environ[s["name"]] = s["value"]
for k, v in {"SQL_DRIVER": "x", "SQL_SERVER_HOST": "x", "SQL_SERVER_PORT": "1",
             "SQL_SERVER_USERNAME": "x", "SQL_SERVER_PASSWORD": "x"}.items():
    os.environ[k] = v
from config.settings import Settings
s = Settings()
print(s.sigrid_proforma_origen_enabled, s.sigrid_proforma_write_enabled)
'@ | .venv\Scripts\python -
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$f"
az functionapp config appsettings list -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --query "[?starts_with(name, 'SIGRID_PROFORMA_') || name == 'SIGRID_DOMAIN_WRITE_ENABLED'].{n:name, v:value}" -o table
```

Se mira: el `python` imprime `False False` (si falla, no se sube); el `list` enseña las **seis** `SIGRID_PROFORMA_*`, con
`SIGRID_PROFORMA_WRITE_ENABLED` y `SIGRID_PROFORMA_ORIGEN_ENABLED` a `false` y las otras cuatro como las dejó F-007.

**D2 · Publicar** desde la rama revisada (o `dev` tras el merge). El humano, con el prefijo `!` y la orden literal (en
lugar de `<app>` teclea el nombre de la Function App):

```text
! func azure functionapp publish <app> --python
```

**D3 · Lo primero, un dry-run de `sigrid/albaran`** (tras V0), como D3 de F-007:

```powershell
$U = Fila "SELECT t.ide, t.entcif FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride WHERE c.tip = ? AND c.cod = ? AND o.tip = ? AND o.emp = ? AND o.cod = ?" @(44, "CTSU16/0206", 42, 1, "0404")
$lineaU = Fila "SELECT TOP 1 p.ide, p.pre FROM dbo.ctrpro p WHERE p.docide = ? AND p.can > p.canser ORDER BY p.ide" @($U[0])
$a = Llamar "sigrid/albaran" @{ database = "ruesma"; cod_obra = "0404"; cod_contrato = "CTSU16/0206"; cif_proveedor = $U[1]; usu = "prueba"
  referencia_externa = "ALB-prueba-F016-1"; su_referencia = "prueba-F016-1"; commit = $false
  lineas = @(@{ referencia_linea = "1"; ctrpro_ide = $lineaU[0]; cantidad = 1; precio = $lineaU[1] }) }
$a.estado
```

Se mira: `previsto`. Un 500/503 o un arranque fallido: `az functionapp config appsettings delete -g $env:SIGRID_API_RG
-n $env:SIGRID_API_APP --setting-names SIGRID_PROFORMA_ORIGEN_ENABLED`, se repite D3 y se para.

## V · Previas (T17; sin escribir)

**V1 · Las llaves** (se lanza justo después de V2, con su `$ctride` y su `$p`). Con la hoja de la punta, un
`commit:true` a origen:

```powershell
$h = HojaDe $ctride $p "PRF-prueba-F016-llave"; $h.commit = $true; Llamar "sigrid/proforma" $h
```

Se mira: 400 `escritura_proformas_deshabilitada` (la de F-007 se mira **antes** que la de origen, R4). No escribiría
aunque estuviera abierta: es `existente`.

**V2 · Dos contratos con cadena viva de 2026 y las dos consultas del contrato (T15).** Ayuda para elegirlos (si tarda o
corta, se eligen a mano, p. ej. los de M44 en `progress/explore_F-016.md`):

```powershell
Q "SELECT TOP 10 d.ctride, MAX(c.fec) AS ultima, COUNT(*) AS n FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND c.emp = ? AND c.fec >= ? AND d.docoritip = ? AND d.docoriide > ? GROUP BY d.ctride ORDER BY MAX(c.fec) DESC" @(14, 1, 20260601, 1, 0)
$ctride = <ctride elegido>
$sw = [Diagnostics.Stopwatch]::StartNew(); $ps = Puntas $ctride; "puntas en $($sw.Elapsed.TotalSeconds) s"
$ps | ForEach-Object { "$($_[1]) fec $($_[2]) totbas $($_[3]) anterior $($_[4]) cadena $($_[5])" }
$p = $ps[0]   # la punta (si hay varias, la que elegiria la persona)
$sw.Restart(); $ls = LineasDe $p[0]; "lineas en $($sw.Elapsed.TotalSeconds) s: $($ls.Count)"
$ls | ForEach-Object { "$($_[0]) pos $($_[1]) linoriide $($_[2]) partida $($_[4]) pre $($_[8]) can $($_[9]) canoriori $($_[10])" }
```

Se mira: ninguna lectura truncada; cada punta sin sucesora; para la punta, `importe_cadena` = Σ round(`canoriori`·`pre`,
2) de sus líneas y, si es encadenada, ≈ `importe_cadena` de su anterior + `totbas` (M44). Tiempos (M44: ~4 s).

**V3 · La hoja de la punta da `existente`** (R5):

```powershell
$sw.Restart(); $r = Llamar "sigrid/proforma" (HojaDe $ctride $p "PRF-prueba-F016-punta"); "en $($sw.Elapsed.TotalSeconds) s"
$r.estado; $r.cod; $r.cadena; $r.avisos | Select-Object codigo, mensaje
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("PRF-prueba-F016-punta")
```

Se mira: `existente` sobre `$p[1]`, `cadena` nula, `count` 0.

**V4 · La del mes siguiente, encadenada a la punta** (R6-R13, R19):

```powershell
$s = Siguiente $ctride $p "PRF-prueba-F016-sig"
$sw.Restart(); $r = Llamar "sigrid/proforma" $s; "en $($sw.Elapsed.TotalSeconds) s"
$r.estado; $r.cadena; $r.totales; $r.filas.dca | Select-Object docoritip, docoriide, totbas
$r.avisos | Select-Object codigo, mensaje; Lineas $r
$r.filas.dcapro | Select-Object pos, refent, linoriide, can, tot, canorilin, canoriori, canoriant, imporiori, imporiant | Format-Table
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("PRF-prueba-F016-sig")
```

Se mira: `previsto`; `docoritip` 1 y `docoriide` = `$p[0]`; `cadena.anterior.cod` = `$p[1]`,
`importe_anterior_cadena` = `$p[5]` (±0,01), `importe_origen_cadena` ≈ `$p[5]` + `importe_mes`, `n_arrastradas` = nº de
líneas de la punta − 2; las dos continuadas con `canorilin` = su `linea_anterior` y `canoriori` = el de la punta + 1;
las arrastradas detrás, `can` y `tot` 0, `canorilin` = su `ide` y su `canoriori`; `canoriant`/`imporiant` 0;
`totales` del MES; `count` 0. Si la punta es del mes en curso, aviso `otra_del_mes` (es la punta: sigue).

**V4b · El aviso de R10**: la misma, con la primera línea como nueva.

```powershell
$s.lineas[0].Remove("linea_anterior"); $r = Llamar "sigrid/proforma" $s
$r.estado; $r.lineas[0].avisos | Select-Object codigo, lineas_anterior; $r.cadena.n_arrastradas
```

Se mira: `previsto`, aviso `linea_nueva_ya_en_la_anterior` con el `ide` de la línea de la punta; una arrastrada más.

**V5 · Sin `modo`, igual que F-007** (R1):

```powershell
$m = HojaDe $ctride $p "PRF-prueba-F016-mes"; $m.Remove("modo"); $m.Remove("proforma_anterior"); $m.Remove("primera_de_cadena")
$r = Llamar "sigrid/proforma" $m; $r.estado; $r.cod; $r.PSObject.Properties.Name -contains "cadena"; $r.avisos | Select-Object codigo
```

Se mira: `existente` sobre `$p[1]`, **sin** clave `cadena` (`False`) y, en `avisos`, `contrato_a_origen`. Además, como
red, V2 de F-007 tal cual sobre la 0719: los mismos resultados que en su `progress/verificacion_F-007.md`.

**V6 · Los errores de la cadena** (R6, R7, R9). Con una punta encadenada (`$p[4]` > 0):

```powershell
$e = Siguiente $ctride $p "PRF-prueba-F016-err"; $e.proforma_anterior = CodDe $p[4]; Llamar "sigrid/proforma" $e
$e.proforma_anterior = "NOEXISTE/00000"; Llamar "sigrid/proforma" $e
$e.proforma_anterior = $p[1]; $e.lineas[0].linea_anterior = 1; Llamar "sigrid/proforma" $e
```

Se mira: 400 `anterior_con_sucesora` con el `cod` de `$p[1]` en el mensaje; 400 `anterior_no_valida`; 400
`lineas_no_validas` con `linea_anterior_no_valida` en la línea 0. V2-V6 se repiten con el segundo contrato.

## G · Grabaciones (T18; el humano, con autorización expresa para CADA `commit:true`)

En la obra de pruebas 0404, sobre el contrato de los `ctrpro` 258782 y 258783 (los de la grabación de F-007 T22; otros
si el humano lo prefiere). Una **primera de cadena** con las dos líneas y otra **encadenada** que continúa solo la
258782 (la 258783 se arrastra). Mes pasado (fecha = su último día), con `otra_del_mes` para que ninguna proforma
real de ese mes la convierta en `existente`.

**Regla de parada en G1-G3.** Ante **cualquier** resultado distinto del que dice «Se mira» (un código, un estado, una
lectura o un 500 inesperados), se cierran **en el acto las dos llaves** (`SIGRID_PROFORMA_WRITE_ENABLED` y
`SIGRID_PROFORMA_ORIGEN_ENABLED`), **se para** y se avisa al humano. No se sigue con el resto de pasos:

```powershell
'[{"name":"SIGRID_PROFORMA_ORIGEN_ENABLED","value":"false","slotSetting":false},{"name":"SIGRID_PROFORMA_WRITE_ENABLED","value":"false","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline "$env:TEMP\f016_cerrar.json"
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$env:TEMP\f016_cerrar.json"
```

Antes, las lecturas de partida:

```powershell
$ctrG = (Fila "SELECT docide FROM dbo.ctrpro WHERE ide = ?" @(258782))[0]; $cG = Ctr $ctrG
$preG = @{}; foreach ($i in 258782, 258783) { $preG[$i] = (Fila "SELECT pre FROM dbo.ctrpro WHERE ide = ?" @($i))[0] }
$perG = [int](Get-Date).AddMonths(-1).ToString("yyyyMM")
function CuerpoG($ref, $lineas) {
  $mes = [decimal]0; foreach ($l in $lineas) { $mes += [math]::Round([decimal]$l.cantidad * [decimal]$l.precio, 2, [MidpointRounding]::AwayFromZero) }
  @{ database = "ruesma"; usu = "prueba"; referencia_externa = $ref; cod_obra = $cG[1]; cod_contrato = $cG[0]; periodo = $perG
     importe_mes = [double]$mes; otra_del_mes = $true; modo = "origen"; commit = $false; lineas = $lineas } }
$g1c = CuerpoG "PRF-prueba-F016-1" @(
  @{ referencia_linea = "1"; ctrpro_ide = 258782; cantidad = 1; precio = $preG[258782]; descripcion = "Prueba F-016 1" },
  @{ referencia_linea = "2"; ctrpro_ide = 258783; cantidad = 1; precio = $preG[258783]; descripcion = "Prueba F-016 2" })
$g1c.primera_de_cadena = $true
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE ide IN (?, ?)" @(258782, 258783)
$r = Llamar "sigrid/proforma" $g1c; $r.estado; $r.cadena; $r.filas.dca | Select-Object docoritip, docoriide
```

Se sigue solo con `previsto` y `docoriide` 0. **G1 · La llave de origen se mira después** (R4): se abre solo la de F-007
y el `commit` a origen debe dar 400 `escritura_proformas_origen_deshabilitada` sin escribir:

```powershell
'[{"name":"SIGRID_PROFORMA_WRITE_ENABLED","value":"true","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline "$env:TEMP\f016_abrir1.json"
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$env:TEMP\f016_abrir1.json"
$g1c.commit = $true; Llamar "sigrid/proforma" $g1c; Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("PRF-prueba-F016-1")
```

**G2 · La primera.** Se abre la de origen, se graba y se repite:

```powershell
'[{"name":"SIGRID_PROFORMA_ORIGEN_ENABLED","value":"true","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline "$env:TEMP\f016_abrir2.json"
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$env:TEMP\f016_abrir2.json"
$g1 = Llamar "sigrid/proforma" $g1c; $g1.estado; $g1.con_ide; $g1.cod; $g1.cadena
Q "SELECT c.cod, c.fec, d.cla, d.ctride, d.docoritip, d.docoriide, d.entref, d.totbas FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.ide = ?" @($g1.con_ide)
Q "SELECT ide, pos, linoriide, can, tot, canorilin, canoriori, canoriant, imporiori, imporiant FROM dbo.dcapro WHERE docide = ? ORDER BY pos" @($g1.con_ide)
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE ide IN (?, ?)" @(258782, 258783)
$h1 = Llamar "sigrid/proforma" $g1c; $h1.estado; $h1.con_ide; $h1.cadena
```

Se mira: `creado`, `PROF26/…`, `docoritip` 1, `docoriide` 0, `canoriori` = `can` (1) y `canorilin` 0 en las dos,
`canser` +1 en cada `ctrpro`; la repetición, `idempotente`, el mismo `con_ide` y `cadena` nula.

**G3 · La encadenada** (continúa la línea de la 258782; arrastra la de la 258783):

```powershell
$l1 = (Leer "SELECT ide FROM dbo.dcapro WHERE docide = ? AND linoriide = ?" @($g1.con_ide, 258782)).rows[0][0]
$g2c = CuerpoG "PRF-prueba-F016-2" @(@{ referencia_linea = "1"; ctrpro_ide = 258782; linea_anterior = $l1; cantidad = 2; precio = $preG[258782]; descripcion = "Prueba F-016 1" })
$g2c.proforma_anterior = $g1.cod
$p2 = Llamar "sigrid/proforma" $g2c; $p2.estado; $p2.cadena; Lineas $p2
$g2c.commit = $true; $g2 = Llamar "sigrid/proforma" $g2c; $g2.estado; $g2.con_ide; $g2.cod
Q "SELECT c.cod, d.docoritip, d.docoriide, d.totbas FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.ide = ?" @($g2.con_ide)
Q "SELECT ide, pos, linoriide, can, tot, canorilin, canoriori, canoriant, imporiori, imporiant FROM dbo.dcapro WHERE docide = ? ORDER BY pos" @($g2.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.ctrprodes WHERE docdeside = ? AND docdestip = ?" @($g2.con_ide, 14)
Q "SELECT COUNT(*) AS n FROM dbo.mov WHERE docide = ? AND doctip = ?" @($g2.con_ide, 14)
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE ide IN (?, ?)" @(258782, 258783)
$h2 = Llamar "sigrid/proforma" $g2c; $h2.estado; $h2.con_ide
'[{"name":"SIGRID_PROFORMA_ORIGEN_ENABLED","value":"false","slotSetting":false},{"name":"SIGRID_PROFORMA_WRITE_ENABLED","value":"false","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline "$env:TEMP\f016_cerrar.json"
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$env:TEMP\f016_cerrar.json"
```

Se mira: previa `previsto` con `n_arrastradas` 1; `creado`; `docoriide` = `$g1.con_ide`; la continuada con `can` 2,
`canorilin` = `$l1` y `canoriori` 3; la arrastrada (258783) detrás con `can` y `tot` 0, `canorilin` = su `ide` en la
primera y `canoriori` 1; **una** `ctrprodes` (solo la continuada) y los `mov` solo de ella; `canser` de la 258782 +2 y
de la 258783 sin cambio; repetición `idempotente`; las dos llaves, cerradas al final.

**V9 en la UI** (Administración): ficha de las dos, impresión con las unidades ORIGEN/ANTERIOR, que el paso a factura
ofrece solo las líneas con cantidad (sin grabar la factura) y la anulación. **Se anulan desde la UI en orden inverso**
(primero la encadenada, después la primera; nunca `DELETE`) y se comprueba en lectura:

```powershell
Q "SELECT COUNT(*) AS n FROM dbo.con WHERE ide IN (?, ?)" @($g1.con_ide, $g2.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey IN (?, ?)" @("PRF-prueba-F016-1", "PRF-prueba-F016-2")
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE ide IN (?, ?)" @(258782, 258783)
```

Se mira: 0, 0 y `canser` como en la lectura de partida.
