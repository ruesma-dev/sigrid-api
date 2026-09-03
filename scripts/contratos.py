# tools/inspeccionar_docs_contrato.py
"""Inspecciona y descarga TODOS los documentos asociados a un contrato.

Uso (consola, PowerShell o CMD):

    python inspeccionar_docs_contrato.py "CTSU22/0162"

Configuración: variables de entorno SIGRID_API_BASE_URL y
SIGRID_API_FUNCTION_KEY (las mismas del .env de sv3), o edita las
constantes de abajo.

Qué hace:
  1. Resuelve el contrato por su código (ruesma: con + ctr).
  2. Lista los documentos relacionados (rcg → gra) con TODOS los campos
     discriminantes: rcg.pos, rcg.cla, gra.cod/res/cla/fec/nom/nomori/
     gratipide (+ su descripción en auxgra)/anx/ori/graant/tipocu/numrev
     y gra.tex (camino).
  3. Cruza con PFfir (tabla de firmas) para marcar qué gra están
     vinculados a procesos de firma.
  4. Resuelve cada gra.cod en ruesma_rep (donde vive el binario) y
     DESCARGA todos los ficheros a ./docs_<codigo>/ nombrados
     "<rep_ide>_<nomori>".
  5. Imprime un resumen para deducir el patrón de selección del
     "contrato bueno" frente a audit-trails/firmas/borradores.

Solo usa la librería estándar (urllib), sin dependencias.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------- #
# Configuración
# --------------------------------------------------------------------- #
BASE_URL = os.environ.get(
    "SIGRID_API_BASE_URL",
    "https://func-sigridapi-dev-huyke.azurewebsites.net",
).rstrip("/")
FUNCTION_KEY = os.environ.get("SIGRID_API_FUNCTION_KEY", "PON_AQUI_LA_KEY")
DB = os.environ.get("SIGRID_DB", "ruesma")
DB_REP = os.environ.get("SIGRID_DB_REP", "ruesma_rep")
TIMEOUT_S = 60

# --------------------------------------------------------------------- #
# Helpers HTTP (stdlib)
# --------------------------------------------------------------------- #


def _post_json(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{BASE_URL}{path}"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-functions-key": FUNCTION_KEY,
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


def sql_read(database: str, sql: str, params: list[Any]) -> list[dict[str, Any]]:
    data = _post_json(
        "/api/sql/read",
        {
            "database": database,
            "sql": sql,
            "parameters": params,
            "timeout_seconds": TIMEOUT_S,
            "max_rows": 500,
        },
    )
    cols = data.get("columns") or []
    rows = data.get("rows") or []
    return [dict(zip(cols, r)) for r in rows]


def download_gra(rep_ide: int, dest: Path) -> tuple[bool, str]:
    """Descarga el binario gra.ima de ruesma_rep. Devuelve (ok, detalle)."""
    url = f"{BASE_URL}/api/documents/read"
    payload = {
        "database": DB_REP,
        "schema": "dbo",
        "table": "gra",
        "id_column": "ide",
        "id_value": int(rep_ide),
        "blob_column": "ima",
        "filename_columns": ["nomori", "nom"],
        "disposition": "attachment",
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-functions-key": FUNCTION_KEY,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            content = resp.read()
            if not content:
                return False, "cuerpo vacío"
            dest.write_bytes(content)
            return True, f"{len(content)} bytes"
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return False, repr(exc)


# --------------------------------------------------------------------- #
# Formato
# --------------------------------------------------------------------- #


def fmt_fecha(v: Any) -> str:
    try:
        n = int(v)
    except (TypeError, ValueError):
        return "-"
    if n <= 0:
        return "-"
    s = str(n)
    return f"{s[6:8]}/{s[4:6]}/{s[0:4]}" if len(s) == 8 else s


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name or "").strip("_") or "sin_nombre"


def print_table(title: str, rows: list[dict[str, Any]], cols: list[str]) -> None:
    print(f"\n=== {title} ===")
    if not rows:
        print("  (sin filas)")
        return
    widths = {
        c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols
    }
    header = " | ".join(c.ljust(min(widths[c], 40)) for c in cols)
    print("  " + header)
    print("  " + "-" * len(header))
    for r in rows:
        line = " | ".join(
            str(r.get(c, "") if r.get(c) is not None else "")[:40]
            .ljust(min(widths[c], 40))
            for c in cols
        )
        print("  " + line)


# --------------------------------------------------------------------- #
# Pipeline de inspección
# --------------------------------------------------------------------- #


def main() -> int:
    if len(sys.argv) < 2:
        print('Uso: python inspeccionar_docs_contrato.py "CTSU22/0162"')
        return 2
    codigo_contrato = sys.argv[1].strip()

    # ---- Paso 1: resolver el contrato (ide) por código -------------- #
    contratos = sql_read(
        DB,
        """
        SELECT c.ide AS contrato_ide, c.cod AS codigo, c.res AS nombre
        FROM con c
        JOIN ctr ON ctr.ide = c.ide
        WHERE c.cod = ? AND c.emp = 1
        """,
        [codigo_contrato],
    )
    if not contratos:
        print(f"No se encontró contrato con código {codigo_contrato!r}.")
        return 1
    contrato = contratos[0]
    contrato_ide = int(contrato["contrato_ide"])
    print(
        f"Contrato: {contrato['codigo']} — {contrato.get('nombre')} "
        f"(ide={contrato_ide})"
    )

    # ---- Paso 2: clases de gráfico (auxgra), defensivo -------------- #
    clases: dict[int, str] = {}
    try:
        for row in sql_read(DB, "SELECT ide, cod, res FROM auxgra", []):
            try:
                clases[int(row["ide"])] = (
                    f"{row.get('cod') or ''} {row.get('res') or ''}".strip()
                )
            except (TypeError, ValueError, KeyError):
                continue
    except Exception as exc:  # noqa: BLE001
        print(f"(auxgra no disponible: {exc})")

    # ---- Paso 3: documentos relacionados (rcg → gra) en ruesma ------ #
    docs = sql_read(
        DB,
        """
        SELECT
            rcg.pos        AS rel_pos,
            rcg.cla        AS rel_cla,
            g.ide          AS gra_ide,
            g.cod          AS gra_cod,
            g.res          AS resumen,
            g.cla          AS clave,
            g.fec          AS fecha,
            g.nom          AS nom,
            g.nomori       AS nomori,
            g.gratipide    AS gratipide,
            g.anx          AS anexo,
            g.ori          AS procedencia,
            g.graant       AS version_anterior,
            g.tipocu       AS oculto,
            g.numrev       AS num_revision,
            g.tex          AS camino
        FROM rcg
        JOIN gra g ON rcg.gra = g.ide
        WHERE rcg.con = ?
        ORDER BY rcg.pos
        """,
        [contrato_ide],
    )
    for d in docs:
        d["fecha"] = fmt_fecha(d.get("fecha"))
        tip = d.get("gratipide")
        d["clase_doc"] = clases.get(int(tip), str(tip)) if tip else "-"
        ext = str(d.get("nomori") or d.get("nom") or "").lower()
        d["ext"] = ext.rsplit(".", 1)[-1] if "." in ext else "?"

    print_table(
        f"Documentos relacionados con el contrato (ruesma.rcg→gra): {len(docs)}",
        docs,
        [
            "rel_pos", "rel_cla", "gra_ide", "gra_cod", "ext", "nomori",
            "resumen", "clase_doc", "anexo", "procedencia",
            "version_anterior", "num_revision", "oculto", "fecha", "camino",
        ],
    )

    # ---- Paso 4: firmas (PFfir) que apuntan a estos gra, defensivo -- #
    gra_ides = [int(d["gra_ide"]) for d in docs if d.get("gra_ide") is not None]
    if gra_ides:
        placeholders = ",".join("?" for _ in gra_ides)
        try:
            firmas = sql_read(
                DB,
                f"""
                SELECT graide, dogide, tipfir, estfir, fec AS fecha_firma
                FROM PFfir
                WHERE graide IN ({placeholders})
                """,
                gra_ides,
            )
            for f in firmas:
                f["fecha_firma"] = fmt_fecha(f.get("fecha_firma"))
            print_table(
                "Vínculos de firma (ruesma.PFfir sobre esos gra)",
                firmas,
                ["graide", "dogide", "tipfir", "estfir", "fecha_firma"],
            )
        except Exception as exc:  # noqa: BLE001
            print(f"(PFfir no disponible: {exc})")

    # ---- Paso 5: resolver en ruesma_rep y descargar TODO ------------ #
    out_dir = Path(f"docs_{safe_name(codigo_contrato)}")
    out_dir.mkdir(exist_ok=True)
    print(f"\n=== Resolución en {DB_REP} + descarga a ./{out_dir}/ ===")

    rep_rows: list[dict[str, Any]] = []
    for d in docs:
        cod = d.get("gra_cod")
        if not cod:
            continue
        try:
            reps = sql_read(
                DB_REP,
                """
                SELECT ide AS rep_ide, cod, res, fec, nom, nomori,
                       gratipide, anx, ori, graant, numrev, tipocu
                FROM gra
                WHERE cod = ?
                """,
                [cod],
            )
        except Exception as exc:  # noqa: BLE001
            print(f"  gra_cod={cod}: error consultando rep: {exc}")
            continue
        if not reps:
            print(f"  gra_cod={cod} ({d.get('nomori')}): SIN fila en rep")
            continue
        for rep in reps:
            rep["fec"] = fmt_fecha(rep.get("fec"))
            rep["gra_cod_ruesma"] = cod
            rep["nomori_ruesma"] = d.get("nomori")
            rep_rows.append(rep)
            rep_ide = int(rep["rep_ide"])
            fname = f"{rep_ide}_{safe_name(str(rep.get('nomori') or rep.get('nom') or 'doc'))}"
            ok, detail = download_gra(rep_ide, out_dir / fname)
            estado = "OK " if ok else "FALLO"
            print(f"  [{estado}] rep_ide={rep_ide} → {fname} ({detail})")

    print_table(
        f"Filas en {DB_REP}.gra",
        rep_rows,
        [
            "rep_ide", "cod", "nomori", "res", "gratipide", "anx", "ori",
            "graant", "numrev", "tipocu", "fec",
        ],
    )

    # ---- Paso 6: pista de patrón ------------------------------------ #
    print("\n=== Pistas de patrón (heurística por nombre) ===")
    suspect = re.compile(
        r"audit|trail|evidenc|certificad|signaturit|firma", re.IGNORECASE
    )
    for d in docs:
        name = str(d.get("nomori") or d.get("nom") or "")
        marca = []
        if suspect.search(name):
            marca.append("¿FIRMA/AUDIT?")
        if d.get("ext") not in ("pdf",):
            marca.append("no-PDF")
        if d.get("version_anterior"):
            marca.append(f"versión de gra_ide={d['version_anterior']}")
        if str(d.get("oculto") or "0") not in ("0", "None", ""):
            marca.append("OCULTO")
        print(f"  pos={d['rel_pos']} {name}  →  {', '.join(marca) or 'candidato a contrato'}")

    print(
        "\nListo. Mándame la salida completa de esta consola (y dime cuál de "
        "los ficheros descargados es el contrato 'bueno') para fijar el "
        "criterio de selección en sv3."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())