<!-- specs/F-007-registrar-proforma/requirements.md -->
# F-007 · Requisitos (v1, pendiente de la PARADA 1)

**`POST /api/sigrid/proforma`: alta idempotente de UNA proforma de subcontratista** con el mismo contrato JSON que el
modo extendido de `sigrid/albaran` (F-009) y la retención del contrato. Una proforma es un albarán de compra
(`con.tip 14`, `dca`, `dcapro`) de la serie `PROF<aa>/` (`sercon` 230) con `dca.cla 141`, casi siempre desde un
contrato, con IVA de inversión del sujeto pasivo y retención de garantía. Medición **Mn**:
[`progress/explore_F-007.md`](../../progress/explore_F-007.md). Decisiones abiertas **Dn**: design §Decisiones.
**Precondición: D1** (quién la llama y para qué). Mientras F-009 diga algo que aquí no se repite, manda F-009.

## Contrato y configuración
- **R1.** CUANDO llegue `POST /api/sigrid/proforma`, el sistema debe validar el cuerpo con `ProformaRequest`: los
campos, dominios y validaciones de `AlbaranCompraRequest` (F-009 R5-R6, `extra="forbid"`, CIF normalizado) con
`fecha_proforma` en lugar de `fecha_albaran` (mandar `fecha_albaran` da 400); si no valida, 400 `Solicitud invalida.`
sin `codigo`.
- **R2.** El sistema debe leer cinco App Settings nuevas con defecto cerrado (despliegue entre paréntesis, D7):
`SIGRID_PROFORMA_WRITE_ENABLED=false`, `SIGRID_PROFORMA_PREFIJOS_REFERENCIA=[]` (`["PRF-"]`),
`SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO=[]` (`["SB9999", "SM9999"]`), `SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO={}`
(`{"SB9999": "SB99", "SM9999": "SM99"}`, M8) y `SIGRID_PROFORMA_MAX_LINEAS=100`, con los validadores de F-009 (listas y
objeto en JSON; otra cosa **no arranca**). La obra se resuelve en las empresas de `SIGRID_ALBARAN_EMPRESAS_OBRA`.
Ninguna App Setting existente cambia de valor.
- **R3.** El sistema debe responder con la forma de la respuesta del modo extendido (F-009 R7: `estado` `previsto` |
`creado` | `idempotente`, avisos, líneas con `indice` desde 0, sin columnas bancarias) más `filas.dcarec[]`; `cabecera`
lleva `tot` y `totpag` con la retención descontada (R13).
- **R4.** SI falla una validación, ENTONCES el sistema debe responder como F-009 R9 (400 `details:{type, codigo[,
lineas]}`, todos los fallos de línea juntos en `lineas_no_validas`; lo inesperado, 500), con los códigos de F-009 más
`escritura_proformas_deshabilitada`, `proveedor_sin_proforma_previa` y `retencion_no_soportada`.
- **R5.** CUANDO `sigrid/proforma` reciba `commit:true` con `SIGRID_PROFORMA_WRITE_ENABLED=false`, el sistema debe
responder 400 `escritura_proformas_deshabilitada` **antes** de ejecutar el caso de uso; el dry-run no cambia.

## Resolución
- **R6.** El sistema debe resolver obra, contrato, `usu`, líneas vinculadas y sin vincular, partidas, productos,
naturaleza, IVA, almacén, centro y analítica **exactamente como F-009 R11-R17**, con la lista blanca y el mapeo de
naturaleza de R2 en lugar de los de albaranes, salvo la plantilla de cabecera (R7).
- **R7.** El sistema debe tomar como plantilla de cabecera la **última proforma** (`tip 14`, `cla 141`, `cod LIKE
'PROF%'`) del mismo proveedor en la empresa de la obra; SI no hay ninguna, ENTONCES 400 `proveedor_sin_proforma_previa`,
sin recurrir a un albarán (D5; M14).

