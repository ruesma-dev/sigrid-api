# infra/scripts/setup-deploy-write.ps1
# =====================================================================
# Habilita la ESCRITURA en sigrid-api y redespliega.
#
# Qué hace:
#   1) Selecciona la suscripcion.
#   2) Obtiene la password de user_rw (env var -> .env -> prompt) y la guarda
#      como secreto en Key Vault.
#   3) Fija TODOS los app settings de escritura de una vez via fichero JSON
#      (evita que cmd.exe/PowerShell rompan parentesis, comillas y ';').
#      ro_user NO se toca.
#   4) Publica el codigo (endpoint sql/write) con Core Tools.
#   5) Reinicia para forzar la re-resolucion de la referencia a Key Vault.
#
# Origen de la password (en este orden):
#   1) $env:SQL_SERVER_WRITE_PASSWORD
#   2) .env en la raiz del proyecto (clave SQL_SERVER_WRITE_PASSWORD)
#   3) Prompt interactivo
#
# Uso (desde cualquier ruta):
#   .\infra\scripts\setup-deploy-write.ps1
# =====================================================================

$ErrorActionPreference = "Stop"

# ----------------------------- PARAMETROS ----------------------------
$Subscription        = "863dfedd-d208-467f-9e8b-415e9cb59c5d"
$ResourceGroup       = "rg-sigrid-dev-data-api"
$FunctionApp         = "func-sigridapi-dev-huyke"
$KeyVault            = "kv-sigridapi-dev-huyke"
$WriteSecretName     = "sigrid-write-password"
$WriteUser           = "user_rw"
$WritePasswordEnvVar = "SQL_SERVER_WRITE_PASSWORD"

# Valores operacionales de escritura.
$AllowedWriteDbs      = '["ruesma"]'
$AllowedWritePrefixes = '["INSERT","UPDATE","DELETE"]'
$DefaultWriteTimeout  = "30"
$MaxWriteTimeout      = "120"
$DefaultMaxAffected   = "200"
$MaxAffected          = "1000"
$MaxStatementsBatch   = "50"
$UseFastExecutemany   = "true"
$RequireWhere         = "true"
# ---------------------------------------------------------------------

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")

function Assert-LastExit {
    param([string]$What)
    if ($LASTEXITCODE -ne 0) {
        throw "Fallo en: $What (codigo $LASTEXITCODE)."
    }
}

function Import-DotEnv {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    Write-Host "==> Cargando variables desde $Path" -ForegroundColor Cyan
    foreach ($line in Get-Content -Path $Path) {
        $trimmed = $line.Trim()
        if ($trimmed -eq "" -or $trimmed.StartsWith("#")) { continue }
        $idx = $trimmed.IndexOf("=")
        if ($idx -lt 1) { continue }
        $key = $trimmed.Substring(0, $idx).Trim()
        $val = $trimmed.Substring($idx + 1).Trim()
        if (($val.StartsWith('"') -and $val.EndsWith('"')) -or
            ($val.StartsWith("'") -and $val.EndsWith("'"))) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        if ([string]::IsNullOrEmpty([Environment]::GetEnvironmentVariable($key))) {
            [Environment]::SetEnvironmentVariable($key, $val)
        }
    }
}

