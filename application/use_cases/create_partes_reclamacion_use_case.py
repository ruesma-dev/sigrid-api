# application/use_cases/create_partes_reclamacion_use_case.py
"""
Alta EN LOTE de partes de reclamacion de Posventa en Sigrid (F-006).

Un parte son cinco filas, como las escribe el escritorio de Sigrid al crear
un parte desde la pestana Reclamaciones de la unidad postventa: `con` (tip
708, serie `RS<aa>.<mm>/`), `rcp`, `rcpint` (0..N intervinientes), `conext`
(`RCPCLI`, la referencia externa que da la idempotencia) y la fila de alta de
`dbo.log`. Sin triggers, sin IDENTITY y sin DEFAULT en ninguna.

Flujo: guards del lote -> lecturas comunes de la obra (una vez) -> por parte,
en el orden de la peticion: presupuesto de tiempo -> validar -> idempotencia
-> preview (dry-run) o SU PROPIA transaccion (commit). Un parte que falla no
impide los demas: su fallo va en su resultado y el lote responde 200.

`commit=False` (por defecto) => DRY-RUN: solo lecturas y solo con credenciales
de lectura. El `cod` y los `ide` del preview son provisionales.
"""
from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.use_cases.parte_reclamacion_statements import (
    POS_PASO,
    TAM_SERIE,
    ParteReclamacionStatements,
    Sellos,
    sellos,
    siguiente_cod,
)
from domain.models.parte_reclamacion_models import (
    CreatePartesReclamacionRequest,
    CreatePartesReclamacionResponse,
    MotivoParte,
    ObraResumen,
    ParteIn,
    ParteReclamacionError,
    ResultadoParte,
    ResumenLote,
)
from domain.models.sql_models import SqlReadRequest

logger = logging.getLogger(__name__)

_ENDPOINT = "sigrid/partes-reclamacion"

#: Bloqueos de aplicacion de cada transaccion, SIEMPRE en este orden.
#: `SIGRID_IDE_con` es el mismo nombre que usan los albaranes: las altas de
#: `con` de los dos endpoints quedan serializadas. Los demas no los toma nadie
#: mas, asi que no hay orden inverso posible (design.md §Applocks).
APPLOCKS: tuple[str, ...] = (
    "SIGRID_REFEXT_708",
    "SIGRID_SERIE_708",
    "SIGRID_IDE_con",
    "SIGRID_POS_rcp",
    "SIGRID_IDE_rcpint",
    "SIGRID_IDE_conext",
    "SIGRID_IDE_log",
)

_AVISO_PROVISIONAL = (
    "DRY-RUN: no se ha escrito nada. El cod y los ide son provisionales (MAX en el "
    "instante de la consulta, consecutivos dentro del lote); se reservan de nuevo "
    "bajo bloqueo en el commit."
)


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _clave(texto: str | None) -> str | None:
    """Codigos comparados como los compara el ERP (`Modern_Spanish_CI_AS`):
    sin mayusculas ni espacios de cola."""
    return None if texto is None else str(texto).strip().casefold()


def _es_colision_de_clave(exc: BaseException) -> bool:
    """`pyodbc.IntegrityError` sin importar `pyodbc` en la capa de aplicacion:
    el repositorio la propaga tal cual cuando agota los reintentos."""
    return any(clase.__name__ == "IntegrityError" for clase in type(exc).__mro__)


@dataclass
class _Lote:
    """Lo leido una vez por lote (R6)."""

    emp: int
    est: int
    obra: ObraResumen
    # clave(cod) -> (ide, cod, cliide, recide)
    unidades: dict[str, tuple[int, str, int, int]]
    # (obrofc.ide, pos, clave(oficio) | None, clave(proveedor) | None)
    oficios_de_obra: list[tuple[int, int, str | None, str | None]]
    tipos: dict[str, int]
    clases: dict[str, int]
    oficios: dict[str, int]


