# tests/test_f010_modelo.py
"""
F-010 · R6-R9 y R12 (`localizacion()`): el campo `key` de `DocumentReadRequest`
y su exclusión con `id_column`/`id_value`.

Modelo puro: ni red, ni base de datos, ni ajustes.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.models import sql_models
from domain.models.sql_models import DocumentReadRequest

_BASE: dict[str, Any] = {
    "database": "ruesma_rep",
    "table": "gra",
    "blob_column": "ima",
}


def peticion(**campos: Any) -> DocumentReadRequest:
    return DocumentReadRequest.model_validate({**_BASE, **campos})


def rechaza(**campos: Any) -> ValidationError:
    with pytest.raises(ValidationError) as info:
        peticion(**campos)
    return info.value


# --- R6: `key` admitido -------------------------------------------------------


def test_f010_r6_key_con_entero_y_texto_se_acepta() -> None:
    p = peticion(key={"emp": 1, "cod": "ABC"})
    assert p.key == {"emp": 1, "cod": "ABC"}
    assert p.id_column is None
    assert p.id_value is None


def test_f010_r6_los_nombres_se_recortan_y_el_orden_se_conserva() -> None:
    p = peticion(key={" cod ": "X", "\temp": 2, "b": 3})
    assert list(p.key) == ["cod", "emp", "b"]
    assert p.key == {"cod": "X", "emp": 2, "b": 3}


def test_f010_r6_sin_coercion_entre_texto_y_entero() -> None:
    p = peticion(key={"a": "123", "b": 123})
    assert p.key["a"] == "123" and isinstance(p.key["a"], str)
    assert p.key["b"] == 123 and isinstance(p.key["b"], int)


@pytest.mark.parametrize("valor", [None, True, False, 1.5, 1.0, [1], {"x": 1}])
def test_f010_r6_valor_de_tipo_no_admitido_se_rechaza(valor: Any) -> None:
    rechaza(key={"emp": valor})


def test_f010_r6_key_que_no_es_objeto_se_rechaza() -> None:
    rechaza(key=["emp", 1])
    rechaza(key="emp=1")


# --- R7: `key` es excluyente con `id_column`/`id_value` -----------------------


def test_f010_r7_key_con_id_column_se_rechaza() -> None:
    error = rechaza(key={"emp": 1}, id_column="ide")
    assert "key es excluyente con id_column/id_value." in str(error)


def test_f010_r7_key_con_id_value_se_rechaza() -> None:
    error = rechaza(key={"emp": 1}, id_value=5)
    assert "key es excluyente con id_column/id_value." in str(error)


def test_f010_r7_key_con_id_value_null_tambien_se_rechaza() -> None:
    rechaza(key={"emp": 1}, id_value=None)


def test_f010_r7_key_con_las_dos_se_rechaza() -> None:
    rechaza(key={"emp": 1}, id_column="ide", id_value=5)


# --- R8: falta la localización o está a medias --------------------------------


def test_f010_r8_sin_key_ni_id_column_se_rechaza() -> None:
    error = rechaza()
    assert "Indica key, o id_column con id_value." in str(error)


def test_f010_r8_id_column_sin_id_value_se_rechaza() -> None:
    error = rechaza(id_column="ide")
    assert "Indica key, o id_column con id_value." in str(error)


def test_f010_r8_id_value_sin_id_column_se_rechaza() -> None:
    error = rechaza(id_value=365617)
    assert "Indica key, o id_column con id_value." in str(error)


def test_f010_r8_id_column_con_id_value_null_se_sigue_aceptando() -> None:
    p = peticion(id_column="ide", id_value=None)
    assert p.id_column == "ide"
    assert p.id_value is None
    assert p.localizacion() == {"ide": None}


def test_f010_r8_id_column_vacia_se_rechaza_como_hoy() -> None:
    rechaza(id_column="", id_value=1)
    rechaza(id_column="   ", id_value=1)


def test_f010_r8_id_column_de_un_caracter_se_acepta_como_hoy() -> None:
    # Frontera de min_length=1: superviviente 1 de la primera campaña.
    assert peticion(id_column="a", id_value=1).localizacion() == {"a": 1}


def test_f010_r8_id_column_se_recorta_como_hoy() -> None:
    assert peticion(id_column="  ide ", id_value=1).id_column == "ide"


# --- R9: forma de `key` -------------------------------------------------------


def test_f010_r9_el_tope_es_cuatro() -> None:
    assert sql_models.MAX_COLUMNAS_CLAVE == 4


def test_f010_r9_cuatro_entradas_pasan() -> None:
    clave = {"a": 1, "b": 2, "c": 3, "d": 4}
    assert peticion(key=clave).key == clave


def test_f010_r9_cinco_entradas_no() -> None:
    rechaza(key={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5})


def test_f010_r9_una_entrada_pasa() -> None:
    assert peticion(key={"ide": 365617}).key == {"ide": 365617}


def test_f010_r9_objeto_vacio_se_rechaza() -> None:
    rechaza(key={})


@pytest.mark.parametrize("nombre", ["", "   ", "\t"])
def test_f010_r9_nombre_en_blanco_se_rechaza(nombre: str) -> None:
    rechaza(key={nombre: 1})


def test_f010_r9_nombre_en_blanco_entre_validos_se_rechaza() -> None:
    rechaza(key={"emp": 1, " ": 2})


@pytest.mark.parametrize(
    "clave",
    [
        {"emp": 1, " EMP": 2},
        {"Cod": "a", "cOD": "b"},
        {"emp ": 1, " emp": 2},
        {"a": 1, "b": 2, "c": 3, "B": 4},
    ],
)
def test_f010_r9_nombres_duplicados_sin_distinguir_mayusculas_se_rechazan(clave: dict) -> None:
    rechaza(key=clave)


def test_f010_r9_duplicado_detectado_con_casefold_y_no_con_lower() -> None:
    # "ß".casefold() == "ss" == "SS".casefold(); con lower() pasarían por distintos.
    rechaza(key={"ß": 1, "SS": 2})


# --- R12: localizacion() ------------------------------------------------------


def test_f010_r12_localizacion_desde_id_column_es_una_clave_de_una_columna() -> None:
    p = peticion(id_column="ide", id_value=365617)
    assert p.localizacion() == {"ide": 365617}


def test_f010_r12_localizacion_desde_key_es_la_key_en_su_orden() -> None:
    p = peticion(key={"emp": 1, "cod": "ABC"})
    localizacion = p.localizacion()
    assert localizacion == {"emp": 1, "cod": "ABC"}
    assert list(localizacion) == ["emp", "cod"]


def test_f010_r12_localizacion_es_una_copia() -> None:
    p = peticion(key={"emp": 1})
    p.localizacion()["otra"] = 2
    assert p.key == {"emp": 1}


def test_f010_r12_los_demas_campos_no_cambian() -> None:
    p = peticion(id_column="ide", id_value=1)
    assert p.schema == "dbo"
    assert p.filename_columns == ["nomori", "nom"]
    assert p.disposition == "attachment"


def test_f010_r12_extra_se_sigue_ignorando() -> None:
    p = peticion(id_column="ide", id_value=1, campo_de_mas="x")
    assert not hasattr(p, "campo_de_mas")


# --- Los errores de localización se vuelcan a JSON (la ruta lo hace) ----------


@pytest.mark.parametrize(
    "campos",
    [
        {"key": {"emp": 1}, "id_column": "ide"},
        {},
        {"id_column": "ide"},
        {"key": {}},
        {"key": {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}},
        {"key": {" ": 1}},
        {"key": {"emp": 1, "EMP": 2}},
        {"key": {"emp": None}},
    ],
)
def test_f010_r7_r9_los_errores_se_serializan_a_json(campos: dict[str, Any]) -> None:
    import json

    error = rechaza(**campos)
    json.dumps(error.errors())


def test_f010_r9_los_mensajes_nombran_el_motivo() -> None:
    assert "key admite como mucho 4 columnas." in str(rechaza(key={c: 1 for c in "abcde"}))
    assert "key repite la columna EMP." in str(rechaza(key={"emp": 1, " EMP ": 2}))


# --- Nulos explícitos: `null` equivale a ausente en id_column y en key ---------


def test_f010_r6_key_null_explicito_equivale_a_no_traerla() -> None:
    p = peticion(key=None, id_column="ide", id_value=7)
    assert p.key is None
    assert p.localizacion() == {"ide": 7}


def test_f010_r8_key_null_sin_id_column_se_rechaza() -> None:
    rechaza(key=None)


def test_f010_r7_id_column_null_explicito_con_key_equivale_a_no_traerla() -> None:
    p = peticion(key={"emp": 1}, id_column=None)
    assert p.id_column is None
    assert p.localizacion() == {"emp": 1}


def test_f010_r8_id_column_null_con_id_value_se_rechaza() -> None:
    rechaza(id_column=None, id_value=1)


def test_f010_r6_un_identificador_null_ya_no_se_convierte_en_el_texto_none() -> None:
    error = rechaza(id_column="ide", id_value=1, table=None)
    assert "table" in str(error)
