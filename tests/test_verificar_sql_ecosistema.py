# tests/test_verificar_sql_ecosistema.py
"""
F-003 · El verificador del ecosistema.

Este script es la prueba de la condición que puso el humano al aprobar la
feature: «no puede fallar la escritura/lectura que se hace ahora». Si se
rompiera en silencio —por ejemplo, dejando de reconocer un fichero como
consumidor de la API— seguiría diciendo «ningún rechazo» sin haber mirado
nada, y esa es la peor forma de fallar que puede tener una verificación.

Sin red y sin base de datos: se le dan ficheros en un directorio temporal.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.verificar_sql_ecosistema import (
    extraer_sql,
    main,
    normalizar,
    recorrer,
    revisar_fichero,
)

CONSUMIDOR = 'URL = BASE + "/api/sql/read"\n'


def escribir(carpeta: Path, nombre: str, contenido: str) -> Path:
    ruta = carpeta / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


# --- extraer_sql ------------------------------------------------------------


def test_f003_r10_reconoce_una_consulta_normal() -> None:
    assert extraer_sql('sql = "SELECT ide FROM dbo.con WHERE tip = ?"') == [
        "SELECT ide FROM dbo.con WHERE tip = ?"
    ]


def test_f003_r10_reconoce_una_consulta_de_varias_lineas() -> None:
    texto = 'SQL = """\nSELECT ide, cod\nFROM dbo.con\nWHERE tip = ?\n"""'
    encontrados = extraer_sql(texto)
    assert len(encontrados) == 1
    assert "FROM dbo.con" in encontrados[0]


@pytest.mark.parametrize(
    "texto",
    [
        # Cadena corta: no es SQL.
        '"SELECT 1"',
        # Un verbo suelto sin cláusula de tabla.
        '"SELECT algo que no tiene clausula de tabla ninguna"',
        # Docstring que DESCRIBE una sentencia pero no empieza por el verbo.
        '"""Paso 10: construye el plan. Hace un UPDATE ... FROM sobre la tabla."""',
        # Código embebido en un here-string, que empieza por un import.
        '@"\nimport os\nfrom x import y\n# SELECT ide FROM dbo.con\n"@',
        # Texto de ayuda que menciona la consulta pero no la envía.
        '"   Comprueba en SSMS: SELECT TOP 5 cif FROM prv"',
    ],
)
def test_f003_r10_descarta_lo_que_no_es_sql_enviado(texto: str) -> None:
    """
    Cada uno de estos salió del ecosistema real y llenaba el informe de ruido.
    Un verificador con 42 falsos positivos no lo mira nadie.
    """
    assert extraer_sql(texto) == []


# --- normalizar -------------------------------------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT ide FROM {database_rep}.dbo.gra",
        "SELECT ide FROM ${SigridBaseDocumental}.dbo.gra",
        "SELECT ide FROM $SigridBaseDocumental.dbo.gra",
    ],
)
def test_f003_r10_las_interpolaciones_se_sustituyen_por_el_peor_caso(sql: str) -> None:
    """
    El nombre de la base viaja en una variable en los cinco scripts reales que
    la interpolan. Si el verificador no la sustituye, no ve nada.
    """
    assert "ruesma_rep.dbo.gra" in normalizar(sql)


# --- revisar_fichero --------------------------------------------------------


def test_f003_r10_ignora_un_fichero_que_no_habla_con_esta_api(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        "pg_repository.py",
        'import psycopg\nSQL = "SELECT ide FROM otra_base.dbo.tabla"\n',
    )
    habla, rechazos = revisar_fichero(ruta)
    assert habla is False
    assert rechazos == []


def test_f003_r8_acepta_la_lectura_cruzada_de_los_scripts_reales(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path,
        "diagnose.py",
        CONSUMIDOR
        + 'SQL = "SELECT g.ide FROM dbo.gra g JOIN {database_rep}.dbo.gra d ON d.cod = g.cod"\n',
    )
    habla, rechazos = revisar_fichero(ruta)
    assert habla is True
    assert rechazos == []


def test_f003_r7_delata_una_lectura_contra_una_base_ajena(tmp_path: Path) -> None:
    ruta = escribir(
        tmp_path, "malo.py", CONSUMIDOR + 'SQL = "SELECT ide FROM msdb.dbo.sysjobs"\n'
    )
    _, rechazos = revisar_fichero(ruta)
    assert len(rechazos) == 1
    assert "msdb" in rechazos[0][1]


def test_f003_r1_delata_una_escritura_contra_la_documental(tmp_path: Path) -> None:
    """La escritura se mide contra ALLOWED_WRITE_DATABASES, más estrecha."""
    ruta = escribir(
        tmp_path,
        "escritor.py",
        CONSUMIDOR + 'SQL = "INSERT INTO ruesma_rep.dbo.gra (ide) VALUES (?)"\n',
    )
    _, rechazos = revisar_fichero(ruta)
    assert len(rechazos) == 1
    assert "ruesma_rep" in rechazos[0][1]
    assert "escritura" in rechazos[0][1]


def test_f003_r8_una_lectura_de_la_documental_si_pasa(tmp_path: Path) -> None:
    """Misma base, distinto verbo, distinta lista: es la asimetría del diseño."""
    ruta = escribir(
        tmp_path,
        "lector.py",
        CONSUMIDOR + 'SQL = "SELECT ide FROM ruesma_rep.dbo.gra WHERE cod = ?"\n',
    )
    _, rechazos = revisar_fichero(ruta)
    assert rechazos == []


def test_f003_r10_un_literal_partido_por_el_extractor_no_cuenta_como_rechazo(tmp_path: Path) -> None:
    """
    `print("... LIKE '%" + cif + "%'")` deja una comilla sin cerrar al
    extraerlo. Es ruido del extractor, no SQL que se envíe así.
    """
    ruta = escribir(
        tmp_path,
        "ayuda.py",
        CONSUMIDOR + 'print("SELECT TOP 5 cif FROM prv WHERE cif LIKE \'%" + cif + "%\'")\n',
    )
    _, rechazos = revisar_fichero(ruta)
    assert rechazos == []


# --- recorrer ---------------------------------------------------------------


def test_f003_r10_no_entra_en_las_carpetas_ignoradas(tmp_path: Path) -> None:
    escribir(tmp_path, "bueno.py", "x = 1")
    escribir(tmp_path, ".venv/malo.py", "x = 1")
    escribir(tmp_path, "node_modules/malo.js", "x = 1")
    escribir(tmp_path, "sub/.tmp/drop/malo.json", "{}")
    escribir(tmp_path, "notas.md", "texto")  # extensión fuera de la lista
    assert [ruta.name for ruta in recorrer(tmp_path)] == ["bueno.py"]


# --- main -------------------------------------------------------------------


def test_f003_r10_main_devuelve_cero_cuando_no_hay_nada_que_romper(tmp_path, capsys) -> None:
    escribir(
        tmp_path,
        "ok.py",
        CONSUMIDOR + 'SQL = "SELECT ide FROM dbo.con WHERE tip = ?"\n',
    )
    assert main(["--raiz", str(tmp_path)]) == 0
    assert "ninguna consulta del ecosistema sería rechazada" in capsys.readouterr().out


def test_f003_r10_main_devuelve_uno_cuando_algo_se_rompe(tmp_path, capsys) -> None:
    escribir(
        tmp_path, "mal.py", CONSUMIDOR + 'SQL = "SELECT ide FROM msdb.dbo.sysjobs"\n'
    )
    assert main(["--raiz", str(tmp_path)]) == 1
    salida = capsys.readouterr().out
    assert "[RECHAZO]" in salida
    assert "msdb" in salida


def test_f003_r10_main_avisa_si_la_raiz_no_existe(tmp_path, capsys) -> None:
    assert main(["--raiz", str(tmp_path / "no_existe")]) == 2


# --- El resumen que se lee al final (mutación F-003, pasada 1) --------------
#
# Los números del resumen son la conclusión del verificador: si un contador
# miente, el informe dice «256 consumidores revisados» habiendo mirado otra
# cosa, y nadie lo notaría. Por eso se comprueban uno a uno.


def _arbol_conocido(carpeta: Path) -> None:
    """Tres consumidores (uno con dos rechazos) y dos ficheros ajenos."""
    escribir(carpeta, "c1.py", CONSUMIDOR + 'S = "SELECT ide FROM dbo.con WHERE tip = ?"\n')
    escribir(carpeta, "c2.py", CONSUMIDOR + 'S = "SELECT ide FROM ruesma_rep.dbo.gra"\n')
    escribir(
        carpeta,
        "c3.py",
        CONSUMIDOR
        + 'A = "SELECT ide FROM msdb.dbo.sysjobs"\n'
        + 'B = "INSERT INTO ruesma_rep.dbo.gra (ide) VALUES (?)"\n',
    )
    escribir(carpeta, "ajeno.py", 'import psycopg\nS = "SELECT ide FROM tempdb.dbo.x"\n')
    escribir(carpeta, "otro.py", "x = 1\n")


def test_f003_r10_el_resumen_cuenta_bien_los_ficheros_y_los_consumidores(tmp_path, capsys) -> None:
    _arbol_conocido(tmp_path)
    main(["--raiz", str(tmp_path)])
    salida = capsys.readouterr().out
    assert "Ficheros recorridos: 5" in salida
    assert "De ellos, hablan con esta API: 3" in salida


def test_f003_r10_el_resumen_cuenta_bien_los_rechazos(tmp_path, capsys) -> None:
    _arbol_conocido(tmp_path)
    main(["--raiz", str(tmp_path)])
    salida = capsys.readouterr().out
    assert "Ficheros con rechazos: 1" in salida
    assert "sentencias rechazadas: 2" in salida


def test_f003_r10_un_arbol_limpio_no_cuenta_rechazos(tmp_path, capsys) -> None:
    escribir(tmp_path, "c1.py", CONSUMIDOR + 'S = "SELECT ide FROM dbo.con WHERE tip = ?"\n')
    assert main(["--raiz", str(tmp_path)]) == 0
    salida = capsys.readouterr().out
    assert "Ficheros recorridos: 1" in salida
    assert "De ellos, hablan con esta API: 1" in salida
    assert "Ficheros con rechazos" not in salida


def test_f003_r10_la_cabecera_declara_las_listas_con_las_que_se_midio(tmp_path, capsys) -> None:
    """
    Sin saber contra qué listas se midió, el «cero rechazos» no significa nada.
    """
    escribir(tmp_path, "c1.py", CONSUMIDOR + 'S = "SELECT ide FROM dbo.con WHERE tip = ?"\n')
    main(["--raiz", str(tmp_path)])
    salida = capsys.readouterr().out
    assert "Lectura permitida : master, ruesma_rep, ruesma" in salida
    assert "Escritura permit. : ruesma" in salida
    assert ("=" * 78) in salida
    assert ("=" * 79) not in salida
    assert ("-" * 78) in salida
    assert ("-" * 79) not in salida


def test_f003_r10_el_sql_largo_se_recorta_salvo_con_detalle(tmp_path, capsys) -> None:
    largo = "SELECT " + ", ".join(f"columna_{i}" for i in range(30)) + " FROM msdb.dbo.sysjobs"
    assert len(largo) > 200
    escribir(tmp_path, "c1.py", CONSUMIDOR + f'S = "{largo}"\n')

    main(["--raiz", str(tmp_path)])
    recortado = capsys.readouterr().out
    assert largo[:150] in recortado
    assert largo[:151] not in recortado
    assert largo not in recortado

    main(["--raiz", str(tmp_path), "--detalle"])
    assert largo in capsys.readouterr().out


def test_f003_r10_una_cadena_de_veinte_caracteres_todavia_es_sql() -> None:
    """El corte por longitud es `< 20`, no `<= 20`: el borde importa."""
    sql = "SELECT a FROM bb.c.d"
    assert len(sql) == 20
    assert extraer_sql(f'S = "{sql}"') == [sql]


def test_f003_r10_un_fichero_ilegible_no_cuenta_como_consumidor(tmp_path, monkeypatch) -> None:
    """
    Mata el `return False, []` del `except OSError`, que ningún test recorría.
    Un fichero que no se puede leer no puede declararse consumidor de la API:
    diría que se revisó algo que nadie miró.
    """
    ruta = escribir(tmp_path, "ilegible.py", CONSUMIDOR)

    def explota(*args, **kwargs):
        raise OSError("permiso denegado")

    monkeypatch.setattr(Path, "read_text", explota)
    habla, rechazos = revisar_fichero(ruta)
    assert habla is False
    assert rechazos == []
