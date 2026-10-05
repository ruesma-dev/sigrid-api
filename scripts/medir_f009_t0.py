# scripts/medir_f009_t0.py
"""
F-009 · T0: mediciones M1-M18 de la spec, SOLO LECTURA.

Lanza cada medición como SELECT por `POST /api/sql/read` contra la API
desplegada y escribe, en español, la conclusión que necesita la spec
(`specs/F-009-alta-albaran-compra/`, puntos [Mn]; M16-M18 y las ampliaciones de M11
y M14, de `progress/spec_F-009.md` §T0 v5; M9 y M11 por ventanas cortas, M14b, M16b y
M17b, de la segunda pasada T0a-bis). No escribe nada en Sigrid, no llama a ningún
endpoint de dominio (ni en dry-run) y no se conecta por SQL.

Configuración (la de los demás scripts de este repositorio): variables de
entorno o, si no están, el `.env` de la raíz del repositorio:
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY
Se cargan en el proceso y NUNCA se imprimen.

Uso:
    python -m scripts.medir_f009_t0                 # M1-M18
    python -m scripts.medir_f009_t0 --solo M5       # una (o varias: --solo M5 M6)
    python -m scripts.medir_f009_t0 --solo M3 M7 M9 M11 M13 M14 M16 M17 M18   # repetición T0b
    python -m scripts.medir_f009_t0 --solo M9 M11 M14 M16 M17                  # segunda pasada (T0a-bis)
    python -m scripts.medir_f009_t0 --salida C:\\ruta\\fuera\\del\\repo.txt

Resultado: por pantalla y en un fichero de %TEMP% (`f009_t0_<fecha>.txt`), que
es lo que se pega de vuelta. El fichero nunca se escribe dentro del repositorio.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

RAIZ_REPO = Path(__file__).resolve().parents[1]
DATABASE = "ruesma"
TIMEOUT_NORMAL_S = 120
TIMEOUT_PESADO_S = 200          # el balanceador corta a 230 s
MUESTRA_DEVOLUCIONES = 20
MUESTRA_FECHA_ATRASADA = 3
COD_ALBARAN_API = "AC26/15951"  # creado por la API en junio (desde contrato)
PRODUCTOS_GENERICOS = ("MA9999", "SM9999", "SB9999", "QA9999")
LISTA_BLANCA_GENERICOS = ("MA9999", "QA9999")   # spec v6: M11 mide y concluye cada uno por separado
LISTA_DE_RESETEO = (
    "fec", "pla", "refent", "cod2", "dncide", "dncproide", "anades", "serdes",
    "parcandes", "med", "canmed", "item", "pac", "desesp", "edilin", "texcom",
    "anexo", "fecimp", "garfec", "mesrevpre", "ejerevpre", "taride", "prepma",
)
# Columnas que por construcción cambian de un documento a otro: no se señalan en M14.
PROPIAS_DEL_DOCUMENTO = {
    "ide", "docide", "cod", "res", "fec", "tiemod", "proide", "pos", "pre", "can", "tar",
    "tot", "ivacuo", "tex", "entide", "entcod", "entres", "entcif", "entref", "fecdoc",
    "hor", "obride", "ctride", "almide", "cenide", "caaide", "paride", "linoriide",
    "docoriide", "docoricod", "canoriori", "imporiori", "impbru", "impnet", "totbas",
    "totiva", "totdoc", "totpag", "totbasdiv", "totivadiv", "totdocdiv", "totdiv",
    "totpagdiv", "unimed", "cueide", "ivaide", "natide", "empide", "ano", "mes",
}


def marcadores(n: int) -> str:
    """`?, ?, ?` para una lista IN de n valores (n >= 1)."""
    if n < 1:
        raise ValueError("Una lista IN necesita al menos un valor.")
    return ", ".join("?" for _ in range(n))


# Fragmentos fijos (nunca valores de fuera) que se repiten en el SELECT y en el GROUP BY.
_TIPO_LINEA = "CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 'vinculada' ELSE 'sin_vincular' END"
_PARTIDA_DISTINTA = (
    "CASE WHEN ISNULL(d.docoritip, 0) = 44 AND ISNULL(d.paride, 0) <> ISNULL(t.paride, 0) THEN 1 ELSE 0 END"
)
_TIPO_PARTIDA = "CASE WHEN ISNULL(d.paride, 0) > 0 THEN 'con_partida' ELSE 'almacen' END"
_CABECERA = "CASE WHEN ISNULL(a.ctride, 0) > 0 THEN 'con_contrato' ELSE 'sin_contrato' END"
_VENTANA_LOG = "(SELECT MAX(ide) - 1000000 FROM dbo.log)"   # la de M13: log tiene millones de filas
_CON_SIN_PARTIDA = "CASE WHEN ISNULL(d.paride, 0) > 0 THEN 'con_partida' ELSE 'sin_partida' END"
_GENERICOS = marcadores(len(PRODUCTOS_GENERICOS))
# T0a-bis, M9 y M11: ventana `c.fec >= ? AND c.fec <= ?` (parámetros) y mov por `doclin`.
_VENTANA_PARAM = "c.tip = 14 AND c.fec >= ? AND c.fec <= ?"
_M9_VENTANA = f"WHERE {_VENTANA_PARAM}"
_M9_LINEAS_Y_MOV = (
    "JOIN dbo.dcapro d ON d.docide = c.ide LEFT JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide"
)
_CON_MOV = (
    "COUNT(DISTINCT d.ide) AS lineas, COUNT(DISTINCT CASE WHEN m.ide IS NULL THEN NULL ELSE d.ide END) AS con_mov, "
    "COUNT(m.ide) AS movs"
)
_TIPMOV, _TIPINV = "ISNULL(r.tipmov, -1)", "ISNULL(r.tipinv, -1)"
_M11_LINEAS = "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide"
# T0a-bis, M16b: grupo de producto (cada genérico de la empresa EMPRESA_GENERICOS por separado y «resto»).
# Lleva `?`: se calcula en una tabla derivada y se agrupa por su alias (repetir la expresión con otros
# `?` en el GROUP BY no lo aceptaría SQL Server).
_GRUPO_GENERICO = f"CASE WHEN kp.emp = ? AND kp.cod IN ({_GENERICOS}) THEN kp.cod ELSE 'resto' END"
_CAA_INFORMADA = "ISNULL(d.caaide, 0) <> 0"
_SIN_VINCULAR_DESDE_2025 = "WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.docoritip, 0) <> 44"
_M16B_DESDE = (
    "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide LEFT JOIN dbo.con kp ON kp.ide = d.proide "
    "LEFT JOIN dbo.pro r ON r.ide = d.proide LEFT JOIN dbo.caa k ON k.ide = d.caaide"
)
# Código de la caa (kc), de la cuenta financiera (cf, `dcapro.cueide` → `cua`), de la obra (oc) y del
# centro (ec): `caa`, `cua`, `obr` y `cen` son «Propiedades de con», así que su código está en `con.cod`.
_M16B_CODIGOS = (
    "LEFT JOIN dbo.auxpronat nt ON nt.ide = r.natide LEFT JOIN dbo.con kc ON kc.ide = d.caaide "
    "LEFT JOIN dbo.con cf ON cf.ide = d.cueide LEFT JOIN dbo.con oc ON oc.ide = d.obride "
    "LEFT JOIN dbo.con ec ON ec.ide = d.cenide"
)
_CAA_ES_CAAGASCOD = "ISNULL(nt.caagascod, '') <> '' AND kc.cod = nt.caagascod"
_CAA_EMPIEZA_POR_CUENTA = "ISNULL(cf.cod, '') <> '' AND LEFT(kc.cod, LEN(cf.cod)) = cf.cod"
_CAA_DEL_CENTRO = "k.cenide = d.cenide"
# T0a-bis, M17b: altas (ope 1) de albarán en la ventana de log, por (emp, cod), y el caso de cada ope 2.
_ALTAS_LOG = (
    "(SELECT emp, cod, MIN(ide) AS pri_alta, MAX(ide) AS ult_alta FROM dbo.log "
    f"WHERE ide > {_VENTANA_LOG} AND tab = 'con' AND tip = 14 AND ope = 1 GROUP BY emp, cod)"
)
_CASO_M17B = (
    "CASE WHEN c.ide IS NULL THEN 'no_existe' WHEN p.ult_alta > l.ide THEN 'existe_con_alta_posterior' "
    "ELSE 'existe_sin_alta_posterior' END"
)
_LOG_ALBARANES = f"WHERE l.ide > {_VENTANA_LOG} AND l.tab = 'con' AND l.tip = 14"

# M14 ampliada (spec v5 §T0, H11): columna de dcapro y condición de «tiene valor», en el orden de la
# spec. `med` es binario y `tex`/`texcom` texto ilimitado (DATALENGTH); `cod2`/`pac`/`refent`, texto.
COLUMNAS_SV: tuple[tuple[str, str], ...] = (
    ("med", "DATALENGTH(d.med) > 0"),
    *((col, f"ISNULL(d.{col}, 0) <> 0") for col in (
        "canmed", "parcandes", "anades", "serdes", "fecimp", "item", "anexo", "taride", "fec", "pla")),
    ("tex", "DATALENGTH(d.tex) > 0"),
    ("texcom", "DATALENGTH(d.texcom) > 0"),
    *((col, f"ISNULL(d.{col}, '') <> ''") for col in ("cod2", "pac", "refent")),
    # El resto de LISTA_DE_RESETEO (ajuste del líder: T0 se ejecuta una sola vez, H28, y M14 debe
    # poder confirmar la lista entera). `desesp` es texto ilimitado; las demás, enteros o reales.
    ("desesp", "DATALENGTH(d.desesp) > 0"),
    *((col, f"ISNULL(d.{col}, 0) <> 0") for col in (
        "dncide", "dncproide", "edilin", "garfec", "mesrevpre", "ejerevpre", "prepma")),
)
UMBRAL_CASI_TODO = 0.95      # «≥ 95 %» y «≈» de la spec v5 §T0 (no «dominante»: ver la siguiente)
UMBRAL_DOMINANTE = 0.5       # M16 «dominante»: ≥ 50 % de las líneas y no menos que la alternativa
UMBRAL_CASI_NADA = 0.001     # «≤ 0,1 %» de M18 (y «≈ 0» de M14 ampliada)
UMBRAL_BORRA = 0.05          # M17: «con_existe ≈ 0»
EMPRESA_ARRASTRE = 1         # M14 ampliada: el MA9999 de la empresa 1
UMBRAL_CASI_NINGUNA = 0.05   # M9: «≈ 0» (simétrico de UMBRAL_CASI_TODO)

# T0a-bis: la ejecución del 2026-10-05 perdió M9 y M11 enteras por ReadTimeout (el balanceador corta a
# 230 s). Ventanas cortas y cerradas (el último mes completo: menos filas y menos bloqueos de las que el
# escritorio está editando hoy), guiadas desde `con` (tip, fec) y con `mov` por su índice `doclin`.
VENTANA_M9 = (20260901, 20260930)
VENTANA_M11 = (20260701, 20260930)
DESDE_M14B, DESDE_LAG_M14B = 20260901, 20260101   # M14b: albaranes desde 2026-09, el anterior desde 2026
EMPRESA_GENERICOS = 1        # M16b: los genéricos de la empresa 1, cada uno por separado
REINTENTOS_INTERBLOQUEO = 2  # error 1205 de SQL Server (transitorio): se reintenta con espera creciente
ESPERA_INTERBLOQUEO_S = 5


# ---------------------------------------------------------------------------
# SQL: TODAS las sentencias del script, una por constante. Solo SELECT/WITH.
# Las que llevan `{in}` se completan con `marcadores(n)`.
# ---------------------------------------------------------------------------
SQL: dict[str, str] = {
    "M1_total": (
        "SELECT COUNT(*) AS total, SUM(CASE WHEN ISNULL(synckey, '') <> '' THEN 1 ELSE 0 END) "
        "AS con_synckey FROM dbo.dca"
    ),
    "M1_prefijos": (
        "SELECT TOP 20 LEFT(synckey, 6) AS prefijo, COUNT(*) AS n FROM dbo.dca "
        "WHERE ISNULL(synckey, '') <> '' GROUP BY LEFT(synckey, 6) ORDER BY n DESC"
    ),
    "M1_prefijo_alb": "SELECT COUNT(*) AS n FROM dbo.dca WHERE synckey LIKE ?",
    "M1_busqueda": (
        "SELECT c.ide, c.cod FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide "
        "WHERE c.tip = ? AND d.synckey = ?"
    ),
    "M2_est_emp": (
        "SELECT c.emp, c.est, COUNT(*) AS n FROM dbo.con c WHERE c.tip = 14 AND c.fec >= 20250101 "
        "GROUP BY c.emp, c.est ORDER BY n DESC"
    ),
    "M2_est_sin_facturar": (
        "SELECT c.est, COUNT(*) AS n FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
        "WHERE c.tip = 14 AND c.fec >= 20260901 AND ISNULL(d.estfac, 0) = 0 GROUP BY c.est ORDER BY n DESC"
    ),
    "M2_conest": "SELECT tip, est, cod, res FROM dbo.conest WHERE tip = 14 ORDER BY est",
    "M2_sercon": "SELECT ide, tip, cod, emp, estini, act FROM dbo.sercon WHERE tip = 14",
    "M2_mov_emp": (
        "SELECT emp, COUNT(*) AS n FROM dbo.mov WHERE doctip = 14 AND fec >= 20250101 "
        "GROUP BY emp ORDER BY n DESC"
    ),
    "M2_indices_con": (
        "SELECT i.name AS indice, i.is_unique AS unico, c.name AS columna, ic.key_ordinal AS orden "
        "FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id = i.object_id "
        "AND ic.index_id = i.index_id JOIN sys.columns c ON c.object_id = ic.object_id "
        "AND c.column_id = ic.column_id WHERE i.object_id = OBJECT_ID('dbo.con') "
        "ORDER BY i.name, ic.key_ordinal"
    ),
    "M3_partidas_usadas": (
        "SELECT p.tip, p.tipdes, p.tipvis, COUNT(*) AS n FROM dbo.dcapro d "
        "JOIN dbo.obrparpar p ON p.ide = d.paride JOIN dbo.con c ON c.ide = d.docide "
        "WHERE c.tip = 14 AND c.fec >= 20250101 GROUP BY p.tip, p.tipdes, p.tipvis ORDER BY n DESC"
    ),
    "M3_tipos": "SELECT tip, COUNT(*) AS n FROM dbo.obrparpar GROUP BY tip ORDER BY tip",
    "M3_repetidos": (
        "SELECT COUNT(*) AS repetidos FROM (SELECT obride, cod FROM dbo.obrparpar "
        "GROUP BY obride, cod HAVING COUNT(*) > 1) x"
    ),
    # Lo mismo solo entre las partidas imputables (tip 1, activas, de coste o ambas).
    "M3_repetidos_imputables": (
        "SELECT COUNT(*) AS repetidos, SUM(x.n) AS filas FROM (SELECT obride, cod, COUNT(*) AS n "
        "FROM dbo.obrparpar WHERE tip = 1 AND tipdes = 0 AND tipvis IN (0, 1) "
        "GROUP BY obride, cod HAVING COUNT(*) > 1) x"
    ),
    "M4_vinculadas": (
        "SELECT COUNT(*) AS n, SUM(CASE WHEN ISNULL(d.paride, 0) <> ISNULL(p.paride, 0) THEN 1 ELSE 0 END) "
        "AS partida_distinta, SUM(CASE WHEN ABS(d.pre - p.pre) > 0.0001 THEN 1 ELSE 0 END) AS precio_distinto "
        "FROM dbo.dcapro d JOIN dbo.ctrpro p ON p.ide = d.linoriide JOIN dbo.con c ON c.ide = d.docide "
        "WHERE d.docoritip = 44 AND c.tip = 14 AND c.fec >= 20250101"
    ),
    "M4_nulos_ctrpro": (
        "SELECT SUM(CASE WHEN paride IS NULL THEN 1 ELSE 0 END) AS paride_null, "
        "SUM(CASE WHEN cenide IS NULL THEN 1 ELSE 0 END) AS cenide_null, "
        "SUM(CASE WHEN caaide IS NULL THEN 1 ELSE 0 END) AS caaide_null, COUNT(*) AS n FROM dbo.ctrpro"
    ),
    "M5_por_origen": (
        "SELECT ISNULL(d.docoritip, 0) AS docoritip, COUNT(*) AS n, MIN(c.fec) AS desde, MAX(c.fec) AS hasta "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND d.can < 0 "
        "GROUP BY ISNULL(d.docoritip, 0)"
    ),
    "M5_muestra": (
        "SELECT TOP 20 c.cod, c.fec, d.ide AS linea, d.proide, d.almide, d.can, d.pre, d.paride, "
        "ISNULL(d.docoritip, 0) AS docoritip, m.ide AS mov, m.tip, m.oritip, m.destip, m.canent, m.cansal, "
        "m.pre AS mpre, m.prepma, m.almcan, m.almpma, m.fechor FROM dbo.dcapro d "
        "JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide "
        "WHERE c.tip = 14 AND d.can < 0 ORDER BY d.ide DESC"
    ),
    "M5_mov_anterior": (
        "SELECT TOP 1 ide, almcan, almpma, fechor FROM dbo.mov WHERE proide = ? AND almide = ? AND ide < ? "
        "ORDER BY ide DESC"
    ),
    "M6_muestra": (
        "SELECT TOP 20 d.ide, d.can, d.linoriide, s.can AS ctrprodes_can, p.can AS ctr_can, p.canser "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.ctrprodes s "
        "ON s.lindeside = d.ide AND s.docdestip = 14 JOIN dbo.ctrpro p ON p.ide = d.linoriide "
        "WHERE c.tip = 14 AND d.docoritip = 44 AND d.can < 0 ORDER BY d.ide DESC"
    ),
    "M6_descuadres": (
        "SELECT COUNT(*) AS descuadres FROM dbo.ctrpro p WHERE p.ide IN (SELECT linoriide FROM dbo.dcapro "
        "WHERE docoritip = 44 AND can < 0) AND ABS(p.canser - (SELECT ISNULL(SUM(s.can), 0) "
        "FROM dbo.ctrprodes s WHERE s.docproide = p.ide AND s.docdestip = 14)) > 0.001"
    ),
    "M6_revisadas": (
        "SELECT COUNT(*) AS lineas_contrato, SUM(CASE WHEN p.canser < 0 THEN 1 ELSE 0 END) AS canser_negativo "
        "FROM dbo.ctrpro p WHERE p.ide IN (SELECT linoriide FROM dbo.dcapro WHERE docoritip = 44 AND can < 0)"
    ),
    # Sin subconsultas dentro de un agregado (error 130 de SQL Server): el «tiene desglose»
    # sale de una tabla derivada con DISTINCT unida por LEFT JOIN.
    "M7_desglose": (
        "SELECT COUNT(*) AS lineas, SUM(CASE WHEN x.docproide IS NULL THEN 0 ELSE 1 END) AS con_desglose, "
        "SUM(CASE WHEN ISNULL(d.parcandes, 0) <> 0 THEN 1 ELSE 0 END) AS parcandes "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide "
        "LEFT JOIN (SELECT DISTINCT docproide FROM dbo.dcapropar) x ON x.docproide = d.ide "
        "WHERE c.tip = 14 AND c.fec >= 20250101 AND d.paride > 0"
    ),
    "M8_almacenes_por_obra": (
        "SELECT n_almacenes, COUNT(*) AS obras FROM (SELECT obride, COUNT(*) AS n_almacenes FROM dbo.alm "
        "WHERE obride > 0 GROUP BY obride) x GROUP BY n_almacenes ORDER BY n_almacenes"
    ),
    "M8_almacen_del_contrato": (
        "SELECT SUM(CASE WHEN a.obride = t.obride THEN 1 ELSE 0 END) AS alm_de_su_obra, COUNT(*) AS n "
        "FROM dbo.ctr t LEFT JOIN dbo.alm a ON a.ide = t.almide"
    ),
    "M8_lineas_sin_partida": (
        "SELECT CASE WHEN a.obride = d.obride THEN 'alm_de_la_obra' ELSE 'otro' END AS tipo, "
        "ISNULL(a.paride, 0) AS alm_paride, CASE WHEN d.cenide = a.cenide THEN 1 ELSE 0 END AS cen_del_alm, "
        "COUNT(*) AS n FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.alm a "
        "ON a.ide = d.almide WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.paride, 0) = 0 "
        "GROUP BY CASE WHEN a.obride = d.obride THEN 'alm_de_la_obra' ELSE 'otro' END, ISNULL(a.paride, 0), "
        "CASE WHEN d.cenide = a.cenide THEN 1 ELSE 0 END ORDER BY n DESC"
    ),
    # T0a-bis: M9 por la ventana VENTANA_M9 (parámetros), sin `IN (SELECT ...)`: `con` (tip, fec) →
    # `dcapro` → `mov` por su índice `doclin` (docide, linide). Una línea puede tener más de un mov:
    # se cuentan líneas distintas. Ningún agregado lleva subconsulta (error 130).
    "M9_por_tipsininv": (
        f"SELECT a.tipsininv, COUNT(DISTINCT c.ide) AS albaranes, {_CON_MOV} "
        f"FROM dbo.con c JOIN dbo.dca a ON a.ide = c.ide {_M9_LINEAS_Y_MOV} {_M9_VENTANA} GROUP BY a.tipsininv"
    ),
    "M9_por_partida": (
        f"SELECT {_CON_SIN_PARTIDA} AS tipo, {_CON_MOV} FROM dbo.con c {_M9_LINEAS_Y_MOV} {_M9_VENTANA} "
        f"GROUP BY {_CON_SIN_PARTIDA}"
    ),
    # ¿Qué decide que una línea genere mov? Banderas del maestro de productos (`pro.tipmov` «Hace
    # movimientos», `pro.tipinv` «Es inventariable») y de su familia (`auxfam.tipinv`).
    "M9_por_banderas": (
        f"SELECT {_TIPMOV} AS tipmov, {_TIPINV} AS tipinv, ISNULL(f.tipinv, -1) AS fam_tipinv, {_CON_MOV} "
        f"FROM dbo.con c {_M9_LINEAS_Y_MOV} LEFT JOIN dbo.pro r ON r.ide = d.proide "
        f"LEFT JOIN dbo.auxfam f ON f.ide = r.famide {_M9_VENTANA} "
        f"GROUP BY {_TIPMOV}, {_TIPINV}, ISNULL(f.tipinv, -1) ORDER BY lineas DESC"
    ),
    # ¿Generan mov las líneas de los genéricos (MA9999, QA9999…)? Por código y empresa.
    "M9_genericos": (
        f"SELECT k.cod, k.emp, {_TIPMOV} AS tipmov, {_TIPINV} AS tipinv, {_CON_MOV} "
        f"FROM dbo.con c {_M9_LINEAS_Y_MOV} JOIN dbo.con k ON k.ide = d.proide "
        f"LEFT JOIN dbo.pro r ON r.ide = d.proide {_M9_VENTANA} AND k.cod IN ({_GENERICOS}) "
        f"GROUP BY k.cod, k.emp, {_TIPMOV}, {_TIPINV} ORDER BY k.cod, k.emp"
    ),
    "M9_sin_mov_por_producto": (
        f"SELECT TOP 10 d.proide, k.cod, k.emp, {_TIPMOV} AS tipmov, {_TIPINV} AS tipinv, COUNT(*) AS lineas "
        f"FROM dbo.con c {_M9_LINEAS_Y_MOV} LEFT JOIN dbo.con k ON k.ide = d.proide "
        f"LEFT JOIN dbo.pro r ON r.ide = d.proide {_M9_VENTANA} AND m.ide IS NULL "
        f"GROUP BY d.proide, k.cod, k.emp, {_TIPMOV}, {_TIPINV} ORDER BY lineas DESC"
    ),
    "M10_atrasados": (
        "SELECT TOP 20 m.ide, m.proide, m.almide, m.fechor, m.canent, m.almcan FROM dbo.mov m "
        "WHERE m.doctip = 14 AND m.fec >= 20260101 AND EXISTS (SELECT 1 FROM dbo.mov n "
        "WHERE n.proide = m.proide AND n.almide = m.almide AND n.ide < m.ide AND n.fechor > m.fechor) "
        "ORDER BY m.ide DESC"
    ),
    "M10_serie": (
        "SELECT TOP 40 ide, fechor, canent, cansal, almcan, almpma FROM dbo.mov "
        "WHERE proide = ? AND almide = ? AND fechor >= ? ORDER BY fechor, ide"
    ),
    "M11_productos": (
        "SELECT c.ide, c.cod, c.res, c.tip, c.emp, c.fecbaj, p.ivacomide, p.comide, p.natide, p.medide, "
        "p.gaside FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide WHERE c.cod IN ({in})"
    ),
    # T0a-bis: todas las de M11 van por la ventana VENTANA_M11 (parámetros `?`, antes del `ide`).
    "M11_lineas_producto": (
        f"SELECT TOP 30 d.cueide, d.ivaide, d.natide, d.unimed, d.caaide, COUNT(*) AS n {_M11_LINEAS} "
        f"WHERE {_VENTANA_PARAM} AND d.proide = ? "
        "GROUP BY d.cueide, d.ivaide, d.natide, d.unimed, d.caaide ORDER BY n DESC"
    ),
    "M11_total_producto": (
        f"SELECT COUNT(*) AS lineas, MIN(c.fec) AS desde, MAX(c.fec) AS hasta {_M11_LINEAS} "
        f"WHERE {_VENTANA_PARAM} AND d.proide = ?"
    ),
    # Solo los IVA que usan las líneas de albarán de la ventana, y si `ivacuo` = round(tot·iva, 2).
    "M11_iva_usado": (
        "SELECT d.ivaide, k.cod, i.iva, COUNT(*) AS lineas, "
        "SUM(CASE WHEN ABS(d.ivacuo - ROUND(d.tot * i.iva, 2)) > 0.011 THEN 1 ELSE 0 END) AS ivacuo_distinto "
        f"{_M11_LINEAS} LEFT JOIN dbo.iva i ON i.ide = d.ivaide "
        f"LEFT JOIN dbo.con k ON k.ide = d.ivaide WHERE {_VENTANA_PARAM} "
        "GROUP BY d.ivaide, k.cod, i.iva ORDER BY lineas DESC"
    ),
    # T0a (spec v5, H15): IVA de cada MA9999 por proveedor. El recuento por proveedor va en una
    # tabla derivada (regla del error 130).
    "M11_iva_por_proveedor": (
        "SELECT COUNT(*) AS proveedores, SUM(CASE WHEN x.n_iva > 1 THEN 1 ELSE 0 END) AS con_varios_iva "
        f"FROM (SELECT a.entide, COUNT(DISTINCT d.ivaide) AS n_iva {_M11_LINEAS} JOIN dbo.dca a "
        f"ON a.ide = c.ide WHERE {_VENTANA_PARAM} AND d.proide = ? GROUP BY a.entide) x"
    ),
    "M11_iva_y_isp": (
        "SELECT a.tipisp, d.ivaide, COUNT(DISTINCT a.entide) AS proveedores, COUNT(*) AS lineas "
        f"{_M11_LINEAS} JOIN dbo.dca a ON a.ide = c.ide "
        f"WHERE {_VENTANA_PARAM} AND d.proide = ? GROUP BY a.tipisp, d.ivaide "
        "ORDER BY lineas DESC"
    ),
    # ¿Acierta más el IVA de la línea anterior del MISMO proveedor que el de la anterior de
    # cualquiera? `LAG ... OVER` en una tabla derivada; si la API la rechaza, m11 lo anota y sigue.
    "M11_acierto": (
        "SELECT COUNT(*) AS lineas, SUM(CASE WHEN x.iva_prev_prv IS NULL THEN 1 ELSE 0 END) AS sin_previa_del_prv, "
        "SUM(CASE WHEN x.ivaide = x.iva_prev_prv THEN 1 ELSE 0 END) AS acierta_mismo_prv, "
        "SUM(CASE WHEN x.ivaide = x.iva_prev THEN 1 ELSE 0 END) AS acierta_cualquiera "
        "FROM (SELECT d.ivaide, LAG(d.ivaide) OVER (PARTITION BY a.entide ORDER BY d.ide) AS iva_prev_prv, "
        f"LAG(d.ivaide) OVER (ORDER BY d.ide) AS iva_prev {_M11_LINEAS} JOIN dbo.dca a ON a.ide = c.ide "
        f"WHERE {_VENTANA_PARAM} AND d.proide = ?) x"
    ),
    "M12_mezcla": (
        "SELECT COUNT(DISTINCT d.ide) AS con_lineas_sin_vincular, (SELECT COUNT(*) FROM dbo.dca d2 "
        "JOIN dbo.con c2 ON c2.ide = d2.ide WHERE c2.tip = 14 AND c2.fec >= 20250101 AND d2.ctride > 0) "
        "AS con_contrato FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide JOIN dbo.dcapro p "
        "ON p.docide = d.ide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.ctride > 0 "
        "AND ISNULL(p.docoritip, 0) <> 44"
    ),
    # Ventana acotada por ide (log tiene millones de filas) y por fecha de la fila de log.
    "M13_est_alta": (
        "SELECT est, ori, COUNT(*) AS n FROM dbo.log WHERE ide > (SELECT MAX(ide) - 1000000 FROM dbo.log) "
        "AND fec >= 20260901 AND tab = 'con' AND tip = 14 AND ope = 1 GROUP BY est, ori ORDER BY n DESC"
    ),
    "M13_cobertura": (
        "SELECT COUNT(*) AS albaranes, SUM(CASE WHEN l.cod IS NULL THEN 0 ELSE 1 END) AS con_log "
        "FROM dbo.con c LEFT JOIN (SELECT DISTINCT cod FROM dbo.log WHERE ide > (SELECT MAX(ide) - 1000000 "
        "FROM dbo.log) AND fec >= 20260901 AND tab = 'con' AND tip = 14 AND ope = 1) l ON l.cod = c.cod "
        "WHERE c.tip = 14 AND c.fec >= 20260915 AND c.cod LIKE 'AC%'"
    ),
    # Muestra del MISMO proveedor que el albarán de la API: así la cabecera es comparable.
    "M14_escritorio": (
        "SELECT TOP 3 c.ide, c.cod FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
        "WHERE c.tip = 14 AND d.ctride > 0 AND c.ide <> ? "
        "AND d.entide = (SELECT entide FROM dbo.dca WHERE ide = ?) ORDER BY c.ide DESC"
    ),
    # ¿Sale la forma de pago y el efecto de la cabecera del maestro del proveedor?
    "M14_prv": (
        "SELECT COUNT(*) AS n, SUM(CASE WHEN d.pagide = v.pagide THEN 1 ELSE 0 END) AS pagide_del_prv, "
        "SUM(CASE WHEN d.efeide = v.efeide THEN 1 ELSE 0 END) AS efeide_del_prv FROM dbo.dca d "
        "JOIN dbo.con c ON c.ide = d.ide JOIN dbo.prv v ON v.ide = d.entide "
        "WHERE c.tip = 14 AND c.fec >= 20260901"
    ),
    # ¿Qué guarda el escritorio en dcapro.prepma? Frente al PMP resultante y al prepma de su mov.
    "M14_prepma": (
        "SELECT COUNT(*) AS n, SUM(CASE WHEN ABS(d.prepma - m.almpma) < 0.0001 THEN 1 ELSE 0 END) "
        "AS igual_pmp_resultante, SUM(CASE WHEN ABS(d.prepma - m.prepma) < 0.0001 THEN 1 ELSE 0 END) "
        "AS igual_prepma_del_mov FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide "
        "JOIN dbo.mov m ON m.docide = d.docide AND m.linide = d.ide WHERE c.tip = 14 AND c.fec >= 20260901"
    ),
    "M14_api": "SELECT ide, cod FROM dbo.con WHERE tip = 14 AND cod = ?",
    "M14_con": "SELECT * FROM dbo.con WHERE ide IN ({in})",
    "M14_dca": "SELECT * FROM dbo.dca WHERE ide IN ({in})",
    "M14_dcapro": "SELECT * FROM dbo.dcapro WHERE docide IN ({in}) ORDER BY docide, pos",
    # T0a (spec v5, H11): columnas de la lista de reseteo en las líneas sin vincular de 2026.
    "M14_sv_valores": (
        "SELECT COUNT(*) AS n, "
        + ", ".join(f"SUM(CASE WHEN {cond} THEN 1 ELSE 0 END) AS {col}" for col, cond in COLUMNAS_SV)
        + ", SUM(CASE WHEN d.fec = c.fec THEN 1 ELSE 0 END) AS fec_igual_albaran "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20260101 "
        "AND ISNULL(d.docoritip, 0) <> 44"
    ),
    # Arrastre: las 3 últimas sin vincular del MA9999 de la empresa 1, cada una frente a su plantilla.
    "M14_sv_ma9999": "SELECT c.ide FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide WHERE c.cod = ? AND c.emp = ?",
    "M14_sv_ultimas": (
        "SELECT TOP 3 d.ide, d.proide FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide "
        "WHERE c.tip = 14 AND c.fec >= 20260901 AND ISNULL(d.docoritip, 0) <> 44 AND d.proide = ? "
        "ORDER BY d.ide DESC"
    ),
    "M14_sv_linea": "SELECT * FROM dbo.dcapro WHERE ide = ?",
    "M14_sv_plantilla": "SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? AND ide < ? ORDER BY ide DESC",
    # T0a-bis, M14b: forma de pago y efecto del albarán ANTERIOR del mismo proveedor en la misma empresa
    # (por ide) frente al maestro del proveedor. Las dos tasas se comparan sobre los mismos albaranes
    # (los que tienen anterior); la del maestro sobre todos va aparte.
    "M14b_pago_previo": (
        "SELECT COUNT(*) AS n, SUM(CASE WHEN x.ide_previo IS NULL THEN 1 ELSE 0 END) AS sin_previo, "
        "SUM(CASE WHEN x.ide_previo IS NOT NULL AND x.pagide = x.pag_previo THEN 1 ELSE 0 END) AS pagide_del_previo, "
        "SUM(CASE WHEN x.ide_previo IS NOT NULL AND x.efeide = x.efe_previo THEN 1 ELSE 0 END) AS efeide_del_previo, "
        "SUM(CASE WHEN x.ide_previo IS NOT NULL AND x.pagide = x.pag_prv THEN 1 ELSE 0 END) "
        "AS pagide_del_prv_con_previo, "
        "SUM(CASE WHEN x.ide_previo IS NOT NULL AND x.efeide = x.efe_prv THEN 1 ELSE 0 END) "
        "AS efeide_del_prv_con_previo, "
        "SUM(CASE WHEN x.pagide = x.pag_prv THEN 1 ELSE 0 END) AS pagide_del_prv, "
        "SUM(CASE WHEN x.efeide = x.efe_prv THEN 1 ELSE 0 END) AS efeide_del_prv "
        "FROM (SELECT c.fec, a.pagide, a.efeide, v.pagide AS pag_prv, v.efeide AS efe_prv, "
        "LAG(c.ide) OVER (PARTITION BY c.emp, a.entide ORDER BY c.ide) AS ide_previo, "
        "LAG(a.pagide) OVER (PARTITION BY c.emp, a.entide ORDER BY c.ide) AS pag_previo, "
        "LAG(a.efeide) OVER (PARTITION BY c.emp, a.entide ORDER BY c.ide) AS efe_previo "
        "FROM dbo.con c JOIN dbo.dca a ON a.ide = c.ide LEFT JOIN dbo.prv v ON v.ide = a.entide "
        "WHERE c.tip = 14 AND c.fec >= ?) x WHERE x.fec >= ?"
    ),
    "M15_stock_negativo": (
        "SELECT COUNT(*) AS n, COUNT(DISTINCT almide) AS almacenes FROM dbo.mov "
        "WHERE almcan < 0 AND fec >= 20250101"
    ),
    # --- T0a (spec v5): M16 analítica, almacén y centro (H10, H13) ---
    "M16_caa_con_partida": (
        f"SELECT {_TIPO_LINEA} AS tipo, {_PARTIDA_DISTINTA} AS partida_distinta, COUNT(*) AS n, "
        "SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(p.caaide, 0) THEN 1 ELSE 0 END) AS caa_de_la_partida, "
        "SUM(CASE WHEN ISNULL(p.caaide, 0) = 0 THEN 1 ELSE 0 END) AS partida_sin_caa, "
        "SUM(CASE WHEN t.ide IS NOT NULL AND ISNULL(d.caaide, 0) = ISNULL(t.caaide, 0) THEN 1 ELSE 0 END) "
        "AS caa_del_ctrpro FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide "
        "JOIN dbo.obrparpar p ON p.ide = d.paride LEFT JOIN dbo.ctrpro t ON t.ide = d.linoriide "
        "AND d.docoritip = 44 WHERE c.tip = 14 AND c.fec >= 20250101 AND d.paride > 0 "
        f"GROUP BY {_TIPO_LINEA}, {_PARTIDA_DISTINTA}"
    ),
    "M16_caa_almacen": (
        f"SELECT {_TIPO_LINEA} AS tipo, COUNT(*) AS n, "
        "SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(a.caaproide, 0) THEN 1 ELSE 0 END) AS caa_pro_del_alm, "
        "SUM(CASE WHEN ISNULL(d.caaide, 0) = ISNULL(a.caaseride, 0) THEN 1 ELSE 0 END) AS caa_ser_del_alm, "
        "SUM(CASE WHEN ISNULL(a.caaproide, 0) = 0 THEN 1 ELSE 0 END) AS alm_sin_caa "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide LEFT JOIN dbo.alm a ON a.ide = d.almide "
        f"WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.paride, 0) = 0 GROUP BY {_TIPO_LINEA}"
    ),
    "M16_almacen_sin_vincular": (
        f"SELECT {_TIPO_PARTIDA} AS tipo, {_CABECERA} AS cabecera, COUNT(*) AS n, "
        "SUM(CASE WHEN d.almide = t.almide THEN 1 ELSE 0 END) AS alm_del_contrato, "
        "SUM(CASE WHEN d.almide = o.almide THEN 1 ELSE 0 END) AS alm_de_la_ficha, "
        "SUM(CASE WHEN d.cenide = t.cenide THEN 1 ELSE 0 END) AS cen_del_contrato, "
        "SUM(CASE WHEN d.cenide = o.cenide THEN 1 ELSE 0 END) AS cen_de_la_ficha "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide JOIN dbo.dca a ON a.ide = d.docide "
        "LEFT JOIN dbo.obr o ON o.ide = d.obride LEFT JOIN dbo.ctr t ON t.ide = a.ctride "
        "WHERE c.tip = 14 AND c.fec >= 20250101 AND ISNULL(d.docoritip, 0) <> 44 "
        f"GROUP BY {_TIPO_PARTIDA}, {_CABECERA}"
    ),
    "M16_ficha_obra": (
        "SELECT COUNT(*) AS obras, SUM(CASE WHEN ISNULL(o.almide, 0) > 0 THEN 1 ELSE 0 END) AS con_almide, "
        "SUM(CASE WHEN a.obride = o.ide THEN 1 ELSE 0 END) AS almide_de_su_obra, "
        "SUM(CASE WHEN ISNULL(o.cenide, 0) > 0 THEN 1 ELSE 0 END) AS con_cenide "
        "FROM dbo.obr o LEFT JOIN dbo.alm a ON a.ide = o.almide WHERE o.ide IN (SELECT d.obride "
        "FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide WHERE c.tip = 14 AND c.fec >= 20250101)"
    ),
    # --- T0a-bis, M16b: origen de dcapro.caaide en las líneas sin vincular, desde 2025 ---
    # Cada candidata es una bandera 0/1 por línea en la tabla derivada; fuera solo se suman.
    "M16b_fuentes": (
        "SELECT x.grupo, x.partida, COUNT(*) AS n, SUM(x.caa_cero) AS caa_cero, SUM(x.pro_gaside) AS pro_gaside, "
        "SUM(x.cen_gaside) AS cen_gaside, SUM(x.cab_caaide) AS cab_caaide, SUM(x.ctr_caaide) AS ctr_caaide, "
        "SUM(x.par_caaide) AS par_caaide, SUM(x.caa_del_centro) AS caa_del_centro "
        f"FROM (SELECT {_GRUPO_GENERICO} AS grupo, {_CON_SIN_PARTIDA} AS partida, "
        "CASE WHEN ISNULL(d.caaide, 0) = 0 THEN 1 ELSE 0 END AS caa_cero, "
        f"CASE WHEN {_CAA_INFORMADA} AND d.caaide = r.gaside THEN 1 ELSE 0 END AS pro_gaside, "
        f"CASE WHEN {_CAA_INFORMADA} AND d.caaide = e.gaside THEN 1 ELSE 0 END AS cen_gaside, "
        f"CASE WHEN {_CAA_INFORMADA} AND d.caaide = a.caaide THEN 1 ELSE 0 END AS cab_caaide, "
        f"CASE WHEN {_CAA_INFORMADA} AND d.caaide = t.caaide THEN 1 ELSE 0 END AS ctr_caaide, "
        f"CASE WHEN {_CAA_INFORMADA} AND d.caaide = p.caaide THEN 1 ELSE 0 END AS par_caaide, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_DEL_CENTRO} THEN 1 ELSE 0 END AS caa_del_centro "
        f"{_M16B_DESDE} JOIN dbo.dca a ON a.ide = c.ide LEFT JOIN dbo.cen e ON e.ide = d.cenide "
        "LEFT JOIN dbo.ctr t ON t.ide = a.ctride LEFT JOIN dbo.obrparpar p ON p.ide = d.paride "
        f"{_SIN_VINCULAR_DESDE_2025}) x GROUP BY x.grupo, x.partida ORDER BY x.grupo, x.partida"
    ),
    # Pista de negocio (Administración y Control de Costes, 2026-09-29): la analítica va vinculada al
    # centro de coste y a la cuenta financiera de gasto (6XX). Se prueba si el código de la caa sale del
    # de la naturaleza, del de la cuenta financiera, del de la obra o del centro, solo y con su centro.
    "M16b_codigos": (
        "SELECT x.grupo, x.partida, COUNT(*) AS n, SUM(x.caa_cod_caagascod) AS caa_cod_caagascod, "
        "SUM(x.caa_cod_caaexicod) AS caa_cod_caaexicod, SUM(x.caa_cod_cuafaccod) AS caa_cod_cuafaccod, "
        "SUM(x.caa_cod_cuenta) AS caa_cod_cuenta, SUM(x.caa_cod_empieza_por_cuenta) AS caa_cod_empieza_por_cuenta, "
        "SUM(x.caa_cod_contiene_obra) AS caa_cod_contiene_obra, "
        "SUM(x.caa_cod_contiene_centro) AS caa_cod_contiene_centro, SUM(x.centro_y_caagascod) AS centro_y_caagascod, "
        "SUM(x.centro_y_cuenta) AS centro_y_cuenta, SUM(x.cuenta_6xx) AS cuenta_6xx, "
        "SUM(x.cuenta_es_cuacomcod) AS cuenta_es_cuacomcod "
        f"FROM (SELECT {_GRUPO_GENERICO} AS grupo, {_CON_SIN_PARTIDA} AS partida, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_ES_CAAGASCOD} THEN 1 ELSE 0 END AS caa_cod_caagascod, "
        f"CASE WHEN {_CAA_INFORMADA} AND ISNULL(nt.caaexicod, '') <> '' AND kc.cod = nt.caaexicod THEN 1 ELSE 0 END "
        "AS caa_cod_caaexicod, "
        f"CASE WHEN {_CAA_INFORMADA} AND ISNULL(nt.cuafaccod, '') <> '' AND kc.cod = nt.cuafaccod THEN 1 ELSE 0 END "
        "AS caa_cod_cuafaccod, "
        f"CASE WHEN {_CAA_INFORMADA} AND ISNULL(cf.cod, '') <> '' AND kc.cod = cf.cod THEN 1 ELSE 0 END "
        "AS caa_cod_cuenta, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_EMPIEZA_POR_CUENTA} THEN 1 ELSE 0 END AS caa_cod_empieza_por_cuenta, "
        f"CASE WHEN {_CAA_INFORMADA} AND ISNULL(oc.cod, '') <> '' AND CHARINDEX(RTRIM(oc.cod), kc.cod) > 0 "
        "THEN 1 ELSE 0 END AS caa_cod_contiene_obra, "
        f"CASE WHEN {_CAA_INFORMADA} AND ISNULL(ec.cod, '') <> '' AND CHARINDEX(RTRIM(ec.cod), kc.cod) > 0 "
        "THEN 1 ELSE 0 END AS caa_cod_contiene_centro, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_DEL_CENTRO} AND {_CAA_ES_CAAGASCOD} THEN 1 ELSE 0 END "
        "AS centro_y_caagascod, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_DEL_CENTRO} AND {_CAA_EMPIEZA_POR_CUENTA} THEN 1 ELSE 0 END "
        "AS centro_y_cuenta, "
        "CASE WHEN LEFT(ISNULL(cf.cod, ''), 1) = '6' THEN 1 ELSE 0 END AS cuenta_6xx, "
        "CASE WHEN ISNULL(nt.cuacomcod, '') <> '' AND cf.cod = nt.cuacomcod THEN 1 ELSE 0 END AS cuenta_es_cuacomcod "
        f"{_M16B_DESDE} {_M16B_CODIGOS} {_SIN_VINCULAR_DESDE_2025}) x "
        "GROUP BY x.grupo, x.partida ORDER BY x.grupo, x.partida"
    ),
    # Muestra agregada por frecuencia para ver a ojo el patrón del código de la caa.
    "M16b_muestra": (
        "SELECT TOP 20 kc.cod AS caa_cod, nt.caagascod, nt.caaexicod, oc.cod AS obra, ec.cod AS centro, "
        f"cf.cod AS cuenta, {_CON_SIN_PARTIDA} AS partida, COUNT(*) AS lineas {_M16B_DESDE} {_M16B_CODIGOS} "
        f"{_SIN_VINCULAR_DESDE_2025} AND {_CAA_INFORMADA} "
        f"GROUP BY kc.cod, nt.caagascod, nt.caaexicod, oc.cod, ec.cod, cf.cod, {_CON_SIN_PARTIDA} "
        "ORDER BY lineas DESC"
    ),
    # --- T0a (spec v5): M17 anulación de albaranes (H9). Ventana de log acotada por ide, como M13 ---
    "M17_ope": (
        "SELECT ope, COUNT(*) AS n, MIN(fec) AS desde, MAX(fec) AS hasta FROM dbo.log "
        f"WHERE ide > {_VENTANA_LOG} AND tab = 'con' AND tip = 14 GROUP BY ope ORDER BY ope"
    ),
    # Lo resuelve el propio script: si `log.emp` sale 0 o nulo, m17 repite el JOIN sin `emp`.
    "M17_emp_log": (
        "SELECT ISNULL(emp, -1) AS emp, COUNT(*) AS n FROM dbo.log "
        f"WHERE ide > {_VENTANA_LOG} AND tab = 'con' AND tip = 14 AND ope <> 1 "
        "GROUP BY ISNULL(emp, -1) ORDER BY n DESC"
    ),
    "M17_existe": (
        "SELECT l.ope, COUNT(*) AS n, SUM(CASE WHEN c.ide IS NULL THEN 0 ELSE 1 END) AS con_existe, "
        "SUM(CASE WHEN ISNULL(c.fecbaj, 0) > 0 THEN 1 ELSE 0 END) AS con_fecbaj FROM dbo.log l "
        "LEFT JOIN dbo.con c ON c.emp = l.emp AND c.tip = l.tip AND c.cod = l.cod "
        f"WHERE l.ide > {_VENTANA_LOG} AND l.tab = 'con' AND l.tip = 14 AND l.ope <> 1 "
        "GROUP BY l.ope ORDER BY l.ope"
    ),
    "M17_existe_sin_emp": (
        "SELECT l.ope, COUNT(*) AS n, SUM(CASE WHEN c.ide IS NULL THEN 0 ELSE 1 END) AS con_existe, "
        "SUM(CASE WHEN ISNULL(c.fecbaj, 0) > 0 THEN 1 ELSE 0 END) AS con_fecbaj FROM dbo.log l "
        "LEFT JOIN dbo.con c ON c.tip = l.tip AND c.cod = l.cod "
        f"WHERE l.ide > {_VENTANA_LOG} AND l.tab = 'con' AND l.tip = 14 AND l.ope <> 1 "
        "GROUP BY l.ope ORDER BY l.ope"
    ),
    "M17_marcas": (
        "SELECT est, CASE WHEN ISNULL(fecbaj, 0) > 0 THEN 1 ELSE 0 END AS con_fecbaj, COUNT(*) AS n "
        "FROM dbo.con WHERE tip = 14 AND fec >= 20250101 "
        "GROUP BY est, CASE WHEN ISNULL(fecbaj, 0) > 0 THEN 1 ELSE 0 END ORDER BY n DESC"
    ),
    # --- T0a-bis, M17b: tras una ope 2, ¿el con con ese (emp, tip, cod) es el mismo o uno posterior? ---
    # `log` no guarda el ide del registro (diccionario: ide, emp, ori, ope, fec, hor, usu, tab, tip, cod,
    # res, tex, est, err): se busca un alta (ope 1) del mismo (emp, cod) POSTERIOR a la ope 2.
    "M17b_reutiliza": (
        f"SELECT {_CASO_M17B} AS caso, COUNT(*) AS n, "
        "SUM(CASE WHEN p.pri_alta < l.ide THEN 1 ELSE 0 END) AS con_alta_previa, "
        "SUM(CASE WHEN c.ide IS NOT NULL AND c.fec > l.fec THEN 1 ELSE 0 END) AS con_fec_posterior, "
        "SUM(CASE WHEN c.ide IS NOT NULL AND c.fec <= l.fec THEN 1 ELSE 0 END) AS con_fec_anterior "
        "FROM dbo.log l LEFT JOIN dbo.con c ON c.emp = l.emp AND c.tip = l.tip AND c.cod = l.cod "
        f"LEFT JOIN {_ALTAS_LOG} p ON p.emp = l.emp AND p.cod = l.cod {_LOG_ALBARANES} AND l.ope = 2 "
        f"GROUP BY {_CASO_M17B}"
    ),
    # Perfil de cada ope (filas por documento, usuarios, est) y su resumen más frecuente.
    "M17b_perfil": (
        "SELECT l.ope, COUNT(*) AS n, COUNT(DISTINCT l.cod) AS documentos, COUNT(DISTINCT l.usu) AS usuarios, "
        "COUNT(DISTINCT l.est) AS estados, MIN(l.est) AS est_min, MAX(l.est) AS est_max, "
        "SUM(CASE WHEN DATALENGTH(l.tex) > 0 THEN 1 ELSE 0 END) AS con_tex "
        f"FROM dbo.log l {_LOG_ALBARANES} GROUP BY l.ope ORDER BY l.ope"
    ),
    "M17b_res": (
        "SELECT TOP 40 l.ope, LEFT(ISNULL(l.res, ''), 40) AS res, COUNT(*) AS n "
        f"FROM dbo.log l {_LOG_ALBARANES} AND l.ope <> 1 GROUP BY l.ope, LEFT(ISNULL(l.res, ''), 40) "
        "ORDER BY n DESC"
    ),
    # --- T0a (spec v5): M18 uso de dcapro.refent (H18) ---
    "M18_refent": (
        f"SELECT {_TIPO_LINEA} AS tipo, COUNT(*) AS n, "
        "SUM(CASE WHEN ISNULL(d.refent, '') <> '' THEN 1 ELSE 0 END) AS con_refent "
        "FROM dbo.dcapro d JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 "
        f"GROUP BY {_TIPO_LINEA}"
    ),
    "M18_valores": (
        "SELECT TOP 20 LEFT(d.refent, 8) AS prefijo, COUNT(*) AS n FROM dbo.dcapro d "
        "JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 "
        "AND ISNULL(d.refent, '') <> '' GROUP BY LEFT(d.refent, 8) ORDER BY n DESC"
    ),
    "M18_propagacion": (
        "SELECT COUNT(*) AS n, SUM(CASE WHEN ISNULL(f.refent, '') <> '' THEN 1 ELSE 0 END) AS con_refent, "
        "SUM(CASE WHEN ISNULL(d.refent, '') <> '' AND f.refent = d.refent THEN 1 ELSE 0 END) AS copiada "
        "FROM dbo.dcfpro f JOIN dbo.dcapro d ON d.ide = f.linoriide WHERE f.docoritip = 14 "
        "AND f.docide IN (SELECT ide FROM dbo.con WHERE fec >= 20250101)"
    ),
}

_PRIMERA_PALABRA = re.compile(r"^\s*(\w+)", re.IGNORECASE)


def es_solo_lectura(sql: str) -> bool:
    """Una sola sentencia que empieza por SELECT o WITH (sin `;`)."""
    m = _PRIMERA_PALABRA.match(sql)
    return bool(m) and m.group(1).upper() in {"SELECT", "WITH"} and ";" not in sql


_AGREGADO = re.compile(r"\b(SUM|COUNT|AVG|MIN|MAX)\s*\(", re.IGNORECASE)
_APPLY_ESCALAR = re.compile(r"\bAPPLY\s*\(\s*SELECT\s*\(\s*SELECT\b", re.IGNORECASE)


def agregado_con_subconsulta(sql: str) -> bool:
    """Detecta lo que SQL Server rechaza con el error 130 («No es posible usar una función de
    agregado con una expresión que contiene un agregado o una subconsulta»): un agregado cuyo
    argumento lleva SELECT/EXISTS, o columnas escalares de un APPLY que luego se agregan.
    Heurística conservadora, sin parser: mira el argumento con los paréntesis equilibrados."""
    if _APPLY_ESCALAR.search(sql):
        return True
    for coincidencia in _AGREGADO.finditer(sql):
        profundidad, i = 1, coincidencia.end()
        while i < len(sql) and profundidad:
            profundidad += {"(": 1, ")": -1}.get(sql[i], 0)
            i += 1
        argumento = sql[coincidencia.end(): i - 1].upper()
        if re.search(r"\b(SELECT|EXISTS)\b", argumento):
            return True
    return False


# ---------------------------------------------------------------------------
# Cliente de solo lectura
# ---------------------------------------------------------------------------
class ErrorDeLectura(Exception):
    pass


def es_interbloqueo(texto: str) -> bool:
    """Error 1205 de SQL Server (SQLSTATE 40001): la sentencia fue la víctima de un interbloqueo y
    basta con repetirla (le pasó a M14 el 2026-10-05)."""
    return "(1205)" in texto or "40001" in texto


@dataclass
class Resultado:
    filas: list[dict[str, Any]]
    truncado: bool
    segundos: float


class ClienteLectura:
    """Solo `POST /api/sql/read`. Rechaza en local cualquier SQL que no sea lectura."""

    def __init__(self, base_url: str, clave: str, sesion: Any = None,
                 dormir: Callable[[float], Any] = time.sleep) -> None:
        self._url = base_url.rstrip("/") + "/api/sql/read"
        self._cabeceras = {"x-functions-key": clave, "Content-Type": "application/json"}
        if sesion is None:
            import requests  # solo hace falta con red

            sesion = requests.Session()
        self._sesion = sesion
        self._dormir = dormir

    def leer(self, sql: str, parametros: list[Any] | None = None, *, max_rows: int = 200,
             timeout_s: int = TIMEOUT_NORMAL_S) -> Resultado:
        """Una lectura; ante el interbloqueo 1205 se repite hasta REINTENTOS_INTERBLOQUEO veces con
        espera creciente. Cualquier otro error (también un ReadTimeout) sale a la primera."""
        for intento in range(REINTENTOS_INTERBLOQUEO + 1):
            try:
                return self._leer_una_vez(sql, parametros, max_rows=max_rows, timeout_s=timeout_s)
            except ErrorDeLectura as exc:
                if intento == REINTENTOS_INTERBLOQUEO or not es_interbloqueo(str(exc)):
                    raise
                self._dormir(ESPERA_INTERBLOQUEO_S * (intento + 1))
        raise AssertionError("inalcanzable")  # pragma: no cover

    def _leer_una_vez(self, sql: str, parametros: list[Any] | None, *, max_rows: int,
                      timeout_s: int) -> Resultado:
        if not es_solo_lectura(sql):
            raise ErrorDeLectura("SQL rechazada en local: solo SELECT/WITH de una sentencia.")
        cuerpo = {"database": DATABASE, "sql": sql, "parameters": parametros or [],
                  "max_rows": max_rows, "timeout_seconds": timeout_s}
        t0 = time.monotonic()
        try:
            resp = self._sesion.post(self._url, headers=self._cabeceras, json=cuerpo,
                                     timeout=timeout_s + 30)
        except Exception as exc:  # noqa: BLE001 - red o tiempo agotado: se traduce sin filtrar la URL
            raise ErrorDeLectura(f"{type(exc).__name__} al llamar a sql/read") from None
        segundos = time.monotonic() - t0
        try:
            datos = resp.json()
        except ValueError:
            raise ErrorDeLectura(f"HTTP {resp.status_code} sin JSON") from None
        if resp.status_code != 200 or not datos.get("ok", False):
            raise ErrorDeLectura(f"HTTP {resp.status_code}: {datos.get('error')} {datos.get('details')}")
        columnas = datos.get("columns", [])
        filas = [dict(zip(columnas, fila)) for fila in datos.get("rows", [])]
        return Resultado(filas, bool(datos.get("truncated", False)), segundos)


# ---------------------------------------------------------------------------
# Informe
# ---------------------------------------------------------------------------
@dataclass
class Informe:
    clave: str
    titulo: str
    lineas: list[str] = field(default_factory=list)
    conclusiones: list[str] = field(default_factory=list)

    def tabla(self, nombre: str, res: Resultado, limite: int = 40) -> None:
        self.lineas.append(f"  [{nombre}] {len(res.filas)} filas en {res.segundos:.1f} s"
                           + ("  ** TRUNCADO: resultado incompleto **" if res.truncado else ""))
        for fila in res.filas[:limite]:
            self.lineas.append("    " + "; ".join(f"{k}={_corto(v)}" for k, v in fila.items()))
        if len(res.filas) > limite:
            self.lineas.append(f"    ... {len(res.filas) - limite} filas más")
        if res.truncado:
            self.conclusiones.append(f"AVISO: {nombre} vino truncado; la conclusión puede estar incompleta.")

    def concluir(self, texto: str) -> None:
        self.conclusiones.append(texto)

    def texto(self) -> str:
        cab = f"=== {self.clave} · {self.titulo} ==="
        concl = ["  CONCLUSIÓN:"] + [f"   - {c}" for c in self.conclusiones] if self.conclusiones else []
        return "\n".join([cab, *self.lineas, *concl, ""])


def _corto(valor: Any, n: int = 60) -> str:
    texto = "NULL" if valor is None else str(valor)
    return texto if len(texto) <= n else texto[: n - 3] + "..."


def _num(valor: Any) -> float:
    return float(valor or 0)


def _casi(a: float, b: float, tol: float = 1e-4) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def _pct(parte: float, total: float) -> str:
    return f"{parte:.0f} de {total:.0f}" + (f" ({100 * parte / total:.1f} %)" if total else "")


# ---------------------------------------------------------------------------
# Análisis puros (probados sin red)
# ---------------------------------------------------------------------------
def regla_devolucion(fila: dict[str, Any], anterior: dict[str, Any] | None) -> str:
    """'A' (entrada negativa con la fórmula del PMP), 'B' (salida a PMP vigente) o '?'."""
    if fila.get("mov") is None:
        return "sin_mov"
    can, pre = _num(fila.get("can")), _num(fila.get("pre"))
    canent, cansal = _num(fila.get("canent")), _num(fila.get("cansal"))
    almcan, almpma = _num(fila.get("almcan")), _num(fila.get("almpma"))
    stock = _num(anterior.get("almcan")) if anterior else 0.0
    pma = _num(anterior.get("almpma")) if anterior else 0.0
    if _casi(canent, can) and _casi(cansal, 0.0) and _casi(almcan, stock + can):
        esperado = pma if _casi(stock + can, 0.0) else (stock * pma + can * pre) / (stock + can)
        if _casi(almpma, esperado, 1e-3):
            return "A"
        if _casi(almpma, pma, 1e-3):
            return "A_pmp_sin_cambio"
        return "A_pmp_distinto"
    if _casi(canent, 0.0) and _casi(cansal, -can) and _casi(almcan, stock + can):
        return "B" if _casi(almpma, pma, 1e-3) else "B_pmp_distinto"
    return "?"


def roturas_de_cadena(movs: list[dict[str, Any]]) -> int:
    """Cuántas veces `almcan` no es el anterior + entrada - salida, en el orden dado."""
    roturas = 0
    for previo, actual in pairwise(movs):
        esperado = _num(previo.get("almcan")) + _num(actual.get("canent")) - _num(actual.get("cansal"))
        if not _casi(_num(actual.get("almcan")), esperado, 1e-3):
            roturas += 1
    return roturas


def columnas_distintas(escritorio: list[dict[str, Any]], api: list[dict[str, Any]],
                       ignorar: set[str]) -> dict[str, tuple[list[str], list[str]]]:
    """Columnas cuyo(s) valor(es) en la API no aparecen en ninguna fila del escritorio."""
    salida: dict[str, tuple[list[str], list[str]]] = {}
    if not escritorio or not api:
        return salida
    for col in api[0]:
        if col in ignorar:
            continue
        v_esc = {_corto(f.get(col), 40) for f in escritorio}
        v_api = {_corto(f.get(col), 40) for f in api}
        if not v_api & v_esc:
            salida[col] = (sorted(v_esc)[:5], sorted(v_api)[:5])
    return salida


# ---------------------------------------------------------------------------
# Mediciones
# ---------------------------------------------------------------------------
def m1(c: ClienteLectura) -> Informe:
    inf = Informe("M1", "dca.synckey: ¿libre? ¿cuánto cuesta buscar sin índice?")
    r = c.leer(SQL["M1_total"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("total", r)
    tot = r.filas[0] if r.filas else {}
    inf.concluir(f"dca.synckey informado en {_pct(_num(tot.get('con_synckey')), _num(tot.get('total')))} albaranes.")
    r = c.leer(SQL["M1_prefijos"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("prefijos", r)
    r = c.leer(SQL["M1_prefijo_alb"], ["ALB-%"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("prefijo ALB-", r)
    n_alb = _num(r.filas[0].get("n")) if r.filas else -1
    inf.concluir(f"synckey que ya empiezan por 'ALB-': {n_alb:.0f} (debe ser 0 para usar ese prefijo).")
    r = c.leer(SQL["M1_busqueda"], [14, "ALB-F009-T0-NO-EXISTE"], max_rows=5, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("búsqueda por synckey", r)
    inf.concluir(f"Búsqueda de un albarán por synckey (sin índice): {r.segundos:.1f} s de ida y vuelta.")
    return inf


def m2(c: ClienteLectura) -> Informe:
    inf = Informe("M2", "con.est y emp de los albaranes, serie AC, mov.emp e índices de con")
    r = c.leer(SQL["M2_est_emp"], max_rows=50)
    inf.tabla("est/emp desde 2025", r)
    total = sum(_num(f.get("n")) for f in r.filas)
    for f in r.filas[:5]:
        inf.concluir(f"con.est={f.get('est')} emp={f.get('emp')}: {_pct(_num(f.get('n')), total)} albaranes desde 2025.")
    r = c.leer(SQL["M2_est_sin_facturar"], max_rows=20)
    inf.tabla("est de los no facturados desde 2026-09", r)
    total = sum(_num(f.get("n")) for f in r.filas)
    if r.filas:
        f = r.filas[0]
        inf.concluir(f"Estado ACTUAL más frecuente de los no facturados desde 2026-09: {f.get('est')} en "
                     f"{_pct(_num(f.get('n')), total)} (sesgado: incluye los ya contabilizados; el inicial lo da M13).")
    for nombre in ("M2_conest", "M2_sercon"):
        inf.tabla(nombre, c.leer(SQL[nombre], max_rows=50))
    r = c.leer(SQL["M2_mov_emp"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("mov.emp (doctip 14)", r)
    inf.concluir("mov.emp de los albaranes: " + ", ".join(f"{f.get('emp')}→{_num(f.get('n')):.0f}" for f in r.filas))
    r = c.leer(SQL["M2_indices_con"], max_rows=200)
    inf.tabla("índices de dbo.con", r, limite=60)
    unicos = sorted({f"{f.get('indice')}" for f in r.filas if f.get("unico") in (1, True)})
    inf.concluir("Índices únicos de con: " + (", ".join(unicos) or "ninguno") + " (se busca uno sobre (emp, tip, cod)).")
    return inf


def m3(c: ClienteLectura) -> Informe:
    inf = Informe("M3", "partidas: tipo, desactivadas y códigos repetidos por obra")
    r = c.leer(SQL["M3_partidas_usadas"], max_rows=100, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("partidas usadas en dcapro desde 2025", r)
    total = sum(_num(f.get("n")) for f in r.filas)
    for f in r.filas[:5]:
        inf.concluir(f"obrparpar.tip={f.get('tip')} tipdes={f.get('tipdes')} tipvis={f.get('tipvis')}: {_pct(_num(f.get('n')), total)} líneas.")
    inf.tabla("tipos de obrparpar", c.leer(SQL["M3_tipos"], max_rows=50))
    r = c.leer(SQL["M3_repetidos"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("(obride, cod) repetidos", r)
    inf.concluir(f"Pares (obra, código de partida) repetidos: {_num(r.filas[0].get('repetidos')) if r.filas else -1:.0f}.")
    r = c.leer(SQL["M3_repetidos_imputables"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("(obride, cod) repetidos entre partidas imputables", r)
    f = r.filas[0] if r.filas else {}
    inf.concluir(f"Repetidos entre partidas imputables (tip 1, tipdes 0, tipvis 0/1): {_num(f.get('repetidos')):.0f} "
                 f"pares ({_num(f.get('filas')):.0f} filas); son los que darían `partida_ambigua`.")
    return inf


def m4(c: ClienteLectura) -> Informe:
    inf = Informe("M4", "líneas vinculadas del escritorio con partida o precio distintos del contrato")
    r = c.leer(SQL["M4_vinculadas"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("vinculadas desde 2025", r)
    f = r.filas[0] if r.filas else {}
    n = _num(f.get("n"))
    inf.concluir(f"Partida distinta de la del ctrpro: {_pct(_num(f.get('partida_distinta')), n)} vinculadas.")
    inf.concluir(f"Precio distinto del ctrpro: {_pct(_num(f.get('precio_distinto')), n)} vinculadas.")
    r = c.leer(SQL["M4_nulos_ctrpro"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("NULL en ctrpro", r)
    f = r.filas[0] if r.filas else {}
    inf.concluir(f"ctrpro con paride NULL: {_pct(_num(f.get('paride_null')), _num(f.get('n')))}; "
                 f"cenide NULL: {_num(f.get('cenide_null')):.0f}; caaide NULL: {_num(f.get('caaide_null')):.0f}.")
    return inf


def m5(c: ClienteLectura) -> Informe:
    inf = Informe("M5", "devoluciones reales (dcapro.can < 0) y su mov: ¿regla A o B?")
    r = c.leer(SQL["M5_por_origen"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("negativas por origen", r)
    if not r.filas:
        inf.concluir("NO hay devoluciones reales en Sigrid: se aplica la hipótesis A (decisión del humano) y T24 la verifica.")
        return inf
    m = c.leer(SQL["M5_muestra"], max_rows=MUESTRA_DEVOLUCIONES, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("muestra", m)
    reglas: Counter[str] = Counter()
    for fila in m.filas[:MUESTRA_DEVOLUCIONES]:
        anterior = None
        if fila.get("mov") is not None:
            a = c.leer(SQL["M5_mov_anterior"], [fila.get("proide"), fila.get("almide"), fila.get("mov")], max_rows=1)
            anterior = a.filas[0] if a.filas else None
        regla = regla_devolucion(fila, anterior)
        reglas[regla] += 1
        inf.lineas.append(f"    línea {fila.get('linea')} ({fila.get('cod')}): mov tip={fila.get('tip')} "
                          f"oritip={fila.get('oritip')} destip={fila.get('destip')} → regla {regla}")
    total = sum(reglas.values())
    inf.concluir("Reglas en la muestra: " + ", ".join(f"{k} en {_pct(v, total)}" for k, v in reglas.most_common()) + ".")
    inf.concluir("A = canent negativo y PMP por la fórmula de entrada; B = cansal positivo y PMP sin cambio; "
                 "'?' = ninguna (mirar tip/oritip/destip de la muestra).")
    return inf


def m6(c: ClienteLectura) -> Informe:
    inf = Informe("M6", "vinculadas negativas: signo de ctrprodes.can y canser = Σ ctrprodes")
    r = c.leer(SQL["M6_muestra"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("muestra", r)
    con_signo = sum(1 for f in r.filas if f.get("ctrprodes_can") is not None and _casi(_num(f.get("ctrprodes_can")), _num(f.get("can"))))
    inf.concluir(f"ctrprodes.can igual a la cantidad negativa de la línea: {_pct(con_signo, len(r.filas))} de la muestra.")
    rv = c.leer(SQL["M6_revisadas"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("líneas de contrato con devoluciones", rv)
    rd = c.leer(SQL["M6_descuadres"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("descuadres canser vs Σ ctrprodes", rd)
    rev = rv.filas[0] if rv.filas else {}
    inf.concluir(f"canser ≠ Σ ctrprodes.can en {_num(rd.filas[0].get('descuadres')) if rd.filas else -1:.0f} de "
                 f"{_num(rev.get('lineas_contrato')):.0f} líneas de contrato con devoluciones; "
                 f"con canser < 0: {_num(rev.get('canser_negativo')):.0f}.")
    return inf


def m7(c: ClienteLectura) -> Informe:
    inf = Informe("M7", "¿escribe el escritorio dcapropar en líneas con partida?")
    r = c.leer(SQL["M7_desglose"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("líneas con partida desde 2025", r)
    f = r.filas[0] if r.filas else {}
    n = _num(f.get("lineas"))
    inf.concluir(f"Con fila en dcapropar: {_pct(_num(f.get('con_desglose')), n)}; parcandes ≠ 0: {_pct(_num(f.get('parcandes')), n)}.")
    return inf


def m8(c: ClienteLectura) -> Informe:
    inf = Informe("M8", "almacén de la obra y líneas sin partida")
    r = c.leer(SQL["M8_almacenes_por_obra"], max_rows=50)
    inf.tabla("almacenes por obra", r)
    inf.concluir("Obras por nº de almacenes: " + ", ".join(f"{f.get('n_almacenes')}→{_num(f.get('obras')):.0f}" for f in r.filas))
    r = c.leer(SQL["M8_almacen_del_contrato"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("almacén del contrato", r)
    f = r.filas[0] if r.filas else {}
    inf.concluir(f"ctr.almide es un almacén de su obra en {_pct(_num(f.get('alm_de_su_obra')), _num(f.get('n')))} contratos.")
    r = c.leer(SQL["M8_lineas_sin_partida"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("líneas sin partida desde 2025", r)
    total = sum(_num(x.get("n")) for x in r.filas)
    for x in r.filas[:5]:
        inf.concluir(f"Sin partida → {x.get('tipo')}, alm.paride={x.get('alm_paride')}, centro del almacén={x.get('cen_del_alm')}: {_pct(_num(x.get('n')), total)}.")
    return inf


def _veredicto_mov(con_mov: float, lineas: float) -> str:
    if lineas <= 0:
        return "sin líneas en la ventana"
    tasa, texto = con_mov / lineas, _pct(con_mov, lineas)
    if tasa >= UMBRAL_CASI_TODO:
        return f"SÍ genera mov ({texto})"
    if tasa <= UMBRAL_CASI_NINGUNA:
        return f"NO genera mov ({texto})"
    return f"a veces ({texto})"


def _explica_mov(banderas: list[dict[str, Any]], campo: str) -> tuple[bool, str]:
    """¿Decide `campo` (1 ⇒ casi todas con mov; otro valor ⇒ casi ninguna)?"""
    valores = sorted({str(f.get(campo)) for f in banderas})
    partes, ok = [], bool(valores)
    for v in valores:
        con, n = _suma(banderas, "con_mov", **{campo: v}), _suma(banderas, "lineas", **{campo: v})
        partes.append(f"{campo}={v} → con mov {_pct(con, n)}")
        if n > 0:
            tasa = con / n
            ok = ok and (tasa >= UMBRAL_CASI_TODO if v == "1" else tasa <= UMBRAL_CASI_NINGUNA)
    return ok, ", ".join(partes)


def lectura_m9(banderas: list[dict[str, Any]], genericos: list[dict[str, Any]]) -> list[str]:
    """T0a-bis, M9: ¿qué decide que una línea genere mov? ¿Lo generan los genéricos?"""
    salida = []
    decide = []
    for campo in ("tipmov", "tipinv"):
        ok, detalle = _explica_mov(banderas, campo)
        salida.append(f"pro.{campo}: " + (f"DECIDE si la línea genera mov ({detalle})." if ok
                                           else f"no lo explica solo ({detalle or 'sin datos'})."))
        if ok:
            decide.append(campo)
    salida.append("Lectura automática: " + (f"pro.{decide[0]} DECIDE si la línea genera mov." if decide else
                                            "ni pro.tipmov ni pro.tipinv lo explican solos: mirar las combinaciones "
                                            "(y tipsininv de la cabecera)."))
    for cod in PRODUCTOS_GENERICOS:
        emp1 = _veredicto_mov(_suma(genericos, "con_mov", cod=cod, emp=EMPRESA_GENERICOS),
                              _suma(genericos, "lineas", cod=cod, emp=EMPRESA_GENERICOS))
        todas = _veredicto_mov(_suma(genericos, "con_mov", cod=cod), _suma(genericos, "lineas", cod=cod))
        salida.append(f"{cod} emp {EMPRESA_GENERICOS}: {emp1}; todas las empresas: {todas}.")
    return salida


def m9(c: ClienteLectura) -> Informe:
    desde, hasta = VENTANA_M9
    inf = Informe("M9", f"¿un mov por línea? ¿qué lo decide? (albaranes de {desde} a {hasta})")
    ventana = list(VENTANA_M9)
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    for f in _leer_tabla(c, inf, "M9_por_tipsininv", "por tipsininv", ventana, **kw):
        inf.concluir(f"tipsininv={f.get('tipsininv')}: {_num(f.get('albaranes')):.0f} albaranes, "
                     f"{_num(f.get('lineas')):.0f} líneas, con mov {_pct(_num(f.get('con_mov')), _num(f.get('lineas')))}.")
    for f in _leer_tabla(c, inf, "M9_por_partida", "líneas con mov según partida", ventana, **kw):
        inf.concluir(f"{f.get('tipo')}: con mov {_pct(_num(f.get('con_mov')), _num(f.get('lineas')))}.")
    banderas = _leer_tabla(c, inf, "M9_por_banderas", "líneas con mov según pro.tipmov / pro.tipinv / auxfam.tipinv",
                           ventana, **kw)
    genericos = _leer_tabla(c, inf, "M9_genericos", "líneas con mov de los productos genéricos",
                            [*ventana, *PRODUCTOS_GENERICOS], **kw)
    sin_mov = _leer_tabla(c, inf, "M9_sin_mov_por_producto", "productos de las líneas sin mov", ventana,
                          max_rows=10, timeout_s=TIMEOUT_PESADO_S)
    if sin_mov:
        top = sin_mov[0]
        inf.concluir(f"Producto con más líneas sin mov: {top.get('cod')} (ide {top.get('proide')}, emp {top.get('emp')}, "
                     f"tipmov {top.get('tipmov')}, tipinv {top.get('tipinv')}), {_num(top.get('lineas')):.0f} líneas.")
    for texto in lectura_m9(banderas, genericos):
        inf.concluir(texto)
    return inf


def m10(c: ClienteLectura) -> Informe:
    inf = Informe("M10", "albaranes con fecha atrasada: ¿recalcula el escritorio los mov posteriores?")
    r = c.leer(SQL["M10_atrasados"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("mov de albarán con un mov anterior (por ide) de fecha posterior", r)
    if not r.filas:
        inf.concluir("No hay movimientos de albarán con fecha atrasada desde 2026: sin evidencia.")
        return inf
    vistos: set[tuple[Any, Any]] = set()
    for f in r.filas:
        clave = (f.get("proide"), f.get("almide"))
        if clave in vistos or len(vistos) >= MUESTRA_FECHA_ATRASADA:
            continue
        vistos.add(clave)
        s = c.leer(SQL["M10_serie"], [f.get("proide"), f.get("almide"), f.get("fechor")], max_rows=40)
        inf.tabla(f"serie producto {clave[0]} almacén {clave[1]}", s, limite=10)
        por_fechor = roturas_de_cadena(s.filas)
        por_ide = roturas_de_cadena(sorted(s.filas, key=lambda x: _num(x.get("ide"))))
        inf.concluir(f"Producto {clave[0]}/almacén {clave[1]}: roturas de almcan en orden de fechor={por_fechor}, "
                     f"en orden de ide={por_ide} (el orden con 0 roturas es el que mantiene Sigrid).")
    return inf


def m11(c: ClienteLectura) -> Informe:
    desde, hasta = VENTANA_M11
    inf = Informe("M11", f"productos genéricos (MA9999…) e IVA (líneas de {desde} a {hasta})")
    sql = SQL["M11_productos"].format(**{"in": marcadores(len(PRODUCTOS_GENERICOS))})
    productos = _leer_tabla(c, inf, "M11_productos", "maestro de productos", list(PRODUCTOS_GENERICOS),
                            sql=sql, max_rows=20)
    for f in productos:
        inf.concluir(f"{f.get('cod')}: ide={f.get('ide')} tip={f.get('tip')} emp={f.get('emp')} fecbaj={f.get('fecbaj')} "
                     f"comide={f.get('comide')} ivacomide={f.get('ivacomide')} natide={f.get('natide')}.")
    # Hay un MA9999 (y un QA9999) por empresa (1, 31, 34): se mira cada uno, no el primero que llegue.
    for ma in (f for f in productos if str(f.get("cod", "")).strip().upper() in LISTA_BLANCA_GENERICOS):
        emp, por_producto = ma.get("emp"), [*VENTANA_M11, ma.get("ide")]
        cod = str(ma.get("cod")).strip().upper()
        t = _leer_tabla(c, inf, "M11_total_producto", f"{cod} emp {emp} (ide {ma.get('ide')}): total de líneas",
                        por_producto, max_rows=1, timeout_s=TIMEOUT_PESADO_S)
        if t:
            inf.concluir(f"{cod} emp {emp}: {_num(t[0].get('lineas')):.0f} líneas de albarán en la ventana, "
                         f"de {t[0].get('desde')} a {t[0].get('hasta')}.")
        lp = _leer_tabla(c, inf, "M11_lineas_producto", f"{cod} emp {emp}: combinaciones", por_producto,
                         limite=10, max_rows=30, timeout_s=TIMEOUT_PESADO_S)
        if lp:
            top = lp[0]
            total = sum(_num(x.get("n")) for x in lp)
            inf.concluir(f"{cod} emp {emp}, combinación más frecuente: cueide={top.get('cueide')} "
                         f"ivaide={top.get('ivaide')} natide={top.get('natide')} unimed={top.get('unimed')} en "
                         f"{_pct(_num(top.get('n')), total)}; maestro: comide={ma.get('comide')} "
                         f"ivacomide={ma.get('ivacomide')} natide={ma.get('natide')}.")
        _m11_iva_por_proveedor(c, inf, ma)
    iv = _leer_tabla(c, inf, "M11_iva_usado", "IVA usados en líneas de albarán de la ventana", list(VENTANA_M11),
                     limite=30, max_rows=200, timeout_s=TIMEOUT_PESADO_S)
    total = sum(_num(x.get("lineas")) for x in iv)
    distintos = sum(_num(x.get("ivacuo_distinto")) for x in iv)
    inf.concluir(f"ivacuo ≠ round(tot·iva, 2): {_pct(distintos, total)} líneas de la ventana (dbo.iva.iva es una fracción).")
    return inf


def tasa_mismo_prv(acierto: dict[str, Any]) -> float:
    """Aciertos del mismo proveedor sobre las líneas que TIENEN previa de ese proveedor: la primera
    línea de cada proveedor no puede acertar, y contarla sesgaría contra L8b."""
    base = _num(acierto.get("lineas")) - _num(acierto.get("sin_previa_del_prv"))
    return _num(acierto.get("acierta_mismo_prv")) / base if base > 0 else 0.0


def tasa_cualquiera(acierto: dict[str, Any]) -> float:
    lineas = _num(acierto.get("lineas"))
    return _num(acierto.get("acierta_cualquiera")) / lineas if lineas > 0 else 0.0


def _leer_o_anotar(c: ClienteLectura, inf: Informe, nombre: str, parametros: list[Any] | None = None,
                   *, sql: str | None = None, **kw: Any) -> Resultado | None:
    """T0 se ejecuta una sola vez (H28): una sentencia que falla se anota y el bloque sigue.
    `sql` sustituye a `SQL[nombre]` cuando hay que completarla (listas IN)."""
    try:
        return c.leer(sql or SQL[nombre], parametros, **kw)
    except ErrorDeLectura as exc:
        inf.concluir(f"{nombre} no se pudo leer ({exc}); el resto del bloque sigue.")
        return None


def _leer_tabla(c: ClienteLectura, inf: Informe, nombre: str, titulo: str, parametros: list[Any] | None = None,
                *, limite: int = 40, **kw: Any) -> list[dict[str, Any]]:
    """`_leer_o_anotar` + tabla en el informe. Devuelve las filas ([] si falló)."""
    r = _leer_o_anotar(c, inf, nombre, parametros, **kw)
    if r is None:
        return []
    inf.tabla(titulo, r, limite=limite)
    return r.filas


def lectura_l8b(acierto: dict[str, Any] | None, iva_isp: list[dict[str, Any]]) -> str:
    """Spec v5 §T0, M11 ampliada: ¿justifica la medición L8b (plantilla del mismo proveedor)?"""
    isp1 = {f.get("ivaide") for f in iva_isp if _num(f.get("tipisp")) == 1}
    resto = {f.get("ivaide") for f in iva_isp if _num(f.get("tipisp")) != 1}
    motivos = []
    if acierto and tasa_mismo_prv(acierto) > tasa_cualquiera(acierto):
        motivos.append("acierta más la línea previa del mismo proveedor")
    if isp1 - resto:
        motivos.append("IVA distinto con tipisp 1")
    if motivos:
        return f"L8b JUSTIFICADA ({'; '.join(motivos)})."
    if acierto:
        return "L8b inocua (aciertan igual o menos): se queda."
    return "Sin M11_acierto ni IVA distinto con tipisp 1: L8b ni justificada ni descartada por la medición."


def _m11_iva_por_proveedor(c: ClienteLectura, inf: Informe, ma: dict[str, Any]) -> None:
    """T0a (spec v5, H15; v6 también QA9999): IVA de un genérico de la lista blanca por proveedor,
    ISP y acierto de la línea previa."""
    ide, emp, cod = ma.get("ide"), ma.get("emp"), str(ma.get("cod", "MA9999")).strip().upper()
    por_producto = [*VENTANA_M11, ide]
    r = _leer_o_anotar(c, inf, "M11_iva_por_proveedor", por_producto, max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    if r is not None:
        inf.tabla(f"{cod} emp {emp}: proveedores con más de un IVA en la ventana", r)
        f = r.filas[0] if r.filas else {}
        inf.concluir(f"{cod} emp {emp}: proveedores con más de un IVA "
                     f"{_pct(_num(f.get('con_varios_iva')), _num(f.get('proveedores')))}.")
    isp = _leer_o_anotar(c, inf, "M11_iva_y_isp", por_producto, max_rows=100, timeout_s=TIMEOUT_PESADO_S)
    if isp is not None:
        inf.tabla(f"{cod} emp {emp}: IVA por tipisp", isp, limite=20)
    acierto: dict[str, Any] | None = None
    try:
        a = c.leer(SQL["M11_acierto"], por_producto, max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    except ErrorDeLectura as exc:
        inf.concluir(f"{cod} emp {emp}: M11_acierto (LAG ... OVER) no se pudo leer ({exc}); "
                     "según la spec se queda con las dos primeras.")
    else:
        inf.tabla(f"{cod} emp {emp}: acierto del IVA de la línea previa", a)
        acierto = a.filas[0] if a.filas else {}
        n, sin_previa = _num(acierto.get("lineas")), _num(acierto.get("sin_previa_del_prv"))
        inf.concluir(f"{cod} emp {emp}: acierta el IVA previo del mismo proveedor "
                     f"{_pct(_num(acierto.get('acierta_mismo_prv')), n - sin_previa)} (sobre las líneas con previa "
                     f"del proveedor); el previo de cualquiera {_pct(_num(acierto.get('acierta_cualquiera')), n)}; "
                     f"sin previa del proveedor {sin_previa:.0f}.")
    inf.concluir(f"{cod} emp {emp}: {lectura_l8b(acierto, isp.filas if isp else [])}")


def m12(c: ClienteLectura) -> Informe:
    inf = Informe("M12", "¿mezcla el escritorio líneas sin vincular en albaranes de contrato?")
    r = c.leer(SQL["M12_mezcla"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("albaranes con contrato desde 2025", r)
    f = r.filas[0] if r.filas else {}
    inf.concluir(f"Albaranes con contrato que llevan alguna línea sin vincular: "
                 f"{_pct(_num(f.get('con_lineas_sin_vincular')), _num(f.get('con_contrato')))}.")
    return inf


def m13(c: ClienteLectura) -> Informe:
    inf = Informe("M13", "¿escribe el escritorio una fila de log al crear un albarán?")
    e = c.leer(SQL["M13_est_alta"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("altas de albarán en log desde 2026-09 por est y ori", e)
    total = sum(_num(f.get("n")) for f in e.filas)
    for f in e.filas[:5]:
        inf.concluir(f"Alta en log con est={f.get('est')} ori={f.get('ori')}: {_pct(_num(f.get('n')), total)} "
                     "(est de la fila de alta = estado INICIAL del albarán).")
    k = c.leer(SQL["M13_cobertura"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("albaranes AC desde 2026-09-15 con fila de alta en log", k)
    f = k.filas[0] if k.filas else {}
    inf.concluir(f"Albaranes AC con fecha desde 2026-09-15 que tienen fila de alta en log: "
                 f"{_pct(_num(f.get('con_log')), _num(f.get('albaranes')))}.")
    return inf


def m14(c: ClienteLectura) -> Informe:
    inf = Informe("M14", "diff de columnas frente a AC26/15951 (API) y columnas de la dcapro sin vincular")
    # T0 se ejecuta una sola vez (H28): si una parte falla, se anota y las demás siguen.
    partes = (("comparación con la API", _m14_frente_a_la_api), ("valores de las sin vincular", _m14_sv_valores),
              ("arrastre desde la plantilla", _m14_arrastre), ("pago del albarán anterior", _m14b_pago))
    for nombre, parte in partes:
        try:
            parte(c, inf)
        except ErrorDeLectura as exc:
            inf.concluir(f"M14, {nombre}: no se pudo leer ({exc}); el resto del bloque sigue.")
    return inf


def _m14_frente_a_la_api(c: ClienteLectura, inf: Informe) -> None:
    """Albaranes de contrato del MISMO proveedor frente a AC26/15951 (API), columna a columna."""
    a = c.leer(SQL["M14_api"], [COD_ALBARAN_API], max_rows=1)
    inf.tabla("albarán de la API", a)
    if not a.filas:
        inf.concluir("No está el albarán de la API: no se puede comparar.")
        return
    ide_api = a.filas[0].get("ide")
    e = c.leer(SQL["M14_escritorio"], [ide_api, ide_api], max_rows=3)
    inf.tabla("albaranes del escritorio del mismo proveedor", e)
    ides_esc = [f.get("ide") for f in e.filas]
    # T0a-bis: un fallo de estas dos (el 1205 del 2026-10-05 cayó en una) ya no se lleva la comparación.
    p = _leer_tabla(c, inf, "M14_prv", "forma de pago y efecto frente al maestro del proveedor", max_rows=1,
                    timeout_s=TIMEOUT_PESADO_S)
    if p:
        inf.concluir(f"Albaranes desde 2026-09 con pagide del maestro del proveedor: "
                     f"{_pct(_num(p[0].get('pagide_del_prv')), _num(p[0].get('n')))}; "
                     f"efeide: {_pct(_num(p[0].get('efeide_del_prv')), _num(p[0].get('n')))}.")
    q = _leer_tabla(c, inf, "M14_prepma", "dcapro.prepma frente a su mov", max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    if q:
        inf.concluir(f"dcapro.prepma = PMP resultante del mov en {_pct(_num(q[0].get('igual_pmp_resultante')), _num(q[0].get('n')))}; "
                     f"= mov.prepma en {_pct(_num(q[0].get('igual_prepma_del_mov')), _num(q[0].get('n')))} líneas desde 2026-09.")
    if not ides_esc:
        inf.concluir("No hay albaranes del escritorio del mismo proveedor: no se compara columna a columna.")
        return
    ides = [*ides_esc, ide_api]
    for tabla, clave_doc in (("con", "ide"), ("dca", "ide"), ("dcapro", "docide")):
        sql = SQL[f"M14_{tabla}"].format(**{"in": marcadores(len(ides))})
        r = c.leer(sql, ides, max_rows=500)
        if r.truncado:
            inf.concluir(f"AVISO: {tabla} vino truncado.")
        esc = [f for f in r.filas if f.get(clave_doc) != ide_api]
        api = [f for f in r.filas if f.get(clave_doc) == ide_api]
        inf.lineas.append(f"  [{tabla}] escritorio={len(esc)} filas, API={len(api)} filas")
        dif = columnas_distintas(esc, api, PROPIAS_DEL_DOCUMENTO)
        for col, (v_esc, v_api) in sorted(dif.items()):
            marca = " (lista de reseteo)" if col in LISTA_DE_RESETEO else ""
            inf.lineas.append(f"    {tabla}.{col}{marca}: escritorio={v_esc} API={v_api}")
        inf.concluir(f"{tabla}: columnas cuyo valor en la API no aparece en el escritorio: "
                     + (", ".join(sorted(dif)) or "ninguna") + ".")
        if tabla == "dcapro":
            no_vistas = [col for col in LISTA_DE_RESETEO if col not in dif]
            inf.concluir("Columnas de la lista de reseteo SIN diferencia en esta muestra: " + (", ".join(no_vistas) or "ninguna") + ".")


def lectura_sv_valores(fila: dict[str, Any]) -> list[str]:
    """Spec v5 §T0, M14 ampliada: qué columnas de la lista de reseteo vienen vacías y si `fec` es la
    del albarán. Devuelve las conclusiones."""
    n = _num(fila.get("n"))
    if not n:
        return ["No hay líneas sin vincular desde 2026: sin medición de columnas."]
    # Solo las columnas DE LA LISTA se clasifican (spec §T0 v5 M14); las de fuera (tex), aparte.
    de_la_lista = [col for col, _ in COLUMNAS_SV if col in LISTA_DE_RESETEO]
    vacias = [col for col in de_la_lista if _num(fila.get(col)) / n <= UMBRAL_CASI_NADA]
    llenas = [f"{col} {_pct(_num(fila.get(col)), n)}" for col in de_la_lista if col not in vacias]
    fuera = [f"{col} {_pct(_num(fila.get(col)), n)}" for col, _ in COLUMNAS_SV if col not in LISTA_DE_RESETEO]
    salida = [
        f"Sin vincular de 2026 ({n:.0f} líneas), vacías (≤ 0,1 %) ⇒ reseteo confirmado: " + (", ".join(vacias) or "ninguna") + ".",
        "Con valores ⇒ revisar §Reseteo (v6): " + (", ".join(llenas) or "ninguna") + ".",
        "Fuera de la lista de reseteo (solo informativas): " + (", ".join(fuera) or "ninguna") + ".",
    ]
    igual = _num(fila.get("fec_igual_albaran"))
    if igual / n >= UMBRAL_CASI_TODO:
        salida.append(f"dcapro.fec = fecha del albarán en {_pct(igual, n)} ⇒ §Reseteo debe escribir fec = con.fec (v6).")
    else:
        salida.append(f"dcapro.fec = fecha del albarán en {_pct(igual, n)} (no es la regla general).")
    return salida


def _m14_sv_valores(c: ClienteLectura, inf: Informe) -> None:
    """T0a (spec v5, H11): columnas de la lista de reseteo en la dcapro sin vincular."""
    r = c.leer(SQL["M14_sv_valores"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("sin vincular de 2026: líneas con valor en cada columna", r)
    for texto in lectura_sv_valores(r.filas[0] if r.filas else {}):
        inf.concluir(texto)


def _m14_arrastre(c: ClienteLectura, inf: Informe) -> None:
    """T0a (spec v5, H11): qué no copia el escritorio de la plantilla en las últimas sin vincular."""
    p = c.leer(SQL["M14_sv_ma9999"], ["MA9999", EMPRESA_ARRASTRE], max_rows=5)
    inf.tabla(f"MA9999 de la empresa {EMPRESA_ARRASTRE}", p)
    if not p.filas:
        inf.concluir(f"No está el MA9999 de la empresa {EMPRESA_ARRASTRE}: sin comprobación de arrastre.")
        return
    u = c.leer(SQL["M14_sv_ultimas"], [p.filas[0].get("ide")], max_rows=3, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("últimas sin vincular del MA9999 desde 2026-09", u)
    fuera: Counter[str] = Counter()
    for ult in u.filas:
        linea = c.leer(SQL["M14_sv_linea"], [ult.get("ide")], max_rows=1).filas
        plantilla = c.leer(SQL["M14_sv_plantilla"], [ult.get("proide"), ult.get("ide")], max_rows=1).filas
        if not linea or not plantilla:
            inf.lineas.append(f"    línea {ult.get('ide')}: sin plantilla anterior del producto")
            continue
        inf.lineas.append(f"  [arrastre] línea {ult.get('ide')} frente a su plantilla {plantilla[0].get('ide')}")
        dif = columnas_distintas(plantilla, linea, PROPIAS_DEL_DOCUMENTO - set(LISTA_DE_RESETEO))
        for col, (v_pla, v_lin) in sorted(dif.items()):
            marca = "lista de reseteo" if col in LISTA_DE_RESETEO else "FUERA de la lista"
            inf.lineas.append(f"    dcapro.{col} ({marca}): plantilla={v_pla} línea={v_lin}")
            if col not in LISTA_DE_RESETEO:
                fuera[col] += 1
    inf.concluir("Columnas FUERA de la lista de reseteo que el escritorio no copia de la plantilla "
                 f"(candidatas a añadir, en cuántas de {len(u.filas)} líneas): "
                 + (", ".join(f"{col} ({k})" for col, k in sorted(fuera.items())) or "ninguna") + ".")


def lectura_m14b(fila: dict[str, Any]) -> list[str]:
    """T0a-bis, M14b: ¿acierta más la forma de pago / el efecto del albarán anterior del mismo proveedor
    (regla de la spec) o los del maestro del proveedor? Las dos tasas, sobre los mismos albaranes."""
    n = _num(fila.get("n"))
    base = n - _num(fila.get("sin_previo"))
    if base <= 0:
        return ["Sin albaranes desde 2026-09 con un albarán anterior del mismo proveedor."]
    salida = [f"Albaranes desde 2026-09: {n:.0f}; con albarán anterior del mismo proveedor y empresa: {base:.0f}."]
    for campo in ("pagide", "efeide"):
        previo, maestro = _num(fila.get(f"{campo}_del_previo")), _num(fila.get(f"{campo}_del_prv_con_previo"))
        if previo > maestro:
            veredicto = "acierta más el ALBARÁN ANTERIOR ⇒ la regla de la spec se sostiene"
        elif maestro > previo:
            veredicto = "acierta más el MAESTRO del proveedor ⇒ revisar la regla de cabecera (v6)"
        else:
            veredicto = "empate ⇒ cualquiera de las dos"
        salida.append(f"{campo}: albarán anterior {_pct(previo, base)}, maestro del proveedor {_pct(maestro, base)} "
                      f"(mismos albaranes; el maestro sobre todos: {_pct(_num(fila.get(f'{campo}_del_prv')), n)}). "
                      f"{campo}: {veredicto}.")
    return salida


def _m14b_pago(c: ClienteLectura, inf: Informe) -> None:
    """T0a-bis, M14b: pagide y efeide del albarán anterior del mismo proveedor frente al maestro."""
    r = _leer_tabla(c, inf, "M14b_pago_previo", "pago y efecto: albarán anterior frente al maestro del proveedor",
                    [DESDE_LAG_M14B, DESDE_M14B], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    if r:
        for texto in lectura_m14b(r[0]):
            inf.concluir(texto)


def m15(c: ClienteLectura) -> Informe:
    inf = Informe("M15", "stock negativo en mov desde 2025")
    r = c.leer(SQL["M15_stock_negativo"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("mov con almcan < 0", r)
    f = r.filas[0] if r.filas else {}
    inf.concluir(f"mov con stock resultante negativo desde 2025: {_num(f.get('n')):.0f}, en {_num(f.get('almacenes')):.0f} almacenes.")
    return inf


# ---------------------------------------------------------------------------
# T0a (spec v5, §T0 v5): M16, M17 y M18
# ---------------------------------------------------------------------------
def _suma(filas: list[dict[str, Any]], campo: str, **filtro: Any) -> float:
    """Σ `campo` en las filas cuyo valor coincide (como texto) con cada clave del filtro."""
    return sum(_num(f.get(campo)) for f in filas if all(str(f.get(k)) == str(v) for k, v in filtro.items()))


def _cumple(parte: float, total: float, umbral: float = UMBRAL_CASI_TODO) -> bool:
    return total > 0 and parte / total >= umbral


def _si(ok: bool) -> str:
    return "sí" if ok else "NO"


def lectura_m16(caa_partida: list[dict[str, Any]], caa_alm: list[dict[str, Any]],
                alm_sv: list[dict[str, Any]], ficha: dict[str, Any]) -> list[str]:
    """Spec v5 §T0, M16 «debe salir / decide»: hipótesis de design §Analítica y orden de R15."""
    salida: list[str] = []
    n_sv, caa_sv = _suma(caa_partida, "n", tipo="sin_vincular"), _suma(caa_partida, "caa_de_la_partida", tipo="sin_vincular")
    n_vd = _suma(caa_partida, "n", tipo="vinculada", partida_distinta=1)
    caa_vd = _suma(caa_partida, "caa_de_la_partida", tipo="vinculada", partida_distinta=1)
    n_alm, caa_alm_pro = _suma(caa_alm, "n"), _suma(caa_alm, "caa_pro_del_alm")
    analitica = {
        "caa de la partida en sin vincular con partida": (caa_sv, n_sv),
        "caa de la partida en vinculadas con partida distinta": (caa_vd, n_vd),
        "caa de productos del almacén en líneas sin partida": (caa_alm_pro, n_alm),
    }
    for texto, (parte, total) in analitica.items():
        salida.append(f"{texto}: {_pct(parte, total)} (≥ 95 %: {_si(_cumple(parte, total))}).")
    ok_analitica = all(_cumple(p, t) for p, t in analitica.values())
    salida.append("Hipótesis de design §Analítica: " + ("CONFIRMADA." if ok_analitica else "NO confirmada ⇒ PARADA y v6."))

    def dominante(cabecera: str, campo: str, otro: str) -> bool:
        n, a, b = (_suma(alm_sv, k, cabecera=cabecera) for k in ("n", campo, otro))
        salida.append(f"{cabecera}: {campo} {_pct(a, n)}, {otro} {_pct(b, n)}.")
        return n > 0 and a >= b and a / n >= UMBRAL_DOMINANTE

    ok_ctr = dominante("con_contrato", "alm_del_contrato", "alm_de_la_ficha")
    ok_ficha = dominante("sin_contrato", "alm_de_la_ficha", "alm_del_contrato")
    obras, con_almide, de_su_obra = (_num(ficha.get(k)) for k in ("obras", "con_almide", "almide_de_su_obra"))
    salida.append(f"Ficha de obra: con almide {_pct(con_almide, obras)}, de su obra {_pct(de_su_obra, con_almide)}, "
                  f"con cenide {_pct(_num(ficha.get('con_cenide')), obras)}.")
    ok_r15 = ok_ctr and ok_ficha and _cumple(con_almide, obras) and _cumple(de_su_obra, con_almide)
    salida.append("Orden de R15 (contrato → ficha de obra → único alm): "
                  + ("CONFIRMADO." if ok_r15 else
                     f"NO confirmado (contrato dominante: {_si(ok_ctr)}, ficha dominante: {_si(ok_ficha)}) ⇒ PARADA y v6."))
    salida.append(f"(dominante = ≥ {UMBRAL_DOMINANTE:.0%} de las líneas y no menos que la alternativa; "
                  f"ficha de obra ≥ {UMBRAL_CASI_TODO:.0%}.)".replace("%", " %"))
    return salida


# Candidatas de M16b en orden de desempate: las más específicas primero (a igual proporción, gana la de
# más arriba). Cada una: (columna de M16b_fuentes o M16b_codigos, descripción).
FUENTES_M16B: tuple[tuple[str, str], ...] = (
    ("caa_cero", "caaide = 0"),
    ("pro_gaside", "pro.gaside del producto"),
    ("cen_gaside", "cen.gaside del centro de la línea"),
    ("cab_caaide", "dca.caaide de la cabecera"),
    ("ctr_caaide", "ctr.caaide del contrato de la cabecera"),
    ("par_caaide", "obrparpar.caaide de la partida"),
    ("centro_y_caagascod", "caa del centro con código = auxpronat.caagascod"),
    ("centro_y_cuenta", "caa del centro cuyo código empieza por la cuenta financiera"),
    ("caa_cod_caagascod", "código de caa = auxpronat.caagascod"),
    ("caa_cod_caaexicod", "código de caa = auxpronat.caaexicod"),
    ("caa_cod_cuafaccod", "código de caa = auxpronat.cuafaccod"),
    ("caa_cod_cuenta", "código de caa = cuenta financiera de la línea"),
    ("caa_cod_empieza_por_cuenta", "código de caa empieza por la cuenta financiera"),
    ("caa_cod_contiene_obra", "código de caa contiene el de la obra"),
    ("caa_cod_contiene_centro", "código de caa contiene el del centro"),
    ("caa_del_centro", "caa del centro de la línea (caa.cenide = dcapro.cenide)"),
)


def lectura_m16b(fuentes: list[dict[str, Any]], codigos: list[dict[str, Any]]) -> list[str]:
    """T0a-bis, M16b: por grupo de producto y con/sin partida, qué fuente explica `dcapro.caaide`.
    Domina la de mayor proporción si llega a UMBRAL_DOMINANTE; ≥ UMBRAL_CASI_TODO es «regla»."""
    filas: dict[tuple[str, str], dict[str, Any]] = {}
    for f in [*fuentes, *codigos]:
        filas.setdefault((str(f.get("grupo")), str(f.get("partida"))), {}).update(f)
    if not filas:
        return ["No hay líneas sin vincular desde 2025: sin medición del origen de caaide."]
    salida = []
    for (grupo, partida), f in sorted(filas.items()):
        n = _num(f.get("n"))
        mejor, desc_mejor = 0.0, ""
        for campo, desc in FUENTES_M16B:
            if _num(f.get(campo)) > mejor:
                mejor, desc_mejor = _num(f.get(campo)), desc
        cab = f"{grupo} / {partida} ({n:.0f} líneas): "
        if n > 0 and mejor / n >= UMBRAL_DOMINANTE:
            regla = " ⇒ REGLA" if mejor / n >= UMBRAL_CASI_TODO else ""
            texto = f"domina «{desc_mejor}» {_pct(mejor, n)}{regla}"
        else:
            texto = f"ninguna fuente domina (la mejor: «{desc_mejor or '-'}» {_pct(mejor, n)})"
        extra = ""
        if "cuenta_6xx" in f:
            extra = (f"; cuenta financiera 6XX {_pct(_num(f.get('cuenta_6xx')), n)}, cuenta = auxpronat.cuacomcod "
                     f"{_pct(_num(f.get('cuenta_es_cuacomcod')), n)}")
        salida.append(cab + texto + extra + ".")
    salida.append(f"(domina = la de mayor proporción con ≥ {UMBRAL_DOMINANTE:.0%}; REGLA = ≥ {UMBRAL_CASI_TODO:.0%}.)"
                  .replace("%", " %"))
    return salida


def lectura_muestra_m16b(muestra: list[dict[str, Any]]) -> str:
    """Patrón del código de caa en la muestra TOP 20 (ponderado por líneas)."""
    total = sum(_num(f.get("lineas")) for f in muestra)
    if not total:
        return "Muestra vacía: sin patrón del código de caa."

    def peso(cumple: Callable[[str, dict[str, Any]], bool]) -> float:
        return sum(_num(f.get("lineas")) for f in muestra if cumple(str(f.get("caa_cod") or "").strip(), f))

    def txt(f: dict[str, Any], campo: str) -> str:
        return str(f.get(campo) or "").strip()

    igual = peso(lambda caa, f: bool(caa) and caa == txt(f, "caagascod"))
    obra = peso(lambda caa, f: bool(txt(f, "obra")) and txt(f, "obra") in caa)
    centro = peso(lambda caa, f: bool(txt(f, "centro")) and txt(f, "centro") in caa)
    cuenta = peso(lambda caa, f: bool(txt(f, "cuenta")) and caa.startswith(txt(f, "cuenta")))
    return (f"Muestra TOP 20 ({total:.0f} líneas): código de caa = caagascod {_pct(igual, total)}; "
            f"contiene el código de obra {_pct(obra, total)}; contiene el del centro {_pct(centro, total)}; "
            f"empieza por la cuenta financiera {_pct(cuenta, total)}.")


def m16(c: ClienteLectura) -> Informe:
    inf = Informe("M16", "analítica, almacén y centro de las líneas (H10, H13) y origen de caaide (M16b)")
    kw = {"max_rows": 10, "timeout_s": TIMEOUT_PESADO_S}
    r1 = _leer_tabla(c, inf, "M16_caa_con_partida", "caaide de las líneas con partida desde 2025", **kw)
    r2 = _leer_tabla(c, inf, "M16_caa_almacen", "caaide de las líneas sin partida frente al almacén", **kw)
    r3 = _leer_tabla(c, inf, "M16_almacen_sin_vincular", "almacén y centro de las sin vincular", **kw)
    r4 = _leer_tabla(c, inf, "M16_ficha_obra", "ficha de las obras con albaranes desde 2025", max_rows=1,
                     timeout_s=TIMEOUT_PESADO_S)
    for texto in lectura_m16(r1, r2, r3, r4[0] if r4 else {}):
        inf.concluir(texto)
    grupos = [EMPRESA_GENERICOS, *PRODUCTOS_GENERICOS]
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    fuentes = _leer_tabla(c, inf, "M16b_fuentes", "M16b: origen de caaide en las sin vincular (campos)", grupos, **kw)
    codigos = _leer_tabla(c, inf, "M16b_codigos", "M16b: origen de caaide en las sin vincular (códigos)", grupos, **kw)
    muestra = _leer_tabla(c, inf, "M16b_muestra", "M16b: muestra (caa, naturaleza, obra, centro, cuenta)", **kw)
    for texto in lectura_m16b(fuentes, codigos):
        inf.concluir("M16b " + texto)
    inf.concluir("M16b " + lectura_muestra_m16b(muestra))
    return inf


def lectura_m17(existe: list[dict[str, Any]], marcas: list[dict[str, Any]], estados: set[str]) -> str:
    """Spec v5 §T0, M17 «debe salir / decide»: ¿anular borra, marca o no se sabe?"""
    borran = [str(f.get("ope")) for f in existe if _num(f.get("n")) > 0
              and _num(f.get("con_existe")) / _num(f.get("n")) <= UMBRAL_BORRA]
    if borran:
        return f"Lectura automática: ope {', '.join(borran)} con con_existe ≈ 0 ⇒ anular BORRA: R30 sin cambios."
    todas = bool(existe) and all(_cumple(_num(f.get("con_existe")), _num(f.get("n"))) for f in existe)
    con_fecbaj = _suma(marcas, "n", con_fecbaj=1)
    fuera = sorted({str(f.get("est")) for f in marcas if str(f.get("est")) not in estados})
    if todas and (con_fecbaj > 0 or fuera):
        return ("Lectura automática: con_existe ≈ n y hay marca (fecbaj > 0 en "
                f"{con_fecbaj:.0f} albaranes; est fuera de conest: {', '.join(fuera) or 'ninguno'}) ⇒ anular MARCA: "
                "L11 añade AND <no marcado> y F-053 usa ALB-{id}-{n}.")
    return "Lectura automática: sin ope de baja clara ⇒ se decide con T23 (anulación del albarán de prueba)."


def lectura_m17b(reutiliza: list[dict[str, Any]]) -> str:
    """T0a-bis, M17b: tras una ope 2 sobre un albarán, ¿desaparece el registro (y el cod se reutiliza)
    o sigue el mismo?"""
    n = _suma(reutiliza, "n")
    no_existe = _suma(reutiliza, "n", caso="no_existe")
    reutilizado = _suma(reutiliza, "n", caso="existe_con_alta_posterior")
    sigue = _suma(reutiliza, "n", caso="existe_sin_alta_posterior")
    cifras = (f"no existe {_pct(no_existe, n)}, existe con un alta posterior del mismo cod {_pct(reutilizado, n)}, "
              f"sigue sin alta posterior {_pct(sigue, n)}")
    if _cumple(no_existe + reutilizado, n):
        return (f"Lectura automática M17b: ope 2 ⇒ anular BORRA ({cifras}); "
                f"el cod se reutiliza en {reutilizado:.0f}: R30 sin cambios.")
    if _cumple(sigue, n):
        return f"Lectura automática M17b: ope 2 no borra ⇒ MARCA o no es anulación ({cifras})."
    return f"Lectura automática M17b: no concluyente ({cifras or 'sin ope 2'}) ⇒ se decide con T23."


# Palabras del resumen (`log.res`) que delatan el significado de una ope.
_SIGNIFICADOS_OPE = (
    ("modific", "modificación"), ("impr", "impresión"), ("anul", "anulación"), ("baja", "baja"),
    ("borr", "borrado"), ("elimin", "borrado"), ("estado", "cambio de estado"), ("contab", "contabilización"),
    ("factur", "facturación"), ("consult", "consulta"), ("envi", "envío"), ("correo", "envío"),
    ("mail", "envío"), ("export", "exportación"), ("alta", "alta"),
)


def lectura_ope(res: list[dict[str, Any]]) -> list[str]:
    """T0a-bis, M17b: significado deducible de cada ope ≠ 1 por su resumen más frecuente."""
    salida = []
    for ope in sorted({f.get("ope") for f in res}, key=lambda o: _num(o)):
        top = max((f for f in res if f.get("ope") == ope), key=lambda f: _num(f.get("n")))
        texto = str(top.get("res") or "").strip()
        guess = next((nombre for clave, nombre in _SIGNIFICADOS_OPE if clave in texto.lower()), None)
        detalle = f"(res más frecuente: '{texto}', {_num(top.get('n')):.0f} filas)"
        salida.append(f"ope {ope}: parece «{guess}» {detalle}." if guess
                      else f"ope {ope}: significado no deducible por su resumen {detalle}.")
    return salida


def m17(c: ClienteLectura) -> Informe:
    inf = Informe("M17", "anulación de albaranes: ¿borra o marca? (H9) y reutilización del código (M17b)")
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    for f in _leer_tabla(c, inf, "M17_ope", "operaciones de log sobre albaranes (últimos 1.000.000 ide)", **kw):
        inf.concluir(f"log.ope={f.get('ope')}: {_num(f.get('n')):.0f} filas, de {f.get('desde')} a {f.get('hasta')}.")
    e = _leer_tabla(c, inf, "M17_emp_log", "log.emp de las operaciones que no son alta", **kw)
    sin_emp = sum(_num(f.get("n")) for f in e if f.get("emp") in (0, -1, None))
    existe = _leer_tabla(c, inf, "M17_existe", "¿sigue existiendo el albarán? (JOIN por emp, tip, cod)", **kw)
    if sin_emp > 0:
        inf.concluir(f"log.emp sale 0 o nulo en {sin_emp:.0f} filas: se repite el JOIN solo por tip y cod (spec) "
                     "y la lectura usa esa repetición (un cod repetido entre empresas cuenta de más).")
        existe = _leer_tabla(c, inf, "M17_existe_sin_emp", "¿sigue existiendo el albarán? (JOIN solo por tip, cod)",
                             **kw)
    for f in existe:
        inf.concluir(f"ope={f.get('ope')}: existe {_pct(_num(f.get('con_existe')), _num(f.get('n')))}; "
                     f"con fecbaj {_num(f.get('con_fecbaj')):.0f}.")
    m = _leer_tabla(c, inf, "M17_marcas", "albaranes desde 2025 por est y fecbaj", **kw)
    k = _leer_tabla(c, inf, "M2_conest", "estados de conest (tip 14)", max_rows=50)
    inf.concluir(lectura_m17(existe, m, {str(f.get("est")) for f in k}))
    reutiliza = _leer_tabla(c, inf, "M17b_reutiliza", "M17b: tras ope 2, ¿mismo registro o cod reutilizado?", **kw)
    inf.concluir(lectura_m17b(reutiliza))
    _leer_tabla(c, inf, "M17b_perfil", "M17b: perfil de cada ope (documentos, usuarios, est)", **kw)
    for texto in lectura_ope(_leer_tabla(c, inf, "M17b_res", "M17b: resumen más frecuente por ope", **kw)):
        inf.concluir(texto)
    return inf


def lectura_m18(refent: list[dict[str, Any]], propagacion: dict[str, Any]) -> list[str]:
    """Spec v5 §T0, M18 «debe salir / decide»: ¿está libre `dcapro.refent`?"""
    n, con = _suma(refent, "n"), _suma(refent, "con_refent")
    libre = n > 0 and con / n <= UMBRAL_CASI_NADA
    salida = [f"dcapro.refent informado en {_pct(con, n)} líneas desde 2025 ⇒ "
              + ("LIBRE: se escribe referencia_linea (1-24) y se devuelve en idempotente."
                 if libre else "NO libre (> 0,1 %): no se escribe referencia_linea.")]
    copiada = _num(propagacion.get("copiada"))
    salida.append(f"Líneas de factura de albarán con refent copiado del albarán: {copiada:.0f} de "
                  f"{_num(propagacion.get('n')):.0f}" + (" ⇒ la referencia llegaría a la factura (N9)." if copiada > 0 else "."))
    return salida


def m18(c: ClienteLectura) -> Informe:
    inf = Informe("M18", "uso de dcapro.refent (H18)")
    r = c.leer(SQL["M18_refent"], max_rows=5, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("refent por tipo de línea desde 2025", r)
    for f in r.filas:
        inf.concluir(f"{f.get('tipo')}: refent informado {_pct(_num(f.get('con_refent')), _num(f.get('n')))}.")
    inf.tabla("prefijos de refent más frecuentes", c.leer(SQL["M18_valores"], max_rows=20, timeout_s=TIMEOUT_PESADO_S))
    p = c.leer(SQL["M18_propagacion"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("¿pasa refent del albarán a la factura?", p)
    for texto in lectura_m18(r.filas, p.filas[0] if p.filas else {}):
        inf.concluir(texto)
    return inf


MEDICIONES: dict[str, Callable[[ClienteLectura], Informe]] = {
    "M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5, "M6": m6, "M7": m7, "M8": m8,
    "M9": m9, "M10": m10, "M11": m11, "M12": m12, "M13": m13, "M14": m14, "M15": m15,
    "M16": m16, "M17": m17, "M18": m18,
}


# ---------------------------------------------------------------------------
# Configuración, argumentos y salida
# ---------------------------------------------------------------------------
def leer_dotenv(ruta: Path) -> dict[str, str]:
    valores: dict[str, str] = {}
    if not ruta.exists():
        return valores
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, _, valor = linea.partition("=")
        valores[clave.strip()] = valor.strip().strip('"').strip("'")
    return valores


def cargar_config(entorno: dict[str, str] | None = None, dotenv: Path | None = None) -> tuple[str, str]:
    """(base_url, clave) del entorno o del `.env` de la raíz. Nunca se imprimen."""
    entorno = dict(os.environ) if entorno is None else entorno
    fichero = leer_dotenv(dotenv or RAIZ_REPO / ".env")

    def coger(nombre: str) -> str:
        return entorno.get(nombre) or fichero.get(nombre) or ""

    base, clave = coger("SIGRID_API_BASE_URL"), coger("SIGRID_API_FUNCTION_KEY")
    faltan = [n for n, v in (("SIGRID_API_BASE_URL", base), ("SIGRID_API_FUNCTION_KEY", clave)) if not v]
    if faltan:
        raise SystemExit(f"[ERROR] Falta {', '.join(faltan)} (variable de entorno o .env de la raíz del repositorio).")
    return base, clave


def ruta_de_salida(pedida: str | None, ahora: datetime | None = None) -> Path:
    """Fichero de resultados: por defecto en %TEMP%; nunca dentro del repositorio."""
    ahora = ahora or datetime.now().astimezone()
    ruta = Path(pedida) if pedida else Path(tempfile.gettempdir()) / f"f009_t0_{ahora:%Y%m%d_%H%M%S}.txt"
    ruta = ruta.resolve()
    if ruta == RAIZ_REPO or RAIZ_REPO in ruta.parents:
        raise SystemExit("[ERROR] El fichero de resultados no puede ir dentro del repositorio.")
    return ruta


def analizar_argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="F-009 T0: mediciones M1-M18 de solo lectura por sql/read.")
    p.add_argument("--solo", nargs="+", metavar="Mn", help="Lanza solo estas mediciones (p. ej. --solo M5 M6).")
    p.add_argument("--salida", help="Fichero de resultados (por defecto en %%TEMP%%; nunca dentro del repo).")
    args = p.parse_args(argv)
    if args.solo:
        normal = [s.strip().upper() for s in args.solo]
        malas = [s for s in normal if s not in MEDICIONES]
        if malas:
            p.error(f"medición desconocida: {', '.join(malas)} (válidas: {', '.join(MEDICIONES)})")
        args.solo = normal
    return args


def main(argv: list[str] | None = None) -> int:
    args = analizar_argumentos(argv)
    salida = ruta_de_salida(args.salida)
    base, clave = cargar_config()
    cliente = ClienteLectura(base, clave)
    claves = args.solo or list(MEDICIONES)
    textos = [f"F-009 · T0 · mediciones de solo lectura · {datetime.now().astimezone():%Y-%m-%d %H:%M} · {', '.join(claves)}", ""]
    for k in claves:
        print(f"... {k}", flush=True)
        try:
            texto = MEDICIONES[k](cliente).texto()
        except ErrorDeLectura as exc:
            texto = f"=== {k} === ERROR: {exc}\n"
        print(texto, flush=True)
        textos.append(texto)
        salida.write_text("\n".join(textos), encoding="utf-8")
    print(f"Resultados en: {salida}\nPega ese fichero entero en la conversación.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
