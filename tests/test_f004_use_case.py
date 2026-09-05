# tests/test_f004_use_case.py
"""
F-004 · R6, R7, R9, R10, R12, R14, R15, R17 y R21: el caso de uso.

Sin red y sin base de datos: el repositorio y el cursor son dobles que graban
lo que se les pide. El doble del cursor NO revierte nada (el `ROLLBACK` es del
repositorio real, `run_in_write_transaction`): lo que se comprueba aqui es que
el caso de uso deja subir el fallo en vez de tragarselo, y que no ejecuta lo
que viene despues.
"""
from __future__ import annotations

import base64
import hashlib
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

import pytest

from application.use_cases.attach_concepto_grafico_use_case import (
    AttachConceptoGraficoUseCase,
)
from domain.models.concepto_grafico_models import (
    AttachConceptoGraficoRequest,
    ConceptoGraficoError,
)

_PDF = b"%PDF-1.4 el parte firmado"
_SHA_PDF = hashlib.sha256(_PDF).hexdigest()
_B64 = base64.b64encode(_PDF).decode("ascii")

_OTRO_PDF = b"%PDF-1.4 otro parte firma"  # mismo tamano, distinto contenido
assert len(_OTRO_PDF) == len(_PDF)

_IDE_DOCUMENTAL = 357208
_IDE_NEGOCIO = 296221
_IDE_ENLACE = 296661


# --- Dobles ------------------------------------------------------------------


@dataclass
class SettingsDoble:
    sigrid_document_write_database: str = "ruesma_rep"
    sigrid_document_write_enabled: bool = True
    sigrid_domain_write_enabled: bool = True
    sql_server_write_username: str | None = "usuario_de_mentira"
    sql_server_write_password: str | None = "no-es-una-credencial"
    allowed_write_databases: list[str] = field(default_factory=lambda: ["ruesma"])
    sigrid_document_max_bytes: int = 10485760
    sigrid_document_allowed_magic: list[str] = field(default_factory=lambda: ["%PDF-"])
    sigrid_document_allowed_contip: list[int] = field(default_factory=lambda: [708])
    sigrid_document_allowed_gratipide: list[int] = field(default_factory=lambda: [35])
    sigrid_document_write_timeout_seconds: int = 120
    applock_timeout_ms: int = 10000
    domain_write_max_retries: int = 3
    default_query_timeout_seconds: int = 30
    max_allowed_rows: int = 1000


def _clave_de(sql: str) -> str:
    if "dbo.con WHERE ide" in sql:
        return "concepto"
    if "dbo.auxgra" in sql:
        return "clase"
    if "dbo.usu" in sql:
        return "usuario"
    if "MAX(pos)" in sql:
        return "pos"
    if "DATALENGTH" in sql:
        return "idempotencia"
    if "d.ide IS NULL" in sql:
        return "huerfanas"
    if "+ 1 FROM [ruesma_rep].dbo.gra" in sql:
        return "reserva_documental"
    if "+ 1 FROM dbo.gra" in sql:
        return "reserva_negocio"
    if "+ 1 FROM dbo.rcg" in sql:
        return "reserva_enlace"
    if "COUNT(*) FROM [ruesma_rep].dbo.gra" in sql:
        return "relectura_documental"
    if "COUNT(*) FROM dbo.gra" in sql:
        return "relectura_negocio"
    if "COUNT(*) FROM dbo.rcg" in sql:
        return "relectura_enlace"
    if "INSERT INTO [ruesma_rep].dbo.gra" in sql:
        return "insert_documental"
    if "INSERT INTO dbo.gra" in sql:
        return "insert_negocio"
    if "INSERT INTO dbo.rcg" in sql:
        return "insert_enlace"
    raise AssertionError(f"sentencia inesperada: {sql}")


_LECTURAS_FELICES: dict[str, list[tuple[Any, ...]]] = {
    "concepto": [(2811179, 708, 1, "RS26.08/0123", "Sellado de falsos techos")],
    "clase": [(35, "PV002", "POSTVENTA:Fotos Reparaciones", 0, "UPV,RCP,TAR")],
    "usuario": [("aechevarria",)],
    "pos": [(64, 0)],
    "idempotencia": [],
    "huerfanas": [],
}

