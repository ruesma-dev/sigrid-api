# tests/test_f008_transaccion.py
"""
F-008 T12-T14 · el trabajo de la transaccion de `sigrid/factura`: applocks en
orden, re-comprobacion bajo bloqueo (R14, R15, R22, R43), reserva, `INSERT`s,
marcas condicionadas (R40-R42), relectura antes del COMMIT (R45) y reintento
reentrante ante choque de clave (R37).

Repositorio y cursor dobles sobre el ERP de mentira de `tests/f008_dobles.py`:
una excepcion dentro de `work` devuelve el `Mundo` a su copia (ROLLBACK).
"""
from __future__ import annotations

from typing import Any

import pytest
from f008_dobles import (
    AHORA,
    Mundo,
    Repositorio,
    ajustes_de_escritura,
    con_transaccion,
    linea_gg,
    peticion,
)

from application.use_cases.create_factura_use_case import CreateFacturaUseCase
from application.use_cases.factura_statements import APPLOCKS_FACTURA
from domain.models.factura_models import FacturaError, FacturaRequest

_A_ORIGEN = {
    "origenes": ["PROF26/1"], "modo": "origen",
    "a_origen": [{"linea": 8101, "canoriori": 10.0, "imporiori": 100.0}],
    "total_base": 30.0, "total_iva": 6.3, "total_factura": 36.3,
    "vencimientos": [{"fecha": 20261130, "importe": 36.3}],
}
_FRGG_SIN_ORIGEN = {
    "serie": "FRGG", "origenes": [], "cod_obra": "GG", "lineas": [linea_gg()],
    "total_base": 100.0, "total_iva": 21.0, "total_factura": 121.0,
    "vencimientos": [{"fecha": 20261130, "importe": 121.0}],
}


def _repo() -> Repositorio:
    return con_transaccion(Repositorio())


def _commit(repo: Repositorio | None = None, **cambios: Any) -> tuple[dict[str, Any], Repositorio]:
    repo = repo or _repo()
    caso = CreateFacturaUseCase(repo, ajustes_de_escritura(), ahora_utc=lambda: AHORA)
    return caso.run(FacturaRequest.model_validate(peticion(commit=True, **cambios))), repo


def _error_commit(repo: Repositorio, **cambios: Any) -> FacturaError:
    with pytest.raises(FacturaError) as error:
        _commit(repo, **cambios)
    return error.value


def _nombres(repo: Repositorio) -> list[str]:
    return [nombre for nombre, _p in repo.sentencias]


def _intacto(repo: Repositorio) -> None:
    """ROLLBACK: nada insertado y los origenes como estaban."""
    limpio = Mundo()
    assert repo.mundo.insertadas == {}
    assert repo.mundo.dca == limpio.dca and repo.mundo.ctrpro == limpio.ctrpro
    assert [o["est"] for o in repo.mundo.origenes.values()] == [o["est"] for o in limpio.origenes.values()]
    assert [l["canfac"] for l in repo.mundo.lineas] == [l["canfac"] for l in limpio.lineas]


def _antes(repo: Repositorio, sentencia: str, que: Any) -> Repositorio:
    repo.mundo.antes_de[sentencia] = que
    return repo


# --------------------------------------------------------------------------- #
# T12 · applocks, re-comprobacion, reserva e INSERTs
# --------------------------------------------------------------------------- #


def test_f008_r36_r37_fr_de_mes_en_una_transaccion_con_sus_applocks() -> None:
    r, repo = _commit()
    assert r["estado"] == "creado" and r["committed"] is True and r["dry_run"] is False
    assert r["cod"] == "FR26/00042" and r["con_ide"] == 10000 and r["avisos"] == []
    (transaccion,) = repo.transacciones
    assert transaccion["applock_resources"] == list(APPLOCKS_FACTURA)
    assert transaccion["database"] == "ruesma" and transaccion["max_retries"] == 3
    filas = repo.mundo.insertadas
    assert {t: len(v) for t, v in filas.items()} == {
        "con": 2, "dcf": 1, "dcfpro": 1, "pag": 1, "consii": 1, "dcaprodes": 1, "log": 1,
    }
    factura, pago = filas["con"]
    assert (factura["ide"], factura["tip"], factura["cod"], factura["est"]) == (10000, 15, "FR26/00042", 1)
    assert (pago["ide"], pago["tip"], pago["cod"]) == (10001, 25, "FR26/00042_01")
    assert (filas["pag"][0]["ide"], filas["pag"][0]["conide"]) == (10001, 10000)
    assert filas["dcf"][0]["synckey"] == "FAC-1" and filas["dcfpro"][0]["docide"] == 10000
    dcaprodes = filas["dcaprodes"][0]
    assert (dcaprodes["docproide"], dcaprodes["docdeside"], dcaprodes["lindeside"]) == (8001, 10000, 20000)
    assert dcaprodes["docdescod"] == "FR26/00042"
    assert (filas["log"][0]["ide"], filas["log"][0]["cod"], filas["log"][0]["tip"]) == (600, "FR26/00042", 15)
    assert filas["consii"][0]["conide"] == 10000


