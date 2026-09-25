<!-- progress/verificacion_F-006_obra0626.md -->
# F-006 · Verificación en producción (T15-T18), obra 0626

> Líder, 2026-09-25. Autorizaciones del humano en el chat: «te autorizo la
> escritura» (T17) y «te autorizo t18». Lecturas por `sql/read` de la API
> desplegada; `az` solo para leer y, por el humano, fijar App Settings. Sin
> secretos ni datos personales (la UPV de prueba no tiene propietario ni persona).

## T15 · Despliegue y App Settings

- El humano publicó desde `dev` `9e552b0` (`func azure functionapp publish
  func-sigridapi-dev-huyke --python`, exit 0): la ruta
  `sigrid_partes_reclamacion` aparece entre las funciones publicadas.
- App Settings fijadas por fichero JSON (ASCII, sin BOM). Leídas después con
  `az functionapp config appsettings list` filtrando `SIGRID_RECLAMACION*`,
  `ALLOWED_WRITE_DATABASES` y `SIGRID_DOMAIN_WRITE_ENABLED`:
  `ALLOWED_WRITE_DATABASES ["ruesma"]`, `SIGRID_DOMAIN_WRITE_ENABLED true`,
  `SIGRID_RECLAMACION_WRITE_ENABLED false`, `_MAX_PARTES 50`,
  `_PREFIJOS_REFERENCIA ["PVI-"]`, `_PRESUPUESTO_SEGUNDOS 150`.
- **Hallazgo al preparar el JSON:** una lista de App Setting en CSV (`PVI-`,
  y también `ALLOWED_WRITE_DATABASES=ruesma`) hace fallar `Settings` con
  `SettingsError`: pydantic-settings la decodifica como JSON antes del
  validador. Se fijó en JSON. No es de F-006 (afecta a todas las listas);
  corregido el texto de `azure-apps/sigrid_api.md` §4 (`b3a43c2`). El test
  `test_f006_r4_los_prefijos_aceptan_json_y_csv` solo prueba el constructor.

## T16 · Dry-run (lote literal de tres partes), OK

HTTP 200 en 5,0 s; `committed:false`, `dry_run:true`; resumen `previstos 1,
rechazados 2`:

| `indice` | Referencia | Estado | Detalle |
|---|---|---|---|
| 0 | `PVI-PRUEBA-0001` | `previsto` | `RS26.09/0439` provisional, `ide` 2841944 |
| 1 | `PVI-PRUEBA-0002` | `rechazado` | `unidad_postventa_no_encontrada` |
| 2 | `PVI-PRUEBA-0003` | `rechazado` | `interviniente_no_esta_en_la_obra` (oficio `0006`) |

Contadores antes → después: `MAX(con.ide)` 2841943 → 2841943; `MAX(cod)` de
`RS26.09/[0-9][0-9][0-9][0-9]` `RS26.09/0438` → igual; `RCPCLI` con `PVI-%`
0 → 0. `MAX(log.ide)` subió de 8489424 a 8489426: leídas esas filas, son
modificaciones (`ope 5`) de facturas `FR26/…` de otro usuario, ninguna de
`prueba` ni de `tip 708`. El preview de las cinco filas coincidió con
`design.md` §Filas (UPV 2080537, `trcpide` 2, `ofcide` 39, `rcptip` 1,
`rcpint.obrofcide` 1052, `RCPCLI` = `PVI-PRUEBA-0001`, `log` `ope 1` `usu prueba`).

## T17 · Primer `commit:true` (autorizado), OK

El humano abrió **solo** `SIGRID_RECLAMACION_WRITE_ENABLED` (leída `true`,
con `SIGRID_DOMAIN_WRITE_ENABLED` `true`). Una llamada con el parte válido:
HTTP 200 en 6,1 s, `committed:true`, `creado` **`RS26.09/0439`**, `ide`
**2842466**. Lecturas:

| Tabla | Filas | Valores |
|---|---|---|
| `con` | 1 | `emp 1`, `tip 708`, `subtip 0`, `res` «PRUEBA API - ANULAR», `fec` 20260925, `est 1`, `tiemod` 46290,4857 (11:39:20 UTC = 13:39:20 Madrid), resto de constantes de §Filas |
| `rcp` | 1 | `upvide` 2080537 (`0626.03PORTAL 1.1.A`, obra 1758465), `pos` 1437120, `hor` 133920, `cliide`/`recide`/`cntide` 0, `trcpide` 2, `rcptip` 1, `ofcide` 39 |
| `rcpint` | 1 | `obrofcide` 1052 (oficio `0039`, proveedor `1181`, obra 1758465), `pos 0`, `cauave 0` |
| `conext` | 1 | `RCPCLI` = `PVI-PRUEBA-0001`, `camtip 0` |
| `log` | 1 | `ope 1`, `usu prueba`, `tab con`, `tip 708`, `cod` `RS26.09/0439`, `est 1` |

`con` con ese `cod`: 1 fila. **El humano abrió el parte en Sigrid** (pestaña
Reclamaciones de la UPV): «se ha creado bien, todo ok».

## T18 · Repetición idempotente (autorizada), OK

Misma llamada con `commit:true`: HTTP 200 en 5,9 s, `idempotente`,
`RS26.09/0439` / 2842466, aviso «Ya existe el parte … no se ha escrito nada»,
`committed:false`. Después: 1 `conext` con `PVI-PRUEBA-0001`, 1 parte «PRUEBA
API» en la UPV, 1 `rcpint`, 1 alta en `log`.

## Decisiones del humano y pendientes

- **La llave se queda abierta** (2026-09-25): `SIGRID_RECLAMACION_WRITE_ENABLED=true`
  de forma estable, como `concepto-grafico`. El paso 3 de T17 (cerrarla) no se
  ejecuta por esa decisión.
- **El parte de prueba sigue en SAT** (leído el 2026-09-25 tras T18): falta
  anularlo desde la UI de Sigrid (NO PROCEDE, **sin** correo), nunca con `DELETE`.
