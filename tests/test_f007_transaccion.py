# tests/test_f007_transaccion.py
"""
F-007 T14 · R25-R29: la transaccion de `sigrid/proforma` es la del nucleo de
F-009 con F-015 (sentencias, applocks y relecturas) y, bajo el applock de
referencias, LP1 otra vez (R28): si entre la previa y el commit alguien ha
registrado la proforma del mes, se responde con lo que salga sin escribir.

Doble de `tests/f007_dobles.py` con la obra 0719. Sin red ni base de datos.
"""
from __future__ import annotations

import re
from typing import Any

import pytest
from f007_dobles import (
    DATOS,
    RepositorioProforma,
    SettingsProforma,
    ctride_de,
    peticion,
)
from f009_dobles import AHORA, ENTIDE, OBRA, IntegrityError

from application.use_cases.albaran_compra_statements import (
    APPLOCKS,
    E9_SERVIDO,
    E11_ESTADOS_CONTRATO,
    L16_COLUMNAS,
)
from application.use_cases.create_proforma_use_case import CreateProformaUseCase
from domain.models.albaran_compra_models import AlbaranCompraError
from domain.models.proforma_models import (
    ProformaError,
    ProformaRequest,
    ProformaResponse,
)

CTR_0472 = ctride_de("CTSB26/0472")
_COLUMNAS_LP1 = ("ide", "cod", "fec", "entref", "totbas", "docoritip")
JULIO, AGOSTO = (tuple(p[c] for c in _COLUMNAS_LP1) for p in DATOS["proformas"]["CTSB26/0472"])


def ctrrec_fila() -> tuple[Any, ...]:
    base = {
        "ide": 7001, "recide": 6005, "pos": 64, "valdef": 1, "valpor": 0.05, "valcan": 0.0,
        "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4705, "ivaide": 0, "tex": "RETENCION",
        "resalt": "", "item": 0, "cla": 5, "cod": "RET5",
    }
    return tuple(base[columna] for columna in L16_COLUMNAS)


def repo_commit(**kwargs: Any) -> RepositorioProforma:
    """La 0719 con la retencion del contrato y, por defecto, sin la de agosto
    fuera: la previa no ve ninguna del mes."""
    lecturas = {"retenciones": [ctrrec_fila()], "lp1_proformas": [JULIO],
                **kwargs.pop("lecturas", {})}
    return RepositorioProforma(lecturas=lecturas, **kwargs)


def ejecutar(repo: RepositorioProforma, **cambios: Any) -> ProformaResponse:
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    return caso.run(ProformaRequest(**peticion(commit=True, **cambios)))


#: El orden de F-009 con F-015 (retencion, sin `mov`) y LP1 tras E1 (R28).
ORDEN_DEL_INTENTO = [
    "referencia", "lp1_proformas", "reservar_cod", "ide_con", "ide_dcapro", "ide_ctrprodes",
    "ide_dcarec", "insert_con", "insert_dca", *["insert_dcapro"] * 6, *["insert_ctrprodes"] * 5,
    "insert_dcarec", *["servido"] * 5, "sumas_contrato", "estados_contrato", "ide_log",
    "insert_log", "releer_con", "releer_dca", "releer_dcapro", "releer_mov", "releer_ctrprodes",
    "releer_dcarec", "releer_log",
]


def test_f007_r27_orden_de_las_sentencias_y_applocks_de_f015() -> None:
    repo = repo_commit()
    respuesta = ejecutar(repo)
    assert (respuesta.estado, respuesta.committed, respuesta.cod) == ("creado", True, "PROF26/01282")
    assert repo.sentencias() == ORDEN_DEL_INTENTO
    (transaccion,) = repo.transacciones
    assert transaccion["applock_resources"] == list(APPLOCKS)
    assert APPLOCKS[0] == "SIGRID_REFEXT_14"
    assert repo.parametros_en_transaccion("lp1_proformas") == [
        [14, CTR_0472, "PROF%", "PROF%", "PREV%"]
    ]
    assert len(respuesta.filas["dcarec"]) == 1


