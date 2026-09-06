# tests/test_f004_document_write_guard.py
"""
F-004 · R8 (y la parte de listas blancas de R7): el guardia del documento.

Modulo puro: recibe la configuracion como argumentos, nunca `Settings`. Sin red
y sin base de datos.
"""
from __future__ import annotations

import base64
import hashlib
from dataclasses import FrozenInstanceError

import pytest

from domain.models.concepto_grafico_models import ConceptoGraficoError
from infrastructure.security.document_write_guard import DocumentWriteGuard

_PDF = b"%PDF-1.4 contenido de mentira"
_PNG = b"\x89PNG\r\n\x1a\n contenido de mentira"
_SHA_PDF = hashlib.sha256(_PDF).hexdigest()


def b64(contenido: bytes) -> str:
    return base64.b64encode(contenido).decode("ascii")


def validar(
    contenido: bytes | str = _PDF,
    *,
    sha256_esperado: str | None = None,
    max_bytes: int = 10485760,
    firmas_permitidas: list[str] | None = None,
):
    return DocumentWriteGuard.validar_documento(
        contenido_base64=contenido if isinstance(contenido, str) else b64(contenido),
        sha256_esperado=sha256_esperado,
        max_bytes=max_bytes,
        firmas_permitidas=["%PDF-"] if firmas_permitidas is None else firmas_permitidas,
    )


def codigo_de(excinfo: pytest.ExceptionInfo[ConceptoGraficoError]) -> str:
    return excinfo.value.codigo


# --- R8: el camino feliz -----------------------------------------------------


def test_f004_r8_un_pdf_valido_devuelve_bytes_sha256_y_tipo() -> None:
    documento = validar()
    assert documento.contenido == _PDF
    assert documento.bytes == len(_PDF)
    assert documento.sha256 == _SHA_PDF
    assert documento.content_type == "application/pdf"


def test_f004_r8_el_sha256_se_calcula_siempre_aunque_el_cliente_no_lo_mande() -> None:
    """HASHBYTES no sirve (SQL Server 2012): el hash es de Python o no es."""
    assert validar(sha256_esperado=None).sha256 == _SHA_PDF


# --- R8: base64 -------------------------------------------------------------


@pytest.mark.parametrize("crudo", ["@@@@", "AB*=", "....", "a b c!"])
def test_f004_r8_el_base64_se_decodifica_en_modo_estricto(crudo: str) -> None:
    """Sin `validate=True`, Python tira los caracteres raros y decodifica otra
    cosa distinta de la que mando el cliente."""
    with pytest.raises(ValueError) as excinfo:
        validar(crudo)
    assert not isinstance(excinfo.value, ConceptoGraficoError)


# --- R8: tamano --------------------------------------------------------------


def test_f004_r8_un_fichero_vacio_se_rechaza() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(b"")
    assert codigo_de(excinfo) == "fichero_vacio"


def test_f004_r8_el_tope_se_mira_sobre_el_base64_antes_de_decodificar() -> None:
    """Con 10 bytes de tope, 100 caracteres de base64 no se llegan a decodificar."""
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar("A" * 100, max_bytes=10)
    assert codigo_de(excinfo) == "tamano_excedido"


def test_f004_r8_el_tope_se_mira_tambien_sobre_los_bytes_decodificados() -> None:
    """El tope del base64 tiene holgura (hasta 3 bytes): la comprobacion buena
    es la de despues de decodificar."""
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(b"%PDF-1", max_bytes=5)
    assert codigo_de(excinfo) == "tamano_excedido"


def test_f004_r8_el_tamano_exacto_del_tope_entra() -> None:
    assert validar(b"%PDF-1", max_bytes=6).bytes == 6


# --- R8: firma binaria -------------------------------------------------------


def test_f004_r8_un_fichero_con_firma_ajena_se_rechaza() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(_PNG)
    assert codigo_de(excinfo) == "tipo_de_fichero_no_permitido"


def test_f004_r8_la_firma_se_compara_al_principio_del_fichero_no_en_medio() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(b"hola %PDF-1.4")
    assert codigo_de(excinfo) == "tipo_de_fichero_no_permitido"


def test_f004_r8_una_lista_de_firmas_vacia_no_admite_nada() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(_PDF, firmas_permitidas=[])
    assert codigo_de(excinfo) == "tipo_de_fichero_no_permitido"