@dataclass
class _Plan:
    """Un parte ya validado, listo para preview o para escribir."""

    upvide: int
    sellos: Sellos
    filas: dict[str, Any]
    obrofcides: list[int]
    avisos: list[str] = field(default_factory=list)


class _Rechazo(Exception):
    """Un parte que no se escribe, con su resultado ya decidido."""

    def __init__(self, estado: str, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.estado = estado
        self.codigo = codigo
        self.mensaje = mensaje


class CreatePartesReclamacionUseCase:
    def __init__(
        self,
        repository: Any,
        settings: Any,
        reloj: Callable[[], float] = time.monotonic,
        ahora_utc: Callable[[], datetime] = _ahora_utc,
    ) -> None:
        self._repo = repository
        self._settings = settings
        self._reloj = reloj
        self._ahora_utc = ahora_utc

    # ------------------------------------------------------------------ #
    # Orquestacion y trazas (R20)
    # ------------------------------------------------------------------ #
    def run(self, request: CreatePartesReclamacionRequest) -> CreatePartesReclamacionResponse:
        arranque = self._reloj()
        traza: dict[str, Any] = {
            "endpoint": _ENDPOINT,
            "database": request.database,
            "obra": request.obra,
            "usu": request.usu,
            "commit": request.commit,
            "partes": len(request.partes),
        }
        try:
            respuesta = self._ejecutar(request, arranque)
        except ParteReclamacionError as exc:
            traza["resultado"] = "error"
            traza["codigo"] = exc.codigo
            self._trazar(traza, arranque)
            raise
        except Exception as exc:
            traza["resultado"] = "excepcion"
            traza["codigo"] = type(exc).__name__
            self._trazar(traza, arranque)
            raise

        for resultado in respuesta.partes:
            # Una traza por parte: referencia, estado, codigo, ide y cod.
            # NUNCA descripciones, ubicaciones ni textos del parte.
            logger.info(
                json.dumps(
                    {
                        "endpoint": _ENDPOINT,
                        "indice": resultado.indice,
                        "referencia": resultado.referencia_externa,
                        "estado": resultado.estado,
                        "codigo": resultado.motivo.codigo if resultado.motivo else None,
                        "ide": resultado.ide,
                        "cod": resultado.cod,
                    },
                    ensure_ascii=False,
                )
            )
        traza["resultado"] = "ok"
        traza["resumen"] = respuesta.resumen.model_dump()
        self._trazar(traza, arranque)
        return respuesta

    def _trazar(self, traza: dict[str, Any], arranque: float) -> None:
        traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)
        logger.info(json.dumps(traza, ensure_ascii=False, default=str))

    def _ejecutar(
        self, request: CreatePartesReclamacionRequest, arranque: float
    ) -> CreatePartesReclamacionResponse:
        # 1. Guards del lote: antes de leer nada.
        if request.commit:
            self._exigir_llaves_de_escritura()
        self._validar_base(request.database)
        tope = self._settings.sigrid_reclamacion_max_partes
        if len(request.partes) > tope:
            raise ParteReclamacionError(
                f"El lote trae {len(request.partes)} partes y el tope es {tope}: trocealo.",
                codigo="lote_demasiado_grande",
            )

        # 2. Lecturas comunes de la obra, una vez.
        sentencias = ParteReclamacionStatements(database=request.database)
        lote = self._leer_lote(request, sentencias)

        # 3. Parte a parte, en el orden de la peticion.
        numeracion = _NumeracionProvisional(self, request, sentencias, lote.emp)
        presupuesto = self._settings.sigrid_reclamacion_presupuesto_segundos
        referencias_vistas: dict[str, int] = {}
        agotado = False
        resultados: list[ResultadoParte] = []

        for indice, parte in enumerate(request.partes):
            if not agotado and self._reloj() - arranque > presupuesto:
                agotado = True
            if agotado:
                resultados.append(
                    self._resultado_fallido(
                        indice,
                        parte,
                        _Rechazo(
                            "no_procesado",
                            "presupuesto_de_tiempo_agotado",
                            f"Pasados {presupuesto} s no se empiezan mas partes. Reenvialo: "
                            "la referencia externa hace que reenviar sea seguro.",
                        ),
                    )
                )
                continue
            try:
                resultados.append(
                    self._procesar_parte(
                        request, sentencias, lote, numeracion, referencias_vistas, indice, parte
                    )
                )
            except _Rechazo as rechazo:
                resultados.append(self._resultado_fallido(indice, parte, rechazo))

        resumen = ResumenLote(
            creados=sum(r.estado == "creado" for r in resultados),
            idempotentes=sum(r.estado == "idempotente" for r in resultados),
            previstos=sum(r.estado == "previsto" for r in resultados),
            rechazados=sum(r.estado == "rechazado" for r in resultados),
            no_procesados=sum(r.estado == "no_procesado" for r in resultados),
        )
        return CreatePartesReclamacionResponse(
            committed=resumen.creados > 0,
            dry_run=not request.commit,
            database=request.database,
            obra=lote.obra,
            resumen=resumen,
            partes=resultados,
        )

    # ------------------------------------------------------------------ #
    # Guards del lote (R3, R10)
    # ------------------------------------------------------------------ #
    def _exigir_llaves_de_escritura(self) -> None:
        if not (
            self._settings.sigrid_domain_write_enabled
            and self._settings.sigrid_reclamacion_write_enabled
            and self._settings.sql_server_write_username
            and self._settings.sql_server_write_password
        ):
            raise ParteReclamacionError(
                "Escritura de partes desactivada: hacen falta SIGRID_DOMAIN_WRITE_ENABLED, "
                "SIGRID_RECLAMACION_WRITE_ENABLED y credenciales de escritura.",
                codigo="escritura_reclamaciones_deshabilitada",
            )

    def _validar_base(self, database: str) -> None:
        # Una lista VACIA no abre: al contrario que el patron de albaranes.
        if database not in self._settings.allowed_write_databases:
            raise ParteReclamacionError(
                f"La base '{database}' no esta permitida para escritura.",
                codigo="base_de_datos_no_permitida",
            )

    # ------------------------------------------------------------------ #
    # Lecturas (R6)
    # ------------------------------------------------------------------ #
    def _leer(
        self,
        request: CreatePartesReclamacionRequest,
        sentencia: tuple[str, list[Any]],
        *,
        muchas: bool = False,
    ) -> list[tuple[Any, ...]]:
        """
        Lectura con credenciales de LECTURA. `model_construct` a proposito,
        como en F-004: el SQL es constante y los parametros los pone el caso de
        uso. Las lecturas que pueden traer muchas filas piden el tope maximo, y
        truncar NUNCA se ignora: una lista de UPV u oficios a medias validaria
        mal en silencio.
        """
        sql, params = sentencia
        _columnas, filas, truncado = self._repo.execute_read_query(
            SqlReadRequest.model_construct(
                database=request.database,
                sql=sql,
                parameters=params,
                max_rows=self._settings.max_allowed_rows if muchas else None,
            )
        )
        if truncado:
            raise ValueError(
                "Una lectura devolvio mas filas de las que se pueden traer (truncada): "
                f"no se procesa el lote de la obra '{request.obra}'."
            )
        return list(filas)

    def _leer_lote(
        self, request: CreatePartesReclamacionRequest, sentencias: ParteReclamacionStatements
    ) -> _Lote:
        series = self._leer(request, sentencias.leer_serie())
        if len(series) != 1 or int(series[0][2]) != TAM_SERIE:
            raise ParteReclamacionError(
                "No hay una unica serie activa RS<año2>.<mes>/ de partes (tip 708) con "
                f"{TAM_SERIE} digitos en dbo.sercon.",
                codigo="serie_no_encontrada",
            )
        # Las filas se desempaquetan enteras: el SQL es constante y trae
        # exactamente esas columnas (lo fija test_f006_statements).
        _ide_serie, emp, _tam, estini = series[0]
        emp, estini = int(emp), int(estini)

        # El estado NO se escribe a mano: sale de la serie y se valida (ARCH §7).
        if not self._leer(request, sentencias.leer_estado_inicial(estini)):
            raise ParteReclamacionError(
                f"El estado inicial {estini} de la serie no existe en dbo.conest (tip 708).",
                codigo="estado_inicial_no_encontrado",
            )

        obras = self._leer(request, sentencias.leer_obra(emp, request.obra))
        if not obras:
            raise ParteReclamacionError(
                f"No existe la obra '{request.obra}' en la empresa {emp}.",
                codigo="obra_no_encontrada",
            )
        obra_ide, obra_emp, obra_cod = obras[0]
        obra = ObraResumen(ide=int(obra_ide), cod=str(obra_cod), emp=int(obra_emp))

        if not self._leer(request, sentencias.leer_usuario(request.usu)):
            raise ParteReclamacionError(
                f"El usuario '{request.usu}' no existe en dbo.usu.",
                codigo="usuario_no_valido",
            )

        # cliide/recide nunca llegan NULL: L5 los lee con ISNULL(..., 0).
        unidades = {
            _clave(cod): (int(ide), str(cod), int(cliide), int(recide))
            for ide, cod, cliide, recide in self._leer(
                request, sentencias.leer_unidades_postventa(obra.ide, emp), muchas=True
            )
        }
        oficios_de_obra = [
            (int(ide), int(pos or 0), _clave(oficio), _clave(proveedor))
            for ide, pos, oficio, proveedor in self._leer(
                request, sentencias.leer_oficios_de_la_obra(obra.ide), muchas=True
            )
        ]
        return _Lote(
            emp=emp,
            est=estini,
            obra=obra,
            unidades=unidades,
            oficios_de_obra=oficios_de_obra,
            tipos=self._catalogo(request, sentencias.leer_tipos()),
            clases=self._catalogo(request, sentencias.leer_clases()),
            oficios=self._catalogo(request, sentencias.leer_oficios()),
        )

    def _catalogo(
        self, request: CreatePartesReclamacionRequest, sentencia: tuple[str, list[Any]]
    ) -> dict[str, int]:
        """clave(cod) -> ide de un catalogo; `fecbaj != 0` cuenta como inexistente."""
        return {
            _clave(cod): int(ide)
            for ide, cod, fecbaj in self._leer(request, sentencia, muchas=True)
            if not int(fecbaj or 0)
        }

    # ------------------------------------------------------------------ #
    # Un parte
    # ------------------------------------------------------------------ #
    def _procesar_parte(
        self,
        request: CreatePartesReclamacionRequest,
        sentencias: ParteReclamacionStatements,
        lote: _Lote,
        numeracion: _NumeracionProvisional,
        referencias_vistas: dict[str, int],
        indice: int,
        parte: ParteIn,
    ) -> ResultadoParte:
        plan = self._planificar(request, sentencias, lote, referencias_vistas, indice, parte)

        if not request.commit:
            filas_leidas = self._leer(
                request, sentencias.buscar_referencia(parte.referencia_externa, lote.emp), muchas=True
            )
            existente = self._resolver_referencia(filas_leidas, plan.upvide, parte)
            if existente is not None:
                return self._resultado_idempotente(indice, parte, existente, plan.avisos)
            filas = numeracion.numerar(plan)
            return ResultadoParte(
                indice=indice,
                referencia_externa=parte.referencia_externa,
                estado="previsto",
                ide=filas["con"]["ide"],
                cod=filas["con"]["cod"],
                filas=filas,
                avisos=plan.avisos + [_AVISO_PROVISIONAL],
            )

        return self._escribir(request, sentencias, lote, indice, parte, plan)

    def _planificar(
        self,
        request: CreatePartesReclamacionRequest,
        sentencias: ParteReclamacionStatements,
        lote: _Lote,
        referencias_vistas: dict[str, int],
        indice: int,
        parte: ParteIn,
    ) -> _Plan:
        """Validaciones de R7-R8 con lo ya leido: ninguna ida a la base."""
        referencia = parte.referencia_externa
        prefijos = self._settings.sigrid_reclamacion_prefijos_referencia
        if not any(referencia.startswith(prefijo) for prefijo in prefijos):
            raise _Rechazo(
                "rechazado",
                "referencia_no_permitida",
                "La referencia externa no empieza por ningun prefijo admitido "
                f"({', '.join(prefijos) or 'ninguno configurado'}).",
            )
        clave_referencia = _clave(referencia)
        if clave_referencia in referencias_vistas:
            raise _Rechazo(
                "rechazado",
                "referencia_duplicada_en_lote",
                "La misma referencia externa ya viene en el parte de indice "
                f"{referencias_vistas[clave_referencia]} de este lote.",
            )
        # La primera aparicion es la duena de la referencia en el lote.
        referencias_vistas[clave_referencia] = indice

        unidad = lote.unidades.get(_clave(parte.unidad_postventa))
        if unidad is None:
            raise _Rechazo(
                "rechazado",
                "unidad_postventa_no_encontrada",
                f"La unidad postventa '{parte.unidad_postventa}' no existe o no es de la obra.",
            )
        trcpide = lote.tipos.get(_clave(parte.tipo))
        if trcpide is None:
            raise _Rechazo(
                "rechazado", "tipo_no_valido",
                f"El tipo de reclamacion '{parte.tipo}' no existe o esta de baja en dbo.auxtrcp.",
            )
        clase_ide = 0
        if parte.clase is not None:
            clase = lote.clases.get(_clave(parte.clase))
            if clase is None:
                raise _Rechazo(
                    "rechazado", "clase_no_valida",
                    f"La clase '{parte.clase}' no existe o esta de baja en dbo.auxrcp.",
                )
            clase_ide = clase
        clave_oficio = _clave(parte.oficio)
        ofcide = lote.oficios.get(clave_oficio)
        if ofcide is None or not any(f[2] == clave_oficio for f in lote.oficios_de_obra):
            raise _Rechazo(
                "rechazado", "oficio_no_esta_en_la_obra",
                f"El oficio '{parte.oficio}' no existe en dbo.auxofc o no esta entre los "
                "oficios de la obra.",
            )

        avisos: list[str] = []
        intervinientes = self._resolver_intervinientes(lote, parte, avisos)
        if not any(_clave(i.oficio) == clave_oficio for i in parte.intervinientes):
            avisos.append(
                f"El oficio del parte ({parte.oficio}) no esta entre los intervinientes: "
                "se crea igual."
            )

        momento = sellos(self._ahora_utc())
        filas = sentencias.construir_filas(
            emp=lote.emp,
            est=lote.est,
            descripcion=parte.descripcion,
            descripcion_larga=parte.descripcion_larga,
            fec=momento.fec,
            hor=momento.hor,
            tiemod=momento.tiemod,
            upvide=unidad[0],
            cliide=unidad[2],
            recide=unidad[3],
            clase_ide=clase_ide,
            rcptip=parte.forma_comunicacion,
            trcpide=trcpide,
            resubi=parte.ubicacion,
            ofcide=ofcide,
            intervinientes=intervinientes,
            referencia=referencia,
            usu=request.usu,
        )
        return _Plan(
            upvide=unidad[0],
            sellos=momento,
            filas=filas,
            obrofcides=[obrofcide for obrofcide, _causante in intervinientes],
            avisos=avisos,
        )

    @staticmethod
    def _resolver_intervinientes(
        lote: _Lote, parte: ParteIn, avisos: list[str]
    ) -> list[tuple[int, bool]]:
        """R8: cada interviniente contra los `obrofc` de la obra."""
        elegidos: list[tuple[int, bool]] = []
        for interviniente in parte.intervinientes:
            oficio = _clave(interviniente.oficio)
            proveedor = _clave(interviniente.proveedor)
            candidatos = [
                fila
                for fila in lote.oficios_de_obra
                if fila[2] == oficio and (proveedor is None or fila[3] == proveedor)
            ]
            descripcion = interviniente.oficio + (
                f"/{interviniente.proveedor}" if interviniente.proveedor else ""
            )
            if not candidatos:
                raise _Rechazo(
                    "rechazado", "interviniente_no_esta_en_la_obra",
                    f"El interviniente {descripcion} no esta entre los oficios de la obra.",
                )
            if len({fila[3] for fila in candidatos}) > 1:
                raise _Rechazo(
                    "rechazado", "interviniente_ambiguo",
                    f"El oficio {interviniente.oficio} tiene varios proveedores en la obra: "
                    "indica el proveedor.",
                )
            elegido = min(candidatos, key=lambda fila: (fila[1], fila[0]))
            if len(candidatos) > 1:
                avisos.append(
                    f"El interviniente {descripcion} tiene {len(candidatos)} filas identicas "
                    f"en la obra: se usa la de menor pos (obrofc {elegido[0]})."
                )
            if any(obrofcide == elegido[0] for obrofcide, _ in elegidos):
                raise _Rechazo(
                    "rechazado", "interviniente_repetido",
                    f"El interviniente {descripcion} (obrofc {elegido[0]}) viene dos veces.",
                )
            elegidos.append((elegido[0], interviniente.causante))
        return elegidos

    @staticmethod
    def _resolver_referencia(
        filas: list[tuple[Any, ...]], upvide: int, parte: ParteIn
    ) -> tuple[int, str] | None:
        """R15: un parte con la misma referencia Y la misma UPV es el mismo
        parte. Cualquier otra coincidencia es un conflicto."""
        if not filas:
            return None
        if len(filas) == 1 and filas[0][2] is not None and int(filas[0][2]) == upvide:
            return int(filas[0][0]), str(filas[0][1])
        raise _Rechazo(
            "rechazado", "referencia_en_conflicto",
            f"La referencia externa ya esta en {len(filas)} parte(s) de otra unidad postventa "
            f"o sin ficha: {', '.join(str(f[1]) for f in filas)}.",
        )

    # ------------------------------------------------------------------ #
    # Commit: una transaccion por parte (R11-R15)
    # ------------------------------------------------------------------ #
    def _escribir(
        self,
        request: CreatePartesReclamacionRequest,
        sentencias: ParteReclamacionStatements,
        lote: _Lote,
        indice: int,
        parte: ParteIn,
        plan: _Plan,
    ) -> ResultadoParte:
        timeout = self._settings.default_write_timeout_seconds

        def work(cursor: Any) -> dict[str, Any]:
            # Reentrante: el repositorio repite `work` entero ante una clave
            # duplicada. Las filas de `plan` no se tocan; cada intento numera
            # sobre ellas, y fec/hor/tiemod ya vienen fijados (R16).
            cursor.connection.timeout = timeout

            # E1: idempotencia bajo el applock de referencias.
            self._ejecutar_sql(cursor, sentencias.buscar_referencia(parte.referencia_externa, lote.emp))
            existente = self._resolver_referencia(list(cursor.fetchall()), plan.upvide, parte)
            if existente is not None:
                return {"idempotente": existente}

            # E2-E7: numeracion bajo UPDLOCK, HOLDLOCK.
            self._ejecutar_sql(cursor, sentencias.reservar_cod(lote.emp, plan.sellos.prefijo))
            cod = siguiente_cod(plan.sellos.prefijo, cursor.fetchone()[0], TAM_SERIE)
            ide_con = self._reservar(cursor, sentencias.reservar_ide_con())
            pos_rcp = self._reservar(cursor, sentencias.reservar_pos_rcp())
            ide_rcpint = (
                self._reservar(cursor, sentencias.reservar_ide_rcpint())
                if plan.obrofcides
                else None
            )
            ide_conext = self._reservar(cursor, sentencias.reservar_ide_conext())
            ide_log = self._reservar(cursor, sentencias.reservar_ide_log())

            # E8: la UPV y cada obrofc siguen siendo de la obra.
            self._contar(
                cursor, sentencias.revalidar_unidad_postventa(plan.upvide, lote.obra.ide), 1,
                "la unidad postventa en la obra",
            )
            for obrofcide in plan.obrofcides:
                self._contar(
                    cursor, sentencias.revalidar_oficio_de_obra(obrofcide, lote.obra.ide), 1,
                    f"el obrofc {obrofcide} en la obra",
                )

            filas = sentencias.numerar(
                plan.filas,
                cod=cod,
                ide_con=ide_con,
                pos_rcp=pos_rcp,
                ide_rcpint=ide_rcpint,
                ide_conext=ide_conext,
                ide_log=ide_log,
            )

            # E9-E13, en este orden.
            self._ejecutar_sql(cursor, sentencias.insertar_con(filas["con"]))
            self._ejecutar_sql(cursor, sentencias.insertar_rcp(filas["rcp"]))
            for fila in filas["rcpint"]:
                self._ejecutar_sql(cursor, sentencias.insertar_rcpint(fila))
            self._ejecutar_sql(cursor, sentencias.insertar_conext(filas["conext"]))
            self._ejecutar_sql(cursor, sentencias.insertar_log(filas["log"]))

            # E14: con NOCOUNT ON el rowcount no es fiable; se relee por clave.
            for sentencia, esperadas, que in (
                (sentencias.releer_con(lote.emp, cod), 1, "con"),
                (sentencias.releer_rcp(ide_con), 1, "rcp"),
                (sentencias.releer_rcpint(ide_con), len(filas["rcpint"]), "rcpint"),
                (sentencias.releer_conext(ide_con), 1, "conext"),
                (sentencias.releer_log(ide_log), 1, "log"),
            ):
                self._contar(cursor, sentencia, esperadas, f"las filas de {que}")
            return {"filas": filas}

        try:
            resultado = self._repo.run_in_write_transaction(
                database=request.database,
                timeout_seconds=timeout,
                applock_resources=list(APPLOCKS),
                applock_timeout_ms=self._settings.applock_timeout_ms,
                max_retries=self._settings.domain_write_max_retries,
                work=work,
            )
        except _Rechazo:
            raise
        except ParteReclamacionError as exc:
            raise _Rechazo("rechazado", exc.codigo, str(exc)) from exc
        except Exception as exc:
            if _es_colision_de_clave(exc):
                raise _Rechazo(
                    "rechazado", "colision_de_clave",
                    "Colision de clave repetida tras los reintentos (alta simultanea): el "
                    "parte no se ha escrito. Reenvialo.",
                ) from exc
            raise _Rechazo(
                "rechazado", "error_de_escritura",
                f"Error al escribir el parte ({type(exc).__name__}): la transaccion se "
                "revirtio y no se ha escrito nada de el.",
            ) from exc

        if "idempotente" in resultado:
            return self._resultado_idempotente(indice, parte, resultado["idempotente"], plan.avisos)
        filas = resultado["filas"]
        return ResultadoParte(
            indice=indice,
            referencia_externa=parte.referencia_externa,
            estado="creado",
            ide=filas["con"]["ide"],
            cod=filas["con"]["cod"],
            filas=filas,
            avisos=plan.avisos,
        )

    @staticmethod
    def _ejecutar_sql(cursor: Any, sentencia: tuple[str, list[Any]]) -> None:
        cursor.execute(sentencia[0], *sentencia[1])

    @classmethod
    def _reservar(cls, cursor: Any, sentencia: tuple[str, list[Any]]) -> int:
        cls._ejecutar_sql(cursor, sentencia)
        return int(cursor.fetchone()[0])

    @classmethod
    def _contar(
        cls, cursor: Any, sentencia: tuple[str, list[Any]], esperadas: int, que: str
    ) -> None:
        cuantas = cls._reservar(cursor, sentencia)
        if cuantas != esperadas:
            raise ParteReclamacionError(
                f"Se esperaban {esperadas} para {que} y hay {cuantas}: se revierte el parte.",
                codigo="filas_afectadas_inesperadas",
            )

    # ------------------------------------------------------------------ #
    # Resultados
    # ------------------------------------------------------------------ #
    @staticmethod
    def _resultado_fallido(indice: int, parte: ParteIn, rechazo: _Rechazo) -> ResultadoParte:
        return ResultadoParte(
            indice=indice,
            referencia_externa=parte.referencia_externa,
            estado=rechazo.estado,
            motivo=MotivoParte(codigo=rechazo.codigo, mensaje=rechazo.mensaje),
        )

    @staticmethod
    def _resultado_idempotente(
        indice: int, parte: ParteIn, existente: tuple[int, str], avisos: list[str]
    ) -> ResultadoParte:
        ide, cod = existente
        return ResultadoParte(
            indice=indice,
            referencia_externa=parte.referencia_externa,
            estado="idempotente",
            ide=ide,
            cod=cod,
            avisos=avisos
            + [
                (
                    f"Ya existe el parte {cod} con esta referencia externa en esta unidad "
                    "postventa: no se ha escrito nada."
                )
            ],
        )


