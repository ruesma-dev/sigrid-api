# tests/test_f016_statements.py
"""
F-016 T6 · R5-R13, R19, R22: el SQL nuevo (LP7-LP9) y las funciones puras de
la proforma a origen (`application/use_cases/proforma_origen_statements.py`).

Datos: la cadena sintetica de `tests/fixtures/f016_cadena.json` (forma de M44)
sobre el contrato CTSB26/0472 de la obra 0719 de F-007. Sin red ni base.
"""
from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from f016_dobles import (
    CTR_0472,
    DE_MES,
    DOCUMENTOS,
    IDE_PUNTA,
    PARALELA,
    PRIMERA,
    PUNTA,
    fila_lp1,
    fila_lp7,
    lineas_de,
)

import application.use_cases.proforma_origen_statements as modulo
from application.use_cases.albaran_compra_statements import POS_PASO
from application.use_cases.proforma_origen_statements import (
    DOCORITIP_A_ORIGEN,
    LP7_PROFORMA_ANTERIOR,
    LP8_SUCESORAS,
    LP9_LINEAS_ANTERIOR,
    CadenaValidada,
    DocumentoCadena,
    ProformaOrigenStatements,
    avisos_de_nuevas,
    buscar_del_mes_origen,
    cabecera_a_origen,
    comprobar_sucesoras,
    filas_arrastradas,
    importe_de_cadena,
    superponer_cadena,
    validar_anterior,
    validar_continuadas,
)
from application.use_cases.proforma_statements import LineaContrato, ProformaRegistrada
from domain.models.proforma_models import LineaProformaIn, ProformaError
from domain.models.proforma_origen_models import (
    AvisoProformaOrigen,
    FalloLineaProformaOrigen,
    ProformaOrigenError,
)

F007 = json.loads((Path(__file__).parent / "fixtures" / "f007_obra0719.json").read_text(
    encoding="utf-8"))
CTRPRO = {l["ide"]: LineaContrato(**l) for l in F007["ctrpro"]["CTSB26/0472"]}
FIN_AGOSTO = 20260831
BD = "ruesma"
S = ProformaOrigenStatements(database=BD)


def de_contrato(ref: str, ctrpro: int, **extra: Any) -> LineaProformaIn:
    return LineaProformaIn(referencia_linea=ref, ctrpro_ide=ctrpro, descripcion="D",
                           cantidad=extra.pop("cantidad", 1.0), precio=11.0, **extra)


def sin_vincular(ref: str, **extra: Any) -> LineaProformaIn:
    return LineaProformaIn(referencia_linea=ref, producto="SM1004", partida="02.20.02.02.11",
                           descripcion="D", cantidad=extra.pop("cantidad", 1.0), precio=3.5,
                           **extra)


# =====================================================================================
# R22 · SQL constante, caracter a caracter, de lectura y validado
# =====================================================================================


def test_f016_r22_lp7_la_anterior_por_su_cod_en_el_contrato() -> None:
    assert LP7_PROFORMA_ANTERIOR == (
        "SELECT c.ide, c.cod, c.fec, d.docoritip FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide "
        "WHERE c.tip = ? AND d.ctride = ? AND c.cod = ?"
    )
    assert S.leer_proforma_anterior(CTR_0472, PUNTA) == (
        LP7_PROFORMA_ANTERIOR, [14, CTR_0472, PUNTA])


def test_f016_r22_lp8_las_sucesoras_de_la_anterior_en_el_contrato() -> None:
    assert LP8_SUCESORAS == (
        "SELECT c.ide, c.cod FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? "
        "AND d.ctride = ? AND d.docoriide = ?"
    )
    assert S.leer_sucesoras(CTR_0472, IDE_PUNTA) == (LP8_SUCESORAS, [14, CTR_0472, IDE_PUNTA])


def test_f016_r22_lp9_las_lineas_completas_de_la_anterior() -> None:
    assert LP9_LINEAS_ANTERIOR == "SELECT * FROM dbo.dcapro WHERE docide = ? ORDER BY pos, ide"
    assert S.leer_lineas_anterior(IDE_PUNTA) == (LP9_LINEAS_ANTERIOR, [IDE_PUNTA])


