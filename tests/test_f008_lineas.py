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
    validar_vencimientos([_v(20261015, 10.0)], fecha_factura=20261015, totpag=Decimal(10))


def test_f008_r33_730_dias_vale_y_731_no() -> None:
    # 2026-10-15 + 730 dias = 2028-10-14 (2028 es bisiesto).
    validar_vencimientos([_v(20281014, 10.0)], fecha_factura=20261015, totpag=Decimal(10))
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20281015, 10.0)], fecha_factura=20261015, totpag=Decimal(10))
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 0, "fecha": 20281015}


def test_f008_r33_anterior_a_la_factura_no_vale() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos(
            [_v(20261115, 5.0), _v(20261014, 5.0)], fecha_factura=20261015, totpag=Decimal(10)
        )
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 1, "fecha": 20261014}


def test_f008_r33_fecha_que_no_existe_no_vale() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20261131, 10.0)], fecha_factura=20261015, totpag=Decimal(10))
    assert error.value.details["posicion"] == 0


def test_f008_r33_fechas_repetidas_no_valen() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos(
            [_v(20261115, 5.0), _v(20261215, 2.0), _v(20261115, 3.0)],
            fecha_factura=20261015, totpag=Decimal(10),
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

from application.use_cases.factura_lineas import comparar_a_origen
from domain.models.factura_models import EntradaAOrigen

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


# --------------------------------------------------------------------------- #
# T6 · linea propia FRGG y constructor unico (R24, R26-R28)
# --------------------------------------------------------------------------- #

from application.use_cases.factura_lineas import (
    LecturasLineas,
    LineaResuelta,
    linea_sin_origen,
    resolver_linea_gg,
)
from domain.models.factura_models import LineaSinOrigen

_IVAS = {"i21": (777740, 0.21), "i10": (777742, 0.10), "i21nded": (777741, 0.21), "i0": (496338, 0.0)}


def _lecturas_gg(**cambios: Any) -> LecturasLineas:
    base: dict[str, Any] = {
        "ivas": _IVAS,
        "ivas_permitidos": ["I21", "I10", "I21NDED", "i0"],
        "cuentas": {"6290000000": (7001, 5), "6000000000": (7002, 4), "2160000000": (7003, 5)},
        "prefijos_cuenta": ["6"],
        "analiticas": {"gg.gen": (8001, True), "gg": (8002, False), "0404.mat": (8003, True),
                       "sinpunto": (8004, True), "zz.otra": (8005, True)},
        "obras": {"gg": (600, 61), "0404": (404, 41)},
    }
    base.update(cambios)
    return LecturasLineas(**base)


def _gg(**cambios: Any) -> LineaSinOrigen:
    datos: dict[str, Any] = {"descripcion": "Gasto general", "cantidad": 2.0, "precio": 10.125,
                             "iva": "I21", "cuenta": "6290000000", "analitica": "GG.GEN"}
    datos.update(cambios)
    return LineaSinOrigen(**datos)


def test_f008_r27_resuelve_cuenta_analitica_obra_y_centro() -> None:
    resuelta, fallos = resolver_linea_gg(_gg(), _lecturas_gg())
    assert fallos == []
    assert resuelta == LineaResuelta(
        proide=0, natide=0, paride=0, cueide=7001, caaide=8001, obride=600, cenide=61,
        almide=None, ivaide=777740, tasa_iva=0.21,
    )


def test_f008_r26_la_analitica_manda_la_obra_aunque_sea_otra() -> None:
    resuelta, _f = resolver_linea_gg(_gg(analitica="0404.MAT"), _lecturas_gg())
    assert (resuelta.obride, resuelta.cenide, resuelta.caaide) == (404, 41, 8003)


@pytest.mark.parametrize("cuenta", ["6000000000", "2160000000", "6999999999"])
def test_f008_r26_cuenta_no_hoja_fuera_de_prefijo_o_inexistente(cuenta: str) -> None:
    resuelta, fallos = resolver_linea_gg(_gg(cuenta=cuenta), _lecturas_gg())
    assert resuelta is None
    assert [codigo for codigo, _m in fallos] == ["cuenta_no_valida"]


def test_f008_r26_sin_prefijos_de_cuenta_no_vale_ninguna() -> None:
    _r, fallos = resolver_linea_gg(_gg(), _lecturas_gg(prefijos_cuenta=[]))
    assert [codigo for codigo, _m in fallos] == ["cuenta_no_valida"]


def test_f008_r26_otro_prefijo_configurado_si_vale() -> None:
    resuelta, fallos = resolver_linea_gg(_gg(cuenta="2160000000"),
                                         _lecturas_gg(prefijos_cuenta=["6", "21"]))
    assert fallos == [] and resuelta.cueide == 7003


@pytest.mark.parametrize("analitica", ["GG", "SINPUNTO", "ZZ.OTRA", "NO.EXISTE"])
def test_f008_r26_analitica_no_hoja_sin_obra_o_inexistente(analitica: str) -> None:
    _r, fallos = resolver_linea_gg(_gg(analitica=analitica), _lecturas_gg())
    assert [codigo for codigo, _m in fallos] == ["analitica_no_valida"]


def test_f008_r24_iva_fuera_de_la_lista_o_inexistente() -> None:
    _r, fallos = resolver_linea_gg(_gg(iva="I4"), _lecturas_gg())
    assert [codigo for codigo, _m in fallos] == ["iva_no_valido"]
    _r, fallos = resolver_linea_gg(_gg(iva="I21"), _lecturas_gg(ivas={}))
    assert [codigo for codigo, _m in fallos] == ["iva_no_valido"]


def test_f008_r24_el_iva_no_distingue_mayusculas() -> None:
    resuelta, fallos = resolver_linea_gg(_gg(iva="I0"), _lecturas_gg())
    assert fallos == [] and resuelta.ivaide == 496338


def test_f008_r24_los_fallos_de_una_linea_salen_juntos() -> None:
    _r, fallos = resolver_linea_gg(_gg(iva="X", cuenta="1", analitica="Y"), _lecturas_gg())
    assert [codigo for codigo, _m in fallos] == ["iva_no_valido", "cuenta_no_valida",
                                                 "analitica_no_valida"]


def test_f008_p21_un_iva_no_deducible_solo_cambia_el_ivaide() -> None:
    normal, _f = resolver_linea_gg(_gg(iva="I21"), _lecturas_gg())
    nded, _f = resolver_linea_gg(_gg(iva="I21NDED"), _lecturas_gg())
    fila_normal = linea_sin_origen(_gg(iva="I21"), normal, serie="FRGG", almide=12)
    fila_nded = linea_sin_origen(_gg(iva="I21NDED"), nded, serie="FRGG", almide=12)
    assert fila_nded["ivaide"] == 777741
    assert {**fila_nded, "ivaide": 0} == {**fila_normal, "ivaide": 0}


def test_f008_r28_constructor_unico_importes_y_ceros() -> None:
    resuelta, _f = resolver_linea_gg(_gg(), _lecturas_gg())
    fila = linea_sin_origen(_gg(), resuelta, serie="FRGG", almide=12)
    # tot = round(2 * 10,125, 2) = 20,25; ivacuo = round(20,25 * 0,21, 2) = 4,2525 -> 4,25.
    assert (fila["can"], fila["pre"], fila["tar"], fila["dto"], fila["tot"], fila["ivacuo"]) == (
        2.0, 10.125, 10.125, "", 20.25, 4.25
    )
    assert (fila["cueide"], fila["caaide"], fila["obride"], fila["cenide"], fila["almide"]) == (
        7001, 8001, 600, 61, 12
    )
    assert (fila["proide"], fila["paride"], fila["natide"]) == (0, 0, 0)
    for columna in ("docoritip", "docoriide", "linoriide", "canorilin", "canoriori", "canoriant",
                    "imporiori", "imporiant", "canfac"):
        assert fila[columna] == 0
    assert fila["docoricod"] == ""
    assert fila["res"] == "Gasto general"
    assert fila["unimed"] == ""


def test_f008_r28_redondeo_half_up() -> None:
    resuelta = LineaResuelta(proide=0, natide=0, paride=0, cueide=1, caaide=1, obride=1, cenide=1,
                             almide=None, ivaide=1, tasa_iva=0.21)
    fila = linea_sin_origen(_gg(cantidad=1.0, precio=2.675), resuelta, serie="FRGG", almide=1)
    assert fila["tot"] == 2.68
    fila = linea_sin_origen(_gg(cantidad=1.0, precio=0.5), resuelta, serie="FRGG", almide=1)
    assert fila["ivacuo"] == 0.11


def test_f008_r28_negativos_se_admiten() -> None:
    resuelta = LineaResuelta(proide=0, natide=0, paride=0, cueide=1, caaide=1, obride=1, cenide=1,
                             almide=None, ivaide=1, tasa_iva=0.21)
    fila = linea_sin_origen(_gg(cantidad=-1.0, precio=10.0), resuelta, serie="FRGG", almide=1)
    assert (fila["tot"], fila["ivacuo"]) == (-10.0, -2.1)


@pytest.mark.parametrize("serie", ["FR", "FRGG"])
def test_f008_r28_el_almacen_de_la_linea_manda_si_lo_tiene(serie: str) -> None:
    resuelta = LineaResuelta(proide=5, natide=6, paride=7, cueide=1, caaide=2, obride=3, cenide=4,
                             almide=88, ivaide=9, tasa_iva=0.1)
    linea = LineaSinOrigen(descripcion="d", cantidad=1.0, precio=1.0, iva="I10",
                           **({"producto": "MA9999", "unidad": "UD"} if serie == "FR"
                              else {"cuenta": "6", "analitica": "GG.GEN"}))
    fila = linea_sin_origen(linea, resuelta, serie=serie, almide=12)
    assert fila["almide"] == 88
    assert (fila["proide"], fila["natide"], fila["paride"]) == (5, 6, 7)
    assert fila["unimed"] == ("UD" if serie == "FR" else "")


def test_f008_r28_serie_desconocida_falla() -> None:
    resuelta, _f = resolver_linea_gg(_gg(), _lecturas_gg())
    with pytest.raises(ValueError, match="serie"):
        linea_sin_origen(_gg(), resuelta, serie="AB", almide=1)


# --------------------------------------------------------------------------- #
# T7 · linea propia FR con las reglas de F-009 (R25, R28)
# --------------------------------------------------------------------------- #

from application.use_cases.albaran_compra_statements import naturalezas_elegidas  # noqa: E402
from application.use_cases.factura_lineas import (
    naturalezas_con_cuenta,
    naturalezas_resueltas,
    resolver_linea_fr,
    resolver_partida,
)


def _lecturas_fr(**cambios: Any) -> LecturasLineas:
    base: dict[str, Any] = {
        "ivas": _IVAS,
        "ivas_permitidos": ["I21", "I10"],
        "productos_permitidos": ["MA9999", "SM9999", "QA9999"],
        # (ide, cod, fecbaj, tipmov), como L7 de F-009.
        "productos": {"ma9999": [(31, "MA9999", 0, 1)], "sm9999": [(32, "SM9999", 20200101, 0)]},
        "naturalezas": {"MA9999": (51, 52, 53), "QA9999": "naturaleza_no_valida"},
        # (ide, cod, tip, tipdes, tipvis), como L6 de F-009.
        "partidas": {
            "01": [(901, "01", 1, 0, 0)],
            "02": [(902, "02", 0, 0, 0)],
            "03": [(903, "03", 1, 0, 1), (904, "03", 1, 0, 0)],
            "04": [(905, "04", 1, 1, 0)],
        },
        "obride": 404,
        "almacen": (71, 72),
    }
    base.update(cambios)
    return LecturasLineas(**base)


def _fr(**cambios: Any) -> LineaSinOrigen:
    datos: dict[str, Any] = {"descripcion": "Material", "cantidad": 1.0, "precio": 3.0, "iva": "I21",
                             "producto": "MA9999"}
    datos.update(cambios)
    return LineaSinOrigen(**datos)


def test_f008_r25_resuelve_producto_naturaleza_cuenta_y_analitica() -> None:
    resuelta, fallos = resolver_linea_fr(_fr(partida="01"), _lecturas_fr())
    assert fallos == []
    assert resuelta == LineaResuelta(proide=31, natide=51, paride=901, cueide=52, caaide=53,
                                     obride=404, cenide=72, almide=71, ivaide=777740, tasa_iva=0.21)


def test_f008_r25_sin_partida_es_cero() -> None:
    resuelta, _f = resolver_linea_fr(_fr(), _lecturas_fr())
    assert resuelta.paride == 0


@pytest.mark.parametrize("producto,codigo", [
    ("XA9999", "producto_no_permitido"),
    ("SM9999", "producto_no_encontrado"),
    ("QA9999", "producto_no_encontrado"),
])
def test_f008_r25_producto_no_permitido_o_no_encontrado(producto: str, codigo: str) -> None:
    _r, fallos = resolver_linea_fr(_fr(producto=producto), _lecturas_fr())
    assert [c for c, _m in fallos] == [codigo]


@pytest.mark.parametrize("codigo", ["naturaleza_no_valida", "analitica_no_resuelta"])
def test_f008_r25_fallos_de_la_naturaleza(codigo: str) -> None:
    _r, fallos = resolver_linea_fr(_fr(), _lecturas_fr(naturalezas={"MA9999": codigo}))
    assert [c for c, _m in fallos] == [codigo]


@pytest.mark.parametrize("origen,dice,no_dice", [
    ("forzada", "SIGRID_FACTURA_NATURALEZA_FORZADA", "ficha"),
    ("ficha", "ficha", "FORZADA"),
])
def test_f008_r50_naturaleza_no_valida_dice_de_donde_venia(origen: str, dice: str, no_dice: str) -> None:
    _r, fallos = resolver_linea_fr(_fr(), _lecturas_fr(naturalezas={"MA9999": "naturaleza_no_valida"},
                                                       origenes_naturaleza={"MA9999": origen}))
    ((codigo, mensaje),) = fallos
    assert codigo == "naturaleza_no_valida" and dice in mensaje and no_dice not in mensaje


def test_f008_r50_analitica_no_resuelta_con_el_mensaje_de_siempre() -> None:
    _r, fallos = resolver_linea_fr(_fr(), _lecturas_fr(naturalezas={"MA9999": "analitica_no_resuelta"},
                                                       origenes_naturaleza={"MA9999": "ficha"}))
    assert fallos == [("analitica_no_resuelta", "La obra no tiene la cuenta analitica de la naturaleza "
                                                "del producto en su centro: alta a mano.")]


def test_f008_r25_lista_blanca_vacia_no_admite_ninguno() -> None:
    _r, fallos = resolver_linea_fr(_fr(), _lecturas_fr(productos_permitidos=[]))
    assert [c for c, _m in fallos] == ["producto_no_permitido"]


@pytest.mark.parametrize("partida,paride,esperado", [
    ("01", None, (901, None)),
    ("01", 901, (901, None)),
    ("01", 999, (None, "paride_no_valido")),
    ("99", None, (None, "partida_no_encontrada")),
    ("02", None, (None, "partida_no_imputable")),
    ("04", None, (None, "partida_no_imputable")),
    ("03", None, (None, "partida_ambigua")),
    ("03", 904, (904, None)),
    (None, None, (0, None)),
])
def test_f008_r25_partida_con_las_reglas_de_f009(
    partida: str | None, paride: int | None, esperado: tuple[Any, Any]
) -> None:
    valor, fallo = resolver_partida(_fr(partida=partida, paride=paride), _lecturas_fr().partidas)
    assert (valor, fallo[0] if fallo else None) == esperado


def test_f008_r25_partida_con_tipvis_2_no_es_imputable() -> None:
    _v, fallo = resolver_partida(_fr(partida="05"), {"05": [(906, "05", 1, 0, 2)]})
    assert fallo[0] == "partida_no_imputable"


def test_f008_r24_r25_todos_los_fallos_de_la_linea_juntos() -> None:
    _r, fallos = resolver_linea_fr(_fr(producto="XA9999", partida="99", iva="I4"), _lecturas_fr())
    assert [c for c, _m in fallos] == ["iva_no_valido", "producto_no_permitido",
                                       "partida_no_encontrada"]


def test_f008_r28_fr_y_frgg_salen_por_el_mismo_constructor() -> None:
    resuelta, _f = resolver_linea_fr(_fr(unidad="UD"), _lecturas_fr())
    fila = linea_sin_origen(_fr(unidad="UD"), resuelta, serie="FR", almide=1)
    assert (fila["proide"], fila["natide"], fila["cueide"], fila["caaide"], fila["almide"],
            fila["cenide"], fila["obride"], fila["unimed"], fila["tot"], fila["ivacuo"]) == (
        31, 51, 52, 53, 71, 72, 404, "UD", 3.0, 0.63)


# --- naturaleza de F-009 R13b, en tres pasos puros ------------------------------

_NAT = {  # (ide, cod, numemp, fecbaj, caagascod, cuacomcod), como L15A de F-009.
    "ma99": [(51, "MA99", 0, 0, "MOD.MAT", "6000000000")],
    "sm99": [(61, "SM99", 2, 0, "SUB", "6070000000"), (62, "SM99", 1, 0, "SUB", "6070000000")],
    "qa99": [(71, "QA99", 1, 20200101, "X", "6000000000")],
    "xa99": [(81, "XA99", 1, 0, "X", "  ")],
    "rep": [(91, "REP", 0, 0, "X", "1"), (92, "REP", 1, 0, "X", "1")],
}


def test_f008_r25_naturalezas_validas_por_empresa_y_baja() -> None:
    """Enmienda 1: `naturalezas_validas` desaparece en favor de la regla comun
    `naturalezas_elegidas`; con todo forzado, la misma regla y el mismo resultado."""
    mapeados = {"MA9999": "MA99", "SM9999": "SM99", "QA9999": "QA99", "XA9999": "XA99",
                "R": "REP", "N": "NADA"}
    validas, _origenes = naturalezas_elegidas(
        dict.fromkeys(mapeados, 1), {f"1:{p}": c for p, c in mapeados.items()}, _NAT, {}, emp=1,
    )
    assert {p: f[0] for p, f in validas.items()} == {"MA9999": 51, "SM9999": 62}


def test_f008_r25_naturalezas_con_una_sola_cuenta() -> None:
    validas = {"MA9999": _NAT["ma99"][0], "SM9999": _NAT["sm99"][1]}
    cuentas = {"6000000000": [(4001, "6000000000")], "6070000000": [(4002, "x"), (4003, "x")]}
    assert naturalezas_con_cuenta(validas, cuentas) == {"MA9999": (_NAT["ma99"][0], 4001)}


def test_f008_r25_naturalezas_resueltas_con_la_analitica_del_centro() -> None:
    con_cuenta = {"MA9999": (_NAT["ma99"][0], 4001), "SM9999": (_NAT["sm99"][1], 4002),
                  "ZZ": ((99, "ZZ", 0, 0, "", "1"), 4003)}
    analiticas = {"0404.mat": [(3001, "0404.MAT", 72), (3002, "0404.MAT", 99)],
                  "0404.sub": [(3003, "0404.SUB", 99)]}
    resultado = naturalezas_resueltas(
        ["MA9999", "SM9999", "ZZ", "SIN"], con_cuenta, analiticas, cod_obra="0404 ", centro=72,
    )
    assert resultado == {"MA9999": (51, 4001, 3001), "SM9999": "analitica_no_resuelta",
                         "ZZ": "analitica_no_resuelta", "SIN": "naturaleza_no_valida"}


# --- Enmienda 1 · T27: forzada por `<emp>:<producto>` o la de la ficha ------------

from application.use_cases.albaran_compra_statements import naturalezas_elegidas  # noqa: E402

#: L15D: (p.ide, p.natide, n.cod, n.numemp, n.fecbaj, n.caagascod, n.cuacomcod).
_FICHA = {
    31: (31, 15, "MA1501", 0, 0, "MOD.CDMA15", "6010000000"),      # valida
    32: (32, 0, None, None, None, None, None),                     # natide 0
    33: (33, None, None, None, None, None, None),                  # natide NULL
    34: (34, 77, None, None, None, None, None),                    # sin auxpronat
    35: (35, 16, "BAJA", 0, 20200101, "X", "6000000000"),          # de baja
    36: (36, 17, "AJENA", 2, 0, "X", "6000000000"),                # numemp ajeno
    37: (37, 18, "SINCUA", 1, 0, "X", "  "),                       # sin cuacomcod
    38: (38, 19, "PROPIA", 1, 0, "MOD.P", "6020000000"),           # numemp de la empresa
}


def test_f008_r49_forzada_de_la_empresa_manda_sobre_la_ficha() -> None:
    validas, origenes = naturalezas_elegidas(
        {"MA9999": 31}, {"1:MA9999": "MA99"}, _NAT, _FICHA, emp=1,
    )
    assert validas == {"MA9999": _NAT["ma99"][0]}
    assert origenes == {"MA9999": "forzada"}


def test_f008_r49_forzada_de_otra_empresa_no_aplica_y_manda_la_ficha() -> None:
    validas, origenes = naturalezas_elegidas(
        {"MA9999": 31}, {"31:MA9999": "MA99"}, _NAT, _FICHA, emp=1,
    )
    assert validas == {"MA9999": (15, "MA1501", 0, 0, "MOD.CDMA15", "6010000000")}
    assert origenes == {"MA9999": "ficha"}


def test_f008_r49_r50_la_ficha_valida_o_rechazada_por_cada_motivo() -> None:
    productos = {f"P{proide}": proide for proide in _FICHA}
    validas, origenes = naturalezas_elegidas(productos, {}, _NAT, _FICHA, emp=1)
    assert validas == {
        "P31": (15, "MA1501", 0, 0, "MOD.CDMA15", "6010000000"),
        "P38": (19, "PROPIA", 1, 0, "MOD.P", "6020000000"),
    }
    assert origenes == {p: "ficha" for p in productos}


def test_f008_r50_sin_fila_de_ficha_no_es_valida() -> None:
    validas, origenes = naturalezas_elegidas({"X": 999}, {}, _NAT, _FICHA, emp=1)
    assert (validas, origenes) == ({}, {"X": "ficha"})


@pytest.mark.parametrize("forzada,esperada", [
    ("SM99", 62),       # dos filas, una de la empresa: la de la empresa (regla del mapeo viejo, R53)
    ("QA99", None),     # de baja
    ("XA99", None),     # sin cuacomcod
    ("REP", None),      # dos validas: ambigua
    ("NADA", None),     # no existe
    (" ma99 ", 51),     # comparada como el ERP
])
def test_f008_r53_la_forzada_sigue_la_regla_del_mapeo_viejo(forzada: str, esperada: int | None) -> None:
    validas, origenes = naturalezas_elegidas({"P": 31}, {"1:P": forzada}, _NAT, _FICHA, emp=1)
    assert ({p: f[0] for p, f in validas.items()}.get("P"), origenes) == (esperada, {"P": "forzada"})


def test_f008_r49_mezcla_de_forzadas_y_de_ficha() -> None:
    validas, origenes = naturalezas_elegidas(
        {"MA9999": 31, "SM370001": 38}, {"1:MA9999": "MA99", "34:SM370001": "SM37"}, _NAT, _FICHA,
        emp=1,
    )
    assert {p: f[0] for p, f in validas.items()} == {"MA9999": 51, "SM370001": 19}
    assert origenes == {"MA9999": "forzada", "SM370001": "ficha"}
