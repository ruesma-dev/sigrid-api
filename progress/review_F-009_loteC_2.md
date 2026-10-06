<!-- progress/review_F-009_loteC_2.md -->
Revisión completa (pasada 1) del trozo 2 del lote C: `git diff d4e695d..1c10f72` (T10 `65f4ae6`, T11 `f60d9a5`,
T12 `1c10f72`). De T7-T9 (otro reviewer) solo lo que estos commits consumen: `_resolver_lineas`, `_construir` y dobles.

# F-009 · Revisión del lote C, trozo 2 (T10-T12: commit, devoluciones, equivalencia)

**Veredicto: APPROVED.** Sin cambios requeridos. Seis observaciones (O1-O6) que no bloquean; tres son para el lote D/T18.

**Nivel de rigor:** `critico` (declarado en `features.json`), con fase RED, cobertura ≥ 80 % y mutación con cero
supervivientes. La mutación es **T16 (lote E)**, sobre la feature entera, por el plan de lotes aprobado en la PARADA 1:
en este trozo es N/A justificado y será exigible al cierre. Para compensarlo, abajo va un análisis RM4.

## Verificación (salidas reales)

- `bash harness/init.sh`, tal cual: `2284 passed, 1 skipped`, `PUERTA COBERTURA 100.0% (1042/1042, critico)`,
  `PUERTA TAMAÑO` dentro de los topes y `ENTORNO LISTO`. `ruff` limpio en los cuatro ficheros del trozo.
- **RED reproducida** en el scratchpad (`git archive d4e695d` más el `test_f009_use_case.py` de `65f4ae6`):
  `-k "r26 or r27 or r28"` da `15 failed, 132 deselected`; el `-k` ancho del informe, `29 failed, 4 passed, 114
  deselected`. Las dos coinciden con el informe, y los 4 que pasan son los que él dice.
- **RM4, mutantes manuales del camino de commit** (copia de HEAD en el scratchpad, `test_f009_use_case.py` y
  `test_f009_equivalencia.py`): **15/15 MUERTOS**. Los mutantes:
  - `if vinculadas:` → `True`, y E5 reservado siempre.
  - `_es_colision_de_clave` → `False`.
  - `cuantas != esperadas` → `>`, y → `<`.
  - E7 ignorado, y `ide` del `log` sin poner.
  - Sin `timeout`, y sin comprobar la clave de escritura.
  - Servido = 0 en `_estados`, y `estser`/`estfac` cruzados.
  - `abs(cantidad)` en E9, y lista de bases vacía que abre.
  - `almcan <= 0`, y relectura de `mov` con `len(dcapro)`.

  Un decimosexto mutante, que solo tocaba un comentario, era el control y quedó vivo, como debía.
- Dorado intacto: `git log -- tests/fixtures/f009_caracterizacion.json` da solo `91b929d` y `783f2d1`.
- `git diff dev..HEAD` **vacío** en el clásico, `albaran-directo` y sus modelos, `infrastructure/` (incluido
  `security/`), `function_app.py` y `.env`. `.env` no está versionado.
- Los campos de `SettingsDoble` existen todos en `Settings.model_fields` (comprobado por script), y las firmas del
  repositorio coinciden con `sql_server_repository.py`: el doble no tapa ningún nombre mal escrito.

## Los diez puntos del encargo

1. **Guardas antes de leer (R24, decisión 14)**, `create_albaran_compra_use_case.py:219-252`.
   - Orden: tope → prefijo → con commit, llaves, usuario y clave de escritura → base. Lista vacía no abre (`:248`).
   - Sigue el patrón de F-006 (`create_partes_reclamacion_use_case.py:264-277`). Los tests exigen
     `repo.llamadas == []`, y la previa no pide llaves. **OK.**
2. **Una transacción (R25).** Todo `work` (`:488-571`) va dentro de `run_in_write_transaction`.
   - Ante cualquier excepción hay `rollback` y se relanza (`sql_server_repository.py:302-315`).
   - `work` es reentrante: no muta `lineas` (las plantillas se copian, `statements.py:468/494`) y numera sobre filas
     limpias.
   - `r31_*` fija los verbos `{SELECT, INSERT, UPDATE}` y los dos `UPDATE` exactos. Sin `DELETE`. **OK.**
3. **Reservas (R26).**
   - Los siete applocks van en el orden de design, compatible con F-006 (`_con` antes que `_log`), el clásico y
     `albaran-directo`.
   - E2-E7 y E11b llevan `UPDLOCK, HOLDLOCK` (`statements.py:140-155`). E5/E6 solo con `ctrprodes`/`mov`
     (`:506-507`); E11b al final; el `cod` se reserva dentro (`[6, 1, 14, "AC26/%"]`).
   - **Alta simultánea del escritorio:** en las claves no hay choque que pase sin detectarse. El `cod` tiene índice
     único `(emp, tip, cod)` y los `ide` de las seis tablas son «INDICE PRIMARIO Único» (`azure-apps/sigrid_tablas.md`):
     un choque da `IntegrityError` y se reintenta.
   - El `HOLDLOCK` de E7 cubre el rango de `pafhi` (`proide`, `almide`, `fechor`, `ide`): un `mov` del mismo par queda
     bloqueado hasta nuestro `COMMIT`. Lo residual, en O5. **OK.**
