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

from application.use_cases.albaran_compra_statements import (
    DCA_COLUMNAS,
    DCAREC_COLUMNAS,
)
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
from application.use_cases.parte_reclamacion_statements import (
    CON_COLUMNAS,
    LOG_COLUMNAS,
)

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
    from datetime import datetime, timezone

    from application.use_cases.albaran_compra_statements import sellos_del_alta
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


# --------------------------------------------------------------------------- #
# T9 · lecturas con `?`, comparadas caracter a caracter
# --------------------------------------------------------------------------- #

from application.use_cases.factura_statements import (
    APPLOCKS_FACTURA,
    FacturaStatements,
    prefijo_y_cifras,
)

S = FacturaStatements(database="ruesma")


def test_f008_r9_conest_de_factura_albaran_y_pago() -> None:
    assert S.leer_estados() == (
        "SELECT tip, est, cod FROM dbo.conest WHERE tip IN (?, ?, ?)", [15, 14, 25]
    )


def test_f008_r10_proveedor_por_ide() -> None:
    assert S.leer_proveedor(77) == (
        "SELECT v.ide, c.cod, v.raz, v.cif, v.tipcif, v.cifpai, v.cueide, v.cuepdtide, v.pagide, "
        "v.efeide, v.eioide, v.banban, v.bansuc, v.bandig, v.bancue, v.ban, v.bantipide "
        "FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide WHERE v.ide = ?",
        [77],
    )


def test_f008_r10_forma_de_pago() -> None:
    assert S.leer_auxpag(5) == ("SELECT res, formul FROM dbo.auxpag WHERE ide = ?", [5])


def test_f008_r11_obras_de_la_empresa() -> None:
    assert S.leer_obras(1, ["GG", "0404"]) == (
        "SELECT c.ide, c.cod, o.cenide FROM dbo.con c JOIN dbo.obr o ON o.ide = c.ide "
        "WHERE c.tip = ? AND c.emp = ? AND c.cod IN (?, ?)",
        [42, 1, "GG", "0404"],
    )


def test_f008_r13_origenes_por_codigo() -> None:
    assert S.leer_origenes(["AC26/1", "PROF26/2"]) == (
        "SELECT c.ide, c.cod, c.emp, c.est, d.entide, d.obride, d.ctride, d.docoritip "
        "FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = ? AND c.cod IN (?, ?)",
        [14, "AC26/1", "PROF26/2"],
    )


def test_f008_r13_cabecera_del_primer_origen() -> None:
    sql, params = S.leer_cabecera_de_origen(800)
    assert sql == (
        "SELECT entide, entcod, entres, entcif, entciftip, entcifpai, obride, cenide, almide, "
        "empide, diremp1, dircon1, dirdir1, pagide, pagtex, pagfor, efeide, eioide, ivadif, cocide, "
        "tipgar, fecent, feclim, banban, bansuc, bandig, bancue, ban, bantipide FROM dbo.dca WHERE ide = ?"
    )
    assert params == [800]


def test_f008_r14_asientos_de_los_origenes() -> None:
    assert S.leer_asientos(1, ["AC26/1"]) == (
        "SELECT cod FROM dbo.con WHERE tip = ? AND emp = ? AND cod IN (?)", [20, 1, "AC26/1"]
    )


_COLUMNAS_LINEA = (
    "p.ide, p.docide, p.pos, p.proide, p.can, p.pre, p.tar, p.dto, p.tot, p.ivaide, p.ivacuo, "
    "p.cenide, p.caaide, p.paride, p.natide, p.almide, p.obride, p.res, p.tex, p.cod2, p.unimed, "
    "p.prepma, p.dncide, p.dncproide, p.canfac, p.linoriide, p.canorilin, p.canoriori, p.imporiori, "
    "p.docoritip"
)


def test_f008_r15_r17_lineas_de_los_origenes() -> None:
    assert S.leer_lineas_de_origenes([800, 801]) == (
        f"SELECT {_COLUMNAS_LINEA} FROM dbo.dcapro p WHERE p.docide IN (?, ?) "
        "ORDER BY p.docide, p.pos, p.ide",
        [800, 801],
    )


def test_f008_r15_lineas_de_los_origenes_bajo_bloqueo() -> None:
    assert S.bloquear_lineas_de_origenes([800]) == (
        f"SELECT {_COLUMNAS_LINEA} FROM dbo.dcapro p WITH (UPDLOCK, HOLDLOCK) WHERE p.docide IN (?) "
        "ORDER BY p.docide, p.pos, p.ide",
        [800],
    )


