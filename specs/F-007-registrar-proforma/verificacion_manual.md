<!-- specs/F-007-registrar-proforma/verificacion_manual.md -->
# F-007 · Verificación manual (R35; T20-T22)

Anexo de tasks (T37, pasada 1 de revisión): los comandos exactos de T21 y T22, como el de F-015. T20 (V8 con
Administración y respuesta de `proformas`) no lleva comandos: se anota en `progress/verificacion_F-007.md`, igual que
el resultado de cada paso de este fichero.

**Cuándo y quién.** Todo después de T20 y de la revisión aprobada. El despliegue (D1-D3) y la grabación (V5) los lanza
el **humano**: `func publish` con el prefijo `!` y cada escritura con autorización expresa para esa llamada. Las
lecturas y los dry-runs (V1-V4) los lanza el líder con autorización del humano para esa sesión. Todo desde PowerShell
5.1, contra la API desplegada; nada por SQL directo. **Nunca `DELETE`**: lo grabado se anula desde la UI de Sigrid.

**Sin secretos.** Ni la URL ni la clave ni los nombres de los recursos se escriben en ningún fichero: van en variables
de entorno de la propia consola. Los ficheros JSON de App Settings se dejan en `$env:TEMP`, fuera del repositorio.

```powershell
$env:SIGRID_API_APP = "<nombre de la Function App>"; $env:SIGRID_API_RG = "<su grupo de recursos>"
$env:SIGRID_API_BASE_URL = "https://$env:SIGRID_API_APP.azurewebsites.net"
$env:SIGRID_API_FUNCTION_KEY = az functionapp keys list --name $env:SIGRID_API_APP --resource-group $env:SIGRID_API_RG --query "functionKeys.default" -o tsv
```

## D · Despliegue (T21; el humano)

**D1 · Las cinco App Settings, en JSON y cerradas.** Riesgo O3: las listas y el objeto solo admiten JSON válido; una
mal formada impide arrancar la Function y tumba **todas** las rutas, también `sigrid/albaran`. Fichero ASCII sin BOM,
validado con `Settings` antes de subirlo (la lista de productos está pendiente de V8):

```powershell
$f = "$env:TEMP\f007_appsettings.json"
@'
[{"name":"SIGRID_PROFORMA_WRITE_ENABLED","value":"false","slotSetting":false},
 {"name":"SIGRID_PROFORMA_PREFIJOS_REFERENCIA","value":"[\"PRF-\"]","slotSetting":false},
 {"name":"SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO","value":"[\"SM9999\",\"SB9999\",\"SM370001\"]","slotSetting":false},
 {"name":"SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO","value":"{\"SM9999\":\"SM99\",\"SB9999\":\"SB99\",\"SM370001\":\"SM37\"}","slotSetting":false},
 {"name":"SIGRID_PROFORMA_MAX_LINEAS","value":"500","slotSetting":false}]
'@ | Set-Content -Encoding ascii -NoNewline $f
$env:F007_JSON = $f
@'
import json, os
for s in json.load(open(os.environ["F007_JSON"], encoding="ascii")):
    os.environ[s["name"]] = s["value"]
for k, v in {"SQL_DRIVER": "x", "SQL_SERVER_HOST": "x", "SQL_SERVER_PORT": "1",
             "SQL_SERVER_USERNAME": "x", "SQL_SERVER_PASSWORD": "x"}.items():
    os.environ[k] = v
from config.settings import Settings
s = Settings()
print(s.sigrid_proforma_write_enabled, s.sigrid_proforma_prefijos_referencia,
      s.sigrid_proforma_productos_sin_contrato, s.sigrid_proforma_naturaleza_por_producto,
      s.sigrid_proforma_max_lineas)
'@ | .venv\Scripts\python -
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$f"
az functionapp config appsettings list -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --query "[?starts_with(name, 'SIGRID_PROFORMA_') || name == 'SIGRID_DOMAIN_WRITE_ENABLED'].{n:name, v:value}" -o table
```

Se mira: el `python` imprime `False ['PRF-'] ['SM9999', 'SB9999', 'SM370001'] {...} 500` (si falla, no se sube);
el `list` enseña las cinco con esos valores (el `set` las enseña a `null`: es normal).

**D2 · Publicar** desde la rama revisada (el humano, con `!`):
`func azure functionapp publish $env:SIGRID_API_APP --python`. La primera llamada puede dar timeout por arranque en
frío: se repite.

**D3 · Lo primero, un dry-run de `sigrid/albaran`** (O3). Obra 0404, contrato `CTSU16/0206` (el de F-009), una línea
con cantidad pendiente; antes, las ayudas de V0:

