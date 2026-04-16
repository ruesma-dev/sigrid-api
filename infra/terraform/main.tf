locals {
  location_short = replace(var.location, " ", "")
}

data "azurerm_client_config" "current" {}

resource "random_string" "suffix" {
  length  = 5
  special = false
  upper   = false
  numeric = true
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location
  tags     = var.tags
}

data "azurerm_virtual_network" "spoke_dev" {
  name                = var.existing_spoke_vnet_name
  resource_group_name = var.existing_spoke_vnet_resource_group_name
}

# Route table ya existente y utilizada por la subnet de la VM que sí llega a on-prem.
data "azurerm_route_table" "spoke_std" {
  name                = "rt-spoke-std-spaincentral"
  resource_group_name = "rg-hub-spaincentral"
}

resource "azurerm_subnet" "function_integration" {
  name                 = var.function_subnet_name
  resource_group_name  = data.azurerm_virtual_network.spoke_dev.resource_group_name
  virtual_network_name = data.azurerm_virtual_network.spoke_dev.name
  address_prefixes     = var.function_subnet_address_prefixes

  delegation {
    name = "delegation-microsoft-app-environments"

    service_delegation {
      name = "Microsoft.App/environments"
    }
  }
}

resource "azurerm_subnet_route_table_association" "function_integration" {
  subnet_id      = azurerm_subnet.function_integration.id
  route_table_id = data.azurerm_route_table.spoke_std.id
}

resource "azurerm_storage_account" "this" {
  name                     = substr("st${var.project_code}${var.environment}${random_string.suffix.result}", 0, 24)
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = var.tags
}

resource "azurerm_storage_container" "deployment" {
  name                  = "function-code"
  storage_account_id    = azurerm_storage_account.this.id
  container_access_type = "private"
}

resource "azurerm_service_plan" "this" {
  name                = "asp-${var.project_code}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  os_type             = "Linux"
  sku_name            = "FC1"
  tags                = var.tags
}

resource "azurerm_key_vault" "this" {
  name                       = substr("kv-${var.project_code}-${var.environment}-${random_string.suffix.result}", 0, 24)
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  rbac_authorization_enabled = true
  purge_protection_enabled   = false
  soft_delete_retention_days = 7
  tags                       = var.tags
}

resource "azurerm_function_app_flex_consumption" "this" {
  name                = "func-${var.project_code}-${var.environment}-${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.this.name
  location            = azurerm_resource_group.this.location
  service_plan_id     = azurerm_service_plan.this.id

  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.this.primary_blob_endpoint}${azurerm_storage_container.deployment.name}"
  storage_authentication_type = "StorageAccountConnectionString"
  storage_access_key          = azurerm_storage_account.this.primary_access_key

  runtime_name           = var.function_runtime_name
  runtime_version        = var.function_runtime_version
  maximum_instance_count = var.maximum_instance_count
  instance_memory_in_mb  = var.instance_memory_in_mb

  site_config {}

  virtual_network_subnet_id = azurerm_subnet.function_integration.id

  identity {
    type = "SystemAssigned"
  }

  app_settings = {
    SQL_DRIVER                    = "ODBC Driver 18 for SQL Server"
    SQL_SERVER_HOST               = var.sql_server_host
    SQL_SERVER_PORT               = tostring(var.sql_server_port)
    SQL_SERVER_USERNAME           = var.sql_server_username
    SQL_SERVER_PASSWORD           = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.this.name};SecretName=${var.sql_password_secret_name})"
    DEFAULT_QUERY_TIMEOUT_SECONDS = tostring(var.default_query_timeout_seconds)
    MAX_QUERY_TIMEOUT_SECONDS     = tostring(var.max_query_timeout_seconds)
    DEFAULT_MAX_ROWS              = tostring(var.default_max_rows)
    MAX_ALLOWED_ROWS              = tostring(var.max_allowed_rows)
    MAX_INLINE_BINARY_BYTES       = tostring(var.max_inline_binary_bytes)
    ALLOWED_DATABASES             = jsonencode(var.allowed_databases)
    ALLOWED_QUERY_PREFIXES        = jsonencode(var.allowed_query_prefixes)
  }

  tags = var.tags

  depends_on = [
    azurerm_subnet_route_table_association.function_integration
  ]
}

resource "azurerm_role_assignment" "function_key_vault_secrets_user" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_function_app_flex_consumption.this.identity[0].principal_id
  principal_type       = "ServicePrincipal"
}

resource "azurerm_role_assignment" "current_principal_key_vault_secrets_officer" {
  count                = var.grant_current_principal_key_vault_secrets_officer ? 1 : 0
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets Officer"
  principal_id         = data.azurerm_client_config.current.object_id
  principal_type       = "User"
}