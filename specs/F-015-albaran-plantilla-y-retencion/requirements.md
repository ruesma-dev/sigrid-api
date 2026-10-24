# F-015 · Requisitos (v2)

> **Aprobada por el humano el 2026-10-24**: D1-D12 (D10, fuera de alcance: lo resuelve albaranes en su F-069), con el
> orden de fuentes final **contrato → albarán anterior → proveedor**. Pendiente de T0 (contrato con albaranes v8.3 y su
> acuse) antes de pasar a `in_progress`.

**El modo extendido de `POST /api/sigrid/albaran` (F-009) construye `con` y `dca` columna a columna con una lista blanca
(petición, obra, cálculo, valor fijo o, por este orden, contrato → albarán anterior → proveedor), toma la forma de pago
del contrato y escribe la retención del contrato (`ctrrec` → `dcarec`) con su total neto.** La v2 sustituye a la v1
(2026-10-19, commit `05b3b24`) por decisión del humano y recoge sus respuestas del 2026-10-23 y 2026-10-24 (orden de
fuentes, respaldo opcional): la cabecera ya no se clona de una plantilla. Medidas **Mn**:
[`progress/explore_F-015.md`](../../progress/explore_F-015.md) (M1-M16 de la v1, M17-M28 de la v2). F-009 sigue mandando
en lo que esta spec no cambia («F-009 Rn»). Decisiones **Dn** y la lista columna a columna: design §Decisiones y §Lista
blanca. «Respaldo» = el albarán anterior del proveedor que define R6: segundo origen, tras el contrato y antes del
proveedor.

## Cabecera por lista blanca (O1)

- **R1.** El sistema debe construir `con` con exactamente las columnas de `CON_COLUMNAS` (F-006) y `dca` con exactamente
  las 145 de `DCA_COLUMNAS` (esquema vivo, M17), en ese orden, cada una con **un único origen** de design §Lista blanca; el
  `INSERT` de las dos lleva esas columnas fijas, nunca las de una fila leída (D6).
- **R2.** El sistema no debe escribir en `con` ni en `dca` un valor leído del contrato, del proveedor o del respaldo en una
  columna cuyo origen en la lista no lo admita (D6).
- **R3.** El sistema debe tomar cada columna de origen **cascada** (design §Lista blanca) del primer origen que la traiga
  con valor (≠ 0, no vacío) en este orden, igual para todas: **contrato** (`ctr`), **respaldo** y **proveedor** (`prv`
  del `entide`); sin contrato, respaldo y proveedor. El grupo pago (`pagide`, `pagtex`, `pagfor`, `efeide`) sale entero
  del origen del primer `pagide` ≠ 0 (del `prv`, los textos de su `auxpag`) y el grupo banco (`banban`, `bansuc`,
  `bandig`, `bancue`, `ban`, `bantipide`), del primero con banco; `ivadif`, del `ctr` si hay contrato (aunque sea 0) y,
  si no, del respaldo (M28; D2, D5).
- **R4.** El sistema debe tomar `entide`, `entcod`, `entres`, `entcif`, `entciftip` y `entcifpai` del `ctr` CUANDO haya
  contrato; sin él, del respaldo por CIF y, sin respaldo, del proveedor de R7 (`ide`, `con.cod`, `raz`, `cif`, `tipcif`,
  `cifpai`) (M20, M27; D3).
- **R5.** SI ningún origen trae una columna de cascada, ENTONCES el sistema debe escribir el valor que deja el alta a mano
  (0 o `''`), sin error ni parada; y, si es del pago o del banco con efecto de confirming (`CC`, `CT`) o transferencia
  (`TR`), añadir el aviso de cabecera informativo `cabecera_sin_dato` con las columnas que faltan (M28: banco, 4 de 426
  con contrato y 4 de 234 sin él; D12).
- **R6.** El respaldo (L5) debe ser el último `con.tip 14` del proveedor (por `entide` con contrato, por `entcif` sin él)
  en la empresa de la obra con `con.cod LIKE 'AC__/%'`, `dca.cla = 0` y `ISNULL(dca.entref, '')` que no empiece por
  `PROF`: nunca una proforma (por serie o por referencia), una nota de cargo ni un `AC` de otra clase (M1, M25). **Es
  opcional**: sin él, el alta sigue con el contrato y el proveedor; `proveedor_sin_albaran_previo` se retira (D4).
- **R7.** CUANDO el albarán no tenga contrato ni respaldo por CIF, el sistema debe resolver el proveedor (L17) entre los
  `prv` con `con.tip 5`, la empresa de la obra, `fecbaj` 0 y `cif` = `cif_proveedor`: uno, ese; ninguno, 400
  `proveedor_no_encontrado`; varios, 400 `proveedor_ambiguo` (M27: uno en 422 de 429; D3). Con respaldo, el `prv` es el
  de su `entide`.
