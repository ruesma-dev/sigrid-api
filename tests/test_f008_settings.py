# tests/test_f008_settings.py
"""
F-008 · los siete ajustes nuevos de `sigrid/factura` (R4, R6, R8, R24-R26, R47),
con defecto CERRADO o vacío, los valores de despliegue de design §4 y la
muestra `local.settings.sample.json`.

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
    "SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO",
    "SIGRID_FACTURA_IVAS",
    "SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS",
)

#: Valores de despliegue propuestos (design §4), solo en JSON.
_DESPLIEGUE = {
    "SIGRID_FACTURA_WRITE_ENABLED": "false",
    "SIGRID_FACTURA_PREFIJOS_REFERENCIA": '["FAC-"]',
    "SIGRID_FACTURA_MAX_LINEAS": "500",
    "SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN": '["MA9999", "SM9999", "SB9999", "QA9999", "XA9999", "SM370001"]',
    "SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO": '{"MA9999": "MA99", "SM9999": "SM99"}',
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
    for clave in _claves_que_settings_reconoce() | set(_CLAVES_NUEVAS):
        monkeypatch.delenv(clave, raising=False)


def ajustes(**extra: object) -> Settings:
    return Settings(_env_file=None, **{**_MINIMO, **extra})


def test_f008_r47_los_siete_ajustes_arrancan_ausentes_y_cerrados() -> None:
    settings = ajustes()

    assert settings.sigrid_factura_write_enabled is False
    assert settings.sigrid_factura_prefijos_referencia == []
    assert settings.sigrid_factura_max_lineas == 500
    assert settings.sigrid_factura_productos_sin_origen == []
    assert settings.sigrid_factura_naturaleza_por_producto == {}
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
    assert settings.sigrid_factura_naturaleza_por_producto == {"MA9999": "MA99", "SM9999": "SM99"}
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
    monkeypatch.setenv("SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO", '{"A": "x", "A": "y"}')
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
        "SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO": "{}",
        "SIGRID_FACTURA_IVAS": "[]",
        "SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS": "[]",
    }
