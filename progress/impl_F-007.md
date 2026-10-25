<!-- progress/impl_F-007.md -->
# F-007 · Informe del implementer (lotes A, B y C: T1-T17; T18-T19)

Rama `feature/F-007-registrar-proforma`, rigor **critico**. Spec v3, PARADA 1 aprobada el 2026-10-25 (D4-D14; D11
con `SM9999`, `SB9999`, `SM370001`). Nada contra Sigrid: ni lecturas ni escrituras; los tests no tocan red ni base.
T1-T17 hechas, un commit por tarea (`04f13ba`…`bbd562c`); T18-T19 en un segundo encargo (`904a2ef`…`d9e97a8`,
más `af81713` en `azure-apps`). **Paro en T19**: T20-T24 van aparte.

## Qué cambió (por tarea)

- **T1** · red de R31 sin tocarla: `pytest tests/test_f009_*.py tests/test_f015_*.py` → 816 passed. Intocables:
  los ocho `test_f009_*.py`, los dos `test_f015_*.py`, el dorado `tests/fixtures/f009_caracterizacion.json` y el
  doble `tests/f009_dobles.py`. Al terminar, `git diff dev --` de todos ellos (y de `infrastructure/`) **vacío**.
- **T2-T5** · costuras en el núcleo de F-009 con los valores de hoy (sin cambio de conducta):
  `PerfilAlta`/`PERFIL_ALBARAN` y `perfil` de clase en `create_albaran_compra_use_case.py` (traza, serie, guardas,
  llave, catálogo y `cifras_serie` leen del perfil); `prefijo_de_serie`/`sellos_del_alta` con `prefijo` y
  `siguiente_cod(..., cifras=0)` en `albaran_compra_statements.py` (ninguna constante SQL cambia); gancho
  `_comprobar_dentro` tras E1 (vacío en la base); `_Catalogo` con `productos_del_contrato` (R17); `codigos` de clase en
  `FalloLinea`, `AlbaranCompraError` y `AvisoAlbaran`. Cinco App Settings de R4 en `config/settings.py` y
  `local.settings.sample.json`, con defecto cerrado y los validadores de F-009.
- **T6-T7** · `domain/models/proforma_models.py`: petición (R1-R3), línea (R2, R13), respuesta (R10, R30),
  `ProformaError` con `reparto`, `FalloLineaProforma` con `candidatos`, conjuntos de códigos ampliados.
- **T8-T11** · `application/use_cases/proforma_statements.py`: LP1-LP6 constantes con `?`, validadas con
  `DatabaseReferenceGuard` (LP4 al generarse); puras `normalizar_nombre`, `primer_dia_de_periodo`, `fin_de_periodo`,
  `candidatos_de_contrato`, `contrato_pedido` (R7), `resolver_contrato` (R8-R9), `identificar_linea`,
  `revisar_lineas` (etapa 1), `fecha_de_periodo`, `entref_por_defecto`, `comprobar_hoja`, `linea_descuadrada`,
  `anterior_y_origen`, `aviso_anterior_de_linea`, `buscar_del_mes`, `lineas_del_existente`, `es_proforma`, `traducir`.
  Fixture `tests/fixtures/f007_obra0719.json` (M29) generado con proveedores y CIF ficticios.
- **T12-T15** · `application/use_cases/create_proforma_use_case.py`: `CreateProformaUseCase(CreateAlbaranCompraUseCase)`
  con `PERFIL_PROFORMA` (`sigrid/proforma`, `PROF`, 5 cifras, `cla` 141, llave y listas `sigrid_proforma_*`,
  `productos_del_contrato`, `ProformaError`); `run` con la traza R33; flujo de design §Flujo; `_construir` pone
  `dca.cla`; `_comprobar_dentro` repite R24 con LP1 por el cursor bajo `SIGRID_REFEXT_14` (R28). Doble
  `tests/f007_dobles.py` que extiende el de F-009 sin tocarlo (reconoce LP1-LP6 dentro y fuera de la transacción).
