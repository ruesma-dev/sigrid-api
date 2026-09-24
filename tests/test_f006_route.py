# tests/test_f006_route.py
"""
F-006 · R2 y R3: la ruta `POST /api/sigrid/partes-reclamacion`.

Sin red y sin base de datos: se doblan `build_dependencies` (que leería el
entorno) y el caso de uso. Lo que vive en `function_app.py` es SOLO la
traducción de excepciones a HTTP, y eso es lo que se comprueba.
"""
from __future__ import annotations

import json
from typing import Any

import azure.functions as func
import pytest

import function_app
from domain.models.parte_reclamacion_models import (
    CreatePartesReclamacionResponse,
    ParteReclamacionError,
    ResultadoParte,
)

_CUERPO = {
    "database": "ruesma",
    "obra": "0626",
    "usu": "prueba",
    "partes": [
        {
            "referencia_externa": "PVI-PRUEBA-0001",
            "unidad_postventa": "0626.03PORTAL 1.1.A",
            "descripcion": "PRUEBA API - ANULAR",
            "oficio": "0039",
            "intervinientes": [{"oficio": "0039", "proveedor": "1181"}],
        }
    ],
}


def ruta() -> Any:
    return function_app.sigrid_partes_reclamacion._function.get_user_function()


def peticion_http(cuerpo: Any = None, *, crudo: bytes | None = None) -> func.HttpRequest:
    return func.HttpRequest(
        method="POST",
        url="/api/sigrid/partes-reclamacion",
        body=crudo if crudo is not None else json.dumps(_CUERPO if cuerpo is None else cuerpo).encode(),
        headers={"Content-Type": "application/json"},
    )


@pytest.fixture(autouse=True)
def _sin_entorno(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        function_app, "build_dependencies", lambda: ("ajustes", "repositorio") + (None,) * 5
    )


def con_caso_de_uso(monkeypatch: pytest.MonkeyPatch, comportamiento: Any) -> list[Any]:
    construidos: list[Any] = []

    class CasoDoble:
        def __init__(self, repository: Any, settings: Any) -> None:
            construidos.append((repository, settings))

        def run(self, request: Any) -> Any:
            construidos.append(request)
            return comportamiento(request)

    monkeypatch.setattr(function_app, "CreatePartesReclamacionUseCase", CasoDoble)
    return construidos


def cuerpo_de(respuesta: func.HttpResponse) -> dict[str, Any]:
    return json.loads(respuesta.get_body().decode("utf-8"))


def test_f006_r2_la_ruta_esta_registrada_y_las_anteriores_siguen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `get_functions()` del SDK no es idempotente: apunta los nombres en
    # `functions_bindings` y a la segunda llamada del proceso (la primera la
    # hace test_f004_route) los da por duplicados. Se vacía solo en este test.
    monkeypatch.setattr(function_app.app, "functions_bindings", {})
    nombres = [f.get_function_name() for f in function_app.app.get_functions()]
    assert "sigrid_partes_reclamacion" in nombres
    for anterior in ("sql_read", "sql_write", "sigrid_contrato_lineas", "sigrid_albaran",
                     "sigrid_albaran_directo", "sigrid_concepto_grafico", "documents_read",
                     "diagnostics_tcp"):
        assert anterior in nombres


def test_f006_r2_un_lote_con_partes_rechazados_responde_200(monkeypatch: pytest.MonkeyPatch) -> None:
    def responde(request: Any) -> CreatePartesReclamacionResponse:
        return CreatePartesReclamacionResponse(
            committed=False,
            dry_run=True,
            database=request.database,
            obra={"ide": 1758465, "cod": "0626", "emp": 1},
            resumen={"rechazados": 1},
            partes=[
                ResultadoParte(
                    indice=0,
                    referencia_externa="PVI-PRUEBA-0001",
                    estado="rechazado",
                    motivo={"codigo": "tipo_no_valido", "mensaje": "No existe."},
                )
            ],
        )

    construidos = con_caso_de_uso(monkeypatch, responde)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 200
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["ok"] is True
    assert cuerpo["partes"][0]["motivo"]["codigo"] == "tipo_no_valido"
    assert construidos[0] == ("repositorio", "ajustes")
    assert construidos[1].partes[0].referencia_externa == "PVI-PRUEBA-0001"
    assert construidos[1].commit is False


def test_f006_r3_un_fallo_del_lote_sale_como_400_con_su_codigo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falla(_request: Any) -> Any:
        raise ParteReclamacionError("No existe la obra.", codigo="obra_no_encontrada")

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 400
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["ok"] is False
    assert cuerpo["error"] == "No existe la obra."
    assert cuerpo["details"] == {"type": "ParteReclamacionError", "codigo": "obra_no_encontrada"}


@pytest.mark.parametrize(
    "cuerpo",
    [
        {**_CUERPO, "partes": []},
        {**_CUERPO, "ide": 1},
        {k: v for k, v in _CUERPO.items() if k != "obra"},
        {**_CUERPO, "partes": [{**_CUERPO["partes"][0], "forma_comunicacion": 2}]},
    ],
)
def test_f006_r1_un_cuerpo_invalido_sale_como_400_solicitud_invalida(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any]
) -> None:
    con_caso_de_uso(monkeypatch, lambda _request: pytest.fail("no deberia llegar al caso de uso"))
    respuesta = ruta()(peticion_http(cuerpo))

    assert respuesta.status_code == 400
    salida = cuerpo_de(respuesta)
    assert salida["error"] == "Solicitud invalida."
    assert salida["details"]["type"] == "ValidationError"
    assert salida["details"]["validation"]


def test_f006_r3_un_json_roto_sale_como_400(monkeypatch: pytest.MonkeyPatch) -> None:
    con_caso_de_uso(monkeypatch, lambda _request: pytest.fail("no deberia llegar al caso de uso"))
    respuesta = ruta()(peticion_http(crudo=b"{no es json"))
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["details"]["type"] == "JSONDecodeError"  # un ValueError


def test_f006_r3_una_lectura_truncada_sale_como_400(monkeypatch: pytest.MonkeyPatch) -> None:
    def falla(_request: Any) -> Any:
        raise ValueError("Una lectura devolvio mas filas de las que se pueden traer (truncada)")

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())
    assert respuesta.status_code == 400
    assert cuerpo_de(respuesta)["details"] == {"type": "ValueError"}


def test_f006_r3_lo_inesperado_sale_como_500_con_la_excepcion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def falla(_request: Any) -> Any:
        raise RuntimeError("se cayo la red")

    con_caso_de_uso(monkeypatch, falla)
    respuesta = ruta()(peticion_http())

    assert respuesta.status_code == 500
    cuerpo = cuerpo_de(respuesta)
    assert cuerpo["error"] == "Error interno ejecutando sigrid/partes-reclamacion."
    assert cuerpo["details"] == {"type": "RuntimeError", "exception": "se cayo la red"}
