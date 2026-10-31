<!-- specs/F-008-registrar-factura/requirements.md -->
# F-008 · Registrar facturas de compra FR y FRGG: alta sin contabilidad (v3.1)

Rigor **critico**. Cifras de [`progress/explore_F-008.md`](../../progress/explore_F-008.md) (M52-M74). v3.1: decisiones del
humano P11-P21 del 2026-10-30 (FRGG con y sin orígenes, a origen comparado, NDED); todas en `design.md` §9. **Alta sin
contabilidad** (P1): se escribe lo que arrastra el alta (`con`, `dcf`, `dcfpro`, `dcfrec`, `pag`, `consii`, `log`, marcas de los
orígenes); asiento, `regiva` y `regirp` los hace «Contabilizar» en el escritorio. Cobertura: **~95 %** de FR26 y **87,2 %** de
FRGG26 (M74).

**La API registra y valida; no deduce.** Serie, modo, a origen, vencimientos, cuentas y analíticas los decide el llamante.

## Entrada, llaves y llamantes

R1. CUANDO llegue `POST /api/sigrid/factura`, el sistema debe validar el cuerpo con `extra="forbid"` y números estrictos; un
cuerpo no válido da 400 «Solicitud invalida.» sin eco de valores ni `codigo`.
R2. SI no vienen `origenes` ni `lineas`; `modo` es `"origen"` sin `origenes`; se repite un código de `origenes`; o viene
`a_origen` en modo mes, ENTONCES el sistema debe responder 400 sin `codigo` (R1).
R3. El sistema debe tratar toda petición sin `commit: true` como previa: mismas validaciones y respuesta, sin sentencias de
escritura.
R4. SI llega `commit: true` y `SIGRID_FACTURA_WRITE_ENABLED` no es verdadera, ENTONCES 400 `escritura_facturas_deshabilitada`,
tras validar el cuerpo y antes del caso de uso. Ninguna otra llave la abre.
R5. SI llega `commit: true`, ENTONCES el sistema debe exigir además `SIGRID_DOMAIN_WRITE_ENABLED`, credenciales de escritura y la
base en `ALLOWED_WRITE_DATABASES` (lista vacía no abre: `base_de_datos_no_permitida`).
R6. SI `referencia_externa` no empieza por un prefijo de `SIGRID_FACTURA_PREFIJOS_REFERENCIA`, ENTONCES `referencia_no_permitida`;
la lista vacía no admite ninguno. Sin lógica distinta por prefijo ni por aplicación (P15).
R7. SI `usu` no es un `dbo.usu.cod` existente, ENTONCES `usuario_no_valido`.
R8. SI las líneas a escribir superan `SIGRID_FACTURA_MAX_LINEAS` (defecto 500), ENTONCES `demasiadas_lineas`, aun en previa.

## Serie, proveedor y obra

R9. El sistema debe aceptar `serie` `"FR"` (defecto) o `"FRGG"`, sin deducirla de la obra (M64): FR nace en REC (1) con `cod`
`FR<aa>/` + 5 cifras; FRGG, en RECGG (20) con `FRGG<aa>/` + 4 cifras; los estados, resueltos contra `conest`.
R10. CUANDO vengan `origenes`, el sistema debe tomar el proveedor de ellos (R13); CUANDO no, debe resolver `cif_proveedor` contra
`prv` de la empresa de la obra: ninguno da `proveedor_no_encontrado` y más de uno, `proveedor_ambiguo`.
R11. El sistema debe resolver `cod_obra` en la empresa de `SIGRID_ALBARAN_EMPRESAS_OBRA` (`obra_no_encontrada`); es obligatorio
sin `origenes`, y con ellos, SI no es la obra de los orígenes, ENTONCES `varias_obras`.
R12. El sistema debe poner `dcf.cueide` = `prv.cueide` y, en las líneas de origen de las dos series, `dcfpro.cueide` =
`prv.cuepdtide` (M69); SI la que
se necesita vale 0, ENTONCES `proveedor_sin_cuenta`.