def test_f008_r37_orden_de_las_sentencias() -> None:
    _r, repo = _commit()
    nombres = _nombres(repo)
    clave = [
        "referencia", "duplicadas", "bloquear_origenes", "asientos", "bloquear_lineas",
        "facturadas", "reservar_cod", "reservar_ide_con", "reservar_ide_dcfpro",
        "reservar_ide_consii", "reservar_ide_dcaprodes", "insertar_con", "insertar_dcf",
        "insertar_dcfpro", "insertar_pag", "insertar_consii", "insertar_dcaprodes", "marcar_linea",
        "marcar_cabecera", "marcar_estado", "reservar_ide_log", "insertar_log", "releer_con",
    ]
    posiciones = [nombres.index(n) for n in clave]
    assert posiciones == sorted(posiciones)
    assert "reservar_ide_dcfrec" not in nombres


def test_f008_r36_sin_origenes_ni_bloqueo_ni_marcas() -> None:
    r, repo = _commit(**_FRGG_SIN_ORIGEN)
    assert r["cod"] == "FRGG26/0008" and repo.mundo.insertadas["con"][0]["est"] == 20
    nombres = _nombres(repo)
    assert not [n for n in nombres if n.startswith(("bloquear_", "marcar_", "sumar_", "estfac_"))]
    assert "insertar_dcaprodes" not in nombres and "reservar_ide_dcaprodes" not in nombres
    _sin_marcas(repo)


def _sin_marcas(repo: Repositorio) -> None:
    limpio = Mundo()
    assert repo.mundo.dca == limpio.dca and repo.mundo.lineas == limpio.lineas


def test_f008_r36_frgg_con_albaran_con_marcas() -> None:
    r, repo = _commit(serie="FRGG")
    assert r["cod"] == "FRGG26/0008"
    assert {"marcar_linea", "marcar_cabecera", "marcar_estado"} <= set(_nombres(repo))
    assert repo.mundo.origenes[800]["est"] == 10


def test_f008_r31_retencion_inserta_su_dcfrec_y_el_pag_cla_2() -> None:
    repo = _repo()
    repo.mundo.retenciones.append({
        "docide": 800, "recide": 77, "pos": 64, "valdef": 0, "valpor": 0.05, "valcan": 0,
        "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4730, "ivaide": 0, "tex": "",
        "resalt": "", "item": 0,
    })
    _r, repo = _commit(repo, total_factura=23.2, vencimientos=[{"fecha": 20261130, "importe": 23.2}],
                       vencimiento_retencion=20271015)
    filas = repo.mundo.insertadas
    assert [(f["ide"], f["docide"], f["cuo"]) for f in filas["dcfrec"]] == [(300, 10000, 1.0)]
    assert [(p["cla"], p["ide"], p["retide"]) for p in filas["pag"]] == [(0, 10001, 0), (2, 10002, 77)]
    assert [c["cod"] for c in filas["con"]] == ["FR26/00042", "FR26/00042_01", "FR26/00042_02"]


def _factura(**cambios: Any) -> dict[str, Any]:
    base = {"ide": 7777, "cod": "FR26/00030", "entide": 500, "entref": "F-77", "totbas": 20.0,
            "totiva": 4.2, "totdoc": 24.2, "tot": 24.2, "est": 1, "synckey": "FAC-1",
            "entcif": "B00000001"}
    base.update(cambios)
    return base


def test_f008_r43_idempotente_bajo_el_applock() -> None:
    repo = _antes(_repo(), "referencia", lambda m: m.facturas.append(_factura()))
    r, repo = _commit(repo)
    assert r["estado"] == "idempotente" and r["cod"] == "FR26/00030"
    _intacto(repo)


