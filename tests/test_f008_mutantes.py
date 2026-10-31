# tests/test_f008_mutantes.py
"""
F-008 T20 · tests que nacen de la campana de mutacion: cada uno caza un
superviviente medido (aplicado y ejecutado) de `progress/mutacion_F-008.md`.
Bordes, contratos de los detalles de error y propiedades que la suite de cada
tarea daba por supuestas. Sin red ni base de datos: el ERP de
`tests/f008_dobles.py`.
"""
from __future__ import annotations

import dataclasses
import json
import logging
from typing import Any

import pytest
from f008_dobles import (
    AHORA,
    AjustesFactura,
    Mundo,
    Repositorio,
    linea_fr,
    linea_gg,
    peticion,
)
from pydantic import ValidationError

from application.use_cases import create_factura_use_case as modulo
from application.use_cases.create_factura_use_case import CreateFacturaUseCase
from domain.models.factura_models import (
    EntradaAOrigen,
    FacturaError,
    FacturaRequest,
    FalloLineaFactura,
    LineaSinOrigen,
    Vencimiento,
)

#: Una FR sin origen de 100 + 21 en la obra 0404.
SIN_ORIGEN: dict[str, Any] = {
    "origenes": [], "cod_obra": "0404", "lineas": [linea_fr()],
    "total_base": 100.0, "total_iva": 21.0, "total_factura": 121.0,
    "vencimientos": [{"fecha": 20261130, "importe": 121.0}],
}


def _caso(repo: Repositorio | None = None, ajustes: AjustesFactura | None = None, **kw: Any) -> CreateFacturaUseCase:
    return CreateFacturaUseCase(repo or Repositorio(), ajustes or AjustesFactura(), ahora_utc=lambda: AHORA, **kw)


def _run(repo: Repositorio | None = None, ajustes: AjustesFactura | None = None, **cambios: Any) -> dict[str, Any]:
    return _caso(repo, ajustes).run(FacturaRequest.model_validate(peticion(**cambios)))


def _error(repo: Repositorio | None = None, ajustes: AjustesFactura | None = None, **cambios: Any) -> FacturaError:
    with pytest.raises(FacturaError) as error:
        _run(repo, ajustes, **cambios)
    return error.value


def _factura(**cambios: Any) -> dict[str, Any]:
    base = {
        "ide": 7777, "cod": "FR26/00030", "entide": 500, "entref": "F-77", "totbas": 20.0,
        "totiva": 4.2, "totdoc": 24.2, "tot": 24.2, "est": 1, "synckey": "FAC-1", "entcif": "B00000001",
    }
    base.update(cambios)
    return base


# --- Datos internos inmutables -------------------------------------------------------


def test_f008_la_obra_y_la_factura_montada_son_inmutables() -> None:
    """La previa y el commit reutilizan lo leido y lo armado: nadie puede tocarlo
    entre la validacion y la escritura."""
    from application.use_cases.factura_lineas import LecturasLineas, LineaResuelta
    from application.use_cases.factura_statements import FilasFactura

    for clase in (modulo._Obra, modulo._Montada, LineaResuelta, LecturasLineas, FilasFactura):
        valor = clase(**{campo.name: None for campo in dataclasses.fields(clase)})
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(valor, dataclasses.fields(clase)[0].name, 1)


# --- Traza (R46) ---------------------------------------------------------------------


def test_f008_r46_duracion_en_milisegundos_con_un_decimal(caplog: pytest.LogCaptureFixture) -> None:
    tiempos = iter([10.0, 10.12345])
    caso = _caso(reloj=lambda: next(tiempos))
    with caplog.at_level(logging.INFO, logger=modulo.__name__):
        caso.run(FacturaRequest.model_validate(peticion()))
    (traza,) = [json.loads(r.getMessage()) for r in caplog.records if r.name == modulo.__name__]
    assert traza["duracion_ms"] == 123.5


def test_f008_r46_la_traza_se_lee_en_castellano(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger=modulo.__name__), pytest.raises(FacturaError):
        _run(usu="ñandú")
    assert '"usu": "ñandú"' in caplog.text


