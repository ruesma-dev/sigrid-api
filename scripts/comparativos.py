# extraer_comparativos_aprobados.py
"""Script standalone: COMPARATIVOS de ofertas y su relacion con CONTRATOS,
obra, proveedor y demas informacion relacionada, a CSV.

Saca de Sigrid (via sigrid-api, POST /api/sql/read):
  1) Cabecera de los comparativos (dbo.com, que extiende dbo.con) filtrando por
     estado (con.est). Salida: comparativos_aprobados.csv
  2) Contratos adjudicados a cada comparativo (dbo.ctr), por las DOS vias:
       - ctr.comide  -> com.ide          ("Documento comparativo" del contrato)
       - comlin.ctride -> ctr.ide        ("Adjudicado a contrato" de la linea)
     Salida: comparativos_contratos.csv
  3) Proveedores invitados al comparativo (dbo.comprv) con su oferta (dco).
     Salida: comparativos_proveedores.csv
  4) Tabla auxiliar de estados (dbo.conest) del tipo de concepto comparativo.
     Salida: comparativos_estados_catalogo.csv

Ademas, enriquece con:
  * Ultima firma (dbo.confir, workflow de firmas): MAX(fec) con firok=1 o
    fir=1, tanto del comparativo como de cada contrato.
  * Importe facturado: por comparativo (importe_facturado_com) = SUM(dcf.totbas)
    de las facturas con dcf.comide, excluyendo facturas de baja (los abonos ya
    netan: dcf.facoriide los enlaza y totbas viene en negativo); por contrato =
    SUM(canfac/can * tot) de ctrpro, prorrateo del Importe Linea NETO (usar
    canfac*pre inflaria el facturado en contratos con descuento de linea).
    AVISO BI: ambos facturados miden cosas distintas (una factura contra el
    contrato sin comide en cabecera cuenta en el segundo y no en el primero).
    NUNCA sumarlos; el canonico es el de contrato (canfac es el tracking
    propio de Sigrid); el de comparativo es informativo.
  * Firma pendiente (confir con fir=0 y firok=0): firmas_pendientes,
    pendiente_desde (fecdes) y rol_pendiente (orientativo) -> donde esta
    atascado el circuito de cada comparativo.
  * KPI de contratacion: los contratos dados de baja NO cuentan en
    num_contratos ni en las sumas del bloque ctr_* (si aparecen en el CSV de
    detalle, con contrato_fecha_baja). En Power Query, filtrar igual la tabla
    de contratos o los totales no cuadraran con num_contratos.
  * Importes del comparativo (modelo Ruesma con proveedores FICTICIOS):
      - importe_comparativo = SUM(comlin.can * comlin.pre) (Total documento)
      - importe_objetivo    = oferta del proveedor ficticio *OBJETIVO*
      - importe_abc         = oferta del proveedor ficticio *ABC*
      - importe_ot          = oferta del ficticio *OFICINA TECNICA* (c/s tilde)
      - importe_planificado = oferta del ficticio *PLANIFICACION* (c/s tilde)
    Matching por 'contiene', sin mayusculas ni tildes, sobre el nombre del
    proveedor en comprv; importe = dco.totbas (fallback dco.tot); si hay
    varias ofertas del mismo ficticio, gana la de fecha mas reciente.

ESTADOS: la tabla auxiliar es dbo.conest ("Tipos de Estados de Conceptos"), que
es justo lo que Sigrid muestra en "Definicion de tipos de conceptos" > pestaña
Estados para el tipo TIPCOM ("Doc. comparativo de ofertas"). Mapea:
    conest.tip + conest.est  ->  conest.cod (p.ej. APROBADO) + conest.res
El join con los documentos es:  con.tip = conest.tip AND con.est = conest.est
El script vuelca esa tabla auxiliar a CSV y ademas resuelve el estado de cada
comparativo/contrato a su codigo y descripcion, para no depender de numeros.

Puedes filtrar por CODIGO (recomendado) o por numero:
    --estado-cod APROBADO
    --estado-cod APR,APCOM,APROBADO
    --estado 110
Si no se indica ninguno, NO filtra y saca TODOS los comparativos.

Campos VERIFICADOS contra tablas_sigrid.pdf (v.20240618):
  com  "Documento comparativo ofertas" (extiende con por ide):
    obride(->obr), empide(->emp), natide(->auxpronat), cocide(->auxobrcoc),
    ppoide(->ppo), comide(comparativo origen), feccon (fecha contratacion),
    fecent, feclim, fecinirec, fecfinrec, tipsub (es subasta), tex
  comlin "Detalle del comparativo": comide(->com), ctride(->ctr ADJUDICADO A
    CONTRATO), can, pre, pos, numlin, dcoproide
  comprv "Proveedores del comparativo": comide(->com), prvide(->prv),
    docide(->dco oferta), shrlst (short list), pos
  ctr  "Contratos de compra" (extiende con por ide): comide(->com), obride,
    entide/entcod/entres/entcif (proveedor), cocide, totbas, tot, fecdoc
  con  (padre de com, ctr, obr, prv): cod, res, fec, est, fecbaj

Lanzar desde la consola de un servicio (p.ej. sv3), SIN tocar nada:

    python extraer_comparativos_aprobados.py --listar-estados
    python extraer_comparativos_aprobados.py --estado-cod APROBADO
    python extraer_comparativos_aprobados.py --estado-cod APR,APCOM --desde-anio 2024

Config del .env del directorio actual (o variables de entorno):
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY, SIGRID_API_DATABASE, SIGRID_API_TIMEOUT_S
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import date

import requests

# ----------------------------- Config editable ----------------------------- #
BASE_URL_DEFAULT = "https://func-sigridapi-dev-huyke.azurewebsites.net"
DATABASE_DEFAULT = "ruesma"
TIMEOUT_DEFAULT = 60
MAX_ROWS = 10000
# Tamano de pagina (OFFSET/FETCH) para no topar con MAX_ROWS de la API.
PAGINA = 5000

# Estado que significa "aprobado" en con.est. None = no filtrar (todos).
# Descubrelo con --listar-estados y fijalo aqui o pasalo con --estado.
ESTADO_APROBADO = None
# Alternativa (recomendada): filtrar por CODIGO de estado de dbo.conest,
# p.ej. "APROBADO", "APR", "APCOM". Admite varios separados por coma.
# Es mas robusto que el numero, que varia por tipo/instalacion.
ESTADO_APROBADO_COD = None
ANIO_MIN_DEFAULT = 0                       # 0 = todos los anos
CSV_EST = "comparativos_estados_catalogo.csv"
CSV_COM = "comparativos_aprobados.csv"
CSV_CTR = "comparativos_contratos.csv"
CSV_PRV = "comparativos_proveedores.csv"
# --------------------------------------------------------------------------- #

BASE_URL = BASE_URL_DEFAULT
KEY = ""
DATABASE = DATABASE_DEFAULT
TIMEOUT = TIMEOUT_DEFAULT

# ---- 0a) Catalogo REAL de estados del tipo de concepto de los comparativos.
# dbo.conest "Tipos de Estados de Conceptos": tip + est -> cod + res.
# Es la tabla que se ve en Sigrid en "Definicion de tipos de conceptos" >
# pestaña Estados (para el tipo TIPCOM "Doc. comparativo de ofertas").
# El join con los documentos es: con.tip = conest.tip AND con.est = conest.est
_SQL_CATALOGO_ESTADOS = """
SELECT e.tip                    AS tip,
       e.est                    AS estado,
       e.cod                    AS estado_cod,
       e.res                    AS estado_res,
       e.pos                    AS posicion,
       e.cladef                 AS clase_predefinida,
       e.esigcod                AS estado_portal
