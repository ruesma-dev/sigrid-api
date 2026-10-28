<!-- specs/F-016-proforma-a-origen/requirements.md -->
# F-016 · Requisitos (v2: cambio de alcance del humano, 2026-10-28)

**`POST /api/sigrid/proforma` registra también proformas A ORIGEN cuando el llamante lo pide con `modo: "origen"`**;
sin `modo`, o con `"mes"`, es **exactamente F-007**, que está desplegada. A origen, la proforma lleva
`dca.docoritip 1`, cuelga de la **anterior que indica el llamante** (`docoriide`), continúa las líneas que él indica,
arrastra las demás de la anterior y acumula las cantidades a origen línea a línea, como las que deja Sigrid.

**Alcance (humano, 2026-10-28)**: «aquí solo es la gestión del registro en sí, el endpoint; marcar si es a origen,
importes a buscar en Sigrid, etc., deberá hacerlo el portal». La API **registra y valida la integridad**; **no busca
ni deduce**: el modo, la anterior y qué línea continúa cada una las decide el llamante (`proformas`), que lee Sigrid
por `sql/read` (design §Contrato v1.2). **Mn**: [`explore_F-007.md`](../../progress/explore_F-007.md) (M11, M16-M26)
y [`explore_F-016.md`](../../progress/explore_F-016.md) (M41-M44); **Dn**: design §Decisiones. **«F-007 Rn»** (spec de
F-007, v3.1) manda en todo lo que aquí no se repite.

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
  `dcapro.ide` de la línea de la anterior que continúa). SI `modo` es `"origen"` y no trae **exactamente uno** de
  `proforma_anterior` y `primera_de_cadena`; o esos dos campos o `linea_anterior` vienen sin `modo` `"origen"`; o viene
  `linea_anterior` con `primera_de_cadena`; o dos líneas traen el mismo `linea_anterior`; o `modo` `"origen"` viene con
  `sin_contrato`, ENTONCES 400 `Solicitud invalida.` sin `codigo` (F-012). Los importes y cantidades de la hoja siguen
  siendo opcionales, como en F-007.
- **R4.** El sistema debe leer `SIGRID_PROFORMA_ORIGEN_ENABLED` (defecto `false`, validador de booleano de F-009).
  CUANDO llegue `commit:true` con `modo` `"origen"` y esa llave cerrada, el sistema debe responder 400
  `escritura_proformas_origen_deshabilitada`, **después** de la llave de F-007 R5 y antes del caso de uso. La previa no
  cambia. Ninguna App Setting existente cambia (D10).

## Ya registrada (D8)

- **R5.** A origen, el sistema debe aplicar F-007 R23 (idempotente o `referencia_en_conflicto`) y R24 con una sola
  diferencia: una proforma del contrato y del mes **a origen** (`docoritip 1`) con otro total no da
  `proforma_del_mes_existente` sino el aviso informativo `otra_del_mes` y sigue (cadenas paralelas, M18). Las de mes
  (`docoritip 0`) con otro total y cualquiera con el mismo total (±0,05), como F-007 (también `otra_del_mes`).

## La anterior: la indica el llamante y la API la valida (D2)

- **R6.** CUANDO venga `proforma_anterior`, el sistema debe leer (LP7) el `tip 14` de ese `con.cod` en el contrato
  resuelto: SI no hay exactamente uno, o no es a origen (`docoritip` ≠ 1), o su `con.fec` es posterior a la fecha de
  F-007 R18, ENTONCES `anterior_no_valida`.
- **R7.** El sistema debe leer (LP8) los `tip 14` del contrato con `docoriide` = la anterior: SI hay alguno, ENTONCES
  `anterior_con_sucesora` con su `cod` en el mensaje (la cadena es lineal, M19).
- **R8.** CUANDO venga `primera_de_cadena`, el sistema debe registrarla sin anterior y sin leer LP7 ni LP8.

## Líneas (D3-D6)

- **R9.** CUANDO una línea traiga `linea_anterior`, el sistema debe comprobar contra las líneas de la anterior (LP9)
  que es una de ellas y que es del mismo `ctrpro` (`linoriide`) si la línea es de contrato o sin vincular (`linoriide`
  0) si no; SI no, ENTONCES `linea_anterior_no_valida`, con los demás fallos de la etapa 1 de F-007 en el mismo
  `lineas_no_validas`. Sin `linea_anterior`, la línea es **nueva**: la API no casa por su cuenta (D3).
- **R10.** CUANDO una línea de contrato nueva tenga su `ctrpro` en alguna línea de la anterior, el sistema debe añadirle
  el aviso informativo `linea_nueva_ya_en_la_anterior` con los `dcapro.ide` de esas líneas (D3).
- **R11.** El sistema debe construir las líneas de la petición como F-007 (R13-R17) con estas columnas: **continuada**,
  `canorilin` = su `linea_anterior`, `canoriori` = el `canoriori` de esa línea + `cantidad`, `imporiori` = el del
  `ctrpro` (vinculada) o el de la anterior (sin vincular); **nueva**, `canorilin` 0, `canoriori` = `cantidad` e
  `imporiori` como F-007; en las dos, `canoriant` e `imporiant` 0 (M41, M23).
