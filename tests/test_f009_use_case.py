# tests/test_f009_use_case.py
"""
F-009 · lote C · el caso de uso del modo extendido de `sigrid/albaran`
(`application/use_cases/create_albaran_compra_use_case.py`).

T7 (R9, R11-R17), T8 (R29, R30, R30c), T9 (R7, R23), T10 (R19-R21, R24-R28) y
T11 (R18, R20). Sin red y sin base de datos: repositorio, cursor y reloj son
los dobles de `f009_dobles.py`, que reconocen cada sentencia por su SQL exacto.
"""
from __future__ import annotations

from typing import Any

import pytest
from f009_dobles import (
    AHORA,
    CTR,
    OBRA,
    IntegrityError,
    RepositorioDoble,
    SettingsDoble,
)

from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
)
from domain.models.albaran_compra_models import AlbaranCompraError, AlbaranCompraRequest


def vinculada(ref: str = "L1", ctrpro_ide: int = 9001, **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "ctrpro_ide": ctrpro_ide, "cantidad": 2.0, "precio": 10.5,
            **extra}


def sin_vincular(ref: str = "L2", producto: str = "MA9999", **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "producto": producto, "descripcion": "Arena de rio",
            "unidad": "m3", "cantidad": 3.0, "precio": 2.675, **extra}


def peticion(lineas: list[dict[str, Any]] | None = None, **cambios: Any) -> AlbaranCompraRequest:
    base = {
        "database": "ruesma", "cod_obra": "0404", "usu": "prueba",
        "cif_proveedor": "B12345678", "referencia_externa": "ALB-1",
        "cod_contrato": "CTSU16/0206", "su_referencia": "A-77", "fecha_albaran": 20261005,
        "lineas": lineas if lineas is not None else [vinculada()],
    }
    return AlbaranCompraRequest.model_validate({**base, **cambios})


def ejecutar(
    lineas: list[dict[str, Any]] | None = None,
    *,
    repo: RepositorioDoble | None = None,
    settings: SettingsDoble | None = None,
    **cambios: Any,
):
    repo = repo or RepositorioDoble()
    caso = CreateAlbaranCompraUseCase(repo, settings or SettingsDoble(), ahora_utc=lambda: AHORA)
    return caso.run(peticion(lineas, **cambios)), repo


def error(lineas: list[dict[str, Any]] | None = None, **kwargs: Any) -> AlbaranCompraError:
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(lineas, **kwargs)
    return excinfo.value


def codigo(lineas: list[dict[str, Any]] | None = None, **kwargs: Any) -> str:
    return error(lineas, **kwargs).codigo


def fallos(lineas: list[dict[str, Any]], **kwargs: Any) -> list[tuple[int, str, str]]:
    exc = error(lineas, **kwargs)
    assert exc.codigo == "lineas_no_validas"
    return [(f.indice, f.referencia_linea, f.codigo) for f in exc.lineas]


def avisos(linea: Any) -> list[str]:
    return [a.codigo for a in linea.avisos]


def dcapro(respuesta: Any, i: int = 0) -> dict[str, Any]:
    return respuesta.filas["dcapro"][i]


# =====================================================================================
# T7 · R11: resolución de la cabecera
# =====================================================================================


def test_f009_r11_lecturas_de_cabecera_en_orden_y_con_sus_parametros() -> None:
    _respuesta, repo = ejecutar()
    cabecera = [c for c in repo.lecturas_hechas() if c != "referencia"][:4]
    assert cabecera == ["obra", "plantilla_por_entide", "conest", "usuario"]
    assert repo.parametros_de("obra") == [[42, "0404"]]
    assert repo.parametros_de("plantilla_por_entide") == [[14, 1, 77]]
    assert repo.parametros_de("usuario") == [["prueba"]]
    assert repo.parametros_de("conest") == [[14, 1]]
    llamadas = [tipo for tipo, _ in repo.llamadas[:6]]
    assert llamadas == ["leer", "locate_contract", "read_full_row", "read_rows_by", "leer",
                        "read_full_row"]
    assert repo.llamadas[1][1] == {
        "database": "ruesma", "cod_contrato": "CTSU16/0206", "cod_obra": "0404",
        "cif_proveedor": "B12345678", "contract_tip": 44,
    }
    assert repo.llamadas[2][1] == ("ctr", CTR)
    assert repo.llamadas[3][1] == ("ctrpro", "docide", CTR, "pos")
    assert ("read_full_row", ("con", 15950)) in repo.llamadas
    assert ("read_full_row", ("dca", 15950)) in repo.llamadas


def test_f009_r11_obra_solo_entre_las_empresas_admitidas() -> None:
    repo = RepositorioDoble({"obra": [(6000, 2, "0404"), (OBRA, 1, "0404")]})
    respuesta, _ = ejecutar(repo=repo)
    assert respuesta.filas["dca"]["obride"] == OBRA
    assert respuesta.filas["con"]["emp"] == 1


def test_f009_r11_con_emp_es_la_empresa_de_la_obra() -> None:
    repo = RepositorioDoble({"obra": [(OBRA, 2, "0404")]}, contratos=[{"ide": CTR, "obride": OBRA}])
    respuesta, repo = ejecutar(
        [vinculada(), sin_vincular()], repo=repo, settings=SettingsDoble(sigrid_albaran_empresas_obra=[2])
    )
    assert respuesta.filas["con"]["emp"] == 2
    assert {m["emp"] for m in respuesta.filas["mov"]} == {2}
    assert respuesta.filas["log"]["emp"] == 2
    assert repo.parametros_de("plantilla_por_entide") == [[14, 2, 77]]
    assert repo.parametros_de("productos") == [[2, 3, "MA9999"]]
    assert repo.parametros_de("cuentas") == [[2, "6000001"]]


@pytest.mark.parametrize(
    ("obras", "empresas", "esperado"),
    [
        ([], [1], "obra_no_encontrada"),
        ([(6000, 2, "0404")], [1], "obra_de_empresa_no_permitida"),
        ([(OBRA, 1, "0404")], [], "obra_de_empresa_no_permitida"),
        ([(OBRA, 1, "0404"), (6000, 2, "0404")], [1, 2], "obra_ambigua"),
    ],
)
def test_f009_r11_obra_por_empresa(obras: list, empresas: list[int], esperado: str) -> None:
    repo = RepositorioDoble({"obra": obras})
    assert codigo(repo=repo, settings=SettingsDoble(sigrid_albaran_empresas_obra=empresas)) == esperado
    assert repo.lecturas_hechas() == ["obra"]


@pytest.mark.parametrize(
    ("contratos", "esperado"),
    [
        ([], "contrato_no_encontrado"),
        ([{"ide": 301, "obride": 6000}], "contrato_no_encontrado"),
        ([{"ide": CTR, "obride": OBRA}, {"ide": 301, "obride": OBRA}], "contrato_ambiguo"),
    ],
)
def test_f009_r11_contrato_del_localizador_y_de_esa_obra(contratos: list, esperado: str) -> None:
    repo = RepositorioDoble(contratos=contratos)
    assert codigo(repo=repo) == esperado
    assert [t for t, _ in repo.llamadas] == ["leer", "locate_contract"]


def test_f009_r11_el_contrato_de_otra_obra_se_descarta_si_hay_uno_de_esta() -> None:
    repo = RepositorioDoble(contratos=[{"ide": 301, "obride": 6000}, {"ide": CTR, "obride": OBRA}])
    respuesta, _ = ejecutar(repo=repo)
    assert respuesta.filas["dca"]["ctride"] == CTR


def test_f009_r11_contrato_sin_fila_ctr() -> None:
    assert codigo(repo=RepositorioDoble(filas={("ctr", CTR): None})) == "contrato_no_encontrado"


def test_f009_r11_proveedor_sin_albaran_previo_en_la_empresa() -> None:
    repo = RepositorioDoble({"plantilla_por_entide": []})
    assert codigo(repo=repo) == "proveedor_sin_albaran_previo"


def test_f009_r11_sin_contrato_la_plantilla_es_por_cif_normalizado() -> None:
    repo = RepositorioDoble({"analiticas": [(721, "0404.CDSB37", 82)]})
    respuesta, repo = ejecutar(
        [sin_vincular()], repo=repo, cod_contrato=None, cif_proveedor=" b12 345678 "
    )
    assert repo.parametros_de("plantilla_por_cif") == [[14, 1, "B12345678"]]
    assert not any(t in ("locate_contract", "read_rows_by") for t, _ in repo.llamadas)
    assert respuesta.filas["dca"]["ctride"] == 0
    assert respuesta.filas["dca"]["entide"] == 77
    assert respuesta.contrato["ctride"] == 0


