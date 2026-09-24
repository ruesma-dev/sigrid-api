<!-- specs/F-006-alta-parte-reclamacion/design.md -->
# F-006 · Diseño

## La decisión de fondo

Un **endpoint de dominio** que copia lo que hace el escritorio de Sigrid al crear un parte
desde la pestaña Reclamaciones de la UPV, medido en
`progress/explore_F-006_modelo_parte.md` (en adelante «§»): cinco tablas, sin triggers, sin
IDENTITY y sin DEFAULT. Mismo esqueleto que `sigrid/concepto-grafico` (F-004): modelo
Pydantic → **constructor puro de sentencias** → caso de uso con dry-run por defecto →
`run_in_write_transaction()`, llamado **una vez por parte**. Lo nuevo frente a los
albaranes: el código de serie se calcula **dentro** de la transacción (su `_next_cod` lo
calcula fuera: carrera que aquí no se admite) y la colisión con la UI la detecta el índice
único `con_emptipcod (emp, tip, cod)` [§3].

**Límite de microservicio: cabe.** Crear un concepto del ERP con sus filas es exactamente la
responsabilidad de la pasarela. Lo que no cabe se queda fuera: decidir qué incidencia se
vuelca, agruparlas por obra o traducir su catálogo a códigos de Sigrid es de
`postventa-incidencias` (F-040); pasar a PTE, tareas y correos son procesos de Sigrid.

## Ficheros a crear

| Fichero | Capa | Qué contiene |
|---|---|---|
| `domain/models/parte_reclamacion_models.py` | domain | `IntervinienteIn`, `ParteIn`, `CreatePartesReclamacionRequest`, `ResultadoParte`, `CreatePartesReclamacionResponse`, `ParteReclamacionError(ValueError)` con `codigo` de un conjunto cerrado (R3, R7, R12-R14, R17) |
| `application/use_cases/parte_reclamacion_statements.py` | application | `ParteReclamacionStatements(database)`: SQL constante `(sql, params)` de L1-L10 y E1-E14, constructores de las cinco filas, `siguiente_cod()`, `fecha_ole_utc()`. Sin E/S. Se autovalida con `DatabaseReferenceGuard` en `__init__` |
| `application/use_cases/create_partes_reclamacion_use_case.py` | application | `CreatePartesReclamacionUseCase(repository, settings, reloj=time.monotonic)`: guards del lote → lecturas comunes → por parte: validar → idempotencia → preview o `work(cursor)` |
| `tests/test_f006_settings.py`, `test_f006_models.py`, `test_f006_statements.py`, `test_f006_use_case.py`, `test_f006_route.py` | — | Ver `tasks.md` |

## Ficheros a modificar

| Fichero | Qué cambia |
|---|---|
| `config/settings.py` | Cuatro campos de R4. `SIGRID_RECLAMACION_PREFIJOS_REFERENCIA` reutiliza `parse_string_list` |
| `function_app.py` | Ruta `sigrid/partes-reclamacion` (POST) con el esqueleto de `sigrid_concepto_grafico`: `ParteReclamacionError` → 400 con `details.codigo`; `ValidationError`/`ValueError` → 400; resto → 500. Ninguna ruta existente se edita |
| `local.settings.sample.json` | Las cuatro claves con su defecto |
| `docs/ARCHITECTURE.md` | Ruta, modelo y caso de uso nuevos en «Capas y estructura» |
| `CLAUDE.md` | Solo la lista de rutas del mapa del repositorio |
| `azure-apps/sigrid_api.md` | R23 (commit aparte en `azure-apps`) |

## Ficheros que NO se tocan

`infrastructure/security/*` (se usan `DatabaseReferenceGuard`; ningún guardia cambia);
`sql_server_repository.py` (bastan `execute_read_query`, `peek_next_ide` y
`run_in_write_transaction`, que ya reintenta `IntegrityError`); los casos de uso y modelos de
albaranes y de `concepto-grafico` (se **importa** `hora_local_de_madrid`, no se edita);
`execute_sql_command_use_case.py`; `infra/`. No hay SQL en ficheros `NN_nombre.sql`: todo el
SQL vive como constante en el constructor, como en F-004.

## Modelo de petición (R1)

