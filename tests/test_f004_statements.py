# tests/test_f004_statements.py
"""
F-004 · R11, R13, R16, R18, R19 y R20: el constructor de sentencias.

Es el corazon de la feature y por eso se compara el SQL **caracter a
caracter**: una columna omitida en `gra` no falla, se queda en NULL (ninguna
tiene DEFAULT [MEDIDO]), y una fila documental con `cod` o `emp` distintos del
de negocio deja el grafico "sin fichero" sin que el motor avise.

Constantes tomadas de `progress/explore_F-004_mediciones.md` §2.1-2.3 y de
`progress/explore_F-004_relacion_gra.md`. Sin red y sin base de datos.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

import pytest

from application.use_cases.concepto_grafico_statements import (
    ConceptoGraficoStatements,
    construir_cod,
    hora_local_de_madrid,
)
from infrastructure.security.database_reference_guard import (
    DatabaseReferenceError,
    DatabaseReferenceGuard,
)
from infrastructure.security.identifier_guard import IdentifierValidationError

_NEGOCIO = "ruesma"
_DOCUMENTAL = "ruesma_rep"

#: Las 29 columnas de `dbo.gra`, en el orden en que se midieron.
_GRA_29 = (
    "ide", "cod", "emp", "res", "tex", "cla", "usu", "fec", "nom", "nomori",
    "ima", "gratipide", "vin", "estcon", "cam", "tipocu", "texrev", "numrev",
    "salfec", "salhor", "salusu", "saltex", "mntide", "guid", "graant", "anx",
    "ori", "pul", "tip",
)

#: Las 7 columnas reales de `dbo.rcg` (`feclee` y `fecalt` no constan en
#: `sigrid_tablas.md`, pero existen y valen 0 en las 3.680 filas medidas).
_RCG_7 = ("ide", "con", "gra", "pos", "cla", "feclee", "fecalt")

_SHA = "1a2b3c4d" + "0" * 56


def local(*partes: int) -> datetime:
    """Hora local de Madrid: naive a proposito, es lo que sella Sigrid."""
    return datetime(*partes)  # noqa: DTZ001


_AHORA = local(2026, 9, 5, 12, 30, 45)


@pytest.fixture
def sentencias() -> ConceptoGraficoStatements:
    return ConceptoGraficoStatements(database=_NEGOCIO, documental=_DOCUMENTAL)


def filas(sentencias: ConceptoGraficoStatements, **cambios: object):
    argumentos = {
        "ahora": _AHORA,
        "sha256": _SHA,
        "emp": 1,
        "usu": "aechevarria",
        "nom": "RS26.08 - 0123 PARTE FIRMADO.pdf",
        "res": "PARTE FIRMADO",
        "gratipide": 35,
        "contenido": b"%PDF-1.4 binario",
    }
    argumentos.update(cambios)
    return sentencias.construir_filas_gra(**argumentos)


# --- R18: las lecturas L1-L6, literales ------------------------------------


def test_f004_r18_l1_lee_el_concepto(sentencias: ConceptoGraficoStatements) -> None:
    assert sentencias.leer_concepto(2811179) == (
        "SELECT ide, tip, emp, cod, res FROM dbo.con WHERE ide = ?",
        [2811179],
    )


def test_f004_r18_l2_lee_la_clase_de_grafico(sentencias: ConceptoGraficoStatements) -> None:
    assert sentencias.leer_clase(35) == (
        "SELECT ide, cod, res, fecbaj, tipaso FROM dbo.auxgra WHERE ide = ?",
        [35],
    )


def test_f004_r18_l3_lee_el_usuario(sentencias: ConceptoGraficoStatements) -> None:
    assert sentencias.leer_usuario("aechevarria") == (
        "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?",
        ["aechevarria"],
    )


def test_f004_r18_l4_calcula_la_posicion_siguiente(sentencias: ConceptoGraficoStatements) -> None:
    """`pos` = 64 x posicion dentro del concepto [MEDIDO: 795 filas con 64,
    1.991 con 128, 448 con 192...]."""
    assert sentencias.siguiente_pos(2811179) == (
        "SELECT ISNULL(MAX(pos), 0) + 64, COUNT(*) FROM dbo.rcg WHERE con = ?",
        [2811179],
    )


def test_f004_r18_l5_busca_la_idempotencia_cruzando_por_emp_y_cod(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """El JOIN va por `(emp, cod)`: por `ide` devuelve documentos ajenos el
    99,85 % de las veces [MEDIDO]."""
    assert sentencias.buscar_idempotencia(2811179, 242534) == (
        (
            "SELECT n.ide, n.cod, r.ide, CAST(d.ima AS varbinary(max)) FROM dbo.rcg r "
            "JOIN dbo.gra n ON n.ide = r.gra "
            "JOIN [ruesma_rep].dbo.gra d ON d.emp = n.emp AND d.cod = n.cod "
            "WHERE r.con = ? AND DATALENGTH(d.ima) = ?"
        ),
        [2811179, 242534],
    )


def test_f004_r18_l6_lista_las_huerfanas_del_concepto(
    sentencias: ConceptoGraficoStatements,
) -> None:
    assert sentencias.buscar_huerfanas(2811179) == (
        (
            "SELECT n.ide, n.cod FROM dbo.rcg r "
            "JOIN dbo.gra n ON n.ide = r.gra "
            "LEFT JOIN [ruesma_rep].dbo.gra d ON d.emp = n.emp AND d.cod = n.cod "
            "WHERE r.con = ? AND d.ide IS NULL"
        ),
        [2811179],
    )


# --- R12: la reserva de los tres ide ----------------------------------------


def test_f004_r12_la_reserva_bloquea_el_rango_en_las_tres_tablas(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """UPDLOCK+HOLDLOCK ademas del applock: Sigrid escribe ~200 gra al dia sin
    pasar por nuestro bloqueo de aplicacion."""
    assert sentencias.reservar_ide_documental() == (
        (
            "SELECT ISNULL(MAX(g.ide), 0) + 1 FROM [ruesma_rep].dbo.gra g "
            "WITH (UPDLOCK, HOLDLOCK)"
        ),
        [],
    )
    assert sentencias.reservar_ide_negocio() == (
        "SELECT ISNULL(MAX(g.ide), 0) + 1 FROM dbo.gra g WITH (UPDLOCK, HOLDLOCK)",
        [],
    )
    assert sentencias.reservar_ide_enlace() == (
        "SELECT ISNULL(MAX(r.ide), 0) + 1 FROM dbo.rcg r WITH (UPDLOCK, HOLDLOCK)",
        [],
    )


# --- R11: las 29 columnas, explicitas y completas ---------------------------


def test_f004_r11_e4_inserta_las_29_columnas_en_la_documental(
    sentencias: ConceptoGraficoStatements,
) -> None:
    _cod, documental, _negocio = filas(sentencias)
    sql, params = sentencias.insertar_documental(documental)
    assert sql == (
        "INSERT INTO [ruesma_rep].dbo.gra (" + ", ".join(_GRA_29) + ") "
        "VALUES (" + ", ".join(["?"] * 29) + ")"
    )
    assert len(params) == 29


def test_f004_r11_e5_inserta_las_29_columnas_en_negocio(
    sentencias: ConceptoGraficoStatements,
) -> None:
    _cod, _documental, negocio = filas(sentencias)
    sql, params = sentencias.insertar_negocio(negocio)
    assert sql == (
        "INSERT INTO dbo.gra (" + ", ".join(_GRA_29) + ") "
        "VALUES (" + ", ".join(["?"] * 29) + ")"
    )
    assert len(params) == 29


def test_f004_r11_e6_inserta_las_7_columnas_del_enlace(
    sentencias: ConceptoGraficoStatements,
) -> None:
    enlace = sentencias.construir_fila_enlace(ide=296661, con=2811179, gra=296221, pos=64)
    sql, params = sentencias.insertar_enlace(enlace)
    assert sql == (
        "INSERT INTO dbo.rcg (" + ", ".join(_RCG_7) + ") VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    assert params == [296661, 2811179, 296221, 64, 0, 0, 0]


def test_f004_r11_la_fila_documental_lleva_las_constantes_medidas(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """3.679 de 3.679 parejas: en la documental `gratipide=0` y `res=''`,
    aunque en negocio sean 35 y «PARTE FIRMADO»."""
    _cod, documental, _negocio = filas(sentencias)
    assert tuple(documental) == _GRA_29
    assert documental["res"] == ""
    assert documental["gratipide"] == 0
    assert documental["vin"] == 3
    assert documental["ima"] == b"%PDF-1.4 binario"
    assert documental["nom"] == documental["nomori"] == "RS26.08 - 0123 PARTE FIRMADO.pdf"
    assert documental["fec"] == 20260905
    assert documental["usu"] == "aechevarria"
    for columna in ("tex", "cam", "pul"):
        assert documental[columna] is None
    for columna in ("cla", "guid", "texrev", "salusu", "saltex"):
        assert documental[columna] == ""
    for columna in ("estcon", "tipocu", "numrev", "salfec", "salhor", "mntide",
                    "graant", "anx", "ori", "tip"):
        assert documental[columna] == 0


def test_f004_r11_la_fila_de_negocio_lleva_lo_de_la_peticion_y_el_binario_no(
    sentencias: ConceptoGraficoStatements,
) -> None:
    _cod, _documental, negocio = filas(sentencias)
    assert tuple(negocio) == _GRA_29
    assert negocio["res"] == "PARTE FIRMADO"
    assert negocio["gratipide"] == 35
    assert negocio["vin"] == 3
    assert negocio["ima"] is None


def test_f004_r11_las_dos_filas_comparten_el_mismo_objeto_cod_y_emp(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """No dos cadenas iguales: el MISMO objeto. Si `cod` o `emp` difieren en un
    caracter, el motor no avisa y el grafico queda sin fichero (asi son los 517
    huerfanos `vin=3` de 2021)."""
    cod, documental, negocio = filas(sentencias)
    assert documental["cod"] is negocio["cod"] is cod
    assert documental["emp"] is negocio["emp"]
    for columna in ("usu", "fec", "nom", "nomori", "vin"):
        assert documental[columna] == negocio[columna]


def test_f004_r11_las_filas_no_comparten_el_diccionario(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """Cada `ide` es el de su tabla: los de las dos `gra` no coinciden ni se
    intenta que coincidan [MEDIDO: solo 426 filas de 2009]."""
    _cod, documental, negocio = filas(sentencias)
    documental["ide"] = 357208
    negocio["ide"] = 296221
    assert documental["ide"] != negocio["ide"]


def test_f004_r11_los_ide_nacen_vacios_hasta_que_se_reservan(
    sentencias: ConceptoGraficoStatements,
) -> None:
    _cod, documental, negocio = filas(sentencias)
    assert documental["ide"] is None
    assert negocio["ide"] is None


def test_f004_r11_los_parametros_van_en_el_orden_de_las_columnas(
    sentencias: ConceptoGraficoStatements,
) -> None:
    _cod, documental, _negocio = filas(sentencias)
    documental["ide"] = 357208
    _sql, params = sentencias.insertar_documental(documental)
    assert params == [documental[columna] for columna in _GRA_29]


# --- R13: el cod, generado una sola vez -------------------------------------


def test_f004_r13_el_cod_conserva_el_formato_medido_de_sigrid() -> None:
    """`AAAAMMDDHHMMSS` + 4 digitos + `.` + login: 3.680 de 3.680 en la clase 35."""
    cod = construir_cod(ahora=_AHORA, sha256=_SHA, usu="aechevarria")
    assert cod == "202609051230451101.aechevarria"
    assert re.fullmatch(r"\d{18}\.aechevarria", cod)


def test_f004_r13_los_cuatro_digitos_salen_del_sha256_sin_azar() -> None:
    """Reproducible en tests y en el reintento: el `cod` se genera UNA vez."""
    assert construir_cod(ahora=_AHORA, sha256="0" * 64, usu="x").endswith("0000.x")
    assert construir_cod(ahora=_AHORA, sha256="ffffffff" + "0" * 56, usu="x").endswith(
        f"{0xFFFFFFFF % 10000:04d}.x"
    )


def test_f004_r13_el_cod_de_las_filas_es_el_que_devuelve_el_constructor(
    sentencias: ConceptoGraficoStatements,
) -> None:
    cod, documental, negocio = filas(sentencias)
    assert cod == construir_cod(ahora=_AHORA, sha256=_SHA, usu="aechevarria")
    assert documental["cod"] == negocio["cod"] == cod


@pytest.mark.parametrize(
    "instante_utc, esperado",
    [
        (datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc), local(2026, 1, 15, 13, 0)),
        (datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc), local(2026, 7, 15, 14, 0)),
        # Ultimo domingo de marzo de 2026: el 29, a la 01:00 UTC.
        (datetime(2026, 3, 29, 0, 59, tzinfo=timezone.utc), local(2026, 3, 29, 1, 59)),
        (datetime(2026, 3, 29, 1, 0, tzinfo=timezone.utc), local(2026, 3, 29, 3, 0)),
        # Ultimo domingo de octubre de 2026: el 25, a la 01:00 UTC.
        (datetime(2026, 10, 25, 0, 59, tzinfo=timezone.utc), local(2026, 10, 25, 2, 59)),
        (datetime(2026, 10, 25, 1, 0, tzinfo=timezone.utc), local(2026, 10, 25, 2, 0)),
        (datetime(2027, 12, 31, 23, 30, tzinfo=timezone.utc), local(2028, 1, 1, 0, 30)),
    ],
)
def test_f004_r13_el_sello_va_en_hora_de_madrid(
    instante_utc: datetime, esperado: datetime
) -> None:
    """Los workers de Azure corren en UTC y Sigrid sella en hora local."""
    assert hora_local_de_madrid(instante_utc) == esperado


def test_f004_r13_un_instante_sin_zona_se_entiende_como_utc() -> None:
    assert hora_local_de_madrid(local(2026, 1, 15, 12, 0)) == local(2026, 1, 15, 13, 0)


# --- R14: la relectura previa al COMMIT -------------------------------------


def test_f004_r14_la_relectura_cruza_por_emp_y_cod_nunca_por_ide(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """`SET NOCOUNT ON` deja `cursor.rowcount` en -1: la unica prueba de que la
    fila esta es volver a leerla."""
    cod = "202609051230451101.aechevarria"
    assert sentencias.releer_documental(1, cod) == (
        "SELECT COUNT(*) FROM [ruesma_rep].dbo.gra WHERE emp = ? AND cod = ?",
        [1, cod],
    )
    assert sentencias.releer_negocio(1, cod) == (
        "SELECT COUNT(*) FROM dbo.gra WHERE emp = ? AND cod = ?",
        [1, cod],
    )
    assert sentencias.releer_enlace(296661) == (
        "SELECT COUNT(*) FROM dbo.rcg WHERE ide = ?",
        [296661],
    )


# --- R16: la unicidad la da el indice, no un COUNT previo -------------------


def test_f004_r16_ninguna_sentencia_cuenta_por_cod_antes_de_insertar(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """Un `COUNT(*) ... WHERE cod = ?` previo seria una comprobacion con
    carrera: la unicidad la impone el indice unico `(emp, cod)`."""
    antes_del_insert = [
        sentencias.leer_concepto(1)[0],
        sentencias.leer_clase(1)[0],
        sentencias.leer_usuario("x")[0],
        sentencias.siguiente_pos(1)[0],
        sentencias.buscar_idempotencia(1, 1)[0],
        sentencias.buscar_huerfanas(1)[0],
        sentencias.reservar_ide_documental()[0],
        sentencias.reservar_ide_negocio()[0],
        sentencias.reservar_ide_enlace()[0],
    ]
    for sql in antes_del_insert:
        assert not ("COUNT(*)" in sql and "cod = ?" in sql), sql
    # La busqueda de idempotencia filtra por CONTENIDO (tamano del binario),
    # no por el `cod` que se acaba de generar.
    idempotencia = sentencias.buscar_idempotencia(1, 1)[0]
    assert "DATALENGTH(d.ima) = ?" in idempotencia
    assert "d.cod = ?" not in idempotencia


# --- R20: control negativo de verbos ----------------------------------------


def test_f004_r20_ninguna_sentencia_modifica_ni_borra_nada(
    sentencias: ConceptoGraficoStatements,
) -> None:
    prohibidos = re.compile(
        r"\b(UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|GRANT|USE)\b",
        re.IGNORECASE,
    )
    todas = sentencias.todas_las_sentencias()
    assert len(todas) == 15
    for sql in todas:
        assert not prohibidos.search(sql), sql
        assert sql.startswith(("SELECT", "INSERT INTO"))
        assert ";" not in sql


# --- R19: el guardia de bases cruzadas sigue mandando -----------------------


def test_f004_r19_solo_la_documental_se_nombra_y_solo_dbo_gra(
    sentencias: ConceptoGraficoStatements,
) -> None:
    for sql in sentencias.todas_las_sentencias():
        referencias = DatabaseReferenceGuard.extract_database_references(sql)
        assert referencias in ([], [_DOCUMENTAL]), sql
        if referencias:
            assert f"[{_DOCUMENTAL}].dbo.gra" in sql


def test_f004_r19_cada_sentencia_pasa_el_guardia_con_las_dos_bases(
    sentencias: ConceptoGraficoStatements,
) -> None:
    for sql in sentencias.todas_las_sentencias():
        DatabaseReferenceGuard.validate(
            sql, allowed=[_NEGOCIO, _DOCUMENTAL], contexto="escritura"
        )


def test_f004_r19_el_guardia_sigue_cerrando_la_documental_a_sql_write(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """Las sentencias que nombran la documental serian RECHAZADAS por
    `sql/write`, cuya lista sigue siendo solo `ruesma` (R5)."""
    cruzadas = [
        sql
        for sql in sentencias.todas_las_sentencias()
        if DatabaseReferenceGuard.extract_database_references(sql)
    ]
    assert len(cruzadas) == 5  # L5, L6, E1, E4 y la relectura documental de E7
    for sql in cruzadas:
        with pytest.raises(DatabaseReferenceError):
            DatabaseReferenceGuard.validate(sql, allowed=[_NEGOCIO], contexto="escritura")


def test_f004_r19_el_constructor_valida_cada_sentencia_al_construirse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """R19 exige validar ANTES de abrir conexion. Se comprueba con un espia:
    las 15 sentencias pasan por el guardia, con las dos bases y ninguna mas."""
    llamadas: list[tuple[str, tuple[str, ...], str]] = []
    original = DatabaseReferenceGuard.validate

    def espia(sql: str, *, allowed: list[str], contexto: str) -> None:
        llamadas.append((sql, tuple(allowed), contexto))
        original(sql, allowed=allowed, contexto=contexto)

    monkeypatch.setattr(DatabaseReferenceGuard, "validate", staticmethod(espia))
    construidas = ConceptoGraficoStatements(database=_NEGOCIO, documental=_DOCUMENTAL)

    assert [llamada[0] for llamada in llamadas] == list(construidas.todas_las_sentencias())
    assert {llamada[1] for llamada in llamadas} == {(_NEGOCIO, _DOCUMENTAL)}
    assert {llamada[2] for llamada in llamadas} == {"escritura"}


# --- R18: la documental pasa por IdentifierGuard ----------------------------


@pytest.mark.parametrize(
    "documental",
    ["ruesma_rep]; DROP TABLE gra --", "ruesma rep", "", "1base", "ruesma-rep", "[ruesma_rep]"],
)
def test_f004_r18_una_base_documental_con_caracteres_raros_se_rechaza(documental: str) -> None:
    with pytest.raises(IdentifierValidationError):
        ConceptoGraficoStatements(database=_NEGOCIO, documental=documental)


def test_f004_r18_el_unico_identificador_no_literal_es_la_base_documental(
    sentencias: ConceptoGraficoStatements,
) -> None:
    """Nada de la peticion entra en el SQL: los valores viajan como `?`."""
    otra = ConceptoGraficoStatements(database="otra_base", documental="otro_repositorio")
    for sql in otra.todas_las_sentencias():
        assert "otra_base" not in sql
        assert sql.count("[") == sql.count("]") <= 1
