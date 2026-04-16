# domain/models/sql_models.py
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class SqlReadRequest(BaseModel):
    database: str = Field(..., min_length=1)
    sql: str = Field(..., min_length=1)
    parameters: list[Any] = Field(default_factory=list)
    timeout_seconds: int | None = Field(default=None, ge=1, le=600)
    max_rows: int | None = Field(default=None, ge=1, le=10000)

    @field_validator("database")
    @classmethod
    def _normalize_database(cls, value: str) -> str:
        return value.strip()

    @field_validator("sql")
    @classmethod
    def _normalize_sql(cls, value: str) -> str:
        return value.strip()


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
