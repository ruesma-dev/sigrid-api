<!-- progress/review_F-015_C3C4ter.md -->
Revisión completa (pasada 1), bloques C3, C3 bis y C4 ter, sobre `git diff dev` en HEAD `e42e0ad`

# Review F-015 · C3, C3 bis y C4 ter (troceada)

- **Veredicto:** CAMBIOS (CHANGES_REQUESTED). Tres hallazgos, los tres de **documentación**; el código de
  escritura no cambia y ninguno toca la seguridad.
- **Rigor:** `critico` (declarado en `features.json`). RED, cobertura y mutación son C4 bis, otro encargo.
- **Alcance:** solo estos bloques. Sin `init.sh` ni suite completa (lo pide el encargo). Nada contra Sigrid.
- **Tests ejecutados:** `pytest tests/test_f015_statements.py tests/test_f015_use_case.py
  tests/test_f009_statements.py tests/test_f009_route.py -k "r24 or r19 or r31 or r8 or r1_insert or r10
  or r14 or r16 or r5_"` → **111 passed**, 271 deselected, 4,0 s.

## C3 — Arquitectura y convenciones

- [x] **Hexagonal.** `domain/models/albaran_compra_models.py` solo suma códigos a `CODIGOS_CABECERA` y
  `CODIGOS_AVISO`, sin importar infraestructura. Lo nuevo vive en `application/` y lee por `read_full_row`
  del puerto con tablas literales (`dca`, `prv`, `auxpag`, `auxefp`). `infrastructure/` no cambia. El
  import de `infrastructure.security` en `albaran_compra_statements` ya estaba en `dev` (F-009).
- [x] **Primera línea con ruta** en los 13 `.py` del diff.
- [x] **Sin `print`, TODO, FIXME ni `breakpoint`** en lo añadido; sin secretos (barrido en C3 bis); sin
  dependencias nuevas (`requirements*`, `pyproject`, `config/` y `.env*` fuera del diff).
- [x] **Sin duplicar.** Reutiliza `CON_COLUMNAS` y `fecha_ole_utc` (F-006), `redondear_euros`,
  `_insertar_fija`, `_insert_fijo` y `sin_columnas_bancarias`; retira `_TOTALES_DCA`. `resolver_cascada`
  corre dos veces (aviso y construcción), pero es pura: se acepta.
- [x] **Tamaño de funciones** (observación; `CONVENTIONS.md` no pone límite). Crecen poco las que ya eran
  grandes en F-009: `_escribir` 127→134, `_construir` 114→128, `work` 85→92. Las nuevas son cortas salvo
  `resolver_cascada` (70) y `construir_dca` (57).
- [x] **Comentarios en español**, sin tildes, como el resto del módulo. Excepción de exactitud: H1.
- [x] **Reglas de dominio de Sigrid:**
  - [x] **Base correcta**: todo a `request.database`, contra `allowed_write_databases` y
    `DatabaseReferenceGuard(contexto="escritura")`; `ruesma_rep` no se toca.
  - [x] **`cod`, `res`, `fec`, `tip` y `est` en `con`** (`construir_con`); `DCA_COLUMNAS` no lleva ninguno.
  - [x] **Nada se recalcula solo**: la `dcarec` va con `dca.tot` = `totpag` = `totdoc` − `cuo` en la misma
    transacción; `canser`, `estser/estfac` y `mov` siguen como en F-009.
  - [x] **Estados sin hardcodear**: no hay estados nuevos; `est` 1 se sigue resolviendo en `conest` (L13A).
  - [x] **SQL con `?`**: L16 trae pocas filas y va con `muchas=True`; truncar sigue siendo error.

## C3 bis — Documentos que entran de fuera

- [x] N/A cabecera con origen y fecha: el diff no toca `docs/referencia/` (`git diff dev --stat` vacío).
- [x] N/A originales PDF u ofimática: `git log --diff-filter=A dev..HEAD` solo añade 10 ficheros `.md` y
  `.py` (specs, progress y dos tests).
