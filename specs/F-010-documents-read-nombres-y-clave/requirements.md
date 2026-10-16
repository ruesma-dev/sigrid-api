<!-- specs/F-010-documents-read-nombres-y-clave/requirements.md -->
# F-010 · Requisitos

**`POST /api/documents/read`: nombres de fichero no ASCII sin 500 y localización de la fila
sin ambigüedad.** Origen: datamart-seg-anual F-139 y mcp-bbdd F-023 (2026-10-16). Rigor
`critico`. Diseño en [`design.md`](design.md); decisiones abiertas en `progress/spec_F-010.md`.

Hechos de partida (medidos por el líder el 2026-10-16, no se repiten aquí): `ruesma_rep.dbo.gra`
ide 365617 con `filename_columns ["nomori"]` → 500 con cuerpo vacío (lo rechaza el host de
Functions por la cabecera no ASCII); con `["cod"]` → 200. En `gra` solo son únicos `ide` (PK) y
`(emp, cod)`; `cod` solo no tiene restricción.

## A. La cabecera `X-Document-Filename`

Notación: `nombre` es el `file_name` que el caso de uso entrega a `binary_file_response`;
`cabecera` es el valor de `X-Document-Filename`; «ASCII imprimible» es 0x20-0x7E.

**R1.** El sistema debe emitir `cabecera` compuesta solo por caracteres ASCII imprimibles, para
cualquier `nombre` (casos obligatorios en test: ñ, á, emoji, ideograma CJK, `%`, el control
0x1F y DEL 0x7F).

**R2.** El sistema debe codificar `cabecera` de forma que
`urllib.parse.unquote(cabecera, encoding="utf-8", errors="strict") == nombre` para todo
`nombre`; en particular un `%` literal del nombre viaja como `%25` (`"a%20b.pdf"` no puede
decodificarse como `"a b.pdf"`).

**R3.** DONDE `nombre` sea solo ASCII imprimible y no contenga `%`, el sistema debe emitir
`cabecera == nombre`, byte a byte (compatibilidad con los consumidores que la leen tal cual,
p. ej. `albaranes-persistencia`). Ejemplos obligatorios en test: `"Contrato 2024 (v2).pdf"`,
`'Oferta [final]; "x".pdf'`.

**R4.** El sistema debe emitir `Content-Disposition` como
`<disposition>; filename*=UTF-8''<quote(nombre, safe="")>`. Para todo `nombre` sin `/` el valor
es idéntico byte a byte al actual (`quote(nombre)`); un `/` viaja como `%2F` (RFC 5987 no lo
admite sin codificar). `X-Document-Size` y el cuerpo no cambian.

**R5.** CUANDO `documents/read` sirva un documento cuyo nombre resuelto sea
`"Factura año señal.pdf"`, el sistema debe responder 200 con el binario, `cabecera`
`"Factura a%C3%B1o se%C3%B1al.pdf"` y `Content-Disposition`
`attachment; filename*=UTF-8''Factura%20a%C3%B1o%20se%C3%B1al.pdf` (test de ruta con el caso de
uso doblado).

## B. Localización de la fila

**R6.** El sistema debe aceptar en `DocumentReadRequest` un campo opcional `key`: objeto JSON
de **1 a 4** entradas `nombre_de_columna → valor`, con valor entero JSON o texto JSON (ni
`null`, ni booleano, ni decimal, ni lista, ni objeto). Los nombres se recortan (`strip`).

**R7.** SI la petición trae `key` y también `id_column` o `id_value`, ENTONCES el sistema debe
responder 400 `Solicitud invalida.` (`details.type = "ValidationError"`) sin consultar la base.

**R8.** SI la petición no trae ni `key` ni `id_column`, o trae `id_column` sin `id_value`, o
`id_value` sin `id_column`, ENTONCES el sistema debe responder 400 `Solicitud invalida.`
(`ValidationError`) sin consultar la base. `id_value: null` con `id_column` presente se sigue
aceptando, como hoy.

**R9.** SI `key` es un objeto vacío, tiene más de 4 entradas, un nombre vacío tras recortar,
dos nombres iguales sin distinguir mayúsculas (`"emp"` y `" EMP"`), o un valor de tipo no
admitido (R6), ENTONCES el sistema debe responder 400 `Solicitud invalida.` (`ValidationError`).
Frontera obligatoria en test: 4 entradas pasan, 5 no.

