# application/use_cases/proforma_origen_statements.py
"""
SQL y funciones puras de la proforma A ORIGEN de `sigrid/proforma` (F-016).

Las sentencias LP7-LP9 (design §SQL nuevo) son constantes, de LECTURA, con
marcadores `?` y validadas con `DatabaseReferenceGuard` contra la base de la
peticion al construir `ProformaOrigenStatements` (R22). Nada de `DELETE`,
`MERGE`, DDL ni `UPDATE`: lo que se escribe es lo del nucleo de F-009 mas las
`dcapro` arrastradas, que van en su mismo `INSERT` clonado.

La API registra y valida (alcance del humano, 2026-10-28): la anterior y las
continuaciones las manda el llamante. Las funciones validan la anterior (R6,
R7), las continuaciones (R9) y su aviso de integridad (R10), y construyen las
columnas a origen (R11, R13), las arrastradas (R12), la ya registrada (R5) y
el importe de cadena de la respuesta (R19). Sin E/S.
"""
from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from application.use_cases.albaran_compra_statements import (
    _SEGUIMIENTO_A_CERO,
    POS_PASO,
    TIP_ALBARAN,
    redondear_euros,
)
from application.use_cases.proforma_statements import (
    DOCORITIP_A_ORIGEN,
    TOLERANCIA_IMPORTE,
    LineaContrato,
    ProformaRegistrada,
    _d,
    _texto,
    buscar_del_mes,
)
from domain.models.proforma_models import LineaProformaIn
from domain.models.proforma_origen_models import (
    AvisoProformaOrigen,
    FalloLineaProformaOrigen,
    ProformaOrigenError,
)
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard

# --- Lecturas (credenciales de lectura) -------------------------------------------

#: LP7 (R6): la anterior que indica el llamante, por su `con.cod` en el contrato.
LP7_PROFORMA_ANTERIOR = (
    "SELECT c.ide, c.cod, c.fec, d.docoritip FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide "
    "WHERE c.tip = ? AND d.ctride = ? AND c.cod = ?"
)
#: LP8 (R7, R17): los `tip 14` del contrato que ya cuelgan de la anterior.
LP8_SUCESORAS = (
    "SELECT c.ide, c.cod FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? "
    "AND d.ctride = ? AND d.docoriide = ?"
)
#: LP9 (R9-R12, R19): las lineas COMPLETAS de la anterior, plantilla de las arrastradas.
LP9_LINEAS_ANTERIOR = "SELECT * FROM dbo.dcapro WHERE docide = ? ORDER BY pos, ide"


class ProformaOrigenStatements:
    """Las sentencias de F-016 con sus parametros, validadas al construirse."""

    def __init__(self, *, database: str) -> None:
        self._database = database.strip()
        for sql in self.todas_las_sentencias():
            DatabaseReferenceGuard.validate(sql, allowed=[self._database], contexto="lectura")

    @staticmethod
    def todas_las_sentencias() -> tuple[str, ...]:
        return (LP7_PROFORMA_ANTERIOR, LP8_SUCESORAS, LP9_LINEAS_ANTERIOR)

    def leer_proforma_anterior(self, ctride: int, cod: str) -> tuple[str, list[Any]]:
        return LP7_PROFORMA_ANTERIOR, [TIP_ALBARAN, ctride, cod]

    def leer_sucesoras(self, ctride: int, ide_anterior: int) -> tuple[str, list[Any]]:
        """LP8: fuera y, dentro de la transaccion, por el cursor del `work` (R17)."""
        return LP8_SUCESORAS, [TIP_ALBARAN, ctride, ide_anterior]

    def leer_lineas_anterior(self, ide_anterior: int) -> tuple[str, list[Any]]:
        return LP9_LINEAS_ANTERIOR, [ide_anterior]


# --- La anterior (R6, R7) ------------------------------------------------------------


@dataclass(frozen=True)
class DocumentoCadena:
    """La anterior de la cadena (LP7)."""

    ide: int
    cod: str
    fec: int
    docoritip: int

    @classmethod
    def de_fila(cls, fila: Sequence[Any]) -> DocumentoCadena:
        ide, cod, fec, docoritip = fila
        return cls(ide=int(ide), cod=_texto(cod), fec=int(fec or 0),
                   docoritip=int(docoritip or 0))


@dataclass(frozen=True)
class CadenaValidada:
    """Lo validado de la cadena, que viaja en el contexto del alta: la anterior
    (`None` en la primera), sus lineas completas (LP9), las continuaciones
    (indice de la peticion -> fila de la anterior) y los avisos de R10."""

    anterior: DocumentoCadena | None
    filas: list[dict[str, Any]]
    continuadas: dict[int, dict[str, Any]]
    avisos: dict[int, AvisoProformaOrigen]

    @property
    def n_arrastradas(self) -> int:
        return len(self.filas) - len(self.continuadas)