FROM dbo.conest AS e
WHERE e.tip IN (SELECT DISTINCT c.tip
                FROM dbo.com AS m
                INNER JOIN dbo.con AS c ON c.ide = m.ide)
ORDER BY e.tip, e.pos, e.est
"""

# ---- 0b) Uso real: que estados aparecen en los comparativos y cuantos ---- #
_SQL_ESTADOS_USO = """
SELECT c.tip                    AS tip,
       c.est                    AS estado,
       e.cod                    AS estado_cod,
       e.res                    AS estado_res,
       COUNT(*)                 AS num_comparativos,
       MIN(c.fec)               AS fec_min,
       MAX(c.fec)               AS fec_max
FROM dbo.com       AS m
INNER JOIN dbo.con AS c ON c.ide = m.ide
LEFT  JOIN dbo.conest AS e ON e.tip = c.tip AND e.est = c.est
GROUP BY c.tip, c.est, e.cod, e.res
ORDER BY num_comparativos DESC
"""

# ---- 1) Cabecera de comparativos + obra + tipo contrato + naturaleza ---- #
# El filtro de estado y de ano se inyectan como predicados opcionales.
_SQL_COMPARATIVOS = """
SELECT
    m.ide                       AS comparativo_ide,
    c.cod                       AS comparativo_cod,
    c.res                       AS comparativo_res,
    c.est                       AS estado,
    ce.cod                      AS estado_cod,
    ce.res                      AS estado_res,
    c.fec                       AS fecha_alta,
    c.fecbaj                    AS fecha_baja,
    (c.fec / 10000)             AS anio,
    m.feccon                    AS fecha_contratacion,
    m.fecent                    AS fecha_entrega_prevista,
    m.feclim                    AS fecha_limite,
    m.fecinirec                 AS fec_ini_recepcion,
    m.fecfinrec                 AS fec_fin_recepcion,
    m.tipsub                    AS es_subasta,
    oc.cod                      AS obra_cod,
    oc.res                      AS obra_nombre,
    ec.cod                      AS empleado_cod,
    ec.res                      AS empleado_nombre,
    nat.res                     AS naturaleza,
    coc.res                     AS tipo_contrato,
    poc.cod                     AS presupuesto_cod,
    ori.cod                     AS comparativo_origen_cod,
    m.tex                       AS observaciones
FROM dbo.com              AS m
INNER JOIN dbo.con        AS c   ON c.ide   = m.ide
LEFT  JOIN dbo.conest     AS ce  ON ce.tip  = c.tip AND ce.est = c.est
LEFT  JOIN dbo.con        AS oc  ON oc.ide  = m.obride
LEFT  JOIN dbo.con        AS ec  ON ec.ide  = m.empide
LEFT  JOIN dbo.auxpronat  AS nat ON nat.ide = m.natide
LEFT  JOIN dbo.auxobrcoc  AS coc ON coc.ide = m.cocide
LEFT  JOIN dbo.con        AS poc ON poc.ide = m.ppoide
LEFT  JOIN dbo.con        AS ori ON ori.ide = m.comide
WHERE 1 = 1
  {filtro_estado}
  {filtro_anio}
