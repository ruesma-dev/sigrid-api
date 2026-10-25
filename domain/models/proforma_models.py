# domain/models/proforma_models.py
"""
Contrato de `POST /api/sigrid/proforma` (F-007): alta idempotente de UNA
proforma DE MES de un subcontratista, con la hoja del jefe de obra ya leida y
casada por el microservicio `proformas` (su F-005).

La forma campo a campo esta en `specs/F-007-registrar-proforma/contrato_proformas.md`
§2-§4. La respuesta es la del modo extendido de `sigrid/albaran` (F-009 R7,
F-015 R17) mas `estado` `existente`, `contrato`, `origen` y, por linea,
`de_contrato`, `cantidad_anterior_sigrid` y, en `existente`, `dcapro_ide` e
`importe` (R30). Los codigos amplian los conjuntos cerrados de F-009 (costura 5):
`sigrid/albaran` sigue con los suyos.
"""
from __future__ import annotations

from datetime import date
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.models.albaran_compra_models import (
    CODIGOS_AVISO,
    CODIGOS_CABECERA,
    CODIGOS_LINEA,
    AlbaranCompraError,
    AlbaranCompraResponse,
    AvisoAlbaran,
    FalloLinea,
    LineaResultado,
)

EstadoProforma = Literal["previsto", "creado", "idempotente", "existente"]
ResueltoPor = Literal["peticion", "proveedor", "lineas"]

#: Errores de cabecera (design §Codigos): los de F-009/F-015 y los nuevos.
CODIGOS_CABECERA_PROFORMA: frozenset[str] = CODIGOS_CABECERA | frozenset(
    {
        "escritura_proformas_deshabilitada",
        "periodo_no_valido",
        "contrato_no_resuelto",
        "contrato_de_otro_proveedor",
        "hoja_de_varios_contratos",
        "importe_mes_no_cuadra",
        "hoja_descuadrada",
        "proforma_del_mes_existente",
    }
)

#: Errores de linea: dentro de `lineas_no_validas`, como en F-009.
CODIGOS_LINEA_PROFORMA: frozenset[str] = CODIGOS_LINEA | frozenset(
    {"linea_ambigua", "producto_obligatorio", "linea_descuadrada"}
)

#: Avisos informativos nuevos (R20-R22, R24), en cabecera o en linea.
CODIGOS_AVISO_PROFORMA: frozenset[str] = CODIGOS_AVISO | frozenset(
    {
        "anterior_distinto_de_sigrid",
        "supera_contrato",
        "supera_contrato_10",
        "contrato_a_origen",
        "otra_del_mes",
    }
)


def _recortar(value: object) -> object:
    """Recorta SOLO cadenas (un numero no se vuelve texto)."""
    return value.strip() if isinstance(value, str) else value


def _recortar_o_nada(value: object) -> object:
    """Como `_recortar`, pero un texto vacio es un campo ausente."""
    value = _recortar(value)
    return None if value == "" else value


class FalloLineaProforma(FalloLinea):
    """Una linea que no vale; con `linea_ambigua`, los `ctrpro_ide` que casan."""

    codigos: ClassVar[frozenset[str]] = CODIGOS_LINEA_PROFORMA

    candidatos: list[int] = Field(default_factory=list)


class ProformaError(AlbaranCompraError):
    """
    Fallo de negocio de `sigrid/proforma`, con su `codigo` (R6). Ademas de lo de
    F-009, `hoja_de_varios_contratos` lleva SIEMPRE `reparto` (referencia de
    linea -> `cod` del contrato que la tiene, D5) y ningun otro codigo lo lleva.
    """

    codigos: ClassVar[frozenset[str]] = CODIGOS_CABECERA_PROFORMA

    def __init__(
        self,
        mensaje: str,
        *,
        codigo: str,
        lineas: list[FalloLinea] | None = None,
        reparto: dict[str, str] | None = None,
    ) -> None:
        super().__init__(mensaje, codigo=codigo, lineas=lineas)
        reparto = dict(reparto or {})
        if (codigo == "hoja_de_varios_contratos") != bool(reparto):
            raise ValueError("'reparto' va si y solo si el codigo es 'hoja_de_varios_contratos'.")
        self.reparto = reparto


