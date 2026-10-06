# tests/test_f009_models.py
"""
F-009 · R1, R5, R6, R7 y R9: el contrato del modo extendido de
`POST /api/sigrid/albaran` (`domain/models/albaran_compra_models.py`).

Sin red y sin base de datos. El detalle campo a campo está en
`specs/F-009-alta-albaran-compra/contrato_albaranes.md` §2-§3 (congelado: es la
referencia de F-053); estos tests fijan esa forma.
"""
from __future__ import annotations

import json
import math
from typing import Any

import pytest
from pydantic import ValidationError

from domain.models.albaran_compra_models import (
    CODIGOS_AVISO,
    CODIGOS_CABECERA,
    CODIGOS_LINEA,
    COLUMNAS_BANCARIAS,
    AlbaranCompraError,
    AlbaranCompraRequest,
    AlbaranCompraResponse,
    AvisoAlbaran,
    FalloLinea,
    LineaAlbaranIn,
    LineaResultado,
    elegir_modo_albaran,
    sin_columnas_bancarias,
)
from domain.models.albaran_domain_models import (
    AddPurchaseAlbaranResponse,
    AlbaranLinePreview,
)


def vinculada(**extra: Any) -> dict[str, Any]:
    return {"referencia_linea": "L1", "ctrpro_ide": 9001, "cantidad": 2.0, "precio": 10.5, **extra}


def sin_vincular(**extra: Any) -> dict[str, Any]:
    return {
        "referencia_linea": "L2",
        "producto": "MA9999",
        "descripcion": "Arena",
        "cantidad": 1.0,
        "precio": 3.25,
        **extra,
    }


def peticion(**extra: Any) -> dict[str, Any]:
    return {
        "database": "ruesma",
        "cod_obra": "0404",
        "usu": "prueba",
        "cif_proveedor": "B12345678",
        "referencia_externa": "ALB-123",
        "cod_contrato": "CTSU16/0206",
        "lineas": [vinculada(), sin_vincular()],
        **extra,
    }


# --- R1: el modo se decide por las claves presentes ------------------------------


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"lineas": []},
        {"lineas": None},
        {"referencia_externa": ""},
        {"referencia_externa": None, "cod_obra": "0404"},
        {"lineas": [1], "referencia_externa": "ALB-1"},
        peticion(),
    ],
)
def test_f009_r1_con_lineas_o_referencia_externa_es_extendido(cuerpo: dict[str, Any]) -> None:
    assert elegir_modo_albaran(cuerpo) == "extendido"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        {"lineas_recibidas": [{"ctrpro_ide": 1, "cantidad": 1}]},
        {"database": "ruesma", "cod_contrato": "X", "commit": True},
        {"Lineas": [], "REFERENCIA_EXTERNA": "ALB-1"},  # las claves son exactas
    ],
)
def test_f009_r1_sin_ninguna_de_las_dos_es_clasico(cuerpo: dict[str, Any]) -> None:
    assert elegir_modo_albaran(cuerpo) == "clasico"


@pytest.mark.parametrize("cuerpo", [None, [], [{"lineas": []}], "lineas", 42, b"{}"])
def test_f009_r1_lo_que_no_es_un_objeto_va_al_clasico(cuerpo: object) -> None:
    """Pydantic lo rechaza ahí igual que hoy."""
    assert elegir_modo_albaran(cuerpo) == "clasico"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"lineas": [], "lineas_recibidas": []},
        {"referencia_externa": "ALB-1", "lineas_recibidas": None},
        {**peticion(), "lineas_recibidas": [{"ctrpro_ide": 1, "cantidad": 1}]},
    ],
)
def test_f009_r1_peticion_mixta(cuerpo: dict[str, Any]) -> None:
    with pytest.raises(AlbaranCompraError) as error:
        elegir_modo_albaran(cuerpo)
    assert error.value.codigo == "peticion_mixta"
    assert error.value.lineas == []


# --- R5: validación de la cabecera -----------------------------------------------


def test_f009_r5_peticion_minima_valida_con_defectos() -> None:
    p = AlbaranCompraRequest.model_validate(peticion(cod_contrato=None, lineas=[sin_vincular()]))
    assert p.cod_contrato is None
    assert p.su_referencia == ""
    assert p.fecha_albaran is None
    assert p.empide is None
    assert p.commit is False
    assert p.lineas[0].partida is None
    assert p.lineas[0].paride is None


