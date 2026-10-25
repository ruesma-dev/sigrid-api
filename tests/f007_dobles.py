# tests/f007_dobles.py
"""
F-007 · dobles del caso de uso de `sigrid/proforma`. No es un fichero de
tests: lo importan `test_f007_use_case.py` y `test_f007_transaccion.py`.

Extiende el doble de F-009 (`tests/f009_dobles.py`, que no se toca): el
repositorio y el cursor reconocen ademas LP1-LP6 por su SQL EXACTO, dentro y
fuera de la transaccion; cualquier otra sentencia hace fallar el test. El ERP
de mentira es la obra 0719 de `tests/fixtures/f007_obra0719.json` (M29): sus
contratos, lineas de contrato, proformas registradas y lineas de la
proforma ya registrada, con proveedores y CIF ficticios.

Sin red y sin base de datos.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import f009_dobles
from f009_dobles import (
    BD,
    ENTIDE,
    CursorDoble,
    IntegrityError,
    RepositorioDoble,
    SettingsDoble,
    ctr,
    plantilla_dcapro,
)

from application.use_cases.proforma_statements import (
    LP4_LINEAS_DE_CONTRATOS,
    ProformaStatements,
)

FIXTURE = Path(__file__).parent / "fixtures" / "f007_obra0719.json"
DATOS: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))

OBRA_0719 = DATOS["obra"]["ide"]
#: El producto de los contratos de la 0719 y el de la lista de R4 (sin contrato).
SM1004, SM1026, SM9999 = 610004, 610026, 690099
#: `pro.tipmov` 0: subcontratas sin `mov` (M34: `SM370001`; aqui todos).
_TIPMOV = 0

_P = ProformaStatements(database=BD)
_IN = re.compile(r"IN \(\?(?:, \?)*\)")

#: SQL exacto (IN normalizado) -> nombre corto, las de F-007.
NOMBRES_F007: dict[str, str] = {
    _P.leer_proformas_del_contrato(1)[0]: "lp1_proformas",
    _P.leer_anterior(1, 1)[0]: "lp2_anterior",
    _P.leer_contratos_de_obra(1)[0]: "lp3_contratos",
    LP4_LINEAS_DE_CONTRATOS.format(marcadores="(?)"): "lp4_lineas",
    _P.buscar_referencia("x")[0]: "lp5_referencia",
    _P.leer_lineas_de_proforma(1)[0]: "lp6_lineas",
}


def nombre(sql: str) -> str:
    """Las de F-007 y, si no, las de F-009 (o `AssertionError`)."""
    normalizado = _IN.sub("IN (?)", sql)
    if normalizado in NOMBRES_F007:
        return NOMBRES_F007[normalizado]
    return f009_dobles.nombre(sql)


# --- La obra 0719 -------------------------------------------------------------------


def ctride_de(cod: str) -> int:
    return next(c["ide"] for c in DATOS["contratos"] if c["cod"] == cod)


def contrato_de(cod: str) -> dict[str, Any]:
    return next(c for c in DATOS["contratos"] if c["cod"] == cod)


def ctr_0719(cod: str) -> dict[str, Any]:
    """La fila `ctr` completa (la de F-009 con la identidad del contrato)."""
    c = contrato_de(cod)
    return {**ctr(), "ide": c["ide"], "obride": OBRA_0719, "entcif": c["entcif"],
            "entres": c["entres"]}


def ctrpro_0719(cod: str) -> list[dict[str, Any]]:
    """Las `ctrpro` completas del contrato (las lee el nucleo por `read_rows_by`)."""
    anterior = DATOS["anterior"].get(cod, {})
    filas = []
    for pos, linea in enumerate(DATOS["ctrpro"][cod], start=1):
        filas.append({
            "ide": linea["ide"], "docide": linea["docide"], "pos": 64 * pos,
            "proide": linea["proide"], "pre": float(linea["pre"]), "tar": float(linea["pre"]),
            "dto": "", "can": float(linea["can"]), "canser": float(anterior.get(str(linea["ide"]), 0)),
            "canfac": 0.0, "tot": float(linea["tot"]), "ivacuo": round(linea["tot"] * 0.21, 2),
            "ivaide": 3, "res": f"LINEA {linea['partida']}", "unimed": linea["unimed"],
            "almide": 70, "cenide": 80, "caaide": 90, "paride": linea["paride"], "tex": "",
            "cod2": "", "dncide": 0, "dncproide": 0,
        })
    return filas


def _lp4(params: list[Any]) -> list[tuple[Any, ...]]:
    columnas = ("ide", "docide", "paride", "partida", "can", "pre", "tot", "unimed", "proide",
                "producto")
    return [
        tuple(linea[c] for c in columnas)
        for lineas in DATOS["ctrpro"].values() for linea in lineas if linea["docide"] in params
    ]


def _lp1(params: list[Any]) -> list[tuple[Any, ...]]:
    cod = next((c["cod"] for c in DATOS["contratos"] if c["ide"] == params[1]), None)
    columnas = ("ide", "cod", "fec", "entref", "totbas", "docoritip")
    return [tuple(p[c] for c in columnas) for p in DATOS["proformas"].get(cod, [])]


def _lp2(params: list[Any]) -> list[tuple[Any, ...]]:
    cod = next((c["cod"] for c in DATOS["contratos"] if c["ide"] == params[1]), None)
    return [(int(ide), can) for ide, can in DATOS["anterior"].get(cod, {}).items()]


def _lp6(params: list[Any]) -> list[tuple[Any, ...]]:
    cods = {p["ide"]: p["cod"] for lista in DATOS["proformas"].values() for p in lista}
    columnas = ("ide", "linoriide", "producto", "can", "pre", "tot")
    return [tuple(l[c] for c in columnas) for l in DATOS["existentes"].get(cods.get(params[0]), [])]


def lecturas_0719() -> dict[str, Any]:
    plantillas = {
        SM1004: plantilla_dcapro(SM1004),
        SM1026: plantilla_dcapro(SM1026),
        SM9999: plantilla_dcapro(SM9999),
    }
    # La del MISMO proveedor (L8b): de ella salen naturaleza, cuenta y analitica (R17).
    del_proveedor = {
        (SM1004, ENTIDE): plantilla_dcapro(SM1004, ide=5004, natide=4101, cueide=4102,
                                           caaide=4103, ivaide=4),
        (SM1026, ENTIDE): plantilla_dcapro(SM1026, ide=5026, natide=4201, cueide=4202,
                                           caaide=4203, ivaide=4),
    }
    return {
        "obra": [(OBRA_0719, 1, "0719")],
        "lp3_contratos": [
            (c["ide"], c["cod"], c["fec"], c["entcif"], c["entres"], c["nlin"])
            for c in DATOS["contratos"]
        ],
        "lp4_lineas": _lp4,
        "lp5_referencia": [],
        "lp1_proformas": _lp1,
        "lp2_anterior": _lp2,
        "lp6_lineas": _lp6,
        "ultimo_cod": [(1281,)],
        "partidas": [(p["ide"], p["cod"], 1, 0, 0) for p in DATOS["partidas"]],
        "productos": [
            (SM1004, "SM1004", 0, _TIPMOV), (SM1026, "SM1026", 0, _TIPMOV),
            (SM9999, "SM9999", 0, _TIPMOV), (690098, "SM7777", 0, _TIPMOV),
        ],
        "tipmov": [(SM1004, _TIPMOV), (SM1026, _TIPMOV)],
        "plantilla_linea": lambda p: [plantillas[p[0]]] if p[0] in plantillas else [],
        "plantilla_linea_proveedor": (
            lambda p: [del_proveedor[(p[0], p[1])]] if (p[0], p[1]) in del_proveedor else []
        ),
        "almacen_de_obra": [(72, 82)],
        "naturalezas": [(501, "SM99", 0, 0, "MOD.CDSB37", "6000001")],
        "cuentas": [(601, "6000001")],
        "analiticas": [(701, "0719.CDSB37", 82), (702, "0719.CDSB37", 80)],
    }


#: Reservas de la transaccion: la serie `PROF26/` va por la 1281 (M1: `PROF26/01282`).
RESERVAS_0719: dict[str, Any] = {"reservar_cod": (1281,)}


@dataclass
class SettingsProforma(SettingsDoble):
    """Las de F-009 mas las cinco de R4, abiertas para los tests."""

    sigrid_proforma_write_enabled: bool = True
    sigrid_proforma_prefijos_referencia: list[str] = field(default_factory=lambda: ["PRF-"])
    sigrid_proforma_productos_sin_contrato: list[str] = field(default_factory=lambda: ["SM9999"])
    sigrid_proforma_naturaleza_por_producto: dict[str, str] = field(
        default_factory=lambda: {"SM9999": "SM99"}
    )
    sigrid_proforma_max_lineas: int = 500


class CursorProforma(CursorDoble):
    """El cursor de F-009 que reconoce tambien LP1-LP6 (R28: LP1 dentro)."""

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


class RepositorioProforma(RepositorioDoble):
    """El repositorio de F-009 con la obra 0719 y el contrato `cod`."""

    def __init__(
        self,
        cod: str = "CTSB26/0472",
        lecturas: dict[str, Any] | None = None,
        *,
        reservas: dict[str, Any] | None = None,
        filas: dict[tuple[str, int], dict[str, Any] | None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            {**lecturas_0719(), **(lecturas or {})},
            reservas={**RESERVAS_0719, **(reservas or {})},
            contratos=[{"ide": ctride_de(cod), "obride": OBRA_0719}],
            filas={("ctr", ctride_de(cod)): ctr_0719(cod), **(filas or {})},
            ctrpro_filas=ctrpro_0719(cod),
            **kwargs,
        )

    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        assert request.database == BD
        clave = nombre(request.sql)
        self.llamadas.append(("leer", (clave, list(request.parameters), request.max_rows)))
        filas = self._responder(clave, list(request.parameters))
        if filas and isinstance(filas[0], dict):
            columnas = list(filas[0].keys())
            return columnas, [tuple(f[c] for c in columnas) for f in filas], False
        return [], [tuple(f) for f in filas], clave == self.truncar_en

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
        self.transacciones.append({
            "database": database, "timeout_seconds": timeout_seconds,
            "applock_resources": list(applock_resources),
            "applock_timeout_ms": applock_timeout_ms, "max_retries": max_retries,
        })
        intento = 0
        while True:
            intento += 1
            cursor = CursorProforma(self, intento)
            self.cursores.append(cursor)
            try:
                return work(cursor)
            except IntegrityError:
                if intento > max_retries:
                    raise
                continue


def peticion(cod: str = "CTSB26/0472", **cambios: Any) -> dict[str, Any]:
    """La hoja de agosto del contrato `cod` como cuerpo de `sigrid/proforma`."""
    return {"database": BD, "usu": "prueba", "referencia_externa": "PRF-1001",
            **DATOS["hojas"][cod], **cambios}
