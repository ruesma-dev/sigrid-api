# tests/test_f004_route.py
"""
F-004 · R3: la ruta `POST /api/sigrid/concepto-grafico` y sus codigos de error.

Sin red y sin base de datos: se doblan `build_dependencies` (que leeria el
entorno) y el caso de uso. Lo que se comprueba aqui es SOLO la traduccion de
excepciones a HTTP, que es lo unico que vive en `function_app.py`.
"""
from __future__ import annotations

import base64
import json
from typing import Any

import azure.functions as func
import pyodbc
import pytest

import function_app
from domain.models.concepto_grafico_models import ConceptoGraficoError

_CUERPO = {
    "database": "ruesma",
    "conide": 2811179,
    "contip": 708,
    "gratipide": 35,
    "res": "PRUEBA API - BORRAR",
    "nom": "parte.pdf",
    "usu": "aechevarria",
    "contenido_base64": base64.b64encode(b"%PDF-1.4 hola").decode("ascii"),
}


def ruta() -> Any:
    return function_app.sigrid_concepto_grafico._function.get_user_function()


def peticion_http(cuerpo: dict[str, Any] | None = None) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="/api/sigrid/concepto-grafico",
        body=json.dumps(_CUERPO if cuerpo is None else cuerpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture(autouse=True)
def _sin_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(function_app, "build_dependencies", lambda: (None,) * 7)


def con_caso_de_uso(monkeypatch: pytest.MonkeyPatch, comportamiento: Any) -> None:
    class CasoDoble:
        def __init__(self, repository: Any, settings: Any) -> None:
            pass

        def run(self, request: Any) -> Any:
            return comportamiento(request)

    monkeypatch.setattr(function_app, "AttachConceptoGraficoUseCase", CasoDoble)


def cuerpo_de(respuesta: func.HttpResponse) -> dict[str, Any]:
    return json.loads(respuesta.get_body().decode("utf-8"))


# --- La ruta existe y no toca a las demas ------------------------------------


def test_f004_r3_la_ruta_esta_registrada_y_las_anteriores_siguen() -> None:
    nombres = [f.get_function_name() for f in function_app.app.get_functions()]
    assert "sigrid_concepto_grafico" in nombres
    for anterior in ("sql_read", "sql_write", "sigrid_contrato_lineas", "sigrid_albaran",
                     "sigrid_albaran_directo", "documents_read", "diagnostics_tcp"):
        assert anterior in nombres


# --- R3: cada fallo, con su codigo -------------------------------------------


def test_f004_r3_un_fallo_de_negocio_sale_como_400_con_su_codigo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falla(_request: Any) -> Any:
        raise ConceptoGraficoError(
            "La escritura documental esta desactivada.",
            codigo="escritura_documental_deshabilitada",
        )

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 400
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["ok"] is False
    assert cuerpo["error"] == "La escritura documental esta desactivada."
    assert cuerpo["details"]["codigo"] == "escritura_documental_deshabilitada"
    assert cuerpo["details"]["type"] == "ConceptoGraficoError"


def test_f004_r3_una_clave_duplicada_sale_como_400_colision_de_clave(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """El cliente tiene que saber que el ERP quedo SIN cambios y puede reintentar."""
    def falla(_request: Any) -> Any:
        raise pyodbc.IntegrityError("23000", "Violation of UNIQUE KEY constraint 'gra_empcod'")

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 400
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["details"]["codigo"] == "colision_de_clave"
    assert "sin cambios" in cuerpo["error"]


def test_f004_r3_un_cuerpo_invalido_sale_como_400_solicitud_invalida(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    con_caso_de_uso(monkeypatch, lambda _request: pytest.fail("no deberia llegar al caso de uso"))
    respuesta = ruta()(peticion_http({"database": "ruesma"}))

    assert respuesta.status_code == 400
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["error"] == "Solicitud invalida."
    assert cuerpo["details"]["type"] == "ValidationError"


def test_f004_r3_un_valueerror_sin_codigo_sigue_siendo_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falla(_request: Any) -> Any:
        raise ValueError("contenido_base64 no es base64 valido.")

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 400
    cuerpo = cuerpo_de(respuesta)
    assert "codigo" not in cuerpo["details"]


def test_f004_r3_lo_inesperado_sigue_siendo_500(monkeypatch: pytest.MonkeyPatch) -> None:
    def falla(_request: Any) -> Any:
        raise RuntimeError("el driver exploto")

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 500
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["details"]["type"] == "RuntimeError"
    assert cuerpo["details"]["exception"] == "el driver exploto"


# --- El camino feliz ---------------------------------------------------------


def test_f004_r2_una_respuesta_correcta_sale_como_200_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from domain.models.concepto_grafico_models import (
        AttachConceptoGraficoResponse,
        ConceptoPreview,
        EnlacePreview,
        GraficoPreview,
    )

    def responde(request: Any) -> Any:
        assert request.commit is False        # el defecto llega hasta el caso de uso
        assert request.database == "ruesma"
        return AttachConceptoGraficoResponse(
            committed=False, dry_run=True, idempotente=False,
            database="ruesma", database_documental="ruesma_rep",
            concepto=ConceptoPreview(ide=2811179, tip=708, emp=1, cod="RS26.08/0123"),
            grafico=GraficoPreview(
                cod="202609051230451101.aechevarria", emp=1, nom="parte.pdf",
                fec=20260905, usu="aechevarria", res="PRUEBA", gratipide=35, vin=3,
                bytes=13, sha256="a" * 64, content_type="application/pdf",
            ),
            enlace=EnlacePreview(con=2811179, pos=64),
            filas_afectadas=0,
        )

    con_caso_de_uso(monkeypatch, responde)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 200
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["ok"] is True
    assert cuerpo["dry_run"] is True
    assert cuerpo["grafico"]["sha256"] == "a" * 64


# --- R3: de que posiciones de `build_dependencies` sale cada dependencia -----


def test_f004_r3_la_ruta_toma_settings_y_repositorio_de_las_dos_primeras_posiciones(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    `build_dependencies()` devuelve una tupla de siete: `deps[0]` es `Settings`
    y `deps[1]` el repositorio; las otras cinco son casos de uso de endpoints
    anteriores. Coger otra posicion construiria el caso de uso con el objeto
    equivocado y solo se veria en produccion.
    """
    dependencias = tuple(f"dep{indice}" for indice in range(7))
    monkeypatch.setattr(function_app, "build_dependencies", lambda: dependencias)
    recibido: dict[str, Any] = {}

    class CasoDoble:
        def __init__(self, repository: Any, settings: Any) -> None:
            recibido["repository"] = repository
            recibido["settings"] = settings

        def run(self, request: Any) -> Any:
            raise ConceptoGraficoError("no hace falta llegar", codigo="usuario_no_valido")

    monkeypatch.setattr(function_app, "AttachConceptoGraficoUseCase", CasoDoble)
    ruta()(peticion_http())

    assert recibido == {"repository": "dep1", "settings": "dep0"}
