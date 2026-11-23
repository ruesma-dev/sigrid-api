# tests/test_f007_filas.py
"""
F-007 T18 · huecos de la campana de mutacion (`progress/mutacion_F-007.md`) en
las piezas pequenas de `proforma_statements` y del caso de uso:

- las filas de LP1, LP3, LP4 y LP2 con columnas a NULL se leen como 0 o como
  texto vacio, nunca como otro numero (un `paride` 1 seria una partida real);
- las filas leidas y el contexto de R28 son inmutables por el camino;
- la tolerancia del precio de R14 incluye el borde y, fuera de el, no hay
  vuelta atras; el respaldo sin `ctrpro_ide` nombra la partida que no esta y
  da ambigua con dos;
- R20 (la del primer dia del periodo no es anterior), R21 (contrato de 1 euro),
  R23 (`es_proforma` con nulos) y R24 (lineas del existente con nulos).

Funciones puras: sin red ni base de datos.
"""
from __future__ import annotations

import dataclasses
from typing import Any

import pytest

from application.use_cases.create_proforma_use_case import _Contexto
from application.use_cases.proforma_statements import (
    ContratoCandidato,
    FalloIdentificacion,
    LineaContrato,
    ProformaRegistrada,
    anterior_por_linea,
    anterior_y_origen,
    es_proforma,
    identificar_linea,
    lineas_del_existente,
)
from domain.models.proforma_models import LineaProformaIn

# =====================================================================================
# Columnas a NULL
# =====================================================================================


def test_f007_t18_contrato_con_nulos() -> None:
    contrato = ContratoCandidato.de_fila((2793879, "CTSB26/0472", None, None, None, None))
    assert (contrato.fec, contrato.entcif, contrato.entres, contrato.nlin) == (0, "", "", 0)


def test_f007_t18_linea_de_contrato_con_nulos() -> None:
    linea = LineaContrato.de_fila((262990, 2793879, None, None, None, None, None, None, None, None))
    assert (linea.paride, linea.partida, linea.can, linea.pre, linea.tot, linea.unimed,
            linea.proide, linea.producto) == (0, "", 0.0, 0.0, 0.0, "", 0, "")


def test_f007_t18_proforma_registrada_con_nulos() -> None:
    proforma = ProformaRegistrada.de_fila((2831541, "AC26/25548", None, None, None, None))
    assert (proforma.fec, proforma.entref, proforma.totbas, proforma.docoritip) == (0, "", 0.0, 0)


def test_f007_t18_anterior_con_suma_nula() -> None:
    assert anterior_por_linea([(262990, None), (262996, 37.22)]) == {262990: 0.0, 262996: 37.22}


# =====================================================================================
# Inmutables
# =====================================================================================

_EJEMPLOS: dict[str, Any] = {
    "contrato": ContratoCandidato.de_fila((1, "C", 20260101, "B1", "X", 1)),
    "linea": LineaContrato.de_fila((1, 1, 1, "P", 1, 1, 1, "M3", 1, "SM1004")),
    "proforma": ProformaRegistrada.de_fila((1, "PROF26/00001", 20260831, "E", 1, 0)),
    "contexto": _Contexto(ctride=1, periodo=202608, importe_mes=1.0, otra_del_mes=False),
}


@pytest.mark.parametrize("nombre", sorted(_EJEMPLOS))
def test_f007_t18_lo_leido_y_el_contexto_no_cambian_por_el_camino(nombre: str) -> None:
    ejemplo = _EJEMPLOS[nombre]
    campo = dataclasses.fields(ejemplo)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(ejemplo, campo, 2)


# =====================================================================================
# Bordes de las tolerancias
# =====================================================================================


# =====================================================================================
# R14, respaldo sin `ctrpro_ide`
# =====================================================================================


def _de_contrato(ide: int, *, partida: str = "01.01", pre: float = 11.0) -> LineaContrato:
    return LineaContrato(ide=ide, docide=1, paride=1, partida=partida, can=10.0, pre=pre,
                         tot=10.0 * pre, unimed="M3", proide=1, producto="SM1004")


