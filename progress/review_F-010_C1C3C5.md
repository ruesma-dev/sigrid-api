# Revisión F-010 · bloques C1, C2, C3, C3 bis y C5 (más corrección del código frente a la spec)

Revisión completa (pasada 1), `git diff dev..HEAD` con HEAD `c3d4e45`, y `azure-apps` `0c4cbeb`.
Reviewer, 2026-10-17. Rigor declarado: **`critico`**. C4 y C4 bis (RED, cobertura, mutación,
RM1-RM6) **quedan fuera** de este trozo. No se ha ejecutado `init.sh` ni la suite completa
(prohibido por el encargo).

## Veredicto del bloque: **RECHAZADO** (2 hallazgos, los dos de arreglo corto)

El código es correcto y seguro frente a la spec en lo que se pidió mirar con prioridad
(inyección, exclusión, textos, 409, cabecera). Rechazan: un texto de error de R12 que cambia sin
declararse (H1) y `progress/current.md` desactualizado (H2).

## Cambios requeridos

1. **H1 · R12, texto del error de identificador por `id_column`.**
   `infrastructure/repositories/sql_server_repository.py:36` valida los nombres de la
   localización con `field_name="key"`, y `domain/models/sql_models.py:268` convierte
   `id_column` en `key`. Medido: `{"id_column": "ide;x", "id_value": 1, …}` →
   `El identificador 'key' contiene caracteres no permitidos: ide;x`; en `dev` decía
   `'id_column'` (`dev:…sql_server_repository.py` l. 333). R12 exige la misma respuesta
   «(cuerpo, cabeceras, códigos y **textos de error**)» salvo R1-R4 y R13, y el cliente lee el
   nombre de un campo que no mandó. Ni `design.md` ni `impl_F-010.md` lo declaran. A elegir:
   (a) que el camino `id_column` informe `field_name="id_column"` (parámetro del nombre de campo
   en `build_document_query`, o que lo pase el caso de uso) con un test
   `test_f010_r12_id_column_no_valido_conserva_su_texto`; o (b) llevarlo al humano y, si lo
   acepta, enmendar R12 por escrito y anotarlo en `impl_F-010.md` y en §8.3. Código y tipo
   (400 `IdentifierValidationError`) no cambian y los consumidores mandan constantes válidas
   (`ide`, `cod`): impacto real nulo, pero en `critico` no se aprueba una desviación no declarada.
2. **H2 · C2, `progress/current.md` no describe solo la sesión activa y tiene partes falsas hoy.**
   l. 30-41 «F-010 · spec escrita, pendiente de aprobación» con D1-D7 «abiertas» (superado: l. 14);
   l. 163-178 «Lo siguiente en el backlog» y «Prompt para retomar» **no nombran F-010** y mandan a
   F-007/F-008: una sesión nueva ignoraría una feature `in_progress` con T13 y el aviso a
   albaranes pendientes; l. 43-118, bloques de F-009 y F-006 cerradas con guiones ya ejecutados.
   Requerido: dejar F-010 (estado, T13-T15, aviso a albaranes) y reescribir «Lo siguiente» y el
   prompt para F-010. Lo heredado que siga pendiente del humano (T24 de F-009, rotar
   `local.settings.json`, menores) puede quedar como lista corta o ir a `history.md`. Mismo
   criterio que `review_F-006_estado.md`.

## C1 — El arnés está completo y en verde

- **N/A** `bash harness/init.sh` exit 0: **no ejecutado por orden expresa del encargo** (hay
  revisiones y una campaña en paralelo). El implementer declara ENTORNO LISTO (2527 passed); este
  trozo no lo certifica: lo comprueba quien cierre la feature.
- [x] Existen los siete ficheros base (`CLAUDE.md`, `features.json`, `SPECS.md`, `current.md`,
  `history.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`), comprobado con `ls`.

## C2 — El estado es coherente

