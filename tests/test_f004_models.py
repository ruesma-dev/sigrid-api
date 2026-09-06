# tests/test_f004_models.py
"""
F-004 · R1 y R2: el contrato de `POST /api/sigrid/concepto-grafico`.

Sin red y sin base de datos: los modelos de F-004 no llaman a `get_settings()`
a proposito (el tope de tamano del base64 lo aplica el guard, que recibe la
configuracion como argumento), asi que se pueden validar en aislamiento.
"""
from __future__ import annotations

import base64

import pytest
from pydantic import ValidationError

from domain.models.concepto_grafico_models import (
    CODIGOS_DE_ERROR,
    AttachConceptoGraficoRequest,
    AttachConceptoGraficoResponse,
    ConceptoGraficoError,
    ConceptoPreview,
    EnlacePreview,
    GraficoPreview,
)

_PDF = base64.b64encode(b"%PDF-1.4 hola").decode("ascii")

_MINIMO = {
    "database": "ruesma",
    "conide": 2811179,
    "contip": 708,
    "gratipide": 35,
    "res": "PRUEBA API - BORRAR",
    "nom": "parte.pdf",
    "usu": "aechevarria",
    "contenido_base64": _PDF,
}


def peticion(**cambios: object) -> AttachConceptoGraficoRequest:
    return AttachConceptoGraficoRequest.model_validate({**_MINIMO, **cambios})


# --- R1: campos obligatorios, longitudes y defectos --------------------------


@pytest.mark.parametrize("campo", sorted(_MINIMO))
def test_f004_r1_todos_los_campos_del_contrato_son_obligatorios(campo: str) -> None:
    cuerpo = {clave: valor for clave, valor in _MINIMO.items() if clave != campo}
    with pytest.raises(ValidationError):
        AttachConceptoGraficoRequest.model_validate(cuerpo)


def test_f004_r1_el_caso_minimo_valida_y_commit_es_false_por_defecto() -> None:
    request = peticion()
    assert request.commit is False
    assert request.sha256 is None
    assert request.database == "ruesma"


@pytest.mark.parametrize(
    "campo, largo",
    [("res", 49), ("nom", 256), ("usu", 25)],
)
def test_f004_r1_las_longitudes_medidas_del_erp_se_respetan(campo: str, largo: int) -> None:
    """48 / 255 / 24: los anchos reales de gra.res, gra.nom y usu.cod."""
    assert peticion(**{campo: "x" * (largo - 1)})  # el limite exacto entra
    with pytest.raises(ValidationError):
        peticion(**{campo: "x" * largo})


@pytest.mark.parametrize("valor", ["", "   "])
def test_f004_r1_los_textos_no_pueden_venir_vacios(valor: str) -> None:
    with pytest.raises(ValidationError):
        peticion(res=valor)


def test_f004_r1_los_textos_se_recortan() -> None:
    request = peticion(database="  ruesma  ", usu="  aechevarria ", nom=" parte.pdf ")
    assert request.database == "ruesma"
    assert request.usu == "aechevarria"
    assert request.nom == "parte.pdf"


@pytest.mark.parametrize("campo", ["conide", "contip"])
def test_f004_r1_los_identificadores_son_enteros_positivos(campo: str) -> None:
    """`gratipide` salio de esta lista en F-005: su 0 es legitimo («sin clase»)
    y lo prueba `test_f005_el_modelo_acepta_gratipide_0`."""
    with pytest.raises(ValidationError):
        peticion(**{campo: 0})


def test_f004_r1_el_sha256_opcional_exige_64_hexadecimales() -> None:
    valido = "a" * 64
    assert peticion(sha256=valido).sha256 == valido
    for invalido in ("a" * 63, "a" * 65, "z" * 64, ""):
        with pytest.raises(ValidationError):
            peticion(sha256=invalido)


@pytest.mark.parametrize("valor", ["no es base64!", "AAA", "A===", "%%%%", "   "])
def test_f004_r1_un_base64_mal_formado_se_rechaza_en_el_modelo(valor: str) -> None:
    with pytest.raises(ValidationError):
        peticion(contenido_base64=valor)


def test_f004_r1_el_base64_admite_saltos_de_linea_y_los_normaliza() -> None:
    """Los clientes que parten el base64 en lineas de 76 no deben fallar."""
    partido = "\n".join([_PDF[:8], _PDF[8:]])
    assert peticion(contenido_base64=partido).contenido_base64 == _PDF


def test_f004_r1_el_cliente_no_puede_elegir_base_documental_tabla_ide_cod_ni_vin() -> None:
    """Campos de la propuesta que NO se aceptan: si llegan, se ignoran, y en
    ningun caso acaban en el modelo ni en el SQL."""
    request = AttachConceptoGraficoRequest.model_validate(
        {
            **_MINIMO,
            "content_type": "application/pdf",
            "clave_idempotencia": "lo-que-sea",
            "database_documental": "master",
            "tabla": "gra",
            "ide": 1,
            "cod": "inventado",
            "vin": 0,
        }
    )
    for prohibido in ("content_type", "clave_idempotencia", "database_documental",
                      "tabla", "ide", "cod", "vin"):
        assert not hasattr(request, prohibido)
    assert set(request.model_dump()) == set(_MINIMO) | {"sha256", "commit"}


# --- R3: el error de negocio lleva su codigo ---------------------------------


def test_f004_r3_el_error_de_negocio_es_un_valueerror_con_codigo() -> None:
    error = ConceptoGraficoError("El concepto no existe.", codigo="concepto_no_encontrado")
    assert isinstance(error, ValueError)
    assert error.codigo == "concepto_no_encontrado"
    assert str(error) == "El concepto no existe."


