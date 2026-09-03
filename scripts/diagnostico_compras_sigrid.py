# diagnostico_compras_sigrid.py
"""Script standalone de DIAGNOSTICO del circuito de compras en Sigrid.

Ejecuta tres bloques contra sigrid-api (POST /api/sql/read):

  A. VOLUMENES: COUNT(*) de com, ctr, ctrpro, dca, dcapro, dcapropar,
     dcf, dcfpro, dcfpropar, dcfprodes  -> dimensionar la ingesta.
  B. ENLACE FACTURA -> ALBARAN: muestra de dcfpro con docoritip IN (14, 44)
     y linoriide > 0, para confirmar el patron linoriide.
  C. COLUMNAS DE dcapro: ultima fila (TOP 1 *) y, ademas, el listado de
     columnas desde INFORMATION_SCHEMA (mas legible que una fila suelta).
  D. SERIES DOCUMENTALES: agrupa dbo.con por tip (14 = albaran de compra,
     15 = factura de compra) y por el prefijo de 2 caracteres de con.cod,
     con recuento y ejemplos min/max de cada serie.

Tablas/campos VERIFICADOS contra tablas_sigrid.pdf:
  dcapropar "Desglose partidas de Albaranes de compra"
  dcfpropar "Desglose partidas de Facturas de compra"
  dcfprodes "Destinos en Facturas de compra"
  dcfpro: docide, docoritip ("Tipo origen"), docoriide, linoriide
          ("Ide linea origen"), can, pre
  dcapro: SI tiene contadores canped / canser / canfac ("Cantidad facturada")
          / cancan, ademas de canorilin, canoriant, canoriori.

Uso (SIN tocar nada):
    python diagnostico_compras_sigrid.py
    python diagnostico_compras_sigrid.py --top 50
    python diagnostico_compras_sigrid.py --csv        (vuelca los 3 a CSV)

Config del .env del directorio actual (o variables de entorno):
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY, SIGRID_API_DATABASE, SIGRID_API_TIMEOUT_S
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

import requests

# ----------------------------- Config editable ----------------------------- #
BASE_URL_DEFAULT = "https://func-sigridapi-dev-huyke.azurewebsites.net"
DATABASE_DEFAULT = "ruesma"
TIMEOUT_DEFAULT = 120          # los COUNT(*) sobre tablas grandes tardan
MAX_ROWS = 10000
TOP_DEFAULT = 20
TABLA_COLUMNAS = "dcapro"      # tabla a inspeccionar en el bloque C
# --------------------------------------------------------------------------- #

BASE_URL = BASE_URL_DEFAULT
KEY = ""
DATABASE = DATABASE_DEFAULT
TIMEOUT = TIMEOUT_DEFAULT

# --- A. Volumenes --- #
_SQL_VOLUMENES = """
SELECT 'com' AS tabla, COUNT(*) AS n FROM dbo.com
UNION ALL SELECT 'ctr',       COUNT(*) FROM dbo.ctr
UNION ALL SELECT 'ctrpro',    COUNT(*) FROM dbo.ctrpro
UNION ALL SELECT 'dca',       COUNT(*) FROM dbo.dca
UNION ALL SELECT 'dcapro',    COUNT(*) FROM dbo.dcapro
UNION ALL SELECT 'dcapropar', COUNT(*) FROM dbo.dcapropar
UNION ALL SELECT 'dcf',       COUNT(*) FROM dbo.dcf
UNION ALL SELECT 'dcfpro',    COUNT(*) FROM dbo.dcfpro
UNION ALL SELECT 'dcfpropar', COUNT(*) FROM dbo.dcfpropar
UNION ALL SELECT 'dcfprodes', COUNT(*) FROM dbo.dcfprodes
"""

# --- B. Enlace factura -> albaran (patron linoriide) --- #
# Se enriquece con el codigo/tipo del documento origen para leerlo mejor.
_SQL_ENLACE = """
SELECT TOP (?)
       fp.ide          AS linea_factura_ide,
       fp.docide       AS factura_ide,
       fc.cod          AS factura_cod,
       fp.linoriide    AS linea_origen_ide,
       fp.docoritip    AS tipo_origen,
       fp.docoriide    AS doc_origen_ide,
       fp.docoricod    AS doc_origen_cod,
       fp.can          AS cantidad,
       fp.pre          AS precio,
       fp.res          AS descripcion
