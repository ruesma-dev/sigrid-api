# infra/scripts/discover-write-schema.ps1
# =====================================================================
# Consultas de SOLO LECTURA para confirmar la arquitectura de BBDD de
# Sigrid antes de diseñar la escritura de albaranes y de lineas de contrato.
#
# No escribe nada. Lanza una bateria de SELECT contra /api/sql/read y
# muestra el resultado de cada uno con su etiqueta.
#
# Uso recomendado (vuelca todo a un fichero para pegarmelo):
#   .\infra\scripts\discover-write-schema.ps1 *> discover.txt
#
# Si alguna consulta a sys.* da error de permisos, no pasa nada: el script
# sigue con las demas y lo veremos en la salida.
# =====================================================================

$ErrorActionPreference = "Continue"

$base = "https://func-sigridapi-dev-huyke.azurewebsites.net"
$key  = az functionapp keys list --name func-sigridapi-dev-huyke --resource-group rg-sigrid-dev-data-api --query "functionKeys.default" -o tsv
$headers = @{ "x-functions-key" = $key }
$DB = "ruesma"

function Invoke-Read {
    param([string]$Label, [string]$Sql, [int]$MaxRows = 1000)
    Write-Host ""
    Write-Host "===== $Label =====" -ForegroundColor Cyan
    $body = @{ database = $DB; sql = $Sql; max_rows = $MaxRows } | ConvertTo-Json
    try {
        Invoke-RestMethod -Uri "$base/api/sql/read" -Method Post -Headers $headers -ContentType "application/json" -Body $body | ConvertTo-Json -Depth 6
    }
    catch {
        if ($_.ErrorDetails -and $_.ErrorDetails.Message) { $_.ErrorDetails.Message }
        elseif ($_.Exception.Response) { (New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())).ReadToEnd() }
        else { $_.Exception.Message }
    }
}

# ---------------------------------------------------------------------
# GRUPO A — Generacion de 'ide' (lo critico)
# ---------------------------------------------------------------------

Invoke-Read "A1 - ¿ide es IDENTITY en las tablas clave?" @"
SELECT OBJECT_NAME(c.object_id) AS tabla, c.name AS columna, c.is_identity
FROM sys.columns c
WHERE c.name = 'ide'
  AND c.object_id IN (OBJECT_ID('dbo.con'), OBJECT_ID('dbo.dca'), OBJECT_ID('dbo.dcapro'),
                      OBJECT_ID('dbo.dcapropar'), OBJECT_ID('dbo.obrparpar'), OBJECT_ID('dbo.obrparpre'),
                      OBJECT_ID('dbo.obrctr'))
ORDER BY tabla
"@

Invoke-Read "A2 - ¿Existe ALGUNA columna IDENTITY en la BD?" @"
SELECT OBJECT_NAME(object_id) AS tabla, name AS columna, seed_value, increment_value
FROM sys.identity_columns
ORDER BY tabla
"@

Invoke-Read "A3 - ¿Hay tabla contador / numerador / secuencia?" @"
SELECT TABLE_SCHEMA, TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_TYPE = 'BASE TABLE'
  AND (TABLE_NAME LIKE 'k[_]%' OR TABLE_NAME LIKE '%numera%' OR TABLE_NAME LIKE '%contad%'
       OR TABLE_NAME LIKE '%secuen%' OR TABLE_NAME LIKE '%seq%' OR TABLE_NAME LIKE '%maxid%'
       OR TABLE_NAME LIKE '%ultim%' OR TABLE_NAME LIKE '%siguien%')
ORDER BY TABLE_NAME
"@

Invoke-Read "A4 - ¿Hay objetos SEQUENCE?" @"
SELECT name, start_value, increment, current_value FROM sys.sequences ORDER BY name
"@

Invoke-Read "A5 - Rango actual de con.ide (magnitud del contador)" @"
SELECT MIN(ide) AS min_ide, MAX(ide) AS max_ide, COUNT(*) AS filas FROM dbo.con
"@

# ---------------------------------------------------------------------
# GRUPO B — Estructura del ALBARAN de compra (con + dca + dcapro + dcapropar)
# ---------------------------------------------------------------------

Invoke-Read "B1 - Columnas de con/dca/dcapro/dcapropar/dcaproana" @"
SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('con','dca','dcapro','dcapropar','dcaproana')
ORDER BY TABLE_NAME, ORDINAL_POSITION
"@ 1000

