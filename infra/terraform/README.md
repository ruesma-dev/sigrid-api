# infra/terraform

Terraform de infraestructura para desplegar la API `sigrid-api` en Azure Functions Flex Consumption, integrada en el spoke DEV.

## Qué crea

- Resource Group dedicado para la API
- Storage Account + contenedor de despliegue
- Service Plan FC1 (Flex Consumption)
- Key Vault en RBAC
- Subnet dedicada con delegación `Microsoft.App/environments`
- Function App Flex Consumption con:
  - Python 3.12
  - VNet integration al spoke DEV
  - System Assigned Managed Identity
  - app settings de la aplicación
  - referencia a Key Vault para la contraseña SQL

## Qué NO crea

- El secreto SQL dentro de Key Vault
- El código de la Function App
- APIM, Front Door o Private Endpoint

## Importante sobre secretos

La contraseña SQL no se crea con Terraform para no dejarla persistida en el `terraform.tfstate`.
Después del `apply`, usa el `output set_sql_secret_command`.

## Requisitos previos

1. Azure CLI autenticado con permisos en la suscripción
2. Terraform instalado
3. Provider `Microsoft.App` registrado en la suscripción:
   `az provider register --namespace Microsoft.App`
4. VNet del spoke DEV ya existente

## Flujo

1. Copia `terraform.tfvars.example` a `terraform.tfvars`
2. Ajusta nombres y prefijos si hace falta
3. Ejecuta:

```powershell
terraform init -upgrade
terraform plan -out main.tfplan
terraform apply main.tfplan
```

4. Carga el secreto SQL en Key Vault con el comando del output
5. Publica el código con:
   `func azure functionapp publish <nombre-func-app> --python`
