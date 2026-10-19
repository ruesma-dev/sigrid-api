<!-- specs/F-007-registrar-proforma/requirements.md -->
# F-007 · Requisitos (v2, pendiente de la PARADA 1)

**`POST /api/sigrid/proforma`: alta idempotente de UNA proforma a origen de subcontratista**, primera de su cadena o
encadenada a la anterior, que el endpoint **resuelve él**. La llama la app de facturas (su F-063) con lo que lee de la
hoja de certificación: contrato, periodo, importe ANTERIOR total y, por línea, la cantidad del MES. Una proforma es un
albarán de compra (`con.tip 14`, `dca`, `dcapro`) de la serie `PROF<aa>/` con `dca.cla 141`. Medición **Mn**:
[`progress/explore_F-007.md`](../../progress/explore_F-007.md). Decisiones **Dn**: design §Decisiones.
**Precondición: F-015 cerrada** (plantilla solo `AC` y `dcarec` desde `ctrrec`): F-007 se apoya en ese núcleo. Lo
que F-009 o F-015 dicen y aquí no se repite, manda allí.

## Contrato y configuración
- **R1.** CUANDO llegue `POST /api/sigrid/proforma`, el sistema debe validar con `ProformaRequest` (`extra="forbid"`,
textos recortados, números estrictos): `database`, `cod_obra`, **`cod_contrato`** (obligatorio), `usu`,
`referencia_externa` (1-128), `periodo` (`AAAAMM`, mes 1-12), `importe_anterior` (número; 0 = primera de cadena),
`importe_mes` (número: TOTALES MES de la hoja), opcionales `fecha_proforma` (`AAAAMMDD`), `su_referencia` (≤128),
`cod_proforma_anterior` y `commit` (`false`), y `lineas` (lista; vacía solo con `commit` `false`). Sin
`cif_proveedor`: el proveedor sale del contrato. Si no valida, 400 `Solicitud invalida.` sin `codigo`.
- **R2.** Cada línea debe llevar `referencia_linea` (1-24, única en la petición, → `dcapro.refent`), **uno solo** de
`linea_anterior_ide`, `ctrpro_ide` o `producto` (este con `descripcion`), `cantidad` ≠ 0 (la del MES), y opcionales
`precio` (obligatorio con `producto`), `cantidad_anterior`, `partida`/`paride` (como F-009 R14-R14b) y `unidad`;
si no, 400 sin `codigo`.
- **R3.** El sistema debe leer cinco App Settings con defecto cerrado (despliegue entre paréntesis, D7):
`SIGRID_PROFORMA_WRITE_ENABLED=false`, `SIGRID_PROFORMA_PREFIJOS_REFERENCIA=[]` (`["PRF-"]`),
`SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO=[]` (`["SB9999", "SM9999"]`), `SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO={}`
(`{"SB9999": "SB99", "SM9999": "SM99"}`) y `SIGRID_PROFORMA_MAX_LINEAS=500`, con los validadores de F-009 (JSON;
otra cosa no arranca). La obra se resuelve en `SIGRID_ALBARAN_EMPRESAS_OBRA`. Ninguna App Setting existente cambia.
- **R4.** El sistema debe responder con la forma del modo extendido de F-009 (R7, más `filas.dcarec[]` de F-015),
con `estado` `previsto` | `creado` | `idempotente` | **`existente`** y un objeto **`cadena`**: `anterior` (`cod`,
`ide`) o `null`, y `lineas_anteriores[]` (`linea_anterior_ide`, `pos`, `ctrpro_ide`, `producto`, `partida`,
`descripcion`, `precio`, `cantidad_origen`, `importe_origen`) para que el llamante identifique sus líneas (D9).
- **R5.** SI falla una validación, ENTONCES el sistema debe responder como F-009 R9 (400 `details:{type, codigo[,
lineas]}`, todos los fallos de línea juntos; lo inesperado, 500) con los códigos de F-009 y F-015 más los de design
§Códigos.
- **R6.** CUANDO llegue `commit:true` con `SIGRID_PROFORMA_WRITE_ENABLED=false`, el sistema debe responder 400
`escritura_proformas_deshabilitada` **antes** del caso de uso; el dry-run no cambia.

## Cabecera
- **R7.** El sistema debe resolver obra y contrato como F-009 R11 (el contrato, obligatorio, de la obra) y tomar el
proveedor de `ctr.entide`; `usu`, estado inicial y almacén de la obra, como F-009.
- **R8.** El sistema debe fijar la fecha (D8): `fecha_proforma` si viene y cae en `periodo`; si no, el último día de
`periodo` si ya pasó (hora de Madrid) u hoy si `periodo` es el mes en curso. SI `periodo` es futuro o
`fecha_proforma` cae fuera, ENTONCES `periodo_no_valido`.
- **R9.** El sistema debe tomar como plantilla de cabecera (D5), por este orden: la **anterior** (R12), la última
`PROF` del proveedor en la empresa de la obra, o la plantilla `AC` de F-015; SI no hay ninguna, ENTONCES
`proveedor_sin_documento_previo`.

