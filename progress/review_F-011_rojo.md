<!-- progress/review_F-011_rojo.md -->
# F-011 · Revisión acotada: C4 bis, fase ROJO y cobertura

Revisión completa (pasada 1) del bloque ROJO + cobertura, sobre HEAD `4d1c266`
(rama `feature/F-011-documents-read-valida-database`). La mutación la revisa otro encargo.

**Veredicto del bloque: APPROVED** (sin cambios requeridos).

**Nivel de rigor:** `critico`, declarado en `harness/features.json` (no se aplica el defecto). Para
este bloque exige fase RED con traza real en los requisitos centrales y cobertura de las líneas
cambiadas ≥ 80 %.

## Método

Todo en copias aisladas del scratchpad (`git worktree`), sin cambiar la rama del árbol principal ni
tocar código: `wt_rojo` (rama temporal en `4d1c266`, para la cobertura) y `wt_rojo_t1` (detached,
recorriendo `6defcad`, `9929e69`, `adbc2ec`, `b76c403` y `4d1c266`). Los dos worktrees y la rama
temporal están borrados; el worktree `wt` / `review-f011-mut` es del encargo de mutación y no lo
toqué. Intérprete: `.venv` del proyecto, comprobado que los módulos se cargan desde la copia.
`tests/test_f011_caso_de_uso.py` no cambia entre `6defcad` (T1) y HEAD: el ROJO se midió con el
mismo test que hoy pasa.

## Fase ROJO: lo reproducido

| Tarea | Cómo | Resultado del informe | Resultado reproducido |
|---|---|---|---|
| T1 (firma) | `6defcad`, `pytest tests/test_f011_caso_de_uso.py` | `28 failed` (TypeError ×25, AttributeError ×3) | **idéntico**: 25 `TypeError` de `__init__`, 3 `AttributeError` de `BaseNoPermitidaError`, `28 failed` |
| T1 (semántico) | `9929e69` con `self._validar_base(...)` sustituido por `pass` | `21 failed, 7 passed` | **idéntico**: 8 `DID NOT RAISE`, 7 `no debía llamarse a read_document`, 5 `IdentifierValidationError` (R6), 1 R2-conexión; los 7 verdes son R8 y R10. Restaurado: `39 passed` con F-010 |
| T3 (ruta) | `adbc2ec` con `function_app.py` de `9929e69` | `1 failed, 12 passed` (R9) | **idéntico**: falla solo `test_f011_r9_el_rechazo_deja_un_warning` (`ValueError en documents/read` ≠ `BaseNoPermitidaError en documents/read`). Restaurado: `28 passed` con `test_f010_ruta.py` |
| T4 (composición) | HEAD, `build_dependencies` con `settings.model_copy()` | `1 failed, 1 passed` | **idéntico** (falla el de identidad `is`) |
| T4 (bis) | HEAD, settings doble con `allowed_write_databases` + base documental | `2 failed` | **idéntico**: `2 failed` |
| T5 (adaptador A1) | `b76c403`, `pytest test_f011_repositorio.py test_f011_ruta.py` | `66 failed, 37 passed` | **idéntico**: 64 R14 (`Capturada`: la base llegó a `pyodbc.connect`), 1 R13, 1 ruta (`assert 500 == 400`) |
| Test del tipo literal (T9) | HEAD, `details={"type": type(exc).__name__}` | M14 sobrevivía hasta añadirlo | **rojo confirmado**: `1 failed, 14 passed`, solo `..._literal_tambien_para_una_subclase` |
| R15 (guarda de regresión) | HEAD, `DATABASE={safe_database} ;` | (no lo enseña: pasa antes y después por diseño) | **rojo confirmado por mí**: 24 R15 + 1 R13 fallan |

Todas las roturas se restauraron con `git checkout -- .` y `git status` limpio antes de borrar.

### Valoración

- El ROJO es **semántico, no solo de firma**: el implementer no se quedó en el `TypeError` de T1 y
  enseñó (y he reproducido) el fallo con la firma ya puesta y sin la validación. Cada fallo cita el
  comportamiento vigilado (no se lanza, se llama al repositorio, llega a `pyodbc.connect`, log con
  otro tipo, 500 en vez de 400).
- **Hallazgo honesto del informe, confirmado:** sin el `except BaseNoPermitidaError` propio, el
  `except ValueError` genérico ya daba 400 con `details.type = "BaseNoPermitidaError"` (usa
  `type(exc).__name__`). Los tests R1/R8 de ruta no podían ponerse en rojo contra la rama; lo que
  sostiene la rama dedicada son R9 (texto del log) y el test de la subclase (tipo literal). Los dos
  tienen rojo real, así que no queda código de producción sin un test que falle al quitarlo.