_RESERVAS_FELICES: dict[str, tuple[Any, ...]] = {
    "reserva_documental": (_IDE_DOCUMENTAL,),
    "reserva_negocio": (_IDE_NEGOCIO,),
    "reserva_enlace": (_IDE_ENLACE,),
    "relectura_documental": (1,),
    "relectura_negocio": (1,),
    "relectura_enlace": (1,),
}


class CursorDoble:
    def __init__(
        self,
        respuestas: dict[str, tuple[Any, ...]],
        idempotencia: list[tuple[Any, ...]],
        fallar_en: str | None = None,
    ) -> None:
        self.respuestas = respuestas
        self.idempotencia = idempotencia
        self.fallar_en = fallar_en
        self.ejecutadas: list[tuple[str, list[Any]]] = []
        self._ultima = ""
        self.connection = SimpleNamespace(timeout=None)

    def execute(self, sql: str, *params: Any) -> None:
        clave = _clave_de(sql)
        self.ejecutadas.append((clave, list(params)))
        self._ultima = clave
        if self.fallar_en == clave:
            raise RuntimeError(f"el motor rechazo {clave}")

    def fetchone(self) -> tuple[Any, ...]:
        return self.respuestas[self._ultima]

    def fetchall(self) -> list[tuple[Any, ...]]:
        return self.idempotencia


class RepositorioDoble:
    def __init__(
        self,
        lecturas: dict[str, list[tuple[Any, ...]]] | None = None,
        reservas: dict[str, tuple[Any, ...]] | None = None,
        idempotencia_en_transaccion: list[tuple[Any, ...]] | None = None,
        fallar_en: str | None = None,
        truncar_en: str | None = None,
    ) -> None:
        self.truncar_en = truncar_en
        self.topes: list[tuple[str, int | None]] = []
        self.lecturas = dict(_LECTURAS_FELICES if lecturas is None else lecturas)
        self.reservas = dict(_RESERVAS_FELICES if reservas is None else reservas)
        self.idempotencia_en_transaccion = idempotencia_en_transaccion or []
        self.fallar_en = fallar_en
        self.consultadas: list[tuple[str, list[Any]]] = []
        self.peticiones_peek: list[tuple[str, str]] = []
        self.transacciones: list[dict[str, Any]] = []
        self.cursor: CursorDoble | None = None

    def execute_read_query(self, request: Any) -> tuple[list[str], list[tuple[Any, ...]], bool]:
        clave = _clave_de(request.sql)
        self.consultadas.append((clave, list(request.parameters)))
        self.topes.append((clave, getattr(request, "max_rows", None)))
        return [], list(self.lecturas.get(clave, [])), clave == self.truncar_en

    def peek_next_ide(self, *, database: str, table: str) -> int:
        self.peticiones_peek.append((database, table))
        return {"ruesma_rep": _IDE_DOCUMENTAL, "gra": _IDE_NEGOCIO}.get(
            database if database != "ruesma" else table, _IDE_ENLACE
        )

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
        self.cursor = CursorDoble(
            self.reservas, self.idempotencia_en_transaccion, self.fallar_en
        )
        return work(self.cursor)


def peticion(**cambios: object) -> AttachConceptoGraficoRequest:
    base = {
        "database": "ruesma",
        "conide": 2811179,
        "contip": 708,
        "gratipide": 35,
        "res": "PRUEBA API - BORRAR",
        "nom": "parte.pdf",
        "usu": "aechevarria",
        "contenido_base64": _B64,
    }
    return AttachConceptoGraficoRequest.model_validate({**base, **cambios})


def ejecutar(repositorio: RepositorioDoble | None = None, settings=None, **cambios: object):
    repositorio = repositorio or RepositorioDoble()
    caso = AttachConceptoGraficoUseCase(repositorio, settings or SettingsDoble())
    return caso.run(peticion(**cambios)), repositorio


def fallo(repositorio: RepositorioDoble | None = None, settings=None, **cambios: object) -> str:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        ejecutar(repositorio, settings, **cambios)
    return excinfo.value.codigo


# --- R6 y R10: los guards de configuracion, antes de tocar la red ------------


def test_f004_r6_sin_base_documental_el_endpoint_esta_apagado() -> None:
    repositorio = RepositorioDoble()
    assert (
        fallo(repositorio, SettingsDoble(sigrid_document_write_database=""))
        == "escritura_documental_deshabilitada"
    )
    assert repositorio.consultadas == []


