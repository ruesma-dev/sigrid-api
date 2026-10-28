# F-018 · Requisitos (v1.2)

**El modo extendido de `POST /api/sigrid/albaran` (F-009/F-015) acepta un descuento simple por línea, `lineas[].dto`, y
registra la línea como la registra Sigrid: unitario original, cantidad, porcentaje e importe neto.** Lo pide albaranes
(su F-110; obra 0692): hoy sv9 manda `precio` = importe/cantidad y el descuento se pierde. Medidas **Mn**:
[`progress/explore_F-018.md`](../../progress/explore_F-018.md) (M45-M51). Decisiones **Dn** y preguntas **Pn**: design
§Decisiones y §Preguntas. F-007, F-009, F-015 y F-016 mandan en lo que aquí no se repite.

> **v1.2 (2026-10-28).** P1-P9 **decididas por el humano, 2026-10-28** (design §Decisiones): P1 = D1 (`tar` bruto,
> `pre` neto), P2 `ROUND_HALF_UP` sobre el producto exacto, P3 = D3 (dos avisos informativos), P4 (la proforma no
> admite `dto`), P5 (se corrige aquí, R15), P6 (0 a 100), P7 (motivo de la Semántica 9), **P8 = (a): la proforma, de
> mes y a origen, hereda R15 sin interruptor (R21, R22)** y P9 (R17). **Abierta P10 (bloqueante)**: el aviso nuevo
> rompe además `tests/test_f016_models.py` (design §Preguntas, medido).

## La línea con descuento (objetivo del humano)

- **R1.** CUANDO una línea del modo extendido traiga `dto` > 0, el sistema debe registrar en su `dcapro` el precio
  unitario original sin descuento, la cantidad, el porcentaje y el importe total de la línea, con el importe resultado
  de operar los otros tres: `tar` = `precio` (unitario original), `can` = `cantidad`, `dto` = el texto de R3,
  `tot` = `redondear_euros(cantidad · precio · (1 − dto/100))` y `pre` = `tot` / `cantidad` (unitario neto).
- **R2.** El sistema debe calcular ese `tot` sobre el producto **exacto** en `Decimal` (cada número por su `repr`, como
  `_decimal` de F-009) y redondearlo a 2 decimales con `ROUND_HALF_UP` (mitad lejos del cero, también en negativo),
  que es el redondeo de Sigrid (M46): 1 · 18,625 · (1 − 0,40) → 11,18; 1 · 265 · (1 − 0,035) → 255,73;
  −0,4 · 1.275,68 · (1 − 0,025) → −497,52; 36 · 4,278 · (1 − 0,40) → 92,40 con `pre` 2,5666…
- **R3.** El sistema debe escribir `dcapro.dto` como lo escribe Sigrid (M45): el porcentaje con **coma decimal**, sin
  ceros a la derecha ni separador de miles y seguido de `%` (`40` → `40%`, `1.5` → `1,5%`, `21.45` → `21,45%`,
  `0.01` → `0,01%`, `100` → `100%`).
- **R4.** El sistema debe validar `dto` con Pydantic en `LineaAlbaranIn`: opcional, número JSON (`strict`, finito),
  **0 ≤ `dto` ≤ 100, los dos incluidos** (P6), y como mucho 2 decimales (`Decimal(repr(dto))`); si no, 400 `Solicitud
  invalida.` sin `codigo` (F-012). No hay cascada (`"10+5"` es un texto: no valida; M45: ninguna desde 2020).
- **R5.** El sistema debe calcular `ivacuo` = `redondear_euros(tot · iva)` sobre el `tot` neto, como hoy (M47d).
- **R6.** SI `precio` < 0, ENTONCES fallo de línea `precio_negativo` como hoy, con o sin `dto`.

## Compatibilidad (criterio de aceptación de F-018)

- **R7.** CUANDO una línea venga sin `dto` en la petición (ausente, `null` o 0) **y** no copie del `ctrpro` un dto
  legible (R14) mayor que 0, el sistema debe construirla exactamente como hoy (mismas funciones con los mismos
  argumentos, mismas filas, mismo SQL, misma respuesta y misma traza, sin claves nuevas); los tests y dorados de F-007,
  F-009, F-015 y F-016 deben pasar sin modificarlos, salvo los conjuntos cerrados de avisos de R17 (P9 y P10).

## Cabecera, `mov` y contrato