@pytest.mark.parametrize(
    "cif, esperado",
    [("b12345678", "B12345678"), (" b 1234 5678 ", "B12345678"), ("es\tb12\n345678", "ESB12345678")],
)
def test_f009_r5_cif_en_mayusculas_y_sin_espacios(cif: str, esperado: str) -> None:
    """H21: solo mayúsculas y espacios; el resto del formato es de albaranes."""
    assert AlbaranCompraRequest.model_validate(peticion(cif_proveedor=cif)).cif_proveedor == esperado


def test_f009_r5_textos_recortados() -> None:
    p = AlbaranCompraRequest.model_validate(
        peticion(
            database=" ruesma ",
            cod_obra=" 0404 ",
            usu=" prueba ",
            referencia_externa=" ALB-1 ",
            cod_contrato=" CTSU16/0206 ",
            su_referencia="  albaran 77  ",
            lineas=[
                sin_vincular(
                    referencia_linea=" L2 ",
                    producto=" MA9999 ",
                    descripcion=" Arena ",
                    unidad=" m3 ",
                    partida=" 01.02 ",
                )
            ],
        )
    )
    assert (p.database, p.cod_obra, p.usu, p.referencia_externa) == (
        "ruesma",
        "0404",
        "prueba",
        "ALB-1",
    )
    assert (p.cod_contrato, p.su_referencia) == ("CTSU16/0206", "albaran 77")
    linea = p.lineas[0]
    assert (linea.referencia_linea, linea.producto, linea.descripcion, linea.unidad, linea.partida) == (
        "L2",
        "MA9999",
        "Arena",
        "m3",
        "01.02",
    )


def test_f009_r5_su_referencia_nula_es_vacia() -> None:
    assert AlbaranCompraRequest.model_validate(peticion(su_referencia=None)).su_referencia == ""


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("database", ""),
        ("database", "   "),
        ("cod_obra", ""),
        ("cod_obra", "x" * 25),
        ("usu", ""),
        ("usu", "u" * 25),
        ("cif_proveedor", ""),
        ("cif_proveedor", " "),
        ("cif_proveedor", "B" * 25),
        ("referencia_externa", ""),
        ("referencia_externa", "A" * 129),
        ("cod_contrato", ""),
        ("cod_contrato", "C" * 25),
        ("su_referencia", "r" * 129),
        ("fecha_albaran", 19000100),
        ("fecha_albaran", 29991232),
        ("fecha_albaran", "20261006"),
        ("empide", 0),
        ("empide", "5"),
        ("lineas", []),
        ("lineas", None),
        ("almacen", "ALM"),          # no existe (v5.1)
        ("naturaleza", "MA99"),      # retirado en la v8 (H34)
        ("lineas_recibidas", []),
        ("otra", 1),
    ],
)
def test_f009_r5_cabecera_invalida_es_400_sin_codigo(campo: str, valor: object) -> None:
    with pytest.raises(ValidationError):
        AlbaranCompraRequest.model_validate(peticion(**{campo: valor}))


@pytest.mark.parametrize("campo", ["database", "cod_obra", "usu", "cif_proveedor", "referencia_externa", "lineas"])
def test_f009_r5_campos_obligatorios(campo: str) -> None:
    cuerpo = peticion()
    del cuerpo[campo]
    with pytest.raises(ValidationError):
        AlbaranCompraRequest.model_validate(cuerpo)


@pytest.mark.parametrize("fecha", [19000101, 20261006, 20991231, 29991231, 20261399])
def test_f009_r5_fecha_solo_en_rango(fecha: int) -> None:
    """Solo formato y rango (H19): ni futuras ni días imposibles se rechazan aquí."""
    assert AlbaranCompraRequest.model_validate(peticion(fecha_albaran=fecha)).fecha_albaran == fecha