def test_f004_r6_sin_base_documental_tampoco_hay_dry_run() -> None:
    """Sin base documental no hay preview honesto de `ide` ni de idempotencia."""
    assert (
        fallo(settings=SettingsDoble(sigrid_document_write_database=""), commit=False)
        == "escritura_documental_deshabilitada"
    )


def test_f004_r6_una_base_de_negocio_fuera_de_la_lista_se_rechaza() -> None:
    repositorio = RepositorioDoble()
    assert fallo(repositorio, database="master") == "base_de_datos_no_permitida"
    assert repositorio.consultadas == []


@pytest.mark.parametrize("nombre", ["ruesma_rep", "RUESMA_REP", " ruesma_rep "])
def test_f004_r6_la_documental_no_puede_ser_la_base_de_la_conexion(nombre: str) -> None:
    """Aunque alguien la metiera en ALLOWED_WRITE_DATABASES: se escribe en ella
    por nombre de tres partes, nunca conectandose."""
    settings = SettingsDoble(allowed_write_databases=["ruesma", "ruesma_rep"])
    assert fallo(settings=settings, database=nombre) == "base_de_datos_no_permitida"


@pytest.mark.parametrize(
    "settings",
    [
        SettingsDoble(sigrid_domain_write_enabled=False),
        SettingsDoble(sigrid_document_write_enabled=False),
        SettingsDoble(sql_server_write_username=None),
        SettingsDoble(sql_server_write_password=None),
    ],
)
def test_f004_r10_el_commit_exige_las_tres_llaves(settings: SettingsDoble) -> None:
    repositorio = RepositorioDoble()
    assert (
        fallo(repositorio, settings, commit=True) == "escritura_documental_deshabilitada"
    )
    assert repositorio.transacciones == []


def test_f004_r10_sin_las_llaves_el_dry_run_sigue_funcionando() -> None:
    """Solo el commit las exige: el dry-run es 100 % lectura."""
    respuesta, _ = ejecutar(
        settings=SettingsDoble(sigrid_document_write_enabled=False), commit=False
    )
    assert respuesta.dry_run is True


# --- R7: las validaciones contra el ERP, con lecturas ------------------------


def test_f004_r7_un_concepto_que_no_existe_se_rechaza() -> None:
    repositorio = RepositorioDoble(lecturas={**_LECTURAS_FELICES, "concepto": []})
    assert fallo(repositorio) == "concepto_no_encontrado"


def test_f004_r7_un_concepto_de_otro_tipo_se_rechaza() -> None:
    repositorio = RepositorioDoble(
        lecturas={**_LECTURAS_FELICES, "concepto": [(2811179, 14, 1, "AC26/1", "Albaran")]}
    )
    assert fallo(repositorio) == "tipo_de_concepto_no_coincide"


def test_f004_r7_una_clase_de_grafico_dada_de_baja_se_rechaza() -> None:
    repositorio = RepositorioDoble(
        lecturas={**_LECTURAS_FELICES, "clase": [(35, "PV002", "x", 20250101, "UPV")]}
    )
    assert fallo(repositorio) == "clase_de_grafico_no_permitida"


def test_f004_r7_una_clase_de_grafico_que_no_existe_se_rechaza() -> None:
    repositorio = RepositorioDoble(lecturas={**_LECTURAS_FELICES, "clase": []})
    assert fallo(repositorio) == "clase_de_grafico_no_permitida"


def test_f004_r7_un_usuario_que_no_existe_se_rechaza() -> None:
    repositorio = RepositorioDoble(lecturas={**_LECTURAS_FELICES, "usuario": []})
    assert fallo(repositorio) == "usuario_no_valido"


def test_f004_r7_el_emp_sale_del_concepto_no_de_la_peticion() -> None:
    repositorio = RepositorioDoble(
        lecturas={**_LECTURAS_FELICES, "concepto": [(2811179, 708, 28, "RS26.08/0123", "x")]}
    )
    respuesta, _ = ejecutar(repositorio)
    assert respuesta.concepto.emp == 28
    assert respuesta.grafico.emp == 28


def test_f004_r7_el_guard_del_fichero_se_aplica_antes_de_leer_el_erp() -> None:
    """Un PNG no llega ni a preguntar por el concepto."""
    repositorio = RepositorioDoble()
    png = base64.b64encode(b"\x89PNG\r\n\x1a\n datos").decode("ascii")
    assert fallo(repositorio, contenido_base64=png) == "tipo_de_fichero_no_permitido"
    assert repositorio.consultadas == []


