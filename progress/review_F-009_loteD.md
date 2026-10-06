<!-- progress/review_F-009_loteD.md -->
Revisión completa (pasada 1) del lote D (T13, T14, T15, O1 y O2 del lote C), diff `1ac999a..0abf048b4a5e3e3c8fa04538ca7b95d45378f2d4`

# F-009 · Revisión del lote D · **Veredicto: APPROVED**

Alcance: `6ed3c7a` y `8ab15de` (T13), `8ac52cb` (T14), `fd1674c` (T15), `11d13c0` (O1, O2), `0abf048` (informe).
Lo aprobado en los lotes A-C (hasta `1ac999a`) queda dado por bueno; el delta solo toca `run` del caso de uso (envoltura
de traza alrededor del `_ejecutar` de antes, sin cambios dentro) y el mensaje del IVA, así que no invalida nada aprobado.

## Nivel de rigor

`critico` (declarado en `harness/features.json`). Exige fase RED, cobertura ≥ 80 % de lo cambiado y mutación con cero
supervivientes. La campaña completa es **T16 (lote E)** por el plan de lotes aprobado: aquí C4 bis-mutación es N/A con ese
motivo, y en su lugar he medido mutantes dirigidos (abajo).

## Verificación ejecutada (salida real)

- `bash harness/init.sh` (tal cual): `2339 passed, 1 skipped`; `PUERTA COBERTURA: 100.0% de 1102 líneas cambiadas
  (1102/1102, nivel critico)`; `PUERTA TAMAÑO` en verde; `ENTORNO LISTO`.
- `ruff check` de `test_f009_route.py`, `test_f009_use_case.py` y del caso de uso: `All checks passed!`.
- **T14**: `git diff dev --` de los dos casos de uso y los dos modelos del clásico y del directo → 0 líneas;
  `git diff dev --stat -- infrastructure/` vacío; `git log -- tests/fixtures/f009_caracterizacion.json` → solo `91b929d`
  y `783f2d1` (T1). El diff del test de caracterización es **un único hunk** en `ejecutar` (`:378-382`, el doble de
  `build_dependencies` con ocho posiciones): ni `CASOS` ni comprobaciones ni dorado. `SettingsDoble` ya traía
  `sigrid_albaran_write_enabled = True` desde `783f2d1` (llave R8 abierta en los casos de commit del dorado).
- **Mutantes medidos por mí (RM4)** sobre una copia `git archive HEAD` en el scratchpad (árbol de trabajo intacto; `git
  status` solo enseña `` `0`].{t `` , preexistente, ver O5). Los nueve **mueren**:

| # | Mutante | Resultado |
|---|---|---|
| 1 | `_clave` sin `.casefold()` (`create_albaran_compra_use_case.py:80`) | 6 failed (partida, producto, naturaleza, analítica, cuenta, mapeo) |
| 2 | O2: mensaje del IVA sin `(referencia_linea '…')` (`:1244-1247`) | 1 failed |
| 3 | R8 `if not settings…` (sin `commit`) (`function_app.py:280`) | failed |
| 4 | R8 `if commit or not settings…` | failed |
| 5 | sin `_exigir_escritura_de_albaranes` en el extendido (`:272`) | failed |
| 6 | sin `_exigir_escritura_de_albaranes` en el directo (`:319`) | failed |
| 7 | `self._reloj = time.monotonic` (reloj ignorado) | failed |
| 8 | traza de excepción con `str(exc)` en vez del tipo | failed |
| 9 | selector anulado (`if False:` en vez de `elegir_modo_albaran`) | failed |

## Comprobaciones del encargo

1. **T13.** `function_app.py:220-228`: el modo sale de `elegir_modo_albaran(body)` (claves, no valores) antes de validar;
   `peticion_mixta` sale del selector con un repositorio que revienta si se toca (`test_f009_r1_peticion_mixta…`, ×3,
   también con `lineas: null`). Extendido: 200 superconjunto sin bancarias (§3.1); 400 `{type, codigo}` y `details.lineas`
   solo en `lineas_no_validas`, forma exacta `{indice, referencia_linea, codigo, mensaje}` (§3.3); `ValueError` → 400 de
   texto y lo inesperado → 500 (§3.4). R8 en clásico, extendido y directo, después de Pydantic y antes de `run`; el
   defecto es cerrado (`config/settings.py:115`, `False`). Docstring H32 corregido y fijado por test. `build_dependencies`
   de ocho, con test del cableado y de las otras cuatro rutas (`test_f009_t13_las_demas_rutas…`). RED real de R1 y R8 en
   el informe (traza de `pytest` antes del código, separando el fallo de la tupla del de comportamiento).
