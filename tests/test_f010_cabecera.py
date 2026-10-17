# tests/test_f010_cabecera.py
"""
F-010 · R1-R4: la cabecera `X-Document-Filename` y `Content-Disposition` de
`binary_file_response`.

Sin red ni base de datos: se construye la respuesta y se leen sus cabeceras.
El 500 vacío del host de Functions no se reproduce aquí (ñ y á son latin-1 y
`func.HttpResponse` las admite); el criterio verificable es que la cabecera
sea ASCII imprimible y que `unquote` la devuelva al nombre original.
"""
from __future__ import annotations

from urllib.parse import quote, unquote

import pytest

from interface_adapters.http import http_response_factory
from interface_adapters.http.http_response_factory import binary_file_response

#: Nombres obligatorios de R1/R2: ñ, á, emoji, CJK, `%`, control 0x1F y DEL 0x7F.
_NOMBRES_DIFICILES = [
    "Factura año señal.pdf",
    "árbol.pdf",
    "informe \U0001F600.pdf",
    "合同.pdf",
    "100% real.pdf",
    "a%20b.pdf",
    "control\x1fsep.pdf",
    "borrar\x7f.pdf",
    "%",
    "%%25%",
]

_CONTENIDO = b"%PDF-1.4 contenido"


def respuesta(nombre: str, disposition: str = "attachment"):
    return binary_file_response(
        content=_CONTENIDO,
        content_type="application/pdf",
        file_name=nombre,
        disposition=disposition,
    )


def cabecera(nombre: str) -> str:
    return respuesta(nombre).headers["X-Document-Filename"]


def es_ascii_imprimible(texto: str) -> bool:
    return all(0x20 <= ord(caracter) <= 0x7E for caracter in texto)


# --- R1: solo ASCII imprimible -----------------------------------------------


@pytest.mark.parametrize("nombre", _NOMBRES_DIFICILES)
def test_f010_r1_la_cabecera_es_ascii_imprimible(nombre: str) -> None:
    assert es_ascii_imprimible(cabecera(nombre))


def test_f010_r1_cada_control_y_del_viajan_codificados() -> None:
    for codigo in [*range(0x20), 0x7F]:
        nombre = f"x{chr(codigo)}y"
        assert cabecera(nombre) == f"x%{codigo:02X}y"


def test_f010_r1_el_primer_caracter_no_ascii_viaja_codificado() -> None:
    # 0x80 en UTF-8 son dos bytes: frontera superior del rango seguro.
    assert cabecera("\x80") == "%C2%80"


# --- R2: unquote devuelve el original, sin ambigüedad ------------------------


@pytest.mark.parametrize("nombre", _NOMBRES_DIFICILES)
def test_f010_r2_unquote_devuelve_el_nombre_original(nombre: str) -> None:
    assert unquote(cabecera(nombre), encoding="utf-8", errors="strict") == nombre


def test_f010_r2_el_porcentaje_literal_viaja_como_25() -> None:
    assert cabecera("a%20b.pdf") == "a%2520b.pdf"
    assert cabecera("100% real.pdf") == "100%25 real.pdf"


def test_f010_r2_los_no_ascii_viajan_en_utf8() -> None:
    assert cabecera("Factura año señal.pdf") == "Factura a%C3%B1o se%C3%B1al.pdf"
    assert cabecera("\U0001F600") == "%F0%9F%98%80"


# --- R3: los nombres ASCII sin `%` viajan idénticos --------------------------


@pytest.mark.parametrize(
    "nombre",
    ["Contrato 2024 (v2).pdf", 'Oferta [final]; "x".pdf', "simple.pdf", " ", "~"],
)
def test_f010_r3_nombre_ascii_sin_porcentaje_viaja_identico(nombre: str) -> None:
    assert cabecera(nombre) == nombre


def test_f010_r3_todo_el_ascii_imprimible_salvo_porcentaje_viaja_identico() -> None:
    nombre = "".join(chr(c) for c in range(0x20, 0x7F) if chr(c) != "%")
    assert cabecera(nombre) == nombre


def test_f010_r3_la_funcion_publica_es_la_que_usa_la_cabecera() -> None:
    funcion = http_response_factory.filename_header_value
    for nombre in [*_NOMBRES_DIFICILES, "Contrato 2024 (v2).pdf"]:
        assert funcion(nombre) == cabecera(nombre)


# --- R4: Content-Disposition --------------------------------------------------


@pytest.mark.parametrize("nombre", [*_NOMBRES_DIFICILES, "Contrato 2024 (v2).pdf"])
@pytest.mark.parametrize("disposition", ["attachment", "inline"])
def test_f010_r4_content_disposition_sin_barra_es_la_de_hoy(nombre: str, disposition: str) -> None:
    valor = respuesta(nombre, disposition).headers["Content-Disposition"]
    assert valor == f"{disposition}; filename*=UTF-8''{quote(nombre)}"


def test_f010_r4_la_barra_viaja_como_2f() -> None:
    valor = respuesta("carpeta/fichero.pdf").headers["Content-Disposition"]
    assert valor == "attachment; filename*=UTF-8''carpeta%2Ffichero.pdf"


def test_f010_r4_tamano_cuerpo_y_tipo_no_cambian() -> None:
    r = respuesta("Factura año señal.pdf")
    assert r.status_code == 200
    assert r.get_body() == _CONTENIDO
    assert r.headers["X-Document-Size"] == str(len(_CONTENIDO))
    assert r.mimetype == "application/pdf"
