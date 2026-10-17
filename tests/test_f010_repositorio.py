# tests/test_f010_repositorio.py
"""
F-010 · R10, R11, R13 y R14: la consulta de documents/read en el adaptador.

Sin red ni base de datos: `_connect` se dobla con una conexión falsa cuyo
cursor registra el SQL y los parámetros y devuelve 0, 1 o 2 filas, y
`pyodbc.connect` se sustituye por algo que revienta si alguien lo llega a
llamar. Ajustes falsos con `SimpleNamespace`.
"""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

import pytest

from domain.models import document_models
from infrastructure.repositories import sql_server_repository as adaptador
from infrastructure.security.identifier_guard import IdentifierValidationError

_AJUSTES = SimpleNamespace(
    default_query_timeout_seconds=37,
    sql_server_username="lector",
    sql_server_password="no-es-una-clave",
    sql_server_write_username="escritor",
    sql_server_write_password="tampoco",
)

_PDF = b"%PDF-1.4 binario"

_TEXTO_AMBIGUO = (
    "La localizacion casa con mas de una fila en [dbo].[gra] ({condicion}): no se sirve "
    "ninguna. Usa una clave unica (en dbo.gra: key con emp y cod, o id_column ide)."
)


class CursorFalso:
    def __init__(self, filas: list[tuple[Any, ...]]) -> None:
        self._filas = filas
        self.llamadas: list[tuple[str, tuple[Any, ...]]] = []

    def execute(self, sql: str, *parametros: Any) -> None:
        self.llamadas.append((sql, parametros))

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._filas)

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._filas[0] if self._filas else None


class ConexionFalsa:
    def __init__(self, cursor: CursorFalso) -> None:
        self._cursor = cursor

    def cursor(self) -> CursorFalso:
        return self._cursor


