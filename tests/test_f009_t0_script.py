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
    assert list(t0.MEDICIONES) == [f"M{i}" for i in range(1, 16)]


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
