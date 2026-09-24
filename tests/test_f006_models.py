# tests/test_f006_models.py
"""
F-006 · R1 y R2: el contrato de `POST /api/sigrid/partes-reclamacion`.

Sin red y sin base de datos: solo Pydantic. Lo que se fija aquí es lo que el
cliente puede mandar (y lo que NO: `ide`, `cod`, `emp`, `est`, `pos`), sus
longitudes, los defectos de Q2 y del tipo `0002`, y el conjunto cerrado de
códigos de error.
"""
from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError

from domain.models.parte_reclamacion_models import (
    CODIGOS_DE_ERROR,
    CODIGOS_DE_LOTE,
    CODIGOS_DE_PARTE,
    CreatePartesReclamacionRequest,
    CreatePartesReclamacionResponse,
    IntervinienteIn,
    ParteIn,
    ParteReclamacionError,
    ResultadoParte,
)


def parte(**cambios: Any) -> dict[str, Any]:
    base = {
        "referencia_externa": "PVI-PRUEBA-0001",
        "unidad_postventa": "0626.03PORTAL 1.1.A",
        "descripcion": "PRUEBA API - ANULAR",
        "oficio": "0039",
    }
    return {**base, **cambios}


def peticion(**cambios: Any) -> dict[str, Any]:
    base = {"database": "ruesma", "obra": "0626", "usu": "prueba", "partes": [parte()]}
    return {**base, **cambios}


def validar(cuerpo: dict[str, Any]) -> CreatePartesReclamacionRequest:
    return CreatePartesReclamacionRequest.model_validate(cuerpo)