# --- Tope de lineas (R8) -------------------------------------------------------------


def test_f008_r8_justo_en_el_tope_pasa() -> None:
    r = _run(ajustes=AjustesFactura(sigrid_factura_max_lineas=1), **SIN_ORIGEN)
    assert r["estado"] == "previsto"


def test_f008_r8_justo_en_el_tope_contando_las_de_origen_pasa() -> None:
    r = _run(ajustes=AjustesFactura(sigrid_factura_max_lineas=2), lineas=[linea_fr()],
             total_base=120.0, total_iva=25.2, total_factura=145.2,
             vencimientos=[{"fecha": 20261130, "importe": 145.2}])
    assert r["estado"] == "previsto" and len(r["filas"]["dcfpro"]) == 2


# --- Idempotencia y conflicto (R43, R44) ---------------------------------------------


@pytest.mark.parametrize("factura", [
    _factura(entcif="B00000002", entide=600),  # mismo numero, otro proveedor
    _factura(entide=999),                      # proveedor que ya no existe
])
def test_f008_r43_conflicto_por_proveedor(factura: dict[str, Any]) -> None:
    repo = Repositorio()
    repo.mundo.facturas.append(factura)
    e = _error(repo)
    assert e.codigo == "referencia_en_conflicto" and e.details == {"cod": "FR26/00030"}


def test_f008_r43_dos_facturas_con_la_misma_referencia_son_conflicto() -> None:
    repo = Repositorio()
    repo.mundo.facturas += [_factura(), _factura(ide=7778, cod="FR26/00031")]
    e = _error(repo)
    assert e.codigo == "referencia_en_conflicto" and e.details == {"cod": "FR26/00030"}


# --- Obra sin almacen en su ficha ----------------------------------------------------


class _SinFicha(Mundo):
    def _r_almacen_de_obra(self, p: list[Any]) -> list[tuple[Any, ...]]:
        return []


def test_f008_obra_sin_ficha_de_almacen_queda_a_cero_en_la_cabecera() -> None:
    r = _run(Repositorio(mundo=_SinFicha()), **SIN_ORIGEN)
    assert (r["filas"]["dcf"]["almide"], r["filas"]["dcf"]["cenide"]) == (0, 0)
    (fila,) = r["filas"]["dcfpro"]
    assert (fila["almide"], fila["cenide"]) == (70, 80)


# --- Origenes de varias empresas (R13) -----------------------------------------------


def test_f008_r13_misma_obra_en_dos_empresas_son_varias_obras() -> None:
    repo = Repositorio()
    repo.mundo.origenes[801]["emp"] = 2
    e = _error(repo, AjustesFactura(sigrid_albaran_empresas_obra=[1, 2]), origenes=["AC26/1", "AC26/2"])
    assert e.codigo == "varias_obras"


# --- Cabecera sin origenes -----------------------------------------------------------


def test_f008_sin_origenes_la_cabecera_nace_sin_empresa_de_envio() -> None:
    """`empide` 0: sin albaran del que heredarlo (M61, cabecera sin origen)."""
    r = _run(**SIN_ORIGEN)
    assert r["filas"]["dcf"]["empide"] == 0


# --- Retencion (R31) -----------------------------------------------------------------


def _retencion(docide: int, **cambios: Any) -> dict[str, Any]:
    base = {"docide": docide, "recide": 77, "pos": 64, "valdef": 0, "valpor": 0.05, "valcan": 0,
            "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4730, "ivaide": 0, "tex": "",
            "resalt": "", "item": 0}
    base.update(cambios)
    return base


def test_f008_r31_dos_retenciones_iguales_en_un_origen_no_se_copian() -> None:
    repo = Repositorio()
    repo.mundo.retenciones = [_retencion(800), _retencion(800, pos=128)]
    assert _error(repo).codigo == "retencion_no_soportada"


# --- Lineas anteriores de la cadena (R20) --------------------------------------------