- **R8.** El sistema debe escribir de la petición, la obra o un cálculo, como F-009: en `dca`, `ide`, `entref`, `fecdoc`,
  `hor`, `obride`, `ctride`, `almide`, `cenide`, `empide`, `synckey` y los totales (R13), y `diremp1` = la `entres`
  escrita (M20: 100 %); en `con`, `ide`, `emp`, `tip`, `cod`, `res`, `fec` y `est`, y **`tiemod` = fecha OLE en UTC del
  alta** (`fecha_ole_utc` de F-006, en los sellos de la petición).
- **R9.** El sistema debe escribir en el resto de columnas el valor fijo del alta a mano (M18): `cla` 0, `tipgar` −1,
  `emptex` y `con.tex` NULL, las demás de texto `''` y las numéricas 0. Entre ellas, facturación (`fecfac`, `horfac`,
  `idefac`, `antestfac`, `estfac`), cadena (`docoritip`, `docoriide`, `pasdeside`, `pasori`, `docrelide`, `fecpag`),
  divisa (`totbasdiv`, `totivadiv`, `totdocdiv`, `totdiv`, `totpagdiv`), `fecent`, `feclim`, `cocide`, `dtumID`, `estser`,
  `impdes` e `imprec` (M19; D7).
- **R10.** SI a la fila del contrato, del proveedor o del respaldo le falta una columna que la lista toma de ella, ENTONCES el sistema
  debe fallar con `ValueError` (500) sin escribir nada: un cambio de esquema no se rellena a ciegas.
- **R11.** El modo clásico y `sigrid/albaran-directo` no deben cambiar: ni modelo, ni caso de uso, ni sentencias, ni el
  dorado `tests/fixtures/f009_caracterizacion.json`, que sigue pasando sin tocarlo (D9).

## Retención del contrato (O2)

- **R12.** CUANDO el albarán tenga contrato (con o sin vinculadas, también en devoluciones), el sistema debe leer sus
  `ctrrec` (L16) y, si es soportada (R14), escribir **una** `dcarec`; sin contrato o sin `ctrrec`, ninguna (M9, M10; D8).
- **R13.** El sistema debe construir la `dcarec` copiando del `ctrrec` `recide`, `pos`, `valdef`, `valpor`, `valcan`,
  `valmod`, `valfij`, `reccla`, `cueide`, `ivaide`, `tex`, `resalt` e `item` (M11), con `docide` = `con.ide`, `bas` y
  `cuo` de R15 e `ivacuo`, `reqcuo`, `refide` y `frasupide` a 0 (M13), y escribir `dca.tot` = `totdoc` − `cuo` y
  `dca.totpag` = `tot`; sin ella, `tot` = `totpag` = `totdoc`. `totbas`, `totiva`, `totdoc`, `impbru` e `impnet` son los
  de F-009 (M13).
- **R14.** SI el contrato tiene más de un `ctrrec`, o el suyo tiene `recide` sin fila en `dbo.rec`, clase de `rec` fuera de
  {3, 4, 5}, `valfij` ≠ 0 o `ivaide` ≠ 0, ENTONCES el sistema debe responder 400 `retencion_no_soportada` (cabecera),
  también en dry-run, después de la idempotencia (F-009 R30) y antes de validar las líneas (M11: 15 de 651; D8).
- **R15.** El sistema debe calcular `bas` = `totbas` (clases 3 y 5) o `totdoc` (clase 4) y `cuo` =
  `redondear_euros(bas · valpor)` (`Decimal`, `ROUND_HALF_UP`, lejos del cero también en negativo) (M12).
- **R16.** CUANDO haya `dcarec`, el sistema debe añadir el aviso de cabecera `retencion_del_contrato` (código del
  recargo, porcentaje, `bas` y `cuo` en el mensaje), informativo (D8).

## Respuesta (contrato con albaranes)

- **R17.** El sistema debe añadir a `totales` `tot` (= `dca.tot`), `retenciones` (= `cuo`, 0 sin `dcarec`) y
  `n_retenciones` (0 o 1), en previa y en `creado`, y `filas.dcarec` (0 o 1 filas). `cabecera` y `filas.dca` llevan las
  columnas de R1 sin las bancarias (F-009 H16); `contrato.template_ide` pasa a ser el `ide` del respaldo (0 sin él).
- **R18.** En `idempotente`, el sistema debe leer `dca.tot` (L11) y devolver `totales.tot` y `totales.retenciones` =
  `totdoc` − `tot` del albarán existente, sin leer su `dcarec`.
- **R19.** El sistema debe trazar (F-009 R32) además `n_retenciones`; nunca `bas`, `cuo`, `valpor`, ni la forma de pago.

## Escritura

- **R20.** MIENTRAS `commit` sea `false`, el sistema debe devolver la `dcarec` numerada con `peek_next_ide("dcarec")`,
  sin reservar nada (como F-009 R23).
