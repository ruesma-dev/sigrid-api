Revisión completa (pasada 1) · bloques C3, C3 bis y C4 ter · `dev...HEAD` (merge-base `60db955`, HEAD `fe85523`)

# Review F-007 · registrar proforma · C3, C3 bis y C4 ter

- **Veredicto (de estos tres bloques):** APPROVED
- **Alcance del encargo:** solo C3, C3 bis y C4 ter de `CHECKPOINTS.md`. C1, C2, C4, C4 bis y C5 los revisan
  otros reviewers. Por instrucción del líder: sin `init.sh` ni suite completa, solo `pytest` de ficheros concretos;
  nada contra Sigrid ni contra la API desplegada; solo lectura del árbol.
- **Nivel de rigor:** `critico` (declarado). En estos bloques no cambia lo que se exige: C3 y C3 bis aplican en todo
  nivel; C4 ter depende solo de la declaración de rutas sensibles.

**Ejecutado:** `pytest -p no:cacheprovider` de `test_f007_{statements_contrato,transaccion,route,use_case,models}.py`:
**273 passed** (2,6 s). `git diff dev...HEAD -- infrastructure/` → **0 líneas** (ni `security/` ni el resto).

## C3 — Arquitectura y convenciones

- [x] **Hexagonal.** `domain/models/proforma_models.py` importa solo `pydantic`, `datetime.date` (validación pura de
      `fecha_proforma`, sin reloj) y `domain.models.albaran_compra_models`. `application/` sin `pyodbc`, red, `open`
      ni `os.environ` (grep). La única E/S de `create_proforma_use_case.py` es el repositorio inyectado (`_leer`) y el
      `cursor` que el núcleo de F-009 entrega a `_comprobar_dentro` (R28). `infrastructure/`: nada nuevo
      (ARCHITECTURE §`sigrid/proforma` lo declara). El import `application → infrastructure.security
      .DatabaseReferenceGuard` es el patrón ya establecido (`albaran_compra_statements`,
      `concepto_grafico_statements`), no una violación nueva.
- [x] **Primera línea con la ruta** en los 13 `.py` nuevos (comprobado uno a uno) y en los 6 `.md` de referencia.
- [x] **Sin `print()`, TODO/FIXME, `breakpoint` ni secretos** en las líneas añadidas (grep del diff). Sin
      dependencias nuevas (`requirements*`/`pyproject` sin cambios).
- [x] **Reglas de dominio de Sigrid:**
  - [x] **Base correcta.** Todo contra la base de la petición (`ruesma`); ni rastro de `ruesma_rep`. Las escrituras
        van por el núcleo de F-009 (`ALLOWED_WRITE_DATABASES` sin cambios, comprobado en `_comprobar_guardas`).
  - [x] **`cod`/`fec`/`tip` de `con`.** LP1-LP6 toman `c.cod`, `c.fec`, `c.tip` de `dbo.con` por
        `JOIN ... ON c.ide = d.ide|t.ide`; de las extensiones solo sus campos propios (`dca.entref/totbas/ctride/
        cla/synckey/docoritip`, `ctr.entcif/entres/obride`, `ctrpro`/`dcapro`).
  - [x] **Nada se recalcula solo.** El alta es el núcleo de F-009 + F-015 (totales, `canser`, estados, `mov`/PMP);
        `test_f007_transaccion.py:94` fija que los únicos `UPDATE` son `E9_SERVIDO` y `E11_ESTADOS_CONTRATO` (R27).
  - [x] **Estados no hardcodeados.** Ningún `est`/`conest` nuevo. `CLA_PROFORMA = 141` y `docoritip` 1/44 son clase
        y tipo de origen fijados por la spec (R12, M31, D13), no estados.
  - [x] **SQL parametrizado y agregación en SQL.** Ver tabla siguiente. LP2 agrega con `SUM ... GROUP BY`. El
        anterior/origen (R20-R22) suma `totbas` de LP1 en Python, pero sobre las proformas de UN contrato (una por
        mes) y con `max_rows` = tope y **truncado → `ValueError`** (`_leer`, sin ignorarlo): aceptable.

### SQL nuevo (`application/use_cases/proforma_statements.py`, LP1-LP6)

