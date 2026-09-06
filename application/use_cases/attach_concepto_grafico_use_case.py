# application/use_cases/attach_concepto_grafico_use_case.py
"""
Adjuntar un documento a un concepto de Sigrid (F-004).

Tres filas en UNA transaccion local contra la base de NEGOCIO, llegando a la
documental por nombre de tres partes (las dos bases estan en la misma
instancia [MEDIDO], asi que no hace falta MSDTC):

  1. el binario en `<documental>.dbo.gra`  (`gratipide=0`, `res=''`, `vin=3`)
  2. los metadatos en `dbo.gra`            (`ima` NULL, `vin=3`, el MISMO `cod` y `emp`)
  3. el enlace en `dbo.rcg`                (`con`=concepto, `gra`=ide de (2))

Ese orden no es casual: si algo se partiera, cada prefijo es invisible para
Sigrid. El orden inverso reproduce la anomalia de los graficos sin fichero.

`commit=False` (por defecto) => DRY-RUN: solo lecturas y solo con credenciales
de lectura.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from application.use_cases.concepto_grafico_statements import (
    POS_PASO,
    VIN_REPOSITORIO,
    ConceptoGraficoStatements,
    hora_local_de_madrid,
)
from domain.models.concepto_grafico_models import (
    AttachConceptoGraficoRequest,
    AttachConceptoGraficoResponse,
    ConceptoGraficoError,
    ConceptoPreview,
    EnlacePreview,
    GraficoPreview,
)
from domain.models.sql_models import SqlReadRequest
from infrastructure.security.document_write_guard import DocumentWriteGuard

logger = logging.getLogger(__name__)

_AVISO_DRY_RUN = (
    "DRY-RUN: no se ha escrito nada. Los tres ide son provisionales (MAX+1 en el "
    "instante de la consulta); en el commit se reservan de nuevo bajo bloqueo."
)


class AttachConceptoGraficoUseCase:
    def __init__(self, repository: Any, settings: Any) -> None:
        self._repo = repository
        self._settings = settings

    # ------------------------------------------------------------------ #
    # Orquestacion
    # ------------------------------------------------------------------ #
    def run(self, request: AttachConceptoGraficoRequest) -> AttachConceptoGraficoResponse:
        arranque = time.monotonic()
        traza: dict[str, Any] = {
            "endpoint": "sigrid/concepto-grafico",
            "database": request.database,
            "conide": request.conide,
            "contip": request.contip,
            "gratipide": request.gratipide,
            "usu": request.usu,
            "commit": request.commit,
        }
        try:
            respuesta = self._ejecutar(request, traza)
        except ConceptoGraficoError as exc:
            traza["resultado"] = "error"
            traza["codigo"] = exc.codigo
            self._trazar(traza, arranque)
            raise
        except Exception as exc:
            traza["resultado"] = "excepcion"
            traza["codigo"] = type(exc).__name__
            self._trazar(traza, arranque)
            raise

        traza["resultado"] = "ok"
        traza["idempotente"] = respuesta.idempotente
        traza["filas_afectadas"] = respuesta.filas_afectadas
        self._trazar(traza, arranque)
        return respuesta

    def _trazar(self, traza: dict[str, Any], arranque: float) -> None:
        """R21: `sha256` y tamano, NUNCA el binario ni el base64."""
        traza["duracion_ms"] = round((time.monotonic() - arranque) * 1000, 1)
        logger.info(json.dumps(traza, ensure_ascii=False, default=str))

    def _ejecutar(
        self, request: AttachConceptoGraficoRequest, traza: dict[str, Any]
    ) -> AttachConceptoGraficoResponse:
        documental = self._base_documental()
        self._validar_bases(request.database, documental)
        if request.commit:
            self._exigir_llaves_de_escritura()

        # El fichero, antes de tocar la red: lo barato y lo que mas se rechaza.
        documento = DocumentWriteGuard.validar_documento(
            contenido_base64=request.contenido_base64,
            sha256_esperado=request.sha256,
            max_bytes=self._settings.sigrid_document_max_bytes,
            firmas_permitidas=self._settings.sigrid_document_allowed_magic,
        )
        traza["bytes"] = documento.bytes
        traza["sha256"] = documento.sha256

        sentencias = ConceptoGraficoStatements(
            database=request.database, documental=documental
        )

        avisos: list[str] = []
        concepto = self._leer_concepto(request, sentencias)
        self._leer_clase(request, sentencias, avisos)
        self._leer_usuario(request, sentencias)
        pos = self._leer_posicion(request, sentencias)

        cod, fila_documental, fila_negocio = sentencias.construir_filas_gra(
            ahora=hora_local_de_madrid(datetime.now(timezone.utc)),
            sha256=documento.sha256,
            emp=concepto.emp,
            usu=request.usu,
            nom=request.nom,
            res=request.res,
            gratipide=request.gratipide,
            contenido=documento.contenido,
        )
        traza["cod"] = cod

        # R17: idempotencia por contenido, con lecturas.
        candidatos = self._leer(
            request,
            sentencias.buscar_idempotencia(request.conide, documento.bytes),
            max_rows=self._settings.max_allowed_rows,
        )
        ya_colgado = self._buscar_idempotencia(documento, candidatos)
        avisos.extend(self._avisar_de_huerfanas(request, sentencias))

        if ya_colgado is not None:
            return self._respuesta_idempotente(
                request, documental, concepto, documento, cod, ya_colgado, avisos
            )

        if not request.commit:
            return self._respuesta_dry_run(
                request, documental, concepto, documento, cod, pos,
                fila_documental, fila_negocio, avisos,
            )

        return self._commit(
            request, documental, concepto, documento, cod, pos,
            fila_documental, fila_negocio, sentencias, avisos,
        )

    # ------------------------------------------------------------------ #
    # Guards de configuracion (R6, R10)
    # ------------------------------------------------------------------ #
    def _base_documental(self) -> str:
        documental = (self._settings.sigrid_document_write_database or "").strip()
        if not documental:
            raise ConceptoGraficoError(
                "La escritura documental esta desactivada: SIGRID_DOCUMENT_WRITE_DATABASE "
                "esta vacia.",
                codigo="escritura_documental_deshabilitada",
            )
        return documental

    def _validar_bases(self, database: str, documental: str) -> None:
        permitidas = self._settings.allowed_write_databases
        if permitidas and database not in permitidas:
            raise ConceptoGraficoError(
                f"La base '{database}' no esta permitida para escritura.",
                codigo="base_de_datos_no_permitida",
            )
        if database.strip().lower() == documental.strip().lower():
            raise ConceptoGraficoError(
                "La base de la peticion es la documental. A la documental se escribe por "
                "nombre de tres partes desde la base de negocio, nunca conectandose a ella.",
                codigo="base_de_datos_no_permitida",
            )

    def _exigir_llaves_de_escritura(self) -> None:
        if not (
            self._settings.sigrid_domain_write_enabled
            and self._settings.sigrid_document_write_enabled
            and self._settings.sql_server_write_username
            and self._settings.sql_server_write_password
        ):
            raise ConceptoGraficoError(
                "Escritura documental desactivada: hacen falta SIGRID_DOMAIN_WRITE_ENABLED, "
                "SIGRID_DOCUMENT_WRITE_ENABLED y credenciales de escritura.",
                codigo="escritura_documental_deshabilitada",
            )

    # ------------------------------------------------------------------ #
    # Lecturas (R7, R17)
    # ------------------------------------------------------------------ #
    def _leer(
        self,
        request: AttachConceptoGraficoRequest,
        sentencia: tuple[str, list[Any]],
        *,
        max_rows: int | None = None,
    ) -> list[tuple[Any, ...]]:
        """
        Lectura con credenciales de LECTURA.

        `model_construct` y no `model_validate` a proposito: los validadores de
        `SqlReadRequest` llaman a `get_settings()`, y aqui el SQL es constante y
        los parametros los pone el propio caso de uso, asi que no hay nada que
        validar y si un `.env` que no pintaría nada en un test unitario.

        Con `max_rows=None` manda `DEFAULT_MAX_ROWS` (200), que sobra para las
        lecturas de una fila. Las que pueden traer muchas (L5 y L6) piden el
        tope maximo. Truncar NUNCA se ignora: una lista de candidatos a medias
        haria fallar la idempotencia en silencio y duplicaria el adjunto.
        """
        sql, params = sentencia
        _columnas, filas, truncado = self._repo.execute_read_query(
            SqlReadRequest.model_construct(
                database=request.database, sql=sql, parameters=params, max_rows=max_rows
            )
        )
        if truncado:
            # Sin codigo de R3: la lista de codigos es cerrada a proposito y
            # ninguno describe "no he podido ver todas las filas"
            # (`filas_afectadas_inesperadas` habla de las filas ESCRITAS en el
            # commit, R14). Sube como ValueError y la ruta lo saca como 400.
            raise ValueError(
                "La lectura devolvio mas filas de las que se pueden traer (truncada) y "
                "el resultado seria incompleto: no se adjunta nada. Revise el concepto "
                f"ide={request.conide}."
            )
        return list(filas)

    def _leer_concepto(
        self, request: AttachConceptoGraficoRequest, sentencias: ConceptoGraficoStatements
    ) -> ConceptoPreview:
        filas = self._leer(request, sentencias.leer_concepto(request.conide))
        if not filas:
            raise ConceptoGraficoError(
                f"No existe ningun concepto con ide={request.conide}.",
                codigo="concepto_no_encontrado",
            )
        ide, tip, emp, cod, res = filas[0][:5]
        DocumentWriteGuard.validar_tipo_de_concepto(
            contip=request.contip,
            tip_del_concepto=int(tip),
            permitidos=self._settings.sigrid_document_allowed_contip,
        )
        return ConceptoPreview(ide=int(ide), tip=int(tip), emp=int(emp), cod=str(cod), res=res)

    def _leer_clase(
        self,
        request: AttachConceptoGraficoRequest,
        sentencias: ConceptoGraficoStatements,
        avisos: list[str],
    ) -> None:
        # F-005: el 0 es "sin clase" y NO tiene fila en `dbo.auxgra`, asi que
        # con el la L2 no se ejecuta: preguntar por el garantiza cero filas y
        # gastaria una ida y vuelta al ERP en cada contrato y cada albaran.
        # `fila` se queda entonces en None, que es exactamente la verdad, y el
        # guardia decide solo con la lista blanca: si el 0 no esta, rechaza
        # igual (`clase_de_grafico_no_permitida`) sin haber leido nada.
        fila: tuple[Any, ...] | None = None
        if request.gratipide != 0:
            filas = self._leer(request, sentencias.leer_clase(request.gratipide))
            fila = filas[0] if filas else None

        DocumentWriteGuard.validar_clase_de_grafico(
            gratipide=request.gratipide,
            permitidas=self._settings.sigrid_document_allowed_gratipide,
            existe=fila is not None,
            fecbaj=int(fila[3] or 0) if fila else None,
        )
        if fila is not None and not (fila[4] or "").strip():
            # `tipaso` dice a que tipos de concepto se asocia la clase. No se
            # valida (la correspondencia no esta medida), pero si esta vacio
            # conviene que el humano lo sepa. Sin clase no hay `tipaso` del que
            # avisar: el aviso saldria SIEMPRE y taparia el que si importa.
            avisos.append(
                f"La clase de grafico {request.gratipide} no declara tipaso en dbo.auxgra."
            )

    def _leer_usuario(
        self, request: AttachConceptoGraficoRequest, sentencias: ConceptoGraficoStatements
    ) -> None:
        if not self._leer(request, sentencias.leer_usuario(request.usu)):
            raise ConceptoGraficoError(
                f"El usuario '{request.usu}' no existe en dbo.usu.",
                codigo="usuario_no_valido",
            )

    def _leer_posicion(
        self, request: AttachConceptoGraficoRequest, sentencias: ConceptoGraficoStatements
    ) -> int:
        filas = self._leer(request, sentencias.siguiente_pos(request.conide))
        return int(filas[0][0]) if filas else POS_PASO

    @staticmethod
    def _buscar_idempotencia(
        documento: Any, candidatos: list[tuple[Any, ...]]
    ) -> tuple[int, str, int] | None:
        """
        De los binarios del concepto con el MISMO tamano, el que ademas tenga el
        mismo `sha256`. Se compara en Python: `HASHBYTES` no vale en SQL Server
        2012 [MEDIDO]. Una huerfana nunca llega aqui: L5 hace `JOIN` con la
        documental, y sin binario no hay nada que comparar.
        """
        for fila in candidatos:
            ide_negocio, cod_existente, ide_enlace, binario = fila[:4]
            if binario is None:
                continue
            if hashlib.sha256(bytes(binario)).hexdigest() == documento.sha256:
                return int(ide_negocio), str(cod_existente), int(ide_enlace)
        return None

    def _avisar_de_huerfanas(
        self, request: AttachConceptoGraficoRequest, sentencias: ConceptoGraficoStatements
    ) -> list[str]:
        huerfanas = self._leer(
            request,
            sentencias.buscar_huerfanas(request.conide),
            max_rows=self._settings.max_allowed_rows,
        )
        if not huerfanas:
            return []
        ides = ", ".join(str(fila[0]) for fila in huerfanas)
        return [
            (
                f"El concepto tiene {len(huerfanas)} grafico(s) sin binario en la base "
                f"documental (ide {ides}). No se reparan: se adjunta uno nuevo."
            )
        ]

    # ------------------------------------------------------------------ #
    # Respuestas
    # ------------------------------------------------------------------ #
    def _grafico(
        self,
        request: AttachConceptoGraficoRequest,
        documento: Any,
        cod: str,
        emp: int,
        fec: int,
        *,
        ide_documental: int | None = None,
        ide_negocio: int | None = None,
        fila_documental: dict[str, Any] | None = None,
        fila_negocio: dict[str, Any] | None = None,
    ) -> GraficoPreview:
        return GraficoPreview(
            ide_documental=ide_documental,
            ide_negocio=ide_negocio,
            cod=cod,
            emp=emp,
            nom=request.nom,
            fec=fec,
            usu=request.usu,
            res=request.res,
            gratipide=request.gratipide,
            vin=VIN_REPOSITORIO,
            bytes=documento.bytes,
            sha256=documento.sha256,
            content_type=documento.content_type,
            fila_documental=(
                ConceptoGraficoStatements.fila_para_preview(fila_documental)
                if fila_documental
                else {}
            ),
            fila_negocio=(
                ConceptoGraficoStatements.fila_para_preview(fila_negocio)
                if fila_negocio
                else {}
            ),
        )

    def _respuesta_idempotente(
        self,
        request: AttachConceptoGraficoRequest,
        documental: str,
        concepto: ConceptoPreview,
        documento: Any,
        cod_nuevo: str,
        ya_colgado: tuple[int, str, int],
        avisos: list[str],
    ) -> AttachConceptoGraficoResponse:
        ide_negocio, cod_existente, ide_enlace = ya_colgado
        return AttachConceptoGraficoResponse(
            committed=False,
            dry_run=not request.commit,
            idempotente=True,
            database=request.database,
            database_documental=documental,
            concepto=concepto,
            grafico=self._grafico(
                request, documento, cod_existente, concepto.emp, 0,
                ide_negocio=ide_negocio,
            ),
            enlace=EnlacePreview(ide=ide_enlace, con=concepto.ide, gra=ide_negocio),
            filas_afectadas=0,
            avisos=avisos
            + [
                (
                    "Ese documento ya estaba adjunto a este concepto (mismo tamano y "
                    f"sha256): no se ha escrito nada. Se devuelve el grafico existente "
                    f"(ide {ide_negocio}, cod {cod_existente}); el cod que se habria "
                    f"generado era {cod_nuevo}."
                )
            ],
        )

    def _respuesta_dry_run(
        self,
        request: AttachConceptoGraficoRequest,
        documental: str,
        concepto: ConceptoPreview,
        documento: Any,
        cod: str,
        pos: int,
        fila_documental: dict[str, Any],
        fila_negocio: dict[str, Any],
        avisos: list[str],
    ) -> AttachConceptoGraficoResponse:
        ide_documental = self._repo.peek_next_ide(database=documental, table="gra")
        ide_negocio = self._repo.peek_next_ide(database=request.database, table="gra")
        ide_enlace = self._repo.peek_next_ide(database=request.database, table="rcg")
        fila_documental = {**fila_documental, "ide": ide_documental}
        fila_negocio = {**fila_negocio, "ide": ide_negocio}
        return AttachConceptoGraficoResponse(
            committed=False,
            dry_run=True,
            idempotente=False,
            database=request.database,
            database_documental=documental,
            concepto=concepto,
            grafico=self._grafico(
                request, documento, cod, concepto.emp, int(fila_negocio["fec"]),
                ide_documental=ide_documental,
                ide_negocio=ide_negocio,
                fila_documental=fila_documental,
                fila_negocio=fila_negocio,
            ),
            enlace=EnlacePreview(
                ide=ide_enlace, con=concepto.ide, gra=ide_negocio, pos=pos
            ),
            filas_afectadas=0,
            avisos=avisos + [_AVISO_DRY_RUN],
        )

    # ------------------------------------------------------------------ #
    # Commit (R11, R12, R14, R15)
    # ------------------------------------------------------------------ #
    def _commit(
        self,
        request: AttachConceptoGraficoRequest,
        documental: str,
        concepto: ConceptoPreview,
        documento: Any,
        cod: str,
        pos: int,
        fila_documental: dict[str, Any],
        fila_negocio: dict[str, Any],
        sentencias: ConceptoGraficoStatements,
        avisos: list[str],
    ) -> AttachConceptoGraficoResponse:
        timeout = self._settings.sigrid_document_write_timeout_seconds

        def work(cursor: Any) -> dict[str, Any]:
            # Reentrante: `run_in_write_transaction` repite `work` entero en
            # cada reintento, y el `cod` (generado fuera) es el mismo.
            cursor.connection.timeout = timeout

            # R17: bajo el applock, por si lo colgo otro entre la lectura y aqui.
            sql, params = sentencias.buscar_idempotencia(request.conide, documento.bytes)
            cursor.execute(sql, *params)
            ya_colgado = self._buscar_idempotencia(documento, list(cursor.fetchall()))
            if ya_colgado is not None:
                return {"idempotente": ya_colgado}

            ide_documental = self._reservar(cursor, sentencias.reservar_ide_documental())
            ide_negocio = self._reservar(cursor, sentencias.reservar_ide_negocio())
            ide_enlace = self._reservar(cursor, sentencias.reservar_ide_enlace())

            fila_documental["ide"] = ide_documental
            fila_negocio["ide"] = ide_negocio
            fila_enlace = sentencias.construir_fila_enlace(
                ide=ide_enlace, con=concepto.ide, gra=ide_negocio, pos=pos
            )

            # Orden: documental -> negocio -> enlace. Cada prefijo es invisible
            # para Sigrid si algo se partiera.
            for sentencia in (
                sentencias.insertar_documental(fila_documental),
                sentencias.insertar_negocio(fila_negocio),
                sentencias.insertar_enlace(fila_enlace),
            ):
                cursor.execute(sentencia[0], *sentencia[1])

            # R14: con NOCOUNT ON el `rowcount` no es fiable; la prueba de que
            # la fila esta es volver a leerla.
            for sentencia, que in (
                (sentencias.releer_documental(concepto.emp, cod), "la fila documental"),
                (sentencias.releer_negocio(concepto.emp, cod), "la fila de negocio"),
                (sentencias.releer_enlace(ide_enlace), "el enlace"),
            ):
                cursor.execute(sentencia[0], *sentencia[1])
                cuantas = int(cursor.fetchone()[0])
                if cuantas != 1:
                    raise ConceptoGraficoError(
                        f"Tras insertar, {que} aparece {cuantas} veces en vez de una. "
                        "Se revierte la transaccion entera.",
                        codigo="filas_afectadas_inesperadas",
                    )

            return {
                "ide_documental": ide_documental,
                "ide_negocio": ide_negocio,
                "ide_enlace": ide_enlace,
            }

        resultado = self._repo.run_in_write_transaction(
            database=request.database,
            timeout_seconds=timeout,
            applock_resources=[
                f"SIGRID_IDE_{documental}_gra",
                "SIGRID_IDE_gra",
                "SIGRID_IDE_rcg",
            ],
            applock_timeout_ms=self._settings.applock_timeout_ms,
            max_retries=self._settings.domain_write_max_retries,
            work=work,
        )

        if "idempotente" in resultado:
            return self._respuesta_idempotente(
                request, documental, concepto, documento, cod,
                resultado["idempotente"], avisos,
            )

        return AttachConceptoGraficoResponse(
            committed=True,
            dry_run=False,
            idempotente=False,
            database=request.database,
            database_documental=documental,
            concepto=concepto,
            grafico=self._grafico(
                request, documento, cod, concepto.emp, int(fila_negocio["fec"]),
                ide_documental=resultado["ide_documental"],
                ide_negocio=resultado["ide_negocio"],
                fila_documental=fila_documental,
                fila_negocio=fila_negocio,
            ),
            enlace=EnlacePreview(
                ide=resultado["ide_enlace"],
                con=concepto.ide,
                gra=resultado["ide_negocio"],
                pos=pos,
            ),
            filas_afectadas=3,
            avisos=avisos
            + [
                (
                    "Escritas las tres filas y releidas dentro de la transaccion. "
                    "Comprueba el fichero con documents/read sobre la base documental "
                    "(table=gra, id_column=cod) y el sha256 devuelto."
                )
            ],
        )

    @staticmethod
    def _reservar(cursor: Any, sentencia: tuple[str, list[Any]]) -> int:
        cursor.execute(sentencia[0], *sentencia[1])
        return int(cursor.fetchone()[0])
