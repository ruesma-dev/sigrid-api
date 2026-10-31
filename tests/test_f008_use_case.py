# tests/test_f008_use_case.py
"""
F-008 T11 · `CreateFacturaUseCase` en previa: orden de validacion de design §7,
sin escribir, FR y FRGG, con y sin origenes y mixtas (R3, R5-R35, R43, R44).

Repositorio doble (`tests/f008_dobles.py`): sin red ni base de datos. Toda
previa termina comprobando que no se ha abierto transaccion ni se ha lanzado
otra cosa que `SELECT`.
"""
from __future__ import annotations

from typing import Any

import pytest
from f008_dobles import (
    AHORA,
    AjustesFactura,
    Repositorio,
    ajustes_de_escritura,
    linea_fr,
    linea_gg,
    peticion,
)

from application.use_cases.create_factura_use_case import CreateFacturaUseCase
from domain.models.factura_models import FacturaError, FacturaRequest


def _caso(repo: Repositorio | None = None, ajustes: AjustesFactura | None = None):
    repo = repo or Repositorio()
    return CreateFacturaUseCase(repo, ajustes or AjustesFactura(), ahora_utc=lambda: AHORA), repo


def _previa(repo: Repositorio | None = None, ajustes: AjustesFactura | None = None, **cambios: Any):
    caso, repo = _caso(repo, ajustes)
    resultado = caso.run(FacturaRequest.model_validate(peticion(**cambios)))
    assert repo.transaccion is None
    return resultado, repo


def _error(repo: Repositorio | None = None, ajustes: AjustesFactura | None = None, **cambios: Any) -> FacturaError:
    caso, repo = _caso(repo, ajustes)
    with pytest.raises(FacturaError) as error:
        caso.run(FacturaRequest.model_validate(peticion(**cambios)))
    return error.value


# --------------------------------------------------------------------------- #
# Previas que salen bien
# --------------------------------------------------------------------------- #


def test_f008_r3_previa_fr_de_mes_con_un_albaran() -> None:
    r, repo = _previa()
    assert r["estado"] == "previsto" and r["dry_run"] is True and r["committed"] is False
    assert r["cod"] == "FR26/00042" and r["con_ide"] == 10000
    assert r["serie"] == "FR" and r["modo"] == "mes"
    filas = r["filas"]
    assert filas["con"]["est"] == 1 and filas["con"]["tip"] == 15 and filas["con"]["fec"] == 20261030
    assert filas["con"]["res"] == "PROVEEDOR UNO SL. (F-77)"
    assert filas["dcf"]["synckey"] == "FAC-1" and filas["dcf"]["cla"] == 1001
    assert filas["dcf"]["cueide"] == 4001 and filas["dcf"]["fecdoc"] == 20261015
    assert filas["dcf"]["entide"] == 500 and filas["dcf"]["obride"] == 4040
    # R16: la de `can` 0 no pasa.
    assert [f["linoriide"] for f in filas["dcfpro"]] == [8001]
    assert filas["dcfpro"][0]["cueide"] == 4009 and filas["dcfpro"][0]["pos"] == 64
    assert filas["dcfpro"][0]["docoricod"] == "AC26/1" and filas["dcfpro"][0]["docoriide"] == 800
    assert [f["docproide"] for f in filas["dcaprodes"]] == [8001]
    assert filas["dcaprodes"][0]["lindeside"] == 20000
    assert r["totales"]["totbas"] == 20.0 and r["totales"]["totiva"] == 4.2
    assert r["totales"]["tot"] == 24.2 and r["retencion"] is None
    assert [p["cla"] for p in filas["pag"]] == [0] and filas["pag"][0]["tot"] == 24.2
    assert filas["con_pag"][0]["cod"] == "FR26/00042_01" and filas["con_pag"][0]["ide"] == 10001
    assert filas["consii"]["desope"] == "PROVEEDOR UNO SL. (F-77)"
    assert filas["log"]["tip"] == 15 and filas["log"]["usu"] == "prueba"
    assert [a["codigo"] for a in r["avisos"]] == ["cod_provisional"]
    assert r["origenes"] == [{"cod": "AC26/1", "con_ide": 800, "lineas": 1}]
    assert [l["clase"] for l in r["lineas"]] == ["origen"]
    assert r["pendiente_en_sigrid"]
    assert all(nombre != "cuentas_gasto" for nombre in repo.nombres())


