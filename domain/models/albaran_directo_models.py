# domain/models/albaran_directo_models.py
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DirectLine(BaseModel):
    """Una linea de un albaran de compra directo (sin contrato)."""

    # Producto recibido. De su ultima dcapro se heredan cueide/ivaide/prepma/
    # natide/almide/cenide si no se indican explicitamente.
    proide: int = Field(..., ge=1)
    can: float = Field(..., ge=0)
    pre: float = Field(..., ge=0)
    res: str | None = None          # descripcion; por defecto, la de la plantilla del producto
    unimed: str | None = None       # unidad; por defecto, la de la plantilla del producto
    ivaide: int | None = None       # tipo de IVA; por defecto, el de la plantilla del producto
    paride: int | None = None       # partida (opcional)

    @field_validator("res", "unimed", mode="before")
    @classmethod
    def _strip_optional(cls, value: object) -> object:
        if value is None:
            return None
        return str(value).strip()


class AddDirectAlbaranRequest(BaseModel):
    """
    Peticion para dar de alta un albaran de compra DIRECTO (no asociado a un
    contrato). El proveedor se resuelve por CIF (de su ultimo albaran, que
    aporta formas de pago y cuentas), la obra por su codigo, y cada linea
    aporta producto + cantidad + precio.

    A diferencia del albaran desde contrato: NO se enlaza a ningun contrato
    (dca.ctride=0, dcapro sin docori*), NO se crea ctrprodes, NO se toca
    ctrpro.canser ni los estados del contrato. El efecto en stock (mov + PMP)
    es identico.

    commit=False (por defecto) => DRY-RUN.
    """

    database: str = Field(..., min_length=1)
    cif_proveedor: str = Field(..., min_length=1)
    cod_obra: str = Field(..., min_length=1)

    # Almacen / centro de coste de la cabecera. Si se omiten, se derivan de la
    # ultima dcapro de los productos de las lineas.
    almide: int | None = Field(default=None, ge=1)
    cenide: int | None = Field(default=None, ge=1)

    su_referencia: str = Field(default="", max_length=200)
    fecha_albaran: int | None = Field(default=None, ge=19000101, le=29991231)
    empide: int | None = Field(default=None, ge=1)

    lineas: list[DirectLine] = Field(..., min_length=1)
    commit: bool = Field(default=False)

    @field_validator("database", "cif_proveedor", "cod_obra", mode="before")
    @classmethod
    def _strip(cls, value: object) -> str:
        return str(value).strip()

    @field_validator("su_referencia", mode="before")
    @classmethod
    def _strip_ref(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()
