# domain/models/parte_reclamacion_models.py
"""
Contrato de `POST /api/sigrid/partes-reclamacion` (F-006).

Alta EN LOTE de partes de reclamacion de Posventa (`con.tip 708`, serie
`RS<aa>.<mm>/`) de UNA obra, como los crea el escritorio de Sigrid desde la
pestana Reclamaciones de la unidad postventa. El cliente habla por CODIGOS
(obra, unidad postventa, tipo, clase, oficio, proveedor) y NUNCA manda `ide`,
`cod`, `emp`, `est` ni `pos`: los decide el servidor con lo medido en
`progress/explore_F-006_modelo_parte.md`.

La respuesta es parte a parte: un parte rechazado no tumba el lote (R2, R7).
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Fallos del LOTE (R3): ninguna escritura, 400 con `details.codigo`.
CODIGOS_DE_LOTE: frozenset[str] = frozenset(
    {
        "escritura_reclamaciones_deshabilitada",
        "base_de_datos_no_permitida",
        "lote_demasiado_grande",
        "obra_no_encontrada",
        "usuario_no_valido",
        "serie_no_encontrada",
        "estado_inicial_no_encontrado",
    }
)

#: Fallos de UN parte (R7, R8, R12-R15, R17): el parte queda `rechazado` o
#: `no_procesado` y el lote sigue.
CODIGOS_DE_PARTE: frozenset[str] = frozenset(
    {
        "referencia_no_permitida",
        "referencia_duplicada_en_lote",
        "referencia_en_conflicto",
        "unidad_postventa_no_encontrada",
        "tipo_no_valido",
        "clase_no_valida",
        "oficio_no_esta_en_la_obra",
        "interviniente_no_esta_en_la_obra",
        "interviniente_ambiguo",
        "interviniente_repetido",
        "numeracion_agotada",
        "colision_de_clave",
        "filas_afectadas_inesperadas",
        "presupuesto_de_tiempo_agotado",
        "error_de_escritura",
    }
)

#: Cerrada a proposito: el cliente decide por el `codigo`, asi que inventarse
#: uno le rompe el contrato en silencio.
CODIGOS_DE_ERROR: frozenset[str] = CODIGOS_DE_LOTE | CODIGOS_DE_PARTE

EstadoParte = Literal["previsto", "creado", "idempotente", "rechazado", "no_procesado"]


class ParteReclamacionError(ValueError):
    """Fallo de negocio del endpoint, con el `codigo` que viaja en la respuesta."""

    def __init__(self, mensaje: str, *, codigo: str) -> None:
        if codigo not in CODIGOS_DE_ERROR:
            raise ValueError(
                f"'{codigo}' no es un codigo de error de sigrid/partes-reclamacion. "
                f"Permitidos: {', '.join(sorted(CODIGOS_DE_ERROR))}"
            )
        super().__init__(mensaje)
        self.codigo = codigo


def _recortar(value: object) -> object:
    """Recorta SOLO cadenas: un numero no se convierte en texto por las buenas,
    y el `None` de un opcional sigue siendo `None`."""
    return value.strip() if isinstance(value, str) else value


class IntervinienteIn(BaseModel):
    """Un interviniente (`rcpint`): un oficio de la obra y, si hay varios
    proveedores para ese oficio, cual."""

    model_config = ConfigDict(extra="forbid")

    oficio: str = Field(..., min_length=1, max_length=24)
    proveedor: str | None = Field(default=None, min_length=1, max_length=24)
    causante: bool = False                                   # -> rcpint.cauave 1/0

    @field_validator("oficio", "proveedor", mode="before")
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)


class ParteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    referencia_externa: str = Field(..., min_length=1, max_length=80)   # conext.valt
    unidad_postventa: str = Field(..., min_length=1, max_length=24)
    descripcion: str = Field(..., min_length=1, max_length=128)         # con.res
    descripcion_larga: str | None = None                                # rcp.tex (defecto: descripcion)
    tipo: str = Field(default="0002", min_length=1, max_length=24)      # auxtrcp.cod
    clase: str | None = Field(default=None, min_length=1, max_length=24)  # auxrcp.cod
    oficio: str = Field(..., min_length=1, max_length=24)               # auxofc.cod
    ubicacion: str = Field(default="", max_length=48)                   # rcp.resubi
    forma_comunicacion: Literal[0, 1] = 1                               # rcp.rcptip, 1 «Escrita» (Q2)
    intervinientes: list[IntervinienteIn] = Field(default_factory=list, max_length=10)

    @field_validator(
        "referencia_externa",
        "unidad_postventa",
        "descripcion",
        "descripcion_larga",
        "tipo",
        "clase",
        "oficio",
        "ubicacion",
        mode="before",
    )
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)


class CreatePartesReclamacionRequest(BaseModel):
    """
    Lote de partes de UNA obra. `commit=False` (por defecto) => DRY-RUN: solo
    lecturas, con credenciales de lectura, y preview completo de las filas.

    El tope del lote NO va aqui: es configuracion
    (`SIGRID_RECLAMACION_MAX_PARTES`) y lo aplica el caso de uso antes de leer.
    """

    model_config = ConfigDict(extra="forbid")

    database: str
    obra: str = Field(..., min_length=1, max_length=24)
    usu: str = Field(..., min_length=1, max_length=24)                  # dbo.usu.cod
    partes: list[ParteIn] = Field(..., min_length=1)
    commit: bool = False

    @field_validator("database", "obra", "usu", mode="before")
    @classmethod
    def _recortar_textos(cls, value: object) -> object:
        return _recortar(value)


class MotivoParte(BaseModel):
    codigo: str
    mensaje: str

    @field_validator("codigo")
    @classmethod
    def _codigo_cerrado(cls, value: str) -> str:
        if value not in CODIGOS_DE_ERROR:
            raise ValueError(f"'{value}' no es un codigo de sigrid/partes-reclamacion.")
        return value


class ObraResumen(BaseModel):
    ide: int
    cod: str
    emp: int


class ResumenLote(BaseModel):
    creados: int = 0
    idempotentes: int = 0
    previstos: int = 0
    rechazados: int = 0
    no_procesados: int = 0


class ResultadoParte(BaseModel):
    """
    El resultado de UN parte, en el orden de la peticion (`indice` desde 0).

    `filas` lleva, por tabla, las filas que se escribirian (dry-run) o que se
    escribieron (commit): `con`, `rcp`, `rcpint` (lista), `conext` y `log`.
    Vacio si el parte se rechazo, no se proceso o ya existia.
    """

    indice: int
    referencia_externa: str
    estado: EstadoParte
    ide: int | None = None
    cod: str | None = None
    motivo: MotivoParte | None = None
    filas: dict[str, Any] = Field(default_factory=dict)
    avisos: list[str] = Field(default_factory=list)


class CreatePartesReclamacionResponse(BaseModel):
    """Misma forma en dry-run y en commit (R2). Un lote con partes rechazados
    responde 200: el fallo de un parte va en SU resultado."""

    ok: bool = True
    committed: bool
    dry_run: bool
    database: str
    obra: ObraResumen
    resumen: ResumenLote
    avisos: list[str] = Field(default_factory=list)
    partes: list[ResultadoParte] = Field(default_factory=list)