| Sentencia | Constante | `?` | Guardia | Verbo |
|---|---|---|---|---|
| LP1 proformas del contrato | sí (l. 64) | 5 | sí | `SELECT` |
| LP2 anterior por línea | sí (l. 70) | 7 | sí | `SELECT ... SUM ... GROUP BY` |
| LP3 contratos de la obra | sí (l. 77) | 2 | sí | `SELECT` (subconsulta `COUNT`) |
| LP4 líneas de contratos | plantilla `IN {marcadores}` (l. 83) | n | sí, **al generarse** (l. 148) | `SELECT` |
| LP5 referencia | sí (l. 90) | 2 | sí | `SELECT` |
| LP6 líneas de la proforma | sí (l. 95) | 1 | sí | `SELECT` |

- `{marcadores}` solo se rellena con `"(" + "?, " * n + ")"` a partir de un **número**; lista vacía → `ValueError`
  (no hay `IN ()`). Los patrones `PROF%`/`PREV%` viajan como parámetro, no en el SQL.
- `ProformaStatements.__init__` valida las seis con `DatabaseReferenceGuard.validate(..., allowed=[database],
  contexto="lectura")`; también la instancia que crea `_comprobar_dentro` dentro de la transacción.
- Sin `DELETE`, `MERGE`, `INSERT`, `UPDATE` ni DDL en el código nuevo (grep). En el núcleo (`albaran_compra_
  statements.py`, `create_albaran_compra_use_case.py`) el diff **no añade ninguna sentencia**: solo parametriza
  serie, cifras, `cla`, llave y catálogo por `PerfilAlta` (costuras 1-5).
- Control negativo en tests (R32): `test_f007_r32_todas_de_lectura_sin_delete_merge_ni_ddl`,
  `..._cada_sentencia_pasa_por_el_guardia_de_bases`, `..._otra_base_dentro_del_sql_no_pasa`, y el de R27 en
  `test_f007_transaccion.py`. En verde.

### Traza R33 (`create_proforma_use_case.py:131-175`)

- Claves: `endpoint`, `database`, `obra` (código), `contrato` (código), `resuelto_por`, `referencia`, `periodo`,
  `numero_orden`, `commit`, nº de líneas, `resultado`, `estado`, `cod`, `con_ide`, `codigo(s)`, `duracion_ms`. Sin
  textos, nombres, CIF, precios ni importes. En excepción, `type(exc).__name__`, nunca el mensaje.
- Ruta: `ValidationError` traza `(loc, type)` sin valores; `ValueError`, solo el tipo; `ProformaError`, solo códigos
  (`_respuesta_albaran_compra_error`). Tests `test_f007_r33_*` (4) con lista de valores prohibidos: en verde.

### Ruta `sigrid/proforma` (`function_app.py`)

- [x] Orden: `model_validate` → `_exigir_escritura_de_proformas(settings, commit)` → `CreateProformaUseCase.run`. La
      llave R5 va **antes** del caso de uso y **solo con `commit`**; la de albaranes no la abre. Además el núcleo
      vuelve a exigir `SIGRID_PROFORMA_WRITE_ENABLED` vía `perfil.campo_llave` (defensa en profundidad).
      Tests `test_f007_r5_*` (3) en verde.

## C3 bis — Documentos de fuera (6 nuevos en `docs/referencia/`)

- [x] **Cabecera con origen y fecha** según el caso 1 de `docs/referencia/README.md` en los seis (origen, fecha del
      documento, conversión con `markitdown` el 2026-10-25, original fuera del repo). Índice del README actualizado.
- [x] **Originales fuera.** `git log --diff-filter=A` de la rama y de **todo el historial** (`--all`): ningún
      `.pdf/.xls(x)/.doc(x)/.ppt(x)/.msg/.eml`. Árbol de trabajo: ninguno (fuera de `.venv`).