def test_f009_r11_sin_contrato_y_sin_albaran_previo_del_cif() -> None:
    repo = RepositorioDoble({"plantilla_por_cif": []})
    assert codigo([sin_vincular()], repo=repo, cod_contrato=None) == "proveedor_sin_albaran_previo"


def test_f009_r11_plantilla_de_cabecera_ilegible() -> None:
    with pytest.raises(ValueError, match="plantilla"):
        ejecutar(repo=RepositorioDoble(filas={("dca", 15950): None}))


def test_f009_r11_usuario_que_no_existe() -> None:
    repo = RepositorioDoble({"usuario": []})
    assert codigo(repo=repo) == "usuario_no_valido"


def test_f009_r22_el_instante_por_defecto_es_utc_con_zona() -> None:
    from application.use_cases import create_albaran_compra_use_case as modulo

    instante = modulo._ahora_utc()
    assert instante.utcoffset() is not None and instante.utcoffset().total_seconds() == 0
    caso = CreateAlbaranCompraUseCase(RepositorioDoble(), SettingsDoble())
    assert caso.run(peticion()).estado == "previsto"


def test_f009_r22_estado_inicial_que_no_esta_en_conest() -> None:
    repo = RepositorioDoble({"conest": []})
    assert codigo(repo=repo) == "estado_inicial_no_encontrado"


def test_f009_r9_un_error_de_cabecera_corta_antes_de_mirar_las_lineas() -> None:
    repo = RepositorioDoble({"usuario": []})
    codigo([vinculada(precio=-1.0, partida="99")], repo=repo)
    assert not {"partidas", "productos", "tipmov", "plantilla_linea"} & set(repo.lecturas_hechas())


def test_f009_r11_una_lectura_truncada_no_se_ignora() -> None:
    with pytest.raises(ValueError, match="truncada"):
        ejecutar([vinculada(partida="01.01")], repo=RepositorioDoble(truncar_en="partidas"))


# =====================================================================================
# T7 · R12: vinculadas
# =====================================================================================


def test_f009_r12_linea_que_no_es_del_contrato() -> None:
    assert fallos([vinculada(ctrpro_ide=1234)]) == [(0, "L1", "linea_no_es_del_contrato")]


def test_f009_r12_vinculada_toma_del_ctrpro_y_no_de_la_plantilla() -> None:
    respuesta, repo = ejecutar([vinculada()])
    fila = dcapro(respuesta)
    assert (fila["proide"], fila["ivaide"], fila["caaide"], fila["cod2"], fila["dncide"],
            fila["dncproide"], fila["res"], fila["unimed"], fila["linoriide"]) == (
        55, 3, 90, "PLAN-7", 41, 42, "Hormigon HA-25", "m3", 9001)
    assert repo.parametros_de("plantilla_linea") == [[55]]
    linea = respuesta.lineas[0]
    assert (linea.tipo, linea.ctrpro_ide, linea.linoriide, linea.proide) == ("vinculada", 9001, 9001, 55)


def test_f009_r12_descripcion_y_unidad_de_la_peticion_si_vienen() -> None:
    respuesta, _ = ejecutar([vinculada(descripcion="Otra", unidad="kg")])
    assert (dcapro(respuesta)["res"], dcapro(respuesta)["unimed"]) == ("Otra", "kg")


def test_f009_r12_varias_al_mismo_ctrpro_no_se_suman() -> None:
    respuesta, repo = ejecutar([vinculada("A", cantidad=2.0), vinculada("B", cantidad=3.0)])
    assert [f["can"] for f in respuesta.filas["dcapro"]] == [2.0, 3.0]
    assert [f["can"] for f in respuesta.filas["ctrprodes"]] == [2.0, 3.0]
    assert [f["canent"] for f in respuesta.filas["mov"]] == [2.0, 3.0]
    assert [f["lindeside"] for f in respuesta.filas["ctrprodes"]] == [8000001, 8000002]
    # La plantilla de línea se lee una vez por producto.
    assert repo.parametros_de("plantilla_linea") == [[55]]


def test_f009_r12_supera_pendiente_con_lo_acumulado_en_el_albaran() -> None:
    """9001: can 100, canser 20 => pendiente 80. 50 cabe; 50 + 40 no."""
    respuesta, _ = ejecutar([vinculada("A", cantidad=50.0, partida="01.01"),
                             vinculada("B", cantidad=40.0, partida="01.01"),
                             vinculada("C", cantidad=-10.0, partida="01.01")])
    assert [avisos(l) for l in respuesta.lineas] == [[], ["supera_pendiente"], []]


def test_f009_r12_tipmov_de_los_productos_de_los_ctrpro() -> None:
    _respuesta, repo = ejecutar([vinculada("A"), vinculada("B", ctrpro_ide=9003, precio=100.0),
                                 vinculada("C")])
    assert repo.parametros_de("tipmov") == [[55, 57]]


# =====================================================================================
# T7 · R13 y R13b: sin vincular, producto, IVA y naturaleza
# =====================================================================================


def test_f009_r13_producto_fuera_de_la_lista_blanca_no_se_lee() -> None:
    assert fallos([sin_vincular(producto="SM9999")]) == [(0, "L2", "producto_no_permitido")]


@pytest.mark.parametrize("productos", [[], [(66, "MA9999", 20250101, 1)]])
def test_f009_r13_producto_inexistente_o_de_baja(productos: list) -> None:
    repo = RepositorioDoble({"productos": productos})
    assert fallos([sin_vincular()], repo=repo) == [(0, "L2", "producto_no_encontrado")]


def test_f009_r13_una_lectura_por_lista_de_productos() -> None:
    _respuesta, repo = ejecutar([sin_vincular("A"), sin_vincular("B", producto="QA9999"),
                                 sin_vincular("C")])
    assert repo.parametros_de("productos") == [[1, 3, "MA9999", "QA9999"]]
    assert repo.parametros_de("naturalezas") == [["MA99", "QA99"]]


def test_f009_r13_iva_de_la_ultima_del_mismo_proveedor() -> None:
    respuesta, repo = ejecutar([sin_vincular()])
    assert repo.parametros_de("plantilla_linea_proveedor") == [[66, 77]]
    assert "plantilla_linea" not in repo.lecturas_hechas()
    assert dcapro(respuesta)["ivaide"] == 3
    assert avisos(respuesta.lineas[0]) == []


def test_f009_r13_iva_de_otro_proveedor_con_aviso() -> None:
    respuesta, repo = ejecutar([sin_vincular(producto="QA9999")])
    assert repo.parametros_de("plantilla_linea") == [[67]]
    fila = dcapro(respuesta)
    assert (fila["ivaide"], fila["tot"], fila["ivacuo"]) == (4, 8.03, 0.8)
    assert avisos(respuesta.lineas[0]) == ["iva_de_otro_proveedor"]


def test_f009_r13_producto_sin_historico_con_aviso() -> None:
    respuesta, _ = ejecutar([sin_vincular(producto="XA9999")])
    fila = dcapro(respuesta)
    assert (fila["ivaide"], fila["ivacuo"], fila["natide"], fila["cueide"], fila["caaide"]) == (
        0, 0.0, 503, 603, 703)
    assert avisos(respuesta.lineas[0]) == ["producto_sin_historico"]


def test_f009_r13_sin_vincular_sin_docori_ni_ctrprodes_ni_canser() -> None:
    respuesta, _ = ejecutar([sin_vincular()])
    fila = dcapro(respuesta)
    assert (fila["docoritip"], fila["docoricod"], fila["docoriide"], fila["linoriide"]) == (0, "", 0, 0)
    assert respuesta.filas["ctrprodes"] == []
    assert respuesta.estados_contrato == {}
    linea = respuesta.lineas[0]
    assert (linea.tipo, linea.ctrpro_ide, linea.linoriide, linea.producto) == ("sin_vincular", 0, 0, "MA9999")


def test_f009_r13b_naturaleza_cuenta_y_analitica_del_mapeo() -> None:
    respuesta, repo = ejecutar([sin_vincular()])
    fila = dcapro(respuesta)
    # Nunca pro.natide ni la plantilla (natide 999, cueide 888, caaide 1).
    assert (fila["natide"], fila["cueide"], fila["caaide"]) == (501, 601, 701)
    assert repo.parametros_de("cuentas") == [[1, "6000001"]]
    assert repo.parametros_de("analiticas") == [["0404.CDSB37"]]


