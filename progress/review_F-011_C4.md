<!-- progress/review_F-011_C4.md -->
Revisión completa (pasada 1) de `dev...4d1c266` (HEAD `4d1c266a6bce40566e1aa9cb7dca79424229e399`), acotada a C4 y C4 ter, más la lupa sobre `_connect` y la guía manual T12-T14

# Review F-011 · bloque C4 / C4 ter

**Veredicto del bloque: APROBADO.** No hay cambios requeridos en el código. Antes de ejecutar T14 conviene hacer
cuatro ajustes a la guía manual (§Observaciones 1-4). No bloquean el APROBADO, pero el líder debería aplicarlos.

**Nivel de rigor:** `critico`, declarado en `harness/features.json` (F-011). Para este bloque exige tests trazables
por requisito, ninguno con red ni BBDD, y las verificaciones MANUAL con su comando exacto.

**Lo que NO se ejecutó, por orden del encargo:** ni `bash harness/init.sh` ni la suite completa, porque otra revisión
corre la campaña de mutación. Las cifras «2664 passed» y «cobertura 16/16» del informe no las he reproducido yo.
Su comprobación queda para los bloques C1 y C4 bis. Tampoco toqué el código ni `.env`. No hice commit.

## Lo que se ejecutó

- `pytest tests/test_f011_{caso_de_uso,ruta,composicion,repositorio}.py tests/test_f010_{caso_de_uso,ruta}.py -q`
  → **160 passed**. `--collect-only` de los cuatro de F-011 → **134**, la cifra de «Evidencias». Por fichero salen
  28 + 15 + 2 + 89, contados a mano en el código: 89 = 8 métodos × 8 bases (R14) + 8 × 3 (R15) + 1 (R13).
- **Comprobación independiente de R15 (RM4, en el scratchpad, sin tocar el árbol).** Script
  `scratchpad/r15/comparar.py`. Carga el adaptador de `dev` (`git show dev:…`) y el de HEAD con `pyodbc.connect`
  sustituido por un doble. Para los 8 métodos que conectan y 6 bases válidas (`ruesma`, `ruesma_rep`, `master`,
  `_x`, `A1_b`, `RUESMA`) compara la cadena y los kwargs (`timeout`, `autocommit`). Usa credenciales con `;`, `{`
  y `}`. Resultado: **48 comparaciones, 0 diferencias**. R15 se cumple contra la cadena real de `dev`, no solo
  contra la cadena que el test reconstruye a mano.
- `git diff --stat cafc340..HEAD`: desde el SHA en que se midió la mutación solo cambian `docs/ARCHITECTURE.md`,
  `tests/test_f011_ruta.py`, `tasks.md` y ficheros de `progress/`. El código de producción es el medido.
- `git show --stat 4d1c266`: el commit T15 solo toca `current.md`, `impl_F-011.md` y `tasks.md`. El `init.sh`
  que cita el informe corresponde al código de HEAD.

## C4 — La verificación es real

- [x] **Cada requisito tiene ≥ 1 test trazable y todos pasan.** Tabla abajo. R16 y R17 quedan fuera por diseño
  (requirements, «Trazabilidad»): R16 es revisión documental y R17 es MANUAL post-despliegue.
- [x] **Los unit tests no tocan red ni BBDD.** Lo leí en los cuatro ficheros:
  - Los repositorios son dobles (`RepositorioDoble`, `RepositorioQueRevienta`).
  - Donde se usa el adaptador real, `pyodbc.connect` se sustituye por `prohibido` (lanza `AssertionError`) o por
    el doble que captura la cadena y corta con `Capturada`.
  - Los ajustes son `SimpleNamespace` o `Settings.model_construct`, que no lee ni el entorno ni `.env`.
    `build_dependencies.cache_clear()` se llama antes y después.
  - No hay `socket`, `requests`, `httpx` ni `urllib` (grep).
  - `build_dependencies()` real (R7) solo construye objetos: ningún constructor conecta.
- [x] **MANUAL listadas con comando y pendientes.** T12-T14 están en `[ ]` y marcadas MANUAL en `tasks.md`.
  `current.md` las da como «Quedan T12-T14 (MANUAL)». Los comandos están en design §Verificación manual. Remitir
  a ese apartado se aceptó ya en F-010 (`review_F-010_C4.md`). El paso 5 no trae un cuerpo exacto: ver
  Observación 1.