```powershell
$U = Fila "SELECT t.ide, t.entcif FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride WHERE c.tip = ? AND c.cod = ? AND o.tip = ? AND o.emp = ? AND o.cod = ?" @(44, "CTSU16/0206", 42, 1, "0404")
$lineaU = Fila "SELECT TOP 1 p.ide, p.pre FROM dbo.ctrpro p WHERE p.docide = ? AND p.can > p.canser ORDER BY p.ide" @($U[0])
$a = Llamar "sigrid/albaran" @{ database = "ruesma"; cod_obra = "0404"; cod_contrato = "CTSU16/0206"; cif_proveedor = $U[1]; usu = "prueba"
  referencia_externa = "ALB-prueba-F007-1"; su_referencia = "prueba-F007-1"; commit = $false
  lineas = @(@{ referencia_linea = "1"; ctrpro_ide = $lineaU[0]; cantidad = 1; precio = $lineaU[1] }) }
$a.estado; $a.cod
```

Se mira: `previsto`. Un 500/503 o un arranque fallido es O3: se quitan las cinco (`az functionapp config appsettings
delete -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --setting-names SIGRID_PROFORMA_WRITE_ENABLED
SIGRID_PROFORMA_PREFIJOS_REFERENCIA SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO
SIGRID_PROFORMA_MAX_LINEAS`), se repite D3 y se para.

## V · Verificación (T21-T22)

**V0 · Setup.** `Leer` hace la lectura por `sql/read`; `Q` la imprime; `Fila` devuelve su primera fila; `Llamar`
llama a una ruta y, si responde 400, devuelve el cuerpo; `Vinc` es el `ctrpro_ide` que `proformas` mandaría: la
**única** línea del contrato con esa partida y ese precio (±0,0001; si no hay una, para). Las hojas son las de agosto
de 2026 de `docs/referencia/proforma_ejemplo_*.md` (partida, MES, precio unitario; solo las de MES ≠ 0):

```powershell
$base = $env:SIGRID_API_BASE_URL; $headers = @{ "x-functions-key" = $env:SIGRID_API_FUNCTION_KEY }
function Leer($sql, $p = @()) {
  $b = @{ database = "ruesma"; sql = $sql; parameters = $p; max_rows = 200 } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) }
function Q($sql, $p = @()) { Leer $sql $p | ConvertTo-Json -Depth 8 }
function Fila($sql, $p = @()) { (Leer $sql $p).rows[0] }
function Llamar($ruta, $cuerpo) {
  $b = $cuerpo | ConvertTo-Json -Depth 6
  try { Invoke-RestMethod -Uri "$base/api/$ruta" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) }
  catch { $_.ErrorDetails.Message } }
function Ctr($cod) { (Fila "SELECT t.ide FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride WHERE c.tip = ? AND c.cod = ? AND o.tip = ? AND o.emp = ? AND o.cod = ?" @(44, $cod, 42, 1, "0719"))[0] }
function Vinc($ctride, $partida, $precio) {
  $r = Leer "SELECT p.ide FROM dbo.ctrpro p JOIN dbo.obrparpar pp ON pp.ide = p.paride WHERE p.docide = ? AND pp.cod = ? AND ABS(p.pre - ?) <= ?" @($ctride, $partida, $precio, 0.0001)
  if ($r.rows.Count -ne 1) { throw "$partida a $precio casa con $($r.rows.Count) lineas" }; $r.rows[0][0] }
$hojas = @{
  "CTSB26/0472" = @{ mes = 17024.28; anterior = 2651.0; origen = 19675.28; existente = "AC26/25548"; contrato = @(
      @("F09", "02.03.02.01", 620, 11, "VERTIDO HORMIGON CIMENTACION LIMPIEZA"),
      @("F11", "02.03.02.04", 117.5, 26, "ENCOFRADO CIMENTACION"),
      @("F15", "02.03.03.06", 38.57, 10, "VERTIDO HORMIGON MUROS"),
      @("F16", "02.03.03.08", 261.4335, 21, "ENCOFRADO MURO 2 CARA . MUROS DE CONTENCION"),
      @("F21", "02.20.02.02.11", 48, 21, "ENCOFRADO MURO 2 CARA (MED X2)"))
    nuevas = @(@{ referencia_linea = "F23"; producto = "SM1004"; partida = "02.20.02.02.11"; unidad = "M2"; cantidad = 75.85; precio = 3.5; descripcion = "BERENJENO" }) }
  "CTSB26/0417" = @{ mes = 31291.05; anterior = 36249.31; origen = 67540.36; existente = "AC26/25552"; contrato = @(
      @("M09", "02.03.02.03", 18492.48, 1, "SUMINISTRO FERRALLA 02.03.02.03"),
      @("M10", "02.03.02.03", 18492.48, 0.2, "ELABORACION DE FERRALLA 02.03.02.03"),
      @("M11", "02.03.02.03", 18492.48, 0.27, "COLOCACION DE FERRALLA 02.03.02.03"),
      @("M12", "02.03.03.04", 871.21, 1, "SUMINISTRO FERRALLA 02.03.03.04"),
      @("M13", "02.03.03.04", 871.21, 0.2, "ELABORACION DE FERRALLA 02.03.03.04"),
      @("M14", "02.03.03.04", 871.21, 0.27, "COLOCACION DE FERRALLA 02.03.03.04"),
      @("M15", "02.03.04.02", 871.51, 1, "SUMINISTRO FERRALLA 02.03.04.02"),
      @("M16", "02.03.04.02", 871.51, 0.2, "ELABORACION DE FERRALLA 02.03.04.02"),
      @("M17", "02.03.04.02", 871.51, 0.27, "COLOCACION DE FERRALLA 02.03.04.02"))
    nuevas = @(
      @{ referencia_linea = "M31"; producto = "SM1026"; partida = "02.03.02.03"; cantidad = 20235.2; precio = 0.036; descripcion = "Regularizacion precio acero agosto" },
      @{ referencia_linea = "M33"; producto = "SM1026"; partida = "9.01"; cantidad = 816.84; precio = 1; descripcion = "Seguridad y replanteo. Agosto" }) }
  "CTSB26/0369" = @{ mes = 7991.0; anterior = 6056.0; origen = 14047.0; existente = "AC26/25551"; contrato = @(
      @("N10", "02.02.02", 1250.467, 2.8, "EXCAVACION DESBROCE A BORDE DE EXCAVACION"),
      @("N11", "02.02.03", 1603.46, 2.8, "EXCAVACION GENERAL A BORDE DE EXCAVACION"))
    nuevas = @() } }
function Cuerpo($cod, $ref, $otra = $false, $conIde = $true) {
  $h = $hojas[$cod]; $ctride = Ctr $cod; $lineas = @()
  foreach ($l in $h.contrato) {
    $x = @{ referencia_linea = $l[0]; cantidad = $l[2]; precio = $l[3]; descripcion = $l[4] }
    if ($conIde) { $x.ctrpro_ide = Vinc $ctride $l[1] $l[3] } else { $x.partida = $l[1] }
    $lineas += $x }
  @{ database = "ruesma"; usu = "prueba"; referencia_externa = $ref; cod_obra = "0719"; periodo = 202608
     cod_contrato = $cod; importe_mes = $h.mes; importe_anterior = $h.anterior; importe_origen = $h.origen
     numero_orden = 2; otra_del_mes = $otra; commit = $false; lineas = $lineas + $h.nuevas } }
function Lineas($r) { $r.lineas | Select-Object ctrpro_ide, producto, cantidad, precio, total | Format-Table }
```