4. **Reintento (R27, decisión 12).** `_es_colision_de_clave` (`:951-954`) es la de F-006. Tres casos probados:
   - El reintento recalcula `cod`, `ide` y balance: `AC26/15954`, `dcapro` 8000021, `almcan` 22.
   - Agotados los reintentos: `colision_de_clave`, con `__cause__` `IntegrityError` y 4 cursores.
   - `RuntimeError`: sube tal cual, con 1 cursor. **OK** (ver O3).
5. **Relecturas (R28)**, E12 (`:552-566`).
   - Un fallo de cuadre lanza `filas_afectadas_inesperadas` dentro de `work`: hay `rollback` y no se reintenta.
   - El doble contesta con lo **realmente insertado** en el intento (`f009_dobles.py:271-273`).
   - Los seis casos cubren el exceso y el defecto. **OK** (ver O1).
6. **Sin `UPDATE` sin vinculadas (R20, H31, decisión 10)**: `if vinculadas:` (`:532`).
   - El test fija `dca.ctride` = CTR y `estados_contrato` `{}`.
   - E9 va por línea (`[[2.0, 9001], [3.0, 9001]]`). Los estados salen de E10, leído tras E9. **OK.**
7. **`mov` y `prepma` (R19, R21; O3 del lote B)**: `_construir` (`:742-763`).
   - El `mov` sale si y solo si `tipmov` = 1. `dcapro.prepma` es el de su `mov` o 0, encadenado con el `pre` escrito.
   - Los tests de O3 existen y pasan: `r19_mov_si_y_solo_si_*` (vinculada 0, `MA9999` 0, `XA9999` 1),
     `r21_prepma_encadenado_*` y `r19_el_mov_lleva_el_pre_escrito_*`.
   - El ε vive en `encadenar_balances` (lote B), y el caso de uso no compara por su cuenta. **OK** (ver O4).
8. **Devoluciones (R18, R20).** Probadas la vinculada y la sin vincular, en previa y en commit:
   - Regla A: `tip 1`/`oritip 5`/`destip 2`, `canent` < 0, `cansal` 0. `ctrprodes` y E9 llevan signo.
   - `servido_negativo` se acumula por `ctrpro`. `stock_negativo` sale del balance de **E7**, no del de L12.
   - Con stock 0 se conserva el PMP; `estser` pasa de 1 a 0 en commit y en previa; `totdoc` −38,12. **OK** (ver O2).
9. **Equivalencia (R33).** Se espía a los dos modos donde numeran (`monkeypatch`, el clásico sin tocar).
   - Mismas columnas y mismo orden.
   - Diferencia exacta: `dca.synckey`, `dcapro` {`prepma`, `refent`, `cod2`, `dncide`, `dncproide`} y `mov` {`fec`,
     `fechor`, `prepma`}. Todas declaradas en design §Equivalencia v8.2, y `DECLARADAS` rechaza cualquier otra.
   - Con la fecha de hoy solo queda `prepma`. **OK.**
10. **Tests y entorno.**
    - El doble reconoce el SQL **exacto** del constructor y falla con cualquier otro.
    - RED real en R26-R28, reproducida.
    - Ficheros prohibidos sin tocar e `init.sh` en verde. **OK.**

## Checkpoints

- **C1** [x] `init.sh` exit 0; ficheros del arnés presentes.
- **C2** [x] una `in_progress` · [x] rama correcta · [x] `current.md` al día (`699ba6f`) · [x] `history.md` (sin
  `done` nueva).
- **C3**
  - [x] Hexagonal: sin `pyodbc` en `application/`; `IntegrityError` se reconoce por nombre.
  - [x] Ruta en la primera línea. [x] Sin `print`, TODO ni secretos (el doble usa credenciales falsas y nombradas así).
    Sin dependencias nuevas.
  - [x] Base `ruesma`. [x] `cod`/`res`/`fec`/`tip`/`est` en `con`.
  - [x] Totales, `canser`, `estser/estfac` y `mov`/PMP recalculados. [x] `est` contra `conest`. [x] SQL con `?`.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] Requisitos del trozo trazados (tabla de cobertura) · [x] sin red ni BBDD · [x] manuales T19-T24 listados.
