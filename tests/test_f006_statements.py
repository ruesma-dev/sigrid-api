# tests/test_f006_statements.py
"""
F-006 · R11, R12, R16 y R18: el constructor PURO de sentencias y filas.

Sin red y sin base de datos. El SQL se compara carácter a carácter: cambiar
una coma es cambiar el contrato con el ERP y tiene que verse en el diff de
este fichero. Las constantes de las cinco filas salen de `design.md` §Filas
(medidas en `progress/explore_F-006_modelo_parte.md`); los nombres y el orden
de columnas se confirmaron con `INFORMATION_SCHEMA.COLUMNS` el 2026-09-24.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from application.use_cases.parte_reclamacion_statements import (
    CON_COLUMNAS,
    CONEXT_COLUMNAS,
    LOG_COLUMNAS,
    PLANTILLA_SERIE,
    RCP_COLUMNAS,
    RCPINT_COLUMNAS,
    ParteReclamacionStatements,
    fecha_ole_utc,
    patron_de_cod,
    prefijo_de_serie,
    sellos,
    siguiente_cod,
)
from domain.models.parte_reclamacion_models import ParteReclamacionError
from infrastructure.security.database_reference_guard import (
    DatabaseReferenceError,
    DatabaseReferenceGuard,
)


@pytest.fixture
def sentencias() -> ParteReclamacionStatements:
    return ParteReclamacionStatements(database="ruesma")


# --- Lecturas comunes del lote (L1-L7) --------------------------------------


def test_f006_r6_l1_serie(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_serie() == (
        "SELECT ide, emp, tam, estini FROM dbo.sercon WHERE tip = ? AND cod = ? AND act = 1",
        [708, "RS<año2>.<mes>/"],
    )
    assert PLANTILLA_SERIE == "RS<año2>.<mes>/"


def test_f006_r6_l2_estado_inicial(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_estado_inicial(1) == (
        "SELECT est, cod FROM dbo.conest WHERE tip = ? AND est = ?",
        [708, 1],
    )


def test_f006_r6_l3_obra_con_su_emp(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_obra(1, "0626") == (
        "SELECT ide, emp, cod FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?",
        [1, 42, "0626"],
    )


def test_f006_r6_l4_usuario(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_usuario("prueba") == (
        "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?",
        ["prueba"],
    )


def test_f006_r6_l5_unidades_postventa(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_unidades_postventa(1758465, 1) == (
        (
            "SELECT c.ide, c.cod, ISNULL(u.cliide, 0), ISNULL(u.peride, 0) FROM dbo.upv u "
            "JOIN dbo.con c ON c.ide = u.ide WHERE u.obride = ? AND c.emp = ? AND c.tip = ?"
        ),
        [1758465, 1, 707],
    )


def test_f006_r6_l6_oficios_de_la_obra(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_oficios_de_la_obra(1758465) == (
        (
            "SELECT o.ide, o.pos, a.cod, p.cod FROM dbo.obrofc o "
            "LEFT JOIN dbo.auxofc a ON a.ide = o.ofcide "
            "LEFT JOIN dbo.con p ON p.ide = o.prvide WHERE o.obride = ?"
        ),
        [1758465],
    )


def test_f006_r6_l7_catalogos(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.leer_tipos() == ("SELECT ide, cod, fecbaj FROM dbo.auxtrcp", [])
    assert sentencias.leer_clases() == ("SELECT ide, cod, fecbaj FROM dbo.auxrcp", [])
    assert sentencias.leer_oficios() == ("SELECT ide, cod, fecbaj FROM dbo.auxofc", [])


# --- Por parte (L8-L10) ------------------------------------------------------


def test_f006_r15_l8_idempotencia_por_referencia(
    sentencias: ParteReclamacionStatements,
) -> None:
    assert sentencias.buscar_referencia("PVI-1", 1) == (
        (
            "SELECT c.ide, c.cod, r.upvide FROM dbo.conext x "
            "JOIN dbo.con c ON c.ide = x.conide LEFT JOIN dbo.rcp r ON r.ide = c.ide "
            "WHERE x.cod = ? AND x.valt = ? AND c.tip = ? AND c.emp = ?"
        ),
        ["RCPCLI", "PVI-1", 708, 1],
    )


def test_f006_r9_l9_ultimo_cod_del_mes_sin_bloqueo(
    sentencias: ParteReclamacionStatements,
) -> None:
    assert sentencias.ultimo_cod(1, "RS26.09/") == (
        "SELECT MAX(cod) FROM dbo.con WHERE emp = ? AND tip = ? AND cod LIKE ?",
        [1, 708, "RS26.09/[0-9][0-9][0-9][0-9]"],
    )


def test_f006_r9_l10_siguiente_pos_sin_bloqueo(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.siguiente_pos_sin_bloqueo() == (
        "SELECT ISNULL(MAX(pos), 0) + 64 FROM dbo.rcp",
        [],
    )


# --- Dentro de la transacción (E2-E8, E14) ----------------------------------


def test_f006_r12_e2_cod_bajo_bloqueo(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.reservar_cod(1, "RS26.09/") == (
        (
            "SELECT MAX(cod) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) "
            "WHERE emp = ? AND tip = ? AND cod LIKE ?"
        ),
        [1, 708, "RS26.09/[0-9][0-9][0-9][0-9]"],
    )


def test_f006_r12_e3_a_e7_ide_y_pos_bajo_bloqueo(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.reservar_ide_con() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.con WITH (UPDLOCK, HOLDLOCK)", []
    )
    assert sentencias.reservar_pos_rcp() == (
        "SELECT ISNULL(MAX(pos), 0) + 64 FROM dbo.rcp WITH (UPDLOCK, HOLDLOCK)", []
    )
    assert sentencias.reservar_ide_rcpint() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.rcpint WITH (UPDLOCK, HOLDLOCK)", []
    )
    assert sentencias.reservar_ide_conext() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.conext WITH (UPDLOCK, HOLDLOCK)", []
    )
    assert sentencias.reservar_ide_log() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.log WITH (UPDLOCK, HOLDLOCK)", []
    )


def test_f006_r14_e8_revalidacion(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.revalidar_unidad_postventa(2751478, 1758465) == (
        "SELECT COUNT(*) FROM dbo.upv WHERE ide = ? AND obride = ?",
        [2751478, 1758465],
    )
    assert sentencias.revalidar_oficio_de_obra(2173, 1758465) == (
        "SELECT COUNT(*) FROM dbo.obrofc WHERE ide = ? AND obride = ?",
        [2173, 1758465],
    )


def test_f006_r14_e14_relecturas_por_clave(sentencias: ParteReclamacionStatements) -> None:
    assert sentencias.releer_con(1, "RS26.09/0001") == (
        "SELECT COUNT(*) FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?",
        [1, 708, "RS26.09/0001"],
    )
    assert sentencias.releer_rcp(2900001) == ("SELECT COUNT(*) FROM dbo.rcp WHERE ide = ?", [2900001])
    assert sentencias.releer_rcpint(2900001) == (
        "SELECT COUNT(*) FROM dbo.rcpint WHERE rcpide = ?", [2900001]
    )
    assert sentencias.releer_conext(2900001) == (
        "SELECT COUNT(*) FROM dbo.conext WHERE conide = ? AND cod = ?",
        [2900001, "RCPCLI"],
    )
    assert sentencias.releer_log(8500000) == ("SELECT COUNT(*) FROM dbo.log WHERE ide = ?", [8500000])


# --- E9-E13: las cinco filas, completas --------------------------------------


def test_f006_r11_columnas_de_las_cinco_tablas() -> None:
    assert CON_COLUMNAS == (
        "ide", "emp", "tip", "subtip", "cod", "res", "fec", "tex", "cee", "est",
        "fecbaj", "tiemod", "ico", "delo", "del", "obr", "doc", "serie", "hor",
    )
    assert RCP_COLUMNAS == (
        "ide", "upvide", "pos", "fec", "hor", "cliide", "recide", "cntide", "tel", "ele",
        "tex", "rcpide", "motrcp", "rcptip", "fecpre", "solrcp", "trcpide", "resubi",
        "texurg", "ofcide",
    )
    assert RCPINT_COLUMNAS == ("ide", "rcpide", "pos", "obrofcide", "cauave")
    assert CONEXT_COLUMNAS == (
        "ide", "conide", "cod", "camtip", "camtab", "valt", "valn", "valf", "vali",
        "valm", "valb",
    )
    assert LOG_COLUMNAS == (
        "ide", "emp", "ori", "ope", "fec", "hor", "usu", "tab", "tip", "cod", "res",
        "tex", "est", "err",
    )
    assert [len(c) for c in (CON_COLUMNAS, RCP_COLUMNAS, RCPINT_COLUMNAS,
                             CONEXT_COLUMNAS, LOG_COLUMNAS)] == [19, 20, 5, 11, 14]


def _filas(sentencias: ParteReclamacionStatements, **cambios: object) -> dict:
    datos: dict[str, object] = {
        "emp": 1,
        "est": 1,
        "descripcion": "Fisura en tabique",
        "descripcion_larga": None,
        "fec": 20260924,
        "hor": 221530,
        "tiemod": 46289.847,
        "upvide": 2751478,
        "cliide": 2811575,
        "recide": 2811576,
        "clase_ide": 0,
        "rcptip": 1,
        "trcpide": 2,
        "resubi": "Cocina",
        "ofcide": 39,
        "intervinientes": [(2173, False), (2268, True)],
        "referencia": "PVI-1",
        "usu": "prueba",
    }
    datos.update(cambios)
    return sentencias.construir_filas(**datos)


def _numeradas(sentencias: ParteReclamacionStatements, **cambios: object) -> dict:
    return sentencias.numerar(
        _filas(sentencias, **cambios),
        cod="RS26.09/0007",
        ide_con=2900001,
        pos_rcp=1408064,
        ide_rcpint=25405,
        ide_conext=56286,
        ide_log=8488889,
    )


def test_f006_r11_fila_con(sentencias: ParteReclamacionStatements) -> None:
    assert _numeradas(sentencias)["con"] == {
        "ide": 2900001, "emp": 1, "tip": 708, "subtip": 0, "cod": "RS26.09/0007",
        "res": "Fisura en tabique", "fec": 20260924, "tex": None, "cee": 0, "est": 1,
        "fecbaj": 0, "tiemod": 46289.847, "ico": "", "delo": "", "del": "", "obr": "",
        "doc": "", "serie": 0, "hor": 0,
    }


def test_f006_r11_fila_rcp(sentencias: ParteReclamacionStatements) -> None:
    assert _numeradas(sentencias)["rcp"] == {
        "ide": 2900001, "upvide": 2751478, "pos": 1408064, "fec": 20260924, "hor": 221530,
        "cliide": 2811575, "recide": 2811576, "cntide": 0, "tel": None, "ele": None,
        "tex": "Fisura en tabique", "rcpide": 0, "motrcp": "", "rcptip": 1, "fecpre": 0,
        "solrcp": None, "trcpide": 2, "resubi": "Cocina", "texurg": "", "ofcide": 39,
    }


def test_f006_r11_la_descripcion_larga_va_a_rcp_tex(sentencias: ParteReclamacionStatements) -> None:
    filas = _numeradas(sentencias, descripcion_larga="Largo", clase_ide=3)
    assert filas["rcp"]["tex"] == "Largo"
    assert filas["rcp"]["rcpide"] == 3
    assert filas["con"]["res"] == "Fisura en tabique"


def test_f006_r11_filas_rcpint_consecutivas(sentencias: ParteReclamacionStatements) -> None:
    assert _numeradas(sentencias)["rcpint"] == [
        {"ide": 25405, "rcpide": 2900001, "pos": 0, "obrofcide": 2173, "cauave": 0},
        {"ide": 25406, "rcpide": 2900001, "pos": 0, "obrofcide": 2268, "cauave": 1},
    ]
    assert _numeradas(sentencias, intervinientes=[])["rcpint"] == []


def test_f006_r11_fila_conext(sentencias: ParteReclamacionStatements) -> None:
    assert _numeradas(sentencias)["conext"] == {
        "ide": 56286, "conide": 2900001, "cod": "RCPCLI", "camtip": 0, "camtab": "",
        "valt": "PVI-1", "valn": 0, "valf": 0, "vali": 0, "valm": None, "valb": None,
    }


def test_f006_r11_fila_log(sentencias: ParteReclamacionStatements) -> None:
    assert _numeradas(sentencias)["log"] == {
        "ide": 8488889, "emp": 1, "ori": 0, "ope": 1, "fec": 20260924, "hor": 221530,
        "usu": "prueba", "tab": "con", "tip": 708, "cod": "RS26.09/0007",
        "res": "Fisura en tabique", "tex": None, "est": 1, "err": None,
    }


def test_f006_r11_las_filas_derivadas_comparten_con_ide_y_datos(
    sentencias: ParteReclamacionStatements,
) -> None:
    filas = _numeradas(sentencias, emp=28, est=3)
    con = filas["con"]
    assert filas["rcp"]["ide"] == con["ide"]
    assert all(fila["rcpide"] == con["ide"] for fila in filas["rcpint"])
    assert filas["conext"]["conide"] == con["ide"]
    for campo in ("cod", "res", "est", "fec", "emp"):
        assert filas["log"][campo] == con[campo], campo
    assert filas["log"]["hor"] == filas["rcp"]["hor"]
    assert filas["rcp"]["fec"] == con["fec"]


def test_f006_r11_sin_numerar_las_filas_nacen_sin_ide_cod_ni_pos(
    sentencias: ParteReclamacionStatements,
) -> None:
    filas = _filas(sentencias)
    assert filas["con"]["ide"] is None and filas["con"]["cod"] is None
    assert filas["rcp"]["ide"] is None and filas["rcp"]["pos"] is None
    assert all(f["ide"] is None and f["rcpide"] is None for f in filas["rcpint"])
    assert filas["conext"]["ide"] is None and filas["conext"]["conide"] is None
    assert filas["log"]["ide"] is None and filas["log"]["cod"] is None


def test_f006_r13_numerar_no_toca_las_filas_de_partida(
    sentencias: ParteReclamacionStatements,
) -> None:
    """Reentrante: cada reintento numera sobre las filas limpias."""
    filas = _filas(sentencias)
    sentencias.numerar(
        filas, cod="RS26.09/0001", ide_con=1, pos_rcp=64, ide_rcpint=1, ide_conext=1, ide_log=1
    )
    assert filas["con"]["ide"] is None
    assert filas["rcpint"][0]["ide"] is None
    assert filas["log"]["cod"] is None


def test_f006_r11_insert_de_cada_tabla(sentencias: ParteReclamacionStatements) -> None:
    filas = _numeradas(sentencias)
    for metodo, tabla, columnas, fila in (
        (sentencias.insertar_con, "con", CON_COLUMNAS, filas["con"]),
        (sentencias.insertar_rcp, "rcp", RCP_COLUMNAS, filas["rcp"]),
        (sentencias.insertar_rcpint, "rcpint", RCPINT_COLUMNAS, filas["rcpint"][0]),
        (sentencias.insertar_conext, "conext", CONEXT_COLUMNAS, filas["conext"]),
        (sentencias.insertar_log, "log", LOG_COLUMNAS, filas["log"]),
    ):
        sql, params = metodo(fila)
        assert sql == (
            f"INSERT INTO dbo.{tabla} ({', '.join(columnas)}) "
            f"VALUES ({', '.join(['?'] * len(columnas))})"
        )
        assert params == [fila[c] for c in columnas]


def test_f006_r11_insert_con_literal(sentencias: ParteReclamacionStatements) -> None:
    sql, _ = sentencias.insertar_con(_numeradas(sentencias)["con"])
    assert sql == (
        "INSERT INTO dbo.con (ide, emp, tip, subtip, cod, res, fec, tex, cee, est, fecbaj, "
        "tiemod, ico, delo, del, obr, doc, serie, hor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
        "?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )


# --- R12: numeración de la serie ---------------------------------------------


@pytest.mark.parametrize(
    "max_cod, esperado",
    [
        (None, "RS26.09/0001"),
        ("RS26.09/0771", "RS26.09/0772"),
        ("RS26.09/0009", "RS26.09/0010"),
        ("RS26.09/9998", "RS26.09/9999"),
    ],
)
def test_f006_r12_siguiente_cod(max_cod: str | None, esperado: str) -> None:
    assert siguiente_cod("RS26.09/", max_cod, 4) == esperado


def test_f006_r12_pasado_9999_la_numeracion_se_agota() -> None:
    with pytest.raises(ParteReclamacionError) as excinfo:
        siguiente_cod("RS26.09/", "RS26.09/9999", 4)
    assert excinfo.value.codigo == "numeracion_agotada"


def test_f006_r12_el_patron_like_exige_tam_digitos() -> None:
    assert patron_de_cod("RS26.09/", 4) == "RS26.09/[0-9][0-9][0-9][0-9]"
    assert patron_de_cod("RS26.09/", 2) == "RS26.09/[0-9][0-9]"


@pytest.mark.parametrize(
    "momento, esperado",
    [
        # Hora LOCAL de Madrid, sin zona: es lo que recibe prefijo_de_serie.
        (datetime(2026, 9, 24, 22, 15), "RS26.09/"),  # noqa: DTZ001
        (datetime(2027, 1, 1, 0, 0), "RS27.01/"),  # noqa: DTZ001
        (datetime(2026, 12, 31, 23, 59), "RS26.12/"),  # noqa: DTZ001
    ],
)
def test_f006_r12_prefijo_del_mes(momento: datetime, esperado: str) -> None:
    assert prefijo_de_serie(momento) == esperado


# --- R16: sellos de tiempo ---------------------------------------------------


def test_f006_r16_fecha_ole_en_utc_verano() -> None:
    """El 2811304 medido: 2026-08-04 08:41:29 UTC -> 46238.362141 (rcp.hor 104129)."""
    instante = datetime(2026, 8, 4, 8, 41, 29, tzinfo=timezone.utc)
    assert fecha_ole_utc(instante) == pytest.approx(46238.362141, abs=1e-6)
    madrid = instante.astimezone(ZoneInfo("Europe/Madrid"))
    assert fecha_ole_utc(madrid) == pytest.approx(46238.362141, abs=1e-6)
    assert fecha_ole_utc(instante.replace(tzinfo=None)) == pytest.approx(46238.362141, abs=1e-6)


def test_f006_r16_fecha_ole_en_utc_invierno() -> None:
    instante = datetime(2026, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    assert fecha_ole_utc(instante) == 46037.5
    assert fecha_ole_utc(datetime(1899, 12, 30, tzinfo=timezone.utc)) == 0.0


def test_f006_r16_sellos_verano() -> None:
    s = sellos(datetime(2026, 8, 4, 8, 41, 29, tzinfo=timezone.utc))
    assert (s.fec, s.hor, s.prefijo) == (20260804, 104129, "RS26.08/")
    assert s.tiemod == pytest.approx(46238.362141, abs=1e-6)


def test_f006_r16_sellos_invierno_y_cambio_de_mes_en_madrid() -> None:
    """A las 23:30 UTC del 31 de enero ya es 1 de febrero en Madrid: el mes del
    código es el de `con.fec`, local (20.756 de 20.757 medidos)."""
    s = sellos(datetime(2026, 1, 31, 23, 30, 5, tzinfo=timezone.utc))
    assert (s.fec, s.hor, s.prefijo) == (20260201, 3005, "RS26.02/")
    assert s.tiemod == pytest.approx(46053.979224, abs=1e-6)


# --- R18: todo con `?`, sin verbos prohibidos, y el guardia no protesta -----


def test_f006_r18_ninguna_sentencia_modifica_ni_borra_nada(
    sentencias: ParteReclamacionStatements,
) -> None:
    prohibidos = re.compile(
        r"\b(UPDATE|DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|GRANT|USE)\b",
        re.IGNORECASE,
    )
    todas = sentencias.todas_las_sentencias()
    assert len(todas) == 30
    assert len(set(todas)) == 30
    for sql in todas:
        assert not prohibidos.search(sql), sql
        assert sql.startswith(("SELECT", "INSERT INTO")), sql
        assert ";" not in sql
        assert "'" not in sql, sql  # ningún literal de texto: todo valor va como ?


def test_f006_r18_ninguna_sentencia_toca_tar_ni_graficos(
    sentencias: ParteReclamacionStatements,
) -> None:
    """R19: no se pasa a PTE ni se crean tareas, gráficos, UPV ni oficios."""
    for sql in sentencias.todas_las_sentencias():
        for tabla in ("dbo.tar", "dbo.gra", "dbo.rcg"):
            assert tabla not in sql, sql
        if sql.startswith("INSERT"):
            assert re.match(r"INSERT INTO dbo\.(con|rcp|rcpint|conext|log) \(", sql), sql


def test_f006_r18_el_guardia_no_rechaza_ninguna(sentencias: ParteReclamacionStatements) -> None:
    for sql in sentencias.todas_las_sentencias():
        assert DatabaseReferenceGuard.extract_database_references(sql) == [], sql
        DatabaseReferenceGuard.validate(sql, allowed=["ruesma"], contexto="escritura")


def test_f006_r18_el_constructor_se_autovalida(monkeypatch: pytest.MonkeyPatch) -> None:
    """Si alguna sentencia nombrara otra base, el constructor no llega a existir."""
    llamadas: list[tuple[str, list[str]]] = []

    def espia(sql: str, *, allowed: list[str], contexto: str) -> None:
        llamadas.append((sql, allowed))
        raise DatabaseReferenceError("rechazada")

    monkeypatch.setattr(DatabaseReferenceGuard, "validate", staticmethod(espia))
    with pytest.raises(DatabaseReferenceError):
        ParteReclamacionStatements(database=" ruesma ")
    assert llamadas[0][1] == ["ruesma"]


def test_f006_r18_el_constructor_valida_todas(monkeypatch: pytest.MonkeyPatch) -> None:
    vistas: list[str] = []
    monkeypatch.setattr(
        DatabaseReferenceGuard,
        "validate",
        staticmethod(lambda sql, *, allowed, contexto: vistas.append(sql)),
    )
    sentencias = ParteReclamacionStatements(database="ruesma")
    assert vistas == list(sentencias.todas_las_sentencias())
