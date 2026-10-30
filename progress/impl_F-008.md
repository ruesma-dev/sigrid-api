<!-- progress/impl_F-008.md -->
# F-008 · Informe del implementer (T0-T20 y correcciones de la revisión T21)

Spec v3.1 (`specs/F-008-registrar-factura/`), rigor `critico`. Rama `feature/F-008-registrar-factura`.

## T0 · Esquema medido (solo `sys.columns` y agregados por `sql/read`, 2026-10-30)

Ninguna columna es `IDENTITY`: todos los `ide` se reservan con `MAX + 1` bajo applock. Nulables: todas salvo `ide` (y
`docide`/`docproide` en las hijas). Tipos de texto `text` (`tex`, `pagtex`, `pagfor`, `dir*`, `detinm`...) aceptan `NULL`.

| Tabla | Cols | Lista blanca y vacíos fijados (lo no citado: 0 en numéricas, `''` en `varchar`) |
|---|---|---|
| `con` | 19 | `CON_COLUMNAS` de F-006; `tip` 15 o 25, `tex` NULL (`con` 25: NULL en 11 de 11) |
| `dcf` | 145 | **Idénticas a `dca`** (mismo orden): `DCA_COLUMNAS` de F-009. `tipgar` -1 (10.857 de 11.408), `emptex` NULL, `cla` 1001 |
| `dcfpro` | 73 | lista propia `DCFPRO_COLUMNAS`; `texcom`, `desesp`, `serdesdat`, `med` NULL (35 de 35 en REC/COM); `tex`, `pac`, `ico`, `refent` `''` |
| `dcfrec` | 21 | **Idénticas a `dcarec`**: `DCAREC_COLUMNAS`; `pos` 64, `tex` `''` |
| `pag` | 46 | lista propia; `remide`, `fecrea`, `blo*`, `natide`, `pun`, divisa 0; `cypref`, `retref`, `blores`, `cpa*` `''` |
| `consii` | 50 | lista propia; `pos` 64, A0/F1/01, `emiter`/`facsimcua`/`facsinide`/`difplaenv` N, resto `''`/0, `detinm` NULL |
| `dcaprodes` | 7 | `ide`, `docproide`, `can`, `docdestip` 15, `docdescod`, `docdeside`, `lindeside` |
| `log` | 14 | `LOG_COLUMNAS` de F-006; alta de factura: `ope 1`, `tab con`, `tip 15`, `est 1`, `ori 0` (medido) |

Identificación medida para las lecturas: IVA = `con.tip 23` por (`emp`, `cod`) con `iva.iva` (tasa) e `iva.sopded` (0 en
los NDED); cuenta = `con.tip 17` + `cua.niv`; analítica = `con.tip 19` + `caa`, hoja = sin `caa.padide` que la apunte (0
analíticas con hijas en 8.634 líneas FRGG26); obra `tip 42`; `conest` 14: CON 3, FAC 10; 15: REC 1, RECGG 20; 25: PDT 1.

## Ficheros tocados (diff `0dcfcee..HEAD`; un commit por tarea salvo T9-T10 y T12-T14, ver desviación 7)

| Fichero | Qué |
|---|---|
| `config/settings.py`, `local.settings.sample.json` | siete ajustes `SIGRID_FACTURA_*`; la llave `SIGRID_FACTURA_WRITE_ENABLED` **apagada** por defecto (T1) |
| `domain/models/factura_models.py` | `FacturaRequest` estricta, `FacturaError` con `codigo`/`details`, `FacturaResultado` (T2) |
| `application/use_cases/factura_lineas.py` | puro: línea de origen copiada, a origen (M63), resolvedores FR y FRGG, vencimientos (T3-T7) |
| `application/use_cases/factura_statements.py` | listas blancas, constructores de filas, numeración y las 53 constantes SQL con `?` (T8-T14) |
| `application/use_cases/create_factura_use_case.py` | caso de uso: previa, transacción reentrante, marcas, relectura, traza (T11-T14) |
| `function_app.py` | ruta `sigrid/factura`, llave propia, 400 sin eco (T16) |
| `tests/f008_dobles.py` + 8 `tests/test_f008_*.py` | ERP doble y 418 tests de F-008 (7 de la ronda T21) |
| `docs/ARCHITECTURE.md`, `CLAUDE.md` | ruta y sección F-008 (T18) |
| `azure-apps/sigrid_api.md` | commit `a2127a6` **en ese repositorio**, solo ese fichero (T18) |
| `specs/F-008-registrar-factura/verificacion_manual.md` | pasos de T22-T24 (T19) |
| `progress/mutacion_F-008.md` | campaña entera y los 101 análisis (T20) |