class _NumeracionProvisional:
    """
    Numeracion del DRY-RUN: se lee UNA vez (sin bloqueo) en el primer parte
    previsto y se desplaza por los previstos anteriores del lote, para que el
    preview de N partes muestre N numeros consecutivos y no N veces el mismo.
    Los rechazados no gastan numero. El `cod` se lleva por prefijo de mes.
    """

    def __init__(
        self,
        caso: CreatePartesReclamacionUseCase,
        request: CreatePartesReclamacionRequest,
        sentencias: ParteReclamacionStatements,
        emp: int,
    ) -> None:
        self._caso = caso
        self._request = request
        self._sentencias = sentencias
        self._emp = emp
        self._ultimo_cod: dict[str, str | None] = {}
        self._base: dict[str, int] | None = None
        self._previstos = 0
        self._rcpint = 0

    def numerar(self, plan: _Plan) -> dict[str, Any]:
        prefijo = plan.sellos.prefijo
        if prefijo not in self._ultimo_cod:
            filas = self._caso._leer(self._request, self._sentencias.ultimo_cod(self._emp, prefijo))
            self._ultimo_cod[prefijo] = filas[0][0] if filas else None
        try:
            cod = siguiente_cod(prefijo, self._ultimo_cod[prefijo], TAM_SERIE)
        except ParteReclamacionError as exc:
            raise _Rechazo("rechazado", exc.codigo, str(exc)) from exc

        if self._base is None:
            pos = self._caso._leer(self._request, self._sentencias.siguiente_pos_sin_bloqueo())
            peek = self._caso._repo.peek_next_ide
            database = self._request.database
            self._base = {
                "pos": int(pos[0][0]) if pos else POS_PASO,
                "con": peek(database=database, table="con"),
                "rcpint": peek(database=database, table="rcpint"),
                "conext": peek(database=database, table="conext"),
                "log": peek(database=database, table="log"),
            }

        base, k = self._base, self._previstos
        filas = self._sentencias.numerar(
            plan.filas,
            cod=cod,
            ide_con=base["con"] + k,
            pos_rcp=base["pos"] + POS_PASO * k,
            ide_rcpint=base["rcpint"] + self._rcpint,
            ide_conext=base["conext"] + k,
            ide_log=base["log"] + k,
        )
        self._ultimo_cod[prefijo] = cod
        self._previstos += 1
        self._rcpint += len(plan.filas["rcpint"])
        return filas
