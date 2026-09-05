<!-- specs/F-003-guardia-bases-cruzadas/design.md -->
# F-003 · Diseño

## La decisión de fondo: detectar, no analizar

No se escribe un analizador de T-SQL. Se escribe un **detector de referencias
cualificadas**: cualquier secuencia de identificadores separados por puntos con
**tres o más partes** se considera una referencia a otra base, y su primera
parte se valida contra la lista blanca.

Por qué así y no un parser:

- Un analizador completo de T-SQL es un proyecto en sí mismo, y uno incompleto
  da falsa seguridad —justo el fallo que esta feature corrige—.
- La forma de nombrar otra base en SQL Server es **una sola**: prefijar el
  identificador. No hay otra vía que no esté ya prohibida por
  `_ALWAYS_FORBIDDEN` (`OPENROWSET`, `OPENDATASOURCE`, `EXEC`, `USE`).
- El detector puede **pasarse de estricto sin romper nada**, porque en este
  repositorio no se usan nombres de tres partes salvo para cruzar bases, que es
  exactamente lo que se quiere controlar.

Esto cumple R11: ante la duda, rechaza.

## Ficheros a crear

| Fichero | Qué contiene |
|---|---|
| `infrastructure/security/database_reference_guard.py` | `DatabaseReferenceGuard`: extrae las bases citadas en un SQL y las valida contra una lista blanca. Sin dependencias de `Settings`: recibe la lista como argumento, para que sea un módulo puro y trivial de testear |
| `tests/test_database_reference_guard.py` | Los casos de R3, R4, R5 y R11 sobre el detector aislado |
| `tests/test_sql_write_guard_bases.py` | R1, R2, R6: el guardia de escritura rechazando y aceptando |
| `tests/test_sql_query_guard_bases.py` | R7, R8: lo mismo en lectura |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `infrastructure/security/sql_write_guard.py` | En `_validate_statement()`, tras las comprobaciones actuales, llamar al detector con `settings.allowed_write_databases`. **No se toca nada más de la clase** |
| `infrastructure/security/sql_query_guard.py` | En `validate()`, tras las palabras prohibidas, llamar al detector con `settings.allowed_databases` |

## Ficheros que NO se tocan

- `infrastructure/security/identifier_guard.py` — valida identificadores
  sueltos que llegan por campos del request, no SQL. Otro problema.
- `infrastructure/repositories/sql_server_repository.py` — la elección de
  credencial y la transacción no cambian.
- `function_app.py`, los casos de uso y los modelos de dominio. Los guardias ya
  están enganchados donde toca; esto es lógica dentro de ellos.
- `config/settings.py` — **no se añade ninguna variable de entorno**. La
  feature no es configurable a propósito: un interruptor para desactivar el
  guardia es la forma segura de que acabe desactivado.

## La clase

```python
class DatabaseReferenceError(ValueError): ...

class DatabaseReferenceGuard:
    @classmethod
    def extract_database_references(cls, sql: str) -> list[str]:
        """Bases citadas explícitamente. Vacío si el SQL solo usa 1-2 partes."""

    @classmethod
    def validate(cls, sql: str, *, allowed: list[str], contexto: str) -> None:
        """Lanza DatabaseReferenceError si cita una base fuera de `allowed`
        o si usa un nombre de cuatro partes."""
```

Capa: `infrastructure/security`, como sus hermanos. No es dominio: es una
defensa del adaptador SQL.

## El reconocedor

Un identificador de SQL Server, en las formas que admitimos:

```
IDENT   = [A-Za-z_][A-Za-z0-9_$#]*      |  [ ... ]  |  " ... "
CADENA  = IDENT ( \s* \. \s* IDENT? )+   ← el `?` cubre `base..tabla`
```

Reglas de decisión sobre cada CADENA encontrada:

| Partes | Decisión |
|---|---|
| 1 o 2 | Se ignora: es `tabla` o `esquema.tabla`, resuelto contra la conexión (R5) |
| 3 | La **primera** parte es la base. Se valida contra la lista blanca (R1, R2, R7) |
| 4 o más | **Rechazo siempre**: servidor vinculado (R4) |

Antes de recorrer, se **neutralizan literales y comentarios** para no confundir
un texto con una referencia: cadenas `'...'` (con `''` escapado), comentarios
`--` hasta fin de línea y `/* ... */`. Se sustituyen por espacios, conservando
las posiciones. Sin esto, `WHERE res = 'a.b.c'` daría un falso positivo, que
por R11 sería un rechazo injusto.

**Normalización de la comparación**: se quitan corchetes y comillas, y se
compara en minúsculas contra la lista blanca también en minúsculas. SQL Server
es habitualmente insensible a mayúsculas en nombres de base, y la lista blanca
es configuración escrita a mano (R3).

**Falsos positivos aceptados a conciencia**: un alias con punto tipo
`a.b.c` fuera de una referencia real (por ejemplo `t.col.valor` sobre un tipo
CLR o XML) se rechazaría. No se usa nada de eso en este repositorio, y R11 dice
que ante la duda se rechaza. Si algún día apareciera, el mensaje de error lo
dice con claridad y se decide entonces.

## Puntos de enganche

`SqlWriteGuard._validate_statement(sql)` — al final, antes del `return`:

```python
DatabaseReferenceGuard.validate(
    normalized_sql,
    allowed=self._settings.allowed_write_databases,
    contexto="escritura",
)
```

`SqlQueryGuard.validate(request)` — tras el bucle de palabras prohibidas, con
`allowed=self._settings.allowed_databases` y `contexto="lectura"`.

El mensaje: `"la sentencia nombra la base de datos 'X', que no está permitida
para <contexto>. Permitidas: a, b"`. Nada de host ni de usuario (R6).

## Riesgos y decisiones

| Decisión | Alternativa descartada | Por qué |
|---|---|---|
| Detector por reconocimiento léxico | Analizador T-SQL completo (`sqlglot`) | Una dependencia nueva en una Function App por una comprobación de diez líneas, y un parser que no entienda un dialecto acaba dejando pasar lo que no entiende |
| Rechazar los nombres de 4 partes siempre | Validar el servidor contra otra lista | No hay servidores vinculados; una lista vacía que nadie mantiene es una lista que alguien acabará rellenando sin pensar |
| Sin variable de entorno para desactivarlo | `ENFORCE_DATABASE_REFERENCES=true` | Un interruptor de seguridad configurable termina apagado. Si hay que revertir, se revierte el despliegue |
| Aplicarlo también a lectura | Solo a escritura | El agujero es el mismo; que el daño sea menor no lo convierte en aceptable, y `ALLOWED_DATABASES` deja de ser decorativa |

## Riesgo de regresión, y cómo se acota

El riesgo real es romper una consulta legítima que hoy funciona. Mitigación:

1. Los 341 tests actuales deben seguir en verde.
2. **Antes de dar la feature por cerrada**, se ejecuta contra la API desplegada
   una consulta de cada script de `scripts/` que hoy funcione, para comprobar
   que ninguna usa nombres de tres partes sin querer. Es verificación `MANUAL`
   y la ejecuta el humano o el implementer con lecturas.
3. `documents/read` no pasa por estos guardias (construye su SQL con
   `IdentifierGuard`), así que la descarga de PDFs no puede verse afectada.