def validar_anterior(filas_lp7: Sequence[Sequence[Any]], *, cod: str, fecha: int) -> DocumentoCadena:
    """R6: exactamente un `tip 14` con ese `cod` en el contrato, a origen
    (`docoritip` 1) y con `con.fec` no posterior a la fecha de la proforma."""
    if len(filas_lp7) != 1:
        raise ProformaOrigenError(
            f"El contrato tiene {len(filas_lp7)} proformas '{cod}': la anterior ha de ser una.",
            codigo="anterior_no_valida",
        )
    anterior = DocumentoCadena.de_fila(filas_lp7[0])
    if anterior.docoritip != DOCORITIP_A_ORIGEN:
        raise ProformaOrigenError(
            f"La proforma anterior '{cod}' no es a origen.", codigo="anterior_no_valida"
        )
    if anterior.fec > fecha:
        raise ProformaOrigenError(
            f"La proforma anterior '{cod}' es del {anterior.fec}, posterior a la fecha de esta "
            f"({fecha}).",
            codigo="anterior_no_valida",
        )
    return anterior


def comprobar_sucesoras(filas_lp8: Sequence[Sequence[Any]]) -> None:
    """R7, R17: la cadena es lineal (M19); si la anterior ya tiene sucesora, no
    se le cuelga otra."""
    if filas_lp8:
        raise ProformaOrigenError(
            "La proforma anterior ya tiene sucesora: "
            f"{', '.join(_texto(fila[1]) for fila in filas_lp8)}. Encadena a la ultima.",
            codigo="anterior_con_sucesora",
        )


# --- Lineas (R9, R10) ------------------------------------------------------------------


def _vinculo(fila: Mapping[str, Any]) -> int:
    return int(fila.get("linoriide") or 0)


def validar_continuadas(
    lineas: Sequence[LineaProformaIn],
    identificadas: Mapping[int, LineaContrato],
    filas_anterior: Sequence[Mapping[str, Any]],
) -> tuple[dict[int, dict[str, Any]], list[FalloLineaProformaOrigen]]:
    """
    R9: cada `linea_anterior` es una linea de la anterior y del mismo tipo: del
    mismo `ctrpro` si la linea es de contrato, sin vincular si no. Una de
    contrato que la etapa 1 no ha identificado ya lleva su fallo: solo se mira
    que sea de la anterior. Sin `linea_anterior`, la linea es nueva (D3).
    """
    por_ide = {int(fila["ide"]): dict(fila) for fila in filas_anterior}
    continuadas: dict[int, dict[str, Any]] = {}
    fallos: list[FalloLineaProformaOrigen] = []
    for indice, linea in enumerate(lineas):
        if linea.linea_anterior is None:
            continue
        fila = por_ide.get(linea.linea_anterior)
        if fila is None:
            mensaje = f"La linea {linea.linea_anterior} no es una linea de la proforma anterior."
        elif indice in identificadas:
            if _vinculo(fila) == identificadas[indice].ide:
                continuadas[indice] = fila
                continue
            mensaje = (
                f"La linea {linea.linea_anterior} de la anterior es "
                + (f"de la linea de contrato {_vinculo(fila)}" if _vinculo(fila) else "sin vincular")
                + f", no de la {identificadas[indice].ide}."
            )
        elif linea.de_contrato:
            continue
        elif _vinculo(fila) == 0:
            continuadas[indice] = fila
            continue
        else:
            mensaje = (
                f"La linea {linea.linea_anterior} de la anterior es de contrato y esta va sin "
                "vincular."
            )
        fallos.append(FalloLineaProformaOrigen(
            indice=indice, referencia_linea=linea.referencia_linea,
            codigo="linea_anterior_no_valida", mensaje=mensaje,
        ))
    return continuadas, fallos


def avisos_de_nuevas(
    lineas: Sequence[LineaProformaIn],
    identificadas: Mapping[int, LineaContrato],
    filas_anterior: Sequence[Mapping[str, Any]],
    continuadas: Mapping[int, Any],
) -> dict[int, AvisoProformaOrigen]:
    """R10 (D3): una linea de contrato NUEVA cuyo `ctrpro` ya esta en la
    anterior parte su origen en dos lineas; casi siempre es un olvido, pero
    Sigrid lo admite: aviso con los `dcapro.ide` de esas lineas."""
    avisos: dict[int, AvisoProformaOrigen] = {}
    for indice, ctrpro in identificadas.items():
        if indice in continuadas:
            continue
        ides = [int(fila["ide"]) for fila in filas_anterior if _vinculo(fila) == ctrpro.ide]
        if ides:
            avisos[indice] = AvisoProformaOrigen(
                codigo="linea_nueva_ya_en_la_anterior",
                mensaje=(
                    f"La linea '{lineas[indice].referencia_linea}' va como nueva y la linea de "
                    f"contrato {ctrpro.ide} ya esta en la anterior ({', '.join(map(str, ides))}): "
                    "su origen se parte en dos lineas."
                ),
                lineas_anterior=ides,
            )
    return avisos


