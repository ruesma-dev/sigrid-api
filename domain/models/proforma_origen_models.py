# domain/models/proforma_origen_models.py
"""
Codigos, errores y respuesta de la proforma A ORIGEN de `sigrid/proforma`
(F-016, design §Codigos, R19, R20).

Todo vive en subclases de lo de F-007, como F-007 amplio lo de F-009 (costura
5): los conjuntos y clases de `proforma_models` no cambian, y una respuesta de
mes sigue sin ninguna clave nueva (R1). La forma campo a campo esta en
`specs/F-007-registrar-proforma/contrato_proformas.md` v1.2.
"""
from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from domain.models.proforma_models import (
    CODIGOS_AVISO_PROFORMA,
    CODIGOS_CABECERA_PROFORMA,
    CODIGOS_LINEA_PROFORMA,
    AvisoProforma,
    FalloLineaProforma,
    LineaProformaResultado,
    ProformaError,
    ProformaResponse,
)

#: Errores de cabecera: los de F-007 y los tres de la cadena.
CODIGOS_CABECERA_PROFORMA_ORIGEN: frozenset[str] = CODIGOS_CABECERA_PROFORMA | frozenset(
    {
        "escritura_proformas_origen_deshabilitada",
        "anterior_no_valida",
        "anterior_con_sucesora",
    }
)

#: Errores de linea: los de F-007 y la continuacion que no vale (R9).
CODIGOS_LINEA_PROFORMA_ORIGEN: frozenset[str] = CODIGOS_LINEA_PROFORMA | frozenset(
    {"linea_anterior_no_valida"}
)

#: Avisos: los de F-007 y el de integridad de R10 (D3).
CODIGOS_AVISO_PROFORMA_ORIGEN: frozenset[str] = CODIGOS_AVISO_PROFORMA | frozenset(
    {"linea_nueva_ya_en_la_anterior"}
)


class FalloLineaProformaOrigen(FalloLineaProforma):
    """Una linea que no vale, con `linea_anterior_no_valida` ademas (R9)."""

    codigos: ClassVar[frozenset[str]] = CODIGOS_LINEA_PROFORMA_ORIGEN


class ProformaOrigenError(ProformaError):
    """Fallo de negocio de la proforma a origen: los codigos de F-007 y los de
    la cadena (`anterior_no_valida`, `anterior_con_sucesora`) y su llave."""

    codigos: ClassVar[frozenset[str]] = CODIGOS_CABECERA_PROFORMA_ORIGEN


class AvisoProformaOrigen(AvisoProforma):
    """Aviso de la respuesta a origen. `linea_nueva_ya_en_la_anterior` lleva en
    `lineas_anterior` los `dcapro.ide` de la anterior con el mismo `ctrpro`
    (R10); en los demas va vacia."""

    codigos: ClassVar[frozenset[str]] = CODIGOS_AVISO_PROFORMA_ORIGEN

    lineas_anterior: list[int] = Field(default_factory=list)


class AnteriorCadena(BaseModel):
    """La proforma anterior de la cadena: su `con.cod` y su `con.ide`."""

    cod: str
    ide: int


class CadenaProforma(BaseModel):
    """
    R19: la cadena de la proforma escrita. `anterior` `None` en la primera; los
    importes de cadena son Σ round(`canoriori`·`pre`, 2) de las lineas de la
    anterior (LP9) y de las escritas; `n_arrastradas`, las de la anterior que
    ninguna linea de la peticion continua.
    """

    anterior: AnteriorCadena | None
    primera_de_cadena: bool
    importe_anterior_cadena: float
    importe_origen_cadena: float
    n_arrastradas: int


class LineaProformaOrigenResultado(LineaProformaResultado):
    """
    Una linea de la respuesta a origen: la de F-007 mas `linea_anterior` (el
    `dcapro.ide` de la anterior que continua o arrastra; `None` en las nuevas),
    `arrastrada` y las cantidades a origen de la cadena antes y despues. En
    `existente` e `idempotente` (lineas LEIDAS) van a `None`.
    """

    avisos: list[AvisoProformaOrigen] = Field(default_factory=list)  # type: ignore[assignment]
    linea_anterior: int | None = None
    arrastrada: bool | None = None
    cantidad_anterior_cadena: float | None = None
    cantidad_origen_cadena: float | None = None


class ProformaOrigenResponse(ProformaResponse):
    """La respuesta de F-007 mas `cadena` (`None` en `existente` e
    `idempotente`); las arrastradas, detras de las de la peticion (R19)."""

    avisos: list[AvisoProformaOrigen] = Field(default_factory=list)  # type: ignore[assignment]
    lineas: list[LineaProformaOrigenResultado] = Field(default_factory=list)  # type: ignore[assignment]
    cadena: CadenaProforma | None = None
