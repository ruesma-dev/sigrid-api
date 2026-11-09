# tests/test_f008_naturaleza_albaran.py
"""
F-008 enmienda 1 · T28: la naturaleza de las sin vincular de `sigrid/albaran`
(R49-R51, R53, R54). Forzada por `<emp>:<producto>` en
`SIGRID_ALBARAN_NATURALEZA_FORZADA`; si no, la de la ficha del producto
(`pro.natide`, L15D), con la validez y la analitica de F-009 R13b y R15. Las
proformas (`naturaleza_de_ficha` False) siguen con su mapa por producto.

Sin red ni base: el ERP doble de F-009 (`f009_dobles`). La obra del doble es
la `0404` de la empresa 1; `MA9999` (proide 66) tiene en su ficha `MA1501`
(natide 505, cuenta 605, analitica `0404.CDMA15` 705) y el forzado del doble
le da `MA99` (natide 501), como el mapeo viejo.
"""
from __future__ import annotations

import dataclasses
from typing import Any

import pytest
from f009_dobles import AHORA, RepositorioDoble, SettingsDoble

from application.use_cases.create_albaran_compra_use_case import (
    PERFIL_ALBARAN,
    CreateAlbaranCompraUseCase,
)
from application.use_cases.create_proforma_use_case import PERFIL_PROFORMA
from domain.models.albaran_compra_models import AlbaranCompraError, AlbaranCompraRequest


def _sin_vincular(ref: str = "L2", producto: str = "MA9999") -> dict[str, Any]:
    return {"referencia_linea": ref, "producto": producto, "descripcion": "Arena de rio",
            "unidad": "m3", "cantidad": 3.0, "precio": 2.675}


def _peticion(lineas: list[dict[str, Any]]) -> AlbaranCompraRequest:
    return AlbaranCompraRequest.model_validate({
        "database": "ruesma", "cod_obra": "0404", "usu": "prueba", "cif_proveedor": "B12345678",
        "referencia_externa": "ALB-1", "cod_contrato": "CTSU16/0206", "su_referencia": "A-77",
        "fecha_albaran": 20261005, "lineas": lineas,
    })


def _ejecutar(lineas: list[dict[str, Any]], *, forzada: dict[str, str] | None = None,
              lecturas: dict[str, Any] | None = None, caso: type = CreateAlbaranCompraUseCase,
              settings: SettingsDoble | None = None) -> tuple[Any, RepositorioDoble]:
    settings = settings or SettingsDoble()
    if forzada is not None:
        settings.sigrid_albaran_naturaleza_forzada = forzada
    repo = RepositorioDoble(lecturas)
    return caso(repo, settings, ahora_utc=lambda: AHORA).run(_peticion(lineas)), repo


def _fallos(lineas: list[dict[str, Any]], **kwargs: Any) -> list[tuple[str, str]]:
    with pytest.raises(AlbaranCompraError) as excinfo:
        _ejecutar(lineas, **kwargs)
    assert excinfo.value.codigo == "lineas_no_validas"
    return [(f.codigo, f.mensaje) for f in excinfo.value.lineas]


def _nca(respuesta: Any, i: int = 0) -> tuple[int, int, int]:
    fila = respuesta.filas["dcapro"][i]
    return fila["natide"], fila["cueide"], fila["caaide"]


# --- R49, R53: forzada de la empresa, de otra empresa y la ficha -----------------


def test_f008_r53_forzada_de_la_empresa_da_lo_del_mapeo_viejo_sin_leer_la_ficha() -> None:
    respuesta, repo = _ejecutar([_sin_vincular()])
    assert _nca(respuesta) == (501, 601, 701)
    assert repo.parametros_de("naturalezas") == [["MA99"]]
    assert "naturalezas_de_ficha" not in repo.lecturas_hechas()