# --- Filas a origen (R11-R13) --------------------------------------------------------


def superponer_cadena(
    dcapro: Sequence[Mapping[str, Any]], continuadas: Mapping[int, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """R11 (M41, M23): sobre las `dcapro` del nucleo, en el orden de la
    peticion. Continuada: `canorilin` su linea anterior y `canoriori` el de esa
    mas `can`; `imporiori` el del `ctrpro` (vinculada, ya puesto) o el de la
    anterior (sin vincular). Nueva: `canorilin` 0 y `canoriori` = `can`. En las
    dos, `canoriant` e `imporiant` 0. No toca las filas recibidas."""
    resultado = []
    for indice, fila in enumerate(dcapro):
        nueva = {**fila, "canoriant": 0, "imporiant": 0}
        anterior = continuadas.get(indice)
        if anterior is None:
            nueva.update(canorilin=0, canoriori=fila["can"])
        else:
            nueva.update(
                canorilin=int(anterior["ide"]),
                canoriori=float(_d(anterior.get("canoriori")) + _d(fila["can"])),
            )
            if not _vinculo(fila):
                nueva["imporiori"] = anterior.get("imporiori")
        resultado.append(nueva)
    return resultado


def filas_arrastradas(
    filas_anterior: Sequence[Mapping[str, Any]], usadas: Collection[int], primera_pos: int
) -> list[dict[str, Any]]:
    """R12 (D6, D12): copia de cada linea de la anterior que nadie continua,
    con cantidad e importes a 0, `canorilin` a ella, su `canoriori` e
    `imporiori`, el seguimiento a 0 como el nucleo y la medicion vacia; `pos`
    detras de las de la peticion, en el orden de la anterior. Sin `ide` ni
    `docide`: los pone `numerar`, como a las demas."""
    arrastradas: list[dict[str, Any]] = []
    for fila in filas_anterior:
        if int(fila["ide"]) in usadas:
            continue
        copia = dict(fila)
        for columna in _SEGUIMIENTO_A_CERO:
            if columna in copia:
                copia[columna] = 0
        copia.update({
            "ide": None, "docide": None, "pos": primera_pos + len(arrastradas) * POS_PASO,
            "can": 0.0, "tot": 0.0, "ivacuo": 0.0, "prepma": 0.0, "canorilin": int(fila["ide"]),
            "canoriant": 0, "imporiant": 0, "med": None, "canmed": 0,
        })
        arrastradas.append(copia)
    return arrastradas


def cabecera_a_origen(dca: Mapping[str, Any], anterior: DocumentoCadena | None) -> dict[str, Any]:
    """R13: la `dca` de F-007 R12 con `docoritip` 1 y `docoriide` la anterior (0 en la primera)."""
    return {
        **dca,
        "docoritip": DOCORITIP_A_ORIGEN,
        "docoriide": anterior.ide if anterior is not None else 0,
    }


# --- Ya registrada (R5) y respuesta (R19) --------------------------------------------


def buscar_del_mes_origen(
    proformas: Sequence[ProformaRegistrada],
    *,
    periodo: int,
    importe_mes: float,
    otra_del_mes: bool,
) -> tuple[ProformaRegistrada | None, list[AvisoProformaOrigen]]:
    """
    R5 (D8): F-007 R24 con una diferencia. Si TODAS las del contrato y del mes
    son a origen, la del mismo total (±0,05) es la `existente` y, si ninguna lo
    es, aviso `otra_del_mes` y sigue (cadenas paralelas, M18). Con alguna de mes
    o con `otra_del_mes`, exactamente F-007.
    """
    del_mes = [p for p in proformas if p.fec // 100 == periodo]
    if otra_del_mes or any(p.docoritip != DOCORITIP_A_ORIGEN for p in del_mes):
        existente, avisos = buscar_del_mes(
            proformas, periodo=periodo, importe_mes=importe_mes, otra_del_mes=otra_del_mes
        )
        return existente, [AvisoProformaOrigen(**a.model_dump()) for a in avisos]
    for proforma in del_mes:
        if abs(_d(proforma.totbas) - _d(importe_mes)) <= TOLERANCIA_IMPORTE:
            return proforma, []
    if not del_mes:
        return None, []
    return None, [AvisoProformaOrigen(
        codigo="otra_del_mes",
        mensaje=(
            "El contrato ya tiene proforma a origen de este mes con otro importe: "
            f"{', '.join(p.cod for p in del_mes)}. Se registra en su cadena."
        ),
    )]


def importe_de_cadena(filas: Sequence[Mapping[str, Any]]) -> float:
    """R19: Σ round(`canoriori`·`pre`, 2), cada producto en `Decimal` (M25)."""
    return float(sum(
        (redondear_euros(_d(fila.get("canoriori")) * _d(fila.get("pre"))) for fila in filas),
        Decimal(0),
    ))
