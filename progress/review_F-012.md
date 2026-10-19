<!-- progress/review_F-012.md -->
Revisión incremental desde 496bfeb (pasada 2): delta `496bfeb..aea4c77`; lo de la pasada 1, dado por bueno

# F-012 · Revisión

## Pasada 2 (2026-10-19, HEAD `aea4c77`)

- **Veredicto final: APPROVED** para merge a `dev`. No es el `done`: T9 y T10 (MANUAL) lo siguen bloqueando.
- `bash harness/init.sh` entero: **ENTORNO LISTO**, exit 0, **2702 passed, 1 skipped**; `PUERTA COBERTURA [OK]`
  100,0 % (14/14); `PUERTA TAMAÑO [OK]`; ruff 79 avisos, como en `dev`.
- `git diff 496bfeb..HEAD --stat`: solo `http_response_factory.py` (2 líneas en blanco), `current.md`,
  `impl_F-012.md`, `mutacion_F-012.md` y este informe. Ningún test, ni `function_app.py`, ni `azure-apps`.
- **H1 resuelto** (`1676d09`): una línea en blanco menos antes de `_errores_serializables` y una más antes de
  `#: ASCII imprimible`; `ruff check --select E3 --preview` del fichero: «All checks passed!».
- **H2 resuelto** (`aea4c77`): decisiones como aprobadas (y el aviso a albaranes ya dado); el punto «500 en vez de
  400» remite a F-012 `in_progress` y descarta `include_context=False`; backlog y prompt para retomar ya no dan
  F-012 por pendiente.
- **H3 resuelto**: «Lo que queda, en orden» lista merge y push (`! git -C … push origin dev`), T9 con
  `! func azure functionapp publish func-sigridapi-dev-huyke --python` y T10 con el paso 1 de design
  §Verificación manual, el resultado esperado y el paso 2 solo con autorización. Vale como en F-011.
- **H4 resuelto** (`563374c`): campaña **repetida en serie** (`--workers 1`) sobre `1676d09`: 1 generado, 1
  muerto, 0 supervivientes, **104,2 s**, línea base 97,0 s, Workers 1; «Evidencias» trae el worker.
  Verificación: recálculo puro sobre HEAD = 30 líneas, **1 mutante** (factory l. 52 tras H1, `status_code=400,` →
  `401,`): coincide. **Campaña no reejecutada: 104,2 s según el informe** (> 60 s). RM1: después de `1676d09`
  solo cambia `progress/`. RM2: 104,2 = base 97,0 + ~7 s del mutante (muere pronto con `-x`), coste 104 s por
  mutante con W = 1: coherente. Sin «⚠ CAMPAÑA NO VÁLIDA», base rota 0.
- **Checkpoints que estaban `[ ]`:** C2 `current.md` [x] · C3 estilo [x] · C4 MANUAL con comando [x] · C4 bis
  «Evidencias» con workers [x]. C5 sigue aceptado como en F-010/F-011 (T9-T10 MANUAL, tras el merge).
- **O4 · Para `arnes-base`** (lo detectó el implementer en H4): la primera campaña se lanzó en paralelo, pero el
  informe generado decía `--workers 1` y «Workers 1» (con un solo mutante registra los workers efectivos, no el
  modo). La cabecera del informe debería reflejar la orden real; que lo valore el líder.

## Pasada 1 (2026-10-18, HEAD `496bfeb`): CHANGES_REQUESTED

- **Nivel de rigor:** `estandar`, declarado en `harness/features.json`: fase RED, cobertura ≥ 80 % de lo cambiado
  y mutación con supervivientes analizados. Sin tocar código, tests, `features.json` ni `.env`; sin red, API ni base.
- Texto completo de los hallazgos: `git show aea4c77:progress/review_F-012.md`. Resumen:
  1. H1 · C3, PEP 8: E303/E305 en `http_response_factory.py` (l. 39 y 58).
  2. H2 · C2, `current.md` con partes falsas (decisiones abiertas, F-012 «en el backlog», prompt para retomar).
  3. H3 · C4, T9 y T10 sin comando exacto en `current.md`.
  4. H4 · C4 bis, «Evidencias» sin el nº de workers de la campaña.

### Lo ejecutado (pasada 1)

- `bash harness/init.sh` sobre `496bfeb`: **ENTORNO LISTO**, 2702 passed, 1 skipped; cobertura 100,0 % (14/14).
- **Fase RED reproducida** en una copia (`git archive HEAD` al scratchpad, con el `function_app.py` de `dev`):
  `tests/test_f012_rutas.py` → **26 failed**, los mismos 26 del informe del implementer. Volviendo al de HEAD, 38/38.
