# tests/test_f015_statements.py
"""
F-015 · el constructor PURO del modo extendido de `sigrid/albaran` tras la
lista blanca de cabecera (O1) y la retención del contrato (O2):
`application/use_cases/albaran_compra_statements.py`.

Sin red y sin base de datos. El SQL se compara carácter a carácter, como en
`test_f009_statements.py`. Las columnas y sus orígenes salen de
`specs/F-015-albaran-plantilla-y-retencion/design.md` §Lista blanca; las
sentencias, de §Sentencias.
"""
from __future__ import annotations

import pytest

import application.use_cases.albaran_compra_statements as modulo

#: design §Lista blanca, `DCA_COLUMNAS` copiada del texto de la spec (M17).
_DCA_DE_LA_SPEC = (
    "ide, cla, entide, entcod, entres, entref, entcif, ivareq, facper, fecdoc, fecpag, hor, eioide, "
    "eiotex, eitide, eittra, pagide, pagtex, pagfor, efeide, cueide, impbru, impnet, impdes, imprec, "
    "totbas, totiva, totdoc, tot, totpag, cenide, caaide, almide, ivaide, tex, bul, pes, volum, empide, "
    "ageide, ageimp, obride, ctride, fecent, feclim, fecrec, diremp1, dircon1, dirdir1, diremp2, "
    "dircon2, dirdir2, diremp3, dircon3, dirdir3, estser, estfac, antestser, antestfac, ivadif, "
    "docoritip, docoriide, comide, pasdeside, pasori, divcod, divcam, emppreide, empconide, docrelide, "
    "cocide, paclis, tipsininv, prmide, estped, antestped, empcif, cveide, alqide, alqfec, pexide, "
    "divcamfec, ctdide, totbasdiv, totivadiv, totdocdiv, totdiv, totpagdiv, cypnatide, refarc, emptex, "
    "horlim, pdpide, ano, mes, texent, refcom, emnet, eg3w, dtumID, cptide, eleenvio, tipisp, delide, "
    "banide, banban, bansuc, bandig, bancue, ban, bantipide, entciftip, entcifpai, aoside, PFID, "
    "cadcod1, caddir1, cadcod2, caddir2, cadcod3, caddir3, cadcod4, caddir4, cpapai, cpaban, cpasuc, "
    "cpaswi, cpatip, cpadiv, cpacue1, cpacue2, ppoide, fecfac, horfac, idefac, clabieser, facoriide, "
    "duaide, numregcon, fas, periodo, tipctr, tipgar, impavr, synckey"
).split(", ")

_TEXTO_DE_LA_SPEC = (
    "entcod, entres, entref, entcif, eiotex, eittra, pagtex, pagfor, tex, diremp1, diremp2, diremp3, "
    "dircon1, dircon2, dircon3, dirdir1, dirdir2, dirdir3, divcod, paclis, empcif, refarc, emptex, "
    "texent, refcom, dtumID, eleenvio, bandig, bancue, ban, entciftip, entcifpai, PFID, cadcod1, "
    "cadcod2, cadcod3, cadcod4, cpapai, cpaban, cpasuc, cpaswi, cpatip, cpadiv, cpacue1, cpacue2, "
    "numregcon, periodo, synckey"
).split(", ")


# =====================================================================================
# T2 · R1: las columnas de `dca` y el origen de cada una
# =====================================================================================


def test_f015_r1_dca_columnas_son_las_145_del_esquema_vivo_en_su_orden() -> None:
    assert modulo.DCA_COLUMNAS == tuple(_DCA_DE_LA_SPEC)
    assert len(modulo.DCA_COLUMNAS) == 145
    assert len(set(modulo.DCA_COLUMNAS)) == 145


def test_f015_r1_columnas_de_texto_de_dca() -> None:
    assert modulo._DCA_TEXTO == frozenset(_TEXTO_DE_LA_SPEC)
    assert len(modulo._DCA_TEXTO) == 48
    assert modulo._DCA_TEXTO <= set(modulo.DCA_COLUMNAS)


