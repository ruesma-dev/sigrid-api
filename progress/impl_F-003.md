# progress/impl_F-003.md

# F-003 · Informe de implementación

**El guardia de escritura valida también las bases nombradas dentro del SQL.**

| | |
|---|---|
| **Rama** | `feature/F-003-guardia-bases-cruzadas` |
| **Rigor** | `critico` |
| **Portero** | `bash harness/init.sh` en **ENTORNO LISTO** |
| **Pasada de revisión** | 1ª: RECHAZADO ([`review_F-003.md`](review_F-003.md)). Los seis cambios requeridos, atendidos |
| **Condición del humano** | «No puede fallar la escritura/lectura que se hace ahora» — **verificada, no supuesta**. Ver §3 |

---

## 1 · Qué se hizo

Un módulo nuevo, `infrastructure/security/database_reference_guard.py`, y dos
llamadas: una en `SqlWriteGuard._validate_statement()` y otra en
`SqlQueryGuard.validate()`. Nada más de producción cambia.

No es un analizador de T-SQL: es un reconocedor de nombres cualificados. Toda
cadena de identificadores con **tres o más partes** se trata como referencia a
otra base; la primera parte se valida contra la lista blanca. Los de **cuatro o
más** (servidor vinculado) se rechazan siempre.

Antes de recorrer, se neutralizan literales `'...'` (con `''` escapado) y
comentarios `--` y `/* */`, para que un `WHERE nom = 'a.b.c'` no parezca una
referencia. Un literal o un comentario **sin cerrar rechaza**, en vez de
adivinar: es R11, ante la duda no se deja pasar.

## 2 · Fase RED, con su traza

| Tarea | Traza |
|---|---|
| T1 | `ModuleNotFoundError: No module named 'infrastructure.security.database_reference_guard'` — el módulo no existía |
| T3 | `10 failed, 11 passed`. Fallaban **exactamente** los diez que exigen rechazo; los once de no regresión ya pasaban, que es la señal de que el test no se estaba engañando |
| T5 | `13 failed` en lectura, incluidos casos triviales de dos partes → **no era el guardia, era el doble**: al `SettingsDoble` le faltaba `max_rows`. Corregido el doble, no el guardia |

El fallo de T5 merece quedar escrito: un test que falla por su andamiaje se
parece a uno que encuentra un fallo real; los delataba que caían también los
casos que no tenían nada que ver.

## 3 · La condición del humano: verificada sobre el ecosistema entero

No bastaba con que los tests pasaran: había que demostrar que **ninguna
consulta que hoy funciona empieza a fallar**. Se hizo en dos pasos.

**a) Inventario.** Un subagente barrió los repositorios buscando SQL enviado a
esta API. Encontró **seis ficheros** con nombres de tres partes —cuatro
scripts de `albaranes-persistencia` (y su copia en el monorepo) y un `.ps1` de
`postventa-incidencias`—, todos de **lectura** contra `ruesma_rep`, ninguno de
escritura, ninguno de cuatro partes, ninguno a una base ajena. Todos
**interpolan** el nombre de la base en un f-string, así que un grep del literal
no los habría encontrado. Como `ruesma_rep` está en `ALLOWED_DATABASES` siguen
funcionando, y los siete casos están fijados en
`tests/test_sql_query_guard_bases.py::TestConsultasRealesDelEcosistema` con su
fichero de origen anotado.

**b) Verificador reproducible.** `scripts/verificar_sql_ecosistema.py` recorre
los repositorios, extrae las cadenas que parecen SQL destinado a esta API,
sustituye cada interpolación por el peor caso (`ruesma_rep`) y las pasa por el
guardia real con la configuración **real** de la Function App
(`ALLOWED_DATABASES = master, ruesma_rep, ruesma`;
`ALLOWED_WRITE_DATABASES = ruesma`). Resultado:

```
Ficheros recorridos: 13633
De ellos, hablan con esta API: 256

RESULTADO: ninguna consulta del ecosistema sería rechazada por el
guardia nuevo. Lo que hoy funciona seguirá funcionando.
```

**Y el verificador tiene sus propios tests**
(`tests/test_verificar_sql_ecosistema.py`, 20 casos), porque una verificación
que se rompe en silencio es peor que no tenerla: seguiría diciendo «ningún
rechazo» sin haber mirado nada.

Esos tests **encontraron un fallo real que una lectura del código no vio**: el
extractor no reconocía `INSERT INTO t (a) VALUES (?)` como SQL —el `INTO` lo
consumía el primer grupo de la expresión regular y no quedaba ninguna otra
palabra clave detrás—, así que **el verificador se estaba saltando en silencio
todas las escrituras con `VALUES`**, que son justo las que más importan.
Corregido, el barrido se repitió y siguió dando cero.

Se ejecuta con `python scripts/verificar_sql_ecosistema.py` y devuelve 1 si
algo se rompería, así que sirve igual la próxima vez que se toque una lista
blanca.