```python
class IntervinienteIn(BaseModel):        # extra="forbid" en los tres
    oficio: str = Field(..., min_length=1, max_length=24)
    proveedor: str | None = Field(default=None, min_length=1, max_length=24)
    causante: bool = False                                   # -> rcpint.cauave 1/0

class ParteIn(BaseModel):
    referencia_externa: str = Field(..., min_length=1, max_length=80)   # conext.valt
    unidad_postventa: str = Field(..., min_length=1, max_length=24)
    descripcion: str = Field(..., min_length=1, max_length=128)         # con.res
    descripcion_larga: str | None = None                                # rcp.tex (defecto: descripcion)
    tipo: str = Field(default="0002", min_length=1, max_length=24)     # auxtrcp.cod
    clase: str | None = Field(default=None, min_length=1, max_length=24)  # auxrcp.cod
    oficio: str = Field(..., min_length=1, max_length=24)               # auxofc.cod
    ubicacion: str = Field(default="", max_length=48)                   # rcp.resubi
    forma_comunicacion: Literal[0, 1] = 0                               # rcp.rcptip (Q2)
    intervinientes: list[IntervinienteIn] = Field(default_factory=list, max_length=10)

class CreatePartesReclamacionRequest(BaseModel):
    database: str
    obra: str = Field(..., min_length=1, max_length=24)
    usu: str = Field(..., min_length=1, max_length=24)                   # dbo.usu.cod
    partes: list[ParteIn] = Field(..., min_length=1)   # tope de configuración: en el caso de uso
    commit: bool = False
```

Los textos se recortan (`strip`) y uno vacío tras recortar es 400. El tope del lote no va en
Pydantic porque es configuración: `len(partes) > SIGRID_RECLAMACION_MAX_PARTES` →
`lote_demasiado_grande` antes de leer.

## Filas que se escriben (R11) — origen de cada columna [§2, §3, §5]

| Tabla | Columna ← origen |
|---|---|
| `con` (19) | `ide` ← E3 · `emp` ← `sercon.emp` · `tip` 708 · `subtip` 0 · `cod` ← E2 · `res` ← `descripcion` · `fec` ← hoy (Madrid) · `tex` NULL · `cee` 0 · `est` ← `sercon.estini` validado en `conest` · `fecbaj` 0 · `tiemod` ← `fecha_ole_utc(ahora)` · `ico` '' · `delo` '' · `del` '' · `obr` '' · `doc` '' · `serie` 0 · `hor` 0 |
| `rcp` (20) | `ide` = `con.ide` · `upvide` ← UPV · `pos` ← E4 · `fec` = `con.fec` · `hor` ← HHMMSS Madrid · `cliide` ← `ISNULL(upv.cliide,0)` · `recide` ← `ISNULL(upv.peride,0)` · `cntide` 0 · `tel` NULL · `ele` NULL · `tex` ← `descripcion_larga` o `descripcion` · `rcpide` ← `auxrcp.ide` o 0 · `motrcp` '' · `rcptip` ← `forma_comunicacion` · `fecpre` 0 · `solrcp` NULL · `trcpide` ← `auxtrcp.ide` · `resubi` ← `ubicacion` · `texurg` '' · `ofcide` ← `auxofc.ide` |
| `rcpint` (5) ×N | `ide` ← E5 (consecutivos) · `rcpide` = `con.ide` · `pos` 0 · `obrofcide` ← resuelto (R8) · `cauave` ← `causante` |
| `conext` (11) | `ide` ← E6 · `conide` = `con.ide` · `cod` 'RCPCLI' · `camtip` 0 · `camtab` '' · `valt` ← `referencia_externa` · `valn` 0 · `valf` 0 · `vali` 0 · `valm` NULL · `valb` NULL |
| `log` (14) | `ide` ← E7 · `emp` · `ori` 0 · `ope` 1 · `fec` · `hor` (= `rcp.hor`) · `usu` ← petición · `tab` 'con' · `tip` 708 · `cod` · `res` = `con.res` · `tex` NULL · `est` = `con.est` · `err` NULL |

`tip 708`, `'RCPCLI'`, `ope 1` y `tab 'con'` son discriminadores de tipo, no estados: el
estado sale de `sercon.estini` (1 `SAT` hoy) y se comprueba contra `conest` (ARCHITECTURE §7).
El `tiemod` va en **UTC** como fecha OLE (días desde 1899-12-30), medido en dos partes [§2].
`rcpint.pos` 0 es lo del escritorio y el importador; el `MAX+64` es del portal [§2].

