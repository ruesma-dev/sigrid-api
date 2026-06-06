# domain/models/sql_models.py
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_core import PydanticCustomError

from config.settings import get_settings


class SqlReadRequest(BaseModel):
    database: str = Field(..., min_length=1)
    sql: str = Field(..., min_length=1)
    parameters: list[Any] = Field(default_factory=list)
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
        settings = get_settings()
        if value is None:
            return settings.default_max_rows
        if value > settings.max_allowed_rows:
            raise PydanticCustomError(
                "less_than_equal",
                "Input should be less than or equal to {le}",
                {"le": settings.max_allowed_rows, "input": value},
            )
        return value

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout_seconds(cls, value: int | None) -> int:
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


class SqlWriteStatement(BaseModel):
    """
    Una sentencia de escritura dentro de un batch.

    Dos modos de parametrización:
      - parameters: una única ejecución (cursor.execute).
      - parameter_sets: ejecución masiva (cursor.executemany) con
        fast_executemany; ideal para insertar/actualizar muchas filas rápido.
    """

    sql: str = Field(..., min_length=1)
    parameters: list[Any] = Field(default_factory=list)
    parameter_sets: list[list[Any]] | None = Field(default=None)

    @field_validator("sql")
    @classmethod
    def _normalize_sql(cls, value: str) -> str:
        return value.strip()


class SqlWriteRequest(BaseModel):
    """
    Petición de escritura. Soporta:
      - Una sola sentencia (atajo): `sql` + `parameters`.
      - Varias sentencias (posiblemente a tablas distintas): `statements`.

    Todo el batch se ejecuta en UNA conexión y UNA transacción (atómico):
    o se aplican todas las sentencias o ninguna (rollback).
    """

    database: str = Field(..., min_length=1)
    statements: list[SqlWriteStatement] = Field(default_factory=list)

    # Atajo single-statement (retrocompatible).
    sql: str | None = Field(default=None)
    parameters: list[Any] = Field(default_factory=list)

    timeout_seconds: int | None = Field(default=None, ge=1, validate_default=True)
    # Tope de filas afectadas ACUMULADAS en el batch; si se supera → ROLLBACK.
    max_affected_rows: int | None = Field(default=None, ge=1, validate_default=True)

    @field_validator("database")
    @classmethod
    def _normalize_database(cls, value: str) -> str:
        return value.strip()

    @field_validator("timeout_seconds")
    @classmethod
    def _validate_timeout_seconds(cls, value: int | None) -> int:
        settings = get_settings()
        if value is None:
            return settings.default_write_timeout_seconds
        if value > settings.max_write_timeout_seconds:
            raise PydanticCustomError(
                "less_than_equal",
                "Input should be less than or equal to {le}",
                {"le": settings.max_write_timeout_seconds, "input": value},
            )
        return value

    @field_validator("max_affected_rows")
    @classmethod
    def _validate_max_affected_rows(cls, value: int | None) -> int:
        settings = get_settings()
        if value is None:
            return settings.default_max_affected_rows
        if value > settings.max_affected_rows:
            raise PydanticCustomError(
                "less_than_equal",
                "Input should be less than or equal to {le}",
                {"le": settings.max_affected_rows, "input": value},
            )
        return value

    @model_validator(mode="after")
    def _fold_single_into_statements(self) -> "SqlWriteRequest":
        """Normaliza el atajo single-statement a la lista `statements`."""
        has_single = bool(self.sql and self.sql.strip())
        has_batch = bool(self.statements)

        if has_single and has_batch:
            raise ValueError("Usa 'sql' (atajo) o 'statements' (batch), no ambos.")
        if not has_single and not has_batch:
            raise ValueError("Debes indicar 'sql' o al menos una sentencia en 'statements'.")

        if has_single:
            self.statements = [
                SqlWriteStatement(sql=self.sql.strip(), parameters=self.parameters)
            ]
            self.sql = None
            self.parameters = []

        return self


class SqlWriteStatementResult(BaseModel):
    operation: str
    affected_rows: int


class SqlWriteResponse(BaseModel):
    ok: bool = True
    database: str
    statements: int
    results: list[SqlWriteStatementResult]
    total_affected_rows: int
    committed: bool


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
