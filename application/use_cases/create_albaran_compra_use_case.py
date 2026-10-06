# application/use_cases/create_albaran_compra_use_case.py
"""
Modo EXTENDIDO de `POST /api/sigrid/albaran` (F-009): alta idempotente de UN
albaran de compra (`con.tip 14`) con lineas vinculadas a un contrato y sin
vincular (producto de la lista blanca), con o sin partida y con devoluciones.

Flujo (design §Flujo):
1. Guardas sin leer la base (tope de lineas, prefijo, llaves de escritura).
2. Cabecera con lecturas: obra en las empresas admitidas -> contrato -> plantilla
   de cabecera del mismo proveedor y empresa -> idempotencia -> `conest` y `usu`.
3. Lineas, TODAS, acumulando los fallos (`lineas_no_validas`).
4. Construccion pura de las filas (`albaran_compra_statements`) y, en previa,
   numeracion provisional; en commit, UNA transaccion reentrante.

El SQL es el constante de `AlbaranCompraStatements`; aqui solo se orquesta.
Las lecturas usan credenciales de LECTURA (`execute_read_query` y los metodos
de lectura del repositorio); solo el commit abre una transaccion de escritura.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from application.use_cases.albaran_compra_statements import (
    TIP_CONTRATO,
    AlbaranCompraStatements,
    Balance,
    FilasAlbaran,
    SellosAlbaran,
    codigo_analitica,
    construir_con,
    construir_ctrprodes,
    construir_dca,
    construir_dcapro_sin_vincular,
    construir_dcapro_vinculada,
    construir_log,
    construir_mov,
    encadenar_balances,
    estados_contrato,
    importe_linea,
    numerar,
    sellos_del_alta,
    siguiente_cod,
    sumar_importes,
    usa_precio_del_contrato,
)
from domain.models.albaran_compra_models import (
    AlbaranCompraError,
    AlbaranCompraRequest,
    AlbaranCompraResponse,
    AvisoAlbaran,
    FalloLinea,
    LineaAlbaranIn,
    LineaResultado,
)
from domain.models.sql_models import SqlReadRequest

_AVISO_PROVISIONAL = (
    "DRY-RUN: no se ha escrito nada. El cod y los ide son provisionales (MAX+1 sin "
    "reservar); en el commit se reservan bajo bloqueo."
)


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


def _clave(texto: Any) -> str:
    """Codigos comparados como los compara el ERP (`Modern_Spanish_CI_AS`): sin
    mayusculas ni espacios de cola."""
    return str(texto).strip().casefold()


def _entero(valor: Any) -> int:
    return int(valor or 0)


def _r2(valor: Any) -> float:
    return round(float(valor or 0), 2)


def _aviso(codigo: str, mensaje: str) -> AvisoAlbaran:
    return AvisoAlbaran(codigo=codigo, mensaje=mensaje)


class _FalloDeLinea(Exception):
    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje


@dataclass(frozen=True)
class _Obra:
    ide: int
    emp: int
    cod: str


@dataclass(frozen=True)
class _Contrato:
    ide: int
    fila: dict[str, Any]
    lineas: dict[int, dict[str, Any]]


@dataclass
class _Cabecera:
    obra: _Obra
    contrato: _Contrato | None
    entide: int
    entidad: dict[str, Any]
    entres: str | None
    template_ide: int
    con_plantilla: dict[str, Any]
    dca_plantilla: dict[str, Any]
    # Almacen y centro de las sin vincular (R15), resuelto una vez si hace falta.
    almacen_sin_vincular: tuple[int, int] | None = None

    @property
    def ctride(self) -> int:
        return self.contrato.ide if self.contrato else 0

    @property
    def almacen_cabecera(self) -> tuple[int, int]:
        """`dca.almide`/`cenide`: el de las sin vincular si lo hay (que es el del
        contrato cuando este lo tiene, R15) y, si no, el del contrato, como el
        clasico. Sin sin vincular siempre hay contrato (las vinculadas lo exigen)."""
        if self.almacen_sin_vincular is not None:
            return self.almacen_sin_vincular
        assert self.contrato is not None
        fila = self.contrato.fila
        return _entero(fila.get("almide")), _entero(fila.get("cenide"))


@dataclass
class _Linea:
    """Una linea ya validada, con todo lo que necesitan sus filas."""

    indice: int
    linea: LineaAlbaranIn
    proide: int
    producto: str | None
    ctrpro: dict[str, Any] | None
    paride: int
    almide: int
    cenide: int
    natide: int = 0
    cueide: int = 0
    caaide: int = 0
    tipmov: int = 0
    plantilla: dict[str, Any] | None = None
    ivaide: int = 0
    iva: float = 0.0
    avisos: list[AvisoAlbaran] = field(default_factory=list)

    @property
    def vinculada(self) -> bool:
        return self.ctrpro is not None

    @property
    def con_mov(self) -> bool:
        return self.tipmov == 1


@dataclass(frozen=True)
class _Construido:
    """Las filas de un intento y el balance de cada linea con `mov`."""

    filas: FilasAlbaran
    balances: dict[int, Balance]
    totales: dict[str, float]


class CreateAlbaranCompraUseCase:
    def __init__(
        self,
        repository: Any,
        settings: Any,
        ahora_utc: Callable[[], datetime] = _ahora_utc,
    ) -> None:
        self._repo = repository
        self._settings = settings
        self._ahora_utc = ahora_utc

    # ------------------------------------------------------------------ #
    # Orquestacion
    # ------------------------------------------------------------------ #
    def run(self, request: AlbaranCompraRequest) -> AlbaranCompraResponse:
        if request.commit:
            raise NotImplementedError("El commit del modo extendido llega en T10.")
        sentencias = AlbaranCompraStatements(database=request.database)
        # R22: un instante por peticion, fuera de cualquier transaccion.
        sellos = sellos_del_alta(self._ahora_utc(), request.fecha_albaran)
        cabecera = self._leer_cabecera(request, sentencias)
        lineas = self._resolver_lineas(request, sentencias, cabecera)
        return self._previa(request, sentencias, cabecera, lineas, sellos)

    # ------------------------------------------------------------------ #
    # Lecturas (credenciales de lectura)
    # ------------------------------------------------------------------ #
    def _leer(
        self,
        request: AlbaranCompraRequest,
        sentencia: tuple[str, list[Any]],
        *,
        muchas: bool = False,
    ) -> tuple[list[str], list[tuple[Any, ...]]]:
        """`model_construct` a proposito, como F-004 y F-006: el SQL es
        constante y los parametros los pone el caso de uso. Truncar nunca se
        ignora: una lista a medias validaria mal en silencio."""
        sql, params = sentencia
        columnas, filas, truncado = self._repo.execute_read_query(
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
                "no se da de alta el albaran."
            )
        return list(columnas), [tuple(fila) for fila in filas]

    def _fila_completa(self, request: AlbaranCompraRequest, tabla: str, ide: int) -> dict[str, Any] | None:
        leida = self._repo.read_full_row(database=request.database, table=tabla, ide=ide)
        if leida is None:
            return None
        columnas, valores = leida
        return dict(zip(columnas, valores))

    # ------------------------------------------------------------------ #
    # Cabecera (R11, R22)
    # ------------------------------------------------------------------ #
    def _leer_cabecera(
        self, request: AlbaranCompraRequest, sentencias: AlbaranCompraStatements
    ) -> _Cabecera:
        obra = self._resolver_obra(request, sentencias)
        contrato = self._resolver_contrato(request, obra) if request.cod_contrato else None

        if contrato is not None:
            entide = _entero(contrato.fila.get("entide"))
            sentencia = sentencias.leer_plantilla_cabecera(obra.emp, entide)
        else:
            sentencia = sentencias.leer_plantilla_cabecera_por_cif(obra.emp, request.cif_proveedor)
        _columnas, filas = self._leer(request, sentencia)
        if not filas:
            raise AlbaranCompraError(
                "El proveedor no tiene ningun albaran previo en la empresa de la obra del "
                "que copiar la cabecera (forma de pago, efecto, direccion): alta a mano.",
                codigo="proveedor_sin_albaran_previo",
            )
        template_ide = int(filas[0][0])
        con_plantilla = self._fila_completa(request, "con", template_ide)
        dca_plantilla = self._fila_completa(request, "dca", template_ide)
        if con_plantilla is None or dca_plantilla is None:
            raise ValueError(f"No se pudo leer la plantilla de cabecera (con/dca) ide={template_ide}.")

        if contrato is not None:
            entidad = {c: contrato.fila.get(c) for c in ("entide", "entcod", "entres", "entcif")}
            entidad["entide"] = entide
            entres = contrato.fila.get("entres")
        else:
            entide = _entero(dca_plantilla.get("entide"))
            entidad = {"entide": entide, "entcod": None, "entres": None, "entcif": None}
            entres = dca_plantilla.get("entres")

        if not self._leer(request, sentencias.leer_estado_inicial())[1]:
            raise AlbaranCompraError(
                "El estado inicial (tip 14, est 1) no existe en dbo.conest.",
                codigo="estado_inicial_no_encontrado",
            )
        if not self._leer(request, sentencias.leer_usuario(request.usu))[1]:
            raise AlbaranCompraError(
                f"El usuario '{request.usu}' no existe en dbo.usu.", codigo="usuario_no_valido"
            )
        return _Cabecera(
            obra=obra,
            contrato=contrato,
            entide=entide,
            entidad=entidad,
            entres=entres,
            template_ide=template_ide,
            con_plantilla=con_plantilla,
            dca_plantilla=dca_plantilla,
        )

    def _resolver_obra(
        self, request: AlbaranCompraRequest, sentencias: AlbaranCompraStatements
    ) -> _Obra:
        """H2: la obra por `(tip 42, cod)`, solo entre las empresas admitidas."""
        _columnas, filas = self._leer(request, sentencias.leer_obra(request.cod_obra))
        if not filas:
            raise AlbaranCompraError(
                f"No existe la obra '{request.cod_obra}'.", codigo="obra_no_encontrada"
            )
        empresas = self._settings.sigrid_albaran_empresas_obra
        admitidas = [fila for fila in filas if _entero(fila[1]) in empresas]
        if not admitidas:
            raise AlbaranCompraError(
                f"La obra '{request.cod_obra}' no es de ninguna empresa admitida "
                "(SIGRID_ALBARAN_EMPRESAS_OBRA).",
                codigo="obra_de_empresa_no_permitida",
            )
        if len(admitidas) > 1:
            raise AlbaranCompraError(
                f"La obra '{request.cod_obra}' existe en {len(admitidas)} empresas admitidas.",
                codigo="obra_ambigua",
            )
        ide, emp, cod = admitidas[0]
        return _Obra(ide=int(ide), emp=int(emp), cod=str(cod))

    def _resolver_contrato(self, request: AlbaranCompraRequest, obra: _Obra) -> _Contrato:
        """El localizador de siempre (contrato + obra + CIF), y solo los de ESTA obra."""
        columnas, filas = self._repo.locate_contract(
            database=request.database,
            cod_contrato=request.cod_contrato,
            cod_obra=request.cod_obra,
            cif_proveedor=request.cif_proveedor,
            contract_tip=TIP_CONTRATO,
        )
        de_la_obra = [
            fila for fila in (dict(zip(columnas, f)) for f in filas)
            if _entero(fila.get("obride")) == obra.ide
        ]
        if len(de_la_obra) > 1:
            raise AlbaranCompraError(
                f"Hay {len(de_la_obra)} contratos '{request.cod_contrato}' de la obra y el proveedor.",
                codigo="contrato_ambiguo",
            )
        ctride = int(de_la_obra[0]["ide"]) if de_la_obra else 0
        ctr = self._fila_completa(request, "ctr", ctride) if de_la_obra else None
        if ctr is None:
            raise AlbaranCompraError(
                f"No hay un contrato '{request.cod_contrato}' de la obra '{request.cod_obra}' y ese "
                "proveedor.",
                codigo="contrato_no_encontrado",
            )
        columnas, filas = self._repo.read_rows_by(
            database=request.database, table="ctrpro", where_column="docide",
            where_value=ctride, order_by="pos",
        )
        lineas = [dict(zip(columnas, fila)) for fila in filas]
        return _Contrato(ide=ctride, fila=ctr, lineas={int(l["ide"]): l for l in lineas})

    # ------------------------------------------------------------------ #
    # Lineas (R9, R12-R17)
    # ------------------------------------------------------------------ #
    def _resolver_lineas(
        self,
        request: AlbaranCompraRequest,
        sentencias: AlbaranCompraStatements,
        cabecera: _Cabecera,
    ) -> list[_Linea]:
        if any(linea.tipo == "sin_vincular" for linea in request.lineas):
            # Error de CABECERA: corta antes de mirar las lineas.
            cabecera.almacen_sin_vincular = self._almacen_sin_vincular(request, sentencias, cabecera)
        catalogo = _Catalogo(self, request, sentencias, cabecera)

        fallos: list[FalloLinea] = []
        resueltas: list[_Linea] = []
        for indice, linea in enumerate(request.lineas):
            errores: list[_FalloDeLinea] = []
            base: _Linea | None = None
            try:
                base = catalogo.resolver_origen(indice, linea)
            except _FalloDeLinea as fallo:
                errores.append(fallo)
            try:
                paride = catalogo.resolver_partida(linea)
            except _FalloDeLinea as fallo:
                errores.append(fallo)
            if linea.precio < 0:
                errores.append(_FalloDeLinea(
                    "precio_negativo", "El precio no puede ser negativo: la devolucion va en la cantidad."
                ))
            if errores:
                fallos.extend(
                    FalloLinea(indice=indice, referencia_linea=linea.referencia_linea,
                               codigo=e.codigo, mensaje=e.mensaje)
                    for e in errores
                )
                continue
            assert base is not None
            base.paride = paride
            resueltas.append(base)
        if fallos:
            raise AlbaranCompraError(
                f"{len({f.indice for f in fallos})} linea(s) no validas: no se ha escrito nada.",
                codigo="lineas_no_validas",
                lineas=fallos,
            )
        catalogo.completar(resueltas)
        return resueltas

    def _almacen_sin_vincular(
        self,
        request: AlbaranCompraRequest,
        sentencias: AlbaranCompraStatements,
        cabecera: _Cabecera,
    ) -> tuple[int, int]:
        """R15 (H10, H13, M16): el del contrato o, sin el, el de la ficha de obra
        y, si falta, el unico `alm` de la obra."""
        if cabecera.contrato and _entero(cabecera.contrato.fila.get("almide")):
            fila = cabecera.contrato.fila
            return _entero(fila.get("almide")), _entero(fila.get("cenide"))
        _c, ficha = self._leer(request, sentencias.leer_almacen_de_obra(cabecera.obra.ide))
        if ficha and _entero(ficha[0][0]):
            return _entero(ficha[0][0]), _entero(ficha[0][1])
        _c, almacenes = self._leer(
            request, sentencias.leer_almacenes(cabecera.obra.ide, []), muchas=True
        )
        if len(almacenes) != 1:
            raise AlbaranCompraError(
                f"La obra no tiene almacen en su ficha y tiene {len(almacenes)} almacenes: no se "
                "puede decidir el de las lineas sin vincular (alta a mano).",
                codigo="almacen_de_obra_no_resuelto",
            )
        return _entero(almacenes[0][0]), _entero(almacenes[0][2])

    # ------------------------------------------------------------------ #
    # Construccion pura de las filas (R12-R22)
    # ------------------------------------------------------------------ #
    def _construir(
        self,
        request: AlbaranCompraRequest,
        cabecera: _Cabecera,
        lineas: Sequence[_Linea],
        sellos: SellosAlbaran,
        vigentes: Mapping[tuple[int, int], tuple[float, float]],
    ) -> _Construido:
        dcapro: list[dict[str, Any]] = []
        ctrprodes: list[tuple[int, dict[str, Any]]] = []
        importes = []
        for linea in lineas:
            datos = linea.linea
            if linea.vinculada:
                fila = construir_dcapro_vinculada(
                    linea.plantilla,
                    indice=linea.indice,
                    ctrpro=linea.ctrpro,
                    referencia_linea=datos.referencia_linea,
                    cantidad=datos.cantidad,
                    precio=datos.precio,
                    descripcion=datos.descripcion,
                    unidad=datos.unidad,
                    cod_contrato=request.cod_contrato,
                    ctride=cabecera.ctride,
                    obride=cabecera.obra.ide,
                    almide=linea.almide,
                    cenide=linea.cenide,
                    paride=linea.paride,
                    iva=linea.iva,
                    prepma=0.0,
                )
                ctrprodes.append(
                    (linea.indice, construir_ctrprodes(ctrpro_ide=int(linea.ctrpro["ide"]),
                                                       cantidad=datos.cantidad))
                )
            else:
                fila = construir_dcapro_sin_vincular(
                    linea.plantilla,
                    indice=linea.indice,
                    proide=linea.proide,
                    referencia_linea=datos.referencia_linea,
                    cantidad=datos.cantidad,
                    precio=datos.precio,
                    descripcion=datos.descripcion or "",
                    unidad=datos.unidad,
                    natide=linea.natide,
                    cueide=linea.cueide,
                    caaide=linea.caaide,
                    obride=cabecera.obra.ide,
                    almide=linea.almide,
                    cenide=linea.cenide,
                    paride=linea.paride,
                    iva=linea.iva,
                    prepma=0.0,
                )
            # Importes del `pre` ESCRITO (opcion C): fila y totales coherentes.
            importes.append(importe_linea(datos.cantidad, fila["pre"], linea.iva))
            dcapro.append(fila)

        # R19: `mov` si y solo si `pro.tipmov` = 1, con el `pre` escrito; los
        # balances se encadenan por (producto, almacen) en el orden del albaran.
        con_mov = [linea for linea in lineas if linea.con_mov]
        balances = encadenar_balances(
            [(l.proide, l.almide, l.linea.cantidad, dcapro[l.indice]["pre"]) for l in con_mov],
            vigentes,
        )
        movimientos: list[tuple[int, dict[str, Any]]] = []
        for linea, balance in zip(con_mov, balances, strict=True):
            # R21: `dcapro.prepma` = el `prepma` de su `mov` (0 sin `mov`).
            dcapro[linea.indice]["prepma"] = balance.prepma
            movimientos.append((
                linea.indice,
                construir_mov(
                    emp=cabecera.obra.emp,
                    entide=cabecera.entide,
                    almide=linea.almide,
                    proide=linea.proide,
                    cantidad=linea.linea.cantidad,
                    pre=dcapro[linea.indice]["pre"],
                    balance=balance,
                    sellos=sellos,
                ),
            ))

        totales = sumar_importes(importes)
        almide, cenide = cabecera.almacen_cabecera
        con = construir_con(
            cabecera.con_plantilla, emp=cabecera.obra.emp, fec=sellos.fec,
            entres=cabecera.entres, su_referencia=request.su_referencia,
        )
        dca = construir_dca(
            cabecera.dca_plantilla,
            fec=sellos.fec,
            hor=sellos.hor,
            su_referencia=request.su_referencia,
            entidad=cabecera.entidad,
            ctride=cabecera.ctride,
            obride=cabecera.obra.ide,
            almide=almide,
            cenide=cenide,
            empide=request.empide or self._settings.sigrid_albaran_empide,
            totales=totales,
            referencia_externa=request.referencia_externa,
        )
        log = construir_log(emp=cabecera.obra.emp, usu=request.usu, res=con["res"], sellos=sellos)
        return _Construido(
            filas=FilasAlbaran(con=con, dca=dca, dcapro=dcapro, ctrprodes=ctrprodes,
                               mov=movimientos, log=log),
            balances={linea.indice: b for linea, b in zip(con_mov, balances, strict=True)},
            totales=totales,
        )

    @staticmethod
    def _pares_con_mov(lineas: Sequence[_Linea]) -> list[tuple[int, int]]:
        """(producto, almacen) de las lineas con `mov`, sin repetir y en orden."""
        return list(dict.fromkeys((l.proide, l.almide) for l in lineas if l.con_mov))

    # ------------------------------------------------------------------ #
    # Previa (R23)
    # ------------------------------------------------------------------ #
    def _previa(
        self,
        request: AlbaranCompraRequest,
        sentencias: AlbaranCompraStatements,
        cabecera: _Cabecera,
        lineas: list[_Linea],
        sellos: SellosAlbaran,
    ) -> AlbaranCompraResponse:
        vigentes: dict[tuple[int, int], tuple[float, float]] = {}
        for proide, almide in self._pares_con_mov(lineas):
            _c, filas = self._leer(request, sentencias.leer_balance(proide, almide))
            if filas:
                vigentes[(proide, almide)] = (float(filas[0][0] or 0), float(filas[0][1] or 0))
        construido = self._construir(request, cabecera, lineas, sellos, vigentes)

        # L14: el cod y los ide de la previa, sin reservar.
        _c, maximo = self._leer(request, sentencias.ultimo_cod(cabecera.obra.emp, sellos.prefijo))
        peek = {
            tabla: self._repo.peek_next_ide(database=request.database, table=tabla)
            for tabla in ("con", "dcapro", "ctrprodes", "mov", "log")
        }
        filas = numerar(
            construido.filas,
            cod=siguiente_cod(sellos.prefijo, maximo[0][0] if maximo else None),
            ide_con=peek["con"],
            ide_dcapro=peek["dcapro"],
            ide_ctrprodes=peek["ctrprodes"],
            ide_mov=peek["mov"],
            ide_log=peek["log"],
        )
        return self._respuesta(
            request,
            cabecera,
            lineas,
            _Construido(filas=filas, balances=construido.balances, totales=construido.totales),
            estado="previsto",
            estados=self._estados_previstos(cabecera, lineas),
            avisos=[_aviso("cod_provisional", _AVISO_PROVISIONAL)],
        )

    @staticmethod
    def _estados_previstos(cabecera: _Cabecera, lineas: Sequence[_Linea]) -> dict[str, Any]:
        """R20 en la previa: las sumas leidas mas lo que servira el albaran. Sin
        vinculadas no se toca el contrato (H31)."""
        vinculadas = [l for l in lineas if l.vinculada]
        if not vinculadas or cabecera.contrato is None:
            return {}
        contrato = cabecera.contrato
        suma_can = sum(float(l.get("can") or 0) for l in contrato.lineas.values())
        suma_canser = sum(float(l.get("canser") or 0) for l in contrato.lineas.values())
        suma_canfac = sum(float(l.get("canfac") or 0) for l in contrato.lineas.values())
        servido = sum(l.linea.cantidad for l in vinculadas)
        return _estados(contrato.fila, suma_can, suma_canser + servido, suma_canfac, servido)

    # ------------------------------------------------------------------ #
    # Respuesta (R7)
    # ------------------------------------------------------------------ #
    def _respuesta(
        self,
        request: AlbaranCompraRequest,
        cabecera: _Cabecera,
        lineas: Sequence[_Linea],
        construido: _Construido,
        *,
        estado: str,
        estados: dict[str, Any],
        avisos: list[AvisoAlbaran],
    ) -> AlbaranCompraResponse:
        filas = construido.filas
        resultado: list[LineaResultado] = []
        for linea in lineas:
            fila = filas.dcapro[linea.indice]
            balance = construido.balances.get(linea.indice)
            avisos_linea = list(linea.avisos)
            if balance is not None and balance.almcan < 0:
                avisos_linea.append(_aviso(
                    "stock_negativo",
                    f"El movimiento deja el stock del producto {linea.proide} en el almacen "
                    f"{linea.almide} en negativo: se admite.",
                ))
            ctrpro_ide = int(linea.ctrpro["ide"]) if linea.ctrpro else 0
            resultado.append(
                LineaResultado(
                    indice=linea.indice,
                    referencia_linea=linea.linea.referencia_linea,
                    tipo=linea.linea.tipo,
                    ctrpro_ide=ctrpro_ide,
                    linoriide=ctrpro_ide,
                    proide=linea.proide,
                    producto=linea.producto,
                    res=fila.get("res"),
                    unimed=fila.get("unimed"),
                    cantidad=fila["can"],
                    precio=fila["pre"],
                    total=fila["tot"],
                    iva_cuota=fila["ivacuo"],
                    almide=linea.almide,
                    cenide=linea.cenide,
                    paride=linea.paride,
                    partida=linea.linea.partida,
                    stock_anterior=balance.stock_anterior if balance else None,
                    stock_resultante=balance.almcan if balance else None,
                    pmp_anterior=balance.pmp_anterior if balance else None,
                    pmp_resultante=balance.almpma if balance else None,
                    avisos=avisos_linea,
                )
            )
        almide, _cenide = cabecera.almacen_cabecera
        return AlbaranCompraResponse(
            database=request.database,
            committed=estado == "creado",
            dry_run=not request.commit,
            con_ide=int(filas.con["ide"]),
            cod=str(filas.con["cod"]),
            contrato={
                "ctride": cabecera.ctride,
                "obride": cabecera.obra.ide,
                "cod_contrato": request.cod_contrato,
                "cod_obra": request.cod_obra,
                "cif_proveedor": request.cif_proveedor,
                "entide": cabecera.entide,
                "almide": almide,
                "template_ide": cabecera.template_ide,
            },
            cabecera=filas.dca,
            lineas=resultado,
            movimientos=[fila for _i, fila in filas.mov],
            estados_contrato=estados,
            totales={
                **construido.totales,
                "n_lineas": len(filas.dcapro),
                "n_vinculadas": len(filas.ctrprodes),
                "n_movimientos": len(filas.mov),
            },
            estado=estado,
            referencia_externa=request.referencia_externa,
            avisos=avisos,
            filas=filas.como_dict(),
        )


def _estados(
    ctr: Mapping[str, Any], suma_can: float, suma_canser: float, suma_canfac: float, servido: float
) -> dict[str, Any]:
    estser, estfac = estados_contrato(suma_can, suma_canser, suma_canfac)
    return {
        "estser_before": _entero(ctr.get("estser")),
        "estfac_before": _entero(ctr.get("estfac")),
        "estser_after": estser,
        "estfac_after": estfac,
        "sum_can": _r2(suma_can),
        "sum_canser_before": _r2(suma_canser - servido),
        "sum_canser_after": _r2(suma_canser),
        "sum_canfac": _r2(suma_canfac),
    }


class _Catalogo:
    """
    Lo que se lee UNA vez para validar las lineas (partidas, productos,
    naturalezas, cuentas y analiticas: L6, L7, L15a-c) y, ya validadas, lo que
    completa sus filas (L7b, L8/L8b, L9). Cada lectura de lista va con todos los
    codigos de la peticion a la vez.
    """

    def __init__(
        self,
        caso: CreateAlbaranCompraUseCase,
        request: AlbaranCompraRequest,
        sentencias: AlbaranCompraStatements,
        cabecera: _Cabecera,
    ) -> None:
        self._caso = caso
        self._request = request
        self._s = sentencias
        self._cab = cabecera
        settings = caso._settings
        self._lista_blanca: list[str] = list(settings.sigrid_albaran_productos_sin_contrato)
        self._mapeo: dict[str, str] = dict(settings.sigrid_albaran_naturaleza_por_producto)
        lineas = request.lineas
        self._partidas = self._agrupar(
            self._s.leer_partidas, [l.partida for l in lineas if l.partida], cabecera.obra.ide, 1
        )
        permitidos = [
            l.producto for l in lineas if l.producto is not None and l.producto in self._lista_blanca
        ]
        self._productos = self._agrupar(self._s.leer_productos, permitidos, cabecera.obra.emp, 1)
        self._naturalezas = self._leer_naturalezas(permitidos)

    # --- lecturas de lista -----------------------------------------------------
    def _agrupar(
        self, metodo: Callable[..., tuple[str, list[Any]]], codigos: Sequence[str], prefijo: Any,
        columna: int,
    ) -> dict[str, list[tuple[Any, ...]]]:
        """Una lectura con todos los `codigos` (sin repetir); filas por clave."""
        unicos = list(dict.fromkeys(codigos))
        if not unicos:
            return {}
        argumentos = (unicos,) if prefijo is None else (prefijo, unicos)
        _c, filas = self._caso._leer(self._request, metodo(*argumentos), muchas=True)
        agrupadas: dict[str, list[tuple[Any, ...]]] = {}
        for fila in filas:
            agrupadas.setdefault(_clave(fila[columna]), []).append(fila)
        return agrupadas

    def _leer_naturalezas(self, productos: Sequence[str]) -> dict[str, tuple[int, int, int] | str]:
        """
        R13b (H34): producto -> `(natide, cueide, caaide)` o el codigo del fallo.
        Naturaleza = la del mapeo, UNA `auxpronat` con ese `cod`, sin baja y
        `numemp` en {0, empresa}; cuenta = la UNICA `cua` de su `cuacomcod` en
        la empresa; analitica = la `caa` `<obra>.<sufijo>` del centro (R15).
        """
        emp = self._cab.obra.emp
        mapeados = {p: self._mapeo[p] for p in productos if p in self._mapeo}
        filas = self._agrupar(self._s.leer_naturalezas, list(mapeados.values()), None, 1)
        validas: dict[str, tuple[Any, ...]] = {}
        for producto, cod in mapeados.items():
            candidatas = [
                f for f in filas.get(_clave(cod), [])
                if not _entero(f[3]) and _entero(f[2]) in (0, emp)
            ]
            if len(candidatas) == 1 and str(candidatas[0][5] or "").strip():
                validas[producto] = candidatas[0]
        cuentas = self._agrupar(
            self._s.leer_cuentas, [str(f[5]).strip() for f in validas.values()], emp, 1
        )
        con_cuenta = {
            p: (f, cuentas[_clave(str(f[5]))][0][0])
            for p, f in validas.items() if len(cuentas.get(_clave(str(f[5])), [])) == 1
        }
        codigos_caa = {p: codigo_analitica(self._cab.obra.cod, f[4]) for p, (f, _) in con_cuenta.items()}
        analiticas = self._agrupar(
            self._s.leer_analiticas, [c for c in codigos_caa.values() if c], None, 1
        )
        centro = self._cab.almacen_sin_vincular[1] if self._cab.almacen_sin_vincular else None
        resultado: dict[str, tuple[int, int, int] | str] = {}
        for producto in productos:
            if producto not in con_cuenta:
                resultado[producto] = "naturaleza_no_valida"
                continue
            nat, cueide = con_cuenta[producto]
            codigo = codigos_caa[producto]
            caas = [
                f for f in analiticas.get(_clave(codigo), []) if _entero(f[2]) == centro
            ] if codigo else []
            resultado[producto] = (
                (int(nat[0]), int(cueide), int(caas[0][0])) if len(caas) == 1 else "analitica_no_resuelta"
            )
        return resultado

    # --- validacion de una linea -------------------------------------------------
    def resolver_origen(self, indice: int, linea: LineaAlbaranIn) -> _Linea:
        if linea.ctrpro_ide is not None:
            return self._vinculada(indice, linea)
        return self._sin_vincular(indice, linea)

    def _vinculada(self, indice: int, linea: LineaAlbaranIn) -> _Linea:
        contrato = self._cab.contrato
        ctrpro = contrato.lineas.get(linea.ctrpro_ide) if contrato else None
        if ctrpro is None:
            raise _FalloDeLinea(
                "linea_no_es_del_contrato",
                f"La linea de contrato {linea.ctrpro_ide} no es del contrato {self._request.cod_contrato}.",
            )
        ctr = contrato.fila
        return _Linea(
            indice=indice,
            linea=linea,
            proide=_entero(ctrpro.get("proide")),
            producto=None,
            ctrpro=ctrpro,
            paride=0,
            # R15: almacen y centro del ctrpro o, si no los tiene, del contrato.
            almide=_entero(ctrpro.get("almide") or ctr.get("almide")),
            cenide=_entero(ctrpro.get("cenide") or ctr.get("cenide")),
            ivaide=_entero(ctrpro.get("ivaide")),
        )

    def _sin_vincular(self, indice: int, linea: LineaAlbaranIn) -> _Linea:
        producto = linea.producto or ""
        if producto not in self._lista_blanca:
            raise _FalloDeLinea(
                "producto_no_permitido",
                f"El producto '{producto}' no esta en SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO.",
            )
        filas = self._productos.get(_clave(producto), [])
        if not filas or _entero(filas[0][2]):
            raise _FalloDeLinea(
                "producto_no_encontrado",
                f"El producto '{producto}' no existe o esta de baja en la empresa de la obra.",
            )
        naturaleza = self._naturalezas[producto]
        if naturaleza == "naturaleza_no_valida":
            raise _FalloDeLinea(
                "naturaleza_no_valida",
                f"La naturaleza del producto '{producto}' (SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO) "
                "no existe, esta de baja, es de otra empresa o su cuenta no es unica.",
            )
        if naturaleza == "analitica_no_resuelta":
            raise _FalloDeLinea(
                "analitica_no_resuelta",
                f"La obra no tiene la cuenta analitica de la naturaleza del producto '{producto}' "
                "en su centro: alta a mano.",
            )
        natide, cueide, caaide = naturaleza
        almide, cenide = self._cab.almacen_sin_vincular or (0, 0)
        return _Linea(
            indice=indice,
            linea=linea,
            proide=int(filas[0][0]),
            producto=producto,
            ctrpro=None,
            paride=0,
            almide=almide,
            cenide=cenide,
            natide=natide,
            cueide=cueide,
            caaide=caaide,
            tipmov=_entero(filas[0][3]),
        )

    def resolver_partida(self, linea: LineaAlbaranIn) -> int:
        """R14, R14b: la partida entre las IMPUTABLES de la obra (`tip` 1,
        `tipdes` 0, `tipvis` 0/1; no se exige hoja) o 0 sin partida, nunca la
        del `ctrpro` ni la de otra linea."""
        if linea.partida is None:
            return 0
        filas = self._partidas.get(_clave(linea.partida), [])
        imputables = [
            f for f in filas
            if _entero(f[2]) == 1 and not _entero(f[3]) and _entero(f[4]) in (0, 1)
        ]
        if linea.paride is not None:
            if any(int(f[0]) == linea.paride for f in imputables):
                return linea.paride
            raise _FalloDeLinea(
                "paride_no_valido",
                f"La partida {linea.paride} no es una imputable de la obra con el codigo '{linea.partida}'.",
            )
        if not filas:
            raise _FalloDeLinea(
                "partida_no_encontrada", f"La obra no tiene ninguna partida '{linea.partida}'."
            )
        if not imputables:
            raise _FalloDeLinea(
                "partida_no_imputable", f"La partida '{linea.partida}' de la obra no es imputable."
            )
        if len(imputables) > 1:
            raise _FalloDeLinea(
                "partida_ambigua",
                f"Hay {len(imputables)} partidas imputables '{linea.partida}' en la obra: indica paride.",
            )
        return int(imputables[0][0])

    # --- lo que completa las filas de las lineas validas ---------------------------------
    def completar(self, lineas: Sequence[_Linea]) -> None:
        caso, request, s = self._caso, self._request, self._s
        vinculadas = [l for l in lineas if l.vinculada]
        if vinculadas:
            # L7b: `mov` si y solo si `pro.tipmov` = 1 (R19).
            proides = list(dict.fromkeys(l.proide for l in vinculadas))
            _c, filas = caso._leer(request, s.leer_tipmov(proides), muchas=True)
            tipmov = {int(f[0]): _entero(f[1]) for f in filas}
            for linea in vinculadas:
                linea.tipmov = tipmov.get(linea.proide, 0)

        plantillas: dict[tuple[int, bool], dict[str, Any] | None] = {}
        for linea in lineas:
            self._plantilla_de_linea(linea, plantillas)

        ivaides = list(dict.fromkeys(l.ivaide for l in lineas if l.ivaide))
        tasas: dict[int, float] = {}
        if ivaides:
            _c, filas = caso._leer(request, s.leer_tasas_iva(ivaides), muchas=True)
            tasas = {int(f[0]): float(f[1] or 0) for f in filas}
        for linea in lineas:
            if linea.ivaide and linea.ivaide not in tasas:
                raise ValueError(f"El IVA {linea.ivaide} de la linea {linea.indice} no esta en dbo.iva.")
            linea.iva = tasas.get(linea.ivaide, 0.0)
        self._avisos_de_contrato(lineas)

    def _plantilla_de_linea(
        self, linea: _Linea, cache: dict[tuple[int, bool], dict[str, Any] | None]
    ) -> None:
        """Vinculada: L8, como hoy. Sin vincular (H15, M11): L8b del mismo
        proveedor o, sin ella, L8 con aviso; de ella solo vale el `ivaide`."""
        def leer(sentencia: tuple[str, list[Any]], clave: tuple[int, bool]) -> dict[str, Any] | None:
            if clave not in cache:
                columnas, filas = self._caso._leer(self._request, sentencia)
                cache[clave] = dict(zip(columnas, filas[0])) if filas else None
            return cache[clave]

        plantilla = None
        if not linea.vinculada:
            plantilla = leer(
                self._s.leer_plantilla_linea_del_proveedor(linea.proide, self._cab.entide),
                (linea.proide, True),
            )
        if plantilla is None:
            plantilla = leer(self._s.leer_plantilla_linea(linea.proide), (linea.proide, False))
            if plantilla is not None and not linea.vinculada:
                linea.avisos.append(_aviso(
                    "iva_de_otro_proveedor",
                    f"El producto {linea.producto} no tiene lineas previas de este proveedor: "
                    "IVA de la ultima de otro.",
                ))
        if plantilla is None:
            linea.avisos.append(_aviso(
                "producto_sin_historico",
                f"El producto {linea.proide} no tiene lineas previas de albaran: cuenta e IVA a 0.",
            ))
        linea.plantilla = plantilla
        if not linea.vinculada:
            linea.ivaide = _entero((plantilla or {}).get("ivaide"))

    def _avisos_de_contrato(self, lineas: Sequence[_Linea]) -> None:
        """R16, R17 y el seguimiento del `ctrpro`, en el orden de las lineas.
        Lo servido se ACUMULA por `ctrpro` dentro del albaran."""
        servido: dict[int, float] = {}
        for linea in lineas:
            ctrpro = linea.ctrpro
            if ctrpro is None:
                continue
            datos = linea.linea
            paride_contrato = _entero(ctrpro.get("paride"))
            propios: list[AvisoAlbaran] = []
            if datos.partida is not None and linea.paride != paride_contrato:
                propios.append(_aviso(
                    "partida_distinta_del_contrato",
                    "La partida pedida no es la de la linea de contrato: se escribe la pedida y "
                    "el contrato no se toca.",
                ))
            if datos.partida is None and paride_contrato:
                propios.append(_aviso(
                    "sin_partida_en_linea_con_partida",
                    "La linea va sin partida y la de contrato tiene partida.",
                ))
            # La MISMA regla que decide la fila (opcion C).
            if not usa_precio_del_contrato(datos.cantidad, datos.precio, ctrpro.get("pre") or 0):
                propios.append(_aviso(
                    "precio_distinto_del_contrato",
                    "El precio no es el de la linea de contrato: se escribe el pedido.",
                ))
            ide = int(ctrpro["ide"])
            servido[ide] = servido.get(ide, 0.0) + datos.cantidad
            pendiente = _r2(ctrpro.get("can")) - _r2(ctrpro.get("canser"))
            if datos.cantidad > 0 and servido[ide] > pendiente + 1e-9:
                propios.append(_aviso(
                    "supera_pendiente",
                    f"Lo servido de la linea de contrato {ide} en este albaran supera lo pendiente.",
                ))
            if datos.cantidad < 0 and _r2(float(ctrpro.get("canser") or 0) + servido[ide]) < 0:
                propios.append(_aviso(
                    "servido_negativo",
                    f"La devolucion deja lo servido de la linea de contrato {ide} en negativo: se admite.",
                ))
            linea.avisos[:0] = propios
