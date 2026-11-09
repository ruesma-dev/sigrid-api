# tests/test_f008_settings.py
"""
F-008 · los siete ajustes nuevos de `sigrid/factura` (R4, R6, R8, R24-R26, R47),
con defecto CERRADO o vacío, los valores de despliegue de design §4 y la
muestra `local.settings.sample.json`. Enmienda 1 (R54): las dos `_FORZADA`,
con claves `<emp>:<producto>`, sustituyen a las `_NATURALEZA_POR_PRODUCTO`.

Sin red ni base: antes de cada test se borra del entorno toda clave que
`Settings` reconozca y se construye con `_env_file=None` (como F-009).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from config.settings import Settings

_RAIZ = Path(__file__).resolve().parents[1]

_MINIMO = {
    "SQL_DRIVER": "ODBC Driver 18 for SQL Server",
    "SQL_SERVER_HOST": "servidor.de.mentira",
    "SQL_SERVER_PORT": 1433,
    "SQL_SERVER_USERNAME": "usuario_de_mentira",
    "SQL_SERVER_PASSWORD": "no-es-una-credencial",
}

_CLAVES_NUEVAS = (
    "SIGRID_FACTURA_WRITE_ENABLED",
    "SIGRID_FACTURA_PREFIJOS_REFERENCIA",
    "SIGRID_FACTURA_MAX_LINEAS",
    "SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN",
    "SIGRID_FACTURA_NATURALEZA_FORZADA",
    "SIGRID_FACTURA_IVAS",
    "SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS",
)

#: Las que la enmienda 1 deja de leer (R54); también se borran del entorno.
_CLAVES_VIEJAS = (
    "SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO",
    "SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO",
)

#: Valores de despliegue propuestos (design §4), solo en JSON.
_DESPLIEGUE = {
    "SIGRID_FACTURA_WRITE_ENABLED": "false",
    "SIGRID_FACTURA_PREFIJOS_REFERENCIA": '["FAC-"]',
    "SIGRID_FACTURA_MAX_LINEAS": "500",
    "SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN": '["MA9999", "SM9999", "SB9999", "QA9999", "XA9999", "SM370001"]',
    "SIGRID_FACTURA_NATURALEZA_FORZADA": '{"1:MA9999": "MA99", "34:SM370001": "SM37"}',
    "SIGRID_FACTURA_IVAS": '["I21", "I10", "ISP21", "i0", "i4", "I21NDED", "I10NDED"]',
    "SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS": '["6"]',
}


def _claves_que_settings_reconoce() -> frozenset[str]:
    nombres: set[str] = set()
    for nombre, campo in Settings.model_fields.items():
        for candidato in (nombre, campo.alias, campo.validation_alias):
            if isinstance(candidato, str):
                nombres.update({candidato, candidato.upper(), candidato.lower()})
    return frozenset(nombres)


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave in _claves_que_settings_reconoce() | set(_CLAVES_NUEVAS) | set(_CLAVES_VIEJAS):
        monkeypatch.delenv(clave, raising=False)


def ajustes(**extra: object) -> Settings:
    return Settings(_env_file=None, **{**_MINIMO, **extra})


def test_f008_r47_los_siete_ajustes_arrancan_ausentes_y_cerrados() -> None:
    settings = ajustes()

    assert settings.sigrid_factura_write_enabled is False
    assert settings.sigrid_factura_prefijos_referencia == []
    assert settings.sigrid_factura_max_lineas == 500
    assert settings.sigrid_factura_productos_sin_origen == []
    assert settings.sigrid_factura_naturaleza_forzada == {}
    assert settings.sigrid_factura_ivas == []
    assert settings.sigrid_factura_cuentas_gasto_prefijos == []


def test_f008_r6_r24_r26_los_valores_de_despliegue_llegan_por_el_entorno(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for clave, valor in _DESPLIEGUE.items():
        monkeypatch.setenv(clave, valor)

    settings = ajustes()

    assert settings.sigrid_factura_write_enabled is False
    assert settings.sigrid_factura_prefijos_referencia == ["FAC-"]
    assert settings.sigrid_factura_max_lineas == 500
    assert settings.sigrid_factura_productos_sin_origen == [
        "MA9999", "SM9999", "SB9999", "QA9999", "XA9999", "SM370001",
    ]
    assert settings.sigrid_factura_naturaleza_forzada == {"1:MA9999": "MA99", "34:SM370001": "SM37"}
    assert settings.sigrid_factura_ivas == ["I21", "I10", "ISP21", "i0", "i4", "I21NDED", "I10NDED"]
    assert settings.sigrid_factura_cuentas_gasto_prefijos == ["6"]


def test_f008_r4_la_llave_se_abre_solo_con_un_verdadero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SIGRID_FACTURA_WRITE_ENABLED", "true")
    assert ajustes().sigrid_factura_write_enabled is True


def test_f008_r6_las_listas_pasan_por_el_validador_de_listas() -> None:
    """Por el entorno van en JSON (como las de F-009); el validador de listas
    recorta y admite CSV en los valores que no decodifica pydantic-settings."""
    settings = ajustes(
        SIGRID_FACTURA_PREFIJOS_REFERENCIA=" FAC- , OTRA- ",
        SIGRID_FACTURA_IVAS="I21,I10",
        SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS=["6", " 62 ", ""],
        SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN='["MA9999"]',
    )
    assert settings.sigrid_factura_prefijos_referencia == ["FAC-", "OTRA-"]
    assert settings.sigrid_factura_ivas == ["I21", "I10"]
    assert settings.sigrid_factura_cuentas_gasto_prefijos == ["6", "62"]
    assert settings.sigrid_factura_productos_sin_origen == ["MA9999"]


def test_f008_r25_el_mapeo_de_naturalezas_rechaza_claves_repetidas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SIGRID_FACTURA_NATURALEZA_FORZADA", '{"1:A": "x", "1:A": "y"}')
    with pytest.raises(Exception, match="repetida"):
        ajustes()


def test_f008_r8_el_tope_de_lineas_es_entero() -> None:
    with pytest.raises(ValidationError):
        ajustes(SIGRID_FACTURA_MAX_LINEAS="muchas")


def test_f008_r47_la_muestra_lleva_las_siete_cerradas() -> None:
    muestra = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))
    valores = muestra["Values"]
    assert {clave: valores[clave] for clave in _CLAVES_NUEVAS} == {
        "SIGRID_FACTURA_WRITE_ENABLED": "false",
        "SIGRID_FACTURA_PREFIJOS_REFERENCIA": "[]",
        "SIGRID_FACTURA_MAX_LINEAS": "500",
        "SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN": "[]",
        "SIGRID_FACTURA_NATURALEZA_FORZADA": "{}",
        "SIGRID_FACTURA_IVAS": "[]",
        "SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS": "[]",
    }


# --- Enmienda 1 (R54): forzado por empresa en las dos `_FORZADA` ---------------

_FORZADAS = ("SIGRID_FACTURA_NATURALEZA_FORZADA", "SIGRID_ALBARAN_NATURALEZA_FORZADA")
_LARGO = "P" * 24


def _forzada(settings: Settings, variable: str) -> dict[str, str]:
    return getattr(settings, variable.lower())


@pytest.mark.parametrize("variable", _FORZADAS)
def test_f008_r54_las_forzadas_arrancan_vacias(variable: str) -> None:
    assert _forzada(ajustes(), variable) == {}


@pytest.mark.parametrize("variable", _FORZADAS)
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (None, {}),
        ("", {}),
        ("{}", {}),
        ('{"1:MA9999": "MA99"}', {"1:MA9999": "MA99"}),
        ('{" 1:MA9999 ": " MA99 "}', {"1:MA9999": "MA99"}),
        ('{"01:MA9999": "MA99"}', {"1:MA9999": "MA99"}),
        ('{"1:MA9999": "MA99", "31:MA9999": "MA99", "34:SM370001": "SM37"}',
         {"1:MA9999": "MA99", "31:MA9999": "MA99", "34:SM370001": "SM37"}),
        (f'{{"1:{_LARGO}": "X"}}', {f"1:{_LARGO}": "X"}),
        ({"1:MA9999": "MA99"}, {"1:MA9999": "MA99"}),
    ],
)
def test_f008_r54_forzada_valida_y_normalizada(
    variable: str, valor: object, esperado: dict[str, str]
) -> None:
    assert _forzada(ajustes(**{variable: valor}), variable) == esperado


@pytest.mark.parametrize("variable", _FORZADAS)
@pytest.mark.parametrize(
    "valor",
    [
        '{"MA9999": "MA99"}',                          # sin `:` (el formato viejo)
        '{":MA9999": "MA99"}',                         # emp vacio
        '{"0:MA9999": "MA99"}',                        # emp 0
        '{"00:MA9999": "MA99"}',
        '{"-1:MA9999": "MA99"}',                       # emp negativo
        '{"uno:MA9999": "MA99"}',                      # emp no entero
        '{"1.5:MA9999": "MA99"}',
        '{"+1:MA9999": "MA99"}',
        '{"1:": "MA99"}',                              # producto vacio
        '{"1: MA9999": "MA99"}',                       # producto con espacios
        '{"1:MA 9999": "MA99"}',
        '{"1 :MA9999": "MA99"}',
        f'{{"1:{_LARGO}P": "X"}}',                     # producto de mas de 24
        '{"1:MA:9999": "MA99"}',                       # dos `:`
        '{"1:MA9999": ""}',                            # valor vacio
        '{"1:MA9999": "   "}',
        '{"01:MA9999": "MA99", "1:MA9999": "MA98"}',   # repetidas tras normalizar
        '{"1:MA9999": "MA99", "1:MA9999": "MA98"}',
        "1:MA9999=MA99",                               # ni JSON
        "1:MA9999:MA99,2:QA9999:QA99",                 # CSV
        '["1:MA9999", "MA99"]',                        # lista
        "[]",
        '{"1:MA9999": 99}',
        {"1:MA9999": 1},
        {"MA9999": "MA99"},
        42,
    ],
)
def test_f008_r54_forzada_mal_escrita_no_arranca(variable: str, valor: object) -> None:
    with pytest.raises(ValidationError):
        ajustes(**{variable: valor})


@pytest.mark.parametrize("variable", _FORZADAS)
def test_f008_r54_forzada_mal_escrita_en_el_entorno_no_arranca(
    monkeypatch: pytest.MonkeyPatch, variable: str
) -> None:
    monkeypatch.setenv(variable, '{"MA9999": "MA99"}')
    with pytest.raises(ValidationError):
        ajustes()


def test_f008_r54_las_viejas_en_el_entorno_se_ignoran_y_arranca(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Las dos `_NATURALEZA_POR_PRODUCTO` siguen hoy en Azure con el formato
    viejo: con ellas presentes `Settings` arranca y no las expone."""
    for vieja in _CLAVES_VIEJAS:
        monkeypatch.setenv(vieja, '{"MA9999": "MA99"}')
    settings = ajustes()
    assert settings.sigrid_factura_naturaleza_forzada == {}
    assert settings.sigrid_albaran_naturaleza_forzada == {}
    for campo in ("sigrid_factura_naturaleza_por_producto", "sigrid_albaran_naturaleza_por_producto"):
        assert not hasattr(settings, campo)
        assert campo not in Settings.model_fields


def test_f008_r54_el_mapa_de_proformas_sigue_por_producto(monkeypatch: pytest.MonkeyPatch) -> None:
    """P23: el de proformas no cambia de nombre ni de formato."""
    monkeypatch.setenv("SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO", '{"SM9999": "SM99"}')
    assert ajustes().sigrid_proforma_naturaleza_por_producto == {"SM9999": "SM99"}


def test_f008_r54_la_muestra_lleva_las_forzadas_y_no_las_viejas() -> None:
    valores = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))["Values"]
    assert valores["SIGRID_FACTURA_NATURALEZA_FORZADA"] == "{}"
    assert valores["SIGRID_ALBARAN_NATURALEZA_FORZADA"] == "{}"
    assert not set(_CLAVES_VIEJAS) & set(valores)
    assert valores["SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO"] == "{}"