def test_f016_r22_todas_de_lectura_sin_delete_merge_ddl_ni_update() -> None:
    sentencias = ProformaOrigenStatements.todas_las_sentencias()
    assert sentencias == (LP7_PROFORMA_ANTERIOR, LP8_SUCESORAS, LP9_LINEAS_ANTERIOR)
    prohibidas = re.compile(
        r"\b(DELETE|MERGE|UPDATE|INSERT|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT)\b",
        re.IGNORECASE,
    )
    for sql in sentencias:
        assert sql.startswith("SELECT "), sql
        assert not prohibidas.search(sql), sql
        assert "?" in sql and ";" not in sql and "'" not in sql


def test_f016_r22_cada_sentencia_pasa_por_el_guardia_de_bases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    vistas: list[tuple[str, list[str], str]] = []

    def validar(sql: str, *, allowed: list[str], contexto: str) -> None:
        vistas.append((sql, list(allowed), contexto))

    monkeypatch.setattr(modulo.DatabaseReferenceGuard, "validate", staticmethod(validar))
    ProformaOrigenStatements(database=" ruesma ")
    assert vistas == [(sql, ["ruesma"], "lectura")
                      for sql in ProformaOrigenStatements.todas_las_sentencias()]


def test_f016_r22_otra_base_dentro_del_sql_no_pasa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        ProformaOrigenStatements, "todas_las_sentencias",
        staticmethod(lambda: (LP8_SUCESORAS.replace("dbo.dca", "otra.dbo.dca"),)),
    )
    with pytest.raises(ValueError):
        ProformaOrigenStatements(database=BD)


# =====================================================================================
# R6 · validar la anterior (LP7)
# =====================================================================================


def test_f016_r6_anterior_valida() -> None:
    anterior = validar_anterior([fila_lp7(PUNTA)], cod=PUNTA, fecha=FIN_AGOSTO)
    assert anterior == DocumentoCadena(ide=IDE_PUNTA, cod=PUNTA, fec=20260731, docoritip=1)
    assert DOCORITIP_A_ORIGEN == 1


def test_f016_r6_anterior_del_mismo_dia_vale_y_del_siguiente_no() -> None:
    assert validar_anterior([fila_lp7(PUNTA, fec=FIN_AGOSTO)], cod=PUNTA, fecha=FIN_AGOSTO).fec == (
        FIN_AGOSTO)
    with pytest.raises(ProformaOrigenError) as excinfo:
        validar_anterior([fila_lp7(PUNTA, fec=20260901)], cod=PUNTA, fecha=FIN_AGOSTO)
    assert excinfo.value.codigo == "anterior_no_valida"
    assert "20260901" in str(excinfo.value) and str(FIN_AGOSTO) in str(excinfo.value)


@pytest.mark.parametrize(
    ("filas", "en_el_mensaje"),
    [([], "0 proformas"), ([fila_lp7(PUNTA), fila_lp7(PARALELA, cod=PUNTA)], "2 proformas"),
     ([fila_lp7(DE_MES)], "no es a origen"), ([fila_lp7(PUNTA, docoritip=None)], "no es a origen")],
    ids=["ninguna", "dos", "de_mes", "docoritip_nulo"],
)
def test_f016_r6_anterior_no_valida(filas: list[tuple[Any, ...]], en_el_mensaje: str) -> None:
    with pytest.raises(ProformaOrigenError) as excinfo:
        validar_anterior(filas, cod=PUNTA, fecha=FIN_AGOSTO)
    assert excinfo.value.codigo == "anterior_no_valida"
    assert en_el_mensaje in str(excinfo.value) and PUNTA in str(excinfo.value)


def test_f016_r6_fila_lp7_con_nulos() -> None:
    assert DocumentoCadena.de_fila((7, " PROF26/00007 ", None, None)) == DocumentoCadena(
        ide=7, cod="PROF26/00007", fec=0, docoritip=0)


