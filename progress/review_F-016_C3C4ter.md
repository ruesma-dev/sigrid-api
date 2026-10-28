Revisión completa (pasada 1) · bloques C3, C3 bis y C4 ter · `git diff dev` sobre HEAD `c08461fb71b4483ec991cbd45fc1ee4de35cb6b2`

# Review F-016 (proforma a origen) · C3, C3 bis y C4 ter

- **Veredicto del encargo:** APROBADO (C3 `[x]`, C3 bis N/A, C4 ter N/A).
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Este encargo no
  cubre las puertas de rigor (RED, cobertura, mutación): las revisa otro revisor.
- **Alcance:** `application/use_cases/proforma_origen_statements.py` (nuevo),
  `application/use_cases/create_proforma_use_case.py`, `domain/models/proforma_origen_models.py`
  (nuevo), `domain/models/proforma_models.py`, `function_app.py`, `config/settings.py` y,
  por arrastre, `local.settings.sample.json`. Fuera: `1733c2f` (backlog F-018) y
  `.claude/worktrees/`.
- **No ejecutado aquí** (por encargo): `bash harness/init.sh` ni la suite completa. Sí
  pytest acotado por fichero: `test_f016_statements.py` 47 ok, `test_f016_route.py` 16 ok,
  `test_f016_models.py` 38 ok, `test_f016_settings.py` 11 ok,
  `test_f016_use_case.py -k "r20 or r21 or r22"` 4 ok.

## C3 — Arquitectura y convenciones `[x]`

- `[x]` **Hexagonal.** `proforma_origen_models.py` importa solo `pydantic` y
  `domain.models.proforma_models`: dominio sin infraestructura. Las sentencias y funciones
  puras viven en `application/use_cases/`; la llave R4 en `function_app.py` (adaptador de
  entrada). `proforma_origen_statements.py:45` importa `DatabaseReferenceGuard` de
  `infrastructure.security`: mismo patrón ya aceptado en `proforma_statements.py:40`,
  `albaran_compra_statements.py:38`, `concepto_grafico_statements.py:23` y
  `parte_reclamacion_statements.py:30`; no es regresión. `docs/ARCHITECTURE.md` recoge
  `proforma_origen_models` y la ruta a origen.
- `[x]` **Primera línea con ruta** en los 2 ficheros de código nuevos, los 5 modificados y
  los 7 de tests nuevos (comprobado fichero a fichero con `head -1`).
- `[x]` **Sin `print()`, TODO/FIXME ni secretos.** Barrido de las líneas añadidas del
  alcance con los patrones IPv4, GUID, `password|pwd=|secret|apikey|api_key|AccountKey` y
  correo `@dominio.(es|com)`: **0 coincidencias**. Sin dependencias nuevas
  (`requirements.txt` sin cambios).
- `[x]` **Reglas de dominio de Sigrid:**
  - `[x]` Base correcta: LP7-LP9 se validan contra `request.database` al construir
    `ProformaOrigenStatements` (también la relectura de LP8 dentro de la transacción,
    `create_proforma_use_case.py:537`). Nada toca `ruesma_rep`.
  - `[x]` `cod`/`fec`/`tip` se leen de `con` (`c.cod`, `c.fec`, `c.tip`) con
    `JOIN dbo.con c ON c.ide = d.ide`; de `dca` solo `ctride`, `docoritip`, `docoriide`
    (`proforma_origen_statements.py:50-58`).
  - `[x]` Nada se recalcula solo: lo escrito sigue siendo el núcleo de F-009 (totales,
    `ctrprodes`, `mov`) sin tocarlo (R2); las arrastradas van con `can`/`tot`/`ivacuo` 0 y
    sin `mov` ni `UPDATE` (D6, `proforma_origen_statements.py:278-282`), por el mismo
    `insertar_dcapro`, que valida cada columna con `IdentifierGuard`
    (`albaran_compra_statements.py:1389`).
  - `[x]` Estados: ningún estado nuevo. `DOCORITIP_A_ORIGEN` y `TIP_ALBARAN` son
    constantes de tipo ya existentes en F-007/F-009, no estados de `conest`.
  - `[x]` SQL parametrizado con `?`; ver R22 abajo. La suma de R19 (`importe_de_cadena`) es
    sobre las líneas de UN documento, acotadas por el tope de R14, y `_leer` rechaza una
    lectura truncada (`create_albaran_compra_use_case.py:423`): no hay suma a medias.

### R22 · seguridad del SQL nuevo `[x]`

- Tres sentencias, todas constantes de módulo, `SELECT`, con `?` y sin literales ni `;`:
  LP7 `proforma_origen_statements.py:50`, LP8 `:55`, LP9 `:60`. LP9 es `SELECT *` sobre
  `dcapro`: mismo criterio que la plantilla clonada de F-009 (los nombres salen de la
  base, no de la petición).
