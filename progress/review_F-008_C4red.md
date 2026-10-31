<!-- progress/review_F-008_C4red.md -->
Revisión completa (pasada 1) · trozo `C4red` · código de `2879ddb` (base `dev` = merge-base `ccfb334`)

# F-008 · Revisión troceada: C4, fase RED y cobertura

**Veredicto: CHANGES_REQUESTED.** Son dos cambios baratos de trazabilidad. Los tests son de verdad: he reproducido la
fase RED y he medido la cobertura por mi cuenta.

**Rigor:** `critico`, declarado en `harness/features.json`. Exige tests trazables, fase RED, cobertura de lo cambiado
≥ 80 % y mutación. La mutación y las reglas RM1-RM6 son de otro revisor.

**Cómo he trabajado:** sin `init.sh` ni suite completa (convivencia); roturas en un worktree propio ya borrado, árbol
principal intacto. HEAD avanzó a `a7de17d` solo con informes de otros revisores: el código es el de `2879ddb`.

## C4. La verificación es real

### [ ] Cada requisito tiene un test trazable `test_f008_rN_*` y todos pasan

Los 411 tests de `tests/test_f008_*.py` pasan (11,4 s), y hay test con nombre para R1-R15 y R17-R47. Quedan dos huecos:

- **R16 no tiene test con su nombre.** El requisito dice: líneas con `can` ≠ 0; las de `can` 0 no pasan y quedan con
  `canfac` 0. El comportamiento sí está probado:
  - `test_f008_r3_previa_fr_de_mes_con_un_albaran` (`tests/test_f008_use_case.py:64`) lo comprueba, marcado solo con un
    comentario `# R16`.
  - `test_f008_r40_r41_marcas_de_un_albaran_de_mes` (`tests/test_f008_transaccion.py:218`) comprueba `lineas[8002] == 0.0`.
  - Si se rompe (M3), fallan 11 tests.

  Pero el checkpoint pide trazabilidad por nombre. → Cambio 1.
- **R48 es N/A en este trozo.** Es un requisito de documentación; la T18 de `tasks.md` lo verifica con
  `tests/test_documentos_del_arnes.py` y revisión, y le toca al revisor de docs.

### [x] Los tests no tocan red ni base de datos

Ningún `test_f008_*.py` ni `f008_dobles.py` importa `pyodbc`, `requests`, `socket`, `httpx`, `urllib`,
`SqlServerRepository` ni `get_settings`. La ruta sustituye `build_dependencies` y `CreateFacturaUseCase` con
`monkeypatch` (`test_f008_route.py:49-50`). El doble falla con `AssertionError` si se escribe o se abre transacción en
previa (`f008_dobles.py:432-438`) y ante cualquier SQL desconocido (`:414`, `:663`).

### [ ] Las verificaciones MANUAL están en `progress/current.md` con su comando exacto

La entrada de F-008 en `current.md` nombra T22, T23 y T24, pero ni da el comando ni lo enlaza. Los comandos existen:
`Invoke-RestMethod` exacto en `specs/F-008-registrar-factura/verificacion_manual.md` (§S, §D, §T23, §T24). Ese
documento solo lo enlaza `impl_F-008.md`; la entrada de F-015 en `current.md` sí enlaza el suyo. → Cambio 2.

### [x] El doble `tests/f008_dobles.py` no esconde la lógica bajo prueba

- **Qué hace.** Contesta cada sentencia por su SQL **exacto** (`NOMBRES`/`NOMBRES_TX` salen de `FacturaStatements`);
  sobre `Mundo` solo filtra, cuenta y aplica los `WHERE` de las marcas (`:554-559`); el rollback es un `deepcopy`.
- **Qué no hace.** No valida, no suma totales, no decide estados ni resuelve líneas: todo eso queda en producción.
- **El riesgo de construirlo con las constantes de producción** lo cubre `test_f008_statements.py`, que compara el SQL
  literal. Lo comprobé con M8: el doble siguió verde y el test de statements cazó la rotura.

### [x] Muestreo: ¿fallan los tests si se rompe lo que prueban?

Once roturas a mano. En cada una ejecuté los 8 ficheros `test_f008_*.py` y restauré el fichero.

| # | Rotura | Fallos | Test que la caza (ejemplo) |
|---|---|---|---|
| M1 | admitir vencimientos repetidos: quitar `or vencimiento.fecha in vistas` (`factura_lineas.py`) | 1 | `test_f008_r33_fechas_repetidas_no_valen` |
| M2 | tolerancia de vencimientos ×100 (`factura_lineas.py`) | 3 | `test_f008_r33_la_suma_no_cuadra_con_dos_centimos` |
| M3 | dejar pasar las líneas con `can` 0: quitar el `continue` (`create_factura_use_case.py:622`) | 11 | `test_f008_r3_resumen_de_una_mixta` y otros |
| M4 | `_duplicadas` con `if False` (R43) | 2 | `test_f008_r43_factura_ya_registrada_fuera_de_rech` |
| M5 | el commit no exige `sigrid_factura_write_enabled` (`:331`) | 1 | `test_f008_r5_commit_exige_todas_las_llaves` |
| M6 | la ruta ignora la llave (`function_app.py:460`) | 1 | `test_f008_r4_llave_cerrada_antes_del_caso_de_uso` |
| M7 | el 400 añade `input` (`function_app.py`) | 6 | `test_f008_r1_cuerpo_invalido_sin_eco_ni_codigo` |
| M8 | `EM1_LINEA` sin `AND canfac = ?` (`factura_statements.py:467`) | 1 | `test_f008_r40_marca_de_linea_condicionada_a_canfac_cero` |
| M9 | `extra="ignore"` en `FacturaRequest` | 4 | `test_f008_r1_cuerpo_no_valido` |
| M10 | llave `SIGRID_FACTURA_WRITE_ENABLED` abierta por defecto | 1 | `test_f008_r47_los_siete_ajustes_arrancan_ausentes_y_cerrados` |
| M11 | `origen_ya_facturado` con `if False` | 2 | `test_f008_r15_origen_ya_facturado_por_canfac_o_dcaprodes` |