def test_f015_r1_origen_dca_cubre_las_145_sin_huecos_ni_repetidas() -> None:
    """R1, R25: cada columna, un único origen; `ORIGEN_DCA` se deriva de los grupos."""
    grupos = (modulo.DCA_IDENTIDAD, modulo.DCA_CASCADA, modulo.DCA_CALCULADAS, modulo.DCA_FIJAS)
    nombres = [columna for grupo in grupos for columna in grupo]
    assert len(nombres) == len(set(nombres)) == 145
    assert set(nombres) == set(modulo.DCA_COLUMNAS)
    assert tuple(modulo.ORIGEN_DCA) == modulo.DCA_COLUMNAS
    assert [len(g) for g in grupos] == [6, 15, 18, 106]
    cuenta: dict[str, int] = {}
    for origen in modulo.ORIGEN_DCA.values():
        cuenta[origen] = cuenta.get(origen, 0) + 1
    assert cuenta == {"identidad": 6, "cascada": 15, "calculada": 18, "fija": 106}


def test_f015_r1_identidad_y_su_nombre_en_el_proveedor() -> None:
    """R4: con contrato o respaldo, el mismo nombre; del `prv`, estos (M20, M27)."""
    assert modulo.DCA_IDENTIDAD == {
        "entide": "ide", "entcod": "cod", "entres": "raz", "entcif": "cif",
        "entciftip": "tipcif", "entcifpai": "cifpai",
    }


def test_f015_r1_cascada_grupos_y_nombres_en_el_proveedor() -> None:
    """R3: pago y banco en grupo; `dirdir1` es `prv.dir`; `dircon1` e `ivadif` sin
    columna en el `prv` (D5); `pagtex`/`pagfor` del `auxpag` del `prv`."""
    assert modulo.GRUPO_PAGO == ("pagide", "pagtex", "pagfor", "efeide")
    assert modulo.GRUPO_BANCO == ("banban", "bansuc", "bandig", "bancue", "ban", "bantipide")
    assert modulo.DCA_CASCADA == {
        "pagide": "pagide", "pagtex": None, "pagfor": None, "efeide": "efeide",
        "banban": "banban", "bansuc": "bansuc", "bandig": "bandig", "bancue": "bancue",
        "ban": "ban", "bantipide": "bantipide",
        "cueide": "cueide", "eioide": "eioide", "dirdir1": "dir", "dircon1": None, "ivadif": None,
    }
    assert modulo.PAGO_DEL_AUXPAG == {"pagtex": "res", "pagfor": "formul"}


def test_f015_r1_calculadas_de_la_peticion_la_obra_o_un_calculo() -> None:
    """R8 y R13: las 18 que no salen de ninguna fila leída."""
    assert set(modulo.DCA_CALCULADAS) == {
        "ide", "entref", "fecdoc", "hor", "obride", "ctride", "almide", "cenide", "empide",
        "synckey", "impbru", "impnet", "totbas", "totiva", "totdoc", "tot", "totpag", "diremp1",
    }


def test_f015_r9_fijas_valor_del_alta_a_mano() -> None:
    """R9 (M18, D7): `tipgar` −1, `emptex` NULL, las de texto `''` y el resto 0."""
    fijas = modulo.DCA_FIJAS
    assert fijas["tipgar"] == -1
    assert fijas["emptex"] is None
    for columna, valor in fijas.items():
        if columna in ("tipgar", "emptex"):
            continue
        assert valor == ("" if columna in modulo._DCA_TEXTO else 0), columna
        assert type(valor) is (str if columna in modulo._DCA_TEXTO else int), columna
    # Las que R9 nombra, todas fijas.
    for columna in (
        "cla", "fecfac", "horfac", "idefac", "antestfac", "estfac", "docoritip", "docoriide",
        "pasdeside", "pasori", "docrelide", "fecpag", "totbasdiv", "totivadiv", "totdocdiv",
        "totdiv", "totpagdiv", "fecent", "feclim", "cocide", "dtumID", "estser", "impdes", "imprec",
        "banide", "cpacue1",
    ):
        assert columna in fijas, columna


# =====================================================================================
# T3 · R6 y R7: el respaldo (L5) y el proveedor por CIF (L17)
# =====================================================================================