def rechaza(cuerpo: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        validar(cuerpo)


# --- R1: forma mínima y defectos -------------------------------------------


def test_f006_r1_la_peticion_minima_se_acepta_con_sus_defectos() -> None:
    modelo = validar(peticion())

    assert modelo.database == "ruesma"
    assert modelo.obra == "0626"
    assert modelo.usu == "prueba"
    assert modelo.commit is False
    unico = modelo.partes[0]
    assert unico.tipo == "0002"
    assert unico.forma_comunicacion == 1
    assert unico.intervinientes == []
    assert unico.ubicacion == ""
    assert unico.clase is None
    assert unico.descripcion_larga is None


def test_f006_r1_el_interviniente_tiene_sus_defectos() -> None:
    interviniente = IntervinienteIn.model_validate({"oficio": "0039"})
    assert interviniente.proveedor is None
    assert interviniente.causante is False


def test_f006_r1_la_peticion_completa_se_acepta() -> None:
    modelo = validar(
        peticion(
            commit=True,
            partes=[
                parte(
                    descripcion_larga="Texto largo",
                    tipo="0003",
                    clase="0001",
                    ubicacion="Cocina",
                    forma_comunicacion=0,
                    intervinientes=[
                        {"oficio": "0039", "proveedor": "1181", "causante": True}
                    ],
                )
            ],
        )
    )
    unico = modelo.partes[0]
    assert modelo.commit is True
    assert unico.forma_comunicacion == 0
    assert unico.intervinientes[0].proveedor == "1181"
    assert unico.intervinientes[0].causante is True


@pytest.mark.parametrize("campo", ["database", "obra", "usu", "partes"])
def test_f006_r1_los_campos_del_lote_son_obligatorios(campo: str) -> None:
    cuerpo = peticion()
    del cuerpo[campo]
    rechaza(cuerpo)


@pytest.mark.parametrize(
    "campo", ["referencia_externa", "unidad_postventa", "descripcion", "oficio"]
)
def test_f006_r1_los_campos_del_parte_son_obligatorios(campo: str) -> None:
    datos = parte()
    del datos[campo]
    rechaza(peticion(partes=[datos]))


def test_f006_r1_el_oficio_del_interviniente_es_obligatorio() -> None:
    rechaza(peticion(partes=[parte(intervinientes=[{"proveedor": "1181"}])]))


# --- R1: longitudes ----------------------------------------------------------


@pytest.mark.parametrize("campo, tope", [("obra", 24), ("usu", 24)])
def test_f006_r1_longitudes_del_lote(campo: str, tope: int) -> None:
    validar(peticion(**{campo: "x" * tope}))
    rechaza(peticion(**{campo: "x" * (tope + 1)}))


@pytest.mark.parametrize(
    "campo, tope",
    [
        ("referencia_externa", 80),
        ("unidad_postventa", 24),
        ("descripcion", 128),
        ("oficio", 24),
        ("tipo", 24),
        ("clase", 24),
        ("ubicacion", 48),
    ],
)
def test_f006_r1_longitudes_del_parte(campo: str, tope: int) -> None:
    validar(peticion(partes=[parte(**{campo: "x" * tope})]))
    rechaza(peticion(partes=[parte(**{campo: "x" * (tope + 1)})]))


@pytest.mark.parametrize("campo, tope", [("oficio", 24), ("proveedor", 24)])
def test_f006_r1_longitudes_del_interviniente(campo: str, tope: int) -> None:
    datos = {"oficio": "0039", campo: "x" * tope}
    validar(peticion(partes=[parte(intervinientes=[datos])]))
    datos = {"oficio": "0039", campo: "x" * (tope + 1)}
    rechaza(peticion(partes=[parte(intervinientes=[datos])]))


# --- R1: dominios ------------------------------------------------------------


@pytest.mark.parametrize("valor", [2, 3, -1, "Escrita"])
def test_f006_r1_la_forma_de_comunicacion_solo_admite_0_y_1(valor: object) -> None:
    rechaza(peticion(partes=[parte(forma_comunicacion=valor)]))


def test_f006_r1_como_mucho_diez_intervinientes() -> None:
    diez = [{"oficio": f"{n:04d}"} for n in range(10)]
    validar(peticion(partes=[parte(intervinientes=diez)]))
    rechaza(peticion(partes=[parte(intervinientes=diez + [{"oficio": "0099"}])]))


def test_f006_r1_el_lote_no_puede_venir_vacio() -> None:
    rechaza(peticion(partes=[]))


@pytest.mark.parametrize("campo", ["ide", "cod", "emp", "est", "pos"])
def test_f006_r1_el_cliente_no_manda_identificadores_ni_estado(campo: str) -> None:
    rechaza(peticion(partes=[parte(**{campo: 1})]))
    rechaza(peticion(**{campo: 1}))


def test_f006_r1_el_interviniente_tampoco_admite_campos_extra() -> None:
    rechaza(peticion(partes=[parte(intervinientes=[{"oficio": "0039", "obrofcide": 7}])]))


# --- R1: textos recortados ---------------------------------------------------


@pytest.mark.parametrize(
    "campo", ["referencia_externa", "unidad_postventa", "descripcion", "oficio", "tipo"]
)
def test_f006_r1_un_texto_vacio_tras_recortar_se_rechaza(campo: str) -> None:
    rechaza(peticion(partes=[parte(**{campo: "   "})]))


@pytest.mark.parametrize("campo", ["obra", "usu"])
def test_f006_r1_un_texto_del_lote_vacio_tras_recortar_se_rechaza(campo: str) -> None:
    rechaza(peticion(**{campo: "   "}))


def test_f006_r1_los_textos_se_recortan() -> None:
    modelo = validar(
        peticion(
            database=" ruesma ",
            obra=" 0626 ",
            usu=" prueba ",
            partes=[
                parte(
                    referencia_externa=" PVI-1 ",
                    unidad_postventa=" 0626.03PORTAL 1.1.A ",
                    descripcion=" Fisura ",
                    oficio=" 0039 ",
                    ubicacion=" Cocina ",
                    descripcion_larga=" Largo ",
                    clase=" 0001 ",
                    tipo=" 0003 ",
                    intervinientes=[{"oficio": " 0039 ", "proveedor": " 1181 "}],
                )
            ],
        )
    )
    unico = modelo.partes[0]
    assert (modelo.database, modelo.obra, modelo.usu) == ("ruesma", "0626", "prueba")
    assert unico.referencia_externa == "PVI-1"
    assert unico.unidad_postventa == "0626.03PORTAL 1.1.A"
    assert unico.descripcion == "Fisura"
    assert unico.oficio == "0039"
    assert unico.ubicacion == "Cocina"
    assert unico.descripcion_larga == "Largo"
    assert unico.clase == "0001"
    assert unico.tipo == "0003"
    assert unico.intervinientes[0].oficio == "0039"
    assert unico.intervinientes[0].proveedor == "1181"


def test_f006_r1_la_longitud_se_mide_despues_de_recortar() -> None:
    validar(peticion(partes=[parte(descripcion="  " + "x" * 128 + "  ")]))


def test_f006_r1_un_texto_no_se_inventa_desde_otro_tipo() -> None:
    """Un número no es una referencia: no se convierte a cadena por las buenas."""
    rechaza(peticion(partes=[parte(referencia_externa=12345)]))


# --- R3/R7: los códigos de error son un conjunto cerrado ---------------------


def test_f006_r3_los_codigos_del_lote_son_los_de_la_spec() -> None:
    assert CODIGOS_DE_LOTE == frozenset(
        {
            "escritura_reclamaciones_deshabilitada",
            "base_de_datos_no_permitida",
            "lote_demasiado_grande",
            "obra_no_encontrada",
            "usuario_no_valido",
            "serie_no_encontrada",
            "estado_inicial_no_encontrado",
        }
    )


def test_f006_r7_los_codigos_de_parte_son_los_de_la_spec() -> None:
    assert CODIGOS_DE_PARTE == frozenset(
        {
            "referencia_no_permitida",
            "referencia_duplicada_en_lote",
            "referencia_en_conflicto",
            "unidad_postventa_no_encontrada",
            "tipo_no_valido",
            "clase_no_valida",
            "oficio_no_esta_en_la_obra",
            "interviniente_no_esta_en_la_obra",
            "interviniente_ambiguo",
            "interviniente_repetido",
            "numeracion_agotada",
            "colision_de_clave",
            "filas_afectadas_inesperadas",
            "presupuesto_de_tiempo_agotado",
            "error_de_escritura",
        }
    )
    assert CODIGOS_DE_ERROR == CODIGOS_DE_LOTE | CODIGOS_DE_PARTE


@pytest.mark.parametrize("codigo", sorted(CODIGOS_DE_LOTE | CODIGOS_DE_PARTE))
def test_f006_r3_el_error_admite_cada_codigo_cerrado(codigo: str) -> None:
    error = ParteReclamacionError("mensaje", codigo=codigo)
    assert error.codigo == codigo
    assert str(error) == "mensaje"
    assert isinstance(error, ValueError)


def test_f006_r3_el_error_rechaza_un_codigo_inventado() -> None:
    with pytest.raises(ValueError) as excinfo:
        ParteReclamacionError("mensaje", codigo="me_lo_invento")
    assert not isinstance(excinfo.value, ParteReclamacionError)
    assert "me_lo_invento" in str(excinfo.value)


# --- R2: la respuesta tiene la misma forma en dry-run y en commit -----------


def test_f006_r2_la_respuesta_tiene_la_forma_de_la_spec() -> None:
    respuesta = CreatePartesReclamacionResponse(
        committed=False,
        dry_run=True,
        database="ruesma",
        obra={"ide": 1758465, "cod": "0626", "emp": 1},
        resumen={
            "creados": 0,
            "idempotentes": 0,
            "previstos": 1,
            "rechazados": 1,
            "no_procesados": 0,
        },
        partes=[
            ResultadoParte(
                indice=0,
                referencia_externa="PVI-1",
                estado="previsto",
                ide=2900001,
                cod="RS26.09/0001",
                filas={"con": {"ide": 2900001}},
            ),
            ResultadoParte(
                indice=1,
                referencia_externa="PVI-2",
                estado="rechazado",
                motivo={"codigo": "tipo_no_valido", "mensaje": "No existe."},
            ),
        ],
    )
    cuerpo = respuesta.model_dump()

    assert set(cuerpo) == {
        "ok", "committed", "dry_run", "database", "obra", "resumen", "avisos", "partes",
    }
    assert cuerpo["ok"] is True
    assert cuerpo["avisos"] == []
    assert set(cuerpo["partes"][0]) == {
        "indice", "referencia_externa", "estado", "ide", "cod", "motivo", "filas", "avisos",
    }
    assert cuerpo["partes"][0]["motivo"] is None
    assert cuerpo["partes"][1]["motivo"] == {"codigo": "tipo_no_valido", "mensaje": "No existe."}
    assert cuerpo["partes"][1]["filas"] == {}
    assert cuerpo["partes"][1]["ide"] is None


def test_f006_r2_el_estado_de_un_parte_es_cerrado() -> None:
    for estado in ("previsto", "creado", "idempotente", "rechazado", "no_procesado"):
        ResultadoParte(indice=0, referencia_externa="PVI-1", estado=estado)
    with pytest.raises(ValidationError):
        ResultadoParte(indice=0, referencia_externa="PVI-1", estado="inventado")


def test_f006_r2_el_motivo_solo_lleva_codigos_cerrados() -> None:
    with pytest.raises(ValidationError):
        ResultadoParte(
            indice=0,
            referencia_externa="PVI-1",
            estado="rechazado",
            motivo={"codigo": "me_lo_invento", "mensaje": "x"},
        )


def test_f006_r1_parte_in_es_el_modelo_de_cada_parte() -> None:
    assert ParteIn.model_validate(parte()).oficio == "0039"
