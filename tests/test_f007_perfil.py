# tests/test_f007_perfil.py
"""
F-007 · lote A · T2 (R31, D12): las cinco costuras del núcleo de F-009 sin
cambio de conducta (design §Costuras).

1. `PerfilAlta` y `PERFIL_ALBARAN` con los literales de hoy; sus nombres de
   campo existen en `Settings`; el núcleo lee la configuración por el perfil.
2. Prefijo de serie como parámetro (`prefijo_de_serie`, `sellos_del_alta`) con el
   defecto `AC`, y el ancho de la serie (`siguiente_cod`) sin ceros por defecto.
3. `_comprobar_dentro(cursor, request, cabecera, existente)`: en la base no lee
   nada y se llama en `work` justo después de E1 (idempotencia bajo
   `SIGRID_REFEXT_14`), también con la fila que encuentra E1 antes de su salida
   idempotente (enmienda 1, R28).
4. `_Catalogo` con `productos_del_contrato`: apagado, como hoy; encendido, una
   sin vincular cuyo producto es del contrato toma naturaleza, cuenta y
   analítica de su plantilla de línea y el IVA del `ctrpro` (R17).
5. Códigos como conjuntos cerrados de clase (`codigos`), con los de hoy por
   defecto, ampliables por una subclase.

Sin red y sin base de datos: el doble de F-009 (`f009_dobles.py`), sin tocarlo.
"""
from __future__ import annotations

import dataclasses
from typing import Any, ClassVar

import pytest
from f009_dobles import (
    AHORA,
    CTR,
    IntegrityError,
    RepositorioDoble,
    SettingsDoble,
    ctrpro,
    plantilla_dcapro,
)

from application.use_cases.albaran_compra_statements import (
    _DCAPRO_SIN_PLANTILLA,
    PREFIJO_SERIE,
    prefijo_de_serie,
    sellos_del_alta,
    siguiente_cod,
)
from application.use_cases.create_albaran_compra_use_case import (
    PERFIL_ALBARAN,
    CreateAlbaranCompraUseCase,
    PerfilAlta,
)
from config.settings import Settings
from domain.models.albaran_compra_models import (
    CODIGOS_AVISO,
    CODIGOS_CABECERA,
    CODIGOS_LINEA,
    AlbaranCompraError,
    AlbaranCompraRequest,
    AvisoAlbaran,
    FalloLinea,
)


def peticion(lineas: list[dict[str, Any]] | None = None, **cambios: Any) -> AlbaranCompraRequest:
    base = {
        "database": "ruesma", "cod_obra": "0404", "usu": "prueba",
        "cif_proveedor": "B12345678", "referencia_externa": "ALB-1",
        "cod_contrato": "CTSU16/0206", "su_referencia": "A-77", "fecha_albaran": 20261005,
        "lineas": lineas if lineas is not None else [
            {"referencia_linea": "L1", "ctrpro_ide": 9001, "cantidad": 2.0, "precio": 10.5}
        ],
    }
    return AlbaranCompraRequest.model_validate({**base, **cambios})


def sin_vincular(ref: str = "L2", producto: str = "HA25", **extra: Any) -> dict[str, Any]:
    return {"referencia_linea": ref, "producto": producto, "descripcion": "Extra de obra",
            "unidad": "m3", "cantidad": 3.0, "precio": 2.5, **extra}


# =====================================================================================
# Costura 1 · PerfilAlta
# =====================================================================================


def test_f007_r31_perfil_albaran_con_los_literales_de_hoy() -> None:
    assert PERFIL_ALBARAN == PerfilAlta(
        endpoint="sigrid/albaran",
        prefijo_serie="AC",
        cifras_serie=0,
        cla=0,
        codigo_llave="escritura_albaranes_deshabilitada",
        campo_llave="sigrid_albaran_write_enabled",
        campo_prefijos="sigrid_albaran_prefijos_referencia",
        campo_max_lineas="sigrid_albaran_max_lineas",
        campo_productos="sigrid_albaran_productos_sin_contrato",
        campo_naturalezas="sigrid_albaran_naturaleza_por_producto",
        productos_del_contrato=False,
        error=AlbaranCompraError,
        documentos="albaranes",
    )
    assert CreateAlbaranCompraUseCase.perfil is PERFIL_ALBARAN


