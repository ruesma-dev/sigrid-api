# tests/test_f007_settings.py
"""
F-007 · T3 · R4: las cinco App Settings de `sigrid/proforma`, con defecto
CERRADO, en JSON y con los validadores de F-009; ninguna existente cambia.

Como `test_f009_settings.py`: antes de cada test se borra del entorno toda clave
que `Settings` reconozca y se construye con `_env_file=None`, para medir el
defecto del código y no lo que tenga puesto la máquina.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings.sources import SettingsError

from config.settings import Settings

_RAIZ = Path(__file__).resolve().parents[1]

_MINIMO = {
    "SQL_DRIVER": "ODBC Driver 18 for SQL Server",
    "SQL_SERVER_HOST": "servidor.de.mentira",
    "SQL_SERVER_PORT": 1433,
    "SQL_SERVER_USERNAME": "usuario_de_mentira",
    "SQL_SERVER_PASSWORD": "no-es-una-credencial",
}

#: Las cinco claves de R4.
_CLAVES_NUEVAS = (
    "SIGRID_PROFORMA_WRITE_ENABLED",
    "SIGRID_PROFORMA_PREFIJOS_REFERENCIA",
    "SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO",
    "SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO",
    "SIGRID_PROFORMA_MAX_LINEAS",
)

#: Los valores de despliegue de R4 (D11, aprobados el 2026-10-25), solo en JSON.
_DESPLIEGUE = {
    "SIGRID_PROFORMA_WRITE_ENABLED": "false",
    "SIGRID_PROFORMA_PREFIJOS_REFERENCIA": '["PRF-"]',
    "SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO": '["SM9999", "SB9999", "SM370001"]',
    "SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO": '{"SM9999": "SM99", "SB9999": "SB99", "SM370001": "SM37"}',
    "SIGRID_PROFORMA_MAX_LINEAS": "500",
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


def test_f007_r4_los_cinco_ajustes_arrancan_con_defecto_cerrado() -> None:
    settings = ajustes()
    assert settings.sigrid_proforma_write_enabled is False
    assert settings.sigrid_proforma_prefijos_referencia == []
    assert settings.sigrid_proforma_productos_sin_contrato == []
    assert settings.sigrid_proforma_naturaleza_por_producto == {}
    assert settings.sigrid_proforma_max_lineas == 500


def test_f007_r4_los_valores_de_despliegue_llegan_por_el_entorno(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for clave, valor in _DESPLIEGUE.items():
        monkeypatch.setenv(clave, valor)
    settings = ajustes()
    assert settings.sigrid_proforma_write_enabled is False
    assert settings.sigrid_proforma_prefijos_referencia == ["PRF-"]
    assert settings.sigrid_proforma_productos_sin_contrato == ["SM9999", "SB9999", "SM370001"]
    assert settings.sigrid_proforma_naturaleza_por_producto == {
        "SM9999": "SM99", "SB9999": "SB99", "SM370001": "SM37",
    }
    assert settings.sigrid_proforma_max_lineas == 500


def test_f007_r4_los_ajustes_se_leen_de_su_alias() -> None:
    settings = ajustes(SIGRID_PROFORMA_WRITE_ENABLED="true", SIGRID_PROFORMA_MAX_LINEAS="7")
    assert settings.sigrid_proforma_write_enabled is True
    assert settings.sigrid_proforma_max_lineas == 7


@pytest.mark.parametrize(
    "clave, atributo",
    [
        ("SIGRID_PROFORMA_PREFIJOS_REFERENCIA", "sigrid_proforma_prefijos_referencia"),
        ("SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO", "sigrid_proforma_productos_sin_contrato"),
    ],
)
@pytest.mark.parametrize(
    "valor, esperado",
    [('["PRF-"]', ["PRF-"]), ('[" PRF- ", "OTRO"]', ["PRF-", "OTRO"]), ("", []), (None, []),
     (["PRF-"], ["PRF-"])],
)
def test_f007_r4_las_listas_usan_parse_string_list(
    clave: str, atributo: str, valor: object, esperado: list[str]
) -> None:
    assert getattr(ajustes(**{clave: valor}), atributo) == esperado


@pytest.mark.parametrize(
    "clave", ["SIGRID_PROFORMA_PREFIJOS_REFERENCIA", "SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO"]
)
@pytest.mark.parametrize("valor", ["PRF-,OTRO", "SM9999"])
def test_f007_r4_una_lista_en_csv_por_el_entorno_no_arranca(
    monkeypatch: pytest.MonkeyPatch, clave: str, valor: str
) -> None:
    """Como App Setting (el entorno), una lista que no es JSON no arranca."""
    monkeypatch.setenv(clave, valor)
    with pytest.raises((ValidationError, SettingsError)):
        ajustes()


@pytest.mark.parametrize(
    "valor, esperado",
    [(None, {}), ("", {}), ("{}", {}), ('{"SM9999": "SM99"}', {"SM9999": "SM99"}),
     ('{" SM9999 ": " SM99 "}', {"SM9999": "SM99"}), ({"SB9999": "SB99"}, {"SB9999": "SB99"})],
)
def test_f007_r4_naturaleza_por_producto_objeto_json_de_textos(
    valor: object, esperado: dict[str, str]
) -> None:
    settings = ajustes(SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO=valor)
    assert settings.sigrid_proforma_naturaleza_por_producto == esperado


@pytest.mark.parametrize(
    "valor",
    ["SM9999=SM99", "SM9999:SM99,SB9999:SB99", '["SM9999", "SM99"]', "[]", '"SM99"',
     '{"SM9999": 99}', '{"SM9999": ""}', '{"": "SM99"}', '{"SM9999": "SM99", "SM9999": "SB99"}', 42],
)
def test_f007_r4_naturaleza_que_no_es_objeto_no_arranca(valor: object) -> None:
    with pytest.raises(ValidationError):
        ajustes(SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO=valor)


@pytest.mark.parametrize(
    "valor", ["SM9999=SM99", '["SM9999"]', '{"SM9999": 1}', '{"SM9999": "SM99", "SM9999": "SB99"}']
)
def test_f007_r4_naturaleza_mal_escrita_en_el_entorno_no_arranca(
    monkeypatch: pytest.MonkeyPatch, valor: str
) -> None:
    monkeypatch.setenv("SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO", valor)
    with pytest.raises((ValidationError, SettingsError)):
        ajustes()


@pytest.mark.parametrize("valor", ["muchas", "1.5"])
def test_f007_r4_el_tope_de_lineas_es_un_entero(valor: str) -> None:
    with pytest.raises(ValidationError):
        ajustes(SIGRID_PROFORMA_MAX_LINEAS=valor)


def test_f007_r4_ninguna_existente_cambia() -> None:
    settings = ajustes()
    assert settings.sigrid_domain_write_enabled is False
    assert settings.sigrid_albaran_write_enabled is False
    assert settings.sigrid_albaran_prefijos_referencia == []
    assert settings.sigrid_albaran_productos_sin_contrato == []
    assert settings.sigrid_albaran_empresas_obra == []
    assert settings.sigrid_albaran_max_lineas == 100
    assert settings.sigrid_albaran_naturaleza_por_producto == {}
    assert settings.sigrid_albaran_empide == 2425207
    assert settings.allowed_write_databases == []
    assert settings.domain_write_max_retries == 3


def test_f007_r4_las_de_proforma_no_abren_las_de_albaran(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave, valor in _DESPLIEGUE.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setenv("SIGRID_PROFORMA_WRITE_ENABLED", "true")
    settings = ajustes()
    assert settings.sigrid_albaran_write_enabled is False
    assert settings.sigrid_albaran_prefijos_referencia == []
    assert settings.sigrid_albaran_productos_sin_contrato == []


def test_f007_r4_el_fichero_de_ejemplo_declara_las_cinco_cerradas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valores = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))["Values"]
    assert {clave: valores.get(clave) for clave in _CLAVES_NUEVAS} == {
        "SIGRID_PROFORMA_WRITE_ENABLED": "false",
        "SIGRID_PROFORMA_PREFIJOS_REFERENCIA": "[]",
        "SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO": "[]",
        "SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO": "{}",
        "SIGRID_PROFORMA_MAX_LINEAS": "500",
    }
    for clave in _CLAVES_NUEVAS:
        monkeypatch.setenv(clave, valores[clave])
    settings = ajustes()
    assert settings.sigrid_proforma_write_enabled is False
    assert settings.sigrid_proforma_prefijos_referencia == []
    assert settings.sigrid_proforma_naturaleza_por_producto == {}
    assert settings.sigrid_proforma_max_lineas == 500