Sin tocar: `infrastructure/security/`, `.env`, `infra/`, App Settings y el código de F-007/F-009/F-016 (solo se
importa). Tests existentes sin cambios: en T17, el diff de las suites ajenas es vacío y dieron 1737 passed.

## Decisiones de diseño

- **La idempotencia va antes que los orígenes.** Si no, repetir una factura ya grabada encontraría sus orígenes
  facturados por ella misma y daría `origen_ya_facturado` en vez de `idempotente`.
- **Dos cambios en el orden de §7:**
  - `retencion_no_soportada` va después de las líneas (R15-R28) y antes que los totales, porque los totales necesitan
    la cuota (corregido en T21: antes iba en el paso 5; lo fijan los tres `test_f008_orden_*` de la retención);
  - `abono_no_soportado` va antes de comparar totales (R30).
- **Orígenes:** se buscan en la empresa de la obra o en las admitidas. Si un código existe en varias empresas y no
  llega `cod_obra`, el error es `origen_no_encontrado`, con la pista de mandar `cod_obra`.
- **Comprobaciones repetidas dentro de la transacción**, sobre las filas releídas con `UPDLOCK, HOLDLOCK`:
  idempotencia, duplicadas, R14, R15, R22, totales y vencimientos. Si un origen bloqueado cambió o desapareció, el
  error es `origen_no_encontrado`.
- **Marcas verificadas por relectura.** Que cada UPDATE de marca toque su fila (R40) lo garantizan el
  `UPDLOCK, HOLDLOCK` de EF1/EF2 y el `WHERE` condicionado al valor leído bajo ese bloqueo. La relectura comprueba el
  **estado final** que exigen R40-R42 y R45, cosa que un recuento de filas afectadas no dice (`SELECT @@ROWCOUNT`
  funcionaría aun con `NOCOUNT ON`; `cursor.rowcount` no). Se conservan las relecturas por eso:
  - `ctrpro.canfac` se relee con tolerancia, contra lo leído bajo EF4 más `can`;
  - `dca.fecfac` y `dca.horfac` toman la fecha y la hora del alta.
- **`pag.ide` es el `ide` de su `con` 25.** `dcfrec` y `dcaprodes` solo reservan `ide` si hacen falta.
- **Cabecera:**
  - con orígenes, la del primero por `cod`;
  - sin orígenes, la del proveedor, `auxpag` y la obra.
- **Duplicadas:** no se filtran por empresa.
- **Cambios de código en T20:**
  - Se quitaron cuatro respaldos inalcanzables:
    - el argumento `cuo`, que no influía en `totbas`;
    - el `or 0` del vencimiento de garantía;
    - el `(0, 0, 0)` de las sumas del contrato;
    - el `if fila else 0` de `_contar`.
  - `_fecha_real` pierde su tope superior, que era redundante: ahora exige ocho cifras y el resto lo decide `date`.
  - Las conjunciones de los `assert` de tipo se parten en un `assert` por valor.
  - Una línea de contrato que desaparece bajo bloqueo da `filas_afectadas_inesperadas` explícito, **antes** del UPDATE.

## Desviaciones respecto a la spec (justificadas)

1. **No existe `.env.example` en el repositorio.** Los ajustes se documentan en `local.settings.sample.json` y en
   `azure-apps/sigrid_api.md` §4; no se ha creado el fichero.
2. **`linea_sin_origen` no recibe `tasa_iva`**, porque la tasa ya viaja en `LineaResuelta`.
3. **Los valores de los UPDATE van parametrizados** (`estfac = ?`, …), porque la lista negativa de T15 prohíbe valores
   literales en el SQL.
