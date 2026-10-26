<!-- specs/F-007-registrar-proforma/requirements.md -->
# F-007 · Requisitos (v3.1: enmienda 1 del 2026-10-26, tras la pasada 1 de revisión)

**`POST /api/sigrid/proforma`: alta idempotente de UNA proforma DE MES** (no a origen) **de un subcontratista**, con la
hoja del jefe de obra. La llama `proformas` (su F-005) tras aprobarla en su bandeja, con la hoja ya leída y casada;
`facturas` solo lee lo registrado (`sql/read`). Es un albarán de compra (`con.tip 14`) de la serie `PROF<aa>/`, `dca.cla`
141, `docoritip 0`, solo con las partidas de MES ≠ 0 y las de contrato vinculadas a su `ctrpro` (M27-M28, M40). **Mn**:
[`explore_F-007.md`](../../progress/explore_F-007.md) §v3; **Dn**: design §Decisiones; petición y respuesta en
[`contrato_proformas.md`](contrato_proformas.md). F-009 y F-015 mandan en lo que aquí no se repite («F-009 Rn»).

## Petición y configuración

- **R1.** CUANDO llegue `POST /api/sigrid/proforma`, el sistema debe validar con `ProformaRequest` (`extra="forbid"`,
  textos recortados, números estrictos) los campos de `contrato_proformas.md` §2: obligatorios `database`, `usu`
  (quien aprueba), `referencia_externa` (1-128), `cod_obra`, `periodo` (`AAAAMM`, mes 1-12), `importe_mes` y `lineas`
  (1 o más); opcionales `cod_contrato`, `cif_proveedor`, `nombre_proveedor` (1-128), `sin_contrato` (`false`),
  `otra_del_mes` (`false`), `fecha_proforma` (`AAAAMMDD`), `su_referencia` (≤128), `importe_anterior`,
  `importe_origen`, `numero_orden` y `commit` (`false`). Si no valida, 400 `Solicitud invalida.` sin `codigo` (F-012).
- **R2.** Cada línea debe llevar `referencia_linea` (1-24, única en la petición → `dcapro.refent`), `cantidad` (la del
  MES, ≠ 0, con signo), `precio`, `descripcion` (≤128) y opcionales `partida`, `medicion_contrato`, `unidad` (≤8),
  `cantidad_anterior`, `cantidad_origen`, `ctrpro_ide`, `producto` y `partida_imputacion`; `ctrpro_ide` y `producto`
  no van juntos. Si no, 400 sin `codigo`.
- **R3.** SI no viene `cod_contrato` ni `cif_proveedor` ni `nombre_proveedor`, o viene `sin_contrato` sin
  `cif_proveedor`, o `sin_contrato` con `cod_contrato` o con una línea con `ctrpro_ide`, ENTONCES 400 sin `codigo`.
- **R4.** El sistema debe leer cinco App Settings con defecto cerrado (despliegue propuesto entre paréntesis, D11):
  `SIGRID_PROFORMA_WRITE_ENABLED=false`, `SIGRID_PROFORMA_PREFIJOS_REFERENCIA=[]` (`["PRF-"]`),
  `SIGRID_PROFORMA_PRODUCTOS_SIN_CONTRATO=[]` (`["SM9999", "SB9999", "SM370001"]`),
  `SIGRID_PROFORMA_NATURALEZA_POR_PRODUCTO={}` (`{"SM9999": "SM99", "SB9999": "SB99", "SM370001": "SM37"}`) y
  `SIGRID_PROFORMA_MAX_LINEAS=500`, con los validadores de F-009 (JSON; otra cosa no arranca). La obra se resuelve en
  `SIGRID_ALBARAN_EMPRESAS_OBRA`. Ninguna App Setting existente cambia.
- **R5.** CUANDO llegue `commit:true` con `SIGRID_PROFORMA_WRITE_ENABLED=false`, el sistema debe responder 400
  `escritura_proformas_deshabilitada` **antes** del caso de uso; el dry-run no cambia.
- **R6.** SI falla una validación de negocio, ENTONCES como F-009 R9 (400 `details:{type, codigo[, lineas]}`, los fallos
  de línea de cada etapa de design §Flujo juntos, con `candidatos` si los hay; lo inesperado, 500), códigos de §Códigos.

