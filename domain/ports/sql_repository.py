# domain/ports/sql_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from domain.models.document_models import RawDocumentRecord
from domain.models.sql_models import SqlReadRequest


class SqlRepository(ABC):
    @abstractmethod
    def execute_read_query(self, request: SqlReadRequest) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError
