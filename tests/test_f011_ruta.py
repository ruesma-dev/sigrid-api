# tests/test_f011_ruta.py
"""
F-011 · R1, R8, R9 y R11 en la ruta `POST /api/documents/read`.

Sin red ni base de datos: `build_dependencies` se dobla a la tupla de ocho con
el `ReadDocumentUseCase` REAL sobre un repositorio doble y unos ajustes doble.
Así se prueba la cadena entera (modelo → validación de la base → traducción a
HTTP) que vive en `function_app.py` y en el caso de uso.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import azure.functions as func
import pytest

import function_app
from application.use_cases.read_document_use_case import ReadDocumentUseCase
from domain.models.document_models import DocumentoAmbiguoError, RawDocumentRecord
from infrastructure.repositories import sql_server_repository as adaptador

_PDF = b"%PDF-1.4 binario"
_LISTA = ["ruesma", "ruesma_rep", "master"]

_CUERPO = {
    "database": "ruesma_rep",
    "table": "gra",
    "id_column": "ide",
    "id_value": 365617,
    "blob_column": "ima",
    "filename_columns": ["nomori"],
}


class RepositorioDoble:
    """Devuelve lo que diga `comportamiento`; registra cada llamada."""

    def __init__(self, comportamiento: Callable[[dict[str, Any]], RawDocumentRecord]) -> None:
        self._comportamiento = comportamiento
        self.llamadas: list[dict[str, Any]] = []

    def read_document(self, **kwargs: Any) -> RawDocumentRecord:
        self.llamadas.append(kwargs)
        return self._comportamiento(kwargs)


def revienta(_: dict[str, Any]) -> RawDocumentRecord:
    raise AssertionError("no debía llamarse a read_document")


def lanza(excepcion: Exception) -> Callable[[dict[str, Any]], RawDocumentRecord]:
    def comportamiento(_: dict[str, Any]) -> RawDocumentRecord:
        raise excepcion

    return comportamiento


def con_caso_real(monkeypatch: pytest.MonkeyPatch, repo: Any, lista: list[str] | None = None) -> None:
    ajustes = SimpleNamespace(allowed_databases=list(_LISTA if lista is None else lista))
    caso = ReadDocumentUseCase(repo, ajustes)
    monkeypatch.setattr(
        function_app, "build_dependencies", lambda: (ajustes, repo, None, caso, None, None, None, None)
    )


def llamar(cuerpo: dict[str, Any] | bytes) -> func.HttpResponse:
    ruta = function_app.documents_read._function.get_user_function()
    crudo = cuerpo if isinstance(cuerpo, bytes) else json.dumps(cuerpo).encode("utf-8")
    return ruta(func.HttpRequest(
        method="POST",
        url="/api/documents/read",
        body=crudo,
        headers={"Content-Type": "application/json"},
    ))


def cuerpo_de(respuesta: func.HttpResponse) -> dict[str, Any]:
    return json.loads(respuesta.get_body().decode("utf-8"))


# --- R1 y R8: 400 BaseNoPermitidaError ----------------------------------------


def test_f011_r1_base_no_permitida_da_400_con_cuerpo_exacto(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = RepositorioDoble(revienta)
    con_caso_real(monkeypatch, repo)
    respuesta = llamar({**_CUERPO, "database": "base_inexistente_f011"})
    assert respuesta.status_code == 400
    assert respuesta.mimetype == "application/json"
    assert cuerpo_de(respuesta) == {
        "ok": False,
        "error": "La base de datos 'base_inexistente_f011' no está permitida. "
        "Permitidas: ruesma, ruesma_rep, master",
        "details": {"type": "BaseNoPermitidaError"},
    }
    assert repo.llamadas == []


@pytest.mark.parametrize("database", ["ruesma_rep;APP=f011", "RUESMA_REP", "ruesma rep"])
def test_f011_r1_inyeccion_y_mayusculas_dan_400_base_no_permitida(
    monkeypatch: pytest.MonkeyPatch, database: str
) -> None:
    repo = RepositorioDoble(revienta)
    con_caso_real(monkeypatch, repo)
    respuesta = llamar({**_CUERPO, "database": database})
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["details"] == {"type": "BaseNoPermitidaError"}
    assert repo.llamadas == []


def test_f011_r4_lista_vacia_da_400_con_ninguna(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso_real(monkeypatch, RepositorioDoble(revienta), lista=[])
    respuesta = llamar(_CUERPO)
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["error"] == (
        "La base de datos 'ruesma_rep' no está permitida. Permitidas: (ninguna)"
    )


def test_f011_r8_el_tipo_nunca_es_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso_real(monkeypatch, RepositorioDoble(revienta))
    tipo = cuerpo_de(llamar({**_CUERPO, "database": "otra"}))["details"]["type"]
    assert tipo != "ValueError"
    assert tipo == "BaseNoPermitidaError"


# --- R9: warning de log -------------------------------------------------------


def test_f011_r9_el_rechazo_deja_un_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    con_caso_real(monkeypatch, RepositorioDoble(revienta), lista=["ruesma"])
    with caplog.at_level(logging.WARNING, logger="function_app"):
        llamar(_CUERPO)
    mensajes = [
        (registro.levelno, registro.getMessage())
        for registro in caplog.records
        if registro.name == "function_app"
    ]
    assert mensajes == [(
        logging.WARNING,
        "BaseNoPermitidaError en documents/read: "
        "La base de datos 'ruesma_rep' no está permitida. Permitidas: ruesma",
    )]


# --- R10 y R11: con la base permitida, todo como tras F-010 -------------------


def test_f011_r10_base_permitida_responde_200_como_hoy(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = RepositorioDoble(lambda _: RawDocumentRecord(file_name_candidates=["a b.pdf"], content=_PDF))
    con_caso_real(monkeypatch, repo)
    respuesta = llamar(_CUERPO)
    assert respuesta.status_code == 200
    assert respuesta.get_body() == _PDF
    assert respuesta.headers["X-Document-Size"] == str(len(_PDF))
    assert respuesta.headers["X-Document-Filename"] == "a b.pdf"
    assert respuesta.headers["Content-Disposition"] == "attachment; filename*=UTF-8''a%20b.pdf"
    assert repo.llamadas[0]["database"] == "ruesma_rep"


def test_f011_r11_cuerpo_mal_formado_sigue_en_validation_error(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso_real(monkeypatch, RepositorioDoble(revienta))
    respuesta = llamar({k: v for k, v in _CUERPO.items() if k != "table"})
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["error"] == "Solicitud invalida."
    assert cuerpo_de(respuesta)["details"]["type"] == "ValidationError"


def test_f011_r11_identificador_no_valido_sigue_en_400_con_su_texto(monkeypatch: pytest.MonkeyPatch) -> None:
    def prohibido(*_: Any, **__: Any) -> None:
        raise AssertionError("un unit test no puede abrir una conexión real")

    monkeypatch.setattr(adaptador.pyodbc, "connect", prohibido)
    con_caso_real(monkeypatch, adaptador.SqlServerRepository(SimpleNamespace()))
    respuesta = llamar({**_CUERPO, "table": "gra;x"})
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta) == {
        "ok": False,
        "error": "El identificador 'table' contiene caracteres no permitidos: gra;x",
        "details": {"type": "IdentifierValidationError"},
    }


def test_f011_r11_sin_binario_sigue_en_400_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    texto = "No existe ninguna fila en [dbo].[gra] con ide=365617."
    con_caso_real(monkeypatch, RepositorioDoble(lanza(ValueError(texto))))
    respuesta = llamar(_CUERPO)
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta) == {"ok": False, "error": texto, "details": {"type": "ValueError"}}


def test_f011_r11_ambiguedad_sigue_en_409(monkeypatch: pytest.MonkeyPatch) -> None:
    texto = "La localizacion casa con mas de una fila en [dbo].[gra] (ide=365617): no se sirve ninguna."
    con_caso_real(monkeypatch, RepositorioDoble(lanza(DocumentoAmbiguoError(texto))))
    respuesta = llamar(_CUERPO)
    assert respuesta.status_code == 409
    assert cuerpo_de(respuesta) == {"ok": False, "error": texto, "details": {"type": "DocumentoAmbiguoError"}}


def test_f011_r11_error_inesperado_sigue_en_500(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso_real(monkeypatch, RepositorioDoble(lanza(RuntimeError("boom"))))
    respuesta = llamar(_CUERPO)
    assert respuesta.status_code == 500
    assert cuerpo_de(respuesta) == {
        "ok": False,
        "error": "Error interno ejecutando documents/read.",
        "details": {"type": "RuntimeError", "exception": "boom"},
    }
