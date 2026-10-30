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

from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from domain.models.factura_models import FacturaError, Vencimiento

#: Las 73 columnas de `dbo.dcfpro`, en su orden fisico (T0). El `INSERT` lleva
#: estas y solo estas.
DCFPRO_COLUMNAS: tuple[str, ...] = (
    "ide", "docide", "proide", "pos", "pre", "can", "candes", "tar", "dto", "tot", "fec", "pla",
    "res", "tex", "cueide", "envide", "almide", "ivaide", "ivacuo", "reqcuo", "prepma", "lintip",
    "cenide", "caaide", "anades", "tardiv", "totdiv", "cod2", "refent", "garfec", "gardes", "unimed",
    "docoritip", "docoricod", "docoriide", "linoriide", "canser", "canfac", "cancan", "canorilin",
    "canoriant", "canoriori", "imporiant", "imporiori", "taride", "apuide", "cuoman", "dncide",
    "dncproide", "obride", "paride", "natide", "parcandes", "med", "canmed", "pac", "item", "desesp",
    "nueusa", "edilin", "texcom", "serdes", "serdesdat", "dvfproide", "anexo", "fecimp", "canped",
    "imporiantdiv", "imporioridiv", "totimpret", "ico", "ivaope", "vmg",
)
#: `varchar` (vacio `''`) y `text`/`image` que el alta deja en NULL (T0: 35 de 35).
_DCFPRO_TEXTO: frozenset[str] = frozenset({
    "dto", "res", "tex", "cod2", "refent", "unimed", "docoricod", "pac", "ico",
})
_DCFPRO_NULAS: frozenset[str] = frozenset({"med", "desesp", "texcom", "serdesdat"})
#: Las que pone la numeracion de la factura.
_DCFPRO_NUMERACION: tuple[str, ...] = ("ide", "docide", "pos")

#: R17: lo que la linea de origen copia de su `dcapro`, sin recalcular.
COPIADAS_DEL_ORIGEN: tuple[str, ...] = (
    "proide", "can", "pre", "tar", "dto", "tot", "ivaide", "ivacuo", "cenide", "caaide", "paride",
    "natide", "almide", "obride", "res", "tex", "cod2", "unimed", "prepma", "dncide", "dncproide",
)
#: `con.tip` del albaran o proforma de origen (R13, R17).
DOCORITIP_ALBARAN = 14
MODOS: tuple[str, ...] = ("mes", "origen")

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


# --------------------------------------------------------------------------- #
# Filas de `dcfpro` (T4, T6)
# --------------------------------------------------------------------------- #


def _vacio(columna: str) -> Any:
    if columna in _DCFPRO_NULAS:
        return None
    return "" if columna in _DCFPRO_TEXTO else 0


def fila_dcfpro(valores: Mapping[str, Any]) -> dict[str, Any]:
    """La fila de `dcfpro` por lista blanca: `DCFPRO_COLUMNAS` menos la
    numeracion, con lo que trae `valores` y el vacio del tipo en el resto. Una
    columna que no es de `dcfpro` es un error de programacion."""
    ajenas = set(valores) - set(DCFPRO_COLUMNAS)
    if ajenas:
        raise ValueError(f"Columnas que no son de dcfpro: {sorted(ajenas)}.")
    return {
        columna: valores[columna] if columna in valores else _vacio(columna)
        for columna in DCFPRO_COLUMNAS
        if columna not in _DCFPRO_NUMERACION
    }


def _num(valor: Any) -> Decimal:
    return _decimal(float(valor or 0))


def linea_de_origen(
    dcapro: Mapping[str, Any],
    anterior: Mapping[str, Any] | None,
    *,
    modo: str,
    cueide: int,
    docoricod: str,
) -> dict[str, Any]:
    """
    R17: la linea de la factura copiada de su `dcapro` (de un albaran o una
    proforma), con `docoritip` 14, su `cod` y sus `ide` y `canorilin` 0; R12:
    `cueide` = `prv.cuepdtide`, en las dos series (M69). Columnas a origen
    (design §6): en mes (R19) `canoriori` = `can` e `imporiori` = `tot`; a
    origen (R20, M63) `canoriori` = el del `dcapro`, `canoriant`/`imporiant` =
    los de la `anterior` (la `dcapro` de su `canorilin`, o 0 sin ella) e
    `imporiori` = el del `dcapro` si esta vinculada (`linoriide` != 0) o
    `imporiant` + `tot` si no, sumado en `Decimal`.
    """
    if modo not in MODOS:
        raise ValueError(f"El modo '{modo}' no es de mes ni a origen.")
    valores: dict[str, Any] = {columna: dcapro[columna] for columna in COPIADAS_DEL_ORIGEN}
    if modo == "mes":
        a_origen = {"canoriori": dcapro["can"], "canoriant": 0, "imporiant": 0,
                    "imporiori": dcapro["tot"]}
    else:
        previa = anterior or {}
        canoriant = float(_num(previa.get("canoriori")))
        imporiant = float(_num(previa.get("imporiori")))
        vinculada = bool(dcapro.get("linoriide"))
        imporiori = (
            float(_num(dcapro.get("imporiori"))) if vinculada
            else float(_num(imporiant) + _num(dcapro["tot"]))
        )
        a_origen = {"canoriori": float(_num(dcapro.get("canoriori"))), "canoriant": canoriant,
                    "imporiant": imporiant, "imporiori": imporiori}
    valores.update(
        a_origen,
        cueide=cueide,
        docoritip=DOCORITIP_ALBARAN,
        docoricod=docoricod,
        docoriide=dcapro["docide"],
        linoriide=dcapro["ide"],
        canorilin=0,
    )
    return fila_dcfpro(valores)
