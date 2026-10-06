<!-- specs/F-009-alta-albaran-compra/requirements.md -->
# F-009 · Requisitos (v8.2)

**`POST /api/sigrid/albaran` gana un modo extendido (alta idempotente de UN albarán de compra con líneas vinculadas y
sin vincular, con o sin partida por línea y devoluciones); el clásico sigue idéntico.** «PRE-1» de albaranes F-053. Huecos
**Hn** de [`contrato_albaranes.md`](contrato_albaranes.md) §5 (si discrepa, manda la spec). v8.2: `spec_F-009.md` §v8.2.

## Modos y retrocompatibilidad
- **R1.** CUANDO llegue `POST /api/sigrid/albaran`, el sistema debe decidir el modo por las **claves
presentes** (no por sus valores): con `lineas` o `referencia_externa` → **extendido**; sin ninguna →
**clásico**. SI además aparece `lineas_recibidas`, ENTONCES 400 `peticion_mixta`, sin leer la base.
- **R2.** En modo clásico, el sistema debe comportarse **exactamente** como hoy (modelo, caso de uso, respuesta,
errores, sentencias y filas, incluida la suma de `lineas_recibidas` del mismo `ctrpro`), salvo R8.
- **R3.** `sigrid/albaran-directo` no cambia de modelo, caso de uso ni respuesta, salvo R8.
- **R4.** Los casos de uso y modelos actuales de los dos albaranes no se modifican; un **test de caracterización**
escrito sobre `dev` antes de tocar nada fija su respuesta y sentencias en dry-run y en commit, y pasa sin cambios.

## Contrato del modo extendido y configuración
- **R5.** En modo extendido, el sistema debe validar con Pydantic (`extra="forbid"`, textos recortados)
los campos, longitudes y dominios de design §Modelo y normalizar `cif_proveedor` a mayúsculas sin espacios
(H21); si no, 400 `Solicitud invalida.` sin `codigo`.
- **R6.** El sistema debe rechazar así también la línea con a la vez o ninguno de `ctrpro_ide`/`producto`; con
`cantidad == 0`; sin vincular sin `descripcion`; con `referencia_linea` repetida; vinculada sin `cod_contrato`;
o con `paride` sin `partida`. Valen: cantidades **negativas**; `cod_contrato` **sin** vinculadas (H31); `partida`
ausente o `null` (**sin partida**; no hay `almacen` ni `naturaleza`, H34); `fecha_albaran` futura (H19).
- **R7.** El sistema debe responder en modo extendido con un **superconjunto** de la respuesta clásica más los
campos de design §Respuesta: `indice` **desde 0** (H26); avisos `{codigo, mensaje}` en cabecera y línea, cada
texto de `warnings` con su aviso (H27); `cabecera`/`filas.dca` sin columnas bancarias (se escriben; H16).
- **R8.** CUANDO `sigrid/albaran` (cualquier modo) o `sigrid/albaran-directo` reciban `commit:true` con
`SIGRID_ALBARAN_WRITE_ENABLED=false`, el sistema debe responder 400 `escritura_albaranes_deshabilitada`
antes de ejecutar el caso de uso; el dry-run no cambia.
- **R9.** SI falla una validación de cabecera en modo extendido, ENTONCES 400 `{ok:false, error, details:{type,
codigo}}` con `codigo` de design §Códigos. SI fallan líneas, ENTONCES el sistema debe validarlas **todas** y
responder 400 `lineas_no_validas` con `details.lineas[]` = `{indice, referencia_linea, codigo, mensaje}`; lo inesperado, 500.
- **R10.** El sistema debe leer seis App Settings nuevas `SIGRID_ALBARAN_*` con defecto cerrado (despliegue entre
paréntesis): `WRITE_ENABLED=false`, `PREFIJOS_REFERENCIA=[]` (`["ALB-"]`), `PRODUCTOS_SIN_CONTRATO=[]` (`["MA9999",
"QA9999", "XA9999"]`; H20), `EMPRESAS_OBRA=[]` (`[1]`; H2), `MAX_LINEAS=100` y `NATURALEZA_POR_PRODUCTO={}` (`{"MA9999":
"MA99", "QA9999": "QA99", "XA9999": "XA99"}`; H34; objeto JSON de textos o **no arranca**). Ninguna existente cambia.