- **T16-T17** · ruta `sigrid/proforma` en `function_app.py`: valida con `ProformaRequest` (400 de F-012, traza solo
  `loc`/`type`), llave R5 solo con `commit` y antes del caso de uso, caso de uso construido en la ruta (la tupla de
  `build_dependencies` no cambia), `AlbaranCompraError` → 400 con `codigo`, `lineas` (con `candidatos`) y `reparto`.

## T18 · mutación (detalle en [`mutacion_F-007.md`](mutacion_F-007.md))

- En serie (`--workers 1`). **Ronda 1** (`a3acbd7`): 375 mutantes, 308 muertos, **67 supervivientes**. Cada uno se
  aplicó a mano en un `git worktree` desechable (`../sigrid-api-mut007`, nunca en el árbol compartido) y se midió.
- Resolución (`904a2ef`): 22 tests nuevos en `tests/test_f007_filas.py`, 25 en `test_f007_models.py`, 3 en
  `test_f007_use_case.py` y una aserción en `test_f007_statements_contrato.py`. **Hueco real**: las seis lecturas de muchas filas
  no pedían `max_allowed_rows` en ningún test (sin el tope, un contrato grande saldría truncado). **Código muerto**
  quitado: el `break` de `identificar_linea`. Reescritos para que el borde se pueda probar: fecha y periodo por el
  año, `es_proforma` sin `or 0`, `vinculada` por el `tipo` de línea del núcleo.
- **Ronda 2** (`7cbff6b`): 374 mutantes, **372 muertos**, 2 supervivientes: el `cifras: int = 0` (equivalente medido:
  `zfill(0)` ≡ `zfill(1)`; el defecto lo exige el test intocable de F-009) y el borde 2999 del año (test mal
  planteado, corregido en `8c92d52` y medido a mano). **0 supervivientes no aceptados.**
- **Falso superviviente de la herramienta** en la ronda 1: `% 100` → `% 101` de `prefijo_de_serie` (núcleo). Aplicado
  a mano muere en 7 s (`test_f007_r31_prefijo_de_serie_con_el_defecto_ac`) y la ronda 2 también lo mata. Para
  `arnes-base`: la campaña en serie también miente a veces (sin diagnosticar).
- **Manuales** (ficheros con ≤ 2 automáticos: `albaran_compra_models.py` 0, `settings.py` 2), suite entera en el
  worktree, **10 de 10 mueren**: A1-A5 (costura 5: un código de proforma en el conjunto base de `FalloLinea` y de
  `AlbaranCompraError`, y las tres validaciones contra el conjunto fijo) caen en `test_f007_models.py`,
  `test_f007_perfil.py` y `test_f007_filas.py`; S1-S5 (llave abierta por defecto, prefijos y naturalezas fuera de
  su validador, tope 100, productos leídos de la App Setting de albaranes) caen en `test_f007_settings.py`.

## T19 · documentación (R36)

- `docs/ARCHITECTURE.md` (ruta, módulos, sección «`sigrid/proforma`» con las cinco costuras), la ruta en el mapa de
  `CLAUDE.md` (solo eso), docstring de `validation_error_response` con 10 rutas, `contrato_proformas.md` a **v1**
  (`periodo` y `fecha_proforma` enteros, el CIF manda, R9 y el respaldo de R14, sin contrato no se comprueba la hoja
  ni hay `existente`, forma de `existente` e `idempotente`, 400 sin `codigo` y 500; §8 con los cambios). `7cbff6b`.
- `azure-apps/sigrid_api.md`, rama `master`, commit `af81713` (sin push): §8.10 nueva, la ruta en §8, §7.2 punto 9
  (llave), §7.6, las cinco App Settings en §4 y sus valores de despliegue de D11 en §4.1 (la llave **cerrada** hasta
  T22), el consumidor `proformas` F-005 y el `entref` `PROF<MMAA>_<obra>` en la fila de `facturas` (§10), y §13.
  Cada bloque lleva **«PENDIENTE DE DESPLIEGUE (F-007)»**. `local.settings.sample.json` ya iba en T4.