def test_f008_r49_forzada_de_otra_empresa_no_aplica_y_manda_la_ficha() -> None:
    respuesta, repo = _ejecutar([_sin_vincular()], forzada={"31:MA9999": "MA99"})
    assert _nca(respuesta) == (505, 605, 705)
    assert repo.parametros_de("naturalezas_de_ficha") == [[66]]
    assert "naturalezas" not in repo.lecturas_hechas()
    assert repo.parametros_de("cuentas") == [[1, "6000005"]]
    assert repo.parametros_de("analiticas") == [["0404.CDMA15"]]


def test_f008_r49_sin_forzado_manda_la_ficha() -> None:
    respuesta, _repo = _ejecutar([_sin_vincular()], forzada={})
    assert _nca(respuesta) == (505, 605, 705)


def test_f008_r49_r53_mezcla_la_ficha_se_lee_solo_con_los_no_forzados() -> None:
    respuesta, repo = _ejecutar(
        [_sin_vincular("A"), _sin_vincular("B", producto="QA9999")], forzada={"1:MA9999": "MA99"},
    )
    assert [_nca(respuesta, 0), _nca(respuesta, 1)] == [(501, 601, 701), (502, 602, 702)]
    assert repo.parametros_de("naturalezas") == [["MA99"]]
    assert repo.parametros_de("naturalezas_de_ficha") == [[67]]


# --- R50: rechazos, con el mismo codigo y el origen en el mensaje ----------------


@pytest.mark.parametrize("ficha", [
    (66, 0, None, None, None, None, None),                       # natide 0
    (66, None, None, None, None, None, None),                    # natide NULL
    (66, 505, None, None, None, None, None),                     # sin auxpronat
    (66, 505, "MA1501", 0, 20200101, "MOD.CDMA15", "6000005"),   # de baja
    (66, 505, "MA1501", 2, 0, "MOD.CDMA15", "6000005"),          # de otra empresa
    (66, 505, "MA1501", 0, 0, "MOD.CDMA15", " "),                # sin cuacomcod
    (66, 0, "MA1501", 0, 0, "MOD.CDMA15", "6000005"),            # natide 0 con auxpronat 0 (T32)
], ids=["natide_0", "natide_null", "sin_auxpronat", "de_baja", "otra_empresa", "sin_cuacomcod",
        "natide_0_con_auxpronat"])
def test_f008_r50_ficha_sin_naturaleza_valida_es_naturaleza_no_valida(ficha: tuple) -> None:
    fallos = _fallos([_sin_vincular()], forzada={}, lecturas={"naturalezas_de_ficha": [ficha]})
    assert [c for c, _m in fallos] == ["naturaleza_no_valida"]
    assert "ficha" in fallos[0][1]
    assert "FORZADA" not in fallos[0][1]


def test_f008_r50_sin_fila_de_ficha_es_naturaleza_no_valida() -> None:
    fallos = _fallos([_sin_vincular()], forzada={}, lecturas={"naturalezas_de_ficha": []})
    assert [c for c, _m in fallos] == ["naturaleza_no_valida"]


def test_f008_r50_la_ficha_con_cuenta_que_no_es_unica_es_naturaleza_no_valida() -> None:
    fallos = _fallos([_sin_vincular()], forzada={}, lecturas={"cuentas": [(605, "6000005"), (606, "6000005")]})
    assert [c for c, _m in fallos] == ["naturaleza_no_valida"]
    assert "ficha" in fallos[0][1]


def test_f008_r50_forzada_no_valida_dice_que_es_la_forzada() -> None:
    fallos = _fallos([_sin_vincular()], forzada={"1:MA9999": "NADA"})
    assert [c for c, _m in fallos] == ["naturaleza_no_valida"]
    assert "SIGRID_ALBARAN_NATURALEZA_FORZADA" in fallos[0][1]
    assert "forzada" in fallos[0][1]


def test_f008_r50_analitica_no_resuelta_igual_desde_la_ficha() -> None:
    fallos = _fallos([_sin_vincular()], forzada={}, lecturas={"analiticas": []})
    assert [c for c, _m in fallos] == ["analitica_no_resuelta"]


# --- R51, R54: el perfil del albaran lee la ficha; el de proformas, no -----------