def test_f008_r20_de_mes_no_se_leen_las_lineas_anteriores() -> None:
    """La cadena (`canorilin`) solo se lee a origen: de mes no hace falta."""
    repo = Repositorio()
    repo.mundo.lineas[0]["canorilin"] = 7001
    _run(repo)
    assert "anteriores" not in repo.nombres()


# --- IVA sin tasa (R24) --------------------------------------------------------------


def test_f008_r24_iva_sin_tasa_en_la_ficha_cuenta_como_cero() -> None:
    repo = Repositorio()
    repo.mundo.ivas.append((22, 1, "I0", None))  # type: ignore[arg-type]
    ajustes = AjustesFactura(sigrid_factura_ivas=["I0"])
    r = _run(repo, ajustes, **{**SIN_ORIGEN, "lineas": [linea_fr(iva="I0")], "total_iva": 0.0,
                               "total_factura": 100.0, "vencimientos": [{"fecha": 20261130, "importe": 100.0}]})
    (fila,) = r["filas"]["dcfpro"]
    assert (fila["ivaide"], fila["ivacuo"]) == (22, 0)


# --- FRGG: analitica sin prefijo de obra (R26) ---------------------------------------

FRGG: dict[str, Any] = {
    "serie": "FRGG", "origenes": [], "cod_obra": "GG", "total_base": 100.0, "total_iva": 21.0,
    "total_factura": 121.0, "vencimientos": [{"fecha": 20261130, "importe": 121.0}],
}


@pytest.mark.parametrize("analitica", ["GENERAL", ".GENERAL"])
def test_f008_r26_analitica_sin_obra_delante_no_vale_ni_busca_obra(analitica: str) -> None:
    repo = Repositorio()
    repo.mundo.analiticas_gasto.append((193, 1, analitica, 1))
    e = _error(repo, **FRGG, lineas=[{**linea_gg(), "analitica": analitica}])
    assert [f["codigo"] for f in e.details["lineas"]] == ["analitica_no_valida"]
    assert "obras" not in repo.nombres()


# --- Abono (R30) ---------------------------------------------------------------------


def test_f008_r30_base_cero_tambien_es_abono() -> None:
    assert _error(total_base=0.0).codigo == "abono_no_soportado"


# --- Marcas del contrato solo en lineas vinculadas (R42) -----------------------------


def test_f008_r42_linea_con_linoriide_que_no_es_de_contrato_no_toca_el_ctrpro() -> None:
    """`linoriide` sin `docoritip` 44 apunta a otra cosa (un pedido): no se suma."""
    from f008_dobles import ajustes_de_escritura, con_transaccion

    repo = con_transaccion(Repositorio())
    repo.mundo.lineas[0]["linoriide"] = 9902
    caso = CreateFacturaUseCase(repo, ajustes_de_escritura(), ahora_utc=lambda: AHORA)
    assert caso.run(FacturaRequest.model_validate(peticion(commit=True)))["estado"] == "creado"
    assert repo.mundo.ctrpro[9902]["canfac"] == 0.0
    assert "sumar_contrato" not in [nombre for nombre, _p in repo.sentencias]


def test_f008_r42_linea_de_contrato_que_ya_no_existe_revierte_sin_sumar() -> None:
    from f008_dobles import ajustes_de_escritura, con_transaccion

    repo = con_transaccion(Repositorio())
    del repo.mundo.ctrpro[9901]
    caso = CreateFacturaUseCase(repo, ajustes_de_escritura(), ahora_utc=lambda: AHORA)
    with pytest.raises(FacturaError) as error:
        caso.run(FacturaRequest.model_validate(peticion(
            commit=True, origenes=["PROF26/1"], modo="origen",
            a_origen=[{"linea": 8101, "canoriori": 10.0, "imporiori": 100.0}],
            total_base=30.0, total_iva=6.3, total_factura=36.3,
            vencimientos=[{"fecha": 20261130, "importe": 36.3}],
        )))
    assert error.value.codigo == "filas_afectadas_inesperadas"
    assert "sumar_contrato" not in [nombre for nombre, _p in repo.sentencias]
    assert repo.mundo.insertadas == {}


