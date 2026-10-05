# scripts/medir_f009_t0.py
"""
F-009 · T0: mediciones M1-M18 de la spec, SOLO LECTURA.

Lanza cada medición como SELECT por `POST /api/sql/read` contra la API
desplegada y escribe, en español, la conclusión que necesita la spec
(`specs/F-009-alta-albaran-compra/`, puntos [Mn]; M16-M18 y las ampliaciones de M11
y M14, de `progress/spec_F-009.md` §T0 v5). No escribe nada en Sigrid,
no llama a ningún endpoint de dominio (ni en dry-run) y no se conecta por SQL.

Configuración (la de los demás scripts de este repositorio): variables de
entorno o, si no están, el `.env` de la raíz del repositorio:
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY
Se cargan en el proceso y NUNCA se imprimen.

Uso:
    python -m scripts.medir_f009_t0                 # M1-M18
    python -m scripts.medir_f009_t0 --solo M5       # una (o varias: --solo M5 M6)
    python -m scripts.medir_f009_t0 --solo M3 M7 M9 M11 M13 M14 M16 M17 M18   # repetición T0b
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
    # Los recuentos por albarán y por línea se agregan ANTES (tablas derivadas) y se unen con
    # LEFT JOIN: un SUM sobre subconsultas escalares da el error 130 de SQL Server.
    "M9_por_tipsininv": (
        "SELECT d.tipsininv, COUNT(*) AS albaranes, SUM(ISNULL(l.n, 0)) AS lineas, SUM(ISNULL(m.n, 0)) AS movs "
        "FROM dbo.dca d JOIN dbo.con c ON c.ide = d.ide "
        "LEFT JOIN (SELECT docide, COUNT(*) AS n FROM dbo.dcapro WHERE docide IN (SELECT ide FROM dbo.con "
        "WHERE tip = 14 AND fec >= 20260701) GROUP BY docide) l ON l.docide = d.ide "
        "LEFT JOIN (SELECT docide, COUNT(*) AS n FROM dbo.mov WHERE doctip = 14 AND docide IN (SELECT ide "
        "FROM dbo.con WHERE tip = 14 AND fec >= 20260701) GROUP BY docide) m ON m.docide = d.ide "
        "WHERE c.tip = 14 AND c.fec >= 20260701 GROUP BY d.tipsininv"
    ),
    "M9_por_partida": (
        "SELECT CASE WHEN ISNULL(p.paride, 0) > 0 THEN 'con_partida' ELSE 'sin_partida' END AS tipo, "
        "COUNT(*) AS lineas, SUM(CASE WHEN m.linide IS NULL THEN 0 ELSE 1 END) AS con_mov "
        "FROM dbo.dcapro p JOIN dbo.con c ON c.ide = p.docide "
        "LEFT JOIN (SELECT DISTINCT docide, linide FROM dbo.mov WHERE doctip = 14 AND docide IN (SELECT ide "
        "FROM dbo.con WHERE tip = 14 AND fec >= 20260701)) m ON m.docide = p.docide AND m.linide = p.ide "
        "WHERE c.tip = 14 AND c.fec >= 20260701 "
        "GROUP BY CASE WHEN ISNULL(p.paride, 0) > 0 THEN 'con_partida' ELSE 'sin_partida' END"
    ),
    # ¿Qué decide que una línea no tenga mov? Banderas del maestro de productos
    # (`pro.tipmov` «Hace movimientos», `pro.tipinv` «Es inventariable») frente al mov real.
    "M9_por_banderas": (
        "SELECT ISNULL(r.tipmov, -1) AS tipmov, ISNULL(r.tipinv, -1) AS tipinv, COUNT(*) AS lineas, "
        "SUM(CASE WHEN m.linide IS NULL THEN 0 ELSE 1 END) AS con_mov "
        "FROM dbo.dcapro p JOIN dbo.con c ON c.ide = p.docide LEFT JOIN dbo.pro r ON r.ide = p.proide "
        "LEFT JOIN (SELECT DISTINCT docide, linide FROM dbo.mov WHERE doctip = 14 AND docide IN (SELECT ide "
        "FROM dbo.con WHERE tip = 14 AND fec >= 20260701)) m ON m.docide = p.docide AND m.linide = p.ide "
        "WHERE c.tip = 14 AND c.fec >= 20260701 GROUP BY ISNULL(r.tipmov, -1), ISNULL(r.tipinv, -1) "
        "ORDER BY lineas DESC"
    ),
    "M9_sin_mov_por_producto": (
        "SELECT TOP 10 p.proide, k.cod, k.emp, COUNT(*) AS lineas FROM dbo.dcapro p "
        "JOIN dbo.con c ON c.ide = p.docide JOIN dbo.con k ON k.ide = p.proide "
        "LEFT JOIN (SELECT DISTINCT docide, linide FROM dbo.mov WHERE doctip = 14 AND docide IN (SELECT ide "
        "FROM dbo.con WHERE tip = 14 AND fec >= 20260701)) m ON m.docide = p.docide AND m.linide = p.ide "
        "WHERE c.tip = 14 AND c.fec >= 20260701 AND m.linide IS NULL GROUP BY p.proide, k.cod, k.emp "
        "ORDER BY lineas DESC"
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
    "M11_lineas_producto": (
        "SELECT TOP 30 d.cueide, d.ivaide, d.natide, d.unimed, d.caaide, COUNT(*) AS n FROM dbo.dcapro d "
        "JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? "
        "GROUP BY d.cueide, d.ivaide, d.natide, d.unimed, d.caaide ORDER BY n DESC"
    ),
    "M11_total_producto": (
        "SELECT COUNT(*) AS lineas, MIN(c.fec) AS desde, MAX(c.fec) AS hasta FROM dbo.dcapro d "
        "JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND d.proide = ?"
    ),
    # Solo los IVA que usan las líneas de albarán de 2026, y si `ivacuo` = round(tot·iva, 2).
    "M11_iva_usado": (
        "SELECT d.ivaide, k.cod, i.iva, COUNT(*) AS lineas, "
        "SUM(CASE WHEN ABS(d.ivacuo - ROUND(d.tot * i.iva, 2)) > 0.011 THEN 1 ELSE 0 END) AS ivacuo_distinto "
        "FROM dbo.dcapro d JOIN dbo.con a ON a.ide = d.docide LEFT JOIN dbo.iva i ON i.ide = d.ivaide "
        "LEFT JOIN dbo.con k ON k.ide = d.ivaide WHERE a.tip = 14 AND a.fec >= 20260101 "
        "GROUP BY d.ivaide, k.cod, i.iva ORDER BY lineas DESC"
    ),
    # T0a (spec v5, H15): IVA de cada MA9999 por proveedor. El recuento por proveedor va en una
    # tabla derivada (regla del error 130).
    "M11_iva_por_proveedor": (
        "SELECT COUNT(*) AS proveedores, SUM(CASE WHEN x.n_iva > 1 THEN 1 ELSE 0 END) AS con_varios_iva "
        "FROM (SELECT a.entide, COUNT(DISTINCT d.ivaide) AS n_iva FROM dbo.dcapro d JOIN dbo.dca a "
        "ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 "
        "AND d.proide = ? GROUP BY a.entide) x"
    ),
    "M11_iva_y_isp": (
        "SELECT a.tipisp, d.ivaide, COUNT(DISTINCT a.entide) AS proveedores, COUNT(*) AS lineas "
        "FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide JOIN dbo.con c ON c.ide = d.docide "
        "WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ? GROUP BY a.tipisp, d.ivaide "
        "ORDER BY lineas DESC"
    ),
    # ¿Acierta más el IVA de la línea anterior del MISMO proveedor que el de la anterior de
    # cualquiera? `LAG ... OVER` en una tabla derivada; si la API la rechaza, m11 lo anota y sigue.
    "M11_acierto": (
        "SELECT COUNT(*) AS lineas, SUM(CASE WHEN x.iva_prev_prv IS NULL THEN 1 ELSE 0 END) AS sin_previa_del_prv, "
        "SUM(CASE WHEN x.ivaide = x.iva_prev_prv THEN 1 ELSE 0 END) AS acierta_mismo_prv, "
        "SUM(CASE WHEN x.ivaide = x.iva_prev THEN 1 ELSE 0 END) AS acierta_cualquiera "
        "FROM (SELECT d.ivaide, LAG(d.ivaide) OVER (PARTITION BY a.entide ORDER BY d.ide) AS iva_prev_prv, "
        "LAG(d.ivaide) OVER (ORDER BY d.ide) AS iva_prev FROM dbo.dcapro d JOIN dbo.dca a ON a.ide = d.docide "
        "JOIN dbo.con c ON c.ide = d.docide WHERE c.tip = 14 AND c.fec >= 20250101 AND d.proide = ?) x"
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


@dataclass
class Resultado:
    filas: list[dict[str, Any]]
    truncado: bool
    segundos: float


class ClienteLectura:
    """Solo `POST /api/sql/read`. Rechaza en local cualquier SQL que no sea lectura."""

    def __init__(self, base_url: str, clave: str, sesion: Any = None) -> None:
        self._url = base_url.rstrip("/") + "/api/sql/read"
        self._cabeceras = {"x-functions-key": clave, "Content-Type": "application/json"}
        if sesion is None:
            import requests  # solo hace falta con red

            sesion = requests.Session()
        self._sesion = sesion

    def leer(self, sql: str, parametros: list[Any] | None = None, *, max_rows: int = 200,
             timeout_s: int = TIMEOUT_NORMAL_S) -> Resultado:
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


def m9(c: ClienteLectura) -> Informe:
    inf = Informe("M9", "¿un mov por línea? (desde 2026-07)")
    r = c.leer(SQL["M9_por_tipsininv"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("por tipsininv", r)
    for f in r.filas:
        inf.concluir(f"tipsininv={f.get('tipsininv')}: {_num(f.get('albaranes')):.0f} albaranes, "
                     f"{_num(f.get('lineas')):.0f} líneas, {_num(f.get('movs')):.0f} mov.")
    r = c.leer(SQL["M9_por_partida"], max_rows=5, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("líneas con mov según partida", r)
    for f in r.filas:
        inf.concluir(f"{f.get('tipo')}: con mov {_pct(_num(f.get('con_mov')), _num(f.get('lineas')))}.")
    r = c.leer(SQL["M9_por_banderas"], max_rows=20, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("líneas con mov según pro.tipmov / pro.tipinv", r)
    for f in r.filas:
        inf.concluir(f"pro.tipmov={f.get('tipmov')} tipinv={f.get('tipinv')}: con mov "
                     f"{_pct(_num(f.get('con_mov')), _num(f.get('lineas')))} líneas.")
    r = c.leer(SQL["M9_sin_mov_por_producto"], max_rows=10, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("productos de las líneas sin mov", r)
    if r.filas:
        top = r.filas[0]
        inf.concluir(f"Producto con más líneas sin mov: {top.get('cod')} (ide {top.get('proide')}, emp {top.get('emp')}), "
                     f"{_num(top.get('lineas')):.0f} líneas.")
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
    inf = Informe("M11", "productos genéricos (MA9999…) e IVA")
    sql = SQL["M11_productos"].format(**{"in": marcadores(len(PRODUCTOS_GENERICOS))})
    r = c.leer(sql, list(PRODUCTOS_GENERICOS), max_rows=20)
    inf.tabla("maestro de productos", r)
    for f in r.filas:
        inf.concluir(f"{f.get('cod')}: ide={f.get('ide')} tip={f.get('tip')} emp={f.get('emp')} fecbaj={f.get('fecbaj')} "
                     f"comide={f.get('comide')} ivacomide={f.get('ivacomide')} natide={f.get('natide')}.")
    # Hay un MA9999 por empresa (1, 31, 34): se mira cada uno, no el primero que llegue.
    for ma in (f for f in r.filas if str(f.get("cod", "")).strip().upper() == "MA9999"):
        t = c.leer(SQL["M11_total_producto"], [ma.get("ide")], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
        inf.tabla(f"MA9999 emp {ma.get('emp')} (ide {ma.get('ide')}): total de líneas", t)
        tot = t.filas[0] if t.filas else {}
        inf.concluir(f"MA9999 emp {ma.get('emp')}: {_num(tot.get('lineas')):.0f} líneas de albarán, "
                     f"de {tot.get('desde')} a {tot.get('hasta')}.")
        lp = c.leer(SQL["M11_lineas_producto"], [ma.get("ide")], max_rows=30, timeout_s=TIMEOUT_PESADO_S)
        inf.tabla(f"MA9999 emp {ma.get('emp')}: combinaciones desde 2025", lp, limite=10)
        if lp.filas:
            top = lp.filas[0]
            total = sum(_num(x.get("n")) for x in lp.filas)
            inf.concluir(f"MA9999 emp {ma.get('emp')}, combinación más frecuente: cueide={top.get('cueide')} "
                         f"ivaide={top.get('ivaide')} natide={top.get('natide')} unimed={top.get('unimed')} en "
                         f"{_pct(_num(top.get('n')), total)}; maestro: comide={ma.get('comide')} "
                         f"ivacomide={ma.get('ivacomide')} natide={ma.get('natide')}.")
        _m11_iva_por_proveedor(c, inf, ma)
    iv = c.leer(SQL["M11_iva_usado"], max_rows=200, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("IVA usados en líneas de albarán de 2026", iv, limite=30)
    total = sum(_num(x.get("lineas")) for x in iv.filas)
    distintos = sum(_num(x.get("ivacuo_distinto")) for x in iv.filas)
    inf.concluir(f"ivacuo ≠ round(tot·iva, 2): {_pct(distintos, total)} líneas de 2026 (dbo.iva.iva es una fracción).")
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
                   **kw: Any) -> Resultado | None:
    """T0 se ejecuta una sola vez (H28): una sentencia nueva que falla se anota y el bloque sigue."""
    try:
        return c.leer(SQL[nombre], parametros, **kw)
    except ErrorDeLectura as exc:
        inf.concluir(f"{nombre} no se pudo leer ({exc}); el resto del bloque sigue.")
        return None


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
    """T0a (spec v5, H15): IVA de un MA9999 por proveedor, ISP y acierto de la línea previa."""
    ide, emp = ma.get("ide"), ma.get("emp")
    r = _leer_o_anotar(c, inf, "M11_iva_por_proveedor", [ide], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    if r is not None:
        inf.tabla(f"MA9999 emp {emp}: proveedores con más de un IVA desde 2025", r)
        f = r.filas[0] if r.filas else {}
        inf.concluir(f"MA9999 emp {emp}: proveedores con más de un IVA "
                     f"{_pct(_num(f.get('con_varios_iva')), _num(f.get('proveedores')))}.")
    isp = _leer_o_anotar(c, inf, "M11_iva_y_isp", [ide], max_rows=100, timeout_s=TIMEOUT_PESADO_S)
    if isp is not None:
        inf.tabla(f"MA9999 emp {emp}: IVA por tipisp", isp, limite=20)
    acierto: dict[str, Any] | None = None
    try:
        a = c.leer(SQL["M11_acierto"], [ide], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    except ErrorDeLectura as exc:
        inf.concluir(f"MA9999 emp {emp}: M11_acierto (LAG ... OVER) no se pudo leer ({exc}); "
                     "según la spec se queda con las dos primeras.")
    else:
        inf.tabla(f"MA9999 emp {emp}: acierto del IVA de la línea previa", a)
        acierto = a.filas[0] if a.filas else {}
        n, sin_previa = _num(acierto.get("lineas")), _num(acierto.get("sin_previa_del_prv"))
        inf.concluir(f"MA9999 emp {emp}: acierta el IVA previo del mismo proveedor "
                     f"{_pct(_num(acierto.get('acierta_mismo_prv')), n - sin_previa)} (sobre las líneas con previa "
                     f"del proveedor); el previo de cualquiera {_pct(_num(acierto.get('acierta_cualquiera')), n)}; "
                     f"sin previa del proveedor {sin_previa:.0f}.")
    inf.concluir(f"MA9999 emp {emp}: {lectura_l8b(acierto, isp.filas if isp else [])}")


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
              ("arrastre desde la plantilla", _m14_arrastre))
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
    p = c.leer(SQL["M14_prv"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("forma de pago y efecto frente al maestro del proveedor", p)
    fp = p.filas[0] if p.filas else {}
    inf.concluir(f"Albaranes desde 2026-09 con pagide del maestro del proveedor: {_pct(_num(fp.get('pagide_del_prv')), _num(fp.get('n')))}; "
                 f"efeide: {_pct(_num(fp.get('efeide_del_prv')), _num(fp.get('n')))}.")
    q = c.leer(SQL["M14_prepma"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("dcapro.prepma frente a su mov", q)
    fq = q.filas[0] if q.filas else {}
    inf.concluir(f"dcapro.prepma = PMP resultante del mov en {_pct(_num(fq.get('igual_pmp_resultante')), _num(fq.get('n')))}; "
                 f"= mov.prepma en {_pct(_num(fq.get('igual_prepma_del_mov')), _num(fq.get('n')))} líneas desde 2026-09.")
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


def m16(c: ClienteLectura) -> Informe:
    inf = Informe("M16", "analítica, almacén y centro de las líneas (H10, H13)")
    r1 = c.leer(SQL["M16_caa_con_partida"], max_rows=10, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("caaide de las líneas con partida desde 2025", r1)
    r2 = c.leer(SQL["M16_caa_almacen"], max_rows=10, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("caaide de las líneas sin partida frente al almacén", r2)
    r3 = c.leer(SQL["M16_almacen_sin_vincular"], max_rows=10, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("almacén y centro de las sin vincular", r3)
    r4 = c.leer(SQL["M16_ficha_obra"], max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("ficha de las obras con albaranes desde 2025", r4)
    for texto in lectura_m16(r1.filas, r2.filas, r3.filas, r4.filas[0] if r4.filas else {}):
        inf.concluir(texto)
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


def m17(c: ClienteLectura) -> Informe:
    inf = Informe("M17", "anulación de albaranes: ¿borra o marca? (H9)")
    r = c.leer(SQL["M17_ope"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("operaciones de log sobre albaranes (últimos 1.000.000 ide)", r)
    for f in r.filas:
        inf.concluir(f"log.ope={f.get('ope')}: {_num(f.get('n')):.0f} filas, de {f.get('desde')} a {f.get('hasta')}.")
    e = c.leer(SQL["M17_emp_log"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("log.emp de las operaciones que no son alta", e)
    sin_emp = sum(_num(f.get("n")) for f in e.filas if f.get("emp") in (0, -1, None))
    x = c.leer(SQL["M17_existe"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("¿sigue existiendo el albarán? (JOIN por emp, tip, cod)", x)
    existe = x.filas
    if sin_emp > 0:
        inf.concluir(f"log.emp sale 0 o nulo en {sin_emp:.0f} filas: se repite el JOIN solo por tip y cod (spec) "
                     "y la lectura usa esa repetición (un cod repetido entre empresas cuenta de más).")
        y = c.leer(SQL["M17_existe_sin_emp"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
        inf.tabla("¿sigue existiendo el albarán? (JOIN solo por tip, cod)", y)
        existe = y.filas
    for f in existe:
        inf.concluir(f"ope={f.get('ope')}: existe {_pct(_num(f.get('con_existe')), _num(f.get('n')))}; "
                     f"con fecbaj {_num(f.get('con_fecbaj')):.0f}.")
    m = c.leer(SQL["M17_marcas"], max_rows=50, timeout_s=TIMEOUT_PESADO_S)
    inf.tabla("albaranes desde 2025 por est y fecbaj", m)
    k = c.leer(SQL["M2_conest"], max_rows=50)
    inf.tabla("estados de conest (tip 14)", k)
    inf.concluir(lectura_m17(existe, m.filas, {str(f.get("est")) for f in k.filas}))
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
