# application/use_cases/factura_statements.py
"""
Constructor PURO de `sigrid/factura` (F-008): filas por lista blanca, totales,
numeracion y, en `FacturaStatements`, el SQL constante (lecturas `Lnn`,
reservas `Enn`, `INSERT`s, marcas y relecturas).

Sin E/S. Cada sentencia es `(sql, params)` con todos los valores como `?`; al
construirse, la clase valida TODAS las constantes con `DatabaseReferenceGuard`
contra la base de la peticion. Ninguna fila se clona: `con`, `dcf`, `dcfpro`,
`dcfrec`, `pag`, `consii`, `dcaprodes` y `log` van columna a columna (R38) con
las listas de T0 (`progress/impl_F-008.md`). Ninguna sentencia nombra `asi`,
`apu`, `regiva`, `regirp`, `mov`, `dcfproana`, `dcfpropar`, `dcfprodes`,
`dcfproimp` ni `confir`, ni lleva `DELETE` (R39, T15).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from application.use_cases.albaran_compra_statements import (
    _DCA_TEXTO,
    DCA_COLUMNAS,
    DCAREC_COLUMNAS,
    SellosAlbaran,
    bruto_de_linea,
    construir_dcarec,
    construir_log,
    porcentaje_de_dto,
    redondear_euros,
)
from application.use_cases.factura_lineas import DCFPRO_COLUMNAS
from application.use_cases.parte_reclamacion_statements import (
    CON_COLUMNAS,
    LOG_COLUMNAS,
)
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard

#: `con.tip` de la factura de compra, del pago y del albaran de origen.
TIP_FACTURA = 15
TIP_PAGO = 25
TIP_ALBARAN = 14
#: `dcf.cla` de toda factura de compra (M52).
CLA_FACTURA = 1001
#: `con.res` y `log.res`: 128 caracteres.
_LARGO_RES = 128
#: `dcfpro.pos` en multiplos de 64 (M56).
POS_PASO = 64

# --- Listas blancas (T0) ------------------------------------------------------

#: Lo que la cabecera hereda: del primer origen por `cod` (M57) o, sin
#: origenes, del proveedor, su `auxpag` y la obra (M61, M67). Nada mas.
DCF_HEREDABLES: frozenset[str] = frozenset({
    "entide", "entcod", "entres", "entcif", "entciftip", "entcifpai", "obride", "cenide", "almide",
    "empide", "diremp1", "dircon1", "dirdir1", "pagide", "pagtex", "pagfor", "efeide", "eioide",
    "ivadif", "cocide", "tipgar", "fecent", "feclim", "banban", "bansuc", "bandig", "bancue", "ban",
    "bantipide",
})
#: Columnas de `dca`/`dcf` que el alta deja en NULL (T0: `emptex`).
_DCF_NULAS: frozenset[str] = frozenset({"emptex"})

#: Las 46 columnas de `dbo.pag`, en su orden fisico (T0).
PAG_COLUMNAS: tuple[str, ...] = (
    "ide", "cla", "tot", "efeide", "fecven", "conide", "entide", "cueide", "banide", "remide",
    "banban", "bansuc", "bandig", "bancue", "ban", "bantipide", "cypref", "entref", "padide",
    "fecrea", "blofec", "blores", "bloide", "crecedide", "ceside", "natide", "pun", "cenide",
    "fecreaemi", "divcod", "divcam", "divtot", "cetide", "prpide", "retide", "divcamfec",
    "entretide", "cpapai", "cpaban", "cpasuc", "cpaswi", "cpatip", "cpadiv", "cpacue1", "cpacue2",
    "retref",
)
_PAG_TEXTO: frozenset[str] = frozenset({
    "bandig", "bancue", "ban", "cypref", "entref", "blores", "divcod", "cpapai", "cpaban", "cpasuc",
    "cpaswi", "cpatip", "cpadiv", "cpacue1", "cpacue2", "retref",
})
#: Lo que la `pag` toma de la `dcf` (M58).
PAG_DE_LA_DCF: tuple[str, ...] = (
    "efeide", "entide", "cenide", "entref", "banide", "banban", "bansuc", "bandig", "bancue", "ban",
    "bantipide",
)

#: Las 50 columnas de `dbo.consii`, en su orden fisico (T0).
CONSII_COLUMNAS: tuple[str, ...] = (
    "ide", "conide", "pos", "tipcom", "tipdoc", "tiprec", "ultcod", "fecope", "pereje", "perper",
    "claope", "claop1", "claop2", "desope", "emiter", "inttipope", "intcladec", "intestmie",
    "intplaope", "intdesbie", "intdirope", "intfacdoc", "detinm", "usu", "fecrec", "horrec",
    "estenv", "csv", "estreg", "coderr", "txterr", "est", "nocen", "regivaide", "imptra",
    "numacufac", "entsucraz", "entsucnif", "facsimcua", "facsinide", "difplaenv", "agetri",
    "perpos", "poseje", "posper", "cuaiem", "impespcla", "exent", "regsusp", "cuiiee",
)
_CONSII_TEXTO: frozenset[str] = frozenset({
    "tipcom", "tipdoc", "tiprec", "ultcod", "perper", "claope", "claop1", "claop2", "desope",
    "emiter", "inttipope", "intcladec", "intestmie", "intdesbie", "intdirope", "intfacdoc", "usu",
    "estenv", "csv", "estreg", "coderr", "txterr", "numacufac", "entsucraz", "entsucnif",
    "facsimcua", "facsinide", "difplaenv", "perpos", "posper", "impespcla", "exent", "regsusp",
})
#: R38 (M58, M73): los valores del alta, en las dos series.
CONSII_FIJAS: dict[str, Any] = {
    "pos": POS_PASO, "tipcom": "A0", "tipdoc": "F1", "claope": "01", "emiter": "N",
    "facsimcua": "N", "facsinide": "N", "difplaenv": "N", "regivaide": 0, "detinm": None,
}

#: Las 7 columnas de `dbo.dcaprodes` (T0).
DCAPRODES_COLUMNAS: tuple[str, ...] = (
    "ide", "docproide", "can", "docdestip", "docdescod", "docdeside", "lindeside",
)


#: `varchar` de `con` (su vacio es `''`).
_CON_TEXTO: frozenset[str] = frozenset({"cod", "res", "ico", "delo", "del", "obr", "doc"})


def _vacio(columna: str, texto: frozenset[str]) -> Any:
    return "" if columna in texto else 0


# --- Constructores (T8) -------------------------------------------------------


def _res(entres: str | None, entref: str) -> str:
    return f"{entres or ''}. ({entref})".strip()[:_LARGO_RES]


def construir_con_factura(
    *, emp: int, fec: int, entres: str | None, entref: str, est: int, tiemod: float
) -> dict[str, Any]:
    """`con` de la factura: `CON_COLUMNAS`, `tip` 15, `res` = «<entres>. (<entref>)»
    recortado, `fec` del alta, `est` REC o RECGG (R9) y lo demas vacio (M18)."""
    fila: dict[str, Any] = {columna: _vacio(columna, _CON_TEXTO) for columna in CON_COLUMNAS}
    fila.update(ide=None, emp=emp, tip=TIP_FACTURA, cod=None, res=_res(entres, entref), fec=fec,
                tex=None, est=est, tiemod=tiemod)
    return fila


def construir_con_pago(
    *, emp: int, fec: int, res: str, indice: int, de: int, tiemod: float
) -> dict[str, Any]:
    """`con` 25 de un vencimiento (M58): «Pago i de n <res>», `est` 1 PDT. El
    `cod` `<cod>_NN` lo pone `numerar`."""
    fila: dict[str, Any] = {columna: _vacio(columna, _CON_TEXTO) for columna in CON_COLUMNAS}
    fila.update(ide=None, emp=emp, tip=TIP_PAGO, cod=None,
                res=f"Pago {indice} de {de} {res}"[:_LARGO_RES], fec=fec, tex=None, est=1,
                tiemod=tiemod)
    return fila


def construir_dcf(
    *,
    heredadas: Mapping[str, Any],
    cueide: int,
    ctride: int,
    fecdoc: int,
    hor: int,
    entref: str,
    synckey: str,
    totales: Mapping[str, float],
) -> dict[str, Any]:
    """`dcf` por lista blanca (R38, design §6): `DCA_COLUMNAS` (T0: las mismas),
    con lo heredado (`DCF_HEREDABLES`), `cla` 1001, `cueide` = `prv.cueide`,
    `synckey`, `hor` del sello, `entref` y `fecdoc` de la factura, el contrato
    de los origenes y los totales de R29; `estfac`, `estser`, `estped`,
    `docoritip`, `docoriide`, `facoriide`, `fecpag` 0 y lo no citado, vacio
    (`tipgar` -1 sin heredar, como el alta a mano)."""
    ajenas = set(heredadas) - DCF_HEREDABLES
    if ajenas:
        raise ValueError(f"La cabecera no hereda {sorted(ajenas)}.")
    fila: dict[str, Any] = {
        columna: None if columna in _DCF_NULAS else _vacio(columna, _DCA_TEXTO)
        for columna in DCA_COLUMNAS
    }
    fila["tipgar"] = -1
    fila.update(heredadas)
    fila.update(
        ide=None, cla=CLA_FACTURA, cueide=cueide, ctride=ctride, fecdoc=fecdoc, hor=hor,
        entref=entref, synckey=synckey,
        **{c: totales[c] for c in ("impbru", "impnet", "totbas", "totiva", "totdoc", "tot", "totpag")},
    )
    return fila


def totales_factura(lineas: Sequence[Mapping[str, Any]], *, cuo: Decimal) -> dict[str, float]:
    """R29 en `Decimal`: `totbas` = Σ `tot`, `impnet` = `totbas`, `impbru` = Σ
    bruto (`can`·`tar` en las de `dto`, `tot` en las demas, F-018), `totiva` =
    Σ `ivacuo`, `totdoc` = `totbas` + `totiva`, `tot` = `totdoc` - retencion y
    `totpag` = `tot`."""
    def d(valor: Any) -> Decimal:
        return Decimal(repr(float(valor or 0)))

    totbas = sum((d(f["tot"]) for f in lineas), Decimal(0))
    totiva = sum((d(f["ivacuo"]) for f in lineas), Decimal(0))
    impbru = sum(
        (
            bruto_de_linea(float(f["can"] or 0), float(f["tar"] or 0))
            if (porcentaje_de_dto(f["dto"]) or 0) > 0 else d(f["tot"])
            for f in lineas
        ),
        Decimal(0),
    )
    totdoc = totbas + totiva
    tot = totdoc - cuo
    return {"totbas": float(totbas), "impnet": float(totbas), "impbru": float(impbru),
            "totiva": float(totiva), "totdoc": float(totdoc), "tot": float(tot),
            "totpag": float(tot), "retencion": float(cuo)}


def construir_dcfrec(dcarec: Mapping[str, Any], *, totbas: Decimal) -> dict[str, Any]:
    """R31: la retencion del origen copiada a la factura (como F-015 desde el
    `ctrrec`): su `recide`, `valpor`, `reccla`, `cueide`..., `bas` = `totbas` y
    `cuo` = round(`bas`·`valpor`, 2)."""
    bas = redondear_euros(totbas)
    cuo = redondear_euros(bas * Decimal(repr(float(dcarec["valpor"]))))
    return construir_dcarec(dcarec, bas=bas, cuo=cuo)


def construir_pag(
    *, cla: int, tot: float, fecven: int, dcf: Mapping[str, Any], cueide: int, retide: int = 0
) -> dict[str, Any]:
    """`pag` (M58): `cla` 0 por vencimiento o 2 de la retencion (`retide` =
    `recide`); `efeide`, `entide`, `cenide`, `entref` y banco de la `dcf`; sin
    remesa ni `fecrea` (R39). `ide` y `conide`, al numerar."""
    fila: dict[str, Any] = {columna: _vacio(columna, _PAG_TEXTO) for columna in PAG_COLUMNAS}
    fila.update({columna: dcf[columna] for columna in PAG_DE_LA_DCF})
    fila.update(ide=None, conide=None, cla=cla, tot=tot, fecven=fecven, cueide=cueide, retide=retide)
    return fila


def construir_consii(*, desope: str) -> dict[str, Any]:
    """`consii` (R38, M58): los valores medidos y `desope` = `con.res`."""
    fila: dict[str, Any] = {columna: _vacio(columna, _CONSII_TEXTO) for columna in CONSII_COLUMNAS}
    fila.update(CONSII_FIJAS)
    fila.update(ide=None, conide=None, desope=desope)
    return fila


def construir_dcaprodes(*, docproide: int, can: float) -> dict[str, Any]:
    """`dcaprodes` de una linea de origen (M54): `docdestip` 15 y la cantidad;
    el destino (factura, su `cod` y la linea), al numerar."""
    return {"ide": None, "docproide": docproide, "can": can, "docdestip": TIP_FACTURA,
            "docdescod": None, "docdeside": None, "lindeside": None}


def construir_log_factura(*, emp: int, usu: str, res: str, sellos: SellosAlbaran) -> dict[str, Any]:
    """La fila de alta de `log` de F-006 con `tip` 15 (T0: `ope 1`, `tab con`, `est 1`)."""
    return {**construir_log(emp=emp, usu=usu, res=res, sellos=sellos), "tip": TIP_FACTURA}


# --- Filas de una factura y su numeracion -----------------------------------------


@dataclass(frozen=True)
class FilasFactura:
    """Las filas de UNA factura. `pagos` son (`con` 25, `pag`) con los de `cla`
    0 primero; `dcaprodes`, (i, fila) con `i` el indice de su `dcfpro`."""

    con: dict[str, Any]
    dcf: dict[str, Any]
    dcfpro: list[dict[str, Any]]
    dcfrec: list[dict[str, Any]]
    pagos: list[tuple[dict[str, Any], dict[str, Any]]]
    consii: dict[str, Any]
    dcaprodes: list[tuple[int, dict[str, Any]]]
    log: dict[str, Any]

    def como_dict(self) -> dict[str, Any]:
        """`filas` de la respuesta (R44)."""
        return {
            "con": self.con, "dcf": self.dcf, "dcfpro": self.dcfpro, "dcfrec": self.dcfrec,
            "con_pag": [con for con, _p in self.pagos], "pag": [pag for _c, pag in self.pagos],
            "consii": self.consii, "dcaprodes": [fila for _i, fila in self.dcaprodes],
            "log": self.log,
        }


def numerar(
    filas: FilasFactura,
    *,
    cod: str,
    ide_con: int,
    ide_dcfpro: int,
    ide_dcfrec: int | None,
    ide_consii: int,
    ide_dcaprodes: int | None,
    ide_log: int | None,
) -> FilasFactura:
    """Copia con `cod`, `ide` consecutivos y enlaces (R37). Los `con` de los
    pagos van tras el de la factura y la `pag` comparte `ide` con su `con`;
    `pos` en multiplos de 64. No toca `filas`: cada reintento numera limpio."""
    if filas.dcfrec and ide_dcfrec is None:
        raise ValueError("Hay dcfrec y no se ha reservado ide_dcfrec.")
    if filas.dcaprodes and ide_dcaprodes is None:
        raise ValueError("Hay dcaprodes y no se ha reservado ide_dcaprodes.")
    ides_dcfpro = [ide_dcfpro + i for i in range(len(filas.dcfpro))]
    pagos = []
    for k, (con, pag) in enumerate(filas.pagos, start=1):
        ide = ide_con + k
        pagos.append(({**con, "ide": ide, "cod": f"{cod}_{k:02d}"}, {**pag, "ide": ide, "conide": ide_con}))
    return FilasFactura(
        con={**filas.con, "ide": ide_con, "cod": cod},
        dcf={**filas.dcf, "ide": ide_con},
        dcfpro=[
            {"ide": ides_dcfpro[i], "docide": ide_con, "pos": (i + 1) * POS_PASO, **fila}
            for i, fila in enumerate(filas.dcfpro)
        ],
        dcfrec=[{**fila, "ide": ide_dcfrec, "docide": ide_con} for fila in filas.dcfrec],
        pagos=pagos,
        consii={**filas.consii, "ide": ide_consii, "conide": ide_con},
        dcaprodes=[
            (i, {**fila, "ide": ide_dcaprodes + j, "docdescod": cod, "docdeside": ide_con,
                 "lindeside": ides_dcfpro[i]})
            for j, (i, fila) in enumerate(filas.dcaprodes)
        ],
        log={**filas.log, "ide": ide_log, "cod": cod},
    )


# =====================================================================================
# SQL constante (T9, T10). `{marcadores}` es la lista `(?, ?, ...)` de un `IN`.
# =====================================================================================

#: Applocks de la transaccion, SIEMPRE en este orden (design §7): `_con` antes y
#: `_log` al final, como F-006 y F-009; los demas, propios de la factura.
APPLOCKS_FACTURA: tuple[str, ...] = (
    "SIGRID_REFEXT_15",
    "SIGRID_SERIE_15",
    "SIGRID_IDE_con",
    "SIGRID_IDE_dcfpro",
    "SIGRID_IDE_dcaprodes",
    "SIGRID_IDE_dcfrec",
    "SIGRID_IDE_pag",
    "SIGRID_IDE_consii",
    "SIGRID_IDE_log",
)

#: `con.tip` de lo que se lee: asiento, cuenta, analitica, IVA y obra.
TIP_ASIENTO = 20
TIP_CUENTA = 17
TIP_ANALITICA = 19
TIP_IVA = 23
TIP_OBRA = 42

#: R9: prefijo y cifras de cada serie (M52, M64).
SERIES_FACTURA: dict[str, tuple[str, int]] = {"FR": ("FR", 5), "FRGG": ("FRGG", 4)}

#: Lo que se lee de la `dca` del primer origen para heredarlo (M57), en orden fijo.
CABECERA_DE_ORIGEN: tuple[str, ...] = (
    "entide", "entcod", "entres", "entcif", "entciftip", "entcifpai", "obride", "cenide", "almide",
    "empide", "diremp1", "dircon1", "dirdir1", "pagide", "pagtex", "pagfor", "efeide", "eioide",
    "ivadif", "cocide", "tipgar", "fecent", "feclim", "banban", "bansuc", "bandig", "bancue", "ban",
    "bantipide",
)
#: Columnas de una linea de origen (R15, R17, R20; `docoritip` 44 = vinculada a un
#: `ctrpro`, R42), en el orden de LF8.
LINEA_DE_ORIGEN: tuple[str, ...] = (
    "ide", "docide", "pos", "proide", "can", "pre", "tar", "dto", "tot", "ivaide", "ivacuo", "cenide",
    "caaide", "paride", "natide", "almide", "obride", "res", "tex", "cod2", "unimed", "prepma",
    "dncide", "dncproide", "canfac", "linoriide", "canorilin", "canoriori", "imporiori",
    "docoritip",
)
#: Columnas de una retencion de origen (R31), en el orden de LF11.
RETENCION_DE_ORIGEN: tuple[str, ...] = (
    "docide", "recide", "pos", "valdef", "valpor", "valcan", "valmod", "valfij", "reccla", "cueide",
    "ivaide", "tex", "resalt", "item",
)
#: Columnas del proveedor (R10, R12), en el orden de LF2.
PROVEEDOR: tuple[str, ...] = (
    "ide", "cod", "raz", "cif", "tipcif", "cifpai", "cueide", "cuepdtide", "pagide", "efeide",
    "eioide", "banban", "bansuc", "bandig", "bancue", "ban", "bantipide",
)
#: Columnas de un origen (R13, R14, R18), en el orden de LF5.
ORIGEN: tuple[str, ...] = ("ide", "cod", "emp", "est", "entide", "obride", "ctride", "docoritip")

_LF_ORIGEN_COLUMNAS = "c.ide, c.cod, c.emp, c.est, d.entide, d.obride, d.ctride, d.docoritip"
_LF_LINEA_COLUMNAS = ", ".join(f"p.{columna}" for columna in LINEA_DE_ORIGEN)

LF1_ESTADOS = "SELECT tip, est, cod FROM dbo.conest WHERE tip IN (?, ?, ?)"
LF2_PROVEEDOR = (
    "SELECT v.ide, c.cod, v.raz, v.cif, v.tipcif, v.cifpai, v.cueide, v.cuepdtide, v.pagide, "
    "v.efeide, v.eioide, v.banban, v.bansuc, v.bandig, v.bancue, v.ban, v.bantipide "
    "FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide WHERE v.ide = ?"
)
LF3_AUXPAG = "SELECT res, formul FROM dbo.auxpag WHERE ide = ?"
LF4_OBRAS = (
    "SELECT c.ide, c.cod, o.cenide FROM dbo.con c JOIN dbo.obr o ON o.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND c.cod IN {marcadores}"
)
LF5_ORIGENES = (
    f"SELECT {_LF_ORIGEN_COLUMNAS} "
    "FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = ? AND c.cod IN {marcadores}"
)
LF6_CABECERA_DE_ORIGEN = f"SELECT {', '.join(CABECERA_DE_ORIGEN)} FROM dbo.dca WHERE ide = ?"
LF7_ASIENTOS = "SELECT cod FROM dbo.con WHERE tip = ? AND emp = ? AND cod IN {marcadores}"
LF8_LINEAS_DE_ORIGENES = (
    f"SELECT {_LF_LINEA_COLUMNAS} FROM dbo.dcapro p WHERE p.docide IN {{marcadores}} "
    "ORDER BY p.docide, p.pos, p.ide"
)
LF9_FACTURADAS = (
    "SELECT d.docproide FROM dbo.dcaprodes d JOIN dbo.dcapro p ON p.ide = d.docproide "
    "WHERE p.docide IN {marcadores} AND d.docdestip = ?"
)
LF10_ANTERIORES = "SELECT ide, canoriori, imporiori FROM dbo.dcapro WHERE ide IN {marcadores}"
LF11_RETENCIONES = (
    "SELECT r.docide, r.recide, r.pos, r.valdef, r.valpor, r.valcan, r.valmod, r.valfij, "
    "r.reccla, r.cueide, r.ivaide, r.tex, r.resalt, r.item FROM dbo.dcarec r "
    "WHERE r.docide IN {marcadores} ORDER BY r.docide, r.pos, r.ide"
)
LF12_IVAS = (
    "SELECT c.ide, c.cod, i.iva FROM dbo.con c JOIN dbo.iva i ON i.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND c.cod IN {marcadores}"
)
LF13_CUENTAS_GASTO = (
    "SELECT c.ide, c.cod, a.niv FROM dbo.con c JOIN dbo.cua a ON a.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND c.cod IN {marcadores}"
)
LF14_ANALITICAS_GASTO = (
    "SELECT c.ide, c.cod, CASE WHEN EXISTS (SELECT 1 FROM dbo.caa h WHERE h.padide = c.ide) "
    "THEN 0 ELSE 1 END FROM dbo.con c JOIN dbo.caa a ON a.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND c.cod IN {marcadores}"
)
LF15_REFERENCIA = (
    "SELECT c.ide, c.cod, d.entide, d.entref, d.totbas, d.totiva, d.totdoc, d.tot, c.est "
    "FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?"
)
LF16_DUPLICADAS = (
    "SELECT c.ide, c.cod FROM dbo.dcf d JOIN dbo.con c ON c.ide = d.ide "
    "WHERE c.tip = ? AND d.entcif = ? AND d.entref = ? AND c.est <> ?"
)
LF17_ULTIMO_COD = (
    "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con "
    "WHERE emp = ? AND tip = ? AND cod LIKE ? AND LEN(cod) = ?"
)

# --- Dentro de la transaccion --------------------------------------------------------

EF1_ORIGENES_BLOQUEADOS = (
    f"SELECT {_LF_ORIGEN_COLUMNAS} "
    "FROM dbo.con c WITH (UPDLOCK, HOLDLOCK) JOIN dbo.dca d WITH (UPDLOCK, HOLDLOCK) "
    "ON d.ide = c.ide WHERE c.ide IN {marcadores}"
)
EF2_LINEAS_BLOQUEADAS = (
    f"SELECT {_LF_LINEA_COLUMNAS} FROM dbo.dcapro p WITH (UPDLOCK, HOLDLOCK) "
    "WHERE p.docide IN {marcadores} ORDER BY p.docide, p.pos, p.ide"
)
EF3_COD = (
    "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) "
    "WHERE emp = ? AND tip = ? AND cod LIKE ? AND LEN(cod) = ?"
)
_EF_IDE = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.{tabla} WITH (UPDLOCK, HOLDLOCK)"
TABLAS_CON_IDE: tuple[str, ...] = ("con", "dcfpro", "dcfrec", "consii", "dcaprodes", "log")
#: R42: las `ctrpro` de las lineas vinculadas, bloqueadas antes de sumarles nada.
EF4_LINEAS_DE_CONTRATO = (
    "SELECT ide, canfac FROM dbo.ctrpro WITH (UPDLOCK, HOLDLOCK) WHERE ide IN {marcadores}"
)

#: R36, R38: cada tabla con su lista blanca, en su orden fisico (T0).
COLUMNAS_DE_ALTA: dict[str, tuple[str, ...]] = {
    "con": CON_COLUMNAS, "dcf": DCA_COLUMNAS, "dcfpro": DCFPRO_COLUMNAS, "dcfrec": DCAREC_COLUMNAS,
    "pag": PAG_COLUMNAS, "consii": CONSII_COLUMNAS, "dcaprodes": DCAPRODES_COLUMNAS,
    "log": LOG_COLUMNAS,
}
INSERTS: dict[str, str] = {
    tabla: f"INSERT INTO dbo.{tabla} ({', '.join(columnas)}) VALUES ({', '.join(['?'] * len(columnas))})"
    for tabla, columnas in COLUMNAS_DE_ALTA.items()
}

# --- Marcas en los origenes (R40-R42), siempre por `ide` y con `?` -----------------
EM1_LINEA = "UPDATE dbo.dcapro SET canfac = canfac + ? WHERE ide = ? AND canfac = ?"
EM2_CABECERA = (
    "UPDATE dbo.dca SET estfac = ?, fecfac = ?, horfac = ?, antestfac = ? WHERE ide = ? AND estfac = ?"
)
EM3_ESTADO = "UPDATE dbo.con SET est = ? WHERE ide = ? AND tip = ? AND est = ?"
EM4_CONTRATO = "UPDATE dbo.ctrpro SET canfac = canfac + ? WHERE ide = ?"
EM5_ESTFAC_CONTRATO = "UPDATE dbo.ctr SET estfac = ? WHERE ide = ?"
#: R41 (M54): `estfac` 1 y `antestfac` 3 fijos en el 100 % de los facturados.
ESTFAC_FACTURADO = 1
ANTESTFAC_FACTURADO = 3
#: R42: margen de la relectura de un `canfac` sumado (float).
TOLERANCIA_CANFAC = 0.0005

# --- Relecturas antes del COMMIT (R45) ---------------------------------------------
ER1_CON = "SELECT COUNT(*) FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?"
ER2_DCF = "SELECT COUNT(*) FROM dbo.dcf WHERE ide = ? AND synckey = ?"
ER3_DCFPRO = "SELECT COUNT(*) FROM dbo.dcfpro WHERE docide = ?"
ER4_DCFREC = "SELECT COUNT(*) FROM dbo.dcfrec WHERE docide = ?"
ER5_PAGOS = (
    "SELECT COUNT(*) FROM dbo.pag p JOIN dbo.con c ON c.ide = p.ide WHERE p.conide = ? AND c.tip = ?"
)
ER6_CONSII = "SELECT COUNT(*) FROM dbo.consii WHERE conide = ?"
ER7_DCAPRODES = "SELECT COUNT(*) FROM dbo.dcaprodes WHERE docdeside = ? AND docdestip = ?"
ER8_LOG = "SELECT COUNT(*) FROM dbo.log WHERE ide = ?"
ER9_LINEA_MARCADA = "SELECT COUNT(*) FROM dbo.dcapro WHERE ide = ? AND canfac = ?"
ER10_CABECERA_MARCADA = (
    "SELECT COUNT(*) FROM dbo.dca WHERE ide = ? AND estfac = ? AND fecfac = ? AND horfac = ? "
    "AND antestfac = ?"
)
ER11_ESTADO = "SELECT COUNT(*) FROM dbo.con WHERE ide = ? AND tip = ? AND est = ?"
ER12_LINEA_DE_CONTRATO = "SELECT COUNT(*) FROM dbo.ctrpro WHERE ide = ? AND ABS(canfac - ?) < ?"
ER13_ESTFAC_CONTRATO = "SELECT COUNT(*) FROM dbo.ctr WHERE ide = ? AND estfac = ?"


def _marcadores(n: int) -> str:
    return "(" + ", ".join(["?"] * n) + ")"


def prefijo_y_cifras(serie: str, fecha: int) -> tuple[str, int]:
    """R9: `FR<aa>/` con 5 cifras o `FRGG<aa>/` con 4, del anio de `con.fec`."""
    if serie not in SERIES_FACTURA:
        raise ValueError(f"La serie '{serie}' no es FR ni FRGG.")
    prefijo, cifras = SERIES_FACTURA[serie]
    return f"{prefijo}{(fecha // 10000) % 100:02d}/", cifras


def _parametros_de_serie(emp: int, prefijo: str, cifras: int) -> list[Any]:
    """LF17 y EF3: donde empieza el numero, la empresa, el tipo, el `LIKE` del
    prefijo (sin comodines: `FR26/%` no casa `FRGG26/...`) y el largo exacto."""
    return [len(prefijo) + 1, emp, TIP_FACTURA, prefijo + "%", len(prefijo) + cifras]


class FacturaStatements:
    """El SQL de `sigrid/factura`: cada metodo devuelve `(sql, params)`."""

    def __init__(self, *, database: str) -> None:
        self.database = database.strip()
        for sql in self.todas_las_sentencias():
            self._validar(sql)

    def _validar(self, sql: str) -> str:
        DatabaseReferenceGuard.validate(sql, allowed=[self.database], contexto="escritura")
        return sql

    def _con_lista(self, plantilla: str, valores: Sequence[Any]) -> str:
        if not valores:
            raise ValueError("Lista vacia: no hay nada que buscar con IN.")
        return self._validar(plantilla.format(marcadores=_marcadores(len(valores))))

    @staticmethod
    def todas_las_sentencias() -> tuple[str, ...]:
        """Todas las constantes, las de `IN` con un solo marcador (T15)."""
        uno = _marcadores(1)
        return (
            LF1_ESTADOS, LF2_PROVEEDOR, LF3_AUXPAG, LF4_OBRAS.format(marcadores=uno),
            LF5_ORIGENES.format(marcadores=uno), LF6_CABECERA_DE_ORIGEN,
            LF7_ASIENTOS.format(marcadores=uno), LF8_LINEAS_DE_ORIGENES.format(marcadores=uno),
            LF9_FACTURADAS.format(marcadores=uno), LF10_ANTERIORES.format(marcadores=uno),
            LF11_RETENCIONES.format(marcadores=uno), LF12_IVAS.format(marcadores=uno),
            LF13_CUENTAS_GASTO.format(marcadores=uno), LF14_ANALITICAS_GASTO.format(marcadores=uno),
            LF15_REFERENCIA, LF16_DUPLICADAS, LF17_ULTIMO_COD,
            EF1_ORIGENES_BLOQUEADOS.format(marcadores=uno),
            EF2_LINEAS_BLOQUEADAS.format(marcadores=uno), EF3_COD,
            *(_EF_IDE.format(tabla=tabla) for tabla in TABLAS_CON_IDE),
            EF4_LINEAS_DE_CONTRATO.format(marcadores=uno), *INSERTS.values(),
            EM1_LINEA, EM2_CABECERA, EM3_ESTADO, EM4_CONTRATO, EM5_ESTFAC_CONTRATO,
            ER1_CON, ER2_DCF, ER3_DCFPRO, ER4_DCFREC, ER5_PAGOS, ER6_CONSII, ER7_DCAPRODES, ER8_LOG,
            ER9_LINEA_MARCADA, ER10_CABECERA_MARCADA, ER11_ESTADO, ER12_LINEA_DE_CONTRATO,
            ER13_ESTFAC_CONTRATO,
        )

    # --- Lecturas (T9) ---------------------------------------------------------------

    def leer_estados(self) -> tuple[str, list[Any]]:
        """R9, R14, R41: los `conest` de la factura, el albaran y el pago."""
        return LF1_ESTADOS, [TIP_FACTURA, TIP_ALBARAN, TIP_PAGO]

    def leer_proveedor(self, ide: int) -> tuple[str, list[Any]]:
        return LF2_PROVEEDOR, [ide]

    def leer_auxpag(self, ide: int) -> tuple[str, list[Any]]:
        return LF3_AUXPAG, [ide]

    def leer_obras(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        """R26: las obras de la empresa con su centro (`obr.cenide`)."""
        return self._con_lista(LF4_OBRAS, codigos), [TIP_OBRA, emp, *codigos]

    def leer_origenes(self, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(LF5_ORIGENES, codigos), [TIP_ALBARAN, *codigos]

    def leer_cabecera_de_origen(self, ide: int) -> tuple[str, list[Any]]:
        return LF6_CABECERA_DE_ORIGEN, [ide]

    def leer_asientos(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        """R14: los asientos `tip 20` con el `cod` de cada origen, en su empresa."""
        return self._con_lista(LF7_ASIENTOS, codigos), [TIP_ASIENTO, emp, *codigos]

    def leer_lineas_de_origenes(self, docides: Sequence[int]) -> tuple[str, list[Any]]:
        return self._con_lista(LF8_LINEAS_DE_ORIGENES, docides), [*docides]

    def leer_facturadas(self, docides: Sequence[int]) -> tuple[str, list[Any]]:
        """R15: las lineas de los origenes con un `dcaprodes` a una factura."""
        return self._con_lista(LF9_FACTURADAS, docides), [*docides, TIP_FACTURA]

    def leer_anteriores(self, ides: Sequence[int]) -> tuple[str, list[Any]]:
        """R20: las `dcapro` de los `canorilin` de las lineas a origen."""
        return self._con_lista(LF10_ANTERIORES, ides), [*ides]

    def leer_retenciones(self, docides: Sequence[int]) -> tuple[str, list[Any]]:
        return self._con_lista(LF11_RETENCIONES, docides), [*docides]

    def leer_ivas(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(LF12_IVAS, codigos), [TIP_IVA, emp, *codigos]

    def leer_cuentas_gasto(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(LF13_CUENTAS_GASTO, codigos), [TIP_CUENTA, emp, *codigos]

    def leer_analiticas_gasto(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        """R26: la tercera columna es 1 si la analitica es hoja (ninguna `caa`
        la tiene de padre)."""
        return self._con_lista(LF14_ANALITICAS_GASTO, codigos), [TIP_ANALITICA, emp, *codigos]

    def buscar_referencia(self, referencia: str) -> tuple[str, list[Any]]:
        """R43, fuera y otra vez bajo el applock de referencias."""
        return LF15_REFERENCIA, [TIP_FACTURA, referencia]

    def buscar_duplicadas(self, cif: str, entref: str, est_rech: int) -> tuple[str, list[Any]]:
        """R43: otra factura del mismo CIF y numero fuera de RECH."""
        return LF16_DUPLICADAS, [TIP_FACTURA, cif, entref, est_rech]

    def ultimo_cod(self, emp: int, prefijo: str, cifras: int) -> tuple[str, list[Any]]:
        """El `cod` provisional de la previa: EF3 sin bloqueos."""
        return LF17_ULTIMO_COD, _parametros_de_serie(emp, prefijo, cifras)

    # --- Dentro de la transaccion ----------------------------------------------------

    def bloquear_origenes(self, ides: Sequence[int]) -> tuple[str, list[Any]]:
        """R14 otra vez, con las cabeceras de los origenes bloqueadas (design §7)."""
        return self._con_lista(EF1_ORIGENES_BLOQUEADOS, ides), [*ides]

    def bloquear_lineas_de_origenes(self, docides: Sequence[int]) -> tuple[str, list[Any]]:
        """R15 y R22 otra vez: el escritorio no toma nuestros applocks."""
        return self._con_lista(EF2_LINEAS_BLOQUEADAS, docides), [*docides]

    def reservar_cod(self, emp: int, prefijo: str, cifras: int) -> tuple[str, list[Any]]:
        return EF3_COD, _parametros_de_serie(emp, prefijo, cifras)

    def _reservar_ide(self, tabla: str) -> tuple[str, list[Any]]:
        return _EF_IDE.format(tabla=tabla), []

    def reservar_ide_con(self) -> tuple[str, list[Any]]:
        return self._reservar_ide("con")

    def reservar_ide_dcfpro(self) -> tuple[str, list[Any]]:
        return self._reservar_ide("dcfpro")

    def reservar_ide_dcfrec(self) -> tuple[str, list[Any]]:
        return self._reservar_ide("dcfrec")

    def reservar_ide_consii(self) -> tuple[str, list[Any]]:
        return self._reservar_ide("consii")

    def reservar_ide_dcaprodes(self) -> tuple[str, list[Any]]:
        return self._reservar_ide("dcaprodes")

    def reservar_ide_log(self) -> tuple[str, list[Any]]:
        return self._reservar_ide("log")

    def bloquear_lineas_de_contrato(self, ides: Sequence[int]) -> tuple[str, list[Any]]:
        return self._con_lista(EF4_LINEAS_DE_CONTRATO, ides), [*ides]

    # --- INSERTs por lista blanca (R36, R38) -----------------------------------------

    @staticmethod
    def _insertar(tabla: str, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        """Exactamente las columnas de la lista blanca: ni una mas ni una menos."""
        columnas = COLUMNAS_DE_ALTA[tabla]
        if set(fila) != set(columnas):
            raise ValueError(
                f"La fila de {tabla} no trae sus columnas: sobran {sorted(set(fila) - set(columnas))}, "
                f"faltan {sorted(set(columnas) - set(fila))}."
            )
        return INSERTS[tabla], [fila[columna] for columna in columnas]

    def insertar_con(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("con", fila)

    def insertar_dcf(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("dcf", fila)

    def insertar_dcfpro(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("dcfpro", fila)

    def insertar_dcfrec(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("dcfrec", fila)

    def insertar_pag(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("pag", fila)

    def insertar_consii(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("consii", fila)

    def insertar_dcaprodes(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("dcaprodes", fila)

    def insertar_log(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar("log", fila)

    # --- Marcas (R40-R42) ---------------------------------------------------------------

    def marcar_linea(self, ide: int, can: float) -> tuple[str, list[Any]]:
        """R40: solo si `canfac` sigue a 0; la relectura exige la fila marcada."""
        return EM1_LINEA, [can, ide, 0]

    def marcar_cabecera(self, ide: int, fecfac: int, horfac: int) -> tuple[str, list[Any]]:
        """R41: `estfac` 1, la fecha y hora de la operacion y `antestfac` 3; nunca `idefac`."""
        return EM2_CABECERA, [ESTFAC_FACTURADO, fecfac, horfac, ANTESTFAC_FACTURADO, ide, 0]

    def marcar_estado(self, ide: int, *, est_con: int, est_fac: int) -> tuple[str, list[Any]]:
        """R41: de CON a FAC, solo desde CON."""
        return EM3_ESTADO, [est_fac, ide, TIP_ALBARAN, est_con]

    def sumar_facturado_contrato(self, ide: int, can: float) -> tuple[str, list[Any]]:
        return EM4_CONTRATO, [can, ide]

    def actualizar_estfac_contrato(self, ctride: int, estfac: int) -> tuple[str, list[Any]]:
        return EM5_ESTFAC_CONTRATO, [estfac, ctride]

    # --- Relecturas (R45) ---------------------------------------------------------------

    def releer_con(self, emp: int, cod: str) -> tuple[str, list[Any]]:
        return ER1_CON, [emp, TIP_FACTURA, cod]

    def releer_dcf(self, ide: int, synckey: str) -> tuple[str, list[Any]]:
        return ER2_DCF, [ide, synckey]

    def releer_dcfpro(self, ide: int) -> tuple[str, list[Any]]:
        return ER3_DCFPRO, [ide]

    def releer_dcfrec(self, ide: int) -> tuple[str, list[Any]]:
        return ER4_DCFREC, [ide]

    def releer_pagos(self, ide: int) -> tuple[str, list[Any]]:
        return ER5_PAGOS, [ide, TIP_PAGO]

    def releer_consii(self, ide: int) -> tuple[str, list[Any]]:
        return ER6_CONSII, [ide]

    def releer_dcaprodes(self, ide: int) -> tuple[str, list[Any]]:
        return ER7_DCAPRODES, [ide, TIP_FACTURA]

    def releer_log(self, ide: int) -> tuple[str, list[Any]]:
        return ER8_LOG, [ide]

    def releer_linea_marcada(self, ide: int, can: float) -> tuple[str, list[Any]]:
        return ER9_LINEA_MARCADA, [ide, can]

    def releer_cabecera_marcada(self, ide: int, fecfac: int, horfac: int) -> tuple[str, list[Any]]:
        return ER10_CABECERA_MARCADA, [ide, ESTFAC_FACTURADO, fecfac, horfac, ANTESTFAC_FACTURADO]

    def releer_estado(self, ide: int, *, est_fac: int) -> tuple[str, list[Any]]:
        return ER11_ESTADO, [ide, TIP_ALBARAN, est_fac]

    def releer_linea_de_contrato(self, ide: int, canfac: float) -> tuple[str, list[Any]]:
        return ER12_LINEA_DE_CONTRATO, [ide, canfac, TOLERANCIA_CANFAC]

    def releer_estfac_contrato(self, ctride: int, estfac: int) -> tuple[str, list[Any]]:
        return ER13_ESTFAC_CONTRATO, [ctride, estfac]