**V1 · La ruta existe y la llave está cerrada** (sin escribir aunque estuviera abierta: la hoja es `existente`):

```powershell
$c = Cuerpo "CTSB26/0472" "PRF-prueba-F007-llave"; $c.commit = $true
Llamar "sigrid/proforma" $c
```

Se mira: 400 `escritura_proformas_deshabilitada` con «Escritura de proformas desactivada: hacen falta …».

**V2 · Las tres hojas, `existente`** (T21, V7). Para cada contrato, la previa y su tiempo:

```powershell
foreach ($cod in "CTSB26/0472", "CTSB26/0417", "CTSB26/0369") {
  $ref = "PRF-prueba-F007-" + $cod.Substring(7)
  $sw = [Diagnostics.Stopwatch]::StartNew(); $r = Llamar "sigrid/proforma" (Cuerpo $cod $ref); $s = $sw.Elapsed.TotalSeconds
  "$cod -> $($r.estado) $($r.cod) (esperada $($hojas[$cod].existente)) totbas $($r.totales.totbas) en $s s"
  $r.contrato | Select-Object cod, resuelto_por; $r.origen; $r.avisos | Select-Object codigo, mensaje; Lineas $r
  Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @($ref) }
```

Se mira: `existente` sobre `AC26/25548`, `AC26/25552` y `AC26/25551` (la de la 0417 es la de agosto, `entref`
`PROF0826_0719-1`, la desviación 3 resuelta), con sus líneas (`dcapro_ide`, `ctrpro_ide` = `linoriide`, producto,
cantidad, precio, importe), `resuelto_por` `peticion` y el `count` a 0. Un `Vinc` que para es un dato que no casa:
se anota y no se sigue con esa hoja.

**V3 · Con `otra_del_mes`, la previa y las mismas líneas** (T21, V7):

