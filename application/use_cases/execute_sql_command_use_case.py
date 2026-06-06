# application/use_cases/execute_sql_command_use_case.py
from __future__ import annotations

from config.settings import Settings
from domain.models.sql_models import (
    SqlWriteRequest,
    SqlWriteResponse,
    SqlWriteStatementResult,
)
from domain.ports.sql_repository import SqlRepository
from infrastructure.security.sql_write_guard import SqlWriteGuard


class ExecuteSqlCommandUseCase:
    def __init__(self, repository: SqlRepository, settings: Settings) -> None:
        self._repository = repository
        self._write_guard = SqlWriteGuard(settings)

    def run(self, request: SqlWriteRequest) -> SqlWriteResponse:
        operations = self._write_guard.validate(request)
        affected_list = self._repository.execute_write_command(request)

        results = [
            SqlWriteStatementResult(operation=operation, affected_rows=affected)
            for operation, affected in zip(operations, affected_list)
        ]
        total_affected = sum(affected for affected in affected_list if affected and affected > 0)

        return SqlWriteResponse(
            database=request.database,
            statements=len(results),
            results=results,
            total_affected_rows=total_affected,
            committed=True,
        )
