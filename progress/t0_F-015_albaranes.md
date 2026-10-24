# T0 de F-015 · Qué cambia para albaranes (contrato v8.3)

Resumen para la sesión de albaranes del cambio del contrato
[`specs/F-009-alta-albaran-compra/contrato_albaranes.md`](../specs/F-009-alta-albaran-compra/contrato_albaranes.md) a la
**v8.3** (2026-10-24), que acompaña a la spec F-015 v2 de sigrid-api, aprobada por el humano el 2026-10-24. El texto del
contrato manda; esto es la lista de lo que tienen que revisar. **Falta su acuse** antes de implementar.

## La petición (§2) no cambia de forma

Mismos campos y mismas reglas. Dos correcciones de texto:

- **`usu`** (§2.1 l. 199, §2.4.9 l. 264, H1 l. 506; numeración de la v8.3): el contrato decía `ALTA_SIGRID_USUARIO`; hoy es el `usu` de quien
  aprueba o, si no lo hay, `ALTA_SIGRID_USUARIO_RESPALDO`. En §7 (l. 1101, el `usu` del adjunto) queda **a confirmar** por
  albaranes.
- **`empide`**: sigrid-api **no** lo deduce del `usu` (en Sigrid no hay clave que lo permita). Sigue llegando en la
  petición o, con `null`, `SIGRID_ALBARAN_EMPIDE`. Lo resuelve albaranes en su F-069.

## La cabecera (`con` y `dca`) deja de clonarse

- Se construye **columna a columna** desde una lista blanca: petición, obra, cálculo, valor fijo o la **cascada contrato →
  albarán anterior → proveedor**, igual para todas las columnas: cada una sale del primer origen que la trae con valor.
  Sin contrato, albarán anterior (por CIF) → proveedor.
- La cascada cubre la identidad del proveedor, la forma de pago (de los campos estructurados del contrato, nunca de su
  texto), el efecto, el banco, la cuenta, la condición de envío, la dirección e `ivadif`.
- El albarán anterior es el último `AC` de clase 0 del proveedor en la empresa de la obra y **nunca una proforma** (ni por
  serie ni por referencia `PROF…`). Es **opcional**: sin él, el alta sigue.
- **Columnas a 0 o vacías** (lo que deja el alta a mano): facturación (`idefac`, `fecfac`, `horfac`, `antestfac`), cadena,
  divisa (`tot*div`), fechas previstas (`fecent`, `feclim`), `cocide`, Documentum (`dtumID`); `tipgar` −1.
- `cabecera` y `filas.dca` de la respuesta traen esas columnas (sin las bancarias, como hasta ahora).
- `contrato.template_ide` pasa a ser el `ide` del albarán anterior usado (0 sin él).

Qué hace sv9: nada (F-053 R16 no guarda estas columnas).

## Retención del contrato

- Con contrato, sigrid-api escribe **una `dcarec`** copiada de su único recargo (`ctrrec`) y el **total neto**.
- Respuesta: `totales.tot` (neto = `totdoc` − retención), `totales.retenciones` y `totales.n_retenciones` (0 o 1);
  `filas.dcarec[]`; en `idempotente`, `tot` y `retenciones`. `totdoc` sigue sin retención.
- Escribe además el applock `SIGRID_IDE_dcarec`.
- Sin contrato, ninguna retención.

Qué hace sv9: el neto a pagar es `tot`. La comparación de la previa es por línea y no cambia.

## Códigos

| Código | Tipo | Cuándo | Recomendación para sv9 |
|---|---|---|---|
| ~~`proveedor_sin_albaran_previo`~~ | error (retirado) | ya no llega: sin albarán anterior el alta sigue | quitar su mapeo |
| `proveedor_no_encontrado` | error de cabecera | sin contrato: ni albarán anterior por CIF ni proveedor vivo con ese CIF en la empresa de la obra | `no_admitido` |
| `proveedor_ambiguo` | error de cabecera | sin contrato ni albarán anterior por CIF: varios proveedores vivos con ese CIF (medido: 4 CIF) | `no_admitido` |
| `retencion_no_soportada` | error de cabecera | el contrato tiene más de un recargo, o uno que no se sabe calcular (15 de 651 contratos); también en previa | `no_admitido`; sin mapear, H25 lo lleva a `error` |
| `retencion_del_contrato` | aviso de cabecera | se escribe la retención del contrato (código, porcentaje, base y cuota en el mensaje) | informativo; **fuera** de `ALTA_SIGRID_AVISOS_BLOQUEANTES` (~89 % de los albaranes de contratos con retención) |
| `cabecera_sin_dato` | aviso de cabecera | ningún origen trae el pago, o el banco con efecto de confirming o transferencia; se escribe el vacío del alta a mano y el mensaje nombra las columnas | informativo; sv9 decide si lo hace bloqueante (medido: 4 de 426 con contrato, 4 de 234 sin él) |

## Lo que sigrid-api no hace (§4.3)

No interpreta el texto ni el PDF del contrato; no deduce `empide` del `usu`; no pone retención sin contrato ni la de un
recargo no soportado.

## Lo que se pide a albaranes

1. Acuse de la v8.3.
2. Mapeos de los tres códigos nuevos y retirada del de `proveedor_sin_albaran_previo`.
3. Confirmar el `usu` del adjunto (§7, l. 1101).

## Acuse de albaranes (2026-10-24, aprobado por su humano)

1. **De acuerdo con la v8.3**: no les obliga a cambiar nada (sv9 no guarda esas columnas; la previa compara por línea).
2. **Mapeos en sv9** (con texto en el panel de sv4): `proveedor_no_encontrado`, `proveedor_ambiguo` y
   `retencion_no_soportada` → `no_admitido`; `retencion_del_contrato` → aviso informativo, fuera de
   `ALTA_SIGRID_AVISOS_BLOQUEANTES`; `cabecera_sin_dato` → informativo y visible en el panel, no bloqueante;
   `proveedor_sin_albaran_previo` → lo retiran al verificar nuestro despliegue (mantenerlo no hace daño).
3. **`usu` del adjunto (§7)**: confirmado, el mismo `usu` de la petición de alta. Con su F-069 (desplegada) se resuelve
   por la lista de equivalencias de sv9 (`ALTA_SIGRID_EQUIVALENCIAS_USUARIO`), luego el login de quien aprueba
   (`dbo.usu.cod`) y si no `ALTA_SIGRID_USUARIO_RESPALDO`. Piden ese texto en §2.1, §2.4.9, H1 y §7.
4. **Despliegue**: avisarles **antes** de desplegar F-015; sv9 y sv4 (con los mapeos nuevos, en una feature corta suya) se
   despliegan antes o a la vez; si no, `retencion_no_soportada` caería en `error`. Si cambia el nombre de algún código
   antes de publicar, avisarles.
5. **Limpieza** (D11): de acuerdo, tras nuestro despliegue y con autorización del humano. **No filtrar por `empide`
   2425207** (con su F-069 las altas nuevas llevan el empleado de quien aprueba): filtrar por `synckey LIKE 'ALB-%'` más
   la lista de `con.ide` que pueden dar con un script de solo lectura. Su humano decide **no** corregir el `empide` de las
   altas ya escritas.
