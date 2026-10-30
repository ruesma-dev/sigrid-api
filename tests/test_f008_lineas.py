# tests/test_f008_lineas.py
"""
F-008 · T3-T7: funciones puras de `factura_lineas` (vencimientos, linea de
origen, comparacion a origen, resolvedores por serie y constructor unico de la
linea sin origen). Sin red ni base; datos sinteticos y casos anonimos de M63.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from application.use_cases.factura_lineas import (
    fecha_de_vencimiento_valida,
    validar_vencimientos,
)
from domain.models.factura_models import FacturaError, Vencimiento


def _v(fecha: int, importe: float) -> Vencimiento:
    return Vencimiento(fecha=fecha, importe=importe)


# --------------------------------------------------------------------------- #
# T3 · vencimientos (R33-R35)
# --------------------------------------------------------------------------- #


def test_f008_r33_vencimientos_validos_no_dicen_nada() -> None:
    validar_vencimientos(
        [_v(20261115, 60.5), _v(20261215, 60.5)], fecha_factura=20261015, totpag=Decimal("121.00")
    )


def test_f008_r33_el_mismo_dia_de_la_factura_vale() -> None:
    validar_vencimientos([_v(20261015, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))


def test_f008_r33_730_dias_vale_y_731_no() -> None:
    # 2026-10-15 + 730 dias = 2028-10-14 (2028 es bisiesto).
    validar_vencimientos([_v(20281014, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20281015, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 0, "fecha": 20281015}


def test_f008_r33_anterior_a_la_factura_no_vale() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos(
            [_v(20261115, 5.0), _v(20261014, 5.0)], fecha_factura=20261015, totpag=Decimal("10")
        )
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 1, "fecha": 20261014}


def test_f008_r33_fecha_que_no_existe_no_vale() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20261131, 10.0)], fecha_factura=20261015, totpag=Decimal("10"))
    assert error.value.details["posicion"] == 0


def test_f008_r33_fechas_repetidas_no_valen() -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos(
            [_v(20261115, 5.0), _v(20261215, 2.0), _v(20261115, 3.0)],
            fecha_factura=20261015, totpag=Decimal("10"),
        )
    assert error.value.codigo == "vencimiento_no_valido"
    assert error.value.details == {"posicion": 2, "fecha": 20261115}


@pytest.mark.parametrize("totpag", ["10.01", "9.99"])
def test_f008_r33_la_suma_cuadra_con_un_centimo(totpag: str) -> None:
    validar_vencimientos([_v(20261115, 7.0), _v(20261215, 3.0)], fecha_factura=20261015,
                         totpag=Decimal(totpag))


@pytest.mark.parametrize("totpag", ["10.02", "9.98"])
def test_f008_r33_la_suma_no_cuadra_con_dos_centimos(totpag: str) -> None:
    with pytest.raises(FacturaError) as error:
        validar_vencimientos([_v(20261115, 7.0), _v(20261215, 3.0)], fecha_factura=20261015,
                             totpag=Decimal(totpag))
    assert error.value.codigo == "vencimientos_no_cuadran"
    assert error.value.details == {"suma_vencimientos": 10.0, "totpag": float(Decimal(totpag))}


def test_f008_r33_la_suma_se_hace_en_decimal() -> None:
    # 0,1 + 0,2 en binario es 0,30000000000000004.
    validar_vencimientos([_v(20261115, 0.1), _v(20261116, 0.2)], fecha_factura=20261015,
                         totpag=Decimal("0.30"))


@pytest.mark.parametrize("fecha,esperado", [
    (20261015, True), (20281014, True), (20281015, False), (20261014, False), (20260230, False),
    (99999999, False), (0, False),
])
def test_f008_r34_fecha_de_vencimiento_valida(fecha: int, esperado: bool) -> None:
    assert fecha_de_vencimiento_valida(fecha, fecha_factura=20261015) is esperado
