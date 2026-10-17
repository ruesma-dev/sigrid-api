<!-- progress/verificacion_F-010.md -->
# F-010 · Verificación manual (T13-T15)

Hecha por el líder con lecturas contra la API desplegada (`sql/read` y `documents/read`), con
los guiones de design §Verificación manual traducidos a Python (`urllib`, `.env` local; fuera del
repo). Sin nombres ni `cod`: solo coincide / no coincide.

| Tarea | Fecha | Resultado |
|---|---|---|
| T13 (pasos 0 y 4a, antes del despliegue) | 2026-10-17 | `gra` ide 365660 (`nomori` ASCII con espacios, sin `%`): 200, 40.795 bytes; cabeceras guardadas fuera del repo |
| T14 (despliegue) | 2026-10-18 | `func azure functionapp publish func-sigridapi-dev-huyke --python` lanzado por el humano desde `dev` `fc2079a`; exit 0, las 9 funciones listadas; sin App Settings nuevas |
| T15 paso 0 | 2026-10-18 | `sql/read` de `emp, cod, nomori` del ide 365617: 200 |
| T15 paso 1 | 2026-10-18 | ide 365617 con `["nomori"]`: **200** (antes 500 con cuerpo vacío); `X-Document-Filename` solo ASCII y `unquote` = `nomori`; `filename*` de `Content-Disposition` decodifica a `nomori`; 17.865 bytes |
| T15 paso 2 | 2026-10-18 | misma fila por `key {emp, cod}`: 200, `X-Document-Size` 17.865, SHA-256 idéntico al del paso 1 |
| T15 paso 3 | 2026-10-18 | `id_column emp`, `id_value 1`: **409**, `details.type` `DocumentoAmbiguoError`, texto de R14 |
| T15 paso 4b | 2026-10-18 | ide 365660: 200; `X-Document-Filename`, `Content-Disposition` y tamaño idénticos a los de T13 |

Avisos: albaranes antes del despliegue (2026-10-17); mcp-bbdd y datamart, tras el despliegue.
`azure-apps/sigrid_api.md` §8.3: nota «PENDIENTE DE DESPLIEGUE» sustituida (`bdc8ec0`, sin push).