- `git diff dev...HEAD --stat`: solo los ficheros de design (más papeleo). Ni `domain/`, `application/`,
  `infrastructure/`, `config/`, `scripts/`, ni `tests/fixtures/`, ni ningún test previo: R7 y R9 se cumplen.

### Observaciones (no bloquean)

- **O1 · Observación del implementer sobre el 500: confirmada.** Es semántica de Python (una excepción lanzada
  dentro de un `except` no la recoge un `except` hermano) y lo reproduje: en la copia RED, 10 fallos son
  `assert 500 == 400` con cuerpo del arnés (R1 ×7, R4, R10 ×2: el `TypeError` nace en `_sigrid_albaran_extendido`
  y lo recoge el `except Exception` de `sigrid_albaran`) y 6 son el `TypeError` escapando de la función (R2 ×2,
  R3, R5 ×3: 500 del host, sin cuerpo JSON). La spec simplifica, pero `azure-apps` no afirma quién ponía el 500;
  no hay nada que corregir allí.
- **O2 · R5 del extendido y R32.** El `ValidationError` interno del extendido (`use_case.run`, fuera del `try`
  interior) lo traza el `except` exterior con `str(exc)`. Ya anotado en design e informe como fuera de alcance;
  apoyo la feature aparte que unifique la traza `(loc, type)`.
- **O3 · El generador** solo vio la constante `400` (hueco ya anotado para `arnes-base`); los 6 manuales lo cubren.

### Checkpoints (pasada 1)

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés (los comprueba `init.sh`).
- **C2** [x] una sola `in_progress` (F-012) · [x] rama `feature/F-012-validacion-sin-500` · [ ] `current.md` solo
  con la sesión activa y sin partes falsas: **H2** · [x] toda `done` (F-002…F-011) tiene resumen en `history.md`.
- **C3** [x] hexagonal: el arreglo vive en `interface_adapters/http/`, el factory importa solo `pydantic` y
  `azure.functions`; dominio intacto · [x] primera línea con ruta (factory y los dos tests) · [ ] estilo del
  lenguaje: **H1** · [x] sin `print`, TODOs, secretos ni dependencias nuevas · Reglas Sigrid: N/A justificado, la
  feature no lee ni escribe en la base, no añade SQL y no toca guardias (base correcta, `con`, recálculos,
  estados y SQL parametrizado no aplican).
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] R1-R11 con ≥ 1 test trazable en verde (R12 documental, R13 MANUAL, por diseño) · [x] sin red ni
  base: `build_dependencies`, los tres casos de uso que construye la ruta y `sql_models.get_settings` doblados;
  el repositorio no conecta al construirse · [ ] MANUAL en `current.md` con su comando: **H3**.