## Filas
- **R8.** El sistema debe construir el `con` como F-009 R22 con el prefijo **`PROF<aa>/`** del año de `fecha_proforma`
(5 cifras, M1), `est` 1 `PDT` y la fila de alta de `log` con `est` 1 y `ori` 0 (M2).
- **R9.** El sistema debe construir la `dca` como F-009 R21 sobre la plantilla de R7 y además: `cla` 141 (M1);
`ivadif` = `ctr.ivadif`, o 0 sin contrato (D4, M4); `docoritip` 1 con contrato y 0 sin él, y `docoriide` 0 (D2, D4);
y a 0 lo que es de la facturación o de la cadena: `idefac`, `fecfac`, `horfac`, `antestfac`, `antestser`,
`antestped`, `estped`, `pasdeside`, `pasori`, `docrelide` y `facoriide` (M4, M15).
- **R10.** El sistema debe construir cada `dcapro` como F-009 R12-R21 salvo, en los dos tipos de línea, `canorilin`
0, `canoriant` 0 y **`canoriori` = cantidad** (primera de su cadena, M11), e `imporiori` = `ctrpro.tot` en las
vinculadas y 0 en las sin vincular.
- **R11.** CUANDO el contrato tenga filas `ctrrec`, el sistema debe escribir una `dcarec` por cada una, en orden de
`pos`, con `recide`, `pos`, `valdef`, `valpor`, `valcan`, `valmod`, `valfij`, `reccla`, `cueide`, `ivaide`, `tex`,
`resalt`, `refide`, `frasupide` e `item` del `ctrrec`; `docide` = la proforma; `bas` = `dca.totbas`; `cuo` =
`redondear_euros(bas·valpor)`; `ivacuo` y `reqcuo` 0 (M10, D3).
- **R12.** SI algún `ctrrec` del contrato tiene `reccla` distinto de 5 (retención sobre la base imponible), ENTONCES
400 `retencion_no_soportada` sin escribir nada, aun en dry-run (D3).
- **R13.** El sistema debe calcular `totbas`, `totiva` y `totdoc` como F-009, y `tot` = `totpag` = `totdoc` − Σ`cuo`
de R11 (M10); sin retención, `tot` = `totpag` = `totdoc`.
- **R14.** El sistema debe escribir `ctrprodes`, `mov` (si y solo si `pro.tipmov` = 1), `ctrpro.canser` y
`ctr.estser`/`estfac` como F-009 R18-R20 (M6).

## Dry-run, commit e idempotencia
- **R15.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas con credenciales de lectura y devolver
`previsto` con `cod`/`ide` provisionales y las filas completas de `con`, `dca`, `dcapro`, `ctrprodes`, `mov`, `dcarec`
y `log`.
- **R16.** CUANDO `commit` sea `true`, el sistema debe exigir antes de leer nada `SIGRID_DOMAIN_WRITE_ENABLED`,
`SIGRID_PROFORMA_WRITE_ENABLED` y credenciales de escritura (`escritura_proformas_deshabilitada`) y `database` en
`ALLOWED_WRITE_DATABASES` (`base_de_datos_no_permitida`). Aun en dry-run: `demasiadas_lineas` si hay más de
`SIGRID_PROFORMA_MAX_LINEAS` y `referencia_no_permitida` si la referencia no lleva un prefijo de R2.
- **R17.** El sistema debe escribir la proforma en **una** transacción: `INSERT` de `con`, `dca`, `dcapro`×N,
`ctrprodes`×M, `mov`×K, `dcarec`×R y la fila de alta de `log`; con vinculadas, los `UPDATE` de F-009 R25. Nada más (ni
`dcapropar`, `dcaproana`, `dcaprodes`, `asi` ni `pro`).
- **R18.** Dentro de la transacción, bajo `sp_getapplock` en el orden `SIGRID_REFEXT_14`, `SIGRID_SERIE_14`,
`SIGRID_IDE_con`, `_dcapro`, `_ctrprodes`, `_mov`, `_dcarec`, `_log` y con `WITH (UPDLOCK, HOLDLOCK)`, el sistema debe
re-comprobar la idempotencia, reservar el `cod` (`MAX` numérico de `PROF<aa>/` en la empresa + 1), los `ide` (`MAX+1`)
y los balances de stock, como F-009 R26.
- **R19.** SI un `INSERT` choca con una clave única, ENTONCES el sistema debe repetir la transacción entera hasta
`DOMAIN_WRITE_MAX_RETRIES` y, agotados, responder 400 `colision_de_clave` con el ERP intacto (F-009 R27).
- **R20.** SI antes del `COMMIT` las relecturas no dan 1 `con`, 1 `dca`, N `dcapro`, M `ctrprodes`, K `mov`, R
`dcarec` y 1 `log`, ENTONCES `ROLLBACK` y `filas_afectadas_inesperadas`.
- **R21.** CUANDO ya exista un `tip 14` con `dca.synckey` = `referencia_externa`, el sistema debe devolverlo
`idempotente` sin escribir (como F-009 R30) **solo si** es una proforma (`cla 141`, `cod LIKE 'PROF%'`) del mismo
proveedor y obra; SI es un albarán, de otro proveedor u obra, o hay más de uno, ENTONCES `referencia_en_conflicto`.

