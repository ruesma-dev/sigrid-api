# tests/test_f009_route.py
"""
F-009 · lote D · T13: la ruta `POST /api/sigrid/albaran` con sus dos modos y la
guarda R8 en `sigrid/albaran` y `sigrid/albaran-directo`.

R1 (modo por claves y `peticion_mixta` sin leer la base), R7 (superconjunto de
la respuesta clásica, sin columnas bancarias), R8 (segunda llave antes del caso
de uso; el dry-run no cambia), R9 (400 con `details.codigo` y `details.lineas`;
lo inesperado, 500), R32 en lo que traza la ruta y el cableado del caso de uso
nuevo en `build_dependencies`.

Sin red y sin base de datos: se dobla `build_dependencies` (que leería el
entorno) y, según el test, los casos de uso o el repositorio (`f009_dobles`).
"""
from __future__ import annotations

import json
import logging
from typing import Any

import azure.functions as func
import pytest
from f009_dobles import AHORA, RepositorioDoble, SettingsDoble

import function_app
from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
)
from domain.models.albaran_compra_models import (
    COLUMNAS_BANCARIAS,
    AlbaranCompraError,
    AlbaranCompraRequest,
    FalloLinea,
)
from domain.models.albaran_directo_models import AddDirectAlbaranRequest
from domain.models.albaran_domain_models import (
    AddPurchaseAlbaranRequest,
    AddPurchaseAlbaranResponse,
)

CLASICO: dict[str, Any] = {
    "database": "ruesma", "cod_contrato": "CTSU16/0206", "cod_obra": "0404",
    "cif_proveedor": "B12345678", "lineas_recibidas": [{"ctrpro_ide": 9001, "cantidad": 2.0}],
}

EXTENDIDO: dict[str, Any] = {
    "database": "ruesma", "cod_obra": "0404", "usu": "prueba", "cif_proveedor": "B12345678",
    "referencia_externa": "ALB-1", "cod_contrato": "CTSU16/0206", "su_referencia": "A-77",
    "fecha_albaran": 20261005,
    "lineas": [{"referencia_linea": "L1", "ctrpro_ide": 9001, "cantidad": 2.0, "precio": 10.5}],
}

DIRECTO: dict[str, Any] = {
    "database": "ruesma", "cif_proveedor": "B12345678", "cod_obra": "0404",
    "lineas": [{"proide": 55, "can": 1.0, "pre": 2.0}],
}


class RepositorioIntocable:
    """Cualquier uso del repositorio hace fallar el test (`sin leer la base`)."""

    def __getattr__(self, nombre: str) -> Any:
        raise AssertionError(f"no se debía tocar el repositorio ({nombre})")


class CasoDoble:
    """Caso de uso de mentira: graba las peticiones y responde o lanza."""

    def __init__(self, respuesta: Any = None, *, lanza: BaseException | None = None) -> None:
        self.peticiones: list[Any] = []
        self._respuesta = respuesta if respuesta is not None else {"ok": True, "doble": True}
        self._lanza = lanza

    def run(self, request: Any) -> Any:
        self.peticiones.append(request)
        if self._lanza is not None:
            raise self._lanza
        return self._respuesta


def dependencias(
    monkeypatch: pytest.MonkeyPatch,
    *,
    settings: Any = None,
    repositorio: Any = None,
    clasico: Any = None,
    extendido: Any = None,
) -> None:
    tupla = (
        settings or SettingsDoble(), repositorio or RepositorioIntocable(),
        None, None, None, None, clasico or CasoDoble(), extendido or CasoDoble(),
    )
    monkeypatch.setattr(function_app, "build_dependencies", lambda: tupla)


def llamar(ruta: str, cuerpo: Any) -> tuple[int, dict[str, Any]]:
    funcion = {
        "albaran": function_app.sigrid_albaran,
        "albaran-directo": function_app.sigrid_albaran_directo,
    }[ruta]._function.get_user_function()
    respuesta = funcion(func.HttpRequest(
        method="POST", url=f"/api/sigrid/{ruta}",
        body=json.dumps(cuerpo).encode(), headers={"Content-Type": "application/json"},
    ))
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


def extendido_real(repo: RepositorioDoble | None = None) -> CreateAlbaranCompraUseCase:
    return CreateAlbaranCompraUseCase(repo or RepositorioDoble(), SettingsDoble(), ahora_utc=lambda: AHORA)