def test_f008_r15_lineas_ya_facturadas() -> None:
    assert S.leer_facturadas([800]) == (
        "SELECT d.docproide FROM dbo.dcaprodes d JOIN dbo.dcapro p ON p.ide = d.docproide "
        "WHERE p.docide IN (?) AND d.docdestip = ?",
        [800, 15],
    )


def test_f008_r14_cabeceras_de_origen_bajo_bloqueo() -> None:
    assert S.bloquear_origenes([800, 801]) == (
        "SELECT c.ide, c.cod, c.emp, c.est, d.entide, d.obride, d.ctride, d.docoritip "
        "FROM dbo.con c WITH (UPDLOCK, HOLDLOCK) JOIN dbo.dca d WITH (UPDLOCK, HOLDLOCK) "
        "ON d.ide = c.ide WHERE c.ide IN (?, ?)",
        [800, 801],
    )


def test_f008_r20_lineas_anteriores() -> None:
    assert S.leer_anteriores([7, 8]) == (
        "SELECT ide, canoriori, imporiori FROM dbo.dcapro WHERE ide IN (?, ?)", [7, 8]
    )


def test_f008_r31_retenciones_de_los_origenes() -> None:
    assert S.leer_retenciones([800]) == (
        "SELECT r.docide, r.recide, r.pos, r.valdef, r.valpor, r.valcan, r.valmod, r.valfij, "
        "r.reccla, r.cueide, r.ivaide, r.tex, r.resalt, r.item FROM dbo.dcarec r "
        "WHERE r.docide IN (?) ORDER BY r.docide, r.pos, r.ide",
        [800],
    )


def test_f008_r24_ivas_de_la_empresa() -> None:
    assert S.leer_ivas(1, ["I21", "I10NDED"]) == (
        "SELECT c.ide, c.cod, i.iva FROM dbo.con c JOIN dbo.iva i ON i.ide = c.ide "
        "WHERE c.tip = ? AND c.emp = ? AND c.cod IN (?, ?)",
        [23, 1, "I21", "I10NDED"],
    )


def test_f008_r26_cuentas_de_gasto() -> None:
    assert S.leer_cuentas_gasto(1, ["6290000000"]) == (
        "SELECT c.ide, c.cod, a.niv FROM dbo.con c JOIN dbo.cua a ON a.ide = c.ide "
        "WHERE c.tip = ? AND c.emp = ? AND c.cod IN (?)",
        [17, 1, "6290000000"],
    )


def test_f008_r26_analiticas_de_gasto_con_su_hoja() -> None:
    assert S.leer_analiticas_gasto(1, ["GG.GEN"]) == (
        "SELECT c.ide, c.cod, CASE WHEN EXISTS (SELECT 1 FROM dbo.caa h WHERE h.padide = c.ide) "
        "THEN 0 ELSE 1 END FROM dbo.con c JOIN dbo.caa a ON a.ide = c.ide "
        "WHERE c.tip = ? AND c.emp = ? AND c.cod IN (?)",
        [19, 1, "GG.GEN"],
    )


def test_f008_r43_referencia() -> None:
    assert S.buscar_referencia("FAC-1") == (
        "SELECT c.ide, c.cod, d.entide, d.entref, d.totbas, d.totiva, d.totdoc, d.tot, c.est "
        "FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?",
        [15, "FAC-1"],
    )


def test_f008_r43_duplicadas_fuera_de_rech() -> None:
    assert S.buscar_duplicadas("B00000000", "F-77", 15) == (
        "SELECT c.ide, c.cod FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide "
        "WHERE c.tip = ? AND d.entcif = ? AND d.entref = ? AND c.est <> ?",
        [15, "B00000000", "F-77", 15],
    )


def test_f008_listas_vacias_no_son_sql() -> None:
    with pytest.raises(ValueError, match="vacia"):
        S.leer_origenes([])


def test_f008_r37_applocks_en_su_orden_fijo() -> None:
    assert APPLOCKS_FACTURA == (
        "SIGRID_REFEXT_15", "SIGRID_SERIE_15", "SIGRID_IDE_con", "SIGRID_IDE_dcfpro",
        "SIGRID_IDE_dcaprodes", "SIGRID_IDE_dcfrec", "SIGRID_IDE_pag", "SIGRID_IDE_consii",
        "SIGRID_IDE_log",
    )


def test_f008_la_base_se_recorta_y_se_validan_las_constantes() -> None:
    assert FacturaStatements(database=" ruesma ").database == "ruesma"


