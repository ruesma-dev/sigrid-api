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
    sql_server_username: str = Field(..., alias="SQL_SERVER_USERNAME")
    sql_server_password: str = Field(..., alias="SQL_SERVER_PASSWORD")

    default_query_timeout_seconds: int = Field(30, alias="DEFAULT_QUERY_TIMEOUT_SECONDS")
    max_query_timeout_seconds: int = Field(120, alias="MAX_QUERY_TIMEOUT_SECONDS")

    default_max_rows: int = Field(200, alias="DEFAULT_MAX_ROWS")
    max_allowed_rows: int = Field(1000, alias="MAX_ALLOWED_ROWS")
    max_inline_binary_bytes: int = Field(65536, alias="MAX_INLINE_BINARY_BYTES")

    allowed_databases: list[str] = Field(default_factory=list, alias="ALLOWED_DATABASES")
    allowed_query_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_QUERY_PREFIXES")

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("allowed_databases", "allowed_query_prefixes", mode="before")
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()