## Cadena
- **R10.** El sistema debe leer las proformas **a origen** del contrato (`tip 14` de cualquier serie, `dca.ctride` =
contrato, `docoritip 1`) con, por documento, Σ round(`canoriori`·`pre`, 2) de sus líneas y, por `ctrpro`, Σ`can` y
Σ`canoriori`; **puntas** = las que ninguna `dca` cita en `docoriide` (M19).
- **R11.** CUANDO una a origen del contrato tenga Σ = `importe_anterior` + `importe_mes` (±0,05 €) y, en cada línea
con `ctrpro_ide`, la misma `can` (±0,0001) y, si trae `cantidad_anterior`, `canoriori` = esa + `cantidad`, el sistema
debe devolverla `existente` (`cod`, `ide`, `committed` `false`) **sin escribir**; SI casan dos o más, ENTONCES
`proforma_existente_ambigua` (D10, M26).
- **R12.** CUANDO `importe_anterior` sea 0, el sistema debe dar de alta la proforma como **primera de su cadena** sin
buscar anterior; si no, debe elegir como anterior la **única punta** con Σ = `importe_anterior` (±0,05 €) y sin
contradicción con ninguna `cantidad_anterior` de la petición (D2, M25). SI no casa ninguna, ENTONCES
`anterior_no_encontrada`; SI casan varias, ENTONCES `cadena_ambigua`.
- **R13.** CUANDO venga `cod_proforma_anterior`, el sistema debe usar ese documento si es una punta a origen del
contrato y casa como en R12; SI no es una punta del contrato, ENTONCES `anterior_no_valida`; SI no casa,
`anterior_no_encontrada`.
- **R14.** SI una línea trae `cantidad_anterior` distinta (±0,0001) del Σ`canoriori` de su línea en la anterior (0 si
no está), ENTONCES fallo de línea `anterior_no_casa`.

## Líneas
- **R15.** El sistema debe **arrastrar todas las líneas de la anterior**, en su orden, y después las nuevas en el de la
petición (M23), numeradas como F-009. Cada línea de la petición se aplica a una arrastrada (por
`linea_anterior_ide`, o por `ctrpro_ide` si la anterior lo tiene) o crea una nueva.
- **R16.** SI `linea_anterior_ide` no es una línea de la anterior, ENTONCES `linea_anterior_no_valida`; SI un
`ctrpro_ide` está en dos o más líneas de la anterior, ENTONCES `linea_ambigua` (que use `linea_anterior_ide`); SI
dos líneas de la petición caen en la misma, ENTONCES `linea_repetida`. Todas son fallos de línea.
- **R17.** La arrastrada debe ser la línea de la anterior con: `can` = la del MES o 0, `tot` e IVA recalculados como
F-009 sobre su `pre` (o el `precio` de la petición, con el aviso de F-009 si difiere del contrato), `canorilin` = su
`ide`, `canoriant` e `imporiant` 0, `canoriori` = el suyo + `can`, `imporiori` el suyo, `refent` =
`referencia_linea` o vacío, y el seguimiento a 0 como F-009 (M23).
- **R18.** La nueva vinculada debe construirse como F-009 R12, R16-R17, con la partida del `ctrpro` si no trae
`partida` (M21), `canoriori` = `can`, `canorilin` y `canoriant` 0 e `imporiori` = `ctrpro.tot` (M11).
- **R19.** La nueva sin vincular debe construirse como F-009 R13-R15 con la lista y el mapeo de R3, `canoriori` =
`can` e `imporiori` 0. La lista blanca no se aplica a las arrastradas.
- **R20.** SI la proforma resultante pasa de `SIGRID_PROFORMA_MAX_LINEAS` líneas, ENTONCES `demasiadas_lineas`; SI hay
líneas y Σ round(`cantidad`·precio efectivo, 2) difiere de `importe_mes` en más de 0,05 €, ENTONCES
`importe_mes_no_cuadra`. Las dos, aun en dry-run.

