# application/use_cases/create_direct_albaran_use_case.py
from __future__ import annotations

from typing import Any

from domain.models.albaran_directo_models import AddDirectAlbaranRequest
from domain.models.albaran_domain_models import (
    AddPurchaseAlbaranResponse,
    AlbaranLinePreview,
)
from application.use_cases.create_purchase_albaran_use_case import (
    CreatePurchaseAlbaranUseCase,
    _ALBARAN_TIP,
    _MOV_DESTIP,
    _MOV_ORITIP,
    _MOV_TIP,
    _POS_STEP,
    _SERIE_PREFIX,
    _CON,
    _DCA,
    _DCAPRO,
    _MOV,
    _r2,
    _now_hhmmss,
    _today_yyyymmdd,
)

_OBRA_TIP = 42  # con.tip de una obra


class CreateDirectAlbaranUseCase(CreatePurchaseAlbaranUseCase):
    """
    Albaran de compra DIRECTO (sin contrato). Reutiliza todos los helpers del
    caso de uso desde contrato (serie, plantillas, balance de stock, ensamblado
    e inserts) pero NO enlaza a contrato: sin ctrprodes, sin docori*, sin
    actualizar ctrpro.canser ni los estados del contrato.
    """

    # ------------------------------------------------------------------ #
    # Resolucion proveedor (por CIF) y obra (por codigo)
    # ------------------------------------------------------------------ #
    def _find_template_by_cif(self, db: str, cif: str, prefix: str) -> dict[str, Any] | None:
        """Ultimo albaran del proveedor (por CIF). Devuelve ide + datos de
        proveedor (entide/entcod/entres/entcif) para clonar la cabecera."""
        sql = (
            "SELECT TOP 1 d.ide, d.entide, d.entcod, d.entres, d.entcif "
            "FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
            "WHERE c.tip = ? AND d.entcif = ? ORDER BY c.ide DESC"
        )
        cols, rows = self._read(db, sql, [_ALBARAN_TIP, cif], max_rows=1)
        if not rows:
            return None
        return dict(zip(cols, rows[0]))

    def _resolve_obra(self, db: str, cod_obra: str) -> int | None:
        cols, rows = self._read(
            db, "SELECT TOP 1 ide FROM dbo.con WHERE tip = ? AND cod = ? ORDER BY ide DESC",
            [_OBRA_TIP, cod_obra], max_rows=1,
        )
        return int(rows[0][0]) if rows else None

    # ------------------------------------------------------------------ #
    # Orquestacion
    # ------------------------------------------------------------------ #
    def run(self, request: AddDirectAlbaranRequest) -> AddPurchaseAlbaranResponse:
        db = request.database
        warnings: list[str] = []

        fec = request.fecha_albaran or _today_yyyymmdd()
        hor = _now_hhmmss()
        fechor = float(f"{fec}.{hor:06d}")
        year2 = (fec // 10000) % 100
        prefix = f"{_SERIE_PREFIX}{year2:02d}/"

        # 1) Resolver obra por codigo.
        obride = self._resolve_obra(db, request.cod_obra)
        if obride is None:
            raise ValueError(f"No se encontro la obra (tip={_OBRA_TIP}) con cod='{request.cod_obra}'.")

        # 2) Resolver proveedor + plantilla de cabecera por CIF.
        prov = self._find_template_by_cif(db, request.cif_proveedor, prefix)
        if prov is None:
            raise ValueError(
                f"No existe ningun albaran previo del proveedor con CIF '{request.cif_proveedor}' "
                "para clonar la cabecera (formas de pago, cuentas...). Crea uno en Sigrid o pide "
                "soporte para resolver el proveedor desde su maestro."
            )
        template_ide = int(prov["ide"])
        entide = int(prov.get("entide") or 0)
        con_tpl = self._full_row_map(db, _CON, template_ide)
        dca_tpl = self._full_row_map(db, _DCA, template_ide)
        if con_tpl is None or dca_tpl is None:
            raise ValueError(f"No se pudo leer la plantilla de cabecera (con/dca) ide={template_ide}.")

        empide = int(request.empide or self._settings.sigrid_albaran_empide)
        cod, _num = self._next_cod(db, prefix)

        # 3) Construir lineas (dcapro) + movimientos (mov). Sin contrato: sin
        # ctrprodes, sin docori*, sin canser.
        balances: dict[tuple[int, int], tuple[float, float]] = {}

        def balance_for(proide: int, almide: int) -> tuple[float, float]:
            key = (proide, almide)
            if key not in balances:
                balances[key] = self._latest_mov_balance(db, proide, almide)
            return balances[key]

        dcapro_tpl_cache: dict[int, dict[str, Any] | None] = {}
        dcapro_rows: list[dict[str, Any]] = []
        mov_rows: list[dict[str, Any]] = []
        line_previews: list[AlbaranLinePreview] = []

        sum_tot = 0.0
        sum_iva = 0.0
        header_almide = request.almide
        header_cenide = request.cenide

        for i, line in enumerate(request.lineas):
            proide = int(line.proide)
            received = float(line.can)
            pre = float(line.pre)

            if proide not in dcapro_tpl_cache:
                dcapro_tpl_cache[proide] = self._latest_dcapro_for_product(db, proide, template_ide)
            tpl = dcapro_tpl_cache[proide]
            if tpl is None:
                tpl = {c: 0 for c in (
                    "cueide", "prepma", "natide", "envide", "reqcuo", "lintip", "taride", "cuoman",
                )}
                warnings.append(
                    f"Producto {proide} sin historico de dcapro: cueide/ivaide/prepma/natide a 0; "
                    "revisa la linea en el dry-run."
                )

            # IVA: tasa de la plantilla del producto (ivacuo/tot), salvo override.
            tpl_tot = _r2(tpl.get("tot"))
            tpl_iva = _r2(tpl.get("ivacuo"))
            rate = (tpl_iva / tpl_tot) if tpl_tot else 0.0
            ivaide = line.ivaide if line.ivaide is not None else tpl.get("ivaide")

            # Almacen / centro de coste de la linea.
            almide = int(request.almide or tpl.get("almide") or 0)
            cenide = int(request.cenide or tpl.get("cenide") or 0)
            if not almide:
                raise ValueError(
                    f"No se pudo determinar el almacen para el producto {proide}. "
                    "Pasalo en 'almide' o usa un producto con historico de albaran."
                )
            if header_almide is None:
                header_almide = almide
            if header_cenide is None:
                header_cenide = cenide

            tot = _r2(received * pre)
            ivacuo = _r2(tot * rate)
            sum_tot += tot
            sum_iva += ivacuo

            row = dict(tpl)
            row["docide"] = None
            row["pos"] = (i + 1) * _POS_STEP
            row["proide"] = proide
            row["pre"] = pre
            row["can"] = received
            row["tar"] = pre
            row["dto"] = ""
            row["tot"] = tot
            row["res"] = line.res if line.res is not None else (tpl.get("res") or "")
            if line.unimed is not None:
                row["unimed"] = line.unimed
            if ivaide is not None:
                row["ivaide"] = ivaide
            row["ivacuo"] = ivacuo
            row["almide"] = almide
            row["obride"] = obride
            if "cenide" in row:
                row["cenide"] = cenide
            if line.paride is not None:
                row["paride"] = line.paride
            # SIN contrato: limpiar origen y seguimiento.
            for f in ("docoritip", "docoricod", "docoriide", "linoriide",
                      "canser", "canfac", "cancan", "canped",
                      "canorilin", "canoriant", "canoriori",
                      "imporiant", "imporiori", "imporiantdiv", "imporioridiv"):
                if f in row:
                    row[f] = "" if isinstance(row.get(f), str) else 0
            dcapro_rows.append(row)

            # mov (idéntico al albaran desde contrato).
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

            line_previews.append(AlbaranLinePreview(
                ctrpro_ide=0, linoriide=0, proide=proide,
                res=row["res"], unimed=row.get("unimed"), cantidad=received,
                precio=pre, total=tot, iva_cuota=ivacuo, almide=almide,
                stock_anterior=stock_ant, stock_resultante=stock_new,
                pmp_anterior=pma_ant, pmp_resultante=pma_new,
            ))

        sum_tot = _r2(sum_tot)
        sum_iva = _r2(sum_iva)
        tot_doc = _r2(sum_tot + sum_iva)
        header_almide = int(header_almide or 0)
        header_cenide = int(header_cenide or 0)

        # 4) Cabecera dca (clon + campos propios). ctride=0 (SIN contrato).
        doc_res = (f"{prov.get('entres') or ''}. ({request.su_referencia})").strip()[:200]
        dca = dict(dca_tpl)
        for _col, _val in (
            ("fecdoc", fec), ("hor", hor),
            ("entref", request.su_referencia), ("eioide", 1),
            ("entide", entide), ("ctride", 0),
            ("obride", obride), ("almide", header_almide), ("cenide", header_cenide),
            ("empide", empide),
        ):
            if _col in dca:
                dca[_col] = _val
        for f in ("entcod", "entres", "entcif"):
            if f in dca and prov.get(f) is not None:
                dca[f] = prov.get(f)
        _header_totals = {
            "impbru": sum_tot, "impnet": sum_tot,
            "totbas": sum_tot, "totiva": sum_iva,
            "totdoc": tot_doc, "tot": tot_doc, "totpag": tot_doc,
            "totbasdiv": sum_tot, "totivadiv": sum_iva, "totdocdiv": tot_doc,
        }
        for _col, _val in _header_totals.items():
            if _col in dca:
                dca[_col] = _val
        for _col in ("impdes", "imprec", "impdesdiv", "imprecdiv"):
            if _col in dca:
                dca[_col] = 0
        if "estser" in dca:
            dca["estser"] = 0
        if "estfac" in dca:
            dca["estfac"] = 0
        if "synckey" in dca:
            dca["synckey"] = ""

        con = dict(con_tpl)
        con["tip"] = _ALBARAN_TIP
        con["cod"] = cod
        con["res"] = doc_res
        con["fec"] = fec
        if "est" in con:
            con["est"] = 1

        totales = {
            "impbru": sum_tot, "impnet": sum_tot, "totbas": sum_tot,
            "totiva": sum_iva, "totdoc": tot_doc, "tot": tot_doc, "totpag": tot_doc,
            "n_lineas": len(request.lineas), "n_recibidas": sum(1 for l in request.lineas if l.can > 0),
        }
        contrato_info = {
            "sin_contrato": True, "obride": obride, "entide": entide,
            "cod_obra": request.cod_obra, "cif_proveedor": request.cif_proveedor,
            "almide": header_almide, "template_ide": template_ide,
        }

        # 5) DRY-RUN.
        if not request.commit:
            con_ide = self._repo.peek_next_ide(database=db, table=_CON)
            dcapro_base = self._repo.peek_next_ide(database=db, table=_DCAPRO)
            mov_base = self._repo.peek_next_ide(database=db, table=_MOV)
            self._assign_ides(con, dca, dcapro_rows, [], mov_rows,
                              con_ide, dcapro_base, 0, mov_base)
            note = (
                "DRY-RUN (albaran directo, SIN contrato): no se ha escrito nada. Revisa cabecera, "
                "lineas y movimientos de stock antes de poner commit=true. Los ide son provisionales."
            )
            return AddPurchaseAlbaranResponse(
                database=db, committed=False, dry_run=True, con_ide=con_ide, cod=cod,
                contrato=contrato_info, cabecera=dca, lineas=line_previews,
                movimientos=mov_rows, estados_contrato={}, totales=totales,
                warnings=warnings + [note],
            )

        # 6) COMMIT.
        if not self._settings.sigrid_domain_write_enabled:
            raise ValueError(
                "Alta de dominio desactivada. Active SIGRID_DOMAIN_WRITE_ENABLED para confirmar."
            )
        if self._settings.allowed_write_databases and db not in self._settings.allowed_write_databases:
            raise ValueError(f"La base '{db}' no esta permitida para escritura.")

        def work(cursor: Any) -> dict[str, Any]:
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.[{_CON}]")
            con_ide = int(cursor.fetchone()[0])
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) FROM dbo.[{_DCAPRO}]")
            dcapro_base = int(cursor.fetchone()[0]) + 1
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) FROM dbo.[{_MOV}]")
            mov_base = int(cursor.fetchone()[0]) + 1

            self._assign_ides(con, dca, dcapro_rows, [], mov_rows,
                              con_ide, dcapro_base, 0, mov_base)

            self._insert(cursor, _CON, con)
            self._insert(cursor, _DCA, dca)
            for row in dcapro_rows:
                self._insert(cursor, _DCAPRO, row)
            for row in mov_rows:
                self._insert(cursor, _MOV, row)
            return {"con_ide": con_ide}

        result = self._repo.run_in_write_transaction(
            database=db,
            timeout_seconds=self._settings.default_write_timeout_seconds,
            applock_resources=[f"SIGRID_IDE_{_CON}", f"SIGRID_IDE_{_DCAPRO}", f"SIGRID_IDE_{_MOV}"],
            applock_timeout_ms=self._settings.applock_timeout_ms,
            max_retries=self._settings.domain_write_max_retries,
            work=work,
        )
        con_ide = int(result["con_ide"])
        return AddPurchaseAlbaranResponse(
            database=db, committed=True, dry_run=False, con_ide=con_ide, cod=cod,
            contrato=contrato_info, cabecera=dca, lineas=line_previews,
            movimientos=mov_rows, estados_contrato={}, totales=totales,
            warnings=warnings + [
                "Albaran directo creado (sin contrato). Verifica abriendolo en Sigrid (stock y totales)."
            ],
        )