def test_f007_r31_el_perfil_es_inmutable() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        PERFIL_ALBARAN.prefijo_serie = "PROF"  # type: ignore[misc]


def test_f007_r31_los_nombres_del_perfil_existen_en_settings() -> None:
    campos = [valor for nombre, valor in dataclasses.asdict(PERFIL_ALBARAN).items()
              if nombre.startswith("campo_")]
    assert len(campos) == 5
    assert set(campos) <= set(Settings.model_fields)


@dataclasses.dataclass
class SettingsConOtrosNombres(SettingsDoble):
    """Los mismos ajustes, con nombres nuevos para comprobar que el núcleo los
    lee del perfil y no de un literal."""

    otra_llave: bool = True
    otros_prefijos: list[str] = dataclasses.field(default_factory=lambda: ["OTR-"])
    otro_tope: int = 100
    otros_productos: list[str] = dataclasses.field(default_factory=lambda: ["MA9999"])
    otras_naturalezas: dict[str, str] = dataclasses.field(default_factory=lambda: {"MA9999": "MA99"})


class _ErrorAmpliado(AlbaranCompraError):
    codigos: ClassVar[frozenset[str]] = CODIGOS_CABECERA | {"escritura_otra_deshabilitada"}


_PERFIL_OTRO = dataclasses.replace(
    PERFIL_ALBARAN,
    codigo_llave="escritura_otra_deshabilitada",
    campo_llave="otra_llave",
    campo_prefijos="otros_prefijos",
    campo_max_lineas="otro_tope",
    campo_productos="otros_productos",
    campo_naturalezas="otras_naturalezas",
    error=_ErrorAmpliado,
)


class CasoConOtroPerfil(CreateAlbaranCompraUseCase):
    perfil = _PERFIL_OTRO


def ejecutar_otro(settings: SettingsConOtrosNombres, **cambios: Any) -> Any:
    caso = CasoConOtroPerfil(RepositorioDoble(), settings, ahora_utc=lambda: AHORA)
    return caso.run(peticion(**{"referencia_externa": "OTR-1", **cambios}))


def test_f007_r31_las_guardas_leen_los_campos_del_perfil() -> None:
    settings = SettingsConOtrosNombres(sigrid_albaran_max_lineas=0,
                                       sigrid_albaran_prefijos_referencia=[],
                                       sigrid_albaran_write_enabled=False)
    respuesta = ejecutar_otro(settings, commit=True)
    assert respuesta.estado == "creado"


@pytest.mark.parametrize(
    "cambio, codigo",
    [
        ({"otro_tope": 0}, "demasiadas_lineas"),
        ({"otros_prefijos": ["ALB-"]}, "referencia_no_permitida"),
        ({"otra_llave": False}, "escritura_otra_deshabilitada"),
    ],
)
def test_f007_r31_cada_guarda_por_el_campo_y_el_codigo_del_perfil(
    cambio: dict[str, Any], codigo: str
) -> None:
    with pytest.raises(_ErrorAmpliado) as excinfo:
        ejecutar_otro(SettingsConOtrosNombres(**cambio), commit=True)
    assert excinfo.value.codigo == codigo


def test_f007_r31_el_mensaje_de_la_llave_nombra_la_app_setting_del_perfil() -> None:
    with pytest.raises(_ErrorAmpliado) as excinfo:
        ejecutar_otro(SettingsConOtrosNombres(otra_llave=False), commit=True)
    assert "OTRA_LLAVE" in str(excinfo.value)
    assert "SIGRID_ALBARAN_WRITE_ENABLED" not in str(excinfo.value)


def test_f007_r31_el_mensaje_de_la_llave_del_albaran_es_el_de_hoy() -> None:
    caso = CreateAlbaranCompraUseCase(
        RepositorioDoble(), SettingsDoble(sigrid_albaran_write_enabled=False), ahora_utc=lambda: AHORA
    )
    with pytest.raises(AlbaranCompraError) as excinfo:
        caso.run(peticion(commit=True))
    assert type(excinfo.value) is AlbaranCompraError
    assert str(excinfo.value) == (
        "Escritura de albaranes desactivada: hacen falta SIGRID_DOMAIN_WRITE_ENABLED, "
        "SIGRID_ALBARAN_WRITE_ENABLED y credenciales de escritura."
    )


