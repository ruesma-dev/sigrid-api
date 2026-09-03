# scripts/diagnostico_retenciones_2.py
"""
================================================================================
DIAGNÓSTICO DE RETENCIONES — RONDA 2 (enfocada)
================================================================================

La ronda 1 confirmó el PATRÓN A: las retenciones se materializan como efectos
en cob/pag con la columna `retide` informada.
    · 25.124 pagos    con retide (retenciones a proveedores)
    ·  2.219 cobros   con retide (retenciones que nos hace el cliente)
    ·    497 contratos de obra con coegar = 5.0 (5 % de garantía)
    · avales (avr/ava) NO se usan; defretpag vacía

Esta ronda cierra lo que falta para modelar el SALDO VIVO de cada retención:
  1. Estructura completa de cob / pag / rec.
  2. Qué es realmente el catálogo `rec` al que apunta retide.
  3. Cómo se ve un efecto de retención real (importes, signo, fechas).
  4. Si la DEVOLUCIÓN genera un efecto nuevo, encadena por padide, o solo
     se marca con fecrea (fecha real de cobro/pago).
  5. Qué campos son `entretide` y `retref` (exclusivos de pag).

Uso:
    python scripts/diagnostico_retenciones_2.py
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


def _env(*n: str, default: str | None = None) -> str | None:
    for x in n:
        v = os.environ.get(x)
        if v:
            return v
    return default


_cargar_env()
BASE_URL = _env("SIGRID_API_BASE_URL", "SIGRID_API__BASE_URL", "SIGRID_BASE_URL")
KEY = _env("SIGRID_API_FUNCTION_KEY", "SIGRID_API__FUNCTION_KEY", "SIGRID_FUNCTION_KEY")
DATABASE = _env("SIGRID_API_DATABASE", "SIGRID_API__DATABASE", default="ruesma")
TIMEOUT = 180

if not BASE_URL or not KEY:
    print("ERROR: faltan credenciales de sigrid-api en el .env", file=sys.stderr)
    sys.exit(2)

URL = BASE_URL.rstrip("/") + "/api/sql/read"
HEADERS = {"x-functions-key": KEY, "Content-Type": "application/json"}


def q(sql: str, params: list[Any] | None = None,
      max_rows: int = 500) -> tuple[list[str], list[list[Any]]]:
    body = {"database": DATABASE, "sql": sql, "parameters": params or [],
            "timeout_seconds": TIMEOUT, "max_rows": max_rows}
    r = requests.post(URL, json=body, headers=HEADERS, timeout=TIMEOUT + 30)
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:250]}")
    d = r.json()
    if not d.get("ok", False):
        raise RuntimeError(f"API error: {str(d)[:250]}")
    return d["columns"], d["rows"]


def tabla(titulo: str, cols: list[str], rows: list[list[Any]],
          max_ancho: int = 26) -> None:
    print(f"\n   {titulo}")
    if not rows:
        print("      (sin resultados)")
        return
    anchos = [min(max(len(str(c)), *(len(str(r[i])[:max_ancho]) for r in rows)),
                  max_ancho) for i, c in enumerate(cols)]
    print("      " + "  ".join(str(c)[:a].ljust(a) for c, a in zip(cols, anchos)))
    print("      " + "  ".join("-" * a for a in anchos))
    for r in rows:
        print("      " + "  ".join(str(v)[:a].ljust(a) for v, a in zip(r, anchos)))


def bloque(n: str, t: str) -> None:
    print("\n" + "=" * 74)
    print(f"{n}. {t}")
    print("=" * 74)


def seguro(fn) -> None:
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        print(f"      [ERROR] {e}")


def columnas_de(t: str) -> list[str]:
    _, rows = q(
        """
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=? ORDER BY ORDINAL_POSITION
        """, [t], max_rows=300)
    return [r[0] for r in rows]


print(f"  base_url={BASE_URL}  database={DATABASE}")

# --- J: estructura completa de cob / pag / rec ---------------------------
bloque("J", "ESTRUCTURA COMPLETA DE cob / pag / rec")


def _j():
    for t in ("cob", "pag", "rec"):
        cols, rows = q(
            """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME=?
            ORDER BY ORDINAL_POSITION
            """, [t], max_rows=300)
        print(f"\n   dbo.{t}  ({len(rows)} columnas)")
        for r in rows:
            print(f"      {r[0]:<16} {r[1]}")


seguro(_j)

# --- K: qué es el catálogo rec -------------------------------------------
bloque("K", "CATÁLOGO rec — ¿a qué apunta retide?")


def _k():
    cols = columnas_de("rec")
    print(f"      columnas de rec: {', '.join(cols)}")
    sel = ", ".join(c for c in cols
                    if c.lower() in ("ide", "cod", "res", "tip", "cla", "por",
                                     "val", "pos", "reccla", "codigo", "nom")
                    ) or "TOP 1 *"
    _c, rows = q(f"SELECT TOP 30 {sel} FROM dbo.rec ORDER BY ide", max_rows=30)
    tabla("muestra de rec", _c, rows, max_ancho=40)


seguro(_k)

# --- L: los rec efectivamente usados como retención ----------------------
bloque("L", "QUÉ VALORES DE retide SE USAN (y su volumen)")


def _l():
    for t, quien in (("pag", "PAGOS a proveedor"), ("cob", "COBROS de cliente")):
        _c, rows = q(
            f"""
            SELECT TOP 30 e.retide,
                   COUNT(*)      AS n_efectos,
                   SUM(e.tot)    AS suma_importe,
                   MIN(e.tot)    AS min_importe,
                   MAX(e.tot)    AS max_importe
            FROM dbo.{t} e
            WHERE ISNULL(e.retide,0) <> 0
            GROUP BY e.retide
            ORDER BY COUNT(*) DESC
            """, max_rows=30)
        tabla(f"{t} — {quien}: retide más usados", _c, rows)


seguro(_l)

# --- M: cómo se ve un efecto de retención real ---------------------------
bloque("M", "MUESTRA REAL DE EFECTOS DE RETENCIÓN")


def _m():
    # PAGOS (retención a proveedor)
    _c, rows = q(
        """
        SELECT TOP 15
            p.ide, p.tot, p.fecven, p.fecrea, p.retide, p.padide,
            p.conide, doc.cod AS doc_origen, doc.tip AS tip_origen,
            ent.res AS proveedor, p.natide, p.entretide, p.retref
        FROM dbo.pag p
        LEFT JOIN dbo.con doc ON doc.ide = p.conide
        LEFT JOIN dbo.con ent ON ent.ide = p.entide
        WHERE ISNULL(p.retide,0) <> 0
        ORDER BY p.ide DESC
        """, max_rows=20)
    tabla("PAGOS con retención (a proveedor)", _c, rows, max_ancho=22)

    # COBROS (retención de cliente)
    _c, rows = q(
        """
        SELECT TOP 15
            c.ide, c.tot, c.fecven, c.fecrea, c.retide, c.padide,
            c.conide, doc.cod AS doc_origen, doc.tip AS tip_origen,
            ent.res AS cliente, c.natide
        FROM dbo.cob c
        LEFT JOIN dbo.con doc ON doc.ide = c.conide
        LEFT JOIN dbo.con ent ON ent.ide = c.entide
        WHERE ISNULL(c.retide,0) <> 0
        ORDER BY c.ide DESC
        """, max_rows=20)
    tabla("COBROS con retención (de cliente)", _c, rows, max_ancho=22)


seguro(_m)

# --- N: ¿la retención está viva o devuelta? ------------------------------
bloque("N", "SALDO: ¿cuántas retenciones siguen VIVAS? (fecrea = 0 → pendiente)")


def _n():
    for t, quien in (("pag", "a proveedores"), ("cob", "de clientes")):
        _c, rows = q(
            f"""
            SELECT
                CASE WHEN ISNULL(fecrea,0) = 0 THEN 'PENDIENTE (viva)'
                     ELSE 'REALIZADA (devuelta)' END AS estado,
                COUNT(*)   AS n_efectos,
                SUM(tot)   AS suma_importe
            FROM dbo.{t}
            WHERE ISNULL(retide,0) <> 0
            GROUP BY CASE WHEN ISNULL(fecrea,0) = 0 THEN 'PENDIENTE (viva)'
                          ELSE 'REALIZADA (devuelta)' END
            """, max_rows=10)
        tabla(f"{t} — retenciones {quien}", _c, rows)


seguro(_n)

# --- O: encadenamiento por padide (¿la devolución es otro efecto?) -------
bloque("O", "¿LA DEVOLUCIÓN ENCADENA EFECTOS? (padide)")


def _o():
    for t in ("pag", "cob"):
        _c, rows = q(
            f"""
            SELECT
                SUM(CASE WHEN ISNULL(padide,0) <> 0 THEN 1 ELSE 0 END) AS con_padide,
                COUNT(*) AS total_con_retencion
            FROM dbo.{t}
            WHERE ISNULL(retide,0) <> 0
            """, max_rows=10)
        tabla(f"{t}: efectos de retención que apuntan a un padre", _c, rows)

    # Ejemplo de cadena completa
    _c, rows = q(
        """
        SELECT TOP 10
            hijo.ide AS hijo_ide, hijo.tot AS hijo_tot,
            hijo.fecven AS hijo_fecven, hijo.fecrea AS hijo_fecrea,
            padre.ide AS padre_ide, padre.tot AS padre_tot,
            padre.fecrea AS padre_fecrea, padre.retide AS padre_retide
        FROM dbo.pag hijo
        JOIN dbo.pag padre ON padre.ide = hijo.padide
        WHERE ISNULL(hijo.padide,0) <> 0
          AND (ISNULL(hijo.retide,0) <> 0 OR ISNULL(padre.retide,0) <> 0)
        ORDER BY hijo.ide DESC
        """, max_rows=15)
    tabla("cadena padre→hijo en pagos con retención", _c, rows)


seguro(_o)

# --- P: retenciones por obra (¿se puede atribuir a la obra?) -------------
bloque("P", "¿SE PUEDE ATRIBUIR LA RETENCIÓN A UNA OBRA?")


def _p():
    # Vía documento origen: pag.conide → dcf (factura compra) → líneas → obride
    _c, rows = q(
        """
        SELECT TOP 20
            obr.cod AS obra, obr.res AS nombre_obra,
            COUNT(DISTINCT p.ide) AS n_retenciones,
            SUM(p.tot)            AS importe_retenido,
            SUM(CASE WHEN ISNULL(p.fecrea,0) = 0 THEN p.tot ELSE 0 END) AS vivo
        FROM dbo.pag p
        JOIN dbo.dcfpro fp ON fp.docide = p.conide
        JOIN dbo.con obr   ON obr.ide   = fp.obride
        WHERE ISNULL(p.retide,0) <> 0
        GROUP BY obr.cod, obr.res
        ORDER BY SUM(p.tot) DESC
        """, max_rows=25)
    tabla("retenciones a proveedor agregadas por obra", _c, rows, max_ancho=24)

    # Vía cenide directamente en el efecto
    _c, rows = q(
        """
        SELECT
            SUM(CASE WHEN ISNULL(cenide,0) <> 0 THEN 1 ELSE 0 END) AS con_cenide,
            COUNT(*) AS total
        FROM dbo.pag WHERE ISNULL(retide,0) <> 0
        """, max_rows=10)
    tabla("pag: ¿el efecto lleva centro de coste?", _c, rows)


seguro(_p)

# --- Q: retención de cliente ligada a certificación/factura de venta -----
bloque("Q", "RETENCIÓN DE CLIENTE: documento origen del cobro")


def _q():
    _c, rows = q(
        """
        SELECT TOP 20
            doc.tip AS tip_documento,
            COUNT(*) AS n_cobros_con_retencion,
            SUM(c.tot) AS importe
        FROM dbo.cob c
        LEFT JOIN dbo.con doc ON doc.ide = c.conide
        WHERE ISNULL(c.retide,0) <> 0
        GROUP BY doc.tip
        ORDER BY COUNT(*) DESC
        """, max_rows=25)
    tabla("¿de qué tipo de documento nacen los cobros con retención?", _c, rows)

    # Por obra vía factura de venta
    _c, rows = q(
        """
        SELECT TOP 20
            obr.cod AS obra, obr.res AS nombre_obra,
            COUNT(DISTINCT c.ide) AS n_retenciones,
            SUM(c.tot)            AS importe_retenido,
            SUM(CASE WHEN ISNULL(c.fecrea,0) = 0 THEN c.tot ELSE 0 END) AS vivo
        FROM dbo.cob c
        JOIN dbo.dvfpro vp ON vp.docide = c.conide
        JOIN dbo.con obr   ON obr.ide   = vp.obride
        WHERE ISNULL(c.retide,0) <> 0
        GROUP BY obr.cod, obr.res
        ORDER BY SUM(c.tot) DESC
        """, max_rows=25)
    tabla("retenciones de cliente por obra (vía factura de venta)",
          _c, rows, max_ancho=24)


seguro(_q)

# --- R: campos de garantía que SÍ existen en dcf/ctr ---------------------
bloque("R", "CAMPOS DE GARANTÍA EXISTENTES EN dcf Y ctr")


def _r():
    for t in ("dcf", "ctr"):
        cols = columnas_de(t)
        gar = [c for c in cols if any(
            k in c.lower() for k in ("gar", "ret", "ava", "avr", "fia"))]
        print(f"      {t}: {', '.join(gar) if gar else '(ninguno)'}")


seguro(_r)

print("\n[OK] ronda 2 completada.\n")
