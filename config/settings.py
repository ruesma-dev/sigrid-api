# config/settings.py
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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
                except Exception:
                    parsed = None
                if not isinstance(parsed, list):
                    raise ValueError(f"Formato no soportado para lista de enteros: {value!r}")
                crudos = [str(item).strip() for item in parsed]
            else:
                crudos = [item.strip() for item in raw.split(",")]
        else:
            raise ValueError(f"Formato no soportado para lista de enteros: {value!r}")

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