def test_f009_r13b_numemp_de_la_empresa_de_la_obra_vale() -> None:
    respuesta, _ = ejecutar([sin_vincular(producto="QA9999")])
    assert (dcapro(respuesta)["natide"], dcapro(respuesta)["caaide"]) == (502, 702)


@pytest.mark.parametrize(
    ("lecturas", "mapeo"),
    [
        ({}, {}),
        ({}, {"QA9999": "QA99"}),
        ({"naturalezas": []}, None),
        ({"naturalezas": [(501, "MA99", 0, 20240101, "MOD.CDSB37", "6000001")]}, None),
        ({"naturalezas": [(501, "MA99", 2, 0, "MOD.CDSB37", "6000001")]}, None),
        ({"naturalezas": [(501, "MA99", 0, 0, "MOD.CDSB37", "6000001"),
                          (504, "MA99", 1, 0, "MOD.CDSB37", "6000001")]}, None),
        ({"cuentas": []}, None),
        ({"cuentas": [(601, "6000001"), (611, "6000001")]}, None),
        ({"naturalezas": [(501, "MA99", 0, 0, "MOD.CDSB37", "  ")]}, None),
    ],
    ids=["mapeo_vacio", "sin_entrada", "no_existe", "de_baja", "otra_empresa", "dos",
         "sin_cua", "dos_cua", "cuacomcod_vacio"],
)
def test_f009_r13b_naturaleza_no_valida(lecturas: dict, mapeo: dict | None) -> None:
    settings = SettingsDoble()
    if mapeo is not None:
        settings.sigrid_albaran_naturaleza_por_producto = mapeo
    repo = RepositorioDoble(lecturas)
    assert fallos([sin_vincular()], repo=repo, settings=settings) == [(0, "L2", "naturaleza_no_valida")]


def test_f009_r13b_una_naturaleza_de_otra_empresa_no_estorba_a_la_buena() -> None:
    repo = RepositorioDoble({"naturalezas": [(501, "MA99", 0, 0, "MOD.CDSB37", "6000001"),
                                             (504, "MA99", 2, 0, "OTRA", "6000009")]})
    respuesta, _ = ejecutar([sin_vincular()], repo=repo)
    assert dcapro(respuesta)["natide"] == 501


# =====================================================================================
# T7 · R14 y R14b: partidas
# =====================================================================================


def test_f009_r14_partida_imputable_de_la_obra() -> None:
    respuesta, repo = ejecutar([vinculada("A", partida="01.01"), sin_vincular("B", partida="01.02"),
                                sin_vincular("C", partida="01.01")])
    assert [f["paride"] for f in respuesta.filas["dcapro"]] == [5, 6, 5]
    assert [(l.paride, l.partida) for l in respuesta.lineas] == [(5, "01.01"), (6, "01.02"), (5, "01.01")]
    assert repo.parametros_de("partidas") == [[OBRA, "01.01", "01.02"]]


def test_f009_r14_sin_partida_es_paride_0_nunca_el_del_ctrpro() -> None:
    respuesta, repo = ejecutar([vinculada(), sin_vincular()])
    assert [f["paride"] for f in respuesta.filas["dcapro"]] == [0, 0]
    assert [(l.paride, l.partida) for l in respuesta.lineas] == [(0, None), (0, None)]
    assert "partidas" not in repo.lecturas_hechas()


def test_f009_r14_la_partida_se_compara_como_el_erp() -> None:
    repo = RepositorioDoble({"partidas": [(5, "01.01  ", 1, 0, 0)]})
    respuesta, _ = ejecutar([vinculada(partida="01.01")], repo=repo)
    assert dcapro(respuesta)["paride"] == 5


@pytest.mark.parametrize(
    ("partida", "esperado"),
    [("99", "partida_no_encontrada"), ("02", "partida_no_imputable"),
     ("04", "partida_no_imputable"), ("05", "partida_no_imputable"), ("03", "partida_ambigua")],
)
def test_f009_r14_partida_que_no_vale(partida: str, esperado: str) -> None:
    assert fallos([sin_vincular(partida=partida)]) == [(0, "L2", esperado)]


def test_f009_r14b_paride_desambigua() -> None:
    respuesta, _ = ejecutar([sin_vincular(partida="03", paride=9)])
    assert dcapro(respuesta)["paride"] == 9


@pytest.mark.parametrize("paride", [5, 7, 10, 12345])
def test_f009_r14b_paride_no_valido(paride: int) -> None:
    partida = {5: "03", 7: "02", 10: "04", 12345: "01.01"}[paride]
    assert fallos([sin_vincular(partida=partida, paride=paride)]) == [(0, "L2", "paride_no_valido")]


# =====================================================================================
# T7 · R15: almacén, centro y analítica
# =====================================================================================


def test_f009_r15_vinculada_almacen_del_ctrpro_o_del_contrato() -> None:
    respuesta, _ = ejecutar([vinculada("A"), vinculada("B", ctrpro_ide=9002, precio=3.0)])
    filas = respuesta.filas["dcapro"]
    assert [(f["almide"], f["cenide"], f["caaide"]) for f in filas] == [(70, 80, 90), (70, 80, 91)]
    assert [(l.almide, l.cenide) for l in respuesta.lineas] == [(70, 80), (70, 80)]


def test_f009_r15_sin_vincular_con_contrato_almacen_del_contrato() -> None:
    respuesta, repo = ejecutar([sin_vincular()])
    assert (dcapro(respuesta)["almide"], dcapro(respuesta)["cenide"]) == (70, 80)
    assert not {"almacen_de_obra", "almacenes"} & set(repo.lecturas_hechas())


def test_f009_r15_sin_contrato_almacen_de_la_ficha_de_obra() -> None:
    repo = RepositorioDoble({"analiticas": [(721, "0404.CDSB37", 82)]})
    respuesta, repo = ejecutar([sin_vincular()], repo=repo, cod_contrato=None)
    fila = dcapro(respuesta)
    assert (fila["almide"], fila["cenide"], fila["caaide"]) == (72, 82, 721)
    assert (respuesta.filas["dca"]["almide"], respuesta.filas["dca"]["cenide"]) == (72, 82)
    assert repo.parametros_de("almacen_de_obra") == [[OBRA]]
    assert "almacenes" not in repo.lecturas_hechas()


def test_f009_r15_contrato_sin_almacen_cae_a_la_ficha_de_obra() -> None:
    repo = RepositorioDoble({"analiticas": [(721, "0404.CDSB37", 82)]},
                            filas={("ctr", CTR): {**_ctr_sin_almacen()}})
    respuesta, _ = ejecutar([sin_vincular()], repo=repo)
    assert (dcapro(respuesta)["almide"], dcapro(respuesta)["cenide"]) == (72, 82)
    assert (respuesta.filas["dca"]["almide"], respuesta.filas["dca"]["cenide"]) == (72, 82)


def test_f009_r15_solo_vinculadas_la_cabecera_lleva_el_almacen_del_contrato() -> None:
    respuesta, repo = ejecutar([vinculada("A", ctrpro_ide=9003, precio=100.0)])
    assert (respuesta.filas["dca"]["almide"], respuesta.filas["dca"]["cenide"]) == (70, 80)
    assert (dcapro(respuesta)["almide"], dcapro(respuesta)["cenide"]) == (71, 81)
    assert not {"almacen_de_obra", "almacenes"} & set(repo.lecturas_hechas())


def _ctr_sin_almacen() -> dict[str, Any]:
    from f009_dobles import ctr

    return {**ctr(), "almide": 0, "cenide": 0}


@pytest.mark.parametrize("ficha", [[(0, 0)], [(None, 82)], []])
def test_f009_r15_sin_ficha_el_unico_almacen_de_la_obra(ficha: list) -> None:
    repo = RepositorioDoble({"almacen_de_obra": ficha, "analiticas": [(731, "0404.CDSB37", 83)]})
    respuesta, repo = ejecutar([sin_vincular()], repo=repo, cod_contrato=None)
    assert (dcapro(respuesta)["almide"], dcapro(respuesta)["cenide"], dcapro(respuesta)["caaide"]) == (
        73, 83, 731)
    assert repo.parametros_de("almacenes") == [[OBRA]]