# --- Respuesta: el resumen de lineas, origenes y vencimientos (R3) -------------------


def test_f008_r3_resumen_de_una_mixta() -> None:
    r = _run(lineas=[linea_fr()], total_base=120.0, total_iva=25.2, total_factura=145.2,
             vencimientos=[{"fecha": 20261130, "importe": 145.2}])
    assert r["lineas"] == [
        {"posicion": 0, "clase": "origen", "origen": "AC26/1", "linea": 8001, "indice": None,
         "can": 2.0, "tot": 20.0, "ivacuo": 4.2},
        {"posicion": 1, "clase": "sin_origen", "origen": None, "linea": None, "indice": 0,
         "can": 2.0, "tot": 100.0, "ivacuo": 21.0},
    ]
    assert r["origenes"] == [{"cod": "AC26/1", "con_ide": 800, "lineas": 1}]
    assert r["vencimientos"] == [{"cla": 0, "fecha": 20261130, "importe": 145.2}]


# --- Respuesta idempotente (R44) -----------------------------------------------------


#: Una factura de partida con retencion (`tot` < `totdoc`) y otra sin totales (NULL).
_TOTALES = [
    ({"totbas": 20.0, "totiva": 4.2, "totdoc": 24.2, "tot": 23.2},
     {"totbas": 20.0, "totiva": 4.2, "totdoc": 24.2, "tot": 23.2}),
    ({"totbas": None, "totiva": None, "totdoc": None, "tot": None},
     {"totbas": 0.0, "totiva": 0.0, "totdoc": 0.0, "tot": 0.0}),
]


@pytest.mark.parametrize("commit", [False, True])
@pytest.mark.parametrize("en_dcf,totales", _TOTALES)
def test_f008_r44_respuesta_idempotente_entera(
    commit: bool, en_dcf: dict[str, Any], totales: dict[str, float]
) -> None:
    from f008_dobles import ajustes_de_escritura, con_transaccion

    repo = con_transaccion(Repositorio()) if commit else Repositorio()
    repo.mundo.facturas.append(_factura(**en_dcf))
    ajustes = ajustes_de_escritura() if commit else AjustesFactura()
    r = _run(repo, ajustes, commit=commit)
    assert r == {
        "database": "ruesma", "estado": "idempotente", "committed": False, "dry_run": not commit,
        "cod": "FR26/00030", "con_ide": 7777, "serie": "FR", "modo": "mes", "referencia_externa": "FAC-1",
        "totales": totales,
        "retencion": None, "vencimientos": [], "origenes": [], "lineas": [], "filas": {}, "avisos": [],
        "pendiente_en_sigrid": list(modulo.PENDIENTE_EN_SIGRID),
    }
    assert repo.mundo.insertadas == {}


# --- Lecturas de las lineas sin origen: lo que no se lee queda vacio -------------------


def test_f008_lecturas_sin_leer_quedan_vacias() -> None:
    """La FRGG no lee obra ni almacen de F-009: sus `LecturasLineas` los dejan a
    0 y `None`, y todo lo demas vacio."""
    from application.use_cases.factura_lineas import LecturasLineas

    lecturas = LecturasLineas(ivas={}, ivas_permitidos=[])
    assert (lecturas.obride, lecturas.almacen) == (0, None)
    assert lecturas.cuentas == lecturas.analiticas == lecturas.obras == {}
    assert lecturas.productos == lecturas.naturalezas == lecturas.partidas == {}
    assert tuple(lecturas.prefijos_cuenta) == tuple(lecturas.productos_permitidos) == ()


# --- Totales con NULL (R29) ----------------------------------------------------------


