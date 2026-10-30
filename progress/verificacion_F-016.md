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

## T17 V1 y T18 · G1-G3 (líder, 2026-10-30; autorización expresa del humano para T17 y T18)

Obra 0404, `CTSU16/0206`, `ctrpro` 258782 (`pre` 30) y 258783 (`pre` 45), periodo 202609, `otra_del_mes`, usuario `prueba`.
`PROF26/01360` no estorba: es de 202610. `canser` de partida: 2 y 1.

- **V1**, llaves cerradas, `commit:true` del cuerpo de G2 (no la hoja de una punta): 400
  `escritura_proformas_deshabilitada`, 0 filas.
- **Previa**: `previsto`, `docoriide` 0, 75,00.
- **G1**, solo la llave de F-007 abierta: 400 `escritura_proformas_origen_deshabilitada`, 0 filas (R4).
- **G2**, las dos abiertas: `creado`, **`PROF26/01386`** (`con_ide` 2864685), fecha 20260930, `cla` 141, `docoritip` 1,
  `docoriide` 0, `totbas` 75; dos líneas con `can` 1, `canoriori` 1, `canorilin` 0; `canser` 3 y 2. Repetición:
  `idempotente`, mismo `con_ide`, `cadena` nula.
- **G3**: previa `previsto`, 1 arrastrada, origen 135. `creado`, **`PROF26/01387`** (`con_ide` 2864687), `docoriide`
  2864685, `totbas` 60; continuada `can` 2, `tot` 60, `canorilin` 1383572, `canoriori` 3; arrastrada 258783 detrás, `can`
  y `tot` 0, `canorilin` 1383573, `canoriori` 1; 1 `ctrprodes` y 1 `mov`; `canser` 5 y 2. Repetición: `idempotente`.
- **Llaves**: las dos en `false` al acabar, comprobado con `appsettings list`.

**Sin desviaciones; no saltó la regla de parada.** El `canser` de la 258782 queda en 5 de 5 hasta anular.

## Pendiente

- **V9 en la UI** (ficha, impresión con ORIGEN/ANTERIOR, paso a factura sin grabarla) y anular desde la UI en orden
  inverso: primero `PROF26/01387`, después `PROF26/01386` (nunca `DELETE`). Lectura final: 0, 0 y `canser` 2 y 1.
- **`PROF26/01360`**: el humano dijo el 2026-10-30 que no hace falta anularla para T18.
