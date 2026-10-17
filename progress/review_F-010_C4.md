<!-- progress/review_F-010_C4.md -->
Revisión completa (pasada 1) de `dev..c3d4e45` (HEAD `c3d4e45ad221f227517646e41db8ceb8b6bc9881`), acotada a C4, C4 bis (solo FASE RED y COBERTURA) y C4 ter

# Review F-010 · bloque C4 / C4 bis (RED y cobertura) / C4 ter

**Veredicto del bloque: APROBADO.** Sin cambios requeridos; cuatro observaciones no bloqueantes al final.

**Nivel de rigor:** `critico`, declarado en `harness/features.json` (F-010). Exige fase RED en los requisitos
centrales, cobertura de las líneas cambiadas ≥ 80 % (`harness/rigor.json`, `umbral_lineas_cambiadas: 80`),
mutación con cero supervivientes (fuera de este encargo: la revisa otro) y manuales con su comando exacto.

**Lo que NO se ejecutó, por orden del encargo:** ni `bash harness/init.sh` ni la suite completa (corren en
paralelo otras revisiones y una campaña de mutación). Se ejecutaron solo los cinco ficheros `tests/test_f010_*.py`
y `-k test_f009_t13_las_demas_rutas_desempaquetan_la_tupla_de_ocho`. El verde completo de la suite (R17, C1) lo
valida la revisión que corre `init.sh`.

## C4 — La verificación es real

- [x] **Cada requisito tiene ≥ 1 test trazable y pasa.** 157 tests `test_f010_r<N>_*`, todos con prefijo de
  requisito; `157 passed in 1.70s` en mi ejecución. Tabla abajo. R16, R17 y R18 no tienen test unitario por
  diseño (justificado en la tabla).
- [x] **Los unit tests no tocan red ni BBDD.** `test_f010_repositorio.py:62-67` sustituye `pyodbc.connect` por una
  función que lanza `AssertionError` y dobla `_connect` con cursor falso; `test_f010_ruta.py:46-49` dobla
  `build_dependencies`; caso de uso con repositorio doble; modelo y cabecera son puros. `grep` de
  `requests|httpx|socket|urlopen|get_settings|.env` en los cinco ficheros: sin coincidencias.
- [x] **Manuales listados, pendientes y con comando exacto.** `tasks.md` T13-T15 en `[ ]` y marcadas
  «MANUAL (humano)»; `progress/current.md` (entrada F-010 implementada) las da como «Quedan» y remite a
  `design.md` §Verificación manual (líneas 216-240), donde están los comandos PowerShell exactos, todos de solo
  lectura (`sql/read`, `documents/read`); T14 trae su `func azure functionapp publish ...` en `tasks.md` y en
  `impl_F-010.md` §Pendiente. Ninguna se presenta como hecha. Ver observación 1.

### Cobertura requisito → test (leídos, no solo contados)

