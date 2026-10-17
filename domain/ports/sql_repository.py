# domain/ports/sql_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.models.document_models import RawDocumentRecord
from domain.models.sql_models import SqlReadRequest, SqlWriteRequest


class SqlRepository(ABC):
    @abstractmethod
    def execute_read_query(self, request: SqlReadRequest) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        raise NotImplementedError

    @abstractmethod
    def execute_write_command(self, request: SqlWriteRequest) -> list[int]:
        """Ejecuta el batch de escritura en UNA transacción y devuelve la lista
        de filas afectadas por cada sentencia (en orden). Hace commit si todo
        va bien; rollback ante cualquier error o si se supera el tope de filas."""
        raise NotImplementedError

    @abstractmethod
    def read_document(
        self,
        *,
        database: str,
        schema: str,
        table: str,
        key: dict[str, Any],
        blob_column: str,
        filename_columns: list[str],
        key_field_name: str = "key",
    ) -> RawDocumentRecord:
        """Lee UNA fila localizada por `key` (columnas unidas por AND, en orden).

        `key_field_name` es el campo que nombra el error de un nombre de `key` no
        valido ("id_column" si la peticion llego por id_column, F-010 R12).

        Lanza IdentifierValidationError (nombre no valido), ValueError (ninguna
        fila, o BLOB NULL) y DocumentoAmbiguoError (mas de una fila).
        """
        raise NotImplementedError
