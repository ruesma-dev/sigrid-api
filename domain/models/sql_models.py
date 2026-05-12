# domain/models/sql_models.py
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_core import PydanticCustomError

from config.settings import get_settings


class SqlReadRequest(BaseModel):
    database: str = Field(..., min_length=1)
    sql: str = Field(..., min_length=1)
    parameters: list[Any] = Field(default_factory=list)
    # validate_default=True hace que el validator se ejecute también cuando el
    # cliente NO envía el campo, permitiendo resolver el default desde settings.
    timeout_seconds: int | None = Field(default=None, ge=1, validate_default=True)
    max_rows: int | None = Field(default=None, ge=1, validate_default=True)

    @field_validator("database")
    @classmethod
    def _normalize_database(cls, value: str) -> str:
        return value.strip()

    @field_validator("sql")
    @classmethod
    def _normalize_sql(cls, value: str) -> str:
        return value.strip()

    @field_validator("max_rows")
    @classmethod
    def _validate_max_rows(cls, value: int | None) -> int:
        """
        Aplica el cap de filas y el default leyendo de settings.

        Reemplaza al antiguo `Field(le=10000)` hardcoded para que el límite
        operacional viva en una única fuente de verdad: la env var
        MAX_ALLOWED_ROWS (vía config/settings.py).

        - Si el cliente no envía max_rows → usa settings.default_max_rows.
        - Si excede el cap → error 400 con estructura compatible con clientes
          que ya parsean PydanticV2 less_than_equal (mantiene ctx.le e input).
        """
        settings = get_settings()
        if value is None:
            return settings.default_max_rows
        if value > settings.max_allowed_rows:
            # Mantenemos el "type=less_than_equal" para compatibilidad con
            # clientes existentes que parsean este error específico.
            raise PydanticCustomError(
                "less_than_equal",
                "Input should be less than or equal to {le}",
                {"le": settings.max_allowed_rows, "input": value},
            )
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout_seconds(cls, value: int | None) -> int:
        """
        Aplica el cap de timeout y el default leyendo de settings.

        Reemplaza al antiguo `Field(le=600)` hardcoded. El cap real viene de
        la env var MAX_QUERY_TIMEOUT_SECONDS y el default de
        DEFAULT_QUERY_TIMEOUT_SECONDS.
        """
        settings = get_settings()
        if value is None:
            return settings.default_query_timeout_seconds
        if value > settings.max_query_timeout_seconds:
            raise PydanticCustomError(
                "less_than_equal",
                "Input should be less than or equal to {le}",
                {"le": settings.max_query_timeout_seconds, "input": value},
            )
        return value


class SqlReadResponse(BaseModel):
    ok: bool = True
    database: str
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool


class DocumentReadRequest(BaseModel):
    database: str = Field(..., min_length=1)
    schema: str = Field("dbo", min_length=1)
    table: str = Field(..., min_length=1)
    id_column: str = Field(..., min_length=1)
    id_value: Any
    blob_column: str = Field(..., min_length=1)
    filename_columns: list[str] = Field(default_factory=lambda: ["nomori", "nom"])
    disposition: Literal["attachment", "inline"] = "attachment"

    @field_validator("database", "schema", "table", "id_column", "blob_column", mode="before")
    @classmethod
    def _strip_identifier(cls, value: object) -> str:
        return str(value).strip()

    @field_validator("filename_columns", mode="before")
    @classmethod
    def _normalize_filename_columns(cls, value: object) -> list[str]:
        if value is None:
            return ["nomori", "nom"]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()]


class DocumentReadResponse(BaseModel):
    file_name: str
    content_type: str
    size_bytes: int
    content: bytes