## Sentencias (constructor puro; todas con `?`)

Lecturas comunes, una vez por lote (credenciales de lectura):

- **L1** `SELECT ide, emp, tam, estini FROM dbo.sercon WHERE tip = ? AND cod = ? AND act = 1` — `[708, 'RS<año2>.<mes>/']`; 0 filas o `tam ≠ 4` → `serie_no_encontrada`.
- **L2** `SELECT est, cod FROM dbo.conest WHERE tip = ? AND est = ?` → si no hay, `estado_inicial_no_encontrado`.
- **L3** `SELECT ide, emp, cod FROM dbo.con WHERE emp = ? AND tip = ? AND cod = ?` (obra, `tip 42`, con `emp`: `0677` existe en `emp 1` y `28` [§6]).
- **L4** `SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?`.
- **L5** UPV de la obra: `SELECT c.ide, c.cod, ISNULL(u.cliide, 0), ISNULL(u.peride, 0) FROM dbo.upv u JOIN dbo.con c ON c.ide = u.ide WHERE u.obride = ? AND c.emp = ? AND c.tip = ?` (707).
- **L6** Oficios de la obra: `SELECT o.ide, o.pos, a.cod, p.cod FROM dbo.obrofc o LEFT JOIN dbo.auxofc a ON a.ide = o.ofcide LEFT JOIN dbo.con p ON p.ide = o.prvide WHERE o.obride = ?`.
- **L7a/b/c** `SELECT ide, cod, fecbaj FROM dbo.auxtrcp` / `dbo.auxrcp` / `dbo.auxofc` (4, 3 y 130 filas). `fecbaj ≠ 0` cuenta como inexistente.

Por parte: **L8** idempotencia, `SELECT c.ide, c.cod, r.upvide FROM dbo.conext x JOIN dbo.con c
ON c.ide = x.conide LEFT JOIN dbo.rcp r ON r.ide = c.ide WHERE x.cod = ? AND x.valt = ? AND
c.tip = ? AND c.emp = ?`. En dry-run, además, **L9** `SELECT MAX(cod) FROM dbo.con WHERE emp = ?
AND tip = ? AND cod LIKE ?` y **L10** `SELECT ISNULL(MAX(pos), 0) + 64 FROM dbo.rcp`, más
`peek_next_ide` de `con`, `rcpint`, `conext` y `log`. Toda lectura con `truncado` → `ValueError`
(400): una lista de UPV u oficios a medias validaría mal en silencio.

Dentro de `work(cursor)`, por parte y en este orden:

- **E1** = L8 bajo el applock de referencias (R15). Si aparece, se devuelve sin escribir.
- **E2** `SELECT MAX(cod) FROM dbo.con WITH (UPDLOCK, HOLDLOCK) WHERE emp = ? AND tip = ? AND cod LIKE ?` con `prefijo + '[0-9][0-9][0-9][0-9]'`; `siguiente_cod(prefijo, max_cod, tam)` en Python: `None` → `0001`; > 9999 → `numeracion_agotada`.
- **E3/E5/E6/E7** `SELECT ISNULL(MAX(ide), 0) + 1 FROM dbo.<con|rcpint|conext|log> WITH (UPDLOCK, HOLDLOCK)`; **E4** `SELECT ISNULL(MAX(pos), 0) + 64 FROM dbo.rcp WITH (UPDLOCK, HOLDLOCK)`.
- **E8** revalidación: `SELECT COUNT(*) FROM dbo.upv WHERE ide = ? AND obride = ?` y `SELECT COUNT(*) FROM dbo.obrofc WHERE ide = ? AND obride = ?` por interviniente; ≠1 → `filas_afectadas_inesperadas`.
- **E9-E13** `INSERT INTO dbo.<tabla> (<todas las columnas>) VALUES (?, …)`: `con` → `rcp` → `rcpint`×N → `conext` → `log`.
- **E14** relecturas: `con` por `(emp, tip, cod)` = 1, `rcp` por `ide` = 1, `rcpint` por `rcpide` = N, `conext` por `(conide, cod)` = 1, `log` por `ide` = 1 (con `NOCOUNT ON` el `rowcount` no es fiable).