@pytest.mark.parametrize("almacenes", [[], [(73, OBRA, 83), (74, OBRA, 84)]])
def test_f009_r15_almacen_de_obra_no_resuelto(almacenes: list) -> None:
    repo = RepositorioDoble({"almacen_de_obra": [(0, 0)], "almacenes": almacenes})
    assert codigo([sin_vincular()], repo=repo, cod_contrato=None) == "almacen_de_obra_no_resuelto"


@pytest.mark.parametrize(
    "lecturas",
    [
        {"analiticas": []},
        {"analiticas": [(799, "0404.CDSB37", 81)]},
        {"analiticas": [(701, "0404.CDSB37", 80), (702, "0404.CDSB37", 80)]},
        {"naturalezas": [(501, "MA99", 0, 0, "", "6000001")]},
        {"naturalezas": [(501, "MA99", 0, 0, "MOD.", "6000001")]},
    ],
    ids=["ninguna", "de_otro_centro", "dos", "caagascod_vacio", "solo_prefijo"],
)
def test_f009_r15_analitica_no_resuelta(lecturas: dict) -> None:
    repo = RepositorioDoble(lecturas)
    assert fallos([sin_vincular()], repo=repo) == [(0, "L2", "analitica_no_resuelta")]


def test_f009_r15_analitica_con_el_codigo_de_obra_recortado() -> None:
    repo = RepositorioDoble({"obra": [(OBRA, 1, "0404  ")]})
    _respuesta, repo = ejecutar([sin_vincular()], repo=repo)
    assert repo.parametros_de("analiticas") == [["0404.CDSB37"]]


# =====================================================================================
# T7 · R16: partida de la vinculada frente a la del ctrpro
# =====================================================================================


def test_f009_r16_partida_distinta_del_contrato() -> None:
    respuesta, _ = ejecutar([vinculada(partida="01.02")])
    assert dcapro(respuesta)["paride"] == 6
    assert avisos(respuesta.lineas[0]) == ["partida_distinta_del_contrato"]


def test_f009_r16_misma_partida_que_el_contrato_sin_aviso() -> None:
    respuesta, _ = ejecutar([vinculada(partida="01.01")])
    assert avisos(respuesta.lineas[0]) == []


def test_f009_r16_sin_partida_en_linea_con_partida() -> None:
    respuesta, _ = ejecutar([vinculada("A"), vinculada("B", ctrpro_ide=9002, precio=3.0)])
    assert [avisos(l) for l in respuesta.lineas] == [["sin_partida_en_linea_con_partida"], []]


# =====================================================================================
# T7 · R17: importes
# =====================================================================================


def test_f009_r17_precio_del_contrato_con_tar_y_dto() -> None:
    respuesta, _ = ejecutar([vinculada()])
    fila = dcapro(respuesta)
    assert (fila["pre"], fila["tar"], fila["dto"], fila["tot"], fila["ivacuo"]) == (
        10.5, 12.0, "10+2,5", 21.0, 4.41)
    assert avisos(respuesta.lineas[0]) == ["sin_partida_en_linea_con_partida"]


def test_f009_r17_precio_distinto_del_contrato() -> None:
    respuesta, _ = ejecutar([vinculada(precio=10.6, partida="01.01")])
    fila = dcapro(respuesta)
    assert (fila["pre"], fila["tar"], fila["dto"], fila["tot"]) == (10.6, 10.6, "", 21.2)
    assert avisos(respuesta.lineas[0]) == ["precio_distinto_del_contrato"]


def test_f009_r17_el_aviso_se_decide_con_la_regla_de_la_fila_opcion_c() -> None:
    """Dentro de la tolerancia (|δ| = 0,00005) pero el importe cambia de céntimo
    con 25.000 uds: la fila lleva el precio pedido y el aviso salta."""
    respuesta, _ = ejecutar([vinculada(cantidad=25000.0, precio=10.50005, partida="01.01")])
    fila = dcapro(respuesta)
    assert (fila["pre"], fila["tot"]) == (10.50005, 262501.25)
    assert avisos(respuesta.lineas[0]) == ["precio_distinto_del_contrato", "supera_pendiente"]


def test_f009_r17_dentro_de_la_tolerancia_y_mismo_importe_sin_aviso() -> None:
    respuesta, _ = ejecutar([vinculada(cantidad=2.0, precio=10.50004, partida="01.01")])
    assert (dcapro(respuesta)["pre"], avisos(respuesta.lineas[0])) == (10.5, [])


def test_f009_r17_precio_negativo_es_fallo_de_linea() -> None:
    assert fallos([sin_vincular(precio=-1.0)]) == [(0, "L2", "precio_negativo")]


def test_f009_r17_importes_con_decimal_y_redondeo_hacia_arriba() -> None:
    respuesta, _ = ejecutar([vinculada(), sin_vincular()])
    assert (dcapro(respuesta, 1)["tot"], dcapro(respuesta, 1)["ivacuo"]) == (8.03, 1.69)
    linea = respuesta.lineas[1]
    assert (linea.cantidad, linea.precio, linea.total, linea.iva_cuota) == (3.0, 2.675, 8.03, 1.69)
    assert respuesta.totales["totbas"] == 29.03
    assert respuesta.totales["totiva"] == 6.1
    assert respuesta.totales["totdoc"] == 35.13
    assert (respuesta.filas["dca"]["totbas"], respuesta.filas["dca"]["totdoc"]) == (29.03, 35.13)


def test_f009_r17_una_tasa_de_iva_que_no_existe_no_se_inventa() -> None:
    with pytest.raises(ValueError, match="IVA"):
        ejecutar([vinculada()], repo=RepositorioDoble({"iva": []}))


# =====================================================================================
# T7 · R9: todos los fallos de línea, acumulados
# =====================================================================================


def test_f009_r9_se_validan_todas_las_lineas_y_se_devuelven_todos_los_fallos() -> None:
    lineas = [
        vinculada("A"),
        vinculada("B", ctrpro_ide=1),
        sin_vincular("C", producto="SM9999"),
        sin_vincular("D", partida="99", precio=-2.0),
        sin_vincular("E", partida="03"),
        vinculada("F", partida="01.01"),
    ]
    assert fallos(lineas) == [
        (1, "B", "linea_no_es_del_contrato"),
        (2, "C", "producto_no_permitido"),
        (3, "D", "partida_no_encontrada"),
        (3, "D", "precio_negativo"),
        (4, "E", "partida_ambigua"),
    ]


def test_f009_r9_con_fallos_no_se_leen_plantillas_ni_balances() -> None:
    repo = RepositorioDoble()
    fallos([vinculada(ctrpro_ide=1)], repo=repo)
    assert not {"plantilla_linea", "iva", "balance", "ultimo_cod"} & set(repo.lecturas_hechas())


# =====================================================================================
# T8 · R29: prefijo de la referencia, también en la previa
# =====================================================================================


@pytest.mark.parametrize("commit", [False, True])
@pytest.mark.parametrize(
    ("referencia", "prefijos"),
    [("XYZ-1", ["ALB-"]), ("alb-1", ["ALB-"]), ("ALB-1", [])],
    ids=["otro_prefijo", "distingue_mayusculas", "sin_prefijos"],
)
def test_f009_r29_referencia_no_permitida_sin_leer(
    referencia: str, prefijos: list[str], commit: bool
) -> None:
    repo = RepositorioDoble()
    settings = SettingsDoble(sigrid_albaran_prefijos_referencia=prefijos)
    exc = error(repo=repo, settings=settings, referencia_externa=referencia, commit=commit)
    assert exc.codigo == "referencia_no_permitida"
    assert repo.llamadas == []


def test_f009_r29_vale_cualquiera_de_los_prefijos() -> None:
    settings = SettingsDoble(sigrid_albaran_prefijos_referencia=["PRU-", "ALB-"])
    respuesta, _ = ejecutar(settings=settings, referencia_externa="ALB-9")
    assert respuesta.referencia_externa == "ALB-9"


# =====================================================================================
# T8 · R30 y R30c: idempotencia por dca.synckey
# =====================================================================================

_EXISTENTE = (2800001, "AC26/15000 ", 20261001, 77, OBRA, 29.03, 35.13)
_LINEAS_EXISTENTE = [
    (64, 55, 2.0, 10.5, 21.0, 5, 70, "L1"),
    (128, 66, 3.0, 2.675, 8.03, 0, 70, "L2    "),
]


