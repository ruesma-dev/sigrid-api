<!-- specs/F-006-alta-parte-reclamacion/requirements.md -->
# F-006 · Requisitos

**`POST /api/sigrid/partes-reclamacion`: crear en lote partes de reclamación de
Posventa (`con.tip 708`, serie `RS<aa>.<mm>/`) como los crea el escritorio de Sigrid.**

## Preguntas abiertas para el humano (bloquean la aprobación, no la redacción)

Las decisiones del 2026-09-24 se mantienen; la medición (`progress/explore_F-006_modelo_parte.md`, «§») deja cuatro:

- **Q1 · Referencia externa en `RCPCLI` con prefijo.** El «Nº Referencia Externo» del importador
  es `conext.cod='RCPCLI'` (`varchar(80)`, §5), **ya en uso**: promotor (≈4.080, `V#I2021…`) y notas
  (`OK`, «según proyecto»). Propuesta: usarlo **con prefijo obligatorio del llamante**
  (`SIGRID_RECLAMACION_PREFIJOS_REFERENCIA`, p. ej. `PVI-`); un parte de la API no podrá llevar
  además la del promotor. Alternativa: `con.doc` (vacío al 100 %, indexado, invisible en la ficha).
- **Q2 · `rcp.rcptip`** (forma de comunicación): medidos 0 (importador), 1 («Escrita») y 3 (portal,
  arrastra `conext` `02`/`03`). Propuesta: 0 por defecto, informable entre `{0, 1}`.
- **Q3 · Fila de alta en `dbo.log`**: la escribe el escritorio (94/94), no el portal (0/14).
  Propuesta: escribirla, con el `usu` de la petición.
- **Q4 · UPV de prueba**: la obra 0404 no tiene UPV ni oficios (§7); Posventa elige una UPV real. El
  parte se anula en la UI (NO PROCEDE **sin** correo), nunca con `DELETE`; si el propietario usa
  el portal, lo verá mientras exista.

## Contrato y configuración

**R1.** CUANDO llegue `POST /api/sigrid/partes-reclamacion` con `x-functions-key` y JSON con
`database`, `obra` (código, ≤24), `usu` (≤24), `commit` (defecto `false`) y `partes` (lista
≥1), cada parte con `referencia_externa` (1-80, obligatoria), `unidad_postventa` (código,
≤24), `descripcion` (1-128), `oficio` (código, ≤24) y opcionales `descripcion_larga`, `tipo`
(código, **defecto `"0002"`**), `clase` (código), `ubicacion` (≤48), `forma_comunicacion`
(`0`|`1`, defecto 0) e `intervinientes` (0-10 de `{oficio, proveedor?, causante=false}`),
el sistema debe validarlo con Pydantic (`extra="forbid"`) y responder 400 `Solicitud
invalida.` ante campo ausente, longitud excedida o valor fuera de dominio. El cliente NO
envía `ide`, `cod`, `emp`, `est` ni `pos`.

**R2.** El sistema debe responder con la misma forma en dry-run y en commit: `ok`, `committed`,
`dry_run`, `database`, `obra {ide, cod, emp}`, `resumen {creados, idempotentes, previstos,
rechazados, no_procesados}`, `avisos` y `partes[]` con `indice`, `referencia_externa`, `estado`
(`previsto`|`creado`|`idempotente`|`rechazado`|`no_procesado`), `ide`, `cod`, `motivo {codigo,
mensaje}` o null, `filas` (preview) y `avisos`. Un lote con partes rechazados responde **200**.

**R3.** SI falla una validación **del lote** (ninguna escritura), ENTONCES el sistema debe
responder 400 `{ok:false, error, details:{type, codigo}}` con `codigo` en:
`escritura_reclamaciones_deshabilitada`, `base_de_datos_no_permitida`, `lote_demasiado_grande`,
`obra_no_encontrada`, `usuario_no_valido`, `serie_no_encontrada`, `estado_inicial_no_encontrado`
(`database` fuera de `ALLOWED_WRITE_DATABASES`, **o esa lista vacía**, es `base_de_datos_no_permitida`).
Lo inesperado fuera de un parte sigue en 500 con `details.exception`.