# =====================================================================================
# R7 · la anterior no tiene sucesora (LP8)
# =====================================================================================


def test_f016_r7_sin_sucesoras_sigue() -> None:
    assert comprobar_sucesoras([]) is None


def test_f016_r7_con_sucesora_nombra_su_cod() -> None:
    with pytest.raises(ProformaOrigenError) as excinfo:
        comprobar_sucesoras([(2850999, " PROF26/00999 "), (2851000, "AC26/1")])
    assert excinfo.value.codigo == "anterior_con_sucesora"
    assert "PROF26/00999, AC26/1" in str(excinfo.value)


# =====================================================================================
# R9 · las continuaciones (LP9)
# =====================================================================================


def test_f016_r9_continuadas_de_la_anterior_y_del_mismo_tipo() -> None:
    lineas = [de_contrato("F09", 262990, linea_anterior=1400001), sin_vincular("F23",
              linea_anterior=1400003), de_contrato("F11", 262992)]
    identificadas = {0: CTRPRO[262990], 2: CTRPRO[262992]}
    filas = lineas_de(PUNTA)
    continuadas, fallos = validar_continuadas(lineas, identificadas, filas)
    assert fallos == []
    assert continuadas == {0: filas[0], 1: filas[2]}


def test_f016_r9_sin_linea_anterior_es_nueva_aunque_su_ctrpro_sea_unico() -> None:
    """D3: la API no casa por su cuenta, ni con un `ctrpro` unico en la anterior (262994)."""
    lineas = [de_contrato("F13", 262994)]
    continuadas, fallos = validar_continuadas(lineas, {0: CTRPRO[262994]}, lineas_de(PUNTA))
    assert (continuadas, fallos) == ({}, [])


@pytest.mark.parametrize(
    ("linea", "identificadas", "en_el_mensaje"),
    [
        (de_contrato("F09", 262990, linea_anterior=1400002), {0: CTRPRO[262990]}, "262994"),
        (de_contrato("F09", 262990, linea_anterior=1400003), {0: CTRPRO[262990]}, "sin vincular"),
        (sin_vincular("F23", linea_anterior=1400001), {}, "de contrato"),
        (de_contrato("F09", 262990, linea_anterior=1500001), {0: CTRPRO[262990]}, "no es una linea"),
    ],
    ids=["otro_ctrpro", "contrato_sobre_sin_vincular", "sin_vincular_sobre_contrato",
         "ajena_a_la_anterior"],
)
def test_f016_r9_linea_anterior_no_valida(
    linea: LineaProformaIn, identificadas: dict[int, LineaContrato], en_el_mensaje: str
) -> None:
    continuadas, fallos = validar_continuadas([linea], identificadas, lineas_de(PUNTA))
    assert continuadas == {}
    (fallo,) = fallos
    assert type(fallo) is FalloLineaProformaOrigen
    assert (fallo.indice, fallo.referencia_linea, fallo.codigo) == (
        0, linea.referencia_linea, "linea_anterior_no_valida")
    assert en_el_mensaje in fallo.mensaje and str(linea.linea_anterior) in fallo.mensaje


def test_f016_r9_de_contrato_sin_identificar_solo_se_mira_que_sea_de_la_anterior() -> None:
    """Su fallo ya va en la etapa 1: no se le anade otro por el tipo."""
    lineas = [de_contrato("F09", 999999, linea_anterior=1400003),
              de_contrato("F10", 999999, linea_anterior=1500001)]
    continuadas, fallos = validar_continuadas(lineas, {}, lineas_de(PUNTA))
    assert continuadas == {}
    assert [(f.indice, f.codigo) for f in fallos] == [(1, "linea_anterior_no_valida")]


def test_f016_r9_varios_fallos_juntos_en_su_orden() -> None:
    lineas = [sin_vincular("F23", linea_anterior=1400001), de_contrato("F09", 262990),
              de_contrato("F21", 263002, linea_anterior=1400099)]
    identificadas = {1: CTRPRO[262990], 2: CTRPRO[263002]}
    _continuadas, fallos = validar_continuadas(lineas, identificadas, lineas_de(PUNTA))
    assert [(f.indice, f.referencia_linea) for f in fallos] == [(0, "F23"), (2, "F21")]