def _comprobar_idempotente(respuesta: Any, *, dry_run: bool) -> None:
    assert respuesta.estado == "idempotente"
    assert (respuesta.committed, respuesta.dry_run) == (False, dry_run)
    assert (respuesta.con_ide, respuesta.cod) == (2800001, "AC26/15000")
    assert respuesta.cabecera == {"fec": 20261001}
    assert respuesta.totales == {"totbas": 29.03, "totdoc": 35.13, "n_lineas": 2}
    assert (respuesta.contrato, respuesta.filas, respuesta.movimientos) == ({}, {}, [])
    assert (respuesta.estados_contrato, respuesta.avisos, respuesta.warnings) == ({}, [], [])
    assert [
        (l.indice, l.pos, l.referencia_linea, l.proide, l.cantidad, l.precio, l.total,
         l.paride, l.almide, l.ctrpro_ide, l.linoriide, l.iva_cuota, l.tipo, l.avisos)
        for l in respuesta.lineas
    ] == [
        (0, 64, "L1", 55, 2.0, 10.5, 21.0, 5, 70, 0, 0, 0.0, None, []),
        (1, 128, "L2", 66, 3.0, 2.675, 8.03, 0, 70, 0, 0, 0.0, None, []),
    ]


def test_f009_r30_previa_idempotente_sin_seguir_leyendo() -> None:
    repo = RepositorioDoble({"referencia": [_EXISTENTE], "lineas_del_existente": _LINEAS_EXISTENTE})
    respuesta, repo = ejecutar(repo=repo)
    _comprobar_idempotente(respuesta, dry_run=True)
    assert repo.parametros_de("referencia") == [[14, "ALB-1"]]
    assert repo.parametros_de("lineas_del_existente") == [[2800001]]
    assert repo.lecturas_hechas() == [
        "obra", "plantilla_por_entide", "referencia", "lineas_del_existente",
    ]
    assert not any(t in ("peek", "transaccion") for t, _ in repo.llamadas)


def test_f009_r30_la_referencia_se_mira_tras_la_plantilla_y_antes_de_conest() -> None:
    _respuesta, repo = ejecutar()
    assert repo.lecturas_hechas()[:5] == [
        "obra", "plantilla_por_entide", "referencia", "conest", "usuario",
    ]


def test_f009_r30_idempotente_aunque_las_lineas_de_ahora_no_valgan() -> None:
    repo = RepositorioDoble({"referencia": [_EXISTENTE], "lineas_del_existente": _LINEAS_EXISTENTE})
    respuesta, _ = ejecutar([vinculada(ctrpro_ide=1)], repo=repo)
    assert respuesta.estado == "idempotente"


@pytest.mark.parametrize(
    "filas",
    [
        [_EXISTENTE, (2800002, "AC26/15001", 20261001, 77, OBRA, 1.0, 1.0)],
        [(2800001, "AC26/15000", 20261001, 78, OBRA, 1.0, 1.0)],
        [(2800001, "AC26/15000", 20261001, 77, 6000, 1.0, 1.0)],
    ],
    ids=["dos", "otro_proveedor", "otra_obra"],
)
def test_f009_r30_referencia_en_conflicto(filas: list) -> None:
    repo = RepositorioDoble({"referencia": filas})
    assert codigo(repo=repo) == "referencia_en_conflicto"
    assert "lineas_del_existente" not in repo.lecturas_hechas()


def test_f009_r30_sin_contrato_el_proveedor_es_el_de_la_plantilla_por_cif() -> None:
    repo = RepositorioDoble({"referencia": [_EXISTENTE], "lineas_del_existente": _LINEAS_EXISTENTE,
                             "analiticas": [(721, "0404.CDSB37", 82)]})
    respuesta, _ = ejecutar([sin_vincular()], repo=repo, cod_contrato=None)
    assert respuesta.estado == "idempotente"


def test_f009_r30_commit_con_la_referencia_ya_leida_fuera_no_abre_transaccion() -> None:
    repo = RepositorioDoble({"referencia": [_EXISTENTE], "lineas_del_existente": _LINEAS_EXISTENTE})
    respuesta, repo = ejecutar(repo=repo, commit=True)
    _comprobar_idempotente(respuesta, dry_run=False)
    assert repo.transacciones == []


def test_f009_r30_commit_dentro_de_la_transaccion_antes_de_reservar_nada() -> None:
    repo = RepositorioDoble(
        filas_en_transaccion={"referencia": [_EXISTENTE], "lineas_del_existente": _LINEAS_EXISTENTE}
    )
    respuesta, repo = ejecutar(repo=repo, commit=True)
    _comprobar_idempotente(respuesta, dry_run=False)
    assert repo.sentencias() == ["referencia", "lineas_del_existente"]
    assert repo.parametros_en_transaccion("referencia") == [[14, "ALB-1"]]
    assert repo.parametros_en_transaccion("lineas_del_existente") == [[2800001]]
    assert repo.transacciones[0]["applock_resources"][0] == "SIGRID_REFEXT_14"


def test_f009_r30_commit_conflicto_dentro_de_la_transaccion() -> None:
    repo = RepositorioDoble(
        filas_en_transaccion={"referencia": [(2800001, "AC26/15000", 20261001, 78, OBRA, 1.0, 1.0)]}
    )
    assert codigo(repo=repo, commit=True) == "referencia_en_conflicto"
    assert repo.sentencias() == ["referencia"]


# =====================================================================================
# T9 · R23 y R7: la previa, solo lecturas y con las filas completas
# =====================================================================================


def test_f009_r23_la_previa_no_necesita_ninguna_llave_de_escritura() -> None:
    settings = SettingsDoble(
        sigrid_domain_write_enabled=False, sigrid_albaran_write_enabled=False,
        sql_server_write_username=None, sql_server_write_password=None,
        allowed_write_databases=[],
    )
    respuesta, repo = ejecutar([vinculada(), sin_vincular()], settings=settings)
    assert (respuesta.estado, respuesta.committed, respuesta.dry_run) == ("previsto", False, True)
    assert {tipo for tipo, _ in repo.llamadas} == {
        "leer", "locate_contract", "read_full_row", "read_rows_by", "peek",
    }
    assert repo.transacciones == []


def test_f009_r23_cod_e_ide_provisionales_con_aviso() -> None:
    respuesta, repo = ejecutar([vinculada(), sin_vincular()])
    assert repo.parametros_de("ultimo_cod") == [[6, 1, 14, "AC26/%"]]
    assert [d for t, d in repo.llamadas if t == "peek"] == ["con", "dcapro", "ctrprodes", "mov", "log"]
    assert (respuesta.con_ide, respuesta.cod) == (2900001, "AC26/15953")
    assert [(a.codigo, a.mensaje) for a in respuesta.avisos] == [
        ("cod_provisional",
         ("DRY-RUN: no se ha escrito nada. El cod y los ide son provisionales (MAX+1 sin "
          "reservar); en el commit se reservan bajo bloqueo.")),
    ]


def test_f009_r23_sin_albaranes_en_la_serie_empieza_en_1_y_por_el_anio_del_albaran() -> None:
    repo = RepositorioDoble({"ultimo_cod": [(None,)]})
    respuesta, repo = ejecutar(repo=repo, fecha_albaran=20251231)
    assert repo.parametros_de("ultimo_cod") == [[6, 1, 14, "AC25/%"]]
    assert respuesta.cod == "AC25/1"


def test_f009_r23_las_seis_filas_numeradas_y_enlazadas() -> None:
    respuesta, _ = ejecutar([vinculada(), sin_vincular()])
    filas = respuesta.filas
    assert set(filas) == {"con", "dca", "dcapro", "ctrprodes", "mov", "log"}
    assert (filas["con"]["ide"], filas["con"]["cod"], filas["con"]["tip"], filas["con"]["est"]) == (
        2900001, "AC26/15953", 14, 1)
    assert filas["con"]["res"] == "PROVEEDOR PRUEBA SL. (A-77)"
    assert (filas["dca"]["ide"], filas["dca"]["synckey"], filas["dca"]["ctride"]) == (
        2900001, "ALB-1", CTR)
    assert [(f["ide"], f["docide"], f["pos"], f["refent"]) for f in filas["dcapro"]] == [
        (8000001, 2900001, 64, "L1"), (8000002, 2900001, 128, "L2")]
    assert [(f["ide"], f["docdeside"], f["lindeside"], f["docdescod"], f["docproide"])
            for f in filas["ctrprodes"]] == [(400001, 2900001, 8000001, "AC26/15953", 9001)]
    assert [(f["ide"], f["docide"], f["linide"], f["proide"], f["almide"])
            for f in filas["mov"]] == [
        (9000001, 2900001, 8000001, 55, 70), (9000002, 2900001, 8000002, 66, 70)]
    assert (filas["log"]["ide"], filas["log"]["cod"], filas["log"]["usu"], filas["log"]["res"]) == (
        8488889, "AC26/15953", "prueba", "PROVEEDOR PRUEBA SL. (A-77)")
    assert respuesta.movimientos == filas["mov"]