- Las notas «PENDIENTE (F-015)» de `azure-apps` siguen ahí: se quitan al cerrar F-015 (`current.md`), no aquí.

**Texto del aviso** (lo manda el líder; no he avisado a nadie):

> **sigrid-api F-007 (`POST /api/sigrid/proforma`) implementada en su rama, pendiente de revisión y despliegue.**
> - **proformas (F-005)**: contrato v1 en `sigrid-api/specs/F-007-registrar-proforma/contrato_proformas.md` (§8, lo
>   que cambió desde v0.1). Lo que os afecta: `periodo` y `fecha_proforma` son **enteros** (`202608`; el texto da
>   400); si mandáis `cif_proveedor`, manda sobre el nombre; sin contrato no hay `existente` ni comprobación de la
>   hoja; referencia `PRF-`; vuestra lista de productos debe estar contenida en la de la API. Siguen abiertas las
>   preguntas de design §Preguntas.
> - **facturas**: las proformas que registre la API serán `tip 14` de la serie `PROF<aa>/` (`cla 141`) con
>   `dca.entref` = `PROF<MMAA>_<cod_obra>`, el mismo de las `AC` de hoy. Si buscáis proformas por `con.cod` `AC…`,
>   añadid la serie `PROF`. Ver `azure-apps/sigrid_api.md` §8.10 y §10.
> - **albaranes**: se ha tocado el núcleo del modo extendido de `sigrid/albaran` **sin cambio de conducta** (cinco
>   costuras con los valores de hoy); su dorado y sus tests de F-009 y F-015 pasan sin modificarse. No hay nada que
>   cambiar en sv9.

## Fase ROJA (comando y salida real, antes del código)

- T2 `python -m pytest tests/test_f007_perfil.py -q`:
  `E ImportError: cannot import name 'PERFIL_ALBARAN' from 'application.use_cases.create_albaran_compra_use_case'`
  → `1 warning, 1 error in 1.49s`.
- T3 `python -m pytest tests/test_f007_settings.py -q`: `40 failed, 2 passed in 2.09s` (p. ej.
  `FAILED ...::test_f007_r4_el_fichero_de_ejemplo_declara_las_cinco_cerradas`).
- T6 `python -m pytest tests/test_f007_models.py -q`:
  `E ModuleNotFoundError: No module named 'domain.models.proforma_models'` → `1 error in 0.44s`.
- T8 `python -m pytest tests/test_f007_statements_contrato.py -q`:
  `E ModuleNotFoundError: No module named 'application.use_cases.proforma_statements'` → `1 error in 0.67s`.
- T10 `python -m pytest tests/test_f007_statements_lineas.py -q`: `E ImportError: cannot import name
  'FalloIdentificacion' from 'application.use_cases.proforma_statements'` → `1 error in 2.67s`.
- T12 `python -m pytest tests/test_f007_use_case.py -q`:
  `E ModuleNotFoundError: No module named 'application.use_cases.create_proforma_use_case'` → `1 error in 0.80s`.
- T14 `python -m pytest tests/test_f007_transaccion.py -q`: `6 failed, 9 passed` — las seis de R28/R29 con LP1
  dentro, p. ej. `E AssertionError: assert ('creado', 'P...2900011, True) == ('existente',...831541, False)`. Las
  nueve que ya pasaban caracterizan lo heredado del núcleo (orden, `UPDATE`, relecturas, previa).
- T16 `python -m pytest tests/test_f007_route.py -q`: `17 failed` (`E AttributeError: <module 'function_app' ...> has
  no attribute 'CreateProformaUseCase'`; la de registro, `assert 'sigrid_proforma' in {...}`).