4. **Se usan relecturas en vez de `rowcount`** para R40-R42 y R45: comprueban el estado final, y la unicidad de la
   fila la dan los bloqueos de EF1/EF2 (ver decisiones; el motivo «`NOCOUNT ON`» de la primera versión era falso).
5. **La ruta tiene su propio 400 de validación.** El `validation_error_response` compartido devuelve `input`, que con
   un `model_validator` es el cuerpo entero (CIF, número, importes), y R1 lo prohíbe. La función compartida no se toca.
6. **T15 recorre 53 constantes, no «≥ 60»** como estimaba la tarea. El umbral del test es 50 y el recorrido es exhaustivo.
7. **Dos commits agrupan tareas** (hallazgo H1 de C1C2C5; no se reescribe la historia): `517ddd2` lleva T9 y T10
   (lecturas y reserva de `cod`, en el mismo módulo y con el mismo RED de importación) y `1da3d67` lleva T12, T13 y
   T14 (inserciones, marcas y relectura: una sola transacción, cuyos tests en rojo son comunes, ver la tabla RED). Son 18
   commits para 21 tareas. Pendiente de que el humano la acepte por escrito.

## Fase RED (salida real del primer intento con `python -m pytest -q tests/<fichero>`)

| Tarea | Fichero | Fallo pegado |
|---|---|---|
| T1 | `test_f008_settings.py` | `7 failed ... KeyError: 'SIGRID_FACTURA_WRITE_ENABLED'` |
| T2 | `test_f008_models.py` | `ModuleNotFoundError: No module named 'domain.models.factura_models'` |
| T3 | `test_f008_lineas.py` | `ModuleNotFoundError: No module named 'application.use_cases.factura_lineas'` |
| T4 | `test_f008_lineas.py` | `ImportError: cannot import name 'DCFPRO_COLUMNAS'` |
| T5 | `test_f008_lineas.py` | `ImportError: cannot import name 'comparar_a_origen'` |
| T6 | `test_f008_lineas.py` | `ImportError: cannot import name 'LecturasLineas'` |
| T7 | `test_f008_lineas.py` | `ImportError: cannot import name 'naturalezas_con_cuenta'` |
| T8 | `test_f008_statements.py` | `ModuleNotFoundError: No module named 'application.use_cases.factura_statements'` |
| T9-T10 | `test_f008_statements.py` | `ImportError: cannot import name 'APPLOCKS_FACTURA' from 'application.use_cases.factura_statements'` |
| T11 | `test_f008_use_case.py` | `E   ModuleNotFoundError: No module named 'application.use_cases.create_factura_use_case'` |
| T12-T14 | `test_f008_statements.py` | `16 failed, 52 passed` / `AttributeError: 'FacturaStatements' object has no attribute 'insertar_con'` |
| T12-T14 | `test_f008_transaccion.py` | `27 failed` / `AssertionError: assert ('previsto' == 'creado'` |
| T16 | `test_f008_route.py` | `17 failed, 1 passed` / `AttributeError: <module 'function_app' ...> has no attribute 'CreateFacturaUseCase'` |
| T20 | `test_f008_mutantes.py -k ya_no_existe` | `E       KeyError: 9901` (línea de contrato desaparecida, antes del error explícito) |

- **T15** es un guardia de verificación sobre código ya escrito. Su RED es el autotest del detector: 7 sentencias
  prohibidas de muestra, cada una detectada.
- **T20:** el RED de cada test nuevo es su mutante, aplicado y **medido como muerto** (ver `mutacion_F-008.md`).

### Correcciones de la revisión T21 (ronda 1): RED con `python -m pytest -q -x tests -k f008`

| Commit | Hallazgo | Fallo pegado antes del código |
|---|---|---|
| `a837ab0` | `con` 25 en el PDT de `conest` (C3C4ter H1, escritura 1) | `assert [1] == [7]`; sin PDT: `Failed: DID NOT RAISE <class '...FacturaError'>`; statements: `TypeError: construir_con_pago() got an unexpected keyword argument 'est'` |
| `9cea72f` | `paride` sin `partida` → 400 (lectura 1) | `E       Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>` |
| `23207dd` | orden de `retencion_no_soportada` (lectura 2) | `AssertionError: assert 'retencion_no_soportada' == 'origen_ya_facturado'` y `... == 'lineas_no_validas'` |
| `215aff4` | test trazable de R16 (C4red 1) | conducta ya existente: con la regla rota (`if False:` en el filtro de `can`), `assert [8001, 8002] == [8001]` |