**Cifras de «Evidencias»:** 134 tests de F-011, reproducida; SHA de mutación `cafc340`, coherente con HEAD;
2664 tests y 16/16 de cobertura, no reproducidas por orden del encargo (tienen su comando en el informe).

## C4 ter — Rutas sensibles

- **N/A formal.** `harness/rutas_sensibles.json` no existe en el repositorio (`ls harness/`). Según
  `CHECKPOINTS.md` §C4 ter, sin esa declaración el bloque es N/A y no hay informe que exigir.
- **Verificación extra pedida por el líder sobre `_connect`.** Hecha y en verde:
  1. **Un único punto de conexión.** `pyodbc.connect` solo aparece en `sql_server_repository.py:91`, dentro de
     `_connect`. Hice grep en `application`, `domain`, `infrastructure`, `interface_adapters`, `config`,
     `function_app.py` y `scripts`. El `pyodbc` de `function_app.py` solo se usa para `except pyodbc.IntegrityError`.
  2. **Los 8 métodos pasan por `_connect`.** `_connect` tiene exactamente 8 llamadas (l. 118, 150, 196, 232, 252,
     286, 322 y 391), una por método público. Son los 8 que parametriza `_METODOS` en `test_f011_repositorio.py`.
     El modo extendido de `sigrid/albaran` lee con `execute_read_query(model_construct(...))`: se salta
     `SqlQueryGuard`, pero no `_connect`.
  3. **La validación va antes de componer la cadena.** `validate_identifier` (l. 80) precede a la cadena y a
     `pyodbc.connect`. Usa `fullmatch` sobre el valor recortado, así que no aplica la trampa de `$` ante un salto
     de línea final. La cadena usa `safe_database`.
  4. **En `run_in_write_transaction` el error no se traga.** El `IdentifierValidationError` salta al entrar en
     `with self._connect(...)`, fuera del `try` de reintentos, y sale tal cual. Está probado en R14.
  5. **Ningún caso de uso convierte el error en un 200.** Los `except Exception` de `create_albaran_compra`,
     `partes_reclamacion` y `concepto_grafico` relanzan o lo traducen a su error. Las seis rutas de dominio y las
     de `sql/*` tienen `except ValueError` → 400 con `type(exc).__name__`. Por tanto una base fuera del patrón da
     400 `IdentifierValidationError` en toda la API. Esto confirma lo que dice el nuevo párrafo de `ARCHITECTURE.md`.
  6. **R15 contra la cadena real de `dev`:** 48/48 idénticas (ver «Lo que se ejecutó»).
  7. **Efecto lateral documentado.** `" ruesma "` ahora conecta como `DATABASE=ruesma;` porque el guardia recorta.
     Lo fija `test_f011_r13_…`. Es inocuo: los modelos ya recortaban, y los consumidores mandan `ruesma` o
     `ruesma_rep` (`azure-apps/sigrid_api.md`; los modelos de dominio usan `ruesma` por defecto).

## Cobertura requisito → test (los F-011 están todos en verde)

| R | Tests |
|---|---|
| R1 | `caso_de_uso::test_f011_r1_*` (×2); `ruta::test_f011_r1_*` (cuerpo exacto; inyección y mayúsculas, ×3) |
| R2 | `caso_de_uso::test_f011_r2_*`, que comprueban que no se llama al repositorio y que no se abre conexión |
| R3 | `caso_de_uso::test_f011_r3_*` (×4 mayúsculas y prefijos; espacios recortados) |
| R4 | `caso_de_uso::test_f011_r4_*`; `ruta::test_f011_r4_*` |
| R5 | `caso_de_uso::test_f011_r5_*` (×6) |
| R6 | `caso_de_uso::test_f011_r6_*` (×5 identificadores, con el adaptador real y la conexión prohibida) |
| R7 | `composicion::test_f011_r7_*` (×2: mismo objeto `Settings`; las bases de escritura y la documental se rechazan) |
| R8 | `caso_de_uso::test_f011_r8_*` (×2); `ruta::test_f011_r8_*` (`!= "ValueError"`; literal también para una subclase) |
| R9 | `ruta::test_f011_r9_el_rechazo_deja_un_warning` |
| R10 | `caso_de_uso::test_f011_r10_*` (×5); `ruta::test_f011_r10_*` |
| R11 | `ruta::test_f011_r11_*` (×5: ValidationError, Identifier, sin binario, 409 y 500) |
| R12 | `test_f010_*` en verde. Los únicos cambios en `test_f010_caso_de_uso.py` son las 2 construcciones; no se tocó ninguna aserción |
| R13 | `repositorio::test_f011_r13_*`; `ruta::test_f011_r14_lista_mal_configurada_*` |
| R14 | `repositorio::test_f011_r14_*` (8 métodos × 8 bases, texto exacto, `cadenas == []`) |
| R15 | `repositorio::test_f011_r15_*` (8 × 3), más la comparación independiente contra `dev` |
| R16 | Documental (fuera de este bloque). El párrafo de `ARCHITECTURE.md` cuadra con el código (puntos 2 y 5) |
| R17 | MANUAL, T12-T14 pendientes |

