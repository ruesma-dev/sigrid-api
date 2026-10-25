# tests/test_f007_statements_contrato.py
"""
F-007 T8 · R7-R9, R32: SQL de lectura de `sigrid/proforma` (LP3-LP6, y LP1-LP2,
que se comparan aqui con el resto de constantes) y las funciones puras que
resuelven el contrato: `normalizar_nombre`, `candidatos_de_contrato`,
`contrato_pedido` y `resolver_contrato`.

Datos: las tres hojas de agosto de 2026 de la obra 0719 (M29) en
`tests/fixtures/f007_obra0719.json`, con `cod`, partidas, mediciones, precios e
importes de la medicion, `ide` sinteticos salvo los de `contrato_proformas.md`
y proveedores ficticios. Sin red ni base de datos.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

import application.use_cases.proforma_statements as modulo
from application.use_cases.proforma_statements import (
    LP1_PROFORMAS_DEL_CONTRATO,
    LP2_ANTERIOR_POR_LINEA,
    LP3_CONTRATOS_DE_OBRA,
    LP4_LINEAS_DE_CONTRATOS,
    LP5_REFERENCIA,
    LP6_LINEAS_DE_PROFORMA,
    ContratoCandidato,
    LineaContrato,
    ProformaStatements,
    candidatos_de_contrato,
    contrato_pedido,
    fin_de_periodo,
    normalizar_nombre,
    primer_dia_de_periodo,
    resolver_contrato,
)
from domain.models.proforma_models import (
    ContratoResuelto,
    LineaProformaIn,
    ProformaError,
)

FIXTURE = Path(__file__).parent / "fixtures" / "f007_obra0719.json"
DATOS: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))
BD = "ruesma"
FIN_AGOSTO = 20260831


def contratos() -> list[ContratoCandidato]:
    return [ContratoCandidato(**c) for c in DATOS["contratos"]]


def lineas_de(cod: str) -> list[LineaContrato]:
    return [LineaContrato(**fila) for fila in DATOS["ctrpro"][cod]]


def candidato(cod: str) -> ContratoCandidato:
    return next(c for c in contratos() if c.cod == cod)


def por_contrato(*cods: str) -> dict[int, list[LineaContrato]]:
    return {candidato(cod).ide: lineas_de(cod) for cod in cods}


def hoja(cod: str) -> list[LineaProformaIn]:
    return [LineaProformaIn(**linea) for linea in DATOS["hojas"][cod]["lineas"]]


def codigo_de(exc: pytest.ExceptionInfo[ProformaError]) -> str:
    return exc.value.codigo


# =====================================================================================
# R32 · SQL constante, carácter a carácter, con `?` y validado
# =====================================================================================

S = ProformaStatements(database=BD)


def test_f007_r32_lp1_proformas_registradas_del_contrato() -> None:
    assert LP1_PROFORMAS_DEL_CONTRATO == (
        "SELECT c.ide, c.cod, c.fec, d.entref, d.totbas, d.docoritip FROM dbo.dca d JOIN dbo.con c "
        "ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND (c.cod LIKE ? OR d.entref LIKE ?) "
        "AND ISNULL(d.entref, '') NOT LIKE ?"
    )
    assert S.leer_proformas_del_contrato(2793879) == (
        LP1_PROFORMAS_DEL_CONTRATO, [14, 2793879, "PROF%", "PROF%", "PREV%"]
    )


def test_f007_r32_lp2_cantidad_anterior_por_linea_de_contrato() -> None:
    assert LP2_ANTERIOR_POR_LINEA == (
        "SELECT p.linoriide, SUM(p.can) FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide "
        "JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND p.docoritip = ? "
        "AND c.fec < ? AND (c.cod LIKE ? OR d.entref LIKE ?) AND ISNULL(d.entref, '') NOT LIKE ? "
        "GROUP BY p.linoriide"
    )
    assert S.leer_anterior(2793879, 20260801) == (
        LP2_ANTERIOR_POR_LINEA, [14, 2793879, 44, 20260801, "PROF%", "PROF%", "PREV%"]
    )


def test_f007_r32_lp3_contratos_de_la_obra() -> None:
    assert LP3_CONTRATOS_DE_OBRA == (
        "SELECT t.ide, c.cod, c.fec, t.entcif, t.entres, (SELECT COUNT(*) FROM dbo.ctrpro p "
        "WHERE p.docide = t.ide) AS nlin FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide "
        "WHERE c.tip = ? AND t.obride = ?"
    )
    assert S.leer_contratos_de_obra(7190) == (LP3_CONTRATOS_DE_OBRA, [44, 7190])


def test_f007_r32_lp4_lineas_de_los_contratos_candidatos() -> None:
    assert LP4_LINEAS_DE_CONTRATOS == (
        "SELECT p.ide, p.docide, p.paride, ISNULL(pp.cod, '') AS partida, p.can, p.pre, p.tot, "
        "p.unimed, p.proide, ISNULL(pc.cod, '') AS producto FROM dbo.ctrpro p LEFT JOIN "
        "dbo.obrparpar pp ON pp.ide = p.paride LEFT JOIN dbo.con pc ON pc.ide = p.proide "
        "WHERE p.docide IN {marcadores} ORDER BY p.docide, p.pos, p.ide"
    )
    sql, params = S.leer_lineas_de_contratos([2793879, 2790417])
    assert sql == LP4_LINEAS_DE_CONTRATOS.format(marcadores="(?, ?)")
    assert params == [2793879, 2790417]
    assert S.leer_lineas_de_contratos([2793879]) == (
        LP4_LINEAS_DE_CONTRATOS.format(marcadores="(?)"), [2793879]
    )


def test_f007_r32_lp4_sin_contratos_no_genera_un_in_vacio() -> None:
    with pytest.raises(ValueError):
        S.leer_lineas_de_contratos([])


def test_f007_r32_lp5_referencia_con_clase_y_contrato() -> None:
    assert LP5_REFERENCIA == (
        "SELECT c.ide, c.cod, d.cla, d.ctride FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide "
        "WHERE c.tip = ? AND d.synckey = ?"
    )
    assert S.buscar_referencia("PRF-77") == (LP5_REFERENCIA, [14, "PRF-77"])


def test_f007_r32_lp6_lineas_de_la_proforma_existente() -> None:
    assert LP6_LINEAS_DE_PROFORMA == (
        "SELECT p.ide, p.linoriide, ISNULL(pc.cod, '') AS producto, p.can, p.pre, p.tot "
        "FROM dbo.dcapro p LEFT JOIN dbo.con pc ON pc.ide = p.proide WHERE p.docide = ? "
        "ORDER BY p.pos, p.ide"
    )
    assert S.leer_lineas_de_proforma(2831541) == (LP6_LINEAS_DE_PROFORMA, [2831541])


def test_f007_r32_todas_de_lectura_sin_delete_merge_ni_ddl() -> None:
    sentencias = ProformaStatements.todas_las_sentencias()
    assert len(sentencias) == 6
    prohibidas = re.compile(
        r"\b(DELETE|MERGE|UPDATE|INSERT|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT)\b",
        re.IGNORECASE,
    )
    for sql in sentencias:
        assert sql.startswith("SELECT "), sql
        assert not prohibidas.search(sql), sql
        assert "?" in sql and ";" not in sql and "'%" not in sql


def test_f007_r32_cada_sentencia_pasa_por_el_guardia_de_bases(monkeypatch: pytest.MonkeyPatch) -> None:
    vistas: list[tuple[str, list[str]]] = []

    def validar(sql: str, *, allowed: list[str], contexto: str) -> None:
        vistas.append((sql, list(allowed)))

    monkeypatch.setattr(modulo.DatabaseReferenceGuard, "validate", staticmethod(validar))
    sentencias = ProformaStatements(database=" ruesma ")
    assert [sql for sql, _ in vistas] == list(ProformaStatements.todas_las_sentencias())
    assert {tuple(bases) for _, bases in vistas} == {("ruesma",)}
    vistas.clear()
    sentencias.leer_lineas_de_contratos([1, 2, 3])
    assert vistas == [(LP4_LINEAS_DE_CONTRATOS.format(marcadores="(?, ?, ?)"), ["ruesma"])]


def test_f007_r32_otra_base_dentro_del_sql_no_pasa(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(modulo, "LP5_REFERENCIA", LP5_REFERENCIA.replace("dbo.dca", "otra.dbo.dca"))
    monkeypatch.setattr(
        ProformaStatements, "todas_las_sentencias",
        staticmethod(lambda: (modulo.LP5_REFERENCIA,)),
    )
    with pytest.raises(ValueError):
        ProformaStatements(database=BD)


# =====================================================================================
# Periodo y nombre normalizado
# =====================================================================================


@pytest.mark.parametrize(
    ("periodo", "primero", "ultimo"),
    [(202608, 20260801, 20260831), (202602, 20260201, 20260228), (202402, 20240201, 20240229),
     (202612, 20261201, 20261231), (202604, 20260401, 20260430)],
)
def test_f007_r8_primer_y_ultimo_dia_del_periodo(periodo: int, primero: int, ultimo: int) -> None:
    assert primer_dia_de_periodo(periodo) == primero
    assert fin_de_periodo(periodo) == ultimo


@pytest.mark.parametrize(
    ("uno", "otro"),
    [("NUN S.A.", "NUN, S.A."), ("MODELO DIGITAL", "MODELODIGITAL"), ("nun s.a.", "NUN SA"),
     ("  Ferrallas - del  Centro ", "FERRALLASDELCENTRO")],
)
def test_f007_r8_normalizar_nombre_iguala_signos_espacios_y_mayusculas(uno: str, otro: str) -> None:
    assert normalizar_nombre(uno) == normalizar_nombre(otro)


def test_f007_r8_normalizar_nombre_solo_letras_y_cifras() -> None:
    assert normalizar_nombre("Construcciones Peña, S.L. (2)") == "CONSTRUCCIONESPEÑASL2"
    assert normalizar_nombre(None) == ""
    assert normalizar_nombre(" .,- ") == ""


# =====================================================================================
# R8 · candidatos por obra, fecha y proveedor
# =====================================================================================


def test_f007_r8_candidato_por_nombre_contenido_en_entres() -> None:
    elegidos = candidatos_de_contrato(
        contratos(), fin_periodo=FIN_AGOSTO, cif=None, nombre="Hormigones del Siglo"
    )
    assert [c.cod for c in elegidos] == ["CTSB26/0472"]


def test_f007_r8_candidato_por_cif() -> None:
    elegidos = candidatos_de_contrato(contratos(), fin_periodo=FIN_AGOSTO, cif="B00000417", nombre=None)
    assert [c.cod for c in elegidos] == ["CTSB26/0417"]


def test_f007_r8_el_cif_manda_sobre_el_nombre() -> None:
    elegidos = candidatos_de_contrato(
        contratos(), fin_periodo=FIN_AGOSTO, cif="B00000369", nombre="HORMIGONES DEL SIGLO"
    )
    assert [c.cod for c in elegidos] == ["CTSB26/0369"]
    assert candidatos_de_contrato(
        contratos(), fin_periodo=FIN_AGOSTO, cif="B99999999", nombre="HORMIGONES DEL SIGLO"
    ) == []


def test_f007_r8_contrato_posterior_al_periodo_fuera() -> None:
    # CTSB26/0609 es del 10 de septiembre: no vale para agosto y si para septiembre.
    assert candidatos_de_contrato(contratos(), fin_periodo=FIN_AGOSTO, cif="B00000609", nombre=None) == []
    assert [c.cod for c in candidatos_de_contrato(
        contratos(), fin_periodo=20260930, cif="B00000609", nombre=None
    )] == ["CTSB26/0609"]
    # El mismo dia del fin del periodo, dentro.
    assert [c.cod for c in candidatos_de_contrato(
        contratos(), fin_periodo=20260910, cif="B00000609", nombre=None
    )] == ["CTSB26/0609"]


def test_f007_r8_contrato_sin_lineas_fuera() -> None:
    vacio = ContratoCandidato(ide=1, cod="CTSB26/0001", fec=20260101, entcif="B00000472",
                              entres="HORMIGONES DEL SIGLO SL", nlin=0)
    elegidos = candidatos_de_contrato(
        [vacio, *contratos()], fin_periodo=FIN_AGOSTO, cif="B00000472", nombre=None
    )
    assert [c.cod for c in elegidos] == ["CTSB26/0472"]


def test_f007_r8_nombre_con_signos_distintos_casa() -> None:
    nun = ContratoCandidato(ide=2, cod="CTSB26/0002", fec=20260101, entcif="B00000002",
                            entres="NUN, S.A.", nlin=3)
    modelo = ContratoCandidato(ide=3, cod="CTSB26/0003", fec=20260101, entcif="B00000003",
                               entres="MODELODIGITAL SL", nlin=3)
    assert [c.cod for c in candidatos_de_contrato(
        [nun, modelo], fin_periodo=FIN_AGOSTO, cif=None, nombre="NUN S.A."
    )] == ["CTSB26/0002"]
    assert [c.cod for c in candidatos_de_contrato(
        [nun, modelo], fin_periodo=FIN_AGOSTO, cif=None, nombre="Modelo Digital"
    )] == ["CTSB26/0003"]


def test_f007_r8_nombre_vacio_tras_normalizar_no_casa_con_todos() -> None:
    assert candidatos_de_contrato(contratos(), fin_periodo=FIN_AGOSTO, cif=None, nombre=" - ") == []


def test_f007_r8_cif_comparado_sin_espacios_ni_minusculas() -> None:
    raro = ContratoCandidato(ide=4, cod="CTSB26/0004", fec=20260101, entcif=" b00000004 ",
                             entres="X", nlin=1)
    assert [c.cod for c in candidatos_de_contrato(
        [raro], fin_periodo=FIN_AGOSTO, cif="B00000004", nombre=None
    )] == ["CTSB26/0004"]


def test_f007_r8_candidato_de_fila_lp3() -> None:
    fila = (2793879, "CTSB26/0472  ", 20260615, "B00000472", "HORMIGONES DEL SIGLO SL", 14)
    assert ContratoCandidato.de_fila(fila) == candidato("CTSB26/0472")


def test_f007_r8_linea_de_contrato_de_fila_lp4() -> None:
    fila = (262990, 2793879, 355001, "02.03.02.01", 403.058, 11.0, 4433.638, "M3", 610004, "SM1004")
    linea = LineaContrato.de_fila(fila)
    assert linea == lineas_de("CTSB26/0472")[0]


# =====================================================================================
# R7 · `cod_contrato` manda, sin fecha ni proveedor
# =====================================================================================


def test_f007_r7_cod_contrato_entre_los_de_la_obra() -> None:
    assert contrato_pedido(contratos(), "CTSB26/0417", cif=None) == candidato("CTSB26/0417")


def test_f007_r7_cod_contrato_sin_filtro_de_fecha_ni_de_proveedor() -> None:
    # Posterior al periodo y con un nombre de proveedor que no es el suyo: vale igual.
    assert contrato_pedido(contratos(), "CTSB26/0609", cif=None).ide == 2790609


def test_f007_r7_cod_contrato_comparado_como_el_erp() -> None:
    assert contrato_pedido(contratos(), " ctsb26/0472 ", cif=None).ide == 2793879


def test_f007_r7_cod_contrato_que_no_esta_en_la_obra() -> None:
    with pytest.raises(ProformaError) as exc:
        contrato_pedido(contratos(), "CTSB26/9999", cif=None)
    assert codigo_de(exc) == "contrato_no_encontrado"


def test_f007_r7_cod_contrato_repetido_en_la_obra() -> None:
    doble = [*contratos(), ContratoCandidato(ide=5, cod="CTSB26/0472", fec=20260101,
                                             entcif="B00000472", entres="OTRO", nlin=1)]
    with pytest.raises(ProformaError) as exc:
        contrato_pedido(doble, "CTSB26/0472", cif=None)
    assert codigo_de(exc) == "contrato_ambiguo"


def test_f007_r7_cod_contrato_de_otro_cif() -> None:
    with pytest.raises(ProformaError) as exc:
        contrato_pedido(contratos(), "CTSB26/0472", cif="B00000417")
    assert codigo_de(exc) == "contrato_de_otro_proveedor"
    assert contrato_pedido(contratos(), "CTSB26/0472", cif="B00000472").ide == 2793879


# =====================================================================================
# R8, R9 · resolver entre los candidatos con las líneas de contrato
# =====================================================================================


def test_f007_r8_un_candidato_resuelto_por_proveedor() -> None:
    resuelto = resolver_contrato(
        [candidato("CTSB26/0472")], por_contrato("CTSB26/0472"), hoja("CTSB26/0472")
    )
    assert resuelto == ContratoResuelto(
        cod="CTSB26/0472", ide=2793879, resuelto_por="proveedor", candidatos=["CTSB26/0472"]
    )


@pytest.mark.parametrize("cod", ["CTSB26/0472", "CTSB26/0417", "CTSB26/0369"])
def test_f007_r8_las_tres_hojas_de_la_0719_con_un_candidato(cod: str) -> None:
    hoja_ = DATOS["hojas"][cod]
    elegidos = candidatos_de_contrato(
        contratos(), fin_periodo=fin_de_periodo(hoja_["periodo"]), cif=None,
        nombre=hoja_["nombre_proveedor"],
    )
    resuelto = resolver_contrato(elegidos, por_contrato(cod), hoja(cod))
    assert (resuelto.cod, resuelto.resuelto_por) == (cod, "proveedor")


def _gemelo(ide: int, cod: str, de: str) -> tuple[ContratoCandidato, list[LineaContrato]]:
    """Otro contrato del MISMO proveedor que `de`, con otras lineas."""
    base = candidato(de)
    gemelo = ContratoCandidato(ide=ide, cod=cod, fec=base.fec, entcif=base.entcif,
                               entres=base.entres, nlin=2)
    lineas = [
        LineaContrato(ide=ide * 10 + 1, docide=ide, paride=999001, partida="07.01", can=10.0,
                      pre=5.0, tot=50.0, unimed="UD", proide=610004, producto="SM1004"),
        LineaContrato(ide=ide * 10 + 2, docide=ide, paride=999002, partida="02.03.02.01",
                      can=1.0, pre=11.0, tot=11.0, unimed="M3", proide=610004, producto="SM1004"),
    ]
    return gemelo, lineas


def test_f007_r8_varios_candidatos_las_lineas_con_ctrpro_ide_deshacen() -> None:
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    resuelto = resolver_contrato(
        [candidato("CTSB26/0472"), gemelo],
        {**por_contrato("CTSB26/0472"), gemelo.ide: lineas},
        hoja("CTSB26/0472"),
    )
    assert resuelto == ContratoResuelto(
        cod="CTSB26/0472", ide=2793879, resuelto_por="lineas",
        candidatos=["CTSB26/0472", "CTSB26/0701"],
    )


def test_f007_r8_varios_candidatos_por_partida_y_medicion_sin_ctrpro_ide() -> None:
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    respaldo = [
        LineaProformaIn(referencia_linea="F01", partida="02.03.02.01", medicion_contrato=403.0585,
                        unidad="M3", descripcion="VERTIDO", cantidad=10, precio=11),
        LineaProformaIn(referencia_linea="F02", producto="SM1004", descripcion="EXTRA",
                        cantidad=1, precio=1),
    ]
    resuelto = resolver_contrato(
        [gemelo, candidato("CTSB26/0472")],
        {**por_contrato("CTSB26/0472"), gemelo.ide: lineas},
        respaldo,
    )
    assert (resuelto.cod, resuelto.resuelto_por) == ("CTSB26/0472", "lineas")
    assert resuelto.candidatos == ["CTSB26/0701", "CTSB26/0472"]


def test_f007_r8_medicion_fuera_de_la_tolerancia_no_contiene() -> None:
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    respaldo = [LineaProformaIn(referencia_linea="F01", partida="02.03.02.01",
                                medicion_contrato=403.0595, descripcion="X", cantidad=1, precio=11)]
    with pytest.raises(ProformaError) as exc:
        resolver_contrato(
            [candidato("CTSB26/0472"), gemelo],
            {**por_contrato("CTSB26/0472"), gemelo.ide: lineas},
            respaldo,
        )
    assert codigo_de(exc) == "contrato_no_resuelto"


def test_f007_r9_varios_que_contienen_todas_las_lineas_es_ambiguo() -> None:
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    comun = [LineaProformaIn(referencia_linea="F01", partida="02.03.02.01", medicion_contrato=1,
                             descripcion="X", cantidad=1, precio=11)]
    gemelo2 = ContratoCandidato(ide=7002, cod="CTSB26/0702", fec=gemelo.fec,
                                entcif=gemelo.entcif, entres=gemelo.entres, nlin=2)
    lineas2 = [LineaContrato(ide=70021, docide=7002, paride=1, partida="02.03.02.01", can=1.0,
                             pre=11.0, tot=11.0, unimed="M3", proide=1, producto="SM1004")]
    with pytest.raises(ProformaError) as exc:
        resolver_contrato([gemelo, gemelo2], {gemelo.ide: lineas, gemelo2.ide: lineas2}, comun)
    assert codigo_de(exc) == "contrato_ambiguo"
    assert "CTSB26/0701" in str(exc.value) and "CTSB26/0702" in str(exc.value)


def test_f007_r9_varios_candidatos_y_ninguna_linea_de_contrato_es_ambiguo() -> None:
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    nuevas = [LineaProformaIn(referencia_linea="F01", producto="SM1004", descripcion="X",
                              cantidad=1, precio=1)]
    with pytest.raises(ProformaError) as exc:
        resolver_contrato(
            [candidato("CTSB26/0472"), gemelo],
            {**por_contrato("CTSB26/0472"), gemelo.ide: lineas},
            nuevas,
        )
    assert codigo_de(exc) == "contrato_ambiguo"
    assert "CTSB26/0472" in str(exc.value) and "CTSB26/0701" in str(exc.value)


def test_f007_r9_sin_candidatos_contrato_no_resuelto() -> None:
    with pytest.raises(ProformaError) as exc:
        resolver_contrato([], {}, hoja("CTSB26/0472"))
    assert codigo_de(exc) == "contrato_no_resuelto"


def test_f007_r9_hoja_de_dos_contratos_con_su_reparto() -> None:
    """D5: las lineas de la hoja estan cada una en UN candidato y ninguno las
    tiene todas: `hoja_de_varios_contratos` con referencia de linea -> `cod`."""
    mezcla = hoja("CTSB26/0472")[:2] + hoja("CTSB26/0369")
    with pytest.raises(ProformaError) as exc:
        resolver_contrato(
            [candidato("CTSB26/0472"), candidato("CTSB26/0369")],
            por_contrato("CTSB26/0472", "CTSB26/0369"),
            mezcla,
        )
    assert codigo_de(exc) == "hoja_de_varios_contratos"
    assert exc.value.reparto == {
        "F09": "CTSB26/0472", "F11": "CTSB26/0472", "N10": "CTSB26/0369", "N11": "CTSB26/0369",
    }


def test_f007_r9_reparto_solo_de_lineas_de_contrato() -> None:
    # F23 (BERENJENO, nueva) no entra en el reparto ni lo impide.
    mezcla = hoja("CTSB26/0472") + hoja("CTSB26/0369")[:1]
    with pytest.raises(ProformaError) as exc:
        resolver_contrato(
            [candidato("CTSB26/0472"), candidato("CTSB26/0369")],
            por_contrato("CTSB26/0472", "CTSB26/0369"),
            mezcla,
        )
    assert codigo_de(exc) == "hoja_de_varios_contratos"
    assert "F23" not in exc.value.reparto
    assert exc.value.reparto["N10"] == "CTSB26/0369"


def test_f007_r9_una_linea_en_ningun_candidato_no_resuelve() -> None:
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    ajena = hoja("CTSB26/0369")[:1]
    with pytest.raises(ProformaError) as exc:
        resolver_contrato(
            [candidato("CTSB26/0472"), gemelo],
            {**por_contrato("CTSB26/0472"), gemelo.ide: lineas},
            hoja("CTSB26/0472")[:1] + ajena,
        )
    assert codigo_de(exc) == "contrato_no_resuelto"


def test_f007_r9_lineas_que_solapan_sin_contenedor_es_ambiguo() -> None:
    """Una linea en los dos candidatos y otra solo en uno de ellos, y una
    tercera solo en el otro: nadie las tiene todas ni hay reparto limpio."""
    gemelo, lineas = _gemelo(7001, "CTSB26/0701", "CTSB26/0472")
    en_los_dos = LineaProformaIn(referencia_linea="A", partida="02.03.02.01", medicion_contrato=1,
                                 descripcion="X", cantidad=1, precio=11)
    lineas_0472 = [*por_contrato("CTSB26/0472")[2793879],
                   LineaContrato(ide=1, docide=2793879, paride=1, partida="02.03.02.01", can=1.0,
                                 pre=11.0, tot=11.0, unimed="M3", proide=1, producto="SM1004")]
    with pytest.raises(ProformaError) as exc:
        resolver_contrato(
            [candidato("CTSB26/0472"), gemelo],
            {2793879: lineas_0472, gemelo.ide: lineas},
            [en_los_dos, hoja("CTSB26/0472")[0],
             LineaProformaIn(referencia_linea="B", ctrpro_ide=gemelo.ide * 10 + 1,
                             descripcion="X", cantidad=1, precio=5)],
        )
    assert codigo_de(exc) == "contrato_ambiguo"