# --------------------------------------------------------------------------- #
# T10 · reserva de `cod` por serie
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("serie,fecha,esperado", [
    ("FR", 20261030, ("FR26/", 5)), ("FRGG", 20261030, ("FRGG26/", 4)), ("FR", 20270102, ("FR27/", 5)),
])
def test_f008_r9_prefijo_y_cifras_por_serie(serie: str, fecha: int, esperado: tuple[str, int]) -> None:
    assert prefijo_y_cifras(serie, fecha) == esperado


def test_f008_r9_serie_desconocida() -> None:
    with pytest.raises(ValueError, match="serie"):
        prefijo_y_cifras("AB", 20261030)


def test_f008_r37_ultimo_cod_de_la_serie_sin_bloqueo() -> None:
    assert S.ultimo_cod(1, "FR26/", 5) == (
        "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con "
        "WHERE emp = ? AND tip = ? AND cod LIKE ? AND LEN(cod) = ?",
        [6, 1, 15, "FR26/%", 10],
    )


def test_f008_r37_reserva_del_cod_bajo_bloqueo_por_serie() -> None:
    assert S.reservar_cod(1, "FRGG26/", 4) == (
        "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) "
        "WHERE emp = ? AND tip = ? AND cod LIKE ? AND LEN(cod) = ?",
        [8, 1, 15, "FRGG26/%", 11],
    )


def test_f008_r9_un_prefijo_no_casa_el_de_la_otra_serie() -> None:
    """`FR26/%` no casa `FRGG26/0001` y el `LEN` descarta cualquier otro ancho."""
    def casa(patron: str, largo: int, cod: str) -> bool:
        return cod.startswith(patron[:-1]) and len(cod) == largo

    _sql, (_p, _e, _t, fr, largo_fr) = S.reservar_cod(1, "FR26/", 5)
    _sql, (_p, _e, _t, gg, largo_gg) = S.reservar_cod(1, "FRGG26/", 4)
    assert not casa(fr, largo_fr, "FRGG26/0001") and casa(fr, largo_fr, "FR26/00001")
    assert not casa(gg, largo_gg, "FR26/00001") and casa(gg, largo_gg, "FRGG26/0001")
    assert not casa(fr, largo_fr, "FR26/1")


@pytest.mark.parametrize("metodo,tabla", [
    ("reservar_ide_con", "con"), ("reservar_ide_dcfpro", "dcfpro"), ("reservar_ide_dcfrec", "dcfrec"),
    ("reservar_ide_consii", "consii"), ("reservar_ide_dcaprodes", "dcaprodes"),
    ("reservar_ide_log", "log"),
])
def test_f008_r37_reservas_de_ide(metodo: str, tabla: str) -> None:
    assert getattr(S, metodo)() == (
        f"SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.{tabla} WITH (UPDLOCK, HOLDLOCK)", []
    )


# --------------------------------------------------------------------------- #
# T12-T14 · INSERTs por lista blanca, marcas condicionadas y relecturas
# --------------------------------------------------------------------------- #

from application.use_cases.factura_lineas import DCFPRO_COLUMNAS


@pytest.mark.parametrize("metodo,tabla,columnas", [
    ("insertar_con", "con", CON_COLUMNAS), ("insertar_dcf", "dcf", DCA_COLUMNAS),
    ("insertar_dcfpro", "dcfpro", DCFPRO_COLUMNAS), ("insertar_dcfrec", "dcfrec", DCAREC_COLUMNAS),
    ("insertar_pag", "pag", PAG_COLUMNAS), ("insertar_consii", "consii", CONSII_COLUMNAS),
    ("insertar_dcaprodes", "dcaprodes", DCAPRODES_COLUMNAS), ("insertar_log", "log", LOG_COLUMNAS),
])
def test_f008_r38_insert_por_lista_blanca(metodo: str, tabla: str, columnas: tuple[str, ...]) -> None:
    fila = {c: i for i, c in enumerate(columnas)}
    sql, params = getattr(S, metodo)(fila)
    assert sql == (
        f"INSERT INTO dbo.{tabla} ({', '.join(columnas)}) VALUES ({', '.join(['?'] * len(columnas))})"
    )
    assert params == list(range(len(columnas)))


