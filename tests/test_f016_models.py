# tests/test_f016_models.py
"""
F-016 T2 · R1, R3, R19, R20: los modelos de la proforma a origen.

La peticion de F-007 admite `modo`, `proforma_anterior`, `primera_de_cadena` y,
por linea, `linea_anterior`, con las reglas de R3 (400 de F-012 sin `codigo`).
Los codigos, errores y respuestas nuevos viven en subclases
(`domain/models/proforma_origen_models.py`): los conjuntos y clases de F-007
no cambian y una respuesta de mes no trae ninguna clave nueva. Sin red ni base.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.models import proforma_models
from domain.models.proforma_models import (
    CODIGOS_AVISO_PROFORMA,
    CODIGOS_CABECERA_PROFORMA,
    CODIGOS_LINEA_PROFORMA,
    AvisoProforma,
    FalloLineaProforma,
    LineaProformaIn,
    LineaProformaResultado,
    ProformaError,
    ProformaRequest,
    ProformaResponse,
)
from domain.models.proforma_origen_models import (
    CODIGOS_AVISO_PROFORMA_ORIGEN,
    CODIGOS_CABECERA_PROFORMA_ORIGEN,
    CODIGOS_LINEA_PROFORMA_ORIGEN,
    AnteriorCadena,
    AvisoProformaOrigen,
    CadenaProforma,
    FalloLineaProformaOrigen,
    LineaProformaOrigenResultado,
    ProformaOrigenError,
    ProformaOrigenResponse,
)


def linea(**cambios: Any) -> dict[str, Any]:
    base = {"referencia_linea": "F09", "ctrpro_ide": 262990, "unidad": "M3",
            "descripcion": "VERTIDO HORMIGON", "cantidad": 620, "precio": 11}
    return {**base, **cambios}


def nueva(**cambios: Any) -> dict[str, Any]:
    base = {"referencia_linea": "F23", "producto": "SM1004", "partida": "02.20.02.02.11",
            "descripcion": "BERENJENO", "cantidad": 75.85, "precio": 3.5}
    return {**base, **cambios}


def cuerpo(**cambios: Any) -> dict[str, Any]:
    base = {"database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-1",
            "cod_obra": "0719", "periodo": 202608, "nombre_proveedor": "SUBCONTRATA UNO",
            "importe_mes": 7085.48, "lineas": [linea(), nueva()]}
    return {**base, **cambios}


def a_origen(**cambios: Any) -> dict[str, Any]:
    return cuerpo(**{"modo": "origen", "proforma_anterior": "PROF26/00201", **cambios})


# =====================================================================================
# R1 · sin `modo`, la peticion de F-007
# =====================================================================================


def test_f016_r1_sin_modo_es_de_mes_y_sin_cadena() -> None:
    peticion = ProformaRequest(**cuerpo())
    assert (peticion.modo, peticion.proforma_anterior, peticion.primera_de_cadena) == (
        "mes", None, False)
    assert [l.linea_anterior for l in peticion.lineas] == [None, None]


def test_f016_r1_modo_mes_explicito_es_lo_mismo() -> None:
    assert ProformaRequest(**cuerpo(modo="mes")) == ProformaRequest(**cuerpo())


@pytest.mark.parametrize("modo", ["MES", "Origen", "trimestre", "", 1, None])
def test_f016_r3_modo_cerrado(modo: object) -> None:
    with pytest.raises(ValidationError):
        ProformaRequest(**cuerpo(modo=modo))


# =====================================================================================
# R3 · los campos nuevos y sus reglas
# =====================================================================================


def test_f016_r3_a_origen_con_anterior_y_lineas_continuadas() -> None:
    peticion = ProformaRequest(**a_origen(
        proforma_anterior="  PROF26/00201 ",
        lineas=[linea(linea_anterior=1400001), nueva(linea_anterior=1400004)],
    ))
    assert (peticion.modo, peticion.proforma_anterior, peticion.primera_de_cadena) == (
        "origen", "PROF26/00201", False)
    assert [l.linea_anterior for l in peticion.lineas] == [1400001, 1400004]


def test_f016_r3_a_origen_primera_de_cadena() -> None:
    peticion = ProformaRequest(**cuerpo(modo="origen", primera_de_cadena=True))
    assert (peticion.proforma_anterior, peticion.primera_de_cadena) == (None, True)


def test_f016_r3_a_origen_sin_importes_de_la_hoja_valida() -> None:
    """Los importes y las cantidades de la hoja siguen siendo opcionales."""
    peticion = ProformaRequest(**a_origen(importe_anterior=None, importe_origen=None))
    assert (peticion.importe_anterior, peticion.importe_origen) == (None, None)
    assert all(l.cantidad_anterior is None and l.cantidad_origen is None for l in peticion.lineas)


def test_f016_r3_proforma_anterior_de_1_a_24() -> None:
    assert ProformaRequest(**a_origen(proforma_anterior="P")).proforma_anterior == "P"
    assert ProformaRequest(**a_origen(proforma_anterior="P" * 24)).proforma_anterior == "P" * 24
    for malo in ("P" * 25, "", "   ", 26201):
        with pytest.raises(ValidationError):
            ProformaRequest(**a_origen(proforma_anterior=malo))


def test_f016_r3_linea_anterior_entero_desde_1_estricto() -> None:
    ok = ProformaRequest(**a_origen(lineas=[linea(linea_anterior=1), nueva()]))
    assert ok.lineas[0].linea_anterior == 1
    for malo in (0, -5, "1400001", 1.0, True):
        with pytest.raises(ValidationError):
            LineaProformaIn(**linea(linea_anterior=malo))


@pytest.mark.parametrize(
    "cambios",
    [
        {"modo": "origen"},
        {"modo": "origen", "proforma_anterior": "PROF26/00201", "primera_de_cadena": True},
        {"proforma_anterior": "PROF26/00201"},
        {"modo": "mes", "proforma_anterior": "PROF26/00201"},
        {"primera_de_cadena": True},
        {"lineas": [linea(linea_anterior=1400001), nueva()]},
        {"modo": "origen", "primera_de_cadena": True,
         "lineas": [linea(linea_anterior=1400001), nueva()]},
        {"modo": "origen", "proforma_anterior": "PROF26/00201",
         "lineas": [linea(linea_anterior=1400001), nueva(linea_anterior=1400001)]},
        {"modo": "origen", "primera_de_cadena": True, "sin_contrato": True,
         "cif_proveedor": "B00000001", "nombre_proveedor": None, "lineas": [nueva()]},
    ],
    ids=["origen_sin_anterior_ni_primera", "origen_con_las_dos", "anterior_sin_modo",
         "anterior_en_mes", "primera_sin_modo", "linea_anterior_sin_modo",
         "linea_anterior_en_primera", "linea_anterior_repetida", "origen_sin_contrato"],
)
def test_f016_r3_combinaciones_que_no_validan(cambios: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ProformaRequest(**cuerpo(**cambios))


def test_f016_r3_sin_contrato_de_mes_sigue_valiendo() -> None:
    peticion = ProformaRequest(**cuerpo(sin_contrato=True, cif_proveedor="B00000001",
                                        nombre_proveedor=None, lineas=[nueva()]))
    assert (peticion.sin_contrato, peticion.modo) == (True, "mes")


def test_f016_r3_primera_de_cadena_false_explicita_en_mes_vale() -> None:
    assert ProformaRequest(**cuerpo(primera_de_cadena=False)).primera_de_cadena is False


def test_f016_r3_lineas_anteriores_distintas_y_nuevas_sin_ella() -> None:
    peticion = ProformaRequest(**a_origen(lineas=[
        linea(linea_anterior=7), linea(referencia_linea="F10", linea_anterior=8),
        nueva(), nueva(referencia_linea="F24"),
    ]))
    assert [l.linea_anterior for l in peticion.lineas] == [7, 8, None, None]


def test_f016_r3_las_reglas_de_f007_se_comprueban_antes() -> None:
    """Con `referencia_linea` repetida Y a origen sin anterior, el mensaje es el de F-007."""
    with pytest.raises(ValidationError) as excinfo:
        ProformaRequest(**cuerpo(modo="origen", lineas=[linea(), linea()]))
    assert "repetida" in str(excinfo.value)


# =====================================================================================
# R20 · F-007 no cambia; lo nuevo, en subclases
# =====================================================================================

_CABECERA_F007 = frozenset({
    "almacen_de_obra_no_resuelto", "base_de_datos_no_permitida", "colision_de_clave",
    "contrato_ambiguo", "contrato_de_otro_proveedor", "contrato_no_encontrado",
    "contrato_no_resuelto", "demasiadas_lineas", "escritura_albaranes_deshabilitada",
    "escritura_proformas_deshabilitada", "estado_inicial_no_encontrado",
    "filas_afectadas_inesperadas", "hoja_de_varios_contratos", "hoja_descuadrada",
    "importe_mes_no_cuadra", "lineas_no_validas", "obra_ambigua", "obra_de_empresa_no_permitida",
    "obra_no_encontrada", "periodo_no_valido", "peticion_mixta", "proforma_del_mes_existente",
    "proveedor_ambiguo", "proveedor_no_encontrado", "referencia_en_conflicto",
    "referencia_no_permitida", "retencion_no_soportada", "usuario_no_valido",
})
_LINEA_F007 = frozenset({
    "analitica_no_resuelta", "linea_ambigua", "linea_descuadrada", "linea_no_es_del_contrato",
    "naturaleza_no_valida", "paride_no_valido", "partida_ambigua", "partida_no_encontrada",
    "partida_no_imputable", "precio_negativo", "producto_no_encontrado", "producto_no_permitido",
    "producto_obligatorio",
})
_AVISO_F007 = frozenset({
    "anterior_distinto_de_sigrid", "cabecera_sin_dato", "cod_provisional", "contrato_a_origen",
    "iva_de_otro_proveedor", "otra_del_mes", "partida_distinta_del_contrato",
    "precio_distinto_del_contrato", "producto_sin_historico", "retencion_del_contrato",
    "servido_negativo", "sin_partida_en_linea_con_partida", "stock_negativo", "supera_contrato",
    "supera_contrato_10", "supera_pendiente",
})


def test_f016_r20_los_conjuntos_de_f007_identicos() -> None:
    assert CODIGOS_CABECERA_PROFORMA == _CABECERA_F007
    assert CODIGOS_LINEA_PROFORMA == _LINEA_F007
    assert CODIGOS_AVISO_PROFORMA == _AVISO_F007
    assert ProformaError.codigos is proforma_models.CODIGOS_CABECERA_PROFORMA
    assert FalloLineaProforma.codigos is proforma_models.CODIGOS_LINEA_PROFORMA
    assert AvisoProforma.codigos is proforma_models.CODIGOS_AVISO_PROFORMA


def test_f016_r20_los_codigos_nuevos_en_las_subclases() -> None:
    assert CODIGOS_CABECERA_PROFORMA_ORIGEN == _CABECERA_F007 | {
        "escritura_proformas_origen_deshabilitada", "anterior_no_valida", "anterior_con_sucesora"}
    assert CODIGOS_LINEA_PROFORMA_ORIGEN == _LINEA_F007 | {"linea_anterior_no_valida"}
    assert CODIGOS_AVISO_PROFORMA_ORIGEN == _AVISO_F007 | {"linea_nueva_ya_en_la_anterior"}
    assert ProformaOrigenError.codigos is CODIGOS_CABECERA_PROFORMA_ORIGEN
    assert FalloLineaProformaOrigen.codigos is CODIGOS_LINEA_PROFORMA_ORIGEN
    assert AvisoProformaOrigen.codigos is CODIGOS_AVISO_PROFORMA_ORIGEN
    assert issubclass(ProformaOrigenError, ProformaError)
    assert issubclass(FalloLineaProformaOrigen, FalloLineaProforma)
    assert issubclass(AvisoProformaOrigen, AvisoProforma)
    assert issubclass(LineaProformaOrigenResultado, LineaProformaResultado)
    assert issubclass(ProformaOrigenResponse, ProformaResponse)


@pytest.mark.parametrize(
    "codigo", ["escritura_proformas_origen_deshabilitada", "anterior_no_valida",
               "anterior_con_sucesora"])
def test_f016_r20_errores_nuevos_solo_en_la_subclase(codigo: str) -> None:
    error = ProformaOrigenError("mensaje", codigo=codigo)
    assert (error.codigo, str(error), error.lineas, error.reparto) == (codigo, "mensaje", [], {})
    with pytest.raises(ValueError):
        ProformaError("mensaje", codigo=codigo)


def test_f016_r20_la_subclase_admite_los_de_f007() -> None:
    assert ProformaOrigenError("x", codigo="proforma_del_mes_existente").codigo == (
        "proforma_del_mes_existente")
    fallo = FalloLineaProformaOrigen(indice=0, referencia_linea="F09", codigo="linea_ambigua",
                                     mensaje="x", candidatos=[1, 2])
    assert fallo.candidatos == [1, 2]


def test_f016_r20_fallo_de_linea_nuevo_solo_en_la_subclase() -> None:
    fallo = FalloLineaProformaOrigen(indice=2, referencia_linea="F16",
                                     codigo="linea_anterior_no_valida", mensaje="x")
    error = ProformaOrigenError("x", codigo="lineas_no_validas", lineas=[fallo])
    assert error.lineas == [fallo]
    with pytest.raises(ValidationError):
        FalloLineaProforma(indice=2, referencia_linea="F16", codigo="linea_anterior_no_valida",
                           mensaje="x")


def test_f016_r20_aviso_nuevo_con_las_lineas_de_la_anterior() -> None:
    aviso = AvisoProformaOrigen(codigo="linea_nueva_ya_en_la_anterior", mensaje="x",
                                lineas_anterior=[1400001, 1400005])
    assert aviso.model_dump() == {"codigo": "linea_nueva_ya_en_la_anterior", "mensaje": "x",
                                  "lineas_anterior": [1400001, 1400005]}
    assert AvisoProformaOrigen(codigo="otra_del_mes", mensaje="y").lineas_anterior == []
    with pytest.raises(ValidationError):
        AvisoProforma(codigo="linea_nueva_ya_en_la_anterior", mensaje="x")
    with pytest.raises(ValidationError):
        AvisoProformaOrigen(codigo="inventado", mensaje="x")


# =====================================================================================
# R19 · la respuesta a origen; R1 · la de mes, sin claves nuevas
# =====================================================================================

_RESPUESTA_F007 = {
    "avisos", "cabecera", "cod", "committed", "con_ide", "contrato", "database", "dry_run",
    "estado", "estados_contrato", "filas", "lineas", "movimientos", "ok", "origen",
    "referencia_externa", "totales", "warnings",
}
_LINEA_RESPUESTA_F007 = {
    "almide", "avisos", "cantidad", "cantidad_anterior_sigrid", "cenide", "ctrpro_ide",
    "dcapro_ide", "de_contrato", "importe", "indice", "iva_cuota", "linoriide", "paride",
    "partida", "pmp_anterior", "pmp_resultante", "pos", "precio", "producto", "proide",
    "referencia_linea", "res", "stock_anterior", "stock_resultante", "tipo", "total", "unimed",
}


def _linea_resultado(**extra: Any) -> dict[str, Any]:
    return {"indice": 0, "referencia_linea": "F09", "ctrpro_ide": 262990, "linoriide": 262990,
            "proide": 610004, "cantidad": 620.0, "precio": 11.0, "total": 6820.0,
            "iva_cuota": 0.0, "almide": 70, **extra}


def _respuesta(**extra: Any) -> dict[str, Any]:
    return {"database": "ruesma", "committed": False, "dry_run": True, "con_ide": 2900001,
            "cod": "PROF26/01282", "cabecera": {"docoritip": 1}, "estado": "previsto",
            "referencia_externa": "PRF-1", **extra}


def test_f016_r1_la_respuesta_de_mes_no_trae_claves_nuevas() -> None:
    respuesta = ProformaResponse(**_respuesta(lineas=[LineaProformaResultado(**_linea_resultado())]))
    volcado = respuesta.model_dump(mode="json")
    assert set(volcado) == _RESPUESTA_F007
    assert set(volcado["lineas"][0]) == _LINEA_RESPUESTA_F007


def test_f016_r19_la_respuesta_a_origen_con_cadena_y_campos_de_linea() -> None:
    cadena = CadenaProforma(
        anterior=AnteriorCadena(cod="PROF26/00201", ide=2850251), primera_de_cadena=False,
        importe_anterior_cadena=1606.0, importe_origen_cadena=18630.28, n_arrastradas=2,
    )
    continuada = LineaProformaOrigenResultado(**_linea_resultado(
        linea_anterior=1400001, arrastrada=False, cantidad_anterior_cadena=241.0,
        cantidad_origen_cadena=861.0,
        avisos=[AvisoProformaOrigen(codigo="linea_nueva_ya_en_la_anterior", mensaje="m",
                                    lineas_anterior=[1400005])],
    ))
    respuesta = ProformaOrigenResponse(**_respuesta(lineas=[continuada], cadena=cadena))
    volcado = respuesta.model_dump(mode="json")
    assert set(volcado) == _RESPUESTA_F007 | {"cadena"}
    assert volcado["cadena"] == {
        "anterior": {"cod": "PROF26/00201", "ide": 2850251}, "primera_de_cadena": False,
        "importe_anterior_cadena": 1606.0, "importe_origen_cadena": 18630.28, "n_arrastradas": 2,
    }
    assert set(volcado["lineas"][0]) == _LINEA_RESPUESTA_F007 | {
        "linea_anterior", "arrastrada", "cantidad_anterior_cadena", "cantidad_origen_cadena"}
    assert volcado["lineas"][0]["avisos"][0]["lineas_anterior"] == [1400005]
    assert respuesta.warnings == ["m"]


def test_f016_r19_valores_por_defecto_de_lo_nuevo() -> None:
    respuesta = ProformaOrigenResponse(**_respuesta(
        lineas=[LineaProformaOrigenResultado(**_linea_resultado())]))
    assert respuesta.cadena is None
    linea_ = respuesta.lineas[0]
    assert (linea_.linea_anterior, linea_.arrastrada, linea_.cantidad_anterior_cadena,
            linea_.cantidad_origen_cadena) == (None, None, None, None)
    primera = CadenaProforma(anterior=None, primera_de_cadena=True, importe_anterior_cadena=0.0,
                             importe_origen_cadena=5.0, n_arrastradas=0)
    assert primera.anterior is None


def test_f016_r19_los_avisos_de_la_respuesta_a_origen_son_los_ampliados() -> None:
    respuesta = ProformaOrigenResponse(**_respuesta(
        avisos=[{"codigo": "otra_del_mes", "mensaje": "m"}],
        lineas=[_linea_resultado(avisos=[{"codigo": "linea_nueva_ya_en_la_anterior",
                                          "mensaje": "n", "lineas_anterior": [7]}])],
    ))
    assert type(respuesta.avisos[0]) is AvisoProformaOrigen
    assert type(respuesta.lineas[0]) is LineaProformaOrigenResultado
    assert respuesta.lineas[0].avisos[0].lineas_anterior == [7]
    with pytest.raises(ValidationError):
        ProformaResponse(**_respuesta(lineas=[_linea_resultado(
            avisos=[{"codigo": "linea_nueva_ya_en_la_anterior", "mensaje": "n"}])]))
