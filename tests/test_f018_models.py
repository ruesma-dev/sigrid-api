# tests/test_f018_models.py
"""
F-018 · T2: el modelo del descuento por línea.

R4 (`LineaAlbaranIn.dto`: opcional, número JSON estricto y finito, 0 a 100 con
los dos bordes, como mucho 2 decimales; si no, 400 sin código), `con_dto`
(D6: 0 = sin descuento), R16 (`dto` y `precio_bruto` en la línea de respuesta
solo cuando valen algo: con `None` no salen en el JSON, D8), R17 (el aviso
nuevo `dto_distinto_del_contrato`, también en la proforma) y R20 (la línea de
`sigrid/proforma` no admite `dto`).

Sin red y sin base de datos: la ruta se llama con los dobles de F-009 y F-007.
"""
from __future__ import annotations

import math
from typing import Any

import pytest
from pydantic import ValidationError
from test_f007_route import con_caso_de_uso as con_caso_de_proforma
from test_f007_route import dependencias as dependencias_de_proforma
from test_f007_route import llamar as llamar_a_proforma
from test_f007_route import peticion as peticion_de_proforma
from test_f009_route import EXTENDIDO, CasoDoble, dependencias, llamar

from domain.models.albaran_compra_models import (
    CODIGOS_AVISO,
    AvisoAlbaran,
    LineaAlbaranIn,
    LineaResultado,
)
from domain.models.proforma_models import (
    CODIGOS_AVISO_PROFORMA,
    AvisoProforma,
    LineaProformaIn,
    LineaProformaResultado,
)
from domain.models.proforma_origen_models import LineaProformaOrigenResultado


def _linea(**extra: Any) -> dict[str, Any]:
    return {"referencia_linea": "L1", "ctrpro_ide": 9001, "cantidad": 2.0, "precio": 10.5, **extra}


# =====================================================================================
# R4 · `dto` válido e inválido
# =====================================================================================

@pytest.mark.parametrize("dto", [0, 0.0, 40, 40.0, 1.5, 21.45, 0.01, 99.99, 100, 100.0])
def test_f018_r4_dto_valido(dto: float) -> None:
    linea = LineaAlbaranIn(**_linea(dto=dto))
    assert linea.dto == dto


def test_f018_r4_dto_ausente_o_null_es_none() -> None:
    assert LineaAlbaranIn(**_linea()).dto is None
    assert LineaAlbaranIn(**_linea(dto=None)).dto is None


@pytest.mark.parametrize(
    "dto",
    ["40", "10+5", "40%", True, False, -0.01, -1, 100.01, 101, 21.455, 0.001, math.nan, math.inf,
     -math.inf, [40], {"valor": 40}],
    ids=["texto", "cascada", "con_porcentaje", "true", "false", "menos_un_centimo", "negativo",
         "sobre_100", "101", "tres_decimales", "milesima", "nan", "inf", "menos_inf", "lista",
         "objeto"],
)
def test_f018_r4_dto_invalido(dto: Any) -> None:
    with pytest.raises(ValidationError) as exc:
        LineaAlbaranIn(**_linea(dto=dto))
    assert {e["loc"][0] for e in exc.value.errors()} == {"dto"}


@pytest.mark.parametrize("dto", ["10+5", True, -0.01, 100.01, 21.455])
def test_f018_r4_dto_invalido_es_400_sin_codigo_en_la_ruta(
    monkeypatch: pytest.MonkeyPatch, dto: Any
) -> None:
    extendido = CasoDoble()
    dependencias(monkeypatch, extendido=extendido)
    linea = {**EXTENDIDO["lineas"][0], "dto": dto}
    estado, cuerpo = llamar("albaran", {**EXTENDIDO, "lineas": [linea]})
    assert estado == 400
    assert cuerpo["error"] == "Solicitud invalida."
    assert set(cuerpo["details"]) == {"type", "validation"}
    assert extendido.peticiones == []


def test_f018_r4_dto_valido_llega_al_caso_de_uso(monkeypatch: pytest.MonkeyPatch) -> None:
    extendido = CasoDoble()
    dependencias(monkeypatch, extendido=extendido)
    linea = {**EXTENDIDO["lineas"][0], "dto": 21.45}
    estado, _ = llamar("albaran", {**EXTENDIDO, "lineas": [linea]})
    assert estado == 200
    assert extendido.peticiones[0].lineas[0].dto == 21.45


# =====================================================================================
# D6 · `con_dto`: 0 es sin descuento
# =====================================================================================

@pytest.mark.parametrize("dto, esperado", [(None, False), (0, False), (0.0, False), (0.01, True),
                                           (40, True), (100, True)])
