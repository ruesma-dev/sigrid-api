# tests/test_f008_lineas.py
"""
F-008 · T3-T7: funciones puras de `factura_lineas` (vencimientos, linea de
origen, comparacion a origen, resolvedores por serie y constructor unico de la
linea sin origen). Sin red ni base; datos sinteticos y casos anonimos de M63.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from application.use_cases.factura_lineas import (
    DCFPRO_COLUMNAS,
    fecha_de_vencimiento_valida,
    linea_de_origen,
    validar_vencimientos,
)
from domain.models.factura_models import FacturaError, Vencimiento


def _v(fecha: int, importe: float) -> Vencimiento:
    return Vencimiento(fecha=fecha, importe=importe)


# --------------------------------------------------------------------------- #
# T3 · vencimientos (R33-R35)
# --------------------------------------------------------------------------- #


def test_f008_r33_vencimientos_validos_no_dicen_nada() -> None:
    validar_vencimientos(
        [_v(20261115, 60.5), _v(20261215, 60.5)], fecha_factura=20261015, totpag=Decimal("121.00")
    )


def test_f008_r33_el_mismo_dia_de_la_factura_vale() -> None:
    validar_vencimientos([_v(20261015, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))


def test_f008_r33_730_dias_vale_y_731_no() -> None:
    # 2026-10-15 + 730 dias = 2028-10-14 (2028 es bisiesto).
    validar_vencimientos([_v(20281014, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20281015, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 0, "fecha": 20281015}


def test_f008_r33_anterior_a_la_factura_no_vale() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos(
            [_v(20261115, 5.0), _v(20261014, 5.0)], fecha_factura=20261015, totpag=Decimal("10")
        )
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 1, "fecha": 20261014}


def test_f008_r33_fecha_que_no_existe_no_vale() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20261131, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))
    assert error.value.details["posicion"] == 0


def test_f008_r33_fechas_repetidas_no_valen() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos(
            [_v(20261115, 5.0), _v(20261215, 2.0), _v(20261115, 3.0)],
            fecha_factura=20261015, totpag=Decimal("10"),
        )
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 2, "fecha": 20261115}


@pytest.mark.parametrize("totpag", ["10.01", "9.99"])
def test_f008_r33_la_suma_cuadra_con_un_centimo(totpag: str) -> None:
    validar_vencimientos([_v(20261115, 7.0), _v(20261215, 3.0)], fecha_factura=20261015,
                         totpag=Decimal(totpag))


@pytest.mark.parametrize("totpag", ["10.02", "9.98"])
def test_f008_r33_la_suma_no_cuadra_con_dos_centimos(totpag: str) -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20261115, 7.0), _v(20261215, 3.0)], fecha_factura=20261015,
                             totpag=Decimal(totpag))
    assert error.value.codigo == "vencimientos_no_cuadran"
    assert error.value.details == {"suma_vencimientos": 10.0, "totpag": float(Decimal(totpag))}


def test_f008_r33_la_suma_se_hace_en_decimal() -> None:
    # 0,1 + 0,2 en binario es 0,30000000000000004.
    validar_vencimientos([_v(20261115, 0.1), _v(20261116, 0.2)], fecha_factura=20261015,
                         totpag=Decimal("0.30"))


@pytest.mark.parametrize("fecha,esperado", [
    (20261015, True), (20281014, True), (20281015, False), (20261014, False), (20260230, False),
    (99999999, False), (0, False),
])
def test_f008_r34_fecha_de_vencimiento_valida(fecha: int, esperado: bool) -> None:
    assert fecha_de_vencimiento_valida(fecha, fecha_factura=20261015) is esperado


# --------------------------------------------------------------------------- #
# T4 · linea de origen (R12, R17, R19, R20), igual en FR y FRGG
# --------------------------------------------------------------------------- #

#: Una `dcapro` de albaran sintetica, con todo lo que R17 copia.
DCAPRO: dict[str, Any] = {
    "ide": 9001, "docide": 800, "pos": 64, "proide": 41, "can": 3.0, "pre": 12.5, "tar": 13.0,
    "dto": "", "tot": 37.5, "ivaide": 7, "ivacuo": 7.88, "cenide": 55, "caaide": 66, "paride": 77,
    "natide": 88, "almide": 99, "obride": 500, "res": "Hormigon", "tex": "nota", "cod2": "C2",
    "unimed": "m3", "prepma": 11.1, "dncide": 3, "dncproide": 4, "canfac": 0.0, "linoriide": 0,
    "canorilin": 0, "canoriori": 0.0, "imporiori": 0.0,
}
_COPIADAS = ("proide", "can", "pre", "tar", "dto", "tot", "ivaide", "ivacuo", "cenide", "caaide",
             "paride", "natide", "almide", "obride", "res", "tex", "cod2", "unimed", "prepma",
             "dncide", "dncproide")


def test_f008_r17_la_linea_de_origen_copia_su_dcapro_sin_recalcular() -> None:
    fila = linea_de_origen(DCAPRO, None, modo="mes", cueide=4009, docoricod="AC26/00100")
    assert {c: fila[c] for c in _COPIADAS} == {c: DCAPRO[c] for c in _COPIADAS}
    assert fila["docoritip"] == 14
    assert fila["docoricod"] == "AC26/00100"
    assert fila["docoriide"] == 800
    assert fila["linoriide"] == 9001
    assert fila["canorilin"] == 0


def test_f008_r12_la_cuenta_es_la_de_facturas_pendientes_del_proveedor() -> None:
    assert linea_de_origen(DCAPRO, None, modo="mes", cueide=4009, docoricod="x")["cueide"] == 4009


def test_f008_r17_la_fila_trae_exactamente_las_columnas_de_dcfpro_salvo_numeracion() -> None:
    fila = linea_de_origen(DCAPRO, None, modo="mes", cueide=1, docoricod="x")
    assert list(fila) == [c for c in DCFPRO_COLUMNAS if c not in ("ide", "docide", "pos")]
    assert fila["canfac"] == 0 and fila["canser"] == 0 and fila["apuide"] == 0
    assert fila["texcom"] is None and fila["med"] is None
    assert fila["refent"] == "" and fila["pac"] == ""


def test_f008_r19_en_mes_canoriori_es_can_e_imporiori_es_tot() -> None:
    fila = linea_de_origen({**DCAPRO, "canoriori": 99.0, "imporiori": 999.0}, None, modo="mes",
                           cueide=1, docoricod="x")
    assert (fila["canoriori"], fila["imporiori"], fila["canoriant"], fila["imporiant"]) == (
        3.0, 37.5, 0, 0
    )


def test_f008_r19_en_mes_se_ignora_la_anterior() -> None:
    anterior = {"canoriori": 5.0, "imporiori": 50.0}
    fila = linea_de_origen(DCAPRO, anterior, modo="mes", cueide=1, docoricod="x")
    assert (fila["canoriant"], fila["imporiant"]) == (0, 0)


# Casos anonimos de M63: (continuada?, vinculada?) -> columnas a origen.
def test_f008_r20_origen_continuada_vinculada() -> None:
    dcapro = {**DCAPRO, "linoriide": 3333, "canorilin": 8000, "canoriori": 10.0, "imporiori": 500.0}
    fila = linea_de_origen(dcapro, {"canoriori": 7.0, "imporiori": 350.0}, modo="origen",
                           cueide=1, docoricod="x")
    assert (fila["canoriori"], fila["canoriant"], fila["imporiant"], fila["imporiori"]) == (
        10.0, 7.0, 350.0, 500.0
    )


def test_f008_r20_origen_continuada_sin_vincular() -> None:
    dcapro = {**DCAPRO, "linoriide": 0, "canorilin": 8000, "canoriori": 10.0, "imporiori": 1.0,
              "tot": 37.5}
    fila = linea_de_origen(dcapro, {"canoriori": 7.0, "imporiori": 350.1}, modo="origen",
                           cueide=1, docoricod="x")
    assert (fila["canoriori"], fila["canoriant"], fila["imporiant"], fila["imporiori"]) == (
        10.0, 7.0, 350.1, 387.6
    )


def test_f008_r20_origen_nueva_vinculada() -> None:
    dcapro = {**DCAPRO, "linoriide": 3333, "canorilin": 0, "canoriori": 3.0, "imporiori": 900.0}
    fila = linea_de_origen(dcapro, None, modo="origen", cueide=1, docoricod="x")
    assert (fila["canoriori"], fila["canoriant"], fila["imporiant"], fila["imporiori"]) == (
        3.0, 0, 0, 900.0
    )


def test_f008_r20_origen_nueva_sin_vincular() -> None:
    dcapro = {**DCAPRO, "linoriide": 0, "canorilin": 0, "canoriori": 3.0, "imporiori": 5.0}
    fila = linea_de_origen(dcapro, None, modo="origen", cueide=1, docoricod="x")
    assert (fila["canoriori"], fila["canoriant"], fila["imporiant"], fila["imporiori"]) == (
        3.0, 0, 0, 37.5
    )


def test_f008_r20_la_suma_a_origen_es_decimal() -> None:
    dcapro = {**DCAPRO, "linoriide": 0, "tot": 0.2}
    fila = linea_de_origen(dcapro, {"canoriori": 1.0, "imporiori": 0.1}, modo="origen",
                           cueide=1, docoricod="x")
    assert fila["imporiori"] == 0.3


def test_f008_r20_valores_nulos_del_origen_cuentan_como_cero() -> None:
    dcapro = {**DCAPRO, "linoriide": None, "canoriori": None, "imporiori": None}
    fila = linea_de_origen(dcapro, {"canoriori": None, "imporiori": None}, modo="origen",
                           cueide=1, docoricod="x")
    assert (fila["canoriori"], fila["canoriant"], fila["imporiant"], fila["imporiori"]) == (
        0.0, 0.0, 0.0, 37.5
    )


def test_f008_r20_modo_desconocido_falla() -> None:
    with pytest.raises(ValueError, match="modo"):
        linea_de_origen(DCAPRO, None, modo="trimestre", cueide=1, docoricod="x")


def test_f008_r38_fila_dcfpro_rechaza_columnas_ajenas() -> None:
    from application.use_cases.factura_lineas import fila_dcfpro
    with pytest.raises(ValueError, match="no son de dcfpro"):
        fila_dcfpro({"proide": 1, "inventada": 2})
    fila = fila_dcfpro({"proide": 1})
    assert fila["proide"] == 1 and fila["res"] == "" and fila["desesp"] is None and fila["can"] == 0


# --------------------------------------------------------------------------- #
# T5 · comparacion a origen (R21, R22)
# --------------------------------------------------------------------------- #

from application.use_cases.factura_lineas import comparar_a_origen  # noqa: E402
from domain.models.factura_models import EntradaAOrigen  # noqa: E402

_CALCULADAS = [
    {"linoriide": 11, "canoriori": 10.0, "imporiori": 500.0},
    {"linoriide": 12, "canoriori": 2.5, "imporiori": 30.25},
]


def _e(linea: int, canoriori: float, imporiori: float) -> EntradaAOrigen:
    return EntradaAOrigen(linea=linea, canoriori=canoriori, imporiori=imporiori)


def test_f008_r22_iguales_no_dice_nada() -> None:
    comparar_a_origen(_CALCULADAS, [_e(12, 2.5, 30.25), _e(11, 10.0, 500.0)])


def test_f008_r22_en_el_borde_de_la_tolerancia_cuadra() -> None:
    comparar_a_origen(_CALCULADAS, [_e(11, 10.001, 500.01), _e(12, 2.499, 30.24)])


@pytest.mark.parametrize("canoriori,imporiori", [(10.002, 500.0), (9.998, 500.0),
                                                 (10.0, 500.02), (10.0, 499.98)])
def test_f008_r22_fuera_de_tolerancia_no_cuadra(canoriori: float, imporiori: float) -> None:
    with pytest.raises(FacturaError) as error:
        comparar_a_origen(_CALCULADAS, [_e(11, canoriori, imporiori), _e(12, 2.5, 30.25)])
    assert error.value.codigo == "a_origen_no_cuadra"
    assert error.value.details == {"lineas": [{
        "linea": 11,
        "calculado": {"canoriori": 10.0, "imporiori": 500.0},
        "enviado": {"canoriori": canoriori, "imporiori": imporiori},
    }]}


def test_f008_r22_lista_todas_las_que_no_cuadran() -> None:
    with pytest.raises(FacturaError) as error:
        comparar_a_origen(_CALCULADAS, [_e(11, 1.0, 500.0), _e(12, 2.5, 1.0)])
    assert [l["linea"] for l in error.value.details["lineas"]] == [11, 12]


def test_f008_r21_sin_a_origen_faltan_todas() -> None:
    with pytest.raises(FacturaError) as error:
        comparar_a_origen(_CALCULADAS, None)
    assert error.value.codigo == "a_origen_incompleto"
    assert error.value.details == {"faltan": [11, 12], "sobran": [], "repetidas": []}


def test_f008_r21_faltas_sobras_y_repetidas() -> None:
    with pytest.raises(FacturaError) as error:
        comparar_a_origen(_CALCULADAS, [_e(12, 2.5, 30.25), _e(12, 2.5, 30.25), _e(99, 1.0, 1.0)])
    assert error.value.codigo == "a_origen_incompleto"
    assert error.value.details == {"faltan": [11], "sobran": [99], "repetidas": [12]}


def test_f008_r21_solo_sobra_una() -> None:
    with pytest.raises(FacturaError) as error:
        comparar_a_origen(_CALCULADAS, [_e(11, 10.0, 500.0), _e(12, 2.5, 30.25), _e(13, 0.0, 0.0)])
    assert error.value.details == {"faltan": [], "sobran": [13], "repetidas": []}
