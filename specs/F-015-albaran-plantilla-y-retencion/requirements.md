<!-- specs/F-015-albaran-plantilla-y-retencion/requirements.md -->
# F-015 · Requisitos (v1)

**El modo extendido de `POST /api/sigrid/albaran` (F-009) toma la cabecera solo de un albarán de la serie `AC`, no
arrastra la facturación de la plantilla y escribe la retención del contrato (`ctrrec` → `dcarec`) con su total neto.**
Medidas **Mn**: [`progress/explore_F-015.md`](../../progress/explore_F-015.md). F-009 sigue mandando en todo lo que esta
spec no cambia; sus **R** se citan como «F-009 Rn». Decisiones abiertas **Dn**: design §Decisiones.

## Plantilla de cabecera (O1)

- **R1.** El sistema debe tomar como plantilla de cabecera (L5) el último `con.tip 14` del proveedor (por `entide` con
contrato, por `entcif` sin él) en la empresa de la obra **con `con.cod LIKE 'AC__/%'` y `dca.cla = 0`** (serie 87): nunca
una proforma (`PROF`, `cla 141`), una nota de cargo (`NTC`) ni un `AC` de otra clase (M1, M2; D1).
- **R2.** SI el proveedor no tiene ningún albarán así en la empresa de la obra, ENTONCES el sistema debe responder 400
`proveedor_sin_albaran_previo` (mismo código que F-009, mensaje que nombra la serie `AC`), sin *fallback* a otra serie,
proveedor ni empresa (M4: 6 proveedores, solo con proformas).
- **R3.** El sistema debe escribir 0 en las columnas de `dca` de facturación y de cadena que traiga la plantilla:
`fecfac`, `horfac`, `idefac`, `antestfac`, `docoritip`, `docoriide`, `pasdeside`, `pasori`, `docrelide` y `fecpag`,
como ya hace con `estser` y `estfac` (M5; D2). Las que la plantilla no trae no se añaden.
- **R4.** El sistema debe escribir 0 en `totbasdiv`, `totivadiv`, `totdocdiv`, `totdiv` y `totpagdiv` si la plantilla los
trae, en vez de los totales en euros (M6: el escritorio, 0 en 29.486 de 29.487; D3).
- **R5.** El modo clásico y `sigrid/albaran-directo` no deben cambiar: ni modelo, ni caso de uso, ni sentencias, ni el
dorado `tests/fixtures/f009_caracterizacion.json`, que sigue pasando sin tocarlo (D4).

## Retención del contrato (O2)

- **R6.** CUANDO el albarán tenga contrato (con o sin vinculadas, también en devoluciones y con líneas sin vincular), el
sistema debe leer sus `ctrrec` (L16) y, si es soportada (R8), escribir **una** `dcarec`; sin contrato o con un contrato
sin `ctrrec`, ninguna (M9, M10; D5, D6).
- **R7.** El sistema debe construir la `dcarec` copiando del `ctrrec` `recide`, `pos`, `valdef`, `valpor`, `valcan`,
`valmod`, `valfij`, `reccla`, `cueide`, `ivaide`, `tex`, `resalt` e `item` (M11), con `docide` = `con.ide`, `bas` y
`cuo` de R9 e `ivacuo`, `reqcuo`, `refide` y `frasupide` a 0 (M13). Columnas, las del esquema vivo (M14).
- **R8.** SI el contrato tiene más de un `ctrrec`, o el suyo tiene `recide` sin fila en `dbo.rec`, clase de `rec` fuera de
{3, 4, 5}, `valfij` ≠ 0 o `ivaide` ≠ 0, ENTONCES el sistema debe responder 400 `retencion_no_soportada` (cabecera),
también en dry-run, después de la idempotencia (F-009 R30) y antes de validar las líneas (M11: 15 de 651 contratos; D7).
- **R9.** El sistema debe calcular `bas` = `totbas` del albarán (clases 3 y 5) o `totdoc` (clase 4, «sobre total») y `cuo`
= `redondear_euros(bas · valpor)` (`Decimal`, `ROUND_HALF_UP`: lejos del cero también en negativo), con `totbas` y
`totdoc` los de F-009 (M12: 3.223 de 3.223; devoluciones con `bas` y `cuo` negativos, M10).
- **R10.** CUANDO haya `dcarec`, el sistema debe escribir `dca.tot` = `totdoc` − `cuo` y `dca.totpag` = `tot`; sin ella,
`tot` = `totpag` = `totdoc`, como hoy. `totbas`, `totiva`, `totdoc`, `impbru`, `impnet` e `imprec` (0) no cambian (M13).
- **R11.** CUANDO haya `dcarec`, el sistema debe añadir el aviso de cabecera `retencion_del_contrato` (código del
recargo, porcentaje, `bas` y `cuo` en el mensaje); informativo (D8).

