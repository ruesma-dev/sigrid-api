# application/use_cases/execute_sql_query_use_case.py
from __future__ import annotations

from config.settings import Settings
from domain.models.sql_models import SqlReadRequest, SqlReadResponse
from domain.ports.sql_repository import SqlRepository
from infrastructure.security.sql_query_guard import SqlQueryGuard
from infrastructure.serialization.json_encoder import JsonValueSerializer


class ExecuteSqlQueryUseCase:
    def __init__(self, repository: SqlRepository, settings: Settings) -> None:
        self._repository = repository
        self._query_guard = SqlQueryGuard(settings)
        self._serializer = JsonValueSerializer(settings)

    def run(self, request: SqlReadRequest) -> SqlReadResponse:
        self._query_guard.validate(request)
        columns, rows, truncated = self._repository.execute_read_query(request)
        serialized_rows = [
            [self._serializer.serialize(cell) for cell in row]
            for row in rows
        ]
        return SqlReadResponse(
            database=request.database,
            columns=columns,
            rows=serialized_rows,
            row_count=len(serialized_rows),
            truncated=truncated,
        )
