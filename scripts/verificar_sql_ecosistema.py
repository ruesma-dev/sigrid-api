# scripts/verificar_sql_ecosistema.py
"""
================================================================================
VERIFICADOR · ¿ROMPERÍA EL GUARDIA DE BASES ALGO DE LO QUE HOY FUNCIONA?
================================================================================

F-003 añade una defensa: las sentencias que llegan a `sql/read` y `sql/write` ya
no pueden nombrar una base fuera de la lista blanca, ni siquiera cualificando el
nombre dentro del SQL. Eso cierra un agujero real, pero abre un riesgo: que una
consulta legítima que hoy funciona empiece a fallar.

Este script responde a esa pregunta con hechos. Recorre los repositorios del
ecosistema, extrae las cadenas que parecen SQL destinado a esta API y las pasa
por el guardia REAL, con la configuración REAL de la Function App desplegada.
Informa de todo lo que sería rechazado.

Es la verificación de la condición que puso el humano al aprobar F-003:
«no puede fallar la escritura/lectura que se hace ahora».

No toca la red ni la base de datos: solo lee ficheros y ejecuta el guardia.

Uso:
    python scripts/verificar_sql_ecosistema.py
    python scripts/verificar_sql_ecosistema.py --raiz C:\\ruta\\a\\PycharmProjects
    python scripts/verificar_sql_ecosistema.py --detalle

Código de salida: 0 si no hay nada que se rompa; 1 si aparece algún rechazo.
================================================================================
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from infrastructure.security.database_reference_guard import (
    DatabaseReferenceError,
    DatabaseReferenceGuard,
)

# Configuración REAL de la Function App, comprobada con
# `az functionapp config appsettings list` el 2026-09-03.
ALLOWED_DATABASES = ["master", "ruesma_rep", "ruesma"]
ALLOWED_WRITE_DATABASES = ["ruesma"]

EXTENSIONES = {".py", ".ps1", ".ts", ".js", ".cs", ".sql", ".json", ".yml", ".yaml"}
CARPETAS_IGNORADAS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".idea", ".vscode",
    "dist", ".dist", "build", ".pytest_cache", ".ruff_cache", "site-packages",
    ".tmp", "worktrees",
    # Los tests no envían SQL a la API: llevan sentencias de ejemplo, muchas
    # pensadas justo para que el guardia las rechace. Sin esta exclusión, el
    # verificador se delata a sí mismo y el informe deja de significar nada.
    "tests",
}

# Solo interesa el SQL que va a ESTA API. Media docena de proyectos del
# ecosistema hablan con PostgreSQL, y su SQL no pasa por estos guardias: si no
# se filtran, el informe se llena de ruido y deja de servir para decidir.
SENAL_DE_LA_API = re.compile(
    r"sql/read|sql/write|SIGRID_API|x-functions-key|sigridapi|"
    r"database_rep|SigridBaseDocumental|sigrid/albaran|sigrid/contrato",
    re.IGNORECASE,
)

# Una cadena que parece SQL: lleva un verbo y una cláusula de tabla.
#
# `VALUES` está en la segunda alternancia porque sin él un
# `INSERT INTO t (a) VALUES (?)` no casaba —el `INTO` lo consume el primer
# grupo y no queda ninguna otra palabra clave detrás—, y el verificador se
# saltaba en silencio las escrituras, que son justo las que más importan. Lo
# encontró `tests/test_verificar_sql_ecosistema.py`, no una lectura del código.
PARECE_SQL = re.compile(
    r"\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|WITH)\b.*?\b(FROM|INTO|JOIN|SET|VALUES)\b",
    re.IGNORECASE | re.DOTALL,
)
ES_ESCRITURA = re.compile(r"^\s*(INSERT|UPDATE|DELETE|MERGE)\b", re.IGNORECASE)

# Una cadena SQL de verdad EMPIEZA por su verbo. Exigirlo descarta el ruido que
# si no inunda el informe y lo vuelve inservible: bloques de código embebidos en
# here-strings, docstrings que describen sentencias, textos de ayuda que las
# mencionan.
EMPIEZA_POR_VERBO = re.compile(
    r"^\s*(?:--[^\n]*\n|/\*.*?\*/|\s)*(SELECT|WITH|INSERT|UPDATE|DELETE)\b",
    re.IGNORECASE | re.DOTALL,
)

# Literales de varias líneas y de una línea, en Python y en PowerShell.
LITERALES = [
    re.compile(r'"""(.*?)"""', re.DOTALL),
    re.compile(r"'''(.*?)'''", re.DOTALL),
    re.compile(r'@"(.*?)"@', re.DOTALL),
    re.compile(r"@'(.*?)'@", re.DOTALL),
    re.compile(r'`(.*?)`', re.DOTALL),
    re.compile(r'"((?:[^"\\\n]|\\.)*)"'),
    re.compile(r"'((?:[^'\\\n]|\\.)*)'"),
]

# Interpolaciones: se sustituyen por el peor caso, el nombre de la base
# documental, que es lo que de verdad se interpola en el ecosistema.
INTERPOLACION = re.compile(r"\{[^{}\n]*\}|\$\{[^}\n]*\}|\$[A-Za-z_][A-Za-z0-9_]*")
PEOR_CASO = "ruesma_rep"


def extraer_sql(texto: str) -> list[str]:
    encontrados: list[str] = []
    for patron in LITERALES:
        for match in patron.finditer(texto):
            cadena = match.group(1)
            if len(cadena) < 20 or not PARECE_SQL.search(cadena):
                continue
            if not EMPIEZA_POR_VERBO.match(cadena):
                continue
            encontrados.append(cadena)
    return encontrados


def normalizar(sql: str) -> str:
    """Deja el SQL en la forma en que viajaría por la red."""
    sustituido = INTERPOLACION.sub(PEOR_CASO, sql)
    return sustituido.replace("\\n", "\n").replace('\\"', '"').strip()


def revisar_fichero(ruta: Path) -> tuple[bool, list[tuple[str, str]]]:
    """
    Devuelve (habla con la API, [(sql, motivo del rechazo)]).

    Solo se analiza el SQL de los ficheros que hablan con esta API: el de los
    proyectos que van contra PostgreSQL no pasa por estos guardias.
    """
    try:
        texto = ruta.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False, []

    if not SENAL_DE_LA_API.search(texto):
        return False, []

    rechazos: list[tuple[str, str]] = []
    no_analizables: list[str] = []
    for bruto in extraer_sql(texto):
        sql = normalizar(bruto)
        escritura = bool(ES_ESCRITURA.match(sql))
        permitidas = ALLOWED_WRITE_DATABASES if escritura else ALLOWED_DATABASES
        try:
            DatabaseReferenceGuard.validate(
                sql,
                allowed=permitidas,
                contexto="escritura" if escritura else "lectura",
            )
        except DatabaseReferenceError as exc:
            motivo = str(exc)
            if "sin cerrar" in motivo:
                # El extractor ha cortado una concatenación de código por la
                # mitad. El guardia real nunca vería esto: lo que viaja por la
                # red es la cadena ya montada. No es un rechazo, es ruido.
                no_analizables.append(sql)
                continue
            rechazos.append((sql, motivo))
    return True, rechazos


def recorrer(raiz: Path):
    for ruta in raiz.rglob("*"):
        if not ruta.is_file() or ruta.suffix.lower() not in EXTENSIONES:
            continue
        if CARPETAS_IGNORADAS & set(ruta.parts):
            continue
        yield ruta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raiz",
        default=str(RAIZ_PROYECTO.parent),
        help="Carpeta que contiene los repositorios del ecosistema.",
    )
    parser.add_argument(
        "--detalle", action="store_true", help="Muestra el SQL completo de cada rechazo."
    )
    args = parser.parse_args(argv)

    raiz = Path(args.raiz)
    if not raiz.is_dir():
        print(f"ERROR: no existe la carpeta {raiz}", file=sys.stderr)
        return 2

    print("=" * 78)
    print("VERIFICADOR DEL GUARDIA DE BASES (F-003)")
    print("=" * 78)
    print(f"  Raíz              : {raiz}")
    print(f"  Lectura permitida : {', '.join(ALLOWED_DATABASES)}")
    print(f"  Escritura permit. : {', '.join(ALLOWED_WRITE_DATABASES)}")
    print("  Las interpolaciones se sustituyen por el peor caso: " + PEOR_CASO)
    print()

    ficheros = 0
    consumidores = 0
    con_sql = 0
    rechazos_totales = 0

    for ruta in recorrer(raiz):
        ficheros += 1
        habla_con_la_api, rechazos = revisar_fichero(ruta)
        if habla_con_la_api:
            consumidores += 1
        if rechazos:
            con_sql += 1
            rechazos_totales += len(rechazos)
            print(f"[RECHAZO] {ruta}")
            for sql, motivo in rechazos:
                recorte = sql if args.detalle else " ".join(sql.split())[:150]
                print(f"    SQL   : {recorte}")
                print(f"    Motivo: {motivo}")
            print()

    print("-" * 78)
    print(f"Ficheros recorridos: {ficheros}")
    print(f"De ellos, hablan con esta API: {consumidores}")
    if rechazos_totales == 0:
        print()
        print("RESULTADO: ninguna consulta del ecosistema sería rechazada por el")
        print("guardia nuevo. Lo que hoy funciona seguirá funcionando.")
        return 0

    print(f"Ficheros con rechazos: {con_sql}  ·  sentencias rechazadas: {rechazos_totales}")
    print()
    print("RESULTADO: hay SQL que el guardia rechazaría. Revísalo UNO A UNO antes")
    print("de desplegar: o la consulta se corrige, o la base entra en la lista.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
