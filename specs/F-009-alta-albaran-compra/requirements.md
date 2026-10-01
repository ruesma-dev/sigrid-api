<!-- specs/F-009-alta-albaran-compra/requirements.md -->
# F-009 · Requisitos

**`POST /api/sigrid/albaran-compra`: alta idempotente de UN albarán de compra (`con.tip 14`,
serie `AC<aa>/`) con líneas vinculadas a contrato y sin vincular, partida o almacén por línea
y devoluciones.** Es la «PRE-1» de albaranes F-053 (su `design.md` §2). Decisiones del humano
(2026-10-01), preguntas y mediciones: `progress/spec_F-009.md`. Lo marcado **[Mn]** depende de
una medición de solo lectura (T0): si la contradice, se vuelve a la PARADA 1.

## Contrato y configuración

- **R1.** CUANDO llegue `POST /api/sigrid/albaran-compra` con `x-functions-key` y JSON con
`database`, `cod_obra` (≤24), `cif_proveedor` (≤24), `referencia_externa` (1-128,
obligatoria), `cod_contrato` (≤24, opcional), `su_referencia` (≤128, defecto `""`),
`fecha_albaran` (`YYYYMMDD`, opcional), `empide` (opcional), `commit` (defecto `false`) y
`lineas` (≥1), cada una con `referencia_linea` (1-64), `ctrpro_ide` **o** `producto` (código,
≤24), `descripcion` (≤128), `unidad` (≤8), `cantidad`, `precio` (≥0), `partida` (código, ≤24)
**o** `almacen: true`, el sistema debe validarlo con Pydantic (`extra="forbid"`, textos
recortados) y responder 400 `Solicitud invalida.` ante campo ausente o sobrante, longitud
excedida o valor fuera de dominio.
- **R2.** El sistema debe rechazar así también la línea que: traiga a la vez o ninguno de
`ctrpro_ide`/`producto`, o de `partida`/`almacen:true`; tenga `cantidad == 0`; sea sin vincular
sin `descripcion`; repita `referencia_linea`; o sea vinculada sin `cod_contrato`. Las
cantidades **negativas** (devoluciones) son válidas en los dos tipos de línea.
- **R3.** El sistema debe responder con la misma forma en dry-run, commit e idempotencia: `ok`,
`database`, `committed`, `dry_run`, `estado` (`previsto`|`creado`|`idempotente`), `con_ide`,
`cod`, `referencia_externa`, `cabecera` (obra, proveedor, contrato, `almide`, `cenide`,
`empide`, `fec`, totales), `lineas[]` (`indice`, `referencia_linea`, `tipo`
`vinculada`|`sin_vincular`, `ctrpro_ide`, `proide`, `producto`, `descripcion`, `unidad`,
`cantidad`, `precio`, `total`, `iva_cuota`, `paride`, `partida`, `almacen`, `almide`, `cenide`,
stock y PMP anterior y resultante, `avisos`), `estados_contrato`, `filas` y `avisos[]` como
`{codigo, mensaje}`.
- **R4.** SI falla una validación de cabecera, ENTONCES el sistema debe responder 400 `{ok:false,
error, details:{type, codigo}}` con `codigo` del conjunto cerrado de design §Códigos. SI fallan
líneas, ENTONCES debe validarlas **todas** y responder 400 `lineas_no_validas` con
`details.lineas[]` = `{indice, referencia_linea, codigo, mensaje}`. Lo inesperado, 500.
- **R5.** El sistema debe leer cuatro App Settings nuevas con defecto cerrado:
`SIGRID_ALBARAN_WRITE_ENABLED=false`, `SIGRID_ALBARAN_PREFIJOS_REFERENCIA=[]`,
`SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO=[]` y `SIGRID_ALBARAN_MAX_LINEAS=100`.
- **R6.** `sigrid/albaran` y `sigrid/albaran-directo` deben conservar petición, respuesta y
comportamiento: sus casos de uso y modelos no se modifican.
- **R7.** *(Si el humano aprueba la pregunta 2.)* CUANDO `sigrid/albaran` o `albaran-directo`
reciban `commit:true` con `SIGRID_ALBARAN_WRITE_ENABLED=false`, el sistema debe responder 400
antes de abrir ninguna transacción; el dry-run no cambia.
- **R8.** Ninguna App Setting existente cambia de valor; `ALLOWED_WRITE_DATABASES` sigue en
`["ruesma"]`; no se toca `infrastructure/security/`.

## Resolución y construcción del albarán