- **C4 bis**
  - [x] `rigor: "estandar"` declarado.
  - [x] Fase RED con salida real (T1 `ImportError` y el `TypeError` de hoy; T3, 26 failed con extracto),
    reproducida por mí (arriba).
  - [x] Cobertura `[OK]` 100,0 % (14/14).
  - [x] Mutación verificada de forma independiente: `alcance_de_feature("F-012")` = 2 ficheros, **30 líneas**
    (`function_app.py` 10, factory 20), origen rama `768e2e4..`; `generar_mutantes` = **1** (factory l. 53,
    `entero`, `status_code=400,` → `status_code=401,`). Coincide con el informe.
  - [x] **Campaña no reejecutada: 175,2 s según el informe** (> 60 s): vale el recálculo puro más RM1-RM6.
  - [x] Coste por mutante = 175,2 × 1 ÷ 1 = 175 s (≥ 1 s).
  - [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto (base rota)» = 0; línea base medida (92,7 s).
  - [x] RM1: SHA medido `347ec24`; `git diff 347ec24..HEAD` no toca `function_app.py` ni el factory (solo
    ARCHITECTURE, papeleo y el orden de importaciones de `tests/test_f012_rutas.py`): el alcance es el revisado.
  - [x] RM2: media 175,2 s = «Tiempo total» ÷ evaluados (`InformeMutacion.segundos_por_mutante`, incluye la
    línea base); 1 × 175,2 = total; media × W frente a base 92,7 s, sin salto de orden de magnitud.
  - RM3: sin equivalentes declarados. RM4: aplicado (abajo). RM5: N/A por nivel `estandar`. RM6: N/A, no se
    quitó ninguna guarda.
  - [x] Campaña manual: N/A como sustituta (la automática no dio 0; la manual complementa). Aun así reproduje dos
    filas al pie de la letra en una copia: **M1** (`json.dumps(exc.errors(), default=str)` → `json.dumps(exc.errors())`)
    → **20 failed**, y **M3** (`default=str` → `default=repr`) → **8 failed**; los mismos números del informe.
  - [x] Supervivientes: ninguno, nada en `PENDIENTE`.
  - [ ] «Evidencias» con los cuatro números **y los workers**: faltan los workers, **H4**.
  - [x] Ningún N/A sin justificar en este bloque.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json` (solo el ejemplo). **C5** [ ] aceptado como en F-010 y F-011: T1-T8 y T11 `[x]` con su commit `F-012 Tn:`; **T9 y T10 abiertas**,
  MANUAL, imposibles antes del merge; bloquean el `done`, no el APROBADO · [x] sin temporales ni sin trackear
  · [x] `features.json` = `in_progress`, real.

### Fidelidad a requisitos y design

- **D1 = B**: `_errores_serializables` = `json.loads(json.dumps(exc.errors(), default=str))`. `json_response` usa
  `json.dumps` sin encoder propio, así que todo lo serializable sale idéntico (ida y vuelta estable: tuplas,
  floats, `inf`) y el cuerpo es byte a byte el de antes (test R6 dedicado). Solo cambia lo que antes reventaba.
- **D2**: 9 `return validation_error_response(exc)`, ningún `exc.errors()` en un `details`; los dos
  `exc.errors()` que quedan son las trazas `(loc, type)` del extendido y de partes (R10, R11). Orden de `except`,
  códigos y cuerpos de los demás errores, intactos (R9). **D3**: `json_response` sin tocar.
- **Trazas (R32 de F-009)**: R10 prueba en dos casos que ni referencia, ni descripción, ni precio, ni `msg` llegan
  a `caplog`; el helper no traza (R11).
- **`docs/ARCHITECTURE.md`**: fiel al código.
- **`azure-apps` `4584469`** (solo `sigrid_api.md`, sin remoto): §1.3, §8.2, §8.6 y §8.8 fieles; los mensajes
  citados coinciden literalmente con `sql_models.py` l. 155/157, `albaran_compra_models.py` l. 301 y
  `concepto_grafico_models.py` l. 101; «sin conectar» es cierto (el `model_validate` va antes del caso de uso y
  el repositorio no conecta al construirse); las cuatro notas PENDIENTE DE DESPLIEGUE están; §10 sin tocar, como
  dice el design. La corrección de la frase del `ValidationError` interno de §8.6 es correcta (antes era 500).

### Cobertura requisito → test

| R | Test | Estado |
|---|---|---|
| R1 | `test_f012_r1_cada_regla_del_extendido_es_400_de_validacion` (7 casos, las 6 reglas) | verde, rojo en `dev` |
| R2 | `test_f012_r2_sql_write_sql_y_statements_es_400_de_validacion` (los dos, ninguno) | verde, rojo en `dev` |
| R3 | `test_f012_r3_concepto_grafico_base64_mal_formado_es_400_de_validacion` | verde, rojo en `dev` |
| R4 | `test_f012_r4_*` (3 del helper: `ctx`, `ctx` opaco, `input` opaco) y `..._ctx_error_es_el_mensaje_exacto...` | verde |
| R5 | `test_f012_r5_un_validationerror_interno_es_400_y_no_500` (extendido, clásico, partes) | verde, rojo en `dev` |
| R6 | `test_f012_r6_*` (5 tipos, orden, cuerpo exacto, byte a byte) | verde |
| R7 | `tests/test_f009_caracterizacion.py` y su dorado, sin tocar | verde |
| R8 | `test_f012_r8_las_9_rutas_...` (espía, 9) y `..._ya_no_construye_el_400_a_mano` (fuente) | verde, rojo en `dev` |
| R9 | suite previa sin cambios en aserciones (`git diff` vacío en tests previos) | verde |
| R10 | `test_f012_r10_la_traza_del_extendido_no_lleva_msg_input_ni_ctx` (2 casos) | verde |
| R11 | `test_f012_r11_el_helper_no_emite_trazas` | verde |
| R12 | revisión del reviewer (arriba) | conforme |
| R13 | MANUAL, T10 | pendiente (tras desplegar) |