@pytest.fixture(autouse=True)
def _sin_pyodbc(monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibido(*_: Any, **__: Any) -> None:
        raise AssertionError("un unit test no puede abrir una conexión real")

    monkeypatch.setattr(adaptador.pyodbc, "connect", prohibido)


def repositorio(monkeypatch: pytest.MonkeyPatch, filas: list[tuple[Any, ...]]):
    cursor = CursorFalso(filas)
    conexiones: list[dict[str, Any]] = []

    @contextmanager
    def conectar(self: Any, **kwargs: Any) -> Iterator[ConexionFalsa]:
        conexiones.append(kwargs)
        yield ConexionFalsa(cursor)

    monkeypatch.setattr(adaptador.SqlServerRepository, "_connect", conectar)
    return adaptador.SqlServerRepository(_AJUSTES), cursor, conexiones


def leer(repo: Any, key: dict[str, Any], **otros: Any):
    campos = {
        "database": "ruesma_rep",
        "schema": "dbo",
        "table": "gra",
        "key": key,
        "blob_column": "ima",
        "filename_columns": ["nomori", "nom"],
    }
    campos.update(otros)
    return repo.read_document(**campos)


def componer(key: dict[str, Any], **otros: Any) -> tuple[str, list[Any], str]:
    campos = {
        "schema": "dbo",
        "table": "gra",
        "key": key,
        "blob_column": "ima",
        "filename_columns": ["nomori", "nom"],
    }
    campos.update(otros)
    return adaptador.build_document_query(**campos)


# --- R11: el SQL exacto, con parámetros en orden ------------------------------


def test_f010_r11_sql_con_dos_columnas_en_el_orden_de_key() -> None:
    sql, parametros, condicion = componer({"emp": 1, "cod": "ABC"})
    assert sql == (
        "SELECT TOP (2) [nomori], [nom], CAST([ima] AS varbinary(max)) AS file_content "
        "FROM [dbo].[gra] WHERE [emp] = ? AND [cod] = ?"
    )
    assert parametros == [1, "ABC"]
    assert condicion == "emp=1 AND cod=ABC"


def test_f010_r11_el_orden_de_key_manda_en_sql_y_parametros() -> None:
    sql, parametros, condicion = componer({"d": 4, "a": "x", "c": 3, "b": "y"})
    assert sql.endswith("WHERE [d] = ? AND [a] = ? AND [c] = ? AND [b] = ?")
    assert parametros == [4, "x", 3, "y"]
    assert condicion == "d=4 AND a=x AND c=3 AND b=y"


def test_f010_r11_una_columna_compone_la_condicion_de_hoy() -> None:
    sql, parametros, condicion = componer({"ide": 365617}, filename_columns=["nomori"])
    assert sql == (
        "SELECT TOP (2) [nomori], CAST([ima] AS varbinary(max)) AS file_content "
        "FROM [dbo].[gra] WHERE [ide] = ?"
    )
    assert parametros == [365617]
    assert condicion == "ide=365617"


def test_f010_r11_ningun_valor_aparece_en_el_texto_del_sql() -> None:
    malicioso = "X' OR 1=1; --"
    sql, parametros, _ = componer({"cod": malicioso, "emp": 987654321})
    assert malicioso not in sql
    assert "987654321" not in sql
    assert parametros == [malicioso, 987654321]


def test_f010_r11_los_identificadores_salen_validados_y_recortados() -> None:
    sql, _, condicion = componer({" ide ": 1}, schema=" dbo ", table=" gra ", blob_column=" ima ")
    assert "[dbo].[gra]" in sql and "[ima]" in sql and "WHERE [ide] = ?" in sql
    assert condicion == "ide=1"


def test_f010_r11_read_document_ejecuta_una_vez_con_parametros_posicionales(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo, cursor, _ = repositorio(monkeypatch, [("a.pdf", None, _PDF)])
    leer(repo, {"emp": 1, "cod": "ABC"})
    esperado_sql, _esperados, _ = componer({"emp": 1, "cod": "ABC"})
    assert cursor.llamadas == [(esperado_sql, (1, "ABC"))]


def test_f010_r11_conecta_como_hoy_con_la_credencial_de_lectura(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, conexiones = repositorio(monkeypatch, [("a.pdf", None, _PDF)])
    leer(repo, {"ide": 1})
    assert conexiones == [{
        "database": "ruesma_rep",
        "timeout_seconds": 37,
        "username": "lector",
        "password": "no-es-una-clave",
        "autocommit": True,
    }]


# --- R10: cada nombre de key pasa por IdentifierGuard -------------------------


@pytest.mark.parametrize("nombre", ["emp; DROP TABLE x", "a]b", "1emp", "cód", "e-m-p"])
def test_f010_r10_nombre_de_key_no_valido_se_rechaza(nombre: str) -> None:
    with pytest.raises(IdentifierValidationError) as info:
        componer({"emp": 1, nombre: 2})
    assert "'key'" in str(info.value)


def test_f010_r10_nombre_no_valido_no_abre_conexion(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, cursor, conexiones = repositorio(monkeypatch, [("a.pdf", None, _PDF)])
    with pytest.raises(IdentifierValidationError):
        leer(repo, {"emp": 1, "co]d": "x"})
    assert conexiones == []
    assert cursor.llamadas == []


def test_f010_r10_orden_de_validacion_schema_table_key_blob_filename() -> None:
    malo = "x]"
    casos = [
        ({"schema": malo, "table": malo, "key": {malo: 1}, "blob_column": malo}, "'schema'"),
        ({"table": malo, "key": {malo: 1}, "blob_column": malo}, "'table'"),
        ({"key": {malo: 1}, "blob_column": malo, "filename_columns": [malo]}, "'key'"),
        ({"blob_column": malo, "filename_columns": [malo]}, "'blob_column'"),
        ({"filename_columns": ["nomori", malo]}, "'filename_columns'"),
    ]
    for otros, campo in casos:
        key = otros.pop("key", {"ide": 1})
        with pytest.raises(IdentifierValidationError) as info:
            componer(key, **otros)
        assert campo in str(info.value)


# --- Una fila: el registro de hoy, sin id_value -------------------------------


def test_f010_r11_una_fila_devuelve_candidatos_y_contenido(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [("  nombre.pdf ", "otro", bytearray(_PDF))])
    registro = leer(repo, {"emp": 1, "cod": "ABC"})
    assert registro.file_name_candidates == ["nombre.pdf", "otro"]
    assert registro.content == _PDF and isinstance(registro.content, bytes)
    assert not hasattr(registro, "id_value")


def test_f010_r11_candidatos_vacios_o_nulos_se_descartan(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [(None, "", 42, _PDF)])
    registro = leer(repo, {"ide": 1}, filename_columns=["a", "b", "c"])
    assert registro.file_name_candidates == ["42"]
    assert registro.content == _PDF


# --- R14: ninguna fila o BLOB nulo, textos de hoy ------------------------------


def test_f010_r14_ninguna_fila_con_una_columna_es_el_texto_de_hoy(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [])
    with pytest.raises(ValueError) as info:
        leer(repo, {"ide": 365617})
    assert str(info.value) == "No existe ninguna fila en [dbo].[gra] con ide=365617."
    assert type(info.value) is ValueError


def test_f010_r14_ninguna_fila_con_dos_columnas(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [])
    with pytest.raises(ValueError) as info:
        leer(repo, {"emp": 1, "cod": "ABC"})
    assert str(info.value) == "No existe ninguna fila en [dbo].[gra] con emp=1 AND cod=ABC."


def test_f010_r14_blob_nulo_es_el_texto_de_hoy(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [("a.pdf", None, None)])
    with pytest.raises(ValueError) as info:
        leer(repo, {"ide": 365617})
    assert str(info.value) == "La columna ima esta vacia para ide=365617."
    assert type(info.value) is ValueError


def test_f010_r14_blob_nulo_con_dos_columnas(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [("a.pdf", None, None)])
    with pytest.raises(ValueError) as info:
        leer(repo, {"emp": 2, "cod": "Z"})
    assert str(info.value) == "La columna ima esta vacia para emp=2 AND cod=Z."


# --- R13: más de una fila → DocumentoAmbiguoError -----------------------------


def test_f010_r13_dos_filas_por_key_es_ambiguo(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [("a.pdf", None, _PDF), ("b.pdf", None, _PDF)])
    with pytest.raises(document_models.DocumentoAmbiguoError) as info:
        leer(repo, {"emp": 1, "cod": "ABC"})
    assert str(info.value) == _TEXTO_AMBIGUO.format(condicion="emp=1 AND cod=ABC")


def test_f010_r13_dos_filas_por_una_columna_tambien(monkeypatch: pytest.MonkeyPatch) -> None:
    repo, _, _ = repositorio(monkeypatch, [("a.pdf", None, _PDF), ("b.pdf", None, None)])
    with pytest.raises(document_models.DocumentoAmbiguoError) as info:
        leer(repo, {"emp": 1})
    assert str(info.value) == _TEXTO_AMBIGUO.format(condicion="emp=1")


def test_f010_r13_la_ambiguedad_es_un_valueerror_de_otro_tipo() -> None:
    assert issubclass(document_models.DocumentoAmbiguoError, ValueError)
    assert document_models.DocumentoAmbiguoError.__name__ == "DocumentoAmbiguoError"
