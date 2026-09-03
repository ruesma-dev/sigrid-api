# extraer_proveedores_email.py
"""Script standalone: PROVEEDORES QUE TIENEN EMAIL, con su informacion
completa, deduplicados por CIF quedandose con la linea MAS ACTUALIZADA.

Sigrid, al actualizar la ficha de un proveedor, a menudo DUPLICA el registro y
deja la informacion nueva en el ultimo. Por eso se agrupa por CIF normalizado y
se conserva un solo proveedor por CIF: el mas reciente segun
    (con.tiemod, con.ide)
tiemod = "Tiempo modificacion" (campo de auditoria estandar de Sigrid).

EMAILS: no hay un unico campo de email en prv. Se recogen de TRES origenes y
se consolida:
  1) concnt.ele  -> "Correo electronico" de los CONTACTOS del proveedor
  2) condir.ele  -> "Correo electronico" de las DIRECCIONES del proveedor
  3) prv.facpdfele -> "Correo envio facturas PDF"
Se emite el email principal (el primero disponible por prioridad contacto >
direccion > facturas PDF) y ademas TODOS los emails distintos concatenados.

Campos VERIFICADOS contra tablas_sigrid.pdf:
  prv "Proveedores" (extiende con): cif, tipcif, cifpai, raz, dir1, dir2,
      dircpo, munide(->auxmun), proide(->auxpro), tipsub, tipdis, crelim,
      refprv, regmer, perfis, facpdfele, secide(->auxsec), taride(->auxtarprv),
      delide(->auxdel), pagide(->auxpag), cnaeide(->auxcnae), ban/bancue
  con  (padre): cod, res, fec, fecbaj, tiemod
  concnt "Contactos de conceptos" (1N por conide): res, ele, tel, tel2, tel3,
      fax, caride(->auxcar), dni
  condir "Direcciones de conceptos" (1N por conide): res, dir1, dir2, dircpo,
      munide, proide, paiide, tel, tel2, fax, ele
  auxmun / auxpro / auxpai / auxsec / auxtarprv / auxdel / auxpag / auxcnae /
  auxcar: catalogos con cod + res

Salidas:
  proveedores_email.csv          -> 1 fila por CIF (el mas actualizado)
  proveedores_email_contactos.csv-> detalle de contactos con email
  proveedores_email_descartados.csv -> duplicados descartados (trazabilidad)

Uso (SIN tocar nada):
    python extraer_proveedores_email.py
    python extraer_proveedores_email.py --incluir-bajas
    python extraer_proveedores_email.py --sin-dedup     (todas las lineas)

Config del .env del directorio actual (o variables de entorno):
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY, SIGRID_API_DATABASE, SIGRID_API_TIMEOUT_S
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import unicodedata
from datetime import date

import requests

# ----------------------------- Config editable ----------------------------- #
BASE_URL_DEFAULT = "https://func-sigridapi-dev-huyke.azurewebsites.net"
DATABASE_DEFAULT = "ruesma"
TIMEOUT_DEFAULT = 60
MAX_ROWS = 10000
PAGINA = 5000
CSV_OUT = "proveedores_email.csv"
CSV_CNT = "proveedores_email_contactos.csv"
CSV_DES = "proveedores_email_descartados.csv"
# --------------------------------------------------------------------------- #

BASE_URL = BASE_URL_DEFAULT
KEY = ""
DATABASE = DATABASE_DEFAULT
TIMEOUT = TIMEOUT_DEFAULT

_RE_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")

# --- Ficha del proveedor (1 fila por proveedor; los emails van aparte) --- #
_SQL_PROVEEDORES = """
SELECT
    c.ide                AS ide,
    c.cod                AS cod,
    c.res                AS nombre,
    p.raz                AS razon_social,
    p.cif                AS cif,
    p.tipcif             AS tipo_documento,
    p.cifpai             AS pais_cif,
    c.fec                AS fecha_alta,
    c.fecbaj             AS fecha_baja,
    c.tiemod             AS tiempo_modificacion,
    p.dir1               AS direccion1,
    p.dir2               AS direccion2,
    p.dircpo             AS codigo_postal,
    mun.res              AS municipio,
    pro.res              AS provincia,
    p.facpdfele          AS email_facturas_pdf,
    p.facpdfact          AS envia_factura_pdf,
    sec.res              AS sector,
    tar.res              AS clasificacion,
    del.res              AS delegacion,
    pag.res              AS forma_pago,
    p.pagdia             AS dias_pago,
    cna.res              AS cnae,
    p.tipsub             AS es_subcontratista,
    p.tipdis             AS es_distribuidor,
    p.perfis             AS es_persona_fisica,
    p.crelim             AS limite_credito,
    p.refprv             AS referencia_proveedor,
    p.regmer             AS registro_mercantil,
    p.ban                AS cuenta_banco_ccc,
    p.bancue             AS num_cuenta
