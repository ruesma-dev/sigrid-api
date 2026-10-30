# application/use_cases/create_factura_use_case.py
"""
Caso de uso de `POST /api/sigrid/factura` (F-008): alta de una factura de
compra FR o FRGG en su estado inicial (REC o RECGG), SIN contabilidad (P1).

Patron de `sigrid/proforma`: valida con lecturas y, con `commit`, ejecuta en
`run_in_write_transaction` un trabajo reentrante. No hereda de F-009: importa
sus funciones sueltas y sus lecturas sin editarlas (R47).

Orden de validacion (design §7): llaves y prefijo -> `usu` y `conest` ->
idempotencia -> obra y proveedor -> origenes y modo -> `a_origen` -> lineas sin
origen (fallos juntos) -> totales y retencion -> vencimientos -> duplicadas. La
idempotencia va antes que los origenes a proposito: una peticion repetida
encontraria sus origenes ya facturados por ella misma.

La previa solo lee (R3): ni transaccion ni sentencias de escritura.
"""
from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from application.use_cases.albaran_compra_statements import (
    TIP_CONTRATO,
    AlbaranCompraStatements,
    SellosAlbaran,
    codigo_analitica,
    estados_contrato,
    sellos_del_alta,
    siguiente_cod,
)
from application.use_cases.factura_lineas import (
    LecturasLineas,
    clave,
    comparar_a_origen,
    fecha_de_vencimiento_valida,
    linea_de_origen,
    linea_sin_origen,
    naturalezas_con_cuenta,
    naturalezas_resueltas,
    naturalezas_validas,
    resolver_linea_fr,
    resolver_linea_gg,
    validar_vencimientos,
)
from application.use_cases.factura_statements import (
    APPLOCKS_FACTURA,
    CABECERA_DE_ORIGEN,
    LINEA_DE_ORIGEN,
    ORIGEN,
    PROVEEDOR,
    RETENCION_DE_ORIGEN,
    TIP_ALBARAN,
    TIP_FACTURA,
    TIP_PAGO,
    FacturaStatements,
    FilasFactura,
    construir_con_factura,
    construir_con_pago,
    construir_consii,
    construir_dcaprodes,
    construir_dcf,
    construir_dcfrec,
    construir_log_factura,
    construir_pag,
    numerar,
    prefijo_y_cifras,
    totales_factura,
)
from domain.models.factura_models import (
    FacturaError,
    FacturaRequest,
    FacturaResultado,
    FalloLineaFactura,
)
from domain.models.sql_models import SqlReadRequest

logger = logging.getLogger(__name__)

ENDPOINT = "sigrid/factura"

#: R9: el `conest.cod` del estado inicial de cada serie.
ESTADO_INICIAL: dict[str, str] = {"FR": "REC", "FRGG": "RECGG"}
#: R14, R41: estados del origen; R43: el rechazo de una factura.
CON, FAC, RECH = "CON", "FAC", "RECH"
#: Estado con el que nace el `con` 25 de cada vencimiento (M58), resuelto en `conest`.
PDT = "PDT"
#: R18: `dca.docoritip` de cada modo.
DOCORITIP_DE_MODO: dict[str, int] = {"mes": 0, "origen": 1}
#: R34: `reccla` de la retencion de garantia, que lleva su `pag cla 2`.
RECCLA_GARANTIA = 5
#: R30: tolerancias de los totales del llamante.
TOLERANCIA_BASE = Decimal("0.01")
TOLERANCIA_IVA = Decimal("0.05")
TOLERANCIA_FACTURA = Decimal("0.05")

_AVISO_PROVISIONAL = (
    "DRY-RUN: no se ha escrito nada. El cod y los ide son provisionales (MAX+1 sin "
    "reservar); en el commit se reservan bajo bloqueo."
)
#: R44: lo que la API no hace y queda en el escritorio (P1).
PENDIENTE_EN_SIGRID: tuple[str, ...] = (
    "Comprobar la factura en el escritorio (cabecera, banco, cuentas y analiticas).",
    "Contabilizar en el escritorio: la API no escribe asiento, regiva ni regirp.",
)

Lector = Callable[[tuple[str, list[Any]]], list[tuple[Any, ...]]]


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _entero(valor: Any) -> int:
    return int(valor or 0)


def _d(valor: Any) -> Decimal:
    return valor if isinstance(valor, Decimal) else Decimal(repr(float(valor or 0)))


def _cif(texto: Any) -> str:
    return str(texto or "").strip().upper()


def _unicos(valores: Sequence[str]) -> list[str]:
    vistos: dict[str, str] = {}
    for valor in valores:
        vistos.setdefault(clave(valor), valor)
    return list(vistos.values())


def _agrupar(filas: Sequence[Sequence[Any]], columna: int = 1) -> dict[str, list[Sequence[Any]]]:
    grupos: dict[str, list[Sequence[Any]]] = {}
    for fila in filas:
        grupos.setdefault(clave(fila[columna]), []).append(fila)
    return grupos


@dataclass(frozen=True)
class _Obra:
    ide: int
    emp: int
    cod: str
    cenide: int
    almide: int


@dataclass
class _Contexto:
    """Lo validado fuera de la transaccion, comun a la previa y al commit."""

    request: FacturaRequest
    sellos: SellosAlbaran
    prefijo: str
    cifras: int
    estados: dict[tuple[int, str], int]
    obra: _Obra
    proveedor: dict[str, Any]
    origenes: list[dict[str, Any]]
    heredadas: dict[str, Any]
    ctride: int
    retencion: dict[str, Any] | None
    sin_origen: list[dict[str, Any]]

    @property
    def est_inicial(self) -> int:
        return self.estados[(TIP_FACTURA, ESTADO_INICIAL[self.request.serie])]

    @property
    def est_rech(self) -> int:
        return self.estados[(TIP_FACTURA, RECH)]

    @property
    def est_pago(self) -> int:
        return self.estados[(TIP_PAGO, PDT)]


@dataclass(frozen=True)
class _Montada:
    """La factura armada (sin numerar) a partir de las lineas de origen leidas."""

    lineas_origen: list[tuple[dict[str, Any], dict[str, Any]]]
    filas: FilasFactura
    totales: dict[str, float]
    dcfrec: dict[str, Any] | None