FROM dbo.dcfpro       AS fp
LEFT JOIN dbo.con     AS fc ON fc.ide = fp.docide
WHERE fp.docoritip IN (14, 44) AND fp.linoriide > 0
ORDER BY fp.ide DESC
"""

# --- C1. Ultima fila de dcapro (TOP 1 *) --- #
_SQL_ULTIMA_FILA = """
SELECT TOP 1 * FROM dbo.{tabla} ORDER BY ide DESC
"""

# --- C2. Columnas de la tabla (mas legible que una fila suelta) --- #
_SQL_COLUMNAS = """
SELECT c.ORDINAL_POSITION      AS pos,
       c.COLUMN_NAME           AS columna,
       c.DATA_TYPE             AS tipo,
       c.CHARACTER_MAXIMUM_LENGTH AS longitud,
       c.IS_NULLABLE           AS admite_null
FROM INFORMATION_SCHEMA.COLUMNS AS c
WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = 'dbo'
ORDER BY c.ORDINAL_POSITION
"""


# --- D. Series de albaranes de compra (tip=14) y facturas (tip=15) --- #
# con.tip = tipo de concepto; se agrupa por el prefijo de 2 caracteres del
# codigo, que es la serie documental (p.ej. AC26/..., FC26/...).
_SQL_SERIES = """
SELECT c.tip                 AS tip,
       LEFT(c.cod, 2)        AS serie,
       COUNT(*)              AS n,
       MIN(c.cod)            AS ejemplo_min,
       MAX(c.cod)            AS ejemplo_max
FROM dbo.con AS c
WHERE c.tip IN (14, 15)
GROUP BY c.tip, LEFT(c.cod, 2)
ORDER BY c.tip, n DESC
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


def cargar_config(args: argparse.Namespace) -> None:
    global BASE_URL, KEY, DATABASE, TIMEOUT
    env = _leer_dotenv()

    def pick(*nombres: str, default: str = "") -> str:
        for n in nombres:
            if os.environ.get(n):
                return os.environ[n]
            if env.get(n):
                return env[n]
        return default

    BASE_URL = args.base_url or pick("SIGRID_API_BASE_URL", default=BASE_URL_DEFAULT)
    DATABASE = args.db or pick("SIGRID_API_DATABASE", default=DATABASE_DEFAULT)
    KEY = args.key or pick("SIGRID_API_FUNCTION_KEY", "SIGRID_API_KEY",
                           "SIGRID_API_CODE", "SIGRID_FUNCTION_KEY")
    try:
        TIMEOUT = int(pick("SIGRID_API_TIMEOUT_S", default=str(TIMEOUT_DEFAULT)))
    except ValueError:
        TIMEOUT = TIMEOUT_DEFAULT
    if not KEY:
        sys.exit("[ERROR] Falta la key. Define SIGRID_API_FUNCTION_KEY en el .env.")