# --- R9: dry-run, solo lecturas ---------------------------------------------


def test_f004_r9_el_dry_run_no_abre_ninguna_transaccion_de_escritura() -> None:
    respuesta, repositorio = ejecutar()
    assert repositorio.transacciones == []
    assert respuesta.committed is False
    assert respuesta.dry_run is True
    assert respuesta.filas_afectadas == 0
    assert respuesta.idempotente is False


def test_f004_r9_el_dry_run_hace_las_seis_lecturas_en_orden() -> None:
    _respuesta, repositorio = ejecutar()
    assert [clave for clave, _ in repositorio.consultadas] == [
        "concepto", "clase", "usuario", "pos", "idempotencia", "huerfanas",
    ]


def test_f004_r9_el_dry_run_previsualiza_los_tres_ide_y_avisa_de_que_son_provisionales() -> None:
    respuesta, repositorio = ejecutar()
    assert repositorio.peticiones_peek == [
        ("ruesma_rep", "gra"), ("ruesma", "gra"), ("ruesma", "rcg"),
    ]
    assert respuesta.grafico.ide_documental == _IDE_DOCUMENTAL
    assert respuesta.grafico.ide_negocio == _IDE_NEGOCIO
    assert respuesta.enlace.ide == _IDE_ENLACE
    assert respuesta.enlace.gra == _IDE_NEGOCIO
    assert any("provisional" in aviso for aviso in respuesta.avisos)


def test_f004_r9_el_preview_ensena_las_dos_filas_completas_sin_el_binario() -> None:
    respuesta, _ = ejecutar()
    assert len(respuesta.grafico.fila_documental) == 29
    assert len(respuesta.grafico.fila_negocio) == 29
    assert respuesta.grafico.fila_documental["ima"] == len(_PDF)
    assert respuesta.grafico.fila_negocio["ima"] is None
    assert respuesta.grafico.fila_documental["cod"] == respuesta.grafico.fila_negocio["cod"]
    assert respuesta.grafico.sha256 == _SHA_PDF
    assert respuesta.grafico.bytes == len(_PDF)
    assert respuesta.enlace.pos == 64


def test_f004_r17_las_lecturas_de_candidatos_piden_el_tope_maximo_de_filas() -> None:
    """
    Sin `max_rows` el tope real era `DEFAULT_MAX_ROWS` (200): un concepto con
    mas de 200 binarios del MISMO tamano dejaria fuera al candidato bueno y la
    idempotencia fallaria en silencio, duplicando el adjunto.
    """
    _respuesta, repositorio = ejecutar()
    topes = dict(repositorio.topes)
    assert topes["idempotencia"] == SettingsDoble().max_allowed_rows
    assert topes["huerfanas"] == SettingsDoble().max_allowed_rows
    assert topes["concepto"] is None  # las demas no cambian: devuelven 1 fila


@pytest.mark.parametrize("clave", ["idempotencia", "huerfanas"])
def test_f004_r17_una_lectura_truncada_para_el_adjunto_en_vez_de_duplicarlo(
    clave: str,
) -> None:
    """Truncar es no haber visto todos los candidatos: adjuntar seria adjuntar a
    ciegas. No hay codigo de R3 que encaje, asi que sube un `ValueError`."""
    repositorio = RepositorioDoble(truncar_en=clave)
    with pytest.raises(ValueError) as excinfo:
        ejecutar(repositorio)
    assert not isinstance(excinfo.value, ConceptoGraficoError)
    assert "truncad" in str(excinfo.value).lower()
    assert repositorio.transacciones == []


def test_f004_r9_la_posicion_sale_de_max_pos_mas_64() -> None:
    repositorio = RepositorioDoble(lecturas={**_LECTURAS_FELICES, "pos": [(192, 2)]})
    respuesta, _ = ejecutar(repositorio)
    assert respuesta.enlace.pos == 192


# --- R11 y R12: la transaccion -----------------------------------------------


def test_f004_r12_el_commit_toma_los_tres_applock_y_el_timeout_de_configuracion() -> None:
    _respuesta, repositorio = ejecutar(commit=True)
    transaccion = repositorio.transacciones[0]
    assert transaccion["database"] == "ruesma"
    assert transaccion["applock_resources"] == [
        "SIGRID_IDE_ruesma_rep_gra", "SIGRID_IDE_gra", "SIGRID_IDE_rcg",
    ]
    assert transaccion["timeout_seconds"] == 120
    assert transaccion["applock_timeout_ms"] == 10000
    assert transaccion["max_retries"] == 3