## Orígenes: albaranes y proformas (las dos series, P18)

R13. El sistema debe resolver cada código de `origenes` a un `con.tip 14` de la empresa de la obra (`origen_no_encontrado`, con el
código); SI no son todos del `entide` del `cif_proveedor`, ENTONCES `origen_de_otro_proveedor`; SI son de más de una obra o
contrato (`dca.ctride`), ENTONCES `varias_obras` o `varios_contratos`.
R14. SI un origen no está en CON (contra `conest`) o no tiene asiento `tip 20` con su `cod` en su empresa, ENTONCES
`origen_sin_contabilizar` (P4).
R15. SI una línea de origen con `can` ≠ 0 tiene `canfac` ≠ 0 o `dcaprodes` a un `tip 15`, ENTONCES `origen_ya_facturado`.
R16. El sistema debe facturar **todas** las líneas con `can` ≠ 0 de cada origen; las de `can` 0 no pasan y quedan con `canfac` 0.
R16b. SI un origen no tiene ninguna línea con `can` ≠ 0, ENTONCES `origen_sin_lineas`, también bajo bloqueo (humano, 2026-10-31).
R17. El sistema debe copiar cada línea de origen de su `dcapro` (`proide`, `can`, `pre`, `tar`, `dto`, `tot`, `ivaide`, `ivacuo`,
`cenide`, `caaide`, `paride`, `natide`, `almide`, `obride`, `res`, `tex`, `cod2`, `unimed`, `prepma`, `dncide`, `dncproide`) sin
recalcularla, con `docoritip` 14, `docoricod`, `docoriide`, `linoriide` y `canorilin` 0.

## Modo: de mes o a origen (P14)

R18. El sistema debe aceptar `modo` `"mes"` (defecto) u `"origen"`; SI algún origen tiene `dca.docoritip` distinto (0 mes, 1
origen), ENTONCES `modo_no_coincide_con_origen`; SI los orígenes mezclan modos, ENTONCES `origenes_de_modos_distintos`.
R19. En modo mes, el sistema debe escribir `canoriori` = `can`, `imporiori` = `tot`, `canoriant` e `imporiant` 0 (M56).
R20. En modo origen, el sistema debe calcular por la regla de M63: `canoriori` = `dcapro.canoriori`; `canoriant`/`imporiant` = el
`canoriori`/`imporiori` de la `dcapro` de su `canorilin` (0 sin ella); `imporiori` = `dcapro.imporiori` si `linoriide` ≠ 0, y
`imporiant` + `tot` si no. `dcf.docoritip` 0 en los dos modos.
R21. En modo origen, el sistema debe exigir `a_origen` con **una** entrada `{linea, canoriori, imporiori}` por línea facturada
(`linea` = `dcapro.ide`); faltas, sobras o repetidas dan `a_origen_incompleto` con las líneas.
R22. SI en alguna entrada `canoriori` difiere de R20 en más de 0,001 o `imporiori` en más de 0,01, ENTONCES `a_origen_no_cuadra`
con la línea y los dos juegos, sin escribir. Cuadrando, se escriben los valores de R20.

## Líneas sin origen (P11, P16, P17, P19)