- [x] Una sola `in_progress` (F-010) · [x] rama `feature/F-010-documents-read-nombres-y-clave` ·
  [ ] `current.md` solo la sesión activa: **H2** · [x] toda `done` (F-002..F-006, F-009) tiene su
  sección en `history.md`.

## C3 — Arquitectura y convenciones

- [x] Hexagonal: `DocumentoAmbiguoError` en `domain/models`, lanzada por el adaptador y traducida
  a 409 en `function_app.py`; dominio sin imports de infraestructura (lo único nuevo es
  `StrictInt`/`StrictStr` de pydantic); SQL en el adaptador; cabecera en `interface_adapters`.
  Ficheros tocados = los de `design.md`.
- [x] Primera línea con la ruta en los 12 `.py` del diff (7 modificados, 5 tests nuevos).
- [x] Sin `print`, TODOs ni secretos (en tests, `no-es-una-clave`/`tampoco`, ajustes falsos); sin
  dependencias nuevas; `infrastructure/security`, `config` y `scripts` sin cambios.
- Sigrid: [x] base correcta (solo lectura de `ruesma_rep` por `documents/read`) · N/A `con`/
  extensión (no hay SQL de negocio: tabla y columnas las manda el cliente) · N/A recálculos y
  estados (no escribe ni lee estados) · [x] SQL parametrizado (abajo) · N/A agregación (una fila).

## Corrección del código frente a la spec (prioridad del encargo)

Sondeo propio sin red ni BBDD (script en el scratchpad) y `pytest` de los cinco
`tests/test_f010_*.py`: **157 passed**; `-k "f009_t13_las_demas_rutas or f004_route or
document"`: **98 passed** (incluye el test de la tupla de ocho, R17).

- **Identificadores** [x] R10: `build_document_query` valida schema, table, **cada** nombre de
  `key`, blob y filename con `IdentifierGuard` (`fullmatch` de `^[A-Za-z_][A-Za-z0-9_]*$`, sin
  `\w` Unicode) **antes** de credenciales y conexión. 12 nombres hostiles (`emp] = 1 OR 1=1 --`,
  `[emp]`, `emp'`, `e mp`, `emp\x00`, `año`, ancho completo…): todos rechazados. `"emp\n"` pasa
  porque el guardia recorta (queda `[emp]`, inocuo, como hoy).
- **Valores y nº de columnas** [x] R11: `?` y parámetros salen de la **misma** lista de pares, así
  que nº de `?` = nº de parámetros siempre; `1' OR '1'='1` viaja como parámetro y no aparece en
  el SQL. El tope 1-4 está en el modelo; por la ruta no llega `key` vacía al adaptador.
- **Exclusión y ausencia** [x] R7-R9: 17 casos (key+id_column, key+`id_value:null`, nada, uno solo
  de los dos, bool/decimal/lista/objeto, `key` no objeto, 5 entradas, duplicado por `casefold`
  incluido `STRASSE`/`straße`, `id_column` en blanco): todos 400 `ValidationError`, y
  `exc.errors()` serializa por `error_response` en todos. `id_value:null` aceptado; orden y
  recorte de `key` conservados.
- **Textos R13/R14** [x]: idénticos a la spec; con una columna `ide=365617` como en `dev`. Orden:
  0 filas → 400; >1 → 409 aunque los BLOB sean NULL; 1 con NULL → 400. Discrepancia única: **H1**.
- **409** [x] R13: primer `except`, `details.type` literal `"DocumentoAmbiguoError"`. En mcp-bbdd
  (`cliente_documentos.py`) 409 no es reintentable (`{502, 503, 504}`) ni `SinBinario` (exige 400
  + `"ValueError"`): «origen no disponible», como pide D3. El 400 `ValueError` de la ruta solo lo
  dan los dos `ValueError` del adaptador (un JSON inválido sale como `JSONDecodeError`).