def test_f007_r31_productos_y_naturalezas_por_el_perfil() -> None:
    settings = SettingsConOtrosNombres(sigrid_albaran_productos_sin_contrato=[],
                                       sigrid_albaran_naturaleza_por_producto={})
    respuesta = ejecutar_otro(settings, lineas=[sin_vincular(producto="MA9999")])
    assert respuesta.filas["dcapro"][0]["natide"] == 501


def test_f007_r31_producto_fuera_de_la_lista_del_perfil_nombra_su_app_setting() -> None:
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar_otro(SettingsConOtrosNombres(), lineas=[sin_vincular(producto="QA9999")])
    assert [f.codigo for f in excinfo.value.lineas] == ["producto_no_permitido"]
    assert "OTROS_PRODUCTOS" in excinfo.value.lineas[0].mensaje


def test_f007_r31_la_traza_lleva_el_endpoint_del_perfil(caplog: pytest.LogCaptureFixture) -> None:
    class CasoOtroEndpoint(CreateAlbaranCompraUseCase):
        perfil = dataclasses.replace(PERFIL_ALBARAN, endpoint="sigrid/otro")

    caplog.set_level("INFO", logger="application.use_cases.create_albaran_compra_use_case")
    CasoOtroEndpoint(RepositorioDoble(), SettingsDoble(), ahora_utc=lambda: AHORA).run(peticion())
    assert '"endpoint": "sigrid/otro"' in caplog.records[-1].getMessage()


# =====================================================================================
# Costura 2 · prefijo y ancho de la serie
# =====================================================================================


def test_f007_r31_prefijo_de_serie_con_el_defecto_ac() -> None:
    assert PREFIJO_SERIE == "AC"
    assert prefijo_de_serie(20261005) == "AC26/"
    assert prefijo_de_serie(20261005, prefijo="PROF") == "PROF26/"
    assert prefijo_de_serie(20991231, prefijo="PROF") == "PROF99/"


def test_f007_r31_sellos_del_alta_con_el_defecto_ac() -> None:
    assert sellos_del_alta(AHORA, 20261005).prefijo == "AC26/"
    assert sellos_del_alta(AHORA, None).prefijo == "AC26/"
    assert sellos_del_alta(AHORA, 20250131, prefijo="PROF").prefijo == "PROF25/"


@pytest.mark.parametrize(
    "prefijo, maximo, cifras, esperado",
    [
        ("AC26/", 15952, 0, "AC26/15953"),
        ("AC26/", None, 0, "AC26/1"),
        ("PROF26/", 1282, 5, "PROF26/01283"),
        ("PROF26/", None, 5, "PROF26/00001"),
        ("PROF26/", 99999, 5, "PROF26/100000"),
    ],
)
def test_f007_r31_siguiente_cod_sin_ceros_por_defecto(
    prefijo: str, maximo: int | None, cifras: int, esperado: str
) -> None:
    assert siguiente_cod(prefijo, maximo, cifras=cifras) == esperado


def test_f007_r31_siguiente_cod_por_defecto_no_rellena() -> None:
    assert siguiente_cod("AC26/", 41) == "AC26/42"


def test_f007_r31_el_albaran_sigue_en_la_serie_ac_sin_ceros() -> None:
    caso = CreateAlbaranCompraUseCase(RepositorioDoble(), SettingsDoble(), ahora_utc=lambda: AHORA)
    respuesta = caso.run(peticion())
    assert respuesta.cod == "AC26/15953"
    assert respuesta.cabecera["cla"] == 0


