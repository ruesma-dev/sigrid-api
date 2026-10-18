# tests/test_f011_caso_de_uso.py
"""
F-011 · R1-R6, R8 y R10: `ReadDocumentUseCase` valida `database` contra la
lista de lectura (`Settings.allowed_databases`) antes de tocar el repositorio.

Ajustes `SimpleNamespace` y repositorio doble que registra o revienta; ni red
ni base de datos. `modelos.BaseNoPermitidaError` se resuelve en cada test (y no
al importar) para que la fase ROJO falle test a test.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from application.use_cases.read_document_use_case import ReadDocumentUseCase
from domain.models import document_models as modelos
from domain.models.document_models import RawDocumentRecord
from domain.models.sql_models import DocumentReadRequest
from infrastructure.repositories import sql_server_repository as adaptador

_PDF = b"%PDF-1.4 binario"
_LISTA = ["ruesma", "ruesma_rep", "master"]


class RepositorioDoble:
    def __init__(self) -> None:
        self.llamadas: list[dict[str, Any]] = []

    def read_document(self, **kwargs: Any) -> RawDocumentRecord:
        self.llamadas.append(kwargs)
        return RawDocumentRecord(file_name_candidates=["a.pdf"], content=_PDF)


class RepositorioQueRevienta:
    """R2: si la base no está permitida, el repositorio no se toca."""

    def read_document(self, **_: Any) -> RawDocumentRecord:
        raise AssertionError("no debía llamarse a read_document")


def ajustes(lista: list[str] | None = None) -> SimpleNamespace:
    return SimpleNamespace(allowed_databases=list(_LISTA if lista is None else lista))


def peticion(**campos: Any) -> DocumentReadRequest:
    base = {
        "database": "ruesma_rep",
        "table": "gra",
        "id_column": "ide",
        "id_value": 365617,
        "blob_column": "ima",
        "filename_columns": ["nomori"],
    }
    return DocumentReadRequest.model_validate({**base, **campos})


def rechazo(database: str, lista: list[str]) -> str:
    return (
        f"La base de datos '{database}' no está permitida. "
        f"Permitidas: {', '.join(lista) or '(ninguna)'}"
    )


# --- R1 y R2: base fuera de la lista ------------------------------------------


def test_f011_r1_base_no_permitida_lanza_con_el_texto_exacto() -> None:
    caso = ReadDocumentUseCase(RepositorioQueRevienta(), ajustes())
    with pytest.raises(modelos.BaseNoPermitidaError) as info:
        caso.run(peticion(database="ruesma_otra"))
    assert str(info.value) == (
        "La base de datos 'ruesma_otra' no está permitida. Permitidas: ruesma, ruesma_rep, master"
    )


def test_f011_r1_el_texto_respeta_el_orden_de_la_lista() -> None:
    caso = ReadDocumentUseCase(RepositorioQueRevienta(), ajustes(["b", "a"]))
    with pytest.raises(modelos.BaseNoPermitidaError) as info:
        caso.run(peticion(database="ruesma_rep"))
    assert str(info.value) == "La base de datos 'ruesma_rep' no está permitida. Permitidas: b, a"


def test_f011_r2_base_no_permitida_no_llama_al_repositorio() -> None:
    repo = RepositorioDoble()
    caso = ReadDocumentUseCase(repo, ajustes(["ruesma"]))
    with pytest.raises(modelos.BaseNoPermitidaError):
        caso.run(peticion(database="ruesma_rep"))
    assert repo.llamadas == []


def test_f011_r2_base_no_permitida_no_abre_conexion(monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibido(*_: Any, **__: Any) -> None:
        raise AssertionError("un unit test no puede abrir una conexión real")

    monkeypatch.setattr(adaptador.pyodbc, "connect", prohibido)
    repo = adaptador.SqlServerRepository(SimpleNamespace())
    with pytest.raises(modelos.BaseNoPermitidaError):
        ReadDocumentUseCase(repo, ajustes(["ruesma"])).run(peticion(database="ruesma_rep"))


# --- R3: igualdad exacta y sensible a mayúsculas ------------------------------


@pytest.mark.parametrize("database", ["RUESMA_REP", "Ruesma_Rep", "ruesma_re", "ruesma_rep_x"])
def test_f011_r3_igualdad_exacta_y_sensible_a_mayusculas(database: str) -> None:
    caso = ReadDocumentUseCase(RepositorioQueRevienta(), ajustes())
    with pytest.raises(modelos.BaseNoPermitidaError) as info:
        caso.run(peticion(database=database))
    assert str(info.value) == rechazo(database, _LISTA)


def test_f011_r3_espacios_alrededor_se_aceptan_porque_el_modelo_los_recorta() -> None:
    repo = RepositorioDoble()
    ReadDocumentUseCase(repo, ajustes()).run(peticion(database="  ruesma_rep  "))
    assert repo.llamadas[0]["database"] == "ruesma_rep"


# --- R4: lista vacía, todo cerrado --------------------------------------------


def test_f011_r4_lista_vacia_rechaza_con_ninguna() -> None:
    caso = ReadDocumentUseCase(RepositorioQueRevienta(), ajustes([]))
    with pytest.raises(modelos.BaseNoPermitidaError) as info:
        caso.run(peticion(database="ruesma_rep"))
    assert str(info.value) == "La base de datos 'ruesma_rep' no está permitida. Permitidas: (ninguna)"


# --- R5: caracteres de la cadena de conexión ----------------------------------


@pytest.mark.parametrize(
    "database",
    ["ruesma_rep;APP=x", "ruesma_rep;", "x=y", "ruesma rep", "{ruesma_rep}", "ruesma_rep}"],
)
def test_f011_r5_caracteres_de_cadena_de_conexion_se_rechazan(database: str) -> None:
    repo = RepositorioDoble()
    caso = ReadDocumentUseCase(repo, ajustes())
    with pytest.raises(modelos.BaseNoPermitidaError) as info:
        caso.run(peticion(database=database))
    assert str(info.value) == rechazo(database, _LISTA)
    assert repo.llamadas == []


# --- R6: la base se valida antes que los identificadores ----------------------


@pytest.mark.parametrize(
    "campos",
    [
        {"table": "gra;x"},
        {"blob_column": "ima]"},
        {"id_column": "ide;x"},
        {"schema": "dbo x"},
        {"filename_columns": ["nom;x"]},
    ],
)
def test_f011_r6_base_no_permitida_gana_a_identificador_no_valido(
    monkeypatch: pytest.MonkeyPatch, campos: dict[str, Any]
) -> None:
    def prohibido(*_: Any, **__: Any) -> None:
        raise AssertionError("un unit test no puede abrir una conexión real")

    monkeypatch.setattr(adaptador.pyodbc, "connect", prohibido)
    repo = adaptador.SqlServerRepository(SimpleNamespace())
    caso = ReadDocumentUseCase(repo, ajustes(["ruesma"]))
    with pytest.raises(modelos.BaseNoPermitidaError):
        caso.run(peticion(database="ruesma_rep", **campos))


# --- R8: clase propia que hereda de ValueError --------------------------------


def test_f011_r8_base_no_permitida_hereda_de_value_error() -> None:
    assert issubclass(modelos.BaseNoPermitidaError, ValueError)
    assert modelos.BaseNoPermitidaError is not ValueError
    assert modelos.BaseNoPermitidaError.__name__ == "BaseNoPermitidaError"


def test_f011_r8_no_es_documento_ambiguo() -> None:
    assert not issubclass(modelos.BaseNoPermitidaError, modelos.DocumentoAmbiguoError)


# --- R10: con la base permitida, todo como tras F-010 -------------------------


def test_f011_r10_base_permitida_llega_al_repositorio_con_los_argumentos_de_f010() -> None:
    repo = RepositorioDoble()
    respuesta = ReadDocumentUseCase(repo, ajustes()).run(peticion())
    assert repo.llamadas == [{
        "database": "ruesma_rep",
        "schema": "dbo",
        "table": "gra",
        "key": {"ide": 365617},
        "blob_column": "ima",
        "filename_columns": ["nomori"],
        "key_field_name": "id_column",
    }]
    assert respuesta.file_name == "a.pdf"
    assert respuesta.content == _PDF
    assert respuesta.content_type == "application/pdf"


@pytest.mark.parametrize("database", _LISTA)
def test_f011_r10_cada_base_de_la_lista_se_acepta(database: str) -> None:
    repo = RepositorioDoble()
    ReadDocumentUseCase(repo, ajustes()).run(peticion(database=database))
    assert repo.llamadas[0]["database"] == database


def test_f011_r10_la_lista_se_lee_en_cada_llamada() -> None:
    """Como SqlQueryGuard: un cambio de la lista vale sin reconstruir el caso de uso."""
    repo = RepositorioDoble()
    conf = ajustes(["ruesma"])
    caso = ReadDocumentUseCase(repo, conf)
    with pytest.raises(modelos.BaseNoPermitidaError):
        caso.run(peticion(database="ruesma_rep"))
    conf.allowed_databases = ["ruesma_rep"]
    caso.run(peticion(database="ruesma_rep"))
    assert len(repo.llamadas) == 1