- **C4 bis**
  - [x] `rigor` `critico`. [x] RED de R26-R28 real y **reproducida**; T11 y T12 no la piden (R34). [x] Cobertura
    100 %.
  - N/A con motivo: mutación, muertos comprobados, coste por mutante, cabecera, RM1, RM2, RM5, RM6, campaña manual y
    supervivientes. Son T16, lote E, sobre la feature entera, por el plan aprobado; aquí solo el RM4 de arriba.
  - [x] «Evidencias» con los cuatro números (mutación «no medido», con su motivo).
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5**
  - [x] T10-T12 `[x]` con commits `F-009 T10:`/`T11:`/`T12:`. N/A el resto de `tasks.md`: la feature sigue abierta.
  - N/A sin trackear: `` `0`].{t `` es anterior y ajeno (anotado en el lote B). `review_F-009_loteC_1.md` es del otro
    reviewer, en curso.
  - [x] `features.json` al día.

## Cobertura (requisito → tests; `test_f009_use_case.py`, salvo R33)

| Req. | Tests |
|---|---|
| R18 | `r18_devolucion_vinculada_en_commit`, `r18_*_servido_en_negativo_*`, `r18_devolucion_sin_vincular_con_stock_negativo`, `r18_el_stock_negativo_se_decide_con_el_balance_de_dentro`, `r18_*_stock_a_cero_conserva_el_pmp`, `r18_la_devolucion_no_supera_lo_pendiente` |
| R19, R21 | `r19_mov_si_y_solo_si_tipmov_1_*`, `r19_el_mov_lleva_el_pre_escrito_en_la_fila`, `r21_prepma_encadenado_*` |
| R20 | `r20_sin_vinculadas_ningun_update_*`, `r20_servido_por_linea_y_estados_*`, `r20_una_devolucion_devuelve_estser_a_0`, `r20_en_la_previa_*` |
| R24 | `r24_demasiadas_lineas_*` (×2), `r24_en_el_tope_vale`, `r24_commit_sin_llaves_no_lee_nada` (×4), `r24_commit_en_una_base_no_permitida` (×2) |
| R25, R31 | `r25_el_albaran_entero_en_una_transaccion`, `r25_lo_insertado_es_lo_que_se_devuelve`, `r25_la_fila_dca_escrita_lleva_las_bancarias`, `r31_en_la_transaccion_solo_los_update_*` |
| R26 | `r26_reservas_bajo_bloqueo_*`, `r26_el_balance_sale_de_e7_*`, `r26_sin_mov_anterior_*`, `r26_serie_vacia_*`, `r26_sin_vinculadas_ni_mov_*` |
| R27 | `r27_reintenta_*_recalculando`, `r27_agotados_*_colision_de_clave`, `r27_otro_error_de_la_base_no_se_disfraza` |
| R28 | `r28_relecturas_por_clave`, `r28_si_no_cuadran_rollback_con_codigo` (×6) |
| R33 | `test_f009_equivalencia.py`: `r33_mismas_filas_*_salvo_las_declaradas`, `r33_con_la_fecha_de_hoy_*` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **O1.** No se comprueban las filas afectadas por E9/E11 (`:533-544`): un `UPDATE` que no toque ninguna fila de
  `ctrpro`/`ctr` pasaría. R28 no lo pide y el `ctrpro` se acaba de leer. Si se quiere, es una ampliación de spec.
- **O2.** `servido_negativo` y `supera_pendiente` se deciden con el `canser` leído **fuera** de la transacción
  (`:1259-1271`). Con un alta simultánea, el aviso podría no salir; lo escrito es correcto (E9 relativo).
- **O3.** El repositorio reintenta **toda** `IntegrityError` (NOT NULL, FK, CHECK; no solo 2627/2601): una fila mal
  construida acabaría en `colision_de_clave` con un «Reenvíalo» engañoso. El ERP queda intacto, y es comportamiento
  compartido con F-006 y el clásico. En T18, documentarlo; a futuro, filtrar por número de error en el repositorio.
- **O4.** No hay test de punta a punta del ε con residuo binario a través del caso de uso. Basta el de
  `encadenar_balances` (lote B): el caso de uso delega y M17 murió. Si se quiere blindar, en T16.
- **O5.** Concurrencia residual, la misma que en el clásico: E10 suma `ctrpro` sin bloquear las líneas que no toca
  (`estser` desfasado si el escritorio sirve otra línea en el mismo instante), y el escritorio lee su balance sin
  bloqueo (M10, N1). Se mira en la UI en T22.
- **O6.** Si el commit se hace y falla la respuesta, el llamante recibe un 500 con el albarán ya escrito. Lo cubre la
  idempotencia. En T13/T18, decirle a F-053 que ante un 500 reenvíe la misma `referencia_externa`.

**Automejora (propuesta, no aplicada).** En `.claude/agents/reviewer.md`, para rigor `critico` con la mutación diferida
a un lote posterior: exigir una muestra RM4 de mutantes manuales sobre el camino de escritura en cada trozo que escriba
en producción. Esta revisión la hizo con 15 mutantes, en unos 60 s de CPU.
