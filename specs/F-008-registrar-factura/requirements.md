<!-- specs/F-008-registrar-factura/requirements.md -->
# F-008 · Registrar facturas de compra: alta en REC, sin contabilidad (v2)

Rigor **critico**. Cifras de [`progress/explore_F-008.md`](../../progress/explore_F-008.md) (M52-M63). v2: cambio de alcance
del humano del 2026-10-30 (origen opcional, vencimientos del llamante, a origen, varios llamantes); decisiones P1-P17 en
`design.md` §9. **Alta en REC, sin contabilidad** (P1): se escribe lo que arrastra el alta (`con`, `dcf`, `dcfpro`, `dcfrec`,
`pag`, `consii`, `log`, marcas de los orígenes); el asiento, `regiva` y `regirp` los hace «Contabilizar» en el escritorio.
Cobertura estimada: **~95 %** de FR26 (de mes, a origen, mixtas y sin origen; fuera FRGG y abonos).

**La API registra y valida; no deduce.** El modo, los vencimientos y las líneas sin origen los decide el llamante.

## Entrada, llaves y llamantes

R1. CUANDO llegue `POST /api/sigrid/factura`, el sistema debe validar el cuerpo con `extra="forbid"` y números estrictos; un
cuerpo no válido da 400 «Solicitud invalida.» sin eco de valores ni `codigo`.
R2. SI no vienen `origenes` ni `lineas`; o `modo` es `"origen"` sin `origenes`; o se repite un código de `origenes`, ENTONCES el
sistema debe responder 400 sin `codigo` (R1).
R3. El sistema debe tratar toda petición sin `commit: true` como previa: mismas validaciones y respuesta, sin sentencias de
escritura.
R4. SI llega `commit: true` y `SIGRID_FACTURA_WRITE_ENABLED` no es verdadera, ENTONCES 400 `escritura_facturas_deshabilitada`,
tras validar el cuerpo y antes del caso de uso. Ninguna otra llave la abre.
R5. SI llega `commit: true`, ENTONCES el sistema debe exigir además `SIGRID_DOMAIN_WRITE_ENABLED`, credenciales de escritura y la
base en `ALLOWED_WRITE_DATABASES` (lista vacía no abre: `base_de_datos_no_permitida`).
R6. SI `referencia_externa` no empieza por un prefijo de `SIGRID_FACTURA_PREFIJOS_REFERENCIA`, ENTONCES `referencia_no_permitida`;
la lista vacía no admite ninguno. El sistema no debe tener lógica distinta por prefijo ni por aplicación (P15).
R7. SI `usu` no es un `dbo.usu.cod` existente, ENTONCES `usuario_no_valido`.
R8. SI las líneas a escribir superan `SIGRID_FACTURA_MAX_LINEAS` (defecto 500), ENTONCES `demasiadas_lineas`, aun en previa.

## Proveedor y obra

R9. CUANDO vengan `origenes`, el sistema debe tomar el proveedor de ellos (R12); CUANDO no, debe resolver `cif_proveedor` contra
`prv` de la empresa de la obra: ninguno da `proveedor_no_encontrado` y más de uno, `proveedor_ambiguo`.
R10. El sistema debe resolver `cod_obra` en la empresa de `SIGRID_ALBARAN_EMPRESAS_OBRA` (`obra_no_encontrada`); es obligatorio
sin `origenes`, y con ellos, SI no es la obra de los orígenes, ENTONCES `varias_obras`.
R11. El sistema debe poner `dcfpro.cueide` = `prv.cuepdtide` en las líneas de origen y `dcf.cueide` = `prv.cueide`; SI la que se
necesita vale 0, ENTONCES `proveedor_sin_cuenta`.

## Orígenes: albaranes y proformas (opcionales)

R12. El sistema debe resolver cada código de `origenes` a un `con.tip 14` (albarán o proforma) de la empresa de la obra
(`origen_no_encontrado`, con el código en `details`); SI no son todos del mismo `entide` con el `cif_proveedor` pedido,
ENTONCES `origen_de_otro_proveedor`; SI son de más de una obra o contrato (`dca.ctride`), ENTONCES `varias_obras` o
`varios_contratos`.
R13. SI un origen no está en CON (resuelto contra `conest`) o no tiene asiento `tip 20` con su `cod` en su empresa, ENTONCES
`origen_sin_contabilizar` (P4).
R14. SI una línea de origen con `can` ≠ 0 tiene `canfac` ≠ 0 o `dcaprodes` a un `tip 15`, ENTONCES `origen_ya_facturado` con la
línea y su factura.
R15. El sistema debe facturar **todas** las líneas con `can` ≠ 0 de cada origen, sin selección; las de `can` 0 (arrastradas de
una a origen) no pasan a la factura y quedan con `canfac` 0.

