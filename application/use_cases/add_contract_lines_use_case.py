# application/use_cases/add_contract_lines_use_case.py
from __future__ import annotations

from typing import Any

from config.settings import Settings
from domain.models.sigrid_domain_models import AddContractLinesRequest, AddContractLinesResponse
from infrastructure.repositories.sql_server_repository import SqlServerRepository

_CTR = "ctr"
_LINE = "ctrpro"
_CONTRACT_TIP = 44

# Campos de encadenamiento de documentos (origen/seguimiento) que en una linea
# NUEVA y manual no deben heredarse de la plantilla.
_CHAIN_FIELDS = (
    "docoritip", "docoricod", "docoriide", "linoriide",
    "canorilin", "canoriant", "canoriori", "imporiant", "imporiori",
    "imporiantdiv", "imporioridiv",
    "dncide", "dncproide", "comide", "comlinide", "rqsproide",
    "canser", "canfac", "cancan", "canped",
)


def _r2(value: Any) -> float:
    return round(float(value or 0), 2)


class AddContractLinesUseCase:
    def __init__(self, repository: SqlServerRepository, settings: Settings) -> None:
        self._repo = repository
        self._settings = settings

    def run(self, request: AddContractLinesRequest) -> AddContractLinesResponse:
        db = request.database

        # 1) Localizar el contrato por (cod_contrato + cod_obra + CIF).
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
                f"Se encontraron {len(rows)} contratos con esos criterios; "
                "el localizador debe devolver exactamente uno."
            )
        ctr_map = dict(zip(cols, rows[0]))
        ctride = int(ctr_map["ide"])
        obride = int(ctr_map["obride"])

        # 2) Lineas actuales del contrato (para plantilla y para max pos/numlin).
        line_cols, line_rows = self._repo.read_rows_by(
            database=db, table=_LINE, where_column="docide", where_value=ctride, order_by="pos",
        )

        if request.template_line_ide is not None:
            tpl = self._repo.read_full_row(database=db, table=_LINE, ide=request.template_line_ide)
            if tpl is None:
                raise ValueError(f"No existe la linea plantilla ide={request.template_line_ide}.")
            line_cols, tpl_values = tpl
            tmap = dict(zip(line_cols, tpl_values))
            if int(tmap.get("docide")) != ctride:
                raise ValueError("La linea plantilla no pertenece al contrato localizado.")
            template_ide = request.template_line_ide
        else:
            if not line_rows:
                raise ValueError(
                    "El contrato no tiene lineas; indica 'template_line_ide' de una linea "
                    "con la misma estructura para clonarla."
                )
            tmap = dict(zip(line_cols, line_rows[-1]))
            template_ide = int(tmap["ide"])

        # Tasa de IVA efectiva de la plantilla (ivacuo/tot).
        t_tot = _r2(tmap.get("tot"))
        t_iva = _r2(tmap.get("ivacuo"))
        iva_rate = (t_iva / t_tot) if t_tot else 0.0

        # Max pos / numlin del contrato.
        pos_idx = line_cols.index("pos")
        numlin_idx = line_cols.index("numlin")
        max_pos = max((int(r[pos_idx] or 0) for r in line_rows), default=0)
        max_numlin = max((int(r[numlin_idx] or 0) for r in line_rows), default=0)

        # 3) Construir las lineas nuevas clonando la plantilla.
        new_rows: list[dict[str, Any]] = []
        sum_tot = 0.0
        sum_iva = 0.0
        for i, line in enumerate(request.lines):
            row = dict(tmap)
            row["docide"] = ctride
            row["obride"] = obride
            row["res"] = line.res
            row["tex"] = line.tex if line.tex is not None else ""
            row["can"] = float(line.can)
            row["pre"] = float(line.pre)
            tot = _r2(line.can * line.pre)
            row["tot"] = tot
            row["tar"] = float(line.pre)
            row["dto"] = ""
            row["ivacuo"] = _r2(tot * iva_rate)
            if line.unimed is not None:
                row["unimed"] = line.unimed
            if line.paride is not None:
                row["paride"] = line.paride
            if line.proide is not None:
                row["proide"] = line.proide
            row["pos"] = max_pos + 1 + i
            row["numlin"] = max_numlin + 1 + i
            # Limpiar encadenamiento de documentos (linea nueva, sin origen).
            for field in _CHAIN_FIELDS:
                if field in row:
                    row[field] = "" if isinstance(row.get(field), str) else 0
            new_rows.append(row)
            sum_tot += tot
            sum_iva += row["ivacuo"]

        sum_tot = _r2(sum_tot)
        sum_iva = _r2(sum_iva)

        # 4) Totales de cabecera (modelo aditivo; informativo en la respuesta).
        keys = ("impbru", "impnet", "impdes", "imprec", "totbas", "totiva", "totdoc", "tot", "totpag")
        before = {k: ctr_map.get(k) for k in keys}
        has_global_adj = (_r2(ctr_map.get("impdes")) != 0) or (_r2(ctr_map.get("imprec")) != 0)
        after = dict(before)
        after["impbru"] = _r2(_r2(before["impbru"]) + sum_tot)
        after["impnet"] = _r2(_r2(before["impnet"]) + sum_tot)
        after["totbas"] = _r2(_r2(before["totbas"]) + sum_tot)
        after["totiva"] = _r2(_r2(before["totiva"]) + sum_iva)
        after["totdoc"] = _r2(_r2(before["totdoc"]) + sum_tot + sum_iva)
        after["tot"] = _r2(_r2(before["tot"]) + sum_tot + sum_iva)
        after["totpag"] = _r2(_r2(before["totpag"]) + sum_tot + sum_iva)

        # 5) DRY-RUN (por defecto).
        if not request.commit:
            base = self._repo.peek_next_ide(database=db, table=_LINE)
            reserved: list[int] = []
            preview: list[dict[str, Any]] = []
            for i, row in enumerate(new_rows):
                r = dict(row)
                r["ide"] = base + i
                reserved.append(base + i)
                preview.append(r)
            note = "DRY-RUN: no se ha escrito nada. Revisa estas filas y los totales antes de poner commit=true."
            if has_global_adj:
                note += (
                    " ATENCION: el contrato tiene descuento/recargo global (impdes/imprec != 0); "
                    "el COMMIT esta bloqueado para no corromper totales (gestionar desde Sigrid)."
                )
            return AddContractLinesResponse(
                dry_run=True, committed=False, database=db, ctride=ctride, obride=obride,
                cod_contrato=request.cod_contrato, cif_proveedor=request.cif_proveedor,
                template_line_ide=template_ide, reserved_ctrpro_ides=reserved, ctrpro=preview,
                header_totals_before=before, header_totals_after=after, note=note,
            )

        # 6) COMMIT real.
        if not self._settings.sigrid_domain_write_enabled:
            raise ValueError(
                "Alta de dominio desactivada. Active SIGRID_DOMAIN_WRITE_ENABLED para confirmar "
                "escrituras (el dry-run no lo necesita)."
            )
        if self._settings.allowed_write_databases and db not in self._settings.allowed_write_databases:
            raise ValueError(f"La base '{db}' no esta permitida para escritura.")
        if has_global_adj:
            raise ValueError(
                "El contrato tiene descuento/recargo global (impdes/imprec != 0). COMMIT bloqueado: "
                "recalcular sus totales requiere logica adicional; hazlo desde Sigrid o pide soporte."
            )

        def work(cursor: Any) -> list[int]:
            cursor.execute(f"SELECT ISNULL(MAX(ide), 0) FROM dbo.[{_LINE}]")
            base = int(cursor.fetchone()[0])
            reserved: list[int] = []
            for i, row in enumerate(new_rows):
                line_ide = base + 1 + i
                ins = dict(row)
                ins["ide"] = line_ide
                ins_cols = list(ins.keys())
                collist = ", ".join(f"[{c}]" for c in ins_cols)
                placeholders = ", ".join("?" for _ in ins_cols)
                cursor.execute(
                    f"INSERT INTO dbo.[{_LINE}] ({collist}) VALUES ({placeholders})",
                    *[ins[c] for c in ins_cols],
                )
                reserved.append(line_ide)

            # Actualizar totales de la cabecera de forma RELATIVA (concurrencia-segura).
            cursor.execute(
                f"UPDATE dbo.[{_CTR}] SET "
                "impbru = impbru + ?, impnet = impnet + ?, totbas = totbas + ?, "
                "totiva = totiva + ?, totdoc = totdoc + ?, tot = tot + ?, totpag = totpag + ? "
                "WHERE ide = ?",
                sum_tot, sum_tot, sum_tot, sum_iva, sum_tot + sum_iva, sum_tot + sum_iva,
                sum_tot + sum_iva, ctride,
            )
            return reserved

        reserved = self._repo.run_in_write_transaction(
            database=db,
            timeout_seconds=self._settings.default_write_timeout_seconds,
            applock_resources=[f"SIGRID_IDE_{_LINE}"],
            applock_timeout_ms=self._settings.applock_timeout_ms,
            max_retries=self._settings.domain_write_max_retries,
            work=work,
        )

        committed: list[dict[str, Any]] = []
        for i, row in enumerate(new_rows):
            r = dict(row)
            r["ide"] = reserved[i]
            committed.append(r)
        return AddContractLinesResponse(
            dry_run=False, committed=True, database=db, ctride=ctride, obride=obride,
            cod_contrato=request.cod_contrato, cif_proveedor=request.cif_proveedor,
            template_line_ide=template_ide, reserved_ctrpro_ides=reserved, ctrpro=committed,
            header_totals_before=before, header_totals_after=after,
            note="Lineas anadidas y totales de cabecera actualizados. Verifica abriendo el contrato en Sigrid.",
        )
