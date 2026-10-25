# application/use_cases/proforma_statements.py
"""
SQL y funciones puras de `POST /api/sigrid/proforma` (F-007).

Las sentencias LP1-LP6 (design §Sentencias nuevas) son constantes, de LECTURA,
con marcadores `?` y validadas con `DatabaseReferenceGuard` contra la base de
la peticion al construir `ProformaStatements` (R32); la lista `IN` de LP4 se
valida al generarse. Nada de `DELETE`, `MERGE`, DDL ni `UPDATE`: lo que se
escribe es lo del nucleo de F-009 (R27).

Las funciones puras resuelven el contrato (R7-R9), identifican las lineas
(R13-R16), fijan la fecha (R18), comprueban la hoja (R19), calculan lo
registrado y los avisos (R20-R22), buscan la del mes (R24) y traducen la
peticion a la del nucleo (design §Traduccion). Sin E/S.
"""
from __future__ import annotations

import calendar
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from application.use_cases.albaran_compra_statements import TIP_ALBARAN, TIP_CONTRATO
from domain.models.proforma_models import (
    ContratoResuelto,
    LineaProformaIn,
    ProformaError,
)
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard

#: Proformas: serie `PROF<aa>/` o `entref` `PROF...`, y nunca una provision `PREV`.
PATRON_PROFORMA = "PROF%"
PATRON_PREVISION = "PREV%"
#: `dcapro.docoritip` de una linea vinculada a una linea de contrato.
DOCORITIP_CONTRATO = 44

#: Tolerancia de la medicion de contrato al casar una linea (R8, R14).
TOLERANCIA_MEDICION = 0.001

# --- Lecturas (credenciales de lectura) -------------------------------------------

#: LP1 (R20-R22, R24, R28): las proformas registradas del contrato.
LP1_PROFORMAS_DEL_CONTRATO = (
    "SELECT c.ide, c.cod, c.fec, d.entref, d.totbas, d.docoritip FROM dbo.dca d JOIN dbo.con c "
    "ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND (c.cod LIKE ? OR d.entref LIKE ?) "
    "AND ISNULL(d.entref, '') NOT LIKE ?"
)
#: LP2 (R20): la cantidad anterior por linea de contrato, de las previas al periodo.
LP2_ANTERIOR_POR_LINEA = (
    "SELECT p.linoriide, SUM(p.can) FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide "
    "JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.ctride = ? AND p.docoritip = ? "
    "AND c.fec < ? AND (c.cod LIKE ? OR d.entref LIKE ?) AND ISNULL(d.entref, '') NOT LIKE ? "
    "GROUP BY p.linoriide"
)
#: LP3 (R7, R8): los contratos de la obra, con su numero de lineas.
LP3_CONTRATOS_DE_OBRA = (
    "SELECT t.ide, c.cod, c.fec, t.entcif, t.entres, (SELECT COUNT(*) FROM dbo.ctrpro p "
    "WHERE p.docide = t.ide) AS nlin FROM dbo.ctr t JOIN dbo.con c ON c.ide = t.ide "
    "WHERE c.tip = ? AND t.obride = ?"
)
#: LP4 (R8, R14, R16, R21): las lineas de los contratos candidatos.
LP4_LINEAS_DE_CONTRATOS = (
    "SELECT p.ide, p.docide, p.paride, ISNULL(pp.cod, '') AS partida, p.can, p.pre, p.tot, "
    "p.unimed, p.proide, ISNULL(pc.cod, '') AS producto FROM dbo.ctrpro p LEFT JOIN "
    "dbo.obrparpar pp ON pp.ide = p.paride LEFT JOIN dbo.con pc ON pc.ide = p.proide "
    "WHERE p.docide IN {marcadores} ORDER BY p.docide, p.pos, p.ide"
)
#: LP5 (R23): el `tip 14` con esa referencia, con su clase y su contrato.
LP5_REFERENCIA = (
    "SELECT c.ide, c.cod, d.cla, d.ctride FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide "
    "WHERE c.tip = ? AND d.synckey = ?"
)
#: LP6 (R24, solo con `existente`): las lineas de la proforma ya registrada.
LP6_LINEAS_DE_PROFORMA = (
    "SELECT p.ide, p.linoriide, ISNULL(pc.cod, '') AS producto, p.can, p.pre, p.tot "
    "FROM dbo.dcapro p LEFT JOIN dbo.con pc ON pc.ide = p.proide WHERE p.docide = ? "
    "ORDER BY p.pos, p.ide"
)


def _marcadores(n: int) -> str:
    return "(" + ", ".join(["?"] * n) + ")"