def test_f008_r43_conflicto_y_duplicada_bajo_el_applock() -> None:
    repo = _antes(_repo(), "referencia", lambda m: m.facturas.append(_factura(entref="OTRA")))
    assert _error_commit(repo).codigo == "referencia_en_conflicto"
    _intacto(repo)
    repo = _antes(_repo(), "duplicadas", lambda m: m.facturas.append(_factura(synckey="OTRA")))
    assert _error_commit(repo).codigo == "factura_ya_registrada"
    _intacto(repo)


def test_f008_r14_origen_que_deja_de_estar_en_con_bajo_bloqueo() -> None:
    repo = _antes(_repo(), "bloquear_origenes", lambda m: m.origenes[800].update(est=10))
    assert _error_commit(repo).codigo == "origen_sin_contabilizar"
    repo = _antes(_repo(), "bloquear_origenes", lambda m: m.origenes.pop(800))
    assert _error_commit(repo).codigo == "origen_no_encontrado"


def test_f008_r15_linea_facturada_por_el_escritorio_bajo_bloqueo() -> None:
    repo = _antes(_repo(), "bloquear_lineas", lambda m: m.lineas[0].update(canfac=2.0))
    e = _error_commit(repo)
    assert e.codigo == "origen_ya_facturado" and e.details["lineas"] == [8001]
    _intacto_salvo_linea(repo)


def test_f008_r16b_origen_que_se_queda_sin_lineas_bajo_bloqueo() -> None:
    """R16b releido bajo `UPDLOCK`: la linea pasa a `can` 0 entre la previa y el bloqueo."""
    repo = _antes(_repo(), "bloquear_lineas", lambda m: m.lineas[0].update(can=0.0))
    e = _error_commit(repo)
    assert e.codigo == "origen_sin_lineas" and e.details["origenes"] == ["AC26/1"]
    _intacto(repo)
    assert repo.mundo.origenes[800]["est"] == 3


def test_f008_r16b_con_commit_no_se_escribe_nada() -> None:
    repo = _repo()
    repo.mundo.lineas[0].update(can=0.0)
    assert _error_commit(repo).codigo == "origen_sin_lineas"
    _intacto(repo)
    # Se rechaza antes de abrir la transaccion: ni bloqueos, ni reservas, ni marcas.
    assert not [n for n in _nombres(repo) if n.startswith(("bloquear", "reservar", "marcar", "sumar"))]


def _intacto_salvo_linea(repo: Repositorio) -> None:
    assert repo.mundo.insertadas == {} and repo.mundo.dca == Mundo().dca


def test_f008_r22_a_origen_releido_bajo_bloqueo() -> None:
    repo = _antes(_repo(), "bloquear_lineas", lambda m: m.lineas[3].update(imporiori=101.0))
    assert _error_commit(repo, **_A_ORIGEN).codigo == "a_origen_no_cuadra"
    assert repo.mundo.insertadas == {}


def test_f008_r30_totales_releidos_bajo_bloqueo() -> None:
    repo = _antes(_repo(), "bloquear_lineas", lambda m: m.lineas[0].update(tot=21.0))
    assert _error_commit(repo).codigo == "totales_no_cuadran"
    assert repo.mundo.insertadas == {}


# --------------------------------------------------------------------------- #
# T13 · marcas y su condicion de una fila
# --------------------------------------------------------------------------- #


def test_f008_r40_r41_marcas_de_un_albaran_de_mes() -> None:
    _r, repo = _commit()
    lineas = {l["ide"]: l["canfac"] for l in repo.mundo.lineas}
    assert lineas[8001] == 2.0 and lineas[8002] == 0.0
    assert repo.mundo.dca[800] == {"estfac": 1, "fecfac": 20261030, "horfac": 100000, "antestfac": 3}
    assert repo.mundo.origenes[800]["est"] == 10
    assert repo.mundo.dca[801]["estfac"] == 0 and repo.mundo.origenes[801]["est"] == 3
    assert "sumar_contrato" not in _nombres(repo)


def test_f008_r42_linea_vinculada_suma_al_ctrpro_y_refresca_el_ctr() -> None:
    _r, repo = _commit(**_A_ORIGEN)
    assert repo.mundo.ctrpro[9901]["canfac"] == 10.0
    # Σcan 15, Σcanfac 10: no esta todo facturado.
    assert repo.mundo.ctr[900]["estfac"] == 0
    assert ("estfac_contrato", [0, 900]) in repo.sentencias
    repo = _repo()
    del repo.mundo.ctrpro[9902]
    _r, repo = _commit(repo, **_A_ORIGEN)
    assert repo.mundo.ctr[900]["estfac"] == 1