def test_f008_r9_previa_frgg_sin_origen_en_recgg() -> None:
    r, _repo = _previa(
        serie="FRGG", origenes=[], cod_obra="GG", lineas=[linea_gg()],
        total_base=100.0, total_iva=21.0, total_factura=121.0,
        vencimientos=[{"fecha": 20261130, "importe": 121.0}],
    )
    assert r["cod"] == "FRGG26/0008" and r["filas"]["con"]["est"] == 20
    dcf = r["filas"]["dcf"]
    # Cabecera del proveedor, su `auxpag` y la obra de cabecera (M61, M67).
    assert dcf["entide"] == 500 and dcf["entcod"] == "P500" and dcf["entres"] == "PROVEEDOR UNO SL"
    assert dcf["pagtex"] == "30 DIAS" and dcf["pagfor"] == "30" and dcf["ban"] == "ES1111111111111111111111"
    assert dcf["obride"] == 9000 and dcf["cenide"] == 81 and dcf["almide"] == 0 and dcf["ctride"] == 0
    (fila,) = r["filas"]["dcfpro"]
    assert (fila["cueide"], fila["caaide"], fila["obride"], fila["cenide"]) == (629, 190, 9000, 81)
    assert (fila["proide"], fila["paride"], fila["natide"], fila["almide"]) == (0, 0, 0, 0)
    assert fila["tot"] == 100.0 and fila["ivacuo"] == 21.0 and fila["docoritip"] == 0
    assert r["filas"]["dcaprodes"] == [] and r["origenes"] == []
    assert [l["clase"] for l in r["lineas"]] == ["sin_origen"]


def test_f008_r25_previa_fr_sin_origen() -> None:
    r, repo = _previa(
        origenes=[], cod_obra="0404", lineas=[linea_fr(partida="01.01")],
        total_base=100.0, total_iva=21.0, total_factura=121.0,
        vencimientos=[{"fecha": 20261130, "importe": 121.0}],
    )
    (fila,) = r["filas"]["dcfpro"]
    assert (fila["proide"], fila["natide"], fila["cueide"], fila["caaide"]) == (300, 50, 600, 191)
    assert (fila["almide"], fila["cenide"], fila["obride"], fila["paride"]) == (70, 80, 4040, 355)
    assert r["filas"]["dcf"]["almide"] == 70 and r["filas"]["con"]["est"] == 1
    assert "almacen_de_obra" in repo.nombres()


def test_f008_r28_previa_fr_mixta_origen_primero() -> None:
    r, _repo = _previa(
        lineas=[linea_fr()], total_base=120.0, total_iva=25.2, total_factura=145.2,
        vencimientos=[{"fecha": 20261130, "importe": 100.0}, {"fecha": 20261231, "importe": 45.2}],
    )
    dcfpro = r["filas"]["dcfpro"]
    assert [f["docoritip"] for f in dcfpro] == [14, 0]
    assert [f["pos"] for f in dcfpro] == [64, 128]
    assert [l["clase"] for l in r["lineas"]] == ["origen", "sin_origen"]
    assert [p["fecven"] for p in r["filas"]["pag"]] == [20261130, 20261231]
    assert [c["res"] for c in r["filas"]["con_pag"]][1].startswith("Pago 2 de 2 ")


def test_f008_r12_frgg_con_albaran_igual_que_fr() -> None:
    r, _repo = _previa(serie="FRGG")
    assert r["cod"] == "FRGG26/0008" and r["filas"]["con"]["est"] == 20
    assert r["filas"]["dcfpro"][0]["cueide"] == 4009
    assert [f["docproide"] for f in r["filas"]["dcaprodes"]] == [8001]


