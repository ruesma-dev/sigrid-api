# tests/test_f007_route.py
"""
F-007 T16 · R5, R6: la ruta `POST /api/sigrid/proforma`.

Registrada junto a las demas; valida con `ProformaRequest` (400 de F-012 sin
`codigo`); la llave `SIGRID_PROFORMA_WRITE_ENABLED` solo con `commit` y ANTES
del caso de uso; `ProformaError` -> 400 con `codigo`, `lineas` (con
`candidatos`) y `reparto`; lo inesperado, 500. El caso de uso se construye en
la ruta con el repositorio y los settings de `build_dependencies`, sin tocar su
tupla.

Sin red ni base de datos: se dobla `build_dependencies` y, segun el test, el
caso de uso o el repositorio (`f007_dobles`).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func
import pytest
from f007_dobles import RepositorioProforma, SettingsProforma, peticion
from f009_dobles import AHORA

import function_app
from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.proforma_models import (
    FalloLineaProforma,
    ProformaError,
    ProformaRequest,
)


class RepositorioIntocable:
    """Cualquier uso del repositorio hace fallar el test (`sin leer la base`)."""

    def __getattr__(self, nombre: str) -> Any:
        raise AssertionError(f"no se debia tocar el repositorio ({nombre})")


def dependencias(
    monkeypatch: pytest.MonkeyPatch, *, settings: Any = None, repositorio: Any = None
) -> tuple[Any, Any]:
    settings = settings or SettingsProforma()
    repositorio = repositorio or RepositorioIntocable()
    tupla = (settings, repositorio, None, None, None, None, None, None)
    monkeypatch.setattr(function_app, "build_dependencies", lambda: tupla)
    return settings, repositorio


def con_caso_de_uso(
    monkeypatch: pytest.MonkeyPatch, *, respuesta: Any = None, lanza: BaseException | None = None
) -> list[Any]:
    construidos: list[Any] = []

    class CasoDoble:
        def __init__(self, repository: Any, settings: Any) -> None:
            construidos.append((repository, settings))

        def run(self, request: Any) -> Any:
            construidos.append(request)
            if lanza is not None:
                raise lanza
            return respuesta if respuesta is not None else {"ok": True, "doble": True}

    monkeypatch.setattr(function_app, "CreateProformaUseCase", CasoDoble)
    return construidos


def llamar(cuerpo: Any, *, crudo: bytes | None = None) -> tuple[int, dict[str, Any]]:
    funcion = function_app.sigrid_proforma._function.get_user_function()
    respuesta = funcion(func.HttpRequest(
        method="POST", url="/api/sigrid/proforma",
        body=crudo if crudo is not None else json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json"},
    ))
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def test_f007_r6_la_ruta_esta_registrada_y_las_anteriores_siguen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # `get_functions()` no es idempotente (ver test_f006_route): se vacia aqui.
    monkeypatch.setattr(function_app.app, "functions_bindings", {})
    funciones = {f.get_function_name(): f for f in function_app.app.get_functions()}
    assert "sigrid_proforma" in funciones
    disparador = funciones["sigrid_proforma"].get_trigger()
    assert (disparador.route, [str(m) for m in disparador.methods]) == ("sigrid/proforma", ["POST"])
    for anterior in ("sql_read", "sql_write", "sigrid_contrato_lineas", "sigrid_albaran",
                     "sigrid_albaran_directo", "sigrid_concepto_grafico",
                     "sigrid_partes_reclamacion", "documents_read", "diagnostics_tcp"):
        assert anterior in funciones


def test_f007_r6_valida_y_construye_el_caso_de_uso_en_la_ruta(monkeypatch: pytest.MonkeyPatch) -> None:
    settings, repositorio = dependencias(monkeypatch)
    construidos = con_caso_de_uso(monkeypatch)
    estado, cuerpo = llamar(peticion())
    assert (estado, cuerpo) == (200, {"ok": True, "doble": True})
    (repo, ajustes), recibida = construidos
    assert (repo, ajustes) == (repositorio, settings)
    assert type(recibida) is ProformaRequest and recibida.referencia_externa == "PRF-1001"


@pytest.mark.parametrize(
    "cuerpo",
    [{}, {**peticion(), "periodo": "202608"}, {**peticion(), "lineas": []},
     {**peticion(), "campo_raro": 1},
     {**peticion(), "cod_contrato": None, "nombre_proveedor": None, "cif_proveedor": None}],
    ids=["vacio", "periodo_texto", "sin_lineas", "campo_de_mas", "sin_contrato_ni_proveedor"],
)
def test_f007_r1_r6_peticion_invalida_400_de_f012_sin_codigo(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any]
) -> None:
    dependencias(monkeypatch)
    construidos = con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(cuerpo)
    assert estado == 400
    assert respuesta["error"] == "Solicitud invalida."
    assert respuesta["details"]["type"] == "ValidationError"
    assert "codigo" not in respuesta["details"]
    assert construidos == []


def test_f007_r6_validacion_sin_valores_en_la_traza(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    dependencias(monkeypatch)
    con_caso_de_uso(monkeypatch)
    with caplog.at_level(logging.WARNING):
        llamar({**peticion(), "importe_mes": "17024.28", "nombre_proveedor": "X" * 200})
    texto = " ".join(r.getMessage() for r in caplog.records)
    assert "sigrid/proforma" in texto
    assert "17024" not in texto and "XXXX" not in texto


def test_f007_r6_cuerpo_que_no_es_json_400(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch)
    construidos = con_caso_de_uso(monkeypatch)
    estado, _respuesta = llamar(None, crudo=b"{no es json")
    assert estado == 400
    assert construidos == []


def test_f007_r5_commit_con_la_llave_cerrada_antes_del_caso_de_uso(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencias(monkeypatch, settings=SettingsProforma(sigrid_proforma_write_enabled=False))
    construidos = con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(peticion(commit=True))
    assert estado == 400
    assert respuesta["details"]["codigo"] == "escritura_proformas_deshabilitada"
    assert respuesta["details"]["type"] == "ProformaError"
    assert construidos == []


def test_f007_r5_la_llave_del_albaran_no_abre_la_proforma(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch, settings=SettingsProforma(
        sigrid_proforma_write_enabled=False, sigrid_albaran_write_enabled=True))
    con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(peticion(commit=True))
    assert (estado, respuesta["details"]["codigo"]) == (400, "escritura_proformas_deshabilitada")


def test_f007_r5_el_dry_run_no_cambia_con_la_llave_cerrada(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch, settings=SettingsProforma(sigrid_proforma_write_enabled=False))
    construidos = con_caso_de_uso(monkeypatch)
    estado, _respuesta = llamar(peticion(commit=False))
    assert estado == 200
    assert len(construidos) == 2


def test_f007_r6_proforma_error_400_con_codigo_y_lineas_con_candidatos(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencias(monkeypatch)
    fallos = [FalloLineaProforma(indice=0, referencia_linea="M09", codigo="linea_ambigua",
                                 mensaje="varias", candidatos=[271001, 271002])]
    con_caso_de_uso(monkeypatch, lanza=ProformaError("1 linea", codigo="lineas_no_validas",
                                                     lineas=fallos))
    estado, respuesta = llamar(peticion())
    assert estado == 400
    assert respuesta["details"]["codigo"] == "lineas_no_validas"
    assert respuesta["details"]["lineas"] == [{
        "indice": 0, "referencia_linea": "M09", "codigo": "linea_ambigua", "mensaje": "varias",
        "candidatos": [271001, 271002],
    }]
    assert "reparto" not in respuesta["details"]


def test_f007_r6_hoja_de_varios_contratos_400_con_reparto(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch)
    reparto = {"F09": "CTSB26/0472", "N10": "CTSB26/0369"}
    con_caso_de_uso(monkeypatch, lanza=ProformaError(
        "dos contratos", codigo="hoja_de_varios_contratos", reparto=reparto))
    estado, respuesta = llamar(peticion())
    assert estado == 400
    assert (respuesta["details"]["codigo"], respuesta["details"]["reparto"]) == (
        "hoja_de_varios_contratos", reparto)
    assert "lineas" not in respuesta["details"]


def test_f007_r6_error_de_negocio_se_traza_solo_con_codigos(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    dependencias(monkeypatch)
    con_caso_de_uso(monkeypatch, lanza=ProformaError(
        "Las lineas suman 17024.28 y el importe del mes es 1.00.", codigo="importe_mes_no_cuadra"))
    with caplog.at_level(logging.WARNING):
        llamar(peticion())
    texto = " ".join(r.getMessage() for r in caplog.records)
    assert "importe_mes_no_cuadra" in texto and "17024" not in texto


def test_f007_r6_inesperado_500(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch)
    con_caso_de_uso(monkeypatch, lanza=RuntimeError("se cayo"))
    estado, respuesta = llamar(peticion())
    assert estado == 500
    assert respuesta["details"]["type"] == "RuntimeError"
    assert respuesta["error"] == "Error interno ejecutando sigrid/proforma."


def test_f007_r6_de_punta_a_punta_con_el_doble_existente(monkeypatch: pytest.MonkeyPatch) -> None:
    """La ruta con el caso de uso REAL y el repositorio doble: la hoja de agosto
    de CTSB26/0472 da `existente` con sus lineas."""
    dependencias(monkeypatch, repositorio=RepositorioProforma())
    monkeypatch.setattr(
        function_app, "CreateProformaUseCase",
        lambda repo, settings: CreateProformaUseCase(repo, settings, ahora_utc=lambda: AHORA),
    )
    estado, respuesta = llamar(peticion())
    assert estado == 200
    assert (respuesta["estado"], respuesta["cod"], respuesta["con_ide"]) == (
        "existente", "AC26/25548", 2831541)
    assert respuesta["contrato"]["resuelto_por"] == "proveedor"
    assert respuesta["origen"]["porcentaje_contrato"] == 30.3
    assert [l["dcapro_ide"] for l in respuesta["lineas"]][:2] == [1352729, 1352731]
