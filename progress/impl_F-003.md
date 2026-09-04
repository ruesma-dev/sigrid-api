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

El fallo de T5 merece quedar escrito: un test que falla por su propio andamiaje
se parece a uno que encuentra un fallo real; la diferencia estaba en que caían
también los casos que no tenían nada que ver.

## 3 · La condición del humano: verificada sobre el ecosistema entero

No bastaba con que los tests pasaran: había que demostrar que **ninguna
consulta que hoy funciona empieza a fallar**. Se hizo en dos pasos.

**a) Inventario.** Un subagente barrió `C:\Users\pgris\PycharmProjects\`
buscando SQL enviado a esta API. Encontró **seis ficheros** con nombres de tres
partes, todos de **lectura** contra `ruesma_rep`, ninguno de escritura, ninguno
de cuatro partes, ninguno a una base ajena:

- `albaranes-persistencia/scripts/` — `diagnose_sigrid_contrato_docs.py`,
  `diagnose_sigrid_contrato_docs_v2.py`,
  `diagnose_sigrid_contrato_gra_modificado.py`, `trace_sigrid_rcg_dual.py`
  (y su copia idéntica dentro del monorepo `albaranes`).
- `postventa-incidencias/infra/13_caracterizacion_grafico_url.ps1`.

Todos interpolan el nombre de la base en un f-string (`{database_rep}.dbo.gra`,
`$SigridBaseDocumental.dbo.gra`), así que **un grep del literal `ruesma_rep.dbo`
no los habría encontrado**. Como `ruesma_rep` está en `ALLOWED_DATABASES`,
siguen funcionando. Los siete están en
`tests/test_sql_query_guard_bases.py::TestConsultasRealesDelEcosistema`, con el
fichero de origen anotado en cada uno.

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

## 5 · Evidencias

| Qué | Resultado |
|---|---|
| **Suite completa** | **1.210 pasan**, 1 skip, 0 fallos. Los 341 previos siguen en verde |
| **Tiempo de la suite** | 32,4 s en el árbol principal; 32,5 s la línea base medida por la campaña |
| **`ruff`** | **79 avisos**, exactamente los de antes de la feature. Los 7 que introduje se corrigieron |
| **Cobertura** | **99,2 %** de las líneas cambiadas (244/246), umbral 80 % del nivel `critico` |
| **Mutación · mutantes** | **129** generados y evaluados, alcance 513 líneas en 4 ficheros |
| **Mutación · muertos** | **110** |
| **Mutación · supervivientes** | **13**, los trece analizados uno a uno en [`mutacion_F-003.md`](mutacion_F-003.md) |
| **Mutación · timeouts** | **6**, repasados en serie; son bucles infinitos (`fin += 1` → `fin -= 1`), que la suite mata colgándose |
| **Mutación · workers** | **8** worktrees en paralelo; el repaso de timeouts, en serie |
| **Mutación · tiempo** | 1.363,6 s (22,7 min) |
| **Verificador del ecosistema** | 13.639 ficheros recorridos, 256 consumidores, **0 rechazos**, exit 0 |
| Puerta de tamaño | requirements 83/150, design 142/250, impl dentro del tope |
| T7 · `scripts/` de este repo | ningún nombre de tres partes |
| T8 · MANUAL | **pendiente del humano**, ver §6 |

### 5.1 · Recorrido de las campañas

**52 → 18 → 13 → 9** supervivientes en cuatro campañas. El detalle de cada una
y el análisis de los que quedan vivos, en
[`mutacion_F-003.md`](mutacion_F-003.md). Tres cosas que merecen quedar aquí:

**Un test que pasaba por casualidad**, encontrado por la mutación y no por
lectura: el que debía verificar `SELECT ruesma_rep.dbo.gra.*` nombraba la base
**dos veces** en el mismo SQL, así que la segunda aparición hacía que el
resultado saliera bien aunque la lógica estuviera rota.

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

## 7 · Falsos positivos: los previstos, y los dos que encontró el reviewer

**Corregidos tras la pasada 1 de revisión** (los encontró el reviewer probando
47 formas de T-SQL, no una lectura del código):

- **`SELECT dbo.con.*`** se leía como tres partes, siendo SQL válido y
  corriente. Ahora se descarta la última parte cuando está vacía. Solo la
  última: en `base..tabla` la vacía es la del medio y ahí sí hay tres partes,
  y `ruesma_rep.dbo.gra.*` sigue detectándose.
- **`SELECT [Client's Name] FROM dbo.con`** moría con «literal sin cerrar»:
  el apóstrofo dentro de un identificador entre corchetes arrancaba un literal
  falso que se comía el resto de la sentencia. Ahora el neutralizador conoce el
  corchete como delimitador, con su escape `]]`.

Se corrigieron en vez de solo anotarse porque van en la dirección de la
condición del humano: que nada legítimo se rechace.

> **Corrección de la pasada 2: lo que decía aquí era falso.** El arreglo de
> `dbo.con.*` **sí amplió lo que pasaba el filtro**, porque descartaba la parte
> vacía final **siempre**, sin mirar qué seguía al punto: ocho formas hostiles
> pasaban de rechazarse a colarse, entre ellas `tempdb..#t`, T-SQL válido
> contra una base fuera de `ALLOWED_DATABASES`. No era la vulnerabilidad que
> F-003 vino a cerrar —`ruesma_rep` seguía bloqueada— pero era justo lo que R11
> prohíbe. Corregido: la parte vacía se descarta **solo si lo siguiente es un
> `*`**. Lo encontró el reviewer comparando 26 formas hostiles antes y después,
> no leyendo el código.

**Deuda que sí se queda, y con motivo:**

- El detector **rechaza `base.esquema.tabla.columna`**, que es SQL válido de
  cuatro partes sin ser un servidor vinculado, y `t.col.value(...)` /
  `c.doc.nodes(...)` de XML y CLR. Nadie los usa en el ecosistema (verificado
  en §3) y el mensaje de error es explícito. Distinguirlos exigiría saber la
  posición dentro de la sentencia, es decir, un analizador: el precio no
  compensa mientras nadie los escriba.
- **Punto ciego del verificador** (lo señaló el reviewer): un fragmento sin
  verbo no llega a ser candidato. Lo cubre el inventario manual del §3a.
- Los avisos `RUF012` y `SIM102` de los dos guardias son **anteriores** a esta
  feature y no se tocan: no es su sitio.
