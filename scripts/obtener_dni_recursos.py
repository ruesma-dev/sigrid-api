# obtener_dni_recursos.py
"""Script standalone: obtiene el DNI de empleados de Sigrid a partir del nombre.

Busca en dbo.emp (extiende dbo.con) por nombre normalizado (sin tildes ni
mayusculas) y devuelve DNI (emp.dni), codigo (con.cod) y nombre (con.res).

Campos VERIFICADOS contra tablas_sigrid.pdf:
    emp "Empleados" (extiende con): dni ("DNI/CIF"), dnipai ("Pais del DNI")
    con (padre): cod, res, fecbaj

Uso (SIN tocar nada):
    python obtener_dni_recursos.py

Config del .env del directorio actual (o variables de entorno):
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY, SIGRID_API_DATABASE, SIGRID_API_TIMEOUT_S
"""
from __future__ import annotations

import os
import sys
import unicodedata

import requests

# ----------------------------- Config editable ----------------------------- #
BASE_URL_DEFAULT = "https://func-sigridapi-dev-huyke.azurewebsites.net"
DATABASE_DEFAULT = "ruesma"
TIMEOUT_DEFAULT = 30
MAX_ROWS = 10000

# Nombres a buscar (tal cual, con o sin tildes; el matching los normaliza).
NOMBRES = [
    "José Gómez García",
    "Rafael Serrano Rodríguez",
    "Francisco Javier Roldán Jiménez",
    "José Luis Colmenar Romero",
]
# --------------------------------------------------------------------------- #

# Trae todos los empleados no dados de baja; el match fino se hace en cliente
# (asi toleramos tildes, orden de apellidos y espacios dobles).
_SQL_EMPLEADOS = """
SELECT c.cod AS cod, c.res AS nombre, e.dni AS dni, e.dnipai AS pais
FROM dbo.emp AS e
INNER JOIN dbo.con AS c ON c.ide = e.ide
WHERE (c.fecbaj IS NULL OR c.fecbaj = 0)
ORDER BY c.res
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


def _leer_dotenv(ruta: str = ".env") -> dict[str, str]:
    valores: dict[str, str] = {}
    if not os.path.exists(ruta):
        return valores
    with open(ruta, "r", encoding="utf-8") as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def cfg() -> tuple[str, str, str, int]:
    env = _leer_dotenv()

    def pick(*nombres: str, default: str = "") -> str:
        for n in nombres:
            if os.environ.get(n):
                return os.environ[n]
            if env.get(n):
                return env[n]
        return default

    base = pick("SIGRID_API_BASE_URL", default=BASE_URL_DEFAULT)
    db = pick("SIGRID_API_DATABASE", default=DATABASE_DEFAULT)
    key = pick("SIGRID_API_FUNCTION_KEY", "SIGRID_API_KEY",
               "SIGRID_API_CODE", "SIGRID_FUNCTION_KEY")
    try:
        to = int(pick("SIGRID_API_TIMEOUT_S", default=str(TIMEOUT_DEFAULT)))
    except ValueError:
        to = TIMEOUT_DEFAULT
    if not key:
        sys.exit("[ERROR] Falta la key. Define SIGRID_API_FUNCTION_KEY en el .env.")
    return base, db, key, to


def sql_read(base: str, db: str, key: str, to: int, sql: str, params: list) -> list[dict]:
    resp = requests.post(
        f"{base.rstrip('/')}/api/sql/read",
        headers={"x-functions-key": key, "Content-Type": "application/json"},
        json={"database": db, "sql": sql, "parameters": params,
              "timeout_seconds": to, "max_rows": MAX_ROWS},
        timeout=to + 60,
    )
    data = resp.json()
    if resp.status_code != 200 or not data.get("ok", False):
        sys.exit(f"[ERROR sigrid-api] HTTP {resp.status_code}: "
                 f"{data.get('error')} {data.get('details')}")
    cols = data.get("columns", [])
    return [dict(zip(cols, row)) for row in data.get("rows", [])]


def norm(texto: str) -> str:
    """Minusculas, sin tildes, sin dobles espacios."""
    t = unicodedata.normalize("NFD", (texto or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return " ".join(t.split())


def main() -> int:
    base, db, key, to = cfg()

    # Cargar todos los empleados activos (paginado por si son >10k).
    empleados: list[dict] = []
    offset = 0
    while True:
        pagina = sql_read(base, db, key, to, _SQL_EMPLEADOS, [offset, MAX_ROWS])
        empleados.extend(pagina)
        if len(pagina) < MAX_ROWS:
            break
        offset += MAX_ROWS
    print(f"empleados activos cargados: {len(empleados)}\n")

    # Indexar por nombre normalizado.
    idx: dict[str, list[dict]] = {}
    for e in empleados:
        idx.setdefault(norm(e.get("nombre")), []).append(e)

    print(f"{'Nombre buscado':<36}{'DNI':<14}{'Cod':<10}Nombre en Sigrid")
    print("-" * 90)
    for nombre in NOMBRES:
        clave = norm(nombre)
        matches = idx.get(clave)
        if not matches:
            # Fallback: coincidencia por 'contiene' en ambos sentidos.
            matches = [e for e in empleados
                       if clave in norm(e.get("nombre"))
                       or norm(e.get("nombre")) in clave]
        if not matches:
            print(f"{nombre:<36}{'NO ENCONTRADO':<14}")
            continue
        for e in matches:
            print(f"{nombre:<36}{str(e.get('dni') or ''):<14}"
                  f"{str(e.get('cod') or ''):<10}{e.get('nombre') or ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
