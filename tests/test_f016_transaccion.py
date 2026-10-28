# tests/test_f016_transaccion.py
"""
F-016 T10 · R17, R18: la transaccion de la proforma a origen es la de F-007
(nucleo de F-009 con F-015: sentencias, applocks y relecturas) con las
`dcapro` arrastradas en el mismo `INSERT` y, bajo el applock de referencias,
tras LP1 (R28 con R5), LP8 otra vez: si entre la previa y el commit alguien ha
encadenado otra a la misma anterior, `anterior_con_sucesora` sin escribir.

Doble de `tests/f016_dobles.py` (la 0719 con la cadena sintetica). Sin red ni
base de datos.
"""
from __future__ import annotations

from typing import Any

import pytest
from f007_dobles import DATOS, SettingsProforma, peticion
from f009_dobles import AHORA, IntegrityError, _columnas_del_insert
from f016_dobles import CTR_0472, DOCUMENTOS, IDE_PUNTA, PUNTA, RepositorioOrigen, fila_lp1

from application.use_cases.albaran_compra_statements import APPLOCKS, DCA_COLUMNAS
from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.albaran_compra_models import AlbaranCompraError
from domain.models.proforma_models import ProformaError, ProformaRequest
from domain.models.proforma_origen_models import ProformaOrigenError, ProformaOrigenResponse

HOJA = DATOS["hojas"]["CTSB26/0472"]
CONTINUAN = {"F09": 1400001, "F21": 1400005, "F23": 1400003}
LP1_FUERA = [fila_lp1(cod) for cod in DOCUMENTOS]
_AGOSTO = (2860001, "PROF26/00401", 20260831, "PROF0826_0719", 17024.28, 1)


def lineas() -> list[dict[str, Any]]:
    return [{**l, "linea_anterior": CONTINUAN[l["referencia_linea"]]}
            if l["referencia_linea"] in CONTINUAN else dict(l) for l in HOJA["lineas"]]


def ejecutar(repo: RepositorioOrigen, **cambios: Any) -> Any:
    cuerpo = peticion(**{"modo": "origen", "proforma_anterior": PUNTA, "lineas": lineas(),
                         "commit": True, **cambios})
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    return caso.run(ProformaRequest(**cuerpo))


def insertadas(repo: RepositorioOrigen, intento: int = 1) -> list[dict[str, Any]]:
    """Las `dcapro` del `INSERT` de un intento, como diccionarios."""
    return [dict(zip(_columnas_del_insert(sql), params, strict=True))
            for i, clave, sql, params in repo.en_transaccion
            if i == intento and clave == "insert_dcapro"]


#: El orden de F-009 con F-015 (sin retencion ni `mov`), LP1 tras E1 (F-007 R28),
#: LP8 tras LP1 (R17) y las 6 `dcapro` de la peticion mas las 2 arrastradas (R18).
ORDEN_DEL_INTENTO = [
    "referencia", "lp1_proformas", "lp8_sucesoras", "reservar_cod", "ide_con", "ide_dcapro",
    "ide_ctrprodes", "insert_con", "insert_dca", *["insert_dcapro"] * 8,
    *["insert_ctrprodes"] * 5, *["servido"] * 5, "sumas_contrato", "estados_contrato",
    "ide_log", "insert_log", "releer_con", "releer_dca", "releer_dcapro", "releer_mov",
    "releer_ctrprodes", "releer_dcarec", "releer_log",
]


def test_f016_r18_orden_de_las_sentencias_y_applocks_de_f015() -> None:
    repo = RepositorioOrigen()
    respuesta = ejecutar(repo)
    assert type(respuesta) is ProformaOrigenResponse
    assert (respuesta.estado, respuesta.committed, respuesta.cod) == ("creado", True, "PROF26/01282")
    assert repo.sentencias() == ORDEN_DEL_INTENTO
    assert [t["applock_resources"] for t in repo.transacciones] == [list(APPLOCKS)]
    assert respuesta.cadena.n_arrastradas == 2 and len(respuesta.lineas) == 8


def test_f016_r17_lp8_por_el_cursor_tras_lp1() -> None:
    repo = RepositorioOrigen()
    ejecutar(repo)
    assert repo.parametros_en_transaccion("lp8_sucesoras") == [[14, CTR_0472, IDE_PUNTA]]
    assert repo.parametros_en_transaccion("lp1_proformas") == [
        [14, CTR_0472, "PROF%", "PROF%", "PREV%"]]