ORDER BY m.ide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# ---- 2) Contratos relacionados con cada comparativo (las DOS vias) ---- #
# Via A: ctr.comide -> com.ide          (contrato apunta al comparativo)
# Via B: comlin.ctride -> ctr.ide       (linea del comparativo adjudicada)
# {filtro_ides} se sustituye por  AND v.comparativo_ide IN (?,?,...)
# NOTA: NO usar SELECT DISTINCT aqui: t.tex y t.pagtex son "Texto ilimitado"
# (text en SQL Server) y ese tipo NO es comparable -> error 42000. La
# subconsulta v con UNION ya deduplica los pares (comparativo, contrato, via).
_SQL_CONTRATOS = """
SELECT
    v.comparativo_ide,
    v.via,
    t.ide                       AS contrato_ide,
    tc.cod                      AS contrato_cod,
    tc.res                      AS contrato_res,
    tc.est                      AS contrato_estado,
    tce.cod                     AS contrato_estado_cod,
    tce.res                     AS contrato_estado_res,
    tc.fec                      AS contrato_fecha_alta,
    tc.fecbaj                   AS contrato_fecha_baja,
    t.fecdoc                    AS contrato_fecha_doc,
    t.fecent                    AS contrato_fecha_entrega,
    t.feclim                    AS contrato_fecha_limite,
    t.fecpag                    AS contrato_fecha_pago,
    t.fecfac                    AS contrato_fecha_factura,
    toc.cod                     AS contrato_obra_cod,
    toc.res                     AS contrato_obra_nombre,
    t.entcod                    AS proveedor_cod,
    t.entres                    AS proveedor_nombre,
    t.entcif                    AS proveedor_cif,
    t.entref                    AS proveedor_referencia,
    tcoc.res                    AS contrato_tipo,
    tec.cod                     AS contrato_empleado_cod,
    tec.res                     AS contrato_empleado_nombre,
    cec.cod                     AS centro_coste_cod,
    cec.res                     AS centro_coste_nombre,
    pag.res                     AS forma_pago,
    t.pagtex                    AS cond_pago,
    ivc.res                     AS iva_nombre,
    iv.iva                      AS iva_porcentaje,
    t.impbru                    AS importe_bruto,
    t.impdes                    AS importe_descuentos,
    t.imprec                    AS importe_recargos,
    t.totbas                    AS base_sin_iva,
    t.totiva                    AS cuota_iva,
    t.totdoc                    AS total_sin_retencion,
    t.tot                       AS total_con_retencion,
    t.totpag                    AS importe_a_pagar,
    t.estped                    AS esta_pedido,
    t.estser                    AS esta_servido,
    t.estfac                    AS esta_facturado,
    t.facper                    AS es_factura_periodica,
    t.tex                       AS contrato_observaciones
FROM (
    SELECT m.ide AS comparativo_ide, t.ide AS contrato_ide, 'ctr.comide' AS via
    FROM dbo.com AS m
    INNER JOIN dbo.ctr AS t ON t.comide = m.ide
    UNION
    SELECT l.comide AS comparativo_ide, l.ctride AS contrato_ide,
           'comlin.ctride' AS via
    FROM dbo.comlin AS l
    WHERE l.ctride IS NOT NULL AND l.ctride > 0
) AS v
INNER JOIN dbo.ctr        AS t    ON t.ide    = v.contrato_ide
INNER JOIN dbo.con        AS tc   ON tc.ide   = t.ide
LEFT  JOIN dbo.conest     AS tce  ON tce.tip  = tc.tip AND tce.est = tc.est
LEFT  JOIN dbo.con        AS toc  ON toc.ide  = t.obride
LEFT  JOIN dbo.con        AS tec  ON tec.ide  = t.empide
LEFT  JOIN dbo.con        AS cec  ON cec.ide  = t.cenide
LEFT  JOIN dbo.auxobrcoc  AS tcoc ON tcoc.ide = t.cocide
LEFT  JOIN dbo.auxpag     AS pag  ON pag.ide  = t.pagide
LEFT  JOIN dbo.iva        AS iv   ON iv.ide   = t.ivaide
LEFT  JOIN dbo.con        AS ivc  ON ivc.ide  = t.ivaide
WHERE 1 = 1
  {filtro_ides}
ORDER BY v.comparativo_ide, t.ide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


# ---- 3) Proveedores invitados al comparativo (+ su oferta dco) ---- #
_SQL_PROVEEDORES = """
SELECT
    p.comide                    AS comparativo_ide,
    p.pos                       AS posicion,
    p.shrlst                    AS short_list,
    pc.cod                      AS proveedor_cod,
    pc.res                      AS proveedor_nombre,
    prv.cif                     AS proveedor_cif,
    oc.cod                      AS oferta_cod,
    oc.res                      AS oferta_res,
    oc.est                      AS oferta_estado,
    o.fecdoc                    AS oferta_fecha,
    o.totbas                    AS oferta_base_sin_iva,
    o.tot                       AS oferta_total
FROM dbo.comprv           AS p
LEFT  JOIN dbo.prv        AS prv ON prv.ide = p.prvide
LEFT  JOIN dbo.con        AS pc  ON pc.ide  = p.prvide
LEFT  JOIN dbo.dco        AS o   ON o.ide   = p.docide
LEFT  JOIN dbo.con        AS oc  ON oc.ide  = p.docide
WHERE 1 = 1
  {filtro_ides}
ORDER BY p.comide, p.pos
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""


# ---- 4) Ultima firma por documento (dbo.confir, workflow de firmas) ---- #
# MAX(fec) de las firmas efectuadas (firok=1 o fir=1). Sirve para cualquier
# concepto (comparativos y contratos) via conide.
_SQL_ULTIMA_FIRMA = """
SELECT f.conide              AS conide,
       MAX(f.fec)            AS fecha_ultima_firma,
       COUNT(*)              AS num_firmas
FROM dbo.confir AS f
WHERE (f.firok = 1 OR f.fir = 1)
  {filtro_ides}
GROUP BY f.conide
ORDER BY f.conide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# ---- 5) Facturado por comparativo (dbo.dcf.comide -> facturas de compra) --- #
_SQL_FACTURADO_COM = """
SELECT d.comide              AS comide,
       SUM(d.totbas)         AS facturado_base,
       COUNT(*)              AS num_facturas
FROM dbo.dcf AS d
INNER JOIN dbo.con AS c ON c.ide = d.ide
WHERE (c.fecbaj IS NULL OR c.fecbaj = 0)
  {filtro_ides}
GROUP BY d.comide
ORDER BY d.comide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# ---- 6) Facturado por contrato (dbo.ctrpro.canfac = Cantidad facturada) ---- #
# NO usar canfac*pre: ignora los descuentos de linea (ctrpro.dto), mientras
# que ctr.totbas si los aplica -> facturado inflado en contratos con dto.
# ctrpro.tot es el "Importe Linea" ya neto: se prorratea canfac/can * tot.
# contratado_lineas sirve de control: debe cuadrar (o casi) con base_sin_iva
# de cabecera; si no, hay recargos de cabecera y el % de facturacion debe
# calcularse contra las lineas, no contra totbas.
_SQL_FACTURADO_CTR = """
SELECT p.docide                                 AS ctride,
       SUM(p.canfac / NULLIF(p.can, 0) * p.tot) AS facturado_importe,
       SUM(p.tot)                               AS contratado_lineas
FROM dbo.ctrpro AS p
WHERE p.can <> 0
  {filtro_ides}
GROUP BY p.docide
ORDER BY p.docide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# ---- 6b) Firma PENDIENTE por documento (circuito atascado) ---- #
# En firmas pendientes fec (fecha de firma) esta normalmente vacio porque aun
# no se ha firmado; el "pendiente desde" sale de fecdes (fecha desde).
# rol_pendiente es orientativo (MAX alfabetico de los roles pendientes).
_SQL_FIRMA_PENDIENTE = """
SELECT f.conide                        AS conide,
       COUNT(*)                        AS firmas_pendientes,
       MIN(NULLIF(f.fecdes, 0))        AS pendiente_desde,
       MAX(f.rol)                      AS rol_pendiente