def test_f008_r13_varios_origenes_cabecera_del_primero_por_cod() -> None:
    r, repo = _previa(
        origenes=["AC26/2", "AC26/1"], total_base=25.0, total_iva=5.25, total_factura=30.25,
        vencimientos=[{"fecha": 20261130, "importe": 30.25}],
    )
    assert [f["linoriide"] for f in r["filas"]["dcfpro"]] == [8011, 8001]
    # La cabecera, del primer origen por `cod` (AC26/1, fecent 20261001), no del primero pedido.
    assert r["filas"]["dcf"]["fecent"] == 20261001
    assert ("cabecera_de_origen", [800]) in repo.lecturas


def test_f008_r20_a_origen_con_a_origen_que_cuadra() -> None:
    r, _repo = _previa(
        origenes=["PROF26/1"], modo="origen",
        a_origen=[{"linea": 8101, "canoriori": 10.0, "imporiori": 100.005}],
        total_base=30.0, total_iva=6.3, total_factura=36.3,
        vencimientos=[{"fecha": 20261130, "importe": 36.3}],
    )
    (fila,) = r["filas"]["dcfpro"]
    assert (fila["canoriori"], fila["canoriant"], fila["imporiant"], fila["imporiori"]) == (10.0, 7.0, 70.0, 100.0)
    assert r["filas"]["dcf"]["ctride"] == 900 and r["filas"]["dcf"]["docoritip"] == 0


def test_f008_r24_nded_solo_cambia_el_ivaide() -> None:
    r, _repo = _previa(
        serie="FRGG", origenes=[], cod_obra="GG", lineas=[linea_gg(iva="I21NDED")],
        total_base=100.0, total_iva=21.0, total_factura=121.0,
        vencimientos=[{"fecha": 20261130, "importe": 121.0}],
    )
    (fila,) = r["filas"]["dcfpro"]
    assert fila["ivaide"] == 2121 and fila["ivacuo"] == 21.0


def test_f008_r31_r34_retencion_del_origen_con_su_pag_cla_2() -> None:
    repo = Repositorio()
    repo.mundo.retenciones.append({
        "docide": 800, "recide": 77, "pos": 64, "valdef": 0, "valpor": 0.05, "valcan": 0,
        "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4730, "ivaide": 0, "tex": "",
        "resalt": "", "item": 0,
    })
    r, _repo = _previa(
        repo, total_factura=23.2, vencimientos=[{"fecha": 20261130, "importe": 23.2}],
        vencimiento_retencion=20271015,
    )
    assert r["totales"]["retencion"] == 1.0 and r["totales"]["tot"] == 23.2
    (dcfrec,) = r["filas"]["dcfrec"]
    assert dcfrec["recide"] == 77 and dcfrec["bas"] == 20.0 and dcfrec["cuo"] == 1.0
    assert [p["cla"] for p in r["filas"]["pag"]] == [0, 2]
    garantia = r["filas"]["pag"][1]
    assert (garantia["tot"], garantia["retide"], garantia["cueide"], garantia["fecven"]) == (1.0, 77, 4730, 20271015)
    assert r["filas"]["con_pag"][1]["cod"] == "FR26/00042_02"
    assert r["retencion"] == {"recide": 77, "reccla": 5, "valpor": 0.05, "bas": 20.0, "cuo": 1.0}


def test_f008_r3_la_previa_solo_lee() -> None:
    _r, repo = _previa(lineas=[linea_fr()], total_base=120.0, total_iva=25.2, total_factura=145.2,
                       vencimientos=[{"fecha": 20261130, "importe": 145.2}])
    assert repo.lecturas and repo.transaccion is None
    assert set(repo.peeks) == {"con", "dcfpro", "consii", "dcaprodes", "log"}


def test_f008_r44_idempotente_sin_escribir() -> None:
    repo = Repositorio()
    repo.mundo.facturas.append({
        "ide": 7777, "cod": "FR26/00030", "entide": 500, "entref": "F-77", "totbas": 20.0,
        "totiva": 4.2, "totdoc": 24.2, "tot": 24.2, "est": 1, "synckey": "FAC-1", "entcif": "B00000001",
    })
    r, repo = _previa(repo)
    assert r["estado"] == "idempotente" and r["cod"] == "FR26/00030" and r["con_ide"] == 7777
    assert r["totales"] == {"totbas": 20.0, "totiva": 4.2, "totdoc": 24.2, "tot": 24.2}
    assert "origenes" not in repo.nombres()


