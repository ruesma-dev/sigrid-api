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
def test_f003_r5_sin_referencias_a_otra_base(sql: str) -> None:
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
def test_f003_r3_detecta_la_base_de_un_nombre_de_tres_partes(sql: str, esperada: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == [esperada]


def test_f003_r3_detecta_varias_bases_distintas_sin_repetir() -> None:
    sql = (
        "SELECT n.ide FROM ruesma.dbo.gra n "
        "JOIN ruesma_rep.dbo.gra d ON d.cod = n.cod "
        "JOIN ruesma.dbo.rcg r ON r.gra = n.ide"
    )
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma", "ruesma_rep"]


# --- R1 / R2 / R7: la lista blanca ------------------------------------------


def test_f003_r1_rechaza_una_base_fuera_de_la_lista() -> None:
    sql = "INSERT INTO ruesma_rep.dbo.gra (ide) SELECT 0 WHERE 1 = 0"
    with pytest.raises(DatabaseReferenceError) as excinfo:
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")
    mensaje = str(excinfo.value)
    # R6: el mensaje nombra la base detectada y las permitidas.
    assert "ruesma_rep" in mensaje
    assert "ruesma" in mensaje
    assert "escritura" in mensaje


def test_f003_r2_acepta_una_base_que_si_esta_en_la_lista() -> None:
    sql = "INSERT INTO ruesma.dbo.gra (ide) SELECT 0 WHERE 1 = 0"
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


def test_f003_r8_acepta_lectura_cruzada_cuando_las_dos_bases_estan_permitidas() -> None:
    sql = "SELECT d.cod FROM ruesma_rep.dbo.gra d JOIN ruesma.dbo.gra n ON n.cod = d.cod"
    DatabaseReferenceGuard.validate(
        sql, allowed=["ruesma", "ruesma_rep"], contexto="lectura"
    )


def test_f003_r3_la_comparacion_no_distingue_mayusculas() -> None:
    sql = "SELECT ide FROM RUESMA.DBO.CON"
    DatabaseReferenceGuard.validate(sql, allowed=["ruesma"], contexto="lectura")
    DatabaseReferenceGuard.validate(sql, allowed=["RuEsMa"], contexto="lectura")


def test_f003_r1_lista_vacia_rechaza_cualquier_referencia_cualificada() -> None:
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
def test_f003_r4_rechaza_siempre_los_nombres_de_cuatro_partes(sql: str) -> None:
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
def test_f003_r5_los_literales_y_comentarios_no_cuentan(sql: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == []


def test_f003_r3_una_referencia_real_junto_a_un_literal_si_cuenta() -> None:
    sql = "SELECT ide FROM ruesma_rep.dbo.gra WHERE nom = 'a.b.c'"
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma_rep"]


# --- R11: ante la duda, rechaza ---------------------------------------------


def test_f003_r11_un_literal_sin_cerrar_no_deja_pasar_la_referencia_de_despues() -> None:
    """
    Un SQL con una comilla sin cerrar es basura que el motor rechazaría, pero el
    detector no puede saber dónde acaba el literal. Ante la duda, rechaza.
    """
    sql = "SELECT ide FROM dbo.gra WHERE res = 'sin cerrar AND x = ruesma_rep.dbo.gra"
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


def test_f003_r11_un_comentario_de_bloque_sin_cerrar_tambien_rechaza() -> None:
    sql = "SELECT ide FROM dbo.gra /* sin cerrar"
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="escritura")


def test_f003_r5_el_sql_vacio_no_rompe() -> None:
    assert DatabaseReferenceGuard.extract_database_references("") == []


# --- Falsos positivos que encontró el reviewer (F-003, pasada 1) -------------


@pytest.mark.parametrize(
    "sql",
    [
        # `esquema.tabla.*` es SQL válido y se leía como tres partes.
        "SELECT dbo.con.* FROM dbo.con",
        "SELECT dbo.con.*, dbo.obr.* FROM dbo.con JOIN dbo.obr ON obr.ide = con.ide",
    ],
)
def test_f003_r5_el_asterisco_cualificado_no_es_una_base(sql: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == []
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


def test_f003_r3_el_asterisco_no_esconde_una_base_de_verdad() -> None:
    """Descartar la parte vacía final no puede servir para colarse."""
    sql = "SELECT ruesma_rep.dbo.gra.* FROM ruesma_rep.dbo.gra"
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma_rep"]


@pytest.mark.parametrize(
    "sql",
    [
        # Un apóstrofo dentro de corchetes es una letra, no un literal.
        "SELECT [Client's Name] FROM dbo.con",
        "SELECT ide FROM dbo.con WHERE [Owner's Id] = ?",
        # Y con un literal de verdad detrás, que sí debe neutralizarse.
        "SELECT [Client's Name] FROM dbo.con WHERE res = 'a.b.c'",
    ],
)
def test_f003_r5_un_apostrofo_entre_corchetes_no_abre_un_literal(sql: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == []
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


def test_f003_r3_una_base_sigue_viendose_junto_a_un_identificador_con_apostrofo() -> None:
    sql = "SELECT [Client's Name] FROM ruesma_rep.dbo.gra"
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma_rep"]


def test_f003_r11_un_corchete_sin_cerrar_rechaza() -> None:
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(
            "SELECT [sin cerrar FROM dbo.con", allowed=PERMITIDAS, contexto="lectura"
        )


def test_f003_r3_el_corchete_de_cierre_escapado_no_confunde() -> None:
    """SQL Server escapa `]` duplicándolo dentro del identificador."""
    sql = "SELECT [raro]]nombre] FROM ruesma_rep.dbo.gra"
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma_rep"]


# --- Robustez del neutralizador (mutación F-003, pasada 1) ------------------
#
# El neutralizador promete en su docstring «sustituye por espacios el contenido
# de literales y comentarios, CONSERVANDO LAS POSICIONES». Esa promesa importa:
# si el relleno no midiera lo mismo que lo sustituido, dos identificadores
# separados por un literal podrían quedar pegados y formar una referencia que
# no existe, o al revés. Estos tests la fijan.

NEUTRALIZAR = DatabaseReferenceGuard._neutralizar_literales_y_comentarios


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM dbo.gra WHERE cod = 'ruesma_rep.dbo.gra'",
        "SELECT ide FROM dbo.gra WHERE res = 'con ''comilla'' dentro'",
        "SELECT ide FROM dbo.gra -- comentario hasta el final\nWHERE ide = ?",
        "SELECT ide FROM dbo.gra /* bloque */ WHERE ide = ?",
        "SELECT [Client's Name] FROM dbo.gra WHERE res = 'x'",
        "SELECT ide FROM [ruesma_rep].[dbo].[gra]",
        "SELECT ide FROM dbo.gra WHERE a = '' AND b = ''",
        "SELECT ide FROM dbo.gra /**/ WHERE ide = ?",
        "SELECT ide FROM dbo.gra WHERE res = 'a' /* c */ -- fin\n",
    ],
)
def test_f003_r11_el_neutralizador_conserva_la_longitud(sql: str) -> None:
    assert len(NEUTRALIZAR(sql)) == len(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM dbo.gra WHERE cod = 'ruesma_rep.dbo.gra'",
        "SELECT ide FROM dbo.gra /* ruesma_rep.dbo.gra */ WHERE ide = ?",
    ],
)
def test_f003_r11_el_neutralizador_borra_el_contenido_pero_no_el_sql(sql: str) -> None:
    limpio = NEUTRALIZAR(sql)
    assert "ruesma_rep" not in limpio
    assert "FROM dbo.gra" in limpio


