# infrastructure/security/sql_query_guard.py
from __future__ import annotations

import re

from config.settings import Settings
from domain.models.sql_models import SqlReadRequest


class QueryValidationError(ValueError):
    pass


class SqlQueryGuard:
    _LEADING_COMMENT_RE = re.compile(
        r"^(?:\s|--[^\n]*\n|/\*.*?\*/)*",
        re.DOTALL,
    )
    _DANGEROUS_KEYWORDS = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "MERGE",
        "ALTER",
        "DROP",
        "TRUNCATE",
        "CREATE",
        "EXEC",
        "EXECUTE",
        "GRANT",
        "REVOKE",
        "DENY",
        "BACKUP",
        "RESTORE",
        "USE",
        "OPENROWSET",
        "OPENDATASOURCE",
        "BULK",
        "XP_CMDSHELL",
        "SP_",
    ]

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate(self, request: SqlReadRequest) -> None:
        database = request.database.strip()
        if database not in self._settings.allowed_databases:
            raise QueryValidationError(
                f"La base de datos '{database}' no está permitida. "
                f"Permitidas: {', '.join(self._settings.allowed_databases)}"
            )

        normalized_sql = self._normalize_sql(request.sql)
        prefix = self._first_keyword(normalized_sql)
        if prefix not in self._settings.allowed_query_prefixes:
            raise QueryValidationError(
                f"Solo se permiten consultas que comiencen por: "
                f"{', '.join(self._settings.allowed_query_prefixes)}"
            )

        if self._contains_multiple_statements(normalized_sql):
            raise QueryValidationError("Solo se permite una única sentencia SQL por petición.")

        upper_sql = normalized_sql.upper()
        for keyword in self._DANGEROUS_KEYWORDS:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, upper_sql):
                raise QueryValidationError(
                    f"La consulta contiene una palabra no permitida: {keyword}"
                )

        if (request.timeout_seconds or self._settings.default_query_timeout_seconds) > self._settings.max_query_timeout_seconds:
            raise QueryValidationError(
                f"timeout_seconds no puede superar {self._settings.max_query_timeout_seconds}."
            )

        if (request.max_rows or self._settings.default_max_rows) > self._settings.max_allowed_rows:
            raise QueryValidationError(
                f"max_rows no puede superar {self._settings.max_allowed_rows}."
            )

    def _normalize_sql(self, sql: str) -> str:
        stripped = sql.strip()
        stripped = self._LEADING_COMMENT_RE.sub("", stripped)
        stripped = stripped.lstrip(";").strip()
        return stripped

    @staticmethod
    def _contains_multiple_statements(sql: str) -> bool:
        if ";" not in sql:
            return False
        return sql.rstrip().count(";") > (1 if sql.rstrip().endswith(";") else 0)

    @staticmethod
    def _first_keyword(sql: str) -> str:
        match = re.match(r"^([A-Za-z_]+)", sql)
        return match.group(1).upper() if match else ""