# --------------------------------------------------------------------------- #
# Errores, en el orden de design §7
# --------------------------------------------------------------------------- #


def _repo_con(**mundo: Any) -> Repositorio:
    repo = Repositorio()
    for nombre, valor in mundo.items():
        setattr(repo.mundo, nombre, valor)
    return repo


def test_f008_r6_referencia_no_permitida_antes_que_nada() -> None:
    e = _error(referencia_externa="OTRA-1", usu="nadie")
    assert e.codigo == "referencia_no_permitida"


def test_f008_r6_lista_vacia_no_admite_ninguna() -> None:
    assert _error(ajustes=AjustesFactura(sigrid_factura_prefijos_referencia=[])).codigo == "referencia_no_permitida"


def test_f008_r8_demasiadas_lineas_aun_en_previa() -> None:
    e = _error(ajustes=AjustesFactura(sigrid_factura_max_lineas=1), lineas=[linea_fr(), linea_fr()])
    assert e.codigo == "demasiadas_lineas"


def test_f008_r8_demasiadas_lineas_contando_las_de_origen() -> None:
    e = _error(ajustes=AjustesFactura(sigrid_factura_max_lineas=1), lineas=[linea_fr()])
    assert e.codigo == "demasiadas_lineas"


@pytest.mark.parametrize("cambio", [
    {"sigrid_domain_write_enabled": False}, {"sigrid_factura_write_enabled": False},
    {"sql_server_write_username": None}, {"sql_server_write_password": ""},
])
def test_f008_r5_commit_exige_todas_las_llaves(cambio: dict[str, Any]) -> None:
    e = _error(ajustes=ajustes_de_escritura(**cambio), commit=True)
    assert e.codigo == "escritura_facturas_deshabilitada"


@pytest.mark.parametrize("bases", [[], ["otra"]])
def test_f008_r5_base_no_permitida(bases: list[str]) -> None:
    e = _error(ajustes=ajustes_de_escritura(allowed_write_databases=bases), commit=True)
    assert e.codigo == "base_de_datos_no_permitida"


def test_f008_r7_usuario_no_valido() -> None:
    assert _error(usu="nadie", cod_obra="NOEXISTE").codigo == "usuario_no_valido"


def test_f008_r9_estado_inicial_de_la_serie_en_conest() -> None:
    repo = _repo_con(conest=[(15, 1, "REC"), (15, 15, "RECH"), (14, 3, "CON"), (14, 10, "FAC")])
    assert _error(repo, serie="FRGG").codigo == "estado_inicial_no_encontrado"


@pytest.mark.parametrize("cod_obra", ["NOEXISTE", "0405"])
def test_f008_r11_obra_no_encontrada(cod_obra: str) -> None:
    assert _error(cod_obra=cod_obra).codigo == "obra_no_encontrada"


def test_f008_r11_obra_solo_entre_las_empresas_admitidas() -> None:
    e = _error(ajustes=AjustesFactura(sigrid_albaran_empresas_obra=[3]), cod_obra="0404")
    assert e.codigo == "obra_no_encontrada"


def test_f008_r10_proveedor_no_encontrado_sin_origenes() -> None:
    e = _error(origenes=[], cod_obra="GG", serie="FRGG", lineas=[linea_gg()], cif_proveedor="B99999999")
    assert e.codigo == "proveedor_no_encontrado"


def test_f008_r10_proveedor_ambiguo_sin_origenes() -> None:
    repo = Repositorio()
    repo.mundo.proveedores[600]["cif"] = "B00000001"
    e = _error(repo, origenes=[], cod_obra="GG", serie="FRGG", lineas=[linea_gg()])
    assert e.codigo == "proveedor_ambiguo"


def test_f008_r12_proveedor_sin_cuenta() -> None:
    repo = Repositorio()
    repo.mundo.proveedores[500]["cuepdtide"] = 0
    assert _error(repo).codigo == "proveedor_sin_cuenta"
    repo = Repositorio()
    repo.mundo.proveedores[500]["cueide"] = 0
    e = _error(repo, origenes=[], cod_obra="GG", serie="FRGG", lineas=[linea_gg()])
    assert e.codigo == "proveedor_sin_cuenta"