| R | Tests que lo prueban de verdad |
|---|---|
| R1 | `cabecera.py`: `r1_la_cabecera_es_ascii_imprimible` (ñ, á, emoji, CJK, `%`, 0x1F, 0x7F), `r1_cada_control_y_del_viajan_codificados` (0x00-0x1F y 0x7F, valor exacto), `r1_el_primer_caracter_no_ascii...` (0x80) |
| R2 | `r2_unquote_devuelve_el_nombre_original` (`errors="strict"`), `r2_el_porcentaje_literal_viaja_como_25` (`a%20b` → `a%2520b`), `r2_los_no_ascii_viajan_en_utf8` |
| R3 | `r3_nombre_ascii_sin_porcentaje_viaja_identico` (los dos ejemplos obligatorios), `r3_todo_el_ascii_imprimible_salvo_porcentaje...`, `r3_la_funcion_publica...` |
| R4 | `r4_content_disposition_sin_barra_es_la_de_hoy` (attachment/inline × nombres, contra `quote(nombre)`), `r4_la_barra_viaja_como_2f`, `r4_tamano_cuerpo_y_tipo_no_cambian` |
| R5 | `ruta.py`: `r5_nombre_no_ascii_responde_200_con_cabeceras_exactas` (los dos valores exactos de la spec), `r5_inline_se_respeta` |
| R6 | `modelo.py`: `r6_key_con_entero_y_texto...`, `r6_los_nombres_se_recortan...`, `r6_sin_coercion...` (`"123"` sigue texto), `r6_valor_de_tipo_no_admitido...` (null, bool, 1.5, 1.0, lista, objeto), `r6_key_que_no_es_objeto...` |
| R7 | `modelo.py` `r7_key_con_id_column/id_value/id_value_null/las_dos` (con texto); `ruta.py` `r7_r8_localizacion_invalida_da_400_validation_error` (400, `Solicitud invalida.`, `ValidationError`, y `caso.peticiones == []`: sin consultar) |
| R8 | `modelo.py` `r8_sin_key_ni_id_column`, `r8_id_column_sin_id_value`, `r8_id_value_sin_id_column`, `r8_id_column_con_id_value_null_se_sigue_aceptando`, frontera `min_length`; `ruta.py` casos R8 |
| R9 | `modelo.py` `r9_cuatro_entradas_pasan` / `r9_cinco_entradas_no` (frontera), vacío, nombre en blanco, duplicados por `casefold` (incl. `ß`/`SS`), mensajes; `r7_r9_los_errores_se_serializan_a_json` (el 500 latente de la desviación 1) |
| R10 | `repositorio.py` `r10_nombre_de_key_no_valido_se_rechaza` (field `'key'`), `r10_nombre_no_valido_no_abre_conexion` (`conexiones == []`), `r10_orden_de_validacion...`; `ruta.py` `r10_identificador_no_valido_da_400_con_su_tipo` |
| R11 | `repositorio.py` SQL exacto con `TOP (2)` y `AND` en orden (2 y 4 columnas), una columna, `r11_ningun_valor_aparece_en_el_texto_del_sql` (cadena maliciosa y entero), parámetros posicionales `(1, "ABC")`, credencial de lectura |
| R12 | `caso_de_uso.py` `r12_id_column_llega_como_key_de_una_columna` (kwargs exactos), `r12_key_llega_tal_cual...`; `modelo.py` `r12_localizacion_*`; `ruta.py` `r12_la_peticion_por_key...`, `r12_error_inesperado_sigue_en_500` |
| R13 | `repositorio.py` `r13_dos_filas_por_key_es_ambiguo` y `r13_dos_filas_por_una_columna_tambien` (texto exacto de la spec), `r13_la_ambiguedad_es_un_valueerror_de_otro_tipo`; `ruta.py` `r13_ambiguedad_da_409...` (cuerpo exacto) y `r13_el_tipo_nunca_es_value_error` |
| R14 | `repositorio.py` 0 filas y BLOB `NULL` con una y dos columnas, textos exactos (`ide=365617` como hoy) y `type(...) is ValueError`; `ruta.py` `r14_sin_fila_o_blob_vacio_sigue_en_400_value_error` |
| R15 | `caso_de_uso.py` `document_365617.pdf`, `document_1_ABC.pdf`, `document_None.bin`, saneado, candidato vacío, con candidato |
| R16 | Sin test por diseño (spec: «revisión del reviewer, commit aparte»). Compruebo solo que existe `azure-apps` `0c4cbeb` y que trata key, 409, `unquote` y `filename*`; el contenido lo juzga el bloque de documentación |
| R17 | Sin test propio por diseño (es la suite). `git diff dev..HEAD --stat -- tests`: solo 5 ficheros NUEVOS, ninguna aserción previa tocada; `test_f009_t13_...`: `4 passed`. Suite completa: la valida quien corre `init.sh` |
| R18 | MANUAL (humano), post-despliegue: T15, pendiente. Correcto que no tenga test |

## C4 bis — solo FASE RED y COBERTURA

- [x] Nivel declarado: `critico` (`harness/features.json`).
- [x] **Fase RED con traza real, reproducida.** `impl_F-010.md` §Fase RED pega la salida real de T1, T3, T5, T7 y
  T8, más una RED de comportamiento de R13 (cursor de dos filas sobre el adaptador previo). La reproduje entera,
  extrayendo con `git archive` cada árbol previo al código en mi scratchpad (árbol de trabajo intacto):

  | Tarea | Árbol y test | Informe | Reproducido |
  |---|---|---|---|
  | T1 | `b86a4c8`, `test_f010_cabecera.py` | 14 failed, 41 passed | **14 failed, 41 passed** |
  | T3 | `de5f29e`, `test_f010_modelo.py` | 16 failed, 24 passed (`Field required` id_column/id_value) | **16 failed, 24 passed**, mismo error |
  | T5 | `e29a3cf`, `test_f010_repositorio.py` | 23 failed (3 `AttributeError`/`TypeError`) | **23 failed**: 11 `build_document_query`, 9 `key`, 3 `DocumentoAmbiguoError` |
  | T7 | `605ff32` + test de `c5cced5` | 9 failed, `no attribute 'id_value'` | **9 failed**, mismo error |
  | T8 | `fd06b96` + test de `5575ff4` | 1 failed, 14 passed, `assert 400 == 409` | **1 failed, 14 passed**, `assert 400 == 409` |

  **Las trazas corresponden a los tests actuales:** `git diff <commit RED> HEAD` en cabecera y repositorio solo
  trae cambios cosméticos (`range(0x00, 0x20)` → `range(0x20)`, import de `Iterator`, `_esperados`). En modelo se
  añadieron después 62 líneas: el test de serialización (RED en T8, `TypeError ... not JSON serializable`), la
  frontera `min_length` (medida con el mutante aplicado, según el informe) y los nulos explícitos (`bef6a25`,
  cobertura de los `return None`). Ver observación 2.
