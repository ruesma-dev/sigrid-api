<!-- progress/verificacion_F-018.md -->
# F-018 · Verificación en producción (T19-T20)

**Despliegue (2026-10-30, lo lanzó el humano):** `func azure functionapp publish` desde `dev` `6339617` (merge de
F-018), «The deployment was successful!», host `Running`. Sin App Settings nuevas. Push de `dev` confirmado
(`origin/dev` = `6339617`).

## T19 · V0-V3 y V5 (líder, 2026-10-30; solo lecturas y previas `commit:false`)

Guion: `specs/F-018-descuento-por-linea/verificacion_manual.md`, traducido a Python desde el scratchpad (mismas
consultas parametrizadas y mismos cuerpos; ningún `commit:true`). Ninguna lectura vino `truncated`.

| Paso | Caso | Resultado |
|---|---|---|
| V1a | `AC26/30435`, obra 0692, `MA9999`: 48 uds, `tar` 11,2, `7%`, `tot` 499,97, `pre` 10,416041…, `impbru` 537,6, `totbas` 499,97 | encontrado |
| V0 | Previa sin `dto` de esa línea | `previsto`; líneas **sin** `dto` ni `precio_bruto`; `dto` `''`, `pre` = `tar` = 11,2, `tot` 537,6; `impbru` = `totbas` = 537,6 |
| V2 | La gemela con `dto` 7 | `previsto`; `tar` 11,2, `dto` `7%`, `tot` **499,97**, `pre` **10,416041…** (= `tot`/`can`), iguales al escritorio; `impbru` **537,6** y `totbas` **499,97**, iguales; `mov.pre` = `prc` = neto; respuesta con `dto` 7 y `precio_bruto` 11,2; sin avisos de línea |
| V1b | `ctrpro` 257586 (`CTSB26/0331`, obra 0710): `tar` 175,98, `2%`, `pre` 172,460421…; albarán del escritorio `AC26/30904`: 30 uds, `tot` 5.173,81, `pre` 172,460333… | encontrado |
| V3 r1 | Su bruto y su dto | `previsto`; `tot` **5.173,81** y `pre` 172,460333… como el escritorio; `impbru` 5.279,4; sin `precio_distinto_del_contrato` ni `dto_distinto_del_contrato` |
| V3 r2 | Dto 3 frente al 2 del contrato | `previsto`; `dto_distinto_del_contrato` «El descuento pedido (3%) no es el de la linea de contrato (2%)»; sin aviso de precio; `tot` 5.121,02 |
| V3 r3 | Sin `dto`, con el `pre` neto del `ctrpro` (R15) | `previsto`; `tar` 175,98 y `dto` `2%` copiados del `ctrpro`; `tot` **5.173,81** y `pre` **172,460333…**, iguales al albarán del escritorio; respuesta con `dto` 2 y `precio_bruto` 175,98; sin avisos de precio ni de dto |
| V1c | `PROF26/01377` (`CTSB26/0281`, obra 0713, 2026-10-28), 7 líneas vinculadas al `1%` | encontrado |
| V5 | Previa de proforma de mes con esas 7 líneas, `precio` = `ctrpro.pre`, `otra_del_mes` | `previsto`; las 7 con `tar`, `dto` y `tot` **iguales** a la proforma del escritorio y `pre` igual (diferencia 0 a 8 decimales); `impbru` **85.050,02** = Σ round(`can`·`tar`, 2) y `totbas` **84.199,51** = Σ `tot`; avisos de hoja `cod_provisional`, `retencion_del_contrato`, `contrato_a_origen`, `otra_del_mes` (los de siempre) |

Avisos ajenos a F-018, previstos en el guion: `sin_partida_en_linea_con_partida` en V3 (los cuerpos no llevan
`partida`), `retencion_del_contrato` (RET5 de `CTSB26/0331`) y `stock_negativo` en V5. **T19: sin discrepancias.**

**Corrección sobre V1a/V2:** `AC26/30435` no es un albarán puro del escritorio: su `synckey` es `ALB-…`, nació por la
API desde albaranes y su línea se retocó después en Sigrid. Sus cifras siguen la regla de M46; el contraste con
documentos del escritorio lo dan V3 y V5.

## T20 · V4 (2026-10-30, autorización expresa del humano; obra 0404)

El humano fijó la obra y dejó al líder elegir proveedor: el del último albarán de la 0404. Previa, `previsto`. Con
`commit:true`, `creado`: `AC26/31378` (`con_ide` 2864560), 48 uds de `MA9999`, `tar` 11,2, `7%`, `pre` 10,416041…,
`tot` 499,97, IVA 104,99; `impbru` 537,6, `totbas` 499,97, `totdoc` 604,96; `mov` 840855 al neto. Filas leídas iguales a
la respuesta y a V2.

- **Cotejo por lectura con `AC26/30435`:** de 71 columnas de `dcapro` difieren 12 y de 145 de `dca` difieren 31, todas de
  identificadores, proveedor, obra, fecha, partida o facturación; ninguna de cálculo.
- **UI (captura del humano):** Uds. 48,00, Precio/Ud 11,2, Dto 7%, Importe 499,97, Importe/Ud 10,42, total 604,96.
- **Relectura tras la UI:** línea, cabecera y `mov` sin cambios. **No consta** que el humano abriera y cerrara la línea:
  la captura enseña la ficha.
- **Repetición:** solo en dry-run (`commit:false`), `idempotente`, mismo `con_ide`, sin `dto` ni `precio_bruto`, una fila
  en `dca`, `dcapro` y `mov`. El `commit:true` repetido lo bloqueó el clasificador de la sesión y no se insistió.
- **Anulación:** desde la UI, por el humano. Lecturas: `con`, `dcapro`, `mov` y `dca` por `synckey`, **0, 0, 0 y 0**.

Aparte de F-018: `dca.empide` sale del valor por defecto (`sigrid_albaran_empide`), que en la UI muestra como Empleado a
una persona real aunque `usu` sea `prueba`. Ya era así; no es de esta feature.
