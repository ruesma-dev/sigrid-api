# tests/test_f007_models.py
"""
F-007 · lote B · T6 (R1-R3, R6, R10, R30): los modelos de `sigrid/proforma`
(`domain/models/proforma_models.py`).

Petición (`ProformaRequest`, `LineaProformaIn`), respuesta (`ProformaResponse`
con `existente`, `contrato`, `origen` y los campos de línea) y errores
(`ProformaError` con `reparto`, `FalloLineaProforma` con `candidatos`), con sus
conjuntos cerrados ampliados sobre los de F-009 (costura 5). Sin red ni base.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.models.albaran_compra_models import (
    CODIGOS_AVISO,
    CODIGOS_CABECERA,
    CODIGOS_LINEA,
    AlbaranCompraError,
    AlbaranCompraResponse,
    FalloLinea,
)
from domain.models.proforma_models import (
    CODIGOS_AVISO_PROFORMA,
    CODIGOS_CABECERA_PROFORMA,
    CODIGOS_LINEA_PROFORMA,
    AvisoProforma,
    ContratoResuelto,
    FalloLineaProforma,
    LineaProformaIn,
    LineaProformaResultado,
    OrigenProforma,
    ProformaError,
    ProformaRequest,
    ProformaResponse,
)


def linea(**cambios: Any) -> dict[str, Any]:
    base = {"referencia_linea": "F09", "ctrpro_ide": 262990, "unidad": "M3",
            "descripcion": "VERTIDO HORMIGON CIMENTACION LIMPIEZA", "cantidad": 620,
            "cantidad_anterior": 241, "cantidad_origen": 861, "precio": 11}
    return {**base, **cambios}


def nueva(**cambios: Any) -> dict[str, Any]:
    base = {"referencia_linea": "F23", "producto": "SM1004", "partida": "02.20.02.02.11",
            "unidad": "M2", "descripcion": "BERENJENO", "cantidad": 75.85, "precio": 3.5}
    return {**base, **cambios}


def cuerpo(**cambios: Any) -> dict[str, Any]:
    base = {"database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-1",
            "cod_obra": "0719", "periodo": 202608, "nombre_proveedor": "SUBCONTRATA UNO",
            "numero_orden": 2, "importe_mes": 7085.48, "importe_anterior": 2651.0,
            "importe_origen": 9736.48, "lineas": [linea(), nueva()], "commit": False}
    return {**base, **cambios}


def valida(**cambios: Any) -> ProformaRequest:
    return ProformaRequest.model_validate(cuerpo(**cambios))


def invalida(**cambios: Any) -> None:
    with pytest.raises(ValidationError):
        valida(**cambios)


# =====================================================================================
# R1 · la petición
# =====================================================================================


def test_f007_r1_peticion_minima_y_defectos() -> None:
    peticion = ProformaRequest.model_validate({
        "database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-1", "cod_obra": "0719",
        "periodo": 202608, "importe_mes": 10.0, "cif_proveedor": "B00000001",
        "lineas": [linea()],
    })
    assert (peticion.cod_contrato, peticion.nombre_proveedor) == (None, None)
    assert (peticion.sin_contrato, peticion.otra_del_mes, peticion.commit) == (False, False, False)
    assert (peticion.fecha_proforma, peticion.su_referencia, peticion.numero_orden) == (None, None, None)
    assert (peticion.importe_anterior, peticion.importe_origen) == (None, None)


def test_f007_r1_el_ejemplo_del_contrato_valida() -> None:
    peticion = valida()
    assert peticion.periodo == 202608
    assert [l.referencia_linea for l in peticion.lineas] == ["F09", "F23"]
    assert peticion.lineas[0].cantidad == 620.0


@pytest.mark.parametrize(
    "campo", ["database", "usu", "referencia_externa", "cod_obra", "periodo", "importe_mes", "lineas"]
)
def test_f007_r1_obligatorios(campo: str) -> None:
    datos = cuerpo()
    del datos[campo]
    with pytest.raises(ValidationError):
        ProformaRequest.model_validate(datos)


def test_f007_r1_textos_recortados_y_cif_normalizado() -> None:
    peticion = valida(referencia_externa="  PRF-1 ", cod_obra=" 0719 ", usu=" prueba ",
                      cif_proveedor=" b00 000001 ", nombre_proveedor="  UNO SL ",
                      cod_contrato=" CTSB26/0472 ", su_referencia="  ", database=" ruesma ")
    assert (peticion.referencia_externa, peticion.cod_obra, peticion.usu) == ("PRF-1", "0719", "prueba")
    assert (peticion.cif_proveedor, peticion.nombre_proveedor) == ("B00000001", "UNO SL")
    assert (peticion.cod_contrato, peticion.database) == ("CTSB26/0472", "ruesma")
    assert peticion.su_referencia is None


@pytest.mark.parametrize(
    "cambio",
    [
        {"importe_mes": "7085.48"}, {"importe_mes": True}, {"periodo": "202608"},
        {"periodo": 202608.0}, {"importe_anterior": "1"}, {"numero_orden": "2"},
        {"numero_orden": -1}, {"fecha_proforma": "20260831"}, {"importe_mes": float("nan")},
        {"referencia_externa": ""}, {"referencia_externa": "P" * 129}, {"usu": "u" * 25},
        {"cod_obra": ""}, {"nombre_proveedor": ""}, {"nombre_proveedor": "N" * 129},
        {"su_referencia": "S" * 129}, {"cod_contrato": "C" * 25}, {"cif_proveedor": "C" * 25},
        {"lineas": []}, {"campo_que_no_existe": 1}, {"sin_contrato": "si"},
    ],
)
def test_f007_r1_no_valida(cambio: dict[str, Any]) -> None:
    invalida(**cambio)


@pytest.mark.parametrize("periodo", [202600, 202613, 20260, 1202608, 189912])
def test_f007_r1_periodo_aaaamm_con_mes_de_1_a_12(periodo: int) -> None:
    invalida(periodo=periodo)


@pytest.mark.parametrize("periodo", [202601, 202612, 199001])
def test_f007_r1_periodo_valido(periodo: int) -> None:
    assert valida(periodo=periodo).periodo == periodo


@pytest.mark.parametrize("fecha", [20260231, 20261301, 2026083, 20260800])
def test_f007_r1_fecha_proforma_es_una_fecha(fecha: int) -> None:
    invalida(fecha_proforma=fecha)


def test_f007_r1_fecha_proforma_valida() -> None:
    assert valida(fecha_proforma=20260831).fecha_proforma == 20260831


# =====================================================================================
# R2 · la línea
# =====================================================================================


def test_f007_r2_linea_con_sus_opcionales() -> None:
    peticion = valida(lineas=[linea(partida=" 02.03.02.01 ", medicion_contrato=403.058,
                                    partida_imputacion=" 02.03.02.02 ", unidad=" M3 ")])
    datos = peticion.lineas[0]
    assert (datos.partida, datos.partida_imputacion, datos.unidad) == (
        "02.03.02.01", "02.03.02.02", "M3"
    )
    assert datos.medicion_contrato == 403.058
    assert (datos.cantidad_anterior, datos.cantidad_origen) == (241.0, 861.0)


@pytest.mark.parametrize(
    "cambio",
    [
        {"producto": "SM1004"},                          # ctrpro_ide y producto juntos
        {"cantidad": 0}, {"cantidad": 0.0}, {"cantidad": "1"}, {"precio": "11"},
        {"descripcion": None}, {"descripcion": ""}, {"descripcion": "   "}, {"descripcion": "D" * 129},
        {"referencia_linea": ""}, {"referencia_linea": "R" * 25}, {"unidad": "U" * 9},
        {"ctrpro_ide": 0}, {"ctrpro_ide": "262990"}, {"medicion_contrato": "1"},
        {"cantidad_anterior": "1"}, {"partida": ""}, {"partida_imputacion": "P" * 25},
        {"producto_que_no_existe": 1}, {"precio": float("inf")},
    ],
)
def test_f007_r2_linea_no_valida(cambio: dict[str, Any]) -> None:
    invalida(lineas=[linea(**cambio)])


def test_f007_r2_descripcion_obligatoria() -> None:
    sin = linea()
    del sin["descripcion"]
    invalida(lineas=[sin])


def test_f007_r2_cantidad_negativa_vale() -> None:
    assert valida(lineas=[linea(cantidad=-3.5)]).lineas[0].cantidad == -3.5


def test_f007_r2_referencia_de_linea_unica() -> None:
    invalida(lineas=[linea(), nueva(referencia_linea="F09")])
    invalida(lineas=[linea(), nueva(referencia_linea=" F09 ")])


def test_f007_r2_linea_sin_ctrpro_ni_producto_valida_en_el_modelo() -> None:
    """Respaldo (R14) o `producto_obligatorio` (R16): lo decide el caso de uso."""
    sin_nada = nueva()
    del sin_nada["producto"]
    assert valida(lineas=[sin_nada]).lineas[0].producto is None


@pytest.mark.parametrize(
    "cambio, de_contrato",
    [
        ({}, True),
        ({"ctrpro_ide": None, "medicion_contrato": 403.058}, True),
        ({"ctrpro_ide": None, "medicion_contrato": 0.0}, False),
        ({"ctrpro_ide": None, "medicion_contrato": -1.0}, False),
        ({"ctrpro_ide": None}, False),
    ],
)
def test_f007_r13_de_contrato_por_ctrpro_o_medicion_positiva(
    cambio: dict[str, Any], de_contrato: bool
) -> None:
    assert LineaProformaIn.model_validate(linea(**cambio)).de_contrato is de_contrato


# =====================================================================================
# R3 · contrato, proveedor y sin contrato
# =====================================================================================


@pytest.mark.parametrize(
    "cambio",
    [
        {"nombre_proveedor": None},                                            # nada que resuelva
        {"nombre_proveedor": None, "sin_contrato": True, "lineas": [nueva()]},  # sin CIF
        {"sin_contrato": True, "lineas": [nueva()]},                            # con nombre, sin CIF
        {"cif_proveedor": "B00000001", "sin_contrato": True, "cod_contrato": "CTSB26/0472",
         "lineas": [nueva()]},
        {"cif_proveedor": "B00000001", "sin_contrato": True},                  # con ctrpro_ide
    ],
)
def test_f007_r3_sus_cuatro_variantes_no_validan(cambio: dict[str, Any]) -> None:
    invalida(**cambio)


@pytest.mark.parametrize(
    "cambio",
    [
        {"nombre_proveedor": None, "cod_contrato": "CTSB26/0472"},
        {"nombre_proveedor": None, "cif_proveedor": "B00000001"},
        {},
        {"nombre_proveedor": None, "cif_proveedor": "B00000001", "sin_contrato": True,
         "lineas": [nueva()]},
        {"nombre_proveedor": "UNO", "cif_proveedor": "B00000001", "sin_contrato": True,
         "lineas": [nueva(), nueva(referencia_linea="F24", medicion_contrato=5.0)]},
    ],
)
def test_f007_r3_lo_que_si_vale(cambio: dict[str, Any]) -> None:
    assert valida(**cambio)


# =====================================================================================
# R6 · errores con código y conjuntos cerrados
# =====================================================================================


def test_f007_r6_codigos_de_cabecera_nuevos_y_heredados() -> None:
    assert CODIGOS_CABECERA_PROFORMA == CODIGOS_CABECERA | {
        "escritura_proformas_deshabilitada", "periodo_no_valido", "contrato_no_resuelto",
        "contrato_de_otro_proveedor", "hoja_de_varios_contratos", "importe_mes_no_cuadra",
        "hoja_descuadrada", "proforma_del_mes_existente",
    }
    assert ProformaError.codigos is CODIGOS_CABECERA_PROFORMA


def test_f007_r6_codigos_de_linea_y_avisos_nuevos() -> None:
    assert CODIGOS_LINEA_PROFORMA == CODIGOS_LINEA | {
        "linea_ambigua", "producto_obligatorio", "linea_descuadrada",
    }
    assert CODIGOS_AVISO_PROFORMA == CODIGOS_AVISO | {
        "anterior_distinto_de_sigrid", "supera_contrato", "supera_contrato_10",
        "contrato_a_origen", "otra_del_mes",
    }
    assert FalloLineaProforma.codigos is CODIGOS_LINEA_PROFORMA
    assert AvisoProforma.codigos is CODIGOS_AVISO_PROFORMA


def test_f007_r6_los_nuevos_no_entran_en_los_conjuntos_de_albaranes() -> None:
    assert not (CODIGOS_CABECERA_PROFORMA - CODIGOS_CABECERA) & CODIGOS_CABECERA
    with pytest.raises(ValueError):
        AlbaranCompraError("x", codigo="contrato_no_resuelto")
    with pytest.raises(ValidationError):
        FalloLinea(indice=0, referencia_linea="F09", codigo="linea_ambigua", mensaje="x")


def test_f007_r6_proforma_error_es_un_error_de_albaran() -> None:
    exc = ProformaError("No hay contrato.", codigo="contrato_no_resuelto")
    assert isinstance(exc, AlbaranCompraError)
    assert (exc.codigo, exc.lineas, exc.reparto, str(exc)) == (
        "contrato_no_resuelto", [], {}, "No hay contrato."
    )
    assert ProformaError("x", codigo="contrato_ambiguo").codigo == "contrato_ambiguo"


def test_f007_r6_codigo_desconocido_no_se_construye() -> None:
    with pytest.raises(ValueError, match="no es un codigo de error"):
        ProformaError("x", codigo="me_lo_invento")


def test_f007_r9_hoja_de_varios_contratos_lleva_reparto() -> None:
    exc = ProformaError("x", codigo="hoja_de_varios_contratos",
                        reparto={"F09": "CTSB24/0901", "F10": "CTSB25/0043"})
    assert exc.reparto == {"F09": "CTSB24/0901", "F10": "CTSB25/0043"}
    with pytest.raises(ValueError):
        ProformaError("x", codigo="hoja_de_varios_contratos")
    with pytest.raises(ValueError):
        ProformaError("x", codigo="contrato_ambiguo", reparto={"F09": "CTSB24/0901"})


def test_f007_r6_lineas_no_validas_con_candidatos() -> None:
    fallo = FalloLineaProforma(indice=1, referencia_linea="F10", codigo="linea_ambigua",
                               mensaje="Varias", candidatos=[11, 12])
    exc = ProformaError("1 linea", codigo="lineas_no_validas", lineas=[fallo])
    assert exc.lineas[0].model_dump() == {
        "indice": 1, "referencia_linea": "F10", "codigo": "linea_ambigua", "mensaje": "Varias",
        "candidatos": [11, 12],
    }
    assert FalloLineaProforma(indice=0, referencia_linea="F", codigo="precio_negativo",
                              mensaje="x").candidatos == []
    with pytest.raises(ValueError):
        ProformaError("x", codigo="lineas_no_validas")


@pytest.mark.parametrize("codigo", sorted(CODIGOS_AVISO_PROFORMA))
def test_f007_r6_avisos_de_proforma(codigo: str) -> None:
    assert AvisoProforma(codigo=codigo, mensaje="m").codigo == codigo


def test_f007_r6_aviso_desconocido() -> None:
    with pytest.raises(ValidationError):
        AvisoProforma(codigo="no_existe", mensaje="m")


# =====================================================================================
# R10, R30 · la respuesta
# =====================================================================================


def _respuesta(**cambios: Any) -> ProformaResponse:
    base: dict[str, Any] = {
        "database": "ruesma", "committed": False, "dry_run": True, "con_ide": 2831541,
        "cod": "AC26/25548", "cabecera": {"fec": 20260831}, "estado": "existente",
        "referencia_externa": "PRF-1",
        "contrato": {"cod": "CTSB26/0472", "ide": 2793879, "resuelto_por": "proveedor",
                     "candidatos": ["CTSB26/0472"]},
        "origen": {"importe_anterior_sigrid": 2651.0, "importe_mes": 17024.28,
                   "importe_origen": 19675.28, "importe_contrato": 64897.38,
                   "porcentaje_contrato": 30.3},
        "lineas": [{"indice": 0, "referencia_linea": "", "ctrpro_ide": 262990, "linoriide": 262990,
                    "proide": 0, "producto": "SM1004", "cantidad": 620.0, "precio": 11.0,
                    "total": 6820.0, "importe": 6820.0, "iva_cuota": 0.0, "almide": 0,
                    "dcapro_ide": 1352729, "de_contrato": True,
                    "avisos": [{"codigo": "anterior_distinto_de_sigrid", "mensaje": "lin"}]}],
        "avisos": [{"codigo": "supera_contrato", "mensaje": "cab"}],
    }
    return ProformaResponse.model_validate({**base, **cambios})


def test_f007_r30_respuesta_existente_con_contrato_origen_y_lineas() -> None:
    respuesta = _respuesta()
    assert isinstance(respuesta, AlbaranCompraResponse)
    assert respuesta.estado == "existente"
    assert respuesta.contrato == ContratoResuelto(cod="CTSB26/0472", ide=2793879,
                                                  resuelto_por="proveedor",
                                                  candidatos=["CTSB26/0472"])
    assert respuesta.origen == OrigenProforma(
        importe_anterior_sigrid=2651.0, importe_mes=17024.28, importe_origen=19675.28,
        importe_contrato=64897.38, porcentaje_contrato=30.3,
    )
    fila = respuesta.lineas[0]
    assert isinstance(fila, LineaProformaResultado)
    assert (fila.dcapro_ide, fila.linoriide, fila.producto, fila.importe, fila.de_contrato) == (
        1352729, 262990, "SM1004", 6820.0, True
    )
    assert fila.cantidad_anterior_sigrid is None
    assert respuesta.warnings == ["cab", "lin"]


@pytest.mark.parametrize("estado", ["previsto", "creado", "idempotente", "existente"])
def test_f007_r30_estados(estado: str) -> None:
    assert _respuesta(estado=estado).estado == estado


def test_f007_r30_estado_desconocido() -> None:
    with pytest.raises(ValidationError):
        _respuesta(estado="duplicado")


def test_f007_r30_sin_contrato_contrato_y_origen_nulos() -> None:
    respuesta = _respuesta(contrato=None, origen=None)
    assert (respuesta.contrato, respuesta.origen) == (None, None)
    assert "contrato" in respuesta.model_dump() and respuesta.model_dump()["origen"] is None


def test_f007_r10_resuelto_por_cerrado() -> None:
    for resuelto in ("peticion", "proveedor", "lineas"):
        assert ContratoResuelto(cod="C", ide=1, resuelto_por=resuelto, candidatos=["C"])
    with pytest.raises(ValidationError):
        ContratoResuelto(cod="C", ide=1, resuelto_por="nombre", candidatos=[])


def test_f007_r30_avisos_de_proforma_en_cabecera_y_linea() -> None:
    with pytest.raises(ValidationError):
        _respuesta(avisos=[{"codigo": "no_existe", "mensaje": "x"}])


def test_f007_r30_porcentaje_puede_faltar() -> None:
    origen = OrigenProforma(importe_anterior_sigrid=0.0, importe_mes=1.0, importe_origen=1.0,
                            importe_contrato=0.0, porcentaje_contrato=None)
    assert origen.porcentaje_contrato is None


def test_f007_r30_sin_columnas_bancarias_como_el_nucleo() -> None:
    respuesta = _respuesta(cabecera={"fec": 1, "banban": 21, "bancue": "ES12"},
                           filas={"dca": {"ide": 1, "cpacue1": "ES34"}})
    assert respuesta.cabecera == {"fec": 1}
    assert respuesta.filas["dca"] == {"ide": 1}


# =====================================================================================
# T18 · bordes de los campos (huecos de la campana de mutacion)
# =====================================================================================


@pytest.mark.parametrize(
    "campo", ["database", "usu", "referencia_externa", "cod_obra", "cod_contrato",
              "cif_proveedor", "nombre_proveedor"],
)
def test_f007_t18_textos_de_cabecera_de_un_caracter(campo: str) -> None:
    assert getattr(valida(**{campo: "X"}), campo) == "X"


@pytest.mark.parametrize("campo", ["partida", "producto", "partida_imputacion"])
def test_f007_t18_textos_de_linea_de_un_caracter(campo: str) -> None:
    assert getattr(valida(lineas=[nueva(**{campo: "X"})]).lineas[0], campo) == "X"


def test_f007_t18_textos_de_24_y_no_de_25() -> None:
    assert valida(cod_obra="9" * 24).cod_obra == "9" * 24
    invalida(cod_obra="9" * 25)
    for campo in ("partida", "producto"):
        assert getattr(valida(lineas=[nueva(**{campo: "P" * 24})]).lineas[0], campo) == "P" * 24
        invalida(lineas=[nueva(**{campo: "P" * 25})])


def test_f007_t18_origenes_estrictos() -> None:
    invalida(importe_origen="9736.48")
    invalida(lineas=[linea(cantidad_origen="861")])


def test_f007_t18_numero_de_orden_cero() -> None:
    assert valida(numero_orden=0).numero_orden == 0


@pytest.mark.parametrize("periodo", [190001, 299912])
def test_f007_t18_periodo_en_los_bordes(periodo: int) -> None:
    assert valida(periodo=periodo).periodo == periodo


@pytest.mark.parametrize("fecha", [19000101, 29991231, 20240229])
def test_f007_t18_fecha_proforma_en_los_bordes_y_el_29_de_febrero(fecha: int) -> None:
    assert valida(periodo=fecha // 100, fecha_proforma=fecha).fecha_proforma == fecha


def test_f007_t18_fecha_proforma_29_de_febrero_de_un_anio_no_bisiesto() -> None:
    invalida(periodo=202302, fecha_proforma=20230229)


@pytest.mark.parametrize("fecha", [18991231, 30000101])
def test_f007_t18_fecha_proforma_fuera_de_los_anios(fecha: int) -> None:
    invalida(periodo=fecha // 100, fecha_proforma=fecha)


@pytest.mark.parametrize("periodo", [189912, 300001, 202600, 202613])
def test_f007_t18_periodo_fuera_de_los_anios_o_del_mes(periodo: int) -> None:
    invalida(periodo=periodo)
