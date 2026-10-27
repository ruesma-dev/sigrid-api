<!-- progress/verificacion_F-007.md -->
# F-007 · Verificación manual (T20-T22) contra la API desplegada

Guion: [`verificacion_manual.md`](../specs/F-007-registrar-proforma/verificacion_manual.md). Todo por la API
desplegada; nada por SQL directo. Hasta T22, ninguna escritura: solo lecturas y previas con `commit:false`.

## T20 · Respuestas de `proformas` a design §Preguntas (2026-10-26)

Llegaron de la sesión `proformas` (su humano). Han recibido el contrato v1.1 y dicen que nada les choca.

1. **CIF o nombre:** mandan **solo `cif_proveedor`**, nunca `nombre_proveedor`. Sacan el CIF del contrato en Sigrid
   por `sql/read`, porque la hoja trae el nombre del subcontratista y no su CIF.
2. **Líneas:** mandan solo las de MES ≠ 0.
3. **Avisos:** solo `supera_contrato_10` bloquea la aprobación. Los demás (`anterior_distinto_de_sigrid`,
   `otra_del_mes`…) se enseñan en su bandeja como informativos.
4. Las líneas de contrato irán **siempre con `ctrpro_ide`**, así que no usarán el respaldo por partida y precio.

**Queda de T20:** V8 con Administración (los contratos a origen). Los productos de las partidas sin contrato y la
lista de R4 (`SM9999`, `SB9999`, `SM370001`) los decidió el humano el 2026-10-25 (D11).

## T21 · Despliegue y previas (2026-10-26/27)

- **Avisos enviados antes del despliegue (2026-10-26):** a `proformas` (contrato v1.1), a `facturas` (serie `PROF`
  y `entref`) y a `albaranes` (costuras sin cambio de conducta y riesgo O3).
- **Merge local** de F-007 en `dev`: `0e9aa8d`. Suite completa sobre `dev`: `3393 passed, 1 skipped`.
- **D1.** Las cinco App Settings se subieron en JSON por `@fichero` (fuera del repositorio), después de validarlas con
  `Settings`: `False ['PRF-'] ['SM9999', 'SB9999', 'SM370001'] {...} 500`. El `appsettings list` enseña las cinco con
  esos valores, más `SIGRID_DOMAIN_WRITE_ENABLED` `true`, que no se tocó. Tras el reinicio, `sql/read` responde.
- **D2.** El humano publicó desde `dev` (`0e9aa8d`) con `!` el 2026-10-26 a las 23:00:56 UTC: «The deployment was
  successful!», con 10 funciones, entre ellas `sigrid_proforma`.
- **D3.** Dry-run de `sigrid/albaran`, obra 0404, contrato `CTSU16/0206`: `200 previsto AC26/30822`,
  `dry_run True`. Las rutas siguen vivas y el riesgo O3 no se dio.
- **V1** (llave cerrada con `commit:true`): **no se lanzó**. El clasificador de permisos de la sesión bloqueó el
  comando porque llevaba `commit:true` contra producción. Que la llave está cerrada se ve en el `appsettings list`.
  Queda para T22, cuando el humano autorice esa llamada.
- **V2.** Las tres hojas dan `existente` sobre la `AC` esperada. `resuelto_por` es `peticion` y no hay avisos. Las
  líneas son las de LP6 (`ctrpro_ide` = `linoriide`), y `count` por `synckey` es 0 en las tres.

  | Contrato | Estado | Documento | `totbas` | Tiempo |
  |---|---|---|---|---|
  | `CTSB26/0472` | `existente` | `AC26/25548` | 17024.27 | 5,6 s (frío) |
  | `CTSB26/0417` | `existente` | `AC26/25552` | 31291.06 | 2,7 s |
  | `CTSB26/0369` | `existente` | `AC26/25551` | 7991.01 | 1,1 s |

- **V3** (con `otra_del_mes`): las tres dan `previsto` con `PROF26/01356` (código provisional) y el aviso
  `otra_del_mes`, que cita su `AC`. Las líneas de contrato llevan los mismos `ctrpro_ide`, cantidad y precio que la
  `existente`; las nuevas van sin vincular y con su producto. `totbas`: 17024.28 frente a 17024.27, 31291.06 frente
  a 31291.06 y 7991.00 frente a 7991.01, todos dentro de ±0,01. La retención coincide con la de la `AC`: 851.21 al 5 %
  y 500.66 al 1,6 % en la 0417 (`dcarec` de `AC26/25552`, `valpor` 0.016). `count` es 0 en las tres.
- **V4** (respaldo sin `ctrpro_ide`, por partida y precio): las tres dan `previsto` con **los mismos `ctrpro_ide`
  que V3**. Ninguna es `linea_ambigua`: en la 0417, las tres líneas de cada partida de ferralla tienen precios
  distintos (1, 0,2 y 0,27). `count` es 0.