- [x] **Barrido de datos sensibles, hecho por el reviewer** sobre lo añadido en todo el diff y en el commit
  `49dfb36` de azure-apps. Patrones: correo, IPv4, GUID `8-4-4-4-12`, `password|pwd|secret|apikey|
  x-functions-key|AccountKey|SharedAccessSignature` seguidos de `=` o `:`, JWT `eyJ…`, base64 de 40+
  caracteres, forma de NIF/CIF y razones sociales (`S.L.`, `S.A.`, `SLU`). Resultado: dos SHA de git en
  `mutacion_F-015.md` y los CIF ficticios `B12345678` (×13) y `B00000000` (×2) de los tests. **Ningún dato
  real.**
- [x] N/A redacciones en cabecera: no hay documento externo, así que nada redactado.

## C4 ter — Rutas sensibles

- [x] N/A los cuatro checkboxes: no existe `harness/rutas_sensibles.json` (solo el `.ejemplo.json`), y sin
  esa declaración `CHECKPOINTS.md` deja el bloque en N/A.
- **Verificaciones extra del encargo** (escritura en producción), hechas leyendo el código:
  - [x] **SQL nuevo constante con `?`, sin valores interpolados**: L5 (las dos), L11 (+ `tot`), L16, L17,
    E6b, E12_DCAREC y los `INSERT` de `con`, `dca` y `dcarec`. Único literal: el `''` de
    `ISNULL(d.entref, '')`, constante de la spec; `AC__/%` y `PROF%` van como parámetro.
  - [x] **Identificadores de listas fijas**: `_insert_fijo` con `CON_COLUMNAS`, `DCA_COLUMNAS` y
    `DCAREC_COLUMNAS`; tablas literales en `read_full_row`, que además pasan `IdentifierGuard`.
    `_TABLAS_CLONADAS` = `{"dcapro"}`; `insertar_clonada` rechaza `con` y `dca`
    (`test_f015_r24_solo_dcapro_se_clona`).
  - [x] **`DatabaseReferenceGuard`**: las sentencias nuevas están en `todas_las_sentencias()` y se validan
    en `__init__` (`test_f015_r24_las_sentencias_nuevas_estan_validadas`).
  - [x] **Control negativo**: 47 sentencias; solo E9 y E11 son `UPDATE`; sin `DELETE`, `MERGE`, DDL,
    `EXEC`, `;` ni otros literales (`test_f015_r24_control_negativo_…`, en verde).
  - [x] **`infrastructure/security/` sin cambios** (`git diff dev --stat` vacío).
  - [x] **Mismas guardas del commit**: `_exigir_escritura_de_albaranes` en la ruta (`function_app.py:268`)
    y `_comprobar_guardas` (`create_albaran_compra_use_case.py:330-344`) con las dos llaves, credenciales
    y `allowed_write_databases`, antes de cualquier lectura. Tests R8 y R31 en verde.
  - [x] **Sin datos sensibles en trazas ni respuestas**:
    - la traza solo añade `n_retenciones` (R19, en verde); los errores se trazan por tipo o código, no por
      mensaje (`_respuesta_albaran_compra_error`);
    - los mensajes nuevos citan columnas, `ide`, recuentos y el `cod` del recargo (`RET5`): ni `entres`,
      ni `raz`, ni CIF, ni `nomori` (es de `gra`; F-015 no lo usa);
    - la respuesta sigue sin `COLUMNAS_BANCARIAS` (`ban*`, `banide`, `cpa*`); `bas` y `cuo` solo en el
      aviso, como pide R16;
    - observación: `retencion_no_soportada` cita el `valfij` del contrato, un importe de negocio y no
      personal, en la respuesta y no en la traza. Se acepta.
  - [ ] **azure-apps `sigrid_api.md`** (`49dfb36`, solo local en `master`): cubre §7.5 (applocks), la
    tabla de qué recalcula, §8.6, §8.7 y §13, todo con «PENDIENTE DE DESPLIEGUE». Imprecisión: **H3**.
  - [ ] **`contrato_albaranes.md` v8.3**: casan los 3 códigos nuevos (`proveedor_sin_albaran_previo`
    retirado de dominio y código), los avisos `cabecera_sin_dato` (pago, o banco con efecto CC, CT o TR) y
    `retencion_del_contrato`, `totales` (`tot`, `retenciones`, `n_retenciones` en previa y creado; `tot` y
    `retenciones` en idempotente), `filas.dcarec`, `template_ide` (respaldo o 0) y el applock `_dcarec`.
    Discrepancia de orden en §4.1: **H2**.

