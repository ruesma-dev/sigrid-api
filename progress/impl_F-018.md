<!-- progress/impl_F-018.md -->
# F-018 · Informe del implementer

Spec v1.2 aprobada por el humano (P1-P10). Rama `feature/F-018-descuento-por-linea`. Rigor `critico`.

## T0 · Contratos (sin código)

Commit solo de documentos (`git show --stat` lo comprueba): ningún fichero de producción ni de tests.

- `specs/F-009-alta-albaran-compra/contrato_albaranes.md` → **v8.4**: párrafo de versión con lo que tiene que hacer
  albaranes (seis puntos); fila de fuentes; §2.2 (`precio` y fila nueva `dto`); §2.3 (sin vincular, remite a §2.2);
  §3.1 (`cabecera` con `impbru`, `precio`/`total` neto con dto, claves `dto` y `precio_bruto`, PMP con el neto,
  comparación de la previa); §3.2 (`precio_distinto_del_contrato` con dto y aviso nuevo `dto_distinto_del_contrato`);
  §3.4 (400 sin código por `dto` no válido); §4.2 (filas con dto, sin sentencias nuevas); §4.3 (lo de «no aplica
  descuentos» ya no es cierto: ahora dice qué descuentos aplica y cuáles no); H8 en la tabla de §5 y en su texto.
- `specs/F-007-registrar-proforma/contrato_proformas.md` → **v1.3**: párrafo de versión con lo que tiene que hacer
  `proformas` (cinco puntos); §2.2 (`precio` y nota: la línea no tiene `dto`, 400 sin código); §3 (la línea de
  contrato con descuento del `ctrpro`, de mes y a origen, con el ejemplo de design D9); §3.1 (excepción a «sin claves
  nuevas» en la de mes; `importe_origen_cadena` con el `pre` neto); §4 (aviso heredado `dto_distinto_del_contrato`,
  que hoy no sale, y el efecto en `existente` de reenviar con otra referencia); §6 (cómo lee `facturas` esas líneas);
  §8 (entrada v1.3).

Decisiones de redacción:

- **§4.3 del contrato con albaranes**: tasks T0 no lo lista, pero decía «no aplica descuentos (por eso sv9 manda el
  neto)», que con F-018 deja de ser cierto. Se corrige para que el contrato no se contradiga.
- **«Quién edita qué»**: la columna «Origen en albaranes» y §2.4 son de albaranes. En la fila nueva `dto` la columna va
  como «Propuesta para su F-110», y la columna de `precio` y la regla 4 de §2.4 no se tocan: el punto 6 de la v8.4 les
  pide que las pongan al día ellos.
- **Proformas, aviso `dto_distinto_del_contrato`**: va en §4 como heredado y «hoy no sale», que es lo que dicen la spec
  (R17) y el design (§La proforma: «Avisos R12/R13: nunca»).
- **§6 a `facturas`**: queda en el contrato de proformas. El texto de abajo para `proformas` dice que a `facturas` se
  le avisa aparte, porque los avisos los manda el líder (tasks T0). No se escribe aquí un tercer texto porque el
  encargo pide dos.
- Sin nombres de personas, proveedores ni CIF en lo añadido. En el contrato de proformas, la cabecera y §8 de la v1.2
  siguen diciendo «pendiente de revisión y de despliegue», aunque F-016 ya está desplegada (`progress/current.md`).
  No se toca porque queda fuera de T0; se lo apunto al líder.

Verificación de T0: MANUAL (humano). Faltan los acuses de las dos sesiones. `git show --stat` del commit de T0: solo
los dos contratos, `tasks.md`, este informe y `progress/current.md`.

### Aviso a `albaranes` (lo envía el líder)

> sigrid-api F-018 (spec aprobada, **sin implementar todavía**). Lo pedisteis en vuestra F-110: el **descuento por
> línea** en el modo extendido de `POST /api/sigrid/albaran`. El contrato sube a la **v8.4**
> (`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md`, el párrafo de la v8.4 al principio). Necesitamos
> vuestro acuse **antes de implementar**. Cambios:
>
> 1. Campo opcional nuevo `lineas[].dto`: porcentaje, número JSON de 0 a 100 y como mucho 2 decimales. Con él, `precio`
>    es el unitario **bruto**. Sin descuento, todo sigue como hoy (`precio` = importe/cantidad). No mandéis el neto
>    junto con `dto`, porque se descontaría dos veces. Un `dto` en texto o en cascada (`"10+5"`), fuera de rango o con
>    más decimales da 400 sin código: validadlo antes. Una cascada se convierte a un porcentaje único o va a revisión
>    (§2.2, H8).
> 2. Seguid comparando la previa por `total`. Con descuento, `total` = ROUND_HALF_UP(cantidad · precio · (1 − dto/100), 2)
>    y el `precio` de la respuesta es el **neto** (§3.1).
> 3. Las líneas con descuento traen dos claves nuevas en la respuesta, `dto` y `precio_bruto`. Las demás no, y en
>    `idempotente` nunca (§3.1).
> 4. **Os cambia sin que mandéis nada nuevo**: una vinculada sin `dto` que casa con un `ctrpro` con descuento se escribe
>    como Sigrid con el dto del contrato. Su `total` puede diferir **un céntimo** de round(cantidad·precio, 2), dentro
>    de vuestra tolerancia de 0,05, y trae `dto` y `precio_bruto` (§2.2).
> 5. Aviso informativo nuevo `dto_distinto_del_contrato`. Además, en una vinculada con `dto`,
>    `precio_distinto_del_contrato` compara el bruto con el `ctrpro.tar` (§3.2).
> 6. Actualizad vuestra parte del contrato: la columna «Origen en albaranes» de `precio` y de `dto` (§2.2) y la regla 4
>    de §2.4.
>
> Os avisamos cuando esté desplegada.

### Aviso a `proformas` (lo envía el líder)

> sigrid-api F-018 (spec aprobada, **sin implementar todavía**): descuento por línea. El contrato de
> `POST /api/sigrid/proforma` sube a la **v1.3** (`sigrid-api/specs/F-007-registrar-proforma/contrato_proformas.md`,
> el párrafo de la v1.3 al principio). La petición no cambia. Necesitamos vuestro acuse **antes de implementar**.
> Cambios:
>
> 1. Nada en la petición. Sigue sin `dto` (mandarlo da 400 sin código) y el `precio` de una línea de contrato sigue
>    siendo el de la hoja (§2.2).
> 2. Las líneas de contrato cuyo `ctrpro` tiene descuento se escriben ahora como Sigrid, de mes y a origen, con `tot` y
>    `pre` netos calculados desde el `tar` y el dto del contrato. Contad con **hasta un céntimo por línea así** entre
>    `importe_mes` y `totales.totbas` y, a origen, entre el ORIGEN de la hoja y `importe_origen_cadena` (§3, §3.1). La
>    comprobación de la hoja no cambia.
> 3. Esas líneas traen dos claves nuevas en la respuesta, `dto` y `precio_bruto`, también en las de mes. Las demás
>    líneas, `existente`, `idempotente` y las arrastradas no las traen (§3.1).
> 4. Reenviad siempre con la misma `referencia_externa` (sale `idempotente`). Con otra referencia, una proforma con más
>    de unas cinco de esas líneas puede no reconocerse como `existente` (§4).
> 5. Aviso heredado `dto_distinto_del_contrato`: hoy no sale en la proforma, pero mapeadlo como informativo si vuestro
>    conjunto de avisos es cerrado (§4).
>
> Os avisamos cuando esté desplegada.