def test_f008_r54_el_perfil_del_albaran_lee_la_forzada_y_la_ficha() -> None:
    assert PERFIL_ALBARAN.naturaleza_de_ficha is True
    assert PERFIL_ALBARAN.campo_naturalezas == "sigrid_albaran_naturaleza_forzada"


def test_f008_r51_las_proformas_siguen_con_su_mapa_por_producto() -> None:
    assert PERFIL_PROFORMA.naturaleza_de_ficha is False
    assert PERFIL_PROFORMA.campo_naturalezas == "sigrid_proforma_naturaleza_por_producto"


@dataclasses.dataclass
class _SettingsConMapa(SettingsDoble):
    mapa_por_producto: dict[str, str] = dataclasses.field(default_factory=lambda: {"MA9999": "MA99"})


class _CasoSinFicha(CreateAlbaranCompraUseCase):
    """El nucleo con `naturaleza_de_ficha` False, como las proformas."""

    perfil = dataclasses.replace(PERFIL_ALBARAN, naturaleza_de_ficha=False,
                                 campo_naturalezas="mapa_por_producto")


def test_f008_r51_sin_ficha_el_mapa_es_por_producto_y_l15d_no_se_lanza() -> None:
    respuesta, repo = _ejecutar([_sin_vincular()], caso=_CasoSinFicha, settings=_SettingsConMapa())
    assert _nca(respuesta) == (501, 601, 701)
    assert "naturalezas_de_ficha" not in repo.lecturas_hechas()


def test_f008_r51_sin_ficha_fuera_del_mapa_sigue_siendo_naturaleza_no_valida() -> None:
    fallos = _fallos([_sin_vincular()], caso=_CasoSinFicha,
                     settings=_SettingsConMapa(mapa_por_producto={}))
    assert fallos == [("naturaleza_no_valida",
                       ("La naturaleza del producto 'MA9999' (MAPA_POR_PRODUCTO) no existe, esta de baja, "
                        "es de otra empresa o su cuenta no es unica."))]


# --- T32 (mutacion): la validez de la candidata, en la ficha y en el mapa --------


def test_f008_r50_ficha_con_numemp_y_fecbaj_nulos_es_valida() -> None:
    """`numemp` y `fecbaj` NULL valen 0 (de todas las empresas, sin baja): la
    existencia de la naturaleza la dice `n.cod`, no `n.numemp`."""
    ficha = (66, 505, "MA1501", None, None, "MOD.CDMA15", "6000005")
    respuesta, _repo = _ejecutar([_sin_vincular()], forzada={}, lecturas={"naturalezas_de_ficha": [ficha]})
    assert _nca(respuesta) == (505, 605, 705)


@pytest.mark.parametrize("naturalezas", [
    [(501, "MA99", 0, 20200101, "MOD.CDSB37", "6000001")],              # de baja, de todas
    [(501, "MA99", 2, 0, "MOD.CDSB37", "6000001")],                     # de otra empresa
    [(501, "MA99", 0, 0, "MOD.CDSB37", " ")],                           # sin cuacomcod
    [(501, "MA99", 0, 0, "MOD.CDSB37", "6000001"),
     (509, "MA99", 1, 0, "MOD.CDSB37", "6000001")],                     # dos candidatas
], ids=["de_baja", "otra_empresa", "sin_cuacomcod", "dos_candidatas"])
def test_f008_r51_sin_ficha_el_mapa_valida_la_candidata_como_siempre(naturalezas: list[tuple]) -> None:
    fallos = _fallos([_sin_vincular()], caso=_CasoSinFicha, settings=_SettingsConMapa(),
                     lecturas={"naturalezas": naturalezas})
    assert [c for c, _m in fallos] == ["naturaleza_no_valida"]


def test_f008_r53_l15d_es_una_lectura_de_lista_y_pide_el_tope() -> None:
    _respuesta, repo = _ejecutar([_sin_vincular()], forzada={})
    topes = {d[2] for t, d in repo.llamadas if t == "leer" and d[0] == "naturalezas_de_ficha"}
    assert topes == {SettingsDoble().max_allowed_rows}