- **R12.** El sistema debe escribir cada línea de la anterior que ninguna continúa como **arrastrada**: copia de su fila
  con `can`, `tot`, `ivacuo` y `prepma` 0, `canorilin` = su `ide`, sus `canoriori` e `imporiori`, `canoriant` e
  `imporiant` 0, el seguimiento a 0 como el núcleo (`canser`, `canfac`, `cancan`, `canped`…), `med` vacío y `canmed` 0,
  y `pos` detrás de las de la petición en el orden de la anterior. Sin `ctrprodes`, `mov` ni `UPDATE` (D6).
- **R13.** El sistema debe construir la cabecera como F-007 R12 con `dca.docoritip` 1 y `docoriide` = la anterior (0 en
  primera).
- **R14.** SI las líneas de la petición más las arrastradas superan `SIGRID_PROFORMA_MAX_LINEAS`, ENTONCES
  `demasiadas_lineas`, aun en previa.

## Comprobaciones y avisos (D9)

- **R15.** A origen, F-007 R19 (cuadre de la hoja si vienen los importes y las cantidades), R20 (`origen` y
  `anterior_distinto_de_sigrid` frente a lo registrado del contrato) y R21 (`supera_contrato`, `supera_contrato_10`)
  deben aplicarse sin cambios. No hay avisos nuevos de comparación con Sigrid.
- **R16.** A origen, el sistema no debe emitir `contrato_a_origen` (F-007 R22): avisa de que la proforma se registra de
  mes en un contrato que va a origen, y a origen no es cierto.

## Transacción

- **R17.** Dentro de la transacción, tras F-007 R28 (con R5 en lugar de R24), el sistema debe releer LP8 por el cursor
  y, SI la anterior ya tiene sucesora, ENTONCES responder `anterior_con_sucesora` sin escribir.
- **R18.** El sistema debe escribir en **una** transacción lo de F-007 R27 más las `dcapro` arrastradas, con los applocks
  de F-015 en su orden, y releer antes del COMMIT tantas `dcapro` como se insertaron (arrastradas incluidas).

## Respuesta, trazas, pruebas y documentación

- **R19.** A origen, el sistema debe responder lo de F-007 R30 más `cadena` (`anterior` con `cod` e `ide` o `null`,
  `primera_de_cadena`, `importe_anterior_cadena` e `importe_origen_cadena` = Σ round(`canoriori`·`pre`, 2) de las líneas
  de la anterior (LP9) y de las escritas, y `n_arrastradas`) y, por línea, `linea_anterior`, `arrastrada`,
  `cantidad_anterior_cadena` y `cantidad_origen_cadena`; las arrastradas, detrás de las de la petición. En `existente`
  e `idempotente`, `cadena` es `null`.
- **R20.** Los códigos nuevos (design §Códigos) deben vivir en subclases: los conjuntos y clases de F-007 no cambian.
- **R21.** La traza de F-007 R33 debe añadir `modo`, `primera_de_cadena`, el `cod` de la anterior, el nº de
  continuadas y el de arrastradas; nunca textos, nombres, CIF, precios ni importes.
- **R22.** Todo el SQL nuevo debe ser constante con `?`, de lectura y validado con `DatabaseReferenceGuard`; ningún
  `DELETE`, `MERGE`, DDL ni `UPDATE` nuevo (control negativo en tests).
- **R23.** El sistema debe cubrir R1-R22 con tests sin red ni BBDD (`test_f016_rN_*`), SQL comparado carácter a
  carácter, fase RED y campaña de mutación sin supervivientes no aceptados por el humano (rigor `critico`).
- **R24.** MANUAL (humano): despliegue con `SIGRID_PROFORMA_ORIGEN_ENABLED=false`; previas a origen sobre cadenas
  reales (la hoja de la punta da `existente`; la del mes siguiente con esa punta como anterior, `previsto` encadenado);
  una anterior con sucesora (`anterior_con_sucesora`); un `commit:true` autorizado con la llave abierta solo para él,
  revisado en la UI (V9), repetido y anulado desde la UI.
- **R25.** El sistema debe actualizar en el mismo trabajo `contrato_proformas.md` (v1.2, con lo que el llamante lee de
  Sigrid), `azure-apps/sigrid_api.md`, `docs/ARCHITECTURE.md`, el mapa de `CLAUDE.md` y `local.settings.sample.json`,
  y dejar escrito el aviso a `proformas` y a `facturas` (D13).

## Fuera de alcance

Elegir el modo, la anterior o qué línea continúa cada una y leer para ello los importes de Sigrid (del llamante:
design §Contrato v1.2); deducir la ANTERIOR de la hoja; proformas a origen sin contrato o con la anterior en otro
contrato (M19: 9 casos); sembrar el origen con los meses de mes (D7); `ctrprodes` y `mov` a 0 de las arrastradas (D6,
V9); partidas con el código repetido (F-017); facturar (F-008); modificar o anular.
