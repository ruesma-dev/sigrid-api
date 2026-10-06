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
§Sentencias en su v8.1 (sin L12b, L12c ni E7b). `con`, `dca` y `dcapro` se
CLONAN de su plantilla (`SELECT *`, como el modo clasico): sus columnas son las
de la fila, cada una validada como identificador y entre corchetes; `mov`,
`ctrprodes` y `log` tienen columnas fijas (las del clasico y las de F-006).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from application.use_cases.parte_reclamacion_statements import LOG_COLUMNAS
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard
from infrastructure.security.identifier_guard import IdentifierGuard

#: Tipos de concepto (`con.tip`): albaran de compra, contrato, obra y producto.
TIP_ALBARAN = 14
TIP_CONTRATO = 44
TIP_OBRA = 42
TIP_PRODUCTO = 3

#: Prefijo de la serie del albaran de compra: `AC<aa>/` del anio de la fecha.
PREFIJO_SERIE = "AC"

#: Tolerancia de precio frente al `ctrpro` (H14, M4) y centimo de euro (H33).
TOLERANCIA_PRECIO = Decimal("0.0001")
_CENTIMO = Decimal("0.01")

#: Estado inicial del albaran: `est` 1 (`PDT`), que debe estar en `dbo.conest` (R22).
EST_INICIAL = 1

#: Applocks de la transaccion, SIEMPRE en este orden (design §Applocks): los
#: cuatro del medio, como el clasico y `albaran-directo`; F-006 toma `_con` y
#: `_log` en el mismo orden, asi que no hay orden inverso posible.
APPLOCKS: tuple[str, ...] = (
    "SIGRID_REFEXT_14",
    "SIGRID_SERIE_14",
    "SIGRID_IDE_con",
    "SIGRID_IDE_dcapro",
    "SIGRID_IDE_ctrprodes",
    "SIGRID_IDE_mov",
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

#: Tablas que se clonan de una plantilla y cuyo `INSERT` lleva las columnas de
#: la fila. Ninguna otra se escribe asi.
_TABLAS_CLONADAS = frozenset({"con", "dca", "dcapro"})

# --- Lecturas (con credenciales de lectura) -------------------------------------
# `{marcadores}` es la lista `(?, ?, ...)` de un `IN`; nunca lleva valores.

L1_OBRA = "SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?"
L5_PLANTILLA_POR_ENTIDE = (
    "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND d.entide = ? ORDER BY c.ide DESC"
)
L5_PLANTILLA_POR_CIF = (
    "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
    "WHERE c.tip = ? AND c.emp = ? AND d.entcif = ? ORDER BY c.ide DESC"
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
L11_REFERENCIA = (
    "SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc FROM dbo.dca d "
    "JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?"
)
L11_LINEAS = (
    "SELECT pos, proide, can, pre, tot, paride, almide, refent FROM dbo.dcapro "
    "WHERE docide = ? ORDER BY pos"
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


def prefijo_de_serie(fecha: int) -> str:
    """`AC<aa>/` del anio de `fecha` (AAAAMMDD, la del albaran; R22)."""
    return f"{PREFIJO_SERIE}{(fecha // 10000) % 100:02d}/"


def siguiente_cod(prefijo: str, maximo: int | None) -> str:
    """El siguiente `cod` de la serie a partir del MAX numerico de E2/L14
    (`None` si no hay ninguno). Sin ceros a la izquierda, como el clasico."""
    return f"{prefijo}{(maximo or 0) + 1}"


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
    """
    stock, pma = anterior if anterior is not None else (0.0, 0.0)
    almcan = stock + cantidad
    almpma = pma if almcan == 0 else (stock * pma + cantidad * pre) / almcan
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
            L5_PLANTILLA_POR_ENTIDE,
            L5_PLANTILLA_POR_CIF,
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
            E7_BALANCE,
            _insert_fijo("ctrprodes", CTRPRODES_COLUMNAS),
            _insert_fijo("mov", MOV_COLUMNAS),
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
            E12_LOG,
        )

    # --- Lecturas de cabecera ----------------------------------------------------

    def leer_obra(self, cod: str) -> tuple[str, list[Any]]:
        return L1_OBRA, [TIP_OBRA, cod]

    def leer_plantilla_cabecera(self, emp: int, entide: int) -> tuple[str, list[Any]]:
        """L5: ultimo albaran del MISMO proveedor en la empresa de la obra (H3)."""
        return L5_PLANTILLA_POR_ENTIDE, [TIP_ALBARAN, emp, entide]

    def leer_plantilla_cabecera_por_cif(self, emp: int, cif: str) -> tuple[str, list[Any]]:
        """L5 sin contrato: el proveedor se reconoce por `dca.entcif`."""
        return L5_PLANTILLA_POR_CIF, [TIP_ALBARAN, emp, cif]

    def buscar_referencia(self, referencia: str) -> tuple[str, list[Any]]:
        """L11 (previa) y E1 (bajo el applock de referencias): la MISMA sentencia."""
        return L11_REFERENCIA, [TIP_ALBARAN, referencia]

    def leer_lineas_de_albaran(self, docide: int) -> tuple[str, list[Any]]:
        return L11_LINEAS, [docide]

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

    def insertar_con(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self.insertar_clonada("con", fila)

    def insertar_dca(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self.insertar_clonada("dca", fila)

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

    def insertar_ctrprodes(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar_fija("ctrprodes", CTRPRODES_COLUMNAS, fila)

    def insertar_mov(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar_fija("mov", MOV_COLUMNAS, fila)

    def insertar_log(self, fila: Mapping[str, Any]) -> tuple[str, list[Any]]:
        return self._insertar_fija("log", LOG_COLUMNAS, fila)

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