def test_f004_r8_ampliar_la_lista_de_firmas_admite_el_nuevo_tipo() -> None:
    documento = validar(_PNG, firmas_permitidas=["%PDF-", "\x89PNG"])
    assert documento.content_type == "image/png"


def test_f004_r8_una_firma_admitida_sin_tipo_conocido_cae_en_octet_stream() -> None:
    documento = validar(b"XYZ datos", firmas_permitidas=["XYZ"])
    assert documento.content_type == "application/octet-stream"


# --- R8: sha256 --------------------------------------------------------------


def test_f004_r8_el_sha256_enviado_que_casa_pasa_en_mayusculas_o_minusculas() -> None:
    assert validar(sha256_esperado=_SHA_PDF.upper()).sha256 == _SHA_PDF


def test_f004_r8_el_sha256_enviado_que_no_casa_se_rechaza() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(sha256_esperado="b" * 64)
    assert codigo_de(excinfo) == "sha256_no_coincide"


def test_f004_r8_el_sha256_se_comprueba_despues_de_la_firma() -> None:
    """Un PNG con su sha256 correcto sigue siendo un PNG."""
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(_PNG, sha256_esperado=hashlib.sha256(_PNG).hexdigest())
    assert codigo_de(excinfo) == "tipo_de_fichero_no_permitido"


# --- R7: listas blancas de concepto y de clase de grafico --------------------


def test_f004_r7_el_tipo_de_concepto_tiene_que_coincidir_con_el_del_erp() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_tipo_de_concepto(
            contip=708, tip_del_concepto=14, permitidos=[708]
        )
    assert codigo_de(excinfo) == "tipo_de_concepto_no_coincide"


def test_f004_r7_un_tipo_de_concepto_fuera_de_la_lista_blanca_se_rechaza() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_tipo_de_concepto(
            contip=14, tip_del_concepto=14, permitidos=[708]
        )
    assert codigo_de(excinfo) == "tipo_de_concepto_no_coincide"


def test_f004_r7_una_lista_de_conceptos_vacia_no_admite_ninguno() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_tipo_de_concepto(
            contip=708, tip_del_concepto=708, permitidos=[]
        )
    assert codigo_de(excinfo) == "tipo_de_concepto_no_coincide"


def test_f004_r7_el_tipo_de_concepto_correcto_y_permitido_pasa() -> None:
    DocumentWriteGuard.validar_tipo_de_concepto(
        contip=708, tip_del_concepto=708, permitidos=[707, 708]
    )


@pytest.mark.parametrize(
    "gratipide, permitidas, existe, fecbaj",
    [
        (34, [35], True, 0),        # fuera de la lista blanca
        (35, [], True, 0),          # lista vacia: ninguna clase vale
        (35, [35], False, None),    # no existe en auxgra
        (35, [35], True, 20250101),  # dada de baja
    ],
)
def test_f004_r7_la_clase_de_grafico_se_rechaza(
    gratipide: int, permitidas: list[int], existe: bool, fecbaj: int | None
) -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_clase_de_grafico(
            gratipide=gratipide, permitidas=permitidas, existe=existe, fecbaj=fecbaj
        )
    assert codigo_de(excinfo) == "clase_de_grafico_no_permitida"


def test_f004_r7_la_clase_permitida_viva_y_existente_pasa() -> None:
    DocumentWriteGuard.validar_clase_de_grafico(
        gratipide=35, permitidas=[35], existe=True, fecbaj=0
    )


# --- R8: los bordes exactos que la campana de mutacion dejo al aire ----------


def test_f004_r8_la_longitud_exacta_del_tope_del_base64_no_se_rechaza() -> None:
    """
    El tope del base64 es `ceil(max_bytes * 4 / 3) + 4`: con `max_bytes=10`,
    `ceil(40/3) = 14` y el tope son 18 caracteres. La comparacion es ESTRICTA,
    asi que 18 no se rechaza por tamano: se decodifica, y es ahi donde falla
    por no ser base64. Un `>=` en su lugar, o un tope mas corto, lo convertiria
    en `tamano_excedido` y este test lo caza.
    """
    with pytest.raises(ValueError) as excinfo:
        validar("A" * 18, max_bytes=10)
    assert not isinstance(excinfo.value, ConceptoGraficoError)
    assert "no es base64 valido" in str(excinfo.value)