class CreateFacturaUseCase:
    def __init__(
        self,
        repository: Any,
        settings: Any,
        ahora_utc: Callable[[], datetime] = _ahora_utc,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._repo = repository
        self._settings = settings
        self._ahora_utc = ahora_utc
        self._reloj = reloj

    # ------------------------------------------------------------------ #
    # Orquestacion y traza (R46)
    # ------------------------------------------------------------------ #
    def run(self, request: FacturaRequest) -> dict[str, Any]:
        """Una traza por peticion al terminar, con exito o sin el: obra,
        prefijo, `usu`, serie, modo, `commit`, estado, `cod`, lineas por clase,
        vencimientos, codigos y duracion. NUNCA textos, nombres, CIF, numero de
        factura, cuentas ni importes."""
        arranque = self._reloj()
        traza: dict[str, Any] = {
            "endpoint": ENDPOINT,
            "database": request.database,
            "obra": request.cod_obra,
            "prefijo": self._prefijo_de(request.referencia_externa),
            "usu": request.usu,
            "serie": request.serie,
            "modo": request.modo,
            "commit": request.commit,
            "n_origenes": len(request.origenes),
            "n_lineas_origen": None,
            "n_lineas_sin_origen": len(request.lineas),
            "n_vencimientos": len(request.vencimientos),
        }
        try:
            resultado = self._ejecutar(request, traza)
        except FacturaError as exc:
            lineas = exc.details.get("lineas", []) if exc.codigo == "lineas_no_validas" else []
            traza.update(resultado="error", codigo=exc.codigo,
                         codigos=[fallo["codigo"] for fallo in lineas])
            self._trazar(traza, arranque)
            raise
        except Exception as exc:
            # El tipo y no el mensaje: puede citar valores de la peticion.
            traza.update(resultado="excepcion", codigo=type(exc).__name__, codigos=[])
            self._trazar(traza, arranque)
            raise
        traza.update(resultado="ok", estado=resultado.estado, cod=resultado.cod,
                     codigos=[aviso["codigo"] for aviso in resultado.avisos])
        self._trazar(traza, arranque)
        return resultado.model_dump()

    def _trazar(self, traza: dict[str, Any], arranque: float) -> None:
        traza["duracion_ms"] = round((self._reloj() - arranque) * 1000, 1)
        logger.info(json.dumps(traza, ensure_ascii=False, default=str))

    def _prefijo_de(self, referencia: str) -> str | None:
        for prefijo in self._settings.sigrid_factura_prefijos_referencia:
            if referencia.startswith(prefijo):
                return prefijo
        return None

    def _ejecutar(self, request: FacturaRequest, traza: dict[str, Any]) -> FacturaResultado:
        # 1. Llaves, prefijo y tope de lineas, sin leer la base (R4-R6, R8).
        self._comprobar_guardas(request)
        fs = FacturaStatements(database=request.database)
        f9 = AlbaranCompraStatements(database=request.database)
        leer = self._lector(request)

        # 2. `usu` y estados (R7, R9).
        if not leer(f9.leer_usuario(request.usu)):
            raise FacturaError(f"El usuario '{request.usu}' no existe en dbo.usu.",
                               codigo="usuario_no_valido")
        estados = self._estados(request, leer(fs.leer_estados()))

        # 3. Idempotencia (R43) antes que nada que la peticion repetida cambie.
        idempotente = self._idempotencia(request, leer(fs.buscar_referencia(request.referencia_externa)),
                                         leer, fs)
        if idempotente is not None:
            return idempotente

        # 4. Instante unico de la peticion (fuera de la transaccion) y serie (R9, R37).
        sellos = sellos_del_alta(self._ahora_utc(), None)
        prefijo, cifras = prefijo_y_cifras(request.serie, sellos.fec)

        # 5. Obra, origenes y proveedor (R10-R14, R18).
        obra = self._obra_pedida(request, leer, f9) if request.cod_obra else None
        origenes = self._origenes(request, leer, fs, obra, estados) if request.origenes else []
        if obra is None:
            obra = self._obra_de_los_origenes(request, leer, f9, origenes)
        proveedor = self._proveedor(request, leer, fs, f9, obra, origenes)
        heredadas, ctride = self._cabecera(request, leer, fs, obra, proveedor, origenes)
        retencion = self._retencion(request, leer, fs, origenes) if origenes else None

        # 6. Lineas de origen y `a_origen` (R15-R22).
        lineas_origen: list[tuple[dict[str, Any], dict[str, Any]]] = []
        if origenes:
            lineas_origen = self._lineas_de_origen(
                request, proveedor, origenes, *self._leer_lineas(leer, fs, origenes, request.modo)
            )
        traza["n_lineas_origen"] = len(lineas_origen)

        # 7. Lineas sin origen, todos sus fallos juntos (R23-R28).
        sin_origen = self._sin_origen(request, leer, fs, f9, obra, heredadas)

        contexto = _Contexto(
            request=request, sellos=sellos, prefijo=prefijo, cifras=cifras, estados=estados,
            obra=obra, proveedor=proveedor, origenes=origenes, heredadas=heredadas, ctride=ctride,
            retencion=retencion, sin_origen=sin_origen,
        )
        # 8-9. Totales, retencion y vencimientos (R29-R35).
        montada = self._montar(contexto, lineas_origen)
        # 10. Duplicadas (R43).
        self._duplicadas(contexto, leer(fs.buscar_duplicadas(
            _cif(heredadas["entcif"]), request.numero_factura, contexto.est_rech
        )))
        if request.commit:
            return self._escribir(contexto, fs, f9, traza)
        return self._previa(contexto, montada, leer, fs)

    # ------------------------------------------------------------------ #
    # Guardas sin leer la base (R4-R6, R8)
    # ------------------------------------------------------------------ #
    def _comprobar_guardas(self, request: FacturaRequest) -> None:
        settings = self._settings
        tope = settings.sigrid_factura_max_lineas
        if len(request.lineas) > tope:
            raise FacturaError(
                f"La factura trae {len(request.lineas)} lineas sin origen y el tope es {tope}.",
                codigo="demasiadas_lineas",
            )
        if self._prefijo_de(request.referencia_externa) is None:
            raise FacturaError(
                "La referencia externa no empieza por ningun prefijo admitido "
                "(SIGRID_FACTURA_PREFIJOS_REFERENCIA).",
                codigo="referencia_no_permitida",
            )
        if not request.commit:
            return
        if not (
            settings.sigrid_domain_write_enabled
            and settings.sigrid_factura_write_enabled
            and settings.sql_server_write_username
            and settings.sql_server_write_password
        ):
            raise FacturaError(
                "Escritura de facturas desactivada: hacen falta SIGRID_DOMAIN_WRITE_ENABLED, "
                "SIGRID_FACTURA_WRITE_ENABLED y credenciales de escritura.",
                codigo="escritura_facturas_deshabilitada",
            )
        # Una lista VACIA no abre.
        if request.database not in settings.allowed_write_databases:
            raise FacturaError(
                f"La base '{request.database}' no esta permitida para escritura.",
                codigo="base_de_datos_no_permitida",
            )

    # ------------------------------------------------------------------ #
    # Lecturas (credenciales de lectura)
    # ------------------------------------------------------------------ #
    def _lector(self, request: FacturaRequest) -> Lector:
        def leer(sentencia: tuple[str, list[Any]]) -> list[tuple[Any, ...]]:
            sql, params = sentencia
            _columnas, filas, truncado = self._repo.execute_read_query(
                SqlReadRequest.model_construct(
                    database=request.database, sql=sql, parameters=params,
                    max_rows=self._settings.max_allowed_rows,
                )
            )
            if truncado:
                raise ValueError(
                    "Una lectura devolvio mas filas de las que se pueden traer (truncada): no se "
                    "da de alta la factura."
                )
            return [tuple(fila) for fila in filas]

        return leer

    def _estados(self, request: FacturaRequest, filas: Sequence[Sequence[Any]]) -> dict[tuple[int, str], int]:
        """R9, R14, R41, R43: los `conest` por `(tip, cod)`."""
        estados = {(_entero(f[0]), str(f[2] or "").strip().upper()): _entero(f[1]) for f in filas}
        # Toda factura lleva al menos un vencimiento (R32): el PDT de los pagos, siempre.
        necesarios = [(TIP_FACTURA, ESTADO_INICIAL[request.serie]), (TIP_FACTURA, RECH), (TIP_PAGO, PDT)]
        if request.origenes:
            necesarios += [(TIP_ALBARAN, CON), (TIP_ALBARAN, FAC)]
        faltan = [f"{tip} {cod}" for tip, cod in necesarios if (tip, cod) not in estados]
        if faltan:
            raise FacturaError(
                f"No estan en dbo.conest los estados {', '.join(faltan)}.",
                codigo="estado_inicial_no_encontrado",
            )
        return estados

    def _idempotencia(
        self, request: FacturaRequest, filas: Sequence[Sequence[Any]], leer: Lector, fs: FacturaStatements
    ) -> FacturaResultado | None:
        """R43: la referencia ya registrada con el mismo proveedor (por CIF) y
        numero es `idempotente`; con otros datos, `referencia_en_conflicto`."""
        if not filas:
            return None
        fila = filas[0]
        proveedor = leer(fs.leer_proveedor(_entero(fila[2])))
        mismo_cif = bool(proveedor) and _cif(proveedor[0][3]) == _cif(request.cif_proveedor)
        if len(filas) > 1 or not mismo_cif or str(fila[3] or "").strip() != request.numero_factura:
            raise FacturaError(
                "La referencia externa ya esta registrada con otro proveedor o numero de factura.",
                codigo="referencia_en_conflicto",
                details={"cod": str(fila[1] or "").strip()},
            )
        return _resultado_idempotente(request, fila)

    # ------------------------------------------------------------------ #
    # Obra, origenes y proveedor (R10-R14, R18)
    # ------------------------------------------------------------------ #
    def _obra_pedida(self, request: FacturaRequest, leer: Lector, f9: AlbaranCompraStatements) -> _Obra:
        """R11: `cod_obra` en UNA de las empresas de `SIGRID_ALBARAN_EMPRESAS_OBRA`."""
        empresas = self._settings.sigrid_albaran_empresas_obra
        filas = [f for f in leer(f9.leer_obra(str(request.cod_obra))) if _entero(f[1]) in empresas]
        if len(filas) != 1:
            raise FacturaError(
                f"La obra '{request.cod_obra}' no existe en una sola de las empresas admitidas "
                f"({len(filas)}).",
                codigo="obra_no_encontrada",
            )
        ide, emp, cod = filas[0]
        return self._con_almacen(leer, f9, int(ide), int(emp), str(cod).strip())

    def _con_almacen(self, leer: Lector, f9: AlbaranCompraStatements, ide: int, emp: int, cod: str) -> _Obra:
        ficha = leer(f9.leer_almacen_de_obra(ide))
        almide, cenide = (ficha[0][0], ficha[0][1]) if ficha else (0, 0)
        return _Obra(ide=ide, emp=emp, cod=cod, cenide=_entero(cenide), almide=_entero(almide))

    def _obra_de_los_origenes(
        self, request: FacturaRequest, leer: Lector, f9: AlbaranCompraStatements,
        origenes: Sequence[dict[str, Any]],
    ) -> _Obra:
        obride = _entero(origenes[0]["obride"])
        leida = self._repo.read_full_row(database=request.database, table="con", ide=obride)
        if leida is None:
            raise FacturaError(f"La obra de los origenes (ide {obride}) no existe.",
                               codigo="obra_no_encontrada")
        con = dict(zip(*leida))
        return self._con_almacen(leer, f9, obride, _entero(con["emp"]), str(con["cod"]).strip())

    def _origenes(
        self, request: FacturaRequest, leer: Lector, fs: FacturaStatements, obra: _Obra | None,
        estados: Mapping[tuple[int, str], int],
    ) -> list[dict[str, Any]]:
        """R13, R14, R18: cada codigo, un `tip 14` de la empresa (la de la obra o
        una admitida), del mismo proveedor, obra y contrato, contabilizado y del
        modo pedido. En el orden de la peticion."""
        empresas = [obra.emp] if obra else list(self._settings.sigrid_albaran_empresas_obra)
        filas = [dict(zip(ORIGEN, f)) for f in leer(fs.leer_origenes(request.origenes))]
        por_cod = {}
        for fila in filas:
            if _entero(fila["emp"]) in empresas:
                por_cod.setdefault(clave(fila["cod"]), []).append(fila)
        origenes: list[dict[str, Any]] = []
        for cod in request.origenes:
            candidatos = por_cod.get(clave(cod), [])
            if len(candidatos) != 1:
                raise FacturaError(
                    f"El origen '{cod}' no es un albaran o proforma de la empresa de la obra"
                    + (" (esta en varias empresas: indica cod_obra)." if candidatos else "."),
                    codigo="origen_no_encontrado",
                    details={"origen": cod},
                )
            origenes.append(candidatos[0])
        if len({_entero(o["emp"]) for o in origenes}) > 1 or len({_entero(o["obride"]) for o in origenes}) > 1 \
                or (obra is not None and _entero(origenes[0]["obride"]) != obra.ide):
            raise FacturaError("Los origenes no son todos de la misma obra (o no de cod_obra).",
                               codigo="varias_obras")
        if len({_entero(o["ctride"]) for o in origenes}) > 1:
            raise FacturaError("Los origenes son de mas de un contrato.", codigo="varios_contratos")
        if len({_entero(o["entide"]) for o in origenes}) > 1:
            raise FacturaError("Los origenes son de mas de un proveedor.",
                               codigo="origen_de_otro_proveedor")
        self._comprobar_contabilizados(origenes, estados, leer(fs.leer_asientos(
            _entero(origenes[0]["emp"]), [str(o["cod"]) for o in origenes]
        )))
        modos = {_entero(o["docoritip"]) for o in origenes}
        if len(modos) > 1:
            raise FacturaError("Los origenes mezclan albaranes de mes y a origen.",
                               codigo="origenes_de_modos_distintos")
        if modos != {DOCORITIP_DE_MODO[request.modo]}:
            raise FacturaError(f"Los origenes no son del modo '{request.modo}'.",
                               codigo="modo_no_coincide_con_origen")
        return origenes

    @staticmethod
    def _comprobar_contabilizados(
        origenes: Sequence[Mapping[str, Any]], estados: Mapping[tuple[int, str], int],
        asientos: Sequence[Sequence[Any]],
    ) -> None:
        """R14 (P4): en CON y con su asiento `tip 20` del mismo `cod`."""
        con_asiento = {clave(f[0]) for f in asientos}
        for origen in origenes:
            if (
                _entero(origen["est"]) != estados[(TIP_ALBARAN, CON)]
                or clave(origen["cod"]) not in con_asiento
            ):
                raise FacturaError(
                    f"El origen '{origen['cod']}' no esta contabilizado (CON y con asiento).",
                    codigo="origen_sin_contabilizar",
                    details={"origen": str(origen["cod"]).strip()},
                )

    def _proveedor(
        self, request: FacturaRequest, leer: Lector, fs: FacturaStatements,
        f9: AlbaranCompraStatements, obra: _Obra, origenes: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        """R10, R12, R13: el de los origenes (y su CIF el pedido) o, sin ellos, el
        UNICO `prv` vivo con el CIF en la empresa de la obra."""
        if origenes:
            entide = _entero(origenes[0]["entide"])
        else:
            filas = leer(f9.leer_proveedor_por_cif(obra.emp, request.cif_proveedor))
            if not filas:
                raise FacturaError("Ningun proveedor vivo con ese CIF en la empresa de la obra.",
                                   codigo="proveedor_no_encontrado")
            if len(filas) > 1:
                raise FacturaError(
                    f"Hay {len(filas)} proveedores vivos con ese CIF en la empresa de la obra.",
                    codigo="proveedor_ambiguo",
                )
            entide = _entero(filas[0][0])
        leidas = leer(fs.leer_proveedor(entide))
        if not leidas:
            raise FacturaError("El proveedor no existe en dbo.prv.", codigo="proveedor_no_encontrado")
        proveedor = dict(zip(PROVEEDOR, leidas[0]))
        if origenes and _cif(proveedor["cif"]) != _cif(request.cif_proveedor):
            raise FacturaError("Los origenes son de otro proveedor que el del CIF.",
                               codigo="origen_de_otro_proveedor")
        if not _entero(proveedor["cueide"]) or (origenes and not _entero(proveedor["cuepdtide"])):
            raise FacturaError(
                "El proveedor no tiene la cuenta que hace falta (cueide, o cuepdtide con origenes).",
                codigo="proveedor_sin_cuenta",
            )
        return proveedor

    def _cabecera(
        self, request: FacturaRequest, leer: Lector, fs: FacturaStatements, obra: _Obra,
        proveedor: Mapping[str, Any], origenes: Sequence[dict[str, Any]],
    ) -> tuple[dict[str, Any], int]:
        """design §6: con origenes, la `dca` del primero por `cod` (M57) y su
        contrato; sin ellos, el proveedor, su `auxpag` y la obra (M61, M67)."""
        if origenes:
            primero = min(origenes, key=lambda o: str(o["cod"]))
            filas = leer(fs.leer_cabecera_de_origen(_entero(primero["ide"])))
            if not filas:
                raise ValueError(f"No se pudo leer la cabecera del origen ide={primero['ide']}.")
            return dict(zip(CABECERA_DE_ORIGEN, filas[0])), _entero(primero["ctride"])
        pagtex, pagfor = "", ""
        if _entero(proveedor["pagide"]):
            auxpag = leer(fs.leer_auxpag(_entero(proveedor["pagide"])))
            if auxpag:
                pagtex, pagfor = auxpag[0][0] or "", auxpag[0][1] or ""
        heredadas = {
            "entide": proveedor["ide"], "entcod": str(proveedor["cod"] or "").strip(),
            "entres": proveedor["raz"], "entcif": proveedor["cif"], "entciftip": proveedor["tipcif"],
            "entcifpai": proveedor["cifpai"], "obride": obra.ide, "cenide": obra.cenide,
            "almide": obra.almide, "empide": 0, "pagide": proveedor["pagide"], "pagtex": pagtex,
            "pagfor": pagfor,
            **{c: proveedor[c] for c in ("efeide", "eioide", "banban", "bansuc", "bandig", "bancue",
                                         "ban", "bantipide")},
        }
        return heredadas, 0

    def _retencion(
        self, request: FacturaRequest, leer: Lector, fs: FacturaStatements,
        origenes: Sequence[dict[str, Any]],
    ) -> dict[str, Any] | None:
        """R31: UNA retencion igual en todos los origenes o ninguna. Lo que no se
        sabe copiar (mas de una, distintas, unos con y otros sin, importe fijo,
        IVA o sin porcentaje) es `retencion_no_soportada`."""
        filas = [dict(zip(RETENCION_DE_ORIGEN, f))
                 for f in leer(fs.leer_retenciones([_entero(o["ide"]) for o in origenes]))]
        if not filas:
            return None
        por_origen: dict[int, list[dict[str, Any]]] = {}
        for fila in filas:
            por_origen.setdefault(_entero(fila["docide"]), []).append(fila)
        firmas = {
            (_entero(f["recide"]), _d(f["valpor"]) if f["valpor"] is not None else None,
             _entero(f["reccla"]), _entero(f["cueide"]))
            for f in filas
        }
        if (
            len(por_origen) != len(origenes)
            or any(len(v) > 1 for v in por_origen.values())
            or len(firmas) > 1
            or any(f["valpor"] is None or _d(f["valfij"]) or _entero(f["ivaide"]) for f in filas)
        ):
            raise FacturaError(
                "La retencion de los origenes no se sabe copiar (mas de una, distintas, solo en "
                "algunos, importe fijo o con IVA): alta a mano.",
                codigo="retencion_no_soportada",
            )
        return filas[0]

    # ------------------------------------------------------------------ #
    # Lineas de origen (R15-R22): fuera y otra vez dentro de la transaccion
    # ------------------------------------------------------------------ #
    @staticmethod
    def _leer_lineas(
        leer: Lector, fs: FacturaStatements, origenes: Sequence[dict[str, Any]], modo: str,
        *, bloquear: bool = False,
    ) -> tuple[list[dict[str, Any]], set[int], dict[int, dict[str, Any]]]:
        docides = [_entero(o["ide"]) for o in origenes]
        sentencia = fs.bloquear_lineas_de_origenes(docides) if bloquear else fs.leer_lineas_de_origenes(docides)
        lineas = [dict(zip(LINEA_DE_ORIGEN, f)) for f in leer(sentencia)]
        facturadas = {_entero(f[0]) for f in leer(fs.leer_facturadas(docides))}
        anteriores: dict[int, dict[str, Any]] = {}
        enlazadas = sorted({_entero(l["canorilin"]) for l in lineas if _entero(l["canorilin"])})
        if modo == "origen" and enlazadas:
            anteriores = {
                _entero(f[0]): {"canoriori": f[1], "imporiori": f[2]}
                for f in leer(fs.leer_anteriores(enlazadas))
            }
        return lineas, facturadas, anteriores

    @staticmethod
    def _lineas_de_origen(
        request: FacturaRequest, proveedor: Mapping[str, Any], origenes: Sequence[dict[str, Any]],
        lineas: Sequence[dict[str, Any]], facturadas: set[int], anteriores: Mapping[int, dict[str, Any]],
    ) -> list[tuple[dict[str, Any], dict[str, Any]]]:
        """R15-R17, R19-R22: TODAS las de `can` != 0 de cada origen, en el orden
        de `origenes` y `pos`; ninguna ya facturada; a origen, comparadas."""
        por_origen: dict[int, list[dict[str, Any]]] = {}
        for fila in lineas:
            por_origen.setdefault(_entero(fila["docide"]), []).append(fila)
        resultado: list[tuple[dict[str, Any], dict[str, Any]]] = []
        ya: list[int] = []
        for origen in origenes:
            for dcapro in por_origen.get(_entero(origen["ide"]), []):
                if not float(dcapro["can"] or 0):
                    continue
                if float(dcapro["canfac"] or 0) or _entero(dcapro["ide"]) in facturadas:
                    ya.append(_entero(dcapro["ide"]))
                    continue
                anterior = anteriores.get(_entero(dcapro["canorilin"])) if request.modo == "origen" else None
                resultado.append((dcapro, linea_de_origen(
                    dcapro, anterior, modo=request.modo, cueide=_entero(proveedor["cuepdtide"]),
                    docoricod=str(origen["cod"]).strip(),
                )))
        if ya:
            raise FacturaError(f"{len(ya)} linea(s) de los origenes ya estan facturadas.",
                               codigo="origen_ya_facturado", details={"lineas": ya})
        if request.modo == "origen":
            comparar_a_origen([fila for _d, fila in resultado], request.a_origen)
        return resultado

    # ------------------------------------------------------------------ #
    # Lineas sin origen (R23-R28)
    # ------------------------------------------------------------------ #
    def _sin_origen(
        self, request: FacturaRequest, leer: Lector, fs: FacturaStatements,
        f9: AlbaranCompraStatements, obra: _Obra, heredadas: Mapping[str, Any],
    ) -> list[dict[str, Any]]:
        if not request.lineas:
            return []
        settings, emp = self._settings, obra.emp
        ivas = {
            clave(f[1]): (_entero(f[0]), float(f[2] or 0))
            for f in leer(fs.leer_ivas(emp, _unicos([l.iva for l in request.lineas])))
        }
        comunes = {"ivas": ivas, "ivas_permitidos": settings.sigrid_factura_ivas}
        if request.serie == "FRGG":
            lecturas = self._lecturas_gg(request, leer, fs, emp, comunes)
            resolver = resolver_linea_gg
        else:
            lecturas = self._lecturas_fr(request, leer, f9, obra, comunes)
            resolver = resolver_linea_fr
        fallos: list[FalloLineaFactura] = []
        filas: list[dict[str, Any]] = []
        for indice, linea in enumerate(request.lineas):
            resuelta, errores = resolver(linea, lecturas)
            if errores:
                fallos.extend(FalloLineaFactura(indice=indice, codigo=c, mensaje=m) for c, m in errores)
                continue
            assert resuelta is not None
            filas.append(linea_sin_origen(linea, resuelta, serie=request.serie,
                                          almide=_entero(heredadas["almide"])))
        if fallos:
            raise FacturaError(
                f"{len({f.indice for f in fallos})} linea(s) sin origen no validas: no se ha escrito nada.",
                codigo="lineas_no_validas",
                details={"lineas": [f.model_dump() for f in fallos]},
            )
        return filas

    def _lecturas_gg(
        self, request: FacturaRequest, leer: Lector, fs: FacturaStatements, emp: int,
        comunes: Mapping[str, Any],
    ) -> LecturasLineas:
        """R26: cuentas, analiticas y las obras de sus prefijos, de la empresa."""
        cuentas = _unicos([str(l.cuenta) for l in request.lineas])
        analiticas = _unicos([str(l.analitica) for l in request.lineas])
        prefijos = _unicos([a.split(".")[0] for a in analiticas if "." in a and a.split(".")[0]])
        return LecturasLineas(
            **comunes,
            cuentas={clave(f[1]): (_entero(f[0]), _entero(f[2])) for f in leer(fs.leer_cuentas_gasto(emp, cuentas))},
            prefijos_cuenta=self._settings.sigrid_factura_cuentas_gasto_prefijos,
            analiticas={clave(f[1]): (_entero(f[0]), bool(_entero(f[2])))
                        for f in leer(fs.leer_analiticas_gasto(emp, analiticas))},
            obras=({clave(f[1]): (_entero(f[0]), _entero(f[2])) for f in leer(fs.leer_obras(emp, prefijos))}
                   if prefijos else {}),
        )

    def _lecturas_fr(
        self, request: FacturaRequest, leer: Lector, f9: AlbaranCompraStatements, obra: _Obra,
        comunes: Mapping[str, Any],
    ) -> LecturasLineas:
        """R25: producto, naturaleza, cuenta, analitica, partida y almacen con
        las lecturas y reglas de F-009."""
        almacen = self._almacen(leer, f9, obra)
        productos = _unicos([str(l.producto) for l in request.lineas])
        mapa = self._settings.sigrid_factura_naturaleza_por_producto
        mapeados = {p: mapa[p] for p in productos if p in mapa}
        naturalezas: dict[str, tuple[int, int, int] | str] = {}
        if mapeados:
            validas = naturalezas_validas(
                mapeados, _agrupar(leer(f9.leer_naturalezas(_unicos(list(mapeados.values()))))),
                emp=obra.emp,
            )
            cuacomcods = _unicos([str(f[5]).strip() for f in validas.values()])
            cuentas = _agrupar(leer(f9.leer_cuentas(obra.emp, cuacomcods))) if cuacomcods else {}
            con_cuenta = naturalezas_con_cuenta(validas, cuentas)
            codigos = _unicos([c for c in (codigo_analitica(obra.cod, f[4]) for f, _c in con_cuenta.values()) if c])
            analiticas = _agrupar(leer(f9.leer_analiticas(codigos))) if codigos else {}
            naturalezas = naturalezas_resueltas(productos, con_cuenta, analiticas, cod_obra=obra.cod,
                                                centro=almacen[1])
        partidas = _unicos([str(l.partida) for l in request.lineas if l.partida is not None])
        return LecturasLineas(
            **comunes,
            productos_permitidos=self._settings.sigrid_factura_productos_sin_origen,
            productos=_agrupar(leer(f9.leer_productos(obra.emp, productos))),
            naturalezas=naturalezas,
            partidas=_agrupar(leer(f9.leer_partidas(obra.ide, partidas))) if partidas else {},
            obride=obra.ide,
            almacen=almacen,
        )

    @staticmethod
    def _almacen(leer: Lector, f9: AlbaranCompraStatements, obra: _Obra) -> tuple[int, int]:
        """F-009 R15 sin contrato: el de la ficha de la obra o su UNICO `alm`."""
        if obra.almide:
            return obra.almide, obra.cenide
        almacenes = leer(f9.leer_almacenes(obra.ide, []))
        if len(almacenes) != 1:
            raise FacturaError(
                f"La obra no tiene almacen en su ficha y tiene {len(almacenes)} almacenes: no se puede "
                "decidir el de las lineas sin origen.",
                codigo="almacen_de_obra_no_resuelto",
            )
        return _entero(almacenes[0][0]), _entero(almacenes[0][2])

    # ------------------------------------------------------------------ #
    # Totales, retencion, vencimientos y filas (R29-R35, R38)
    # ------------------------------------------------------------------ #
    def _montar(
        self, ctx: _Contexto, lineas_origen: list[tuple[dict[str, Any], dict[str, Any]]]
    ) -> _Montada:
        """Pura: se repite tal cual dentro de la transaccion con las lineas
        releidas bajo bloqueo."""
        request = ctx.request
        dcfpro = [fila for _d, fila in lineas_origen] + ctx.sin_origen
        tope = self._settings.sigrid_factura_max_lineas
        if len(dcfpro) > tope:
            raise FacturaError(f"La factura tendria {len(dcfpro)} lineas y el tope es {tope}.",
                               codigo="demasiadas_lineas")
        if request.total_base <= 0:
            raise FacturaError("Una factura con base no positiva es un abono: alta a mano.",
                               codigo="abono_no_soportado")
        # La base de la retencion es la de las lineas: no depende de la retencion.
        totbas = sum((_d(f["tot"]) for f in dcfpro), Decimal(0))
        dcfrec = construir_dcfrec(ctx.retencion, totbas=totbas) if ctx.retencion else None
        cuo = _d(dcfrec["cuo"]) if dcfrec else Decimal(0)
        totales = totales_factura(dcfpro, cuo=cuo)
        self._comprobar_totales(request, totales)
        validar_vencimientos(request.vencimientos, fecha_factura=request.fecha_factura,
                             totpag=_d(totales["totpag"]))
        garantia = bool(ctx.retencion) and _entero(ctx.retencion["reccla"]) == RECCLA_GARANTIA
        vence = request.vencimiento_retencion
        if (garantia and (vence is None or not fecha_de_vencimiento_valida(vence, fecha_factura=request.fecha_factura))) \
                or (not garantia and vence is not None):
            raise FacturaError(
                "vencimiento_retencion va solo, y es obligatorio, con una retencion de garantia "
                "(reccla 5), con fecha real entre la de la factura y 730 dias despues.",
                codigo="vencimiento_retencion_no_valido",
            )
        return _Montada(
            lineas_origen=lineas_origen,
            filas=self._filas(ctx, lineas_origen, dcfpro, totales, dcfrec, garantia),
            totales=totales,
            dcfrec=dcfrec,
        )

    @staticmethod
    def _comprobar_totales(request: FacturaRequest, totales: Mapping[str, float]) -> None:
        """R30: los del llamante contra los calculados, sin ajustar nada."""
        calculado = {"total_base": totales["totbas"], "total_iva": totales["totiva"],
                     "total_factura": totales["tot"]}
        enviado = {"total_base": request.total_base, "total_iva": request.total_iva,
                   "total_factura": request.total_factura}
        tolerancias = {"total_base": TOLERANCIA_BASE, "total_iva": TOLERANCIA_IVA,
                       "total_factura": TOLERANCIA_FACTURA}
        if any(abs(_d(enviado[c]) - _d(calculado[c])) > tolerancias[c] for c in calculado):
            raise FacturaError(
                "Los totales de la factura no cuadran con sus lineas: no se ha ajustado nada.",
                codigo="totales_no_cuadran",
                details={"calculado": calculado, "enviado": enviado},
            )

    @staticmethod
    def _filas(
        ctx: _Contexto, lineas_origen: Sequence[tuple[dict[str, Any], dict[str, Any]]],
        dcfpro: list[dict[str, Any]], totales: Mapping[str, float], dcfrec: dict[str, Any] | None,
        garantia: bool,
    ) -> FilasFactura:
        request, sellos, emp = ctx.request, ctx.sellos, ctx.obra.emp
        con = construir_con_factura(emp=emp, fec=sellos.fec, entres=ctx.heredadas.get("entres"),
                                    entref=request.numero_factura, est=ctx.est_inicial,
                                    tiemod=sellos.tiemod)
        dcf = construir_dcf(heredadas=ctx.heredadas, cueide=_entero(ctx.proveedor["cueide"]),
                            ctride=ctx.ctride, fecdoc=request.fecha_factura, hor=sellos.hor,
                            entref=request.numero_factura, synckey=request.referencia_externa,
                            totales=totales)
        plazos = [(0, v.importe, v.fecha, _entero(dcf["cueide"]), 0) for v in request.vencimientos]
        if garantia and dcfrec is not None:
            # `_montar` ya exige `vencimiento_retencion` con garantia (R34).
            assert request.vencimiento_retencion is not None
            plazos.append((2, dcfrec["cuo"], request.vencimiento_retencion,
                           _entero(dcfrec["cueide"]), _entero(dcfrec["recide"])))
        pagos = [
            (
                construir_con_pago(emp=emp, fec=sellos.fec, res=con["res"], indice=i, de=len(plazos),
                                   est=ctx.est_pago, tiemod=sellos.tiemod),
                construir_pag(cla=cla, tot=tot, fecven=fecven, dcf=dcf, cueide=cueide, retide=retide),
            )
            for i, (cla, tot, fecven, cueide, retide) in enumerate(plazos, start=1)
        ]
        return FilasFactura(
            con=con, dcf=dcf, dcfpro=dcfpro, dcfrec=[dcfrec] if dcfrec else [], pagos=pagos,
            consii=construir_consii(desope=con["res"]),
            dcaprodes=[
                (i, construir_dcaprodes(docproide=_entero(d["ide"]), can=d["can"]))
                for i, (d, _f) in enumerate(lineas_origen)
            ],
            log=construir_log_factura(emp=emp, usu=request.usu, res=con["res"], sellos=sellos),
        )

    @staticmethod
    def _duplicadas(ctx: _Contexto, filas: Sequence[Sequence[Any]]) -> None:
        """R43: otra factura del mismo CIF y numero fuera de RECH."""
        if filas:
            raise FacturaError(
                "Ya hay una factura de ese proveedor con ese numero (fuera de RECH).",
                codigo="factura_ya_registrada",
                details={"cod": str(filas[0][1] or "").strip()},
            )

    # ------------------------------------------------------------------ #
    # Commit (R36-R45, design §7)
    # ------------------------------------------------------------------ #
    def _escribir(
        self, ctx: _Contexto, fs: FacturaStatements, f9: AlbaranCompraStatements, traza: dict[str, Any]
    ) -> FacturaResultado:
        request, settings = ctx.request, self._settings
        timeout = settings.default_write_timeout_seconds

        def work(cursor: Any) -> FacturaResultado:
            # Reentrante: el repositorio repite `work` entero ante una clave
            # duplicada (R37). Cada intento relee, reserva y numera desde cero;
            # el instante de la peticion ya viene fijado en `ctx.sellos`.
            cursor.connection.timeout = timeout

            def leer(sentencia: tuple[str, list[Any]]) -> list[tuple[Any, ...]]:
                _ejecutar_sql(cursor, sentencia)
                return [tuple(fila) for fila in cursor.fetchall()]

            # (1) R43 otra vez, bajo el applock de referencias.
            idempotente = self._idempotencia(
                request, leer(fs.buscar_referencia(request.referencia_externa)), leer, fs
            )
            if idempotente is not None:
                return idempotente
            self._duplicadas(ctx, leer(fs.buscar_duplicadas(
                _cif(ctx.heredadas["entcif"]), request.numero_factura, ctx.est_rech
            )))
            # (2) R14, R15, R22 y R29-R34 otra vez con los origenes bloqueados: el
            # escritorio no toma nuestros applocks. Sin origenes, nada que bloquear.
            lineas_origen: list[tuple[dict[str, Any], dict[str, Any]]] = []
            if ctx.origenes:
                self._bloquear_origenes(ctx, leer, fs)
                lineas_origen = self._lineas_de_origen(
                    request, ctx.proveedor, ctx.origenes,
                    *self._leer_lineas(leer, fs, ctx.origenes, request.modo, bloquear=True),
                )
            traza["n_lineas_origen"] = len(lineas_origen)
            montada = self._montar(ctx, lineas_origen)
            # (3) Reservas bajo UPDLOCK, HOLDLOCK (`pag` comparte `ide` con su `con`).
            maximo = leer(fs.reservar_cod(ctx.obra.emp, ctx.prefijo, ctx.cifras))
            cod = siguiente_cod(ctx.prefijo, maximo[0][0] if maximo else None, cifras=ctx.cifras)
            filas = montada.filas
            numeradas = numerar(
                filas, cod=cod, ide_con=_contar(cursor, fs.reservar_ide_con()),
                ide_dcfpro=_contar(cursor, fs.reservar_ide_dcfpro()),
                ide_dcfrec=_contar(cursor, fs.reservar_ide_dcfrec()) if filas.dcfrec else None,
                ide_consii=_contar(cursor, fs.reservar_ide_consii()),
                ide_dcaprodes=_contar(cursor, fs.reservar_ide_dcaprodes()) if filas.dcaprodes else None,
                ide_log=None,
            )
            # (4) INSERTs por lista blanca (R36, R38).
            _ejecutar_sql(cursor, fs.insertar_con(numeradas.con))
            _ejecutar_sql(cursor, fs.insertar_dcf(numeradas.dcf))
            for fila in numeradas.dcfpro:
                _ejecutar_sql(cursor, fs.insertar_dcfpro(fila))
            for fila in numeradas.dcfrec:
                _ejecutar_sql(cursor, fs.insertar_dcfrec(fila))
            for con_pago, pag in numeradas.pagos:
                _ejecutar_sql(cursor, fs.insertar_con(con_pago))
                _ejecutar_sql(cursor, fs.insertar_pag(pag))
            _ejecutar_sql(cursor, fs.insertar_consii(numeradas.consii))
            for _i, fila in numeradas.dcaprodes:
                _ejecutar_sql(cursor, fs.insertar_dcaprodes(fila))
            # (5) Marcas en los origenes (R40-R42), solo con origenes.
            marcas = self._marcar(ctx, cursor, leer, fs, f9, lineas_origen) if ctx.origenes else []
            # El `log`, al final (F-006): su `ide` se reserva aqui.
            numeradas = replace(numeradas, log={**numeradas.log,
                                                "ide": _contar(cursor, fs.reservar_ide_log())})
            _ejecutar_sql(cursor, fs.insertar_log(numeradas.log))
            # (6) Relectura antes del COMMIT (R45).
            self._releer(ctx, cursor, fs, numeradas, marcas)
            return _resultado(ctx, montada, numeradas, estado="creado", avisos=[])

        try:
            return self._repo.run_in_write_transaction(
                database=request.database,
                timeout_seconds=timeout,
                applock_resources=list(APPLOCKS_FACTURA),
                applock_timeout_ms=settings.applock_timeout_ms,
                max_retries=settings.domain_write_max_retries,
                work=work,
            )
        except Exception as exc:
            if _es_colision_de_clave(exc):
                raise FacturaError(
                    "Colision de clave repetida tras los reintentos (alta simultanea con el "
                    "escritorio): no se ha escrito nada. Reenviala.",
                    codigo="colision_de_clave",
                ) from exc
            raise

    def _bloquear_origenes(self, ctx: _Contexto, leer: Lector, fs: FacturaStatements) -> None:
        """R13-R14 bajo `UPDLOCK, HOLDLOCK`: siguen ahi, igual, en CON y con asiento."""
        bloqueados = {
            _entero(f[0]): dict(zip(ORIGEN, f))
            for f in leer(fs.bloquear_origenes([_entero(o["ide"]) for o in ctx.origenes]))
        }
        for origen in ctx.origenes:
            actual = bloqueados.get(_entero(origen["ide"]))
            if actual is None or any(
                _entero(actual[c]) != _entero(origen[c]) for c in ("emp", "entide", "obride", "ctride", "docoritip")
            ):
                raise FacturaError(
                    f"El origen '{origen['cod']}' ha cambiado o ya no existe: no se ha escrito nada.",
                    codigo="origen_no_encontrado",
                    details={"origen": str(origen["cod"]).strip()},
                )
        self._comprobar_contabilizados(
            [bloqueados[_entero(o["ide"])] for o in ctx.origenes], ctx.estados,
            leer(fs.leer_asientos(ctx.obra.emp, [str(o["cod"]) for o in ctx.origenes])),
        )

    def _marcar(
        self, ctx: _Contexto, cursor: Any, leer: Lector, fs: FacturaStatements,
        f9: AlbaranCompraStatements, lineas_origen: Sequence[tuple[dict[str, Any], dict[str, Any]]],
    ) -> list[tuple[tuple[str, list[Any]], str]]:
        """R40-R42. Devuelve las relecturas de cada marca y el fallo si no da 1."""
        sellos, relecturas = ctx.sellos, []
        for dcapro, _fila in lineas_origen:
            _ejecutar_sql(cursor, fs.marcar_linea(_entero(dcapro["ide"]), dcapro["can"]))
            relecturas.append((fs.releer_linea_marcada(_entero(dcapro["ide"]), dcapro["can"]),
                               "origen_ya_facturado"))
        est_con, est_fac = ctx.estados[(TIP_ALBARAN, CON)], ctx.estados[(TIP_ALBARAN, FAC)]
        for origen in ctx.origenes:
            ide = _entero(origen["ide"])
            _ejecutar_sql(cursor, fs.marcar_cabecera(ide, sellos.fec_alta, sellos.hor))
            _ejecutar_sql(cursor, fs.marcar_estado(ide, est_con=est_con, est_fac=est_fac))
            relecturas.append((fs.releer_cabecera_marcada(ide, sellos.fec_alta, sellos.hor),
                               "filas_afectadas_inesperadas"))
            relecturas.append((fs.releer_estado(ide, est_fac=est_fac), "filas_afectadas_inesperadas"))
        vinculadas = [
            d for d, _f in lineas_origen
            if _entero(d["docoritip"]) == TIP_CONTRATO and _entero(d["linoriide"])
        ]
        if vinculadas:
            ides = sorted({_entero(d["linoriide"]) for d in vinculadas})
            esperado = {_entero(f[0]): _d(f[1]) for f in leer(fs.bloquear_lineas_de_contrato(ides))}
            if set(ides) - set(esperado):
                raise FacturaError(
                    "Una linea de contrato de los origenes ya no existe: no se ha escrito nada.",
                    codigo="filas_afectadas_inesperadas",
                )
            for dcapro in vinculadas:
                ctrpro = _entero(dcapro["linoriide"])
                _ejecutar_sql(cursor, fs.sumar_facturado_contrato(ctrpro, dcapro["can"]))
                esperado[ctrpro] += _d(dcapro["can"])
            for ctrpro, canfac in esperado.items():
                relecturas.append((fs.releer_linea_de_contrato(ctrpro, float(canfac)),
                                   "filas_afectadas_inesperadas"))
            if ctx.ctride:
                # Agregado sin GROUP BY: siempre una fila, y aqui con lineas (las vinculadas).
                suma_can, suma_canser, suma_canfac = leer(f9.leer_sumas_contrato(ctx.ctride))[0]
                _estser, estfac = estados_contrato(suma_can, suma_canser, suma_canfac)
                _ejecutar_sql(cursor, fs.actualizar_estfac_contrato(ctx.ctride, estfac))
                relecturas.append((fs.releer_estfac_contrato(ctx.ctride, estfac),
                                   "filas_afectadas_inesperadas"))
        return relecturas

    @staticmethod
    def _releer(
        ctx: _Contexto, cursor: Any, fs: FacturaStatements, filas: FilasFactura,
        marcas: Sequence[tuple[tuple[str, list[Any]], str]],
    ) -> None:
        """R45: cada fila escrita y cada marca, por clave; si algo no cuadra, se
        revierte la factura entera (la excepcion hace el ROLLBACK)."""
        ide = filas.con["ide"]
        for sentencia, esperadas, que in (
            (fs.releer_con(ctx.obra.emp, filas.con["cod"]), 1, "con"),
            (fs.releer_dcf(ide, ctx.request.referencia_externa), 1, "dcf"),
            (fs.releer_dcfpro(ide), len(filas.dcfpro), "dcfpro"),
            (fs.releer_dcfrec(ide), len(filas.dcfrec), "dcfrec"),
            (fs.releer_pagos(ide), len(filas.pagos), "pag"),
            (fs.releer_consii(ide), 1, "consii"),
            (fs.releer_dcaprodes(ide), len(filas.dcaprodes), "dcaprodes"),
            (fs.releer_log(filas.log["ide"]), 1, "log"),
        ):
            cuantas = _contar(cursor, sentencia)
            if cuantas != esperadas:
                raise FacturaError(
                    f"Se esperaban {esperadas} filas de {que} y hay {cuantas}: se revierte la "
                    "factura entera.",
                    codigo="filas_afectadas_inesperadas",
                )
        for sentencia, codigo in marcas:
            if _contar(cursor, sentencia) != 1:
                raise FacturaError(
                    "Una marca en los origenes no ha quedado como se esperaba (otro proceso los ha "
                    "tocado): se revierte la factura entera.",
                    codigo=codigo,
                )

    # ------------------------------------------------------------------ #
    # Previa (R3, R44)
    # ------------------------------------------------------------------ #
    def _previa(self, ctx: _Contexto, montada: _Montada, leer: Lector, fs: FacturaStatements) -> FacturaResultado:
        request, filas = ctx.request, montada.filas
        maximo = leer(fs.ultimo_cod(ctx.obra.emp, ctx.prefijo, ctx.cifras))
        cod = siguiente_cod(ctx.prefijo, maximo[0][0] if maximo else None, cifras=ctx.cifras)

        def peek(tabla: str) -> int:
            return self._repo.peek_next_ide(database=request.database, table=tabla)

        numeradas = numerar(
            filas, cod=cod, ide_con=peek("con"), ide_dcfpro=peek("dcfpro"),
            ide_dcfrec=peek("dcfrec") if filas.dcfrec else None, ide_consii=peek("consii"),
            ide_dcaprodes=peek("dcaprodes") if filas.dcaprodes else None, ide_log=peek("log"),
        )
        return _resultado(ctx, montada, numeradas, estado="previsto",
                          avisos=[{"codigo": "cod_provisional", "mensaje": _AVISO_PROVISIONAL}])


def _ejecutar_sql(cursor: Any, sentencia: tuple[str, list[Any]]) -> None:
    cursor.execute(sentencia[0], *sentencia[1])


def _contar(cursor: Any, sentencia: tuple[str, list[Any]]) -> int:
    """Las reservas (`ISNULL(MAX) + 1`) y las relecturas (`COUNT`) son agregados
    sin GROUP BY: siempre UNA fila y nunca NULL."""
    _ejecutar_sql(cursor, sentencia)
    return int(cursor.fetchone()[0])


def _es_colision_de_clave(exc: BaseException) -> bool:
    """`pyodbc.IntegrityError` sin importar `pyodbc` en la capa de aplicacion
    (como F-006 y F-009): el repositorio la propaga al agotar los reintentos."""
    return any(clase.__name__ == "IntegrityError" for clase in type(exc).__mro__)


def _resultado(
    ctx: _Contexto, montada: _Montada, filas: FilasFactura, *, estado: str, avisos: list[dict[str, Any]],
) -> FacturaResultado:
    request = ctx.request
    n_origen = len(montada.lineas_origen)
    lineas = [
        {"posicion": i, "clase": "origen" if i < n_origen else "sin_origen",
         "origen": fila["docoricod"] or None, "linea": fila["linoriide"] or None,
         "indice": None if i < n_origen else i - n_origen, "can": fila["can"], "tot": fila["tot"],
         "ivacuo": fila["ivacuo"]}
        for i, fila in enumerate(filas.dcfpro)
    ]
    origenes = [
        {"cod": str(o["cod"]).strip(), "con_ide": _entero(o["ide"]),
         "lineas": sum(1 for d, _f in montada.lineas_origen if _entero(d["docide"]) == _entero(o["ide"]))}
        for o in ctx.origenes
    ]
    vencimientos = [{"cla": pag["cla"], "fecha": pag["fecven"], "importe": pag["tot"]}
                    for _c, pag in filas.pagos]
    retencion = None
    if montada.dcfrec is not None:
        retencion = {c: montada.dcfrec[c] for c in ("recide", "reccla", "valpor", "bas", "cuo")}
    commit = estado == "creado"
    return FacturaResultado(
        database=request.database, estado=estado, committed=commit, dry_run=not commit,
        cod=filas.con["cod"], con_ide=filas.con["ide"], serie=request.serie, modo=request.modo,
        referencia_externa=request.referencia_externa, totales=dict(montada.totales),
        retencion=retencion, vencimientos=vencimientos, origenes=origenes, lineas=lineas,
        filas=filas.como_dict(), avisos=avisos, pendiente_en_sigrid=list(PENDIENTE_EN_SIGRID),
    )


def _resultado_idempotente(request: FacturaRequest, fila: Sequence[Any]) -> FacturaResultado:
    """R43, R44: la factura ya registrada con esta referencia; nada se escribe."""
    return FacturaResultado(
        database=request.database, estado="idempotente", committed=False, dry_run=not request.commit,
        cod=str(fila[1] or "").strip(), con_ide=_entero(fila[0]), serie=request.serie,
        modo=request.modo, referencia_externa=request.referencia_externa,
        totales={"totbas": float(fila[4] or 0), "totiva": float(fila[5] or 0),
                 "totdoc": float(fila[6] or 0), "tot": float(fila[7] or 0)},
        retencion=None, vencimientos=[], origenes=[], lineas=[], filas={}, avisos=[],
        pendiente_en_sigrid=list(PENDIENTE_EN_SIGRID),
    )

