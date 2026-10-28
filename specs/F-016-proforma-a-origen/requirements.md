<!-- specs/F-016-proforma-a-origen/requirements.md -->
# F-016 · Requisitos (v1, 2026-10-28)

**`POST /api/sigrid/proforma` registra también proformas A ORIGEN cuando `proformas` lo pide con `modo: "origen"`**
(lo indica el jefe de obra); sin `modo`, o con `"mes"`, es **exactamente F-007**, que está desplegada. A origen, la
proforma lleva `dca.docoritip 1`, cuelga de su **anterior** de la cadena del contrato (`docoriide`), arrastra todas sus
líneas y acumula las cantidades a origen línea a línea, como las que deja Sigrid. **Mn**:
[`explore_F-007.md`](../../progress/explore_F-007.md) (M11, M16-M26) y [`explore_F-016.md`](../../progress/explore_F-016.md)
(M41-M44); **Dn**: design §Decisiones. **«F-007 Rn»** (spec de F-007, v3.1) manda en todo lo que aquí no se repite.

## Compatibilidad

- **R1.** CUANDO la petición no traiga `modo` o traiga `"mes"`, el sistema debe comportarse exactamente como F-007:
  mismas lecturas en el mismo orden, mismas filas, mismos errores y la misma respuesta, **sin ninguna clave nueva**.
  Los tests de F-007 y los tests y dorados de F-009 y F-015 deben pasar **sin modificarlos**.
- **R2.** El sistema no debe modificar el núcleo de F-009 (`create_albaran_compra_use_case.py`,
  `albaran_compra_statements.py`, `albaran_compra_models.py`) ni lo de F-007 que no cite el design §Ficheros: `sigrid/albaran`
  (los dos modos), `sigrid/albaran-directo` y la proforma de mes no cambian (D11).

## Petición y configuración

- **R3.** El sistema debe admitir en la cabecera `modo` (`"mes"` por defecto, o `"origen"`), `proforma_anterior` (texto
  1-24, `con.cod` de la anterior) y `primera_de_cadena` (`false`), y en la línea `linea_anterior` (entero ≥ 1,
  `dcapro.ide` de la línea de la anterior que continúa). SI `proforma_anterior`, `primera_de_cadena` o `linea_anterior`
  vienen sin `modo` `"origen"`; o vienen juntos `proforma_anterior` y `primera_de_cadena`; o `linea_anterior` con
  `primera_de_cadena`; o dos líneas con el mismo `linea_anterior`; o `modo` `"origen"` con `sin_contrato` o sin
  `importe_anterior`, ENTONCES 400 `Solicitud invalida.` sin `codigo` (F-012).
- **R4.** El sistema debe leer `SIGRID_PROFORMA_ORIGEN_ENABLED` (defecto `false`, validador de booleano de F-009).
  CUANDO llegue `commit:true` con `modo` `"origen"` y esa llave cerrada, el sistema debe responder 400
  `escritura_proformas_origen_deshabilitada`, **después** de la llave de F-007 R5 y antes del caso de uso. La previa no
  cambia. Ninguna App Setting existente cambia (D10).

## Ya registrada (D8)

- **R5.** A origen, el sistema debe aplicar F-007 R23 (idempotente o `referencia_en_conflicto`) y R24 con una sola
  diferencia: una proforma del contrato y del mes **a origen** (`docoritip 1`) con otro total no da
  `proforma_del_mes_existente` sino el aviso informativo `otra_del_mes` y sigue (cadenas paralelas, M18). Las de mes
  (`docoritip 0`) con otro total y cualquiera con el mismo total (±0,05), como F-007 (también `otra_del_mes`).

## La anterior (D2)

- **R6.** El sistema debe leer las **candidatas** (LP7): los `tip 14` del contrato con `docoritip 1`, de cualquier serie,
  con `con.fec` ≤ la fecha de F-007 R18 y, de cada una, su **importe de cadena** = Σ round(`canoriori`·`pre`, 2) de sus
  líneas. **Punta** = candidata que no es `docoriide` de ninguna otra del contrato.