- [x] **Barrido ejecutado por este reviewer** sobre los 42 ficheros del diff (docs, specs, progress, código, tests,
      fixture). Patrones: correo `[\w.%+-]+@[\w.-]+\.\w{2,}`; IPv4 `(\d{1,3}\.){3}\d{1,3}`; GUID
      `[0-9a-f]{8}-...-[0-9a-f]{12}`; credenciales `(password|secret|token|api_key|function_key|
      connectionstring|AccountKey|SharedAccessSignature|sig=|Bearer)\s*[:=]`; claves `[A-Za-z0-9+/]{32,}={0,2}`;
      teléfonos españoles; NIF/CIF/NIE; IBAN `ES\d{2}...`; Azure (`subscriptions/`, `tenant`, `azurewebsites.net`,
      `database.windows.net`, `vault.azure`); firmas (`Fdo`, `Firmado`, `Sr./Sra.`, `Un saludo`); ~80 nombres de
      pila españoles. **Resultado:** 0 correos, 0 GUID, 0 credenciales, 0 teléfonos, 0 IBAN, 0 IDs de Azure
      (solo la frase normativa de ARCHITECTURE). Falsos positivos explicados: «IPv4» = códigos de partida
      `02.03.02.01`; «claves» = dos SHA de git en `mutacion_F-007.md`; CIF = sintéticos `B000004xx`/`B0000000n`
      (fixture y tests, declarados ficticios en `_nota`); «BERENJENO» = partida de encofrado, no un apellido;
      «Firmado por:» de las hojas, sin nombre detrás.
- [x] **Redacciones anotadas** en la cabecera de los dos correos (nombres, correos, teléfonos, firma con CIF y
      dirección, URL de Outlook y del artifact, aviso legal); el cuerpo solo lleva marcadores (`[Nombre]`,
      `[correo]`, `[Firma: <rol>]`). Las cuatro hojas declaran «Trae precios de subcontratista. Su conversión la
      autorizó el humano el 2026-10-25»: la autorización consta **solo** en esas cabeceras (ver observación 3).

### `azure-apps` commit `af81713` (solo ese commit)

- [x] 1 fichero (`sigrid_api.md`, +100/−1). Mismo barrido sobre las líneas añadidas: 0 coincidencias. Solo
      nombres de App Settings, valores de despliegue no secretos (`["PRF-"]`, productos, naturalezas), códigos de
      error y la obra 0719. Sin URL de la Function, claves ni personas. El autor del commit es la identidad git de
      siempre del repositorio (291/291 commits), no contenido del documento.

## C4 ter — Rutas sensibles

- **N/A, justificado:** no existe `harness/rutas_sensibles.json` (solo `rutas_sensibles.ejemplo.json`), y
  `harness/init.sh:513` solo evalúa la puerta si existe la declaración. `CHECKPOINTS.md` (C4 ter): «Sin esa
  declaración este bloque es N/A y no hay nada que justificar». Sin declaración no hay informe, `exige_lineas` ni
  frescura que comprobar. En cualquier caso el diff no toca `infrastructure/` (0 líneas).

## Cobertura de lo revisado (requisito → test)

| Requisito | Tests |
|---|---|
| R5 llave antes del caso de uso, solo con `commit` | `test_f007_route.py::test_f007_r5_*` (3) |
| R27 solo los `UPDATE` de F-009 | `test_f007_transaccion.py` (aserción l. 94-97) |
| R32 SQL constante, `?`, guardia, sin DML/DDL | `test_f007_statements_contrato.py::test_f007_r32_*` (10) |
| R33 traza sin datos sensibles | `test_f007_use_case.py::test_f007_r33_*` (4) |

## Observaciones (no bloquean)

1. `create_albaran_compra_use_case.py` (`_comprobar_guardas`): con el perfil de proforma el mensaje sigue diciendo
   «Escritura de albaranes desactivada: ...» aunque el código sea `escritura_proformas_deshabilitada` y cite
   `SIGRID_PROFORMA_WRITE_ENABLED`. Solo aparece si la ruta deja pasar el commit (falta `SIGRID_DOMAIN_WRITE_ENABLED`
   o credenciales). Cosmético; el consumidor decide por el código.
2. `function_app.py:341`: el 500 usa `logger.exception` (traceback completo) y devuelve `str(exc)`, igual que las
   otras nueve rutas. No es la traza de R33, pero un mensaje de excepción inesperada puede citar valores. Patrón
   heredado, fuera de esta feature.
3. La autorización del humano para convertir hojas con precios de subcontratista consta solo en la cabecera de cada
   documento, no en `progress/`. Suficiente para C3 bis; para auditar, convendría que también quedara en el
   informe del implementer.

**Automejora (propuesta, no aplicada):** declarar `infrastructure/security/**` en un `harness/rutas_sensibles.json`
de este repo; hoy C4 ter es N/A aunque `CLAUDE.md` trata ese directorio como sensible solo en prosa.

## Cambios requeridos: ninguno en C3, C3 bis ni C4 ter.