## Guía de verificación manual (design §Verificación manual)

**¿Es de solo lectura?** Sí. Paso 0: `appsettings list` filtrado a tres claves, sin secretos. Pasos 1-3:
`documents/read`. Paso 4: `sql/read` con un `SELECT`. Paso 5: `contrato-lineas` con `commit:false`, dry-run
autorizado; con A1 se corta en `locate_contract` antes de conectar, y aunque conectara el dry-run solo lee.
T13 (`func publish`) es el despliegue y lo lanza el humano.

**¿Basta para dar la feature por buena en producción?** Sí, con los matices de abajo. El paso 2 demuestra que el
código nuevo está desplegado; los pasos 1 y 4, que `_connect` sigue conectando con una base válida y la credencial
de lectura; el 5, A1 en un endpoint de dominio; y el 0 descarta, antes de desplegar, la caída global por una base
configurada fuera del patrón. La credencial de escritura no se puede comprobar sin escribir: ese hueco lo cubren
R15 en los dos métodos de escritura y mi comparación 48/48 con `dev`. Es aceptable.

## Observaciones (no bloqueantes; recomiendo aplicarlas antes de T14)

1. **El paso 5 no trae cuerpo exacto** («campos de relleno»). En rigor `critico` se pide el comando exacto.
   Propuesta, que pasa el modelo (`AddContractLinesRequest` y `ContractLineInput`):
   `{"database":"ruesma;APP=f011","cod_contrato":"F011-NO-EXISTE","cod_obra":"F011","cif_proveedor":"F011","lines":[{"res":"f011","can":1,"pre":0}],"commit":false}`.
   Esperado: 400, `details.type` `IdentifierValidationError`, texto
   `El identificador 'database' contiene caracteres no permitidos: ruesma;APP=f011`. Si sale 400 `ValueError`
   («No se encontro un contrato…»), es que se conectó y A1 no está desplegado: PARAR.
2. **El paso 5 debe ir explícitamente después de un paso 2 correcto**, igual que el 3. Con el código viejo
   conectaría a `ruesma` con un atributo ODBC inyectado. Sería inocuo, pero no aportaría ninguna evidencia.
3. **Los pasos 2, 3 y 5 esperan 400**, y en PowerShell 5.1 `Invoke-WebRequest` o `Invoke-RestMethod` lanzan una
   excepción y ocultan el cuerpo. Hay que usar el `try/catch` con `StreamReader` de `azure-apps/sigrid_api.md`
   §11 (l. 1427-1435). Sin él no se puede leer `details.type`.
4. **Precisiones al paso 0:**
   - El patrón se aplica a **cada elemento** de las listas JSON.
   - Una `SIGRID_DOCUMENT_WRITE_DATABASE` vacía es «apagado», no un fallo.
   - Sería útil añadir al paso 4 un `sql/read` con `database:"ruesma"` (el ejemplo de §8.1, `dbo.con` con
     `tip = 44`). Es la base que usan todos los endpoints de dominio y la mayoría de consumidores.
   - Si `||` en `--query` da guerra a través de `az.cmd`, se puede consultar clave a clave.

## Propuestas al arnés (las decide el humano)

- Crear `harness/rutas_sensibles.json` con `infrastructure/security/**` e
  `infrastructure/repositories/sql_server_repository.py`. Ya está anotado en `current.md` como pendiente. En esta
  feature, C4 ter ha sido N/A formal pese a tocar el adaptador por el que pasan todas las conexiones.
- `CHECKPOINTS.md` C4, tercer punto: aceptar por escrito que las MANUAL estén «en `current.md` o enlazadas desde
  ahí al design». Es la misma propuesta de F-010, aún sin decidir.