- [x] **Cobertura de líneas cambiadas, verificada de forma independiente.** Declarado: `PUERTA COBERTURA: 100.0% de
  80 líneas cambiadas cubiertas (80/80, umbral 80%, nivel critico)`. El umbral 80 cuadra con `harness/rigor.json`.
  Lo reproduje con `coverage` (datos en el scratchpad, `COVERAGE_FILE` fuera del repo) ejecutando SOLO los 157
  tests de F-010 y pasando el JSON a `python -m harness.cobertura --cov <scratchpad>`: **la misma línea, 100.0 %,
  80/80**. Es decir, los tests nuevos cubren por sí solos todo lo cambiado, sin apoyarse en la suite previa.
- Mutación, RM1-RM6, coste por mutante, Evidencias de mutación: **fuera de este encargo** (los revisa otro).

## C4 ter — Rutas sensibles

- **N/A justificado:** no existe `harness/rutas_sensibles.json` en el repositorio (ni en su historial); sin esa
  declaración, CHECKPOINTS.md dice textualmente que el bloque «es N/A y no hay nada que justificar», y la
  sección 7 ter de `init.sh` (líneas 498-518) solo actúa si el fichero existe. No hay informe declarado que exigir.
- Aun así, por tratarse del adaptador que compone SQL dinámico con identificadores del cliente, comprobé a mano lo
  que una verificación de ruta sensible pediría:
  - [x] Cada identificador (schema, table, **cada nombre de `key`**, blob, filename_columns) pasa por
    `IdentifierGuard.validate_identifier` antes de componer (`sql_server_repository.py:16-54`); la regex es
    `^[A-Za-z_][A-Za-z0-9_]*$`, así que `]` no puede cerrar el corchete. Test: `r10_*`.
  - [x] Los valores solo viajan como `?` (`sql_server_repository.py:390`, `cursor.execute(query, *parameters)`);
    test con cadena maliciosa (`r11_ningun_valor_aparece...`).
  - [x] La ambigüedad no sirve binario (`:397`) y la ruta la traduce a 409 antes del `except ValueError`
    (`function_app.py:474`).
  - [x] `infrastructure/security`, `config` y `scripts` sin tocar: `git diff dev..HEAD --stat` vacío.
  - Hueco conocido y fuera de alcance por decisión del humano (D6): `database` no se valida contra
    `ALLOWED_DATABASES` y se interpola en `_connect`. No es de esta feature.

## Observaciones (no bloquean)

1. `progress/current.md` no copia los comandos de T13-T15, remite a `design.md` §Verificación manual. Se acepta
   como en revisiones anteriores (F-009 lote B), pero el checkbox de C4 pide «con su comando exacto» en
   `current.md`: ver propuesta.
2. T7 y T8 commitearon test y código juntos (`c5cced5`, `5575ff4`); su RED no se puede sacar del historial tal
   cual, solo combinando el test del commit con el árbol padre, que es lo que hice y cuadra. T1, T3 y T5 sí
   tienen commit RED propio.
3. `read_document_use_case.py:40`: la reserva de segundo nivel (`or f"document_{etiqueta}"`) no se sanea. Es
   comportamiento de antes (con `id_value`) y R15 pide «como hoy», pero con `key` de texto (`cod` con `/`) un
   candidato que quede vacío al sanear devolvería `document_1_a/b`. No llega desde el adaptador real (recorta y
   descarta vacíos) y las cabeceras ya lo codifican (`%2F`). Para una feature futura, no para esta.
4. Varios tests de rechazo de `modelo.py` (`rechaza(...)` sin mirar el mensaje) pasaban ya en RED «por el motivo
   equivocado» (falta de `id_column`), como reconoce el informe. En verde discriminan, porque quitar cada guarda
   haría aceptar la petición; lo respalda la campaña de mutación, que revisa otro.

## Propuesta de automejora (no aplicada; para el humano)

- `CHECKPOINTS.md` C4, tercer punto: aceptar explícitamente «en `progress/current.md`, o enlazados desde ahí a la
  sección del `design.md` que los trae literalmente», que es lo que se viene haciendo y evita copiar comandos en
  dos sitios.
- Valorar declarar en `harness/rutas_sensibles.json` `infrastructure/security/**` y
  `infrastructure/repositories/sql_server_repository.py` (SQL dinámico con identificadores del cliente), con una
  verificación de tipo «pruebas de inyección de identificadores y valores» que hoy solo existe por disciplina.

## Rastro

Árboles extraídos y datos de cobertura en el scratchpad de la sesión (`.../scratchpad/red/`, `cov_f010.json`).
`git status --short` al terminar igual que al empezar (`.claude/worktrees/` y `` `0`].{t `` ya estaban, no son míos).