def test_f007_r31_otro_perfil_numera_con_su_prefijo_y_su_ancho() -> None:
    class CasoSerie(CreateAlbaranCompraUseCase):
        perfil = dataclasses.replace(PERFIL_ALBARAN, prefijo_serie="PROF", cifras_serie=5)

    repo = RepositorioDoble()
    respuesta = CasoSerie(repo, SettingsDoble(), ahora_utc=lambda: AHORA).run(peticion())
    assert respuesta.cod == "PROF26/15953"
    assert repo.parametros_de("ultimo_cod") == [[8, 1, 14, "PROF26/%"]]

    repo = RepositorioDoble(reservas={"reservar_cod": (41,)})
    respuesta = CasoSerie(repo, SettingsDoble(), ahora_utc=lambda: AHORA).run(peticion(commit=True))
    assert respuesta.cod == "PROF26/00042"
    assert repo.parametros_en_transaccion("reservar_cod") == [[8, 1, 14, "PROF26/%"]]


# =====================================================================================
# Costura 3 · _comprobar_dentro
# =====================================================================================


class CursorIntocable:
    def __getattr__(self, nombre: str) -> Any:
        raise AssertionError(f"el gancho de la base no debe usar el cursor ({nombre})")


def test_f007_r31_comprobar_dentro_de_la_base_no_lee_nada() -> None:
    caso = CreateAlbaranCompraUseCase(RepositorioDoble(), SettingsDoble())
    assert caso._comprobar_dentro(CursorIntocable(), peticion(), None, None) is None
    fila_e1 = (2900500, "AC26/15000", 20261001, 77, 5000, 21.0, 25.41, 25.41)
    assert caso._comprobar_dentro(CursorIntocable(), peticion(), None, fila_e1) is None


class CasoConGancho(CreateAlbaranCompraUseCase):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.vistas: list[tuple[int, list[str], Any, int]] = []
        self.existentes: list[Any] = []

    def _comprobar_dentro(self, cursor: Any, request: Any, cabecera: Any, existente: Any) -> None:
        self.vistas.append(
            (cursor.intento, self._repo.sentencias(cursor.intento), request, cabecera.ctride)
        )
        self.existentes.append(existente)


