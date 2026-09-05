# domain/models/concepto_grafico_models.py
"""
Contrato de `POST /api/sigrid/concepto-grafico` (F-004).

Adjuntar un documento a un concepto de Sigrid son TRES filas: el binario en la
base documental (`ruesma_rep.dbo.gra`), los metadatos en la de negocio
(`ruesma.dbo.gra`, con el MISMO `cod` y el MISMO `emp`) y el enlace con el
concepto (`ruesma.dbo.rcg`). El cliente no elige ninguna de esas piezas: no
manda base documental, ni tabla, ni columna, ni `ide`, ni `cod`, ni `vin`.
Todo eso lo decide el servidor con constantes medidas contra el ERP
(`progress/explore_F-004_mediciones.md`).
"""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

#: Codigos de error de negocio (R3). Cerrada a proposito: el cliente decide por
#: el `codigo`, asi que inventarse uno le rompe el contrato en silencio.
CODIGOS_DE_ERROR: frozenset[str] = frozenset(
    {
        "escritura_documental_deshabilitada",
        "base_de_datos_no_permitida",
        "concepto_no_encontrado",
        "tipo_de_concepto_no_coincide",
        "clase_de_grafico_no_permitida",
        "usuario_no_valido",
        "fichero_vacio",
        "tipo_de_fichero_no_permitido",
        "tamano_excedido",
        "sha256_no_coincide",
        "colision_de_clave",
        "filas_afectadas_inesperadas",
    }
)

#: Alfabeto de base64 estandar con su relleno. No decodifica: solo comprueba la
#: forma, para que un fichero enorme no se decodifique antes de que el guard
#: mire el tope de tamano (R8).
_BASE64_RE = re.compile(r"[A-Za-z0-9+/]+={0,2}")


class ConceptoGraficoError(ValueError):
    """Fallo de negocio del endpoint, con el `codigo` que viaja en la respuesta."""

    def __init__(self, mensaje: str, *, codigo: str) -> None:
        if codigo not in CODIGOS_DE_ERROR:
            raise ValueError(
                f"'{codigo}' no es un codigo de error de sigrid/concepto-grafico. "
                f"Permitidos: {', '.join(sorted(CODIGOS_DE_ERROR))}"
            )
        super().__init__(mensaje)
        self.codigo = codigo


class AttachConceptoGraficoRequest(BaseModel):
    """
    Peticion para adjuntar un documento a un concepto.

    `commit=False` (por defecto) => DRY-RUN: solo lecturas, con credenciales de
    lectura, y preview completo de las tres filas.
    """

    model_config = ConfigDict(extra="ignore")

    database: str = Field(..., min_length=1)          # base de NEGOCIO (ruesma)
    conide: int = Field(..., ge=1)                    # con.ide del concepto
    contip: int = Field(..., ge=1)                    # con.tip esperado (se coteja)
    gratipide: int = Field(..., ge=1)                 # clase de grafico (auxgra.ide)
    res: str = Field(..., min_length=1, max_length=48)
    nom: str = Field(..., min_length=1, max_length=255)
    # A proposito 24: gra.usu es varchar(128), pero el login tiene que existir
    # en usu.cod, que es Texto 24.
    usu: str = Field(..., min_length=1, max_length=24)
    contenido_base64: str = Field(..., min_length=4)
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    commit: bool = False

    @field_validator("database", "res", "nom", "usu", mode="before")
    @classmethod
    def _recortar(cls, value: object) -> str:
        return str(value).strip()

    @field_validator("contenido_base64", mode="before")
    @classmethod
    def _base64_bien_formado(cls, value: object) -> str:
        """
        Normaliza (quita los saltos de linea con que muchos clientes parten el
        base64) y comprueba la FORMA sin decodificar. Decodificar aqui obligaria
        a materializar el fichero entero antes de que nadie haya mirado el tope
        de `SIGRID_DOCUMENT_MAX_BYTES`.
        """
        limpio = "".join(str(value).split())
        if not limpio or len(limpio) % 4 != 0 or not _BASE64_RE.fullmatch(limpio):
            raise ValueError("contenido_base64 no es base64 valido.")
        return limpio


class ConceptoPreview(BaseModel):
    """El concepto al que se adjunta, tal y como esta en `dbo.con`."""

    ide: int
    tip: int
    emp: int
    cod: str
    res: str | None = None


class GraficoPreview(BaseModel):
    """
    Las dos filas `gra` que se escriben (o que ya existian, si es idempotente).

    El binario NUNCA viaja de vuelta: van su tamano y su `sha256`, que es lo que
    permite comprobar con `documents/read` que se guardo el fichero correcto.
    """

    ide_documental: int | None = None
    ide_negocio: int | None = None
    cod: str
    emp: int
    nom: str
    fec: int
    usu: str
    res: str
    gratipide: int
    vin: int
    bytes: int
    sha256: str
    content_type: str

    # Las filas completas (29 columnas) que se insertarian, para que el humano
    # pueda revisarlas en el dry-run. `ima` va como su tamano, no como bytes.
    fila_documental: dict[str, Any] = Field(default_factory=dict)
    fila_negocio: dict[str, Any] = Field(default_factory=dict)


class EnlacePreview(BaseModel):
    """La fila de `dbo.rcg` que enlaza el concepto con el grafico de negocio."""

    ide: int | None = None
    con: int
    gra: int | None = None
    # None cuando es idempotente: se conoce el enlace existente, no su posicion.
    pos: int | None = None
    cla: int = 0
    feclee: int = 0
    fecalt: int = 0


class AttachConceptoGraficoResponse(BaseModel):
    """Misma forma en dry-run y en commit (R2)."""

    ok: bool = True
    committed: bool
    dry_run: bool
    idempotente: bool
    database: str
    database_documental: str
    concepto: ConceptoPreview
    grafico: GraficoPreview
    enlace: EnlacePreview
    filas_afectadas: int
    avisos: list[str] = Field(default_factory=list)