def test_f003_r11_el_neutralizador_conserva_los_corchetes_tal_cual() -> None:
    """El identificador entre corchetes NO se borra: el detector lo necesita."""
    assert NEUTRALIZAR("SELECT x FROM [ruesma_rep].[dbo].[gra]") == (
        "SELECT x FROM [ruesma_rep].[dbo].[gra]"
    )


# Casos límite de los escapes: un carácter de más o de menos al buscar el
# cierre y el análisis se desalinea entero.


@pytest.mark.parametrize(
    ("sql", "esperada"),
    [
        # Literal vacío: las dos comillas son apertura y cierre, no un escape.
        ("SELECT ide FROM ruesma_rep.dbo.gra WHERE a = ''", ["ruesma_rep"]),
        ("SELECT ide FROM dbo.gra WHERE a = '' AND b = 'x.y.z'", []),
        # Comilla escapada pegada al cierre.
        ("SELECT ide FROM ruesma_rep.dbo.gra WHERE a = 'x'''", ["ruesma_rep"]),
        # Identificador entre corchetes vacío.
        ("SELECT [] FROM ruesma_rep.dbo.gra", ["ruesma_rep"]),
        # Corchete de cierre escapado, y una base de verdad detrás.
        ("SELECT [a]]b] FROM ruesma_rep.dbo.gra", ["ruesma_rep"]),
        # Comentario de línea sin salto final.
        ("SELECT ide FROM ruesma_rep.dbo.gra -- final", ["ruesma_rep"]),
        ("SELECT ide FROM dbo.gra -- ruesma_rep.dbo.gra", []),
        # Comentario de bloque vacío.
        ("SELECT ide FROM ruesma_rep.dbo.gra /**/", ["ruesma_rep"]),
        ("SELECT ide FROM dbo.gra /*ruesma_rep.dbo.gra*/", []),
    ],
)
def test_f003_r3_los_escapes_no_desalinean_el_analisis(sql: str, esperada: list) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == esperada


