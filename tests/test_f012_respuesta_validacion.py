# tests/test_f012_respuesta_validacion.py
"""
F-012 · R4, R6 y R11: `validation_error_response`, el 400 de validación común.

Sin red y sin base: modelos Pydantic mínimos definidos aquí. La «lista de hoy»
es `json.loads(json.dumps(exc.errors()))`, lo que las rutas devolvían cuando la
serialización no fallaba; el helper debe dar exactamente eso (R6) y, cuando hay
un valor no serializable, su `str` en vez de un 500 (R4).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Literal

import pytest
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator
from pydantic_core import PydanticCustomError

from interface_adapters.http.http_response_factory import validation_error_response


class _ConRegla(BaseModel):
    valor: int = 0

    @model_validator(mode="after")
    def _regla(self) -> _ConRegla:
        raise ValueError("Regla X")


class _Opaco:
    """Un objeto que `json` no sabe serializar y con un `str` reconocible."""

    def __str__(self) -> str:
        return "opaco-legible"


class _ConCtxOpaco(BaseModel):
    valor: int = 0

    @field_validator("valor")
    @classmethod
    def _regla(cls, value: int) -> int:
        raise PydanticCustomError("regla_propia", "Regla con contexto {objeto}", {"objeto": _Opaco()})


class _Entero(BaseModel):
    numero: int


class _Muestrario(BaseModel):
    """Un campo por cada `type` de R6."""

    cantidad: float = Field(..., ge=0)
    modo: Literal["a", "b"]
    codigo: str = Field(..., pattern=r"^[A-Z]{2}$")
    hijo: _Entero


def _error_de(modelo: type[BaseModel], datos: Any) -> ValidationError:
    with pytest.raises(ValidationError) as info:
        modelo.model_validate(datos)
    return info.value


def _cuerpo(exc: ValidationError) -> tuple[int, dict[str, Any]]:
    respuesta = validation_error_response(exc)
    return respuesta.status_code, json.loads(respuesta.get_body().decode("utf-8"))


# --- R4: lo no serializable sale como texto, no como 500 ---------------------


def test_f012_r4_el_valueerror_de_una_regla_sale_como_su_mensaje() -> None:
    exc = _error_de(_ConRegla, {})
    estado, cuerpo = _cuerpo(exc)
    assert estado == 400
    [error] = cuerpo["details"]["validation"]
    assert error["type"] == "value_error"
    assert error["loc"] == []
    assert error["ctx"] == {"error": "Regla X"}
    assert error["msg"] == "Value error, Regla X"


def test_f012_r4_un_objeto_opaco_en_ctx_sale_como_su_str() -> None:
    exc = _error_de(_ConCtxOpaco, {"valor": 1})
    estado, cuerpo = _cuerpo(exc)
    assert estado == 400
    [error] = cuerpo["details"]["validation"]
    assert error["type"] == "regla_propia"
    assert error["ctx"] == {"objeto": "opaco-legible"}


def test_f012_r4_un_valor_opaco_fuera_de_ctx_tambien_sale_como_texto() -> None:
    """R4 dice «en ctx o en cualquier otra clave»: aquí es el `input`."""
    exc = _error_de(_Entero, {"numero": _Opaco()})
    estado, cuerpo = _cuerpo(exc)
    assert estado == 400
    [error] = cuerpo["details"]["validation"]
    assert error["input"] == "opaco-legible"
    assert error["loc"] == ["numero"]


# --- R6: lo serializable sale idéntico a la lista de hoy ---------------------


_INVALIDOS = [
    pytest.param({"cantidad": -1, "modo": "a", "codigo": "AB", "hijo": {"numero": 1}}, "greater_than_equal", id="ge"),
    pytest.param({"cantidad": 1, "modo": "z", "codigo": "AB", "hijo": {"numero": 1}}, "literal_error", id="literal"),
    pytest.param({"modo": "a", "codigo": "AB", "hijo": {"numero": 1}}, "missing", id="missing"),
    pytest.param({"cantidad": 1, "modo": "a", "codigo": "abc", "hijo": {"numero": 1}},
                 "string_pattern_mismatch", id="pattern"),
    pytest.param({"cantidad": 1, "modo": "a", "codigo": "AB", "hijo": 7}, "model_type", id="model_type"),
]


@pytest.mark.parametrize(("datos", "tipo"), _INVALIDOS)
def test_f012_r6_lo_serializable_sale_identico_a_la_lista_de_hoy(datos: dict[str, Any], tipo: str) -> None:
    exc = _error_de(_Muestrario, datos)
    de_hoy = json.loads(json.dumps(exc.errors()))
    _, cuerpo = _cuerpo(exc)
    assert cuerpo["details"]["validation"] == de_hoy
    assert [error["type"] for error in de_hoy] == [tipo]


def test_f012_r6_varios_errores_mantienen_su_orden_y_su_ctx() -> None:
    exc = _error_de(_Muestrario, {"cantidad": -1, "modo": "z", "codigo": "abc", "hijo": 7})
    de_hoy = json.loads(json.dumps(exc.errors()))
    _, cuerpo = _cuerpo(exc)
    assert cuerpo["details"]["validation"] == de_hoy
    assert [e["type"] for e in de_hoy] == [
        "greater_than_equal", "literal_error", "string_pattern_mismatch", "model_type",
    ]
    assert de_hoy[0]["ctx"] == {"ge": 0}


def test_f012_r6_el_cuerpo_es_el_400_de_validacion_y_nada_mas() -> None:
    exc = _error_de(_Entero, {})
    estado, cuerpo = _cuerpo(exc)
    assert estado == 400
    assert cuerpo == {
        "ok": False,
        "error": "Solicitud invalida.",
        "details": {"type": "ValidationError", "validation": json.loads(json.dumps(exc.errors()))},
    }
    respuesta = validation_error_response(exc)
    assert respuesta.mimetype == "application/json"


def test_f012_r6_el_cuerpo_es_byte_a_byte_el_de_error_response() -> None:
    """Cuando todo es serializable, el cuerpo es el que daba `error_response` con
    `exc.errors()` tal cual (mismo `ensure_ascii`, mismas claves, mismo orden)."""
    from interface_adapters.http.http_response_factory import error_response

    exc = _error_de(_Muestrario, {"cantidad": -1, "modo": "ñ", "codigo": "abc", "hijo": 7})
    de_hoy = error_response(
        "Solicitud invalida.", status_code=400,
        details={"type": type(exc).__name__, "validation": exc.errors()},
    )
    assert validation_error_response(exc).get_body() == de_hoy.get_body()


# --- R11: el helper no traza ----------------------------------------------------


def test_f012_r11_el_helper_no_emite_trazas(caplog: pytest.LogCaptureFixture) -> None:
    exc = _error_de(_ConRegla, {})
    with caplog.at_level(logging.DEBUG):
        validation_error_response(exc)
    assert caplog.records == []
