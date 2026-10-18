# F-011 · Requisitos: `documents/read` valida `database`

> **Aprobada por el humano el 2026-10-18** con D1 = `ALLOWED_DATABASES` tal cual, D2 = **A1**, D3 = 400 `BaseNoPermitidaError` listando las bases permitidas y D4 = sensible a mayúsculas. Las tareas y requisitos marcados [A1] / «solo con A1» **aplican**. El humano autoriza también el paso 5 de la verificación manual (un dry-run de `sigrid/contrato-lineas` con una base inyectada, sin `commit`).

Origen: D6 de F-010 (`progress/spec_F-010.md`). Rigor `critico`. Diseño en
[`design.md`](design.md); decisiones abiertas D1-D4 en design §Decisiones.

Hoy `POST documents/read` no valida `database` en ningún punto (modelo, caso de
uso ni ruta) y `SqlServerRepository._connect` lo interpola sin escapar en
`DATABASE={database};`. `sql/read` sí lo valida (`SqlQueryGuard`).

Glosario:
- **Lista de lectura**: `Settings.allowed_databases` (`ALLOWED_DATABASES`), la
  misma de `sql/read`, tal como la deja `parse_string_list` (elementos
  recortados).
- **Texto de rechazo**: `La base de datos '<database>' no está permitida.
  Permitidas: <lista unida por ", ">`, y `(ninguna)` en lugar de la lista
  cuando está vacía. `<database>` es el valor ya recortado por el modelo.
- **Patrón de identificador**: el de `IdentifierGuard`,
  `^[A-Za-z_][A-Za-z0-9_]*$`, sobre el valor recortado.

## A · Validación de `database` en `documents/read` (acceptance 1-3)

R1. CUANDO `documents/read` recibe una petición válida para el modelo cuyo
`database` no está en la lista de lectura, el sistema debe responder **400**
con `error` igual al texto de rechazo y `details` igual a
`{"type": "BaseNoPermitidaError"}` (sin más claves).

R2. SI `database` no está en la lista de lectura, ENTONCES el sistema no debe
llamar a `SqlRepository.read_document` ni, por tanto, a `pyodbc.connect`.

R3. El sistema debe comparar `database` con la lista de lectura por igualdad
exacta de texto, distinguiendo mayúsculas (como `SqlQueryGuard`): `RUESMA_REP`
se rechaza si la lista solo trae `ruesma_rep`; ` ruesma_rep ` se acepta porque
el modelo ya lo recorta (comportamiento actual de `DocumentReadRequest`).

R4. MIENTRAS la lista de lectura esté vacía, el sistema debe rechazar toda
petición de `documents/read` según R1, con `Permitidas: (ninguna)`.

R5. SI `database` contiene `;`, `=`, `{`, `}` o espacios interiores (p. ej.
`ruesma_rep;APP=x`, `ruesma_rep;`, `x=y`, `ruesma rep`), ENTONCES el sistema
debe rechazarlo según R1 y R2, salvo que ese texto exacto figure en la lista
de lectura (caso cubierto por R13-R15 si se aprueba D2).

R6. CUANDO una petición trae a la vez un `database` no permitido y un
identificador no válido (`table`, `key`, `blob_column`...), el sistema debe
responder el rechazo de R1: la base se valida antes que los identificadores.

R7. El sistema debe leer la lista de lectura del mismo `Settings` que usa el
resto de la aplicación (`build_dependencies()`), y no debe consultar
`SIGRID_DOCUMENT_WRITE_DATABASE` ni `ALLOWED_WRITE_DATABASES` para esta
validación.

R8. El error de R1 debe ser una clase propia, `BaseNoPermitidaError`, que
herede de `ValueError` (si faltara su `except`, caería en 400 y no en 500),
cuyo `details.type` **nunca** sea `"ValueError"`: mcp-bbdd lee
400 + `ValueError` como «sin binario».

R9. CUANDO la ruta rechaza por R1, el sistema debe emitir un `warning` de log
`BaseNoPermitidaError en documents/read: <texto de rechazo>`, como el resto
de errores de la ruta.

## B · Lo que no cambia (acceptance 2)

R10. CUANDO `database` está en la lista de lectura (`ruesma_rep`), el sistema
debe comportarse exactamente como tras F-010: mismos argumentos a
`read_document`, misma respuesta 200, mismas cabeceras.

R11. El sistema debe conservar sin cambios de código HTTP, `details.type` ni
texto los demás errores de `documents/read`: 400 `ValidationError`
(`Solicitud invalida.`), 400 `IdentifierValidationError`, 400 `ValueError`
(«sin binario», F-010 R14), 409 `DocumentoAmbiguoError` (F-010 R13) y 500.

R12. Los tests de F-010 deben seguir pasando con sus aserciones intactas; solo
puede cambiar la construcción de `ReadDocumentUseCase` en
`tests/test_f010_caso_de_uso.py`.

## C · Defensa en profundidad en `_connect` (SOLO si el humano aprueba D2 = A1)

R13. El adaptador `SqlServerRepository._connect` debe validar `database` con
`IdentifierGuard.validate_identifier(database, field_name="database")` antes
de componer la cadena de conexión, y usar el valor que devuelve.

R14. SI `database` no casa con el patrón de identificador, ENTONCES `_connect`
debe lanzar `IdentifierValidationError` con el texto
`El identificador 'database' contiene caracteres no permitidos: <valor>` y no
llamar a `pyodbc.connect`. Aplica a todos los métodos públicos del adaptador
que conectan (lectura, escritura, documentos, dominio).

R15. CUANDO `database` casa con el patrón (`ruesma`, `ruesma_rep`, `master`),
la cadena que recibe `pyodbc.connect` debe ser idéntica carácter a carácter a
la de hoy.

## D · Documentación y verificación (acceptance 4-5)

R16. El sistema debe quedar documentado en `azure-apps/sigrid_api.md` (§8.3
campo `database` y tabla de errores; §5.1; §4 fila de `ALLOWED_DATABASES`;
§10 consumidores) y en `docs/ARCHITECTURE.md` (párrafo de listas blancas), en
el mismo trabajo.

R17. Tras el despliegue, en solo lectura: `ruesma_rep` con `gra` ide 365617
debe responder 200 con `X-Document-Size` 17865 (el de F-010 T15), y una base
no permitida debe responder 400 `BaseNoPermitidaError` (design §Verificación
manual).

Trazabilidad: cada R tiene al menos un test `test_f011_rN_*`, salvo R16
(revisión del reviewer contra el código) y R17 (MANUAL, tasks T12-T14).
