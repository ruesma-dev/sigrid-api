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
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from application.use_cases.albaran_compra_statements import (
    TIP_ALBARAN,
    TIP_CONTRATO,
    redondear_euros,
)
from domain.models.albaran_compra_models import AlbaranCompraRequest, LineaAlbaranIn
from domain.models.proforma_models import (
    AvisoProforma,
    ContratoResuelto,
    FalloLineaProforma,
    LineaProformaIn,
    LineaProformaResultado,
    OrigenProforma,
    ProformaError,
    ProformaRequest,
)
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard

#: Proformas: serie `PROF<aa>/` o `entref` `PROF...`, y nunca una provision `PREV`.
PATRON_PROFORMA = "PROF%"
PATRON_PREVISION = "PREV%"
#: `dcapro.docoritip` de una linea vinculada a una linea de contrato.
DOCORITIP_CONTRATO = 44
#: `dca.cla` de una proforma (R12, M31).
CLA_PROFORMA = 141

#: Tolerancias (R8, R14, R19-R21, R24): medicion y cantidad, precio e importe.
TOLERANCIA_CANTIDAD = Decimal("0.001")
TOLERANCIA_PRECIO = Decimal("0.0001")
TOLERANCIA_IMPORTE = Decimal("0.05")
#: `supera_contrato_10`: el origen pasa del 110 % del contrato (D8).
MARGEN_CONTRATO = Decimal("1.10")
#: `dca.docoritip` de una proforma a origen (D13).
DOCORITIP_A_ORIGEN = 1
#: Prefijo del `entref` por defecto: `PROF<MMAA>_<obra>` (R12, M36).
PREFIJO_ENTREF = "PROF"

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


def _d(valor: Any) -> Decimal:
    """`Decimal` de lo que se ve (`repr` del float), como `redondear_euros`."""
    return valor if isinstance(valor, Decimal) else Decimal(repr(float(valor or 0)))


def _casa_medicion(can: float, medicion: float | None) -> bool:
    return abs(_d(can) - _d(medicion)) <= TOLERANCIA_CANTIDAD



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
        _clave(l.partida) == _clave(linea.partida) and _casa_medicion(l.can, linea.medicion_contrato)
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



# --- Lineas (R13-R16, R19 de linea) -------------------------------------------------


class FalloIdentificacion(Exception):
    """Una linea de contrato que no se identifica (R14), con sus candidatas."""

    def __init__(self, codigo: str, mensaje: str, candidatos: Sequence[int] = ()) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.candidatos = list(candidatos)


def identificar_linea(
    linea: LineaProformaIn, lineas_del_contrato: Sequence[LineaContrato]
) -> LineaContrato:
    """
    R14 (D6). Con `ctrpro_ide`, SOLO se comprueba que es una linea del contrato
    resuelto: ni se re-identifica ni se sustituye. Sin el (respaldo), la
    partida (codigo, obligatoria si viene) y despues, mientras queden varias y
    quedandose con las que casan si casa alguna: `medicion_contrato` (±0,001),
    `unidad` y precio (±0,0001). Varias, `linea_ambigua`; ninguna,
    `linea_no_es_del_contrato`.
    """
    if linea.ctrpro_ide is not None:
        for candidata in lineas_del_contrato:
            if candidata.ide == linea.ctrpro_ide:
                return candidata
        raise FalloIdentificacion(
            "linea_no_es_del_contrato",
            f"La linea de contrato {linea.ctrpro_ide} no es del contrato resuelto.",
        )
    quedan = list(lineas_del_contrato)
    if linea.partida is not None:
        quedan = [l for l in quedan if _clave(l.partida) == _clave(linea.partida)]
    filtros = []
    if linea.medicion_contrato is not None:
        filtros.append(lambda l: _casa_medicion(l.can, linea.medicion_contrato))
    if linea.unidad is not None:
        filtros.append(lambda l: _clave(l.unimed) == _clave(linea.unidad))
    filtros.append(lambda l: abs(_d(l.pre) - _d(linea.precio)) <= TOLERANCIA_PRECIO)
    # Sin `break` con una sola: un filtro que no la casa no la quita (T18).
    for filtro in filtros:
        casan = [l for l in quedan if filtro(l)]
        if casan:
            quedan = casan
    if not quedan:
        raise FalloIdentificacion(
            "linea_no_es_del_contrato",
            f"Ninguna linea del contrato casa con la partida '{linea.partida or ''}'.",
        )
    if len(quedan) > 1:
        raise FalloIdentificacion(
            "linea_ambigua",
            f"{len(quedan)} lineas del contrato casan con la partida, la medicion, la unidad y "
            "el precio: indica ctrpro_ide.",
            [l.ide for l in quedan],
        )
    return quedan[0]