def test_f007_r27_solo_los_update_de_f009_y_nada_de_delete_merge_ni_ddl() -> None:
    repo = repo_commit()
    ejecutar(repo)
    sqls = [sql for _i, _c, sql, _p in repo.en_transaccion]
    assert {sql for sql in sqls if sql.startswith("UPDATE")} == {E9_SERVIDO, E11_ESTADOS_CONTRATO}
    prohibidas = re.compile(r"\b(DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE)\b", re.IGNORECASE)
    assert not any(prohibidas.search(sql) for sql in sqls)
    assert all(sql.split()[0] in {"SELECT", "INSERT", "UPDATE"} for sql in sqls)


def test_f007_r28_dentro_aparece_la_del_mes_con_el_mismo_total_y_es_existente() -> None:
    repo = repo_commit(filas_en_transaccion={"referencia": [], "lp1_proformas": [JULIO, AGOSTO]})
    respuesta = ejecutar(repo)
    assert (respuesta.estado, respuesta.cod, respuesta.con_ide, respuesta.committed) == (
        "existente", "AC26/25548", 2831541, False)
    assert repo.sentencias() == ["referencia", "lp1_proformas"]
    assert [l.dcapro_ide for l in respuesta.lineas] == [
        f["ide"] for f in DATOS["existentes"]["AC26/25548"]]
    # LP6 se lee despues, fuera de la transaccion.
    assert repo.lecturas_hechas()[-1] == "lp6_lineas"
    assert respuesta.contrato is not None and respuesta.origen is not None


