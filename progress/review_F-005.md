<!-- progress/review_F-005.md -->
Revisión completa (pasada 1) del código de F-005 sobre `cfb8048`; encargo
acotado a **código + puerta de mutación**. El papeleo (C1, C2, C4 trazabilidad,
C4 ter, C5, docs) lo revisa otro reviewer en paralelo, y `init.sh` lo corre el
líder.

# F-005 · Review (código + mutación)

**Veredicto: APROBADO.** **Rigor `critico`** (declarado en
`harness/features.json`): exige fase RED, cobertura, mutación **completa**
(`max_mutantes: null`) y **0 supervivientes**. Se cumple.

## 1 · Solo se relaja lo aprobado — [x]

`git diff 602e079..cfb8048 --stat`: **tres** ficheros de producción y cinco de
tests. **No** aparecen `sql_write_guard.py`, `sql_query_guard.py`,
`database_reference_guard.py`, `identifier_guard.py`, el repositorio,
`config/settings.py` (ni `ALLOWED_WRITE_DATABASES`),
`concepto_grafico_statements.py` ni `function_app.py`. Sin cambios en
`requirements*.txt` ni `pyproject.toml`.

- `document_write_guard.py:162` — el `if gratipide == 0: return` va **después**
  de la lista blanca (156-161), nunca antes: con `permitidas=[]` o sin el 0, el
  0 muere en el mismo `raise` de F-004. Para `gratipide > 0`, cuerpo idéntico a
  F-004 (`if not existe` y `if fecbaj` intactos).
- `attach_concepto_grafico_use_case.py:271-275` — `fila` nace en `None` y la L2
  solo se ejecuta `if request.gratipide != 0`. `existe` y `fecbaj` se siguen
  derivando de `fila`, no de literales.
- `concepto_grafico_models.py:75` — `ge=1` → `ge=0`. Los negativos los sigue
  cortando el modelo, y `conide`/`contip` mantienen `ge=1`
  (`test_f005_conide_y_contip_siguen_exigiendo_al_menos_1`).

**Control negativo real, no declarado:** los tests que fijan que la clase 35
sigue exigiendo `auxgra` *con el 0 en la misma lista blanca* existen y muerden
(`test_f005_una_clase_mayor_que_cero_sigue_exigiendo_auxgra_con_el_0_permitido`
×2, `..._sigue_leyendo_auxgra_...`, `..._con_tipaso_vacio_sigue_avisando`).

**La «decisión de diseño» de T5 se acepta, y es mejor que la propuesta.** La
propuesta aprobada tenía dos llamadas al guardia, la del 0 con
`existe=False, fecbaj=None` escritos a mano: un literal que **mentiría por
construcción** si el guardia dejara de volver antes (familia F-019/F-027). T5
deja un único punto de llamada donde `existe`/`fecbaj` salen del dato real.
Mismo comportamiento, un punto de decisión menos, ningún valor muerto, y sin
ampliar el alcance: sigue tocando solo `_leer_clase`.

## 2 · Las filas del documento sin clase — [x] verificado EJECUTANDO

`ConceptoGraficoStatements.construir_filas_gra` ejecutado con `gratipide=0` y
con `gratipide=35`, mismos `ahora/sha256/emp/usu/nom/res/contenido`:

```
documental(0): gratipide=0  res=''  ima=bytes   -> doc(0) == doc(35): True
negocio(0):    gratipide=0  res='OBRA 0404'  ima=None  vin=3
cod compartido por las dos filas: True
diff negocio 0 vs 35: {'gratipide': (0, 35)}   <- UNA sola columna
```

Es el criterio (c): negocio con `gratipide=0`, documental con `gratipide=0` y
`res=''` (ya era así desde F-004: `GRATIPIDE_DOCUMENTAL=0`, `RES_DOCUMENTAL=''`),
y **ninguna otra constante cambia** (`vin=3`, `nom==nomori`, `guid=''`, `cla=''`,
`ide=None`, 29 columnas). Lo mismo afirman
`test_f005_la_fila_de_negocio_sin_clase_solo_cambia_en_gratipide` y
`test_f005_el_commit_con_el_0_escribe_las_tres_filas_igual`.

## 3 · Puerta de mutación y RM1-RM6 — [x]

**Verificación independiente del alcance y del nº de mutantes** (cálculo puro):

```
alcance_de_feature('F-005') -> origen 'rama', ref 1a0a996..feature/F-005-...
  use_case {265..275,285,286}=13 | models {71..75}=5 | guard {144..155,162,163}=14  -> 32
generar_mutantes -> TOTAL 6, uno a uno idénticos a los que la campaña dice
```