def sql_read(sql: str, params: list | None = None, fatal: bool = True):
    """Devuelve (columnas, filas). Si fatal=False, un error no aborta: devuelve
    (None, mensaje) para poder seguir con los demas bloques."""
    resp = requests.post(
        f"{BASE_URL.rstrip('/')}/api/sql/read",
        headers={"x-functions-key": KEY, "Content-Type": "application/json"},
        json={"database": DATABASE, "sql": sql, "parameters": params or [],
              "timeout_seconds": TIMEOUT, "max_rows": MAX_ROWS},
        timeout=TIMEOUT + 60,
    )
    try:
        data = resp.json()
    except ValueError:
        msg = f"HTTP {resp.status_code}: respuesta no JSON"
        if fatal:
            sys.exit(f"[ERROR sigrid-api] {msg}")
        return None, msg
    if resp.status_code != 200 or not data.get("ok", False):
        msg = (f"HTTP {resp.status_code}: {data.get('error')} "
               f"{data.get('details')}")
        if fatal:
            sys.exit(f"[ERROR sigrid-api] {msg}")
        return None, msg
    cols = data.get("columns", [])
    filas = [dict(zip(cols, row)) for row in data.get("rows", [])]
    return cols, filas


def _s(valor) -> str:
    return "" if valor is None else str(valor)


def tabla_consola(cols: list[str], filas: list[dict], max_ancho: int = 28) -> None:
    """Imprime una tabla alineada, recortando valores largos."""
    if not filas:
        print("   (sin filas)")
        return
    anchos = {}
    for c in cols:
        ancho = max(len(c), *(len(_s(f.get(c))) for f in filas))
        anchos[c] = min(ancho, max_ancho)
    print("   " + "  ".join(c[:anchos[c]].ljust(anchos[c]) for c in cols))
    print("   " + "  ".join("-" * anchos[c] for c in cols))
    for f in filas:
        print("   " + "  ".join(
            _s(f.get(c))[:anchos[c]].ljust(anchos[c]) for c in cols))