def test_f008_r12_sin_origenes_la_cuenta_pendiente_no_hace_falta() -> None:
    repo = Repositorio()
    repo.mundo.proveedores[500]["cuepdtide"] = 0
    r, _repo = _previa(repo, serie="FRGG", origenes=[], cod_obra="GG", lineas=[linea_gg()],
                       total_base=100.0, total_iva=21.0, total_factura=121.0,
                       vencimientos=[{"fecha": 20261130, "importe": 121.0}])
    assert r["estado"] == "previsto"


def test_f008_r13_origen_no_encontrado_con_su_codigo() -> None:
    e = _error(origenes=["AC26/1", "AC26/99"])
    assert e.codigo == "origen_no_encontrado" and e.details["origen"] == "AC26/99"


def test_f008_r13_origen_de_otra_empresa_no_vale() -> None:
    repo = Repositorio()
    repo.mundo.origenes[801]["emp"] = 2
    assert _error(repo, origenes=["AC26/1", "AC26/2"]).codigo == "origen_no_encontrado"


def test_f008_r13_origen_de_otro_proveedor() -> None:
    repo = Repositorio()
    repo.mundo.origenes[801]["entide"] = 600
    assert _error(repo, origenes=["AC26/1", "AC26/2"]).codigo == "origen_de_otro_proveedor"
    assert _error(cif_proveedor="B00000002").codigo == "origen_de_otro_proveedor"


def test_f008_r11_r13_varias_obras() -> None:
    repo = Repositorio()
    repo.mundo.origenes[801]["obride"] = 9000
    assert _error(repo, origenes=["AC26/1", "AC26/2"]).codigo == "varias_obras"
    assert _error(cod_obra="GG").codigo == "varias_obras"


def test_f008_r13_varios_contratos() -> None:
    repo = Repositorio()
    repo.mundo.origenes[801]["ctride"] = 901
    assert _error(repo, origenes=["AC26/1", "AC26/2"]).codigo == "varios_contratos"


def test_f008_r14_origen_sin_contabilizar_por_estado_y_por_asiento() -> None:
    repo = Repositorio()
    repo.mundo.origenes[800]["est"] = 1
    assert _error(repo).codigo == "origen_sin_contabilizar"
    repo = _repo_con(asientos={(1, "AC26/2")})
    e = _error(repo)
    assert e.codigo == "origen_sin_contabilizar" and e.details["origen"] == "AC26/1"


def test_f008_r15_origen_ya_facturado_por_canfac_o_dcaprodes() -> None:
    repo = Repositorio()
    repo.mundo.lineas[0]["canfac"] = 2.0
    e = _error(repo)
    assert e.codigo == "origen_ya_facturado" and e.details["lineas"] == [8001]
    repo = _repo_con(facturadas={8001})
    assert _error(repo).codigo == "origen_ya_facturado"


def test_f008_r15_la_linea_de_can_cero_no_cuenta() -> None:
    repo = _repo_con(facturadas={8002})
    r, _repo = _previa(repo)
    assert r["estado"] == "previsto"


def _sin_lineas_en_801(repo: Repositorio) -> Repositorio:
    """AC26/2 con su unica linea a `can` 0: no tiene nada que facturar."""
    repo.mundo.lineas[2].update(can=0.0, tot=0.0, ivacuo=0.0)
    return repo


def test_f008_r16b_origen_sin_lineas_con_can_distinta_de_cero() -> None:
    """R16b (humano, 2026-10-31): un origen sin ninguna linea de `can` != 0 se rechaza,
    aunque los demas origenes si tengan; no se marcaria facturado sin facturar nada."""
    repo = _sin_lineas_en_801(Repositorio())
    e = _error(repo, origenes=["AC26/1", "AC26/2"])
    assert e.codigo == "origen_sin_lineas" and e.details["origenes"] == ["AC26/2"]
    assert repo.transaccion is None


