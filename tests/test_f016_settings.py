# tests/test_f016_settings.py
"""
F-016 T4 · R4: `SIGRID_PROFORMA_ORIGEN_ENABLED`, la llave propia del commit a
origen, con defecto CERRADO y booleana como las demas; ninguna App Setting
existente cambia (D10).

Como `test_f007_settings.py`: antes de cada test se borra del entorno toda
clave que `Settings` reconozca y se construye con `_env_file=None`.
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

_CLAVE = "SIGRID_PROFORMA_ORIGEN_ENABLED"


def _claves_que_settings_reconoce() -> frozenset[str]:
    nombres: set[str] = set()
    for nombre, campo in Settings.model_fields.items():
        for candidato in (nombre, campo.alias, campo.validation_alias):
            if isinstance(candidato, str):
                nombres.update({candidato, candidato.upper(), candidato.lower()})
    return frozenset(nombres)


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave in _claves_que_settings_reconoce() | {_CLAVE}:
        monkeypatch.delenv(clave, raising=False)


def ajustes(**extra: object) -> Settings:
    return Settings(_env_file=None, **{**_MINIMO, **extra})


def test_f016_r4_la_llave_de_origen_arranca_cerrada() -> None:
    assert ajustes().sigrid_proforma_origen_enabled is False


@pytest.mark.parametrize(("valor", "esperado"),
                         [("true", True), ("1", True), ("false", False), ("0", False)])
def test_f016_r4_se_lee_de_su_alias_como_booleano(valor: str, esperado: bool,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    assert ajustes(**{_CLAVE: valor}).sigrid_proforma_origen_enabled is esperado
    monkeypatch.setenv(_CLAVE, valor)
    assert ajustes().sigrid_proforma_origen_enabled is esperado


@pytest.mark.parametrize("valor", ["quizas", "2", "[]"])
def test_f016_r4_un_valor_que_no_es_booleano_no_arranca(valor: str) -> None:
    with pytest.raises(ValidationError):
        ajustes(**{_CLAVE: valor})


def test_f016_r4_ninguna_existente_cambia() -> None:
    settings = ajustes()
    assert settings.sigrid_domain_write_enabled is False
    assert settings.sigrid_albaran_write_enabled is False
    assert settings.sigrid_proforma_write_enabled is False
    assert settings.sigrid_proforma_prefijos_referencia == []
    assert settings.sigrid_proforma_productos_sin_contrato == []
    assert settings.sigrid_proforma_naturaleza_por_producto == {}
    assert settings.sigrid_proforma_max_lineas == 500


def test_f016_r4_abrir_la_de_origen_no_abre_la_de_proformas(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_CLAVE, "true")
    settings = ajustes()
    assert settings.sigrid_proforma_origen_enabled is True
    assert settings.sigrid_proforma_write_enabled is False
    assert settings.sigrid_domain_write_enabled is False


def test_f016_r4_el_fichero_de_ejemplo_la_declara_cerrada(monkeypatch: pytest.MonkeyPatch) -> None:
    valores = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))["Values"]
    assert valores.get(_CLAVE) == "false"
    monkeypatch.setenv(_CLAVE, valores[_CLAVE])
    assert ajustes().sigrid_proforma_origen_enabled is False
