<!-- specs/F-015-albaran-plantilla-y-retencion/verificacion_manual.md -->
# F-015 · Verificación manual (R29, R30; T19-T21)

Anexo de design §Verificación manual, aparte por el tope de tamaño de design.

**Cuándo y quién.** Todo después de avisar a albaranes y de desplegar F-015 (lo lanza el humano). Las lecturas y los
dry-runs (V0-V4) los lanza el **líder**, con autorización del humano para esa sesión; la grabación (V5) y la limpieza
(V6) las lanza el **humano**, con autorización expresa para cada escritura. Todo desde PowerShell 5.1, contra la API
desplegada; nada por SQL directo. La clave no se escribe en ningún fichero: se lee con `az` en la propia consola.

**V0 · Setup** (el de `azure-apps/sigrid_api.md` §8) y cuatro ayudas: `Leer` hace la lectura por `sql/read`; `Q` imprime una lectura de `sql/read`; `Fila`
devuelve su primera fila (un array, por posición); `Alta` llama al endpoint y, si responde 400, imprime el cuerpo.

```powershell
$base = "https://func-sigridapi-dev-huyke.azurewebsites.net"
$code = az functionapp keys list --name func-sigridapi-dev-huyke --resource-group rg-sigrid-dev-data-api --query "functionKeys.default" -o tsv
$headers = @{ "x-functions-key" = $code }
function Leer($sql, $p = @()) {
  $b = @{ database = "ruesma"; sql = $sql; parameters = $p; max_rows = 200 } | ConvertTo-Json -Depth 5
  Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) }
function Q($sql, $p = @()) { Leer $sql $p | ConvertTo-Json -Depth 8 }
function Fila($sql, $p = @()) { (Leer $sql $p).rows[0] }
function Alta($cuerpo) {
  $b = $cuerpo | ConvertTo-Json -Depth 6
  try { Invoke-RestMethod -Uri "$base/api/sigrid/albaran" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) }
  catch { $_.ErrorDetails.Message } }
```

**Lo que se mira en toda previa** (`$r` es la respuesta): `$r.estado` = `previsto`; nada escrito,
`Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @($r.referencia_externa)` da 0; y en `$r.filas.dca` la
facturación, las fechas previstas y la divisa a 0 (`idefac`, `fecfac`, `horfac`, `antestfac`, `fecent`, `feclim`,
`cocide`, `totbasdiv`, `totivadiv`, `totdocdiv`, `totdiv`, `totpagdiv`), `dtumID` vacío y `tipgar` −1:

```powershell
$r.filas.dca | Select-Object idefac, fecfac, horfac, antestfac, fecent, feclim, cocide, totbasdiv, totivadiv, totdocdiv, totdiv, totpagdiv, dtumID, tipgar
```

**V1 · Contrato con `RET5`** (T19). Un contrato de compra de una obra de la empresa 1 con un único `ctrrec`, `RET5`
(clase 5, sin `valfij` ni `ivaide`, con `valpor`), y una línea con cantidad pendiente:

```powershell
$A = Fila "SELECT TOP 1 c.ide, c.cod, o.cod, t.entcif FROM dbo.con c JOIN dbo.ctr t ON t.ide = c.ide JOIN dbo.con o ON o.ide = t.obride JOIN dbo.ctrrec r ON r.docide = t.ide JOIN dbo.con x ON x.ide = r.recide JOIN dbo.rec e ON e.ide = r.recide WHERE c.tip = ? AND o.tip = ? AND o.emp = ? AND x.cod = ? AND e.cla = ? AND r.valfij = ? AND r.ivaide = ? AND r.valpor IS NOT NULL AND NOT EXISTS (SELECT 1 FROM dbo.ctrrec r2 WHERE r2.docide = t.ide AND r2.ide <> r.ide) AND EXISTS (SELECT 1 FROM dbo.ctrpro p WHERE p.docide = t.ide AND p.can > p.canser) ORDER BY c.ide DESC" @(44, 42, 1, "RET5", 5, 0, 0)
$lineaA = Fila "SELECT TOP 1 p.ide, p.pre FROM dbo.ctrpro p WHERE p.docide = ? AND p.can > p.canser ORDER BY p.ide" @($A[0])
$cuerpoA = @{ database = "ruesma"; cod_obra = $A[2]; cod_contrato = $A[1]; cif_proveedor = $A[3]; usu = "prueba"
  referencia_externa = "ALB-prueba-F015-1"; su_referencia = "prueba-F015-1"; commit = $false
  lineas = @(@{ referencia_linea = "1"; ctrpro_ide = $lineaA[0]; cantidad = 1; precio = $lineaA[1] }) }
$r = Alta $cuerpoA
$r.filas.dcarec; $r.totales | Select-Object totbas, totdoc, tot, retenciones, n_retenciones; $r.avisos
Q "SELECT entide, entcif, entres, pagide, pagtex, pagfor, efeide, banban, ban, cueide, eioide, dirdir1, dircon1, ivadif FROM dbo.ctr WHERE ide = ?" @($A[0])
```

