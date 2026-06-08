# application/use_cases/create_purchase_albaran_use_case.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from config.settings import Settings
from domain.models.albaran_domain_models import (
    AddPurchaseAlbaranRequest,
    AddPurchaseAlbaranResponse,
    AlbaranLinePreview,
)
from domain.models.sql_models import SqlReadRequest
from infrastructure.repositories.sql_server_repository import SqlServerRepository

# --- Tipos de concepto / constantes Sigrid (descubiertas por ingenieria inversa) ---
_CONTRACT_TIP = 44          # con.tip de un contrato de compra (ctr)
_ALBARAN_TIP = 14           # con.tip de un albaran de compra (dca)
_SERIE_PREFIX = "AC"        # prefijo de la serie estandar de albaran de compra
_POS_STEP = 64              # Sigrid ordena las lineas con pos en multiplos de 64

# Tablas
_CON = "con"
_DCA = "dca"
_DCAPRO = "dcapro"
_CTR = "ctr"
_CTRPRO = "ctrpro"
_CTRPRODES = "ctrprodes"
_MOV = "mov"

# mov: tipo de movimiento de ENTRADA por compra (tip=1), origen proveedor
# (oritip=5), destino almacen (destip=2), documento albaran de compra (doctip=14).
_MOV_TIP = 1
_MOV_ORITIP = 5
_MOV_DESTIP = 2

# Columnas EXACTAS del ledger de stock `mov` (orden segun esquema vivo de Sigrid).
_MOV_COLUMNS = [
    "ide", "emp", "docide", "linide", "tip", "oritip", "oriide", "destip",
    "deside", "proide", "doctip", "fec", "hor", "fecdoc", "canent", "cansal",
    "pre", "prc", "prepma", "nueusa", "almide", "almcan", "almpma", "fecblo",
    "fechor",
]

# Columnas EXACTAS de la tabla de enlace contrato->albaran `ctrprodes`.
_CTRPRODES_COLUMNS = [
    "ide", "docproide", "can", "docdestip", "docdescod", "docdeside",
    "lindeside", "ctrproactide",
]

# Campos de la cabecera `dca` que en un albaran NUEVO no deben heredarse de la
# plantilla con un valor stale (se ponen a su valor inicial).
_DCA_RESET_FIELDS = ("synckey",)


def _r2(value: Any) -> float:
    return round(float(value or 0), 2)


def _today_yyyymmdd() -> int:
    now = datetime.now()
    return now.year * 10000 + now.month * 100 + now.day


def _now_hhmmss() -> int:
    now = datetime.now()
    return now.hour * 10000 + now.minute * 100 + now.second


