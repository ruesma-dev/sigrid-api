# function_app.py
from __future__ import annotations

import logging
from functools import lru_cache

import azure.functions as func
import pyodbc
from pydantic import ValidationError

from application.use_cases.add_contract_lines_use_case import AddContractLinesUseCase
from application.use_cases.attach_concepto_grafico_use_case import (
    AttachConceptoGraficoUseCase,
)
from application.use_cases.create_direct_albaran_use_case import CreateDirectAlbaranUseCase
from application.use_cases.create_purchase_albaran_use_case import CreatePurchaseAlbaranUseCase
from application.use_cases.execute_sql_command_use_case import ExecuteSqlCommandUseCase
from application.use_cases.execute_sql_query_use_case import ExecuteSqlQueryUseCase
from application.use_cases.read_document_use_case import ReadDocumentUseCase
from config.settings import Settings, get_settings
from domain.models.albaran_directo_models import AddDirectAlbaranRequest
from domain.models.albaran_domain_models import AddPurchaseAlbaranRequest
from domain.models.concepto_grafico_models import (
    AttachConceptoGraficoRequest,
    ConceptoGraficoError,
)
from domain.models.sigrid_domain_models import AddContractLinesRequest
from domain.models.sql_models import DocumentReadRequest, SqlReadRequest, SqlWriteRequest
from infrastructure.repositories.sql_server_repository import SqlServerRepository
from infrastructure.security.identifier_guard import IdentifierValidationError
from infrastructure.security.sql_query_guard import QueryValidationError
from infrastructure.security.sql_write_guard import WriteValidationError
from interface_adapters.http.http_response_factory import (
    binary_file_response,
    error_response,
    json_response,
)

logger = logging.getLogger(__name__)
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@lru_cache(maxsize=1)
def build_dependencies() -> tuple[
    Settings,
    SqlServerRepository,
    ExecuteSqlQueryUseCase,
    ReadDocumentUseCase,
    ExecuteSqlCommandUseCase,
    AddContractLinesUseCase,
    CreatePurchaseAlbaranUseCase,
]:
    settings = get_settings()
    repository = SqlServerRepository(settings)
    sql_use_case = ExecuteSqlQueryUseCase(repository, settings)
    document_use_case = ReadDocumentUseCase(repository)
    command_use_case = ExecuteSqlCommandUseCase(repository, settings)
    contract_lines_use_case = AddContractLinesUseCase(repository, settings)
    albaran_use_case = CreatePurchaseAlbaranUseCase(repository, settings)
    return (
        settings, repository, sql_use_case, document_use_case,
        command_use_case, contract_lines_use_case, albaran_use_case,
    )