def test_f016_r9_linoriide_nulo_es_sin_vincular() -> None:
    filas = [{**lineas_de(PUNTA)[2], "linoriide": None}]
    continuadas, fallos = validar_continuadas(
        [sin_vincular("F23", linea_anterior=1400003)], {}, filas)
    assert (list(continuadas), fallos) == ([0], [])


# =====================================================================================
# R10 · aviso de integridad de las nuevas
# =====================================================================================


def test_f016_r10_nueva_de_contrato_con_su_ctrpro_en_la_anterior() -> None:
    lineas = [de_contrato("F09", 262990), de_contrato("F21", 263002, linea_anterior=1400005),
              sin_vincular("F23"), de_contrato("F11", 262992)]
    identificadas = {0: CTRPRO[262990], 1: CTRPRO[263002], 3: CTRPRO[262992]}
    filas = lineas_de(PUNTA)
    continuadas, _fallos = validar_continuadas(lineas, identificadas, filas)
    avisos = avisos_de_nuevas(lineas, identificadas, filas, continuadas)
    assert list(avisos) == [0]
    aviso = avisos[0]
    assert type(aviso) is AvisoProformaOrigen
    assert (aviso.codigo, aviso.lineas_anterior) == ("linea_nueva_ya_en_la_anterior",
                                                      [1400001, 1400004])
    assert "1400001, 1400004" in aviso.mensaje and "262990" in aviso.mensaje


def test_f016_r10_sin_anterior_no_hay_avisos() -> None:
    lineas = [de_contrato("F09", 262990)]
    assert avisos_de_nuevas(lineas, {0: CTRPRO[262990]}, [], {}) == {}


# =====================================================================================
# R11, R13 · columnas a origen de las lineas de la peticion y de la cabecera
# =====================================================================================


def _fila_construida(linoriide: int, can: float, **extra: Any) -> dict[str, Any]:
    """Una `dcapro` como la deja el nucleo de F-009 (F-007): con la plantilla."""
    return {"ide": None, "docide": None, "pos": 64, "can": can, "pre": 11.0, "linoriide": linoriide,
            "docoritip": 44 if linoriide else 0, "canoriori": 403.058 if linoriide else 0,
            "imporiori": 4433.64 if linoriide else 0, "canorilin": 0, "canoriant": 0,
            "imporiant": 0, "canser": 0, **extra}


def test_f016_r11_continuada_y_nueva_vinculada_y_sin_vincular() -> None:
    filas = lineas_de(PUNTA)
    dcapro = [_fila_construida(262990, 620.0), _fila_construida(262992, 117.5),
              _fila_construida(0, 75.85), _fila_construida(0, 4.0, imporiori=7.0)]
    continuadas = {0: filas[0], 2: filas[2]}
    resultado = superponer_cadena(dcapro, continuadas)
    columnas = ("canorilin", "canoriori", "imporiori", "canoriant", "imporiant")
    assert [tuple(f[c] for c in columnas) for f in resultado] == [
        (1400001, 861.0, 4433.64, 0, 0),   # continuada vinculada: imporiori del ctrpro
        (0, 117.5, 4433.64, 0, 0),         # nueva vinculada: como F-007
        (1400003, 105.85, 0.0, 0, 0),      # continuada sin vincular: imporiori de la anterior
        (0, 4.0, 7.0, 0, 0),               # nueva sin vincular: como F-007
    ]
    assert dcapro[0]["canoriori"] == 403.058, "no toca las filas del nucleo"
    assert [f["can"] for f in resultado] == [620.0, 117.5, 75.85, 4.0]