- **R9.** El sistema debe resolver con lecturas: la obra por `(tip 42, cod)` (0 →
`obra_no_encontrada`, >1 → `obra_ambigua`); con `cod_contrato`, el contrato con el localizador
actual y de esa obra (`contrato_no_encontrado`, `contrato_ambiguo`); la plantilla de cabecera
como hoy (último albarán del proveedor; sin contrato, por CIF; ninguno →
`proveedor_sin_albaran_previo`), con aviso `plantilla_de_otro_proveedor` si no es suya.
- **R10.** Por línea vinculada, el sistema debe exigir que el `ctrpro` sea del contrato
(`linea_no_es_del_contrato`) y tomar de él producto, cuenta, IVA, centro, almacén y, si no
vienen, `descripcion` y `unidad`. Varias líneas al mismo `ctrpro` son cada una su `dcapro`,
su `ctrprodes` y su `mov`.
- **R11.** Por línea sin vincular, el sistema debe resolver `producto` por código en el maestro
[M11]: fuera de `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` → `producto_no_permitido`; inexistente o
de baja → `producto_no_encontrado`. Cuenta, IVA y naturaleza, del maestro y, si valen 0, de la
última `dcapro` del producto. Sin `docori*`, sin `ctrprodes` y sin tocar `canser`.
- **R12.** El sistema debe resolver `partida` por código entre las partidas de la obra
(`obrparpar.obride`): 0 → `partida_no_encontrada`, >1 → `partida_ambigua`, capítulo o
desactivada → `partida_no_imputable` [M3]. `dcapro.paride` es la resuelta o 0: **nunca** se
hereda de la plantilla ni de otra `dcapro`.
- **R13.** CUANDO una línea traiga `almacen:true`, el sistema debe escribir `paride` 0 y el
almacén: vinculada, el del `ctrpro` o el del contrato; sin vincular, el del contrato o, sin él,
el de la obra [M8]; si no sale uno solo → `almacen_de_obra_no_resuelto`. El centro, igual.
- **R14.** CUANDO una vinculada traiga partida distinta de la del `ctrpro`, el sistema debe
escribir la de la petición, no tocar el `ctrpro` y avisar `partida_distinta_del_contrato` [M4].
- **R15.** El sistema debe escribir `pre` = `precio`, `tot` = `round(cantidad·precio, 2)` e
`ivacuo` = `round(tot·tasa, 2)` con la tasa de `dbo.iva` [M11]. CUANDO una vinculada traiga
precio distinto del `ctrpro`, `tar` = `precio`, `dto` = `''` y aviso
`precio_distinto_del_contrato`; si es igual, `tar` y `dto` del `ctrpro`.
- **R16.** CUANDO una línea tenga cantidad negativa, el sistema debe escribir `can` y `tot`
negativos y su `mov` con la regla de devolución medida [M5] (design §Devoluciones); en una
vinculada, `ctrprodes.can` = cantidad y `canser += cantidad` [M6]. SI el `canser` resultante
queda < 0, ENTONCES `devolucion_supera_lo_servido`; SI el stock queda < 0, aviso `stock_negativo`.
- **R17.** Para cantidades positivas, el sistema debe escribir `mov` como hoy (`tip 1`, `oritip 5`,
`destip 2`, `doctip 14`) con PMP `(stock·pma + can·pre)/(stock + can)` sin redondear,
encadenado por (producto, almacén) dentro del albarán.
- **R18.** El sistema debe recalcular `ctr.estser`/`estfac` **dentro** de la transacción con las
sumas de todas las líneas del contrato leídas tras actualizar `canser`.
- **R19.** El sistema debe construir cada `dcapro` desde la plantilla poniendo a su valor inicial
las columnas que describen otra línea (lista de reseteo, design §Filas) [M14], y la `dca` con
`synckey` = `referencia_externa`, `ctride` 0 sin contrato y los totales sumados.
- **R20.** El sistema debe calcular `fec` (si no viene), `hor` y `fechor` en hora de Madrid una
vez por petición; el prefijo `AC<aa>/` sale del año de `fecha_albaran`; `con.est` es el estado
inicial medido [M2], comprobado en `dbo.conest` (`estado_inicial_no_encontrado`).

## Dry-run, commit e idempotencia

