# tests/test_f018_proforma.py
"""
F-018 · T9 y T11: la proforma hereda la vinculada con el dto del contrato
(R21, R22; P8 = (a), design D10 y §La proforma).

Sin tocar `f007_dobles.py` ni `f016_dobles.py`: subclases aquí de
`RepositorioProforma` y `RepositorioOrigen` cuya línea de contrato 262990
(F09 de la hoja de CTSB26/0472) tiene `tar` 4,278, `can` 36, `tot` 92,40 y
`pre` 92,4/36, en la fila completa y en LP4, con dto `40%` o, de control,
sin dto. La hoja lleva F09 a 12,5 uds al precio del contrato: 32,08 en la
hoja y 32,09 en Sigrid (D9). Todo lo demás debe salir igual que el control.

Sin red y sin base de datos.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from f007_dobles import DATOS, RepositorioProforma, SettingsProforma, peticion
from f009_dobles import AHORA
from f016_dobles import PUNTA, RepositorioOrigen

from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.proforma_models import ProformaRequest

HOJA = DATOS["hojas"]["CTSB26/0472"]
F09 = 262990
_LP4 = ("ide", "docide", "paride", "partida", "can", "pre", "tot", "unimed", "proide", "producto")
_CTRPRO_F09 = {"pre": 92.4 / 36, "tar": 4.278, "can": 36.0, "tot": 92.4}
_CLAVES = {"dto", "precio_bruto"}


def _parchear(repo: Any, dto: str) -> Any:
    """La 262990 con el `tar`/`dto` del caso, en la fila completa y en LP4."""
    repo.ctrpro_filas = [
        {**fila, **_CTRPRO_F09, "dto": dto} if fila["ide"] == F09 else fila
        for fila in repo.ctrpro_filas
    ]
    lp4 = repo.lecturas["lp4_lineas"]

    def lp4_parcheada(params: list[Any]) -> list[tuple[Any, ...]]:
        filas = []
        for fila in lp4(params):
            datos = dict(zip(_LP4, fila, strict=True))
            if datos["ide"] == F09:
                datos.update(can=36.0, pre=92.4 / 36, tot=92.4)
            filas.append(tuple(datos[c] for c in _LP4))
        return filas

    repo.lecturas["lp4_lineas"] = lp4_parcheada
    return repo


class RepositorioProformaConDto(RepositorioProforma):
    def __init__(self, dto: str = "40%", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        _parchear(self, dto)


class RepositorioOrigenConDto(RepositorioOrigen):
    def __init__(self, dto: str = "40%", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        _parchear(self, dto)


def _lineas(**f09: Any) -> list[dict[str, Any]]:
    primera = {**HOJA["lineas"][0], "cantidad": 12.5, "precio": 92.4 / 36,
               "cantidad_anterior": 241, "cantidad_origen": 253.5, **f09}
    return [primera, *HOJA["lineas"][1:]]


#: 17.024,28 de la hoja menos F09 (620 · 11 = 6.820) más 12,5 · 2,5666… = 32,08.
_IMPORTE_MES = round(17024.28 - 6820 + 32.08, 2)


def hoja_de_mes(**cambios: Any) -> dict[str, Any]:
    return peticion(**{"lineas": _lineas(), "importe_mes": _IMPORTE_MES,
                       "importe_origen": round(2651 + _IMPORTE_MES, 2), "otra_del_mes": True,
                       **cambios})


def hoja_a_origen(**cambios: Any) -> dict[str, Any]:
    """Encadenada a la punta de F-016: F09 continúa la 1400001 (`canoriori` 241)."""
    return hoja_de_mes(**{"modo": "origen", "proforma_anterior": PUNTA,
                          "lineas": _lineas(linea_anterior=1400001), **cambios})


def ejecutar(cuerpo: dict[str, Any], repo: Any) -> Any:
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    return caso.run(ProformaRequest(**cuerpo))


def _con_y_control(cuerpo: dict[str, Any], clase: type) -> tuple[Any, Any]:
    return ejecutar(cuerpo, clase("40%")), ejecutar(cuerpo, clase(""))


def _codigos(respuesta: Any) -> tuple[list[str], list[list[str]]]:
    return ([a.codigo for a in respuesta.avisos],
            [[a.codigo for a in linea.avisos] for linea in respuesta.lineas])


# =====================================================================================
# R21 · de mes
# =====================================================================================


def test_f018_r21_proforma_de_mes_con_el_dto_del_contrato() -> None:
    con, control = _con_y_control(hoja_de_mes(), RepositorioProformaConDto)
    assert con.estado == control.estado == "previsto"
    fila, fila_control = con.filas["dcapro"][0], control.filas["dcapro"][0]
    assert (fila["tar"], fila["dto"], fila["tot"], fila["ivacuo"]) == (4.278, "40%", 32.09, 6.74)
    assert fila["pre"] == 32.09 / 12.5
    assert (fila_control["tot"], fila_control["dto"], fila_control["pre"]) == (32.08, "", 92.4 / 36)
    # Solo cambian las columnas de la línea (R26).
    cambian = {"tot", "pre", "ivacuo", "dto"}
    assert {c: v for c, v in fila.items() if c not in cambian} == {
        c: v for c, v in fila_control.items() if c not in cambian}
    assert con.filas["dcapro"][1:] == control.filas["dcapro"][1:]


def test_f018_r21_cabecera_de_mes_con_impbru_y_totales_de_las_filas() -> None:
    con, control = _con_y_control(hoja_de_mes(), RepositorioProformaConDto)
    dca, dca_control = con.filas["dca"], control.filas["dca"]
    assert dca["totbas"] == round(dca_control["totbas"] + 0.01, 2)
    assert dca["impbru"] == round(dca_control["totbas"] - 32.08 + 53.48, 2)  # 12,5·4,278 = 53,475
    assert dca_control["impbru"] == dca_control["totbas"]
    assert dca["impnet"] == dca["totbas"]
    assert con.totales["totbas"] == dca["totbas"]
    assert dca["cla"] == dca_control["cla"] == 141


def test_f018_r21_respuesta_de_mes_con_dto_y_precio_bruto() -> None:
    con, control = _con_y_control(hoja_de_mes(), RepositorioProformaConDto)
    volcado = con.model_dump(mode="json")["lineas"]
    assert (volcado[0]["dto"], volcado[0]["precio_bruto"], volcado[0]["total"]) == (40.0, 4.278, 32.09)
    assert volcado[0]["precio"] == 32.09 / 12.5
    assert all(not _CLAVES & set(linea) for linea in volcado[1:])
    assert all(not _CLAVES & set(l) for l in control.model_dump(mode="json")["lineas"])


def test_f018_r22_de_mes_origen_y_avisos_como_sin_dto() -> None:
    con, control = _con_y_control(hoja_de_mes(), RepositorioProformaConDto)
    assert con.origen == control.origen
    assert _codigos(con) == _codigos(control)
    assert [l.cantidad_anterior_sigrid for l in con.lineas] == [
        l.cantidad_anterior_sigrid for l in control.lineas]


# =====================================================================================
# R21, R22 · a origen
# =====================================================================================


def test_f018_r21_a_origen_importe_origen_cadena_con_el_pre_neto() -> None:
    con, control = _con_y_control(hoja_a_origen(), RepositorioOrigenConDto)
    assert con.estado == control.estado == "previsto"
    fila = con.filas["dcapro"][0]
    assert (fila["canoriori"], fila["canorilin"], fila["tot"]) == (253.5, 1400001, 32.09)
    # Σ round(canoriori·pre, 2): solo cambia el término de F09.
    delta = round(253.5 * (32.09 / 12.5), 2) - round(253.5 * (92.4 / 36), 2)
    assert con.cadena.importe_origen_cadena == pytest.approx(
        control.cadena.importe_origen_cadena + delta, abs=1e-9)
    assert delta != 0


def test_f018_r22_a_origen_lo_demas_de_la_cadena_igual() -> None:
    con, control = _con_y_control(hoja_a_origen(), RepositorioOrigenConDto)
    assert con.cadena.importe_anterior_cadena == control.cadena.importe_anterior_cadena
    assert con.cadena.n_arrastradas == control.cadena.n_arrastradas > 0
    assert con.cadena.anterior == control.cadena.anterior
    for linea, linea_control in zip(con.lineas, control.lineas, strict=True):
        assert (linea.cantidad_anterior_cadena, linea.cantidad_origen_cadena, linea.arrastrada,
                linea.linea_anterior) == (
            linea_control.cantidad_anterior_cadena, linea_control.cantidad_origen_cadena,
            linea_control.arrastrada, linea_control.linea_anterior)
    pedidas = len(hoja_a_origen()["lineas"])
    # Las arrastradas: misma fila y misma línea de respuesta, sin `dto`/`precio_bruto`.
    assert con.filas["dcapro"][pedidas:] == control.filas["dcapro"][pedidas:]
    arrastradas = con.model_dump(mode="json")["lineas"][pedidas:]
    assert arrastradas == control.model_dump(mode="json")["lineas"][pedidas:]
    assert all(not _CLAVES & set(l) for l in arrastradas)
    assert _codigos(con) == _codigos(control)


def test_f018_r21_a_origen_respuesta_con_dto() -> None:
    con, _control = _con_y_control(hoja_a_origen(), RepositorioOrigenConDto)
    primera = con.model_dump(mode="json")["lineas"][0]
    assert (primera["dto"], primera["precio_bruto"], primera["cantidad_origen_cadena"]) == (
        40.0, 4.278, 253.5)


# =====================================================================================
# R22 · `existente`, `idempotente` y la traza, sin cambios
# =====================================================================================


def test_f018_r22_existente_sin_las_claves() -> None:
    respuesta = ejecutar(peticion(), RepositorioProformaConDto())
    assert respuesta.estado == "existente"
    assert all(not _CLAVES & set(l) for l in respuesta.model_dump(mode="json")["lineas"])


def test_f018_r22_idempotente_sin_las_claves() -> None:
    from test_f007_use_case import _L11, CTR_0472, SM1004

    repo = RepositorioProformaConDto(lecturas={
        "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)],
        "referencia": [_L11],
        "lineas_del_existente": [(64, SM1004, 12.5, 32.09 / 12.5, 32.09, 355001, 70, "F09")],
    })
    respuesta = ejecutar(hoja_de_mes(), repo)
    assert respuesta.estado == "idempotente"
    assert all(not _CLAVES & set(l) for l in respuesta.model_dump(mode="json")["lineas"])


def test_f018_r22_traza_de_proforma_sin_n_lineas_con_dto(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        ejecutar(hoja_de_mes(), RepositorioProformaConDto())
    (mensaje,) = [r.getMessage() for r in caplog.records if '"sigrid/proforma"' in r.getMessage()]
    assert "n_lineas_con_dto" not in json.loads(mensaje)


# =====================================================================================
# T11 · R24: el commit de la proforma con el dto del contrato
# =====================================================================================


def test_f018_r24_commit_de_proforma_de_mes_con_el_dto_del_contrato() -> None:
    from application.use_cases.albaran_compra_statements import APPLOCKS, DCA_COLUMNAS

    repo = RepositorioProformaConDto()
    respuesta = ejecutar(hoja_de_mes(commit=True), repo)
    assert (respuesta.estado, respuesta.committed) == ("creado", True)
    assert repo.transacciones[0]["applock_resources"] == list(APPLOCKS)
    insertadas = repo.parametros_en_transaccion("insert_dcapro")
    assert insertadas == [list(f.values()) for f in respuesta.filas["dcapro"]]
    assert (respuesta.filas["dcapro"][0]["tot"], respuesta.filas["dcapro"][0]["dto"]) == (32.09, "40%")
    (dca,) = repo.parametros_en_transaccion("insert_dca")
    assert dca[DCA_COLUMNAS.index("impbru")] == respuesta.filas["dca"]["impbru"]
    assert dca[DCA_COLUMNAS.index("impbru")] != dca[DCA_COLUMNAS.index("totbas")]
    assert "releer_dcapro" in repo.sentencias()
    assert respuesta.model_dump(mode="json")["lineas"][0]["dto"] == 40.0


def test_f018_r24_commit_de_proforma_a_origen_con_el_dto_del_contrato() -> None:
    repo = RepositorioOrigenConDto()
    respuesta = ejecutar(hoja_a_origen(commit=True), repo)
    assert respuesta.estado == "creado"
    insertadas = repo.parametros_en_transaccion("insert_dcapro")
    assert insertadas == [list(f.values()) for f in respuesta.filas["dcapro"]]
    fila = respuesta.filas["dcapro"][0]
    assert (fila["tot"], fila["canoriori"], fila["canorilin"]) == (32.09, 253.5, 1400001)
