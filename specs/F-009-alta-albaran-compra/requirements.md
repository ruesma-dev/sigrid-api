<!-- specs/F-009-alta-albaran-compra/requirements.md -->
# F-009 · Requisitos (v2)

**`POST /api/sigrid/albaran` gana un modo extendido (alta idempotente de UN albarán de compra con
líneas vinculadas y sin vincular, partida o almacén por línea y devoluciones); el clásico sigue
idéntico.** «PRE-1» de albaranes F-053; v2 con las respuestas del humano del 2026-10-01
(`progress/spec_F-009.md`). **[Mn]** = depende de una medición de solo lectura (T0).

## Modos y retrocompatibilidad
- **R1.** CUANDO llegue `POST /api/sigrid/albaran`, el sistema debe decidir el modo por las
**claves presentes** en el objeto JSON, sin mirar sus valores: con `lineas` o
`referencia_externa` → **extendido**; sin ninguna de las dos → **clásico**. SI aparece
`lineas_recibidas` junto a `lineas` o a `referencia_externa`, ENTONCES 400 con `codigo`
`peticion_mixta`, sin leer la base.
- **R2.** En modo clásico, el sistema debe comportarse **exactamente** como hoy: mismo modelo
`AddPurchaseAlbaranRequest`, mismo `CreatePurchaseAlbaranUseCase`, misma respuesta, mismos
errores y las mismas sentencias y filas (incluida la suma en una `dcapro` de las
`lineas_recibidas` del mismo `ctrpro`), con la única excepción de R8.
- **R3.** `sigrid/albaran-directo` no cambia de modelo, caso de uso ni respuesta, salvo R8.
- **R4.** Los casos de uso y modelos actuales de los dos albaranes no se modifican; un **test de
caracterización**, escrito sobre `dev` antes de tocar nada, fija su respuesta y sus sentencias en
dry-run y en commit, y debe seguir pasando sin cambios.

## Contrato del modo extendido y configuración
- **R5.** En modo extendido, el sistema debe validar con Pydantic (`extra="forbid"`, textos
recortados): `database`, `cod_obra` (≤24), `cif_proveedor` (≤24), `referencia_externa` (1-128,
obligatoria), `cod_contrato` (≤24, opcional), `su_referencia` (≤128, defecto `""`),
`fecha_albaran` (`YYYYMMDD`, opcional), `empide` (≥1, opcional), `commit` (defecto `false`) y
`lineas` (≥1), cada una con `referencia_linea` (1-64), `ctrpro_ide` **o** `producto` (código,
≤24), `descripcion` (≤128), `unidad` (≤8), `cantidad`, `precio` (≥0) y `partida` (código, ≤24)
**o** `almacen: true`; ante campo ausente o sobrante, longitud o dominio → 400 `Solicitud invalida.`
- **R6.** El sistema debe rechazar así también la línea que traiga a la vez o ninguno de
`ctrpro_ide`/`producto`, o de `partida`/`almacen:true`; tenga `cantidad == 0`; sea sin vincular
sin `descripcion`; repita `referencia_linea`; o sea vinculada sin `cod_contrato`. Las
cantidades **negativas** valen en vinculadas **y en sin vincular**.
- **R7.** El sistema debe responder en modo extendido con un **superconjunto** de la respuesta
clásica (todos los campos de `AddPurchaseAlbaranResponse`; en cada línea, todos los de
`AlbaranLinePreview`, con `ctrpro_ide`/`linoriide` 0 en las sin vincular) más `estado`
(`previsto`|`creado`|`idempotente`), `referencia_externa`, `avisos[]` `{codigo, mensaje}`,
`filas` y, por línea, `indice`, `referencia_linea`, `tipo`, `producto`, `paride`, `partida`,
`almacen`, `cenide` y `avisos`; igual en dry-run, commit e idempotencia.
- **R8.** CUANDO `sigrid/albaran` (en cualquier modo) o `sigrid/albaran-directo` reciban
`commit:true` con `SIGRID_ALBARAN_WRITE_ENABLED=false`, el sistema debe responder 400 con
`codigo` `escritura_albaranes_deshabilitada` antes de ejecutar el caso de uso; el dry-run no cambia.
- **R9.** SI falla una validación de cabecera en modo extendido, ENTONCES 400 `{ok:false, error,
details:{type, codigo}}` con `codigo` del conjunto cerrado de design §Códigos. SI fallan
líneas, ENTONCES el sistema debe validarlas **todas** y responder 400 `lineas_no_validas` con
`details.lineas[]` = `{indice, referencia_linea, codigo, mensaje}`. Lo inesperado, 500.
- **R10.** El sistema debe leer cuatro App Settings nuevas con defecto cerrado: `SIGRID_ALBARAN_WRITE_ENABLED=false`,
`SIGRID_ALBARAN_PREFIJOS_REFERENCIA=[]` (despliegue `["ALB-"]`), `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO=[]`
(despliegue `["MA9999"]`) y `SIGRID_ALBARAN_MAX_LINEAS=100`. Ninguna existente cambia
(`ALLOWED_WRITE_DATABASES` sigue en `["ruesma"]`) y no se toca `infrastructure/security/`.

