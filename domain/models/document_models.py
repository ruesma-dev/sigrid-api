# domain/models/document_models.py
from __future__ import annotations

from dataclasses import dataclass


class DocumentoAmbiguoError(ValueError):
    """La localización casa con más de una fila: no se sirve ninguna (F-010 R13).

    Hereda de `ValueError` para que, si faltara su `except` propio en la ruta,
    cayera en 400 y no en 500; su `details.type` nunca es `"ValueError"`.
    """


@dataclass(frozen=True)
class RawDocumentRecord:
    file_name_candidates: list[str]
    content: bytes