**R10.** El sistema debe validar **cada** nombre de `key` con
`IdentifierGuard.validate_identifier(nombre, field_name="key")` antes de componer el SQL; SI
alguno no es válido, ENTONCES debe responder 400 con `details.type = "IdentifierValidationError"`
sin abrir conexión. `infrastructure/security/` no se modifica.

**R11.** El sistema debe leer el documento con
`SELECT TOP (2) [f1], …, CAST([<blob>] AS varbinary(max)) AS file_content FROM [<schema>].[<table>]
WHERE [c1] = ? AND [c2] = ? …`, con una condición por columna en el orden de `key`, unidas por
`AND`, y los valores pasados como parámetros en ese mismo orden. Ningún valor aparece en el
texto del SQL.

**R12.** CUANDO la petición localice con `id_column`/`id_value`, el sistema debe comportarse
como con `key = {id_column: id_value}`: una sola condición `[id_column] = ?` con `id_value` como
parámetro, y la misma respuesta (cuerpo, cabeceras, códigos y textos de error) que hoy salvo lo
que cambian R1-R4 y R13. Los dos consumidores actuales (`id_column` `ide` en albaranes, `cod` en
mcp-bbdd) no tienen que cambiar su petición.

**R13.** SI la condición de localización casa con **más de una fila**, ENTONCES el sistema debe
responder **409** `{ok:false, error, details:{type:"DocumentoAmbiguoError"}}` sin servir ningún
binario, con `error` =
`La localizacion casa con mas de una fila en [<schema>].[<table>] (<condicion>): no se sirve ninguna. Usa una clave unica (en dbo.gra: key con emp y cod, o id_column ide).`
Aplica a **toda** petición, venga por `key` o por `id_column`. `details.type` nunca es
`"ValueError"` (mcp-bbdd lee ese tipo como «no hay binario»).

**R14.** SI no casa ninguna fila, ENTONCES el sistema debe responder 400 (`ValueError`) con
`No existe ninguna fila en [<schema>].[<table>] con <condicion>.`; SI casa una y su BLOB es
`NULL`, ENTONCES 400 (`ValueError`) con `La columna <blob> esta vacia para <condicion>.`
`<condicion>` es `c1=v1 AND c2=v2…` en el orden de `key`; con una sola columna queda
`ide=365617`, idéntico al texto de hoy.

**R15.** CUANDO ninguna columna de nombre traiga valor, el sistema debe usar como nombre de
reserva `document_<v1>_<v2>…` (valores de la localización en orden, unidos por `_`), que con
una sola columna es el `document_<id_value>` de hoy; se sanea y se le añade extensión como hoy.

## C. Documentación y verificación

**R16.** El sistema debe quedar documentado en `azure-apps/sigrid_api.md`: §8.3 con `key`
(1-4 columnas, exclusiva con `id_column`/`id_value`), el 409 de ambigüedad, la codificación de
`X-Document-Filename` y cómo decodificarla (`unquote`), y que `Content-Disposition` `filename*`
es la fuente canónica del nombre; §10 con los consumidores de `documents/read`. Verificación:
revisión del reviewer, commit aparte en `azure-apps`.

**R17.** Toda la suite existente debe seguir en verde sin modificar sus aserciones (en
particular `test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho` con `documents_read`).

**R18.** MANUAL (humano), solo lectura, post-despliegue: ide 365617 con `["nomori"]` → 200 y
`unquote(cabecera)` igual al `nomori` leído por `sql/read`; la misma fila por `key` `{emp, cod}`
→ mismo `X-Document-Size` y mismo SHA-256; `id_column emp`, `id_value 1` → 409; y un documento
de nombre ASCII con espacios devuelve las mismas cabeceras que antes del despliegue. Comandos
exactos en `design.md` §Verificación manual.

## Fuera de alcance (con aviso)

- **`sigrid-api-v2`** (`interface_adapters/http/responses.py:62`) tiene el mismo fallo de
  cabecera: no se toca aquí; se avisa en `progress/spec_F-010.md`.
- **Validar `database` de `documents/read` contra `ALLOWED_DATABASES`**: hallazgo de esta spec
  (hoy no se valida); decisión abierta para el humano, no se implementa aquí.
- `scripts/invoke_api_examples.py` (guarda el fichero con el nombre de la cabecera sin
  decodificar): no se toca; un nombre no ASCII se guardaría con `%XX`, cosmético.
- Consumidores (albaranes, mcp-bbdd, datamart): ningún cambio obligatorio; recomendaciones en el
  informe.
