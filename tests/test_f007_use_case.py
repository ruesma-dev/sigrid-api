# tests/test_f007_use_case.py
"""
F-007 T12 · R7-R12, R15-R17, R19-R30, R33: el caso de uso de `sigrid/proforma`
con el doble de F-009 extendido (`tests/f007_dobles.py`) y la obra 0719 (M29).

Las tres hojas de agosto ya estan en Sigrid: dan `existente` sin escribir. Con
`otra_del_mes`, el alta sigue por el nucleo de F-009 con la cabecera de
proforma (`PROF<aa>/`, `cla 141`, `entref` `PROF<MMAA>_<obra>`). Sin red ni base
de datos.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import pytest
from f007_dobles import (
    DATOS,
    OBRA_0719,
    SM1004,
    RepositorioProforma,
    SettingsProforma,
    ctride_de,
    peticion,
)
from f009_dobles import AHORA, ENTIDE

from application.use_cases.albaran_compra_statements import (
    APPLOCKS,
    DCA_COLUMNAS,
    L16_COLUMNAS,
)
from application.use_cases.create_proforma_use_case import (
    PERFIL_PROFORMA,
    CreateProformaUseCase,
)
from domain.models.albaran_compra_models import AlbaranCompraError
from domain.models.proforma_models import (
    ContratoResuelto,
    OrigenProforma,
    ProformaError,
    ProformaRequest,
    ProformaResponse,
)

PARTIDAS = {p["cod"]: p["ide"] for p in DATOS["partidas"]}
CTR_0472 = ctride_de("CTSB26/0472")

#: Lo que lee el caso de uso antes del nucleo cuando la proforma ya esta en Sigrid.
LECTURAS_EXISTENTE = [
    "obra", "lp5_referencia", "lp3_contratos", "lp4_lineas", "lp1_proformas", "lp2_anterior",
    "lp6_lineas",
]


def ejecutar(
    cuerpo: dict[str, Any] | None = None,
    *,
    repo: RepositorioProforma | None = None,
    settings: SettingsProforma | None = None,
) -> tuple[ProformaResponse, RepositorioProforma]:
    repo = repo or RepositorioProforma()
    caso = CreateProformaUseCase(repo, settings or SettingsProforma(), ahora_utc=lambda: AHORA)
    return caso.run(ProformaRequest(**(cuerpo or peticion()))), repo


def fallo(cuerpo: dict[str, Any], **kwargs: Any) -> AlbaranCompraError:
    with pytest.raises(AlbaranCompraError) as excinfo:
        ejecutar(cuerpo, **kwargs)
    return excinfo.value


def ctrrec_fila(**valores: Any) -> tuple[Any, ...]:
    """Una fila de L16: un recargo de retencion del 5 % sobre la base (F-015)."""
    base = {
        "ide": 7001, "recide": 6005, "pos": 64, "valdef": 1, "valpor": 0.05, "valcan": 0.0,
        "valmod": 0, "valfij": 0, "reccla": 5, "cueide": 4705, "ivaide": 0, "tex": "RETENCION",
        "resalt": "", "item": 0, "cla": 5, "cod": "RET5", **valores,
    }
    return tuple(base[columna] for columna in L16_COLUMNAS)


# =====================================================================================
# El perfil (costura 1)
# =====================================================================================


def test_f007_perfil_de_proforma() -> None:
    assert CreateProformaUseCase.perfil is PERFIL_PROFORMA
    assert (PERFIL_PROFORMA.endpoint, PERFIL_PROFORMA.prefijo_serie, PERFIL_PROFORMA.cifras_serie,
            PERFIL_PROFORMA.cla, PERFIL_PROFORMA.codigo_llave, PERFIL_PROFORMA.productos_del_contrato,
            PERFIL_PROFORMA.error) == (
        "sigrid/proforma", "PROF", 5, 141, "escritura_proformas_deshabilitada", True, ProformaError,
    )
    settings = SettingsProforma()
    for campo in ("campo_llave", "campo_prefijos", "campo_max_lineas", "campo_productos",
                  "campo_naturalezas"):
        nombre_campo = getattr(PERFIL_PROFORMA, campo)
        assert nombre_campo.startswith("sigrid_proforma_") and hasattr(settings, nombre_campo)


# =====================================================================================
# R24 · las tres hojas de la 0719 ya estan en Sigrid: `existente`, sin escribir
# =====================================================================================


@pytest.mark.parametrize("commit", [False, True])
@pytest.mark.parametrize(
    ("cod", "cod_ac", "con_ide", "n_lineas"),
    [("CTSB26/0472", "AC26/25548", 2831541, 6), ("CTSB26/0417", "AC26/25552", 2825552, 11),
     ("CTSB26/0369", "AC26/25551", 2825551, 2)],
)
def test_f007_r24_las_tres_hojas_de_la_0719_son_existentes(
    cod: str, cod_ac: str, con_ide: int, n_lineas: int, commit: bool
) -> None:
    respuesta, repo = ejecutar(peticion(cod, commit=commit), repo=RepositorioProforma(cod))
    assert type(respuesta) is ProformaResponse
    assert (respuesta.estado, respuesta.cod, respuesta.con_ide, respuesta.committed,
            respuesta.dry_run) == ("existente", cod_ac, con_ide, False, not commit)
    assert repo.lecturas_hechas() == LECTURAS_EXISTENTE
    assert repo.transacciones == [] and repo.en_transaccion == []
    assert repo.parametros_de("lp6_lineas") == [[con_ide]]
    leidas = DATOS["existentes"][cod_ac]
    assert len(respuesta.lineas) == n_lineas == len(leidas)
    assert [(l.dcapro_ide, l.linoriide, l.producto, l.cantidad, l.precio, l.importe)
            for l in respuesta.lineas] == [
        (f["ide"], f["linoriide"], f["producto"], f["can"], f["pre"], f["tot"]) for f in leidas
    ]
    assert respuesta.contrato == ContratoResuelto(
        cod=cod, ide=ctride_de(cod), resuelto_por="proveedor", candidatos=[cod]
    )


def test_f007_r24_existente_de_ctsb26_0472_como_el_ejemplo_del_contrato() -> None:
    respuesta, repo = ejecutar()
    assert respuesta.origen == OrigenProforma(
        importe_anterior_sigrid=2651.0, importe_mes=17024.28, importe_origen=19675.28,
        importe_contrato=64897.38, porcentaje_contrato=30.3,
    )
    assert respuesta.avisos == []
    assert repo.parametros_de("lp1_proformas") == [[14, CTR_0472, "PROF%", "PROF%", "PREV%"]]
    assert repo.parametros_de("lp2_anterior") == [
        [14, CTR_0472, 44, 20260801, "PROF%", "PROF%", "PREV%"]
    ]
    assert repo.parametros_de("lp3_contratos") == [[44, OBRA_0719]]
    assert repo.parametros_de("lp4_lineas") == [[CTR_0472]]
    assert repo.parametros_de("lp5_referencia") == [[14, "PRF-1001"]]


def test_f007_r24_existente_lleva_los_avisos_de_la_hoja() -> None:
    respuesta, _repo = ejecutar(peticion(importe_anterior=2600.0, importe_origen=19624.28))
    assert respuesta.estado == "existente"
    assert [a.codigo for a in respuesta.avisos] == ["anterior_distinto_de_sigrid"]


def test_f007_r24_del_mes_con_otro_total_es_error_sin_escribir() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    cuerpo = peticion(lineas=hoja["lineas"][:1], importe_mes=6820.0, importe_anterior=None,
                      importe_origen=None)
    error = fallo(cuerpo)
    assert isinstance(error, ProformaError) and error.codigo == "proforma_del_mes_existente"
    assert "AC26/25548" in str(error)


def test_f007_r24_solo_cuenta_el_contrato_resuelto() -> None:
    """Otra proforma del MISMO mes, obra y proveedor en OTRO contrato no la ve:
    LP1 va por el `ctride` del resuelto."""
    proformas = {**DATOS["proformas"], "CTSB26/0472": DATOS["proformas"]["CTSB26/0472"][:1]}
    repo = RepositorioProforma()
    repo.lecturas["lp1_proformas"] = lambda p: [
        tuple(x[c] for c in ("ide", "cod", "fec", "entref", "totbas", "docoritip"))
        for cod, lista in proformas.items() if ctride_de(cod) == p[1] for x in lista
    ]
    respuesta, repo = ejecutar(repo=repo)
    assert respuesta.estado == "previsto"
    assert repo.parametros_de("lp1_proformas")[0][1] == CTR_0472


# =====================================================================================
# R12, R15-R17, R25 · con `otra_del_mes`, el alta por el nucleo
# =====================================================================================


def test_f007_r12_previsto_con_la_cabecera_de_proforma() -> None:
    respuesta, repo = ejecutar(peticion(otra_del_mes=True))
    assert (respuesta.estado, respuesta.cod, respuesta.committed) == ("previsto", "PROF26/01282", False)
    con, dca = respuesta.filas["con"], respuesta.filas["dca"]
    assert (con["cod"], con["fec"], con["tip"]) == ("PROF26/01282", 20260831, 14)
    assert (dca["cla"], dca["docoritip"], dca["docoriide"], dca["entref"], dca["fecdoc"],
            dca["ctride"], dca["obride"], dca["synckey"]) == (
        141, 0, 0, "PROF0826_0719", 20260831, CTR_0472, OBRA_0719, "PRF-1001",
    )
    assert [a.codigo for a in respuesta.avisos] == ["cod_provisional", "otra_del_mes"]
    assert repo.transacciones == []
    assert respuesta.contrato is not None and respuesta.contrato.cod == "CTSB26/0472"
    assert respuesta.origen is not None and respuesta.origen.importe_origen == 19675.28


def test_f007_r12_su_referencia_de_la_peticion_va_al_entref() -> None:
    respuesta, _repo = ejecutar(peticion(otra_del_mes=True, su_referencia="HOJA 2/2026"))
    assert respuesta.filas["dca"]["entref"] == "HOJA 2/2026"


def test_f007_r15_vinculadas_como_f009_con_la_partida_del_ctrpro() -> None:
    respuesta, _repo = ejecutar(peticion(otra_del_mes=True))
    dcapro = respuesta.filas["dcapro"]
    ctrpro = {f["ide"]: f for f in DATOS["ctrpro"]["CTSB26/0472"]}
    for fila, ide in zip(dcapro[:5], [262990, 262992, 262996, 262997, 263002], strict=True):
        assert (fila["linoriide"], fila["docoritip"], fila["docoriide"], fila["docoricod"]) == (
            ide, 44, CTR_0472, "CTSB26/0472")
        assert (fila["canoriori"], fila["imporiori"]) == (
            round(ctrpro[ide]["can"], 2), round(ctrpro[ide]["tot"], 2))
        assert [fila.get(c, 0) for c in ("canoriant", "imporiant", "canorilin")] == [0, 0, 0]
        assert fila["paride"] == ctrpro[ide]["paride"]
    assert [l.ctrpro_ide for l in respuesta.lineas] == [262990, 262992, 262996, 262997, 263002, 0]
    assert [l.de_contrato for l in respuesta.lineas] == [True] * 5 + [False]
    assert [l.cantidad_anterior_sigrid for l in respuesta.lineas] == [241.0, 0.0, 0.0, 0.0, 0.0, None]
    # F15: 38,57 frente a 37,22 de contrato (contrato_proformas.md §3).
    assert "supera_pendiente" in [a.codigo for a in respuesta.lineas[2].avisos]
    assert respuesta.totales["n_vinculadas"] == 5


def test_f007_r15_partida_de_imputacion_manda() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [dict(hoja["lineas"][0], partida_imputacion="9.01"), *hoja["lineas"][1:]]
    respuesta, _repo = ejecutar(peticion(otra_del_mes=True, lineas=lineas))
    assert respuesta.filas["dcapro"][0]["paride"] == PARTIDAS["9.01"]
    assert "partida_distinta_del_contrato" in [a.codigo for a in respuesta.lineas[0].avisos]


def test_f007_r17_berenjeno_sin_vincular_con_el_producto_del_contrato() -> None:
    respuesta, repo = ejecutar(peticion(otra_del_mes=True))
    fila = respuesta.filas["dcapro"][5]
    assert (fila["proide"], fila["refent"], fila["res"], fila["can"], fila["pre"], fila["tot"]) == (
        SM1004, "F23", "BERENJENO", 75.85, 3.5, 265.48)
    # Naturaleza, cuenta y analitica de su plantilla (L8b del proveedor); IVA del `ctrpro`.
    assert (fila["natide"], fila["cueide"], fila["caaide"], fila["ivaide"]) == (4101, 4102, 4103, 3)
    assert fila["paride"] == PARTIDAS["02.20.02.02.11"]
    assert fila["linoriide"] == 0
    assert respuesta.lineas[5].producto == "SM1004"
    assert "naturalezas" not in repo.lecturas_hechas()
    assert repo.parametros_de("plantilla_linea_proveedor") == [[SM1004, ENTIDE]]


def test_f007_r17_berenjeno_sin_plantilla_con_el_iva_del_ctrpro() -> None:
    """Enmienda 1 (D1): sin L8b ni L8, el IVA del `ctrpro` (21 %) con su cuota en
    la fila y en los totales; naturaleza, cuenta y analitica a 0."""
    sin_plantilla = {"plantilla_linea": lambda p: [], "plantilla_linea_proveedor": lambda p: []}
    respuesta, _repo = ejecutar(peticion(otra_del_mes=True),
                                repo=RepositorioProforma(lecturas=sin_plantilla))
    fila = respuesta.filas["dcapro"][5]
    assert (fila["natide"], fila["cueide"], fila["caaide"]) == (0, 0, 0)
    assert (fila["ivaide"], fila["ivacuo"]) == (3, 55.75)  # 265,48 · 21 %
    assert (respuesta.totales["totiva"], respuesta.totales["totdoc"]) == (3575.1, 20599.38)
    assert respuesta.filas["dca"]["totiva"] == 3575.1


def test_f007_r16_producto_ni_de_la_lista_ni_del_contrato() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [*hoja["lineas"][:-1], dict(hoja["lineas"][-1], producto="SM7777")]
    error = fallo(peticion(otra_del_mes=True, lineas=lineas))
    assert error.codigo == "lineas_no_validas"
    assert [(f.referencia_linea, f.codigo) for f in error.lineas] == [("F23", "producto_no_permitido")]


def test_f007_r27_retencion_del_contrato_en_la_previa() -> None:
    repo = RepositorioProforma(lecturas={"retenciones": [ctrrec_fila()]})
    respuesta, repo = ejecutar(peticion(otra_del_mes=True), repo=repo)
    assert len(respuesta.filas["dcarec"]) == 1
    assert "retencion_del_contrato" in [a.codigo for a in respuesta.avisos]
    assert repo.parametros_de("retenciones") == [[CTR_0472]]


def test_f007_r27_commit_escribe_la_proforma_en_una_transaccion() -> None:
    repo = RepositorioProforma(lecturas={"retenciones": [ctrrec_fila()]})
    respuesta, repo = ejecutar(peticion(otra_del_mes=True, commit=True), repo=repo)
    assert (respuesta.estado, respuesta.committed, respuesta.cod) == ("creado", True, "PROF26/01282")
    assert len(repo.transacciones) == 1
    assert repo.transacciones[0]["applock_resources"] == list(APPLOCKS)
    sentencias = repo.sentencias()
    for clave in ("insert_con", "insert_dca", "insert_dcarec", "insert_log", "servido",
                  "estados_contrato"):
        assert clave in sentencias
    assert sentencias.count("insert_dcapro") == 6
    assert sentencias.count("insert_ctrprodes") == 5
    assert sentencias.count("servido") == 5
    assert "insert_mov" not in sentencias
    (insert_dca,) = repo.parametros_en_transaccion("insert_dca")
    assert insert_dca[DCA_COLUMNAS.index("cla")] == 141
    assert insert_dca[DCA_COLUMNAS.index("entref")] == "PROF0826_0719"
    assert repo.parametros_en_transaccion("reservar_cod")[0][-1].startswith("PROF26/")


def test_f007_r20_anterior_de_linea_distinto_de_sigrid_en_la_previa() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [dict(hoja["lineas"][0], cantidad_anterior=240, cantidad_origen=860),
              *hoja["lineas"][1:]]
    respuesta, _repo = ejecutar(peticion(otra_del_mes=True, lineas=lineas))
    avisos = [a.codigo for a in respuesta.lineas[0].avisos]
    assert avisos[-1] == "anterior_distinto_de_sigrid"
    assert "240" in respuesta.lineas[0].avisos[-1].mensaje
    assert respuesta.lineas[0].cantidad_anterior_sigrid == 241.0
    assert all("anterior_distinto_de_sigrid" not in [a.codigo for a in l.avisos]
               for l in respuesta.lineas[1:])


# =====================================================================================
# R23 · idempotencia
# =====================================================================================

_L11 = (2900011, "PROF26/01282", 20260831, ENTIDE, OBRA_0719, 17024.28, 20599.38, 19570.17)


@pytest.mark.parametrize("commit", [False, True])
def test_f007_r23_misma_referencia_de_proforma_del_contrato_es_idempotente(commit: bool) -> None:
    repo = RepositorioProforma(lecturas={
        "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)],
        "referencia": [_L11],
        "lineas_del_existente": [(64, SM1004, 620.0, 11.0, 6820.0, 355001, 70, "F09")],
    })
    respuesta, repo = ejecutar(peticion(commit=commit), repo=repo)
    assert (respuesta.estado, respuesta.cod, respuesta.con_ide, respuesta.committed) == (
        "idempotente", "PROF26/01282", 2900011, False)
    assert respuesta.contrato is not None and respuesta.contrato.cod == "CTSB26/0472"
    assert [l.referencia_linea for l in respuesta.lineas] == ["F09"]
    assert repo.lecturas_hechas() == [
        "obra", "lp5_referencia", "lp3_contratos", "lp4_lineas", "referencia",
        "lineas_del_existente",
    ]
    assert repo.transacciones == []


def test_f007_r23_la_referencia_que_desaparece_entre_dos_lecturas_no_es_idempotente() -> None:
    repo = RepositorioProforma(lecturas={
        "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)], "referencia": [],
    })
    with pytest.raises(ValueError):
        ejecutar(peticion(), repo=repo)


@pytest.mark.parametrize(
    "filas",
    [[(2831541, "AC26/25548", 0, CTR_0472)],               # un albaran, no una proforma
     [(2900011, "PROF26/01282", 141, 2790417)],             # proforma de otro contrato
     [(1, "PROF26/00001", 141, CTR_0472), (2, "PROF26/00002", 141, CTR_0472)]],
)
def test_f007_r23_misma_referencia_en_otro_documento_es_conflicto(filas: list[tuple[Any, ...]]) -> None:
    error = fallo(peticion(), repo=RepositorioProforma(lecturas={"lp5_referencia": filas}))
    assert isinstance(error, ProformaError) and error.codigo == "referencia_en_conflicto"


# =====================================================================================
# R7-R11 · contrato
# =====================================================================================


def test_f007_r7_cod_contrato_resuelto_por_peticion() -> None:
    cuerpo = peticion(cod_contrato="CTSB26/0472", nombre_proveedor=None, otra_del_mes=True)
    respuesta, repo = ejecutar(cuerpo)
    assert respuesta.contrato == ContratoResuelto(
        cod="CTSB26/0472", ide=CTR_0472, resuelto_por="peticion", candidatos=["CTSB26/0472"]
    )
    assert respuesta.contrato is not None
    # O4: el nucleo carga el contrato YA resuelto por su `ide`, sin volver a buscarlo.
    assert "locate_contract" not in [tipo for tipo, _datos in repo.llamadas]
    assert ("read_full_row", ("ctr", CTR_0472)) in repo.llamadas


class RepositorioCifComoSql(RepositorioProforma):
    """La 0719 con el `ctr.entcif` de CTSB26/0472 escrito como venga, y un
    `locate_contract` que compara el CIF como el SQL (`t.entcif = ?`)."""

    def __init__(self, entcif: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.entcif = entcif
        self.lecturas["lp3_contratos"] = [
            (c["ide"], c["cod"], c["fec"], entcif if c["ide"] == CTR_0472 else c["entcif"],
             c["entres"], c["nlin"])
            for c in DATOS["contratos"]
        ]
        self.filas[("ctr", CTR_0472)] = {**self.filas[("ctr", CTR_0472)], "entcif": entcif}

    def locate_contract(self, **kwargs: Any) -> tuple[list[str], list[tuple[Any, ...]]]:
        columnas, filas = super().locate_contract(**kwargs)
        return columnas, [f for f in filas if kwargs["cif_proveedor"] == self.entcif]


@pytest.mark.parametrize("commit", [False, True])
@pytest.mark.parametrize("entcif", ["B 00000472", " b00000472"])
def test_f007_o4_el_contrato_resuelto_se_graba_aunque_su_entcif_traiga_espacios(
    entcif: str, commit: bool
) -> None:
    """O4: R8 resuelve el contrato por el nombre; la grabacion no debe volver a
    buscarlo por un CIF normalizado que ya no es el de `ctr.entcif`."""
    repo = RepositorioCifComoSql(entcif)
    respuesta, repo = ejecutar(peticion(otra_del_mes=True, commit=commit), repo=repo)
    assert respuesta.estado == ("creado" if commit else "previsto")
    assert respuesta.contrato is not None and respuesta.contrato.cod == "CTSB26/0472"
    assert respuesta.filas["dca"]["ctride"] == CTR_0472


def test_f007_o4_contrato_sin_cif_es_un_fallo_con_codigo_sin_escribir() -> None:
    """Un `ctr.entcif` vacio no puede acabar en un 400 sin `codigo` (un
    `ValidationError` de la peticion del nucleo): es un fallo de negocio."""
    repo = RepositorioCifComoSql("")
    error = fallo(peticion(otra_del_mes=True, commit=True), repo=repo)
    assert isinstance(error, ProformaError) and error.codigo == "proveedor_no_encontrado"
    assert repo.transacciones == []


def test_f007_r7_cod_contrato_de_otro_proveedor() -> None:
    error = fallo(peticion(cod_contrato="CTSB26/0472", cif_proveedor="B00000417"))
    assert error.codigo == "contrato_de_otro_proveedor"


def test_f007_r9_proveedor_sin_contrato_en_la_obra() -> None:
    repo = RepositorioProforma()
    error = fallo(peticion(nombre_proveedor="NADIE"), repo=repo)
    assert error.codigo == "contrato_no_resuelto"
    assert repo.lecturas_hechas() == ["obra", "lp5_referencia", "lp3_contratos"]


def test_f007_r9_hoja_de_varios_contratos_con_reparto() -> None:
    hoja = DATOS["hojas"]
    lineas = hoja["CTSB26/0472"]["lineas"][:1] + hoja["CTSB26/0369"]["lineas"][:1]
    repo = RepositorioProforma()
    # Los dos contratos, del mismo proveedor en la obra.
    repo.lecturas["lp3_contratos"] = [
        (c["ide"], c["cod"], c["fec"], "B00000472", c["entres"], c["nlin"])
        for c in DATOS["contratos"]
    ]
    error = fallo(peticion(cif_proveedor="B00000472", lineas=lineas), repo=repo)
    assert isinstance(error, ProformaError) and error.codigo == "hoja_de_varios_contratos"
    assert error.reparto == {"F09": "CTSB26/0472", "N10": "CTSB26/0369"}


def test_f007_r11_sin_contrato_por_el_camino_de_f015() -> None:
    cuerpo = {
        "database": "ruesma", "usu": "prueba", "referencia_externa": "PRF-2002",
        "cod_obra": "0719", "periodo": 202608, "importe_mes": 816.84,
        "cif_proveedor": "B00000999", "sin_contrato": True,
        "lineas": [{"referencia_linea": "S1", "producto": "SM9999", "partida": "9.01",
                    "descripcion": "Seguridad y replanteo", "cantidad": 816.84, "precio": 1}],
    }
    respuesta, repo = ejecutar(cuerpo)
    assert (respuesta.estado, respuesta.contrato, respuesta.origen) == ("previsto", None, None)
    hechas = repo.lecturas_hechas()
    assert not {"lp1_proformas", "lp2_anterior", "lp3_contratos", "lp4_lineas", "lp6_lineas",
                "retenciones"} & set(hechas)
    assert "plantilla_por_cif" in hechas and "naturalezas" in hechas
    dca = respuesta.filas["dca"]
    assert (dca["cla"], dca["ctride"], dca["entref"]) == (141, 0, "PROF0826_0719")
    assert respuesta.filas["dcarec"] == []
    assert respuesta.lineas[0].de_contrato is False
    assert respuesta.filas["dcapro"][0]["paride"] == PARTIDAS["9.01"]


# =====================================================================================
# R6, R13-R16, R19, R26 · fallos
# =====================================================================================


def test_f007_r6_fallos_de_la_etapa_1_juntos_y_sin_llegar_al_nucleo() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [dict(hoja["lineas"][0], ctrpro_ide=271001), *hoja["lineas"][1:-1],
              {k: v for k, v in hoja["lineas"][-1].items() if k != "producto"}]
    repo = RepositorioProforma()
    error = fallo(peticion(lineas=lineas, importe_mes=1.0), repo=repo)
    assert isinstance(error, ProformaError) and error.codigo == "lineas_no_validas"
    assert [(f.indice, f.codigo) for f in error.lineas] == [
        (0, "linea_no_es_del_contrato"), (5, "producto_obligatorio")]
    assert repo.lecturas_hechas() == ["obra", "lp5_referencia", "lp3_contratos", "lp4_lineas"]


def test_f007_r6_despues_los_fallos_de_f009_juntos() -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [dict(hoja["lineas"][0], partida_imputacion="99.99"), *hoja["lineas"][1:-1],
              dict(hoja["lineas"][-1], producto="SM7777")]
    error = fallo(peticion(lineas=lineas, otra_del_mes=True))
    assert error.codigo == "lineas_no_validas"
    assert [(f.indice, f.codigo) for f in error.lineas] == [
        (0, "partida_no_encontrada"), (5, "producto_no_permitido")]


def test_f007_r19_importe_del_mes_que_no_cuadra_antes_de_lp1() -> None:
    repo = RepositorioProforma()
    error = fallo(peticion(importe_mes=17000.0, importe_anterior=None, importe_origen=None), repo=repo)
    assert error.codigo == "importe_mes_no_cuadra"
    assert "lp1_proformas" not in repo.lecturas_hechas()


def test_f007_r18_periodo_futuro_sin_leer_nada() -> None:
    repo = RepositorioProforma()
    error = fallo(peticion(periodo=202611), repo=repo)
    assert error.codigo == "periodo_no_valido"
    assert repo.llamadas == []


@pytest.mark.parametrize(
    ("cuerpo", "settings", "codigo"),
    [
        ({"referencia_externa": "ALB-1"}, {}, "referencia_no_permitida"),
        ({}, {"sigrid_proforma_max_lineas": 5}, "demasiadas_lineas"),
        ({"commit": True}, {"sigrid_proforma_write_enabled": False},
         "escritura_proformas_deshabilitada"),
        ({"commit": True}, {"sigrid_domain_write_enabled": False},
         "escritura_proformas_deshabilitada"),
    ],
)
def test_f007_r26_guardas_sin_leer_la_base(
    cuerpo: dict[str, Any], settings: dict[str, Any], codigo: str
) -> None:
    repo = RepositorioProforma()
    error = fallo(peticion(**cuerpo), repo=repo, settings=SettingsProforma(**settings))
    assert isinstance(error, ProformaError) and error.codigo == codigo
    assert repo.llamadas == []


def test_f007_r26_la_llave_del_albaran_no_abre_la_proforma() -> None:
    settings = SettingsProforma(sigrid_proforma_write_enabled=False, sigrid_albaran_write_enabled=True)
    error = fallo(peticion(commit=True), settings=settings)
    assert error.codigo == "escritura_proformas_deshabilitada"
    assert "SIGRID_PROFORMA_WRITE_ENABLED" in str(error)
    # Y en dry-run la llave cerrada no cambia nada (R5).
    respuesta, _repo = ejecutar(peticion(), settings=settings)
    assert respuesta.estado == "existente"


# =====================================================================================
# R18 · hora de Madrid y cambio de anio (D5); R24 · `otra_del_mes` (O3)
# =====================================================================================


def _a_las(ahora: datetime, cuerpo: dict[str, Any]) -> ProformaResponse:
    caso = CreateProformaUseCase(RepositorioProforma(), SettingsProforma(), ahora_utc=lambda: ahora)
    return caso.run(ProformaRequest(**cuerpo))


def test_f007_r18_a_las_2230_utc_del_31_de_agosto_ya_es_septiembre_en_madrid() -> None:
    # 22:30 UTC = 00:30 del 1 de septiembre en Madrid (CEST): 202609 es el mes en curso.
    respuesta = _a_las(datetime(2026, 8, 31, 22, 30, tzinfo=timezone.utc),
                       peticion(periodo=202609))
    assert respuesta.estado == "previsto"
    assert (respuesta.filas["con"]["fec"], respuesta.filas["dca"]["entref"]) == (
        20260901, "PROF0926_0719")


def test_f007_r18_a_las_2130_utc_del_31_de_agosto_septiembre_es_futuro() -> None:
    # 21:30 UTC = 23:30 del 31 de agosto en Madrid: 202609 aun no ha empezado.
    with pytest.raises(ProformaError) as excinfo:
        _a_las(datetime(2026, 8, 31, 21, 30, tzinfo=timezone.utc), peticion(periodo=202609))
    assert excinfo.value.codigo == "periodo_no_valido"


def test_f007_r18_r12_cambio_de_anio_en_madrid() -> None:
    # 23:30 UTC del 31-12 = 00:30 del 1-1-2027 en Madrid (CET): diciembre ya paso,
    # su ultimo dia es la fecha y la serie es la de 2026.
    respuesta = _a_las(datetime(2026, 12, 31, 23, 30, tzinfo=timezone.utc),
                       peticion(periodo=202612))
    assert (respuesta.estado, respuesta.cod) == ("previsto", "PROF26/01282")
    assert (respuesta.filas["con"]["fec"], respuesta.filas["dca"]["entref"]) == (
        20261231, "PROF1226_0719")
    # Y enero de 2027 ya es el mes en curso: serie de 2027 y fecha de hoy en Madrid.
    respuesta = _a_las(datetime(2026, 12, 31, 23, 30, tzinfo=timezone.utc),
                       peticion(periodo=202701))
    assert (respuesta.estado, respuesta.cod) == ("previsto", "PROF27/01282")
    assert (respuesta.filas["con"]["fec"], respuesta.filas["dca"]["entref"]) == (
        20270101, "PROF0127_0719")


def test_f007_r24_otra_del_mes_se_salta_la_del_mismo_total_con_su_aviso() -> None:
    """O3: la hoja de CTSB26/0472 tiene el MISMO total que AC26/25548; con
    `otra_del_mes` no es `existente`: aviso y alta."""
    hoja = DATOS["hojas"]["CTSB26/0472"]
    assert hoja["importe_mes"] == next(
        p["totbas"] for p in DATOS["proformas"]["CTSB26/0472"] if p["cod"] == "AC26/25548")
    respuesta, _repo = ejecutar(peticion(otra_del_mes=True))
    assert respuesta.estado == "previsto"
    (aviso,) = [a for a in respuesta.avisos if a.codigo == "otra_del_mes"]
    assert "AC26/25548" in aviso.mensaje


# =====================================================================================
# R33 · traza
# =====================================================================================


def _traza(caplog: pytest.LogCaptureFixture) -> tuple[dict[str, Any], str]:
    mensajes = [r.getMessage() for r in caplog.records if '"sigrid/proforma"' in r.getMessage()]
    assert len(mensajes) == 1
    return json.loads(mensajes[0]), mensajes[0]


def _sin_datos_sensibles(texto: str) -> None:
    for prohibido in ("HORMIGONES", "B00000472", "17024", "6820", "VERTIDO", "BERENJENO",
                      "prueba", "2651"):
        assert prohibido not in texto, prohibido


def test_f007_r33_traza_de_una_existente(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        ejecutar()
    traza, texto = _traza(caplog)
    duracion = traza.pop("duracion_ms")
    assert isinstance(duracion, float)
    assert traza == {
        "endpoint": "sigrid/proforma", "database": "ruesma", "obra": "0719",
        "contrato": "CTSB26/0472", "resuelto_por": "proveedor", "referencia": "PRF-1001",
        "periodo": 202608, "numero_orden": 2, "commit": False, "n_lineas_contrato": 5,
        "n_lineas_sin_contrato": 1, "resultado": "ok", "estado": "existente",
        "cod": "AC26/25548", "con_ide": 2831541, "codigos": [],
    }
    _sin_datos_sensibles(texto)


def test_f007_r33_traza_de_una_previa_con_sus_codigos(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO):
        ejecutar(peticion(otra_del_mes=True))
    traza, texto = _traza(caplog)
    assert (traza["estado"], traza["cod"]) == ("previsto", "PROF26/01282")
    assert traza["codigos"][:2] == ["cod_provisional", "otra_del_mes"]
    assert "supera_pendiente" in traza["codigos"]
    _sin_datos_sensibles(texto)


def test_f007_r33_traza_de_un_error(caplog: pytest.LogCaptureFixture) -> None:
    hoja = DATOS["hojas"]["CTSB26/0472"]
    lineas = [dict(hoja["lineas"][0], ctrpro_ide=271001), *hoja["lineas"][1:]]
    with caplog.at_level(logging.INFO), pytest.raises(ProformaError):
        ejecutar(peticion(lineas=lineas))
    traza, texto = _traza(caplog)
    assert (traza["resultado"], traza["codigo"], traza["codigos"]) == (
        "error", "lineas_no_validas", ["linea_no_es_del_contrato"])
    assert (traza["contrato"], traza["resuelto_por"]) == ("CTSB26/0472", "proveedor")
    _sin_datos_sensibles(texto)


def test_f007_r33_traza_de_una_excepcion(caplog: pytest.LogCaptureFixture) -> None:
    repo = RepositorioProforma(truncar_en="lp3_contratos")
    with caplog.at_level(logging.INFO), pytest.raises(ValueError):
        ejecutar(repo=repo)
    traza, _texto = _traza(caplog)
    assert (traza["resultado"], traza["codigo"]) == ("excepcion", "ValueError")


# =====================================================================================
# T18 · huecos de la campana de mutacion (progress/mutacion_F-007.md)
# =====================================================================================


def _topes(repo: RepositorioProforma) -> dict[str, Any]:
    """Lectura -> `max_rows` pedido (la ultima vez que se hizo)."""
    return {datos[0]: datos[2] for tipo, datos in repo.llamadas if tipo == "leer"}


def test_f007_t18_las_lecturas_de_muchas_filas_piden_el_tope_de_filas() -> None:
    """LP1-LP4 y LP6 pueden traer mas filas que el defecto de `sql/read`: piden
    `max_allowed_rows`, como las de F-009 (si no, un contrato grande saldria
    truncado y la proforma no se podria registrar)."""
    tope = SettingsProforma().max_allowed_rows
    _respuesta, repo = ejecutar()
    topes = _topes(repo)
    for lectura in ("lp3_contratos", "lp4_lineas", "lp1_proformas", "lp2_anterior", "lp6_lineas"):
        assert topes[lectura] == tope, lectura


def test_f007_t18_las_lineas_del_idempotente_piden_el_tope_de_filas() -> None:
    repo = RepositorioProforma(lecturas={
        "lp5_referencia": [(2900011, "PROF26/01282", 141, CTR_0472)],
        "referencia": [_L11],
        "lineas_del_existente": [(64, SM1004, 620.0, 11.0, 6820.0, 355001, 70, "F09")],
    })
    _respuesta, repo = ejecutar(repo=repo)
    assert _topes(repo)["lineas_del_existente"] == SettingsProforma().max_allowed_rows


def test_f007_t18_el_conflicto_de_referencia_nombra_los_cod() -> None:
    filas = [(2831541, "AC26/25548", 0, CTR_0472)]
    error = fallo(peticion(), repo=RepositorioProforma(lecturas={"lp5_referencia": filas}))
    assert error.codigo == "referencia_en_conflicto"
    assert "AC26/25548" in str(error)

