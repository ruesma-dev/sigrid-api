# domain/models/document_models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RawDocumentRecord:
    file_name_candidates: list[str]
    content: bytes
    id_value: Any
