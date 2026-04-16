# docs/DEPLOYMENT_TERRAFORM_AND_CODE.md

## 1. Estructura recomendada en PyCharm

Abre en PyCharm la carpeta raíz:

```text
sigrid-api/
```

Dentro tendrás:

- `function_app.py` y el código de Azure Functions
- `infra/terraform/` con el Terraform
- `infra/scripts/deploy_infra.ps1` para automatizar el apply local

## 2. Requisitos en tu equipo local

### Herramientas

- Python 3.12
- Terraform 1.6 o superior
- Azure CLI
- Azure Functions Core Tools v4
- Git (opcional)
- Driver ODBC 18 para SQL Server si vas a ejecutar pruebas locales directas

### Login Azure

```powershell
az login
az account set --subscription 863dfedd-d208-467f-9e8b-415e9cb59c5d
```

## 3. Qué valores necesitas antes del despliegue

### Datos ya conocidos en vuestro entorno

- Suscripción: `863dfedd-d208-467f-9e8b-415e9cb59c5d`
- Región: `spaincentral`
- VNet existente del spoke DEV: `vnet-spoke-dev-spaincentral`
- RG de la VNet del spoke DEV: `rg-spoke-dev-spaincentral`
- SQL host on-prem: `192.168.14.238`
- SQL puerto on-prem: `49782` (mejor cambiar a fijo en el futuro)
- SQL usuario: `ro_user`

### Dato que te tiene que dar DBA / sistemas

- Contraseña SQL de `ro_user`

### Dato que debes decidir tú

- Subnet libre dedicada para la Function App, por ejemplo `10.0.193.0/27`

## 4. Preparar terraform.tfvars

Copia:

```text
infra/terraform/terraform.tfvars.example
```

a:

```text
infra/terraform/terraform.tfvars
```

y ajusta los valores si hace falta.

## 5. Desplegar infraestructura

En la terminal de PyCharm o en PowerShell:

```powershell
cd .\infra\terraform
$env:ARM_SUBSCRIPTION_ID = "863dfedd-d208-467f-9e8b-415e9cb59c5d"

az provider register --namespace Microsoft.App

terraform init -upgrade
terraform plan -out main.tfplan
terraform apply main.tfplan
```

## 6. Qué hace Terraform

- crea `rg-sigrid-dev-data-api`
- crea una subnet dedicada para la Function App
- crea Storage Account y blob container para despliegue
- crea Key Vault
- crea Function App Flex Consumption en Python 3.12
- asigna identidad administrada a la Function App
- da a esa identidad el rol `Key Vault Secrets User`
- da al principal con el que haces `az login` el rol `Key Vault Secrets Officer` en el Key Vault

## 7. Cargar el secreto SQL en Key Vault

Tras el apply, ejecuta el comando que te devuelve el output `set_sql_secret_command`.

Ejemplo:

```powershell
az keyvault secret set --vault-name <kv-name> --name sql-server-password --value "<PASSWORD_SQL_REAL>"
```

## 8. Preparar el entorno local para publicar código

En la raíz del proyecto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 9. Probar localmente (opcional)

Copia:

```text
local.settings.sample.json
```

a:

```text
local.settings.json
```

Para pruebas locales, NO uses la referencia de Key Vault.
Pon valores directos en `local.settings.json`.

Luego:

```powershell
func start
```

## 10. Publicar el código a Azure

Desde la raíz del proyecto:

```powershell
func azure functionapp publish <NOMBRE_FUNCTION_APP> --python
```

Puedes obtener el nombre exacto desde:

```powershell
cd .\infra\terraform
terraform output function_app_name
```

## 11. Obtener la host key

Una vez desplegado el código:

```powershell
az functionapp keys list -g <RG_API> -n <NOMBRE_FUNCTION_APP>
```

Usa la `default` host key o la que prefieras.

## 12. Probar el endpoint SQL

Ejemplo con PowerShell:

```powershell
$body = @{
  database = "ruesma_rep"
  sql = "SELECT TOP 5 ide, nom, nomori FROM dbo.gra ORDER BY ide DESC"
  parameters = @()
  timeout_seconds = 30
  max_rows = 5
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri "https://<NOMBRE_FUNCTION_APP>.azurewebsites.net/api/sql/read" `
  -Headers @{ "x-functions-key" = "<HOST_KEY>" } `
  -ContentType "application/json" `
  -Body $body
```

## 13. Probar el endpoint de documentos

```powershell
$body = @{
  database = "ruesma_rep"
  schema = "dbo"
  table = "gra"
  id_column = "ide"
  id_value = 340434
  blob_column = "ima"
  filename_columns = @("nomori", "nom")
  disposition = "attachment"
} | ConvertTo-Json

Invoke-WebRequest `
  -Method Post `
  -Uri "https://<NOMBRE_FUNCTION_APP>.azurewebsites.net/api/documents/read" `
  -Headers @{ "x-functions-key" = "<HOST_KEY>" } `
  -ContentType "application/json" `
  -Body $body `
  -OutFile ".\DNI MANUEL CASTILLO BURGOS.pdf"
```

## 14. Dónde conseguir la información que falta

- `subscription_id`: de `az account show --query id -o tsv`
- `existing_spoke_vnet_name`: ya existe en Azure Portal (`vnet-spoke-dev-spaincentral`)
- `existing_spoke_vnet_resource_group_name`: ya existe (`rg-spoke-dev-spaincentral`)
- `sql_server_host`: del host on-prem validado
- `sql_server_port`: del SQL Server actual (`49782`) o el fijo que os deje DBA
- `sql_server_username`: del DBA (`ro_user`)
- `sql_password`: lo fija DBA y lo cargas tú manualmente en Key Vault
- `function_app_name`: lo da `terraform output function_app_name`
- `key_vault_name`: lo da `terraform output key_vault_name`
- `host key`: la obtienes con `az functionapp keys list`

## 15. Recomendación operativa

Mientras el SQL siga con puerto dinámico, la app funcionará si actualizas el puerto en Terraform/app settings.
Pero para dejarlo estable, pedid a DBA un puerto fijo y abrid solo ese puerto desde el spoke DEV.
