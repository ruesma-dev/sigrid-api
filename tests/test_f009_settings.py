# tests/test_f009_settings.py
"""
F-009 · R10: las seis App Settings nuevas del modo extendido de
`sigrid/albaran`, con defecto CERRADO, y la promesa de que ninguna existente
cambia.

Sin red y sin base de datos. Como en F-004 (lección de su T14c) y F-006, ANTES
de cada test se borra del entorno toda clave que `Settings` reconozca y se
construye con `_env_file=None`: lo que se mide es el defecto del código, no lo
que tenga puesta la máquina ni lo que la campaña de mutación vuelque del `.env`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError
from pydantic_settings.sources import SettingsError

from config.settings import Settings

_RAIZ = Path(__file__).resolve().parents[1]

#: Lo mínimo que `Settings` exige para arrancar. Ninguna credencial real.
_MINIMO = {
    "SQL_DRIVER": "ODBC Driver 18 for SQL Server",
    "SQL_SERVER_HOST": "servidor.de.mentira",
    "SQL_SERVER_PORT": 1433,
    "SQL_SERVER_USERNAME": "usuario_de_mentira",
    "SQL_SERVER_PASSWORD": "no-es-una-credencial",
}

#: Las seis claves de R10.
_CLAVES_NUEVAS = (
    "SIGRID_ALBARAN_WRITE_ENABLED",
    "SIGRID_ALBARAN_PREFIJOS_REFERENCIA",
    "SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO",
    "SIGRID_ALBARAN_EMPRESAS_OBRA",
    "SIGRID_ALBARAN_MAX_LINEAS",
    "SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO",
)

#: Los valores de despliegue de T19 (R10, entre paréntesis), tal como irán en
#: las App Settings: solo JSON.
_DESPLIEGUE = {
    "SIGRID_ALBARAN_WRITE_ENABLED": "false",
    "SIGRID_ALBARAN_PREFIJOS_REFERENCIA": '["ALB-"]',
    "SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO": '["MA9999", "QA9999", "XA9999"]',
    "SIGRID_ALBARAN_EMPRESAS_OBRA": "[1]",
    "SIGRID_ALBARAN_MAX_LINEAS": "100",
    "SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO": (
        '{"MA9999": "MA99", "QA9999": "QA99", "XA9999": "XA99"}'
    ),
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


# --- R10: los seis ajustes nuevos, con defecto cerrado -----------------------


def test_f009_r10_los_seis_ajustes_nuevos_arrancan_con_defecto_cerrado() -> None:
    settings = ajustes()

    assert settings.sigrid_albaran_write_enabled is False
    assert settings.sigrid_albaran_prefijos_referencia == []
    assert settings.sigrid_albaran_productos_sin_contrato == []
    assert settings.sigrid_albaran_empresas_obra == []
    assert settings.sigrid_albaran_max_lineas == 100
    assert settings.sigrid_albaran_naturaleza_por_producto == {}


def test_f009_r10_los_valores_de_despliegue_llegan_por_el_entorno(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Las App Settings de T19 entran por el entorno, en JSON, y se leen tal cual."""
    for clave, valor in _DESPLIEGUE.items():
        monkeypatch.setenv(clave, valor)

    settings = ajustes()

    assert settings.sigrid_albaran_write_enabled is False
    assert settings.sigrid_albaran_prefijos_referencia == ["ALB-"]
    assert settings.sigrid_albaran_productos_sin_contrato == ["MA9999", "QA9999", "XA9999"]
    assert settings.sigrid_albaran_empresas_obra == [1]
    assert settings.sigrid_albaran_max_lineas == 100
    assert settings.sigrid_albaran_naturaleza_por_producto == {
        "MA9999": "MA99",
        "QA9999": "QA99",
        "XA9999": "XA99",
    }


def test_f009_r10_los_ajustes_se_leen_de_su_alias() -> None:
    settings = ajustes(SIGRID_ALBARAN_WRITE_ENABLED="true", SIGRID_ALBARAN_MAX_LINEAS="7")
    assert settings.sigrid_albaran_write_enabled is True
    assert settings.sigrid_albaran_max_lineas == 7


@pytest.mark.parametrize(
    "clave, atributo",
    [
        ("SIGRID_ALBARAN_PREFIJOS_REFERENCIA", "sigrid_albaran_prefijos_referencia"),
        ("SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO", "sigrid_albaran_productos_sin_contrato"),
    ],
)
@pytest.mark.parametrize(
    "valor, esperado",
    [
        ('["ALB-"]', ["ALB-"]),
        ('[" ALB- ", "OTRO"]', ["ALB-", "OTRO"]),
        ("", []),
        (None, []),
        (["ALB-"], ["ALB-"]),
    ],
)
def test_f009_r10_las_listas_de_texto_usan_parse_string_list(
    clave: str, atributo: str, valor: object, esperado: list[str]
) -> None:
    assert getattr(ajustes(**{clave: valor}), atributo) == esperado


@pytest.mark.parametrize(
    "valor, esperado",
    [("[1]", [1]), ("[1, 2]", [1, 2]), ("1,2", [1, 2]), ("", []), (None, []), ([3], [3])],
)
def test_f009_r10_empresas_obra_usa_parse_int_list(valor: object, esperado: list[int]) -> None:
    assert ajustes(SIGRID_ALBARAN_EMPRESAS_OBRA=valor).sigrid_albaran_empresas_obra == esperado


