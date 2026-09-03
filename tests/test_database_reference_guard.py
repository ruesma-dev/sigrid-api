# tests/test_database_reference_guard.py
"""
F-003 · El detector de referencias a otras bases de datos.

Estos tests no tocan red ni base de datos: el detector es un módulo puro que
recibe una cadena SQL y una lista blanca.
"""
from __future__ import annotations

import pytest

from infrastructure.security.database_reference_guard import (
    DatabaseReferenceError,
    DatabaseReferenceGuard,
)

PERMITIDAS = ["ruesma"]


# --- R5: uno y dos nombres se ignoran ---------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM con",
        "SELECT ide FROM dbo.con",
        "SELECT c.ide, o.cod FROM dbo.con c JOIN dbo.obr o ON o.ide = c.ide",
        "INSERT INTO dbo.gra (ide, cod) VALUES (?, ?)",
        "UPDATE dbo.ctr SET estser = 1 WHERE ide = ?",
        # Alias con punto: dos partes, no es una base.
        "SELECT t.valor FROM dbo.tabla t WHERE t.ide = ?",
    ],
)
def test_sin_referencias_a_otra_base(sql: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == []
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


# --- R3: tres partes, en todas sus formas -----------------------------------


@pytest.mark.parametrize(
    ("sql", "esperada"),
    [
        ("SELECT ide FROM ruesma_rep.dbo.gra", "ruesma_rep"),
        ("SELECT ide FROM ruesma_rep..gra", "ruesma_rep"),
        ("SELECT ide FROM [ruesma_rep].[dbo].[gra]", "ruesma_rep"),
        ('SELECT ide FROM "ruesma_rep"."dbo"."gra"', "ruesma_rep"),
        ("SELECT ide FROM RUESMA_REP.DBO.GRA", "ruesma_rep"),
        ("SELECT ide FROM RuEsMa_ReP.dbo.gra", "ruesma_rep"),
        ("SELECT ide FROM ruesma_rep . dbo . gra", "ruesma_rep"),
        ("SELECT ide FROM [ruesma_rep]..gra", "ruesma_rep"),
        ("INSERT INTO ruesma_rep.dbo.gra (ide) SELECT 0 WHERE 1 = 0", "ruesma_rep"),
        ("UPDATE ruesma_rep.dbo.gra SET res = res WHERE 1 = 0", "ruesma_rep"),
        ("DELETE FROM ruesma_rep.dbo.gra WHERE ide = ?", "ruesma_rep"),
        ("SELECT ide FROM master.dbo.spt_values", "master"),
    ],
)
def test_detecta_la_base_de_un_nombre_de_tres_partes(sql: str, esperada: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == [esperada]


def test_detecta_varias_bases_distintas_sin_repetir() -> None:
    sql = (
        "SELECT n.ide FROM ruesma.dbo.gra n "
        "JOIN ruesma_rep.dbo.gra d ON d.cod = n.cod "
        "JOIN ruesma.dbo.rcg r ON r.gra = n.ide"
    )
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma", "ruesma_rep"]


# --- R1 / R2 / R7: la lista blanca ------------------------------------------


def test_rechaza_una_base_fuera_de_la_lista() -> None:
    sql = "INSERT INTO ruesma_rep.dbo.gra (ide) SELECT 0 WHERE 1 = 0"
    with pytest.raises(DatabaseReferenceError) as excinfo:
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")
    mensaje = str(excinfo.value)
    # R6: el mensaje nombra la base detectada y las permitidas.
    assert "ruesma_rep" in mensaje
    assert "ruesma" in mensaje
    assert "escritura" in mensaje


def test_acepta_una_base_que_si_esta_en_la_lista() -> None:
    sql = "INSERT INTO ruesma.dbo.gra (ide) SELECT 0 WHERE 1 = 0"
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


def test_acepta_lectura_cruzada_cuando_las_dos_bases_estan_permitidas() -> None:
    sql = "SELECT d.cod FROM ruesma_rep.dbo.gra d JOIN ruesma.dbo.gra n ON n.cod = d.cod"
    DatabaseReferenceGuard.validate(
        sql, allowed=["ruesma", "ruesma_rep"], contexto="lectura"
    )


def test_la_comparacion_no_distingue_mayusculas() -> None:
    sql = "SELECT ide FROM RUESMA.DBO.CON"
    DatabaseReferenceGuard.validate(sql, allowed=["ruesma"], contexto="lectura")
    DatabaseReferenceGuard.validate(sql, allowed=["RuEsMa"], contexto="lectura")


def test_lista_vacia_rechaza_cualquier_referencia_cualificada() -> None:
    sql = "SELECT ide FROM ruesma.dbo.con"
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=[], contexto="escritura")


# --- R4: cuatro partes, siempre fuera ---------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM servidor.ruesma.dbo.con",
        "SELECT ide FROM [servidor].[ruesma].[dbo].[con]",
        "SELECT ide FROM servidor.ruesma..con",
        "INSERT INTO otro.ruesma.dbo.gra (ide) SELECT 0 WHERE 1 = 0",
    ],
)
def test_rechaza_siempre_los_nombres_de_cuatro_partes(sql: str) -> None:
    with pytest.raises(DatabaseReferenceError) as excinfo:
        DatabaseReferenceGuard.validate(sql, allowed=["ruesma", "servidor", "otro"], contexto="lectura")
    assert "cuatro partes" in str(excinfo.value).lower() or "servidor" in str(excinfo.value).lower()


# --- Literales y comentarios no son referencias -----------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM dbo.gra WHERE cod = 'ruesma_rep.dbo.gra'",
        "SELECT ide FROM dbo.gra WHERE nom = 'fichero.con.puntos.pdf'",
        "SELECT ide FROM dbo.gra -- ojo con ruesma_rep.dbo.gra\n WHERE ide = ?",
        "SELECT ide FROM dbo.gra /* ni ruesma_rep.dbo.gra ni nada */ WHERE ide = ?",
        # Comilla simple escapada dentro del literal.
        "SELECT ide FROM dbo.gra WHERE res = 'no es ''ruesma_rep.dbo.gra'' de verdad'",
    ],
)
def test_los_literales_y_comentarios_no_cuentan(sql: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == []


def test_una_referencia_real_junto_a_un_literal_si_cuenta() -> None:
    sql = "SELECT ide FROM ruesma_rep.dbo.gra WHERE nom = 'a.b.c'"
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma_rep"]


# --- R11: ante la duda, rechaza ---------------------------------------------


def test_un_literal_sin_cerrar_no_deja_pasar_la_referencia_de_despues() -> None:
    """
    Un SQL con una comilla sin cerrar es basura que el motor rechazaría, pero el
    detector no puede saber dónde acaba el literal. Ante la duda, rechaza.
    """
    sql = "SELECT ide FROM dbo.gra WHERE res = 'sin cerrar AND x = ruesma_rep.dbo.gra"
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


def test_un_comentario_de_bloque_sin_cerrar_tambien_rechaza() -> None:
    sql = "SELECT ide FROM dbo.gra /* sin cerrar"
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


def test_el_sql_vacio_no_rompe() -> None:
    assert DatabaseReferenceGuard.extract_database_references("") == []