def test_f004_r8_un_caracter_por_encima_del_tope_muere_antes_de_decodificar() -> None:
    """
    19 caracteres = tope + 1. La prueba de que no se llega a decodificar es el
    codigo: la decodificacion de `A`*19 lanzaria un `ValueError` pelado, no un
    `ConceptoGraficoError` con `tamano_excedido`. Un tope mas largo (`*5/3`, o
    `+5`) dejaria pasar estos 19 caracteres y este test lo caza.
    """
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar("A" * 19, max_bytes=10)
    assert codigo_de(excinfo) == "tamano_excedido"


def test_f004_r8_el_documento_validado_es_inmutable() -> None:
    """Lo que sale del guardia no se retoca aguas abajo: el caso de uso escribe
    en el ERP los bytes, el tamano y el hash que el guardia midio."""
    documento = validar()
    with pytest.raises(FrozenInstanceError):
        documento.bytes = 0  # type: ignore[misc]


def test_f004_r8_el_error_de_firma_nombra_las_firmas_que_si_valen() -> None:
    """Quien recibe el 400 tiene que poder saber que tipos se admiten."""
    with pytest.raises(ConceptoGraficoError) as excinfo:
        validar(_PNG, firmas_permitidas=["%PDF-", "II*\x00"])
    assert "%PDF-" in str(excinfo.value)

    with pytest.raises(ConceptoGraficoError) as sin_firmas:
        validar(_PDF, firmas_permitidas=[])
    assert "(ninguna)" in str(sin_firmas.value)


# --- F-005: la clase 0, «sin clase», como Sigrid en contratos y albaranes ----


def test_f005_la_clase_0_permitida_pasa_sin_exigir_fila_en_auxgra() -> None:
    """
    El 0 NO es una fila de `dbo.auxgra`: es la ausencia de clase con la que
    Sigrid adjunta el 99,98 % de los documentos de contratos (`con.tip` 44) y
    el 100 % de los de albaranes de compra (`tip` 14) [MEDIDO 2026-09-06]. Asi
    que ni existe ni puede estar de baja, y exigirselo lo rechazaria siempre.
    """
    DocumentWriteGuard.validar_clase_de_grafico(
        gratipide=0, permitidas=[35, 0], existe=False, fecbaj=None
    )


def test_f005_la_clase_0_permitida_pasa_aunque_lleguen_existe_falso_y_un_fecbaj() -> None:
    """Para el 0 no hay baja que mirar: la lista blanca es el UNICO control."""
    DocumentWriteGuard.validar_clase_de_grafico(
        gratipide=0, permitidas=[0], existe=False, fecbaj=20250101
    )


def test_f005_la_clase_0_fuera_de_la_lista_blanca_se_rechaza() -> None:
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_clase_de_grafico(
            gratipide=0, permitidas=[35], existe=False, fecbaj=None
        )
    assert codigo_de(excinfo) == "clase_de_grafico_no_permitida"


def test_f005_con_la_lista_blanca_vacia_el_0_tampoco_vale() -> None:
    """Lista vacia = ninguna clase, tampoco la ausencia de clase. Es el defecto
    de `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE`, que no cambia con F-005."""
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_clase_de_grafico(
            gratipide=0, permitidas=[], existe=False, fecbaj=None
        )
    assert codigo_de(excinfo) == "clase_de_grafico_no_permitida"


@pytest.mark.parametrize(
    "existe, fecbaj",
    [
        (False, None),      # no existe en auxgra
        (True, 20250101),   # existe pero esta dada de baja
    ],
)
def test_f005_una_clase_mayor_que_cero_sigue_exigiendo_auxgra_con_el_0_permitido(
    existe: bool, fecbaj: int | None
) -> None:
    """
    Control negativo: admitir el 0 no relaja NADA para las demas clases. Ni
    siquiera cuando el 0 esta en la misma lista blanca.
    """
    with pytest.raises(ConceptoGraficoError) as excinfo:
        DocumentWriteGuard.validar_clase_de_grafico(
            gratipide=35, permitidas=[35, 0], existe=existe, fecbaj=fecbaj
        )
    assert codigo_de(excinfo) == "clase_de_grafico_no_permitida"


def test_f005_una_clase_mayor_que_cero_viva_sigue_pasando_con_el_0_permitido() -> None:
    DocumentWriteGuard.validar_clase_de_grafico(
        gratipide=35, permitidas=[35, 0], existe=True, fecbaj=0
    )
