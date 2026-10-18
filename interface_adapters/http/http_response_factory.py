# interface_adapters/http/http_response_factory.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any
from urllib.parse import quote

import azure.functions as func
from pydantic import BaseModel, ValidationError


def json_response(payload: Any, *, status_code: int = 200) -> func.HttpResponse:
    if isinstance(payload, BaseModel):
        serializable = payload.model_dump(mode="json")
    elif is_dataclass(payload):
        serializable = asdict(payload)
    else:
        serializable = payload

    return func.HttpResponse(
        body=json.dumps(serializable, ensure_ascii=False),
        status_code=status_code,
        mimetype="application/json",
    )


def error_response(message: str, *, status_code: int = 400, details: dict[str, Any] | None = None) -> func.HttpResponse:
    payload: dict[str, Any] = {
        "ok": False,
        "error": message,
    }
    if details:
        payload["details"] = details
    return json_response(payload, status_code=status_code)


def _errores_serializables(exc: ValidationError) -> list[dict[str, Any]]:
    """`exc.errors()` con cada valor que `json` no sabe serializar pasado a `str`
    (F-012 R4: la excepcion de una regla con mensaje propio, en `ctx.error`). Lo
    serializable sale identico a la lista de siempre (R6): `default` solo se
    invoca para lo que `json` rechaza."""
    return json.loads(json.dumps(exc.errors(), default=str))


def validation_error_response(exc: ValidationError) -> func.HttpResponse:
    """400 «Solicitud invalida.» con `details` = `{type, validation}`, el de las
    9 rutas (F-012 R8). `validation` es `exc.errors()` serializable siempre (R4,
    R6). No traza nada: cada ruta conserva su propia traza (R11)."""
    return error_response(
        "Solicitud invalida.",
        status_code=400,
        details={"type": type(exc).__name__, "validation": _errores_serializables(exc)},
    )


#: ASCII imprimible (0x20-0x7E) salvo "%": lo que X-Document-Filename deja tal cual (F-010 R1-R3).
_SEGUROS_EN_CABECERA = "".join(chr(c) for c in range(0x20, 0x7F) if chr(c) != "%")


def filename_header_value(file_name: str) -> str:
    """Nombre para X-Document-Filename: ASCII imprimible que `unquote` devuelve al original.

    Codifica en porcentual UTF-8 todo lo que no sea ASCII imprimible y el propio
    `%`, de modo que un nombre ASCII sin `%` viaja identico y cualquier otro se
    decodifica sin ambiguedad con `urllib.parse.unquote` (F-010, decision D1).
    """
    return quote(file_name, safe=_SEGUROS_EN_CABECERA, encoding="utf-8", errors="strict")


def binary_file_response(
    *,
    content: bytes,
    content_type: str,
    file_name: str,
    disposition: str = "attachment",
) -> func.HttpResponse:
    # safe="": RFC 5987 no admite "/" sin codificar en filename* (F-010, decision D2).
    encoded_name = quote(file_name, safe="")
    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_name}",
        "X-Document-Filename": filename_header_value(file_name),
        "X-Document-Size": str(len(content)),
    }
    return func.HttpResponse(
        body=content,
        status_code=200,
        headers=headers,
        mimetype=content_type,
    )
