# tests/test_f009_t0_script.py
"""
F-009 · T0: prueba de humo del script de mediciones `scripts/medir_f009_t0.py`.

Sin red y sin base de datos: argumentos, que toda sentencia sea de solo
lectura, que el cliente rechace lo demás antes de llamar, que la clave no se
imprima, que el fichero de resultados no caiga dentro del repositorio y los
análisis puros que sacan las conclusiones.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts import medir_f009_t0 as t0


class _Respuesta:
    def __init__(self, cuerpo: dict[str, Any], status: int = 200) -> None:
        self._cuerpo = cuerpo
        self.status_code = status

    def json(self) -> dict[str, Any]:
        return self._cuerpo


class _Sesion:
    def __init__(self, respuestas: list[_Respuesta]) -> None:
        self.respuestas = respuestas
        self.llamadas: list[tuple[str, dict[str, Any]]] = []

    def post(self, url: str, *, headers: dict[str, str], json: dict[str, Any], timeout: int) -> _Respuesta:
        self.llamadas.append((url, json))
        return self.respuestas.pop(0)


def _sql_completa(sql: str) -> str:
    return sql.format(**{"in": t0.marcadores(3)}) if "{in}" in sql else sql


def test_f009_t0_hay_una_medicion_por_cada_m_de_la_spec() -> None:
    assert list(t0.MEDICIONES) == [f"M{i}" for i in range(1, 19)]


# Las sentencias que añade T0a (spec v5, §T0 v5): M16, M17, M18 y las ampliaciones de M11 y M14.
_NUEVAS_T0A = (
    "M16_caa_con_partida", "M16_caa_almacen", "M16_almacen_sin_vincular", "M16_ficha_obra",
    "M17_ope", "M17_emp_log", "M17_existe", "M17_existe_sin_emp", "M17_marcas",
    "M18_refent", "M18_valores", "M18_propagacion",
    "M11_iva_por_proveedor", "M11_iva_y_isp", "M11_acierto",
    "M14_sv_valores", "M14_sv_ma9999", "M14_sv_ultimas", "M14_sv_linea", "M14_sv_plantilla",
)
# Las que reciben valores de fuera: van con marcador `?`, nunca con el valor dentro del texto.
_CON_PARAMETROS = (
    "M11_iva_por_proveedor", "M11_iva_y_isp", "M11_acierto",
    "M14_sv_ma9999", "M14_sv_ultimas", "M14_sv_linea", "M14_sv_plantilla",
)


def test_f009_t0a_existen_las_sentencias_nuevas_de_la_spec_v5() -> None:
    faltan = [k for k in _NUEVAS_T0A if k not in t0.SQL]
    assert faltan == []


@pytest.mark.parametrize("nombre", _CON_PARAMETROS)
def test_f009_t0a_las_sentencias_nuevas_con_valores_van_parametrizadas(nombre: str) -> None:
    sql = t0.SQL[nombre]
    assert "?" in sql and "{" not in sql, nombre
    assert "MA9999" not in sql, nombre


def test_f009_t0a_m14_sv_valores_cuenta_las_columnas_de_la_spec() -> None:
    sql = t0.SQL["M14_sv_valores"]
    for col in ("med", "canmed", "parcandes", "anades", "serdes", "fecimp", "item", "anexo", "taride",
                "fec", "pla", "tex", "texcom", "cod2", "pac", "refent", "fec_igual_albaran"):
        assert f"AS {col}," in sql or f"AS {col} " in sql, col
    assert "DATALENGTH(d.med) > 0" in sql and "ISNULL(d.refent, '') <> ''" in sql
    assert "ISNULL(d.canmed, 0) <> 0" in sql and "d.fec = c.fec" in sql


@pytest.mark.parametrize("col", t0.LISTA_DE_RESETEO)
def test_f009_t0a_m14_sv_valores_cuenta_toda_la_lista_de_reseteo(col: str) -> None:
    """T0 se ejecuta una sola vez (H28): M14 tiene que poder confirmar la lista de reseteo entera."""
    sql = t0.SQL["M14_sv_valores"]
    assert f"(d.{col})" in sql or f"(d.{col}," in sql, col
    assert f"AS {col}," in sql or f"AS {col} " in sql, col
    assert col in dict(t0.COLUMNAS_SV), col


def test_f009_t0a_solo_acepta_la_repeticion_unica_de_t0b() -> None:
    lista = ["M3", "M7", "M9", "M11", "M13", "M14", "M16", "M17", "M18"]
    assert t0.analizar_argumentos(["--solo", *lista]).solo == lista
    assert t0.analizar_argumentos(["--solo", "m16", "m17", "m18"]).solo == ["M16", "M17", "M18"]


@pytest.mark.parametrize("nombre", sorted(t0.SQL))
def test_f009_t0_toda_sentencia_es_select_o_with_de_una_sola_sentencia(nombre: str) -> None:
    sql = _sql_completa(t0.SQL[nombre])
    assert t0.es_solo_lectura(sql), nombre
    for prohibida in ("INSERT ", "UPDATE ", "DELETE ", "MERGE ", "DROP ", "EXEC", "ALTER ", "CREATE "):
        assert prohibida not in sql.upper(), (nombre, prohibida)


@pytest.mark.parametrize("sql", ["UPDATE dbo.ctr SET estser = 0", "SELECT 1; DELETE FROM dbo.mov", "EXEC sp_who", ""])
def test_f009_t0_el_cliente_rechaza_en_local_lo_que_no_es_lectura(sql: str) -> None:
    sesion = _Sesion([])
    cliente = t0.ClienteLectura("https://ejemplo.invalid", "clave-falsa", sesion=sesion)
    with pytest.raises(t0.ErrorDeLectura):
        cliente.leer(sql)
    assert sesion.llamadas == []


def test_f009_t0_el_cliente_solo_llama_a_sql_read_y_marca_el_truncado() -> None:
    sesion = _Sesion([_Respuesta({"ok": True, "columns": ["n"], "rows": [[3]], "truncated": True})])
    cliente = t0.ClienteLectura("https://ejemplo.invalid/", "clave-falsa", sesion=sesion)
    res = cliente.leer("SELECT COUNT(*) AS n FROM dbo.dca", max_rows=1)
    url, cuerpo = sesion.llamadas[0]
    assert url == "https://ejemplo.invalid/api/sql/read"
    assert cuerpo["database"] == "ruesma" and cuerpo["max_rows"] == 1
    assert res.filas == [{"n": 3}] and res.truncado is True


def test_f009_t0_un_error_de_la_api_no_muestra_la_clave() -> None:
    sesion = _Sesion([_Respuesta({"ok": False, "error": "Solicitud invalida.", "details": {}}, status=400)])
    cliente = t0.ClienteLectura("https://ejemplo.invalid", "clave-secreta-123", sesion=sesion)
    with pytest.raises(t0.ErrorDeLectura) as exc:
        cliente.leer("SELECT 1 AS x")
    assert "clave-secreta-123" not in str(exc.value)
    assert "ejemplo.invalid" not in str(exc.value)


def test_f009_t0_argumentos_solo_y_por_defecto() -> None:
    assert t0.analizar_argumentos([]).solo is None
    assert t0.analizar_argumentos(["--solo", "m5"]).solo == ["M5"]
    assert t0.analizar_argumentos(["--solo", "M5", "M14"]).solo == ["M5", "M14"]
    with pytest.raises(SystemExit):
        t0.analizar_argumentos(["--solo", "M99"])


def test_f009_t0_la_salida_va_a_temp_y_nunca_al_repositorio(tmp_path: Path) -> None:
    por_defecto = t0.ruta_de_salida(None)
    assert t0.RAIZ_REPO not in por_defecto.parents and por_defecto.name.startswith("f009_t0_")
    assert t0.ruta_de_salida(str(tmp_path / "r.txt")) == (tmp_path / "r.txt").resolve()
    with pytest.raises(SystemExit):
        t0.ruta_de_salida(str(t0.RAIZ_REPO / "progress" / "t0.txt"))


def test_f009_t0_la_config_falla_sin_clave_y_sin_mostrar_valores(tmp_path: Path) -> None:
    vacio = tmp_path / ".env"
    vacio.write_text("SIGRID_API_BASE_URL=https://ejemplo.invalid\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        t0.cargar_config({}, vacio)
    assert "SIGRID_API_FUNCTION_KEY" in str(exc.value) and "ejemplo.invalid" not in str(exc.value)
    assert t0.cargar_config({"SIGRID_API_FUNCTION_KEY": "k"}, vacio) == ("https://ejemplo.invalid", "k")


def test_f009_t0_regla_de_devolucion_a_y_b() -> None:
    anterior = {"almcan": 10.0, "almpma": 5.0}
    # A: entrada negativa, PMP por la fórmula: (10·5 + -2·8) / 8 = 4,25
    a = {"mov": 1, "can": -2, "pre": 8, "canent": -2, "cansal": 0, "almcan": 8, "almpma": 4.25}
    assert t0.regla_devolucion(a, anterior) == "A"
    # B: salida a PMP vigente
    b = {"mov": 1, "can": -2, "pre": 8, "canent": 0, "cansal": 2, "almcan": 8, "almpma": 5.0}
    assert t0.regla_devolucion(b, anterior) == "B"
    assert t0.regla_devolucion({"mov": None}, anterior) == "sin_mov"
    assert t0.regla_devolucion({**a, "almcan": 99}, anterior) == "?"


def test_f009_t0_roturas_de_cadena_de_stock() -> None:
    buena = [{"almcan": 5}, {"almcan": 7, "canent": 2, "cansal": 0}, {"almcan": 6, "canent": 0, "cansal": 1}]
    assert t0.roturas_de_cadena(buena) == 0
    assert t0.roturas_de_cadena([buena[0], buena[2], buena[1]]) == 2


def test_f009_t0_columnas_distintas_ignora_las_del_documento() -> None:
    esc = [{"ide": 1, "anades": 0, "refent": ""}, {"ide": 2, "anades": 0, "refent": ""}]
    api = [{"ide": 3, "anades": 1, "refent": ""}]
    assert list(t0.columnas_distintas(esc, api, {"ide"})) == ["anades"]


@pytest.mark.parametrize("nombre", sorted(t0.SQL))
def test_f009_t0_el_guardia_de_lectura_de_la_api_acepta_cada_sentencia(nombre: str) -> None:
    """El mismo `SqlQueryGuard` que aplica `sql/read`, con los topes de la instancia `dev`
    (azure-apps/sigrid_api.md §4.1): ninguna medición se quedará en un 400 del guardia."""
    from types import SimpleNamespace

    from domain.models.sql_models import SqlReadRequest
    from infrastructure.security.sql_query_guard import SqlQueryGuard

    ajustes = SimpleNamespace(
        allowed_databases=["ruesma"], allowed_query_prefixes=["SELECT", "WITH"],
        default_query_timeout_seconds=30, max_query_timeout_seconds=230,
        default_max_rows=200, max_allowed_rows=500000,
    )
    # model_construct: sus validadores leerían la configuración real del entorno.
    peticion = SqlReadRequest.model_construct(database="ruesma", sql=_sql_completa(t0.SQL[nombre]).strip(),
                                              parameters=[], timeout_seconds=t0.TIMEOUT_PESADO_S, max_rows=500)
    SqlQueryGuard(ajustes).validate(peticion)


# --- Error 130 de SQL Server (T0 del 2026-10-02: M7 y M9 cayeron por esto) ------------------


@pytest.mark.parametrize("nombre", sorted(t0.SQL))
def test_f009_t0_ninguna_sentencia_agrega_sobre_una_subconsulta(nombre: str) -> None:
    assert not t0.agregado_con_subconsulta(_sql_completa(t0.SQL[nombre])), nombre


@pytest.mark.parametrize(
    "sql",
    [
        # Las dos formas que fallaron en producción (texto de la versión anterior del script).
        (
            "SELECT COUNT(*) AS lineas, SUM(CASE WHEN EXISTS (SELECT 1 FROM dbo.dcapropar x "
            "WHERE x.docproide = d.ide) THEN 1 ELSE 0 END) AS con_desglose FROM dbo.dcapro d"
        ),
        (
            "SELECT d.tipsininv, SUM(x.lineas) AS lineas FROM dbo.dca d CROSS APPLY (SELECT (SELECT COUNT(*) "
            "FROM dbo.dcapro p WHERE p.docide = d.ide) AS lineas) x GROUP BY d.tipsininv"
        ),
        "SELECT MAX((SELECT TOP 1 ide FROM dbo.con)) AS x FROM dbo.dca",
    ],
)
def test_f009_t0_el_detector_reconoce_lo_que_da_el_error_130(sql: str) -> None:
    assert t0.agregado_con_subconsulta(sql)


def test_f009_t0_el_detector_no_confunde_subconsultas_fuera_del_agregado() -> None:
    assert not t0.agregado_con_subconsulta(
        "SELECT COUNT(*) AS n FROM dbo.ctrpro p WHERE ABS(p.canser - (SELECT ISNULL(SUM(s.can), 0) "
        "FROM dbo.ctrprodes s WHERE s.docproide = p.ide)) > 0.001"
    )


# --- M11: hay un MA9999 por empresa ----------------------------------------------------------


class _ClienteFalso:
    def __init__(self, respuestas: dict[str, list[dict[str, Any]]]) -> None:
        self.respuestas = respuestas
        self.llamadas: list[tuple[str, list[Any]]] = []

    def leer(self, sql: str, parametros: list[Any] | None = None, **_: Any) -> t0.Resultado:
        clave = next(k for k, v in t0.SQL.items() if _sql_completa(v) == sql or v == sql
                     or ("{in}" in v and sql.startswith(v.split("{in}")[0])))
        self.llamadas.append((clave, parametros or []))
        return t0.Resultado(self.respuestas.get(clave, []), False, 0.0)


def test_f009_t0_m11_mira_cada_ma9999_y_no_solo_el_primero() -> None:
    productos = [
        {"ide": 31, "cod": "MA9999", "emp": 31, "comide": 0, "ivacomide": 0, "natide": 310},
        {"ide": 1, "cod": "MA9999", "emp": 1, "comide": 0, "ivacomide": 0, "natide": 274},
        {"ide": 7, "cod": "SB9999", "emp": 1, "comide": 0, "ivacomide": 0, "natide": 313},
    ]
    cliente = _ClienteFalso({"M11_productos": productos, "M11_total_producto": [{"lineas": 5}]})
    t0.m11(cliente)  # type: ignore[arg-type]
    totales = [p for k, p in cliente.llamadas if k == "M11_total_producto"]
    assert totales == [[*t0.VENTANA_M11, 31], [*t0.VENTANA_M11, 1]]  # T0a-bis: la ventana va delante


# --- Recorrido completo sin red: cada medición con datos de ejemplo ---------------------------

_DATOS: dict[str, list[dict[str, Any]]] = {
    "M1_total": [{"total": 10, "con_synckey": 0}],
    "M1_prefijo_alb": [{"n": 0}],
    "M2_est_emp": [{"emp": 1, "est": 10, "n": 8}, {"emp": 1, "est": 1, "n": 2}],
    "M2_est_sin_facturar": [{"est": 3, "n": 5}],
    "M2_mov_emp": [{"emp": 1, "n": 9}],
    "M2_indices_con": [{"indice": "con_emptipcod", "unico": True, "columna": "emp", "orden": 1}],
    "M3_partidas_usadas": [{"tip": 1, "tipdes": 0, "tipvis": 0, "n": 4}],
    "M3_repetidos": [{"repetidos": 2}],
    "M3_repetidos_imputables": [{"repetidos": 1, "filas": 2}],
    "M4_vinculadas": [{"n": 10, "partida_distinta": 1, "precio_distinto": 1}],
    "M4_nulos_ctrpro": [{"paride_null": 0, "cenide_null": 0, "caaide_null": 0, "n": 5}],
    "M5_por_origen": [{"docoritip": 0, "n": 3}],
    "M5_muestra": [
        {"linea": 1, "cod": "AC", "mov": 9, "proide": 1, "almide": 2, "can": -2, "pre": 8,
         "canent": -2, "cansal": 0, "almcan": 8, "almpma": 4.25},
        {"linea": 2, "cod": "AC", "mov": None, "proide": 1, "almide": 2, "can": -1, "pre": 1},
    ],
    "M5_mov_anterior": [{"almcan": 10, "almpma": 5}],
    "M6_muestra": [{"ide": 1, "can": -3, "ctrprodes_can": -3}],
    "M6_revisadas": [{"lineas_contrato": 4, "canser_negativo": 1}],
    "M6_descuadres": [{"descuadres": 0}],
    "M7_desglose": [{"lineas": 10, "con_desglose": 0, "parcandes": 0}],
    "M8_almacenes_por_obra": [{"n_almacenes": 1, "obras": 3}],
    "M8_almacen_del_contrato": [{"alm_de_su_obra": 9, "n": 10}],
    "M8_lineas_sin_partida": [{"tipo": "alm_de_la_obra", "alm_paride": 0, "cen_del_alm": 1, "n": 5}],
    "M9_por_tipsininv": [{"tipsininv": 0, "albaranes": 2, "lineas": 4, "movs": 3}],
    "M9_por_partida": [{"tipo": "con_partida", "lineas": 4, "con_mov": 3}],
    "M9_por_banderas": [{"tipmov": 1, "tipinv": 1, "lineas": 4, "con_mov": 3}],
    "M9_sin_mov_por_producto": [{"proide": 5, "cod": "X", "emp": 1, "lineas": 1}],
    "M10_atrasados": [{"proide": 1, "almide": 2, "fechor": 20260901.1}, {"proide": 1, "almide": 2, "fechor": 1}],
    "M10_serie": [{"ide": 2, "almcan": 5}, {"ide": 1, "almcan": 7, "canent": 2, "cansal": 0}],
    "M11_productos": [{"ide": 1, "cod": "MA9999", "emp": 1, "comide": 0, "ivacomide": 0, "natide": 274}],
    "M11_total_producto": [{"lineas": 100, "desde": 20080101, "hasta": 20261001}],
    "M11_lineas_producto": [{"cueide": 7, "ivaide": 8, "natide": 274, "unimed": "UD", "n": 90}],
    "M11_iva_usado": [{"ivaide": 8, "cod": "I21", "iva": 0.21, "lineas": 90, "ivacuo_distinto": 0}],
    "M12_mezcla": [{"con_lineas_sin_vincular": 7, "con_contrato": 10}],
    "M13_est_alta": [{"est": 1, "ori": 0, "n": 50}],
    "M13_cobertura": [{"albaranes": 60, "con_log": 50}],
    "M14_api": [{"ide": 99, "cod": "AC26/15951"}],
    "M14_escritorio": [{"ide": 1, "cod": "AC26/1"}],
    "M14_prv": [{"n": 10, "pagide_del_prv": 9, "efeide_del_prv": 9}],
    "M14_prepma": [{"n": 10, "igual_pmp_resultante": 10, "igual_prepma_del_mov": 0}],
    "M14_con": [{"ide": 1, "est": 1}, {"ide": 99, "est": 1}],
    "M14_dca": [{"ide": 1, "pagide": 23}, {"ide": 99, "pagide": 36}],
    "M14_dcapro": [{"docide": 1, "prepma": 1.5}, {"docide": 99, "prepma": 69.5}],
    "M15_stock_negativo": [{"n": 7, "almacenes": 2}],
    # T0a (spec v5)
    "M11_iva_por_proveedor": [{"proveedores": 10, "con_varios_iva": 2}],
    "M11_iva_y_isp": [{"tipisp": 0, "ivaide": 8, "proveedores": 9, "lineas": 80},
                      {"tipisp": 1, "ivaide": 9, "proveedores": 1, "lineas": 10}],
    "M11_acierto": [{"lineas": 90, "sin_previa_del_prv": 10, "acierta_mismo_prv": 75, "acierta_cualquiera": 60}],
    "M14_sv_valores": [{"n": 1000, "med": 0, "canmed": 0, "parcandes": 0, "anades": 0, "serdes": 0, "fecimp": 0,
                        "item": 0, "anexo": 0, "taride": 0, "fec": 1000, "pla": 0, "tex": 300, "texcom": 0,
                        "cod2": 0, "pac": 0, "refent": 1, "fec_igual_albaran": 990}],
    "M14_sv_ma9999": [{"ide": 1}],
    "M14_sv_ultimas": [{"ide": 50, "proide": 1}],
    "M14_sv_linea": [{"ide": 50, "docide": 9, "proide": 1, "anades": 0, "almide": 7, "dto": 5}],
    "M14_sv_plantilla": [{"ide": 40, "docide": 8, "proide": 1, "anades": 1, "almide": 6, "dto": 0}],
    "M16_caa_con_partida": [
        {"tipo": "sin_vincular", "partida_distinta": 0, "n": 100, "caa_de_la_partida": 99, "partida_sin_caa": 0,
         "caa_del_ctrpro": 0},
        {"tipo": "vinculada", "partida_distinta": 1, "n": 20, "caa_de_la_partida": 20, "partida_sin_caa": 0,
         "caa_del_ctrpro": 1},
        {"tipo": "vinculada", "partida_distinta": 0, "n": 50, "caa_de_la_partida": 50, "partida_sin_caa": 0,
         "caa_del_ctrpro": 50},
    ],
    "M16_caa_almacen": [{"tipo": "sin_vincular", "n": 100, "caa_pro_del_alm": 97, "caa_ser_del_alm": 1,
                         "alm_sin_caa": 0}],
    "M16_almacen_sin_vincular": [
        {"tipo": "almacen", "cabecera": "con_contrato", "n": 60, "alm_del_contrato": 58, "alm_de_la_ficha": 50,
         "cen_del_contrato": 58, "cen_de_la_ficha": 50},
        {"tipo": "almacen", "cabecera": "sin_contrato", "n": 40, "alm_del_contrato": 0, "alm_de_la_ficha": 39,
         "cen_del_contrato": 0, "cen_de_la_ficha": 39},
    ],
    "M16_ficha_obra": [{"obras": 100, "con_almide": 98, "almide_de_su_obra": 98, "con_cenide": 97}],
    "M17_ope": [{"ope": 1, "n": 500, "desde": 20250101, "hasta": 20261004},
                {"ope": 2, "n": 300, "desde": 20250101, "hasta": 20261004},
                {"ope": 3, "n": 4, "desde": 20250301, "hasta": 20260901}],
    "M17_emp_log": [{"emp": 1, "n": 304}],
    "M17_existe": [{"ope": 2, "n": 300, "con_existe": 299, "con_fecbaj": 0},
                   {"ope": 3, "n": 4, "con_existe": 0, "con_fecbaj": 0}],
    "M17_marcas": [{"est": 10, "con_fecbaj": 0, "n": 900}, {"est": 1, "con_fecbaj": 0, "n": 50}],
    "M2_conest": [{"tip": 14, "est": 1}, {"tip": 14, "est": 2}, {"tip": 14, "est": 3}, {"tip": 14, "est": 10}],
    "M18_refent": [{"tipo": "vinculada", "n": 600, "con_refent": 0}, {"tipo": "sin_vincular", "n": 400, "con_refent": 0}],
    "M18_propagacion": [{"n": 800, "con_refent": 0, "copiada": 0}],
}


def test_f009_t0_cada_medicion_se_recorre_entera_con_datos_de_ejemplo() -> None:
    cliente = _ClienteFalso(_DATOS)
    for clave, medir in t0.MEDICIONES.items():
        informe = medir(cliente)  # type: ignore[arg-type]
        assert informe.clave == clave and informe.conclusiones, clave
    textos = {k: m(_ClienteFalso(_DATOS)).texto() for k, m in t0.MEDICIONES.items()}  # type: ignore[arg-type]
    assert "Reglas en la muestra: A en 1 de 2" in textos["M5"] and "sin_mov en 1 de 2" in textos["M5"]
    assert "pagide (lista de reseteo)" not in textos["M14"] and "dca.pagide" in textos["M14"]
    assert "prepma (lista de reseteo)" in textos["M14"]


def test_f009_t0_mediciones_sin_datos_no_revientan() -> None:
    for clave, medir in t0.MEDICIONES.items():
        assert medir(_ClienteFalso({})).texto().startswith(f"=== {clave}"), clave  # type: ignore[arg-type]


def test_f009_t0_main_escribe_el_fichero_y_sigue_tras_un_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
                                                              capsys: pytest.CaptureFixture[str]) -> None:
    class _ConFallo(_ClienteFalso):
        def leer(self, sql: str, parametros: list[Any] | None = None, **kw: Any) -> t0.Resultado:
            if sql == t0.SQL["M7_desglose"]:
                raise t0.ErrorDeLectura("HTTP 500: error 130")
            return super().leer(sql, parametros, **kw)

    monkeypatch.setattr(t0, "cargar_config", lambda: ("https://ejemplo.invalid", "clave-secreta-123"))
    monkeypatch.setattr(t0, "ClienteLectura", lambda base, clave: _ConFallo(_DATOS))
    salida = tmp_path / "t0.txt"
    assert t0.main(["--solo", "M7", "M15", "--salida", str(salida)]) == 0
    texto = salida.read_text(encoding="utf-8")
    assert "=== M7 === ERROR: HTTP 500: error 130" in texto and "=== M15 ·" in texto
    impreso = capsys.readouterr().out
    assert "clave-secreta-123" not in impreso + texto and "ejemplo.invalid" not in impreso + texto


def test_f009_t0_errores_de_red_y_de_formato_del_cliente() -> None:
    class _Rota:
        def post(self, *a: Any, **k: Any) -> Any:
            raise ConnectionError("https://ejemplo.invalid caído")

    with pytest.raises(t0.ErrorDeLectura) as exc:
        t0.ClienteLectura("https://ejemplo.invalid", "k", sesion=_Rota()).leer("SELECT 1 AS x")
    assert "ejemplo.invalid" not in str(exc.value)

    class _SinJson(_Respuesta):
        def json(self) -> dict[str, Any]:
            raise ValueError("no es JSON")

    with pytest.raises(t0.ErrorDeLectura, match="sin JSON"):
        t0.ClienteLectura("https://ejemplo.invalid", "k", sesion=_Sesion([_SinJson({}, 502)])).leer("SELECT 1 AS x")


def test_f009_t0_marcadores_y_dotenv(tmp_path: Path) -> None:
    assert t0.marcadores(3) == "?, ?, ?"
    with pytest.raises(ValueError):
        t0.marcadores(0)
    env = tmp_path / ".env"
    env.write_text("# comentario\n\nSIN_IGUAL\nSIGRID_API_BASE_URL='https://a.invalid'\n", encoding="utf-8")
    assert t0.leer_dotenv(env) == {"SIGRID_API_BASE_URL": "https://a.invalid"}
    assert t0.leer_dotenv(tmp_path / "no-existe") == {}


# --- T0a (spec v5): M16, M17, M18 y las ampliaciones de M11 y M14 ---------------------------


def test_f009_t0a_las_mediciones_nuevas_sacan_su_conclusion() -> None:
    textos = {k: t0.MEDICIONES[k](_ClienteFalso(_DATOS)).texto() for k in ("M11", "M14", "M16", "M17", "M18")}  # type: ignore[arg-type]
    assert "Hipótesis de design §Analítica: CONFIRMADA." in textos["M16"]
    assert "Orden de R15 (contrato → ficha de obra → único alm): CONFIRMADO." in textos["M16"]
    assert "ope 3 con con_existe ≈ 0 ⇒ anular BORRA" in textos["M17"]
    assert "LIBRE: se escribe referencia_linea" in textos["M18"]
    assert "L8b JUSTIFICADA (acierta más la línea previa del mismo proveedor; IVA distinto con tipisp 1)" in textos["M11"]
    assert "fec = con.fec (v6)" in textos["M14"] and "fec 1000 de 1000" in textos["M14"]
    assert "dcapro.anades (lista de reseteo)" in textos["M14"]
    assert "dcapro.dto (FUERA de la lista)" in textos["M14"] and "dto (1)" in textos["M14"]
    assert "dcapro.almide" not in textos["M14"]  # propia del documento: no se señala


def test_f009_t0a_m11_ampliada_va_por_cada_ma9999_con_su_ide_como_parametro() -> None:
    productos = [{"ide": 31, "cod": "MA9999", "emp": 31}, {"ide": 1, "cod": "MA9999", "emp": 1}]
    cliente = _ClienteFalso({**_DATOS, "M11_productos": productos})
    t0.m11(cliente)  # type: ignore[arg-type]
    for clave in ("M11_iva_por_proveedor", "M11_iva_y_isp", "M11_acierto"):
        assert [p[-1] for k, p in cliente.llamadas if k == clave] == [31, 1], clave


def test_f009_t0a_m11_sigue_si_la_api_rechaza_over() -> None:
    class _SinOver(_ClienteFalso):
        def leer(self, sql: str, parametros: list[Any] | None = None, **kw: Any) -> t0.Resultado:
            if sql == t0.SQL["M11_acierto"]:
                raise t0.ErrorDeLectura("HTTP 400: OVER")
            return super().leer(sql, parametros, **kw)

    texto = t0.m11(_SinOver(_DATOS)).texto()  # type: ignore[arg-type]
    assert "M11_acierto (LAG ... OVER) no se pudo leer (HTTP 400: OVER)" in texto
    assert "L8b JUSTIFICADA (IVA distinto con tipisp 1)" in texto
    assert "ivacuo ≠ round(tot·iva, 2)" in texto


def test_f009_t0a_m17_repite_el_join_sin_emp_si_log_emp_sale_0_o_nulo() -> None:
    con_emp = _ClienteFalso(_DATOS)
    t0.m17(con_emp)  # type: ignore[arg-type]
    assert "M17_existe_sin_emp" not in [k for k, _ in con_emp.llamadas]
    datos = {**_DATOS, "M17_emp_log": [{"emp": -1, "n": 304}],
             "M17_existe": [{"ope": 3, "n": 4, "con_existe": 0}],
             "M17_existe_sin_emp": [{"ope": 3, "n": 4, "con_existe": 4, "con_fecbaj": 4}]}
    sin_emp = _ClienteFalso(datos)
    texto = t0.m17(sin_emp).texto()  # type: ignore[arg-type]
    assert "M17_existe_sin_emp" in [k for k, _ in sin_emp.llamadas]
    assert "log.emp sale 0 o nulo en 304 filas" in texto and "BORRA" not in texto


def test_f009_t0a_lectura_m17_borra_marca_o_t23() -> None:
    estados = {"1", "2", "3", "10"}
    assert "BORRA" in t0.lectura_m17([{"ope": 3, "n": 10, "con_existe": 0}], [], estados)
    marca = t0.lectura_m17([{"ope": 3, "n": 10, "con_existe": 10}], [{"est": 99, "con_fecbaj": 0, "n": 5}], estados)
    assert "MARCA" in marca and "est fuera de conest: 99" in marca
    assert "MARCA" in t0.lectura_m17([{"ope": 3, "n": 10, "con_existe": 10}], [{"est": 1, "con_fecbaj": 1, "n": 2}], estados)
    assert "T23" in t0.lectura_m17([{"ope": 3, "n": 10, "con_existe": 10}], [{"est": 1, "con_fecbaj": 0, "n": 2}], estados)
    assert "T23" in t0.lectura_m17([], [], estados)


def test_f009_t0a_lectura_m16_para_si_no_se_cumple() -> None:
    caa = [{"tipo": "sin_vincular", "partida_distinta": 0, "n": 100, "caa_de_la_partida": 80}]
    alm = [{"cabecera": "con_contrato", "n": 10, "alm_del_contrato": 2, "alm_de_la_ficha": 8}]
    texto = " ".join(t0.lectura_m16(caa, [], alm, {}))
    assert "§Analítica: NO confirmada ⇒ PARADA y v6." in texto
    assert "NO confirmado (contrato dominante: NO, ficha dominante: NO) ⇒ PARADA y v6." in texto


def test_f009_t0a_lectura_m18_y_sv_valores_en_los_limites() -> None:
    assert "LIBRE" in t0.lectura_m18([{"n": 1000, "con_refent": 1}], {})[0]
    assert "NO libre" in t0.lectura_m18([{"n": 1000, "con_refent": 2}], {})[0]
    assert "llegaría a la factura (N9)" in t0.lectura_m18([], {"n": 5, "copiada": 1})[1]
    assert t0.lectura_sv_valores({}) == ["No hay líneas sin vincular desde 2026: sin medición de columnas."]
    sv = t0.lectura_sv_valores({"n": 1000, "fec": 2, "fec_igual_albaran": 10})
    assert "fec 2 de 1000" in sv[1] and "no es la regla general" in sv[3]


def test_f009_t0a_main_con_la_lista_de_t0b(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(t0, "cargar_config", lambda: ("https://ejemplo.invalid", "clave-secreta-123"))
    monkeypatch.setattr(t0, "ClienteLectura", lambda base, clave: _ClienteFalso(_DATOS))
    salida = tmp_path / "t0b.txt"
    lista = ["M3", "M7", "M9", "M11", "M13", "M14", "M16", "M17", "M18"]
    assert t0.main(["--solo", *lista, "--salida", str(salida)]) == 0
    texto = salida.read_text(encoding="utf-8")
    assert all(f"=== {k} ·" in texto for k in lista) and "ERROR" not in texto


# --- T0a, ciclo 1 de revisión ----------------------------------------------------------------


def _ficha_ok() -> dict[str, Any]:
    return {"obras": 100, "con_almide": 100, "almide_de_su_obra": 100}


@pytest.mark.parametrize(("a", "confirmado"), [(50, True), (49, False)])
def test_f009_t0a_r1_dominante_en_el_limite_del_umbral(a: int, confirmado: bool) -> None:
    assert t0.UMBRAL_DOMINANTE == 0.5
    alm = [{"cabecera": "con_contrato", "n": 100, "alm_del_contrato": a, "alm_de_la_ficha": 40},
           {"cabecera": "sin_contrato", "n": 100, "alm_del_contrato": 0, "alm_de_la_ficha": 100}]
    texto = " ".join(t0.lectura_m16([], [], alm, _ficha_ok()))
    assert ("Orden de R15 (contrato → ficha de obra → único alm): CONFIRMADO." in texto) is confirmado
    assert "dominante = ≥ 50 % de las líneas y no menos que la alternativa" in texto


def test_f009_t0a_r1_dominante_exige_no_ser_menor_que_la_alternativa() -> None:
    alm = [{"cabecera": "con_contrato", "n": 100, "alm_del_contrato": 60, "alm_de_la_ficha": 61},
           {"cabecera": "sin_contrato", "n": 100, "alm_del_contrato": 0, "alm_de_la_ficha": 100}]
    assert "contrato dominante: NO" in " ".join(t0.lectura_m16([], [], alm, _ficha_ok()))


def test_f009_t0a_r2_sv_valores_no_clasifica_columnas_fuera_de_la_lista() -> None:
    sv = t0.lectura_sv_valores({"n": 1000, "tex": 300, "fec": 1000, "fec_igual_albaran": 0})
    clasificadas = [c.split(" ")[0] for linea in sv[:2] for c in linea.split(": ", 1)[1].rstrip(".").split(", ")]
    assert "tex" not in clasificadas and "texcom" in clasificadas
    assert "fec 1000 de 1000" in sv[1]
    assert "Fuera de la lista de reseteo (solo informativas): tex 300 de 1000 (30.0 %)." == sv[2]


def test_f009_t0a_l8b_isp_solo_cuenta_un_iva_que_el_resto_no_usa() -> None:
    # tipisp 1 usa un IVA (8) que también usan los demás: con `isp1 != resto` salía «justificada».
    mismo_iva = [{"tipisp": 0, "ivaide": 8}, {"tipisp": 0, "ivaide": 7}, {"tipisp": 1, "ivaide": 8}]
    assert "JUSTIFICADA" not in t0.lectura_l8b(None, mismo_iva)
    assert "IVA distinto con tipisp 1" in t0.lectura_l8b(None, [*mismo_iva, {"tipisp": 1, "ivaide": 9}])


def test_f009_t0a_l8b_compara_tasas_sobre_las_lineas_con_previa_del_proveedor() -> None:
    # En bruto 45 < 50 (inocua); en tasa 45/50 = 90 % frente a 50/100 = 50 % (justificada).
    acierto = {"lineas": 100, "sin_previa_del_prv": 50, "acierta_mismo_prv": 45, "acierta_cualquiera": 50}
    assert "L8b JUSTIFICADA (acierta más la línea previa del mismo proveedor)" in t0.lectura_l8b(acierto, [])
    igual = {"lineas": 100, "sin_previa_del_prv": 50, "acierta_mismo_prv": 25, "acierta_cualquiera": 50}
    assert "inocua" in t0.lectura_l8b(igual, [])


@pytest.mark.parametrize("rota", ["M11_iva_por_proveedor", "M11_iva_y_isp"])
def test_f009_t0a_m11_un_fallo_de_una_sentencia_nueva_no_pierde_el_bloque(rota: str) -> None:
    class _Rota(_ClienteFalso):
        def leer(self, sql: str, parametros: list[Any] | None = None, **kw: Any) -> t0.Resultado:
            if sql == t0.SQL[rota]:
                raise t0.ErrorDeLectura("HTTP 500: timeout")
            return super().leer(sql, parametros, **kw)

    texto = t0.m11(_Rota(_DATOS)).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer (HTTP 500: timeout)" in texto
    assert "ivacuo ≠ round(tot·iva, 2)" in texto and "acierta el IVA previo del mismo proveedor" in texto


@pytest.mark.parametrize(("rota", "sigue"), [
    ("M14_sv_valores", "[arrastre] línea 50"),
    ("M14_sv_ultimas", "reseteo confirmado"),
    ("M14_api", "reseteo confirmado"),
])
def test_f009_t0a_m14_un_fallo_de_una_parte_no_pierde_el_bloque(rota: str, sigue: str) -> None:
    class _Rota(_ClienteFalso):
        def leer(self, sql: str, parametros: list[Any] | None = None, **kw: Any) -> t0.Resultado:
            if sql == t0.SQL[rota]:
                raise t0.ErrorDeLectura("HTTP 500: timeout")
            return super().leer(sql, parametros, **kw)

    texto = t0.m14(_Rota(_DATOS)).texto()  # type: ignore[arg-type]
    assert "no se pudo leer (HTTP 500: timeout)" in texto and sigue in texto


# --- T0a-bis (ejecución del 2026-10-05): M9 y M11 sin cortes, M14b, M16b, M17b y reintento 1205 ----

_NUEVAS_T0A_BIS = (
    "M9_genericos", "M14b_pago_previo", "M16b_fuentes", "M16b_codigos", "M16b_muestra",
    "M17b_reutiliza", "M17b_perfil", "M17b_res",
)
_M9 = ("M9_por_tipsininv", "M9_por_partida", "M9_por_banderas", "M9_genericos", "M9_sin_mov_por_producto")
_M11_POR_PRODUCTO = ("M11_total_producto", "M11_lineas_producto", "M11_iva_por_proveedor", "M11_iva_y_isp",
                     "M11_acierto")

_DATOS_BIS: dict[str, list[dict[str, Any]]] = {
    "M9_por_banderas": [
        {"tipmov": 1, "tipinv": 1, "fam_tipinv": 1, "lineas": 900, "con_mov": 899, "movs": 899},
        {"tipmov": 1, "tipinv": 0, "fam_tipinv": 0, "lineas": 100, "con_mov": 98, "movs": 98},
        {"tipmov": 0, "tipinv": 0, "fam_tipinv": 0, "lineas": 50, "con_mov": 0, "movs": 0},
    ],
    "M9_genericos": [
        {"cod": "MA9999", "emp": 1, "tipmov": 1, "tipinv": 1, "lineas": 400, "con_mov": 400, "movs": 400},
        {"cod": "MA9999", "emp": 31, "tipmov": 1, "tipinv": 1, "lineas": 10, "con_mov": 10, "movs": 10},
        {"cod": "QA9999", "emp": 1, "tipmov": 0, "tipinv": 0, "lineas": 80, "con_mov": 0, "movs": 0},
    ],
    "M14b_pago_previo": [{"n": 1000, "sin_previo": 100, "pagide_del_previo": 880, "efeide_del_previo": 890,
                          "pagide_del_prv_con_previo": 740, "efeide_del_prv_con_previo": 800,
                          "pagide_del_prv": 829, "efeide_del_prv": 888}],
    "M16b_fuentes": [
        {"grupo": "MA9999", "partida": "con_partida", "n": 1000, "caa_cero": 10, "pro_gaside": 0, "cen_gaside": 5,
         "cab_caaide": 20, "ctr_caaide": 0, "par_caaide": 30, "caa_del_centro": 980},
        {"grupo": "resto", "partida": "sin_partida", "n": 200, "caa_cero": 150, "pro_gaside": 0, "cen_gaside": 0,
         "cab_caaide": 0, "ctr_caaide": 0, "par_caaide": 0, "caa_del_centro": 40},
    ],
    "M16b_codigos": [
        {"grupo": "MA9999", "partida": "con_partida", "n": 1000, "caa_cod_caagascod": 100, "caa_cod_caaexicod": 0,
         "caa_cod_cuafaccod": 0, "caa_cod_cuenta": 0, "caa_cod_empieza_por_cuenta": 0, "caa_cod_contiene_obra": 0,
         "caa_cod_contiene_centro": 0, "centro_y_caagascod": 960, "centro_y_cuenta": 0, "cuenta_6xx": 990,
         "cuenta_es_cuacomcod": 950},
        {"grupo": "resto", "partida": "sin_partida", "n": 200, "caa_cod_caagascod": 10, "caa_cod_caaexicod": 0,
         "caa_cod_cuafaccod": 0, "caa_cod_cuenta": 0, "caa_cod_empieza_por_cuenta": 0, "caa_cod_contiene_obra": 0,
         "caa_cod_contiene_centro": 0, "centro_y_caagascod": 10, "centro_y_cuenta": 0, "cuenta_6xx": 200,
         "cuenta_es_cuacomcod": 0},
    ],
    "M16b_muestra": [
        {"caa_cod": "6010001", "caagascod": "6010001", "caagascod_linea": "6010001", "caaexicod": "", "obra": "O-1",
         "centro": "C-1",
         "cuenta": "60100000", "partida": "con_partida", "lineas": 70},
        {"caa_cod": "O-2-601", "caagascod": "6010001", "caaexicod": "", "obra": "O-2", "centro": "C-2",
         "cuenta": "60100000", "partida": "sin_partida", "lineas": 30},
    ],
    "M17b_reutiliza": [
        {"caso": "no_existe", "n": 514, "con_alta_previa": 500, "con_fec_posterior": 0, "con_fec_anterior": 0},
        {"caso": "existe_con_alta_posterior", "n": 300, "con_alta_previa": 290, "con_fec_posterior": 300,
         "con_fec_anterior": 0},
        {"caso": "existe_sin_alta_posterior", "n": 8, "con_alta_previa": 8, "con_fec_posterior": 0,
         "con_fec_anterior": 8},
    ],
    "M17b_perfil": [{"ope": 2, "n": 822, "documentos": 800, "usuarios": 9, "estados": 1, "est_min": 0, "est_max": 0,
                     "con_tex": 0}],
    "M17b_res": [{"ope": 3, "res": "Impresión de documento", "n": 9000},
                 {"ope": 5, "res": "Modificación", "n": 80000},
                 {"ope": 30, "res": "XYZ", "n": 2000}],
}


def _datos_bis() -> dict[str, list[dict[str, Any]]]:
    return {**_DATOS, **_DATOS_BIS}


def test_f009_t0a_bis_existen_las_sentencias_nuevas() -> None:
    assert [k for k in _NUEVAS_T0A_BIS if k not in t0.SQL] == []


@pytest.mark.parametrize("nombre", _NUEVAS_T0A_BIS)
def test_f009_t0a_bis_las_sentencias_nuevas_van_parametrizadas_o_sin_valores_de_fuera(nombre: str) -> None:
    sql = t0.SQL[nombre]
    assert "{" not in sql and "MA9999" not in sql and "QA9999" not in sql, nombre
    if nombre.startswith(("M9", "M14b", "M16b_fuentes", "M16b_codigos")):
        assert "?" in sql, nombre


@pytest.mark.parametrize("nombre", _M9)
def test_f009_t0a_bis_m9_va_por_ventana_corta_sin_subconsultas_in(nombre: str) -> None:
    sql = t0.SQL[nombre]
    assert "IN (SELECT" not in sql.upper(), nombre
    assert "c.fec >= ? AND c.fec <= ?" in sql, nombre
    assert "m.docide = d.docide AND m.linide = d.ide" in sql, nombre  # índice doclin de mov


@pytest.mark.parametrize("nombre", [*_M11_POR_PRODUCTO, "M11_iva_usado"])
def test_f009_t0a_bis_m11_va_por_ventana_corta(nombre: str) -> None:
    sql = t0.SQL[nombre]
    assert "c.fec >= ? AND c.fec <= ?" in sql, nombre
    assert "20250101" not in sql and "20260101" not in sql, nombre


def test_f009_t0a_bis_m11_pasa_la_ventana_y_el_ide_de_cada_ma9999() -> None:
    productos = [{"ide": 31, "cod": "MA9999", "emp": 31}, {"ide": 1, "cod": "MA9999", "emp": 1}]
    cliente = _ClienteFalso({**_DATOS, "M11_productos": productos})
    t0.m11(cliente)  # type: ignore[arg-type]
    for clave in _M11_POR_PRODUCTO:
        assert [p for k, p in cliente.llamadas if k == clave] == [[*t0.VENTANA_M11, 31], [*t0.VENTANA_M11, 1]], clave
    assert [p for k, p in cliente.llamadas if k == "M11_iva_usado"] == [list(t0.VENTANA_M11)]


def test_f009_t0a_bis_m9_pasa_la_ventana_y_los_genericos() -> None:
    cliente = _ClienteFalso(_datos_bis())
    t0.m9(cliente)  # type: ignore[arg-type]
    llamadas = dict(cliente.llamadas)
    assert llamadas["M9_genericos"] == [*t0.VENTANA_M11, *t0.PRODUCTOS_GENERICOS]  # ciclo 1, obs. (b)
    assert llamadas["M9_por_banderas"] == list(t0.VENTANA_M9)


def _rompe(rota: str, datos: dict[str, list[dict[str, Any]]] | None = None) -> _ClienteFalso:
    class _Rota(_ClienteFalso):
        def leer(self, sql: str, parametros: list[Any] | None = None, **kw: Any) -> t0.Resultado:
            if sql == t0.SQL[rota] or (rota == "M11_productos" and sql.startswith("SELECT c.ide, c.cod, c.res")):
                raise t0.ErrorDeLectura("ReadTimeout al llamar a sql/read")
            return super().leer(sql, parametros, **kw)

    return _Rota(datos or _datos_bis())


@pytest.mark.parametrize("rota", _M9)
def test_f009_t0a_bis_m9_un_fallo_no_pierde_el_bloque(rota: str) -> None:
    texto = t0.m9(_rompe(rota)).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer (ReadTimeout al llamar a sql/read)" in texto
    assert texto.count("no se pudo leer") == 1


@pytest.mark.parametrize("rota", ["M11_productos", "M11_total_producto", "M11_lineas_producto", "M11_acierto",
                                  "M11_iva_usado"])
def test_f009_t0a_bis_m11_un_fallo_no_pierde_el_bloque(rota: str) -> None:
    texto = t0.m11(_rompe(rota)).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer (ReadTimeout" in texto or "M11_acierto (LAG ... OVER) no se pudo leer" in texto
    if rota != "M11_iva_usado":
        assert "ivacuo ≠ round(tot·iva, 2)" in texto


@pytest.mark.parametrize("rota", ["M16_caa_con_partida", "M16b_fuentes", "M16b_codigos", "M16b_muestra"])
def test_f009_t0a_bis_m16_un_fallo_no_pierde_el_bloque(rota: str) -> None:
    texto = t0.m16(_rompe(rota)).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer" in texto and "Orden de R15" in texto


@pytest.mark.parametrize("rota", ["M17_ope", "M17_existe", "M17b_reutiliza", "M17b_res"])
def test_f009_t0a_bis_m17_un_fallo_no_pierde_el_bloque(rota: str) -> None:
    texto = t0.m17(_rompe(rota)).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer" in texto and "Lectura automática" in texto


@pytest.mark.parametrize("rota", ["M14_prepma", "M14_prv", "M14b_pago_previo"])
def test_f009_t0a_bis_m14_un_fallo_no_pierde_la_comparacion(rota: str) -> None:
    texto = t0.m14(_rompe(rota)).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer" in texto
    assert "dcapro: columnas cuyo valor en la API no aparece en el escritorio" in texto


def test_f009_t0a_bis_lectura_m9_tipmov_decide_y_genericos() -> None:
    texto = " ".join(t0.lectura_m9(_DATOS_BIS["M9_por_banderas"], _DATOS_BIS["M9_genericos"]))
    assert "pro.tipmov DECIDE si la línea genera mov" in texto
    assert "pro.tipinv: no lo explica solo" in texto
    assert "MA9999 emp 1: SÍ genera mov (400 de 400" in texto
    assert "QA9999 emp 1: NO genera mov (0 de 80" in texto
    assert "SM9999 emp 1: sin líneas en la ventana" in texto


def test_f009_t0a_bis_lectura_m9_ninguna_bandera_y_a_veces() -> None:
    banderas = [{"tipmov": 1, "tipinv": 1, "lineas": 100, "con_mov": 60}]
    genericos = [{"cod": "MA9999", "emp": 1, "lineas": 100, "con_mov": 60}]
    texto = " ".join(t0.lectura_m9(banderas, genericos))
    assert "ni pro.tipmov ni pro.tipinv lo explican solos" in texto
    assert "MA9999 emp 1: a veces (60 de 100" in texto
    # Cero filas es «sin líneas»; no se pudo leer (None) es SIN MEDICIÓN (ciclo 1, cambio 2).
    vacio = " ".join(t0.lectura_m9([], []))
    assert "sin líneas en la ventana" in vacio and "SIN MEDICIÓN" not in vacio


def test_f009_t0a_bis_lectura_m16b_dice_que_fuente_domina() -> None:
    texto = " ".join(t0.lectura_m16b(_DATOS_BIS["M16b_fuentes"], _DATOS_BIS["M16b_codigos"]))
    # Ciclo 1, cambio 3: «caa del centro» (980) es una propiedad, no fija la caa: no compite. Domina la
    # mejor identificativa, la que sí se puede escribir como regla.
    assert ("MA9999 / con_partida (1000 líneas): domina «caa del centro con código = caagascod de la "
            "naturaleza del producto» 960 de 1000 (96.0 %) ⇒ REGLA") in texto
    assert "domina «caa del centro de la línea" not in texto
    assert "propiedades (no fijan la caa): caa del centro de la línea (caa.cenide = dcapro.cenide) 980 de 1000" in texto
    assert "resto / sin_partida (200 líneas): domina «caaide = 0» 150 de 200" in texto
    assert "cuenta financiera 6XX" in texto
    assert t0.UMBRAL_DOMINANTE == 0.5


def test_f009_t0a_bis_lectura_m16b_sin_dominante_y_desempate() -> None:
    fuentes = [{"grupo": "QA9999", "partida": "sin_partida", "n": 100, "caa_cero": 40, "pro_gaside": 0,
                "caa_del_centro": 90}]
    texto = " ".join(t0.lectura_m16b(fuentes, []))
    assert ("QA9999 / sin_partida (100 líneas): ninguna identificativa domina (la mejor: «caaide = 0» 40 de 100"
            in texto)
    # Empate entre la naturaleza de la línea y la del producto: se nombran las dos.
    codigos = [{"grupo": "SB9999", "partida": "con_partida", "n": 10, "lin_centro_y_caagascod": 10,
                "centro_y_caagascod": 10}]
    empate = " ".join(t0.lectura_m16b([], codigos))
    assert "domina «caa del centro con código = caagascod de la naturaleza de la línea»" in empate
    assert "empata con: caa del centro con código = caagascod de la naturaleza del producto" in empate
    assert t0.lectura_m16b([], []) == ["No hay líneas sin vincular desde 2025: sin medición del origen de caaide."]


@pytest.mark.parametrize("col", ["caa_del_centro", "caa_cod_empieza_por_cuenta", "caa_cod_contiene_obra",
                                 "caa_cod_contiene_centro", "centro_y_cuenta"])
def test_f009_t0a_bis_c1_las_propiedades_no_compiten_por_la_regla(col: str) -> None:
    assert col in dict(t0.PROPIEDADES_M16B) and col not in dict(t0.IDENTIFICATIVAS_M16B)
    fila = [{"grupo": "MA9999", "partida": "con_partida", "n": 100, col: 100, "caa_cero": 1}]
    texto = " ".join(t0.lectura_m16b(fila, []))
    assert "REGLA" not in texto and "ninguna identificativa domina (la mejor: «caaide = 0» 1 de 100" in texto


def test_f009_t0a_bis_c1_m16b_mide_tambien_la_naturaleza_de_la_linea() -> None:
    sql = t0.SQL["M16b_codigos"]
    assert "nt.ide = r.natide" in sql and "nl.ide = d.natide" in sql
    for col in ("lin_caa_cod_caagascod", "lin_caa_cod_caaexicod", "lin_centro_y_caagascod", "lin_centro_y_caaexicod",
                "centro_y_caaexicod", "nat_linea_igual_producto"):
        assert f"AS {col}" in sql, col
    for col in ("lin_caa_cod_caagascod", "lin_caa_cod_caaexicod", "lin_centro_y_caagascod", "lin_centro_y_caaexicod"):
        assert col in dict(t0.IDENTIFICATIVAS_M16B), col
    assert "nl.caagascod" in t0.SQL["M16b_muestra"]


def test_f009_t0a_bis_c1_tipmov_y_tipinv_son_byte_sin_isnull_con_literal() -> None:
    """`pro.tipmov`/`tipinv` son Byte: ISNULL(col, -1) toma el tipo de la columna (error 220 o -1 → 1)."""
    import re

    for nombre, sql in t0.SQL.items():
        assert not re.search(r"ISNULL\(\s*\w+\.tip(mov|inv)\b", sql, re.IGNORECASE), nombre
    for nombre in ("M9_por_banderas", "M9_genericos", "M9_sin_mov_por_producto"):
        assert "COALESCE(CAST(r.tipmov AS int), -1)" in t0.SQL[nombre], nombre
        assert "COALESCE(CAST(r.tipinv AS int), -1)" in t0.SQL[nombre], nombre


def test_f009_t0a_bis_c1_lecturas_distinguen_no_se_pudo_leer_de_cero_filas() -> None:
    assert "SIN MEDICIÓN" in " ".join(t0.lectura_m9(None, _DATOS_BIS["M9_genericos"]))
    sin_genericos = " ".join(t0.lectura_m9(_DATOS_BIS["M9_por_banderas"], None))
    assert "SIN MEDICIÓN" in sin_genericos and "sin líneas en la ventana" not in sin_genericos
    assert "pro.tipmov DECIDE" in sin_genericos
    assert "SIN MEDICIÓN" in " ".join(t0.lectura_m16b(None, None))
    assert "No hay líneas sin vincular" not in " ".join(t0.lectura_m16b(None, None))
    parcial = " ".join(t0.lectura_m16b(_DATOS_BIS["M16b_fuentes"], None))
    assert "M16b_codigos SIN MEDICIÓN" in parcial and "domina «caaide = 0» 150 de 200" in parcial
    assert "SIN MEDICIÓN" in t0.lectura_muestra_m16b(None)
    m17b = t0.lectura_m17b(None)
    assert "SIN MEDICIÓN" in m17b and "T23" not in m17b
    assert "sin ope 2" in t0.lectura_m17b([])
    assert "SIN MEDICIÓN" in " ".join(t0.lectura_ope(None))
    assert "SIN MEDICIÓN" in t0.lectura_m17(None, [], set())
    assert "SIN MEDICIÓN" in t0.lectura_m17([{"ope": 3, "n": 10, "con_existe": 10}], None, set())
    assert "SIN MEDICIÓN" in " ".join(t0.lectura_m16(None, [], [], {}))
    assert "SIN MEDICIÓN" in " ".join(t0.lectura_m16([], [], None, {}))
    assert "SIN MEDICIÓN" in " ".join(t0.lectura_m16([], [], [], None))
    assert "SIN MEDICIÓN" in t0.lectura_l8b(None, None)


@pytest.mark.parametrize(("medir", "rota", "prohibido", "esperado"), [
    ("m9", "M9_genericos", "sin líneas en la ventana", "M9_genericos SIN MEDICIÓN"),
    ("m9", "M9_por_banderas", "lo explican solos", "M9_por_banderas SIN MEDICIÓN"),
    ("m16", "M16b_fuentes", "No hay líneas sin vincular", "M16b_fuentes SIN MEDICIÓN"),
    ("m17", "M17b_reutiliza", "Lectura automática M17b: no concluyente", "M17b_reutiliza SIN MEDICIÓN"),
    ("m11", "M11_iva_y_isp", "L8b inocua (aciertan igual o menos): se queda.", "M11_iva_y_isp SIN MEDICIÓN"),
])
def test_f009_t0a_bis_c1_un_fallo_no_se_lee_como_dato_vacio(medir: str, rota: str, prohibido: str,
                                                            esperado: str) -> None:
    datos = _datos_bis()
    if rota == "M16b_fuentes":
        datos = {**datos, "M16b_codigos": []}
    if rota == "M11_iva_y_isp":
        datos = {**datos, "M11_acierto": [{"lineas": 90, "sin_previa_del_prv": 10, "acierta_mismo_prv": 1,
                                           "acierta_cualquiera": 60}]}

    class _Rota(_ClienteFalso):
        def leer(self, sql: str, parametros: list[Any] | None = None, **kw: Any) -> t0.Resultado:
            if sql == t0.SQL[rota] or (rota == "M16b_fuentes" and sql == t0.SQL["M16b_codigos"]):
                raise t0.ErrorDeLectura("ReadTimeout al llamar a sql/read")
            return super().leer(sql, parametros, **kw)

    texto = getattr(t0, medir)(_Rota(datos)).texto()
    assert prohibido not in texto and esperado in texto


def test_f009_t0a_bis_c1_lectura_m9_compara_el_codigo_sin_espacios() -> None:
    genericos = [{"cod": "MA9999  ", "emp": 1, "lineas": 10, "con_mov": 10},
                 {"cod": "QA9999 ", "emp": 1, "lineas": 10, "con_mov": 0}]
    texto = " ".join(t0.lectura_m9([], genericos))
    assert "MA9999 emp 1: SÍ genera mov" in texto and "QA9999 emp 1: NO genera mov" in texto


def test_f009_t0a_bis_c1_dcaproana_informativa_y_envuelta() -> None:
    sql = t0.SQL["M16b_dcaproana"]
    assert "dbo.dcaproana" in sql and "GROUP BY docproide" in sql
    datos = {**_datos_bis(), "M16b_dcaproana": [{"n": 1000, "con_ana": 40, "ana_caa_distinta": 5,
                                                  "ana_varias_filas": 3}]}
    texto = t0.m16(_ClienteFalso(datos)).texto()  # type: ignore[arg-type]
    assert "dcaproana: 40 de 1000 (4.0 %) sin vincular tienen reparto analítico" in texto
    assert "con caa distinta de dcapro.caaide 5" in texto
    assert "M16b_dcaproana no se pudo leer" in t0.m16(_rompe("M16b_dcaproana")).texto()  # type: ignore[arg-type]


def test_f009_t0a_bis_c1_ope_envio_con_tilde() -> None:
    assert "parece «envío»" in " ".join(t0.lectura_ope([{"ope": 7, "res": "Envío de documento", "n": 3}]))


def test_f009_t0a_bis_lectura_muestra_m16b_ve_el_patron_del_codigo() -> None:
    texto = t0.lectura_muestra_m16b(_DATOS_BIS["M16b_muestra"])
    assert "= caagascod 70 de 100" in texto and "contiene el código de obra 30 de 100" in texto
    assert "empieza por la cuenta financiera 0 de 100" in texto
    assert t0.lectura_muestra_m16b([]) == "Muestra vacía: sin patrón del código de caa."
    assert "= caagascod de la naturaleza de la línea" in texto


def test_f009_t0a_bis_lectura_m17b_borra_marca_o_no_concluyente() -> None:
    assert "anular BORRA" in t0.lectura_m17b(_DATOS_BIS["M17b_reutiliza"])
    assert "el cod se reutiliza" in t0.lectura_m17b(_DATOS_BIS["M17b_reutiliza"])
    sigue = [{"caso": "existe_sin_alta_posterior", "n": 100}]
    assert "MARCA" in t0.lectura_m17b(sigue)
    mezcla = [{"caso": "no_existe", "n": 50}, {"caso": "existe_sin_alta_posterior", "n": 50}]
    assert "no concluyente" in t0.lectura_m17b(mezcla)
    assert "no concluyente" in t0.lectura_m17b([]) and "sin ope 2" in t0.lectura_m17b([])


def test_f009_t0a_bis_significado_de_ope_por_su_resumen() -> None:
    texto = " ".join(t0.lectura_ope(_DATOS_BIS["M17b_res"]))
    assert "ope 3: parece «impresión»" in texto and "ope 5: parece «modificación»" in texto
    assert "ope 30: significado no deducible" in texto


def test_f009_t0a_bis_lectura_m14b_anterior_frente_a_maestro() -> None:
    texto = " ".join(t0.lectura_m14b(_DATOS_BIS["M14b_pago_previo"][0]))
    assert "pagide: albarán anterior 880 de 900" in texto and "maestro del proveedor 740 de 900" in texto
    assert "pagide: acierta más el ALBARÁN ANTERIOR" in texto
    maestro = {"n": 10, "sin_previo": 0, "pagide_del_previo": 5, "pagide_del_prv_con_previo": 9,
               "efeide_del_previo": 5, "efeide_del_prv_con_previo": 5}
    texto = " ".join(t0.lectura_m14b(maestro))
    assert "pagide: acierta más el MAESTRO" in texto and "efeide: empate" in texto
    assert t0.lectura_m14b({}) == ["Sin albaranes desde 2026-09 con un albarán anterior del mismo proveedor."]


def _respuesta_1205() -> _Respuesta:
    return _Respuesta({"ok": False, "error": "Error interno ejecutando sql/read.",
                       "details": {"exception": "('40001', '... interbloqueo ... (1205) (SQLExecDirectW)')"}}, 500)


def test_f009_t0a_bis_el_cliente_reintenta_ante_el_interbloqueo_1205() -> None:
    esperas: list[float] = []
    sesion = _Sesion([_respuesta_1205(), _Respuesta({"ok": True, "columns": ["n"], "rows": [[1]]})])
    cliente = t0.ClienteLectura("https://ejemplo.invalid", "k", sesion=sesion, dormir=esperas.append)
    assert cliente.leer("SELECT 1 AS n").filas == [{"n": 1}]
    assert len(sesion.llamadas) == 2 and esperas == [t0.ESPERA_INTERBLOQUEO_S]


def test_f009_t0a_bis_el_cliente_se_rinde_tras_los_reintentos_y_no_reintenta_otros_errores() -> None:
    esperas: list[float] = []
    sesion = _Sesion([_respuesta_1205() for _ in range(t0.REINTENTOS_INTERBLOQUEO + 1)])
    cliente = t0.ClienteLectura("https://ejemplo.invalid", "k", sesion=sesion, dormir=esperas.append)
    with pytest.raises(t0.ErrorDeLectura, match="1205"):
        cliente.leer("SELECT 1 AS n")
    assert len(sesion.llamadas) == t0.REINTENTOS_INTERBLOQUEO + 1 and len(esperas) == t0.REINTENTOS_INTERBLOQUEO
    otra = _Sesion([_Respuesta({"ok": False, "error": "timeout", "details": {}}, 500)])
    with pytest.raises(t0.ErrorDeLectura):
        t0.ClienteLectura("https://ejemplo.invalid", "k", sesion=otra, dormir=esperas.append).leer("SELECT 1 AS n")
    assert len(otra.llamadas) == 1


def test_f009_t0a_bis_main_con_la_lista_de_la_segunda_pasada(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(t0, "cargar_config", lambda: ("https://ejemplo.invalid", "clave-secreta-123"))
    monkeypatch.setattr(t0, "ClienteLectura", lambda base, clave: _ClienteFalso(_datos_bis()))
    salida = tmp_path / "t0bis.txt"
    lista = ["M9", "M11", "M14", "M16", "M17"]
    assert t0.main(["--solo", *lista, "--salida", str(salida)]) == 0
    texto = salida.read_text(encoding="utf-8")
    assert all(f"=== {k} ·" in texto for k in lista) and "ERROR" not in texto and "no se pudo leer" not in texto
    assert "SIN MEDICIÓN" not in texto
    for esperado in ("pro.tipmov DECIDE", "MA9999 emp 1: SÍ genera mov", "domina «", "anular BORRA",
                     "acierta más el ALBARÁN ANTERIOR", "ope 5: parece «modificación»"):
        assert esperado in texto, esperado


def test_f009_t0a_bis_m11_mide_y_concluye_qa9999_aparte_de_ma9999() -> None:
    """Spec v6: QA9999 entra en la lista blanca con MA9999; M11 los mide y concluye por separado."""
    productos = [{"ide": 1, "cod": "MA9999", "emp": 1}, {"ide": 5, "cod": "QA9999", "emp": 1},
                 {"ide": 7, "cod": "SB9999", "emp": 1}]
    cliente = _ClienteFalso({**_DATOS, "M11_productos": productos})
    texto = t0.m11(cliente).texto()  # type: ignore[arg-type]
    for clave in _M11_POR_PRODUCTO:
        assert [p[-1] for k, p in cliente.llamadas if k == clave] == [1, 5], clave
    assert "MA9999 emp 1: L8b" in texto and "QA9999 emp 1: L8b" in texto
    assert "QA9999 emp 1 (ide 5): total de líneas" in texto and "SB9999 emp 1: L8b" not in texto


# --- T0a-ter (ejecución del 2026-10-05 16:32): M16c, la regla del código de la caa -------------------
# Hipótesis de la muestra de M16b: caa = <obra o centro> + '.' + caagascod de la naturaleza de la LÍNEA
# tras el primer '.', en el centro de la línea; cueide = la cua de cuacomcod de la naturaleza.

_NUEVAS_T0A_TER = ("M16c_reglas", "M16c_naturalezas_ma", "M16c_vinculadas")

_DATOS_TER: dict[str, list[dict[str, Any]]] = {
    "M16c_reglas": [
        {"grupo": "MA9999", "partida": "con_partida", "n": 1000, "regla_linea_obra": 990, "regla_linea_centro": 990,
         "regla_producto_obra": 480, "regla_producto_centro": 480, "cueide_linea": 500, "cueide_producto": 1000,
         "linea_sin_mod": 10, "linea_sin_punto": 10, "linea_sin_naturaleza": 0, "producto_sin_mod": 0,
         "linea_caaexicod": 0, "producto_caaexicod": 0, "caa_repetida": 0, "obra_igual_centro": 1000},
        {"grupo": "resto", "partida": "sin_partida", "n": 200, "regla_linea_obra": 150, "regla_linea_centro": 140,
         "regla_producto_obra": 150, "regla_producto_centro": 140, "cueide_linea": 140, "cueide_producto": 141,
         "linea_sin_mod": 50, "linea_sin_punto": 40, "linea_sin_naturaleza": 5, "producto_sin_mod": 50,
         "linea_caaexicod": 3, "producto_caaexicod": 3, "caa_repetida": 2, "obra_igual_centro": 190},
    ],
    "M16c_naturalezas_ma": [
        {"nat_cod": "CDSB37", "nat_res": "Subcontratas", "caagascod": "MOD.CDSB37", "lineas": 600,
         "regla_linea_obra": 600, "regla_producto_obra": 100, "igual_producto": 100},
        {"nat_cod": "CDMA15", "nat_res": "Materiales", "caagascod": "MOD.CDMA15", "lineas": 350,
         "regla_linea_obra": 345, "regla_producto_obra": 345, "igual_producto": 350},
        {"nat_cod": "VAR", "nat_res": "Varios", "caagascod": "", "lineas": 50, "regla_linea_obra": 0,
         "regla_producto_obra": 0, "igual_producto": 50},
    ],
    "M16c_vinculadas": [
        {"grupo": "MA9999", "lineas": 500, "ctrpro": 400, "caa_informada": 400, "regla_linea_obra": 396,
         "regla_linea_centro": 396},
        {"grupo": "resto", "lineas": 120, "ctrpro": 100, "caa_informada": 100, "regla_linea_obra": 99,
         "regla_linea_centro": 98},
    ],
}


def _datos_ter() -> dict[str, list[dict[str, Any]]]:
    return {**_datos_bis(), **_DATOS_TER}


def test_f009_t0a_ter_existen_las_sentencias_de_m16c() -> None:
    assert [k for k in _NUEVAS_T0A_TER if k not in t0.SQL] == []


@pytest.mark.parametrize("nombre", _NUEVAS_T0A_TER)
def test_f009_t0a_ter_m16c_va_parametrizada_y_sin_isnull_con_literal_negativo(nombre: str) -> None:
    sql = t0.SQL[nombre]
    assert "?" in sql and "{" not in sql, nombre
    for literal in ("MA9999", "QA9999", "SM9999", "SB9999"):
        assert literal not in sql, (nombre, literal)
    assert ", -1)" not in sql, nombre  # nada de ISNULL(..., -1) (columnas Byte, ciclo 1 de T0a-bis)


def test_f009_t0a_ter_m16c_construye_el_codigo_con_la_naturaleza_de_la_linea_y_la_del_producto() -> None:
    sql = t0.SQL["M16c_reglas"]
    assert "nl.ide = d.natide" in sql and "nt.ide = r.natide" in sql
    for nat in ("nl", "nt"):
        gas = f"RTRIM(LTRIM({nat}.caagascod))"
        assert f"CHARINDEX('.', {gas}) > 0" in sql, nat  # sin '.' no casa
        assert f"SUBSTRING({gas}, CHARINDEX('.', {gas}) + 1, 24)" in sql, nat
        assert f"RTRIM(LTRIM(cf.cod)) = RTRIM(LTRIM({nat}.cuacomcod))" in sql, nat
    for cod in ("oc", "ec"):  # código de la obra y, en la variante, el del centro
        assert f"RTRIM(LTRIM({cod}.cod)) + '.' + SUBSTRING(" in sql, cod
    assert "k.cenide = d.cenide" in sql and "RTRIM(LTRIM(kc.cod)) = " in sql
    for col in ("regla_linea_obra", "regla_linea_centro", "regla_producto_obra", "regla_producto_centro",
                "cueide_linea", "cueide_producto", "linea_sin_mod", "linea_sin_punto", "linea_sin_naturaleza",
                "producto_sin_mod", "linea_caaexicod", "producto_caaexicod", "caa_repetida", "obra_igual_centro"):
        assert f"AS {col}," in sql or f"AS {col} " in sql, col
    assert "'MOD.'" in sql and "nl.caaexicod" in sql and "nt.caaexicod" in sql


def test_f009_t0a_ter_m16c_la_regla_exige_que_centro_y_codigo_identifiquen_una_sola_caa() -> None:
    """Una regla escribible busca LA caa por (centro, código): si hay dos, no fija ninguna."""
    for nombre in _NUEVAS_T0A_TER:
        sql = t0.SQL[nombre]
        assert "HAVING COUNT(*) > 1" in sql and "u.cod IS NULL" in sql, nombre
    assert "u.cenide = k.cenide AND u.cod = RTRIM(LTRIM(kc.cod))" in t0.SQL["M16c_reglas"]


def test_f009_t0a_ter_m16c_vinculadas_usa_la_linea_del_contrato() -> None:
    sql = t0.SQL["M16c_vinculadas"]
    assert "t.ide = d.linoriide" in sql and "d.docoritip = 44" in sql
    assert "tn.ide = t.natide" in sql and "kt.cenide = t.cenide" in sql
    assert "COUNT(DISTINCT x.ctrpro)" in sql
    assert "RTRIM(LTRIM(ot.cod)) + '.' + SUBSTRING(" in sql and "RTRIM(LTRIM(et.cod)) + '.' + SUBSTRING(" in sql


def test_f009_t0a_ter_m16_pasa_los_grupos_y_el_generico_de_las_naturalezas() -> None:
    cliente = _ClienteFalso(_datos_ter())
    t0.m16(cliente)  # type: ignore[arg-type]
    llamadas = dict(cliente.llamadas)
    grupos = [t0.EMPRESA_GENERICOS, *t0.PRODUCTOS_GENERICOS]
    assert llamadas["M16c_reglas"] == grupos and llamadas["M16c_vinculadas"] == grupos
    assert llamadas["M16c_naturalezas_ma"] == [t0.EMPRESA_GENERICOS, "MA9999"]


def test_f009_t0a_ter_lectura_m16c_regla_escribible_y_manda_la_linea() -> None:
    assert t0.UMBRAL_REGLA_ESCRIBIBLE == 0.95
    texto = " ".join(t0.lectura_m16c(_DATOS_TER["M16c_reglas"]))
    assert ("MA9999 / con_partida (1000 líneas): caa ⇒ REGLA escribible «obra.sufijo de caagascod de la "
            "naturaleza de la línea» 990 de 1000 (99.0 %) (empata con: centro.sufijo de caagascod de la "
            "naturaleza de la línea)") in texto
    assert "cueide ⇒ REGLA escribible «cuacomcod de la naturaleza del producto» 1000 de 1000" in texto
    assert ("resto / sin_partida (200 líneas): caa sin regla escribible (la mejor: «obra.sufijo de caagascod de "
            "la naturaleza de la línea» 150 de 200 (75.0 %)") in texto
    assert "naturaleza de la línea sin «MOD.» 50 de 200" in texto and "caa con (centro, código) repetido 2 de 200" in texto
    # Total: 1140 de 1200 = 95,0 %: en el límite cuenta como regla.
    assert "TOTAL (1200 líneas): caa ⇒ REGLA escribible «obra.sufijo de caagascod de la naturaleza de la línea» " \
           "1140 de 1200 (95.0 %)" in texto
    assert "Hipótesis M16c (caa = <obra o centro>.<caagascod tras el '.'> de la naturaleza de la LÍNEA): " \
           "CONFIRMADA" in texto


@pytest.mark.parametrize(("aciertos", "regla"), [(95, True), (94, False)])
def test_f009_t0a_ter_lectura_m16c_en_el_limite_del_umbral(aciertos: int, regla: bool) -> None:
    fila = [{"grupo": "QA9999", "partida": "sin_partida", "n": 100, "regla_linea_obra": aciertos,
             "regla_producto_obra": 10, "cueide_linea": 0, "cueide_producto": 0}]
    texto = " ".join(t0.lectura_m16c(fila))
    assert ("caa ⇒ REGLA escribible «obra.sufijo de caagascod de la naturaleza de la línea»" in texto) is regla
    assert ("Hipótesis M16c (caa = <obra o centro>.<caagascod tras el '.'> de la naturaleza de la LÍNEA): "
            + ("CONFIRMADA" if regla else "NO confirmada")) in texto


def test_f009_t0a_ter_lectura_m16c_manda_el_producto_si_acierta_mas() -> None:
    fila = [{"grupo": "SB9999", "partida": "con_partida", "n": 100, "regla_linea_obra": 50,
             "regla_producto_obra": 99}]
    texto = " ".join(t0.lectura_m16c(fila))
    assert "caa ⇒ REGLA escribible «obra.sufijo de caagascod de la naturaleza del producto» 99 de 100" in texto
    assert "NO confirmada" in texto and "con la del producto 99 de 100" in texto


def test_f009_t0a_ter_lecturas_m16c_distinguen_sin_medicion_de_cero_filas() -> None:
    rota = " ".join(t0.lectura_m16c(None))
    assert "M16c_reglas SIN MEDICIÓN" in rota and "cero filas" not in rota and "REGLA" not in rota
    vacia = " ".join(t0.lectura_m16c([]))
    assert "cero filas" in vacia and "SIN MEDICIÓN" not in vacia and "CONFIRMADA" not in vacia
    assert "M16c_naturalezas_ma SIN MEDICIÓN" in t0.lectura_m16c_naturalezas(None)
    assert "cero filas" in t0.lectura_m16c_naturalezas([]) and "SIN MEDICIÓN" not in t0.lectura_m16c_naturalezas([])
    assert "M16c_vinculadas SIN MEDICIÓN" in t0.lectura_m16c_vinculadas(None)
    assert "cero filas" in t0.lectura_m16c_vinculadas([]) and "SIN MEDICIÓN" not in t0.lectura_m16c_vinculadas([])


def test_f009_t0a_ter_lectura_de_las_naturalezas_de_ma9999() -> None:
    texto = t0.lectura_m16c_naturalezas(_DATOS_TER["M16c_naturalezas_ma"])
    assert "Naturalezas de la línea en MA9999 (empresa 1), TOP 3 (1000 líneas)" in texto
    assert "«CDSB37» Subcontratas (MOD.CDSB37) 600 de 1000 (60.0 %)" in texto
    assert "la regla de la línea no llega al 95 % en: «VAR» 0 de 50 (0.0 %)" in texto
    assert "«CDMA15»" not in texto.split("no llega")[1]  # 345 de 350 = 98,6 %: sí llega


def test_f009_t0a_ter_lectura_del_control_con_las_vinculadas() -> None:
    texto = t0.lectura_m16c_vinculadas(_DATOS_TER["M16c_vinculadas"])
    assert "Control con las vinculadas (500 líneas de contrato)" in texto
    assert "obra.sufijo de caagascod de la naturaleza de la línea del contrato 495 de 500 (99.0 %)" in texto
    assert "con el centro 494 de 500" in texto and "la regla también explica las del contrato" in texto
    malo = [{"grupo": "resto", "ctrpro": 100, "regla_linea_obra": 10, "regla_linea_centro": 20}]
    assert "NO sigue la regla" in t0.lectura_m16c_vinculadas(malo)


@pytest.mark.parametrize("rota", _NUEVAS_T0A_TER)
def test_f009_t0a_ter_un_fallo_de_m16c_no_pierde_el_bloque_ni_se_lee_como_vacio(rota: str) -> None:
    texto = t0.m16(_rompe(rota, _datos_ter())).texto()  # type: ignore[arg-type]
    assert f"{rota} no se pudo leer (ReadTimeout" in texto and f"{rota} SIN MEDICIÓN" in texto
    assert texto.count("no se pudo leer") == 1 and "cero filas" not in texto
    assert "Orden de R15" in texto and "dcaproana" in texto  # lo de después sigue


def test_f009_t0a_ter_main_solo_m16_con_m16c(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(t0, "cargar_config", lambda: ("https://ejemplo.invalid", "clave-secreta-123"))
    monkeypatch.setattr(t0, "ClienteLectura", lambda base, clave: _ClienteFalso(_datos_ter()))
    salida = tmp_path / "t0ter.txt"
    assert t0.main(["--solo", "M16", "--salida", str(salida)]) == 0
    texto = salida.read_text(encoding="utf-8")
    assert "=== M16 ·" in texto and "M16c" in texto.split("\n")[2]  # el título del bloque la nombra
    assert "SIN MEDICIÓN" not in texto and "no se pudo leer" not in texto
    for esperado in ("M16c MA9999 / con_partida (1000 líneas): caa ⇒ REGLA escribible",
                     "M16c Naturalezas de la línea en MA9999", "M16c Control con las vinculadas",
                     "M16c Hipótesis M16c"):
        assert esperado in texto, esperado
