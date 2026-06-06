# infrastructure/security/sql_write_guard.py
from __future__ import annotations

import re

from config.settings import Settings
from domain.models.sql_models import SqlWriteRequest


class WriteValidationError(ValueError):
    pass


class SqlWriteGuard:
    """
    Guard específico para sentencias de escritura.

    Filosofía: lista blanca estricta. Solo se permite lo que esté en
    ALLOWED_WRITE_PREFIXES (por defecto vacío => escritura desactivada).
    Todo lo que huela a DDL o administración sigue bloqueado, incluso en el
    camino de escritura. Valida cada sentencia del batch por separado.
    """

    _LEADING_COMMENT_RE = re.compile(
        r"^(?:\s|--[^\n]*\n|/\*.*?\*/)*",
        re.DOTALL,
    )

    _ALWAYS_FORBIDDEN = [
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
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
        "SHUTDOWN",
        "RECONFIGURE",
        "EXEC",
        "EXECUTE",
        "MERGE",
    ]

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate(self, request: SqlWriteRequest) -> list[str]:
        """Valida el batch completo y devuelve la operación de cada sentencia."""
        if not self._settings.write_enabled:
            raise WriteValidationError(
                "La escritura está desactivada. Configura el usuario rw_user "
                "(SQL_SERVER_WRITE_USERNAME / SQL_SERVER_WRITE_PASSWORD) y "
                "ALLOWED_WRITE_PREFIXES para habilitarla."
            )

        database = request.database.strip()
        if database not in self._settings.allowed_write_databases:
            raise WriteValidationError(
                f"La base de datos '{database}' no está permitida para escritura. "
                f"Permitidas: {', '.join(self._settings.allowed_write_databases) or '(ninguna)'}"
            )

        if not request.statements:
            raise WriteValidationError("El batch no contiene ninguna sentencia.")

        if len(request.statements) > self._settings.max_statements_per_batch:
            raise WriteValidationError(
                f"El batch tiene {len(request.statements)} sentencias y supera el "
                f"máximo permitido ({self._settings.max_statements_per_batch})."
            )

        operations: list[str] = []
        for index, statement in enumerate(request.statements):
            try:
                operations.append(self._validate_statement(statement.sql))
            except WriteValidationError as exc:
                raise WriteValidationError(f"Sentencia #{index + 1}: {exc}") from exc

        if (request.timeout_seconds or self._settings.default_write_timeout_seconds) > self._settings.max_write_timeout_seconds:
            raise WriteValidationError(
                f"timeout_seconds no puede superar {self._settings.max_write_timeout_seconds}."
            )

        return operations

    def _validate_statement(self, sql: str) -> str:
        normalized_sql = self._normalize_sql(sql)
        operation = self._first_keyword(normalized_sql)

        allowed = {p.upper() for p in self._settings.allowed_write_prefixes}
        if operation not in allowed:
            raise WriteValidationError(
                f"solo se permiten sentencias que comiencen por "
                f"{', '.join(sorted(allowed)) or '(ninguna)'}"
            )

        if self._contains_multiple_statements(normalized_sql):
            raise WriteValidationError("solo se permite una única sentencia SQL por elemento.")

        forbidden = [kw for kw in self._ALWAYS_FORBIDDEN if kw not in allowed]
        upper_sql = normalized_sql.upper()
        for keyword in forbidden:
            pattern = rf"\b{re.escape(keyword)}\b"
            if re.search(pattern, upper_sql):
                raise WriteValidationError(f"contiene una palabra no permitida: {keyword}")

        if self._settings.require_where_on_update_delete and operation in ("UPDATE", "DELETE"):
            if not re.search(r"\bWHERE\b", upper_sql):
                raise WriteValidationError(
                    f"{operation} sin cláusula WHERE no está permitido. Añade un WHERE "
                    "explícito (o desactiva REQUIRE_WHERE_ON_UPDATE_DELETE bajo tu responsabilidad)."
                )

        return operation

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
