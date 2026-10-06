<!-- progress/review_F-009_loteB_1.md -->
Revisión completa (pasada 1) del trozo 1 del lote B (T2, T3 y T4), sobre HEAD `53489b3064a3fc4db6a957958664b0bae30da722`

# F-009 · Revisión del lote B, trozo 1 (T2-T4) · **Veredicto: APPROVED**

Alcance: `c7c0b95` (T2), `91f80f6` (T3), `e2d52fb` (T4) y lo suyo de `43eae24` (columna con espacios, CIF no texto). T5-T6 (`f0130ed`, `d936ced`) los revisa otro reviewer; de ellos solo he mirado lo que consume
T4: las claves de E12 cuadran con lo que escriben `numerar`/`construir_ctrprodes`/`construir_mov` (`docdeside` y
`docdestip` 14; `docide` y `doctip` 14). `git diff e2d52fb HEAD` no quita ni cambia ninguna línea de T4 (solo añade).

## Nivel de rigor

`critico` (declarado en `harness/features.json`). Puertas: fase RED en los requisitos centrales, cobertura de lo
cambiado ≥ 80 %, mutación con cero supervivientes y manuales listados. Para este trozo: RED de R1 y R10 (las de R34
que caen en T2-T4); cobertura, sí; **mutación N/A justificada**: es T16 (lote E), sobre la feature entera, como fijó
el plan aprobado por el humano en la PARADA 1; medir ahora mediría un caso de uso que no existe.

## Verificación propia

- `bash harness/init.sh` tal cual: `2110 passed, 1 skipped`; `PUERTA COBERTURA: 100.0% de 517 líneas` (`[OK]`,
  umbral 80 %, `critico`); `PUERTA TAMAÑO` `[OK]`; `ENTORNO LISTO`.
- `pytest tests/test_f009_settings.py tests/test_f009_models.py`: `202 passed`. `pytest tests/test_f009_statements.py
  -k "r31 or sql"`: `56 passed, 102 deselected`. Sin red ni BBDD en los tres ficheros (ni `pyodbc`, ni sockets).
- `ruff check` de los ficheros del trozo: solo los 2 avisos previos de `parse_string_list` (`settings.py:168`, de `dev`).
- No tocados (`git diff dev...HEAD`, vacío): `infrastructure/security/`, `create_purchase_albaran_use_case.py`,
  `create_direct_albaran_use_case.py`, `albaran_domain_models.py`, `albaran_directo_models.py`, `function_app.py`.
  `.env` no versionado. Dorado: `git log dev..HEAD -- tests/fixtures/f009_caracterizacion.json` = solo `783f2d1` y
  `91b929d` (T1). `contrato_albaranes.md` no lo toca ningún commit del trozo.
- Sondas propias: `cantidad=3` → `3.0`; `True`, `"1"`, `NaN` (también el de `json.loads`) → rechazados;
  `{"lineas": None}` → extendido; `cabecera`/`filas.dca` pierden las bancarias; los `warnings` que llegan se ignoran.

## T2 · App Settings (R10)

- Defecto cerrado de las seis (`settings.py:115-132`): `false`, `[]`, `[]`, `[]`, `100`, `{}`. Test que lo fija y
  test que lee los valores de despliegue **por el entorno**.
- `parse_string_dict`: objeto JSON de textos no vacíos o `ValueError` al arrancar (CSV, lista, `[]`, texto suelto,
  valores no texto o vacíos, claves repetidas también tras recortar). `NoDecode` + `object_pairs_hook` con clase
  centinela: verificado que `{"A":"x","A":"y"}` por el entorno no arranca (test `..._en_el_entorno_no_arranca`).
- Aislamiento (lección de F-004): fixture `autouse` que borra del entorno toda clave que `Settings` reconoce, y
  `_env_file=None`. Correcto.
- `local.settings.sample.json`: las seis en JSON, sin secretos (deuda previa en la línea 8: observación 5).

## T3 · Modelos (R1, R5-R7, R9, R14b, R30c)

- R1 por claves, `peticion_mixta` antes de validar; lo que no es `dict` va al clásico. Correcto.
- Contra el contrato §2-§4 (congelado), campo a campo: tipos, obligatoriedad y longitudes de §2.1 y §2.2
  coinciden; `almacen`/`naturaleza` ⇒ 400 sin código (`extra="forbid"`, probado en cabecera y en línea); R6
  completo (dos o ninguno, `cantidad == 0` también `-0.0`, sin vincular sin `descripcion` o con solo espacios,
  `referencia_linea` repetida tras recortar, vinculada sin `cod_contrato`, `paride` sin `partida`); valen
  negativas, contrato sin vinculadas, sin partida, `precio` negativo (lo para el caso de uso) y fecha futura.