R23. El sistema debe admitir en `lineas` (0..N): `descripcion` (1-128), `cantidad`, `precio` e `iva` (código de `dbo.iva`); en FR
además `producto`, `partida?`, `paride?`, `unidad?`; en FRGG además `cuenta` y `analitica` (códigos). Un campo de la otra serie
da 400 (R1). Cantidad o precio negativos se admiten (ajustes, M61).
R24. SI `iva` no está en `SIGRID_FACTURA_IVAS` o no existe, ENTONCES fallo de línea `iva_no_valido`; un IVA no deducible
(`I21NDED`, `I10NDED`) solo cambia `ivaide` (P21, M72). Todos los fallos de línea, juntos en `lineas_no_validas` con su posición.
R25. En FR, SI `producto` no está en `SIGRID_FACTURA_PRODUCTOS_SIN_ORIGEN` o no existe en la empresa (`tip 3`, sin baja),
ENTONCES `producto_no_permitido` o `producto_no_encontrado`; el sistema debe resolver la naturaleza por
`SIGRID_FACTURA_NATURALEZA_POR_PRODUCTO`, y de ella `natide`, `cueide` (la `cua` de `cuacomcod`) y `caaide`, más partida, almacén
y centro, con las reglas de F-009 R13b, R14, R14b y R15 y sus mismos fallos de línea.
R26. En la línea propia FRGG (P19), SI `cuenta` no es una `cua` hoja (`niv` 5) de la empresa o no empieza por un prefijo de
`SIGRID_FACTURA_CUENTAS_GASTO_PREFIJOS` (lista vacía: ninguno), ENTONCES `cuenta_no_valida`; SI `analitica` no es una `caa` hoja
de la empresa cuyo prefijo `<obra>.` sea una obra de esa empresa, ENTONCES `analitica_no_valida`. Las dos son obligatorias.
R27. En la línea propia FRGG, el sistema debe escribir `cueide` = la cuenta, `caaide` = la analítica, `obride` = la obra de su
prefijo, `cenide` = `obr.cenide` de esa obra, `almide` = `dcf.almide`, y `proide`, `paride`, `natide` 0 (M66); sin contabilidad (M65).
R28. El sistema debe escribir toda línea sin origen con `pre` = `tar` = `precio`, `dto` vacío, `tot` = round(`cantidad`·`precio`,
2), `ivacuo` = round(`tot`·`iva.iva`, 2) (`Decimal`, `ROUND_HALF_UP`), `docori*`, `linoriide`, `canori*` e `impori*` a 0, sin
`dcaprodes` ni marcas, por un solo camino en las dos series (la serie solo decide R25 o R26-R27).

## Importes y retención

R29. El sistema debe calcular `totbas` = Σ `tot`, `impnet` = `totbas`, `impbru` = Σ bruto, `totiva` = Σ `ivacuo`, `totdoc` =
`totbas` + `totiva`, `tot` = `totdoc` − retención y `totpag` = `tot`.
R30. SI `total_base` difiere de `totbas` en más de 0,01, `total_iva` de `totiva` en más de 0,05 o `total_factura` de `tot` en más
de 0,05, ENTONCES `totales_no_cuadran` con los dos juegos, sin ajustar nada; SI `total_base` no es positivo, `abono_no_soportado`.
R31. DONDE los orígenes lleven `dcarec`, el sistema debe escribir **una** `dcfrec` con su `recide`, `valpor`, `reccla` y `cueide`,
`bas` = `totbas` y `cuo` = round(`bas`·`valpor`, 2); recargos distintos o más de uno: `retencion_no_soportada`. Vale en las dos
series (M71); sin `origenes`, sin retención (P20).

## Vencimientos (P12, P13)

R32. El sistema debe exigir `vencimientos` (1..12) con `fecha` (`AAAAMMDD`) e `importe` (> 0, 2 decimales), y escribir un `pag
cla 0` por cada uno, en su orden, con `cod` `<cod>_NN`.
R33. SI una `fecha` no es real, es anterior a `fecha_factura` o posterior a `fecha_factura` + 730 días, o dos se repiten,
ENTONCES `vencimiento_no_valido` con su posición; SI Σ `importe` difiere de `totpag` en más de 0,01, ENTONCES
`vencimientos_no_cuadran` con las dos cifras.
R34. DONDE haya retención `reccla` 5, el sistema debe exigir `vencimiento_retencion` (reglas de R33) y escribir el `pag cla 2` con
`tot` = `cuo` y `retide` = `recide`; SI falta, o viene sin esa retención, ENTONCES `vencimiento_retencion_no_valido`.
R35. El sistema no debe calcular ni estimar vencimientos ni comparar con `pagfor`, `pagdia` o `pagmes` (sin regla del 77 %).

## Lo que escribe y lo que no

