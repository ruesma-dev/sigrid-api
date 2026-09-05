# infrastructure/security/document_write_guard.py
"""
Guardia del documento que se adjunta a un concepto (F-004, R7 y R8).

Modulo PURO: recibe los valores de configuracion como argumentos y no importa
`Settings`. Asi el caso de uso decide la politica y el guardia solo la aplica,
y los tests pueden fijar cada limite sin tocar el entorno.

No sustituye a ningun guardia existente ni lo modifica: `sql_write_guard`,
`sql_query_guard`, `identifier_guard` y `database_reference_guard` siguen tal
cual. Este mira el CONTENIDO (base64, tamano, firma, hash) y las listas blancas
de tipo de concepto y clase de grafico.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
import math
from dataclasses import dataclass

from domain.models.concepto_grafico_models import ConceptoGraficoError

#: Tipo MIME por firma binaria conocida. La lista blanca es configurable, asi
#: que una firma admitida que no este aqui se sirve como octet-stream en vez de
#: mentir sobre el tipo.
_TIPOS_POR_FIRMA: dict[bytes, str] = {
    b"%PDF-": "application/pdf",
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG": "image/png",
    b"II*\x00": "image/tiff",
    b"MM\x00*": "image/tiff",
}


@dataclass(frozen=True)
class DocumentoValidado:
    """Lo que sale del guardia: el binario y lo que se sabe de el."""

    contenido: bytes
    bytes: int
    sha256: str
    content_type: str


class DocumentWriteGuard:
    @staticmethod
    def validar_documento(
        *,
        contenido_base64: str,
        sha256_esperado: str | None,
        max_bytes: int,
        firmas_permitidas: list[str],
    ) -> DocumentoValidado:
        """
        Decodifica y valida el fichero. Orden deliberado (R8): tamano del
        base64 -> decodificacion estricta -> vacio -> tamano real -> firma ->
        sha256. Lo caro (decodificar) va detras de lo barato, y la firma va
        antes que el hash porque un fichero del tipo equivocado no mejora
        porque su hash cuadre.
        """
        # 1) Tope ANTES de decodificar: 3 bytes crudos ocupan 4 de base64, mas
        # el relleno. Un fichero desmedido no se llega a materializar.
        tope_base64 = math.ceil(max_bytes * 4 / 3) + 4
        if len(contenido_base64) > tope_base64:
            raise ConceptoGraficoError(
                f"El fichero supera el maximo permitido ({max_bytes} bytes).",
                codigo="tamano_excedido",
            )

        # 2) Estricto: sin `validate=True`, base64 descarta en silencio los
        # caracteres que no son del alfabeto y decodifica OTRA cosa.
        try:
            contenido = base64.b64decode(contenido_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise ValueError(f"contenido_base64 no es base64 valido: {exc}") from exc

        if not contenido:
            raise ConceptoGraficoError("El fichero esta vacio.", codigo="fichero_vacio")

        if len(contenido) > max_bytes:
            raise ConceptoGraficoError(
                f"El fichero ocupa {len(contenido)} bytes y supera el maximo "
                f"permitido ({max_bytes}).",
                codigo="tamano_excedido",
            )

        firma = DocumentWriteGuard._firma_que_casa(contenido, firmas_permitidas)
        if firma is None:
            raise ConceptoGraficoError(
                "El fichero no empieza por ninguna de las firmas permitidas "
                f"({', '.join(firmas_permitidas) or '(ninguna)'}).",
                codigo="tipo_de_fichero_no_permitido",
            )

        sha256 = hashlib.sha256(contenido).hexdigest()
        if sha256_esperado is not None and sha256_esperado.strip().lower() != sha256:
            raise ConceptoGraficoError(
                "El sha256 enviado no coincide con el del fichero recibido.",
                codigo="sha256_no_coincide",
            )

        return DocumentoValidado(
            contenido=contenido,
            bytes=len(contenido),
            sha256=sha256,
            content_type=_TIPOS_POR_FIRMA.get(firma, "application/octet-stream"),
        )

    @staticmethod
    def _firma_que_casa(contenido: bytes, firmas_permitidas: list[str]) -> bytes | None:
        for firma in firmas_permitidas:
            crudo = firma.encode("latin-1")
            if crudo and contenido.startswith(crudo):
                return crudo
        return None

    @staticmethod
    def validar_tipo_de_concepto(
        *, contip: int, tip_del_concepto: int, permitidos: list[int]
    ) -> None:
        """
        El `contip` de la peticion tiene que ser el `con.tip` real del concepto
        Y estar en la lista blanca. Lo primero evita adjuntar a un documento
        que no es el que el cliente cree; lo segundo acota a que tipos de
        concepto puede adjuntar la API. Lista vacia = ninguno (R7).
        """
        if tip_del_concepto != contip:
            raise ConceptoGraficoError(
                f"El concepto es de tipo {tip_del_concepto} y la peticion dice {contip}.",
                codigo="tipo_de_concepto_no_coincide",
            )
        if contip not in permitidos:
            raise ConceptoGraficoError(
                f"El tipo de concepto {contip} no esta permitido para adjuntar "
                "documentos (SIGRID_DOCUMENT_ALLOWED_CONTIP).",
                codigo="tipo_de_concepto_no_coincide",
            )

    @staticmethod
    def validar_clase_de_grafico(
        *, gratipide: int, permitidas: list[int], existe: bool, fecbaj: int | None
    ) -> None:
        """Clase de grafico (`auxgra`): en la lista blanca, existente y viva."""
        if gratipide not in permitidas:
            raise ConceptoGraficoError(
                f"La clase de grafico {gratipide} no esta permitida "
                "(SIGRID_DOCUMENT_ALLOWED_GRATIPIDE).",
                codigo="clase_de_grafico_no_permitida",
            )
        if not existe:
            raise ConceptoGraficoError(
                f"La clase de grafico {gratipide} no existe en dbo.auxgra.",
                codigo="clase_de_grafico_no_permitida",
            )
        if fecbaj:
            raise ConceptoGraficoError(
                f"La clase de grafico {gratipide} esta dada de baja (fecbaj={fecbaj}).",
                codigo="clase_de_grafico_no_permitida",
            )
