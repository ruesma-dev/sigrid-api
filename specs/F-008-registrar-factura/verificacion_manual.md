<!-- specs/F-008-registrar-factura/verificacion_manual.md -->
# F-008 · Verificación manual (T22-T24 y T34)

Los pasos exactos de T22, T23, T24 y T34 (despliegue de la enmienda 1), con el modelo de
[`F-016/verificacion_manual.md`](../F-016-proforma-a-origen/verificacion_manual.md). Lo que salga de cada paso (salidas,
tiempos, lo que no cuadre) se anota en `progress/verificacion_F-008.md`. Las V1-V7 son las de `progress/explore_F-008.md`.

**Cuándo y quién.** Todo después de la revisión aprobada (T21).
- El despliegue y las grabaciones (G1, G2) los lanza el **humano**, cada escritura con autorización expresa para esa
  llamada.
- Las lecturas y las previas (P1-P7) las lanza el líder, con autorización del humano para esa sesión.
- Todo desde PowerShell 5.1 y contra la API desplegada; nada por SQL directo.
- **Nunca `DELETE`**: lo grabado se anula desde la UI de Sigrid (V4).

**Sin secretos ni datos reales en el repositorio.** La URL y la clave van en variables de entorno de la consola. Los
códigos de obra, proveedor, CIF y número de las facturas reales que se usen se anotan en `progress/verificacion_F-008.md`
**solo como `con.ide`**, nunca con nombre ni CIF.

```powershell
$env:SIGRID_API_BASE_URL = "<URL base de la Function App>"
$env:SIGRID_API_FUNCTION_KEY = "<clave de función, leída con az functionapp keys list>"
```

## S · Setup

`Leer` lee por `sql/read` y **para si viene `truncated`**; `Fila` da la primera fila; `Factura` llama a la ruta y, si
responde 400, devuelve el cuerpo con `details.codigo`.

```powershell
$base = $env:SIGRID_API_BASE_URL; $headers = @{ "x-functions-key" = $env:SIGRID_API_FUNCTION_KEY }
function Leer($sql, $p = @(), $max = 1000) {
  $b = @{ database = "ruesma"; sql = $sql; parameters = $p; max_rows = $max } | ConvertTo-Json -Depth 5
  $r = Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b))
  if ($r.truncated) { throw "Lectura truncada: no vale" }; $r }
function Fila($sql, $p = @()) { (Leer $sql $p).rows[0] }
function Factura($cuerpo) {
  $b = $cuerpo | ConvertTo-Json -Depth 8
  try { Invoke-RestMethod -Uri "$base/api/sigrid/factura" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b)) }
  catch { $_.ErrorDetails.Message | ConvertFrom-Json } }
```

## T22 · Permisos de `user_rw` (V1)

Lo comprueba con quien administra Sigrid; `sys.database_permissions` no se ve con el usuario de lectura. Hace falta:

- `INSERT` en `con`, `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `dcaprodes` y `log`;
- `UPDATE` en `con`, `dca`, `dcapro`, `ctrpro` y `ctr`.

Si falta alguno, G1 acaba en ROLLBACK con un 500 y no queda nada escrito; se anota y **no** se repite hasta corregirlo.

## D · Despliegue con la llave cerrada

1. **Cargar las seis App Settings que no son la llave** (el humano, por `@json` como en F-009), en JSON y literales.
   Sin ellas toda previa acaba en `referencia_no_permitida` (prefijos vacíos) o en `lineas_no_validas` (P3-P5, P7):
   ```text
   SIGRID_FACTURA_PREFIJOS_REFERENCIA      = ["FAC-"]
   SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN     = ["MA9999","SM9999","SB9999","QA9999","XA9999","SM370001"]
   SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO  = las entradas de esos seis productos copiadas de SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO
   SIGRID_FACTURA_IVAS                     = ["I21","I10","ISP21","i0","i4","I21NDED","I10NDED"]
   SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS   = ["6"]
   SIGRID_FACTURA_MAX_LINEAS               = sin cargar (500 por defecto)
   ```
   - `FAC-` es el prefijo de la app `facturas` y **sigue pendiente de confirmar** con ella (P15).
   - Si alguno de los seis productos no está en `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO`, se para y se pregunta al
     humano.
   - **Superado por la enmienda 1 (spec v3.2):** `SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO` deja de leerse con el código
     de la enmienda. Se cargó en D1 del 2026-11-01 (`progress/verificacion_F-008.md`); **no se vuelve a cargar**. La
     naturaleza sale de la ficha o de `SIGRID_FACTURA_NATURALEZA_FORZADA`, y su despliegue va en **§T34**.
   - `SIGRID_FACTURA_WRITE_ENABLED` **no se carga** (ausente vale `false`) o se carga `false`: la llave, cerrada.
2. **Publicar el código** (el humano, como en F-016).
3. **Leer las App Settings** (solo lectura) y confirmar que `SIGRID_FACTURA_WRITE_ENABLED` está ausente o en `false`
   y que las otras seis son las del paso 1. Si la llave saliera `true`, **no** se sigue: se avisa al humano.
   ```powershell
   az functionapp config appsettings list --name <function app> --resource-group <grupo> --query "[?starts_with(name, 'SIGRID_FACTURA_')].{n:name, v:value}" -o table
   ```
4. **Comprobar la llave (D4)** con este cuerpo **fijo**, que no podría escribir aunque la llave estuviera abierta: su
   `referencia_externa` lleva un prefijo no admitido, y `referencia_no_permitida` sale antes de cualquier lectura o
   escritura. Esperado: 400 con `details.codigo = "escritura_facturas_deshabilitada"` (llave cerrada). Si respondiera
   `referencia_no_permitida`, la llave está abierta: se para y se avisa al humano. Nunca puede salir `creado`.
   ```powershell
   $d2 = @{ database = "ruesma"; usu = "prueba"; referencia_externa = "NOADMITIDA-D2"; serie = "FR"
            cif_proveedor = "B00000000"; numero_factura = "NOADMITIDA-D2"; fecha_factura = 20261130; cod_obra = "0404"
            lineas = @(@{ descripcion = "Comprobacion de la llave"; cantidad = 1.0; precio = 1.0; iva = "I21"; producto = "MA9999" })
            vencimientos = @(@{ fecha = 20261230; importe = 1.21 }); total_base = 1.0; total_iva = 0.21; total_factura = 1.21
            commit = $true }
   Factura $d2
   ```
5. Comprobar el 400 sin eco: el cuerpo de D4 con `total_base = "20"` (y `commit = $false`) responde «Solicitud
   invalida.» y `details.validation` trae solo `loc`, `type` y `msg` (ni `input` ni `ctx`).

## T23 · Previas (sin `commit`) sobre datos reales

Cada previa debe responder `estado = "previsto"`, `committed = false` y el aviso `cod_provisional`. Tras cada una,
**C0** comprueba que no se escribió nada (mismo resultado antes y después):

```powershell
# C0: ultimo con de factura FR y FRGG y maximos de ide; deben coincidir antes y despues
Fila "SELECT (SELECT MAX(ide) FROM dbo.con), (SELECT MAX(ide) FROM dbo.dcfpro), (SELECT MAX(ide) FROM dbo.pag), (SELECT COUNT(*) FROM dbo.con WHERE tip = 15)"
```

### Elegir los datos

- **Albaranes pendientes de facturar** (para P1-P3 y P6): de compra, contabilizados (`est` CON) y sin facturar.
  ```powershell
  Leer "SELECT TOP 20 c.ide, c.cod, d.entide, d.ctride, d.docoritip FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.estfac = 0 AND NOT EXISTS (SELECT 1 FROM dbo.dcapro p WHERE p.docide = d.ide AND p.canfac <> 0) ORDER BY c.ide DESC" @(14)
  ```
  Se confirma que su `con.est` es el de CON en `conest` (`SELECT est, cod FROM dbo.conest WHERE tip = 14`).
- **Facturas ya registradas en el escritorio** (para P4, P5 y P7): una FR sin origen y una FRGG, de 2026.
  ```powershell
  Leer "SELECT TOP 10 c.ide, c.cod FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = 15 AND c.cod LIKE ? AND NOT EXISTS (SELECT 1 FROM dbo.dcfpro p WHERE p.docide = d.ide AND p.docoritip <> 0) ORDER BY c.ide DESC" @("FR26/%")
  Leer "SELECT TOP 10 c.ide, c.cod FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = 15 AND c.cod LIKE ? ORDER BY c.ide DESC" @("FRGG26/%")
  ```

El cuerpo de cada previa se arma con lo leído: `cif_proveedor` = `dcf.entcif` de la factura o el CIF del proveedor del
albarán; `numero_factura` **inventado** (`"VERIF-F008-<n>"`), para que no salte `factura_ya_registrada`;
`referencia_externa` con el formato fijo **`FAC-VERIF-F008-<previa>-<n>`** (`FAC-VERIF-F008-P1-1`, `-P1-2` si se
repite, `FAC-VERIF-F008-G1-1` en T24): lleva el prefijo admitido, pero `VERIF-F008` no lo genera la app `facturas`, así
que no pisa su idempotencia; cada una se anota junto a su `con.ide` en `progress/verificacion_F-008.md`; `usu = "prueba"`; sin orígenes, `cod_obra` (el de la obra de la factura real); `vencimientos` con la suma de `total_factura`.

| Previa | Serie y modo | Orígenes | Líneas sin origen | Qué se mira |
|---|---|---|---|---|
| P1 | FR, `mes` | 1-2 albaranes pendientes del mismo proveedor y obra | — | `lineas[].tot` = `ROUND(dcapro.can * pre, 2)`; `filas.dcaprodes` una por línea |
| P2 | FR, `origen` | una proforma de contrato contabilizada, con `a_origen` de sus líneas | — | `canoriori`/`imporiori` de la línea = los mandados; sin `a_origen` → `a_origen_incompleto` |
| P3 | FR, `mes` | 1 albarán pendiente | 1 línea MA9999 de ajuste | `lineas[]` con una `origen` y una `sin_origen`; `cueide` de la sin origen = la de F-009 |
| P4 | FR | — | las de una FR ya registrada sin origen | `filas.dcfpro[].cueide`, `caaide`, `natide`, `ivaide`, `almide` = los de su `dcfpro` real |
| P5 | FRGG | — | las de una FRGG ya registrada, con su `cuenta` y `analitica` | `cod` `FRGG26/` + 4 cifras; `cueide`/`caaide` = los de su `dcfpro` real |
| P6 | FRGG, `mes` | 1 albarán pendiente de un proveedor de gastos generales | — | se admite el origen en FRGG; marca prevista igual que en FR |
| P7 | FR | — | las de P4 con su `numero_factura` **real** | `factura_ya_registrada` con `details.cod` = el de la factura real |

Lectura de comparación de P4 y P5 (líneas reales de la factura elegida):

```powershell
Leer "SELECT pos, proide, paride, cueide, caaide, natide, ivaide, almide, cenide, can, pre, tot FROM dbo.dcfpro WHERE docide = ? ORDER BY pos" @(<con.ide de la factura>)
```

Lo que no coincida se anota línea a línea en `progress/verificacion_F-008.md`; no se corrige sin feature nueva.

## T24 · Grabaciones autorizadas (V2-V4, V6, V7)

Requisitos: T22 confirmado, D y T23 en verde. **Una autorización expresa del humano por llamada.** Antes de cada una
se repite la previa del mismo cuerpo y el humano la revisa.

1. **Abrir la llave** (el humano): App Setting `SIGRID_FACTURA_WRITE_ENABLED=true`, solo durante G1-G2.
2. **G1 · FR en la obra 0404**, con un albarán pendiente y, si lo hay, una línea sin origen (mixta: cubre V6). El mismo
   cuerpo de la previa con `commit = $true`. Esperado: `estado = "creado"`, `cod` `FR26/` definitivo.
3. **Repetir G1** con la misma `referencia_externa`: esperado `estado = "idempotente"` y el mismo `cod`; C0 no cambia.
4. **G2 · FRGG sin origen** (V7), con la cuenta y la analítica de una FRGG real del mismo proveedor.
5. **Cerrar la llave** (el humano): `SIGRID_FACTURA_WRITE_ENABLED=false`; después, la lectura de App Settings de D3
   (debe salir `false`) y, solo entonces, D4 con su cuerpo fijo `NOADMITIDA-D2`, nunca con otro.

Lecturas tras G1 y G2 (`<ide>` = `con_ide` de la respuesta):

```powershell
Fila "SELECT c.cod, c.est, d.synckey, d.totbas, d.totiva, d.totdoc, d.tot FROM dbo.con c JOIN dbo.dcf d ON d.ide = c.ide WHERE c.ide = ?" @(<ide>)
Leer "SELECT pos, docoritip, docoriide, linoriide, can, tot, cueide, caaide FROM dbo.dcfpro WHERE docide = ? ORDER BY pos" @(<ide>)
Leer "SELECT p.ide, p.cla, p.fecven, p.tot, p.remide, p.fecrea FROM dbo.pag p JOIN dbo.con c ON c.ide = p.ide WHERE p.conide = ? AND c.tip = 25" @(<ide>)
Leer "SELECT COUNT(*) FROM dbo.dcfrec WHERE docide = ?" @(<ide>)
Leer "SELECT COUNT(*) FROM dbo.consii WHERE conide = ?" @(<ide>)
Leer "SELECT COUNT(*) FROM dbo.dcaprodes WHERE docdeside = ? AND docdestip = 15" @(<ide>)
# Solo G1: las marcas del albaran de origen
Leer "SELECT ide, can, canfac FROM dbo.dcapro WHERE docide = ?" @(<ide del albaran>)
Fila "SELECT d.estfac, d.fecfac, d.horfac, d.antestfac, c.est FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE d.ide = ?" @(<ide del albaran>)
# Lista negativa (R39): la API no escribe asiento; debe salir 0 hasta «Contabilizar»
Leer "SELECT COUNT(*) FROM dbo.regiva WHERE docide = ?" @(<ide>)
```

Esperado: la factura en REC (G1) o RECGG (G2); `pag` con `remide = 0` y `fecrea = 0`; `canfac = can` en las líneas del
albarán, `estfac = 1`, `antestfac = 3` y `con.est` del albarán = FAC.

**En el escritorio**, por quien administra Sigrid y con la factura delante:

| V | Paso | Qué se anota |
|---|---|---|
| V2 | «Comprobar» y «Contabilizar» G1 | si el asiento cuadra y lleva las cuentas de `dcfpro` |
| V6 | ídem, la línea sin origen de G1 | si respeta `cueide` y `caaide` de la API |
| V7 | «Comprobar» y «Contabilizar» G2 | si la cuenta va al debe con la analítica mandada |
| V3 | cambiar `fecven` del vencimiento y guardar | si deja y si regenera los vencimientos |
| V4 | **anular** G1 y G2 | repetir las lecturas: `canfac`, `dcaprodes`, `con.est` del albarán y `pag` revertidos |

Si «Comprobar» o «Contabilizar» rechazan la factura, **no** se toca nada por la API: se anula en el escritorio, se anota
el mensaje exacto y la feature vuelve a revisión.

## T34 · Despliegue de la enmienda 1 (naturaleza de la ficha o forzada, FR con cuenta)

**Cuándo y quién.** Tras el APROBADO del reviewer (T35). Las órdenes que **escriben** en Azure (publicar,
`appsettings set` y `appsettings delete`) las lanza el **humano**, cada una con su **autorización expresa**. Las lanza
en el prompt de la sesión con el prefijo `!` (corre en Git Bash) y tecleando él `<app>` y `<grupo>`. Las lecturas
(`appsettings list`, `sql/read`) y las previas las lanza el líder, con autorización del humano para esa sesión.
`MSYS_NO_PATHCONV=1` evita que Git Bash reescriba el `@<ruta>` y las rutas de las órdenes `az`.

**Qué cambia al publicar, medido** (lectura de `dbo.pro` del líder, 2026-11-06). Las dos `_FORZADA` nacen vacías y las
`_POR_PRODUCTO` de facturas y albaranes dejan de leerse: desde el primer minuto **manda la ficha**, en FR y en las sin
vincular de `sigrid/albaran`. La llave de albaranes está **abierta**.
- **Empresa 1** (la única de `SIGRID_ALBARAN_EMPRESAS_OBRA`):
  - las fichas de `SM9999`, `SB9999` y `SM370001` dicen `SM99`, `SB99` y `SM37`, igual que el mapa viejo de facturas;
  - `QA9999` y `XA9999` dicen `QA99` y `XA99` (H34 del contrato);
  - **solo cambia `MA9999`**: de `MA99` (`<obra>.CDSB37`) a la de su ficha, **`MA1501`** (`<obra>.CDMA15`).
- **Empresa 34:** la ficha de `SM370001` dice **`SM08`**, no `SM37`. Hoy no entra (no está en `EMPRESAS_OBRA`). Si
  algún día entra, manda `SM08` salvo que se fuerce `34:SM370001`.

**T34.0 · Aviso previo a `albaranes`** (el líder, por el humano), **antes** de publicar: desde ese momento, las sin
vincular `MA9999` llevan `MA1501` y `<obra>.CDMA15`, salvo que el humano fuerce `1:MA9999` en T34.4. Se espera su
acuse antes de seguir.

**T34.1 · Lectura de App Settings** (solo lectura). La de proformas sale también y **no se toca** (P23):

```bash
! export MSYS_NO_PATHCONV=1; az functionapp config appsettings list -g <grupo> -n <app> --query "[?contains(name, 'NATURALEZA')].{n:name, v:value}" -o table
```

Esperado:
- las dos `_POR_PRODUCTO` de facturas (seis productos) y de albaranes (tres), con los valores de D1;
- las dos `_FORZADA`, ausentes;
- `SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO`, con lo suyo.

Si sale otra cosa, se para.

**T34.2 · Publicar** (el humano, con autorización expresa) desde `dev` tras el merge de la rama revisada:

```bash
! func azure functionapp publish <app> --python
```

**T34.3 · Previas, solo `commit:false`** (el líder, con el Setup de §S). Antes y después de cada previa, **C0** de §T23 y
el de albaranes: `Fila "SELECT (SELECT MAX(ide) FROM dbo.con), (SELECT COUNT(*) FROM dbo.con WHERE tip = 14)"`. Lo
esperado se lee primero:

```powershell
$nat = Fila "SELECT n.ide, n.cod, n.caagascod, n.cuacomcod FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide JOIN dbo.auxpronat n ON n.ide = p.natide WHERE c.emp = ? AND c.tip = ? AND c.cod = ?" @(1, 3, "MA9999")
$caa = Fila "SELECT c.ide, a.cenide FROM dbo.con c JOIN dbo.caa a ON a.ide = c.ide WHERE c.cod = ?" @("0404.CDMA15")
$cif = (Fila "SELECT TOP 1 d.entcif FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = 15 AND c.cod LIKE ? ORDER BY c.ide DESC" @("FR26/%"))[0]
$gg = Leer "SELECT TOP 5 p.docide, cu.cod, ca.cod FROM dbo.dcfpro p JOIN dbo.con c ON c.ide = p.docide JOIN dbo.con cu ON cu.ide = p.cueide JOIN dbo.con ca ON ca.ide = p.caaide WHERE c.tip = 15 AND c.cod LIKE ? AND p.proide = 0 AND p.docoritip = 0 ORDER BY p.docide DESC" @("FR26/%")
```

`$nat` debe ser `MA1501` y `MOD.CDMA15`; si no, se para (la ficha cambió desde la medición). Si `$caa` sale vacío,
`0404.CDMA15` no existe. Entonces PA y PC dan `analitica_no_resuelta`, que es la regla y no un fallo: se anota.

- **PA · FR con `MA9999` en la obra 0404.** Esperado:
  - `previsto` y `cod_provisional`;
  - `filas.dcfpro[0].natide` = `$nat[0]` y `caaide` = `$caa[0]`;
  - `cueide` = la `cua` del `cuacomcod` de `$nat`.

  ```powershell
  $pa = @{ database = "ruesma"; usu = "prueba"; referencia_externa = "FAC-VERIF-F008-PA-1"; serie = "FR"
           cif_proveedor = $cif; numero_factura = "VERIF-F008-PA-1"; fecha_factura = 20261109; cod_obra = "0404"
           lineas = @(@{ descripcion = "Verificacion enmienda 1"; cantidad = 1.0; precio = 10.0; iva = "I21"; producto = "MA9999" })
           vencimientos = @(@{ fecha = 20261209; importe = 12.1 }); total_base = 10.0; total_iva = 2.1; total_factura = 12.1
           commit = $false }
  $r = Factura $pa; $r.estado; $r.filas.dcfpro | Select-Object natide, cueide, caaide, cenide
  ```
- **PB · FR solo con cuenta y analítica.** Se usan la cuenta (`$gg.rows[0][1]`) y la analítica (`$gg.rows[0][2]`) de
  una FR real sin producto, con el `cod_obra` de la obra de esa factura (como en P4). Es el cuerpo de PA sin `producto`
  y con `cuenta`, `analitica`, `referencia_externa = "FAC-VERIF-F008-PB-1"` y `numero_factura = "VERIF-F008-PB-1"`.
  Esperado:
  - `previsto`, con `cod` `FR26/` y 5 cifras;
  - `proide`, `paride` y `natide` a 0;
  - `cueide` y `caaide` = los de esa línea real.

  Con `producto` **y** `cuenta`: 400 «Solicitud invalida.» (ambigua).
- **PC · `sigrid/albaran` con una sin vincular `MA9999`, SOLO `commit:false`.** La llave de albaranes está abierta, así
  que **nunca** se manda `commit:true` y `commit = $false` va escrito en el cuerpo. Esperado:
  - `estado` `previsto` y `committed` false;
  - `filas.dcapro[0].natide` = `$nat[0]` y `caaide` = `$caa[0]`;
  - C0 de albaranes igual.

  ```powershell
  $U = Fila "SELECT t.ide, t.entcif FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide JOIN dbo.con o ON o.ide = t.obride WHERE c.tip = ? AND c.cod = ? AND o.tip = ? AND o.emp = ? AND o.cod = ?" @(44, "CTSU16/0206", 42, 1, "0404")
  $pc = @{ database = "ruesma"; cod_obra = "0404"; cod_contrato = "CTSU16/0206"; cif_proveedor = $U[1]; usu = "prueba"
           referencia_externa = "ALB-prueba-F008-E1-1"; su_referencia = "prueba-F008-E1-1"; fecha_albaran = 20261109
           lineas = @(@{ referencia_linea = "1"; producto = "MA9999"; descripcion = "Verificacion enmienda 1"; unidad = "UD"; cantidad = 1.0; precio = 1.0 })
           commit = $false }
  $b = $pc | ConvertTo-Json -Depth 8
  $a = Invoke-RestMethod -Uri "$base/api/sigrid/albaran" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($b))
  $a.estado; $a.committed; $a.filas.dcapro | Select-Object natide, cueide, caaide
  ```

**T34.4 · Cargar las `_FORZADA`** (el humano, con autorización expresa). Solo excepciones reales, y el humano decide
cuáles a la vista de PA y PC. Por ejemplo, `{"1:MA9999":"MA99"}` conserva el criterio de H34; `{}` deja mandar la
ficha. Fichero ASCII sin BOM, validado con `Settings` como en D1 de F-007 (el `python` debe imprimir los dos mapas;
si falla, no se sube):

```powershell
$f = "$env:TEMP\f008_forzadas.json"
@'
[{"name":"SIGRID_FACTURA_NATURALEZA_FORZADA","value":"{}","slotSetting":false},
 {"name":"SIGRID_ALBARAN_NATURALEZA_FORZADA","value":"{}","slotSetting":false}]