## Modo: de mes o a origen (P14)

R16. El sistema debe aceptar `modo` `"mes"` (defecto) u `"origen"`; SI algún origen tiene `dca.docoritip` distinto del modo
pedido (0 en mes, 1 en origen), ENTONCES `modo_no_coincide_con_origen` con los códigos; SI los orígenes mezclan modos,
ENTONCES `origenes_de_modos_distintos`. Las líneas sin origen no tienen modo.
R17. El sistema debe copiar cada línea de origen de su `dcapro` (`proide`, `can`, `pre`, `tar`, `dto`, `tot`, `ivaide`, `ivacuo`,
`cenide`, `caaide`, `paride`, `natide`, `almide`, `obride`, `res`, `tex`, `cod2`, `unimed`, `prepma`, `dncide`, `dncproide`) sin
recalcularla, con `docoritip` 14, `docoricod`, `docoriide`, `linoriide` y `canorilin` 0.
R18. En modo mes, el sistema debe escribir `canoriori` = `can`, `imporiori` = `tot`, `canoriant` e `imporiant` 0 (M56).
R19. En modo origen, el sistema debe escribir `canoriori` = `dcapro.canoriori`; `canoriant` e `imporiant` = el `canoriori` y el
`imporiori` de la `dcapro` de su `canorilin` (0 si no tiene); `imporiori` = `dcapro.imporiori` si la línea está vinculada
(`dcapro.linoriide` ≠ 0) y `imporiant` + `tot` si no (M63, 99,5 %). `dcf.docoritip` 0 en los dos modos.

## Líneas sin origen (P11, P16, P17)

R20. El sistema debe admitir en `lineas` (0..N): `producto`, `partida` y `paride` opcionales, `descripcion`, `unidad` opcional,
`cantidad`, `precio` e `iva` (código de `dbo.iva`). Cantidad o precio negativos se admiten (ajustes, M61).
R21. SI `producto` no está en `SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN` o no existe en la empresa (`tip 3`, sin baja), ENTONCES fallo
de línea `producto_no_permitido` o `producto_no_encontrado`; SI `iva` no está en `SIGRID_FACTURA_IVAS` o no existe, ENTONCES
`iva_no_valido`. Todos los fallos de línea, juntos en `lineas_no_validas`.
R22. El sistema debe resolver la naturaleza por `SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO`, y de ella `natide`, `cueide` (la `cua`
de `cuacomcod`) y `caaide`, y la partida, el almacén y el centro, con las reglas de F-009 R13b, R14, R14b y R15 (sus mismos
fallos de línea: `naturaleza_no_valida`, `partida_no_encontrada`, `analitica_no_resuelta`…).
R23. El sistema debe escribir la línea sin origen con `pre` = `tar` = `precio`, `dto` vacío, `tot` = round(`cantidad`·`precio`, 2),
`ivacuo` = round(`tot`·`iva.iva`, 2) (`Decimal`, `ROUND_HALF_UP`), `docori*`, `linoriide`, `canori*` e `impori*` a 0, sin
`dcaprodes` ni marcas.

## Importes y retención

R24. El sistema debe calcular `totbas` = Σ `tot`, `impnet` = `totbas`, `impbru` = Σ bruto, `totiva` = Σ `ivacuo`, `totdoc` =
`totbas` + `totiva`, `tot` = `totdoc` − retención y `totpag` = `tot`, sobre todas las líneas.
R25. SI `total_base` difiere de `totbas` en más de 0,01, `total_iva` de `totiva` en más de 0,05 o `total_factura` de `tot` en más
de 0,05, ENTONCES `totales_no_cuadran` con los dos juegos, sin ajustar nada.
R26. SI `total_base` no es positivo, ENTONCES `abono_no_soportado`.
R27. DONDE los orígenes lleven `dcarec`, el sistema debe escribir **una** `dcfrec` con su `recide`, `valpor`, `reccla` y `cueide`,
`bas` = `totbas` y `cuo` = round(`bas`·`valpor`, 2); recargos distintos o más de uno: `retencion_no_soportada`. Sin
`origenes`, sin retención.

## Vencimientos (P12, P13)

R28. El sistema debe exigir `vencimientos` (1..12) con `fecha` (`AAAAMMDD`) e `importe` (> 0, 2 decimales), y escribir un `pag
cla 0` por cada uno, en su orden, con `cod` `<cod>_NN`.
R29. SI una `fecha` no es una fecha real, es anterior a `fecha_factura` o posterior a `fecha_factura` + 730 días, o dos se
repiten, ENTONCES `vencimiento_no_valido` con su posición; SI Σ `importe` difiere de `totpag` en más de 0,01, ENTONCES
`vencimientos_no_cuadran` con las dos cifras.
R30. DONDE haya retención de `reccla` 5, el sistema debe exigir `vencimiento_retencion` (fecha, mismas reglas de R29) y escribir el
`pag cla 2` con `tot` = `cuo` y `retide` = `recide`; SI falta, o viene sin esa retención, ENTONCES `vencimiento_retencion_no_valido`.
Con `reccla` 3, ningún `pag` de retención.
R31. El sistema no debe calcular ni estimar vencimientos ni comparar con `pagfor`, `pagdia` o `pagmes`.

