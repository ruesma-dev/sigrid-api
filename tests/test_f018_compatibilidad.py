# tests/test_f018_compatibilidad.py
"""
F-018 · T12: compatibilidad (R7, R19, R26).

1. Albarán (peticiones y dobles de F-009 y F-015, sin tocarlos): con `dto`
   ausente, `null` o 0 en todas las líneas, las filas, el SQL grabado (lecturas
   y transacción, con sus parámetros), `model_dump(mode="json")` y la traza son
   idénticos.
2. Proforma (peticiones y dobles de F-007 y F-016, sin tocarlos): la petición no
   admite `dto` (R20), así que lo que se varía es el `ctrpro`: vacío, `NULL` y
   no legible (`10+2,5`, `5`) dan lo mismo que hoy salvo el texto copiado de
   `dcapro.dto`, que es el del `ctrpro` como hoy.
3. Un `ctrpro` con dto legible (R15, R21): solo cambian `tot`, `pre` e `ivacuo`
   de esa línea, `impbru` y los totales de la cabecera, el `mov` y las claves de
   R16 (a origen, además `importe_origen_cadena`).

R19 (el clásico y `albaran-directo` no cambian) lo fijan sus tests y su dorado,
sin tocar, y `git diff dev` (T13). Sin red ni base de datos.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import pytest
from f007_dobles import RepositorioProforma, SettingsProforma
from f007_dobles import peticion as hoja
from f009_dobles import AHORA, RepositorioDoble, SettingsDoble, ctrpro
from f016_dobles import RepositorioOrigen
from test_f009_use_case import RelojDoble, sin_vincular, vinculada
from test_f009_use_case import peticion as peticion_albaran
from test_f015_use_case import _ANALITICA_SIN_CONTRATO, ctrrec_fila
from test_f016_use_case import encadenada, primera

from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
)
from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.proforma_models import ProformaRequest

_LOGGER = "application.use_cases.create_albaran_compra_use_case"


def _foto(repo: Any, respuesta: Any, caplog: pytest.LogCaptureFixture) -> dict[str, Any]:
    """Todo lo observable de una ejecución: respuesta, filas, SQL y traza."""
    trazas = [json.loads(r.getMessage()) for r in caplog.records if r.name == _LOGGER]
    caplog.clear()
    return {
        "respuesta": respuesta.model_dump(mode="json"),
        "lecturas": [d for tipo, d in repo.llamadas],
        "transaccion": [(i, c, sql, p) for i, c, sql, p in repo.en_transaccion],
        "trazas": trazas,
    }


# =====================================================================================
# 1 · Albarán: dto ausente, null y 0
# =====================================================================================

#: (lineas, cambios de la petición, lecturas del doble): peticiones de F-009 y F-015.
_ALBARANES: dict[str, tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]] = {
    "vinculada": ([vinculada()], {}, {}),
    "vinculada_opcion_c_10+2,5": ([vinculada(precio=10.50009)], {}, {}),
    "vinculada_precio_distinto": ([vinculada(precio=12.0)], {}, {}),
    "sin_vincular": ([sin_vincular()], {}, {}),
    "mezcla_con_partida": ([vinculada(partida="01.01"), sin_vincular(partida="03", paride=8),
                            vinculada("L3", 9002, cantidad=1.0, precio=3.0)], {}, {}),
    "devoluciones": ([vinculada(cantidad=-1.0), sin_vincular(cantidad=-2.0)], {}, {}),
    "f015_retencion": ([vinculada(), sin_vincular()], {}, {"retenciones": [ctrrec_fila()]}),
    "f015_sin_contrato": ([sin_vincular()], {"cod_contrato": None}, _ANALITICA_SIN_CONTRATO),
}


def _albaran(lineas: list[dict[str, Any]], cambios: dict[str, Any], lecturas: dict[str, Any],
             caplog: pytest.LogCaptureFixture, *, repo: RepositorioDoble | None = None) -> dict:
    repo = repo or RepositorioDoble(lecturas)
    caso = CreateAlbaranCompraUseCase(repo, _settings(), ahora_utc=lambda: AHORA,
                                      reloj=RelojDoble(100.0, 100.25))
    with caplog.at_level(logging.INFO, logger=_LOGGER):
        respuesta = caso.run(peticion_albaran(lineas, **cambios))
    return _foto(repo, respuesta, caplog)


def _settings() -> Any:
    return SettingsDoble()


@pytest.mark.parametrize("commit", [False, True], ids=["previa", "commit"])
@pytest.mark.parametrize("caso", list(_ALBARANES))
def test_f018_r7_albaran_con_dto_ausente_null_o_0_identico(
    caso: str, commit: bool, caplog: pytest.LogCaptureFixture
) -> None:
    lineas, cambios, lecturas = _ALBARANES[caso]
    cambios = {**cambios, "commit": commit}
    ausente = _albaran(lineas, cambios, lecturas, caplog)
    for dto in (None, 0, 0.0):
        con = _albaran([{**l, "dto": dto} for l in lineas], cambios, lecturas, caplog)
        assert con == ausente, dto
    assert "n_lineas_con_dto" not in ausente["trazas"][0]
    assert all("dto" not in l for l in ausente["respuesta"]["lineas"])


# =====================================================================================
# 2 · Proforma: `ctrpro` vacío, NULL o no legible
# =====================================================================================

_PROFORMAS = {
    "mes_existente": (lambda: hoja(), RepositorioProforma),
    "mes_previa": (lambda: hoja(otra_del_mes=True), RepositorioProforma),
    "mes_commit": (lambda: hoja(otra_del_mes=True, commit=True), RepositorioProforma),
    "origen_primera": (lambda: primera(), RepositorioOrigen),
    "origen_encadenada": (lambda: encadenada(), RepositorioOrigen),
    "origen_commit": (lambda: encadenada(commit=True), RepositorioOrigen),
}


def _proforma(cuerpo: dict[str, Any], clase: type, dto: Any) -> tuple[dict[str, Any], Any]:
    repo = clase()
    if dto != "":
        repo.ctrpro_filas = [{**f, "dto": dto} for f in repo.ctrpro_filas]
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA,
                                 reloj=RelojDoble(100.0, 100.25))
    respuesta = caso.run(ProformaRequest(**cuerpo))
    return respuesta.model_dump(mode="json"), repo


def _sin_dto_copiado(volcado: dict[str, Any]) -> dict[str, Any]:
    filas = volcado.get("filas") or {}
    if "dcapro" not in filas:
        return volcado
    return {**volcado, "filas": {**filas, "dcapro": [
        {c: v for c, v in f.items() if c != "dto"} for f in filas["dcapro"]]}}


@pytest.mark.parametrize("dto", [None, "10+2,5", "5", " "], ids=["null", "cascada", "sin_pct",
                                                                  "blanco"])
@pytest.mark.parametrize("caso", list(_PROFORMAS))
def test_f018_r7_proforma_con_ctrpro_sin_dto_legible_identica(caso: str, dto: Any) -> None:
    cuerpo, clase = _PROFORMAS[caso]
    hoy, repo_hoy = _proforma(cuerpo(), clase, "")
    con, repo_con = _proforma(cuerpo(), clase, dto)
    assert _sin_dto_copiado(con) == _sin_dto_copiado(hoy)
    assert all(not {"dto", "precio_bruto"} & set(l) for l in con["lineas"])
    # El SQL y sus parámetros, iguales salvo el `dto` copiado del INSERT de `dcapro`.
    assert [c for _i, c, _s, _p in repo_con.en_transaccion] == [
        c for _i, c, _s, _p in repo_hoy.en_transaccion]
    assert repo_con.lecturas_hechas() == repo_hoy.lecturas_hechas()
    # El `dto` de las vinculadas: el copiado del `ctrpro` (opción C, como hoy) o ''.
    for fila in (con.get("filas") or {}).get("dcapro", []):
        assert fila["dto"] in {"", dto or ""}


# =====================================================================================
# 3 · R26: con un `ctrpro` de dto legible solo cambia lo de R15/R21
# =====================================================================================


def _diferencias(a: Any, b: Any, ruta: str = "") -> set[str]:
    """Las rutas (con `[]` en lugar de los índices) donde `a` y `b` difieren."""
    if isinstance(a, dict) and isinstance(b, dict):
        return {r for k in a.keys() | b.keys()
                for r in _diferencias(a.get(k, "<falta>"), b.get(k, "<falta>"), f"{ruta}.{k}")}
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return {r for x, y in zip(a, b, strict=True) for r in _diferencias(x, y, f"{ruta}[]")}
    return set() if a == b else {ruta}


#: Lo único que puede cambiar en la respuesta del albarán con R15 (R26).
_PERMITIDAS_ALBARAN = {
    ".filas.dcapro[].tot", ".filas.dcapro[].pre", ".filas.dcapro[].ivacuo",
    ".filas.dca.impbru", ".filas.dca.impnet", ".filas.dca.totbas", ".filas.dca.totiva",
    ".filas.dca.totdoc", ".filas.dca.tot", ".filas.dca.totpag",
    ".cabecera.impbru", ".cabecera.impnet", ".cabecera.totbas", ".cabecera.totiva",
    ".cabecera.totdoc", ".cabecera.tot", ".cabecera.totpag",
    ".totales.totbas", ".totales.totiva", ".totales.totdoc", ".totales.tot",
    ".filas.mov[].pre", ".filas.mov[].prc", ".filas.mov[].almpma",
    ".movimientos[].pre", ".movimientos[].prc", ".movimientos[].almpma",
    ".lineas[].precio", ".lineas[].total", ".lineas[].iva_cuota", ".lineas[].pmp_resultante",
    ".lineas[].dto", ".lineas[].precio_bruto",
    # El texto copiado del `ctrpro` por la opción C, como hoy (`40%` frente a `''`).
    ".filas.dcapro[].dto",
}


def test_f018_r26_albaran_r15_solo_cambia_lo_de_la_linea_y_la_cabecera(
    caplog: pytest.LogCaptureFixture,
) -> None:
    def repo(dto: str) -> RepositorioDoble:
        lineas = ctrpro()
        cambio = {"pre": 92.4 / 36, "tar": 4.278, "dto": dto, "can": 36.0, "tot": 92.4}
        return RepositorioDoble(ctrpro_filas=[{**lineas[0], **cambio}, *lineas[1:]])

    lineas = [vinculada(cantidad=12.5, precio=92.4 / 36), sin_vincular()]
    con = _albaran(lineas, {}, {}, caplog, repo=repo("40%"))
    hoy = _albaran(lineas, {}, {}, caplog, repo=repo(""))
    diferencias = _diferencias(con["respuesta"], hoy["respuesta"])
    assert diferencias <= _PERMITIDAS_ALBARAN, diferencias - _PERMITIDAS_ALBARAN
    assert ".filas.dcapro[].tot" in diferencias and ".lineas[].dto" in diferencias
    # Solo la línea del `ctrpro` con dto: la sin vincular, igual.
    assert con["respuesta"]["lineas"][1] == hoy["respuesta"]["lineas"][1]
    assert con["respuesta"]["filas"]["dcapro"][1] == hoy["respuesta"]["filas"]["dcapro"][1]
    # La traza solo añade `n_lineas_con_dto`; las lecturas, iguales.
    assert {k: v for k, v in con["trazas"][0].items() if k != "n_lineas_con_dto"} == hoy["trazas"][0]
    assert con["lecturas"] == hoy["lecturas"]


def _proforma_f09(cuerpo: dict[str, Any], clase: type, dto: str) -> dict[str, Any]:
    from test_f018_proforma import _parchear

    repo = _parchear(clase(), dto)
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    return caso.run(ProformaRequest(**cuerpo)).model_dump(mode="json")


@pytest.mark.parametrize("modo", ["mes", "origen"])
def test_f018_r26_proforma_r21_solo_cambia_lo_de_r26(modo: str) -> None:
    from test_f018_proforma import hoja_a_origen, hoja_de_mes

    cuerpo, clase = (hoja_de_mes(), RepositorioProforma) if modo == "mes" else (
        hoja_a_origen(), RepositorioOrigen)
    con = _proforma_f09(cuerpo, clase, "40%")
    hoy = _proforma_f09(cuerpo, clase, "")
    permitidas = _PERMITIDAS_ALBARAN | (
        {".cadena.importe_origen_cadena"} if modo == "origen" else set())
    diferencias = _diferencias(con, hoy)
    assert diferencias <= permitidas, diferencias - permitidas
    assert ".filas.dca.impbru" in diferencias