def test_f008_r16b_origen_sin_ninguna_linea() -> None:
    repo = Repositorio()
    del repo.mundo.lineas[2]
    e = _error(repo, origenes=["AC26/1", "AC26/2"])
    assert e.codigo == "origen_sin_lineas" and e.details["origenes"] == ["AC26/2"]


def test_f008_r16b_el_unico_origen_sin_lineas() -> None:
    repo = Repositorio()
    repo.mundo.lineas[0].update(can=0.0)
    e = _error(repo)
    assert e.codigo == "origen_sin_lineas" and e.details["origenes"] == ["AC26/1"]


def test_f008_orden_origen_sin_lineas_antes_que_ya_facturado() -> None:
    repo = _sin_lineas_en_801(Repositorio())
    repo.mundo.lineas[0]["canfac"] = 2.0
    assert _error(repo, origenes=["AC26/1", "AC26/2"]).codigo == "origen_sin_lineas"


def test_f008_r18_modo_no_coincide_y_modos_distintos() -> None:
    assert _error(modo="origen", a_origen=[]).codigo == "modo_no_coincide_con_origen"
    assert _error(origenes=["PROF26/1"]).codigo == "modo_no_coincide_con_origen"
    repo = Repositorio()
    repo.mundo.origenes[801]["docoritip"] = 1
    e = _error(repo, origenes=["AC26/1", "AC26/2"])
    assert e.codigo == "origenes_de_modos_distintos"


def test_f008_r21_r22_a_origen_incompleto_y_que_no_cuadra() -> None:
    base = {"origenes": ["PROF26/1"], "modo": "origen"}
    assert _error(**base).codigo == "a_origen_incompleto"
    e = _error(**base, a_origen=[{"linea": 8101, "canoriori": 10.0, "imporiori": 100.02}])
    assert e.codigo == "a_origen_no_cuadra" and e.details["lineas"][0]["linea"] == 8101


def test_f008_r24_r26_lineas_no_validas_juntas_con_su_posicion() -> None:
    e = _error(
        serie="FRGG", origenes=[], cod_obra="GG",
        lineas=[linea_gg(), linea_gg(iva="I4", cuenta="6290"), linea_gg(analitica="GG.PADRE"),
                linea_gg(cuenta="4000000000", analitica="XX.GEN")],
    )
    assert e.codigo == "lineas_no_validas"
    assert [(f["indice"], f["codigo"]) for f in e.details["lineas"]] == [
        (1, "iva_no_valido"), (1, "cuenta_no_valida"), (2, "analitica_no_valida"),
        (3, "cuenta_no_valida"), (3, "analitica_no_valida"),
    ]


def test_f008_r25_lineas_fr_no_validas() -> None:
    e = _error(origenes=[], cod_obra="0404",
               lineas=[linea_fr(producto="SM9999"), linea_fr(producto="XA9999"),
                       linea_fr(partida="99.99")])
    assert [(f["indice"], f["codigo"]) for f in e.details["lineas"]] == [
        (0, "producto_no_permitido"), (1, "producto_no_encontrado"), (2, "partida_no_encontrada"),
    ]


def test_f008_r25_almacen_de_obra_no_resuelto() -> None:
    repo = _repo_con(obras=[(4040, 1, "0404", 80, 0)], almacenes=[])
    e = _error(repo, origenes=[], cod_obra="0404", lineas=[linea_fr()])
    assert e.codigo == "almacen_de_obra_no_resuelto"


def test_f008_r25_almacen_unico_de_la_obra() -> None:
    repo = _repo_con(analiticas=[(192, "GG.MAT", 81)])
    r, _repo = _previa(repo, origenes=[], cod_obra="GG", lineas=[linea_fr()],
                       total_base=100.0, total_iva=21.0, total_factura=121.0,
                       vencimientos=[{"fecha": 20261130, "importe": 121.0}])
    (fila,) = r["filas"]["dcfpro"]
    assert (fila["almide"], fila["cenide"], fila["caaide"]) == (71, 81, 192)


@pytest.mark.parametrize("campo,valor", [
    ("total_base", 20.02), ("total_iva", 4.26), ("total_factura", 24.26),
])
def test_f008_r30_totales_no_cuadran(campo: str, valor: float) -> None:
    e = _error(**{campo: valor})
    assert e.codigo == "totales_no_cuadran"
    assert e.details["calculado"] == {"total_base": 20.0, "total_iva": 4.2, "total_factura": 24.2}


