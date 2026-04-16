# infrastructure/serialization/json_encoder.py
from __future__ import annotations

import base64
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from config.settings import Settings


class JsonValueSerializer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def serialize(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date, time)):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, memoryview):
            value = value.tobytes()
        if isinstance(value, (bytes, bytearray)):
            raw = bytes(value)
            if len(raw) <= self._settings.max_inline_binary_bytes:
                return {
                    "type": "binary",
                    "encoding": "base64",
                    "size": len(raw),
                    "value": base64.b64encode(raw).decode("ascii"),
                }
            return {
                "type": "binary",
                "encoding": "omitted",
                "size": len(raw),
            }
        return str(value)
