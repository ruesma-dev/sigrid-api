# tests/test_f006_use_case.py
"""
F-006 · R3, R6-R10, R13-R15, R17, R19 y R20: el caso de uso del lote.

Sin red y sin base de datos: repositorio, cursor y reloj son dobles. El doble
del repositorio reproduce el bucle de reintentos de `run_in_write_transaction`
(nuevo cursor por intento, repetir ante `IntegrityError` hasta `max_retries`),
así se comprueba que `work` es reentrante. El doble del cursor contesta las
relecturas con lo que de verdad se insertó en ESE intento, como haría la base.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from application.use_cases.create_partes_reclamacion_use_case import (
    APPLOCKS,
    CreatePartesReclamacionUseCase,
)
from application.use_cases.parte_reclamacion_statements import (
    CON_COLUMNAS,
    LOG_COLUMNAS,
    ParteReclamacionStatements,
)
from domain.models.parte_reclamacion_models import (
    CreatePartesReclamacionRequest,
    ParteReclamacionError,
)

# --- Datos del ERP de mentira (obra 0626, como la prueba manual de Q4) -------

_OBRA = 1758465
_UPV = 2751478
_UPV_B = 2751479
_AHORA = datetime(2026, 9, 24, 20, 15, 30, tzinfo=timezone.utc)  # 22:15:30 en Madrid

_S = ParteReclamacionStatements(database="ruesma")
_NOMBRES: dict[str, str] = {
    _S.leer_serie()[0]: "serie",
    _S.leer_estado_inicial(1)[0]: "estado",
    _S.leer_obra(1, "x")[0]: "obra",
    _S.leer_usuario("x")[0]: "usuario",
    _S.leer_unidades_postventa(1, 1)[0]: "upv",
    _S.leer_oficios_de_la_obra(1)[0]: "oficios_obra",
    _S.leer_tipos()[0]: "tipos",
    _S.leer_clases()[0]: "clases",
    _S.leer_oficios()[0]: "oficios",
    _S.buscar_referencia("x", 1)[0]: "referencia",
    _S.ultimo_cod(1, "x")[0]: "ultimo_cod",
    _S.siguiente_pos_sin_bloqueo()[0]: "pos_sin_bloqueo",
    _S.reservar_cod(1, "x")[0]: "reservar_cod",
    _S.reservar_ide_con()[0]: "ide_con",
    _S.reservar_pos_rcp()[0]: "pos_rcp",
    _S.reservar_ide_rcpint()[0]: "ide_rcpint",
    _S.reservar_ide_conext()[0]: "ide_conext",
    _S.reservar_ide_log()[0]: "ide_log",
    _S.revalidar_unidad_postventa(1, 1)[0]: "revalidar_upv",
    _S.revalidar_oficio_de_obra(1, 1)[0]: "revalidar_obrofc",
    _S.insertar_con(dict.fromkeys(CON_COLUMNAS))[0]: "insert_con",
    _S.releer_con(1, "x")[0]: "releer_con",
    _S.releer_rcp(1)[0]: "releer_rcp",
    _S.releer_rcpint(1)[0]: "releer_rcpint",
    _S.releer_conext(1)[0]: "releer_conext",
    _S.releer_log(1)[0]: "releer_log",
    _S.insertar_log(dict.fromkeys(LOG_COLUMNAS))[0]: "insert_log",
}


def _nombre(sql: str) -> str:
    if sql in _NOMBRES:
        return _NOMBRES[sql]
    # Los INSERT de rcp, rcpint y conext se reconocen por su cabecera exacta;
    # su SQL completo ya lo fija carácter a carácter test_f006_statements.
    for tabla in ("rcpint", "rcp", "conext"):
        if sql.startswith(f"INSERT INTO dbo.{tabla} ("):
            return f"insert_{tabla}"
    raise AssertionError(f"sentencia inesperada: {sql}")


_LECTURAS: dict[str, list[tuple[Any, ...]]] = {
    "serie": [(213, 1, 4, 1)],
    "estado": [(1, "SAT")],
    "obra": [(_OBRA, 1, "0626")],
    "usuario": [("prueba",)],
    "upv": [
        (_UPV, "0626.03PORTAL 1.1.A", 2811575, 2811576),
        (_UPV_B, "0626.03PORTAL 1.1.B", 0, 0),
    ],
    # (obrofc.ide, pos, oficio, proveedor)
    "oficios_obra": [
        (2173, 64, "0039", "1181"),
        (2200, 128, "0070", "2001"),     # 0070: dos proveedores distintos
        (2201, 192, "0070", "2002"),
        (2301, 320, "0080", "3001"),     # 0080: dos filas idénticas
        (2300, 256, "0080", "3001"),
        (2400, 384, None, "4001"),       # sin oficio
        (2500, 448, "0090", None),       # sin proveedor
        (2305, 1, "0085", "5001"),       # 0085: idénticas, una con pos NULL
        (2310, None, "0085", "5001"),
        (2402, 500, "0086", "6001"),     # 0086: idénticas y con la misma pos
        (2401, 500, "0086", "6001"),
    ],
    "tipos": [(1, "0001", 0), (2, "0002", 0), (3, "0003", 0), (5, "0005", 20250101)],
    "clases": [(1, "0001", 0), (2, "0002", 0), (3, "0003", None)],
    "oficios": [
        (39, "0039", 0), (70, "0070", 0), (80, "0080", 0), (90, "0090", 0),
        (99, "0099", 0), (98, "0098", 20240101),
    ],
    "referencia": [],
    "ultimo_cod": [("RS26.09/0771",)],
    "pos_sin_bloqueo": [(1408064,)],
}

_PEEK = {"con": 2900001, "rcpint": 25405, "conext": 56286, "log": 8488889}

_RESERVAS: dict[str, Any] = {
    "reservar_cod": ("RS26.09/0771",),
    "ide_con": (2900001,),
    "pos_rcp": (1408064,),
    "ide_rcpint": (25405,),
    "ide_conext": (56286,),
    "ide_log": (8488889,),
    "revalidar_upv": (1,),
    "revalidar_obrofc": (1,),
}


class IntegrityError(Exception):
    """Como `pyodbc.IntegrityError`: el caso de uso la reconoce por su nombre."""


# --- Dobles ------------------------------------------------------------------


@dataclass
class SettingsDoble:
    sigrid_domain_write_enabled: bool = True
    sigrid_reclamacion_write_enabled: bool = True
    sql_server_write_username: str | None = "usuario_de_mentira"
    sql_server_write_password: str | None = "no-es-una-credencial"
    allowed_write_databases: list[str] = field(default_factory=lambda: ["ruesma"])
    sigrid_reclamacion_max_partes: int = 50
    sigrid_reclamacion_prefijos_referencia: list[str] = field(default_factory=lambda: ["PVI-"])
    sigrid_reclamacion_presupuesto_segundos: int = 150
    applock_timeout_ms: int = 10000
    domain_write_max_retries: int = 3
    default_write_timeout_seconds: int = 30
    max_allowed_rows: int = 1000


class CursorDoble:
    """Un intento de transacción. Las reservas pueden variar por intento:
    `respuestas[clave]` es una tupla o una función del nº de intento."""

    def __init__(self, repo: RepositorioDoble, intento: int) -> None:
        self.repo = repo
        self.intento = intento
        self.ejecutadas: list[tuple[str, list[Any]]] = []
        self.insertadas: dict[str, int] = {}
        self._ultima = ""
        self.connection = SimpleNamespace(timeout=None)

    def execute(self, sql: str, *params: Any) -> None:
        clave = _nombre(sql)
        self.ejecutadas.append((clave, list(params)))
        self.repo.sentencias_en_transaccion.append((clave, sql, list(params)))
        self._ultima = clave
        fallo = self.repo.fallos.get(clave)
        if fallo is not None:
            excepcion = fallo(self.intento) if callable(fallo) else fallo
            if excepcion is not None:
                raise excepcion
        if clave.startswith("insert_"):
            tabla = clave.removeprefix("insert_")
            self.insertadas[tabla] = self.insertadas.get(tabla, 0) + 1

    def fetchone(self) -> tuple[Any, ...]:
        clave = self._ultima
        if clave in self.repo.forzar:
            return self.repo.forzar[clave]
        if clave.startswith("releer_"):
            return (self.insertadas.get(clave.removeprefix("releer_"), 0),)
        respuesta = self.repo.reservas[clave]
        return respuesta(self.intento) if callable(respuesta) else respuesta

    def fetchall(self) -> list[tuple[Any, ...]]:
        assert self._ultima == "referencia"
        return list(self.repo.referencia_en_transaccion)


class RepositorioDoble:
    def __init__(
        self,
        lecturas: dict[str, list[tuple[Any, ...]]] | None = None,
        *,
        reservas: dict[str, Any] | None = None,
        fallos: dict[str, Any] | None = None,
        forzar: dict[str, tuple[Any, ...]] | None = None,
        referencia_en_transaccion: list[tuple[Any, ...]] | None = None,
        truncar_en: str | None = None,
    ) -> None:
        self.lecturas = {**_LECTURAS, **(lecturas or {})}
        self.reservas = {**_RESERVAS, **(reservas or {})}
        self.fallos = fallos or {}
        self.forzar = forzar or {}
        self.referencia_en_transaccion = referencia_en_transaccion or []
        self.truncar_en = truncar_en
        self.consultadas: list[tuple[str, list[Any], Any]] = []
        self.peeks: list[tuple[str, str]] = []
        self.transacciones: list[dict[str, Any]] = []
        self.cursores: list[CursorDoble] = []
        self.sentencias_en_transaccion: list[tuple[str, str, list[Any]]] = []

    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        clave = _nombre(request.sql)
        self.consultadas.append((clave, list(request.parameters), request.max_rows))
        assert request.database == "ruesma"
        return [], list(self.lecturas[clave]), clave == self.truncar_en

    def peek_next_ide(self, *, database: str, table: str) -> int:
        self.peeks.append((database, table))
        return _PEEK[table]

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


class Reloj:
    def __init__(self, valores: Iterable[float] = ()) -> None:
        self._valores = list(valores) or [0.0]
        self.llamadas = 0

    def __call__(self) -> float:
        self.llamadas += 1
        indice = min(self.llamadas - 1, len(self._valores) - 1)
        return self._valores[indice]


class Ahora:
    def __init__(self, instante: datetime = _AHORA) -> None:
        self.instante = instante
        self.llamadas = 0

    def __call__(self) -> datetime:
        self.llamadas += 1
        return self.instante


def parte(**cambios: Any) -> dict[str, Any]:
    base = {
        "referencia_externa": "PVI-1",
        "unidad_postventa": "0626.03PORTAL 1.1.A",
        "descripcion": "Fisura en tabique",
        "oficio": "0039",
        "intervinientes": [{"oficio": "0039", "proveedor": "1181"}],
    }
    return {**base, **cambios}


def peticion(partes: list[dict[str, Any]] | None = None, **cambios: Any) -> CreatePartesReclamacionRequest:
    base = {"database": "ruesma", "obra": "0626", "usu": "prueba", "partes": partes or [parte()]}
    return CreatePartesReclamacionRequest.model_validate({**base, **cambios})


def ejecutar(
    partes: list[dict[str, Any]] | None = None,
    *,
    repo: RepositorioDoble | None = None,
    settings: SettingsDoble | None = None,
    reloj: Reloj | None = None,
    ahora: Ahora | None = None,
    **cambios: Any,
):
    repo = repo or RepositorioDoble()
    caso = CreatePartesReclamacionUseCase(
        repo, settings or SettingsDoble(), reloj=reloj or Reloj(), ahora_utc=ahora or Ahora()
    )
    return caso.run(peticion(partes, **cambios)), repo


def fallo_de_lote(**kwargs: Any) -> tuple[str, RepositorioDoble]:
    repo = kwargs.pop("repo", None) or RepositorioDoble()
    with pytest.raises(ParteReclamacionError) as excinfo:
        ejecutar(repo=repo, **kwargs)
    return excinfo.value.codigo, repo


def motivos(respuesta: Any) -> list[str | None]:
    return [p.motivo.codigo if p.motivo else None for p in respuesta.partes]


def estados(respuesta: Any) -> list[str]:
    return [p.estado for p in respuesta.partes]


# --- R10 y R3: guards del lote, antes de leer nada ---------------------------


@pytest.mark.parametrize(
    "settings",
    [
        SettingsDoble(sigrid_domain_write_enabled=False),
        SettingsDoble(sigrid_reclamacion_write_enabled=False),
        SettingsDoble(sql_server_write_username=None),
        SettingsDoble(sql_server_write_password=""),
    ],
)
def test_f006_r10_el_commit_exige_las_llaves_antes_de_leer(settings: SettingsDoble) -> None:
    codigo, repo = fallo_de_lote(settings=settings, commit=True)
    assert codigo == "escritura_reclamaciones_deshabilitada"
    assert repo.consultadas == [] and repo.transacciones == []


def test_f006_r10_sin_llaves_el_dry_run_sigue_funcionando() -> None:
    respuesta, repo = ejecutar(
        settings=SettingsDoble(
            sigrid_domain_write_enabled=False,
            sigrid_reclamacion_write_enabled=False,
            sql_server_write_username=None,
            sql_server_write_password=None,
        )
    )
    assert estados(respuesta) == ["previsto"]
    assert repo.transacciones == []


def test_f006_r3_una_base_fuera_de_la_lista_se_rechaza_sin_leer() -> None:
    codigo, repo = fallo_de_lote(database="master")
    assert codigo == "base_de_datos_no_permitida"
    assert repo.consultadas == []


def test_f006_r3_con_la_lista_de_bases_vacia_tambien_se_rechaza() -> None:
    """Al contrario que el patrón heredado de albaranes: vacía NO abre."""
    codigo, repo = fallo_de_lote(settings=SettingsDoble(allowed_write_databases=[]))
    assert codigo == "base_de_datos_no_permitida"
    assert repo.consultadas == []


def test_f006_r3_un_lote_por_encima_del_tope_se_rechaza_sin_leer() -> None:
    tres = [parte(referencia_externa=f"PVI-{n}") for n in range(3)]
    codigo, repo = fallo_de_lote(partes=tres, settings=SettingsDoble(sigrid_reclamacion_max_partes=2))
    assert codigo == "lote_demasiado_grande"
    assert repo.consultadas == []
    respuesta, _ = ejecutar(tres, settings=SettingsDoble(sigrid_reclamacion_max_partes=3))
    assert len(respuesta.partes) == 3


@pytest.mark.parametrize(
    "serie",
    [[], [(213, 1, 5, 1)], [(213, 1, 4, 1), (215, 1, 4, 1)]],
)
def test_f006_r3_sin_una_serie_activa_de_4_digitos_no_hay_lote(serie: list) -> None:
    codigo, _ = fallo_de_lote(repo=RepositorioDoble({"serie": serie}))
    assert codigo == "serie_no_encontrada"


def test_f006_r3_el_estado_inicial_sale_de_la_serie_y_se_valida_en_conest() -> None:
    repo = RepositorioDoble({"serie": [(213, 1, 4, 3)], "estado": []})
    codigo, _ = fallo_de_lote(repo=repo)
    assert codigo == "estado_inicial_no_encontrado"
    assert ("estado", [708, 3], None) in repo.consultadas


def test_f006_r3_una_obra_que_no_existe_se_rechaza() -> None:
    codigo, _ = fallo_de_lote(repo=RepositorioDoble({"obra": []}))
    assert codigo == "obra_no_encontrada"


def test_f006_r6_la_obra_se_busca_con_el_emp_de_la_serie() -> None:
    repo = RepositorioDoble({"serie": [(213, 28, 4, 1)], "obra": [(_OBRA, 28, "0626")]})
    respuesta, _ = ejecutar(repo=repo)
    assert ("obra", [28, 42, "0626"], None) in repo.consultadas
    assert respuesta.obra.model_dump() == {"ide": _OBRA, "cod": "0626", "emp": 28}
    assert respuesta.partes[0].filas["con"]["emp"] == 28
    assert ("upv", [_OBRA, 28, 707], 1000) in repo.consultadas


def test_f006_r3_un_usuario_que_no_existe_se_rechaza() -> None:
    codigo, _ = fallo_de_lote(repo=RepositorioDoble({"usuario": []}))
    assert codigo == "usuario_no_valido"


@pytest.mark.parametrize("clave", ["upv", "oficios_obra", "tipos", "clases", "oficios", "referencia"])
def test_f006_r6_una_lectura_truncada_no_se_ignora(clave: str) -> None:
    with pytest.raises(ValueError) as excinfo:
        ejecutar(repo=RepositorioDoble(truncar_en=clave))
    assert not isinstance(excinfo.value, ParteReclamacionError)
    assert "truncada" in str(excinfo.value)


def test_f006_r6_las_lecturas_comunes_se_hacen_una_vez_y_en_orden() -> None:
    dos = [parte(), parte(referencia_externa="PVI-2")]
    _, repo = ejecutar(dos)
    comunes = [c[0] for c in repo.consultadas if c[0] not in ("referencia",)]
    assert comunes[:9] == [
        "serie", "estado", "obra", "usuario", "upv", "oficios_obra", "tipos", "clases", "oficios",
    ]
    assert [c for c in comunes if c in ("ultimo_cod", "pos_sin_bloqueo")] == [
        "ultimo_cod", "pos_sin_bloqueo",
    ]
    topes = {c[0]: c[2] for c in repo.consultadas}
    for clave in ("upv", "oficios_obra", "tipos", "clases", "oficios", "referencia"):
        assert topes[clave] == 1000, clave
    assert ("serie", [708, "RS<año2>.<mes>/"], None) in repo.consultadas
    assert ("usuario", ["prueba"], None) in repo.consultadas
    assert ("oficios_obra", [_OBRA], 1000) in repo.consultadas


# --- R7 y R8: rechazos por parte, sin afectar al siguiente --------------------


def _rechazo(defectuoso: dict[str, Any], settings: SettingsDoble | None = None) -> str | None:
    respuesta, _ = ejecutar(
        [defectuoso, parte(referencia_externa="PVI-BUENO")], settings=settings
    )
    assert estados(respuesta) == ["rechazado", "previsto"]
    assert respuesta.partes[0].filas == {} and respuesta.partes[0].ide is None
    assert respuesta.partes[1].cod == "RS26.09/0772"  # el rechazado no gasta número
    return respuesta.partes[0].motivo.codigo


def test_f006_r7_referencia_sin_prefijo_admitido() -> None:
    assert _rechazo(parte(referencia_externa="XYZ-1")) == "referencia_no_permitida"


def test_f006_r7_el_prefijo_distingue_mayusculas() -> None:
    assert _rechazo(parte(referencia_externa="pvi-1")) == "referencia_no_permitida"


def test_f006_r7_sin_prefijos_configurados_toda_referencia_se_rechaza() -> None:
    respuesta, _ = ejecutar(
        [parte(), parte(referencia_externa="PVI-2")],
        settings=SettingsDoble(sigrid_reclamacion_prefijos_referencia=[]),
    )
    assert motivos(respuesta) == ["referencia_no_permitida"] * 2
    assert "(ninguno configurado)" in respuesta.partes[0].motivo.mensaje


def test_f006_r7_el_rechazo_por_prefijo_dice_cuales_valen() -> None:
    respuesta, _ = ejecutar(
        [parte(referencia_externa="XYZ-1")],
        settings=SettingsDoble(sigrid_reclamacion_prefijos_referencia=["PVI-", "OTRO-"]),
    )
    assert "(PVI-, OTRO-)" in respuesta.partes[0].motivo.mensaje


def test_f006_r7_admite_cualquiera_de_los_prefijos() -> None:
    respuesta, _ = ejecutar(
        [parte(referencia_externa="OTRO-1")],
        settings=SettingsDoble(sigrid_reclamacion_prefijos_referencia=["PVI-", "OTRO-"]),
    )
    assert estados(respuesta) == ["previsto"]


def test_f006_r7_referencia_duplicada_en_el_lote() -> None:
    """La colación del ERP es CI: `PVI-1` y `pvi-1`... no llegan (prefijo), pero
    `PVI-a` y `PVI-A` son la misma referencia para SQL Server."""
    respuesta, _ = ejecutar(
        [
            parte(referencia_externa="PVI-a"),
            parte(referencia_externa="PVI-A"),
            parte(referencia_externa="PVI-b"),
            parte(referencia_externa="PVI-a"),
        ]
    )
    assert estados(respuesta) == ["previsto", "rechazado", "previsto", "rechazado"]
    assert motivos(respuesta)[1] == "referencia_duplicada_en_lote"
    assert "0" in respuesta.partes[1].motivo.mensaje
    assert respuesta.partes[2].cod == "RS26.09/0773"


def test_f006_r7_unidad_postventa_que_no_es_de_la_obra() -> None:
    assert _rechazo(parte(unidad_postventa="0626.NOEXISTE")) == "unidad_postventa_no_encontrada"


def test_f006_r7_la_unidad_postventa_se_compara_sin_mayusculas() -> None:
    respuesta, _ = ejecutar([parte(unidad_postventa="0626.03portal 1.1.b")])
    assert respuesta.partes[0].filas["rcp"]["upvide"] == _UPV_B
    assert respuesta.partes[0].filas["rcp"]["cliide"] == 0


@pytest.mark.parametrize("tipo", ["0009", "0005"])
def test_f006_r7_tipo_inexistente_o_de_baja(tipo: str) -> None:
    assert _rechazo(parte(tipo=tipo)) == "tipo_no_valido"


def test_f006_r7_clase_inexistente() -> None:
    assert _rechazo(parte(clase="0009")) == "clase_no_valida"


def test_f006_r7_tipo_y_clase_informados_van_a_rcp() -> None:
    respuesta, _ = ejecutar([parte(tipo="0003", clase="0003")])
    rcp = respuesta.partes[0].filas["rcp"]
    assert (rcp["trcpide"], rcp["rcpide"]) == (3, 3)
    respuesta, _ = ejecutar()
    rcp = respuesta.partes[0].filas["rcp"]
    assert (rcp["trcpide"], rcp["rcpide"]) == (2, 0)


@pytest.mark.parametrize("oficio", ["0077", "0098", "0099"])
def test_f006_r8_oficio_inexistente_de_baja_o_fuera_de_la_obra(oficio: str) -> None:
    assert _rechazo(parte(oficio=oficio, intervinientes=[])) == "oficio_no_esta_en_la_obra"


@pytest.mark.parametrize(
    "interviniente",
    [{"oficio": "0099"}, {"oficio": "0039", "proveedor": "9999"}, {"oficio": "0090", "proveedor": "1"}],
)
def test_f006_r8_interviniente_que_no_esta_en_la_obra(interviniente: dict[str, Any]) -> None:
    assert _rechazo(parte(intervinientes=[interviniente])) == "interviniente_no_esta_en_la_obra"


def test_f006_r8_interviniente_ambiguo_sin_proveedor() -> None:
    assert _rechazo(parte(intervinientes=[{"oficio": "0070"}])) == "interviniente_ambiguo"


def test_f006_r8_con_proveedor_deja_de_ser_ambiguo() -> None:
    respuesta, _ = ejecutar([parte(intervinientes=[{"oficio": "0070", "proveedor": "2002"}])])
    assert [f["obrofcide"] for f in respuesta.partes[0].filas["rcpint"]] == [2201]


def test_f006_r8_filas_identicas_se_resuelven_por_la_menor_pos_con_aviso() -> None:
    respuesta, _ = ejecutar([parte(intervinientes=[{"oficio": "0080"}])])
    assert [f["obrofcide"] for f in respuesta.partes[0].filas["rcpint"]] == [2300]
    assert any("2300" in aviso for aviso in respuesta.partes[0].avisos)


def test_f006_r8_un_pos_nulo_cuenta_como_cero_al_desempatar() -> None:
    respuesta, _ = ejecutar([parte(intervinientes=[{"oficio": "0085"}])])
    assert [f["obrofcide"] for f in respuesta.partes[0].filas["rcpint"]] == [2310]


def test_f006_r8_a_igual_pos_desempata_el_menor_ide() -> None:
    respuesta, _ = ejecutar([parte(intervinientes=[{"oficio": "0086"}])])
    assert [f["obrofcide"] for f in respuesta.partes[0].filas["rcpint"]] == [2401]


def test_f006_r8_un_interviniente_con_una_sola_fila_no_avisa() -> None:
    respuesta, _ = ejecutar()
    assert respuesta.partes[0].avisos == [
        aviso for aviso in respuesta.partes[0].avisos if "DRY-RUN" in aviso
    ]
    assert len(respuesta.partes[0].avisos) == 1


def test_f006_r8_un_oficio_sin_proveedor_en_la_obra_se_resuelve() -> None:
    respuesta, _ = ejecutar([parte(intervinientes=[{"oficio": "0090"}])])
    assert [f["obrofcide"] for f in respuesta.partes[0].filas["rcpint"]] == [2500]


def test_f006_r8_el_mismo_obrofc_dos_veces() -> None:
    dos = [{"oficio": "0039"}, {"oficio": "0039", "proveedor": "1181"}]
    assert _rechazo(parte(intervinientes=dos)) == "interviniente_repetido"
    respuesta, _ = ejecutar([parte(intervinientes=dos)])
    assert "(obrofc 2173)" in respuesta.partes[0].motivo.mensaje


def test_f006_r8_oficio_del_parte_fuera_de_los_intervinientes_solo_avisa() -> None:
    respuesta, _ = ejecutar([parte(oficio="0090")])
    assert estados(respuesta) == ["previsto"]
    assert respuesta.partes[0].filas["rcp"]["ofcide"] == 90
    assert any("0090" in aviso for aviso in respuesta.partes[0].avisos)
    respuesta, _ = ejecutar([parte()])
    assert not any("intervinientes" in aviso for aviso in respuesta.partes[0].avisos)


def test_f006_r8_causante_y_varios_intervinientes() -> None:
    respuesta, _ = ejecutar(
        [parte(intervinientes=[{"oficio": "0039", "causante": True}, {"oficio": "0090"}])]
    )
    assert [(f["obrofcide"], f["cauave"]) for f in respuesta.partes[0].filas["rcpint"]] == [
        (2173, 1), (2500, 0),
    ]


# --- R9: dry-run --------------------------------------------------------------


def test_f006_r9_el_dry_run_no_abre_transacciones_y_numera_en_provisional() -> None:
    respuesta, repo = ejecutar(
        [
            parte(),
            parte(referencia_externa="PVI-X", unidad_postventa="0626.NOEXISTE"),
            parte(
                referencia_externa="PVI-2",
                intervinientes=[{"oficio": "0039"}, {"oficio": "0090"}],
            ),
            parte(referencia_externa="PVI-3", intervinientes=[]),
        ]
    )
    assert repo.transacciones == []
    assert (respuesta.committed, respuesta.dry_run) == (False, True)
    assert estados(respuesta) == ["previsto", "rechazado", "previsto", "previsto"]
    uno, _, dos, tres = respuesta.partes
    assert [uno.cod, dos.cod, tres.cod] == ["RS26.09/0772", "RS26.09/0773", "RS26.09/0774"]
    assert [uno.ide, dos.ide, tres.ide] == [2900001, 2900002, 2900003]
    assert [p.filas["rcp"]["pos"] for p in (uno, dos, tres)] == [1408064, 1408128, 1408192]
    assert [f["ide"] for f in uno.filas["rcpint"]] == [25405]
    assert [f["ide"] for f in dos.filas["rcpint"]] == [25406, 25407]
    assert tres.filas["rcpint"] == []
    assert [p.filas["conext"]["ide"] for p in (uno, dos, tres)] == [56286, 56287, 56288]
    assert [p.filas["log"]["ide"] for p in (uno, dos, tres)] == [8488889, 8488890, 8488891]
    assert all(any("se reservan de nuevo" in a for a in p.avisos) for p in (uno, dos, tres))
    assert respuesta.resumen.model_dump() == {
        "creados": 0, "idempotentes": 0, "previstos": 3, "rechazados": 1, "no_procesados": 0,
    }
    # Numeración provisional leída UNA vez, sin bloqueo, y con el prefijo del mes.
    assert sorted(repo.peeks) == sorted(("ruesma", t) for t in ("con", "rcpint", "conext", "log"))
    assert [c for c in repo.consultadas if c[0] == "ultimo_cod"] == [
        ("ultimo_cod", [1, 708, "RS26.09/[0-9][0-9][0-9][0-9]"], None)
    ]
    assert [c[0] for c in repo.consultadas].count("pos_sin_bloqueo") == 1


def test_f006_r9_las_filas_del_preview_son_las_cinco_completas() -> None:
    respuesta, _ = ejecutar()
    filas = respuesta.partes[0].filas
    assert set(filas) == {"con", "rcp", "rcpint", "conext", "log"}
    assert filas["con"] == {
        "ide": 2900001, "emp": 1, "tip": 708, "subtip": 0, "cod": "RS26.09/0772",
        "res": "Fisura en tabique", "fec": 20260924, "tex": None, "cee": 0, "est": 1,
        "fecbaj": 0, "tiemod": pytest.approx(46289.844097, abs=1e-6), "ico": "", "delo": "",
        "del": "", "obr": "", "doc": "", "serie": 0, "hor": 0,
    }
    assert filas["rcp"]["hor"] == 221530 and filas["log"]["hor"] == 221530
    assert filas["rcp"]["cliide"] == 2811575 and filas["rcp"]["recide"] == 2811576
    assert filas["rcp"]["rcptip"] == 1 and filas["rcp"]["ofcide"] == 39
    assert filas["log"]["usu"] == "prueba"
    assert filas["conext"]["valt"] == "PVI-1"


def test_f006_r9_sin_cod_previo_en_el_mes_empieza_en_0001() -> None:
    respuesta, _ = ejecutar(repo=RepositorioDoble({"ultimo_cod": [(None,)]}))
    assert respuesta.partes[0].cod == "RS26.09/0001"


def test_f006_r12_dry_run_con_la_numeracion_agotada() -> None:
    respuesta, _ = ejecutar(
        [parte(), parte(referencia_externa="PVI-2")],
        repo=RepositorioDoble({"ultimo_cod": [("RS26.09/9998",)]}),
    )
    assert estados(respuesta) == ["previsto", "rechazado"]
    assert motivos(respuesta) == [None, "numeracion_agotada"]


# --- R15: idempotencia --------------------------------------------------------


def test_f006_r15_dry_run_idempotente_sin_numerar() -> None:
    repo = RepositorioDoble({"referencia": [(2811304, "RS26.08/0169", _UPV)]})
    respuesta, _ = ejecutar(repo=repo)
    unico = respuesta.partes[0]
    assert (unico.estado, unico.ide, unico.cod, unico.filas) == (
        "idempotente", 2811304, "RS26.08/0169", {},
    )
    assert ("referencia", ["RCPCLI", "PVI-1", 708, 1], 1000) in repo.consultadas
    assert repo.peeks == []
    assert respuesta.resumen.idempotentes == 1


@pytest.mark.parametrize(
    "encontrados",
    [
        [(2811304, "RS26.08/0169", _UPV_B)],
        [(2811304, "RS26.08/0169", None)],
        [(2811304, "RS26.08/0169", _UPV), (2811305, "RS26.08/0170", _UPV)],
    ],
)
def test_f006_r15_referencia_en_conflicto(encontrados: list) -> None:
    respuesta, _ = ejecutar(repo=RepositorioDoble({"referencia": encontrados}))
    assert motivos(respuesta) == ["referencia_en_conflicto"]
    # El mensaje nombra los partes que ya la tienen, por su código.
    assert "RS26.08/0169" in respuesta.partes[0].motivo.mensaje


def test_f006_r15_commit_idempotente_dentro_de_la_transaccion() -> None:
    repo = RepositorioDoble(referencia_en_transaccion=[(2811304, "RS26.08/0169", _UPV)])
    respuesta, _ = ejecutar(repo=repo, commit=True)
    assert estados(respuesta) == ["idempotente"]
    assert respuesta.partes[0].ide == 2811304
    assert [c[0] for c in repo.cursores[0].ejecutadas] == ["referencia"]
    assert "referencia" not in [c[0] for c in repo.consultadas]  # en commit, solo dentro
    assert respuesta.committed is False


def test_f006_r15_commit_con_referencia_en_conflicto() -> None:
    repo = RepositorioDoble(referencia_en_transaccion=[(2811304, "RS26.08/0169", _UPV_B)])
    respuesta, _ = ejecutar([parte(), parte(referencia_externa="PVI-2")], repo=repo, commit=True)
    assert motivos(respuesta)[0] == "referencia_en_conflicto"


# --- R11-R14: commit, una transacción por parte ------------------------------

_ORDEN_E = [
    "referencia", "reservar_cod", "ide_con", "pos_rcp", "ide_rcpint", "ide_conext", "ide_log",
    "revalidar_upv", "revalidar_obrofc",
    "insert_con", "insert_rcp", "insert_rcpint", "insert_conext", "insert_log",
    "releer_con", "releer_rcp", "releer_rcpint", "releer_conext", "releer_log",
]


def test_f006_r11_commit_una_transaccion_por_parte_con_los_applocks_en_orden() -> None:
    respuesta, repo = ejecutar(
        [parte(), parte(referencia_externa="XYZ"), parte(referencia_externa="PVI-2")], commit=True
    )
    assert estados(respuesta) == ["creado", "rechazado", "creado"]
    assert len(repo.transacciones) == 2
    for transaccion in repo.transacciones:
        assert transaccion == {
            "database": "ruesma",
            "timeout_seconds": 30,
            "applock_resources": [
                "SIGRID_REFEXT_708", "SIGRID_SERIE_708", "SIGRID_IDE_con", "SIGRID_POS_rcp",
                "SIGRID_IDE_rcpint", "SIGRID_IDE_conext", "SIGRID_IDE_log",
            ],
            "applock_timeout_ms": 10000,
            "max_retries": 3,
        }
    assert APPLOCKS == tuple(repo.transacciones[0]["applock_resources"])
    assert (respuesta.committed, respuesta.dry_run) == (True, False)
    assert respuesta.resumen.creados == 2
    assert repo.peeks == []
    assert not {"referencia", "ultimo_cod", "pos_sin_bloqueo"} & {c[0] for c in repo.consultadas}


def test_f006_r11_work_ejecuta_e1_a_e14_en_orden() -> None:
    respuesta, repo = ejecutar(commit=True)
    cursor = repo.cursores[0]
    assert [c[0] for c in cursor.ejecutadas] == _ORDEN_E
    assert cursor.connection.timeout == 30
    params = {clave: valores for clave, valores in cursor.ejecutadas}
    assert params["referencia"] == ["RCPCLI", "PVI-1", 708, 1]
    assert params["reservar_cod"] == [1, 708, "RS26.09/[0-9][0-9][0-9][0-9]"]
    assert params["revalidar_upv"] == [_UPV, _OBRA]
    assert params["revalidar_obrofc"] == [2173, _OBRA]
    filas = respuesta.partes[0].filas
    assert params["insert_con"] == [filas["con"][c] for c in CON_COLUMNAS]
    assert params["insert_log"] == [filas["log"][c] for c in LOG_COLUMNAS]
    assert filas["con"]["cod"] == "RS26.09/0772" and filas["con"]["ide"] == 2900001
    assert params["releer_con"] == [1, 708, "RS26.09/0772"]
    assert params["releer_rcp"] == [2900001]
    assert params["releer_rcpint"] == [2900001]
    assert params["releer_conext"] == [2900001, "RCPCLI"]
    assert params["releer_log"] == [8488889]
    unico = respuesta.partes[0]
    assert (unico.estado, unico.ide, unico.cod, unico.motivo) == (
        "creado", 2900001, "RS26.09/0772", None,
    )
    assert (respuesta.committed, respuesta.resumen.creados) == (True, 1)


def test_f006_r11_sin_intervinientes_no_se_toca_rcpint_mas_que_para_releer() -> None:
    _, repo = ejecutar([parte(intervinientes=[])], commit=True)
    orden = [c[0] for c in repo.cursores[0].ejecutadas]
    assert "ide_rcpint" not in orden and "insert_rcpint" not in orden
    assert "revalidar_obrofc" not in orden and "releer_rcpint" in orden


def test_f006_r11_varios_intervinientes_se_revalidan_e_insertan_todos() -> None:
    _, repo = ejecutar(
        [parte(intervinientes=[{"oficio": "0039"}, {"oficio": "0090"}])], commit=True
    )
    ejecutadas = repo.cursores[0].ejecutadas
    assert [p for c, p in ejecutadas if c == "revalidar_obrofc"] == [[2173, _OBRA], [2500, _OBRA]]
    assert [p[0] for c, p in ejecutadas if c == "insert_rcpint"] == [25405, 25406]


def test_f006_r13_una_colision_repite_la_transaccion_entera_con_numeros_nuevos() -> None:
    ahora = Ahora()
    repo = RepositorioDoble(
        reservas={
            "reservar_cod": lambda intento: ("RS26.09/0771",) if intento == 1 else ("RS26.09/0772",),
            "ide_con": lambda intento: (2900000 + intento,),
            "pos_rcp": lambda intento: (1408000 + 64 * intento,),
            "ide_log": lambda intento: (8488888 + intento,),
        },
        fallos={"insert_con": lambda intento: IntegrityError("con_emptipcod") if intento == 1 else None},
    )
    respuesta, _ = ejecutar(repo=repo, ahora=ahora, commit=True)
    assert len(repo.cursores) == 2
    unico = respuesta.partes[0]
    assert (unico.estado, unico.cod, unico.ide) == ("creado", "RS26.09/0773", 2900002)
    assert unico.filas["rcp"]["pos"] == 1408128
    assert unico.filas["log"]["ide"] == 8488890
    assert unico.filas["log"]["cod"] == "RS26.09/0773"
    assert [c[0] for c in repo.cursores[1].ejecutadas] == _ORDEN_E
    assert ahora.llamadas == 1  # R16: los sellos no se recalculan en el reintento


def test_f006_r13_colision_persistente_rechaza_el_parte_y_el_lote_sigue() -> None:
    repo = RepositorioDoble(
        fallos={"insert_rcp": lambda intento: IntegrityError("dup") if len(repo.cursores) <= 4 else None}
    )
    respuesta, _ = ejecutar([parte(), parte(referencia_externa="PVI-2")], repo=repo, commit=True)
    assert estados(respuesta) == ["rechazado", "creado"]
    assert motivos(respuesta)[0] == "colision_de_clave"
    assert len(repo.cursores) == 5


@pytest.mark.parametrize("tabla", ["con", "rcp", "rcpint", "conext", "log"])
def test_f006_r14_una_relectura_que_no_cuadra_revierte(tabla: str) -> None:
    repo = RepositorioDoble(forzar={f"releer_{tabla}": (2,)})
    respuesta, _ = ejecutar([parte(), parte(referencia_externa="PVI-2")], repo=repo, commit=True)
    assert motivos(respuesta) == ["filas_afectadas_inesperadas"] * 2
    assert tabla in respuesta.partes[0].motivo.mensaje


def test_f006_r14_una_relectura_que_falta_revierte() -> None:
    repo = RepositorioDoble(forzar={"releer_con": (0,)})
    respuesta, _ = ejecutar(repo=repo, commit=True)
    assert motivos(respuesta) == ["filas_afectadas_inesperadas"]


@pytest.mark.parametrize("clave", ["revalidar_upv", "revalidar_obrofc"])
def test_f006_r14_la_revalidacion_para_antes_de_insertar(clave: str) -> None:
    repo = RepositorioDoble(forzar={clave: (0,)})
    respuesta, _ = ejecutar(repo=repo, commit=True)
    assert motivos(respuesta) == ["filas_afectadas_inesperadas"]
    assert not any(c.startswith("insert_") for c, _ in repo.cursores[0].ejecutadas)


def test_f006_r12_commit_con_la_numeracion_agotada() -> None:
    repo = RepositorioDoble(reservas={"reservar_cod": ("RS26.09/9999",)})
    respuesta, _ = ejecutar(repo=repo, commit=True)
    assert motivos(respuesta) == ["numeracion_agotada"]
    assert [c[0] for c in repo.cursores[0].ejecutadas] == ["referencia", "reservar_cod"]


def test_f006_r17_otro_error_de_escritura_rechaza_el_parte_y_el_lote_sigue() -> None:
    repo = RepositorioDoble(
        fallos={"insert_log": lambda intento: RuntimeError("timeout") if len(repo.cursores) == 1 else None}
    )
    respuesta, _ = ejecutar([parte(), parte(referencia_externa="PVI-2")], repo=repo, commit=True)
    assert estados(respuesta) == ["rechazado", "creado"]
    assert motivos(respuesta)[0] == "error_de_escritura"
    assert "RuntimeError" in respuesta.partes[0].motivo.mensaje
    assert len(repo.cursores) == 2  # un error que no es de clave NO se reintenta


def test_f006_r10_commit_todo_rechazado_no_es_committed() -> None:
    respuesta, repo = ejecutar([parte(referencia_externa="XYZ")], commit=True)
    assert (respuesta.committed, respuesta.dry_run) == (False, False)
    assert repo.transacciones == []


# --- R17: presupuesto de tiempo ----------------------------------------------


def test_f006_r17_pasado_el_presupuesto_no_se_empiezan_mas_partes() -> None:
    reloj = Reloj([0.0, 10.0, 150.0, 150.5])
    respuesta, repo = ejecutar(
        [parte(), parte(referencia_externa="PVI-2"), parte(referencia_externa="PVI-3"),
         parte(referencia_externa="PVI-4")],
        reloj=reloj,
        commit=True,
    )
    assert estados(respuesta) == ["creado", "creado", "no_procesado", "no_procesado"]
    assert motivos(respuesta)[2:] == ["presupuesto_de_tiempo_agotado"] * 2
    assert len(repo.transacciones) == 2
    assert respuesta.resumen.no_procesados == 2


def test_f006_r17_el_presupuesto_es_configurable() -> None:
    reloj = Reloj([0.0, 5.0, 6.0])
    respuesta, _ = ejecutar(
        [parte(), parte(referencia_externa="PVI-2")],
        reloj=reloj,
        settings=SettingsDoble(sigrid_reclamacion_presupuesto_segundos=5),
    )
    assert estados(respuesta) == ["previsto", "no_procesado"]


# --- R16: sellos de tiempo ---------------------------------------------------


def test_f006_r16_un_sello_por_parte() -> None:
    ahora = Ahora()
    ejecutar([parte(), parte(referencia_externa="PVI-2")], ahora=ahora)
    assert ahora.llamadas == 2


# --- R19: nada de tar, gráficos ni otras tablas ------------------------------


def test_f006_r19_ninguna_sentencia_ejecutada_toca_tar_ni_pasa_a_pte() -> None:
    _, repo = ejecutar([parte(), parte(referencia_externa="PVI-2")], commit=True)
    for _clave, sql, _params in repo.sentencias_en_transaccion:
        assert "dbo.tar" not in sql and "dbo.gra" not in sql
        assert not sql.startswith(("UPDATE", "DELETE", "MERGE"))
    insertadas = {c for c, _, _ in repo.sentencias_en_transaccion if c.startswith("insert_")}
    assert insertadas == {"insert_con", "insert_rcp", "insert_rcpint", "insert_conext", "insert_log"}


# --- R20: trazas -------------------------------------------------------------


def _trazas(caplog: pytest.LogCaptureFixture) -> list[dict[str, Any]]:
    return [
        json.loads(r.getMessage())
        for r in caplog.records
        if r.name == "application.use_cases.create_partes_reclamacion_use_case"
    ]


def test_f006_r20_una_traza_por_lote_y_una_por_parte_sin_descripciones(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    ejecutar(
        [
            parte(descripcion="SECRETO CORTO", descripcion_larga="SECRETO LARGO", ubicacion="SECRETA"),
            parte(referencia_externa="XYZ-Ñ", descripcion="OTRO SECRETO"),
        ],
        reloj=Reloj([100.0, 100.0, 100.0, 101.23456]),
        commit=True,
        usu="muñoz",
    )
    trazas = _trazas(caplog)
    assert len(trazas) == 3
    lote = trazas[-1]
    assert lote["obra"] == "0626" and lote["usu"] == "muñoz" and lote["commit"] is True
    assert lote["resumen"] == {
        "creados": 1, "idempotentes": 0, "previstos": 0, "rechazados": 1, "no_procesados": 0,
    }
    assert lote["duracion_ms"] == 1234.6  # desde el arranque, en ms, con un decimal
    assert trazas[0] == {
        "endpoint": "sigrid/partes-reclamacion",
        "indice": 0,
        "referencia": "PVI-1",
        "estado": "creado",
        "codigo": None,
        "ide": 2900001,
        "cod": "RS26.09/0772",
    }
    assert trazas[1]["codigo"] == "referencia_no_permitida"
    todo = "".join(r.getMessage() for r in caplog.records)
    assert "SECRETO" not in todo and "SECRETA" not in todo
    # Legibles en los logs, sin escapar a \u00f1.
    assert '"usu": "muñoz"' in todo and '"referencia": "XYZ-Ñ"' in todo


def test_f006_r20_un_fallo_de_lote_tambien_deja_traza(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    fallo_de_lote(repo=RepositorioDoble({"obra": []}))
    (traza,) = _trazas(caplog)
    assert traza["resultado"] == "error" and traza["codigo"] == "obra_no_encontrada"


def test_f006_r20_una_excepcion_inesperada_tambien_deja_traza(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO)
    with pytest.raises(ValueError):
        ejecutar(repo=RepositorioDoble(truncar_en="upv"))
    (traza,) = _trazas(caplog)
    assert traza["resultado"] == "excepcion" and traza["codigo"] == "ValueError"


# --- Relojes por defecto -----------------------------------------------------


def test_f006_r16_por_defecto_se_sella_con_la_hora_utc_real() -> None:
    """Sin relojes inyectados: `time.monotonic` para el presupuesto y la hora
    UTC real (con zona) para los sellos."""
    import time

    from application.use_cases import create_partes_reclamacion_use_case as modulo

    caso = CreatePartesReclamacionUseCase(RepositorioDoble(), SettingsDoble())
    assert caso._reloj is time.monotonic
    antes = datetime.now(timezone.utc)
    sello = modulo._ahora_utc()
    assert sello.tzinfo is not None and sello.utcoffset().total_seconds() == 0
    assert antes <= sello <= datetime.now(timezone.utc)
    assert estados(caso.run(peticion())) == ["previsto"]
