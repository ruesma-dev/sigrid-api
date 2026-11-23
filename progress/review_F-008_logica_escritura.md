<!-- progress/review_F-008_logica_escritura.md -->
Revisión completa (pasada 1) · trozo `logica-escritura` · HEAD `2879ddb` · diff `ccfb334...HEAD`

# F-008 · Revisión troceada (T21): lógica de escritura

- **Veredicto:** CHANGES_REQUESTED (un cambio pequeño y una corrección de texto; la lógica de transacción es sólida).
- **Nivel de rigor:** `critico` (declarado). Este trozo no juzga RED, cobertura ni mutación (otros revisores).
- **Alcance:** R36-R47 y design §6-§8 contra `create_factura_use_case.py`, `factura_statements.py`, la ruta de
  `function_app.py`, `test_f008_{transaccion,statements,route}.py` y `tests/f008_dobles.py`.
- **Ejecutado:** `pytest tests/test_f008_transaccion.py tests/test_f008_statements.py tests/test_f008_route.py`, con
  **123 passed**. No he ejecutado `init.sh` ni la suite completa, por la regla de convivencia. Sin red y sin tocar el árbol.
  Una sonda sobre el doble, en el scratchpad (ver O1).

## Cambios requeridos

1. **Estado del pago hardcodeado.** Incumple C3 («Estados nunca hardcodeados: se resuelven contra `dbo.conest`»).
   - Dónde: `factura_statements.py:142-143`. `construir_con_pago` escribe `est=1` (PDT) como literal.
   - Lo raro: `leer_estados()` ya lee los `conest` del `tip 25` (`factura_statements.py:560-562`), pero
     `_estados` (`create_factura_use_case.py:368-380`) no exige `(25, "PDT")` y nadie usa ese dato.
   - Escenario de fallo: si PDT no vale 1 en otra base o empresa, o lo renumeran, los `con 25` nacen en un estado
     ajeno y nadie lo detecta. Los `con` 15 y 14 sí van contra `conest`.
   - Cambio pedido:
     - Añadir `(TIP_PAGO, "PDT")` a `necesarios` en `_estados`. Si falta, `estado_inicial_no_encontrado`.
     - Pasar `est` a `construir_con_pago` como parámetro, desde `ctx.estados`, en `create_factura_use_case.py:825`.
     - Añadir un test con PDT distinto de 1 en el doble, para ver que se escribe el de `conest`, y otro con PDT
       ausente.
2. **Corregir la justificación de la Desviación 4** (`progress/impl_F-008.md:82` y `:57`). Dice que con `NOCOUNT ON`
   «`rowcount` no sirve», y es cierto para `cursor.rowcount`. Pero `SELECT @@ROWCOUNT` en el mismo lote **sí
   funciona** con `NOCOUNT ON`. Hay que elegir una de dos:
   - (a) dejar las relecturas y reescribir la justificación. Debe decir que R40 lo garantiza el `UPDLOCK, HOLDLOCK` de
     EF1/EF2, y que la relectura comprueba el estado final, no las filas afectadas (ver O1);
   - (b) pasar EM1-EM3 a `UPDATE ...; SELECT @@ROWCOUNT` y exigir 1.

   Me vale cualquiera de las dos. Lo que no vale es dejar escrito un motivo técnico falso en una feature `critico`.

## Hallazgos no bloqueantes (observaciones)

- **O1 · Las relecturas ER9/ER10/ER11 no distinguen «lo marqué yo» de «otro dejó el mismo valor».** Lo he medido en
  el doble: si antes de `marcar_linea` el «escritorio» pone `canfac = can`, el `UPDATE` no afecta a ninguna fila, la
  relectura `canfac = can` da 1 y la factura sale `creado` (sonda `sonda_er9.py`: `estado: creado canfac 2.0 can
  2.0`). En SQL Server real **no es explotable**: EF2 (`factura_statements.py:440-443`) y EF1 (`:435-439`) dejan
  `U` sobre esas filas hasta el COMMIT, y otra sesión no puede escribirlas. R40 se cumple por el bloqueo, no por la
  relectura. Ver el cambio 2.
- **O2 · EF2 bloquea `dcapro` por `docide`** (`WITH (UPDLOCK, HOLDLOCK) WHERE p.docide IN ...`). Es un patrón nuevo en
  el repo: F-009 solo bloquea por `ide` o `MAX(ide)`. El diccionario no dice que `dcapro.docide` tenga índice. Si
  no lo tiene, el escaneo toma bloqueos de rango sobre toda `dcapro` mientras dura la transacción, y el escritorio
  no podría grabar líneas de albarán en ese rato. Se pide comprobarlo **solo leyendo** `sys.indexes`, en T22/T23,
  antes de la grabación de T24.