R36. CUANDO se confirme, el sistema debe escribir en **una** transacción: `con` (`tip 15`, `cod` de la serie, estado de R9), `dcf`
(`cla` 1001, `synckey` = `referencia_externa`), `dcfpro` ×N, `dcfrec` ×0-1, `con` + `pag` ×M, `consii` ×1, `dcaprodes` por
línea de origen, la fila de `dbo.log` (`ope 1`, `usu`) y los `UPDATE` de R40-R42.
R37. El sistema debe reservar `cod` e `ide` dentro de la transacción bajo `sp_getapplock` en orden fijo; `cod` = prefijo de la serie
+ cifras de R9, `aa` del año de `con.fec`, `MAX` numérico + 1 en la empresa y serie; un choque de clave repite la transacción
hasta `DOMAIN_WRITE_MAX_RETRIES` y, agotados, `colision_de_clave` con el ERP intacto.
R38. El sistema debe escribir `con`, `dcf`, `dcfpro`, `pag`, `dcfrec`, `consii` y `dcaprodes` por **lista blanca**, sin clonar
filas; `consii` con `tipcom` A0, `tipdoc` F1, `claope` 01, `emiter`/`facsimcua`/`facsinide`/`difplaenv` N, `desope` = `con.res` y
`regivaide` 0, en las dos series.
R39. El sistema no debe escribir `asi`, `apu`, `regiva`, `regirp`, `mov`, `dcfproana`, `dcfpropar`, `dcfprodes`, `dcfproimp`,
`confir`, ni `pag.remide`/`fecrea`, ni sacar la factura de su estado inicial, ni ejecutar `DELETE`.

## Marcas en los orígenes

R40. CUANDO se escriba una línea de origen, el sistema debe sumar su `can` a `dcapro.canfac` con un `UPDATE` condicionado a
`canfac` = 0; si no afecta a una fila, revertir todo y responder `origen_ya_facturado`.
R41. El sistema debe pasar cada `dca` a `estfac` 1, `fecfac`/`horfac` = la operación y `antestfac` 3, y su `con.est` de CON a FAC
(contra `conest`); no debe escribir `dca.idefac`.
R42. DONDE la línea de origen apunte a un `ctrpro`, el sistema debe sumar su `can` a `ctrpro.canfac` y refrescar `ctr.estfac` con
`estados_contrato` (F-009).

## Idempotencia, respuesta y traza

R43. SI existe `dcf.synckey` = `referencia_externa` con el mismo proveedor y número, ENTONCES `idempotente` sin escribir; con otros
datos, `referencia_en_conflicto`. SI hay otra `dcf` de ese `entcif` y `entref` fuera de RECH, ENTONCES `factura_ya_registrada`
con su `cod`. Las dos, otra vez bajo el applock.
R44. El sistema debe responder `estado` (`previsto`, `creado`, `idempotente`), `cod`, `con_ide`, `serie`, `modo`, `totales`,
`retencion`, `vencimientos`, `origenes`, `lineas` (con su clase), `filas`, `avisos` y `pendiente_en_sigrid`.
R45. CUANDO se confirme, el sistema debe releer antes del COMMIT cada fila escrita y cada marca, y revertir si no cuadran.
R46. El sistema debe registrar una línea por petición (obra, prefijo, `usu`, `serie`, `modo`, `commit`, `estado`, `cod`, nº de
líneas por clase, nº de vencimientos, códigos, duración) y **nunca** textos, nombres, CIF, número de factura, cuentas ni importes.

## Compatibilidad y documentación

R47. El sistema debe dejar sin cambios las rutas existentes y el código de F-007, F-009 y F-016 (se importa, no se edita); debe
arrancar con los ajustes nuevos ausentes y `SIGRID_FACTURA_WRITE_ENABLED` falsa.
R48. `azure-apps/sigrid_api.md`, `docs/ARCHITECTURE.md` y el mapa de `CLAUDE.md` deben documentar la ruta, los ajustes, los applocks
y lo que **no** hace, en el mismo trabajo.

Criterios manuales: T22-T24 de `tasks.md` (permisos, previas, grabaciones autorizadas; V1-V7 de `explore_F-008.md`).