def test_f009_r23_balance_vigente_de_cada_producto_y_almacen() -> None:
    respuesta, repo = ejecutar([vinculada("A"), sin_vincular("B"), vinculada("C", cantidad=3.0)])
    assert repo.parametros_de("balance") == [[55, 70], [66, 70]]
    assert [(l.stock_anterior, l.stock_resultante, l.pmp_anterior) for l in respuesta.lineas] == [
        (10.0, 12.0, 9.0), (4.0, 7.0, 2.0), (12.0, 15.0, (10.0 * 9.0 + 2.0 * 10.5) / 12.0)]


def test_f009_r23_un_producto_sin_mov_anterior_parte_de_cero() -> None:
    respuesta, _ = ejecutar([sin_vincular(producto="QA9999")])
    linea = respuesta.lineas[0]
    assert (linea.stock_anterior, linea.stock_resultante, linea.pmp_anterior, linea.pmp_resultante) == (
        0.0, 3.0, 0.0, (0.0 * 0.0 + 3.0 * 2.675) / 3.0)  # R19: sin redondear


def test_f009_r7_superconjunto_de_la_respuesta_clasica() -> None:
    from domain.models.albaran_domain_models import (
        AddPurchaseAlbaranResponse,
        AlbaranLinePreview,
    )

    respuesta, _ = ejecutar([vinculada(), sin_vincular()])
    assert isinstance(respuesta, AddPurchaseAlbaranResponse)
    assert all(isinstance(l, AlbaranLinePreview) for l in respuesta.lineas)
    assert [l.indice for l in respuesta.lineas] == [0, 1]
    assert [l.referencia_linea for l in respuesta.lineas] == ["L1", "L2"]
    assert respuesta.contrato == {
        "ctride": CTR, "obride": OBRA, "cod_contrato": "CTSU16/0206", "cod_obra": "0404",
        "cif_proveedor": "B12345678", "entide": 77, "almide": 70, "template_ide": 15950,
    }
    assert respuesta.totales == {"totbas": 29.03, "totiva": 6.1, "totdoc": 35.13, "n_lineas": 2,
                                 "n_vinculadas": 1, "n_movimientos": 2}
    assert respuesta.estados_contrato == {
        "estser_before": 0, "estfac_before": 0, "estser_after": 0, "estfac_after": 0,
        "sum_can": 111.0, "sum_canser_before": 25.0, "sum_canser_after": 27.0, "sum_canfac": 0.0,
    }


def test_f009_r7_sin_columnas_bancarias_en_la_respuesta() -> None:
    respuesta, _ = ejecutar([vinculada()])
    for fila in (respuesta.cabecera, respuesta.filas["dca"]):
        assert not {"bancue", "cpacue1"} & set(fila)
        assert fila["pagide"] == 12
    volcado = respuesta.model_dump_json()
    assert "ES12" not in volcado and "ES34" not in volcado


def test_f009_r7_avisos_con_codigo_y_warnings_en_orden() -> None:
    respuesta, _ = ejecutar([vinculada(precio=10.6), sin_vincular(producto="QA9999")])
    assert [avisos(l) for l in respuesta.lineas] == [
        ["sin_partida_en_linea_con_partida", "precio_distinto_del_contrato"],
        ["iva_de_otro_proveedor"],
    ]
    esperados = [a.mensaje for a in respuesta.avisos] + [
        a.mensaje for l in respuesta.lineas for a in l.avisos
    ]
    assert respuesta.warnings == esperados and len(esperados) == 4


# =====================================================================================
# T10 · R24: guardas antes de leer nada
# =====================================================================================


@pytest.mark.parametrize("commit", [False, True])
def test_f009_r24_demasiadas_lineas_tambien_en_la_previa(commit: bool) -> None:
    repo = RepositorioDoble()
    settings = SettingsDoble(sigrid_albaran_max_lineas=2)
    lineas = [vinculada("A"), vinculada("B"), vinculada("C")]
    assert codigo(lineas, repo=repo, settings=settings, commit=commit) == "demasiadas_lineas"
    assert repo.llamadas == []


def test_f009_r24_en_el_tope_vale() -> None:
    respuesta, _ = ejecutar([vinculada("A"), vinculada("B")],
                            settings=SettingsDoble(sigrid_albaran_max_lineas=2))
    assert len(respuesta.lineas) == 2


@pytest.mark.parametrize(
    "settings",
    [
        SettingsDoble(sigrid_domain_write_enabled=False),
        SettingsDoble(sigrid_albaran_write_enabled=False),
        SettingsDoble(sql_server_write_username=None),
        SettingsDoble(sql_server_write_password=""),
    ],
    ids=["dominio", "albaranes", "sin_usuario", "sin_clave"],
)
def test_f009_r24_commit_sin_llaves_no_lee_nada(settings: SettingsDoble) -> None:
    repo = RepositorioDoble()
    assert codigo(repo=repo, settings=settings, commit=True) == "escritura_albaranes_deshabilitada"
    assert repo.llamadas == []


@pytest.mark.parametrize("bases", [[], ["otra"]], ids=["lista_vacia", "otra_base"])
def test_f009_r24_commit_en_una_base_no_permitida(bases: list[str]) -> None:
    repo = RepositorioDoble()
    settings = SettingsDoble(allowed_write_databases=bases)
    assert codigo(repo=repo, settings=settings, commit=True) == "base_de_datos_no_permitida"
    assert repo.llamadas == []


# =====================================================================================
# T10 · R25, R26, R20: una transacción, reservas bajo bloqueo y medición del contrato
# =====================================================================================

_SECUENCIA_COMPLETA = [
    "referencia", "reservar_cod", "ide_con", "ide_dcapro", "ide_ctrprodes", "ide_mov",
    "balance_bajo_bloqueo", "balance_bajo_bloqueo",
    "insert_con", "insert_dca", "insert_dcapro", "insert_dcapro", "insert_ctrprodes",
    "insert_mov", "insert_mov",
    "servido", "sumas_contrato", "estados_contrato",
    "ide_log", "insert_log",
    "releer_con", "releer_dca", "releer_dcapro", "releer_mov", "releer_ctrprodes", "releer_log",
]


def test_f009_r25_el_albaran_entero_en_una_transaccion() -> None:
    respuesta, repo = ejecutar([vinculada(), sin_vincular()], commit=True)
    assert repo.transacciones == [{
        "database": "ruesma", "timeout_seconds": 30,
        "applock_resources": ["SIGRID_REFEXT_14", "SIGRID_SERIE_14", "SIGRID_IDE_con",
                              "SIGRID_IDE_dcapro", "SIGRID_IDE_ctrprodes", "SIGRID_IDE_mov",
                              "SIGRID_IDE_log"],
        "applock_timeout_ms": 10000, "max_retries": 3,
    }]
    assert repo.sentencias() == _SECUENCIA_COMPLETA
    assert repo.cursores[0].connection.timeout == 30
    assert (respuesta.estado, respuesta.committed, respuesta.dry_run) == ("creado", True, False)
    assert (respuesta.con_ide, respuesta.cod) == (2900011, "AC26/15953")
    assert respuesta.avisos == []


def test_f009_r25_lo_insertado_es_lo_que_se_devuelve() -> None:
    respuesta, repo = ejecutar([vinculada(), sin_vincular()], commit=True)
    filas = respuesta.filas
    assert repo.parametros_en_transaccion("insert_con") == [list(filas["con"].values())]
    assert repo.parametros_en_transaccion("insert_dcapro") == [list(f.values()) for f in filas["dcapro"]]
    assert repo.parametros_en_transaccion("insert_log") == [list(filas["log"].values())]
    assert [f["ide"] for f in filas["dcapro"]] == [8000011, 8000012]
    assert [f["ide"] for f in filas["ctrprodes"]] == [400011]
    assert [f["ide"] for f in filas["mov"]] == [9000011, 9000012]
    assert (filas["log"]["ide"], filas["log"]["cod"]) == (8488899, "AC26/15953")
    assert len(repo.parametros_en_transaccion("insert_ctrprodes")) == 1
    assert len(repo.parametros_en_transaccion("insert_mov")) == 2


