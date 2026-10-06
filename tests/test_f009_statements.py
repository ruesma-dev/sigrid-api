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

import dataclasses
import re
from decimal import Decimal

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


# =====================================================================================
# T5 · funciones puras. Se usan por `modulo.<nombre>` a propósito: así la fase RED
# falla test a test (AttributeError) sin tumbar la recogida de los de T4.
# =====================================================================================


# --- R26: numeración de la serie -------------------------------------------------------


@pytest.mark.parametrize(
    "maximo, esperado",
    [(None, "AC26/1"), (0, "AC26/1"), (1, "AC26/2"), (15952, "AC26/15953")],
)
def test_f009_r26_siguiente_cod(maximo: int | None, esperado: str) -> None:
    """E2/L14 dan el MAX numérico tras el prefijo (`None` sin ninguno): + 1,
    sin ceros a la izquierda, como el clásico (`AC26/15950`)."""
    assert modulo.siguiente_cod("AC26/", maximo) == esperado


@pytest.mark.parametrize(
    "fecha, esperado",
    [
        (20261006, "AC26/"),
        (20270101, "AC27/"),
        (20001231, "AC00/"),
        (19991231, "AC99/"),
    ],
)
def test_f009_r22_prefijo_del_anio_de_la_fecha_del_albaran(
    fecha: int, esperado: str
) -> None:
    assert modulo.prefijo_de_serie(fecha) == esperado


# --- R17: importes con Decimal y ROUND_HALF_UP --------------------------------------------


def test_f009_r17_redondear_euros_empate_hacia_arriba() -> None:
    """H33: 2,675 → 2,68 (`round` da 2,67 por la representación binaria)."""
    assert round(2.675, 2) == 2.67
    assert modulo.redondear_euros(2.675) == Decimal("2.68")
    assert modulo.redondear_euros(-2.675) == Decimal("-2.68")
    assert modulo.redondear_euros(1.005) == Decimal("1.01")
    assert modulo.redondear_euros(Decimal("0.125")) == Decimal("0.13")
    assert modulo.redondear_euros(2.674999) == Decimal("2.67")
    assert modulo.redondear_euros(0) == Decimal("0.00")


@pytest.mark.parametrize(
    "cantidad, precio, iva, tot, ivacuo",
    [
        (1.0, 2.675, 0.21, "2.68", "0.56"),  # empate en tot
        (3.0, 0.895, 0.21, "2.69", "0.56"),  # 2,685 exacto en Decimal
        (2.0, 10.5, 0.21, "21.00", "4.41"),
        (10.0, 1.25, 0.10, "12.50", "1.25"),
        (1.0, 0.5, 0.21, "0.50", "0.11"),  # 0,105 → 0,11
        (-2.0, 10.5, 0.21, "-21.00", "-4.41"),  # devolución (R18)
        (-1.0, 2.675, 0.21, "-2.68", "-0.56"),
        (7.0, 33.333333, 0.21, "233.33", "49.00"),
        (1.0, 0.0, 0.21, "0.00", "0.00"),
        (5.0, 4.0, 0.0, "20.00", "0.00"),
    ],
)
def test_f009_r17_importe_linea(
    cantidad: float, precio: float, iva: float, tot: str, ivacuo: str
) -> None:
    """`tot` = cantidad·precio e `ivacuo` = tot·iva, a 2 decimales, con el IVA de
    `dbo.iva` en fracción (M11)."""
    assert modulo.importe_linea(cantidad, precio, iva) == (
        Decimal(tot),
        Decimal(ivacuo),
    )


def test_f009_r17_sumar_importes_sin_error_binario() -> None:
    importes = [(Decimal("0.10"), Decimal("0.02")), (Decimal("0.20"), Decimal("0.04"))]
    assert modulo.sumar_importes(importes) == {
        "totbas": 0.3,
        "totiva": 0.06,
        "totdoc": 0.36,
    }
    assert modulo.sumar_importes([]) == {"totbas": 0.0, "totiva": 0.0, "totdoc": 0.0}
    resultado = modulo.sumar_importes([(Decimal("-21.00"), Decimal("-4.41"))])
    assert resultado == {"totbas": -21.0, "totiva": -4.41, "totdoc": -25.41}


@pytest.mark.parametrize(
    "precio, pre_contrato, coincide",
    [
        (10.0, 10.0, True),
        (10.0001, 10.0, True),  # en el borde: ≤ 0,0001
        (9.9999, 10.0, True),
        (10.00010001, 10.0, False),
        (10.0002, 10.0, False),
        (33.333333, 33.3333, True),  # el cociente de sv9 frente al del contrato
        (0.0, 0.0001, True),
        (0.0, 0.00011, False),
    ],
)
def test_f009_r17_tolerancia_de_precio(
    precio: float, pre_contrato: float, coincide: bool
) -> None:
    """H14: |precio − ctrpro.pre| ≤ 0,0001 (M4), sin error binario en el borde."""
    assert modulo.precio_coincide(precio, pre_contrato) is coincide


# --- R19 y R18: balance de stock, PMP y `prepma` -------------------------------------------


def test_f009_r19_balance_de_entrada() -> None:
    balance = modulo.siguiente_balance((10.0, 2.0), 5.0, 3.0)
    assert balance == modulo.Balance(
        stock_anterior=10.0, pmp_anterior=2.0, almcan=15.0, almpma=(10 * 2 + 5 * 3) / 15
    )
    # `prepma` = el PMP de PARTIDA (design §prepma, v8.1), no el resultante.
    assert balance.prepma == 2.0


def test_f009_r19_sin_mov_anterior_parte_de_cero() -> None:
    balance = modulo.siguiente_balance(None, 4.0, 2.5)
    assert (balance.stock_anterior, balance.pmp_anterior) == (0.0, 0.0)
    assert (balance.almcan, balance.almpma, balance.prepma) == (4.0, 2.5, 0.0)


def test_f009_r19_almpma_sin_redondear() -> None:
    balance = modulo.siguiente_balance((3.0, 1.0), 1.0, 2.0)
    assert balance.almpma == 5.0 / 4.0
    balance = modulo.siguiente_balance((2.0, 1.0), 1.0, 1.0 / 3.0)
    assert balance.almpma == (2.0 + 1.0 / 3.0) / 3.0
    assert round(balance.almpma, 2) != balance.almpma


def test_f009_r19_con_denominador_cero_se_conserva_el_pmp() -> None:
    balance = modulo.siguiente_balance((5.0, 7.5), -5.0, 9.0)
    assert (balance.almcan, balance.almpma, balance.prepma) == (0.0, 7.5, 7.5)
    balance = modulo.siguiente_balance((-2.0, 4.0), 2.0, 9.0)
    assert (balance.almcan, balance.almpma) == (0.0, 4.0)


def test_f009_r18_devolucion_regla_a() -> None:
    """M5: entrada con `canent` < 0 y PMP `(stock·pma + can·pre)/(stock + can)`."""
    balance = modulo.siguiente_balance((10.0, 2.0), -4.0, 3.0)
    assert balance.almcan == 6.0
    assert balance.almpma == (10 * 2 - 4 * 3) / 6
    assert balance.prepma == 2.0


def test_f009_r18_devolucion_que_deja_el_stock_negativo() -> None:
    balance = modulo.siguiente_balance((1.0, 2.0), -3.0, 2.0)
    assert balance.almcan == -2.0
    assert balance.almpma == (1 * 2 - 3 * 2) / -2
    balance = modulo.siguiente_balance(None, -1.0, 5.0)
    assert (balance.almcan, balance.almpma, balance.prepma) == (-1.0, 5.0, 0.0)


def test_f009_r19_encadenado_por_producto_y_almacen() -> None:
    """Varias líneas del mismo par se encadenan: cada una parte del resultado
    de la anterior; los pares distintos no se mezclan."""
    vigentes = {(55, 7): (10.0, 2.0), (55, 8): (1.0, 100.0)}
    balances = modulo.encadenar_balances(
        [
            (55, 7, 5.0, 3.0),
            (55, 8, 1.0, 50.0),
            (55, 7, -3.0, 4.0),
            (56, 7, 2.0, 1.0),
            (55, 7, 2.0, 1.0),
        ],
        vigentes,
    )
    primero = modulo.siguiente_balance((10.0, 2.0), 5.0, 3.0)
    tercero = modulo.siguiente_balance((primero.almcan, primero.almpma), -3.0, 4.0)
    quinto = modulo.siguiente_balance((tercero.almcan, tercero.almpma), 2.0, 1.0)
    assert balances == [
        primero,
        modulo.siguiente_balance((1.0, 100.0), 1.0, 50.0),
        tercero,
        modulo.siguiente_balance(None, 2.0, 1.0),
        quinto,
    ]
    assert tercero.prepma == primero.almpma
    assert quinto.prepma == tercero.almpma
    # Pura: los vigentes no se tocan.
    assert vigentes == {(55, 7): (10.0, 2.0), (55, 8): (1.0, 100.0)}


def test_f009_r19_encadenar_sin_lineas() -> None:
    assert modulo.encadenar_balances([], {(1, 1): (1.0, 1.0)}) == []


def test_f009_r19_el_balance_no_se_puede_cambiar() -> None:
    balance = modulo.siguiente_balance(None, 1.0, 1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        balance.almcan = 3.0  # type: ignore[misc]


# --- R15: sufijo de la cuenta analítica -----------------------------------------------------


@pytest.mark.parametrize(
    "caagascod, sufijo",
    [
        ("MOD.CDSB37", "CDSB37"),
        ("MOD.CDQA12", "CDQA12"),
        ("CDXA01", "CDXA01"),  # sin MOD., entero (M16d)
        ("  MOD.CDSB37  ", "CDSB37"),
        ("CDXA01   ", "CDXA01"),
        ("MOD.", ""),
        ("", ""),
        ("   ", ""),
        (None, ""),
        ("MOD.MOD.X", "MOD.X"),  # solo un prefijo
        ("XMOD.CDSB37", "XMOD.CDSB37"),
        ("mod.cdsb37", "mod.cdsb37"),  # el prefijo medido va en mayúsculas
        (
            "CD.SB37",
            "CD.SB37",
        ),  # un punto que no es MOD. no corta (regla de la v7, descartada)
    ],
)
def test_f009_r15_sufijo_analitica(caagascod: str | None, sufijo: str) -> None:
    assert modulo.sufijo_analitica(caagascod) == sufijo


@pytest.mark.parametrize(
    "cod_obra, caagascod, codigo",
    [
        ("0678", "MOD.CDSB37", "0678.CDSB37"),
        ("0404", "CDXA01", "0404.CDXA01"),
        ("0676-B  ", "MOD.CDQA12", "0676-B.CDQA12"),  # RTRIM del código de obra
        ("0404", "MOD.", None),
        ("0404", "", None),
        ("0404", None, None),
    ],
)
def test_f009_r15_codigo_de_la_analitica(
    cod_obra: str, caagascod: str | None, codigo: str | None
) -> None:
    """`<cod_obra>.<sufijo>`; sin sufijo no hay código (→ `analitica_no_resuelta`)."""
    assert modulo.codigo_analitica(cod_obra, caagascod) == codigo


# --- R20: estados del contrato -----------------------------------------------------------------


@pytest.mark.parametrize(
    "can, canser, canfac, estados",
    [
        (10.0, 10.0, 0.0, (1, 0)),
        (10.0, 9.99, 10.0, (0, 1)),
        (10.0, 12.0, 12.0, (1, 1)),
        (10.0, -2.0, 0.0, (0, 0)),  # devolución que deja Σcanser < 0
        (0.0, 0.0, 0.0, (1, 1)),
        (0.0, -1.0, 0.0, (0, 1)),
        (10.0, 9.999, 0.0, (1, 0)),  # a 2 decimales, como el clásico
        (10.0, 9.994, 0.0, (0, 0)),
    ],
)
def test_f009_r20_estados_contrato(
    can: float, canser: float, canfac: float, estados: tuple[int, int]
) -> None:
    """`estser` = 1 si Σcanser ≥ Σcan (una devolución puede devolverlo a 0);
    `estfac` = 1 si Σcanfac ≥ Σcan. Sumas de E10, tras el `UPDATE` de `canser`."""
    assert modulo.estados_contrato(can, canser, canfac) == estados


def test_f009_r20_estados_con_sumas_nulas() -> None:
    """`SUM` de E10 sin filas da NULL: cuenta como 0."""
    assert modulo.estados_contrato(None, None, None) == (1, 1)
