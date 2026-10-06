# tests/f009_dobles.py
"""
F-009 · dobles y datos de mentira del caso de uso del modo extendido de
`sigrid/albaran` (lote C). No es un fichero de tests: lo importan
`test_f009_use_case.py` y `test_f009_equivalencia.py`.

Sin red y sin base de datos. El repositorio doble reconoce cada sentencia por
su SQL EXACTO (el de `AlbaranCompraStatements`; las listas `IN (?, ...)` se
normalizan a un marcador): una sentencia que no sea del constructor hace fallar
el test. Graba nombre, SQL y parámetros de cada lectura y de cada sentencia de
la transacción, y reproduce el bucle de reintentos de
`run_in_write_transaction` (cursor nuevo por intento, repetir ante
`IntegrityError` hasta `max_retries`), como el doble de F-006. El cursor
contesta las relecturas (E12) con lo que de verdad se insertó en ESE intento.

Datos sintéticos: ni CIF, ni obras, ni identificadores reales.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

from application.use_cases.albaran_compra_statements import (
    CTRPRODES_COLUMNAS,
    LOG_COLUMNAS,
    MOV_COLUMNAS,
    AlbaranCompraStatements,
)

BD = "ruesma"
OBRA = 5000
CTR = 300
ENTIDE = 77
PLANTILLA_CABECERA = 15950
#: 08:15:30 UTC del 6 de octubre de 2026 = 10:15:30 en Madrid (CEST).
AHORA = datetime(2026, 10, 6, 8, 15, 30, tzinfo=timezone.utc)

_S = AlbaranCompraStatements(database=BD)
_UNO = ["x"]

#: SQL exacto (IN normalizado) -> nombre corto de la sentencia.
NOMBRES: dict[str, str] = {
    _S.leer_obra("x")[0]: "obra",
    _S.leer_plantilla_cabecera(1, 1)[0]: "plantilla_por_entide",
    _S.leer_plantilla_cabecera_por_cif(1, "x")[0]: "plantilla_por_cif",
    _S.buscar_referencia("x")[0]: "referencia",
    _S.leer_lineas_de_albaran(1)[0]: "lineas_del_existente",
    _S.leer_estado_inicial()[0]: "conest",
    _S.leer_usuario("x")[0]: "usuario",
    _S.ultimo_cod(1, "x")[0]: "ultimo_cod",
    _S.leer_partidas(1, _UNO)[0]: "partidas",
    _S.leer_productos(1, _UNO)[0]: "productos",
    _S.leer_tipmov([1])[0]: "tipmov",
    _S.leer_plantilla_linea(1)[0]: "plantilla_linea",
    _S.leer_plantilla_linea_del_proveedor(1, 1)[0]: "plantilla_linea_proveedor",
    _S.leer_tasas_iva([1])[0]: "iva",
    _S.leer_almacen_de_obra(1)[0]: "almacen_de_obra",
    _S.leer_almacenes(1, [])[0]: "almacenes",
    _S.leer_almacenes(1, [1])[0]: "almacenes_y_resueltos",
    _S.leer_balance(1, 1)[0]: "balance",
    _S.leer_naturalezas(_UNO)[0]: "naturalezas",
    _S.leer_analiticas(_UNO)[0]: "analiticas",
    _S.leer_cuentas(1, _UNO)[0]: "cuentas",
    _S.reservar_cod(1, "x")[0]: "reservar_cod",
    _S.reservar_ide_con()[0]: "ide_con",
    _S.reservar_ide_dcapro()[0]: "ide_dcapro",
    _S.reservar_ide_ctrprodes()[0]: "ide_ctrprodes",
    _S.reservar_ide_mov()[0]: "ide_mov",
    _S.reservar_balance(1, 1)[0]: "balance_bajo_bloqueo",
    _S.reservar_ide_log()[0]: "ide_log",
    _S.insertar_ctrprodes(dict.fromkeys(CTRPRODES_COLUMNAS))[0]: "insert_ctrprodes",
    _S.insertar_mov(dict.fromkeys(MOV_COLUMNAS))[0]: "insert_mov",
    _S.insertar_log(dict.fromkeys(LOG_COLUMNAS))[0]: "insert_log",
    _S.sumar_servido(1, 1.0)[0]: "servido",
    _S.leer_sumas_contrato(1)[0]: "sumas_contrato",
    _S.actualizar_estados_contrato(1, 0, 0)[0]: "estados_contrato",
    _S.releer_con(1, "x")[0]: "releer_con",
    _S.releer_dca(1)[0]: "releer_dca",
    _S.releer_dcapro(1)[0]: "releer_dcapro",
    _S.releer_ctrprodes(1)[0]: "releer_ctrprodes",
    _S.releer_mov(1)[0]: "releer_mov",
    _S.releer_log(1)[0]: "releer_log",
}

_IN = re.compile(r"IN \(\?(?:, \?)*\)")


def nombre(sql: str) -> str:
    """Nombre corto de una sentencia del constructor, o `AssertionError`. Los
    `INSERT` de las tablas clonadas se reconocen por su cabecera; su SQL
    completo lo fija carácter a carácter `test_f009_statements.py`."""
    normalizado = _IN.sub("IN (?)", sql)
    if normalizado in NOMBRES:
        return NOMBRES[normalizado]
    for tabla in ("dcapro", "dca", "con"):
        if sql.startswith(f"INSERT INTO dbo.{tabla} ([") and sql == _S.insertar_clonada(
            tabla, dict.fromkeys(_columnas_del_insert(sql))
        )[0]:
            return f"insert_{tabla}"
    raise AssertionError(f"sentencia inesperada: {sql}")


def _columnas_del_insert(sql: str) -> list[str]:
    cabecera = sql[sql.index("(") + 1 : sql.index(")")]
    return [columna.strip()[1:-1] for columna in cabecera.split(",")]


# --- El ERP de mentira -------------------------------------------------------------


def ctr() -> dict[str, Any]:
    return {
        "ide": CTR, "obride": OBRA, "entide": ENTIDE, "entcod": "P0077",
        "entres": "PROVEEDOR PRUEBA SL", "entcif": "B12345678", "almide": 70,
        "cenide": 80, "estser": 0, "estfac": 0,
    }


def ctrpro() -> list[dict[str, Any]]:
    base = {"docide": CTR, "tex": "", "dto": "", "ivaide": 3, "cod2": "", "dncide": 0,
            "dncproide": 0, "canfac": 0.0}
    return [
        {**base, "ide": 9001, "pos": 64, "proide": 55, "pre": 10.5, "tar": 12.0,
         "dto": "10+2,5", "can": 100.0, "canser": 20.0, "tot": 1050.0, "ivacuo": 220.5,
         "res": "Hormigon HA-25", "unimed": "m3", "almide": 70, "cenide": 80,
         "caaide": 90, "paride": 5, "cod2": "PLAN-7", "dncide": 41, "dncproide": 42},
        {**base, "ide": 9002, "pos": 128, "proide": 56, "pre": 3.0, "tar": 3.0,
         "can": 10.0, "canser": 5.0, "tot": 30.0, "ivacuo": 6.3, "res": "Arena",
         "unimed": "t", "almide": None, "cenide": None, "caaide": 91, "paride": 0},
        {**base, "ide": 9003, "pos": 192, "proide": 57, "pre": 100.0, "tar": 100.0,
         "can": 1.0, "canser": 0.0, "tot": 100.0, "ivacuo": 21.0, "res": "Servicio",
         "unimed": "ud", "almide": 71, "cenide": 81, "caaide": 92, "paride": 0},
    ]


def con_plantilla() -> dict[str, Any]:
    return {"ide": PLANTILLA_CABECERA, "emp": 1, "tip": 14, "cod": "AC26/15950",
            "res": "PLANTILLA", "fec": 20260601, "est": 3, "usu": "viejo"}


def dca_plantilla() -> dict[str, Any]:
    return {
        "ide": PLANTILLA_CABECERA, "fecdoc": 20260601, "hor": 101010, "entref": "vieja",
        "eioide": 3, "entide": ENTIDE, "entcod": "P0077", "entres": "PROVEEDOR PRUEBA SL",
        "entcif": "B12345678", "ctride": 999, "obride": 1, "almide": 1, "cenide": 1,
        "empide": 1, "pagide": 12, "efeide": 13, "totbas": 5.0, "totiva": 1.0,
        "totdoc": 6.0, "impdes": 1.0, "estser": 1, "estfac": 1, "synckey": "ALB-viejo",
        "bancue": "ES12", "cpacue1": "ES34",
    }


def plantilla_dcapro(proide: int, **extra: Any) -> dict[str, Any]:
    """Una `dcapro` de otro albarán del producto, con lo que no se debe arrastrar."""
    return {
        "ide": 4000 + proide, "docide": 3333, "pos": 640, "proide": proide, "can": 99.0,
        "pre": 99.0, "tar": 99.0, "dto": "5", "tot": 9801.0, "ivaide": 3, "ivacuo": 1.0,
        "res": "ajena", "unimed": "kg", "almide": 1, "cenide": 1, "obride": 1,
        "caaide": 1, "paride": 1, "natide": 999, "cueide": 888, "prepma": 77.7,
        "refent": "otra", "docoritip": 44, "docoricod": "CTR/OTRO", "docoriide": 1,
        "linoriide": 1, "canoriori": 5.0, "imporiori": 5.0, "canser": 1, "canfac": 1,
        "cod2": "AJENO", "dncide": 9, "dncproide": 9, "med": b"m", "tex": "ajeno",
        **extra,
    }


def lecturas_base() -> dict[str, Any]:
    """Respuesta de cada lectura: lista de filas o función de los parámetros."""
    plantillas = {55: plantilla_dcapro(55), 56: plantilla_dcapro(56), 66: plantilla_dcapro(66),
                  67: plantilla_dcapro(67, ivaide=4)}
    del_proveedor = {(66, ENTIDE): plantilla_dcapro(66, ide=4166, ivaide=3)}
    balances = {(55, 70): (10.0, 9.0), (66, 70): (4.0, 2.0)}
    return {
        "obra": [(OBRA, 1, "0404")],
        "plantilla_por_entide": [(PLANTILLA_CABECERA,)],
        "plantilla_por_cif": [(PLANTILLA_CABECERA,)],
        "referencia": [],
        "lineas_del_existente": [],
        "conest": [(1,)],
        "usuario": [("prueba",)],
        "ultimo_cod": [(15952,)],
        "partidas": [
            (5, "01.01", 1, 0, 0), (6, "01.02", 1, 0, 1), (7, "02", 0, 0, 0),
            (8, "03", 1, 0, 0), (9, "03", 1, 0, 1), (10, "04", 1, 1, 0), (11, "05", 1, 0, 2),
        ],
        "productos": [
            (66, "MA9999", 0, 1), (67, "QA9999", 0, 1), (68, "XA9999", 0, 1),
        ],
        "tipmov": [(55, 1), (56, 1), (57, 0)],
        "plantilla_linea": lambda p: [plantillas[p[0]]] if p[0] in plantillas else [],
        "plantilla_linea_proveedor": (
            lambda p: [del_proveedor[(p[0], p[1])]] if (p[0], p[1]) in del_proveedor else []
        ),
        "iva": [(3, 0.21), (4, 0.10)],
        "almacen_de_obra": [(72, 82)],
        "almacenes": [(73, OBRA, 83)],
        "balance": lambda p: [balances[(p[0], p[1])]] if (p[0], p[1]) in balances else [],
        "naturalezas": [
            (501, "MA99", 0, 0, "MOD.CDSB37", "6000001"),
            (502, "QA99", 1, 0, "MOD.CDQA12", "6000002"),
            (503, "XA99", 0, 0, "CDXA01", "6000003"),
        ],
        "cuentas": [(601, "6000001"), (602, "6000002"), (603, "6000003")],
        "analiticas": [
            (701, "0404.CDSB37", 80), (702, "0404.CDQA12", 80), (703, "0404.CDXA01", 80),
            (799, "0404.CDSB37", 81),
        ],
    }


PEEK = {"con": 2900001, "dcapro": 8000001, "ctrprodes": 400001, "mov": 9000001, "log": 8488889}

RESERVAS: dict[str, Any] = {
    "reservar_cod": (15952,),
    "ide_con": (2900011,),
    "ide_dcapro": (8000011,),
    "ide_ctrprodes": (400011,),
    "ide_mov": (9000011,),
    "ide_log": (8488899,),
    "sumas_contrato": (111.0, 33.0, 0.0),
}


class IntegrityError(Exception):
    """Como `pyodbc.IntegrityError`: el caso de uso la reconoce por su nombre."""


@dataclass
class SettingsDoble:
    sigrid_domain_write_enabled: bool = True
    sigrid_albaran_write_enabled: bool = True
    sql_server_write_username: str | None = "usuario_de_mentira"
    sql_server_write_password: str | None = "no-es-una-credencial"
    allowed_write_databases: list[str] = field(default_factory=lambda: [BD])
    sigrid_albaran_prefijos_referencia: list[str] = field(default_factory=lambda: ["ALB-"])
    sigrid_albaran_productos_sin_contrato: list[str] = field(
        default_factory=lambda: ["MA9999", "QA9999", "XA9999"]
    )
    sigrid_albaran_empresas_obra: list[int] = field(default_factory=lambda: [1])
    sigrid_albaran_max_lineas: int = 100
    sigrid_albaran_naturaleza_por_producto: dict[str, str] = field(
        default_factory=lambda: {"MA9999": "MA99", "QA9999": "QA99", "XA9999": "XA99"}
    )
    sigrid_albaran_empide: int = 2425207
    max_allowed_rows: int = 1000
    applock_timeout_ms: int = 10000
    domain_write_max_retries: int = 3
    default_write_timeout_seconds: int = 30


class CursorDoble:
    """Un intento de transacción. `reservas[clave]` es una tupla o una función
    `(intento, parametros) -> tupla | None`; `filas_en_transaccion[clave]`, lo
    mismo para `fetchall`."""

    def __init__(self, repo: RepositorioDoble, intento: int) -> None:
        self.repo = repo
        self.intento = intento
        self.insertadas: dict[str, int] = {}
        self._ultima = ("", [])
        self.connection = SimpleNamespace(timeout=None)

    def execute(self, sql: str, *params: Any) -> None:
        clave = nombre(sql)
        self.repo.en_transaccion.append((self.intento, clave, sql, list(params)))
        self._ultima = (clave, list(params))
        fallo = self.repo.fallos.get(clave)
        if fallo is not None:
            excepcion = fallo(self.intento) if callable(fallo) else fallo
            if excepcion is not None:
                raise excepcion
        if clave.startswith("insert_"):
            tabla = clave.removeprefix("insert_")
            self.insertadas[tabla] = self.insertadas.get(tabla, 0) + 1

    def fetchone(self) -> tuple[Any, ...] | None:
        clave, params = self._ultima
        if clave in self.repo.forzar:
            return self.repo.forzar[clave]
        if clave.startswith("releer_"):
            return (self.insertadas.get(clave.removeprefix("releer_"), 0),)
        respuesta = self.repo.reservas[clave]
        return respuesta(self.intento, params) if callable(respuesta) else respuesta

    def fetchall(self) -> list[tuple[Any, ...]]:
        clave, params = self._ultima
        respuesta = self.repo.filas_en_transaccion.get(clave, [])
        return list(respuesta(self.intento, params) if callable(respuesta) else respuesta)


class RepositorioDoble:
    def __init__(
        self,
        lecturas: dict[str, Any] | None = None,
        *,
        reservas: dict[str, Any] | None = None,
        filas_en_transaccion: dict[str, Any] | None = None,
        fallos: dict[str, Any] | None = None,
        forzar: dict[str, tuple[Any, ...]] | None = None,
        contratos: list[dict[str, Any]] | None = None,
        filas: dict[tuple[str, int], dict[str, Any] | None] | None = None,
        ctrpro_filas: list[dict[str, Any]] | None = None,
        truncar_en: str | None = None,
    ) -> None:
        self.lecturas = {**lecturas_base(), **(lecturas or {})}
        self.reservas = {
            **RESERVAS,
            "balance_bajo_bloqueo": lambda _intento, p: self._balance(p),
            **(reservas or {}),
        }
        self.filas_en_transaccion = filas_en_transaccion or {"referencia": []}
        self.fallos = fallos or {}
        self.forzar = forzar or {}
        self.contratos = (
            contratos if contratos is not None else [{"ide": CTR, "obride": OBRA}]
        )
        self.filas: dict[tuple[str, int], dict[str, Any] | None] = {
            ("ctr", CTR): ctr(),
            ("con", PLANTILLA_CABECERA): con_plantilla(),
            ("dca", PLANTILLA_CABECERA): dca_plantilla(),
            **(filas or {}),
        }
        self.ctrpro_filas = ctrpro_filas if ctrpro_filas is not None else ctrpro()
        self.truncar_en = truncar_en
        self.llamadas: list[tuple[str, Any]] = []
        self.transacciones: list[dict[str, Any]] = []
        self.cursores: list[CursorDoble] = []
        self.en_transaccion: list[tuple[int, str, str, list[Any]]] = []

    def _balance(self, params: list[Any]) -> tuple[Any, ...] | None:
        filas = self._responder("balance", params)
        return filas[0] if filas else None

    def _responder(self, clave: str, params: list[Any]) -> list[Any]:
        respuesta = self.lecturas[clave]
        return list(respuesta(params) if callable(respuesta) else respuesta)

    # --- lecturas (credenciales de lectura) ---------------------------------------
    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        assert request.database == BD
        clave = nombre(request.sql)
        self.llamadas.append(("leer", (clave, list(request.parameters), request.max_rows)))
        filas = self._responder(clave, list(request.parameters))
        if filas and isinstance(filas[0], dict):
            columnas = list(filas[0].keys())
            return columnas, [tuple(f[c] for c in columnas) for f in filas], False
        return [], [tuple(f) for f in filas], clave == self.truncar_en

    def locate_contract(self, **kwargs: Any) -> tuple[list[str], list[tuple[Any, ...]]]:
        self.llamadas.append(("locate_contract", kwargs))
        columnas = ["ide", "obride", "cod_contrato", "entcif"]
        return columnas, [
            (c["ide"], c["obride"], kwargs["cod_contrato"], kwargs["cif_proveedor"])
            for c in self.contratos
        ]

    def read_full_row(self, *, database: str, table: str, ide: int):
        assert database == BD
        self.llamadas.append(("read_full_row", (table, ide)))
        fila = self.filas.get((table, ide))
        if fila is None:
            return None
        return list(fila.keys()), tuple(fila.values())

    def read_rows_by(self, *, database: str, table: str, where_column: str, where_value: Any,
                     order_by: str | None = None):
        assert database == BD
        self.llamadas.append(("read_rows_by", (table, where_column, where_value, order_by)))
        filas = self.ctrpro_filas
        columnas = list(filas[0].keys()) if filas else []
        return columnas, [tuple(f.get(c) for c in columnas) for f in filas]

    def peek_next_ide(self, *, database: str, table: str) -> int:
        assert database == BD
        self.llamadas.append(("peek", table))
        return PEEK[table]

    # --- escritura -------------------------------------------------------------------
    def run_in_write_transaction(
        self,
        *,
        database: str,
        timeout_seconds: int,
        applock_resources: list[str],
        applock_timeout_ms: int,
        max_retries: int,
        work: Callable[[Any], Any],
    ) -> Any:
        self.llamadas.append(("transaccion", database))
        self.transacciones.append(
            {
                "database": database,
                "timeout_seconds": timeout_seconds,
                "applock_resources": list(applock_resources),
                "applock_timeout_ms": applock_timeout_ms,
                "max_retries": max_retries,
            }
        )
        intento = 0
        while True:
            intento += 1
            cursor = CursorDoble(self, intento)
            self.cursores.append(cursor)
            try:
                return work(cursor)
            except IntegrityError:
                if intento > max_retries:
                    raise
                continue

    # --- consultas para los tests ---------------------------------------------------
    def lecturas_hechas(self) -> list[str]:
        return [datos[0] for tipo, datos in self.llamadas if tipo == "leer"]

    def parametros_de(self, clave: str) -> list[list[Any]]:
        return [datos[1] for tipo, datos in self.llamadas if tipo == "leer" and datos[0] == clave]

    def sentencias(self, intento: int | None = None) -> list[str]:
        return [c for i, c, _sql, _p in self.en_transaccion if intento is None or i == intento]

    def parametros_en_transaccion(self, clave: str, intento: int | None = None) -> list[list[Any]]:
        return [
            p for i, c, _sql, p in self.en_transaccion
            if c == clave and (intento is None or i == intento)
        ]