'@ | Set-Content -Encoding ascii -NoNewline $f
$env:F008_JSON = $f; $f
@'
import json, os
for s in json.load(open(os.environ["F008_JSON"], encoding="ascii")):
    os.environ[s["name"]] = s["value"]
for k, v in {"SQL_DRIVER": "x", "SQL_SERVER_HOST": "x", "SQL_SERVER_PORT": "1",
             "SQL_SERVER_USERNAME": "x", "SQL_SERVER_PASSWORD": "x"}.items():
    os.environ[k] = v
from config.settings import Settings
s = Settings()
print(s.sigrid_factura_naturaleza_forzada, s.sigrid_albaran_naturaleza_forzada)
'@ | .venv\Scripts\python -
```

En el `{}` de cada `value` se escribe lo que decida el humano, con las comillas escapadas como en F-007. La ruta que
imprime `$f`, con barras `/`, va en la orden:

```bash
! export MSYS_NO_PATHCONV=1; az functionapp config appsettings set -g <grupo> -n <app> --settings @<ruta de $f>
```

**T34.5 · Borrar las dos viejas** (el humano, con autorización expresa; la de proformas, **no**):

```bash
! export MSYS_NO_PATHCONV=1; az functionapp config appsettings delete -g <grupo> -n <app> --setting-names SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO
```

**T34.6 · Releer** con la orden de T34.1. Esperado:
- las dos `_FORZADA`, con lo de T34.4;
- ninguna `_POR_PRODUCTO` de facturas ni de albaranes;
- la de proformas, intacta.

Si algo se forzó, se repiten PA y PC (`-2` en las referencias): deben salir con la forzada.

**Qué se anota** en `progress/verificacion_F-008.md`, sección «T34 · Enmienda 1»:
- el acuse de `albaranes`;
- las salidas de T34.1 y T34.6;
- el commit publicado;
- `$nat` y `$caa`;
- de PA, PB y PC: estado, `natide`, `cueide` y `caaide`, y C0 antes y después, solo con `con.ide` y códigos (nunca CIF
  ni nombres);
- la decisión del humano sobre los forzados, con su fecha.

