<!-- specs/F-008-registrar-factura/requirements.md -->
# F-008 · Registrar facturas de compra: alta en REC, sin contabilidad

Rigor **critico**. Cifras de [`progress/explore_F-008.md`](../../progress/explore_F-008.md) (M52-M60). Alcance pendiente de P1-P10 (`design.md` §9).

**Alta en REC, sin contabilidad.** En REC y COM no hay asiento ni `regiva` (M53): nacen con «Contabilizar» en el escritorio
(M55). Ese paso **no cabe con seguridad aquí** (19 familias de cuenta, ISP, deducibilidad, periodos de IVA) y no se reproduce;
si se pidiera, `blocked` por LÍMITE DE MICROSERVICIO. Sí se escribe lo que arrastra el alta: `con`, `dcf`, `dcfpro`, `dcfrec`,
`pag`, `consii`, `log` y las marcas de los orígenes (`dcaprodes`, `canfac`, estados de `dca`, `con` y `ctr`).

**Cobertura:** serie `FR<aa>/`, una obra y un contrato, albaranes o proformas **de mes**, enteros y contabilizados: **~80 %**
de FR26 (estimación: 91,8 % todo albarán menos ~9,5 % a origen y casos raros). El resto, por el escritorio.

## Requisitos

### Entrada y autorización

R1. CUANDO llegue `POST /api/sigrid/factura`, el sistema debe validar el cuerpo con `extra="forbid"` y números estrictos, y
un cuerpo no válido debe dar 400 «Solicitud invalida.» sin eco de valores.

R2. El sistema debe tratar toda petición sin `commit: true` como previa: mismas validaciones y misma respuesta, sin ejecutar
ninguna sentencia de escritura.

R3. SI llega `commit: true` y `SIGRID_FACTURA_WRITE_ENABLED` no es verdadera, ENTONCES el sistema debe responder 400
`escritura_facturas_deshabilitada`, después de validar el cuerpo y antes del caso de uso, sin escribir. Ninguna otra llave la abre.

R4. SI llega `commit: true`, ENTONCES el sistema debe exigir además `SIGRID_DOMAIN_WRITE_ENABLED`, credenciales de escritura
y la base en `ALLOWED_WRITE_DATABASES`, donde una lista vacía no abre (`base_de_datos_no_permitida`).

R5. SI `referencia_externa` no empieza por un prefijo de `SIGRID_FACTURA_PREFIJOS_REFERENCIA`, ENTONCES el sistema debe
responder `referencia_no_permitida`. La lista vacía no admite ninguno.

R6. SI las líneas resultantes superan `SIGRID_FACTURA_MAX_LINEAS` (por defecto 500; máximo medido, 373), ENTONCES el sistema debe
responder `demasiadas_lineas` sin escribir.

### Orígenes (qué se puede facturar)

R7. El sistema debe resolver cada código de `albaranes` a un `con.tip` 14 de la empresa de la obra; SI alguno no existe,
ENTONCES debe responder `albaran_no_encontrado` con el código en `details`.

R8. SI los albaranes no son todos del mismo `entide` y este no tiene el `cif_proveedor` de la petición, ENTONCES el sistema
debe responder `origen_de_otro_proveedor`.

R9. SI los albaranes son de más de una obra o de más de un contrato (`dca.ctride`), ENTONCES el sistema debe responder
`varias_obras` o `varios_contratos`. La obra debe pertenecer a `SIGRID_ALBARAN_EMPRESAS_OBRA`.

R10. SI un albarán no está en `con.est` CON resuelto contra `conest` o no tiene asiento `tip 20` con su mismo `cod` en su
empresa, ENTONCES el sistema debe responder `origen_sin_contabilizar` sin escribir.

R11. SI alguna línea de un albarán con `can` ≠ 0 tiene `canfac` ≠ 0 o `dcaprodes` con destino `tip 15`, ENTONCES el sistema debe
responder `origen_ya_facturado` con la línea y su factura.

R12. SI un albarán tiene `dca.docoritip` 1 (a origen), ENTONCES el sistema debe responder `origen_a_origen_no_soportado`.

R13. El sistema debe tomar **todas** las líneas con `can` ≠ 0 de cada albarán, sin admitir selección de líneas.

### Importes

R14. El sistema debe copiar cada línea de su `dcapro` (`proide`, `can`, `pre`, `tar`, `dto`, `tot`, `ivaide`, `ivacuo`, `cenide`, `caaide`,
`paride`, `natide`, `almide`, `obride`, `res`, `tex`, `cod2`, `unimed`, `prepma`, `dncide`, `dncproide`), sin recalcularla.

R15. El sistema debe calcular `totbas` = Σ `tot`, `impnet` = `totbas`, `impbru` = Σ bruto de línea, `totiva` = Σ `ivacuo`,
`totdoc` = `totbas` + `totiva`, `tot` = `totdoc` − retención y `totpag` = `tot`.

R16. SI `total_base` difiere de `totbas` en más de 0,01, `total_iva` de `totiva` en más de 0,05, o `total_factura` de `tot` en más de
0,05, ENTONCES el sistema debe responder `totales_no_cuadran` con los dos juegos de cifras, sin escribir. El sistema no debe
ajustar líneas ni IVA para que cuadre: ese caso se registra en el escritorio.

R17. SI `total_base` no es positivo, ENTONCES el sistema debe responder `abono_no_soportado`.

R18. DONDE los albaranes lleven `dcarec`, el sistema debe escribir **una** `dcfrec` con el `recide`, `valpor`, `reccla` y `cueide` de la
`dcarec`, `bas` = `totbas` y `cuo` = round(`bas`·`valpor`, 2); SI los albaranes llevan recargos distintos o más de uno, ENTONCES
debe responder `retencion_no_soportada`.

