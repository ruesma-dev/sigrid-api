# tests/test_f009_mutacion.py
"""
F-009 · T16: tests que cierran los supervivientes de la campaña de mutación
(`progress/mutacion_F-009.md`). Cada uno fija un comportamiento de la spec que
ningún test fijaba todavía; el mutante que mata cada uno va en su docstring con
su línea (las de `92bf606`).

Sin red y sin base de datos: los dobles de `f009_dobles.py`.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

import pytest
from f009_dobles import (
    AHORA,
    CTR,
    ENTIDE,
    OBRA,
    RepositorioDoble,
    SettingsDoble,
    ctrpro,
)

from application.use_cases.albaran_compra_statements import (
    L6_PARTIDAS,
    MOV_COLUMNAS,
    AlbaranCompraStatements,
    FilasAlbaran,
    construir_dcapro_vinculada,
    encadenar_balances,
    estados_contrato,
    siguiente_balance,
)
from application.use_cases.create_albaran_compra_use_case import (
    CreateAlbaranCompraUseCase,
    _Construido,
    _Contrato,
    _Obra,
)
from domain.models.albaran_compra_models import AlbaranCompraError, AlbaranCompraRequest

_LOGGER = "application.use_cases.create_albaran_compra_use_case"


def vinculada(ref: str = "L1", ctrpro_ide: int = 9001, **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "ctrpro_ide": ctrpro_ide, "cantidad": 2.0, "precio": 10.5,
            **extra}


def sin_vincular(ref: str = "L2", producto: str = "MA9999", **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "producto": producto, "descripcion": "Arena de rio",
            "unidad": "m3", "cantidad": 3.0, "precio": 2.675, **extra}


def peticion(lineas: list[dict[str, Any]] | None = None, **cambios: Any) -> AlbaranCompraRequest:
    base = {
        "database": "ruesma", "cod_obra": "0404", "usu": "prueba",
        "cif_proveedor": "B12345678", "referencia_externa": "ALB-1",
        "cod_contrato": "CTSU16/0206", "su_referencia": "A-77", "fecha_albaran": 20261005,
        "lineas": lineas if lineas is not None else [vinculada()],
    }
    return AlbaranCompraRequest.model_validate({**base, **cambios})


def ejecutar(
    lineas: list[dict[str, Any]] | None = None,
    *,
    repo: RepositorioDoble | None = None,
    settings: SettingsDoble | None = None,
    reloj: Any = None,
    **cambios: Any,
) -> tuple[Any, RepositorioDoble]:
    repo = repo or RepositorioDoble()
    extra = {"reloj": reloj} if reloj is not None else {}
    caso = CreateAlbaranCompraUseCase(repo, settings or SettingsDoble(), ahora_utc=lambda: AHORA,
                                      **extra)
    return caso.run(peticion(lineas, **cambios)), repo


def error(lineas: list[dict[str, Any]] | None = None, **kwargs: Any) -> AlbaranCompraError:
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(lineas, **kwargs)
    return excinfo.value


def avisos(linea: Any) -> list[str]:
    return [a.codigo for a in linea.avisos]


def contrato_con(**cambios_por_ide: dict[str, Any]) -> list[dict[str, Any]]:
    """Las líneas de contrato de los dobles con cambios por `ide` (`l9001={...}`)."""
    cambios = {int(clave.removeprefix("l")): valor for clave, valor in cambios_por_ide.items()}
    return [{**fila, **cambios.get(fila["ide"], {})} for fila in ctrpro()]


# =====================================================================================
# Funciones puras (albaran_compra_statements)
# =====================================================================================


def test_f009_r19_el_epsilon_del_stock_es_estricto() -> None:
    """R19: «= 0» es |stock + can| < ε. Un stock de EXACTAMENTE ε no es cero: se
    calcula el PMP. Mata `abs(almcan) < EPSILON_STOCK` -> `<=` (l. 284)."""
    balance = siguiente_balance((0.0, 5.0), 1e-6, 7.0)
    assert balance.almcan == 1e-6
    assert balance.almpma == pytest.approx(7.0)


def test_f009_r19_epsilon_de_punta_a_punta_por_el_caso_de_uso() -> None:
    """O4 del lote C: el residuo binario de 0,3 − 0,1 − 0,2 (5,55e-17) llega al
    `mov` como stock 0 con el PMP conservado, a través del caso de uso."""
    repo = RepositorioDoble({"balance": lambda p: [(0.3, 9.0)] if (p[0], p[1]) == (55, 70) else []})
    respuesta, _ = ejecutar(
        [vinculada("A", cantidad=-0.1), vinculada("B", cantidad=-0.2)], repo=repo
    )
    primero, segundo = respuesta.filas["mov"]
    assert primero["almcan"] == pytest.approx(0.2) and primero["almpma"] == pytest.approx(8.25)
    assert segundo["almcan"] == 0.0 and segundo["almpma"] == primero["almpma"]
    assert respuesta.lineas[1].stock_resultante == 0.0


def test_f009_r19_encadenar_devuelve_un_balance_por_movimiento() -> None:
    """Invariante del que dependen los `zip` del caso de uso (RM6): un balance por
    movimiento, en su orden, se repitan o no los pares."""
    for n in range(12):
        movimientos = [(55 + i % 3, 70 + i % 2, float(i + 1) * (-1) ** i, 1.5 * i) for i in range(n)]
        assert len(encadenar_balances(movimientos, {(55, 70): (4.0, 2.0)})) == n


def test_f009_r20_una_suma_null_cuenta_como_cero() -> None:
    """R20: Σcan NULL (contrato sin líneas) es 0, y 0 ≥ 0. Mata `_r2`: `valor or 0`
    -> `or 1` (l. 330)."""
    assert estados_contrato(None, 0.0, 0.0) == (1, 1)


def _vinculada_pura(ctrpro_fila: dict[str, Any], **cambios: Any) -> dict[str, Any]:
    argumentos: dict[str, Any] = {
        "indice": 0, "ctrpro": ctrpro_fila, "referencia_linea": "L1", "cantidad": 2.0,
        "precio": 0.0, "descripcion": None, "unidad": None, "cod_contrato": "C", "ctride": 1,
        "obride": 2, "almide": 3, "cenide": 4, "paride": 0, "iva": 0.21, "prepma": 0.0,
    }
    return construir_dcapro_vinculada(None, **{**argumentos, **cambios})


def test_f009_r17_precio_null_del_ctrpro_es_cero_y_coincide_con_precio_cero() -> None:
    """R17/H14: un `ctrpro.pre` NULL vale 0; con `precio` 0 coincide y se toman
    `pre`, `tar` y `dto` del contrato. Mata `ctrpro.get("pre") or 0` -> `or 1` en la
    condición (l. 534) y en el `pre` (l. 535)."""
    fila = _vinculada_pura({"ide": 9, "proide": 5, "pre": None, "tar": None, "dto": "7"})
    assert (fila["pre"], fila["tar"], fila["dto"], fila["tot"]) == (0.0, 0.0, "7", 0.0)


def test_f009_r15_caaide_null_del_ctrpro_es_cero_y_sin_seguimiento_de_origen() -> None:
    """R15: `caaide` de la vinculada, el del `ctrpro`; NULL = 0. Y sin `can`/`tot`
    en el `ctrpro`, `canoriori`/`imporiori` 0. Mata `caaide ... or 0` -> `or 1`
    (l. 558) y `_r2` `or 0` -> `or 1` (l. 330)."""
    fila = _vinculada_pura({"ide": 9, "proide": 5, "pre": 1.0, "caaide": None}, precio=1.0)
    assert (fila["caaide"], fila["canoriori"], fila["imporiori"]) == (0, 0.0, 0.0)


def test_f009_r31_todas_las_sentencias_validan_los_in_con_un_solo_marcador() -> None:
    """R31: la validación al construir usa las `IN` con UN marcador. Mata
    `_marcadores(1)` -> `_marcadores(2)` (l. 815)."""
    todas = AlbaranCompraStatements.todas_las_sentencias()
    assert L6_PARTIDAS.format(marcadores="(?)") in todas
    assert not any("(?, ?)" in sql for sql in todas)


def test_f009_r25_la_fila_fija_con_una_columna_cambiada_se_rechaza_con_su_nombre() -> None:
    """Las filas de columnas fijas: misma cantidad de columnas pero una distinta
    es un `ValueError` que nombra la que falta y la que sobra. Mata `or` -> `and`
    en `_insertar_fija` (l. 991), que la dejaría pasar."""
    fila = dict.fromkeys(MOV_COLUMNAS, 0)
    del fila["fechor"]
    fila["intrusa"] = 0
    with pytest.raises(ValueError, match=r"faltan \['fechor'\], sobran \['intrusa'\]"):
        AlbaranCompraStatements(database="ruesma").insertar_mov(fila)


def test_f009_r27_las_filas_y_los_datos_de_un_intento_son_inmutables() -> None:
    """R27 (reentrante): ni las filas de un intento ni lo resuelto de la cabecera
    se pueden reasignar. Mata `frozen=True` -> `False` en `FilasAlbaran`
    (statements l. 720) y en `_Obra`, `_Contrato` y `_Construido` (caso de uso
    l. 102, 109 y 175)."""
    filas = FilasAlbaran(con={}, dca={}, dcapro=[], ctrprodes=[], mov=[], log={})
    objetos: list[tuple[Any, str]] = [
        (filas, "con"),
        (_Obra(ide=1, emp=1, cod="0404"), "ide"),
        (_Contrato(ide=1, fila={}, lineas={}), "ide"),
        (_Construido(filas=filas, balances={}, totales={}), "totales"),
    ]
    for objeto, campo in objetos:
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(objeto, campo, None)


# =====================================================================================
# Modelos: los mínimos de longitud y los enteros estrictos son los del contrato §2
# =====================================================================================


def test_f009_r5_un_caracter_basta_en_cada_texto_y_uno_en_cada_entero() -> None:
    """Contrato §2: `min_length=1` y `ge=1`. Mata `min_length=1` -> `2` en
    `database`, `cod_obra`, `usu`, `cif_proveedor`, `referencia_externa`,
    `cod_contrato`, `producto` y `partida`, y `ge=1` -> `2` en `paride` y `empide`."""
    modelo = AlbaranCompraRequest.model_validate({
        "database": "r", "cod_obra": "4", "usu": "u", "cif_proveedor": "B",
        "referencia_externa": "A", "cod_contrato": "C", "empide": 1,
        "lineas": [
            {"referencia_linea": "1", "ctrpro_ide": 1, "cantidad": 1.0, "precio": 1.0,
             "partida": "P", "paride": 1},
            {"referencia_linea": "2", "producto": "M", "descripcion": "d", "cantidad": 1.0,
             "precio": 1.0},
        ],
    })
    assert (modelo.database, modelo.cod_obra, modelo.usu, modelo.cif_proveedor) == ("r", "4", "u", "B")
    assert (modelo.referencia_externa, modelo.cod_contrato, modelo.empide) == ("A", "C", 1)
    assert (modelo.lineas[0].partida, modelo.lineas[0].paride, modelo.lineas[1].producto) == ("P", 1, "M")


def test_f009_r14b_paride_como_texto_no_cuela() -> None:
    """`paride` es un entero JSON (`strict`). Mata `strict=True` -> `False` (l. 220)."""
    with pytest.raises(ValueError, match="paride"):
        AlbaranCompraRequest.model_validate({
            "database": "r", "cod_obra": "4", "usu": "u", "cif_proveedor": "B",
            "referencia_externa": "A", "cod_contrato": "C",
            "lineas": [{"referencia_linea": "1", "ctrpro_ide": 1, "cantidad": 1.0,
                        "precio": 1.0, "partida": "P", "paride": "5"}],
        })


# =====================================================================================
# Caso de uso: lecturas acotadas (truncado, `_leer`)
# =====================================================================================


def _max_rows(repo: RepositorioDoble) -> dict[str, set[Any]]:
    vistos: dict[str, set[Any]] = {}
    for tipo, datos in repo.llamadas:
        if tipo == "leer":
            vistos.setdefault(datos[0], set()).add(datos[2])
    return vistos


_TOPE = SettingsDoble().max_allowed_rows
_LISTAS = {"partidas", "productos", "naturalezas", "cuentas", "analiticas", "tipmov", "iva",
           "almacenes", "lineas_del_existente"}


def test_f009_r9_las_lecturas_de_lista_piden_el_tope_y_las_de_una_fila_no() -> None:
    """Las lecturas que traen una lista piden `max_allowed_rows` (y un truncado
    aborta); las de una fila, el defecto. Mata `muchas=True` -> `False` en
    partidas/productos/naturalezas/cuentas/analíticas (l. 1066), `tipmov`
    (l. 1228), `iva` (l. 1240), almacenes (l. 718) y líneas del existente
    (l. 256), y el defecto `muchas: bool = False` -> `True` (l. 313)."""
    vistos: dict[str, set[Any]] = {}
    sin_almacen = RepositorioDoble({"almacen_de_obra": [], "almacenes": [(73, OBRA, 80)]})
    for repo, lineas, cambios in (
        (RepositorioDoble(), [vinculada(partida="01.01"), sin_vincular()], {}),
        (sin_almacen, [sin_vincular()], {"cod_contrato": None}),
        (RepositorioDoble({"referencia": [(2800001, "AC26/1", 20261001, ENTIDE, OBRA, 1.0, 1.0)],
                           "lineas_del_existente": [(64, 55, 2.0, 10.5, 21.0, 0, 70, "L1")]}),
         [vinculada()], {}),
    ):
        ejecutar(lineas, repo=repo, **cambios)
        for clave, valores in _max_rows(repo).items():
            vistos.setdefault(clave, set()).update(valores)
    assert _LISTAS <= set(vistos)
    for clave, valores in vistos.items():
        assert valores == ({_TOPE} if clave in _LISTAS else {None}), clave


# =====================================================================================
# Caso de uso: traza (R32)
# =====================================================================================


class _Reloj:
    def __init__(self, *marcas: float) -> None:
        self.marcas = list(marcas)

    def __call__(self) -> float:
        return self.marcas.pop(0)


def test_f009_r32_duracion_con_un_decimal_y_textos_sin_escapar(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """R32: `duracion_ms` con un decimal y la traza en UTF-8 legible (la
    referencia con `ñ` sale tal cual, no como `\\u00f1`). Mata `round(..., 1)` ->
    `2` (l. 240) y `ensure_ascii=False` -> `True` (l. 241)."""
    with caplog.at_level(logging.DEBUG, logger=_LOGGER):
        ejecutar(reloj=_Reloj(100.0, 100.0123456), referencia_externa="ALB-ñ1")
    mensajes = [r.getMessage() for r in caplog.records if r.name == _LOGGER]
    assert len(mensajes) == 1
    assert "ALB-ñ1" in mensajes[0]
    assert json.loads(mensajes[0])["duracion_ms"] == 12.3


# =====================================================================================
# Caso de uso: NULL de Sigrid que valen 0
# =====================================================================================


def test_f009_r30_idempotente_con_nulos_en_lo_leido() -> None:
    """R30/H18: lo LEÍDO de Sigrid con NULL en cantidades e importes vale 0.
    Mata `can or 0`, `pre or 0`, `tot or 0` (l. 508-510) y `totbas or 0`/`totdoc
    or 0` (l. 517) -> `or 1`."""
    repo = RepositorioDoble({
        "referencia": [(2800001, "AC26/1", 20261001, ENTIDE, OBRA, None, None)],
        "lineas_del_existente": [(64, 55, None, None, None, 0, 70, "L1")],
    })
    respuesta, _ = ejecutar(repo=repo)
    linea = respuesta.lineas[0]
    assert (linea.cantidad, linea.precio, linea.total) == (0.0, 0.0, 0.0)
    assert respuesta.totales == {"totbas": 0.0, "totdoc": 0.0, "n_lineas": 1}


def test_f009_r19_balance_vigente_con_nulos_es_cero_en_previa_y_en_commit() -> None:
    """R19: un `mov` anterior con `almcan`/`almpma` NULL es stock y PMP 0. Mata
    `fila[0] or 0`/`fila[1] or 0` -> `or 1` en la previa (l. 864) y en el commit
    (l. 564)."""
    nulos = {"balance": lambda p: [(None, None)]}
    previa, _ = ejecutar(repo=RepositorioDoble(nulos))
    commit, _ = ejecutar(repo=RepositorioDoble(nulos), commit=True)
    for respuesta in (previa, commit):
        linea = respuesta.lineas[0]
        assert (linea.stock_anterior, linea.pmp_anterior) == (0.0, 0.0)
        assert linea.stock_resultante == 2.0 and linea.pmp_resultante == 10.5


def test_f009_r20_sumas_null_del_contrato_en_el_commit() -> None:
    """R20: E10 con sumas NULL cuenta 0. Mata `suma_can or 0` y `suma_canser or 0`
    -> `or 1` (l. 590)."""
    respuesta, _ = ejecutar(repo=RepositorioDoble(reservas={"sumas_contrato": (None, None, None)}),
                            commit=True)
    estados = respuesta.estados_contrato
    assert (estados["sum_can"], estados["sum_canser_after"], estados["sum_canfac"]) == (0.0, 0.0, 0.0)
    assert (estados["estser_after"], estados["estfac_after"]) == (1, 1)


def test_f009_r20_sumas_previstas_con_can_null_y_con_facturado() -> None:
    """R20 en la previa: `can` NULL de una línea de contrato es 0 y lo facturado
    se suma. Mata `can or 0` -> `or 1` (l. 900) y `canfac or 0` -> `and 0` (l. 902)."""
    repo = RepositorioDoble(ctrpro_filas=contrato_con(l9003={"can": None}, l9001={"canfac": 4.0}))
    respuesta, _ = ejecutar(repo=repo)
    estados = respuesta.estados_contrato
    assert (estados["sum_can"], estados["sum_canfac"]) == (110.0, 4.0)


def test_f009_r20_sumas_previstas_redondeadas_a_dos_decimales() -> None:
    """R20: las sumas del contrato, a 2 decimales como el clásico. Mata `_r2`
    `round(..., 2)` -> `3` del caso de uso (l. 88)."""
    repo = RepositorioDoble(ctrpro_filas=contrato_con(l9003={"can": 1.004}))
    respuesta, _ = ejecutar(repo=repo)
    assert respuesta.estados_contrato["sum_can"] == 111.0


def test_f009_r17_iva_null_es_tasa_cero() -> None:
    """R17: una tasa NULL de `dbo.iva` es 0. Mata `f[1] or 0` -> `or 1` (l. 1241)."""
    respuesta, _ = ejecutar(repo=RepositorioDoble({"iva": [(3, None), (4, 0.10)]}))
    assert respuesta.filas["dcapro"][0]["ivacuo"] == 0.0


def test_f009_r19_producto_sin_fila_en_pro_no_lleva_mov() -> None:
    """R19: `mov` si y solo si `pro.tipmov` = 1; un producto que L7b no devuelve
    no lo lleva. Mata `tipmov.get(proide, 0)` -> `1` (l. 1231)."""
    respuesta, _ = ejecutar(repo=RepositorioDoble({"tipmov": [(56, 1), (57, 0)]}))
    assert respuesta.filas["mov"] == []


def test_f009_r17_precio_null_del_ctrpro_y_precio_cero_no_avisan() -> None:
    """R17 en el aviso: `ctrpro.pre` NULL y `precio` 0 coinciden. Mata
    `ctrpro.get("pre") or 0` -> `or 1` del aviso (l. 1308)."""
    repo = RepositorioDoble(ctrpro_filas=contrato_con(l9001={"pre": None}))
    respuesta, _ = ejecutar([vinculada(precio=0.0)], repo=repo)
    assert "precio_distinto_del_contrato" not in avisos(respuesta.lineas[0])


# =====================================================================================
# Caso de uso: precio, conflicto, mensajes
# =====================================================================================


def test_f009_r17_precio_cero_es_valido() -> None:
    """R17: SOLO `precio` < 0 es `precio_negativo`; 0 vale. Mata `< 0` -> `< 1` y
    -> `<= 0` (l. 680)."""
    respuesta, _ = ejecutar([sin_vincular(precio=0.0)])
    assert respuesta.filas["dcapro"][0]["pre"] == 0.0


def test_f009_r30_el_conflicto_nombra_los_cod_de_los_albaranes() -> None:
    """R30: `referencia_en_conflicto` dice en qué albaranes está. Mata `f[1]` ->
    `f[2]` (l. 479)."""
    repo = RepositorioDoble({"referencia": [(1, "AC26/77 ", 20260101, 999, OBRA, 1.0, 1.0)]})
    exc = error(repo=repo)
    assert exc.codigo == "referencia_en_conflicto"
    assert "AC26/77." in str(exc)


def test_f009_r29_el_mensaje_nombra_los_prefijos_o_que_no_hay() -> None:
    """R29: el mensaje de `referencia_no_permitida` lista los prefijos admitidos,
    o dice que no hay. Mata `or 'ninguno configurado'` -> `and` (l. 282)."""
    con = error(settings=SettingsDoble(sigrid_albaran_prefijos_referencia=["ALB-", "OTRA-"]),
                referencia_externa="X-1")
    sin = error(settings=SettingsDoble(sigrid_albaran_prefijos_referencia=[]))
    assert "(ALB-, OTRA-)" in str(con)
    assert "(ninguno configurado)" in str(sin)


def test_f009_r13_la_sin_vincular_escribe_su_descripcion() -> None:
    """R13: `dcapro.res` de la sin vincular = `descripcion`. Mata
    `datos.descripcion or ""` -> `and ""` (l. 775)."""
    respuesta, _ = ejecutar([sin_vincular()])
    assert respuesta.filas["dcapro"][0]["res"] == "Arena de rio"


# =====================================================================================
# Caso de uso: avisos de seguimiento del contrato (R18)
# =====================================================================================


def test_f009_r18_una_positiva_tras_una_devolucion_no_avisa_servido_negativo() -> None:
    """R18: `servido_negativo` es de las devoluciones. Una positiva (0,5) tras una
    devolución que dejó lo servido en negativo no avisa. Mata `cantidad < 0` ->
    `< 1` (l. 1321)."""
    respuesta, _ = ejecutar([vinculada("A", cantidad=-30.0), vinculada("B", cantidad=0.5)])
    assert "servido_negativo" in avisos(respuesta.lineas[0])
    assert "servido_negativo" not in avisos(respuesta.lineas[1])


def test_f009_r18_supera_pendiente_tambien_con_cantidades_menores_que_uno() -> None:
    """Lo servido se acumula por `ctrpro`: 4,8 + 0,5 supera los 5 pendientes y
    avisa en la segunda. Mata `cantidad > 0` -> `> 1` (l. 1316)."""
    respuesta, _ = ejecutar([vinculada("A", 9002, cantidad=4.8, precio=3.0),
                             vinculada("B", 9002, cantidad=0.5, precio=3.0)])
    assert "supera_pendiente" not in avisos(respuesta.lineas[0])
    assert "supera_pendiente" in avisos(respuesta.lineas[1])


def test_f009_r18_servir_exactamente_lo_pendiente_no_avisa() -> None:
    """Servir justo lo pendiente (5 de 5), o lo pendiente más la tolerancia de
    1e-9, no supera. Mata `pendiente + 1e-9` -> `- 1e-9` y `>` -> `>=` (l. 1316)."""
    for cantidad in (5.0, 5.0 + 1e-9):
        respuesta, _ = ejecutar([vinculada("A", 9002, cantidad=cantidad, precio=3.0)])
        assert "supera_pendiente" not in avisos(respuesta.lineas[0]), cantidad


def test_f009_r18_servido_negativo_con_canser_null_y_en_la_frontera() -> None:
    """R18: `canser` NULL es 0 (devolver 1 deja −1: avisa); dejar lo servido en
    0,5 o en 0 no avisa. Mata `canser or 0` -> `or 1`, `< 0` -> `< 1` y `< 0` ->
    `<= 0` (l. 1321)."""
    casos = ((None, -1.0, True), (5.0, -4.5, False), (5.0, -5.0, False))
    for canser, cantidad, avisa in casos:
        repo = RepositorioDoble(ctrpro_filas=contrato_con(l9002={"canser": canser}))
        respuesta, _ = ejecutar([vinculada("A", 9002, cantidad=cantidad, precio=3.0)], repo=repo)
        assert ("servido_negativo" in avisos(respuesta.lineas[0])) is avisa, (canser, cantidad)


def test_f009_r16_los_avisos_del_contrato_van_delante_de_los_de_la_plantilla() -> None:
    """Los avisos de contrato se ANTEPONEN a los que la línea ya traía
    (`producto_sin_historico`), sin pisarlos. Mata `avisos[:0]` -> `[:1]` (l. 1326)."""
    repo = RepositorioDoble({"plantilla_linea": lambda p: []})
    respuesta, _ = ejecutar([vinculada(ctrpro_ide=9002, precio=11.0)], repo=repo)
    assert avisos(respuesta.lineas[0]) == ["precio_distinto_del_contrato", "producto_sin_historico"]


def test_f009_r20_el_contrato_de_los_dobles_es_el_esperado() -> None:
    """Control de los datos de los tests de arriba: si cambian los dobles, que
    falle aquí y no en un sitio que no lo explique."""
    filas = {f["ide"]: f for f in ctrpro()}
    assert (filas[9002]["can"], filas[9002]["canser"], filas[9002]["pre"]) == (10.0, 5.0, 3.0)
    assert sum(f["can"] for f in filas.values()) == 111.0 and CTR == 300
