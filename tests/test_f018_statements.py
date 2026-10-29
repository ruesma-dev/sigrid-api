# tests/test_f018_statements.py
"""
F-018 · T4 y T6: el constructor puro del descuento por línea.

T4, funciones puras (design §Funciones puras): R3 (`texto_de_dto`, el texto
como lo escribe Sigrid), R14 (`porcentaje_de_dto`, que solo lee su formato),
R1, R2 y R5 (`importe_con_dto`, con los casos medidos en M46), R8
(`bruto_de_linea`), D9 (`dto_del_contrato`) y R13 (`dto_coincide`).

Sin red y sin base de datos.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from application.use_cases.albaran_compra_statements import (
    bruto_de_linea,
    dto_coincide,
    dto_del_contrato,
    importe_con_dto,
    porcentaje_de_dto,
    texto_de_dto,
)

# =====================================================================================
# R3 · el texto de `dcapro.dto` como lo escribe Sigrid (M45)
# =====================================================================================


@pytest.mark.parametrize(
    "dto, texto",
    [(40, "40%"), (40.0, "40%"), (1.5, "1,5%"), (21.45, "21,45%"), (0.01, "0,01%"),
     (100, "100%"), (100.0, "100%"), (7.1, "7,1%"), (2.5, "2,5%"), (10.1, "10,1%"),
     (Decimal("40.00"), "40%"), (Decimal("1.50"), "1,5%"), (20, "20%"), (0.5, "0,5%")],
)
def test_f018_r3_texto_de_dto(dto: float | Decimal, texto: str) -> None:
    assert texto_de_dto(dto) == texto


# =====================================================================================
# R14 · leer un `dto` de Sigrid: solo su formato
# =====================================================================================


@pytest.mark.parametrize(
    "texto, esperado",
    [(None, Decimal(0)), ("", Decimal(0)), ("   ", Decimal(0)), ("40%", Decimal(40)),
     (" 1,5% ", Decimal("1.5")), ("21,45%", Decimal("21.45")), ("0,01%", Decimal("0.01")),
     ("100%", Decimal(100)), ("0%", Decimal(0)), ("40 %", Decimal(40)), ("\t7%\t", Decimal(7))],
)
def test_f018_r14_porcentaje_legible(texto: str | None, esperado: Decimal) -> None:
    assert porcentaje_de_dto(texto) == esperado


@pytest.mark.parametrize(
    "texto",
    ["10+2,5", "5", "1.5%", "5+5", "-5%", "40%%", "%", ",5%", "5,%", "1,5,5%", "40% 2", "4 0%",
     "x%", "1.000%"],
)
def test_f018_r14_porcentaje_no_legible(texto: str) -> None:
    assert porcentaje_de_dto(texto) is None


# =====================================================================================
# R1, R2, R5 · el importe de la línea con descuento (M46)
# =====================================================================================


@pytest.mark.parametrize(
    "cantidad, tar, dto, tot",
    [
        (1, 18.625, 40, "11.18"),        # 11,175 -> 11,18 (en float daría 11,17)
        (1, 265, 3.5, "255.73"),         # 255,725 -> 255,73
        (-0.4, 1275.68, 2.5, "-497.52"),  # -497,5152 -> -497,52
        (36, 4.278, 40, "92.40"),        # 92,4048 -> 92,40
        (0.3, 12825, 1, "3809.03"),      # 3.809,025 -> 3.809,03
        (-1, 18.625, 40, "-11.18"),      # mitad lejos del cero también en negativo
        (12.5, 4.278, 40, "32.09"),      # el ejemplo de D9
        (3, 10, 100, "0.00"),            # 100 %: tot 0
        (2, 10, 0.01, "20.00"),
    ],
)
def test_f018_r2_importe_con_dto(cantidad: float, tar: float, dto: float, tot: str) -> None:
    total, _ivacuo, pre = importe_con_dto(cantidad, tar, dto, 0.21)
    assert total == Decimal(tot)
    # `pre` = tot / cantidad SIN redondear (R1), con la misma expresión.
    assert pre == float(Decimal(tot)) / cantidad


def test_f018_r1_pre_neto_sin_redondear() -> None:
    tot, _ivacuo, pre = importe_con_dto(36, 4.278, 40, 0.21)
    assert tot == Decimal("92.40")
    assert pre == 92.4 / 36
    assert pre != round(pre, 6)  # 2,5666...: no se redondea


def test_f018_r5_ivacuo_sobre_el_neto() -> None:
    tot, ivacuo, _pre = importe_con_dto(1, 18.625, 40, 0.21)
    assert (tot, ivacuo) == (Decimal("11.18"), Decimal("2.35"))  # 11,18·0,21 = 2,3478
    tot, ivacuo, _pre = importe_con_dto(-0.4, 1275.68, 2.5, 0.21)
    assert ivacuo == Decimal("-104.48")  # -497,52·0,21 = -104,4792
    _tot, ivacuo, _pre = importe_con_dto(1, 10, 25, 0.1)
    assert ivacuo == Decimal("0.75")


def test_f018_r2_admite_decimal_y_float_como_porcentaje() -> None:
    assert importe_con_dto(1, 18.625, Decimal(40), 0.21) == importe_con_dto(1, 18.625, 40.0, 0.21)
    assert importe_con_dto(1, 265, Decimal("3.5"), 0.21)[0] == Decimal("255.73")


def test_f018_r2_100_por_cien_da_cero() -> None:
    tot, ivacuo, pre = importe_con_dto(3, 10, 100, 0.21)
    assert (tot, ivacuo, pre) == (Decimal("0.00"), Decimal("0.00"), 0.0)


# =====================================================================================
# R8 · el bruto de una línea para `impbru`
# =====================================================================================


@pytest.mark.parametrize(
    "cantidad, tar, bruto",
    [(1, 18.625, "18.63"), (36, 4.278, "154.01"), (-0.4, 1275.68, "-510.27"), (2, 10, "20.00"),
     (-1, 18.625, "-18.63")],
)
def test_f018_r8_bruto_de_linea(cantidad: float, tar: float, bruto: str) -> None:
    assert bruto_de_linea(cantidad, tar) == Decimal(bruto)


# =====================================================================================
# D9 · el dto del contrato que se copia (legible, > 0 y con `tar` != 0)
# =====================================================================================


@pytest.mark.parametrize(
    "ctrpro, esperado",
    [
        ({"dto": "40%", "tar": 4.278}, Decimal(40)),
        ({"dto": " 1,5% ", "tar": 10.0}, Decimal("1.5")),
        ({"dto": "10+2,5", "tar": 4.278}, None),   # cascada: no legible
        ({"dto": "5", "tar": 4.278}, None),        # sin %: no legible
        ({"dto": "", "tar": 4.278}, None),         # sin dto
        ({"dto": None, "tar": 4.278}, None),
        ({"tar": 4.278}, None),
        ({"dto": "0%", "tar": 4.278}, None),       # 0: sin dto
        ({"dto": "40%", "tar": 0}, None),          # tar 0
        ({"dto": "40%", "tar": None}, None),
        ({"dto": "40%"}, None),
    ],
)
def test_f018_d9_dto_del_contrato(ctrpro: dict, esperado: Decimal | None) -> None:
    assert dto_del_contrato(ctrpro) == esperado


# =====================================================================================
# R13 · el dto pedido frente al del `ctrpro`
# =====================================================================================


@pytest.mark.parametrize(
    "pedido, texto, esperado",
    [(40, "40%", True), (40.0, "40%", True), (1.5, "1,5%", True), (21.45, "21,45%", True),
     (40, "50%", False), (40, "", False), (40, None, False), (40, "0%", False),
     (1.5, "1,50%", True), (40, "10+2,5", None), (40, "40", None), (40, "40.0%", None)],
)
def test_f018_r13_dto_coincide(pedido: float, texto: str | None, esperado: bool | None) -> None:
    assert dto_coincide(pedido, texto) is esperado