### Lo que escribe

R19. CUANDO se confirme, el sistema debe escribir en **una** transacción: `con` (`tip` 15, `cod` de la serie, `est` REC resuelto
contra `conest`), `dcf` (`cla` 1001, `synckey` = `referencia_externa`), `dcfpro` ×N, `dcfrec` ×0-1, `con` + `pag` ×M, `consii` ×1,
`dcaprodes` ×N y la fila de alta de `dbo.log` (`ope 1`), y los `UPDATE` de R24-R26.

R20. El sistema debe reservar `cod` e `ide` dentro de la transacción, bajo `sp_getapplock` en orden fijo, y `cod` = `FR<aa>/` + 5
cifras con `aa` del año de `con.fec`, siendo `con.fec` la fecha de la operación, y `MAX` numérico + 1 en la empresa de la obra.

R21. SI un `INSERT` choca por clave, ENTONCES el sistema debe repetir la transacción entera recalculando `cod`, `ide` y estados hasta
`DOMAIN_WRITE_MAX_RETRIES`; agotados, debe responder `colision_de_clave` con el ERP intacto.

R22. El sistema debe poner `dcfpro.cueide` = `prv.cuepdtide` y `dcf.cueide` = `prv.cueide`; SI alguna vale 0, ENTONCES debe responder
`proveedor_sin_cuenta` sin escribir.

R23. El sistema debe escribir las columnas de `con`, `dcf`, `dcfpro`, `pag`, `dcfrec`, `consii` y `dcaprodes` **por lista blanca**, sin
clonar ninguna fila. `consii` con `tipcom` A0, `tipdoc` F1, `claope` 01, `emiter`, `facsimcua`, `facsinide` y `difplaenv` N, `desope`
= `con.res` y `regivaide` 0.

### Marcas en los orígenes

R24. CUANDO se escriba una línea, el sistema debe sumar su `can` a `dcapro.canfac` con un `UPDATE` condicionado a `canfac` = 0, y si
no afecta a una fila debe revertir todo y responder `origen_ya_facturado`.

R25. El sistema debe pasar cada `dca` a `estfac` 1, `fecfac`/`horfac` = la operación y `antestfac` 3, y su `con.est` de CON a FAC,
resueltos contra `conest`; no debe escribir `dca.idefac`.

R26. DONDE la línea de albarán apunte a un `ctrpro`, el sistema debe sumar la `can` a `ctrpro.canfac` y refrescar `ctr.estfac` con
`estados_contrato` (F-009).

### Cartera

R27. El sistema debe escribir un `pag` `cla` 0 con `tot` = `totpag`, y, si hay retención `reccla` 5, otro `cla` 2 con `tot` = `cuo` y
`retide` = `recide`; con `reccla` 3, solo el de `cla` 0. `cod` `<cod>_01`, `<cod>_02`; `con.est` PDT resuelto contra `conest`.

R28. El vencimiento del `cla` 0 debe ser `vencimiento` de la petición si viene, y si no, la regla de `design.md`, emitiendo el aviso
`vencimiento_estimado` (acierta el 77,3 %, M58). El del `cla` 2 debe ser `con.fec` + los meses de la `R` de `pagfor` (450R, 15).

R29. SI `pagfor` tiene más de un plazo de pago o ningún plazo legible, ENTONCES el sistema debe responder
`forma_de_pago_no_soportada`.

### Lo que NO escribe

R30. El sistema no debe escribir `asi`, `apu`, `regiva`, `regirp`, `mov`, `dcfproana`, `dcfpropar`, `dcfprodes`, `dcfproimp`, `confir`, ni
pasar la factura de REC ni tocar `pag.remide`, `fecrea` o `regivaide`. No debe ejecutar `DELETE`.

### Idempotencia y duplicadas

R31. SI existe `dcf.synckey` = `referencia_externa` con el mismo proveedor y número, ENTONCES el sistema debe responder `idempotente` con
esa factura y sin escribir, comprobándolo otra vez bajo el applock; con otros datos, `referencia_en_conflicto`.

R32. SI existe otra `dcf` de ese `entcif` y `entref` que no esté en RECH, ENTONCES el sistema debe responder `factura_ya_registrada` con su
`cod`, sin escribir, también bajo el applock.

### Respuesta y traza

R33. El sistema debe responder `estado` (`previsto`, `creado`, `idempotente`), `cod`, `con_ide`, `totales`, `retencion`, `vencimientos`,
`origenes`, `lineas`, `filas`, `avisos` y `pendiente_en_sigrid` (siempre: comprobar y contabilizar).

R34. CUANDO se confirme, el sistema debe releer antes del COMMIT cada fila escrita y cada marca, y revertir si no cuadran.

R35. El sistema debe registrar una línea por petición (obra, referencia, `commit`, `estado`, `cod`, nº de líneas, códigos, duración) y
**nunca** textos, nombres, CIF, número de factura ni importes.

## Compatibilidad

R36. El sistema debe dejar sin cambios el contrato de `sql/read`, `sql/write`, `sigrid/albaran`, `sigrid/albaran-directo`,
`sigrid/proforma` y demás rutas; ningún consumidor actual llama a la ruta nueva.

R37. El sistema debe arrancar con los ajustes nuevos ausentes, con `SIGRID_FACTURA_WRITE_ENABLED` falsa por defecto.

R38. `azure-apps/sigrid_api.md` y `docs/ARCHITECTURE.md` deben documentar la ruta, los ajustes, los applocks y lo que **no** hace.

Criterios manuales: T17-T19 de `tasks.md` (previas; una grabación solo con autorización expresa; V1-V4 de `explore_F-008.md`).
