<!-- progress/review_F-009_loteC_1.md -->
Revisión completa (pasada 1) del trozo 1 del lote C (T7, T8 y T9), sobre HEAD `699ba6fa4814cec176cc204cb5700c7e1407157e`

# F-009 · Revisión del lote C, trozo 1 (T7-T9) · **Veredicto: APPROVED**

Alcance: `c4fb55b` (T7), `0ed5573` (T8), `d4e695d` (T9). T10-T12 (`65f4ae6`, `f60d9a5`, `1c10f72`) los revisa otro
reviewer. De ellos solo he mirado el diff del caso de uso `d4e695d..HEAD`: añade guardas de R24 y el cuerpo de `work`,
y no cambia ninguna regla de resolución, previa ni idempotencia de T7-T9 (solo renombra `_comprobar_prefijo` →
`_comprobar_guardas`, con el prefijo en el mismo orden).

## Nivel de rigor

`critico` (declarado en `harness/features.json`): fase RED en los requisitos centrales, cobertura ≥ 80 % de lo
cambiado, mutación con cero supervivientes y manuales listados. En este trozo, RED de R11, R13b, R14 y R15 (T7) y de
R30 (T8); T9 no la pide (R34). **Mutación N/A justificada**: es T16 (lote E), sobre la feature entera, según el plan
que el humano aprobó en la PARADA 1, igual que en el lote B.

## Verificación propia

- `bash harness/init.sh`, tal cual: `2284 passed, 1 skipped`; `PUERTA COBERTURA: 100.0% de 1042 líneas` `[OK]`;
  `PUERTA TAMAÑO` `[OK]`; `ENTORNO LISTO`.
- **RED de T8 reproducida al pie de la letra**: en una copia (`git archive 0ed5573`) con el caso de uso de `c4fb55b`,
  `-k "r29 or r30"` da `16 failed, 1 passed, 88 deselected`, como el informe. **RED de T7**: la traza (`85 failed,
  1 deselected`; `58 failed, 28 deselected`) es de un estado intermedio. En `c4fb55b` salen 86/2 y 59/29 porque luego
  se añadieron un test de R22 y otro del filtro. Es el mismo caso que la O4 del lote B y no bloquea.
- **Sin SQL fuera del constructor**: el caso de uso no contiene ni `SELECT`, ni `INSERT`, ni `UPDATE`. El doble
  (`tests/f009_dobles.py:92-104`) rechaza cualquier SQL que no sea el exacto de `AlbaranCompraStatements`, y los tests
  fijan los parámetros de cada lectura.
- `git diff --stat bee6716..d4e695d`: solo el caso de uso, `tasks.md`, `f009_dobles.py` y `test_f009_use_case.py`.
  Hasta HEAD siguen intactos el clásico, `albaran-directo`, `domain/`, `infrastructure/` (con `security/`), `config/`,
  `function_app.py` y el contrato. En el dorado, `git log` solo da `783f2d1` y `91b929d` (T1). `.env` no está
  versionado, y `ruff check` sale limpio en los tres ficheros.
- Credenciales: las cinco lecturas del repositorio (`execute_read_query`, `read_full_row`, `read_rows_by`,
  `peek_next_ide`, `locate_contract`) usan `_read_credentials()`. La previa no llama a `run_in_write_transaction`.
- Sondas en el scratchpad (sin `__pycache__`; el árbol queda limpio):
  - El producto `ma9999` da `producto_no_permitido`.
  - La partida `01.0a` se resuelve contra la fila `01.0A`, y lo mismo la naturaleza `ma99` y la `caa` `0404.cdsb37`.
  - La clave de mapeo `ma9999` da `naturaleza_no_valida`.
  - Un `ivaide` que no está en `dbo.iva`, con `commit:true`, da `ValueError` antes de abrir la transacción.

## Lo pedido, punto por punto

1. **Reglas de resolución.** Todas cuadran con la spec v8.2 y con el contrato §2.3/§4.1:
   - La obra se busca por empresas (`:350-373`).
   - El contrato es el del localizador, solo los de esa obra (`:375-406`).
   - La plantilla se busca en la empresa de la obra, por `entide` o por CIF (`:293-335`). Sin contrato, el `entide`
     sale de la `dca` plantilla (decisión 2).
   - Almacén y centro salen de la misma fuente, y un error ahí corta antes de mirar las líneas (`:652-675`,
     decisión 3).
   - Vinculadas: `ctrpro or ctr` (`:1072-1092`).
   - Sin vincular: lista blanca → maestro → naturaleza (`numemp` ∈ {0, emp}, `fecbaj` 0) → la única `cua` → la `caa`
     `<obra>.<sufijo>` del centro (`:1021-1064`).
   - Partidas: solo imputables, y el `paride` de R14b (`:1137-1168`).
   - Precio: la **misma** `usa_precio_del_contrato` decide la fila (`albaran_compra_statements.py:534`) y el aviso
     (`:1254`).
   - Los fallos de línea se acumulan (`:605-650`). Los avisos salen en este orden: partida, precio, seguimiento, IVA
     o histórico, y al final `stock_negativo` (`:1272`, `:875`).
   - Decisión 1: con la lista vacía y la obra existente, `obra_de_empresa_no_permitida`. Sin la obra en ninguna
     empresa, `obra_no_encontrada`, que también encaja con §3.3.
   - La O3 del lote B queda cubierta (`r19_mov_si_y_solo_si_tipmov_1_…`, `r21_prepma_encadenado_…`).
