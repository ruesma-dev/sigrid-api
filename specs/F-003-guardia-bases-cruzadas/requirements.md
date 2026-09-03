<!-- specs/F-003-guardia-bases-cruzadas/requirements.md -->
# F-003 · Requisitos

**El guardia debe validar también las bases nombradas dentro del SQL.**

## Contexto

Medido el 2026-09-03 (`progress/explore_ruesma_rep.md`): `SqlWriteGuard`
valida `request.database` contra `ALLOWED_WRITE_DATABASES`, pero **no mira los
identificadores de base que aparecen dentro de la sentencia**. Con
`database: "ruesma"` y `INSERT INTO ruesma_rep.dbo.gra ...` se escribe en la
base documental, que la configuración declara cerrada. Lo mismo vale para
lectura: `SqlQueryGuard` no impide leer cualquier base de la instancia.

No es teórico: así se midieron los permisos de `user_rw`. Y `user_rw` tiene
`INSERT`, `SELECT` y `UPDATE` sobre `ruesma_rep.dbo.gra`, donde vive la **única
copia** de los 359.438 documentos de la empresa, en una base con modelo de
recuperación `SIMPLE`.

## Requisitos

### Escritura

**R1.** CUANDO una sentencia de `sql/write` nombre una base de datos que no
esté en `ALLOWED_WRITE_DATABASES`, el sistema debe rechazar el batch completo
antes de abrir ninguna conexión, aunque el campo `database` de la petición sí
esté permitido.

**R2.** CUANDO una sentencia de `sql/write` nombre una base de datos que sí
esté en `ALLOWED_WRITE_DATABASES`, el sistema debe ejecutarla con normalidad.

**R3.** El sistema debe reconocer la referencia a una base tanto en nombres de
tres partes (`base.esquema.tabla`) como de cuatro (`servidor.base.esquema.tabla`),
con el esquema omitido (`base..tabla`), entre corchetes (`[base].[dbo].[tabla]`),
entre comillas dobles (`"base"."dbo"."tabla"`) y con cualquier capitalización.

**R4.** SI una sentencia usa un nombre de **cuatro partes** (servidor
vinculado), ENTONCES el sistema debe rechazarla siempre, aunque la base citada
esté permitida. No hay servidores vinculados en uso y la única razón de un
nombre así es salir de la instancia.

**R5.** El sistema debe seguir aceptando los nombres de una y dos partes
(`tabla`, `dbo.tabla`), que se resuelven contra la base de la conexión y son la
forma normal de escribir en este proyecto.

**R6.** SI el rechazo se produce, ENTONCES el mensaje de error debe nombrar la
base detectada y la lista de bases permitidas, sin revelar credenciales ni
host.

### Lectura

**R7.** CUANDO una consulta de `sql/read` nombre una base que no esté en
`ALLOWED_DATABASES`, el sistema debe rechazarla, con el mismo criterio de R3,
R4 y R5.

**R8.** MIENTRAS `ALLOWED_DATABASES` contenga una base, las consultas que la
nombren explícitamente deben seguir funcionando: la lectura cruzada entre
`ruesma` y `ruesma_rep` es legítima y hay diagnósticos que la usan.

### Cobertura y no regresión

**R9.** El sistema debe cubrir cada uno de R1-R8 con al menos un test
unitario que no toque red ni base de datos.

**R10.** El sistema no debe cambiar el comportamiento de ninguna petición que
hoy sea válida: todos los tests existentes deben seguir en verde, y los
endpoints de dominio (`sigrid/albaran`, `sigrid/albaran-directo`,
`sigrid/contrato-lineas`) deben seguir funcionando sin cambios en su código.

**R11.** SI la detección no puede decidir con certeza si un identificador es
una base (por ejemplo, ante un SQL que el analizador no sepa recorrer),
ENTONCES el sistema debe **rechazar**, no permitir. Un guardia que ante la duda
deja pasar no es un guardia.

## Fuera de alcance

- Abrir `ruesma_rep` a la escritura. Eso es F-004, y por la puerta del endpoint
  de dominio, no por `sql/write`.
- Revisar por qué `user_rw` tiene `UPDATE` sobre la documental, o si tiene
  `DELETE`. Es una conversación con quien administre el motor.
- Quitar `master` de `ALLOWED_DATABASES`, que conviene revisar pero es una
  decisión de configuración, no de código.
- Reescribir los guardias como un analizador SQL completo. Ver `design.md`.
