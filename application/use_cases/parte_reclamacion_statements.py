# application/use_cases/parte_reclamacion_statements.py
"""
Constructor PURO de las sentencias y filas de `sigrid/partes-reclamacion` (F-006).

Sin E/S: devuelve cada sentencia como `(sql, params)` y cada fila como un
diccionario columna -> valor. Todo el SQL es constante y todos los valores
viajan como `?`; ninguna sentencia nombra otra base, y al construirse la clase
las valida TODAS con `DatabaseReferenceGuard` contra la base de la peticion
(R18).

Las constantes de las cinco filas (`con`, `rcp`, `rcpint`, `conext`, `log`)
salen de `specs/F-006-alta-parte-reclamacion/design.md` §Filas, medidas en
`progress/explore_F-006_modelo_parte.md`; nombres y orden de columnas
confirmados con `INFORMATION_SCHEMA.COLUMNS` el 2026-09-24. Van explicitas y
completas porque NINGUNA columna de esas tablas tiene DEFAULT: omitir una la
deja en NULL, que no es lo que escribe el escritorio de Sigrid.

`tip 708`, `'RCPCLI'`, `ope 1` y `tab 'con'` son discriminadores de tipo, no
estados: el estado del parte sale de `sercon.estini` y se comprueba contra
`dbo.conest` en el caso de uso (ARCHITECTURE §7).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from application.use_cases.concepto_grafico_statements import hora_local_de_madrid
from domain.models.parte_reclamacion_models import ParteReclamacionError
from infrastructure.security.database_reference_guard import DatabaseReferenceGuard

#: Tipos de concepto: parte de reclamacion, obra y unidad postventa.
TIP_PARTE = 708
TIP_OBRA = 42
TIP_UNIDAD_POSTVENTA = 707

#: `sercon.cod` de la serie: se guarda LITERAL con sus marcadores (leido el
#: 2026-09-24: ide 213, emp 1, tam 4, estini 1). El prefijo de cada mes se
#: calcula a partir de `con.fec`.
PLANTILLA_SERIE = "RS<año2>.<mes>/"

#: Digitos del numero de la serie. Otro `tam` en `sercon` no esta medido.
TAM_SERIE = 4

#: `rcp.pos` es global, en multiplos de 64, en el orden de `ide`.
POS_PASO = 64

#: Campo extendido «Nº Referencia Externo» del parte (`defext` ide 36).
COD_REFERENCIA_EXTERNA = "RCPCLI"

#: Fila de alta de `dbo.log`: operacion 1, sobre la tabla `con`, origen 0.
LOG_OPE_ALTA = 1
LOG_TAB = "con"
LOG_ORI = 0

#: Las columnas de cada tabla, en su orden fisico.
CON_COLUMNAS: tuple[str, ...] = (
    "ide", "emp", "tip", "subtip", "cod", "res", "fec", "tex", "cee", "est",
    "fecbaj", "tiemod", "ico", "delo", "del", "obr", "doc", "serie", "hor",
)
RCP_COLUMNAS: tuple[str, ...] = (
    "ide", "upvide", "pos", "fec", "hor", "cliide", "recide", "cntide", "tel", "ele",
    "tex", "rcpide", "motrcp", "rcptip", "fecpre", "solrcp", "trcpide", "resubi",
    "texurg", "ofcide",
)
RCPINT_COLUMNAS: tuple[str, ...] = ("ide", "rcpide", "pos", "obrofcide", "cauave")
CONEXT_COLUMNAS: tuple[str, ...] = (
    "ide", "conide", "cod", "camtip", "camtab", "valt", "valn", "valf", "vali",
    "valm", "valb",
)
LOG_COLUMNAS: tuple[str, ...] = (
    "ide", "emp", "ori", "ope", "fec", "hor", "usu", "tab", "tip", "cod", "res",
    "tex", "est", "err",
)

#: Origen de las fechas OLE (las de `con.tiemod`).
_ORIGEN_OLE = datetime(1899, 12, 30, tzinfo=timezone.utc)


def _insert(tabla: str, columnas: tuple[str, ...]) -> str:
    return (
        f"INSERT INTO dbo.{tabla} ({', '.join(columnas)}) "
        f"VALUES ({', '.join(['?'] * len(columnas))})"
    )


def prefijo_de_serie(momento_local: datetime) -> str:
    """`RS<año2>.<mes>/` del mes de `con.fec` (hora local de Madrid)."""
    return PLANTILLA_SERIE.replace("<año2>", f"{momento_local:%y}").replace(
        "<mes>", f"{momento_local:%m}"
    )


def patron_de_cod(prefijo: str, tam: int) -> str:
    """Patron `LIKE` del prefijo seguido de EXACTAMENTE `tam` digitos: asi un
    `cod` tecleado a mano con otra forma no desplaza el `MAX`."""
    return prefijo + "[0-9]" * tam


def siguiente_cod(prefijo: str, max_cod: str | None, tam: int) -> str:
    """El siguiente numero de la serie del mes: `None` -> `0001`."""
    siguiente = 1 if max_cod is None else int(max_cod[len(prefijo):]) + 1
    if siguiente >= 10**tam:
        raise ParteReclamacionError(
            f"La serie {prefijo} ha llegado a su ultimo numero ({max_cod}): no caben mas "
            "partes este mes.",
            codigo="numeracion_agotada",
        )
    return f"{prefijo}{siguiente:0{tam}d}"


def fecha_ole_utc(instante: datetime) -> float:
    """Dias (con fraccion) desde 1899-12-30 en UTC, como `con.tiemod` [medido
    en dos partes]. Un instante sin zona se entiende UTC."""
    utc = (
        instante.replace(tzinfo=timezone.utc)
        if instante.tzinfo is None
        else instante.astimezone(timezone.utc)
    )
    return (utc - _ORIGEN_OLE).total_seconds() / 86400


@dataclass(frozen=True)
class Sellos:
    """Los sellos de tiempo de UN parte, calculados una vez y fuera de la
    transaccion (R16): los reintentos no cambian de mes ni de hora."""

    fec: int        # AAAAMMDD local de Madrid: con.fec, rcp.fec, log.fec
    hor: int        # HHMMSS local de Madrid: rcp.hor, log.hor
    tiemod: float   # fecha OLE en UTC: con.tiemod
    prefijo: str    # RS<aa>.<mm>/ del mes de `fec`


def sellos(instante_utc: datetime) -> Sellos:
    local = hora_local_de_madrid(instante_utc)
    return Sellos(
        fec=int(f"{local:%Y%m%d}"),
        hor=int(f"{local:%H%M%S}"),
        tiemod=fecha_ole_utc(instante_utc),
        prefijo=prefijo_de_serie(local),
    )


class ParteReclamacionStatements:
    def __init__(self, *, database: str) -> None:
        self._database = database.strip()

        # --- Lecturas comunes del lote (L1-L7) ---
        self._l1 = (
            "SELECT ide, emp, tam, estini FROM dbo.sercon WHERE tip = ? AND cod = ? AND act = 1"
        )
        self._l2 = "SELECT est, cod FROM dbo.conest WHERE tip = ? AND est = ?"
        self._l3 = "SELECT ide, emp, cod FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?"
        self._l4 = "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?"
        self._l5 = (
            "SELECT c.ide, c.cod, ISNULL(u.cliide, 0), ISNULL(u.peride, 0) FROM dbo.upv u "
            "JOIN dbo.con c ON c.ide = u.ide WHERE u.obride = ? AND c.emp = ? AND c.tip = ?"
        )
        self._l6 = (
            "SELECT o.ide, o.pos, a.cod, p.cod FROM dbo.obrofc o "
            "LEFT JOIN dbo.auxofc a ON a.ide = o.ofcide "
            "LEFT JOIN dbo.con p ON p.ide = o.prvide WHERE o.obride = ?"
        )
        self._l7_tipos = "SELECT ide, cod, fecbaj FROM dbo.auxtrcp"
        self._l7_clases = "SELECT ide, cod, fecbaj FROM dbo.auxrcp"
        self._l7_oficios = "SELECT ide, cod, fecbaj FROM dbo.auxofc"

        # --- Por parte: idempotencia (L8 = E1) y numeracion provisional ---
        self._l8 = (
            "SELECT c.ide, c.cod, r.upvide FROM dbo.conext x "
            "JOIN dbo.con c ON c.ide = x.conide LEFT JOIN dbo.rcp r ON r.ide = c.ide "
            "WHERE x.cod = ? AND x.valt = ? AND c.tip = ? AND c.emp = ?"
        )
        self._l9 = "SELECT MAX(cod) FROM dbo.con WHERE emp = ? AND tip = ? AND cod LIKE ?"
        self._l10 = f"SELECT ISNULL(MAX(pos), 0) + {POS_PASO} FROM dbo.rcp"

        # --- Dentro de la transaccion: reservas bajo bloqueo (E2-E7) ---
        self._e2 = (
            "SELECT MAX(cod) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) "
            "WHERE emp = ? AND tip = ? AND cod LIKE ?"
        )
        self._e3 = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.con WITH (UPDLOCK, HOLDLOCK)"
        self._e4 = f"SELECT ISNULL(MAX(pos), 0) + {POS_PASO} FROM dbo.rcp WITH (UPDLOCK, HOLDLOCK)"
        self._e5 = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.rcpint WITH (UPDLOCK, HOLDLOCK)"
        self._e6 = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.conext WITH (UPDLOCK, HOLDLOCK)"
        self._e7 = "SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.log WITH (UPDLOCK, HOLDLOCK)"

        # --- Revalidacion (E8) ---
        self._e8_upv = "SELECT COUNT(*) FROM dbo.upv WHERE ide = ? AND obride = ?"
        self._e8_obrofc = "SELECT COUNT(*) FROM dbo.obrofc WHERE ide = ? AND obride = ?"

        # --- Inserciones (E9-E13), en este orden ---
        self._e9 = _insert("con", CON_COLUMNAS)
        self._e10 = _insert("rcp", RCP_COLUMNAS)
        self._e11 = _insert("rcpint", RCPINT_COLUMNAS)
        self._e12 = _insert("conext", CONEXT_COLUMNAS)
        self._e13 = _insert("log", LOG_COLUMNAS)

        # --- Relecturas por clave (E14): con NOCOUNT ON el rowcount no vale ---
        self._e14_con = "SELECT COUNT(*) FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?"
        self._e14_rcp = "SELECT COUNT(*) FROM dbo.rcp WHERE ide = ?"
        self._e14_rcpint = "SELECT COUNT(*) FROM dbo.rcpint WHERE rcpide = ?"
        self._e14_conext = "SELECT COUNT(*) FROM dbo.conext WHERE conide = ? AND cod = ?"
        self._e14_log = "SELECT COUNT(*) FROM dbo.log WHERE ide = ?"

        # R18: se valida TODO antes de que nadie abra una conexion.
        for sql in self.todas_las_sentencias():
            DatabaseReferenceGuard.validate(
                sql, allowed=[self._database], contexto="escritura"
            )

    def todas_las_sentencias(self) -> tuple[str, ...]:
        return (
            self._l1, self._l2, self._l3, self._l4, self._l5, self._l6,
            self._l7_tipos, self._l7_clases, self._l7_oficios,
            self._l8, self._l9, self._l10,
            self._e2, self._e3, self._e4, self._e5, self._e6, self._e7,
            self._e8_upv, self._e8_obrofc,
            self._e9, self._e10, self._e11, self._e12, self._e13,
            self._e14_con, self._e14_rcp, self._e14_rcpint, self._e14_conext, self._e14_log,
        )

    # --- Lecturas comunes del lote -------------------------------------------

    def leer_serie(self) -> tuple[str, list[Any]]:
        return self._l1, [TIP_PARTE, PLANTILLA_SERIE]

    def leer_estado_inicial(self, estini: int) -> tuple[str, list[Any]]:
        return self._l2, [TIP_PARTE, estini]

    def leer_obra(self, emp: int, cod: str) -> tuple[str, list[Any]]:
        return self._l3, [emp, TIP_OBRA, cod]

    def leer_usuario(self, usu: str) -> tuple[str, list[Any]]:
        return self._l4, [usu]

    def leer_unidades_postventa(self, obride: int, emp: int) -> tuple[str, list[Any]]:
        return self._l5, [obride, emp, TIP_UNIDAD_POSTVENTA]

    def leer_oficios_de_la_obra(self, obride: int) -> tuple[str, list[Any]]:
        return self._l6, [obride]

    def leer_tipos(self) -> tuple[str, list[Any]]:
        return self._l7_tipos, []

    def leer_clases(self) -> tuple[str, list[Any]]:
        return self._l7_clases, []

    def leer_oficios(self) -> tuple[str, list[Any]]:
        return self._l7_oficios, []

    # --- Por parte ------------------------------------------------------------

    def buscar_referencia(self, referencia: str, emp: int) -> tuple[str, list[Any]]:
        """L8 (dry-run) y E1 (bajo el applock de referencias): la MISMA sentencia."""
        return self._l8, [COD_REFERENCIA_EXTERNA, referencia, TIP_PARTE, emp]

    def ultimo_cod(self, emp: int, prefijo: str) -> tuple[str, list[Any]]:
        return self._l9, [emp, TIP_PARTE, patron_de_cod(prefijo, TAM_SERIE)]

    def siguiente_pos_sin_bloqueo(self) -> tuple[str, list[Any]]:
        return self._l10, []

    # --- Reservas bajo bloqueo --------------------------------------------------

    def reservar_cod(self, emp: int, prefijo: str) -> tuple[str, list[Any]]:
        return self._e2, [emp, TIP_PARTE, patron_de_cod(prefijo, TAM_SERIE)]

    def reservar_ide_con(self) -> tuple[str, list[Any]]:
        return self._e3, []

    def reservar_pos_rcp(self) -> tuple[str, list[Any]]:
        return self._e4, []

    def reservar_ide_rcpint(self) -> tuple[str, list[Any]]:
        return self._e5, []

    def reservar_ide_conext(self) -> tuple[str, list[Any]]:
        return self._e6, []

    def reservar_ide_log(self) -> tuple[str, list[Any]]:
        return self._e7, []

    # --- Revalidacion ---------------------------------------------------------

    def revalidar_unidad_postventa(self, upvide: int, obride: int) -> tuple[str, list[Any]]:
        return self._e8_upv, [upvide, obride]

    def revalidar_oficio_de_obra(self, obrofcide: int, obride: int) -> tuple[str, list[Any]]:
        return self._e8_obrofc, [obrofcide, obride]

    # --- Filas ------------------------------------------------------------------

    def construir_filas(
        self,
        *,
        emp: int,
        est: int,
        descripcion: str,
        descripcion_larga: str | None,
        fec: int,
        hor: int,
        tiemod: float,
        upvide: int,
        cliide: int,
        recide: int,
        clase_ide: int,
        rcptip: int,
        trcpide: int,
        resubi: str,
        ofcide: int,
        intervinientes: list[tuple[int, bool]],
        referencia: str,
        usu: str,
    ) -> dict[str, Any]:
        """
        Las cinco filas de un parte, con `ide`, `cod` y `pos` a `None`: los
        pone `numerar` en cada intento de la transaccion (reentrante).
        `intervinientes` son pares `(obrofc.ide, causante)`.
        """
        con = {
            "ide": None,
            "emp": emp,
            "tip": TIP_PARTE,
            "subtip": 0,
            "cod": None,
            "res": descripcion,
            "fec": fec,
            "tex": None,
            "cee": 0,
            "est": est,
            "fecbaj": 0,
            "tiemod": tiemod,
            "ico": "",
            "delo": "",
            "del": "",
            "obr": "",
            "doc": "",
            "serie": 0,
            "hor": 0,
        }
        rcp = {
            "ide": None,
            "upvide": upvide,
            "pos": None,
            "fec": fec,
            "hor": hor,
            "cliide": cliide,            # ISNULL(upv.cliide, 0): propietario de la UPV
            "recide": recide,            # ISNULL(upv.peride, 0): persona de la UPV
            "cntide": 0,
            "tel": None,
            "ele": None,
            "tex": descripcion_larga or descripcion,
            "rcpide": clase_ide,         # auxrcp.ide o 0
            "motrcp": "",
            "rcptip": rcptip,
            "fecpre": 0,
            "solrcp": None,
            "trcpide": trcpide,
            "resubi": resubi,
            "texurg": "",
            "ofcide": ofcide,
        }
        rcpint = [
            {
                "ide": None,
                "rcpide": None,
                "pos": 0,                # escritorio e importador; el MAX+64 es del portal
                "obrofcide": obrofcide,
                "cauave": 1 if causante else 0,
            }
            for obrofcide, causante in intervinientes
        ]
        conext = {
            "ide": None,
            "conide": None,
            "cod": COD_REFERENCIA_EXTERNA,
            "camtip": 0,
            "camtab": "",
            "valt": referencia,
            "valn": 0,
            "valf": 0,
            "vali": 0,
            "valm": None,
            "valb": None,
        }
        log = {
            "ide": None,
            "emp": emp,
            "ori": LOG_ORI,
            "ope": LOG_OPE_ALTA,
            "fec": fec,
            "hor": hor,
            "usu": usu,
            "tab": LOG_TAB,
            "tip": TIP_PARTE,
            "cod": None,
            "res": descripcion,
            "tex": None,
            "est": est,
            "err": None,
        }
        return {"con": con, "rcp": rcp, "rcpint": rcpint, "conext": conext, "log": log}

    @staticmethod
    def numerar(
        filas: dict[str, Any],
        *,
        cod: str,
        ide_con: int,
        pos_rcp: int,
        ide_rcpint: int | None,
        ide_conext: int,
        ide_log: int,
    ) -> dict[str, Any]:
        """Copia de `filas` con la numeracion puesta. No toca `filas`: cada
        reintento numera sobre las filas limpias. Los `rcpint` son consecutivos
        desde `ide_rcpint`, que es `None` cuando el parte no trae ninguno (no
        se reserva un `ide` que no se va a usar)."""
        return {
            "con": {**filas["con"], "ide": ide_con, "cod": cod},
            "rcp": {**filas["rcp"], "ide": ide_con, "pos": pos_rcp},
            "rcpint": [
                {**fila, "ide": ide_rcpint + desplazamiento, "rcpide": ide_con}
                for desplazamiento, fila in enumerate(filas["rcpint"])
            ],
            "conext": {**filas["conext"], "ide": ide_conext, "conide": ide_con},
            "log": {**filas["log"], "ide": ide_log, "cod": cod},
        }

    # --- Inserciones ------------------------------------------------------------

    def insertar_con(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e9, [fila[c] for c in CON_COLUMNAS]

    def insertar_rcp(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e10, [fila[c] for c in RCP_COLUMNAS]

    def insertar_rcpint(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e11, [fila[c] for c in RCPINT_COLUMNAS]

    def insertar_conext(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e12, [fila[c] for c in CONEXT_COLUMNAS]

    def insertar_log(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e13, [fila[c] for c in LOG_COLUMNAS]

    # --- Relecturas previas al COMMIT (R14) --------------------------------------

    def releer_con(self, emp: int, cod: str) -> tuple[str, list[Any]]:
        return self._e14_con, [emp, TIP_PARTE, cod]

    def releer_rcp(self, ide: int) -> tuple[str, list[Any]]:
        return self._e14_rcp, [ide]

    def releer_rcpint(self, rcpide: int) -> tuple[str, list[Any]]:
        return self._e14_rcpint, [rcpide]

    def releer_conext(self, conide: int) -> tuple[str, list[Any]]:
        return self._e14_conext, [conide, COD_REFERENCIA_EXTERNA]

    def releer_log(self, ide: int) -> tuple[str, list[Any]]:
        return self._e14_log, [ide]
