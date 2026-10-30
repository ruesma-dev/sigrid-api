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

## T17 · V2-V6 (líder, 2026-10-30; solo lecturas y `commit:false`, usuario `prueba`)

Con `dev` `c2b6107` desplegado (F-018 incluida). Guion traducido a Python desde el scratchpad, mismas consultas.

| Paso | Cadena 1: punta `AC26/31258` (3 líneas) | Cadena 2: punta `PROF26/01378` (18 líneas) |
|---|---|---|
| V2 consultas §2.3 | 1 punta; `importe_cadena` 5.060,60 = Σ de líneas = anterior 2.846,80 + `totbas` 2.213,80; 4,0 y 4,6 s | 1 punta; 96.295,09 = Σ de líneas = anterior 92.795,09 + `totbas` 3.500; 0,2 s |
| V3 hoja de la punta | `existente`, sin `cadena`, 0 filas | igual |
| V4 siguiente | `previsto`; `docoritip` 1 y `docoriide` de la punta; origen 5.060,60 + 46,83 = 5.107,43; 1 arrastrada, como se esperaba; continuadas con `canorilin` y `canoriori` + 1; arrastrada a 0; 0 filas | `previsto`; 96.295,09 + 28.163 = 124.458,09; 16 arrastradas, como se esperaba |
| V4b línea como nueva | `linea_nueva_ya_en_la_anterior` y 2 arrastradas | igual, 17 arrastradas |
| V5 sin `modo` | `existente`, sin clave `cadena`, `contrato_a_origen` | igual |
| V6 errores | `anterior_con_sucesora`, `anterior_no_valida` y `linea_anterior_no_valida` | igual |

La punta de la cadena 1 es de serie `AC` (`cla` 0): el contrato §2.3 ya dice que la cadena mezcla series; 71 de 925
encadenadas de 2026 son `AC`. No se repitió V2 de F-007 sobre la 0719. **Sin discrepancias.**

## Pendiente

- **V1 de T17**: lleva un `commit:true` que debe dar 400 con la llave cerrada; no se ha lanzado. Queda con T18.
- **T18** (grabaciones G1-G3 en la 0404): solo con autorización expresa para cada `commit:true`; en la 0404 antes hay
  que anular `PROF26/01360` desde la UI o usar otro periodo.