def test_f004_r3_la_lista_de_codigos_es_exactamente_la_del_requisito() -> None:
    assert CODIGOS_DE_ERROR == frozenset(
        {
            "escritura_documental_deshabilitada",
            "base_de_datos_no_permitida",
            "concepto_no_encontrado",
            "tipo_de_concepto_no_coincide",
            "clase_de_grafico_no_permitida",
            "usuario_no_valido",
            "fichero_vacio",
            "tipo_de_fichero_no_permitido",
            "tamano_excedido",
            "sha256_no_coincide",
            "colision_de_clave",
            "filas_afectadas_inesperadas",
        }
    )


def test_f004_r3_un_codigo_fuera_de_la_lista_no_se_puede_construir() -> None:
    """El cliente decide por el `codigo`: inventarse uno seria romperle el
    contrato sin que ningun test lo notara."""
    with pytest.raises(ValueError):
        ConceptoGraficoError("vaya", codigo="me_lo_invento")


# --- R2: la respuesta tiene la misma forma en dry-run y en commit ------------


def respuesta(**cambios: object) -> AttachConceptoGraficoResponse:
    base = {
        "committed": False,
        "dry_run": True,
        "idempotente": False,
        "database": "ruesma",
        "database_documental": "ruesma_rep",
        "concepto": ConceptoPreview(ide=2811179, tip=708, emp=1, cod="RS26.08/0123", res="x"),
        "grafico": GraficoPreview(
            cod="202609051200000041.aechevarria", emp=1, nom="parte.pdf", fec=20260905,
            usu="aechevarria", res="PRUEBA", gratipide=35, vin=3, bytes=13,
            sha256="a" * 64, content_type="application/pdf",
        ),
        "enlace": EnlacePreview(con=2811179, pos=64),
        "filas_afectadas": 0,
    }
    return AttachConceptoGraficoResponse.model_validate({**base, **cambios})


def test_f004_r2_la_respuesta_tiene_los_once_campos_del_contrato() -> None:
    volcado = respuesta().model_dump()
    assert set(volcado) == {
        "ok", "committed", "dry_run", "idempotente", "database", "database_documental",
        "concepto", "grafico", "enlace", "filas_afectadas", "avisos",
    }
    assert volcado["ok"] is True
    assert volcado["avisos"] == []


def test_f004_r2_el_sha256_y_los_bytes_van_siempre_en_el_grafico() -> None:
    for cambios in ({}, {"committed": True, "dry_run": False, "filas_afectadas": 3}):
        volcado = respuesta(**cambios).model_dump()
        assert volcado["grafico"]["sha256"] == "a" * 64
        assert volcado["grafico"]["bytes"] == 13


def test_f004_r2_el_binario_no_viaja_en_la_respuesta() -> None:
    """Se devuelve el sha256 y el tamano, nunca el contenido."""
    volcado = respuesta().model_dump()
    texto = repr(volcado)
    assert "contenido" not in texto
    assert "ima" not in volcado["grafico"]


def test_f004_r2_el_enlace_admite_ide_desconocido_en_el_caso_idempotente() -> None:
    """Idempotente: se conoce el rcg existente pero no su `pos`."""
    enlace = EnlacePreview(ide=296661, con=2811179, gra=296221)
    assert enlace.pos is None
    assert (enlace.cla, enlace.feclee, enlace.fecalt) == (0, 0, 0)


# --- R1: el borde de ABAJO de cada campo -------------------------------------


@pytest.mark.parametrize(
    "campo, minimo",
    [
        ("database", "r"),
        ("conide", 1),
        ("contip", 1),
        # 0 desde F-005: «sin clase». Antes era 1.
        ("gratipide", 0),
        ("res", "x"),
        ("nom", "x"),
        ("usu", "u"),
        # 4 caracteres = un bloque de base64, el minimo que decodifica a algo.
        ("contenido_base64", "JVBE"),
    ],
)
def test_f004_r1_el_valor_minimo_exacto_de_cada_campo_entra(
    campo: str, minimo: object
) -> None:
    """
    Los `max_length` ya tenian su borde probado; los `min_length` y los `ge`,
    no. Subir cualquiera de ellos en uno rechazaria un valor legitimo del ERP
    (un `ide` 1, un `res` de una letra) y nadie se enteraria.
    """
    assert getattr(peticion(**{campo: minimo}), campo) == minimo


def test_f004_r1_un_base64_con_longitud_no_multiplo_de_cuatro_se_rechaza() -> None:
    """
    `AAAAA` pasa el alfabeto y llega al minimo de 4, pero 5 no es multiplo de
    4: sin esa comprobacion el modelo daria por bueno un base64 truncado y el
    fichero llegaria roto al guardia.
    """
    with pytest.raises(ValidationError):
        peticion(contenido_base64="AAAAA")


# --- F-005: gratipide admite el 0 («sin clase») ------------------------------


def test_f005_el_modelo_acepta_gratipide_0() -> None:
    """El 0 es la ausencia de clase con la que Sigrid adjunta en contratos y
    albaranes de compra. Quien decide si vale es la lista blanca, no el modelo."""
    assert peticion(gratipide=0).gratipide == 0


@pytest.mark.parametrize("valor", [-1, -35])
def test_f005_el_modelo_sigue_rechazando_un_gratipide_negativo(valor: int) -> None:
    """Bajar el suelo a 0 no lo quita: un negativo nunca llega al guardia."""
    with pytest.raises(ValidationError):
        peticion(gratipide=valor)


def test_f005_conide_y_contip_siguen_exigiendo_al_menos_1() -> None:
    """Control negativo: el suelo baja SOLO para `gratipide`."""
    for campo in ("conide", "contip"):
        with pytest.raises(ValidationError):
            peticion(**{campo: 0})