def test_f018_d6_con_dto(dto: float | None, esperado: bool) -> None:
    assert LineaAlbaranIn(**_linea(dto=dto)).con_dto is esperado


# =====================================================================================
# R16 · `dto` y `precio_bruto` en la respuesta solo si valen algo (D8)
# =====================================================================================

_BASE = {"indice": 0, "referencia_linea": "L1", "ctrpro_ide": 0, "linoriide": 0, "proide": 1,
         "cantidad": 1.0, "precio": 11.18, "total": 11.18, "iva_cuota": 2.35, "almide": 70}


@pytest.mark.parametrize(
    "clase", [LineaResultado, LineaProformaResultado, LineaProformaOrigenResultado]
)
def test_f018_r16_sin_dto_no_salen_las_claves(clase: type) -> None:
    linea = clase(**_BASE)
    assert (linea.dto, linea.precio_bruto) == (None, None)
    for volcado in (linea.model_dump(), linea.model_dump(mode="json")):
        assert "dto" not in volcado and "precio_bruto" not in volcado
        assert volcado["precio"] == 11.18


@pytest.mark.parametrize(
    "clase", [LineaResultado, LineaProformaResultado, LineaProformaOrigenResultado]
)
def test_f018_r16_con_dto_salen_las_dos(clase: type) -> None:
    linea = clase(**_BASE, dto=40.0, precio_bruto=18.625)
    for volcado in (linea.model_dump(), linea.model_dump(mode="json")):
        assert (volcado["dto"], volcado["precio_bruto"]) == (40.0, 18.625)
    # El resto de las claves, las de siempre: el volcado sin dto mas las dos.
    assert set(linea.model_dump()) == set(clase(**_BASE).model_dump()) | {"dto", "precio_bruto"}


def test_f018_r16_las_demas_claves_none_siguen_saliendo() -> None:
    """Solo se omiten `dto` y `precio_bruto`: los otros `None` (pos, partida,
    stock...) salen como hoy."""
    volcado = LineaResultado(**_BASE).model_dump(mode="json")
    assert volcado["pos"] is None and volcado["partida"] is None and volcado["tipo"] is None


def test_f018_r16_el_volcado_se_puede_reconstruir_en_la_subclase() -> None:
    """La proforma construye su línea con `**linea.model_dump(exclude={"avisos"})`."""
    nucleo = LineaResultado(**_BASE, dto=1.5, precio_bruto=10.0)
    proforma = LineaProformaResultado(**nucleo.model_dump(exclude={"avisos"}))
    assert (proforma.dto, proforma.precio_bruto) == (1.5, 10.0)
    sin = LineaProformaResultado(**LineaResultado(**_BASE).model_dump(exclude={"avisos"}))
    assert "dto" not in sin.model_dump()


# =====================================================================================
# R17 · el aviso nuevo, también heredado por la proforma
# =====================================================================================

def test_f018_r17_dto_distinto_del_contrato_es_un_aviso() -> None:
    assert "dto_distinto_del_contrato" in CODIGOS_AVISO
    assert "dto_distinto_del_contrato" in CODIGOS_AVISO_PROFORMA
    assert AvisoAlbaran(codigo="dto_distinto_del_contrato", mensaje="x").codigo
    assert AvisoProforma(codigo="dto_distinto_del_contrato", mensaje="x").codigo


# =====================================================================================
# R20 · la proforma no admite `dto`
# =====================================================================================

def test_f018_r20_linea_de_proforma_con_dto_no_valida() -> None:
    with pytest.raises(ValidationError) as exc:
        LineaProformaIn(referencia_linea="P1", cantidad=1.0, precio=2.0, descripcion="x", dto=10)
    assert exc.value.errors()[0]["type"] == "extra_forbidden"


def test_f018_r20_proforma_con_dto_es_400_sin_codigo(monkeypatch: pytest.MonkeyPatch) -> None:
    dependencias_de_proforma(monkeypatch)
    construidos = con_caso_de_proforma(monkeypatch)
    cuerpo = peticion_de_proforma()
    # Lista nueva: la de la hoja es la de la fixture compartida y no se toca.
    cuerpo["lineas"] = [{**cuerpo["lineas"][0], "dto": 10}, *cuerpo["lineas"][1:]]
    estado, respuesta = llamar_a_proforma(cuerpo)
    assert estado == 400
    assert respuesta["error"] == "Solicitud invalida."
    assert respuesta["details"]["type"] == "ValidationError"
    assert "codigo" not in respuesta["details"]
    assert construidos == []
