<!-- progress/review_F-008_C4red.md -->
Revisión completa (pasada 1) · trozo `C4red` · código de `2879ddb` (base `dev` = merge-base `ccfb334`)

# F-008 · Revisión troceada: C4, fase RED y cobertura

**Veredicto: CHANGES_REQUESTED** (dos cambios baratos de trazabilidad. Los tests son de verdad: la fase RED se
reproduce y la cobertura se confirma de forma independiente).

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige tests trazables, fase RED, cobertura de lo
cambiado ≥ 80 % y mutación. La mutación y RM1-RM6 son de otro revisor.

**Alcance:** C4 completo, más dos puntos de C4 bis: la fase RED y la cobertura.
**Fuera:** mutación, RM, la lógica contra la spec, C1/C2/C3/C5 y la documentación.
**Cómo se trabajó:**
- Sin `init.sh` ni la suite completa, por convivencia con otros revisores.
- Lo que hubo que romper se rompió en un worktree propio, `scratchpad/wt`, que ya está borrado.
- El árbol principal no se ha tocado: `git status` está limpio.
- Desde que empecé, HEAD avanzó a `a7de17d`, pero solo con informes de otros revisores (`progress/review_F-008_*.md`).
  El código revisado sigue siendo el de `2879ddb`.

## Checkpoints

### C4. La verificación es real

- [ ] **Cada requisito tiene un test trazable `test_f008_rN_*` y todos pasan.** Los 411 tests de
  `tests/test_f008_*.py` pasan (11,4 s). Hay test con nombre `rN` para R1-R15 y R17-R47. Quedan dos huecos:
  - **R16** («todas las líneas con `can` ≠ 0; las de `can` 0 no pasan y quedan con `canfac` 0») **no tiene ningún
    test con su nombre**. El comportamiento sí está probado:
    - lo comprueban `test_f008_r3_previa_fr_de_mes_con_un_albaran` (`tests/test_f008_use_case.py:64`, solo un
      comentario `# R16`) y `test_f008_r40_r41_marcas_de_un_albaran_de_mes` (`tests/test_f008_transaccion.py:218`,
      `lineas[8002] == 0.0`);
    - al quitar el `continue` de `can` 0 (M3, abajo) fallan 11 tests.

    Pero nada se llama `r16`, y el checkpoint pide trazabilidad por nombre. → Cambio 1.
  - **R48** (documentación): N/A en este trozo, con justificación. Es un requisito de documentos, y `tasks.md` T18
    declara que se verifica con `tests/test_documentos_del_arnes.py` más revisión. Le toca al revisor de docs.
- [x] **Los tests no tocan red ni base de datos.**
  - Ningún `tests/test_f008_*.py` ni `tests/f008_dobles.py` importa `pyodbc`, `requests`, `socket`, `httpx`,
    `urllib`, `SqlServerRepository` ni `get_settings`.
  - La ruta dobla `build_dependencies` y `CreateFacturaUseCase` con `monkeypatch` (`tests/test_f008_route.py:49-50`).
  - El doble de repositorio:
    - lanza `AssertionError` si se llama a `execute_write_command` o a una transacción en previa (`f008_dobles.py:432-438`);
    - lanza `AssertionError` ante cualquier SQL desconocido (`:414`, `:663`).
- [ ] **Las verificaciones MANUAL están en `progress/current.md` con su comando exacto.**
  - La entrada de F-008 en `current.md` nombra T22, T23 y T24, pero **no da el comando ni enlaza** el documento que
    lo tiene.
  - Los comandos existen, en `specs/F-008-registrar-factura/verificacion_manual.md` §S, §D, §T23 y §T24, con
    `Invoke-RestMethod` exacto. Solo enlaza a ese documento `impl_F-008.md`.
  - Precedente: F-015, en `current.md`, sí enlaza su `verificacion_manual.md`.

  → Cambio 2.

### El doble `tests/f008_dobles.py` no esconde la lógica bajo prueba [x]

- **Dónde está la semántica del doble.** Contesta cada sentencia por su SQL **exacto**: construye el mapa
  `NOMBRES`/`NOMBRES_TX` a partir de las propias constantes de `FacturaStatements`. Esa semántica la emula sobre
  `Mundo` y se reduce a filtrar, contar y aplicar las condiciones `WHERE` de las marcas
  (`marcar_linea`, `:554-559`, respeta `canfac = ?`).
- **Lo que no hace.** No valida, no suma totales, no decide estados, no numera más allá de `MAX` y no resuelve líneas.
  Todo eso queda en el código de producción.
