# tests/test_f018_use_case.py
"""
F-018 · T8 y T11: el descuento por línea en el caso de uso del modo extendido
de `sigrid/albaran`.

T8: R1, R6, R8-R18 y R20 en previa, con el doble de F-009 sin modificarlo
(`f009_dobles.py`) y `ctrpro` propios con dto en el formato de Sigrid. T11:
R23 y R24 (commit, applocks, reintento y relecturas; SQL igual que en `dev`).

Sin red y sin base de datos.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest
from f009_dobles import RepositorioDoble, ctrpro
from pydantic import ValidationError
from test_f009_use_case import (
    _EXISTENTE,
    _LINEAS_EXISTENTE,
    avisos,
    dcapro,
    ejecutar,
    fallos,
    sin_vincular,
    trazar,
    vinculada,
)
from test_f015_use_case import ctrrec_fila

from domain.models.proforma_models import ProformaRequest


def con_9001(**cambios: Any) -> RepositorioDoble:
    """El doble de F-009 con la línea de contrato 9001 cambiada (sin tocar el doble)."""
    lineas = ctrpro()
    return RepositorioDoble(ctrpro_filas=[{**lineas[0], **cambios}, *lineas[1:]])


#: D9: `tar` 4,278 al 40 % con 36 uds: `tot` 92,40 y `pre` = 92,4/36 (coherente).
_CTRPRO_40 = {"pre": 92.4 / 36, "tar": 4.278, "dto": "40%", "can": 36.0, "tot": 92.4}

_CLAVES = ("dto", "precio_bruto")


def _volcado(linea: Any) -> dict[str, Any]:
    return linea.model_dump(mode="json")


# =====================================================================================
# R1, R8, R9, R16 · sin vincular con dto
# =====================================================================================


def test_f018_r1_previa_sin_vincular_con_dto() -> None:
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)])
    fila = dcapro(respuesta)
    assert (fila["tar"], fila["dto"], fila["tot"], fila["ivacuo"]) == (18.625, "40%", 11.18, 2.35)
    assert fila["pre"] == 11.18 / 1.0
    assert (respuesta.totales["totbas"], respuesta.totales["totiva"], respuesta.totales["totdoc"]) == (
        11.18, 2.35, 13.53)


def test_f018_r8_cabecera_con_impbru_bruto() -> None:
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)])
    dca = respuesta.filas["dca"]
    assert dca["impbru"] == 18.63  # round(1·18,625, 2)
    assert (dca["impnet"], dca["totbas"], dca["totiva"], dca["totdoc"]) == (11.18, 11.18, 2.35, 13.53)
    assert (dca["tot"], dca["totpag"], dca["impdes"]) == (13.53, 13.53, 0)


def test_f018_r9_mov_y_pmp_con_el_neto() -> None:
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)])
    mov = respuesta.filas["mov"][0]  # MA9999 (66) tiene `tipmov` 1; balance (4, 2)
    assert (mov["pre"], mov["prc"], mov["canent"]) == (11.18, 11.18, 1.0)
    assert mov["almpma"] == (4.0 * 2.0 + 1.0 * 11.18) / 5.0
    assert mov["prepma"] == 2.0 == dcapro(respuesta)["prepma"]
    assert respuesta.lineas[0].pmp_resultante == mov["almpma"]


def test_f018_r16_linea_de_respuesta_con_dto_y_precio_bruto() -> None:
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)])
    linea = _volcado(respuesta.lineas[0])
    assert (linea["precio"], linea["total"], linea["iva_cuota"]) == (11.18, 11.18, 2.35)
    assert (linea["dto"], linea["precio_bruto"]) == (40.0, 18.625)


def test_f018_r1_devolucion_con_dto() -> None:
    respuesta, _ = ejecutar([sin_vincular(cantidad=-0.4, precio=1275.68, dto=2.5)])
    fila = dcapro(respuesta)
    assert (fila["can"], fila["tar"], fila["dto"], fila["tot"], fila["ivacuo"]) == (
        -0.4, 1275.68, "2,5%", -497.52, -104.48)
    assert respuesta.filas["dca"]["impbru"] == -510.27
    assert respuesta.filas["mov"][0]["pre"] == -497.52 / -0.4
    assert _volcado(respuesta.lineas[0])["dto"] == 2.5


def test_f018_r8_mezcla_con_y_sin_dto() -> None:
    respuesta, _ = ejecutar([
        sin_vincular("L1", cantidad=1.0, precio=18.625, dto=40.0),
        sin_vincular("L2"),  # 3 · 2,675 = 8,025 -> 8,03 (sin descuento)
    ])
    dca = respuesta.filas["dca"]
    assert dca["impbru"] == 26.66  # 18,63 + 8,03: el bruto de una y el `tot` de la otra
    assert dca["totbas"] == 19.21
    con, sin = (_volcado(linea) for linea in respuesta.lineas)
    assert (con["dto"], con["precio_bruto"]) == (40.0, 18.625)
    assert not set(_CLAVES) & set(sin)
    assert dcapro(respuesta, 1)["dto"] == ""


def test_f018_r7_dto_0_es_sin_descuento() -> None:
    con_cero, _ = ejecutar([sin_vincular(dto=0)])
    sin, _ = ejecutar([sin_vincular()])
    assert con_cero.model_dump(mode="json") == sin.model_dump(mode="json")


# =====================================================================================
# R11-R13 · vinculadas con dto: validar, no pisar
# =====================================================================================


def test_f018_r11_vinculada_con_dto_como_el_contrato_sin_avisos() -> None:
    repo = con_9001(tar=12.0, dto="40%")
    respuesta, _ = ejecutar([vinculada(precio=12.0, dto=40.0)], repo=repo)
    fila = dcapro(respuesta)
    assert (fila["tar"], fila["dto"], fila["tot"]) == (12.0, "40%", 14.4)
    assert fila["pre"] == 14.4 / 2.0
    assert not {"precio_distinto_del_contrato", "dto_distinto_del_contrato"} & set(
        avisos(respuesta.lineas[0]))
    assert respuesta.filas["dca"]["impbru"] == 24.0
    assert respuesta.filas["mov"][0]["pre"] == 7.2
    assert (_volcado(respuesta.lineas[0])["dto"], respuesta.lineas[0].precio_bruto) == (40.0, 12.0)


def test_f018_r12_otro_bruto_avisa_del_precio() -> None:
    respuesta, _ = ejecutar([vinculada(precio=13.0, dto=40.0)], repo=con_9001(tar=12.0, dto="40%"))
    linea = respuesta.lineas[0]
    assert "precio_distinto_del_contrato" in avisos(linea)
    assert "dto_distinto_del_contrato" not in avisos(linea)
    mensaje = next(a.mensaje for a in linea.avisos if a.codigo == "precio_distinto_del_contrato")
    assert "bruto" in mensaje
    assert (dcapro(respuesta)["tar"], dcapro(respuesta)["tot"]) == (13.0, 15.6)  # lo pedido


def test_f018_r12_tolerancia_del_bruto() -> None:
    respuesta, _ = ejecutar([vinculada(precio=12.0001, dto=40.0)], repo=con_9001(tar=12.0, dto="40%"))
    assert "precio_distinto_del_contrato" not in avisos(respuesta.lineas[0])
    respuesta, _ = ejecutar([vinculada(precio=12.00011, dto=40.0)], repo=con_9001(tar=12.0, dto="40%"))
    assert "precio_distinto_del_contrato" in avisos(respuesta.lineas[0])


def test_f018_r13_otro_dto_avisa_con_los_dos_porcentajes() -> None:
    respuesta, _ = ejecutar([vinculada(precio=12.0, dto=30.0)], repo=con_9001(tar=12.0, dto="40%"))
    linea = respuesta.lineas[0]
    assert "dto_distinto_del_contrato" in avisos(linea)
    assert "precio_distinto_del_contrato" not in avisos(linea)
    mensaje = next(a.mensaje for a in linea.avisos if a.codigo == "dto_distinto_del_contrato")
    assert "30%" in mensaje and "40%" in mensaje
    assert (dcapro(respuesta)["dto"], dcapro(respuesta)["tot"]) == ("30%", 16.8)


def test_f018_r13_los_dos_avisos_a_la_vez_en_orden() -> None:
    respuesta, _ = ejecutar([vinculada(precio=13.0, dto=30.0)], repo=con_9001(tar=12.0, dto="40%"))
    codigos = avisos(respuesta.lineas[0])
    assert codigos.index("precio_distinto_del_contrato") + 1 == codigos.index(
        "dto_distinto_del_contrato")


def test_f018_r13_ctrpro_sin_dto_cuenta_como_0() -> None:
    respuesta, _ = ejecutar([vinculada(precio=12.0, dto=40.0)], repo=con_9001(tar=12.0, dto=""))
    linea = respuesta.lineas[0]
    mensaje = next(a.mensaje for a in linea.avisos if a.codigo == "dto_distinto_del_contrato")
    assert "40%" in mensaje and "0%" in mensaje


def test_f018_r13_ctrpro_con_dto_no_legible_avisa_con_mensaje_propio() -> None:
    respuesta, _ = ejecutar([vinculada(precio=12.0, dto=40.0)])  # 9001: `10+2,5`
    linea = respuesta.lineas[0]
    mensaje = next(a.mensaje for a in linea.avisos if a.codigo == "dto_distinto_del_contrato")
    assert "10+2,5" in mensaje and "no se puede leer" in mensaje
    assert dcapro(respuesta)["dto"] == "40%"


def test_f018_r13_mismo_dto_con_otra_escritura() -> None:
    respuesta, _ = ejecutar([vinculada(precio=12.0, dto=1.5)], repo=con_9001(tar=12.0, dto=" 1,5% "))
    assert "dto_distinto_del_contrato" not in avisos(respuesta.lineas[0])


def test_f018_r12_sin_dto_el_aviso_de_precio_es_el_de_hoy() -> None:
    """Sin `dto`, `precio_distinto_del_contrato` sigue comparando con `ctrpro.pre`
    (opción C), no con `tar`."""
    respuesta, _ = ejecutar([vinculada(precio=12.0)], repo=con_9001(tar=12.0, dto="40%"))
    assert "precio_distinto_del_contrato" in avisos(respuesta.lineas[0])  # pre 10,5
    assert "dto_distinto_del_contrato" not in avisos(respuesta.lineas[0])


# =====================================================================================
# R15 · vinculada sin dto que casa con un `ctrpro` con dto (P5)
# =====================================================================================


def test_f018_r15_vinculada_sin_dto_con_ctrpro_con_dto() -> None:
    respuesta, _ = ejecutar([vinculada(cantidad=12.5, precio=92.4 / 36)], repo=con_9001(**_CTRPRO_40))
    fila = dcapro(respuesta)
    assert (fila["tar"], fila["dto"], fila["tot"], fila["ivacuo"]) == (4.278, "40%", 32.09, 6.74)
    assert fila["pre"] == 32.09 / 12.5
    assert respuesta.filas["dca"]["impbru"] == 53.48  # round(12,5·4,278, 2) = 53,475 -> 53,48
    assert respuesta.totales["totbas"] == 32.09
    assert respuesta.filas["mov"][0]["pre"] == 32.09 / 12.5
    assert respuesta.filas["ctrprodes"][0]["can"] == 12.5
    linea = _volcado(respuesta.lineas[0])
    assert (linea["dto"], linea["precio_bruto"], linea["precio"], linea["total"]) == (
        40.0, 4.278, 32.09 / 12.5, 32.09)
    assert not {"precio_distinto_del_contrato", "dto_distinto_del_contrato"} & set(
        avisos(respuesta.lineas[0]))


@pytest.mark.parametrize("dto", ["10+2,5", "5", ""])
def test_f018_r15_ctrpro_no_legible_o_sin_dto_es_la_opcion_c_de_hoy(dto: str) -> None:
    respuesta, _ = ejecutar([vinculada(cantidad=12.5, precio=92.4 / 36)],
                            repo=con_9001(**{**_CTRPRO_40, "dto": dto}))
    assert dcapro(respuesta)["tot"] == 32.08
    assert respuesta.filas["dca"]["impbru"] == respuesta.filas["dca"]["totbas"] == 32.08
    assert not set(_CLAVES) & set(_volcado(respuesta.lineas[0]))


def test_f018_r15_ctrpro_con_tar_0_es_la_opcion_c_de_hoy() -> None:
    respuesta, _ = ejecutar([vinculada(cantidad=12.5, precio=92.4 / 36)],
                            repo=con_9001(**{**_CTRPRO_40, "tar": 0.0}))
    assert dcapro(respuesta)["tot"] == 32.08
    assert not set(_CLAVES) & set(_volcado(respuesta.lineas[0]))


# =====================================================================================
# R6 · `precio_negativo` con o sin dto; R5 con retención (F-015) sobre el neto
# =====================================================================================


def test_f018_r6_precio_negativo_con_dto() -> None:
    assert fallos([sin_vincular(precio=-1.0, dto=10.0), vinculada(precio=-2.0, dto=5.0)]) == [
        (0, "L2", "precio_negativo"), (1, "L1", "precio_negativo")]


def test_f018_r8_retencion_sobre_el_neto() -> None:
    repo = RepositorioDoble({"retenciones": [ctrrec_fila()]})
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)], repo=repo)
    dcarec = respuesta.filas["dcarec"][0]
    assert (dcarec["bas"], dcarec["cuo"]) == (11.18, 0.56)  # 11,18 · 0,05 = 0,559
    assert respuesta.filas["dca"]["tot"] == 12.97  # 13,53 - 0,56
    assert respuesta.filas["dca"]["impbru"] == 18.63


# =====================================================================================
# R16 · `idempotente` sin las claves; R18 · la traza
# =====================================================================================


def test_f018_r16_idempotente_sin_dto_ni_precio_bruto() -> None:
    repo = RepositorioDoble({"referencia": [_EXISTENTE], "lineas_del_existente": _LINEAS_EXISTENTE})
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)], repo=repo)
    assert respuesta.estado == "idempotente"
    for linea in respuesta.model_dump(mode="json")["lineas"]:
        assert not set(_CLAVES) & set(linea)


def test_f018_r18_traza_con_n_lineas_con_dto(caplog: pytest.LogCaptureFixture) -> None:
    _respuesta, trazas = trazar(caplog, [
        sin_vincular("L1", cantidad=1.0, precio=18.625, dto=40.0),
        sin_vincular("L3", cantidad=1.0, precio=18.625),
    ])
    assert trazas[0]["n_lineas_con_dto"] == 1
    assert "18.625" not in caplog.text and "11.18" not in caplog.text and "40%" not in caplog.text


def test_f018_r18_traza_con_r15_cuenta_la_copiada(caplog: pytest.LogCaptureFixture) -> None:
    _respuesta, trazas = trazar(caplog, [vinculada(cantidad=12.5, precio=92.4 / 36)],
                                repo=con_9001(**_CTRPRO_40))
    assert trazas[0]["n_lineas_con_dto"] == 1


def test_f018_r18_sin_dto_la_traza_no_cambia(caplog: pytest.LogCaptureFixture) -> None:
    _respuesta, trazas = trazar(caplog, [sin_vincular(dto=0)])
    assert "n_lineas_con_dto" not in trazas[0]


def test_f018_r18_error_sin_n_lineas_con_dto(caplog: pytest.LogCaptureFixture) -> None:
    _exc, trazas = trazar(caplog, [sin_vincular(precio=-1.0, dto=10.0)])
    assert trazas[0]["resultado"] == "error"
    assert "n_lineas_con_dto" not in trazas[0]


# =====================================================================================
# R20 · la proforma no admite `dto` en su petición
# =====================================================================================


def test_f018_r20_peticion_de_proforma_con_dto_no_valida() -> None:
    from f007_dobles import peticion as hoja

    cuerpo = hoja()
    cuerpo["lineas"] = [{**cuerpo["lineas"][0], "dto": 10}, *cuerpo["lineas"][1:]]
    with pytest.raises(ValidationError) as exc:
        ProformaRequest.model_validate(cuerpo)
    assert [e["type"] for e in exc.value.errors()] == ["extra_forbidden"]


def test_f018_d6_decimal_de_la_respuesta() -> None:
    """El `dto` de la respuesta es el leído de la fila (R14), como número."""
    respuesta, _ = ejecutar([sin_vincular(cantidad=1.0, precio=10.0, dto=21.45)])
    assert respuesta.lineas[0].dto == float(Decimal("21.45"))
    assert dcapro(respuesta)["dto"] == "21,45%"


# =====================================================================================
# T11 · R23: ninguna sentencia nueva ni cambiada; R24: el commit
# =====================================================================================

#: sha256 de `"\n".join(todas_las_sentencias())` medido en `dev` (`6aca027`) el
#: 2026-10-29: 47 sentencias del albarán, 6 de la proforma y 3 de la cadena.
_SQL_DE_DEV = {
    "albaran": (47, "d494a01d1b32a4532a5b354e365df1492871bc3101842fe13277263d37b1630e"),
    "proforma": (6, "eda6c1004d48ad40c58b933e25ba6d81d11804e9b1539b26899bd8972608387a"),
    "origen": (3, "61e9021f140f36efdd9814bb6080da4af23dd3cc2c01d56236ef1c3e3694c484"),
}


def test_f018_r23_las_sentencias_son_las_de_dev() -> None:
    import hashlib

    from application.use_cases.albaran_compra_statements import AlbaranCompraStatements
    from application.use_cases.proforma_origen_statements import ProformaOrigenStatements
    from application.use_cases.proforma_statements import ProformaStatements

    for nombre, clase in (("albaran", AlbaranCompraStatements), ("proforma", ProformaStatements),
                          ("origen", ProformaOrigenStatements)):
        sentencias = clase.todas_las_sentencias()
        huella = hashlib.sha256("\n".join(sentencias).encode()).hexdigest()
        assert (len(sentencias), huella) == _SQL_DE_DEV[nombre], nombre


def _sql_en_transaccion(repo: RepositorioDoble) -> list[tuple[str, str]]:
    return [(clave, sql) for _i, clave, sql, _p in repo.en_transaccion]


def test_f018_r23_el_commit_con_dto_usa_las_mismas_sentencias_que_sin_el() -> None:
    _con, repo_con = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)], commit=True)
    _sin, repo_sin = ejecutar([sin_vincular(cantidad=1.0, precio=18.625)], commit=True)
    assert _sql_en_transaccion(repo_con) == _sql_en_transaccion(repo_sin)
    assert repo_con.lecturas_hechas() == repo_sin.lecturas_hechas()


def test_f018_r24_commit_sin_vincular_con_dto() -> None:
    respuesta, repo = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)], commit=True)
    assert (respuesta.estado, respuesta.committed) == ("creado", True)
    from application.use_cases.albaran_compra_statements import APPLOCKS, DCA_COLUMNAS

    assert repo.transacciones[0]["applock_resources"] == list(APPLOCKS)
    (insert,) = repo.parametros_en_transaccion("insert_dcapro")
    fila = respuesta.filas["dcapro"][0]
    assert insert == list(fila.values())
    assert (fila["tar"], fila["dto"], fila["tot"], fila["pre"]) == (18.625, "40%", 11.18, 11.18)
    (mov,) = repo.parametros_en_transaccion("insert_mov")
    assert mov == list(respuesta.filas["mov"][0].values())
    assert respuesta.filas["mov"][0]["pre"] == 11.18
    (dca,) = repo.parametros_en_transaccion("insert_dca")
    assert (dca[DCA_COLUMNAS.index("impbru")], dca[DCA_COLUMNAS.index("totbas")]) == (18.63, 11.18)
    for releida in ("releer_con", "releer_dca", "releer_dcapro", "releer_mov", "releer_log"):
        assert releida in repo.sentencias()
    assert (respuesta.lineas[0].dto, respuesta.lineas[0].precio_bruto) == (40.0, 18.625)


def test_f018_r24_commit_vinculada_r15() -> None:
    respuesta, repo = ejecutar([vinculada(cantidad=12.5, precio=92.4 / 36)], commit=True,
                               repo=con_9001(**_CTRPRO_40))
    (insert,) = repo.parametros_en_transaccion("insert_dcapro")
    assert insert == list(respuesta.filas["dcapro"][0].values())
    assert (respuesta.filas["dcapro"][0]["tot"], respuesta.filas["dcapro"][0]["tar"]) == (32.09, 4.278)
    assert repo.parametros_en_transaccion("servido") == [[12.5, 9001]]  # canser por cantidad (R10)
    (mov,) = repo.parametros_en_transaccion("insert_mov")
    assert respuesta.filas["mov"][0]["pre"] == 32.09 / 12.5
    assert mov == list(respuesta.filas["mov"][0].values())
    assert respuesta.lineas[0].dto == 40.0


def test_f018_r24_reintento_con_los_mismos_importes() -> None:
    from f009_dobles import IntegrityError

    repo = RepositorioDoble(
        reservas={"ide_dcapro": lambda i, _p: (8000011 + 10 * (i - 1),)},
        fallos={"insert_dcapro": lambda i: IntegrityError("2627") if i == 1 else None},
    )
    respuesta, repo = ejecutar([sin_vincular(cantidad=1.0, precio=18.625, dto=40.0)], repo=repo,
                               commit=True)
    assert len(repo.cursores) == 2
    (primero,) = repo.parametros_en_transaccion("insert_dcapro", intento=1)
    (segundo,) = repo.parametros_en_transaccion("insert_dcapro", intento=2)
    assert (primero[0], segundo[0]) == (8000011, 8000021)
    assert primero[1:] == segundo[1:] == list(respuesta.filas["dcapro"][0].values())[1:]
    assert respuesta.filas["dca"]["impbru"] == 18.63
    assert respuesta.lineas[0].dto == 40.0
