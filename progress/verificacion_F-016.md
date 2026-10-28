<!-- progress/verificacion_F-016.md -->
# F-016 · Verificación en producción (T17-T18)

Guion: [`specs/F-016-proforma-a-origen/verificacion_manual.md`](../specs/F-016-proforma-a-origen/verificacion_manual.md).
Sin secretos ni URL: llamadas por la API desplegada con la clave del `.env`, desde un script fuera del repositorio.

## D · Despliegue (2026-10-28, por orden del humano: «despliega f16»)

- **D1.** `SIGRID_PROFORMA_ORIGEN_ENABLED=false` subida por fichero JSON, validado antes con `Settings` (`False False`).
  `appsettings list`: `SIGRID_DOMAIN_WRITE_ENABLED` true, `SIGRID_PROFORMA_WRITE_ENABLED` false,
  `SIGRID_PROFORMA_ORIGEN_ENABLED` false; las otras cuatro `SIGRID_PROFORMA_*` como las dejó F-007.
- **D2.** `func azure functionapp publish` desde `dev` `6735a75`: publicadas todas las rutas, `sigrid/proforma`
  incluida. Antes se quitó el worktree del spec-author de F-018 (`.claude/` no está en `.funcignore`).
- **D3.** Todo con `commit:false`, obra 0404, contrato `CTSU16/0206`, usuario `prueba`:
  - `sigrid/albaran` (extendido, una vinculada): 200 `previsto`, 1,4 s (5,3 s en frío).
  - `sigrid/proforma` sin `modo`, periodo 202610: 400 `proforma_del_mes_existente` por `PROF26/01360` (la de T22 de
    F-007, de mes, aún sin anular): el comportamiento de F-007, sin cambios.
  - `modo: "origen"` sin `proforma_anterior` ni `primera_de_cadena`: 400 `Solicitud invalida.` sin `codigo` (R3).
  - `modo: "origen"` con `primera_de_cadena`: 400 `proforma_del_mes_existente` por la misma `PROF26/01360`: es de mes
    (`docoritip 0`) con otro total, que a origen sigue siendo error (R5).

## Pendiente

- **T17** (V0-V6, previas sobre cadenas reales, con la prueba en lectura de las consultas del contrato v1.2 §2.3):
  las lanza el líder con el visto bueno del humano. Avisar a `proformas` del resultado de §2.3.
- **T18** (grabaciones G1-G3 en la 0404): solo con autorización expresa para cada `commit:true`; en la 0404 antes hay
  que anular `PROF26/01360` desde la UI o usar otro periodo.
