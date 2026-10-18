# tests/test_f012_rutas.py
"""
F-012 · R1, R2, R3, R5, R8 y R10: las rutas responden el 400 de validación,
nunca un 500, cuando Pydantic rechaza la petición (o un modelo de respuesta).

Sin red y sin base: se doblan `build_dependencies`, los casos de uso que la ruta
construye y `sql_models.get_settings`. Los dobles y los cuerpos de mentira se
importan de los tests de F-004, F-006 y F-009; no se copian.
"""
from __future__ import annotations

import inspect
import json
import logging
import re
from typing import Any

import azure.functions as func
import pytest
from f009_dobles import SettingsDoble
from pydantic import ValidationError
from test_f004_route import _CUERPO as CUERPO_GRAFICO
from test_f006_route import _CUERPO as CUERPO_PARTES
from test_f009_route import _LIMITES_SQL, CLASICO, EXTENDIDO, CasoDoble, RepositorioIntocable

import function_app
from domain.models import sql_models
from domain.models.albaran_compra_models import FalloLinea
from domain.models.parte_reclamacion_models import MotivoParte

#: Las 9 rutas de R8: (función de `function_app`, url, cuerpo que no valida).
RUTAS: list[tuple[str, str, Any]] = [
    ("sql_read", "/api/sql/read", {}),
    ("sql_write", "/api/sql/write", {}),
    ("sigrid_contrato_lineas", "/api/sigrid/contrato-lineas", {}),
    ("sigrid_albaran", "/api/sigrid/albaran", {}),                    # clásico
    ("sigrid_albaran", "/api/sigrid/albaran", {"lineas": []}),        # extendido
    ("sigrid_albaran_directo", "/api/sigrid/albaran-directo", {}),
    ("sigrid_concepto_grafico", "/api/sigrid/concepto-grafico", {}),
    ("sigrid_partes_reclamacion", "/api/sigrid/partes-reclamacion", {}),
    ("documents_read", "/api/documents/read", {}),
]
_IDS_RUTAS = [
    "sql-read", "sql-write", "contrato-lineas", "albaran-clasico", "albaran-extendido",
    "albaran-directo", "concepto-grafico", "partes-reclamacion", "documents-read",
]


