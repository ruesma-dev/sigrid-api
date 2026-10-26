# tests/test_f007_statements_lineas.py
"""
F-007 T10 · R12-R14, R16, R18-R22, R24: funciones puras de las lineas, la
fecha, las comprobaciones de la hoja, lo registrado en Sigrid, la proforma del
mes y la traduccion a la peticion del nucleo de F-009.

Datos: las hojas de agosto de 2026 de la obra 0719 (M29) de
`tests/fixtures/f007_obra0719.json`. Sin red ni base de datos.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from application.use_cases.proforma_statements import (
    ContratoCandidato,
    FalloIdentificacion,
    LineaContrato,
    ProformaRegistrada,
    anterior_por_linea,
    anterior_y_origen,
    aviso_anterior_de_linea,
    buscar_del_mes,
    comprobar_hoja,
    entref_por_defecto,
    es_proforma,
    fecha_de_periodo,
    identificar_linea,
    importe_de_contrato,
    linea_descuadrada,
    lineas_del_existente,
    revisar_lineas,
    traducir,
)
from domain.models.albaran_compra_models import AlbaranCompraRequest, LineaAlbaranIn
from domain.models.proforma_models import (
    LineaProformaIn,
    LineaProformaResultado,
    OrigenProforma,
    ProformaError,
    ProformaRequest,
)

FIXTURE = Path(__file__).parent / "fixtures" / "f007_obra0719.json"
DATOS: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))


def lineas_de(cod: str) -> list[LineaContrato]:
    return [LineaContrato(**fila) for fila in DATOS["ctrpro"][cod]]


def contrato(cod: str) -> ContratoCandidato:
    return next(ContratoCandidato(**c) for c in DATOS["contratos"] if c["cod"] == cod)


def peticion(cod: str, **cambios: Any) -> ProformaRequest:
    datos = {"database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-1",
             **DATOS["hojas"][cod]}
    datos.update(cambios)
    return ProformaRequest(**datos)


def linea(**campos: Any) -> LineaProformaIn:
    base = {"referencia_linea": "X1", "descripcion": "LINEA", "cantidad": 1, "precio": 1}
    return LineaProformaIn(**{**base, **campos})


def registradas(cod: str) -> list[ProformaRegistrada]:
    return [ProformaRegistrada(**fila) for fila in DATOS["proformas"][cod]]


IDES_0417 = [fila["ide"] for fila in DATOS["ctrpro"]["CTSB26/0417"]]
IDES_0369 = [fila["ide"] for fila in DATOS["ctrpro"]["CTSB26/0369"]]


# =====================================================================================
# R13, R14 · identificar la linea de contrato
# =====================================================================================


def test_f007_r14_ctrpro_ide_del_contrato_se_acepta_sin_reidentificar() -> None:
    # El embudo daria la de ELABORACION (precio 0,2); manda el `ctrpro_ide` (SUMINISTRO).
    pedida = linea(ctrpro_ide=IDES_0417[0], partida="02.03.02.03", medicion_contrato=20140.26,
                   unidad="KG", precio=0.2)
    assert identificar_linea(pedida, lineas_de("CTSB26/0417")).ide == IDES_0417[0]


@pytest.mark.parametrize("ctrpro_ide", [262990, 999999])
def test_f007_r14_ctrpro_ide_de_otro_contrato_o_de_ninguno(ctrpro_ide: int) -> None:
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(linea(ctrpro_ide=ctrpro_ide), lineas_de("CTSB26/0417"))
    assert exc.value.codigo == "linea_no_es_del_contrato"
    assert exc.value.candidatos == []


@pytest.mark.parametrize(
    ("precio", "esperada"), [(1, 0), (0.2, 1), (0.27, 2), (0.20005, 1)]
)
def test_f007_r14_respaldo_suministro_elaboracion_colocacion_por_precio(
    precio: float, esperada: int
) -> None:
    pedida = linea(partida="02.03.02.03", medicion_contrato=20140.26, unidad="KG", precio=precio)
    assert identificar_linea(pedida, lineas_de("CTSB26/0417")).ide == IDES_0417[esperada]


def test_f007_r14_respaldo_misma_partida_por_precio() -> None:
    # «02.02.02»: DESBROCE 3700 M2 a 0,6 y EXCAVACION 5180 M3 a 2,8.
    pedida = linea(partida="02.02.02", medicion_contrato=5180, unidad="M3", precio=2.8)
    assert identificar_linea(pedida, lineas_de("CTSB26/0369")).ide == IDES_0369[1]
    pedida = linea(partida="02.02.02", medicion_contrato=1, precio=0.6)
    assert identificar_linea(pedida, lineas_de("CTSB26/0369")).ide == IDES_0369[0]


@pytest.mark.parametrize(
    "otros",
    [
        {"medicion_contrato": 3700, "unidad": "M2"},     # la medicion y la unidad de la otra
        {"medicion_contrato": 1, "unidad": "KG"},        # ni una ni otra casan
        {"medicion_contrato": 5180, "producto": "SM9999"},
    ],
)
def test_f007_r14_respaldo_medicion_unidad_y_producto_no_cuentan(otros: dict[str, Any]) -> None:
    # Precio de la EXCAVACION (2,8): da esa, digan lo que digan los demas campos.
    pedida = linea(partida="02.02.02", precio=2.8, **otros)
    assert identificar_linea(pedida, lineas_de("CTSB26/0369")).ide == IDES_0369[1]


@pytest.mark.parametrize(
    "campos",
    [
        {"partida": "02.02.02", "medicion_contrato": 3700.0004, "precio": 9},  # casaba la medicion
        {"partida": "02.02.02", "medicion_contrato": 5000, "unidad": "m3", "precio": 9},  # y la unidad
        {"partida": "02.02.04", "medicion_contrato": 1123.2, "precio": 99},  # una sola con la partida
        {"partida": "02.03.02.03", "medicion_contrato": 20140.26, "precio": 0.5},  # tres por partida
    ],
)
def test_f007_r14_respaldo_sin_precio_que_case_no_vuelve_atras(campos: dict[str, Any]) -> None:
    """Partida y precio son filtros estrictos: si el precio deja cero, no se
    vuelve a las de la partida (enmienda 1, R14)."""
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(linea(**campos), lineas_de(
            "CTSB26/0417" if campos["partida"] == "02.03.02.03" else "CTSB26/0369"))
    assert (exc.value.codigo, exc.value.candidatos) == ("linea_no_es_del_contrato", [])


@pytest.mark.parametrize("precio", [10.8, 8.8, 2.8])
def test_f007_r14_respaldo_sin_partida_no_casa_ninguna(precio: float) -> None:
    # 10,8 es de UNA sola linea de CTSB26/0369; aun asi, sin partida no hay linea.
    pedida = linea(medicion_contrato=1258.39, unidad="M3", precio=precio)
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(pedida, lineas_de("CTSB26/0369"))
    assert exc.value.codigo == "linea_no_es_del_contrato"


def test_f007_r14_sonda_d4_una_sola_linea_que_no_casa_no_se_vincula() -> None:
    """La sonda D4 de `review_F-007_proforma.md`: contrato de UNA linea, sin
    `partida`, medicion, unidad y precio distintos y con `producto`."""
    unica = [LineaContrato(ide=1, docide=1, paride=1, partida="07.01", can=100.0, pre=10.0,
                           tot=1000.0, unimed="M3", proide=1, producto="SM1004")]
    pedida = linea(producto="SM1004", medicion_contrato=55, unidad="UD", precio=99)
    assert pedida.de_contrato
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(pedida, unica)
    assert exc.value.codigo == "linea_no_es_del_contrato"


def _dos_iguales() -> list[LineaContrato]:
    """Dos lineas de la misma partida y el mismo precio (el desempate es semantico)."""
    return [
        LineaContrato(ide=11, docide=1, paride=1, partida="02.02.10", can=8368.15, pre=4.0,
                      tot=33472.6, unimed="M3", proide=1, producto="SM1026"),
        LineaContrato(ide=12, docide=1, paride=1, partida="02.02.10", can=769.87, pre=4.0,
                      tot=3079.48, unimed="M2", proide=1, producto="SM1026"),
        LineaContrato(ide=13, docide=1, paride=1, partida="02.02.10", can=769.87, pre=21.8,
                      tot=16783.166, unimed="M3", proide=1, producto="SM1026"),
    ]


@pytest.mark.parametrize(
    "otros", [{}, {"medicion_contrato": 769.87, "unidad": "M2"}, {"medicion_contrato": 8368.15}]
)
def test_f007_r14_respaldo_varias_que_casan_es_linea_ambigua_con_candidatos(
    otros: dict[str, Any]
) -> None:
    # Ni la medicion ni la unidad deshacen el empate de partida y precio.
    pedida = linea(partida="02.02.10", precio=4, **{"medicion_contrato": 1, **otros})
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(pedida, _dos_iguales())
    assert (exc.value.codigo, exc.value.candidatos) == ("linea_ambigua", [11, 12])
    assert "partida y el precio" in exc.value.mensaje


def test_f007_r14_respaldo_partida_que_no_es_del_contrato() -> None:
    pedida = linea(partida="99.99", medicion_contrato=20140.26, precio=1)
    with pytest.raises(FalloIdentificacion) as exc:
        identificar_linea(pedida, lineas_de("CTSB26/0417"))
    assert exc.value.codigo == "linea_no_es_del_contrato"


def test_f007_r14_respaldo_partida_comparada_como_el_erp() -> None:
    pedida = linea(partida=" 02.02.04 ", medicion_contrato=1123.2, precio=8.8)
    assert identificar_linea(pedida, lineas_de("CTSB26/0369")).ide == IDES_0369[4]


def test_f007_r13_de_contrato_y_sin_contrato() -> None:
    assert linea(ctrpro_ide=1).de_contrato
    assert linea(medicion_contrato=0.5, partida="01").de_contrato
    assert not linea(medicion_contrato=0, producto="SM1004").de_contrato
    assert not linea(producto="SM1004").de_contrato


def test_f007_r14_r16_revisar_lineas_junta_todos_los_fallos_de_la_etapa_1() -> None:
    lineas = [
        linea(referencia_linea="A", ctrpro_ide=IDES_0369[1]),
        linea(referencia_linea="B", ctrpro_ide=262990),
        linea(referencia_linea="C", partida="02.03.02.03", medicion_contrato=20140.26),
        linea(referencia_linea="D", partida="9.01"),
        linea(referencia_linea="E", producto="SM1026"),
        linea(referencia_linea="F", ctrpro_ide=IDES_0369[2], cantidad=1, cantidad_anterior=1,
              cantidad_origen=3),
    ]
    identificadas, fallos = revisar_lineas(lineas, lineas_de("CTSB26/0369"), sin_contrato=False)
    assert {i: l.ide for i, l in identificadas.items()} == {0: IDES_0369[1], 5: IDES_0369[2]}
    assert [(f.indice, f.referencia_linea, f.codigo) for f in fallos] == [
        (1, "B", "linea_no_es_del_contrato"),
        (2, "C", "linea_no_es_del_contrato"),
        (3, "D", "producto_obligatorio"),
        (5, "F", "linea_descuadrada"),
    ]


def test_f007_r14_revisar_lineas_lleva_los_candidatos_de_la_ambigua() -> None:
    lineas = [linea(referencia_linea="C", partida="02.02.10", medicion_contrato=1, precio=4)]
    _identificadas, fallos = revisar_lineas(lineas, _dos_iguales(), sin_contrato=False)
    assert [(f.codigo, f.candidatos) for f in fallos] == [("linea_ambigua", [11, 12])]


def test_f007_r16_sin_producto_es_obligatorio_aunque_el_contrato_tenga_uno_solo() -> None:
    # Todas las lineas de CTSB26/0472 son de SM1004 y aun asi no hay producto por defecto.
    assert {l.producto for l in lineas_de("CTSB26/0472")} == {"SM1004"}
    _identificadas, fallos = revisar_lineas(
        [linea(referencia_linea="Z", partida="02.20.02.02.11")], lineas_de("CTSB26/0472"),
        sin_contrato=False,
    )
    assert [f.codigo for f in fallos] == ["producto_obligatorio"]


def test_f007_r11_sin_contrato_no_identifica_y_exige_producto() -> None:
    lineas = [
        linea(referencia_linea="A", partida="02.02.02", medicion_contrato=5180),
        linea(referencia_linea="B", producto="SM9999", cantidad_anterior=1, cantidad_origen=9),
    ]
    identificadas, fallos = revisar_lineas(lineas, None, sin_contrato=True)
    assert identificadas == {}
    # Sin contrato no hay R19 (R11): B no da `linea_descuadrada`.
    assert [(f.referencia_linea, f.codigo) for f in fallos] == [("A", "producto_obligatorio")]


def test_f007_r14_las_tres_hojas_de_la_0719_se_identifican_sin_fallos() -> None:
    for cod in ("CTSB26/0472", "CTSB26/0417", "CTSB26/0369"):
        hoja = peticion(cod)
        identificadas, fallos = revisar_lineas(hoja.lineas, lineas_de(cod), sin_contrato=False)
        assert fallos == []
        assert {i: l.ide for i, l in identificadas.items()} == {
            i: l.ctrpro_ide for i, l in enumerate(hoja.lineas) if l.ctrpro_ide
        }


# =====================================================================================
# R18 · fecha
# =====================================================================================


@pytest.mark.parametrize(
    ("periodo", "fecha_proforma", "hoy", "esperada"),
    [
        (202608, None, 20261025, 20260831),       # mes pasado: su ultimo dia
        (202610, None, 20261025, 20261025),       # mes en curso: hoy
        (202608, 20260815, 20261025, 20260815),   # fecha dentro del periodo
        (202610, 20261030, 20261025, 20261030),   # dentro del mes en curso
        (202512, None, 20260105, 20251231),       # cambio de anio
        (202602, None, 20260301, 20260228),
    ],
)
def test_f007_r18_fecha_de_periodo(
    periodo: int, fecha_proforma: int | None, hoy: int, esperada: int
) -> None:
    assert fecha_de_periodo(periodo, fecha_proforma, hoy) == esperada


@pytest.mark.parametrize(
    ("periodo", "fecha_proforma", "hoy"),
    [(202611, None, 20261025), (202701, None, 20261231), (202608, 20260901, 20261025),
     (202608, 20260731, 20261025), (202611, 20261101, 20261025)],
)
def test_f007_r18_periodo_futuro_o_fecha_fuera_del_periodo(
    periodo: int, fecha_proforma: int | None, hoy: int
) -> None:
    with pytest.raises(ProformaError) as exc:
        fecha_de_periodo(periodo, fecha_proforma, hoy)
    assert exc.value.codigo == "periodo_no_valido"


@pytest.mark.parametrize(
    ("periodo", "obra", "entref"),
    [(202608, "0719", "PROF0826_0719"), (202601, "0404", "PROF0126_0404"),
     (203012, "1234", "PROF1230_1234")],
)
def test_f007_r12_entref_por_defecto(periodo: int, obra: str, entref: str) -> None:
    assert entref_por_defecto(periodo, obra) == entref


# =====================================================================================
# R19 · la hoja cuadra
# =====================================================================================


@pytest.mark.parametrize("cod", ["CTSB26/0472", "CTSB26/0417", "CTSB26/0369"])
def test_f007_r19_las_tres_hojas_cuadran(cod: str) -> None:
    comprobar_hoja(peticion(cod))
    assert not any(linea_descuadrada(l) for l in peticion(cod).lineas)


@pytest.mark.parametrize(("delta", "falla"), [(0.05, False), (-0.05, False), (0.06, True), (-0.06, True)])
def test_f007_r19_importe_mes_con_tolerancia_de_005(delta: float, falla: bool) -> None:
    # Hoja de CTSB26/0472: Σ round(cantidad·precio, 2) = 17024,28 (BERENJENO 265,475 -> 265,48).
    hoja = peticion("CTSB26/0472", importe_mes=round(17024.28 + delta, 2), importe_anterior=None,
                    importe_origen=None)
    if falla:
        with pytest.raises(ProformaError) as exc:
            comprobar_hoja(hoja)
        assert exc.value.codigo == "importe_mes_no_cuadra"
    else:
        comprobar_hoja(hoja)


@pytest.mark.parametrize(("origen", "falla"), [(19675.33, False), (19675.34, True), (19675.22, True)])
def test_f007_r19_origen_igual_a_anterior_mas_mes(origen: float, falla: bool) -> None:
    hoja = peticion("CTSB26/0472", importe_origen=origen)
    if falla:
        with pytest.raises(ProformaError) as exc:
            comprobar_hoja(hoja)
        assert exc.value.codigo == "hoja_descuadrada"
    else:
        comprobar_hoja(hoja)


@pytest.mark.parametrize(
    "cambios", [{"importe_anterior": None}, {"importe_origen": None},
                {"importe_anterior": None, "importe_origen": None}]
)
def test_f007_r19_sin_anterior_u_origen_no_se_comprueba_el_origen(cambios: dict[str, Any]) -> None:
    comprobar_hoja(peticion("CTSB26/0472", **{"importe_origen": 1.0, **cambios}))


@pytest.mark.parametrize(
    ("anterior", "origen", "descuadrada"),
    [(241, 861, False), (241, 861.001, False), (241, 861.002, True), (241, 860.998, True),
     (None, 861.5, False), (241, None, False)],
)
def test_f007_r19_linea_descuadrada_con_tolerancia_de_0001(
    anterior: float | None, origen: float | None, descuadrada: bool
) -> None:
    pedida = linea(cantidad=620, cantidad_anterior=anterior, cantidad_origen=origen)
    assert linea_descuadrada(pedida) is descuadrada


# =====================================================================================
# R20-R22 · lo registrado en Sigrid y los avisos
# =====================================================================================


def test_f007_r20_proforma_registrada_de_fila_lp1() -> None:
    fila = (2822961, "AC26/22961 ", 20260731, "PROF0726_0719", 2651.0, 0)
    assert ProformaRegistrada.de_fila(fila) == registradas("CTSB26/0472")[0]


def test_f007_r20_anterior_por_linea_de_lp2() -> None:
    assert anterior_por_linea([(262990, 241.0), (262992, None)]) == {262990: 241.0, 262992: 0.0}


def test_f007_r21_importe_de_contrato_redondeado() -> None:
    assert importe_de_contrato(lineas_de("CTSB26/0472")) == 64897.38


def test_f007_r20_r21_origen_de_la_hoja_de_ctsb26_0472() -> None:
    origen, avisos = anterior_y_origen(
        registradas("CTSB26/0472"), primer_dia=20260801, importe_mes=17024.28,
        importe_contrato=64897.38, importe_anterior=2651.0,
    )
    assert origen == OrigenProforma(
        importe_anterior_sigrid=2651.0, importe_mes=17024.28, importe_origen=19675.28,
        importe_contrato=64897.38, porcentaje_contrato=30.3,
    )
    assert avisos == []


def test_f007_r20_solo_las_previas_al_periodo_cuentan_como_anterior() -> None:
    # La de agosto (AC26/25548) no es anterior a agosto: es la del mes.
    origen, _avisos = anterior_y_origen(
        registradas("CTSB26/0417"), primer_dia=20260801, importe_mes=31291.05,
        importe_contrato=73519.95, importe_anterior=None,
    )
    assert origen.importe_anterior_sigrid == 36249.3
    origen, _avisos = anterior_y_origen(
        registradas("CTSB26/0417"), primer_dia=20260901, importe_mes=1.0,
        importe_contrato=73519.95, importe_anterior=None,
    )
    assert origen.importe_anterior_sigrid == 67540.36


@pytest.mark.parametrize(("anterior", "avisa"), [(2651.05, False), (2650.95, False), (2651.06, True),
                                                 (2600.0, True), (None, False)])
def test_f007_r20_anterior_distinto_de_sigrid_en_cabecera(anterior: float | None, avisa: bool) -> None:
    _origen, avisos = anterior_y_origen(
        registradas("CTSB26/0472"), primer_dia=20260801, importe_mes=17024.28,
        importe_contrato=64897.38, importe_anterior=anterior,
    )
    assert [a.codigo for a in avisos] == (["anterior_distinto_de_sigrid"] if avisa else [])
    if avisa:
        assert "2651.00" in avisos[0].mensaje and f"{anterior:.2f}" in avisos[0].mensaje


@pytest.mark.parametrize(
    ("mes", "codigos", "porcentaje"),
    [(1000.0, [], 100.0), (1000.01, ["supera_contrato"], 100.0),
     (1100.0, ["supera_contrato"], 110.0), (1100.01, ["supera_contrato_10"], 110.0),
     (999.99, [], 100.0)],
)
def test_f007_r21_supera_contrato_y_10_en_el_borde(
    mes: float, codigos: list[str], porcentaje: float
) -> None:
    origen, avisos = anterior_y_origen(
        [], primer_dia=20260801, importe_mes=mes, importe_contrato=1000.0, importe_anterior=None,
    )
    assert [a.codigo for a in avisos] == codigos
    assert origen.porcentaje_contrato == porcentaje
    if codigos:
        assert "1000.00" in avisos[0].mensaje and f"{mes:.2f}" in avisos[0].mensaje


def test_f007_r21_contrato_sin_importe_sin_porcentaje_ni_aviso() -> None:
    origen, avisos = anterior_y_origen(
        [], primer_dia=20260801, importe_mes=10.0, importe_contrato=0.0, importe_anterior=None,
    )
    assert origen.porcentaje_contrato is None
    assert avisos == []


def test_f007_r22_contrato_con_proforma_a_origen() -> None:
    a_origen = [*registradas("CTSB26/0472"),
                ProformaRegistrada(ide=1, cod="PROF26/00001", fec=20260630, entref="", totbas=1.0,
                                   docoritip=1)]
    _origen, avisos = anterior_y_origen(
        a_origen, primer_dia=20260801, importe_mes=17024.28, importe_contrato=64897.38,
        importe_anterior=None,
    )
    assert [a.codigo for a in avisos] == ["contrato_a_origen"]


@pytest.mark.parametrize(("anterior", "avisa"), [(241, False), (241.001, False), (241.002, True),
                                                 (0, True), (None, False)])
def test_f007_r20_anterior_distinto_de_sigrid_en_linea(anterior: float | None, avisa: bool) -> None:
    aviso = aviso_anterior_de_linea(linea(cantidad_anterior=anterior), 241.0)
    assert (aviso is not None) is avisa
    if aviso is not None:
        assert aviso.codigo == "anterior_distinto_de_sigrid"


# =====================================================================================
# R23, R24 · ya registrada
# =====================================================================================


def test_f007_r23_es_proforma_del_mismo_contrato() -> None:
    assert es_proforma((2831541, "PROF26/00001", 141, 2793879), 2793879)
    assert not es_proforma((2831541, "AC26/25548", 0, 2793879), 2793879)
    assert not es_proforma((2831541, "PROF26/00001", 141, 2790417), 2793879)
    assert es_proforma((2831541, "PROF26/00001", 141, 0), 0)


@pytest.mark.parametrize("importe", [17024.28, 17024.33, 17024.23])
def test_f007_r24_misma_del_mes_y_mismo_total_es_existente(importe: float) -> None:
    existente, avisos = buscar_del_mes(
        registradas("CTSB26/0472"), periodo=202608, importe_mes=importe, otra_del_mes=False
    )
    assert existente is not None and existente.cod == "AC26/25548"
    assert avisos == []


def test_f007_r24_del_mes_con_otro_total_es_error_con_su_cod() -> None:
    with pytest.raises(ProformaError) as exc:
        buscar_del_mes(registradas("CTSB26/0472"), periodo=202608, importe_mes=17024.34,
                       otra_del_mes=False)
    assert exc.value.codigo == "proforma_del_mes_existente"
    assert "AC26/25548" in str(exc.value)


@pytest.mark.parametrize("importe", [17024.28, 500.0])
def test_f007_r24_otra_del_mes_avisa_y_sigue(importe: float) -> None:
    existente, avisos = buscar_del_mes(
        registradas("CTSB26/0472"), periodo=202608, importe_mes=importe, otra_del_mes=True
    )
    assert existente is None
    assert [a.codigo for a in avisos] == ["otra_del_mes"]
    assert "AC26/25548" in avisos[0].mensaje


def test_f007_r24_sin_ninguna_del_mes() -> None:
    assert buscar_del_mes(registradas("CTSB26/0472"), periodo=202609, importe_mes=1.0,
                          otra_del_mes=False) == (None, [])
    assert buscar_del_mes(registradas("CTSB26/0472"), periodo=202609, importe_mes=1.0,
                          otra_del_mes=True) == (None, [])
    assert buscar_del_mes([], periodo=202608, importe_mes=1.0, otra_del_mes=False) == (None, [])


def test_f007_r24_dos_del_mes_y_una_con_el_mismo_total() -> None:
    dos = [*registradas("CTSB26/0472"),
           ProformaRegistrada(ide=9, cod="PROF26/00009", fec=20260820, entref="PROF0826_0719",
                              totbas=10.0, docoritip=0)]
    existente, _avisos = buscar_del_mes(dos, periodo=202608, importe_mes=10.0, otra_del_mes=False)
    assert existente is not None and existente.cod == "PROF26/00009"


def test_f007_r24_lineas_del_existente_de_lp6() -> None:
    filas = [tuple(f[c] for c in ("ide", "linoriide", "producto", "can", "pre", "tot"))
             for f in DATOS["existentes"]["AC26/25548"]]
    lineas = lineas_del_existente(filas)
    assert [type(l) for l in lineas] == [LineaProformaResultado] * 6
    primera, ultima = lineas[0], lineas[-1]
    assert (primera.indice, primera.dcapro_ide, primera.linoriide, primera.ctrpro_ide,
            primera.producto, primera.cantidad, primera.precio, primera.importe, primera.total,
            primera.de_contrato) == (0, 1352729, 262990, 262990, "SM1004", 620.0, 11.0, 6820.0,
                                     6820.0, True)
    assert (ultima.indice, ultima.dcapro_ide, ultima.linoriide, ultima.ctrpro_ide,
            ultima.de_contrato, ultima.importe) == (5, 1352739, 0, 0, False, 265.48)


# =====================================================================================
# Traduccion a la peticion del nucleo (design §Traduccion)
# =====================================================================================


def _traducida(cod: str = "CTSB26/0472", **cambios: Any) -> AlbaranCompraRequest:
    hoja = peticion(cod, **cambios)
    lineas = lineas_de(cod)
    identificadas = {
        i: next(l for l in lineas if l.ide == pedida.ctrpro_ide)
        for i, pedida in enumerate(hoja.lineas) if pedida.ctrpro_ide
    }
    return traducir(hoja, contrato=contrato(cod), identificadas=identificadas, fecha=20260831)


def test_f007_traducir_cabecera_campo_a_campo() -> None:
    traducida = _traducida(commit=True)
    assert type(traducida) is AlbaranCompraRequest
    assert traducida.model_dump(exclude={"lineas"}) == {
        "database": "ruesma", "cod_obra": "0719", "usu": "prueba", "cif_proveedor": "B00000472",
        "referencia_externa": "PRF-1", "cod_contrato": "CTSB26/0472",
        "su_referencia": "PROF0826_0719", "fecha_albaran": 20260831, "empide": None,
        "commit": True,
    }


def _solo_la_nueva() -> ProformaRequest:
    """La hoja de CTSB26/0472 con solo la BERENJENO (sin contrato, no hay que identificar)."""
    nueva = DATOS["hojas"]["CTSB26/0472"]["lineas"][-1]
    return peticion("CTSB26/0472", lineas=[nueva], importe_mes=265.48, importe_anterior=None,
                    importe_origen=None)


def test_f007_o4_traducir_normaliza_el_cif_del_contrato() -> None:
    sucio = ContratoCandidato(**{**DATOS["contratos"][0], "entcif": " b 00000472 "})
    traducida = traducir(_solo_la_nueva(), contrato=sucio, identificadas={}, fecha=20260831)
    assert traducida.cif_proveedor == "B00000472"


def test_f007_o4_traducir_con_el_contrato_sin_cif_es_un_fallo_con_codigo() -> None:
    sin_cif = ContratoCandidato(**{**DATOS["contratos"][0], "entcif": "  "})
    with pytest.raises(ProformaError) as exc:
        traducir(_solo_la_nueva(), contrato=sin_cif, identificadas={}, fecha=20260831)
    assert exc.value.codigo == "proveedor_no_encontrado"
    assert "CTSB26/0472" in str(exc.value) and "entcif" in str(exc.value)


def test_f007_traducir_lineas_de_contrato_y_nueva_en_su_orden() -> None:
    traducida = _traducida()
    assert traducida.lineas[0] == LineaAlbaranIn(
        referencia_linea="F09", ctrpro_ide=262990, descripcion="VERTIDO HORMIGON CIMENTACION LIMPIEZA",
        unidad="M3", cantidad=620, precio=11, partida="02.03.02.01", paride=355001,
    )
    assert traducida.lineas[-1] == LineaAlbaranIn(
        referencia_linea="F23", producto="SM1004", descripcion="BERENJENO", unidad="M2",
        cantidad=75.85, precio=3.5, partida="02.20.02.02.11",
    )
    assert [l.referencia_linea for l in traducida.lineas] == ["F09", "F11", "F15", "F16", "F21", "F23"]


def test_f007_traducir_su_referencia_de_la_peticion() -> None:
    assert _traducida(su_referencia="FRA 12/2026").su_referencia == "FRA 12/2026"


def test_f007_traducir_partida_de_imputacion_manda_sobre_la_del_contrato() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [dict(hoja["lineas"][0], partida_imputacion="9.01"), *hoja["lineas"][1:]]
    traducida = _traducida(lineas=lineas)
    assert (traducida.lineas[0].partida, traducida.lineas[0].paride) == ("9.01", None)
    nueva = [*hoja["lineas"][:-1], dict(hoja["lineas"][-1], partida_imputacion="9.01")]
    assert _traducida(lineas=nueva).lineas[-1].partida == "9.01"


def test_f007_traducir_linea_de_contrato_sin_partida() -> None:
    hoja = peticion("CTSB26/0472", lineas=DATOS["hojas"]["CTSB26/0472"]["lineas"][:1])
    sin_partida = LineaContrato(ide=262990, docide=2793879, paride=0, partida="", can=1.0,
                                pre=11.0, tot=11.0, unimed="M3", proide=610004, producto="SM1004")
    traducida = traducir(hoja, contrato=contrato("CTSB26/0472"), identificadas={0: sin_partida},
                         fecha=20260831)
    assert (traducida.lineas[0].partida, traducida.lineas[0].paride) == (None, None)


def test_f007_traducir_respaldo_identificada_sin_ctrpro_ide() -> None:
    hoja = peticion("CTSB26/0369", lineas=[
        {"referencia_linea": "N10", "partida": "02.02.02", "medicion_contrato": 5180,
         "unidad": "M3", "descripcion": "EXCAVACION", "cantidad": 1250.467, "precio": 2.8},
    ], importe_mes=3501.31, importe_anterior=None, importe_origen=None)
    traducida = traducir(hoja, contrato=contrato("CTSB26/0369"),
                         identificadas={0: lineas_de("CTSB26/0369")[1]}, fecha=20260831)
    assert (traducida.lineas[0].ctrpro_ide, traducida.lineas[0].producto) == (IDES_0369[1], None)


def test_f007_traducir_sin_contrato() -> None:
    hoja = ProformaRequest(
        database="ruesma", usu="prueba", referencia_externa="PRF-2", cod_obra="0719",
        periodo=202608, importe_mes=10.0, cif_proveedor="b 00000999", sin_contrato=True,
        lineas=[{"referencia_linea": "A", "producto": "SM9999", "partida": "9.01",
                 "descripcion": "VARIOS", "cantidad": 10, "precio": 1},
                {"referencia_linea": "B", "producto": "SM9999", "partida": "9.01",
                 "partida_imputacion": "9.02", "medicion_contrato": 3,
                 "descripcion": "OTROS", "cantidad": 1, "precio": 0}],
    )
    traducida = traducir(hoja, contrato=None, identificadas={}, fecha=20260831)
    assert (traducida.cod_contrato, traducida.cif_proveedor) == (None, "B00000999")
    assert [(l.producto, l.ctrpro_ide, l.partida) for l in traducida.lineas] == [
        ("SM9999", None, "9.01"), ("SM9999", None, "9.02"),
    ]