function Resolve-WritePassword {
    $fromEnv = [Environment]::GetEnvironmentVariable($WritePasswordEnvVar)
    if (-not [string]::IsNullOrWhiteSpace($fromEnv)) {
        Write-Host "==> Password de $WriteUser tomada de $WritePasswordEnvVar" -ForegroundColor Cyan
        return $fromEnv
    }
    Write-Host "==> Introduce la password de $WriteUser (no se mostrara):" -ForegroundColor Yellow
    $secure = Read-Host -AsSecureString
    $bstr   = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

Write-Host "==> Suscripcion: $Subscription" -ForegroundColor Cyan
az account set --subscription $Subscription
Assert-LastExit "az account set"

# --- 1) Password de user_rw ------------------------------------------
Import-DotEnv -Path (Join-Path $ProjectRoot ".env")
$plain = Resolve-WritePassword
if ([string]::IsNullOrWhiteSpace($plain)) { throw "No se pudo obtener la password de $WriteUser." }

# --- 2) Secreto en Key Vault -----------------------------------------
Write-Host "==> Guardando secreto '$WriteSecretName' en $KeyVault ..." -ForegroundColor Cyan
az keyvault secret set --vault-name $KeyVault --name $WriteSecretName --value $plain | Out-Null
Assert-LastExit "az keyvault secret set"
$plain = $null

$secretRef = "@Microsoft.KeyVault(VaultName=$KeyVault;SecretName=$WriteSecretName)"

# --- 3) App settings de escritura via FICHERO JSON -------------------
# Se construye el JSON con ConvertTo-Json (escapa comillas solo) y se
# escribe en ASCII a una ruta que siempre existe ($env:TEMP).
$settings = @(
    @{ name = "SQL_SERVER_WRITE_USERNAME";      value = $WriteUser;            slotSetting = $false }
    @{ name = "SQL_SERVER_WRITE_PASSWORD";      value = $secretRef;            slotSetting = $false }
    @{ name = "ALLOWED_WRITE_DATABASES";        value = $AllowedWriteDbs;      slotSetting = $false }
    @{ name = "ALLOWED_WRITE_PREFIXES";         value = $AllowedWritePrefixes; slotSetting = $false }
    @{ name = "DEFAULT_WRITE_TIMEOUT_SECONDS";  value = $DefaultWriteTimeout;  slotSetting = $false }
    @{ name = "MAX_WRITE_TIMEOUT_SECONDS";      value = $MaxWriteTimeout;      slotSetting = $false }
    @{ name = "DEFAULT_MAX_AFFECTED_ROWS";      value = $DefaultMaxAffected;   slotSetting = $false }
    @{ name = "MAX_AFFECTED_ROWS";              value = $MaxAffected;          slotSetting = $false }
    @{ name = "MAX_STATEMENTS_PER_BATCH";       value = $MaxStatementsBatch;   slotSetting = $false }
    @{ name = "USE_FAST_EXECUTEMANY";           value = $UseFastExecutemany;   slotSetting = $false }
    @{ name = "REQUIRE_WHERE_ON_UPDATE_DELETE"; value = $RequireWhere;         slotSetting = $false }
)
$json = ConvertTo-Json -InputObject $settings -Depth 3
$settingsFile = Join-Path $env:TEMP "sigrid-write-settings.json"
Set-Content -Path $settingsFile -Value $json -Encoding ascii

Write-Host "==> Fijando app settings de escritura en $FunctionApp ..." -ForegroundColor Cyan
az functionapp config appsettings set `
    --name $FunctionApp `
    --resource-group $ResourceGroup `
    --settings "@$settingsFile" | Out-Null
Assert-LastExit "az functionapp config appsettings set"
Remove-Item $settingsFile -ErrorAction SilentlyContinue

# --- 4) Publicar el codigo -------------------------------------------
Write-Host "==> Publicando codigo desde $ProjectRoot ..." -ForegroundColor Cyan
Push-Location $ProjectRoot
try {
    func azure functionapp publish $FunctionApp
}
finally {
    Pop-Location
}

# --- 5) Reiniciar (re-resolver referencia a Key Vault) ---------------
Write-Host "==> Reiniciando para re-resolver la referencia a Key Vault ..." -ForegroundColor Cyan
az functionapp restart --name $FunctionApp --resource-group $ResourceGroup
Assert-LastExit "az functionapp restart"

# --- 6) Verificacion -------------------------------------------------
Write-Host "==> App settings de escritura:" -ForegroundColor Green
az functionapp config appsettings list `
    --name $FunctionApp `
    --resource-group $ResourceGroup `
    --query "[?starts_with(name,'SQL_SERVER_WRITE') || starts_with(name,'ALLOWED_WRITE') || contains(name,'AFFECTED') || contains(name,'WRITE_TIMEOUT') || name=='MAX_STATEMENTS_PER_BATCH' || name=='USE_FAST_EXECUTEMANY' || name=='REQUIRE_WHERE_ON_UPDATE_DELETE'].{name:name,value:value}" `
    --output table

Write-Host ""
Write-Host "OK. Escritura habilitada y codigo publicado." -ForegroundColor Green
Write-Host "Espera 1-2 min a que resuelva la referencia a Key Vault y prueba sql/write." -ForegroundColor Yellow