def linea_descuadrada(linea: LineaProformaIn) -> bool:
    """R19: con anterior y origen, origen = anterior + mes (±0,001)."""
    if linea.cantidad_anterior is None or linea.cantidad_origen is None:
        return False
    esperado = _d(linea.cantidad_anterior) + _d(linea.cantidad)
    return abs(_d(linea.cantidad_origen) - esperado) > TOLERANCIA_CANTIDAD


def revisar_lineas(
    lineas: Sequence[LineaProformaIn],
    lineas_del_contrato: Sequence[LineaContrato] | None,
    *,
    sin_contrato: bool,
) -> tuple[dict[int, LineaContrato], list[FalloLineaProforma]]:
    """
    Etapa 1 de las lineas (design §Flujo 4): identifica las de contrato (R13,
    R14), exige `producto` en las demas (R16) y comprueba que cada linea cuadra
    (R19), juntando TODOS los fallos. Sin contrato (R11), todas van sin vincular
    con su `producto` y no hay comprobaciones de R19.
    """
    identificadas: dict[int, LineaContrato] = {}
    fallos: list[FalloLineaProforma] = []

    def fallo(indice: int, linea: LineaProformaIn, codigo: str, mensaje: str,
              candidatos: Sequence[int] = ()) -> None:
        fallos.append(FalloLineaProforma(
            indice=indice, referencia_linea=linea.referencia_linea, codigo=codigo,
            mensaje=mensaje, candidatos=list(candidatos),
        ))

    for indice, linea in enumerate(lineas):
        if linea.de_contrato and not sin_contrato:
            try:
                identificadas[indice] = identificar_linea(linea, lineas_del_contrato or ())
            except FalloIdentificacion as exc:
                fallo(indice, linea, exc.codigo, exc.mensaje, exc.candidatos)
        elif linea.producto is None:
            fallo(indice, linea, "producto_obligatorio",
                  "Una linea sin contrato necesita su producto: no hay producto por defecto.")
        if not sin_contrato and linea_descuadrada(linea):
            fallo(indice, linea, "linea_descuadrada",
                  "La cantidad a origen no es la anterior mas la del mes.")
    return identificadas, fallos


# --- Fecha (R18) y referencia (R12) ------------------------------------------------


def fecha_de_periodo(periodo: int, fecha_proforma: int | None, hoy: int) -> int:
    """R18 (D9): `fecha_proforma` si cae en el periodo; si no, el ultimo dia del
    periodo si ya paso u `hoy` (Madrid) en el mes en curso. Periodo futuro o
    `fecha_proforma` fuera de el: `periodo_no_valido`."""
    if periodo > hoy // 100:
        raise ProformaError(
            f"El periodo {periodo} es futuro: no se registra la proforma de un mes que no ha "
            "empezado.",
            codigo="periodo_no_valido",
        )
    if fecha_proforma is not None:
        if fecha_proforma // 100 != periodo:
            raise ProformaError(
                f"La fecha de la proforma {fecha_proforma} no cae en el periodo {periodo}.",
                codigo="periodo_no_valido",
            )
        return fecha_proforma
    return fin_de_periodo(periodo) if periodo < hoy // 100 else hoy


def entref_por_defecto(periodo: int, cod_obra: str) -> str:
    """R12 (M36): `PROF<MMAA>_<obra>`, el contrato de lectura con `facturas`."""
    anio, mes = divmod(periodo, 100)
    return f"{PREFIJO_ENTREF}{mes:02d}{anio % 100:02d}_{cod_obra}"


# --- Comprobaciones de la hoja (R19) -----------------------------------------------


def importe_de_lineas(lineas: Sequence[LineaProformaIn]) -> Decimal:
    """Σ round(cantidad·precio, 2), cada producto en `Decimal`."""
    return sum((redondear_euros(_d(l.cantidad) * _d(l.precio)) for l in lineas), Decimal(0))