## Contrato (D4)

- **R7.** CUANDO venga `cod_contrato`, el sistema debe tomarlo entre los contratos de la obra (LP3, sin exigir CIF):
  ninguno, `contrato_no_encontrado`; dos, `contrato_ambiguo`; con `cif_proveedor` ≠ `ctr.entcif`,
  `contrato_de_otro_proveedor`. Manda sobre R8: es como el llamante cambia el contrato resuelto.
- **R8.** CUANDO no venga `cod_contrato` ni `sin_contrato`, el sistema debe resolver el contrato (LP3, LP4): candidatos
  = contratos de la obra con `con.fec` ≤ último día de `periodo`, con alguna línea y del proveedor (`ctr.entcif` =
  `cif_proveedor`, o el `nombre_proveedor` normalizado contenido en el `ctr.entres` normalizado; normalizar = mayúsculas
  y solo letras y cifras); con uno, ese; con varios, los que contienen todas las **líneas de contrato** de la petición
  (R13), por su `ctrpro_ide` o, sin él, por partida y precio (±0,0001) como R14; con uno, ese (M32).
- **R9.** SI tras R8 no queda ningún candidato, ENTONCES `contrato_no_resuelto`; SI quedan varios, ENTONCES
  `contrato_ambiguo` con sus `cod` en el mensaje; SI ningún candidato contiene todas las líneas de contrato pero dos o
  más las reparten sin solaparse, ENTONCES `hoja_de_varios_contratos` con, por línea, el `cod` de su contrato (D5).
- **R10.** El sistema debe devolver en `contrato` (`cod`, `ide`, `resuelto_por`: `peticion` | `proveedor` | `lineas`,
  y `candidatos` con sus `cod`) cómo lo resolvió, en previa y en `creado`.
- **R11.** DONDE venga `sin_contrato`, el sistema debe dar de alta la proforma sin contrato como el modo extendido de
  F-009 sin `cod_contrato` (F-015 R4, R6, R7: proveedor por `cif_proveedor`), con todas las líneas sin vincular y sin
  retención, avisos de contrato ni las comprobaciones de R19-R21.

## Cabecera

- **R12.** El sistema debe construir `con` y `dca` como F-015 (lista blanca y cascada contrato → albarán anterior →
  proveedor) con estas diferencias, y ninguna más: `con.cod` con el prefijo `PROF<aa>/` del año de la fecha de R18
  (5 cifras); `dca.cla` 141; `docoritip` y `docoriide` 0; `entref` = `su_referencia` o, si no viene,
  `PROF<MMAA>_<cod_obra>` (M36), que es el contrato de lectura entre `proformas` y `facturas`; `fecdoc` y `con.fec` = la
  fecha de R18 (D3, D9).

## Líneas (D6)

- **R13.** Una línea es **de contrato** si trae `ctrpro_ide` o `medicion_contrato` > 0; si no, **sin contrato**.
- **R14.** CUANDO una línea de contrato traiga `ctrpro_ide`, el sistema debe comprobar solo que es del contrato
  resuelto, sin re-identificarla ni sustituirla; SI no lo es (también si es de otro contrato de la obra), ENTONCES
  `linea_no_es_del_contrato`. Sin `ctrpro_ide` (respaldo; `proformas` lo manda siempre, D6), debe quedarse, sin relajar
  ningún filtro, con las del contrato de `partida` = código de partida (`obrparpar.cod` del `ctrpro.paride`; sin
  `partida`, ninguna) y |`ctrpro.pre` − `precio`| ≤ 0,0001: una, esa; ninguna, la de arriba; varias, `linea_ambigua` con
  sus `ctrpro_ide` (el desempate, por descripción, es de `proformas`). Medición, unidad y `producto` no cuentan.
- **R15.** La línea de contrato debe construirse como la vinculada de F-009 (R12, R16-R17: `canoriori` = `ctrpro.can`,
  `imporiori` = `ctrpro.tot`, `canoriant`, `imporiant` y `canorilin` 0; aviso de precio distinto) con `paride` = el de
  `partida_imputacion` si viene (F-009 R14) o, si no, el del `ctrpro` (M28: 97,1 %).
