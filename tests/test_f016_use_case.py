# tests/test_f016_use_case.py
"""
F-016 T8 · R1, R5-R16, R19, R21: el caso de uso de `sigrid/proforma` a origen,
con el doble de F-007 extendido (`tests/f016_dobles.py`): la hoja de agosto de
CTSB26/0472 (obra 0719) sobre la cadena sintetica de `f016_cadena.json`.

En mes, nada cambia (los tests de F-007, sin tocar, fijan el resto). A origen,
la previa de una primera y de una encadenada (continuadas, arrastradas,
columnas a origen y `cadena`), la ya registrada, las validaciones de la
anterior y de las lineas, el tope, los avisos y la traza. Sin red ni base.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from f007_dobles import DATOS, RepositorioProforma, SettingsProforma, peticion
from f009_dobles import AHORA
from f016_dobles import (
    CTR_0472,
    DE_MES,
    DOCUMENTOS,
    IDE_PUNTA,
    PRIMERA,
    PUNTA,
    RepositorioOrigen,
    fila_lp1,
    fila_lp7,
)

from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.albaran_compra_models import AlbaranCompraError
from domain.models.proforma_models import ProformaRequest, ProformaResponse
from domain.models.proforma_origen_models import (
    AnteriorCadena,
    CadenaProforma,
    LineaProformaOrigenResultado,
    ProformaOrigenError,
    ProformaOrigenResponse,
)

HOJA = DATOS["hojas"]["CTSB26/0472"]
#: Lo que lee F-007 antes del nucleo con contrato (la previa, sin la del mes).
LECTURAS_F007 = ["obra", "lp5_referencia", "lp3_contratos", "lp4_lineas", "lp1_proformas",
                 "lp2_anterior"]
LECTURAS_EXISTENTE = [*LECTURAS_F007, "lp6_lineas"]
#: F09 -> 1400001, F21 -> 1400005 y F23 (sin vincular) -> 1400003; las demas, nuevas.
CONTINUAN = {"F09": 1400001, "F21": 1400005, "F23": 1400003}


def lineas(continuan: dict[str, int] | None = None) -> list[dict[str, Any]]:
    continuan = CONTINUAN if continuan is None else continuan
    return [
        {**l, "linea_anterior": continuan[l["referencia_linea"]]}
        if l["referencia_linea"] in continuan else dict(l)
        for l in HOJA["lineas"]
    ]


def encadenada(**cambios: Any) -> dict[str, Any]:
    return peticion(**{"modo": "origen", "proforma_anterior": PUNTA, "lineas": lineas(),
                       **cambios})


def primera(**cambios: Any) -> dict[str, Any]:
    return peticion(**{"modo": "origen", "primera_de_cadena": True, **cambios})


def ejecutar(
    cuerpo: dict[str, Any],
    *,
    repo: RepositorioProforma | None = None,
    settings: SettingsProforma | None = None,
) -> tuple[Any, RepositorioProforma]:
    repo = repo or RepositorioOrigen()
    caso = CreateProformaUseCase(repo, settings or SettingsProforma(), ahora_utc=lambda: AHORA)
    return caso.run(ProformaRequest(**cuerpo)), repo


def fallo(cuerpo: dict[str, Any], **kwargs: Any) -> AlbaranCompraError:
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(cuerpo, **kwargs)
    return excinfo.value


def codigos(avisos: list[Any]) -> list[str]:
    return [a.codigo for a in avisos]


# =====================================================================================
# R1 · en mes, F-007 exacta
# =====================================================================================


@pytest.mark.parametrize("cambios", [{}, {"otra_del_mes": True}, {"modo": "mes"}],
                         ids=["existente", "previa", "modo_mes"])
def test_f016_r1_en_mes_con_la_0719_ni_lp7_ni_lp8_ni_lp9_ni_claves_nuevas(
    cambios: dict[str, Any],
) -> None:
    """El doble de F-007 no conoce LP7-LP9: si se leyeran, el test fallaria."""
    respuesta, repo = ejecutar(peticion(**cambios), repo=RepositorioProforma())
    assert type(respuesta) is ProformaResponse
    assert "cadena" not in respuesta.model_dump(mode="json")
    assert not {"lp7_anterior", "lp8_sucesoras", "lp9_lineas"} & set(repo.lecturas_hechas())


def test_f016_r1_en_mes_sobre_la_cadena_sigue_siendo_de_mes() -> None:
    respuesta, repo = ejecutar(peticion())
    assert type(respuesta) is ProformaResponse and respuesta.estado == "previsto"
    assert repo.lecturas_hechas()[:6] == LECTURAS_F007
    assert not {"lp7_anterior", "lp8_sucesoras", "lp9_lineas"} & set(repo.lecturas_hechas())
    assert (respuesta.cabecera["docoritip"], respuesta.cabecera["docoriide"]) == (0, 0)
    assert len(respuesta.filas["dcapro"]) == 6
    assert "contrato_a_origen" in codigos(respuesta.avisos)


# =====================================================================================
# R8, R11, R13, R19 · previa de una primera de cadena
# =====================================================================================


def test_f016_r8_r13_previa_de_una_primera() -> None:
    respuesta, repo = ejecutar(primera())
    assert type(respuesta) is ProformaOrigenResponse
    assert (respuesta.estado, respuesta.committed, respuesta.dry_run) == ("previsto", False, True)
    assert not {"lp7_anterior", "lp8_sucesoras", "lp9_lineas"} & set(repo.lecturas_hechas())
    assert repo.transacciones == []
    assert (respuesta.cabecera["docoritip"], respuesta.cabecera["docoriide"],
            respuesta.cabecera["cla"]) == (1, 0, 141)
    dcapro = respuesta.filas["dcapro"]
    assert [f["canoriori"] for f in dcapro] == [f["can"] for f in dcapro]
    assert [f["can"] for f in dcapro] == [l["cantidad"] for l in HOJA["lineas"]]
    assert {(f["canorilin"], f["canoriant"], f["imporiant"]) for f in dcapro} == {(0, 0, 0)}
    assert respuesta.cadena == CadenaProforma(
        anterior=None, primera_de_cadena=True, importe_anterior_cadena=0.0,
        importe_origen_cadena=17024.28, n_arrastradas=0,
    )
    assert all(type(l) is LineaProformaOrigenResultado for l in respuesta.lineas)
    assert [(l.linea_anterior, l.arrastrada, l.cantidad_anterior_cadena, l.cantidad_origen_cadena)
            for l in respuesta.lineas] == [
        (None, False, 0.0, l["cantidad"]) for l in HOJA["lineas"]]


# =====================================================================================
# R9, R11, R12, R13, R19 · previa de una encadenada
# =====================================================================================


def test_f016_r11_r12_previa_encadenada_lee_y_escribe_la_cadena() -> None:
    respuesta, repo = ejecutar(encadenada())
    de_mes, repo_mes = ejecutar(peticion())
    hechas = repo.lecturas_hechas()
    assert hechas == [*LECTURAS_F007, "lp7_anterior", "lp8_sucesoras", "lp9_lineas",
                      *repo_mes.lecturas_hechas()[6:]]
    assert repo.parametros_de("lp7_anterior") == [[14, CTR_0472, PUNTA]]
    assert repo.parametros_de("lp8_sucesoras") == [[14, CTR_0472, IDE_PUNTA]]
    assert repo.parametros_de("lp9_lineas") == [[IDE_PUNTA]]
    assert repo.transacciones == []
    assert (respuesta.cabecera["docoritip"], respuesta.cabecera["docoriide"]) == (1, IDE_PUNTA)

    dcapro = respuesta.filas["dcapro"]
    assert len(dcapro) == 8 and respuesta.totales["n_lineas"] == 8
    assert [f["canorilin"] for f in dcapro] == [1400001, 0, 0, 0, 1400005, 1400003,
                                                1400002, 1400004]
    assert [f["canoriori"] for f in dcapro] == [861.0, 117.5, 38.57, 261.4335, 53.0, 105.85,
                                                50.0, 10.0]
    assert [f["can"] for f in dcapro][6:] == [0.0, 0.0]
    assert [f["pos"] for f in dcapro] == [64 * i for i in range(1, 9)]
    assert [f["ide"] for f in dcapro] == [8000001 + i for i in range(8)]
    assert {f["docide"] for f in dcapro} == {respuesta.con_ide}
    assert [f["refent"] for f in dcapro][6:] == ["F13", "F09B"]
    # Sin `ctrprodes` ni `mov` de mas: las arrastradas solo son `dcapro` (D6).
    assert (respuesta.totales["n_vinculadas"], respuesta.totales["n_movimientos"]) == (5, 0)
    assert len(respuesta.filas["ctrprodes"]) == 5
    # Los totales son los del MES, como en F-007.
    assert {k: respuesta.totales[k] for k in ("totbas", "totdoc", "tot")} == {
        k: de_mes.totales[k] for k in ("totbas", "totdoc", "tot")}
    assert respuesta.totales["totbas"] == 17024.28

    assert respuesta.cadena == CadenaProforma(
        anterior=AnteriorCadena(cod=PUNTA, ide=IDE_PUNTA), primera_de_cadena=False,
        importe_anterior_cadena=3521.0, importe_origen_cadena=20545.28, n_arrastradas=2,
    )
    resumen = [(l.indice, l.referencia_linea, l.linea_anterior, l.arrastrada,
                l.cantidad_anterior_cadena, l.cantidad_origen_cadena)
               for l in respuesta.lineas]
    assert resumen == [
        (0, "F09", 1400001, False, 241.0, 861.0), (1, "F11", None, False, 0.0, 117.5),
        (2, "F15", None, False, 0.0, 38.57), (3, "F16", None, False, 0.0, 261.4335),
        (4, "F21", 1400005, False, 5.0, 53.0), (5, "F23", 1400003, False, 30.0, 105.85),
        (6, "F13", 1400002, True, 50.0, 50.0), (7, "F09B", 1400004, True, 10.0, 10.0),
    ]


def test_f016_r19_las_arrastradas_en_la_respuesta() -> None:
    respuesta, _repo = ejecutar(encadenada())
    arrastrada = respuesta.lineas[6]
    assert (arrastrada.tipo, arrastrada.ctrpro_ide, arrastrada.linoriide, arrastrada.proide,
            arrastrada.de_contrato, arrastrada.cantidad, arrastrada.precio, arrastrada.total,
            arrastrada.iva_cuota) == ("vinculada", 262994, 262994, 610004, True, 0.0, 11.0, 0.0, 0.0)
    assert (arrastrada.almide, arrastrada.cenide, arrastrada.paride, arrastrada.res,
            arrastrada.unimed) == (70, 80, 355001, "VERTIDO HORMIGON ZAPATAS", "M3")
    assert (arrastrada.cantidad_anterior_sigrid, arrastrada.avisos, arrastrada.producto) == (
        None, [], None)


def test_f016_r19_arrastrada_sin_vincular() -> None:
    continuan = {"F09": 1400001, "F21": 1400005}
    respuesta, _repo = ejecutar(encadenada(lineas=lineas(continuan)))
    assert [l.referencia_linea for l in respuesta.lineas if l.arrastrada] == ["F13", "F23", "F09B"]
    sin_vincular = respuesta.lineas[7]
    assert (sin_vincular.tipo, sin_vincular.ctrpro_ide, sin_vincular.de_contrato,
            sin_vincular.linea_anterior) == ("sin_vincular", 0, False, 1400003)
    assert respuesta.cadena.n_arrastradas == 3


def test_f016_r15_r16_avisos_de_f007_iguales_y_sin_contrato_a_origen() -> None:
    respuesta, _repo = ejecutar(encadenada())
    de_mes, _r = ejecutar(peticion())
    assert codigos(respuesta.avisos) == [c for c in codigos(de_mes.avisos)
                                         if c != "contrato_a_origen"]
    assert "anterior_distinto_de_sigrid" in codigos(respuesta.avisos)
    assert respuesta.origen == de_mes.origen
    assert [codigos(l.avisos) for l in respuesta.lineas[:6]] == [
        codigos(l.avisos) for l in de_mes.lineas]
    assert [l.cantidad_anterior_sigrid for l in respuesta.lineas[:6]] == [
        l.cantidad_anterior_sigrid for l in de_mes.lineas]
    assert respuesta.warnings == [a.mensaje for a in respuesta.avisos] + [
        a.mensaje for l in respuesta.lineas for a in l.avisos]


def test_f016_r15_sin_importes_ni_cantidades_de_la_hoja_no_hay_cuadre_ni_error() -> None:
    sin = [{k: v for k, v in l.items() if k not in ("cantidad_anterior", "cantidad_origen")}
           for l in lineas()]
    respuesta, _repo = ejecutar(encadenada(lineas=sin, importe_anterior=None,
                                           importe_origen=None))
    assert respuesta.estado == "previsto"
    assert "anterior_distinto_de_sigrid" not in codigos(respuesta.avisos)
    assert all("anterior_distinto_de_sigrid" not in codigos(l.avisos) for l in respuesta.lineas)


def test_f016_r15_el_cuadre_de_la_hoja_sigue_valiendo_a_origen() -> None:
    error = fallo(encadenada(importe_mes=1.0))
    assert error.codigo == "importe_mes_no_cuadra"


# =====================================================================================
# R10 · aviso de integridad de las nuevas
# =====================================================================================


def test_f016_r10_nueva_con_su_ctrpro_en_la_anterior_avisa_y_arrastra_la_vieja() -> None:
    respuesta, _repo = ejecutar(encadenada(lineas=lineas({"F21": 1400005, "F23": 1400003})))
    (aviso,) = [a for a in respuesta.lineas[0].avisos if a.codigo == "linea_nueva_ya_en_la_anterior"]
    assert aviso.lineas_anterior == [1400001, 1400004]
    assert all("linea_nueva_ya_en_la_anterior" not in codigos(l.avisos)
               for l in respuesta.lineas[1:])
    assert [l.linea_anterior for l in respuesta.lineas if l.arrastrada] == [
        1400001, 1400002, 1400004]
    assert respuesta.lineas[0].cantidad_origen_cadena == 620.0
    assert aviso.mensaje in respuesta.warnings


# =====================================================================================
# R5 · ya registrada a origen
# =====================================================================================

_AGOSTO = (2860001, "PROF26/00401", 20260831, "PROF0826_0719", 17024.28, 1)


def test_f016_r5_existente_antes_de_validar_la_anterior() -> None:
    """La hoja ya registrada como sucesora de la punta: `existente`, no
    `anterior_con_sucesora` (D8), y sin leer LP7-LP9."""
    repo = RepositorioOrigen({
        "lp1_proformas": [*(fila_lp1(c) for c in DOCUMENTOS), _AGOSTO],
        "lp8_sucesoras": [(2860001, "PROF26/00401")],
        "lp6_lineas": [(1700001, 262990, "SM1004", 620.0, 11.0, 6820.0)],
    })
    respuesta, repo = ejecutar(encadenada(), repo=repo)
    assert type(respuesta) is ProformaOrigenResponse
    assert (respuesta.estado, respuesta.cod, respuesta.con_ide, respuesta.cadena) == (
        "existente", "PROF26/00401", 2860001, None)
    assert repo.lecturas_hechas() == LECTURAS_EXISTENTE
    (linea,) = respuesta.lineas
    assert (linea.dcapro_ide, linea.arrastrada, linea.linea_anterior,
            linea.cantidad_origen_cadena) == (1700001, None, None, None)
    assert "contrato_a_origen" not in codigos(respuesta.avisos)


def test_f016_r5_a_origen_del_mes_con_otro_total_avisa_y_sigue() -> None:
    otra = (*_AGOSTO[:4], 99.0, 1)
    repo = RepositorioOrigen({"lp1_proformas": [*(fila_lp1(c) for c in DOCUMENTOS), otra]})
    respuesta, _repo = ejecutar(encadenada(), repo=repo)
    assert respuesta.estado == "previsto"
    assert "otra_del_mes" in codigos(respuesta.avisos)


def test_f016_r5_de_mes_del_mes_con_otro_total_es_el_error_de_f007() -> None:
    de_mes = (*_AGOSTO[:4], 99.0, 0)
    repo = RepositorioOrigen({"lp1_proformas": [*(fila_lp1(c) for c in DOCUMENTOS), de_mes]})
    error = fallo(encadenada(), repo=repo)
    assert error.codigo == "proforma_del_mes_existente"
    assert "lp7_anterior" not in repo.lecturas_hechas()


def test_f016_r23_idempotente_a_origen_sin_cadena() -> None:
    l11 = (2900011, "PROF26/01282", 20260831, 77, 7190, 17024.28, 17024.28, 17024.28)
    repo = RepositorioOrigen({
        "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)],
        "referencia": [l11],
        "lineas_del_existente": [(64, 610004, 620.0, 11.0, 6820.0, 355001, 70, "F09")],
    })
    respuesta, repo = ejecutar(encadenada(), repo=repo)
    assert type(respuesta) is ProformaOrigenResponse
    assert (respuesta.estado, respuesta.cadena) == ("idempotente", None)
    assert (respuesta.lineas[0].arrastrada, respuesta.lineas[0].linea_anterior) == (None, None)
    assert "lp7_anterior" not in repo.lecturas_hechas()


# =====================================================================================
# R6, R7 · la anterior
# =====================================================================================


@pytest.mark.parametrize(
    ("anterior", "lp7"),
    [("PROF26/09999", None), (DE_MES, None), (PUNTA, [fila_lp7(PUNTA, fec=20260901)])],
    ids=["no_existe", "de_mes", "posterior"],
)
def test_f016_r6_anterior_no_valida_sin_seguir(anterior: str, lp7: Any) -> None:
    repo = RepositorioOrigen({"lp7_anterior": lp7} if lp7 else None)
    error = fallo(encadenada(proforma_anterior=anterior), repo=repo)
    assert type(error) is ProformaOrigenError and error.codigo == "anterior_no_valida"
    assert repo.lecturas_hechas() == [*LECTURAS_F007, "lp7_anterior"]
    assert repo.transacciones == []


def test_f016_r6_la_fecha_es_la_de_la_proforma() -> None:
    """Con `fecha_proforma` el 15 de agosto, una anterior del 20 es posterior."""
    repo = RepositorioOrigen({"lp7_anterior": [fila_lp7(PUNTA, fec=20260820)]})
    error = fallo(encadenada(fecha_proforma=20260815), repo=repo)
    assert error.codigo == "anterior_no_valida"
    respuesta, _repo = ejecutar(encadenada(fecha_proforma=20260820), repo=RepositorioOrigen(
        {"lp7_anterior": [fila_lp7(PUNTA, fec=20260820)]}))
    assert respuesta.estado == "previsto"


def test_f016_r7_anterior_con_sucesora() -> None:
    repo = RepositorioOrigen()
    error = fallo(encadenada(proforma_anterior=PRIMERA, lineas=lineas({})), repo=repo)
    assert type(error) is ProformaOrigenError and error.codigo == "anterior_con_sucesora"
    assert PUNTA in str(error)
    assert repo.lecturas_hechas() == [*LECTURAS_F007, "lp7_anterior", "lp8_sucesoras"]
    assert repo.parametros_de("lp8_sucesoras") == [[14, CTR_0472, DOCUMENTOS[PRIMERA]["ide"]]]


# =====================================================================================
# R9 · lineas no validas, con las de la etapa 1
# =====================================================================================


def test_f016_r9_los_fallos_de_r9_y_de_la_etapa_1_juntos() -> None:
    hoja = lineas({"F21": 1400003, "F23": 1400003})
    hoja = [*hoja[:5], {**hoja[5], "linea_anterior": 1400099}]
    hoja[0] = {**hoja[0], "ctrpro_ide": 271001}
    repo = RepositorioOrigen()
    error = fallo(encadenada(lineas=hoja), repo=repo)
    assert error.codigo == "lineas_no_validas"
    assert [(f.indice, f.codigo) for f in error.lineas] == [
        (0, "linea_no_es_del_contrato"), (4, "linea_anterior_no_valida"),
        (5, "linea_anterior_no_valida")]
    assert "3 linea(s)" in str(error)
    assert repo.lecturas_hechas() == [*LECTURAS_F007, "lp7_anterior", "lp8_sucesoras",
                                      "lp9_lineas"]


def test_f016_r9_en_primera_los_fallos_de_la_etapa_1_tras_la_ya_registrada() -> None:
    hoja = [{**HOJA["lineas"][0], "ctrpro_ide": 271001}, *HOJA["lineas"][1:]]
    repo = RepositorioOrigen()
    error = fallo(primera(lineas=hoja), repo=repo)
    assert error.codigo == "lineas_no_validas"
    assert [(f.indice, f.codigo) for f in error.lineas] == [(0, "linea_no_es_del_contrato")]
    assert repo.lecturas_hechas() == LECTURAS_F007


# =====================================================================================
# R14 · el tope cuenta las arrastradas
# =====================================================================================


def test_f016_r14_tope_con_las_arrastradas_aun_en_previa() -> None:
    error = fallo(encadenada(), settings=SettingsProforma(sigrid_proforma_max_lineas=7))
    assert error.codigo == "demasiadas_lineas"
    assert "6 lineas y 2 arrastradas" in str(error) and "7" in str(error)
    respuesta, _repo = ejecutar(encadenada(),
                                settings=SettingsProforma(sigrid_proforma_max_lineas=8))
    assert respuesta.estado == "previsto"


# =====================================================================================
# R21 · traza
# =====================================================================================


def _traza(caplog: pytest.LogCaptureFixture) -> tuple[dict[str, Any], str]:
    mensajes = [r.getMessage() for r in caplog.records if '"sigrid/proforma"' in r.getMessage()]
    assert len(mensajes) == 1
    return json.loads(mensajes[0]), mensajes[0]


def _sin_datos_sensibles(texto: str) -> None:
    for prohibido in ("HORMIGONES", "B00000472", "17024", "6820", "VERTIDO", "BERENJENO",
                      "prueba", "2651", "3521", "20545", "ZAPATAS"):
        assert prohibido not in texto, prohibido


def test_f016_r21_traza_de_una_encadenada(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        ejecutar(encadenada())
    traza, texto = _traza(caplog)
    assert {k: traza[k] for k in ("modo", "primera_de_cadena", "anterior", "n_continuadas",
                                  "n_arrastradas", "estado")} == {
        "modo": "origen", "primera_de_cadena": False, "anterior": PUNTA, "n_continuadas": 3,
        "n_arrastradas": 2, "estado": "previsto"}
    _sin_datos_sensibles(texto)


def test_f016_r21_traza_de_una_primera(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        ejecutar(primera())
    traza, texto = _traza(caplog)
    assert {k: traza[k] for k in ("modo", "primera_de_cadena", "anterior", "n_continuadas",
                                  "n_arrastradas")} == {
        "modo": "origen", "primera_de_cadena": True, "anterior": None, "n_continuadas": 0,
        "n_arrastradas": 0}
    _sin_datos_sensibles(texto)


def test_f016_r21_traza_de_un_error_de_la_cadena(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO), pytest.raises(ProformaOrigenError):
        ejecutar(encadenada(proforma_anterior=PRIMERA, lineas=lineas({})))
    traza, texto = _traza(caplog)
    assert (traza["resultado"], traza["codigo"], traza["modo"], traza["anterior"],
            traza["n_arrastradas"]) == ("error", "anterior_con_sucesora", "origen", PRIMERA, None)
    _sin_datos_sensibles(texto)


def test_f016_r21_en_mes_la_traza_no_cambia(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        ejecutar(peticion())
    traza, _texto = _traza(caplog)
    assert not {"modo", "primera_de_cadena", "anterior", "n_continuadas", "n_arrastradas"} & set(
        traza)


def test_f016_t8_los_datos_de_la_fixture_son_coherentes() -> None:
    """La punta cuelga de la primera y la de mes no es de la cadena (M44)."""
    assert DOCUMENTOS[PUNTA]["docoriide"] == DOCUMENTOS[PRIMERA]["ide"]
    assert DOCUMENTOS[DE_MES]["docoritip"] == 0
