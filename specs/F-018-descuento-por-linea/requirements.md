# F-018 · Requisitos (v1)

**El modo extendido de `POST /api/sigrid/albaran` (F-009/F-015) acepta un descuento simple por línea, `lineas[].dto`, y
registra la línea como la registra Sigrid: unitario original, cantidad, porcentaje e importe neto.** Lo pide albaranes
(su F-110; obra 0692): hoy sv9 manda `precio` = importe/cantidad y el descuento se pierde. Objetivo fijado por el humano
el 2026-10-28 (R1). Medidas **Mn**: [`progress/explore_F-018.md`](../../progress/explore_F-018.md) (M45-M51).
Decisiones **Dn** y preguntas **Pn**: design §Decisiones y §Preguntas. F-009 y F-015 mandan en lo que aquí no se repite.

> **Lo que la medición cambia del encargo (D1, P1, bloqueante para la PARADA 1).** El humano y albaranes pidieron el
> unitario original en `dcapro.pre`. Sigrid lo guarda en **`tar`** («P.Bruto») y deja en `pre` el **neto** =
> `tot`/`can` (M46: 23.990 de 23.993 líneas; `ctrpro` igual, M49h); el `mov` y el PMP van con ese neto (M48). Esta
> spec registra los cuatro datos del objetivo en las columnas donde Sigrid los guarda. Si el humano mantiene `pre` =
> bruto, cambian R1, R8 y R9 (alternativa B de design §Decisiones).

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
  `0.01` → `0,01%`).
- **R4.** El sistema debe validar `dto` con Pydantic en `LineaAlbaranIn`: opcional, número JSON (`strict`, finito),
  0 ≤ `dto` ≤ 100 y como mucho 2 decimales (`Decimal(repr(dto))`); si no, 400 `Solicitud invalida.` sin `codigo`
  (F-012). No hay cascada (`"10+5"` es un texto: no valida; M45: ninguna desde 2020).
- **R5.** El sistema debe calcular `ivacuo` = `redondear_euros(tot · iva)` sobre el `tot` neto de R1, como hoy (M47d).
- **R6.** SI `precio` < 0, ENTONCES fallo de línea `precio_negativo` como hoy, con o sin `dto`.

## Compatibilidad (criterio de aceptación de F-018)

- **R7.** CUANDO una línea venga sin `dto`, con `dto: null` o con `dto: 0`, el sistema debe construirla exactamente
  como hoy (mismas funciones con los mismos argumentos, mismas filas, mismo SQL y misma respuesta salvo los campos
  nuevos de R16); y los tests y dorados de F-007, F-009 y F-015 deben pasar **sin modificarlos**.

## Cabecera, `mov` y contrato

- **R8.** El sistema debe sumar en la cabecera los importes **de las filas escritas**: `totbas` = Σ `tot` (neto),
  `totiva` = Σ `ivacuo`, `totdoc`, `tot`, `totpag` y la retención de F-015 sobre esos netos; `impnet` = `totbas` e
  `impdes` 0 (M47); e `impbru` = Σ por línea de `redondear_euros(cantidad · tar)` en las líneas con `dto` > 0 y de
  `tot` en las demás (M47: `impbru` = Σ bruto en 7.541 de 7.541). Sin líneas con `dto`, `impbru` = `totbas` como hoy.
- **R9.** El sistema debe escribir el `mov` de una línea con `dto` con `pre` = `prc` = el `dcapro.pre` neto de R1 y
  calcular con él el balance y el PMP (`almpma`) de F-009 R19; `prepma`, igual que hoy (M48: 22.366 de 22.368).
- **R10.** El sistema debe escribir `ctrprodes.can` y sumar `canser` por **cantidad**, como hoy: el `dto` no los toca
  (M49g: 2.267 de 2.267).

## Vinculadas (D3)

- **R11.** CUANDO una vinculada traiga `dto` > 0, el sistema debe escribir R1 con el `precio` y el `dto` **pedidos**,
  sin aplicar la opción C de F-009 R17 y sin copiar `pre`, `tar` ni `dto` del `ctrpro` (validar, no pisar).
- **R12.** CUANDO una vinculada con `dto` > 0 tenga |`precio` − `ctrpro.tar`| > 0,0001, el sistema debe añadir el aviso
  de línea `precio_distinto_del_contrato` (el de F-009, con un mensaje que diga que compara el precio bruto).
- **R13.** CUANDO una vinculada con `dto` > 0 tenga un `ctrpro.dto` distinto del pedido (leído con R14; un `ctrpro`
  sin dto vale 0), el sistema debe añadir el aviso de línea nuevo **`dto_distinto_del_contrato`**, informativo, con
  los dos porcentajes en el mensaje (M49a: 2.243 de 2.244 coinciden; 23 líneas con dto y `ctrpro` sin él).