class ProformaStatements:
    """Las sentencias de F-007 con sus parametros, validadas al construirse."""

    def __init__(self, *, database: str) -> None:
        self._database = database.strip()
        for sql in self.todas_las_sentencias():
            self._validar(sql)

    def _validar(self, sql: str) -> str:
        DatabaseReferenceGuard.validate(sql, allowed=[self._database], contexto="lectura")
        return sql

    @staticmethod
    def todas_las_sentencias() -> tuple[str, ...]:
        """Todas las constantes; la de `IN`, con un solo marcador."""
        return (
            LP1_PROFORMAS_DEL_CONTRATO,
            LP2_ANTERIOR_POR_LINEA,
            LP3_CONTRATOS_DE_OBRA,
            LP4_LINEAS_DE_CONTRATOS.format(marcadores=_marcadores(1)),
            LP5_REFERENCIA,
            LP6_LINEAS_DE_PROFORMA,
        )

    def leer_proformas_del_contrato(self, ctride: int) -> tuple[str, list[Any]]:
        """LP1: fuera y, dentro de la transaccion, por el cursor del `work` (R28)."""
        return LP1_PROFORMAS_DEL_CONTRATO, [
            TIP_ALBARAN, ctride, PATRON_PROFORMA, PATRON_PROFORMA, PATRON_PREVISION,
        ]

    def leer_anterior(self, ctride: int, primer_dia: int) -> tuple[str, list[Any]]:
        return LP2_ANTERIOR_POR_LINEA, [
            TIP_ALBARAN, ctride, DOCORITIP_CONTRATO, primer_dia, PATRON_PROFORMA,
            PATRON_PROFORMA, PATRON_PREVISION,
        ]

    def leer_contratos_de_obra(self, obride: int) -> tuple[str, list[Any]]:
        return LP3_CONTRATOS_DE_OBRA, [TIP_CONTRATO, obride]

    def leer_lineas_de_contratos(self, ctrides: Sequence[int]) -> tuple[str, list[Any]]:
        if not ctrides:
            raise ValueError("Lista vacia: no hay contratos cuyas lineas leer.")
        sql = self._validar(LP4_LINEAS_DE_CONTRATOS.format(marcadores=_marcadores(len(ctrides))))
        return sql, list(ctrides)

    def buscar_referencia(self, referencia: str) -> tuple[str, list[Any]]:
        return LP5_REFERENCIA, [TIP_ALBARAN, referencia]

    def leer_lineas_de_proforma(self, con_ide: int) -> tuple[str, list[Any]]:
        return LP6_LINEAS_DE_PROFORMA, [con_ide]


# --- Filas leidas ------------------------------------------------------------------


def _texto(valor: Any) -> str:
    return str(valor or "").strip()


def _clave(valor: Any) -> str:
    """Codigos comparados como el ERP (`Modern_Spanish_CI_AS`)."""
    return _texto(valor).casefold()


def _cif(valor: Any) -> str:
    return "".join(_texto(valor).split()).upper()


@dataclass(frozen=True)
class ContratoCandidato:
    """Un contrato de la obra (LP3)."""

    ide: int
    cod: str
    fec: int
    entcif: str
    entres: str
    nlin: int

    @classmethod
    def de_fila(cls, fila: Sequence[Any]) -> ContratoCandidato:
        ide, cod, fec, entcif, entres, nlin = fila
        return cls(ide=int(ide), cod=_texto(cod), fec=int(fec or 0), entcif=_texto(entcif),
                   entres=_texto(entres), nlin=int(nlin or 0))


@dataclass(frozen=True)
class LineaContrato:
    """Una linea de contrato (LP4) con el codigo de su partida y de su producto."""

    ide: int
    docide: int
    paride: int
    partida: str
    can: float
    pre: float
    tot: float
    unimed: str
    proide: int
    producto: str

    @classmethod
    def de_fila(cls, fila: Sequence[Any]) -> LineaContrato:
        ide, docide, paride, partida, can, pre, tot, unimed, proide, producto = fila
        return cls(
            ide=int(ide), docide=int(docide), paride=int(paride or 0), partida=_texto(partida),
            can=float(can or 0), pre=float(pre or 0), tot=float(tot or 0), unimed=_texto(unimed),
            proide=int(proide or 0), producto=_texto(producto),
        )


# --- Periodo y nombre ------------------------------------------------------------


def primer_dia_de_periodo(periodo: int) -> int:
    return periodo * 100 + 1


def fin_de_periodo(periodo: int) -> int:
    anio, mes = divmod(periodo, 100)
    return periodo * 100 + calendar.monthrange(anio, mes)[1]


def normalizar_nombre(texto: str | None) -> str:
    """R8: mayusculas y solo letras y cifras («NUN, S.A.» = «NUN S.A.»)."""
    return "".join(caracter for caracter in (texto or "").upper() if caracter.isalnum())


# --- Contrato (R7-R9) ----------------------------------------------------------------