# --- La lista blanca, en sus bordes -----------------------------------------


def test_f003_r6_con_lista_vacia_el_mensaje_dice_ninguna() -> None:
    with pytest.raises(DatabaseReferenceError) as excinfo:
        DatabaseReferenceGuard.validate(
            "SELECT ide FROM ruesma.dbo.con", allowed=[], contexto="lectura"
        )
    assert "(ninguna)" in str(excinfo.value)


def test_f003_r6_las_entradas_vacias_de_la_lista_no_cuentan_como_base() -> None:
    """
    Una lista mal escrita (`ALLOWED_WRITE_DATABASES=",,"`) no puede acabar
    autorizando nada, ni ensuciar el mensaje de error.
    """
    with pytest.raises(DatabaseReferenceError) as excinfo:
        DatabaseReferenceGuard.validate(
            "SELECT ide FROM ruesma.dbo.con", allowed=["", "   ", None], contexto="lectura"
        )
    assert "(ninguna)" in str(excinfo.value)


def test_f003_r2_los_espacios_sobrantes_de_la_lista_se_ignoran() -> None:
    DatabaseReferenceGuard.validate(
        "SELECT ide FROM ruesma.dbo.con", allowed=["  ruesma  "], contexto="lectura"
    )


@pytest.mark.parametrize("sql", ["", "   ", "\n\t "])
def test_f003_r5_un_sql_vacio_o_en_blanco_no_rompe(sql: str) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == []
    DatabaseReferenceGuard.validate(sql, allowed=[], contexto="lectura")


# --- Supervivientes de la campaña 2 (F-003) ---------------------------------


def test_f003_r3_una_base_se_detecta_aunque_solo_aparezca_con_asterisco() -> None:
    """
    Mata el mutante `partes[:-1] -> partes[:-2]`. El test anterior no lo mataba
    porque el mismo SQL nombraba la base otra vez sin asterisco: bastaba la
    segunda aparición para que el resultado saliera bien por casualidad.
    """
    assert DatabaseReferenceGuard.extract_database_references(
        "SELECT ruesma_rep.dbo.gra.* FROM otra"
    ) == ["ruesma_rep"]