def test_f008_r40_carrera_en_la_marca_de_linea_revierte_todo() -> None:
    repo = _antes(_repo(), "marcar_linea", lambda m: m.lineas[0].update(canfac=1.0))
    e = _error_commit(repo)
    assert e.codigo == "origen_ya_facturado"
    _intacto_salvo_linea(repo)
    assert repo.mundo.origenes[800]["est"] == 3


@pytest.mark.parametrize("sentencia,cambio", [
    ("marcar_estado", lambda m: m.origenes[800].update(est=1)),
    ("marcar_cabecera", lambda m: m.dca[800].update(estfac=1)),
    # El escritorio factura 1 mas en el ctrpro entre el bloqueo y la suma.
    ("sumar_contrato", lambda m: m.ctrpro[9901].update(canfac=8.0)),
])
def test_f008_r41_r42_marca_que_no_cuadra_revierte_todo(sentencia: str, cambio: Any) -> None:
    repo = _antes(_repo(), sentencia, cambio)
    cambios = _A_ORIGEN if sentencia == "sumar_contrato" else {}
    e = _error_commit(repo, **cambios)
    assert e.codigo == "filas_afectadas_inesperadas"
    assert repo.mundo.insertadas == {}


# --------------------------------------------------------------------------- #
# T14 · relectura y reintento reentrante
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("sentencia,tabla", [
    ("releer_dcfpro", "dcfpro"), ("releer_pagos", "pag"), ("releer_dcaprodes", "dcaprodes"),
    ("releer_consii", "consii"), ("releer_log", "log"), ("releer_dcf", "dcf"),
])
def test_f008_r45_relectura_que_no_cuadra_revierte(sentencia: str, tabla: str) -> None:
    repo = _antes(_repo(), sentencia, lambda m: m.insertadas[tabla].pop())
    e = _error_commit(repo)
    assert e.codigo == "filas_afectadas_inesperadas"
    _intacto(repo)


def test_f008_r37_choque_de_clave_se_reintenta_desde_cero() -> None:
    repo = _repo()
    repo.mundo.colisiones = 2
    r, repo = _commit(repo)
    assert repo.intentos == 3 and r["cod"] == "FR26/00042"
    assert len(repo.mundo.insertadas["con"]) == 2 and len(repo.mundo.insertadas["dcfpro"]) == 1
    assert repo.mundo.insertadas["dcfpro"][0]["ide"] == 20000
    assert repo.mundo.lineas[0]["canfac"] == 2.0


def test_f008_r37_choques_agotados_dan_colision_de_clave() -> None:
    repo = _repo()
    repo.mundo.colisiones = 4
    e = _error_commit(repo)
    assert e.codigo == "colision_de_clave" and repo.intentos == 4
    _intacto(repo)


def test_f008_r37_reserva_tras_otra_factura_de_la_serie() -> None:
    repo = _repo()
    _commit(repo)
    r, repo = _commit(repo, referencia_externa="FAC-2", numero_factura="F-78",
                      origenes=["AC26/2"], total_base=5.0, total_iva=1.05, total_factura=6.05,
                      vencimientos=[{"fecha": 20261130, "importe": 6.05}])
    assert r["cod"] == "FR26/00043" and r["con_ide"] == 10002
    assert [f["ide"] for f in repo.mundo.insertadas["dcfpro"]] == [20000, 20001]
    assert [f["ide"] for f in repo.mundo.insertadas["log"]] == [600, 601]


def test_f008_r43_la_misma_peticion_otra_vez_es_idempotente() -> None:
    r1, repo = _commit()
    r2, repo = _commit(repo)
    assert r2["estado"] == "idempotente" and (r2["cod"], r2["con_ide"]) == (r1["cod"], r1["con_ide"])
    assert len(repo.mundo.insertadas["dcf"]) == 1


def test_f008_r16_solo_lineas_con_can_distinta_de_cero() -> None:
    """R16: AC26/1 tiene 8001 (`can` 2) y 8002 (`can` 0). Solo pasa la primera; la de
    `can` 0 no entra en `dcfpro` ni en `dcaprodes` y su `canfac` sigue a 0."""
    r, repo = _commit()
    assert [f["linoriide"] for f in r["filas"]["dcfpro"]] == [8001]
    assert [f["docproide"] for f in repo.mundo.insertadas["dcaprodes"]] == [8001]
    canfac = {l["ide"]: l["canfac"] for l in repo.mundo.lineas}
    assert (canfac[8001], canfac[8002]) == (2.0, 0.0)