@app.route(route="sql/read", methods=["POST"])
def sql_read(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, _, sql_use_case, _, _, _, _ = build_dependencies()
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
            "Solicitud invalida.",
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


@app.route(route="sql/write", methods=["POST"])
def sql_write(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, _, _, _, command_use_case, _, _ = build_dependencies()
        body = req.get_json()
        request_model = SqlWriteRequest.model_validate(body)
        response_model = command_use_case.run(request_model)
        return json_response(response_model)
    except WriteValidationError as exc:
        logger.warning("WriteValidationError en sql/write: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except ValidationError as exc:
        logger.warning("ValidationError en sql/write: %s", exc)
        return error_response(
            "Solicitud invalida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en sql/write: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en sql/write")
        return error_response(
            "Error interno ejecutando sql/write.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )


@app.route(route="sigrid/contrato-lineas", methods=["POST"])
def sigrid_contrato_lineas(req: func.HttpRequest) -> func.HttpResponse:
    """
    Anade lineas (ctrpro) a un contrato de compra existente, localizado por
    (codigo de contrato + codigo de obra + CIF del proveedor). DRY-RUN por
    defecto (commit=false): no escribe, solo previsualiza filas y totales.
    """
    try:
        _, _, _, _, _, contract_lines_use_case, _ = build_dependencies()
        body = req.get_json()
        request_model = AddContractLinesRequest.model_validate(body)
        response_model = contract_lines_use_case.run(request_model)
        return json_response(response_model)
    except ValidationError as exc:
        logger.warning("ValidationError en sigrid/contrato-lineas: %s", exc)
        return error_response(
            "Solicitud invalida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en sigrid/contrato-lineas: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en sigrid/contrato-lineas")
        return error_response(
            "Error interno ejecutando sigrid/contrato-lineas.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )


@app.route(route="sigrid/albaran", methods=["POST"])
def sigrid_albaran(req: func.HttpRequest) -> func.HttpResponse:
    """
    Crea un albaran de compra (recepcion) a partir de un contrato de compra
    existente, localizado por (codigo de contrato + codigo de obra + CIF del
    proveedor). Replica TODAS las lineas del contrato: las recibidas con su
    cantidad, el resto con cantidad 0. Inserta la cabecera (con + dca), las
    lineas (dcapro), la trazabilidad contrato->albaran (ctrprodes), los
    movimientos de stock (mov), actualiza ctrpro.canser y recalcula los
    estados estser/estfac de la cabecera del contrato.

    DRY-RUN por defecto (commit=false): no escribe, solo previsualiza la
    cabecera resultante, lineas, movimientos de stock y nuevos estados del
    contrato, reservando los identificadores que se usarian.
    """
    try:
        _, _, _, _, _, _, albaran_use_case = build_dependencies()
        body = req.get_json()
        request_model = AddPurchaseAlbaranRequest.model_validate(body)
        response_model = albaran_use_case.run(request_model)
        return json_response(response_model)
    except ValidationError as exc:
        logger.warning("ValidationError en sigrid/albaran: %s", exc)
        return error_response(
            "Solicitud invalida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en sigrid/albaran: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en sigrid/albaran")
        return error_response(
            "Error interno ejecutando sigrid/albaran.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )


@app.route(route="sigrid/albaran-directo", methods=["POST"])
def sigrid_albaran_directo(req: func.HttpRequest) -> func.HttpResponse:
    """
    Crea un albaran de compra DIRECTO (no asociado a un contrato). El proveedor
    se resuelve por CIF, la obra por su codigo, y cada linea aporta producto +
    cantidad + precio (almacen/IVA/cuenta se heredan de la ultima dcapro del
    producto, salvo override). Inserta con + dca + dcapro + mov (NO ctrprodes,
    NO toca canser ni estados de contrato). DRY-RUN por defecto.
    """
    try:
        deps = build_dependencies()
        settings, repository = deps[0], deps[1]
        use_case = CreateDirectAlbaranUseCase(repository, settings)
        body = req.get_json()
        request_model = AddDirectAlbaranRequest.model_validate(body)
        response_model = use_case.run(request_model)
        return json_response(response_model)
    except ValidationError as exc:
        logger.warning("ValidationError en sigrid/albaran-directo: %s", exc)
        return error_response(
            "Solicitud invalida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en sigrid/albaran-directo: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en sigrid/albaran-directo")
        return error_response(
            "Error interno ejecutando sigrid/albaran-directo.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )


@app.route(route="sigrid/concepto-grafico", methods=["POST"])
def sigrid_concepto_grafico(req: func.HttpRequest) -> func.HttpResponse:
    """
    Adjunta un documento a un concepto de Sigrid: escribe el binario en la base
    DOCUMENTAL, sus metadatos en la de negocio (mismo cod y mismo emp) y el
    enlace con el concepto, todo en UNA transaccion. Es la UNICA via por la que
    se escribe en la base documental: sql/write sigue sin poder nombrarla.

    DRY-RUN por defecto (commit=false): solo lecturas, con credenciales de
    lectura, y preview completo de las tres filas.
    """
    try:
        deps = build_dependencies()
        settings, repository = deps[0], deps[1]
        use_case = AttachConceptoGraficoUseCase(repository, settings)
        body = req.get_json()
        request_model = AttachConceptoGraficoRequest.model_validate(body)
        response_model = use_case.run(request_model)
        return json_response(response_model)
    except ConceptoGraficoError as exc:
        logger.warning("ConceptoGraficoError en sigrid/concepto-grafico: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__, "codigo": exc.codigo},
        )
    except pyodbc.IntegrityError as exc:
        # Clave duplicada: la transaccion ya se revirtio entera (el repositorio
        # reintenta y, agotados los reintentos, propaga). El ERP quedo intacto.
        logger.warning("IntegrityError en sigrid/concepto-grafico: %s", exc)
        return error_response(
            "Colision de clave al escribir el grafico: el ERP quedo sin cambios; reintente.",
            status_code=400,
            details={"type": type(exc).__name__, "codigo": "colision_de_clave"},
        )
    except ValidationError as exc:
        logger.warning("ValidationError en sigrid/concepto-grafico: %s", exc)
        return error_response(
            "Solicitud invalida.",
            status_code=400,
            details={"type": type(exc).__name__, "validation": exc.errors()},
        )
    except ValueError as exc:
        logger.warning("ValueError en sigrid/concepto-grafico: %s", exc)
        return error_response(
            str(exc),
            status_code=400,
            details={"type": type(exc).__name__},
        )
    except Exception as exc:
        logger.exception("Error inesperado en sigrid/concepto-grafico")
        return error_response(
            "Error interno ejecutando sigrid/concepto-grafico.",
            status_code=500,
            details={"type": type(exc).__name__, "exception": str(exc)},
        )


@app.route(route="documents/read", methods=["POST"])
def documents_read(req: func.HttpRequest) -> func.HttpResponse:
    try:
        _, _, _, document_use_case, _, _, _ = build_dependencies()
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
            "Solicitud invalida.",
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