def test_f008_r29_tot_e_ivacuo_nulos_suman_cero() -> None:
    from decimal import Decimal

    from application.use_cases.factura_statements import totales_factura

    lineas = [{"tot": None, "ivacuo": None, "can": 0, "tar": 0, "dto": ""},
              # Sin descuento, el bruto es su `tot` (aunque can x tar diga otra cosa).
              {"tot": 10.0, "ivacuo": 2.1, "can": 1, "tar": 12, "dto": ""},
              # Con descuento, el bruto es can x tar (F-018); NULL cuenta 0.
              {"tot": 0.0, "ivacuo": 0.0, "can": None, "tar": 5, "dto": "10%"},
              {"tot": 0.0, "ivacuo": 0.0, "can": 2, "tar": None, "dto": "10%"},
              {"tot": 9.0, "ivacuo": 0.0, "can": 2, "tar": 5, "dto": "10%"},
              {"tot": 4.0, "ivacuo": 0.0, "can": 1, "tar": 4.02, "dto": "0,5%"},
              # Descuento ilegible: como sin descuento, el bruto es su `tot`.
              {"tot": 3.0, "ivacuo": 0.0, "can": 1, "tar": 7, "dto": "x"}]
    assert totales_factura(lineas, cuo=Decimal(0)) == {
        "totbas": 26.0, "impnet": 26.0, "impbru": 27.02, "totiva": 2.1, "totdoc": 28.1, "tot": 28.1,
        "totpag": 28.1, "retencion": 0.0,
    }


# --- Recorrido de constantes (T15): las de IN con un solo marcador -------------------


def test_f008_t15_las_de_in_se_recorren_con_un_marcador() -> None:
    from application.use_cases.factura_statements import LF1_ESTADOS, FacturaStatements

    # LF1 lleva sus tres `tip` fijos; las demas son plantillas `{marcadores}`.
    con_in = [sql for sql in FacturaStatements.todas_las_sentencias() if " IN (" in sql and sql != LF1_ESTADOS]
    assert len(con_in) == 13
    assert all("IN (?)" in sql and "?, ?" not in sql for sql in con_in)


# --- Fechas AAAAMMDD: los bordes del rango (R2) --------------------------------------


@pytest.mark.parametrize("valor", [10000101, 99991231, 20240229, 20261130])
def test_f008_r2_fecha_en_los_bordes_vale(valor: int) -> None:
    from domain.models.factura_models import _fecha_real

    assert _fecha_real(valor) == valor


@pytest.mark.parametrize("valor", [9991231, 10000100, 99991232, 99991301, 100000101, -1000101, 20230229, 20261131])
def test_f008_r2_fecha_fuera_de_rango_no_vale(valor: int) -> None:
    from domain.models.factura_models import _fecha_real

    with pytest.raises(ValueError):
        _fecha_real(valor)


# --- Bordes de los campos del cuerpo (R1, R2) ----------------------------------------

def _linea(**cambio: Any) -> Any:
    return LineaSinOrigen.model_validate({**linea_fr(), **cambio})


def _cuerpo(**cambio: Any) -> Any:
    return FacturaRequest.model_validate(peticion(**cambio))


#: (constructor, campo, largo minimo, largo maximo) de los textos con tope.
_TEXTOS = [
    (_linea, "descripcion", 1, 128), (_linea, "iva", 1, 24), (_linea, "producto", 1, 24),
    (_linea, "partida", 1, 24), (_linea, "unidad", 0, 8),
    (_cuerpo, "database", 1, 128), (_cuerpo, "usu", 1, 24), (_cuerpo, "referencia_externa", 1, 128),
    (_cuerpo, "cif_proveedor", 1, 24), (_cuerpo, "numero_factura", 1, 128), (_cuerpo, "cod_obra", 1, 24),
]


@pytest.mark.parametrize("construir,campo,minimo,maximo", _TEXTOS)
def test_f008_r1_largos_de_los_textos_en_sus_bordes(construir: Any, campo: str, minimo: int, maximo: int) -> None:
    for largo in (minimo, maximo):
        construir(**{campo: "x" * largo})
    for largo in ((minimo - 1,) if minimo else ()) + (maximo + 1,):
        with pytest.raises(ValidationError):
            construir(**{campo: "x" * largo})