Ninguna rotura pasó inadvertida; no hay `assert True`, `skip` ni `xfail`. Los seis tests sin `assert`
(`test_f008_lineas.py`, `r33_*` válidos y `r22_*` del borde) son legítimos: comprueban que no lanza. El detector de T15
caza sus 7 sentencias de muestra, y `todas_las_sentencias()` cubre las 53 constantes SQL (recalculado con `vars()`).

## C4 bis (solo fase RED y cobertura)

### [x] Fase RED: reproducida, no creída

Cada commit `Tn` trae test y código juntos, así que el historial por sí solo no demuestra el orden. Para cada fila de la
tabla «Fase RED» de `impl_F-008.md` puse el código de `Tn^`, traje los `tests/` de `Tn` y ejecuté el fichero citado.

| Tarea (commit) | Lo que declara el informe | Lo que reproduje |
|---|---|---|
| T1 `68c7bf1` | `7 failed`, `KeyError: 'SIGRID_FACTURA_WRITE_ENABLED'` | igual ✔ |
| T2, T3, T8, T11 | `ModuleNotFoundError` del módulo nuevo | igual en los cuatro ✔ |
| T4-T7, T9-T10 | `ImportError: cannot import name ...` (5 nombres) | igual en los cinco ✔ |
| T12-T14 `1da3d67`, statements | `16 failed, 52 passed`, `no attribute 'insertar_con'` | igual ✔ |
| T12-T14 `1da3d67`, transacción | `27 failed`, `assert ('previsto' == 'creado'` | igual, pero solo con el `factura_statements.py` de `Tn` ✔ (ver abajo) |
| T16 `eff3e4a` | `17 failed, 1 passed`, `no attribute 'CreateFacturaUseCase'` | igual ✔ |
| T20 `192b3eb` | `-k ya_no_existe`, `KeyError: 9901` | igual ✔ |

- **La fila de transacción.** Con el código de `Tn^` tal cual, el doble no carga: le falta
  `bloquear_lineas_de_contrato`. Con el `factura_statements.py` de `Tn` y el caso de uso de `Tn^`, la traza sale exacta.
  Encaja con un orden interno (primero statements, después la transacción) dentro del mismo commit, así que la doy por
  creíble.
- **Observación (no bloquea).** 10 de las 14 filas son RED de importación: demuestran que el test existía antes que el
  módulo, no que cada aserción fallara por la conducta. En `critico`, ese hueco lo cubre la campaña de mutación (la
  revisa otro trozo).

### [x] Cobertura de las líneas cambiadas

Medí solo con los tests de F-008, sin `init.sh`: `coverage run -m pytest tests/test_f008_*.py` y después
`python -m harness.cobertura --cov <json del scratchpad>`. Resultado:

```
PUERTA COBERTURA: 99.2% de 1195 líneas cambiadas cubiertas (1186/1195, umbral 80%, nivel critico)
```

Coincide con lo que declara el implementer, y eso que solo he corrido la suite de F-008.

Las 9 líneas sin cubrir están en `create_factura_use_case.py` y son respaldos defensivos: 114 (`_ahora_utc` real),
232-236 (traza de una excepción que no es `FacturaError`), 360 (lectura truncada), 428, 517 y 539 (obra, proveedor y
cabecera no encontrados). El resto de los ficheros está al 100 %.

**Sugerencia (no bloquea).** Las líneas 232-236 son las que impiden que la traza vuelque el mensaje de una excepción
inesperada (R46). Un test barato las protegería: que el repositorio lance `RuntimeError("CIF B00000001")` y comprobar que
la traza no lleva el CIF.

## Requisito → test

| Requisito | Tests |
|---|---|
| R1-R15, R17-R47 | al menos un `test_f008_rN_*` cada uno; por ejemplo R1 (route/models), R33 (lineas/use_case), R43 (use_case/transaccion), R47 (settings) |
| R16 | sin nombre propio; lo cubren `..._r3_previa_fr_de_mes_con_un_albaran` y `..._r40_r41_marcas_de_un_albaran_de_mes` (Cambio 1) |
| R48 | N/A aquí (documentación, trozo `docs`) |

## Cambios requeridos

1. **Dar a R16 un test trazable**, en `tests/test_f008_use_case.py:64` o en `tests/test_f008_transaccion.py:215`. Por
   ejemplo, `test_f008_r16_solo_lineas_con_can_distinta_de_cero`: en la previa, la línea 8002 (`can` 0) no aparece en
   `dcfpro` ni en `dcaprodes`; tras el commit, su `canfac` vale 0. Basta con extraerlo de los dos tests actuales.
2. **Enlazar `../specs/F-008-registrar-factura/verificacion_manual.md` junto a T22-T24** en la entrada de F-008 de
   `progress/current.md`, como hace F-015. Si el trozo C1C2C5 ya pide reescribir esa entrada, hacedlo en la misma
   edición.

## Automejora (propuesta para `CHECKPOINTS.md`, C4 bis, fase RED; no aplicada)

Cuando el test y el código van en el mismo commit, propongo pedir que el RED sea reproducible ejecutando los tests de
`Tn` sobre el código de `Tn^`, o que el implementer diga qué estado intermedio lo produjo.
