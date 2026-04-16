# infrastructure/security/identifier_guard.py
from __future__ import annotations

import re


class IdentifierValidationError(ValueError):
    pass


class IdentifierGuard:
    _IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    @classmethod
    def validate_identifier(cls, value: str, *, field_name: str) -> str:
        identifier = value.strip()
        if not cls._IDENTIFIER_RE.fullmatch(identifier):
            raise IdentifierValidationError(
                f"El identificador '{field_name}' contiene caracteres no permitidos: {value}"
            )
        return identifier