- **R21.** CUANDO `commit` sea `true` y haya `dcarec`, el sistema debe, dentro de la transacción de F-009 R25 y tras los
  `mov`, reservar su `ide` (`MAX(ide)+1 WITH (UPDLOCK, HOLDLOCK)`) bajo el applock nuevo `SIGRID_IDE_dcarec`, tomado
  entre `SIGRID_IDE_mov` y `SIGRID_IDE_log`, e insertarla; sin `dcarec`, ni reserva ni `INSERT`.
- **R22.** El reintento por clave duplicada (F-009 R27) debe recalcular también el `ide` de la `dcarec`.
- **R23.** SI antes del `COMMIT` la relectura (E12) no da tantas `dcarec` del albarán como se insertaron (0 o 1),
  ENTONCES `ROLLBACK` y 400 `filas_afectadas_inesperadas`.
- **R24.** Todo el SQL nuevo o cambiado (L5, L11, L16, L17, E6b, los `INSERT` de `con`, `dca` y `dcarec`, E12) debe ser
  constante con `?` y validado con `DatabaseReferenceGuard`; ningún `UPDATE`, `DELETE`, `MERGE` ni DDL nuevo (control
  negativo de F-009 R31).

## Equivalencia, pruebas y documentación

- **R25.** El sistema debe tener un test **centinela**: con contrato, proveedor y respaldo cuyas columnas valen todas un
  valor distinto y reconocible, cada columna de `con` y `dca` lleva un centinela solo si la lista le da como origen esa
  fila, y la lista cubre `CON_COLUMNAS` y `DCA_COLUMNAS` sin dejar ni repetir ninguna; con y sin contrato, con y sin
  respaldo, y vaciando un origen para ver que la columna pasa al siguiente en el orden contrato → respaldo → proveedor
  (R3) o al valor de R5.
- **R26.** El test de equivalencia con el clásico (F-009 R33) debe seguir pasando con estas diferencias **declaradas**, y
  ninguna más: en `con` y `dca`, las columnas cuyo origen no es el respaldo ni la cascada (el clásico las clona; el
  contrato y el proveedor del fixture dejan vacías las de cascada: salen del respaldo); con `ctrrec`, `dcarec`
  y el aviso R16. Las columnas de origen respaldo deben salir **iguales** a las del clásico; `dcapro`, `ctrprodes` y `mov`
  como en `dev`.
- **R27.** El sistema debe cubrir R1-R26 con tests sin red ni BBDD (`test_f015_rN_*`), SQL comparado carácter a carácter,
  con fase RED en R1, R2, R3, R5, R6, R7, R9, R12, R14, R15, R21 y R23. Los tests de F-009 que fijan L5, L11, los applocks,
  `construir_con`, `construir_dca`, `totales` o la `dca` se cambian solo en lo que R1-R24 cambian, cada uno con su R.
- **R28.** El sistema debe actualizar **antes de implementar** `contrato_albaranes.md` a la v8.3 (design §Contrato) y
  avisar a albaranes, y en el mismo trabajo `azure-apps/sigrid_api.md` (§7.5, §7.6, §8.6, §8.7, §13),
  `docs/ARCHITECTURE.md` (lista blanca, applocks, `dcarec`) y el docstring de `sigrid_albaran`.
- **R29.** MANUAL (humano), tras desplegar: dry-run de un albarán de un contrato con `RET5`, de uno sin `ctrrec`, de uno
  sin contrato y de un proveedor sin respaldo, revisando `filas.dca` (forma de pago del contrato, facturación y fechas a 0), `filas.dcarec` y `totales`;
  una grabación solo con autorización expresa para esa escritura, revisada en la UI (V1), repetida (`idempotente`) y
  anulada desde la UI (nunca `DELETE`).

## Limpieza de las altas ya escritas (MANUAL)

- **R30.** MANUAL (humano), con autorización expresa para esa escritura y después de desplegar F-015: el plan de design
  §Limpieza (lectura previa, `UPDATE` parametrizado por `sql/write` con `max_affected_rows` = filas leídas, relectura),
  solo sobre altas de la API (`synckey` `ALB-%` y la lista de `con.ide` de albaranes; no por `empide`) sin facturar ni líneas en `dcfpro`. Nada de `DELETE`
  (M19: 60 de 68 el 2026-10-23; D11).

## Fuera de alcance

Interpretar el texto o el PDF del contrato (D1; límite de microservicio); deducir `empide` del `usu` (M24; D10: lo
resuelve albaranes en su F-069); la plantilla de línea `dcapro` (sigue clonada de L8/L8b, F-009); retención sin contrato (M9) y `ctrrec` no
soportados (R14: alta a mano); recalcular la `dcarec` si el escritorio cambia el albarán; IRPF y cartera (los genera la
factura, F-008); cambiar el clásico o `albaran-directo` (D9).
