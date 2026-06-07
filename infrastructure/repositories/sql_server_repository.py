# infrastructure/repositories/sql_server_repository.py
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Iterator

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
    # Conexion
    # ------------------------------------------------------------------ #
    @contextmanager
    def _connect(
        self,
        *,
        database: str,
        timeout_seconds: int,
        username: str,
        password: str,
        autocommit: bool = True,
    ) -> Iterator[pyodbc.Connection]:
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
        connection = pyodbc.connect(connection_string, timeout=timeout_seconds, autocommit=autocommit)
        try:
            yield connection
        finally:
            connection.close()

    def _read_credentials(self) -> tuple[str, str]:
        return self._settings.sql_server_username, self._settings.sql_server_password

    def _write_credentials(self) -> tuple[str, str]:
        username = self._settings.sql_server_write_username
        password = self._settings.sql_server_write_password
        if not username or not password:
            raise ValueError(
                "Escritura no configurada: faltan SQL_SERVER_WRITE_USERNAME / "
                "SQL_SERVER_WRITE_PASSWORD."
            )
        return username, password

    # ------------------------------------------------------------------ #
    # Lectura generica
    # ------------------------------------------------------------------ #
    def execute_read_query(self, request: SqlReadRequest) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        timeout_seconds = request.timeout_seconds or self._settings.default_query_timeout_seconds
        max_rows = request.max_rows or self._settings.default_max_rows
        username, password = self._read_credentials()

        with self._connect(
            database=request.database,
            timeout_seconds=timeout_seconds,
            username=username,
            password=password,
            autocommit=True,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(request.sql, *request.parameters)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = cursor.fetchmany(max_rows + 1)

        truncated = len(rows) > max_rows
        if truncated:
            rows = rows[:max_rows]
        return columns, rows, truncated

    # ------------------------------------------------------------------ #
    # Escritura generica: BATCH transaccional.
    # Ejecuta todas las sentencias de request.statements en UNA conexion y
    # UNA transaccion (atomico). Devuelve una lista con las filas afectadas
    # por cada sentencia (en el mismo orden), tal y como espera el use case.
    # ------------------------------------------------------------------ #
    def execute_write_command(self, request: SqlWriteRequest) -> list[int]:
        timeout_seconds = request.timeout_seconds or self._settings.default_write_timeout_seconds
        cap = request.max_affected_rows or self._settings.default_max_affected_rows
        username, password = self._write_credentials()

        affected_list: list[int] = []
        running_total = 0

        # autocommit=False => control transaccional explicito sobre todo el batch.
        with self._connect(
            database=request.database,
            timeout_seconds=timeout_seconds,
            username=username,
            password=password,
            autocommit=False,
        ) as connection:
            cursor = connection.cursor()
            try:
                for statement in request.statements:
                    if statement.parameter_sets:
                        # Insercion/actualizacion masiva con executemany.
                        cursor.fast_executemany = bool(self._settings.use_fast_executemany)
                        cursor.executemany(statement.sql, statement.parameter_sets)
                    else:
                        cursor.execute(statement.sql, *statement.parameters)

                    affected = cursor.rowcount if cursor.rowcount is not None else -1
                    affected_list.append(affected)
                    # Con fast_executemany rowcount puede ser -1 (driver no lo reporta);
                    # solo acumulamos los positivos para el tope.
                    if affected and affected > 0:
                        running_total += affected

                if running_total > cap:
                    connection.rollback()
                    raise ValueError(
                        f"El batch afectaria a {running_total} filas y supera el maximo "
                        f"permitido ({cap}). Se hizo ROLLBACK y no se aplico ningun cambio."
                    )

                connection.commit()
                return affected_list
            except Exception:
                try:
                    connection.rollback()
                except Exception:
                    pass
                raise

    # ------------------------------------------------------------------ #
    # Lectura de filas completas / localizacion (alta de dominio)
    # ------------------------------------------------------------------ #
    def read_full_row(self, *, database: str, table: str, ide: int) -> tuple[list[str], tuple[Any, ...]] | None:
        safe_table = IdentifierGuard.validate_identifier(table, field_name="table")
        username, password = self._read_credentials()
        with self._connect(
            database=database,
            timeout_seconds=self._settings.default_query_timeout_seconds,
            username=username,
            password=password,
            autocommit=True,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM dbo.[{safe_table}] WHERE ide = ?", ide)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            row = cursor.fetchone()
        if row is None:
            return None
        return columns, tuple(row)

    def read_rows_by(
        self,
        *,
        database: str,
        table: str,
        where_column: str,
        where_value: Any,
        order_by: str | None = None,
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        safe_table = IdentifierGuard.validate_identifier(table, field_name="table")
        safe_col = IdentifierGuard.validate_identifier(where_column, field_name="where_column")
        order_clause = ""
        if order_by:
            parts = [
                f"[{IdentifierGuard.validate_identifier(piece.strip(), field_name='order_by')}]"
                for piece in order_by.split(",")
                if piece.strip()
            ]
            if parts:
                order_clause = " ORDER BY " + ", ".join(parts)
        username, password = self._read_credentials()
        with self._connect(
            database=database,
            timeout_seconds=self._settings.default_query_timeout_seconds,
            username=username,
            password=password,
            autocommit=True,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT * FROM dbo.[{safe_table}] WHERE [{safe_col}] = ?{order_clause}",
                where_value,
            )
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = [tuple(row) for row in cursor.fetchall()]
        return columns, rows

    def peek_next_ide(self, *, database: str, table: str) -> int:
        """Previsualiza el siguiente ide (MAX+1) SIN reservar. Solo para dry-run."""
        safe_table = IdentifierGuard.validate_identifier(table, field_name="table")
        username, password = self._read_credentials()
        with self._connect(
            database=database,
            timeout_seconds=self._settings.default_query_timeout_seconds,
            username=username,
            password=password,
            autocommit=True,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.[{safe_table}]")
            return int(cursor.fetchone()[0])

    def locate_contract(
        self,
        *,
        database: str,
        cod_contrato: str,
        cod_obra: str,
        cif_proveedor: str,
        contract_tip: int = 44,
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        """
        Localiza un contrato de compra (con.tip=44) por codigo de contrato +
        codigo de obra + CIF del proveedor. Devuelve (columnas, filas); el
        caso de uso valida que haya exactamente una.
        """
        username, password = self._read_credentials()
        sql = (
            "SELECT t.ide, t.obride, c.cod AS cod_contrato, t.entcif, t.entres, "
            "t.impbru, t.impnet, t.impdes, t.imprec, t.totbas, t.totiva, t.totdoc, t.tot, t.totpag "
            "FROM dbo.con c "
            "JOIN dbo.ctr t ON t.ide = c.ide "
            "JOIN dbo.con co ON co.ide = t.obride "
            "WHERE c.tip = ? AND c.cod = ? AND co.cod = ? AND t.entcif = ?"
        )
        with self._connect(
            database=database,
            timeout_seconds=self._settings.default_query_timeout_seconds,
            username=username,
            password=password,
            autocommit=True,
        ) as connection:
            cursor = connection.cursor()
            cursor.execute(sql, contract_tip, cod_contrato, cod_obra, cif_proveedor)
            columns = [column[0] for column in cursor.description] if cursor.description else []
            rows = [tuple(row) for row in cursor.fetchall()]
        return columns, rows

    # ------------------------------------------------------------------ #
    # Transaccion de alta de dominio (reserva de ide + inserts atomicos)
    # ------------------------------------------------------------------ #
    def run_in_write_transaction(
        self,
        *,
        database: str,
        timeout_seconds: int,
        applock_resources: list[str],
        applock_timeout_ms: int,
        max_retries: int,
        work: Callable[[pyodbc.Cursor], Any],
    ) -> Any:
        """
        Ejecuta `work(cursor)` en UNA transaccion (autocommit=False), tras tomar
        un bloqueo de aplicacion exclusivo por cada recurso (serializa nuestras
        propias altas). Si otra sesion gana la carrera y salta clave duplicada,
        hace ROLLBACK y reintenta hasta `max_retries` veces.
        """
        username, password = self._write_credentials()
        attempt = 0
        while True:
            attempt += 1
            with self._connect(
                database=database,
                timeout_seconds=timeout_seconds,
                username=username,
                password=password,
                autocommit=False,
            ) as connection:
                cursor = connection.cursor()
                try:
                    for resource in applock_resources:
                        cursor.execute(
                            "SET NOCOUNT ON; "
                            "DECLARE @r int; "
                            "EXEC @r = sp_getapplock @Resource = ?, @LockMode = 'Exclusive', "
                            "@LockOwner = 'Transaction', @LockTimeout = ?; "
                            "SELECT @r;",
                            resource,
                            applock_timeout_ms,
                        )
                        code = cursor.fetchone()[0]
                        if code is None or int(code) < 0:
                            raise ValueError(
                                f"No se pudo obtener el bloqueo de aplicacion para "
                                f"'{resource}' (codigo {code})."
                            )
                    result = work(cursor)
                    connection.commit()
                    return result
                except pyodbc.IntegrityError:
                    try:
                        connection.rollback()
                    except Exception:
                        pass
                    if attempt > max_retries:
                        raise
                    continue
                except Exception:
                    try:
                        connection.rollback()
                    except Exception:
                        pass
                    raise

    # ------------------------------------------------------------------ #
    # Documentos (BLOB)
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

        username, password = self._read_credentials()
        with self._connect(
            database=database,
            timeout_seconds=self._settings.default_query_timeout_seconds,
            username=username,
            password=password,
            autocommit=True,
        ) as connection:
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
                f"La columna {safe_blob_column} esta vacia para {safe_id_column}={id_value}."
            )

        candidates = [str(value).strip() for value in row[:-1] if value not in (None, "")]
        return RawDocumentRecord(
            file_name_candidates=candidates,
            content=bytes(file_content),
            id_value=id_value,
        )
