# infrastructure/security/database_reference_guard.py
from __future__ import annotations

import re


class DatabaseReferenceError(ValueError):
    pass


class DatabaseReferenceGuard:
    """
    Detecta las bases de datos que una sentencia nombra explícitamente y las
    valida contra una lista blanca.

    El problema que resuelve: `SqlWriteGuard` y `SqlQueryGuard` validan el
    campo `database` de la petición, que es la base de la CONEXIÓN. Pero en
    SQL Server una sentencia puede saltar a otra base de la misma instancia
    con solo cualificar el nombre (`otra_base.dbo.tabla`), y eso no lo miraba
    nadie. Medido el 2026-09-03: con `database: "ruesma"` se escribía en la
    base documental, que la configuración declara cerrada.

    No es un analizador de T-SQL, y no pretende serlo: es un reconocedor de
    nombres cualificados. La forma de nombrar otra base es una sola —prefijar
    el identificador—, y todo lo demás que podría llevar fuera (`USE`, `EXEC`,
    `OPENROWSET`, `OPENDATASOURCE`) ya está prohibido por los guardias.

    Filosofía: ante la duda, RECHAZA. Un guardia que ante lo que no entiende
    deja pasar no es un guardia.
    """

    # Un identificador de SQL Server en las formas que admitimos: normal,
    # entre corchetes o entre comillas dobles.
    _IDENT = r"(?:\[[^\]\r\n]*\]|\"[^\"\r\n]*\"|[A-Za-z_][A-Za-z0-9_$#@]*)"

    # Una cadena cualificada: un identificador y al menos un punto más. La
    # parte tras el punto es opcional para cubrir `base..tabla`, que es SQL
    # válido con el esquema omitido.
    _CADENA_RE = re.compile(rf"{_IDENT}(?:\s*\.\s*(?:{_IDENT})?)+")

    _COMILLAS_DELIMITADORAS = ('[', ']', '"')

    # --- API pública --------------------------------------------------------

    @classmethod
    def extract_database_references(cls, sql: str) -> list[str]:
        """
        Bases citadas por un nombre de TRES partes, en minúsculas y por orden
        de aparición, sin repetir.

        Informativo: no incluye los nombres de cuatro o más partes, que
        `validate()` rechaza aparte. Para decidir, usa `validate()`.
        """
        bases, _ = cls._analizar(sql)
        return bases

    @classmethod
    def validate(cls, sql: str, *, allowed: list[str], contexto: str) -> None:
        """
        Lanza `DatabaseReferenceError` si la sentencia nombra una base fuera de
        `allowed`, o si usa un nombre de cuatro o más partes.

        `contexto` es "lectura" o "escritura", y solo sirve para el mensaje.
        """
        bases, cualificadas_de_mas = cls._analizar(sql)

        if cualificadas_de_mas:
            raise DatabaseReferenceError(
                f"la sentencia usa el nombre cualificado '{cualificadas_de_mas[0]}', de cuatro "
                "partes o más. No se permite: un nombre así apunta a un servidor vinculado, y "
                "no hay ninguno en uso. Usa como mucho base.esquema.tabla."
            )

        permitidas = {base.strip().lower() for base in allowed if base and base.strip()}
        for base in bases:
            if base not in permitidas:
                raise DatabaseReferenceError(
                    f"la sentencia nombra la base de datos '{base}', que no está permitida "
                    f"para {contexto}. Permitidas: "
                    f"{', '.join(sorted(permitidas)) or '(ninguna)'}"
                )

    # --- Interior -----------------------------------------------------------

    @classmethod
    def _analizar(cls, sql: str) -> tuple[list[str], list[str]]:
        """Devuelve (bases de tres partes, nombres de cuatro o más partes)."""
        if not sql or not sql.strip():
            return [], []

        limpio = cls._neutralizar_literales_y_comentarios(sql)

        bases: list[str] = []
        de_mas: list[str] = []
        for match in cls._CADENA_RE.finditer(limpio):
            texto = match.group(0)
            partes = cls._partir(texto)
            # Una última parte vacía significa que el punto final no separa dos
            # identificadores. Solo hay un caso en que eso es inocente: que lo
            # siguiente sea un `*`, como en `dbo.con.*`, SQL corriente que sin
            # esto se leía como tres partes y se rechazaba.
            #
            # Se comprueba QUÉ sigue, y no se descarta a ciegas, porque hay
            # terceros elementos que el reconocedor no sabe leer y que sí son
            # tabla: `tempdb..#t`, `tempdb.dbo.##global`, `dbo.$x`, `dbo.9tabla`.
            # Descartándolos a ciegas, esas referencias pasaban a leerse como
            # dos partes y la base se colaba. Ante un tercer elemento que no se
            # entiende, se trata como referencia y se rechaza (R11).
            #
            # Ojo: solo se mira la ÚLTIMA parte. En `base..tabla` la vacía es
            # la del medio y ahí sí hay tres partes de verdad.
            if len(partes) > 1 and not partes[-1]:
                if limpio[match.end() : match.end() + 1] == "*":
                    partes = partes[:-1]
            if len(partes) <= 2:
                continue
            if len(partes) >= 4:
                de_mas.append(texto.strip())
                continue
            base = cls._normalizar_identificador(partes[0])
            if base and base not in bases:
                bases.append(base)

        return bases, de_mas

    @staticmethod
    def _partir(cadena: str) -> list[str]:
        """
        Parte por los puntos que separan identificadores, respetando los que
        van dentro de corchetes o comillas dobles.
        """
        partes: list[str] = []
        actual: list[str] = []
        cierre: str | None = None
        for caracter in cadena:
            if cierre is not None:
                actual.append(caracter)
                if caracter == cierre:
                    cierre = None
                continue
            if caracter in ("[", '"'):
                cierre = "]" if caracter == "[" else '"'
                actual.append(caracter)
                continue
            if caracter == ".":
                partes.append("".join(actual).strip())
                actual = []
                continue
            actual.append(caracter)
        partes.append("".join(actual).strip())
        return partes

    @classmethod
    def _normalizar_identificador(cls, parte: str) -> str:
        identificador = parte.strip()
        delimitado = (identificador.startswith("[") and identificador.endswith("]")) or (
            identificador.startswith('"') and identificador.endswith('"')
        )
        if delimitado:
            identificador = identificador[1:-1]
        return identificador.strip().lower()

    @staticmethod
    def _neutralizar_literales_y_comentarios(sql: str) -> str:
        """
        Sustituye por espacios el contenido de literales de cadena y de
        comentarios, conservando las posiciones. Sin esto, un
        `WHERE nom = 'a.b.c'` parecería una referencia a otra base.

        Un literal o un comentario sin cerrar es SQL que el motor rechazaría,
        pero aquí no se puede saber dónde termina: se lanza el error en vez de
        adivinar (R11).
        """
        salida: list[str] = []
        indice = 0
        total = len(sql)

        while indice < total:
            caracter = sql[indice]

            # Un identificador entre corchetes se copia tal cual, y ANTES de
            # mirar la comilla simple: dentro de `[Client's Name]` el apóstrofo
            # es una letra más, no el principio de un literal. Sin esto, un
            # identificador así arrancaba un literal falso que se comía el
            # resto de la sentencia y acababa en «literal sin cerrar».
            # SQL Server escapa el corchete de cierre duplicándolo (`]]`).
            if caracter == "[":
                fin = indice + 1
                while fin < total:
                    if sql[fin] == "]":
                        if fin + 1 < total and sql[fin + 1] == "]":
                            fin += 2
                            continue
                        break
                    fin += 1
                if fin >= total:
                    raise DatabaseReferenceError(
                        "la sentencia tiene un identificador entre corchetes sin cerrar; "
                        "no se puede analizar con seguridad y se rechaza."
                    )
                salida.append(sql[indice : fin + 1])
                indice = fin + 1
                continue

            if caracter == "'":
                fin = indice + 1
                while fin < total:
                    if sql[fin] == "'":
                        # Dos comillas seguidas son una comilla escapada.
                        if fin + 1 < total and sql[fin + 1] == "'":
                            fin += 2
                            continue
                        break
                    fin += 1
                if fin >= total:
                    raise DatabaseReferenceError(
                        "la sentencia tiene un literal de cadena sin cerrar; no se puede "
                        "analizar con seguridad y se rechaza."
                    )
                salida.append(" " * (fin - indice + 1))
                indice = fin + 1
                continue

            if sql.startswith("--", indice):
                fin = sql.find("\n", indice)
                if fin == -1:
                    fin = total
                salida.append(" " * (fin - indice))
                indice = fin
                continue

            if sql.startswith("/*", indice):
                fin = sql.find("*/", indice + 2)
                if fin == -1:
                    raise DatabaseReferenceError(
                        "la sentencia tiene un comentario de bloque sin cerrar; no se puede "
                        "analizar con seguridad y se rechaza."
                    )
                salida.append(" " * (fin + 2 - indice))
                indice = fin + 2
                continue

            salida.append(caracter)
            indice += 1

        return "".join(salida)