- **R8.** El sistema debe sumar en la cabecera los importes **de las filas escritas**: `totbas` = Σ `tot` (neto),
  `totiva` = Σ `ivacuo`, `totdoc`, `tot`, `totpag` y la retención de F-015 sobre esos netos; `impnet` = `totbas` e
  `impdes` 0 (M47); e `impbru` = Σ por línea de `redondear_euros(can · tar)` en las líneas **con dto efectivo** (R1 o
  R15) y de `tot` en las demás (M47: 7.541 de 7.541). Sin líneas con dto efectivo, `impbru` = `totbas` como hoy.
- **R9.** El sistema debe escribir el `mov` de una línea con dto efectivo con `pre` = `prc` = el `dcapro.pre` neto y
  calcular con él el balance y el PMP (`almpma`) de F-009 R19; `prepma`, igual que hoy (M48: 22.366 de 22.368).
- **R10.** El sistema debe escribir `ctrprodes.can` y sumar `canser` por **cantidad**, como hoy (M49g: 2.267 de 2.267).

## Vinculadas (D3, D8)

- **R11.** CUANDO una vinculada traiga `dto` > 0, el sistema debe escribir R1 con el `precio` y el `dto` **pedidos**,
  sin aplicar la opción C de F-009 R17 y sin copiar `pre`, `tar` ni `dto` del `ctrpro` (validar, no pisar).
- **R12.** CUANDO una vinculada con `dto` > 0 tenga |`precio` − `ctrpro.tar`| > 0,0001, el sistema debe añadir el aviso
  de línea `precio_distinto_del_contrato` (el de F-009, con un mensaje que diga que compara el precio bruto).
- **R13.** CUANDO una vinculada con `dto` > 0 tenga un `ctrpro.dto` distinto del pedido (leído con R14; sin dto vale 0;
  no legible cuenta como distinto, con mensaje propio), el sistema debe añadir el aviso de línea nuevo
  **`dto_distinto_del_contrato`**, informativo, con los dos porcentajes. R12 y R13 se emiten los dos si hay las dos
  diferencias (P3; M49a: 2.243 de 2.244 coinciden).
- **R14.** El sistema debe leer el texto de un `dto` de Sigrid como número solo en su formato (M45, M49f: 100 % desde
  2020): vacío o `NULL` → 0; `N%` o `N,N…%` con espacios alrededor → `N`; cualquier otra forma (cascada `10+2,5`, sin
  `%`, con punto) → **no legible**.
- **R15.** CUANDO una vinculada venga sin `dto` en la petición y case por la opción C (F-009 R17) con un `ctrpro` cuyo
  `dto` sea legible y mayor que 0 y cuyo `tar` sea distinto de 0, el sistema debe copiar `tar` y `dto` del `ctrpro`
  como hoy y escribir, como Sigrid (P5, M46, M49h): `tot` = `redondear_euros(cantidad · tar · (1 − d/100))` con el
  `d` copiado, `pre` = `tot` / `cantidad`, `ivacuo` sobre ese `tot`, `impbru` con su bruto (R8) y el `mov` con ese
  neto (R9). Con `dto` no legible o `tar` 0, la línea sigue la opción C de hoy, sin aviso (R7).

## Respuesta, avisos y trazas

- **R16.** En `previsto` y `creado`, una línea con dto efectivo debe llevar además `dto` (el porcentaje, R14) y
  `precio_bruto` (= `tar` escrito); `precio` (= `pre`, neto) y `total` (= `tot`) son los de la fila. Las demás
  líneas, y todas en `idempotente` (L11 no cambia), no llevan esas claves en el JSON.
- **R17.** `CODIGOS_AVISO` debe aceptar `dto_distinto_del_contrato`; los demás conjuntos cerrados de `sigrid/albaran` no
  cambian. `tests/test_f009_models.py:413` lo añade a su conjunto (P9); los de la proforma, según P10.
- **R18.** CUANDO alguna línea de `sigrid/albaran` tenga dto efectivo, el sistema debe trazar (F-009 R32) además
  `n_lineas_con_dto`; nunca porcentajes, precios ni importes. Sin ninguna, la traza no cambia.

## Alcance de las demás rutas (D2, D10)

- **R19.** El modo clásico de `sigrid/albaran` y `sigrid/albaran-directo` no cambian: ni modelo, ni caso de uso, ni
  sentencias, ni dorado (`tests/fixtures/f009_caracterizacion.json`).
- **R20.** `sigrid/proforma` (de mes y a origen) no debe admitir `dto` en sus líneas (`LineaProformaIn`,
  `extra="forbid"`: 400 sin código, como hoy) y su traducción al núcleo no lo pasa (P4).
