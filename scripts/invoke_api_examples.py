# scripts/invoke_api_examples.py
from __future__ import annotations

import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()
BASE_URL = os.environ.get("FUNCTION_BASE_URL", "http://localhost:7071")
FUNCTION_KEY = os.environ.get("FUNCTION_KEY", "")
HEADERS = {
    "Content-Type": "application/json",
}
if FUNCTION_KEY:
    HEADERS["x-functions-key"] = FUNCTION_KEY


def call_sql_read() -> None:
    payload = {
        "database": "ruesma_rep",
        "sql": "SELECT TOP 5 ide, nom, nomori FROM dbo.gra ORDER BY ide DESC",
        "parameters": [],
        "max_rows": 5,
        "timeout_seconds": 30,
    }
    response = requests.post(
        f"{BASE_URL}/api/sql/read",
        headers=HEADERS,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def call_document_read() -> None:
    payload = {
        "database": "ruesma_rep",
        "schema": "dbo",
        "table": "gra",
        "id_column": "ide",
        "id_value": 340434,
        "blob_column": "ima",
        "filename_columns": ["nomori", "nom"],
        "disposition": "attachment",
    }
    response = requests.post(
        f"{BASE_URL}/api/documents/read",
        headers=HEADERS,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    output_dir = Path("downloads")
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = response.headers.get("X-Document-Filename", "documento.bin")
    output_path = output_dir / filename
    output_path.write_bytes(response.content)
    print(f"Documento guardado en: {output_path.resolve()}")


if __name__ == "__main__":
    call_sql_read()
    call_document_read()