## Resolución y construcción (modo extendido)
- **R11.** El sistema debe resolver con lecturas: la obra por `(tip 42, cod)` **entre las empresas de
`SIGRID_ALBARAN_EMPRESAS_OBRA`** (H2: ninguna → `obra_no_encontrada`; solo en otras, o lista vacía →
`obra_de_empresa_no_permitida`; >1 → `obra_ambigua`); el contrato con el localizador actual y de esa obra
(`contrato_no_encontrado`, `contrato_ambiguo`); `usu` en `dbo.usu` (`usuario_no_valido`); y la plantilla
de cabecera, el último albarán **del mismo proveedor en la empresa de la obra** (H3; ninguno →
`proveedor_sin_albaran_previo`). `con.emp` = empresa de la obra.
- **R12.** Por vinculada, el sistema debe exigir que el `ctrpro` sea del contrato (`linea_no_es_del_contrato`)
y tomar de él producto, cuenta, IVA, centro, almacén, analítica, `cod2`, `dncide` y `dncproide` (`''`/0 si no los
tiene; nunca de la plantilla; H35) y, si no vienen, `descripcion` y `unidad`. Varias al mismo `ctrpro`: una
`dcapro`, `ctrprodes` y `mov` cada una (**no** se suman).
- **R13.** Toda línea sin vincular lleva un `producto` de la lista blanca, elegido por el llamante línea
a línea; el sistema debe resolverlo por `(emp de la obra, cod)` en el maestro (`tip 3`): fuera de
`SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO` → `producto_no_permitido`; inexistente o de baja →
`producto_no_encontrado`. IVA, de la última `dcapro` del producto **del mismo proveedor** o, si no hay, de la
última del producto con aviso `iva_de_otro_proveedor` (H15; M11); naturaleza, cuenta y analítica, de R13b y
R15; §Reseteo vacías (H11, H35, M14); sin `docori*`, `ctrprodes` ni `canser`.
- **R13b.** El sistema debe tomar como naturaleza de la sin vincular la de su producto en el mapeo de R10 (H34;
**nunca** `pro.natide` ni la plantilla): una sola `auxpronat` con ese `cod`, sin baja y `numemp` en {0, empresa de la
obra} (P2); de ella `natide`, el `caaide` de R15 y `cueide` = la única `cua` de código `cuacomcod` en la empresa del
albarán (P3, P4). SI falta la entrada, la naturaleza o esa `cua`, ENTONCES fallo de línea `naturaleza_no_valida`.
- **R14.** El sistema debe resolver `partida` entre las **imputables** de la obra (`tip 1`, `tipdes 0`,
`tipvis` 0/1; **no** exige hoja, H4): ninguna → `partida_no_encontrada` (o `partida_no_imputable`), >1
sin `paride` → `partida_ambigua` (N2). `paride`: la resuelta o 0 (sin partida); **nunca** del `ctrpro` ni
de otra línea.
- **R14b.** CUANDO una línea con `partida` traiga `paride` (opcional; M3: 4.312 códigos repetidos, H17), el
sistema debe exigir que sea de la obra, imputable y con ese código (`paride_no_valido`) y usarlo.
- **R15.** El sistema debe escribir `paride` 0 en la línea sin partida, y en toda línea su almacén físico
(el del stock y el `mov`) y centro: vinculada, del `ctrpro` o del contrato; **toda sin vincular** (H10),
del contrato o, sin él, `obr.almide`/`obr.cenide` y, si faltan, del único `alm` de la obra (H13; M16);
si no sale uno → `almacen_de_obra_no_resuelto`. `caaide`: vinculada, **siempre** el del `ctrpro` (M16); sin
vincular, la `caa` del centro de la línea y código `<cod_obra>.<caagascod de R13b sin el prefijo MOD.>` (H10, M16c/
M16d); ninguna, varias o `caagascod` vacío → fallo de línea `analitica_no_resuelta`.
- **R16.** CUANDO una vinculada traiga partida distinta de la del `ctrpro`, el sistema debe escribir la
pedida, no tocar el `ctrpro` y avisar `partida_distinta_del_contrato`; CUANDO venga sin partida con
`ctrpro.paride` ≠ 0, avisar `sin_partida_en_linea_con_partida` (H12), informativo.
- **R17.** El sistema debe escribir `pre` = `tar` = `precio`, `dto` = `''`, `tot` = `cantidad·pre` e `ivacuo` = `tot·iva`
(`dbo.iva`; M11), a 2 decimales con `Decimal` y `ROUND_HALF_UP` (H33). Vinculada con |`precio` − `ctrpro.pre`| ≤ 0,0001
**y** `round(cantidad·precio, 2)` = `round(cantidad·ctrpro.pre, 2)` (opción C, v8.2): `pre`, `tar` y `dto` del `ctrpro`
(H14); si no, aviso `precio_distinto_del_contrato`. SI `precio` < 0, ENTONCES fallo de línea `precio_negativo` (H8).
- **R18.** CUANDO una línea tenga cantidad negativa, el sistema debe escribir `can` y `tot` negativos y su
`mov` con la **regla A** (M5: entrada con `canent` < 0 y PMP de R19). Vinculada: `ctrprodes.can` =
cantidad y `canser += cantidad`. SI `canser` queda < 0, ENTONCES se **admite** con aviso
`servido_negativo`; SI el stock queda < 0, `stock_negativo`.
- **R19.** El sistema debe escribir un `mov` por línea **si y solo si** su producto tiene `pro.tipmov` = 1 (M9, también
`XA9999`), como hoy (`tip 1`, `oritip 5`, `destip 2`, `doctip 14`), **fechado en el alta** (N1), con `almpma` `(stock·pma +
can·pre)/(stock + can)` sin redondear y `prepma` = el PMP de partida (design §`prepma`). Con |`stock + can`| < ε = 1e-6
(cero con residuo binario: `almcan` y `almpma` son «Real», con tolerancia; v8.2) se conserva el PMP y se escribe `almcan` 0.
- **R20.** CUANDO haya vinculadas, el sistema debe recalcular `ctr.estser`/`estfac` **dentro** de la
transacción con las sumas del contrato tras actualizar `canser` (`estser` = 1 si `Σcanser ≥ Σcan`, si no
0: una devolución puede devolverlo a 0). Sin vinculadas, ningún `UPDATE` (H31).
- **R21.** El sistema debe construir cada `dcapro` desde su plantilla, como hoy, salvo `prepma` = el `mov.prepma` de
su `mov` (M14: 100 %) o 0 sin `mov` (M14c: 99,4 %), `refent` (R30c) y lo de R12-R15; y la `dca` con pago y efecto de
la plantilla L5 (M14b), `synckey` = `referencia_externa`, `ctride` del contrato (0 sin él) y los totales sumados.
- **R22.** El sistema debe calcular `fec` (si no viene), `hor` y `fechor` en hora de Madrid una vez por petición;
prefijo `AC<aa>/` del año de `fecha_albaran`; `con.est` 1 `PDT` (en `dbo.conest`; si no, `estado_inicial_no_encontrado`)
y fila de alta de `log` con `est` 1 y `ori` 0 (M13); `mov.emp` = `con.emp`.

