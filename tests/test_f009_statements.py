# tests/test_f009_statements.py
"""
F-009 · el constructor PURO del modo extendido de `sigrid/albaran`
(`application/use_cases/albaran_compra_statements.py`): sentencias (T4, R31),
funciones puras (T5) y filas (T6).

Sin red y sin base de datos. El SQL se compara carácter a carácter: cambiar una
coma es cambiar el contrato con el ERP y tiene que verse en el diff de este
fichero. Las sentencias salen de `specs/F-009-alta-albaran-compra/design.md`
§Sentencias (v8.1: sin L12b, L12c ni E7b).
"""

from __future__ import annotations

import re

import pytest

import application.use_cases.albaran_compra_statements as modulo
from application.use_cases.albaran_compra_statements import (
    APPLOCKS,
    CTRPRODES_COLUMNAS,
    LOG_COLUMNAS,
    MOV_COLUMNAS,
    AlbaranCompraStatements,
)
from infrastructure.security.database_reference_guard import (
    DatabaseReferenceError,
    DatabaseReferenceGuard,
)
from infrastructure.security.identifier_guard import IdentifierValidationError


@pytest.fixture
def sentencias() -> AlbaranCompraStatements:
    return AlbaranCompraStatements(database="ruesma")


# --- T4 · lecturas de cabecera (L1, L5, L11, L13, L14) -----------------------------


def test_f009_sql_l1_obra_por_tipo_y_codigo(
    sentencias: AlbaranCompraStatements,
) -> None:
    """Sin `emp`: se filtra por `SIGRID_ALBARAN_EMPRESAS_OBRA` en Python (H2)."""
    assert sentencias.leer_obra("0404") == (
        "SELECT ide, emp, cod FROM dbo.con WHERE tip = ? AND cod = ?",
        [42, "0404"],
    )