def comprobar_hoja(request: ProformaRequest) -> None:
    """R19 de cabecera, aun en dry-run: la suma de las lineas es el importe del
    mes (±0,05) y, con anterior y origen, origen = anterior + mes (±0,05)."""
    suma = importe_de_lineas(request.lineas)
    if abs(suma - _d(request.importe_mes)) > TOLERANCIA_IMPORTE:
        raise ProformaError(
            f"Las lineas suman {suma:.2f} y el importe del mes es {_d(request.importe_mes):.2f}.",
            codigo="importe_mes_no_cuadra",
        )
    if request.importe_anterior is None or request.importe_origen is None:
        return
    esperado = _d(request.importe_anterior) + _d(request.importe_mes)
    if abs(_d(request.importe_origen) - esperado) > TOLERANCIA_IMPORTE:
        raise ProformaError(
            "El importe a origen de la hoja no es el anterior mas el del mes.",
            codigo="hoja_descuadrada",
        )


# --- Lo registrado en Sigrid (R20-R22) ---------------------------------------------


@dataclass(frozen=True)
class ProformaRegistrada:
    """Una proforma registrada del contrato (LP1)."""

    ide: int
    cod: str
    fec: int
    entref: str
    totbas: float
    docoritip: int

    @classmethod
    def de_fila(cls, fila: Sequence[Any]) -> ProformaRegistrada:
        ide, cod, fec, entref, totbas, docoritip = fila
        return cls(ide=int(ide), cod=_texto(cod), fec=int(fec or 0), entref=_texto(entref),
                   totbas=float(totbas or 0), docoritip=int(docoritip or 0))


def anterior_por_linea(filas: Sequence[Sequence[Any]]) -> dict[int, float]:
    """LP2: `linoriide` -> Σ `can` de las proformas previas al periodo."""
    return {int(linoriide): float(suma or 0) for linoriide, suma in filas}


def importe_de_contrato(lineas: Sequence[LineaContrato]) -> float:
    """R21 (D8): Σ `ctrpro.tot`, el «IMPORTE TOTAL» de la hoja."""
    return float(redondear_euros(sum((_d(l.tot) for l in lineas), Decimal(0))))


def _aviso(codigo: str, mensaje: str) -> AvisoProforma:
    return AvisoProforma(codigo=codigo, mensaje=mensaje)


