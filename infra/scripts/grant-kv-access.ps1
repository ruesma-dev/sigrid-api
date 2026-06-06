# infra/scripts/grant-kv-access.ps1
# =====================================================================
# Concede a la identidad administrada (System Assigned) de la Function App
# permiso para LEER secretos del Key Vault.
#
# NOTA: normalmente NO hace falta ejecutarlo, porque la identidad ya lee
# secretos de este vault para ro_user (el permiso es a nivel de vault).
# Se incluye por si en algun momento hubiera que reconcederlo.
#
# Corregido respecto a la version anterior:
#   - Vault correcto: kv-sigridapi-dev-huyke.
#   - Comprueba el codigo de salida de az; ya NO da "OK" en falso.
#
# Uso:
#   .\infra\scripts\grant-kv-access.ps1
# =====================================================================

$ErrorActionPreference = "Stop"

# ----------------------------- PARAMETROS ----------------------------
$Subscription  = "863dfedd-d208-467f-9e8b-415e9cb59c5d"
$ResourceGroup = "rg-sigrid-dev-data-api"
$FunctionApp   = "func-sigridapi-dev-huyke"
$KeyVault      = "kv-sigridapi-dev-huyke"
$RoleName      = "Key Vault Secrets User"
# ---------------------------------------------------------------------

function Assert-LastExit {
    param([string]$What)
    if ($LASTEXITCODE -ne 0) { throw "Fallo en: $What (codigo $LASTEXITCODE)." }
}

Write-Host "==> Suscripcion: $Subscription" -ForegroundColor Cyan
az account set --subscription $Subscription
Assert-LastExit "az account set"

# --- 1) Principal Id de la identidad System Assigned -----------------
Write-Host "==> Comprobando identidad administrada de $FunctionApp ..." -ForegroundColor Cyan
$principalId = az functionapp identity show `
    --name $FunctionApp `
    --resource-group $ResourceGroup `
    --query principalId -o tsv

if ([string]::IsNullOrWhiteSpace($principalId)) {
    Write-Host "    No estaba activada. Activando System Assigned ..." -ForegroundColor Yellow
    az functionapp identity assign --name $FunctionApp --resource-group $ResourceGroup | Out-Null
    Assert-LastExit "az functionapp identity assign"
    $principalId = az functionapp identity show --name $FunctionApp --resource-group $ResourceGroup --query principalId -o tsv
}
Write-Host "    principalId: $principalId"

# --- 2) Scope del Key Vault y modo de autorizacion -------------------
$kvScope = az keyvault show --name $KeyVault --query id -o tsv
Assert-LastExit "az keyvault show (id)"
$rbacEnabled = az keyvault show --name $KeyVault --query properties.enableRbacAuthorization -o tsv
Assert-LastExit "az keyvault show (rbac)"
Write-Host "==> Key Vault: $KeyVault (RBAC=$rbacEnabled)" -ForegroundColor Cyan

if ($rbacEnabled -eq "true") {
    $existing = az role assignment list --assignee $principalId --scope $kvScope --query "[?roleDefinitionName=='$RoleName'].id" -o tsv
    if ([string]::IsNullOrWhiteSpace($existing)) {
        Write-Host "==> Asignando rol '$RoleName' (RBAC) ..." -ForegroundColor Cyan
        az role assignment create `
            --assignee-object-id $principalId `
            --assignee-principal-type ServicePrincipal `
            --role $RoleName `
            --scope $kvScope | Out-Null
        Assert-LastExit "az role assignment create"
        Write-Host "    Rol asignado." -ForegroundColor Green
    }
    else {
        Write-Host "    El rol ya estaba asignado. Nada que hacer." -ForegroundColor Green
    }
}
else {
    Write-Host "==> Configurando access policy (get,list de secretos) ..." -ForegroundColor Cyan
    az keyvault set-policy --name $KeyVault --object-id $principalId --secret-permissions get list | Out-Null
    Assert-LastExit "az keyvault set-policy"
    Write-Host "    Access policy aplicada." -ForegroundColor Green
}

Write-Host ""
Write-Host "OK. La Function App puede leer secretos de $KeyVault." -ForegroundColor Green
Write-Host "Una asignacion RBAC nueva puede tardar 1-2 min en propagarse." -ForegroundColor Yellow