## Resolución y construcción (modo extendido)
- **R11.** El sistema debe resolver con lecturas la obra por `(tip 42, cod)` (0 →
`obra_no_encontrada`, >1 → `obra_ambigua`); con `cod_contrato`, el contrato con el localizador
actual y de esa obra (`contrato_no_encontrado`, `contrato_ambiguo`); y la plantilla de cabecera
como hoy (último albarán del proveedor; sin contrato, por CIF; ninguno →
`proveedor_sin_albaran_previo`), con aviso `plantilla_de_otro_proveedor` si no es suya.
- **R12.** Por línea vinculada, el sistema debe exigir que el `ctrpro` sea del contrato
(`linea_no_es_del_contrato`) y tomar de él producto, cuenta, IVA, centro, almacén y, si no
vienen, `descripcion` y `unidad`. Varias líneas al mismo `ctrpro` son cada una su `dcapro`,
su `ctrprodes` y su `mov` (aquí **no** se suman).
- **R13.** Por línea sin vincular, el sistema debe resolver `producto` por código en el maestro
[M11]: fuera de `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` → `producto_no_permitido`; inexistente o
de baja → `producto_no_encontrado`. Cuenta, IVA y naturaleza, del maestro y, si valen 0, de la
última `dcapro` del producto. Sin `docori*`, sin `ctrprodes` y sin tocar `canser`.
- **R14.** El sistema debe resolver `partida` por código entre las partidas de la obra: 0 →
`partida_no_encontrada`, >1 → `partida_ambigua`, capítulo o desactivada →
`partida_no_imputable` [M3]. `dcapro.paride` es la resuelta o 0: **nunca** heredada.
- **R15.** CUANDO una línea traiga `almacen:true`, el sistema debe escribir `paride` 0 y el
almacén: vinculada, el del `ctrpro` o del contrato; sin vincular, el del contrato o, sin él, el
de la obra [M8]; si no sale uno solo → `almacen_de_obra_no_resuelto`. El centro, igual.
- **R16.** CUANDO una vinculada traiga partida distinta de la del `ctrpro`, el sistema debe
escribir la de la petición, no tocar el `ctrpro` y avisar `partida_distinta_del_contrato` [M4].
- **R17.** El sistema debe escribir `pre` = `precio`, `tot` = `round(cantidad·precio, 2)` e
`ivacuo` = `round(tot·tasa, 2)` con la tasa de `dbo.iva` [M11]. CUANDO una vinculada traiga
precio distinto del `ctrpro`: `tar` = `precio`, `dto` = `''` y aviso
`precio_distinto_del_contrato`; si es igual, `tar` y `dto` del `ctrpro`.
- **R18.** CUANDO una línea (vinculada o sin vincular) tenga cantidad negativa, el sistema debe
escribir `can` y `tot` negativos y su `mov` con la regla de design §Devoluciones: la que mida
M5 o, si M5 no encuentra devoluciones reales, la **hipótesis A** (simétrica al alta). En una
vinculada, `ctrprodes.can` = cantidad y `canser += cantidad` [M6]. SI el `canser` resultante
queda < 0, ENTONCES se **admite** con aviso `servido_negativo`; SI el stock queda < 0, aviso
`stock_negativo`.
- **R19.** Para cantidades positivas, el sistema debe escribir `mov` como hoy (`tip 1`, `oritip 5`,
`destip 2`, `doctip 14`) con PMP `(stock·pma + can·pre)/(stock + can)` sin redondear,
encadenado por (producto, almacén) dentro del albarán.
- **R20.** El sistema debe recalcular `ctr.estser`/`estfac` **dentro** de la transacción con las
sumas de todas las líneas del contrato tras actualizar `canser`, con la regla de hoy (`estser` =
1 si `Σcanser ≥ Σcan`, si no 0): una devolución puede devolver `estser` a 0 (`Σcanser` < 0 da 0).
- **R21.** El sistema debe construir cada `dcapro` desde la plantilla poniendo a su valor inicial
las columnas que describen otra línea (lista de reseteo, design §Filas) [M14], y la `dca` con
`synckey` = `referencia_externa`, `ctride` 0 sin contrato y los totales sumados.
- **R22.** El sistema debe calcular `fec` (si no viene), `hor` y `fechor` en hora de Madrid una
vez por petición; el prefijo `AC<aa>/` sale del año de `fecha_albaran`; `con.est` es el estado
inicial medido [M2], comprobado en `dbo.conest` (`estado_inicial_no_encontrado`).