def test_f009_r25_la_fila_dca_escrita_lleva_las_bancarias() -> None:
    respuesta, repo = ejecutar([vinculada()], commit=True)
    ((sql, params),) = [(s, p) for _i, c, s, p in repo.en_transaccion if c == "insert_dca"]
    columnas = [c.strip()[1:-1] for c in sql[sql.index("(") + 1 : sql.index(")")].split(",")]
    escrita = dict(zip(columnas, params, strict=True))
    assert (escrita["bancue"], escrita["cpacue1"]) == ("ES12", "ES34")
    assert "bancue" not in respuesta.filas["dca"]


def test_f009_r31_en_la_transaccion_solo_los_update_de_r25_y_ningun_delete() -> None:
    _respuesta, repo = ejecutar([vinculada(), sin_vincular()], commit=True)
    verbos = {sql.split()[0] for _i, _c, sql, _p in repo.en_transaccion}
    assert verbos == {"SELECT", "INSERT", "UPDATE"}
    actualizaciones = {sql for _i, _c, sql, _p in repo.en_transaccion if sql.startswith("UPDATE")}
    assert actualizaciones == {
        "UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?",
        "UPDATE dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?",
    }


def test_f009_r26_reservas_bajo_bloqueo_y_sin_lecturas_de_la_previa() -> None:
    _respuesta, repo = ejecutar([vinculada(), sin_vincular()], commit=True)
    assert repo.parametros_en_transaccion("reservar_cod") == [[6, 1, 14, "AC26/%"]]
    assert repo.parametros_en_transaccion("balance_bajo_bloqueo") == [[55, 70], [66, 70]]
    assert not {"balance", "ultimo_cod"} & set(repo.lecturas_hechas())
    assert not any(t == "peek" for t, _ in repo.llamadas)


def test_f009_r26_el_balance_sale_de_e7_no_de_la_previa() -> None:
    repo = RepositorioDoble(reservas={"balance_bajo_bloqueo": lambda _i, p: (20.0, 5.0)})
    respuesta, _ = ejecutar([vinculada()], repo=repo, commit=True)
    mov = respuesta.filas["mov"][0]
    assert (mov["almcan"], mov["almpma"], mov["prepma"]) == (
        22.0, (20.0 * 5.0 + 2.0 * 10.5) / 22.0, 5.0)
    assert dcapro(respuesta)["prepma"] == 5.0
    assert (respuesta.lineas[0].stock_anterior, respuesta.lineas[0].stock_resultante) == (20.0, 22.0)


def test_f009_r26_sin_mov_anterior_bajo_bloqueo_parte_de_cero() -> None:
    repo = RepositorioDoble(reservas={"balance_bajo_bloqueo": lambda _i, p: None})
    respuesta, _ = ejecutar([vinculada()], repo=repo, commit=True)
    assert (respuesta.filas["mov"][0]["almcan"], respuesta.filas["mov"][0]["prepma"]) == (2.0, 0.0)


def test_f009_r26_serie_vacia_empieza_en_1() -> None:
    repo = RepositorioDoble(reservas={"reservar_cod": (None,)})
    respuesta, _ = ejecutar(repo=repo, commit=True)
    assert respuesta.cod == "AC26/1"


def test_f009_r26_sin_vinculadas_ni_mov_no_se_reservan_sus_ide() -> None:
    repo = RepositorioDoble({"productos": [(66, "MA9999", 0, 0)]})
    respuesta, repo = ejecutar([sin_vincular()], repo=repo, commit=True)
    assert repo.sentencias() == [
        "referencia", "reservar_cod", "ide_con", "ide_dcapro",
        "insert_con", "insert_dca", "insert_dcapro",
        "ide_log", "insert_log",
        "releer_con", "releer_dca", "releer_dcapro", "releer_mov", "releer_ctrprodes", "releer_log",
    ]
    assert (respuesta.filas["mov"], respuesta.filas["ctrprodes"]) == ([], [])


def test_f009_r20_sin_vinculadas_ningun_update_aunque_haya_contrato() -> None:
    respuesta, repo = ejecutar([sin_vincular()], commit=True)
    assert not {"servido", "sumas_contrato", "estados_contrato"} & set(repo.sentencias())
    assert respuesta.filas["dca"]["ctride"] == CTR
    assert respuesta.estados_contrato == {}


def test_f009_r20_servido_por_linea_y_estados_con_las_sumas_de_dentro() -> None:
    repo = RepositorioDoble(reservas={"sumas_contrato": (111.0, 111.0, 0.0)})
    respuesta, repo = ejecutar([vinculada("A", cantidad=2.0), vinculada("B", cantidad=3.0)],
                               repo=repo, commit=True)
    assert repo.parametros_en_transaccion("servido") == [[2.0, 9001], [3.0, 9001]]
    assert repo.parametros_en_transaccion("sumas_contrato") == [[CTR]]
    assert repo.parametros_en_transaccion("estados_contrato") == [[1, 0, CTR]]
    assert respuesta.estados_contrato == {
        "estser_before": 0, "estfac_before": 0, "estser_after": 1, "estfac_after": 0,
        "sum_can": 111.0, "sum_canser_before": 106.0, "sum_canser_after": 111.0, "sum_canfac": 0.0,
    }


def test_f009_r19_mov_si_y_solo_si_tipmov_1_y_prepma_de_su_mov_o_0() -> None:
    """O3 del lote B: el caso de uso decide qué líneas llevan `mov` y su `prepma`."""
    repo = RepositorioDoble({"productos": [(66, "MA9999", 0, 0), (68, "XA9999", 0, 1)]})
    respuesta, _ = ejecutar(
        [vinculada("A"), vinculada("B", ctrpro_ide=9003, precio=100.0), sin_vincular("C"),
         sin_vincular("D", producto="XA9999")],
        repo=repo,
    )
    filas = respuesta.filas
    assert [(m["linide"], m["proide"]) for m in filas["mov"]] == [(8000001, 55), (8000004, 68)]
    assert [f["prepma"] for f in filas["dcapro"]] == [9.0, 0, 0, 0.0]
    por_linea = {m["linide"]: m["prepma"] for m in filas["mov"]}
    for fila in filas["dcapro"]:
        assert fila["prepma"] == por_linea.get(fila["ide"], 0)


def test_f009_r21_prepma_encadenado_en_el_mismo_producto_y_almacen() -> None:
    respuesta, _ = ejecutar([vinculada("A", cantidad=2.0), vinculada("B", cantidad=3.0)])
    movs = respuesta.filas["mov"]
    assert movs[0]["prepma"] == 9.0
    assert movs[1]["prepma"] == movs[0]["almpma"] == (10.0 * 9.0 + 2.0 * 10.5) / 12.0
    assert [f["prepma"] for f in respuesta.filas["dcapro"]] == [m["prepma"] for m in movs]


def test_f009_r19_el_mov_lleva_el_pre_escrito_en_la_fila() -> None:
    """Condición (b) del reviewer del lote B: `mov.pre` y el balance, con el `pre` escrito."""
    respuesta, _ = ejecutar([vinculada(precio=10.50004, partida="01.01")])
    assert dcapro(respuesta)["pre"] == 10.5
    mov = respuesta.filas["mov"][0]
    assert (mov["pre"], mov["prc"], mov["almpma"]) == (10.5, 10.5, (10.0 * 9.0 + 2.0 * 10.5) / 12.0)


# =====================================================================================
# T10 · R27: reintento ante clave duplicada
# =====================================================================================


def test_f009_r27_reintenta_la_transaccion_entera_recalculando() -> None:
    repo = RepositorioDoble(
        reservas={
            "reservar_cod": lambda i, _p: (15952 + i - 1,),
            "ide_con": lambda i, _p: (2900011 + 10 * (i - 1),),
            "ide_dcapro": lambda i, _p: (8000011 + 10 * (i - 1),),
            "balance_bajo_bloqueo": lambda i, _p: (10.0 * i, 9.0),
        },
        fallos={"insert_dcapro": lambda i: IntegrityError("2627") if i == 1 else None},
    )
    respuesta, repo = ejecutar([vinculada()], repo=repo, commit=True)
    assert len(repo.cursores) == 2
    assert repo.sentencias(2)[:2] == ["referencia", "reservar_cod"]
    assert (respuesta.con_ide, respuesta.cod) == (2900021, "AC26/15954")
    assert repo.parametros_en_transaccion("insert_con", intento=2) == [
        list(respuesta.filas["con"].values())
    ]
    assert respuesta.filas["dcapro"][0]["ide"] == 8000021
    assert respuesta.filas["mov"][0]["almcan"] == 22.0
    assert respuesta.filas["dcapro"][0]["prepma"] == 9.0
    # Reentrante: el intento 2 parte de filas limpias, no de las del 1.
    (dcapro1,) = repo.parametros_en_transaccion("insert_dcapro", intento=1)
    (dcapro2,) = repo.parametros_en_transaccion("insert_dcapro", intento=2)
    assert (dcapro1[0], dcapro2[0]) == (8000011, 8000021)