- **Códigos cerrados (R9) = §3.3 y §3.2 del contrato**: 18 de cabecera, 10 de línea y 9 avisos, uno a uno, sin
  sobrantes ni faltantes y disjuntos. `AlbaranCompraError` y `FalloLinea` rechazan cualquier otro (decisión 8).
- **Decisión 5 (números estrictos)**: encaja con §2 («números como números JSON, no texto») y con §2.1-§2.2 (`int`
  en `ctrpro_ide`, `paride`, `fecha_albaran`, `empide`; `float` en `cantidad`/`precio`, que siguen admitiendo un
  entero JSON). F-053 R12 no fija tipos JSON más allá del contrato; ver observación 8 para albaranes.
- R7 superconjunto: `LineaResultado(AlbaranLinePreview)` y `AlbaranCompraResponse(AddPurchaseAlbaranResponse)`
  traen todos los campos de §3.1 (cabecera y línea). Decisión 7: `warnings` derivados (cabecera y luego líneas,
  en orden) y `COLUMNAS_BANCARIAS` fuera de `cabecera` y `filas.dca` en el propio validador. He contrastado
  las 15 con el diccionario (`azure-apps/sigrid_tablas.md`, tabla `dca`): son exactamente sus `ban*` y `cpa*`.

## T4 · SQL constante (R31) — revisado con lupa

- Las 40 constantes comparadas carácter a carácter con design §Sentencias: L1, L5 (dos variantes), L6, L7 (sin
  `natide`), L7b, L8, L8b, L9, L10 (`obr` y `alm`), L11 (con `refent`), L12, L13, L14, L15a-c, E2-E7, E9-E11,
  E11b y E12: idénticas. Todas con `?`; ni literales, ni `;`, ni comentarios (test). `MOV_COLUMNAS` y
  `CTRPRODES_COLUMNAS` = las del clásico (comprobado por introspección); `LOG_COLUMNAS` = F-006.
- **Decisión 2 (columnas de E8 desde la plantilla): no abre inyección ni escritura en otra base.** (a) la tabla sale
  de un conjunto cerrado (`con`, `dca`, `dcapro`) con `dbo.` fijo; (b) cada columna pasa
  `IdentifierGuard` (`^[A-Za-z_][A-Za-z0-9_]*$`, solo ASCII: no cabe `]`, `.`, espacio, comilla ni `;`) y se
  rechaza si el guardia tuvo que recortarla (`albaran_compra_statements.py`, `insertar_clonada`); (c) va entre
  corchetes; (d) los valores, siempre `?`, en el orden de las claves; (e) el `INSERT` generado pasa
  `DatabaseReferenceGuard`. Sin puntos ni corchetes internos no hay nombre de tres partes posible. Es **más
  estricto que el clásico** (`create_purchase_albaran_use_case.py:599-602` pone corchetes sin validar). Los nombres
  salen de `SELECT *` de Sigrid y de claves literales de los constructores, nunca de la petición. Lo que protege la
  **base de la conexión** no es este guardia sino R24 (`ALLOWED_WRITE_DATABASES`), que es del lote C.
- Control negativo de R31: una constante con `ruesma_rep.dbo.` impide construir la clase; una generada con
  `msdb.dbo.` se rechaza; tabla fuera del conjunto, columna inyectada (`ide]) VALUES (1); DROP TABLE...`),
  con espacios o vacía, rechazadas; solo los dos `UPDATE` de R25; ningún `INSERT` fijo fuera de `mov`,
  `ctrprodes` y `log`; ni `dcapropar`, `dcaproana` ni `pro`.
- Decisión 3 (L10 sin almacenes resueltos ⇒ solo `WHERE obride = ?`): correcta; las demás listas `IN` vacías dan
  `ValueError` en vez de SQL inválido. Decisión 4 (claves de E12): coherentes con R28 y con las filas que escribe T6.

## Checkpoints

Fuera de este trozo, con motivo: **C3 bis** N/A (no toca `docs/referencia/`); **C4 ter** N/A (no existe
`harness/rutas_sensibles.json`); **C5** y la parte de C4 de manuales, N/A en una revisión parcial (se evalúan al
cerrar la feature; T5-T25 son de otros trozos/lotes). Mutación: N/A justificada arriba (T16).

- C1: [x] `init.sh` exit 0 · [x] ficheros del arnés.
- C2: [x] una sola `in_progress` (F-009) · [x] rama `feature/F-009-alta-albaran-compra` · [x] `history.md` (sin
  `done` nuevas) · `current.md`: N/A para este trozo (lo lleva el líder; ver observación 6).
