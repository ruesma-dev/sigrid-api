# tests/test_f004_settings.py
"""
F-004 · R4 y R5: las siete App Settings nuevas del endpoint
`sigrid/concepto-grafico` y la promesa de que ninguna existente cambia.

Sin red y sin base de datos. `Settings` se construye con los argumentos
mínimos por su alias (los kwargs de `__init__` mandan sobre el entorno en
pydantic-settings), y las claves nuevas se borran del entorno antes de cada
test para que lo que se mide sea el defecto del código y no lo que tenga
puesta la máquina.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

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

#: Las siete claves de R4, con su defecto seguro.
_CLAVES_NUEVAS = (
    "SIGRID_DOCUMENT_WRITE_ENABLED",
    "SIGRID_DOCUMENT_WRITE_DATABASE",
    "SIGRID_DOCUMENT_MAX_BYTES",
    "SIGRID_DOCUMENT_ALLOWED_MAGIC",
    "SIGRID_DOCUMENT_ALLOWED_CONTIP",
    "SIGRID_DOCUMENT_ALLOWED_GRATIPIDE",
    "SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS",
)


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch: pytest.MonkeyPatch) -> None:
    for clave in _CLAVES_NUEVAS:
        monkeypatch.delenv(clave, raising=False)
    monkeypatch.delenv("ALLOWED_WRITE_DATABASES", raising=False)


def ajustes(**extra: object) -> Settings:
    return Settings(**{**_MINIMO, **extra})


# --- R4: los siete ajustes nuevos, con defecto seguro ------------------------


def test_f004_r4_los_siete_ajustes_nuevos_arrancan_con_defecto_seguro() -> None:
    """Con el entorno mínimo, `Settings()` arranca y el endpoint queda cerrado."""
    settings = ajustes()

    assert settings.sigrid_document_write_enabled is False
    assert settings.sigrid_document_write_database == ""
    assert settings.sigrid_document_max_bytes == 10485760
    assert settings.sigrid_document_allowed_magic == ["%PDF-"]
    assert settings.sigrid_document_allowed_contip == []
    assert settings.sigrid_document_allowed_gratipide == []
    assert settings.sigrid_document_write_timeout_seconds == 120


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("[708]", [708]),
        ("[708, 707]", [708, 707]),
        ("708", [708]),
        ("708,707", [708, 707]),
        (" 708 , 707 ", [708, 707]),
        ("", []),
        ("   ", []),
        (None, []),
        ([708, "707"], [708, 707]),
        ([], []),
    ],
)
def test_f004_r4_parse_int_list_acepta_json_y_csv(valor: object, esperado: list[int]) -> None:
    settings = ajustes(SIGRID_DOCUMENT_ALLOWED_CONTIP=valor)
    assert settings.sigrid_document_allowed_contip == esperado


def test_f004_r4_parse_int_list_tambien_gobierna_la_lista_de_clases() -> None:
    settings = ajustes(SIGRID_DOCUMENT_ALLOWED_GRATIPIDE="35,34")
    assert settings.sigrid_document_allowed_gratipide == [35, 34]


@pytest.mark.parametrize("valor", ["treinta y cinco", "35,x", "[35, 'x']", "3.5", {"a": 1}])
def test_f004_r4_parse_int_list_rechaza_lo_que_no_es_entero(valor: object) -> None:
    """Ante una lista blanca que no se entiende, se falla al arrancar: una
    lista mal escrita que degradara a [] abriría la puerta en silencio."""
    with pytest.raises(ValidationError):
        ajustes(SIGRID_DOCUMENT_ALLOWED_GRATIPIDE=valor)


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ('["%PDF-"]', ["%PDF-"]),
        ("%PDF-", ["%PDF-"]),
        ("%PDF-,\\x89PNG", ["%PDF-", "\\x89PNG"]),
        ("", []),
    ],
)
def test_f004_r4_allowed_magic_reutiliza_parse_string_list(valor: str, esperado: list[str]) -> None:
    settings = ajustes(SIGRID_DOCUMENT_ALLOWED_MAGIC=valor)
    assert settings.sigrid_document_allowed_magic == esperado


def test_f004_r4_la_base_documental_se_lee_tal_cual() -> None:
    settings = ajustes(SIGRID_DOCUMENT_WRITE_DATABASE="ruesma_rep")
    assert settings.sigrid_document_write_database == "ruesma_rep"


# --- R5: ninguna App Setting existente cambia de valor ni de uso -------------


def test_f004_r5_allowed_write_databases_sigue_siendo_solo_la_de_negocio() -> None:
    settings = ajustes(
        ALLOWED_WRITE_DATABASES="ruesma",
        SIGRID_DOCUMENT_WRITE_DATABASE="ruesma_rep",
    )
    assert settings.allowed_write_databases == ["ruesma"]
    assert settings.sigrid_document_write_database not in settings.allowed_write_databases


def test_f004_r5_el_fichero_de_ejemplo_declara_las_siete_claves_cerradas() -> None:
    """`local.settings.sample.json` es la plantilla de despliegue: si ahí la
    escritura documental no viniera cerrada, T18 abriría la puerta sin querer."""
    ejemplo = json.loads((_RAIZ / "local.settings.sample.json").read_text(encoding="utf-8"))
    valores = ejemplo["Values"]

    assert valores["ALLOWED_WRITE_DATABASES"] == "ruesma"
    for clave in _CLAVES_NUEVAS:
        assert clave in valores, f"falta {clave} en local.settings.sample.json"
    assert valores["SIGRID_DOCUMENT_WRITE_ENABLED"] == "false"
    assert valores["SIGRID_DOCUMENT_ALLOWED_CONTIP"] == ""
    assert valores["SIGRID_DOCUMENT_ALLOWED_GRATIPIDE"] == ""
