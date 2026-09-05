# application/use_cases/concepto_grafico_statements.py
"""
Constructor PURO de las sentencias de `sigrid/concepto-grafico` (F-004).

Sin E/S: recibe la base de negocio y la documental, y devuelve cada sentencia
como `(sql, params)`. Todo el SQL es constante en el codigo y todos los valores
viajan como `?`; el unico identificador que no es literal es el nombre de la
base documental, que sale de configuracion (NUNCA de la peticion) y pasa por
`IdentifierGuard`. Al construirse, la clase valida TODAS sus sentencias con
`DatabaseReferenceGuard` contra `[negocio, documental]` (R18, R19).

Las constantes de las 29 columnas de `gra` y las 7 de `rcg` salen de
`progress/explore_F-004_mediciones.md` §2.1-2.3. Van explicitas y completas
porque NINGUNA columna tiene DEFAULT [MEDIDO]: omitir una la deja en NULL, que
no es lo que tiene el ERP.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from infrastructure.security.database_reference_guard import DatabaseReferenceGuard
from infrastructure.security.identifier_guard import IdentifierGuard

#: Las 29 columnas de `dbo.gra`, en el orden medido.
GRA_COLUMNAS: tuple[str, ...] = (
    "ide", "cod", "emp", "res", "tex", "cla", "usu", "fec", "nom", "nomori",
    "ima", "gratipide", "vin", "estcon", "cam", "tipocu", "texrev", "numrev",
    "salfec", "salhor", "salusu", "saltex", "mntide", "guid", "graant", "anx",
    "ori", "pul", "tip",
)

#: Las 7 columnas reales de `dbo.rcg`. `feclee` y `fecalt` no constan en
#: `sigrid_tablas.md` pero existen y valen 0 en las 3.680 filas medidas.
RCG_COLUMNAS: tuple[str, ...] = ("ide", "con", "gra", "pos", "cla", "feclee", "fecalt")

#: `vin` = modo de almacenamiento del binario [MEDIDO]. 3 = "incrustado
#: externo": el fichero vive en la documental y se localiza por `(emp, cod)`.
#: Es el 99,9 % de negocio y el 100 % de la documental.
VIN_REPOSITORIO = 3

#: Sigrid ordena los graficos de un concepto con `pos` en multiplos de 64.
POS_PASO = 64

#: Zona horaria del ERP. Sigrid sella en hora local; los workers corren en UTC.
ZONA_DE_MADRID = "Europe/Madrid"

#: En la documental NO existe la clase 35: `gratipide` es 0 y `res` vacio en
#: las 3.679 parejas medidas, aunque en negocio sean 35 y "PARTE FIRMADO".
GRATIPIDE_DOCUMENTAL = 0
RES_DOCUMENTAL = ""

_COLUMNAS_GRA_SQL = ", ".join(GRA_COLUMNAS)
_MARCADORES_GRA = ", ".join(["?"] * len(GRA_COLUMNAS))
_COLUMNAS_RCG_SQL = ", ".join(RCG_COLUMNAS)
_MARCADORES_RCG = ", ".join(["?"] * len(RCG_COLUMNAS))


def _ultimo_domingo(anio: int, mes: int) -> date:
    primero_del_siguiente = (
        date(anio + 1, 1, 1) if mes == 12 else date(anio, mes + 1, 1)
    )
    ultimo = primero_del_siguiente - timedelta(days=1)
    return ultimo - timedelta(days=(ultimo.weekday() + 1) % 7)


def _hora_por_la_regla_de_respaldo(utc: datetime) -> datetime:
    """
    Respaldo para maquinas sin base de zonas horarias (Windows sin `tzdata`).

    La regla europea es fija desde 1996: CET (UTC+1) salvo entre el ultimo
    domingo de marzo a la 01:00 UTC y el ultimo domingo de octubre a la 01:00
    UTC, en que es CEST (UTC+2). Verificada contra `zoneinfo` en 1996-2040.

    No es la via normal —lo es `ZoneInfo`, para que un cambio de la regla llegue
    con `tzdata` y no haya que tocar codigo—, pero se conserva y se prueba con
    los MISMOS casos: si el sistema se queda sin zonas, el endpoint sigue
    sellando bien en vez de reventar.
    """
    entra_el_verano = datetime.combine(_ultimo_domingo(utc.year, 3), time(1, 0))
    sale_el_verano = datetime.combine(_ultimo_domingo(utc.year, 10), time(1, 0))
    horas = 2 if entra_el_verano <= utc < sale_el_verano else 1
    return utc + timedelta(hours=horas)


def hora_local_de_madrid(instante_utc: datetime) -> datetime:
    """
    Hora local de Madrid (naive) a partir de un instante UTC.

    Via normal: `zoneinfo.ZoneInfo("Europe/Madrid")` con `tzdata` en
    `requirements.txt`. Si `ZoneInfo` no encuentra la zona (maquina sin base de
    zonas), y SOLO en ese caso, se cae a `_hora_por_la_regla_de_respaldo`.

    Un instante sin zona se entiende como UTC: los workers de Azure corren en
    UTC y Sigrid sella en hora local.
    """
    utc = (
        instante_utc
        if instante_utc.tzinfo is None
        else instante_utc.astimezone(timezone.utc).replace(tzinfo=None)
    )
    try:
        zona = ZoneInfo(ZONA_DE_MADRID)
    except ZoneInfoNotFoundError:
        return _hora_por_la_regla_de_respaldo(utc)
    return utc.replace(tzinfo=timezone.utc).astimezone(zona).replace(tzinfo=None)


def construir_cod(*, ahora: datetime, sha256: str, usu: str) -> str:
    """
    `gra.cod` con el formato medido de Sigrid: `AAAAMMDDHHMMSS` + 4 digitos +
    `.` + login (3.680 de 3.680 en la clase 35).

    Los cuatro digitos salen del `sha256` en vez de un generador aleatorio: asi
    el `cod` es reproducible en los tests y, sobre todo, EL MISMO en cada
    reintento de la transaccion. Sigrid no interpreta el sello ni esos digitos
    [MEDIDO: tolera 31.941 `cod` que son nombres de fichero]; la unicidad la da
    el indice unico `(emp, cod)`.
    """
    digitos = int(sha256[:8], 16) % 10000
    return f"{ahora:%Y%m%d%H%M%S}{digitos:04d}.{usu}"


class ConceptoGraficoStatements:
    def __init__(self, *, database: str, documental: str) -> None:
        self._database = database.strip()
        self._documental = IdentifierGuard.validate_identifier(
            documental, field_name="SIGRID_DOCUMENT_WRITE_DATABASE"
        )
        doc = f"[{self._documental}]"

        # --- Lecturas (dry-run y commit) ---
        self._l1 = "SELECT ide, tip, emp, cod, res FROM dbo.con WHERE ide = ?"
        self._l2 = "SELECT ide, cod, res, fecbaj, tipaso FROM dbo.auxgra WHERE ide = ?"
        self._l3 = "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?"
        self._l4 = (
            f"SELECT ISNULL(MAX(pos), 0) + {POS_PASO}, COUNT(*) FROM dbo.rcg WHERE con = ?"
        )
        # L5 y L6 cruzan por `(emp, cod)`, NUNCA por `ide`: el join por `ide`
        # devuelve documentos ajenos el 99,85 % de las veces [MEDIDO].
        self._l5 = (
            "SELECT n.ide, n.cod, r.ide, CAST(d.ima AS varbinary(max)) FROM dbo.rcg r "
            "JOIN dbo.gra n ON n.ide = r.gra "
            f"JOIN {doc}.dbo.gra d ON d.emp = n.emp AND d.cod = n.cod "
            "WHERE r.con = ? AND DATALENGTH(d.ima) = ?"
        )
        self._l6 = (
            "SELECT n.ide, n.cod FROM dbo.rcg r "
            "JOIN dbo.gra n ON n.ide = r.gra "
            f"LEFT JOIN {doc}.dbo.gra d ON d.emp = n.emp AND d.cod = n.cod "
            "WHERE r.con = ? AND d.ide IS NULL"
        )

        # --- Escrituras (solo con commit) ---
        self._e1 = (
            f"SELECT ISNULL(MAX(g.ide), 0) + 1 FROM {doc}.dbo.gra g "
            "WITH (UPDLOCK, HOLDLOCK)"
        )
        self._e2 = "SELECT ISNULL(MAX(g.ide), 0) + 1 FROM dbo.gra g WITH (UPDLOCK, HOLDLOCK)"
        self._e3 = "SELECT ISNULL(MAX(r.ide), 0) + 1 FROM dbo.rcg r WITH (UPDLOCK, HOLDLOCK)"
        self._e4 = (
            f"INSERT INTO {doc}.dbo.gra ({_COLUMNAS_GRA_SQL}) VALUES ({_MARCADORES_GRA})"
        )
        self._e5 = f"INSERT INTO dbo.gra ({_COLUMNAS_GRA_SQL}) VALUES ({_MARCADORES_GRA})"
        self._e6 = f"INSERT INTO dbo.rcg ({_COLUMNAS_RCG_SQL}) VALUES ({_MARCADORES_RCG})"
        self._e7_documental = (
            f"SELECT COUNT(*) FROM {doc}.dbo.gra WHERE emp = ? AND cod = ?"
        )
        self._e7_negocio = "SELECT COUNT(*) FROM dbo.gra WHERE emp = ? AND cod = ?"
        self._e7_enlace = "SELECT COUNT(*) FROM dbo.rcg WHERE ide = ?"

        # R19: se valida TODO antes de que nadie abra una conexion. La unica
        # base ajena a la conexion que se nombra es la documental, y solo su
        # `dbo.gra`.
        for sql in self.todas_las_sentencias():
            DatabaseReferenceGuard.validate(
                sql,
                allowed=[self._database, self._documental],
                contexto="escritura",
            )

    def todas_las_sentencias(self) -> tuple[str, ...]:
        return (
            self._l1, self._l2, self._l3, self._l4, self._l5, self._l6,
            self._e1, self._e2, self._e3, self._e4, self._e5, self._e6,
            self._e7_documental, self._e7_negocio, self._e7_enlace,
        )

    # --- Lecturas ---------------------------------------------------------

    def leer_concepto(self, conide: int) -> tuple[str, list[Any]]:
        return self._l1, [conide]

    def leer_clase(self, gratipide: int) -> tuple[str, list[Any]]:
        return self._l2, [gratipide]

    def leer_usuario(self, usu: str) -> tuple[str, list[Any]]:
        return self._l3, [usu]

    def siguiente_pos(self, conide: int) -> tuple[str, list[Any]]:
        return self._l4, [conide]

    def buscar_idempotencia(self, conide: int, bytes_del_fichero: int) -> tuple[str, list[Any]]:
        """
        Binarios ya colgados del concepto con el MISMO tamano. El `sha256` se
        compara despues en Python: `HASHBYTES` no vale en SQL Server 2012
        [MEDIDO]. Filtrar por `DATALENGTH` deja normalmente 0 o 1 filas.
        """
        return self._l5, [conide, bytes_del_fichero]

    def buscar_huerfanas(self, conide: int) -> tuple[str, list[Any]]:
        """Graficos del concepto SIN pareja documental: no tienen binario, asi
        que nunca son candidatos a idempotencia. Solo se avisa de ellos."""
        return self._l6, [conide]

    # --- Reserva de identificadores --------------------------------------

    def reservar_ide_documental(self) -> tuple[str, list[Any]]:
        return self._e1, []

    def reservar_ide_negocio(self) -> tuple[str, list[Any]]:
        return self._e2, []

    def reservar_ide_enlace(self) -> tuple[str, list[Any]]:
        return self._e3, []

    # --- Construccion de las filas ---------------------------------------

    def construir_filas_gra(
        self,
        *,
        ahora: datetime,
        sha256: str,
        emp: int,
        usu: str,
        nom: str,
        res: str,
        gratipide: int,
        contenido: bytes,
    ) -> tuple[str, dict[str, Any], dict[str, Any]]:
        """
        Devuelve `(cod, fila_documental, fila_negocio)`.

        El `cod` se genera UNA vez y las dos filas comparten EL MISMO objeto,
        igual que `emp`: si difirieran en un caracter, el motor no avisaria y el
        grafico quedaria "sin fichero" (asi son los 517 huerfanos `vin=3` de
        2021). Los `ide` nacen a None; los rellena la transaccion al reservarlos,
        cada uno con el contador de SU tabla (los de las dos `gra` no coinciden
        ni se intenta que coincidan).
        """
        cod = construir_cod(ahora=ahora, sha256=sha256, usu=usu)
        fec = int(f"{ahora:%Y%m%d}")

        def fila(*, res_columna: str, gratipide_columna: int, ima: bytes | None) -> dict[str, Any]:
            return {
                "ide": None,
                "cod": cod,
                "emp": emp,
                "res": res_columna,
                "tex": None,
                "cla": "",
                "usu": usu,
                "fec": fec,
                "nom": nom,
                "nomori": nom,          # nom = nomori en las 3.679 parejas
                "ima": ima,
                "gratipide": gratipide_columna,
                "vin": VIN_REPOSITORIO,
                "estcon": 0,
                "cam": None,
                "tipocu": 0,
                "texrev": "",
                "numrev": 0,
                "salfec": 0,
                "salhor": 0,
                "salusu": "",
                "saltex": "",
                "mntide": 0,
                "guid": "",             # vacio en las 643.668 filas [MEDIDO]
                "graant": 0,
                "anx": 0,
                "ori": 0,
                "pul": None,
                "tip": 0,
            }

        documental = fila(
            res_columna=RES_DOCUMENTAL,
            gratipide_columna=GRATIPIDE_DOCUMENTAL,
            ima=contenido,
        )
        negocio = fila(res_columna=res, gratipide_columna=gratipide, ima=None)
        return cod, documental, negocio

    def construir_fila_enlace(
        self, *, ide: int | None, con: int, gra: int | None, pos: int
    ) -> dict[str, Any]:
        return {
            "ide": ide,
            "con": con,
            "gra": gra,
            "pos": pos,
            "cla": 0,
            "feclee": 0,
            "fecalt": 0,
        }

    # --- Insercion ---------------------------------------------------------

    def insertar_documental(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e4, [fila[columna] for columna in GRA_COLUMNAS]

    def insertar_negocio(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e5, [fila[columna] for columna in GRA_COLUMNAS]

    def insertar_enlace(self, fila: dict[str, Any]) -> tuple[str, list[Any]]:
        return self._e6, [fila[columna] for columna in RCG_COLUMNAS]

    # --- Relectura previa al COMMIT (R14) ---------------------------------

    def releer_documental(self, emp: int, cod: str) -> tuple[str, list[Any]]:
        return self._e7_documental, [emp, cod]

    def releer_negocio(self, emp: int, cod: str) -> tuple[str, list[Any]]:
        return self._e7_negocio, [emp, cod]

    def releer_enlace(self, ide: int) -> tuple[str, list[Any]]:
        return self._e7_enlace, [ide]

    # --- Utilidad para el preview -----------------------------------------

    @staticmethod
    def fila_para_preview(fila: dict[str, Any]) -> dict[str, Any]:
        """La fila tal cual se insertaria, con `ima` como su tamano en bytes: el
        binario no viaja de vuelta al cliente (R2, R21)."""
        visible = dict(fila)
        ima = visible.get("ima")
        visible["ima"] = None if ima is None else len(ima)
        return visible
