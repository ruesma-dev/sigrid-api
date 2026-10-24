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

## T20 y T21

Pendientes de decisión del humano. Albaranes comunica (2026-10-24) que su humano ha decidido **no** limpiar las altas ya
escritas y que no mandará la lista de `con.ide`.
