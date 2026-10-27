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

## T22 · Grabación autorizada

Pendiente. El humano elige una hoja real que no esté en Sigrid y autoriza esa llamada. V1 se hará junto con ella.