Se mira: una `dcarec` con el `recide` de `RET5`, `valpor` 0.05, `bas` = `totales.totbas` y `cuo` = `bas` · 0,05 a
céntimos; `totales.tot` = `totdoc` − `cuo` = `filas.dca.tot` = `filas.dca.totpag`; `retenciones` = `cuo`,
`n_retenciones` 1; aviso `retencion_del_contrato` con `RET5`, el 5 %, `bas` y `cuo`; en `filas.dca` la identidad
(`ent*`), el pago y el banco **del contrato** (los de la última lectura), y `ivadif` el del contrato aunque sea 0.

**V2 · Contrato sin `ctrrec`** (T19). Como V1, con un contrato sin recargos:

```powershell
$B = Fila "SELECT TOP 1 c.ide, c.cod, o.cod, t.entcif FROM dbo.con c JOIN dbo.ctr t ON t.ide = c.ide JOIN dbo.con o ON o.ide = t.obride WHERE c.tip = ? AND o.tip = ? AND o.emp = ? AND NOT EXISTS (SELECT 1 FROM dbo.ctrrec r WHERE r.docide = t.ide) AND EXISTS (SELECT 1 FROM dbo.ctrpro p WHERE p.docide = t.ide AND p.can > p.canser) ORDER BY c.ide DESC" @(44, 42, 1)
$lineaB = Fila "SELECT TOP 1 p.ide, p.pre FROM dbo.ctrpro p WHERE p.docide = ? AND p.can > p.canser ORDER BY p.ide" @($B[0])
$r = Alta @{ database = "ruesma"; cod_obra = $B[2]; cod_contrato = $B[1]; cif_proveedor = $B[3]; usu = "prueba"
  referencia_externa = "ALB-prueba-F015-2"; su_referencia = "prueba-F015-2"; commit = $false
  lineas = @(@{ referencia_linea = "1"; ctrpro_ide = $lineaB[0]; cantidad = 1; precio = $lineaB[1] }) }
$r.filas.dcarec; $r.totales | Select-Object totdoc, tot, retenciones, n_retenciones; $r.avisos
```

Se mira: `filas.dcarec` vacía; `tot` = `totdoc`; `retenciones` 0 y `n_retenciones` 0; sin `retencion_del_contrato`.

**V3 · Sin contrato, con albarán anterior** (T19). Obra 0404 (la de F-009) y una línea `QA9999` sin partida (va al
almacén de la obra, como en F-009 T21); el CIF, el de un proveedor con albarán anterior en la empresa 1:

```powershell
$C = Fila "SELECT TOP 1 d.entcif, c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = ? AND c.emp = ? AND c.cod LIKE ? AND d.cla = ? AND ISNULL(d.entref, '') NOT LIKE ? AND ISNULL(d.entcif, '') <> ? ORDER BY c.ide DESC" @(14, 1, "AC__/%", 0, "PROF%", "")
$r = Alta @{ database = "ruesma"; cod_obra = "0404"; cod_contrato = $null; cif_proveedor = $C[0]; usu = "prueba"
  referencia_externa = "ALB-prueba-F015-3"; su_referencia = "prueba-F015-3"; commit = $false
  lineas = @(@{ referencia_linea = "1"; producto = "QA9999"; descripcion = "Prueba F-015"; unidad = "H"; cantidad = 1; precio = 1.0 }) }
$r.contrato.template_ide; $r.filas.dcarec; $r.avisos
Q "SELECT entide, entcif, entres, pagide, pagtex, pagfor, efeide, banban, ban, cueide, eioide, dirdir1, dircon1, ivadif FROM dbo.dca WHERE ide = ?" @($r.contrato.template_ide)
```

Se mira: `contrato.template_ide` = `$C[1]` (el último `AC__/` de clase 0 de ese CIF que no es proforma); la identidad,
el pago, el banco, `dircon1` e `ivadif` de `filas.dca`, los de ese albarán anterior (la última lectura); sin `dcarec`.

**V4 · Proveedor sin albarán anterior** (T19, R7). Obra 0404, sin contrato; el CIF, el de un proveedor vivo y
**único** con ese CIF en la empresa 1 y sin ningún albarán anterior:

```powershell
$D = Fila "SELECT TOP 1 v.cif, v.ide, c.cod FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ? AND ISNULL(v.cif, '') <> ? AND NOT EXISTS (SELECT 1 FROM dbo.con a JOIN dbo.dca d ON d.ide = a.ide WHERE a.tip = ? AND a.emp = ? AND d.entcif = v.cif AND a.cod LIKE ? AND d.cla = ? AND ISNULL(d.entref, '') NOT LIKE ?) AND (SELECT COUNT(*) FROM dbo.prv w JOIN dbo.con k ON k.ide = w.ide WHERE k.tip = ? AND k.emp = ? AND k.fecbaj = ? AND w.cif = v.cif) = ? ORDER BY c.ide DESC" @(5, 1, 0, "", 14, 1, "AC__/%", 0, "PROF%", 5, 1, 0, 1)
$r = Alta @{ database = "ruesma"; cod_obra = "0404"; cod_contrato = $null; cif_proveedor = $D[0]; usu = "prueba"
  referencia_externa = "ALB-prueba-F015-4"; su_referencia = "prueba-F015-4"; commit = $false
  lineas = @(@{ referencia_linea = "1"; producto = "QA9999"; descripcion = "Prueba F-015"; unidad = "H"; cantidad = 1; precio = 1.0 }) }
$r.contrato.template_ide; $r.filas.dca | Select-Object entide, entcod, entcif, pagide, pagtex, pagfor, efeide, dirdir1, dircon1, ivadif; $r.avisos
Q "SELECT v.pagide, v.efeide, v.dir, a.res, a.formul FROM dbo.prv v LEFT JOIN dbo.auxpag a ON a.ide = v.pagide WHERE v.ide = ?" @($D[1])
```

Se mira: `template_ide` 0; `entide` = `$D[1]` y `entcod` = `$D[2]`; `pagide`/`efeide` y `dirdir1` los del `prv`,
`pagtex`/`pagfor` el `res`/`formul` de su `auxpag`; `dircon1` vacío e `ivadif` 0; `cabecera_sin_dato` solo si el
`prv` no trae pago, o no trae banco con un efecto CC, CT o TR.

**V5 · Grabación con retención** (T20; el humano, con autorización expresa para esta escritura). El cuerpo de V1 con
otra referencia y `commit:true`; antes, la medición de la línea:

```powershell
Q "SELECT can, canser FROM dbo.ctrpro WHERE ide = ?" @($lineaA[0])
$cuerpoG = $cuerpoA.Clone(); $cuerpoG.referencia_externa = "ALB-prueba-F015-5"; $cuerpoG.su_referencia = "prueba-F015-5"; $cuerpoG.commit = $true
$g = Alta $cuerpoG
$g.estado; $g.con_ide; $g.cod; $g.filas.dcarec; $g.totales | Select-Object totdoc, tot, retenciones, n_retenciones
Q "SELECT ide, docide, recide, bas, valpor, cuo FROM dbo.dcarec WHERE docide = ?" @($g.con_ide)
Q "SELECT totdoc, tot, totpag, synckey FROM dbo.dca WHERE ide = ?" @($g.con_ide)
```

Se mira: `estado` `creado`; una `dcarec` con `docide` = `con_ide`, igual a la de la respuesta; `dca.tot` = `totpag` =
`totdoc` − `cuo`. Revisión en la UI de Sigrid (V1 de la spec): la retención y el neto como en un albarán del
escritorio del mismo contrato. Repetición, el mismo cuerpo:

```powershell
$h = Alta $cuerpoG
$h.estado; $h.con_ide; $h.totales | Select-Object tot, retenciones
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("ALB-prueba-F015-5")
```

Se mira: `idempotente`, el mismo `con_ide`, `retenciones` = el `cuo` de antes y una sola fila. Después, **anularlo
desde la UI de Sigrid** (nunca `DELETE`) y comprobar en lectura que no queda nada (0, 0 y 0) y que `canser` vuelve al
valor leído antes de grabar:

```powershell
Q "SELECT COUNT(*) AS n FROM dbo.con WHERE ide = ?" @($g.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.dcarec WHERE docide = ?" @($g.con_ide)
Q "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey = ?" @("ALB-prueba-F015-5")
Q "SELECT can, canser FROM dbo.ctrpro WHERE ide = ?" @($lineaA[0])
```

**V6 · Limpieza** (T21; el humano, con autorización expresa para esa escritura): la de §Limpieza, tal cual (previa
por `sql/read`, lista en `progress/limpieza_F-015.md` sin nombres, `UPDATE` por `sql/write` con `max_affected_rows`
= N y relectura a 0). Requiere `UPDATE` en `ALLOWED_WRITE_PREFIXES`.