**Dos datos del guion que estaban mal, corregidos en `verificacion_manual.md`.** Ninguno es un defecto de la API.

1. **En la hoja de la 0417, la partida de «Seguridad y replanteo» es `09.01`, no `9.01`.** Con `9.01` la API responde
   400 `partida_no_encontrada`, que es lo correcto, y la `AC26/25552` real la tiene en `09.01`. Es el caso «código
   como en el presupuesto» de `plantilla_hoja.md`.
2. **En V4, `Cuerpo` no mandaba `medicion_contrato`.** Sin `ctrpro_ide` ni medición, la línea es sin contrato (R13) y
   sale `producto_obligatorio`, que también es lo correcto. Ahora manda la medición del contrato, que es la columna de
   la hoja.

## T22 · Grabación autorizada (2026-10-27)

**Autorización.** El humano no tenía hoja real sin registrar. Autorizó la grabación de una **hoja sintética** en la
obra 0404, contrato de pruebas `CTSU16/0206` (`ctr.ide` 1035535, sin retenciones), referencia
`PRF-prueba-F007-T22`, periodo `202610`, usuario `prueba`. La hoja trae dos líneas de contrato, `ctrpro_ide` 258782
(2 × 30) y 258783 (1 × 45). Importes: mes 105, anterior 0 y origen 105.

**La línea sin contrato no entró.** Con `partida` `13.01` y con `02.04.01.01`, la previa respondió 400
`partida_ambigua`: «Hay 5 partidas imputables … en la obra: indica paride». La proforma no admite `paride`
(contrato v1.1), así que en una obra con códigos de partida repetidos las líneas sin contrato no se pueden imputar. En
la 0719 no pasó. Queda como observación para `proformas`. No se reintentó con otra partida: la hoja se quedó en las
dos líneas de contrato.

- **Previa:** `200 previsto PROF26/01360`, `cla 141`, `ctride` 1035535, `entref` `PROF1026_0404`, `synckey` la
  referencia. Totales: `totbas` 105, `totiva` 22.05, `totdoc`/`tot` 127.05. Las dos `dcapro` llevan `docoritip` 44 y
  `linoriide` = su `ctrpro_ide`; no hay `dcarec`. Antes de grabar, `canser` es 0 en las dos líneas y `count` por
  `synckey` es 0.
- **V1** (`commit:true` con la llave cerrada): 400 `escritura_proformas_deshabilitada`, «Escritura de proformas
  desactivada (SIGRID_PROFORMA_WRITE_ENABLED=false): no se ha escrito nada.». `canser` y `count`, sin cambios.
- **Llave:** se abrió solo `SIGRID_PROFORMA_WRITE_ENABLED=true` por `@json`. `SIGRID_DOMAIN_WRITE_ENABLED` siguió en
  `true`, sin tocar.
- **V5 · grabación:** `200 creado`, `con_ide` **2861898**, `PROF26/01360`, `dry_run False`, aviso `cabecera_sin_dato`
  (bancos vacíos, como el alta a mano). Lecturas:
  - `con.fec` 20261027: el mes en curso toma la fecha de hoy (R18). `cla` 141, `ctride`, `entref`, `synckey` y
    totales como en la previa.
  - `dcapro`: (64, `S1`, 44, 258782, 2, 30, 60) y (128, `S2`, 44, 258783, 1, 45, 45). `dcarec` 0.
  - `canser` 0→2 y 0→1. `ctr.estser`/`estfac` 0/0, porque el contrato no queda servido entero.
  - `dbo.log`: ope 1, usuario `prueba`, `tab` `con`.
- **Repetición:** `200 idempotente`, mismo `con_ide` 2861898, `origen` nulo, `avisos` vacío, y `canser` sin cambios.
- **Llave cerrada** después de la repetición: `SIGRID_PROFORMA_WRITE_ENABLED=false` (comprobado con `appsettings list`).

**El código `PROF26/01360` ya se había usado.** En `dbo.log` consta una `PROF26/01360` anterior, de otra obra y otro
proveedor: alta (ope 1) y baja (ope 2) de un usuario de Administración el mismo día a las 08:54-08:55. Al grabar ya no
existía. Hoy hay **una sola** `con` con ese código, la nuestra. Es el MAX+1 de Sigrid, que también reutiliza el número
tras una baja.

**Queda de T22 (humano):**
- V6 en la UI: la ficha (serie, clase, líneas vinculadas, totales, servido), la impresión y el paso a factura.
- **Anular `PROF26/01360` desde la UI** (es de prueba; nunca `DELETE`).
- Después, las lecturas de V5: sin `con` 2861898, `count` por `synckey` 0 y `canser` de 258782 y 258783 de vuelta a 0.