class AvisoProforma(AvisoAlbaran):
    """Aviso con codigo: `proformas` decide por el `codigo`, nunca por el texto."""

    codigos: ClassVar[frozenset[str]] = CODIGOS_AVISO_PROFORMA


class LineaProformaIn(BaseModel):
    """
    Una linea de la hoja con MES != 0 (R2). De contrato con `ctrpro_ide` (lo que
    manda `proformas`) o, de respaldo, con `medicion_contrato` > 0 (R13); nueva
    con `producto`. `ctrpro_ide` y `producto` nunca juntos. Numeros estrictos.
    """

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    referencia_linea: str = Field(..., min_length=1, max_length=24)            # -> dcapro.refent
    cantidad: float = Field(..., strict=True)                                  # la del MES, != 0
    precio: float = Field(..., strict=True)
    descripcion: str = Field(..., min_length=1, max_length=128)                # -> dcapro.res
    partida: str | None = Field(default=None, min_length=1, max_length=24)
    medicion_contrato: float | None = Field(default=None, strict=True)
    unidad: str | None = Field(default=None, max_length=8)
    cantidad_anterior: float | None = Field(default=None, strict=True)
    cantidad_origen: float | None = Field(default=None, strict=True)
    ctrpro_ide: int | None = Field(default=None, ge=1, strict=True)
    producto: str | None = Field(default=None, min_length=1, max_length=24)
    partida_imputacion: str | None = Field(default=None, min_length=1, max_length=24)

    @field_validator(
        "referencia_linea", "descripcion", "partida", "producto", "partida_imputacion",
        mode="before",
    )
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)

    @field_validator("unidad", mode="before")
    @classmethod
    def _recortar_unidad(cls, value: object) -> object:
        return _recortar_o_nada(value)

    @model_validator(mode="after")
    def _reglas_de_linea(self) -> LineaProformaIn:
        if self.ctrpro_ide is not None and self.producto is not None:
            raise ValueError("'ctrpro_ide' y 'producto' no van juntos en una linea.")
        if self.cantidad == 0:
            raise ValueError("'cantidad' no puede ser 0: solo van las partidas con MES.")
        return self

    @property
    def de_contrato(self) -> bool:
        """R13: de contrato si trae `ctrpro_ide` o `medicion_contrato` > 0."""
        return self.ctrpro_ide is not None or (self.medicion_contrato or 0) > 0