## Respuesta (contrato con albaranes)

- **R12.** El sistema debe añadir a `totales` `tot` (= `dca.tot`), `retenciones` (= `cuo`, 0 sin `dcarec`) y
`n_retenciones` (0 o 1), en previa y en `creado`, y `filas.dcarec` (lista de 0 o 1 filas completas).
- **R13.** En `idempotente`, el sistema debe leer `dca.tot` (L11) y devolver `totales.tot` y `totales.retenciones` =
`totdoc` − `tot` del albarán existente, sin leer su `dcarec`.
- **R14.** El sistema debe trazar (F-009 R32) además `n_retenciones` y el código de error; nunca `bas`, `cuo` ni `valpor`.

## Escritura

- **R15.** MIENTRAS `commit` sea `false`, el sistema debe devolver la `dcarec` numerada con `peek_next_ide("dcarec")`,
sin reservar nada (como F-009 R23).
- **R16.** CUANDO `commit` sea `true` y haya `dcarec`, el sistema debe, dentro de la transacción de F-009 R25 y tras los
`mov`, reservar su `ide` (`MAX(ide)+1 WITH (UPDLOCK, HOLDLOCK)`) bajo el applock nuevo `SIGRID_IDE_dcarec`, tomado
entre `SIGRID_IDE_mov` y `SIGRID_IDE_log`, e insertarla; sin `dcarec`, ni reserva ni `INSERT`.
- **R17.** El reintento por clave duplicada (F-009 R27) debe recalcular también el `ide` de la `dcarec`.
- **R18.** SI antes del `COMMIT` la relectura (E12) no da tantas `dcarec` del albarán como se insertaron (0 o 1),
ENTONCES `ROLLBACK` y 400 `filas_afectadas_inesperadas`.
- **R19.** Todo el SQL nuevo o cambiado (L5, L11, L16, E6b, E8 de `dcarec`, E12) debe ser constante con `?` y validado con
`DatabaseReferenceGuard`; ningún `UPDATE`, `DELETE`, `MERGE` ni DDL nuevo (control negativo de F-009 R31).

## Equivalencia, pruebas y documentación

- **R20.** El test de equivalencia con el clásico (F-009 R33) debe seguir pasando con estas diferencias **declaradas**, y
ninguna más: R3 y R4 en `dca`; con `ctrrec`, `dcarec`, `tot`/`totpag` y el aviso R11. Sin `ctrrec` y con una plantilla
sin facturación ni divisa, las filas del modo extendido deben salir **idénticas** a las de `dev`.
- **R21.** El sistema debe cubrir R1-R20 con tests sin red ni BBDD (`test_f015_rN_*`), SQL comparado carácter a carácter,
con fase RED en R1, R3, R4, R6, R8, R9, R10, R16 y R18. Los tests de F-009 que fijan L5, L11, los applocks, `totales` o la
`dca` se cambian solo en lo que R1-R19 cambian, cada cambio con su R en el commit.
- **R22.** El sistema debe actualizar **antes de implementar** `contrato_albaranes.md` (design §Contrato) y avisar a
albaranes, y en el mismo trabajo `azure-apps/sigrid_api.md` (§7.5, §7.6, §8.6, §8.7, §13), `docs/ARCHITECTURE.md`
(applocks, `dcarec`) y el docstring de `sigrid_albaran`.
- **R23.** MANUAL (humano), tras desplegar: dry-run de un albarán de un contrato con `RET5` (201 contratos con AC26 desde
septiembre) y de uno sin `ctrrec`, revisando `filas.dcarec`, `totales` y la `dca`; una grabación solo con autorización
expresa para esa escritura, revisada en la UI (V1), repetida (`idempotente`) y anulada desde la UI (nunca `DELETE`).

## Fuera de alcance

Retención sin contrato (M9: manual; `entrec` no es la fuente); `ctrrec` no soportados (R8: alta a mano); más de una
retención; recalcular la `dcarec` si el escritorio cambia el albarán; IRPF y cartera (los genera la factura, F-008);
`ivadif` (sigue de la plantilla, M7); cambiar el clásico o `albaran-directo` (D4); plantilla de otro proveedor o empresa.
