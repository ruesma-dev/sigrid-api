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
    assert totales == [[31], [1]]


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
        assert [p for k, p in cliente.llamadas if k == clave] == [[31], [1]], clave


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
