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

## T14 · Pasos 1-5 (tras el despliegue)

Pendiente.
