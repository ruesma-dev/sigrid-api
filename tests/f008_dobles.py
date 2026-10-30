# tests/f008_dobles.py
"""
F-008 · dobles y ERP de mentira de `sigrid/factura`. No es un fichero de tests:
lo importan `test_f008_use_case.py`, `test_f008_transaccion.py` y
`test_f008_route.py`.

Sin red y sin base de datos. El repositorio doble reconoce cada sentencia por
su SQL EXACTO (el de `FacturaStatements` y las de F-009 que se reutilizan; las
listas `IN (?, ...)` se normalizan a un marcador): una sentencia desconocida
hace fallar el test. Graba nombre y parametros de cada lectura. Las respuestas
salen de `Mundo`, un ERP diminuto en memoria que se puede retocar test a test.

Datos sinteticos: ni CIF, ni obras, ni proveedores, ni identificadores reales.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.use_cases.albaran_compra_statements import AlbaranCompraStatements
from application.use_cases.factura_statements import (
    CABECERA_DE_ORIGEN,
    LINEA_DE_ORIGEN,
    PROVEEDOR,
    RETENCION_DE_ORIGEN,
    FacturaStatements,
)

BD = "ruesma"
#: 09:00 UTC del 30 de octubre de 2026 = 10:00 en Madrid (CET).
AHORA = datetime(2026, 10, 30, 9, 0, 0, tzinfo=timezone.utc)

_F = FacturaStatements(database=BD)
_A = AlbaranCompraStatements(database=BD)
_IN = re.compile(r"IN \(\?(?:, \?)*\)")


def normalizar(sql: str) -> str:
    return _IN.sub("IN (?)", sql)


#: SQL exacto (IN normalizado) -> nombre corto de la lectura.
NOMBRES: dict[str, str] = {
    normalizar(sql): nombre
    for sql, nombre in (
        (_F.leer_estados()[0], "conest"),
        (_F.leer_proveedor(1)[0], "proveedor"),
        (_F.leer_auxpag(1)[0], "auxpag"),
        (_F.leer_obras(1, ["x"])[0], "obras"),
        (_F.leer_origenes(["x"])[0], "origenes"),
        (_F.leer_cabecera_de_origen(1)[0], "cabecera_de_origen"),
        (_F.leer_asientos(1, ["x"])[0], "asientos"),
        (_F.leer_lineas_de_origenes([1])[0], "lineas_de_origenes"),
        (_F.leer_facturadas([1])[0], "facturadas"),
        (_F.leer_anteriores([1])[0], "anteriores"),
        (_F.leer_retenciones([1])[0], "retenciones"),
        (_F.leer_ivas(1, ["x"])[0], "ivas"),
        (_F.leer_cuentas_gasto(1, ["x"])[0], "cuentas_gasto"),
        (_F.leer_analiticas_gasto(1, ["x"])[0], "analiticas_gasto"),
        (_F.buscar_referencia("x")[0], "referencia"),
        (_F.buscar_duplicadas("x", "x", 1)[0], "duplicadas"),
        (_F.ultimo_cod(1, "FR26/", 5)[0], "ultimo_cod"),
        (_A.leer_obra("x")[0], "obra"),
        (_A.leer_usuario("x")[0], "usuario"),
        (_A.leer_proveedor_por_cif(1, "x")[0], "proveedor_por_cif"),
        (_A.leer_productos(1, ["x"])[0], "productos"),
        (_A.leer_naturalezas(["x"])[0], "naturalezas"),
        (_A.leer_cuentas(1, ["x"])[0], "cuentas"),
        (_A.leer_analiticas(["x"])[0], "analiticas"),
        (_A.leer_partidas(1, ["x"])[0], "partidas"),
        (_A.leer_almacen_de_obra(1)[0], "almacen_de_obra"),
        (_A.leer_almacenes(1, [])[0], "almacenes"),
    )
}


def _c(texto: Any) -> str:
    return str(texto).strip().casefold()


def cabecera_de_origen(**cambios: Any) -> dict[str, Any]:
    """La `dca` de un albaran del proveedor 500 en la obra 0404."""
    base = dict.fromkeys(CABECERA_DE_ORIGEN, 0)
    base.update(
        entide=500, entcod="P500", entres="PROVEEDOR UNO SL", entcif="B00000001", entciftip=1,
        entcifpai="ES", obride=4040, cenide=80, almide=70, empide=0, diremp1=0, dircon1=0,
        dirdir1=0, pagide=7, pagtex="30 DIAS", pagfor="30", efeide=2, eioide=0, ivadif=0, cocide=0,
        tipgar=-1, fecent=20261001, feclim=0, banban="0000", bansuc="0000", bandig="00",
        bancue="0000000000", ban="ES0000000000000000000000", bantipide=1,
    )
    base.update(cambios)
    return base


def linea(ide: int, docide: int, pos: int, **cambios: Any) -> dict[str, Any]:
    """Una `dcapro` de origen (las columnas de LF8)."""
    base = dict.fromkeys(LINEA_DE_ORIGEN, 0)
    base.update(
        ide=ide, docide=docide, pos=pos, proide=300, can=2.0, pre=10.0, tar=10.0, dto="", tot=20.0,
        ivaide=21, ivacuo=4.2, cenide=80, caaide=191, paride=355, natide=50, almide=70,
        obride=4040, res="ARIDO", tex="", cod2="", unimed="T", prepma=9.0, dncide=0, dncproide=0,
        canfac=0.0, linoriide=0, canorilin=0, canoriori=0.0, imporiori=0.0, docoritip=0,
    )
    base.update(cambios)
    return base


@dataclass
class Mundo:
    """El ERP de mentira. Empresa 1; obras 0404 (con almacen en su ficha) y GG
    (sin el, con un unico `alm`); proveedor 500; albaranes AC26/1 y AC26/2 de
    mes contabilizados y la proforma PROF26/1 a origen, vinculada a un contrato."""

    usuarios: set[str] = field(default_factory=lambda: {"prueba"})
    conest: list[tuple[int, int, str]] = field(default_factory=lambda: [
        (15, 1, "REC"), (15, 15, "RECH"), (15, 20, "RECGG"), (15, 30, "COM"),
        (14, 1, "PDT"), (14, 3, "CON"), (14, 10, "FAC"), (25, 1, "PDT"),
    ])
    #: (ide, emp, cod, cenide, almide)
    obras: list[tuple[int, int, str, int, int]] = field(default_factory=lambda: [
        (4040, 1, "0404", 80, 70), (9000, 1, "GG", 81, 0), (9100, 2, "0404", 82, 72),
    ])
    #: (ide, obride, cenide)
    almacenes: list[tuple[int, int, int]] = field(default_factory=lambda: [
        (70, 4040, 80), (71, 9000, 81),
    ])
    proveedores: dict[int, dict[str, Any]] = field(default_factory=lambda: {
        500: {
            "ide": 500, "cod": "P500", "raz": "PROVEEDOR UNO SL", "cif": "B00000001",
            "tipcif": 1, "cifpai": "ES", "cueide": 4001, "cuepdtide": 4009, "pagide": 7,
            "efeide": 2, "eioide": 0, "banban": "1111", "bansuc": "2222", "bandig": "33",
            "bancue": "4444444444", "ban": "ES1111111111111111111111", "bantipide": 1,
            "emp": 1, "fecbaj": 0,
        },
        600: {
            "ide": 600, "cod": "P600", "raz": "PROVEEDOR DOS SL", "cif": "B00000002",
            "tipcif": 1, "cifpai": "ES", "cueide": 4002, "cuepdtide": 4019, "pagide": 0,
            "efeide": 2, "eioide": 0, "banban": "", "bansuc": "", "bandig": "", "bancue": "",
            "ban": "", "bantipide": 0, "emp": 1, "fecbaj": 0,
        },
    })
    auxpag: dict[int, tuple[str, str]] = field(default_factory=lambda: {7: ("30 DIAS", "30")})
    #: ide -> (ide, cod, emp, est, entide, obride, ctride, docoritip)
    origenes: dict[int, dict[str, Any]] = field(default_factory=lambda: {
        800: {"ide": 800, "cod": "AC26/1", "emp": 1, "est": 3, "entide": 500, "obride": 4040,
              "ctride": 0, "docoritip": 0},
        801: {"ide": 801, "cod": "AC26/2", "emp": 1, "est": 3, "entide": 500, "obride": 4040,
              "ctride": 0, "docoritip": 0},
        810: {"ide": 810, "cod": "PROF26/1", "emp": 1, "est": 3, "entide": 500, "obride": 4040,
              "ctride": 900, "docoritip": 1},
    })
    cabeceras: dict[int, dict[str, Any]] = field(default_factory=lambda: {
        800: cabecera_de_origen(), 801: cabecera_de_origen(fecent=20261005),
        810: cabecera_de_origen(),
    })
    asientos: set[tuple[int, str]] = field(default_factory=lambda: {
        (1, "AC26/1"), (1, "AC26/2"), (1, "PROF26/1"),
    })
    lineas: list[dict[str, Any]] = field(default_factory=lambda: [
        linea(8001, 800, 64),
        linea(8002, 800, 128, can=0.0, tot=0.0, ivacuo=0.0),
        linea(8011, 801, 64, can=1.0, pre=5.0, tar=5.0, tot=5.0, ivacuo=1.05),
        linea(8101, 810, 64, can=3.0, pre=10.0, tar=10.0, tot=30.0, ivacuo=6.3, linoriide=9901,
              docoritip=44, canorilin=7001, canoriori=10.0, imporiori=100.0),
    ])
    #: dcapro.ide de lineas ya llevadas a una factura (`dcaprodes` 15).
    facturadas: set[int] = field(default_factory=set)
    #: dcapro.ide -> (canoriori, imporiori) de las lineas anteriores de la cadena.
    anteriores: dict[int, tuple[float, float]] = field(default_factory=lambda: {7001: (7.0, 70.0)})
    #: dcarec de los origenes (las columnas de LF11).
    retenciones: list[dict[str, Any]] = field(default_factory=list)
    #: (ide, emp, cod, tasa)
    ivas: list[tuple[int, int, str, float]] = field(default_factory=lambda: [
        (21, 1, "I21", 0.21), (10, 1, "I10", 0.10), (2121, 1, "I21NDED", 0.21),
    ])
    #: (ide, emp, cod, niv)
    cuentas_gasto: list[tuple[int, int, str, int]] = field(default_factory=lambda: [
        (629, 1, "6290000000", 5), (62, 1, "6290", 3), (400, 1, "4000000000", 5),
    ])
    #: (ide, emp, cod, hoja)
    analiticas_gasto: list[tuple[int, int, str, int]] = field(default_factory=lambda: [
        (190, 1, "GG.GEN", 1), (189, 1, "GG.PADRE", 0), (191, 1, "0404.MAT", 1),
    ])
    #: (ide, emp, cod, fecbaj, tipmov)
    productos: list[tuple[int, int, str, int, int]] = field(default_factory=lambda: [
        (300, 1, "MA9999", 0, 1), (301, 1, "XA9999", 20250101, 1),
    ])
    #: (ide, cod, numemp, fecbaj, caagascod, cuacomcod) de `auxpronat`
    naturalezas: list[tuple[int, str, int, int, str, str]] = field(default_factory=lambda: [
        (50, "MAT", 0, 0, "MAT", "6000000000"),
    ])
    #: (ide, emp, cod) de `cua`
    cuentas: list[tuple[int, int, str]] = field(default_factory=lambda: [(600, 1, "6000000000")])
    #: (ide, cod, cenide) de `caa`
    analiticas: list[tuple[int, str, int]] = field(default_factory=lambda: [(191, "0404.MAT", 80)])
    #: (ide, obride, cod, tip, tipdes, tipvis)
    partidas: list[tuple[int, int, str, int, int, int]] = field(default_factory=lambda: [
        (355, 4040, "01.01", 1, 0, 0),
    ])
    #: facturas ya dadas de alta (`dcf` + `con`)
    facturas: list[dict[str, Any]] = field(default_factory=list)
    #: (emp, prefijo) -> mayor numero de la serie
    max_cod: dict[tuple[int, str], int] = field(default_factory=lambda: {
        (1, "FR26/"): 41, (1, "FRGG26/"): 7,
    })
    siguiente_ide: dict[str, int] = field(default_factory=lambda: {
        "con": 10000, "dcfpro": 20000, "dcfrec": 300, "consii": 400, "dcaprodes": 500, "log": 600,
    })
    # --- Lo que toca la transaccion (T12-T14) ---
    #: filas insertadas por tabla
    insertadas: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    #: marcas de facturacion de la `dca` de cada origen
    dca: dict[int, dict[str, int]] = field(default_factory=lambda: {
        ide: {"estfac": 0, "fecfac": 0, "horfac": 0, "antestfac": 0} for ide in (800, 801, 810)
    })
    ctrpro: dict[int, dict[str, float]] = field(default_factory=lambda: {
        9901: {"docide": 900, "can": 10.0, "canser": 10.0, "canfac": 7.0},
        9902: {"docide": 900, "can": 5.0, "canser": 0.0, "canfac": 0.0},
    })
    ctr: dict[int, dict[str, int]] = field(default_factory=lambda: {900: {"estfac": 0}})
    #: cuantos `INSERT` de `con` chocan (IntegrityError) antes de dejar pasar
    colisiones: int = 0
    #: nombre de sentencia -> lo que hace "el escritorio" justo antes de ella
    antes_de: dict[str, Callable[[Mundo], None]] = field(default_factory=dict)

    def todas_las_facturas(self) -> list[dict[str, Any]]:
        """Las de partida y las insertadas (`dcf` con su `con`)."""
        cons = {c["ide"]: c for c in self.insertadas.get("con", [])}
        nuevas = [
            {**d, "cod": cons[d["ide"]]["cod"], "est": cons[d["ide"]]["est"]}
            for d in self.insertadas.get("dcf", []) if d["ide"] in cons
        ]
        return [*self.facturas, *nuevas]

    # --- Respuestas a las lecturas ------------------------------------------------

    def responder(self, nombre: str, p: list[Any]) -> list[tuple[Any, ...]]:
        return getattr(self, f"_r_{nombre}")(p)

    def _r_conest(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [fila for fila in self.conest if fila[0] in p]

    def _r_usuario(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [(p[0],)] if p[0] in self.usuarios else []

    def _r_obra(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [(o[0], o[1], o[2]) for o in self.obras if _c(o[2]) == _c(p[1])]

    def _r_obras(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[2:]}
        return [(o[0], o[2], o[3]) for o in self.obras if o[1] == p[1] and _c(o[2]) in cods]

    def _r_almacen_de_obra(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [(o[4], o[3]) for o in self.obras if o[0] == p[0]]

    def _r_almacenes(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [a for a in self.almacenes if a[1] == p[0]]

    def _r_proveedor(self, p: list[Any]) -> list[tuple[Any, ...]]:
        prv = self.proveedores.get(p[0])
        return [tuple(prv[c] for c in PROVEEDOR)] if prv else []

    def _r_proveedor_por_cif(self, p: list[Any]) -> list[tuple[Any, ...]]:
        _tip, emp, fecbaj, cif = p
        return [
            (v["ide"], v["cod"]) for v in self.proveedores.values()
            if v["emp"] == emp and v["fecbaj"] == fecbaj and v["cif"] == cif
        ]

    def _r_auxpag(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [self.auxpag[p[0]]] if p[0] in self.auxpag else []

    def _r_origenes(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[1:]}
        return [_origen(o) for o in self.origenes.values() if _c(o["cod"]) in cods]

    def _r_cabecera_de_origen(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cab = self.cabeceras.get(p[0])
        return [tuple(cab[c] for c in CABECERA_DE_ORIGEN)] if cab else []

    def _r_asientos(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [(cod,) for cod in p[2:] if (p[1], cod) in self.asientos]

    def _r_lineas_de_origenes(self, p: list[Any]) -> list[tuple[Any, ...]]:
        filas = sorted(
            (l for l in self.lineas if l["docide"] in p),
            key=lambda l: (l["docide"], l["pos"], l["ide"]),
        )
        return [tuple(l[c] for c in LINEA_DE_ORIGEN) for l in filas]

    def _r_facturadas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        docides = set(p[:-1])
        return [(l["ide"],) for l in self.lineas if l["docide"] in docides and l["ide"] in self.facturadas]

    def _r_anteriores(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [(ide, *self.anteriores[ide]) for ide in p if ide in self.anteriores]

    def _r_retenciones(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [tuple(r[c] for c in RETENCION_DE_ORIGEN) for r in self.retenciones if r["docide"] in p]

    def _r_ivas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[2:]}
        return [(i[0], i[2], i[3]) for i in self.ivas if i[1] == p[1] and _c(i[2]) in cods]

    def _r_cuentas_gasto(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[2:]}
        return [(c[0], c[2], c[3]) for c in self.cuentas_gasto if c[1] == p[1] and _c(c[2]) in cods]

    def _r_analiticas_gasto(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[2:]}
        return [(a[0], a[2], a[3]) for a in self.analiticas_gasto if a[1] == p[1] and _c(a[2]) in cods]

    def _r_productos(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[2:]}
        return [(x[0], x[2], x[3], x[4]) for x in self.productos if x[1] == p[0] and _c(x[2]) in cods]

    def _r_naturalezas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p}
        return [n for n in self.naturalezas if _c(n[1]) in cods]

    def _r_cuentas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[1:]}
        return [(c[0], c[2]) for c in self.cuentas if c[1] == p[0] and _c(c[2]) in cods]

    def _r_analiticas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p}
        return [a for a in self.analiticas if _c(a[1]) in cods]

    def _r_partidas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cods = {_c(c) for c in p[1:]}
        return [(x[0], x[2], x[3], x[4], x[5]) for x in self.partidas if x[1] == p[0] and _c(x[2]) in cods]

    def _r_referencia(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [
            (f["ide"], f["cod"], f["entide"], f["entref"], f["totbas"], f["totiva"], f["totdoc"],
             f["tot"], f["est"])
            for f in self.todas_las_facturas() if f["synckey"] == p[1]
        ]

    def _r_duplicadas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        _tip, cif, entref, rech = p
        return [
            (f["ide"], f["cod"]) for f in self.todas_las_facturas()
            if f["entcif"] == cif and f["entref"] == entref and f["est"] != rech
        ]

    def _r_ultimo_cod(self, p: list[Any]) -> list[tuple[Any, ...]]:
        _desde, emp, _tip, patron, _largo = p
        return [(self.max_cod.get((emp, patron[:-1])),)]


def _origen(o: dict[str, Any]) -> tuple[Any, ...]:
    return (o["ide"], o["cod"], o["emp"], o["est"], o["entide"], o["obride"], o["ctride"],
            o["docoritip"])


@dataclass
class AjustesFactura:
    """Los `Settings` que lee el caso de uso, abiertos para la previa."""

    sigrid_domain_write_enabled: bool = False
    sigrid_factura_write_enabled: bool = False
    sql_server_write_username: str | None = None
    sql_server_write_password: str | None = None
    allowed_write_databases: list[str] = field(default_factory=list)
    sigrid_factura_prefijos_referencia: list[str] = field(default_factory=lambda: ["FAC-"])
    sigrid_factura_max_lineas: int = 500
    sigrid_factura_productos_sin_origen: list[str] = field(default_factory=lambda: ["MA9999", "XA9999"])
    sigrid_factura_naturaleza_por_producto: dict[str, str] = field(
        default_factory=lambda: {"MA9999": "MAT", "XA9999": "MAT"}
    )
    sigrid_factura_ivas: list[str] = field(default_factory=lambda: ["I21", "I10", "I21NDED"])
    sigrid_factura_cuentas_gasto_prefijos: list[str] = field(default_factory=lambda: ["6"])
    sigrid_albaran_empresas_obra: list[int] = field(default_factory=lambda: [1])
    max_allowed_rows: int = 5000
    default_write_timeout_seconds: int = 30
    applock_timeout_ms: int = 10000
    domain_write_max_retries: int = 3


def ajustes_de_escritura(**cambios: Any) -> AjustesFactura:
    base = AjustesFactura(
        sigrid_domain_write_enabled=True, sigrid_factura_write_enabled=True,
        sql_server_write_username="usuario", sql_server_write_password="clave-de-prueba",
        allowed_write_databases=[BD],
    )
    for nombre, valor in cambios.items():
        setattr(base, nombre, valor)
    return base


@dataclass
class Repositorio:
    """`SqlRepository` doble: lecturas desde `Mundo`. La previa NO puede llamar
    a nada de escritura: si lo hace, el test falla aqui mismo."""

    mundo: Mundo = field(default_factory=Mundo)
    lecturas: list[tuple[str, list[Any]]] = field(default_factory=list)
    filas_completas: list[tuple[str, int]] = field(default_factory=list)
    peeks: list[str] = field(default_factory=list)
    transaccion: Callable[..., Any] | None = None
    #: dentro de la transaccion: (nombre, params) de cada sentencia, todos los intentos
    sentencias: list[tuple[str, list[Any]]] = field(default_factory=list)
    transacciones: list[dict[str, Any]] = field(default_factory=list)
    intentos: int = 0

    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        sql = normalizar(request.sql)
        assert sql.startswith("SELECT "), f"La previa solo lee: {request.sql}"
        nombre = NOMBRES.get(sql)
        assert nombre is not None, f"Sentencia desconocida: {request.sql}"
        assert request.database == BD
        params = list(request.parameters)
        self.lecturas.append((nombre, params))
        return [], self.mundo.responder(nombre, params), False

    def read_full_row(self, *, database: str, table: str, ide: int) -> tuple[list[str], tuple[Any, ...]] | None:
        assert table == "con", f"Solo se lee la con de la obra: {table}"
        self.filas_completas.append((table, ide))
        for obra in self.mundo.obras:
            if obra[0] == ide:
                return ["ide", "emp", "tip", "cod"], (obra[0], obra[1], 42, obra[2])
        return None

    def peek_next_ide(self, *, database: str, table: str) -> int:
        self.peeks.append(table)
        return self.mundo.siguiente_ide[table]

    def execute_write_command(self, request: Any) -> list[int]:
        raise AssertionError("sigrid/factura nunca usa sql/write")

    def run_in_write_transaction(self, **kwargs: Any) -> Any:
        if self.transaccion is None:
            raise AssertionError("La previa no abre transaccion")
        return self.transaccion(**kwargs)

    def nombres(self) -> list[str]:
        return [nombre for nombre, _p in self.lecturas]


def peticion(**cambios: Any) -> dict[str, Any]:
    """FR de mes con el albaran AC26/1 (una linea de 20 + 4,20 de IVA)."""
    base: dict[str, Any] = {
        "database": BD,
        "usu": "prueba",
        "referencia_externa": "FAC-1",
        "serie": "FR",
        "cif_proveedor": "B00000001",
        "numero_factura": "F-77",
        "fecha_factura": 20261015,
        "origenes": ["AC26/1"],
        "vencimientos": [{"fecha": 20261130, "importe": 24.2}],
        "total_base": 20.0,
        "total_iva": 4.2,
        "total_factura": 24.2,
    }
    base.update(cambios)
    return base


def linea_gg(**cambios: Any) -> dict[str, Any]:
    base = {"descripcion": "Gasto general", "cantidad": 1.0, "precio": 100.0, "iva": "I21",
            "cuenta": "6290000000", "analitica": "GG.GEN"}
    base.update(cambios)
    return base


def linea_fr(**cambios: Any) -> dict[str, Any]:
    base = {"descripcion": "Material", "cantidad": 2.0, "precio": 50.0, "iva": "I21",
            "producto": "MA9999"}
    base.update(cambios)
    return base


# =====================================================================================
# La transaccion (T12-T14): cursor sobre `Mundo` y bucle de reintentos
# =====================================================================================


class IntegrityError(Exception):
    """Como `pyodbc.IntegrityError`: el caso de uso la reconoce por su nombre."""


#: SQL exacto (IN normalizado) -> nombre de las sentencias que solo van dentro.
NOMBRES_TX: dict[str, str] = {
    normalizar(sql): nombre
    for sql, nombre in (
        (_F.bloquear_origenes([1])[0], "bloquear_origenes"),
        (_F.bloquear_lineas_de_origenes([1])[0], "bloquear_lineas"),
        (_F.reservar_cod(1, "FR26/", 5)[0], "reservar_cod"),
        *((getattr(_F, f"reservar_ide_{t}")()[0], f"reservar_ide_{t}")
          for t in ("con", "dcfpro", "dcfrec", "consii", "dcaprodes", "log")),
        (_F.bloquear_lineas_de_contrato([1])[0], "bloquear_contrato"),
        (_F.marcar_linea(1, 1)[0], "marcar_linea"),
        (_F.marcar_cabecera(1, 1, 1)[0], "marcar_cabecera"),
        (_F.marcar_estado(1, est_con=1, est_fac=1)[0], "marcar_estado"),
        (_F.sumar_facturado_contrato(1, 1)[0], "sumar_contrato"),
        (_F.actualizar_estfac_contrato(1, 1)[0], "estfac_contrato"),
        (_A.leer_sumas_contrato(1)[0], "sumas_contrato"),
        (_F.releer_con(1, "x")[0], "releer_con"),
        (_F.releer_dcf(1, "x")[0], "releer_dcf"),
        (_F.releer_dcfpro(1)[0], "releer_dcfpro"),
        (_F.releer_dcfrec(1)[0], "releer_dcfrec"),
        (_F.releer_pagos(1)[0], "releer_pagos"),
        (_F.releer_consii(1)[0], "releer_consii"),
        (_F.releer_dcaprodes(1)[0], "releer_dcaprodes"),
        (_F.releer_log(1)[0], "releer_log"),
        (_F.releer_linea_marcada(1, 1)[0], "releer_linea"),
        (_F.releer_cabecera_marcada(1, 1, 1)[0], "releer_cabecera"),
        (_F.releer_estado(1, est_fac=1)[0], "releer_estado"),
        (_F.releer_linea_de_contrato(1, 1)[0], "releer_contrato"),
        (_F.releer_estfac_contrato(1, 1)[0], "releer_estfac"),
    )
}
_INSERT = re.compile(r"^INSERT INTO dbo\.(\w+) \(([^)]*)\) VALUES ")


class _Transaccion:
    """Lo que contesta el cursor a las sentencias de dentro."""

    def __init__(self, mundo: Mundo) -> None:
        self.m = mundo

    def _filas(self, tabla: str) -> list[dict[str, Any]]:
        return self.m.insertadas.get(tabla, [])

    def bloquear_origenes(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [_origen(self.m.origenes[ide]) for ide in p if ide in self.m.origenes]

    def bloquear_lineas(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self.m.responder("lineas_de_origenes", p)

    def reservar_cod(self, p: list[Any]) -> list[tuple[Any, ...]]:
        desde, emp, _tip, patron, largo = p
        prefijo = patron[:-1]
        numeros = [
            int(c["cod"][desde - 1:]) for c in self._filas("con")
            if c["emp"] == emp and c["tip"] == 15 and c["cod"].startswith(prefijo) and len(c["cod"]) == largo
        ]
        maximo = self.m.max_cod.get((emp, prefijo))
        todos = [n for n in [maximo, *numeros] if n is not None]
        return [(max(todos) if todos else None,)]

    def _ide(self, tabla: str) -> list[tuple[Any, ...]]:
        insertados = [f["ide"] for f in self._filas(tabla)]
        return [(max([self.m.siguiente_ide[tabla] - 1, *insertados]) + 1,)]

    def bloquear_contrato(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return [(ide, self.m.ctrpro[ide]["canfac"]) for ide in p if ide in self.m.ctrpro]

    def marcar_linea(self, p: list[Any]) -> list[tuple[Any, ...]]:
        can, ide, cero = p
        for fila in self.m.lineas:
            if fila["ide"] == ide and fila["canfac"] == cero:
                fila["canfac"] = fila["canfac"] + can
        return []

    def marcar_cabecera(self, p: list[Any]) -> list[tuple[Any, ...]]:
        estfac, fecfac, horfac, antestfac, ide, antes = p
        marca = self.m.dca.get(ide)
        if marca is not None and marca["estfac"] == antes:
            marca.update(estfac=estfac, fecfac=fecfac, horfac=horfac, antestfac=antestfac)
        return []

    def marcar_estado(self, p: list[Any]) -> list[tuple[Any, ...]]:
        est, ide, tip, antes = p
        origen = self.m.origenes.get(ide)
        if origen is not None and tip == 14 and origen["est"] == antes:
            origen["est"] = est
        return []

    def sumar_contrato(self, p: list[Any]) -> list[tuple[Any, ...]]:
        can, ide = p
        self.m.ctrpro[ide]["canfac"] += can
        return []

    def estfac_contrato(self, p: list[Any]) -> list[tuple[Any, ...]]:
        estfac, ide = p
        self.m.ctr[ide]["estfac"] = estfac
        return []

    def sumas_contrato(self, p: list[Any]) -> list[tuple[Any, ...]]:
        lineas = [c for c in self.m.ctrpro.values() if c["docide"] == p[0]]
        return [(sum(c["can"] for c in lineas), sum(c["canser"] for c in lineas),
                 sum(c["canfac"] for c in lineas))]

    def _cuenta(self, n: int) -> list[tuple[Any, ...]]:
        return [(n,)]

    def releer_con(self, p: list[Any]) -> list[tuple[Any, ...]]:
        emp, tip, cod = p
        return self._cuenta(sum(1 for c in self._filas("con") if (c["emp"], c["tip"], c["cod"]) == (emp, tip, cod)))

    def releer_dcf(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._cuenta(sum(1 for d in self._filas("dcf") if (d["ide"], d["synckey"]) == tuple(p)))

    def _por(self, tabla: str, columna: str, valor: Any) -> list[tuple[Any, ...]]:
        return self._cuenta(sum(1 for f in self._filas(tabla) if f[columna] == valor))

    def releer_dcfpro(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._por("dcfpro", "docide", p[0])

    def releer_dcfrec(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._por("dcfrec", "docide", p[0])

    def releer_pagos(self, p: list[Any]) -> list[tuple[Any, ...]]:
        cons = {c["ide"]: c for c in self._filas("con")}
        return self._cuenta(sum(
            1 for pag in self._filas("pag")
            if pag["conide"] == p[0] and pag["ide"] in cons and cons[pag["ide"]]["tip"] == p[1]
        ))

    def releer_consii(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._por("consii", "conide", p[0])

    def releer_dcaprodes(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._cuenta(sum(
            1 for f in self._filas("dcaprodes") if f["docdeside"] == p[0] and f["docdestip"] == p[1]
        ))

    def releer_log(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._por("log", "ide", p[0])

    def releer_linea(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._cuenta(sum(1 for f in self.m.lineas if f["ide"] == p[0] and f["canfac"] == p[1]))

    def releer_cabecera(self, p: list[Any]) -> list[tuple[Any, ...]]:
        ide, estfac, fecfac, horfac, antestfac = p
        marca = self.m.dca.get(ide)
        return self._cuenta(int(marca == {"estfac": estfac, "fecfac": fecfac, "horfac": horfac,
                                          "antestfac": antestfac}))

    def releer_estado(self, p: list[Any]) -> list[tuple[Any, ...]]:
        ide, _tip, est = p
        return self._cuenta(int(ide in self.m.origenes and self.m.origenes[ide]["est"] == est))

    def releer_contrato(self, p: list[Any]) -> list[tuple[Any, ...]]:
        ide, canfac, margen = p
        return self._cuenta(int(abs(self.m.ctrpro[ide]["canfac"] - canfac) < margen))

    def releer_estfac(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return self._cuenta(int(self.m.ctr[p[0]]["estfac"] == p[1]))


class Cursor:
    """Cursor doble: lee del `Mundo`, inserta y marca en el. Graba cada sentencia."""

    def __init__(self, repo: Repositorio) -> None:
        self.repo = repo
        self.connection = type("Conexion", (), {"timeout": None})()
        self._resultado: list[tuple[Any, ...]] = []

    def execute(self, sql: str, *params: Any) -> None:
        mundo, p = self.repo.mundo, list(params)
        insert = _INSERT.match(sql)
        if insert:
            nombre = f"insertar_{insert.group(1)}"
        else:
            nombre = NOMBRES.get(normalizar(sql)) or NOMBRES_TX.get(normalizar(sql), "")
            assert nombre, f"Sentencia desconocida dentro de la transaccion: {sql}"
        self.repo.sentencias.append((nombre, p))
        if nombre in mundo.antes_de:
            mundo.antes_de.pop(nombre)(mundo)
        if insert:
            tabla, columnas = insert.group(1), insert.group(2).split(", ")
            assert len(columnas) == len(p) and "?" not in p
            if tabla == "con" and mundo.colisiones:
                mundo.colisiones -= 1
                raise IntegrityError("clave duplicada en con_emptipcod")
            mundo.insertadas.setdefault(tabla, []).append(dict(zip(columnas, p)))
            self._resultado = []
        elif nombre in NOMBRES.values():
            self._resultado = mundo.responder(nombre, p)
        elif nombre.startswith("reservar_ide_"):
            self._resultado = _Transaccion(mundo)._ide(nombre.removeprefix("reservar_ide_"))
        else:
            self._resultado = getattr(_Transaccion(mundo), nombre)(p)

    def fetchall(self) -> list[tuple[Any, ...]]:
        return list(self._resultado)

    def fetchone(self) -> tuple[Any, ...] | None:
        return self._resultado[0] if self._resultado else None


def con_transaccion(repo: Repositorio) -> Repositorio:
    """Arma `run_in_write_transaction` como el repositorio real: cursor nuevo por
    intento, ROLLBACK (el `Mundo` vuelve a su copia) ante cualquier excepcion y
    reintento ante `IntegrityError` hasta `max_retries`."""
    import copy

    def transaccion(**kwargs: Any) -> Any:
        repo.transacciones.append({k: v for k, v in kwargs.items() if k != "work"})
        intento = 0
        while True:
            intento += 1
            copia = copy.deepcopy({k: v for k, v in vars(repo.mundo).items() if k not in ("antes_de", "colisiones")})
            repo.intentos += 1
            try:
                return kwargs["work"](Cursor(repo))
            except Exception as exc:
                for clave_, valor in copia.items():
                    setattr(repo.mundo, clave_, valor)
                if isinstance(exc, IntegrityError) and intento <= kwargs["max_retries"]:
                    continue
                raise

    repo.transaccion = transaccion
    return repo
