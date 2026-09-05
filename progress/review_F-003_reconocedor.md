# progress/review_F-003_reconocedor.md

Revisión acotada a `infrastructure/security/database_reference_guard.py`
(rama `feature/F-003-guardia-bases-cruzadas`, HEAD `9248269`). Encargo 1 de 2:
solo el código; no se revisan checkpoints, informes ni tasks.

## VEREDICTO: RECONOCEDOR CON FALLOS

**Agujero real y explotable**: con `database: "ruesma"` se lee `msdb`. Verificado
extremo a extremo contra `SqlQueryGuard.validate()` con la config desplegada.

### H1 (GRAVE) · un salto de línea en un delimitado esconde la referencia

```sql
SELECT 1 AS "a
", name FROM msdb.dbo.sysjobs AS "z"
```

T-SQL válido: los dos alias son nombres arbitrarios que elige quien escribe la
consulta, y `msdb.dbo.sysjobs` se lee de verdad. El guardia **PASA**. Otras 40
variantes pasan igual: `SELECT 1 AS [a\n"b], name FROM msdb.dbo.sysjobs AS
[j"]`, la misma con `\r`, o `SELECT 1 AS "a""b\nc", ... ORDER BY "w"`.

**Mecanismo.** El neutralizador copia el delimitado tal cual (correcto), pero
`_IDENT` (línea 40) prohíbe `\r` y `\n` dentro de `[...]` y de `"..."`. Al
escanear, la alternativa delimitada falla en la apertura, el identificador se
desmonta y **queda una `"` suelta**; `finditer` la empareja con la siguiente `"`
de la línea y produce un único `suelto` = `'", name FROM msdb.dbo.sysjobs AS "'`.
La referencia queda dentro de ese "identificador" y nunca se analiza:
`extract_database_references` devuelve `[]`. Mismo fallo que `"z--"`, movido una
capa: allí desincronizaba el neutralizador, aquí el reconocedor. Segunda
condición suficiente: `_IDENT` tampoco entiende el escape `""`.

### H2 (GRAVE) · un `--` cerrado solo por CR se come el resto de la sentencia

```sql
SELECT --x\r name FROM msdb.dbo.sysjobs
```

La línea 256 busca el fin del comentario con `sql.find("\n", indice)`; con
finales de línea CR solos no encuentra ninguno, blanquea **hasta el final**
(`'SELECT' + 38 espacios`) y `msdb` desaparece. SQL Server cierra el comentario
de línea en CR, así que el motor sí lee `msdb`; y aunque no lo cerrara,
blanquear el resto nunca es correcto (R11). Igual con `\x0b`, `\x0c` y `\x85`.

### H3 y H4 (MENORES) · dos "deja pasar" que hoy no se explotan

`[].dbo.t`, `"".dbo.t` y `[ ].dbo.t` pasan: `_normalizar_identificador` devuelve
`""` y `_analizar` lo descarta con `if base and ...` (línea 144). Y
`SELECT msdb.dbo.*`, `... .*, 1` y `msdb.dbo. * FROM x` pasan: la excepción para
`dbo.con.*` (línea 132) recorta a dos partes sin mirar si la primera es una base.
Ninguna de las cinco es T-SQL válido, y `SELECT msdb.dbo.* FROM msdb.dbo.sysjobs`
sí se rechaza (por el FROM).

## Lo que SÍ funciona (confirmado)

- **El caso histórico y 20 variantes rechazan**: `"z--"`, `[z--]`, `"z/*"`,
  `[Client's]`, `"z""--"`, `[z]]--]`, `[z]]/*]`, `"z""'"` con `msdb` detrás;
  `[msdb]`, `"msdb"`, `msdb . dbo . sysjobs`, `msdb/*x*/.dbo.sysjobs`,
  `msdb--x\n.dbo.sysjobs`, `tempdb..sysobjects`, `tempdb.dbo.##g`, 4 partes,
  mayúsculas, `N'a.b.c'`, concatenación, comentario anidado, `\x00`, y el salto
  en un delimitador **si no hay una segunda `"` en la misma línea**.
- **Literales y comentarios**: nada de lo probado dentro de `'...'` (`[`, `"`,
  `--`, `/*`, `''`, saltos) filtra al reconocedor; `/*` anidado y `/* */ */`
  rechazan por sobreanálisis, el lado seguro.
- **Regresión: las 26 formas corrientes probadas PASAN.** `dbo.tabla`, `tabla`,
  `t.*`, `dbo.con.*`, `dbo.con .*`, literales con puntos, `'msdb.dbo.sysjobs'`
  como literal, comentarios normales, `ruesma.dbo.tabla` en cualquier caja y
  delimitada, `[mi columna]`, `[a-b]`, `[a.b]`, `[Client's Name]`, `"z--"`,
  `[a]]b]`, `"a""b"`, `N'...'`, decimales, JOIN con alias, funciones de esquema,
  multilínea y `?`. Único rechazo: `SELECT t.c.d FROM dbo.t`, correcto (R11).

## Comprobaciones pedidas

- `pytest tests/test_database_reference_guard.py -q` → **833 passed**, 1,73 s.
- `python scripts/verificar_sql_ecosistema.py` → **exit 0**, 13.639 ficheros,
  256 que hablan con la API, **0 rechazos**.

## Cambios requeridos

1. `_IDENT` (línea 40): admitir `\r` y `\n` dentro de `[...]` y `"..."`, y
   entender el escape `""` igual que ya entiende `]]`. Mientras neutralizador y
   reconocedor no lean el delimitado con la misma regla, H1 vuelve.
2. Línea 256: cerrar el comentario `--` en el primer `\r` **o** `\n`.
3. Línea 143: una base delimitada que normaliza a cadena vacía debe rechazar.
4. Línea 132: recortar por el `*` solo si la primera parte no es base prohibida.
5. Un test por cada uno de los cuatro, con el SQL exacto de este informe.

Guiones de ataque (396 combinaciones + regresión) en el scratchpad de la sesión
(`ataque.py`, `fuzz.py`, `fuzz2.py`, `e2e.py`). Solo se escribió este informe.