def _pedida(**campos: Any) -> LineaProformaIn:
    return LineaProformaIn(**{"referencia_linea": "F1", "cantidad": 1.0, "precio": 11.0,
                              "descripcion": "VERTIDO", "partida": "01.01",
                              "medicion_contrato": 10.0, **campos})


@pytest.mark.parametrize("precio", [11.0001, 10.9999])
def test_f007_t18_r14_el_precio_casa_con_el_borde(precio: float) -> None:
    contrato = [_de_contrato(1, pre=11.0), _de_contrato(2, pre=12.0)]
    assert identificar_linea(_pedida(precio=precio), contrato).ide == 1


@pytest.mark.parametrize("precio", [11.00011, 10.99989])
def test_f007_t18_r14_el_precio_fuera_del_borde_no_casa_ni_vuelve_atras(precio: float) -> None:
    # La unica de la partida «01.01» no se toma si el precio no casa (enmienda 1).
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(_pedida(precio=precio), [_de_contrato(1, pre=11.0)])
    assert exc.value.codigo == "linea_no_es_del_contrato"


def test_f007_t18_r14_dos_que_casan_son_ambiguas() -> None:
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(_pedida(), [_de_contrato(1), _de_contrato(2)])
    assert (exc.value.codigo, exc.value.candidatos) == ("linea_ambigua", [1, 2])


def test_f007_t18_r14_la_partida_que_no_esta_se_nombra() -> None:
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(_pedida(partida="99.99"), [_de_contrato(1)])
    assert exc.value.codigo == "linea_no_es_del_contrato"
    assert "'99.99'" in exc.value.mensaje


# =====================================================================================
# R20-R21 y R24 en sus bordes
# =====================================================================================


def _registrada(fec: int, totbas: float) -> ProformaRegistrada:
    return ProformaRegistrada(ide=fec, cod=f"PROF26/{fec % 100:05d}", fec=fec, entref="E",
                              totbas=totbas, docoritip=0)


def test_f007_t18_r20_la_del_primer_dia_del_periodo_no_es_anterior() -> None:
    origen, _avisos = anterior_y_origen(
        [_registrada(20260731, 50.0), _registrada(20260801, 100.0)],
        primer_dia=20260801, importe_mes=100.0, importe_contrato=1000.0, importe_anterior=None,
    )
    assert origen.importe_anterior_sigrid == 50.0


def test_f007_t18_r21_un_contrato_de_un_euro_tiene_porcentaje_y_avisos() -> None:
    origen, avisos = anterior_y_origen(
        [], primer_dia=20260801, importe_mes=2.0, importe_contrato=1.0, importe_anterior=None,
    )
    assert origen.porcentaje_contrato == 200.0
    assert [a.codigo for a in avisos] == ["supera_contrato_10"]


def test_f007_t18_r24_lineas_del_existente_con_nulos_y_vinculo_1() -> None:
    (resultado,) = lineas_del_existente([(1352729, 1, None, None, None, None)])
    assert resultado.model_dump(include={
        "proide", "almide", "producto", "cantidad", "precio", "total", "importe", "de_contrato",
        "ctrpro_ide", "linoriide",
    }) == {"proide": 0, "almide": 0, "producto": None, "cantidad": 0.0, "precio": 0.0,
           "total": 0.0, "importe": 0.0, "de_contrato": True, "ctrpro_ide": 1, "linoriide": 1}


@pytest.mark.parametrize(
    ("fila", "es"),
    [((1, "PROF26/00001", 141, 7), True), ((1, "PROF26/00001", None, 7), False),
     ((1, "AC26/00001", 0, 7), False), ((1, "PROF26/00001", 141, None), False)],
)
def test_f007_t18_r23_es_proforma_con_nulos(fila: tuple[Any, ...], es: bool) -> None:
    assert es_proforma(fila, 7) is es