- R10, R11 y R12 son de **no-regresión** (comportamiento de F-010 que no debe cambiar): pasan antes
  y después por construcción. Su ROJO previo es N/A con motivo: no hay código nuevo cuyo fallo
  enseñar; R15 era del mismo tipo y lo he roto en copia para confirmar que vigila de verdad.
- Matiz menor, sin efecto: en el rojo semántico, `test_f011_r2_base_no_permitida_no_abre_conexion`
  falla por `DID NOT RAISE`/`AttributeError` del doble `SimpleNamespace()` del adaptador antes de
  llegar al `prohibido` de `pyodbc.connect`. Sigue siendo rojo por la causa correcta (se pasó de la
  validación), pero el mensaje no es el del espía. No requiere cambio.

## Cobertura de las líneas cambiadas: recalculada

En `wt_rojo` (HEAD `4d1c266`): `coverage run -m pytest tests -q --tb=short -x` (el mismo comando de
`init.sh`, sin lanzar `init.sh`) → **`2664 passed, 1 skipped`** en 97,7 s; después
`python -m harness.cobertura --base dev --config harness/rigor.json`:

```
PUERTA COBERTURA: 100.0% de 16 líneas cambiadas cubiertas (16/16, umbral 80%, nivel critico)
exit=0
```

Cruce independiente con `harness.alcance` + `coverage.json` (líneas de sentencia del alcance):

| Fichero | Sentencias cambiadas ejecutadas | Sin cubrir |
|---|---|---|
| `application/use_cases/read_document_use_case.py` | 7, 8, 14, 16, 20, 44, 49, 50, 51 | — |
| `domain/models/document_models.py` | 15 | — |
| `function_app.py` | 37, 72, 483, 486, 487 | — |
| `infrastructure/repositories/sql_server_repository.py` | 80 | — |

9 + 1 + 5 + 1 = **16/16**, coincide con lo declarado en `impl_F-011.md`. El resto de líneas del alcance
(docstrings, continuaciones de una misma sentencia como `DATABASE={safe_database};` en l. 85) no son
sentencias propias y la herramienta no las cuenta, como en las demás features.

## Checkpoints de este bloque (C4 bis)

- [x] La feature declara `rigor: "critico"` en `harness/features.json`.
- [x] **Fase RED**: trazas reales pegadas en `impl_F-011.md` para T1 (firma y semántica), T3, T4 y
      T5; las seis reproducidas al pie de la letra en copia aislada, más dos roturas propias
      (tipo literal y R15) que también ponen la suite en rojo.
- [x] **Cobertura**: `PUERTA COBERTURA` en `[OK]`, 100,0 % de 16 (umbral 80 %), recalculada por mí
      con la herramienta del arnés y con el cruce línea a línea.
- N/A en este informe: mutación, RM1–RM6 y el resto de C1–C5. **Motivo:** fuera del alcance de este
      encargo; los revisa otro bloque (`review_F-011_C1C2C5.md` y el de mutación).

## Cobertura de requisitos por ROJO

| Req. | Test que lo cubre | ROJO |
|---|---|---|
| R1, R3, R4, R5, R6 | `test_f011_caso_de_uso.py::test_f011_r1_*`, `r3_*`, `r4_*`, `r5_*`, `r6_*` | semántico reproducido (T1) |
| R2 | `test_f011_r2_base_no_permitida_no_llama_al_repositorio`, `..._no_abre_conexion` | semántico reproducido |
| R7 | `test_f011_composicion.py` (2) | reproducido en copia (T4) |
| R8 | `test_f011_r8_base_no_permitida_hereda_de_value_error`, `..._literal_tambien_para_una_subclase` | firma (T1) + literal reproducido |
| R9 | `test_f011_ruta.py::test_f011_r9_el_rechazo_deja_un_warning` | reproducido (T3) |
| R10, R11, R12 | `test_f011_r10_*`, `test_f011_r11_*` y suite F-010 intacta | N/A: no-regresión, pasan antes y después |
| R13, R14 | `test_f011_repositorio.py::test_f011_r13_*`, `r14_*` y ruta `r14_lista_mal_configurada_*` | reproducido (T5) |
| R15 | `test_f011_repositorio.py::test_f011_r15_cadena_identica_a_la_de_hoy` (24) | rojo por rotura en copia (mío) |
| R16, R17 | revisión documental / MANUAL (T12-T14) | N/A: no son código |

## Cambios requeridos

Ninguno en este bloque.

## Propuesta de automejora (no aplicada)

Al protocolo del reviewer: cuando una rama `except` nueva queda tapada por una genérica que ya da el
mismo código y tipo (aquí `except ValueError` con `type(exc).__name__`), pedir explícitamente qué test
pone en rojo **esa rama** y no solo el requisito. Aquí estaba resuelto (R9 + test de la subclase),
pero el ROJO de R1 en ruta, por sí solo, no lo habría demostrado.