2. **El clásico no cambia**: `test_f009_caracterizacion.py` 17 passed; ver T14 arriba. El `except AlbaranCompraError`
   añadido antes de `ValidationError` no altera ningún camino clásico: su caso de uso no lanza ese error.
3. **T15** (`create_albaran_compra_use_case.py:200-241`, `run` y `_trazar`): una traza `INFO` por petición en éxito, error y excepción; los
   siete tests comparan el dict entero y buscan once valores prohibidos en `caplog.text`. La excepción se traza por tipo y
   se relanza con `raise` desnudo; `reloj` solo alimenta `duracion_ms` (mutante 7 muere; el resto de la suite, igual).
4. **O1** cerrada: siete tests nuevos; mutante 1 medido por mí, 6 failed. **O2** cerrada: mensaje con `referencia_linea`,
   fijado con `^…$` (mutante 2 muere).
5. **Seguridad.** Con `commit:true` y la llave cerrada ningún caso de uso se ejecuta (R8 en ruta, ×3 rutas, con
   `caso.peticiones == []`); en el extendido, además, `_comprobar_guardas` (`:285-303`) exige las dos llaves, credenciales
   de escritura y base en `ALLOWED_WRITE_DATABASES` (vacía no abre). Clásico y directo conservan sus guardas de siempre
   (R2/R3). La ruta del extendido traza `ValidationError` solo por `(loc, type)` y `AlbaranCompraError` solo por códigos.
   Ver O1 y O2 sobre el 500.
6. Tests sin red ni BBDD: `build_dependencies`, `SqlServerRepository`, casos de uso y repositorio doblados.

## Checkpoints

Fuera: **C3 bis** (N/A: el lote no trae documentos de fuera) y **C4 ter** (N/A: no existe `harness/rutas_sensibles.json`).

- C1: [x] init en verde · [x] ficheros del arnés.
- C2: [x] una `in_progress` (F-009) · [x] rama `feature/F-009-alta-albaran-compra` · [x] `current.md` al día ·
  N/A `history.md` (F-009 no está `done`).
- C3: [x] hexagonal (la ruta orquesta; dominio sin infraestructura; el caso de uso detecta `IntegrityError` sin importar
  `pyodbc`) · [x] primera línea con ruta · [x] sin `print`, TODO ni secretos; sin dependencias nuevas · Sigrid: N/A
  justificado en base, `con`/extensión, recálculo, estados y SQL: el lote no añade SQL ni filas (lo hicieron B-C).
- C4: [x] trazabilidad (tabla abajo) · [x] sin red ni BBDD · [x] los MANUAL siguen en T19-T24.
- C4 bis: [x] `rigor` declarado · [x] fase RED con salida real (R1, R8, T15, O2) · [x] cobertura 100 % ·
  N/A mutación, «muertos comprobados», tiempo, CAMPAÑA NO VÁLIDA, RM1, RM2, RM5, RM6, campaña manual y supervivientes:
  la campaña `critico` es T16 (lote E) por el plan aprobado; sustituida aquí, solo como control, por los nueve mutantes
  medidos de la tabla · [x] «Evidencias» con los cuatro números · [x] ningún N/A sin motivo.
- C5: [x] T13-T15 `[x]` con commits `F-009 Tn:` (O1/O2 van como `F-009:`, no son tareas) · N/A «todas las tareas»: T16-T24
  quedan para lotes posteriores · [x] sin artefactos nuevos sin trackear (el único es anterior, O5) · [x] `features.json`.

## Cobertura requisito → test (lote D)