def test_f009_r5_longitudes_maximas_admitidas() -> None:
    p = AlbaranCompraRequest.model_validate(
        peticion(
            cod_obra="o" * 24,
            usu="u" * 24,
            cif_proveedor="B" * 24,
            referencia_externa="A" * 128,
            cod_contrato="C" * 24,
            su_referencia="r" * 128,
            lineas=[
                sin_vincular(
                    referencia_linea="L" * 24,
                    producto="P" * 24,
                    descripcion="d" * 128,
                    unidad="u" * 8,
                    partida="p" * 24,
                )
            ],
        )
    )
    assert len(p.lineas[0].referencia_linea) == 24


# --- R6: validación de las líneas ---------------------------------------------------


@pytest.mark.parametrize(
    "linea",
    [
        vinculada(producto="MA9999"),                       # los dos
        {"referencia_linea": "L1", "cantidad": 1.0, "precio": 1.0},  # ninguno
        vinculada(cantidad=0),
        vinculada(cantidad=0.0),
        vinculada(cantidad=-0.0),
        sin_vincular(descripcion=None),
        sin_vincular(descripcion="   "),
        {k: v for k, v in sin_vincular().items() if k != "descripcion"},
        vinculada(paride=7),                                # paride sin partida
        sin_vincular(paride=7, partida=None),
        vinculada(paride=0, partida="01"),
        vinculada(ctrpro_ide=0),
        sin_vincular(producto=""),
        sin_vincular(producto="P" * 25),
        sin_vincular(descripcion="d" * 129),
        sin_vincular(unidad="u" * 9),
        vinculada(partida=""),
        vinculada(partida="p" * 25),
        vinculada(referencia_linea=""),
        vinculada(referencia_linea="L" * 25),
        vinculada(cantidad=math.inf),
        vinculada(cantidad=-math.inf),
        vinculada(cantidad=math.nan),
        vinculada(precio=math.inf),
        vinculada(precio=math.nan),
        vinculada(cantidad="2"),                            # números como números JSON
        vinculada(precio="10.5"),
        vinculada(cantidad=True),
        vinculada(ctrpro_ide="9001"),
        vinculada(ctrpro_ide=9001.0),
        vinculada(almacen="ALM"),                           # no existe (v5.1)
        sin_vincular(naturaleza="MA99"),                    # retirado (v8, H34)
        vinculada(otra=1),
    ],
)
def test_f009_r6_linea_invalida_es_400_sin_codigo(linea: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        AlbaranCompraRequest.model_validate(peticion(lineas=[linea]))


@pytest.mark.parametrize("campo", ["referencia_linea", "cantidad", "precio"])
def test_f009_r6_campos_obligatorios_de_linea(campo: str) -> None:
    linea = vinculada()
    del linea[campo]
    with pytest.raises(ValidationError):
        LineaAlbaranIn.model_validate(linea)


def test_f009_r6_referencia_linea_repetida() -> None:
    with pytest.raises(ValidationError, match="referencia_linea"):
        AlbaranCompraRequest.model_validate(
            peticion(lineas=[vinculada(referencia_linea="X"), sin_vincular(referencia_linea=" X ")])
        )


def test_f009_r6_vinculada_sin_cod_contrato() -> None:
    with pytest.raises(ValidationError, match="cod_contrato"):
        AlbaranCompraRequest.model_validate(peticion(cod_contrato=None, lineas=[vinculada()]))


@pytest.mark.parametrize(
    "lineas, extra",
    [
        ([vinculada(cantidad=-3.5), sin_vincular(cantidad=-1)], {}),     # devoluciones
        ([sin_vincular()], {"cod_contrato": "CTSU16/0206"}),              # contrato sin vinculadas (H31)
        ([sin_vincular(partida=None)], {}),                               # sin partida
        ([sin_vincular(partida="01.02", paride=33)], {}),                 # paride con partida (R14b)
        ([vinculada(precio=-1.0)], {}),                                   # precio < 0: lo para el caso de uso
        ([vinculada(precio=0)], {}),
        ([vinculada(descripcion=None, unidad=None)], {}),
        ([vinculada(), vinculada(referencia_linea="L1b")], {}),          # mismo ctrpro, dos líneas
        ([sin_vincular()], {"fecha_albaran": 29991231}),                  # futura (H19)
    ],
)
def test_f009_r6_lo_que_vale(lineas: list[dict[str, Any]], extra: dict[str, Any]) -> None:
    p = AlbaranCompraRequest.model_validate(peticion(lineas=lineas, **extra))
    assert [linea.referencia_linea for linea in p.lineas] == [
        linea["referencia_linea"] for linea in lineas
    ]


def test_f009_r6_vinculada_sin_descripcion_ni_unidad_las_deja_a_none() -> None:
    """Vacías tras recortar son ausentes: la vinculada las tomará del `ctrpro` (R12)."""
    linea = LineaAlbaranIn.model_validate(vinculada(descripcion="  ", unidad=""))
    assert linea.descripcion is None
    assert linea.unidad is None


def test_f009_r6_tipo_de_linea() -> None:
    assert LineaAlbaranIn.model_validate(vinculada()).tipo == "vinculada"
    assert LineaAlbaranIn.model_validate(sin_vincular()).tipo == "sin_vincular"


def test_f009_r6_el_orden_de_las_lineas_se_conserva() -> None:
    lineas = [sin_vincular(referencia_linea=f"R{i}") for i in range(5, 0, -1)]
    p = AlbaranCompraRequest.model_validate(peticion(lineas=lineas))
    assert [linea.referencia_linea for linea in p.lineas] == ["R5", "R4", "R3", "R2", "R1"]


def test_f009_r6_cantidad_entera_en_json_es_float() -> None:
    p = AlbaranCompraRequest.model_validate_json(json.dumps(peticion(lineas=[vinculada(cantidad=3)])))
    assert p.lineas[0].cantidad == 3.0
    assert isinstance(p.lineas[0].cantidad, float)


# --- R9: AlbaranCompraError con códigos cerrados -----------------------------------


def test_f009_r9_codigos_cerrados_de_design() -> None:
    assert CODIGOS_CABECERA == {
        "peticion_mixta",
        "escritura_albaranes_deshabilitada",
        "base_de_datos_no_permitida",
        "demasiadas_lineas",
        "referencia_no_permitida",
        "referencia_en_conflicto",
        "obra_no_encontrada",
        "obra_de_empresa_no_permitida",
        "obra_ambigua",
        "contrato_no_encontrado",
        "contrato_ambiguo",
        "usuario_no_valido",
        "proveedor_sin_albaran_previo",
        "estado_inicial_no_encontrado",
        "almacen_de_obra_no_resuelto",
        "colision_de_clave",
        "filas_afectadas_inesperadas",
        "lineas_no_validas",
    }
    assert CODIGOS_LINEA == {
        "linea_no_es_del_contrato",
        "producto_no_permitido",
        "producto_no_encontrado",
        "partida_no_encontrada",
        "partida_ambigua",
        "partida_no_imputable",
        "precio_negativo",
        "paride_no_valido",
        "naturaleza_no_valida",
        "analitica_no_resuelta",
    }
    assert CODIGOS_AVISO == {
        "producto_sin_historico",
        "supera_pendiente",
        "partida_distinta_del_contrato",
        "sin_partida_en_linea_con_partida",
        "precio_distinto_del_contrato",
        "iva_de_otro_proveedor",
        "servido_negativo",
        "stock_negativo",
        "cod_provisional",
    }
    assert not CODIGOS_CABECERA & CODIGOS_LINEA
    assert not (CODIGOS_CABECERA | CODIGOS_LINEA) & CODIGOS_AVISO


def test_f009_r9_error_de_cabecera() -> None:
    error = AlbaranCompraError("No hay obra.", codigo="obra_no_encontrada")
    assert isinstance(error, ValueError)
    assert str(error) == "No hay obra."
    assert error.codigo == "obra_no_encontrada"
    assert error.lineas == []


@pytest.mark.parametrize("codigo", ["inventado", "precio_negativo", "cod_provisional", ""])
def test_f009_r9_codigo_fuera_de_la_lista_no_se_construye(codigo: str) -> None:
    """Un código de línea va dentro de `lineas_no_validas`, nunca suelto."""
    with pytest.raises(ValueError, match="no es un codigo"):
        AlbaranCompraError("x", codigo=codigo)


def test_f009_r9_lineas_no_validas_con_todas_las_lineas() -> None:
    fallos = [
        FalloLinea(indice=0, referencia_linea="L1", codigo="linea_no_es_del_contrato", mensaje="a"),
        FalloLinea(indice=3, referencia_linea="L4", codigo="precio_negativo", mensaje="b"),
    ]
    error = AlbaranCompraError("Hay líneas que no valen.", codigo="lineas_no_validas", lineas=fallos)
    assert error.lineas == fallos
    assert [f.model_dump() for f in error.lineas] == [
        {"indice": 0, "referencia_linea": "L1", "codigo": "linea_no_es_del_contrato", "mensaje": "a"},
        {"indice": 3, "referencia_linea": "L4", "codigo": "precio_negativo", "mensaje": "b"},
    ]


def test_f009_r9_lineas_no_validas_exige_lineas() -> None:
    with pytest.raises(ValueError, match="lineas"):
        AlbaranCompraError("x", codigo="lineas_no_validas")
    with pytest.raises(ValueError, match="lineas"):
        AlbaranCompraError("x", codigo="lineas_no_validas", lineas=[])


def test_f009_r9_solo_lineas_no_validas_lleva_lineas() -> None:
    fallo = FalloLinea(indice=0, referencia_linea="L1", codigo="precio_negativo", mensaje="m")
    with pytest.raises(ValueError, match="lineas"):
        AlbaranCompraError("x", codigo="obra_no_encontrada", lineas=[fallo])


@pytest.mark.parametrize("codigo", ["obra_no_encontrada", "cod_provisional", "otro"])
def test_f009_r9_fallo_de_linea_solo_con_codigo_de_linea(codigo: str) -> None:
    with pytest.raises(ValidationError):
        FalloLinea(indice=0, referencia_linea="L1", codigo=codigo, mensaje="m")


def test_f009_r9_fallo_de_linea_indice_desde_0() -> None:
    with pytest.raises(ValidationError):
        FalloLinea(indice=-1, referencia_linea="L1", codigo="precio_negativo", mensaje="m")


# --- R7: respuesta superconjunto, avisos y columnas bancarias ----------------------


def _linea_resultado(**extra: Any) -> LineaResultado:
    return LineaResultado(
        **{
            "indice": 0,
            "referencia_linea": "L1",
            "tipo": "vinculada",
            "ctrpro_ide": 9001,
            "linoriide": 9001,
            "proide": 55,
            "producto": "HO0001",
            "cantidad": 2.0,
            "precio": 10.5,
            "total": 21.0,
            "iva_cuota": 4.41,
            "almide": 7,
            "cenide": 8,
            **extra,
        }
    )


def _respuesta(**extra: Any) -> AlbaranCompraResponse:
    return AlbaranCompraResponse(
        **{
            "database": "ruesma",
            "committed": False,
            "dry_run": True,
            "con_ide": 100,
            "cod": "AC26/15953",
            "contrato": {"ctride": 1},
            "cabecera": {"ide": 100},
            "estado": "previsto",
            "referencia_externa": "ALB-1",
            **extra,
        }
    )


def test_f009_r7_la_respuesta_es_superconjunto_de_la_clasica() -> None:
    assert issubclass(AlbaranCompraResponse, AddPurchaseAlbaranResponse)
    assert issubclass(LineaResultado, AlbaranLinePreview)
    clasicos = set(AddPurchaseAlbaranResponse.model_fields)
    assert clasicos <= set(AlbaranCompraResponse.model_fields)
    assert set(AlbaranCompraResponse.model_fields) - clasicos == {
        "estado",
        "referencia_externa",
        "avisos",
        "filas",
    }
    assert set(AlbaranLinePreview.model_fields) <= set(LineaResultado.model_fields)
    assert set(LineaResultado.model_fields) - set(AlbaranLinePreview.model_fields) == {
        "indice",
        "referencia_linea",
        "tipo",
        "producto",
        "paride",
        "partida",
        "cenide",
        "pos",
        "avisos",
    }


def test_f009_r7_linea_sin_vincular_y_sin_partida() -> None:
    linea = _linea_resultado(tipo="sin_vincular", ctrpro_ide=0, linoriide=0)
    assert (linea.paride, linea.partida, linea.avisos, linea.pos) == (0, None, [], None)


@pytest.mark.parametrize("campo, valor", [("indice", -1), ("tipo", "otra"), ("paride", -1)])
def test_f009_r7_linea_resultado_invalida(campo: str, valor: object) -> None:
    with pytest.raises(ValidationError):
        _linea_resultado(**{campo: valor})


@pytest.mark.parametrize("estado", ["previsto", "creado", "idempotente"])
def test_f009_r7_estados(estado: str) -> None:
    assert _respuesta(estado=estado).estado == estado


def test_f009_r7_estado_desconocido() -> None:
    with pytest.raises(ValidationError):
        _respuesta(estado="registrado")


def test_f009_r7_aviso_con_codigo_cerrado() -> None:
    assert AvisoAlbaran(codigo="stock_negativo", mensaje="m").model_dump() == {
        "codigo": "stock_negativo",
        "mensaje": "m",
    }
    with pytest.raises(ValidationError):
        AvisoAlbaran(codigo="precio_negativo", mensaje="m")


def test_f009_r7_warnings_son_los_mensajes_de_todos_los_avisos_en_orden() -> None:
    """H27: cabecera primero y después cada línea en su orden; nada más."""
    respuesta = _respuesta(
        avisos=[AvisoAlbaran(codigo="cod_provisional", mensaje="provisional")],
        lineas=[
            _linea_resultado(
                avisos=[
                    AvisoAlbaran(codigo="supera_pendiente", mensaje="a"),
                    AvisoAlbaran(codigo="stock_negativo", mensaje="b"),
                ]
            ),
            _linea_resultado(indice=1, referencia_linea="L2"),
            _linea_resultado(
                indice=2,
                referencia_linea="L3",
                avisos=[AvisoAlbaran(codigo="iva_de_otro_proveedor", mensaje="c")],
            ),
        ],
        warnings=["texto suelto que no es de ningún aviso"],
    )
    assert respuesta.warnings == ["provisional", "a", "b", "c"]


def test_f009_r7_sin_avisos_no_hay_warnings() -> None:
    assert _respuesta(warnings=["suelto"]).warnings == []


def test_f009_r7_columnas_bancarias_de_design() -> None:
    assert COLUMNAS_BANCARIAS == (
        "banide",
        "banban",
        "bansuc",
        "bandig",
        "bancue",
        "ban",
        "bantipide",
        "cpapai",
        "cpaban",
        "cpasuc",
        "cpaswi",
        "cpatip",
        "cpadiv",
        "cpacue1",
        "cpacue2",
    )


def test_f009_r7_sin_columnas_bancarias_no_toca_la_fila_original() -> None:
    fila = {columna: "dato" for columna in COLUMNAS_BANCARIAS} | {"ide": 1, "entref": "x"}
    assert sin_columnas_bancarias(fila) == {"ide": 1, "entref": "x"}
    assert len(fila) == len(COLUMNAS_BANCARIAS) + 2


def test_f009_r7_cabecera_y_filas_dca_salen_sin_columnas_bancarias() -> None:
    dca = {columna: "ES00" for columna in COLUMNAS_BANCARIAS} | {"ide": 100, "synckey": "ALB-1"}
    respuesta = _respuesta(
        cabecera=dict(dca),
        filas={"con": {"ide": 100, "ban": "no es de dca"}, "dca": dict(dca), "dcapro": []},
    )
    assert respuesta.cabecera == {"ide": 100, "synckey": "ALB-1"}
    assert respuesta.filas["dca"] == {"ide": 100, "synckey": "ALB-1"}
    # Solo se limpia `dca`: las demás tablas no tienen esas columnas.
    assert respuesta.filas["con"] == {"ide": 100, "ban": "no es de dca"}
    volcado = json.dumps(respuesta.model_dump())
    assert "ES00" not in volcado


def test_f009_r7_respuesta_idempotente_minima() -> None:
    respuesta = _respuesta(
        estado="idempotente",
        committed=False,
        dry_run=False,
        cabecera={},
        contrato={},
        lineas=[
            LineaResultado(
                indice=0,
                pos=64,
                referencia_linea="L1",
                ctrpro_ide=0,
                linoriide=0,
                proide=55,
                cantidad=2.0,
                precio=10.5,
                total=21.0,
                iva_cuota=0.0,
                paride=0,
                almide=7,
            )
        ],
    )
    assert respuesta.filas == {}
    assert respuesta.avisos == []
    assert respuesta.lineas[0].tipo is None
    assert respuesta.lineas[0].pos == 64
