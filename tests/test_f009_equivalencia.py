# tests/test_f009_equivalencia.py
"""
F-009 · T12 · R33: el modo extendido frente al clásico.

El mismo albarán (solo vinculadas, positivas, sin `ctrpro` repetido, partida y
precio del `ctrpro`, plantilla de la misma empresa y productos con `tipmov` 1)
se construye en previa por los dos modos sobre el mismo ERP de mentira
(`f009_dobles.py`), y las filas CONSTRUIDAS se comparan columna a columna:
mismas columnas en cada fila y, en los valores, solo las diferencias declaradas
en design §Equivalencia (v8.2), ni una más.

Las filas se capturan donde cada modo las numera (el clásico en
`_assign_ides`, el extendido en `numerar`), así se comparan completas y con las
columnas bancarias que se escriben, no la respuesta. El caso de uso clásico no
se toca: se le espía con `monkeypatch`.
"""
from __future__ import annotations

from datetime import datetime as _datetime_real
from types import SimpleNamespace
from typing import Any

import pytest
from f009_dobles import AHORA, CTR, RepositorioDoble, SettingsDoble

from application.use_cases import create_albaran_compra_use_case as modulo_extendido
from application.use_cases import create_purchase_albaran_use_case as modulo_clasico
from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
)
from application.use_cases.create_purchase_albaran_use_case import (
    CreatePurchaseAlbaranUseCase,
)
from domain.models import sql_models
from domain.models.albaran_compra_models import AlbaranCompraRequest
from domain.models.albaran_domain_models import AddPurchaseAlbaranRequest

#: design §Equivalencia (v8.2): las ÚNICAS columnas en que pueden diferir.
DECLARADAS: dict[str, set[str]] = {
    "con": {"est", "res"},
    "dca": {"synckey", "hor"},
    "dcapro": {"prepma", "ivacuo", "tot", "refent", "cod2", "dncide", "dncproide"},
    "ctrprodes": set(),
    "mov": {"hor", "fec", "fechor", "prepma", "almpma"},
}

#: Hora del clásico (`datetime.now()` sin zona): la de Madrid del instante del
#: extendido, como si el servidor estuviera en hora de Madrid.
_AHORA_MADRID = _datetime_real(2026, 10, 6, 10, 15, 30)  # noqa: DTZ001


class _RelojClasico:
    @staticmethod
    def now() -> _datetime_real:
        return _AHORA_MADRID


class RepositorioClasico(RepositorioDoble):
    """El mismo ERP, contestando también las cuatro lecturas propias del clásico."""

    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        sql, p = request.sql, list(request.parameters)
        if sql.startswith("SELECT ISNULL(MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))), 0) + 1"):
            return [], [(15953,)], False
        if sql == ("SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
                   "WHERE c.tip = ? AND d.entide = ? ORDER BY c.ide DESC"):
            assert p == [14, 77]
            return [], [(15950,)], False
        if sql == ("SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? "
                   "ORDER BY ide DESC"):
            return [], self._responder("balance", p), False
        return super().execute_read_query(request)


@pytest.fixture(autouse=True)
def _aislado(monkeypatch: pytest.MonkeyPatch) -> None:
    # `SqlReadRequest.model_validate` (el clásico) valida contra `get_settings()`.
    monkeypatch.setattr(sql_models, "get_settings", lambda: SimpleNamespace(
        default_max_rows=200, max_allowed_rows=1000,
        default_query_timeout_seconds=30, max_query_timeout_seconds=120,
    ))
    monkeypatch.setattr(modulo_clasico, "datetime", _RelojClasico)


def _filas_del_clasico(monkeypatch: pytest.MonkeyPatch, **cambios: Any) -> dict[str, Any]:
    capturadas: dict[str, Any] = {}
    original = CreatePurchaseAlbaranUseCase._assign_ides

    def espia(con, dca, dcapro_rows, ctrprodes_rows, mov_rows, *ides):
        original(con, dca, dcapro_rows, ctrprodes_rows, mov_rows, *ides)
        capturadas.update(con=dict(con), dca=dict(dca), dcapro=[dict(f) for f in dcapro_rows],
                          ctrprodes=[dict(f) for f in ctrprodes_rows], mov=[dict(f) for f in mov_rows])

    monkeypatch.setattr(CreatePurchaseAlbaranUseCase, "_assign_ides", staticmethod(espia))
    peticion = AddPurchaseAlbaranRequest.model_validate({
        "database": "ruesma", "cod_contrato": "CTSU16/0206", "cod_obra": "0404",
        "cif_proveedor": "B12345678", "su_referencia": "A-77", "fecha_albaran": 20261005,
        "lineas_recibidas": [{"ctrpro_ide": 9001, "cantidad": 2.0}, {"ctrpro_ide": 9002, "cantidad": 4.0}],
        **cambios,
    })
    respuesta = CreatePurchaseAlbaranUseCase(RepositorioClasico(), SettingsDoble()).run(peticion)
    assert respuesta.dry_run
    return capturadas