FROM dbo.confir AS f
WHERE f.fir = 0 AND f.firok = 0
  {filtro_ides}
GROUP BY f.conide
ORDER BY f.conide
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

# ---- 7) Importe del comparativo (Total documento = lineas comlin) ---- #
_SQL_IMPORTE_COMPARATIVO = """
SELECT l.comide                AS comide,
       SUM(l.can * l.pre)      AS importe_comparativo
FROM dbo.comlin AS l
WHERE 1 = 1
  {filtro_ides}
GROUP BY l.comide
ORDER BY l.comide
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
    KEY = args.key or pick(
        "SIGRID_API_FUNCTION_KEY", "SIGRID_API_KEY",
        "SIGRID_API_CODE", "SIGRID_FUNCTION_KEY",
    )
    try:
        TIMEOUT = int(pick("SIGRID_API_TIMEOUT_S", default=str(TIMEOUT_DEFAULT)))
    except ValueError:
        TIMEOUT = TIMEOUT_DEFAULT

    if not KEY:
        sys.exit("[ERROR] Falta la key. Define SIGRID_API_FUNCTION_KEY en el .env, "
                 "o pasala con --key.")


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
    filas = [dict(zip(cols, row)) for row in data.get("rows", [])]
    return filas, bool(data.get("truncated", False))


# Tamano de lote para el IN (...) del filtro por ides. SQL Server admite
# hasta 2100 parametros por sentencia; 500 va sobrado y evita el tope de
# MAX_ROWS al no traerse tablas enteras.
# Ids por lote del IN (...). SQL Server admite ~2100 parametros por sentencia;
# 1000 reduce a la mitad las llamadas dejando margen holgado. La union de
# muchos ides en menos llamadas grandes baja el overhead de red drasticamente.
LOTE_IDES = 1000
# Nº de lotes CONSECUTIVOS totalmente vacios tras los cuales se asume que la
# consulta no aporta datos para este conjunto de ides y se corta (evita barrer
# 40 lotes en balde cuando p.ej. las facturas no llevan comide). Se sigue
# probando un colchon por si los datos empiezan tarde en el rango de ides.
VACIOS_PARA_CORTAR = 5


def sql_read_paginado(sql_tpl: str, params_base: list, **fmt) -> list[dict]:
    """Ejecuta una consulta paginada con OFFSET/FETCH hasta agotar resultados.

    La API tiene un tope duro de MAX_ROWS (10.000) filas POR LLAMADA, y no se
    puede subir sin tocar y redesplegar sigrid-api (y aun asi chocarias con el
    timeout de 230 s del load balancer de Azure). Por eso encadenamos varias
    queries de PAGINA filas hasta que una devuelva menos de PAGINA.
    """
    sql = sql_tpl.format(**fmt)
    filas: list[dict] = []
    offset = 0
    while True:
        pagina, _ = sql_read(sql, list(params_base) + [offset, PAGINA])
        filas.extend(pagina)
        if len(pagina) < PAGINA:
            break
        offset += PAGINA
    return filas


def sql_read_agregado_por_ides(sql_tpl: str, ides: list,
                               columna: str) -> list[dict]:
    """Para consultas AGREGADAS (GROUP BY por la columna de ids): la salida de
    cada lote es <= nº de ids del lote (<= LOTE_IDES < MAX_ROWS), asi que NO
    necesita paginacion interna -> 1 sola llamada por lote. Es el camino de
    firmas, facturado e importe_comparativo (todas GROUP BY).
    """
    if not ides:
        return []
    filas: list[dict] = []
    total_lotes = (len(ides) + LOTE_IDES - 1) // LOTE_IDES
    for i in range(0, len(ides), LOTE_IDES):
        lote = list(ides[i:i + LOTE_IDES])
        marcas = ",".join("?" for _ in lote)
        # OFFSET/FETCH a 0/MAX_ROWS: una pagina cubre todo el lote agregado.
        sql = sql_tpl.format(filtro_ides=f"AND {columna} IN ({marcas})")
        parte, truncado = sql_read(sql, list(lote) + [0, MAX_ROWS])
        if truncado:
            print(f"   AVISO: lote agregado {i // LOTE_IDES + 1} truncado "
                  f"(ids del lote > MAX_ROWS?); reduce LOTE_IDES.")
        filas.extend(parte)
        n = i // LOTE_IDES + 1
        if total_lotes > 1:
            print(f"   lote {n}/{total_lotes}: acumuladas {len(filas)} filas")
    return filas


def sql_read_por_ides(sql_tpl: str, ides: list, columna: str) -> list[dict]:
    """Consulta filtrando en SERVIDOR por lotes grandes de ides, paginando
    cada lote y CORTANDO pronto si la consulta no aporta nada.

    - Lotes grandes (LOTE_IDES) => menos llamadas, menos overhead.
    - Si los primeros VACIOS_PARA_CORTAR lotes seguidos vienen a 0, se asume
      que la consulta no tiene datos para estos ides y se deja de iterar (evita
      barrer decenas de lotes en balde, p.ej. firmas de contrato inexistentes).
      El colchon protege el caso de datos que empiezan tarde en el rango.
    """
    if not ides:
        return []
    filas: list[dict] = []
    total_lotes = (len(ides) + LOTE_IDES - 1) // LOTE_IDES
    for i in range(0, len(ides), LOTE_IDES):
        lote = list(ides[i:i + LOTE_IDES])
        marcas = ",".join("?" for _ in lote)
        filas.extend(
            sql_read_paginado(
                sql_tpl, lote, filtro_ides=f"AND {columna} IN ({marcas})"
            )
        )
        n = i // LOTE_IDES + 1
        if total_lotes > 1:
            print(f"   lote {n}/{total_lotes}: acumuladas {len(filas)} filas")
    return filas



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


def _sino(valor) -> str:
    try:
        return "SI" if int(valor) != 0 else "NO"
    except (TypeError, ValueError):
        return "NO"


def _v(valor) -> object:
    return "" if valor is None else valor


def _txt(valor) -> str:
    """Texto en una sola linea (para CSV)."""
    return (valor or "").replace("\r", " ").replace("\n", " ").strip()


def escribir_catalogo_estados(filas: list[dict], out: str) -> None:
    """Vuelca la tabla auxiliar de estados (dbo.conest) a CSV."""
    cabecera = ["tip", "estado", "estado_cod", "estado_res", "posicion",
                "clase_predefinida", "estado_portal"]
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cabecera)
        for f in filas:
            w.writerow([
                _v(f.get("tip")), _v(f.get("estado")), _v(f.get("estado_cod")),
                _v(f.get("estado_res")), _v(f.get("posicion")),
                _v(f.get("clase_predefinida")), _v(f.get("estado_portal")),
            ])


def cargar_catalogo_estados() -> list[dict]:
    """Lee dbo.conest para el/los tipo(s) de concepto de los comparativos."""
    filas, _ = sql_read(_SQL_CATALOGO_ESTADOS, [])
    return filas


def listar_estados(out_est: str) -> int:
    """Muestra el catalogo real de estados (conest) + su uso en comparativos."""
    catalogo = cargar_catalogo_estados()
    if not catalogo:
        print("  [AVISO] dbo.conest no devolvio estados para el tipo de los "
              "comparativos. Revisa que exista dbo.com con registros.")
    else:
        print("Catalogo de estados del tipo 'Doc. comparativo de ofertas' "
              "(dbo.conest):\n")
        print(f"  {'est':>5}  {'codigo':<12}  descripcion")
        print("  " + "-" * 60)
        for f in catalogo:
            print(f"  {str(_v(f.get('estado'))):>5}  "
                  f"{str(_v(f.get('estado_cod'))):<12}  "
                  f"{_v(f.get('estado_res'))}")
        escribir_catalogo_estados(catalogo, out_est)
        print(f"\n  -> catalogo volcado a {out_est}")

    print("\nUso real en los comparativos (dbo.com):\n")
    uso, _ = sql_read(_SQL_ESTADOS_USO, [])
    if not uso:
        print("  No hay comparativos en dbo.com.")
        return 0
    print(f"  {'est':>5}  {'codigo':<12}  {'nº com':>7}  {'desde':>12}  "
          f"{'hasta':>12}  descripcion")
    print("  " + "-" * 80)
    for f in uso:
        print(f"  {str(_v(f.get('estado'))):>5}  "
              f"{str(_v(f.get('estado_cod'))):<12}  "
              f"{str(_v(f.get('num_comparativos'))):>7}  "
              f"{_fec(f.get('fec_min')):>12}  {_fec(f.get('fec_max')):>12}  "
              f"{_v(f.get('estado_res'))}")
    print("\n  Relanza filtrando, p.ej.:")
    print("    --estado-cod APROBADO")
    print("    --estado-cod APR,APCOM,APROBADO")
    print("    --estado 110")
    return 0


def _num(valor) -> float:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _sin_tildes(texto: str) -> str:
    """Mayusculas y sin acentos, para matching de nombres."""
    import unicodedata
    t = unicodedata.normalize("NFD", (texto or "").upper())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


# Proveedores FICTICIOS del comparativo: guardan los importes de referencia
# como ofertas (dco). Matching por 'contiene', sin tildes ni mayusculas.
_FICTICIOS = [
    ("OBJETIVO", "importe_objetivo"),
    ("ABC", "importe_abc"),
    ("OFICINA TECNICA", "importe_ot"),
    ("PLANIFICACION", "importe_planificado"),
]


def importes_ficticios(proveedores: list[dict]) -> dict:
    """{comide: {importe_objetivo/abc/ot/planificado}} desde las ofertas de
    los proveedores ficticios. Importe = dco.totbas (fallback dco.tot); si un
    ficticio tiene varias ofertas, gana la de fecha mas reciente."""
    res: dict = {}
    mejor_fec: dict = {}
    for f in proveedores:
        nombre = _sin_tildes(f.get("proveedor_nombre") or "")
        clave = next((k for pat, k in _FICTICIOS if pat in nombre), None)
        if clave is None:
            continue
        cid = f.get("comparativo_ide")
        imp = f.get("oferta_base_sin_iva")
        if imp is None:
            imp = f.get("oferta_total")
        fec = f.get("oferta_fecha") or 0
        if fec >= mejor_fec.get((cid, clave), -1):
            mejor_fec[(cid, clave)] = fec
            res.setdefault(cid, {})[clave] = imp
    return res


def _cols_contrato(contratos: list[dict]) -> list:
    """Devuelve el bloque de columnas de contrato para un comparativo.

    Agrega los N contratos adjudicados (num, codigos, sumas) y detalla el
    contrato PRINCIPAL = el de mayor base imponible (totbas). Si el comparativo
    no tiene contrato adjudicado, devuelve el bloque vacio.
    """
    # Deduplicar por contrato_ide: un mismo contrato puede venir por las dos
    # vias (ctr.comide y comlin.ctride) y no debe contarse ni sumarse doble.
    # Excluir contratos dados de baja del agregado del comparativo: un
    # contrato anulado no debe contar como "comparativo contratado" (falso
    # negativo en el KPI). El CSV de detalle SI los conserva, con su
    # contrato_fecha_baja visible. En Power Query hay que filtrar igual la
    # tabla de contratos o los totales no cuadraran con num_contratos.
    unicos: dict[object, dict] = {}
    vias: dict[object, set] = {}
    for c in contratos:
        if _num(c.get("contrato_fecha_baja")) > 0:
            continue
        cid = c.get("contrato_ide")
        unicos.setdefault(cid, c)
        vias.setdefault(cid, set()).add(c.get("via"))

    if not unicos:
        return [0, ""] + [""] * 27

    lista = list(unicos.values())
    num = len(lista)
    cods = " | ".join(sorted(str(c.get("contrato_cod") or "") for c in lista))
    suma_bas = round(sum(_num(c.get("base_sin_iva")) for c in lista), 2)
    suma_tot = round(sum(_num(c.get("total_sin_retencion")) for c in lista), 2)

    # Principal: mayor base imponible (desempate por contrato_ide)
    pr = max(lista, key=lambda c: (_num(c.get("base_sin_iva")),
                                   c.get("contrato_ide") or 0))
    via_pr = ",".join(sorted(v for v in vias.get(pr.get("contrato_ide"), set()) if v))

    return [
        num, cods, suma_bas, suma_tot,
        _v(pr.get("contrato_cod")), _v(pr.get("contrato_res")),
        _v(pr.get("contrato_estado_cod")), _v(pr.get("contrato_estado_res")),
        _fec(pr.get("contrato_fecha_doc")), _fec(pr.get("contrato_fecha_alta")),
        _fec(pr.get("contrato_fecha_entrega")), _fec(pr.get("contrato_fecha_limite")),
        _v(pr.get("proveedor_cod")), _v(pr.get("proveedor_nombre")),
        _v(pr.get("proveedor_cif")), _v(pr.get("contrato_tipo")),
        _v(pr.get("contrato_obra_cod")), _v(pr.get("forma_pago")),
        _v(pr.get("base_sin_iva")), _v(pr.get("cuota_iva")),
        _v(pr.get("total_sin_retencion")), _v(pr.get("total_con_retencion")),
        _v(pr.get("importe_a_pagar")),
        _fec(pr.get("fecha_ultima_firma")), _v(pr.get("importe_facturado")),
        _sino(pr.get("esta_pedido")), _sino(pr.get("esta_servido")),
        _sino(pr.get("esta_facturado")), via_pr,
    ]


def escribir_comparativos(filas: list[dict], out: str,
                          ctr_por_com: dict | None = None,
                          firmas_com: dict | None = None,
                          fact_com: dict | None = None,
                          imp_com: dict | None = None,
                          fict: dict | None = None,
                          pend_com: dict | None = None) -> None:
    cabecera = [
        "comparativo_ide", "comparativo_cod", "comparativo_res",
        "estado", "estado_cod", "estado_res",
        "anio", "fecha_alta", "fecha_baja", "fecha_contratacion",
        "fecha_entrega_prevista", "fecha_limite", "fec_ini_recepcion",
        "fec_fin_recepcion", "es_subasta", "obra_cod", "obra_nombre",
        "empleado_cod", "empleado_nombre", "naturaleza", "tipo_contrato",
        "presupuesto_cod", "comparativo_origen_cod", "observaciones",
        # --- Firmas e importes propios del comparativo ---
        "fecha_ultima_firma", "num_firmas",
        "importe_comparativo",
        "importe_objetivo", "importe_abc", "importe_ot", "importe_planificado",
        "importe_facturado_com", "num_facturas_com",
        "firmas_pendientes", "firma_pendiente_desde", "rol_pendiente",
        # --- Bloque CONTRATO adjudicado (agregado del comparativo) ---
        "num_contratos", "contratos_cods",
        "contrato_base_sin_iva_total", "contrato_total_doc_total",
        # --- Contrato PRINCIPAL (el de mayor base imponible) ---
        "ctr_cod", "ctr_res", "ctr_estado_cod", "ctr_estado_res",
        "ctr_fecha_doc", "ctr_fecha_alta", "ctr_fecha_entrega", "ctr_fecha_limite",
        "ctr_proveedor_cod", "ctr_proveedor_nombre", "ctr_proveedor_cif",
        "ctr_tipo", "ctr_obra_cod", "ctr_forma_pago",
        "ctr_base_sin_iva", "ctr_cuota_iva", "ctr_total_sin_retencion",
        "ctr_total_con_retencion", "ctr_importe_a_pagar",
        "ctr_fecha_ultima_firma", "ctr_importe_facturado",
        "ctr_pedido", "ctr_servido", "ctr_facturado", "ctr_via",
    ]
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cabecera)
        for f in filas:
            cid = f.get("comparativo_ide")
            w.writerow([
                _v(f.get("comparativo_ide")), _v(f.get("comparativo_cod")),
                _v(f.get("comparativo_res")), _v(f.get("estado")),
                _v(f.get("estado_cod")), _v(f.get("estado_res")),
                _v(f.get("anio")), _fec(f.get("fecha_alta")),
                _fec(f.get("fecha_baja")), _fec(f.get("fecha_contratacion")),
                _fec(f.get("fecha_entrega_prevista")), _fec(f.get("fecha_limite")),
                _fec(f.get("fec_ini_recepcion")), _fec(f.get("fec_fin_recepcion")),
                _sino(f.get("es_subasta")),
                _v(f.get("obra_cod")), _v(f.get("obra_nombre")),
                _v(f.get("empleado_cod")), _v(f.get("empleado_nombre")),
                _v(f.get("naturaleza")), _v(f.get("tipo_contrato")),
                _v(f.get("presupuesto_cod")), _v(f.get("comparativo_origen_cod")),
                _txt(f.get("observaciones")),
                _fec(((firmas_com or {}).get(cid) or {}).get("fecha_ultima_firma")),
                _v(((firmas_com or {}).get(cid) or {}).get("num_firmas")),
                _v(((imp_com or {}).get(cid) or {}).get("importe_comparativo")),
                _v(((fict or {}).get(cid) or {}).get("importe_objetivo")),
                _v(((fict or {}).get(cid) or {}).get("importe_abc")),
                _v(((fict or {}).get(cid) or {}).get("importe_ot")),
                _v(((fict or {}).get(cid) or {}).get("importe_planificado")),
                _v(((fact_com or {}).get(cid) or {}).get("facturado_base")),
                _v(((fact_com or {}).get(cid) or {}).get("num_facturas")),
                _v(((pend_com or {}).get(cid) or {}).get("firmas_pendientes")),
                _fec(((pend_com or {}).get(cid) or {}).get("pendiente_desde")),
                _v(((pend_com or {}).get(cid) or {}).get("rol_pendiente")),
            ] + _cols_contrato(
                (ctr_por_com or {}).get(f.get("comparativo_ide"), [])
            ))


def escribir_contratos(filas: list[dict], out: str) -> None:
    cabecera = [
        "comparativo_ide", "via", "contrato_ide", "contrato_cod", "contrato_res",
        "contrato_estado", "contrato_estado_cod", "contrato_estado_res",
        "contrato_fecha_alta", "contrato_fecha_baja", "contrato_fecha_doc",
        "contrato_fecha_entrega", "contrato_fecha_limite", "contrato_fecha_pago",
        "contrato_fecha_factura",
        "contrato_obra_cod", "contrato_obra_nombre",
        "proveedor_cod", "proveedor_nombre", "proveedor_cif",
        "proveedor_referencia", "contrato_tipo",
        "contrato_empleado_cod", "contrato_empleado_nombre",
        "centro_coste_cod", "centro_coste_nombre",
        "forma_pago", "cond_pago", "iva_nombre", "iva_porcentaje",
        "importe_bruto", "importe_descuentos", "importe_recargos",
        "base_sin_iva", "cuota_iva", "total_sin_retencion",
        "total_con_retencion", "importe_a_pagar",
        "esta_pedido", "esta_servido", "esta_facturado",
        "es_factura_periodica",
        "fecha_ultima_firma", "num_firmas", "importe_facturado",
        "contratado_lineas",
        "contrato_observaciones",
    ]
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cabecera)
        for f in filas:
            w.writerow([
                _v(f.get("comparativo_ide")), _v(f.get("via")),
                _v(f.get("contrato_ide")), _v(f.get("contrato_cod")),
                _v(f.get("contrato_res")), _v(f.get("contrato_estado")),
                _v(f.get("contrato_estado_cod")), _v(f.get("contrato_estado_res")),
                _fec(f.get("contrato_fecha_alta")), _fec(f.get("contrato_fecha_baja")),
                _fec(f.get("contrato_fecha_doc")), _fec(f.get("contrato_fecha_entrega")),
                _fec(f.get("contrato_fecha_limite")), _fec(f.get("contrato_fecha_pago")),
                _fec(f.get("contrato_fecha_factura")),
                _v(f.get("contrato_obra_cod")), _v(f.get("contrato_obra_nombre")),
                _v(f.get("proveedor_cod")), _v(f.get("proveedor_nombre")),
                _v(f.get("proveedor_cif")), _v(f.get("proveedor_referencia")),
                _v(f.get("contrato_tipo")),
                _v(f.get("contrato_empleado_cod")),
                _v(f.get("contrato_empleado_nombre")),
                _v(f.get("centro_coste_cod")), _v(f.get("centro_coste_nombre")),
                _v(f.get("forma_pago")), _txt(f.get("cond_pago")),
                _v(f.get("iva_nombre")), _v(f.get("iva_porcentaje")),
                _v(f.get("importe_bruto")), _v(f.get("importe_descuentos")),
                _v(f.get("importe_recargos")), _v(f.get("base_sin_iva")),
                _v(f.get("cuota_iva")), _v(f.get("total_sin_retencion")),
                _v(f.get("total_con_retencion")), _v(f.get("importe_a_pagar")),
                _sino(f.get("esta_pedido")), _sino(f.get("esta_servido")),
                _sino(f.get("esta_facturado")), _sino(f.get("es_factura_periodica")),
                _fec(f.get("fecha_ultima_firma")), _v(f.get("num_firmas")),
                _v(f.get("importe_facturado")), _v(f.get("contratado_lineas")),
                _txt(f.get("contrato_observaciones")),
            ])


def escribir_proveedores(filas: list[dict], out: str) -> None:
    cabecera = [
        "comparativo_ide", "posicion", "short_list", "proveedor_cod",
        "proveedor_nombre", "proveedor_cif", "oferta_cod", "oferta_res",
        "oferta_estado", "oferta_fecha", "oferta_base_sin_iva", "oferta_total",
    ]
    with open(out, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";")
        w.writerow(cabecera)
        for f in filas:
            w.writerow([
                _v(f.get("comparativo_ide")), _v(f.get("posicion")),
                _sino(f.get("short_list")),
                _v(f.get("proveedor_cod")), _v(f.get("proveedor_nombre")),
                _v(f.get("proveedor_cif")), _v(f.get("oferta_cod")),
                _v(f.get("oferta_res")), _v(f.get("oferta_estado")),
                _fec(f.get("oferta_fecha")), _v(f.get("oferta_base_sin_iva")),
                _v(f.get("oferta_total")),
            ])


def main() -> int:
    global PAGINA, LOTE_IDES
    ap = argparse.ArgumentParser(
        description="Comparativos aprobados + contratos, obra y proveedor (a CSV).")
    ap.add_argument("--key", help="Function key (si no, del .env/entorno).")
    ap.add_argument("--base-url", help="URL base de sigrid-api (si no, del .env).")
    ap.add_argument("--db", help="Base de datos (si no, del .env; por defecto ruesma).")
    ap.add_argument("--listar-estados", action="store_true",
                    help="Lista el catalogo de estados (dbo.conest) y su uso, y sale.")
    ap.add_argument("--estado", type=int, default=ESTADO_APROBADO,
                    help="Valor NUMERICO de con.est (p.ej. 110). "
                         "Alternativa a --estado-cod.")
    ap.add_argument("--estado-cod", default=ESTADO_APROBADO_COD,
                    help="Codigo(s) de estado de dbo.conest, separados por coma "
                         "(p.ej. APROBADO o APR,APCOM,APROBADO). Recomendado. "
                         "Si se omiten ambos, NO se filtra (saca todos).")
    ap.add_argument("--lote", type=int, default=LOTE_IDES,
                    help=f"Ids por lote del IN(...). Def. {LOTE_IDES}, max ~2000 "
                         "(limite de parametros de SQL Server).")
    ap.add_argument("--pagina", type=int, default=PAGINA,
                    help=f"Filas por pagina (OFFSET/FETCH). Def. {PAGINA}. "
                         "Debe ser <= al tope de sigrid-api (MAX_ROWS).")
    ap.add_argument("--out-est", default=CSV_EST,
                    help="CSV del catalogo auxiliar de estados (dbo.conest).")
    ap.add_argument("--desde-anio", type=int, default=ANIO_MIN_DEFAULT,
                    help="Ano minimo de alta del comparativo (0 = todos).")
    ap.add_argument("--incluir-bajas", action="store_true",
                    help="Incluye comparativos dados de baja (con.fecbaj > 0).")
    ap.add_argument("--out-com", default=CSV_COM, help="CSV de comparativos.")
    ap.add_argument("--out-ctr", default=CSV_CTR, help="CSV de contratos.")
    ap.add_argument("--out-prv", default=CSV_PRV, help="CSV de proveedores.")
    args = ap.parse_args()

    cargar_config(args)
    PAGINA = max(1, min(args.pagina, MAX_ROWS))
    LOTE_IDES = max(1, min(args.lote, 2000))
    print(f"  base_url={BASE_URL}  database={DATABASE}  timeout={TIMEOUT}s "
          f"pagina={PAGINA}")

    if args.listar_estados:
        return listar_estados(args.out_est)

    # --- 0) Catalogo auxiliar de estados (dbo.conest) --- #
    print("0) Catalogo de estados (dbo.conest)...")
    catalogo = cargar_catalogo_estados()
    escribir_catalogo_estados(catalogo, args.out_est)
    print(f"  estados en catalogo: {len(catalogo)} -> {args.out_est}")
    # cod (mayus) -> lista de est numericos
    cod2est: dict[str, list[int]] = defaultdict(list)
    for e in catalogo:
        cod = (e.get("estado_cod") or "").strip().upper()
        try:
            num = int(e.get("estado"))
        except (TypeError, ValueError):
            continue
        if cod:
            cod2est[cod].append(num)

    # --- 1) Comparativos --- #
    params: list = []
    filtro_estado = ""

    estados_num: list[int] = []
    if args.estado_cod:
        pedidos = [c.strip().upper() for c in args.estado_cod.split(",") if c.strip()]
        no_encontrados = []
        for c in pedidos:
            if cod2est.get(c):
                estados_num.extend(cod2est[c])
            else:
                no_encontrados.append(c)
        if no_encontrados:
            print(f"  [ERROR] Codigo(s) de estado no encontrados en dbo.conest: "
                  f"{', '.join(no_encontrados)}")
            print("  Lanza --listar-estados para ver los codigos validos.")
            return 1
    if args.estado is not None:
        estados_num.append(args.estado)

    estados_num = sorted(set(estados_num))
    if estados_num:
        marcas = ", ".join("?" for _ in estados_num)
        filtro_estado = f"AND c.est IN ({marcas})"
        params.extend(estados_num)
        print(f"1) Comparativos con estado IN {estados_num}"
              f"{' (' + args.estado_cod + ')' if args.estado_cod else ''}...")
    else:
        print("1) Comparativos (SIN filtro de estado: se sacan TODOS).")
        print("   Usa --listar-estados para ver los codigos y filtrar.")

    filtro_anio = ""
    if args.desde_anio:
        filtro_anio = "AND (c.fec / 10000) >= ?"
        params.append(args.desde_anio)

    if not args.incluir_bajas:
        filtro_anio += " AND (c.fecbaj IS NULL OR c.fecbaj = 0)"

    comparativos = sql_read_paginado(
        _SQL_COMPARATIVOS, params,
        filtro_estado=filtro_estado, filtro_anio=filtro_anio,
    )
    print(f"  comparativos: {len(comparativos)}")
    if not comparativos:
        print("[OK] Sin comparativos para el filtro indicado.")
        return 0

    ides = {f.get("comparativo_ide") for f in comparativos}

    # --- 2) Contratos (se traen todos y se filtran en cliente por los ides) --- #
    print("2) Contratos adjudicados (ctr.comide + comlin.ctride)...")
    lista_ides = sorted(i for i in ides if i is not None)
    contratos = sql_read_por_ides(
        _SQL_CONTRATOS, lista_ides, "v.comparativo_ide"
    )
    por_com: dict[object, set] = defaultdict(set)
    ctr_por_com: dict[object, list] = defaultdict(list)
    for f in contratos:
        por_com[f.get("comparativo_ide")].add(f.get("contrato_ide"))
        ctr_por_com[f.get("comparativo_ide")].append(f)
    con_contrato = sum(1 for i in ides if por_com.get(i))
    print(f"  filas contrato-comparativo: {len(contratos)}  "
          f"comparativos con contrato: {con_contrato}/{len(ides)}")

    # --- 2b) Agregados: firmas, facturado, objetivo/planificado --- #
    print("2b) Ultima firma, facturado y objetivo/planificado...")
    ides_ctr = sorted({f.get("contrato_ide") for f in contratos
                       if f.get("contrato_ide") is not None})

    firmas_com = {f["conide"]: f for f in sql_read_agregado_por_ides(
        _SQL_ULTIMA_FIRMA, lista_ides, "f.conide")}
    firmas_ctr = {f["conide"]: f for f in sql_read_agregado_por_ides(
        _SQL_ULTIMA_FIRMA, ides_ctr, "f.conide")} if ides_ctr else {}
    fact_com = {f["comide"]: f for f in sql_read_agregado_por_ides(
        _SQL_FACTURADO_COM, lista_ides, "d.comide")}
    fact_ctr = {f["ctride"]: f for f in sql_read_agregado_por_ides(
        _SQL_FACTURADO_CTR, ides_ctr, "p.docide")} if ides_ctr else {}
    imp_com = {f["comide"]: f for f in sql_read_agregado_por_ides(
        _SQL_IMPORTE_COMPARATIVO, lista_ides, "l.comide")}
    pend_com = {f["conide"]: f for f in sql_read_agregado_por_ides(
        _SQL_FIRMA_PENDIENTE, lista_ides, "f.conide")}
    print(f"  firmas: com={len(firmas_com)} ctr={len(firmas_ctr)}  "
          f"facturado: com={len(fact_com)} ctr={len(fact_ctr)}  "
          f"importe_comparativo: {len(imp_com)}")

    # Enriquecer las filas de contrato (detalle + bloque principal)
    for f in contratos:
        cid = f.get("contrato_ide")
        f["fecha_ultima_firma"] = (firmas_ctr.get(cid) or {}).get(
            "fecha_ultima_firma")
        f["num_firmas"] = (firmas_ctr.get(cid) or {}).get("num_firmas")
        f["importe_facturado"] = (fact_ctr.get(cid) or {}).get(
            "facturado_importe")
        f["contratado_lineas"] = (fact_ctr.get(cid) or {}).get(
            "contratado_lineas")

    # --- 3) Proveedores del comparativo --- #
    print("3) Proveedores invitados (comprv) + ofertas (dco)...")
    proveedores = sql_read_por_ides(
        _SQL_PROVEEDORES, lista_ides, "p.comide"
    )
    fict = importes_ficticios(proveedores)
    print(f"  comparativos con importes ficticios: {len(fict)}")
    print(f"  filas proveedor-comparativo: {len(proveedores)}")

    # --- 4) CSVs --- #
    print(f"4) Escribiendo CSVs...")
    escribir_comparativos(comparativos, args.out_com, ctr_por_com,
                          firmas_com, fact_com, imp_com, fict, pend_com)
    escribir_contratos(contratos, args.out_ctr)
    escribir_proveedores(proveedores, args.out_prv)
    print(f"   -> {args.out_est}")
    print(f"   -> {args.out_com}")
    print(f"   -> {args.out_ctr}")
    print(f"   -> {args.out_prv}")

    print(f"[OK] comparativos={len(comparativos)} contratos={len(contratos)} "
          f"proveedores={len(proveedores)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())