- **R16.** La línea sin contrato debe construirse como la sin vincular de F-009 (R13-R15) con su `producto`, de la lista
  de R4 o de los del contrato: SI no lo trae, ENTONCES `producto_obligatorio` (no hay producto por defecto, D6); SI no
  es de ninguno, `producto_no_permitido`. La partida es `partida_imputacion` o `partida` (F-009 R14).
- **R17.** CUANDO el producto de una línea sin contrato sea del contrato, el sistema debe tomar su naturaleza, cuenta y
  analítica de la plantilla de línea de F-009 (L8b, L8; sin ella, 0) y su IVA del `ctrpro` de ese producto, haya o no
  plantilla, nunca del mapeo de R4 (M34: 95,8 %).

## Fecha, comprobaciones y avisos

- **R18.** El sistema debe fijar la fecha como la v2 (D9): `fecha_proforma` si cae en `periodo`; si no, el último día
  de `periodo` si ya pasó (hora de Madrid) u hoy en el mes en curso. SI `periodo` es futuro o `fecha_proforma` cae
  fuera, ENTONCES `periodo_no_valido`.
- **R19.** SI Σ round(`cantidad`·`precio`, 2) difiere de `importe_mes` en más de 0,05 €, ENTONCES
  `importe_mes_no_cuadra`; SI vienen `importe_anterior` e `importe_origen` y `importe_origen` ≠ `importe_anterior` +
  `importe_mes` (±0,05), ENTONCES `hoja_descuadrada`; SI una línea trae `cantidad_anterior` y `cantidad_origen` y
  `cantidad_origen` ≠ `cantidad_anterior` + `cantidad` (±0,001), ENTONCES `linea_descuadrada`. Aun en dry-run.
- **R20.** El sistema debe calcular, sobre las **proformas registradas del contrato** (LP1: `tip 14`, su `ctride`,
  serie `PROF` o `entref` `PROF%`, también las `AC`; sin `PREV`) con fecha anterior al primer día de `periodo`: el
  importe anterior (Σ `totbas`) y, por `ctrpro`, la cantidad anterior (Σ `can`, LP2); y devolverlos en `origen` y por
  línea. CUANDO difieran de `importe_anterior` (±0,05) o de `cantidad_anterior` (±0,001), el sistema debe añadir el
  aviso informativo `anterior_distinto_de_sigrid` (cabecera o línea) con los dos valores (D7).
- **R21.** CUANDO el importe a origen (anterior de R20 + `importe_mes`) supere Σ `ctrpro.tot` del contrato, el sistema
  debe añadir el aviso `supera_contrato`; CUANDO lo supere en más del 10 %, `supera_contrato_10` en su lugar; los
  dos informativos, con importe del contrato, origen y porcentaje, también en `origen` (D8).
- **R22.** CUANDO el contrato tenga alguna proforma a origen (`docoritip 1`), aviso informativo `contrato_a_origen` (D13).

## Ya registrada, dry-run y commit

- **R23.** CUANDO ya exista un `tip 14` con `dca.synckey` = `referencia_externa`, el sistema debe devolverlo
  `idempotente` como F-009 R30 solo si es una proforma (`cla 141`) del mismo contrato; si no, `referencia_en_conflicto`.
- **R24.** CUANDO, sin `otra_del_mes`, entre las proformas **del mismo contrato** (LP1 por `ctride`; ni por obra ni por
  subcontratista) haya una del mismo mes (`con.fec` en `periodo`) con |`totbas` − `importe_mes`| ≤ 0,05, el sistema debe
  devolverla `existente` **sin escribir**, en previa y con `commit`: `cod`, `ide`, `committed` `false` y, por línea
  (LP6), `dcapro.ide`, `linoriide`, producto, cantidad, precio e importe; SI solo las hay con otro total, ENTONCES
  `proforma_del_mes_existente` con sus `cod`. Con `otra_del_mes` y alguna del mes (de cualquier total), aviso
  `otra_del_mes` y sigue (M36; D10; una hoja de dos contratos, D5, no salta).