- `DatabaseReferenceGuard.validate(..., contexto="lectura")` sobre las tres en el
  constructor (`:66-69`); tests `test_f016_r22_cada_sentencia_pasa_por_el_guardia_de_bases`
  y `..._otra_base_dentro_del_sql_no_pasa`.
- Ningún `DELETE`, `MERGE`, DDL ni `UPDATE` nuevo: `grep` sobre las líneas añadidas de
  `application/`, `domain/`, `function_app.py` y `config/` solo encuentra esas palabras en
  docstrings. Control negativo en `test_f016_r22_todas_de_lectura_sin_delete_merge_ddl_ni_update`.
- **`infrastructure/security/` sin tocar:** `git diff dev --stat -- infrastructure/` vacío y
  `git log dev..HEAD -- infrastructure/` sin commits.

### R20 · códigos nuevos en subclases `[x]`

- `CODIGOS_*_PROFORMA` de `proforma_models.py` sin cambios en el diff. Los nuevos
  (`escritura_proformas_origen_deshabilitada`, `anterior_no_valida`,
  `anterior_con_sucesora`, `linea_anterior_no_valida`, `linea_nueva_ya_en_la_anterior`)
  viven en `CODIGOS_*_ORIGEN` y en `ProformaOrigenError`, `FalloLineaProformaOrigen` y
  `AvisoProformaOrigen` (`proforma_origen_models.py:29-66`).
- Todo `raise`/construcción con código nuevo usa la subclase (grep en `application/` y
  `function_app.py`): `proforma_origen_statements.py:125,131,135,147,200,222`,
  `function_app.py:376`. Como `ProformaOrigenError` hereda de `AlbaranCompraError`, la ruta
  lo responde con el manejador de siempre (400 + `details.codigo`).

### R21 · traza `[x]`

- `create_proforma_use_case.py:195-202`: solo a origen se añaden `modo`,
  `primera_de_cadena`, `anterior` (el `con.cod`, que R21 pide), `n_continuadas` y
  `n_arrastradas` (`:322`). Nada de textos, nombres, CIF, precios ni importes. En mes la
  traza no cambia (R1).
- Los mensajes de error, que sí citan `cod` y fechas, no van a la traza: el caso de uso
  guarda solo `codigo`/`codigos` y la ruta registra `codigo` e índices
  (`function_app.py:283-288`). Tests `test_f016_r21_*` (4) con lista negativa de valores
  sensibles, en verde.

### R4 · llave en `function_app.py` `[x]`

- `config/settings.py:156`: `sigrid_proforma_origen_enabled`, defecto `False`, alias
  `SIGRID_PROFORMA_ORIGEN_ENABLED`; `local.settings.sample.json` la declara `"false"`.
  Ninguna App Setting existente cambia.
- `function_app.py:337-338`: tras validar el modelo, **después** de la llave de F-007 y
  **antes** del caso de uso; solo cierra `commit` + `modo == "origen"`
  (`:375`), la previa y la de mes no la miran. Tests `test_f016_r4_*` de ruta (4) y de
  settings (6) en verde.

## C3 bis — Documentos que entran de fuera · N/A

Motivo: el diff no añade ni modifica nada en `docs/referencia/`
(`git diff dev --stat -- docs/referencia/` vacío). Comprobado además que ninguna rama del
historial `dev..HEAD` añade PDF ni ofimática (`git log --diff-filter=A --name-only` filtrado
por `.pdf|.doc(x)|.xls(x)|.ppt(x)`: 0 ficheros).

## C4 ter — Rutas sensibles · N/A

Motivo: el repositorio no declara `harness/rutas_sensibles.json` (no existe), así que el
bloque no aplica según su propia cabecera.

## Observaciones (no bloquean)

1. Variable de una letra `l` (PEP8 la desaconseja) en `create_proforma_use_case.py:200` y
   `domain/models/proforma_models.py:268`. Hay decenas de precedentes en el repo
   (`create_albaran_compra_use_case.py`, `proforma_statements.py`); no se exige cambio.

2. Al cerrar esta revisión el árbol de trabajo tenía un cambio SIN commitear ajeno a este
   revisor en `proforma_origen_statements.py:247` (`"canoriant": 0` -> `1`): tiene forma
   de mutante aplicado por la campaña o el RM4 que corre otro revisor en paralelo **en el
   árbol principal**. No lo he tocado; esta revisión vale sobre el HEAD commiteado. Quien
   lo lanzó debe confirmar que el árbol queda limpio (`git status`) antes del cierre.

## Cambios requeridos

Ninguno en los bloques de este encargo.
