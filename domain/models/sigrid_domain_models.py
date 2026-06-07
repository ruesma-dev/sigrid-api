# domain/models/sigrid_domain_models.py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ContractLineInput(BaseModel):
    """Una linea nueva a anadir al contrato."""

    res: str = Field(..., min_length=1)        # descripcion corta de la linea
    can: float                                  # cantidad
    pre: float                                  # precio unitario
    unimed: str | None = None                   # unidad (por defecto, la de la plantilla)
    paride: int | None = None                   # partida a la que imputa (por defecto, la de la plantilla)
    proide: int | None = None                   # producto (por defecto, el de la plantilla)
    tex: str | None = None                      # descripcion larga (opcional)

    @field_validator("res")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class AddContractLinesRequest(BaseModel):
    """
    Anade lineas (`ctrpro`) a un contrato de compra existente, localizado por
    (codigo de contrato + codigo de obra + CIF del proveedor).

    Clona una linea existente del contrato como plantilla (para fidelidad de
    campos) y solo sobreescribe descripcion, cantidad, precio, unidad, partida
    y producto. Recalcula `tot`, `ivacuo` y los totales de la cabecera `ctr`.

    `commit=False` (por defecto) => DRY-RUN: no escribe nada.
    """

    database: str = Field("ruesma", min_length=1)
    cod_contrato: str = Field(..., min_length=1)
    cod_obra: str = Field(..., min_length=1)
    cif_proveedor: str = Field(..., min_length=1)
    # Linea plantilla a clonar; por defecto, la ultima linea del contrato.
    template_line_ide: int | None = None
    lines: list[ContractLineInput] = Field(..., min_length=1)
    commit: bool = False

    @field_validator("database", "cod_contrato", "cod_obra", "cif_proveedor")
    @classmethod
    def _strip(cls, value: str) -> str:
        return value.strip()


class AddContractLinesResponse(BaseModel):
    ok: bool = True
    dry_run: bool
    committed: bool
    database: str
    ctride: int
    obride: int
    cod_contrato: str
    cif_proveedor: str
    template_line_ide: int
    reserved_ctrpro_ides: list[int]
    ctrpro: list[dict[str, Any]]
    header_totals_before: dict[str, Any]
    header_totals_after: dict[str, Any]
    note: str | None = None