- C3: [x] hexagonal (dominio sin infraestructura; `application` importa los guardias como ya hace
  `concepto_grafico_statements.py`) · [x] primera línea con ruta en los seis ficheros · [x] sin `print`, TODO ni
  secretos, sin dependencias nuevas · [x] base correcta (nada nombra `ruesma_rep`) · [x] `cod/res/fec/tip/est` en
  `con` (L1, L5, L11, E2, E12 por `JOIN dbo.con`) · [x] nada se recalcula solo (E9-E11 previstas) · [x] estado por
  `dbo.conest` (L13) · [x] SQL con `?`.
- C4: [x] tests trazables `test_f009_r1/r5/r6/r7/r9/r10/r25/r26/r28/r31_*` y `_sql_*`, en verde · [x] sin red ni BBDD.
- C4 bis: [x] `rigor` declarado (`critico`) · [x] fase RED con salida real de R10 (`54 failed, 1 passed`,
  `AttributeError`/`DID NOT RAISE`) y de R1 (`ModuleNotFoundError` en la recogida) en `impl_F-009_loteB.md` · [x]
  cobertura `[OK]` 100 % · mutación, RM1-RM6 y campaña manual: N/A en este trozo (T16, ver arriba) · [x] sección
  «Evidencias» con los cuatro números (mutación declarada «no medido en este lote» con su motivo).

## Cobertura requisito → test (este trozo)

| Req. | Tests |
|---|---|
| R1 | `test_f009_r1_con_lineas_o_referencia_externa_es_extendido`, `_sin_ninguna_...`, `_lo_que_no_es_un_objeto_...`, `_peticion_mixta` |
| R5 | `test_f009_r5_*` (CIF, recortes, longitudes, obligatorios, rango de fecha, `almacen`/`naturaleza`) |
| R6, R14b, R30c | `test_f009_r6_linea_invalida_es_400_sin_codigo`, `_lo_que_vale`, `_referencia_linea_repetida`, `_vinculada_sin_cod_contrato` |
| R7 | `test_f009_r7_*` (superconjunto, `warnings` derivados, bancarias, idempotente mínima) |
| R9 | `test_f009_r9_*` (códigos cerrados = design = contrato, `lineas` solo con `lineas_no_validas`) |
| R10 | `test_f009_r10_*` (57 casos: defectos, despliegue por entorno, mapeo, fichero de ejemplo, existentes) |
| R31 | `test_f009_r31_*` y `test_f009_sql_*` (carácter a carácter, guardia, control negativo) |

**Cambios requeridos: ninguno.**

## Observaciones (no bloquean; para el líder y lotes siguientes)

1. **`commit` admite texto** (`albaran_compra_models.py:271`): `"yes"`, `"true"` o `1` dan `True` (modo laxo), igual
   que en el clásico. No diverge del contrato, pero choca con el espíritu de la decisión 5 en el campo más
   sensible. Propuesta: `strict=True` en `commit` (cambio de una línea y un test), a decidir por el humano.
2. **`fecha_albaran` 20261399 pasa** (design y T3: «solo en rango»; el clásico igual). Se escribiría en `con.fec`.
   El contrato dice «formato y rango»; F-053 la saca de una fecha real, así que el riesgo es bajo. A decidir.
3. **Lote C**: `contrato` de la respuesta no lo filtra el modelo (solo `cabecera` y `filas.dca`, como pide el
   design): debe ser el resumen del clásico (`ctride`, `obride`…), nunca la fila `ctr` (lleva `banban`, `bansuc`,
   `bantipide`). El modelo deriva `warnings` solo al construirse: no mutar `lineas` después.
4. **Lote D (T13)**: `AlbaranCompraError` hereda de `ValueError`; el `except` que lo traduce a `details.codigo`
   tiene que ir **antes** de los `except ValueError` existentes, o saldría como 400 sin código.
5. **Deuda previa**, no de este trozo: `local.settings.sample.json:8` lleva una IP interna desde `e903394` (primer
   commit), contra la regla transversal de CLAUDE.md. Propongo ficha aparte (no se borra del historial).
6. Fichero vacío sin trackear en la raíz, `` `0`].{t `` (24-sep, anterior a F-009): que el humano lo borre.
   Y `progress/current.md` arrastra el estado de la v7 («ya superado»): limpiarlo al cerrar el lote.
7. **Para albaranes (F-053)**: con la decisión 5, un `precio` serializado como texto (p. ej. un `Decimal` como
   cadena) o un `empide` leído de entorno sin convertir a entero dan 400 sin código (`error`). Lo dice ya §2 del
   contrato; conviene que sus tests de sv9 fijen que manda números JSON.
8. `SIGRID_ALBARAN_MAX_LINEAS` no tiene `ge=1`: 0 o negativo cierran el modo (`demasiadas_lineas`), así que es
   seguro; solo se anota.

**Automejora (propuesta, no aplicada):** nota en `CHECKPOINTS.md` para revisiones parciales por lotes: qué bloques
se evalúan en cada trozo (C1, C3, C4, RED) y cuáles se difieren al cierre (C5, manuales, mutación).
