# application/use_cases/albaran_compra_statements.py
"""
Constructor PURO del modo extendido de `sigrid/albaran` (F-009): sentencias,
funciones de calculo y filas.

Sin E/S: cada sentencia se devuelve como `(sql, params)` y cada fila como un
diccionario columna -> valor. El SQL es constante y todos los valores viajan
como `?` (R31); al construirse la clase valida TODAS las constantes con
`DatabaseReferenceGuard` contra la base de la peticion, y las que se generan
(listas `IN (?, ...)` y los `INSERT` de las tablas clonadas) se validan al
generarse.

Las sentencias son las de `specs/F-009-alta-albaran-compra/design.md`
§Sentencias (sin L12b, L12c ni E7b) con los cambios de F-015 (contrato con
albaranes v8.3): L5 pasa a respaldo opcional y hay sentencias nuevas, L16
(`ctrrec` del contrato), L17 (`prv` por CIF), E6b (`ide` de la `dcarec`) y
E12_DCAREC (su relectura). Solo `dcapro` se CLONA de su plantilla
(`_TABLAS_CLONADAS`, `SELECT *` como el modo clasico: sus columnas son las de
la fila, cada una validada como identificador y entre corchetes). `con` y
`dca` se construyen por lista blanca, columna a columna, con columnas fijas
(`CON_COLUMNAS`, `DCA_COLUMNAS`), igual que la `dcarec` (`DCAREC_COLUMNAS`),
`mov`, `ctrprodes` y `log` (las del clasico y las de F-006).
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from application.use_cases.concepto_grafico_statements import hora_local_de_madrid
from application.use_cases.parte_reclamacion_statements import (
    CON_COLUMNAS,
    LOG_COLUMNAS,
    fecha_ole_utc,
)
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard
from infrastructure.security.identifier_guard import IdentifierGuard

#: Tipos de concepto (`con.tip`): albaran de compra, contrato, obra y producto.
TIP_ALBARAN = 14
TIP_CONTRATO = 44
TIP_OBRA = 42
TIP_PRODUCTO = 3
TIP_PROVEEDOR = 5

#: Respaldo de la cabecera (F-015 R6, M1, M25): un `AC<aa>/` de clase 0 cuya
#: referencia no empieza por `PROF`. Nunca una proforma ni una nota de cargo.
PATRON_SERIE_RESPALDO = "AC__/%"
CLA_ALBARAN = 0
PATRON_PROFORMA = "PROF%"

#: Prefijo de la serie del albaran de compra: `AC<aa>/` del anio de la fecha.
PREFIJO_SERIE = "AC"

#: Tolerancia de precio frente al `ctrpro` (H14, M4) y centimo de euro (H33).
TOLERANCIA_PRECIO = Decimal("0.0001")
_CENTIMO = Decimal("0.01")

#: Estado inicial del albaran: `est` 1 (`PDT`), que debe estar en `dbo.conest` (R22).
EST_INICIAL = 1

#: Applocks de la transaccion, SIEMPRE en este orden (design §Applocks): los
#: cuatro del medio, como el clasico y `albaran-directo`; F-006 toma `_con` y
#: `_log` en el mismo orden, asi que no hay orden inverso posible. F-015 R21:
#: `SIGRID_IDE_dcarec` entre `_mov` y `_log`; nadie mas lo toma.
APPLOCKS: tuple[str, ...] = (
    "SIGRID_REFEXT_14",
    "SIGRID_SERIE_14",
    "SIGRID_IDE_con",
    "SIGRID_IDE_dcapro",
    "SIGRID_IDE_ctrprodes",
    "SIGRID_IDE_mov",
    "SIGRID_IDE_dcarec",
    "SIGRID_IDE_log",
)

#: Columnas EXACTAS de `mov` y `ctrprodes`, las del modo clasico (orden del
#: esquema vivo de Sigrid). Las de `log` son las de F-006 (se importan).
MOV_COLUMNAS: tuple[str, ...] = (
    "ide", "emp", "docide", "linide", "tip", "oritip", "oriide", "destip",
    "deside", "proide", "doctip", "fec", "hor", "fecdoc", "canent", "cansal",
    "pre", "prc", "prepma", "nueusa", "almide", "almcan", "almpma", "fecblo",
    "fechor",
)
CTRPRODES_COLUMNAS: tuple[str, ...] = (
    "ide", "docproide", "can", "docdestip", "docdescod", "docdeside",
    "lindeside", "ctrproactide",
)

# --- Lista blanca de la cabecera `dca` (F-015 R1-R9, design §Lista blanca) ----------

#: Las 145 columnas de `dca`, en el orden fisico del esquema vivo (F-015 M17).
#: El `INSERT` lleva estas y solo estas: una columna nueva de Sigrid no se copia
#: de ninguna fila leida (D6).
DCA_COLUMNAS: tuple[str, ...] = (
    "ide", "cla", "entide", "entcod", "entres", "entref", "entcif", "ivareq", "facper", "fecdoc",
    "fecpag", "hor", "eioide", "eiotex", "eitide", "eittra", "pagide", "pagtex", "pagfor", "efeide",
    "cueide", "impbru", "impnet", "impdes", "imprec", "totbas", "totiva", "totdoc", "tot", "totpag",
    "cenide", "caaide", "almide", "ivaide", "tex", "bul", "pes", "volum", "empide", "ageide",
    "ageimp", "obride", "ctride", "fecent", "feclim", "fecrec", "diremp1", "dircon1", "dirdir1",
    "diremp2", "dircon2", "dirdir2", "diremp3", "dircon3", "dirdir3", "estser", "estfac",
    "antestser", "antestfac", "ivadif", "docoritip", "docoriide", "comide", "pasdeside", "pasori",
    "divcod", "divcam", "emppreide", "empconide", "docrelide", "cocide", "paclis", "tipsininv",
    "prmide", "estped", "antestped", "empcif", "cveide", "alqide", "alqfec", "pexide", "divcamfec",
    "ctdide", "totbasdiv", "totivadiv", "totdocdiv", "totdiv", "totpagdiv", "cypnatide", "refarc",
    "emptex", "horlim", "pdpide", "ano", "mes", "texent", "refcom", "emnet", "eg3w", "dtumID",
    "cptide", "eleenvio", "tipisp", "delide", "banide", "banban", "bansuc", "bandig", "bancue",
    "ban", "bantipide", "entciftip", "entcifpai", "aoside", "PFID", "cadcod1", "caddir1",
    "cadcod2", "caddir2", "cadcod3", "caddir3", "cadcod4", "caddir4", "cpapai", "cpaban", "cpasuc",
    "cpaswi", "cpatip", "cpadiv", "cpacue1", "cpacue2", "ppoide", "fecfac", "horfac", "idefac",
    "clabieser", "facoriide", "duaide", "numregcon", "fas", "periodo", "tipctr", "tipgar",
    "impavr", "synckey",
)

#: Las de texto (`varchar`/`text`, M17): su vacio es `''`; el de las demas, 0.
_DCA_TEXTO: frozenset[str] = frozenset({
    "entcod", "entres", "entref", "entcif", "eiotex", "eittra", "pagtex", "pagfor", "tex",
    "diremp1", "diremp2", "diremp3", "dircon1", "dircon2", "dircon3", "dirdir1", "dirdir2",
    "dirdir3", "divcod", "paclis", "empcif", "refarc", "emptex", "texent", "refcom", "dtumID",
    "eleenvio", "bandig", "bancue", "ban", "entciftip", "entcifpai", "PFID", "cadcod1", "cadcod2",
    "cadcod3", "cadcod4", "cpapai", "cpaban", "cpasuc", "cpaswi", "cpatip", "cpadiv", "cpacue1",
    "cpacue2", "numregcon", "periodo", "synckey",
})

#: Identidad del proveedor (R4): del `ctr` con contrato; sin el, del respaldo
#: (mismo nombre) y, sin respaldo, del `prv` de L17 con ESTE nombre (`cod` es el
#: `con.cod` del proveedor, que da L17).
DCA_IDENTIDAD: dict[str, str] = {
    "entide": "ide", "entcod": "cod", "entres": "raz", "entcif": "cif",
    "entciftip": "tipcif", "entcifpai": "cifpai",
}

#: Grupos de la cascada que salen enteros de un mismo origen (R3).
GRUPO_PAGO: tuple[str, ...] = ("pagide", "pagtex", "pagfor", "efeide")
GRUPO_BANCO: tuple[str, ...] = ("banban", "bansuc", "bandig", "bancue", "ban", "bantipide")

#: Cascada contrato -> respaldo -> proveedor (R3, D2): columna de `dca` -> la del
#: `prv` que la trae (`None`: el `prv` no la tiene; `pagtex`/`pagfor` salen del
#: `auxpag` de su `pagide`, `PAGO_DEL_AUXPAG`).
DCA_CASCADA: dict[str, str | None] = {
    "pagide": "pagide", "pagtex": None, "pagfor": None, "efeide": "efeide",
    "banban": "banban", "bansuc": "bansuc", "bandig": "bandig", "bancue": "bancue",
    "ban": "ban", "bantipide": "bantipide",
    "cueide": "cueide", "eioide": "eioide", "dirdir1": "dir", "dircon1": None, "ivadif": None,
}
PAGO_DEL_AUXPAG: dict[str, str] = {"pagtex": "res", "pagfor": "formul"}

#: Efectos (`auxefp.cod`) en los que el banco es imprescindible: confirming y
#: transferencia (F-015 R5, M22, D12). Sin banco de ningun origen, aviso.
EFECTOS_CON_BANCO: frozenset[str] = frozenset({"CC", "CT", "TR"})

#: De la peticion, la obra o un calculo (R8, R13), nunca de una fila leida.
DCA_CALCULADAS: tuple[str, ...] = (
    "ide", "entref", "fecdoc", "hor", "obride", "ctride", "almide", "cenide", "empide",
    "synckey", "impbru", "impnet", "totbas", "totiva", "totdoc", "tot", "totpag", "diremp1",
)


def _valor_fijo(columna: str) -> Any:
    """R9 (M18, D7): lo que deja el alta a mano en una columna que nadie trae."""
    if columna == "tipgar":
        return -1
    if columna == "emptex":
        return None
    return "" if columna in _DCA_TEXTO else 0


#: Las demas columnas, con el valor fijo del alta a mano (R9).
DCA_FIJAS: dict[str, Any] = {
    columna: _valor_fijo(columna)
    for columna in DCA_COLUMNAS
    if columna not in DCA_IDENTIDAD and columna not in DCA_CASCADA and columna not in DCA_CALCULADAS
}

#: Columna -> origen, derivado de los cuatro grupos y en el orden de `DCA_COLUMNAS`.
ORIGEN_DCA: dict[str, str] = {
    columna: (
        "identidad" if columna in DCA_IDENTIDAD
        else "cascada" if columna in DCA_CASCADA
        else "calculada" if columna in DCA_CALCULADAS
        else "fija"
    )
    for columna in DCA_COLUMNAS
}

#: Tablas que se clonan de una plantilla y cuyo `INSERT` lleva las columnas de
#: la fila. Ninguna otra se escribe asi: desde F-015, `con` y `dca` van por lista
#: blanca con columnas fijas (D6).
_TABLAS_CLONADAS = frozenset({"dcapro"})

# --- Lecturas (con credenciales de lectura) -------------------------------------
# `{marcadores}` es la lista `(?, ?, ...)` de un `IN`; nunca lleva valores.

L1_OBRA = "SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?"
L5_RESPALDO_POR_ENTIDE = (
    "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND d.entide = ? AND c.cod LIKE ? AND d.cla = ? "
    "AND ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC"
)
L5_RESPALDO_POR_CIF = (
    "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND d.entcif = ? AND c.cod LIKE ? AND d.cla = ? "
    "AND ISNULL(d.entref, '') NOT LIKE ? ORDER BY c.ide DESC"
)
L17_PROVEEDOR_POR_CIF = (
    "SELECT v.ide, c.cod FROM dbo.prv v JOIN dbo.con c ON c.ide = v.ide "
    "WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ? AND v.cif = ?"
)
L6_PARTIDAS = (
    "SELECT ide, cod, tip, tipdes, tipvis FROM dbo.obrparpar WHERE obride = ? AND cod IN {marcadores}"
)
L7_PRODUCTOS = (
    "SELECT c.ide, c.cod, c.fecbaj, p.tipmov FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide "
    "WHERE c.emp = ? AND c.tip = ? AND c.cod IN {marcadores}"
)
L7B_TIPMOV = "SELECT ide, tipmov FROM dbo.pro WHERE ide IN {marcadores}"
L8_PLANTILLA_LINEA = "SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC"
L8B_PLANTILLA_LINEA_PROVEEDOR = (
    "SELECT TOP 1 p.* FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide "
    "WHERE p.proide = ? AND d.entide = ? ORDER BY p.ide DESC"
)
L9_TASAS_IVA = "SELECT ide, iva FROM dbo.iva WHERE ide IN {marcadores}"
L10_ALMACEN_DE_OBRA = "SELECT almide, cenide FROM dbo.obr WHERE ide = ?"
L10_ALMACENES = "SELECT ide, obride, cenide FROM dbo.alm WHERE obride = ?"
L10_ALMACENES_RESUELTOS = " OR ide IN {marcadores}"
#: F-015 R18: con el `tot` (neto de la retencion) al final.
L11_REFERENCIA = (
    "SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc, d.tot "
    "FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?"
)
L11_LINEAS = (
    "SELECT pos, proide, can, pre, tot, paride, almide, refent FROM dbo.dcapro "
    "WHERE docide = ? ORDER BY pos"
)
#: L16 (F-015 R12, R14): los recargos del contrato con la clase de su `rec` (NULL
#: si el `recide` no esta en `dbo.rec`) y el `cod` del recargo, para el aviso.
L16_RETENCIONES = (
    "SELECT r.ide, r.recide, r.pos, r.valdef, r.valpor, r.valcan, r.valmod, r.valfij, "
    "r.reccla, r.cueide, r.ivaide, r.tex, r.resalt, r.item, x.cla, c.cod FROM dbo.ctrrec r "
    "LEFT JOIN dbo.rec x ON x.ide = r.recide LEFT JOIN dbo.con c ON c.ide = r.recide "
    "WHERE r.docide = ? ORDER BY r.pos, r.ide"
)
#: Nombres de las columnas de L16, en su orden.
L16_COLUMNAS: tuple[str, ...] = (
    "ide", "recide", "pos", "valdef", "valpor", "valcan", "valmod", "valfij", "reccla",
    "cueide", "ivaide", "tex", "resalt", "item", "cla", "cod",
)
L12_BALANCE = (
    "SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? "
    "ORDER BY fechor DESC, ide DESC"
)
L13A_ESTADO = "SELECT est FROM dbo.conest WHERE tip = ? AND est = ?"
L13B_USUARIO = "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?"
L14_ULTIMO_COD = (
    "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con "
    "WHERE emp = ? AND tip = ? AND cod LIKE ?"
)
L15A_NATURALEZAS = (
    "SELECT ide, cod, numemp, fecbaj, caagascod, cuacomcod FROM dbo.auxpronat "
    "WHERE cod IN {marcadores}"
)
L15B_ANALITICAS = (
    "SELECT c.ide, c.cod, a.cenide FROM dbo.con c JOIN dbo.caa a ON a.ide = c.ide "
    "WHERE c.cod IN {marcadores}"
)
L15C_CUENTAS = (
    "SELECT c.ide, c.cod FROM dbo.con c JOIN dbo.cua a ON a.ide = c.ide "
    "WHERE c.emp = ? AND c.cod IN {marcadores}"
)

# --- Dentro de la transaccion (E1 = L11) ---------------------------------------------

E2_COD = (
    "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) "
    "WHERE emp = ? AND tip = ? AND cod LIKE ?"
)
E3_IDE_CON = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.con WITH (UPDLOCK, HOLDLOCK)"
E4_IDE_DCAPRO = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcapro WITH (UPDLOCK, HOLDLOCK)"
E5_IDE_CTRPRODES = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.ctrprodes WITH (UPDLOCK, HOLDLOCK)"
E6_IDE_MOV = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.mov WITH (UPDLOCK, HOLDLOCK)"
#: F-015 R21: el `ide` de la `dcarec`, solo si el albaran la lleva.
E6B_IDE_DCAREC = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcarec WITH (UPDLOCK, HOLDLOCK)"
E7_BALANCE = (
    "SELECT TOP 1 almcan, almpma FROM dbo.mov WITH (UPDLOCK, HOLDLOCK) "
    "WHERE proide = ? AND almide = ? ORDER BY fechor DESC, ide DESC"
)
E9_SERVIDO = "UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?"
E10_SUMAS_CONTRATO = "SELECT SUM(can), SUM(canser), SUM(canfac) FROM dbo.ctrpro WHERE docide = ?"
E11_ESTADOS_CONTRATO = "UPDATE dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?"
E11B_IDE_LOG = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.log WITH (UPDLOCK, HOLDLOCK)"
E12_CON = "SELECT COUNT(*) FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?"
E12_DCA = "SELECT COUNT(*) FROM dbo.dca WHERE ide = ?"
E12_DCAPRO = "SELECT COUNT(*) FROM dbo.dcapro WHERE docide = ?"
E12_CTRPRODES = "SELECT COUNT(*) FROM dbo.ctrprodes WHERE docdeside = ? AND docdestip = ?"
E12_MOV = "SELECT COUNT(*) FROM dbo.mov WHERE docide = ? AND doctip = ?"
E12_LOG = "SELECT COUNT(*) FROM dbo.log WHERE ide = ?"
#: F-015 R23: las `dcarec` del albaran (0 o 1).
E12_DCAREC = "SELECT COUNT(*) FROM dbo.dcarec WHERE docide = ?"


def _marcadores(n: int) -> str:
    return "(" + ", ".join(["?"] * n) + ")"


def _insert_fijo(tabla: str, columnas: tuple[str, ...]) -> str:
    return (
        f"INSERT INTO dbo.{tabla} ({', '.join(columnas)}) "
        f"VALUES ({', '.join(['?'] * len(columnas))})"
    )


def _parametros_de_serie(emp: int, prefijo: str) -> list[Any]:
    """Parametros de L14 y E2: donde empieza el numero tras el prefijo, la
    empresa, el tipo y el `LIKE` del prefijo (`AC<aa>/` no lleva comodines)."""
    return [len(prefijo) + 1, emp, TIP_ALBARAN, prefijo + "%"]


# =====================================================================================
# Funciones puras (T5)
# =====================================================================================


def prefijo_de_serie(fecha: int, prefijo: str = PREFIJO_SERIE) -> str:
    """`AC<aa>/` del anio de `fecha` (AAAAMMDD, la del albaran; R22). F-007
    (costura 2): otra serie del `tip 14` con su `prefijo` (`PROF`)."""
    return f"{prefijo}{(fecha // 10000) % 100:02d}/"


def siguiente_cod(prefijo: str, maximo: int | None, *, cifras: int = 0) -> str:
    """El siguiente `cod` de la serie a partir del MAX numerico de E2/L14
    (`None` si no hay ninguno). Sin ceros a la izquierda, como el clasico; con
    `cifras` (F-007: la serie `PROF` va a 5, M1), relleno con ceros hasta ellas."""
    return f"{prefijo}{str((maximo or 0) + 1).zfill(cifras)}"


def _decimal(valor: float | Decimal) -> Decimal:
    """`Decimal` de lo que se ve: `repr` del float, no su binario (2,675 es
    2,675 y no 2,67499999...)."""
    return valor if isinstance(valor, Decimal) else Decimal(repr(valor))


def redondear_euros(valor: float | Decimal) -> Decimal:
    """A 2 decimales con `ROUND_HALF_UP` (H33): 2,675 -> 2,68."""
    return _decimal(valor).quantize(_CENTIMO, rounding=ROUND_HALF_UP)


def importe_linea(cantidad: float, precio: float, iva: float) -> tuple[Decimal, Decimal]:
    """R17: `tot` = cantidad·precio y `ivacuo` = tot·iva, cada uno redondeado
    a 2 decimales; `iva` es la fraccion de `dbo.iva` (M11). El producto se hace
    en `Decimal`, sin pasar por el binario."""
    tot = redondear_euros(_decimal(cantidad) * _decimal(precio))
    return tot, redondear_euros(tot * _decimal(iva))


def sumar_importes(importes: Sequence[tuple[Decimal, Decimal]]) -> dict[str, float]:
    """Totales de la cabecera (`totbas`, `totiva`, `totdoc`) a partir de los
    `(tot, ivacuo)` de las lineas, sumados en `Decimal`."""
    totbas = sum((tot for tot, _ in importes), Decimal(0))
    totiva = sum((ivacuo for _, ivacuo in importes), Decimal(0))
    return {"totbas": float(totbas), "totiva": float(totiva), "totdoc": float(totbas + totiva)}


def precio_coincide(precio: float, pre_contrato: float) -> bool:
    """H14: el precio pedido es el del `ctrpro` si difiere <= 0,0001 (M4)."""
    return abs(_decimal(precio) - _decimal(pre_contrato)) <= TOLERANCIA_PRECIO


def usa_precio_del_contrato(cantidad: float, precio: float, pre_contrato: float) -> bool:
    """
    R17 con la decision del humano (opcion C, `progress/review_F-009_loteB_2.md`):
    una vinculada toma `pre`, `tar` y `dto` del `ctrpro` solo si el precio
    coincide (H14, <= 0,0001) Y el importe redondeado no cambia:
    `round(cantidad·precio, 2) == round(cantidad·pre_contrato, 2)` (H33). Si
    no, va por `precio_distinto_del_contrato` (`pre` = `tar` = `precio`). La
    misma funcion decide la fila (T6) y el aviso (caso de uso).
    """
    if not precio_coincide(precio, pre_contrato):
        return False
    cantidad_d = _decimal(cantidad)
    return redondear_euros(cantidad_d * _decimal(precio)) == redondear_euros(
        cantidad_d * _decimal(pre_contrato)
    )


#: Por debajo de esto, `stock + can` es 0 (R19). 1e-6 queda muy por debajo de
#: cualquier cantidad real de Sigrid (se manejan con 2-3 decimales) y muy por
#: encima del residuo binario de sumar cantidades decimales (~1e-16 a 1e-12).
EPSILON_STOCK = 1e-6


# --- Retencion del contrato (F-015 O2, R12-R16) -------------------------------------

#: Clase del `rec` -> total de la cabecera que es la base de la retencion (M12):
#: retencion (5) e IRPF (3) sobre la base; la de clase 4, sobre el total.
CLASES_RETENCION_BASE: dict[int, str] = {5: "totbas", 3: "totbas", 4: "totdoc"}


class RetencionNoSoportada(ValueError):
    """R14: el recargo del contrato no se sabe calcular; el motivo, en el texto."""


def resolver_retencion(filas_ctrrec: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """
    R12, R14 (M11): el UNICO `ctrrec` del contrato, si se sabe calcular, o
    `None` sin ninguno. Mas de uno, uno sin recargo (`recide` 0) o con un
    `recide` que no esta en `dbo.rec`, de una clase fuera de
    `CLASES_RETENCION_BASE`, con `valfij`, con `ivaide` o sin porcentaje (`valpor`
    NULL, que R15 no sabe multiplicar) -> `RetencionNoSoportada`.
    """
    if not filas_ctrrec:
        return None
    if len(filas_ctrrec) > 1:
        raise RetencionNoSoportada(f"El contrato tiene {len(filas_ctrrec)} recargos.")
    fila = filas_ctrrec[0]
    if not fila["recide"]:
        raise RetencionNoSoportada("El recargo del contrato esta vacio (sin recargo).")
    if fila["cla"] is None:
        raise RetencionNoSoportada(f"El recargo {fila['recide']} no esta en dbo.rec.")
    if int(fila["cla"]) not in CLASES_RETENCION_BASE:
        raise RetencionNoSoportada(f"El recargo {fila['cod']} es de clase {fila['cla']}.")
    if fila["valfij"]:
        raise RetencionNoSoportada(f"El recargo {fila['cod']} lleva valfij {fila['valfij']}.")
    if fila["ivaide"]:
        raise RetencionNoSoportada(f"El recargo {fila['cod']} lleva ivaide {fila['ivaide']}.")
    if fila["valpor"] is None:
        raise RetencionNoSoportada(f"El recargo {fila['cod']} no lleva valpor (sin porcentaje).")
    return fila


#: Las 21 columnas de `dbo.dcarec`, en su orden fisico (M14).
DCAREC_COLUMNAS: tuple[str, ...] = (
    "ide", "docide", "recide", "pos", "bas", "valdef", "valpor", "valcan", "valmod", "valfij",
    "cuo", "tex", "reccla", "cueide", "ivaide", "ivacuo", "reqcuo", "refide", "resalt",
    "frasupide", "item",
)

#: Lo que la `dcarec` copia del `ctrrec` (M11).
_DCAREC_DEL_CTRREC: tuple[str, ...] = (
    "recide", "pos", "valdef", "valpor", "valcan", "valmod", "valfij", "reccla", "cueide",
    "ivaide", "tex", "resalt", "item",
)


def calcular_retencion(
    ctrrec: Mapping[str, Any], totales: Mapping[str, float]
) -> tuple[Decimal, Decimal]:
    """R15 (M12): `bas` = `totbas` (clases 5 y 3) o `totdoc` (clase 4) y `cuo` =
    `redondear_euros(bas * valpor)`, en `Decimal` y lejos del cero tambien en
    negativo (devoluciones). Solo para un `ctrrec` ya resuelto (R14)."""
    bas = redondear_euros(totales[CLASES_RETENCION_BASE[int(ctrrec["cla"])]])
    return bas, redondear_euros(bas * _decimal(ctrrec["valpor"]))


def construir_dcarec(ctrrec: Mapping[str, Any], *, bas: Decimal, cuo: Decimal) -> dict[str, Any]:
    """R13: la `dcarec` del albaran, copia del `ctrrec` (M11) con `bas` y `cuo`
    de R15 y lo propio de la factura a 0 (M13). Sin `ide` ni `docide`: los pone
    `numerar`."""
    fila: dict[str, Any] = {columna: ctrrec[columna] for columna in _DCAREC_DEL_CTRREC}
    fila.update(
        {
            "ide": None,
            "docide": None,
            "bas": float(bas),
            "cuo": float(cuo),
            "ivacuo": 0,
            "reqcuo": 0,
            "refide": 0,
            "frasupide": 0,
        }
    )
    return {columna: fila[columna] for columna in DCAREC_COLUMNAS}


@dataclass(frozen=True)
class Balance:
    """Balance de UN `mov`: stock y PMP de partida y resultantes (R19)."""

    stock_anterior: float
    pmp_anterior: float
    almcan: float
    almpma: float

    @property
    def prepma(self) -> float:
        """`mov.prepma` (y `dcapro.prepma`): el PMP de PARTIDA del almacen, el
        `almpma` del `mov` anterior del mismo producto y almacen (design
        §`prepma`, v8.1; hipotesis con verificacion manual en T22/T24)."""
        return self.pmp_anterior


def siguiente_balance(
    anterior: tuple[float, float] | None, cantidad: float, pre: float
) -> Balance:
    """
    R19: `almcan` = stock + can; `almpma` = (stock·pma + can·pre)/(stock + can)
    sin redondear, y con `stock + can` = 0 se conserva el PMP. Sin `mov`
    anterior, `(0, 0)`. Las devoluciones (cantidad < 0) usan la MISMA formula:
    regla A, entrada con `canent` < 0 (M5, R18).

    «= 0» es `|stock + can| < EPSILON_STOCK`, y entonces `almcan` se escribe
    0.0: en binario 0,1 + 0,2 − 0,3 da 5,55e-17, y dividir por eso dispararia
    el PMP a ~1e17 y lo arrastraria a todas las lineas siguientes del par.
    """
    stock, pma = anterior if anterior is not None else (0.0, 0.0)
    almcan = stock + cantidad
    if abs(almcan) < EPSILON_STOCK:
        return Balance(stock_anterior=stock, pmp_anterior=pma, almcan=0.0, almpma=pma)
    almpma = (stock * pma + cantidad * pre) / almcan
    return Balance(stock_anterior=stock, pmp_anterior=pma, almcan=almcan, almpma=almpma)


def encadenar_balances(
    movimientos: Sequence[tuple[int, int, float, float]],
    vigentes: Mapping[tuple[int, int], tuple[float, float]],
) -> list[Balance]:
    """
    Los balances de los `mov` del albaran, en su orden. `movimientos` son
    `(proide, almide, cantidad, pre)`; `vigentes`, el `(almcan, almpma)` de L12/E7
    por (producto, almacen) (sin entrada: sin `mov` anterior). Si dos lineas
    llevan el mismo par, la segunda parte del resultado de la primera. No toca
    `vigentes`.
    """
    actuales: dict[tuple[int, int], tuple[float, float]] = dict(vigentes)
    balances: list[Balance] = []
    for proide, almide, cantidad, pre in movimientos:
        balance = siguiente_balance(actuales.get((proide, almide)), cantidad, pre)
        actuales[(proide, almide)] = (balance.almcan, balance.almpma)
        balances.append(balance)
    return balances


_PREFIJO_ANALITICA = "MOD."


def sufijo_analitica(caagascod: str | None) -> str:
    """R15: el `caagascod` de la naturaleza, recortado y sin el prefijo `MOD.`
    si lo lleva; entero si no (M16d). Vacio si no hay."""
    sufijo = (caagascod or "").strip()
    if sufijo.startswith(_PREFIJO_ANALITICA):
        sufijo = sufijo[len(_PREFIJO_ANALITICA):].strip()
    return sufijo


def codigo_analitica(cod_obra: str, caagascod: str | None) -> str | None:
    """`<RTRIM(cod_obra)>.<sufijo>` de la `caa` de una sin vincular (R15), o
    `None` si el sufijo sale vacio (`analitica_no_resuelta`)."""
    sufijo = sufijo_analitica(caagascod)
    return f"{cod_obra.rstrip()}.{sufijo}" if sufijo else None


def _r2(valor: float | None) -> float:
    return round(float(valor or 0), 2)


def estados_contrato(
    suma_can: float | None, suma_canser: float | None, suma_canfac: float | None
) -> tuple[int, int]:
    """
    R20: `(estser, estfac)` con las sumas del contrato (E10) tras actualizar
    `canser`. `estser` = 1 si Σcanser >= Σcan (una devolucion puede devolverlo
    a 0); `estfac` = 1 si Σcanfac >= Σcan. A 2 decimales, como el clasico; una
    suma NULL (contrato sin lineas) cuenta como 0.
    """
    can = _r2(suma_can)
    return (1 if _r2(suma_canser) >= can else 0, 1 if _r2(suma_canfac) >= can else 0)


# =====================================================================================
# Filas (T6). Todas nacen sin `ide`, `cod` ni enlaces: los pone `numerar` en cada
# intento de la transaccion (reentrante, R27). Ninguna toca su plantilla.
# =====================================================================================

#: `mov` de entrada por compra: tipo 1, origen proveedor (5), destino almacen (2).
MOV_TIP = 1
MOV_ORITIP = 5
MOV_DESTIP = 2

#: Fila de alta de `dbo.log` (F-006, M13): operacion 1 sobre la tabla `con`,
#: origen 0, estado 1.
LOG_OPE_ALTA = 1
LOG_TAB = "con"
LOG_ORI = 0

#: `dcapro.pos` en multiplos de 64, en el orden de la peticion.
POS_PASO = 64

#: `con.res` (y `log.res`): 128 caracteres.
_LARGO_RES = 128

#: Lo minimo de una `dcapro` sin plantilla (producto sin historico), como el
#: clasico: el caso de uso avisa `producto_sin_historico`.
_DCAPRO_SIN_PLANTILLA = ("cueide", "prepma", "natide", "envide", "reqcuo", "lintip", "taride", "cuoman")

#: Seguimiento del propio albaran, recien creado: nada servido ni facturado. Se
#: ponen a 0 SOLO si la plantilla las trae, como el clasico.
_SEGUIMIENTO_A_CERO = (
    "canser", "canfac", "cancan", "canped", "canorilin", "canoriant",
    "imporiant", "imporiantdiv", "imporioridiv",
)

#: §Reseteo de las sin vincular (H11, H35, M14): ninguna se arrastra de la
#: plantilla. `cod2`, `dncide` y `dncproide` vacios: decision del humano (M19).
_RESETEO_SIN_VINCULAR: dict[str, Any] = {
    "med": None,
    **dict.fromkeys(
        (
            "canmed", "parcandes", "anades", "serdes", "fecimp", "item", "anexo", "taride",
            "fec", "pla", "dncide", "dncproide", "edilin", "garfec", "mesrevpre", "ejerevpre",
        ),
        0,
    ),
    **dict.fromkeys(("tex", "texcom", "desesp", "cod2", "pac"), ""),
}

@dataclass(frozen=True)
class SellosAlbaran:
    """Los sellos de tiempo de UNA peticion, calculados una vez y fuera de la
    transaccion (R22): los reintentos no cambian de dia ni de hora."""

    fec: int        # AAAAMMDD del albaran (o hoy en Madrid): con.fec, dca.fecdoc
    hor: int        # HHMMSS del alta en Madrid: dca.hor, mov.hor, log.hor
    fec_alta: int   # AAAAMMDD del alta en Madrid: mov.fec (N1), log.fec
    fechor: float   # fec_alta.hor del alta: mov.fechor (N1)
    prefijo: str    # AC<aa>/ del anio de `fec`
    tiemod: float   # fecha OLE en UTC del alta: con.tiemod (F-015 R8, F-006)


def sellos_del_alta(
    instante_utc: datetime, fecha_albaran: int | None, prefijo: str = PREFIJO_SERIE
) -> SellosAlbaran:
    local = hora_local_de_madrid(instante_utc)
    fec_alta = int(f"{local:%Y%m%d}")
    hor = int(f"{local:%H%M%S}")
    fec = fecha_albaran or fec_alta
    return SellosAlbaran(
        fec=fec,
        hor=hor,
        fec_alta=fec_alta,
        fechor=float(f"{fec_alta}.{hor:06d}"),
        prefijo=prefijo_de_serie(fec, prefijo),
        tiemod=fecha_ole_utc(instante_utc),
    )


def construir_con(
    *, emp: int, fec: int, entres: str | None, su_referencia: str, tiemod: float
) -> dict[str, Any]:
    """`con` del albaran (F-015 R8): exactamente `CON_COLUMNAS` (F-006), sin
    plantilla. `tip` 14, `emp` de la obra, `res` = "<entres>. (<su_referencia>)"
    recortado, `fec`, `est` 1, `tiemod` del alta y el resto lo que deja el alta a
    mano (M18): `tex` NULL, textos vacios y numeros a 0."""
    fila: dict[str, Any] = {
        "ide": None,
        "emp": emp,
        "tip": TIP_ALBARAN,
        "subtip": 0,
        "cod": None,
        "res": f"{entres or ''}. ({su_referencia})".strip()[:_LARGO_RES],
        "fec": fec,
        "tex": None,
        "cee": 0,
        "est": EST_INICIAL,
        "fecbaj": 0,
        "tiemod": tiemod,
        "ico": "",
        "delo": "",
        "del": "",
        "obr": "",
        "doc": "",
        "serie": 0,
        "hor": 0,
    }
    return {columna: fila[columna] for columna in CON_COLUMNAS}


def _tiene_valor(valor: Any) -> bool:
    """R3: «trae la columna» = ni NULL, ni 0, ni texto vacio (o de espacios)."""
    if valor is None:
        return False
    if isinstance(valor, str):
        return valor.strip() != ""
    return valor != 0


def _exigir(fila: Mapping[str, Any], columnas: Sequence[str], que: str) -> None:
    """R10: a la fila le falta una columna que la lista toma de ella -> no se
    construye nada (un cambio de esquema no se rellena a ciegas)."""
    faltan = [columna for columna in columnas if columna not in fila]
    if faltan:
        raise ValueError(
            f"A la fila de {que} le faltan columnas que la lista blanca toma de ella: "
            f"{', '.join(faltan)}."
        )


#: Columnas que la lista toma del `prv` en la cascada (con su nombre en el `prv`).
_CASCADA_DEL_PROVEEDOR: tuple[str, ...] = tuple(n for n in DCA_CASCADA.values() if n)


def _origenes(
    contrato: Mapping[str, Any] | None,
    respaldo: Mapping[str, Any] | None,
    proveedor: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    """La cascada en el orden del humano (D2): contrato -> respaldo -> proveedor."""
    filas = (("contrato", contrato), ("respaldo", respaldo), ("proveedor", proveedor))
    return [(nombre, fila) for nombre, fila in filas if fila is not None]


def _en_el_origen(nombre: str, fila: Mapping[str, Any], columna: str) -> Any:
    """La columna de `dca` en una fila de la cascada; del `prv`, con su nombre
    (`None` si el `prv` no la tiene)."""
    if nombre != "proveedor":
        return fila[columna]
    en_prv = DCA_CASCADA[columna]
    return fila[en_prv] if en_prv else None


def pago_del_proveedor(
    contrato: Mapping[str, Any] | None,
    respaldo: Mapping[str, Any] | None,
    proveedor: Mapping[str, Any],
) -> bool:
    """R3: el grupo pago sale del `prv` (y hay que leer su `auxpag`) si ni el
    contrato ni el respaldo traen `pagide` y el `prv` si."""
    for nombre, fila in _origenes(contrato, respaldo, proveedor):
        _exigir(fila, ("pagide",), nombre)
        if _tiene_valor(fila["pagide"]):
            return nombre == "proveedor"
    return False


def resolver_cascada(
    *,
    contrato: Mapping[str, Any] | None,
    respaldo: Mapping[str, Any] | None,
    proveedor: Mapping[str, Any],
    pago_proveedor: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """
    Las columnas de `dca` que salen de una fila leida (F-015 R3-R5, R10): la
    identidad y la cascada, y las de cascada que ningun origen trae.

    - identidad (R4): del `contrato`; sin el, del `respaldo` y, sin el, del
      `proveedor` (`prv` mas el `cod` de L17) con los nombres de `DCA_IDENTIDAD`;
    - cascada (R3): del primer origen con valor en el orden contrato -> respaldo
      -> proveedor; el pago y el banco en grupo; del `prv`, `pagtex`/`pagfor` de
      su `auxpag` (`pago_proveedor`); `ivadif` del contrato aunque sea 0;
    - sin fuente (R5): el vacio del alta a mano, y la columna en la lista.

    Una columna que la lista toma de una fila y no esta en ella -> `ValueError`
    (R10): se comprueban todas, se usen o no.
    """
    origenes = _origenes(contrato, respaldo, proveedor)
    for nombre, fila in origenes:
        if nombre == "proveedor":
            _exigir(fila, _CASCADA_DEL_PROVEEDOR, "proveedor")
        else:
            _exigir(fila, tuple(DCA_CASCADA), nombre)

    # Identidad (R4).
    if contrato is not None or respaldo is not None:
        fuente, que = (contrato, "contrato") if contrato is not None else (respaldo, "respaldo")
        _exigir(fuente, tuple(DCA_IDENTIDAD), que)
        valores: dict[str, Any] = {columna: fuente[columna] for columna in DCA_IDENTIDAD}
    else:
        _exigir(proveedor, tuple(DCA_IDENTIDAD.values()), "proveedor")
        valores = {columna: proveedor[en_prv] for columna, en_prv in DCA_IDENTIDAD.items()}

    # Cascada (R3, R5).
    sin_fuente: list[str] = []

    def de_un_grupo(
        columnas: tuple[str, ...], trae: Callable[[str, Mapping[str, Any]], bool]
    ) -> None:
        for nombre, fila in origenes:
            if trae(nombre, fila):
                for columna in columnas:
                    valores[columna] = _de_la_cascada(nombre, fila, columna, pago_proveedor)
                return
        valores.update({columna: _valor_fijo(columna) for columna in columnas})
        sin_fuente.extend(columnas)

    de_un_grupo(GRUPO_PAGO, lambda nombre, fila: _tiene_valor(fila["pagide"]))
    de_un_grupo(
        GRUPO_BANCO,
        lambda nombre, fila: _tiene_valor(fila["banban"]) or _tiene_valor(fila["ban"]),
    )
    for columna in DCA_CASCADA:
        if columna in GRUPO_PAGO or columna in GRUPO_BANCO or columna == "ivadif":
            continue
        de_un_grupo(
            (columna,),
            lambda nombre, fila, columna=columna: _tiene_valor(_en_el_origen(nombre, fila, columna)),
        )
    # `ivadif` es una marca (D5): del contrato aunque sea 0; si no, del respaldo.
    if contrato is not None or respaldo is not None:
        valores["ivadif"] = (contrato if contrato is not None else respaldo)["ivadif"]
    else:
        valores["ivadif"] = _valor_fijo("ivadif")
        sin_fuente.append("ivadif")
    return valores, tuple(columna for columna in DCA_CASCADA if columna in sin_fuente)


def construir_dca(
    *,
    contrato: Mapping[str, Any] | None,
    proveedor: Mapping[str, Any],
    pago_proveedor: Mapping[str, Any] | None,
    respaldo: Mapping[str, Any] | None,
    fec: int,
    hor: int,
    su_referencia: str,
    obride: int,
    ctride: int,
    almide: int,
    cenide: int,
    empide: int,
    totales: Mapping[str, float],
    cuo: Decimal,
    referencia_externa: str,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    """
    `dca` del albaran por lista blanca (F-015 R1-R10): recorre `DCA_COLUMNAS` y
    da a cada una el valor de su UNICO origen (`ORIGEN_DCA`), nunca una plantilla:
    identidad y cascada de `resolver_cascada`; calculadas de la peticion, la obra
    y los totales (R8, R13), con `tot` = `totpag` = `totdoc` - `cuo` y `diremp1` =
    la `entres` escrita; y las fijas de `DCA_FIJAS` (R9).

    Devuelve la fila y las columnas de cascada que ningun origen trae (R5).
    """
    valores, sin_fuente = resolver_cascada(
        contrato=contrato, respaldo=respaldo, proveedor=proveedor, pago_proveedor=pago_proveedor
    )

    # Calculadas (R8, R13).
    tot = float(_decimal(totales["totdoc"]) - cuo)
    valores.update(
        {
            "ide": None,
            "entref": su_referencia,
            "fecdoc": fec,
            "hor": hor,
            "obride": obride,
            "ctride": ctride,
            "almide": almide,
            "cenide": cenide,
            "empide": empide,
            "synckey": referencia_externa,
            "impbru": totales["totbas"],
            "impnet": totales["totbas"],
            "totbas": totales["totbas"],
            "totiva": totales["totiva"],
            "totdoc": totales["totdoc"],
            "tot": tot,
            "totpag": tot,
            "diremp1": valores["entres"],
        }
    )
    valores.update(DCA_FIJAS)
    return {columna: valores[columna] for columna in DCA_COLUMNAS}, sin_fuente


def _de_la_cascada(
    nombre: str, fila: Mapping[str, Any], columna: str, pago_proveedor: Mapping[str, Any] | None
) -> Any:
    """El valor de `columna` en el origen elegido; del `prv`, `pagtex`/`pagfor`
    salen del `auxpag` de su `pagide`."""
    if nombre == "proveedor" and columna in PAGO_DEL_AUXPAG:
        if pago_proveedor is None:
            raise ValueError("El pago sale del proveedor y no se ha leido su auxpag.")
        _exigir(pago_proveedor, tuple(PAGO_DEL_AUXPAG.values()), "auxpag")
        return pago_proveedor[PAGO_DEL_AUXPAG[columna]]
    return _en_el_origen(nombre, fila, columna)


def _base_de_linea(plantilla: Mapping[str, Any] | None, indice: int) -> dict[str, Any]:
    fila = dict(plantilla) if plantilla is not None else dict.fromkeys(_DCAPRO_SIN_PLANTILLA, 0)
    fila.update({"ide": None, "docide": None, "pos": (indice + 1) * POS_PASO})
    for columna in _SEGUIMIENTO_A_CERO:
        if columna in fila:
            fila[columna] = 0
    return fila


def construir_dcapro_vinculada(
    plantilla: Mapping[str, Any] | None,
    *,
    indice: int,
    ctrpro: Mapping[str, Any],
    referencia_linea: str,
    cantidad: float,
    precio: float,
    descripcion: str | None,
    unidad: str | None,
    cod_contrato: str,
    ctride: int,
    obride: int,
    almide: int,
    cenide: int,
    paride: int,
    iva: float,
    prepma: float,
) -> dict[str, Any]:
    """
    `dcapro` de una linea vinculada (R12): plantilla = ultima `dcapro` del
    producto (L8), como el clasico, con producto, IVA, unidad, analitica,
    `docori*` y textos del `ctrpro`, y ademas:
    - `cod2`, `dncide` y `dncproide` del `ctrpro` (`''`/0 si no los tiene;
      nunca de la plantilla; H35);
    - `pre`, `tar` y `dto` del `ctrpro` si `usa_precio_del_contrato` (H14 y
      el mismo importe redondeado, opcion C) o `pre` = `tar` = `precio` y `dto`
      `''` si no (R17); `tot` = round(cantidad·pre, 2) del `pre` escrito;
    - `paride` el resuelto o 0, nunca el del `ctrpro` (R14, R16);
    - `almide`/`cenide` los resueltos (R15), `refent` (R30c) y `prepma` (R21).
    """
    fila = _base_de_linea(plantilla, indice)
    if usa_precio_del_contrato(cantidad, precio, ctrpro.get("pre") or 0):
        pre = float(ctrpro.get("pre") or 0)
        tar = float(ctrpro.get("tar") or pre)
        dto = ctrpro.get("dto") if ctrpro.get("dto") is not None else ""
    else:
        pre, tar, dto = precio, precio, ""
    # `tot` del `pre` escrito: fila coherente y, por la condicion de
    # `usa_precio_del_contrato`, igual al importe aprobado (cantidad·precio).
    tot, ivacuo = importe_linea(cantidad, pre, iva)
    fila.update(
        {
            "proide": ctrpro.get("proide"),
            "can": cantidad,
            "pre": pre,
            "tar": tar,
            "dto": dto,
            "tot": float(tot),
            "ivaide": ctrpro.get("ivaide"),
            "ivacuo": float(ivacuo),
            "res": descripcion or ctrpro.get("res") or "",
            "tex": ctrpro.get("tex") if ctrpro.get("tex") is not None else "",
            "almide": almide,
            "obride": obride,
            "cenide": cenide,
            "caaide": ctrpro.get("caaide") or 0,
            "paride": paride,
            "docoritip": TIP_CONTRATO,
            "docoricod": cod_contrato,
            "docoriide": ctride,
            "linoriide": ctrpro.get("ide"),
            "canoriori": _r2(ctrpro.get("can")),
            "imporiori": _r2(ctrpro.get("tot")),
            "refent": referencia_linea,
            "cod2": ctrpro.get("cod2") or "",
            "dncide": ctrpro.get("dncide") or 0,
            "dncproide": ctrpro.get("dncproide") or 0,
            "prepma": prepma,
        }
    )
    unimed = unidad or ctrpro.get("unimed")
    if unimed is not None:
        fila["unimed"] = unimed
    return fila


def construir_dcapro_sin_vincular(
    plantilla: Mapping[str, Any] | None,
    *,
    indice: int,
    proide: int,
    referencia_linea: str,
    cantidad: float,
    precio: float,
    descripcion: str,
    unidad: str | None,
    natide: int,
    cueide: int,
    caaide: int,
    obride: int,
    almide: int,
    cenide: int,
    paride: int,
    iva: float,
    prepma: float,
) -> dict[str, Any]:
    """
    `dcapro` de una linea sin vincular (R13): plantilla = L8b (mismo
    proveedor) o L8 (con aviso `iva_de_otro_proveedor`), de la que solo vale
    el `ivaide`. `natide`, `cueide` y `caaide` de la naturaleza del mapeo y de
    la obra (R13b, R15); `pre` = `tar` = `precio` y `dto` `''`; sin `docori*`
    ni cantidades o importes de origen; y §Reseteo (H11, H35).
    """
    fila = _base_de_linea(plantilla, indice)
    tot, ivacuo = importe_linea(cantidad, precio, iva)
    for columna in ("canoriori", "imporiori"):
        if columna in fila:
            fila[columna] = 0
    fila.update(_RESETEO_SIN_VINCULAR)
    fila.update(
        {
            "proide": proide,
            "can": cantidad,
            "pre": precio,
            "tar": precio,
            "dto": "",
            "tot": float(tot),
            "ivaide": (plantilla or {}).get("ivaide") or 0,
            "ivacuo": float(ivacuo),
            "res": descripcion,
            "unimed": unidad or "",
            "natide": natide,
            "cueide": cueide,
            "caaide": caaide,
            "obride": obride,
            "almide": almide,
            "cenide": cenide,
            "paride": paride,
            "docoritip": 0,
            "docoricod": "",
            "docoriide": 0,
            "linoriide": 0,
            "refent": referencia_linea,
            "prepma": prepma,
        }
    )
    return fila


def construir_ctrprodes(*, ctrpro_ide: int, cantidad: float) -> dict[str, Any]:
    """Enlace contrato -> albaran de UNA vinculada, `can` con signo (M6)."""
    return {
        "ide": None,
        "docproide": ctrpro_ide,
        "can": cantidad,
        "docdestip": TIP_ALBARAN,
        "docdescod": None,
        "docdeside": None,
        "lindeside": None,
        "ctrproactide": 0,
    }


def construir_mov(
    *,
    emp: int,
    entide: int,
    almide: int,
    proide: int,
    cantidad: float,
    pre: float,
    balance: Balance,
    sellos: SellosAlbaran,
) -> dict[str, Any]:
    """`mov` de UNA linea con `pro.tipmov` = 1 (R19), como el clasico salvo
    `emp` = `con.emp` (R22), fecha y hora del ALTA (N1) y `prepma` = PMP de
    partida (design §`prepma`). Las devoluciones, entrada con `canent` < 0
    (regla A, R18)."""
    return {
        "ide": None,
        "emp": emp,
        "docide": None,
        "linide": None,
        "tip": MOV_TIP,
        "oritip": MOV_ORITIP,
        "oriide": entide,
        "destip": MOV_DESTIP,
        "deside": almide,
        "proide": proide,
        "doctip": TIP_ALBARAN,
        "fec": sellos.fec_alta,
        "hor": sellos.hor,
        "fecdoc": 0,
        "canent": cantidad,
        "cansal": 0.0,
        "pre": pre,
        "prc": pre,
        "prepma": balance.prepma,
        "nueusa": 0,
        "almide": almide,
        "almcan": balance.almcan,
        "almpma": balance.almpma,
        "fecblo": 0,
        "fechor": sellos.fechor,
    }


def construir_log(*, emp: int, usu: str, res: str, sellos: SellosAlbaran) -> dict[str, Any]:
    """Fila de alta de `log` (la de F-006; M13): `est` 1, `ori` 0, `ope` 1."""
    return {
        "ide": None,
        "emp": emp,
        "ori": LOG_ORI,
        "ope": LOG_OPE_ALTA,
        "fec": sellos.fec_alta,
        "hor": sellos.hor,
        "usu": usu,
        "tab": LOG_TAB,
        "tip": TIP_ALBARAN,
        "cod": None,
        "res": res,
        "tex": None,
        "est": EST_INICIAL,
        "err": None,
    }


@dataclass(frozen=True)
class FilasAlbaran:
    """
    Las filas de UN albaran. `ctrprodes` y `mov` van como `(i, fila)`, con `i`
    el indice de su `dcapro` en `dcapro`: de ahi salen `lindeside` y `linide`
    al numerar (no todas las lineas tienen `ctrprodes` ni `mov`). `dcarec`
    (F-015 R13) es la retencion del contrato: vacia o una fila.
    """

    con: dict[str, Any]
    dca: dict[str, Any]
    dcapro: list[dict[str, Any]]
    ctrprodes: list[tuple[int, dict[str, Any]]]
    mov: list[tuple[int, dict[str, Any]]]
    log: dict[str, Any]
    dcarec: list[dict[str, Any]] = field(default_factory=list)

    def como_dict(self) -> dict[str, Any]:
        """`filas` de la respuesta (R23)."""
        return {
            "con": self.con,
            "dca": self.dca,
            "dcapro": self.dcapro,
            "ctrprodes": [fila for _, fila in self.ctrprodes],
            "mov": [fila for _, fila in self.mov],
            "dcarec": self.dcarec,
            "log": self.log,
        }


def numerar(
    filas: FilasAlbaran,
    *,
    cod: str,
    ide_con: int,
    ide_dcapro: int,
    ide_ctrprodes: int | None,
    ide_mov: int | None,
    ide_log: int | None,
    ide_dcarec: int | None = None,
) -> FilasAlbaran:
    """
    Copia de `filas` con `cod`, los `ide` reservados y los enlaces puestos. No
    toca `filas`: cada reintento numera sobre las filas limpias (R27). Los
    `ide` de cada tabla son consecutivos desde el reservado; sin `ctrprodes` o
    sin `mov` no hace falta reservar (`None`). El commit numera `log` con
    `None` y le pone su `ide` al reservarlo, al final (E11b, como F-006).
    La `dcarec` (F-015 R20) lleva el `ide` reservado y `docide` = `ide_con`.
    """
    if filas.ctrprodes and ide_ctrprodes is None:
        raise ValueError("Hay ctrprodes y no se ha reservado ide_ctrprodes.")
    if filas.mov and ide_mov is None:
        raise ValueError("Hay mov y no se ha reservado ide_mov.")
    if filas.dcarec and ide_dcarec is None:
        raise ValueError("Hay dcarec y no se ha reservado ide_dcarec.")
    if len(filas.dcarec) > 1:
        raise ValueError("Un albaran lleva como mucho una dcarec (F-015 R12).")
    ides_dcapro = [ide_dcapro + i for i in range(len(filas.dcapro))]
    return FilasAlbaran(
        con={**filas.con, "ide": ide_con, "cod": cod},
        dca={**filas.dca, "ide": ide_con},
        dcapro=[
            {**fila, "ide": ides_dcapro[i], "docide": ide_con}
            for i, fila in enumerate(filas.dcapro)
        ],
        ctrprodes=[
            (
                i,
                {
                    **fila,
                    "ide": ide_ctrprodes + j,
                    "docdescod": cod,
                    "docdeside": ide_con,
                    "lindeside": ides_dcapro[i],
                },
            )
            for j, (i, fila) in enumerate(filas.ctrprodes)
        ],
        mov=[
            (i, {**fila, "ide": ide_mov + k, "docide": ide_con, "linide": ides_dcapro[i]})
            for k, (i, fila) in enumerate(filas.mov)
        ],
        log={**filas.log, "ide": ide_log, "cod": cod},
        dcarec=[{**fila, "ide": ide_dcarec, "docide": ide_con} for fila in filas.dcarec],
    )


class AlbaranCompraStatements:
    def __init__(self, *, database: str) -> None:
        self._database = database.strip()
        # R31: se valida TODO antes de que nadie abra una conexion.
        for sql in self.todas_las_sentencias():
            self._validar(sql)

    def _validar(self, sql: str) -> str:
        DatabaseReferenceGuard.validate(sql, allowed=[self._database], contexto="escritura")
        return sql

    def _con_lista(self, plantilla: str, valores: Sequence[Any]) -> str:
        if not valores:
            raise ValueError("Lista vacia: no hay nada que buscar con IN.")
        return self._validar(plantilla.format(marcadores=_marcadores(len(valores))))

    @staticmethod
    def todas_las_sentencias() -> tuple[str, ...]:
        """Todas las constantes, las de `IN` con un solo marcador."""
        uno = _marcadores(1)
        return (
            L1_OBRA,
            L5_RESPALDO_POR_ENTIDE,
            L5_RESPALDO_POR_CIF,
            L17_PROVEEDOR_POR_CIF,
            L6_PARTIDAS.format(marcadores=uno),
            L7_PRODUCTOS.format(marcadores=uno),
            L7B_TIPMOV.format(marcadores=uno),
            L8_PLANTILLA_LINEA,
            L8B_PLANTILLA_LINEA_PROVEEDOR,
            L9_TASAS_IVA.format(marcadores=uno),
            L10_ALMACEN_DE_OBRA,
            L10_ALMACENES,
            L10_ALMACENES + L10_ALMACENES_RESUELTOS.format(marcadores=uno),
            L11_REFERENCIA,
            L11_LINEAS,
            L12_BALANCE,
            L16_RETENCIONES,
            L13A_ESTADO,
            L13B_USUARIO,
            L14_ULTIMO_COD,
            L15A_NATURALEZAS.format(marcadores=uno),
            L15B_ANALITICAS.format(marcadores=uno),
            L15C_CUENTAS.format(marcadores=uno),
            E2_COD,
            E3_IDE_CON,
            E4_IDE_DCAPRO,
            E5_IDE_CTRPRODES,
            E6_IDE_MOV,
            E6B_IDE_DCAREC,
            E7_BALANCE,
            _insert_fijo("con", CON_COLUMNAS),
            _insert_fijo("dca", DCA_COLUMNAS),
            _insert_fijo("ctrprodes", CTRPRODES_COLUMNAS),
            _insert_fijo("mov", MOV_COLUMNAS),
            _insert_fijo("dcarec", DCAREC_COLUMNAS),
            E9_SERVIDO,
            E10_SUMAS_CONTRATO,
            E11_ESTADOS_CONTRATO,
            E11B_IDE_LOG,
            _insert_fijo("log", LOG_COLUMNAS),
            E12_CON,
            E12_DCA,
            E12_DCAPRO,
            E12_CTRPRODES,
            E12_MOV,
            E12_DCAREC,
            E12_LOG,
        )

    # --- Lecturas de cabecera ----------------------------------------------------

    def leer_obra(self, cod: str) -> tuple[str, list[Any]]:
        return L1_OBRA, [TIP_OBRA, cod]

    def leer_plantilla_cabecera(self, emp: int, entide: int) -> tuple[str, list[Any]]:
        """L5: el respaldo (F-015 R6), el ultimo albaran `AC` de clase 0 y sin
        referencia de proforma del MISMO proveedor en la empresa de la obra (H3).
        Opcional: sin filas no hay respaldo, ni error."""
        return L5_RESPALDO_POR_ENTIDE, [
            TIP_ALBARAN, emp, entide, PATRON_SERIE_RESPALDO, CLA_ALBARAN, PATRON_PROFORMA,
        ]

    def leer_plantilla_cabecera_por_cif(self, emp: int, cif: str) -> tuple[str, list[Any]]:
        """L5 sin contrato: el proveedor se reconoce por `dca.entcif`."""
        return L5_RESPALDO_POR_CIF, [
            TIP_ALBARAN, emp, cif, PATRON_SERIE_RESPALDO, CLA_ALBARAN, PATRON_PROFORMA,
        ]

    def leer_proveedor_por_cif(self, emp: int, cif: str) -> tuple[str, list[Any]]:
        """L17 (F-015 R7): los `prv` vivos con ese CIF en la empresa de la obra,
        solo sin contrato ni respaldo por CIF."""
        return L17_PROVEEDOR_POR_CIF, [TIP_PROVEEDOR, emp, 0, cif]

    def buscar_referencia(self, referencia: str) -> tuple[str, list[Any]]:
        """L11 (previa) y E1 (bajo el applock de referencias): la MISMA sentencia."""
        return L11_REFERENCIA, [TIP_ALBARAN, referencia]

    def leer_lineas_de_albaran(self, docide: int) -> tuple[str, list[Any]]:
        return L11_LINEAS, [docide]

    def leer_retenciones(self, ctride: int) -> tuple[str, list[Any]]:
        """L16 (F-015 R12): los `ctrrec` del contrato, con o sin vinculadas."""
        return L16_RETENCIONES, [ctride]

    def leer_estado_inicial(self) -> tuple[str, list[Any]]:
        return L13A_ESTADO, [TIP_ALBARAN, EST_INICIAL]

    def leer_usuario(self, usu: str) -> tuple[str, list[Any]]:
        return L13B_USUARIO, [usu]

    def ultimo_cod(self, emp: int, prefijo: str) -> tuple[str, list[Any]]:
        """L14: el `cod` provisional de la previa, E2 sin bloqueos."""
        return L14_ULTIMO_COD, _parametros_de_serie(emp, prefijo)

    # --- Lecturas de linea ------------------------------------------------------------

    def leer_partidas(self, obride: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(L6_PARTIDAS, codigos), [obride, *codigos]

    def leer_productos(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(L7_PRODUCTOS, codigos), [emp, TIP_PRODUCTO, *codigos]

    def leer_tipmov(self, proides: Sequence[int]) -> tuple[str, list[Any]]:
        return self._con_lista(L7B_TIPMOV, proides), [*proides]

    def leer_plantilla_linea(self, proide: int) -> tuple[str, list[Any]]:
        return L8_PLANTILLA_LINEA, [proide]

    def leer_plantilla_linea_del_proveedor(self, proide: int, entide: int) -> tuple[str, list[Any]]:
        return L8B_PLANTILLA_LINEA_PROVEEDOR, [proide, entide]

    def leer_tasas_iva(self, ivaides: Sequence[int]) -> tuple[str, list[Any]]:
        return self._con_lista(L9_TASAS_IVA, ivaides), [*ivaides]

    def leer_almacen_de_obra(self, obride: int) -> tuple[str, list[Any]]:
        return L10_ALMACEN_DE_OBRA, [obride]

    def leer_almacenes(self, obride: int, almides: Sequence[int]) -> tuple[str, list[Any]]:
        """Los almacenes de la obra y los ya resueltos (M8). Sin resueltos, solo
        los de la obra: `ide IN ()` no es SQL."""
        if not almides:
            return L10_ALMACENES, [obride]
        sql = self._con_lista(L10_ALMACENES + L10_ALMACENES_RESUELTOS, almides)
        return sql, [obride, *almides]

    def leer_balance(self, proide: int, almide: int) -> tuple[str, list[Any]]:
        return L12_BALANCE, [proide, almide]

    def leer_naturalezas(self, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(L15A_NATURALEZAS, codigos), [*codigos]

    def leer_analiticas(self, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(L15B_ANALITICAS, codigos), [*codigos]

    def leer_cuentas(self, emp: int, codigos: Sequence[str]) -> tuple[str, list[Any]]:
        return self._con_lista(L15C_CUENTAS, codigos), [emp, *codigos]

    # --- Reservas bajo bloqueo (E2-E7, E11b) ----------------------------------------

    def reservar_cod(self, emp: int, prefijo: str) -> tuple[str, list[Any]]:
        return E2_COD, _parametros_de_serie(emp, prefijo)

    def reservar_ide_con(self) -> tuple[str, list[Any]]:
        return E3_IDE_CON, []

    def reservar_ide_dcapro(self) -> tuple[str, list[Any]]:
        return E4_IDE_DCAPRO, []

    def reservar_ide_ctrprodes(self) -> tuple[str, list[Any]]:
        return E5_IDE_CTRPRODES, []

    def reservar_ide_mov(self) -> tuple[str, list[Any]]:
        return E6_IDE_MOV, []

    def reservar_ide_dcarec(self) -> tuple[str, list[Any]]:
        """E6b (F-015 R21)."""
        return E6B_IDE_DCAREC, []

    def reservar_balance(self, proide: int, almide: int) -> tuple[str, list[Any]]:
        return E7_BALANCE, [proide, almide]

    def reservar_ide_log(self) -> tuple[str, list[Any]]:
        return E11B_IDE_LOG, []

    # --- Inserciones (E8, E11b) --------------------------------------------------------

    def insertar_clonada(self, tabla: str, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        """`INSERT` de una fila clonada de su plantilla: sus columnas, en su
        orden. Los nombres salen de la base (`SELECT *`), no de la peticion, y
        aun asi cada uno se valida como identificador antes de entrar."""
        if tabla not in _TABLAS_CLONADAS:
            raise ValueError(f"La tabla '{tabla}' no se escribe por clonado.")
        if not fila:
            raise ValueError(f"Fila de '{tabla}' vacia: no hay nada que insertar.")
        columnas = [
            IdentifierGuard.validate_identifier(columna, field_name=f"{tabla}.columna")
            for columna in fila
        ]
        if columnas != list(fila):
            # El guardia recorta: una columna con espacios no es la de la fila.
            raise ValueError(f"Columnas no validas en '{tabla}'.")
        sql = (
            f"INSERT INTO dbo.{tabla} ({', '.join(f'[{c}]' for c in columnas)}) "
            f"VALUES ({', '.join(['?'] * len(columnas))})"
        )
        return self._validar(sql), list(fila.values())

    def insertar_dcapro(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self.insertar_clonada("dcapro", fila)

    @staticmethod
    def _insertar_fija(
        tabla: str, columnas: tuple[str, ...], fila: Mapping[str, Any]
    ) -> tuple[str, list[Any]]:
        if set(fila) != set(columnas) or len(fila) != len(columnas):
            raise ValueError(
                f"La fila de '{tabla}' no trae exactamente sus columnas: "
                f"faltan {sorted(set(columnas) - set(fila))}, sobran {sorted(set(fila) - set(columnas))}."
            )
        return _insert_fijo(tabla, columnas), [fila[c] for c in columnas]

    def insertar_con(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        """F-015 R1: `con` con `CON_COLUMNAS` (F-006), nunca las de una fila leida."""
        return self._insertar_fija("con", CON_COLUMNAS, fila)

    def insertar_dca(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        """F-015 R1: `dca` con las 145 de `DCA_COLUMNAS`."""
        return self._insertar_fija("dca", DCA_COLUMNAS, fila)

    def insertar_ctrprodes(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar_fija("ctrprodes", CTRPRODES_COLUMNAS, fila)

    def insertar_mov(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar_fija("mov", MOV_COLUMNAS, fila)

    def insertar_log(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar_fija("log", LOG_COLUMNAS, fila)

    def insertar_dcarec(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        """F-015 R13, R21: la retencion del contrato, con las 21 de `DCAREC_COLUMNAS`."""
        return self._insertar_fija("dcarec", DCAREC_COLUMNAS, fila)

    # --- Medicion del contrato (E9-E11; solo con vinculadas, H31) -------------------

    def sumar_servido(self, ctrpro_ide: int, cantidad: float) -> tuple[str, list[Any]]:
        """E9: `UPDATE` RELATIVO, por linea (no se suman las del mismo `ctrpro`)."""
        return E9_SERVIDO, [cantidad, ctrpro_ide]

    def leer_sumas_contrato(self, ctride: int) -> tuple[str, list[Any]]:
        return E10_SUMAS_CONTRATO, [ctride]

    def actualizar_estados_contrato(
        self, ctride: int, estser: int, estfac: int
    ) -> tuple[str, list[Any]]:
        return E11_ESTADOS_CONTRATO, [estser, estfac, ctride]

    # --- Relecturas previas al COMMIT (E12, R28) ---------------------------------------

    def releer_con(self, emp: int, cod: str) -> tuple[str, list[Any]]:
        return E12_CON, [emp, TIP_ALBARAN, cod]

    def releer_dca(self, ide: int) -> tuple[str, list[Any]]:
        return E12_DCA, [ide]

    def releer_dcapro(self, docide: int) -> tuple[str, list[Any]]:
        return E12_DCAPRO, [docide]

    def releer_ctrprodes(self, docdeside: int) -> tuple[str, list[Any]]:
        return E12_CTRPRODES, [docdeside, TIP_ALBARAN]

    def releer_mov(self, docide: int) -> tuple[str, list[Any]]:
        return E12_MOV, [docide, TIP_ALBARAN]

    def releer_log(self, ide: int) -> tuple[str, list[Any]]:
        return E12_LOG, [ide]

    def releer_dcarec(self, docide: int) -> tuple[str, list[Any]]:
        """E12 (F-015 R23)."""
        return E12_DCAREC, [docide]
