# domain/models/factura_models.py
"""
Contrato de `POST /api/sigrid/factura` (F-008): alta de UNA factura de compra
en Sigrid, serie FR (REC) o FRGG (RECGG), SIN contabilidad (P1). La API
registra y valida; no deduce: serie, modo, a origen, vencimientos, cuentas y
analiticas los decide el llamante.

Un cuerpo no valido es 400 «Solicitud invalida.» sin `codigo` (R1, R2); los
fallos de negocio, `FacturaError` con su `codigo` de `CODIGOS_FACTURA` y, en
`lineas_no_validas`, los fallos de linea con su posicion (R24).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SerieFactura = Literal["FR", "FRGG"]
ModoFactura = Literal["mes", "origen"]
EstadoFactura = Literal["previsto", "creado", "idempotente"]

#: Codigos de error de la factura (design §6-§8). Conjunto cerrado.
CODIGOS_FACTURA: frozenset[str] = frozenset({
    "escritura_facturas_deshabilitada",
    "base_de_datos_no_permitida",
    "referencia_no_permitida",
    "usuario_no_valido",
    "demasiadas_lineas",
    "estado_inicial_no_encontrado",
    "obra_no_encontrada",
    "almacen_de_obra_no_resuelto",
    "proveedor_no_encontrado",
    "proveedor_ambiguo",
    "proveedor_sin_cuenta",
    "varias_obras",
    "varios_contratos",
    "origen_no_encontrado",
    "origen_de_otro_proveedor",
    "origen_sin_contabilizar",
    "origen_ya_facturado",
    "modo_no_coincide_con_origen",
    "origenes_de_modos_distintos",
    "a_origen_incompleto",
    "a_origen_no_cuadra",
    "lineas_no_validas",
    "totales_no_cuadran",
    "abono_no_soportado",
    "retencion_no_soportada",
    "vencimiento_no_valido",
    "vencimientos_no_cuadran",
    "vencimiento_retencion_no_valido",
    "referencia_en_conflicto",
    "factura_ya_registrada",
    "colision_de_clave",
    "filas_afectadas_inesperadas",
})

#: Codigos de los fallos de linea, dentro de `lineas_no_validas` (R24-R26).
CODIGOS_LINEA_FACTURA: frozenset[str] = frozenset({
    "iva_no_valido",
    "producto_no_permitido",
    "producto_no_encontrado",
    "naturaleza_no_valida",
    "analitica_no_resuelta",
    "partida_no_encontrada",
    "partida_no_imputable",
    "partida_ambigua",
    "paride_no_valido",
    "cuenta_no_valida",
    "analitica_no_valida",
})

#: Campos de linea propios de cada serie (R23): uno de la otra serie es 400.
CAMPOS_FR: tuple[str, ...] = ("producto", "partida", "paride", "unidad")
CAMPOS_FRGG: tuple[str, ...] = ("cuenta", "analitica")
#: Obligatorios por serie (R23, P19).
OBLIGATORIOS: dict[str, tuple[str, ...]] = {"FR": ("producto",), "FRGG": CAMPOS_FRGG}


def _fecha_real(valor: int) -> int:
    """`AAAAMMDD` que es una fecha del calendario; si no, `ValueError`."""
    if not 10000101 <= valor <= 99991231:
        raise ValueError("La fecha va como AAAAMMDD.")
    date(valor // 10000, valor // 100 % 100, valor % 100)
    return valor


class _Estricto(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class EntradaAOrigen(_Estricto):
    """R21: lo que el llamante calcula a origen para UNA linea facturada."""

    linea: int = Field(..., ge=1, strict=True)        # dcapro.ide de la linea de origen
    canoriori: float = Field(..., strict=True)
    imporiori: float = Field(..., strict=True)


class Vencimiento(_Estricto):
    """R32: un vencimiento del llamante; la realidad y el rango, en el caso de uso (R33)."""

    fecha: int = Field(..., strict=True)
    importe: float = Field(..., gt=0, strict=True)

    @field_validator("importe")
    @classmethod
    def _dos_decimales(cls, valor: float) -> float:
        if Decimal(repr(valor)).as_tuple().exponent < -2:
            raise ValueError("El importe lleva como mucho 2 decimales.")
        return valor


class LineaSinOrigen(_Estricto):
    """R23: una linea que no sale de un albaran ni de una proforma. Comunes y,
    por serie, FR (`producto`, `partida`, `paride`, `unidad`) o FRGG (`cuenta`,
    `analitica`); la mezcla la rechaza `FacturaRequest`."""

    descripcion: str = Field(..., min_length=1, max_length=128)
    cantidad: float = Field(..., strict=True)
    precio: float = Field(..., strict=True)
    iva: str = Field(..., min_length=1, max_length=24)
    producto: str | None = Field(default=None, min_length=1, max_length=24)
    partida: str | None = Field(default=None, min_length=1, max_length=24)
    paride: int | None = Field(default=None, ge=1, strict=True)
    unidad: str | None = Field(default=None, max_length=8)
    cuenta: str | None = Field(default=None, min_length=1, max_length=24)
    analitica: str | None = Field(default=None, min_length=1, max_length=24)


class FacturaRequest(_Estricto):
    database: str = Field(..., min_length=1, max_length=128)
    usu: str = Field(..., min_length=1, max_length=24)
    referencia_externa: str = Field(..., min_length=1, max_length=128)
    serie: SerieFactura = "FR"
    cif_proveedor: str = Field(..., min_length=1, max_length=24)
    numero_factura: str = Field(..., min_length=1, max_length=128)
    fecha_factura: int = Field(..., strict=True)
    cod_obra: str | None = Field(default=None, min_length=1, max_length=24)
    modo: ModoFactura = "mes"
    origenes: list[str] = Field(default_factory=list)
    a_origen: list[EntradaAOrigen] | None = None
    lineas: list[LineaSinOrigen] = Field(default_factory=list)
    vencimientos: list[Vencimiento] = Field(..., min_length=1, max_length=12)
    vencimiento_retencion: int | None = Field(default=None, strict=True)
    total_base: float = Field(..., strict=True)
    total_iva: float = Field(..., strict=True)
    total_factura: float = Field(..., strict=True)
    commit: bool = Field(default=False, strict=True)

    @field_validator("fecha_factura")
    @classmethod
    def _fecha(cls, valor: int) -> int:
        return _fecha_real(valor)

    @field_validator("origenes")
    @classmethod
    def _codigos(cls, valores: list[str]) -> list[str]:
        recortados = [valor.strip() for valor in valores]
        if any(not valor or len(valor) > 24 for valor in recortados):
            raise ValueError("Cada origen es un con.cod de 1 a 24 caracteres.")
        return recortados

    @model_validator(mode="after")
    def _coherencia(self) -> FacturaRequest:
        """R2, R11 y R23: lo que se decide sin leer la base."""
        if not self.origenes and not self.lineas:
            raise ValueError("Sin origenes ni lineas no hay factura.")
        if self.modo == "origen" and not self.origenes:
            raise ValueError("El modo origen exige origenes.")
        if len({valor.casefold() for valor in self.origenes}) != len(self.origenes):
            raise ValueError("Hay un origen repetido.")
        if self.modo == "mes" and self.a_origen is not None:
            raise ValueError("a_origen solo va en modo origen.")
        if not self.origenes and self.cod_obra is None:
            raise ValueError("Sin origenes, cod_obra es obligatorio.")
        ajenos = CAMPOS_FRGG if self.serie == "FR" else CAMPOS_FR
        for indice, linea in enumerate(self.lineas):
            for campo in ajenos:
                if getattr(linea, campo) is not None:
                    raise ValueError(f"lineas[{indice}].{campo} no va en la serie {self.serie}.")
            for campo in OBLIGATORIOS[self.serie]:
                if getattr(linea, campo) is None:
                    raise ValueError(f"lineas[{indice}].{campo} es obligatorio en la serie {self.serie}.")
        return self


class FalloLineaFactura(_Estricto):
    """Un fallo de una linea sin origen (R24), con su posicion en `lineas`."""

    indice: int = Field(..., ge=0)
    codigo: str
    mensaje: str

    @field_validator("codigo")
    @classmethod
    def _codigo(cls, valor: str) -> str:
        if valor not in CODIGOS_LINEA_FACTURA:
            raise ValueError(f"Codigo de linea desconocido: {valor}.")
        return valor


class FacturaError(ValueError):
    """Fallo de negocio de `sigrid/factura`: 400 con `details.codigo` y lo que
    lleve `details` (las cifras de R22, R30, R33; las lineas de R24)."""

    codigos: ClassVar[frozenset[str]] = CODIGOS_FACTURA

    def __init__(self, mensaje: str, *, codigo: str, details: dict[str, Any] | None = None) -> None:
        if codigo not in self.codigos:
            raise ValueError(f"Codigo de factura desconocido: {codigo}.")
        super().__init__(mensaje)
        self.codigo = codigo
        self.details: dict[str, Any] = dict(details or {})


class FacturaResultado(BaseModel):
    """R44: la respuesta, en previa, al crear y en `idempotente`."""

    database: str
    estado: EstadoFactura
    committed: bool
    dry_run: bool
    cod: str
    con_ide: int
    serie: SerieFactura
    modo: ModoFactura
    referencia_externa: str
    totales: dict[str, Any]
    retencion: dict[str, Any] | None
    vencimientos: list[dict[str, Any]]
    origenes: list[dict[str, Any]]
    lineas: list[dict[str, Any]]
    filas: dict[str, Any]
    avisos: list[dict[str, Any]]
    pendiente_en_sigrid: list[str]