def test_f016_r11_canoriori_sin_errores_de_coma_flotante_y_con_nulos() -> None:
    anterior = {**lineas_de(PUNTA)[0], "canoriori": 0.1}
    (fila,) = superponer_cadena([_fila_construida(262990, 0.2)], {0: anterior})
    assert fila["canoriori"] == 0.3
    sin_origen = {**lineas_de(PUNTA)[0], "canoriori": None}
    (fila,) = superponer_cadena([_fila_construida(262990, 5.0)], {0: sin_origen})
    assert fila["canoriori"] == 5.0


def test_f016_r11_sin_plantilla_tambien_lleva_las_columnas_a_origen() -> None:
    (fila,) = superponer_cadena([{"ide": None, "pos": 64, "can": 3.0, "linoriide": 0}], {})
    assert {c: fila[c] for c in ("canorilin", "canoriori", "canoriant", "imporiant")} == {
        "canorilin": 0, "canoriori": 3.0, "canoriant": 0, "imporiant": 0}


def test_f016_r13_cabecera_a_origen() -> None:
    dca = {"ide": None, "cla": 141, "docoritip": 0, "docoriide": 0, "totbas": 5.0}
    anterior = DocumentoCadena(ide=IDE_PUNTA, cod=PUNTA, fec=20260731, docoritip=1)
    assert cabecera_a_origen(dca, anterior) == {**dca, "docoritip": 1, "docoriide": IDE_PUNTA}
    assert cabecera_a_origen(dca, None) == {**dca, "docoritip": 1, "docoriide": 0}
    assert dca["docoritip"] == 0


# =====================================================================================
# R12 · las arrastradas
# =====================================================================================


def test_f016_r12_arrastradas_las_no_continuadas_en_su_orden_detras() -> None:
    filas = lineas_de(PUNTA)
    arrastradas = filas_arrastradas(filas, {1400001, 1400003, 1400005}, 7 * POS_PASO)
    assert [f["canorilin"] for f in arrastradas] == [1400002, 1400004]
    assert [f["pos"] for f in arrastradas] == [448, 512]
    original = filas[1]
    fila = arrastradas[0]
    assert (fila["ide"], fila["docide"]) == (None, None)
    assert {c: fila[c] for c in ("can", "tot", "ivacuo", "prepma")} == dict.fromkeys(
        ("can", "tot", "ivacuo", "prepma"), 0.0)
    assert (fila["canoriori"], fila["imporiori"]) == (original["canoriori"], original["imporiori"])
    seguimiento = ("canser", "canfac", "cancan", "canped", "canoriant", "imporiant",
                   "imporiantdiv", "imporioridiv", "canmed")
    assert {c: fila[c] for c in seguimiento} == dict.fromkeys(seguimiento, 0)
    assert fila["med"] is None
    # El resto, copia de la fila de la anterior: producto, precio, partida, textos, vinculo.
    for columna in ("proide", "pre", "tar", "paride", "res", "refent", "ivaide", "linoriide",
                    "docoritip", "docoricod", "docoriide", "almide", "unimed", "fec"):
        assert fila[columna] == original[columna], columna
    assert set(fila) == set(original)
    assert original["can"] == 50.0 and original["canser"] == 1.0, "no toca las filas leidas"


def test_f016_r12_sin_anterior_o_todas_continuadas_no_hay_arrastradas() -> None:
    assert filas_arrastradas([], set(), 64) == []
    filas = lineas_de(PUNTA)
    assert filas_arrastradas(filas, {f["ide"] for f in filas}, 64) == []


def test_f016_r12_las_columnas_que_no_trae_no_se_inventan_salvo_las_de_r12() -> None:
    (fila,) = filas_arrastradas([{"ide": 9, "pos": 64, "can": 2.0, "canoriori": 2.0}], set(), 128)
    assert fila == {"ide": None, "docide": None, "pos": 128, "can": 0.0, "tot": 0.0,
                    "ivacuo": 0.0, "prepma": 0.0, "canoriori": 2.0, "canorilin": 9,
                    "canoriant": 0, "imporiant": 0, "med": None, "canmed": 0}


# =====================================================================================
# R5 · ya registrada a origen
# =====================================================================================