def _filas_del_extendido(monkeypatch: pytest.MonkeyPatch, **cambios: Any) -> dict[str, Any]:
    capturadas: dict[str, Any] = {}
    original = modulo_extendido.numerar

    def espia(filas, **ides):
        numeradas = original(filas, **ides)
        capturadas.update(numeradas.como_dict())
        return numeradas

    monkeypatch.setattr(modulo_extendido, "numerar", espia)
    peticion = AlbaranCompraRequest.model_validate({
        "database": "ruesma", "cod_obra": "0404", "usu": "prueba", "cif_proveedor": "B12345678",
        "referencia_externa": "ALB-1", "cod_contrato": "CTSU16/0206", "su_referencia": "A-77",
        "fecha_albaran": 20261005,
        "lineas": [
            {"referencia_linea": "L1", "ctrpro_ide": 9001, "cantidad": 2.0, "precio": 10.5,
             "partida": "01.01"},
            {"referencia_linea": "L2", "ctrpro_ide": 9002, "cantidad": 4.0, "precio": 3.0},
        ],
        **cambios,
    })
    caso = CreateAlbaranCompraUseCase(RepositorioDoble(), SettingsDoble(), ahora_utc=lambda: AHORA)
    assert caso.run(peticion).estado == "previsto"
    return capturadas


def _diferencias(clasica: dict[str, Any], extendida: dict[str, Any]) -> set[str]:
    assert list(clasica) == list(extendida), "las dos filas deben tener las mismas columnas"
    return {columna for columna in clasica if clasica[columna] != extendida[columna]}


def _comparar(clasico: dict[str, Any], extendido: dict[str, Any]) -> dict[str, list[set[str]]]:
    diferencias: dict[str, list[set[str]]] = {}
    for tabla in ("con", "dca", "dcapro", "ctrprodes", "mov"):
        filas_c = clasico[tabla] if isinstance(clasico[tabla], list) else [clasico[tabla]]
        filas_e = extendido[tabla] if isinstance(extendido[tabla], list) else [extendido[tabla]]
        assert len(filas_c) == len(filas_e), tabla
        diferencias[tabla] = [_diferencias(c, e) for c, e in zip(filas_c, filas_e, strict=True)]
        for diferencia in diferencias[tabla]:
            assert diferencia <= DECLARADAS[tabla], (tabla, diferencia - DECLARADAS[tabla])
    return diferencias


def test_f009_r33_mismas_filas_que_el_clasico_salvo_las_declaradas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clasico = _filas_del_clasico(monkeypatch)
    extendido = _filas_del_extendido(monkeypatch)
    assert _comparar(clasico, extendido) == {
        "con": [set()],
        "dca": [{"synckey"}],
        "dcapro": [{"prepma", "refent", "cod2", "dncide", "dncproide"}] * 2,
        "ctrprodes": [set(), set()],
        "mov": [{"fec", "fechor", "prepma"}] * 2,
    }
    # Lo que sí coincide y sostiene la equivalencia, dicho explícitamente.
    for clave in ("pre", "tar", "dto", "tot", "ivacuo", "paride", "caaide", "almide", "cenide"):
        assert [f[clave] for f in clasico["dcapro"]] == [f[clave] for f in extendido["dcapro"]]
    assert extendido["dca"]["ctride"] == clasico["dca"]["ctride"] == CTR
    assert (extendido["dca"]["synckey"], clasico["dca"]["synckey"]) == ("ALB-1", "")
    # Las diferencias declaradas, con su valor: N1, `prepma` (§`prepma`), R30c y H35.
    assert [m["fec"] for m in extendido["mov"]] == [20261006, 20261006]
    assert [m["fec"] for m in clasico["mov"]] == [20261005, 20261005]
    assert [m["prepma"] for m in extendido["mov"]] == [9.0, 0.0]
    assert [f["prepma"] for f in extendido["dcapro"]] == [9.0, 0.0]
    assert [(f["refent"], f["cod2"], f["dncide"], f["dncproide"]) for f in extendido["dcapro"]] == [
        ("L1", "PLAN-7", 41, 42), ("L2", "", 0, 0)]
    # La fila de alta de `log` solo la escribe el extendido.
    assert "log" in extendido and "log" not in clasico


def test_f009_r33_con_la_fecha_de_hoy_el_mov_coincide_salvo_prepma(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sin `fecha_albaran` los dos fechan hoy: `hor`, `fec` y `fechor` coinciden
    (el reloj del clásico está en hora de Madrid) y solo queda `prepma`."""
    clasico = _filas_del_clasico(monkeypatch, fecha_albaran=None)
    extendido = _filas_del_extendido(monkeypatch, fecha_albaran=None)
    diferencias = _comparar(clasico, extendido)
    assert diferencias["mov"] == [{"prepma"}] * 2
    assert diferencias["con"] == [set()] and diferencias["dca"] == [{"synckey"}]
    assert extendido["con"]["fec"] == clasico["con"]["fec"] == 20261006
