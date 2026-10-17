# tests/test_f010_caso_de_uso.py
"""
F-010 · R12 y R15: `ReadDocumentUseCase` pasa la localización como `key` y
compone el nombre de reserva con sus valores.

Repositorio doble que registra la llamada; ni red ni base de datos.
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from application.use_cases.read_document_use_case import ReadDocumentUseCase
from domain.models.document_models import RawDocumentRecord
from domain.models.sql_models import DocumentReadRequest
from infrastructure.repositories import sql_server_repository as adaptador
from infrastructure.security.identifier_guard import IdentifierValidationError

_PDF = b"%PDF-1.4 binario"


class RepositorioDoble:
    def __init__(self, candidatos: list[str], contenido: bytes = _PDF) -> None:
        self._registro = RawDocumentRecord(file_name_candidates=candidatos, content=contenido)
        self.llamadas: list[dict[str, Any]] = []

    def read_document(self, **kwargs: Any) -> RawDocumentRecord:
        self.llamadas.append(kwargs)
        return self._registro


def peticion(**campos: Any) -> DocumentReadRequest:
    base = {"database": "ruesma_rep", "table": "gra", "blob_column": "ima"}
    return DocumentReadRequest.model_validate({**base, **campos})


def ejecutar(repo: RepositorioDoble, **campos: Any):
    return ReadDocumentUseCase(repo).run(peticion(**campos))


# --- R12: un solo camino hacia el repositorio ---------------------------------


def test_f010_r12_id_column_llega_como_key_de_una_columna() -> None:
    repo = RepositorioDoble(["a.pdf"])
    ejecutar(repo, id_column="ide", id_value=365617, filename_columns=["nomori"])
    assert repo.llamadas == [{
        "database": "ruesma_rep",
        "schema": "dbo",
        "table": "gra",
        "key": {"ide": 365617},
        "blob_column": "ima",
        "filename_columns": ["nomori"],
        "key_field_name": "id_column",
    }]


def test_f010_r12_key_llega_tal_cual_y_en_su_orden() -> None:
    repo = RepositorioDoble(["a.pdf"])
    ejecutar(repo, key={"emp": 1, "cod": "ABC"}, schema="otro")
    llamada = repo.llamadas[0]
    assert llamada["key"] == {"emp": 1, "cod": "ABC"}
    assert list(llamada["key"]) == ["emp", "cod"]
    assert llamada["key_field_name"] == "key"
    assert llamada["schema"] == "otro"
    assert llamada["filename_columns"] == ["nomori", "nom"]


def test_f010_r12_la_respuesta_no_cambia() -> None:
    repo = RepositorioDoble(["Factura año señal.pdf"])
    respuesta = ejecutar(repo, id_column="ide", id_value=1)
    assert respuesta.file_name == "Factura año señal.pdf"
    assert respuesta.content == _PDF
    assert respuesta.size_bytes == len(_PDF)
    assert respuesta.content_type == "application/pdf"


# --- R15: nombre de reserva desde la localización -----------------------------


def test_f010_r15_reserva_con_una_columna_es_la_de_hoy() -> None:
    respuesta = ejecutar(RepositorioDoble([]), id_column="ide", id_value=365617)
    assert respuesta.file_name == "document_365617.pdf"


def test_f010_r15_reserva_con_dos_columnas_une_los_valores_en_orden() -> None:
    respuesta = ejecutar(RepositorioDoble([]), key={"emp": 1, "cod": "ABC"})
    assert respuesta.file_name == "document_1_ABC.pdf"


def test_f010_r15_reserva_con_id_value_null_como_hoy() -> None:
    respuesta = ejecutar(RepositorioDoble([], b"???"), id_column="ide", id_value=None)
    assert respuesta.file_name == "document_None.bin"


def test_f010_r15_reserva_cuando_el_candidato_queda_vacio_al_sanear() -> None:
    respuesta = ejecutar(RepositorioDoble(["   "]), key={"emp": 2, "cod": "Z"})
    assert respuesta.file_name == "document_2_Z.pdf"


def test_f010_r15_la_reserva_se_sanea_como_hoy() -> None:
    respuesta = ejecutar(RepositorioDoble([]), key={"emp": 1, "cod": 'a/b:c"d'})
    assert respuesta.file_name == "document_1_a_b_c_d.pdf"


def test_f010_r15_con_candidato_no_se_usa_la_reserva() -> None:
    respuesta = ejecutar(RepositorioDoble(["", "contrato"]), key={"emp": 1, "cod": "ABC"})
    assert respuesta.file_name == "contrato.pdf"


# --- R12: el texto del error de identificador es el de dev (hallazgo H1) ------


def _caso_con_repositorio_real(monkeypatch: pytest.MonkeyPatch) -> ReadDocumentUseCase:
    """Caso de uso sobre el adaptador real; la validacion corta antes de conectar."""

    def prohibido(*_: Any, **__: Any) -> None:
        raise AssertionError("un unit test no puede abrir una conexión real")

    monkeypatch.setattr(adaptador.pyodbc, "connect", prohibido)
    return ReadDocumentUseCase(adaptador.SqlServerRepository(SimpleNamespace()))


def test_f010_r12_id_column_no_valido_conserva_su_texto(monkeypatch: pytest.MonkeyPatch) -> None:
    caso = _caso_con_repositorio_real(monkeypatch)
    with pytest.raises(IdentifierValidationError) as info:
        caso.run(peticion(id_column=" ide;x ", id_value=1))
    # Texto literal de dev (read_document validaba con field_name="id_column").
    assert str(info.value) == "El identificador 'id_column' contiene caracteres no permitidos: ide;x"


def test_f010_r10_key_no_valida_informa_key(monkeypatch: pytest.MonkeyPatch) -> None:
    caso = _caso_con_repositorio_real(monkeypatch)
    with pytest.raises(IdentifierValidationError) as info:
        caso.run(peticion(key={"emp": 1, "co;d": "x"}))
    assert str(info.value) == "El identificador 'key' contiene caracteres no permitidos: co;d"
