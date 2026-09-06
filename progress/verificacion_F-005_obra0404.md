<!-- progress/verificacion_F-005_obra0404.md -->
# F-005 · Verificación manual en la obra 0404 (2026-09-06)

Criterio 8 de F-005. Desplegado `dev` = `0d8b206` en `func-sigridapi-dev-huyke`
(8 rutas). App Settings ampliadas por fichero JSON y releídas:
`SIGRID_DOCUMENT_ALLOWED_CONTIP=[708,44,14]`,
`SIGRID_DOCUMENT_ALLOWED_GRATIPIDE=[35,0]`; el resto sin cambios
(`WRITE_ENABLED=true`, `WRITE_DATABASE=ruesma_rep`, `ALLOWED_WRITE_DATABASES`
`["ruesma"]`). Scripts `f005_m2_dry_run.py` y `f005_m3_commit.py` del
scratchpad (no se versionan). Obra 0404 «CUBIERTA NAVE 14 - JOHN DEERE».

## M2 — dry-run (todo lectura; `MAX(ide)` idénticos antes y después)

| Concepto | Respuesta | Negocio | Documental | Enlace |
|---|---|---|---|---|
| Contrato `CTSB20/0519` (1686634, tip 44) | 200, `dry_run`, 0 filas | `gratipide 0`, `res` PRUEBA API - BORRAR, `vin 3`, `ima` NULL | `gratipide 0`, `res ''`, `vin 3`, 303 B | `pos 192` (tenía 64 y 128), `cla 0` |
| Albarán `AC26/15951` (2774375, tip 14) | 200, `dry_run`, 0 filas | ídem | ídem | `pos 64` (no tenía) |

Sin aviso de `tipaso`. Negativos: clase 40 (existe en `auxgra`, no en la
lista) → `clase_de_grafico_no_permitida`; clase 99 → ídem; clase 35 en un
contrato → aceptada (solo la lista manda); contrato declarado tip 14 →
`tipo_de_concepto_no_coincide`.

## M3 — `commit:true` sobre el albarán `AC26/15951` (autorización expresa del humano)

`usu=prueba`, `gratipide=0`, PDF de 303 bytes, `sha256` `9bd10a9b…3571b144`.

Respuesta **200**: `committed:true`, `filas_afectadas:3`, documental
**359574**, negocio **298419**, `cod` **`202609061309288219.prueba`**,
enlace `{ide 298859, con 2774375, gra 298419, pos 64, cla 0}`. Los `ide`
coinciden con los provisionales del dry-run.

| Comprobación | Resultado |
|---|---|
| `documents/read` por `cod` | 303 bytes, `sha256` **idéntico** |
| negocio `WHERE cod = ?` | 298419: `res` PRUEBA API - BORRAR, `gratipide` **0**, `vin` 3, `ima` NULL, usu prueba |
| documental `WHERE cod = ?` | 359574: `res` `''`, `gratipide` **0**, `vin` 3, `DATALENGTH` 303 |
| enlace | 1 fila, `gra` = ide de negocio, `pos` 64 |
| huérfanos de la prueba | ninguna fila |
| repetición de la misma llamada | `idempotente:true`, `committed:false`, `filas_afectadas:0`; enlaces con ese `cod`: **1** |

**Criterios de F-005 cumplidos en producción**: el documento queda como los que
Sigrid crea para albaranes (sin clase). Pendiente del humano: abrirlo desde la
ficha del albarán `AC26/15951` en Sigrid (obra 0404, proveedor GARSAN) y
decidir si se borra desde la UI.

Corrección al guion de `current.md`: el ide 2774375 es `AC26/15951`
(ALB-PRUEBA-001); `AC26/15950` es el 2774374.