- **Cabecera** [x] R1-R5: 20.000 nombres aleatorios de los cinco planos Unicode: siempre
  0x20-0x7E, `unquote(…, errors="strict")` da el original, ASCII sin `%` idéntico; CR/LF salen
  `%0D%0A` (sin inyección de cabecera). `Content-Disposition` con `safe=""`.

**Desviaciones declaradas, valoradas.** (1) `PydanticCustomError`: correcta y necesaria (un
`ValueError` en `ctx` no serializa: 500), patrón ya existente y con test. Aceptada. (2) Pares sin
`zip`: misma semántica y garantiza la paridad `?`/parámetros. Aceptada. (3) `source` con
`.strip()` en `read_document` (l. 379): hoy equivale a lo validado, pero acopla el texto al
detalle del guardia; mejor que `build_document_query` devolviera el origen. Observación, no
bloquea. (4) SQL en una línea: es el texto de R11. Aceptada. (5) `null` como «no enviado» en
`key`/`id_column` (no en `id_value`): coherente con el diseño y con R8; la asimetría
(`{key, id_column:null}` pasa, `{key, id_value:null}` es 400) es defendible porque
`id_value:null` es valor legítimo; de paso `database:null` ya no se vuelve `"None"`. Aceptada.

## `azure-apps` `0c4cbeb` (R16)

Fiel al código, punto por punto: `key` (1-4, entero o texto, AND, recorte, duplicados,
excluyente), `id_value:null`, defecto `["nomori","nom"]` y reserva `document_<v1>_<v2>`,
`Content-Type` por firma, regla de `X-Document-Filename` con `unquote`/`UnescapeDataString`,
`filename*` canónica, tabla de errores (400 ×3, 409, 500 con `filename_columns: []`), regex del
guardia, `TOP (2)`, corrección de `MAX_INLINE_BINARY_BYTES`, aviso «PENDIENTE DE DESPLIEGUE».
§10 contrastado en los repos: albaranes-persistencia manda `ide` + `["nomori","nom"]` y lee la
cabecera en el cliente y en **cinco** scripts; mcp-bbdd manda `cod` + `["cod"]` y no la lee.
Barrido de sensibles (correos, IPv4, GUID, `password|pwd=|secret|token|AccountKey|SharedAccess|
code=`, base64 ≥ 40): solo el autor y el `Co-Authored-By` del commit. Sin secretos. Si se elige
H1 (b), §8.3 debe recogerlo.

## C3 bis — Documentos que entran de fuera

- N/A los cuatro: nada tocado en `docs/referencia/` (`git diff --stat` vacío). Barrido hecho
  igualmente sobre el diff de la rama, mismos patrones: solo SHAs y falsos positivos.

## C5 — La sesión se cerró bien (lo juzgable antes del cierre)

- **N/A parcial** `tasks.md` todo `[x]`: T1-T12 y T16 `[x]`; **T13-T15 abiertas por ser MANUAL
  (humano)** y posteriores a la revisión. [x] commit `F-010 Tn:` por tarea: T1-T8, T11 (×2), T16;
  T9-T10 comparten `2bcda71` (dos verificaciones sin código, aceptable); T12 vive en `azure-apps`
  `0c4cbeb`, con el formato `sigrid-api: …` de ese repo y citando F-010.
- [x] Sin artefactos de la feature sin trackear. Lo que hay es ajeno: `` `0`].{t `` (vacío,
  2026-09-24, anterior a la rama, ya anotado en `current.md`) y `.claude/worktrees/agent-ab0e…`
  (worktree *locked* de hoy 19:48 sobre `c3d4e45`, de un agente en paralelo).
- [x] `features.json`: F-010 `in_progress`, `critico`, rama correcta; `BACKLOG.md` coherente.

**Dato para RM1** (fuera de este trozo): de `bb4a612` (medido) a HEAD solo cambian `progress/` y
`tasks.md`. **Automejora** (propuesta): `.claude/worktrees/` al `.gitignore` del arnés y a
`arnes-base`; los worktrees de revisiones en paralelo ensucian C5 y pueden forzar mutación en serie.