- **El riesgo de construir el doble con las constantes de producción.** Si el SQL de producción estuviera mal, el doble
  no lo notaría. Lo cubre `test_f008_statements.py`, que compara el SQL **literal**. Comprobado con M8, abajo: al quitar
  `AND canfac = ?` de `EM1_LINEA`, el doble sigue verde y lo caza
  `test_f008_r40_marca_de_linea_condicionada_a_canfac_cero`. Las capas están bien repartidas.
- **El rollback.** El doble lo emula con `deepcopy` del `Mundo` (`:689-712`), y no hay lógica de negocio dentro.

### Muestreo: ¿fallan los tests si se rompe lo que prueban? [x]

Once roturas a mano en el worktree aislado. En cada una se ejecutaron los 8 `test_f008_*.py`, y después se restauró
el fichero.

| # | Rotura (fichero) | Resultado | Ejemplo de test que la caza |
|---|---|---|---|
| M1 | admite un vencimiento repetido: quita `or vencimiento.fecha in vistas` (`factura_lineas.py`) | 1 failed | `test_f008_r33_fechas_repetidas_no_valen` |
| M2 | tolerancia de vencimientos ×100 (`factura_lineas.py`) | 3 failed | `test_f008_r33_la_suma_no_cuadra_con_dos_centimos` |
| M3 | las líneas con `can` 0 pasan: quita el `continue` (`create_factura_use_case.py:622`) | 11 failed | `test_f008_r3_resumen_de_una_mixta` y otras |
| M4 | `_duplicadas` con `if False` (R43) | 2 failed | `test_f008_r43_factura_ya_registrada_fuera_de_rech` |
| M5 | el commit no exige `sigrid_factura_write_enabled` (`:331`) | 1 failed | `test_f008_r5_commit_exige_todas_las_llaves` |
| M6 | la ruta ignora la llave (`function_app.py:460`) | 1 failed | `test_f008_r4_llave_cerrada_antes_del_caso_de_uso` |
| M7 | el 400 añade `input` (`function_app.py`) | 6 failed | `test_f008_r1_cuerpo_invalido_sin_eco_ni_codigo` |
| M8 | `EM1_LINEA` sin `AND canfac = ?` (`factura_statements.py:467`) | 1 failed | `test_f008_r40_marca_de_linea_condicionada_a_canfac_cero` |
| M9 | `extra="ignore"` en `FacturaRequest` | 4 failed | `test_f008_r1_cuerpo_no_valido` |
| M10 | llave `SIGRID_FACTURA_WRITE_ENABLED` abierta por defecto | 1 failed | `test_f008_r47_los_siete_ajustes_arrancan_ausentes_y_cerrados` |
| M11 | `origen_ya_facturado` con `if False` | 2 failed | `test_f008_r15_origen_ya_facturado_por_canfac_o_dcaprodes` |

**Tautologías.** Ninguna `assert True`, ninguna `skip` ni `xfail`.

**Tests sin `assert`.** Hay seis, en `test_f008_lineas.py` (`r33_*` válidos y `r22_*` en el borde), y son legítimos:
prueban que la función **no lanza** en los casos válidos, y M2 demuestra que sus vecinos sí fallan.

**El detector de la lista negativa.**
- La de T15 tiene autotest: 7 sentencias prohibidas, todas cazadas.
- Ninguna de las 53 constantes de SQL del módulo queda fuera de `todas_las_sentencias()`. Lo recalculé recorriendo
  `vars(factura_statements)`.

## C4 bis (solo los dos puntos de este trozo)

### [x] Fase RED: creíble y coherente con el historial (reproducida, no creída)

**El problema del historial.** Cada commit `Tn` trae juntos el test y el código, así que el historial no demuestra el
orden por sí solo.

**Cómo lo reproduje.** Para cada fila de la tabla «Fase RED» de `impl_F-008.md`:
1. puse el worktree en `Tn^`, es decir, el código de antes;
2. traje `tests/` de `Tn`;
3. ejecuté el fichero citado.

| Tarea (commit) | Lo que declara el informe | Lo que reproduje |
|---|---|---|
| T1 `68c7bf1` | `7 failed ... KeyError: 'SIGRID_FACTURA_WRITE_ENABLED'` | `7 failed`, mismo `KeyError` ✔ |
| T2, T3, T8, T11 | `ModuleNotFoundError` del módulo nuevo | idéntico en los cuatro ✔ |
| T4-T7, T9-T10 | `ImportError: cannot import name ...` (5 nombres) | idéntico en los cinco ✔ |
| T12-T14 `1da3d67`, statements | `16 failed, 52 passed`, `no attribute 'insertar_con'` | `16 failed, 52 passed`, idéntico ✔ |
| T12-T14 `1da3d67`, transaccion | `27 failed`, `assert ('previsto' == 'creado'` | ver la nota de debajo |
| T16 `eff3e4a` | `17 failed, 1 passed`, `no attribute 'CreateFacturaUseCase'` | `17 failed, 1 passed`, idéntico ✔ |
| T20 `192b3eb` | `-k ya_no_existe`, `KeyError: 9901` | `1 failed`, `KeyError: 9901` ✔ |

