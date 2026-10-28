# tests/test_f016_route.py
"""
F-016 T12 · R3, R4: la ruta `POST /api/sigrid/proforma` a origen.

La llave `SIGRID_PROFORMA_ORIGEN_ENABLED` solo con `commit` y `modo` `origen`,
DESPUES de la de F-007 (R5) y ANTES del caso de uso; los codigos nuevos, 400
con `details.codigo` (y `details.lineas` en `linea_anterior_no_valida`); las
combinaciones de R3, 400 de F-012 sin `codigo`. En mes nada cambia
(`tests/test_f007_route.py`, intacto, lo fija).

Sin red ni base de datos: se dobla `build_dependencies` y, segun el test, el
caso de uso o el repositorio (`f016_dobles`).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func
import pytest
from f007_dobles import DATOS, peticion
from f009_dobles import AHORA
from f016_dobles import PUNTA, RepositorioOrigen, SettingsOrigen

import function_app
from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.proforma_models import ProformaRequest
from domain.models.proforma_origen_models import (
    FalloLineaProformaOrigen,
    ProformaOrigenError,
)


class RepositorioIntocable:
    """Cualquier uso del repositorio hace fallar el test (`sin leer la base`)."""

    def __getattr__(self, nombre: str) -> Any:
        raise AssertionError(f"no se debia tocar el repositorio ({nombre})")


def dependencias(
    monkeypatch: pytest.MonkeyPatch, *, settings: Any = None, repositorio: Any = None
) -> None:
    tupla = (settings or SettingsOrigen(), repositorio or RepositorioIntocable(),
             None, None, None, None, None, None)
    monkeypatch.setattr(function_app, "build_dependencies", lambda: tupla)


def con_caso_de_uso(
    monkeypatch: pytest.MonkeyPatch, *, lanza: BaseException | None = None
) -> list[Any]:
    construidos: list[Any] = []

    class CasoDoble:
        def __init__(self, repository: Any, settings: Any) -> None:
            construidos.append((repository, settings))

        def run(self, request: Any) -> Any:
            construidos.append(request)
            if lanza is not None:
                raise lanza
            return {"ok": True, "doble": True}

    monkeypatch.setattr(function_app, "CreateProformaUseCase", CasoDoble)
    return construidos


def llamar(cuerpo: Any) -> tuple[int, dict[str, Any]]:
    funcion = function_app.sigrid_proforma._function.get_user_function()
    respuesta = funcion(func.HttpRequest(
        method="POST", url="/api/sigrid/proforma", body=json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json"},
    ))
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def a_origen(**cambios: Any) -> dict[str, Any]:
    return peticion(**{"modo": "origen", "proforma_anterior": PUNTA, **cambios})


# =====================================================================================
# R4 · la llave propia
# =====================================================================================


def test_f016_r4_commit_a_origen_con_la_llave_cerrada_antes_del_caso_de_uso(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencias(monkeypatch, settings=SettingsOrigen(sigrid_proforma_origen_enabled=False))
    construidos = con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(a_origen(commit=True))
    assert estado == 400
    assert respuesta["details"] == {"type": "ProformaOrigenError",
                                    "codigo": "escritura_proformas_origen_deshabilitada"}
    assert "SIGRID_PROFORMA_ORIGEN_ENABLED" in respuesta["error"]
    assert construidos == []


def test_f016_r4_va_despues_de_la_llave_de_f007(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch, settings=SettingsOrigen(
        sigrid_proforma_write_enabled=False, sigrid_proforma_origen_enabled=False))
    construidos = con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(a_origen(commit=True))
    assert (estado, respuesta["details"]["codigo"]) == (400, "escritura_proformas_deshabilitada")
    assert construidos == []


def test_f016_r4_la_de_origen_no_abre_la_de_proformas(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch, settings=SettingsOrigen(sigrid_proforma_write_enabled=False))
    con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(a_origen(commit=True))
    assert (estado, respuesta["details"]["codigo"]) == (400, "escritura_proformas_deshabilitada")


@pytest.mark.parametrize(
    ("cuerpo", "abierta"),
    [(a_origen(commit=True), True), (a_origen(commit=False), False),
     (peticion(commit=True), False), (peticion(modo="mes", commit=True), False)],
    ids=["commit_a_origen_abierta", "previa_a_origen_cerrada", "commit_de_mes_cerrada",
         "commit_mes_explicito_cerrada"],
)
def test_f016_r4_solo_cierra_el_commit_a_origen(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any], abierta: bool
) -> None:
    dependencias(monkeypatch, settings=SettingsOrigen(sigrid_proforma_origen_enabled=abierta))
    construidos = con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(cuerpo)
    assert (estado, respuesta) == (200, {"ok": True, "doble": True})
    assert type(construidos[1]) is ProformaRequest


# =====================================================================================
# R3 · 400 de F-012 sin codigo
# =====================================================================================


@pytest.mark.parametrize(
    "cuerpo",
    [peticion(modo="origen"), peticion(proforma_anterior=PUNTA),
     peticion(modo="origen", primera_de_cadena=True, proforma_anterior=PUNTA),
     peticion(modo="trimestral"),
     a_origen(lineas=[{**l, "linea_anterior": 1400001} for l in DATOS["hojas"]["CTSB26/0472"]
                      ["lineas"][:2]])],
    ids=["origen_sin_anterior", "anterior_sin_modo", "las_dos", "modo_desconocido",
         "linea_anterior_repetida"],
)
def test_f016_r3_peticion_invalida_400_de_f012_sin_codigo(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any]
) -> None:
    dependencias(monkeypatch)
    construidos = con_caso_de_uso(monkeypatch)
    estado, respuesta = llamar(cuerpo)
    assert estado == 400
    assert respuesta["error"] == "Solicitud invalida."
    assert "codigo" not in respuesta["details"]
    assert construidos == []


# =====================================================================================
# Los codigos nuevos, 400 con `details.codigo`
# =====================================================================================


@pytest.mark.parametrize("codigo", ["anterior_no_valida", "anterior_con_sucesora"])
def test_f016_r20_errores_de_la_cadena_400_con_codigo(
    monkeypatch: pytest.MonkeyPatch, codigo: str
) -> None:
    dependencias(monkeypatch)
    con_caso_de_uso(monkeypatch, lanza=ProformaOrigenError("la cadena", codigo=codigo))
    estado, respuesta = llamar(a_origen())
    assert (estado, respuesta["details"]) == (400, {"type": "ProformaOrigenError", "codigo": codigo})


def test_f016_r9_linea_anterior_no_valida_400_con_sus_lineas(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    dependencias(monkeypatch)
    fallo = FalloLineaProformaOrigen(indice=4, referencia_linea="F21",
                                     codigo="linea_anterior_no_valida", mensaje="sin vincular")
    con_caso_de_uso(monkeypatch, lanza=ProformaOrigenError(
        "1 linea", codigo="lineas_no_validas", lineas=[fallo]))
    with caplog.at_level(logging.WARNING):
        estado, respuesta = llamar(a_origen())
    assert estado == 400
    assert respuesta["details"]["codigo"] == "lineas_no_validas"
    assert respuesta["details"]["lineas"] == [{
        "indice": 4, "referencia_linea": "F21", "codigo": "linea_anterior_no_valida",
        "mensaje": "sin vincular", "candidatos": [],
    }]
    assert "linea_anterior_no_valida" in " ".join(r.getMessage() for r in caplog.records)


def test_f016_r19_de_punta_a_punta_previa_encadenada(monkeypatch: pytest.MonkeyPatch) -> None:
    """La ruta con el caso de uso REAL y el repositorio doble: previa a origen
    con `cadena` y las arrastradas al final, con la llave de origen cerrada."""
    dependencias(monkeypatch, settings=SettingsOrigen(sigrid_proforma_origen_enabled=False),
                 repositorio=RepositorioOrigen())
    monkeypatch.setattr(
        function_app, "CreateProformaUseCase",
        lambda repo, settings: CreateProformaUseCase(repo, settings, ahora_utc=lambda: AHORA),
    )
    hoja = DATOS["hojas"]["CTSB26/0472"]["lineas"]
    lineas = [{**hoja[0], "linea_anterior": 1400001}, *hoja[1:]]
    estado, respuesta = llamar(a_origen(lineas=lineas))
    assert estado == 200
    assert (respuesta["estado"], respuesta["cabecera"]["docoritip"]) == ("previsto", 1)
    assert respuesta["cadena"]["anterior"] == {"cod": PUNTA, "ide": 2850201}
    assert respuesta["cadena"]["n_arrastradas"] == 4
    assert [l["arrastrada"] for l in respuesta["lineas"]] == [False] * 6 + [True] * 4