2. **Decisión 7 (el `ivaide` que no está en `dbo.iva` da `ValueError`, un 400 de texto): se queda así, sin código
   nuevo.**
   - §3.4 del contrato ya lleva el 400 de texto libre a `error` en F-053, el mismo destino que los fallos de maestro
     con código (`naturaleza_no_valida`, `producto_no_encontrado`). El design §Sentencias trata igual lo ilegible
     (`truncado`), y la plantilla ilegible (`:315`) también.
   - Un 500 («lo inesperado» de R9) sería peor. En grabación es `incierto`: F-053 reenviaría, aunque no se ha escrito
     nada (falla en `completar`, antes de `_escribir`), y el reenvío fallaría igual.
   - Ningún código de §3.3 dice «IVA inexistente». Reutilizar uno engañaría al panel de sv4, y escribir IVA 0 sería un
     error fiscal silencioso. Ver O2.
3. **Decisión 8 (comparación sin mayúsculas): es coherente.**
   - Las `IN (…)` ya filtran con `Modern_Spanish_CI_AS`. `_clave` (`:71-74`) replica en Python lo que el SQL devolvió;
     sin `casefold` se descartarían filas que el ERP da por iguales. Es el criterio de F-006
     (`create_partes_reclamacion_use_case.py:81`) y respeta los acentos, como `_AS`.
   - En seguridad no abre nada: lista blanca, mapeo y prefijo son exactos sobre el texto pedido, más estrictos que el
     ERP. Además, el índice único CI `(emp, tip, cod)` impide que el SQL devuelva otro producto.
   - **Pero no la fija ningún test** (O1).
4. **Idempotencia.**
   - La RED de R30 es real (reproducida arriba).
   - En la previa, L11 va tras la plantilla y antes de `conest`/`usu`, como en §4.1.
   - En commit, si la referencia ya aparece fuera, sale sin abrir transacción (el test comprueba `transacciones ==
     []`). Si no, E1 es la primera sentencia de `work`, bajo `SIGRID_REFEXT_14`.
   - La respuesta `idempotente` sigue §3.1 y §6.d: `committed` false, `dry_run` = `not commit`, `cod` recortado,
     `totales {totbas, totdoc, n_lineas}`, líneas por `pos` con `indice` desde 0 y `referencia_linea` de `refent`
     recortado, sin avisos ni filas.
5. **Dry-run.** Solo lecturas, con credenciales de lectura: un test comprueba los tipos de llamada y que no se abre
   ninguna transacción. Las columnas bancarias las quita el propio modelo (`albaran_compra_models.py:358-365`) de
   `cabecera` y `filas.dca`, y el test las busca en el JSON volcado. El preview viene completo: seis filas numeradas
   y enlazadas, `cod_provisional` con L14 y `peek` de las cinco tablas, y el balance de L12 por producto y almacén.
6. **Tests y ficheros.** Los tests no tocan red ni BBDD y comparan SQL y parámetros. No se ha tocado nada prohibido, e
   `init.sh` sale en verde.

## Checkpoints

Fuera de este trozo, porque son del cierre de la feature: en C2, `current.md` y `history.md`; los manuales de C4; los
puntos de campaña de C4 bis (RM1-RM6, totales y tiempos; T16); y el resto de C5 (`tasks.md`, con T13-T25 abiertas).

- **C1** [x] `init.sh` termina con exit 0 · [x] están los ficheros del arnés.
- **C2** [x] solo F-009 está `in_progress` · [x] la rama es `feature/F-009-alta-albaran-compra`.
- **C3** [x] Hexagonal: `application` importa solo `application` y `domain` · [x] primera línea con la ruta · [x] sin
  `print`, TODO, secretos (la credencial del doble es ficticia) ni dependencias nuevas · [x] base de la petición y
  nada contra `ruesma_rep` · [x] `cod/res/fec/tip/est` en `con` · [x] estado contra `dbo.conest` (L13) · [x] SQL con
  `?`. Lo recalculado es de T10 (lo revisa el otro reviewer).
- **C3 bis** N/A: el trozo no toca ningún fichero de `docs/referencia/`.
- **C4** [x] cada requisito tiene su `test_f009_rN_*` y pasa (tabla de abajo) · [x] sin red ni BBDD.
- **C4 bis** [x] `rigor: critico` declarado · [x] RED de T7 y T8 con la traza real · [x] cobertura `[OK]` al 100 % ·
  mutación N/A justificada (T16, arriba) · [x] «Evidencias» con los cuatro números; la de mutantes dice «no medido,
  T16» con su motivo, y sin campaña no hay workers que declarar.