- **R21.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas con credenciales de
lectura y devolver `estado:"previsto"`, `cod`/`ide` provisionales con su aviso y las filas
completas de `con`, `dca`, `dcapro`, `ctrprodes` y `mov`.
- **R22.** CUANDO `commit` sea `true`, el sistema debe exigir antes de leer nada
`SIGRID_DOMAIN_WRITE_ENABLED`, `SIGRID_ALBARAN_WRITE_ENABLED` y credenciales de escritura
(`escritura_albaranes_deshabilitada`), y `database` en `ALLOWED_WRITE_DATABASES`, que vacía
**no** abre (`base_de_datos_no_permitida`). Más de `SIGRID_ALBARAN_MAX_LINEAS` líneas →
`demasiadas_lineas`, también en dry-run.
- **R23.** El sistema debe escribir el albarán en **una** transacción: `INSERT` de `con`, `dca`,
`dcapro`×N, `ctrprodes`×M y `mov`×N, `UPDATE` relativo de `ctrpro.canser` por línea vinculada
y `UPDATE` de `ctr.estser/estfac` por `ide`. Ninguna otra escritura.
- **R24.** Dentro de la transacción, bajo `sp_getapplock` en el orden de design §Applocks y con
`WITH (UPDLOCK, HOLDLOCK)`, el sistema debe reservar el `cod` (`MAX` numérico del prefijo + 1,
por `emp` [M2]), los `ide` de `con`, `dcapro`, `ctrprodes` y `mov` (`MAX+1`) y leer el stock y
PMP vigentes de cada (producto, almacén).
- **R25.** SI un `INSERT` choca con una clave única (alta simultánea del escritorio), ENTONCES el
sistema debe revertir y repetir la transacción entera recalculando `cod`, `ide` y balances
hasta `DOMAIN_WRITE_MAX_RETRIES`; agotados, 400 `colision_de_clave` y el ERP intacto.
- **R26.** Antes del `COMMIT`, el sistema debe releer `con` por `(tip, cod)` = 1, `dca` por `ide`
= 1, `dcapro` y `mov` por `docide` = N, `ctrprodes` por `docdeside` = M y el `canser` de cada
`ctrpro` tocado ≥ 0; SI no cuadra, ENTONCES `ROLLBACK` y `filas_afectadas_inesperadas`.
- **R27.** SI `referencia_externa` no empieza por un prefijo de
`SIGRID_ALBARAN_PREFIJOS_REFERENCIA`, ENTONCES `referencia_no_permitida`, también en dry-run.
- **R28.** CUANDO ya exista un albarán `tip 14` con `dca.synckey` = `referencia_externa`, del mismo
proveedor y obra, el sistema debe devolverlo `idempotente` (`ide`, `cod`, `fec`, totales y
líneas leídas) sin escribir; se busca con lecturas en dry-run y, en commit, **dentro** de la
transacción bajo el applock de referencias, antes de reservar nada. Más de uno, u otro
proveedor u obra → `referencia_en_conflicto` [M1].

## Seguridad, trazas, verificación y documentación

- **R29.** Todo el SQL debe ser constante con valores `?` y validado con
`DatabaseReferenceGuard.validate(..., allowed=[database])`; sin `DELETE`, `MERGE` ni DDL, y sin
más `UPDATE` que los de R23 (control negativo en tests).
- **R30.** CUANDO termine una petición, el sistema debe registrar una traza (obra, contrato,
referencia, `commit`, `estado`, `cod`, nº de líneas, códigos de error, duración), **nunca**
descripciones ni precios.
- **R31.** Ante una petición equivalente a una de `sigrid/albaran` (solo vinculadas, positivas,
partida y precio del `ctrpro`), el sistema debe producir filas iguales columna a columna a las
del caso de uso actual, salvo las diferencias declaradas en design §Equivalencia.
- **R32.** El sistema debe cubrir R1-R31 con tests sin red ni BBDD (`test_f009_rN_*`), comparando
el SQL carácter a carácter, con fase RED en R12, R16, R24-R26 y R28.
- **R33.** MANUAL (humano): T0 (mediciones M1-M15); dry-run sobre `CTSU16/0206` (obra 0404) con
líneas vinculada, sin vincular, de almacén y negativa; `commit:true` autorizado de **un**
albarán revisado en la UI; repetición `idempotente`; anulación desde la UI (nunca `DELETE`).
- **R34.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (§4, §4.1,
§7.2, §7.5, §7.6, §8.10 nueva, §10 con albaranes F-053, §13), `docs/ARCHITECTURE.md`, el mapa
de rutas de `CLAUDE.md` y `local.settings.sample.json`.

## Fuera de alcance

`dcapropar` (salvo que M7 diga que el escritorio lo escribe siempre), fila de `dbo.log` (salvo
M13), almacén, centro o cuenta analítica en la petición, recalcular `mov` posteriores a un
albarán con fecha atrasada (M10), el PDF (`concepto-grafico`), modificar o anular albaranes,
facturas, producto por familia, varios albaranes por petición y cambiar `sigrid/albaran` o
`albaran-directo` más allá de R7.