def _es_fecha(valor: int) -> bool:
    try:
        date(valor // 10000, (valor // 100) % 100, valor % 100)
    except ValueError:
        return False
    return 19000101 <= valor <= 29991231


class ProformaRequest(BaseModel):
    """
    Peticion de `sigrid/proforma` (R1-R3). `commit=False` (por defecto) =>
    previa: solo lecturas. El prefijo de la referencia y el tope de lineas son
    configuracion y los aplica el caso de uso con codigo (R26).
    """

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    database: str = Field(..., min_length=1)
    usu: str = Field(..., min_length=1, max_length=24)                         # quien aprueba
    referencia_externa: str = Field(..., min_length=1, max_length=128)         # dca.synckey
    cod_obra: str = Field(..., min_length=1, max_length=24)
    periodo: int = Field(..., strict=True)                                     # AAAAMM
    importe_mes: float = Field(..., strict=True)
    lineas: list[LineaProformaIn] = Field(..., min_length=1)                   # orden = dcapro.pos
    cod_contrato: str | None = Field(default=None, min_length=1, max_length=24)
    cif_proveedor: str | None = Field(default=None, min_length=1, max_length=24)
    nombre_proveedor: str | None = Field(default=None, min_length=1, max_length=128)
    sin_contrato: bool = False
    otra_del_mes: bool = False
    fecha_proforma: int | None = Field(default=None, strict=True)              # AAAAMMDD
    su_referencia: str | None = Field(default=None, max_length=128)            # dca.entref
    importe_anterior: float | None = Field(default=None, strict=True)
    importe_origen: float | None = Field(default=None, strict=True)
    numero_orden: int | None = Field(default=None, ge=0, strict=True)          # solo traza
    commit: bool = False

    @field_validator(
        "database", "usu", "referencia_externa", "cod_obra", "cod_contrato", "nombre_proveedor",
        mode="before",
    )
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)

    @field_validator("cif_proveedor", mode="before")
    @classmethod
    def _normalizar_cif(cls, value: object) -> object:
        """Como F-009 H21: mayusculas y sin espacios."""
        if isinstance(value, str):
            return "".join(value.split()).upper()
        return value

    @field_validator("su_referencia", mode="before")
    @classmethod
    def _recortar_su_referencia(cls, value: object) -> object:
        return _recortar_o_nada(value)

    @field_validator("periodo")
    @classmethod
    def _periodo_aaaamm(cls, value: int) -> int:
        if not (190001 <= value <= 299912 and 1 <= value % 100 <= 12):
            raise ValueError("'periodo' es AAAAMM con el mes de 1 a 12.")
        return value

    @field_validator("fecha_proforma")
    @classmethod
    def _fecha_aaaammdd(cls, value: int | None) -> int | None:
        if value is not None and not _es_fecha(value):
            raise ValueError("'fecha_proforma' es una fecha AAAAMMDD.")
        return value

    @model_validator(mode="after")
    def _reglas_de_peticion(self) -> ProformaRequest:
        vistas: set[str] = set()
        for linea in self.lineas:
            if linea.referencia_linea in vistas:
                raise ValueError(f"'referencia_linea' repetida: {linea.referencia_linea!r}.")
            vistas.add(linea.referencia_linea)
        # R3.
        if self.cod_contrato is None and self.cif_proveedor is None and self.nombre_proveedor is None:
            raise ValueError("Hace falta 'cod_contrato', 'cif_proveedor' o 'nombre_proveedor'.")
        if self.sin_contrato:
            if self.cif_proveedor is None:
                raise ValueError("'sin_contrato' exige 'cif_proveedor'.")
            if self.cod_contrato is not None:
                raise ValueError("'sin_contrato' no va con 'cod_contrato'.")
            if any(linea.ctrpro_ide is not None for linea in self.lineas):
                raise ValueError("'sin_contrato' no admite lineas con 'ctrpro_ide'.")
        return self


class ContratoResuelto(BaseModel):
    """R10: el contrato elegido y como (`peticion`, `proveedor` o `lineas`)."""

    cod: str
    ide: int
    resuelto_por: ResueltoPor
    candidatos: list[str] = Field(default_factory=list)


class OrigenProforma(BaseModel):
    """R20, R21, R30: lo registrado en Sigrid antes del mes y frente al contrato."""

    importe_anterior_sigrid: float
    importe_mes: float
    importe_origen: float
    importe_contrato: float
    porcentaje_contrato: float | None = None


class LineaProformaResultado(LineaResultado):
    """
    Una linea de la respuesta (R30): la del nucleo mas `de_contrato` y
    `cantidad_anterior_sigrid` (las de contrato; `None` en las nuevas). En
    `existente` son las LEIDAS (LP6) con `dcapro_ide`, `linoriide`, `producto`,
    `cantidad`, `precio` e `importe`.
    """

    avisos: list[AvisoProforma] = Field(default_factory=list)
    de_contrato: bool | None = None
    cantidad_anterior_sigrid: float | None = None
    dcapro_ide: int | None = None
    importe: float | None = None


class ProformaResponse(AlbaranCompraResponse):
    """
    Respuesta de `sigrid/proforma`: la del modo extendido de `sigrid/albaran`
    (con sus garantias: `warnings` derivados y sin columnas bancarias) mas
    `existente`, `contrato` y `origen` (`None` sin contrato).
    """

    estado: EstadoProforma  # type: ignore[assignment]
    contrato: ContratoResuelto | None = None  # type: ignore[assignment]
    origen: OrigenProforma | None = None
    avisos: list[AvisoProforma] = Field(default_factory=list)  # type: ignore[assignment]
    lineas: list[LineaProformaResultado] = Field(default_factory=list)  # type: ignore[assignment]