@pytest.mark.parametrize("valor", ['["uno"]', "1,dos", '{"a": 1}'])
def test_f009_r10_empresas_obra_mal_escrita_no_arranca(valor: str) -> None:
    with pytest.raises(ValidationError):
        ajustes(SIGRID_ALBARAN_EMPRESAS_OBRA=valor)


# --- R10: el mapeo producto -> naturaleza (parse_string_dict) ----------------


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (None, {}),
        ("", {}),
        ("   ", {}),
        ("{}", {}),
        ('{"MA9999": "MA99"}', {"MA9999": "MA99"}),
        ('{" MA9999 ": " MA99 ", "QA9999": "QA99"}', {"MA9999": "MA99", "QA9999": "QA99"}),
        ({"XA9999": "XA99"}, {"XA9999": "XA99"}),
        ({}, {}),
    ],
)
def test_f009_r10_naturaleza_por_producto_objeto_json_de_textos(
    valor: object, esperado: dict[str, str]
) -> None:
    settings = ajustes(SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO=valor)
    assert settings.sigrid_albaran_naturaleza_por_producto == esperado


@pytest.mark.parametrize(
    "valor",
    [
        "MA9999=MA99",                              # ni JSON
        "MA9999:MA99,QA9999:QA99",                  # CSV
        '["MA9999", "MA99"]',                       # lista
        "[]",                                       # lista vacía: no es un objeto
        '[["MA9999", "MA99"]]',
        '"MA99"',                                   # texto JSON suelto
        "{MA9999: MA99}",                           # JSON roto
        '{"MA9999": 99}',                           # valor que no es texto
        '{"MA9999": null}',
        '{"MA9999": ["MA99"]}',
        '{"MA9999": ""}',                           # valor vacío
        '{"MA9999": "   "}',
        '{"": "MA99"}',                             # clave vacía
        '{" ": "MA99"}',
        '{"MA9999": "MA99", "MA9999": "QA99"}',     # clave repetida
        '{"MA9999": "MA99", " MA9999": "QA99"}',    # repetida tras recortar
        ["MA9999", "MA99"],
        {"MA9999": 1},
        {"MA9999": ""},
        {1: "MA99"},
        42,
    ],
)
def test_f009_r10_naturaleza_mal_escrita_no_arranca(valor: object) -> None:
    """Objeto JSON de textos no vacíos, o el proceso no arranca (design §Ficheros
    a modificar): un mapeo a medias abriría a medias las sin vincular."""
    with pytest.raises(ValidationError):
        ajustes(SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO=valor)


@pytest.mark.parametrize(
    "valor",
    ["MA9999=MA99", '["MA9999"]', '{"MA9999": 1}', '{"MA9999": "MA99", "MA9999": "QA99"}'],
)
def test_f009_r10_naturaleza_mal_escrita_en_el_entorno_no_arranca(
    monkeypatch: pytest.MonkeyPatch, valor: str
) -> None:
    """Por el entorno (como llega la App Setting) tampoco arranca: o lo para el
    JSON de pydantic-settings o lo para el validador."""
    monkeypatch.setenv("SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO", valor)
    with pytest.raises((ValidationError, SettingsError)):
        ajustes()


# --- R10: ninguna App Setting existente cambia --------------------------------


def test_f009_r10_ninguna_existente_cambia() -> None:
    settings = ajustes()
    assert settings.sigrid_domain_write_enabled is False
    assert settings.sigrid_albaran_empide == 2425207
    assert settings.domain_write_max_retries == 3
    assert settings.applock_timeout_ms == 10000
    assert settings.allowed_write_databases == []
    assert settings.sigrid_document_write_enabled is False
    assert settings.sigrid_reclamacion_write_enabled is False
    assert settings.sigrid_reclamacion_prefijos_referencia == []
    assert settings.sigrid_document_allowed_contip == []


def test_f009_r10_el_fichero_de_ejemplo_declara_las_seis_claves_cerradas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`local.settings.sample.json` (R36) trae las seis, en JSON, y con ellas
    `Settings` arranca con el defecto cerrado."""
    ejemplo = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))
    valores = ejemplo["Values"]

    assert {clave: valores.get(clave) for clave in _CLAVES_NUEVAS} == {
        "SIGRID_ALBARAN_WRITE_ENABLED": "false",
        "SIGRID_ALBARAN_PREFIJOS_REFERENCIA": "[]",
        "SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO": "[]",
        "SIGRID_ALBARAN_EMPRESAS_OBRA": "[]",
        "SIGRID_ALBARAN_MAX_LINEAS": "100",
        "SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO": "{}",
    }
    for clave in _CLAVES_NUEVAS:
        monkeypatch.setenv(clave, valores[clave])
    settings = ajustes()
    assert settings.sigrid_albaran_write_enabled is False
    assert settings.sigrid_albaran_prefijos_referencia == []
    assert settings.sigrid_albaran_productos_sin_contrato == []
    assert settings.sigrid_albaran_empresas_obra == []
    assert settings.sigrid_albaran_max_lineas == 100
    assert settings.sigrid_albaran_naturaleza_por_producto == {}
