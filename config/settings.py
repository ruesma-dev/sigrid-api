# config/settings.py
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    sql_driver: str = Field(..., alias="SQL_DRIVER")
    sql_server_host: str = Field(..., alias="SQL_SERVER_HOST")
    sql_server_port: int = Field(..., alias="SQL_SERVER_PORT")

    # --- Credenciales de LECTURA (ro_user) ---
    sql_server_username: str = Field(..., alias="SQL_SERVER_USERNAME")
    sql_server_password: str = Field(..., alias="SQL_SERVER_PASSWORD")

    # --- Credenciales de ESCRITURA (user_rw); opcionales ---
    sql_server_write_username: str | None = Field(default=None, alias="SQL_SERVER_WRITE_USERNAME")
    sql_server_write_password: str | None = Field(default=None, alias="SQL_SERVER_WRITE_PASSWORD")

    default_query_timeout_seconds: int = Field(30, alias="DEFAULT_QUERY_TIMEOUT_SECONDS")
    max_query_timeout_seconds: int = Field(120, alias="MAX_QUERY_TIMEOUT_SECONDS")

    default_max_rows: int = Field(200, alias="DEFAULT_MAX_ROWS")
    max_allowed_rows: int = Field(1000, alias="MAX_ALLOWED_ROWS")
    max_inline_binary_bytes: int = Field(65536, alias="MAX_INLINE_BINARY_BYTES")

    allowed_databases: list[str] = Field(default_factory=list, alias="ALLOWED_DATABASES")
    allowed_query_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_QUERY_PREFIXES")

    # --- Escritura generica (endpoint sql/write) ---
    allowed_write_databases: list[str] = Field(default_factory=list, alias="ALLOWED_WRITE_DATABASES")
    allowed_write_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_WRITE_PREFIXES")

    default_write_timeout_seconds: int = Field(30, alias="DEFAULT_WRITE_TIMEOUT_SECONDS")
    max_write_timeout_seconds: int = Field(120, alias="MAX_WRITE_TIMEOUT_SECONDS")

    default_max_affected_rows: int = Field(200, alias="DEFAULT_MAX_AFFECTED_ROWS")
    max_affected_rows: int = Field(1000, alias="MAX_AFFECTED_ROWS")

    # --- Batch de escritura ---
    # Numero maximo de sentencias por peticion sql/write y uso de
    # fast_executemany de pyodbc para los parameter_sets (executemany).
    max_statements_per_batch: int = Field(20, alias="MAX_STATEMENTS_PER_BATCH")
    use_fast_executemany: bool = Field(True, alias="USE_FAST_EXECUTEMANY")

    require_where_on_update_delete: bool = Field(True, alias="REQUIRE_WHERE_ON_UPDATE_DELETE")

    # --- Alta de DOMINIO en Sigrid (lineas de contrato, etc.) ---
    sigrid_domain_write_enabled: bool = Field(False, alias="SIGRID_DOMAIN_WRITE_ENABLED")
    applock_timeout_ms: int = Field(10000, alias="APPLOCK_TIMEOUT_MS")
    domain_write_max_retries: int = Field(3, alias="DOMAIN_WRITE_MAX_RETRIES")

    # Empleado (empide) por defecto en la cabecera de un albaran creado por la
    # API; sobreescribible por peticion. 2425207 = GRIS MARTINEZ, PABLO.
    sigrid_albaran_empide: int = Field(2425207, alias="SIGRID_ALBARAN_EMPIDE")

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator(
        "allowed_databases",
        "allowed_query_prefixes",
        "allowed_write_databases",
        "allowed_write_prefixes",
        mode="before",
    )
    @classmethod
    def parse_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass

            return [item.strip() for item in raw.split(",") if item.strip()]

        raise ValueError(f"Formato no soportado para lista: {value!r}")

    @property
    def write_enabled(self) -> bool:
        return bool(
            self.sql_server_write_username
            and self.sql_server_write_password
            and self.allowed_write_prefixes
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()