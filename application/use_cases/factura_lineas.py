# application/use_cases/factura_lineas.py
"""
Funciones PURAS de las lineas y los vencimientos de `sigrid/factura` (F-008):
sin E/S, sin SQL. Las filas que salen de aqui son las de `dcfpro` por lista
blanca (`DCFPRO_COLUMNAS`, T0); `ide`, `docide` y `pos` los pone el
constructor de la factura al numerar.

- Vencimientos del llamante (R32-R35): se validan forma, rango y suma; nunca se
  calculan ni se comparan con `pagfor`, `pagdia` o `pagmes`.
- Linea de origen (R12, R17, R19, R20): copia de su `dcapro` sin recalcular,
  igual en FR y FRGG (M69), y comparacion con lo que manda el llamante a
  origen (R21, R22).
- Linea sin origen (R23-R28): dos resolvedores por serie que devuelven la MISMA
  `LineaResuelta` y UN constructor (`linea_sin_origen`) para las dos.
"""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from collections.abc import Sequence

from domain.models.factura_models import FacturaError, Vencimiento

#: R33: un vencimiento va como mucho 730 dias detras de la factura.
MAX_DIAS_VENCIMIENTO = 730
#: R33: Σ importes = `totpag` con un centimo de margen.
TOLERANCIA_VENCIMIENTOS = Decimal("0.01")


def _decimal(valor: float | Decimal) -> Decimal:
    """`Decimal` de lo que se ve (`repr` del float), como F-009."""
    return valor if isinstance(valor, Decimal) else Decimal(repr(valor))


def _fecha(aaaammdd: int) -> date | None:
    try:
        return date(aaaammdd // 10000, aaaammdd // 100 % 100, aaaammdd % 100)
    except ValueError:
        return None


def fecha_de_vencimiento_valida(fecha: int, *, fecha_factura: int) -> bool:
    """R33 (y R34): fecha real dentro de [`fecha_factura`, +730 dias]."""
    vence, factura = _fecha(fecha), _fecha(fecha_factura)
    if vence is None or factura is None:
        return False
    return factura <= vence <= factura + timedelta(days=MAX_DIAS_VENCIMIENTO)


def validar_vencimientos(
    vencimientos: Sequence[Vencimiento], *, fecha_factura: int, totpag: Decimal
) -> None:
    """R33: cada fecha real, en rango y sin repetir (`vencimiento_no_valido`
    con la primera posicion que falla); despues Σ `importe` = `totpag` ±0,01
    (`vencimientos_no_cuadran` con las dos cifras)."""
    vistas: set[int] = set()
    for posicion, vencimiento in enumerate(vencimientos):
        if (
            not fecha_de_vencimiento_valida(vencimiento.fecha, fecha_factura=fecha_factura)
            or vencimiento.fecha in vistas
        ):
            raise FacturaError(
                f"El vencimiento {posicion} no es una fecha real entre la de la factura y 730 "
                "dias despues, o repite otra.",
                codigo="vencimiento_no_valido",
                details={"posicion": posicion, "fecha": vencimiento.fecha},
            )
        vistas.add(vencimiento.fecha)
    suma = sum((_decimal(v.importe) for v in vencimientos), Decimal(0))
    if abs(suma - _decimal(totpag)) > TOLERANCIA_VENCIMIENTOS:
        raise FacturaError(
            f"Los vencimientos suman {suma} y la factura deja {totpag} por pagar.",
            codigo="vencimientos_no_cuadran",
            details={"suma_vencimientos": float(suma), "totpag": float(totpag)},
        )
