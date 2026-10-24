# tests/test_f015_use_case.py
"""
F-015 · el caso de uso del modo extendido de `sigrid/albaran`
(`application/use_cases/create_albaran_compra_use_case.py`) con la cabecera por
lista blanca (O1) y la retención del contrato (O2).

Sin red y sin base de datos: los dobles de `f009_dobles.py`, que reconocen cada
sentencia por su SQL exacto. Datos sintéticos.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from f009_dobles import (
    AHORA,
    AUXPAG_PRV,
    CTR,
    ENTIDE,
    OBRA,
    PEEK,
    PLANTILLA_CABECERA,
    RESERVAS,
    IntegrityError,
    RepositorioDoble,
    SettingsDoble,
    ctr,
    dca_plantilla,
    prv,
)

from application.use_cases.albaran_compra_statements import (
    APPLOCKS,
    GRUPO_BANCO,
    GRUPO_PAGO,
    L16_COLUMNAS,
)
from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
)
from domain.models.albaran_compra_models import AlbaranCompraError, AlbaranCompraRequest


def vinculada(ref: str = "L1", ctrpro_ide: int = 9001, **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "ctrpro_ide": ctrpro_ide, "cantidad": 2.0, "precio": 10.5,
            **extra}


def sin_vincular(ref: str = "L2", producto: str = "MA9999", **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "producto": producto, "descripcion": "Arena de rio",
            "unidad": "m3", "cantidad": 3.0, "precio": 2.675, **extra}


def peticion(lineas: list[dict[str, Any]] | None = None, **cambios: Any) -> AlbaranCompraRequest:
    base = {
        "database": "ruesma", "cod_obra": "0404", "usu": "prueba",
        "cif_proveedor": "B12345678", "referencia_externa": "ALB-1",
        "cod_contrato": "CTSU16/0206", "su_referencia": "A-77", "fecha_albaran": 20261005,
        "lineas": lineas if lineas is not None else [vinculada()],
    }
    return AlbaranCompraRequest.model_validate({**base, **cambios})


def ejecutar(lineas=None, *, repo: RepositorioDoble | None = None, **cambios: Any):
    repo = repo or RepositorioDoble()
    caso = CreateAlbaranCompraUseCase(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    return caso.run(peticion(lineas, **cambios)), repo


def codigo(lineas=None, **kwargs: Any) -> str:
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(lineas, **kwargs)
    return excinfo.value.codigo


#: Sin contrato, la línea sin vincular necesita la analítica del centro del
#: almacén de la ficha de obra (82 en el doble).
_ANALITICA_SIN_CONTRATO = {"analiticas": [(721, "0404.CDSB37", 82)]}


def _sin_contrato(lecturas: dict[str, Any] | None = None, **kwargs: Any):
    repo = RepositorioDoble({**_ANALITICA_SIN_CONTRATO, **(lecturas or {})}, **kwargs)
    return ejecutar([sin_vincular()], repo=repo, cod_contrato=None)


def _leidas_completas(repo: RepositorioDoble) -> list[tuple[str, int]]:
    return [datos for tipo, datos in repo.llamadas if tipo == "read_full_row"]


def _con_pago(**valores: Any) -> dict[str, Any]:
    return {"pagide": 41, "pagtex": "CONFIRMING 120", "pagfor": "120", "efeide": 42, **valores}


#: El `auxpag` y el `auxefp` (pagaré: sin banco no avisa) de `_con_pago`.
_AUXILIARES_DEL_PAGO = {
    ("auxpag", 41): {"ide": 41, "cod": "CF120", "res": "CONFIRMING 120 (PRV)", "formul": "120"},
    ("auxefp", 42): {"ide": 42, "cod": "P", "res": "PAGARE"},
}


# =====================================================================================
# T7 · R6: el respaldo es opcional y nunca una proforma
# =====================================================================================


def test_f015_r6_l5_con_serie_clase_y_sin_proformas() -> None:
    respuesta, repo = ejecutar()
    assert repo.parametros_de("plantilla_por_entide") == [[14, 1, ENTIDE, "AC__/%", 0, "PROF%"]]
    assert respuesta.contrato["template_ide"] == PLANTILLA_CABECERA


def test_f015_r6_no_se_lee_la_con_del_albaran_anterior() -> None:
    _respuesta, repo = ejecutar()
    assert ("dca", PLANTILLA_CABECERA) in _leidas_completas(repo)
    assert ("con", PLANTILLA_CABECERA) not in _leidas_completas(repo)


def test_f015_r6_sin_respaldo_el_alta_sigue_con_contrato_y_proveedor() -> None:
    """D4: sin albarán anterior no hay error; `template_ide` 0 (R17)."""
    repo = RepositorioDoble(
        {"plantilla_por_entide": []},
        filas={("ctr", CTR): {**ctr(), **_con_pago()}, ("prv", ENTIDE): prv(cueide=55, dir="C/ P"),
               **_AUXILIARES_DEL_PAGO},
    )
    respuesta, repo = ejecutar(repo=repo)
    assert respuesta.estado == "previsto"
    assert respuesta.contrato["template_ide"] == 0
    assert not any(t == "dca" for t, _ in _leidas_completas(repo))
    dca = respuesta.filas["dca"]
    assert [dca[c] for c in GRUPO_PAGO] == [41, "CONFIRMING 120", "120", 42]
    assert (dca["cueide"], dca["dirdir1"]) == (55, "C/ P")
    assert "proveedor_por_cif" not in repo.lecturas_hechas()


def test_f015_r6_sin_contrato_el_respaldo_por_cif_da_la_identidad() -> None:
    respuesta, repo = _sin_contrato()
    assert repo.parametros_de("plantilla_por_cif") == [[14, 1, "B12345678", "AC__/%", 0, "PROF%"]]
    assert "proveedor_por_cif" not in repo.lecturas_hechas()
    assert ("prv", ENTIDE) in _leidas_completas(repo)
    dca = respuesta.filas["dca"]
    assert (dca["entide"], dca["entcod"], dca["entres"], dca["entcifpai"]) == (
        ENTIDE, "P0077", "PROVEEDOR PRUEBA SL", "ES")
    assert respuesta.contrato["template_ide"] == PLANTILLA_CABECERA


def test_f015_r6_respaldo_ilegible_no_sigue() -> None:
    with pytest.raises(ValueError, match="respaldo"):
        ejecutar(repo=RepositorioDoble(filas={("dca", PLANTILLA_CABECERA): None}))


# =====================================================================================
# T7 · R7: sin contrato ni respaldo, el proveedor por CIF
# =====================================================================================


def test_f015_r7_sin_contrato_ni_respaldo_el_prv_unico_del_cif() -> None:
    repo_lecturas = {"plantilla_por_cif": [], "proveedor_por_cif": [(88, "P0088 ")]}
    filas = {("prv", 88): prv(ide=88, raz="OTRO PROVEEDOR SA", pagide=41, efeide=42),
             **_AUXILIARES_DEL_PAGO}
    respuesta, repo = _sin_contrato(repo_lecturas, filas=filas)
    assert repo.parametros_de("proveedor_por_cif") == [[5, 1, 0, "B12345678"]]
    dca = respuesta.filas["dca"]
    assert (dca["entide"], dca["entcod"], dca["entres"], dca["diremp1"]) == (
        88, "P0088", "OTRO PROVEEDOR SA", "OTRO PROVEEDOR SA")
    assert respuesta.filas["con"]["res"] == "OTRO PROVEEDOR SA. (A-77)"
    assert respuesta.contrato["entide"] == 88 and respuesta.contrato["template_ide"] == 0
    # El pago del `prv`, con los textos de su `auxpag`.
    assert ("auxpag", 41) in _leidas_completas(repo)
    assert [dca[c] for c in GRUPO_PAGO] == [41, "CONFIRMING 120 (PRV)", "120", 42]


@pytest.mark.parametrize(
    ("filas_l17", "esperado"),
    [([], "proveedor_no_encontrado"), ([(88, "P0088"), (89, "P0089")], "proveedor_ambiguo")],
)
def test_f015_r7_sin_proveedor_unico_por_cif_no_se_da_de_alta(filas_l17: list, esperado: str) -> None:
    repo = RepositorioDoble(
        {**_ANALITICA_SIN_CONTRATO, "plantilla_por_cif": [], "proveedor_por_cif": filas_l17}
    )
    assert codigo([sin_vincular()], repo=repo, cod_contrato=None) == esperado
    assert repo.lecturas_hechas() == ["obra", "plantilla_por_cif", "proveedor_por_cif"]
    assert not any(t in ("read_full_row", "peek", "transaccion") for t, _ in repo.llamadas)


def test_f015_r7_con_contrato_sin_respaldo_no_se_busca_por_cif() -> None:
    _respuesta, repo = ejecutar(repo=RepositorioDoble({"plantilla_por_entide": []}))
    assert "proveedor_por_cif" not in repo.lecturas_hechas()
    assert ("prv", ENTIDE) in _leidas_completas(repo)


def test_f015_r7_proveedor_ilegible_no_sigue() -> None:
    with pytest.raises(ValueError, match="prv"):
        ejecutar(repo=RepositorioDoble(filas={("prv", ENTIDE): None}))


# =====================================================================================
# T7 · R3, R4: la cascada y la identidad en el caso de uso
# =====================================================================================


def test_f015_r4_con_contrato_la_identidad_del_contrato() -> None:
    respuesta, _ = ejecutar(repo=RepositorioDoble(
        filas={("ctr", CTR): {**ctr(), "entcod": "P0077-C", "entciftip": "02"}}
    ))
    dca = respuesta.filas["dca"]
    assert (dca["entide"], dca["entcod"], dca["entciftip"], dca["entcifpai"]) == (
        ENTIDE, "P0077-C", "02", "ES")


def test_f015_r3_el_contrato_manda_sobre_el_respaldo() -> None:
    respuesta, repo = ejecutar(repo=RepositorioDoble(filas={("ctr", CTR): {**ctr(), **_con_pago()}}))
    assert [respuesta.filas["dca"][c] for c in GRUPO_PAGO] == [41, "CONFIRMING 120", "120", 42]
    assert not any(t == "auxpag" for t, _ in _leidas_completas(repo))


def test_f015_r3_sin_pago_en_contrato_el_del_respaldo() -> None:
    respuesta, repo = ejecutar()
    assert [respuesta.filas["dca"][c] for c in GRUPO_PAGO] == [12, "PAGARE 90 DIAS", "90", 13]
    assert not any(t == "auxpag" for t, _ in _leidas_completas(repo))


def test_f015_r3_sin_pago_en_contrato_ni_respaldo_el_del_prv_con_su_auxpag() -> None:
    repo = RepositorioDoble(filas={
        ("dca", PLANTILLA_CABECERA): dca_plantilla(pagide=0, pagtex="", pagfor="", efeide=0),
        ("prv", ENTIDE): prv(pagide=AUXPAG_PRV, efeide=13),
    })
    respuesta, repo = ejecutar(repo=repo)
    assert [respuesta.filas["dca"][c] for c in GRUPO_PAGO] == [
        AUXPAG_PRV, "PAGARE 120 DIAS", "120", 13]
    # El `auxpag` se lee después de `conest` y `usu`, una vez.
    assert _leidas_completas(repo).count(("auxpag", AUXPAG_PRV)) == 1


def test_f015_r3_auxpag_ilegible_no_sigue() -> None:
    repo = RepositorioDoble(filas={
        ("dca", PLANTILLA_CABECERA): dca_plantilla(pagide=0),
        ("prv", ENTIDE): prv(pagide=99),
    })
    with pytest.raises(ValueError, match="auxpag"):
        ejecutar(repo=repo)
    assert not any(t in ("peek", "transaccion") for t, _ in repo.llamadas)


def test_f015_r3_la_respuesta_lleva_lo_escrito_sin_las_bancarias() -> None:
    respuesta, _ = ejecutar()
    for fila in (respuesta.cabecera, respuesta.filas["dca"]):
        assert not set(GRUPO_BANCO) & set(fila)
        assert (fila["fecfac"], fila["idefac"], fila["totbasdiv"], fila["dtumID"], fila["tipgar"]) == (
            0, 0, 0, "", -1)


# =====================================================================================
# T7 · R5: `cabecera_sin_dato`
# =====================================================================================


def _sin_banco(efecto: str, **lecturas: Any) -> RepositorioDoble:
    """Ni el contrato, ni el respaldo, ni el `prv` traen banco; el efecto del
    pago escrito (el del respaldo, 13) es `efecto`."""
    return RepositorioDoble(lecturas or None, filas={
        ("dca", PLANTILLA_CABECERA): dca_plantilla(banban=0, bancue="", ban=""),
        ("auxefp", 13): {"ide": 13, "cod": efecto, "res": "x"},
    })


def _avisos(respuesta: Any) -> list[tuple[str, str]]:
    return [(a.codigo, a.mensaje) for a in respuesta.avisos]


@pytest.mark.parametrize("efecto", ["CC", "CT", "TR", " cc "])
def test_f015_r5_banco_sin_fuente_con_confirming_o_transferencia_avisa(efecto: str) -> None:
    respuesta, repo = ejecutar(repo=_sin_banco(efecto))
    assert _avisos(respuesta) == [
        ("cod_provisional", respuesta.avisos[0].mensaje),
        ("cabecera_sin_dato",
         ("Ni el contrato, ni el albaran anterior, ni el proveedor traen banban, bansuc, bandig, "
          "bancue, ban, bantipide: se escriben vacias, como el alta a mano.")),
    ]
    assert ("auxefp", 13) in _leidas_completas(repo)
    assert respuesta.estado == "previsto"


@pytest.mark.parametrize("efecto", ["P", "R", ""])
def test_f015_r5_banco_sin_fuente_con_pagare_o_recibo_no_avisa(efecto: str) -> None:
    respuesta, _ = ejecutar(repo=_sin_banco(efecto))
    assert [a.codigo for a in respuesta.avisos] == ["cod_provisional"]


def test_f015_r5_con_banco_no_se_lee_el_efecto() -> None:
    _respuesta, repo = ejecutar()
    assert not any(t == "auxefp" for t, _ in _leidas_completas(repo))


def test_f015_r5_banco_sin_fuente_y_sin_efecto_no_avisa_ni_lee() -> None:
    repo = RepositorioDoble(filas={
        ("dca", PLANTILLA_CABECERA): dca_plantilla(banban=0, bancue="", ban="", efeide=0),
    })
    respuesta, repo = ejecutar(repo=repo)
    assert [a.codigo for a in respuesta.avisos] == ["cod_provisional"]
    assert not any(t == "auxefp" for t, _ in _leidas_completas(repo))


def test_f015_r5_efecto_ilegible_no_sigue() -> None:
    repo = RepositorioDoble(filas={("dca", PLANTILLA_CABECERA): dca_plantilla(banban=0, bancue="")})
    with pytest.raises(ValueError, match="auxefp"):
        ejecutar(repo=repo)


def test_f015_r5_pago_sin_fuente_avisa_y_escribe_vacio() -> None:
    repo = RepositorioDoble(filas={
        ("dca", PLANTILLA_CABECERA): dca_plantilla(pagide=0, pagtex="", pagfor="", efeide=0),
    })
    respuesta, repo = ejecutar(repo=repo)
    assert [respuesta.filas["dca"][c] for c in GRUPO_PAGO] == [0, "", "", 0]
    assert _avisos(respuesta)[1] == (
        "cabecera_sin_dato",
        (
            "Ni el contrato, ni el albaran anterior, ni el proveedor traen pagide, pagtex, pagfor, "
            "efeide: se escriben vacias, como el alta a mano."
        ),
    )
    assert not any(t == "auxpag" for t, _ in _leidas_completas(repo))


def test_f015_r5_el_aviso_tambien_en_el_alta() -> None:
    respuesta, _ = ejecutar(repo=_sin_banco("CC"), commit=True)
    assert (respuesta.estado, [a.codigo for a in respuesta.avisos]) == (
        "creado", ["cabecera_sin_dato"])


# =====================================================================================
# T7 · R10: una columna que falta en una fila leída no construye nada
# =====================================================================================


@pytest.mark.parametrize(
    ("tabla", "ide", "columna"),
    [("prv", ENTIDE, "dir"), ("ctr", CTR, "dircon1"), ("dca", PLANTILLA_CABECERA, "eioide")],
)
@pytest.mark.parametrize("commit", [False, True])
def test_f015_r10_columna_ausente_falla_sin_escribir(
    tabla: str, ide: int, columna: str, commit: bool
) -> None:
    filas = {("prv", ENTIDE): prv(), ("ctr", CTR): ctr(), ("dca", PLANTILLA_CABECERA): dca_plantilla()}
    del filas[(tabla, ide)][columna]
    repo = RepositorioDoble(filas=filas)
    with pytest.raises(ValueError, match=columna):
        ejecutar(repo=repo, commit=commit)
    assert not any(t in ("peek", "transaccion") for t, _ in repo.llamadas)
    assert "partidas" not in repo.lecturas_hechas() and "tipmov" not in repo.lecturas_hechas()


# =====================================================================================
# T12 · R12, R14, R16-R20: la retención del contrato en el caso de uso
# =====================================================================================

#: El `ide` que el doble devuelve al mirar la siguiente `dcarec` (previa, R20).
PEEK_DCAREC = PEEK["dcarec"]


def ctrrec_fila(**valores: Any) -> tuple[Any, ...]:
    """Una fila de L16: el `ctrrec` de `RET5` (M11), en el orden de `L16_COLUMNAS`."""
    base = {
        "ide": 7001, "recide": 6005, "pos": 64, "valdef": 1, "valpor": 0.05, "valcan": 0.0,
        "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4705, "ivaide": 0, "tex": "RETENCION",
        "resalt": "", "item": 0, "cla": 5, "cod": "RET5  ", **valores,
    }
    return tuple(base[columna] for columna in L16_COLUMNAS)


def _con_retencion(*filas: tuple[Any, ...], **lecturas: Any) -> RepositorioDoble:
    return RepositorioDoble({"retenciones": list(filas or [ctrrec_fila()]), **lecturas})


#: `vinculada()`: 2 · 10,50 = 21,00 de base y 4,41 de IVA (21 %): totdoc 25,41.
#: RET5 (clase 5) sobre la base: 21,00 · 0,05 = 1,05; tot = 25,41 - 1,05 = 24,36.
_DCAREC_RET5 = {
    "ide": PEEK_DCAREC, "docide": PEEK["con"], "recide": 6005, "pos": 64, "bas": 21.0,
    "valdef": 1, "valpor": 0.05, "valcan": 0.0, "valmod": 0, "valfij": 0, "cuo": 1.05,
    "tex": "RETENCION", "reccla": 5, "cueide": 4705, "ivaide": 0, "ivacuo": 0, "reqcuo": 0,
    "refide": 0, "resalt": "", "frasupide": 0, "item": 0,
}


def test_f015_r12_con_contrato_l16_tras_conest_y_usuario() -> None:
    _respuesta, repo = ejecutar()
    hechas = repo.lecturas_hechas()
    assert hechas[hechas.index("usuario") + 1] == "retenciones"
    assert repo.parametros_de("retenciones") == [[CTR]]


def test_f015_r12_sin_contrato_no_se_lee_l16() -> None:
    respuesta, repo = _sin_contrato({"retenciones": [ctrrec_fila()]})
    assert "retenciones" not in repo.lecturas_hechas()
    assert respuesta.filas["dcarec"] == []


def test_f015_r12_contrato_con_ret5_escribe_una_dcarec() -> None:
    respuesta, repo = ejecutar(repo=_con_retencion())
    assert respuesta.filas["dcarec"] == [_DCAREC_RET5]
    dca = respuesta.filas["dca"]
    assert (dca["totbas"], dca["totdoc"], dca["tot"], dca["totpag"]) == (21.0, 25.41, 24.36, 24.36)
    assert ("peek", "dcarec") in repo.llamadas


def test_f015_r12_contrato_sin_ctrrec_ninguna_dcarec() -> None:
    respuesta, repo = ejecutar()
    assert respuesta.filas["dcarec"] == []
    assert (respuesta.filas["dca"]["tot"], respuesta.filas["dca"]["totdoc"]) == (25.41, 25.41)
    assert ("peek", "dcarec") not in repo.llamadas  # R20: sin `dcarec` no se mira


def test_f015_r12_en_devolucion_la_retencion_es_negativa() -> None:
    respuesta, _ = ejecutar([vinculada(cantidad=-2.0)], repo=_con_retencion())
    (dcarec,) = respuesta.filas["dcarec"]
    assert (dcarec["bas"], dcarec["cuo"]) == (-21.0, -1.05)
    assert respuesta.filas["dca"]["tot"] == -24.36


def test_f015_r12_un_albaran_ya_escrito_es_idempotente_aunque_su_retencion_no_valga() -> None:
    repo = _con_retencion(
        ctrrec_fila(), ctrrec_fila(ide=7002),
        referencia=[(2800001, "AC26/15000", 20261001, ENTIDE, OBRA, 21.0, 25.41, 24.36)],
    )
    respuesta, repo = ejecutar(repo=repo)
    assert respuesta.estado == "idempotente"
    assert "retenciones" not in repo.lecturas_hechas()


@pytest.mark.parametrize(
    ("filas", "motivo"),
    [
        ((ctrrec_fila(), ctrrec_fila(ide=7002, pos=128)), "2 recargos"),
        ((ctrrec_fila(cla=None, cod=None),), "no esta en dbo.rec"),
        ((ctrrec_fila(cla=1, cod="RETESP"),), "clase 1"),
        ((ctrrec_fila(valfij=1),), "valfij"),
        ((ctrrec_fila(ivaide=777740),), "ivaide"),
        ((ctrrec_fila(recide=0, cla=None, cod=None),), "sin recargo"),
    ],
    ids=["varias", "sin_rec", "clase_1", "valfij", "ivaide", "recide_0"],
)
@pytest.mark.parametrize("commit", [False, True])
def test_f015_r14_retencion_no_soportada_400_antes_de_las_lineas(
    filas: tuple, motivo: str, commit: bool
) -> None:
    repo = _con_retencion(*filas)
    with pytest.raises(AlbaranCompraError, match=motivo) as excinfo:
        ejecutar(repo=repo, commit=commit)
    assert excinfo.value.codigo == "retencion_no_soportada"
    assert "tipmov" not in repo.lecturas_hechas()
    assert not any(t in ("peek", "transaccion") for t, _ in repo.llamadas)
    assert not any(t == "auxpag" for t, _ in _leidas_completas(repo))


def test_f015_r16_aviso_de_la_retencion_en_la_previa() -> None:
    respuesta, _ = ejecutar(repo=_con_retencion())
    assert _avisos(respuesta)[1:] == [(
        "retencion_del_contrato",
        ("El contrato lleva el recargo RET5 (5 %): se retienen 1.05 sobre 21.00 y el neto "
         "(tot) es totdoc menos la retencion."),
    )]


def test_f015_r16_aviso_con_otro_porcentaje_y_tras_el_de_cabecera() -> None:
    repo = _con_retencion(ctrrec_fila(valpor=0.015, cla=4, cod="IRPF15"))
    repo.filas[("dca", PLANTILLA_CABECERA)] = dca_plantilla(pagide=0, pagtex="", pagfor="", efeide=0)
    respuesta, _ = ejecutar(repo=repo)
    assert [codigo for codigo, _ in _avisos(respuesta)] == [
        "cod_provisional", "cabecera_sin_dato", "retencion_del_contrato"]
    assert _avisos(respuesta)[2][1] == (
        "El contrato lleva el recargo IRPF15 (1.5 %): se retienen 0.38 sobre 25.41 y el neto "
        "(tot) es totdoc menos la retencion."
    )


def test_f015_r16_sin_retencion_no_hay_aviso() -> None:
    respuesta, _ = ejecutar()
    assert "retencion_del_contrato" not in [codigo for codigo, _ in _avisos(respuesta)]


def test_f015_r17_totales_con_retencion() -> None:
    respuesta, _ = ejecutar(repo=_con_retencion())
    assert respuesta.totales == {
        "totbas": 21.0, "totiva": 4.41, "totdoc": 25.41, "tot": 24.36, "retenciones": 1.05,
        "n_retenciones": 1, "n_lineas": 1, "n_vinculadas": 1, "n_movimientos": 1,
    }


def test_f015_r17_totales_sin_retencion() -> None:
    respuesta, _ = ejecutar()
    assert {k: respuesta.totales[k] for k in ("totdoc", "tot", "retenciones", "n_retenciones")} == {
        "totdoc": 25.41, "tot": 25.41, "retenciones": 0.0, "n_retenciones": 0}


def test_f015_r17_totales_en_el_alta_sin_retencion() -> None:
    respuesta, _ = ejecutar(commit=True)
    assert respuesta.estado == "creado"
    assert (respuesta.totales["tot"], respuesta.totales["retenciones"],
            respuesta.totales["n_retenciones"], respuesta.filas["dcarec"]) == (25.41, 0.0, 0, [])


@pytest.mark.parametrize(
    ("totdoc", "tot", "retenciones"), [(4568.11, 4379.34, 188.77), (25.41, 25.41, 0.0)]
)
def test_f015_r18_idempotente_tot_y_retenciones_del_albaran_existente(
    totdoc: float, tot: float, retenciones: float
) -> None:
    repo = RepositorioDoble({
        "referencia": [(2800001, "AC26/15000", 20261001, ENTIDE, OBRA, 3775.30, totdoc, tot)],
        "lineas_del_existente": [(64, 55, 2.0, 10.5, 21.0, 5, 70, "L1")],
    })
    respuesta, repo = ejecutar(repo=repo)
    assert respuesta.estado == "idempotente"
    assert respuesta.totales == {
        "totbas": 3775.30, "totdoc": totdoc, "tot": tot, "retenciones": retenciones,
        "n_lineas": 1,
    }
    assert "retenciones" not in repo.lecturas_hechas()  # sin leer su `dcarec` ni el `ctrrec`


_LOGGER = "application.use_cases.create_albaran_compra_use_case"


def _trazas(caplog: pytest.LogCaptureFixture, **kwargs: Any) -> tuple[Any, list[dict[str, Any]]]:
    repo = kwargs.pop("repo", None) or RepositorioDoble()
    # Reloj quieto: `duracion_ms` 0.0 no se confunde con un importe.
    caso = CreateAlbaranCompraUseCase(repo, SettingsDoble(), ahora_utc=lambda: AHORA,
                                      reloj=lambda: 100.0)
    with caplog.at_level(logging.DEBUG, logger=_LOGGER):
        try:
            resultado: Any = caso.run(peticion(None, **kwargs))
        except Exception as exc:  # noqa: BLE001 - el test mira la traza de cualquier fallo
            resultado = exc
    registros = [r for r in caplog.records if r.name == _LOGGER]
    return resultado, [json.loads(r.getMessage()) for r in registros]


def test_f015_r19_la_traza_cuenta_las_retenciones_sin_importes(
    caplog: pytest.LogCaptureFixture,
) -> None:
    respuesta, (traza,) = _trazas(caplog, repo=_con_retencion())
    assert respuesta.estado == "previsto"
    assert traza["n_retenciones"] == 1
    assert traza["codigos"][:2] == ["cod_provisional", "retencion_del_contrato"]
    for prohibido in ("1.05", "21.0", "0.05", "RET5", "PAGARE", "24.36", "RETENCION"):
        assert prohibido not in caplog.text, prohibido


def test_f015_r19_la_traza_sin_retencion_dice_0(caplog: pytest.LogCaptureFixture) -> None:
    _respuesta, (traza,) = _trazas(caplog, commit=True)
    assert traza["n_retenciones"] == 0


def test_f015_r19_la_traza_de_un_error_no_cuenta_retenciones(
    caplog: pytest.LogCaptureFixture,
) -> None:
    exc, (traza,) = _trazas(caplog, repo=_con_retencion(ctrrec_fila(), ctrrec_fila(ide=7002)))
    assert (type(exc), traza["codigo"]) == (AlbaranCompraError, "retencion_no_soportada")
    assert "n_retenciones" not in traza


def test_f015_r20_previa_numera_la_dcarec_con_peek_sin_reservar() -> None:
    respuesta, repo = ejecutar(repo=_con_retencion())
    assert [(d["ide"], d["docide"]) for d in respuesta.filas["dcarec"]] == [
        (PEEK_DCAREC, respuesta.con_ide)]
    assert "transaccion" not in [t for t, _ in repo.llamadas]


# =====================================================================================
# T13 · R21-R23: la `dcarec` en el commit
# =====================================================================================

#: `ide` que el doble reserva para la `dcarec` (E6b) y el de `con` (E3).
IDE_DCAREC = RESERVAS["ide_dcarec"][0]
IDE_CON = RESERVAS["ide_con"][0]


def test_f015_r21_con_retencion_e6b_tras_e6_e_insert_tras_los_mov() -> None:
    respuesta, repo = ejecutar(repo=_con_retencion(), commit=True)
    assert respuesta.estado == "creado"
    assert repo.sentencias() == [
        "referencia", "reservar_cod", "ide_con", "ide_dcapro", "ide_ctrprodes", "ide_mov",
        "ide_dcarec", "balance_bajo_bloqueo",
        "insert_con", "insert_dca", "insert_dcapro", "insert_ctrprodes", "insert_mov",
        "insert_dcarec",
        "servido", "sumas_contrato", "estados_contrato",
        "ide_log", "insert_log",
        "releer_con", "releer_dca", "releer_dcapro", "releer_mov", "releer_ctrprodes",
        "releer_dcarec", "releer_log",
    ]
    assert repo.transacciones[0]["applock_resources"] == list(APPLOCKS)


def test_f015_r21_lo_insertado_es_lo_que_se_devuelve() -> None:
    respuesta, repo = ejecutar(repo=_con_retencion(), commit=True)
    (dcarec,) = respuesta.filas["dcarec"]
    assert dcarec == {**_DCAREC_RET5, "ide": IDE_DCAREC, "docide": IDE_CON}
    assert repo.parametros_en_transaccion("insert_dcarec") == [list(dcarec.values())]
    assert repo.parametros_en_transaccion("releer_dcarec") == [[IDE_CON]]
    assert respuesta.filas["dca"]["tot"] == 24.36
    assert respuesta.totales["retenciones"] == 1.05 and respuesta.totales["n_retenciones"] == 1


def test_f015_r21_aviso_de_la_retencion_en_el_alta() -> None:
    respuesta, _ = ejecutar(repo=_con_retencion(), commit=True)
    assert [a.codigo for a in respuesta.avisos] == ["retencion_del_contrato"]


def test_f015_r21_sin_retencion_ni_reserva_ni_insert() -> None:
    respuesta, repo = ejecutar(commit=True)
    assert respuesta.estado == "creado"
    assert "ide_dcarec" not in repo.sentencias() and "insert_dcarec" not in repo.sentencias()
    assert repo.parametros_en_transaccion("releer_dcarec") == [[IDE_CON]]  # R23: se esperan 0
    assert repo.transacciones[0]["applock_resources"] == list(APPLOCKS)


def test_f015_r22_el_reintento_recalcula_el_ide_de_la_dcarec() -> None:
    repo = _con_retencion()
    repo.fallos["insert_dcarec"] = lambda intento: IntegrityError("2627") if intento == 1 else None
    repo.reservas["ide_dcarec"] = lambda intento, _p: (44100 + intento,)
    repo.reservas["ide_con"] = lambda intento, _p: (2900100 + intento,)
    respuesta, repo = ejecutar(repo=repo, commit=True)
    assert len(repo.cursores) == 2
    assert [p[:2] for p in repo.parametros_en_transaccion("insert_dcarec")] == [
        [44101, 2900101], [44102, 2900102]]
    assert [(d["ide"], d["docide"]) for d in respuesta.filas["dcarec"]] == [(44102, 2900102)]


@pytest.mark.parametrize(("retencion", "leidas"), [(True, 0), (True, 2), (False, 1)])
def test_f015_r23_relectura_de_dcarec_distinta_revierte(retencion: bool, leidas: int) -> None:
    repo = _con_retencion() if retencion else RepositorioDoble()
    repo.forzar["releer_dcarec"] = (leidas,)
    with pytest.raises(AlbaranCompraError, match="dcarec") as excinfo:
        ejecutar(repo=repo, commit=True)
    assert excinfo.value.codigo == "filas_afectadas_inesperadas"
    assert "releer_log" not in repo.sentencias()  # corta ahí: nada llega al COMMIT
