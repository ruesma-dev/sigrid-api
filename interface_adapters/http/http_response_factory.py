# interface_adapters/http/http_response_factory.py
from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from typing import Any
from urllib.parse import quote

import azure.functions as func
from pydantic import BaseModel


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


def binary_file_response(
    *,
    content: bytes,
    content_type: str,
    file_name: str,
    disposition: str = "attachment",
) -> func.HttpResponse:
    encoded_name = quote(file_name)
    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{encoded_name}",
        "X-Document-Filename": file_name,
        "X-Document-Size": str(len(content)),
    }
    return func.HttpResponse(
        body=content,
        status_code=200,
        headers=headers,
        mimetype=content_type,
    )
