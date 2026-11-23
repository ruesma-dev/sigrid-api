# application/use_cases/create_proforma_use_case.py
"""
`POST /api/sigrid/proforma` (F-007): alta idempotente de UNA proforma DE MES de
un subcontratista sobre el nucleo de F-009 (D12): la peticion se valida contra
Sigrid, se traduce a la del modo extendido de `sigrid/albaran` y la escribe el
nucleo con el perfil de proforma (serie `PROF<aa>/`, `dca.cla 141`, llave y
listas propias).

Flujo (design §Flujo):
1. Guardas sin leer la base y fecha del periodo (R18, R26).
2. Obra y referencia (LP5, R23).
3. Contrato (LP3, LP4; R7-R9), salvo `sin_contrato` (R11).
4. Etapa 1 de las lineas: identificar, `producto`, R19 de linea (R13-R16).
5. Comprobaciones de la hoja (R19), lo registrado (LP1, LP2) y ya registrada
   (R24: `existente` con LP6, sin escribir); avisos R20-R22.
6. Traduccion y nucleo: etapa 2 de las lineas, construccion, previa o
   transaccion (R25-R29).
7. Respuesta (R30) y traza (R33).

Solo lecturas con credenciales de lectura hasta el commit, que es la
transaccion del nucleo. El SQL es el constante de `ProformaStatements` y de
`AlbaranCompraStatements`.

F-016: con `modo` `origen`, la proforma A ORIGEN sobre el mismo flujo. En 5,
la ya registrada es la de R5 y, despues, la cadena que manda el llamante
(LP7-LP9: la anterior, sus sucesoras y sus lineas), con las continuaciones y
el tope (R6-R10, R14); en 6, las columnas a origen y las arrastradas al final
de las `dcapro` (R11-R13) y LP8 otra vez bajo el applock (R17); en 7, la
respuesta con `cadena` (R19). En mes, cada rama es inerte (R1).
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Any

from pydantic import PrivateAttr

from application.use_cases.albaran_compra_statements import (
    POS_PASO,
    AlbaranCompraStatements,
    SellosAlbaran,
)
from application.use_cases.concepto_grafico_statements import hora_local_de_madrid
from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
    PerfilAlta,
    _Cabecera,
    _Construido,
    _Contrato,
    _Linea,
    _Obra,
)
from application.use_cases.proforma_origen_statements import (
    CadenaValidada,
    ProformaOrigenStatements,
    avisos_de_nuevas,
    buscar_del_mes_origen,
    cabecera_a_origen,
    comprobar_sucesoras,
    filas_arrastradas,
    importe_de_cadena,
    superponer_cadena,
    validar_anterior,
    validar_continuadas,
)
from application.use_cases.proforma_statements import (
    ContratoCandidato,
    LineaContrato,
    ProformaRegistrada,
    ProformaStatements,
    anterior_por_linea,
    anterior_y_origen,
    aviso_anterior_de_linea,
    buscar_del_mes,
    candidatos_de_contrato,
    comprobar_hoja,
    contrato_pedido,
    es_proforma,
    fecha_de_periodo,
    fin_de_periodo,
    importe_de_contrato,
    lineas_del_existente,
    primer_dia_de_periodo,
    resolver_contrato,
    revisar_lineas,
    traducir,
)
from domain.models.albaran_compra_models import (
    AlbaranCompraError,
    AlbaranCompraRequest,
    AlbaranCompraResponse,
)
from domain.models.proforma_models import (
    AvisoProforma,
    ContratoResuelto,
    LineaProformaResultado,
    OrigenProforma,
    ProformaError,
    ProformaRequest,
    ProformaResponse,
)
from domain.models.proforma_origen_models import (
    AnteriorCadena,
    AvisoProformaOrigen,
    CadenaProforma,
    LineaProformaOrigenResultado,
    ProformaOrigenError,
    ProformaOrigenResponse,
)


@dataclass(frozen=True)
class _Contexto:
    """Lo que `_comprobar_dentro` necesita de la proforma (R28) y, a origen, la
    cadena validada para `_construir` y para R17 (F-016; `None` en mes)."""

    ctride: int
    periodo: int
    importe_mes: float
    otra_del_mes: bool
    cadena: CadenaValidada | None = None


class _AltaDeProforma(AlbaranCompraRequest):
    """La peticion traducida al nucleo con el contexto de R28, que no viaja en
    ningun campo: el nucleo la trata como una `AlbaranCompraRequest` mas."""

    _contexto: _Contexto | None = PrivateAttr(default=None)


class _ExistenteDentro(Exception):
    """R28: bajo el applock aparecio la proforma del mes con el mismo total."""

    def __init__(self, proforma: ProformaRegistrada) -> None:
        super().__init__(proforma.cod)
        self.proforma = proforma


def _conflicto_de_referencia(filas: Sequence[Sequence[Any]]) -> ProformaError:
    """R23: la referencia esta en algo que no es UNA proforma de este contrato."""
    return ProformaError(
        f"La referencia externa ya esta en {len(filas)} documento(s) que no son una "
        f"proforma de este contrato: {', '.join(str(f[1]).strip() for f in filas)}.",
        codigo="referencia_en_conflicto",
    )


#: Lo que distingue el alta de una proforma (costura 1, R4, R12).
PERFIL_PROFORMA = PerfilAlta(
    endpoint="sigrid/proforma",
    prefijo_serie="PROF",
    cifras_serie=5,
    cla=141,
    codigo_llave="escritura_proformas_deshabilitada",
    campo_llave="sigrid_proforma_write_enabled",
    campo_prefijos="sigrid_proforma_prefijos_referencia",
    campo_max_lineas="sigrid_proforma_max_lineas",
    campo_productos="sigrid_proforma_productos_sin_contrato",
    campo_naturalezas="sigrid_proforma_naturaleza_por_producto",
    productos_del_contrato=True,
    error=ProformaError,
    documentos="proformas",
)


class CreateProformaUseCase(CreateAlbaranCompraUseCase):
    perfil: PerfilAlta = PERFIL_PROFORMA

    # ------------------------------------------------------------------ #
    # Orquestacion y traza (R33)
    # ------------------------------------------------------------------ #
    def run(self, request: ProformaRequest) -> ProformaResponse:
        """Una traza por peticion al terminar, con exito o sin el: obra,
        contrato y como se resolvio, referencia, periodo, numero de orden,
        `commit`, `estado`, `cod`, lineas de contrato y sin contrato, codigos y
        duracion. NUNCA textos, nombres, CIF, precios ni importes."""
        arranque = self._reloj()
        de_contrato = sum(
            1 for linea in request.lineas if linea.de_contrato and not request.sin_contrato
        )
        traza: dict[str, Any] = {
            "endpoint": self.perfil.endpoint,
            "database": request.database,
            "obra": request.cod_obra,
            "contrato": request.cod_contrato,
            "resuelto_por": None,
            "referencia": request.referencia_externa,
            "periodo": request.periodo,
            "numero_orden": request.numero_orden,
            "commit": request.commit,
            "n_lineas_contrato": de_contrato,
            "n_lineas_sin_contrato": len(request.lineas) - de_contrato,
        }
        if request.modo == "origen":
            # F-016 R21: solo a origen (la de mes no cambia, R1); sin importes.
            traza.update(
                modo=request.modo, primera_de_cadena=request.primera_de_cadena,
                anterior=request.proforma_anterior,
                n_continuadas=sum(1 for l in request.lineas if l.linea_anterior is not None),
                n_arrastradas=None,
            )
        try:
            respuesta = self._proforma(request, traza)
        except AlbaranCompraError as exc:
            traza.update(resultado="error", codigo=exc.codigo,
                         codigos=[fallo.codigo for fallo in exc.lineas])
            self._trazar(traza, arranque)
            raise
        except Exception as exc:
            # El tipo y no el mensaje: puede citar valores de la peticion.
            traza.update(resultado="excepcion", codigo=type(exc).__name__, codigos=[])
            self._trazar(traza, arranque)
            raise
        traza.update(
            resultado="ok",
            estado=respuesta.estado,
            cod=respuesta.cod,
            con_ide=respuesta.con_ide,
            codigos=[aviso.codigo for aviso in respuesta.avisos]
            + [aviso.codigo for linea in respuesta.lineas for aviso in linea.avisos],
        )
        self._trazar(traza, arranque)
        return respuesta

    def _proforma(self, request: ProformaRequest, traza: dict[str, Any]) -> ProformaResponse:
        # 1. Guardas sin leer la base (R26; R5 ya en la ruta) y fecha (R18).
        self._comprobar_guardas(request)
        hoy = int(f"{hora_local_de_madrid(self._ahora_utc()):%Y%m%d}")
        fecha = fecha_de_periodo(request.periodo, request.fecha_proforma, hoy)
        sentencias = AlbaranCompraStatements(database=request.database)
        lecturas = ProformaStatements(database=request.database)

        # 2. Obra y referencia (R23, se decide con el contrato resuelto).
        obra = self._resolver_obra(request, sentencias)
        _c, referencias = self._leer(request, lecturas.buscar_referencia(request.referencia_externa))

        # 3. Contrato (R7-R11).
        contrato: ContratoCandidato | None = None
        resuelto: ContratoResuelto | None = None
        lineas_contrato: list[LineaContrato] = []
        if not request.sin_contrato:
            contrato, resuelto, lineas_contrato = self._contrato(request, lecturas, obra)
            traza.update(contrato=resuelto.cod, resuelto_por=resuelto.resuelto_por)
        ctride = contrato.ide if contrato is not None else 0
        if referencias:
            if len(referencias) == 1 and es_proforma(referencias[0], ctride):
                return self._a_origen(request, self._idempotente(request, sentencias, resuelto))
            raise _conflicto_de_referencia(referencias)

        # 4. Etapa 1 de las lineas: todos sus fallos juntos. A origen (F-016 R9)
        # salen despues, con los de las continuaciones, en un solo error.
        a_origen = request.modo == "origen"
        identificadas, fallos = revisar_lineas(
            request.lineas, lineas_contrato, sin_contrato=request.sin_contrato
        )
        if fallos and not a_origen:
            raise ProformaError(
                f"{len({f.indice for f in fallos})} linea(s) no validas: no se ha escrito nada.",
                codigo="lineas_no_validas",
                lineas=list(fallos),
            )

        # 5. Comprobaciones, lo registrado y ya registrada (con contrato).
        origen: OrigenProforma | None = None
        avisos: list[AvisoProforma] = []
        anterior: dict[int, float] = {}
        avisos_linea: dict[int, AvisoProforma] = {}
        cadena: CadenaValidada | None = None
        if contrato is not None:
            comprobar_hoja(request)
            proformas = self._proformas_del_contrato(request, lecturas, ctride)
            _c, filas = self._leer(
                request,
                lecturas.leer_anterior(ctride, primer_dia_de_periodo(request.periodo)),
                muchas=True,
            )
            anterior = anterior_por_linea(filas)
            origen, avisos_origen = anterior_y_origen(
                proformas,
                primer_dia=primer_dia_de_periodo(request.periodo),
                importe_mes=request.importe_mes,
                importe_contrato=importe_de_contrato(lineas_contrato),
                importe_anterior=request.importe_anterior,
            )
            # F-016 R5: a origen, otra a origen del mes con otro total es aviso.
            existente, avisos_mes = (buscar_del_mes_origen if a_origen else buscar_del_mes)(
                proformas, periodo=request.periodo, importe_mes=request.importe_mes,
                otra_del_mes=request.otra_del_mes,
            )
            if a_origen:
                # F-016 R16: «se registra de mes» seria falso.
                avisos_origen = [a for a in avisos_origen if a.codigo != "contrato_a_origen"]
            avisos = [*avisos_origen, *avisos_mes]
            for indice, ctrpro in identificadas.items():
                aviso = aviso_anterior_de_linea(request.lineas[indice], anterior.get(ctrpro.ide, 0.0))
                if aviso is not None:
                    avisos_linea[indice] = aviso
            if existente is not None:
                return self._a_origen(
                    request, self._existente(request, lecturas, existente, resuelto, origen, avisos)
                )
            if a_origen:
                cadena = self._cadena(request, ctride, fecha, identificadas, fallos)
                traza["n_arrastradas"] = cadena.n_arrastradas

        # 6. Traduccion y nucleo, con lo que R28 repite bajo el applock de referencias.
        traducida = traducir(request, contrato=contrato, identificadas=identificadas, fecha=fecha)
        alta = _AltaDeProforma.model_validate(traducida.model_dump())
        alta._contexto = _Contexto(
            ctride=ctride, periodo=request.periodo, importe_mes=request.importe_mes,
            otra_del_mes=request.otra_del_mes, cadena=cadena,
        )
        try:
            nucleo = self._ejecutar(alta)
        except _ExistenteDentro as dentro:
            # La transaccion ya se ha revertido sin escribir nada (R28).
            return self._a_origen(request, self._existente(
                request, lecturas, dentro.proforma, resuelto, origen, avisos
            ))
        if nucleo.estado == "idempotente":
            # R28 (D3): la misma referencia aparecio bajo el applock; como la de
            # fuera (R23), sin `origen` ni los avisos de la hoja.
            origen, avisos = None, []
        # 7. Respuesta (R30; F-016 R19).
        return self._a_origen(request, self._convertir(
            request, nucleo, resuelto=resuelto, origen=origen, avisos=avisos,
            avisos_linea=avisos_linea, anterior=anterior,
        ), cadena)

    # ------------------------------------------------------------------ #
    # F-016 · la cadena a origen (R6-R10, R14)
    # ------------------------------------------------------------------ #
    def _cadena(
        self,
        request: ProformaRequest,
        ctride: int,
        fecha: int,
        identificadas: Mapping[int, LineaContrato],
        fallos: Sequence[Any],
    ) -> CadenaValidada:
        """Con `proforma_anterior`: LP7 (R6), LP8 (R7) y LP9; en la primera,
        nada que leer (R8). Despues las continuaciones (R9), con los fallos de
        la etapa 1 en el mismo `lineas_no_validas`, el aviso de R10 y el tope
        de R14 con las arrastradas, aun en previa."""
        lecturas = ProformaOrigenStatements(database=request.database)
        anterior = None
        filas: list[dict[str, Any]] = []
        if request.proforma_anterior is not None:
            _c, encontradas = self._leer(
                request, lecturas.leer_proforma_anterior(ctride, request.proforma_anterior)
            )
            anterior = validar_anterior(encontradas, cod=request.proforma_anterior, fecha=fecha)
            _c, sucesoras = self._leer(
                request, lecturas.leer_sucesoras(ctride, anterior.ide), muchas=True
            )
            comprobar_sucesoras(sucesoras)
            columnas, leidas = self._leer(
                request, lecturas.leer_lineas_anterior(anterior.ide), muchas=True
            )
            filas = [dict(zip(columnas, fila, strict=True)) for fila in leidas]
        continuadas, fallos_cadena = validar_continuadas(request.lineas, identificadas, filas)
        todos = [*fallos, *fallos_cadena]
        if todos:
            raise ProformaOrigenError(
                f"{len({f.indice for f in todos})} linea(s) no validas: no se ha escrito nada.",
                codigo="lineas_no_validas",
                lineas=todos,
            )
        cadena = CadenaValidada(
            anterior=anterior, filas=filas, continuadas=continuadas,
            avisos=avisos_de_nuevas(request.lineas, identificadas, filas, continuadas),
        )
        tope = getattr(self._settings, self.perfil.campo_max_lineas)
        if len(request.lineas) + cadena.n_arrastradas > tope:
            raise ProformaOrigenError(
                f"La proforma trae {len(request.lineas)} lineas y {cadena.n_arrastradas} "
                f"arrastradas y el tope es {tope}: alta a mano.",
                codigo="demasiadas_lineas",
            )
        return cadena

    # ------------------------------------------------------------------ #
    # Contrato (R7-R10)
    # ------------------------------------------------------------------ #
    def _contrato(
        self, request: ProformaRequest, lecturas: ProformaStatements, obra: _Obra
    ) -> tuple[ContratoCandidato, ContratoResuelto, list[LineaContrato]]:
        _c, filas = self._leer(request, lecturas.leer_contratos_de_obra(obra.ide), muchas=True)
        contratos = [ContratoCandidato.de_fila(fila) for fila in filas]
        if request.cod_contrato is not None:
            elegido = contrato_pedido(contratos, request.cod_contrato, cif=request.cif_proveedor)
            lineas = self._lineas_de_contratos(request, lecturas, [elegido.ide])
            resuelto = ContratoResuelto(
                cod=elegido.cod, ide=elegido.ide, resuelto_por="peticion", candidatos=[elegido.cod]
            )
            return elegido, resuelto, list(lineas.get(elegido.ide, []))
        candidatos = candidatos_de_contrato(
            contratos, fin_periodo=fin_de_periodo(request.periodo),
            cif=request.cif_proveedor, nombre=request.nombre_proveedor,
        )
        lineas = (
            self._lineas_de_contratos(request, lecturas, [c.ide for c in candidatos])
            if candidatos else {}
        )
        resuelto = resolver_contrato(candidatos, lineas, request.lineas)
        elegido = next(c for c in candidatos if c.ide == resuelto.ide)
        return elegido, resuelto, list(lineas.get(elegido.ide, []))

    def _lineas_de_contratos(
        self, request: ProformaRequest, lecturas: ProformaStatements, ctrides: Sequence[int]
    ) -> dict[int, list[LineaContrato]]:
        _c, filas = self._leer(request, lecturas.leer_lineas_de_contratos(ctrides), muchas=True)
        por_contrato: dict[int, list[LineaContrato]] = {ide: [] for ide in ctrides}
        for fila in filas:
            linea = LineaContrato.de_fila(fila)
            por_contrato.setdefault(linea.docide, []).append(linea)
        return por_contrato

    def _proformas_del_contrato(
        self, request: ProformaRequest, lecturas: ProformaStatements, ctride: int
    ) -> list[ProformaRegistrada]:
        _c, filas = self._leer(request, lecturas.leer_proformas_del_contrato(ctride), muchas=True)
        return [ProformaRegistrada.de_fila(fila) for fila in filas]

    # ------------------------------------------------------------------ #
    # Ya registrada (R23, R24)
    # ------------------------------------------------------------------ #
    def _idempotente(
        self, request: ProformaRequest, sentencias: AlbaranCompraStatements,
        resuelto: ContratoResuelto | None,
    ) -> ProformaResponse:
        """R23 como F-009 R30: lo LEIDO de Sigrid (L11), sin escribir."""
        _c, filas = self._leer(request, sentencias.buscar_referencia(request.referencia_externa))
        if len(filas) != 1:
            raise ValueError(
                "La referencia externa cambio entre dos lecturas: no se responde idempotente."
            )
        _c, lineas = self._leer(
            request, sentencias.leer_lineas_de_albaran(int(filas[0][0])), muchas=True
        )
        nucleo = self._respuesta_idempotente(request, filas[0], lineas)
        return self._convertir(
            request, nucleo, resuelto=resuelto, origen=None, avisos=[], avisos_linea={},
            anterior={},
        )

    def _existente(
        self,
        request: ProformaRequest,
        lecturas: ProformaStatements,
        proforma: ProformaRegistrada,
        resuelto: ContratoResuelto | None,
        origen: OrigenProforma | None,
        avisos: list[AvisoProforma],
    ) -> ProformaResponse:
        """R24 (D10): la proforma del contrato y del mes con el mismo total, con
        sus lineas (LP6) para enlazarla; sin escribir, en previa y con commit."""
        _c, filas = self._leer(request, lecturas.leer_lineas_de_proforma(proforma.ide), muchas=True)
        lineas = lineas_del_existente(filas)
        return ProformaResponse(
            database=request.database,
            committed=False,
            dry_run=not request.commit,
            con_ide=proforma.ide,
            cod=proforma.cod,
            contrato=resuelto,
            cabecera={"fec": proforma.fec, "entref": proforma.entref},
            lineas=lineas,
            totales={"totbas": proforma.totbas, "n_lineas": len(lineas)},
            estado="existente",
            referencia_externa=request.referencia_externa,
            avisos=avisos,
            origen=origen,
        )

    # ------------------------------------------------------------------ #
    # Nucleo: el contrato resuelto, R28 dentro de la transaccion y la clase
    # de la `dca` (R12)
    # ------------------------------------------------------------------ #
    def _resolver_contrato(self, request: AlbaranCompraRequest, obra: _Obra) -> _Contrato:
        """O4: el contrato que R7-R9 ya han resuelto, cargado por su `ide` (el
        de LP3, de esta obra). No se vuelve a localizar por `cod` + obra + CIF:
        un `ctr.entcif` con espacios no casaria con el CIF normalizado."""
        assert isinstance(request, _AltaDeProforma)
        assert request._contexto is not None
        contrato = self._cargar_contrato(request, request._contexto.ctride)
        if contrato is None:
            raise ProformaError(
                f"El contrato '{request.cod_contrato}' ya no esta en Sigrid.",
                codigo="contrato_no_encontrado",
            )
        return contrato

    def _comprobar_dentro(
        self,
        cursor: Any,
        request: AlbaranCompraRequest,
        cabecera: _Cabecera,
        existente: tuple[Any, ...] | None,
    ) -> None:
        """R28 (costura 3, enmienda 1): tras E1, con `SIGRID_REFEXT_14` tomado y
        antes de reservar nada, por el cursor del `work`. Si E1 ha encontrado la
        referencia, R23 con LP5: solo sale `idempotente` si es UNA proforma del
        contrato resuelto (o sin contrato, si lo era la peticion); si no,
        `referencia_en_conflicto`. Si no, R24 con LP1: una del mes con el mismo
        total aparecida entre tanto es `existente`; con otro total, el error de
        R24; con `otra_del_mes`, sigue (sin contrato no hay R24). A origen
        (F-016 R17), R5 en lugar de R24 y, con anterior, LP8: si ya tiene
        sucesora, `anterior_con_sucesora`. Lo que se lance aqui revierte la
        transaccion sin escribir."""
        assert isinstance(request, _AltaDeProforma)
        contexto = request._contexto
        assert contexto is not None
        lecturas = ProformaStatements(database=request.database)
        if existente is not None:
            sql, params = lecturas.buscar_referencia(request.referencia_externa)
            cursor.execute(sql, *params)
            filas = list(cursor.fetchall())
            if len(filas) == 1 and es_proforma(filas[0], contexto.ctride):
                return
            raise _conflicto_de_referencia(filas)
        if not contexto.ctride:
            return
        sql, params = lecturas.leer_proformas_del_contrato(contexto.ctride)
        cursor.execute(sql, *params)
        proformas = [ProformaRegistrada.de_fila(fila) for fila in cursor.fetchall()]
        cadena = contexto.cadena
        # F-016 R17: a origen, R5 en lugar de R24 y, con anterior, LP8 otra vez.
        existente, _avisos = (buscar_del_mes_origen if cadena is not None else buscar_del_mes)(
            proformas, periodo=contexto.periodo, importe_mes=contexto.importe_mes,
            otra_del_mes=contexto.otra_del_mes,
        )
        if existente is not None:
            raise _ExistenteDentro(existente)
        if cadena is not None and cadena.anterior is not None:
            sql, params = ProformaOrigenStatements(database=request.database).leer_sucesoras(
                contexto.ctride, cadena.anterior.ide
            )
            cursor.execute(sql, *params)
            comprobar_sucesoras(list(cursor.fetchall()))

    def _construir(
        self,
        request: AlbaranCompraRequest,
        cabecera: _Cabecera,
        lineas: Sequence[_Linea],
        sellos: SellosAlbaran,
        vigentes: Mapping[tuple[int, int], tuple[float, float]],
    ) -> _Construido:
        """Las filas del nucleo con la clase de proforma en la `dca` (R12, M31)
        y, a origen (F-016 R11-R13), las columnas a origen de las lineas de la
        peticion, las arrastradas AL FINAL de las `dcapro` (asi `numerar`, la
        previa, el `INSERT` y la relectura E12 las cuentan sin tocar el nucleo;
        no son `_Linea`: sin `ctrprodes`, `mov` ni `UPDATE`, D6) y la `dca`
        encadenada a la anterior."""
        construido = super()._construir(request, cabecera, lineas, sellos, vigentes)
        filas = replace(construido.filas, dca={**construido.filas.dca, "cla": self.perfil.cla})
        assert isinstance(request, _AltaDeProforma)
        assert request._contexto is not None
        cadena = request._contexto.cadena
        if cadena is not None:
            dcapro = superponer_cadena(filas.dcapro, cadena.continuadas)
            usadas = {int(fila["ide"]) for fila in cadena.continuadas.values()}
            dcapro += filas_arrastradas(cadena.filas, usadas, (len(dcapro) + 1) * POS_PASO)
            filas = replace(filas, dca=cabecera_a_origen(filas.dca, cadena.anterior), dcapro=dcapro)
        return replace(construido, filas=filas)

    # ------------------------------------------------------------------ #
    # Respuesta (R30)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _convertir(
        request: ProformaRequest,
        nucleo: AlbaranCompraResponse,
        *,
        resuelto: ContratoResuelto | None,
        origen: OrigenProforma | None,
        avisos: list[AvisoProforma],
        avisos_linea: Mapping[int, AvisoProforma],
        anterior: Mapping[int, float],
    ) -> ProformaResponse:
        """La del nucleo mas `contrato`, `origen`, los avisos de F-007 y, por
        linea, `de_contrato` y `cantidad_anterior_sigrid`. En `idempotente` las
        lineas son las LEIDAS y no se casan con las de la peticion."""
        leidas = nucleo.estado == "idempotente"
        lineas = []
        for linea in nucleo.lineas:
            vinculada = linea.tipo == "vinculada"
            propios = [AvisoProforma(**aviso.model_dump()) for aviso in linea.avisos]
            if not leidas and linea.indice in avisos_linea:
                propios.append(avisos_linea[linea.indice])
            lineas.append(LineaProformaResultado(
                **linea.model_dump(exclude={"avisos"}),
                avisos=propios,
                de_contrato=None if leidas else vinculada,
                cantidad_anterior_sigrid=(
                    anterior.get(linea.ctrpro_ide, 0.0) if vinculada and not leidas else None
                ),
            ))
        return ProformaResponse(
            **nucleo.model_dump(exclude={"contrato", "avisos", "lineas", "warnings"}),
            contrato=resuelto,
            origen=origen,
            avisos=[*(AvisoProforma(**a.model_dump()) for a in nucleo.avisos), *avisos],
            lineas=lineas,
        )

    # ------------------------------------------------------------------ #
    # F-016 · respuesta a origen (R19)
    # ------------------------------------------------------------------ #
    @staticmethod
    def _a_origen(
        request: ProformaRequest,
        respuesta: ProformaResponse,
        cadena: CadenaValidada | None = None,
    ) -> ProformaResponse:
        """En mes, la de F-007 tal cual (R1). A origen, `ProformaOrigenResponse`:
        si se ha construido (previsto o creado), con `cadena`, los campos de la
        cadena por linea, el aviso de R10 y las arrastradas detras, leidas de
        `filas.dcapro` a partir de las de la peticion; en `existente` e
        `idempotente` (lineas LEIDAS), `cadena` null y nada de eso."""
        if request.modo != "origen":
            return respuesta
        construida = cadena is not None and respuesta.estado in ("previsto", "creado")
        lineas: list[LineaProformaOrigenResultado] = []
        for linea in respuesta.lineas:
            propios = [AvisoProformaOrigen(**aviso.model_dump()) for aviso in linea.avisos]
            extra: dict[str, Any] = {}
            if construida:
                assert cadena is not None
                continuada = cadena.continuadas.get(linea.indice)
                if linea.indice in cadena.avisos:
                    propios.append(cadena.avisos[linea.indice])
                extra = {
                    "linea_anterior": request.lineas[linea.indice].linea_anterior,
                    "arrastrada": False,
                    "cantidad_anterior_cadena": (
                        float(continuada.get("canoriori") or 0) if continuada is not None else 0.0
                    ),
                    "cantidad_origen_cadena": respuesta.filas["dcapro"][linea.indice]["canoriori"],
                }
            lineas.append(LineaProformaOrigenResultado(
                **linea.model_dump(exclude={"avisos"}), avisos=propios, **extra
            ))
        resumen: CadenaProforma | None = None
        if construida:
            assert cadena is not None
            escritas = respuesta.filas["dcapro"]
            pedidas = len(request.lineas)
            lineas.extend(
                _linea_arrastrada(indice, fila)
                for indice, fila in enumerate(escritas[pedidas:], start=pedidas)
            )
            resumen = CadenaProforma(
                anterior=(
                    AnteriorCadena(cod=cadena.anterior.cod, ide=cadena.anterior.ide)
                    if cadena.anterior is not None else None
                ),
                primera_de_cadena=request.primera_de_cadena,
                importe_anterior_cadena=importe_de_cadena(cadena.filas),
                importe_origen_cadena=importe_de_cadena(escritas),
                n_arrastradas=len(escritas) - pedidas,
            )
        return ProformaOrigenResponse(
            **respuesta.model_dump(exclude={"avisos", "lineas", "warnings"}),
            avisos=[AvisoProformaOrigen(**aviso.model_dump()) for aviso in respuesta.avisos],
            lineas=lineas,
            cadena=resumen,
        )


def _linea_arrastrada(indice: int, fila: Mapping[str, Any]) -> LineaProformaOrigenResultado:
    """F-016 R19: una arrastrada en la respuesta, de su fila escrita (R12)."""
    vinculo = int(fila.get("linoriide") or 0)
    origen = float(fila.get("canoriori") or 0)
    return LineaProformaOrigenResultado(
        indice=indice,
        referencia_linea=str(fila.get("refent") or "").strip(),
        tipo="vinculada" if vinculo else "sin_vincular",
        ctrpro_ide=vinculo,
        linoriide=vinculo,
        proide=int(fila.get("proide") or 0),
        res=fila.get("res"),
        unimed=fila.get("unimed"),
        cantidad=float(fila["can"]),
        precio=float(fila.get("pre") or 0),
        total=float(fila["tot"]),
        iva_cuota=float(fila["ivacuo"]),
        almide=int(fila.get("almide") or 0),
        cenide=fila.get("cenide"),
        paride=int(fila.get("paride") or 0),
        de_contrato=vinculo > 0,
        linea_anterior=int(fila["canorilin"]),
        arrastrada=True,
        cantidad_anterior_cadena=origen,
        cantidad_origen_cadena=origen,
    )