| Req. | Tests |
|---|---|
| R1 | `test_f009_r1_con_lineas_va…`, `_sin_lineas_ni_referencia…`, `_basta_la_clave…` (×3), `_peticion_mixta…` (×3), `_lo_que_no_es_un_objeto…` (×3) |
| R2-R4 | `test_f009_caracterizacion.py` (17, dorado intacto) + comandos de T14 |
| R5 (ruta) | `test_f009_r5_campo_naturaleza_400_sin_codigo` |
| R7 | `test_f009_r7_previa_extendida_200_superconjunto_sin_bancarias` |
| R8 | `test_f009_r8_commit_con_la_llave_cerrada…` (×3), `_el_dry_run_no_cambia…` (×6), `_commit_con_la_llave_abierta…` (×3), `_la_guarda_va_despues…`, `_el_directo_sigue_construyendose…` |
| R9 | `test_f009_r9_error_de_cabecera…`, `_lineas_no_validas_trae_todas…`, `_el_codigo_y_las_lineas…`, `_un_valueerror…`, `_lo_inesperado…` |
| R32 | `test_f009_r32_traza_de_una_previa`, `_de_un_commit`, `_de_un_idempotente`, `_de_un_error_de_cabecera`, `_de_lineas_no_validas…`, `_de_lo_inesperado…`, `_el_reloj_por_defecto…` + los dos `r32` de ruta |
| Cableado/H32 | `test_f009_t13_build_dependencies…`, `_las_demas_rutas…` (×4), `test_f009_h32_el_docstring…` |
| O1 / O2 | siete `…sin_mayusculas` / `…es_exact[ao]…`; `test_f009_r17_el_iva_inexistente_nombra…` |

## Observaciones (no bloquean)

- **O1 · Un `ValidationError` lanzado DENTRO del caso de uso extendido** (p. ej. al construir `AlbaranCompraResponse`,
  `create_albaran_compra_use_case.py:492` y `:960`, también tras un COMMIT) caería en el `except ValidationError` externo
  de `function_app.py:231-237`: 400 `Solicitud invalida.` (F-053 lo lee `error`, no `incierto`) y `str(exc)` en la traza,
  con valores de entrada (R32). No hay hoy camino conocido que lo dispare y design manda no cambiar los `except`
  existentes; **para T16/T18**: decidir si `_sigrid_albaran_extendido` convierte ese caso en 500 y documentarlo.
- **O2 · El 500 devuelve `details.exception = str(exc)`** (`function_app.py:245-251`), heredado de todas las rutas; en el
  extendido puede llevar el texto de un error de `pyodbc`. No es secreto, pero conviene anotarlo en T18.
- **O3 · Decisión 2 del informe, inexacta en un punto.** Con `commit:true` y la llave cerrada, R8 responde antes que
  `demasiadas_lineas`, al revés que el orden de §4.1 del contrato. Lo manda la spec (R8: «antes de ejecutar el caso de
  uso»; la spec manda sobre el contrato). Pero **no es cierto** que F-053 vea el mismo estado: `demasiadas_lineas` va a
  `no_admitido` y `escritura_albaranes_deshabilitada` a `error` (§3.3). Sin impacto práctico (sv9 siempre hace antes la
  previa, que no pasa por R8), pero **T18 debe escribirlo así** en `azure-apps/sigrid_api.md`.
- **O4 · Desviación de design aceptada**: sin `except pyodbc.IntegrityError` en la ruta (decisión 5); la colisión ya llega
  como `AlbaranCompraError(colision_de_clave)` desde `create_albaran_compra_use_case.py:634-638`. T17 debe reflejarlo.
- **O5 · Fichero vacío sin trackear `` `0`].{t `` en la raíz** (fecha 2026-09-24, anterior a F-009 lote D). No lo creó este
  lote; el humano o el líder deberían borrarlo.
- **O6** · La traza R32 no se emite cuando la ruta corta antes del caso de uso (`peticion_mixta`, Pydantic, R8); la ruta
  deja un `warning` sin obra ni referencia. Coherente con design §Flujo (paso 6); anotarlo en T17.
- **O7** · Docstring «tupla de siete» de `tests/test_f004_route.py` (decisión 6): para T17.

## Cambios requeridos

Ninguno.

## Automejora (propuesta, no aplicada)

En revisiones por lotes de rigor `critico`, que el encargo del reviewer pida explícitamente **mutantes dirigidos sobre las
guardas nuevas del lote** (como la tabla de arriba), no solo sobre las observaciones previas: cuesta segundos sobre una copia
`git archive` y adelanta los supervivientes de la campaña final.
