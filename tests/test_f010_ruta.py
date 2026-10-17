# tests/test_f010_ruta.py
"""
F-010 · R5, R7, R8, R10, R13 y R14 en la ruta `POST /api/documents/read`.

Sin red ni base de datos: `build_dependencies` se dobla a una tupla de ocho
con el caso de uso doblado en su sitio (patrón de `tests/test_f004_route.py`).
Lo que se comprueba es la traducción a HTTP, que vive en `function_app.py`.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import azure.functions as func
import pytest

import function_app
from domain.models.document_models import DocumentoAmbiguoError
from domain.models.sql_models import DocumentReadResponse
from infrastructure.security.identifier_guard import IdentifierValidationError

_PDF = b"%PDF-1.4 binario"

_CUERPO_IDE = {
    "database": "ruesma_rep",
    "table": "gra",
    "id_column": "ide",
    "id_value": 365617,
    "blob_column": "ima",
    "filename_columns": ["nomori"],
}


class CasoDoble:
    def __init__(self, comportamiento: Callable[[Any], Any]) -> None:
        self._comportamiento = comportamiento
        self.peticiones: list[Any] = []

    def run(self, request: Any) -> Any:
        self.peticiones.append(request)
        return self._comportamiento(request)


def con_caso(monkeypatch: pytest.MonkeyPatch, comportamiento: Callable[[Any], Any]) -> CasoDoble:
    caso = CasoDoble(comportamiento)
    monkeypatch.setattr(function_app, "build_dependencies", lambda: (None, None, None, caso, None, None, None, None))
    return caso


def llamar(cuerpo: dict[str, Any]) -> func.HttpResponse:
    ruta = function_app.documents_read._function.get_user_function()
    return ruta(func.HttpRequest(
        method="POST",
        url="/api/documents/read",
        body=json.dumps(cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    ))


def cuerpo_de(respuesta: func.HttpResponse) -> dict[str, Any]:
    return json.loads(respuesta.get_body().decode("utf-8"))


def lanza(excepcion: Exception) -> Callable[[Any], Any]:
    def comportamiento(_: Any) -> Any:
        raise excepcion

    return comportamiento


# --- R5: nombre no ASCII → 200 con cabeceras codificadas ----------------------


def test_f010_r5_nombre_no_ascii_responde_200_con_cabeceras_exactas(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso(monkeypatch, lambda _: DocumentReadResponse(
        file_name="Factura año señal.pdf", content_type="application/pdf",
        size_bytes=len(_PDF), content=_PDF,
    ))
    respuesta = llamar(_CUERPO_IDE)
    assert respuesta.status_code == 200
    assert respuesta.get_body() == _PDF
    assert respuesta.headers["X-Document-Filename"] == "Factura a%C3%B1o se%C3%B1al.pdf"
    assert respuesta.headers["Content-Disposition"] == (
        "attachment; filename*=UTF-8''Factura%20a%C3%B1o%20se%C3%B1al.pdf"
    )
    assert respuesta.headers["X-Document-Size"] == str(len(_PDF))


def test_f010_r5_inline_se_respeta(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso(monkeypatch, lambda _: DocumentReadResponse(
        file_name="a b.pdf", content_type="application/pdf", size_bytes=len(_PDF), content=_PDF,
    ))
    respuesta = llamar({**_CUERPO_IDE, "disposition": "inline"})
    assert respuesta.headers["Content-Disposition"] == "inline; filename*=UTF-8''a%20b.pdf"
    assert respuesta.headers["X-Document-Filename"] == "a b.pdf"


def test_f010_r12_la_peticion_por_key_llega_al_caso_de_uso(monkeypatch: pytest.MonkeyPatch) -> None:
    caso = con_caso(monkeypatch, lambda _: DocumentReadResponse(
        file_name="a.pdf", content_type="application/pdf", size_bytes=len(_PDF), content=_PDF,
    ))
    cuerpo = {k: v for k, v in _CUERPO_IDE.items() if k not in ("id_column", "id_value")}
    respuesta = llamar({**cuerpo, "key": {"emp": 1, "cod": "ABC"}})
    assert respuesta.status_code == 200
    assert caso.peticiones[0].localizacion() == {"emp": 1, "cod": "ABC"}


# --- R7 y R8: 400 ValidationError sin llegar al caso de uso -------------------


@pytest.mark.parametrize(
    "cambios",
    [
        {"key": {"emp": 1, "cod": "ABC"}},                     # key con id_column e id_value (R7)
        {"id_column": None, "id_value": None, "_quitar": ["id_column", "id_value"]},  # ninguna (R8)
        {"_quitar": ["id_value"]},                              # id_column sin id_value (R8)
        {"_quitar": ["id_column"]},                             # id_value sin id_column (R8)
        {"_quitar": ["id_column", "id_value"], "key": {}},      # key vacía (R9)
        {"_quitar": ["id_column", "id_value"], "key": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}},
    ],
)
def test_f010_r7_r8_localizacion_invalida_da_400_validation_error(
    monkeypatch: pytest.MonkeyPatch, cambios: dict[str, Any]
) -> None:
    caso = con_caso(monkeypatch, lambda _: pytest.fail("no debía llegar al caso de uso"))
    cambios = dict(cambios)
    quitar = cambios.pop("_quitar", [])
    cuerpo = {k: v for k, v in {**_CUERPO_IDE, **cambios}.items() if k not in quitar}
    respuesta = llamar(cuerpo)
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["error"] == "Solicitud invalida."
    assert cuerpo_de(respuesta)["details"]["type"] == "ValidationError"
    assert caso.peticiones == []


# --- R10: nombre de key no válido ---------------------------------------------


def test_f010_r10_identificador_no_valido_da_400_con_su_tipo(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso(monkeypatch, lanza(IdentifierValidationError("El identificador 'key' contiene caracteres no permitidos: a]")))
    respuesta = llamar(_CUERPO_IDE)
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["details"] == {"type": "IdentifierValidationError"}


# --- R13: ambigüedad → 409, nunca ValueError ----------------------------------


def test_f010_r13_ambiguedad_da_409_documento_ambiguo(monkeypatch: pytest.MonkeyPatch) -> None:
    texto = "La localizacion casa con mas de una fila en [dbo].[gra] (emp=1): no se sirve ninguna."
    con_caso(monkeypatch, lanza(DocumentoAmbiguoError(texto)))
    respuesta = llamar({**_CUERPO_IDE, "id_column": "emp", "id_value": 1})
    assert respuesta.status_code == 409
    assert cuerpo_de(respuesta) == {"ok": False, "error": texto, "details": {"type": "DocumentoAmbiguoError"}}
    assert respuesta.mimetype == "application/json"


def test_f010_r13_el_tipo_nunca_es_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso(monkeypatch, lanza(DocumentoAmbiguoError("x")))
    assert cuerpo_de(llamar(_CUERPO_IDE))["details"]["type"] != "ValueError"


# --- R14: sin fila o BLOB vacío, sin cambios ----------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "No existe ninguna fila en [dbo].[gra] con ide=365617.",
        "La columna ima esta vacia para ide=365617.",
    ],
)
def test_f010_r14_sin_fila_o_blob_vacio_sigue_en_400_value_error(
    monkeypatch: pytest.MonkeyPatch, texto: str
) -> None:
    con_caso(monkeypatch, lanza(ValueError(texto)))
    respuesta = llamar(_CUERPO_IDE)
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta) == {"ok": False, "error": texto, "details": {"type": "ValueError"}}


def test_f010_r12_error_inesperado_sigue_en_500(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso(monkeypatch, lanza(RuntimeError("boom")))
    respuesta = llamar(_CUERPO_IDE)
    assert respuesta.status_code == 500
    assert cuerpo_de(respuesta)["details"] == {"type": "RuntimeError", "exception": "boom"}
