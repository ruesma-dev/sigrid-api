# tests/test_f011_repositorio.py
"""
F-011 · R13-R15 (decisión D2 = A1): `SqlServerRepository._connect` valida
`database` con `IdentifierGuard` antes de componer la cadena de conexión, para
TODOS los métodos del adaptador que conectan.

`pyodbc.connect` se sustituye por un doble que captura la cadena y corta con
una excepción propia: ni red ni base de datos. Las credenciales son de mentira.
"""
from __future__ import annotations

from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest

from domain.models.sql_models import SqlReadRequest, SqlWriteRequest
from infrastructure.repositories import sql_server_repository as adaptador
from infrastructure.security.identifier_guard import IdentifierValidationError

_AJUSTES = SimpleNamespace(
    sql_driver="ODBC Driver 18 for SQL Server",
    sql_server_host="servidor.falso",
    sql_server_port=1433,
    sql_server_username="lector",
    sql_server_password="no-es}una-clave",
    sql_server_write_username="escritor",
    sql_server_write_password="tampoco",
    default_query_timeout_seconds=37,
    default_max_rows=10,
    default_write_timeout_seconds=41,
    default_max_affected_rows=10,
    use_fast_executemany=False,
)


class Capturada(Exception):
    """El doble de pyodbc.connect corta aquí, con la cadena ya capturada."""


@pytest.fixture
def cadenas(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    capturadas: list[str] = []

    def connect(cadena: str, **_: Any) -> None:
        capturadas.append(cadena)
        raise Capturada

    monkeypatch.setattr(adaptador.pyodbc, "connect", connect)
    return capturadas


def _repo() -> adaptador.SqlServerRepository:
    return adaptador.SqlServerRepository(_AJUSTES)


# Cada método público que conecta, llamado con una base dada.
_METODOS: dict[str, Callable[[adaptador.SqlServerRepository, str], Any]] = {
    "execute_read_query": lambda repo, db: repo.execute_read_query(
        SqlReadRequest.model_construct(database=db, sql="SELECT 1", parameters=[], max_rows=None, timeout_seconds=None)
    ),
    "execute_write_command": lambda repo, db: repo.execute_write_command(
        SqlWriteRequest.model_construct(database=db, statements=[], max_affected_rows=None, timeout_seconds=None)
    ),
    "read_document": lambda repo, db: repo.read_document(
        database=db, schema="dbo", table="gra", key={"ide": 1}, blob_column="ima", filename_columns=["nomori"]
    ),
    "read_full_row": lambda repo, db: repo.read_full_row(database=db, table="ctr", ide=1),
    "read_rows_by": lambda repo, db: repo.read_rows_by(
        database=db, table="ctrpro", where_column="ctride", where_value=1, order_by="ide"
    ),
    "peek_next_ide": lambda repo, db: repo.peek_next_ide(database=db, table="con"),
    "locate_contract": lambda repo, db: repo.locate_contract(
        database=db, cod_contrato="C1", cod_obra="O1", cif_proveedor="B0"
    ),
    "run_in_write_transaction": lambda repo, db: repo.run_in_write_transaction(
        database=db, timeout_seconds=5, applock_resources=[], applock_timeout_ms=10, max_retries=0,
        work=lambda _: None,
    ),
}

_ESCRITURA = {"execute_write_command", "run_in_write_transaction"}


def _esperada(database: str, *, escritura: bool) -> str:
    """La cadena de hoy, carácter a carácter (R15)."""
    usuario, clave = ("escritor", "tampoco") if escritura else ("lector", "no-es}}una-clave")
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        "SERVER=tcp:servidor.falso,1433;"
        f"DATABASE={database};"
        f"UID={usuario};"
        f"PWD={{{clave}}};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )


# --- R13 y R14: base fuera del patrón, sin conectar ---------------------------


@pytest.mark.parametrize("metodo", sorted(_METODOS))
@pytest.mark.parametrize(
    "database",
    ["ruesma_rep;APP=x", "x=y", "{x}", "1ruesma", "ruesma-rep", "ruesma rep", "ruesma;", "ruesma}"],
)
def test_f011_r14_base_fuera_del_patron_no_conecta(
    cadenas: list[str], metodo: str, database: str
) -> None:
    with pytest.raises(IdentifierValidationError) as info:
        _METODOS[metodo](_repo(), database)
    assert str(info.value) == f"El identificador 'database' contiene caracteres no permitidos: {database}"
    assert cadenas == []


# --- R15: base dentro del patrón, cadena idéntica a la de hoy -----------------


@pytest.mark.parametrize("metodo", sorted(_METODOS))
@pytest.mark.parametrize("database", ["ruesma", "ruesma_rep", "master"])
def test_f011_r15_cadena_identica_a_la_de_hoy(cadenas: list[str], metodo: str, database: str) -> None:
    with pytest.raises(Capturada):
        _METODOS[metodo](_repo(), database)
    assert cadenas == [_esperada(database, escritura=metodo in _ESCRITURA)]


def test_f011_r13_se_usa_el_valor_que_devuelve_el_guardia(cadenas: list[str]) -> None:
    """IdentifierGuard recorta: la cadena lleva el valor validado, no el crudo."""
    with pytest.raises(Capturada):
        _METODOS["read_full_row"](_repo(), "  ruesma_rep  ")
    assert cadenas == [_esperada("ruesma_rep", escritura=False)]
