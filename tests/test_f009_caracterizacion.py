# tests/test_f009_caracterizacion.py
"""
F-009 · T1 · R2, R3 y R4: caracterización del modo clásico de
`POST /api/sigrid/albaran` y de `POST /api/sigrid/albaran-directo`.

Fija **lo que hacen hoy** (código de `dev`, antes de cualquier cambio de
producción de F-009) las dos rutas, extremo a extremo y sin red ni BBDD:

- la respuesta HTTP (código y cuerpo JSON completo);
- cada llamada al repositorio, en orden: método, argumentos, SQL y parámetros;
- dentro de la transacción de escritura: recursos de applock, reintentos y
  cada sentencia que se ejecuta con su SQL y sus parámetros, es decir, las
  filas construidas columna a columna tal como se insertan.

Lo observado se compara con el dorado `tests/fixtures/f009_caracterizacion.json`.
**El dorado no se regenera** (design §Caracterización): se escribió una vez en
T1 y la única forma legítima de que cambie es que cambie el comportamiento, y
eso R2-R4 lo prohíben salvo R8 (el interruptor `SIGRID_ALBARAN_WRITE_ENABLED`,
que aquí se deja **abierto** en los casos de commit para que el test pase igual
antes y después de F-009).

Los datos son sintéticos: ni CIF, ni obras, ni identificadores reales.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime as _datetime_real
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

import azure.functions as func
import pytest

import function_app
from application.use_cases import create_purchase_albaran_use_case as modulo_clasico
from application.use_cases.create_purchase_albaran_use_case import CreatePurchaseAlbaranUseCase
from domain.models import sql_models

DORADO = Path(__file__).parent / "fixtures" / "f009_caracterizacion.json"

_BD = "ruesma_prueba"
_AHORA = _datetime_real(2026, 3, 15, 9, 30, 5)


# ---------------------------------------------------------------------------
# Dobles
# ---------------------------------------------------------------------------


@dataclass
class SettingsDoble:
    """Solo lo que leen las dos rutas y los dos casos de uso. Con
    `sigrid_albaran_write_enabled` a True la llave de R8 queda abierta."""

    sigrid_domain_write_enabled: bool = True
    sigrid_albaran_write_enabled: bool = True
    allowed_write_databases: list[str] = field(default_factory=lambda: [_BD])
    sigrid_albaran_empide: int = 7777
    default_write_timeout_seconds: int = 30
    applock_timeout_ms: int = 10000
    domain_write_max_retries: int = 3


class _RelojFijo:
    """Sustituye a `datetime` en el módulo del caso de uso clásico (el directo
    importa de él `_today_yyyymmdd` y `_now_hhmmss`)."""

    @staticmethod
    def now() -> _datetime_real:
        return _AHORA


class CursorDoble:
    def __init__(self, repo: RepositorioDoble) -> None:
        self._repo = repo
        self._ultima = ""
        self.sentencias: list[dict[str, Any]] = []

    def execute(self, sql: str, *params: Any) -> None:
        self._ultima = sql
        self.sentencias.append({"sql": sql, "parametros": list(params)})

    def fetchone(self) -> tuple[Any, ...]:
        for tabla, valor in self._repo.max_ide.items():
            if self._ultima.endswith(f"FROM dbo.[{tabla}]"):
                return (valor,)
        raise AssertionError(f"fetchone sin respuesta para: {self._ultima}")


class RepositorioDoble:
    """Graba cada llamada y responde con los datos fijos del caso."""

    def __init__(self, datos: dict[str, Any]) -> None:
        self.datos = datos
        self.max_ide: dict[str, int] = datos.get("max_ide", {})
        self.llamadas: list[dict[str, Any]] = []

    # --- lecturas -----------------------------------------------------------
    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        self.llamadas.append({
            "metodo": "execute_read_query", "database": request.database,
            "sql": request.sql, "parameters": list(request.parameters),
            "max_rows": request.max_rows,
        })
        filas = self._responder(request.sql, list(request.parameters))
        if not filas:
            return [], [], False
        columnas = list(filas[0].keys())
        return columnas, [tuple(f[c] for c in columnas) for f in filas], False

    def _responder(self, sql: str, p: list[Any]) -> list[dict[str, Any]]:
        d = self.datos
        if "FROM dbo.mov" in sql:
            return d.get("mov", {}).get(f"{p[0]}/{p[1]}", [])
        if "FROM dbo.dcapro WHERE proide" in sql:
            return d.get("dcapro_por_producto", {}).get(str(p[0]), [])
        if "FROM dbo.dcapro WHERE docide" in sql:
            return d.get("dcapro_por_documento", {}).get(str(p[0]), [])
        if "MAX(TRY_CONVERT" in sql:
            return [{"siguiente": d["siguiente_cod"]}]
        if "d.entcif = ?" in sql:
            return d.get("plantilla_por_cif", [])
        if "d.entide = ?" in sql:
            return d.get("plantilla_por_proveedor", [])
        if "cod LIKE ?" in sql:
            return d.get("plantilla_por_serie", [])
        if "AND cod = ?" in sql:
            return d.get("obra", [])
        if "WHERE tip = ? ORDER BY" in sql:
            return d.get("plantilla_cualquiera", [])
        raise AssertionError(f"lectura no prevista: {sql}")

    def locate_contract(self, **kwargs: Any) -> tuple[list[str], list[tuple[Any, ...]]]:
        self.llamadas.append({"metodo": "locate_contract", **kwargs})
        filas = self.datos.get("contratos", [])
        columnas = ["ide", "obride", "cod_contrato", "entcif"]
        return columnas, [tuple(f[c] for c in columnas) for f in filas]

    def read_full_row(self, **kwargs: Any) -> tuple[list[str], tuple[Any, ...]] | None:
        self.llamadas.append({"metodo": "read_full_row", **kwargs})
        fila = self.datos.get("filas", {}).get(f"{kwargs['table']}/{kwargs['ide']}")
        if fila is None:
            return None
        return list(fila.keys()), tuple(fila.values())

    def read_rows_by(self, **kwargs: Any) -> tuple[list[str], list[tuple[Any, ...]]]:
        self.llamadas.append({"metodo": "read_rows_by", **kwargs})
        filas = self.datos.get("ctrpro", [])
        columnas = list(filas[0].keys()) if filas else []
        return columnas, [tuple(f[c] for c in columnas) for f in filas]

    def peek_next_ide(self, **kwargs: Any) -> int:
        self.llamadas.append({"metodo": "peek_next_ide", **kwargs})
        return self.datos["peek"][kwargs["table"]]

    # --- escritura ----------------------------------------------------------
    def run_in_write_transaction(self, *, work: Callable[[Any], Any], **kwargs: Any) -> Any:
        cursor = CursorDoble(self)
        llamada: dict[str, Any] = {"metodo": "run_in_write_transaction", **kwargs}
        self.llamadas.append(llamada)
        resultado = work(cursor)
        llamada["sentencias"] = cursor.sentencias
        llamada["resultado"] = resultado
        return resultado


# ---------------------------------------------------------------------------
# Datos fijos (sintéticos)
# ---------------------------------------------------------------------------

_CTR = {
    "ide": 5001, "entide": 3001, "entcod": "P0001", "entres": "PROVEEDOR PRUEBA SL",
    "entcif": "B00000000", "almide": 6001, "cenide": 6101, "estser": 0, "estfac": 0,
}

_CTRPRO = [
    {"ide": 5101, "docide": 5001, "pos": 64, "proide": 9001, "can": 10.0, "canser": 4.0,
     "canfac": 0.0, "pre": 12.5, "tar": 12.5, "dto": "", "tot": 125.0, "ivacuo": 26.25,
     "res": "CEMENTO PRUEBA", "tex": None, "ivaide": 3, "unimed": "SAC", "almide": None,
     "cenide": 6101, "caaide": 7001, "paride": 8001},
    {"ide": 5102, "docide": 5001, "pos": 128, "proide": 9002, "can": 5.0, "canser": 0.0,
     "canfac": 0.0, "pre": 3.333, "tar": None, "dto": None, "tot": 16.67, "ivacuo": 3.5,
     "res": "ARENA PRUEBA", "tex": "texto de linea", "ivaide": 3, "unimed": None,
     "almide": 6002, "cenide": None, "caaide": None, "paride": None},
    {"ide": 5103, "docide": 5001, "pos": 192, "proide": 9003, "can": 2.0, "canser": 2.0,
     "canfac": 2.0, "pre": 1.0, "tar": 1.0, "dto": "", "tot": 2.0, "ivacuo": 0.42,
     "res": "GRAVA PRUEBA", "tex": "", "ivaide": 3, "unimed": "T", "almide": 6001,
     "cenide": 6101, "caaide": 7001, "paride": 8001},
]


def _con_plantilla(ide: int) -> dict[str, Any]:
    return {"ide": ide, "emp": 1, "tip": 14, "cod": "AC00/1", "res": "PLANTILLA",
            "fec": 20000101, "est": 3, "usu": "PRUEBA"}


def _dca_plantilla(ide: int, entide: int, *, completa: bool = True) -> dict[str, Any]:
    fila = {
        "ide": ide, "entide": entide, "entcod": "PVIEJO", "entres": "NOMBRE VIEJO",
        "entcif": "B99999999", "fecdoc": 20000101, "hor": 101010, "entref": "REF VIEJA",
        "eioide": 9, "ctride": 1, "obride": 1, "almide": 1, "cenide": 1, "empide": 1,
        "forpagide": 11, "impbru": 50.0, "impnet": 50.0, "totbas": 50.0, "totiva": 10.5,
        "totdoc": 60.5, "tot": 60.5, "totpag": 60.5, "impdes": 2.0, "imprec": 1.0,
        "estser": 1, "estfac": 1, "synckey": "CLAVE VIEJA",
    }
    if completa:
        fila.update({"totbasdiv": 50.0, "totivadiv": 10.5, "totdocdiv": 60.5,
                     "impdesdiv": 2.0, "imprecdiv": 1.0})
    return fila


def _dcapro_plantilla(ide: int, proide: int, almide: int) -> dict[str, Any]:
    return {
        "ide": ide, "docide": 1200, "pos": 64, "proide": proide, "pre": 9.0, "can": 1.0,
        "tar": 9.0, "dto": "", "tot": 9.0, "res": "DESCRIPCION VIEJA", "tex": "",
        "ivaide": 3, "ivacuo": 1.89, "unimed": "UD", "almide": almide, "obride": 4000,
        "cenide": 6101, "caaide": 7000, "paride": 0, "docoritip": 0, "docoricod": "",
        "docoriide": 0, "linoriide": 0, "canoriori": 0.0, "imporiori": 0.0, "canser": 1.0,
        "canfac": 1.0, "cancan": 0.0, "canped": 0.0, "canorilin": 0.0, "canoriant": 0.0,
        "imporiant": 0.0, "imporiantdiv": 0.0, "imporioridiv": 0.0, "cueide": 501,
        "prepma": 8.5, "natide": 601,
    }


def _datos_clasico(**extra: Any) -> dict[str, Any]:
    datos: dict[str, Any] = {
        "contratos": [{"ide": 5001, "obride": 4001, "cod_contrato": "CT00/0001",
                       "entcif": "B00000000"}],
        "filas": {"ctr/5001": _CTR},
        "ctrpro": _CTRPRO,
        "siguiente_cod": 41,
        "peek": {"con": 12001, "dcapro": 22001, "ctrprodes": 32001, "mov": 42001},
        "max_ide": {"con": 12001, "dcapro": 22000, "ctrprodes": 32000, "mov": 42000},
    }
    datos.update(extra)
    return datos


_PETICION_CLASICA = {
    "database": _BD, "cod_contrato": " CT00/0001 ", "cod_obra": "9999",
    "cif_proveedor": "B00000000", "su_referencia": " ALB-PRUEBA-1 ",
}

CASOS: dict[str, dict[str, Any]] = {
    # Plantilla de cabecera del mismo proveedor; 9001 con histórico de dcapro y
    # de mov; 9002 sin histórico propio (cae a la primera línea de la plantilla)
    # ni mov. Pedidas en orden inverso al del contrato y sin fecha (hoy).
    "clasico_dry_run": {
        "ruta": "albaran",
        "peticion": {**_PETICION_CLASICA, "lineas_recibidas": [
            {"ctrpro_ide": 5102, "cantidad": 2}, {"ctrpro_ide": 5101, "cantidad": 3}]},
        "datos": _datos_clasico(
            plantilla_por_proveedor=[{"ide": 1200}],
            filas={"ctr/5001": _CTR, "con/1200": _con_plantilla(1200),
                   "dca/1200": _dca_plantilla(1200, 3001)},
            dcapro_por_producto={"9001": [_dcapro_plantilla(21000, 9001, 6001)]},
            dcapro_por_documento={"1200": [_dcapro_plantilla(21001, 9555, 6003)]},
            mov={"9001/6001": [{"almcan": 100.0, "almpma": 10.0}]},
        ),
    },
    # Commit: dos lineas_recibidas al MISMO ctrpro (se suman: 2 + 5 = 7 > 6
    # pendiente) y otra con cantidad 0. Plantilla de cabecera por la serie (de
    # otro proveedor, con aviso y sin columnas *div). 9001 sin ningún histórico.
    "clasico_commit": {
        "ruta": "albaran",
        "peticion": {**_PETICION_CLASICA, "fecha_albaran": 20251231, "empide": 4242,
                     "commit": True, "lineas_recibidas": [
                         {"ctrpro_ide": 5101, "cantidad": 2}, {"ctrpro_ide": 5102, "cantidad": 0},
                         {"ctrpro_ide": 5101, "cantidad": 5}]},
        "datos": _datos_clasico(
            plantilla_por_serie=[{"ide": 1300}],
            filas={"ctr/5001": _CTR, "con/1300": _con_plantilla(1300),
                   "dca/1300": _dca_plantilla(1300, 3999, completa=False)},
            dcapro_por_producto={"9002": [_dcapro_plantilla(21002, 9002, 6002)]},
            mov={"9002/6002": [{"almcan": 4.0, "almpma": 3.0}]},
        ),
    },
    "clasico_contrato_inexistente": {
        "ruta": "albaran",
        "peticion": {**_PETICION_CLASICA, "lineas_recibidas": [{"ctrpro_ide": 5101, "cantidad": 1}]},
        "datos": _datos_clasico(contratos=[]),
    },
    "clasico_linea_ajena": {
        "ruta": "albaran",
        "peticion": {**_PETICION_CLASICA, "lineas_recibidas": [{"ctrpro_ide": 5999, "cantidad": 1}]},
        "datos": _datos_clasico(),
    },
    # Directo sin almacén ni centro en la petición: salen de la plantilla de
    # cada producto (9002 cae a la primera línea del albarán plantilla).
    "directo_dry_run": {
        "ruta": "albaran-directo",
        "peticion": {"database": _BD, "cif_proveedor": " B00000000 ", "cod_obra": "9999",
                     "su_referencia": "ALB-PRUEBA-2", "lineas": [
                         {"proide": 9001, "can": 4, "pre": 11.0, "res": " PIEZA PRUEBA ",
                          "unimed": "UD", "paride": 8001},
                         {"proide": 9002, "can": 1.5, "pre": 2.0}]},
        "datos": {
            "obra": [{"ide": 4001}],
            "plantilla_por_cif": [{"ide": 1200, "entide": 3001, "entcod": "P0001",
                                   "entres": "PROVEEDOR PRUEBA SL", "entcif": "B00000000"}],
            "filas": {"con/1200": _con_plantilla(1200), "dca/1200": _dca_plantilla(1200, 3001)},
            "siguiente_cod": 7,
            "dcapro_por_producto": {"9001": [_dcapro_plantilla(21000, 9001, 6001)]},
            "dcapro_por_documento": {"1200": [_dcapro_plantilla(21001, 9555, 6003)]},
            "mov": {"9001/6001": [{"almcan": 100.0, "almpma": 10.0}]},
            "peek": {"con": 12001, "dcapro": 22001, "mov": 42001},
        },
    },
    # Directo commit con almacén y centro en la petición; 9004 sin histórico
    # (plantilla mínima, aviso) y cantidad 0; IVA forzado en la primera línea.
    "directo_commit": {
        "ruta": "albaran-directo",
        "peticion": {"database": _BD, "cif_proveedor": "B00000000", "cod_obra": "9999",
                     "almide": 6001, "cenide": 6101, "fecha_albaran": 20251231, "commit": True,
                     "lineas": [
                         {"proide": 9001, "can": 4, "pre": 11.0, "ivaide": 5},
                         {"proide": 9004, "can": 0, "pre": 2.5}]},
        "datos": {
            "obra": [{"ide": 4001}],
            "plantilla_por_cif": [{"ide": 1200, "entide": 3001, "entcod": "P0001",
                                   "entres": "PROVEEDOR PRUEBA SL", "entcif": "B00000000"}],
            "filas": {"con/1200": _con_plantilla(1200), "dca/1200": _dca_plantilla(1200, 3001)},
            "siguiente_cod": 7,
            "dcapro_por_producto": {"9001": [_dcapro_plantilla(21000, 9001, 6001)]},
            "mov": {"9001/6001": [{"almcan": 100.0, "almpma": 10.0}]},
            "max_ide": {"con": 12001, "dcapro": 22000, "mov": 42000},
        },
    },
}


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _aislado(monkeypatch: pytest.MonkeyPatch) -> None:
    # `SqlReadRequest` valida contra `get_settings()`, que leería el `.env`.
    monkeypatch.setattr(sql_models, "get_settings", lambda: SimpleNamespace(
        default_max_rows=200, max_allowed_rows=1000,
        default_query_timeout_seconds=30, max_query_timeout_seconds=120,
    ))
    monkeypatch.setattr(modulo_clasico, "datetime", _RelojFijo)


def ejecutar(nombre: str, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Lanza el caso por la ruta HTTP real y devuelve lo observado, ya pasado
    por JSON (tuplas → listas) para compararlo con el dorado."""
    caso = CASOS[nombre]
    repo = RepositorioDoble(json.loads(json.dumps(caso["datos"])))
    settings = SettingsDoble()
    caso_de_uso = CreatePurchaseAlbaranUseCase(repo, settings)
    monkeypatch.setattr(
        function_app, "build_dependencies",
        lambda: (settings, repo, None, None, None, None, caso_de_uso),
    )
    ruta = {
        "albaran": function_app.sigrid_albaran,
        "albaran-directo": function_app.sigrid_albaran_directo,
    }[caso["ruta"]]._function.get_user_function()
    respuesta = ruta(func.HttpRequest(
        method="POST", url=f"/api/sigrid/{caso['ruta']}",
        body=json.dumps(caso["peticion"]).encode(),
        headers={"Content-Type": "application/json"},
    ))
    observado = {
        "ruta": caso["ruta"],
        "peticion": caso["peticion"],
        "status": respuesta.status_code,
        "cuerpo": json.loads(respuesta.get_body().decode("utf-8")),
        "llamadas": repo.llamadas,
    }
    return json.loads(json.dumps(observado))