def test_f007_r28_dentro_aparece_la_del_mes_con_otro_total_y_es_error() -> None:
    otra = (*AGOSTO[:4], 99.0, 0)
    repo = repo_commit(filas_en_transaccion={"referencia": [], "lp1_proformas": [JULIO, otra]})
    with pytest.raises(ProformaError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "proforma_del_mes_existente"
    assert repo.sentencias() == ["referencia", "lp1_proformas"]
    assert "lp6_lineas" not in repo.lecturas_hechas()


def test_f007_r28_con_otra_del_mes_lo_de_dentro_no_para() -> None:
    repo = repo_commit(filas_en_transaccion={"referencia": [], "lp1_proformas": [JULIO, AGOSTO]})
    respuesta = ejecutar(repo, otra_del_mes=True)
    assert respuesta.estado == "creado"
    assert repo.sentencias() == ORDEN_DEL_INTENTO


#: La L11 de E1: misma referencia, mismo proveedor y misma obra.
_L11 = (2900011, "PROF26/01282", 20260831, ENTIDE, DATOS["obra"]["ide"], 17024.28, 20599.38,
        19570.17)


def test_f007_r28_dentro_aparece_la_misma_referencia_y_es_idempotente() -> None:
    """R28 (enmienda 1): la fila de E1 se relee con LP5 por el cursor; si es una
    proforma del contrato resuelto, `idempotente` con `origen` nulo y sin los
    avisos de la hoja (D3), como la idempotente de fuera."""
    repo = repo_commit(filas_en_transaccion={
        "referencia": [_L11], "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)],
        "lineas_del_existente": [(64, 610004, 620.0, 11.0, 6820.0, 0, 70, "F09")],
    })
    # Fuera, la hoja da un aviso (ANTERIOR 2600 frente a 2651 registrado).
    respuesta = ejecutar(repo, importe_anterior=2600.0, importe_origen=19624.28)
    assert (respuesta.estado, respuesta.cod, respuesta.committed) == ("idempotente", "PROF26/01282", False)
    assert repo.sentencias() == ["referencia", "lp5_referencia", "lineas_del_existente"]
    assert repo.parametros_en_transaccion("lp5_referencia") == [[14, "PRF-1001"]]
    assert respuesta.contrato is not None and respuesta.contrato.cod == "CTSB26/0472"
    assert (respuesta.origen, respuesta.avisos) == (None, [])


@pytest.mark.parametrize(
    "lp5",
    [[(2900011, "PROF26/01282", 0, CTR_0472)],                         # un albaran, no proforma
     [(2900011, "PROF26/01282", 141, ctride_de("CTSB26/0417"))],       # de otro contrato
     [(2900011, "PROF26/01282", 141, CTR_0472), (1, "PROF26/00001", 141, CTR_0472)],
     []],
)
def test_f007_r28_dentro_la_misma_referencia_que_no_es_proforma_del_contrato_es_conflicto(
    lp5: list[tuple[Any, ...]],
) -> None:
    """D2: dos peticiones con la misma referencia y distinto contrato. La
    primera escribe; la segunda, bajo el applock, no puede salir idempotente con
    el documento de la otra: `referencia_en_conflicto` sin escribir nada."""
    repo = repo_commit(filas_en_transaccion={"referencia": [_L11], "lp5_referencia": lp5})
    with pytest.raises(ProformaError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "referencia_en_conflicto"
    assert repo.sentencias() == ["referencia", "lp5_referencia"]


def test_f007_r28_sin_contrato_dentro_la_misma_referencia_es_idempotente() -> None:
    cuerpo = {
        "database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-2002",
        "cod_obra": "0719", "periodo": 202608, "importe_mes": 816.84,
        "cif_proveedor": "B00000999", "sin_contrato": True, "commit": True,
        "lineas": [{"referencia_linea": "S1", "producto": "SM9999", "partida": "9.01",
                    "descripcion": "Seguridad y replanteo", "cantidad": 816.84, "precio": 1}],
    }
    repo = RepositorioProforma(filas_en_transaccion={
        "referencia": [_L11], "lp5_referencia": [(2900011, "PROF26/01282", 141, 0)],
        "lineas_del_existente": [],
    })
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    respuesta = caso.run(ProformaRequest(**cuerpo))
    assert (respuesta.estado, respuesta.contrato, respuesta.origen) == ("idempotente", None, None)
    assert repo.sentencias() == ["referencia", "lp5_referencia", "lineas_del_existente"]


def test_f007_r28_dentro_la_misma_referencia_de_otra_obra_es_conflicto() -> None:
    ajena = (1, "AC26/00001", 20260831, ENTIDE, OBRA, 1.0, 1.0, 1.0)
    repo = repo_commit(filas_en_transaccion={"referencia": [ajena]})
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "referencia_en_conflicto"
    assert repo.sentencias() == ["referencia"]


def test_f007_r29_colision_de_clave_y_reintento_reentrante() -> None:
    repo = repo_commit(fallos={"insert_dcapro": lambda intento: IntegrityError() if intento == 1 else None})
    respuesta = ejecutar(repo)
    assert respuesta.estado == "creado"
    assert repo.sentencias(1)[:2] == ["referencia", "lp1_proformas"]
    assert repo.sentencias(2) == ORDEN_DEL_INTENTO


def test_f007_r29_colision_de_clave_tras_los_reintentos() -> None:
    repo = repo_commit(fallos={"insert_con": IntegrityError()})
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "colision_de_clave"
    assert len(repo.cursores) == SettingsProforma().domain_write_max_retries + 1
    assert all(repo.sentencias(i)[:2] == ["referencia", "lp1_proformas"]
               for i in range(1, len(repo.cursores) + 1))


@pytest.mark.parametrize("tabla", ["dcarec", "dcapro", "ctrprodes", "con"])
def test_f007_r29_relecturas_que_no_cuadran(tabla: str) -> None:
    repo = repo_commit(forzar={f"releer_{tabla}": (0,)})
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(repo)
    assert excinfo.value.codigo == "filas_afectadas_inesperadas"


def test_f007_r25_la_previa_no_reserva_nada() -> None:
    repo = repo_commit()
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    respuesta = caso.run(ProformaRequest(**peticion()))
    assert (respuesta.estado, respuesta.cod) == ("previsto", "PROF26/01282")
    assert repo.transacciones == [] and repo.en_transaccion == []
    assert "ultimo_cod" in repo.lecturas_hechas()
    assert {d for t, d in repo.llamadas if t == "peek"} == {
        "con", "dcapro", "ctrprodes", "mov", "log", "dcarec"}


def test_f007_r28_sin_contrato_no_lee_lp1_dentro() -> None:
    cuerpo = {
        "database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-2002",
        "cod_obra": "0719", "periodo": 202608, "importe_mes": 816.84,
        "cif_proveedor": "B00000999", "sin_contrato": True, "commit": True,
        "lineas": [{"referencia_linea": "S1", "producto": "SM9999", "partida": "9.01",
                    "descripcion": "Seguridad y replanteo", "cantidad": 816.84, "precio": 1}],
    }
    repo = RepositorioProforma()
    caso = CreateProformaUseCase(repo, SettingsProforma(), ahora_utc=lambda: AHORA)
    respuesta = caso.run(ProformaRequest(**cuerpo))
    assert respuesta.estado == "creado"
    assert "lp1_proformas" not in repo.sentencias()
    assert repo.sentencias()[:2] == ["referencia", "reservar_cod"]
