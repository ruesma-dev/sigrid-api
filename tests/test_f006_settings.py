# tests/test_f006_settings.py
"""
F-006 · R4 y R5: las cuatro App Settings nuevas de `sigrid/partes-reclamacion`
y la promesa de que ninguna existente cambia.

Sin red y sin base de datos. Como en F-004 (lección de su T14c), ANTES de cada
test se borra del entorno toda clave que `Settings` reconozca y se construye
con `_env_file=None`: lo que se mide es el defecto del código, no lo que tenga
puesta la máquina ni lo que la campaña de mutación vuelque del `.env`.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

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

#: Las cuatro claves de R4.
_CLAVES_NUEVAS = (
    "SIGRID_RECLAMACION_WRITE_ENABLED",
    "SIGRID_RECLAMACION_MAX_PARTES",
    "SIGRID_RECLAMACION_PREFIJOS_REFERENCIA",
    "SIGRID_RECLAMACION_PRESUPUESTO_SEGUNDOS",
)


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


# --- R4: los cuatro ajustes nuevos, con defecto seguro -----------------------


def test_f006_r4_los_cuatro_ajustes_nuevos_arrancan_con_defecto_seguro() -> None:
    settings = ajustes()

    assert settings.sigrid_reclamacion_write_enabled is False
    assert settings.sigrid_reclamacion_max_partes == 50
    assert settings.sigrid_reclamacion_prefijos_referencia == []
    assert settings.sigrid_reclamacion_presupuesto_segundos == 150


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ('["PVI-"]', ["PVI-"]),
        ('["PVI-", "OTRO-"]', ["PVI-", "OTRO-"]),
        ("PVI-", ["PVI-"]),
        ("PVI-,OTRO-", ["PVI-", "OTRO-"]),
        (" PVI- , OTRO- ", ["PVI-", "OTRO-"]),
        ("", []),
        (None, []),
        (["PVI-"], ["PVI-"]),
    ],
)
def test_f006_r4_los_prefijos_aceptan_json_y_csv(valor: object, esperado: list[str]) -> None:
    settings = ajustes(SIGRID_RECLAMACION_PREFIJOS_REFERENCIA=valor)
    assert settings.sigrid_reclamacion_prefijos_referencia == esperado


def test_f006_r4_los_ajustes_se_leen_de_su_alias() -> None:
    settings = ajustes(
        SIGRID_RECLAMACION_WRITE_ENABLED="true",
        SIGRID_RECLAMACION_MAX_PARTES="7",
        SIGRID_RECLAMACION_PRESUPUESTO_SEGUNDOS="30",
    )
    assert settings.sigrid_reclamacion_write_enabled is True
    assert settings.sigrid_reclamacion_max_partes == 7
    assert settings.sigrid_reclamacion_presupuesto_segundos == 30


def test_f006_r4_el_entorno_tambien_llega(monkeypatch: pytest.MonkeyPatch) -> None:
    """La App Setting de despliegue (`["PVI-"]`) entra por el entorno, no por kwargs."""
    monkeypatch.setenv("SIGRID_RECLAMACION_PREFIJOS_REFERENCIA", '["PVI-"]')
    assert ajustes().sigrid_reclamacion_prefijos_referencia == ["PVI-"]


# --- R5: ninguna App Setting existente cambia --------------------------------


def test_f006_r5_allowed_write_databases_sigue_siendo_solo_ruesma() -> None:
    settings = ajustes(ALLOWED_WRITE_DATABASES="ruesma")
    assert settings.allowed_write_databases == ["ruesma"]
    # Los defectos de lo que ya existía no se mueven.
    assert settings.sigrid_domain_write_enabled is False
    assert settings.domain_write_max_retries == 3
    assert settings.applock_timeout_ms == 10000
    assert settings.sigrid_document_write_enabled is False


def test_f006_r5_el_fichero_de_ejemplo_declara_las_cuatro_claves_cerradas() -> None:
    ejemplo = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))
    valores = ejemplo["Values"]

    assert valores["ALLOWED_WRITE_DATABASES"] == "ruesma"
    for clave in _CLAVES_NUEVAS:
        assert clave in valores, f"falta {clave} en local.settings.sample.json"
    assert valores["SIGRID_RECLAMACION_WRITE_ENABLED"] == "false"
    assert valores["SIGRID_RECLAMACION_MAX_PARTES"] == "50"
    assert valores["SIGRID_RECLAMACION_PREFIJOS_REFERENCIA"] == ""
    assert valores["SIGRID_RECLAMACION_PRESUPUESTO_SEGUNDOS"] == "150"
