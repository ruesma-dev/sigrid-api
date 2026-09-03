# tests/test_sql_write_guard_bases.py
"""
F-003 · El guardia de escritura también mira las bases nombradas dentro del SQL.

Sin red y sin base de datos: se doblan `Settings` y la petición con objetos
mínimos que exponen solo lo que el guardia consulta. Se doblan a propósito en
vez de construir los modelos reales, porque los validadores de
`SqlWriteRequest` llaman a `get_settings()` y eso leería el `.env` de la
máquina, que no tiene nada que hacer en un test unitario.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from infrastructure.security.sql_write_guard import SqlWriteGuard, WriteValidationError


@dataclass
class SettingsDoble:
    allowed_write_databases: list[str] = field(default_factory=lambda: ["ruesma"])
    allowed_write_prefixes: list[str] = field(
        default_factory=lambda: ["INSERT", "UPDATE", "DELETE"]
    )
    max_statements_per_batch: int = 20
    require_where_on_update_delete: bool = True
    default_write_timeout_seconds: int = 30
    max_write_timeout_seconds: int = 120
    write_enabled: bool = True


@dataclass
class SentenciaDoble:
    sql: str


@dataclass
class PeticionDoble:
    database: str
    statements: list[SentenciaDoble]
    timeout_seconds: int | None = None


def guardia(**ajustes) -> SqlWriteGuard:
    return SqlWriteGuard(SettingsDoble(**ajustes))


def peticion(sql: str, database: str = "ruesma") -> PeticionDoble:
    return PeticionDoble(database=database, statements=[SentenciaDoble(sql=sql)])


# --- R1: el agujero que cierra esta feature ---------------------------------


def test_f003_r1_rechaza_escribir_en_la_documental_aunque_el_campo_database_este_permitido() -> None:
    """
    Es exactamente la petición con la que se midió el agujero el 2026-09-03:
    database permitido, pero la sentencia nombra la base documental.
    """
    peticion_maliciosa = peticion(
        "INSERT INTO ruesma_rep.dbo.gra (ide) SELECT 0 WHERE 1 = 0"
    )
    with pytest.raises(WriteValidationError) as excinfo:
        guardia().validate(peticion_maliciosa)
    mensaje = str(excinfo.value)
    assert "ruesma_rep" in mensaje
    assert "Sentencia #1" in mensaje


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE ruesma_rep.dbo.gra SET res = res WHERE 1 = 0",
        "DELETE FROM ruesma_rep.dbo.gra WHERE ide = ?",
        "INSERT INTO [ruesma_rep].[dbo].[gra] (ide) SELECT 0 WHERE 1 = 0",
        "INSERT INTO ruesma_rep..gra (ide) SELECT 0 WHERE 1 = 0",
        "INSERT INTO RUESMA_REP.DBO.GRA (ide) SELECT 0 WHERE 1 = 0",
        "INSERT INTO master.dbo.spt_monitor (lastrun) SELECT GETDATE() WHERE 1 = 0",
    ],
)
def test_f003_r3_rechaza_cualquier_forma_de_nombrar_una_base_no_permitida(sql: str) -> None:
    with pytest.raises(WriteValidationError):
        guardia().validate(peticion(sql))


def test_f003_r1_rechaza_aunque_la_sentencia_culpable_no_sea_la_primera() -> None:
    lote = PeticionDoble(
        database="ruesma",
        statements=[
            SentenciaDoble("INSERT INTO dbo.gra (ide) VALUES (?)"),
            SentenciaDoble("UPDATE dbo.ctr SET estser = 1 WHERE ide = ?"),
            SentenciaDoble("INSERT INTO ruesma_rep.dbo.gra (ide) VALUES (?)"),
        ],
    )
    with pytest.raises(WriteValidationError) as excinfo:
        guardia().validate(lote)
    assert "Sentencia #3" in str(excinfo.value)


# --- R2 y R10: lo que hoy funciona debe seguir funcionando ------------------


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO dbo.gra (ide, cod) VALUES (?, ?)",
        "INSERT INTO gra (ide, cod) VALUES (?, ?)",
        "UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?",
        "DELETE FROM dbo.aux WHERE ide = ?",
        "INSERT INTO ruesma.dbo.gra (ide) SELECT 0 WHERE 1 = 0",
        "UPDATE [ruesma].[dbo].[con] SET est = ? WHERE ide = ?",
        # Un literal con puntos no debe confundirse con una referencia.
        "UPDATE dbo.gra SET nom = 'parte.firmado.pdf' WHERE ide = ?",
        # Una columna cualificada por alias son dos partes, no una base.
        "UPDATE g SET g.res = ? FROM dbo.gra g WHERE g.ide = ?",
    ],
)
def test_f003_r10_sigue_aceptando_las_escrituras_normales(sql: str) -> None:
    guardia().validate(peticion(sql))


def test_f003_r2_acepta_la_documental_si_alguien_la_pone_en_la_lista() -> None:
    """
    El guardia aplica la política, no la decide. Si mañana se decide abrir la
    documental, se abre en la configuración y el guardia obedece.
    """
    guardia(allowed_write_databases=["ruesma", "ruesma_rep"]).validate(
        peticion("INSERT INTO ruesma_rep.dbo.gra (ide) VALUES (?)")
    )


# --- R4 ---------------------------------------------------------------------


def test_f003_r4_rechaza_los_nombres_de_cuatro_partes() -> None:
    with pytest.raises(WriteValidationError) as excinfo:
        guardia(allowed_write_databases=["ruesma", "servidor"]).validate(
            peticion("INSERT INTO servidor.ruesma.dbo.gra (ide) VALUES (?)")
        )
    assert "cuatro partes" in str(excinfo.value).lower()


# --- R6: el mensaje ayuda y no filtra nada ----------------------------------


def test_f003_r6_el_mensaje_nombra_la_base_y_la_lista_sin_filtrar_credenciales() -> None:
    with pytest.raises(WriteValidationError) as excinfo:
        guardia().validate(peticion("INSERT INTO ruesma_rep.dbo.gra (ide) VALUES (?)"))
    mensaje = str(excinfo.value).lower()
    assert "ruesma_rep" in mensaje
    assert "escritura" in mensaje
    for prohibido in ("password", "user_rw", "server=", "tcp:"):
        assert prohibido not in mensaje


# --- Las comprobaciones anteriores siguen mandando --------------------------


def test_f003_r10_la_lista_de_prefijos_sigue_actuando_antes() -> None:
    """Un SELECT se rechaza por prefijo, no por base: el orden no cambió."""
    with pytest.raises(WriteValidationError) as excinfo:
        guardia().validate(peticion("SELECT ide FROM ruesma_rep.dbo.gra"))
    assert "comiencen por" in str(excinfo.value)


def test_f003_r10_el_where_obligatorio_sigue_actuando() -> None:
    with pytest.raises(WriteValidationError) as excinfo:
        guardia().validate(peticion("UPDATE dbo.gra SET res = ?"))
    assert "WHERE" in str(excinfo.value)
