# scripts/diagnostico_retenciones_sigrid.py
"""
================================================================================
DIAGNÓSTICO DE RETENCIONES EN SIGRID
================================================================================

Averigua CÓMO materializa Ruesma las retenciones (garantías) en Sigrid, tanto
las que nos practican los clientes como las que practicamos a proveedores.

Hay dos patrones posibles y hay que saber cuál se usa antes de modelar:
  A) Como efecto/vencimiento en cob/pag con retención asociada (retide).
  B) Como recargo negativo en la factura (dcfrec / dvfrec, campo reccla).

Ejecuta 9 bloques de sondeo y muestra el resultado por consola. Pega la salida
completa para diseñar el módulo de retenciones.

Uso:
    python scripts/diagnostico_retenciones_sigrid.py

Requisitos: requests, python-dotenv (opcional). Lee el .env del proyecto
sigrid-api (SIGRID_API_BASE_URL / SIGRID_API_FUNCTION_KEY / SIGRID_API_DATABASE).
================================================================================
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


RAIZ = Path(__file__).resolve().parent.parent


def _cargar_env() -> None:
    if load_dotenv is None:
        return
    for c in (RAIZ / ".env", Path.cwd() / ".env"):
        if c.exists():
            load_dotenv(c)
            return


def _env(*nombres: str, default: str | None = None) -> str | None:
    for n in nombres:
        v = os.environ.get(n)
        if v:
            return v
    return default


_cargar_env()
BASE_URL = _env("SIGRID_API_BASE_URL", "SIGRID_API__BASE_URL", "SIGRID_BASE_URL")
KEY = _env("SIGRID_API_FUNCTION_KEY", "SIGRID_API__FUNCTION_KEY", "SIGRID_FUNCTION_KEY")
DATABASE = _env("SIGRID_API_DATABASE", "SIGRID_API__DATABASE", default="ruesma")
TIMEOUT = 180

if not BASE_URL or not KEY:
    print("ERROR: faltan SIGRID_API_BASE_URL / SIGRID_API_FUNCTION_KEY en el .env",
          file=sys.stderr)
    sys.exit(2)

URL = BASE_URL.rstrip("/") + "/api/sql/read"
HEADERS = {"x-functions-key": KEY, "Content-Type": "application/json"}


def q(sql: str, params: list[Any] | None = None,
      max_rows: int = 500) -> tuple[list[str], list[list[Any]]]:
    body = {
        "database": DATABASE, "sql": sql, "parameters": params or [],
        "timeout_seconds": TIMEOUT, "max_rows": max_rows,
    }
    r = requests.post(URL, json=body, headers=HEADERS, timeout=TIMEOUT + 30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
    d = r.json()
    if not d.get("ok", False):
        raise RuntimeError(f"API error: {str(d)[:300]}")
    return d["columns"], d["rows"]


def tabla(titulo: str, cols: list[str], rows: list[list[Any]],
          max_ancho: int = 30) -> None:
    print(f"\n   {titulo}")
    if not rows:
        print("      (sin resultados)")
        return
    anchos = []
    for i, c in enumerate(cols):
        ancho = max(len(str(c)), *(len(str(r[i])[:max_ancho]) for r in rows))
        anchos.append(min(ancho, max_ancho))
    print("      " + "  ".join(str(c)[:a].ljust(a) for c, a in zip(cols, anchos)))
    print("      " + "  ".join("-" * a for a in anchos))
    for r in rows:
        print("      " + "  ".join(
            str(v)[:a].ljust(a) for v, a in zip(r, anchos)))


def bloque(n: str, titulo: str) -> None:
    print("\n" + "=" * 74)
    print(f"{n}. {titulo}")
    print("=" * 74)


def seguro(fn) -> None:
    """Ejecuta un bloque tolerando errores (tablas que quizá no existan)."""
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"      [ERROR] {e}")


# =============================================================================
print(f"  base_url={BASE_URL}  database={DATABASE}")

# --- A: columnas de las tablas de efectos --------------------------------
bloque("A", "COLUMNAS DE cob (cobros) Y pag (pagos)")


def _a():
    for t in ("cob", "pag"):
        cols, rows = q(
            """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?
            ORDER BY ORDINAL_POSITION
            """, [t], max_rows=500)
        nombres = [r[0] for r in rows]
        print(f"\n   dbo.{t}: {len(nombres)} columnas")
        # Destacar las que huelen a retención / garantía / vencimiento
        clave = [n for n in nombres if any(
            k in n.lower() for k in
            ("ret", "gar", "ven", "fec", "imp", "tot", "nat", "est", "tip"))]
        print(f"      relevantes: {', '.join(clave)}")


seguro(_a)

# --- B: catálogo de definiciones de retención ----------------------------
bloque("B", "CATÁLOGO defretpag (definición de retenciones de pago)")


def _b():
    cols, rows = q(
        "SELECT ide, cod, res, porret, usaesc, codcue FROM dbo.defretpag "
        "ORDER BY pos", max_rows=200)
    tabla("defretpag", cols, rows, max_ancho=40)
    cols, rows = q("SELECT TOP 20 * FROM dbo.defretpagesc ORDER BY ide",
                   max_rows=20)
    tabla("defretpagesc (escalado)", cols, rows)


seguro(_b)

# --- C: retención de CLIENTE configurada en los contratos de obra --------
bloque("C", "RETENCIÓN DE CLIENTE: configuración en obrctr")


def _c():
    cols, rows = q(
        """
        SELECT
            SUM(CASE WHEN ISNULL(coegar,0)    <> 0 THEN 1 ELSE 0 END) AS con_coegar,
            SUM(CASE WHEN ISNULL(cobporret,0) <> 0 THEN 1 ELSE 0 END) AS con_cobporret,
            SUM(CASE WHEN ISNULL(plaret,0)    <> 0 THEN 1 ELSE 0 END) AS con_plaret,
            SUM(CASE WHEN ISNULL(plagar,0)    <> 0 THEN 1 ELSE 0 END) AS con_plagar,
            SUM(CASE WHEN ISNULL(fecdevret,0) <> 0 THEN 1 ELSE 0 END) AS con_fecdevret,
            SUM(CASE WHEN ISNULL(fecfingar,0) <> 0 THEN 1 ELSE 0 END) AS con_fecfingar,
            COUNT(*) AS total_contratos
        FROM dbo.obrctr
        """, max_rows=10)
    tabla("¿cuántos contratos de obra tienen retención configurada?", cols, rows)

    cols, rows = q(
        """
        SELECT TOP 15
            c.cod AS obra, c.res AS nombre_obra,
            oc.coegar, oc.cobporret, oc.plaret, oc.plagar,
            oc.cobfecret, oc.cobfecpor1, oc.cobfecret2, oc.cobfecpor2,
            oc.fecdevret, oc.fecinigar, oc.fecfingar
        FROM dbo.obrctr oc
        JOIN dbo.con c ON c.ide = oc.obride
        WHERE ISNULL(oc.coegar,0) <> 0 OR ISNULL(oc.cobporret,0) <> 0
        ORDER BY oc.ide DESC
        """, max_rows=20)
    tabla("muestra de contratos con retención", cols, rows, max_ancho=22)


seguro(_c)

# --- D: ¿los efectos llevan retención asociada? --------------------------
bloque("D", "PATRÓN A: retención como efecto en cob / pag (retide)")


def _d():
    for t, quien in (("cob", "clientes"), ("pag", "proveedores")):
        cols, rows = q(
            f"""
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN ISNULL(retide,0) <> 0 THEN 1 ELSE 0 END) AS con_retide
            FROM dbo.{t}
            """, max_rows=10)
        tabla(f"{t} ({quien}): ¿cuántos tienen retide?", cols, rows)


seguro(_d)

# --- E: naturalezas de cobro/pago (¿existe una "retención"?) -------------
bloque("E", "NATURALEZAS DE COBRO/PAGO (auxnac) — ¿hay una de retención?")


def _e():
    cols, rows = q("SELECT ide, cod, res FROM dbo.auxnac ORDER BY ide",
                   max_rows=200)
    tabla("auxnac", cols, rows, max_ancho=45)


seguro(_e)

# --- F: recargos: ¿se usan como retención? -------------------------------
bloque("F", "PATRÓN B: retención como recargo (rec / dcfrec / dvfrec)")


def _f():
    cols, rows = q("SELECT ide, cod, res FROM dbo.rec ORDER BY ide",
                   max_rows=200)
    tabla("catálogo rec (recargos)", cols, rows, max_ancho=45)

    for t, doc in (("dcfrec", "facturas de compra"),
                   ("dvfrec", "facturas de venta")):
        cols, rows = q(
            f"""
            SELECT r.recide, rc.cod, rc.res, r.reccla,
                   COUNT(*) AS n_lineas,
                   SUM(r.cuo) AS suma_cuota
            FROM dbo.{t} r
            LEFT JOIN dbo.rec rc ON rc.ide = r.recide
            GROUP BY r.recide, rc.cod, rc.res, r.reccla
            ORDER BY COUNT(*) DESC
            """, max_rows=100)
        tabla(f"{t} ({doc}): recargos usados", cols, rows, max_ancho=28)


seguro(_f)

# --- G: garantías y avales en facturas de compra -------------------------
bloque("G", "GARANTÍAS/AVALES EN FACTURAS DE COMPRA (dcf)")


def _g():
    cols, rows = q(
        """
        SELECT
            COUNT(*) AS total_facturas,
            SUM(CASE WHEN ISNULL(tipgar,0) <> 0 THEN 1 ELSE 0 END) AS con_tipgar,
            SUM(CASE WHEN ISNULL(impavr,0) <> 0 THEN 1 ELSE 0 END) AS con_impavr,
            SUM(CASE WHEN ISNULL(avride,0) <> 0 THEN 1 ELSE 0 END) AS con_avride
        FROM dbo.dcf
        """, max_rows=10)
    tabla("dcf: uso de campos de garantía", cols, rows)

    cols, rows = q(
        """
        SELECT tipgar, COUNT(*) AS n, SUM(impavr) AS suma_aval
        FROM dbo.dcf GROUP BY tipgar ORDER BY COUNT(*) DESC
        """, max_rows=50)
    tabla("dcf por tipo de garantía", cols, rows)


seguro(_g)

# --- H: avales recibidos / entregados ------------------------------------
bloque("H", "AVALES (avr = recibidos de proveedor, ava = entregados a cliente)")


def _h():
    for t, desc in (("avr", "recibidos"), ("ava", "entregados")):
        cols, rows = q(f"SELECT COUNT(*) AS n FROM dbo.{t}", max_rows=5)
        tabla(f"{t} ({desc}): volumen", cols, rows)
        cols, rows = q(
            f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='{t}'
            ORDER BY ORDINAL_POSITION
            """, max_rows=200)
        print(f"      columnas: {', '.join(r[0] for r in rows)}")


seguro(_h)

# --- I: volúmenes generales ----------------------------------------------
bloque("I", "VOLÚMENES DE LAS TABLAS IMPLICADAS")


def _i():
    tablas = ["cob", "pag", "rec", "dcfrec", "dvfrec", "avr", "ava",
              "defretpag", "defretpagesc", "dvf", "dvfpro", "cer", "obrcer"]
    filas = []
    for t in tablas:
        try:
            _, r = q(f"SELECT COUNT(*) FROM dbo.{t}", max_rows=5)
            filas.append([t, f"{int(r[0][0]):,}"])
        except Exception as e:  # noqa: BLE001
            filas.append([t, f"ERROR ({str(e)[:30]})"])
    tabla("conteos", ["tabla", "filas"], filas)


seguro(_i)

print("\n[OK] diagnóstico completado.\n")