@pytest.mark.parametrize("campo,valor", [
    ("total_base", 20.01), ("total_iva", 4.25), ("total_factura", 24.25),
])
def test_f008_r30_tolerancias_en_el_borde(campo: str, valor: float) -> None:
    venc = [{"fecha": 20261130, "importe": 24.2}]
    r, _repo = _previa(**{campo: valor, "vencimientos": venc})
    assert r["estado"] == "previsto"


def test_f008_r30_abono_no_soportado() -> None:
    repo = Repositorio()
    repo.mundo.lineas[0].update(can=-2.0, tot=-20.0, ivacuo=-4.2)
    e = _error(repo, total_base=-20.0, total_iva=-4.2, total_factura=-24.2)
    assert e.codigo == "abono_no_soportado"


def _retencion(docide: int, **cambios: Any) -> dict[str, Any]:
    base = {"docide": docide, "recide": 77, "pos": 64, "valdef": 0, "valpor": 0.05, "valcan": 0,
            "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4730, "ivaide": 0, "tex": "",
            "resalt": "", "item": 0}
    base.update(cambios)
    return base


@pytest.mark.parametrize("retenciones,origenes", [
    ([_retencion(800), _retencion(800, recide=78, pos=128)], ["AC26/1"]),
    ([_retencion(800), _retencion(801, valpor=0.15)], ["AC26/1", "AC26/2"]),
    ([_retencion(800)], ["AC26/1", "AC26/2"]),
    ([_retencion(800, valfij=1)], ["AC26/1"]),
    ([_retencion(800, ivaide=21)], ["AC26/1"]),
    ([_retencion(800, valpor=None)], ["AC26/1"]),
])
def test_f008_r31_retencion_no_soportada(
    retenciones: list[dict[str, Any]], origenes: list[str]
) -> None:
    """Mas de una en un origen, distintas entre origenes, unos con y otros sin,
    importe fijo, IVA o sin porcentaje: no se sabe copiar (conservador)."""
    e = _error(_repo_con(retenciones=retenciones), origenes=origenes)
    assert e.codigo == "retencion_no_soportada"


def test_f008_r34_vencimiento_de_la_retencion() -> None:
    repo = _repo_con(retenciones=[_retencion(800)])
    base = {"total_factura": 23.2, "vencimientos": [{"fecha": 20261130, "importe": 23.2}]}
    assert _error(repo, **base).codigo == "vencimiento_retencion_no_valido"
    assert _error(repo, **base, vencimiento_retencion=20261014).codigo == "vencimiento_retencion_no_valido"
    assert _error(vencimiento_retencion=20261130).codigo == "vencimiento_retencion_no_valido"


def test_f008_r34_retencion_sin_garantia_no_lleva_pag_cla_2() -> None:
    repo = _repo_con(retenciones=[_retencion(800, reccla=1)])
    r, _repo = _previa(repo, total_factura=23.2, vencimientos=[{"fecha": 20261130, "importe": 23.2}])
    assert [p["cla"] for p in r["filas"]["pag"]] == [0]


def test_f008_r33_vencimientos() -> None:
    assert _error(vencimientos=[{"fecha": 20261014, "importe": 24.2}]).codigo == "vencimiento_no_valido"
    e = _error(vencimientos=[{"fecha": 20261130, "importe": 24.0}])
    assert e.codigo == "vencimientos_no_cuadran"


def test_f008_r43_referencia_en_conflicto() -> None:
    repo = Repositorio()
    repo.mundo.facturas.append({
        "ide": 7777, "cod": "FR26/00030", "entide": 500, "entref": "OTRA", "totbas": 1.0,
        "totiva": 0.0, "totdoc": 1.0, "tot": 1.0, "est": 1, "synckey": "FAC-1", "entcif": "B00000001",
    })
    assert _error(repo).codigo == "referencia_en_conflicto"