Coinciden **exactamente** con el informe (32 líneas, 6 mutantes). **La campaña
NO se queda corta:** las líneas nuevas del caso de uso están en el alcance y
generan mutante (272 `!= 0` → `== 0` y `!= 0` → `!= 1`; 274 `filas[0]` →
`filas[1]`), igual que las dos del guardia (162 `== 0` → `!= 0` y `== 0` →
`== 1`) y la del modelo (75 `ge=0` → `ge=1`). Las 32 líneas son 7 de código
efectivo más comentarios y docstring, que no producen mutantes: por eso 6 y no
más. No queda línea ejecutable del diff sin mutante.

**Reproducción de 3 de los 6 mutantes** en worktree aislado sobre `cfb8048`,
fuera del árbol real, con `pytest -k "f005 or f004"` (base limpia: `240 passed`):

| Mutante | Resultado |
|---|---|
| `guard:162` `== 0` → `!= 0` | **13 failed**, 227 passed |
| `use_case:272` `!= 0` → `== 0` | **41 failed**, 199 passed |
| `models:75` `ge=0` → `ge=1` | **9 failed**, 231 passed |

Los tres mueren, y entre los que fallan están los que el informe dice que los
matan. Worktree eliminado; `git status` y `git worktree list` limpios.

- **RM1 [x]** — «SHA de HEAD medido» = `cfb804811843749c486e71f69beae735e641e4b8`,
  completo. `git diff cfb8048..4e0a940 --stat` toca **solo** `progress/`: el
  alcance no ha crecido desde la medición, y recalculado hoy sobre HEAD da las
  mismas 32 líneas.
- **RM2 [x]** — Total 183,6 s; 6 mutantes × media 30,6 = 183,6 (coherente por
  construcción). Coste real por mutante = media × W = 30,6 × 6 = **183,6 s**,
  **por encima** de la línea base (85,9-91,6 s con los 6 workers compitiendo):
  ni salto de orden de magnitud a la baja ni coste sub-segundo. Timeout efectivo
  184 s = ceil(91,6 × 2) ✓, sin timeouts. `-x` confirmado en
  `harness/mutacion.py:551`. Total > 60 s → **campaña NO reejecutada** (183,6 s
  según el informe): recálculo puro + reproducción de 3 mutantes, como manda la
  regla. W consta en el informe de mutación («Workers | 6»), no en la tabla
  «Evidencias» de `impl_F-005.md`: dato presente y generado por la herramienta,
  no bloquea.
- **RM3 [x] N/A justificado** — cero supervivientes y cero equivalentes
  declarados en la campaña final: no hay equivalente que pueda salir muerto.
- **RM4 [x]** — aplicado por iniciativa propia: la reproducción de arriba es
  subconjunto de tests sobre copia aislada, no sobre el árbol real.
- **RM5 [x] N/A justificado** — rigor `critico`, pero **no hay superviviente
  declarado equivalente** en la campaña entregada. El único de la historia
  (campaña 1 sobre `f36a242`) no se aceptó: T5 eliminó el código muerto.
  Verificado: `generar_mutantes` sobre `cfb8048` ya no produce ese mutante.
- **RM6 [x]** — para matar aquel mutante **no se quitó código defensivo**: se
  quitó un *literal* (`existe=False`), y las guardas `if not existe` / `if fecbaj`
  siguen enteras para toda clase > 0. El invariante queda verificado **en quien
  construye el dato** (`use_case:279-280`: `existe=fila is not None`,
  `fecbaj=int(fila[3] or 0) if fila else None`), que es lo que RM6 pide. Consta
  por escrito en `impl_F-005.md` §«Decisión de diseño».
- Informe **sin** cabecera «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» =
  0; «Muestreo: no: campaña completa», como exige `critico`.

## 4 · C3 sobre los ficheros tocados — [x]

- [x] Hexagonal: `domain/models/` solo importa `re`, `typing` y `pydantic`. El
      `import` del guardia desde el caso de uso es **preexistente** de F-004
      (línea 43 ya en `602e079`), no lo introduce F-005.
- [x] Primera línea con la ruta relativa en los tres ficheros.
- [x] Sin `print()`, `breakpoint`, TODO/FIXME ni secretos: el grep sobre el diff
      solo casa «TODOS» dentro de dos comentarios en prosa.
- [x] `ruff check` sobre los tres: `All checks passed!`.
- [x] Reglas de Sigrid: no se toca SQL ni la parametrización; `insertar_negocio`
      sigue mandando 29 parámetros con `?`. Ninguna escritura ni base nuevas.
      Español en comentarios y docstrings.

## Cambios requeridos: ninguno.