class Entorno:
    """Todas las dependencias dobladas: cada caso de uso es un `CasoDoble` que
    graba lo que recibe, y los que la ruta construye ella misma también."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, **lanzan: BaseException) -> None:
        self.casos = {nombre: CasoDoble(lanza=lanzan.get(nombre)) for nombre in (
            "sql_read", "documentos", "sql_write", "contrato_lineas", "clasico", "extendido",
            "directo", "grafico", "partes",
        )}
        c = self.casos
        tupla = (
            SettingsDoble(), RepositorioIntocable(), c["sql_read"], c["documentos"], c["sql_write"],
            c["contrato_lineas"], c["clasico"], c["extendido"],
        )
        monkeypatch.setattr(function_app, "build_dependencies", lambda: tupla)
        monkeypatch.setattr(sql_models, "get_settings", lambda: _LIMITES_SQL)
        for clase, nombre in (
            ("CreateDirectAlbaranUseCase", "directo"),
            ("AttachConceptoGraficoUseCase", "grafico"),
            ("CreatePartesReclamacionUseCase", "partes"),
        ):
            monkeypatch.setattr(function_app, clase, self._fabrica(c[nombre]))

    @staticmethod
    def _fabrica(caso: CasoDoble) -> Any:
        return lambda repository, settings: caso

    def ninguno_llamado(self) -> bool:
        return all(caso.peticiones == [] for caso in self.casos.values())


def llamar(funcion: str, url: str, cuerpo: Any) -> tuple[int, dict[str, Any]]:
    ruta = getattr(function_app, funcion)._function.get_user_function()
    respuesta = ruta(func.HttpRequest(
        method="POST", url=url, body=json.dumps(cuerpo).encode(),
        headers={"Content-Type": "application/json"},
    ))
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def assert_400_de_validacion(estado: int, cuerpo: dict[str, Any]) -> list[dict[str, Any]]:
    assert estado == 400, cuerpo
    assert cuerpo["ok"] is False
    assert cuerpo["error"] == "Solicitud invalida."
    assert set(cuerpo["details"]) == {"type", "validation"}
    assert cuerpo["details"]["type"] == "ValidationError"
    validacion = cuerpo["details"]["validation"]
    assert validacion
    for error in validacion:
        assert {"loc", "msg", "type"} <= set(error)
    return validacion


def _error_de_validacion(modelo: Any, **datos: Any) -> ValidationError:
    with pytest.raises(ValidationError) as info:
        modelo(**datos)
    return info.value


# =====================================================================================
# R1: las 6 reglas del modo extendido de sigrid/albaran
# =====================================================================================

_LINEA = EXTENDIDO["lineas"][0]
_SIN_VINCULAR = {"referencia_linea": "L2", "producto": "MA9999", "descripcion": "Arena",
                 "cantidad": 1.0, "precio": 2.0}
_SIN_CONTRATO = {k: v for k, v in EXTENDIDO.items() if k != "cod_contrato"}
_SIN_IDE = {k: v for k, v in _LINEA.items() if k != "ctrpro_ide"}
_SIN_DESCRIPCION = {k: v for k, v in _SIN_VINCULAR.items() if k != "descripcion"}

_REGLAS = [
    pytest.param(_SIN_CONTRATO, "exige 'cod_contrato'", id="vinculada-sin-cod_contrato"),
    pytest.param({**EXTENDIDO, "lineas": [_LINEA, {**_SIN_VINCULAR, "referencia_linea": "L1"}]},
                 "'referencia_linea' repetida", id="referencia-repetida"),
    pytest.param({**EXTENDIDO, "lineas": [{**_LINEA, "producto": "MA9999"}]}, "uno solo",
                 id="ctrpro_ide-y-producto"),
    pytest.param({**EXTENDIDO, "lineas": [_SIN_IDE]}, "uno solo", id="ni-ctrpro_ide-ni-producto"),
    pytest.param({**EXTENDIDO, "lineas": [{**_LINEA, "cantidad": 0.0}]}, "no puede ser 0",
                 id="cantidad-0"),
    pytest.param({**EXTENDIDO, "lineas": [_SIN_DESCRIPCION]}, "necesita 'descripcion'",
                 id="sin-vincular-sin-descripcion"),
    pytest.param({**EXTENDIDO, "lineas": [{**_LINEA, "paride": 3}]}, "solo va con 'partida'",
                 id="paride-sin-partida"),
]


@pytest.mark.parametrize(("cuerpo", "mensaje"), _REGLAS)
def test_f012_r1_cada_regla_del_extendido_es_400_de_validacion(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any], mensaje: str
) -> None:
    entorno = Entorno(monkeypatch)
    validacion = assert_400_de_validacion(*llamar("sigrid_albaran", "/api/sigrid/albaran", cuerpo))
    [error] = validacion
    assert error["type"] == "value_error"
    assert isinstance(error["ctx"]["error"], str)
    assert mensaje in error["ctx"]["error"]
    assert entorno.ninguno_llamado()


def test_f012_r4_el_ctx_error_es_el_mensaje_exacto_de_la_regla(monkeypatch: pytest.MonkeyPatch) -> None:
    Entorno(monkeypatch)
    validacion = assert_400_de_validacion(*llamar("sigrid_albaran", "/api/sigrid/albaran", _SIN_CONTRATO))
    assert validacion[0]["ctx"] == {"error": "Una linea vinculada exige 'cod_contrato'."}
    assert validacion[0]["loc"] == []


# =====================================================================================
# R2: sql/write con `sql` y `statements` a la vez, o ninguno
# =====================================================================================

_SQL = "UPDATE dbo.x SET a = ? WHERE b = ?"


@pytest.mark.parametrize(("cuerpo", "mensaje"), [
    pytest.param({"database": "ruesma", "sql": _SQL, "statements": [{"sql": _SQL}]}, "no ambos",
                 id="los-dos"),
    pytest.param({"database": "ruesma"}, "Debes indicar", id="ninguno"),
])
def test_f012_r2_sql_write_sql_y_statements_es_400_de_validacion(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any], mensaje: str
) -> None:
    entorno = Entorno(monkeypatch)
    [error] = assert_400_de_validacion(*llamar("sql_write", "/api/sql/write", cuerpo))
    assert error["type"] == "value_error"
    assert mensaje in error["ctx"]["error"]
    assert entorno.ninguno_llamado()


# =====================================================================================
# R3: concepto-grafico con base64 mal formado
# =====================================================================================


def test_f012_r3_concepto_grafico_base64_mal_formado_es_400_de_validacion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entorno = Entorno(monkeypatch)
    cuerpo = {**CUERPO_GRAFICO, "contenido_base64": "!!!"}
    [error] = assert_400_de_validacion(
        *llamar("sigrid_concepto_grafico", "/api/sigrid/concepto-grafico", cuerpo)
    )
    assert error["loc"] == ["contenido_base64"]
    assert error["ctx"] == {"error": "contenido_base64 no es base64 valido."}
    assert entorno.ninguno_llamado()


# =====================================================================================
# R5: un ValidationError de un modelo de respuesta, desde dentro del caso de uso
# =====================================================================================

_FALLO_INVENTADO = {"indice": 0, "referencia_linea": "L1", "codigo": "inventado", "mensaje": "x"}


@pytest.mark.parametrize(("funcion", "url", "cuerpo", "caso", "modelo", "datos"), [
    pytest.param("sigrid_albaran", "/api/sigrid/albaran", EXTENDIDO, "extendido", FalloLinea,
                 _FALLO_INVENTADO, id="albaran-extendido"),
    pytest.param("sigrid_albaran", "/api/sigrid/albaran", CLASICO, "clasico", FalloLinea,
                 _FALLO_INVENTADO, id="albaran-clasico"),
    pytest.param("sigrid_partes_reclamacion", "/api/sigrid/partes-reclamacion", CUERPO_PARTES,
                 "partes", MotivoParte, {"codigo": "inventado", "mensaje": "x"}, id="partes"),
])
def test_f012_r5_un_validationerror_interno_es_400_y_no_500(
    monkeypatch: pytest.MonkeyPatch, funcion: str, url: str, cuerpo: dict[str, Any], caso: str,
    modelo: Any, datos: dict[str, Any],
) -> None:
    interno = _error_de_validacion(modelo, **datos)
    entorno = Entorno(monkeypatch, **{caso: interno})
    [error] = assert_400_de_validacion(*llamar(funcion, url, cuerpo))
    assert error["loc"] == ["codigo"]
    assert error["ctx"]["error"].startswith("'inventado' no es un codigo de ")
    assert len(entorno.casos[caso].peticiones) == 1


# =====================================================================================
# R8: las 9 rutas construyen su 400 con la función común
# =====================================================================================


@pytest.mark.parametrize(("funcion", "url", "cuerpo"), RUTAS, ids=_IDS_RUTAS)
def test_f012_r8_las_9_rutas_responden_con_la_funcion_comun(
    monkeypatch: pytest.MonkeyPatch, funcion: str, url: str, cuerpo: Any
) -> None:
    Entorno(monkeypatch)
    llamadas: list[ValidationError] = []
    real = function_app.validation_error_response

    def espia(exc: ValidationError) -> func.HttpResponse:
        llamadas.append(exc)
        return real(exc)

    monkeypatch.setattr(function_app, "validation_error_response", espia)
    assert_400_de_validacion(*llamar(funcion, url, cuerpo))
    assert len(llamadas) == 1


def test_f012_r8_function_app_ya_no_construye_el_400_a_mano() -> None:
    fuente = inspect.getsource(function_app)
    assert not re.search(r"details\s*=\s*\{[^}]*exc\.errors\(\)", fuente)
    assert fuente.count("return validation_error_response(exc)") == 9
    assert "validation_error_response" in function_app.__dict__


# =====================================================================================
# R10: la traza del extendido sigue siendo solo (loc, type)
# =====================================================================================

_SECRETA = {"referencia_linea": "REF-SECRETA", "producto": "MA9999", "descripcion": "Arena secreta",
            "cantidad": 1.0, "precio": 123.456}


@pytest.mark.parametrize("cuerpo", [
    pytest.param({**EXTENDIDO, "lineas": [_SECRETA, _SECRETA]}, id="referencia-repetida"),
    pytest.param({**_SIN_CONTRATO, "lineas": [{**_LINEA, "referencia_linea": "REF-SECRETA",
                                               "precio": 123.456}]}, id="vinculada-sin-contrato"),
])
def test_f012_r10_la_traza_del_extendido_no_lleva_msg_input_ni_ctx(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, cuerpo: dict[str, Any]
) -> None:
    Entorno(monkeypatch)
    with caplog.at_level(logging.DEBUG):
        estado, _ = llamar("sigrid_albaran", "/api/sigrid/albaran", cuerpo)
    assert estado == 400
    trazado = " ".join(r.getMessage() for r in caplog.records)
    assert "value_error" in trazado
    for prohibido in ("REF-SECRETA", "Arena secreta", "123.456", "exige", "repetida", "Value error"):
        assert prohibido not in trazado
