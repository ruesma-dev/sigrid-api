<!-- progress/verificacion_F-015.md -->
# F-015 · Verificación manual

## Aviso y despliegue (2026-10-24)

- Albaranes avisado antes (líder): sv9 `r20261024-1838` y sv4 `r20261024-1841` desplegados con los mapeos de la v8.3
  (su F-104); los dos cambios posteriores (§4.1/§4.2 y `valpor` NULL) no les afectan.
- Humano: push de `dev` (`6faacd7..60db955`). Despliegue `func azure functionapp publish func-sigridapi-dev-huyke
  --python` desde `dev` `60db955` (lo lanzó el líder: el `!` del humano llegó con un espacio delante y no se ejecutó):
  «The deployment was successful!» a las 18:21:18 UTC, las 9 funciones listadas y el host `Running`. Sin App Settings
  nuevas. Hora comunicada a albaranes.

## T19 · Dry-runs V1-V4 (líder, autorizados por el humano el 2026-10-24)

Script Python en el scratchpad con la function key del `.env` local (nada al repo), `commit: false`, `usu` `prueba`,
`referencia_externa` `ALB-prueba-F015-1`…`4`. En las cuatro: HTTP 200 `previsto`, **0 filas `dca` con su `synckey`**
(nada escrito), facturación, fechas previstas, `cocide` y divisa a 0, `dtumID` `''` y `tipgar` −1.

| Paso | Caso | Resultado |
|---|---|---|
| V1 | Contrato `CTSB26/0734` con `RET5` | `dcarec` con `valpor` 0.05, `bas` 152.66 = `totbas`, `cuo` 7.63 (152.66 · 0,05 a céntimos); `tot` = `totpag` = 145.03 = `totdoc` − `cuo`; `retenciones` 7.63, `n_retenciones` 1; aviso `retencion_del_contrato` con RET5, 5 %, base y cuota; identidad, pago, efecto e `ivadif` = los del `ctr` |
| V2 | Contrato `CTSB26/0735` sin `ctrrec` | `filas.dcarec` vacía; `tot` = `totdoc` = 250.00; `retenciones` 0, `n_retenciones` 0; sin aviso de retención |
| V3 | Obra 0404, sin contrato, con albarán anterior | `template_ide` = el último `AC__/` de clase 0 de ese CIF que no es proforma (el esperado); identidad, pago, efecto, `dircon1` e `ivadif` = los de ese albarán (las bancarias no viajan en `filas.dca`, como hasta ahora); sin `dcarec` |
| V4 | Obra 0404, proveedor sin albarán anterior | el alta sigue: `template_ide` 0; `entide`/`entcod` del `prv`; `pagide`/`efeide` y `dirdir1` del `prv`, `pagtex`/`pagfor` de su `auxpag`; `dircon1` `''`, `ivadif` 0; sin `cabecera_sin_dato` (el `prv` trae pago) |

Resultado: **OK**. Tras el despliegue no había entrado aún ninguna alta real de albaranes (la última `ALB-%` es
`AC26/30665`, anterior). Albaranes comprobará en lectura las primeras.

## T20 · Grabación V5 (líder, autorizada expresamente por el humano el 2026-10-24: «graba uno en la 404»)

Contrato `CTSB19/0490` (obra 0404, un único `ctrrec` RET5 clase 5, `valpor` 0.05, sin `valfij` ni `ivaide`), una
línea vinculada (`ctrpro` 104172, 1 ud a 22,00), `usu` `prueba`, `referencia_externa` `ALB-prueba-F015-5`. Script
en el scratchpad: dry-run primero con el mismo cuerpo y parada ante cualquier discrepancia.

| Paso | Resultado |
|---|---|
| Dry-run | 200 `previsto`; `totbas` 22.00, `totdoc` 26.62, `tot` 25.52, `retenciones` 1.10 (= 22,00 · 0,05), `n_retenciones` 1 |
| Commit | 200 `creado`, `con_ide` 2860439, **`AC26/30670`**; aviso `retencion_del_contrato` |
| Lecturas | `dcarec` 44288 (`docide` 2860439, RET5, `bas` 22.0, `valpor` 0.05, `cuo` 1.1); `dca`: `totdoc` 26.62, `tot` = `totpag` = 25.52; facturación, `fecent`, `feclim` y `cocide` a 0; pago y efecto del contrato; `canser` de la línea 69 → 70 |
| Repetición | 200 `idempotente`, mismo `con_ide`, `tot` 25.52 y `retenciones` 1.1; una sola fila con su `synckey` |

**Pendiente:** revisión en la UI de Sigrid (retención y neto como en un albarán del escritorio) y **anulación de
`AC26/30670` desde la UI** por Administración (nunca `DELETE`); después, comprobar en lectura que no queda `con`, `dca`
ni `dcarec` con `docide` 2860439 y que el `canser` de `ctrpro` 104172 vuelve a 69.

**Cierre (2026-11-23):** el humano descarta la anulación («olvídate de ese albarán»). `AC26/30670` se queda en
Sigrid tal cual, con su `dcarec` y el `canser` 70 de `ctrpro` 104172; no se hacen las lecturas de comprobación. La
revisión en la UI tampoco se registró: se cierra sin ella.

## T21 · Limpieza: descartada

El humano la descarta el 2026-10-24, como el de albaranes. Las ~60 altas anteriores al despliegue conservan la
facturación, las fechas y el `cocide` copiados (32 con `idefac` de facturas de otros albaranes; no se ha medido qué hace
el escritorio al facturarlas).
