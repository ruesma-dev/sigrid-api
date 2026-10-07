# domain/models/albaran_compra_models.py
"""
Contrato del modo EXTENDIDO de `POST /api/sigrid/albaran` (F-009).

Alta idempotente de UN albaran de compra (`con.tip 14`) con lineas vinculadas a
un contrato (`ctrpro_ide`) y sin vincular (`producto` de la lista blanca), con
o sin partida por linea y con devoluciones (cantidad < 0). La forma campo a
campo, los casos de linea y los codigos estan en
`specs/F-009-alta-albaran-compra/contrato_albaranes.md` §2-§3, congelados: son
la referencia de albaranes F-053.

El modo CLASICO no pasa por aqui: sigue en `albaran_domain_models.py`, que se
IMPORTA y no se edita (R2, R4). La respuesta extendida es un superconjunto de
la clasica (R7).
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from domain.models.albaran_domain_models import (
    AddPurchaseAlbaranResponse,
    AlbaranLinePreview,
)

ModoAlbaran = Literal["clasico", "extendido"]
EstadoAlbaran = Literal["previsto", "creado", "idempotente"]
TipoLinea = Literal["vinculada", "sin_vincular"]

#: Errores de CABECERA (R9, design §Codigos): 400 con `details.codigo`. Cortan
#: antes de mirar las lineas, salvo `lineas_no_validas`, que las trae todas.
CODIGOS_CABECERA: frozenset[str] = frozenset(
    {
        "peticion_mixta",
        "escritura_albaranes_deshabilitada",
        "base_de_datos_no_permitida",
        "demasiadas_lineas",
        "referencia_no_permitida",
        "referencia_en_conflicto",
        "obra_no_encontrada",
        "obra_de_empresa_no_permitida",
        "obra_ambigua",
        "contrato_no_encontrado",
        "contrato_ambiguo",
        "usuario_no_valido",
        "proveedor_sin_albaran_previo",
        "estado_inicial_no_encontrado",
        "almacen_de_obra_no_resuelto",
        "colision_de_clave",
        "filas_afectadas_inesperadas",
        "lineas_no_validas",
    }
)

#: Errores de LINEA: viajan dentro de `lineas_no_validas`, nunca sueltos.
CODIGOS_LINEA: frozenset[str] = frozenset(
    {
        "linea_no_es_del_contrato",
        "producto_no_permitido",
        "producto_no_encontrado",
        "partida_no_encontrada",
        "partida_ambigua",
        "partida_no_imputable",
        "precio_negativo",
        "paride_no_valido",
        "naturaleza_no_valida",
        "analitica_no_resuelta",
    }
)

#: Avisos (no impiden el alta), en cabecera o en linea (H27).
CODIGOS_AVISO: frozenset[str] = frozenset(
    {
        "producto_sin_historico",
        "supera_pendiente",
        "partida_distinta_del_contrato",
        "sin_partida_en_linea_con_partida",
        "precio_distinto_del_contrato",
        "iva_de_otro_proveedor",
        "servido_negativo",
        "stock_negativo",
        "cod_provisional",
    }
)

#: Columnas de `dca` con datos bancarios del proveedor (H16, diccionario de
#: Sigrid). Se ESCRIBEN igual que hoy, pero no salen en la respuesta ni en
#: las trazas: albaranes guarda la respuesta en un PostgreSQL compartido.
COLUMNAS_BANCARIAS: tuple[str, ...] = (
    "banide",
    "banban",
    "bansuc",
    "bandig",
    "bancue",
    "ban",
    "bantipide",
    "cpapai",
    "cpaban",
    "cpasuc",
    "cpaswi",
    "cpatip",
    "cpadiv",
    "cpacue1",
    "cpacue2",
)

#: Las dos claves que hacen extendida una peticion, y la del clasico que no
#: puede ir con ellas (R1).
_CLAVES_EXTENDIDO = ("lineas", "referencia_externa")
_CLAVE_CLASICO = "lineas_recibidas"


class FalloLinea(BaseModel):
    """Una linea que no vale, dentro de `details.lineas` (R9)."""

    indice: int = Field(..., ge=0)
    referencia_linea: str
    codigo: str
    mensaje: str

    @field_validator("codigo")
    @classmethod
    def _codigo_de_linea(cls, value: str) -> str:
        if value not in CODIGOS_LINEA:
            raise ValueError(f"'{value}' no es un codigo de linea de sigrid/albaran.")
        return value


class AlbaranCompraError(ValueError):
    """
    Fallo de negocio del modo extendido, con el `codigo` que viaja en
    `details.codigo` (R9). La lista es CERRADA: F-053 decide por el codigo, y
    uno inventado le romperia el contrato en silencio.

    `lineas` va si y solo si el codigo es `lineas_no_validas`, y entonces con
    TODAS las lineas que fallan.
    """

    def __init__(
        self, mensaje: str, *, codigo: str, lineas: list[FalloLinea] | None = None
    ) -> None:
        if codigo not in CODIGOS_CABECERA:
            raise ValueError(
                f"'{codigo}' no es un codigo de error de sigrid/albaran. "
                f"Permitidos: {', '.join(sorted(CODIGOS_CABECERA))}"
            )
        lineas = list(lineas or [])
        if codigo == "lineas_no_validas" and not lineas:
            raise ValueError("'lineas_no_validas' exige las lineas que fallan.")
        if codigo != "lineas_no_validas" and lineas:
            raise ValueError(f"Solo 'lineas_no_validas' lleva lineas, no '{codigo}'.")
        super().__init__(mensaje)
        self.codigo = codigo
        self.lineas = lineas


def elegir_modo_albaran(cuerpo: object) -> ModoAlbaran:
    """
    R1: el modo sale de las CLAVES presentes, no de sus valores, y antes de
    validar nada. Con `lineas` o `referencia_externa`, extendido; sin ninguna,
    clasico. Si ademas viene `lineas_recibidas`, `peticion_mixta`: el clasico
    ignora las claves que no conoce y olvidaria las lineas sin avisar.

    Lo que no es un objeto JSON va al clasico, que lo rechaza como hoy.
    """
    if not isinstance(cuerpo, dict):
        return "clasico"
    if not any(clave in cuerpo for clave in _CLAVES_EXTENDIDO):
        return "clasico"
    if _CLAVE_CLASICO in cuerpo:
        raise AlbaranCompraError(
            "La peticion mezcla 'lineas_recibidas' (modo clasico) con 'lineas' o "
            "'referencia_externa' (modo extendido).",
            codigo="peticion_mixta",
        )
    return "extendido"


def _recortar(value: object) -> object:
    """Recorta SOLO cadenas: un numero no se convierte en texto por las buenas,
    y el `None` de un opcional sigue siendo `None`."""
    return value.strip() if isinstance(value, str) else value


def _recortar_o_nada(value: object) -> object:
    """Como `_recortar`, pero un texto vacio es un campo ausente."""
    value = _recortar(value)
    return None if value == "" else value


def sin_columnas_bancarias(fila: Mapping[str, Any]) -> dict[str, Any]:
    """Copia de `fila` sin las columnas de `COLUMNAS_BANCARIAS` (H16)."""
    return {columna: valor for columna, valor in fila.items() if columna not in COLUMNAS_BANCARIAS}


class LineaAlbaranIn(BaseModel):
    """
    Una linea del albaran (R5, R6). Vinculada (`ctrpro_ide`) o sin vincular
    (`producto`), nunca las dos ni ninguna. `partida` ausente o `null` = sin
    partida (`paride` 0). No hay campo `almacen` (v5.1) ni `naturaleza` (v8,
    H34): con `extra="forbid"`, mandarlos da 400 sin codigo.

    Numeros como numeros JSON (`strict`): un texto o un booleano no cuelan
    como cantidad. `precio` no lleva `ge`: el negativo es un fallo de linea
    con codigo (`precio_negativo`) que decide el caso de uso.
    """

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    referencia_linea: str = Field(..., min_length=1, max_length=24)          # -> dcapro.refent
    ctrpro_ide: int | None = Field(default=None, ge=1, strict=True)          # vinculada
    producto: str | None = Field(default=None, min_length=1, max_length=24)  # sin vincular
    descripcion: str | None = Field(default=None, max_length=128)            # dcapro.res
    unidad: str | None = Field(default=None, max_length=8)                   # dcapro.unimed
    cantidad: float = Field(..., strict=True)                                # != 0; < 0 devolucion
    precio: float = Field(..., strict=True)
    partida: str | None = Field(default=None, min_length=1, max_length=24)   # None: sin partida
    paride: int | None = Field(default=None, ge=1, strict=True)              # R14b; exige partida

    @field_validator("referencia_linea", "producto", "partida", mode="before")
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)

    @field_validator("descripcion", "unidad", mode="before")
    @classmethod
    def _recortar_opcionales(cls, value: object) -> object:
        return _recortar_o_nada(value)

    @model_validator(mode="after")
    def _reglas_de_linea(self) -> LineaAlbaranIn:
        if (self.ctrpro_ide is None) == (self.producto is None):
            raise ValueError("Cada linea lleva 'ctrpro_ide' (vinculada) o 'producto' (sin vincular), uno solo.")
        if self.cantidad == 0:
            raise ValueError("'cantidad' no puede ser 0.")
        if self.producto is not None and self.descripcion is None:
            raise ValueError("Una linea sin vincular necesita 'descripcion'.")
        if self.paride is not None and self.partida is None:
            raise ValueError("'paride' solo va con 'partida'.")
        return self

    @property
    def tipo(self) -> TipoLinea:
        return "vinculada" if self.ctrpro_ide is not None else "sin_vincular"


class AlbaranCompraRequest(BaseModel):
    """
    Peticion del modo extendido (R5, R6). `commit=False` (por defecto) =>
    previa: solo lecturas con credenciales de lectura (R23).

    El tope de lineas (`SIGRID_ALBARAN_MAX_LINEAS`) y el prefijo de la
    referencia son configuracion y los aplica el caso de uso con codigo
    (`demasiadas_lineas`, `referencia_no_permitida`), tambien en previa.
    """

    model_config = ConfigDict(extra="forbid")

    database: str = Field(..., min_length=1)
    cod_obra: str = Field(..., min_length=1, max_length=24)
    usu: str = Field(..., min_length=1, max_length=24)                       # dbo.usu.cod -> log.usu
    cif_proveedor: str = Field(..., min_length=1, max_length=24)             # H21
    referencia_externa: str = Field(..., min_length=1, max_length=128)       # dca.synckey
    cod_contrato: str | None = Field(default=None, min_length=1, max_length=24)
    su_referencia: str = Field(default="", max_length=128)                   # dca.entref
    fecha_albaran: int | None = Field(default=None, ge=19000101, le=29991231, strict=True)
    empide: int | None = Field(default=None, ge=1, strict=True)
    lineas: list[LineaAlbaranIn] = Field(..., min_length=1)                  # orden = dcapro.pos
    commit: bool = False

    @field_validator(
        "database", "cod_obra", "usu", "referencia_externa", "cod_contrato", mode="before"
    )
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)

    @field_validator("cif_proveedor", mode="before")
    @classmethod
    def _normalizar_cif(cls, value: object) -> object:
        """H21: mayusculas y sin espacios. El resto del formato es de albaranes."""
        if isinstance(value, str):
            return "".join(value.split()).upper()
        return value

    @field_validator("su_referencia", mode="before")
    @classmethod
    def _recortar_su_referencia(cls, value: object) -> object:
        return "" if value is None else _recortar(value)

    @model_validator(mode="after")
    def _reglas_de_peticion(self) -> AlbaranCompraRequest:
        vistas: set[str] = set()
        for linea in self.lineas:
            if linea.referencia_linea in vistas:
                raise ValueError(f"'referencia_linea' repetida: {linea.referencia_linea!r}.")
            vistas.add(linea.referencia_linea)
        if self.cod_contrato is None and any(linea.tipo == "vinculada" for linea in self.lineas):
            raise ValueError("Una linea vinculada exige 'cod_contrato'.")
        return self


class AvisoAlbaran(BaseModel):
    """Aviso con codigo (H27): F-053 decide por el `codigo`, nunca por el texto."""

    codigo: str
    mensaje: str

    @field_validator("codigo")
    @classmethod
    def _codigo_de_aviso(cls, value: str) -> str:
        if value not in CODIGOS_AVISO:
            raise ValueError(f"'{value}' no es un codigo de aviso de sigrid/albaran.")
        return value


class LineaResultado(AlbaranLinePreview):
    """
    Una linea de la respuesta: lo de la clasica mas lo del extendido (R7).
    `ctrpro_ide`/`linoriide` 0 en las sin vincular; `paride` 0 y `partida`
    `None` sin partida. En `idempotente` son las LEIDAS de Sigrid por `pos`
    (con `referencia_linea` de `dcapro.refent`, R30c) y el resto va vacio.
    """

    indice: int = Field(..., ge=0)                       # posicion en la peticion, desde 0 (H26)
    referencia_linea: str
    tipo: TipoLinea | None = None                        # None en idempotente
    producto: str | None = None
    paride: int = Field(default=0, ge=0)
    partida: str | None = None
    cenide: int | None = None
    pos: int | None = None                               # solo en idempotente
    avisos: list[AvisoAlbaran] = Field(default_factory=list)


class AlbaranCompraResponse(AddPurchaseAlbaranResponse):
    """
    Respuesta del modo extendido: superconjunto de la clasica (R7), con la
    misma forma en `previsto`, `creado` e `idempotente`.

    Dos garantias que da el propio modelo, para que ningun camino del caso de
    uso pueda saltarselas:
    - `warnings` son los `mensaje` de todos los avisos (cabecera y despues
      cada linea, en orden) y nada mas (H27).
    - `cabecera` y `filas["dca"]` salen sin `COLUMNAS_BANCARIAS` (H16).
    """

    estado: EstadoAlbaran
    referencia_externa: str
    avisos: list[AvisoAlbaran] = Field(default_factory=list)
    lineas: list[LineaResultado] = Field(default_factory=list)
    # `con`, `dca`, `dcapro[]`, `ctrprodes[]`, `mov[]`, `log`; vacio en idempotente.
    filas: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _derivados(self) -> AlbaranCompraResponse:
        self.warnings = [aviso.mensaje for aviso in self.avisos] + [
            aviso.mensaje for linea in self.lineas for aviso in linea.avisos
        ]
        self.cabecera = sin_columnas_bancarias(self.cabecera)
        if isinstance(self.filas.get("dca"), Mapping):
            self.filas = {**self.filas, "dca": sin_columnas_bancarias(self.filas["dca"])}
        return self
