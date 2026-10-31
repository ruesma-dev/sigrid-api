# application/use_cases/factura_lineas.py
"""
Funciones PURAS de las lineas y los vencimientos de `sigrid/factura` (F-008):
sin E/S, sin SQL. Las filas que salen de aqui son las de `dcfpro` por lista
blanca (`DCFPRO_COLUMNAS`, T0); `ide`, `docide` y `pos` los pone el
constructor de la factura al numerar.

- Vencimientos del llamante (R32-R35): se validan forma, rango y suma; nunca se
  calculan ni se comparan con `pagfor`, `pagdia` o `pagmes`.
- Linea de origen (R12, R17, R19, R20): copia de su `dcapro` sin recalcular,
  igual en FR y FRGG (M69), y comparacion con lo que manda el llamante a
  origen (R21, R22).
- Linea sin origen (R23-R28): dos resolvedores por serie que devuelven la MISMA
  `LineaResuelta` y UN constructor (`linea_sin_origen`) para las dos.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from application.use_cases.albaran_compra_statements import (
    codigo_analitica,
    importe_linea,
)
from domain.models.factura_models import (
    EntradaAOrigen,
    FacturaError,
    LineaSinOrigen,
    Vencimiento,
)

#: Las 73 columnas de `dbo.dcfpro`, en su orden fisico (T0). El `INSERT` lleva
#: estas y solo estas.
DCFPRO_COLUMNAS: tuple[str, ...] = (
    "ide", "docide", "proide", "pos", "pre", "can", "candes", "tar", "dto", "tot", "fec", "pla",
    "res", "tex", "cueide", "envide", "almide", "ivaide", "ivacuo", "reqcuo", "prepma", "lintip",
    "cenide", "caaide", "anades", "tardiv", "totdiv", "cod2", "refent", "garfec", "gardes", "unimed",
    "docoritip", "docoricod", "docoriide", "linoriide", "canser", "canfac", "cancan", "canorilin",
    "canoriant", "canoriori", "imporiant", "imporiori", "taride", "apuide", "cuoman", "dncide",
    "dncproide", "obride", "paride", "natide", "parcandes", "med", "canmed", "pac", "item", "desesp",
    "nueusa", "edilin", "texcom", "serdes", "serdesdat", "dvfproide", "anexo", "fecimp", "canped",
    "imporiantdiv", "imporioridiv", "totimpret", "ico", "ivaope", "vmg",
)
#: `varchar` (vacio `''`) y `text`/`image` que el alta deja en NULL (T0: 35 de 35).
_DCFPRO_TEXTO: frozenset[str] = frozenset({
    "dto", "res", "tex", "cod2", "refent", "unimed", "docoricod", "pac", "ico",
})
_DCFPRO_NULAS: frozenset[str] = frozenset({"med", "desesp", "texcom", "serdesdat"})
#: Las que pone la numeracion de la factura.
_DCFPRO_NUMERACION: tuple[str, ...] = ("ide", "docide", "pos")

#: R17: lo que la linea de origen copia de su `dcapro`, sin recalcular.
COPIADAS_DEL_ORIGEN: tuple[str, ...] = (
    "proide", "can", "pre", "tar", "dto", "tot", "ivaide", "ivacuo", "cenide", "caaide", "paride",
    "natide", "almide", "obride", "res", "tex", "cod2", "unimed", "prepma", "dncide", "dncproide",
)
#: `con.tip` del albaran o proforma de origen (R13, R17).
DOCORITIP_ALBARAN = 14
MODOS: tuple[str, ...] = ("mes", "origen")

#: R33: un vencimiento va como mucho 730 dias detras de la factura.
MAX_DIAS_VENCIMIENTO = 730
#: R33: Σ importes = `totpag` con un centimo de margen.
TOLERANCIA_VENCIMIENTOS = Decimal("0.01")


def _decimal(valor: float | Decimal) -> Decimal:
    """`Decimal` de lo que se ve (`repr` del float), como F-009."""
    return valor if isinstance(valor, Decimal) else Decimal(repr(valor))


def _fecha(aaaammdd: int) -> date | None:
    try:
        return date(aaaammdd // 10000, aaaammdd // 100 % 100, aaaammdd % 100)
    except ValueError:
        return None


def fecha_de_vencimiento_valida(fecha: int, *, fecha_factura: int) -> bool:
    """R33 (y R34): fecha real dentro de [`fecha_factura`, +730 dias]."""
    vence, factura = _fecha(fecha), _fecha(fecha_factura)
    if vence is None or factura is None:
        return False
    return factura <= vence <= factura + timedelta(days=MAX_DIAS_VENCIMIENTO)


def validar_vencimientos(
    vencimientos: Sequence[Vencimiento], *, fecha_factura: int, totpag: Decimal
) -> None:
    """R33: cada fecha real, en rango y sin repetir (`vencimiento_no_valido`
    con la primera posicion que falla); despues Σ `importe` = `totpag` ±0,01
    (`vencimientos_no_cuadran` con las dos cifras)."""
    vistas: set[int] = set()
    for posicion, vencimiento in enumerate(vencimientos):
        if (
            not fecha_de_vencimiento_valida(vencimiento.fecha, fecha_factura=fecha_factura)
            or vencimiento.fecha in vistas
        ):
            raise FacturaError(
                f"El vencimiento {posicion} no es una fecha real entre la de la factura y 730 "
                "dias despues, o repite otra.",
                codigo="vencimiento_no_valido",
                details={"posicion": posicion, "fecha": vencimiento.fecha},
            )
        vistas.add(vencimiento.fecha)
    suma = sum((_decimal(v.importe) for v in vencimientos), Decimal(0))
    if abs(suma - _decimal(totpag)) > TOLERANCIA_VENCIMIENTOS:
        raise FacturaError(
            f"Los vencimientos suman {suma} y la factura deja {totpag} por pagar.",
            codigo="vencimientos_no_cuadran",
            details={"suma_vencimientos": float(suma), "totpag": float(totpag)},
        )


# --------------------------------------------------------------------------- #
# Filas de `dcfpro` (T4, T6)
# --------------------------------------------------------------------------- #


def _vacio(columna: str) -> Any:
    if columna in _DCFPRO_NULAS:
        return None
    return "" if columna in _DCFPRO_TEXTO else 0


def fila_dcfpro(valores: Mapping[str, Any]) -> dict[str, Any]:
    """La fila de `dcfpro` por lista blanca: `DCFPRO_COLUMNAS` menos la
    numeracion, con lo que trae `valores` y el vacio del tipo en el resto. Una
    columna que no es de `dcfpro` es un error de programacion."""
    ajenas = set(valores) - set(DCFPRO_COLUMNAS)
    if ajenas:
        raise ValueError(f"Columnas que no son de dcfpro: {sorted(ajenas)}.")
    return {
        columna: valores[columna] if columna in valores else _vacio(columna)
        for columna in DCFPRO_COLUMNAS
        if columna not in _DCFPRO_NUMERACION
    }


def _num(valor: Any) -> Decimal:
    return _decimal(float(valor or 0))


def linea_de_origen(
    dcapro: Mapping[str, Any],
    anterior: Mapping[str, Any] | None,
    *,
    modo: str,
    cueide: int,
    docoricod: str,
) -> dict[str, Any]:
    """
    R17: la linea de la factura copiada de su `dcapro` (de un albaran o una
    proforma), con `docoritip` 14, su `cod` y sus `ide` y `canorilin` 0; R12:
    `cueide` = `prv.cuepdtide`, en las dos series (M69). Columnas a origen
    (design §6): en mes (R19) `canoriori` = `can` e `imporiori` = `tot`; a
    origen (R20, M63) `canoriori` = el del `dcapro`, `canoriant`/`imporiant` =
    los de la `anterior` (la `dcapro` de su `canorilin`, o 0 sin ella) e
    `imporiori` = el del `dcapro` si esta vinculada (`linoriide` != 0) o
    `imporiant` + `tot` si no, sumado en `Decimal`.
    """
    if modo not in MODOS:
        raise ValueError(f"El modo '{modo}' no es de mes ni a origen.")
    valores: dict[str, Any] = {columna: dcapro[columna] for columna in COPIADAS_DEL_ORIGEN}
    if modo == "mes":
        a_origen = {"canoriori": dcapro["can"], "canoriant": 0, "imporiant": 0,
                    "imporiori": dcapro["tot"]}
    else:
        previa = anterior or {}
        canoriant = float(_num(previa.get("canoriori")))
        imporiant = float(_num(previa.get("imporiori")))
        vinculada = bool(dcapro.get("linoriide"))
        imporiori = (
            float(_num(dcapro.get("imporiori"))) if vinculada
            else float(_num(imporiant) + _num(dcapro["tot"]))
        )
        a_origen = {"canoriori": float(_num(dcapro.get("canoriori"))), "canoriant": canoriant,
                    "imporiant": imporiant, "imporiori": imporiori}
    valores.update(
        a_origen,
        cueide=cueide,
        docoritip=DOCORITIP_ALBARAN,
        docoricod=docoricod,
        docoriide=dcapro["docide"],
        linoriide=dcapro["ide"],
        canorilin=0,
    )
    return fila_dcfpro(valores)


#: R22: tolerancias de la comparacion a origen (P14).
TOLERANCIA_CANORIORI = Decimal("0.001")
TOLERANCIA_IMPORIORI = Decimal("0.01")


def comparar_a_origen(
    calculadas: Sequence[Mapping[str, Any]], enviadas: Sequence[EntradaAOrigen] | None
) -> None:
    """
    R21: UNA entrada de `a_origen` por linea facturada, casada por `linea` =
    `dcapro.ide` (el `linoriide` de la fila calculada); faltas, sobras o
    repetidas -> `a_origen_incompleto` con las tres listas. R22: `canoriori`
    a ±0,001 e `imporiori` a ±0,01 de lo calculado por M63; si no,
    `a_origen_no_cuadra` con cada linea que difiere y los dos juegos. Se
    escribe lo calculado (que, cuadrando, es lo enviado dentro de la tolerancia).
    """
    entradas = list(enviadas or [])
    esperadas = [int(fila["linoriide"]) for fila in calculadas]
    vistas: dict[int, int] = {}
    for entrada in entradas:
        vistas[entrada.linea] = vistas.get(entrada.linea, 0) + 1
    faltan = [linea for linea in esperadas if linea not in vistas]
    sobran = [linea for linea in vistas if linea not in esperadas]
    repetidas = [linea for linea, veces in vistas.items() if veces > 1]
    if faltan or sobran or repetidas:
        raise FacturaError(
            "a_origen no trae exactamente una entrada por linea facturada.",
            codigo="a_origen_incompleto",
            details={"faltan": faltan, "sobran": sobran, "repetidas": repetidas},
        )
    por_linea = {entrada.linea: entrada for entrada in entradas}
    distintas: list[dict[str, Any]] = []
    for fila in calculadas:
        entrada = por_linea[int(fila["linoriide"])]
        if (
            abs(_num(fila["canoriori"]) - _decimal(entrada.canoriori)) > TOLERANCIA_CANORIORI
            or abs(_num(fila["imporiori"]) - _decimal(entrada.imporiori)) > TOLERANCIA_IMPORIORI
        ):
            distintas.append({
                "linea": entrada.linea,
                "calculado": {"canoriori": fila["canoriori"], "imporiori": fila["imporiori"]},
                "enviado": {"canoriori": entrada.canoriori, "imporiori": entrada.imporiori},
            })
    if distintas:
        raise FacturaError(
            f"{len(distintas)} linea(s) a origen no cuadran con el albaran: no se ha escrito nada.",
            codigo="a_origen_no_cuadra",
            details={"lineas": distintas},
        )


# --------------------------------------------------------------------------- #
# Lineas sin origen: dos resolvedores, un constructor (T6, T7)
# --------------------------------------------------------------------------- #

#: Nivel de una cuenta hoja (`cua.niv`, M65).
NIVEL_CUENTA_HOJA = 5
SERIES: tuple[str, ...] = ("FR", "FRGG")

Fallo = tuple[str, str]


def clave(texto: Any) -> str:
    """Codigos comparados como el ERP (`Modern_Spanish_CI_AS`): sin mayusculas
    ni espacios alrededor."""
    return str(texto).strip().casefold()


@dataclass(frozen=True)
class LineaResuelta:
    """Lo que necesita `linea_sin_origen`, igual para las dos series. `almide`
    `None`: el de la cabecera (`dcf.almide`)."""

    proide: int
    natide: int
    paride: int
    cueide: int
    caaide: int
    obride: int
    cenide: int
    almide: int | None
    ivaide: int
    tasa_iva: float


@dataclass(frozen=True)
class LecturasLineas:
    """Lo leido UNA vez para resolver las lineas sin origen, por `clave`.

    Comunes: `ivas` (clave -> (`ide`, tasa)) de la empresa y la lista blanca.
    FRGG: `cuentas` (clave -> (`ide`, `niv`)), `prefijos_cuenta`, `analiticas`
    (clave -> (`ide`, hoja)) y `obras` (clave -> (`ide`, `obr.cenide`)).
    FR: la lista blanca de productos, `productos` (clave -> filas de L7 de
    F-009: `ide`, `cod`, `fecbaj`, `tipmov`), `naturalezas` (producto ->
    (`natide`, `cueide`, `caaide`) o el codigo del fallo), `partidas` (clave ->
    filas de L6 de F-009), la obra y el almacen y centro de F-009 R15.
    """

    ivas: Mapping[str, tuple[int, float]]
    ivas_permitidos: Sequence[str]
    cuentas: Mapping[str, tuple[int, int]] = field(default_factory=dict)
    prefijos_cuenta: Sequence[str] = ()
    analiticas: Mapping[str, tuple[int, bool]] = field(default_factory=dict)
    obras: Mapping[str, tuple[int, int]] = field(default_factory=dict)
    productos_permitidos: Sequence[str] = ()
    productos: Mapping[str, Sequence[Sequence[Any]]] = field(default_factory=dict)
    naturalezas: Mapping[str, tuple[int, int, int] | str] = field(default_factory=dict)
    partidas: Mapping[str, Sequence[Sequence[Any]]] = field(default_factory=dict)
    obride: int = 0
    almacen: tuple[int, int] | None = None


def resolver_iva(codigo: str, lecturas: LecturasLineas) -> tuple[tuple[int, float] | None, Fallo | None]:
    """R24: el IVA en `SIGRID_FACTURA_IVAS` y en `dbo.iva` de la empresa. Un NDED
    es uno mas (P21): solo cambia el `ivaide`."""
    permitidos = {clave(p) for p in lecturas.ivas_permitidos}
    leido = lecturas.ivas.get(clave(codigo))
    if clave(codigo) not in permitidos or leido is None:
        return None, ("iva_no_valido",
                      f"El IVA '{codigo}' no esta en SIGRID_FACTURA_IVAS o no existe en la empresa.")
    return leido, None


def resolver_linea_gg(
    linea: LineaSinOrigen, lecturas: LecturasLineas
) -> tuple[LineaResuelta | None, list[Fallo]]:
    """R26-R27 (M65, M66): `cuenta` hoja (`niv` 5) de la empresa con un prefijo
    de `SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS` (vacia: ninguno); `analitica`
    hoja de la empresa cuyo texto antes del primer `.` es una obra de la
    empresa, de la que salen `obride` y `cenide`. `proide`, `paride`, `natide`
    0 y `almide` el de la cabecera. Todos los fallos de la linea, juntos."""
    fallos: list[Fallo] = []
    iva, fallo = resolver_iva(linea.iva, lecturas)
    if fallo:
        fallos.append(fallo)
    cuenta = str(linea.cuenta or "")
    leida = lecturas.cuentas.get(clave(cuenta))
    if (
        leida is None
        or leida[1] != NIVEL_CUENTA_HOJA
        or not any(cuenta.strip().startswith(p) for p in lecturas.prefijos_cuenta)
    ):
        fallos.append(("cuenta_no_valida",
                       f"La cuenta '{cuenta}' no es una cuenta hoja de la empresa con un prefijo "
                       "de SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS."))
    analitica = str(linea.analitica or "")
    caa = lecturas.analiticas.get(clave(analitica))
    obra = lecturas.obras.get(clave(analitica.split(".")[0])) if "." in analitica else None
    if caa is None or not caa[1] or obra is None:
        fallos.append(("analitica_no_valida",
                       f"La analitica '{analitica}' no es una hoja de la empresa con la obra delante."))
    if fallos:
        return None, fallos
    # Sin fallos, todo resuelto: un `assert` por valor (y no una conjuncion, que
    # admite mutantes equivalentes) para que el tipo deje de ser opcional.
    assert iva is not None
    assert leida is not None
    assert caa is not None
    assert obra is not None
    return LineaResuelta(
        proide=0, natide=0, paride=0, cueide=leida[0], caaide=caa[0], obride=obra[0],
        cenide=obra[1], almide=None, ivaide=iva[0], tasa_iva=iva[1],
    ), []


def linea_sin_origen(
    linea: LineaSinOrigen, resuelta: LineaResuelta, *, serie: str, almide: int
) -> dict[str, Any]:
    """R27, R28: la fila de una linea sin origen, IGUAL en las dos series (la
    serie solo ha elegido el resolvedor): `pre` = `tar` = `precio`, `dto`
    vacio, `tot` = round(cantidad·precio, 2) e `ivacuo` = round(tot·iva, 2) en
    `Decimal` con `ROUND_HALF_UP` (F-009), origen y a origen a 0; `almide` el
    de la linea o, sin el, `almide` (el de `dcf`)."""
    if serie not in SERIES:
        raise ValueError(f"La serie '{serie}' no es FR ni FRGG.")
    tot, ivacuo = importe_linea(linea.cantidad, linea.precio, resuelta.tasa_iva)
    return fila_dcfpro({
        "proide": resuelta.proide,
        "pre": linea.precio,
        "can": linea.cantidad,
        "tar": linea.precio,
        "tot": float(tot),
        "res": linea.descripcion,
        "cueide": resuelta.cueide,
        "almide": resuelta.almide if resuelta.almide is not None else almide,
        "ivaide": resuelta.ivaide,
        "ivacuo": float(ivacuo),
        "cenide": resuelta.cenide,
        "caaide": resuelta.caaide,
        "unimed": linea.unidad or "",
        "obride": resuelta.obride,
        "paride": resuelta.paride,
        "natide": resuelta.natide,
    })


def _entero(valor: Any) -> int:
    return int(valor or 0)


def resolver_partida(
    linea: LineaSinOrigen, partidas: Mapping[str, Sequence[Sequence[Any]]]
) -> tuple[int | None, Fallo | None]:
    """F-009 R14, R14b: la partida entre las IMPUTABLES de la obra (`tip` 1,
    `tipdes` 0, `tipvis` 0/1), o 0 sin partida. Con `paride`, esa y solo esa."""
    if linea.partida is None:
        return 0, None
    filas = partidas.get(clave(linea.partida), [])
    imputables = [
        f for f in filas if _entero(f[2]) == 1 and not _entero(f[3]) and _entero(f[4]) in (0, 1)
    ]
    if linea.paride is not None:
        if any(int(f[0]) == linea.paride for f in imputables):
            return linea.paride, None
        return None, ("paride_no_valido",
                      f"La partida {linea.paride} no es una imputable de la obra con el codigo "
                      f"'{linea.partida}'.")
    if not filas:
        return None, ("partida_no_encontrada", f"La obra no tiene ninguna partida '{linea.partida}'.")
    if not imputables:
        return None, ("partida_no_imputable",
                      f"La partida '{linea.partida}' de la obra no es imputable.")
    if len(imputables) > 1:
        return None, ("partida_ambigua",
                      f"Hay {len(imputables)} partidas imputables '{linea.partida}' en la obra: "
                      "indica paride.")
    return int(imputables[0][0]), None


def naturalezas_validas(
    mapeados: Mapping[str, str], filas: Mapping[str, Sequence[Sequence[Any]]], *, emp: int
) -> dict[str, Sequence[Any]]:
    """F-009 R13b, paso 1: producto -> la UNICA `auxpronat` de su `cod` sin baja
    y con `numemp` en {0, empresa} y `cuacomcod` informado (filas de L15A)."""
    validas: dict[str, Sequence[Any]] = {}
    for producto, cod in mapeados.items():
        candidatas = [
            f for f in filas.get(clave(cod), []) if not _entero(f[3]) and _entero(f[2]) in (0, emp)
        ]
        if len(candidatas) == 1 and str(candidatas[0][5] or "").strip():
            validas[producto] = candidatas[0]
    return validas


def naturalezas_con_cuenta(
    validas: Mapping[str, Sequence[Any]], cuentas: Mapping[str, Sequence[Sequence[Any]]]
) -> dict[str, tuple[Sequence[Any], int]]:
    """Paso 2: la UNICA `cua` de su `cuacomcod` en la empresa (filas de L15C)."""
    return {
        producto: (fila, int(cuentas[clave(fila[5])][0][0]))
        for producto, fila in validas.items()
        if len(cuentas.get(clave(fila[5]), [])) == 1
    }


def naturalezas_resueltas(
    productos: Sequence[str],
    con_cuenta: Mapping[str, tuple[Sequence[Any], int]],
    analiticas: Mapping[str, Sequence[Sequence[Any]]],
    *,
    cod_obra: str,
    centro: int | None,
) -> dict[str, tuple[int, int, int] | str]:
    """Paso 3 (F-009 R15): la `caa` `<obra>.<sufijo>` del centro (filas de
    L15B). Producto -> (`natide`, `cueide`, `caaide`) o el codigo del fallo."""
    resultado: dict[str, tuple[int, int, int] | str] = {}
    for producto in productos:
        if producto not in con_cuenta:
            resultado[producto] = "naturaleza_no_valida"
            continue
        fila, cueide = con_cuenta[producto]
        codigo = codigo_analitica(cod_obra, fila[4])
        caas = [
            f for f in analiticas.get(clave(codigo), []) if _entero(f[2]) == centro
        ] if codigo else []
        resultado[producto] = (
            (int(fila[0]), cueide, int(caas[0][0])) if len(caas) == 1 else "analitica_no_resuelta"
        )
    return resultado


_MENSAJES_NATURALEZA = {
    "naturaleza_no_valida": "La naturaleza del producto (SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO) no "
                            "existe, esta de baja, es de otra empresa o su cuenta no es unica.",
    "analitica_no_resuelta": "La obra no tiene la cuenta analitica de la naturaleza del producto en "
                             "su centro: alta a mano.",
}


def resolver_linea_fr(
    linea: LineaSinOrigen, lecturas: LecturasLineas
) -> tuple[LineaResuelta | None, list[Fallo]]:
    """R25: producto de `SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN` que exista sin
    baja en la empresa (`tip 3`); naturaleza, cuenta (`cuacomcod`) y analitica
    por el mapeo de naturalezas; partida, almacen y centro con F-009 R13b, R14,
    R14b y R15 y sus mismos fallos. Todos los de la linea, juntos."""
    fallos: list[Fallo] = []
    iva, fallo = resolver_iva(linea.iva, lecturas)
    if fallo:
        fallos.append(fallo)
    producto = str(linea.producto or "")
    filas = lecturas.productos.get(clave(producto), [])
    naturaleza: tuple[int, int, int] | str | None = None
    if producto not in lecturas.productos_permitidos:
        fallos.append(("producto_no_permitido",
                       f"El producto '{producto}' no esta en SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN."))
    elif not filas or _entero(filas[0][2]):
        fallos.append(("producto_no_encontrado",
                       f"El producto '{producto}' no existe o esta de baja en la empresa de la obra."))
    else:
        naturaleza = lecturas.naturalezas.get(producto, "naturaleza_no_valida")
        if isinstance(naturaleza, str):
            fallos.append((naturaleza, _MENSAJES_NATURALEZA[naturaleza]))
    paride, fallo = resolver_partida(linea, lecturas.partidas)
    if fallo:
        fallos.append(fallo)
    if fallos:
        return None, fallos
    assert iva is not None
    assert isinstance(naturaleza, tuple)
    assert paride is not None
    assert lecturas.almacen is not None
    natide, cueide, caaide = naturaleza
    return LineaResuelta(
        proide=int(filas[0][0]), natide=natide, paride=paride, cueide=cueide, caaide=caaide,
        obride=lecturas.obride, cenide=lecturas.almacen[1], almide=lecturas.almacen[0],
        ivaide=iva[0], tasa_iva=iva[1],
    ), []