def test_f004_r11_el_trabajo_escribe_documental_negocio_y_enlace_en_ese_orden() -> None:
    respuesta, repositorio = ejecutar(commit=True)
    assert [clave for clave, _ in repositorio.cursor.ejecutadas] == [
        "idempotencia",
        "reserva_documental", "reserva_negocio", "reserva_enlace",
        "insert_documental", "insert_negocio", "insert_enlace",
        "relectura_documental", "relectura_negocio", "relectura_enlace",
    ]
    assert respuesta.committed is True
    assert respuesta.dry_run is False
    assert respuesta.filas_afectadas == 3


def test_f004_r12_el_enlace_usa_el_ide_reservado_de_negocio_sin_rederivarlo() -> None:
    respuesta, repositorio = ejecutar(commit=True)
    ejecutadas = dict(repositorio.cursor.ejecutadas)
    assert ejecutadas["insert_documental"][0] == _IDE_DOCUMENTAL
    assert ejecutadas["insert_negocio"][0] == _IDE_NEGOCIO
    assert ejecutadas["insert_enlace"] == [_IDE_ENLACE, 2811179, _IDE_NEGOCIO, 64, 0, 0, 0]
    assert respuesta.enlace.gra == _IDE_NEGOCIO


def test_f004_r11_las_dos_filas_insertadas_llevan_el_mismo_cod_y_el_mismo_emp() -> None:
    respuesta, repositorio = ejecutar(commit=True)
    ejecutadas = dict(repositorio.cursor.ejecutadas)
    documental = ejecutadas["insert_documental"]
    negocio = ejecutadas["insert_negocio"]
    assert documental[1] == negocio[1] == respuesta.grafico.cod   # cod
    assert documental[2] == negocio[2] == 1                       # emp
    assert documental[10] == _PDF                                 # ima documental
    assert negocio[10] is None                                    # ima negocio


def test_f004_r12_el_trabajo_fija_el_timeout_de_sentencia_en_la_conexion() -> None:
    """El timeout de `_connect` es de login: sin esto, una sentencia colgada se
    comeria los 230 s del balanceador."""
    _respuesta, repositorio = ejecutar(commit=True)
    assert repositorio.cursor.connection.timeout == 120


# --- R14 y R15: relectura y fallo -------------------------------------------


@pytest.mark.parametrize(
    "clave", ["relectura_documental", "relectura_negocio", "relectura_enlace"]
)
def test_f004_r14_si_una_relectura_no_devuelve_una_fila_se_revierte(clave: str) -> None:
    reservas = {**_RESERVAS_FELICES, clave: (0,)}
    repositorio = RepositorioDoble(reservas=reservas)
    assert fallo(repositorio, commit=True) == "filas_afectadas_inesperadas"


def test_f004_r15_un_fallo_en_el_segundo_insert_no_llega_al_tercero() -> None:
    repositorio = RepositorioDoble(fallar_en="insert_negocio")
    with pytest.raises(RuntimeError):
        ejecutar(repositorio, commit=True)
    claves = [clave for clave, _ in repositorio.cursor.ejecutadas]
    assert "insert_negocio" in claves
    assert "insert_enlace" not in claves
    assert "relectura_documental" not in claves


def test_f004_r15_el_caso_de_uso_no_se_traga_el_fallo_de_la_transaccion() -> None:
    """El ROLLBACK es del repositorio: capturarlo aqui lo dejaria sin hacer."""
    repositorio = RepositorioDoble(fallar_en="insert_documental")
    with pytest.raises(RuntimeError):
        ejecutar(repositorio, commit=True)


# --- R17: idempotencia por contenido ----------------------------------------


def test_f004_r17_el_mismo_documento_ya_colgado_no_se_escribe_otra_vez() -> None:
    repositorio = RepositorioDoble(
        lecturas={
            **_LECTURAS_FELICES,
            "idempotencia": [(_IDE_NEGOCIO, "202608181140392614.aechevarria", _IDE_ENLACE, _PDF)],
        }
    )
    respuesta, _ = ejecutar(repositorio, commit=True)
    assert respuesta.idempotente is True
    assert respuesta.ok is True
    assert respuesta.filas_afectadas == 0
    assert respuesta.committed is False
    assert respuesta.grafico.ide_negocio == _IDE_NEGOCIO
    assert respuesta.grafico.cod == "202608181140392614.aechevarria"
    assert respuesta.enlace.ide == _IDE_ENLACE
    assert repositorio.transacciones == []


