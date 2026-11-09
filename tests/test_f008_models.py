# tests/test_f008_models.py
"""
F-008 · T2: el contrato de `POST /api/sigrid/factura` (R1, R2, R9, R21, R23,
R32, R44) y `FacturaError`. Sin red ni base; datos sintéticos.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.models.factura_models import (
    CODIGOS_FACTURA,
    CODIGOS_LINEA_FACTURA,
    EntradaAOrigen,
    FacturaError,
    FacturaRequest,
    FacturaResultado,
    FalloLineaFactura,
    LineaSinOrigen,
    Vencimiento,
)


def cuerpo(**cambios: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "database": "ruesma",
        "usu": "prueba",
        "referencia_externa": "FAC-1",
        "cif_proveedor": "B00000000",
        "numero_factura": "F-77",
        "fecha_factura": 20261015,
        "cod_obra": "0404",
        "lineas": [{"descripcion": "Material", "cantidad": 2.0, "precio": 10.0, "iva": "I21",
                    "producto": "MA9999"}],
        "vencimientos": [{"fecha": 20261115, "importe": 24.2}],
        "total_base": 20.0,
        "total_iva": 4.2,
        "total_factura": 24.2,
    }
    base.update(cambios)
    return base


def test_f008_r1_el_cuerpo_minimo_vale_con_sus_defectos() -> None:
    peticion = FacturaRequest.model_validate(cuerpo())
    assert peticion.serie == "FR"
    assert peticion.modo == "mes"
    assert peticion.origenes == []
    assert peticion.a_origen is None
    assert peticion.commit is False
    assert peticion.vencimiento_retencion is None


@pytest.mark.parametrize("campo,valor", [
    ("sobra", 1),
    ("total_base", "20.0"),
    ("fecha_factura", "20261015"),
    ("commit", "true"),
    ("serie", "AB"),
    ("modo", "trimestre"),
    ("usu", "u" * 25),
    ("referencia_externa", ""),
    ("referencia_externa", "r" * 129),
    ("numero_factura", ""),
    ("numero_factura", "n" * 129),
    ("fecha_factura", 20261332),
    ("fecha_factura", 2026101),
    ("vencimientos", []),
    ("vencimientos", [{"fecha": 20261115, "importe": 1.0}] * 13),
    ("total_iva", float("nan")),
])
def test_f008_r1_cuerpo_no_valido(campo: str, valor: Any) -> None:
    with pytest.raises(ValidationError):
        FacturaRequest.model_validate(cuerpo(**{campo: valor}))


def test_f008_r2_sin_origenes_ni_lineas_es_400() -> None:
    with pytest.raises(ValidationError, match="origenes"):
        FacturaRequest.model_validate(cuerpo(lineas=[]))


def test_f008_r2_modo_origen_sin_origenes_es_400() -> None:
    with pytest.raises(ValidationError, match="origen"):
        FacturaRequest.model_validate(cuerpo(modo="origen"))


def test_f008_r2_origen_repetido_es_400() -> None:
    with pytest.raises(ValidationError, match="repet"):
        FacturaRequest.model_validate(cuerpo(origenes=["AC26/1", "AC26/2", "AC26/1"]))


def test_f008_r2_origen_repetido_tras_recortar_es_400() -> None:
    with pytest.raises(ValidationError, match="repet"):
        FacturaRequest.model_validate(cuerpo(origenes=["AC26/1", " AC26/1 "]))


def test_f008_r2_a_origen_en_modo_mes_es_400() -> None:
    with pytest.raises(ValidationError, match="a_origen"):
        FacturaRequest.model_validate(cuerpo(
            origenes=["AC26/1"], a_origen=[{"linea": 1, "canoriori": 1.0, "imporiori": 1.0}],
        ))


def test_f008_r2_a_origen_vacio_en_modo_mes_tambien_es_400() -> None:
    with pytest.raises(ValidationError, match="a_origen"):
        FacturaRequest.model_validate(cuerpo(origenes=["AC26/1"], a_origen=[]))


def test_f008_r21_a_origen_en_modo_origen_se_admite() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(
        origenes=["AC26/1"], modo="origen", lineas=[],
        a_origen=[{"linea": 9, "canoriori": 3.0, "imporiori": 30}],
    ))
    assert peticion.a_origen == [EntradaAOrigen(linea=9, canoriori=3.0, imporiori=30.0)]


def test_f008_r11_sin_origenes_la_obra_es_obligatoria() -> None:
    with pytest.raises(ValidationError, match="cod_obra"):
        FacturaRequest.model_validate(cuerpo(cod_obra=None))


def test_f008_r11_con_origenes_la_obra_es_opcional() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(cod_obra=None, origenes=["AC26/1"], lineas=[]))
    assert peticion.cod_obra is None
    assert peticion.origenes == ["AC26/1"]


def test_f008_p18_frgg_con_origenes_se_acepta() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(serie="FRGG", origenes=["AC26/1"], lineas=[]))
    assert peticion.serie == "FRGG"


def test_f008_r23_linea_fr_exige_producto() -> None:
    linea = {"descripcion": "x", "cantidad": 1.0, "precio": 1.0, "iva": "I21"}
    with pytest.raises(ValidationError, match="producto"):
        FacturaRequest.model_validate(cuerpo(lineas=[linea]))


@pytest.mark.parametrize("campo", ["cuenta", "analitica"])
def test_f008_r23_linea_fr_con_campo_de_frgg_es_400(campo: str) -> None:
    linea = {"descripcion": "x", "cantidad": 1.0, "precio": 1.0, "iva": "I21", "producto": "MA9999",
             campo: "6000000000"}
    with pytest.raises(ValidationError, match=campo):
        FacturaRequest.model_validate(cuerpo(lineas=[linea]))


def _linea_gg(**cambios: Any) -> dict[str, Any]:
    return {"descripcion": "Gasto", "cantidad": 1.0, "precio": 5.0, "iva": "I21",
            "cuenta": "6290000000", "analitica": "GG.GEN", **cambios}


def test_f008_r23_linea_frgg_valida() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(serie="FRGG", lineas=[_linea_gg()]))
    assert peticion.lineas[0].cuenta == "6290000000"
    assert peticion.lineas[0].analitica == "GG.GEN"


@pytest.mark.parametrize("campo,valor", [
    ("producto", "MA9999"), ("partida", "01"), ("paride", 5), ("unidad", "UD"),
])
def test_f008_r23_linea_frgg_con_campo_de_fr_es_400(campo: str, valor: Any) -> None:
    with pytest.raises(ValidationError, match=campo):
        FacturaRequest.model_validate(cuerpo(serie="FRGG", lineas=[_linea_gg(**{campo: valor})]))


@pytest.mark.parametrize("falta", ["cuenta", "analitica"])
def test_f008_p19_linea_frgg_exige_cuenta_y_analitica(falta: str) -> None:
    linea = _linea_gg()
    del linea[falta]
    with pytest.raises(ValidationError, match=falta):
        FacturaRequest.model_validate(cuerpo(serie="FRGG", lineas=[linea]))


def test_f008_r23_cantidad_y_precio_negativos_se_admiten() -> None:
    linea = {"descripcion": "Ajuste", "cantidad": -1.0, "precio": -3.5, "iva": "I21", "producto": "MA9999"}
    peticion = FacturaRequest.model_validate(cuerpo(lineas=[linea]))
    assert peticion.lineas[0].cantidad == -1.0


@pytest.mark.parametrize("cambios", [
    {"descripcion": ""}, {"descripcion": "d" * 129}, {"cantidad": "1"}, {"precio": None},
    {"iva": ""}, {"sobra": 1}, {"paride": 0},
])
def test_f008_r23_linea_no_valida(cambios: dict[str, Any]) -> None:
    linea = {"descripcion": "x", "cantidad": 1.0, "precio": 1.0, "iva": "I21", "producto": "MA9999",
             **cambios}
    with pytest.raises(ValidationError):
        LineaSinOrigen.model_validate(linea)


@pytest.mark.parametrize("importe", [0, -1.0, 1.001, "1.00"])
def test_f008_r32_importe_de_vencimiento_no_valido(importe: Any) -> None:
    with pytest.raises(ValidationError):
        Vencimiento.model_validate({"fecha": 20261115, "importe": importe})


def test_f008_r32_vencimiento_valido() -> None:
    assert Vencimiento.model_validate({"fecha": 20261115, "importe": 10.25}).importe == 10.25


def test_f008_r1_entrada_a_origen_estricta() -> None:
    with pytest.raises(ValidationError):
        EntradaAOrigen.model_validate({"linea": "1", "canoriori": 1.0, "imporiori": 1.0})
    with pytest.raises(ValidationError):
        EntradaAOrigen.model_validate({"linea": 0, "canoriori": 1.0, "imporiori": 1.0})


def test_f008_r1_los_textos_se_recortan() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(cif_proveedor=" B00000000 ", numero_factura=" F-77 "))
    assert peticion.cif_proveedor == "B00000000"
    assert peticion.numero_factura == "F-77"


def test_f008_error_lleva_codigo_y_detalles() -> None:
    error = FacturaError("No cuadra.", codigo="totales_no_cuadran", details={"total_base": 1.0})
    assert isinstance(error, ValueError)
    assert error.codigo == "totales_no_cuadran"
    assert error.details == {"total_base": 1.0}
    assert str(error) == "No cuadra."


def test_f008_error_sin_detalles_lleva_un_dict_vacio() -> None:
    assert FacturaError("x", codigo="usuario_no_valido").details == {}


def test_f008_error_con_codigo_desconocido_falla() -> None:
    with pytest.raises(ValueError, match="desconocido"):
        FacturaError("x", codigo="me_lo_invento")


def test_f008_r24_fallo_de_linea_con_codigo_cerrado() -> None:
    fallo = FalloLineaFactura(indice=2, codigo="iva_no_valido", mensaje="m")
    assert fallo.model_dump() == {"indice": 2, "codigo": "iva_no_valido", "mensaje": "m"}
    with pytest.raises(ValidationError):
        FalloLineaFactura(indice=0, codigo="otro", mensaje="m")


def test_f008_codigos_son_conjuntos_disjuntos_de_cabecera_y_linea() -> None:
    assert "lineas_no_validas" in CODIGOS_FACTURA
    assert "iva_no_valido" in CODIGOS_LINEA_FACTURA
    assert not CODIGOS_FACTURA & CODIGOS_LINEA_FACTURA


def test_f008_r44_resultado_con_todos_sus_campos() -> None:
    resultado = FacturaResultado(
        database="ruesma", estado="previsto", committed=False, dry_run=True, cod="FR26/00001",
        con_ide=1, serie="FR", modo="mes", referencia_externa="FAC-1", totales={}, retencion=None,
        vencimientos=[], origenes=[], lineas=[], filas={}, avisos=[], pendiente_en_sigrid=[],
    )
    assert set(resultado.model_dump()) == {
        "database", "estado", "committed", "dry_run", "cod", "con_ide", "serie", "modo",
        "referencia_externa", "totales", "retencion", "vencimientos", "origenes", "lineas", "filas",
        "avisos", "pendiente_en_sigrid",
    }
    with pytest.raises(ValidationError):
        FacturaResultado.model_validate({**resultado.model_dump(), "estado": "existente"})


def test_f008_r25_paride_sin_partida_es_400() -> None:
    """F-009 R14b: `paride` solo va con `partida`; sin ella no se descarta en silencio."""
    linea = {"descripcion": "Material", "cantidad": 1.0, "precio": 5.0, "iva": "I21",
             "producto": "MA9999", "paride": 355}
    with pytest.raises(ValidationError, match="paride solo va con partida"):
        FacturaRequest.model_validate(cuerpo(origenes=[], cod_obra="0404", lineas=[linea]))
    FacturaRequest.model_validate(cuerpo(origenes=[], cod_obra="0404", lineas=[{**linea, "partida": "01"}]))


# --------------------------------------------------------------------------- #
# Enmienda 1 · T30: la linea FR con `cuenta` + `analitica`, sin producto (R23, R52)
# --------------------------------------------------------------------------- #


def _linea_fr_cuenta(**cambios: Any) -> dict[str, Any]:
    return {"descripcion": "Portes", "cantidad": 1.0, "precio": 5.0, "iva": "I21",
            "cuenta": "6290000000", "analitica": "0404.MAT", **cambios}


def test_f008_r23_linea_fr_con_cuenta_y_analitica_se_admite() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(lineas=[_linea_fr_cuenta()]))
    linea = peticion.lineas[0]
    assert (linea.producto, linea.cuenta, linea.analitica) == (None, "6290000000", "0404.MAT")


def test_f008_r23_linea_fr_con_cuenta_admite_unidad() -> None:
    peticion = FacturaRequest.model_validate(cuerpo(lineas=[_linea_fr_cuenta(unidad="UD")]))
    assert peticion.lineas[0].unidad == "UD"


def test_f008_r52_fr_mezcla_lineas_con_producto_y_con_cuenta() -> None:
    linea_producto = {"descripcion": "Material", "cantidad": 2.0, "precio": 10.0, "iva": "I21",
                      "producto": "MA9999", "partida": "01", "paride": 3, "unidad": "UD"}
    peticion = FacturaRequest.model_validate(cuerpo(origenes=["AC26/1"],
                                                    lineas=[linea_producto, _linea_fr_cuenta()]))
    assert [l.producto for l in peticion.lineas] == ["MA9999", None]


@pytest.mark.parametrize("cambios", [
    {"producto": "MA9999"},                                  # los dos juegos: ambigua
    {"producto": "MA9999", "cuenta": None},                  # producto + analitica
    {"producto": "MA9999", "analitica": None},               # producto + cuenta
], ids=["producto_cuenta_analitica", "producto_analitica", "producto_cuenta"])
def test_f008_r23_linea_fr_ambigua_es_400(cambios: dict[str, Any]) -> None:
    linea = {k: v for k, v in _linea_fr_cuenta(**cambios).items() if v is not None}
    with pytest.raises(ValidationError, match="ambigua"):
        FacturaRequest.model_validate(cuerpo(lineas=[linea]))


@pytest.mark.parametrize("falta", ["cuenta", "analitica"])
def test_f008_r23_linea_fr_con_juego_de_cuenta_incompleto_es_400(falta: str) -> None:
    linea = _linea_fr_cuenta()
    del linea[falta]
    with pytest.raises(ValidationError, match="cuenta y analitica"):
        FacturaRequest.model_validate(cuerpo(lineas=[linea]))


@pytest.mark.parametrize("cambios", [{"partida": "01"}, {"partida": "01", "paride": 5}],
                         ids=["partida", "partida_paride"])
def test_f008_r23_linea_fr_con_cuenta_y_partida_es_400(cambios: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="solo va con producto"):
        FacturaRequest.model_validate(cuerpo(lineas=[_linea_fr_cuenta(**cambios)]))


def test_f008_r23_linea_fr_sin_ningun_juego_es_400() -> None:
    linea = {"descripcion": "x", "cantidad": 1.0, "precio": 1.0, "iva": "I21", "unidad": "UD"}
    with pytest.raises(ValidationError, match="producto o cuenta y analitica"):
        FacturaRequest.model_validate(cuerpo(lineas=[linea]))


@pytest.mark.parametrize("cambios", [{"partida": "01"}, {"paride": 5}], ids=["partida", "paride"])
def test_f008_r23_linea_fr_solo_con_partida_es_400(cambios: dict[str, Any]) -> None:
    linea = {"descripcion": "x", "cantidad": 1.0, "precio": 1.0, "iva": "I21", **cambios}
    with pytest.raises(ValidationError):
        FacturaRequest.model_validate(cuerpo(lineas=[linea]))