**Applocks**, siempre en este orden: `SIGRID_REFEXT_708`, `SIGRID_SERIE_708`, `SIGRID_IDE_con`,
`SIGRID_POS_rcp`, `SIGRID_IDE_rcpint`, `SIGRID_IDE_conext`, `SIGRID_IDE_log`. `SIGRID_IDE_con`
es el mismo nombre que usan los albaranes: nuestras altas de `con` quedan serializadas entre
endpoints. Los demás no los toma nadie más, así que no hay orden inverso posible.

## Flujo del caso de uso

1. `commit` → exigir llaves (R10). Base en `ALLOWED_WRITE_DATABASES` (`base_de_datos_no_permitida`; lista vacía **no** abre: se rechaza, al contrario que el patrón heredado de albaranes). Tope del lote.
2. `ahora_lote`; L1-L7. Errores del lote → `ParteReclamacionError` → 400.
3. Por parte, en orden de la petición: si `reloj() - arranque > presupuesto` → `no_procesado`; validar (R7-R8) → `rechazado`; L8 → `idempotente` o `referencia_en_conflicto`; si dry-run → `previsto` con filas y `cod`/`ide` provisionales (L9/L10 + `peek_next_ide` + desplazamiento por los `previsto` anteriores); si commit → `run_in_write_transaction(work)`: `IntegrityError` tras reintentos → `colision_de_clave`; `ParteReclamacionError` → su código; cualquier otra `Exception` → `error_de_escritura` con `type(exc).__name__`.
4. `resumen`, trazas (R20) y respuesta.

`work` es **reentrante**: las filas nacen con `ide`/`cod`/`pos` a `None` y se rellenan en cada
intento; `fec`, `hor` y `tiemod` se fijan antes (R16), así el reintento no cambia de mes.

## Riesgos y decisiones

- **Colisión con la UI (acceptance 3).** El escritorio no toma nuestros applocks. Si calcula el
  mismo `cod`, el índice único `(emp, tip, cod)` hace fallar al segundo `INSERT`: si somos
  nosotros, reintento completo (R13); si es la UI, el usuario ve el error de clave y vuelve a
  aceptar. Mientras dure nuestra transacción (milisegundos), el `HOLDLOCK` sobre el rango del
  prefijo hace esperar al `INSERT` de la UI. Con `READ_COMMITTED_SNAPSHOT` OFF [§3].
- **`rcp.pos` no tiene índice único**: una alta simultánea de la UI podría repetir un `pos`. Es
  solo orden de listado y hoy los 22.004 son distintos; se acepta y se documenta.
- **Bloqueo de la cola de `log`** (8,5 M filas, todo el ERP escribe ahí): el `HOLDLOCK` de E7
  retiene las altas de `log` de otros usuarios mientras dura la transacción. Por eso E7 va al
  final y la transacción no hace lecturas de catálogo (Q3 decide si la fila se escribe).
- **Referencia externa (Q1).** `RCPCLI` es el campo del importador y se ve en la ficha, pero ya
  lo usan para otras cosas [§5]; el prefijo obligatorio lo aísla. Sin índice sobre `valt`: L8
  filtra por `cod` (índice `conext_codvaln`) y recorre ~5.100 filas. La intercalación es
  `CI`: `PVI-1` y `pvi-1` son la misma referencia. Descartadas: `con.doc` (invisible en la
  ficha), `con.tex` (lo usan 634 partes) y guardar la referencia solo en `postventa-incidencias`
  (no sobrevive a un reintento tras un corte).
- **Una obra por lote**: aprovecha las lecturas comunes (decisión 1); el llamante trocea.
- **Oficios duplicados en la obra** (51 tripletas repetidas, 114 oficios con varios
  proveedores [§6]): regla de R8. El importador de Sigrid coge el primero; aquí solo cuando
  las filas son indistinguibles.
- **Descartado**: clonar un parte plantilla (como los albaranes): arrastraría el propietario,
  la ubicación y los textos de otro; las 5 filas se construyen enteras desde lo medido.
- **Descartado**: una transacción para todo el lote: un parte erróneo tumbaría los demás y
  retendría los bloqueos de `con` y `log` todo el lote (decisión 1 del humano).
- **Presupuesto de tiempo** (R17): el balanceador corta a 230 s; 150 s deja margen. Un parte
  `no_procesado` se reenvía sin riesgo gracias a la idempotencia.
