<!-- progress/verificacion_F-012.md -->
# F-012 · Verificación manual

## T9 · Aviso y despliegue (2026-10-19)

- Albaranes avisado antes (líder, 2026-10-18 y 2026-10-19): sin altas en curso, sv9 con `ALTA_SIGRID_COMMIT=false`,
  nada que cambiar; da el visto bueno.
- Humano: push de `dev` (`275637c`, merge de F-012) y `func azure functionapp publish func-sigridapi-dev-huyke
  --python`: paquete subido y las 9 funciones listadas. Sin App Settings nuevas. (El `exit 1` del lanzamiento es del
  `!` al inicio de la segunda línea en bash, que niega el código de salida; el log no trae errores.)

## T10 · Paso 1 (líder, 2026-10-19; pydantic corta antes de conectar: ni lee ni escribe)

Script Python en el scratchpad con la function key del `.env` local (nada al repo): `POST sigrid/albaran`, modo
extendido, una línea vinculada (`ctrpro_ide`) **sin** `cod_contrato`, `commit: false`.

| Esperado | Obtenido |
|---|---|
| 400 `ValidationError` con `ctx.error` en texto (antes: 500) | **400**, `details.type` `ValidationError`, `validation[0]`: `loc []`, `type value_error`, `msg` «Value error, Una linea vinculada exige 'cod_contrato'.», `ctx` `{"error": "Una linea vinculada exige 'cod_contrato'."}` |

Paso 2 (opcional, endpoints de escritura) no ejecutado: el humano no lo pidió. Resultado: **OK**. Notas «PENDIENTE DE
DESPLIEGUE» de F-012 retiradas de `azure-apps/sigrid_api.md`.