def test_f003_r11_una_comilla_escapada_no_cierra_el_literal_antes_de_tiempo() -> None:
    """
    Si el escape `''` se leyera desalineado, el literal cerraría antes y el
    texto de dentro pasaría a analizarse como SQL: una base inventada.
    """
    sql = "SELECT ide FROM dbo.gra WHERE res = 'x''ruesma_rep.dbo.gra'"
    assert DatabaseReferenceGuard.extract_database_references(sql) == []


def test_f003_r11_un_literal_escapado_no_esconde_la_base_que_viene_despues() -> None:
    sql = "SELECT ide FROM ruesma_rep.dbo.gra WHERE res = 'x''y' AND z = 1"
    assert DatabaseReferenceGuard.extract_database_references(sql) == ["ruesma_rep"]


# --- Propiedad: una base prohibida no se cuela nunca ------------------------
#
# Los mutantes que sobreviven viven casi todos en la aritmética de los escapes
# del neutralizador (`''` dentro de un literal, `]]` dentro de un identificador).
# Lo que hay que garantizar no es cada índice, sino la PROPIEDAD que sostiene la
# defensa entera: por mucho literal, comentario o corchete que rodee a una
# referencia real, la referencia se ve. Este test la recorre a lo bruto sobre
# todas las combinaciones, que es la forma honesta de defender lo que queda.

_ENTORNOS = [
    "",
    "WHERE res = 'texto'",
    "WHERE res = 'con ''comilla'' dentro'",
    "WHERE res = 'punto.y.punto'",
    "-- comentario con ruesma_rep.dbo.gra dentro\n",
    "/* bloque con a.b.c dentro */",
    "WHERE [Client's Name] = ?",
    "WHERE [raro]]nombre] = ?",
    "WHERE a = '' AND b = ''",
    "/**/",
    "WHERE res = 'x''y'",
]

_REFERENCIAS = [
    "otra_base.dbo.tabla",
    "[otra_base].[dbo].[tabla]",
    "otra_base..tabla",
    "OTRA_BASE.DBO.TABLA",
    "[otra_base]..tabla",
]


@pytest.mark.parametrize("referencia", _REFERENCIAS)
@pytest.mark.parametrize("antes", _ENTORNOS)
@pytest.mark.parametrize("despues", _ENTORNOS)
def test_f003_r1_una_base_prohibida_nunca_se_cuela(
    referencia: str, antes: str, despues: str
) -> None:
    """
    Sea cual sea el contexto, `otra_base` no está en la lista y la sentencia
    debe rechazarse. Un falso positivo sería molesto; un falso NEGATIVO aquí
    sería el agujero que esta feature vino a cerrar.
    """
    sql = f"SELECT ide FROM {referencia} {antes} {despues}"
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


@pytest.mark.parametrize("antes", _ENTORNOS)
@pytest.mark.parametrize("despues", _ENTORNOS)
def test_f003_r5_una_consulta_limpia_nunca_se_rechaza(antes: str, despues: str) -> None:
    """
    La otra mitad de la propiedad, y la que protege la condición del humano: sin
    referencia cualificada, ningún contexto puede provocar un rechazo.
    """
    sql = f"SELECT ide FROM dbo.con {antes} {despues}"
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")
    assert DatabaseReferenceGuard.extract_database_references(sql) == []


# --- Lo que destapó la pasada 2 de revisión ---------------------------------
#
# El arreglo de `dbo.con.*` descartaba la parte vacía final SIEMPRE, sin mirar
# qué seguía al punto. Eso abrió el guardia: `tempdb..#t` es T-SQL válido, y al
# no saber leer `#t` la referencia se leía como dos partes y la base se colaba.
# R11 dice justo lo contrario: ante lo que no se entiende, se rechaza.