- **R25.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas y devolver `previsto` con `cod`/`ide`
  provisionales y todas las filas, como F-009 R23 y F-015 R20.
- **R26.** CUANDO `commit` sea `true`, el sistema debe exigir como F-009 R24 `SIGRID_DOMAIN_WRITE_ENABLED`,
  `SIGRID_PROFORMA_WRITE_ENABLED`, credenciales y base de escritura; aun en dry-run, `referencia_no_permitida` sin un
  prefijo de R4 y `demasiadas_lineas` por encima de `SIGRID_PROFORMA_MAX_LINEAS`.
- **R27.** El sistema debe escribir la proforma en **una** transacción con los `INSERT` y `UPDATE` de F-009 R25 y la
  `dcarec` de F-015 R21, con los applocks de F-015 en su orden, y nada más (ni `dcapropar`, `dcaproana`, `asi`…).
- **R28.** Dentro de la transacción, tras `SIGRID_REFEXT_14`, el sistema debe repetir R23 con LP5 (una fila con esa
  referencia que no sea proforma del contrato resuelto da `referencia_en_conflicto`) y R24 con LP1; SI el resultado
  cambia, ENTONCES responder con lo que salga (`idempotente`, `existente` o el error) sin escribir.
- **R29.** SI un `INSERT` choca con una clave única o las relecturas no cuadran, ENTONCES como F-009 R27-R28 y F-015 R22.

## Respuesta, compatibilidad, trazas, pruebas y documentación

- **R30.** El sistema debe responder con la forma del modo extendido (F-009 R7 y F-015 R17) más `estado` `existente`
  (R24), `contrato` (R10), `origen` (`importe_anterior_sigrid`, `importe_mes`, `importe_origen`, `importe_contrato`,
  `porcentaje_contrato`; `null` sin contrato) y, por línea, `ctrpro_ide`, `de_contrato` y `cantidad_anterior_sigrid`.
- **R31.** `sigrid/albaran` (los dos modos) y `sigrid/albaran-directo` deben producir exactamente lo de hoy: su
  dorado y sus tests pasan **sin modificarlos** (D12).
- **R32.** Todo el SQL nuevo debe ser constante con `?` y validado con `DatabaseReferenceGuard`; sin `DELETE`, `MERGE`
  ni DDL, y sin más `UPDATE` que los de R27 (control negativo en tests).
- **R33.** CUANDO termine una petición, el sistema debe trazar (endpoint, obra, contrato y `resuelto_por`, referencia,
  `periodo`, `numero_orden`, `commit`, `estado`, `cod`, nº de líneas de contrato y sin contrato, códigos y duración),
  nunca textos, nombres, CIF, precios ni importes.
- **R34.** El sistema debe cubrir R1-R33 con tests sin red ni BBDD (`test_f007_rN_*`), SQL comparado carácter a
  carácter, con fase RED y campaña de mutación sin supervivientes no aceptados por el humano.
- **R35.** MANUAL (humano): V6-V8 (M39); dry-run de las tres hojas con contrato de la obra 0719 (`existente` con sus
  líneas) y, con `otra_del_mes`, comparadas con su `AC`; un `commit:true` autorizado, revisado en la ficha y en la
  factura, repetido (`idempotente`) y anulado desde la UI.
- **R36.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (ruta, campos, códigos, App
  Settings, consumidor `proformas` F-005), `contrato_proformas.md` si algo cambia, `docs/ARCHITECTURE.md`, el mapa de
  rutas de `CLAUDE.md` y `local.settings.sample.json`.

## Fuera de alcance

Del microservicio `proformas`: leer el xlsx o el pdf, casar las partidas, elegir el producto, aprobar y bloquear la
aprobación por exceso. Un endpoint de lista de productos (se lee por `sql/read`, D11). Cotejar la proforma firmada del
proveedor (lectura de `facturas`). Proformas a origen y cadenas (v2); `PREV`/`ANUL` e `IMPUT`; ampliaciones de
contrato; escribir observaciones, «Nº ORDEN» o «IMPORTE TOTAL» en Sigrid; varias proformas por petición; modificar o
anular; facturación (F-008); PDF.