## Dry-run, commit e idempotencia (modo extendido)
- **R23.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas con credenciales de
lectura y devolver `estado:"previsto"`, `cod`/`ide` provisionales con su aviso y las filas
completas de `con`, `dca`, `dcapro`, `ctrprodes` y `mov`.
- **R24.** CUANDO `commit` sea `true`, el sistema debe exigir antes de leer nada
`SIGRID_DOMAIN_WRITE_ENABLED`, `SIGRID_ALBARAN_WRITE_ENABLED` y credenciales de escritura
(`escritura_albaranes_deshabilitada`), y `database` en `ALLOWED_WRITE_DATABASES`, que vacía
**no** abre (`base_de_datos_no_permitida`). Más de `SIGRID_ALBARAN_MAX_LINEAS` líneas →
`demasiadas_lineas`, también en dry-run.
- **R25.** El sistema debe escribir el albarán en **una** transacción: `INSERT` de `con`, `dca`,
`dcapro`×N, `ctrprodes`×M y `mov`×N, `UPDATE` relativo de `ctrpro.canser` por vinculada y
`UPDATE` de `ctr.estser/estfac` por `ide`. Ninguna otra escritura.
- **R26.** Dentro de la transacción, bajo `sp_getapplock` en el orden de design §Applocks y con
`WITH (UPDLOCK, HOLDLOCK)`, el sistema debe reservar el `cod` (`MAX` numérico del prefijo + 1,
por `emp` [M2]), los `ide` de `con`, `dcapro`, `ctrprodes` y `mov` (`MAX+1`) y leer el stock y
PMP vigentes de cada (producto, almacén).
- **R27.** SI un `INSERT` choca con una clave única (alta simultánea del escritorio), ENTONCES el
sistema debe repetir la transacción entera recalculando `cod`, `ide` y balances hasta
`DOMAIN_WRITE_MAX_RETRIES`; agotados, 400 `colision_de_clave` y el ERP intacto.
- **R28.** SI antes del `COMMIT` las relecturas (design E12) no dan 1 `con`, 1 `dca`, N `dcapro`,
N `mov` y M `ctrprodes`, ENTONCES el sistema debe hacer `ROLLBACK` (`filas_afectadas_inesperadas`).
- **R29.** SI `referencia_externa` no empieza por un prefijo admitido, ENTONCES `referencia_no_permitida` (también en dry-run).
- **R30.** CUANDO ya exista un albarán `tip 14` con `dca.synckey` = `referencia_externa`, del mismo
proveedor y obra, el sistema debe devolverlo `idempotente` (`ide`, `cod`, `fec`, totales y
líneas leídas) sin escribir; se busca con lecturas en dry-run y, en commit, **dentro** de la
transacción bajo el applock de referencias, antes de reservar nada. Más de uno, u otro
proveedor u obra → `referencia_en_conflicto` [M1].

## Seguridad, trazas, verificación y documentación
- **R31.** Todo el SQL nuevo debe ser constante con valores `?` y validado con
`DatabaseReferenceGuard.validate(..., allowed=[database])`; sin `DELETE`, `MERGE` ni DDL, y sin
más `UPDATE` que los de R25 (control negativo en tests).
- **R32.** CUANDO termine una petición en modo extendido, el sistema debe registrar una traza
(obra, contrato, referencia, `commit`, `estado`, `cod`, nº de líneas, códigos, duración),
**nunca** descripciones ni precios.
- **R33.** Ante una petición extendida equivalente a una clásica (solo vinculadas, positivas, sin
`ctrpro` repetido, partida y precio del `ctrpro`), el sistema debe producir filas iguales columna
a columna a las del modo clásico, salvo las diferencias de design §Equivalencia.
- **R34.** El sistema debe cubrir R1-R33 con tests sin red ni BBDD (`test_f009_rN_*`), comparando
el SQL carácter a carácter, con fase RED en R1, R8, R14, R18, R26-R28 y R30.
- **R35.** MANUAL (humano): T0; dry-run clásico y extendido sobre `CTSU16/0206` (obra 0404);
`commit:true` autorizado de **un** albarán extendido (vinculada, sin vincular, almacén y negativa)
revisado en la UI, repetición `idempotente` y anulación en la UI (nunca `DELETE`); tras el
despliegue, comprobación de solo lectura de la **primera devolución real** del pipeline.
- **R36.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (§4, §4.1,
§7.2, §7.5, §7.6, §8.6 y §8.7, §10 con albaranes F-053, §13), `docs/ARCHITECTURE.md` y
`local.settings.sample.json`.

## Fuera de alcance
`dcapropar` (salvo M7), `dbo.log` (salvo M13), almacén/centro/analítica en la petición, recalcular
`mov` posteriores a una fecha atrasada (M10), el PDF, modificar o anular, producto por familia,
varios albaranes por petición y cambiar el modo clásico o `albaran-directo` salvo R8.