def test_f007_r31_comprobar_dentro_va_justo_tras_e1_en_cada_intento() -> None:
    fallos = {"insert_con": lambda intento: IntegrityError("dup") if intento == 1 else None}
    repo = RepositorioDoble(fallos=fallos)
    caso = CasoConGancho(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    request = peticion(commit=True)
    respuesta = caso.run(request)

    assert respuesta.estado == "creado"
    assert [(i, s) for i, s, _r, _c in caso.vistas] == [(1, ["referencia"]), (2, ["referencia"])]
    assert all(r is request and c == CTR for _i, _s, r, c in caso.vistas)
    assert caso.existentes == [None, None]
    assert repo.sentencias(2)[:2] == ["referencia", "reservar_cod"]


def test_f007_r31_comprobar_dentro_ve_la_fila_de_e1_antes_de_la_salida_idempotente() -> None:
    existente = (2900500, "AC26/15000", 20261001, 77, 5000, 21.0, 25.41, 25.41)
    repo = RepositorioDoble(filas_en_transaccion={"referencia": [existente],
                                                  "lineas_del_existente": []})
    caso = CasoConGancho(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    respuesta = caso.run(peticion(commit=True))
    assert respuesta.estado == "idempotente"
    # El gancho va tras E1 y antes de leer las lineas del existente.
    assert [(i, s) for i, s, _r, _c in caso.vistas] == [(1, ["referencia"])]
    assert caso.existentes == [existente]
    assert repo.sentencias() == ["referencia", "lineas_del_existente"]


def test_f007_r31_lo_que_lance_el_gancho_con_la_fila_de_e1_no_deja_salir_idempotente() -> None:
    class CasoQueRechaza(CasoConGancho):
        def _comprobar_dentro(self, cursor: Any, request: Any, cabecera: Any, existente: Any) -> None:
            if existente is not None:
                raise AlbaranCompraError("ajena", codigo="referencia_en_conflicto")

    existente = (2900500, "AC26/15000", 20261001, 77, 5000, 21.0, 25.41, 25.41)
    repo = RepositorioDoble(filas_en_transaccion={"referencia": [existente]})
    with pytest.raises(AlbaranCompraError) as excinfo:
        CasoQueRechaza(repo, SettingsDoble(), ahora_utc=lambda: AHORA).run(peticion(commit=True))
    assert excinfo.value.codigo == "referencia_en_conflicto"
    assert repo.sentencias() == ["referencia"]


def test_f007_r31_comprobar_dentro_no_se_llama_en_la_previa() -> None:
    caso = CasoConGancho(RepositorioDoble(), SettingsDoble(), ahora_utc=lambda: AHORA)
    assert caso.run(peticion()).estado == "previsto"
    assert caso.vistas == []


# =====================================================================================
# Costura 4 · _Catalogo con productos del contrato
# =====================================================================================

#: `HA25` es el producto de la línea de contrato 9001 (`proide` 55) del doble.
_PRODUCTOS_CON_EL_DEL_CONTRATO = [
    (66, "MA9999", 0, 1), (67, "QA9999", 0, 1), (68, "XA9999", 0, 1), (55, "HA25", 0, 1),
]


class CasoConProductosDelContrato(CreateAlbaranCompraUseCase):
    perfil = dataclasses.replace(PERFIL_ALBARAN, productos_del_contrato=True)


def test_f007_r31_apagado_un_producto_del_contrato_fuera_de_la_lista_no_vale() -> None:
    repo = RepositorioDoble({"productos": _PRODUCTOS_CON_EL_DEL_CONTRATO})
    caso = CreateAlbaranCompraUseCase(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    with pytest.raises(AlbaranCompraError) as excinfo:
        caso.run(peticion([sin_vincular()]))
    assert [f.codigo for f in excinfo.value.lineas] == ["producto_no_permitido"]
    assert "SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO" in excinfo.value.lineas[0].mensaje
    assert "productos" not in repo.lecturas_hechas()


def _con_productos_del_contrato(lineas: list[dict[str, Any]], **lecturas: Any) -> tuple[Any, Any]:
    repo = RepositorioDoble({"productos": _PRODUCTOS_CON_EL_DEL_CONTRATO, **lecturas})
    caso = CasoConProductosDelContrato(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    return caso.run(peticion(lineas)), repo


def test_f007_r17_producto_del_contrato_toma_plantilla_e_iva_del_ctrpro() -> None:
    plantilla = plantilla_dcapro(55, natide=950, cueide=951, caaide=952, ivaide=4)
    respuesta, repo = _con_productos_del_contrato(
        [sin_vincular()], plantilla_linea_proveedor=lambda p: [plantilla] if p[0] == 55 else []
    )
    fila = respuesta.filas["dcapro"][0]
    # Naturaleza, cuenta y analítica de su plantilla (L8b); IVA del ctrpro 9001 (3, 21 %).
    assert (fila["natide"], fila["cueide"], fila["caaide"]) == (950, 951, 952)
    assert fila["ivaide"] == 3
    assert fila["ivacuo"] == 1.58  # 7,50 · 21 % = 1,575, redondeo comercial
    assert (fila["proide"], fila["linoriide"], fila["docoritip"]) == (55, 0, 0)
    assert respuesta.lineas[0].avisos == []
    # Se lee el producto aunque no esté en la lista, y su naturaleza no sale del mapeo.
    assert repo.parametros_de("productos") == [[1, 3, "HA25"]]
    assert "naturalezas" not in repo.lecturas_hechas()
    assert respuesta.filas["ctrprodes"] == []


def test_f007_r17_producto_del_contrato_con_plantilla_de_otro_proveedor_sin_aviso_de_iva() -> None:
    respuesta, _ = _con_productos_del_contrato([sin_vincular()])
    fila = respuesta.filas["dcapro"][0]
    # L8 (de otro proveedor): `plantilla_dcapro(55)` trae natide 999, cueide 888, caaide 1.
    assert (fila["natide"], fila["cueide"], fila["caaide"], fila["ivaide"]) == (999, 888, 1, 3)
    assert respuesta.lineas[0].avisos == []


def test_f007_r17_dos_lineas_del_contrato_con_el_producto_el_iva_es_el_de_la_primera_por_pos(
) -> None:
    """N7 (`review_F-007_mutacion.md`): si el producto esta en dos lineas del
    contrato con distinto IVA, manda la PRIMERA por `pos` (el nucleo las lee
    ordenadas por `pos`; `_productos_del_contrato` se queda con la primera)."""
    otra = {**ctrpro()[0], "ide": 9004, "pos": 256, "ivaide": 4, "ivacuo": 105.0}
    repo = RepositorioDoble({"productos": _PRODUCTOS_CON_EL_DEL_CONTRATO},
                            ctrpro_filas=[*ctrpro(), otra])
    caso = CasoConProductosDelContrato(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    respuesta = caso.run(peticion([sin_vincular()]))
    fila = respuesta.filas["dcapro"][0]
    # 9001 (`pos` 64, IVA 3 al 21 %) y no 9004 (`pos` 256, IVA 4 al 10 %).
    assert (fila["proide"], fila["ivaide"], fila["ivacuo"]) == (55, 3, 1.58)


def test_f007_r17_un_producto_de_la_lista_que_es_del_contrato_va_por_el_contrato() -> None:
    respuesta, repo = _con_productos_del_contrato(
        [sin_vincular(producto="MA9999")], productos=[(56, "MA9999", 0, 1)]
    )
    fila = respuesta.filas["dcapro"][0]
    # `proide` 56 es el de la línea de contrato 9002 (IVA 3): plantilla L8 de 56, nunca el mapeo.
    assert (fila["proide"], fila["natide"], fila["ivaide"]) == (56, 999, 3)
    assert "naturalezas" not in repo.lecturas_hechas()


def test_f007_r17_encendido_un_producto_ni_de_la_lista_ni_del_contrato_no_vale() -> None:
    with pytest.raises(AlbaranCompraError) as excinfo:
        _con_productos_del_contrato([sin_vincular(producto="ZZ0001")])
    assert [f.codigo for f in excinfo.value.lineas] == ["producto_no_permitido"]


def test_f007_r17_encendido_los_de_la_lista_siguen_con_su_mapeo() -> None:
    respuesta, repo = _con_productos_del_contrato([sin_vincular(producto="MA9999")])
    assert respuesta.filas["dcapro"][0]["natide"] == 501
    assert repo.parametros_de("naturalezas") == [["MA99"]]


def test_f007_r17_producto_del_contrato_de_baja_no_vale() -> None:
    with pytest.raises(AlbaranCompraError) as excinfo:
        _con_productos_del_contrato([sin_vincular()], productos=[(55, "HA25", 20240101, 1)])
    assert [f.codigo for f in excinfo.value.lineas] == ["producto_no_encontrado"]


def test_f007_r17_producto_del_contrato_sin_historico_lleva_el_iva_del_ctrpro() -> None:
    """Enmienda 1 (D1): sin plantilla (L8b y L8 vacias), naturaleza, cuenta y
    analitica a 0, pero el IVA sigue siendo el de la linea del contrato."""
    respuesta, _ = _con_productos_del_contrato([sin_vincular()], plantilla_linea=lambda p: [])
    fila = respuesta.filas["dcapro"][0]
    assert (fila["natide"], fila["cueide"], fila["caaide"]) == (0, 0, 0)
    assert (fila["ivaide"], fila["ivacuo"]) == (3, 1.58)  # 7,50 · 21 % del ctrpro 9001
    assert respuesta.lineas[0].iva_cuota == 1.58
    (aviso,) = respuesta.lineas[0].avisos
    assert aviso.codigo == "producto_sin_historico"
    assert "IVA a 0" not in aviso.mensaje and "IVA de su linea de contrato" in aviso.mensaje


def _albaran_sin_historico() -> Any:
    repo = RepositorioDoble({"plantilla_linea": lambda p: [], "plantilla_linea_proveedor": lambda p: []})
    caso = CreateAlbaranCompraUseCase(repo, SettingsDoble(), ahora_utc=lambda: AHORA)
    return caso.run(peticion([sin_vincular(producto="MA9999")]))


def test_f007_r17_el_albaran_sin_historico_sigue_con_iva_0() -> None:
    """R31: en el albaran (perfil apagado) una sin vincular sin plantilla, igual que hoy."""
    respuesta = _albaran_sin_historico()
    fila = respuesta.filas["dcapro"][0]
    assert (fila["ivaide"], fila["ivacuo"]) == (0, 0.0)
    (aviso,) = respuesta.lineas[0].avisos
    assert aviso.mensaje == "El producto 66 no tiene lineas previas de albaran: cuenta e IVA a 0."


def test_f007_r17_sin_historico_la_fila_tiene_las_columnas_de_la_sin_plantilla() -> None:
    """Solo cambian el IVA y su cuota: la fila se construye con las mismas
    columnas que la de una sin vincular sin plantilla del albaran."""
    proforma, _ = _con_productos_del_contrato([sin_vincular()], plantilla_linea=lambda p: [])
    assert set(proforma.filas["dcapro"][0]) == set(_albaran_sin_historico().filas["dcapro"][0])


def test_f007_t32_sin_historico_las_columnas_de_la_sin_plantilla_salen_como_en_el_albaran() -> None:
    """Enmienda 1 (D1), superviviente de la campaña de la pasada 1: sin
    plantilla, la base de la fila es la de una sin vincular sin historico del
    albaran (las columnas de `_DCAPRO_SIN_PLANTILLA` a 0), no solo las mismas
    claves. Cuenta y naturaleza, a 0 (el albaran las saca de su producto) y
    `prepma`, del precio: esas tres se comprueban aparte."""
    proforma, _ = _con_productos_del_contrato([sin_vincular()], plantilla_linea=lambda p: [])
    fila = proforma.filas["dcapro"][0]
    albaran = _albaran_sin_historico().filas["dcapro"][0]
    resto = [c for c in _DCAPRO_SIN_PLANTILLA if c not in ("cueide", "natide", "prepma")]
    assert resto == ["envide", "reqcuo", "lintip", "taride", "cuoman"]
    assert {c: fila[c] for c in resto} == {c: albaran[c] for c in resto} == dict.fromkeys(resto, 0)
    assert (fila["cueide"], fila["natide"]) == (0, 0)


# =====================================================================================
# Costura 5 · códigos como conjuntos de clase
# =====================================================================================


def test_f007_r31_los_conjuntos_de_hoy_son_los_de_las_clases_base() -> None:
    assert AlbaranCompraError.codigos is CODIGOS_CABECERA
    assert FalloLinea.codigos is CODIGOS_LINEA
    assert AvisoAlbaran.codigos is CODIGOS_AVISO


def test_f007_r31_la_base_sigue_rechazando_un_codigo_nuevo() -> None:
    with pytest.raises(ValueError, match="no es un codigo de error de sigrid/albaran"):
        AlbaranCompraError("x", codigo="escritura_otra_deshabilitada")
    with pytest.raises(ValueError, match="no es un codigo de linea de sigrid/albaran"):
        FalloLinea(indice=0, referencia_linea="L", codigo="linea_nueva", mensaje="x")
    with pytest.raises(ValueError, match="no es un codigo de aviso de sigrid/albaran"):
        AvisoAlbaran(codigo="aviso_nuevo", mensaje="x")


def test_f007_r31_una_subclase_amplia_los_conjuntos() -> None:
    class FalloAmpliado(FalloLinea):
        codigos: ClassVar[frozenset[str]] = CODIGOS_LINEA | {"linea_nueva"}

    class AvisoAmpliado(AvisoAlbaran):
        codigos: ClassVar[frozenset[str]] = CODIGOS_AVISO | {"aviso_nuevo"}

    assert _ErrorAmpliado("x", codigo="escritura_otra_deshabilitada").codigo == (
        "escritura_otra_deshabilitada"
    )
    assert FalloAmpliado(indice=0, referencia_linea="L", codigo="linea_nueva", mensaje="x").codigo == (
        "linea_nueva"
    )
    assert AvisoAmpliado(codigo="aviso_nuevo", mensaje="x").codigo == "aviso_nuevo"
    # Y siguen admitiendo los de hoy.
    assert FalloAmpliado(indice=0, referencia_linea="L", codigo="precio_negativo", mensaje="x")
