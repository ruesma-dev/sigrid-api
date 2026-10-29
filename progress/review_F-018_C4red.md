<!-- progress/review_F-018_C4red.md -->
Revisión completa (pasada 1) sobre `7ce2240` (rama `feature/F-018-descuento-por-linea`, base `dev` = `6aca027`)

# F-018 · Revisión troceada · C4 y C4 bis (fase RED y cobertura)

- **Veredicto del bloque:** APROBADO
- **Alcance de este informe:** C4 entero y, de C4 bis, la **fase RED** y la **cobertura**. Mutación, RM1-RM6, C1-C3,
  C4 ter y C5 van en otros informes troceados.
- **Nivel de rigor:** `critico`, declarado en `features.json`. Exige RED, cobertura de líneas cambiadas ≥ 80 %
  (`rigor.json`) y mutación con cero supervivientes (esta última no es de este bloque).
- **Convivencia:** no he ejecutado `init.sh` ni he aplicado mutantes en el árbol principal. Todo corrió en worktrees
  `--detach` del scratchpad, ya retirados. No he tocado Sigrid ni la API desplegada.
- **El checkout a `dev` (13:23:30-13:23:44) no lo hice yo.** Los tests y la cobertura corrieron en worktrees y ese
  cambio no los afectó. En el árbol principal solo hice lecturas con la rama nombrada explícitamente (`git show`,
  `git diff <rama>`, `alcance_de_feature(rama=…)`). La excepción fue el primer barrido AST, que leía del disco: lo
  repetí a las **13:28:57** desde `git show feature/…`, y esa es la ejecución que vale (5 ficheros, 87 funciones
  `test_*`, ninguna sospechosa). Desde `7ce2240`, HEAD solo añade informes `progress/review_F-018_*.md`.

## 1. Orden de los commits (test en rojo antes que el código)

| Tarea | Commit de test (rojo) | Toca | Código después |
|---|---|---|---|
| T2 | `9cd79ad` | `test_f018_models.py`, `tasks.md` | T3 `e9ad53e` (`albaran_compra_models.py`) |
| T4 | `3ed597e` | `test_f018_statements.py`, `tasks.md` | T5 `46767ac` (`albaran_compra_statements.py`) |
| T6 | `be77bd3` | `test_f018_statements.py`, `tasks.md` | T7 `7e92940` (`albaran_compra_statements.py`) |
| T8 | `007f965` | `test_f018_use_case.py`, `tasks.md` | T10 `09ba32d` (`create_albaran_compra_use_case.py`) |
| T9 | `bfa2b38` | `test_f018_proforma.py`, `tasks.md` | T10 `09ba32d` |

Ningún commit de test toca producción. Los retoques de tests dentro de commits verdes **no debilitan nada**:

- T5 añade un caso no legible (`"٤٠%"`).
- T10 deja de mutar la lista de la fixture compartida de F-007 y sube un import.
- T10 cambia `13.53 - 0.56` por `12.97`. En float, esa resta vale `12.969999…`, y la spec pide 12,97.

T11 y T12 son tests posteriores al código, con su RED hecho rompiendo el código en una copia aislada, como admite
C4 bis.

## 2. Reproducción de las salidas RED (los 5 commits de test)

Mismo comando que el informe (`python -m pytest tests/test_f018_X.py -q -p no:cacheprovider`), en un worktree en el
commit de test:

| Commit | Reproducido | ¿Coincide? |
|---|---|---|
| T2 `9cd79ad` | **26 failed, 24 passed**; 16 `ValidationError` extra_forbidden, 3 `KeyError: 'dto'`, los 5 `AttributeError` y el aviso ausente de `CODIGOS_AVISO` | Sí (obs. 1) |
| T4 `3ed597e` | `ImportError: cannot import name 'bruto_de_linea'`, 1 error en la recolección | Sí |
| T6 `be77bd3` | **8 failed, 90 passed**; `TypeError` por `dto=` e `impbru=`, y `(4.278,'40%',32.08,6.74) == (…32.09…)` | Sí |
| T8 `007f965` | **18 failed, 12 passed**, los mismos 18 tests | Sí (obs. 2) |
| T9 `bfa2b38` | **3 failed, 7 passed**; `10236.37 == 10257.76` y `KeyError: 'dto'` ×2 | Sí |

Coinciden los números, los mensajes y los valores concretos: son salidas reales. El RED de T11 y T12 no es
reproducible desde git, porque se hizo en copias con el código revertido o roto. Su relato es coherente: en T11, R23
pasa porque fija un SQL que no cambia; en T12 caen 16 casos de albarán con `dto` 0 y 5 de proforma con `"5"`.

**Requisitos centrales de R25 con RED pegado:**

- R1, R7, R8, R11 y R15 (con la aserción fuerte de D9): T6.
- R4, R16 y R17: T2.
- R8, R9, R12, R13, R16 y R18: T8.
- R21: T9.
- R7: también T12.
- R2, R3, R5 y R14: el `ImportError` de T4. Es legítimo porque las funciones no existían, aunque es el RED más débil
  (obs. 3).

## 3. Calidad de los tests (comportamiento, no implementación)

He leído enteros los 5 ficheros `tests/test_f018_*.py` (1.369 líneas, 87 funciones, 243 casos).

- **Sin tests vacíos ni tautológicos.** Barrido AST: todas las funciones tienen `assert` o `pytest.raises`, y
  ninguna hace `assert` sobre una constante.
- **Comportamiento observable.** Los valores esperados están calculados a mano a partir de M45-M49: 11,18, 32,09
  frente a 32,08, `impbru` 53,48 e `ivacuo` −104,48. No salen de llamar al propio código. Se comprueban las filas,
  los totales, `mov`/PMP, los parámetros del INSERT en la transacción, el reintento, la traza y el JSON. La
  compatibilidad (R7, R26) compara la foto completa (respuesta, lecturas, SQL con parámetros y traza) contra una
  lista blanca de rutas.
