<!-- specs/F-008-registrar-factura/verificacion_manual.md -->
# F-008 · Verificación manual (T22-T24)

Los pasos exactos de T22, T23 y T24, con el modelo de
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