**Honestidad sobre el camino:** la primera pasada dio 42 rechazos en 29
ficheros; se revisaron **uno a uno** y todos eran artefactos del extractor, no
del guardia (proyectos de PostgreSQL, código embebido en here-strings,
docstrings cuyos puntos suspensivos parecen cualificación, un `print()` de
ayuda con la cadena partida). Se afinó con tres reglas —solo ficheros que
hablen con esta API, la cadena empieza por verbo SQL, y un literal sin cerrar
es ruido de extracción— hasta dejarlo en cero. **Ninguna toca el guardia.** El
reviewer las auditó desactivándolas una a una: no esconden ningún caso real.

## 4 · Ficheros

**Creados:** `infrastructure/security/database_reference_guard.py`,
`tests/test_database_reference_guard.py` (37 casos),
`tests/test_sql_write_guard_bases.py` (21), `tests/test_sql_query_guard_bases.py`
(18), `scripts/verificar_sql_ecosistema.py` y
`tests/test_verificar_sql_ecosistema.py` (20).

**Modificados:** `sql_write_guard.py` y `sql_query_guard.py` (import + una
llamada al final de la validación, sin tocar el orden de las comprobaciones
anteriores); `docs/ARCHITECTURE.md`; `azure-apps/sigrid_api.md` §2.1 y §5.1.

**No tocados, a propósito:** `config/settings.py` —la feature **no lleva
variable de entorno**: un interruptor de seguridad configurable acaba
apagado—, `identifier_guard.py`, el repositorio, los casos de uso y
`function_app.py`.

## 5 · Evidencias — todas medidas sobre `e1ac0dd`, HEAD de la rama

| Qué | Resultado |
|---|---|
| **Suite completa** | **1.262 pasan**, 1 skip, 0 fallos. Los 341 previos siguen en verde |
| **Tiempo de la suite** | 32,2 s en worktree limpio (línea base del reviewer); 80,5–88,1 s por worker con los 8 en paralelo, que es contención, no la suite |
| **`ruff`** | **79 avisos**, exactamente los de antes de la feature. Los 7 que introduje se corrigieron |
| **Cobertura** | **99,2 %** de las líneas cambiadas (254/256), umbral 80 % del nivel `critico` |
| **Mutación · mutantes** | **138** generados y evaluados; alcance 4 ficheros, 607 líneas |
| **Mutación · muertos** | **124** — la campaña publicó 123; la corrección está medida, no estimada (§5.1) |
| **Mutación · supervivientes** | **7** — publicó 9; los siete, analizados y aceptados por el humano en [`mutacion_F-003.md`](mutacion_F-003.md), y el reviewer reprodujo uno (0 diferencias en 1.900 entradas) |
| **Mutación · timeouts** | **7** — publicó 6; son bucles infinitos (`fin += 1` → `fin -= 1`), que la suite mata colgándose |
| **Mutación · tiempo y workers** | 1.681,8 s (28,0 min) con **8** worktrees en paralelo |
| **Mutación · fiabilidad** | los 138 reevaluados EN SERIE: **0 falsos muertos** sobre 123 ([`mutacion_F-003_remuestreo.md`](mutacion_F-003_remuestreo.md)) |
| **Verificador del ecosistema** | 13.639 ficheros recorridos, 256 consumidores, **0 rechazos**, exit 0 |
| Puerta de tamaño | requirements 83/150, design 142/250, impl dentro del tope |
| T7 · `scripts/` de este repo | ningún nombre de tres partes |
| T8 · MANUAL | **pendiente del humano**, ver §6 |

### 5.1 · Recorrido de las campañas

**52 → 18 → 13 → 10 → 7 → 7 → 7** supervivientes en siete campañas. La séptima corre sobre `e1ac0dd`, ya con los cuatro arreglos de T16, y devuelve los mismos siete: ninguno nuevo. Dos de los nueve que publicó estaban mal clasificados —el de la línea 263 se cuelga, el de la 266 muere en 1,9 s—, de ahí el recuento real 124/7/7. El detalle de cada una
y el análisis de los que quedan vivos, en
[`mutacion_F-003.md`](mutacion_F-003.md). Tres cosas que merecen quedar aquí:

**Un test que pasaba por casualidad**, encontrado por la mutación y no por
lectura: el que verificaba `SELECT ruesma_rep.dbo.gra.*` nombraba la base **dos
veces** en el mismo SQL, y la segunda aparición tapaba una lógica rota.

**Un agujero que dejaba pasar, encontrado en la pasada 3.** El neutralizador
trataba los corchetes como delimitador pero **no las comillas dobles**, así que
en `SELECT 1 AS "z--", j.name FROM msdb.dbo.sysjobs` —T-SQL válido— veía el
`--` de dentro del alias como un comentario, se comía el resto de la línea y la
referencia a `msdb` **se colaba**. Es el peor tipo de fallo de un guardia. Los
delimitados están ahora unificados en una sola tabla, cada uno con su escape
(`]]` y `""`), y un barrido de 44 combinaciones —cuatro formas de envolver un
alias por once construcciones capaces de tragarse la sentencia— no deja ninguna
pasando salvo el `--` que comenta de verdad.