def candidatos_de_contrato(
    contratos: Sequence[ContratoCandidato],
    *,
    fin_periodo: int,
    cif: str | None,
    nombre: str | None,
) -> list[ContratoCandidato]:
    """R8: de la obra, con fecha hasta el fin del periodo, con lineas y del
    proveedor: por `cif` si viene; si no, por el nombre normalizado contenido
    en el `entres` normalizado. Un nombre que normalizado queda vacio no casa."""
    vivos = [c for c in contratos if c.fec <= fin_periodo and c.nlin > 0]
    if cif:
        return [c for c in vivos if _cif(c.entcif) == _cif(cif)]
    buscado = normalizar_nombre(nombre)
    if not buscado:
        return []
    return [c for c in vivos if buscado in normalizar_nombre(c.entres)]


def contrato_pedido(
    contratos: Sequence[ContratoCandidato], cod: str, *, cif: str | None
) -> ContratoCandidato:
    """R7: el `cod_contrato` entre los contratos de la obra, sin filtro de fecha
    ni de proveedor; con `cif`, ha de ser el suyo."""
    elegidos = [c for c in contratos if _clave(c.cod) == _clave(cod)]
    if not elegidos:
        raise ProformaError(
            f"La obra no tiene ningun contrato '{cod.strip()}'.", codigo="contrato_no_encontrado"
        )
    if len(elegidos) > 1:
        raise ProformaError(
            f"La obra tiene {len(elegidos)} contratos '{cod.strip()}'.", codigo="contrato_ambiguo"
        )
    elegido = elegidos[0]
    if cif and _cif(elegido.entcif) != _cif(cif):
        raise ProformaError(
            f"El contrato '{elegido.cod}' es de otro proveedor (otro CIF).",
            codigo="contrato_de_otro_proveedor",
        )
    return elegido


def _contiene(lineas: Sequence[LineaContrato], linea: LineaProformaIn) -> bool:
    """Una linea de contrato de la peticion esta en el contrato: por su
    `ctrpro_ide` o, sin el, por (partida, `medicion_contrato` ±0,001)."""
    if linea.ctrpro_ide is not None:
        return any(l.ide == linea.ctrpro_ide for l in lineas)
    return any(
        _clave(l.partida) == _clave(linea.partida)
        and abs(l.can - (linea.medicion_contrato or 0)) <= TOLERANCIA_MEDICION + 1e-9
        for l in lineas
    )


def resolver_contrato(
    candidatos: Sequence[ContratoCandidato],
    lineas_por_contrato: Mapping[int, Sequence[LineaContrato]],
    lineas: Sequence[LineaProformaIn],
) -> ContratoResuelto:
    """
    R8-R9 (D4, D5): con un candidato, ese (`proveedor`); con varios, el unico
    que contiene todas las lineas de contrato de la peticion (`lineas`). Si
    ninguno las contiene todas y cada una esta en exactamente un candidato,
    `hoja_de_varios_contratos` con el reparto; si alguna no esta en ninguno,
    `contrato_no_resuelto`; si no, `contrato_ambiguo`.
    """
    cods = [c.cod for c in candidatos]
    if not candidatos:
        raise ProformaError(
            "Ningun contrato de la obra y el proveedor a la fecha del periodo, con lineas.",
            codigo="contrato_no_resuelto",
        )
    if len(candidatos) == 1:
        unico = candidatos[0]
        return ContratoResuelto(cod=unico.cod, ide=unico.ide, resuelto_por="proveedor", candidatos=cods)

    de_contrato = [linea for linea in lineas if linea.de_contrato]
    contienen = {
        c.ide: [linea for linea in de_contrato if _contiene(lineas_por_contrato.get(c.ide, ()), linea)]
        for c in candidatos
    }
    completos = [c for c in candidatos if len(contienen[c.ide]) == len(de_contrato)]
    if len(completos) == 1:
        elegido = completos[0]
        return ContratoResuelto(cod=elegido.cod, ide=elegido.ide, resuelto_por="lineas", candidatos=cods)
    if not completos:
        donde = {
            linea.referencia_linea: [c for c in candidatos if linea in contienen[c.ide]]
            for linea in de_contrato
        }
        if any(not lista for lista in donde.values()):
            raise ProformaError(
                "Alguna linea de contrato no esta en ninguno de los contratos del proveedor "
                f"({', '.join(cods)}).",
                codigo="contrato_no_resuelto",
            )
        if all(len(lista) == 1 for lista in donde.values()):
            raise ProformaError(
                "Las lineas de la hoja son de varios contratos: una peticion por contrato.",
                codigo="hoja_de_varios_contratos",
                reparto={ref: lista[0].cod for ref, lista in donde.items()},
            )
        completos = list(candidatos)
    raise ProformaError(
        f"Varios contratos del proveedor casan con la hoja: {', '.join(c.cod for c in completos)}. "
        "Indica cod_contrato.",
        codigo="contrato_ambiguo",
    )