## Dry-run, commit e idempotencia (modo extendido)
- **R23.** MIENTRAS `commit` sea `false`, el sistema debe hacer solo lecturas con credenciales de lectura
y devolver `previsto`, `cod`/`ide` provisionales (`cod_provisional`) y las filas completas de `con`,
`dca`, `dcapro`, `ctrprodes`, `mov` y `log` (salvo R7).
- **R24.** CUANDO `commit` sea `true`, el sistema debe exigir antes de leer nada
`SIGRID_DOMAIN_WRITE_ENABLED`, `SIGRID_ALBARAN_WRITE_ENABLED` y credenciales de escritura
(`escritura_albaranes_deshabilitada`), y `database` en `ALLOWED_WRITE_DATABASES` (vacía **no** abre;
`base_de_datos_no_permitida`). `demasiadas_lineas` si > `SIGRID_ALBARAN_MAX_LINEAS`, aun en dry-run.
- **R25.** El sistema debe escribir el albarán en **una** transacción: `INSERT` de `con`, `dca`,
`dcapro`×N, `ctrprodes`×M, `mov`×K y la fila de alta de `log`; con vinculadas, `UPDATE` relativo de
`ctrpro.canser` por línea y de `ctr.estser/estfac` por `ide`. Nada más (ni `dcapropar`, ni `dcaproana`, ni `pro`).
- **R26.** Dentro de la transacción, bajo `sp_getapplock` (design §Applocks) y con `WITH (UPDLOCK,
HOLDLOCK)`, el sistema debe reservar el `cod` (`MAX` numérico del prefijo + 1 en la empresa de la obra;
índice único `(emp, tip, cod)`), los `ide` de `con`, `dcapro`, `ctrprodes`, `mov` y `log` (`MAX+1`) y leer
el stock y PMP vigentes de cada (producto, almacén), de los que salen `almcan`, `almpma` y `prepma` (R19).
- **R27.** SI un `INSERT` choca con una clave única (alta simultánea del escritorio), ENTONCES el sistema
debe repetir la transacción entera recalculando `cod`, `ide` y balances hasta `DOMAIN_WRITE_MAX_RETRIES`;
agotados, 400 `colision_de_clave` y el ERP intacto.
- **R28.** SI antes del `COMMIT` las relecturas (design E12) no dan 1 `con`, 1 `dca`, N `dcapro`, K `mov`,
M `ctrprodes` y 1 `log`, ENTONCES `ROLLBACK` (`filas_afectadas_inesperadas`).
- **R29.** SI la referencia no lleva prefijo admitido, ENTONCES `referencia_no_permitida`, aun en dry-run.
- **R30.** CUANDO ya exista un albarán `tip 14` con `dca.synckey` = `referencia_externa`, del mismo
proveedor y obra, el sistema debe devolverlo `idempotente` sin escribir (`committed` `false`, `dry_run` =
`not commit`; `ide`, `cod`, `fec`, totales y líneas leídas por `pos` con `indice` desde 0; H18): con
lecturas en dry-run y, en commit, **dentro** de la transacción bajo el applock de referencias, antes de
reservar nada. Más de uno, u otro proveedor u obra → `referencia_en_conflicto`. Anular **borra** el `con`
(M17b, H9): la misma referencia vuelve a dar de alta (R30b retirada).
- **R30c.** El sistema debe escribir `referencia_linea` (1-24) en `dcapro.refent` y devolverla en las
líneas de `idempotente` (M18: `refent` vacío en el 100 % y no pasa a la factura; H18, N9).