- T18 (los tests nuevos contra cada superviviente aplicado en el worktree; script del scratchpad que corre
  `python -m pytest tests/test_f007_*.py -q -x --tb=no`, más F-009/F-015 si el mutante es del núcleo). Ejemplos:
  `[61] create_proforma_use_case.py:227 MUERE ['FAILED tests/test_f007_use_case.py::test_f007_t18_las_lecturas_de_
  muchas_filas_piden_el_tope_de_filas'] ['1 failed, 453 passed']`; `[219] proforma_statements.py:570 MUERE ['FAILED
  tests/test_f007_filas.py::test_f007_t18_r20_la_del_primer_dia_del_periodo_no_es_anterior']`; `[345]
  proforma_models.py:197 MUERE ['FAILED tests/test_f007_models.py::test_f007_t18_numero_de_orden_cero']`. 61 de 67
  mueren así; los otros seis: dos ya no existen (el `break` quitado y `vinculada` reescrita), tres equivalentes
  medidos con la suite entera (`exit=0`) y reescritos, y el `cifras` (equivalente, medido aparte). Ronda 2, borde 2999: `FAILED tests/test_f007_models.py::test_f007_t18_fecha_
  proforma_fuera_de_los_anios[30000101]` — `Failed: DID NOT RAISE ValidationError` (`1 failed, 1531 passed`).

Cada tarea de implementación siguiente (T4, T5, T7, T9, T11, T13, T15, T17) dejó en verde su verificación de
`tasks.md`; T5, T13 y T15 con `test_f009_*` y `test_f015_*` dentro (858 y 873 passed).

## Desviaciones de la spec y decisiones (para el reviewer y el humano)

1. **Costura 1 ampliada** con `cifras_serie` (R12 «5 cifras», M1 `PROF26/01282`) y `error` (la clase de las guardas,
   para que la llave lance `escritura_proformas_deshabilitada` como `ProformaError`). `PERFIL_ALBARAN` = 0 y
   `AlbaranCompraError`: el albarán sigue igual. La costura 5 se aplica también a `AvisoAlbaran`.
2. **`periodo` es un entero `AAAAMM`** estricto (como `fecha_albaran` de F-009 y «números estrictos» de R1); el ejemplo
   de `contrato_proformas.md` §3 lo escribe como texto `"202608"`, que da 400. Contrato alineado en T19 (v1).
3. **Fixture 0417**: la hoja de septiembre convertida trae MES 0, así que el fixture usa la de **agosto**
   (`AC26/25552`, `totbas` 31.291,06) y no `/29425`, que es la que cita T21. El dry-run manual de T21 debe decidir
   cuál de las dos se compara.
4. **R8, CIF y nombre**: si viene `cif_proveedor`, se filtra solo por CIF (manda sobre el nombre, «por este orden»).
5. **R9 sin contenedor ni reparto limpio**: si alguna línea de contrato no está en ningún candidato,
   `contrato_no_resuelto`; si se solapan, `contrato_ambiguo`. Con varios candidatos y ninguna línea de contrato,
   `contrato_ambiguo`.
6. **R14, respaldo**: la partida (si viene) es filtro duro; medición, unidad y precio solo se aplican mientras quedan
   varias y solo si dejan alguna. Sin partida, se empieza por todas las líneas del contrato.
7. **R11 literal**: sin contrato no hay ninguna comprobación de R19, tampoco `linea_descuadrada`.
8. **R23**: LP5 se lee tras la obra y se decide con el contrato resuelto; `idempotente` se construye con L11 y
   `_respuesta_idempotente` del núcleo (sin re-traducir), con `contrato` y `origen` nulo. Dentro de la transacción,
   E1 sigue con la regla de F-009 (mismo `entide` y obra); el caso «misma referencia, otro `cla`» bajo el applock es
   residual (los prefijos `PRF-` y `ALB-` no se cruzan).
9. **`existente`**: `cabecera` `{fec, entref}`, `totales` `{totbas, n_lineas}` y los avisos de F-007 de la hoja (R20-R22).
10. **Producto del contrato sin plantilla** (R17): naturaleza, cuenta, analítica e IVA a 0 con `producto_sin_historico`,
    como cualquier sin vincular sin histórico.
11. **R28**: el contexto (contrato, periodo, importe, `otra_del_mes`) viaja en un `PrivateAttr` de una subclase de
    `AlbaranCompraRequest`; la `existente` hallada dentro sale por una excepción interna que revierte la transacción
    y se responde fuera con LP6. Con `otra_del_mes`, lo de dentro no para.
