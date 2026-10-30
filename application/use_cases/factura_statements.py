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
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from application.use_cases.albaran_compra_statements import (
    _DCA_TEXTO,
    DCA_COLUMNAS,
    SellosAlbaran,
    bruto_de_linea,
    construir_dcarec,
    construir_log,
    porcentaje_de_dto,
    redondear_euros,
)
from application.use_cases.parte_reclamacion_statements import CON_COLUMNAS

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