**R4.** El sistema debe leer cuatro App Settings nuevas con defecto seguro: `SIGRID_RECLAMACION_WRITE_ENABLED=false`,
`SIGRID_RECLAMACION_MAX_PARTES=50`, `SIGRID_RECLAMACION_PREFIJOS_REFERENCIA=[]`, `SIGRID_RECLAMACION_PRESUPUESTO_SEGUNDOS=150`.

**R5.** Ninguna App Setting existente cambia; `ALLOWED_WRITE_DATABASES` sigue en `["ruesma"]`; no se toca `infrastructure/security/`.

## Validación por parte (lecturas comunes de la obra, una vez por lote)

**R6.** El sistema debe resolver una vez por lote, con lecturas: la serie `RS<año2>.<mes>/`
en `dbo.sercon` (`tip 708`, `act 1`; de ella `emp`, `tam` y `estini`), el estado inicial en
`dbo.conest` (`tip 708`, `est = estini`), la obra por `(emp, tip 42, cod)`, el `usu` en
`dbo.usu`, las UPV de la obra, sus `obrofc` con códigos de oficio y proveedor, y los
catálogos `auxtrcp`, `auxrcp` y `auxofc`. Estado y `emp` **no** se escriben a mano en el
código: salen de `sercon`/`conest` (ARCHITECTURE §7).

**R7.** SI un parte falla su validación, ENTONCES el sistema debe marcarlo `rechazado`
con `motivo.codigo` en: `referencia_no_permitida` (sin prefijo admitido),
`referencia_duplicada_en_lote`, `referencia_en_conflicto`, `unidad_postventa_no_encontrada`
(no existe o no es de la obra), `tipo_no_valido`, `clase_no_valida`,
`oficio_no_esta_en_la_obra`, `interviniente_no_esta_en_la_obra`, `interviniente_ambiguo`,
`interviniente_repetido`, y seguir con los demás partes.

**R8.** El sistema debe exigir que `oficio` exista en `auxofc` **y** en algún `obrofc` de la
obra (medido: 99 %), y resolver cada interviniente contra los `obrofc` de la obra por código
de oficio y, si viene, de proveedor: 0 filas → `interviniente_no_esta_en_la_obra`; varios
proveedores distintos → `interviniente_ambiguo`; varias filas idénticas `(oficio, proveedor)`
→ la de menor `pos` con aviso; el mismo `obrofc` dos veces → `interviniente_repetido`. Si el
oficio del parte no está entre los intervinientes, solo aviso.

## Dry-run, commit e idempotencia

**R9.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas con credenciales
de lectura y devolver, por parte válido, `estado:"previsto"` con las filas completas de
`con`, `rcp`, `rcpint`, `conext` y `log`, `cod`/`ide` provisionales (consecutivos dentro del
lote) y el aviso de que se reservan de nuevo en el commit; `committed:false`.

**R10.** CUANDO `commit` sea `true`, el sistema debe exigir `SIGRID_DOMAIN_WRITE_ENABLED`,
`SIGRID_RECLAMACION_WRITE_ENABLED` y credenciales de escritura; si falta alguna,
`escritura_reclamaciones_deshabilitada` antes de leer nada.

**R11.** El sistema debe escribir **cada parte en su propia transacción**
(`run_in_write_transaction`), en este orden: `con`, `rcp`, `rcpint` (0..N), `conext`
(`RCPCLI`) y `log` (alta), con las columnas y constantes de `design.md` §Filas (todas
explícitas: ninguna tiene DEFAULT). Un parte que falla revierte **solo** sus filas.