def test_f009_sql_l5_plantilla_de_cabecera_del_proveedor_en_la_empresa(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_plantilla_cabecera(1, 77) == (
        (
            "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
            "WHERE c.tip = ? AND c.emp = ? AND d.entide = ? ORDER BY c.ide DESC"
        ),
        [14, 1, 77],
    )


def test_f009_sql_l5_sin_contrato_por_cif(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.leer_plantilla_cabecera_por_cif(1, "B12345678") == (
        (
            "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
            "WHERE c.tip = ? AND c.emp = ? AND d.entcif = ? ORDER BY c.ide DESC"
        ),
        [14, 1, "B12345678"],
    )


def test_f009_sql_l11_idempotencia_por_synckey(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.buscar_referencia("ALB-123") == (
        (
            "SELECT c.ide, c.cod, c.fec, d.entide, d.obride, d.totbas, d.totdoc FROM dbo.dca d "
            "JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = ? AND d.synckey = ?"
        ),
        [14, "ALB-123"],
    )


def test_f009_sql_l11_lineas_del_albaran_existente_con_refent(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_lineas_de_albaran(100) == (
        (
            "SELECT pos, proide, can, pre, tot, paride, almide, refent FROM dbo.dcapro "
            "WHERE docide = ? ORDER BY pos"
        ),
        [100],
    )


def test_f009_sql_l13_estado_inicial_y_usuario(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_estado_inicial() == (
        "SELECT est FROM dbo.conest WHERE tip = ? AND est = ?",
        [14, 1],
    )
    assert sentencias.leer_usuario("prueba") == (
        "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?",
        ["prueba"],
    )


def test_f009_sql_l14_cod_provisional_sin_bloqueos(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.ultimo_cod(1, "AC26/") == (
        (
            "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con "
            "WHERE emp = ? AND tip = ? AND cod LIKE ?"
        ),
        [6, 1, 14, "AC26/%"],
    )


# --- T4 · lecturas de línea (L6-L10, L12, L15) ---------------------------------------


def test_f009_sql_l6_partidas_de_la_obra(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.leer_partidas(5000, ["01.02", "03"]) == (
        "SELECT ide, cod, tip, tipdes, tipvis FROM dbo.obrparpar WHERE obride = ? AND cod IN (?, ?)",
        [5000, "01.02", "03"],
    )


def test_f009_sql_l7_productos_sin_natide(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.leer_productos(1, ["MA9999"]) == (
        (
            "SELECT c.ide, c.cod, c.fecbaj, p.tipmov FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide "
            "WHERE c.emp = ? AND c.tip = ? AND c.cod IN (?)"
        ),
        [1, 3, "MA9999"],
    )


def test_f009_sql_l7b_tipmov_de_los_productos_de_los_ctrpro(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_tipmov([55, 56, 57]) == (
        "SELECT ide, tipmov FROM dbo.pro WHERE ide IN (?, ?, ?)",
        [55, 56, 57],
    )


def test_f009_sql_l8_y_l8b_plantillas_de_linea(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_plantilla_linea(55) == (
        "SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC",
        [55],
    )
    assert sentencias.leer_plantilla_linea_del_proveedor(55, 77) == (
        (
            "SELECT TOP 1 p.* FROM dbo.dcapro p JOIN dbo.dca d ON d.ide = p.docide "
            "WHERE p.proide = ? AND d.entide = ? ORDER BY p.ide DESC"
        ),
        [55, 77],
    )


def test_f009_sql_l9_tasas_de_iva(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.leer_tasas_iva([3, 4]) == (
        "SELECT ide, iva FROM dbo.iva WHERE ide IN (?, ?)",
        [3, 4],
    )


def test_f009_sql_l10_almacen_de_la_obra(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.leer_almacen_de_obra(5000) == (
        "SELECT almide, cenide FROM dbo.obr WHERE ide = ?",
        [5000],
    )
    assert sentencias.leer_almacenes(5000, [7, 8]) == (
        "SELECT ide, obride, cenide FROM dbo.alm WHERE obride = ? OR ide IN (?, ?)",
        [5000, 7, 8],
    )


def test_f009_sql_l10_sin_almacenes_resueltos_solo_los_de_la_obra(
    sentencias: AlbaranCompraStatements,
) -> None:
    """`ide IN ()` no es SQL: sin almacenes resueltos queda la primera mitad."""
    assert sentencias.leer_almacenes(5000, []) == (
        "SELECT ide, obride, cenide FROM dbo.alm WHERE obride = ?",
        [5000],
    )


def test_f009_sql_l12_balance_del_producto_en_el_almacen(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_balance(55, 7) == (
        (
            "SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? "
            "ORDER BY fechor DESC, ide DESC"
        ),
        [55, 7],
    )


def test_f009_sql_l15_naturaleza_analitica_y_cuenta(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.leer_naturalezas(["MA99", "QA99"]) == (
        (
            "SELECT ide, cod, numemp, fecbaj, caagascod, cuacomcod FROM dbo.auxpronat "
            "WHERE cod IN (?, ?)"
        ),
        ["MA99", "QA99"],
    )
    assert sentencias.leer_analiticas(["0404.CDSB37"]) == (
        (
            "SELECT c.ide, c.cod, a.cenide FROM dbo.con c JOIN dbo.caa a ON a.ide = c.ide "
            "WHERE c.cod IN (?)"
        ),
        ["0404.CDSB37"],
    )
    assert sentencias.leer_cuentas(1, ["60000001", "60000002"]) == (
        (
            "SELECT c.ide, c.cod FROM dbo.con c JOIN dbo.cua a ON a.ide = c.ide "
            "WHERE c.emp = ? AND c.cod IN (?, ?)"
        ),
        [1, "60000001", "60000002"],
    )


@pytest.mark.parametrize(
    "llamada",
    [
        lambda s: s.leer_partidas(1, []),
        lambda s: s.leer_productos(1, []),
        lambda s: s.leer_tipmov([]),
        lambda s: s.leer_tasas_iva([]),
        lambda s: s.leer_naturalezas([]),
        lambda s: s.leer_analiticas([]),
        lambda s: s.leer_cuentas(1, []),
    ],
)
def test_f009_sql_una_lista_vacia_no_genera_sql(
    llamada, sentencias: AlbaranCompraStatements
) -> None:
    with pytest.raises(ValueError, match="vacia"):
        llamada(sentencias)


def test_f009_sql_las_listas_no_se_copian_por_referencia(
    sentencias: AlbaranCompraStatements,
) -> None:
    codigos = ["01"]
    _sql, params = sentencias.leer_partidas(5000, codigos)
    codigos.append("02")
    assert params == [5000, "01"]


# --- T4 · dentro de la transacción (E1-E12) -----------------------------------------


def test_f009_sql_e1_es_l11(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.buscar_referencia("X")[0] in sentencias.todas_las_sentencias()


def test_f009_r26_sql_e2_cod_bajo_bloqueo(sentencias: AlbaranCompraStatements) -> None:
    assert sentencias.reservar_cod(1, "AC26/") == (
        (
            "SELECT MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) "
            "WHERE emp = ? AND tip = ? AND cod LIKE ?"
        ),
        [6, 1, 14, "AC26/%"],
    )


def test_f009_r26_sql_e3_a_e6_y_e11b_ide_bajo_bloqueo(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.reservar_ide_con() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.con WITH (UPDLOCK, HOLDLOCK)",
        [],
    )
    assert sentencias.reservar_ide_dcapro() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.dcapro WITH (UPDLOCK, HOLDLOCK)",
        [],
    )
    assert sentencias.reservar_ide_ctrprodes() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.ctrprodes WITH (UPDLOCK, HOLDLOCK)",
        [],
    )
    assert sentencias.reservar_ide_mov() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.mov WITH (UPDLOCK, HOLDLOCK)",
        [],
    )
    assert sentencias.reservar_ide_log() == (
        "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.log WITH (UPDLOCK, HOLDLOCK)",
        [],
    )


def test_f009_r26_sql_e7_balance_bajo_bloqueo(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.reservar_balance(55, 7) == (
        (
            "SELECT TOP 1 almcan, almpma FROM dbo.mov WITH (UPDLOCK, HOLDLOCK) "
            "WHERE proide = ? AND almide = ? ORDER BY fechor DESC, ide DESC"
        ),
        [55, 7],
    )


def test_f009_r25_sql_e9_a_e11_medicion_del_contrato(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.sumar_servido(9001, -2.5) == (
        "UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?",
        [-2.5, 9001],
    )
    assert sentencias.leer_sumas_contrato(300) == (
        "SELECT SUM(can), SUM(canser), SUM(canfac) FROM dbo.ctrpro WHERE docide = ?",
        [300],
    )
    assert sentencias.actualizar_estados_contrato(300, 1, 0) == (
        "UPDATE dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?",
        [1, 0, 300],
    )


def test_f009_r28_sql_e12_relecturas_por_clave(
    sentencias: AlbaranCompraStatements,
) -> None:
    assert sentencias.releer_con(1, "AC26/15953") == (
        "SELECT COUNT(*) FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?",
        [1, 14, "AC26/15953"],
    )
    assert sentencias.releer_dca(100) == (
        "SELECT COUNT(*) FROM dbo.dca WHERE ide = ?",
        [100],
    )
    assert sentencias.releer_dcapro(100) == (
        "SELECT COUNT(*) FROM dbo.dcapro WHERE docide = ?",
        [100],
    )
    assert sentencias.releer_ctrprodes(100) == (
        "SELECT COUNT(*) FROM dbo.ctrprodes WHERE docdeside = ? AND docdestip = ?",
        [100, 14],
    )
    assert sentencias.releer_mov(100) == (
        "SELECT COUNT(*) FROM dbo.mov WHERE docide = ? AND doctip = ?",
        [100, 14],
    )
    assert sentencias.releer_log(900) == (
        "SELECT COUNT(*) FROM dbo.log WHERE ide = ?",
        [900],
    )


def test_f009_r26_sql_applocks_en_su_orden() -> None:
    assert APPLOCKS == (
        "SIGRID_REFEXT_14",
        "SIGRID_SERIE_14",
        "SIGRID_IDE_con",
        "SIGRID_IDE_dcapro",
        "SIGRID_IDE_ctrprodes",
        "SIGRID_IDE_mov",
        "SIGRID_IDE_log",
    )


# --- T4 · E8: inserciones -------------------------------------------------------------


def test_f009_r25_sql_columnas_de_las_tablas_de_columnas_fijas() -> None:
    """`mov` y `ctrprodes`, las del clásico; `log`, la de F-006."""
    assert MOV_COLUMNAS == (
        "ide",
        "emp",
        "docide",
        "linide",
        "tip",
        "oritip",
        "oriide",
        "destip",
        "deside",
        "proide",
        "doctip",
        "fec",
        "hor",
        "fecdoc",
        "canent",
        "cansal",
        "pre",
        "prc",
        "prepma",
        "nueusa",
        "almide",
        "almcan",
        "almpma",
        "fecblo",
        "fechor",
    )
    assert CTRPRODES_COLUMNAS == (
        "ide",
        "docproide",
        "can",
        "docdestip",
        "docdescod",
        "docdeside",
        "lindeside",
        "ctrproactide",
    )
    assert LOG_COLUMNAS == (
        "ide",
        "emp",
        "ori",
        "ope",
        "fec",
        "hor",
        "usu",
        "tab",
        "tip",
        "cod",
        "res",
        "tex",
        "est",
        "err",
    )


def test_f009_r25_sql_insert_de_las_tablas_de_columnas_fijas(
    sentencias: AlbaranCompraStatements,
) -> None:
    fila_mov = {columna: i for i, columna in enumerate(MOV_COLUMNAS)}
    sql, params = sentencias.insertar_mov(fila_mov)
    assert sql == (
        "INSERT INTO dbo.mov (ide, emp, docide, linide, tip, oritip, oriide, destip, deside, "
        "proide, doctip, fec, hor, fecdoc, canent, cansal, pre, prc, prepma, nueusa, almide, "
        "almcan, almpma, fecblo, fechor) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, "
        "?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    assert params == list(range(len(MOV_COLUMNAS)))

    fila_ctrprodes = {columna: columna for columna in reversed(CTRPRODES_COLUMNAS)}
    assert sentencias.insertar_ctrprodes(fila_ctrprodes) == (
        (
            "INSERT INTO dbo.ctrprodes (ide, docproide, can, docdestip, docdescod, docdeside, "
            "lindeside, ctrproactide) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        list(CTRPRODES_COLUMNAS),
    )

    fila_log = {columna: columna for columna in LOG_COLUMNAS}
    assert sentencias.insertar_log(fila_log) == (
        (
            "INSERT INTO dbo.log (ide, emp, ori, ope, fec, hor, usu, tab, tip, cod, res, tex, est, "
            "err) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        ),
        list(LOG_COLUMNAS),
    )


@pytest.mark.parametrize(
    "metodo, columnas",
    [
        ("insertar_mov", MOV_COLUMNAS),
        ("insertar_ctrprodes", CTRPRODES_COLUMNAS),
        ("insertar_log", LOG_COLUMNAS),
    ],
)
def test_f009_r25_sql_una_fila_de_columnas_fijas_que_no_cuadra_no_se_inserta(
    sentencias: AlbaranCompraStatements, metodo: str, columnas: tuple[str, ...]
) -> None:
    """Ni de menos (quedaría NULL) ni de más (se perdería en silencio)."""
    completa = dict.fromkeys(columnas, 0)
    falta = {k: v for k, v in completa.items() if k != columnas[-1]}
    sobra = {**completa, "otra": 1}
    for fila in (falta, sobra):
        with pytest.raises(ValueError, match="columnas"):
            getattr(sentencias, metodo)(fila)


def test_f009_r25_sql_insert_de_las_tablas_clonadas_con_las_columnas_de_la_fila(
    sentencias: AlbaranCompraStatements,
) -> None:
    """`con`, `dca` y `dcapro` se clonan de su plantilla (`SELECT *`): las
    columnas son las de la fila, en su orden, entre corchetes y validadas."""
    fila = {"ide": 100, "tip": 14, "cod": "AC26/1", "del": "", "res": "x"}
    assert sentencias.insertar_con(fila) == (
        "INSERT INTO dbo.con ([ide], [tip], [cod], [del], [res]) VALUES (?, ?, ?, ?, ?)",
        [100, 14, "AC26/1", "", "x"],
    )
    assert sentencias.insertar_dca({"ide": 100, "synckey": "ALB-1"}) == (
        "INSERT INTO dbo.dca ([ide], [synckey]) VALUES (?, ?)",
        [100, "ALB-1"],
    )
    assert sentencias.insertar_dcapro({"ide": 7, "refent": "L1", "prepma": 1.5}) == (
        "INSERT INTO dbo.dcapro ([ide], [refent], [prepma]) VALUES (?, ?, ?)",
        [7, "L1", 1.5],
    )


@pytest.mark.parametrize(
    "columna",
    [
        "ide]) VALUES (1); DROP TABLE dbo.con; --",
        "a b",
        "1ide",
        "ruesma_rep.dbo.gra",
        "",
        "[ide]",
        "co-l",
    ],
)
def test_f009_r31_una_columna_que_no_es_un_identificador_se_rechaza(
    sentencias: AlbaranCompraStatements, columna: str
) -> None:
    with pytest.raises(IdentifierValidationError):
        sentencias.insertar_dcapro({"ide": 1, columna: 2})


def test_f009_r31_una_fila_clonada_vacia_no_se_inserta(
    sentencias: AlbaranCompraStatements,
) -> None:
    with pytest.raises(ValueError, match="vacia"):
        sentencias.insertar_dca({})


# --- R31: SQL constante, con `?`, sin verbos prohibidos ni otra base ------------------


_PROHIBIDOS = re.compile(
    r"\b(DELETE|MERGE|DROP|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|GRANT|REVOKE|USE|OPENROWSET|"
    r"OPENDATASOURCE|INTO\s+#)\b",
    re.IGNORECASE,
)


def test_f009_r31_sin_delete_merge_ni_ddl(sentencias: AlbaranCompraStatements) -> None:
    todas = sentencias.todas_las_sentencias()
    assert len(todas) == len(set(todas)) == 40
    for sql in todas:
        assert not _PROHIBIDOS.search(sql), sql
        assert sql.startswith(("SELECT ", "INSERT INTO dbo.", "UPDATE dbo.")), sql
        assert ";" not in sql, sql
        assert "'" not in sql, sql  # ningún literal: todo valor va como ?
        assert "--" not in sql and "/*" not in sql, sql


def test_f009_r31_sin_mas_update_que_los_de_r25(
    sentencias: AlbaranCompraStatements,
) -> None:
    updates = [
        sql
        for sql in sentencias.todas_las_sentencias()
        if "UPDATE" in sql.upper().replace("UPDLOCK", "")
    ]
    assert updates == [
        "UPDATE dbo.ctrpro SET canser = canser + ? WHERE ide = ?",
        "UPDATE dbo.ctr SET estser = ?, estfac = ? WHERE ide = ?",
    ]


def test_f009_r31_solo_se_inserta_en_las_seis_tablas_del_albaran(
    sentencias: AlbaranCompraStatements,
) -> None:
    """R25: ni `dcapropar`, ni `dcaproana`, ni `pro`."""
    for sql in sentencias.todas_las_sentencias():
        if sql.startswith("INSERT"):
            assert re.match(r"INSERT INTO dbo\.(mov|ctrprodes|log) \(", sql), sql
        assert "dcapropar" not in sql and "dcaproana" not in sql, sql
    with pytest.raises(ValueError, match="tabla"):
        sentencias.insertar_clonada("dcapropar", {"ide": 1})
    with pytest.raises(ValueError, match="tabla"):
        sentencias.insertar_clonada("pro", {"ide": 1})


def test_f009_r31_las_retiradas_en_la_v8_1_no_estan(
    sentencias: AlbaranCompraStatements,
) -> None:
    """L12b, L12c y E7b (media ponderada global de `prepma`) se retiraron."""
    for sql in sentencias.todas_las_sentencias():
        if "FROM dbo.mov" in sql:
            assert "almide = ?" in sql or "docide = ?" in sql or "MAX(ide)" in sql, sql
        assert "prepma" not in sql or sql.startswith("INSERT INTO dbo.mov"), sql


def test_f009_r31_el_guardia_no_rechaza_ninguna(
    sentencias: AlbaranCompraStatements,
) -> None:
    for sql in sentencias.todas_las_sentencias():
        assert DatabaseReferenceGuard.extract_database_references(sql) == [], sql
        DatabaseReferenceGuard.validate(sql, allowed=["ruesma"], contexto="escritura")


def test_f009_r31_el_constructor_valida_todas(monkeypatch: pytest.MonkeyPatch) -> None:
    vistas: list[tuple[str, list[str]]] = []
    monkeypatch.setattr(
        DatabaseReferenceGuard,
        "validate",
        staticmethod(lambda sql, *, allowed, contexto: vistas.append((sql, allowed))),
    )
    sentencias = AlbaranCompraStatements(database=" ruesma ")
    assert [sql for sql, _ in vistas] == list(sentencias.todas_las_sentencias())
    assert {tuple(allowed) for _, allowed in vistas} == {("ruesma",)}


def test_f009_r31_control_negativo_una_sentencia_con_otra_base_no_construye(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Si una constante nombrara otra base, el constructor no llega a existir."""
    monkeypatch.setattr(
        modulo,
        "L13B_USUARIO",
        "SELECT TOP (1) cod FROM ruesma_rep.dbo.usu WHERE cod = ?",
    )
    with pytest.raises(DatabaseReferenceError):
        AlbaranCompraStatements(database="ruesma")


def test_f009_r31_control_negativo_tambien_en_las_generadas(
    monkeypatch: pytest.MonkeyPatch, sentencias: AlbaranCompraStatements
) -> None:
    """Las que llevan `IN (?, …)` o columnas de la plantilla se validan al generarse."""
    monkeypatch.setattr(
        modulo,
        "L9_TASAS_IVA",
        "SELECT ide, iva FROM msdb.dbo.iva WHERE ide IN {marcadores}",
    )
    with pytest.raises(DatabaseReferenceError):
        sentencias.leer_tasas_iva([1])
    monkeypatch.setattr(
        modulo, "_TABLAS_CLONADAS", frozenset({"con", "dca", "dcapro", "msdb.dbo.x"})
    )
    with pytest.raises(DatabaseReferenceError):
        sentencias.insertar_clonada("msdb.dbo.x", {"ide": 1})