FROM dbo.prv              AS p
INNER JOIN dbo.con        AS c   ON c.ide   = p.ide
LEFT  JOIN dbo.auxmun     AS mun ON mun.ide = p.munide
LEFT  JOIN dbo.auxpro     AS pro ON pro.ide = p.proide
LEFT  JOIN dbo.auxsec     AS sec ON sec.ide = p.secide
LEFT  JOIN dbo.auxtarprv  AS tar ON tar.ide = p.taride
LEFT  JOIN dbo.auxdel     AS del ON del.ide = p.delide
LEFT  JOIN dbo.auxpag     AS pag ON pag.ide = p.pagide
LEFT  JOIN dbo.auxcnae    AS cna ON cna.ide = p.cnaeide
WHERE 1 = 1
  {filtro_bajas}
ORDER BY c.ide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# --- Contactos con email (concnt) de proveedores --- #
_SQL_CONTACTOS = """
SELECT
    n.conide             AS ide,
    n.res                AS contacto,
    n.ele                AS email,
    n.tel                AS telefono,
    n.tel2               AS telefono2,
    n.tel3               AS movil,
    n.fax                AS fax,
    car.res              AS cargo,
    n.condoc             AS es_contacto_documentos
FROM dbo.concnt      AS n
INNER JOIN dbo.prv   AS p   ON p.ide   = n.conide
LEFT  JOIN dbo.auxcar AS car ON car.ide = n.caride
WHERE n.ele IS NOT NULL AND LTRIM(RTRIM(n.ele)) <> ''
ORDER BY n.conide, n.pos
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# --- Direcciones con email (condir) de proveedores --- #
_SQL_DIRECCIONES = """
SELECT
    d.conide             AS ide,
    d.res                AS nombre_direccion,
    d.ele                AS email,
    d.tel                AS telefono,
    d.tel2               AS telefono2,
    d.fax                AS fax,
    d.dir1               AS direccion1,
    d.dir2               AS direccion2,
    d.dircpo             AS codigo_postal,
    mun.res              AS municipio,
    pro.res              AS provincia,
    pai.res              AS pais
FROM dbo.condir      AS d
INNER JOIN dbo.prv   AS p   ON p.ide   = d.conide
LEFT  JOIN dbo.auxmun AS mun ON mun.ide = d.munide
LEFT  JOIN dbo.auxpro AS pro ON pro.ide = d.proide
LEFT  JOIN dbo.auxpai AS pai ON pai.ide = d.paiide
WHERE d.ele IS NOT NULL AND LTRIM(RTRIM(d.ele)) <> ''
ORDER BY d.conide, d.pos
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


def sql_read(sql: str, params: list) -> tuple[list[dict], bool]:
    resp = requests.post(
        f"{BASE_URL.rstrip('/')}/api/sql/read",
        headers={"x-functions-key": KEY, "Content-Type": "application/json"},
        json={"database": DATABASE, "sql": sql, "parameters": params,
              "timeout_seconds": TIMEOUT, "max_rows": MAX_ROWS},
        timeout=TIMEOUT + 60,
    )
    data = resp.json()
    if resp.status_code != 200 or not data.get("ok", False):
        sys.exit(f"[ERROR sigrid-api] HTTP {resp.status_code}: "
                 f"{data.get('error')} {data.get('details')}")
    cols = data.get("columns", [])
    return [dict(zip(cols, row)) for row in data.get("rows", [])], \
        bool(data.get("truncated", False))


def sql_read_paginado(sql_tpl: str, **fmt) -> list[dict]:
    """Encadena paginas OFFSET/FETCH hasta agotar (la API topa en MAX_ROWS)."""
    sql = sql_tpl.format(**fmt) if fmt else sql_tpl
    filas: list[dict] = []
    offset = 0
    while True:
        pagina, _ = sql_read(sql, [offset, PAGINA])
        filas.extend(pagina)
        if len(pagina) < PAGINA:
            break
        offset += PAGINA
    return filas


def norm_cif(valor) -> str:
    """CIF normalizado: mayusculas, sin guiones/puntos/espacios."""
    return (valor or "").upper().strip().replace("-", "").replace(
        ".", "").replace(" ", "")


