# config/settings.py
from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class _ParesJson(list):
    """Los pares `(clave, valor)` de un objeto JSON, en orden y con repeticiones,
    tal como los entrega `json.loads(..., object_pairs_hook=...)`."""


class Settings(BaseSettings):
    sql_driver: str = Field(..., alias="SQL_DRIVER")
    sql_server_host: str = Field(..., alias="SQL_SERVER_HOST")
    sql_server_port: int = Field(..., alias="SQL_SERVER_PORT")

    # --- Credenciales de LECTURA (ro_user) ---
    sql_server_username: str = Field(..., alias="SQL_SERVER_USERNAME")
    sql_server_password: str = Field(..., alias="SQL_SERVER_PASSWORD")

    # --- Credenciales de ESCRITURA (user_rw); opcionales ---
    sql_server_write_username: str | None = Field(default=None, alias="SQL_SERVER_WRITE_USERNAME")
    sql_server_write_password: str | None = Field(default=None, alias="SQL_SERVER_WRITE_PASSWORD")

    default_query_timeout_seconds: int = Field(30, alias="DEFAULT_QUERY_TIMEOUT_SECONDS")
    max_query_timeout_seconds: int = Field(120, alias="MAX_QUERY_TIMEOUT_SECONDS")

    default_max_rows: int = Field(200, alias="DEFAULT_MAX_ROWS")
    max_allowed_rows: int = Field(1000, alias="MAX_ALLOWED_ROWS")
    max_inline_binary_bytes: int = Field(65536, alias="MAX_INLINE_BINARY_BYTES")

    allowed_databases: list[str] = Field(default_factory=list, alias="ALLOWED_DATABASES")
    allowed_query_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_QUERY_PREFIXES")

    # --- Escritura generica (endpoint sql/write) ---
    allowed_write_databases: list[str] = Field(default_factory=list, alias="ALLOWED_WRITE_DATABASES")
    allowed_write_prefixes: list[str] = Field(default_factory=list, alias="ALLOWED_WRITE_PREFIXES")

    default_write_timeout_seconds: int = Field(30, alias="DEFAULT_WRITE_TIMEOUT_SECONDS")
    max_write_timeout_seconds: int = Field(120, alias="MAX_WRITE_TIMEOUT_SECONDS")

    default_max_affected_rows: int = Field(200, alias="DEFAULT_MAX_AFFECTED_ROWS")
    max_affected_rows: int = Field(1000, alias="MAX_AFFECTED_ROWS")

    # --- Batch de escritura ---
    # Numero maximo de sentencias por peticion sql/write y uso de
    # fast_executemany de pyodbc para los parameter_sets (executemany).
    max_statements_per_batch: int = Field(20, alias="MAX_STATEMENTS_PER_BATCH")
    use_fast_executemany: bool = Field(True, alias="USE_FAST_EXECUTEMANY")

    require_where_on_update_delete: bool = Field(True, alias="REQUIRE_WHERE_ON_UPDATE_DELETE")

    # --- Alta de DOMINIO en Sigrid (lineas de contrato, etc.) ---
    sigrid_domain_write_enabled: bool = Field(False, alias="SIGRID_DOMAIN_WRITE_ENABLED")
    applock_timeout_ms: int = Field(10000, alias="APPLOCK_TIMEOUT_MS")
    domain_write_max_retries: int = Field(3, alias="DOMAIN_WRITE_MAX_RETRIES")

    # Empleado (empide) por defecto en la cabecera de un albaran creado por la
    # API; sobreescribible por peticion. 2425207 = GRIS MARTINEZ, PABLO.
    sigrid_albaran_empide: int = Field(2425207, alias="SIGRID_ALBARAN_EMPIDE")

    # --- Adjuntar un documento a un concepto (endpoint sigrid/concepto-grafico) ---
    # Los siete defectos son CERRADOS: con ellos el endpoint responde
    # 'escritura_documental_deshabilitada' y ninguna lista blanca admite nada.
    # Abrirlo es un acto deliberado de configuracion, no un descuido.
    sigrid_document_write_enabled: bool = Field(False, alias="SIGRID_DOCUMENT_WRITE_ENABLED")
    # Base DOCUMENTAL (ruesma_rep). Vacia = endpoint apagado, tambien en dry-run.
    # NO se anade a ALLOWED_WRITE_DATABASES: sql/write sigue sin poder nombrarla.
    sigrid_document_write_database: str = Field("", alias="SIGRID_DOCUMENT_WRITE_DATABASE")
    sigrid_document_max_bytes: int = Field(10485760, alias="SIGRID_DOCUMENT_MAX_BYTES")
    # Firmas binarias admitidas, comparadas como bytes ASCII contra el principio
    # del fichero decodificado.
    sigrid_document_allowed_magic: list[str] = Field(
        default_factory=lambda: ["%PDF-"], alias="SIGRID_DOCUMENT_ALLOWED_MAGIC"
    )
    # Listas blancas de con.tip (tipo de concepto) y de gra.gratipide (clase de
    # grafico). Vacias = no se admite ningun concepto ni ninguna clase.
    sigrid_document_allowed_contip: list[int] = Field(
        default_factory=list, alias="SIGRID_DOCUMENT_ALLOWED_CONTIP"
    )
    sigrid_document_allowed_gratipide: list[int] = Field(
        default_factory=list, alias="SIGRID_DOCUMENT_ALLOWED_GRATIPIDE"
    )
    sigrid_document_write_timeout_seconds: int = Field(
        120, alias="SIGRID_DOCUMENT_WRITE_TIMEOUT_SECONDS"
    )

    # --- Alta de partes de reclamacion en lote (endpoint sigrid/partes-reclamacion) ---
    # Defectos CERRADOS: sin interruptor no hay commit, y con la lista de
    # prefijos vacia toda referencia externa se rechaza (tambien en dry-run).
    # En despliegue: SIGRID_RECLAMACION_PREFIJOS_REFERENCIA=["PVI-"] (Q1 de F-006).
    sigrid_reclamacion_write_enabled: bool = Field(False, alias="SIGRID_RECLAMACION_WRITE_ENABLED")
    sigrid_reclamacion_max_partes: int = Field(50, alias="SIGRID_RECLAMACION_MAX_PARTES")
    sigrid_reclamacion_prefijos_referencia: list[str] = Field(
        default_factory=list, alias="SIGRID_RECLAMACION_PREFIJOS_REFERENCIA"
    )
    # El balanceador corta a los 230 s: pasado este presupuesto no se empieza
    # ningun parte mas y los restantes vuelven como `no_procesado`.
    sigrid_reclamacion_presupuesto_segundos: int = Field(
        150, alias="SIGRID_RECLAMACION_PRESUPUESTO_SEGUNDOS"
    )

    # --- Alta de albaranes de compra, modo extendido (F-009, R10) ---
    # Los seis defectos son CERRADOS: sin interruptor no hay commit (tampoco en
    # el clasico ni en albaran-directo, R8); con los prefijos vacios toda
    # referencia se rechaza; sin productos ni naturalezas no hay lineas sin
    # vincular; sin empresas no se encuentra ninguna obra. Todo tambien en
    # dry-run. Despliegue (T19), SOLO en JSON: ["ALB-"], ["MA9999", "QA9999",
    # "XA9999"], [1] y {"MA9999": "MA99", "QA9999": "QA99", "XA9999": "XA99"}.
    sigrid_albaran_write_enabled: bool = Field(False, alias="SIGRID_ALBARAN_WRITE_ENABLED")
    sigrid_albaran_prefijos_referencia: list[str] = Field(
        default_factory=list, alias="SIGRID_ALBARAN_PREFIJOS_REFERENCIA"
    )
    sigrid_albaran_productos_sin_contrato: list[str] = Field(
        default_factory=list, alias="SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO"
    )
    sigrid_albaran_empresas_obra: list[int] = Field(
        default_factory=list, alias="SIGRID_ALBARAN_EMPRESAS_OBRA"
    )
    sigrid_albaran_max_lineas: int = Field(100, alias="SIGRID_ALBARAN_MAX_LINEAS")
    # Naturaleza (auxpronat.cod) de las lineas sin vincular, por producto (H34).
    # `NoDecode`: el texto del entorno llega TAL CUAL a `parse_string_dict`; si
    # lo decodificara pydantic-settings, un `{"A": "x", "A": "y"}` perderia la
    # clave repetida antes de que nadie pudiera rechazarlo.
    sigrid_albaran_naturaleza_por_producto: Annotated[dict[str, str], NoDecode] = Field(
        default_factory=dict, alias="SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO"
    )

    model_config = SettingsConfigDict(
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator(
        "allowed_databases",
        "allowed_query_prefixes",
        "allowed_write_databases",
        "allowed_write_prefixes",
        "sigrid_document_allowed_magic",
        "sigrid_reclamacion_prefijos_referencia",
        "sigrid_albaran_prefijos_referencia",
        "sigrid_albaran_productos_sin_contrato",
        mode="before",
    )
    @classmethod
    def parse_string_list(cls, value: Any) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []

            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except Exception:
                    pass

            return [item.strip() for item in raw.split(",") if item.strip()]

        raise ValueError(f"Formato no soportado para lista: {value!r}")

    @field_validator(
        "sigrid_document_allowed_contip",
        "sigrid_document_allowed_gratipide",
        "sigrid_albaran_empresas_obra",
        mode="before",
    )
    @classmethod
    def parse_int_list(cls, value: Any) -> list[int]:
        """
        Lista blanca de enteros, en JSON (`[708]`) o en CSV (`708,707`), como
        `parse_string_list` pero exigiendo enteros.

        Ante un valor que no se entiende NO degrada a lista vacia: falla al
        arrancar. Una lista blanca mal escrita que quedara en `[]` cerraria la
        puerta, si; pero una que quedara a medias la abriria a medias sin que
        nadie se enterase, y ese es el fallo que no se puede permitir.
        """
        if value is None:
            return []

        if isinstance(value, list):
            crudos = [str(item).strip() for item in value]
        elif isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    parsed = None
                if not isinstance(parsed, list):
                    raise ValueError(f"Formato no soportado para lista de enteros: {value!r}")
                crudos = [str(item).strip() for item in parsed]
            else:
                crudos = [item.strip() for item in raw.split(",")]
        else:
            # ValueError y no TypeError a proposito: pydantic convierte el
            # primero en un ValidationError legible y deja escapar el segundo.
            raise ValueError(  # noqa: TRY004
                f"Formato no soportado para lista de enteros: {value!r}"
            )

        enteros: list[int] = []
        for crudo in crudos:
            if not crudo:
                continue
            try:
                enteros.append(int(crudo))
            except ValueError:
                raise ValueError(
                    f"'{crudo}' no es un entero: revisa la lista blanca."
                ) from None
        return enteros

    @field_validator("sigrid_albaran_naturaleza_por_producto", mode="before")
    @classmethod
    def parse_string_dict(cls, value: Any) -> dict[str, str]:
        """
        Mapeo de textos en JSON (`{"MA9999": "MA99"}`), con claves y valores
        recortados y no vacios. Vacio o ausente => `{}`.

        Como `parse_int_list`, ante lo que no entiende NO degrada a `{}`: falla
        al arrancar. CSV, lista, texto suelto, valores que no son texto, vacios
        o claves repetidas (tambien tras recortar) son un error de
        configuracion, y un mapeo a medias abriria a medias las lineas sin
        vincular sin que nadie se enterase.
        """
        if value is None:
            return {}

        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return {}
            try:
                pares = json.loads(raw, object_pairs_hook=_ParesJson)
            except json.JSONDecodeError:
                raise ValueError(
                    f"Formato no soportado para el mapeo (debe ser un objeto JSON): {value!r}"
                ) from None
            if not isinstance(pares, _ParesJson):
                # Solo un objeto JSON sale como `_ParesJson` (con sus pares en
                # orden y sin perder las claves repetidas): `[]`, una lista o
                # un texto suelto no son un mapeo.
                raise ValueError(  # noqa: TRY004 (ValueError a proposito, ver abajo)
                    f"Formato no soportado para el mapeo (debe ser un objeto JSON): {value!r}"
                )
        elif isinstance(value, dict):
            pares = list(value.items())
        else:
            # ValueError y no TypeError: pydantic lo convierte en un
            # ValidationError legible (ver `parse_int_list`).
            raise ValueError(  # noqa: TRY004
                f"Formato no soportado para el mapeo (debe ser un objeto JSON): {value!r}"
            )

        mapeo: dict[str, str] = {}
        for clave, valor in pares:
            if not isinstance(clave, str) or not isinstance(valor, str):
                raise ValueError(  # noqa: TRY004 (ValueError a proposito, ver abajo)
                    f"El mapeo solo admite textos: {clave!r}: {valor!r}."
                )
            clave_limpia, valor_limpio = clave.strip(), valor.strip()
            if not clave_limpia or not valor_limpio:
                raise ValueError(f"El mapeo no admite textos vacios: {clave!r}: {valor!r}.")
            if clave_limpia in mapeo:
                raise ValueError(f"Clave repetida en el mapeo: {clave_limpia!r}.")
            mapeo[clave_limpia] = valor_limpio
        return mapeo

    @property
    def write_enabled(self) -> bool:
        return bool(
            self.sql_server_write_username
            and self.sql_server_write_password
            and self.allowed_write_prefixes
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()