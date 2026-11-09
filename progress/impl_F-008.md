<!-- progress/impl_F-008.md -->
# F-008 · Informe del implementer (T0-T20, ronda T21 y enmienda 1: T26-T33, T36)

Spec v3.1 (`specs/F-008-registrar-factura/`), rigor `critico`. Rama `feature/F-008-registrar-factura`.

## T0 · Esquema medido (solo `sys.columns` y agregados por `sql/read`, 2026-10-30)

Ninguna columna es `IDENTITY` (todos los `ide`, `MAX + 1` bajo applock). `dcf` = columnas de `dca` y `dcfrec` = las de
`dcarec`; `dcfpro`, `pag`, `consii` y `dcaprodes` con lista blanca propia (vacíos fijados en `factura_statements.py`,
commit de T8). IVA `con.tip 23`, cuenta `tip 17` + `cua.niv`, analítica `tip 19` + `caa` (hoja = sin hijos), obra `tip
42`; `conest` 14: CON 3, FAC 10; 15: REC 1, RECGG 20; 25: PDT 1. Tabla completa: historia de este fichero (`e2bc1f4`).

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

- **La idempotencia va antes que los orígenes** (si no, una repetición vería sus orígenes facturados por ella misma).
- **Orden de §7:** `retencion_no_soportada` tras las líneas y antes de los totales (los totales necesitan la cuota;
  T21), y `abono_no_soportado` antes de comparar totales (R30).
- **Orígenes** en la empresa de la obra o en las admitidas; un código en varias empresas sin `cod_obra` da
  `origen_no_encontrado` con la pista. Dentro de la transacción, idempotencia, duplicadas, R14, R15, R22, totales y
  vencimientos otra vez sobre filas con `UPDLOCK, HOLDLOCK`.
- **Marcas verificadas por relectura** del estado final (R40-R42, R45), no por `rowcount`; la unicidad de la fila la
  dan los bloqueos de EF1/EF2 y el `WHERE` condicionado. `pag.ide` = `ide` de su `con` 25.
- **T20** quitó cuatro respaldos inalcanzables y el tope redundante de `_fecha_real`; una línea de contrato que
  desaparece bajo bloqueo da `filas_afectadas_inesperadas` antes del UPDATE.

## Desviaciones respecto a la spec (justificadas)

1. **No hay `.env.example`** en el repositorio: los ajustes, en `local.settings.sample.json` y `azure-apps` §4.
2. **`linea_sin_origen` no recibe `tasa_iva`**: la tasa ya viaja en `LineaResuelta`.
3. **Los UPDATE van parametrizados** (`estfac = ?`): la lista negativa de T15 prohíbe literales en el SQL.
4. **Relecturas en vez de `rowcount`** para R40-R42 y R45 (ver decisiones).
5. **400 de validación propio en la ruta**: el compartido devuelve `input` (el cuerpo entero), y R1 lo prohíbe.
6. **T15 recorre 53 constantes, no «≥ 60»**: el umbral es 50 y el recorrido es exhaustivo.
7. **Dos commits agrupan tareas**: `517ddd2` (T9-T10) y `1da3d67` (T12-T14). **Aceptado por el humano el
   2026-10-31** (C1 de `review_F-008.md`).

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
de arriba.

**R16b, decisión del humano del 2026-10-31 (C2 de `review_F-008.md`):** un origen sin ninguna línea de `can` ≠ 0 →
`origen_sin_lineas` (`details.origenes`), dentro de `_lineas_de_origen`, que corre en la previa y otra vez bajo
`UPDLOCK`; va antes que `origen_ya_facturado` (es del origen, no de una línea). Commits `e2bc1f4` (código y 6 tests),
`1b9f266` (R16b en `requirements.md`) y `f3f6474` en `azure-apps` (§8.11). RED (`python -m pytest -q
tests/test_f008_use_case.py tests/test_f008_transaccion.py -k "r16b or origen_sin_lineas"`): `6 failed`, con
`Failed: DID NOT RAISE FacturaError` (dos orígenes, uno vacío: la previa salía bien) y
`AssertionError: assert ('totales_no_cuadran' == 'origen_sin_lineas'` / `'origen_ya_facturado' == 'origen_sin_lineas'`.
Los tests de commit comprueban que no se abre la transacción ni se escribe nada (y, bajo bloqueo, ROLLBACK intacto).
Mutantes de las líneas nuevas, uno a uno (`pytest -q -x tests -k f008`): `if not float(can or 0)`, `or 1`, `and 0`,
`if True`, `in por_origen`, `if not vacios`, `if False`: **7 de 7 muertos** (exit 1). Restaurados copiando la copia
previa; `python -m harness.mutacion --restaurar` confirma «no quedó ningún mutante aplicado». Documentos: `4824027`,
`7438910` y `92067d9` en `azure-apps`.

## Verificaciones MANUAL pendientes (del humano, tras la revisión T21)

- **T22:** comprobar los permisos de `user_rw` (V1) con quien administra Sigrid.
- **T23:** desplegar con la llave cerrada y lanzar las previas P1-P7 de `verificacion_manual.md`, sin `commit`.
- **T24:** grabar G1 (FR en la obra 0404) y G2 (FRGG), cada una con su autorización expresa. Después, «Comprobar»,
  «Contabilizar» y anular en el escritorio (V2-V4, V6, V7).