## Lo que escribe y lo que no

R32. CUANDO se confirme, el sistema debe escribir en **una** transacción: `con` (`tip 15`, `cod` de la serie, `est` REC), `dcf`
(`cla` 1001, `synckey` = `referencia_externa`), `dcfpro` ×N, `dcfrec` ×0-1, `con` + `pag` ×M, `consii` ×1, `dcaprodes` por línea
de origen, la fila de `dbo.log` (`ope 1`, `usu`) y los `UPDATE` de R36-R38.
R33. El sistema debe reservar `cod` e `ide` dentro de la transacción bajo `sp_getapplock` en orden fijo; `cod` = `FR<aa>/` + 5
cifras, `aa` del año de `con.fec` (= la operación), `MAX` numérico + 1 en la empresa de la obra; un choque de clave repite la
transacción hasta `DOMAIN_WRITE_MAX_RETRIES` y, agotados, `colision_de_clave` con el ERP intacto.
R34. El sistema debe escribir `con`, `dcf`, `dcfpro`, `pag`, `dcfrec`, `consii` y `dcaprodes` por **lista blanca**, sin clonar
filas; `consii` con `tipcom` A0, `tipdoc` F1, `claope` 01, `emiter`/`facsimcua`/`facsinide`/`difplaenv` N, `desope` = `con.res`
y `regivaide` 0.
R35. El sistema no debe escribir `asi`, `apu`, `regiva`, `regirp`, `mov`, `dcfproana`, `dcfpropar`, `dcfprodes`, `dcfproimp`,
`confir`, ni `pag.remide`/`fecrea`, ni pasar la factura de REC, ni ejecutar `DELETE`.

## Marcas en los orígenes

R36. CUANDO se escriba una línea de origen, el sistema debe sumar su `can` a `dcapro.canfac` con un `UPDATE` condicionado a
`canfac` = 0; si no afecta a una fila, revertir todo y responder `origen_ya_facturado`.
R37. El sistema debe pasar cada `dca` a `estfac` 1, `fecfac`/`horfac` = la operación y `antestfac` 3, y su `con.est` de CON a FAC
(contra `conest`); no debe escribir `dca.idefac`.
R38. DONDE la línea de origen apunte a un `ctrpro`, el sistema debe sumar su `can` a `ctrpro.canfac` y refrescar `ctr.estfac` con
`estados_contrato` (F-009).

## Idempotencia, respuesta y traza

R39. SI existe `dcf.synckey` = `referencia_externa` con el mismo proveedor y número, ENTONCES `idempotente` con esa factura y sin
escribir; con otros datos, `referencia_en_conflicto`. SI hay otra `dcf` de ese `entcif` y `entref` fuera de RECH, ENTONCES
`factura_ya_registrada` con su `cod`. Las dos, otra vez bajo el applock.
R40. El sistema debe responder `estado` (`previsto`, `creado`, `idempotente`), `cod`, `con_ide`, `modo`, `totales`, `retencion`,
`vencimientos`, `origenes`, `lineas` (con su clase: de origen o sin origen), `filas`, `avisos` y `pendiente_en_sigrid`.
R41. CUANDO se confirme, el sistema debe releer antes del COMMIT cada fila escrita y cada marca, y revertir si no cuadran.
R42. El sistema debe registrar una línea por petición (obra, prefijo de referencia, `usu`, `modo`, `commit`, `estado`, `cod`, nº de
líneas de origen y sin origen, nº de vencimientos, códigos, duración) y **nunca** textos, nombres, CIF, número de factura ni
importes.

## Compatibilidad y documentación

R43. El sistema debe dejar sin cambios el contrato de las rutas existentes y el código de F-007, F-009 y F-016 (se importa, no se
edita); debe arrancar con los ajustes nuevos ausentes y `SIGRID_FACTURA_WRITE_ENABLED` falsa.
R44. `azure-apps/sigrid_api.md`, `docs/ARCHITECTURE.md` y el mapa de `CLAUDE.md` deben documentar la ruta, los ajustes, los applocks
y lo que **no** hace, en el mismo trabajo.

Criterios manuales: T19-T21 de `tasks.md` (permisos, previas, una grabación autorizada; V1-V6 de `explore_F-008.md`).
