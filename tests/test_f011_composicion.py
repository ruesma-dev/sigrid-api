# tests/test_f011_composicion.py
"""
F-011 · R7: `build_dependencies()` entrega a `ReadDocumentUseCase` el MISMO
objeto `Settings` que a `ExecuteSqlQueryUseCase` (la lista de `sql/read`).

`get_settings` se dobla con un `Settings.model_construct(...)`, que no lee ni
el entorno ni el `.env` (lección de F-004 T14c), y la caché de
`build_dependencies` se limpia antes y después para no contaminar otros tests.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

import function_app
from config.settings import Settings
from domain.models.document_models import BaseNoPermitidaError
from domain.models.sql_models import DocumentReadRequest


@pytest.fixture
def ajustes_propios(monkeypatch: pytest.MonkeyPatch) -> Iterator[Settings]:
    propios = Settings.model_construct(
        allowed_databases=["solo_f011"],
        allowed_write_databases=["escritura_f011"],
        sigrid_document_write_database="documental_f011",
    )
    monkeypatch.setattr(function_app, "get_settings", lambda: propios)
    function_app.build_dependencies.cache_clear()
    yield propios
    function_app.build_dependencies.cache_clear()


def test_f011_r7_el_caso_de_uso_documental_recibe_el_settings_de_la_aplicacion(
    ajustes_propios: Settings,
) -> None:
    settings, _, sql_use_case, document_use_case, *_ = function_app.build_dependencies()
    assert settings is ajustes_propios
    assert document_use_case._settings is ajustes_propios
    assert document_use_case._settings is sql_use_case._query_guard._settings


def test_f011_r7_valida_con_allowed_databases_y_no_con_las_de_escritura(
    ajustes_propios: Settings,
) -> None:
    _, _, _, document_use_case, *_ = function_app.build_dependencies()
    for database in ("escritura_f011", "documental_f011"):
        peticion = DocumentReadRequest.model_validate(
            {"database": database, "table": "gra", "id_column": "ide", "id_value": 1, "blob_column": "ima"}
        )
        with pytest.raises(BaseNoPermitidaError) as info:
            document_use_case.run(peticion)
        assert str(info.value) == (
            f"La base de datos '{database}' no está permitida. Permitidas: solo_f011"
        )