- **Acoplamientos legítimos.** El sha256 del SQL de `dev` es la letra de R23. `pre == tot / can` en float exacto es
  R1. Las funciones puras son la interfaz de `design.md`.
- **Sin dependencias de orden.** `test_f018_*` delante de `test_f007_route`, `test_f007_use_case`,
  `test_f009_use_case` y `test_f016_use_case`: 520 passed.
- **Sin red ni BBDD.** No hay imports de `pyodbc`, `requests`, `httpx`, `socket`, `urllib`, `azure` ni
  `infrastructure`. `git diff dev...` sale vacío en `tests/fixtures`, `infrastructure/`, `config/` y los protegidos
  de T13.

## 4. Puerta de cobertura (cómo la calcula el arnés y recálculo)

Según `harness/init.sh` §7 y §7b y `harness/cobertura.py`:

- La suite corre como `coverage run -m pytest tests -q -x`. El `coverage.json` se borra antes y se regenera después.
- La puerta toma el alcance de `harness.alcance` (el mismo que la mutación: `git diff merge-base..rama`, solo
  producción) y lo cruza con `executed_lines` y `missing_lines`.
- Un fichero que coverage no mide cuenta como no cubierto.
- Mide líneas, no ramas, y solo las que inician una sentencia. El umbral es 80 %.

**Recálculo:**

1. Worktree en `7ce2240`: `coverage run -m pytest tests -q --tb=short -x` → **3793 passed, 1 skipped** (174 s).
2. `coverage json`.
3. `cobertura_lineas_cambiadas()` con el alcance (refs `6aca027..feature/F-018-…`, 245 líneas de diff de
   producción).

Resultado: **102/102 = 100,0 %**, igual que el informe.

| Fichero | Líneas que cuentan | Sin cubrir |
|---|---|---|
| `albaran_compra_statements.py` | 45 | 0 |
| `create_albaran_compra_use_case.py` | 35 | 0 |
| `albaran_compra_models.py` | 22 | 0 |
| `function_app.py` | 0 (solo docstring) | 0 |

El diff de producción no trae `pragma: no cover`, `noqa` ni `type: ignore`.

## 5. Checkpoints de este bloque

**C4**

- [x] **Cada requisito tiene ≥ 1 test trazable, y todos pasan.** Tests `test_f018_rN_*` por requisito: R1 5, R2 3,
  R3 1, R4 5, R5 1, R6 1, R7 5, R8 5, R9 1, R11 3, R12 4, R13 6, R14 2, R15 9, R16 6, R17 1, R18 4, R20 3, R21 5,
  R22 5, R23 2, R24 5, R26 2. Los que no tienen test con su nombre:
  - **R10** se comprueba con una aserción etiquetada `# (R10)` en `test_f018_r24_commit_vinculada_r15`
    (`servido == [[12.5, 9001]]`) y con `ctrprodes[0]["can"] == 12.5` en
    `test_f018_r15_vinculada_sin_dto_con_ctrpro_con_dto` (obs. 4).
  - **R19** lo cubren las suites del clásico y del directo, sin tocar, y el `git diff dev` vacío de T13, como prevé
    `design.md`.
  - R25 es la propia exigencia de tests, R27 es MANUAL y R28 es documental.
- [x] **Sin red ni BBDD** (§3).
- [x] **Verificaciones MANUAL listadas** en `progress/current.md` (l. 10-20, V0-V5, V4 con autorización expresa).
  Los comandos literales están en `specs/F-018-descuento-por-linea/verificacion_manual.md` (bloques `powershell`,
  sin secretos), pendientes como corresponde antes del despliegue.

**C4 bis (los puntos de este bloque)**

- [x] **Rigor:** `critico`, declarado.
- [x] **Fase RED:** salida real en `impl_F-018.md`; los 5 commits de test reproducidos (§2).
- [x] **Cobertura:** el informe trae `PUERTA COBERTURA: 100.0% de 102 … (102/102, umbral 80%, nivel critico)` y lo
  he recalculado con el mismo código de la puerta (§4). No he visto la línea `[OK]` de `init.sh`, porque aquí no me
  está permitido ejecutarlo en el árbol principal.
- Mutación, muertos comprobados, coste de la campaña y RM1-RM6: **N/A en este informe**. Aplican (el rigor es
  `critico`), pero están asignados a `review_F-018_mutacion.md`.

## 6. Observaciones (no bloquean)

1. La lista agrupada de T2 en el informe omite una línea real: `assert 400 == 200`, de
   `test_f018_r4_dto_valido_llega_al_caso_de_uso`. El total 26/24 sí cuadra.
2. En T8 se elide el número de passed (12) y se llama «r4» a `test_f018_d6_decimal_de_la_respuesta`.
3. El RED de T4 es un `ImportError` en la recolección: prueba que el test no podía pasar, pero no enseña el valor
   esperado. Lo compensan T6, T8 y la mutación.
4. R10 no tiene `test_f018_r10_*`. Lo acepto porque la aserción está etiquetada y el comportamiento no cambia («como
   hoy», también cubierto por F-009). Si se quiere el nombre literal, basta con renombrar.

## 7. Propuesta de automejora (no aplicada)

En `CHECKPOINTS.md` C4 bis, «Fase RED», añadir: «Un RED que solo sea `ImportError` o `AttributeError` de la
recolección prueba la *existencia*. En rigor `critico`, los requisitos de cálculo deben enseñar además al menos un
fallo de aserción, con el valor esperado frente al obtenido».

## Cambios requeridos

Ninguno.