@pytest.mark.parametrize("metodo", ["insertar_con", "insertar_dcfpro", "insertar_pag"])
def test_f008_r38_una_fila_que_no_es_la_lista_blanca_no_se_inserta(metodo: str) -> None:
    columnas = {"insertar_con": CON_COLUMNAS, "insertar_dcfpro": DCFPRO_COLUMNAS,
                "insertar_pag": PAG_COLUMNAS}[metodo]
    fila = dict.fromkeys(columnas, 0)
    with pytest.raises(ValueError, match="columnas"):
        getattr(S, metodo)({**fila, "remide2": 1})
    fila.pop(columnas[-1])
    with pytest.raises(ValueError, match="columnas"):
        getattr(S, metodo)(fila)


def test_f008_r40_marca_de_linea_condicionada_a_canfac_cero() -> None:
    assert S.marcar_linea(8001, 2.5) == (
        "UPDATE dbo.dcapro SET canfac = canfac + ? WHERE ide = ? AND canfac = ?", [2.5, 8001, 0]
    )
    assert S.releer_linea_marcada(8001, 2.5) == (
        "SELECT COUNT(*) FROM dbo.dcapro WHERE ide = ? AND canfac = ?", [8001, 2.5]
    )


def test_f008_r41_marca_de_cabecera_sin_idefac() -> None:
    sql, params = S.marcar_cabecera(800, 20261030, 100000)
    assert sql == (
        "UPDATE dbo.dca SET estfac = ?, fecfac = ?, horfac = ?, antestfac = ? WHERE ide = ? AND estfac = ?"
    )
    assert params == [1, 20261030, 100000, 3, 800, 0]
    assert "idefac" not in sql
    assert S.releer_cabecera_marcada(800, 20261030, 100000) == (
        "SELECT COUNT(*) FROM dbo.dca WHERE ide = ? AND estfac = ? AND fecfac = ? AND horfac = ? "
        "AND antestfac = ?",
        [800, 1, 20261030, 100000, 3],
    )


def test_f008_r41_de_con_a_fac() -> None:
    assert S.marcar_estado(800, est_con=3, est_fac=10) == (
        "UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = ? AND est = ?", [10, 800, 14, 3]
    )
    assert S.releer_estado(800, est_fac=10) == (
        "SELECT COUNT(*) FROM dbo.con WHERE ide = ? AND tip = ? AND est = ?", [800, 14, 10]
    )


def test_f008_r42_contrato() -> None:
    assert S.bloquear_lineas_de_contrato([9901, 9902]) == (
        "SELECT ide, canfac FROM dbo.ctrpro WITH (UPDLOCK, HOLDLOCK) WHERE ide IN (?, ?)", [9901, 9902]
    )
    assert S.sumar_facturado_contrato(9901, 3.0) == (
        "UPDATE dbo.ctrpro SET canfac = canfac + ? WHERE ide = ?", [3.0, 9901]
    )
    assert S.releer_linea_de_contrato(9901, 10.0) == (
        "SELECT COUNT(*) FROM dbo.ctrpro WHERE ide = ? AND ABS(canfac - ?) < ?", [9901, 10.0, 0.0005]
    )
    assert S.actualizar_estfac_contrato(900, 1) == ("UPDATE dbo.ctr SET estfac = ? WHERE ide = ?", [1, 900])
    assert S.releer_estfac_contrato(900, 1) == (
        "SELECT COUNT(*) FROM dbo.ctr WHERE ide = ? AND estfac = ?", [900, 1]
    )


def test_f008_r45_relecturas_por_clave() -> None:
    assert S.releer_con(1, "FR26/00042") == (
        "SELECT COUNT(*) FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?", [1, 15, "FR26/00042"]
    )
    assert S.releer_dcf(10000, "FAC-1") == (
        "SELECT COUNT(*) FROM dbo.dcf WHERE ide = ? AND synckey = ?", [10000, "FAC-1"]
    )
    assert S.releer_dcfpro(10000) == ("SELECT COUNT(*) FROM dbo.dcfpro WHERE docide = ?", [10000])
    assert S.releer_dcfrec(10000) == ("SELECT COUNT(*) FROM dbo.dcfrec WHERE docide = ?", [10000])
    assert S.releer_pagos(10000) == (
        "SELECT COUNT(*) FROM dbo.pag p JOIN dbo.con c ON c.ide = p.ide WHERE p.conide = ? AND c.tip = ?",
        [10000, 25],
    )
    assert S.releer_consii(10000) == ("SELECT COUNT(*) FROM dbo.consii WHERE conide = ?", [10000])
    assert S.releer_dcaprodes(10000) == (
        "SELECT COUNT(*) FROM dbo.dcaprodes WHERE docdeside = ? AND docdestip = ?", [10000, 15]
    )
    assert S.releer_log(600) == ("SELECT COUNT(*) FROM dbo.log WHERE ide = ?", [600])
