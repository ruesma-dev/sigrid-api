variable "subscription_id" {
  description = "ID de la suscripción de Azure donde se desplegará la infraestructura."
  type        = string
}

variable "location" {
  description = "Región de Azure para el despliegue."
  type        = string
  default     = "spaincentral"
}

variable "resource_group_name" {
  description = "Nombre del resource group de la app."
  type        = string
  default     = "rg-sigrid-dev-data-api"
}

variable "existing_spoke_vnet_resource_group_name" {
  description = "Resource group donde ya existe la VNet del spoke DEV."
  type        = string
  default     = "rg-spoke-dev-spaincentral"
}

variable "existing_spoke_vnet_name" {
  description = "Nombre de la VNet existente del spoke DEV."
  type        = string
  default     = "vnet-spoke-dev-spaincentral"
}

variable "function_subnet_name" {
  description = "Nombre de la subnet dedicada para la integración de la Function App."
  type        = string
  default     = "snet-func-sigrid-dev"
}

variable "function_subnet_address_prefixes" {
  description = "Prefijos CIDR de la subnet dedicada de la Function App. Debe ser una subnet libre y dedicada."
  type        = list(string)
  default     = ["10.0.193.0/27"]
}

variable "project_code" {
  description = "Código corto del proyecto para nombres y tags."
  type        = string
  default     = "sigridapi"
}

variable "environment" {
  description = "Entorno de despliegue."
  type        = string
  default     = "dev"
}

variable "sql_server_host" {
  description = "IP o FQDN del SQL Server on-prem."
  type        = string
  default     = "192.168.14.238"
}

variable "sql_server_port" {
  description = "Puerto TCP del SQL Server on-prem."
  type        = number
  default     = 49782
}

variable "sql_server_username" {
  description = "Usuario SQL Server de solo lectura."
  type        = string
  default     = "ro_user"
}

variable "sql_password_secret_name" {
  description = "Nombre del secreto en Key Vault que contiene la contraseña SQL."
  type        = string
  default     = "sigrid-password"
}

variable "default_query_timeout_seconds" {
  description = "Timeout por defecto para consultas SQL."
  type        = number
  default     = 30
}

variable "max_query_timeout_seconds" {
  description = "Timeout máximo permitido para consultas SQL."
  type        = number
  default     = 120
}

variable "default_max_rows" {
  description = "Número de filas por defecto que la función devuelve."
  type        = number
  default     = 200
}

variable "max_allowed_rows" {
  description = "Número máximo de filas permitido en una petición."
  type        = number
  default     = 1000
}

variable "max_inline_binary_bytes" {
  description = "Límite máximo de bytes inline que la API devolverá sin cortar."
  type        = number
  default     = 65536
}

variable "allowed_databases" {
  description = "Lista blanca de bases de datos que la función podrá consultar."
  type        = list(string)
  default     = ["master", "ruesma_rep", "ruesma"]
}

variable "allowed_query_prefixes" {
  description = "Prefijos SQL permitidos. Para esta API solo lectura, normalmente SELECT y WITH."
  type        = list(string)
  default     = ["SELECT", "WITH"]
}

variable "function_runtime_name" {
  description = "Runtime de Azure Functions Flex Consumption."
  type        = string
  default     = "python"
}

variable "function_runtime_version" {
  description = "Versión del runtime de Azure Functions Flex Consumption."
  type        = string
  default     = "3.12"
}

variable "maximum_instance_count" {
  description = "Máximo de instancias del plan Flex Consumption."
  type        = number
  default     = 20
}

variable "instance_memory_in_mb" {
  description = "Memoria por instancia en MB."
  type        = number
  default     = 2048
}

variable "grant_current_principal_key_vault_secrets_officer" {
  description = "Si true, asigna al principal autenticado actualmente el rol Key Vault Secrets Officer para poder cargar el secreto manualmente."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags a aplicar a los recursos."
  type        = map(string)
  default = {
    acens-support            = "UNMANAGED"
    acens-backuppolicy       = "NOAPPLY"
    acens-shutdownpolicy     = "NOAPPLY"
    acens-patchpolicy        = "NOAPPLY"
    acens-customer           = "Construcciones Ruesma"
    acens-environment        = "DEV"
    acens-project            = "sigrid-api"
    acens-costcenter         = "NOAPPLY"
    acens-sla                = "NOAPPLY"
    acens-compliance         = "NOAPPLY"
    acens-retentionpolicy    = "NOAPPLY"
    acens-terraform          = "True"
    acens-responsable-iac    = "pgris"
    acens-responsable-so-app = "pgris"
  }
}
