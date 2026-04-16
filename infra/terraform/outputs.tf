output "resource_group_name" {
  value       = azurerm_resource_group.this.name
  description = "Resource group de la API."
}

output "function_app_name" {
  value       = azurerm_function_app_flex_consumption.this.name
  description = "Nombre de la Function App."
}

output "function_app_url" {
  value       = "https://${azurerm_function_app_flex_consumption.this.name}.azurewebsites.net"
  description = "URL base de la Function App."
}

output "storage_account_name" {
  value       = azurerm_storage_account.this.name
  description = "Storage account de la Function App."
}

output "deployment_container_name" {
  value       = azurerm_storage_container.deployment.name
  description = "Contenedor blob usado por la Function App Flex para despliegues."
}

output "key_vault_name" {
  value       = azurerm_key_vault.this.name
  description = "Nombre del Key Vault."
}

output "sql_password_secret_name" {
  value       = var.sql_password_secret_name
  description = "Nombre del secreto esperado en Key Vault para la contraseña SQL."
}

output "function_subnet_id" {
  value       = azurerm_subnet.function_integration.id
  description = "Subnet dedicada para la Function App."
}

output "set_sql_secret_command" {
  value       = "az keyvault secret set --vault-name ${azurerm_key_vault.this.name} --name ${var.sql_password_secret_name} --value '<REEMPLAZAR_CON_LA_PASSWORD_SQL>'"
  description = "Comando sugerido para cargar manualmente la contraseña SQL en Key Vault sin dejarla en el estado de Terraform."
}

output "publish_code_command" {
  value       = "func azure functionapp publish ${azurerm_function_app_flex_consumption.this.name} --python"
  description = "Comando sugerido para publicar el código de la Function App."
}

output "get_host_keys_command" {
  value       = "az functionapp keys list -g ${azurerm_resource_group.this.name} -n ${azurerm_function_app_flex_consumption.this.name}"
  description = "Comando sugerido para recuperar las host keys de la Function App."
}
