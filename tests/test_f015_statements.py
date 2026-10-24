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

from decimal import Decimal

import pytest

import application.use_cases.albaran_compra_statements as modulo

#: design §Lista blanca, `DCA_COLUMNAS` copiada del texto de la spec (M17).
_DCA_DE_LA_SPEC = (  # noqa: SIM905 (copia literal del texto de la spec)
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

_TEXTO_DE_LA_SPEC = (  # noqa: SIM905
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
        (
            "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
            "WHERE c.tip = ? AND c.emp = ? AND d.entide = ? AND c.cod LIKE ? AND d.cla = ? "
            "AND ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC"
        ),
        [14, 1, 77, "AC__/%", 0, "PROF%"],
    )


def test_f015_r6_sql_l5_respaldo_por_cif_sin_contrato(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_plantilla_cabecera_por_cif(2, "B12345678") == (
        (
            "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
            "WHERE c.tip = ? AND c.emp = ? AND d.entcif = ? AND c.cod LIKE ? AND d.cla = ? "
            "AND ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC"
        ),
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
        (
            "SELECT v.ide, c.cod FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide "
            "WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ? AND v.cif = ?"
        ),
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


# =====================================================================================
# T5 · R2-R5, R8-R10, R25: `construir_dca` por lista
# =====================================================================================

_TOTALES = {"totbas": 100.0, "totiva": 21.0, "totdoc": 121.0}

#: Columnas del `prv` que la lista lee (R3, R4), más otras con nombre de `dca`
#: que la lista NO debe leer nunca del `prv` (R2).
_COLUMNAS_PRV = (
    "ide", "cod", "raz", "cif", "tipcif", "cifpai", "pagide", "efeide", "banban", "bansuc",
    "bandig", "bancue", "ban", "bantipide", "cueide", "eioide", "dir",
    "dircon1", "ivadif", "pagtex", "pagfor", "fecfac", "tipgar", "cla", "entres", "tex",
)
_TEXTO_PRV = {"cod", "raz", "cif", "tipcif", "cifpai", "bandig", "bancue", "ban", "dir",
              "dircon1", "pagtex", "pagfor", "entres", "tex"}


def _centinela(prefijo: str, base: int, columnas: tuple[str, ...], texto: set[str]) -> dict:
    """Una fila en la que cada columna vale algo distinto y reconocible."""
    return {
        c: (f"{prefijo}:{c}" if c in texto else base + i) for i, c in enumerate(columnas)
    }


def _contrato() -> dict:
    return _centinela("C", 100_000, modulo.DCA_COLUMNAS, set(modulo._DCA_TEXTO))


def _respaldo() -> dict:
    return _centinela("R", 200_000, modulo.DCA_COLUMNAS, set(modulo._DCA_TEXTO))


def _proveedor() -> dict:
    return _centinela("P", 300_000, _COLUMNAS_PRV, _TEXTO_PRV)


def _auxpag() -> dict:
    return {"ide": 400_000, "res": "A:res", "formul": "A:formul", "efeide": 400_003}


def _dca(contrato=None, respaldo=None, proveedor=None, pago=None, cuo=Decimal(0)):
    return modulo.construir_dca(
        contrato=contrato, proveedor=proveedor if proveedor is not None else _proveedor(),
        pago_proveedor=pago, respaldo=respaldo, fec=20261005, hor=101530, su_referencia="A-77",
        obride=5000, ctride=300 if contrato is not None else 0, almide=70, cenide=80,
        empide=2425207, totales=_TOTALES, cuo=cuo, referencia_externa="ALB-1",
    )


def _origen_de_cada_columna(fila: dict, **filas: dict) -> dict[str, str]:
    """Para cada columna, qué fila leída trae su valor ('' si ninguna). `diremp1`
    es calculada pero su valor es la `entres` escrita (R8): sale de donde salga
    la identidad, y se comprueba aparte que coincide con `entres`."""
    assert fila["diremp1"] == fila["entres"]
    origen = {}
    for columna, valor in fila.items():
        de = [n for n, f in filas.items() if valor not in (None, "", 0) and valor in f.values()]
        assert len(de) <= 1, (columna, de)
        origen[columna] = de[0] if de else ""
    return origen


def _de_una_fila(columna: str) -> bool:
    return modulo.ORIGEN_DCA[columna] in ("identidad", "cascada") or columna == "diremp1"


def _vaciar(fila: dict, columnas) -> dict:
    return {c: ("" if isinstance(v, str) else 0) if c in columnas else v for c, v in fila.items()}


def test_f015_r25_centinela_con_contrato_todo_del_contrato_salvo_lo_calculado() -> None:
    """R2, R25: con todas las filas llenas, la identidad y la cascada salen del
    contrato y ninguna otra columna lleva un valor leído."""
    contrato, respaldo, proveedor = _contrato(), _respaldo(), _proveedor()
    dca, sin_fuente = _dca(contrato, respaldo, proveedor, _auxpag())
    assert tuple(dca) == modulo.DCA_COLUMNAS
    origen = _origen_de_cada_columna(dca, contrato=contrato, respaldo=respaldo,
                                     proveedor=proveedor, auxpag=_auxpag())
    for columna in modulo.DCA_COLUMNAS:
        esperado = "contrato" if _de_una_fila(columna) else ""
        assert origen[columna] == esperado, columna
    assert sin_fuente == ()


def test_f015_r25_centinela_sin_contrato_con_respaldo_todo_del_respaldo() -> None:
    respaldo, proveedor = _respaldo(), _proveedor()
    dca, sin_fuente = _dca(None, respaldo, proveedor, _auxpag())
    origen = _origen_de_cada_columna(dca, respaldo=respaldo, proveedor=proveedor, auxpag=_auxpag())
    for columna in modulo.DCA_COLUMNAS:
        esperado = "respaldo" if _de_una_fila(columna) else ""
        assert origen[columna] == esperado, columna
    assert dca["ctride"] == 0 and sin_fuente == ()


def test_f015_r25_centinela_sin_contrato_ni_respaldo_del_proveedor() -> None:
    """R3-R5: del `prv`, con sus nombres; `dircon1` e `ivadif` no los tiene (D5):
    quedan sin fuente aunque el `prv` traiga columnas con ese nombre (R2)."""
    proveedor, pago = _proveedor(), _auxpag()
    dca, sin_fuente = _dca(None, None, proveedor, pago)
    origen = _origen_de_cada_columna(dca, proveedor=proveedor, auxpag=pago)
    for columna in modulo.DCA_COLUMNAS:
        if columna in ("pagtex", "pagfor"):
            esperado = "auxpag"
        elif _de_una_fila(columna) and columna not in ("dircon1", "ivadif"):
            esperado = "proveedor"
        else:
            esperado = ""
        assert origen[columna] == esperado, columna
    assert (dca["entide"], dca["entcod"], dca["entres"], dca["entcif"]) == (
        proveedor["ide"], "P:cod", "P:raz", "P:cif")
    assert (dca["entciftip"], dca["entcifpai"], dca["dirdir1"]) == ("P:tipcif", "P:cifpai", "P:dir")
    assert (dca["pagtex"], dca["pagfor"]) == ("A:res", "A:formul")
    assert (dca["dircon1"], dca["ivadif"]) == ("", 0)
    assert sin_fuente == ("dircon1", "ivadif")


def test_f015_r25_centinela_con_contrato_sin_respaldo_todo_del_contrato() -> None:
    """R25, la casilla «con contrato y sin respaldo»: sin respaldo nada cambia;
    la identidad y la cascada salen del contrato y nada del `prv` entra."""
    contrato, proveedor, pago = _contrato(), _proveedor(), _auxpag()
    dca, sin_fuente = _dca(contrato, None, proveedor, pago)
    assert tuple(dca) == modulo.DCA_COLUMNAS
    origen = _origen_de_cada_columna(dca, contrato=contrato, proveedor=proveedor, auxpag=pago)
    for columna in modulo.DCA_COLUMNAS:
        esperado = "contrato" if _de_una_fila(columna) else ""
        assert origen[columna] == esperado, columna
    assert sin_fuente == ()


def test_f015_r25_contrato_sin_cascada_y_sin_respaldo_pasa_al_proveedor() -> None:
    """R3-R5 sin respaldo: con la cascada del contrato vacía, sale del `prv` (pago
    con los textos de su `auxpag`); `dircon1` queda sin fuente; `ivadif` es la
    marca del contrato (D5), 0, y tiene fuente. La identidad sigue en el contrato."""
    contrato = _vaciar(_contrato(), set(modulo.DCA_CASCADA))
    proveedor, pago = _proveedor(), _auxpag()
    dca, sin_fuente = _dca(contrato, None, proveedor, pago)
    for columna, en_prv in modulo.DCA_CASCADA.items():
        if columna in modulo.PAGO_DEL_AUXPAG:
            assert dca[columna] == pago[modulo.PAGO_DEL_AUXPAG[columna]], columna
        elif en_prv is not None:
            assert dca[columna] == proveedor[en_prv], columna
    assert (dca["dircon1"], dca["ivadif"]) == ("", 0)
    assert sin_fuente == ("dircon1",)
    for columna in modulo.DCA_IDENTIDAD:
        assert dca[columna] == contrato[columna], columna


@pytest.mark.parametrize("columna", ["cueide", "eioide", "dirdir1", "dircon1"])
def test_f015_r3_una_columna_vacia_en_el_contrato_pasa_al_respaldo(columna: str) -> None:
    contrato, respaldo = _vaciar(_contrato(), {columna}), _respaldo()
    dca, _ = _dca(contrato, respaldo)
    assert dca[columna] == respaldo[columna]


@pytest.mark.parametrize("columna", ["cueide", "eioide", "dirdir1"])
def test_f015_r3_vacia_en_contrato_y_respaldo_pasa_al_proveedor(columna: str) -> None:
    proveedor = _proveedor()
    dca, _ = _dca(_vaciar(_contrato(), {columna}), _vaciar(_respaldo(), {columna}), proveedor)
    assert dca[columna] == proveedor[modulo.DCA_CASCADA[columna]]


def test_f015_r3_none_cuenta_como_vacio() -> None:
    contrato = {**_contrato(), "cueide": None, "dircon1": None}
    respaldo = _respaldo()
    dca, _ = _dca(contrato, respaldo)
    assert (dca["cueide"], dca["dircon1"]) == (respaldo["cueide"], respaldo["dircon1"])


def test_f015_r3_un_texto_de_espacios_cuenta_como_vacio() -> None:
    respaldo = _respaldo()
    dca, _ = _dca({**_contrato(), "dirdir1": "   "}, respaldo)
    assert dca["dirdir1"] == respaldo["dirdir1"]


def test_f015_r3_pago_en_grupo_del_primer_origen_con_pagide() -> None:
    """Con `pagide` 0 en el contrato, el grupo entero sale del respaldo aunque el
    contrato traiga `pagtex`, `pagfor` o `efeide`."""
    contrato, respaldo = _vaciar(_contrato(), {"pagide"}), _respaldo()
    dca, _ = _dca(contrato, respaldo)
    assert [dca[c] for c in modulo.GRUPO_PAGO] == [respaldo[c] for c in modulo.GRUPO_PAGO]


def test_f015_r3_pago_del_proveedor_con_los_textos_de_su_auxpag() -> None:
    proveedor, pago = _proveedor(), _auxpag()
    contrato = _vaciar(_contrato(), set(modulo.GRUPO_PAGO))
    respaldo = _vaciar(_respaldo(), {"pagide"})
    dca, _ = _dca(contrato, respaldo, proveedor, pago)
    assert [dca[c] for c in modulo.GRUPO_PAGO] == [
        proveedor["pagide"], "A:res", "A:formul", proveedor["efeide"]]
    assert modulo.pago_del_proveedor(contrato, respaldo, proveedor) is True


def test_f015_r3_pago_del_proveedor_sin_su_auxpag_no_construye() -> None:
    with pytest.raises(ValueError, match="auxpag"):
        _dca(None, None, _proveedor(), None)


@pytest.mark.parametrize(
    ("contrato_vacio", "respaldo_vacio", "esperado"),
    [(False, False, False), (True, False, False), (False, True, False), (True, True, True)],
)
def test_f015_r3_pago_del_proveedor_solo_si_nadie_antes_trae_pagide(
    contrato_vacio: bool, respaldo_vacio: bool, esperado: bool
) -> None:
    contrato = _vaciar(_contrato(), {"pagide"}) if contrato_vacio else _contrato()
    respaldo = _vaciar(_respaldo(), {"pagide"}) if respaldo_vacio else _respaldo()
    assert modulo.pago_del_proveedor(contrato, respaldo, _proveedor()) is esperado


def test_f015_r3_pago_del_proveedor_sin_contrato_ni_respaldo() -> None:
    assert modulo.pago_del_proveedor(None, None, _proveedor()) is True
    assert modulo.pago_del_proveedor(None, None, _vaciar(_proveedor(), {"pagide"})) is False


def test_f015_r3_banco_en_grupo_del_primer_origen_con_banban_o_ban() -> None:
    respaldo = _respaldo()
    dca, _ = _dca(_vaciar(_contrato(), {"banban", "ban"}), respaldo)
    assert [dca[c] for c in modulo.GRUPO_BANCO] == [respaldo[c] for c in modulo.GRUPO_BANCO]
    # Basta uno de los dos: `ban` sin `banban`, o `banban` sin `ban`.
    dca, _ = _dca(_vaciar(_contrato(), {"banban"}), respaldo)
    assert (dca["bancue"], dca["banban"]) == ("C:bancue", 0)
    dca, _ = _dca(_vaciar(_contrato(), {"ban"}), respaldo)
    assert (dca["bancue"], dca["ban"]) == ("C:bancue", "")


def test_f015_r3_banco_del_proveedor_si_contrato_y_respaldo_no_lo_traen() -> None:
    proveedor = _proveedor()
    vacio = {"banban", "ban"}
    dca, _ = _dca(_vaciar(_contrato(), vacio), _vaciar(_respaldo(), vacio), proveedor)
    assert [dca[c] for c in modulo.GRUPO_BANCO] == [proveedor[c] for c in modulo.GRUPO_BANCO]


def test_f015_r3_ivadif_del_contrato_aunque_sea_0() -> None:
    """D5: es una marca; con contrato no se mira el respaldo."""
    dca, sin_fuente = _dca(_vaciar(_contrato(), {"ivadif"}), _respaldo())
    assert dca["ivadif"] == 0 and sin_fuente == ()
    dca, _ = _dca(None, _respaldo())
    assert dca["ivadif"] == _respaldo()["ivadif"]


def test_f015_r4_identidad_del_contrato_aunque_venga_vacia() -> None:
    """R4: la identidad no es cascada: con contrato, la del contrato."""
    contrato = _vaciar(_contrato(), {"entciftip"})
    dca, _ = _dca(contrato, _respaldo())
    assert dca["entciftip"] == ""
    assert dca["entide"] == contrato["entide"]


def test_f015_r5_sin_fuente_el_vacio_del_alta_a_mano_y_las_columnas() -> None:
    columnas = set(modulo.DCA_CASCADA)
    proveedor = _vaciar(_proveedor(), {v for v in modulo.DCA_CASCADA.values() if v})
    dca, sin_fuente = _dca(_vaciar(_contrato(), columnas), _vaciar(_respaldo(), columnas), proveedor)
    for columna in modulo.DCA_CASCADA:
        assert dca[columna] == ("" if columna in modulo._DCA_TEXTO else 0), columna
    # `ivadif` sale del contrato (0): tiene fuente.
    assert sin_fuente == tuple(c for c in modulo.DCA_CASCADA if c != "ivadif")


def test_f015_r8_calculadas_de_la_peticion_la_obra_o_un_calculo() -> None:
    dca, _ = _dca(_contrato(), _respaldo(), cuo=Decimal("5.00"))
    assert {c: dca[c] for c in modulo.DCA_CALCULADAS} == {
        "ide": None, "entref": "A-77", "fecdoc": 20261005, "hor": 101530, "obride": 5000,
        "ctride": 300, "almide": 70, "cenide": 80, "empide": 2425207, "synckey": "ALB-1",
        "impbru": 100.0, "impnet": 100.0, "totbas": 100.0, "totiva": 21.0, "totdoc": 121.0,
        "tot": 116.0, "totpag": 116.0, "diremp1": "C:entres",
    }


def test_f015_r8_diremp1_es_la_entres_escrita() -> None:
    dca, _ = _dca(None, None, _proveedor(), _auxpag())
    assert dca["diremp1"] == dca["entres"] == "P:raz"


def test_f015_r9_fijas_en_la_fila_aunque_todas_las_filas_las_traigan() -> None:
    dca, _ = _dca(_contrato(), _respaldo(), _proveedor(), _auxpag())
    assert {c: dca[c] for c in modulo.DCA_FIJAS} == modulo.DCA_FIJAS
    assert (dca["tipgar"], dca["emptex"], dca["fecfac"], dca["idefac"], dca["dtumID"]) == (
        -1, None, 0, 0, "")


@pytest.mark.parametrize(
    ("fila", "columna"),
    [("contrato", "pagide"), ("contrato", "entcifpai"), ("respaldo", "dircon1"),
     ("proveedor", "dir"), ("auxpag", "formul")],
)
def test_f015_r10_columna_que_falta_en_su_fila_falla_sin_construir(fila: str, columna: str) -> None:
    filas = {"contrato": _contrato(), "respaldo": _respaldo(), "proveedor": _proveedor(),
             "auxpag": _auxpag()}
    del filas[fila][columna]
    if fila == "auxpag":
        filas["contrato"] = _vaciar(filas["contrato"], {"pagide"})
        filas["respaldo"] = _vaciar(filas["respaldo"], {"pagide"})
    with pytest.raises(ValueError, match=columna):
        _dca(filas["contrato"], filas["respaldo"], filas["proveedor"], filas["auxpag"])


def test_f015_r10_sin_contrato_la_identidad_del_respaldo_es_obligatoria() -> None:
    respaldo = _respaldo()
    del respaldo["entcod"]
    with pytest.raises(ValueError, match="entcod"):
        _dca(None, respaldo)
    # Con contrato, al respaldo no se le pide la identidad.
    _dca(_contrato(), respaldo)


def test_f015_r10_sin_contrato_ni_respaldo_la_identidad_del_proveedor_es_obligatoria() -> None:
    proveedor = _proveedor()
    del proveedor["cod"]
    with pytest.raises(ValueError, match="cod"):
        _dca(None, None, proveedor, _auxpag())
    _dca(None, _respaldo(), proveedor)


# =====================================================================================
# T6 · R1, R24: `INSERT` de `con` y `dca` con columnas fijas
# =====================================================================================


def test_f015_r1_insert_de_con_con_sus_19_columnas_fijas(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    from application.use_cases.parte_reclamacion_statements import CON_COLUMNAS

    fila = {columna: columna for columna in reversed(CON_COLUMNAS)}
    assert sentencias.insertar_con(fila) == (
        (
            "INSERT INTO dbo.con (ide, emp, tip, subtip, cod, res, fec, tex, cee, est, fecbaj, "
            "tiemod, ico, delo, del, obr, doc, serie, hor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
            "?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        list(CON_COLUMNAS),
    )


def test_f015_r1_insert_de_dca_con_sus_145_columnas_fijas(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    fila = {columna: i for i, columna in reversed(list(enumerate(modulo.DCA_COLUMNAS)))}
    sql, params = sentencias.insertar_dca(fila)
    assert sql == (
        "INSERT INTO dbo.dca (" + ", ".join(_DCA_DE_LA_SPEC) + ") VALUES ("
        + ", ".join(["?"] * 145) + ")"
    )
    assert sql.startswith("INSERT INTO dbo.dca (ide, cla, entide, entcod, entres, entref, ")
    assert sql.count("?") == 145 and "[" not in sql
    assert params == list(range(145))


@pytest.mark.parametrize("metodo", ["insertar_con", "insertar_dca"])
def test_f015_r1_una_fila_de_cabecera_que_no_cuadra_no_se_inserta(
    sentencias: modulo.AlbaranCompraStatements, metodo: str
) -> None:
    """D6: ni una columna de más (de una fila leída) ni una de menos."""
    from application.use_cases.parte_reclamacion_statements import CON_COLUMNAS

    columnas = CON_COLUMNAS if metodo == "insertar_con" else modulo.DCA_COLUMNAS
    fila = dict.fromkeys(columnas, 0)
    with pytest.raises(ValueError, match="sobran"):
        getattr(sentencias, metodo)({**fila, "usu": "viejo"})
    del fila["ide"]
    with pytest.raises(ValueError, match="faltan"):
        getattr(sentencias, metodo)(fila)


def test_f015_r24_solo_dcapro_se_clona() -> None:
    assert frozenset({"dcapro"}) == modulo._TABLAS_CLONADAS
    sentencias = modulo.AlbaranCompraStatements(database="ruesma")
    for tabla in ("con", "dca"):
        with pytest.raises(ValueError, match="no se escribe por clonado"):
            sentencias.insertar_clonada(tabla, {"ide": 1})


def test_f015_r24_los_insert_de_cabecera_se_validan_al_construir() -> None:
    from application.use_cases.parte_reclamacion_statements import CON_COLUMNAS

    todas = modulo.AlbaranCompraStatements.todas_las_sentencias()
    assert modulo._insert_fijo("con", CON_COLUMNAS) in todas
    assert modulo._insert_fijo("dca", modulo.DCA_COLUMNAS) in todas


# =====================================================================================
# T9 · R12, R14: L16 y `resolver_retencion`
# =====================================================================================


def test_f015_r12_sql_l16_recargos_del_contrato_con_su_clase(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_retenciones(300) == (
        (
            "SELECT r.ide, r.recide, r.pos, r.valdef, r.valpor, r.valcan, r.valmod, r.valfij, "
            "r.reccla, r.cueide, r.ivaide, r.tex, r.resalt, r.item, x.cla, c.cod FROM dbo.ctrrec r "
            "LEFT JOIN dbo.rec x ON x.ide = r.recide LEFT JOIN dbo.con c ON c.ide = r.recide "
            "WHERE r.docide = ? ORDER BY r.pos, r.ide"
        ),
        [300],
    )
    assert modulo.L16_RETENCIONES in modulo.AlbaranCompraStatements.todas_las_sentencias()
    assert modulo.L16_COLUMNAS == (
        "ide", "recide", "pos", "valdef", "valpor", "valcan", "valmod", "valfij", "reccla",
        "cueide", "ivaide", "tex", "resalt", "item", "cla", "cod",
    )


def ctrrec(**valores: object) -> dict:
    """Un `ctrrec` de `RET5` como los de M11, con la clase de su `rec` y su `cod`."""
    return {
        "ide": 7001, "recide": 6005, "pos": 64, "valdef": 1, "valpor": 0.05, "valcan": 0.0,
        "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4705, "ivaide": 0, "tex": "",
        "resalt": "", "item": 0, "cla": 5, "cod": "RET5", **valores,
    }


def test_f015_r12_sin_ctrrec_no_hay_retencion() -> None:
    assert modulo.resolver_retencion([]) is None


@pytest.mark.parametrize("cla", [3, 4, 5])
def test_f015_r12_un_ctrrec_soportado_es_la_retencion(cla: int) -> None:
    fila = ctrrec(cla=cla)
    assert modulo.resolver_retencion([fila]) == fila


def test_f015_r14_valpor_0_es_soportado_solo_none_no() -> None:
    """R14: un 0 % se sabe calcular (`cuo` 0); solo `valpor` NULL no. Mata el
    mutante a mano `if not fila["valpor"]` (pasada 2)."""
    fila = ctrrec(valpor=0.0)
    assert modulo.resolver_retencion([fila]) == fila
    totales = {"totbas": 21.0, "totiva": 4.41, "totdoc": 25.41}
    assert modulo.calcular_retencion(fila, totales) == (Decimal("21.00"), Decimal("0.00"))


@pytest.mark.parametrize(
    ("filas", "motivo"),
    [
        ([ctrrec(), ctrrec(ide=7002, pos=128)], "2 recargos"),
        ([ctrrec(recide=0, cla=None, cod=None)], "sin recargo"),
        ([ctrrec(cla=None, cod=None)], "no esta en dbo.rec"),
        ([ctrrec(cla=1, cod="RETESP")], "clase 1"),
        ([ctrrec(valfij=1)], "valfij"),
        ([ctrrec(ivaide=777740)], "ivaide"),
        ([ctrrec(valpor=None)], "sin porcentaje"),
    ],
    ids=["varias", "recide_0", "sin_rec", "clase_1", "valfij", "ivaide", "valpor_null"],
)
def test_f015_r14_ctrrec_no_soportado(filas: list, motivo: str) -> None:
    with pytest.raises(modulo.RetencionNoSoportada, match=motivo) as excinfo:
        modulo.resolver_retencion(filas)
    assert isinstance(excinfo.value, ValueError)


def test_f015_r14_clases_soportadas_y_su_base() -> None:
    assert modulo.CLASES_RETENCION_BASE == {5: "totbas", 3: "totbas", 4: "totdoc"}


# =====================================================================================
# T10 · R13, R15: `calcular_retencion` y `construir_dcarec`
# =====================================================================================


@pytest.mark.parametrize(
    ("cla", "esperado"),
    [(5, (Decimal("1000.00"), Decimal("50.00"))), (3, (Decimal("1000.00"), Decimal("50.00"))),
     (4, (Decimal("1210.00"), Decimal("60.50")))],
)
def test_f015_r15_base_por_clase_del_recargo(cla: int, esperado: tuple) -> None:
    """M12: clases 5 y 3 sobre `totbas`; la 4, sobre `totdoc`."""
    totales = {"totbas": 1000.0, "totiva": 210.0, "totdoc": 1210.0}
    assert modulo.calcular_retencion(ctrrec(cla=cla), totales) == esperado


def test_f015_r15_empate_a_medio_centimo_lejos_del_cero() -> None:
    """M12: 3.775,30 · 0,05 = 188,765 -> 188,77, en `Decimal` y no en binario (el
    `float` de SQL da 188,76 en los 45 empates de M12)."""
    totales = {"totbas": 3775.30, "totiva": 792.81, "totdoc": 4568.11}
    assert modulo.calcular_retencion(ctrrec(), totales) == (Decimal("3775.30"), Decimal("188.77"))
    negativos = {"totbas": -3775.30, "totiva": -792.81, "totdoc": -4568.11}
    assert modulo.calcular_retencion(ctrrec(), negativos) == (
        Decimal("-3775.30"), Decimal("-188.77"))


def test_f015_r15_en_decimal_no_en_binario() -> None:
    """21,50 · 0,05 = 1,075 -> 1,08; en `float`, `round` daría 1,07."""
    assert round(21.5 * 0.05, 2) == 1.07  # el error que se evita
    totales = {"totbas": 21.5, "totiva": 0.0, "totdoc": 21.5}
    assert modulo.calcular_retencion(ctrrec(), totales) == (Decimal("21.50"), Decimal("1.08"))


@pytest.mark.parametrize(
    ("valpor", "totbas", "cuo"),
    [(0.015, 1.0, "0.02"), (0.015, -3.0, "-0.05"), (0.03, 0.5, "0.02")],
)
def test_f015_r15_valpor_por_su_repr_y_no_por_su_binario(
    valpor: float, totbas: float, cuo: str
) -> None:
    """`ctrrec.valpor` es `Real` (llega `float`): 0,015 y 0,03 (M11) quedan en binario
    justo por debajo de su decimal y, en empate a medio céntimo, `Decimal(valpor)`
    redondearía hacia abajo (0,01; -0,04). Mata a M10 de la revisión de mutación."""
    assert Decimal(valpor) < Decimal(repr(valpor))  # el binario que se evita
    totales = {"totbas": totbas, "totiva": 0.0, "totdoc": totbas}
    _bas, calculada = modulo.calcular_retencion(ctrrec(valpor=valpor), totales)
    assert calculada == Decimal(cuo)


def test_f015_r15_totbas_0_retencion_0() -> None:
    totales = {"totbas": 0.0, "totiva": 0.0, "totdoc": 0.0}
    assert modulo.calcular_retencion(ctrrec(), totales) == (Decimal("0.00"), Decimal("0.00"))


def test_f015_r15_otro_porcentaje() -> None:
    totales = {"totbas": 1234.56, "totiva": 0.0, "totdoc": 1234.56}
    assert modulo.calcular_retencion(ctrrec(valpor=0.015), totales) == (
        Decimal("1234.56"), Decimal("18.52"))


def test_f015_r13_dcarec_copia_del_ctrrec_con_bas_y_cuo() -> None:
    fila = modulo.construir_dcarec(
        ctrrec(tex="RETENCION 5%", resalt="R5", item=3), bas=Decimal("1000.00"),
        cuo=Decimal("50.00"),
    )
    assert tuple(fila) == modulo.DCAREC_COLUMNAS
    assert fila == {
        "ide": None, "docide": None, "recide": 6005, "pos": 64, "bas": 1000.0, "valdef": 1,
        "valpor": 0.05, "valcan": 0.0, "valmod": 0, "valfij": 0, "cuo": 50.0,
        "tex": "RETENCION 5%", "reccla": 5, "cueide": 4705, "ivaide": 0, "ivacuo": 0,
        "reqcuo": 0, "refide": 0, "resalt": "R5", "item": 3, "frasupide": 0,
    }
    assert (type(fila["bas"]), type(fila["cuo"])) == (float, float)


def test_f015_r13_dcarec_columnas_del_esquema_vivo() -> None:
    """M14: las 21 columnas de `dbo.dcarec`."""
    assert modulo.DCAREC_COLUMNAS == (
        "ide", "docide", "recide", "pos", "bas", "valdef", "valpor", "valcan", "valmod", "valfij",
        "cuo", "tex", "reccla", "cueide", "ivaide", "ivacuo", "reqcuo", "refide", "resalt",
        "frasupide", "item",
    )


# =====================================================================================
# T11 · R13, R17, R20: el total neto, `FilasAlbaran.dcarec` y `numerar`
# =====================================================================================


@pytest.mark.parametrize(
    ("cuo", "tot"), [(Decimal("50.00"), 71.0), (Decimal(0), 121.0), (Decimal("-6.05"), 127.05)]
)
def test_f015_r13_tot_y_totpag_netos_de_la_retencion(cuo: Decimal, tot: float) -> None:
    dca, _ = _dca(_contrato(), _respaldo(), cuo=cuo)
    assert (dca["totdoc"], dca["tot"], dca["totpag"]) == (121.0, tot, tot)
    assert (dca["imprec"], dca["totbas"]) == (0, 100.0)  # M13: la retención no va en `imprec`


def test_f015_r13_tot_neto_sin_error_binario() -> None:
    dca, _ = modulo.construir_dca(
        contrato=_contrato(), proveedor=_proveedor(), pago_proveedor=None, respaldo=_respaldo(),
        fec=1, hor=1, su_referencia="", obride=1, ctride=1, almide=1, cenide=1, empide=1,
        totales={"totbas": 3775.3, "totiva": 792.81, "totdoc": 4568.11}, cuo=Decimal("188.77"),
        referencia_externa="ALB-1",
    )
    assert dca["tot"] == 4379.34


def _filas(dcarec: list | None = None) -> modulo.FilasAlbaran:
    extra = {} if dcarec is None else {"dcarec": dcarec}
    return modulo.FilasAlbaran(
        con={"ide": None, "cod": None}, dca={"ide": None}, dcapro=[{"ide": None, "docide": None}],
        ctrprodes=[], mov=[], log={"ide": None, "cod": None}, **extra,
    )


def test_f015_r17_filas_sin_dcarec_por_defecto_y_en_el_diccionario() -> None:
    filas = _filas()
    assert filas.dcarec == []
    assert filas.como_dict()["dcarec"] == []
    assert list(filas.como_dict()) == ["con", "dca", "dcapro", "ctrprodes", "mov", "dcarec", "log"]


def test_f015_r20_numerar_pone_ide_y_docide_a_la_dcarec() -> None:
    dcarec = {"ide": None, "docide": None, "recide": 6005}
    filas = _filas([dcarec])
    numeradas = modulo.numerar(
        filas, cod="AC26/1", ide_con=2900001, ide_dcapro=8000001, ide_ctrprodes=None,
        ide_mov=None, ide_log=8488889, ide_dcarec=44134,
    )
    assert numeradas.dcarec == [{"ide": 44134, "docide": 2900001, "recide": 6005}]
    assert numeradas.como_dict()["dcarec"] == numeradas.dcarec
    assert filas.dcarec == [{"ide": None, "docide": None, "recide": 6005}]  # reentrante (R22)


def test_f015_r20_numerar_con_dcarec_sin_ide_no_numera() -> None:
    with pytest.raises(ValueError, match="dcarec"):
        modulo.numerar(
            _filas([{"ide": None, "docide": None}]), cod="x", ide_con=1, ide_dcapro=1,
            ide_ctrprodes=None, ide_mov=None, ide_log=None, ide_dcarec=None,
        )


def test_f015_r20_numerar_sin_dcarec_no_necesita_ide() -> None:
    numeradas = modulo.numerar(
        _filas(), cod="x", ide_con=1, ide_dcapro=1, ide_ctrprodes=None, ide_mov=None,
        ide_log=None,
    )
    assert numeradas.dcarec == []


# =====================================================================================
# T12 · R18: L11 lee también el `tot` del albarán existente
# =====================================================================================


def test_f015_r18_sql_l11_con_el_tot(sentencias: modulo.AlbaranCompraStatements) -> None:
    assert sentencias.buscar_referencia("ALB-1") == (
        (
            "SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc, d.tot "
            "FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?"
        ),
        [14, "ALB-1"],
    )


# =====================================================================================
# T13 · R21, R23, R24: applock, E6b, `INSERT` de `dcarec`, E12 y control negativo
# =====================================================================================


def test_f015_r21_applock_de_dcarec_entre_mov_y_log() -> None:
    assert modulo.APPLOCKS == (
        "SIGRID_REFEXT_14", "SIGRID_SERIE_14", "SIGRID_IDE_con", "SIGRID_IDE_dcapro",
        "SIGRID_IDE_ctrprodes", "SIGRID_IDE_mov", "SIGRID_IDE_dcarec", "SIGRID_IDE_log",
    )


def test_f015_r21_sql_e6b_reserva_del_ide_de_dcarec(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    assert sentencias.reservar_ide_dcarec() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcarec WITH (UPDLOCK, HOLDLOCK)", [])


def test_f015_r21_sql_insert_de_dcarec_con_sus_21_columnas(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    fila = {columna: f"v_{columna}" for columna in reversed(modulo.DCAREC_COLUMNAS)}
    sql, parametros = sentencias.insertar_dcarec(fila)
    assert sql == (
        "INSERT INTO dbo.dcarec (ide, docide, recide, pos, bas, valdef, valpor, valcan, valmod, "
        "valfij, cuo, tex, reccla, cueide, ivaide, ivacuo, reqcuo, refide, resalt, frasupide, item) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    assert parametros == [f"v_{columna}" for columna in modulo.DCAREC_COLUMNAS]


@pytest.mark.parametrize("cambio", ["sobra", "falta"])
def test_f015_r21_insert_de_dcarec_con_otras_columnas_no_se_construye(
    sentencias: modulo.AlbaranCompraStatements, cambio: str
) -> None:
    fila = dict.fromkeys(modulo.DCAREC_COLUMNAS, 0)
    if cambio == "sobra":
        fila["frasupide2"] = 0
    else:
        del fila["item"]
    with pytest.raises(ValueError, match="dcarec"):
        sentencias.insertar_dcarec(fila)


def test_f015_r23_sql_e12_relectura_de_dcarec(sentencias: modulo.AlbaranCompraStatements) -> None:
    assert sentencias.releer_dcarec(2900011) == (
        "SELECT COUNT(*) FROM dbo.dcarec WHERE docide = ?", [2900011])


def test_f015_r24_las_sentencias_nuevas_estan_validadas(
    sentencias: modulo.AlbaranCompraStatements,
) -> None:
    todas = modulo.AlbaranCompraStatements.todas_las_sentencias()
    for sql in (
        sentencias.reservar_ide_dcarec()[0],
        sentencias.insertar_dcarec(dict.fromkeys(modulo.DCAREC_COLUMNAS))[0],
        sentencias.releer_dcarec(1)[0],
        sentencias.leer_retenciones(1)[0],
        sentencias.leer_proveedor_por_cif(1, "x")[0],
        sentencias.leer_plantilla_cabecera(1, 1)[0],
        sentencias.leer_plantilla_cabecera_por_cif(1, "x")[0],
        sentencias.buscar_referencia("x")[0],
        sentencias.insertar_con(dict.fromkeys(modulo.CON_COLUMNAS))[0],
        sentencias.insertar_dca(dict.fromkeys(modulo.DCA_COLUMNAS))[0],
    ):
        assert sql in todas, sql


def test_f015_r24_control_negativo_ningun_update_delete_merge_ni_ddl_nuevo() -> None:
    import re

    todas = modulo.AlbaranCompraStatements.todas_las_sentencias()
    assert len(todas) == len(set(todas)) == 47  # 40 de F-009 + L16, L17, E6b, E12 y 3 INSERT fijos
    updates = [sql for sql in todas if "UPDATE" in sql.upper().replace("UPDLOCK", "")]
    assert updates == [modulo.E9_SERVIDO, modulo.E11_ESTADOS_CONTRATO]
    prohibidos = re.compile(r"\b(DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC)\b", re.IGNORECASE)
    for sql in todas:
        assert not prohibidos.search(sql), sql
        # El unico literal es el `''` de L5 que fija la spec (design §Sentencias): una
        # constante del SQL, no un valor de la peticion.
        assert "'" not in sql.replace("ISNULL(d.entref, '')", "") and ";" not in sql, sql
    insertadas = {re.match(r"INSERT INTO dbo\.(\w+) ", sql).group(1)
                  for sql in todas if sql.startswith("INSERT")}
    assert insertadas == {"con", "dca", "ctrprodes", "mov", "dcarec", "log"}  # `dcapro`, clonada


def test_f015_r12_numerar_con_dos_dcarec_no_numera() -> None:
    """R12: una `dcarec` como mucho. Lo mide la campaña de mutación: un `ide`
    consecutivo por fila (`ide_dcarec + n`) era código muerto (T18)."""
    with pytest.raises(ValueError, match="una dcarec"):
        modulo.numerar(
            _filas([{"ide": None, "docide": None}, {"ide": None, "docide": None}]), cod="x",
            ide_con=1, ide_dcapro=1, ide_ctrprodes=None, ide_mov=None, ide_log=None,
            ide_dcarec=44134,
        )