def test_f008_r43_factura_ya_registrada_fuera_de_rech() -> None:
    repo = Repositorio()
    repo.mundo.facturas.append({
        "ide": 7777, "cod": "FR26/00030", "entide": 500, "entref": "F-77", "totbas": 1.0,
        "totiva": 0.0, "totdoc": 1.0, "tot": 1.0, "est": 1, "synckey": "OTRA-REF",
        "entcif": "B00000001",
    })
    e = _error(repo)
    assert e.codigo == "factura_ya_registrada" and e.details["cod"] == "FR26/00030"
    repo.mundo.facturas[0]["est"] = 15
    r, _repo = _previa(repo)
    assert r["estado"] == "previsto"


# --- El orden de §7, con dos fallos a la vez -------------------------------------


def test_f008_orden_usuario_antes_que_obra_y_origenes() -> None:
    assert _error(usu="nadie", origenes=["AC26/99"]).codigo == "usuario_no_valido"


def test_f008_orden_obra_antes_que_origenes() -> None:
    assert _error(cod_obra="NOEXISTE", origenes=["AC26/99"]).codigo == "obra_no_encontrada"


def test_f008_orden_a_origen_antes_que_lineas() -> None:
    e = _error(origenes=["PROF26/1"], modo="origen", lineas=[linea_fr(producto="SM9999")])
    assert e.codigo == "a_origen_incompleto"


def test_f008_orden_lineas_antes_que_totales() -> None:
    e = _error(lineas=[linea_fr(producto="SM9999")], total_base=1.0)
    assert e.codigo == "lineas_no_validas"


def test_f008_orden_totales_antes_que_vencimientos() -> None:
    e = _error(total_base=1.0, vencimientos=[{"fecha": 20261014, "importe": 1.0}])
    assert e.codigo == "totales_no_cuadran"


def test_f008_orden_vencimientos_antes_que_duplicadas() -> None:
    repo = Repositorio()
    repo.mundo.facturas.append({
        "ide": 7777, "cod": "FR26/00030", "entide": 500, "entref": "F-77", "totbas": 1.0,
        "totiva": 0.0, "totdoc": 1.0, "tot": 1.0, "est": 1, "synckey": "OTRA-REF",
        "entcif": "B00000001",
    })
    e = _error(repo, vencimientos=[{"fecha": 20261014, "importe": 24.2}])
    assert e.codigo == "vencimiento_no_valido"


# --- El estado de los pagos sale de `conest` 25 (C3, R32) ----------------------------


def test_f008_r32_el_con_del_pago_nace_en_el_pdt_de_conest() -> None:
    repo = Repositorio()
    repo.mundo.conest = [e for e in repo.mundo.conest if e[0] != 25] + [(25, 7, "PDT")]
    r, _repo = _previa(repo)
    assert [c["est"] for c in r["filas"]["con_pag"]] == [7]


def test_f008_r32_sin_pdt_en_conest_no_se_da_de_alta() -> None:
    repo = Repositorio()
    repo.mundo.conest = [e for e in repo.mundo.conest if e[0] != 25]
    e = _error(repo)
    assert e.codigo == "estado_inicial_no_encontrado" and "25 PDT" in str(e)


# --- La retencion: despues de las lineas, antes de los totales (design §7, desviacion) --


def test_f008_orden_lineas_de_origen_antes_que_retencion() -> None:
    repo = _repo_con(retenciones=[_retencion(800, valfij=1)])
    repo.mundo.lineas[0]["canfac"] = 2.0
    assert _error(repo).codigo == "origen_ya_facturado"


def test_f008_orden_lineas_sin_origen_antes_que_retencion() -> None:
    repo = _repo_con(retenciones=[_retencion(800, valfij=1)])
    linea = {"descripcion": "Material", "cantidad": 1.0, "precio": 1.0, "iva": "I4", "producto": "MA9999"}
    assert _error(repo, lineas=[linea]).codigo == "lineas_no_validas"


def test_f008_orden_retencion_antes_que_totales() -> None:
    """Los totales necesitan la cuota de la retencion: por eso va antes (desviacion declarada)."""
    repo = _repo_con(retenciones=[_retencion(800, valfij=1)])
    assert _error(repo, total_base=1.0).codigo == "retencion_no_soportada"
