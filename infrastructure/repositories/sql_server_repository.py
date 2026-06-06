# infrastructure/repositories/sql_server_repository.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import pyodbc

from config.settings import Settings
from domain.models.document_models import RawDocumentRecord
from domain.models.sql_models import SqlReadRequest, SqlWriteRequest
from domain.ports.sql_repository import SqlRepository
from infrastructure.security.identifier_guard import IdentifierGuard


class SqlServerRepository(SqlRepository):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    # ------------------------------------------------------------------ #
    # Conexión de LECTURA (ro_user) — SIN CAMBIOS respecto al original
    # ------------------------------------------------------------------ #
    @contextmanager
    def _connect(self, *, database: str, timeout_seconds: int) -> Iterator[pyodbc.Connection]:
        password = self._settings.sql_server_password.replace("}", "}}")
        connection_string = (
            f"DRIVER={{{self._settings.sql_driver}}};"
            f"SERVER=tcp:{self._settings.sql_server_host},{self._settings.sql_server_port};"
            f"DATABASE={database};"
            f"UID={self._settings.sql_server_username};"
            f"PWD={{{password}}};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        connection = pyodbc.connect(connection_string, timeout=timeout_seconds)
        try:
            yield connection
        finally:
            connection.close()

    # ------------------------------------------------------------------ #
    # Conexión de ESCRITURA (rw_user) — autocommit=False (transaccional)
    # ------------------------------------------------------------------ #
    @contextmanager
    def _connect_write(self, *, database: str, timeout_seconds: int) -> Iterator[pyodbc.Connection]:
        username = self._settings.sql_server_write_username
        password = self._settings.sql_server_write_password
        if not username or not password:
            raise ValueError(
                "Escritura no configurada: faltan SQL_SERVER_WRITE_USERNAME / "
                "SQL_SERVER_WRITE_PASSWORD."
            )
        escaped_password = password.replace("}", "}}")
        connection_string = (
            f"DRIVER={{{self._settings.sql_driver}}};"
            f"SERVER=tcp:{self._settings.sql_server_host},{self._settings.sql_server_port};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={{{escaped_password}}};"
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )
        connection = pyodbc.connect(connection_string, timeout=timeout_seconds, autocommit=False)
        try:
            yield connection
        finally:
            connection.close()

    # ------------------------------------------------------------------ #
    # Lectura — SIN CAMBIOS respecto al original
    # ------------------------------------------------------------------ #
    def execute_read_query(self, request: SqlReadRequest) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        timeout_seconds = request.timeout_seconds or self._settings.default_query_timeout_seconds
        max_rows = request.max_rows or self._settings.default_max_rows

        with self._connect(database=request.database, timeout_seconds=timeout_seconds) as connection:
            cursor = connection.cursor()
            cursor.execute(request.sql, *request.parameters)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(max_rows + 1)

        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]
        return columns, rows, truncated

    # ------------------------------------------------------------------ #
    # Escritura — batch atómico (una conexión, una transacción, un commit)
    # ------------------------------------------------------------------ #
    def execute_write_command(self, request: SqlWriteRequest) -> list[int]:
        timeout_seconds = request.timeout_seconds or self._settings.default_write_timeout_seconds
        cap = request.max_affected_rows or self._settings.default_max_affected_rows

        affected_per_statement: list[int] = []
        running_total = 0

        with self._connect_write(database=request.database, timeout_seconds=timeout_seconds) as connection:
            cursor = connection.cursor()
            try:
                for statement in request.statements:
                    if statement.parameter_sets:
                        if self._settings.use_fast_executemany:
                            cursor.fast_executemany = True
                        cursor.executemany(statement.sql, statement.parameter_sets)
                        affected = cursor.rowcount
                        if affected is None or affected < 0:
                            affected = len(statement.parameter_sets)
                    else:
                        cursor.execute(statement.sql, *statement.parameters)
                        affected = cursor.rowcount if cursor.rowcount is not None else -1

                    affected_per_statement.append(affected)
                    if affected > 0:
                        running_total += affected

                    if running_total > cap:
                        connection.rollback()
                        raise ValueError(
                            f"El batch afectaría a {running_total} filas y supera el máximo "
                            f"permitido ({cap}). Se hizo ROLLBACK y no se aplicó ningún cambio."
                        )

                connection.commit()
                return affected_per_statement
            except Exception:
                try:
                    connection.rollback()
                except Exception:
                    pass
                raise

    # ------------------------------------------------------------------ #
    # Documentos (BLOB) — SIN CAMBIOS respecto al original
    # ------------------------------------------------------------------ #
    def read_document(
        self,
        *,
        database: str,
        schema: str,
        table: str,
        id_column: str,
        id_value: Any,
        blob_column: str,
        filename_columns: list[str],
    ) -> RawDocumentRecord:
        safe_schema = IdentifierGuard.validate_identifier(schema, field_name="schema")
        safe_table = IdentifierGuard.validate_identifier(table, field_name="table")
        safe_id_column = IdentifierGuard.validate_identifier(id_column, field_name="id_column")
        safe_blob_column = IdentifierGuard.validate_identifier(blob_column, field_name="blob_column")
        safe_filename_columns = [
            IdentifierGuard.validate_identifier(column, field_name="filename_columns")
            for column in filename_columns
        ]

        projected_filename_columns = ", ".join(f"[{column}]" for column in safe_filename_columns)
        query = f"""
            SELECT TOP (1)
                {projected_filename_columns},
                CAST([{safe_blob_column}] AS varbinary(max)) AS file_content
            FROM [{safe_schema}].[{safe_table}]
            WHERE [{safe_id_column}] = ?
        """

        with self._connect(database=database, timeout_seconds=self._settings.default_query_timeout_seconds) as connection:
            cursor = connection.cursor()
            cursor.execute(query, id_value)
            row = cursor.fetchone()

        if row is None:
            raise ValueError(
                f"No existe ninguna fila en [{safe_schema}].[{safe_table}] con {safe_id_column}={id_value}."
            )

        file_content = row[-1]
        if file_content is None:
            raise ValueError(
                f"La columna {safe_blob_column} está vacía para {safe_id_column}={id_value}."
            )

        candidates = [str(value).strip() for value in row[:-1] if value not in (None, "")]
        return RawDocumentRecord(
            file_name_candidates=candidates,
            content=bytes(file_content),
            id_value=id_value,
        )