def a_csv(nombre: str, cols: list[str], filas: list[dict]) -> None:
    with open(nombre, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cols)
        for f in filas:
            w.writerow([_s(f.get(c)).replace("\r", " ").replace("\n", " ")
                        for c in cols])
    print(f"   -> {nombre}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diagnostico del circuito de compras en Sigrid.")
    ap.add_argument("--key", help="Function key (si no, del .env/entorno).")
    ap.add_argument("--base-url", help="URL base de sigrid-api (si no, del .env).")
    ap.add_argument("--db", help="Base de datos (si no, del .env; def. ruesma).")
    ap.add_argument("--top", type=int, default=TOP_DEFAULT,
                    help=f"Filas de la muestra del bloque B (def. {TOP_DEFAULT}).")
    ap.add_argument("--tabla", default=TABLA_COLUMNAS,
                    help=f"Tabla a inspeccionar en el bloque C (def. {TABLA_COLUMNAS}).")
    ap.add_argument("--csv", action="store_true",
                    help="Ademas de imprimir, vuelca cada bloque a CSV.")
    args = ap.parse_args()

    cargar_config(args)
    print(f"  base_url={BASE_URL}  database={DATABASE}  timeout={TIMEOUT}s\n")

    # ---------------- A. Volumenes ---------------- #
    print("=" * 70)
    print("A. VOLUMENES (dimensionar la ingesta)")
    print("=" * 70)
    cols, filas = sql_read(_SQL_VOLUMENES, fatal=False)
    if cols is None:
        print(f"   [ERROR] {filas}")
    else:
        total = 0
        print(f"   {'tabla':<12}{'filas':>14}")
        print("   " + "-" * 26)
        for f in filas:
            n = f.get("n") or 0
            total += int(n)
            print(f"   {_s(f.get('tabla')):<12}{int(n):>14,}".replace(",", "."))
        print("   " + "-" * 26)
        print(f"   {'TOTAL':<12}{total:>14,}".replace(",", "."))
        if args.csv:
            a_csv("diag_a_volumenes.csv", cols, filas)

    # ---------------- B. Enlace factura -> albaran ---------------- #
    print()
    print("=" * 70)
    print("B. ENLACE FACTURA -> ALBARAN (patron linoriide)")
    print("=" * 70)
    cols_b, filas_b = sql_read(_SQL_ENLACE, [args.top], fatal=False)
    if cols_b is None:
        print(f"   [ERROR] {filas_b}")
    else:
        print(f"   muestra de {len(filas_b)} lineas con docoritip IN (14,44) "
              f"y linoriide > 0\n")
        tabla_consola(cols_b, filas_b)
        if not filas_b:
            print("   NOTA: sin resultados. Prueba otros valores de docoritip:")
            print("         SELECT docoritip, COUNT(*) FROM dbo.dcfpro "
                  "GROUP BY docoritip")
        if args.csv and filas_b:
            a_csv("diag_b_enlace_factura_albaran.csv", cols_b, filas_b)

    # ---------------- C. Columnas de dcapro ---------------- #
    print()
    print("=" * 70)
    print(f"C. COLUMNAS DE dbo.{args.tabla}")
    print("=" * 70)

    # C2 primero: el listado de columnas es mas legible que una fila suelta.
    cols_c2, filas_c2 = sql_read(_SQL_COLUMNAS, [args.tabla], fatal=False)
    if cols_c2 is None:
        print(f"   [ERROR listado de columnas] {filas_c2}")
    else:
        print(f"   {len(filas_c2)} columnas (INFORMATION_SCHEMA):\n")
        tabla_consola(cols_c2, filas_c2)
        # Resaltar los contadores de cantidad, que es la pregunta de fondo.
        contadores = [f for f in filas_c2
                      if _s(f.get("columna")).lower().startswith("can")]
        if contadores:
            print("\n   Contadores de cantidad presentes: "
                  + ", ".join(_s(f.get("columna")) for f in contadores))
        if args.csv:
            a_csv(f"diag_c_columnas_{args.tabla}.csv", cols_c2, filas_c2)

    # C1: la fila real (TOP 1 *), en vertical para que se lea.
    print()
    print(f"   Ultima fila de dbo.{args.tabla} (TOP 1 * ORDER BY ide DESC):\n")
    cols_c1, filas_c1 = sql_read(
        _SQL_ULTIMA_FILA.format(tabla=args.tabla), fatal=False)
    if cols_c1 is None:
        print(f"   [ERROR] {filas_c1}")
    elif not filas_c1:
        print("   (tabla vacia)")
    else:
        fila = filas_c1[0]
        ancho = max(len(c) for c in cols_c1)
        for c in cols_c1:
            valor = _s(fila.get(c)).replace("\r", " ").replace("\n", " ")
            print(f"   {c.ljust(ancho)} : {valor[:80]}")
        if args.csv:
            a_csv(f"diag_c_ultima_fila_{args.tabla}.csv", cols_c1, filas_c1)

    # ---------------- D. Series de albaranes y facturas ---------------- #
    print()
    print("=" * 70)
    print("D. SERIES DOCUMENTALES (tip=14 albaranes compra, tip=15 facturas)")
    print("=" * 70)
    cols_d, filas_d = sql_read(_SQL_SERIES, fatal=False)
    if cols_d is None:
        print(f"   [ERROR] {filas_d}")
    else:
        etiquetas = {14: "albaran compra", 15: "factura compra"}
        tip_actual = None
        for f in filas_d:
            tip = f.get("tip")
            if tip != tip_actual:
                tip_actual = tip
                print(f"\n   tip={_s(tip)} ({etiquetas.get(tip, '?')})")
                print(f"   {'serie':<8}{'n':>10}  {'min':<22}{'max':<22}")
                print("   " + "-" * 62)
            print(f"   {_s(f.get('serie')):<8}"
                  f"{int(f.get('n') or 0):>10,}".replace(",", ".")
                  + f"  {_s(f.get('ejemplo_min')):<22}"
                    f"{_s(f.get('ejemplo_max')):<22}")
        if not filas_d:
            print("   (sin filas: revisa si tip 14/15 son los correctos con")
            print("    SELECT tip, COUNT(*) FROM dbo.con GROUP BY tip)")
        if args.csv and filas_d:
            a_csv("diag_d_series.csv", cols_d, filas_d)

    print("\n[OK] diagnostico completado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())