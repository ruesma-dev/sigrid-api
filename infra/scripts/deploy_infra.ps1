param(
    [string]$SubscriptionId = "863dfedd-d208-467f-9e8b-415e9cb59c5d",
    [string]$TerraformFolder = ".\infra\terraform"
)

$ErrorActionPreference = "Stop"

Write-Host "Login en Azure si es necesario..."
az account show | Out-Null

Write-Host "Seleccionando suscripción $SubscriptionId..."
az account set --subscription $SubscriptionId

Write-Host "Registrando Microsoft.App..."
az provider register --namespace Microsoft.App | Out-Null

Push-Location $TerraformFolder
try {
    $env:ARM_SUBSCRIPTION_ID = $SubscriptionId

    terraform init -upgrade
    terraform plan -out main.tfplan
    terraform apply main.tfplan
}
finally {
    Pop-Location
}