Mutantes de las líneas nuevas, aplicados y medidos uno a uno (sin relanzar la campaña): `paride is not None and
partida is None` → `or`, `paride is None` y `partida is not None`: **los tres muertos** (exit 1). El PDT y el cambio de
orden no añaden operadores mutables: si se quita el PDT de `necesarios` o se vuelve al orden anterior, fallan los tests
de arriba. Documentos (sin código): `4824027` (`current.md`), `7438910` (`verificacion_manual.md`) y `92067d9` en
`azure-apps` (§8.11, solo `sigrid_api.md`).

## Verificaciones MANUAL pendientes (del humano, tras la revisión T21)

- **T22:** comprobar los permisos de `user_rw` (V1) con quien administra Sigrid.
- **T23:** desplegar con la llave cerrada y lanzar las previas P1-P7 de `verificacion_manual.md`, sin `commit`.
- **T24:** grabar G1 (FR en la obra 0404) y G2 (FRGG), cada una con su autorización expresa. Después, «Comprobar»,
  «Contabilizar» y anular en el escritorio (V2-V4, V6, V7).
- **La llave `SIGRID_FACTURA_WRITE_ENABLED` no existe en Azure**, así que vale `false`. Abrirla es decisión del humano.

## Fuera del alcance y avisos

- **Fuera del alcance:**
  - la contabilidad (asiento, `regiva`, `regirp`);
  - los abonos;
  - las retenciones de importe fijo o con IVA;
  - sacar la factura de REC.
- **Cambio ajeno en `azure-apps/sigrid_api.md`:** había una fila de Application Insights sin commitear, de otra persona.
  No se ha tocado ni incluido en `a2127a6`, y sigue en el árbol de ese repositorio.
- **No tocado en la ronda T21, por encargo:** el origen con todas sus líneas a `can` 0 (O1 de `logica_lectura`, decide
  el humano), las demás observaciones no bloqueantes y el hallazgo 6 de `docs` (códigos de línea y
  `SIGRID_ALBARAN_EMPRESAS_OBRA` en §8.11), que el encargo dejó fuera de los puntos 1-5.
- **Sin datos reales:** ningún nombre de persona, proveedor ni CIF real en código, tests, specs ni progress. Los del
  doble son ficticios.

## Evidencias

Medido sobre el código de `215aff4` (el último commit con código de la ronda T21; los posteriores son documentos).

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite completa, `bash harness/init.sh`) | **4211 passed, 1 skipped**, 0 fallos |
| Tests de F-008 (`pytest tests -k f008`) | 418 passed (411 + 7 de la ronda T21) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.3% de 1201 líneas cambiadas cubiertas (1192/1201, umbral 80%, nivel critico)` |
| Mutantes generados / muertos / supervivientes | 568 / 467 / 101 (campaña entera, `--workers 1`, 17.936 s, HEAD `eba243e`) |
| Supervivientes tras el análisis | **0**: 82 con test nuevo, 3 falsos positivos, 16 de código muerto quitado (todo medido) |
| Mutantes de la ronda T21 (manuales, uno a uno) | 4 aplicados, **4 muertos** (los tres de `paride` y quitar el PDT de `necesarios`) |
| Tiempo de la suite | 75,98 s (`4211 passed, 1 skipped, 1 warning in 75.98s`) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (ruff: 104 avisos de deuda previa, no bloquea; tamaño impl 170/220) |

- **Detalle de los 101 supervivientes:** en [`mutacion_F-008.md`](mutacion_F-008.md).
- **Falsos positivos de la campaña (76, 85, 182):** aplicados en aislado, los caza la suite sin cambios; la campaña los
  dio por vivos mientras yo medía en otro worktree. No he encontrado la causa y queda anotado para el reviewer.
- **La campaña es anterior al código final de T20.** Los 16 mutantes de código muerto desaparecen con su línea, y los
  mutantes de las líneas nuevas se aplicaron y midieron uno a uno; no se ha relanzado la campaña entera (unas 5 h).
