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


@pytest.mark.parametrize(
    ("filas", "motivo"),
    [
        ([ctrrec(), ctrrec(ide=7002, pos=128)], "2 recargos"),
        ([ctrrec(recide=0, cla=None, cod=None)], "sin recargo"),
        ([ctrrec(cla=None, cod=None)], "no esta en dbo.rec"),
        ([ctrrec(cla=1, cod="RETESP")], "clase 1"),
        ([ctrrec(valfij=1)], "valfij"),
        ([ctrrec(ivaide=777740)], "ivaide"),
    ],
    ids=["varias", "recide_0", "sin_rec", "clase_1", "valfij", "ivaide"],
)
def test_f015_r14_ctrrec_no_soportado(filas: list, motivo: str) -> None:
    with pytest.raises(modulo.RetencionNoSoportada, match=motivo) as excinfo:
        modulo.resolver_retencion(filas)
    assert isinstance(excinfo.value, ValueError)


def test_f015_r14_clases_soportadas_y_su_base() -> None:
    assert modulo.CLASES_RETENCION_BASE == {5: "totbas", 3: "totbas", 4: "totdoc"}