@pytest.mark.parametrize(
    "sql",
    [
        # Tablas temporales: el `#` no es un identificador que el reconocedor
        # sepa leer, pero la referencia a la base es real.
        "SELECT * FROM tempdb..#t",
        "SELECT * FROM tempdb.dbo.##global",
        "SELECT * FROM ruesma_rep.dbo.#t",
        # Otros terceros elementos que tampoco casan como identificador.
        "SELECT * FROM ruesma_rep.dbo.$x",
        "SELECT * FROM ruesma_rep.dbo.9tabla",
        "SELECT * FROM ruesma_rep.dbo. ",
    ],
)
def test_f003_r11_un_tercer_elemento_ilegible_no_deja_pasar_la_base(sql: str) -> None:
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT dbo.con.* FROM dbo.con",
        "SELECT dbo.con. * FROM dbo.con",
    ],
)
def test_f003_r5_el_asterisco_sigue_siendo_la_unica_excepcion(sql: str) -> None:
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


def test_f003_r3_el_asterisco_no_esconde_la_base_ni_con_el_arreglo() -> None:
    assert DatabaseReferenceGuard.extract_database_references(
        "SELECT ruesma_rep.dbo.gra.* FROM otra"
    ) == ["ruesma_rep"]


# --- Fallo cerrado ante un delimitador mal formado (R11) --------------------
#
# Estos matan los supervivientes 7, 8, 9 y 12, que el análisis daba por
# equivalentes y no lo eran: los cuatro hacen que el guardia falle ABIERTO ante
# un corchete sin cerrar o un comentario pegado a un operador.


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT [a]] FROM x",
        "SELECT * FROM [gra]]",
        "SELECT [a]]b FROM x",
    ],
)
def test_f003_r11_un_corchete_mal_cerrado_falla_cerrado(sql: str) -> None:
    """
    `[a]]` es un identificador que empieza y nunca termina: el `]]` es un
    corchete escapado, no un cierre. No se puede analizar, así que se rechaza.
    """
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


def test_f003_r5_un_comentario_pegado_a_un_operador_no_confunde() -> None:
    """
    `a*/*...*/b` es T-SQL corriente: un `*` de multiplicar pegado a la apertura
    de un comentario. El contenido del comentario no es una referencia.
    """
    sql = "SELECT a*/*ruesma_rep.dbo.gra*/b FROM dbo.con"
    assert DatabaseReferenceGuard.extract_database_references(sql) == []
    DatabaseReferenceGuard.validate(sql, allowed=PERMITIDAS, contexto="lectura")


def test_f003_r1_una_referencia_seguida_de_un_asterisco_de_multiplicar_no_se_pierde() -> None:
    """
    La excepción del `*` vale solo cuando la última parte está VACÍA. Si no se
    comprobaran las dos cosas, `ruesma_rep.dbo.gra*2` perdería la última parte,
    quedaría en dos y la base se colaría.
    """
    assert DatabaseReferenceGuard.extract_database_references(
        "SELECT ruesma_rep.dbo.gra*2 FROM x"
    ) == ["ruesma_rep"]
    with pytest.raises(DatabaseReferenceError):
        DatabaseReferenceGuard.validate(
            "SELECT ruesma_rep.dbo.gra*2 FROM x", allowed=PERMITIDAS, contexto="lectura"
        )


@pytest.mark.parametrize(
    ("sql", "esperada"),
    [
        ("SELECT [a]]b] FROM ruesma_rep.dbo.gra", ["ruesma_rep"]),
        ("SELECT [a]]] FROM ruesma_rep.dbo.gra", ["ruesma_rep"]),
        ("SELECT [a]]b]]c] FROM ruesma_rep.dbo.gra", ["ruesma_rep"]),
        ("SELECT [x]]ruesma_rep.dbo.gra] FROM dbo.con", []),
    ],
)
def test_f003_r3_el_escape_de_corchete_no_desalinea(sql: str, esperada: list) -> None:
    assert DatabaseReferenceGuard.extract_database_references(sql) == esperada


def test_f003_r11_dos_identificadores_delimitados_pegados_no_cuelgan() -> None:
    """
    `[a][b]` no es T-SQL válido, pero el detector no puede colgarse con ello:
    un guardia que se cuelga es una denegación de servicio con la function key.
    """
    assert DatabaseReferenceGuard.extract_database_references(
        "SELECT [a][b] FROM ruesma_rep.dbo.gra"
    ) == ["ruesma_rep"]