## Filas
- **R21.** El sistema debe construir el `con` como F-009 R22 con el prefijo `PROF<aa>/` del año de la fecha de R8 (5
cifras, M1), `est` 1 y la fila de alta de `log` (M2).
- **R22.** El sistema debe construir la `dca` sobre la plantilla de R9 como F-009 R21 y además: `cla` 141, `docoritip`
1 (M17), `docoriide` = la anterior o 0, `ivadif` = `ctr.ivadif`, `pagide`/`pagtex`/`pagfor` del contrato si
`ctr.pagide` > 0 (M22), `entref` = `su_referencia` o `PROF<MMAA>_<cod_obra>` (M16), `fecdoc` = la fecha, y a 0 lo
de la facturación (lista de design §Filas).
- **R23.** El sistema debe escribir `ctrprodes` por cada vinculada (también con `can` 0), `mov` por cada línea con
`pro.tipmov` 1 (también con `can` 0), `ctrpro.canser` solo de las de `can` ≠ 0 y los estados del contrato, como
F-009 R18-R20 (M6); y la retención (`dcarec`, `tot`, `totpag`) como F-015 sobre los totales del MES.

## Dry-run, commit e idempotencia
- **R24.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas y devolver `previsto` con `cod`/`ide`
provisionales, `cadena` y todas las filas; con `lineas` vacía, la cadena y la proforma con todo a 0.
- **R25.** CUANDO `commit` sea `true`, el sistema debe exigir como F-009 R24 `SIGRID_DOMAIN_WRITE_ENABLED`,
`SIGRID_PROFORMA_WRITE_ENABLED`, credenciales y base de escritura, y al menos una línea (`lineas_obligatorias`); aun
en dry-run, `referencia_no_permitida` sin un prefijo de R3.
- **R26.** El sistema debe escribir la proforma en **una** transacción con los `INSERT` y `UPDATE` de F-009 R25 más
los `dcarec` de F-015; nada más (ni `dcapropar`, `dcaproana`, `dcaprodes`, `asi` ni `pro`).
- **R27.** Dentro de la transacción, bajo `sp_getapplock` (design §Applocks: `SIGRID_PROFORMA_CADENA` tras
`SIGRID_REFEXT_14`), el sistema debe **volver a resolver** la idempotencia, R11 y R12 con las mismas reglas; si el
resultado cambia, construir de nuevo o responder con lo que salga (`existente`, error).
- **R28.** SI un `INSERT` choca con una clave única o las relecturas no cuadran, ENTONCES como F-009 R27-R28
(`colision_de_clave`, `filas_afectadas_inesperadas`), contando también `dcarec`.
- **R29.** CUANDO ya exista un `tip 14` con `dca.synckey` = `referencia_externa`, el sistema debe devolverlo
`idempotente` solo si es una `PROF` (`cla 141`) del mismo contrato; si no, `referencia_en_conflicto`.

## Compatibilidad, seguridad, trazas, verificación y documentación
- **R30.** `sigrid/albaran` (los dos modos) y `sigrid/albaran-directo` deben producir exactamente lo de hoy (tras
F-015): su dorado y sus tests pasan **sin modificarlos** (D6).
- **R31.** Todo el SQL nuevo debe ser constante con `?` y validado con `DatabaseReferenceGuard`; sin `DELETE`, `MERGE`
ni DDL, y sin más `UPDATE` que los de R26 (control negativo en tests).
- **R32.** CUANDO termine una petición, el sistema debe trazar (endpoint, obra, contrato, referencia, `periodo`,
`commit`, `estado`, `cod`, anterior, nº de líneas pedidas y escritas, códigos y duración), nunca textos, precios ni
datos bancarios.
- **R33.** El sistema debe cubrir R1-R32 con tests sin red ni BBDD (`test_f007_rN_*`), comparando el SQL carácter a
carácter, con fase RED y campaña de mutación sin supervivientes no aceptados por el humano.
- **R34.** MANUAL (humano): V3-V5 de la medición; dry-run de una primera y de una encadenada reales (cadena y filas
contra la UI); `commit:true` autorizado de **una** encadenada, revisión en la ficha (cabecera, arrastre, a origen,
retención, totales, servido, impresión), repetición `idempotente` y `existente`; anulación desde la UI.
- **R35.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (ruta, campos, códigos, App
Settings, consumidor facturas F-063, la consulta de cadena para el llamante y `tip 20` = asiento),
`azure-apps/facturas.md` si lo pide su dueño, `docs/ARCHITECTURE.md`, el mapa de rutas de `CLAUDE.md` y
`local.settings.sample.json`.

## Fuera de alcance
Provisiones `PREV`/`ANUL` y proformas sin contrato o sin ORIGEN/ANTERIOR; casar líneas por texto (lo hace el llamante,
D9); medición desglosada (`med`/`canmed`); facturación, vencimiento y paso a FAC (F-008); asiento; modificar o anular;
PDF; varias proformas por petición; cadenas que saltan de contrato (M19: 9).
