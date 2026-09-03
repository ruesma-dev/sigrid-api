# tests/test_sql_query_guard_bases.py
"""
F-003 · El guardia de lectura también mira las bases nombradas dentro del SQL.

La clase `TestConsultasRealesDelEcosistema` es la que importa de verdad: son
las consultas que hoy se envían a la API desde otros repositorios, localizadas
en el inventario del 2026-09-03. La condición que puso el humano al aprobar la
feature fue «no puede fallar la escritura/lectura que se hace ahora», y esto es
lo que la comprueba en vez de suponerla.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from infrastructure.security.sql_query_guard import QueryValidationError, SqlQueryGuard

# La lista real de la Function App desplegada, comprobada el 2026-09-03.
ALLOWED_DATABASES_DESPLEGADAS = ["master", "ruesma_rep", "ruesma"]


@dataclass
class SettingsDoble:
    allowed_databases: list[str] = field(
        default_factory=lambda: list(ALLOWED_DATABASES_DESPLEGADAS)
    )
    allowed_query_prefixes: list[str] = field(default_factory=lambda: ["SELECT", "WITH"])
    default_query_timeout_seconds: int = 30
    max_query_timeout_seconds: int = 120
    default_max_rows: int = 200
    max_allowed_rows: int = 1000


@dataclass
class PeticionDoble:
    database: str
    sql: str
    timeout_seconds: int | None = None
    max_rows: int | None = None


def guardia(**ajustes) -> SqlQueryGuard:
    return SqlQueryGuard(SettingsDoble(**ajustes))


def peticion(sql: str, database: str = "ruesma") -> PeticionDoble:
    return PeticionDoble(database=database, sql=sql)


# --- R8: la lectura cruzada legítima sigue funcionando ----------------------


class TestConsultasRealesDelEcosistema:
    """Consultas que hoy funcionan y que NO pueden empezar a fallar."""

    @pytest.mark.parametrize(
        "sql",
        [
            # albaranes-persistencia · diagnose_sigrid_contrato_docs.py
            (
                "SELECT g.ide, g.cod FROM dbo.gra g "
                "LEFT JOIN ruesma_rep.dbo.gra AS g2 ON g2.cod = g.cod"
            ),
            # ídem, con el nombre entre corchetes que produce safe_db_name()
            "SELECT g.ide FROM dbo.gra g JOIN [ruesma_rep].dbo.gra AS g2 ON g2.cod = g.cod",
            # diagnose_sigrid_contrato_gra_modificado.py · gra_table interpolada
            (
                "SELECT g.ide, DATALENGTH(g.ima) AS bytes FROM [ruesma_rep].dbo.gra AS g "
                "WHERE g.cod = ?"
            ),
            # trace_sigrid_rcg_dual.py
            (
                "SELECT r.ide, g.cod FROM dbo.rcg r "
                "LEFT JOIN ruesma_rep.dbo.gra AS g ON g.ide = r.gra"
            ),
            # postventa-incidencias · 13_caracterizacion_grafico_url.ps1
            (
                "SELECT g.ide, rep.cod FROM dbo.gra g "
                "LEFT JOIN ruesma_rep.dbo.gra rep ON rep.cod = g.cod"
            ),
            # El patrón del propio spike de F-002.
            (
                "SELECT d.cod, DATALENGTH(d.ima) FROM ruesma_rep.dbo.gra d "
                "JOIN ruesma.dbo.gra n ON n.cod = d.cod"
            ),
            # master está en la lista desplegada, así que también pasa.
            "SELECT name FROM master.dbo.spt_values WHERE type = ?",
        ],
    )
    def test_las_consultas_que_hoy_funcionan_siguen_pasando(self, sql: str) -> None:
        guardia().validate(peticion(sql))

    @pytest.mark.parametrize(
        "sql",
        [
            "SELECT ide FROM dbo.con WHERE tip = ? AND cod = ?",
            "SELECT c.ide, o.cod FROM dbo.con c JOIN dbo.obr o ON o.ide = c.obride",
            "WITH t AS (SELECT ide FROM dbo.con) SELECT * FROM t",
            "SELECT SUM(canfac / NULLIF(can, 0) * tot) FROM dbo.ctrpro WHERE docide = ?",
            "SELECT ide FROM dbo.gra WHERE nom = 'parte.firmado.pdf'",
        ],
    )
    def test_las_consultas_de_una_y_dos_partes_ni_se_tocan(self, sql: str) -> None:
        guardia().validate(peticion(sql))


# --- R7: salir de la lista blanca sí se rechaza -----------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM otra_base.dbo.tabla",
        "SELECT ide FROM [msdb].[dbo].[sysjobs]",
        "SELECT ide FROM tempdb..cosa",
    ],
)
def test_rechaza_una_base_fuera_de_allowed_databases(sql: str) -> None:
    with pytest.raises(QueryValidationError) as excinfo:
        guardia().validate(peticion(sql))
    assert "lectura" in str(excinfo.value)


def test_rechaza_los_nombres_de_cuatro_partes_tambien_en_lectura() -> None:
    with pytest.raises(QueryValidationError) as excinfo:
        guardia().validate(peticion("SELECT ide FROM servidor.ruesma.dbo.con"))
    assert "cuatro partes" in str(excinfo.value).lower()


def test_si_se_quitara_ruesma_rep_de_la_lista_la_lectura_cruzada_se_rechaza() -> None:
    """
    Documenta la dependencia: la lectura cruzada de los scripts de diagnóstico
    funciona porque `ruesma_rep` está en ALLOWED_DATABASES. Si alguien la quita,
    esos scripts dejan de funcionar, y este test dice por qué.
    """
    solo_negocio = guardia(allowed_databases=["ruesma"])
    with pytest.raises(QueryValidationError):
        solo_negocio.validate(
            peticion("SELECT g.ide FROM dbo.gra g JOIN ruesma_rep.dbo.gra d ON d.cod = g.cod")
        )


def test_las_palabras_prohibidas_siguen_actuando() -> None:
    with pytest.raises(QueryValidationError) as excinfo:
        guardia().validate(peticion("SELECT ide FROM dbo.con WHERE ide = 1 DROP TABLE dbo.con"))
    assert "no permitida" in str(excinfo.value)


def test_la_sentencia_unica_sigue_actuando_antes_que_todo_lo_demas() -> None:
    with pytest.raises(QueryValidationError) as excinfo:
        guardia().validate(peticion("SELECT ide FROM dbo.con; SELECT ide FROM dbo.gra"))
    assert "única sentencia" in str(excinfo.value)
