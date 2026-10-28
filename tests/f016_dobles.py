# tests/f016_dobles.py
"""
F-016 · dobles de la proforma a origen. No es un fichero de tests: lo importan
`test_f016_statements.py`, `test_f016_use_case.py` y `test_f016_transaccion.py`.

Extiende el doble de F-007 (`tests/f007_dobles.py`, que no se toca): el
repositorio y el cursor reconocen ademas LP7-LP9 por su SQL EXACTO, dentro y
fuera de la transaccion; cualquier otra sentencia hace fallar el test. El ERP
de mentira es la obra 0719 de F-007 con la cadena sintetica de
`tests/fixtures/f016_cadena.json` (forma de M44) en el contrato CTSB26/0472.

Sin red y sin base de datos.
"""
from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import f007_dobles
from f007_dobles import CursorProforma, RepositorioProforma, ctride_de
from f009_dobles import IntegrityError, plantilla_dcapro

from application.use_cases.proforma_origen_statements import ProformaOrigenStatements

FIXTURE = Path(__file__).parent / "fixtures" / "f016_cadena.json"
CADENA: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))

CTR_0472 = ctride_de(CADENA["contrato"])
DOCUMENTOS: dict[str, dict[str, Any]] = {d["cod"]: d for d in CADENA["documentos"]}
#: La punta de la cadena larga (julio) y la de la paralela.
PUNTA, PARALELA, PRIMERA, DE_MES = "PROF26/00201", "PROF26/00301", "PROF26/00101", "AC26/20001"
IDE_PUNTA = DOCUMENTOS[PUNTA]["ide"]

_O = ProformaOrigenStatements(database="ruesma")

#: SQL exacto -> nombre corto, las de F-016.
NOMBRES_F016: dict[str, str] = {
    _O.leer_proforma_anterior(1, "x")[0]: "lp7_anterior",
    _O.leer_sucesoras(1, 1)[0]: "lp8_sucesoras",
    _O.leer_lineas_anterior(1)[0]: "lp9_lineas",
}


def nombre(sql: str) -> str:
    """Las de F-016 y, si no, las de F-007 y F-009 (o `AssertionError`)."""
    if sql in NOMBRES_F016:
        return NOMBRES_F016[sql]
    return f007_dobles.nombre(sql)


# --- La cadena ----------------------------------------------------------------------


def fila_dcapro(docide: int, datos: dict[str, Any]) -> dict[str, Any]:
    """Una `dcapro` COMPLETA de la cadena (lo que devuelve `SELECT *`): la plantilla
    de F-009 con lo de la fixture y el seguimiento distinto de 0, para ver que la
    arrastrada lo pone a 0."""
    vinculada = bool(datos["linoriide"])
    can, pre = datos["can"], datos["pre"]
    return {
        **plantilla_dcapro(610004),
        "ide": datos["ide"], "docide": docide, "pos": datos["pos"], "can": can, "pre": pre,
        "tar": pre, "dto": "", "tot": round(can * pre, 2), "ivacuo": round(can * pre * 0.21, 2),
        "prepma": 9.5, "res": datos["res"], "refent": datos["refent"], "unimed": "M3",
        "almide": 70, "cenide": 80, "obride": 7190, "caaide": 90, "paride": 355001,
        "docoritip": 44 if vinculada else 0, "docoricod": "CTSB26/0472" if vinculada else "",
        "docoriide": CTR_0472 if vinculada else 0, "linoriide": datos["linoriide"],
        "canoriori": datos["canoriori"], "imporiori": datos["imporiori"],
        "canorilin": datos["canorilin"], "canoriant": 3.0, "imporiant": 4.0,
        "canser": 1.0, "canfac": 2.0, "cancan": 5.0, "canped": 6.0, "imporiantdiv": 7.0,
        "imporioridiv": 8.0, "canmed": 2.5, "med": b"medicion", "fec": 20260731,
    }


def lineas_de(cod: str) -> list[dict[str, Any]]:
    """Las `dcapro` de un documento de la cadena, por `pos` (LP9)."""
    ide = DOCUMENTOS[cod]["ide"]
    return [fila_dcapro(ide, datos) for datos in CADENA["lineas"].get(str(ide), [])]


def fila_lp1(cod: str) -> tuple[Any, ...]:
    d = DOCUMENTOS[cod]
    return (d["ide"], d["cod"], d["fec"], d["entref"], d["totbas"], d["docoritip"])


def fila_lp7(documento: str, **cambios: Any) -> tuple[Any, ...]:
    d = {**DOCUMENTOS[documento], **cambios}
    return (d["ide"], d["cod"], d["fec"], d["docoritip"])


def _lp7(params: list[Any]) -> list[tuple[Any, ...]]:
    _tip, ctride, cod = params
    return [fila_lp7(c) for c, d in DOCUMENTOS.items() if c == cod and ctride == CTR_0472]


def _lp8(params: list[Any]) -> list[tuple[Any, ...]]:
    _tip, ctride, ide = params
    return [(d["ide"], d["cod"]) for d in DOCUMENTOS.values()
            if d["docoriide"] == ide and ctride == CTR_0472]


def _lp9(params: list[Any]) -> list[dict[str, Any]]:
    cods = {d["ide"]: c for c, d in DOCUMENTOS.items()}
    return lineas_de(cods[params[0]]) if params[0] in cods else []


def lecturas_cadena() -> dict[str, Any]:
    """LP1 con la cadena (ninguna de agosto) y LP7-LP9 de la fixture."""
    return {
        "lp1_proformas": [fila_lp1(cod) for cod in DOCUMENTOS],
        "lp7_anterior": _lp7,
        "lp8_sucesoras": _lp8,
        "lp9_lineas": _lp9,
    }


class CursorOrigen(CursorProforma):
    """El cursor de F-007 que reconoce tambien LP7-LP9 (R17: LP8 dentro)."""

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


class RepositorioOrigen(RepositorioProforma):
    """El repositorio de F-007 con la cadena de CTSB26/0472. Dentro de la
    transaccion, LP1 y LP8 contestan por defecto lo mismo que fuera."""

    def __init__(
        self,
        lecturas: dict[str, Any] | None = None,
        *,
        filas_en_transaccion: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        base = lecturas_cadena()
        todas = {**base, **(lecturas or {})}
        super().__init__(
            CADENA["contrato"],
            todas,
            filas_en_transaccion={
                "referencia": [],
                "lp1_proformas": todas["lp1_proformas"],
                "lp8_sucesoras": lambda _i, p: self._responder("lp8_sucesoras", p),
                **(filas_en_transaccion or {}),
            },
            **kwargs,
        )

    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        assert request.database == "ruesma"
        clave = nombre(request.sql)
        self.llamadas.append(("leer", (clave, list(request.parameters), request.max_rows)))
        filas = self._responder(clave, list(request.parameters))
        if filas and isinstance(filas[0], dict):
            columnas = list(filas[0].keys())
            return columnas, [tuple(f[c] for c in columnas) for f in filas], clave == self.truncar_en
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
            cursor = CursorOrigen(self, intento)
            self.cursores.append(cursor)
            try:
                return work(cursor)
            except IntegrityError:
                if intento > max_retries:
                    raise
                continue