# =====================================================================================
# R1: el modo sale de las claves presentes, no de sus valores
# =====================================================================================


def test_f009_r1_con_lineas_va_al_caso_de_uso_extendido(monkeypatch: pytest.MonkeyPatch) -> None:
    clasico, extendido = CasoDoble(), CasoDoble()
    dependencias(monkeypatch, clasico=clasico, extendido=extendido)
    estado, cuerpo = llamar("albaran", EXTENDIDO)
    assert (estado, cuerpo) == (200, {"ok": True, "doble": True})
    assert clasico.peticiones == []
    assert [type(p) for p in extendido.peticiones] == [AlbaranCompraRequest]
    assert extendido.peticiones[0].referencia_externa == "ALB-1"


def test_f009_r1_sin_lineas_ni_referencia_va_al_clasico(monkeypatch: pytest.MonkeyPatch) -> None:
    clasico, extendido = CasoDoble(), CasoDoble()
    dependencias(monkeypatch, clasico=clasico, extendido=extendido)
    estado, _ = llamar("albaran", CLASICO)
    assert estado == 200
    assert extendido.peticiones == []
    assert [type(p) for p in clasico.peticiones] == [AddPurchaseAlbaranRequest]


@pytest.mark.parametrize(
    "cuerpo",
    [{"referencia_externa": "ALB-1"}, {"lineas": []}, {"lineas": None, "database": "ruesma"}],
    ids=["solo_referencia", "lineas_vacia", "lineas_nula"],
)
def test_f009_r1_basta_la_clave_aunque_su_valor_no_valga(
    monkeypatch: pytest.MonkeyPatch, cuerpo: dict[str, Any]
) -> None:
    """El extendido lo rechaza Pydantic (400 sin código) con SUS campos: el clásico
    habría pedido `cod_contrato` y nunca `usu` ni `lineas`."""
    clasico, extendido = CasoDoble(), CasoDoble()
    dependencias(monkeypatch, clasico=clasico, extendido=extendido)
    estado, respuesta = llamar("albaran", cuerpo)
    assert estado == 400
    assert respuesta["error"] == "Solicitud invalida."
    assert respuesta["details"]["type"] == "ValidationError"
    assert "codigo" not in respuesta["details"]
    campos = {next(iter(e["loc"])) for e in respuesta["details"]["validation"]}
    assert "usu" in campos
    assert clasico.peticiones == [] and extendido.peticiones == []


@pytest.mark.parametrize(
    "extra",
    [{"lineas": EXTENDIDO["lineas"]}, {"referencia_externa": "ALB-1"}, {"lineas": None}],
    ids=["con_lineas", "con_referencia", "lineas_nula"],
)
def test_f009_r1_peticion_mixta_400_sin_leer_la_base(
    monkeypatch: pytest.MonkeyPatch, extra: dict[str, Any]
) -> None:
    clasico, extendido = CasoDoble(), CasoDoble()
    dependencias(monkeypatch, clasico=clasico, extendido=extendido)
    estado, respuesta = llamar("albaran", {**CLASICO, **extra})
    assert estado == 400
    assert respuesta["ok"] is False
    assert respuesta["details"] == {"type": "AlbaranCompraError", "codigo": "peticion_mixta"}
    assert clasico.peticiones == [] and extendido.peticiones == []


@pytest.mark.parametrize("cuerpo", [[EXTENDIDO], 7, "lineas"], ids=["lista", "numero", "texto"])
def test_f009_r1_lo_que_no_es_un_objeto_va_al_clasico(
    monkeypatch: pytest.MonkeyPatch, cuerpo: Any
) -> None:
    clasico, extendido = CasoDoble(), CasoDoble()
    dependencias(monkeypatch, clasico=clasico, extendido=extendido)
    estado, respuesta = llamar("albaran", cuerpo)
    assert estado == 400
    assert respuesta["details"]["type"] == "ValidationError"
    assert clasico.peticiones == [] and extendido.peticiones == []


# =====================================================================================
# R7 y R9: el camino extendido de punta a punta (caso de uso real, repositorio doble)
# =====================================================================================