12. **Ruta**: `ValueError` → 400 como en `sigrid/albaran` (cuerpo que no es JSON, lectura truncada); lo demás, 500.
13. **Test de F-012 tocado**: `test_f012_r8_function_app_ya_no_construye_el_400_a_mano` cuenta las rutas con
    `return validation_error_response(exc)`; pasa de 9 a 10 por la ruta nueva (una línea, con comentario). El
    docstring de `validation_error_response` decía «las 9 rutas»: corregido en T19.
14. `ahora` se lee dos veces (fecha de R18 y sellos del núcleo); la fecha viaja como `fecha_albaran`, así que
    `con.fec` y `fecdoc` no dependen de la segunda lectura (solo `hor` y `tiemod`).

## Verificación (resultado real)

- `python -m pytest tests/test_f007_*.py -q` → **466 passed** en 4,0 s (tras T18: models 144, filas 22, use_case 47;
  el resto como en T17: perfil 37, settings 42, contrato 50, lineas 92, transaccion 15, route 17).
- `python -m pytest tests -q` (dentro de `init.sh`) → **3347 passed, 1 skipped**.
- `bash harness/init.sh` → **ENTORNO LISTO** (salida al final de §Evidencias).
- `git diff dev -- tests/test_f009_* tests/test_f015_* tests/fixtures/f009_caracterizacion.json tests/f009_dobles.py
  infrastructure/` → vacío.
- Las tres hojas de agosto de la 0719 dan `existente` sobre `AC26/25548`, `AC26/25552` y `AC26/25551` con sus líneas,
  en previa y con `commit`, sin transacción (`test_f007_r24_las_tres_hojas_de_la_0719_son_existentes`).
- ruff limpio en todos los ficheros nuevos; en `function_app.py` quedan los 3 avisos previos (I001, BLE001, RUF010),
  que no se tocan.

## Qué queda (fuera de este encargo)

- **T20-T22** MANUALES (V6-V8, despliegue con las App Settings de R4 y la llave cerrada, dry-runs de la 0719 y un
  `commit:true` autorizado). En T21, decidir si la hoja de la 0417 se compara con `/25552` (agosto, la del fixture) o
  con `/29425` (desviación 3).
- **Avisos** a `proformas`, `facturas` y albaranes (texto arriba, los manda el líder).
- **T23** revisión contra `CHECKPOINTS.md`; **T24** `init.sh`. El worktree de la medición ya está borrado (`git worktree remove`).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | 3347 passed, 1 skipped (suite completa en `init.sh`); 466 de F-007 |
| Cobertura de las líneas cambiadas | **100,0 %** (710/710, umbral 80 %, nivel critico) |
| Mutantes generados / supervivientes | Ronda 2: **374 / 2** (372 muertos, 0 timeouts): uno equivalente justificado y uno cazado después (`8c92d52`). Ronda 1: 375 / 67. Manuales: 10 / 0 |
| Tiempo de la suite | 100,63 s con cobertura (`init.sh`); F-007 sola, 4,0 s; campaña ronda 2, 3755 s |

Salida de `bash harness/init.sh` (última ejecución, sin las líneas de puntos):

```
[OK] Arnés v1.7.8 (2026-09-02) · [OK] features.json válido · [OK] BACKLOG.md al día
[AVISO] Hay features en estado blocked: revisa progress/current.md      (F-015, previa)
[AVISO] ruff: 79 avisos (deuda previa, no bloquea)
3347 passed, 1 skipped, 1 warning in 100.63s (0:01:40)
[OK] pytest en verde (con medición de cobertura)
[OK] PUERTA COBERTURA: 100.0% de 710 líneas cambiadas cubiertas (710/710, umbral 80%, nivel critico)
[OK] PUERTA TAMAÑO: F-007 dentro de los topes (requirements 150/150, design 239/250, impl 196/220)
[OK] Rama actual: feature/F-007-registrar-proforma
ENTORNO LISTO. Puedes trabajar.
```