- **C4 ter** N/A: no existe `harness/rutas_sensibles.json`.
- **C5** [x] T7-T9 están `[x]`, cada una con su commit `F-009 Tn:` · [x] `features.json` dice `in_progress` · [x] el
  lote no deja artefactos nuevos (el fichero sin seguimiento de la O6 es anterior y ajeno).

## Cobertura (requisito → tests de `tests/test_f009_use_case.py`)

| Req. | Tests |
|---|---|
| R7 | `r7_superconjunto_de_la_respuesta_clasica`, `r7_sin_columnas_bancarias_…`, `r7_avisos_con_codigo_y_warnings_en_orden` |
| R9 | `r9_se_validan_todas_las_lineas_…`, `r9_un_error_de_cabecera_corta_…`, `r9_con_fallos_no_se_leen_…` |
| R11 | `r11_obra_por_empresa[4]`, `r11_contrato_del_localizador_…[3]`, `r11_con_emp_es_la_empresa_de_la_obra`, `r11_sin_contrato_la_plantilla_es_por_cif_…` y 8 más |
| R12 | `r12_linea_que_no_es_del_contrato`, `r12_vinculada_toma_del_ctrpro_…`, `r12_varias_al_mismo_ctrpro_no_se_suman`, `r12_supera_pendiente_…`, `r12_tipmov_…` |
| R13/R13b | `r13_*` (8), `r13b_naturaleza_no_valida[9]`, `r13b_naturaleza_cuenta_y_analitica_del_mapeo` y 2 más |
| R14/R14b | `r14_partida_imputable_…`, `r14_sin_partida_es_paride_0_…`, `r14_partida_que_no_vale[5]`, `r14b_paride_desambigua`, `r14b_paride_no_valido[4]` |
| R15 | `r15_*` (9 tests): las tres fuentes de almacén, `almacen_de_obra_no_resuelto[2]` y `analitica_no_resuelta[5]` |
| R16/R17 | `r16_*` (3) y `r17_*` (7), incluidos la opción C y el IVA inexistente |
| R23 | `r23_la_previa_no_necesita_ninguna_llave_…`, `r23_cod_e_ide_provisionales_…`, `r23_las_seis_filas_…` y 3 más |
| R29 | `r29_referencia_no_permitida_sin_leer[6]`, `r29_vale_cualquiera_de_los_prefijos` |
| R30/R30c | `r30_*` (8 tests): previa, orden, conflicto[3], y dentro y fuera de la transacción; `refent` en `_comprobar_idempotente` y en `r23_las_seis_filas` |

## Observaciones (no bloquean; la O1 y la O2, antes de T16)

- **O1 · Ningún test fija la decisión 8.** Comprobado con RM4: en una copia sin `.casefold()` en `_clave` (`:74`),
  los dos ficheros de tests siguen en verde (`157 passed`). Sería un superviviente seguro de T16, en `critico`. Hay
  que añadir:
  - un test con la fila de L6 `01.0A` frente a la petición `01.0a`;
  - otro con la naturaleza o la `caa` en minúsculas;
  - y conviene uno de la lista blanca exacta: `ma9999` da `producto_no_permitido` sin leer `productos`.
- **O2 · Decisión 7.** El `ValueError` se queda, pero su mensaje (`:1193`) solo dice el `indice`: hay que añadirle la
  `referencia_linea`. Además, en T18 (`azure-apps/sigrid_api.md`) hay que escribir que el 400 de texto libre también
  cubre un maestro incoherente: IVA inexistente o plantilla ilegible.
- **O3 · Decisión 5: una línea puede salir varias veces en `details.lineas`** (en `r9_…`, la de índice 3). La forma
  no cambia, pero §3.3 y §6.e enseñan un elemento por línea. **Para el líder**: confirmar con F-053 que no indexa por
  `referencia_linea`, porque perdería el código `error` que gana por H25, y escribirlo en T18.
- **O4 · `producto` es `null` en las vinculadas** (decisión 4), y §3.1 lo define como «código del producto». La forma
  no cambia y sv9 no casa por ese campo, pero hay que reflejarlo en T18.
- **O5 · `idempotente` pone `fec` en `cabecera = {"fec": …}`** (decisión 9), cuando en las otras respuestas `cabecera`
  es la fila `dca`, que guarda la fecha en `fecdoc`. No hay forma nueva y sv9 no guarda `cabecera` (F-053 R16), pero
  hay que documentarlo en T18.
- **O6 · El fichero `` `0`].{t `` está sin seguimiento en la raíz**: 0 bytes, del 2026-09-24 y ajeno a F-009. Lo decide
  el humano antes del cierre (C5).
- **O7 · Un `ctrpro` cuyo producto no aparece en L7b se queda sin `mov` y sin aviso** (segunda parte de la decisión
  7). Con `proide` 0 tiene sentido; con un `pro` borrado, el stock no se movería y nadie se enteraría. Para T22 o para
  T18.

**Automejora (propuesta, no aplicada).** Añadir al paso 5 de §Protocolo en `.claude/agents/reviewer.md`: «Toda decisión
de interpretación del implementer que cambie un resultado observable tiene un test que falla sin ella, y el reviewer
lo comprueba con un mutante sobre una copia (RM4)». La O1 solo salió porque la busqué a mano.