def test_f009_r27_agotados_los_reintentos_colision_de_clave() -> None:
    repo = RepositorioDoble(fallos={"insert_con": IntegrityError("2627")})
    exc = error(repo=repo, commit=True)
    assert exc.codigo == "colision_de_clave"
    assert isinstance(exc.__cause__, IntegrityError)
    assert len(repo.cursores) == 4


def test_f009_r27_otro_error_de_la_base_no_se_disfraza() -> None:
    repo = RepositorioDoble(fallos={"insert_mov": RuntimeError("se cayo la red")})
    with pytest.raises(RuntimeError, match="se cayo la red"):
        ejecutar(repo=repo, commit=True)
    assert len(repo.cursores) == 1


# =====================================================================================
# T10 · R28: relecturas antes del COMMIT
# =====================================================================================


def test_f009_r28_relecturas_por_clave() -> None:
    _respuesta, repo = ejecutar([vinculada(), sin_vincular()], commit=True)
    relecturas = ("releer_con", "releer_dca", "releer_dcapro", "releer_mov", "releer_ctrprodes",
                  "releer_log")
    assert [repo.parametros_en_transaccion(c) for c in relecturas] == [
        [[1, 14, "AC26/15953"]], [[2900011]], [[2900011]], [[2900011, 14]], [[2900011, 14]],
        [[8488899]],
    ]


@pytest.mark.parametrize(
    ("relectura", "valor"),
    [("releer_con", 2), ("releer_dca", 0), ("releer_dcapro", 1), ("releer_mov", 3),
     ("releer_ctrprodes", 0), ("releer_log", 0)],
)
def test_f009_r28_si_no_cuadran_rollback_con_codigo(relectura: str, valor: int) -> None:
    repo = RepositorioDoble(forzar={relectura: (valor,)})
    exc = error([vinculada(), sin_vincular()], repo=repo, commit=True)
    assert exc.codigo == "filas_afectadas_inesperadas"
    assert repo.sentencias()[-1] == relectura
    assert len(repo.cursores) == 1


# =====================================================================================
# T11 · R18 y R20: devoluciones de punta a punta
# =====================================================================================


def test_f009_r18_devolucion_vinculada_en_commit() -> None:
    """9001: canser 20; devolver 3 (regla A, M5): entrada con `canent` < 0."""
    repo = RepositorioDoble(reservas={"sumas_contrato": (111.0, 17.0, 0.0)})
    respuesta, repo = ejecutar([vinculada(cantidad=-3.0, partida="01.01")], repo=repo, commit=True)
    fila = dcapro(respuesta)
    assert (fila["can"], fila["tot"], fila["ivacuo"]) == (-3.0, -31.5, -6.62)
    assert [f["can"] for f in respuesta.filas["ctrprodes"]] == [-3.0]
    assert repo.parametros_en_transaccion("servido") == [[-3.0, 9001]]
    mov = respuesta.filas["mov"][0]
    assert (mov["tip"], mov["oritip"], mov["destip"], mov["canent"], mov["cansal"]) == (1, 5, 2, -3.0, 0.0)
    assert (mov["almcan"], mov["almpma"], mov["prepma"]) == (7.0, (10.0 * 9.0 - 3.0 * 10.5) / 7.0, 9.0)
    assert dcapro(respuesta)["prepma"] == 9.0
    assert respuesta.totales["totbas"] == -31.5
    assert respuesta.filas["dca"]["totdoc"] == -38.12
    assert avisos(respuesta.lineas[0]) == []


def test_f009_r18_devolucion_que_deja_el_servido_en_negativo_se_admite_con_aviso() -> None:
    respuesta, _ = ejecutar([vinculada("A", cantidad=-15.0, partida="01.01"),
                             vinculada("B", cantidad=-10.0, partida="01.01")])
    # 9001: canser 20 -> 5 -> -5; stock 10 -> -5 -> -15.
    assert [avisos(l) for l in respuesta.lineas] == [
        ["stock_negativo"], ["servido_negativo", "stock_negativo"]]


def test_f009_r20_una_devolucion_devuelve_estser_a_0() -> None:
    from f009_dobles import ctr

    repo = RepositorioDoble(reservas={"sumas_contrato": (111.0, 108.0, 111.0)},
                            filas={("ctr", CTR): {**ctr(), "estser": 1, "estfac": 1}})
    respuesta, repo = ejecutar([vinculada(cantidad=-3.0, partida="01.01")], repo=repo, commit=True)
    assert repo.parametros_en_transaccion("estados_contrato") == [[0, 1, CTR]]
    estados = respuesta.estados_contrato
    assert (estados["estser_before"], estados["estser_after"], estados["sum_canser_before"]) == (
        1, 0, 111.0)


def test_f009_r20_en_la_previa_la_devolucion_tambien_recalcula_estser() -> None:
    from f009_dobles import ctr, ctrpro

    servidas = [{**l, "canser": l["can"]} for l in ctrpro()]
    repo = RepositorioDoble(ctrpro_filas=servidas,
                            filas={("ctr", CTR): {**ctr(), "estser": 1}})
    respuesta, _ = ejecutar([vinculada(cantidad=-1.0, partida="01.01")], repo=repo)
    estados = respuesta.estados_contrato
    assert (estados["estser_before"], estados["estser_after"]) == (1, 0)
    assert (estados["sum_canser_before"], estados["sum_canser_after"]) == (111.0, 110.0)


def test_f009_r18_devolucion_sin_vincular_con_stock_negativo() -> None:
    """MA9999 en el almacén 70: stock 4; devolver 5 deja -1 (se admite, M15)."""
    respuesta, repo = ejecutar([sin_vincular(cantidad=-5.0)], commit=True)
    fila = dcapro(respuesta)
    assert (fila["can"], fila["tot"], fila["ivacuo"]) == (-5.0, -13.38, -2.81)
    mov = respuesta.filas["mov"][0]
    assert (mov["canent"], mov["almcan"]) == (-5.0, -1.0)
    assert avisos(respuesta.lineas[0]) == ["stock_negativo"]
    assert respuesta.filas["ctrprodes"] == []
    assert not {"servido", "sumas_contrato", "estados_contrato"} & set(repo.sentencias())


def test_f009_r18_el_stock_negativo_se_decide_con_el_balance_de_dentro() -> None:
    """En la previa (L12: stock 10) no avisa; en el commit, E7 dice 1 y avisa."""
    previa, _ = ejecutar([vinculada(cantidad=-3.0, partida="01.01")])
    assert avisos(previa.lineas[0]) == []
    repo = RepositorioDoble(reservas={"balance_bajo_bloqueo": lambda _i, _p: (1.0, 9.0)})
    creado, _ = ejecutar([vinculada(cantidad=-3.0, partida="01.01")], repo=repo, commit=True)
    assert avisos(creado.lineas[0]) == ["stock_negativo"]
    assert creado.lineas[0].stock_resultante == -2.0


def test_f009_r18_devolucion_que_deja_el_stock_a_cero_conserva_el_pmp() -> None:
    respuesta, _ = ejecutar([vinculada(cantidad=-10.0, partida="01.01")])
    mov = respuesta.filas["mov"][0]
    assert (mov["almcan"], mov["almpma"], mov["prepma"]) == (0.0, 9.0, 9.0)
    assert avisos(respuesta.lineas[0]) == []


def test_f009_r18_la_devolucion_no_supera_lo_pendiente() -> None:
    respuesta, _ = ejecutar([vinculada("A", ctrpro_ide=9002, cantidad=-1.0, precio=3.0)])
    # Sin `mov` previo del 56 en el 70: stock 0 -> -1. Ni supera ni deja canser < 0.
    assert avisos(respuesta.lineas[0]) == ["stock_negativo"]
