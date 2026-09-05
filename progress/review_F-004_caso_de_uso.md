<!-- progress/review_F-004_caso_de_uso.md -->
# F-004 · Review ACOTADA: caso de uso, modelos y ruta
Revisión completa (pasada 1) de un ÁMBITO ACOTADO sobre HEAD `8a37b21` (código medido en
`87098d6`): `attach_concepto_grafico_use_case.py` (líneas citadas sin prefijo),
`concepto_grafico_models.py`, la ruta nueva de `function_app.py` y sus tests; de contraste,
`sql_server_repository.py`, `create_direct_albaran_use_case.py` y `sql_models.py`. El constructor
de sentencias y el papeleo los cubren otros dos encargos: **este informe no juzga la feature
entera**. Rigor `critico`; RED, cobertura y mutación quedan **N/A por acotación del encargo**, no
por omisión (la RED de T11/T13 del `impl_F-004.md` §3 es un error de colección: evidencia mínima
válida pero débil; queda para el papeleo). `pytest` de los tres ficheros de test → **81 passed**
(0,89 s). Ni `init.sh` (lo corre el líder) ni nada contra la API ni contra el ERP.

**Veredicto (ámbito): APROBADO**
## 1 · Dry-run: solo lecturas con credencial de LECTURA (R9) · [x]
`_ejecutar:146-155` solo llega a `_commit` con `commit=True`; en dry-run las únicas puertas al
repositorio son `execute_read_query` (`_leer:212`) y `peek_next_ide` (`:394-396`), y **ambas usan
`_read_credentials()`** (repositorio l. 68 y 203). `_exigir_llaves_de_escritura:184` solo corre
con `commit=True`: el dry-run ni mira `sql_server_write_*`. Tests: `..._r9_el_dry_run_no_abre_
ninguna_transaccion_de_escritura` (`transacciones == []`), `..._r9_..._seis_lecturas_en_orden` y
`..._r10_sin_las_llaves_el_dry_run_sigue_funcionando`.
## 2 · La transacción (R11-R15) · [x]
`_commit:423-544`: `work` hace L5 bajo applock → E1,E2,E3 → E4,E5,E6 **en ese orden**
(`:462-467`) → E7, tres relecturas, y si una no da exactamente 1 lanza
`filas_afectadas_inesperadas` (`:477-483`). `work` no tiene ni un `try`: todo sube y el
`except Exception` del repositorio (l. 310-315) hace `ROLLBACK` y relanza. El `cod` se genera
**fuera** de `work` (`:122-131`), igual en cada reintento; `rcg.gra` usa el `ide` de E2 sin
rederivarlo (`:457`, con test que compara la lista exacta de parámetros del INSERT de enlace).
`ConceptoGraficoError` no es `IntegrityError` → no reintenta; el `IntegrityError`, agotados los
reintentos, sube y la ruta lo traduce a `colision_de_clave`. Tests R14 (3 casos) y R15.
## 3 · Idempotencia (R17) · [x]
L5 cruza por `(emp, cod)` y compara `sha256` **en Python** (`:283-289`), saltando candidatos con
`ima` NULL; se repite dentro de la transacción (`:443-448`). Una huérfana no puede ser candidata
(L5 es `JOIN`) y se avisa (`:291-303`). `committed:false` con `commit:true` idempotente: **lo doy
por correcto**: R17 pide `ok:true`, `idempotente:true` y `filas_afectadas:0` —los tres están— y
nada dice de `committed`; ponerlo a `true` sin escribir una fila sería mentir, y `dry_run = not
commit` deja los dos campos independientes con la forma de R2 intacta. Arista: quien decida por
`committed` verá `false` en un éxito; eso debe constar en `azure-apps/sigrid_api.md` (papeleo).
## 4 · Las dos decisiones no escritas en la spec · aceptables
**(a) `model_construct`** (`:200-217`). Comprobado: deja `max_rows`/`timeout_seconds` en `None` y
el repositorio **los resuelve él** (`request.max_rows or default_max_rows`, l. 66-67). Solo se
pierden `strip`, los `min_length` y los topes contra `MAX_ALLOWED_ROWS`/`MAX_QUERY_TIMEOUT_
SECONDS`: inaplicables, porque el SQL es constante de módulo, los parámetros los pone el caso de
uso y `database` ya pasó por el modelo y por `_validar_bases`. El repositorio **no** revalida el
SQL (`SqlQueryGuard` vive en `ExecuteSqlQueryUseCase`): la única defensa es
`DatabaseReferenceGuard` en el constructor de sentencias, y sería igual con `model_validate`.
**(b) base64 en dos sitios.** Fuzz de 200.000 cadenas: de las 179.687 que pasan
`_base64_bien_formado` (alfabeto, `len%4==0`, `=` solo al final y ≤2), **ninguna** falla
`b64decode(validate=True)`; el `ValueError` sin `codigo` del guardia es inalcanzable desde HTTP
—cinturón para quien lo llame directo— y la ruta ya lo saca como 400.
## 5 · Ruta (R3) · [x]
`except` en el orden correcto (`ConceptoGraficoError` → `IntegrityError` → `ValidationError` →
`ValueError` → `Exception`; tres son subclases del siguiente, así que el orden importa y está
bien). `git diff --numstat dev...HEAD -- function_app.py` = **66 / 0**, y el test lista las siete
rutas anteriores. Guards R6/R10 antes de tocar la red (`:97-100`, antes del guardia del fichero y
de `_leer_concepto`); `build_dependencies()` no abre conexión. `ruff`: 3 avisos en `dev` y **los
mismos 3** en HEAD (I001, BLE001, RUF010, todos en código anterior); el nuevo no añade ninguno.
## 6 · Auditoría (R21) y trampas C3 de dominio · [x]
`_trazar:89-92` serializa endpoint, database, conide, contip, gratipide, usu, commit, bytes,
sha256, cod, resultado, codigo, idempotente, filas_afectadas y duracion_ms; ningún camino mete el
binario ni el base64 en el dict, y el test lo prueba por negación (`_B64`, `_B64[:32]`, `"%PDF"` y
`"contenido_base64"` ausentes) y traza también el fallo. C3: documental solo por nombre de tres
partes; `emp` sale de `con.emp`, no de la petición (test `..._r7_el_emp_sale_del_concepto`);
`pos = MAX(pos)+64` leído, no inventado; nada se recalcula (ni totales, ni PMP, ni estados); SQL
constante con `?`; sin `UPDATE`/`DELETE`, sin prints ni secretos; primera línea con la ruta.
## Recomendaciones (NO bloquean; para el humano o el backlog)
1. `:212-217` — `_leer` descarta `_truncado` y el tope real es `DEFAULT_MAX_ROWS` (200,
   `config/settings.py:28`). Un concepto con más de 200 binarios del **mismo tamaño exacto**
   dejaría fuera al candidato bueno y R17 fallaría en silencio (duplicado). Probabilidad ínfima,
   consecuencia silenciosa: `max_rows` explícito en L5/L6, o lanzar si `truncado`.
2. `:172` — `if permitidas and database not in permitidas` **falla abierto** con
   `ALLOWED_WRITE_DATABASES` vacía. Patrón calcado de `add_contract_lines:171`,
   `create_direct_albaran:299` y `create_purchase_albaran:506`, al revés que
   `sql_write_guard.py:69`, que falla cerrado. No bloqueo (calcar era el diseño), pero merece
   feature propia para los cuatro.
3. `:331` y `:271` — `vin=3` y el `64` de respaldo van a pelo existiendo `VIN_REPOSITORIO` y
   `POS_PASO` en `concepto_grafico_statements.py`. Cosmético.
4. Automejora del protocolo (propuesta, no aplicada): cuando una revisión se trocea en encargos
   paralelos, cada trozo debería declarar en cabecera **qué checkpoints quedan fuera de su
   ámbito**, como hace este. Propongo añadirlo a `.claude/agents/reviewer.md` §Informe, para que
   el líder no cierre una feature sumando trozos con un hueco sin cubrir.
