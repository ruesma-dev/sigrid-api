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

    # --- Credenciales de LECTURA (usuario read-only: ro_user) ---
    sql_server_username: str = Field(..., alias="SQL_SERVER_USERNAME")
    sql_server_password: str = Field(..., alias="SQL_SERVER_PASSWORD")

    # --- Credenciales de ESCRITURA (usuario separado: rw_user) ---
    # Opcionales a propósito: si no se configuran, la escritura queda
    # DESACTIVADA y el endpoint sql/write devuelve un error explícito.
    # Nunca reutilizar el usuario de lectura para escribir.
    sql_server_write_username: str | None = Field(default=None, alias="SQL_SERVER_WRITE_USERNAME")
    sql_server_write_password: str | None = Field(default=None, alias="SQL_SERVER_WRITE_PASSWORD")

    default_query_timeout_seconds: int = Field(30, alias="DEFAULT_QUERY_TIMEOUT_SECONDS")
    max_query_timeout_seconds: int = Field(120, alias="MAX_QUERY_TIMEOUT_SECONDS")

    default_max_rows: int = Field(200, alias="DEFAULT_MAX_ROWS")
    max_allowed_rows: int = Field(1000, alias="MAX_ALLOWED_ROWS")
    max_inline_binary_bytes: int = Field(65536, alias="MAX_INLINE_BINARY_BYTES")

    allowed_databases: list[str] = Field(default_factory=list, alias="ALLOWED_DATABASES")
    allowed_query_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_QUERY_PREFIXES")

    # --- Parámetros operacionales de ESCRITURA ---
    # allowed_write_prefixes vacío => escritura DESACTIVADA aunque haya credenciales.
    allowed_write_databases: list[str] = Field(default_factory=list, alias="ALLOWED_WRITE_DATABASES")
    allowed_write_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_WRITE_PREFIXES")

    default_write_timeout_seconds: int = Field(30, alias="DEFAULT_WRITE_TIMEOUT_SECONDS")
    max_write_timeout_seconds: int = Field(120, alias="MAX_WRITE_TIMEOUT_SECONDS")

    # Tope de seguridad: si el batch afectaría a más filas (acumuladas) que esto,
    # se hace ROLLBACK y no se aplica ningún cambio.
    default_max_affected_rows: int = Field(200, alias="DEFAULT_MAX_AFFECTED_ROWS")
    max_affected_rows: int = Field(1000, alias="MAX_AFFECTED_ROWS")

    # Nº máximo de sentencias en un mismo batch.
    max_statements_per_batch: int = Field(50, alias="MAX_STATEMENTS_PER_BATCH")

    # Acelera INSERT/UPDATE masivos cuando se usan parameter_sets (executemany).
    use_fast_executemany: bool = Field(True, alias="USE_FAST_EXECUTEMANY")

    # Exigir WHERE en UPDATE/DELETE (anti-borrado/actualización masiva accidental).
    require_where_on_update_delete: bool = Field(True, alias="REQUIRE_WHERE_ON_UPDATE_DELETE")

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
        """La escritura solo está activa si hay credenciales Y prefijos permitidos."""
        return bool(
            self.sql_server_write_username
            and self.sql_server_write_password
            and self.allowed_write_prefixes
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