> **La lección, y va escrita porque se repitió tres veces:** el apóstrofo en
> corchetes, el escape `]]` y el `--` en comillas dobles son **el mismo
> problema** —un delimitador cuyo contenido no debe interpretarse— y se
> parchearon caso a caso en vez de tratarse de raíz. La tabla de delimitados
> debió existir desde el primer arreglo.

**Cuatro «equivalentes» que no lo eran.** El reviewer reprodujo los trece —no
la muestra de uno que pide RM5— y midió que los supervivientes 7, 8, 9 y 12
**fallaban abiertos** ante un corchete mal cerrado o un comentario pegado a un
operador. Se matan con tests de una línea que fijan el fallo cerrado, que era
lo correcto y estaba al alcance. Corregido en la pasada 2.

**La defensa de lo que sigue vivo es una propiedad**, no una casualidad: un
test recorre las dos direcciones —una base prohibida se ve rodeada de lo que
sea; sin referencia, ningún contexto provoca rechazo— sobre 55 combinaciones.

**Incidente:** el script auxiliar que prueba mutantes se pasó del límite de
tiempo y dejó un fichero mutado en el árbol (`sys.path.insert(0)` →
`insert(1)`). Se detectó con `git status` y se revirtió. **Ningún commit lo
incluye**, comprobado por el reviewer con `git log -S` sobre todo el
historial.

## 6 · Lo que queda, y es del humano

1. **T8 · Prueba contra la API desplegada.** Solo se puede hacer **después** de
   desplegar, y confirma sobre el sistema real lo que §3 demuestra sobre el
   código. Sugerencia: ejecutar `diagnose_sigrid_contrato_docs.py` de
   `albaranes-persistencia`, que es el que usa la lectura cruzada, y comprobar
   que devuelve lo mismo que antes.
2. **Revisar `master` en `ALLOWED_DATABASES`.** Ningún consumidor lo necesita.
   Quitarlo es una línea de configuración y cierra otra puerta. Fuera del
   alcance de F-003.
3. **Merge de la rama a `dev`**, que lo hace el humano.

## 7 · Falsos positivos y agujeros: los seis que hubo que corregir

Los encontró el reviewer probando T-SQL, no leyendo el código, y **casi todos
son la misma clase de fallo**: neutralizador y reconocedor leyendo los
delimitados con reglas distintas. Cada vez que difieren en algo —un apóstrofo,
un escape `]]`, un `--`, un salto de línea— el análisis se desincroniza y una
referencia puede esconderse dentro de un falso identificador. Se parchearon caso
a caso durante tres rondas hasta tratarlo de raíz: **una sola regla, en un solo
sitio**, como debió estar desde el primer arreglo.

| Caso | Qué hacía | Arreglo |
|---|---|---|
| `SELECT dbo.con.*` | Se leía como tres partes y se rechazaba | Se descarta la parte vacía final, **solo si lo siguiente es un `*`** |
| `SELECT [Client's Name] …` | El apóstrofo abría un literal falso que se comía la sentencia → «literal sin cerrar» | El corchete es delimitador, con su escape `]]` |
| `SELECT 1 AS "z--", … FROM msdb.…` | El `--` se leía como comentario y **la referencia se colaba** | La comilla doble también es delimitador, con su escape `""` |
| `SELECT 1 AS "a⏎", … FROM msdb.…` | El reconocedor prohibía saltos de línea dentro del delimitado, lo desmontaba y **la referencia quedaba dentro de un falso identificador** | `_IDENT` lee el delimitado con la MISMA regla que el neutralizador |
| `SELECT --x␍ … FROM msdb.…` | El `--` solo se cerraba con `
`, así que con CR se blanqueaba la sentencia entera | El comentario lo cierra cualquier terminador de línea |
| `SELECT * FROM [].dbo.t` | Base ilegible descartada en silencio | Se rechaza: hay tres partes, luego hay base, y no se sabe cuál |
| `SELECT msdb.dbo.*` | Se recortaba a dos partes sin mirar si la primera era base | Con tres partes solo se recorta si la primera es un esquema conocido |

El primer arreglo **amplió lo que pasaba el filtro** (descartaba la parte vacía
siempre, y ocho formas hostiles se colaban, `tempdb..#t` entre ellas); corregido
en la pasada 2. Los tres últimos dejaban pasar en vez de rechazar de más, que es
el lado malo. Detalle en `review_F-003_reconocedor.md`.

**Deuda que se queda, y con motivo:** el detector rechaza
`base.esquema.tabla.columna` y las notaciones XML/CLR (`t.col.value(...)`);
nadie las usa en el ecosistema y el mensaje es explícito. El verificador tiene
un punto ciego con los fragmentos sin verbo, cubierto por el inventario manual.
