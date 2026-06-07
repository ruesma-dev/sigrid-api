# domain/models/albaran_domain_models.py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReceivedLine(BaseModel):
    """Una línea de contrato (ctrpro) recibida en este albarán, con su cantidad."""

    ctrpro_ide: int = Field(..., ge=1)
    cantidad: float = Field(..., ge=0)


class AddPurchaseAlbaranRequest(BaseModel):
    """
    Petición para dar de alta un albarán de compra a partir de un contrato.

    Réplica fiel del alta manual de Sigrid: el albarán copia TODAS las líneas
    del contrato (las de `lineas_recibidas` con su cantidad recibida; el resto
    con can=0) y genera los movimientos de stock (mov) con recálculo de PMP.

    El contrato se localiza por la terna (cod_contrato + cod_obra + cif_proveedor),
    igual que en el endpoint de líneas de contrato.

    commit=False (por defecto) => DRY-RUN: devuelve el preview completo de lo que
    se insertaría sin tocar la base de datos.
    commit=True => aplica los cambios en una única transacción (requiere que la
    escritura de dominio esté habilitada en settings).
    """

    database: str = Field(..., min_length=1)

    cod_contrato: str = Field(..., min_length=1)
    cod_obra: str = Field(..., min_length=1)
    cif_proveedor: str = Field(..., min_length=1)

    # entref del documento: la referencia/nº de albarán del proveedor.
    su_referencia: str = Field(default="", max_length=200)

    # Fecha del albarán como entero YYYYMMDD. None => se usa la fecha de hoy.
    fecha_albaran: int | None = Field(default=None, ge=19000101, le=29991231)

    lineas_recibidas: list[ReceivedLine] = Field(default_factory=list)

    # Empleado (empide) que figura en la cabecera. None => default de settings
    # (SIGRID_ALBARAN_EMPIDE).
    empide: int | None = Field(default=None, ge=1)

    commit: bool = Field(default=False)

    @field_validator("database", "cod_contrato", "cod_obra", "cif_proveedor", mode="before")
    @classmethod
    def _strip(cls, value: object) -> str:
        return str(value).strip()

    @field_validator("su_referencia", mode="before")
    @classmethod
    def _strip_ref(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()


class AlbaranLinePreview(BaseModel):
    """Preview de una línea del albarán (dcapro) + su movimiento de stock (mov)."""

    ctrpro_ide: int
    linoriide: int
    proide: int
    res: str | None = None
    unimed: str | None = None
    cantidad: float
    precio: float
    total: float
    iva_cuota: float
    almide: int
    # Resultado del ledger de stock tras procesar esta línea (None si can=0 y
    # no se quiere arrastrar, aunque por defecto se arrastra el balance).
    stock_anterior: float | None = None
    stock_resultante: float | None = None
    pmp_anterior: float | None = None
    pmp_resultante: float | None = None


class AddPurchaseAlbaranResponse(BaseModel):
    """
    Resultado del alta (o dry-run) del albarán de compra.

    En dry-run los `ide` reservados (con_ide y los de las líneas) son
    provisionales: reflejan MAX(ide)+1 en el instante de la consulta y pueden
    diferir del valor real en el commit (que se reserva bajo applock).
    """

    ok: bool = True
    database: str
    committed: bool
    dry_run: bool

    # Identificador del concepto/cabecera (con.ide == dca.ide) y código de serie.
    con_ide: int
    cod: str

    # Datos del contrato origen localizado.
    contrato: dict[str, Any]

    # Preview de la cabecera dca (importes, fechas, proveedor, almacén, obra...).
    cabecera: dict[str, Any]

    # Preview de las líneas (dcapro) con su movimiento de stock.
    lineas: list[AlbaranLinePreview] = Field(default_factory=list)

    # Preview de los movimientos de stock (mov) en crudo, por si se quiere ver el
    # detalle completo del ledger.
    movimientos: list[dict[str, Any]] = Field(default_factory=list)

    # Recalculo de estados de la cabecera del contrato (estser/estfac) antes y
    # después de aplicar el albarán.
    estados_contrato: dict[str, Any] = Field(default_factory=dict)

    # Totales agregados de la cabecera del albarán.
    totales: dict[str, Any] = Field(default_factory=dict)

    warnings: list[str] = Field(default_factory=list)