def test_f009_r7_previa_extendida_200_superconjunto_sin_bancarias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencias(monkeypatch, extendido=extendido_real())
    estado, cuerpo = llamar("albaran", EXTENDIDO)
    assert estado == 200
    assert set(AddPurchaseAlbaranResponse.model_fields) <= set(cuerpo)
    assert (cuerpo["ok"], cuerpo["estado"], cuerpo["dry_run"], cuerpo["committed"]) == (
        True, "previsto", True, False)
    assert cuerpo["referencia_externa"] == "ALB-1"
    assert [a["codigo"] for a in cuerpo["avisos"]] == ["cod_provisional"]
    assert cuerpo["warnings"][0] == cuerpo["avisos"][0]["mensaje"]
    assert [(l["indice"], l["referencia_linea"], l["tipo"]) for l in cuerpo["lineas"]] == [
        (0, "L1", "vinculada")]
    assert set(cuerpo["filas"]) == {"con", "dca", "dcapro", "ctrprodes", "mov", "log"}
    assert not set(COLUMNAS_BANCARIAS) & set(cuerpo["cabecera"])
    assert not set(COLUMNAS_BANCARIAS) & set(cuerpo["filas"]["dca"])
    assert "ES12" not in json.dumps(cuerpo) and "ES34" not in json.dumps(cuerpo)


def test_f009_r9_error_de_cabecera_400_con_codigo_y_sin_lineas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependencias(monkeypatch, extendido=extendido_real(RepositorioDoble({"obra": []})))
    estado, cuerpo = llamar("albaran", EXTENDIDO)
    assert estado == 400
    assert cuerpo["ok"] is False and cuerpo["error"]
    assert cuerpo["details"] == {"type": "AlbaranCompraError", "codigo": "obra_no_encontrada"}


def test_f009_r9_lineas_no_validas_trae_todas_en_details_lineas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lineas = [
        {"referencia_linea": "A", "ctrpro_ide": 1, "cantidad": 1.0, "precio": 1.0},
        {"referencia_linea": "B", "producto": "ZZ0001", "descripcion": "x", "cantidad": 1.0,
         "precio": 1.0},
    ]
    dependencias(monkeypatch, extendido=extendido_real())
    estado, cuerpo = llamar("albaran", {**EXTENDIDO, "lineas": lineas})
    assert estado == 400
    detalles = cuerpo["details"]
    assert (detalles["type"], detalles["codigo"]) == ("AlbaranCompraError", "lineas_no_validas")
    assert [(l["indice"], l["referencia_linea"], l["codigo"]) for l in detalles["lineas"]] == [
        (0, "A", "linea_no_es_del_contrato"), (1, "B", "producto_no_permitido")]
    assert all(set(l) == {"indice", "referencia_linea", "codigo", "mensaje"} for l in detalles["lineas"])
    assert all(l["mensaje"] for l in detalles["lineas"])