def _registrada(cod: str, **cambios: Any) -> ProformaRegistrada:
    return replace(ProformaRegistrada.de_fila(fila_lp1(cod)), **cambios)


def test_f016_r5_ninguna_del_mes_sigue_sin_avisos() -> None:
    proformas = [_registrada(c) for c in DOCUMENTOS]
    assert buscar_del_mes_origen(proformas, periodo=202608, importe_mes=17024.28,
                                 otra_del_mes=False) == (None, [])


def test_f016_r5_a_origen_del_mes_con_otro_total_avisa_y_sigue() -> None:
    proformas = [_registrada(PUNTA), _registrada(PARALELA, fec=20260731, totbas=99.0)]
    existente, avisos = buscar_del_mes_origen(proformas, periodo=202607, importe_mes=17024.28,
                                              otra_del_mes=False)
    assert existente is None
    (aviso,) = avisos
    assert type(aviso) is AvisoProformaOrigen and aviso.codigo == "otra_del_mes"
    assert f"{PUNTA}, {PARALELA}" in aviso.mensaje


@pytest.mark.parametrize("importe", [2311.0, 2310.95, 2311.05])
def test_f016_r5_a_origen_del_mes_con_el_mismo_total_es_existente(importe: float) -> None:
    proformas = [_registrada(PARALELA, fec=20260731, totbas=99.0), _registrada(PUNTA)]
    existente, avisos = buscar_del_mes_origen(proformas, periodo=202607, importe_mes=importe,
                                              otra_del_mes=False)
    assert (existente, avisos) == (_registrada(PUNTA), [])


def test_f016_r5_fuera_de_la_tolerancia_no_es_la_misma() -> None:
    existente, avisos = buscar_del_mes_origen([_registrada(PUNTA)], periodo=202607,
                                              importe_mes=2311.06, otra_del_mes=False)
    assert existente is None and [a.codigo for a in avisos] == ["otra_del_mes"]


def test_f016_r5_de_mes_con_otro_total_es_el_error_de_f007() -> None:
    proformas = [_registrada(PUNTA, fec=20260615, totbas=1.0), _registrada(DE_MES)]
    with pytest.raises(ProformaError) as excinfo:
        buscar_del_mes_origen(proformas, periodo=202606, importe_mes=17024.28, otra_del_mes=False)
    assert excinfo.value.codigo == "proforma_del_mes_existente"


def test_f016_r5_de_mes_con_el_mismo_total_es_existente() -> None:
    proformas = [_registrada(DE_MES)]
    assert buscar_del_mes_origen(proformas, periodo=202606, importe_mes=300.0,
                                 otra_del_mes=False) == (_registrada(DE_MES), [])


def test_f016_r5_otra_del_mes_como_f007() -> None:
    proformas = [_registrada(DE_MES), _registrada(PRIMERA, fec=20260620)]
    existente, avisos = buscar_del_mes_origen(proformas, periodo=202606, importe_mes=300.0,
                                              otra_del_mes=True)
    assert existente is None and [a.codigo for a in avisos] == ["otra_del_mes"]


# =====================================================================================
# R19 · importe de cadena
# =====================================================================================


def test_f016_r19_importe_de_cadena_de_la_punta_y_de_la_primera() -> None:
    assert importe_de_cadena(lineas_de(PUNTA)) == 3521.0
    assert importe_de_cadena(lineas_de(PRIMERA)) == 1210.0
    assert importe_de_cadena([]) == 0.0


def test_f016_r19_importe_de_cadena_redondea_cada_linea_y_tolera_nulos() -> None:
    filas = [{"canoriori": 105.85, "pre": 3.5}, {"canoriori": 0.005, "pre": 1.0},
             {"canoriori": None, "pre": 7.0}]
    assert importe_de_cadena(filas) == 370.49


def test_f016_r19_cadena_validada_cuenta_las_arrastradas() -> None:
    filas = lineas_de(PUNTA)
    cadena = CadenaValidada(anterior=None, filas=filas, continuadas={0: filas[0]}, avisos={})
    assert cadena.n_arrastradas == 4