class CreatePurchaseAlbaranUseCase:
    """
    Da de alta un albaran de compra (con.tip=14 -> dca + dcapro) a partir de un
    contrato de compra existente, replicando fielmente lo que hace Sigrid:

      - Inserta el concepto (con) + cabecera (dca), con `cod` de la serie AC.
      - Crea como `dcapro` SOLO las lineas indicadas en `lineas_recibidas`
        (las no indicadas NO se replican), enlazandolas al contrato por
        docoritip/docoriide/linoriide.
      - Crea el enlace contrato->albaran en `ctrprodes` (una fila por linea).
      - Genera el ledger de stock `mov` (una fila por linea incluida),
        recalculando almcan (stock) y almpma (PMP) en orden por (producto, almacen).
      - Actualiza `ctrpro.canser` de las lineas servidas y recalcula
        `ctr.estser`/`ctr.estfac` (sumando sobre TODAS las lineas del contrato,
        no solo las del albaran).

    DRY-RUN por defecto: no escribe; devuelve el preview completo. El COMMIT
    requiere SIGRID_DOMAIN_WRITE_ENABLED y base permitida; va en UNA transaccion
    (reserva de ide por applock + MAX+1 + reintento), igual que el alta de lineas
    de contrato.

    Nota de stock: `proalm`/`pro` NO se tocan; el stock vive solo en `mov`.
    """

    def __init__(self, repository: SqlServerRepository, settings: Settings) -> None:
        self._repo = repository
        self._settings = settings

    # ------------------------------------------------------------------ #
    # Helpers de lectura (usan execute_read_query, que NO aplica el guard de
    # SELECT; el repositorio si limita filas con max_rows).
    # ------------------------------------------------------------------ #
    def _read(self, db: str, sql: str, params: list[Any], max_rows: int = 1000) -> tuple[list[str], list[tuple[Any, ...]]]:
        cols, rows, _ = self._repo.execute_read_query(
            SqlReadRequest.model_validate(
                {"database": db, "sql": sql, "parameters": params, "max_rows": max_rows}
            )
        )
        return cols, rows

    def _next_cod(self, db: str, prefix: str) -> tuple[str, int]:
        """cod = prefix + (MAX(sufijo numerico del anio) + 1). Por anio."""
        sql = (
            "SELECT ISNULL(MAX(TRY_CONVERT(int, SUBSTRING(cod, ?, 40))), 0) + 1 "
            "FROM dbo.con WHERE tip = ? AND cod LIKE ?"
        )
        _cols, rows = self._read(db, sql, [len(prefix) + 1, _ALBARAN_TIP, prefix + "%"], max_rows=1)
        nxt = int(rows[0][0]) if rows else 1
        return f"{prefix}{nxt}", nxt

    def _find_template_ide(self, db: str, entide: int, prefix: str) -> int | None:
        """ide de una cabecera dca plantilla: ultimo albaran del mismo proveedor;
        si no hay, ultimo de la serie AC; si no, cualquier albaran."""
        sql_prov = (
            "SELECT TOP 1 c.ide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
            "WHERE c.tip = ? AND d.entide = ? ORDER BY c.ide DESC"
        )
        _c, rows = self._read(db, sql_prov, [_ALBARAN_TIP, entide], max_rows=1)
        if rows:
            return int(rows[0][0])
        sql_serie = (
            "SELECT TOP 1 ide FROM dbo.con WHERE tip = ? AND cod LIKE ? ORDER BY ide DESC"
        )
        _c, rows = self._read(db, sql_serie, [_ALBARAN_TIP, prefix + "%"], max_rows=1)
        if rows:
            return int(rows[0][0])
        _c, rows = self._read(db, "SELECT TOP 1 ide FROM dbo.con WHERE tip = ? ORDER BY ide DESC", [_ALBARAN_TIP], max_rows=1)
        return int(rows[0][0]) if rows else None

    def _full_row_map(self, db: str, table: str, ide: int) -> dict[str, Any] | None:
        res = self._repo.read_full_row(database=db, table=table, ide=ide)
        if res is None:
            return None
        cols, values = res
        return dict(zip(cols, values))

    def _latest_dcapro_for_product(self, db: str, proide: int, template_doc_ide: int | None) -> dict[str, Any] | None:
        """Plantilla de linea: ultima dcapro del MISMO producto (arrastra cueide,
        prepma, natide correctos). Fallback: primera linea del albaran plantilla."""
        cols, rows = self._read(
            db, "SELECT TOP 1 * FROM dbo.dcapro WHERE proide = ? ORDER BY ide DESC", [proide], max_rows=1
        )
        if rows:
            return dict(zip(cols, rows[0]))
        if template_doc_ide is not None:
            cols, rows = self._read(
                db, "SELECT TOP 1 * FROM dbo.dcapro WHERE docide = ? ORDER BY ide ASC", [template_doc_ide], max_rows=1
            )
            if rows:
                return dict(zip(cols, rows[0]))
        return None

    def _latest_mov_balance(self, db: str, proide: int, almide: int) -> tuple[float, float]:
        """(stock, pmp) actuales = almcan/almpma del mov de mayor ide para
        (producto, almacen). (0, 0) si no hay historico."""
        cols, rows = self._read(
            db,
            "SELECT TOP 1 almcan, almpma FROM dbo.mov WHERE proide = ? AND almide = ? ORDER BY ide DESC",
            [proide, almide],
            max_rows=1,
        )
        if not rows:
            return 0.0, 0.0
        stock = float(rows[0][0] or 0)
        pma = float(rows[0][1] or 0)
        return stock, pma

    # ------------------------------------------------------------------ #
    # Orquestacion
    # ------------------------------------------------------------------ #
    def run(self, request: AddPurchaseAlbaranRequest) -> AddPurchaseAlbaranResponse:
        db = request.database
        warnings: list[str] = []

        fec = request.fecha_albaran or _today_yyyymmdd()
        hor = _now_hhmmss()
        fechor = float(f"{fec}.{hor:06d}")
        year2 = (fec // 10000) % 100
        prefix = f"{_SERIE_PREFIX}{year2:02d}/"

        # 1) Localizar el contrato (misma terna que el endpoint de lineas).
        cols, rows = self._repo.locate_contract(
            database=db,
            cod_contrato=request.cod_contrato,
            cod_obra=request.cod_obra,
            cif_proveedor=request.cif_proveedor,
            contract_tip=_CONTRACT_TIP,
        )
        if not rows:
            raise ValueError(
                f"No se encontro un contrato (tip={_CONTRACT_TIP}) con cod='{request.cod_contrato}', "
                f"obra='{request.cod_obra}' y CIF='{request.cif_proveedor}'."
            )
        if len(rows) > 1:
            raise ValueError(
                f"Se encontraron {len(rows)} contratos con esos criterios; el localizador debe devolver exactamente uno."
            )
        ctr_loc = dict(zip(cols, rows[0]))
        ctride = int(ctr_loc["ide"])
        obride = int(ctr_loc["obride"])

        # 2) Fila completa del contrato (proveedor, almacen, centro de coste...).
        ctr = self._full_row_map(db, _CTR, ctride)
        if ctr is None:
            raise ValueError(f"No se pudo leer la cabecera del contrato ide={ctride}.")
        entide = int(ctr.get("entide") or 0)          # concepto proveedor (mov.oriide)
        ctr_almide = int(ctr.get("almide") or 0)      # almacen de la obra
        ctr_cenide = int(ctr.get("cenide") or 0)      # centro de coste
        empide = int(request.empide or self._settings.sigrid_albaran_empide)

        # 3) Lineas del contrato (todas; en orden de pos).
        line_cols, line_rows = self._repo.read_rows_by(
            database=db, table=_CTRPRO, where_column="docide", where_value=ctride, order_by="pos",
        )
        if not line_rows:
            raise ValueError("El contrato no tiene lineas (ctrpro); no hay nada que recepcionar.")
        contract_lines = [dict(zip(line_cols, r)) for r in line_rows]
        line_by_ide = {int(l["ide"]): l for l in contract_lines}

        # 4) Mapa de cantidades recibidas y validacion.
        received_map: dict[int, float] = {}
        for rl in request.lineas_recibidas:
            if rl.ctrpro_ide not in line_by_ide:
                raise ValueError(
                    f"La linea ctrpro_ide={rl.ctrpro_ide} no pertenece al contrato {request.cod_contrato}."
                )
            received_map[rl.ctrpro_ide] = received_map.get(rl.ctrpro_ide, 0.0) + float(rl.cantidad)
        if not received_map:
            raise ValueError(
                "Debes indicar al menos una linea en 'lineas_recibidas': el albaran "
                "solo incluye las lineas indicadas."
            )
        for line_ide, qty in received_map.items():
            line = line_by_ide[line_ide]
            pend = _r2(line.get("can")) - _r2(line.get("canser"))
            if qty > pend + 1e-9:
                warnings.append(
                    f"Linea {line_ide}: cantidad recibida ({qty}) supera lo pendiente de servir ({pend})."
                )

        # 5) Codigo de serie y plantillas (concepto/cabecera).
        cod, _num = self._next_cod(db, prefix)
        template_ide = self._find_template_ide(db, entide, prefix)
        if template_ide is None:
            raise ValueError("No existe ningun albaran de compra previo para usar como plantilla de cabecera.")
        con_tpl = self._full_row_map(db, _CON, template_ide)
        dca_tpl = self._full_row_map(db, _DCA, template_ide)
        if con_tpl is None or dca_tpl is None:
            raise ValueError(f"No se pudo leer la plantilla de cabecera (con/dca) ide={template_ide}.")
        if int(dca_tpl.get("entide") or 0) != entide:
            warnings.append(
                "La plantilla de cabecera no es del mismo proveedor; revisa formas de pago/cuentas en el dry-run."
            )

        # 6) Construir filas (sin ide). Balances de stock por (producto, almacen).
        balances: dict[tuple[int, int], tuple[float, float]] = {}

        def balance_for(proide: int, almide: int) -> tuple[float, float]:
            key = (proide, almide)
            if key not in balances:
                balances[key] = self._latest_mov_balance(db, proide, almide)
            return balances[key]

        dcapro_tpl_cache: dict[int, dict[str, Any] | None] = {}
        dcapro_rows: list[dict[str, Any]] = []
        ctrprodes_rows: list[dict[str, Any]] = []
        mov_rows: list[dict[str, Any]] = []
        line_previews: list[AlbaranLinePreview] = []

        sum_tot = 0.0
        sum_iva = 0.0
        served_updates: list[tuple[int, float]] = []  # (ctrpro_ide, recibido) para canser += recibido

        # El albaran SOLO incluye las lineas indicadas en lineas_recibidas, en el
        # orden del contrato (por pos). Las no indicadas no se replican.
        lines_to_process = [l for l in contract_lines if int(l["ide"]) in received_map]

        for i, line in enumerate(lines_to_process):
            line_ide = int(line["ide"])
            proide = int(line.get("proide") or 0)
            almide = int(line.get("almide") or ctr_almide)
            received = float(received_map.get(line_ide, 0.0))
            pre = float(line.get("pre") or 0)
            line_tot = _r2(line.get("tot"))
            line_iva = _r2(line.get("ivacuo"))
            rate = (line_iva / line_tot) if line_tot else 0.0

            tot = _r2(received * pre)
            ivacuo = _r2(tot * rate)
            sum_tot += tot
            sum_iva += ivacuo
            if received > 0:
                served_updates.append((line_ide, received))

            # --- dcapro: clonar plantilla del mismo producto y sobreescribir ---
            if proide not in dcapro_tpl_cache:
                dcapro_tpl_cache[proide] = self._latest_dcapro_for_product(db, proide, template_ide)
            tpl = dcapro_tpl_cache[proide]
            if tpl is not None:
                row = dict(tpl)
            else:
                # Fallback minimo (producto sin historico de dcapro): se construye
                # con los campos del contrato; cueide/prepma/natide a 0.
                row = {c: 0 for c in (
                    "cueide", "prepma", "natide", "envide", "reqcuo", "lintip", "taride", "cuoman",
                )}
                warnings.append(f"Producto {proide} sin historico de dcapro: cueide/prepma/natide quedan a 0.")

            row["docide"] = None  # se fija al ide del concepto al reservar
            row["pos"] = (i + 1) * _POS_STEP
            row["proide"] = proide
            row["pre"] = pre
            row["can"] = received
            row["tar"] = float(line.get("tar") or pre)
            row["dto"] = line.get("dto") if line.get("dto") not in (None,) else ""
            row["tot"] = tot
            row["res"] = line.get("res") or ""
            row["tex"] = line.get("tex") if line.get("tex") is not None else ""
            row["ivaide"] = line.get("ivaide")
            row["ivacuo"] = ivacuo
            if line.get("unimed") is not None:
                row["unimed"] = line.get("unimed")
            row["almide"] = almide
            row["obride"] = obride
            if line.get("cenide") is not None:
                row["cenide"] = line.get("cenide")
            elif ctr_cenide:
                row["cenide"] = ctr_cenide
            if line.get("caaide") is not None:
                row["caaide"] = line.get("caaide")
            if line.get("paride") is not None:
                row["paride"] = line.get("paride")
            # Enlace al contrato de origen.
            row["docoritip"] = _CONTRACT_TIP
            row["docoricod"] = request.cod_contrato
            row["docoriide"] = ctride
            row["linoriide"] = line_ide
            row["canoriori"] = _r2(line.get("can"))
            row["imporiori"] = line_tot
            # Seguimiento del propio albaran (recien creado, nada servido/facturado).
            for f in ("canser", "canfac", "cancan", "canped", "canorilin", "canoriant",
                      "imporiant", "imporiantdiv", "imporioridiv"):
                if f in row:
                    row[f] = 0
            dcapro_rows.append(row)

            # --- mov: ledger de stock (recalculo de almcan/almpma en orden) ---
            stock_ant, pma_ant = balance_for(proide, almide)
            if received > 0:
                stock_new = stock_ant + received
                pma_new = ((stock_ant * pma_ant) + (received * pre)) / stock_new if stock_new else pre
            else:
                stock_new = stock_ant
                pma_new = pma_ant
            balances[(proide, almide)] = (stock_new, pma_new)

            mov_rows.append({
                "ide": None, "emp": 1, "docide": None, "linide": None,
                "tip": _MOV_TIP, "oritip": _MOV_ORITIP, "oriide": entide,
                "destip": _MOV_DESTIP, "deside": almide, "proide": proide,
                "doctip": _ALBARAN_TIP, "fec": fec, "hor": hor, "fecdoc": 0,
                "canent": received, "cansal": 0.0, "pre": pre, "prc": pre,
                "prepma": pma_new, "nueusa": 0, "almide": almide,
                "almcan": stock_new, "almpma": pma_new, "fecblo": 0, "fechor": fechor,
            })

            # --- ctrprodes: enlace contrato->albaran ---
            ctrprodes_rows.append({
                "ide": None, "docproide": line_ide, "can": received,
                "docdestip": _ALBARAN_TIP, "docdescod": cod, "docdeside": None,
                "lindeside": None, "ctrproactide": 0,
            })

            line_previews.append(AlbaranLinePreview(
                ctrpro_ide=line_ide, linoriide=line_ide, proide=proide,
                res=row["res"], unimed=row.get("unimed"), cantidad=received,
                precio=pre, total=tot, iva_cuota=ivacuo, almide=almide,
                stock_anterior=stock_ant, stock_resultante=stock_new,
                pmp_anterior=pma_ant, pmp_resultante=pma_new,
            ))

        sum_tot = _r2(sum_tot)
        sum_iva = _r2(sum_iva)
        tot_doc = _r2(sum_tot + sum_iva)

        # Descripcion del documento: vive en con.res (el concepto), NO en dca.
        doc_res = (f"{ctr.get('entres') or ''}. ({request.su_referencia})").strip()[:200]

        # 7) Cabecera dca (clon de plantilla + campos propios). IMPORTANTE:
        # cod/res/fec son columnas del CONCEPTO `con`, no de la extension `dca`;
        # aqui solo se fijan columnas que existen realmente en `dca` (guardadas
        # con `if ... in dca` para no anadir columnas inexistentes al INSERT).
        dca = dict(dca_tpl)
        for _col, _val in (
            ("fecdoc", fec), ("hor", hor),
            ("entref", request.su_referencia), ("eioide", 1),
            ("entide", entide), ("ctride", ctride), ("obride", obride),
            ("almide", ctr_almide), ("cenide", ctr_cenide),
        ):
            if _col in dca:
                dca[_col] = _val
        for f in ("entcod", "entres", "entcif"):
            if f in dca and ctr.get(f) is not None:
                dca[f] = ctr.get(f)
        if "empide" in dca:
            dca["empide"] = empide
        # Totales de cabecera: SOLO columnas realmente presentes en la plantilla
        # (evita anadir claves espurias que romperian el INSERT del commit).
        _header_totals = {
            "impbru": sum_tot, "impnet": sum_tot,
            "totbas": sum_tot, "totiva": sum_iva,
            "totdoc": tot_doc, "tot": tot_doc, "totpag": tot_doc,
            # Divisa: en compra nacional (EUR) la divisa coincide con la base.
            "totbasdiv": sum_tot, "totivadiv": sum_iva, "totdocdiv": tot_doc,
        }
        for _col, _val in _header_totals.items():
            if _col in dca:
                dca[_col] = _val
        # Descuento/recargo de cabecera: un albaran nuevo no arrastra los de la
        # plantilla; se ponen a 0 para que los totales cuadren con las lineas.
        for _col in ("impdes", "imprec", "impdesdiv", "imprecdiv"):
            if _col in dca:
                dca[_col] = 0
        if "estser" in dca:
            dca["estser"] = 0
        if "estfac" in dca:
            dca["estfac"] = 0
        for f in _DCA_RESET_FIELDS:
            if f in dca:
                dca[f] = "" if isinstance(dca.get(f), str) else 0

        # Concepto con (parent) clonado.
        con = dict(con_tpl)
        con["tip"] = _ALBARAN_TIP
        con["cod"] = cod
        con["res"] = doc_res
        con["fec"] = fec
        if "est" in con:
            con["est"] = 1

        # 8) Recalculo de estados del contrato (sumas sobre TODAS las lineas).
        sum_can = sum(_r2(l.get("can")) for l in contract_lines)
        sum_canser_before = sum(_r2(l.get("canser")) for l in contract_lines)
        sum_canfac = sum(_r2(l.get("canfac")) for l in contract_lines)
        delta_ser = sum(q for _ide, q in served_updates)
        sum_canser_after = _r2(sum_canser_before + delta_ser)
        estser_after = 1 if sum_canser_after >= _r2(sum_can) else 0
        estfac_after = 1 if _r2(sum_canfac) >= _r2(sum_can) else 0
        estados = {
            "estser_before": int(ctr.get("estser") or 0),
            "estfac_before": int(ctr.get("estfac") or 0),
            "estser_after": estser_after,
            "estfac_after": estfac_after,
            "sum_can": _r2(sum_can),
            "sum_canser_before": _r2(sum_canser_before),
            "sum_canser_after": sum_canser_after,
            "sum_canfac": _r2(sum_canfac),
        }
        totales = {
            "impbru": sum_tot, "impnet": sum_tot, "totbas": sum_tot,
            "totiva": sum_iva, "totdoc": tot_doc, "tot": tot_doc, "totpag": tot_doc,
            "n_lineas": len(dcapro_rows), "n_recibidas": len(served_updates),
            "n_lineas_contrato": len(contract_lines),
        }
        contrato_info = {
            "ctride": ctride, "obride": obride, "cod_contrato": request.cod_contrato,
            "cod_obra": request.cod_obra, "cif_proveedor": request.cif_proveedor,
            "entide": entide, "almide": ctr_almide, "template_ide": template_ide,
        }

        # 9) DRY-RUN (por defecto): asignar ides provisionales (peek) y devolver.
        if not request.commit:
            con_ide = self._repo.peek_next_ide(database=db, table=_CON)
            dcapro_base = self._repo.peek_next_ide(database=db, table=_DCAPRO)
            ctrprodes_base = self._repo.peek_next_ide(database=db, table=_CTRPRODES)
            mov_base = self._repo.peek_next_ide(database=db, table=_MOV)
            self._assign_ides(con, dca, dcapro_rows, ctrprodes_rows, mov_rows,
                              con_ide, dcapro_base, ctrprodes_base, mov_base)
            self._sync_previews(line_previews, dcapro_rows)
            note = (
                "DRY-RUN: no se ha escrito nada. Revisa cabecera, lineas, movimientos de stock y "
                "estados antes de poner commit=true. Los ide son provisionales (MAX+1 actual)."
            )
            return AddPurchaseAlbaranResponse(
                database=db, committed=False, dry_run=True, con_ide=con_ide, cod=cod,
                contrato=contrato_info, cabecera=dca, lineas=line_previews,
                movimientos=mov_rows, estados_contrato=estados, totales=totales,
                warnings=warnings + [note],
            )

        # 10) COMMIT real.
        if not self._settings.sigrid_domain_write_enabled:
            raise ValueError(
                "Alta de dominio desactivada. Active SIGRID_DOMAIN_WRITE_ENABLED para confirmar "
                "escrituras (el dry-run no lo necesita)."
            )
        if self._settings.allowed_write_databases and db not in self._settings.allowed_write_databases:
            raise ValueError(f"La base '{db}' no esta permitida para escritura.")

        def work(cursor: Any) -> dict[str, Any]:
            # Reservar ide en cada tabla (MAX+1 bajo applock).
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.[{_CON}]")
            con_ide = int(cursor.fetchone()[0])
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) FROM dbo.[{_DCAPRO}]")
            dcapro_base = int(cursor.fetchone()[0]) + 1
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) FROM dbo.[{_CTRPRODES}]")
            ctrprodes_base = int(cursor.fetchone()[0]) + 1
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) FROM dbo.[{_MOV}]")
            mov_base = int(cursor.fetchone()[0]) + 1

            self._assign_ides(con, dca, dcapro_rows, ctrprodes_rows, mov_rows,
                              con_ide, dcapro_base, ctrprodes_base, mov_base)

            # INSERT con (parent) + dca (extension), mismo ide.
            self._insert(cursor, _CON, con)
            self._insert(cursor, _DCA, dca)
            for row in dcapro_rows:
                self._insert(cursor, _DCAPRO, row)
            for row in ctrprodes_rows:
                self._insert(cursor, _CTRPRODES, row)
            for row in mov_rows:
                self._insert(cursor, _MOV, row)

            # UPDATE ctrpro.canser += recibido (relativo, concurrencia-segura).
            for line_ide, qty in served_updates:
                cursor.execute(
                    f"UPDATE dbo.[{_CTRPRO}] SET canser = canser + ? WHERE ide = ?",
                    qty, line_ide,
                )
            # UPDATE estados de cabecera del contrato.
            cursor.execute(
                f"UPDATE dbo.[{_CTR}] SET estser = ?, estfac = ? WHERE ide = ?",
                estser_after, estfac_after, ctride,
            )
            return {"con_ide": con_ide}

        result = self._repo.run_in_write_transaction(
            database=db,
            timeout_seconds=self._settings.default_write_timeout_seconds,
            applock_resources=[
                f"SIGRID_IDE_{_CON}", f"SIGRID_IDE_{_DCAPRO}",
                f"SIGRID_IDE_{_CTRPRODES}", f"SIGRID_IDE_{_MOV}",
            ],
            applock_timeout_ms=self._settings.applock_timeout_ms,
            max_retries=self._settings.domain_write_max_retries,
            work=work,
        )
        con_ide = int(result["con_ide"])
        self._sync_previews(line_previews, dcapro_rows)
        return AddPurchaseAlbaranResponse(
            database=db, committed=True, dry_run=False, con_ide=con_ide, cod=cod,
            contrato=contrato_info, cabecera=dca, lineas=line_previews,
            movimientos=mov_rows, estados_contrato=estados, totales=totales,
            warnings=warnings + [
                "Albaran creado. Verifica abriendolo en Sigrid (stock, totales y enlace al contrato)."
            ],
        )

    # ------------------------------------------------------------------ #
    # Utilidades de ensamblado
    # ------------------------------------------------------------------ #
    @staticmethod
    def _assign_ides(
        con: dict[str, Any], dca: dict[str, Any], dcapro_rows: list[dict[str, Any]],
        ctrprodes_rows: list[dict[str, Any]], mov_rows: list[dict[str, Any]],
        con_ide: int, dcapro_base: int, ctrprodes_base: int, mov_base: int,
    ) -> None:
        con["ide"] = con_ide
        dca["ide"] = con_ide  # la extension comparte el ide del concepto
        for i, row in enumerate(dcapro_rows):
            row["ide"] = dcapro_base + i
            row["docide"] = con_ide
        for i, row in enumerate(ctrprodes_rows):
            row["ide"] = ctrprodes_base + i
            row["docdeside"] = con_ide
            row["lindeside"] = dcapro_base + i
        for i, row in enumerate(mov_rows):
            row["ide"] = mov_base + i
            row["docide"] = con_ide
            row["linide"] = dcapro_base + i

    @staticmethod
    def _sync_previews(previews: list[AlbaranLinePreview], dcapro_rows: list[dict[str, Any]]) -> None:
        # (placeholder por si se quiere exponer el ide de linea en el preview)
        return None

    @staticmethod
    def _insert(cursor: Any, table: str, row: dict[str, Any]) -> None:
        cols = list(row.keys())
        collist = ", ".join(f"[{c}]" for c in cols)
        placeholders = ", ".join("?" for _ in cols)
        cursor.execute(
            f"INSERT INTO dbo.[{table}] ({collist}) VALUES ({placeholders})",
            *[row[c] for c in cols],
        )