- **R21.** CUANDO una línea de `sigrid/proforma`, de mes o a origen, case por la opción C con un `ctrpro` de dto legible
  mayor que 0 y `tar` ≠ 0, el sistema debe aplicarle R15 como al albarán (P8 = (a), sin interruptor): `tot`, `pre` e `ivacuo` de
  Sigrid en su `dcapro`, `impbru` bruto y totales de la cabecera sobre esos `tot` (R8), el `mov` con ese neto si la
  línea lo genera (R9) y, en su línea de respuesta, `dto` y `precio_bruto` (R16); a origen, `importe_origen_cadena`
  (Σ round(`canoriori`·`pre`, 2)) se calcula con ese `pre` neto.
- **R22.** En `sigrid/proforma` el sistema no debe cambiar por F-018: las comprobaciones de la hoja (F-007 R19,
  `comprobar_hoja`, sobre la petición), `origen`, la búsqueda de `existente` y su tolerancia de 0,05 (sobre `totbas`
  leído), `anterior_distinto_de_sigrid`, `cantidad_anterior_cadena`, `cantidad_origen_cadena`,
  `importe_anterior_cadena` (filas leídas), las arrastradas (fila y respuesta, sin `dto`/`precio_bruto`), las
  respuestas `existente` e `idempotente`, la traza (F-007 R33, F-016 R21) ni ninguna línea sin dto efectivo (R7).

## SQL, seguridad y escritura

- **R23.** El sistema no debe añadir ni cambiar ninguna sentencia SQL (ni lecturas, ni L11, ni `INSERT`, ni `UPDATE`):
  `dto` viaja en la fila clonada de `dcapro`. El control negativo de F-009 R31 sigue pasando.
- **R24.** En `commit:true` el sistema debe escribir las filas de R1, R8, R9, R15 y R21 en la transacción de F-009 R25,
  con las llaves, applocks, reintento y relecturas de hoy.

## Pruebas, verificación y documentación

- **R25.** El sistema debe cubrir R1-R24 con tests sin red ni BBDD (`test_f018_rN_*`), con fase RED en R1-R4, R7, R8,
  R9, R11-R16 y R21, y campaña de mutación completa (rigor `critico`) sin supervivientes no aceptados por el humano.
- **R26.** Un test de **compatibilidad** debe recorrer las peticiones de caso de uso de F-009, F-015, F-007 y F-016
  (sus dobles: `ctrpro` con dto no legible o vacío) y comprobar que con `dto` ausente, `null` o 0 las filas, el SQL
  grabado, la respuesta (`model_dump(mode="json")`) y la traza son idénticos; y otro, que con un `ctrpro` de dto legible
  solo cambian `tot`, `pre`, `ivacuo` de esa línea, `impbru`/totales de la cabecera, el `mov` y las claves de R16 (en
  la proforma a origen, además `importe_origen_cadena`).
- **R27.** MANUAL (humano), tras desplegar: previa de un albarán con dto de la obra 0692 (sin vincular), de una
  vinculada con dto, de una vinculada sin dto contra un `ctrpro` con dto (R15) y de una proforma de mes contra un
  contrato con dto (R21), comparadas con documentos del escritorio; y, con autorización expresa para esa escritura, un
  `commit:true` de albarán revisado en la UI (P.Bruto, Dto, Precio, Importe, totales, `mov`), repetido (`idempotente`)
  y anulado desde la UI (nunca `DELETE`). Comandos: design §V.
- **R28.** El sistema debe actualizar **antes de implementar** el contrato con albaranes a la v8.4 y el de proformas a
  la v1.3 (design §Contratos) y avisar a las dos sesiones; y en el mismo trabajo `azure-apps/sigrid_api.md` (§8.6,
  §8.10, §9.4 y §12: el motivo de «`canfac·pre`», P7), `docs/ARCHITECTURE.md` (§Semántica 9, el modo extendido y la
  proforma) y el docstring de `sigrid_albaran`.

## Fuera de alcance

Descuentos en cascada y de cabecera (`impdes`); `dto` en el clásico, `albaran-directo` y en la petición de
`sigrid/proforma` (P4); recargos (`dto` negativo); leer el `dto` en `idempotente`; las 100 cabeceras con `totiva` ≠
Σ `ivacuo` (M47); las arrastradas de F-016 (copian su fila anterior tal cual); cambiar la tolerancia de `existente`;
`dcf`/`dcfpro` (F-008).
