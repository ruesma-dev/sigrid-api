# scripts/medir_f009_t0.py
"""
F-009 · T0: mediciones M1-M19 de la spec, SOLO LECTURA.

Lanza cada medición como SELECT por `POST /api/sql/read` contra la API
desplegada y escribe, en español, la conclusión que necesita la spec
(`specs/F-009-alta-albaran-compra/`, puntos [Mn]; M16-M18 y las ampliaciones de M11
y M14, de `progress/spec_F-009.md` §T0 v5; M9 y M11 por ventanas cortas, M14b, M16b y
M17b, de la segunda pasada T0a-bis; M16c, subbloque de M16, de T0a-ter). No escribe nada en Sigrid, no llama a ningún
endpoint de dominio (ni en dry-run) y no se conecta por SQL.

Configuración (la de los demás scripts de este repositorio): variables de
entorno o, si no están, el `.env` de la raíz del repositorio:
    SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY
Se cargan en el proceso y NUNCA se imprimen.

Uso:
    python -m scripts.medir_f009_t0                 # M1-M19
    python -m scripts.medir_f009_t0 --solo M5       # una (o varias: --solo M5 M6)
    python -m scripts.medir_f009_t0 --solo M3 M7 M9 M11 M13 M14 M16 M17 M18   # repetición T0b
    python -m scripts.medir_f009_t0 --solo M9 M11 M14 M16 M17                  # segunda pasada (T0a-bis)
    python -m scripts.medir_f009_t0 --solo M16                                 # M16c (T0a-ter)
    python -m scripts.medir_f009_t0 --solo M9 M14 M16                          # T0b-ter (M14c, XA9999, numemp)
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
import unicodedata
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
PRODUCTOS_GENERICOS = ("MA9999", "SM9999", "SB9999", "QA9999", "XA9999")
# Spec v6/v7: M11 mide y concluye cada uno por separado; XA9999, P5 de la v7 (lista blanca de despliegue).
LISTA_BLANCA_GENERICOS = ("MA9999", "QA9999", "XA9999")
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
# `pro.tipmov`/`tipinv` son Byte: ISNULL(col, -1) tomaría el tipo de la columna (error 220 con tinyint, 1 con
# bit). Ciclo 1 de revisión de T0a-bis: se convierten antes a int.
_TIPMOV, _TIPINV = "COALESCE(CAST(r.tipmov AS int), -1)", "COALESCE(CAST(r.tipinv AS int), -1)"
_M11_LINEAS = "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide"
_TOL_PRECIO = "0.0001"   # M14c: la de M14_prepma (valores copiados, no recalculados)
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
# `nt`: naturaleza del producto (`pro.natide`); `nl`: la de la línea (`dcapro.natide`, ciclo 1).
_M16B_CODIGOS = (
    "LEFT JOIN dbo.auxpronat nt ON nt.ide = r.natide LEFT JOIN dbo.auxpronat nl ON nl.ide = d.natide "
    "LEFT JOIN dbo.con kc ON kc.ide = d.caaide "
    "LEFT JOIN dbo.con cf ON cf.ide = d.cueide LEFT JOIN dbo.con oc ON oc.ide = d.obride "
    "LEFT JOIN dbo.con ec ON ec.ide = d.cenide"
)


def _caa_es(alias: str, campo: str) -> str:
    """El código de la caa de la línea es el `campo` de la naturaleza `alias` (fragmento fijo)."""
    return f"ISNULL({alias}.{campo}, '') <> '' AND kc.cod = {alias}.{campo}"


_CAA_ES_CAAGASCOD = _caa_es("nt", "caagascod")
_CAA_EMPIEZA_POR_CUENTA = "ISNULL(cf.cod, '') <> '' AND LEFT(kc.cod, LEN(cf.cod)) = cf.cod"
_CAA_DEL_CENTRO = "k.cenide = d.cenide"


# T0a-ter, M16c: la regla que sugiere la muestra de M16b. Códigos de `con`/`auxpronat` recortados (pueden
# ser CHAR). (cenide, código) repetidos entre las caa: ahí la regla no fija UNA caa y no cuenta como acierto.
def _recorta(expr: str) -> str:
    return f"RTRIM(LTRIM({expr}))"


_CAA_REPETIDAS = (
    "(SELECT a2.cenide, RTRIM(LTRIM(c2.cod)) AS cod FROM dbo.caa a2 JOIN dbo.con c2 ON c2.ide = a2.ide "
    "GROUP BY a2.cenide, RTRIM(LTRIM(c2.cod)) HAVING COUNT(*) > 1)"
)


def _une_caa_repetidas(caa: str, caa_cod: str) -> str:
    return f"LEFT JOIN {_CAA_REPETIDAS} u ON u.cenide = {caa}.cenide AND u.cod = {_recorta(caa_cod + '.cod')}"


def _regla_caa(nat: str, codigo: str, caa: str = "k", caa_cod: str = "kc", centro: str = "d.cenide") -> str:
    """La caa (`caa`, su con `caa_cod`) es la del centro de la línea y su código es el de `codigo` (obra o
    centro) + '.' + el `caagascod` de la naturaleza `nat` tras el primer '.'; sin '.' no casa."""
    gas = _recorta(f"{nat}.caagascod")
    return (f"{caa}.cenide = {centro} AND CHARINDEX('.', {gas}) > 0 AND {_recorta(caa_cod + '.cod')} = "
            f"{_recorta(codigo + '.cod')} + '.' + SUBSTRING({gas}, CHARINDEX('.', {gas}) + 1, 24) AND u.cod IS NULL")


# Ciclo 1 de revisión de T0a-ter: L15c busca la cua por (con.emp, cod). La cuenta de la línea solo cuenta como
# acierto si es de la empresa del albarán y (empresa, código) no se repite entre las cua (`w`, como `u`).
_CUA_REPETIDAS = (
    "(SELECT c3.emp, RTRIM(LTRIM(c3.cod)) AS cod FROM dbo.cua a3 JOIN dbo.con c3 ON c3.ide = a3.ide "
    "GROUP BY c3.emp, RTRIM(LTRIM(c3.cod)) HAVING COUNT(*) > 1)"
)
_UNE_CUA_REPETIDAS = f"LEFT JOIN {_CUA_REPETIDAS} w ON w.emp = cf.emp AND w.cod = RTRIM(LTRIM(cf.cod))"


def _cuenta_es_cuacomcod(nat: str) -> str:
    return (f"cf.emp = c.emp AND ISNULL({nat}.cuacomcod, '') <> '' AND {_recorta('cf.cod')} = "
            f"{_recorta(nat + '.cuacomcod')} AND w.cod IS NULL")


def _sin_mod(nat: str) -> str:
    return f"LEFT(LTRIM(ISNULL({nat}.caagascod, '')), 4) <> 'MOD.'"
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

# --- T0a-quater ---------------------------------------------------------------------------------------------
# M14d: mov anterior y siguiente del MISMO producto en cualquier almacén (diccionario: mov.prepma = «Precio Medio
# Compra», del producto; almpma es el del almacén). Por el índice pfhi (producto, fechor): igualdad en proide y rango
# en fechor, desempate por ide. Van en OUTER APPLY TOP 1 (tablas, no subconsultas escalares) dentro de la derivada.
_MOV_ANTERIOR_PRODUCTO = (
    "OUTER APPLY (SELECT TOP 1 p.ide, p.prepma, p.doctip, p.almide FROM dbo.mov p WHERE p.proide = m.proide "
    "AND p.fechor <= m.fechor AND (p.fechor < m.fechor OR p.ide < m.ide) ORDER BY p.fechor DESC, p.ide DESC) a"
)
_MOV_SIGUIENTE_PRODUCTO = (
    "OUTER APPLY (SELECT TOP 1 q.ide, q.prepma, q.doctip FROM dbo.mov q WHERE q.proide = m.proide "
    "AND q.fechor >= m.fechor AND (q.fechor > m.fechor OR q.ide > m.ide) ORDER BY q.fechor, q.ide) s"
)
_M14D_DESDE = (
    f"FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.mov m ON m.docide = d.docide "
    f"AND m.linide = d.ide {_MOV_ANTERIOR_PRODUCTO} {_MOV_SIGUIENTE_PRODUCTO} {_M9_VENTANA} AND m.doctip = 14"
)


def _igual(a: str, b: str) -> str:
    return f"CASE WHEN ABS({a} - {b}) < {_TOL_PRECIO} THEN 1 ELSE 0 END"


# M16d: la regla de M16c (obra o centro) sobre la naturaleza de la línea, y la caa «<obra>.<campo entero>».
_REGLA_M16C_LINEA = f"({_regla_caa('nl', 'oc')}) OR ({_regla_caa('nl', 'ec')})"
_CUMPLE_M16C = f"CASE WHEN {_REGLA_M16C_LINEA} THEN 1 ELSE 0 END"


def _caa_obra_y(campo: str) -> str:
    """La caa del centro de la línea, única por (centro, código), con código = <obra>.<campo entero>."""
    valor = _recorta(campo)
    return (f"k.cenide = d.cenide AND {valor} <> '' AND {_recorta('kc.cod')} = {_recorta('oc.cod')} + '.' + {valor} "
            "AND u.cod IS NULL")


_M16D_UNIVERSO = f"{_M16B_DESDE} {_M16B_CODIGOS} {_une_caa_repetidas('k', 'kc')} {_SIN_VINCULAR_DESDE_2025}"
# Líneas de UN genérico (parámetros: empresa y código) que NO cumplen la regla de M16c.
_M16D_EXCEPCIONES = f"{_M16D_UNIVERSO} AND kp.emp = ? AND kp.cod = ? AND {_CUMPLE_M16C} = 0"
_SUFIJO_CAA = (
    "CASE WHEN CHARINDEX('.', RTRIM(LTRIM(kc.cod))) > 0 THEN SUBSTRING(RTRIM(LTRIM(kc.cod)), "
    "CHARINDEX('.', RTRIM(LTRIM(kc.cod))) + 1, 24) ELSE '(sin punto)' END"
)
_EMPIEZA_POR_OBRA = (
    "CASE WHEN ISNULL(oc.cod, '') <> '' AND LEFT(RTRIM(LTRIM(kc.cod)), LEN(RTRIM(LTRIM(oc.cod))) + 1) = "
    "RTRIM(LTRIM(oc.cod)) + '.' THEN 1 ELSE 0 END"
)
# M16d, MA99 frente a MA1501: líneas sin vincular del genérico (empresa, código) desde DESDE_ALTAS_LOG (`?`).
_ELECCION_COLUMNAS = (
    "COUNT(*) AS lineas, SUM(CASE WHEN ISNULL(d.natide, 0) = ISNULL(r.natide, 0) THEN 1 ELSE 0 END) AS nat_producto, "
    "SUM(CASE WHEN ISNULL(d.natide, 0) <> ISNULL(r.natide, 0) THEN 1 ELSE 0 END) AS otra_nat, "
    f"COUNT(DISTINCT d.natide) AS naturalezas, SUM({_CUMPLE_M16C}) AS cumple_regla"
)
_ELECCION_FILTRO = f"{_SIN_VINCULAR_DESDE_2025} AND kp.emp = ? AND kp.cod = ? AND c.fec >= ?"
# Alta del albarán en log: la ÚLTIMA ope 1 de su (emp, cod) en la ventana (el cod se reutiliza tras borrar, M17b).
_UNE_ALTA_LOG = (
    f"LEFT JOIN {_ALTAS_LOG} al ON al.emp = c.emp AND al.cod = c.cod LEFT JOIN dbo.log l ON l.ide = al.ult_alta"
)
_USUARIO_ALTA = "ISNULL(RTRIM(LTRIM(l.usu)), '')"


def _eleccion(clave: str, union: str = "", agrupa: str | None = None) -> str:
    return (f"SELECT TOP {TOP_ELECCION_M16D} {clave} AS clave, {_ELECCION_COLUMNAS} {_M16B_DESDE} {_M16B_CODIGOS} "
            f"{_une_caa_repetidas('k', 'kc')} {union} {_ELECCION_FILTRO} GROUP BY {agrupa or clave} ORDER BY lineas DESC")


# M19: cod2 recortado; «informado» = no vacío.
def _cod2(alias: str) -> str:
    return f"RTRIM(LTRIM(ISNULL({alias}.cod2, '')))"


_GENERICOS_BLANCA = marcadores(len(LISTA_BLANCA_GENERICOS))
_M19_GENERICOS_DESDE = (
    "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.con kp ON kp.ide = d.proide "
    f"AND kp.emp = ? AND kp.cod IN ({_GENERICOS_BLANCA}) {_UNE_ALTA_LOG}"
)

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
UMBRAL_REGLA_ESCRIBIBLE = 0.95   # M16c: «≥ 95 % ⇒ REGLA escribible» (encargo de T0a-ter)
UMBRAL_REGLA_PREPMA = 0.95       # M14c: «≥ 95 % ⇒ ese es el valor de prepma» (ampliación de T0a-ter, P1)
GENERICO_NATURALEZAS_M16C = "MA9999"   # M16c: qué naturalezas eligen los usuarios en el MA9999 de la empresa 1
# T0a-quater (ejecución del 2026-10-06 00:56): M14d, M16d y M19.
DESDE_ALTAS_LOG = 20250901   # M16d/M19 por usuario: la ventana de log (_VENTANA_LOG) arranca el 2025-08-20 (M17)
GENERICO_XA = "XA9999"       # M16d: su caagascod no lleva '.' y la regla de M16c no casa nunca
GENERICOS_EXCEPCIONES_M16D = (GENERICO_XA, GENERICO_NATURALEZAS_M16C)
UMBRAL_PUREZA_M16D = 0.95    # M16d: «la naturaleza la fija X» si ≥ 95 % de las líneas siguen la mayoritaria de su X
TOP_ELECCION_M16D = 300      # M16d: ítems (obras, proveedores, usuarios) que se traen; la tabla enseña 15
UMBRAL_HEREDA_DNC = 0.95     # M19: «el campo se hereda de la línea de planificación (dncpro)»
# M19: códigos de usuario que delatan un usuario técnico (heurística por el nombre; `usu` no tiene esa marca).
MARCAS_USUARIO_TECNICO = ("API", "SIGRID", "SERVIC", "SVC", "SYNC", "AUTOM", "PRUEBA", "TEST", "SISTEMA", "ADMIN",
                          "_RW", "WEB", "ROBOT")
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
        f"SELECT {_TIPMOV} AS tipmov, {_TIPINV} AS tipinv, COALESCE(CAST(f.tipinv AS int), -1) AS fam_tipinv, {_CON_MOV} "
        f"FROM dbo.con c {_M9_LINEAS_Y_MOV} LEFT JOIN dbo.pro r ON r.ide = d.proide "
        f"LEFT JOIN dbo.auxfam f ON f.ide = r.famide {_M9_VENTANA} "
        f"GROUP BY {_TIPMOV}, {_TIPINV}, COALESCE(CAST(f.tipinv AS int), -1) ORDER BY lineas DESC"
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
    # T0a-ter, M14c (P1 de la spec v7): ¿qué es mov.prepma? Frente al PMP del almacén ANTES de la entrada
    # (almpma del mov anterior del mismo producto y almacén, por fechor e ide: índice pafhi), al PMP resultante
    # (almpma del propio mov) y a pro.prepma. Ventana VENTANA_M9 y mov por `doclin`, como M9. El mov anterior
    # va en un OUTER APPLY TOP 1 (tabla, no subconsulta escalar) dentro de una derivada: solo se suman banderas.
    "M14c_mov_prepma": (
        "SELECT COUNT(*) AS n, SUM(x.sin_anterior) AS sin_anterior, SUM(x.igual_anterior) AS igual_anterior, "
        "SUM(x.igual_resultante) AS igual_resultante, SUM(x.igual_pro_prepma) AS igual_pro_prepma, "
        "SUM(x.anterior_igual_resultante) AS anterior_igual_resultante, SUM(x.prepma_cero) AS prepma_cero, "
        "SUM(x.linea_igual_mov) AS linea_igual_mov "
        "FROM (SELECT CASE WHEN a.almpma IS NULL THEN 1 ELSE 0 END AS sin_anterior, "
        f"CASE WHEN ABS(m.prepma - a.almpma) < {_TOL_PRECIO} THEN 1 ELSE 0 END AS igual_anterior, "
        f"CASE WHEN ABS(m.prepma - m.almpma) < {_TOL_PRECIO} THEN 1 ELSE 0 END AS igual_resultante, "
        f"CASE WHEN ABS(m.prepma - r.prepma) < {_TOL_PRECIO} THEN 1 ELSE 0 END AS igual_pro_prepma, "
        f"CASE WHEN ABS(a.almpma - m.almpma) < {_TOL_PRECIO} THEN 1 ELSE 0 END AS anterior_igual_resultante, "
        f"CASE WHEN ABS(ISNULL(m.prepma, 0)) < {_TOL_PRECIO} THEN 1 ELSE 0 END AS prepma_cero, "
        f"CASE WHEN ABS(d.prepma - m.prepma) < {_TOL_PRECIO} THEN 1 ELSE 0 END AS linea_igual_mov "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.mov m ON m.docide = d.docide "
        "AND m.linide = d.ide LEFT JOIN dbo.pro r ON r.ide = d.proide "
        "OUTER APPLY (SELECT TOP 1 p.almpma FROM dbo.mov p WHERE p.proide = m.proide AND p.almide = m.almide "
        "AND (p.fechor < m.fechor OR (p.fechor = m.fechor AND p.ide < m.ide)) ORDER BY p.fechor DESC, p.ide DESC) a "
        f"{_M9_VENTANA} AND m.doctip = 14) x"
    ),
    # Líneas SIN mov de la misma ventana (H20: las de pro.tipmov 0): dcapro.prepma frente a 0 y a pro.prepma.
    "M14c_sin_mov": (
        f"SELECT {_TIPMOV} AS tipmov, COUNT(*) AS n, "
        f"SUM(CASE WHEN ABS(ISNULL(d.prepma, 0)) < {_TOL_PRECIO} THEN 1 ELSE 0 END) AS prepma_cero, "
        f"SUM(CASE WHEN ISNULL(r.prepma, 0) <> 0 AND ABS(d.prepma - r.prepma) < {_TOL_PRECIO} THEN 1 ELSE 0 END) "
        "AS igual_pro_prepma, SUM(CASE WHEN ISNULL(r.prepma, 0) = 0 THEN 1 ELSE 0 END) AS pro_prepma_cero "
        f"FROM dbo.con c {_M9_LINEAS_Y_MOV} LEFT JOIN dbo.pro r ON r.ide = d.proide {_M9_VENTANA} AND m.ide IS NULL "
        f"GROUP BY {_TIPMOV} ORDER BY n DESC"
    ),
    # T0a-quater, M14d: mov.prepma frente al mov ANTERIOR y al SIGUIENTE del mismo producto en cualquier almacén,
    # a mov.pre, mov.prc y dcapro.pre. Por clase del mov siguiente: si los que no son compra repiten el prepma, es un
    # precio medio de compra del producto que solo cambia con las compras. Misma ventana de un mes que M14c.
    "M14d_prepma_producto": (
        "SELECT x.siguiente, COUNT(*) AS n, SUM(x.sin_anterior) AS sin_anterior, "
        "SUM(x.igual_anterior_producto) AS igual_anterior_producto, "
        "SUM(x.igual_siguiente_producto) AS igual_siguiente_producto, SUM(x.igual_pre) AS igual_pre, "
        "SUM(x.igual_prc) AS igual_prc, SUM(x.igual_dcapro_pre) AS igual_dcapro_pre, "
        "SUM(x.entre_anterior_y_pre) AS entre_anterior_y_pre, SUM(x.anterior_igual_pre) AS anterior_igual_pre, "
        "SUM(x.anterior_igual_siguiente) AS anterior_igual_siguiente, SUM(x.anterior_es_albaran) AS anterior_es_albaran "
        "FROM (SELECT CASE WHEN s.ide IS NULL THEN 'sin_siguiente' WHEN s.doctip = 14 THEN 'albaran_compra' "
        "ELSE 'otro_documento' END AS siguiente, CASE WHEN a.ide IS NULL THEN 1 ELSE 0 END AS sin_anterior, "
        f"{_igual('m.prepma', 'a.prepma')} AS igual_anterior_producto, "
        f"{_igual('m.prepma', 's.prepma')} AS igual_siguiente_producto, {_igual('m.prepma', 'm.pre')} AS igual_pre, "
        f"{_igual('m.prepma', 'm.prc')} AS igual_prc, {_igual('m.prepma', 'd.pre')} AS igual_dcapro_pre, "
        "CASE WHEN a.ide IS NOT NULL AND m.prepma >= (CASE WHEN a.prepma < m.pre THEN a.prepma ELSE m.pre END) "
        f"- {_TOL_PRECIO} AND m.prepma <= (CASE WHEN a.prepma > m.pre THEN a.prepma ELSE m.pre END) + {_TOL_PRECIO} "
        f"THEN 1 ELSE 0 END AS entre_anterior_y_pre, {_igual('a.prepma', 'm.pre')} AS anterior_igual_pre, "
        f"{_igual('a.prepma', 's.prepma')} AS anterior_igual_siguiente, "
        f"CASE WHEN a.doctip = 14 THEN 1 ELSE 0 END AS anterior_es_albaran {_M14D_DESDE}) x "
        "GROUP BY x.siguiente ORDER BY x.siguiente"
    ),
    # Muestra para ver la fórmula a ojo (va a %TEMP%, no al repositorio): los 15 mov de albarán más recientes.
    "M14d_muestra": (
        "SELECT TOP 15 m.ide, m.proide, m.almide, m.canent, m.cansal, m.pre, m.prc, m.prepma, m.almcan, m.almpma, "
        "d.pre AS dcapro_pre, a.prepma AS prepma_anterior, a.doctip AS doctip_anterior, a.almide AS alm_anterior, "
        f"s.prepma AS prepma_siguiente, s.doctip AS doctip_siguiente {_M14D_DESDE} ORDER BY m.ide DESC"
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
        "SUM(x.cuenta_es_cuacomcod) AS cuenta_es_cuacomcod, SUM(x.centro_y_caaexicod) AS centro_y_caaexicod, "
        "SUM(x.lin_caa_cod_caagascod) AS lin_caa_cod_caagascod, SUM(x.lin_caa_cod_caaexicod) AS lin_caa_cod_caaexicod, "
        "SUM(x.lin_centro_y_caagascod) AS lin_centro_y_caagascod, "
        "SUM(x.lin_centro_y_caaexicod) AS lin_centro_y_caaexicod, "
        "SUM(x.nat_linea_igual_producto) AS nat_linea_igual_producto "
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
        "CASE WHEN ISNULL(nt.cuacomcod, '') <> '' AND cf.cod = nt.cuacomcod THEN 1 ELSE 0 END AS cuenta_es_cuacomcod, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_DEL_CENTRO} AND {_caa_es('nt', 'caaexicod')} THEN 1 ELSE 0 END "
        "AS centro_y_caaexicod, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_caa_es('nl', 'caagascod')} THEN 1 ELSE 0 END AS lin_caa_cod_caagascod, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_caa_es('nl', 'caaexicod')} THEN 1 ELSE 0 END AS lin_caa_cod_caaexicod, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_DEL_CENTRO} AND {_caa_es('nl', 'caagascod')} THEN 1 ELSE 0 END "
        "AS lin_centro_y_caagascod, "
        f"CASE WHEN {_CAA_INFORMADA} AND {_CAA_DEL_CENTRO} AND {_caa_es('nl', 'caaexicod')} THEN 1 ELSE 0 END "
        "AS lin_centro_y_caaexicod, "
        "CASE WHEN ISNULL(d.natide, 0) = ISNULL(r.natide, 0) THEN 1 ELSE 0 END AS nat_linea_igual_producto "
        f"{_M16B_DESDE} {_M16B_CODIGOS} {_SIN_VINCULAR_DESDE_2025}) x "
        "GROUP BY x.grupo, x.partida ORDER BY x.grupo, x.partida"
    ),
    # Muestra agregada por frecuencia para ver a ojo el patrón del código de la caa.
    "M16b_muestra": (
        "SELECT TOP 20 kc.cod AS caa_cod, nt.caagascod, nl.caagascod AS caagascod_linea, nt.caaexicod, "
        "oc.cod AS obra, ec.cod AS centro, "
        f"cf.cod AS cuenta, {_CON_SIN_PARTIDA} AS partida, COUNT(*) AS lineas {_M16B_DESDE} {_M16B_CODIGOS} "
        f"{_SIN_VINCULAR_DESDE_2025} AND {_CAA_INFORMADA} "
        f"GROUP BY kc.cod, nt.caagascod, nl.caagascod, nt.caaexicod, oc.cod, ec.cod, cf.cod, {_CON_SIN_PARTIDA} "
        "ORDER BY lineas DESC"
    ),
    # Ciclo 1, obs. (d): ¿reparte el escritorio la analítica en `dcaproana` (1N de dcapro)? Informativa.
    # El reparto se agrega antes por línea (tabla derivada): ningún agregado lleva subconsulta.
    "M16b_dcaproana": (
        "SELECT COUNT(*) AS n, SUM(CASE WHEN x.docproide IS NULL THEN 0 ELSE 1 END) AS con_ana, "
        "SUM(CASE WHEN x.docproide IS NOT NULL AND (x.caa_min <> ISNULL(d.caaide, 0) "
        "OR x.caa_max <> ISNULL(d.caaide, 0)) THEN 1 ELSE 0 END) AS ana_caa_distinta, "
        "SUM(CASE WHEN x.filas > 1 THEN 1 ELSE 0 END) AS ana_varias_filas "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide "
        "LEFT JOIN (SELECT docproide, COUNT(*) AS filas, MIN(ISNULL(caaide, 0)) AS caa_min, "
        "MAX(ISNULL(caaide, 0)) AS caa_max FROM dbo.dcaproana GROUP BY docproide) x ON x.docproide = d.ide "
        f"{_SIN_VINCULAR_DESDE_2025}"
    ),
    # --- T0a-ter, M16c: ¿caa = <obra o centro>.<caagascod tras el '.'> de la naturaleza de la línea? ---
    # Mismo universo y grupos que M16b. Cada regla es una bandera 0/1 por línea en la tabla derivada.
    "M16c_reglas": (
        "SELECT x.grupo, x.partida, COUNT(*) AS n, SUM(x.regla_linea_obra) AS regla_linea_obra, "
        "SUM(x.regla_linea_centro) AS regla_linea_centro, SUM(x.regla_producto_obra) AS regla_producto_obra, "
        "SUM(x.regla_producto_centro) AS regla_producto_centro, SUM(x.cueide_linea) AS cueide_linea, "
        "SUM(x.cueide_producto) AS cueide_producto, SUM(x.linea_sin_mod) AS linea_sin_mod, "
        "SUM(x.linea_sin_punto) AS linea_sin_punto, SUM(x.linea_sin_naturaleza) AS linea_sin_naturaleza, "
        "SUM(x.producto_sin_mod) AS producto_sin_mod, SUM(x.linea_caaexicod) AS linea_caaexicod, "
        "SUM(x.producto_caaexicod) AS producto_caaexicod, SUM(x.caa_repetida) AS caa_repetida, "
        "SUM(x.obra_igual_centro) AS obra_igual_centro, SUM(x.cua_repetida) AS cua_repetida, "
        "SUM(x.cua_de_otra_empresa) AS cua_de_otra_empresa, SUM(x.caa_informada) AS caa_informada "
        f"FROM (SELECT {_GRUPO_GENERICO} AS grupo, {_CON_SIN_PARTIDA} AS partida, "
        f"CASE WHEN {_regla_caa('nl', 'oc')} THEN 1 ELSE 0 END AS regla_linea_obra, "
        f"CASE WHEN {_regla_caa('nl', 'ec')} THEN 1 ELSE 0 END AS regla_linea_centro, "
        f"CASE WHEN {_regla_caa('nt', 'oc')} THEN 1 ELSE 0 END AS regla_producto_obra, "
        f"CASE WHEN {_regla_caa('nt', 'ec')} THEN 1 ELSE 0 END AS regla_producto_centro, "
        f"CASE WHEN {_cuenta_es_cuacomcod('nl')} THEN 1 ELSE 0 END AS cueide_linea, "
        f"CASE WHEN {_cuenta_es_cuacomcod('nt')} THEN 1 ELSE 0 END AS cueide_producto, "
        f"CASE WHEN {_sin_mod('nl')} THEN 1 ELSE 0 END AS linea_sin_mod, "
        "CASE WHEN CHARINDEX('.', ISNULL(nl.caagascod, '')) = 0 THEN 1 ELSE 0 END AS linea_sin_punto, "
        "CASE WHEN nl.ide IS NULL THEN 1 ELSE 0 END AS linea_sin_naturaleza, "
        f"CASE WHEN {_sin_mod('nt')} THEN 1 ELSE 0 END AS producto_sin_mod, "
        "CASE WHEN ISNULL(nl.caaexicod, '') <> '' THEN 1 ELSE 0 END AS linea_caaexicod, "
        "CASE WHEN ISNULL(nt.caaexicod, '') <> '' THEN 1 ELSE 0 END AS producto_caaexicod, "
        "CASE WHEN u.cod IS NULL THEN 0 ELSE 1 END AS caa_repetida, "
        "CASE WHEN RTRIM(LTRIM(oc.cod)) = RTRIM(LTRIM(ec.cod)) THEN 1 ELSE 0 END AS obra_igual_centro, "
        "CASE WHEN w.cod IS NULL THEN 0 ELSE 1 END AS cua_repetida, "
        "CASE WHEN cf.ide IS NOT NULL AND cf.emp <> c.emp THEN 1 ELSE 0 END AS cua_de_otra_empresa, "
        f"CASE WHEN {_CAA_INFORMADA} THEN 1 ELSE 0 END AS caa_informada "
        f"{_M16B_DESDE} {_M16B_CODIGOS} {_une_caa_repetidas('k', 'kc')} {_UNE_CUA_REPETIDAS} "
        f"{_SIN_VINCULAR_DESDE_2025}) x "
        "GROUP BY x.grupo, x.partida ORDER BY x.grupo, x.partida"
    ),
    # Ampliación de T0a-ter, P2: auxpronat.numemp de las naturalezas de la línea en las sin vincular de la
    # empresa del parámetro, desde 2025. Informativa. numemp es Entero (no Byte).
    "M16c_numemp": (
        "SELECT x.clase, COUNT(*) AS lineas, COUNT(DISTINCT x.natide) AS naturalezas, "
        "SUM(x.igual_empresa_obra) AS igual_empresa_obra "
        "FROM (SELECT CASE WHEN nl.ide IS NULL THEN 'sin_naturaleza' WHEN ISNULL(nl.numemp, 0) = 0 THEN 'cero' "
        "WHEN nl.numemp = c.emp THEN 'igual_empresa' ELSE 'otra_empresa' END AS clase, d.natide, "
        "CASE WHEN nl.numemp = oc.emp THEN 1 ELSE 0 END AS igual_empresa_obra "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide LEFT JOIN dbo.auxpronat nl ON nl.ide = d.natide "
        f"LEFT JOIN dbo.con oc ON oc.ide = d.obride {_SIN_VINCULAR_DESDE_2025} AND c.emp = ?) x "
        "GROUP BY x.clase ORDER BY x.clase"
    ),
    # Qué naturalezas ponen los usuarios en las líneas del genérico (parámetros: empresa y código).
    "M16c_naturalezas_ma": (
        "SELECT TOP 15 nl.cod AS nat_cod, nl.res AS nat_res, nl.caagascod, COUNT(*) AS lineas, "
        f"SUM(CASE WHEN {_regla_caa('nl', 'oc')} THEN 1 ELSE 0 END) AS regla_linea_obra, "
        f"SUM(CASE WHEN {_regla_caa('nl', 'ec')} THEN 1 ELSE 0 END) AS regla_linea_centro, "
        f"SUM(CASE WHEN {_regla_caa('nt', 'oc')} THEN 1 ELSE 0 END) AS regla_producto_obra, "
        "SUM(CASE WHEN ISNULL(d.natide, 0) = ISNULL(r.natide, 0) THEN 1 ELSE 0 END) AS igual_producto "
        f"{_M16B_DESDE} {_M16B_CODIGOS} {_une_caa_repetidas('k', 'kc')} {_SIN_VINCULAR_DESDE_2025} "
        "AND kp.emp = ? AND kp.cod = ? GROUP BY nl.cod, nl.res, nl.caagascod ORDER BY lineas DESC"
    ),
    # Control: la misma regla sobre la línea de contrato (ctrpro) de las vinculadas desde 2025, por su clave
    # primaria (como M16_caa_con_partida). Se cuentan líneas de contrato distintas.
    "M16c_vinculadas": (
        "SELECT x.grupo, COUNT(*) AS lineas, COUNT(DISTINCT x.ctrpro) AS ctrpro, "
        "COUNT(DISTINCT CASE WHEN x.caa_informada = 1 THEN x.ctrpro END) AS caa_informada, "
        "COUNT(DISTINCT CASE WHEN x.regla_linea_obra = 1 THEN x.ctrpro END) AS regla_linea_obra, "
        "COUNT(DISTINCT CASE WHEN x.regla_linea_centro = 1 THEN x.ctrpro END) AS regla_linea_centro "
        f"FROM (SELECT {_GRUPO_GENERICO} AS grupo, t.ide AS ctrpro, "
        "CASE WHEN ISNULL(t.caaide, 0) <> 0 THEN 1 ELSE 0 END AS caa_informada, "
        f"CASE WHEN {_regla_caa('tn', 'ot', 'kt', 'ktc', 't.cenide')} THEN 1 ELSE 0 END AS regla_linea_obra, "
        f"CASE WHEN {_regla_caa('tn', 'et', 'kt', 'ktc', 't.cenide')} THEN 1 ELSE 0 END AS regla_linea_centro "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.ctrpro t ON t.ide = d.linoriide "
        "LEFT JOIN dbo.con kp ON kp.ide = d.proide LEFT JOIN dbo.caa kt ON kt.ide = t.caaide "
        "LEFT JOIN dbo.con ktc ON ktc.ide = t.caaide LEFT JOIN dbo.auxpronat tn ON tn.ide = t.natide "
        "LEFT JOIN dbo.con ot ON ot.ide = t.obride LEFT JOIN dbo.con et ON et.ide = t.cenide "
        f"{_une_caa_repetidas('kt', 'ktc')} WHERE c.tip = 14 AND c.fec >= 20250101 AND d.docoritip = 44) x "
        "GROUP BY x.grupo ORDER BY x.grupo"
    ),
    # --- T0a-quater, M16d: XA9999, excepciones de MA9999, candidatas y MA99 frente a MA1501 ---
    "M16d_maestro": (
        "SELECT c.ide, c.cod, c.res, c.emp, c.fecbaj, n.ide AS natide, n.cod AS nat_cod, n.res AS nat_res, "
        "n.caagascod, n.cuacomcod, n.caaexicod, n.cuafaccod FROM dbo.con c JOIN dbo.pro p ON p.ide = c.ide "
        "LEFT JOIN dbo.auxpronat n ON n.ide = p.natide WHERE c.emp = ? AND c.cod = ?"
    ),
    # Líneas del genérico (parámetros) que NO cumplen M16c, agregadas: a ojo, cómo se compone su caa.
    "M16d_excepciones": (
        f"SELECT TOP 20 kc.cod AS caa_cod, nl.cod AS nat_cod, nl.caagascod AS caagascod_linea, oc.cod AS obra, "
        f"{_CON_SIN_PARTIDA} AS partida, COUNT(*) AS lineas {_M16D_EXCEPCIONES} "
        f"GROUP BY kc.cod, nl.cod, nl.caagascod, oc.cod, {_CON_SIN_PARTIDA} ORDER BY lineas DESC"
    ),
    # Lo mismo sin la obra: el sufijo de la caa tras el primer '.', que es lo que la regla tendría que construir.
    "M16d_sufijos": (
        f"SELECT TOP 20 {_SUFIJO_CAA} AS sufijo, nl.cod AS nat_cod, nl.caagascod AS caagascod_linea, "
        f"{_CON_SIN_PARTIDA} AS partida, COUNT(*) AS lineas, COUNT(DISTINCT d.obride) AS obras, "
        f"SUM({_EMPIEZA_POR_OBRA}) AS empieza_por_obra {_M16D_EXCEPCIONES} "
        f"GROUP BY {_SUFIJO_CAA}, nl.cod, nl.caagascod, {_CON_SIN_PARTIDA} ORDER BY lineas DESC"
    ),
    # Candidatas por grupo × partida (universo de M16c). «Anterior» = la sin vincular anterior (por ide) de la misma
    # obra y naturaleza de la línea, o de la misma obra y producto: LAG en la derivada, comparado fuera.
    "M16d_candidatas": (
        "SELECT x.grupo, x.partida, COUNT(*) AS n, SUM(x.regla_actual) AS regla_actual, "
        "SUM(x.caagascod_entero) AS caagascod_entero, SUM(x.obra_natcod) AS obra_natcod, "
        "SUM(CASE WHEN x.regla_actual = 1 OR (x.sin_punto = 1 AND x.caagascod_entero = 1) THEN 1 ELSE 0 END) "
        "AS regla_ampliada, SUM(CASE WHEN x.ant_obra_nat IS NULL THEN 1 ELSE 0 END) AS sin_anterior_obra_nat, "
        "SUM(CASE WHEN x.caaide <> 0 AND x.caaide = x.ant_obra_nat THEN 1 ELSE 0 END) AS anterior_obra_nat, "
        "SUM(CASE WHEN x.ant_obra_pro IS NULL THEN 1 ELSE 0 END) AS sin_anterior_obra_pro, "
        "SUM(CASE WHEN x.caaide <> 0 AND x.caaide = x.ant_obra_pro THEN 1 ELSE 0 END) AS anterior_obra_pro, "
        "SUM(x.caa_informada) AS caa_informada "
        f"FROM (SELECT {_GRUPO_GENERICO} AS grupo, {_CON_SIN_PARTIDA} AS partida, ISNULL(d.caaide, 0) AS caaide, "
        f"{_CUMPLE_M16C} AS regla_actual, "
        f"CASE WHEN {_caa_obra_y('nl.caagascod')} THEN 1 ELSE 0 END AS caagascod_entero, "
        f"CASE WHEN {_caa_obra_y('nl.cod')} THEN 1 ELSE 0 END AS obra_natcod, "
        "CASE WHEN CHARINDEX('.', ISNULL(nl.caagascod, '')) = 0 THEN 1 ELSE 0 END AS sin_punto, "
        f"CASE WHEN {_CAA_INFORMADA} THEN 1 ELSE 0 END AS caa_informada, "
        "LAG(ISNULL(d.caaide, 0)) OVER (PARTITION BY d.obride, d.natide ORDER BY d.ide) AS ant_obra_nat, "
        "LAG(ISNULL(d.caaide, 0)) OVER (PARTITION BY d.obride, d.proide ORDER BY d.ide) AS ant_obra_pro "
        f"{_M16D_UNIVERSO}) x GROUP BY x.grupo, x.partida ORDER BY x.grupo, x.partida"
    ),
    # ¿De qué depende la naturaleza que se pone en el genérico? Por obra, por proveedor (ide, sin nombre) y por
    # usuario del alta en log; nat_producto = la de la ficha del producto (MA1501), otra_nat = la elegida (MA99…).
    "M16d_por_obra": _eleccion("oc.cod"),
    "M16d_por_proveedor": _eleccion("a.entide", "JOIN dbo.dca a ON a.ide = c.ide"),
    "M16d_por_usuario": _eleccion(_USUARIO_ALTA, _UNE_ALTA_LOG),
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
    # --- T0a-quater, M19: planificación de compras (dnc/dncpro), cod2 y altas de los genéricos por usuario ---
    # Sin vincular desde 2025 con línea de planificación: ¿qué se hereda de dncpro? (grupos como M16b, con `?`).
    "M19_dnc": (
        "SELECT x.grupo, COUNT(*) AS n, SUM(x.dncpro_existe) AS dncpro_existe, SUM(x.cod2_linea) AS cod2_linea, "
        "SUM(x.cod2_dncpro) AS cod2_dncpro, SUM(x.cod2_igual) AS cod2_igual, SUM(x.cod2_ambos_vacios) AS cod2_ambos_vacios, "
        "SUM(x.caa_dncpro) AS caa_dncpro, SUM(x.caa_igual) AS caa_igual, SUM(x.pro_igual) AS pro_igual, "
        "SUM(x.nat_dncpro) AS nat_dncpro, SUM(x.nat_igual) AS nat_igual, SUM(x.nat_igual_pro_dncpro) AS nat_igual_pro_dncpro, "
        "SUM(x.paride_igual) AS paride_igual, SUM(x.dncide_igual) AS dncide_igual, SUM(x.obra_igual) AS obra_igual, "
        "SUM(x.cen_igual) AS cen_igual "
        f"FROM (SELECT {_GRUPO_GENERICO} AS grupo, CASE WHEN p.ide IS NULL THEN 0 ELSE 1 END AS dncpro_existe, "
        f"CASE WHEN {_cod2('d')} <> '' THEN 1 ELSE 0 END AS cod2_linea, "
        f"CASE WHEN {_cod2('p')} <> '' THEN 1 ELSE 0 END AS cod2_dncpro, "
        f"CASE WHEN {_cod2('d')} <> '' AND {_cod2('d')} = {_cod2('p')} THEN 1 ELSE 0 END AS cod2_igual, "
        f"CASE WHEN {_cod2('d')} = '' AND {_cod2('p')} = '' THEN 1 ELSE 0 END AS cod2_ambos_vacios, "
        "CASE WHEN ISNULL(p.caaide, 0) <> 0 THEN 1 ELSE 0 END AS caa_dncpro, "
        "CASE WHEN ISNULL(p.caaide, 0) <> 0 AND d.caaide = p.caaide THEN 1 ELSE 0 END AS caa_igual, "
        "CASE WHEN d.proide = p.proide THEN 1 ELSE 0 END AS pro_igual, "
        "CASE WHEN ISNULL(p.natide, 0) <> 0 THEN 1 ELSE 0 END AS nat_dncpro, "
        "CASE WHEN ISNULL(p.natide, 0) <> 0 AND d.natide = p.natide THEN 1 ELSE 0 END AS nat_igual, "
        "CASE WHEN ISNULL(rp.natide, 0) <> 0 AND d.natide = rp.natide THEN 1 ELSE 0 END AS nat_igual_pro_dncpro, "
        "CASE WHEN p.ide IS NOT NULL AND ISNULL(d.paride, 0) = ISNULL(p.paride, 0) THEN 1 ELSE 0 END AS paride_igual, "
        "CASE WHEN d.dncide = p.dncide THEN 1 ELSE 0 END AS dncide_igual, "
        "CASE WHEN n.obride = d.obride THEN 1 ELSE 0 END AS obra_igual, "
        "CASE WHEN ISNULL(p.cenide, 0) <> 0 AND d.cenide = p.cenide THEN 1 ELSE 0 END AS cen_igual "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide LEFT JOIN dbo.con kp ON kp.ide = d.proide "
        "LEFT JOIN dbo.dncpro p ON p.ide = d.dncproide LEFT JOIN dbo.dnc n ON n.ide = p.dncide "
        f"LEFT JOIN dbo.pro rp ON rp.ide = p.proide {_SIN_VINCULAR_DESDE_2025} AND ISNULL(d.dncproide, 0) > 0) x "
        "GROUP BY x.grupo ORDER BY x.grupo"
    ),
    # Sin vincular desde 2025 con cod2: ¿de dónde sale? Candidatas como banderas; las fuentes externas van en tablas
    # derivadas unidas por LEFT JOIN, una fila por clave (no multiplican filas); LAG y COUNT OVER sobre TODAS las sin
    # vincular (la anterior puede no tener cod2) y el filtro «con cod2» fuera. Ciclo 1 de revisión: las «mismo
    # producto» solo aciertan si su clave tiene UN único cod2 (`n_cod2 = 1`, si no, `*_ambigua`); las de «cualquier
    # línea / misma obra» solo dicen que el cod2 existe allí: son propiedades.
    "M19_cod2_origen": (
        "SELECT x.origen_dnc, COUNT(*) AS n, SUM(x.ctr_mismo_producto) AS ctr_mismo_producto, "
        "SUM(x.ctr_cualquier_linea) AS ctr_cualquier_linea, SUM(x.dnc_misma_obra_producto) AS dnc_misma_obra_producto, "
        "SUM(x.dnc_misma_obra) AS dnc_misma_obra, SUM(CASE WHEN x.ant_prv IS NULL THEN 1 ELSE 0 END) AS sin_anterior_prv, "
        "SUM(CASE WHEN x.ant_prv = x.cod2 THEN 1 ELSE 0 END) AS anterior_prv, "
        "SUM(CASE WHEN x.ant_obra_pro IS NULL THEN 1 ELSE 0 END) AS sin_anterior_obra_pro, "
        "SUM(CASE WHEN x.ant_obra_pro = x.cod2 THEN 1 ELSE 0 END) AS anterior_obra_pro, "
        "SUM(x.es_cod_partida) AS es_cod_partida, SUM(x.es_cod_producto) AS es_cod_producto, "
        "SUM(CASE WHEN x.en_albaran > 1 THEN 1 ELSE 0 END) AS repetido_en_albaran, SUM(x.con_contrato) AS con_contrato, "
        "SUM(x.ctr_producto_ambiguo) AS ctr_producto_ambiguo, SUM(x.dnc_obra_producto_ambigua) AS dnc_obra_producto_ambigua "
        "FROM (SELECT CASE WHEN ISNULL(d.dncproide, 0) > 0 THEN 'con_dnc' ELSE 'sin_dnc' END AS origen_dnc, "
        f"{_cod2('d')} AS cod2, CASE WHEN tc.n_cod2 = 1 AND tc.cod2 = {_cod2('d')} THEN 1 ELSE 0 END AS ctr_mismo_producto, "
        "CASE WHEN tc.n_cod2 > 1 THEN 1 ELSE 0 END AS ctr_producto_ambiguo, "
        "CASE WHEN tk.docide IS NULL THEN 0 ELSE 1 END AS ctr_cualquier_linea, "
        f"CASE WHEN dp.n_cod2 = 1 AND dp.cod2 = {_cod2('d')} THEN 1 ELSE 0 END AS dnc_misma_obra_producto, "
        "CASE WHEN dp.n_cod2 > 1 THEN 1 ELSE 0 END AS dnc_obra_producto_ambigua, "
        "CASE WHEN dk.obride IS NULL THEN 0 ELSE 1 END AS dnc_misma_obra, "
        f"CASE WHEN RTRIM(LTRIM(ISNULL(pp.cod, ''))) = {_cod2('d')} THEN 1 ELSE 0 END AS es_cod_partida, "
        f"CASE WHEN RTRIM(LTRIM(ISNULL(kp.cod, ''))) = {_cod2('d')} THEN 1 ELSE 0 END AS es_cod_producto, "
        "CASE WHEN ISNULL(a.ctride, 0) > 0 THEN 1 ELSE 0 END AS con_contrato, "
        f"LAG({_cod2('d')}) OVER (PARTITION BY a.entide ORDER BY d.ide) AS ant_prv, "
        f"LAG({_cod2('d')}) OVER (PARTITION BY d.obride, d.proide ORDER BY d.ide) AS ant_obra_pro, "
        f"COUNT(*) OVER (PARTITION BY d.docide, {_cod2('d')}) AS en_albaran "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.dca a ON a.ide = c.ide "
        "LEFT JOIN dbo.con kp ON kp.ide = d.proide LEFT JOIN dbo.obrparpar pp ON pp.ide = d.paride "
        "LEFT JOIN (SELECT docide, proide, COUNT(DISTINCT RTRIM(LTRIM(cod2))) AS n_cod2, MIN(RTRIM(LTRIM(cod2))) AS cod2 "
        "FROM dbo.ctrpro WHERE ISNULL(cod2, '') <> '' GROUP BY docide, proide) tc "
        "ON tc.docide = a.ctride AND tc.proide = d.proide "
        "LEFT JOIN (SELECT DISTINCT docide, RTRIM(LTRIM(cod2)) AS cod2 FROM dbo.ctrpro WHERE ISNULL(cod2, '') <> '') tk "
        f"ON tk.docide = a.ctride AND tk.cod2 = {_cod2('d')} "
        "LEFT JOIN (SELECT n.obride, p.proide, COUNT(DISTINCT RTRIM(LTRIM(p.cod2))) AS n_cod2, "
        "MIN(RTRIM(LTRIM(p.cod2))) AS cod2 FROM dbo.dncpro p JOIN dbo.dnc n ON n.ide = p.dncide "
        "WHERE ISNULL(p.cod2, '') <> '' GROUP BY n.obride, p.proide) dp ON dp.obride = d.obride AND dp.proide = d.proide "
        "LEFT JOIN (SELECT DISTINCT n.obride, RTRIM(LTRIM(p.cod2)) AS cod2 FROM dbo.dncpro p "
        "JOIN dbo.dnc n ON n.ide = p.dncide WHERE ISNULL(p.cod2, '') <> '') dk ON dk.obride = d.obride "
        f"AND dk.cod2 = {_cod2('d')} {_SIN_VINCULAR_DESDE_2025}) x "
        "WHERE x.cod2 <> '' GROUP BY x.origen_dnc ORDER BY x.origen_dnc"
    ),
    # Los cod2 más frecuentes (forma del valor; sin proveedores, solo cuántos).
    "M19_cod2_valores": (
        f"SELECT TOP 10 {_cod2('d')} AS cod2, COUNT(*) AS lineas, COUNT(DISTINCT d.obride) AS obras, "
        "COUNT(DISTINCT d.proide) AS productos, COUNT(DISTINCT a.entide) AS proveedores, "
        "SUM(CASE WHEN ISNULL(d.dncproide, 0) > 0 THEN 1 ELSE 0 END) AS con_dnc "
        f"FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.dca a ON a.ide = c.ide {_SIN_VINCULAR_DESDE_2025} "
        f"AND {_cod2('d')} <> '' GROUP BY {_cod2('d')} ORDER BY lineas DESC"
    ),
    # Vinculadas desde 2025: cod2, dncide y dncproide de la línea frente a los de su ctrpro (por clave primaria; H35 del
    # contrato v7.1: se copian) y cod2 frente al de la dncpro del contrato. «Igual» exige valor; «ambos 0/vacíos», aparte.
    "M19_vinculadas": (
        f"SELECT COUNT(*) AS n, SUM(CASE WHEN {_cod2('d')} <> '' THEN 1 ELSE 0 END) AS cod2_linea, "
        f"SUM(CASE WHEN {_cod2('t')} <> '' THEN 1 ELSE 0 END) AS cod2_ctrpro, "
        f"SUM(CASE WHEN {_cod2('d')} <> '' AND {_cod2('d')} = {_cod2('t')} THEN 1 ELSE 0 END) AS cod2_igual, "
        f"SUM(CASE WHEN {_cod2('d')} = '' AND {_cod2('t')} = '' THEN 1 ELSE 0 END) AS cod2_ambos_vacios, "
        "SUM(CASE WHEN ISNULL(t.dncproide, 0) > 0 THEN 1 ELSE 0 END) AS ctr_desde_dnc, "
        f"SUM(CASE WHEN {_cod2('d')} <> '' AND {_cod2('d')} = {_cod2('pc')} THEN 1 ELSE 0 END) "
        "AS cod2_igual_dncpro_del_ctr, SUM(CASE WHEN ISNULL(d.dncproide, 0) > 0 THEN 1 ELSE 0 END) AS linea_con_dnc, "
        "SUM(CASE WHEN ISNULL(d.dncproide, 0) <> 0 AND d.dncproide = t.dncproide THEN 1 ELSE 0 END) AS dncproide_igual, "
        "SUM(CASE WHEN ISNULL(d.dncproide, 0) = 0 AND ISNULL(t.dncproide, 0) = 0 THEN 1 ELSE 0 END) "
        "AS dncproide_ambos_cero, "
        "SUM(CASE WHEN ISNULL(d.dncide, 0) <> 0 AND d.dncide = t.dncide THEN 1 ELSE 0 END) AS dncide_igual, "
        "SUM(CASE WHEN ISNULL(d.dncide, 0) = 0 AND ISNULL(t.dncide, 0) = 0 THEN 1 ELSE 0 END) AS dncide_ambos_cero "
        "FROM dbo.con c JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.ctrpro t ON t.ide = d.linoriide "
        "LEFT JOIN dbo.dncpro pc ON pc.ide = t.dncproide "
        "WHERE c.tip = 14 AND c.fec >= 20250101 AND d.docoritip = 44"
    ),
    # Líneas de los genéricos de la lista blanca por usuario del alta del albarán en log (ope 1, la última de su
    # emp y cod en la ventana). '' = sin alta en la ventana: la API no escribe log. De usu solo el código y tipdes.
    "M19_altas_usuario": (
        f"SELECT TOP 40 {_USUARIO_ALTA} AS usu, RTRIM(kp.cod) AS producto, COUNT(*) AS lineas, "
        "COUNT(DISTINCT c.ide) AS albaranes, SUM(CASE WHEN ISNULL(d.docoritip, 0) <> 44 THEN 1 ELSE 0 END) AS sin_vincular, "
        "MIN(c.fec) AS desde, MAX(c.fec) AS hasta, MAX(CASE WHEN s.cod IS NULL THEN 0 ELSE 1 END) AS en_usu, "
        f"MAX(ISNULL(s.tipdes, 0)) AS desactivado {_M19_GENERICOS_DESDE} "
        "LEFT JOIN (SELECT RTRIM(LTRIM(cod)) AS cod, MAX(ISNULL(tipdes, 0)) AS tipdes FROM dbo.usu "
        "GROUP BY RTRIM(LTRIM(cod))) s ON s.cod = RTRIM(LTRIM(l.usu)) WHERE c.tip = 14 AND c.fec >= ? "
        f"GROUP BY {_USUARIO_ALTA}, RTRIM(kp.cod) ORDER BY lineas DESC"
    ),
    # Los albaranes más recientes con líneas de esos genéricos y SIN alta en log (candidatos a la API).
    "M19_sin_alta": (
        "SELECT TOP 10 c.cod, c.fec, c.est, COUNT(*) AS lineas, "
        "SUM(CASE WHEN ISNULL(d.docoritip, 0) <> 44 THEN 1 ELSE 0 END) AS sin_vincular "
        f"{_M19_GENERICOS_DESDE} WHERE c.tip = 14 AND c.fec >= ? AND al.cod IS NULL "
        "GROUP BY c.cod, c.fec, c.est ORDER BY c.fec DESC"
    ),
    # Productos de las líneas del albarán que creó la API (parámetro: su código).
    "M19_api": (
        "SELECT RTRIM(k.cod) AS producto, k.emp, COUNT(*) AS lineas, "
        "SUM(CASE WHEN ISNULL(d.docoritip, 0) = 44 THEN 1 ELSE 0 END) AS vinculadas FROM dbo.con c "
        "JOIN dbo.dcapro d ON d.docide = c.ide JOIN dbo.con k ON k.ide = d.proide WHERE c.tip = 14 AND c.cod = ? "
        "GROUP BY RTRIM(k.cod), k.emp ORDER BY lineas DESC"
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


def lectura_m9(banderas: Filas | None, genericos: Filas | None) -> list[str]:
    """T0a-bis, M9: ¿qué decide que una línea genere mov? ¿Lo generan los genéricos?
    None = la sentencia no se pudo leer: SIN MEDICIÓN, nunca «sin líneas»."""
    salida = []
    if banderas is None:
        salida.append(f"pro.tipmov / pro.tipinv: {sin_medicion('M9_por_banderas', 'M9')}.")
        salida.append("Lectura automática: M9_por_banderas SIN MEDICIÓN ⇒ no se concluye qué decide el mov.")
    else:
        decide = []
        for campo in ("tipmov", "tipinv"):
            ok, detalle = _explica_mov(banderas, campo)
            salida.append(f"pro.{campo}: " + (f"DECIDE si la línea genera mov ({detalle})." if ok
                                               else f"no lo explica solo ({detalle or 'sin líneas en la ventana'})."))
            if ok:
                decide.append(campo)
        if decide:
            salida.append(f"Lectura automática: pro.{decide[0]} DECIDE si la línea genera mov.")
        elif banderas:
            salida.append("Lectura automática: ni pro.tipmov ni pro.tipinv lo explican solos: mirar las "
                          "combinaciones (y tipsininv de la cabecera).")
        else:
            salida.append("Lectura automática: sin líneas en la ventana ⇒ no se concluye qué decide el mov.")
    if genericos is None:
        salida.append(f"Genéricos: {sin_medicion('M9_genericos', 'M9')} ⇒ no se concluye si generan mov.")
        return salida
    # `con.cod` puede venir con espacios (CHAR): se compara recortado, como en m11.
    genericos = [{**f, "cod": str(f.get("cod") or "").strip().upper()} for f in genericos]
    for cod in PRODUCTOS_GENERICOS:
        emp1 = _veredicto_mov(_suma(genericos, "con_mov", cod=cod, emp=EMPRESA_GENERICOS),
                              _suma(genericos, "lineas", cod=cod, emp=EMPRESA_GENERICOS))
        todas = _veredicto_mov(_suma(genericos, "con_mov", cod=cod), _suma(genericos, "lineas", cod=cod))
        salida.append(f"{cod} emp {EMPRESA_GENERICOS}: {emp1}; todas las empresas: {todas}.")
    return salida


def m9(c: ClienteLectura) -> Informe:
    desde, hasta = VENTANA_M9
    inf = Informe("M9", f"¿un mov por línea? ¿qué lo decide? (albaranes de {desde} a {hasta}; genéricos, "
                        f"de {VENTANA_M11[0]} a {VENTANA_M11[1]})")
    ventana = list(VENTANA_M9)
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    for f in _leer_tabla(c, inf, "M9_por_tipsininv", "por tipsininv", ventana, **kw) or []:
        inf.concluir(f"tipsininv={f.get('tipsininv')}: {_num(f.get('albaranes')):.0f} albaranes, "
                     f"{_num(f.get('lineas')):.0f} líneas, con mov {_pct(_num(f.get('con_mov')), _num(f.get('lineas')))}.")
    for f in _leer_tabla(c, inf, "M9_por_partida", "líneas con mov según partida", ventana, **kw) or []:
        inf.concluir(f"{f.get('tipo')}: con mov {_pct(_num(f.get('con_mov')), _num(f.get('lineas')))}.")
    banderas = _leer_tabla(c, inf, "M9_por_banderas", "líneas con mov según pro.tipmov / pro.tipinv / auxfam.tipinv",
                           ventana, **kw)
    # Ciclo 1, obs. (b): los genéricos con la ventana de M11 (tres meses), para que QA9999 tenga líneas.
    genericos = _leer_tabla(c, inf, "M9_genericos", "líneas con mov de los productos genéricos (ventana de M11)",
                            [*VENTANA_M11, *PRODUCTOS_GENERICOS], **kw)
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
    productos = productos or []
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
    if iv is not None:
        total = sum(_num(x.get("lineas")) for x in iv)
        distintos = sum(_num(x.get("ivacuo_distinto")) for x in iv)
        inf.concluir(f"ivacuo ≠ round(tot·iva, 2): {_pct(distintos, total)} líneas de la ventana "
                     "(dbo.iva.iva es una fracción).")
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


Filas = list[dict[str, Any]]


def _leer_tabla(c: ClienteLectura, inf: Informe, nombre: str, titulo: str, parametros: list[Any] | None = None,
                *, limite: int = 40, **kw: Any) -> Filas | None:
    """`_leer_o_anotar` + tabla en el informe. Devuelve las filas, o None si NO se pudo leer: cero filas
    es una medición; None, no (ciclo 1 de revisión: un fallo nunca se lee como dato vacío)."""
    r = _leer_o_anotar(c, inf, nombre, parametros, **kw)
    if r is None:
        return None
    inf.tabla(titulo, r, limite=limite)
    return r.filas


def sin_medicion(nombre: str, clave: str) -> str:
    """Texto de una lectura cuya sentencia no se pudo leer: no se concluye nada de ella."""
    return f"{nombre} SIN MEDICIÓN (falló la lectura; repetir con --solo {clave})"


def lectura_l8b(acierto: dict[str, Any] | None, iva_isp: Filas | None) -> str:
    """Spec v5 §T0, M11 ampliada: ¿justifica la medición L8b (plantilla del mismo proveedor)?
    `iva_isp` None = M11_iva_y_isp no se pudo leer (no es «sin ISP»)."""
    filas = iva_isp or []
    isp1 = {f.get("ivaide") for f in filas if _num(f.get("tipisp")) == 1}
    resto = {f.get("ivaide") for f in filas if _num(f.get("tipisp")) != 1}
    sin_isp = "" if iva_isp is not None else f"{sin_medicion('M11_iva_y_isp', 'M11')}: el motivo ISP no se evaluó"
    motivos = []
    if acierto and tasa_mismo_prv(acierto) > tasa_cualquiera(acierto):
        motivos.append("acierta más la línea previa del mismo proveedor")
    if isp1 - resto:
        motivos.append("IVA distinto con tipisp 1")
    if motivos:
        return f"L8b JUSTIFICADA ({'; '.join(motivos)})." + (f" ({sin_isp}.)" if sin_isp else "")
    if acierto and not sin_isp:
        return "L8b inocua (aciertan igual o menos): se queda."
    if acierto:
        return f"L8b sin decisión: el acierto no la justifica, pero {sin_isp}."
    if sin_isp:
        return "L8b SIN MEDICIÓN: ni M11_acierto ni M11_iva_y_isp se pudieron leer (repetir con --solo M11)."
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
    inf.concluir(f"{cod} emp {emp}: {lectura_l8b(acierto, isp.filas if isp is not None else None)}")


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
    inf = Informe("M14", "diff de columnas frente a AC26/15951 (API), columnas de la dcapro sin vincular y "
                         "valor de prepma (M14c por almacén, M14d por producto)")
    # T0 se ejecuta una sola vez (H28): si una parte falla, se anota y las demás siguen.
    partes = (("comparación con la API", _m14_frente_a_la_api), ("valores de las sin vincular", _m14_sv_valores),
              ("arrastre desde la plantilla", _m14_arrastre), ("pago del albarán anterior", _m14b_pago),
              ("prepma del mov (M14c)", _m14c_prepma), ("prepma del producto (M14d)", _m14d_prepma))
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


def _veredicto_m14c(f: dict[str, Any]) -> str:
    n, base = _num(f.get("n")), _num(f.get("n")) - _num(f.get("sin_anterior"))
    anterior = _cumple(_num(f.get("igual_anterior")), base, UMBRAL_REGLA_PREPMA)
    resultante = _cumple(_num(f.get("igual_resultante")), n, UMBRAL_REGLA_PREPMA)
    if anterior and resultante:
        return "⇒ anterior y resultante a la vez: no discrimina (mirar las que difieren)."
    if anterior:
        return ("⇒ mov.prepma = PMP vigente ANTES de la entrada (hipótesis a): R21 = almpma del mov anterior del "
                "mismo producto y almacén.")
    if resultante:
        return "⇒ mov.prepma = PMP RESULTANTE (almpma del propio mov)."
    if _cumple(_num(f.get("igual_pro_prepma")), n, UMBRAL_REGLA_PREPMA):
        return "⇒ mov.prepma = pro.prepma (hipótesis b) ⇒ PARADA: F-009 no escribe pro (R25)."
    return f"⇒ ninguna llega al {UMBRAL_REGLA_PREPMA:.0%}: no concluyente.".replace("%", " %")


def lectura_m14c(movs: Filas | None, sin_mov: Filas | None) -> list[str]:
    """Ampliación de T0a-ter, M14c (P1): qué valor es mov.prepma y cuál lleva dcapro.prepma en la línea sin mov.
    None = no se pudo leer (SIN MEDICIÓN); [] o n = 0 = cero filas."""
    salida: list[str] = []
    f = (movs or [{}])[0]
    n = _num(f.get("n"))
    if movs is None:
        salida.append(f"M14c mov.prepma: {sin_medicion('M14c_mov_prepma', 'M14')} ⇒ no se concluye qué valor es.")
    elif n <= 0:
        salida.append("M14c mov.prepma: cero filas (ningún mov de albarán en la ventana) ⇒ no se concluye.")
    else:
        base = n - _num(f.get("sin_anterior"))
        salida.append(
            f"M14c mov.prepma ({n:.0f} mov de albarán): = PMP vigente antes de la entrada "
            f"{_pct(_num(f.get('igual_anterior')), base)} (sin mov anterior: {_num(f.get('sin_anterior')):.0f}); "
            f"= PMP resultante {_pct(_num(f.get('igual_resultante')), n)}; = pro.prepma "
            f"{_pct(_num(f.get('igual_pro_prepma')), n)}; anterior = resultante (no discriminan) "
            f"{_pct(_num(f.get('anterior_igual_resultante')), n)}; mov.prepma = 0 {_pct(_num(f.get('prepma_cero')), n)}; "
            f"dcapro.prepma = mov.prepma {_pct(_num(f.get('linea_igual_mov')), n)} {_veredicto_m14c(f)}")
    if sin_mov is None:
        salida.append(f"M14c línea sin mov: {sin_medicion('M14c_sin_mov', 'M14')} ⇒ no se concluye.")
        return salida
    total = _suma(sin_mov, "n")
    if total <= 0:
        salida.append("M14c línea sin mov: cero filas (todas las líneas de la ventana tienen mov).")
        return salida
    cero, pro = _suma(sin_mov, "prepma_cero"), _suma(sin_mov, "igual_pro_prepma")
    if _cumple(cero, total, UMBRAL_REGLA_PREPMA):
        veredicto = "⇒ la línea sin mov lleva prepma 0."
    elif _cumple(pro, total, UMBRAL_REGLA_PREPMA):
        veredicto = "⇒ la línea sin mov lleva pro.prepma."
    else:
        veredicto = "⇒ no concluyente."
    salida.append(f"M14c línea sin mov ({total:.0f} líneas; con pro.tipmov 0: {_suma(sin_mov, 'n', tipmov=0):.0f}): "
                  f"dcapro.prepma = 0 {_pct(cero, total)}; = pro.prepma (≠ 0) {_pct(pro, total)} {veredicto}")
    return salida


def _m14c_prepma(c: ClienteLectura, inf: Informe) -> None:
    kw = {"max_rows": 10, "timeout_s": TIMEOUT_PESADO_S}
    movs = _leer_tabla(c, inf, "M14c_mov_prepma", "M14c: mov.prepma frente al PMP anterior, al resultante y a pro",
                       list(VENTANA_M9), **kw)
    sin_mov = _leer_tabla(c, inf, "M14c_sin_mov", "M14c: dcapro.prepma de las líneas sin mov", list(VENTANA_M9), **kw)
    for texto in lectura_m14c(movs, sin_mov):
        inf.concluir(texto)


# T0a-quater, M14d. Candidatas en orden de desempate: (columna, descripción, base). Base «anterior»/«siguiente» =
# los mov que lo tienen; «n» = todos.
CANDIDATAS_M14D: tuple[tuple[str, str, str], ...] = (
    ("igual_anterior_producto", "prepma del mov anterior del producto (cualquier almacén)", "anterior"),
    ("igual_siguiente_producto", "prepma del mov siguiente del producto (cualquier almacén)", "siguiente"),
    ("igual_pre", "mov.pre", "n"),
    ("igual_prc", "mov.prc", "n"),
    ("igual_dcapro_pre", "dcapro.pre", "n"),
)
_UMBRAL_PREPMA_TXT = f"{UMBRAL_REGLA_PREPMA:.0%}".replace("%", " %")


def lectura_m14d(filas: Filas | None) -> list[str]:
    """T0a-quater, M14d: ¿qué es mov.prepma, mirado por PRODUCTO (cualquier almacén)? None = no se pudo leer
    (SIN MEDICIÓN); [] o n = 0 = cero filas."""
    if filas is None:
        return [f"M14d: {sin_medicion('M14d_prepma_producto', 'M14')} ⇒ no se concluye qué es mov.prepma."]
    n = _suma(filas, "n")
    if n <= 0:
        return ["M14d: cero filas (ningún mov de albarán en la ventana) ⇒ no se concluye."]
    sin_ant, sin_sig = _suma(filas, "sin_anterior"), _suma(filas, "n", siguiente="sin_siguiente")
    bases = {"anterior": n - sin_ant, "siguiente": n - sin_sig, "n": n}
    salida = [(
        f"M14d mov.prepma ({n:.0f} mov de albarán) frente al producto en cualquier almacén: = prepma del mov anterior "
        f"del producto {_pct(_suma(filas, 'igual_anterior_producto'), bases['anterior'])} (sin anterior: {sin_ant:.0f}); "
        f"= prepma del mov siguiente del producto {_pct(_suma(filas, 'igual_siguiente_producto'), bases['siguiente'])} "
        f"(sin siguiente: {sin_sig:.0f}); = mov.pre {_pct(_suma(filas, 'igual_pre'), n)}; = mov.prc "
        f"{_pct(_suma(filas, 'igual_prc'), n)}; = dcapro.pre {_pct(_suma(filas, 'igual_dcapro_pre'), n)}."
    )]
    tasas = [(_suma(filas, campo) / bases[base] if bases[base] > 0 else 0.0, campo, desc, base)
             for campo, desc, base in CANDIDATAS_M14D]
    mejor = max(tasas, key=lambda t: t[0])   # max devuelve la primera de las empatadas: orden de desempate
    empatadas = [t[2] for t in tasas if t is not mejor and t[0] == mejor[0] and mejor[0] > 0]
    cifra = _pct(_suma(filas, mejor[1]), bases[mejor[3]])
    if bases[mejor[3]] > 0 and mejor[0] >= UMBRAL_REGLA_PREPMA:
        salida.append(f"M14d ⇒ mov.prepma = {mejor[2]} ({cifra})"
                      + (f" (empata con: {', '.join(empatadas)})" if empatadas else "") + ".")
    else:
        salida.append(f"M14d ⇒ ninguna candidata llega al {_UMBRAL_PREPMA_TXT}: no concluyente (la mejor: «{mejor[2]}» "
                      f"{cifra}).")
    otro, compra = (_suma(filas, "n", siguiente=k) for k in ("otro_documento", "albaran_compra"))
    igual_otro = _suma(filas, "igual_siguiente_producto", siguiente="otro_documento")
    arrastra = _cumple(igual_otro, otro, UMBRAL_REGLA_PREPMA)
    if otro <= 0:   # ciclo 1 de revisión: sin base no se concluye nada del arrastre
        veredicto = "sin mov siguiente de otro documento: no se mide el arrastre"
    elif arrastra:
        veredicto = ("los mov que no son compra arrastran el prepma: es un precio medio de compra del PRODUCTO que "
                     "solo cambia con las compras (el resultante tras esta entrada)")
    else:
        veredicto = "los mov que no son compra NO arrastran el prepma"
    salida.append(f"M14d mov siguiente que NO es albarán de compra: = mov.prepma {_pct(igual_otro, otro)} ⇒ {veredicto}"
                  + f"; si el siguiente es otro albarán de compra: "
                    f"{_pct(_suma(filas, 'igual_siguiente_producto', siguiente='albaran_compra'), compra)}.")
    salida.append(f"M14d propiedades (no fijan el valor): entre el prepma anterior y mov.pre (compatible con una media "
                  f"ponderada) {_pct(_suma(filas, 'entre_anterior_y_pre'), bases['anterior'])}; anterior = mov.pre (no "
                  f"discriminan) {_pct(_suma(filas, 'anterior_igual_pre'), n)}; anterior = siguiente "
                  f"{_pct(_suma(filas, 'anterior_igual_siguiente'), n)}; el mov anterior es de albarán de compra "
                  f"{_pct(_suma(filas, 'anterior_es_albaran'), n)}.")
    salida.append("M14d: el PMP global resultante no es calculable con una lectura barata (mov guarda el stock por "
                  "almacén, almcan, no el del producto): el prepma del mov siguiente es su sustituto.")
    return salida


def _m14d_prepma(c: ClienteLectura, inf: Informe) -> None:
    kw = {"max_rows": 15, "timeout_s": TIMEOUT_PESADO_S}
    filas = _leer_tabla(c, inf, "M14d_prepma_producto", "M14d: mov.prepma frente al producto (anterior, siguiente, pre)",
                        list(VENTANA_M9), **kw)
    for texto in lectura_m14d(filas):
        inf.concluir(texto)
    _leer_tabla(c, inf, "M14d_muestra", "M14d: muestra de los 15 mov de albarán más recientes", list(VENTANA_M9), **kw)


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


def lectura_m16(caa_partida: Filas | None, caa_alm: Filas | None,
                alm_sv: Filas | None, ficha: dict[str, Any] | None) -> list[str]:
    """Spec v5 §T0, M16 «debe salir / decide»: hipótesis de design §Analítica y orden de R15.
    None = la sentencia no se pudo leer: esa parte sale SIN MEDICIÓN."""
    salida: list[str] = []
    if caa_partida is None or caa_alm is None:
        rotas = [n for n, v in (("M16_caa_con_partida", caa_partida), ("M16_caa_almacen", caa_alm)) if v is None]
        salida.append(f"Hipótesis de design §Analítica: {sin_medicion(' y '.join(rotas), 'M16')} ⇒ no se concluye.")
    else:
        salida.extend(_lectura_analitica(caa_partida, caa_alm))
    if alm_sv is None or ficha is None:
        rotas = [n for n, v in (("M16_almacen_sin_vincular", alm_sv), ("M16_ficha_obra", ficha)) if v is None]
        salida.append(f"Orden de R15: {sin_medicion(' y '.join(rotas), 'M16')} ⇒ no se concluye.")
    else:
        salida.extend(_lectura_r15(alm_sv, ficha))
    return salida


def _lectura_analitica(caa_partida: Filas, caa_alm: Filas) -> list[str]:
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
    return salida


def _lectura_r15(alm_sv: Filas, ficha: dict[str, Any]) -> list[str]:
    salida: list[str] = []

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


# Candidatas de M16b. Ciclo 1 de revisión: solo las IDENTIFICATIVAS (fijan UNA caa y se pueden escribir
# como regla, L15) compiten por «domina» y «⇒ REGLA», en orden de desempate (a igual proporción gana la
# de más arriba y se nombran las empatadas). Las PROPIEDADES (dicen algo de la caa sin fijar cuál) van
# en una línea informativa. Cada una: (columna de M16b_fuentes o M16b_codigos, descripción).
IDENTIFICATIVAS_M16B: tuple[tuple[str, str], ...] = (
    ("caa_cero", "caaide = 0"),
    ("pro_gaside", "pro.gaside del producto"),
    ("cen_gaside", "cen.gaside del centro de la línea"),
    ("cab_caaide", "dca.caaide de la cabecera"),
    ("ctr_caaide", "ctr.caaide del contrato de la cabecera"),
    ("par_caaide", "obrparpar.caaide de la partida"),
    ("lin_centro_y_caagascod", "caa del centro con código = caagascod de la naturaleza de la línea"),
    ("centro_y_caagascod", "caa del centro con código = caagascod de la naturaleza del producto"),
    ("lin_centro_y_caaexicod", "caa del centro con código = caaexicod de la naturaleza de la línea"),
    ("centro_y_caaexicod", "caa del centro con código = caaexicod de la naturaleza del producto"),
    ("lin_caa_cod_caagascod", "código de caa = caagascod de la naturaleza de la línea"),
    ("caa_cod_caagascod", "código de caa = caagascod de la naturaleza del producto"),
    ("lin_caa_cod_caaexicod", "código de caa = caaexicod de la naturaleza de la línea"),
    ("caa_cod_caaexicod", "código de caa = caaexicod de la naturaleza del producto"),
    ("caa_cod_cuafaccod", "código de caa = cuafaccod de la naturaleza del producto"),
    ("caa_cod_cuenta", "código de caa = cuenta financiera de la línea"),
)
PROPIEDADES_M16B: tuple[tuple[str, str], ...] = (
    ("caa_del_centro", "caa del centro de la línea (caa.cenide = dcapro.cenide)"),
    ("centro_y_cuenta", "caa del centro cuyo código empieza por la cuenta financiera"),
    ("caa_cod_empieza_por_cuenta", "código de caa empieza por la cuenta financiera"),
    ("caa_cod_contiene_obra", "código de caa contiene el de la obra"),
    ("caa_cod_contiene_centro", "código de caa contiene el del centro"),
)


def _lectura_grupo_m16b(grupo: str, partida: str, f: dict[str, Any]) -> list[str]:
    n = _num(f.get("n"))
    cab = f"{grupo} / {partida} ({n:.0f} líneas): "
    mejor, desc_mejor = 0.0, ""
    for campo, desc in IDENTIFICATIVAS_M16B:
        if _num(f.get(campo)) > mejor:
            mejor, desc_mejor = _num(f.get(campo)), desc
    empatadas = [desc for campo, desc in IDENTIFICATIVAS_M16B
                 if desc != desc_mejor and mejor > 0 and _num(f.get(campo)) == mejor]
    empate = f" (empata con: {', '.join(empatadas)})" if empatadas else ""
    if n > 0 and mejor / n >= UMBRAL_DOMINANTE:
        regla = " ⇒ REGLA" if mejor / n >= UMBRAL_CASI_TODO else ""
        texto = f"domina «{desc_mejor}» {_pct(mejor, n)}{regla}{empate}"
    else:
        texto = f"ninguna identificativa domina (la mejor: «{desc_mejor or '-'}» {_pct(mejor, n)}){empate}"
    extra = ""
    if "cuenta_6xx" in f:
        extra = (f"; cuenta financiera 6XX {_pct(_num(f.get('cuenta_6xx')), n)}, cuenta = auxpronat.cuacomcod "
                 f"{_pct(_num(f.get('cuenta_es_cuacomcod')), n)}, naturaleza de la línea = la del producto "
                 f"{_pct(_num(f.get('nat_linea_igual_producto')), n)}")
    salida = [cab + texto + extra + "."]
    props = [f"{desc} {_pct(_num(f.get(campo)), n)}" for campo, desc in PROPIEDADES_M16B if campo in f]
    if props:
        salida.append(f"{grupo} / {partida}: propiedades (no fijan la caa): {'; '.join(props)}.")
    return salida


def lectura_m16b(fuentes: Filas | None, codigos: Filas | None) -> list[str]:
    """T0a-bis, M16b: por grupo de producto y con/sin partida, qué fuente IDENTIFICATIVA explica
    `dcapro.caaide`. Domina la de mayor proporción si llega a UMBRAL_DOMINANTE; ≥ UMBRAL_CASI_TODO es
    «regla». None = la sentencia no se pudo leer (SIN MEDICIÓN, nunca «no hay líneas»)."""
    rotas = [n for n, v in (("M16b_fuentes", fuentes), ("M16b_codigos", codigos)) if v is None]
    avisos = [f"{sin_medicion(n, 'M16')}: sus candidatas no compiten." for n in rotas]
    filas: dict[tuple[str, str], dict[str, Any]] = {}
    for f in [*(fuentes or []), *(codigos or [])]:
        filas.setdefault((str(f.get("grupo")), str(f.get("partida"))), {}).update(f)
    if not filas:
        if rotas:
            return [*avisos, "No se concluye el origen de caaide."]
        return ["No hay líneas sin vincular desde 2025: sin medición del origen de caaide."]
    salida = list(avisos)
    for (grupo, partida), f in sorted(filas.items()):
        salida.extend(_lectura_grupo_m16b(grupo, partida, f))
    salida.append(f"(domina = la identificativa de mayor proporción con ≥ {UMBRAL_DOMINANTE:.0%}; con "
                  f"≥ {UMBRAL_CASI_TODO:.0%} se marca como regla escribible; las propiedades solo informan.)"
                  .replace("%", " %"))
    return salida


def lectura_muestra_m16b(muestra: Filas | None) -> str:
    """Patrón del código de caa en la muestra TOP 20 (ponderado por líneas)."""
    if muestra is None:
        return f"Muestra: {sin_medicion('M16b_muestra', 'M16')}."
    total = sum(_num(f.get("lineas")) for f in muestra)
    if not total:
        return "Muestra vacía: sin patrón del código de caa."

    def peso(cumple: Callable[[str, dict[str, Any]], bool]) -> float:
        return sum(_num(f.get("lineas")) for f in muestra if cumple(str(f.get("caa_cod") or "").strip(), f))

    def txt(f: dict[str, Any], campo: str) -> str:
        return str(f.get(campo) or "").strip()

    igual = peso(lambda caa, f: bool(caa) and caa == txt(f, "caagascod"))
    igual_linea = peso(lambda caa, f: bool(caa) and caa == txt(f, "caagascod_linea"))
    obra = peso(lambda caa, f: bool(txt(f, "obra")) and txt(f, "obra") in caa)
    centro = peso(lambda caa, f: bool(txt(f, "centro")) and txt(f, "centro") in caa)
    cuenta = peso(lambda caa, f: bool(txt(f, "cuenta")) and caa.startswith(txt(f, "cuenta")))
    return (f"Muestra TOP 20 ({total:.0f} líneas): código de caa = caagascod {_pct(igual, total)} (naturaleza del "
            f"producto); = caagascod de la naturaleza de la línea {_pct(igual_linea, total)}; "
            f"contiene el código de obra {_pct(obra, total)}; contiene el del centro {_pct(centro, total)}; "
            f"empieza por la cuenta financiera {_pct(cuenta, total)}.")


def lectura_dcaproana(fila: dict[str, Any]) -> str:
    """Ciclo 1, obs. (d): reparto analítico en `dcaproana` de las sin vincular (informativa)."""
    n, con = _num(fila.get("n")), _num(fila.get("con_ana"))
    return (f"dcaproana: {_pct(con, n)} sin vincular tienen reparto analítico; con caa distinta de "
            f"dcapro.caaide {_num(fila.get('ana_caa_distinta')):.0f}; con varias filas "
            f"{_num(fila.get('ana_varias_filas')):.0f}"
            + (" ⇒ en esas líneas dcapro.caaide no cuenta toda la analítica (informativo)." if con > 0
               else " ⇒ el escritorio no reparte la analítica de estas líneas en dcaproana."))


# T0a-ter, M16c. Candidatas en orden de desempate (a igual proporción gana la de más arriba y se nombran
# las empatadas): la naturaleza de la LÍNEA antes que la del producto (F-009 escribe dcapro.natide).
REGLAS_CAA_M16C: tuple[tuple[str, str], ...] = (
    ("regla_linea_obra", "obra.sufijo de caagascod de la naturaleza de la línea"),
    ("regla_linea_centro", "centro.sufijo de caagascod de la naturaleza de la línea"),
    ("regla_producto_obra", "obra.sufijo de caagascod de la naturaleza del producto"),
    ("regla_producto_centro", "centro.sufijo de caagascod de la naturaleza del producto"),
)
REGLAS_CUENTA_M16C: tuple[tuple[str, str], ...] = (
    ("cueide_linea", "cuacomcod de la naturaleza de la línea"),
    ("cueide_producto", "cuacomcod de la naturaleza del producto"),
)
# Informativas: dónde la regla no puede aplicarse o puede fallar.
AVISOS_M16C: tuple[tuple[str, str], ...] = (
    ("linea_sin_mod", "naturaleza de la línea sin «MOD.»"),
    ("linea_sin_punto", "sin «.» en su caagascod"),
    ("linea_sin_naturaleza", "sin naturaleza"),
    ("producto_sin_mod", "naturaleza del producto sin «MOD.»"),
    ("linea_caaexicod", "caaexicod informado en la de la línea"),
    ("producto_caaexicod", "en la del producto"),
    ("caa_repetida", "caa con (centro, código) repetido"),
    ("obra_igual_centro", "código de obra = código de centro"),
    ("cua_repetida", "cua con (empresa, código) repetido"),
    ("cua_de_otra_empresa", "cua de otra empresa"),
    ("caa_informada", "caaide informado"),
)
_UMBRAL_M16C_TXT = f"{UMBRAL_REGLA_ESCRIBIBLE:.0%}".replace("%", " %")


def _veredicto_m16c(f: dict[str, Any], candidatas: tuple[tuple[str, str], ...], n: float) -> str:
    mejor, desc_mejor = 0.0, ""
    for campo, desc in candidatas:
        if _num(f.get(campo)) > mejor:
            mejor, desc_mejor = _num(f.get(campo)), desc
    empatadas = [desc for campo, desc in candidatas if desc != desc_mejor and mejor > 0 and _num(f.get(campo)) == mejor]
    empate = f" (empata con: {', '.join(empatadas)})" if empatadas else ""
    if _cumple(mejor, n, UMBRAL_REGLA_ESCRIBIBLE):
        return f"⇒ REGLA escribible «{desc_mejor}» {_pct(mejor, n)}{empate}"
    return f"sin regla escribible (la mejor: «{desc_mejor or '-'}» {_pct(mejor, n)}){empate}"


def _lectura_grupo_m16c(nombre: str, f: dict[str, Any]) -> list[str]:
    n = _num(f.get("n"))
    caa, cuenta = _veredicto_m16c(f, REGLAS_CAA_M16C, n), _veredicto_m16c(f, REGLAS_CUENTA_M16C, n)
    salida = [f"{nombre} ({n:.0f} líneas): caa {caa}; cueide {cuenta}."]
    avisos = [f"{desc} {_pct(_num(f.get(campo)), n)}" for campo, desc in AVISOS_M16C if campo in f]
    if avisos:
        salida.append(f"{nombre}: dónde no aplica o puede fallar: {'; '.join(avisos)}.")
    return salida


def lectura_m16c(reglas: Filas | None) -> list[str]:
    """T0a-ter, M16c: ¿es escribible la regla «caa = <obra o centro>.<caagascod tras el '.'> de la naturaleza
    de la línea» y la de «cueide = cua de cuacomcod»? Por grupo × partida y en total. None = no se pudo leer
    (SIN MEDICIÓN); [] = cero filas (no hay líneas sin vincular)."""
    if reglas is None:
        return [f"{sin_medicion('M16c_reglas', 'M16')} ⇒ no se concluye la regla de la caa ni la de la cuenta."]
    if not reglas:
        return ["M16c_reglas devolvió cero filas (ninguna línea sin vincular desde 2025): la regla no se contrasta."]
    salida: list[str] = []
    for f in sorted(reglas, key=lambda f: (str(f.get("grupo")), str(f.get("partida")))):
        salida.extend(_lectura_grupo_m16c(f"{f.get('grupo')} / {f.get('partida')}", f))
    campos = ["n", *(c for c, _ in REGLAS_CAA_M16C + REGLAS_CUENTA_M16C + AVISOS_M16C)]
    total = {campo: _suma(reglas, campo) for campo in campos if any(campo in f for f in reglas)}
    salida.extend(_lectura_grupo_m16c("TOTAL", total))
    n = total.get("n", 0.0)
    linea = max(total.get("regla_linea_obra", 0.0), total.get("regla_linea_centro", 0.0))
    producto = max(total.get("regla_producto_obra", 0.0), total.get("regla_producto_centro", 0.0))
    ok = _cumple(linea, n, UMBRAL_REGLA_ESCRIBIBLE) and linea >= producto
    salida.append(f"Hipótesis M16c (caa = <obra o centro>.<caagascod tras el '.'> de la naturaleza de la LÍNEA): "
                  f"{'CONFIRMADA' if ok else 'NO confirmada'} en el total (con la de la línea {_pct(linea, n)}; "
                  f"con la del producto {_pct(producto, n)}).")
    salida.append(f"(REGLA escribible = ≥ {_UMBRAL_M16C_TXT} de las líneas. La de la caa exige caa.cenide = "
                  "dcapro.cenide y que (centro, código) no se repita entre las caa. La de la cuenta exige que la "
                  "cua sea de la empresa del albarán y que (empresa, código) no se repita entre las cua.)")
    return salida


def lectura_m16c_naturalezas(filas: Filas | None) -> str:
    """T0a-ter, M16c: qué naturalezas eligen los usuarios en el genérico y dónde falla la regla de la línea."""
    cab = f"Naturalezas de la línea en {GENERICO_NATURALEZAS_M16C} (empresa {EMPRESA_GENERICOS})"
    if filas is None:
        return f"{cab}: {sin_medicion('M16c_naturalezas_ma', 'M16')}."
    if not filas:
        return f"{cab}: ninguna línea sin vincular desde 2025 (cero filas)."
    total = _suma(filas, "lineas")

    def nombre(f: dict[str, Any]) -> str:
        return f"«{str(f.get('nat_cod') or '').strip()}»"

    usadas = [f"{nombre(f)} {str(f.get('nat_res') or '').strip()} ({str(f.get('caagascod') or '').strip()}) "
              f"{_pct(_num(f.get('lineas')), total)}" for f in filas[:3]]
    def linea(f: dict[str, Any]) -> float:   # ciclo 1, obs. (a): la mejor de las variantes obra y centro
        return max(_num(f.get("regla_linea_obra")), _num(f.get("regla_linea_centro")))

    fallan = [f"{nombre(f)} {_pct(linea(f), _num(f.get('lineas')))}" for f in filas
              if not _cumple(linea(f), _num(f.get("lineas")), UMBRAL_REGLA_ESCRIBIBLE)]
    return (f"{cab}, TOP {len(filas)} ({total:.0f} líneas): las más usadas {', '.join(usadas)}; la regla de la "
            f"línea no llega al {_UMBRAL_M16C_TXT} en: {', '.join(fallan) or 'ninguna'}.")


def lectura_m16c_vinculadas(filas: Filas | None) -> str:
    """T0a-ter, M16c, control: la misma regla sobre ctrpro (naturaleza, obra y centro de la línea de contrato)."""
    if filas is None:
        return f"Control con las vinculadas: {sin_medicion('M16c_vinculadas', 'M16')}."
    if not filas:
        return "Control con las vinculadas: ninguna línea vinculada desde 2025 (cero filas)."
    n, obra, centro = (_suma(filas, k) for k in ("ctrpro", "regla_linea_obra", "regla_linea_centro"))
    # Ciclo 1, obs. (c): una línea de contrato sin caaide no es un contraejemplo; la base son las informadas.
    con_caa = any("caa_informada" in f for f in filas)
    base = _suma(filas, "caa_informada") if con_caa else n
    cab = f"Control con las vinculadas ({n:.0f} líneas de contrato): "
    if con_caa:
        cab += f"caaide informado {_pct(base, n)}; "
    if base <= 0:
        return cab + "ninguna con caaide informado ⇒ no sirve de control (sin contraejemplos)."
    ok = _cumple(max(obra, centro), base, UMBRAL_REGLA_ESCRIBIBLE)
    return (f"{cab}ctrpro.caaide = obra.sufijo de caagascod de la naturaleza de la línea del contrato "
            f"{_pct(obra, base)}; con el centro {_pct(centro, base)} ⇒ "
            + ("la regla también explica las del contrato." if ok else
               "la caa del contrato NO sigue la regla (no sirve de control)."))


def lectura_m16c_numemp(filas: Filas | None) -> str:
    """Ampliación de T0a-ter, P2 (informativa): ¿«naturaleza de la empresa» = auxpronat.numemp?"""
    cab = f"numemp de las naturalezas de la línea (sin vincular, empresa {EMPRESA_GENERICOS}, desde 2025)"
    if filas is None:
        return f"{cab}: {sin_medicion('M16c_numemp', 'M16')}."
    n = _suma(filas, "lineas")
    if n <= 0:
        return f"{cab}: cero filas (ninguna línea)."

    def clase(nombre: str) -> str:
        return (f"{_pct(_suma(filas, 'lineas', clase=nombre), n)}, "
                f"{_suma(filas, 'naturalezas', clase=nombre):.0f} naturalezas")

    igual, cero = _suma(filas, "lineas", clase="igual_empresa"), _suma(filas, "lineas", clase="cero")
    if _cumple(igual, n, UMBRAL_REGLA_ESCRIBIBLE):
        veredicto = "numemp = empresa: la validación por numemp es viable"
    elif _cumple(igual + cero, n, UMBRAL_REGLA_ESCRIBIBLE):
        veredicto = "numemp en {0, empresa}: validar así, no por igualdad"
    else:
        veredicto = "numemp no identifica la empresa: la validación pasa a «existe y sin baja»"
    return (f"{cab} ({n:.0f} líneas): = empresa del albarán {clase('igual_empresa')}; 0: {clase('cero')}; "
            f"otra empresa: {clase('otra_empresa')}; sin naturaleza: {clase('sin_naturaleza')}; = empresa de la "
            f"obra {_pct(_suma(filas, 'igual_empresa_obra'), n)} ⇒ {veredicto} (informativa, P2).")


def _m16c(c: ClienteLectura, inf: Informe, grupos: list[Any]) -> None:
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    reglas = _leer_tabla(c, inf, "M16c_reglas", "M16c: regla del código de la caa y de la cuenta (sin vincular)",
                         grupos, **kw)
    for texto in lectura_m16c(reglas):
        inf.concluir("M16c " + texto)
    nat = _leer_tabla(c, inf, "M16c_naturalezas_ma", f"M16c: naturalezas de la línea en {GENERICO_NATURALEZAS_M16C}",
                      [EMPRESA_GENERICOS, GENERICO_NATURALEZAS_M16C], **kw)
    inf.concluir("M16c " + lectura_m16c_naturalezas(nat))
    vinc = _leer_tabla(c, inf, "M16c_vinculadas", "M16c: control con la línea de contrato (vinculadas)", grupos, **kw)
    inf.concluir("M16c " + lectura_m16c_vinculadas(vinc))
    numemp = _leer_tabla(c, inf, "M16c_numemp", "M16c: numemp de las naturalezas de la línea (P2)",
                         [EMPRESA_GENERICOS], **kw)
    inf.concluir("M16c " + lectura_m16c_numemp(numemp))


# --- T0a-quater, M16d ---------------------------------------------------------------------------------------
# Candidatas para la caa, en orden de desempate (la de más arriba gana y se nombran las empatadas). Todas fijan UNA
# caa: las de código, por (centro de la línea, código) único; las «anterior», por su caaide.
CANDIDATAS_M16D: tuple[tuple[str, str], ...] = (
    ("regla_ampliada", "M16c ampliada (<obra>.<caagascod entero> si no hay '.')"),
    ("regla_actual", "M16c (<obra o centro>.<caagascod tras el '.'>)"),
    ("caagascod_entero", "<obra>.<caagascod entero>"),
    ("obra_natcod", "<obra>.<código de la naturaleza>"),
    ("anterior_obra_nat", "la de la sin vincular anterior de la misma obra y naturaleza"),
    ("anterior_obra_pro", "la de la sin vincular anterior de la misma obra y producto"),
)
DIMENSIONES_M16D: tuple[tuple[str, str, str], ...] = (
    ("obra", "M16d_por_obra", "la obra"),
    ("proveedor", "M16d_por_proveedor", "el proveedor"),
    ("usuario", "M16d_por_usuario", "el usuario del alta"),
)


def _texto(fila: dict[str, Any], campo: str) -> str:
    return str(fila.get(campo) or "").strip()


def lectura_m16d_maestro(filas: Filas | None, cod: str = GENERICO_XA) -> str:
    """T0a-quater, M16d: qué es el genérico (por defecto XA9999) y si su naturaleza admite la regla de M16c."""
    if filas is None:
        return f"Maestro de {cod}: {sin_medicion('M16d_maestro', 'M16')}."
    if not filas:
        return f"Maestro de {cod} (empresa {EMPRESA_GENERICOS}): no está (cero filas)."
    f = filas[0]
    gas = _texto(f, "caagascod")
    return (f"Maestro de {cod} (empresa {EMPRESA_GENERICOS}, ide {f.get('ide')}): «{_texto(f, 'res')}»; naturaleza "
            f"«{_texto(f, 'nat_cod')}» {_texto(f, 'nat_res')}: caagascod «{gas}», cuacomcod «{_texto(f, 'cuacomcod')}», "
            f"caaexicod «{_texto(f, 'caaexicod')}» ⇒ caagascod "
            + ("con '.': la regla de M16c es aplicable." if "." in gas else
               "sin '.': la regla de M16c no se puede aplicar."))


def lectura_m16d_excepciones(cod: str, filas: Filas | None) -> str:
    """T0a-quater, M16d: cómo se compone la caa de las líneas del genérico que NO cumplen M16c (muestra TOP 20)."""
    if filas is None:
        return f"Excepciones de {cod}: {sin_medicion('M16d_excepciones', 'M16')}."
    if not filas:
        return f"Excepciones de {cod}: cero filas (todas sus líneas sin vincular cumplen M16c, o no hay líneas)."
    total = _suma(filas, "lineas")

    def peso(cumple: Callable[[str, dict[str, Any]], bool]) -> float:
        return sum(_num(f.get("lineas")) for f in filas if _texto(f, "obra") and cumple(_texto(f, "caa_cod"), f))

    empieza = peso(lambda caa, f: caa.startswith(_texto(f, "obra") + "."))
    entero = peso(lambda caa, f: bool(_texto(f, "caagascod_linea"))
                  and caa == f"{_texto(f, 'obra')}.{_texto(f, 'caagascod_linea')}")
    natcod = peso(lambda caa, f: bool(_texto(f, "nat_cod")) and caa == f"{_texto(f, 'obra')}.{_texto(f, 'nat_cod')}")
    top = filas[0]
    return (f"Excepciones de {cod}, TOP {len(filas)} ({total:.0f} líneas que no cumplen M16c): caa empieza por "
            f"«<obra>.» {_pct(empieza, total)}; = <obra>.<caagascod entero> {_pct(entero, total)}; = <obra>.<código de "
            f"la naturaleza> {_pct(natcod, total)}; la más frecuente: caa «{_texto(top, 'caa_cod')}», naturaleza "
            f"«{_texto(top, 'nat_cod')}» ({_texto(top, 'caagascod_linea')}), {_texto(top, 'partida')}, "
            f"{_num(top.get('lineas')):.0f} líneas.")


def lectura_m16d_sufijos(cod: str, filas: Filas | None) -> str:
    """T0a-quater, M16d: sufijo de la caa (tras el primer '.') en las excepciones, frente a la naturaleza."""
    if filas is None:
        return f"Sufijos de la caa en las excepciones de {cod}: {sin_medicion('M16d_sufijos', 'M16')}."
    if not filas:
        return f"Sufijos de la caa en las excepciones de {cod}: cero filas (no hay excepciones)."
    total = _suma(filas, "lineas")

    def peso(cumple: Callable[[str, str, str], bool]) -> float:
        return sum(_num(f.get("lineas")) for f in filas
                   if cumple(_texto(f, "sufijo"), _texto(f, "nat_cod"), _texto(f, "caagascod_linea")))

    def tras_punto(gas: str) -> str | None:
        return gas.split(".", 1)[1] if "." in gas else None

    usados = [f"«{_texto(f, 'sufijo')}» (naturaleza «{_texto(f, 'nat_cod')}», {_texto(f, 'caagascod_linea')}) "
              f"{_pct(_num(f.get('lineas')), total)}" for f in filas[:3]]
    return (f"Sufijos de la caa en las excepciones de {cod} ({total:.0f} líneas en el TOP {len(filas)}): los más "
            f"frecuentes {', '.join(usados)}; sufijo = caagascod entero {_pct(peso(lambda s, n, g: bool(g) and s == g), total)}; "
            f"= código de la naturaleza {_pct(peso(lambda s, n, g: bool(n) and s == n), total)}; = caagascod tras el '.' "
            f"{_pct(peso(lambda s, n, g: s == tras_punto(g)), total)}; caa empieza por «<obra>.» "
            f"{_pct(_suma(filas, 'empieza_por_obra'), total)}.")


def _lectura_grupo_m16d(nombre: str, f: dict[str, Any]) -> str:
    n = _num(f.get("n"))

    def condicional(acierto: str, sin: str) -> str:
        return _pct(_num(f.get(acierto)), n - _num(f.get(sin)))

    return (f"{nombre} ({n:.0f} líneas): caa {_veredicto_m16c(f, CANDIDATAS_M16D, n)}; con anterior de la misma obra y "
            f"naturaleza acierta {condicional('anterior_obra_nat', 'sin_anterior_obra_nat')}; con anterior de la misma "
            f"obra y producto acierta {condicional('anterior_obra_pro', 'sin_anterior_obra_pro')}.")


def lectura_m16d_candidatas(filas: Filas | None) -> list[str]:
    """T0a-quater, M16d: candidatas para la caa por grupo × partida y en total; la hipótesis es la regla de M16c
    ampliada con <obra>.<caagascod entero> cuando la naturaleza no tiene '.'. None = SIN MEDICIÓN; [] = cero filas."""
    if filas is None:
        return [f"{sin_medicion('M16d_candidatas', 'M16')} ⇒ no se contrastan las candidatas."]
    if not filas:
        return ["M16d_candidatas devolvió cero filas (ninguna línea sin vincular desde 2025)."]
    salida = [_lectura_grupo_m16d(f"{f.get('grupo')} / {f.get('partida')}", f)
              for f in sorted(filas, key=lambda f: (str(f.get("grupo")), str(f.get("partida"))))]
    campos = ["n", *(c for c, _ in CANDIDATAS_M16D), "sin_anterior_obra_nat", "sin_anterior_obra_pro", "caa_informada"]
    total = {campo: _suma(filas, campo) for campo in campos}
    salida.append(_lectura_grupo_m16d("TOTAL", total))
    ok = _cumple(total["regla_ampliada"], total["n"], UMBRAL_REGLA_ESCRIBIBLE)
    salida.append(f"Hipótesis M16d (regla de M16c ampliada con <obra>.<caagascod entero> si la naturaleza no tiene "
                  f"'.'): {'CONFIRMADA' if ok else 'NO confirmada'} en el total "
                  f"({_pct(total['regla_ampliada'], total['n'])}). (REGLA escribible = ≥ {_UMBRAL_M16C_TXT}; «anterior» "
                  "no aplica a la primera línea de su obra y naturaleza o producto.)")
    return salida


def _eleccion_de(dim: str, filas: Filas) -> tuple[float, float, str]:
    """(líneas que siguen la naturaleza mayoritaria de su ítem, líneas, texto) de una dimensión."""
    lineas = _suma(filas, "lineas")
    mayor = sum(max(_num(f.get("nat_producto")), _num(f.get("otra_nat"))) for f in filas)
    mixtos = [f for f in filas if _num(f.get("nat_producto")) > 0 and _num(f.get("otra_nat")) > 0]
    # Ciclo 1, obs. a: «otra_nat» junta todo lo que no es la naturaleza de la ficha; con más de dos, la pureza se
    # sobrestima en ese ítem.
    varias = [f for f in filas if _num(f.get("naturalezas")) > 2]
    texto = (f"Naturaleza en {GENERICO_NATURALEZAS_M16C} por {dim} ({len(filas)} ítems, {lineas:.0f} líneas): sigue la "
             f"mayoritaria de su {dim} {_pct(mayor, lineas)}; ítems mixtos {len(mixtos)} "
             f"({_pct(_suma(mixtos, 'lineas'), lineas)} de las líneas); con la naturaleza del producto "
             f"{_pct(_suma(filas, 'nat_producto'), lineas)}; cumplen M16c {_pct(_suma(filas, 'cumple_regla'), lineas)}"
             + (f" (TOP {TOP_ELECCION_M16D}: hay más ítems)" if len(filas) >= TOP_ELECCION_M16D else "")
             + (f"; AVISO: {len(varias)} ítems con más de dos naturalezas ({_pct(_suma(varias, 'lineas'), lineas)} de "
                "las líneas): ahí la pureza está sobrestimada" if varias else "") + ".")
    return mayor, lineas, texto


def lectura_m16d_eleccion(dims: dict[str, Filas | None]) -> list[str]:
    """T0a-quater, M16d: ¿la naturaleza que se pone en el genérico (MA99 o la de la ficha, MA1501) la fija la obra, el
    proveedor o el usuario del alta? Pureza = líneas que siguen la naturaleza mayoritaria de su ítem."""
    salida: list[str] = []
    medidas: list[tuple[float, float, str]] = []
    for dim, nombre, articulo in DIMENSIONES_M16D:
        filas = dims.get(dim)
        if filas is None:
            salida.append(f"Naturaleza en {GENERICO_NATURALEZAS_M16C} por {dim}: {sin_medicion(nombre, 'M16')}.")
            continue
        if not filas:
            salida.append(f"Naturaleza en {GENERICO_NATURALEZAS_M16C} por {dim}: cero filas (ninguna línea).")
            continue
        mayor, lineas, texto = _eleccion_de(dim, filas)
        salida.append(texto)
        if lineas > 0:
            medidas.append((mayor, lineas, articulo))
    if not medidas:
        salida.append("Lectura M16d: no hay dimensiones medidas con líneas ⇒ no se concluye.")
        return salida
    mayor, lineas, articulo = max(medidas, key=lambda m: m[0] / m[1])
    otras = "; ".join(f"{a} {_pct(m, n)}" for m, n, a in medidas if a != articulo)
    if _cumple(mayor, lineas, UMBRAL_PUREZA_M16D):
        salida.append(f"Lectura M16d: la naturaleza de las líneas {GENERICO_NATURALEZAS_M16C} la fija {articulo} (sigue "
                      f"la mayoritaria {_pct(mayor, lineas)}" + (f"; {otras}" if otras else "") + ").")
    else:
        salida.append(f"Lectura M16d: ninguna dimensión sola fija la naturaleza (la más pura: {articulo} "
                      f"{_pct(mayor, lineas)}" + (f"; {otras}" if otras else "") + "): la elección es mixta.")
    salida.append(f"(Fija = ≥ {UMBRAL_PUREZA_M16D:.0%} de las líneas siguen la mayoritaria de su ítem. Con muchos "
                  "ítems pequeños la pureza sube por azar: comparar con el número de ítems.)".replace("%", " %"))
    return salida


def _m16d(c: ClienteLectura, inf: Informe) -> None:
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    maestro = _leer_tabla(c, inf, "M16d_maestro", f"M16d: maestro de {GENERICO_XA}", [EMPRESA_GENERICOS, GENERICO_XA],
                          max_rows=5)
    inf.concluir("M16d " + lectura_m16d_maestro(maestro))
    for cod in GENERICOS_EXCEPCIONES_M16D:
        exc = _leer_tabla(c, inf, "M16d_excepciones", f"M16d: líneas de {cod} que no cumplen M16c (TOP 20)",
                          [EMPRESA_GENERICOS, cod], **kw)
        inf.concluir("M16d " + lectura_m16d_excepciones(cod, exc))
        suf = _leer_tabla(c, inf, "M16d_sufijos", f"M16d: sufijo de la caa en las excepciones de {cod} (TOP 20)",
                          [EMPRESA_GENERICOS, cod], **kw)
        inf.concluir("M16d " + lectura_m16d_sufijos(cod, suf))
    cand = _leer_tabla(c, inf, "M16d_candidatas", "M16d: candidatas para la caa (sin vincular)",
                       [EMPRESA_GENERICOS, *PRODUCTOS_GENERICOS], **kw)
    for texto in lectura_m16d_candidatas(cand):
        inf.concluir("M16d " + texto)
    dims = {dim: _leer_tabla(c, inf, nombre, f"M16d: naturaleza de {GENERICO_NATURALEZAS_M16C} por {dim} (TOP 15)",
                             [EMPRESA_GENERICOS, GENERICO_NATURALEZAS_M16C, DESDE_ALTAS_LOG], limite=15,
                             max_rows=TOP_ELECCION_M16D, timeout_s=TIMEOUT_PESADO_S)
            for dim, nombre, _ in DIMENSIONES_M16D}
    for texto in lectura_m16d_eleccion(dims):
        inf.concluir("M16d " + texto)


def m16(c: ClienteLectura) -> Informe:
    inf = Informe("M16", "analítica, almacén y centro de las líneas (H10, H13), origen de caaide (M16b), "
                         "regla del código de la caa (M16c) y sus excepciones (M16d)")
    kw = {"max_rows": 10, "timeout_s": TIMEOUT_PESADO_S}
    r1 = _leer_tabla(c, inf, "M16_caa_con_partida", "caaide de las líneas con partida desde 2025", **kw)
    r2 = _leer_tabla(c, inf, "M16_caa_almacen", "caaide de las líneas sin partida frente al almacén", **kw)
    r3 = _leer_tabla(c, inf, "M16_almacen_sin_vincular", "almacén y centro de las sin vincular", **kw)
    r4 = _leer_tabla(c, inf, "M16_ficha_obra", "ficha de las obras con albaranes desde 2025", max_rows=1,
                     timeout_s=TIMEOUT_PESADO_S)
    ficha = None if r4 is None else (r4[0] if r4 else {})
    for texto in lectura_m16(r1, r2, r3, ficha):
        inf.concluir(texto)
    grupos = [EMPRESA_GENERICOS, *PRODUCTOS_GENERICOS]
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    fuentes = _leer_tabla(c, inf, "M16b_fuentes", "M16b: origen de caaide en las sin vincular (campos)", grupos, **kw)
    codigos = _leer_tabla(c, inf, "M16b_codigos", "M16b: origen de caaide en las sin vincular (códigos)", grupos, **kw)
    muestra = _leer_tabla(c, inf, "M16b_muestra", "M16b: muestra (caa, naturaleza, obra, centro, cuenta)", **kw)
    for texto in lectura_m16b(fuentes, codigos):
        inf.concluir("M16b " + texto)
    inf.concluir("M16b " + lectura_muestra_m16b(muestra))
    _m16c(c, inf, grupos)   # antes que dcaproana, la más expuesta por volumen
    ana = _leer_tabla(c, inf, "M16b_dcaproana", "M16b: reparto analítico (dcaproana) de las sin vincular",
                      max_rows=1, timeout_s=TIMEOUT_PESADO_S)
    if ana is not None:
        inf.concluir("M16b " + lectura_dcaproana(ana[0] if ana else {}))
    _m16d(c, inf)   # T0a-quater: al final, M16d_candidatas lleva dos LAG sobre todo el universo
    return inf


def lectura_m17(existe: Filas | None, marcas: Filas | None, estados: set[str] | None) -> str:
    """Spec v5 §T0, M17 «debe salir / decide»: ¿anular borra, marca o no se sabe?
    None = la sentencia no se pudo leer: no se concluye a partir de ella."""
    if existe is None:
        return f"Lectura automática: {sin_medicion('M17_existe', 'M17')} ⇒ no se concluye."
    borran = [str(f.get("ope")) for f in existe if _num(f.get("n")) > 0
              and _num(f.get("con_existe")) / _num(f.get("n")) <= UMBRAL_BORRA]
    if borran:
        return f"Lectura automática: ope {', '.join(borran)} con con_existe ≈ 0 ⇒ anular BORRA: R30 sin cambios."
    if marcas is None or estados is None:
        rotas = " y ".join(n for n, v in (("M17_marcas", marcas), ("M2_conest", estados)) if v is None)
        return f"Lectura automática: sin ope de baja clara y {sin_medicion(rotas, 'M17')} ⇒ no se concluye."
    todas = bool(existe) and all(_cumple(_num(f.get("con_existe")), _num(f.get("n"))) for f in existe)
    con_fecbaj = _suma(marcas, "n", con_fecbaj=1)
    fuera = sorted({str(f.get("est")) for f in marcas if str(f.get("est")) not in estados})
    if todas and (con_fecbaj > 0 or fuera):
        return ("Lectura automática: con_existe ≈ n y hay marca (fecbaj > 0 en "
                f"{con_fecbaj:.0f} albaranes; est fuera de conest: {', '.join(fuera) or 'ninguno'}) ⇒ anular MARCA: "
                "L11 añade AND <no marcado> y F-053 usa ALB-{id}-{n}.")
    return "Lectura automática: sin ope de baja clara ⇒ se decide con T23 (anulación del albarán de prueba)."


def lectura_m17b(reutiliza: Filas | None) -> str:
    """T0a-bis, M17b: tras una ope 2 sobre un albarán, ¿desaparece el registro (y el cod se reutiliza)
    o sigue el mismo? None = no se pudo leer (no se concluye); [] = no hay ope 2 en la ventana."""
    if reutiliza is None:
        return f"Lectura automática M17b: {sin_medicion('M17b_reutiliza', 'M17')} ⇒ no se concluye."
    n = _suma(reutiliza, "n")
    if n <= 0:
        return "Lectura automática M17b: no concluyente (sin ope 2 en la ventana de log) ⇒ se decide con T23."
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
    return f"Lectura automática M17b: no concluyente ({cifras}) ⇒ se decide con T23."


# Palabras del resumen (`log.res`) que delatan el significado de una ope.
_SIGNIFICADOS_OPE = (
    ("modific", "modificación"), ("impr", "impresión"), ("anul", "anulación"), ("baja", "baja"),
    ("borr", "borrado"), ("elimin", "borrado"), ("estado", "cambio de estado"), ("contab", "contabilización"),
    ("factur", "facturación"), ("consult", "consulta"), ("envi", "envío"), ("correo", "envío"),
    ("mail", "envío"), ("export", "exportación"), ("alta", "alta"),
)


def _sin_tildes(texto: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", texto) if unicodedata.category(ch) != "Mn")


def lectura_ope(res: Filas | None) -> list[str]:
    """T0a-bis, M17b: significado deducible de cada ope ≠ 1 por su resumen más frecuente. Se compara
    sin tildes («Envío» casa con `envi`, ciclo 1, obs. e)."""
    if res is None:
        return [f"Significado de las ope: {sin_medicion('M17b_res', 'M17')}."]
    salida = []
    for ope in sorted({f.get("ope") for f in res}, key=lambda o: _num(o)):
        top = max((f for f in res if f.get("ope") == ope), key=lambda f: _num(f.get("n")))
        texto = str(top.get("res") or "").strip()
        guess = next((nombre for clave, nombre in _SIGNIFICADOS_OPE if clave in _sin_tildes(texto.lower())), None)
        detalle = f"(res más frecuente: '{texto}', {_num(top.get('n')):.0f} filas)"
        salida.append(f"ope {ope}: parece «{guess}» {detalle}." if guess
                      else f"ope {ope}: significado no deducible por su resumen {detalle}.")
    return salida


def m17(c: ClienteLectura) -> Informe:
    inf = Informe("M17", "anulación de albaranes: ¿borra o marca? (H9) y reutilización del código (M17b)")
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    for f in _leer_tabla(c, inf, "M17_ope", "operaciones de log sobre albaranes (últimos 1.000.000 ide)", **kw) or []:
        inf.concluir(f"log.ope={f.get('ope')}: {_num(f.get('n')):.0f} filas, de {f.get('desde')} a {f.get('hasta')}.")
    e = _leer_tabla(c, inf, "M17_emp_log", "log.emp de las operaciones que no son alta", **kw)
    sin_emp = sum(_num(f.get("n")) for f in e or [] if f.get("emp") in (0, -1, None))
    existe = _leer_tabla(c, inf, "M17_existe", "¿sigue existiendo el albarán? (JOIN por emp, tip, cod)", **kw)
    if sin_emp > 0:
        inf.concluir(f"log.emp sale 0 o nulo en {sin_emp:.0f} filas: se repite el JOIN solo por tip y cod (spec) "
                     "y la lectura usa esa repetición (un cod repetido entre empresas cuenta de más).")
        existe = _leer_tabla(c, inf, "M17_existe_sin_emp", "¿sigue existiendo el albarán? (JOIN solo por tip, cod)",
                             **kw)
    for f in existe or []:
        inf.concluir(f"ope={f.get('ope')}: existe {_pct(_num(f.get('con_existe')), _num(f.get('n')))}; "
                     f"con fecbaj {_num(f.get('con_fecbaj')):.0f}.")
    m = _leer_tabla(c, inf, "M17_marcas", "albaranes desde 2025 por est y fecbaj", **kw)
    k = _leer_tabla(c, inf, "M2_conest", "estados de conest (tip 14)", max_rows=50)
    inf.concluir(lectura_m17(existe, m, None if k is None else {str(f.get("est")) for f in k}))
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


# ---------------------------------------------------------------------------
# T0a-quater: M19 planificación de compras (dnc/dncpro), cod2 y altas de los genéricos por usuario
# ---------------------------------------------------------------------------
_UMBRAL_DNC_TXT = f"{UMBRAL_HEREDA_DNC:.0%}".replace("%", " %")
# Qué se hereda de dncpro: (nombre, acierto, base). Base None = todas las líneas con dncproide; cod2 cuenta como
# coherente si es igual o vacío en las dos.
HEREDA_M19: tuple[tuple[str, tuple[str, ...], str | None], ...] = (
    ("cod2", ("cod2_igual", "cod2_ambos_vacios"), None),
    ("caaide", ("caa_igual",), "caa_dncpro"),
    ("producto", ("pro_igual",), None),
    ("natide", ("nat_igual",), "nat_dncpro"),
    ("dncide", ("dncide_igual",), None),   # ciclo 1, obs. d
    ("partida", ("paride_igual",), None),
)
# Fuentes candidatas del cod2 de las sin vincular, en orden de desempate (la de más arriba gana). Ciclo 1 de
# revisión: solo las que fijan UN valor compiten; las «mismo producto» aciertan solo si su clave tiene un único cod2.
CANDIDATAS_COD2: tuple[tuple[str, str], ...] = (
    ("dnc_misma_obra_producto", "planificación de la misma obra y producto (con un único cod2)"),
    ("ctr_mismo_producto", "línea del contrato de la cabecera con el mismo producto (con un único cod2)"),
    ("anterior_obra_pro", "línea anterior de la misma obra y producto"),
    ("anterior_prv", "línea anterior del mismo proveedor"),
    ("es_cod_partida", "código de la partida"),
    ("es_cod_producto", "código del producto"),
)
# Propiedades (no fijan cuál copiar): se informan y no compiten.
PROPIEDADES_COD2: tuple[tuple[str, str], ...] = (
    ("dnc_misma_obra", "existe en alguna planificación de la misma obra"),
    ("ctr_cualquier_linea", "existe en alguna línea del contrato de la cabecera"),
    ("dnc_obra_producto_ambigua", "planificación de la misma obra y producto con varios cod2"),
    ("ctr_producto_ambiguo", "contrato con varios cod2 para el producto"),
    ("repetido_en_albaran", "repetido en otra línea del mismo albarán"),
    ("con_contrato", "albarán con contrato"),
)
# H35 del contrato v7.1: las vinculadas copian de su ctrpro el cod2, el dncide y el dncproide. (nombre, iguales con
# valor, ambos vacíos o 0).
COPIA_H35: tuple[tuple[str, str, str], ...] = (
    ("cod2", "cod2_igual", "cod2_ambos_vacios"),
    ("dncide", "dncide_igual", "dncide_ambos_cero"),
    ("dncproide", "dncproide_igual", "dncproide_ambos_cero"),
)


def _lectura_grupo_m19_dnc(nombre: str, f: dict[str, Any]) -> str:
    n = _num(f.get("n"))

    def v(campo: str) -> float:
        return _num(f.get(campo))

    return (f"{nombre} ({n:.0f} líneas con dncproide; dncpro existe {_pct(v('dncpro_existe'), n)}): cod2 = el de dncpro "
            f"{_pct(v('cod2_igual'), v('cod2_dncpro'))} de las que lo traen en dncpro; coherente (igual o ambos vacíos) "
            f"{_pct(v('cod2_igual') + v('cod2_ambos_vacios'), n)}; caaide = el de dncpro {_pct(v('caa_igual'), v('caa_dncpro'))}; "
            f"producto igual {_pct(v('pro_igual'), n)}; natide = la de dncpro {_pct(v('nat_igual'), v('nat_dncpro'))}; = la "
            f"del producto de dncpro {_pct(v('nat_igual_pro_dncpro'), n)}; partida igual {_pct(v('paride_igual'), n)}; "
            f"dncide igual {_pct(v('dncide_igual'), n)}; obra del dnc igual {_pct(v('obra_igual'), n)}; centro igual "
            f"{_pct(v('cen_igual'), n)}.")


def lectura_m19_dnc(filas: Filas | None) -> list[str]:
    """T0a-quater, M19: en las sin vincular con línea de planificación, ¿qué campos se heredan de dncpro?
    None = SIN MEDICIÓN; [] = cero filas."""
    if filas is None:
        return [f"M19 planificación: {sin_medicion('M19_dnc', 'M19')} ⇒ no se concluye."]
    if not filas:
        return ["M19 planificación: cero filas (ninguna sin vincular desde 2025 con dncproide)."]
    salida = [_lectura_grupo_m19_dnc(str(f.get("grupo")), f) for f in sorted(filas, key=lambda f: str(f.get("grupo")))]
    total = {k: _suma(filas, k) for f in filas for k in f if k != "grupo"}
    salida.append(_lectura_grupo_m19_dnc("TOTAL", total))
    heredan, no = [], []
    for nombre, aciertos, base in HEREDA_M19:
        parte = sum(total.get(a, 0.0) for a in aciertos)
        (heredan if _cumple(parte, total.get(base or "n", 0.0), UMBRAL_HEREDA_DNC) else no).append(nombre)
    salida.append(f"Lectura M19 (total): se heredan de la línea de planificación (≥ {_UMBRAL_DNC_TXT}): "
                  f"{', '.join(heredan) or 'ninguno'}; no se heredan: {', '.join(no) or 'ninguno'}.")
    return salida


def lectura_m19_cod2_origen(filas: Filas | None) -> list[str]:
    """T0a-quater, M19: de dónde sale el cod2 de las sin vincular (con y sin línea de planificación)."""
    if filas is None:
        return [f"M19 cod2: {sin_medicion('M19_cod2_origen', 'M19')} ⇒ no se concluye su origen."]
    if not filas:
        return ["M19 cod2: cero filas (ninguna sin vincular desde 2025 con cod2)."]
    salida = []
    for f in sorted(filas, key=lambda f: str(f.get("origen_dnc"))):
        n = _num(f.get("n"))
        todas = ", ".join(f"{desc} {_pct(_num(f.get(campo)), n)}" for campo, desc in CANDIDATAS_COD2)
        props = "; ".join(f"{desc} {_pct(_num(f.get(campo)), n)}" for campo, desc in PROPIEDADES_COD2)
        salida.append(
            f"cod2 de las sin vincular {f.get('origen_dnc')} ({n:.0f} líneas): {_veredicto_m16c(f, CANDIDATAS_COD2, n)}; "
            f"todas: {todas}; con anterior del mismo proveedor acierta "
            f"{_pct(_num(f.get('anterior_prv')), n - _num(f.get('sin_anterior_prv')))}; propiedades (no fijan el "
            f"valor): {props}.")
    salida.append(f"(REGLA escribible = ≥ {_UMBRAL_M16C_TXT} de las líneas con cod2 y solo entre las que fijan UN "
                  "valor; con_dnc = con dncproide, cuya fuente directa es su dncpro: ver M19_dnc.)")
    return salida


def lectura_m19_vinculadas(fila: dict[str, Any] | None) -> str:
    """T0a-quater, M19: cod2, dncide y dncproide de las vinculadas frente a su línea de contrato (H35)."""
    if fila is None:
        return f"Vinculadas: {sin_medicion('M19_vinculadas', 'M19')}."
    n = _num(fila.get("n"))
    if n <= 0:
        return "Vinculadas desde 2025: cero filas."

    def v(campo: str) -> float:
        return _num(fila.get(campo))

    campos = []
    copian, no = [], []
    for nombre, igual, vacios in COPIA_H35:
        ok = _cumple(v(igual) + v(vacios), n, UMBRAL_HEREDA_DNC)
        (copian if ok else no).append(nombre)
        campos.append(f"{nombre} igual con valor {_pct(v(igual), n)}, ambos vacíos o 0 {_pct(v(vacios), n)} ⇒ "
                      + ("se copia de ctrpro" if ok else "NO se copia siempre de ctrpro"))
    h35 = ("H35 CONFIRMADA (las vinculadas copian de ctrpro cod2, dncide y dncproide)" if not no else
           f"H35 NO confirmada en: {', '.join(no)}")
    return (f"Vinculadas desde 2025 ({n:.0f} líneas): cod2 en la línea {_pct(v('cod2_linea'), n)}; en ctrpro "
            f"{_pct(v('cod2_ctrpro'), n)}; igual al de ctrpro {_pct(v('cod2_igual'), v('cod2_ctrpro'))} de las que lo "
            f"traen en ctrpro; ambos vacíos {_pct(v('cod2_ambos_vacios'), n)}; contrato desde planificación "
            f"(ctrpro.dncproide) {_pct(v('ctr_desde_dnc'), n)}; cod2 = el de la dncpro del contrato "
            f"{_pct(v('cod2_igual_dncpro_del_ctr'), v('ctr_desde_dnc'))}; la línea lleva dncproide "
            f"{_pct(v('linea_con_dnc'), n)}. Línea a línea frente a su ctrpro (≥ {_UMBRAL_DNC_TXT}): "
            f"{'; '.join(campos)} ⇒ {h35}.")


def es_usuario_tecnico(cod: str) -> bool:
    """Heurística por el código (usu no tiene marca de usuario técnico): API, servicio, pruebas…"""
    alto = cod.strip().upper()
    return bool(alto) and any(marca in alto for marca in MARCAS_USUARIO_TECNICO)


def lectura_m19_usuarios(filas: Filas | None) -> list[str]:
    """T0a-quater, M19: líneas de los genéricos de la lista blanca por usuario del alta en log. '' = sin alta."""
    if filas is None:
        return [f"Altas por usuario: {sin_medicion('M19_altas_usuario', 'M19')}."]
    if not filas:
        return ["Altas por usuario: cero filas (ninguna línea de los genéricos en la ventana)."]
    por_usuario: dict[str, Counter[str]] = {}
    for f in filas:
        por_usuario.setdefault(_texto(f, "usu"), Counter())[_texto(f, "producto")] += int(_num(f.get("lineas")))
    total = sum(sum(c.values()) for c in por_usuario.values())

    def nombre(u: str) -> str:
        return f"«{u}»" if u else "«(sin alta en log)»"

    orden = sorted(por_usuario.items(), key=lambda kv: -sum(kv[1].values()))
    top = [f"{nombre(u)} {_pct(sum(c.values()), total)} ({', '.join(f'{p} {k}' for p, k in c.items())})"
           for u, c in orden[:10]]
    salida = [f"Altas de líneas {', '.join(LISTA_BLANCA_GENERICOS)} desde {DESDE_ALTAS_LOG} por usuario del alta en "
              f"log ({total} líneas, {len(por_usuario)} usuarios): {'; '.join(top)}"
              + (" (TOP 40 filas: puede haber más)" if len(filas) >= 40 else "") + "."]
    sin = sum(por_usuario.get("", Counter()).values())
    salida.append(f"Sin fila de alta en log: {_pct(sin, total)} (candidatas a altas fuera del escritorio, p. ej. la "
                  "API, que no escribe log; o albaranes cuya alta quedó fuera de la ventana).")
    tecnicos = [f"{nombre(u)} {_pct(sum(c.values()), total)}" for u, c in orden if es_usuario_tecnico(u)]
    salida.append(f"Posibles usuarios técnicos por su código: {', '.join(tecnicos)}." if tecnicos else
                  "Ningún código de usuario parece técnico (heurística por el nombre: "
                  f"{', '.join(MARCAS_USUARIO_TECNICO)}).")
    fuera = sorted({_texto(f, "usu") for f in filas if _texto(f, "usu") and _num(f.get("en_usu")) == 0})
    salida.append("Usuarios del log que no están en usu: " + (", ".join(f"«{u}»" for u in fuera) + "."
                                                              if fuera else "ninguno."))
    return salida


def lectura_m19_api(api: Filas | None, sin_alta: Filas | None) -> list[str]:
    """T0a-quater, M19: ¿hay líneas de genéricos creadas por la API? (la API no escribe log)."""
    salida = []
    if api is None:
        salida.append(f"{COD_ALBARAN_API}: {sin_medicion('M19_api', 'M19')}.")
    elif not api:
        salida.append(f"{COD_ALBARAN_API}: no está (cero filas).")
    else:
        genericos = [f"{_texto(f, 'producto')} {_num(f.get('lineas')):.0f} ({_num(f.get('vinculadas')):.0f} vinculadas)"
                     for f in api if _texto(f, "producto") in LISTA_BLANCA_GENERICOS]
        salida.append(f"{COD_ALBARAN_API} (API): {_suma(api, 'lineas'):.0f} líneas; de genéricos de la lista blanca: "
                      f"{', '.join(genericos) or 'ninguna'}.")
    cab = f"Albaranes desde {DESDE_ALTAS_LOG} con líneas de {', '.join(LISTA_BLANCA_GENERICOS)} y sin alta en log"
    if sin_alta is None:
        salida.append(f"{cab}: {sin_medicion('M19_sin_alta', 'M19')}.")
    elif not sin_alta:
        salida.append(f"{cab}: ninguno ⇒ no hay líneas de esos genéricos sin alta en log en la ventana (que eso descarte "
                      "la API se apoya en el código de sus endpoints de albarán, que no escriben dbo.log; no se mide aquí).")
    else:
        codigos = [_texto(f, "cod") for f in sin_alta]
        solo_api = all(cod == COD_ALBARAN_API for cod in codigos)
        salida.append(f"{cab}: {len(codigos)} en el TOP 10 ({', '.join(codigos)}) ⇒ "
                      + ("solo el albarán de prueba de la API." if solo_api else
                         "hay otros además del de prueba: revisar si son de la API o anteriores a la ventana de log."))
    return salida


def m19(c: ClienteLectura) -> Informe:
    inf = Informe("M19", "planificación de compras (dnc/dncpro) y cod2; altas de los genéricos por usuario y por la API")
    kw = {"max_rows": 50, "timeout_s": TIMEOUT_PESADO_S}
    dnc = _leer_tabla(c, inf, "M19_dnc", "M19: sin vincular con línea de planificación frente a su dncpro",
                      [EMPRESA_GENERICOS, *PRODUCTOS_GENERICOS], **kw)
    for texto in lectura_m19_dnc(dnc):
        inf.concluir(texto)
    _leer_tabla(c, inf, "M19_cod2_valores", "M19: cod2 más frecuentes de las sin vincular", **kw)
    vinc = _leer_tabla(c, inf, "M19_vinculadas", "M19: cod2 de las vinculadas frente a su ctrpro", **kw)
    inf.concluir(lectura_m19_vinculadas(None if vinc is None else (vinc[0] if vinc else {})))
    blanca = [EMPRESA_GENERICOS, *LISTA_BLANCA_GENERICOS, DESDE_ALTAS_LOG]
    altas = _leer_tabla(c, inf, "M19_altas_usuario", "M19: líneas de los genéricos por usuario del alta en log", blanca,
                        **kw)
    for texto in lectura_m19_usuarios(altas):
        inf.concluir(texto)
    sin_alta = _leer_tabla(c, inf, "M19_sin_alta", "M19: albaranes con genéricos sin alta en log (TOP 10)", blanca, **kw)
    api = _leer_tabla(c, inf, "M19_api", f"M19: productos del albarán de la API {COD_ALBARAN_API}", [COD_ALBARAN_API],
                      max_rows=50)
    for texto in lectura_m19_api(api, sin_alta):
        inf.concluir(texto)
    # Ciclo 1 de revisión: la más cara (tres ventanas sobre ~190.000 filas, ctrpro y dncpro dos veces) va la última:
    # si el balanceador la corta, sigue viva en el servidor y no compite con las anteriores.
    origen = _leer_tabla(c, inf, "M19_cod2_origen", "M19: origen del cod2 de las sin vincular", **kw)
    for texto in lectura_m19_cod2_origen(origen):
        inf.concluir(texto)
    return inf


MEDICIONES: dict[str, Callable[[ClienteLectura], Informe]] = {
    "M1": m1, "M2": m2, "M3": m3, "M4": m4, "M5": m5, "M6": m6, "M7": m7, "M8": m8,
    "M9": m9, "M10": m10, "M11": m11, "M12": m12, "M13": m13, "M14": m14, "M15": m15,
    "M16": m16, "M17": m17, "M18": m18, "M19": m19,
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
    p = argparse.ArgumentParser(description="F-009 T0: mediciones M1-M19 de solo lectura por sql/read.")
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