- **O3 · Desbordamiento de la serie FRGG (4 cifras).** Después de `FRGG26/9999`, `siguiente_cod` produce
  `FRGG26/10000`. EF3 lo excluye por `LEN`, así que cada intento vuelve a 10000. El resultado es un choque, los
  reintentos y `colision_de_clave`, con el ERP intacto. Falla de forma segura; queda anotado por si el volumen de
  FRGG se acerca a ese límite.
- **O4 · Cualquier `IntegrityError` acaba en `colision_de_clave`** tras los reintentos (`create_factura_use_case.py:
  934-941`), incluidos NOT NULL y FK. El patrón viene heredado de F-009 y el ERP queda intacto, pero el mensaje
  engaña.
- **O5 · Un `dca` con `estfac` ≠ 0 y líneas a `canfac` 0** pasa R15, hace que EM2 no afecte a ninguna fila y
  termina en ROLLBACK con `filas_afectadas_inesperadas` (lo cubre `test_f008_r41_r42_..._revierte_todo[marcar_cabecera]`).
  Falla de forma segura; el código de error no explica el motivo.
- **O6 · Lo que se resuelve fuera de la transacción no se relee bajo bloqueo:** la cabecera heredada de la `dca`,
  la retención `dcarec` y las `anteriores` (LF10). Si cambian entre la previa y el commit, se copia la versión
  anterior. Es una ventana mínima y el diseño no lo pedía.

## Requisitos → cumplimiento → test que fallaría

| R | ¿Se cumple? | Test que lo prueba |
|---|---|---|
| R36 una transacción y sus tablas | Sí. Todo dentro de `work`; cualquier excepción provoca ROLLBACK (`sql_server_repository.py:358-363`) | `test_f008_r36_r37_fr_de_mes_...`, `r36_sin_origenes_...`, `r36_frgg_con_albaran_...`, `r31_retencion_inserta_su_dcfrec_...` |
| R37 applocks en orden, `cod` MAX+1, cifras, reintento, `colision_de_clave` | Sí. Las applocks compartidas con F-009 (`_con`, `_log`) van en el mismo orden relativo: no hay interbloqueo entre rutas | `r37_orden_de_las_sentencias`, `r37_applocks_en_su_orden_fijo`, `r9_un_prefijo_no_casa_...`, `r37_choque_de_clave_se_reintenta_desde_cero`, `r37_choques_agotados_...`, `r37_reserva_tras_otra_factura_...` |
| R38 lista blanca y valores de `consii` | Sí. `_insertar` exige el conjunto exacto de columnas | `r38_insert_por_lista_blanca`, `r38_una_fila_que_no_es_la_lista_blanca_...`, `r38_consii_con_los_valores_medidos`, `r38_dcf_*` |
| R39 sin contabilidad, sin DELETE, sin salir de REC | Sí. Hay un detector probado contra casos prohibidos y aplicado también a lo que ejecuta de verdad un commit | `r39_el_detector_caza_lo_prohibido`, `r39_ninguna_constante_...`, `r39_todas_las_que_corren_en_un_commit_...` |
| R40 marca de línea condicionada | Sí, por el bloqueo; la relectura es de estado (O1) | `r40_marca_de_linea_condicionada_a_canfac_cero`, `r40_carrera_en_la_marca_de_linea_revierte_todo`, `r15_linea_facturada_por_el_escritorio_bajo_bloqueo` |
| R41 `dca` y CON→FAC, sin `idefac` | Sí | `r41_marca_de_cabecera_sin_idefac`, `r41_de_con_a_fac`, `r40_r41_marcas_de_un_albaran_de_mes`, `r41_r42_..._revierte_todo` |
| R42 `ctrpro` y `ctr.estfac` | Sí. EF4 bloquea antes de sumar; las sumas se hacen con agregado sin GROUP BY (siempre una fila) | `r42_contrato`, `r42_linea_vinculada_suma_al_ctrpro_...`, `..._revierte_todo[sumar_contrato]` |
| R43 idempotencia y duplicadas, también bajo el applock | Sí. Va antes que los orígenes, dentro y fuera | `r43_idempotente_bajo_el_applock`, `r43_conflicto_y_duplicada_bajo_el_applock`, `r43_la_misma_peticion_otra_vez_...` |
| R44 respuesta | Sí: `_resultado` y `_resultado_idempotente` | `r36_r37_fr_de_mes_...`, `r37_como_dict_de_la_respuesta` |
| R45 relectura antes del COMMIT | Sí. Cuenta por clave las 8 tablas y cada marca | `r45_relectura_que_no_cuadra_revierte` (6 casos), `r45_relecturas_por_clave` |
| R46 traza sin datos | Sí. Solo códigos; las excepciones se trazan por su tipo | `r46_traza_sin_datos_sensibles`, `r46_traza_de_un_fallo_de_lineas_solo_con_codigos` |
| R47 compatibilidad | Sí. El diff no toca `albaran_compra_statements`, `create_proforma`, `create_albaran_compra`, `infrastructure/` ni el puerto | `test_f008_r47_*` (settings); la suite ajena la cubre otro trozo |
| R1/R4 (en la ruta) | Sí. El 400 propio no lleva `input` ni `ctx`; la llave va después del cuerpo y antes del caso de uso, y solo la abre el `true` | `r1_cuerpo_invalido_sin_eco_ni_codigo`, `r4_*` (4 tests) |