def test_f004_r17_un_binario_del_mismo_tamano_pero_distinto_no_es_idempotente() -> None:
    """Por eso el sha256 se compara en Python: `DATALENGTH` solo acota."""
    repositorio = RepositorioDoble(
        lecturas={
            **_LECTURAS_FELICES,
            "idempotencia": [(_IDE_NEGOCIO, "otro.cod", _IDE_ENLACE, _OTRO_PDF)],
        }
    )
    respuesta, _ = ejecutar(repositorio)
    assert respuesta.idempotente is False


def test_f004_r17_un_candidato_sin_binario_se_ignora_en_vez_de_reventar() -> None:
    """Defensa: L5 hace INNER JOIN y `DATALENGTH(NULL)` nunca casa, pero si el
    motor devolviera un `ima` NULL, hashearlo reventaria la peticion entera."""
    repositorio = RepositorioDoble(
        lecturas={
            **_LECTURAS_FELICES,
            "idempotencia": [
                (1, "sin.binario", 2, None),
                (_IDE_NEGOCIO, "202608181140392614.aechevarria", _IDE_ENLACE, _PDF),
            ],
        }
    )
    respuesta, _ = ejecutar(repositorio)
    assert respuesta.idempotente is True
    assert respuesta.grafico.ide_negocio == _IDE_NEGOCIO


def test_f004_r17_la_idempotencia_se_revisa_otra_vez_dentro_de_la_transaccion() -> None:
    """Bajo el applock: entre la lectura y el commit puede haberlo colgado otro."""
    repositorio = RepositorioDoble(
        idempotencia_en_transaccion=[
            (_IDE_NEGOCIO, "202608181140392614.aechevarria", _IDE_ENLACE, _PDF)
        ]
    )
    respuesta, _ = ejecutar(repositorio, commit=True)
    assert respuesta.idempotente is True
    assert respuesta.filas_afectadas == 0
    claves = [clave for clave, _ in repositorio.cursor.ejecutadas]
    assert claves == ["idempotencia"]


def test_f004_r17_una_huerfana_nunca_es_idempotente_pero_se_avisa() -> None:
    """Fila de negocio sin pareja documental: no tiene binario que comparar.
    Hay una real de clase 35 [MEDIDO]."""
    repositorio = RepositorioDoble(
        lecturas={**_LECTURAS_FELICES, "huerfanas": [(236774, "un.cod"), (236775, "otro.cod")]}
    )
    respuesta, _ = ejecutar(repositorio)
    assert respuesta.idempotente is False
    avisos = " ".join(respuesta.avisos)
    assert "sin binario" in avisos
    assert "236774" in avisos and "236775" in avisos


def test_f004_r17_la_clase_sin_tipaso_se_avisa() -> None:
    repositorio = RepositorioDoble(
        lecturas={**_LECTURAS_FELICES, "clase": [(35, "PV002", "x", 0, "")]}
    )
    respuesta, _ = ejecutar(repositorio)
    assert any("tipaso" in aviso for aviso in respuesta.avisos)


# --- R21: la traza -----------------------------------------------------------


def test_f004_r21_la_traza_lleva_lo_que_hace_falta_y_nunca_el_binario(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.INFO):
        respuesta, _ = ejecutar(commit=True)
    texto = "\n".join(registro.getMessage() for registro in caplog.records)

    for esperado in ("conide", "contip", "gratipide", "cod", "bytes", "sha256",
                     "usu", "commit", "idempotente", "filas_afectadas", "duracion"):
        assert esperado in texto, esperado
    assert _SHA_PDF in texto
    assert respuesta.grafico.cod in texto

    assert _B64 not in texto
    assert _B64[:32] not in texto
    assert "%PDF" not in texto
    assert "contenido_base64" not in texto


def test_f004_r21_tambien_se_traza_el_fallo(caplog: pytest.LogCaptureFixture) -> None:
    repositorio = RepositorioDoble(lecturas={**_LECTURAS_FELICES, "usuario": []})
    with caplog.at_level(logging.INFO), pytest.raises(ConceptoGraficoError):
        ejecutar(repositorio)
    texto = "\n".join(registro.getMessage() for registro in caplog.records)
    assert "usuario_no_valido" in texto
    assert _B64 not in texto