@pytest.fixture
def sentencias() -> modulo.AlbaranCompraStatements:
    return modulo.AlbaranCompraStatements(database="ruesma")


def test_f015_r6_sql_l5_respaldo_por_entide_sin_proformas(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    """R6 (M1, M25): serie `AC__/`, clase 0 y referencia que no empieza por `PROF`."""
    assert sentencias.leer_plantilla_cabecera(1, 77) == (
        "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
        "WHERE c.tip = ? AND c.emp = ? AND d.entide = ? AND c.cod LIKE ? AND d.cla = ? "
        "AND ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC",
        [14, 1, 77, "AC__/%", 0, "PROF%"],
    )


def test_f015_r6_sql_l5_respaldo_por_cif_sin_contrato(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_plantilla_cabecera_por_cif(2, "B12345678") == (
        "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
        "WHERE c.tip = ? AND c.emp = ? AND d.entcif = ? AND c.cod LIKE ? AND d.cla = ? "
        "AND ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC",
        [14, 2, "B12345678", "AC__/%", 0, "PROF%"],
    )


def test_f015_r6_constantes_del_respaldo() -> None:
    assert (modulo.PATRON_SERIE_RESPALDO, modulo.CLA_ALBARAN, modulo.PATRON_PROFORMA) == (
        "AC__/%", 0, "PROF%")


def test_f015_r7_sql_l17_proveedor_por_cif_vivo_en_la_empresa(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    """R7 (M27): `prv` de `con.tip 5`, la empresa de la obra y sin baja."""
    assert modulo.TIP_PROVEEDOR == 5
    assert sentencias.leer_proveedor_por_cif(1, "B12345678") == (
        "SELECT v.ide, c.cod FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide "
        "WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ? AND v.cif = ?",
        [5, 1, 0, "B12345678"],
    )


def test_f015_r6_r7_las_sentencias_nuevas_se_validan_al_construir() -> None:
    todas = modulo.AlbaranCompraStatements.todas_las_sentencias()
    assert modulo.L5_RESPALDO_POR_ENTIDE in todas
    assert modulo.L5_RESPALDO_POR_CIF in todas
    assert modulo.L17_PROVEEDOR_POR_CIF in todas
    assert not hasattr(modulo, "L5_PLANTILLA_POR_ENTIDE")
    assert not hasattr(modulo, "L5_PLANTILLA_POR_CIF")


# =====================================================================================
# T4 · R8: la `con` por lista (las columnas de F-006) y `tiemod` del alta
# =====================================================================================


def test_f015_r8_con_sellos_con_tiemod_ole_utc_del_alta() -> None:
    from datetime import datetime, timezone

    from application.use_cases.parte_reclamacion_statements import fecha_ole_utc

    instante = datetime(2026, 10, 6, 8, 15, 30, tzinfo=timezone.utc)
    sellos = modulo.sellos_del_alta(instante, 20261005)
    assert sellos.tiemod == fecha_ole_utc(instante)
    assert 46301.34 < sellos.tiemod < 46301.35  # 2026-10-06 08:15:30 UTC en días OLE


def test_f015_r8_con_exactamente_las_columnas_de_f006_con_su_valor() -> None:
    from application.use_cases.parte_reclamacion_statements import CON_COLUMNAS

    con = modulo.construir_con(
        emp=2, fec=20261005, entres="PROVEEDOR PRUEBA SL", su_referencia="A-77", tiemod=46301.5
    )
    assert tuple(con) == CON_COLUMNAS
    assert con == {
        "ide": None, "emp": 2, "tip": 14, "subtip": 0, "cod": None,
        "res": "PROVEEDOR PRUEBA SL. (A-77)", "fec": 20261005, "tex": None, "cee": 0, "est": 1,
        "fecbaj": 0, "tiemod": 46301.5, "ico": "", "delo": "", "del": "", "obr": "", "doc": "",
        "serie": 0, "hor": 0,
    }


def test_f015_r8_con_res_recortado_a_128_y_sin_entres() -> None:
    con = modulo.construir_con(emp=1, fec=1, entres=None, su_referencia="X" * 200, tiemod=0.0)
    assert con["res"] == (". (" + "X" * 200 + ")")[:128]
    assert len(con["res"]) == 128