Otras comprobaciones:

- Numeración: `pos` múltiplo de 64, `dcaprodes.lindeside` = el `ide` de su `dcfpro` (las de origen van primero) y
  `pag.ide` = `con.ide`.
- Anchos de columna comprobados en `azure-apps/sigrid_tablas.md`: `dcf.entref`, `pag.entref` y `synckey` son de 128,
  `consii.desope` de 500 y en `dcfpro` `res` es de 128 y `unimed` de 8. No hay truncados que hagan eco de valores.

## Juicio de las «Decisiones» y las «Desviaciones» 3-5 (`progress/impl_F-008.md`)

- **Idempotencia antes que los orígenes:** correcta. Sin ella, repetir una petición daría `origen_ya_facturado`.
- **Retención antes que los totales; abono antes de comparar:** correcto, porque la cuota entra en `tot`.
- **Comprobaciones repetidas bajo `UPDLOCK, HOLDLOCK`:** correctas. Es lo que de verdad sostiene R40 y R41.
- **Duplicadas sin filtrar por empresa:** aceptada. El error va en la dirección segura (bloquea de más, nunca
  duplica).
- **Cambios de T20:** comprobé las guardas que se quitaron (RM6). Las sumas del contrato, E10, son
  `SUM` sin GROUP BY, así que siempre devuelven una fila; `estados_contrato` trata el NULL; `_contar` lee
  agregados. El `assert` de `vencimiento_retencion` lo garantiza `_montar`. Ninguna se quitó sin su invariante.
- **D3 (UPDATE parametrizados):** aceptada. Es más estricta que el diseño.
- **D4 (relecturas en vez de `rowcount`):** aceptada como mecanismo, pero su justificación es incorrecta. Ver el
  cambio 2 y O1.
- **D5 (400 propio de la ruta):** aceptada y necesaria. `_respuesta_factura_invalida` emite `loc`, `type` y `msg`.
  Los `msg` del `model_validator` no citan valores del llamante.

## Checkpoints de este trozo

- [ ] **C3 · «Estados nunca hardcodeados»:** el `con 25` lleva `est=1` (cambio 1). Ese punto lo marco aquí porque
  afecta a una escritura. El resto de C3 es de otro revisor.
- [x] **C3 · SQL parametrizado con `?`:** lo verifica el detector `_LITERAL` sobre las 53 constantes y sobre lo que
  se ejecuta de verdad.
- [x] **C3 · `cod/res/fec/tip/est` en `con`:** los `UPDATE` de estado van a `con`; los de `dca` solo tocan
  `estfac`, `fecfac`, `horfac` y `antestfac`.
- [x] **C3 · «Nada se recalcula solo»:** `canfac`, `estfac` del `dca` y del `ctr` y CON→FAC van en la misma
  transacción. No hay `mov`, porque la factura no mueve stock.
- [x] **C4 (parcial) · los R36-R47 de este trozo tienen test que fallaría:** ver la tabla.
- [x] **C4 · los tests no tocan red ni BBDD:** el doble `f008_dobles.py` contesta por nombre de sentencia y, ante
  cualquier excepción, devuelve el `Mundo` a su copia.
- N/A **C1, C2, C3 bis, C4 bis (RED, cobertura, mutación, RM1-RM5), C4 ter y C5:** fuera de este trozo por el
  encargo del líder; los juzgan los otros seis revisores.

## Propuesta de automejora (no aplicada)

Añadir a `CHECKPOINTS.md` C3, dentro de «Estados nunca hardcodeados», esta línea: «también los de los documentos
auxiliares que crea el alta (pagos `tip 25`, etc.), no solo el del documento principal». Ya se escapó aquí,
aunque la lectura de `conest` del `tip 25` estaba hecha.