## Cobertura (lo que toca a este trozo)

| Requisito | Test que lo cubre (ejecutado) |
|---|---|
| R1 (`INSERT` fijos) | `test_f015_r1_insert_de_con_con_sus_19_columnas_fijas`, `…_dca_con_sus_145…`, `…_una_fila_de_cabecera_que_no_cuadra…` |
| R10 | `test_f015_r10_*` (statements y use case) |
| R14 y R16 | `test_f015_r14_*`, `test_f015_r16_*` |
| R19 | `test_f015_r19_la_traza_*` (3) |
| R24 | `test_f015_r24_*` (4) + `test_f009_r31_*` |
| F-009 R8 (llave) | `test_f009_r8_*` (5) |

## Cambios requeridos

1. **H1 · Docstring del módulo desactualizado** (`application/use_cases/albaran_compra_statements.py:13-17`).
   Dice que las sentencias son las de F-009 §Sentencias «en su v8.1» y que «`con`, `dca` y `dcapro` se
   CLONAN de su plantilla (`SELECT *`)». Desde F-015 es al revés: `con` y `dca` van por lista blanca con
   columnas fijas, solo `dcapro` se clona, y hay sentencias nuevas (L16, L17, E6b, E12_DCAREC). Arreglo:
   reescribir esas líneas citando `CON_COLUMNAS`, `DCA_COLUMNAS`, `DCAREC_COLUMNAS` y `_TABLAS_CLONADAS =
   {"dcapro"}`. Es el módulo que fija el SQL de una escritura en producción y su cabecera dice lo contrario.
2. **H2 · `contrato_albaranes.md` §4.1, paso 2** (`specs/F-009-alta-albaran-compra/contrato_albaranes.md:401-403`).
   Pone «contrato … o, sin contrato, el proveedor por CIF (v8.3) → albarán anterior opcional». El código
   (`create_albaran_compra_use_case.py:393-413`), el design §Flujo (l. 137) y R7 hacen lo contrario: sin
   contrato, **primero el albarán anterior por CIF** (L5) y L17 solo si no lo hay; con respaldo nunca hay
   `proveedor_ambiguo`. El §3.3 del contrato ya lo dice bien. Arreglo: «contrato → albarán anterior (por
   `entide` con contrato, por CIF sin él; opcional) → sin contrato ni albarán anterior, el proveedor por
   CIF (L17)». Es redacción de la v8.3, sin cambio de forma ni de códigos: no hace falta un nuevo acuse;
   anotarlo en la línea de la v8.3.
3. **H3 · azure-apps `sigrid_api.md` §8.6** (`azure-apps/sigrid_api.md:1088-1091`, commit `49dfb36`):
   - (a) pone `ivadif` en la cascada contrato → albarán anterior → proveedor, pero sale del contrato
     **aunque sea 0** y, sin contrato, del albarán anterior; nunca del `prv`
     (`albaran_compra_statements.py:515-520`, R3, D5);
   - (b) «Sin fuente, … el aviso `cabecera_sin_dato`» sugiere que avisa por cualquier columna de la
     cascada. Solo avisa por el **grupo pago**, o por el **banco** con efecto CC, CT o TR
     (`create_albaran_compra_use_case.py:466-478`, R5); sin `cueide`, `eioide`, `dirdir1` o `dircon1` se
     escribe vacío y no hay aviso.

   Arreglo: un commit local más en azure-apps que lo deje como el contrato v8.3 §3.2.

## Observaciones (no bloquean)

- Las constantes pasan a `L5_RESPALDO_*`, pero los métodos siguen siendo `leer_plantilla_cabecera*`.
  `template_ide` se mantiene porque es del contrato; los métodos podrían renombrarse más adelante.
- `_escribir` y `_construir` siguen creciendo: conviene trocearlos la próxima vez que se toque el modo
  extendido.

## Automejora (propuesta, no aplicada)

- `CHECKPOINTS.md` C3: añadir «los docstrings de cabecera de los módulos tocados siguen describiendo lo que
  hacen». Ninguna casilla actual habría cazado H1.
