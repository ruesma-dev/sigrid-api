# tests/test_f015_use_case.py
"""
F-015 · el caso de uso del modo extendido de `sigrid/albaran`
(`application/use_cases/create_albaran_compra_use_case.py`) con la cabecera por
lista blanca (O1) y la retención del contrato (O2).

Sin red y sin base de datos: los dobles de `f009_dobles.py`, que reconocen cada
sentencia por su SQL exacto. Datos sintéticos.
"""
from __future__ import annotations

from typing import Any

import pytest
from f009_dobles import (
    AHORA,
    AUXPAG_PRV,
    CTR,
    ENTIDE,
    PLANTILLA_CABECERA,
    RepositorioDoble,
    SettingsDoble,
    ctr,
    dca_plantilla,
    prv,
)

from application.use_cases.albaran_compra_statements import GRUPO_BANCO, GRUPO_PAGO
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