def anterior_y_origen(
    proformas: Sequence[ProformaRegistrada],
    *,
    primer_dia: int,
    importe_mes: float,
    importe_contrato: float,
    importe_anterior: float | None,
) -> tuple[OrigenProforma, list[AvisoProforma]]:
    """
    R20-R22: el importe anterior registrado (Σ `totbas` de las previas al
    periodo), el origen (anterior + mes), el contrato y el porcentaje; y los
    avisos informativos de cabecera: `anterior_distinto_de_sigrid` (±0,05),
    `supera_contrato` (> 100 %) o `supera_contrato_10` (> 110 %) y
    `contrato_a_origen`.
    """
    previas = (_d(p.totbas) for p in proformas if p.fec < primer_dia)
    anterior = redondear_euros(sum(previas, Decimal(0)))
    mes = redondear_euros(_d(importe_mes))
    origen = anterior + mes
    contrato = redondear_euros(_d(importe_contrato))
    porcentaje = (
        float((origen * 100 / contrato).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        if contrato > 0 else None
    )
    avisos: list[AvisoProforma] = []
    if importe_anterior is not None and abs(_d(importe_anterior) - anterior) > TOLERANCIA_IMPORTE:
        avisos.append(_aviso(
            "anterior_distinto_de_sigrid",
            f"El importe anterior de la hoja ({_d(importe_anterior):.2f}) no es el registrado en "
            f"Sigrid ({anterior:.2f}).",
        ))
    if contrato > 0 and origen > contrato:
        codigo = "supera_contrato_10" if origen > contrato * MARGEN_CONTRATO else "supera_contrato"
        avisos.append(_aviso(
            codigo,
            f"El importe a origen ({origen:.2f}) supera el del contrato ({contrato:.2f}): "
            f"{porcentaje} %.",
        ))
    if any(p.docoritip == DOCORITIP_A_ORIGEN for p in proformas):
        avisos.append(_aviso(
            "contrato_a_origen",
            "El contrato ya tiene proformas a origen: esta se registra de mes.",
        ))
    return OrigenProforma(
        importe_anterior_sigrid=float(anterior), importe_mes=float(mes),
        importe_origen=float(origen), importe_contrato=float(contrato),
        porcentaje_contrato=porcentaje,
    ), avisos


def aviso_anterior_de_linea(
    linea: LineaProformaIn, anterior_sigrid: float
) -> AvisoProforma | None:
    """R20 por linea: la cantidad anterior de la hoja frente a la registrada (±0,001)."""
    if linea.cantidad_anterior is None:
        return None
    if abs(_d(linea.cantidad_anterior) - _d(anterior_sigrid)) <= TOLERANCIA_CANTIDAD:
        return None
    return _aviso(
        "anterior_distinto_de_sigrid",
        f"La cantidad anterior de la hoja ({linea.cantidad_anterior}) no es la registrada en "
        f"Sigrid ({anterior_sigrid}).",
    )


# --- Ya registrada (R23, R24) ------------------------------------------------------


def es_proforma(fila_lp5: Sequence[Any], ctride: int) -> bool:
    """R23: el `tip 14` de la referencia es una proforma (`cla 141`) del mismo contrato."""
    _ide, _cod, cla, ctride_fila = fila_lp5
    return cla == CLA_PROFORMA and int(ctride_fila or 0) == ctride


def buscar_del_mes(
    proformas: Sequence[ProformaRegistrada],
    *,
    periodo: int,
    importe_mes: float,
    otra_del_mes: bool,
) -> tuple[ProformaRegistrada | None, list[AvisoProforma]]:
    """
    R24 (D10), entre las proformas DEL CONTRATO: con `otra_del_mes`, si hay
    alguna del mes, aviso y sigue; si no, la del mes con el mismo total (±0,05)
    es la `existente` y una del mes con otro total es
    `proforma_del_mes_existente`.
    """
    del_mes = [p for p in proformas if p.fec // 100 == periodo]
    if not del_mes:
        return None, []
    cods = ", ".join(p.cod for p in del_mes)
    if otra_del_mes:
        return None, [_aviso("otra_del_mes", f"El contrato ya tiene proforma de este mes: {cods}.")]
    for proforma in del_mes:
        if abs(_d(proforma.totbas) - _d(importe_mes)) <= TOLERANCIA_IMPORTE:
            return proforma, []
    raise ProformaError(
        f"El contrato ya tiene proforma de este mes con otro importe: {cods}. Si es una segunda, "
        "otra_del_mes.",
        codigo="proforma_del_mes_existente",
    )


def lineas_del_existente(filas_lp6: Sequence[Sequence[Any]]) -> list[LineaProformaResultado]:
    """R24: las lineas de la proforma ya registrada (LP6), para enlazarla."""
    resultado = []
    for indice, (ide, linoriide, producto, can, pre, tot) in enumerate(filas_lp6):
        vinculo = int(linoriide or 0)
        resultado.append(LineaProformaResultado(
            indice=indice, referencia_linea="", dcapro_ide=int(ide), ctrpro_ide=vinculo,
            linoriide=vinculo, proide=0, producto=_texto(producto) or None,
            cantidad=float(can or 0), precio=float(pre or 0), total=float(tot or 0),
            importe=float(tot or 0), iva_cuota=0.0, almide=0, de_contrato=vinculo > 0,
        ))
    return resultado


# --- Traduccion a la peticion del nucleo (design §Traduccion) ------------------------


def traducir(
    request: ProformaRequest,
    *,
    contrato: ContratoCandidato | None,
    identificadas: Mapping[int, LineaContrato],
    fecha: int,
) -> AlbaranCompraRequest:
    """La peticion de F-009 que da de alta la proforma: las de contrato
    vinculadas con la partida de imputacion o la de su `ctrpro` (codigo y
    `paride`); las demas, sin vincular con su `producto` y su partida."""
    lineas = []
    for indice, linea in enumerate(request.lineas):
        comun: dict[str, Any] = {
            "referencia_linea": linea.referencia_linea, "descripcion": linea.descripcion,
            "unidad": linea.unidad, "cantidad": linea.cantidad, "precio": linea.precio,
        }
        ctrpro = identificadas.get(indice)
        if ctrpro is not None:
            if linea.partida_imputacion is not None:
                comun["partida"] = linea.partida_imputacion
            elif ctrpro.partida:
                comun.update(partida=ctrpro.partida, paride=ctrpro.paride or None)
            lineas.append(LineaAlbaranIn(**comun, ctrpro_ide=ctrpro.ide))
        else:
            lineas.append(LineaAlbaranIn(
                **comun, producto=linea.producto,
                partida=linea.partida_imputacion or linea.partida,
            ))
    return AlbaranCompraRequest(
        database=request.database,
        cod_obra=request.cod_obra,
        usu=request.usu,
        cif_proveedor=contrato.entcif if contrato is not None else request.cif_proveedor,
        referencia_externa=request.referencia_externa,
        cod_contrato=contrato.cod if contrato is not None else None,
        su_referencia=request.su_referencia or entref_por_defecto(request.periodo, request.cod_obra),
        fecha_albaran=fecha,
        empide=None,
        lineas=lineas,
        commit=request.commit,
    )