- **R7.** CUANDO venga `proforma_anterior`, el sistema debe tomar la candidata de ese `cod` (`elegida_por`
  `peticion`): SI no es una candidata del contrato, ENTONCES `anterior_no_valida`; SI no es punta, ENTONCES
  `anterior_con_sucesora` con el `cod` de su sucesora en el mensaje.
- **R8.** CUANDO venga `primera_de_cadena`, el sistema debe registrarla sin anterior (`elegida_por` `primera`).
- **R9.** Sin ninguno de los dos, el sistema debe elegirla así: con `importe_anterior` ≤ 0,05, primera (`primera`); si
  no, las puntas con |importe de cadena − `importe_anterior`| ≤ 0,05 y sin contradicción (R10): una, esa (`importe`);
  varias, `anterior_ambigua`; ninguna, `anterior_con_sucesora` si casa una candidata que no es punta (con su sucesora),
  o si no `anterior_no_resuelta`. Los tres errores llevan `details.puntas` (`cod`, `ide`, `fec`, importe de cadena).
- **R10.** Hay **contradicción** con una candidata si una línea de contrato de la petición trae `cantidad_anterior`, su
  `ctrpro_ide` está en una sola línea de la candidata y difieren `canoriori` y `cantidad_anterior` en más de 0,001.

## Líneas (D3-D6)

- **R11.** El sistema debe casar cada línea de la petición con una línea de la anterior (etapa 1 de F-007, con sus
  fallos juntos en `lineas_no_validas`). Con `linea_anterior`: ha de ser de la anterior, de su mismo `ctrpro` si la línea
  es de contrato y sin vincular si no; si no, `linea_anterior_no_valida`. Sin ella: de contrato, las de la anterior con
  `linoriide` = su `ctrpro`; sin contrato, las sin vincular de la anterior con su código de partida
  (`partida_imputacion` o `partida`; sin partida, ninguna) y su precio (±0,0001); **el producto no cuenta**. Una, esa;
  ninguna, la línea es **nueva**; varias, `linea_anterior_ambigua` con sus `dcapro.ide` en `candidatos`. Una línea de
  la anterior la continúa como mucho una de la petición (si no, `linea_anterior_ambigua`). En primera, todas nuevas.
- **R12.** El sistema debe construir las líneas de la petición como F-007 (R13-R17) con estas columnas: **continuada**,
  `canorilin` = el `ide` de su línea anterior, `canoriori` = su `canoriori` + `cantidad`, `imporiori` = el del `ctrpro`
  (vinculada) o el de la anterior (sin vincular); **nueva**, `canorilin` 0, `canoriori` = `cantidad` e `imporiori` como
  F-007; en las dos, `canoriant` e `imporiant` 0 (M41, M23).
- **R13.** El sistema debe escribir cada línea de la anterior que ninguna continúa como **arrastrada**: copia de su fila
  con `can`, `tot`, `ivacuo` y `prepma` 0, `canorilin` = su `ide`, sus `canoriori` e `imporiori`, `canoriant` e
  `imporiant` 0, el seguimiento a 0 como el núcleo (`canser`, `canfac`, `cancan`, `canped`…), `med` vacío y `canmed` 0,
  y `pos` detrás de las de la petición en el orden de la anterior. Sin `ctrprodes`, `mov` ni `UPDATE` (D6).
- **R14.** El sistema debe construir la cabecera como F-007 R12 con `dca.docoritip` 1 y `docoriide` = la anterior (0 en
  primera).
- **R15.** SI las líneas de la petición más las arrastradas superan `SIGRID_PROFORMA_MAX_LINEAS`, ENTONCES
  `demasiadas_lineas`, aun en previa.

## Cuadre y avisos (D9)

