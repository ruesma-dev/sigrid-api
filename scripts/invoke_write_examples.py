# scripts/invoke_write_examples.py
from __future__ import annotations

import json
import os

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


def _post_write(payload: dict) -> None:
    response = requests.post(
        f"{BASE_URL}/api/sql/write",
        headers=HEADERS,
        json=payload,
        timeout=120,
    )
    print(f"HTTP {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(response.text)
    print("-" * 70)


def example_single_update() -> None:
    """UPDATE simple (atajo de una sola sentencia)."""
    payload = {
        "database": "ruesma",
        "sql": "UPDATE dbo.tu_tabla SET descripcion = ? WHERE ide = ?",
        "parameters": ["valor de prueba", 2563363],
        "max_affected_rows": 1,
        "timeout_seconds": 30,
    }
    _post_write(payload)


def example_multi_table_batch() -> None:
    """Varias tablas en UNA transacción atómica (todo o nada)."""
    payload = {
        "database": "ruesma",
        "statements": [
            {
                "sql": "INSERT INTO dbo.tabla_a (ide, valor) VALUES (?, ?)",
                "parameters": [9001, "alpha"],
            },
            {
                "sql": "UPDATE dbo.tabla_b SET estado = ? WHERE ide = ?",
                "parameters": ["procesado", 9001],
            },
            {
                "sql": "DELETE FROM dbo.tabla_c WHERE ide = ?",
                "parameters": [9001],
            },
        ],
        "max_affected_rows": 10,
        "timeout_seconds": 60,
    }
    _post_write(payload)


def example_bulk_insert() -> None:
    """INSERT masivo con parameter_sets (executemany + fast_executemany)."""
    rows = [[10000 + i, f"item-{i}"] for i in range(50)]
    payload = {
        "database": "ruesma",
        "statements": [
            {
                "sql": "INSERT INTO dbo.tabla_a (ide, valor) VALUES (?, ?)",
                "parameter_sets": rows,
            }
        ],
        "max_affected_rows": 100,
        "timeout_seconds": 60,
    }
    _post_write(payload)


def example_blocked_no_where() -> None:
    """Debe FALLAR (400): UPDATE sin WHERE — salvaguarda anti-masivo."""
    payload = {
        "database": "ruesma",
        "sql": "UPDATE dbo.tu_tabla SET descripcion = ?",
        "parameters": ["esto no debe aplicarse"],
    }
    _post_write(payload)


def example_blocked_ddl() -> None:
    """Debe FALLAR (400): DDL no permitido aunque rw_user tuviera permisos."""
    payload = {
        "database": "ruesma",
        "sql": "DROP TABLE dbo.tu_tabla",
    }
    _post_write(payload)


if __name__ == "__main__":
    # Descomenta los que quieras probar. Empieza por los que DEBEN fallar:
    # son seguros (no escriben nada) y verifican que el guard funciona.
    example_blocked_no_where()
    example_blocked_ddl()

    # Pruebas reales de escritura (ajusta tablas/ides a datos de prueba):
    # example_single_update()
    # example_multi_table_batch()
    # example_bulk_insert()