def _dorado() -> dict[str, Any]:
    return json.loads(DORADO.read_text(encoding="utf-8"))


def test_f009_r4_el_dorado_cubre_exactamente_los_casos_del_diseno() -> None:
    assert sorted(_dorado()) == sorted(CASOS)


@pytest.mark.parametrize("nombre", [n for n in CASOS if n.startswith("clasico_")])
def test_f009_r2_el_modo_clasico_se_comporta_como_en_dev(
    nombre: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert ejecutar(nombre, monkeypatch) == _dorado()[nombre]


@pytest.mark.parametrize("nombre", [n for n in CASOS if n.startswith("directo_")])
def test_f009_r3_albaran_directo_se_comporta_como_en_dev(
    nombre: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert ejecutar(nombre, monkeypatch) == _dorado()[nombre]


# Comprobaciones legibles de lo que el dorado fija, para que un cambio en él
# no pase desapercibido aunque alguien lo regenerase.


def test_f009_r2_el_commit_suma_las_lineas_repetidas_del_mismo_ctrpro() -> None:
    caso = _dorado()["clasico_commit"]
    assert caso["status"] == 200 and caso["cuerpo"]["committed"] is True
    transaccion = caso["llamadas"][-1]
    assert transaccion["applock_resources"] == [
        "SIGRID_IDE_con", "SIGRID_IDE_dcapro", "SIGRID_IDE_ctrprodes", "SIGRID_IDE_mov"]
    updates = [s for s in transaccion["sentencias"] if s["sql"].startswith("UPDATE dbo.[ctrpro]")]
    assert updates == [{"sql": "UPDATE dbo.[ctrpro] SET canser = canser + ? WHERE ide = ?",
                        "parametros": [7.0, 5101]}]
    assert any("supera lo pendiente" in w for w in caso["cuerpo"]["warnings"])


def test_f009_r2_los_errores_del_clasico_son_400_con_valueerror() -> None:
    dorado = _dorado()
    for nombre in ("clasico_contrato_inexistente", "clasico_linea_ajena"):
        assert dorado[nombre]["status"] == 400
        assert dorado[nombre]["cuerpo"]["details"] == {"type": "ValueError"}
        assert not any(l["metodo"] == "run_in_write_transaction" for l in dorado[nombre]["llamadas"])


def test_f009_r3_los_dry_run_no_abren_transaccion() -> None:
    dorado = _dorado()
    for nombre in ("clasico_dry_run", "directo_dry_run"):
        assert dorado[nombre]["cuerpo"]["dry_run"] is True
        assert not any(l["metodo"] == "run_in_write_transaction" for l in dorado[nombre]["llamadas"])