def test_f016_r17_sucesora_aparecida_dentro_no_escribe() -> None:
    repo = RepositorioOrigen(filas_en_transaccion={"lp8_sucesoras": [(2860009, "PROF26/00999")]})
    with pytest.raises(ProformaOrigenError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "anterior_con_sucesora"
    assert "PROF26/00999" in str(excinfo.value)
    assert repo.sentencias() == ["referencia", "lp1_proformas", "lp8_sucesoras"]


def test_f016_r17_a_origen_del_mes_con_otro_total_aparecida_dentro_sigue() -> None:
    otra = (*_AGOSTO[:4], 99.0, 1)
    repo = RepositorioOrigen(filas_en_transaccion={"lp1_proformas": [*LP1_FUERA, otra]})
    respuesta = ejecutar(repo)
    assert (respuesta.estado, respuesta.committed) == ("creado", True)
    assert repo.sentencias() == ORDEN_DEL_INTENTO


def test_f016_r17_la_del_mes_con_el_mismo_total_aparecida_dentro_es_existente() -> None:
    repo = RepositorioOrigen(
        {"lp6_lineas": [(1700001, 262990, "SM1004", 620.0, 11.0, 6820.0)]},
        filas_en_transaccion={"lp1_proformas": [*LP1_FUERA, _AGOSTO]},
    )
    respuesta = ejecutar(repo)
    assert type(respuesta) is ProformaOrigenResponse
    assert (respuesta.estado, respuesta.cod, respuesta.committed, respuesta.cadena) == (
        "existente", "PROF26/00401", False, None)
    assert repo.sentencias() == ["referencia", "lp1_proformas"]


def test_f016_r17_de_mes_del_mes_con_otro_total_aparecida_dentro_es_el_error_de_f007() -> None:
    de_mes = (*_AGOSTO[:4], 99.0, 0)
    repo = RepositorioOrigen(filas_en_transaccion={"lp1_proformas": [*LP1_FUERA, de_mes]})
    with pytest.raises(ProformaError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "proforma_del_mes_existente"
    assert repo.sentencias() == ["referencia", "lp1_proformas"]


def test_f016_r17_en_primera_sin_lp8() -> None:
    repo = RepositorioOrigen()
    respuesta = ejecutar(repo, proforma_anterior=None, primera_de_cadena=True,
                         lineas=HOJA["lineas"])
    assert respuesta.estado == "creado"
    assert "lp8_sucesoras" not in repo.sentencias()
    assert repo.sentencias()[:3] == ["referencia", "lp1_proformas", "reservar_cod"]
    assert [f["canoriori"] for f in insertadas(repo)] == [l["cantidad"] for l in HOJA["lineas"]]


def test_f016_r17_la_misma_referencia_dentro_es_idempotente_sin_lp8() -> None:
    l11 = (2900011, "PROF26/01282", 20260831, 77, 7190, 17024.28, 17024.28, 17024.28)
    repo = RepositorioOrigen(filas_en_transaccion={
        "referencia": [l11], "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)],
        "lineas_del_existente": [(64, 610004, 620.0, 11.0, 6820.0, 355001, 70, "F09")],
    })
    respuesta = ejecutar(repo)
    assert (respuesta.estado, respuesta.cadena) == ("idempotente", None)
    assert "lp8_sucesoras" not in repo.sentencias()


def test_f016_r18_insert_de_las_arrastradas_y_relectura_con_todas() -> None:
    repo = RepositorioOrigen()
    ejecutar(repo)
    filas = insertadas(repo)
    assert len(filas) == 8
    assert [f["ide"] for f in filas] == [8000011 + i for i in range(8)]
    assert {f["docide"] for f in filas} == {2900011}
    arrastradas = filas[6:]
    assert [(f["canorilin"], f["can"], f["tot"], f["pos"], f["refent"]) for f in arrastradas] == [
        (1400002, 0.0, 0.0, 448, "F13"), (1400004, 0.0, 0.0, 512, "F09B")]
    assert [f["canoriori"] for f in filas] == [861.0, 117.5, 38.57, 261.4335, 53.0, 105.85,
                                              50.0, 10.0]
    (dca,) = [dict(zip(DCA_COLUMNAS, p, strict=True))
              for _i, c, _sql, p in repo.en_transaccion if c == "insert_dca"]
    assert (dca["docoritip"], dca["docoriide"], dca["cla"]) == (1, IDE_PUNTA, 141)
    assert repo.cursores[0].insertadas["dcapro"] == 8


def test_f016_r18_relectura_que_no_cuenta_las_arrastradas_revierte() -> None:
    repo = RepositorioOrigen(forzar={"releer_dcapro": (6,)})
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "filas_afectadas_inesperadas"
    assert "8 filas de dcapro" in str(excinfo.value)


def test_f016_r18_ni_update_ni_ctrprodes_ni_mov_por_las_arrastradas() -> None:
    repo = RepositorioOrigen()
    ejecutar(repo)
    assert [p[1] for p in repo.parametros_en_transaccion("servido")] == [
        262990, 262992, 262996, 262997, 263002]
    assert repo.sentencias().count("insert_ctrprodes") == 5
    assert "insert_mov" not in repo.sentencias() and "ide_mov" not in repo.sentencias()
    assert repo.sentencias().count("estados_contrato") == 1


def test_f016_r18_reintento_reentrante_con_las_mismas_filas() -> None:
    repo = RepositorioOrigen(fallos={
        "insert_log": lambda intento: IntegrityError("clave repetida") if intento == 1 else None,
    })
    respuesta = ejecutar(repo)
    assert respuesta.estado == "creado"
    assert len(repo.cursores) == 2
    assert repo.sentencias(2) == ORDEN_DEL_INTENTO
    assert insertadas(repo, 2) == insertadas(repo, 1)
    assert len(insertadas(repo, 2)) == 8
