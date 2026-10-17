<!-- progress/spec_F-010.md -->
# Spec F-010 · `documents/read`: nombres no ASCII sin 500 y localización sin ambigüedad — v1

Spec-author, 2026-10-16. Rama `feature/F-010-documents-read-nombres-y-clave` (desde `dev`,
`838a94a`). Estado `pending` (el líder la pasa a `spec_ready`), `sdd`, rigor `critico`.
Spec en `specs/F-010-documents-read-nombres-y-clave/` (requirements 122 líneas, design ~248,
tasks 16 tareas). **No se ha llamado a la API, ni a Azure, ni al SQL Server**: se usan las
mediciones del líder del 2026-10-16 y la lectura del código de los consumidores.

## Qué propone, en corto

1. **Cabecera** (R1-R5): `X-Document-Filename` con codificación porcentual UTF-8 de todo lo que
   no sea ASCII imprimible y del `%`. Un nombre ASCII sin `%` viaja idéntico; todo nombre se
   decodifica con `unquote`. `Content-Disposition` pasa a `quote(nombre, safe="")`, idéntico
   al de hoy para todo nombre que llega a la ruta (el caso de uso ya cambia `/` por `_`).
2. **Localización** (R6-R15): campo opcional `key` (1-4 columnas, valores entero o texto,
   AND, nombres por `IdentifierGuard`, valores con `?`), excluyente con `id_column`/`id_value`,
   que se traducen a `key` de una columna en el modelo (un solo camino en el adaptador).
   `SELECT TOP (2)` para toda petición: dos filas → **409** `DocumentoAmbiguoError`.
   Textos de «no hay fila» y «BLOB vacío» idénticos a los de hoy con una columna.
3. **Documentación** (R16): `azure-apps/sigrid_api.md` §8.3 y §10, commit aparte (T12).
4. **Manual** (R18, T13-T15): captura previa de cabeceras ASCII, despliegue, y post-despliegue
   ide 365617 con `nomori`, la misma fila por `key {emp, cod}` (mismo hash), `emp = 1` → 409.

## Consumidores revisados (búsqueda acotada a albaranes, mcp-bbdd, datamart, partes, v2)

| Consumidor | Cómo llama | Lee `X-Document-Filename` | Efecto de F-010 |
|---|---|---|---|
| albaranes-persistencia (`sigrid_api_contrato_client.py:709` y 5 scripts de diagnóstico) | `id_column ide`, `["nomori","nom"]` | Sí, tal cual | Nombres ASCII sin `%`: igual. No ASCII: hoy 500, después 200 con `%XX` (le conviene añadir `unquote`, retrocompatible) |
| mcp-bbdd F-023 (`cliente_documentos.py`) | `id_column cod`, `["cod"]` | No (usa `Content-Type`, `X-Document-Size`) | Ninguno. Un `cod` repetido entre empresas daría 409 → «origen no disponible» en vez de un documento ajeno. **400 + `details.type == "ValueError"` = «sin binario» para ellos: la spec lo preserva y el 409 nunca lleva ese tipo** |
| datamart F-139 | No llama (solo el índice) | — | Ninguno |
| `sigrid-api-v2` | — | Sí (`scripts/invoke_api_examples.py`) | Mismo fallo en `responses.py:62`: **fuera de alcance, aviso** |
| partes | No usa `documents/read` | — | — |

## Hallazgos fuera de alcance

- **`documents/read` no valida `database`** contra `ALLOWED_DATABASES` (ni el modelo, ni el
  caso de uso, ni la ruta) y `_connect` la interpola sin escapar en la cadena de conexión
  (`DATABASE={database};`). `sql/read` sí la valida (`SqlQueryGuard`). Ver D6.
- `filename_columns: []` compone un `SELECT` con coma suelta → 500. Menor; nadie lo usa.
- `scripts/invoke_api_examples.py` guarda el fichero con el nombre de la cabecera sin
  decodificar. No se toca: `scripts/` cuenta para cobertura y mutación y el efecto es cosmético.
- En la raíz del repo hay un fichero sin seguimiento llamado `` `0`].{t `` (basura de algún
  comando). No lo he tocado ni incluido en el commit.

## Decisiones que necesitan al humano

- **D1 — Codificación de `X-Document-Filename`** (design §A). Propuesta: mínima (no ASCII,
  controles y `%`). Coste: un nombre ASCII con `%` cambia (`100%25 real.pdf`). Alternativas
  descartadas: quitar la cabecera (rompe albaranes) o `quote` completo (cambia los nombres
  ASCII con espacios, el 94,3 % que hoy funciona).
- **D2 — `safe=""` en `Content-Disposition`.** Sin efecto observable en la ruta; hace correcta
  la función por sí misma (RFC 5987). Si se prefiere no tocar ni un carácter, se quita y R4
  queda en «igual que hoy».
- **D3 — 409 para la ambigüedad** (alternativa: 400 con `details.type` propio). Para mcp-bbdd
  es igual; para albaranes, 409 se distingue por código.
- **D4 — Tope de 4 columnas en `key`**, constante de código, no App Setting.
- **D5 — Ambigüedad para toda petición**, también por `id_column` (lo pide el `acceptance`). Hoy
  no rompe a nadie: `ide` es PK y `cod` es hoy único de hecho (365.617 = 365.617).
- **D6 — El hallazgo de `database`**: recomiendo **feature aparte** (F-011, rigor `critico`):
  validar contra `ALLOWED_DATABASES` en `documents/read` con 400, como `sql/read`. Cambia la
  superficie de seguridad y merece su propia revisión; meterlo aquí sería ampliar F-010 sin
  enseñarlo. Si el humano prefiere incluirlo, es un R más y dos tareas.
- **D7 — Contrato de la petición**: `key` excluyente con `id_column`/`id_value` (las dos → 400;
  ninguna → 400); `id_value: null` con `id_column` se sigue aceptando como hoy; `extra` sigue
  en `ignore`.

## Avisos para que el líder los traslade (no son tareas de este repo)

- **sigrid-api-v2**: mismo fallo de cabecera (`interface_adapters/http/responses.py:62`).
- **albaranes**: tras el despliegue, `X-Document-Filename` puede llevar `%XX`; decodificar con
  `unquote` (o leer `filename*` de `Content-Disposition`). Avisar antes de desplegar, por la
  regla de su sesión (`albaranes [dd1842]`).
- **mcp-bbdd F-023 / datamart F-139**: tras el despliegue pueden volver a
  `filename_columns ["nomori"]` si les sirve, y conviene migrar de `id_column cod` a
  `key {emp, cod}` (el índice único real de `gra`); el 409 llega como «origen no disponible».

## Verificación

`python -m harness.tamano --feature F-010`: dentro de topes (122/150, 248/250).
`bash harness/init.sh` (2026-10-16): ENTORNO LISTO, 2370 passed y 1 skipped; cobertura N/A
(sin código de producción todavía).