Invoke-Read "B2a - Plantilla: 3 ultimos albaranes (cabecera dca)" @"
SELECT TOP 3 * FROM dbo.dca ORDER BY ide DESC
"@ 3

Invoke-Read "B2b - Plantilla: el con de esos albaranes (discriminador)" @"
SELECT TOP 3 c.* FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide ORDER BY c.ide DESC
"@ 3

Invoke-Read "B3 - Plantilla: ultimas lineas de albaran (dcapro)" @"
SELECT TOP 20 * FROM dbo.dcapro ORDER BY ide DESC
"@ 20

Invoke-Read "B4 - Plantilla: ultimos desgloses por partida (dcapropar)" @"
SELECT TOP 20 * FROM dbo.dcapropar ORDER BY ide DESC
"@ 20

# ---------------------------------------------------------------------
# GRUPO C — Estructura del CONTRATO y sus lineas (obrctr + obrparpar + obrparpre)
# ---------------------------------------------------------------------

Invoke-Read "C1 - Columnas de obrctr/obrparpar/obrparpre/auxobramb" @"
SELECT TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('obrctr','obrparpar','obrparpre','auxobramb')
ORDER BY TABLE_NAME, ORDINAL_POSITION
"@ 1000

Invoke-Read "C2 - Plantilla: 5 ultimos contratos (obrctr)" @"
SELECT TOP 5 * FROM dbo.obrctr ORDER BY ide DESC
"@ 5

Invoke-Read "C3 - Partidas de la obra 0404 (ide 828942) con su contrato" @"
SELECT TOP 50 p.ide, p.obride, p.padide, p.ctride, p.expide, p.pos, p.tip, p.cod, p.res,
       p.tipcos, p.tipvis, p.tipcon, p.proide, p.unimed
FROM dbo.obrparpar p
WHERE p.obride = 828942
ORDER BY p.pos
"@ 50

Invoke-Read "C4 - Presupuesto/medicion (obrparpre) de la obra 0404 por ambito/fase" @"
SELECT TOP 50 pr.ide, pr.obride, pr.paride, pr.amb, pr.fas, pr.can, pr.pre
FROM dbo.obrparpre pr
WHERE pr.obride = 828942
ORDER BY pr.paride, pr.amb, pr.fas
"@ 50

Invoke-Read "C5 - Ambitos de obra disponibles (auxobramb)" @"
SELECT TOP 50 * FROM dbo.auxobramb ORDER BY ide
"@ 50

# ---------------------------------------------------------------------
# GRUPO D — Integridad: triggers, claves foraneas y unicidad
# ---------------------------------------------------------------------

Invoke-Read "D1 - Triggers en las tablas implicadas" @"
SELECT OBJECT_NAME(t.parent_id) AS tabla, t.name AS trigger_name, t.is_disabled, t.is_instead_of_trigger
FROM sys.triggers t
WHERE OBJECT_NAME(t.parent_id) IN ('con','dca','dcapro','dcapropar','obrparpar','obrparpre','obrctr')
ORDER BY tabla
"@

Invoke-Read "D2 - ¿Hay claves foraneas definidas (integridad referencial real)?" @"
SELECT OBJECT_NAME(fk.parent_object_id) AS tabla, fk.name AS fk_name,
       OBJECT_NAME(fk.referenced_object_id) AS referencia
FROM sys.foreign_keys fk
WHERE OBJECT_NAME(fk.parent_object_id) IN ('con','dca','dcapro','dcapropar','obrparpar','obrparpre')
   OR OBJECT_NAME(fk.referenced_object_id) IN ('con','dca','obrparpar','obrctr')
ORDER BY tabla
"@

Invoke-Read "D3 - PK / indices unicos en las tablas clave" @"
SELECT OBJECT_NAME(i.object_id) AS tabla, i.name AS indice, i.is_primary_key, i.is_unique, c.name AS columna
FROM sys.indexes i
JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
JOIN sys.columns c ON c.object_id = i.object_id AND c.column_id = ic.column_id
WHERE OBJECT_NAME(i.object_id) IN ('con','dca','dcapro','obrparpar','obrparpre','obrctr')
  AND (i.is_primary_key = 1 OR i.is_unique = 1)
ORDER BY tabla, indice
"@

Write-Host ""
Write-Host "===== FIN =====" -ForegroundColor Green
