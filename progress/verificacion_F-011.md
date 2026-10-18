<!-- progress/verificacion_F-011.md -->
# F-011 · Verificación manual

## T12 · Paso 0 (líder, solo lectura, 2026-10-18, antes del despliegue)

`az functionapp config appsettings list -n func-sigridapi-dev-huyke -g rg-sigrid-dev-data-api` filtrado a las tres
claves (sin secretos), y comprobación de cada elemento contra `^[A-Za-z_][A-Za-z0-9_]*$`:

| App Setting | Valor | Casa con el patrón |
|---|---|---|
| `ALLOWED_DATABASES` | `["master", "ruesma_rep", "ruesma"]` | sí, los tres |
| `ALLOWED_WRITE_DATABASES` | `["ruesma"]` | sí |
| `SIGRID_DOCUMENT_WRITE_DATABASE` | `ruesma_rep` | sí |

`ruesma_rep` está literal en `ALLOWED_DATABASES`. Con A1 ningún endpoint pierde la conexión. Resultado: **OK**.

## T13 · Despliegue (humano, 2026-10-18)

`func azure functionapp publish func-sigridapi-dev-huyke --python` desde `dev` `93710c4` (merge de F-011), exit 0,
las 9 funciones listadas. Sin App Settings nuevas. Antes, postventa-incidencias confirmó que su primera escritura de
F-059 esperaría a T14 (se le avisó al terminar).

## T14 · Pasos 1-5 (líder, 2026-10-18; lecturas y el dry-run autorizado)

Script Python en el scratchpad con la function key del `.env` local (nada al repo; no imprime nombres de fichero):

| Paso | Petición | Resultado | Esperado |
|---|---|---|---|
| 1 | `documents/read`, `ruesma_rep`, `gra` ide 365617 | 200, `X-Document-Size` 17865, 17865 bytes | igual |
| 2 | `database: "base_inexistente_f011"` | 400 `BaseNoPermitidaError`: «La base de datos 'base_inexistente_f011' no está permitida. Permitidas: master, ruesma_rep, ruesma» | igual |
| 3 | `"ruesma_rep;APP=f011"` y `"RUESMA_REP"` | 400 `BaseNoPermitidaError` las dos, mismo texto | igual |
| 4 | `sql/read` sobre `ruesma_rep` (`gra` ide 365617) y `ruesma` (`con`, `tip = 44`) | 200 y una fila cada una | igual |
| 5 | dry-run `sigrid/contrato-lineas`, `database: "ruesma;APP=f011"`, `commit: false` | 400 `IdentifierValidationError`: «El identificador 'database' contiene caracteres no permitidos: ruesma;APP=f011» | igual: no llegó a conectar |

Resultado: **OK**. Notas «PENDIENTE DE DESPLIEGUE» retiradas de `azure-apps/sigrid_api.md` (`0a0a25f`).