## Seguridad, trazas, verificación y documentación
- **R31.** Todo el SQL nuevo debe ser constante con valores `?` y validado con
`DatabaseReferenceGuard.validate(..., allowed=[database])`; sin `DELETE`, `MERGE` ni DDL, y sin más
`UPDATE` que los de R25 (control negativo en tests).
- **R32.** CUANDO termine una petición extendida, el sistema debe trazar (obra, contrato, referencia,
`commit`, `estado`, `cod`, nº líneas, códigos, duración), **nunca** textos, precios ni datos bancarios.
- **R33.** Ante una petición extendida equivalente a una clásica (solo vinculadas, positivas, sin `ctrpro`
repetido, partida y precio del `ctrpro`), el sistema debe producir filas iguales columna a columna a las
del clásico, salvo las diferencias de design §Equivalencia.
- **R34.** El sistema debe cubrir R1-R33 con tests sin red ni BBDD (`test_f009_rN_*`), comparando el SQL
carácter a carácter, con fase RED en R1, R8, R10, R11, R13b, R14, R15, R17-R19, R26-R28 y R30.
- **R35.** MANUAL (humano): T0 (hecha, T0b a T0b-quinquies); dry-run clásico y extendido sobre `CTSU16/0206` (obra
0404); `commit:true` autorizado de **un** albarán extendido revisado en la UI (`prepma` frente a un albarán del escritorio
del mismo día y almacén), repetición `idempotente` y anulación en la UI (nunca `DELETE`); tras el despliegue, solo
lectura de la **primera alta** (`prepma`) **y la primera devolución reales** del pipeline.
- **R36.** El sistema debe actualizar en el mismo trabajo `azure-apps/sigrid_api.md` (§4, §4.1, §7.2, §7.5, §7.6,
§8.6, §8.7, §10 con F-053, §13), el docstring de `sigrid_albaran` (H32), `docs/ARCHITECTURE.md` y `local.settings.sample.json`.

## Fuera de alcance
`dcapropar` (M7), `dcaproana` (M16b: 0 de 189.532), almacén/centro/cuenta/analítica/naturaleza en la petición,
pasar a partida una línea sin partida, rechazar fechas futuras, el PDF, modificar o anular, elegir producto (el
llamante), descuentos (H8), varios albaranes, cambiar el clásico o `albaran-directo` salvo R8, recalcular `mov`
posteriores (N1), escribir `pro` y corregir la naturaleza del maestro de `MA9999` (Administración; H34).
