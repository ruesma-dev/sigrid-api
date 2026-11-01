<!-- progress/verificacion_F-008.md -->
# F-008 · Verificación en producción (T22-T24)

**Despliegue (2026-10-31, lo lanzó el humano):** `func azure functionapp publish` desde `dev` `18c8c20` (merge de
F-008). El primer intento murió en Core Tools 4.9.0 (`System.ArgumentException: Destination is too short` en
`PythonHelpers.VerifyVersion`) sin desplegar nada; el segundo, bien. Azure lista 11 funciones, con `sigrid_factura`.

## T22 · Permisos de `user_rw`

Confirmados por el humano el 2026-11-01 («t22 escribe»).

## D · Llave cerrada (líder, 2026-11-01, autorización del humano para T23)

- **D1:** las cinco App Settings que no son la llave, por `@json`, comprobadas antes con `Settings` como variables de
  entorno: `PREFIJOS_REFERENCIA ["FAC-"]`, `PRODUCTOS_SIN_ORIGEN` (los seis), `IVAS` (los siete), `CUENTAS_GASTO_PREFIJOS
  ["6"]` y `NATURALEZA_POR_PRODUCTO`. `MAX_LINEAS` sin cargar (500). En `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` solo
  estaban `MA9999`, `QA9999` y `XA9999`: se paró y el humano aprobó completar con la naturaleza dominante medida en las
  líneas de FR y FRGG de 2026: `SM9999`→`SM99` (12.912 de 12.914), `SB9999`→`SB99` (4.690 de 4.693), `SM370001`→`SM37`
  (13.640 de 15.332). `MA9999` sigue en `MA99`, como en albaranes, aunque en facturas domina `MA1501` (20.411 de 24.194).
- **D3:** `SIGRID_FACTURA_WRITE_ENABLED` **ausente** (vale `false`); las cinco, con su valor.
- **D4:** cuerpo fijo `NOADMITIDA-D2` con `commit:true`: 400 `escritura_facturas_deshabilitada`.
- **D5:** `total_base = "20"`: 400 «Solicitud invalida.» con solo `loc`, `type` y `msg`.

## T23 · Previas (líder, 2026-11-01; todas `commit:false`)

Referencias `FAC-VERIF-F008-<previa>-1`, `usu` `prueba`, fecha 20261031, un vencimiento a 20261130. **C0** (máximos de
`con`, `dcfpro`, `pag` y número de `con` 15) igual antes y después de **cada** previa. Todas las `previsto` con
`committed` false, `dry_run` true y el aviso `cod_provisional`; ninguna con retención.

| Previa | Datos (`con.ide`) | Resultado | Lo mirado |
|---|---|---|---|
| P1 | FR mes, albarán 2865056 (`AC26/31427`), 1 línea | `previsto`, `FR26/11425` | `tot` 540 = 18 × 30; un `dcaprodes` por línea; totales 540 / 113,4 / 653,4 |
| P2 | FR origen, proforma 2863148 (`PROF26/01382`) | `previsto` | `canoriori` 15 e `imporiori` 2.556 = los mandados; `ctride` el de la proforma; IVA 0 como la proforma |
| P2b | la de P2 sin `a_origen` | 400 `a_origen_incompleto` | `details.faltan` = la línea de la proforma |
| P3 | P1 + una línea `MA9999` de 10 € | `previsto` | una `origen` y una `sin_origen`; la sin origen con `MA99` y cuenta `6000000000` |
| P4 | FR sin origen con la línea de la FR 2856253 (`FR26/10936`, obra 0644, `SB9999`) | `previsto` | `proide`, `ivaide`, `almide` y totales iguales a la real; **difieren** `natide`, `cueide`, `caaide` y `cenide` (abajo) |
| P5 | FRGG sin origen con la cuenta y analítica de la FRGG 2864690 (`FRGG26/2730`) | `previsto`, `FRGG26/2732` | `cod` de 4 cifras; `cueide`, `caaide`, `natide` 0, `ivaide`, `almide` y `cenide` **iguales** a la real |
| P6 | FRGG mes, albarán 2864857 (`AC26/31420`), 2 líneas | `previsto` | se admite el origen en FRGG; dos `dcaprodes` |
| P7 | P4 con el número real | 400 `factura_ya_registrada` | `details.cod` = `FR26/10936` |

**P4, diferencia de datos (no se corrige sin feature nueva):** la línea real, en una factura de la obra 0644, imputa a
la analítica `0544.CDMA36` y al centro de la obra **0544**, con naturaleza `MA36` y cuenta `6000000000`. La API deduce la
naturaleza del producto (`SB9999`→`SB99`, la dominante), y de ahí la cuenta `6060000000` y la analítica `0644.CDSB37`,
siempre de la obra de la factura. Es la regla de la spec (R25, como F-009); la factura real es un caso de imputación a
otra obra que la API no cubre.

**Hallazgos del guion:** `pag` se une a su factura por `conide`, no por `docide` (corregido en `verificacion_manual.md`
§T24). Hay FR sin origen reales sin producto (314 líneas de 2026, con cuenta y analítica como una FRGG); la API las
rechazaría en FR. Para P4 se eligió una con producto.

## T24 · Grabaciones

Pendiente: G1 (FR en la 0404) y G2 (FRGG), cada una con autorización expresa del humano.