def test_f009_r9_el_codigo_y_las_lineas_salen_del_error_tal_cual(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fallo = FalloLinea(indice=3, referencia_linea="R-3", codigo="precio_negativo", mensaje="m")
    error = AlbaranCompraError("texto", codigo="lineas_no_validas", lineas=[fallo])
    dependencias(monkeypatch, extendido=CasoDoble(lanza=error))
    estado, cuerpo = llamar("albaran", EXTENDIDO)
    assert (estado, cuerpo) == (400, {"ok": False, "error": "texto", "details": {
        "type": "AlbaranCompraError", "codigo": "lineas_no_validas",
        "lineas": [{"indice": 3, "referencia_linea": "R-3", "codigo": "precio_negativo",
                    "mensaje": "m"}]}})


def test_f009_r9_un_valueerror_del_extendido_es_400_de_texto(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch, extendido=extendido_real(RepositorioDoble(truncar_en="obra")))
    estado, cuerpo = llamar("albaran", EXTENDIDO)
    assert estado == 400
    assert cuerpo["details"] == {"type": "ValueError"}
    assert "truncada" in cuerpo["error"]


def test_f009_r9_lo_inesperado_del_extendido_es_500(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias(monkeypatch, extendido=CasoDoble(lanza=RuntimeError("se cayó")))
    estado, cuerpo = llamar("albaran", EXTENDIDO)
    assert estado == 500
    assert cuerpo["error"] == "Error interno ejecutando sigrid/albaran."
    assert cuerpo["details"]["type"] == "RuntimeError"


def test_f009_r5_campo_naturaleza_400_sin_codigo(monkeypatch: pytest.MonkeyPatch) -> None:
    extendido = CasoDoble()
    dependencias(monkeypatch, extendido=extendido)
    linea = {**EXTENDIDO["lineas"][0], "naturaleza": "MA99"}
    estado, cuerpo = llamar("albaran", {**EXTENDIDO, "lineas": [linea]})
    assert estado == 400
    assert cuerpo["error"] == "Solicitud invalida."
    assert set(cuerpo["details"]) == {"type", "validation"}
    assert extendido.peticiones == []


# =====================================================================================
# R8: segunda llave (SIGRID_ALBARAN_WRITE_ENABLED) en las dos rutas, antes del caso de uso
# =====================================================================================


_RUTAS_R8 = [("albaran", CLASICO), ("albaran", EXTENDIDO), ("albaran-directo", DIRECTO)]
_IDS_R8 = ["clasico", "extendido", "directo"]


def _con_directo_doble(monkeypatch: pytest.MonkeyPatch, caso: CasoDoble) -> list[Any]:
    construidos: list[Any] = []

    def fabrica(repository: Any, settings: Any) -> CasoDoble:
        construidos.append((repository, settings))
        return caso

    monkeypatch.setattr(function_app, "CreateDirectAlbaranUseCase", fabrica)
    return construidos


def _preparar(monkeypatch: pytest.MonkeyPatch, abierta: bool) -> CasoDoble:
    caso = CasoDoble()
    settings = SettingsDoble(sigrid_albaran_write_enabled=abierta)
    dependencias(monkeypatch, settings=settings, clasico=caso, extendido=caso)
    _con_directo_doble(monkeypatch, caso)
    return caso


@pytest.mark.parametrize(("ruta", "cuerpo"), _RUTAS_R8, ids=_IDS_R8)
def test_f009_r8_commit_con_la_llave_cerrada_400_sin_ejecutar_el_caso_de_uso(
    monkeypatch: pytest.MonkeyPatch, ruta: str, cuerpo: dict[str, Any]
) -> None:
    caso = _preparar(monkeypatch, abierta=False)
    estado, respuesta = llamar(ruta, {**cuerpo, "commit": True})
    assert estado == 400
    assert respuesta["ok"] is False
    assert respuesta["details"] == {
        "type": "AlbaranCompraError", "codigo": "escritura_albaranes_deshabilitada"}
    assert "SIGRID_ALBARAN_WRITE_ENABLED" in respuesta["error"]
    assert caso.peticiones == []


@pytest.mark.parametrize(("ruta", "cuerpo"), _RUTAS_R8, ids=_IDS_R8)
@pytest.mark.parametrize("commit", [False, None], ids=["commit_false", "sin_commit"])
def test_f009_r8_el_dry_run_no_cambia_con_la_llave_cerrada(
    monkeypatch: pytest.MonkeyPatch, ruta: str, cuerpo: dict[str, Any], commit: bool | None
) -> None:
    caso = _preparar(monkeypatch, abierta=False)
    peticion = dict(cuerpo) if commit is None else {**cuerpo, "commit": commit}
    estado, _ = llamar(ruta, peticion)
    assert estado == 200
    assert len(caso.peticiones) == 1 and caso.peticiones[0].commit is False


@pytest.mark.parametrize(("ruta", "cuerpo"), _RUTAS_R8, ids=_IDS_R8)
def test_f009_r8_commit_con_la_llave_abierta_llega_al_caso_de_uso(
    monkeypatch: pytest.MonkeyPatch, ruta: str, cuerpo: dict[str, Any]
) -> None:
    caso = _preparar(monkeypatch, abierta=True)
    estado, _ = llamar(ruta, {**cuerpo, "commit": True})
    assert estado == 200
    assert len(caso.peticiones) == 1 and caso.peticiones[0].commit is True


def test_f009_r8_la_guarda_va_despues_de_validar_el_modelo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un cuerpo inválido con commit da el 400 de Pydantic, como hoy (design)."""
    _preparar(monkeypatch, abierta=False)
    estado, respuesta = llamar("albaran-directo", {"commit": True})
    assert estado == 400
    assert respuesta["error"] == "Solicitud invalida."


def test_f009_r8_el_directo_sigue_construyendose_con_settings_y_repositorio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    caso = CasoDoble()
    settings, repo = SettingsDoble(), RepositorioIntocable()
    dependencias(monkeypatch, settings=settings, repositorio=repo)
    construidos = _con_directo_doble(monkeypatch, caso)
    estado, _ = llamar("albaran-directo", DIRECTO)
    assert estado == 200
    assert construidos == [(repo, settings)]
    assert [type(p) for p in caso.peticiones] == [AddDirectAlbaranRequest]


# =====================================================================================
# R32 en la ruta: lo que traza nunca lleva textos ni precios de la petición
# =====================================================================================


def test_f009_r32_la_ruta_no_traza_los_valores_de_una_peticion_extendida_invalida(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    dependencias(monkeypatch)
    linea = {"referencia_linea": "L1", "producto": "MA9999", "descripcion": "Arena secreta",
             "cantidad": 1.0, "precio": 123.456, "sobrante": "Texto privado"}
    with caplog.at_level(logging.DEBUG):
        estado, _ = llamar("albaran", {**EXTENDIDO, "lineas": [linea]})
    assert estado == 400
    trazado = " ".join(r.getMessage() for r in caplog.records)
    assert "sobrante" in trazado
    for prohibido in ("Arena secreta", "123.456", "Texto privado"):
        assert prohibido not in trazado


def test_f009_r32_la_ruta_traza_los_codigos_de_linea_y_no_sus_mensajes(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    fallo = FalloLinea(indice=0, referencia_linea="L1", codigo="precio_negativo",
                       mensaje="Arena secreta a 123.456")
    error = AlbaranCompraError("Arena secreta", codigo="lineas_no_validas", lineas=[fallo])
    dependencias(monkeypatch, extendido=CasoDoble(lanza=error))
    with caplog.at_level(logging.DEBUG):
        llamar("albaran", EXTENDIDO)
    trazado = " ".join(r.getMessage() for r in caplog.records if r.name == function_app.logger.name)
    assert "lineas_no_validas" in trazado and "precio_negativo" in trazado
    assert "Arena secreta" not in trazado and "123.456" not in trazado


# =====================================================================================
# Cableado (T13) y docstring (H32)
# =====================================================================================


def test_f009_t13_build_dependencies_cablea_el_caso_de_uso_extendido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = SettingsDoble()

    class RepositorioFabricado:
        def __init__(self, recibidos: Any) -> None:
            self.settings = recibidos

    monkeypatch.setattr(function_app, "get_settings", lambda: settings)
    monkeypatch.setattr(function_app, "SqlServerRepository", RepositorioFabricado)
    deps = function_app.build_dependencies.__wrapped__()
    assert len(deps) == 8
    assert deps[0] is settings and isinstance(deps[1], RepositorioFabricado)
    caso = deps[7]
    assert isinstance(caso, CreateAlbaranCompraUseCase)
    assert caso._repo is deps[1] and caso._settings is settings
    assert deps[6]._repo is deps[1]


@pytest.mark.parametrize(
    "funcion", ["sql_read", "sql_write", "sigrid_contrato_lineas", "documents_read"]
)
def test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho(
    monkeypatch: pytest.MonkeyPatch, funcion: str
) -> None:
    """Con la tupla de ocho, cada ruta llega a validar su modelo (`{}` da el 400
    de Pydantic); si desempaquetara siete, saldría un `ValueError` («too many
    values to unpack»), también 400 pero de otro tipo, en todas las peticiones."""
    monkeypatch.setattr(function_app, "build_dependencies", lambda: (None,) * 8)
    ruta = getattr(function_app, funcion)._function.get_user_function()
    respuesta = ruta(func.HttpRequest(
        method="POST", url="/api/x", body=b"{}", headers={"Content-Type": "application/json"},
    ))
    cuerpo = json.loads(respuesta.get_body().decode("utf-8"))
    assert respuesta.status_code == 400
    assert cuerpo["details"]["type"] == "ValidationError"


def test_f009_h32_el_docstring_de_sigrid_albaran_ya_no_dice_que_replica_todas_las_lineas() -> None:
    doc = function_app.sigrid_albaran._function.get_user_function().__doc__ or ""
    assert "TODAS las lineas" not in doc
    assert "extendido" in doc and "clasico" in doc
    assert "SIGRID_ALBARAN_WRITE_ENABLED" in doc