@pytest.mark.parametrize("campo", ["cuenta", "analitica"])
def test_f008_r1_largos_de_cuenta_y_analitica_frgg(campo: str) -> None:
    base = {**linea_gg()}
    for largo in (1, 24):
        LineaSinOrigen.model_validate({**base, campo: "x" * largo})
    for largo in (0, 25):
        with pytest.raises(ValidationError):
            LineaSinOrigen.model_validate({**base, campo: "x" * largo})


def test_f008_r1_bordes_numericos() -> None:
    EntradaAOrigen(linea=1, canoriori=1.0, imporiori=1.0)
    _linea(paride=1)
    Vencimiento(fecha=20261130, importe=0.01)
    FalloLineaFactura(indice=0, codigo="iva_no_valido", mensaje="m")
    for malo in (
        lambda: EntradaAOrigen(linea=0, canoriori=1.0, imporiori=1.0),
        lambda: _linea(paride=0),
        lambda: Vencimiento(fecha=20261130, importe=0.0),
        lambda: FalloLineaFactura(indice=-1, codigo="iva_no_valido", mensaje="m"),
    ):
        with pytest.raises(ValidationError):
            malo()


def test_f008_r1_entre_uno_y_doce_vencimientos() -> None:
    uno = {"fecha": 20261130, "importe": 1.0}
    _cuerpo(vencimientos=[uno])
    _cuerpo(vencimientos=[uno] * 12)
    for lista in ([], [uno] * 13):
        with pytest.raises(ValidationError):
            _cuerpo(vencimientos=lista)


#: Cada numero (y `commit`) es estricto: un texto con cifras no se convierte (R1).
_ESTRICTOS = [
    (lambda v: EntradaAOrigen(linea=v, canoriori=1.0, imporiori=1.0), "1"),
    (lambda v: EntradaAOrigen(linea=1, canoriori=v, imporiori=1.0), "1.0"),
    (lambda v: EntradaAOrigen(linea=1, canoriori=1.0, imporiori=v), "1.0"),
    (lambda v: Vencimiento(fecha=v, importe=1.0), "20261130"),
    (lambda v: Vencimiento(fecha=20261130, importe=v), "1.0"),
    (lambda v: _linea(cantidad=v), "2.0"),
    (lambda v: _linea(precio=v), "50.0"),
    (lambda v: _linea(paride=v), "355"),
    (lambda v: _cuerpo(fecha_factura=v), "20261015"),
    (lambda v: _cuerpo(vencimiento_retencion=v), "20271015"),
    (lambda v: _cuerpo(total_base=v), "20.0"),
    (lambda v: _cuerpo(total_iva=v), "4.2"),
    (lambda v: _cuerpo(total_factura=v), "24.2"),
    (lambda v: _cuerpo(commit=v), "false"),
]


@pytest.mark.parametrize("construir,texto", _ESTRICTOS)
def test_f008_r1_numeros_estrictos(construir: Any, texto: str) -> None:
    with pytest.raises(ValidationError):
        construir(texto)


def test_f008_r2_codigos_de_origen_de_1_a_24_recortados() -> None:
    assert _cuerpo(origenes=[" " + "x" * 24 + " ", "y"]).origenes == ["x" * 24, "y"]
    for malo in (["   "], [""], ["x" * 25]):
        with pytest.raises(ValidationError):
            _cuerpo(origenes=malo)


# --- La ruta traza los codigos de los fallos de linea (R46) --------------------------


def test_f008_r46_la_ruta_traza_los_codigos_de_cada_linea(caplog: pytest.LogCaptureFixture) -> None:
    import function_app

    error = FacturaError("x", codigo="lineas_no_validas", details={"lineas": [
        {"indice": 0, "codigo": "iva_no_valido", "mensaje": "Material I4"},
        {"indice": 2, "codigo": "producto_no_permitido", "mensaje": "SM9999"},
    ]})
    with caplog.at_level(logging.WARNING):
        respuesta = function_app._respuesta_factura_error(error)
    assert respuesta.status_code == 400
    assert "lineas=[(0, 'iva_no_valido'), (2, 'producto_no_permitido')]" in caplog.text
    assert "Material" not in caplog.text and "SM9999" not in caplog.text
