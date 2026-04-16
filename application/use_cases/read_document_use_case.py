# application/use_cases/read_document_use_case.py
from __future__ import annotations

import re
from urllib.parse import quote

from domain.models.sql_models import DocumentReadRequest, DocumentReadResponse
from domain.ports.sql_repository import SqlRepository


class ReadDocumentUseCase:
    def __init__(self, repository: SqlRepository) -> None:
        self._repository = repository

    def run(self, request: DocumentReadRequest) -> DocumentReadResponse:
        record = self._repository.read_document(
            database=request.database,
            schema=request.schema,
            table=request.table,
            id_column=request.id_column,
            id_value=request.id_value,
            blob_column=request.blob_column,
            filename_columns=request.filename_columns,
        )
        file_name = self._resolve_filename(record.file_name_candidates, record.content, record.id_value)
        content_type = self._detect_content_type(record.content)
        return DocumentReadResponse(
            file_name=file_name,
            content_type=content_type,
            size_bytes=len(record.content),
            content=record.content,
        )

    @staticmethod
    def _resolve_filename(candidates: list[str], content: bytes, id_value: object) -> str:
        candidate = next((item for item in candidates if item), f"document_{id_value}")
        safe_name = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', "_", candidate).strip() or f"document_{id_value}"
        if "." in safe_name:
            return safe_name
        extension = ReadDocumentUseCase._extension_from_content(content)
        return f"{safe_name}{extension}"

    @staticmethod
    def _extension_from_content(content: bytes) -> str:
        if content.startswith(b"%PDF"):
            return ".pdf"
        if content.startswith(b"\xFF\xD8\xFF"):
            return ".jpg"
        if content.startswith(b"\x89PNG"):
            return ".png"
        if content.startswith(b"II*\x00") or content.startswith(b"MM\x00*"):
            return ".tif"
        return ".bin"

    @staticmethod
    def _detect_content_type(content: bytes) -> str:
        if content.startswith(b"%PDF"):
            return "application/pdf"
        if content.startswith(b"\xFF\xD8\xFF"):
            return "image/jpeg"
        if content.startswith(b"\x89PNG"):
            return "image/png"
        if content.startswith(b"II*\x00") or content.startswith(b"MM\x00*"):
            return "image/tiff"
        return "application/octet-stream"