**R12.** Dentro de cada transacción, bajo `sp_getapplock` y con `WITH (UPDLOCK, HOLDLOCK)`, el
sistema debe reservar: el `cod` como `MAX(cod)` del prefijo del mes (`emp`, `tip 708`) + 1
con 4 dígitos; `con.ide`, `rcpint.ide`, `conext.ide` y `log.ide` como `MAX(ide)+1`; y
`rcp.pos` como `MAX(pos)+64` global. SI el siguiente número pasa de 9999, ENTONCES
`numeracion_agotada`.

**R13.** SI el `INSERT` choca con una clave única (alta simultánea desde la UI: índice
`(emp, tip, cod)` o `ide`), ENTONCES el sistema debe revertir y **repetir la transacción
entera** recalculando `cod`, `ide` y `pos`, hasta `DOMAIN_WRITE_MAX_RETRIES`; agotados,
el parte queda `rechazado` con `colision_de_clave` y el lote sigue.

**R14.** Antes del `COMMIT`, el sistema debe revalidar que la UPV y cada `obrofc` siguen
siendo de la obra, y releer por clave las filas escritas (`con` por `(emp, tip, cod)`,
`rcp`, `rcpint` por `rcpide`, `conext` por `(conide, cod)`, `log` por `ide`); SI algo no
cuadra, ENTONCES `ROLLBACK` y `filas_afectadas_inesperadas`.

**R15.** CUANDO ya exista un parte `tip 708` de la misma `emp` con `conext RCPCLI` igual a la
referencia **y de la misma UPV**, el sistema debe devolverlo como `idempotente` (su `ide` y
`cod`) sin escribir. Se busca en dry-run con lecturas y en commit **dentro** de la
transacción, bajo un applock de referencias. Si coincide con un parte de otra UPV o con más
de uno → `referencia_en_conflicto`.

**R16.** El sistema debe calcular `fec`, `hor` (Europe/Madrid) y `tiemod` (fecha OLE en UTC)
una sola vez por parte, fuera de la transacción, y usarlos en todos sus reintentos.

**R17.** SI el tiempo del lote supera `SIGRID_RECLAMACION_PRESUPUESTO_SEGUNDOS`, ENTONCES el
sistema no debe empezar más partes y debe marcar los restantes `no_procesado`
(`presupuesto_de_tiempo_agotado`). Otro error de escritura de un parte →
`rechazado` con `error_de_escritura` y el tipo de excepción, y el lote sigue.

## Seguridad, trazas, verificación y documentación

**R18.** Todo el SQL debe ser constante, con valores como `?`, validado en el constructor con
`DatabaseReferenceGuard.validate(..., allowed=[database])`; sin `UPDATE`, `DELETE`, `MERGE`
ni DDL en ninguna sentencia (control negativo en tests).

**R19.** El sistema no debe pasar a PTE ni crear `tar`, correos, gráficos, UPV ni `obrofc`/`auxofc`.

**R20.** CUANDO termine un lote, el sistema debe registrar una traza por lote (obra, `usu`, `commit`,
`resumen`, duración) y una por parte (referencia, estado, código, `ide`, `cod`), **nunca** descripciones.

**R21.** El sistema debe cubrir R1-R20 con tests unitarios sin red ni BBDD
(`test_f006_rN_*`), comparando el SQL generado carácter a carácter y con fase RED en
R11-R15.

**R22.** MANUAL (humano): dry-run y un `commit:true` autorizado de **un** parte sobre la UPV
elegida (Q4); el parte se ve en la pestaña Reclamaciones de la UPV con su tipo, oficio,
intervinientes y estado SAT, y repetir la llamada da `idempotente` sin segunda fila.

**R23.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (§4, §7.1, §7.5,
§7.6, §8.9 nueva, §9.2, §10 con `postventa-incidencias` F-040), `docs/ARCHITECTURE.md` y el mapa de rutas de `CLAUDE.md`.

## Fuera de alcance

Pasar a PTE (crea tareas y envía correos), tareas, correos, fotos (`sigrid/concepto-grafico`), alta
de UPV u oficios de obra, modificar o anular partes, preventa (`RP`), la referencia del promotor
en partes de la API (Q1), los 1.512 `con` sin `rcp` medidos y más de una obra por lote.