- **La llave `SIGRID_FACTURA_WRITE_ENABLED` no existe en Azure**, así que vale `false`. Abrirla es decisión del humano.

## Fuera del alcance y avisos

- **Fuera:** contabilidad (asiento, `regiva`, `regirp`), abonos, retenciones de importe fijo o con IVA, sacar de REC.
- **Cambio ajeno en `azure-apps`** (fila de Application Insights sin commitear, de otra persona): no se ha tocado.
- Hallazgo 6 de `docs` de T21, hecho en `azure-apps` `654e7fd`. **Sin datos reales** en código, tests ni progress.

## Evidencias

Medido sobre el código de `e2bc1f4` (el último commit con código; los posteriores son documentos).

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados (suite completa, `bash harness/init.sh`) | **4217 passed, 1 skipped**, 0 fallos |
| Tests de F-008 (`pytest tests -k f008`) | 424 passed (411 + 7 de la ronda T21 + 6 de R16b) |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 99.3% de 1203 líneas cambiadas cubiertas (1194/1203, umbral 80%, nivel critico)` |
| Mutantes generados / muertos / supervivientes | 568 / 467 / 101 (campaña entera, `--workers 1`, 17.936 s, HEAD `eba243e`) |
| Supervivientes tras el análisis | **0**: 82 con test nuevo, 3 falsos positivos, 16 de código muerto quitado (todo medido) |
| Mutantes de la ronda T21 (manuales, uno a uno) | 11 aplicados, **11 muertos** (3 de `paride`, el PDT de `necesarios`, 7 de R16b) |
| Tiempo de la suite | 276,07 s (`4217 passed, 1 skipped, 1 warning in 276.07s`; la máquina iba cargada: antes, 73-76 s) |
| `bash harness/init.sh` | `ENTORNO LISTO. Puedes trabajar.` (ruff: 104 avisos de deuda previa, no bloquea; tamaño impl 170/220) |

- **Detalle de los 101 supervivientes:** en [`mutacion_F-008.md`](mutacion_F-008.md).
- **Falsos positivos de la campaña (76, 85, 182):** aplicados en aislado, los caza la suite sin cambios; la campaña los
  dio por vivos mientras yo medía en otro worktree. No he encontrado la causa y queda anotado para el reviewer.
- **La campaña es anterior al código final de T20.** Los 16 mutantes de código muerto desaparecen con su línea, y los
  mutantes de las líneas nuevas se aplicaron y midieron uno a uno; no se ha relanzado la campaña entera (unas 5 h).

## Enmienda 1 (spec v3.2, 2026-11-09): naturaleza de la ficha o forzada por empresa, FR con cuenta

| Commit | Tarea | Qué |
|---|---|---|
| `226fcb7` | — | P22, P23 y D3 cerradas (design §9, `spec_F-008_enmienda1.md`, `current.md`) |
| `61cad65` | T26 | `SIGRID_FACTURA_` y `SIGRID_ALBARAN_NATURALEZA_FORZADA` (`{"<emp>:<producto>": cod}`), `parse_naturaleza_forzada`; las dos `_POR_PRODUCTO` retiradas (la de proformas se queda) |
| `892548c` | T27 | `L15D_NATURALEZA_DE_FICHA` (sentencia 48), `leer_naturalezas_de_ficha`, `naturalezas_elegidas` (regla común, con el origen) |
| `f6d81f1` | T28 | `PerfilAlta.naturaleza_de_ficha` (albarán `True`, proforma `False`); mensaje con el origen |
| `24ce6bb` | T29 | FR: `_lecturas_fr` con `naturalezas_elegidas`; `LecturasLineas.origenes_naturaleza` |
| `34cff46` | T30 | `_linea_fr`: o `producto`, o `cuenta` + `analitica` («ambigua» con las dos) |
| `66c7570` | T31 | resolvedor por línea; cada lectura solo con las líneas de su clase |
| `71706f5` | T32 | mutación y 10 tests nuevos (abajo) |
| `e9ab2af` | T33 | `ARCHITECTURE.md`, contrato de albaranes **v8.5**, `tasks.md`; `azure-apps` **`612d84b`** (§4, §8.6, §8.11) |
| `83f6b89` | T36 | ruff: los 9 avisos que añadió la enmienda, a 0 (vuelve a 104, los de antes) |

**Decisiones propias:**
- clave forzada con dos `:` → no arranca (el producto no puede llevar `:`);
- emp con dígitos no ASCII (`١`) → no arranca;
- L7, L15A y L15D solo para productos de la lista blanca, existentes y sin baja (R53);
- L15D va con el tope de filas (`muchas=True`), como las demás lecturas de lista.

**Tests existentes ajustados (no borrados):** `f009_dobles.py` y `f008_dobles.py` (fichas, L15D, forzadas `1:…`);
`test_f007_perfil.py`, `test_f007_settings.py`, `test_f009_settings.py` (nombres y claves nuevos); `test_f009_use_case.py`
(r13b con ficha vacía, `el_mapeo_es_exacto` sin lectura de ficha, r11 con forzado `2:MA9999`);
`test_f009_statements.py` y `test_f015_statements.py` (47 → 48 sentencias); `test_f018_use_case.py` (hash sin L15D).

Sin tocar: `infrastructure/security/`, `.env`, `sigrid/albaran-directo` (P22) y proformas (P23).

### Fase RED (enmienda 1), salida real del primer intento

| Tarea | Comando | Fallo pegado |
|---|---|---|
| T26 | `pytest -q tests/test_f008_settings.py` | `80 failed, 4 passed`; `AttributeError: 'Settings' object has no attribute 'sigrid_factura_naturaleza_forzada'` / `Failed: DID NOT RAISE ValidationError` / `KeyError: 'SIGRID_FACTURA_NATURALEZA_FORZADA'` |
| T27 | `pytest -q tests/test_f008_statements.py tests/test_f008_lineas.py` | `2 errors during collection`; `ImportError: cannot import name 'L15D_NATURALEZA_DE_FICHA'` / `... 'naturalezas_elegidas'` |
| T28 | `pytest -q tests/test_f008_naturaleza_albaran.py` | `TypeError: PerfilAlta.__init__() got an unexpected keyword argument 'naturaleza_de_ficha'`; con solo el campo: `13 failed, 5 passed` (`assert 'ficha' in "La naturaleza del producto 'MA9999' (SIGRID_ALBARAN_NATURALEZA_FORZADA)..."`, `assert ['naturaleza_no_valida'] == ['analitica_no_resuelta']`) |
| T29 | `pytest -q tests/test_f008_lineas.py tests/test_f008_use_case.py` | `17 failed, 165 passed`; `AttributeError: 'AjustesFactura' object has no attribute 'sigrid_factura_naturaleza_por_producto'` / `TypeError: LecturasLineas.__init__() got an unexpected keyword argument 'origenes_naturaleza'` |
| T30 | `pytest -q tests/test_f008_models.py` | `11 failed, 61 passed`; `Value error, lineas[0].cuenta no va en la serie FR.` / `Regex pattern did not match` (`ambigua`, `cuenta y analitica`, `solo va con producto`) |
| T31 | `pytest -q tests/test_f008_use_case.py tests/test_f008_transaccion.py -k "r52 or r27_r52 or r26_fr"` | `5 failed`; `assert [(1, 'producto_no_permitido')] == [(1, 'cuenta_no_valida'), ...]` (la FR con cuenta iba al resolvedor FR) |
| T32 | cada superviviente aplicado a mano | su test nuevo en rojo, `exit 1` (los 10, ver abajo) |

### Mutación (T32): [`mutacion_F-008_enmienda1.md`](mutacion_F-008_enmienda1.md)

`python -m harness.mutacion --feature F-008 --rama feature/F-008-registrar-factura --base dev --workers 1`, sobre
`66c7570`, 315 líneas de 6 ficheros: **104 generados, 94 muertos, 10 supervivientes**, 0 timeouts, 2160,6 s. Ninguno
era equivalente. Cada uno tiene un test nuevo, y aplicado a mano lo caza (`exit 1`). El original se restauró en un
`finally` y `git status` de los fuentes quedó limpio. Huecos cubiertos:
- ficha con `natide` 0 y `auxpronat` 0;
- ficha con `numemp` NULL;
- mapa de proformas: baja, otra empresa, sin `cuacomcod`, dos candidatas;
- tope de filas de L15D;
- producto no permitido sin lecturas de naturaleza;
- dígito no ASCII;
- producto de 1 carácter.

**Total: 104 de 104 muertos.**

### Pendiente (no es del implementer)

- **T34 (MANUAL, humano):** desplegar avisando antes a `albaranes`, porque su llave está abierta y desde ese momento
  manda la ficha. Sin forzado, `MA9999` pasa de `MA99`/`CDSB37` a `MA1501`/`CDMA15`. Después:
  - previas FR con `MA9999`, FR solo con cuenta y una de `sigrid/albaran`;
  - borrar las dos `_POR_PRODUCTO` y cargar en las `_FORZADA` solo excepciones reales;
  - cada cambio, con su autorización expresa.
- **T35:** revisión del reviewer. Siguen pendientes T22-T24 de arriba.

### Evidencias (enmienda 1)

| Evidencia | Valor medido |
|---|---|
| `bash harness/init.sh` (HEAD `83f6b89`) | `ENTORNO LISTO. Puedes trabajar.` |
| Tests (suite completa) | **4364 passed, 1 skipped**, 0 fallos (antes de la enmienda, 4217) |
| Tiempo de la suite | 124,04 s |
| Cobertura de líneas cambiadas | `PUERTA COBERTURA: 100.0% de 136 líneas cambiadas cubiertas (136/136, umbral 80%, nivel critico)` |
| Mutantes generados / supervivientes | 104 / 10 → **0** tras T32 (los 10 con test nuevo, medidos) |
| Tamaños | `requirements 150/150, design 250/250, review 133/140`; ruff 104 avisos (deuda previa) |

