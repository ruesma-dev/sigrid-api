# function_app.py
from __future__ import annotations

import logging
from functools import lru_cache

import azure.functions as func
from pydantic import ValidationError

from application.use_cases.execute_sql_query_use_case import ExecuteSqlQueryUseCase
from application.use_cases.read_document_use_case import ReadDocumentUseCase
from config.settings import Settings, get_settings
from domain.models.sql_models import DocumentReadRequest, SqlReadRequest
from infrastructure.repositories.sql_server_repository import SqlServerRepository
from infrastructure.security.identifier_guard import IdentifierValidationError
from infrastructure.security.sql_query_guard import QueryValidationError
from interface_adapters.http.http_response_factory import (
    binary_file_response,
    error_response,
    json_response,
)

logger = logging.getLogger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@lru_cache(maxsize=1)
def build_dependencies() -> tuple[Settings, SqlServerRepository, ExecuteSqlQueryUseCase, ReadDocumentUseCase]:
    settings = get_settings()
    repository = SqlServerRepository(settings)
    sql_use_case = ExecuteSqlQueryUseCase(repository, settings)
    document_use_case = ReadDocumentUseCase(repository)
    return settings, repository, sql_use_case, document_use_case


@app.route(route="sql/read", methods=["POST"])
def sql_read(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, _, sql_use_case, _ = build_dependencies()
        body = req.get_json()
        request_model = SqlReadRequest.model_validate(body)
        response_model = sql_use_case.run(request_model)
        return json_response(response_model)
    except QueryValidationError as exc:
        logger.warning("QueryValidationError en sql/read: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except ValidationError as exc:
        logger.warning("ValidationError en sql/read: %s", exc)
        return error_response(
            "Solicitud inválida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en sql/read: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en sql/read")
        return error_response(
            "Error interno ejecutando sql/read.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )

@app.route(route="documents/read", methods=["POST"])
def documents_read(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, _, _, document_use_case = build_dependencies()
        body = req.get_json()
        request_model = DocumentReadRequest.model_validate(body)
        response_model = document_use_case.run(request_model)
        return binary_file_response(
            content=response_model.content,
            content_type=response_model.content_type,
            file_name=response_model.file_name,
            disposition=request_model.disposition,
        )
    except IdentifierValidationError as exc:
        logger.warning("IdentifierValidationError en documents/read: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except ValidationError as exc:
        logger.warning("ValidationError en documents/read: %s", exc)
        return error_response(
            "Solicitud inválida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en documents/read: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en documents/read")
        return error_response(
            "Error interno ejecutando documents/read.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )

@app.route(route="diagnostics/tcp", methods=["GET"])
def diagnostics_tcp(req: func.HttpRequest) -> func.HttpResponse:
    import socket

    host = req.params.get("host") or "192.168.14.238"
    port = int(req.params.get("port") or "49782")
    timeout = float(req.params.get("timeout") or "5")

    try:
        with socket.create_connection((host, port), timeout=timeout):
            return func.HttpResponse(
                body=f'{{"ok": true, "host": "{host}", "port": {port}}}',
                status_code=200,
                mimetype="application/json",
            )
    except Exception as exc:
        return func.HttpResponse(
            body=f'{{"ok": false, "host": "{host}", "port": {port}, "error": "{str(exc)}"}}',
            status_code=500,
            mimetype="application/json",
        )