- **R14.** El sistema debe leer el texto de un `dto` de Sigrid como número: vacío o `NULL` → 0; `N%` o `N,NN%`
  (coma decimal, espacios alrededor) → `N`; cualquier otra forma (cascada, sin `%`) → **no legible**, que para R13
  cuenta como distinto, con mensaje propio.
- **R15.** CUANDO una vinculada venga sin `dto` (o con 0) y su `ctrpro` tenga dto, el sistema debe seguir la opción C
  de hoy (comparar `precio` con `ctrpro.pre`, que es neto, M49h, y copiar `pre`, `tar` y `dto` si casa): es R7.

## Respuesta, avisos y trazas

- **R16.** El sistema debe añadir a cada línea de la respuesta, en `previsto` y `creado`, `dto` (el porcentaje de la
  fila escrita leído con R14: el pedido, el del `ctrpro` copiado por la opción C o 0; `null` si no es legible) y
  `precio_bruto` (= `tar` escrito); `precio` (= `pre`) y `total` (= `tot`) siguen siendo los de la fila. En
  `idempotente`, los dos `null` (L11 no cambia).
- **R17.** `CODIGOS_AVISO` debe aceptar `dto_distinto_del_contrato`; los demás conjuntos cerrados no cambian.
- **R18.** El sistema debe trazar (F-009 R32) además `n_lineas_con_dto`; nunca porcentajes, precios ni importes.

## Alcance de las demás rutas (D2)

- **R19.** El modo clásico de `sigrid/albaran` y `sigrid/albaran-directo` no cambian: ni modelo, ni caso de uso, ni
  sentencias, ni dorado (`tests/fixtures/f009_caracterizacion.json`).
- **R20.** `sigrid/proforma` no admite `dto` en sus líneas (`LineaProformaIn` con `extra="forbid"` lo rechaza con 400
  sin código, como hoy) y su traducción al núcleo no lo pasa: sus filas no cambian (P4). Sus líneas de respuesta sí
  llevan los campos de R16, porque comparten `LineaResultado`.

## SQL, seguridad y escritura

- **R21.** El sistema no debe añadir ni cambiar ninguna sentencia SQL (ni lecturas, ni L11, ni `INSERT`, ni `UPDATE`):
  `dto` viaja en la fila clonada de `dcapro` y `tar`/`pre`/`tot` en sus columnas de siempre. El control negativo de
  F-009 R31 sigue pasando.
- **R22.** En `commit:true` el sistema debe escribir las filas de R1, R8 y R9 en la transacción de F-009 R25, con las
  llaves, applocks, reintento y relecturas de hoy.

## Pruebas, verificación y documentación

- **R23.** El sistema debe cubrir R1-R22 con tests sin red ni BBDD (`test_f018_rN_*`), con fase RED en R1-R4, R7, R8,
  R9, R11-R14 y R16, y campaña de mutación completa (rigor `critico`) sin supervivientes no aceptados por el humano.
- **R24.** Un test de **compatibilidad** debe recorrer las peticiones de los tests de caso de uso de F-009, F-015 y
  F-007 (vinculadas con y sin dto en el `ctrpro`, sin vincular, devoluciones, retención, proforma) y comprobar que
  con `dto` ausente, `null` o 0 las filas, el SQL grabado y la respuesta (sin los campos de R16) son idénticos.
- **R25.** MANUAL (humano), tras desplegar: previa de un albarán con dto de la obra 0692 (sin vincular) y de una
  vinculada contra un `ctrpro` con dto, comparadas con un albarán del escritorio con el mismo dto; y, con autorización
  expresa para esa escritura, un `commit:true` revisado en la UI (P.Bruto, Dto, Precio, Importe, totales, `mov`),
  repetido (`idempotente`) y anulado desde la UI (nunca `DELETE`). Comandos: design §Verificación manual.
- **R26.** El sistema debe actualizar **antes de implementar** el contrato con albaranes a la v8.4 (design §Contrato) y
  avisar a albaranes; y en el mismo trabajo `azure-apps/sigrid_api.md` (§8.6, §9.4 y §12: el motivo de «`canfac·pre`»
  medido en M46), `docs/ARCHITECTURE.md` (§Semántica 9 y el modo extendido) y el docstring de `sigrid_albaran`.

## Fuera de alcance

Descuentos en cascada y de cabecera (`impdes`); `dto` en el clásico, `albaran-directo` y `sigrid/proforma` (P4);
recargos (`dto` negativo); leer el `dto` en `idempotente`; corregir el camino de la opción C cuando el `ctrpro` tiene dto
y la petición no (`impbru` = `totbas` y `tot` sobre el `pre` neto del `ctrpro`; P5); las 100 cabeceras con `totiva` ≠
Σ `ivacuo` (M47); `dcf`/`dcfpro` (F-008).
