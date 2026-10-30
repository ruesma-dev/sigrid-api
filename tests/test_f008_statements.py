# tests/test_f008_statements.py
"""
F-008 · T8-T10 y T15: constructores puros de filas por lista blanca, lecturas
con `?` comparadas caracter a caracter, reserva de `cod` por serie y la lista
negativa. Sin red ni base; datos sinteticos.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from application.use_cases.albaran_compra_statements import DCA_COLUMNAS, DCAREC_COLUMNAS
from application.use_cases.factura_lineas import fila_dcfpro
from application.use_cases.factura_statements import (
    CONSII_COLUMNAS,
    DCAPRODES_COLUMNAS,
    DCF_HEREDABLES,
    PAG_COLUMNAS,
    FilasFactura,
    construir_con_factura,
    construir_con_pago,
    construir_consii,
    construir_dcaprodes,
    construir_dcf,
    construir_dcfrec,
    construir_log_factura,
    construir_pag,
    numerar,
    totales_factura,
)
from application.use_cases.parte_reclamacion_statements import CON_COLUMNAS, LOG_COLUMNAS

# --------------------------------------------------------------------------- #
# T8 · constructores puros
# --------------------------------------------------------------------------- #


def test_f008_r9_con_de_la_factura_con_su_estado() -> None:
    con = construir_con_factura(emp=1, fec=20261030, entres="PROVEEDOR SL", entref="F-77", est=20,
                                tiemod=46325.5)
    assert list(con) == list(CON_COLUMNAS)
    assert (con["tip"], con["emp"], con["fec"], con["est"], con["tiemod"]) == (15, 1, 20261030, 20, 46325.5)
    assert con["res"] == "PROVEEDOR SL. (F-77)"
    assert con["ide"] is None and con["cod"] is None and con["tex"] is None
    assert con["fecbaj"] == 0 and con["ico"] == "" and con["serie"] == 0


def test_f008_r9_res_se_recorta_a_128() -> None:
    con = construir_con_factura(emp=1, fec=1, entres="P" * 120, entref="N" * 20, est=1, tiemod=0.0)
    assert len(con["res"]) == 128


_HEREDADAS = {"entide": 77, "entcod": "P0077", "entres": "PROVEEDOR SL", "entcif": "B00000000",
              "obride": 404, "cenide": 41, "almide": 71, "pagide": 5, "pagtex": "120 dias",
              "pagfor": "120", "efeide": 8, "tipgar": 0, "dirdir1": "Calle"}


def _dcf(**cambios: Any) -> dict[str, Any]:
    argumentos: dict[str, Any] = {
        "heredadas": _HEREDADAS, "cueide": 4000, "ctride": 300, "fecdoc": 20261015, "hor": 101530,
        "entref": "F-77", "synckey": "FAC-1",
        "totales": {"impbru": 100.0, "impnet": 100.0, "totbas": 100.0, "totiva": 21.0,
                    "totdoc": 121.0, "tot": 116.0, "totpag": 116.0},
    }
    argumentos.update(cambios)
    return construir_dcf(**argumentos)


def test_f008_r38_dcf_por_lista_blanca_con_las_columnas_de_dca() -> None:
    dcf = _dcf()
    assert list(dcf) == list(DCA_COLUMNAS)
    assert (dcf["cla"], dcf["cueide"], dcf["synckey"], dcf["entref"], dcf["fecdoc"], dcf["hor"],
            dcf["ctride"]) == (1001, 4000, "FAC-1", "F-77", 20261015, 101530, 300)
    assert {c: dcf[c] for c in _HEREDADAS} == _HEREDADAS
    assert (dcf["totbas"], dcf["totiva"], dcf["totdoc"], dcf["tot"], dcf["totpag"], dcf["impbru"],
            dcf["impnet"]) == (100.0, 21.0, 121.0, 116.0, 116.0, 100.0, 100.0)
    for columna in ("estfac", "estser", "estped", "docoritip", "docoriide", "facoriide", "fecpag",
                    "idefac", "fecfac", "horfac", "caaide", "fecrec"):
        assert dcf[columna] == 0
    assert dcf["emptex"] is None and dcf["tex"] == "" and dcf["numregcon"] == ""


def test_f008_r38_dcf_sin_heredar_tipgar_es_menos_uno() -> None:
    assert _dcf(heredadas={"entide": 1})["tipgar"] == -1


def test_f008_r38_dcf_no_hereda_lo_que_no_esta_en_la_lista() -> None:
    with pytest.raises(ValueError, match="totbas"):
        _dcf(heredadas={**_HEREDADAS, "totbas": 1.0})
    assert "cueide" not in DCF_HEREDABLES and "synckey" not in DCF_HEREDABLES


def test_f008_r29_totales_de_las_lineas() -> None:
    lineas = [
        fila_dcfpro({"can": 2.0, "tar": 10.0, "dto": "", "tot": 20.0, "ivacuo": 4.2}),
        fila_dcfpro({"can": 1.0, "tar": 10.0, "dto": "10%", "tot": 9.0, "ivacuo": 1.89}),
        fila_dcfpro({"can": -1.0, "tar": 0.1, "dto": "", "tot": -0.1, "ivacuo": -0.02}),
    ]
    totales = totales_factura(lineas, cuo=Decimal("1.45"))
    assert totales == {"totbas": 28.9, "impnet": 28.9, "impbru": 29.9, "totiva": 6.07,
                       "totdoc": 34.97, "tot": 33.52, "totpag": 33.52, "retencion": 1.45}


def test_f008_r29_sin_retencion_tot_es_totdoc() -> None:
    totales = totales_factura([fila_dcfpro({"can": 1.0, "tar": 0.1, "tot": 0.1, "ivacuo": 0.2})],
                              cuo=Decimal(0))
    assert (totales["tot"], totales["totdoc"], totales["impbru"]) == (0.3, 0.3, 0.1)


def test_f008_r31_dcfrec_copia_el_recargo_del_origen() -> None:
    dcarec = {"recide": 558368, "pos": 64, "valdef": 1, "valpor": 0.05, "valcan": 0.0, "valmod": 0,
              "valfij": 0, "reccla": 5, "cueide": 4008, "ivaide": 0, "tex": "", "resalt": "",
              "item": 0, "ide": 9, "docide": 8, "bas": 1.0, "cuo": 2.0}
    fila = construir_dcfrec(dcarec, totbas=Decimal("1234.50"))
    assert list(fila) == list(DCAREC_COLUMNAS)
    assert (fila["recide"], fila["valpor"], fila["reccla"], fila["cueide"]) == (558368, 0.05, 5, 4008)
    # cuo = round(1234,50 * 0,05, 2) = 61,725 -> 61,73 (ROUND_HALF_UP)
    assert (fila["bas"], fila["cuo"]) == (1234.5, 61.73)
    assert fila["ide"] is None and fila["docide"] is None
    assert (fila["ivacuo"], fila["reqcuo"], fila["refide"], fila["frasupide"]) == (0, 0, 0, 0)


_DCF_PAGO = {"efeide": 8, "entide": 77, "cenide": 41, "entref": "F-77", "banide": 0, "banban": 1,
             "bansuc": 2, "bandig": "33", "bancue": "44", "ban": "ES00", "bantipide": 1}


def test_f008_r32_pag_de_vencimiento() -> None:
    pag = construir_pag(cla=0, tot=60.5, fecven=20261115, dcf=_DCF_PAGO, cueide=4000)
    assert list(pag) == list(PAG_COLUMNAS)
    assert (pag["cla"], pag["tot"], pag["fecven"], pag["cueide"], pag["retide"]) == (
        0, 60.5, 20261115, 4000, 0
    )
    assert {c: pag[c] for c in _DCF_PAGO} == _DCF_PAGO
    for columna in ("remide", "fecrea", "padide", "blofec", "bloide", "natide", "pun", "divcam"):
        assert pag[columna] == 0
    assert pag["ide"] is None and pag["conide"] is None
    assert (pag["cypref"], pag["retref"], pag["blores"], pag["cpapai"], pag["divcod"]) == ("",) * 5


def test_f008_r34_pag_de_retencion() -> None:
    pag = construir_pag(cla=2, tot=61.73, fecven=20280115, dcf=_DCF_PAGO, cueide=4008, retide=558368)
    assert (pag["cla"], pag["tot"], pag["retide"], pag["cueide"]) == (2, 61.73, 558368, 4008)


def test_f008_r32_con_del_pago() -> None:
    con = construir_con_pago(emp=1, fec=20261030, res="PROVEEDOR SL. (F-77)", indice=1, de=2,
                             tiemod=46325.5)
    assert list(con) == list(CON_COLUMNAS)
    assert (con["tip"], con["est"], con["fec"], con["res"], con["cod"]) == (
        25, 1, 20261030, "Pago 1 de 2 PROVEEDOR SL. (F-77)", None
    )


def test_f008_r38_consii_con_los_valores_medidos() -> None:
    fila = construir_consii(desope="PROVEEDOR SL. (F-77)")
    assert list(fila) == list(CONSII_COLUMNAS)
    assert (fila["pos"], fila["tipcom"], fila["tipdoc"], fila["claope"], fila["emiter"],
            fila["facsimcua"], fila["facsinide"], fila["difplaenv"], fila["desope"],
            fila["regivaide"]) == (64, "A0", "F1", "01", "N", "N", "N", "N", "PROVEEDOR SL. (F-77)", 0)
    assert fila["detinm"] is None and fila["usu"] == "" and fila["est"] == 0 and fila["fecope"] == 0
    assert fila["ide"] is None and fila["conide"] is None


def test_f008_r36_dcaprodes_de_una_linea_de_origen() -> None:
    fila = construir_dcaprodes(docproide=9001, can=3.0)
    assert list(fila) == list(DCAPRODES_COLUMNAS)
    assert (fila["docproide"], fila["can"], fila["docdestip"]) == (9001, 3.0, 15)
    assert fila["ide"] is None and fila["docdeside"] is None


def test_f008_r36_log_del_alta_de_la_factura() -> None:
    from application.use_cases.albaran_compra_statements import sellos_del_alta
    from datetime import datetime, timezone
    sellos = sellos_del_alta(datetime(2026, 10, 30, 9, 0, tzinfo=timezone.utc), 20261030, "FR")
    fila = construir_log_factura(emp=1, usu="prueba", res="r", sellos=sellos)
    assert list(fila) == list(LOG_COLUMNAS)
    assert (fila["tip"], fila["ope"], fila["tab"], fila["est"], fila["ori"], fila["usu"]) == (
        15, 1, "con", 1, 0, "prueba"
    )


def _filas() -> FilasFactura:
    con = construir_con_factura(emp=1, fec=20261030, entres="P", entref="F", est=1, tiemod=0.0)
    lineas = [fila_dcfpro({"can": 1.0}), fila_dcfpro({"can": 2.0}), fila_dcfpro({"can": 3.0})]
    return FilasFactura(
        con=con,
        dcf=_dcf(),
        dcfpro=lineas,
        dcfrec=[construir_dcfrec({c: 0 for c in DCAREC_COLUMNAS}, totbas=Decimal(1))],
        pagos=[
            (construir_con_pago(emp=1, fec=1, res="r", indice=1, de=2, tiemod=0.0),
             construir_pag(cla=0, tot=1.0, fecven=1, dcf=_DCF_PAGO, cueide=1)),
            (construir_con_pago(emp=1, fec=1, res="r", indice=2, de=2, tiemod=0.0),
             construir_pag(cla=2, tot=1.0, fecven=1, dcf=_DCF_PAGO, cueide=1, retide=5)),
        ],
        consii=construir_consii(desope="r"),
        dcaprodes=[(0, construir_dcaprodes(docproide=11, can=1.0)),
                   (2, construir_dcaprodes(docproide=13, can=3.0))],
        log={c: None for c in LOG_COLUMNAS},
    )


def test_f008_r37_numerar_pone_cod_ides_y_enlaces() -> None:
    filas = numerar(_filas(), cod="FR26/00042", ide_con=1000, ide_dcfpro=500, ide_dcfrec=70,
                    ide_consii=80, ide_dcaprodes=90, ide_log=None)
    assert (filas.con["ide"], filas.con["cod"], filas.dcf["ide"]) == (1000, "FR26/00042", 1000)
    assert [(f["ide"], f["docide"], f["pos"]) for f in filas.dcfpro] == [
        (500, 1000, 64), (501, 1000, 128), (502, 1000, 192)
    ]
    assert [(c["ide"], c["cod"], p["ide"], p["conide"]) for c, p in filas.pagos] == [
        (1001, "FR26/00042_01", 1001, 1000), (1002, "FR26/00042_02", 1002, 1000)
    ]
    assert (filas.dcfrec[0]["ide"], filas.dcfrec[0]["docide"]) == (70, 1000)
    assert (filas.consii["ide"], filas.consii["conide"]) == (80, 1000)
    assert [(f["ide"], f["docdescod"], f["docdeside"], f["lindeside"]) for _i, f in filas.dcaprodes] == [
        (90, "FR26/00042", 1000, 500), (91, "FR26/00042", 1000, 502)
    ]
    assert (filas.log["ide"], filas.log["cod"]) == (None, "FR26/00042")


def test_f008_r37_numerar_no_toca_las_filas_limpias() -> None:
    limpias = _filas()
    numerar(limpias, cod="X", ide_con=1, ide_dcfpro=1, ide_dcfrec=1, ide_consii=1, ide_dcaprodes=1,
            ide_log=1)
    assert limpias.con["ide"] is None and limpias.dcfpro[0].get("ide") is None


def test_f008_r37_numerar_exige_las_reservas_que_hacen_falta() -> None:
    with pytest.raises(ValueError, match="dcfrec"):
        numerar(_filas(), cod="X", ide_con=1, ide_dcfpro=1, ide_dcfrec=None, ide_consii=1,
                ide_dcaprodes=1, ide_log=1)
    with pytest.raises(ValueError, match="dcaprodes"):
        numerar(_filas(), cod="X", ide_con=1, ide_dcfpro=1, ide_dcfrec=1, ide_consii=1,
                ide_dcaprodes=None, ide_log=1)


def test_f008_r37_como_dict_de_la_respuesta() -> None:
    filas = numerar(_filas(), cod="X", ide_con=1, ide_dcfpro=1, ide_dcfrec=1, ide_consii=1,
                    ide_dcaprodes=1, ide_log=1)
    salida = filas.como_dict()
    assert set(salida) == {"con", "dcf", "dcfpro", "dcfrec", "con_pag", "pag", "consii",
                           "dcaprodes", "log"}
    assert len(salida["pag"]) == 2 and len(salida["dcaprodes"]) == 2