def parse_fecha(valor) -> date | None:
    try:
        n = int(valor)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return None
    try:
        return date(n // 10000, (n // 100) % 100, n % 100)
    except ValueError:
        return None


def _fec(valor) -> str:
    f = parse_fecha(valor)
    return f.isoformat() if f else ""


def _v(valor) -> object:
    return "" if valor is None else valor


def _txt(valor) -> str:
    return (valor or "").replace("\r", " ").replace("\n", " ").strip()


def _sino(valor) -> str:
    try:
        return "SI" if int(valor) != 0 else "NO"
    except (TypeError, ValueError):
        return "NO"


def _num(valor) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def extraer_emails(texto) -> list[str]:
    """Extrae emails validos de un texto libre (puede traer varios separados
    por ; , / o espacios, y a veces texto suelto)."""
    if not texto:
        return []
    vistos: list[str] = []
    for m in _RE_EMAIL.findall(str(texto)):
        e = m.strip().lower()
        if e not in vistos:
            vistos.append(e)
    return vistos


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Proveedores con email, info completa, deduplicados por CIF.")
    ap.add_argument("--key", help="Function key (si no, del .env/entorno).")
    ap.add_argument("--base-url", help="URL base de sigrid-api (si no, del .env).")
    ap.add_argument("--db", help="Base de datos (si no, del .env; def. ruesma).")
    ap.add_argument("--incluir-bajas", action="store_true",
                    help="Incluye proveedores dados de baja (con.fecbaj > 0).")
    ap.add_argument("--sin-dedup", action="store_true",
                    help="No deduplica por CIF: saca todas las lineas con email.")
    ap.add_argument("--out", default=CSV_OUT)
    ap.add_argument("--out-contactos", default=CSV_CNT)
    ap.add_argument("--out-descartados", default=CSV_DES)
    args = ap.parse_args()

    cargar_config(args)
    print(f"  base_url={BASE_URL}  database={DATABASE}  timeout={TIMEOUT}s")

    filtro_bajas = "" if args.incluir_bajas else \
        "AND (c.fecbaj IS NULL OR c.fecbaj = 0)"

    print("1) Fichas de proveedores...")
    provs = sql_read_paginado(_SQL_PROVEEDORES, filtro_bajas=filtro_bajas)
    print(f"   proveedores: {len(provs)}")

    print("2) Contactos con email (concnt.ele)...")
    contactos = sql_read_paginado(_SQL_CONTACTOS)
    print(f"   contactos con email: {len(contactos)}")

    print("3) Direcciones con email (condir.ele)...")
    direcciones = sql_read_paginado(_SQL_DIRECCIONES)
    print(f"   direcciones con email: {len(direcciones)}")

    # Indexar emails por ide de proveedor, con prioridad de origen.
    por_ide: dict[object, dict] = {}
    for c in contactos:
        d = por_ide.setdefault(c["ide"], {"contacto": [], "direccion": [],
                                          "facturas": []})
        d["contacto"].extend(extraer_emails(c.get("email")))
    for x in direcciones:
        d = por_ide.setdefault(x["ide"], {"contacto": [], "direccion": [],
                                          "facturas": []})
        d["direccion"].extend(extraer_emails(x.get("email")))
    for p in provs:
        mails = extraer_emails(p.get("email_facturas_pdf"))
        if mails:
            d = por_ide.setdefault(p["ide"], {"contacto": [], "direccion": [],
                                              "facturas": []})
            d["facturas"].extend(mails)

    # Quedarse SOLO con proveedores que tengan algun email.
    con_email: list[dict] = []
    for p in provs:
        d = por_ide.get(p["ide"])
        if not d:
            continue
        todos: list[str] = []
        for origen in ("contacto", "direccion", "facturas"):
            for e in d[origen]:
                if e not in todos:
                    todos.append(e)
        if not todos:
            continue
        p["email_principal"] = todos[0]
        p["emails_todos"] = "; ".join(todos)
        p["num_emails"] = len(todos)
        p["origen_email"] = ("contacto" if d["contacto"] else
                             "direccion" if d["direccion"] else "facturas_pdf")
        con_email.append(p)
    print(f"4) Proveedores CON email: {len(con_email)}")

    # Deduplicar por CIF: gana el mas reciente por (tiemod, ide).
    descartados: list[dict] = []
    if args.sin_dedup:
        finales = con_email
        print("   (--sin-dedup: no se deduplica por CIF)")
    else:
        mejor: dict[str, dict] = {}
        for p in con_email:
            cif = norm_cif(p.get("cif"))
            # Sin CIF no se puede agrupar: se trata como unico por ide.
            clave = cif if cif else f"__ide_{p.get('ide')}"
            rec = (_num(p.get("tiempo_modificacion")), _num(p.get("ide")))
            actual = mejor.get(clave)
            if actual is None:
                mejor[clave] = p
                continue
            rec_act = (_num(actual.get("tiempo_modificacion")),
                       _num(actual.get("ide")))
            if rec > rec_act:
                descartados.append(actual)
                mejor[clave] = p
            else:
                descartados.append(p)
        finales = list(mejor.values())
        print(f"5) Tras deduplicar por CIF: {len(finales)} "
              f"(descartados {len(descartados)} duplicados)")

    finales.sort(key=lambda p: (p.get("cod") or ""))

    # --- CSV principal --- #
    cab = ["cod", "ide", "nombre", "razon_social", "cif", "tipo_documento",
           "pais_cif", "email_principal", "emails_todos", "num_emails",
           "origen_email", "direccion1", "direccion2", "codigo_postal",
           "municipio", "provincia", "sector", "clasificacion", "delegacion",
           "forma_pago", "dias_pago", "cnae", "es_subcontratista",
           "es_distribuidor", "es_persona_fisica", "limite_credito",
           "referencia_proveedor", "registro_mercantil", "cuenta_banco_ccc",
           "num_cuenta", "envia_factura_pdf", "email_facturas_pdf",
           "fecha_alta", "fecha_baja", "tiempo_modificacion"]

    def fila(p: dict) -> list:
        return [
            _v(p.get("cod")), _v(p.get("ide")), _v(p.get("nombre")),
            _v(p.get("razon_social")), _v(p.get("cif")),
            _v(p.get("tipo_documento")), _v(p.get("pais_cif")),
            _v(p.get("email_principal")), _v(p.get("emails_todos")),
            _v(p.get("num_emails")), _v(p.get("origen_email")),
            _v(p.get("direccion1")), _v(p.get("direccion2")),
            _v(p.get("codigo_postal")), _v(p.get("municipio")),
            _v(p.get("provincia")), _v(p.get("sector")),
            _v(p.get("clasificacion")), _v(p.get("delegacion")),
            _v(p.get("forma_pago")), _v(p.get("dias_pago")), _v(p.get("cnae")),
            _sino(p.get("es_subcontratista")), _sino(p.get("es_distribuidor")),
            _sino(p.get("es_persona_fisica")),
            _v(p.get("limite_credito")), _v(p.get("referencia_proveedor")),
            _txt(p.get("registro_mercantil")), _v(p.get("cuenta_banco_ccc")),
            _v(p.get("num_cuenta")), _sino(p.get("envia_factura_pdf")),
            _txt(p.get("email_facturas_pdf")),
            _fec(p.get("fecha_alta")), _fec(p.get("fecha_baja")),
            _v(p.get("tiempo_modificacion")),
        ]

    with open(args.out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cab)
        for p in finales:
            w.writerow(fila(p))
    print(f"   -> {args.out}")

    # --- CSV descartados (trazabilidad de la deduplicacion) --- #
    if descartados:
        with open(args.out_descartados, "w", encoding="utf-8-sig",
                  newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(cab)
            for p in sorted(descartados, key=lambda x: norm_cif(x.get("cif"))):
                w.writerow(fila(p))
        print(f"   -> {args.out_descartados}")

    # --- CSV detalle de contactos (solo de los proveedores finales) --- #
    ides_fin = {p.get("ide") for p in finales}
    with open(args.out_contactos, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(["ide_proveedor", "origen", "nombre", "cargo", "email",
                    "telefono", "telefono2", "movil", "fax"])
        for c in contactos:
            if c.get("ide") not in ides_fin:
                continue
            w.writerow([_v(c.get("ide")), "contacto", _v(c.get("contacto")),
                        _v(c.get("cargo")), _txt(c.get("email")),
                        _v(c.get("telefono")), _v(c.get("telefono2")),
                        _v(c.get("movil")), _v(c.get("fax"))])
        for x in direcciones:
            if x.get("ide") not in ides_fin:
                continue
            w.writerow([_v(x.get("ide")), "direccion",
                        _v(x.get("nombre_direccion")), "",
                        _txt(x.get("email")), _v(x.get("telefono")),
                        _v(x.get("telefono2")), "", _v(x.get("fax"))])
    print(f"   -> {args.out_contactos}")

    print(f"[OK] proveedores con email: {len(finales)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())