**Nota sobre transaccion.**
- Con el código de `1da3d67^` tal cual, el doble no carga: falta `bloquear_lineas_de_contrato`.
- Con el `factura_statements.py` de `1da3d67` (el paso de statements, cuyo RED es la fila anterior) y el caso de uso
  de antes, sale **exactamente** `27 failed` con `'previsto' == 'creado'`.

Es coherente con un orden interno statements → transacción dentro del mismo commit. Creíble.

**Observación, no bloquea.**
- 10 de las 14 filas son RED de importación: demuestran que el test existía antes que el módulo, pero no que cada
  aserción fallara por la conducta.
- Las filas de T1, T12-T14 y T16 sí son fallos de conducta.
- En `critico`, lo que cubre el hueco es la campaña de mutación (otro revisor). Si sigue en pie, los RED de importación
  bastan.

### [x] Cobertura de las líneas cambiadas

**Medición independiente.** Medí sin `init.sh`, solo con los tests de F-008:

```
.venv/Scripts/python.exe -m coverage run -m pytest tests/test_f008_*.py
```

Pasé el JSON resultante (en el scratchpad) a `python -m harness.cobertura --cov <json>`:

```
PUERTA COBERTURA: 99.2% de 1195 líneas cambiadas cubiertas (1186/1195, umbral 80%, nivel critico)
```

Coincide con lo que declara el implementer, y solo con la suite de F-008.

**Las 9 líneas sin cubrir.** Todas están en `create_factura_use_case.py`, y son respaldos defensivos:

| Línea | Qué es |
|---|---|
| 114 | `_ahora_utc` real |
| 232-236 | traza de una excepción no `FacturaError` |
| 360 | lectura truncada |
| 428 | `obra_no_encontrada` |
| 517 | `proveedor_no_encontrado` |
| 539 | cabecera ilegible |

El resto de ficheros tiene el 100 %.

**Sugerencia, no bloquea.** Las líneas 232-236 garantizan que la traza no vuelque el mensaje de una excepción
inesperada: guardan solo `type(exc).__name__`. Es justo la familia de fuga de R46 y F-012. Un test barato
(el repositorio lanza `RuntimeError("CIF B00000001")` y se comprueba que la traza no lleva el CIF) la blindaría.

## Cobertura de requisitos (resumen; el detalle está en los nombres de los tests)

| Requisito | Tests |
|---|---|
| R1-R15, R17-R47 | ≥ 1 `test_f008_rN_*` cada uno, en los 8 ficheros. Ejemplos: R1 `route/models`, R33 `lineas/use_case`, R43 `use_case/transaccion`, R47 `settings` |
| R16 | **sin nombre propio**. Cubierto de hecho por `test_f008_r3_previa_fr_de_mes_con_un_albaran` y `test_f008_r40_r41_marcas_de_un_albaran_de_mes` (Cambio 1) |
| R48 | N/A aquí: documentación, la verifica el trozo `docs` |

## Cambios requeridos

1. **`tests/test_f008_use_case.py:64` (o `tests/test_f008_transaccion.py:215`): dar a R16 un test trazable.**
   Vale un `test_f008_r16_solo_lineas_con_can_distinta_de_cero` que compruebe las dos mitades del requisito:
   - en la previa, la línea 8002 (`can` 0) no está en `dcfpro` ni en `dcaprodes`;
   - tras el commit, `lineas[8002]["canfac"] == 0.0`.

   Basta con renombrar o extraer de los dos tests actuales; no hace falta conducta nueva.
2. **`progress/current.md`, entrada de F-008: enlazar
   [`verificacion_manual.md`](../specs/F-008-registrar-factura/verificacion_manual.md) junto a T22-T24**, como se hace
   en F-015, para que las verificaciones MANUAL tengan su comando exacto a un clic desde `current.md` (C4, tercer punto).
   Si el trozo C1C2C5 ya pide reescribir esa entrada, se resuelven las dos peticiones en la misma edición.

## Automejora (propuesta, no aplicada)

**Propuesta para `CHECKPOINTS.md` C4 bis, fase RED.** Pedir al implementer que, cuando el test y el código vayan en el
mismo commit, el RED se pueda reproducir con «tests de `Tn` sobre el código de `Tn^`», o que diga qué estado intermedio
lo produjo.

Aquí funcionó en 13 de 14 filas. En la que no (transaccion), costó una búsqueda averiguar que el estado intermedio era
«statements de `Tn` + caso de uso de `Tn^`».