- **R16.** F-007 R19 se aplica igual. A origen, el sistema debe sustituir los avisos de anterior de F-007 R20 por estos,
  informativos: `anterior_distinto_de_sigrid` de cabecera si |`importe_anterior` − importe de cadena de la anterior (0 en
  primera)| > 0,05, y de línea si |`cantidad_anterior` − `canoriori` de su línea anterior (0 si es nueva)| > 0,001; y
  `origen_distinto_de_sigrid` de cabecera si viene `importe_origen` y difiere del importe de cadena de la nueva en más de
  0,05, y de línea si viene `cantidad_origen` y difiere de su `canoriori` escrito en más de 0,001. `origen` (F-007 R20,
  R21) se calcula igual que en F-007, con `supera_contrato` y `supera_contrato_10`.
- **R17.** A origen, el sistema no debe emitir `contrato_a_origen` (F-007 R22) y debe avisar `cadena_con_meses_fuera`,
  con sus `cod`, si el contrato tiene proformas de mes (LP1, `docoritip 0`) anteriores al periodo y posteriores a la
  anterior (o cualquiera, en primera): esos meses no entran en el origen de la cadena (M43).

## Transacción

- **R18.** Dentro de la transacción, tras F-007 R28 (con R5 en lugar de R24), el sistema debe releer LP7 por el cursor
  y, SI la anterior ya tiene sucesora, ENTONCES responder `anterior_con_sucesora` sin escribir.
- **R19.** El sistema debe escribir en **una** transacción lo de F-007 R27 más las `dcapro` arrastradas, con los applocks
  de F-015 en su orden, y releer antes del COMMIT tantas `dcapro` como se insertaron (arrastradas incluidas).

## Respuesta, trazas, pruebas y documentación

- **R20.** A origen, el sistema debe responder lo de F-007 R30 más `cadena` (`anterior` con `cod` e `ide` o `null`,
  `elegida_por`, `importe_anterior_cadena`, `importe_origen_cadena`, `puntas`, `n_arrastradas`) y, por línea,
  `linea_anterior`, `arrastrada`, `cantidad_anterior_cadena` y `cantidad_origen_cadena`; las arrastradas, detrás de las
  de la petición. En `existente` e `idempotente`, `cadena` es `null`.
- **R21.** Los códigos nuevos (design §Códigos) deben vivir en subclases: los conjuntos y clases de F-007 no cambian.
- **R22.** La traza de F-007 R33 debe añadir `modo`, `elegida_por`, el `cod` de la anterior y el nº de arrastradas;
  nunca textos, nombres, CIF, precios ni importes.
- **R23.** Todo el SQL nuevo debe ser constante con `?`, de lectura y validado con `DatabaseReferenceGuard`; ningún
  `DELETE`, `MERGE`, DDL ni `UPDATE` nuevo (control negativo en tests).
- **R24.** El sistema debe cubrir R1-R23 con tests sin red ni BBDD (`test_f016_rN_*`), SQL comparado carácter a
  carácter, fase RED y campaña de mutación sin supervivientes no aceptados por el humano (rigor `critico`).
- **R25.** MANUAL (humano): despliegue con `SIGRID_PROFORMA_ORIGEN_ENABLED=false`; previas a origen sobre cadenas
  reales (la de su punta da `existente`; la del mes siguiente, `previsto` encadenado a la punta); un cambio de modo; un
  `commit:true` autorizado con la llave abierta solo para él, revisado en la UI (V9), repetido y anulado desde la UI.
- **R26.** El sistema debe actualizar en el mismo trabajo `contrato_proformas.md` (v1.2), `azure-apps/sigrid_api.md`,
  `docs/ARCHITECTURE.md`, el mapa de `CLAUDE.md` y `local.settings.sample.json`, y dejar escrito el aviso a `proformas`
  y a `facturas` (D13).

## Fuera de alcance

Elegir el modo (es del jefe de obra, en `proformas`); proformas a origen sin contrato o con la anterior en otro contrato
(M19: 9 casos); sembrar el origen con los meses de mes (D7, V10); `ctrprodes` y `mov` a 0 de las arrastradas (D6, V9);
partidas con el código repetido (F-017); facturar (F-008); modificar o anular.
