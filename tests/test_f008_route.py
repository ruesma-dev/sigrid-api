# tests/test_f008_route.py
"""
F-008 T16 · la ruta `POST /api/sigrid/factura`: cuerpo invalido sin eco (R1),
llave propia tras validar el cuerpo y antes del caso de uso (R4), fallos de
negocio con `details.codigo` (R44) y traza sin datos sensibles (R46).

Sin red y sin base de datos: se dobla `build_dependencies` y el caso de uso se
construye con el repositorio doble de `tests/f008_dobles.py` y un reloj fijo.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func
import pytest
from f008_dobles import (
    AHORA,
    AjustesFactura,
    Repositorio,
    ajustes_de_escritura,
    con_transaccion,
    peticion,
)

import function_app
from application.use_cases.create_factura_use_case import CreateFacturaUseCase
from domain.models.factura_models import FacturaError, FacturaRequest

#: Lo que nunca puede salir en una traza (R46): CIF, numero, referencia,
#: razon social, importes y cuentas del ERP de mentira.
SENSIBLES = ("B00000001", "F-77", "FAC-1", "PROVEEDOR UNO", "24.2", "4.2", "4009", "4001")


class Intocable:
    def __getattr__(self, nombre: str) -> Any:
        raise AssertionError(f"no se debia tocar el repositorio ({nombre})")


def _dependencias(monkeypatch: pytest.MonkeyPatch, settings: Any, repositorio: Any) -> list[Any]:
    creados: list[Any] = []

    def fabrica(repo: Any, ajustes: Any) -> CreateFacturaUseCase:
        caso = CreateFacturaUseCase(repo, ajustes, ahora_utc=lambda: AHORA)
        creados.append(caso)
        return caso

    monkeypatch.setattr(function_app, "build_dependencies", lambda: (settings, repositorio))
    monkeypatch.setattr(function_app, "CreateFacturaUseCase", fabrica)
    return creados


def _llamar(cuerpo: Any) -> tuple[int, dict[str, Any]]:
    funcion = function_app.sigrid_factura._function.get_user_function()
    respuesta = funcion(func.HttpRequest(
        method="POST", url="/api/sigrid/factura", body=json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json"},
    ))
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def test_f008_r3_previa_por_la_ruta(monkeypatch: pytest.MonkeyPatch) -> None:
    _dependencias(monkeypatch, AjustesFactura(), Repositorio())
    estado, cuerpo = _llamar(peticion())
    assert estado == 200 and cuerpo["estado"] == "previsto" and cuerpo["cod"] == "FR26/00042"


def test_f008_r36_commit_por_la_ruta(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = con_transaccion(Repositorio())
    _dependencias(monkeypatch, ajustes_de_escritura(), repo)
    estado, cuerpo = _llamar(peticion(commit=True))
    assert estado == 200 and cuerpo["estado"] == "creado" and cuerpo["committed"] is True
    assert len(repo.mundo.insertadas["dcf"]) == 1


@pytest.mark.parametrize("cambio", [
    {"total_base": "20"}, {"sobra": 1}, {"serie": "FX"}, {"origenes": [], "lineas": []},
    {"commit": "true"}, {"fecha_factura": 20261332},
])
def test_f008_r1_cuerpo_invalido_sin_eco_ni_codigo(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, cambio: dict[str, Any]
) -> None:
    _dependencias(monkeypatch, AjustesFactura(), Intocable())
    with caplog.at_level(logging.INFO):
        estado, cuerpo = _llamar(peticion(**cambio))
    assert estado == 400 and cuerpo["error"] == "Solicitud invalida."
    assert "codigo" not in json.dumps(cuerpo)
    assert cuerpo["details"]["type"] == "ValidationError"
    assert all(set(e) == {"loc", "type", "msg"} for e in cuerpo["details"]["validation"])
    texto = json.dumps(cuerpo) + caplog.text
    assert not [s for s in SENSIBLES if s in texto]


def test_f008_r4_llave_cerrada_antes_del_caso_de_uso(monkeypatch: pytest.MonkeyPatch) -> None:
    creados = _dependencias(monkeypatch, ajustes_de_escritura(sigrid_factura_write_enabled=False), Intocable())
    estado, cuerpo = _llamar(peticion(commit=True))
    assert estado == 400 and cuerpo["details"]["codigo"] == "escritura_facturas_deshabilitada"
    assert creados == []


def test_f008_r4_la_llave_va_despues_del_cuerpo(monkeypatch: pytest.MonkeyPatch) -> None:
    _dependencias(monkeypatch, AjustesFactura(), Intocable())
    estado, cuerpo = _llamar(peticion(commit=True, sobra=1))
    assert estado == 400 and cuerpo["error"] == "Solicitud invalida."


def test_f008_r4_ninguna_otra_llave_la_abre(monkeypatch: pytest.MonkeyPatch) -> None:
    ajustes = ajustes_de_escritura(sigrid_factura_write_enabled=False)
    ajustes.sigrid_albaran_write_enabled = True  # type: ignore[attr-defined]
    ajustes.sigrid_proforma_write_enabled = True  # type: ignore[attr-defined]
    _dependencias(monkeypatch, ajustes, Intocable())
    estado, cuerpo = _llamar(peticion(commit=True))
    assert cuerpo["details"]["codigo"] == "escritura_facturas_deshabilitada"


def test_f008_r4_la_previa_no_mira_la_llave(monkeypatch: pytest.MonkeyPatch) -> None:
    _dependencias(monkeypatch, AjustesFactura(), Repositorio())
    estado, _cuerpo = _llamar(peticion(commit=False))
    assert estado == 200


def test_f008_r44_fallo_de_negocio_con_codigo_y_detalles(monkeypatch: pytest.MonkeyPatch) -> None:
    _dependencias(monkeypatch, AjustesFactura(), Repositorio())
    estado, cuerpo = _llamar(peticion(total_base=1.0))
    assert estado == 400 and cuerpo["details"]["codigo"] == "totales_no_cuadran"
    assert cuerpo["details"]["type"] == "FacturaError"
    assert cuerpo["details"]["calculado"]["total_base"] == 20.0


def test_f008_r24_lineas_no_validas_por_la_ruta(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    _dependencias(monkeypatch, AjustesFactura(), Repositorio())
    linea = {"descripcion": "Material", "cantidad": 1.0, "precio": 1.0, "iva": "I4", "producto": "SM9999"}
    with caplog.at_level(logging.INFO):
        estado, cuerpo = _llamar(peticion(lineas=[linea]))
    assert estado == 400 and cuerpo["details"]["codigo"] == "lineas_no_validas"
    assert [(f["indice"], f["codigo"]) for f in cuerpo["details"]["lineas"]] == [
        (0, "iva_no_valido"), (0, "producto_no_permitido"),
    ]
    assert "Material" not in caplog.text and "SM9999" not in caplog.text


class _Lanza:
    def __init__(self, exc: BaseException) -> None:
        self.exc = exc

    def run(self, request: FacturaRequest) -> Any:
        raise self.exc


@pytest.mark.parametrize("exc,estado", [(ValueError("x"), 400), (RuntimeError("x"), 500)])
def test_f008_errores_no_de_negocio(monkeypatch: pytest.MonkeyPatch, exc: BaseException, estado: int) -> None:
    monkeypatch.setattr(function_app, "build_dependencies", lambda: (AjustesFactura(), Intocable()))
    monkeypatch.setattr(function_app, "CreateFacturaUseCase", lambda repo, ajustes: _Lanza(exc))
    codigo, cuerpo = _llamar(peticion())
    assert codigo == estado and "codigo" not in cuerpo.get("details", {})


def test_f008_r46_traza_sin_datos_sensibles(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    repo = con_transaccion(Repositorio())
    _dependencias(monkeypatch, ajustes_de_escritura(), repo)
    with caplog.at_level(logging.INFO, logger="application.use_cases.create_factura_use_case"):
        _llamar(peticion(commit=True))
        _dependencias(monkeypatch, AjustesFactura(), Repositorio())
        _llamar(peticion(total_base=1.0))
    trazas = [json.loads(r.getMessage()) for r in caplog.records if r.name.endswith("create_factura_use_case")]
    assert [t["resultado"] for t in trazas] == ["ok", "error"]
    ok, error = trazas
    assert ok == {
        "endpoint": "sigrid/factura", "database": "ruesma", "obra": None, "prefijo": "FAC-",
        "usu": "prueba", "serie": "FR", "modo": "mes", "commit": True, "n_origenes": 1,
        "n_lineas_origen": 1, "n_lineas_sin_origen": 0, "n_vencimientos": 1, "resultado": "ok",
        "estado": "creado", "cod": "FR26/00042", "codigos": [], "duracion_ms": ok["duracion_ms"],
    }
    assert error["codigo"] == "totales_no_cuadran"
    assert not [s for s in SENSIBLES if s in caplog.text]


def test_f008_r46_traza_de_un_fallo_de_lineas_solo_con_codigos(caplog: pytest.LogCaptureFixture) -> None:
    caso = CreateFacturaUseCase(Repositorio(), AjustesFactura(), ahora_utc=lambda: AHORA)
    linea = {"descripcion": "Material", "cantidad": 1.0, "precio": 1.0, "iva": "I4", "producto": "MA9999"}
    with caplog.at_level(logging.INFO), pytest.raises(FacturaError):
        caso.run(FacturaRequest.model_validate(peticion(lineas=[linea])))
    (traza,) = [json.loads(r.getMessage()) for r in caplog.records]
    assert traza["codigo"] == "lineas_no_validas" and traza["codigos"] == ["iva_no_valido"]