## Compatibilidad con F-009 (D6)
- **R22.** `sigrid/albaran` (los dos modos) y `sigrid/albaran-directo` deben producir exactamente lo de hoy: un
**dorado del modo extendido** escrito sobre `dev` antes de tocar su código (dry-run y commit; vinculadas, sin vincular,
devolución e idempotente) y los tests de F-009 pasan **sin modificarlos**.

## Seguridad, trazas, verificación y documentación
- **R23.** Todo el SQL nuevo debe ser constante con valores `?` y validado con `DatabaseReferenceGuard`; sin `DELETE`,
`MERGE` ni DDL, y sin más `UPDATE` que los de R17 (control negativo en tests).
- **R24.** CUANDO termine una petición, el sistema debe trazar (endpoint `sigrid/proforma`, obra, contrato, referencia,
`commit`, `estado`, `cod`, nº de líneas, nº de retenciones, códigos y duración), **nunca** textos, precios ni datos
bancarios.
- **R25.** El sistema debe cubrir R1-R24 con tests sin red ni BBDD (`test_f007_rN_*`), comparando el SQL carácter a
carácter, con fase RED en R5, R7-R13, R18, R20, R21 y R22; campaña de mutación sin supervivientes o con equivalentes
aceptados por el humano.
- **R26.** MANUAL (humano): V1-V3 de la medición en la UI; dry-run sobre un contrato de prueba con retención;
`commit:true` autorizado de **una** proforma revisada en la ficha de Sigrid (cabecera, clase, retención, totales,
servido del contrato, impresión) y repetición `idempotente`; anulación desde la UI (nunca `DELETE`).
- **R27.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (§4, §4.1, §7.2, §7.5, §7.6, §8
ruta nueva, §9.2 y §9.7 con la proforma y el `tip 20`, §10 consumidor de D1, §13), `docs/ARCHITECTURE.md`, la lista
de rutas de `CLAUDE.md` y `local.settings.sample.json`.

## Fuera de alcance
El **encadenamiento a origen** (anterior, líneas arrastradas a cantidad 0, `canorilin`, `canoriori` acumulado; D2 →
F-007b), la medición desglosada (`med`/`canmed`), retenciones que no sean de clase 5, la facturación (`dcaprodes`,
`canfac`, estados de factura: F-008), el asiento contable, modificar o anular, el PDF, varias proformas por petición,
cambiar el contrato HTTP de `sigrid/albaran`, y O1/O2 de F-009 (design §Riesgos: features propias).