```powershell
foreach ($cod in "CTSB26/0472", "CTSB26/0417", "CTSB26/0369") {
  $ref = "PRF-prueba-F007-" + $cod.Substring(7) + "-otra"
  $e = Llamar "sigrid/proforma" (Cuerpo $cod ("PRF-prueba-F007-" + $cod.Substring(7)))
  $p = Llamar "sigrid/proforma" (Cuerpo $cod $ref $true)
  "$cod -> $($p.estado) $($p.cod) totbas $($p.filas.dca.totbas) / existente $($e.totales.totbas)"
  $p.avisos | Select-Object codigo, mensaje; Lineas $e; Lineas $p
  Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @($ref) }
```

Se mira: `previsto`, `PROF26/…`, aviso `otra_del_mes` que cita la `AC`; las líneas de contrato con los mismos
`ctrpro_ide`, cantidad y precio que la `existente` y las nuevas sin vincular con su producto; `totbas` igual a ±0,01;
`count` a 0.

**V4 · El respaldo sin `ctrpro_ide`** (contrato v1.1): `Cuerpo $cod $ref $true $false` en el bucle de V3. Se mira: los
mismos `ctrpro_ide` que V3, o `linea_ambigua` con sus `candidatos` si en Sigrid hay dos líneas con la misma partida y
el mismo precio (es lo que `proformas` desempata por la descripción).

**V5 · Una grabación** (T22; el humano, con autorización expresa para **esta** llamada). Una hoja real que **no** esté
en Sigrid, elegida por el humano, con su cuerpo `$cuerpoG` montado como en `Cuerpo` (otra referencia `PRF-<id>`, su
periodo e importes). Antes, su previa y las lecturas:

```powershell
$p = Llamar "sigrid/proforma" $cuerpoG; $p.estado; $p.cod; $p.filas.dca | Select-Object cla, entref, totbas, totdoc, tot
$ctride = $p.contrato.ide
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE docide = ? ORDER BY pos" @($ctride)
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @($cuerpoG.referencia_externa)
```

Se sigue solo con `previsto` (nunca con `existente`). Se abre la llave de proformas, solo esa
(`SIGRID_DOMAIN_WRITE_ENABLED` ya está en `true` y no se toca), se graba, se repite y se cierra **después** de la
repetición (el reenvío con `commit:true` también la exige):

```powershell
'[{"name":"SIGRID_PROFORMA_WRITE_ENABLED","value":"true","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline "$env:TEMP\f007_abrir.json"
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$env:TEMP\f007_abrir.json"
$cuerpoG.commit = $true; $g = Llamar "sigrid/proforma" $cuerpoG
$g.estado; $g.con_ide; $g.cod; $g.totales | Select-Object totbas, totdoc, tot, retenciones
Q "SELECT c.cod, c.fec, d.cla, d.ctride, d.entref, d.synckey, d.totbas, d.totdoc, d.tot FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.ide = ?" @($g.con_ide)
Q "SELECT pos, refent, docoritip, linoriide, can, pre, tot FROM dbo.dcapro WHERE docide = ? ORDER BY pos" @($g.con_ide)
Q "SELECT recide, bas, valpor, cuo FROM dbo.dcarec WHERE docide = ?" @($g.con_ide)
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE docide = ? ORDER BY pos" @($ctride)
$h = Llamar "sigrid/proforma" $cuerpoG; $h.estado; $h.con_ide; $h.origen; $h.avisos
'[{"name":"SIGRID_PROFORMA_WRITE_ENABLED","value":"false","slotSetting":false}]' | Set-Content -Encoding ascii -NoNewline "$env:TEMP\f007_cerrar.json"
az functionapp config appsettings set -g $env:SIGRID_API_RG -n $env:SIGRID_API_APP --settings "@$env:TEMP\f007_cerrar.json"
```

Se mira: `creado`; `cod` `PROF26/` + 5 cifras, `cla` 141, el `ctride` del contrato, `entref` `PROF<MMAA>_<obra>`,
`synckey` la referencia; las de contrato con `docoritip` 44 y `linoriide` = su `ctrpro_ide`, las nuevas con 0; la
retención del contrato en `dcarec`; `canser` de las vinculadas sube en su cantidad. La repetición: `idempotente`, el
mismo `con_ide`, `origen` nulo y `avisos` vacío. En la UI (V6): la ficha (serie, clase, líneas vinculadas, retención,
totales, servido), la impresión y el paso a factura, como una `AC` de proforma del escritorio.

Si es de prueba, **se anula desde la UI de Sigrid** (nunca `DELETE`) y se comprueba en lectura que no queda nada y
que `canser` vuelve a lo leído antes de grabar:

```powershell
Q "SELECT COUNT(*) AS n FROM dbo.con WHERE ide = ?" @($g.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @($cuerpoG.referencia_externa)
Q "SELECT ide, can, canser FROM dbo.ctrpro WHERE docide = ? ORDER BY pos" @($ctride)
```
